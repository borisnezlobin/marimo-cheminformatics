"""The stereocentre editor.

One molecule, drawn in the browser by RDKit's WebAssembly build, with its
stereocentres marked and a control beside each one that turns it into its
mirror arrangement. Clicking a control rewrites the `smiles` trait, which lets
Python look the new structure up in whatever tables the notebook has loaded and
send back a `readout`.

The flip happens in the browser by toggling one chirality token in the SMILES
string, so the drawing changes at the speed of a click and keeps working in a
static export. Python is only needed for the lookup.

Two things the notebook author needs to know:

* `centers` must be derived from the same SMILES string that is in the `smiles`
  trait. RDKit numbers atoms in the order they appear in a SMILES, so the
  widget can line each listed centre up with its token in the string.
* Quinine and quinidine differ at two centres, not one. Flipping either centre
  alone gives epiquinine or epiquinidine; flipping both gives quinidine. That
  is chemistry, not a limitation of the control.
"""

import anywidget
import traitlets

from ._theme import JS_PRELUDE, stylesheet

_CSS = stylesheet("""
.st__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.st__draw {
  background: var(--card);
  border-radius: var(--r-outer);
  box-shadow: var(--lift);
  padding: 10px;
  display: grid;
  place-items: center;
  min-height: 240px;
}

.st__draw svg { max-width: 100%; height: auto; display: block; }

.st__loading { color: var(--ink-3); font-size: 13px; }

.st__centers { list-style: none; margin: 10px 0 0; padding: 0; display: grid; gap: 8px; }

.ctr {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 4px 12px;
  background: var(--card);
  border-radius: var(--r-outer);
  box-shadow: var(--lift);
  padding: 11px 12px 11px 14px;
}

.ctr__label { font-size: 13.5px; }
.ctr__now { display: block; color: var(--ink-2); font-size: 13px; }
.ctr__now b { color: var(--ink); font-weight: 650; }
.ctr__flip { white-space: nowrap; }

.st__smiles {
  margin-top: 12px;
  font-family: var(--num);
  font-size: 12.5px;
  color: var(--ink-2);
  word-break: break-all;
  background: var(--sunk);
  border-radius: var(--r-inner);
  padding: 9px 11px;
}

.st__read { display: grid; gap: 10px; }
.st__read p { color: var(--ink-2); font-size: 13.5px; max-width: 66ch; }

.st__values {
  justify-self: start;
  border-collapse: collapse;
  font-size: 13.5px;
  min-width: 220px;
}

.st__values th {
  text-align: left;
  font-weight: 550;
  color: var(--ink-2);
  padding: 4px 18px 4px 0;
}

.st__values td {
  font-family: var(--num);
  font-variant-numeric: tabular-nums;
  text-align: right;
  padding: 4px 0;
  font-weight: 600;
}

.st__values tbody tr + tr th, .st__values tbody tr + tr td {
  box-shadow: inset 0 1px 0 var(--hair);
}

.st__busy { color: var(--ink-3); font-size: 13px; max-width: 66ch; }

.st__warn {
  margin-top: 10px;
  background: var(--accent-soft);
  border-radius: var(--r-inner);
  padding: 10px 12px;
  font-size: 13px;
  color: var(--ink);
}

@container (max-width: 520px) {
  .st__grid { grid-template-columns: minmax(0, 1fr); }
}
""")

_ESM = (
    JS_PRELUDE
    + """
const RDKIT_VERSION = "2026.3.6";
const RDKIT_ESM = `https://cdn.jsdelivr.net/npm/@rdkit/rdkit@${RDKIT_VERSION}/+esm`;
const RDKIT_WASM = `https://cdn.jsdelivr.net/npm/@rdkit/rdkit@${RDKIT_VERSION}/dist/RDKit_minimal.wasm`;

let rdkitReady = null;
const loadRDKit = () => {
  if (!rdkitReady) {
    rdkitReady = import(RDKIT_ESM)
      .then((mod) => (mod.default || mod.initRDKitModule)({ locateFile: () => RDKIT_WASM }));
  }
  return rdkitReady;
};

const INK = { light: [0.09, 0.09, 0.11], dark: [0.95, 0.95, 0.94] };
const ELEMENTS = [0, 1, 6, 7, 8, 9, 15, 16, 17, 35, 53];

const palette = (shade) => Object.fromEntries(ELEMENTS.map((z) => [z, INK[shade]]));

const tagPositions = (smiles) => {
  const found = [];
  for (let i = 0; i < smiles.length; i += 1) {
    if (smiles[i] !== "@") continue;
    const doubled = smiles[i + 1] === "@";
    found.push({ at: i, len: doubled ? 2 : 1 });
    if (doubled) i += 1;
  }
  return found;
};

const flipToken = (smiles, ordinal) => {
  const tags = tagPositions(smiles);
  const tag = tags[ordinal];
  if (!tag) return null;
  const replacement = tag.len === 2 ? "@" : "@@";
  return smiles.slice(0, tag.at) + replacement + smiles.slice(tag.at + tag.len);
};

// RDKit's own list of assigned stereocentres, in atom order, so a centre can be
// matched to its token even when Python lists only some of them as flippable.
const cipCodes = (mol) => {
  try {
    const raw = JSON.parse(mol.get_stereo_tags());
    const rows = raw.CIP_atoms || raw.CIP_codes || [];
    return rows
      .map(([index, code]) => ({ index, code: String(code).replace(/[()]/g, "") }))
      .filter((row) => /^[RSrs]$/.test(row.code))
      .sort((a, b) => a.index - b.index);
  } catch (err) {
    return [];
  }
};

const other = (code) => (code === "R" ? "S" : code === "S" ? "R" : "its mirror");

const draw = (RDKit, smiles, shade, highlight, width, height) => {
  const mol = RDKit.get_mol(smiles);
  if (!mol || !mol.is_valid()) {
    if (mol) mol.delete();
    return { svg: null, codes: [], tagged: [] };
  }
  const details = {
    width,
    height,
    addStereoAnnotation: true,
    backgroundColour: [0, 0, 0, 0],
    atomColourPalette: palette(shade),
    highlightColour: shade === "dark" ? [0.35, 0.2, 0.1] : [0.98, 0.88, 0.8],
    atoms: highlight,
    bonds: [],
  };
  let svg;
  try {
    svg = mol.get_svg_with_highlights(JSON.stringify(details));
  } catch (err) {
    svg = mol.get_svg(width, height);
  }
  const codes = cipCodes(mol);
  mol.delete();
  return { svg, codes };
};

const readoutMarkup = (readout) => {
  const title = readout && readout.title ? readout.title : "";
  const lines = (readout && readout.lines) || [];
  const measured = (readout && readout.measured) || [];
  const rows = measured
    .map((row) => `<tr><th scope="row">${esc(row.enzyme)}</th><td>${esc(row.value)}</td></tr>`)
    .join("");
  return `
    ${title ? `<h2>${esc(title)}</h2>` : ""}
    ${lines.map((line) => `<p>${esc(line)}</p>`).join("")}
    ${rows ? `<table class="st__values"><tbody>${rows}</tbody></table>` : ""}
  `;
};

export default {
  render({ model, el, signal }) {
    const root = document.createElement("div");
    root.className = "w st";
    root.innerHTML = `
      <section class="sect st__grid">
        <div class="st__draw"><span class="st__loading">Drawing the structure.</span></div>
        <div>
          <h2>Stereocentres you can flip</h2>
          <ul class="st__centers"></ul>
          <p class="st__warn" hidden>This structure writes its stereochemistry in a form the
            editor cannot line up with the listed centres, so flipping is switched off here.</p>
          <p class="st__smiles"></p>
        </div>
      </section>
      <section class="sect st__read" role="status"></section>
    `;
    el.appendChild(root);
    const unbindTheme = bindTheme(root, model);

    const drawBox = root.querySelector(".st__draw");
    const centerList = root.querySelector(".st__centers");
    const warnLine = root.querySelector(".st__warn");
    const smilesLine = root.querySelector(".st__smiles");
    const readBox = root.querySelector(".st__read");

    let alive = true;
    let RDKit = null;
    let codes = [];
    let localSmiles = model.get("smiles") || "";
    let localCenters = (model.get("centers") || []).slice();
    let waiting = null;

    const shade = () => {
      const chosen = root.getAttribute("data-theme");
      if (chosen) return chosen;
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    };

    const ordinalFor = (atomIndex) => {
      if (codes.length) {
        const found = codes.findIndex((c) => c.index === atomIndex);
        if (found >= 0) return found;
      }
      const sorted = localCenters.slice().sort((a, b) => a.atom_index - b.atom_index);
      return sorted.findIndex((c) => c.atom_index === atomIndex);
    };

    const currentCode = (center) => {
      const found = codes.find((c) => c.index === center.atom_index);
      return found ? found.code : String(center.current || "").replace(/[()]/g, "");
    };

    const paintCenters = () => {
      const tagCount = tagPositions(localSmiles).length;
      const mismatch = codes.length > 0 && codes.length !== tagCount;
      centerList.innerHTML = localCenters.map((center) => {
        const code = currentCode(center);
        const target = other(code);
        const ordinal = ordinalFor(center.atom_index);
        const usable = !mismatch && ordinal >= 0 && ordinal < tagCount;
        return `<li class="ctr">
            <span>
              <span class="ctr__label">${esc(center.label)}</span>
              <span class="ctr__now">Currently arranged <b>${esc(code || "unset")}</b></span>
            </span>
            <button class="btn-solid ctr__flip" type="button" data-ordinal="${ordinal}"
                    ${usable ? "" : "disabled"}>Flip to ${esc(target)}</button>
          </li>`;
      }).join("");
      warnLine.hidden = !mismatch;
      smilesLine.textContent = localSmiles;
    };

    const paintDrawing = () => {
      if (!RDKit || !alive) return;
      const width = Math.max(260, Math.min(420, drawBox.clientWidth - 20 || 320));
      const height = Math.round(width * 0.78);
      const highlight = localCenters.map((c) => c.atom_index).filter((i) => Number.isInteger(i));
      const result = draw(RDKit, localSmiles, shade(), highlight, width, height);
      if (!alive) return;
      codes = result.codes;
      drawBox.innerHTML = result.svg
        || `<span class="st__loading">This structure could not be drawn.</span>`;
      paintCenters();
    };

    const paintReadout = () => {
      clearTimeout(waiting);
      waiting = null;
      readBox.innerHTML = readoutMarkup(model.get("readout"));
    };

    paintCenters();
    paintReadout();

    loadRDKit().then((lib) => {
      if (!alive) return;
      RDKit = lib;
      paintDrawing();
    }).catch(() => {
      if (alive) drawBox.innerHTML = `<span class="st__loading">The structure drawer
        could not be loaded from the network.</span>`;
    });

    const onSmiles = () => {
      const incoming = model.get("smiles") || "";
      if (incoming === localSmiles) return;
      localSmiles = incoming;
      paintDrawing();
      paintCenters();
    };

    const onCenters = () => {
      localCenters = (model.get("centers") || []).slice();
      paintDrawing();
      paintCenters();
    };

    const onFlip = (event) => {
      const button = event.target.closest("[data-ordinal]");
      if (!button || button.disabled) return;
      const next = flipToken(localSmiles, Number(button.getAttribute("data-ordinal")));
      if (!next) return;
      localSmiles = next;
      paintDrawing();
      readBox.innerHTML = `<p class="st__busy">Looking up the flipped structure.</p>`;
      clearTimeout(waiting);
      waiting = setTimeout(() => {
        readBox.innerHTML = `<p class="st__busy">Nothing answered the lookup, so this page is
          running without a Python kernel behind it. The structure still flips and redraws
          here; open the notebook itself to see what has been measured for it.</p>`;
      }, 8000);
      model.set("smiles", next);
      model.save_changes();
    };

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onScheme = () => paintDrawing();

    model.on("change:smiles", onSmiles);
    model.on("change:centers", onCenters);
    model.on("change:readout", paintReadout);
    model.on("change:theme", onScheme);
    media.addEventListener("change", onScheme, { signal });
    root.addEventListener("click", onFlip, { signal });

    signal.addEventListener("abort", () => {
      alive = false;
      clearTimeout(waiting);
      unbindTheme();
      model.off("change:theme", onScheme);
      model.off("change:smiles", onSmiles);
      model.off("change:centers", onCenters);
      model.off("change:readout", paintReadout);
      el.innerHTML = "";
    });
  },
};
"""
)

QUININE = "C=C[C@H]1CN2CC[C@H]1C[C@H]2[C@H](O)c1ccnc2ccc(OC)cc12"

QUININE_CENTERS = [
    {"atom_index": 2, "label": "Carbon 3, carrying the vinyl group", "current": "R"},
    {"atom_index": 7, "label": "Carbon 4, the bridgehead", "current": "S"},
    {"atom_index": 9, "label": "Carbon 8, joining the two ring systems", "current": "S"},
    {"atom_index": 10, "label": "Carbon 9, carrying the hydroxyl group", "current": "R"},
]


class StereoEditor(anywidget.AnyWidget):
    """One molecule, its flippable stereocentres, and whatever Python found.

    Traits in: `centers`, `readout`, `theme`. Two-way: `smiles`.
    """

    _esm = _ESM
    _css = _CSS

    smiles = traitlets.Unicode(QUININE).tag(sync=True)
    centers = traitlets.List(traitlets.Dict(), default_value=QUININE_CENTERS).tag(sync=True)
    readout = traitlets.Dict().tag(sync=True)
    theme = traitlets.Unicode("").tag(sync=True)
