"""The gate: what a drug interaction looks like while it is happening.

A tablet dissolves at the left, its molecules drift down into the bloodstream
and flow toward a liver enzyme drawn as a row of chambers. A chamber catches a
molecule, holds it for a moment, and releases it on the far side as something
different, which is the whole of what metabolism is. Park a second drug in some
of those chambers and it never leaves, so traffic queues against the wall and
the level in the vessel climbs past the line where it would otherwise sit.

Everything runs in JavaScript on one canvas, so the picture keeps moving in a
static export with no kernel behind it. Python supplies the figures printed
beside it through `readout` and can drive `blockade` and `dose_interval_hours`,
which the reader also drives from the controls.

Cost control, because this animates continuously: one canvas, at most 170
circles and their short trails per frame, the loop stops when the widget
scrolls out of view or the tab is hidden, and a reader who asks for reduced
motion gets a settled still frame instead of an animation.
"""

import anywidget
import traitlets

from ._theme import JS_PRELUDE, stylesheet

_CSS = stylesheet("""
.gate__stage {
  background: var(--card);
  border-radius: var(--r-outer);
  box-shadow: var(--lift);
  padding: 8px;
  margin-bottom: 14px;
}

.gate__canvas { display: block; width: 100%; height: auto; border-radius: 8px; }

.gate__controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
  gap: 16px;
  align-items: end;
  margin-bottom: 18px;
}

.gate__field { display: grid; gap: 1px; min-width: 0; }
.gate__field label { font-size: 13px; color: var(--ink-2); }
.gate__value {
  font-family: var(--num);
  font-variant-numeric: tabular-nums;
  color: var(--ink);
  font-weight: 600;
}

.gate__slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 34px;
  background: none;
  cursor: pointer;
}

.gate__slider::-webkit-slider-runnable-track {
  height: 8px;
  border-radius: var(--r-pill);
  background: var(--sunk);
}

.gate__slider::-moz-range-track {
  height: 8px;
  border-radius: var(--r-pill);
  background: var(--sunk);
}

.gate__slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 22px;
  height: 22px;
  margin-top: -7px;
  border-radius: 50%;
  background: var(--ink);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.32);
}

.gate__slider::-moz-range-thumb {
  width: 22px;
  height: 22px;
  border: 0;
  border-radius: 50%;
  background: var(--ink);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.32);
}

.gate__readout { display: grid; gap: 10px; }
.gate__figures { display: flex; flex-wrap: wrap; gap: 10px 30px; }
.gate__figure { display: grid; gap: 1px; }
.gate__figure dt { font-size: 13px; color: var(--ink-2); }
.gate__figure dd {
  margin: 0;
  font-family: var(--num);
  font-variant-numeric: tabular-nums;
  font-size: 20px;
  font-weight: 600;
}

.gate__caption { font-size: 13.5px; color: var(--ink-2); max-width: 70ch; }

@container (max-width: 520px) {
  .gate__controls { grid-template-columns: minmax(0, 1fr); align-items: stretch; }
}
""")

_ESM = (
    JS_PRELUDE
    + """
const LANES = 5;
const LANE_ORDER = [2, 0, 4, 1, 3];
const MAX_BODIES = 150;
const DOSE_SIZE = 15;
const EMIT_PER_SECOND = 7;
const HOURS_PER_SECOND = 3;
const LEVEL_FULL = 110;
const OPEN_GATE_LEVEL = 0.29;
const HOLD_SECONDS = 0.6;
const TAIL_POINTS = 5;

const css = (root, name) => getComputedStyle(root).getPropertyValue(name).trim();

const readPalette = (root) => ({
  ink: css(root, "--ink"),
  ink2: css(root, "--ink-2"),
  ink3: css(root, "--ink-3"),
  sunk: css(root, "--sunk"),
  card: css(root, "--card"),
  accent: css(root, "--accent"),
  accentSoft: css(root, "--accent-soft"),
  hair: css(root, "--hair"),
  ui: css(root, "--ui"),
});

const layout = (w, h) => {
  const top = h * 0.05;
  const bottom = h * 0.84;
  const vesselLeft = w * 0.17;
  const gateX = w * 0.655;
  const gateW = Math.max(22, w * 0.062);
  return {
    w, h, top, bottom,
    height: bottom - top,
    vesselLeft,
    gateX, gateW,
    exitX: gateX + gateW,
    laneH: (bottom - top) / LANES,
    tabletX: w * 0.082,
    tabletY: h * 0.36,
  };
};

const laneCentre = (geo, lane) => geo.top + (lane + 0.5) * geo.laneH;

const makeSlots = () => Array.from({ length: LANES }, () => ({
  blocked: false, blockerIn: 0, occupant: null, until: 0, flash: 0,
}));

const setBlockade = (slots, blockade) => {
  const want = Math.round(Math.min(Math.max(blockade, 0), 1) * LANES);
  const chosen = new Set(LANE_ORDER.slice(0, want));
  slots.forEach((slot, lane) => { slot.blocked = chosen.has(lane); });
};

const newBody = (geo) => ({
  x: geo.tabletX + 14 + (Math.random() - 0.5) * 8,
  y: geo.tabletY + (Math.random() - 0.5) * 12,
  vx: 46 + Math.random() * 30,
  vy: 26 + Math.random() * 26,
  r: 2.6 + Math.random() * 1.6,
  speed: 38 + Math.random() * 26,
  wobble: Math.random() * Math.PI * 2,
  drift: 0.1 + Math.random() * 0.8,
  lane: null,
  phase: "falling",
  tail: [],
});

const shortestLane = (slots, queues) => {
  let best = null;
  let bestCost = Infinity;
  for (let lane = 0; lane < LANES; lane += 1) {
    const cost = slots[lane].blocked ? 999 + queues[lane] : queues[lane];
    if (cost < bestCost) { bestCost = cost; best = lane; }
  }
  return best;
};

const advance = (state, geo, dt, now) => {
  const { slots } = state;
  const queues = new Array(LANES).fill(0);
  for (const body of state.bodies) {
    if (body.phase === "queued" && body.lane !== null) queues[body.lane] += 1;
  }

  const surfaceY = geo.bottom - Math.max(state.level, 0.12) * geo.height;
  const keep = [];

  for (const body of state.bodies) {
    body.tail.push(body.x, body.y);
    while (body.tail.length > TAIL_POINTS * 2) body.tail.splice(0, 2);

    if (body.phase === "falling") {
      body.vy += 40 * dt;
      body.x += body.vx * dt;
      body.y += body.vy * dt;
      if (body.x >= geo.vesselLeft + 4 || body.y >= geo.bottom - 12) {
        body.phase = "flowing";
        body.x = Math.max(body.x, geo.vesselLeft + 4);
        body.y = Math.min(Math.max(body.y, surfaceY + 9), geo.bottom - 10);
        body.vy = 0;
      }
    } else if (body.phase === "flowing") {
      body.wobble += dt * 2.4;
      const nearGate = body.x > geo.vesselLeft + (geo.gateX - geo.vesselLeft) * 0.45;
      if (nearGate && body.lane === null) body.lane = shortestLane(slots, queues);
      const targetY = body.lane === null
        ? surfaceY + 9 + body.drift * Math.max(10, geo.bottom - 9 - (surfaceY + 9))
        : laneCentre(geo, body.lane);
      body.y += (targetY - body.y) * Math.min(1, dt * 3.2)
        + Math.sin(body.wobble) * 14 * dt;
      body.x += body.speed * dt;
      if (body.y < surfaceY + 5) body.y = surfaceY + 5;
      if (body.y > geo.bottom - 5) body.y = geo.bottom - 5;
      if (body.x + body.r >= geo.gateX - 2) {
        const slot = slots[body.lane];
        if (slot && !slot.blocked && slot.occupant === null) {
          slot.occupant = body;
          slot.until = now + HOLD_SECONDS;
          slot.flash = 1;
          body.phase = "held";
          body.tail.length = 0;
          body.x = geo.gateX + geo.gateW / 2;
          body.y = laneCentre(geo, body.lane);
        } else {
          body.phase = "queued";
          queues[body.lane] += 1;
        }
      }
    } else if (body.phase === "queued") {
      const slot = slots[body.lane];
      const place = queues[body.lane];
      const restX = geo.gateX - 5 - (place - 1) * 7.2;
      body.x += (restX - body.x) * Math.min(1, dt * 6);
      body.y += (laneCentre(geo, body.lane) - body.y) * Math.min(1, dt * 4)
        + Math.sin(now * 2 + body.wobble) * 6 * dt;
      if (slot && !slot.blocked && slot.occupant === null && place === 1) {
        slot.occupant = body;
        slot.until = now + HOLD_SECONDS;
        slot.flash = 1;
        body.phase = "held";
        body.tail.length = 0;
        body.x = geo.gateX + geo.gateW / 2;
      }
    } else if (body.phase === "held") {
      body.tail.length = 0;
    } else {
      body.x += 95 * dt;
      body.y += Math.sin(now * 3 + body.wobble) * 10 * dt;
      if (body.x > geo.w + 14) continue;
    }
    keep.push(body);
  }

  for (const slot of slots) {
    slot.flash = Math.max(0, slot.flash - dt * 3);
    slot.blockerIn += ((slot.blocked ? 1 : 0) - slot.blockerIn) * Math.min(1, dt * 5);
    if (slot.occupant && now >= slot.until) {
      slot.occupant.phase = "spent";
      slot.occupant.x = geo.exitX + 2;
      slot.occupant = null;
    }
    if (slot.blocked && slot.occupant) {
      slot.occupant.phase = "spent";
      slot.occupant.tail.length = 0;
      slot.occupant = null;
    }
  }

  state.bodies = keep;
  const inBody = keep.filter(
    (b) => b.phase === "flowing" || b.phase === "queued" || b.phase === "falling").length;
  const target = Math.min(inBody / LEVEL_FULL, 1);
  state.level += (target - state.level) * Math.min(1, dt * 1.5);
};

const roundedRect = (ctx, x, y, w, h, r) => {
  const radius = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + w, y, x + w, y + h, radius);
  ctx.arcTo(x + w, y + h, x, y + h, radius);
  ctx.arcTo(x, y + h, x, y, radius);
  ctx.arcTo(x, y, x + w, y, radius);
  ctx.closePath();
};

const hexagon = (ctx, cx, cy, r) => {
  ctx.beginPath();
  for (let i = 0; i < 6; i += 1) {
    const a = (Math.PI / 3) * i - Math.PI / 6;
    const px = cx + Math.cos(a) * r;
    const py = cy + Math.sin(a) * r;
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }
  ctx.closePath();
};

const drawTablet = (ctx, geo, pal, pulse) => {
  ctx.save();
  ctx.translate(geo.tabletX, geo.tabletY);
  ctx.rotate(-0.22);
  ctx.fillStyle = pal.ink2;
  roundedRect(ctx, -17, -10, 34, 20, 10);
  ctx.fill();
  ctx.strokeStyle = pal.card;
  ctx.lineWidth = 1.4;
  ctx.beginPath();
  ctx.moveTo(-9, 0);
  ctx.lineTo(9, 0);
  ctx.stroke();
  if (pulse > 0) {
    ctx.strokeStyle = pal.ink3;
    ctx.globalAlpha = pulse * 3;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.ellipse(0, 0, 24 + (1 - pulse * 3) * 12, 15 + (1 - pulse * 3) * 8, 0, 0, Math.PI * 2);
    ctx.stroke();
    ctx.globalAlpha = 1;
  }
  ctx.restore();
};

const drawVessel = (ctx, geo, pal, level) => {
  const width = geo.gateX - geo.vesselLeft;
  ctx.fillStyle = pal.sunk;
  roundedRect(ctx, geo.vesselLeft, geo.top, width, geo.height, 14);
  ctx.fill();

  const surfaceY = geo.bottom - Math.max(level, 0.12) * geo.height;
  const referenceY = geo.bottom - OPEN_GATE_LEVEL * geo.height;

  ctx.save();
  roundedRect(ctx, geo.vesselLeft, geo.top, width, geo.height, 14);
  ctx.clip();

  ctx.fillStyle = pal.ink;
  ctx.globalAlpha = 0.16;
  ctx.fillRect(geo.vesselLeft, surfaceY, width, geo.bottom - surfaceY);
  ctx.globalAlpha = 1;

  // the excess over where the level would sit with the gate open, which is the
  // one thing this picture exists to show
  if (surfaceY < referenceY - 1) {
    ctx.strokeStyle = pal.accent;
    ctx.globalAlpha = 0.28;
    ctx.lineWidth = 1.4;
    for (let x = geo.vesselLeft - geo.height; x < geo.gateX + 4; x += 11) {
      ctx.beginPath();
      ctx.moveTo(x, referenceY);
      ctx.lineTo(x + (referenceY - surfaceY), surfaceY);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = pal.accent;
    ctx.fillRect(geo.vesselLeft, surfaceY, width, 3);
  } else {
    ctx.fillStyle = pal.ink2;
    ctx.fillRect(geo.vesselLeft, surfaceY, width, 2.5);
  }

  ctx.strokeStyle = pal.ink3;
  ctx.setLineDash([5, 4]);
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(geo.vesselLeft, referenceY);
  ctx.lineTo(geo.gateX, referenceY);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.restore();

  ctx.fillStyle = pal.ink2;
  ctx.textAlign = "right";
  ctx.fillText("level with the gate open", geo.gateX - 10, referenceY + 15);
  ctx.textAlign = "left";
};

const drawEnzyme = (ctx, geo, pal, slots, now) => {
  ctx.fillStyle = pal.ink2;
  roundedRect(ctx, geo.gateX, geo.top - 7, geo.gateW, geo.height + 14, 9);
  ctx.fill();
  for (let lane = 0; lane < LANES; lane += 1) {
    const y = geo.top + lane * geo.laneH;
    const slot = slots[lane];
    ctx.fillStyle = pal.card;
    roundedRect(ctx, geo.gateX + 3, y + 3.5, geo.gateW - 6, geo.laneH - 7, 5);
    ctx.fill();
    if (slot.flash > 0) {
      ctx.strokeStyle = pal.ink2;
      ctx.globalAlpha = slot.flash;
      ctx.lineWidth = 2;
      roundedRect(ctx, geo.gateX + 3, y + 3.5, geo.gateW - 6, geo.laneH - 7, 5);
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
    if (slot.blockerIn > 0.02) {
      const cx = geo.gateX + geo.gateW / 2;
      const cy = laneCentre(geo, lane) - (1 - slot.blockerIn) * 40;
      ctx.globalAlpha = Math.min(1, slot.blockerIn * 1.4);
      ctx.fillStyle = pal.accent;
      hexagon(ctx, cx, cy, Math.min(9, geo.laneH * 0.3));
      ctx.fill();
      ctx.globalAlpha = 1;
    }
  }
  ctx.fillStyle = pal.ink2;
  ctx.textAlign = "center";
  ctx.fillText("liver enzyme", geo.gateX + geo.gateW / 2, geo.bottom + 26);
  ctx.textAlign = "left";
};

const drawBodies = (ctx, geo, pal, bodies) => {
  ctx.lineCap = "round";
  for (const body of bodies) {
    if (body.phase === "spent") {
      ctx.globalAlpha = Math.max(0, 1 - (body.x - geo.exitX) / (geo.w - geo.exitX));
      ctx.strokeStyle = pal.ink2;
      ctx.lineWidth = 1.6;
      ctx.save();
      ctx.translate(body.x, body.y);
      ctx.rotate(Math.PI / 4);
      ctx.strokeRect(-body.r, -body.r, body.r * 2, body.r * 2);
      ctx.restore();
      ctx.globalAlpha = 1;
      continue;
    }
    if (body.tail.length >= 4) {
      ctx.strokeStyle = pal.ink3;
      ctx.globalAlpha = 0.4;
      ctx.lineWidth = body.r * 0.85;
      ctx.beginPath();
      let px = body.tail[0];
      let py = body.tail[1];
      ctx.moveTo(px, py);
      for (let i = 2; i <= body.tail.length; i += 2) {
        const qx = i === body.tail.length ? body.x : body.tail[i];
        const qy = i === body.tail.length ? body.y : body.tail[i + 1];
        if (Math.abs(qx - px) > 26 || Math.abs(qy - py) > 26) ctx.moveTo(qx, qy);
        else ctx.lineTo(qx, qy);
        px = qx; py = qy;
      }
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
    ctx.fillStyle = pal.ink;
    ctx.beginPath();
    ctx.arc(body.x, body.y, body.r, 0, Math.PI * 2);
    ctx.fill();
  }
};

const drawScene = (ctx, geo, pal, state, now) => {
  ctx.clearRect(0, 0, geo.w, geo.h);
  ctx.font = `12px ${pal.ui}`;
  ctx.textBaseline = "alphabetic";
  drawVessel(ctx, geo, pal, state.level);
  drawTablet(ctx, geo, pal, state.pulse);
  drawBodies(ctx, geo, pal, state.bodies);
  drawEnzyme(ctx, geo, pal, state.slots, now);
};

const figure = (label, value, unit) => `<div class="gate__figure"><dt>${esc(label)}</dt>
  <dd>${esc(String(value))} ${esc(unit)}</dd></div>`;

// The figures are derived here as well as in Python, so they stay correct in a
// static export where no kernel is listening. Python's readout wins whenever it
// describes the blockade currently on screen.
const derive = (blockade) => {
  const working = Math.max(1 - blockade, 0.05);
  const steady = 1 / working;
  const caption = blockade < 0.05
    ? "Nothing is blocking the exit. Each dose clears before the next one arrives, so the amount in the blood holds steady."
    : `With ${Math.round(blockade * 100)}% of the enzyme occupied, the drug leaves ${steady.toFixed(1)} times more slowly, and the amount in the blood settles at ${steady.toFixed(1)} times what the prescription intended.`;
  return {
    steady_state_multiple: Number(steady.toFixed(2)),
    half_life_hours: Number((6 / working).toFixed(1)),
    caption,
  };
};

const readoutMarkup = (readout, blockade) => {
  const local = derive(blockade);
  const fromPython = readout && readout.blockade !== undefined
    && Math.abs(readout.blockade - blockade) < 0.005;
  const source = fromPython ? readout : local;
  const steady = source.steady_state_multiple;
  const half = source.half_life_hours;
  const caption = source.caption || "";
  const parts = [];
  if (steady !== undefined && steady !== null && steady !== "") {
    parts.push(figure("Drug in the blood, once it settles", steady, "times"));
  }
  if (half !== undefined && half !== null && half !== "") {
    parts.push(figure("Time to clear half of a dose", half, "hours"));
  }
  return `${parts.length ? `<dl class="gate__figures">${parts.join("")}</dl>` : ""}
    ${caption ? `<p class="gate__caption">${esc(caption)}</p>` : ""}`;
};

export default {
  render({ model, el, signal }) {
    const root = document.createElement("div");
    root.className = "w gate";
    root.innerHTML = `
      <section class="sect">
        <h2>What the interaction does while it is happening</h2>
        <div class="gate__stage"><canvas class="gate__canvas"></canvas></div>
        <div class="gate__controls">
          <div class="gate__field">
            <label for="gate-block">Share of the enzyme a second drug is sitting in,
              <span class="gate__value" id="gate-block-value">0 percent</span></label>
            <input class="gate__slider" id="gate-block" type="range" min="0" max="100" step="20">
          </div>
          <div class="gate__field">
            <label for="gate-dose">Hours between doses,
              <span class="gate__value" id="gate-dose-value">12</span></label>
            <input class="gate__slider" id="gate-dose" type="range" min="4" max="24" step="2">
          </div>
          <button class="btn-solid gate__play" type="button">Pause</button>
        </div>
        <div class="gate__readout"></div>
      </section>
    `;
    el.appendChild(root);
    const unbindTheme = bindTheme(root, model);

    const stage = root.querySelector(".gate__stage");
    const canvas = root.querySelector(".gate__canvas");
    const ctx = canvas.getContext("2d");
    const blockSlider = root.querySelector("#gate-block");
    const blockValue = root.querySelector("#gate-block-value");
    const doseSlider = root.querySelector("#gate-dose");
    const doseValue = root.querySelector("#gate-dose-value");
    const playButton = root.querySelector(".gate__play");
    const readBox = root.querySelector(".gate__readout");

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    let pal = readPalette(root);
    let geo = layout(600, 300);
    const state = { bodies: [], slots: makeSlots(), level: OPEN_GATE_LEVEL,
                    pulse: 0, clock: 0, pending: DOSE_SIZE, emitting: 0 };
    let sinceDose = 0;
    let raf = null;
    let last = 0;
    let onScreen = true;
    let saveTimer = null;

    const blockade = () => Number(model.get("blockade")) || 0;
    const interval = () => Number(model.get("dose_interval_hours")) || 12;
    const wanted = () => model.get("playing") !== false && onScreen
      && !document.hidden && !reduced.matches;

    const resize = () => {
      const width = Math.max(280, stage.clientWidth - 16);
      const height = Math.round(Math.min(340, Math.max(215, width * 0.46)));
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      geo = layout(width, height);
    };

    const tick = (dt) => {
      state.clock += dt;
      setBlockade(state.slots, blockade());
      sinceDose += dt * HOURS_PER_SECOND;
      if (sinceDose >= interval()) {
        sinceDose = 0;
        state.pulse = 0.33;
        state.pending += DOSE_SIZE;
      }
      // A tablet does not arrive as a burst, it dissolves, so the pool it left
      // behind trickles in and the stream never goes empty between doses.
      state.emitting += Math.min(state.pending, EMIT_PER_SECOND * dt);
      while (state.emitting >= 1 && state.pending > 0) {
        state.emitting -= 1;
        state.pending -= 1;
        if (state.bodies.length < MAX_BODIES) state.bodies.push(newBody(geo));
      }
      state.pulse = Math.max(0, state.pulse - dt);
      advance(state, geo, dt, state.clock);
    };

    const paintOnce = () => drawScene(ctx, geo, pal, state, state.clock);

    const settle = () => {
      // Someone who asked for less motion still gets the outcome: run the model
      // forward to where the level stops moving, then draw one still frame.
      for (let i = 0; i < 1100; i += 1) tick(1 / 60);
      paintOnce();
    };

    const frame = (now) => {
      if (!wanted()) { raf = null; return; }
      const dt = Math.min(0.05, (now - last) / 1000 || 0.016);
      last = now;
      tick(dt);
      paintOnce();
      raf = requestAnimationFrame(frame);
    };

    const run = () => {
      if (raf !== null) return;
      if (!wanted()) { if (reduced.matches) settle(); return; }
      last = performance.now();
      raf = requestAnimationFrame(frame);
    };

    const stop = () => {
      if (raf !== null) cancelAnimationFrame(raf);
      raf = null;
    };

    const paintControls = () => {
      const percent = Math.round(blockade() * 100);
      blockSlider.value = String(percent);
      blockValue.textContent = `${percent} percent`;
      doseSlider.value = String(interval());
      doseValue.textContent = String(interval());
      const playing = model.get("playing") !== false;
      playButton.textContent = playing ? "Pause" : "Play";
    };

    const paintReadout = () => {
      readBox.innerHTML = readoutMarkup(model.get("readout"), blockade());
    };

    const push = () => {
      clearTimeout(saveTimer);
      saveTimer = setTimeout(() => model.save_changes(), 180);
    };

    resize();
    setBlockade(state.slots, blockade());
    paintControls();
    paintReadout();
    paintOnce();
    run();

    const observer = new ResizeObserver(() => { resize(); if (raf === null) paintOnce(); });
    observer.observe(stage);

    const watcher = new IntersectionObserver((entries) => {
      onScreen = entries.some((entry) => entry.isIntersecting);
      if (onScreen) run(); else stop();
    }, { threshold: 0.01 });
    watcher.observe(stage);

    const onHidden = () => (document.hidden ? stop() : run());
    const onScheme = () => { pal = readPalette(root); if (raf === null) paintOnce(); };
    const onReduced = () => { stop(); if (reduced.matches) settle(); else run(); };

    blockSlider.addEventListener("input", () => {
      model.set("blockade", Number(blockSlider.value) / 100);
      paintControls();
      setBlockade(state.slots, blockade());
      if (raf === null) { if (reduced.matches) settle(); else paintOnce(); }
      push();
    }, { signal });

    doseSlider.addEventListener("input", () => {
      model.set("dose_interval_hours", Number(doseSlider.value));
      paintControls();
      if (raf === null && reduced.matches) settle();
      push();
    }, { signal });

    playButton.addEventListener("click", () => {
      model.set("playing", model.get("playing") === false);
      model.save_changes();
      paintControls();
      if (model.get("playing") !== false) run(); else stop();
    }, { signal });

    document.addEventListener("visibilitychange", onHidden, { signal });
    reduced.addEventListener("change", onReduced, { signal });

    model.on("change:blockade", paintControls);
    model.on("change:dose_interval_hours", paintControls);
    model.on("change:playing", paintControls);
    model.on("change:readout", paintReadout);
    model.on("change:blockade", paintReadout);
    model.on("change:theme", onScheme);

    signal.addEventListener("abort", () => {
      stop();
      clearTimeout(saveTimer);
      observer.disconnect();
      watcher.disconnect();
      unbindTheme();
      model.off("change:blockade", paintControls);
      model.off("change:dose_interval_hours", paintControls);
      model.off("change:playing", paintControls);
      model.off("change:readout", paintReadout);
      model.off("change:theme", onScheme);
      el.innerHTML = "";
    });
  },
};
"""
)


class Gate(anywidget.AnyWidget):
    """An animated picture of one drug blocking another drug's way out.

    Two-way: `blockade`, `dose_interval_hours`, `playing`. In from Python:
    `readout`, `theme`.
    """

    _esm = _ESM
    _css = _CSS

    blockade = traitlets.Float(0.0).tag(sync=True)
    dose_interval_hours = traitlets.Float(12.0).tag(sync=True)
    readout = traitlets.Dict().tag(sync=True)
    playing = traitlets.Bool(True).tag(sync=True)
    theme = traitlets.Unicode("").tag(sync=True)
