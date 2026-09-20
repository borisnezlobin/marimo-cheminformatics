# Game interfaces

Three pieces are being built in parallel. These shapes are fixed so they meet.

## 1. `data/game.json`, as actually built

The data build produced a richer schema than this file first specified, and the richer
one is what everything conforms to. Shape:

```
{
  "built": "...", "convention": "...",
  "transforms": { "<name>": "how a raw value becomes a 0..1 score" },
  "gate_text":  { "<gate id>": "one plain sentence about that station" },
  "wards": {
    "antiviral" | "library" | "safety": {
      "title": "...", "line": "...", "source": "which release backs this ward",
      "gate_order": ["dissolve", "cross_gut_wall", ...],
      "patient_medicines": [ ... ],        // safety ward only
      "pool": [ { compound }, ... ],
      "summary": { "compounds": n, "fully_measured": n, ... }
    }
  }
}
```

A compound carries `id`, `ward`, `set`, `inchikey`, `smiles`, `canonical_smiles`,
`structure` (a path to its card SVG), `known_drug` (null, or `{drug_id, match}`),
`landmark`, `gates_measured`, `gates_untested`, `mean_gate_score`,
`weakest_gate_score`, `extras`, and `gates`.

Each entry in `gates` is:

```
{ "status": "measured" | "untested", "raw": 8.68, "unit": "pIC50",
  "modifier": "=" | "<" | ">", "censored": false, "transform": "potency_band",
  "score": 0.0-1.0 or null, "band": 1-5 or null, "note": "" }
```

`score` and `band` run in one direction everywhere: high means the gate lets the
compound through, including the safety gates, where high means it leaves the patient's
medicines alone. `status` of `untested` means no measurement exists and the engine
resolves that gate as a visible gamble.

### The gates that exist

| Gate id | What it is |
| --- | --- |
| `cross_gut_wall` | Whatever dissolved now has to get through the lining of the gut. |
| `dissolve` | The pill has to come apart in the stomach before anything else can happen. |
| `leave_the_dial_alone` | Some things turn all four doors up, and the patient's medicines drain away. |
| `reach_target` | What is left has to hold on to the virus tightly enough to stop it working. |
| `resist_the_pump` | The lining pushes some things straight back out again. |
| `spare_cyp1a2` | The patient's first medicine leaves the body through one particular door. |
| `spare_cyp2c9` | The second medicine leaves through a different door. |
| `spare_cyp2d6` | The third medicine leaves through a third door. |
| `spare_cyp3a4` | The fourth medicine leaves through the busiest door of all. |
| `stay_free_in_blood` | In the blood, some of it drifts free and the rest sticks to passing traffic. |
| `survive_liver` | Everything absorbed goes through the liver before it reaches the rest of you. |

The antiviral ward runs dissolve, gut wall, liver, target. The library ward runs
dissolve, gut wall, the efflux pump, liver, staying free in the blood. The safety ward
runs one gate per enzyme plus the induction dial, and its `patient_medicines` are four
real drugs (caffeine, celecoxib, desipramine, midazolam), each tied to the gate its own
clearance depends on.

## 2. `widgets/game_art.js`, written by the art task, read by the engine

Exports one factory:

```js
export function makeRenderer(canvas, theme) {
  return {
    resize(width, height),
    render(state, dtSeconds),   // draws one frame, owns all pixels
    hitTest(x, y),              // returns a string id or null, for clickable scene parts
    destroy(),
  };
}
```

The renderer owns `canvas.width` and `canvas.height`; the engine must not size the
canvas itself. Coordinates in `state` are normalised, with named positions published by
the renderer as `SCENE.landmarks`. A molecule's `size` is a multiplier near 1, not a
fraction of the canvas. The stylesheet export the widget needs is `game_stylesheet`;
using any other export renders the scene flat black with no error.

`state` is a plain object the engine owns and the renderer only reads:

```js
{
  ward: "antiviral",
  phase: "choosing" | "running" | "resolved",
  molecules: [{ x, y, vx, vy, size, status }],   // status: travelling | dissolving | shredded | bounced | bound | arrived
  gates: {
    dissolve: { open: 0..1, jammed: false },
    gut:      { open: 0..1, jammed: false },
    liver:    { open: 0..1, jammed: false, holding: 0..n },
    binding:  { open: 0..1 },
    target:   { health: 0..1 }
  },
  patient: { medicines: [{ name, level: 0..1, danger: 0..1 }] },
  banner: null | { kind: "tip" | "result", text: "..." },
  elapsed: seconds
}
```

The renderer draws the world, the molecules, the gate mechanisms, the proteins and the
target from that state alone. It never computes chemistry and never reads the data file.

## 3. `widgets/game.py`, the engine, class `Gauntlet`

An `anywidget.AnyWidget` following every rule in CONTRACT.md. Traits:

- `game`: Dict, the parsed contents of `data/game.json`, passed in by Python.
- `progress`: Dict, synced back: `{runs, best_score, ward_reached, compounds_played}`.
- `theme`: Unicode.

All game state and logic live in JavaScript, so the game stays playable in a static
export with no kernel. Python supplies the data once and reads progress back.
