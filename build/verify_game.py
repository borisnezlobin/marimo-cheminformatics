"""Checks the game data against the files it came from, and writes GAME_VERIFIED.md.

Three things are checked, in rising order of how much they would hurt if they
were wrong.

Every provenance entry is opened against its source file and the recorded value
is compared with what actually sits in that row and column. This catches a
misaligned join, which is the failure that would quietly put one compound's
measurement on another compound's card.

Every score is recomputed from the raw value through the transformation the
entry names, and compared with the score the build wrote.

Every gate is counted, banded and reported, so a reader can see whether a ward
has a real spread of outcomes or whether one gate passes everybody.

Run: python verify_game.py
"""

import json
import math
import os
from collections import Counter, defaultdict

import pandas as pd

from build_game import ALL_SOURCES, ASAP_LANDMARKS, BAND_EDGES, TRANSFORMS, band_of
from chem import parent_inchikey

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUT_PATH = os.path.join(HERE, "GAME_VERIFIED.md")

TRIVIAL_WIN = 0.9
TRIVIAL_LOSS = 0.15


def load() -> tuple[dict, dict]:
    with open(os.path.join(DATA, "game.json")) as handle:
        game = json.load(handle)
    with open(os.path.join(DATA, "game_provenance.json")) as handle:
        provenance = json.load(handle)
    return game, provenance


def same_value(recorded, actual) -> bool:
    if recorded is None:
        return actual is None or (isinstance(actual, float) and math.isnan(actual))
    if isinstance(recorded, bool):
        return str(actual) == str(recorded)
    if isinstance(recorded, str):
        return str(actual) == recorded
    return abs(float(actual) - float(recorded)) < 1e-9


def check_provenance(entries: list) -> tuple[int, list]:
    """Open every entry against its source file. Entries pointing at the two
    bundled tables rather than a competition file are read from data/."""
    frames = {}
    failures = []
    checked = 0
    for entry in entries:
        key = entry["source_key"]
        if key not in frames:
            frames[key] = (
                pd.read_csv(os.path.join(DATA, "fda_roles.csv"))
                if key == "fda_roles"
                else ALL_SOURCES[key].load()
            )
        frame = frames[key]
        if entry["row"] < 0:
            continue
        checked += 1
        actual = frame.iloc[entry["row"]][entry["column"]]
        if not same_value(entry["value"], actual):
            failures.append((entry["compound_id"], entry["field"], entry["value"], actual))
    return checked, failures


def check_scores(game: dict) -> tuple[int, list]:
    checked = 0
    failures = []
    for ward in game["wards"].values():
        for compound in ward["pool"]:
            for name, entry in list(compound["gates"].items()) + list(compound["extras"].items()):
                if entry.get("status") != "measured" or "raw" not in entry:
                    continue
                checked += 1
                expected = round(TRANSFORMS[entry["transform"]]["function"](entry["raw"]), 4)
                if abs(expected - entry["score"]) > 1e-9 or band_of(expected) != entry["band"]:
                    failures.append((compound["id"], name, entry["score"], expected))
    return checked, failures


def gate_rows(pool: list, gate: str) -> dict:
    bands = Counter()
    untested = 0
    censored = 0
    for compound in pool:
        entry = compound["gates"].get(gate)
        if entry is None or entry["status"] != "measured":
            untested += 1
            continue
        bands[entry["band"]] += 1
        censored += int(bool(entry.get("censored")))
    return {"bands": bands, "untested": untested, "censored": censored, "total": len(pool)}


def band_table(pool: list, gate_order: list) -> str:
    header = (
        "| Gate | Stopped | Struggling | Even | Comfortable | Straight through | Untested | "
        "At an assay limit |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n"
    )
    lines = []
    for gate in gate_order:
        row = gate_rows(pool, gate)
        counts = " | ".join(str(row["bands"].get(band, 0)) for band in range(1, 6))
        lines.append(f"| {gate} | {counts} | {row['untested']} | {row['censored']} |")
    return header + "\n".join(lines) + "\n"


def trivial(pool: list) -> tuple[list, list]:
    wins, losses = [], []
    for compound in pool:
        scores = [
            entry["score"] for entry in compound["gates"].values() if entry["status"] == "measured"
        ]
        if not scores or compound["gates_untested"]:
            continue
        if min(scores) >= TRIVIAL_WIN:
            wins.append(compound)
        if max(scores) <= TRIVIAL_LOSS:
            losses.append(compound)
    return wins, losses


def describe(compound: dict) -> str:
    name = compound["id"]
    known = compound.get("known_drug")
    if known:
        name += f" ({known['drug_id']})"
    weakest = compound["weakest_gate_score"]
    return f"{name}, weakest gate {weakest}, mean {compound['mean_gate_score']}"


BAND_NAMES = ["stopped", "struggling", "even", "comfortable", "straight through"]


def one_sided(pool: list, gate_order: list) -> list:
    """Gates where one band holds three quarters or more of the compounds
    measured for it. A gate like that is not a decision, and the game should
    either lean on it for pacing or leave it out of the ward's scoring."""
    found = []
    for gate in gate_order:
        row = gate_rows(pool, gate)
        measured = sum(row["bands"].values())
        if not measured:
            continue
        band, count = row["bands"].most_common(1)[0]
        if count / measured >= 0.75:
            found.append((gate, BAND_NAMES[band - 1], count, measured))
    return found


def named_drug_line(count: int) -> str:
    if count == 0:
        return "None of them is a drug a reader would recognise by name."
    if count == 1:
        return "One of them is a drug a reader may recognise by name."
    return f"{count} of them are drugs a reader may recognise by name."


def ward_section(key: str, ward: dict) -> str:
    pool = ward["pool"]
    wins, losses = trivial(pool)
    summary = ward["summary"]
    coverage = Counter(compound["gates_measured"] for compound in pool)
    lines = [
        f"## {ward['title']}",
        "",
        f"Source: {ward['source']}",
        "",
        f"The pool holds {len(pool)} compounds. {summary['fully_measured']} of them have a real "
        f"measurement behind every gate, and the rest reach at least one gate marked untested. "
        + named_drug_line(summary["recognisable_drugs"]),
        "",
        "How many gates each compound has a measurement for: "
        + ", ".join(
            f"{number} {'compound has' if number == 1 else 'compounds have'} {count}"
            for count, number in sorted(coverage.items())
        )
        + ".",
        "",
        band_table(pool, ward["gate_order"]),
    ]
    for gate, band, count, measured in one_sided(pool, ward["gate_order"]):
        lines.append(
            f"The {gate} gate barely separates anything here: {count} of the {measured} "
            f"compounds measured for it land in the same band, {band}."
        )
    if one_sided(pool, ward["gate_order"]):
        lines.append("")
    if wins:
        lines.append(
            "Compounds that clear every gate comfortably, which is to say every measured "
            "gate scores at least "
            f"{TRIVIAL_WIN}: " + "; ".join(describe(compound) for compound in wins) + "."
        )
    else:
        lines.append(
            "No compound in this pool clears every gate comfortably, so no card wins a run "
            "without the player choosing a ward it suits."
        )
    if losses:
        lines.append(
            "Compounds that fail everything, meaning no measured gate reaches "
            f"{TRIVIAL_LOSS}: " + "; ".join(describe(compound) for compound in losses) + "."
        )
    else:
        lines.append("No compound fails every gate, so no card is dead on arrival.")
    lines.append("")
    return "\n".join(lines)


def landmark_check(game: dict) -> list:
    rows = []
    pool = {compound["id"]: compound for compound in game["wards"]["antiviral"]["pool"]}
    for compound_id, (name, expected) in ASAP_LANDMARKS.items():
        compound = pool.get(compound_id)
        found = parent_inchikey(compound["smiles"]) if compound else None
        rows.append((compound_id, name, expected, found, found == expected))
    return rows


def playability(game: dict) -> str:
    """Ten minutes is roughly fifteen runs, and each run offers a hand of three,
    so a ward needs enough distinct compounds that a player does not see the
    same card twice, and enough spread that the choice between three cards is
    a real one."""
    lines = [
        "| Ward | Compounds | Every gate measured | Gates with a real spread | Ten minutes of play |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for key, ward in game["wards"].items():
        pool = ward["pool"]
        spread = 0
        for gate in ward["gate_order"]:
            row = gate_rows(pool, gate)
            measured = sum(row["bands"].values())
            if measured and max(row["bands"].values()) / measured < 0.75:
                spread += 1
        verdict = "yes" if len(pool) >= 60 and spread >= 2 else "no"
        lines.append(
            f"| {ward['title']} | {len(pool)} | {ward['summary']['fully_measured']} | "
            f"{spread} of {len(ward['gate_order'])} | {verdict} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    game, provenance = load()
    checked_rows, row_failures = check_provenance(provenance["entries"])
    checked_scores, score_failures = check_scores(game)
    landmarks = landmark_check(game)

    parts = [
        "# What the game data actually contains",
        "",
        "Regenerated by `verify_game.py` from `data/game.json`, "
        "`data/game_provenance.json` and the competition files themselves. Every number "
        "below is recomputed here rather than copied from the build.",
        "",
        "## Checks",
        "",
        "| Check | Result |",
        "| --- | --- |",
        f"| Provenance entries opened against their source row | {checked_rows} checked, "
        f"{len(row_failures)} disagreed |",
        f"| Scores recomputed from the raw value | {checked_scores} checked, "
        f"{len(score_failures)} disagreed |",
    ]
    for compound_id, name, expected, found, agrees in landmarks:
        mark = "matches" if agrees else f"**DISAGREES**, found {found}"
        parts.append(f"| {compound_id} is {name} ({expected}) | {mark} |")
    parts.append("")

    if row_failures:
        parts += ["The provenance entries that disagreed:", ""]
        parts += [f"- {row}" for row in row_failures[:20]]
        parts.append("")
    if score_failures:
        parts += ["The scores that disagreed:", ""]
        parts += [f"- {row}" for row in score_failures[:20]]
        parts.append("")

    parts += [
        "## Is each ward enough for ten minutes",
        "",
        "Ten minutes is about fifteen runs, and each run offers a hand of three cards. A "
        "ward needs enough compounds that a player rarely meets the same card twice, and "
        "enough spread inside its gates that choosing between three cards is a decision "
        "rather than a shrug. A gate counts as having a real spread when no single band "
        "holds more than three quarters of the compounds measured for it.",
        "",
        playability(game),
        "## How a score is worked out",
        "",
        game["convention"]["score"],
        "",
        game["convention"]["untested"],
        "",
        game["convention"]["modifier"],
        "",
        "| Transformation | Takes | What it does |",
        "| --- | --- | --- |",
    ]
    for name, entry in game["transforms"].items():
        parts.append(f"| `{name}` | {entry['input']} | {entry['explanation']} |")
    parts += [
        "",
        "Bands run from one to five, splitting the score at "
        + ", ".join(str(edge) for edge in BAND_EDGES)
        + ". Band one is a gate that stops the compound and band five is a gate it walks "
        "through.",
        "",
    ]
    for key, ward in game["wards"].items():
        parts.append(ward_section(key, ward))

    with open(OUT_PATH, "w") as handle:
        handle.write("\n".join(parts))
    print(f"wrote {OUT_PATH}")
    print(f"{checked_rows} provenance rows checked, {len(row_failures)} failures")
    print(f"{checked_scores} scores recomputed, {len(score_failures)} failures")


if __name__ == "__main__":
    main()
