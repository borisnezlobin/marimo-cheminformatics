# Game copy

Every string the player can see. Use these verbatim rather than writing new ones. If
a string is needed that is not here, ask for it rather than inventing it, because the
writing rules are strict and easy to break by accident.

The rules these follow: every sentence has a subject and a verb, nothing is a fragment
for effect, nothing evokes in place of explaining, no label names a thing the player
is already looking at, and no chemistry vocabulary appears anywhere in the interface.

## Opening

Title: **Send it through**

Standfirst: Send a compound through a body and see how much of it survives the trip.

Start button: Start

## The three wards

**Stop the virus**
A virus is multiplying in this body. Get enough of your compound through to stop it.

**Reach the blood**
There is no target this time. Getting a useful amount of anything into the blood is
the whole job.

**Do not hurt the patient**
This patient already takes four other medicines. Get through without blocking the
route those medicines use to leave.

## Compound cards

Instruction above the hand: Pick one and send it in.

Each card carries one sentence, built from that compound's best and worst gate. Use
the clause for the best gate, then "but", then the clause for the worst.

| Gate | Doing well | Doing badly |
| --- | --- | --- |
| dissolve | Dissolves easily | Barely dissolves, so most of it never gets going |
| gut | Crosses the gut wall without trouble | Struggles to cross the gut wall |
| liver | Slips past the liver mostly intact | The liver destroys most of it on the way through |
| binding | Stays free once it reaches the blood | Sticks to proteins in the blood, so little of it is free to work |
| target | Hits the virus hard when it arrives | Barely troubles the virus, even when it arrives |

Joined, a card reads: *Dissolves easily, but the liver destroys most of it on the way
through.*

When a gate has never been measured, add a second sentence naming it: *Nobody has
measured how well it crosses the gut wall, so that part is a gamble.*

## What happens at each gate

These appear as the molecules reach each station, once per run at most.

- dissolve: Most of it never dissolved.
- gut: Most of it could not get through the gut wall.
- liver: The liver destroyed most of what arrived.
- binding: Proteins in the blood are holding most of it.
- target: Not enough arrived to slow the virus.

When a gate goes well: Almost all of it got through.

## The three tips

Each appears once, at the moment it first matters, and never again.

1. The liver destroys most of what passes through it, so a compound that survives it
   beats a stronger one that does not.
2. Proteins in the blood hold on to some of the drug, and only the free part can do
   anything.
3. Blocking the liver makes the patient's own medicines pile up, and clearing the
   virus does not count if you harm them.

## Results

Won: Enough of it arrived, and the virus stopped.

Lost, nothing arrived: Nothing reached the virus this time.

Lost, too little: Some of it arrived, but not enough to stop the virus.

Lost, patient harmed: You stopped the virus and left the patient with too much of
their own medicine in the blood.

Library ward won: A useful amount reached the blood.

Library ward lost: Almost nothing reached the blood.

## Running score

Label: Best run so far
Second label: Runs played

## After a run

Button: Send another
Button, after three runs in a ward: Try the next ward

## Where the numbers come from

One line under the game, for the reader who wants to know: Every gate in this game is
decided by a real measurement from OpenADMET's data, and the section below shows which
one.

---

# Additions

## Choosing the virus, in the first ward

Prompt: Choose which virus you are treating.

The two options: **SARS-CoV-2, the virus behind covid** and **MERS, a related virus**.

Under them: The same compound is not equally good against both.

## The third ward, framed

The first two wards asked whether your compound arrives. This one asks whether it
hurts anyone on the way.

## Clauses for the safety ward doors

The patient's four medicines each leave the body through a door of their own, so name
the medicine rather than the enzyme.

| Doing well | Doing badly |
| --- | --- |
| Leaves the door that clears caffeine alone | Blocks the door that clears caffeine |

Use the same pair for celecoxib, desipramine and midazolam.

For the dial that changes how fast the whole liver runs:

| Doing well | Doing badly |
| --- | --- |
| Leaves the liver running at its normal speed | Speeds the whole liver up, so the patient's medicines drain away |

## When a part has never been measured

One sentence, naming the part:

- Nobody has measured whether it dissolves, so that part is a gamble.
- Nobody has measured how well it crosses the gut wall, so that part is a gamble.
- Nobody has measured whether the pump throws it back out, so that part is a gamble.
- Nobody has measured how well it survives the liver, so that part is a gamble.
- Nobody has measured how much of it stays free in the blood, so that part is a gamble.
- Nobody has measured what it does to the virus, so that part is a gamble.
- Nobody has measured what it does to the door that clears caffeine, so that part is a gamble.
- Nobody has measured whether it speeds the liver up, so that part is a gamble.

## Results in the third ward

Won: You got through and left the patient's own medicines where they were.

Lost, one medicine: The patient is left with too much celecoxib in their blood.

Lost, more than one: The patient is left with too much of their own medicine in their
blood.

Lost, drained: The patient's own medicines drained away faster than they should have.

## The four vials

All four medicines stay on screen for every run, including the ones this compound has
never been tested against. A vial nobody has measured is drawn as unknown rather than
as safe, and reads: Nobody has tested this compound against the door that clears
midazolam.
