# The game

One playable thing at the top of the notebook. A reader should be able to play it
for ten minutes without reading a word of the notebook, and it should look like it
was made by a professional game designer rather than like a chart with buttons.

## The idea

ADMET stands for absorption, distribution, metabolism, excretion and toxicity, which
is the journey a drug takes through a body. So the game is that journey, in side view.
You choose a real compound and send it in. Every gate it meets is decided by a real
measurement from the OpenADMET releases, and the player never reads a number: they
watch the molecule fail to dissolve, get shredded in the liver, or arrive too thin to
do anything.

## Three wards, each honest to one dataset

The releases share almost no molecules with each other, so a single compound cannot
carry both drug-like properties and CYP liabilities. Rather than fudge that, each ward
is backed by one release and says so.

**Antiviral ward, from the ASAP set.** The only release with potency and properties on
the same molecules. Your compound must survive the body and still be potent enough
against the virus protease to stop it.

**Library ward, from ExpansionRx.** Nine measured endpoints and no target. Winning is
getting a useful amount of anything into the blood, which is what the endpoints
actually decide.

**Safety ward, from the CYP challenge, PXR and Octant.** A patient is already taking
four real medicines. Your compound now has to pass through without jamming the enzymes
those medicines leave by. Jamming them is how you lose the patient.

## The gates, and what decides them

| Gate | Decided by | What the player sees |
| --- | --- | --- |
| Dissolve | solubility (KSOL) | grains that stay behind undissolved |
| Cross the gut wall | permeability (MDR1-MDCKII, Caco-2) | molecules bouncing off the wall or slipping through |
| Survive the liver | clearance (HLM CLint) | molecules shredded at the gate, fewer coming out |
| Stay free in blood | plasma protein binding | molecules stuck to large drifting proteins |
| Reach and hold the target | potency (ASAP Mpro pIC50) | the virus slows and stops, or does not |
| Harm the patient | CYP potency and TDI, PXR induction | the patient's own medicines backing up or draining away |

A compound with no measurement for a gate is not guessed at. It arrives at that gate
marked untested, and the gate resolves as a visible gamble, which is the honest thing
and also a good mechanic.

## Play

A run is one compound through one ward, and lasts under a minute. Between runs the
player picks the next compound from a hand of three, each drawn as its real structure.
Ten minutes comes from wanting a better run, not from length.

## Tutorial

Three tips, maximum, in the game's own language, each attached to the moment it
matters rather than shown up front.

## Rules

No numbers on screen during play, no chemistry vocabulary in the interface, and no
mechanic that a measurement does not actually support. Everything drawn from real
rows, with provenance recorded.
