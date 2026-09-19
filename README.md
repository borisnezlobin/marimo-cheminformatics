# Does the plate predict the clinic?

An interactive marimo notebook built for the molab Notebook Competition #3, run by
marimo with OpenADMET.

A laboratory can measure how strongly a drug blocks a liver enzyme, cheaply and at
scale. What anyone actually wants to know is how much a drug builds up inside a
person, which needs a clinical study and exists for only a few hundred drugs. This
notebook asks whether the cheap measurement predicts the expensive one, using the
competition's own data.

For CYP2D6 it does. Five drugs carry both a potency measured in OpenADMET's files and
a published human exposure increase against the same victim drug, and a line fitted to
four of them predicts the fifth to within 1.15-fold.

For CYP3A4 it does not. Voriconazole, which FDA classifies as a strong blocker on the
strength of human studies, reads as the weakest fitted value in the file, while
isavuconazole, which FDA calls moderate, reads as the strongest. Only four drugs have
both a published class and a measured potency on that enzyme, which is too thin to
call a success rate in either direction, and that sparsity is itself the finding.

## Running it

```sh
uv run --with marimo marimo edit plate_or_clinic.py
```

The script header pins every dependency, so `uv` will build the environment on first
run. Nothing is downloaded at runtime: the notebook reads the small derived tables in
`data/`, which the scripts in `build/` produce from the competition releases.

## What is in here

| Path | What it holds |
| --- | --- |
| `plate_or_clinic.py` | The notebook |
| `theme.css` | Type and table styling, defined once |
| `widgets/` | Four hand-written anywidget components |
| `data/` | Derived tables the notebook reads, plus pre-rendered molecule drawings |
| `build/` | Re-runnable scripts that produce everything in `data/` |
| `build/VERIFIED.md` | Every headline number, recomputed from source, with its file named |

### The widgets

`Gate` animates the mechanism. Molecules flow out through a liver enzyme, and raising
the blockade fills the enzyme's slots with a second drug so traffic queues and the
level in the bloodstream rises past a fixed reference line.

`Cabinet` takes medicines by name, brand names included, and shows which pairs meet at
an enzyme. Every drug lands in one of three evidence states, told apart by icon shape,
fill and wording rather than by colour alone.

`Guess` gives you a plate reading and asks you to predict what it does inside a person,
then reveals the published figure. The line you compete against is refitted without the
drug it is predicting.

`StereoEditor` draws a molecule with rdkit-js and lets you flip its stereocentres.
Turning quinine into quinidine takes two flips and moves the measured potency 362-fold.

Each widget keeps its own visual state in JavaScript, so all four stay alive in a
static export with no Python kernel behind the page.

## Where the numbers come from

Potencies come from the OpenADMET CYP challenge training files, induction values from
the PXR challenge, and clearance from the ExpansionRx release. Clinical exposure
increases are quoted from FDA labels retrieved through openFDA. Enzyme roles and
strength bands come from FDA's public-domain table of drugs that interact with CYP
enzymes. `data/sources.json` records each source with its licence and the exact call
that loads it.

The competition datasets ship no drug names, so names were recovered by matching
structures: salts stripped to the parent, stereochemistry preserved, and every match
recorded in `data/measured_full_provenance.json` with the file and row it came from.
The quinine section of the notebook exists because that decision changes answers.

No model is fitted anywhere except the straight line the guessing game competes
against, which is refitted without whichever drug it is predicting. Everything else
shown is a measurement, or arithmetic on measurements.

## What this notebook does not do

It reports a documented mechanism and FDA's published exposure band. It does not
predict anybody's blood concentration, because the quantities that would be needed,
principally how much of a drug circulates unbound and how much of its clearance runs
through the blocked enzyme, are not publicly available for most drugs. Interactions
that travel by any route other than these enzymes are invisible to it. Warfarin taken
with ibuprofen shows nothing here and is genuinely dangerous.

None of this is medical advice.

## Disclosure

Written with AI assistance. Claude helped with the code and the drafting. Every number
was recomputed from the source files and checked against the cited labels, and
`build/VERIFIED.md` records those checks including the places where an early figure
turned out to be wrong.
