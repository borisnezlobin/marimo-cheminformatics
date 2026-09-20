/* The art of the ADMET run: one 2D canvas, drawn from code, no assets.
 *
 * The scene is a stylised anatomical cross-section seen from the side. A
 * swallowed compound dissolves in the stomach at the left, crosses the gut
 * wall, meets a mechanism set into the liver, drifts through a vessel full of
 * plasma proteins, and reaches a target at the right. Everything is one
 * continuous space, so the molecule never teleports between panels.
 *
 * The engine owns the state and calls `render(state, dt)` once a frame. This
 * file owns every pixel and computes no chemistry.
 *
 * ONE PALETTE. The scene is dark whatever the notebook around it is set to. A
 * running game owns its surface, and the molecule only reads as a light source
 * against a dark body. The colours still come from CSS custom properties in
 * _theme.py, so nothing is written twice and nothing is hard-coded here.
 *
 * COORDINATES. `state.molecules[].x` and `.y` are normalised scene space:
 * x runs 0 at the mouth to 1 past the target, y runs 0 at the top of the
 * canvas to 1 at the bottom. `SCENE.landmarks` gives the x of each station and
 * `SCENE.channel` gives the line the vessel runs along, so an engine can path a
 * molecule through the scene without knowing the pixel layout. Pixel
 * coordinates are also accepted: any molecule with |x| above 1.5 is read as
 * pixels.
 *
 * HIT TEST. `hitTest(x, y)` takes canvas CSS pixels and returns, in priority
 * order, `molecule:<index>`, `protein:<index>`, `banner`, `gate:dissolve`,
 * `gate:gut`, `gate:liver`, `gate:binding`, `gate:target`, `patient`, or null.
 * In the safety ward (`state.ward === "safety"`) it returns `dial`,
 * `enzyme:<0-3>`, `medicine:<0-3>`, or null.
 *
 * TWO SCENES. The travelling wards get the journey: stomach, gut wall, efflux
 * pump, liver mechanism, plasma proteins, target. The safety ward gets the
 * patient instead, with one door per liver enzyme, the medicine that leaves
 * through each one, and the induction throttle. `state.ward` picks between
 * them and the renderer rebakes its background when it changes.
 *
 * SHARED SHAPES. `drawStationGlyph` and `drawJourneyStrip` draw the same
 * silhouettes the scene uses, at card size, so a shape learnt on a compound
 * card is recognised in the scene. They key off the data build's gate ids.
 *
 * COST. The environment is baked into an offscreen canvas once per size and
 * theme, so a frame is one image blit plus a few hundred small paths. No
 * shadowBlur in the loop except the banner; glows are pre-rendered sprites.
 * Particle and body counts fall at narrow widths.
 */

export const SCENE = {
  landmarks: {
    mouth: 0.045,
    stomach: 0.095,
    gutWall: 0.205,
    portal: 0.30,
    liverGate: 0.44,
    blood: 0.64,
    targetEntry: 0.80,
    target: 0.885,
  },
  channel: { y: 0.545, halfHeight: 0.185 },
};

const PALETTE_KEYS = [
  "void", "tissue-far", "tissue-mid", "tissue-near", "lumen", "wall",
  "wall-edge", "membrane", "blood", "blood-deep", "blood-cell", "plasma",
  "organ", "organ-deep", "metal", "metal-edge", "metal-dark", "drug",
  "drug-core", "drug-dim", "foreign", "foreign-deep", "foreign-lit", "hazard",
  "grain", "vignette", "line", "line-lit", "skin", "bone", "surface",
];

const TAU = Math.PI * 2;

const PARALLAX = 22;

const clamp = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);
const lerp = (a, b, t) => a + (b - a) * t;
const ease = (t) => t * t * (3 - 2 * t);

/* A small deterministic generator, so the scene is identical on every reload
 * and nothing pops when the widget is re-mounted. */
export function makeRandom(seed) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}

/* Colour comes from CSS custom properties so light and dark are one source of
 * truth in _theme.py. Nothing here invents a colour. */
export function readPalette(el) {
  const cs = getComputedStyle(el);
  const pick = (name, fallback) => {
    const value = cs.getPropertyValue(name).trim();
    return value || fallback;
  };
  const ink = pick("--g-ink", pick("--ink", "#000"));
  const palette = {
    ink,
    ink2: pick("--g-ink-2", pick("--ink-2", ink)),
    ink3: pick("--g-ink-2", pick("--ink-3", ink)),
    card: pick("--g-card", pick("--card", "#fff")),
    accent: pick("--accent", ink),
    font: cs.fontFamily || "system-ui, sans-serif",
    grainStrength: parseFloat(pick("--g-grain-strength", "0.08")) || 0.08,
    glowStrength: parseFloat(pick("--g-glow-strength", "0.5")) || 0.5,
  };
  for (const key of PALETTE_KEYS) {
    palette[key] = pick(`--g-${key}`, ink);
  }
  return palette;
}

export function withAlpha(color, alpha) {
  if (color.startsWith("#")) {
    const hex = color.length === 4
      ? color.slice(1).split("").map((c) => c + c).join("")
      : color.slice(1, 7);
    const n = parseInt(hex, 16);
    return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
  }
  if (color.startsWith("rgb")) {
    const parts = color.replace(/rgba?\(|\)/g, "").split(/[,/\s]+/).filter(Boolean);
    return `rgba(${parts[0]}, ${parts[1]}, ${parts[2]}, ${alpha})`;
  }
  return color;
}

/* ------------------------------------------------------------ silhouettes
 *
 * One shape per station, drawn into a box. The scene draws them at full size
 * and the compound cards draw the same outlines at about 20 pixels, so a
 * player learns each shape once. Every one of them fits its box exactly and
 * reads as an outline with no colour at all.
 */

export const STATIONS = [
  "dissolve", "cross_gut_wall", "resist_the_pump", "survive_liver",
  "stay_free_in_blood", "reach_target",
];

export function stomachPath(ctx, b) {
  const { x, y, w, h } = b;
  ctx.beginPath();
  ctx.moveTo(x + w * 0.34, y);
  ctx.bezierCurveTo(x + w * 0.02, y + h * 0.22, x - w * 0.02, y + h * 0.72,
    x + w * 0.34, y + h * 0.95);
  ctx.bezierCurveTo(x + w * 0.62, y + h * 1.06, x + w * 0.92, y + h * 0.95,
    x + w * 0.97, y + h * 0.66);
  ctx.bezierCurveTo(x + w * 0.99, y + h * 0.44, x + w * 0.74, y + h * 0.46,
    x + w * 0.70, y + h * 0.30);
  ctx.bezierCurveTo(x + w * 0.67, y + h * 0.16, x + w * 0.58, y + h * 0.04,
    x + w * 0.34, y);
  ctx.closePath();
}

export function gutPath(ctx, b) {
  const { x, y, w, h } = b;
  const teeth = 5;
  ctx.beginPath();
  ctx.moveTo(x + w * 0.45, y);
  ctx.lineTo(x + w, y);
  ctx.lineTo(x + w, y + h);
  ctx.lineTo(x + w * 0.45, y + h);
  for (let i = teeth - 1; i >= 0; i -= 1) {
    const y0 = y + ((i + 1) / teeth) * h;
    const y1 = y + (i / teeth) * h;
    ctx.quadraticCurveTo(x - w * 0.12, y + ((i + 0.5) / teeth) * h,
      x + w * 0.45, y1 + (y0 - y1) * 0.02);
  }
  ctx.closePath();
}

export function gatePath(ctx, b) {
  const { x, y, w, h } = b;
  const r = Math.min(w, h) * 0.16;
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(x, y, w, h, r);
  else ctx.rect(x, y, w, h);
}

export function proteinPath(ctx, b, seed) {
  const rnd = makeRandom(seed || 7);
  const lobes = 5 + Math.floor(rnd() * 3);
  const phase = rnd() * TAU;
  const cx = b.x + b.w / 2;
  const cy = b.y + b.h / 2;
  ctx.beginPath();
  for (let i = 0; i <= 56; i += 1) {
    const a = (i / 56) * TAU;
    const k = 1 + Math.sin(a * lobes + phase) * 0.17 + Math.sin(a * 2 + phase) * 0.06;
    const px = cx + Math.cos(a) * (b.w / 2) * k * 0.92;
    const py = cy + Math.sin(a) * (b.h / 2) * k * 0.92;
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }
  ctx.closePath();
}

export function capsidPath(ctx, b) {
  const cx = b.x + b.w / 2;
  const cy = b.y + b.h / 2;
  const sides = 10;
  ctx.beginPath();
  for (let i = 0; i <= sides; i += 1) {
    const a = (i / sides) * TAU - Math.PI / 2;
    const px = cx + Math.cos(a) * (b.w / 2) * 0.72;
    const py = cy + Math.sin(a) * (b.h / 2) * 0.72;
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }
  ctx.closePath();
}

function glyphDrums(ctx, b) {
  const cx = b.x + b.w / 2;
  const r = Math.min(b.w, b.h) * 0.3;
  for (const dir of [-1, 1]) {
    const cy = b.y + b.h / 2 + dir * b.h * 0.26;
    ctx.beginPath();
    for (let i = 0; i <= 12; i += 1) {
      const a = (i / 12) * TAU;
      const rr = r * (i % 2 === 0 ? 1 : 0.74);
      const px = cx + Math.cos(a) * rr;
      const py = cy + Math.sin(a) * rr;
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.stroke();
  }
}

function glyphSpikes(ctx, b) {
  const cx = b.x + b.w / 2;
  const cy = b.y + b.h / 2;
  for (let i = 0; i < 8; i += 1) {
    const a = (i / 8) * TAU;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(a) * b.w * 0.36, cy + Math.sin(a) * b.h * 0.36);
    ctx.lineTo(cx + Math.cos(a) * b.w * 0.48, cy + Math.sin(a) * b.h * 0.48);
    ctx.stroke();
  }
}

export function pumpPath(ctx, b) {
  const { x, y, w, h } = b;
  const r = Math.min(w, h) * 0.2;
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(x + w * 0.1, y + h * 0.08, w * 0.8, h * 0.84, r);
  else ctx.rect(x + w * 0.1, y + h * 0.08, w * 0.8, h * 0.84);
}

/* The pump throws a molecule back the way it came, so its mark is a return
 * arrow pointing left across the housing. */
function glyphPumpArrow(ctx, b) {
  const cy = b.y + b.h / 2;
  const x0 = b.x + b.w * 0.74;
  const x1 = b.x + b.w * 0.26;
  ctx.beginPath();
  ctx.moveTo(x0, cy);
  ctx.lineTo(x1, cy);
  ctx.moveTo(x1 + b.w * 0.16, cy - b.h * 0.14);
  ctx.lineTo(x1, cy);
  ctx.lineTo(x1 + b.w * 0.16, cy + b.h * 0.14);
  ctx.stroke();
}

const GLYPH_SHAPES = {
  dissolve: (ctx, b) => stomachPath(ctx, b),
  gut: (ctx, b) => gutPath(ctx, { x: b.x + b.w * 0.24, y: b.y, w: b.w * 0.6, h: b.h }),
  pump: (ctx, b) => pumpPath(ctx, b),
  liver: (ctx, b) => gatePath(ctx, { x: b.x + b.w * 0.06, y: b.y, w: b.w * 0.88, h: b.h }),
  binding: (ctx, b) => proteinPath(ctx, b, 41),
  target: (ctx, b) => capsidPath(ctx, b),
};

const GLYPH_MARKS = {
  liver: glyphDrums,
  target: glyphSpikes,
  pump: glyphPumpArrow,
};

function emptyHatch(ctx, b) {
  ctx.save();
  ctx.clip();
  ctx.lineWidth = 1;
  for (let x = b.x - b.h; x < b.x + b.w; x += 4) {
    ctx.beginPath();
    ctx.moveTo(x, b.y + b.h);
    ctx.lineTo(x + b.h, b.y);
    ctx.stroke();
  }
  ctx.restore();
}

/* The data build names the gates differently from the scene, and the CYP gates
 * are liver doors, so they wear the liver's shape. */
export const STATION_ALIASES = {
  cross_gut_wall: "gut",
  resist_the_pump: "pump",
  survive_liver: "liver",
  spare_cyp1a2: "liver",
  spare_cyp2c9: "liver",
  spare_cyp2d6: "liver",
  spare_cyp3a4: "liver",
  leave_the_dial_alone: "liver",
  stay_free_in_blood: "binding",
  reach_target: "target",
};

export function stationShape(station) {
  return STATION_ALIASES[station] || station;
}

function stripConnectors(ctx, P, s) {
  for (let i = 0; i < STATIONS.length - 1; i += 1) {
    const x0 = s.box.x + (s.size + s.gap) * i + s.size;
    const reached = (s.fills?.[STATIONS[i]] ?? 0) > 0.12;
    ctx.strokeStyle = withAlpha(reached ? P.drug : P.ink3, reached ? 0.8 : 0.35);
    ctx.lineWidth = reached ? 2 : 1;
    ctx.setLineDash(reached ? [] : [2, 3]);
    ctx.beginPath();
    ctx.moveTo(x0 + 2, s.cy);
    ctx.lineTo(x0 + s.gap - 2, s.cy);
    ctx.stroke();
  }
}

/* One station, drawn as an outline that fills from the bottom. `fill` is 0 to
 * 1: an empty glyph is hatched, so the state survives without colour. */
export function drawStationGlyph(ctx, station, box, fill, palette) {
  const P = palette;
  const shape = GLYPH_SHAPES[stationShape(station)] || GLYPH_SHAPES.dissolve;
  // Every measurement arrives as one of five bands, so the fill shows fifths.
  const level = Math.round(clamp(fill, 0, 1) * 5) / 5;
  ctx.save();
  ctx.lineJoin = "round";
  shape(ctx, box);
  ctx.fillStyle = withAlpha(P.ink, 0.07);
  ctx.fill();
  if (level > 0.02) {
    ctx.save();
    shape(ctx, box);
    ctx.clip();
    ctx.fillStyle = withAlpha(P.drug, 0.85);
    ctx.fillRect(box.x - 2, box.y + box.h * (1 - level), box.w + 4, box.h * level + 2);
    ctx.restore();
  } else {
    shape(ctx, box);
    ctx.strokeStyle = withAlpha(P.ink2, 0.5);
    emptyHatch(ctx, box);
  }
  shape(ctx, box);
  ctx.strokeStyle = withAlpha(P.ink, 0.72);
  ctx.lineWidth = Math.max(1, box.h * 0.055);
  ctx.stroke();
  const mark = GLYPH_MARKS[station];
  if (mark) {
    ctx.strokeStyle = withAlpha(P.ink, 0.55);
    ctx.lineWidth = Math.max(0.8, box.h * 0.04);
    mark(ctx, box);
  }
  ctx.restore();
}

/* The five stations in order with the run drawn through them, for a card. */
export function drawJourneyStrip(ctx, box, fills, palette) {
  const P = palette;
  const n = STATIONS.length;
  const size = Math.min(box.h, box.w / (n * 1.55));
  const gap = (box.w - size * n) / (n - 1);
  const cy = box.y + box.h / 2;
  let alive = true;
  ctx.save();
  ctx.lineCap = "round";
  stripConnectors(ctx, P, { box, size, gap, cy, fills });
  ctx.setLineDash([]);
  for (let i = 0; i < n; i += 1) {
    const station = STATIONS[i];
    const value = fills?.[station] ?? 0;
    const cell = { x: box.x + (size + gap) * i, y: cy - size / 2, w: size, h: size };
    drawStationGlyph(ctx, station, cell, alive ? value : 0, P);
    if (value < 0.12) alive = false;
  }
  ctx.restore();
}

/* ---------------------------------------------------------------- layout */

export function layout(w, h) {
  const lm = SCENE.landmarks;
  const half = clamp(h * SCENE.channel.halfHeight, 26, 112);
  const cy = h * SCENE.channel.y;
  const skin = clamp(h * 0.055, 10, 30);
  const wallW = clamp(w * 0.026, 12, 28);
  const gateR = Math.min(half * (w < 520 ? 0.85 : 1.05), clamp(w * 0.052, 24, 84));
  const stomachW = clamp(w * (w < 520 ? 0.16 : 0.13), 60, 190);
  const stomachH = clamp(h * 0.40, 74, 210);
  return {
    w,
    h,
    dense: w >= 620,
    skin,
    channel: { cy, half, x0: w * lm.gutWall, x1: w },
    stomach: {
      x: w * lm.mouth * (w < 520 ? 0.4 : 1),
      y: skin + h * 0.06,
      w: stomachW,
      h: stomachH,
      cx: w * lm.mouth + stomachW / 2,
      cy: skin + h * 0.06 + stomachH / 2,
      rx: stomachW / 2,
      ry: stomachH / 2,
    },
    gut: { x: w * lm.gutWall, w: wallW, y0: skin, y1: h - skin * 0.7 },
    lumen: { x0: -20, x1: w * lm.gutWall, y0: skin, y1: h - skin * 0.7 },
    pump: {
      x: w * lm.gutWall + wallW,
      y: cy - half * 0.62,
      w: clamp(w * 0.05, 26, 64),
      h: clamp(half * 1.25, 32, 92),
    },
    liver: {
      x0: w * lm.gutWall + wallW + w * 0.02,
      x1: w * 0.66,
      yTop: skin + h * 0.02,
      yBot: cy - half + 2,
      dipY: cy + half * 0.78,
    },
    ribs: { y0: skin * 0.9, y1: skin + h * 0.1 },
    returnVein: { cy: h * 0.885, half: clamp(h * 0.062, 10, 38) },
    gate: { cx: w * lm.liverGate, cy, r: gateR },
    field: { x0: w * 0.52, x1: w * lm.targetEntry, cy, half },
    target: {
      cx: w * (w < 520 ? 0.82 : lm.target),
      cy,
      r: Math.min(half * 1.25, clamp(w * 0.055, 22, 86),
        (w - w * (w < 520 ? 0.82 : lm.target)) / 2.2),
    },
    vials: { y: h * 0.955, x0: w * 0.30, x1: w * 0.74 },
    resultY: h * 0.145,
  };
}

/* ------------------------------------------------------------- sprites */

function sprite(size, dpr, paint) {
  const c = document.createElement("canvas");
  c.width = Math.max(1, Math.ceil(size * dpr));
  c.height = Math.max(1, Math.ceil(size * dpr));
  const ctx = c.getContext("2d");
  ctx.scale(dpr, dpr);
  paint(ctx, size);
  return c;
}

export function makeGlowSprite(color, radius, strength, dpr) {
  const size = radius * 2;
  return sprite(size, dpr, (ctx) => {
    const g = ctx.createRadialGradient(radius, radius, 0, radius, radius, radius);
    g.addColorStop(0, withAlpha(color, 0.95 * strength));
    g.addColorStop(0.35, withAlpha(color, 0.38 * strength));
    g.addColorStop(1, withAlpha(color, 0));
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, size, size);
  });
}

export function makeGrainTile(palette, dpr) {
  const side = 150;
  const rnd = makeRandom(9137);
  return sprite(side, dpr, (ctx) => {
    for (let i = 0; i < 2600; i += 1) {
      const a = rnd() * palette.grainStrength;
      ctx.fillStyle = withAlpha(palette.grain, a);
      ctx.fillRect(rnd() * side, rnd() * side, 1, 1);
    }
    for (let i = 0; i < 90; i += 1) {
      ctx.fillStyle = withAlpha(palette.grain, rnd() * palette.grainStrength * 0.7);
      ctx.fillRect(rnd() * side, rnd() * side, 2, 2);
    }
  });
}

function makeProteinSprite(palette, radius, seed, dpr) {
  const rnd = makeRandom(seed);
  const lobes = 5 + Math.floor(rnd() * 3);
  const phase = rnd() * TAU;
  const wobble = 0.14 + rnd() * 0.12;
  const size = radius * 2.3;
  const c = size / 2;
  return sprite(size, dpr, (ctx) => {
    ctx.beginPath();
    for (let i = 0; i <= 64; i += 1) {
      const a = (i / 64) * TAU;
      const r = radius * (1 + Math.sin(a * lobes + phase) * wobble
        + Math.sin(a * 2 + phase * 1.7) * 0.06);
      const x = c + Math.cos(a) * r;
      const y = c + Math.sin(a) * r * 0.86;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.closePath();
    const g = ctx.createRadialGradient(
      c - radius * 0.35, c - radius * 0.4, radius * 0.1, c, c, radius * 1.15,
    );
    g.addColorStop(0, withAlpha(palette.plasma, 0.85));
    g.addColorStop(0.55, withAlpha(palette["blood-cell"], 0.55));
    g.addColorStop(1, withAlpha(palette["blood-deep"], 0.75));
    ctx.fillStyle = g;
    ctx.fill();
    ctx.clip();
    ctx.strokeStyle = withAlpha(palette.plasma, 0.5);
    ctx.lineWidth = 1.4;
    for (let i = 0; i < 5; i += 1) {
      ctx.beginPath();
      ctx.arc(c - radius * 0.3, c - radius * 0.35, radius * (0.35 + i * 0.22),
        Math.PI * 0.95, Math.PI * 1.75);
      ctx.stroke();
    }
  });
}

/* --------------------------------------------------------- environment */

function strataPath(ctx, L, yBase, amp, freq, phase) {
  const step = Math.max(18, L.w / 26);
  ctx.beginPath();
  ctx.moveTo(-PARALLAX, yBase);
  for (let x = -PARALLAX; x <= L.w + PARALLAX; x += step) {
    const y = yBase
      + Math.sin(x * freq + phase) * amp
      + Math.sin(x * freq * 2.3 + phase * 1.6) * amp * 0.35;
    ctx.lineTo(x, y);
  }
  ctx.lineTo(L.w + PARALLAX, L.h + 40);
  ctx.lineTo(-PARALLAX, L.h + 40);
  ctx.closePath();
}

/* The engraved contour that every organ in the scene is drawn with. */
function ink(ctx, P, width, alpha) {
  ctx.strokeStyle = withAlpha(P.line, alpha === undefined ? 0.55 : alpha);
  ctx.lineWidth = width || 1.4;
  ctx.stroke();
}

function hatchBand(ctx, P, x0, x1, y0, y1, spacing, alpha) {
  ctx.save();
  ctx.beginPath();
  ctx.rect(x0, y0, x1 - x0, y1 - y0);
  ctx.clip();
  ctx.strokeStyle = withAlpha(P.line, alpha);
  ctx.lineWidth = 1;
  for (let x = x0 - (y1 - y0); x < x1; x += spacing) {
    ctx.beginPath();
    ctx.moveTo(x, y1);
    ctx.lineTo(x + (y1 - y0), y0);
    ctx.stroke();
  }
  ctx.restore();
}

/* The body's own outline, so the cross-section reads as a body rather than a
 * landscape: a skin layer across the top, cut open, and the same at the floor. */
export function drawBodyCut(ctx, P, L) {
  const s = L.skin;
  const top = ctx.createLinearGradient(0, -PARALLAX, 0, s);
  top.addColorStop(0, P.skin);
  top.addColorStop(1, withAlpha(P["tissue-near"], 0.9));
  ctx.fillStyle = top;
  ctx.fillRect(-PARALLAX, -PARALLAX, L.w + PARALLAX * 2, s + PARALLAX);
  hatchBand(ctx, P, -PARALLAX, L.w + PARALLAX, 0, s, 7, 0.22);
  ctx.beginPath();
  ctx.moveTo(-PARALLAX, s);
  const step = Math.max(24, L.w / 20);
  for (let x = -PARALLAX; x <= L.w + PARALLAX; x += step) {
    ctx.quadraticCurveTo(x + step * 0.5, s + Math.sin(x * 0.012) * 3 + 2, x + step, s);
  }
  ink(ctx, P, 1.6, 0.6);

  const floorY = L.h - s * 0.7;
  ctx.fillStyle = withAlpha(P["tissue-near"], 0.85);
  ctx.fillRect(-PARALLAX, floorY, L.w + PARALLAX * 2, L.h - floorY + PARALLAX);
  hatchBand(ctx, P, -PARALLAX, L.w + PARALLAX, floorY, L.h, 7, 0.18);
  ctx.beginPath();
  ctx.moveTo(-PARALLAX, floorY);
  ctx.lineTo(L.w + PARALLAX, floorY);
  ink(ctx, P, 1.2, 0.4);
}

export function drawStrata(ctx, P, L) {
  const base = ctx.createLinearGradient(0, 0, 0, L.h);
  base.addColorStop(0, P["tissue-far"]);
  base.addColorStop(0.45, P["tissue-mid"]);
  base.addColorStop(1, P.void);
  ctx.fillStyle = base;
  ctx.fillRect(-PARALLAX, -PARALLAX, L.w + PARALLAX * 2, L.h + PARALLAX * 2);

  const bands = [
    [L.h * 0.16, L.h * 0.035, 0.010, 0.4, 0.30],
    [L.h * 0.30, L.h * 0.028, 0.014, 2.1, 0.40],
    [L.h * 0.80, L.h * 0.030, 0.011, 1.2, 0.45],
    [L.h * 0.93, L.h * 0.022, 0.017, 3.3, 0.60],
  ];
  for (const [y, amp, freq, phase, alpha] of bands) {
    strataPath(ctx, L, y, amp, freq, phase);
    ctx.fillStyle = withAlpha(P["tissue-near"], alpha);
    ctx.fill();
  }

  const lightY = L.h * SCENE.channel.y;
  const lit = ctx.createLinearGradient(0, 0, 0, L.h);
  lit.addColorStop(0, withAlpha(P.vignette, 0.34));
  lit.addColorStop(clamp(lightY / L.h - 0.18, 0.05, 0.9), withAlpha(P.vignette, 0.05));
  lit.addColorStop(clamp(lightY / L.h + 0.02, 0.1, 0.95), withAlpha(P.vignette, 0));
  lit.addColorStop(1, withAlpha(P.vignette, 0.4));
  ctx.fillStyle = lit;
  ctx.fillRect(-PARALLAX, 0, L.w + PARALLAX * 2, L.h);
}

function fibreTexture(ctx, P, L) {
  const rnd = makeRandom(4471);
  ctx.lineWidth = 1;
  for (let i = 0; i < (L.dense ? 150 : 70); i += 1) {
    const x = rnd() * (L.w + PARALLAX * 2) - PARALLAX;
    const y = rnd() * L.h;
    const len = 12 + rnd() * 46;
    const tilt = (rnd() - 0.5) * 0.8;
    ctx.strokeStyle = withAlpha(P["tissue-near"], 0.10 + rnd() * 0.16);
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.quadraticCurveTo(x + len * 0.5, y + tilt * 14, x + len, y + tilt * 6);
    ctx.stroke();
  }
}

/* Fat lobules: the packed-bubble texture that fills the body of an anatomical
 * plate, so no region of the picture is a flat wash. */
export function drawAdipose(ctx, P, L) {
  const rnd = makeRandom(31771);
  const bands = [
    { y0: L.skin, y1: L.channel.cy - L.channel.half, x0: L.gut.x, x1: L.w },
    { y0: L.channel.cy + L.channel.half, y1: L.h * 0.9, x0: L.gut.x, x1: L.w },
  ];
  for (const band of bands) {
    const h = band.y1 - band.y0;
    if (h < 18) continue;
    const count = Math.round(((band.x1 - band.x0) * h) / (L.dense ? 700 : 1400));
    for (let i = 0; i < count; i += 1) {
      const x = band.x0 + rnd() * (band.x1 - band.x0);
      const y = band.y0 + rnd() * h;
      const r = 3 + rnd() * (L.dense ? 8 : 5);
      ctx.beginPath();
      ctx.ellipse(x, y, r, r * (0.72 + rnd() * 0.3), rnd() * TAU, 0, TAU);
      ctx.fillStyle = withAlpha(P["tissue-far"], 0.09);
      ctx.fill();
      ctx.strokeStyle = withAlpha(P.line, 0.05 + rnd() * 0.04);
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(x - r * 0.3, y - r * 0.35, r * 0.22, 0, TAU);
      ctx.fillStyle = withAlpha(P["line-lit"], 0.07);
      ctx.fill();
    }
  }
}

/* Ribs in section along the top, so the band above the organs is the body's
 * wall rather than a margin. */
export function drawRibs(ctx, P, L) {
  const b = L.ribs;
  const h = (b.y1 - b.y0) * 1.5;
  if (h < 12) return;
  const pitch = Math.max(110, L.w / 6);
  for (let x = pitch * 0.15; x < L.w + pitch; x += pitch) {
    const cy = b.y0 + h * 0.18;
    ctx.save();
    ctx.translate(x, cy);
    ctx.rotate(0.28);
    ctx.beginPath();
    ctx.ellipse(0, 0, h * 0.28, h * 0.6, 0, 0, TAU);
    const grad = ctx.createLinearGradient(-h * 0.28, 0, h * 0.28, 0);
    grad.addColorStop(0, withAlpha(P.bone, 0.95));
    grad.addColorStop(0.4, withAlpha(P["line-lit"], 0.45));
    grad.addColorStop(1, withAlpha(P.bone, 0.7));
    ctx.fillStyle = grad;
    ctx.fill();
    ink(ctx, P, 1.4, 0.7);
    ctx.beginPath();
    ctx.ellipse(0, h * 0.06, h * 0.13, h * 0.34, 0, 0, TAU);
    ctx.fillStyle = withAlpha(P["organ-deep"], 0.85);
    ctx.fill();
    ink(ctx, P, 1, 0.4);
    ctx.restore();
  }
  ctx.beginPath();
  ctx.moveTo(-PARALLAX, b.y1);
  ctx.lineTo(L.w + PARALLAX, b.y1);
  ink(ctx, P, 1, 0.3);
}

/* The vein carrying everything back, deeper in the body and out of focus, so
 * the bottom of the frame is the return half of the circuit. */
export function drawReturnVein(ctx, P, L) {
  const v = L.returnVein;
  const top = v.cy - v.half;
  const grad = ctx.createLinearGradient(0, top, 0, v.cy + v.half);
  grad.addColorStop(0, withAlpha(P["blood-deep"], 0.85));
  grad.addColorStop(0.5, withAlpha(P.blood, 0.6));
  grad.addColorStop(1, withAlpha(P["blood-deep"], 0.9));
  ctx.fillStyle = grad;
  ctx.fillRect(-PARALLAX, top, L.w + PARALLAX * 2, v.half * 2);
  ctx.strokeStyle = withAlpha(P.membrane, 0.4);
  ctx.lineWidth = 2;
  for (const y of [top, v.cy + v.half]) {
    ctx.beginPath();
    ctx.moveTo(-PARALLAX, y);
    const step = Math.max(30, L.w / 26);
    for (let x = -PARALLAX; x <= L.w + PARALLAX; x += step) {
      ctx.quadraticCurveTo(x + step * 0.5, y + 3, x + step, y);
    }
    ctx.stroke();
  }
  ctx.save();
  ctx.beginPath();
  ctx.rect(-PARALLAX, top, L.w + PARALLAX * 2, v.half * 2);
  ctx.clip();
  const rnd = makeRandom(1451);
  for (let i = 0; i < (L.dense ? 22 : 11); i += 1) {
    const x = rnd() * (L.w + 40) - 20;
    const y = top + rnd() * v.half * 2;
    const r = v.half * (0.16 + rnd() * 0.16);
    ctx.beginPath();
    ctx.ellipse(x, y, r, r * 0.62, rnd(), 0, TAU);
    ctx.fillStyle = withAlpha(P["blood-cell"], 0.3);
    ctx.fill();
  }
  ctx.restore();
  const haze = ctx.createLinearGradient(0, top - v.half, 0, v.cy + v.half * 2);
  haze.addColorStop(0, withAlpha(P["tissue-mid"], 0.6));
  haze.addColorStop(0.35, withAlpha(P["tissue-mid"], 0.12));
  haze.addColorStop(1, withAlpha(P["tissue-mid"], 0.45));
  ctx.fillStyle = haze;
  ctx.fillRect(-PARALLAX, top - v.half, L.w + PARALLAX * 2, v.half * 4);
}

function organLobe(ctx, L) {
  const o = L.liver;
  const gate = L.gate;
  const w = o.x1 - o.x0;
  const hw = gate.r * 1.2;
  const inner = hw + gate.r * 0.42;
  const outer = hw + gate.r * 1.15;
  ctx.beginPath();
  ctx.moveTo(o.x0, o.yBot - 6);
  ctx.bezierCurveTo(o.x0 - w * 0.05, o.yTop + (o.yBot - o.yTop) * 0.45,
    o.x0 + w * 0.12, o.yTop, o.x0 + w * 0.4, o.yTop + 4);
  ctx.bezierCurveTo(o.x0 + w * 0.74, o.yTop - 8, o.x1 + w * 0.06,
    o.yTop + (o.yBot - o.yTop) * 0.42, o.x1, o.yBot - 10);
  ctx.quadraticCurveTo(o.x1 - w * 0.03, o.yBot + 10, o.x1 - w * 0.1, o.yBot + 2);
  ctx.lineTo(gate.cx + outer, o.yBot + 2);
  ctx.bezierCurveTo(gate.cx + outer * 0.9, o.yBot + 2,
    gate.cx + inner * 1.05, o.dipY, gate.cx + inner, o.dipY);
  ctx.lineTo(gate.cx - inner, o.dipY);
  ctx.bezierCurveTo(gate.cx - inner * 1.05, o.dipY,
    gate.cx - outer * 0.9, o.yBot + 2, gate.cx - outer, o.yBot + 2);
  ctx.lineTo(o.x0 + w * 0.09, o.yBot + 2);
  ctx.quadraticCurveTo(o.x0 + w * 0.01, o.yBot + 4, o.x0, o.yBot - 6);
  ctx.closePath();
}

/* The portal tree: blood arrives from the gut and fans out through the organ. */
function portalBranch(ctx, P, x, y, angle, len, width, depth) {
  if (depth <= 0 || len < 4) return;
  const x1 = x + Math.cos(angle) * len;
  const y1 = y + Math.sin(angle) * len;
  ctx.strokeStyle = withAlpha(P["organ-deep"], 0.55);
  ctx.lineWidth = width;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.quadraticCurveTo(x + Math.cos(angle) * len * 0.5 + len * 0.1,
    y + Math.sin(angle) * len * 0.5, x1, y1);
  ctx.stroke();
  portalBranch(ctx, P, x1, y1, angle - 0.55, len * 0.62, width * 0.62, depth - 1);
  portalBranch(ctx, P, x1, y1, angle + 0.45, len * 0.58, width * 0.62, depth - 1);
}

export function drawLiverMass(ctx, P, L) {
  const o = L.liver;
  organLobe(ctx, L);
  const g = ctx.createLinearGradient(0, o.yTop, 0, o.yBot);
  g.addColorStop(0, P["organ-deep"]);
  g.addColorStop(0.55, P.organ);
  g.addColorStop(1, P["organ-deep"]);
  ctx.fillStyle = g;
  ctx.fill();

  ctx.save();
  ctx.clip();
  const w = o.x1 - o.x0;
  const h = o.yBot - o.yTop;
  for (let i = 0; i < (L.dense ? 5 : 3); i += 1) {
    portalBranch(ctx, P, o.x0 + w * (0.18 + i * 0.17), o.yBot,
      -Math.PI / 2 + (i - 2) * 0.26, h * 0.42, Math.max(1.4, w * 0.012), 3);
  }
  const sheen = ctx.createLinearGradient(o.x0, o.yTop, o.x0 + w * 0.5, o.yBot);
  sheen.addColorStop(0, withAlpha(P["metal-edge"], 0.10));
  sheen.addColorStop(0.6, withAlpha(P["metal-edge"], 0));
  ctx.fillStyle = sheen;
  ctx.fillRect(o.x0, o.yTop, w, o.yBot - o.yTop);
  ctx.restore();

  organLobe(ctx, L);
  ink(ctx, P, 1.8, 0.62);
  for (const [x, dir] of [[o.x0, -1], [o.x1, 1]]) {
    const mouth = ctx.createLinearGradient(x, 0, x + dir * L.channel.half * 0.9, 0);
    mouth.addColorStop(0, withAlpha(P["organ-deep"], 0.85));
    mouth.addColorStop(1, withAlpha(P["organ-deep"], 0));
    ctx.fillStyle = mouth;
    ctx.fillRect(Math.min(x, x + dir * L.channel.half * 0.9), L.channel.cy - L.channel.half,
      L.channel.half * 0.9, L.channel.half * 2);
  }
  ctx.save();
  organLobe(ctx, L);
  ctx.clip();
  ctx.strokeStyle = withAlpha(P["line-lit"], 0.16);
  ctx.lineWidth = 3;
  organLobe(ctx, L);
  ctx.stroke();
  ctx.restore();
  const shadow = ctx.createLinearGradient(0, o.yBot - 4, 0, o.yBot + L.channel.half * 0.9);
  shadow.addColorStop(0, withAlpha(P.vignette, 0.4));
  shadow.addColorStop(1, withAlpha(P.vignette, 0));
  ctx.fillStyle = shadow;
  ctx.fillRect(o.x0 - 10, o.yBot - 4, o.x1 - o.x0 + 20, L.channel.half * 0.9);
  mountingBracket(ctx, P, L);
}

/* The mechanism hangs off the liver's underside, so the two read as one part
 * rather than a machine parked near an organ. */
function mountingBracket(ctx, P, L) {
  const g = L.gate;
  const collar = g.r * 1.44;
  ctx.save();
  ctx.beginPath();
  ctx.ellipse(g.cx, g.cy, collar, L.channel.half * 1.05, 0, 0, TAU);
  ctx.fillStyle = withAlpha(P["organ-deep"], 0.95);
  ctx.fill();
  ink(ctx, P, 1.6, 0.5);
  const lit = ctx.createRadialGradient(g.cx, g.cy - collar * 0.4, collar * 0.2,
    g.cx, g.cy, collar * 1.2);
  lit.addColorStop(0, withAlpha(P.organ, 0.6));
  lit.addColorStop(1, withAlpha(P["organ-deep"], 0));
  ctx.fillStyle = lit;
  ctx.fill();
  ctx.restore();
}

function cavityPath(ctx, L) {
  stomachPath(ctx, L.stomach);
}

function oesophagus(ctx, P, L) {
  const s = L.stomach;
  const x = s.x + s.w * 0.34;
  ctx.lineCap = "butt";
  ctx.strokeStyle = P.wall;
  ctx.lineWidth = Math.max(10, s.w * 0.17);
  ctx.beginPath();
  ctx.moveTo(x, s.y + 6);
  ctx.lineTo(x, 0);
  ctx.stroke();
  ctx.strokeStyle = P.lumen;
  ctx.lineWidth = Math.max(4, s.w * 0.08);
  ctx.beginPath();
  ctx.moveTo(x, s.y + 6);
  ctx.lineTo(x, 0);
  ctx.stroke();
}

/* The duodenum: the pouch empties down and right into the gut wall. */
function pylorusDuct(ctx, P, L) {
  const s = L.stomach;
  const x0 = s.x + s.w * 0.95;
  const y0 = s.y + s.h * 0.66;
  const x1 = L.gut.x;
  const y1 = L.channel.cy - L.channel.half * 0.2;
  ctx.lineCap = "round";
  ctx.strokeStyle = P.wall;
  ctx.lineWidth = Math.max(11, s.w * 0.2);
  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.bezierCurveTo(x0 + (x1 - x0) * 0.4, y0, x1 - (x1 - x0) * 0.35, y1, x1 + 2, y1);
  ctx.stroke();
  ctx.strokeStyle = P.lumen;
  ctx.lineWidth = Math.max(5, s.w * 0.1);
  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.bezierCurveTo(x0 + (x1 - x0) * 0.4, y0, x1 - (x1 - x0) * 0.35, y1, x1 + 2, y1);
  ctx.stroke();
}

export function drawStomachShell(ctx, P, L) {
  const s = L.stomach;
  oesophagus(ctx, P, L);
  pylorusDuct(ctx, P, L);
  ctx.save();
  cavityPath(ctx, L);
  ctx.strokeStyle = P.wall;
  ctx.lineWidth = Math.max(9, s.w * 0.14);
  ctx.lineJoin = "round";
  ctx.stroke();
  cavityPath(ctx, L);
  ink(ctx, P, Math.max(10, s.w * 0.15) + 2, 0.18);

  cavityPath(ctx, L);
  const g = ctx.createRadialGradient(
    s.cx - s.rx * 0.3, s.cy - s.ry * 0.5, s.rx * 0.1, s.cx, s.cy, s.rx * 1.7,
  );
  g.addColorStop(0, P.lumen);
  g.addColorStop(1, withAlpha(P["wall-edge"], 0.5));
  ctx.fillStyle = g;
  ctx.fill();
  ctx.save();
  ctx.clip();
  ctx.strokeStyle = withAlpha(P["wall-edge"], 0.3);
  ctx.lineWidth = 1.3;
  for (let i = 0; i < 11; i += 1) {
    const y = s.y + (i / 11) * s.h;
    ctx.beginPath();
    ctx.moveTo(s.x - 4, y);
    ctx.quadraticCurveTo(s.cx, y + 9, s.x + s.w + 4, y - 4);
    ctx.stroke();
  }
  ctx.restore();
  cavityPath(ctx, L);
  ink(ctx, P, 1.5, 0.55);
  ctx.restore();
}

export function drawVessel(ctx, P, L) {
  const c = L.channel;
  const top = c.cy - c.half;
  const bot = c.cy + c.half;
  const g = ctx.createLinearGradient(0, top, 0, bot);
  g.addColorStop(0, P["blood-deep"]);
  g.addColorStop(0.42, P.blood);
  g.addColorStop(1, P["blood-deep"]);
  ctx.fillStyle = g;
  ctx.fillRect(c.x0 - 8, top, L.w - c.x0 + 16, c.half * 2);

  ctx.save();
  ctx.beginPath();
  ctx.rect(c.x0 - 8, top - 30, L.w - c.x0 + 16, c.half * 2 + 60);
  ctx.clip();
  for (const [y, dir] of [[top, 1], [bot, -1]]) {
    ctx.beginPath();
    ctx.moveTo(c.x0 - 10, y);
    const step = Math.max(16, L.w / 44);
    for (let x = c.x0 - 10; x <= L.w + 10; x += step) {
      ctx.quadraticCurveTo(x + step * 0.5, y + dir * 5, x + step, y);
    }
    ctx.lineTo(L.w + 10, y - dir * 14);
    ctx.lineTo(c.x0 - 10, y - dir * 14);
    ctx.closePath();
    ctx.fillStyle = withAlpha(P.membrane, 0.55);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(c.x0 - 10, y);
    for (let x = c.x0 - 10; x <= L.w + 10; x += step) {
      ctx.quadraticCurveTo(x + step * 0.5, y + dir * 5, x + step, y);
    }
    ink(ctx, P, 1.5, 0.5);
  }
  ctx.restore();
}

/* The vessel widens into a chamber where the target sits, so the molecule
 * arrives somewhere rather than running off the edge. */
export function drawTargetChamber(ctx, P, L) {
  const t = L.target;
  const r = t.r * 1.72;
  ctx.beginPath();
  ctx.ellipse(t.cx, t.cy, r, r * 0.98, 0, 0, TAU);
  const g = ctx.createRadialGradient(t.cx - r * 0.3, t.cy - r * 0.35, r * 0.1, t.cx, t.cy, r);
  g.addColorStop(0, withAlpha(P.blood, 0.95));
  g.addColorStop(1, P["blood-deep"]);
  ctx.fillStyle = g;
  ctx.fill();
  ink(ctx, P, 1.6, 0.5);
  ctx.save();
  ctx.beginPath();
  ctx.ellipse(t.cx, t.cy, r, r * 0.98, 0, 0, TAU);
  ctx.clip();
  const shade = ctx.createRadialGradient(t.cx, t.cy, r * 0.55, t.cx, t.cy, r);
  shade.addColorStop(0, withAlpha(P["blood-deep"], 0));
  shade.addColorStop(1, withAlpha(P["blood-deep"], 0.85));
  ctx.fillStyle = shade;
  ctx.fillRect(t.cx - r, t.cy - r, r * 2, r * 2);
  ctx.restore();
}

/* Everything left of the wall is the inside of the gut, so the left of the
 * picture is a chamber the compound sits in rather than empty tissue. */
export function drawLumen(ctx, P, L) {
  const b = L.lumen;
  const h = b.y1 - b.y0;
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(b.x1, b.y0);
  ctx.quadraticCurveTo(b.x0 + (b.x1 - b.x0) * 0.45, b.y0 + h * 0.04, b.x0 - 40, b.y0 - 6);
  ctx.lineTo(b.x0 - 40, b.y1 + 6);
  ctx.quadraticCurveTo(b.x0 + (b.x1 - b.x0) * 0.45, b.y1 - h * 0.04, b.x1, b.y1);
  ctx.closePath();
  const g = ctx.createLinearGradient(b.x0 - 40, 0, b.x1, 0);
  g.addColorStop(0, P["wall-edge"]);
  g.addColorStop(0.45, withAlpha(P.wall, 0.95));
  g.addColorStop(1, P.lumen);
  ctx.fillStyle = g;
  ctx.fill();
  ink(ctx, P, 1.5, 0.4);
  ctx.clip();
  ctx.strokeStyle = withAlpha(P.wall, 0.3);
  ctx.lineWidth = 2;
  for (let i = 0; i < 7; i += 1) {
    const y = b.y0 + (i / 7) * h + 8;
    ctx.beginPath();
    ctx.moveTo(b.x0 - 10, y);
    ctx.bezierCurveTo(b.x0 + (b.x1 - b.x0) * 0.4, y + 14,
      b.x1 - (b.x1 - b.x0) * 0.3, y - 10, b.x1, y + 4);
    ctx.stroke();
  }
  const poolTop = b.y1 - h * 0.34;
  const pool = ctx.createLinearGradient(0, poolTop, 0, b.y1);
  pool.addColorStop(0, withAlpha(P.lumen, 0.32));
  pool.addColorStop(1, withAlpha(P["drug-dim"], 0.5));
  ctx.fillStyle = pool;
  ctx.fillRect(b.x0 - 40, poolTop, b.x1 - b.x0 + 50, h * 0.4);
  ctx.strokeStyle = withAlpha(P["drug-core"], 0.3);
  ctx.lineWidth = 1.4;
  ctx.beginPath();
  ctx.moveTo(b.x0 - 40, poolTop);
  ctx.bezierCurveTo(b.x0 + (b.x1 - b.x0) * 0.4, poolTop - 6,
    b.x1 - (b.x1 - b.x0) * 0.3, poolTop + 5, b.x1, poolTop - 2);
  ctx.stroke();
  ctx.restore();
}

/* Capillaries leaving the vessel, which fill the tissue the way a plate does. */
export function drawCapillaryBed(ctx, P, L) {
  const c = L.channel;
  const count = L.dense ? 9 : 5;
  for (let i = 0; i < count; i += 1) {
    const x = c.x0 + ((i + 0.5) / count) * (L.w - c.x0);
    const upLen = (c.cy - c.half - L.skin) * 0.5;
    const downLen = (L.h - c.cy - c.half) * 0.42;
    if (x < L.liver.x0 - 10 || x > L.liver.x1 + 10) {
      capillaryBranch(ctx, P, x, c.cy - c.half, -Math.PI / 2 + (i % 3 - 1) * 0.3,
        upLen, 2.2, 3);
    }
    capillaryBranch(ctx, P, x + 12, c.cy + c.half, Math.PI / 2 + (i % 3 - 1) * 0.3,
      downLen, 2.2, 3);
  }
}

function capillaryBranch(ctx, P, x, y, angle, len, width, depth) {
  if (depth <= 0 || len < 5) return;
  const x1 = x + Math.cos(angle) * len;
  const y1 = y + Math.sin(angle) * len;
  ctx.strokeStyle = withAlpha(P["blood-cell"], 0.16 + depth * 0.07);
  ctx.lineWidth = width;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.quadraticCurveTo(x + Math.cos(angle + 0.14) * len * 0.55,
    y + Math.sin(angle + 0.14) * len * 0.55, x1, y1);
  ctx.stroke();
  capillaryBranch(ctx, P, x1, y1, angle - 0.6, len * 0.6, width * 0.6, depth - 1);
  capillaryBranch(ctx, P, x1, y1, angle + 0.5, len * 0.55, width * 0.6, depth - 1);
}

export function drawGutWallBase(ctx, P, L) {
  const g = L.gut;
  const grad = ctx.createLinearGradient(g.x, 0, g.x + g.w, 0);
  grad.addColorStop(0, P.membrane);
  grad.addColorStop(0.45, P.wall);
  grad.addColorStop(1, P["wall-edge"]);
  ctx.fillStyle = grad;
  ctx.fillRect(g.x, g.y0, g.w, g.y1 - g.y0);
  hatchBand(ctx, P, g.x, g.x + g.w, g.y0, g.y1, 6, 0.24);
  ctx.beginPath();
  ctx.moveTo(g.x, g.y0);
  ctx.lineTo(g.x, g.y1);
  ctx.moveTo(g.x + g.w, g.y0);
  ctx.lineTo(g.x + g.w, g.y1);
  ink(ctx, P, 1.4, 0.55);
  ctx.fillStyle = withAlpha(P["line-lit"], 0.22);
  ctx.fillRect(g.x + g.w - 2, g.y0, 2, g.y1 - g.y0);
}

export function drawTargetAlcove(ctx, P, L) {
  const t = L.target;
  const r = t.r * 2.1;
  const g = ctx.createRadialGradient(t.cx, t.cy, r * 0.2, t.cx, t.cy, r);
  g.addColorStop(0, withAlpha(P["foreign-deep"], 0.55));
  g.addColorStop(0.7, withAlpha(P["foreign-deep"], 0.18));
  g.addColorStop(1, withAlpha(P["foreign-deep"], 0));
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.arc(t.cx, t.cy, r, 0, TAU);
  ctx.fill();

  ctx.strokeStyle = withAlpha(P.wall, 0.5);
  ctx.lineWidth = Math.max(6, t.r * 0.16);
  ctx.beginPath();
  ctx.arc(t.cx, t.cy, t.r * 1.75, -Math.PI * 0.62, Math.PI * 0.62);
  ctx.stroke();
}

/* Tissue in front of the plane the run happens on, out of focus, so the scene
 * has a foreground as well as a distance. */
function foregroundTissue(ctx, P, L) {
  const top = L.h * 0.88;
  const g = ctx.createLinearGradient(0, top, 0, L.h);
  g.addColorStop(0, withAlpha(P["tissue-near"], 0));
  g.addColorStop(0.45, withAlpha(P["tissue-near"], 0.85));
  g.addColorStop(1, P["tissue-near"]);
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.moveTo(-PARALLAX, L.h + 10);
  const step = Math.max(40, L.w / 9);
  for (let x = -PARALLAX; x <= L.w + PARALLAX; x += step) {
    ctx.quadraticCurveTo(x + step * 0.5, top + Math.sin(x * 0.01) * L.h * 0.05,
      x + step, top + L.h * 0.03);
  }
  ctx.lineTo(L.w + PARALLAX, L.h + 10);
  ctx.closePath();
  ctx.fill();
}

function vignette(ctx, P, L) {
  const g = ctx.createRadialGradient(
    L.w * 0.5, L.h * 0.5, Math.min(L.w, L.h) * 0.25,
    L.w * 0.5, L.h * 0.5, Math.max(L.w, L.h) * 0.72,
  );
  g.addColorStop(0, withAlpha(P.vignette, 0));
  g.addColorStop(1, withAlpha(P.vignette, 0.34));
  ctx.fillStyle = g;
  ctx.fillRect(-PARALLAX, -PARALLAX, L.w + PARALLAX * 2, L.h + PARALLAX * 2);
}

export function bakeEnvironment(P, L, dpr, grainTile) {
  const c = document.createElement("canvas");
  c.width = Math.ceil((L.w + PARALLAX * 2) * dpr);
  c.height = Math.ceil(L.h * dpr);
  const ctx = c.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.translate(PARALLAX, 0);
  drawStrata(ctx, P, L);
  fibreTexture(ctx, P, L);
  drawBodyCut(ctx, P, L);
  drawRibs(ctx, P, L);
  drawAdipose(ctx, P, L);
  drawCapillaryBed(ctx, P, L);
  drawReturnVein(ctx, P, L);
  drawLumen(ctx, P, L);
  drawVessel(ctx, P, L);
  drawTargetAlcove(ctx, P, L);
  drawTargetChamber(ctx, P, L);
  drawLiverMass(ctx, P, L);
  drawStomachShell(ctx, P, L);
  drawGutWallBase(ctx, P, L);
  foregroundTissue(ctx, P, L);
  vignette(ctx, P, L);
  if (grainTile) {
    const pattern = ctx.createPattern(grainTile, "repeat");
    if (pattern) {
      pattern.setTransform?.(new DOMMatrix([1 / dpr, 0, 0, 1 / dpr, 0, 0]));
      ctx.fillStyle = pattern;
      ctx.fillRect(-PARALLAX, 0, L.w + PARALLAX * 2, L.h);
    }
  }
  return c;
}

/* ------------------------------------------------------- moving scenery */

export function drawPlasmaFlow(ctx, P, L, t) {
  const c = L.channel;
  ctx.save();
  ctx.beginPath();
  ctx.rect(c.x0, c.cy - c.half + 2, L.w - c.x0, c.half * 2 - 4);
  ctx.clip();
  const lines = L.dense ? 16 : 9;
  ctx.lineCap = "round";
  for (let i = 0; i < lines; i += 1) {
    const k = i / lines;
    const speed = 28 + (i % 4) * 16;
    const span = 90 + (i % 3) * 70;
    const x = c.x0 + ((t * speed + i * 137) % (L.w - c.x0 + span * 2)) - span;
    const y = c.cy + Math.sin(k * 9.1 + t * 0.6) * c.half * 0.82;
    ctx.strokeStyle = withAlpha(P.plasma, 0.07 + (i % 3) * 0.035);
    ctx.lineWidth = 1 + (i % 3) * 0.8;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.quadraticCurveTo(x + span * 0.5, y - 4, x + span, y + 2);
    ctx.stroke();
  }
  ctx.restore();
}

export function drawBloodCells(ctx, P, L, cells, t) {
  const c = L.channel;
  ctx.save();
  ctx.beginPath();
  ctx.rect(c.x0, c.cy - c.half, L.w - c.x0, c.half * 2);
  ctx.clip();
  for (const cell of cells) {
    const span = L.w - c.x0 + 120;
    const x = c.x0 - 60 + ((cell.x + t * cell.speed) % span);
    const y = c.cy + Math.sin(t * cell.bob + cell.phase) * c.half * cell.amp;
    const tilt = Math.sin(t * 0.5 + cell.phase) * 0.5;
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(tilt);
    ctx.beginPath();
    ctx.ellipse(0, 0, cell.r, cell.r * 0.62, 0, 0, TAU);
    ctx.fillStyle = withAlpha(P["blood-cell"], 0.5);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(0, 0, cell.r * 0.5, cell.r * 0.3, 0, 0, TAU);
    ctx.fillStyle = withAlpha(P["blood-deep"], 0.45);
    ctx.fill();
    ctx.restore();
  }
  ctx.restore();
}

function villus(ctx, P, x, y, len, width, sway) {
  ctx.beginPath();
  ctx.moveTo(x, y - width / 2);
  ctx.bezierCurveTo(x - len * 0.55, y - width * 0.55 + sway * 0.4,
    x - len, y - width * 0.22 + sway, x - len - width * 0.18, y + sway);
  ctx.bezierCurveTo(x - len, y + width * 0.22 + sway,
    x - len * 0.55, y + width * 0.55 + sway * 0.4, x, y + width / 2);
  ctx.closePath();
  const g = ctx.createLinearGradient(x, y, x - len, y);
  g.addColorStop(0, P["wall-edge"]);
  g.addColorStop(0.3, P.wall);
  g.addColorStop(0.75, P.membrane);
  g.addColorStop(1, withAlpha(P["wall-edge"], 0.85));
  ctx.fillStyle = g;
  ctx.fill();
  ink(ctx, P, 1, 0.3);
  ctx.beginPath();
  ctx.moveTo(x - width * 0.2, y - width * 0.12 + sway * 0.2);
  ctx.quadraticCurveTo(x - len * 0.6, y - width * 0.2 + sway * 0.6,
    x - len * 0.86, y - width * 0.05 + sway);
  ctx.strokeStyle = withAlpha(P["line-lit"], 0.2);
  ctx.lineWidth = Math.max(1, width * 0.16);
  ctx.stroke();
}

/* The lining, and the tunnels through it. A pore is a slot cut in the wall;
 * it opens with the gate and is dark when shut. */
export function drawVilli(ctx, P, L, t, gate) {
  const g = L.gut;
  const open = clamp(gate?.open ?? 0.5, 0, 1);
  const count = L.dense ? 54 : 30;
  const span = g.y1 - g.y0;
  const pitch = span / count;
  for (let i = 0; i < count; i += 1) {
    const y = g.y0 + (i + 0.5) * pitch;
    const len = g.w * (1.2 + Math.sin(i * 2.3) * 0.38 + Math.sin(i * 0.7) * 0.28);
    villus(ctx, P, g.x + 1, y, len, pitch * 1.35, Math.sin(t * 1.2 + i * 0.8) * len * 0.12);
  }
  const pores = L.dense ? 11 : 6;
  for (let i = 0; i < pores; i += 1) {
    const y = g.y0 + ((i + 0.5) / pores) * span;
    const slot = Math.max(1.5, ease(open) * g.w * 0.42);
    ctx.fillStyle = withAlpha(P["blood-deep"], 0.55);
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(g.x + 1, y - slot / 2, g.w - 2, slot, slot / 2);
    else ctx.rect(g.x + 1, y - slot / 2, g.w - 2, slot);
    ctx.fill();
    if (open > 0.12) {
      ctx.fillStyle = withAlpha(P["drug-core"], 0.1 + open * 0.16);
      ctx.fillRect(g.x + 1, y - slot / 2, g.w - 2, Math.min(slot, 1.6));
    }
  }
}

export function drawDissolveChamber(ctx, P, L, t, gate) {
  const s = L.stomach;
  const open = clamp(gate?.open ?? 1, 0, 1);
  ctx.save();
  cavityPath(ctx, L);
  ctx.clip();

  const fluidY = s.cy - s.ry * 0.25;
  ctx.beginPath();
  ctx.moveTo(s.cx - s.rx * 1.4, fluidY + Math.sin(t * 1.1) * 3);
  const step = s.rx * 0.4;
  for (let x = s.cx - s.rx * 1.4; x < s.cx + s.rx * 1.5; x += step) {
    ctx.quadraticCurveTo(x + step * 0.5, fluidY + Math.sin(t * 1.3 + x * 0.06) * 4,
      x + step, fluidY + Math.sin(t * 1.1 + x * 0.05) * 3);
  }
  ctx.lineTo(s.cx + s.rx * 1.5, s.cy + s.ry * 1.5);
  ctx.lineTo(s.cx - s.rx * 1.4, s.cy + s.ry * 1.5);
  ctx.closePath();
  const g = ctx.createLinearGradient(0, fluidY, 0, s.cy + s.ry);
  g.addColorStop(0, withAlpha(P.plasma, 0.30));
  g.addColorStop(1, withAlpha(P["organ-deep"], 0.35));
  ctx.fillStyle = g;
  ctx.fill();
  ctx.strokeStyle = withAlpha(P["drug-core"], 0.22);
  ctx.lineWidth = 1.2;
  ctx.stroke();

  const settled = Math.round((1 - open) * (L.dense ? 26 : 14));
  const rnd = makeRandom(5501);
  for (let i = 0; i < settled; i += 1) {
    const x = s.cx + (rnd() - 0.5) * s.rx * 1.5;
    const y = s.cy + s.ry * (0.62 + rnd() * 0.3);
    const r = 1.2 + rnd() * 2.2;
    ctx.fillStyle = withAlpha(P["drug-dim"], 0.75);
    ctx.beginPath();
    ctx.ellipse(x, y, r, r * 0.7, 0, 0, TAU);
    ctx.fill();
  }

  ctx.strokeStyle = withAlpha(P["drug-core"], 0.10 + open * 0.14);
  ctx.lineWidth = 1.1;
  for (let i = 0; i < 3; i += 1) {
    const a = t * 0.7 + i * 2.1;
    ctx.beginPath();
    ctx.ellipse(s.cx + Math.cos(a) * s.rx * 0.3, s.cy + s.ry * 0.2 + Math.sin(a) * s.ry * 0.2,
      s.rx * (0.38 + i * 0.14), s.ry * 0.22, a * 0.3, 0, TAU);
    ctx.stroke();
  }
  ctx.restore();
}

/* ------------------------------------------------------- liver mechanism */

/* The efflux pump: a piston set in the gut wall on the blood side that shoves
 * whatever crossed straight back into the gut. `open` is how well the compound
 * resists it, so a low value means a hard, frequent stroke. */
export function drawPump(ctx, P, L, t, gate) {
  const p = L.pump;
  const resist = clamp(gate?.open ?? 1, 0, 1);
  const cycle = (t * (0.6 + (1 - resist) * 1.6)) % 1;
  const stroke = Math.max(0, Math.sin(cycle * Math.PI)) * (1 - resist);
  ctx.save();
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(p.x, p.y, p.w, p.h, 5);
  else ctx.rect(p.x, p.y, p.w, p.h);
  const g = ctx.createLinearGradient(0, p.y, 0, p.y + p.h);
  g.addColorStop(0, P.metal);
  g.addColorStop(0.5, P["metal-dark"]);
  g.addColorStop(1, P.metal);
  ctx.fillStyle = g;
  ctx.fill();
  ink(ctx, P, 1.3, 0.55);
  const barrelY = p.y + p.h * 0.5;
  ctx.fillStyle = withAlpha(P["blood-deep"], 0.9);
  ctx.fillRect(p.x - p.w * 0.5, barrelY - p.h * 0.18, p.w * 0.6, p.h * 0.36);
  const headX = p.x - stroke * p.w * 0.55;
  ctx.fillStyle = P["metal-edge"];
  ctx.fillRect(headX - p.w * 0.16, barrelY - p.h * 0.22, p.w * 0.18, p.h * 0.44);
  ctx.strokeStyle = P.metal;
  ctx.lineWidth = Math.max(2, p.w * 0.1);
  ctx.beginPath();
  ctx.moveTo(headX, barrelY);
  ctx.lineTo(p.x + p.w * 0.5, barrelY);
  ctx.stroke();
  if (stroke > 0.55) {
    ctx.strokeStyle = withAlpha(P.hazard, (stroke - 0.55) * 1.6);
    ctx.lineWidth = 1.6;
    for (let i = 0; i < 3; i += 1) {
      const y = barrelY + (i - 1) * p.h * 0.22;
      ctx.beginPath();
      ctx.moveTo(headX - p.w * 0.3, y);
      ctx.lineTo(headX - p.w * 0.75, y);
      ctx.stroke();
    }
  }
  ctx.restore();
}

function rotorTeeth(ctx, P, cx, cy, r, angle, teeth) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(angle);
  ctx.beginPath();
  for (let i = 0; i < teeth; i += 1) {
    const a0 = (i / teeth) * TAU;
    const a1 = ((i + 0.42) / teeth) * TAU;
    const a2 = ((i + 1) / teeth) * TAU;
    ctx.lineTo(Math.cos(a0) * r * 0.72, Math.sin(a0) * r * 0.72);
    ctx.lineTo(Math.cos(a0 + 0.05) * r, Math.sin(a0 + 0.05) * r);
    ctx.lineTo(Math.cos(a1) * r, Math.sin(a1) * r);
    ctx.lineTo(Math.cos(a2 - 0.08) * r * 0.72, Math.sin(a2 - 0.08) * r * 0.72);
  }
  ctx.closePath();
  const g = ctx.createLinearGradient(-r, -r, r * 0.4, r);
  g.addColorStop(0, P["metal-edge"]);
  g.addColorStop(0.35, P.metal);
  g.addColorStop(1, P["metal-dark"]);
  ctx.fillStyle = g;
  ctx.fill();
  ink(ctx, P, 1.2, 0.5);

  ctx.beginPath();
  ctx.arc(0, 0, r * 0.66, 0, TAU);
  const face = ctx.createRadialGradient(-r * 0.25, -r * 0.3, r * 0.05, 0, 0, r * 0.7);
  face.addColorStop(0, P["metal-edge"]);
  face.addColorStop(0.7, P.metal);
  face.addColorStop(1, P["metal-dark"]);
  ctx.fillStyle = face;
  ctx.fill();
  ink(ctx, P, 1, 0.35);
  ctx.beginPath();
  ctx.arc(0, 0, r * 0.28, 0, TAU);
  ctx.fillStyle = P["metal-dark"];
  ctx.fill();
  ctx.beginPath();
  ctx.arc(0, 0, r * 0.1, 0, TAU);
  ctx.fillStyle = withAlpha(P["metal-edge"], 0.8);
  ctx.fill();
  ctx.strokeStyle = withAlpha(P["metal-dark"], 0.7);
  ctx.lineWidth = Math.max(1, r * 0.05);
  for (let i = 0; i < 4; i += 1) {
    const a = (i / 4) * TAU;
    ctx.beginPath();
    ctx.moveTo(Math.cos(a) * r * 0.3, Math.sin(a) * r * 0.3);
    ctx.lineTo(Math.cos(a) * r * 0.6, Math.sin(a) * r * 0.6);
    ctx.stroke();
  }
  ctx.restore();
}

function gateHousing(ctx, P, L) {
  const g = L.gate;
  const w = g.r * 2.4;
  const h = L.channel.half * 2 + 18;
  const x = g.cx - w / 2;
  const y = g.cy - h / 2;
  ctx.save();
  ctx.beginPath();
  ctx.roundRect?.(x, y, w, h, Math.min(12, g.r * 0.25));
  if (!ctx.roundRect) ctx.rect(x, y, w, h);
  const grad = ctx.createLinearGradient(0, y, 0, y + h);
  grad.addColorStop(0, P["metal-dark"]);
  grad.addColorStop(0.18, P.metal);
  grad.addColorStop(0.5, P["metal-dark"]);
  grad.addColorStop(0.9, P.metal);
  grad.addColorStop(1, P["metal-dark"]);
  ctx.fillStyle = grad;
  ctx.fill();
  ink(ctx, P, 1.6, 0.6);
  ctx.strokeStyle = withAlpha(P["metal-edge"], 0.4);
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.clip();
  ctx.fillStyle = withAlpha(P["blood-deep"], 0.95);
  ctx.fillRect(x + g.r * 0.3, g.cy - g.r * 1.1, w - g.r * 0.6, g.r * 2.2);
  ctx.strokeStyle = withAlpha(P.line, 0.5);
  ctx.lineWidth = 1.2;
  ctx.strokeRect(x + g.r * 0.3, g.cy - g.r * 1.1, w - g.r * 0.6, g.r * 2.2);
  ctx.restore();

  ctx.fillStyle = withAlpha(P["metal-edge"], 0.5);
  for (let i = 0; i < 4; i += 1) {
    const bx = x + 7 + (i % 2) * (w - 14);
    const by = y + 7 + Math.floor(i / 2) * (h - 14);
    ctx.beginPath();
    ctx.arc(bx, by, 2.2, 0, TAU);
    ctx.fill();
  }
  return { x, y, w, h };
}

/* Two drums, teeth meshing across the vessel. `open` slides them apart, so the
 * throat between them is the whole of how much gets through. */
function shredderDrums(ctx, P, L, open, spin) {
  const g = L.gate;
  const r = g.r * 0.78;
  const retract = ease(clamp(open, 0, 1)) * r * 0.6;
  const gap = retract * 2;
  if (gap > 2) {
    const glow = ctx.createLinearGradient(0, g.cy - gap / 2, 0, g.cy + gap / 2);
    glow.addColorStop(0, withAlpha(P["drug-core"], 0.14));
    glow.addColorStop(0.5, withAlpha(P["drug-core"], 0.03));
    glow.addColorStop(1, withAlpha(P["drug-core"], 0.14));
    ctx.fillStyle = glow;
    ctx.fillRect(g.cx - g.r * 1.05, g.cy - gap / 2, g.r * 2.1, gap);
  }
  rotorTeeth(ctx, P, g.cx, g.cy - r * 0.64 - retract, r, spin, 11);
  rotorTeeth(ctx, P, g.cx, g.cy + r * 0.64 + retract, r, -spin, 11);
}

/* A shaft into the liver, so the mechanism is visibly driven by the organ. */
function driveLinkage(ctx, P, L, spin) {
  const g = L.gate;
  const y = g.cy - L.channel.half - 10;
  rotorTeeth(ctx, P, g.cx + g.r * 0.95, y, g.r * 0.3, -spin * 1.6, 8);
  ctx.strokeStyle = P["metal-dark"];
  ctx.lineWidth = Math.max(2, g.r * 0.08);
  ctx.beginPath();
  ctx.moveTo(g.cx + g.r * 0.95, y);
  ctx.lineTo(g.cx + g.r * 0.95, L.liver.yBot - 4);
  ctx.stroke();
}

function grippedMolecules(ctx, P, L, holding, t, glow) {
  const g = L.gate;
  const n = clamp(Math.round(holding), 0, 4);
  for (let i = 0; i < n; i += 1) {
    const x = g.cx - g.r * 0.62 + (i / 3) * g.r * 1.2;
    const y = g.cy + Math.sin(t * 6 + i) * 1.5;
    blit(ctx, glow, x, y, 0.45);
    moleculeBody(ctx, P, x, y, Math.max(4, g.r * 0.17), t * 0.6 + i, P.drug, P["drug-core"]);
    ctx.strokeStyle = P["metal-edge"];
    ctx.lineWidth = Math.max(1.6, g.r * 0.05);
    ctx.lineCap = "round";
    for (const side of [-1, 1]) {
      ctx.beginPath();
      ctx.arc(x, y, g.r * 0.28, side > 0 ? -0.9 : Math.PI - 0.9,
        side > 0 ? 0.9 : Math.PI + 0.9);
      ctx.stroke();
    }
  }
}



function jamMarks(ctx, P, L, t) {
  const g = L.gate;
  const shake = Math.sin(t * 40) * 1.2;
  ctx.save();
  ctx.translate(shake, 0);
  ctx.strokeStyle = withAlpha(P.hazard, 0.85);
  ctx.lineWidth = 2;
  const r = g.r * 1.2;
  ctx.beginPath();
  ctx.arc(g.cx, g.cy, r, -0.7, 0.7);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(g.cx, g.cy, r, Math.PI - 0.7, Math.PI + 0.7);
  ctx.stroke();
  ctx.lineWidth = 1.2;
  for (let i = -3; i <= 3; i += 1) {
    const x = g.cx + i * 7;
    ctx.beginPath();
    ctx.moveTo(x, g.cy - g.r * 1.42);
    ctx.lineTo(x + 6, g.cy - g.r * 1.18);
    ctx.stroke();
  }
  ctx.restore();
}

export function drawLiverGate(ctx, P, L, t, gate, held, glow) {
  const jammed = !!gate?.jammed;
  const open = clamp(gate?.open ?? 1, 0, 1);
  const spin = jammed ? Math.sin(t * 30) * 0.03 : t * (0.9 + open * 1.8);
  const shake = jammed ? Math.sin(t * 34) * 1.3 : 0;
  ctx.save();
  ctx.translate(shake, 0);
  driveLinkage(ctx, P, L, spin);
  const box = gateHousing(ctx, P, L);
  ctx.save();
  ctx.beginPath();
  ctx.rect(box.x + 3, box.y + 3, box.w - 6, box.h - 6);
  ctx.clip();
  shredderDrums(ctx, P, L, open, spin);
  grippedMolecules(ctx, P, L, held, t, glow);
  ctx.restore();
  ctx.restore();
  if (jammed) jamMarks(ctx, P, L, t);
}

/* ------------------------------------------------------------ proteins */

export function drawProteins(ctx, P, L, proteins, t, count) {
  const c = L.channel;
  ctx.save();
  ctx.beginPath();
  ctx.rect(c.x0, c.cy - c.half - 6, L.w - c.x0, c.half * 2 + 12);
  ctx.clip();
  for (let i = 0; i < Math.min(count, proteins.length); i += 1) {
    const p = proteins[i];
    const pos = proteinPosition(p, L, t);
    const s = p.sprite;
    const dpr = s.dpr || 1;
    ctx.save();
    ctx.translate(pos.x, pos.y);
    ctx.rotate(p.spin + t * p.spinRate);
    ctx.globalAlpha = 1;
    ctx.drawImage(s, -s.width / (2 * dpr), -s.height / (2 * dpr),
      s.width / dpr, s.height / dpr);
    ctx.restore();
    ctx.beginPath();
    ctx.arc(pos.x - p.r * 0.3, pos.y - p.r * 0.35, p.r * 0.75, Math.PI * 1.05, Math.PI * 1.65);
    ctx.strokeStyle = withAlpha(P.plasma, 0.4);
    ctx.lineWidth = 1.6;
    ctx.stroke();
  }
  ctx.restore();
}

function proteinPosition(p, L, t) {
  const c = L.channel;
  const span = L.w - c.x0 + 260;
  return {
    x: c.x0 - 130 + ((p.x + t * p.speed) % span),
    y: c.cy + Math.sin(t * p.bob + p.phase) * c.half * p.amp,
  };
}

/* ----------------------------------------------------------- molecules */

function moleculeBody(ctx, P, x, y, size, spin, colour, coreColour) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(spin);
  ctx.fillStyle = colour;
  for (let i = 0; i < 3; i += 1) {
    const a = (i / 3) * TAU;
    ctx.beginPath();
    ctx.arc(Math.cos(a) * size * 0.62, Math.sin(a) * size * 0.62, size * 0.46, 0, TAU);
    ctx.fill();
  }
  ctx.beginPath();
  ctx.arc(0, 0, size * 0.78, 0, TAU);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(-size * 0.2, -size * 0.22, size * 0.34, 0, TAU);
  ctx.fillStyle = coreColour;
  ctx.fill();
  ctx.restore();
}

function drawTrail(ctx, P, vis, size) {
  const n = vis.trail.length;
  if (n < 2) return;
  ctx.lineCap = "round";
  for (let i = 1; i < n; i += 1) {
    const a = (i / n) * 0.55;
    ctx.strokeStyle = withAlpha(P.drug, a);
    ctx.lineWidth = size * (0.5 + (i / n) * 1.1);
    ctx.beginPath();
    ctx.moveTo(vis.trail[i - 1].x, vis.trail[i - 1].y);
    ctx.lineTo(vis.trail[i].x, vis.trail[i].y);
    ctx.stroke();
  }
}

const MOLECULE_PAINTERS = {
  travelling(ctx, P, m, vis, size, glow) {
    drawTrail(ctx, P, vis, size);
    blit(ctx, glow, m.px, m.py, size / 6);
    moleculeBody(ctx, P, m.px, m.py, size, vis.spin, P.drug, P["drug-core"]);
  },
  dissolving(ctx, P, m, vis, size, glow) {
    blit(ctx, glow, m.px, m.py, size / 9);
    ctx.globalAlpha = 0.75;
    moleculeBody(ctx, P, m.px, m.py, size * 0.85, vis.spin, P.drug, P["drug-core"]);
    ctx.globalAlpha = 1;
    ctx.setLineDash([3, 4]);
    ctx.strokeStyle = withAlpha(P["drug-core"], 0.55);
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.arc(m.px, m.py, size * (1.5 + Math.sin(vis.phase * 3) * 0.25), 0, TAU);
    ctx.stroke();
    ctx.setLineDash([]);
  },
  shredded(ctx, P, m, vis, size) {
    for (let i = 0; i < 4; i += 1) {
      const a = vis.phase * 2 + (i / 4) * TAU;
      const d = size * (0.9 + vis.phase * 1.6);
      ctx.save();
      ctx.translate(m.px + Math.cos(a) * d, m.py + Math.sin(a) * d);
      ctx.rotate(a * 2);
      ctx.fillStyle = withAlpha(P["drug-dim"], 0.85);
      ctx.beginPath();
      ctx.moveTo(-size * 0.4, 0);
      ctx.lineTo(0, -size * 0.3);
      ctx.lineTo(size * 0.42, size * 0.12);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }
  },
  bound(ctx, P, m, vis, size) {
    ctx.beginPath();
    for (let i = 0; i <= 18; i += 1) {
      const a = (i / 18) * TAU;
      const r = size * (1.9 + Math.sin(a * 4 + vis.phase) * 0.28);
      const x = m.px + Math.cos(a) * r;
      const y = m.py + Math.sin(a) * r * 0.82;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = withAlpha(P["blood-cell"], 0.5);
    ctx.fill();
    ctx.strokeStyle = withAlpha(P.plasma, 0.55);
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.globalAlpha = 0.55;
    moleculeBody(ctx, P, m.px, m.py, size * 0.9, vis.spin * 0.2, P["drug-dim"], P.drug);
    ctx.globalAlpha = 1;
  },
  arrived(ctx, P, m, vis, size, glow) {
    blit(ctx, glow, m.px, m.py, size / 5);
    moleculeBody(ctx, P, m.px, m.py, size, vis.spin * 0.4, P.drug, P["drug-core"]);
    const r = size * (1.4 + vis.phase * 3);
    ctx.strokeStyle = withAlpha(P["drug-core"], clamp(0.6 - vis.phase * 0.5, 0, 1));
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ctx.arc(m.px, m.py, r, 0, TAU);
    ctx.stroke();
  },
};

function blit(ctx, img, x, y, scale) {
  if (!img) return;
  const dpr = img.dpr || 1;
  const w = (img.width / dpr) * scale;
  const h = (img.height / dpr) * scale;
  ctx.drawImage(img, x - w / 2, y - h / 2, w, h);
}

export function drawMolecules(ctx, P, L, molecules, visuals, glow) {
  for (let i = 0; i < molecules.length; i += 1) {
    const m = molecules[i];
    const vis = visuals[i];
    const size = clamp((m.size || 1) * (L.dense ? 8 : 6), 3.4, 26);
    const paint = MOLECULE_PAINTERS[m.status] || MOLECULE_PAINTERS.travelling;
    paint(ctx, P, m, vis, size, glow);
  }
}

/* -------------------------------------------------------------- target */

/* The shell is a ball of capsomers, each shaded by how far it sits from the
 * light, so the target reads as a body with volume rather than a flat badge. */
/* Protein units in rings, the way a capsid is actually built, each shaded by
 * how far it sits from the light. */
function capsomerLattice(ctx, P, cx, cy, rr, health) {
  const rings = [[0, 1], [0.34, 7], [0.63, 13], [0.85, 17]];
  for (const [dist, count] of rings) {
    for (let i = 0; i < count; i += 1) {
      const a = (i / count) * TAU + dist * 2.1;
      const x = cx + Math.cos(a) * rr * dist;
      const y = cy + Math.sin(a) * rr * dist;
      const lit = clamp(1 - Math.hypot(x - (cx - rr * 0.4), y - (cy - rr * 0.45))
        / (rr * 1.6), 0, 1);
      const size = rr * (0.13 - dist * 0.045);
      ctx.beginPath();
      ctx.arc(x, y, size, 0, TAU);
      ctx.fillStyle = withAlpha(P["foreign-lit"], 0.06 + lit * (0.2 + health * 0.32));
      ctx.fill();
      ctx.strokeStyle = withAlpha(P["foreign-deep"], 0.45);
      ctx.lineWidth = 0.9;
      ctx.stroke();
    }
  }
}

function capsidFacets(ctx, P, cx, cy, r, health, t) {
  const pulse = 1 + Math.sin(t * (1.2 + health * 1.6)) * 0.025 * (0.3 + health);
  const rr = r * pulse;
  ctx.beginPath();
  ctx.arc(cx, cy, rr, 0, TAU);
  const g = ctx.createRadialGradient(
    cx - rr * 0.38, cy - rr * 0.42, rr * 0.08, cx, cy, rr * 1.12,
  );
  g.addColorStop(0, withAlpha(P["foreign-lit"], 0.5 + health * 0.45));
  g.addColorStop(0.55, withAlpha(P.foreign, 0.75 + health * 0.25));
  g.addColorStop(1, P["foreign-deep"]);
  ctx.fillStyle = g;
  ctx.fill();
  ink(ctx, P, 1.6, 0.55);

  capsomerLattice(ctx, P, cx, cy, rr, health);
  ctx.beginPath();
  ctx.arc(cx, cy, rr * 0.88, Math.PI * 1.08, Math.PI * 1.62);
  ctx.strokeStyle = withAlpha(P["line-lit"], 0.18 + health * 0.22);
  ctx.lineWidth = Math.max(1.4, rr * 0.06);
  ctx.stroke();
}

function capsidSpikes(ctx, P, cx, cy, r, health, t) {
  const spikes = 14;
  for (let i = 0; i < spikes; i += 1) {
    const a = (i / spikes) * TAU + Math.sin(t * 0.3) * 0.05;
    const droop = (1 - health) * 0.5;
    const len = r * (0.34 * health + 0.08) * (1 + Math.sin(t * 2 + i) * 0.06);
    const x0 = cx + Math.cos(a) * r * 0.96;
    const y0 = cy + Math.sin(a) * r * 0.96;
    const x1 = cx + Math.cos(a + droop) * (r + len);
    const y1 = cy + Math.sin(a + droop) * (r + len);
    ctx.strokeStyle = withAlpha(health > 0.25 ? P.foreign : P.ink3, 0.55 + health * 0.35);
    ctx.lineWidth = Math.max(1.2, r * 0.045);
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.quadraticCurveTo((x0 + x1) / 2 + droop * 6, (y0 + y1) / 2, x1, y1);
    ctx.stroke();
    ctx.fillStyle = withAlpha(health > 0.25 ? P["foreign-lit"] : P.ink3, 0.35 + health * 0.5);
    ctx.beginPath();
    ctx.arc(x1, y1, Math.max(1.3, r * 0.055), 0, TAU);
    ctx.fill();
  }
}

function capsidCracks(ctx, P, cx, cy, r, health) {
  const damage = 1 - health;
  if (damage < 0.15) return;
  const rnd = makeRandom(31337);
  const count = Math.floor(damage * 7);
  ctx.strokeStyle = withAlpha(P.ink, 0.35 + damage * 0.35);
  ctx.lineWidth = 1.1;
  for (let i = 0; i < count; i += 1) {
    const a = rnd() * TAU;
    let x = cx + Math.cos(a) * r * 0.2;
    let y = cy + Math.sin(a) * r * 0.2;
    ctx.beginPath();
    ctx.moveTo(x, y);
    for (let s = 0; s < 4; s += 1) {
      x += Math.cos(a + (rnd() - 0.5)) * r * 0.22;
      y += Math.sin(a + (rnd() - 0.5)) * r * 0.22;
      ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
}

export function drawTarget(ctx, P, L, t, health, glow) {
  const tg = L.target;
  const h = clamp(health, 0, 1);
  const breathe = 1 + Math.sin(t * (0.7 + h)) * 0.02;
  const r = tg.r * (0.82 + h * 0.18) * breathe;
  if (glow && h > 0.05) {
    ctx.globalAlpha = 0.25 + h * 0.45;
    blit(ctx, glow, tg.cx, tg.cy, (r * 2.4) / (glow.width / (glow.dpr || 1)));
    ctx.globalAlpha = 1;
  }
  for (let i = 0; i < 3; i += 1) {
    const a = t * 0.35 * (i + 1) + i * 2.3;
    const orbit = tg.r * (1.5 + i * 0.22);
    const sat = tg.r * 0.11 * (0.4 + h * 0.6);
    ctx.fillStyle = withAlpha(h > 0.2 ? P.foreign : P.ink3, 0.25 + h * 0.4);
    ctx.beginPath();
    ctx.arc(tg.cx + Math.cos(a) * orbit, tg.cy + Math.sin(a) * orbit * 0.7, sat, 0, TAU);
    ctx.fill();
  }
  capsidSpikes(ctx, P, tg.cx, tg.cy, r, h, t);
  capsidFacets(ctx, P, tg.cx, tg.cy, r, h, t);
  capsidCracks(ctx, P, tg.cx, tg.cy, r, h);
}

/* ------------------------------------------------------------- patient */





/* -------------------------------------------------------------- banner */

function wrapLines(ctx, text, maxWidth) {
  const words = String(text).split(/\s+/);
  const lines = [];
  let line = "";
  for (const word of words) {
    const next = line ? `${line} ${word}` : word;
    if (ctx.measureText(next).width > maxWidth && line) {
      lines.push(line);
      line = word;
    } else {
      line = next;
    }
  }
  if (line) lines.push(line);
  return lines;
}

export function drawBanner(ctx, P, L, banner) {
  if (!banner || !banner.text) return null;
  const result = banner.kind === "result";
  const size = result ? (L.dense ? 19 : 15) : (L.dense ? 14 : 12.5);
  ctx.font = `${result ? 600 : 400} ${size}px ${P.font}`;
  const maxW = Math.min(L.w * 0.62, 460);
  const lines = wrapLines(ctx, banner.text, maxW - 36);
  const lineH = size * 1.45;
  const boxW = Math.min(maxW, Math.max(...lines.map((l) => ctx.measureText(l).width)) + 36);
  const boxH = lines.length * lineH + 26;
  const x = L.w / 2 - boxW / 2;
  const y = result ? (L.resultY ?? L.h * 0.72) - boxH / 2 : L.h * 0.055;
  ctx.save();
  ctx.shadowColor = withAlpha(P.vignette, 0.35);
  ctx.shadowBlur = 24;
  ctx.shadowOffsetY = 6;
  ctx.fillStyle = withAlpha(P.card, 0.96);
  ctx.beginPath();
  ctx.roundRect?.(x, y, boxW, boxH, 12);
  if (!ctx.roundRect) ctx.rect(x, y, boxW, boxH);
  ctx.fill();
  ctx.restore();
  ctx.fillStyle = result ? P.ink : P.ink2;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  lines.forEach((line, i) => {
    ctx.fillText(line, L.w / 2, y + 13 + lineH * (i + 0.5));
  });
  ctx.textAlign = "left";
  ctx.textBaseline = "alphabetic";
  return { x, y, w: boxW, h: boxH };
}

/* ----------------------------------------------------------- particles */

export class ParticleField {
  constructor(limit) {
    this.limit = limit;
    this.items = [];
  }

  emit(x, y, count, spec) {
    for (let i = 0; i < count; i += 1) {
      if (this.items.length >= this.limit) this.items.shift();
      const a = spec.angle !== undefined
        ? spec.angle + (Math.random() - 0.5) * spec.spread
        : Math.random() * TAU;
      const speed = spec.speed * (0.4 + Math.random() * 0.9);
      this.items.push({
        x, y,
        vx: Math.cos(a) * speed,
        vy: Math.sin(a) * speed - (spec.lift || 0),
        life: spec.life * (0.6 + Math.random() * 0.7),
        age: 0,
        r: spec.r * (0.5 + Math.random()),
        kind: spec.kind,
      });
    }
  }

  step(dt) {
    const alive = [];
    for (const p of this.items) {
      p.age += dt;
      if (p.age >= p.life) continue;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.vx *= 0.97;
      p.vy = p.vy * 0.97 + (p.kind === "grain" ? 22 * dt : 0);
      alive.push(p);
    }
    this.items = alive;
  }

  draw(ctx, P) {
    for (const p of this.items) {
      const k = 1 - p.age / p.life;
      if (p.kind === "spark") {
        ctx.strokeStyle = withAlpha(P["drug-core"], k * 0.9);
        ctx.lineWidth = Math.max(0.7, p.r * 0.5);
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.x - p.vx * 0.02, p.y - p.vy * 0.02);
        ctx.stroke();
      } else if (p.kind === "grain") {
        ctx.fillStyle = withAlpha(P["drug-dim"], k * 0.8);
        ctx.fillRect(p.x, p.y, p.r, p.r);
      } else {
        ctx.fillStyle = withAlpha(P["foreign-lit"], k * 0.55);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * k, 0, TAU);
        ctx.fill();
      }
    }
  }
}

/* ------------------------------------------------------- the safety ward
 *
 * A second scene, same materials, no journey. The patient's own liver sits in
 * the middle with one door per enzyme, and under each door stands the medicine
 * that leaves through it. Block a door and that medicine backs up; speed the
 * liver up and it drains away.
 */

/* The bays are deliberately unequal: a symmetrical row of four reads as a
 * chart, and this scene is meant to read as a place where something is filling
 * up that should not be. */
const BAY_WEIGHTS = [1.18, 0.86, 1.32, 0.94];
const ENZYME_GATES = ["spare_cyp1a2", "spare_cyp2c9", "spare_cyp2d6", "spare_cyp3a4"];
const SAFE_LEVEL = 0.55;
const LOW_LEVEL = 0.22;

export function layoutPatient(w, h) {
  const skin = clamp(h * 0.055, 10, 30);
  const liverTop = skin + h * 0.03;
  const liverBot = liverTop + clamp(h * 0.26, 56, 150);
  const basin = {
    x0: w * 0.05,
    x1: w * 0.95,
    y0: liverBot + clamp(h * 0.20, 34, 96),
    y1: h - clamp(h * 0.14, 26, 66),
  };
  const bays = [];
  const total = BAY_WEIGHTS.reduce((a, b) => a + b, 0);
  let x = basin.x0 + 6;
  for (const weight of BAY_WEIGHTS) {
    const bw = ((basin.x1 - basin.x0 - 12) * weight) / total;
    bays.push({ x, w: bw, cx: x + bw / 2, y0: basin.y0, y1: basin.y1 });
    x += bw;
  }
  return {
    w,
    h,
    dense: w >= 620,
    skin,
    liver: { x0: w * 0.07, x1: w * 0.93, yTop: liverTop, yBot: liverBot },
    channel: { cy: (liverTop + liverBot) / 2, half: (liverBot - liverTop) / 2, x0: 0, x1: w },
    gut: { x: 0, w: 0 },
    ribs: { y0: skin * 0.9, y1: skin + h * 0.08 },
    basin,
    bays,
    dial: { cx: w * 0.8, cy: liverTop + (liverBot - liverTop) * 0.42,
      r: clamp(Math.min(w, h) * 0.075, 20, 50) },
    resultY: (liverBot + basin.y0) / 2,
  };
}

function patientLiverLobe(ctx, L) {
  const o = L.liver;
  const w = o.x1 - o.x0;
  const h = o.yBot - o.yTop;
  ctx.beginPath();
  ctx.moveTo(o.x0, o.yBot - h * 0.3);
  ctx.bezierCurveTo(o.x0 - w * 0.02, o.yTop + h * 0.2, o.x0 + w * 0.12, o.yTop - h * 0.05,
    o.x0 + w * 0.33, o.yTop + h * 0.1);
  ctx.bezierCurveTo(o.x0 + w * 0.4, o.yTop + h * 0.34, o.x0 + w * 0.46, o.yTop + h * 0.32,
    o.x0 + w * 0.53, o.yTop + h * 0.04);
  ctx.bezierCurveTo(o.x0 + w * 0.76, o.yTop - h * 0.1, o.x1 + w * 0.03,
    o.yTop + h * 0.3, o.x1, o.yBot - h * 0.34);
  ctx.bezierCurveTo(o.x1 - w * 0.04, o.yBot + h * 0.06, o.x0 + w * 0.2,
    o.yBot + h * 0.08, o.x0, o.yBot - h * 0.3);
  ctx.closePath();
}

function patientLiverBody(ctx, P, L) {
  const o = L.liver;
  const lw = o.x1 - o.x0;
  const lh = o.yBot - o.yTop;
  patientLiverLobe(ctx, L);
  const g = ctx.createLinearGradient(0, o.yTop, 0, o.yBot);
  g.addColorStop(0, P.organ);
  g.addColorStop(1, P["organ-deep"]);
  ctx.fillStyle = g;
  ctx.fill();
  ctx.save();
  patientLiverLobe(ctx, L);
  ctx.clip();
  for (let i = 0; i < 7; i += 1) {
    portalBranch(ctx, P, o.x0 + lw * (0.12 + i * 0.13), o.yBot,
      -Math.PI / 2 + (i - 3) * 0.18, lh * 0.55, Math.max(1.4, lw * 0.006), 3);
  }
  const sheen = ctx.createLinearGradient(0, o.yTop, 0, o.yBot);
  sheen.addColorStop(0, withAlpha(P["line-lit"], 0.12));
  sheen.addColorStop(0.45, withAlpha(P["line-lit"], 0));
  ctx.fillStyle = sheen;
  ctx.fillRect(o.x0, o.yTop, lw, lh);
  ctx.restore();
  patientLiverLobe(ctx, L);
  ink(ctx, P, 1.8, 0.62);
  const cast = ctx.createLinearGradient(0, o.yBot - 6, 0, o.yBot + lh * 0.5);
  cast.addColorStop(0, withAlpha(P.vignette, 0.45));
  cast.addColorStop(1, withAlpha(P.vignette, 0));
  ctx.fillStyle = cast;
  ctx.fillRect(o.x0 - 20, o.yBot - 6, lw + 40, lh * 0.5);
}

/* Five notches, because a measurement arrives as one of five bands. */
export function drawInductionDial(ctx, P, L, value) {
  const d = L.dial;
  const v = Math.round(clamp(value, 0, 1) * 4) / 4;
  const w = d.r * 3;
  const h = d.r * 0.85;
  const x = d.cx - w / 2;
  const y = d.cy - h / 2;
  ctx.save();
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(x, y, w, h, h * 0.42);
  else ctx.rect(x, y, w, h);
  const g = ctx.createLinearGradient(0, y, 0, y + h);
  g.addColorStop(0, P["metal-dark"]);
  g.addColorStop(1, P.metal);
  ctx.fillStyle = g;
  ctx.fill();
  ink(ctx, P, 1.5, 0.6);
  ctx.save();
  ctx.clip();
  ctx.fillStyle = withAlpha(P.hazard, 0.4);
  ctx.fillRect(x, y, w * 0.2, h);
  ctx.fillRect(x + w * 0.8, y, w * 0.2, h);
  ctx.restore();
  ctx.strokeStyle = withAlpha(P["metal-edge"], 0.55);
  ctx.lineWidth = 1.2;
  for (let i = 0; i < 5; i += 1) {
    const tx = x + w * (0.1 + (i / 4) * 0.8);
    ctx.beginPath();
    ctx.moveTo(tx, y + h * 0.24);
    ctx.lineTo(tx, y + h * 0.76);
    ctx.stroke();
  }
  const knobX = x + w * (0.1 + v * 0.8);
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(knobX - h * 0.26, y - h * 0.2, h * 0.52, h * 1.4, h * 0.2);
  else ctx.rect(knobX - h * 0.26, y - h * 0.2, h * 0.52, h * 1.4);
  ctx.fillStyle = P["metal-edge"];
  ctx.fill();
  ink(ctx, P, 1.2, 0.5);
  ctx.restore();
}

function enzymeDoor(ctx, P, box, gate, t) {
  const open = clamp(gate?.open ?? 1, 0, 1);
  ctx.save();
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(box.x, box.y, box.w, box.h, 5);
  else ctx.rect(box.x, box.y, box.w, box.h);
  const g = ctx.createLinearGradient(0, box.y, 0, box.y + box.h);
  g.addColorStop(0, P.metal);
  g.addColorStop(0.5, P["metal-dark"]);
  g.addColorStop(1, P.metal);
  ctx.fillStyle = g;
  ctx.fill();
  ink(ctx, P, 1.4, 0.6);
  ctx.save();
  ctx.clip();
  const throat = { x: box.x + box.w * 0.14, y: box.y + box.h * 0.16,
    w: box.w * 0.72, h: box.h * 0.68 };
  ctx.fillStyle = withAlpha(P["blood-deep"], 0.95);
  ctx.fillRect(throat.x, throat.y, throat.w, throat.h);
  const leaf = (throat.h / 2) * (1 - ease(open));
  const shutter = ctx.createLinearGradient(0, throat.y, 0, throat.y + throat.h);
  shutter.addColorStop(0, P["metal-edge"]);
  shutter.addColorStop(1, P.metal);
  ctx.fillStyle = shutter;
  ctx.fillRect(throat.x, throat.y, throat.w, leaf);
  ctx.fillRect(throat.x, throat.y + throat.h - leaf, throat.w, leaf);
  if (open > 0.1) {
    ctx.fillStyle = withAlpha(P.plasma, 0.4 + Math.sin(t * 3) * 0.08);
    ctx.fillRect(throat.x, throat.y + leaf, throat.w, throat.h - leaf * 2);
  }
  ctx.restore();
  rotorTeeth(ctx, P, box.x + box.w - 2, box.y + box.h * 0.5, box.h * 0.26,
    t * (0.4 + open * 2.2), 8);
  ctx.restore();
}

function basinPath(ctx, L) {
  const b = L.basin;
  const r = Math.min(26, (b.y1 - b.y0) * 0.3);
  ctx.beginPath();
  ctx.moveTo(b.x0, b.y0);
  ctx.lineTo(b.x1, b.y0);
  ctx.lineTo(b.x1, b.y1 - r);
  ctx.quadraticCurveTo(b.x1, b.y1, b.x1 - r, b.y1);
  ctx.lineTo(b.x0 + r, b.y1);
  ctx.quadraticCurveTo(b.x0, b.y1, b.x0, b.y1 - r);
  ctx.closePath();
}

function basinShell(ctx, P, L) {
  const b = L.basin;
  ctx.save();
  basinPath(ctx, L);
  const g = ctx.createLinearGradient(0, b.y0, 0, b.y1);
  g.addColorStop(0, withAlpha(P["blood-deep"], 0.35));
  g.addColorStop(1, withAlpha(P["blood-deep"], 0.7));
  ctx.fillStyle = g;
  ctx.fill();
  ink(ctx, P, 1.8, 0.7);
  ctx.restore();
}

function basinGlass(ctx, P, L) {
  const b = L.basin;
  ctx.save();
  basinPath(ctx, L);
  ctx.clip();
  const shade = ctx.createLinearGradient(b.x0, 0, b.x0 + 40, 0);
  shade.addColorStop(0, withAlpha(P.line, 0.5));
  shade.addColorStop(1, withAlpha(P.line, 0));
  ctx.fillStyle = shade;
  ctx.fillRect(b.x0, b.y0, 40, b.y1 - b.y0);
  const top = ctx.createLinearGradient(0, b.y0, 0, b.y0 + 26);
  top.addColorStop(0, withAlpha(P.line, 0.45));
  top.addColorStop(1, withAlpha(P.line, 0));
  ctx.fillStyle = top;
  ctx.fillRect(b.x0, b.y0, b.x1 - b.x0, 26);
  const seam = ctx.createLinearGradient(b.x0, 0, b.x0 + (b.x1 - b.x0) * 0.12, 0);
  seam.addColorStop(0, withAlpha(P["line-lit"], 0.05));
  seam.addColorStop(1, withAlpha(P["line-lit"], 0));
  ctx.fillStyle = seam;
  ctx.fillRect(b.x0, b.y0, (b.x1 - b.x0) * 0.12, b.y1 - b.y0);
  ctx.restore();
  basinPath(ctx, L);
  ink(ctx, P, 1.6, 0.7);
}

function fluidSurface(ctx, bay, surface, t) {
  ctx.beginPath();
  ctx.moveTo(bay.x, surface);
  const step = bay.w / 6;
  for (let x = bay.x; x < bay.x + bay.w + step; x += step) {
    ctx.quadraticCurveTo(x + step * 0.5, surface + Math.sin(t * 2 + x * 0.06) * 3,
      x + step, surface + Math.sin(t * 1.6 + x * 0.05) * 2);
  }
  ctx.lineTo(bay.x + bay.w, bay.y1);
  ctx.lineTo(bay.x, bay.y1);
  ctx.closePath();
}

function fluidBubbles(ctx, P, bay, surface, seed) {
  const rnd = makeRandom(seed);
  for (let i = 0; i < 14; i += 1) {
    const x = bay.x + rnd() * bay.w;
    const y = surface + rnd() * (bay.y1 - surface);
    const r = 1 + rnd() * 2.6;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, TAU);
    ctx.fillStyle = withAlpha(P["line-lit"], 0.07 + rnd() * 0.07);
    ctx.fill();
  }
}

function bayFluid(ctx, P, bay, med, t) {
  const level = Math.round(clamp(med.level ?? 0, 0, 1) * 5) / 5;
  const over = level > SAFE_LEVEL;
  const h = bay.y1 - bay.y0;
  const surface = bay.y1 - h * level;
  const safeY = bay.y1 - h * SAFE_LEVEL;
  ctx.save();
  ctx.beginPath();
  ctx.rect(bay.x, bay.y0, bay.w, h);
  ctx.clip();
  basinPath(ctx, { basin: { x0: bay.x - 2, x1: bay.x + bay.w + 2, y0: bay.y0, y1: bay.y1 } });
  ctx.clip();
  if (level > 0.01) {
    fluidSurface(ctx, bay, surface, t);
    const g = ctx.createLinearGradient(0, surface, 0, bay.y1);
    g.addColorStop(0, withAlpha(P["blood-cell"], 0.8));
    g.addColorStop(1, withAlpha(P["blood-deep"], 0.95));
    ctx.fillStyle = g;
    ctx.fill();
    fluidBubbles(ctx, P, bay, surface, 900 + Math.round(bay.cx));
    ctx.save();
    fluidSurface(ctx, bay, surface, t);
    ctx.clip();
    ctx.strokeStyle = withAlpha(over ? P.hazard : P.plasma, over ? 0.9 : 0.5);
    ctx.lineWidth = over ? 3 : 2;
    fluidSurface(ctx, bay, surface, t);
    ctx.stroke();
    ctx.restore();
  }
  if (over) excessBand(ctx, P, bay, surface, safeY);
  if (level < LOW_LEVEL) dryStain(ctx, P, bay);
  ctx.restore();
}

/* Only the part above the line is marked, so the hot colour is a warning on
 * the excess rather than paint over the whole medicine. */
function excessBand(ctx, P, bay, surface, safeY) {
  ctx.save();
  ctx.beginPath();
  ctx.rect(bay.x, surface, bay.w, safeY - surface);
  ctx.clip();
  ctx.fillStyle = withAlpha(P.hazard, 0.16);
  ctx.fillRect(bay.x, surface, bay.w, safeY - surface);
  ctx.strokeStyle = withAlpha(P.hazard, 0.42);
  ctx.lineWidth = 1;
  for (let s = -bay.w; s < safeY - surface + bay.w; s += 8) {
    ctx.beginPath();
    ctx.moveTo(bay.x, surface + s);
    ctx.lineTo(bay.x + bay.w, surface + s - bay.w);
    ctx.stroke();
  }
  ctx.restore();
  ctx.strokeStyle = withAlpha(P.hazard, 0.55);
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(bay.x + 1, surface);
  ctx.lineTo(bay.x + 1, safeY);
  ctx.moveTo(bay.x + bay.w - 1, surface);
  ctx.lineTo(bay.x + bay.w - 1, safeY);
  ctx.stroke();
}

/* Over the line the bay stops being a level and starts being a warning. */
function hazardWash(ctx, P, bay, surface) {
  ctx.strokeStyle = withAlpha(P.hazard, 0.35);
  ctx.lineWidth = 1;
  for (let s = -bay.w; s < bay.y1 - surface + bay.w; s += 7) {
    ctx.beginPath();
    ctx.moveTo(bay.x, surface + s);
    ctx.lineTo(bay.x + bay.w, surface + s - bay.w);
    ctx.stroke();
  }
}

/* Drained away, and the wall keeps the tidemark of where it used to sit. */
function dryStain(ctx, P, bay) {
  const h = bay.y1 - bay.y0;
  ctx.strokeStyle = withAlpha(P["drug-dim"], 0.5);
  ctx.setLineDash([6, 5]);
  ctx.lineWidth = 1.2;
  for (const k of [0.5, 0.62]) {
    ctx.beginPath();
    ctx.moveTo(bay.x + 2, bay.y1 - h * k);
    ctx.lineTo(bay.x + bay.w - 2, bay.y1 - h * k);
    ctx.stroke();
  }
  ctx.setLineDash([]);
}

function prescribedLine(ctx, P, L) {
  const b = L.basin;
  const y = b.y1 - (b.y1 - b.y0) * SAFE_LEVEL;
  ctx.strokeStyle = withAlpha(P["line-lit"], 0.55);
  ctx.setLineDash([9, 6]);
  ctx.lineWidth = 1.4;
  ctx.beginPath();
  ctx.moveTo(b.x0 - 8, y);
  ctx.lineTo(b.x1 + 8, y);
  ctx.stroke();
  ctx.setLineDash([]);
  for (const x of [b.x0 - 8, b.x1 + 8]) {
    ctx.beginPath();
    ctx.moveTo(x, y - 6);
    ctx.lineTo(x, y + 6);
    ctx.stroke();
  }
}

function baffles(ctx, P, L) {
  for (let i = 1; i < L.bays.length; i += 1) {
    const x = L.bays[i].x;
    ctx.beginPath();
    ctx.moveTo(x, L.basin.y0 - 4);
    ctx.lineTo(x, L.basin.y1);
    ctx.strokeStyle = withAlpha(P.metal, 0.75);
    ctx.lineWidth = 3;
    ctx.stroke();
    ink(ctx, P, 1, 0.5);
  }
}

function feedPipe(ctx, P, bay, doorBox, level) {
  const x = doorBox.x + doorBox.w * 0.5;
  const top = doorBox.y + doorBox.h - 2;
  const bottom = bay.y0 + 2;
  const wTop = doorBox.w * 0.42;
  const wBot = doorBox.w * 0.6;
  ctx.beginPath();
  ctx.moveTo(x - wTop / 2, top);
  ctx.lineTo(x + wTop / 2, top);
  ctx.lineTo(x + wBot / 2, bottom);
  ctx.lineTo(x - wBot / 2, bottom);
  ctx.closePath();
  const grad = ctx.createLinearGradient(x - wBot / 2, 0, x + wBot / 2, 0);
  grad.addColorStop(0, P["metal-dark"]);
  grad.addColorStop(0.35, P.metal);
  grad.addColorStop(1, P["metal-dark"]);
  ctx.fillStyle = grad;
  ctx.fill();
  ink(ctx, P, 1.2, 0.55);
  ctx.fillStyle = withAlpha(P.metal, 0.9);
  ctx.fillRect(x - wBot * 0.85, bottom - 5, wBot * 1.7, 6);
  ink(ctx, P, 1, 0.4);
  if (level > 0.02) {
    const drip = (performance.now() / 700) % 1;
    ctx.fillStyle = withAlpha(P.plasma, 0.85 * (1 - drip));
    ctx.beginPath();
    ctx.arc(x, bottom + drip * 8, 2.4, 0, TAU);
    ctx.fill();
  }
}

export function drawPatientScene(ctx, P, L, state, t) {
  const meds = state?.patient?.medicines || [];
  const gates = state?.gates || {};
  patientLiverBody(ctx, P, L);
  drawInductionDial(ctx, P, L, gates.leave_the_dial_alone?.open ?? gates.dial?.open ?? 0.5);
  basinShell(ctx, P, L);
  ctx.font = `${L.dense ? 12.5 : 10.5}px ${P.font}`;
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  for (let i = 0; i < L.bays.length; i += 1) {
    const bay = L.bays[i];
    const med = meds[i] || {};
    const doorW = Math.min(bay.w * 0.46, 68);
    const doorH = Math.min(36, doorW * 0.6);
    const doorBox = { x: bay.cx - doorW / 2, y: L.liver.yBot - doorH * 0.62,
      w: doorW, h: doorH };
    feedPipe(ctx, P, bay, doorBox, clamp(med.level ?? 0, 0, 1));
    enzymeDoor(ctx, P, doorBox, gates[ENZYME_GATES[i]] || { open: 1 }, t + i);
    bayFluid(ctx, P, bay, med, t + i);
    ctx.fillStyle = withAlpha(P.ink2, 0.92);
    const label = med.name || "";
    const halfText = ctx.measureText(label).width / 2 + 4;
    ctx.fillText(label, clamp(bay.cx, halfText, L.w - halfText), L.basin.y1 + 8);
  }
  baffles(ctx, P, L);
  basinGlass(ctx, P, L);
  prescribedLine(ctx, P, L);
  ctx.textAlign = "left";
  ctx.textBaseline = "alphabetic";
}

/* ------------------------------------------------------------ renderer */

function makeProteins(P, L, dpr) {
  const rnd = makeRandom(2029);
  const out = [];
  for (let i = 0; i < 12; i += 1) {
    const r = clamp(L.channel.half * (0.34 + rnd() * 0.3), 11, 52);
    out.push({
      x: rnd() * (L.w + 200),
      r,
      speed: 5 + rnd() * 7,
      bob: 0.25 + rnd() * 0.3,
      amp: 0.25 + rnd() * 0.45,
      phase: rnd() * TAU,
      spin: rnd() * TAU,
      spinRate: (rnd() - 0.5) * 0.18,
      sprite: withDpr(makeProteinSprite(P, r, 800 + i * 37, dpr), dpr),
    });
  }
  return out;
}

function makeCells(L) {
  const rnd = makeRandom(6781);
  const n = L.dense ? 16 : 8;
  const out = [];
  for (let i = 0; i < n; i += 1) {
    out.push({
      x: rnd() * (L.w + 120),
      r: clamp(L.channel.half * (0.10 + rnd() * 0.08), 2.5, 11),
      speed: 26 + rnd() * 26,
      bob: 0.5 + rnd(),
      amp: 0.3 + rnd() * 0.55,
      phase: rnd() * TAU,
    });
  }
  return out;
}

function withDpr(canvas, dpr) {
  canvas.dpr = dpr;
  return canvas;
}

/* The engine may key its gates the way the data file does. Both vocabularies
 * land on the five things this scene can draw. */
const GATE_SOURCES = {
  dissolve: ["dissolve"],
  gut: ["gut", "cross_gut_wall"],
  pump: ["pump", "resist_the_pump"],
  liver: ["liver", "survive_liver"],
  binding: ["binding", "stay_free_in_blood"],
  target: ["target", "reach_target"],
};

export function normaliseGates(gates) {
  const g = gates || {};
  const out = {};
  for (const [key, names] of Object.entries(GATE_SOURCES)) {
    out[key] = names.map((name) => g[name]).find(Boolean) || {};
  }
  return out;
}

export function isPatientWard(state) {
  return state?.ward === "safety";
}

export function bakePatientEnvironment(P, L, dpr, grainTile) {
  const c = document.createElement("canvas");
  c.width = Math.ceil((L.w + PARALLAX * 2) * dpr);
  c.height = Math.ceil(L.h * dpr);
  const ctx = c.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.translate(PARALLAX, 0);
  drawStrata(ctx, P, L);
  fibreTexture(ctx, P, L);
  drawBodyCut(ctx, P, L);
  drawAdipose(ctx, P, L);
  foregroundTissue(ctx, P, L);
  vignette(ctx, P, L);
  if (grainTile) {
    const pattern = ctx.createPattern(grainTile, "repeat");
    pattern?.setTransform?.(new DOMMatrix([1 / dpr, 0, 0, 1 / dpr, 0, 0]));
    if (pattern) {
      ctx.fillStyle = pattern;
      ctx.fillRect(-PARALLAX, 0, L.w + PARALLAX * 2, L.h);
    }
  }
  return c;
}

/* Anything still in the stomach is drawn inside the pouch, whatever the engine
 * says, so grains never end up floating in the tissue. */
function intoCavity(x, y, L) {
  const s = L.stomach;
  const k = clamp(x / SCENE.landmarks.gutWall, 0, 1);
  return {
    px: s.x + s.w * (0.18 + k * 0.62),
    py: s.y + s.h * clamp(0.22 + y * 0.62, 0.15, 0.88),
  };
}

/* Past the gut wall the drug is in the blood, so it is drawn inside the vessel
 * or inside the chamber the vessel opens into, never in the tissue between. */
function intoBlood(px, py, L) {
  const t = L.target;
  const reach = t.r * 1.64;
  const d = Math.hypot(px - t.cx, py - t.cy);
  if (d < reach) {
    const k = Math.min(1, (reach - 4) / Math.max(d, 0.001));
    return { px: t.cx + (px - t.cx) * Math.min(1, k), py: t.cy + (py - t.cy) * Math.min(1, k) };
  }
  const pad = Math.min(8, L.channel.half * 0.25);
  return {
    px,
    py: clamp(py, L.channel.cy - L.channel.half + pad, L.channel.cy + L.channel.half - pad),
  };
}

function moleculePixels(m, L) {
  const pixelSpace = Math.abs(m.x) > 1.5 || Math.abs(m.y) > 1.5;
  const px = pixelSpace ? m.x : m.x * L.w;
  const py = pixelSpace ? m.y : m.y * L.h;
  if (!pixelSpace && m.x < SCENE.landmarks.gutWall) return intoCavity(m.x, m.y, L);
  return intoBlood(px, py, L);
}

function visualFor(store, i, m, dt) {
  let vis = store[i];
  if (!vis) {
    vis = { trail: [], spin: (i * 1.7) % TAU, phase: 0, status: m.status };
    store[i] = vis;
  }
  if (vis.status !== m.status) {
    vis.status = m.status;
    vis.phase = 0;
    vis.trail.length = 0;
  }
  vis.phase += dt;
  vis.spin += dt * (m.status === "travelling" ? 2.4 : 0.7);
  return vis;
}

/* A molecule the engine teleports (a respawn, a reset) must not leave a streak
 * across the whole scene, so a long jump starts a new trail. */
function pushTrail(vis, x, y, keep) {
  const last = vis.trail[vis.trail.length - 1];
  if (last && Math.hypot(x - last.x, y - last.y) > 90) vis.trail.length = 0;
  vis.trail.push({ x, y });
  while (vis.trail.length > keep) vis.trail.shift();
}

/* Ordered front to back, so the first zone containing the point wins. */
function zoneTests(L) {
  const c = L.channel;
  const s = L.stomach;
  return [
    ["gate:dissolve", (x, y) => Math.abs(x - s.cx) < s.rx * 1.35
      && Math.abs(y - s.cy) < s.ry * 1.25],
    ["gate:gut", (x) => Math.abs(x - L.gut.x - L.gut.w / 2) < L.gut.w * 2.4],
    ["gate:liver", (x, y) => Math.abs(x - L.gate.cx) < L.gate.r * 1.4
      && Math.abs(y - L.gate.cy) < c.half + 12],
    ["gate:target", (x, y) => Math.hypot(x - L.target.cx, y - L.target.cy) < L.target.r * 1.9],
    ["patient", (x, y) => y > L.vials.y - L.h * 0.14 && x > L.vials.x0 && x < L.vials.x1],
    ["gate:binding", (x, y) => x > c.x0 && Math.abs(y - c.cy) < c.half + 10],
  ];
}

function inRect(x, y, r) {
  return r && x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h;
}

export function makeRenderer(canvas, theme) {
  const ctx = canvas.getContext("2d", { alpha: false });
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  let P = readPalette(canvas);
  let L = layout(canvas.clientWidth || 800, canvas.clientHeight || 340);
  let grain = withDpr(makeGrainTile(P, dpr), dpr);
  let background = null;
  let glowSmall = null;
  let glowBig = null;
  let proteins = [];
  let cells = [];
  let grainPattern = null;
  const particles = new ParticleField(260);
  const visuals = [];
  let clock = 0;
  let paletteProbe = P.drug;
  let probeTimer = 0;
  let lastHolding = 0;
  let bannerBox = null;
  let ward = "journey";
  let patientLayout = layoutPatient(L.w, L.h);
  const proteinBoxes = [];
  const moleculeBoxes = [];

  function rebuild() {
    P = readPalette(canvas);
    paletteProbe = P.drug;
    grain = withDpr(makeGrainTile(P, dpr), dpr);
    patientLayout = layoutPatient(L.w, L.h);
    background = ward === "patient"
      ? bakePatientEnvironment(P, patientLayout, dpr, grain)
      : bakeEnvironment(P, L, dpr, grain);
    glowSmall = withDpr(makeGlowSprite(P.drug, 26, P.glowStrength, dpr), dpr);
    glowBig = withDpr(makeGlowSprite(P.foreign, 80, P.glowStrength, dpr), dpr);
    proteins = makeProteins(P, L, dpr);
    cells = makeCells(L);
    grainPattern = ctx.createPattern(grain, "repeat");
    grainPattern?.setTransform?.(new DOMMatrix([1 / dpr, 0, 0, 1 / dpr, 0, 0]));
  }

  function resize(width, height) {
    const w = Math.max(240, Math.round(width));
    const h = Math.max(160, Math.round(height));
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    L = layout(w, h);
    rebuild();
  }

  function refreshPaletteIfThemeChanged(dt) {
    probeTimer += dt;
    if (probeTimer < 0.5) return;
    probeTimer = 0;
    const current = getComputedStyle(canvas).getPropertyValue("--g-drug").trim();
    if (current && current !== paletteProbe) rebuild();
  }

  function emitForMolecule(m, vis, size) {
    if (m.status === "dissolving" && Math.random() < 0.35) {
      particles.emit(m.px, m.py, 1, { speed: 14, life: 1.1, r: 1.6, kind: "grain" });
    }
    if (m.status === "shredded" && vis.phase < 0.12) {
      particles.emit(m.px, m.py, 7, { speed: 90, life: 0.5, r: 2.2, kind: "spark" });
    }
    if (m.status === "arrived" && vis.phase < 0.1) {
      particles.emit(m.px, m.py, 9, { speed: 60, life: 0.7, r: size * 0.4, kind: "bloom" });
    }
  }

  function prepareMolecules(list, dt) {
    moleculeBoxes.length = 0;
    for (let i = 0; i < list.length; i += 1) {
      const m = list[i];
      const pos = moleculePixels(m, L);
      m.px = pos.px;
      m.py = pos.py;
      const vis = visualFor(visuals, i, m, dt);
      const size = clamp((m.size || 1) * (L.dense ? 8 : 6), 3.4, 26);
      if (m.status === "travelling") pushTrail(vis, m.px, m.py, L.dense ? 9 : 5);
      emitForMolecule(m, vis, size);
      moleculeBoxes.push({ x: m.px, y: m.py, r: Math.max(size * 1.8, 12) });
    }
    visuals.length = list.length;
  }

  function gateEffects(gates, dt) {
    const liver = gates?.liver || {};
    const holding = liver.holding || 0;
    if (holding < lastHolding) {
      particles.emit(L.gate.cx, L.gate.cy, 12,
        { speed: 120, life: 0.45, r: 2.4, kind: "spark" });
    }
    lastHolding = holding;
    if (liver.jammed && Math.random() < dt * 8) {
      particles.emit(L.gate.cx + (Math.random() - 0.5) * L.gate.r,
        L.gate.cy + (Math.random() - 0.5) * L.gate.r, 2,
        { speed: 70, life: 0.3, r: 1.8, kind: "spark" });
    }
  }

  function drawScenery(state, gates) {
    const drift = Math.sin(clock * 0.06) * (PARALLAX * 0.45);
    ctx.drawImage(background, -PARALLAX + drift, 0,
      background.width / dpr, background.height / dpr);
    drawPlasmaFlow(ctx, P, L, clock);
    drawBloodCells(ctx, P, L, cells, clock);
    drawDissolveChamber(ctx, P, L, clock, gates.dissolve);
    drawVilli(ctx, P, L, clock, gates.gut);
    drawPump(ctx, P, L, clock, gates.pump);
  }

  function drawActors(state, gates) {
    const bindingOpen = clamp(gates.binding?.open ?? 1, 0, 1);
    const count = Math.round(lerp(proteins.length, 3, bindingOpen));
    proteinBoxes.length = 0;
    for (let i = 0; i < count; i += 1) {
      const pos = proteinPosition(proteins[i], L, clock);
      proteinBoxes.push({ x: pos.x, y: pos.y, r: proteins[i].r * 1.1 });
    }
    drawProteins(ctx, P, L, proteins, clock, count);
    drawTarget(ctx, P, L, clock, gates.target?.health ?? 1, glowBig);
    drawLiverGate(ctx, P, L, clock, gates.liver, gates.liver?.holding || 0, glowSmall);
    drawMolecules(ctx, P, L, state.molecules || [], visuals, glowSmall);
    particles.draw(ctx, P);
  }

  function syncWard(state) {
    const want = isPatientWard(state) ? "patient" : "journey";
    if (want === ward && background) return;
    ward = want;
    rebuild();
  }

  function drawWard(state, gates) {
    if (isPatientWard(state)) {
      ctx.drawImage(background, -PARALLAX, 0,
        background.width / dpr, background.height / dpr);
      drawPatientScene(ctx, P, patientLayout, state, clock);
      ctx.save();
      ctx.beginPath();
      ctx.rect(0, patientLayout.liver.yTop, L.w,
        patientLayout.basin.y0 - patientLayout.liver.yTop);
      ctx.clip();
      drawMolecules(ctx, P, patientLayout, state.molecules || [], visuals, glowSmall);
      ctx.restore();
      particles.draw(ctx, P);
      return;
    }
    drawScenery(state, gates);
    drawActors(state, gates);
  }

  function render(state, dtSeconds) {
    const dt = clamp(dtSeconds || 0.016, 0, 0.05);
    clock += dt;
    refreshPaletteIfThemeChanged(dt);
    syncWard(state);
    const gates = normaliseGates(state?.gates);
    prepareMolecules(state?.molecules || [], dt);
    gateEffects(gates, dt);
    particles.step(dt);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    drawWard(state, gates);
    if (grainPattern) {
      ctx.globalAlpha = 0.5;
      ctx.fillStyle = grainPattern;
      ctx.fillRect(0, 0, L.w, L.h);
      ctx.globalAlpha = 1;
    }
    bannerBox = drawBanner(ctx, P, ward === "patient" ? patientLayout : L, state?.banner);
  }

  function zoneAt(x, y) {
    for (const [id, inside] of zoneTests(L)) {
      if (inside(x, y)) return id;
    }
    return null;
  }

  /* In the patient ward the clickable things are the dial, each enzyme door
   * and each medicine column. */
  function patientHit(x, y) {
    const PL = patientLayout;
    if (Math.hypot(x - PL.dial.cx, y - PL.dial.cy) <= PL.dial.r * 1.6) return "dial";
    for (let i = 0; i < PL.bays.length; i += 1) {
      const bay = PL.bays[i];
      if (x < bay.x || x > bay.x + bay.w) continue;
      if (y > PL.liver.yBot - 26 && y < PL.basin.y0 - 4) return `enzyme:${i}`;
      if (y >= PL.basin.y0 - 4 && y <= PL.basin.y1 + 22) return `medicine:${i}`;
    }
    return null;
  }


  function hitTest(x, y) {
    if (ward === "patient") return patientHit(x, y);
    for (let i = 0; i < moleculeBoxes.length; i += 1) {
      const b = moleculeBoxes[i];
      if (Math.hypot(x - b.x, y - b.y) <= b.r) return `molecule:${i}`;
    }
    for (let i = 0; i < proteinBoxes.length; i += 1) {
      const b = proteinBoxes[i];
      if (Math.hypot(x - b.x, y - b.y) <= b.r) return `protein:${i}`;
    }
    if (inRect(x, y, bannerBox)) return "banner";
    return zoneAt(x, y);
  }

  function destroy() {
    background = null;
    glowSmall = null;
    glowBig = null;
    grainPattern = null;
    proteins = [];
    cells = [];
    visuals.length = 0;
    particles.items = [];
  }

  resize(canvas.clientWidth || 800, canvas.clientHeight || 340);
  if (theme) canvas.dataset.artTheme = theme;
  return { resize, render, hitTest, destroy };
}
