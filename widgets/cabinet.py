"""The medicine cabinet widget.

A shelf of medicines the reader adds to by typing and removes from by clicking,
and underneath it the pairs of shelf medicines that act on the same enzyme.
Every pair draws FDA's exposure band as a bar and, where one exists, the
potency somebody measured in a laboratory.

Python hands the widget one complete reference set at construction: `catalog`,
every drug the reader can add, and `pair_index`, every interaction that exists
among them. After that the widget owns the shelf. Adding, removing, resolving
a typed name against the alias lists and filtering the pair index all happen in
JavaScript, so the cabinet still works in a static export with no kernel behind
it and cannot form a reactive cycle in marimo.

`shelf` syncs both ways. Python seeds it with the opening example and can read
it back; `shelf_changed` counts the edits the reader has made, for a notebook
that wants to react to one.
"""

import anywidget
import traitlets

from ._theme import JS_PRELUDE, stylesheet

_CSS = stylesheet("""
.cab__add {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.cab__input {
  flex: 1 1 200px;
  min-height: 36px;
  padding: 0 12px;
  border-radius: var(--r-inner);
  border: 1px solid var(--hair);
  background: var(--card);
  color: var(--ink);
}

.cab__input::placeholder { color: var(--ink-3); }

.cab__says { margin-bottom: 12px; font-size: 13px; color: var(--ink-2); max-width: 62ch; }

.cab__shelf {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.shelf__item {
  display: grid;
  grid-template-columns: 1fr auto 34px;
  align-items: center;
  gap: 4px 12px;
  background: var(--card);
  border-radius: var(--r-outer);
  box-shadow: var(--lift);
  padding: 11px 11px 11px 15px;
}

.shelf__name { font-weight: 600; }
.shelf__sub { display: block; }

.state {
  --chip-bg: var(--sunk);
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 4px 11px;
  border-radius: var(--r-pill);
  background: var(--chip-bg);
  color: var(--ink-2);
  font-size: 12.5px;
  line-height: 1.5;
  white-space: nowrap;
}

.state svg { flex: none; }
.state--measured { --chip-bg: var(--ink); color: var(--bg); font-weight: 550; }
.state--unknown {
  background-color: transparent;
  background-image: repeating-linear-gradient(135deg, var(--hatch) 0 5px, transparent 5px 10px);
  color: var(--ink-2);
}

.cab__legend { font-size: 13px; color: var(--ink-2); margin-bottom: 12px; max-width: 74ch; }
.cab__pairs { display: grid; gap: 12px; }

.pair__flow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.pair__drug { font-size: 15px; font-weight: 600; }
.pair__arrow { color: var(--ink-3); flex: none; }

.pair__band { margin-bottom: 10px; max-width: 70ch; }
.pair__band b { font-weight: 600; }

.pair__scale { position: relative; height: 12px; }

.pair__track {
  position: absolute;
  inset: 1px 0;
  border-radius: var(--r-pill);
  background: var(--sunk);
}

.pair__seg {
  position: absolute;
  top: 0;
  bottom: 0;
  border-radius: var(--r-pill);
  background: var(--ink-2);
  min-width: 6px;
}

.pair__seg--open {
  -webkit-mask-image: linear-gradient(to right, #000 78%, transparent 100%);
  mask-image: linear-gradient(to right, #000 78%, transparent 100%);
}

.pair__unity {
  position: absolute;
  top: -2px;
  bottom: -2px;
  width: 2px;
  background: var(--card);
  box-shadow: 0 0 0 1px var(--hair);
}

.pair__ticks {
  position: relative;
  height: 18px;
  margin-bottom: 12px;
  font-size: 12px;
  color: var(--ink-3);
}

.pair__tick {
  position: absolute;
  transform: translateX(-50%);
  font-family: var(--num);
  font-variant-numeric: tabular-nums;
}

.pair__measure {
  display: flex;
  align-items: baseline;
  gap: 9px;
  padding-top: 11px;
  box-shadow: inset 0 1px 0 var(--hair);
  max-width: 74ch;
}

.pair__none { margin-top: 11px; }

.pair__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--accent);
  flex: none;
  transform: translateY(-1px);
}

.pair__value { font-family: var(--num); font-variant-numeric: tabular-nums; font-weight: 600; }
.pair__note { margin-top: 9px; color: var(--ink-2); font-size: 13px; max-width: 74ch; }

.cab__empty {
  background: var(--card);
  border-radius: var(--r-outer);
  box-shadow: var(--lift);
  padding: 18px;
  display: grid;
  gap: 9px;
}

.cab__empty h3 { font-weight: 600; }
.cab__empty p { color: var(--ink-2); font-size: 13.5px; max-width: 62ch; }

@container (max-width: 440px) {
  .shelf__item { grid-template-columns: 1fr 34px; }
  .shelf__text { grid-column: 1; grid-row: 1; }
  .shelf__state { grid-column: 1; grid-row: 2; justify-self: start; margin-top: 4px; }
  .shelf__rm { grid-column: 2; grid-row: 1 / 3; align-self: start; }
}
""")

_ESM = (
    JS_PRELUDE
    + """
const MARKS = {
  measured: `<svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true">
      <circle cx="8" cy="8" r="7" fill="currentColor"></circle>
      <path d="M4.6 8.2 6.9 10.5 11.4 5.9" fill="none" stroke="var(--chip-bg)"
            stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"></path>
    </svg>`,
  documented: `<svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true">
      <circle cx="8" cy="8" r="6.1" fill="none" stroke="currentColor" stroke-width="1.8"></circle>
      <circle cx="8" cy="8" r="2.1" fill="currentColor"></circle>
    </svg>`,
  unknown: `<svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true">
      <circle cx="8" cy="8" r="6.1" fill="none" stroke="currentColor" stroke-width="1.8"
              stroke-dasharray="2 2.6" stroke-linecap="round"></circle>
    </svg>`,
};

const STATE_WORD = {
  measured: "Measured",
  documented: "Documented",
  unknown: "No known role",
};

const ARROW = `<svg class="pair__arrow" width="18" height="12" viewBox="0 0 18 12" aria-hidden="true">
    <path d="M1 6h14M11.5 1.8 15.8 6l-4.3 4.2" fill="none" stroke="currentColor"
          stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></path>
  </svg>`;

const CROSS = `<svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true">
    <path d="M4 4l8 8M12 4l-8 8" fill="none" stroke="currentColor"
          stroke-width="1.7" stroke-linecap="round"></path>
  </svg>`;

const SCALE_MIN = 0.1;
const SCALE_MAX = 20;
const TICKS = [0.2, 1, 5, 20];

const place = (fold) => {
  const lo = Math.log10(SCALE_MIN);
  const hi = Math.log10(SCALE_MAX);
  const at = Math.log10(Math.min(Math.max(fold, SCALE_MIN), SCALE_MAX));
  return ((at - lo) / (hi - lo)) * 100;
};

const trim = (n) => (Number.isInteger(n) ? String(n) : String(Math.round(n * 100) / 100));

const asNumber = (value) => {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
};

const bandClause = (pair) => {
  const low = asNumber(pair.fold_low);
  const high = asNumber(pair.fold_high);
  if (low === null) return "";
  if (low < 1) {
    const from = Math.round((1 - low) * 100);
    if (high !== null && high < 1) {
      const to = Math.round((1 - high) * 100);
      return `cutting exposure by ${Math.min(from, to)} to ${Math.max(from, to)} percent`;
    }
    return `cutting exposure by ${from} percent or more`;
  }
  if (high !== null) return `raising exposure ${trim(low)} to ${trim(high)} times`;
  return `raising exposure ${trim(low)} times or more`;
};

const bandMarkup = (pair) => {
  const clause = bandClause(pair);
  if (!pair.band && !clause) return "";
  if (!clause) return `<p class="pair__band"><b>${esc(pair.band)}</b></p>`;
  return `<p class="pair__band"><b>${esc(pair.band)}</b>, which FDA defines as ${esc(clause)}.</p>`;
};

const scaleMarkup = (pair) => {
  const low = asNumber(pair.fold_low);
  if (low === null) return "";
  const high = asNumber(pair.fold_high);
  const start = Math.min(place(low), high !== null ? place(high) : 100);
  const end = high !== null ? Math.max(place(low), place(high)) : 100;
  const open = high === null ? " pair__seg--open" : "";
  const ticks = TICKS
    .map((t) => `<span class="pair__tick" style="left:${place(t).toFixed(2)}%">${trim(t)}</span>`)
    .join("");
  return `
    <div class="pair__scale">
      <div class="pair__track"></div>
      <div class="pair__seg${open}" style="left:${start.toFixed(2)}%;width:${Math.max(end - start, 2).toFixed(2)}%"></div>
      <div class="pair__unity" style="left:${place(1).toFixed(2)}%"></div>
    </div>
    <div class="pair__ticks">${ticks}</div>
  `;
};

const measureMarkup = (pair, perpetrator) => {
  const value = asNumber(pair.measured_pic50);
  if (value === null) {
    return `<p class="state state--unknown pair__none">${MARKS.unknown}Not measured</p>`;
  }
  return `<p class="pair__measure">
      <span class="pair__dot" aria-hidden="true"></span>
      <span>${esc(perpetrator)} halves ${esc(pair.enzyme)} activity in a test tube at
      pIC50 <span class="pair__value">${value.toFixed(2)}</span>. A higher number means
      less of the drug was needed to do it.</span>
    </p>`;
};

const shelfMarkup = (drugs) => drugs.map((drug) => {
  const state = MARKS[drug.state] ? drug.state : "unknown";
  return `<li class="shelf__item">
      <span class="shelf__text">
        <span class="shelf__name">${esc(drug.display_name)}</span>
        <span class="shelf__sub muted">${esc(drug.sublabel)}</span>
      </span>
      <span class="state state--${state} shelf__state">${MARKS[state]}${STATE_WORD[state]}</span>
      <button class="btn-quiet shelf__rm" type="button" data-remove="${esc(drug.drug_id)}">
        ${CROSS}<span class="sr">Take ${esc(drug.display_name)} off the shelf</span>
      </button>
    </li>`;
}).join("");

const pairMarkup = (pair, nameOf) => {
  const perpetrator = nameOf(pair.perpetrator);
  return `<article class="pair card">
    <div class="pair__flow">
      <span class="pair__drug">${esc(perpetrator)}</span>
      ${ARROW}
      <span class="pill">${esc(pair.enzyme)}</span>
      ${ARROW}
      <span class="pair__drug">${esc(nameOf(pair.victim))}</span>
    </div>
    ${bandMarkup(pair)}
    ${scaleMarkup(pair)}
    ${measureMarkup(pair, perpetrator)}
    ${pair.note ? `<p class="pair__note">${esc(pair.note)}</p>` : ""}
  </article>`;
};

const emptyMarkup = (hasItems) => hasItems
  ? `<div class="cab__empty">
      <h3>No documented interaction was found</h3>
      <p>That is not a finding of safety. It means nobody has published a role for these
      ingredients in the enzyme table this notebook uses, so there is nothing here to report
      rather than nothing to worry about.</p>
      <p>Interactions that work by any route other than these enzymes are invisible to this
      shelf. Warfarin with ibuprofen returns nothing here and is genuinely dangerous.</p>
    </div>`
  : `<div class="cab__empty">
      <h3>The shelf is empty</h3>
      <p>Type the name of a medicine above, either the ingredient or the name on the box, and
      it will be looked up against the enzyme table and against the laboratory measurements.</p>
    </div>`;

const buildIndex = (catalog) => {
  const byId = new Map();
  const byAlias = new Map();
  catalog.forEach((drug) => {
    if (!drug || !drug.drug_id) return;
    byId.set(drug.drug_id, drug);
    [drug.drug_id, drug.display_name, ...(drug.aliases || [])].forEach((key) => {
      if (typeof key === "string" && key.trim()) {
        byAlias.set(key.trim().toLowerCase(), drug.drug_id);
      }
    });
  });
  return { byId, byAlias };
};

export default {
  render({ model, el, signal }) {
    const root = document.createElement("div");
    root.className = "w cab";
    root.innerHTML = `
      <section class="sect">
        <h2>Medicines on the shelf</h2>
        <form class="cab__add">
          <label class="sr" for="cab-q">Name of a medicine to add</label>
          <input class="cab__input" id="cab-q" type="text" autocomplete="off" spellcheck="false"
                 placeholder="Ingredient or the name on the box">
          <button class="btn-solid" type="submit">Add to shelf</button>
        </form>
        <p class="cab__says" role="status" hidden></p>
        <ul class="cab__shelf"></ul>
      </section>
      <section class="sect">
        <h2>Pairs that meet at an enzyme</h2>
        <p class="cab__legend" hidden>Each bar covers the fold change in exposure that FDA's
          band allows, read against the scale printed under it. The upright line sits at 1,
          where exposure does not change.</p>
        <div class="cab__pairs"></div>
      </section>
    `;
    el.appendChild(root);
    const unbindTheme = bindTheme(root, model);

    const input = root.querySelector(".cab__input");
    const says = root.querySelector(".cab__says");
    const shelfList = root.querySelector(".cab__shelf");
    const legend = root.querySelector(".cab__legend");
    const pairsBox = root.querySelector(".cab__pairs");

    let index = buildIndex(model.get("catalog") || []);
    let shelf = (model.get("shelf") || []).filter((id) => index.byId.has(id));
    let ownEdit = false;

    const nameOf = (id) => (index.byId.get(id) || {}).display_name || id;

    const tell = (message) => {
      says.hidden = !message;
      says.textContent = message || "";
    };

    const paint = () => {
      const drugs = shelf.map((id) => index.byId.get(id)).filter(Boolean);
      shelfList.innerHTML = shelfMarkup(drugs);
      shelfList.hidden = drugs.length === 0;
      const onShelf = new Set(shelf);
      const pairs = (model.get("pair_index") || [])
        .filter((pair) => onShelf.has(pair.perpetrator) && onShelf.has(pair.victim));
      legend.hidden = pairs.length === 0;
      pairsBox.innerHTML = pairs.length
        ? pairs.map((pair) => pairMarkup(pair, nameOf)).join("")
        : emptyMarkup(drugs.length > 0);
    };

    const publish = () => {
      ownEdit = true;
      model.set("shelf", shelf.slice());
      model.set("shelf_changed", (model.get("shelf_changed") || 0) + 1);
      model.save_changes();
      ownEdit = false;
    };

    paint();

    const onSubmit = (event) => {
      event.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      const id = index.byAlias.get(text.toLowerCase());
      if (!id) {
        tell(`${text} is not in this notebook's reference set, so there is nothing to look up `
             + `for it. The ingredient name printed under the brand name usually works.`);
        input.select();
        return;
      }
      if (shelf.includes(id)) {
        tell(`${nameOf(id)} is already on the shelf.`);
        input.select();
        return;
      }
      shelf = shelf.concat([id]);
      input.value = "";
      tell("");
      paint();
      publish();
    };

    const onClick = (event) => {
      const button = event.target.closest("[data-remove]");
      if (!button) return;
      shelf = shelf.filter((entry) => entry !== button.getAttribute("data-remove"));
      tell("");
      paint();
      publish();
    };

    const onShelfTrait = () => {
      if (ownEdit) return;
      shelf = (model.get("shelf") || []).filter((id) => index.byId.has(id));
      paint();
    };

    const onReference = () => {
      index = buildIndex(model.get("catalog") || []);
      shelf = shelf.filter((id) => index.byId.has(id));
      paint();
    };

    root.querySelector(".cab__add").addEventListener("submit", onSubmit, { signal });
    root.addEventListener("click", onClick, { signal });
    model.on("change:shelf", onShelfTrait);
    model.on("change:catalog", onReference);
    model.on("change:pair_index", paint);

    signal.addEventListener("abort", () => {
      unbindTheme();
      model.off("change:shelf", onShelfTrait);
      model.off("change:catalog", onReference);
      model.off("change:pair_index", paint);
      el.innerHTML = "";
    });
  },
};
"""
)


class Cabinet(anywidget.AnyWidget):
    """A shelf of medicines and the enzyme interactions between them.

    Reference set in: `catalog`, `pair_index`. Two-way: `shelf`. Counter out:
    `shelf_changed`. Appearance: `theme`.
    """

    _esm = _ESM
    _css = _CSS

    catalog = traitlets.List(traitlets.Dict()).tag(sync=True)
    pair_index = traitlets.List(traitlets.Dict()).tag(sync=True)
    shelf = traitlets.List(traitlets.Unicode()).tag(sync=True)
    shelf_changed = traitlets.Int(0).tag(sync=True)
    theme = traitlets.Unicode("").tag(sync=True)
