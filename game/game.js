function mountDrain(root, host = {}) {
  const BOARD_W = 400;
  const BOARD_H = 560;
  const BASE_COPIES = 7;
  const MAX_COPIES = 14;
  const COPY_SIZE = 46;
  const PAPER = {
    ground: "#EDF1F0",
    grain: "rgba(26, 33, 36, 0.05)",
    ink: "#1A2124",
    inkSoft: "#5B686E",
    water: "#D4E6F1",
    waterLine: "#4F8DB8",
    frost: "#DDE3E6",
    band: "#3E9B6A",
    danger: "#FF6A1F",
    tissue: "#E0E8E5",
    capsule: "#7FB6DA",
    capsuleCap: "#FBFCFC",
  };
  const SPECIALS = [
    { id: "booster", key: "KeyR", shortcut: "R", has: (level) => Boolean(level.boosters), total: (level) => level.boosters.count, left: (state) => state.boostersLeft, name: (level) => level.boosters.label },
    { id: "injection", key: "KeyI", shortcut: "I", has: (level) => Boolean(level.injections), total: (level) => level.injections.count, left: (state) => state.injectionsLeft, name: () => "an injection" },
    { id: "test", key: "KeyB", shortcut: "B", has: (level) => Boolean(level.bloodTests), total: (level) => level.bloodTests, left: (state) => state.testsLeft, name: () => "a blood test" },
  ];
  const SHORTCUTS = { Space: "Space", Digit1: "1", Digit2: "2", Digit3: "3" };
  const TOKEN_GAP = 30;
  const calmMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

  const byId = (id) => root.querySelector(`#${id}`);
  const canvas = byId("board");
  const context = canvas.getContext("2d");
  const ui = {
    title: byId("level-title"),
    score: byId("score"),
    tip: byId("tip"),
    game: byId("game-view"),
    levels: byId("levels-view"),
    levelList: byId("level-list"),
    showLevels: byId("show-levels"),
    hits: byId("hits"),
    result: byId("result"),
    resultTitle: byId("result-title"),
    resultStars: byId("result-stars"),
    resultMeter: byId("result-meter"),
    resultFill: byId("result-fill"),
    resultValue: byId("result-value"),
    resultReveal: byId("result-reveal"),
    retry: byId("retry"),
    next: byId("next"),
    announcer: byId("announcer"),
  };

  const images = Object.fromEntries(Object.entries(SPRITES).map(([key, src]) => {
    const image = new Image();
    image.src = src;
    return [key, image];
  }));
  const grain = makeGrain();
  const slotOrder = [3, 2, 4, 1, 5, 0, 6, 10, 9, 11, 8, 12, 7, 13];

  let levelIndex = 0;
  let level = LEVELS[0];
  let world = WORLDS[0];
  let state = null;
  let view = null;
  let hits = { tanks: [], tray: null };
  let best = { ...loadBest(), ...(host.initialBest ?? {}) };
  let frameId = null;
  let resizeObserver = null;

  function loadBest() {
    try {
      return JSON.parse(localStorage.getItem("drain-best-v2") || "{}");
    } catch (error) {
      return {};
    }
  }

  function saveBest() {
    try {
      localStorage.setItem("drain-best-v2", JSON.stringify(best));
    } catch (error) {
      /* progress is a convenience */
    }
  }

  function makeGrain() {
    const grainCanvas = document.createElement("canvas");
    grainCanvas.width = BOARD_W * 2;
    grainCanvas.height = BOARD_H * 2;
    const grainContext = grainCanvas.getContext("2d");
    grainContext.fillStyle = PAPER.grain;
    for (let i = 0; i < 9000; i += 1) {
      grainContext.fillRect(Math.random() * grainCanvas.width, Math.random() * grainCanvas.height, 1.4, 1.4);
    }
    return grainCanvas;
  }

  function seededMolecules() {
    return Array.from({ length: 30 }, (_, index) => ({
      x: 0.08 + ((index * 0.6180339) % 1) * 0.84,
      depth: 0.08 + ((index * 0.7548776) % 1) * 0.84,
      phase: index * 1.7,
      tilt: ((index * 0.4142) % 1) * 6.28,
    }));
  }

  function newView() {
    return {
      phase: "ready",
      copies: [],
      particles: [],
      callouts: [],
      seenEvents: new Set(),
      pillX: new WeakMap(),
      landed: new WeakSet(),
      bitten: new WeakSet(),
      molecules: seededMolecules(),
      lastReading: null,
      shake: 0,
      flash: 0,
      wobble: level.tanks.map(() => 0),
      clock: 0,
    };
  }

  /* ---------- geometry ---------- */

  const TANK_LAYOUTS = {
    1: [[104, 296]],
    2: [[40, 180], [220, 360]],
    4: [[20, 124], [140, 206], [222, 288], [304, 370]],
  };

  function geometry() {
    const gated = Boolean(level.tanks[0].gate);
    const tankTop = gated ? 160 : (level.tanks.length > 1 ? 84 : 64);
    const tanks = TANK_LAYOUTS[level.tanks.length].map(([left, right]) => ({ left, right, top: tankTop, bottom: 398 }));
    return { gated, tanks, gateTop: 82, gateBottom: 134, liverTop: 432, liverBottom: 548 };
  }

  function levelToY(amount, tank) {
    return tank.bottom - amount * (tank.bottom - tank.top);
  }

  function tankCenter(tank) {
    return (tank.left + tank.right) / 2;
  }

  function slotPosition(slot, g) {
    const row = slot < 7 ? 0 : 1;
    const col = slot % 7;
    return { x: 56 + col * 48 + row * 24, y: g.liverTop + 38 + row * 50 };
  }

  function gateCopyPositions(g) {
    const y = (g.gateTop + g.gateBottom) / 2;
    return [150, 200, 250].map((x) => ({ x, y }));
  }

  function medicineImage(name) {
    return images[`${name}_med`] ?? images[name];
  }

  /* ---------- tap targets ---------- */

  function activeSpecial() {
    return SPECIALS.find((special) => special.has(level)) ?? null;
  }

  function trayRect() {
    const special = activeSpecial();
    if (!special) return null;
    return { x: 12, y: 12, width: 22 + special.total(level) * TOKEN_GAP, height: 40 };
  }

  function tankHitRect(tank) {
    return { x: tank.left - 10, y: tank.top - 40, width: tank.right - tank.left + 20, height: tank.bottom - tank.top + 50 };
  }

  function placeHit(button, rect) {
    button.style.left = `${(rect.x / BOARD_W) * 100}%`;
    button.style.top = `${(rect.y / BOARD_H) * 100}%`;
    button.style.width = `${(rect.width / BOARD_W) * 100}%`;
    button.style.height = `${(rect.height / BOARD_H) * 100}%`;
  }

  function makeHit(rect, shortcut, onActivate) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "hit";
    button.setAttribute("aria-keyshortcuts", shortcut);
    placeHit(button, rect);
    button.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      onActivate();
    });
    button.addEventListener("click", (event) => {
      if (event.detail === 0) onActivate();
    });
    ui.hits.append(button);
    return button;
  }

  function buildHits() {
    ui.hits.innerHTML = "";
    const g = geometry();
    hits = { tanks: [], tray: null };
    level.tanks.forEach((spec, index) => {
      const activate = spec.auto ? () => togglePause(index) : () => takePill(index);
      hits.tanks[index] = makeHit(tankHitRect(g.tanks[index]), SHORTCUTS[spec.key], activate);
    });
    const special = activeSpecial();
    if (special) hits.tray = makeHit(trayRect(), special.shortcut, () => useSpecial(special.id));
  }

  function plainLabel(label) {
    return label === label.toUpperCase() ? label : label.charAt(0).toLowerCase() + label.slice(1);
  }

  function refreshHits() {
    const done = view.phase === "done";
    level.tanks.forEach((spec, index) => {
      const button = hits.tanks[index];
      const paused = state.tanks[index].paused;
      const action = spec.auto ? `${paused ? "Resume" : "Pause"} the ${plainLabel(spec.label)} medicine` : `Take a pill for ${plainLabel(spec.label)}`;
      button.setAttribute("aria-label", action);
      button.disabled = done;
    });
    const special = activeSpecial();
    if (!special) return;
    const left = special.left(state);
    hits.tray.setAttribute("aria-label", `Use ${special.name(level)}, ${left} left`);
    hits.tray.disabled = done || left <= 0;
  }

  /* ---------- actions ---------- */

  function begin() {
    if (view.phase === "ready") view.phase = "running";
  }

  function takePill(index) {
    if (view.phase === "done") return;
    if (Physics.takePill(state, level, index)) begin();
  }

  function togglePause(index) {
    if (view.phase === "done") return;
    Physics.togglePause(state, index);
    begin();
    refreshHits();
    announce(`${level.tanks[index].label} ${state.tanks[index].paused ? "paused" : "resumed"}.`);
  }

  const SPECIAL_ACTIONS = {
    booster: () => {
      if (!Physics.takeBooster(state, level)) return;
      view.callouts.push({ drug: level.boosters.drug, label: level.boosters.label, born: view.clock, fromButton: true });
      announce(`You took ${level.boosters.drug}.`);
    },
    injection: () => {
      if (!Physics.giveInjection(state, level)) return;
      injectParticles();
      announce("Injection given.");
    },
    test: () => {
      if (!Physics.takeBloodTest(state)) return;
      view.lastReading = { level: state.tanks[0].level, time: state.time };
      announce(`Blood test: ${describeReading(state.tanks[0].level)}.`);
    },
  };

  function useSpecial(id) {
    if (view.phase === "done") return;
    begin();
    SPECIAL_ACTIONS[id]();
    refreshHits();
  }

  function describeReading(amount) {
    const spec = level.tanks[0];
    if (amount > spec.band[1]) return "above the green band";
    if (amount < spec.band[0]) return "below the green band";
    return "inside the green band";
  }

  /* ---------- level flow ---------- */

  function loadLevel(index) {
    levelIndex = index;
    level = LEVELS[index];
    world = WORLDS[level.world];
    state = Physics.createState(level);
    view = newView();
    ui.title.textContent = level.title;
    ui.result.hidden = true;
    showGame();
    buildHits();
    refreshHits();
    updateScore();
    reconcileCopies(true);
    resetTips();
    snapshotState();
  }

  function finish() {
    view.phase = "done";
    refreshHits();
    const survived = state.outcome === "done";
    const percent = Physics.score(state, level);
    const stars = survived ? starCount(percent) : 0;
    best[levelIndex] = Math.max(best[levelIndex] ?? 0, stars);
    saveBest();
    host.onFinish?.({ level: levelIndex, stars: best[levelIndex], learned: survived ? level.learned : null });
    showResult(survived, percent, stars);
    if (!survived) {
      view.shake = calmMotion ? 0 : 14;
      view.flash = 1;
    }
  }

  function starCount(percent) {
    if (percent >= 0.88) return 3;
    if (percent >= 0.75) return 2;
    if (percent >= 0.55) return 1;
    return 0;
  }

  function starsMarkup(count) {
    return [0, 1, 2].map((i) => `<span class="${i < count ? "star on" : "star"}">${ICONS[i < count ? "star-fill" : "star"]}</span>`).join("");
  }

  function showResult(survived, percent, stars) {
    const titles = ["You made it, barely", "Good", "Steady hands", "Perfect rhythm"];
    const rounded = Math.round(percent * 100);
    ui.resultTitle.textContent = survived ? titles[stars] : "Overdose";
    ui.resultStars.innerHTML = starsMarkup(stars);
    ui.resultStars.setAttribute("aria-label", `${stars} of 3 stars`);
    ui.resultMeter.hidden = !survived;
    ui.resultMeter.setAttribute("aria-label", `In the green ${rounded}% of the time`);
    ui.resultFill.style.width = `${rounded}%`;
    ui.resultValue.textContent = `${rounded}%`;
    if (survived) ui.resultReveal.innerHTML = `You just learned about <strong>${level.learned}</strong>. ${level.reveal}`;
    else ui.resultReveal.textContent = `The ${plainLabel(level.tanks[state.overdosedTank ?? 0].label)} medicine passed the orange line at ${Math.round(state.time)} seconds.`;
    const isLast = levelIndex === LEVELS.length - 1;
    ui.next.querySelector(".label").textContent = isLast ? "Back to level 1" : "Next level";
    hideTip();
    ui.result.hidden = false;
    ui.next.focus({ preventScroll: true });
  }

  function updateScore() {
    ui.score.textContent = `${Math.round(Physics.score(state, level) * 100)}% in the green`;
  }

  function announce(message) {
    ui.announcer.textContent = message;
  }

  /* ---------- tips ---------- */

  const TIP_TRIGGERS = {
    start: () => true,
    time: (seconds) => view.phase === "running" && state.time >= Number(seconds),
    nearTop: () => state.tanks.some((tank, index) => tank.level > level.tanks[index].band[1] - 0.03),
    event: () => [...view.seenEvents].some((event) => !event.booster),
  };

  function resetTips() {
    view.tips = { shown: new Set(), current: null, shownAt: 0 };
    hideTip();
  }

  function tipIsDue(tip) {
    const [kind, value] = tip.when.split(":");
    return TIP_TRIGGERS[kind](value);
  }

  function tipIsOver(tip) {
    if (tip.until === "pill") return state.tanks.some((tank) => tank.lastPill > -Infinity);
    return view.clock - view.tips.shownAt > 3.2;
  }

  function tipAnchor(anchor) {
    const g = geometry();
    const [kind, index] = anchor.split(":");
    const tank = g.tanks[Number(index ?? 0)];
    const anchors = {
      tank: () => ({ x: tankCenter(tank), y: tank.top + 44, below: true }),
      liver: () => ({ x: 200, y: g.liverTop - 4, below: false }),
      gate: () => ({ x: 200, y: g.gateTop - 2, below: false }),
      tokens: () => {
        const tray = trayRect();
        return { x: tray.x + tray.width / 2, y: tray.y + tray.height + 8, below: true };
      },
    };
    return anchors[kind]();
  }

  function showTip(tip) {
    view.tips.current = tip;
    view.tips.shownAt = view.clock;
    view.tips.shown.add(tip);
    const anchor = tipAnchor(tip.anchor);
    ui.tip.textContent = tip.text;
    ui.tip.classList.toggle("tip--below", anchor.below);
    const scale = canvas.clientWidth / BOARD_W;
    const half = ui.tip.offsetWidth / 2 / scale;
    const x = Math.min(BOARD_W - half - 8, Math.max(half + 8, anchor.x));
    ui.tip.style.setProperty("--caret", `calc(50% + ${(anchor.x - x) * scale}px)`);
    ui.tip.style.left = `${(x / BOARD_W) * 100}%`;
    ui.tip.style.top = `${(anchor.y / BOARD_H) * 100}%`;
    ui.tip.dataset.visible = "true";
    if (tip.until === "pill") hits.tanks[0]?.classList.add("hit--nudge");
    announce(tip.text);
  }

  function hideTip() {
    ui.tip.dataset.visible = "false";
    if (view?.tips) view.tips.current = null;
    for (const button of hits.tanks) button?.classList.remove("hit--nudge");
  }

  function updateTips() {
    if (view.phase === "done") return;
    const current = view.tips.current;
    if (current) {
      if (tipIsOver(current)) hideTip();
      return;
    }
    const next = (level.tips ?? []).find((tip) => !view.tips.shown.has(tip) && tipIsDue(tip));
    if (next) showTip(next);
  }

  /* ---------- levels view ---------- */

  function showGame() {
    ui.game.hidden = false;
    ui.levels.hidden = true;
    ui.showLevels.setAttribute("aria-pressed", "false");
  }

  function showLevels() {
    renderLevelList();
    ui.game.hidden = true;
    ui.levels.hidden = false;
    ui.showLevels.setAttribute("aria-pressed", "true");
    ui.levelList.querySelector("button")?.focus({ preventScroll: true });
  }

  function renderLevelList() {
    ui.levelList.innerHTML = WORLDS.map((worldInfo, worldIndex) => {
      const buttons = LEVELS.map((entry, index) => ({ entry, index }))
        .filter(({ entry }) => entry.world === worldIndex)
        .map(({ entry, index }) => levelButton(entry, index))
        .join("");
      return `<li class="world">
        <img class="world-art" src="${SPRITES[worldInfo.enzyme]}" alt="${worldInfo.enzymeName} enzyme" width="56" height="56">
        <div class="world-body">
          <h2 class="world-name">${worldInfo.name}</h2>
          <p class="world-enzyme">${worldInfo.enzymeName}</p>
          <div class="world-levels">${buttons}</div>
        </div>
      </li>`;
    }).join("");
  }

  function levelButton(entry, index) {
    const stars = best[index] ?? 0;
    const current = index === levelIndex ? " current" : "";
    return `<button type="button" class="button button--stack level-button${current}" data-level="${index}" aria-label="${entry.title}, ${stars} of 3 stars">
      <span class="level-title">${entry.title}</span>
      <span class="level-stars" aria-hidden="true">${starsMarkup(stars)}</span>
    </button>`;
  }

  /* ---------- simulation-driven view state ---------- */

  function reconcileCopies(instant) {
    const target = Math.max(0, Math.min(MAX_COPIES, Math.round(state.enzyme * BASE_COPIES)));
    const alive = view.copies.filter((copy) => copy.dying === null);
    if (alive.length < target) addCopies(target - alive.length, instant);
    if (alive.length > target) retireCopies(alive, alive.length - target);
    view.copies = view.copies.filter((copy) => copy.dying === null || view.clock - copy.dying < 1.4);
  }

  function addCopies(count, instant) {
    const used = new Set(view.copies.filter((copy) => copy.dying === null).map((copy) => copy.slot));
    const free = slotOrder.filter((slot) => !used.has(slot));
    for (const slot of free.slice(0, count)) {
      view.copies.push({ slot, born: instant ? -10 : view.clock, dying: null, pulse: 0 });
    }
  }

  function retireCopies(alive, count) {
    const bySlot = [...alive].sort((a, b) => slotOrder.indexOf(b.slot) - slotOrder.indexOf(a.slot));
    for (const copy of bySlot.slice(0, count)) copy.dying = view.clock;
  }

  function jammingDrug() {
    const blocking = Physics.activeEvents(state).find((event) => (event.block ?? 0) > 0);
    if (blocking) return blocking.drug;
    const competitor = level.tanks.findIndex((spec, index) => spec.compete && state.tanks[index].level > 0.05);
    return competitor >= 0 ? level.tanks[competitor].medicine : null;
  }

  function trackArrivals() {
    for (const event of Physics.activeEvents(state)) {
      if (view.seenEvents.has(event)) continue;
      view.seenEvents.add(event);
      if (event.booster) continue;
      view.callouts.push({ drug: event.drug, label: event.label, born: view.clock, fromButton: false });
      announce(`Your patient started ${plainLabel(event.label ?? event.drug)}.`);
    }
  }

  function trackPills(g) {
    level.tanks.forEach((spec, index) => {
      const tank = g.tanks[index];
      for (const pill of state.tanks[index].pills) {
        if (!view.pillX.has(pill)) view.pillX.set(pill, tankCenter(tank) + (Math.random() - 0.5) * (tank.right - tank.left) * 0.45);
        const landing = Physics.landingTime(spec);
        if (g.gated && pill.age >= landing * 0.45 && !view.bitten.has(pill)) biteAtGate(pill, g);
        if (pill.age >= landing && !view.landed.has(pill)) landPill(pill, index, tank);
      }
    });
  }

  function biteAtGate(pill, g) {
    view.bitten.add(pill);
    const x = view.pillX.get(pill);
    for (const target of gateCopyPositions(g)) {
      view.particles.push({ kind: "crumb", x, y: (g.gateTop + g.gateBottom) / 2, tx: target.x, ty: target.y, born: view.clock, life: 0.45 });
    }
  }

  function landPill(pill, index, tank) {
    view.landed.add(pill);
    view.wobble[index] = Math.min(2, view.wobble[index] + 1);
    if (!Physics.isRevealed(state, level)) return;
    const x = view.pillX.get(pill);
    const y = levelToY(state.tanks[index].level, tank);
    for (let i = 0; i < 9; i += 1) {
      view.particles.push({ kind: "splash", x, y, vx: (Math.random() - 0.5) * 170, vy: -110 - Math.random() * 140, born: view.clock, life: 0.55 });
    }
  }

  function injectParticles() {
    const tank = geometry().tanks[0];
    for (let i = 0; i < 14; i += 1) {
      const x = tankCenter(tank) + (Math.random() - 0.5) * 40;
      view.particles.push({ kind: "splash", x, y: tank.top - 10, vx: (Math.random() - 0.5) * 30, vy: 180 + Math.random() * 120, born: view.clock + i * 0.02, life: 0.5 });
    }
  }

  function emitDrain(dt, g) {
    const alive = view.copies.filter((copy) => copy.dying === null);
    if (!alive.length) return;
    level.tanks.forEach((spec, index) => {
      const flow = spec.drain * Physics.capacity(state) * state.tanks[index].level;
      if (Math.random() > flow * dt * 45) return;
      const target = alive[Math.floor(Math.random() * alive.length)];
      const to = slotPosition(target.slot, g);
      view.particles.push({ kind: "drop", x: tankCenter(g.tanks[index]), y: g.liverTop - 4, tx: to.x, ty: to.y, born: view.clock, life: 0.7, target });
    });
  }

  function ageParticles(dt) {
    for (const particle of view.particles) {
      if (particle.kind !== "splash") continue;
      particle.vy += 650 * dt;
      particle.x += particle.vx * dt;
      particle.y += particle.vy * dt;
    }
    for (const particle of view.particles) {
      if (particle.kind === "drop" && view.clock - particle.born >= particle.life) particle.target.pulse = 1;
    }
    view.particles = view.particles.filter((particle) => view.clock - particle.born < particle.life);
  }

  function update(dt) {
    view.clock += dt;
    view.wobble = view.wobble.map((value) => value * Math.exp(-dt * 2.2));
    view.shake *= Math.exp(-dt * 8);
    view.flash *= Math.exp(-dt * 2.5);
    for (const copy of view.copies) copy.pulse *= Math.exp(-dt * 6);
    ageParticles(dt);
    updateTips();
    if (view.phase !== "running") return;
    const g = geometry();
    Physics.step(state, level, dt);
    trackArrivals();
    trackPills(g);
    reconcileCopies(false);
    emitDrain(dt, g);
    updateScore();
    refreshHits();
    if (state.outcome) finish();
  }

  /* ---------- drawing ---------- */

  function drawBackground() {
    context.fillStyle = PAPER.ground;
    context.fillRect(0, 0, BOARD_W, BOARD_H);
    context.drawImage(grain, 0, 0, BOARD_W, BOARD_H);
  }

  function drawTissue(top, bottom) {
    context.fillStyle = PAPER.tissue;
    context.beginPath();
    context.moveTo(0, bottom);
    context.lineTo(0, top + 6);
    for (let x = 0; x <= BOARD_W; x += 10) context.lineTo(x, top + Math.sin(x * 0.05) * 4);
    context.lineTo(BOARD_W, bottom);
    context.closePath();
    context.fill();
  }

  function surfaceY(x, index, tank) {
    const base = levelToY(state.tanks[index].level, tank);
    const amplitude = (calmMotion ? 0.3 : 1) * (0.8 + view.wobble[index] * 4);
    const t = view.clock;
    return base + Math.sin(x * 0.045 + t * 3.1 + index) * amplitude + Math.sin(x * 0.11 - t * 2.2) * amplitude * 0.5;
  }

  function traceSurface(index, tank, continuePath) {
    for (let x = tank.left; x <= tank.right; x += 4) {
      const y = surfaceY(x, index, tank);
      if (x === tank.left && !continuePath) context.moveTo(x, y);
      else context.lineTo(x, y);
    }
  }

  function drawBand(spec, tank) {
    const top = levelToY(spec.band[1], tank);
    const bottom = levelToY(spec.band[0], tank);
    context.save();
    context.globalAlpha = 0.14;
    context.fillStyle = PAPER.band;
    context.fillRect(tank.left, top, tank.right - tank.left, bottom - top);
    context.globalAlpha = 1;
    context.strokeStyle = PAPER.band;
    context.lineWidth = 2;
    context.setLineDash([6, 6]);
    for (const y of [top, bottom]) {
      context.beginPath();
      context.moveTo(tank.left, y);
      context.lineTo(tank.right, y);
      context.stroke();
    }
    context.restore();
  }

  function drawWater(spec, index, tank) {
    const amount = state.tanks[index].level;
    if (amount <= 0.003) return;
    context.save();
    context.beginPath();
    context.moveTo(tank.left, tank.bottom);
    traceSurface(index, tank, true);
    context.lineTo(tank.right, tank.bottom);
    context.closePath();
    context.fillStyle = PAPER.water;
    context.globalAlpha = 0.9;
    context.fill();
    context.clip();
    context.globalAlpha = 1;
    drawDissolvedMolecules(spec, amount, tank);
    context.restore();
    context.save();
    context.strokeStyle = PAPER.waterLine;
    context.lineWidth = 2.5;
    context.beginPath();
    traceSurface(index, tank);
    context.stroke();
    context.restore();
  }

  function drawDissolvedMolecules(spec, amount, tank) {
    const image = medicineImage(spec.medicine);
    const width = tank.right - tank.left;
    const available = Math.round(view.molecules.length * Math.min(1, width / 192));
    const shown = Math.round((amount / Physics.OVERDOSE) * available);
    const depth = tank.bottom - levelToY(amount, tank);
    for (const molecule of view.molecules.slice(0, shown)) {
      const bob = calmMotion ? 0 : Math.sin(view.clock * 0.9 + molecule.phase) * 3;
      const x = tank.left + molecule.x * width;
      const y = tank.bottom - molecule.depth * depth + bob;
      drawSprite(image, x, y, 20, molecule.tilt + (calmMotion ? 0 : view.clock * 0.15), 0.9);
    }
  }

  function drawFrost(tank) {
    context.save();
    context.fillStyle = PAPER.frost;
    context.fillRect(tank.left, tank.top, tank.right - tank.left, tank.bottom - tank.top);
    context.globalAlpha = 0.5;
    context.drawImage(grain, tank.left * 2, tank.top * 2, (tank.right - tank.left) * 2, (tank.bottom - tank.top) * 2, tank.left, tank.top, tank.right - tank.left, tank.bottom - tank.top);
    context.restore();
  }

  function drawLastReading(tank) {
    if (!view.lastReading) return;
    const y = levelToY(view.lastReading.level, tank);
    const ago = Math.round(state.time - view.lastReading.time);
    context.save();
    context.strokeStyle = PAPER.ink;
    context.lineWidth = 2;
    context.setLineDash([3, 4]);
    context.beginPath();
    context.moveTo(tank.left, y);
    context.lineTo(tank.right, y);
    context.stroke();
    context.fillStyle = PAPER.ink;
    context.font = '600 13px "Atkinson Hyperlegible Next", system-ui, sans-serif';
    context.textAlign = "left";
    context.fillText(`${ago}s ago`, tank.right + 6, y + 4);
    context.restore();
  }

  function drawTestTimer(tank) {
    const remaining = state.revealUntil - state.time;
    if (!level.blind || remaining <= 0 || state.outcome) return;
    const fraction = remaining / Physics.TEST_DURATION;
    context.save();
    context.strokeStyle = PAPER.ink;
    context.lineWidth = 3;
    context.beginPath();
    context.arc(tank.right - 18, tank.top + 18, 10, -Math.PI / 2, -Math.PI / 2 + fraction * Math.PI * 2);
    context.stroke();
    context.restore();
  }

  function drawSprite(image, x, y, height, rotation, alpha) {
    if (!image?.complete || !image.naturalHeight) return;
    const width = height * (image.naturalWidth / image.naturalHeight);
    context.save();
    context.globalAlpha = alpha;
    context.translate(x, y);
    context.rotate(rotation);
    context.drawImage(image, -width / 2, -height / 2, width, height);
    context.restore();
  }

  function drawGraduations(tank) {
    context.strokeStyle = PAPER.inkSoft;
    context.lineWidth = 1.5;
    for (let mark = 1; mark <= 9; mark += 1) {
      const y = levelToY(mark / 10, tank);
      context.beginPath();
      context.moveTo(tank.left, y);
      context.lineTo(tank.left + (mark === 5 ? 14 : 8), y);
      context.stroke();
    }
  }

  function drawOverdoseLine(spec, index, tank) {
    const y = levelToY(Physics.OVERDOSE, tank);
    const visible = Physics.isRevealed(state, level);
    const amount = visible ? state.tanks[index].level : 0;
    const closeness = Math.max(0, (amount - spec.band[1]) / (Physics.OVERDOSE - spec.band[1]));
    const pulse = calmMotion ? 1 : 0.65 + 0.35 * Math.sin(view.clock * 11);
    context.save();
    context.strokeStyle = PAPER.danger;
    context.lineWidth = 2.5;
    context.shadowColor = PAPER.danger;
    context.shadowBlur = 4 + 26 * closeness * pulse;
    context.beginPath();
    context.moveTo(tank.left, y);
    context.lineTo(tank.right, y);
    context.stroke();
    context.restore();
  }

  function drawBeaker(tank) {
    context.save();
    context.strokeStyle = PAPER.ink;
    context.lineWidth = 3;
    context.lineJoin = "round";
    context.beginPath();
    context.moveTo(tank.left - 8, tank.top);
    context.lineTo(tank.left, tank.top);
    context.lineTo(tank.left, tank.bottom);
    context.lineTo(tank.right, tank.bottom);
    context.lineTo(tank.right, tank.top);
    context.lineTo(tank.right + 8, tank.top);
    context.stroke();
    context.restore();
  }

  function wrapLabel(text, maxWidth) {
    const lines = [];
    for (const word of text.split(" ")) {
      const last = lines[lines.length - 1];
      if (last && context.measureText(`${last} ${word}`).width <= maxWidth) lines[lines.length - 1] = `${last} ${word}`;
      else lines.push(word);
    }
    return lines;
  }

  function drawTankLabel(spec, index, tank) {
    const paused = state.tanks[index].paused;
    context.save();
    context.fillStyle = paused ? PAPER.inkSoft : PAPER.ink;
    context.font = `600 ${level.tanks.length > 2 ? 12 : 14}px "Atkinson Hyperlegible Next", system-ui, sans-serif`;
    context.textAlign = "center";
    const lines = wrapLabel(spec.label, tank.right - tank.left + 16);
    lines.forEach((line, lineIndex) => {
      context.fillText(line, tankCenter(tank), tank.top - 12 - (lines.length - 1 - lineIndex) * 14);
    });
    context.restore();
  }

  function drawPauseBadge(spec, index, tank) {
    if (!spec.auto) return;
    const paused = state.tanks[index].paused;
    const x = tankCenter(tank);
    const y = tank.top + 22;
    context.save();
    if (paused) {
      context.globalAlpha = 0.5;
      context.fillStyle = PAPER.ground;
      context.fillRect(tank.left, tank.top, tank.right - tank.left, tank.bottom - tank.top);
      context.globalAlpha = 1;
    }
    context.fillStyle = paused ? PAPER.ink : "#FFFFFF";
    context.beginPath();
    context.arc(x, y, 13, 0, Math.PI * 2);
    context.fill();
    context.fillStyle = paused ? "#FFFFFF" : PAPER.ink;
    if (paused) {
      context.beginPath();
      context.moveTo(x - 4, y - 6);
      context.lineTo(x + 6, y);
      context.lineTo(x - 4, y + 6);
      context.closePath();
      context.fill();
    } else {
      context.fillRect(x - 5, y - 6, 3.5, 12);
      context.fillRect(x + 1.5, y - 6, 3.5, 12);
    }
    context.restore();
  }

  function drawPipe(tank, g) {
    const x = tankCenter(tank);
    context.save();
    context.fillStyle = PAPER.water;
    context.fillRect(x - 6, tank.bottom, 12, g.liverTop - tank.bottom + 2);
    context.strokeStyle = PAPER.ink;
    context.lineWidth = 3;
    context.beginPath();
    context.moveTo(x - 6, tank.bottom);
    context.lineTo(x - 6, g.liverTop + 2);
    context.moveTo(x + 6, tank.bottom);
    context.lineTo(x + 6, g.liverTop + 2);
    context.stroke();
    context.restore();
  }

  function drawTank(spec, index, tank, g) {
    drawPipe(tank, g);
    if (Physics.isRevealed(state, level)) drawWater(spec, index, tank);
    else drawFrost(tank);
    drawBand(spec, tank);
    if (!Physics.isRevealed(state, level)) drawLastReading(tank);
    drawGraduations(tank);
    drawOverdoseLine(spec, index, tank);
    drawPauseBadge(spec, index, tank);
    drawBeaker(tank);
    drawTankLabel(spec, index, tank);
    drawTestTimer(tank);
  }

  function copyScale(copy) {
    if (calmMotion) return 1;
    const age = view.clock - copy.born;
    const pop = age < 0.5 ? 1 + Math.sin(Math.min(1, age / 0.5) * Math.PI) * 0.25 - (1 - Math.min(1, age / 0.25)) : 1;
    return Math.max(0, pop) * (1 + copy.pulse * 0.08);
  }

  function drawCopy(copy, position, jammedBy) {
    const bob = calmMotion ? 0 : Math.sin(view.clock * 1.3 + copy.slot) * 1.5;
    if (copy.dying !== null) {
      const fade = Math.min(1, (view.clock - copy.dying) / 1.4);
      drawSprite(images[`${world.enzyme}_dead`], position.x, position.y + fade * 16, COPY_SIZE, 0, 1 - fade);
      return;
    }
    drawSprite(images[world.enzyme], position.x, position.y + bob, COPY_SIZE * copyScale(copy), 0, 1);
    if (jammedBy) drawSprite(images[jammedBy], position.x, position.y + bob, 17, 0.4, 1);
  }

  function drawLiver(g) {
    drawTissue(g.liverTop, g.liverBottom + 12);
    const drug = jammingDrug();
    const alive = view.copies.filter((copy) => copy.dying === null).sort((a, b) => slotOrder.indexOf(a.slot) - slotOrder.indexOf(b.slot));
    const jammedCount = drug ? Math.round(state.block * alive.length) : 0;
    const jammed = new Set(alive.slice(0, jammedCount));
    for (const copy of view.copies) drawCopy(copy, slotPosition(copy.slot, g), jammed.has(copy) ? drug : null);
  }

  function drawGate(g) {
    if (!g.gated) return;
    context.fillStyle = PAPER.tissue;
    context.fillRect(0, g.gateTop, BOARD_W, g.gateBottom - g.gateTop);
    const drug = jammingDrug();
    for (const position of gateCopyPositions(g)) {
      drawSprite(images[world.enzyme], position.x, position.y, 40, 0, Math.min(1, 0.35 + Physics.capacity(state) * 0.65));
      if (drug && state.block > 0.3) drawSprite(images[drug], position.x, position.y, 15, 0.4, 1);
    }
  }

  const iconPathCache = {};
  function iconPaths(name) {
    iconPathCache[name] ??= [...ICONS[name].matchAll(/ d="([^"]+)"/g)].map((match) => new Path2D(match[1]));
    return iconPathCache[name];
  }

  function drawIcon(name, x, y, size, color, alpha) {
    context.save();
    context.globalAlpha = alpha;
    context.translate(x - size / 2, y - size / 2);
    context.scale(size / 256, size / 256);
    context.fillStyle = color;
    for (const path of iconPaths(name)) context.fill(path);
    context.restore();
  }

  const TOKEN_ART = {
    booster: (x, y, alpha) => drawCapsule(x, y, 0.8, alpha, "#EFC94C"),
    injection: (x, y, alpha) => drawIcon("syringe", x, y, 24, PAPER.ink, alpha),
    test: (x, y, alpha) => drawIcon("drop", x, y, 24, "#B8483E", alpha),
  };

  function drawTray() {
    const special = activeSpecial();
    if (!special) return;
    const rect = trayRect();
    const left = special.left(state);
    context.save();
    context.fillStyle = "rgba(255, 255, 255, 0.85)";
    context.beginPath();
    context.roundRect(rect.x, rect.y, rect.width, rect.height, rect.height / 2);
    context.fill();
    context.restore();
    for (let i = 0; i < special.total(level); i += 1) {
      TOKEN_ART[special.id](rect.x + 26 + i * TOKEN_GAP, rect.y + rect.height / 2, i < left ? 1 : 0.2);
    }
  }

  function drawCapsule(x, y, scale, alpha, cap = PAPER.capsule) {
    context.save();
    context.globalAlpha = alpha;
    context.translate(x, y);
    context.scale(scale, scale);
    context.rotate(-0.35);
    context.lineWidth = 2.5;
    context.strokeStyle = PAPER.ink;
    context.fillStyle = PAPER.capsuleCap;
    context.beginPath();
    context.roundRect(-14, -6.5, 28, 13, 6.5);
    context.fill();
    context.fillStyle = cap;
    context.beginPath();
    context.roundRect(0, -6.5, 14, 13, [0, 6.5, 6.5, 0]);
    context.fill();
    context.beginPath();
    context.roundRect(-14, -6.5, 28, 13, 6.5);
    context.stroke();
    context.restore();
  }

  function drawPills(g) {
    const revealed = Physics.isRevealed(state, level);
    level.tanks.forEach((spec, index) => {
      const tank = g.tanks[index];
      const landing = Physics.landingTime(spec);
      const surface = revealed ? levelToY(state.tanks[index].level, tank) : tank.top + 24;
      const scale = level.tanks.length > 2 ? 0.75 : 1;
      for (const pill of state.tanks[index].pills) {
        const x = view.pillX.get(pill) ?? tankCenter(tank);
        const bite = view.bitten.has(pill) ? 0.55 + 0.45 * Physics.throughGate(state, spec, pill.variance) : 1;
        if (pill.age < landing) {
          const progress = pill.age / landing;
          drawCapsule(x, 12 + (surface - 12) * progress * progress, scale * bite, 1);
        } else if (revealed) {
          const dissolved = 1 - pill.remaining / spec.dose;
          drawCapsule(x, surface + 10 + dissolved * 22, scale * bite, Math.max(0, 1 - dissolved));
        }
      }
    });
  }

  function drawParticles() {
    for (const particle of view.particles) {
      const age = (view.clock - particle.born) / particle.life;
      if (age < 0) continue;
      context.save();
      if (particle.kind === "splash") {
        context.globalAlpha = 1 - age;
        context.fillStyle = PAPER.waterLine;
        context.beginPath();
        context.arc(particle.x, particle.y, 2.4, 0, Math.PI * 2);
        context.fill();
      } else {
        const x = particle.x + (particle.tx - particle.x) * age;
        const y = particle.y + (particle.ty - particle.y) * age - Math.sin(age * Math.PI) * 18;
        context.globalAlpha = particle.kind === "crumb" ? 1 - age * 0.6 : 1;
        context.fillStyle = particle.kind === "crumb" ? PAPER.capsule : PAPER.waterLine;
        context.beginPath();
        context.arc(x, y, particle.kind === "crumb" ? 3 : 2.6, 0, Math.PI * 2);
        context.fill();
      }
      context.restore();
    }
  }

  function drawCallouts(g) {
    const anchorY = g.tanks[0].top + 70;
    for (const callout of view.callouts) {
      const age = view.clock - callout.born;
      if (age > 3) continue;
      const settle = Math.min(1, age / 0.35);
      const leave = Math.max(0, (age - 2.3) / 0.7);
      const startX = callout.fromButton ? 350 : 52;
      const x = startX + (200 - startX) * leave;
      const y = anchorY + (g.liverTop + 40 - anchorY) * leave * leave;
      const alpha = settle * (1 - leave * 0.8);
      drawSprite(images[callout.drug], x, y, 58 * (1 - leave * 0.6), 0.3, alpha);
      context.save();
      context.globalAlpha = alpha * (1 - leave);
      context.fillStyle = PAPER.ink;
      context.font = '600 15px "Atkinson Hyperlegible Next", system-ui, sans-serif';
      context.textAlign = "center";
      context.fillText(callout.label ?? callout.drug, x, y + 46);
      context.restore();
    }
  }

  function drawTimer() {
    const progress = Math.min(1, state.time / level.duration);
    context.fillStyle = "rgba(26, 33, 36, 0.12)";
    context.fillRect(24, 552, BOARD_W - 48, 4);
    context.fillStyle = PAPER.ink;
    context.fillRect(24, 552, (BOARD_W - 48) * progress, 4);
  }

  function drawFlash() {
    if (view.flash < 0.02) return;
    context.save();
    context.globalAlpha = view.flash * 0.22;
    context.fillStyle = PAPER.danger;
    context.fillRect(0, 0, BOARD_W, BOARD_H);
    context.restore();
  }

  function draw() {
    const g = geometry();
    context.save();
    context.clearRect(0, 0, BOARD_W, BOARD_H);
    if (view.shake > 0.3) context.translate((Math.random() - 0.5) * view.shake, (Math.random() - 0.5) * view.shake);
    drawBackground();
    drawGate(g);
    level.tanks.forEach((spec, index) => drawTank(spec, index, g.tanks[index], g));
    drawLiver(g);
    drawPills(g);
    drawParticles();
    drawCallouts(g);
    drawTray();
    drawTimer();
    drawFlash();
    context.restore();
  }

  /* ---------- plumbing ---------- */

  function resize() {
    const ratio = window.devicePixelRatio || 1;
    const cssWidth = canvas.clientWidth;
    canvas.width = Math.round(cssWidth * ratio);
    canvas.height = Math.round(cssWidth * (BOARD_H / BOARD_W) * ratio);
    const scale = (cssWidth / BOARD_W) * ratio;
    context.setTransform(scale, 0, 0, scale, 0, 0);
  }

  let lastFrame = performance.now();
  function frame(now) {
    const dt = Math.min(0.05, (now - lastFrame) / 1000);
    lastFrame = now;
    update(dt);
    draw();
    frameId = requestAnimationFrame(frame);
  }

  function onKey(event) {
    if (!ui.levels.hidden || event.repeat) return;
    if (event.target instanceof HTMLButtonElement && event.target.closest(".result, .hit")) return;
    const tankIndex = level.tanks.findIndex((spec) => spec.key === event.code);
    const special = SPECIALS.find((entry) => entry.key === event.code && entry.has(level));
    if (tankIndex < 0 && !special) return;
    event.preventDefault();
    if (special) useSpecial(special.id);
    else if (level.tanks[tankIndex].auto) togglePause(tankIndex);
    else takePill(tankIndex);
  }

  function snapshotState() {
    host.onLevel?.(levelIndex);
  }

  function bindControls() {
    ui.retry.addEventListener("click", () => loadLevel(levelIndex));
    ui.next.addEventListener("click", () => loadLevel((levelIndex + 1) % LEVELS.length));
    ui.showLevels.addEventListener("click", () => (ui.levels.hidden ? showLevels() : showGame()));
    ui.levelList.addEventListener("click", (event) => {
      const button = event.target.closest("[data-level]");
      if (button) loadLevel(Number(button.dataset.level));
    });
    root.addEventListener("keydown", onKey);
    root.addEventListener("pointerdown", () => root.focus({ preventScroll: true }), true);
  }

  function fillIcons() {
    for (const holder of root.querySelectorAll("[data-icon]")) holder.innerHTML = ICONS[holder.dataset.icon];
  }

  function start(data) {
    fillIcons();
    resize();
    resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(canvas);
    bindControls();
    loadLevel(Math.min(LEVELS.length - 1, Math.max(0, data?.levelIndex ?? 0)));
    frameId = requestAnimationFrame(frame);
  }

  function stop() {
    cancelAnimationFrame(frameId);
    resizeObserver?.disconnect();
  }

  start(host.startData ?? {});
  return stop;
}
