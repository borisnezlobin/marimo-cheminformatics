"""The gauntlet: pick a compound, send it through a body, watch how much survives.

A run is one compound through one ward. The compound arrives as a crowd of
molecules and meets that ward's stations in the order the data gives them, and
each station takes a share of the crowd away according to one real measurement
on that compound. Nothing is announced as a pass or a failure. The player
watches the crowd thin out, and the size of the crowd that arrives is the
feedback.

A station with no measurement behind it is not guessed at. The card says in
words that nobody has measured it, and the station resolves as a gamble the
player can watch happen.

The safety ward works the other way round. The patient already takes four
medicines, each of which leaves the body through a door of its own, and the
player's compound either stands in those doorways or turns up the dial that
opens them. The medicines rise or drain while the run is happening, and only the
doors this particular compound has measurements for are put in front of the
player, so no vial moves on a coin flip.

Everything the game knows lives in JavaScript. Python hands `game` in once and
reads `progress` back, so the game stays playable in a static export with no
kernel behind the page. Every pixel inside the canvas is drawn by
`widgets/game_art.js`, whose source is inlined into this module's `_esm`.

Cost control, because this animates: one canvas, at most 38 molecules a frame,
the loop stops when the widget scrolls out of view or the tab is hidden, and a
reader who asks for reduced motion gets the whole run resolved at once into a
single still frame.
"""

import json
import re
from pathlib import Path

import anywidget
import traitlets

from ._game_art import GAME_ART_JS
from ._theme import JS_PRELUDE, game_stylesheet

WARD_ORDER = ("antiviral", "library", "safety")
ENZYME_GATES = ("spare_cyp1a2", "spare_cyp2c9", "spare_cyp2d6", "spare_cyp3a4")
RARE_COMPOUNDS = ("E-0016931", "E-0017391")
HAND_POOL = 18

_CSS = game_stylesheet("""
.game__head { margin-bottom: 12px; }
.game__blurb { margin-top: 2px; max-width: 62ch; }

.game__stage {
  position: relative;
  background: var(--card);
  border-radius: var(--r-outer);
  box-shadow: var(--lift);
  padding: 8px;
  overflow: hidden;
}

.game__canvas { display: block; width: 100%; border-radius: 8px; }

.game__deck { margin-top: 14px; display: grid; gap: 10px; }
.game__prompt { color: var(--ink-2); font-size: 13px; }

.game__hand {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.game__card {
  display: grid;
  gap: 8px;
  align-content: start;
  padding: 12px;
  border-radius: var(--r-outer);
  background: var(--card);
  box-shadow: var(--lift);
  text-align: left;
  min-width: 0;
}

.game__card:hover { box-shadow: var(--lift), 0 0 0 2px var(--accent-soft); }
.game__card:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.game__art {
  display: block;
  width: 100%;
  aspect-ratio: 22 / 17;
  background: var(--sunk);
  border-radius: var(--r-inner);
  overflow: hidden;
  color: var(--ink);
}

.game__art svg { display: block; width: 100%; height: 100%; }

.game__name {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.25;
  color: var(--ink);
  overflow-wrap: anywhere;
}

.game__journey { display: block; width: 100%; height: auto; color: var(--ink); }
.game__line { font-size: 13px; color: var(--ink-2); line-height: 1.4; }

.game__choice { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.game__pick {
  min-height: 34px;
  padding: 0 14px;
  border-radius: var(--r-pill);
  background: var(--card);
  box-shadow: var(--lift);
  color: var(--ink);
}
.game__pick:hover { background: var(--sunk); }
.game__pick[aria-pressed="true"] {
  background: var(--ink);
  color: var(--bg);
  box-shadow: none;
}

.game__scores { display: flex; flex-wrap: wrap; gap: 8px 22px; }
.game__score { display: grid; gap: 3px; }
.game__score dt { font-size: 12.5px; color: var(--ink-2); }
.game__score dd { margin: 0; display: flex; gap: 3px; align-items: center; }
.game__pip { width: 9px; height: 14px; border-radius: 3px; background: var(--sunk); }
.game__pip[data-on="yes"] { background: var(--ink); }

.game__after { display: grid; gap: 10px; justify-items: start; }
.game__verdict { max-width: 60ch; }
.game__source { margin-top: 12px; font-size: 12.5px; color: var(--ink-3); max-width: 70ch; }

@container (max-width: 470px) {
  .game__hand { grid-template-columns: minmax(0, 1fr); }
  .game__card { grid-template-columns: 84px minmax(0, 1fr); }
  .game__art { grid-row: span 3; aspect-ratio: 1; }
}
""")


def _art_scope() -> str:
    """The art module's source, stripped of its exports and given a scope.

    anywidget serves `_esm` as a single module with no relative imports, so the
    drawing code is concatenated ahead of the engine rather than imported.
    """
    source = re.sub(r"^export default\s+", "const __artDefault = ", GAME_ART_JS, flags=re.M)
    source = re.sub(r"^export\s+", "", source, flags=re.M)
    return (
        "const __art = (() => {\n"
        + source
        + "\n  return { makeRenderer, SCENE };\n})();\n"
    )


_ENGINE = r"""
const START_MOLECULES = 38;
const APPROACH_SECONDS = 1.3;
const RESOLVE_SECONDS = 0.95;
const FINALE_SECONDS = 4.5;
const OUTRO_SECONDS = 1.8;
const RUNS_PER_WARD = 3;
const HEAVY_LOSS = 0.5;
const CLEAN_PASS = 0.85;
// The two lines the scene actually draws across a vial: the prescribed level a
// medicine should sit under, and the level below which it has washed out.
const PRESCRIBED_LEVEL = 0.55;
const DRY_LEVEL = 0.22;
const RESTING_LEVEL = 0.5;
const MOVE_SECONDS = 1.6;
const CROSSING_BEAT = 0.45;
const LANDMARKS = (__art.SCENE && __art.SCENE.landmarks) || {};
const CHANNEL = (__art.SCENE && __art.SCENE.channel) || { y: 0.575, halfHeight: 0.165 };

// Which station of the drawn scene each measured gate belongs to. The data
// names gates for what they measure; the scene has fewer places than that, so
// two gates can share one station and resolve at it one after the other.
const GATE_KIND = {
  dissolve: "dissolve",
  cross_gut_wall: "gut",
  resist_the_pump: "pump",
  survive_liver: "liver",
  stay_free_in_blood: "binding",
  reach_target: "target",
  reach_target_mers: "target",
  spare_cyp1a2: "door",
  spare_cyp2c9: "door",
  spare_cyp2d6: "door",
  spare_cyp3a4: "door",
  leave_the_dial_alone: "dial",
};
// The journey scene names its stations; the patient scene asks for each door
// and the dial by the identifier the data gave them.
const SCENE_GATE = { dissolve: "dissolve", gut: "gut", pump: "pump", liver: "liver",
                     binding: "binding", target: "target" };
const sceneKey = (step) => SCENE_GATE[step.kind] || step.id;
const ATTRITION_KINDS = new Set(["dissolve", "gut", "pump", "liver", "binding"]);
const LOST_STATUS = { dissolve: "dissolving", gut: "bound", pump: "bounced",
                      liver: "shredded", binding: "bound" };
const STATION_X = {
  dissolve: LANDMARKS.stomach || 0.095,
  gut: LANDMARKS.gutWall || 0.205,
  pump: (LANDMARKS.gutWall || 0.205) + 0.055,
  liver: LANDMARKS.liverGate || 0.44,
  binding: LANDMARKS.blood || 0.64,
  target: LANDMARKS.target || 0.885,
  dial: 0.72,
};
const DOOR_X = [0.33, 0.40, 0.47, 0.54];
const FINISH_X = (LANDMARKS.target || 0.885) + 0.02;

// Every string the player can read comes from GAME_COPY.md.
const COPY = {
  title: "Send it through",
  standfirst: "Send a compound through a body and see how much of it survives the trip.",
  start: "Start",
  handPrompt: "Pick one and send it in.",
  again: "Send another",
  nextWard: "Try the next ward",
  bestLabel: "Best run so far",
  runsLabel: "Runs played",
  source: "Every gate in this game is decided by a real measurement from OpenADMET's data, and the section below shows which one.",
  cleanPass: "Almost all of it got through.",
};

const WARD_COPY = {
  antiviral: {
    title: "Stop the virus",
    line: "A virus is multiplying in this body. Get enough of your compound through to stop it.",
  },
  library: {
    title: "Reach the blood",
    line: "There is no target this time. Getting a useful amount of anything into the blood is the whole job.",
  },
  safety: {
    title: "Do not hurt the patient",
    line: "This patient already takes four other medicines. Get through without blocking the route those medicines use to leave.",
  },
};

const WARD_FRAMING = {
  safety: "The first two wards asked whether your compound arrives. This one asks whether it hurts anyone on the way.",
};

const CLAUSES = {
  dissolve: { good: "Dissolves easily",
              bad: "Barely dissolves, so most of it never gets going" },
  gut: { good: "Crosses the gut wall without trouble",
         bad: "Struggles to cross the gut wall" },
  liver: { good: "Slips past the liver mostly intact",
           bad: "The liver destroys most of it on the way through" },
  binding: { good: "Stays free once it reaches the blood",
             bad: "Sticks to proteins in the blood, so little of it is free to work" },
  target: { good: "Hits the virus hard when it arrives",
            bad: "Barely troubles the virus, even when it arrives" },
  // A door names the medicine that leaves through it, since that is the thing
  // the player stands to lose.
  door: { good: "Leaves the door that clears {name} alone",
          bad: "Blocks the door that clears {name}" },
  dial: { good: "Leaves the liver running at its normal speed",
          bad: "Speeds the whole liver up, so the patient's medicines drain away" },
};

// The pump has no clause of its own, so it never becomes a card's best or worst
// gate, and it speaks only through the sentence about what nobody has measured.
const CLAUSELESS = new Set(["pump"]);

const UNTESTED_PHRASE = {
  dissolve: "whether it dissolves",
  cross_gut_wall: "how well it crosses the gut wall",
  resist_the_pump: "whether the pump throws it back out",
  survive_liver: "how well it survives the liver",
  stay_free_in_blood: "how much of it stays free in the blood",
  reach_target: "what it does to the virus",
  reach_target_mers: "what it does to the virus",
  leave_the_dial_alone: "whether it speeds the liver up",
};
const UNTESTED_DOOR = "what it does to the door that clears {name}";
const UNTESTED_VIAL = "Nobody has tested this compound against the door that clears {name}.";

const medicineName = (ward, gateId) => {
  const med = (ward.medicines || []).find((m) => m.gate === gateId);
  return med ? med.name : "the patient's own medicine";
};

const withName = (text, ward, gateId) => text.replace("{name}", medicineName(ward, gateId));

const STATION_MESSAGE = {
  dissolve: "Most of it never dissolved.",
  gut: "Most of it could not get through the gut wall.",
  liver: "The liver destroyed most of what arrived.",
  binding: "Proteins in the blood are holding most of it.",
  target: "Not enough arrived to slow the virus.",
};

const TIPS = {
  liver: "The liver destroys most of what passes through it, so a compound that survives it beats a stronger one that does not.",
  binding: "Proteins in the blood hold on to some of the drug, and only the free part can do anything.",
  patient: "Blocking the liver makes the patient's own medicines pile up, and clearing the virus does not count if you harm them.",
};

const RESULTS = {
  won: "Enough of it arrived, and the virus stopped.",
  none: "Nothing reached the virus this time.",
  thin: "Some of it arrived, but not enough to stop the virus.",
  harmed: "You stopped the virus and left the patient with too much of their own medicine in the blood.",
  libraryWon: "A useful amount reached the blood.",
  libraryLost: "Almost nothing reached the blood.",
  safetyWon: "You got through and left the patient's own medicines where they were.",
  safetyOne: "The patient is left with too much {name} in their blood.",
  safetyMany: "The patient is left with too much of their own medicine in their blood.",
  safetyDrained: "The patient's own medicines drained away faster than they should have.",
};

const VIRUS_PROMPT = "Choose which virus you are treating.";
const VIRUS_NOTE = "The same compound is not equally good against both.";
const VIRUS_OPTIONS = [
  { id: "reach_target", label: "SARS-CoV-2, the virus behind covid" },
  { id: "reach_target_mers", label: "MERS, a related virus" },
];

const clamp01 = (v) => Math.min(1, Math.max(0, v));
const lerp = (a, b, t) => a + (b - a) * t;

const mulberry32 = (seed) => {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

const shuffled = (items, rand) => {
  const out = items.slice();
  for (let i = out.length - 1; i > 0; i -= 1) {
    const j = Math.floor(rand() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
};

const kindOf = (gateId) => GATE_KIND[gateId] || "gut";

const reading = (compound, gateId) => (compound.gates || {})[gateId] || null;

const isUntested = (entry) => !entry || entry.status === "untested"
  || typeof entry.score !== "number";

// One measurement, one share of the crowd that gets through. A score of one lets
// nearly everything past and a score of zero still lets a little past, because a
// gate inside a body is never a wall.
const survival = (score) => 0.07 + 0.88 * Math.pow(clamp01(score), 1.25);

// The antiviral library dissolves well almost everywhere: 170 of its 182
// measured compounds sit in the top band. The station stays in for pacing, and
// its attrition is held down so it cannot decide a run.
const pacingGate = (wardId, kind) => wardId === "antiviral" && kind === "dissolve";

const gateDraw = (compound, gateId, rand) => {
  const entry = reading(compound, gateId);
  if (!isUntested(entry)) {
    return { score: clamp01(entry.score), untested: false, band: entry.band || 1,
             censored: entry.censored === true };
  }
  return { score: 0.12 + rand() * 0.76, untested: true, band: null, censored: false };
};

const doorGates = (gateOrder) => gateOrder.filter((id) => kindOf(id) === "door");

const stationX = (gateId, gateOrder) => {
  const kind = kindOf(gateId);
  if (kind !== "door") return STATION_X[kind] !== undefined ? STATION_X[kind] : 0.5;
  const index = doorGates(gateOrder).indexOf(gateId);
  return DOOR_X[Math.max(0, Math.min(DOOR_X.length - 1, index))];
};

const targetGateFor = (ward, virus) => {
  if (ward.id !== "antiviral") return ward.gateOrder.find((id) => kindOf(id) === "target");
  return virus;
};

const runGateOrder = (ward, virus) => {
  const chosen = targetGateFor(ward, virus);
  return ward.gateOrder
    .filter((id) => kindOf(id) !== "target" || id === chosen)
    .concat(ward.id === "antiviral" && !ward.gateOrder.includes(chosen) ? [chosen] : []);
};

const buildSteps = (ward, compound, virus, rand) => {
  const ids = runGateOrder(ward, virus);
  const seen = {};
  let alive = START_MOLECULES;
  let clock = 0;
  return ids.map((id) => {
    const kind = kindOf(id);
    // Two gates can share one station, so the second one stands a little
    // further down the course rather than on top of the first.
    seen[kind] = (seen[kind] || 0) + 1;
    const drawn = gateDraw(compound, id, rand);
    const opening = pacingGate(ward.id, kind)
      ? Math.max(survival(drawn.score), 0.9)
      : survival(drawn.score);
    const attrition = ATTRITION_KINDS.has(kind);
    const survivors = attrition ? Math.max(0, Math.round(alive * opening)) : alive;
    const step = {
      id, kind, opening,
      score: drawn.score,
      untested: drawn.untested,
      censored: drawn.censored,
      before: alive,
      survivors,
      lost: alive - survivors,
      x: stationX(id, ward.gateOrder) + (seen[kind] - 1) * 0.055,
      start: clock,
      resolveAt: clock + APPROACH_SECONDS,
      end: clock + APPROACH_SECONDS + RESOLVE_SECONDS,
    };
    alive = survivors;
    clock = step.end;
    return step;
  });
};

const assignDeaths = (steps, rand) => {
  const order = shuffled(Array.from({ length: START_MOLECULES }, (_, i) => i), rand);
  const diesAt = new Array(START_MOLECULES).fill(-1);
  let cursor = 0;
  steps.forEach((step, i) => {
    for (let k = 0; k < step.lost && cursor < order.length; k += 1, cursor += 1) {
      diesAt[order[cursor]] = i;
    }
  });
  return diesAt;
};

const laneY = (x, offset) => {
  const settled = CHANNEL.y + offset * CHANNEL.halfHeight * 0.8;
  const wall = LANDMARKS.gutWall || 0.205;
  if (x >= wall) return settled;
  return lerp(0.4 + offset * 0.11, settled, clamp01(x / Math.max(wall, 0.01)));
};

const makeMolecules = (steps, rand) => assignDeaths(steps, rand).map((dies, i) => {
  const offset = ((i % 7) / 3 - 1) + (rand() - 0.5) * 0.25;
  return {
    x: 0.05 + rand() * 0.06,
    y: 0.4 + offset * 0.1,
    vx: 0, vy: 0,
    size: 0.85 + rand() * 0.3,
    status: "travelling",
    offset,
    stage: 0,
    diesAt: dies,
    lostAt: null,
    fade: 0,
    wobble: rand() * Math.PI * 2,
    pace: 0.8 + rand() * 0.5,
  };
});

// All four medicines stay on screen every run. A door this compound was never
// tested against leaves its vial unknown rather than safe, because the absence
// of a test is not reassurance.
const buildPatient = (ward, compound, steps) => {
  const medicines = ward.medicines || [];
  if (!medicines.length) return null;
  return {
    medicines: medicines.map((med) => {
      const step = steps.find((s) => s.id === med.gate);
      const unknown = !step || step.untested;
      return {
        name: med.name,
        gate: med.gate,
        level: RESTING_LEVEL,
        danger: 0,
        crossing: 0,
        crossed: false,
        over: false,
        dry: false,
        hold: 0,
        unsettled: 0,
        unknown,
        note: unknown ? UNTESTED_VIAL.replace("{name}", med.name) : "",
      };
    }),
  };
};

const markLastAttrition = (steps) => {
  const losing = steps.filter((step) => ATTRITION_KINDS.has(step.kind));
  if (losing.length) losing[losing.length - 1].last = true;
  return steps;
};

const buildRun = (ward, compound, virus, seed) => {
  const rand = mulberry32(seed);
  const steps = buildSteps(ward, compound, virus, rand);
  const target = steps.find((step) => step.kind === "target") || null;
  const last = steps.length ? steps[steps.length - 1].end : 0;
  const patient = buildPatient(ward, compound, steps);
  // The last door or dial needs long enough after it for a vial to travel, stop
  // on the line and then fill above it.
  const tail = target ? FINALE_SECONDS
    : (patient ? MOVE_SECONDS + CROSSING_BEAT + 0.8 : 1.0);
  return {
    ward, compound, steps, target, patient,
    molecules: makeMolecules(markLastAttrition(steps), rand),
    resolved: 0,
    t: 0,
    finaleAt: last,
    endsAt: last + tail + OUTRO_SECONDS,
    health: 1,
    message: null,
    tipDue: null,
    done: false,
  };
};

// A censored measurement sits at or past the limit of what the assay could see,
// so its gate waits the way an unmeasured one does and then settles hard against
// the edge of its range rather than easing to somewhere in the middle.
const stepOpen = (step, t) => {
  if (t >= step.end) return step.opening;
  if (t >= step.resolveAt) {
    const k = (t - step.resolveAt) / RESOLVE_SECONDS;
    const eased = step.censored ? Math.min(1, k * 2.4) : 1 - Math.pow(1 - k, 3);
    return step.opening * eased;
  }
  return step.untested || step.censored ? 0.3 + 0.28 * Math.sin(t * 11) : 0;
};

const holdingCount = (molecules) => molecules.filter(
  (m) => m.status === "shredded" && m.fade < 0.6).length;

const medicineFor = (run, gateId) => (run.patient
  ? run.patient.medicines.find((med) => med.gate === gateId) : null);

// How hard the compound leans on a door. A gate the compound barely touches
// leaves the vial under the line; one it sits in pushes the vial well past it.
const lean = (score) => Math.pow(1 - clamp01(score), 1.6) * 0.6;

// However far a vial has to travel, it takes about the same time to get there,
// so the movement itself is legible rather than a jump.
const aimAt = (med, level) => {
  med.target = clamp01(level);
  med.rate = Math.abs(med.target - med.level) / MOVE_SECONDS;
};

const applyDoor = (run, step) => {
  const med = medicineFor(run, step.id);
  if (med && !step.untested) aimAt(med, RESTING_LEVEL + lean(step.score));
};

// An untested door or dial moves nothing. A vial only rises or drains on the
// strength of a measurement.
const applyDial = (run, step) => {
  if (!run.patient || step.untested) return;
  for (const med of run.patient.medicines) {
    if (med.unknown) continue;
    const from = med.target === undefined ? RESTING_LEVEL : med.target;
    aimAt(med, from - lean(step.score));
  }
};

// At most one line per run, and the cheerful one only when the whole trip went
// well, so the line still means something when it appears.
const noteStation = (run, step) => {
  if (step.lost / Math.max(step.before, 1) >= HEAVY_LOSS) {
    run.message = STATION_MESSAGE[step.kind] || null;
    run.spoke = true;
    if (step.kind === "liver") run.tipDue = "liver";
  } else if (step.last && !run.spoke && step.opening >= CLEAN_PASS) {
    run.message = COPY.cleanPass;
    run.spoke = true;
  }
  if (step.kind === "binding" && !run.tipDue) run.tipDue = "binding";
};

const killAtStep = (run, index) => {
  const step = run.steps[index];
  for (const m of run.molecules) {
    if (m.diesAt !== index || m.lostAt !== null) continue;
    m.status = LOST_STATUS[step.kind] || "bound";
    m.lostAt = step.id;
    m.vy = Math.sin(m.wobble * 3) * 0.012;
  }
  advanceSurvivors(run, index);
};

const advanceSurvivors = (run, index) => {
  for (const m of run.molecules) {
    if (m.lostAt === null && (m.diesAt === -1 || m.diesAt > index)) m.stage += 1;
  }
};

const resolveStep = (run, index) => {
  const step = run.steps[index];
  if (ATTRITION_KINDS.has(step.kind)) { killAtStep(run, index); noteStation(run, step); }
  else advanceSurvivors(run, index);
  if (step.kind === "door") {
    applyDoor(run, step);
    if (!run.toldDoor) { run.tipDue = "patient"; run.toldDoor = true; }
  } else if (step.kind === "dial") applyDial(run, step);
};

const moveMolecule = (run, stations, m, dt) => {
  if (m.lostAt !== null) {
    m.fade = Math.min(1, m.fade + dt * 0.45);
    m.y += m.vy + dt * 0.02;
    m.x += dt * 0.004;
    return;
  }
  const station = stations[m.stage];
  const targetX = station ? station.x - 0.015 : FINISH_X;
  const before = m.x;
  m.x += (targetX - m.x) * Math.min(1, dt * 1.6 * m.pace);
  m.wobble += dt * 2.2;
  m.y = laneY(m.x, m.offset) + Math.sin(m.wobble) * 0.01;
  m.vx = (m.x - before) / Math.max(dt, 0.001);
  if (!station && m.x > FINISH_X - 0.03) m.status = "arrived";
};

const dangerOf = (level) => {
  if (level > PRESCRIBED_LEVEL) return clamp01((level - PRESCRIBED_LEVEL) / 0.3);
  if (level < DRY_LEVEL) return clamp01((DRY_LEVEL - level) / 0.18);
  return 0;
};

// A medicine crosses the prescribed line once, and that crossing is the moment
// the patient is lost, so it gets a beat of its own: the level climbs at a
// steady rate, stops dead on the line, and only then does the excess build up
// above it. Draining reads the same way in the other direction.
const stepLevel = (med, dt) => {
  const want = med.target === undefined ? RESTING_LEVEL : med.target;
  const rising = want > med.level;
  const line = rising ? PRESCRIBED_LEVEL : DRY_LEVEL;
  const next = med.level + (rising ? 1 : -1) * dt * (med.rate || 1 / MOVE_SECONDS);
  const crosses = rising ? (med.level < line && next >= line)
    : (med.level > line && next <= line);
  if (crosses && !med.crossed) {
    med.level = line;
    med.crossed = true;
    med.hold = CROSSING_BEAT;
    med.crossing = 1;
    if (rising) med.over = true; else med.dry = true;
    return;
  }
  med.level = rising ? Math.min(next, want) : Math.max(next, want);
};

const updatePatient = (run, dt) => {
  if (!run.patient) return;
  for (const med of run.patient.medicines) {
    med.crossing = Math.max(0, (med.crossing || 0) - dt / 1.2);
    // A door nobody measured leaves its vial unresolved for the whole run.
    if (med.unknown) { med.unsettled = 0.5 + 0.5 * Math.sin(run.t * 2.1); continue; }
    if (med.hold > 0) { med.hold = Math.max(0, med.hold - dt); continue; }
    if (Math.abs((med.target === undefined ? RESTING_LEVEL : med.target) - med.level) > 0.001) {
      stepLevel(med, dt);
    }
    med.danger = dangerOf(med.level);
  }
};

const updateFinale = (run, dt) => {
  if (!run.target || run.t < run.target.resolveAt) return;
  const arrived = run.molecules.filter((m) => m.status === "arrived").length;
  run.health = Math.max(0,
    run.health - (arrived / START_MOLECULES) * run.target.score * dt * 0.55);
};

const advanceRun = (run, dt) => {
  run.t += dt;
  while (run.resolved < run.steps.length && run.t >= run.steps[run.resolved].resolveAt) {
    resolveStep(run, run.resolved);
    run.resolved += 1;
  }
  for (const m of run.molecules) moveMolecule(run, run.steps, m, dt);
  updatePatient(run, dt);
  updateFinale(run, dt);
  if (run.t >= run.endsAt) run.done = true;
};

const arrivedShare = (run) => run.molecules.filter(
  (m) => m.status === "arrived").length / START_MOLECULES;

const worstDanger = (run) => (run.patient
  ? run.patient.medicines.reduce((worst, m) => Math.max(worst, m.danger), 0)
  : 0);

const antiviralOutcome = (run, arrived, danger) => {
  const win = run.health <= 0.02 && danger < 0.5;
  let text = RESULTS.thin;
  if (run.health <= 0.02 && danger >= 0.5) text = RESULTS.harmed;
  else if (win) text = RESULTS.won;
  else if (arrived <= 0.02) text = RESULTS.none;
  return { win, text, score: clamp01(0.45 * arrived + 0.55 * (1 - run.health)) };
};

const harmText = (harmed) => {
  const piled = harmed.filter((med) => med.over);
  if (!piled.length) return RESULTS.safetyDrained;
  if (harmed.length === 1) return RESULTS.safetyOne.replace("{name}", piled[0].name);
  return RESULTS.safetyMany;
};

// Crossing the prescribed line is what loses the patient. How far past it the
// vial then climbs is what the score is made of.
const patientOutcome = (run, arrived, danger) => {
  const harmed = run.patient.medicines.filter((med) => med.over || med.dry);
  return {
    win: !harmed.length,
    text: harmed.length ? harmText(harmed) : RESULTS.safetyWon,
    score: clamp01(0.3 * Math.min(1, arrived / 0.4) + 0.7 * (1 - danger)),
  };
};

const libraryOutcome = (arrived) => ({
  win: arrived >= 0.3,
  text: arrived >= 0.3 ? RESULTS.libraryWon : RESULTS.libraryLost,
  score: clamp01(arrived / 0.7),
});

const runOutcome = (run) => {
  const arrived = arrivedShare(run);
  const danger = worstDanger(run);
  if (run.target) return antiviralOutcome(run, arrived, danger);
  if (run.patient) return patientOutcome(run, arrived, danger);
  return libraryOutcome(arrived);
};

const bestAndWorst = (compound, ward, virus) => {
  const scored = runGateOrder(ward, virus)
    .filter((id) => !pacingGate(ward.id, kindOf(id)) && !CLAUSELESS.has(kindOf(id)))
    .map((id) => ({ id, kind: kindOf(id), entry: reading(compound, id) }))
    .filter((g) => !isUntested(g.entry));
  if (!scored.length) return null;
  const sorted = scored.slice().sort((a, b) => a.entry.score - b.entry.score);
  return { worst: sorted[0], best: sorted[sorted.length - 1] };
};

const untestedPhrase = (ward, gateId) => withName(
  UNTESTED_PHRASE[gateId] || (kindOf(gateId) === "door" ? UNTESTED_DOOR : ""),
  ward, gateId);

const untestedSentence = (compound, ward, virus) => {
  const missing = runGateOrder(ward, virus).filter((id) => isUntested(reading(compound, id)));
  const phrase = missing.length ? untestedPhrase(ward, missing[0]) : "";
  if (!phrase) return "";
  return ` Nobody has measured ${phrase}, so that part is a gamble.`;
};

const clauseFor = (gate, ward, tone) => withName(CLAUSES[gate.kind][tone], ward, gate.id);

const cardSentence = (compound, ward, virus) => {
  const pair = bestAndWorst(compound, ward, virus);
  const tail = untestedSentence(compound, ward, virus);
  if (!pair) {
    return tail.trim()
      || "Nobody has measured this one at all, so the whole trip is a gamble.";
  }
  const good = clauseFor(pair.best, ward, "good");
  if (pair.best.id === pair.worst.id) return `${good}.${tail}`;
  const bad = clauseFor(pair.worst, ward, "bad");
  return `${good}, but ${bad.charAt(0).toLowerCase()}${bad.slice(1)}.${tail}`;
};

const STATION_GLYPH = {
  dissolve: (x, o) => `<ellipse cx="${x}" cy="12" rx="7" ry="${3 + 6 * o}"></ellipse>`,
  gut: (x, o) => `<rect x="${x - 3}" y="${12 - 9 * o}" width="6" height="${18 * o}" rx="2"></rect>`,
  pump: (x, o) => `<path d="M${x - 5} ${17 - 5 * o} h10 l-5 ${-5 - 4 * o} z"></path>`,
  liver: (x, o) => `<circle cx="${x}" cy="12" r="${3 + 5 * o}"></circle>`,
  binding: (x, o) => `<circle cx="${x - 4}" cy="9" r="${1 + 2.6 * o}"></circle>
    <circle cx="${x + 3}" cy="14" r="${1 + 2.6 * o}"></circle>`,
  target: (x, o) => `<circle cx="${x}" cy="12" r="7" fill="none" stroke="currentColor"
    stroke-width="1.6"></circle><circle cx="${x}" cy="12" r="${1 + 4 * o}"></circle>`,
  door: (x, o) => `<path d="M${x - 5} 20 V${12 - 6 * o} h10 V20" fill="none"
    stroke="currentColor" stroke-width="1.8"></path>`,
  dial: (x, o) => `<circle cx="${x}" cy="12" r="6.5" fill="none" stroke="currentColor"
    stroke-width="1.5"></circle><path d="M${x} 12 L${x + 5 * Math.cos((1 - o) * 3.1 - 1.6)}
    ${12 + 5 * Math.sin((1 - o) * 3.1 - 1.6)}" stroke="currentColor" stroke-width="1.6"></path>`,
};

const unknownGlyph = (x) => `<circle cx="${x}" cy="12" r="6" fill="none"
  stroke="currentColor" stroke-width="1.4" stroke-dasharray="3 3" opacity="0.7"></circle>`;

// The same stations as the big scene, in the same order and drawn the same way,
// so a card is read exactly like the run it predicts.
const journeyMarkup = (compound, ward, virus, gateText) => {
  const ids = runGateOrder(ward, virus);
  const width = Math.max(120, ids.length * 30);
  let reach = 1;
  const parts = ids.map((id, i) => {
    const x = 16 + i * ((width - 32) / Math.max(ids.length - 1, 1));
    const entry = reading(compound, id);
    const kind = kindOf(id);
    const open = isUntested(entry) ? 0.5 : clamp01(entry.score);
    if (!isUntested(entry) && ATTRITION_KINDS.has(kind)
        && !pacingGate(ward.id, kind)) reach *= survival(open);
    const glyph = isUntested(entry)
      ? unknownGlyph(x)
      : (STATION_GLYPH[kind] || STATION_GLYPH.gut)(x, open);
    const label = gateText[id] || "";
    return `<g><title>${esc(label)}</title>${glyph}</g>`;
  });
  const end = 16 + (width - 32) * clamp01(Math.pow(reach, 0.35));
  return `<svg class="game__journey" viewBox="0 0 ${width} 26" width="${width}" height="26"
      role="img" aria-hidden="true" fill="currentColor">
    <path d="M12 12 H${width - 12}" stroke="currentColor" stroke-width="1"
      opacity="0.25"></path>
    <path d="M12 12 H${end}" stroke="currentColor" stroke-width="2.4"
      stroke-linecap="round" opacity="0.55"></path>
    ${parts.join("")}</svg>`;
};

const cardMarkup = (compound, ward, virus, gateText) => {
  const sentence = cardSentence(compound, ward, virus);
  return `<button class="game__card" type="button" data-compound="${esc(compound.id)}"
      aria-label="Send in ${esc(compound.name)}. ${esc(sentence)}">
    <span class="game__art">${compound.structure_svg || ""}</span>
    <span class="game__name">${esc(compound.name)}</span>
    ${journeyMarkup(compound, ward, virus, gateText)}
    <span class="game__line">${esc(sentence)}</span>
  </button>`;
};

const pips = (value, count) => Array.from({ length: count }, (_, i) => (
  `<span class="game__pip" data-on="${i < Math.round(value * count) ? "yes" : "no"}"></span>`
)).join("");

const scoresMarkup = (best, runs) => `<dl class="game__scores">
  <div class="game__score"><dt>${COPY.bestLabel}</dt><dd>${pips(best, 5)}</dd></div>
  <div class="game__score"><dt>${COPY.runsLabel}</dt>
    <dd>${pips(Math.min(runs, 5) / 5, 5)}</dd></div></dl>`;

const adaptWard = (id, raw) => ({
  id,
  title: (WARD_COPY[id] || {}).title || raw.title || id,
  line: (WARD_COPY[id] || {}).line || raw.line || "",
  source: raw.source || "",
  gateOrder: raw.gate_order || raw.gates || [],
  medicines: (raw.patient_medicines || []).map((med) => ({
    name: med.display_name || med.drug_id, gate: med.gate,
  })),
  pool: (raw.pool || raw.compounds || []).map((c) => ({
    ...c,
    name: c.name || (c.known_drug ? c.known_drug.drug_id : c.id),
    rare: c.rare === true,
  })),
});

const adaptGame = (raw) => {
  const wards = raw && raw.wards ? raw.wards : {};
  const ids = Array.isArray(wards)
    ? wards.map((w) => w.id)
    : ["antiviral", "library", "safety"].filter((k) => wards[k])
      .concat(Object.keys(wards).filter((k) => !["antiviral", "library", "safety"].includes(k)));
  const get = (id, i) => (Array.isArray(wards) ? wards[i] : wards[id]);
  return {
    wards: ids.map((id, i) => adaptWard(id, get(id, i) || {})),
    gateText: (raw && raw.gate_text) || {},
  };
};

const emptyState = () => ({
  ward: "", phase: "choosing", molecules: [],
  gates: { dissolve: { open: 1 }, gut: { open: 1 }, liver: { open: 1, holding: 0 },
           binding: { open: 1 } },
  patient: null, banner: null, elapsed: 0,
});

const fillState = (state, run, phase, banner) => {
  state.ward = run.ward.id;
  state.phase = phase;
  state.molecules = run.molecules;
  state.elapsed = run.t;
  state.banner = banner;
  state.gates = {};
  for (const step of run.steps) {
    const key = sceneKey(step);
    const open = stepOpen(step, run.t);
    const gate = state.gates[key] || {};
    gate.open = run.t < step.start ? (gate.open === undefined ? 1 : gate.open) : open;
    gate.jammed = step.kind === "door" ? open < 0.4 : open < 0.25 && run.t >= step.end;
    gate.untested = step.untested;
    gate.edge = step.censored === true;
    if (key === "liver") gate.holding = holdingCount(run.molecules);
    state.gates[key] = gate;
  }
  if (run.target) state.gates.target = { health: run.health };
  state.patient = run.patient;
  return state;
};

export default {
  render({ model, el, signal }) {
    const root = document.createElement("div");
    root.className = "w game";
    root.innerHTML = `
      <section class="sect">
        <div class="game__head">
          <h2 class="game__title"></h2>
          <p class="game__blurb muted"></p>
        </div>
        <div class="game__stage"><canvas class="game__canvas" role="img"></canvas></div>
        <p class="sr game__said" role="status" aria-live="polite"></p>
        <div class="game__deck"></div>
        <p class="game__source">${esc(COPY.source)}</p>
      </section>
    `;
    el.appendChild(root);
    const unbindTheme = bindTheme(root, model);

    const stage = root.querySelector(".game__stage");
    const canvas = root.querySelector(".game__canvas");
    const title = root.querySelector(".game__title");
    const blurb = root.querySelector(".game__blurb");
    const deck = root.querySelector(".game__deck");
    // The banner is painted inside the canvas, where a screen reader cannot
    // reach it, so every banner is also spoken here.
    const said = root.querySelector(".game__said");

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    const state = emptyState();
    const toldTips = new Set();
    const framed = new Set();
    const played = new Set();

    let data = adaptGame(model.get("game"));
    let renderer = null;
    let wardIndex = 0;
    let runsHere = 0;
    let hand = [];
    let virus = VIRUS_OPTIONS[0].id;
    let run = null;
    let phase = "opening";
    let banner = null;
    let raf = null;
    let last = 0;
    let onScreen = true;
    let seed = (Date.now() ^ 0x5f3759df) >>> 0;
    let bestScore = 0;
    let runs = 0;

    const ward = () => data.wards[Math.min(wardIndex, data.wards.length - 1)] || null;
    const wanted = () => onScreen && !document.hidden && !reduced.matches;
    const nextSeed = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed; };

    const resize = () => {
      const width = Math.max(260, stage.clientWidth - 16);
      const height = Math.round(Math.min(380, Math.max(200, width * 0.46)));
      if (renderer) renderer.resize(width, height);
      else { canvas.style.width = `${width}px`; canvas.style.height = `${height}px`; }
    };

    const paint = (dt) => {
      if (!renderer) return;
      if (run) fillState(state, run, phase, banner);
      else { state.phase = phase; state.banner = banner; }
      renderer.render(state, dt);
    };

    const setBanner = (kind, text) => {
      banner = text ? { kind, text } : null;
      said.textContent = text || "";
    };

    const tip = (key) => {
      if (!key || toldTips.has(key) || !TIPS[key]) return;
      toldTips.add(key);
      setBanner("tip", TIPS[key]);
    };

    const describeScene = () => {
      if (!run) {
        canvas.setAttribute("aria-label",
          "A side view of the body the next compound will travel through.");
        return;
      }
      const untold = ((run.patient || {}).medicines || [])
        .filter((med) => med.unknown).map((med) => med.note).join(" ");
      canvas.setAttribute("aria-label",
        `${run.compound.name} is travelling through the body from left to right. ${untold}`.trim());
    };

    const pushProgress = () => {
      model.set("progress", {
        runs,
        best_score: Number(bestScore.toFixed(3)),
        ward_reached: (ward() || {}).id || "",
        compounds_played: Array.from(played),
      });
      model.save_changes();
    };

    // Two library compounds clear every measured gate, so they are kept out of
    // an opening hand and turn up later as a rare find.
    const dealable = (pool) => {
      const ordinary = pool.filter((c) => !c.rare);
      return runsHere === 0 || !pool.some((c) => c.rare) ? ordinary : pool;
    };

    const drawHand = () => {
      const current = ward();
      if (!current) return;
      const rand = mulberry32(nextSeed());
      hand = shuffled(dealable(current.pool), rand).slice(0, 3);
    };

    const virusMarkup = () => {
      if ((ward() || {}).id !== "antiviral") return "";
      const buttons = VIRUS_OPTIONS.map((option) => `<button class="game__pick"
        type="button" data-virus="${option.id}"
        aria-pressed="${option.id === virus}">${esc(option.label)}</button>`).join("");
      return `<div class="game__choice"><span class="game__prompt">${esc(VIRUS_PROMPT)}</span>
        ${buttons}</div><p class="game__prompt">${esc(VIRUS_NOTE)}</p>`;
    };

    const showOpening = () => {
      phase = "opening";
      title.textContent = COPY.title;
      blurb.textContent = COPY.standfirst;
      deck.innerHTML = `<div class="game__after"><button class="btn-solid game__start"
        type="button">${esc(COPY.start)}</button></div>`;
      describeScene();
    };

    const showHand = (fresh) => {
      phase = "choosing";
      const current = ward();
      if (!current) { showOpening(); return; }
      title.textContent = current.title;
      blurb.textContent = current.line;
      if (fresh) drawHand();
      const cards = hand.map((c) => cardMarkup(c, current, virus, data.gateText)).join("");
      deck.innerHTML = `${virusMarkup()}
        <p class="game__prompt">${esc(COPY.handPrompt)}</p>
        <div class="game__hand">${cards}</div>
        ${runs ? scoresMarkup(bestScore, runs) : ""}`;
      describeScene();
      if (!framed.has(current.id) && WARD_FRAMING[current.id]) {
        framed.add(current.id);
        setBanner("tip", WARD_FRAMING[current.id]);
      }
    };

    const advanceWard = () => {
      wardIndex = Math.min(wardIndex + 1, data.wards.length - 1);
      runsHere = 0;
      showHand(true);
      paint(0);
    };

    const finishRun = () => {
      phase = "resolved";
      const outcome = runOutcome(run);
      runs += 1;
      runsHere += 1;
      played.add(run.compound.id);
      bestScore = Math.max(bestScore, outcome.score);
      setBanner("result", outcome.text);
      const moveOn = runsHere >= RUNS_PER_WARD && wardIndex < data.wards.length - 1;
      deck.innerHTML = `<div class="game__after">
        <button class="btn-solid game__next" type="button" data-move="${moveOn}">
          ${esc(moveOn ? COPY.nextWard : COPY.again)}</button>
        ${scoresMarkup(bestScore, runs)}</div>`;
      pushProgress();
      paint(0);
    };

    const step = (dt) => {
      advanceRun(run, dt);
      if (run.message) { setBanner("result", run.message); run.message = null; }
      if (run.tipDue) { tip(run.tipDue); run.tipDue = null; }
      if (run.done) finishRun();
    };

    const settle = () => {
      while (!run.done) step(1 / 30);
      paint(0);
    };

    const frame = (now) => {
      if (!wanted() || phase !== "running") { raf = null; return; }
      const dt = Math.min(0.05, (now - last) / 1000 || 0.016);
      last = now;
      step(dt);
      paint(dt);
      if (phase !== "running") { raf = null; return; }
      raf = requestAnimationFrame(frame);
    };

    const startLoop = () => {
      if (raf !== null || phase !== "running") return;
      last = performance.now();
      raf = requestAnimationFrame(frame);
    };

    const stopLoop = () => {
      if (raf !== null) cancelAnimationFrame(raf);
      raf = null;
    };

    const sendIn = (compound) => {
      run = buildRun(ward(), compound, virus, nextSeed());
      phase = "running";
      setBanner(null, "");
      deck.innerHTML = "";
      describeScene();
      if (reduced.matches) { settle(); return; }
      paint(0);
      startLoop();
    };

    const onDeckClick = (event) => {
      const pick = event.target.closest("[data-virus]");
      if (pick) { virus = pick.dataset.virus; showHand(false); return; }
      const card = event.target.closest("[data-compound]");
      if (card) {
        const compound = hand.find((c) => c.id === card.dataset.compound);
        if (compound) sendIn(compound);
        return;
      }
      if (event.target.closest(".game__start")) { showHand(true); paint(0); return; }
      const next = event.target.closest(".game__next");
      if (!next) return;
      if (next.dataset.move === "true") advanceWard();
      else { showHand(true); paint(0); }
    };

    const onCanvasClick = (event) => {
      if (!renderer || phase !== "resolved") return;
      const box = canvas.getBoundingClientRect();
      const id = renderer.hitTest(event.clientX - box.left, event.clientY - box.top);
      if (id === "banner") { setBanner(null, ""); paint(0); }
    };

    const onGame = () => {
      data = adaptGame(model.get("game"));
      wardIndex = 0;
      runsHere = 0;
      run = null;
      showOpening();
      paint(0);
    };

    const onTheme = () => paint(0);

    if (__art.makeRenderer) renderer = __art.makeRenderer(canvas, model.get("theme") || "");
    resize();
    showOpening();
    paint(0);

    const observer = new ResizeObserver(() => { resize(); paint(0); });
    observer.observe(stage);

    const watcher = new IntersectionObserver((entries) => {
      onScreen = entries.some((entry) => entry.isIntersecting);
      if (onScreen) startLoop(); else stopLoop();
    }, { threshold: 0.01 });
    watcher.observe(stage);

    const onHidden = () => (document.hidden ? stopLoop() : startLoop());
    const onReduced = () => {
      if (reduced.matches && phase === "running") { stopLoop(); settle(); }
      else startLoop();
    };

    deck.addEventListener("click", onDeckClick, { signal });
    canvas.addEventListener("click", onCanvasClick, { signal });
    document.addEventListener("visibilitychange", onHidden, { signal });
    reduced.addEventListener("change", onReduced, { signal });
    model.on("change:game", onGame);
    model.on("change:theme", onTheme);

    signal.addEventListener("abort", () => {
      stopLoop();
      observer.disconnect();
      watcher.disconnect();
      unbindTheme();
      model.off("change:game", onGame);
      model.off("change:theme", onTheme);
      if (renderer) renderer.destroy();
      renderer = null;
      el.innerHTML = "";
    });
  },
};
"""


_ESM = JS_PRELUDE + _art_scope() + _ENGINE


def _inline_svg(path: Path, slug: str) -> str:
    """One RDKit drawing, ready to sit beside two others in the same document.

    Every drawing the toolkit writes names its classes `a0`, `a1` and so on, so
    three cards on a page would each redefine the others' colours. The classes
    are renamed per compound, the fixed pixel size is dropped so the card can
    scale it, and the carbon skeleton is drawn in whatever ink the reader's
    theme is using rather than in black.
    """
    svg = path.read_text()
    svg = re.sub(r"\s(width|height)='\d+'", "", svg, count=2)
    svg = re.sub(r"\.a(\d+)\{", rf".{slug}-a\1{{", svg)
    svg = re.sub(r"class='a(\d+)'", rf"class='{slug}-a\1'", svg)
    return svg.replace("#000000", "currentColor")


def _measured_enzyme_gates(compound: dict) -> int:
    gates = compound.get("gates", {})
    return sum(1 for gate in ENZYME_GATES
               if gates.get(gate, {}).get("status") == "measured")


def _playable(ward_id: str, compound: dict) -> bool:
    """A safety compound with fewer than two measured doors is a coin flip, so it
    never reaches the hand."""
    if ward_id != "safety":
        return True
    return _measured_enzyme_gates(compound) >= 2


def _spread(pool: list, wanted: int) -> list:
    """A hand pool taken evenly across the range of compounds, worst to best."""
    ranked = sorted(pool, key=lambda c: c.get("mean_gate_score") or 0)
    if len(ranked) <= wanted:
        return ranked
    stride = len(ranked) / wanted
    return [ranked[int(i * stride)] for i in range(wanted)]


def _trim(compound: dict, base: Path, target_alias: dict | None) -> dict:
    gates = dict(compound.get("gates", {}))
    if target_alias:
        gates.update(target_alias)
    out = {
        "id": compound["id"],
        "name": (compound.get("known_drug") or {}).get("drug_id") or compound["id"],
        "gates": gates,
        "rare": compound["id"] in RARE_COMPOUNDS,
    }
    art = base / str(compound.get("structure") or "")
    if compound.get("structure") and art.is_file():
        out["structure_svg"] = _inline_svg(art, re.sub(r"[^A-Za-z0-9]", "", compound["id"]))
    return out


def load_game(path, per_ward: int = HAND_POOL) -> dict:
    """Read `data/game.json` and cut it down to what the widget has to carry.

    The built file holds every compound with its structure, its provenance and
    its raw values, which is far more than one hand of three cards needs. This
    keeps a spread of compounds per ward, inlines each one's drawing so a static
    export has no file to fetch, and leaves everything else on disk for the
    notebook's own sections to read.
    """
    path = Path(path)
    raw = json.loads(path.read_text())
    wards = {}
    for ward_id in [w for w in WARD_ORDER if w in raw["wards"]] + [
            w for w in raw["wards"] if w not in WARD_ORDER]:
        source = raw["wards"][ward_id]
        pool = [c for c in source.get("pool", []) if _playable(ward_id, c)]
        keep = {c["id"]: c for c in _spread(pool, per_ward)}
        keep.update({c["id"]: c for c in pool if c["id"] in RARE_COMPOUNDS})
        wards[ward_id] = {
            "title": source.get("title", ward_id),
            "line": source.get("line", ""),
            "source": source.get("source", ""),
            "gate_order": source.get("gate_order", []),
            "patient_medicines": [
                {"display_name": m["display_name"], "gate": m["gate"]}
                for m in source.get("patient_medicines", [])
            ],
            "pool": [
                _trim(c, path.parent, _mers_alias(c) if ward_id == "antiviral" else None)
                for c in keep.values()
            ],
        }
    return {"wards": wards, "gate_text": raw.get("gate_text", {})}


def _mers_alias(compound: dict) -> dict:
    """The second virus, carried as a gate so the engine can run it like the first."""
    mers = (compound.get("extras") or {}).get("mers_potency")
    return {"reach_target_mers": mers} if mers else {}


class Gauntlet(anywidget.AnyWidget):
    """One compound, one ward, and everything the body puts between them.

    In from Python: `game`, the trimmed contents of `data/game.json` as
    `load_game` returns it. Back to Python: `progress`, holding the number of
    runs played, the best run so far as a fraction between zero and one, the
    identifier of the ward the player has reached, and the compounds they sent
    in.
    """

    _esm = _ESM
    _css = _CSS

    game = traitlets.Dict().tag(sync=True)
    progress = traitlets.Dict(
        {"runs": 0, "best_score": 0.0, "ward_reached": "", "compounds_played": []}
    ).tag(sync=True)
    theme = traitlets.Unicode("").tag(sync=True)
