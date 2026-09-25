# Drain

An interactive marimo notebook for the molab Notebook Competition #3, run by marimo
with OpenADMET.

Every medicine you swallow has to leave your body again, and most leave through a
handful of liver enzymes. The notebook opens with a game in which you keep a
medicine's level in a safe band while other drugs block, destroy or multiply the
enzymes that clear it. Each of the nine levels teaches one idea, and the sections
below the game show the OpenADMET measurements behind each one.

## Running it

```sh
uv run --with marimo marimo edit drain.py
```

The script header pins every dependency. The notebook reads its tables from
`data/` and the game from `widgets/drain.js`. When those files are missing, for
example when molab opens only the notebook file, it fetches the same files from
this repository on GitHub.

## What is in here

| Path | What it holds |
| --- | --- |
| `drain.py` | The notebook |
| `theme.css` | Type and component styles, defined once |
| `widgets/drain.js` | The game as an anywidget module, built from `game/` |
| `game/` | The game's sources: level physics, rendering, page shell, art, and balance simulations |
| `data/` | Trimmed OpenADMET tables and the named-drug join |
| `build/` | Re-runnable scripts that produce everything in `data/` and `widgets/` |

## The game

`game/physics.js` holds the levels and the simulation. `game/game.js` draws it and
handles input. `game/build.py` combines them with the art in `game/assets.js` into
the widget and a standalone page.

`node game/sim.js` plays every level with a bot that sees the level and with
players who tap at a fixed rhythm, so a change to the physics shows at once whether
a level is still winnable and whether it still punishes a player who ignores the
liver. `node game/gate_sim.js` checks that the injections matter in the first-pass
level.

The enzymes are crystal structures of CYP2D6 (PDB 2F9Q) and CYP3A4 (PDB 1TQN), and
the drugs are RDKit conformers, all drawn with David S. Goodsell's Illustrate.
`game/art/ligands.py` renders the drug sprites.

## AI use

Built with heavy help from Claude, Anthropic's model, running in Claude Code. The
notebook's last section describes how.
