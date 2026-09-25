const { Physics, LEVELS } = require('./physics.js');
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function run(level, useInjections, th) {
  let total = 0, od = 0;
  const spacing = level.duration / ((level.injections?.count ?? 0) + 1);
  for (let seed = 0; seed < 40; seed++) {
    const s = Physics.createState(level, rng(seed));
    let nextShot = spacing * 0.5;
    while (!s.outcome) {
      const t = s.tanks[0], spec = level.tanks[0];
      const pending = t.pills.reduce((a, p) => a + p.remaining * Physics.throughGate(s, spec, 1), 0) + t.injecting;
      if (t.level + pending < th) {
        if (useInjections && s.injectionsLeft > 0 && t.level + pending > spec.band[0] - 0.12) Physics.giveInjection(s, level);
        else Physics.takePill(s, level);
      }
      Physics.step(s, level, 1 / 60);
    }
    if (s.outcome === 'overdose') od++; else total += Physics.score(s, level);
  }
  return { od, avg: total / 40 };
}
function best(level, use) {
  return [0.4, 0.45, 0.5, 0.55].map((th) => run(level, use, th)).sort((a, b) => b.avg - a.avg)[0];
}
const base = LEVELS[3];
for (const [gate, variance, dose, count, amount] of [[0.85, 0.6, 2.0, 6, 0.2], [0.85, 0.6, 2.0, 8, 0.18], [0.85, 0.7, 2.0, 8, 0.18], [0.8, 0.7, 1.5, 8, 0.18], [0.85, 0.7, 2.0, 10, 0.16]]) {
  const level = JSON.parse(JSON.stringify(base));
  Object.assign(level.tanks[0], { gate, gateVariance: variance, dose });
  level.injections = { count, amount };
  const a = best(level, false), b = best(level, true);
  console.log(`gate ${gate} variance ${variance} dose ${dose} shots ${count}x${amount}: pills only ${(a.avg * 100).toFixed(0)}% (${a.od}/40 OD) | with shots ${(b.avg * 100).toFixed(0)}% (${b.od}/40 OD)`);
}
