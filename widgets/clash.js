const FONT_URL = "https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:wght@400;600;750&display=swap";
const ENZYMES = ["CYP1A2", "CYP2C9", "CYP2D6", "CYP3A4"];
const RELIABLE_FLOOR = 4;
const HALF_LIFE_HOURS = 4;
const HOURS = 24;
const CHART_MARGIN = { left: 44, right: 16, top: 16, bottom: 34 };
const CONCENTRATION = { min: -2, max: 2 };
const FDA_BANDS = [
  { from: 1, to: 1.25, name: "No interaction by FDA's yardstick" },
  { from: 1.25, to: 2, name: "Weak interaction" },
  { from: 2, to: 5, name: "Moderate interaction" },
  { from: 5, to: Infinity, name: "Strong interaction" },
];
const SENSITIVITY_MARKS = [
  { value: 50, label: "moderate" },
  { value: 80, label: "sensitive" },
];

const CSS = `
  .clash {
    --ink: #1A2124;
    --muted: #56636A;
    --quiet: #D5DDDA;
    --surface: #F6F8F7;
    --page: #E4EAE8;
    --alone: #8A979C;
    --blocked: #B7741A;
    --blocked-wash: rgba(183, 116, 26, 0.14);
    --focus: #4F8DB8;
    --radius-control: 10px;
    --pad-card: 14px;
    --radius-card: calc(var(--radius-control) + var(--pad-card));
    --inset: 10px;
    --radius-board: calc(var(--radius-card) + var(--inset));
    --shadow: 0 1px 2px rgba(26, 33, 36, 0.08), 0 8px 24px rgba(26, 33, 36, 0.10);
    font-family: "Atkinson Hyperlegible Next", "Atkinson Hyperlegible", system-ui, sans-serif;
    color: var(--ink);
    background: var(--page);
    border-radius: var(--radius-board);
    padding: var(--inset);
    display: grid;
    gap: var(--inset);
    font-size: 1rem;
    line-height: 1.45;
  }
  .clash * { box-sizing: border-box; }
  .clash-card { background: var(--surface); border-radius: var(--radius-card); padding: var(--pad-card); box-shadow: var(--shadow); }
  .clash-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 8px 16px; }
  .clash-name { margin: 0; font-size: 1.25rem; font-weight: 750; }
  .clash-measured { margin: 0; color: var(--muted); font-size: 0.95rem; font-variant-numeric: tabular-nums; }
  .clash-measured strong { color: var(--ink); font-weight: 750; }
  .enzyme-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
  .enzyme {
    min-height: 44px;
    padding: 6px 12px;
    border: 0;
    border-radius: var(--radius-control);
    background: var(--page);
    color: var(--ink);
    font: inherit;
    font-weight: 600;
    display: inline-flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: center;
    cursor: pointer;
    font-variant-numeric: tabular-nums;
  }
  .enzyme small { font-weight: 400; color: var(--muted); font-size: 0.85rem; }
  .enzyme[aria-pressed="true"] { background: var(--ink); color: var(--surface); }
  .enzyme[aria-pressed="true"] small { color: var(--quiet); }
  .enzyme:disabled {
    cursor: not-allowed;
    color: var(--muted);
    background: repeating-linear-gradient(135deg, var(--page) 0 6px, var(--surface) 6px 12px);
  }
  .enzyme:focus-visible, .slider input:focus-visible { outline: 3px solid var(--focus); outline-offset: 2px; }
  .result { display: grid; grid-template-columns: minmax(0, 1fr); gap: 4px; }
  .fold { margin: 0; font-size: 3rem; font-weight: 750; line-height: 1; font-variant-numeric: tabular-nums; }
  .verdict { margin: 0; font-weight: 600; }
  .scale { position: relative; height: 34px; margin-top: 10px; }
  .scale-band { position: absolute; top: 0; height: 10px; }
  .scale-band:first-child { border-radius: 999px 0 0 999px; }
  .scale-band:last-of-type { border-radius: 0 999px 999px 0; }
  .scale-marker { position: absolute; top: -4px; width: 4px; height: 18px; margin-left: -2px; border-radius: 2px; background: var(--ink); }
  .scale-label { position: absolute; top: 16px; font-size: 0.8rem; color: var(--muted); transform: translateX(-50%); font-variant-numeric: tabular-nums; }
  .chart svg { display: block; width: 100%; height: auto; }
  .chart-axis { font-size: 13px; fill: var(--muted); }
  .legend { display: flex; flex-wrap: wrap; gap: 4px 16px; margin: 6px 0 0; padding: 0; list-style: none; font-size: 0.9rem; color: var(--muted); }
  .legend li { display: inline-flex; align-items: center; gap: 6px; }
  .legend i { display: inline-block; width: 18px; height: 3px; border-radius: 2px; }
  .sliders { display: grid; gap: 18px; }
  .slider { display: grid; gap: 4px; }
  .slider-top { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
  .slider label { font-weight: 600; }
  .slider output { font-weight: 750; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .slider input { width: 100%; height: 32px; margin: 0; accent-color: var(--ink); }
  .ticks { position: relative; height: 18px; font-size: 0.8rem; color: var(--muted); }
  .ticks span { position: absolute; transform: translateX(-50%); white-space: nowrap; }
  .ticks span.tick-start { transform: none; }
  .ticks span.tick-end { transform: translateX(-100%); }
  .slider-note { margin: 0; font-size: 0.9rem; color: var(--muted); }
  .empty { margin: 0; color: var(--muted); }
  .visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
  .clash-body { display: grid; gap: var(--inset); }
  @media (min-width: 720px) {
    .clash-body { grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); align-items: start; }
  }
`;

const MARKUP = `
  <div class="clash-card">
    <div class="clash-head">
      <h3 class="clash-name" data-ref="name"></h3>
      <p class="clash-measured" data-ref="measured"></p>
    </div>
    <div class="enzyme-row" role="group" aria-label="Enzyme" data-ref="enzymes"></div>
  </div>
  <div class="clash-body">
    <div class="clash-card chart">
      <div class="result" aria-live="polite">
        <p class="fold" data-ref="fold"></p>
        <p class="verdict" data-ref="verdict"></p>
        <div class="scale" data-ref="scale" aria-hidden="true"></div>
      </div>
      <svg role="img" data-ref="chart"></svg>
      <ul class="legend">
        <li><i style="background: var(--alone)"></i>The other medicine taken alone</li>
        <li><i style="background: var(--blocked)"></i>Taken with the blocker</li>
      </ul>
    </div>
    <div class="clash-card sliders">
      <div class="slider">
        <div class="slider-top">
          <label for="clash-dose">Blocker reaching the enzyme</label>
          <output for="clash-dose" data-ref="doseValue"></output>
        </div>
        <input id="clash-dose" type="range" min="${CONCENTRATION.min}" max="${CONCENTRATION.max}" step="0.01" data-ref="dose">
        <div class="ticks" data-ref="doseTicks"></div>
      </div>
      <div class="slider">
        <div class="slider-top">
          <label for="clash-share">Other medicine's clearance through this enzyme</label>
          <output for="clash-share" data-ref="shareValue"></output>
        </div>
        <input id="clash-share" type="range" min="0" max="100" step="1" data-ref="share">
        <div class="ticks" data-ref="shareTicks"></div>
      </div>
      <p class="slider-note">FDA calls a medicine moderately sensitive to an enzyme above 50% and sensitive above 80%. Neither number is in OpenADMET's files. The first depends on the dose and on how much of the drug floats free in blood. The second depends on which medicine it meets.</p>
    </div>
  </div>
`;

function ensureFont() {
  if (document.querySelector("link[data-drain-font]")) return;
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = FONT_URL;
  link.dataset.drainFont = "";
  document.head.append(link);
}

function exposureRatio(micromolar, ic50Micromolar, share) {
  return 1 / (share / (1 + micromolar / ic50Micromolar) + (1 - share));
}

function fdaBand(ratio) {
  return FDA_BANDS.find((band) => ratio < band.to) ?? FDA_BANDS[FDA_BANDS.length - 1];
}

function formatMicromolar(micromolar) {
  if (micromolar >= 10) return `${micromolar.toFixed(0)} µM`;
  if (micromolar >= 1) return `${micromolar.toFixed(1)} µM`;
  return `${micromolar.toPrecision(1)} µM`;
}

function percentAlong(log10Value) {
  return ((log10Value - CONCENTRATION.min) / (CONCENTRATION.max - CONCENTRATION.min)) * 100;
}

function measuredEnzymes(compound) {
  return ENZYMES.filter((enzyme) => Number.isFinite(compound?.pic50?.[enzyme]));
}

function potencyText(pic50) {
  if (pic50 < RELIABLE_FLOOR) return "weaker than 100 µM";
  return `IC50 ${formatMicromolar(10 ** (6 - pic50))}`;
}

function chartFrame(svg) {
  const width = Math.max(260, Math.round(svg.clientWidth || 560));
  const height = Math.round(Math.min(260, Math.max(180, width * 0.42)));
  return { ...CHART_MARGIN, width, height };
}

function curvePath(rate, frame) {
  const plotW = frame.width - frame.left - frame.right;
  const plotH = frame.height - frame.top - frame.bottom;
  const points = Array.from({ length: 97 }, (_, step) => {
    const hours = (step / 96) * HOURS;
    const level = Math.exp(-rate * hours);
    return `${(frame.left + (hours / HOURS) * plotW).toFixed(1)},${(frame.top + (1 - level) * plotH).toFixed(1)}`;
  });
  return points;
}

function axisMarkup(frame) {
  const plotW = frame.width - frame.left - frame.right;
  const baseY = frame.height - frame.bottom;
  const ticks = [0, 6, 12, 18, 24].map((hours) => {
    const x = frame.left + (hours / HOURS) * plotW;
    return `<text class="chart-axis" x="${x}" y="${baseY + 18}" text-anchor="middle">${hours} h</text>`;
  });
  return `
    <line x1="${frame.left}" y1="${baseY}" x2="${frame.width - frame.right}" y2="${baseY}" stroke="var(--quiet)" stroke-width="1.5"/>
    <text class="chart-axis" x="${frame.left - 8}" y="${frame.top + 4}" text-anchor="end">100%</text>
    <text class="chart-axis" x="${frame.left - 8}" y="${baseY}" text-anchor="end">0</text>
    ${ticks.join("")}`;
}

function chartMarkup(ratio, frame) {
  const rate = Math.LN2 / HALF_LIFE_HOURS;
  const alone = curvePath(rate, frame);
  const blocked = curvePath(rate / ratio, frame);
  const baseY = frame.height - frame.bottom;
  const area = `M${frame.left},${baseY} L${blocked.join(" L")} L${frame.width - frame.right},${baseY} Z`;
  return `${axisMarkup(frame)}
    <path d="${area}" fill="var(--blocked-wash)"/>
    <polyline points="${alone.join(" ")}" fill="none" stroke="var(--alone)" stroke-width="2.5" stroke-dasharray="6 5"/>
    <polyline points="${blocked.join(" ")}" fill="none" stroke="var(--blocked)" stroke-width="3"/>`;
}

function scaleMarkup(ratio) {
  const toPercent = (value) => (Math.log10(Math.min(value, 10)) / Math.log10(10)) * 100;
  const shades = ["#CFD8D5", "#E9D3AE", "#DDB173", "#C48A3A"];
  const bands = FDA_BANDS.map((band, index) => {
    const left = toPercent(band.from);
    const right = toPercent(Math.min(band.to, 10));
    return `<span class="scale-band" style="left:${left}%;width:${right - left}%;background:${shades[index]}"></span>`;
  });
  const labels = [1, 1.25, 2, 5, 10].map((value) => `<span class="scale-label" style="left:${toPercent(value)}%">${value}×</span>`);
  return `${bands.join("")}<span class="scale-marker" style="left:${toPercent(ratio)}%"></span>${labels.join("")}`;
}

function ticksMarkup(marks) {
  return marks.map(({ at, label }) => {
    const edge = at <= 2 ? " tick-start" : at >= 98 ? " tick-end" : "";
    return `<span class="${edge.trim()}" style="left:${at}%">${label}</span>`;
  }).join("");
}

function render({ model, el }) {
  ensureFont();
  const root = document.createElement("div");
  root.className = "clash";
  root.innerHTML = `<style>${CSS}</style>${MARKUP}`;
  el.append(root);
  const ref = Object.fromEntries([...root.querySelectorAll("[data-ref]")].map((node) => [node.dataset.ref, node]));
  const view = { enzyme: null, dose: 0, share: 80 };
  ref.dose.value = String(view.dose);
  ref.share.value = String(view.share);
  ref.shareTicks.innerHTML = ticksMarkup(SENSITIVITY_MARKS.map(({ value, label }) => ({ at: value, label })));

  function sizeChart() {
    const frame = chartFrame(ref.chart);
    ref.chart.setAttribute("viewBox", `0 0 ${frame.width} ${frame.height}`);
    return frame;
  }

  function compound() {
    return model.get("compound") ?? {};
  }

  function pickEnzyme() {
    const measured = measuredEnzymes(compound());
    if (!measured.includes(view.enzyme)) view.enzyme = measured.at(-1) ?? null;
  }

  function renderEnzymes() {
    const current = compound();
    ref.enzymes.innerHTML = ENZYMES.map((enzyme) => {
      const pic50 = current.pic50?.[enzyme];
      const measured = Number.isFinite(pic50);
      const detail = measured ? `pIC50 ${pic50.toFixed(2)}` : "not measured";
      return `<button type="button" class="enzyme" data-enzyme="${enzyme}" aria-pressed="${enzyme === view.enzyme}" ${measured ? "" : "disabled"}>${enzyme}<small>${detail}</small></button>`;
    }).join("");
  }

  function renderEmpty() {
    ref.fold.textContent = "–";
    ref.verdict.textContent = "OpenADMET has no potency for this compound against any of the four enzymes.";
    ref.scale.innerHTML = "";
    ref.chart.innerHTML = axisMarkup(sizeChart());
    ref.doseTicks.innerHTML = "";
  }

  function renderModel() {
    const pic50 = compound().pic50[view.enzyme];
    const censored = pic50 < RELIABLE_FLOOR;
    const ic50 = 10 ** (6 - Math.max(pic50, RELIABLE_FLOOR));
    const micromolar = 10 ** view.dose;
    const ratio = exposureRatio(micromolar, ic50, view.share / 100);
    ref.fold.textContent = `${censored ? "at most " : ""}${ratio.toFixed(ratio < 10 ? 2 : 1)}×`;
    ref.verdict.textContent = `${fdaBand(ratio).name}: the other medicine's exposure is ${ratio.toFixed(1)} times what it is alone.`;
    ref.scale.innerHTML = scaleMarkup(ratio);
    ref.chart.innerHTML = chartMarkup(ratio, sizeChart());
    ref.chart.setAttribute("aria-label", `Blood level of a medicine with a ${HALF_LIFE_HOURS}-hour half-life, alone and with the blocker. The area under the blocked curve is ${ratio.toFixed(1)} times larger.`);
    const ic50Mark = { at: percentAlong(Math.log10(ic50)), label: censored ? "100 µM, the reliable limit" : `IC50, half blocked` };
    const ends = [{ at: 0, label: "0.01 µM" }, { at: 100, label: "100 µM" }];
    ref.doseTicks.innerHTML = ticksMarkup(ic50Mark.at > 12 && ic50Mark.at < 88 ? [ends[0], ic50Mark, ends[1]] : ends);
  }

  function renderAll() {
    pickEnzyme();
    const current = compound();
    ref.name.textContent = current.name ?? "Pick a compound";
    ref.measured.innerHTML = view.enzyme ? `Measured against ${view.enzyme}: <strong>${potencyText(current.pic50[view.enzyme])}</strong>` : "";
    ref.doseValue.textContent = formatMicromolar(10 ** view.dose);
    ref.shareValue.textContent = `${view.share}%`;
    renderEnzymes();
    if (view.enzyme) renderModel();
    else renderEmpty();
  }

  ref.enzymes.addEventListener("click", (event) => {
    const button = event.target.closest("[data-enzyme]");
    if (!button || button.disabled) return;
    view.enzyme = button.dataset.enzyme;
    renderAll();
  });
  ref.dose.addEventListener("input", () => {
    view.dose = Number(ref.dose.value);
    renderAll();
  });
  ref.share.addEventListener("input", () => {
    view.share = Number(ref.share.value);
    renderAll();
  });
  const onCompound = () => {
    view.enzyme = null;
    renderAll();
  };
  model.on("change:compound", onCompound);
  const resizeObserver = new ResizeObserver(() => renderAll());
  resizeObserver.observe(ref.chart);
  renderAll();
  return () => {
    model.off("change:compound", onCompound);
    resizeObserver.disconnect();
  };
}

export default { render };
