const Physics = (() => {
  const ABSORB = 1.6;
  const OVERDOSE = 0.92;
  const GRACE = 2;
  const PILL_COOLDOWN = 0.6;
  const DEFAULT_TURNOVER = 0.045;
  const TEST_DURATION = 2;
  const INJECTION_RATE = 3;

  function randomIn([low, high], random) {
    return low + random() * (high - low);
  }

  function scheduleEvents(level, random) {
    return (level.events ?? []).map((event) => {
      const start = randomIn(event.start, random);
      const stop = event.length ? start + randomIn(event.length, random) : Infinity;
      return { ...event, start, stop };
    });
  }

  function newTank(spec) {
    return { level: 0, pills: [], lastPill: -Infinity, inBand: 0, paused: false, nextAuto: spec.auto?.offset ?? 0, injecting: 0 };
  }

  function createState(level, random = Math.random) {
    return {
      time: 0,
      enzyme: 1,
      block: 0,
      random,
      tanks: level.tanks.map(newTank),
      events: scheduleEvents(level, random),
      boostersLeft: level.boosters?.count ?? 0,
      injectionsLeft: level.injections?.count ?? 0,
      testsLeft: level.bloodTests ?? 0,
      revealUntil: -Infinity,
      outcome: null,
      overdosedTank: null,
    };
  }

  function activeEvents(state) {
    return state.events.filter((event) => state.time >= event.start && state.time < event.stop);
  }

  function pillReady(state, index = 0) {
    return state.time - state.tanks[index].lastPill >= PILL_COOLDOWN;
  }

  function addPill(state, spec, tank) {
    const variance = spec.gate ? 1 + (state.random() - 0.5) * (spec.gateVariance ?? 0) : 1;
    tank.pills.push({ remaining: spec.dose, age: 0, variance });
  }

  function takePill(state, level, index = 0) {
    if (state.outcome || !pillReady(state, index)) return false;
    const tank = state.tanks[index];
    tank.lastPill = state.time;
    addPill(state, level.tanks[index], tank);
    return true;
  }

  function takeBooster(state, level) {
    if (state.outcome || state.boostersLeft <= 0) return false;
    state.boostersLeft -= 1;
    const effect = level.boosters.effect;
    state.events.push({ ...effect, drug: level.boosters.drug, booster: true, start: state.time, stop: state.time + effect.duration });
    return true;
  }

  function giveInjection(state, level) {
    if (state.outcome || state.injectionsLeft <= 0) return false;
    state.injectionsLeft -= 1;
    state.tanks[0].injecting += level.injections.amount;
    return true;
  }

  function takeBloodTest(state) {
    if (state.outcome || state.testsLeft <= 0) return false;
    state.testsLeft -= 1;
    state.revealUntil = state.time + TEST_DURATION;
    return true;
  }

  function togglePause(state, index) {
    if (state.outcome) return false;
    state.tanks[index].paused = !state.tanks[index].paused;
    return true;
  }

  function isRevealed(state, level) {
    return !level.blind || state.outcome !== null || state.time < state.revealUntil;
  }

  function sumOf(events, key) {
    return events.reduce((sum, event) => sum + (event[key] ?? 0), 0);
  }

  function competition(state, level) {
    return level.tanks.reduce((sum, spec, index) => sum + (spec.compete ?? 0) * state.tanks[index].level, 0);
  }

  function updateEnzyme(state, level, active, dt) {
    const targetBlock = Math.min(0.95, sumOf(active, "block") + competition(state, level));
    state.block += (targetBlock - state.block) * Math.min(1, dt * 3);
    const target = 1 + sumOf(active, "induce");
    const turnover = level.turnover ?? DEFAULT_TURNOVER;
    state.enzyme += (turnover * (target - state.enzyme) - sumOf(active, "kill") * state.enzyme) * dt;
  }

  function capacity(state) {
    return state.enzyme * (1 - state.block);
  }

  function throughGate(state, spec, variance = 1) {
    return Math.max(0.05, 1 - (spec.gate ?? 0) * variance * capacity(state));
  }

  function landingTime(spec) {
    return spec.gate ? 0.55 : 0.3;
  }

  function autoDose(state, level) {
    level.tanks.forEach((spec, index) => {
      const tank = state.tanks[index];
      if (!spec.auto || state.time < tank.nextAuto) return;
      tank.nextAuto += spec.auto.period;
      if (!tank.paused) addPill(state, spec, tank);
    });
  }

  function absorb(state, spec, tank, dt) {
    let entered = 0;
    for (const pill of tank.pills) {
      pill.age += dt;
      if (pill.age < landingTime(spec)) continue;
      const amount = pill.remaining * Math.min(1, ABSORB * dt);
      pill.remaining -= amount;
      entered += amount * throughGate(state, spec, pill.variance);
    }
    tank.pills = tank.pills.filter((pill) => pill.remaining > 0.004);
    const injected = Math.min(tank.injecting, INJECTION_RATE * dt);
    tank.injecting -= injected;
    return entered + injected;
  }

  function inBand(tank, spec) {
    return tank.level >= spec.band[0] && tank.level <= spec.band[1];
  }

  function stepTank(state, level, index, dt) {
    const spec = level.tanks[index];
    const tank = state.tanks[index];
    const entered = absorb(state, spec, tank, dt);
    tank.level += entered - spec.drain * capacity(state) * tank.level * dt;
    if (state.time > GRACE && inBand(tank, spec)) tank.inBand += dt;
    if (tank.level >= OVERDOSE && !state.outcome) {
      state.outcome = "overdose";
      state.overdosedTank = index;
    }
  }

  function step(state, level, dt) {
    if (state.outcome) return;
    state.time += dt;
    updateEnzyme(state, level, activeEvents(state), dt);
    autoDose(state, level);
    level.tanks.forEach((_, index) => stepTank(state, level, index, dt));
    if (!state.outcome && state.time >= level.duration) state.outcome = "done";
  }

  function score(state, level) {
    const total = state.tanks.reduce((sum, tank) => sum + tank.inBand, 0);
    return total / (state.tanks.length * (level.duration - GRACE));
  }

  return {
    OVERDOSE, GRACE, PILL_COOLDOWN, TEST_DURATION,
    createState, step, takePill, takeBooster, giveInjection, takeBloodTest, togglePause,
    pillReady, isRevealed, activeEvents, capacity, throughGate, landingTime, inBand, score,
  };
})();

const WORLDS = [
  { name: "The drain", enzyme: "cyp2d6", enzymeName: "CYP2D6" },
  { name: "Two prescriptions", enzyme: "cyp2d6", enzymeName: "CYP2D6" },
  { name: "The gatekeeper", enzyme: "cyp3a4", enzymeName: "CYP3A4" },
  { name: "Paxlovid", enzyme: "cyp3a4", enzymeName: "CYP3A4" },
  { name: "Blind", enzyme: "cyp2d6", enzymeName: "CYP2D6" },
  { name: "A week on antifungals", enzyme: "cyp3a4", enzymeName: "CYP3A4" },
];

const STANDARD_BAND = [0.4, 0.66];

const LEVELS = [
  {
    world: 0, title: "Find the rhythm", duration: 14,
    tanks: [{ medicine: "metoprolol", label: "Blood pressure", drain: 0.3, dose: 0.3, band: STANDARD_BAND, key: "Space" }],
    tips: [
      { when: "start", anchor: "tank", text: "Tap the beaker to take a pill", until: "pill" },
      { when: "time:2.5", anchor: "tank", text: "Keep the water inside the green band" },
      { when: "nearTop", anchor: "liver", text: "Wait while the enzymes drain it" },
    ],
    learned: "drug clearance", reveal: "Liver enzymes remove medicine from your blood, so doses have to keep coming.",
  },
  {
    world: 0, title: "The slow one", duration: 22,
    tanks: [{ medicine: "metoprolol", label: "Blood pressure", drain: 0.12, dose: 0.3, band: STANDARD_BAND, key: "Space" }],
    tips: [{ when: "start", anchor: "liver", text: "These enzymes clear this medicine slowly" }],
    learned: "half-life", reveal: "A medicine that clears slowly lasts longer, so it needs fewer doses and forgives fewer mistakes.",
  },
  {
    world: 1, title: "Two prescriptions", duration: 36,
    tanks: [
      { medicine: "metoprolol", label: "Blood pressure", drain: 0.3, dose: 0.3, band: STANDARD_BAND, key: "Space" },
      { medicine: "paroxetine", label: "Depression", drain: 0.22, dose: 0.3, band: STANDARD_BAND, compete: 0.9, key: "Digit1" },
    ],
    tips: [
      { when: "start", anchor: "tank", text: "Tap a beaker to dose it" },
      { when: "time:4", anchor: "liver", text: "The depression pill also jams the enzymes" },
    ],
    learned: "drug interactions", reveal: "The depression pill blocked the enzyme that clears both pills, so both built up.",
  },
  {
    world: 2, title: "The long way in", duration: 32,
    tanks: [{ medicine: "felodipine", label: "Blood pressure", drain: 0.3, dose: 2.0, gate: 0.85, gateVariance: 0.7, band: [0.38, 0.7], key: "Space" }],
    injections: { count: 8, amount: 0.18 },
    tips: [
      { when: "start", anchor: "gate", text: "The liver takes an unpredictable bite of each pill" },
      { when: "time:4", anchor: "tokens", text: "Injections skip the liver and give an exact dose" },
    ],
    learned: "first-pass metabolism", reveal: "Swallowed pills pass through the liver before your blood and lose part of each dose there. Injections skip it.",
  },
  {
    world: 2, title: "Hit twice", duration: 34,
    tanks: [{ medicine: "felodipine", label: "Blood pressure", drain: 0.3, dose: 0.7, gate: 0.5, gateVariance: 0.8, band: [0.38, 0.7], key: "Space" }],
    injections: { count: 3, amount: 0.22 },
    events: [{ drug: "isavuconazole", label: "An antifungal", kind: "sits", block: 0.6, start: [6, 10], length: [9, 12] }],
    tips: [],
    learned: "enzyme inhibition", reveal: "A blocked liver lets more of each pill through and clears it more slowly, so every dose hits twice.",
  },
  {
    world: 3, title: "Boost it on purpose", duration: 40, turnover: 0.03,
    tanks: [{ medicine: "nirmatrelvir", label: "COVID", drain: 2.0, dose: 0.4, gate: 0.5, band: [0.38, 0.7], key: "Space" }],
    boosters: { drug: "ritonavir", label: "Ritonavir", count: 3, effect: { kind: "breaks", block: 0.5, kill: 0.35, duration: 4 } },
    tips: [
      { when: "start", anchor: "liver", text: "The COVID pill drains almost at once" },
      { when: "time:3", anchor: "tokens", text: "Ritonavir disables the enzymes" },
    ],
    learned: "boosting", reveal: "Paxlovid pairs these two drugs because ritonavir blocks the liver enzyme that would clear the COVID drug.",
  },
  {
    world: 4, title: "Blind", duration: 38, bloodTests: 3, blind: true, turnover: 0.09,
    tanks: [{ medicine: "metoprolol", label: "Blood pressure", drain: 0.3, dose: 0.3, band: [0.38, 0.7], key: "Space" }],
    events: [{ drug: "rifampicin", label: "An antibiotic", kind: "induces", induce: 1.5, start: [5, 8], length: [12, 15] }],
    tips: [
      { when: "start", anchor: "tank", text: "You can't see the level anymore" },
      { when: "time:2.5", anchor: "tokens", text: "A blood test shows the level for 2 seconds" },
      { when: "event", anchor: "liver", text: "Watch the enzymes for clues" },
    ],
    learned: "enzyme induction", reveal: "The antibiotic made the liver build extra enzyme, which cleared medicine faster and lingered after the last dose.",
  },
  {
    world: 4, title: "Blind, and broken", duration: 36, bloodTests: 3, blind: true,
    tanks: [{ medicine: "metoprolol", label: "Blood pressure", drain: 0.3, dose: 0.3, band: [0.38, 0.7], key: "Space" }],
    events: [{ drug: "ritonavir", label: "An HIV medicine", kind: "breaks", block: 0.25, kill: 0.2, start: [6, 11], length: [8, 12] }],
    tips: [],
    learned: "time-dependent inhibition", reveal: "Some drugs destroy the enzyme instead of blocking it, so the drain stays slow until the liver builds more.",
  },
  {
    world: 5, title: "A week on antifungals", duration: 48,
    tanks: [
      { medicine: "isavuconazole", label: "Fungal infection", drain: 0.35, dose: 0.3, band: [0.38, 0.7], compete: 0.9, key: "Space" },
      { medicine: "simvastatin", label: "Cholesterol", drain: 0.45, dose: 0.36, band: [0.3, 0.72], auto: { period: 1.8, offset: 0.2 }, key: "Digit1" },
      { medicine: "felodipine", label: "Blood pressure", drain: 0.3, dose: 0.36, band: [0.3, 0.72], auto: { period: 2.4, offset: 0.9 }, key: "Digit2" },
      { medicine: "midazolam", label: "Sedative", drain: 0.18, dose: 0.3, band: [0.3, 0.72], auto: { period: 3.2, offset: 1.6 }, key: "Digit3" },
    ],
    tips: [
      { when: "start", anchor: "tank", text: "Tap the antifungal to dose it" },
      { when: "time:5", anchor: "tank:1", text: "Tap any other beaker to pause it" },
    ],
    learned: "managing interactions", reveal: "One way doctors handle an interaction is to pause a medicine for the length of a short course.",
  },
];

if (typeof module !== "undefined") module.exports = { Physics, WORLDS, LEVELS };
