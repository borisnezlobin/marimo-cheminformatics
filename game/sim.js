const { Physics, LEVELS } = require('./physics.js');
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const dt = 1 / 60;
const seeds = [...Array(30).keys()];
function pending(s, level, i) { return s.tanks[i].pills.reduce((a, p) => a + p.remaining * Physics.throughGate(s, level.tanks[i], p.variance), 0) + s.tanks[i].injecting; }
function smartBot(th, opts = {}) {
  return (s, level) => {
    level.tanks.forEach((spec, i) => {
      const tank = s.tanks[i];
      if (spec.auto) {
        if (!tank.paused && tank.level > spec.band[1] - (opts.pauseMargin ?? 0.14)) Physics.togglePause(s, i);
        else if (tank.paused && tank.level < spec.band[0] + 0.08) Physics.togglePause(s, i);
        return;
      }
      const inj = level.injections && Physics.throughGate(s, spec) > (opts.injectWhenGate ?? 2) && tank.level + pending(s, level, i) < spec.band[0] + 0.05;
      if (inj) { Physics.giveInjection(s, level); return; }
      if (tank.level + pending(s, level, i) < th) Physics.takePill(s, level, i);
    });
    if (level.boosters && Physics.activeEvents(s).every((e) => !e.booster) && Physics.capacity(s) > (opts.boostAt ?? 0.45)) Physics.takeBooster(s, level);
  };
}
function rhythmBot(period) {
  return (s, level) => level.tanks.forEach((spec, i) => { if (!spec.auto && s.time - s.tanks[i].lastPill >= period) Physics.takePill(s, level, i); });
}
function play(level, seed, bot) {
  const s = Physics.createState(level, rng(seed));
  while (!s.outcome) { bot(s, level); Physics.step(s, level, dt); }
  return s.outcome === 'overdose' ? null : Physics.score(s, level);
}
function summary(r) { const a = r.filter((x) => x !== null); const avg = a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0; return `${r.length - a.length}/${r.length} OD, avg ${(avg * 100).toFixed(0)}%`; }
const only = process.argv[2] ? process.argv[2].split(',').map(Number) : null;
LEVELS.forEach((level, i) => {
  if (only && !only.includes(i + 1)) return;
  let best = null;
  const optionSets = [{}, { injectWhenGate: 0.7 }, { injectWhenGate: 0.85 }, { boostAt: 0.35 }, { pauseMargin: 0.2 }, { pauseMargin: 0.08 }];
  for (const th of [0.4, 0.45, 0.5, 0.55, 0.6]) for (const opts of optionSets) {
    const r = seeds.map((sd) => play(level, sd, smartBot(th, opts)));
    const avg = r.reduce((a, b) => a + (b ?? 0), 0) / r.length;
    if (!best || avg > best.avg) best = { avg, th, opts, r };
  }
  const lines = [`L${i + 1} ${level.title.padEnd(26)} best bot: ${summary(best.r)} th ${best.th} ${JSON.stringify(best.opts)}`];
  for (const p of [1.0, 1.6, 2.2, 3.0]) lines.push(`rhythm ${p}s: ${summary(seeds.map((sd) => play(level, sd, rhythmBot(p))))}`);
  console.log(lines.join('\n     '));
});
