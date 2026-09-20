"""Assembles the playable compound pools for the game at the top of the notebook.

The game sends one real compound through one ward and lets a real measurement
decide every gate it meets. This script is where "real measurement" is turned
into something a game loop can use: for each compound it collects the raw
values, converts each one into a single number between zero and one through a
named transformation, and records the file and row every value came from.

Three rules hold everywhere in here.

A score of zero means the gate stops the compound and a score of one means the
compound passes it without difficulty, for every gate in every ward, including
the safety gates where a high score means the compound leaves the patient's own
medicines alone. One direction throughout means the game can compare gates
without knowing which measurement is behind any of them.

A missing measurement is never filled in. The compound arrives at that gate
marked untested and the game resolves it as a visible gamble, which is what
`GAME.md` asks for and is also the only honest thing to do with an absence.

A value the assay could not pin down keeps its modifier. `<` means the real
value is somewhere below what is written and `>` means it is somewhere above.
A compound sitting at the top of the solubility assay is a different game state
from one measured in the middle of it, and the modifier is how the game knows.

Writes `../data/game.json`, `../data/game_provenance.json`, and one small SVG
per playable compound under `../data/structures/game/`.

Run: python build_game.py
"""

import json
import math
import os
import re
from collections import defaultdict
from datetime import date

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D

from chem import clean_smiles, connectivity_block, parent_identity
from sources import CONTEXT_SOURCES, SOURCES

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
STRUCTURES = os.path.join(DATA, "structures", "game")
GAME_PATH = os.path.join(DATA, "game.json")
PROVENANCE_PATH = os.path.join(DATA, "game_provenance.json")
CARD_SIZE = (220, 170)

LIBRARY_POOL_SIZE = 260
SAFETY_POOL_SIZE = 240

ALL_SOURCES = {**SOURCES, **CONTEXT_SOURCES}
ENZYMES = ["CYP1A2", "CYP2C9", "CYP2D6", "CYP3A4"]

# The four medicines the patient is already taking, one per enzyme in the CYP
# release. Each is a drug FDA's own interaction table calls a sensitive
# substrate of that enzyme, which is to say a drug whose blood level moves a
# long way when the enzyme is blocked. Each also has a structure in drugs.csv,
# so the game can draw it on the bedside table.
PATIENT_MEDICINES = [
    ("caffeine", "CYP1A2"),
    ("celecoxib", "CYP2C9"),
    ("desipramine", "CYP2D6"),
    ("midazolam", "CYP3A4"),
]

# Compounds in the antiviral release that a reader may already know by name.
# Confirmed against PubChem in the research notes and re-checked below by
# recomputing the InChIKey from the released structure.
ASAP_LANDMARKS = {"ASAP-0000370": ("nirmatrelvir", "LIENCHBZNNMNKG-OJFNHCPVSA-N")}


# --------------------------------------------------------------------------
# Turning a measurement into a score


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def rising_log(low: float, high: float):
    """Zero at or below `low`, one at or above `high`, straight in between on a
    log scale. For measurements that span orders of magnitude and where more is
    better, such as solubility and permeability."""
    span = math.log10(high) - math.log10(low)

    def score(value: float) -> float:
        if value <= 0:
            return 0.0
        return clamp01((math.log10(value) - math.log10(low)) / span)

    return score


def falling_log(low: float, high: float):
    """One at or below `low`, zero at or above `high`. More is worse."""
    rising = rising_log(low, high)
    return lambda value: 1.0 - rising(value)


def rising_linear(low: float, high: float):
    def score(value: float) -> float:
        return clamp01((value - low) / (high - low))

    return score


def falling_linear(low: float, high: float):
    rising = rising_linear(low, high)
    return lambda value: 1.0 - rising(value)


def escape_fraction(blood_flow: float):
    """The share of the compound that would leave the liver unchanged on its
    first pass, if none of it were held by anything in the blood.

    This is the well-stirred liver model, `1 - CL_int / (Q + CL_int)`, with the
    free fraction set to one and the blood-to-plasma ratio set to one. Both are
    assumptions and both are stated here rather than buried. The point of using
    it instead of an arbitrary band is that the ExpansionRx clearance columns
    are already scaled to whole-body millilitres per minute per kilogram, so
    they can be divided by a published blood flow in the same units and the
    answer lands between zero and one on its own."""

    def score(value: float) -> float:
        if value <= 0:
            return 1.0
        return clamp01(blood_flow / (blood_flow + value))

    return score


def window(zero_low: float, peak_low: float, peak_high: float, zero_high: float):
    """One across the middle and falling to zero at both ends, for a quantity
    that is as bad when it is too small as when it is too large."""
    rising = rising_linear(zero_low, peak_low)
    falling = falling_linear(peak_high, zero_high)

    def score(value: float) -> float:
        if value < peak_low:
            return rising(value)
        if value > peak_high:
            return falling(value)
        return 1.0

    return score


# Hepatic blood flow, in millilitres per minute per kilogram of body weight.
# Davies and Morris, Pharmaceutical Research 1993;10:1093-5.
HUMAN_LIVER_BLOOD_FLOW = 20.7
MOUSE_LIVER_BLOOD_FLOW = 90.0

TRANSFORMS = {
    "solubility_band": {
        "function": rising_log(1.0, 200.0),
        "input": "kinetic solubility in micromolar",
        "explanation": (
            "Zero at one micromolar and one at two hundred, straight between them on a "
            "log scale. Below about one micromolar a swallowed dose is limited by how "
            "little of it dissolves; above a hundred or so, solubility stops being what "
            "holds absorption back. Both ends sit inside the range the two releases "
            "actually cover, so no compound is scored outside the measured span."
        ),
    },
    "permeability_band": {
        "function": rising_log(0.1, 10.0),
        "input": "apparent permeability in units of 1e-6 cm/s",
        "explanation": (
            "Zero at 0.1 and one at 10 on a log scale. A compound near the bottom of "
            "this range crosses a cell layer too slowly to be absorbed from the gut in "
            "the time it spends there; one near the top crosses freely."
        ),
    },
    "efflux_band": {
        "function": falling_log(1.0, 20.0),
        "input": "efflux ratio, the rate out over the rate in",
        "explanation": (
            "One at a ratio of one, where the gut wall moves the compound equally in "
            "both directions, falling to zero at twenty, where a pump in the wall is "
            "returning almost everything that gets in."
        ),
    },
    "liver_escape_human": {
        "function": escape_fraction(HUMAN_LIVER_BLOOD_FLOW),
        "input": "human liver microsomal intrinsic clearance in mL/min/kg",
        "explanation": (
            "The well-stirred liver model with the free fraction and the blood-to-plasma "
            "ratio both set to one, against a human liver blood flow of 20.7 mL/min/kg. "
            "The score is the fraction that would survive one pass through the liver. "
            "ExpansionRx publishes this clearance already scaled to the whole body in "
            "the same units as the blood flow, so nothing has to be converted."
        ),
    },
    "liver_escape_mouse": {
        "function": escape_fraction(MOUSE_LIVER_BLOOD_FLOW),
        "input": "mouse liver microsomal intrinsic clearance in mL/min/kg",
        "explanation": (
            "The same model against a mouse liver blood flow of 90 mL/min/kg. A mouse "
            "liver is far faster than a human one relative to body weight, which is why "
            "the same compound scores differently here."
        ),
    },
    "microsome_band": {
        "function": falling_log(3.0, 300.0),
        "input": "liver microsomal clearance, units not stated by the source",
        "explanation": (
            "One at three and zero at three hundred, on a log scale. This band is used "
            "for the antiviral release only, because that dataset card does not state "
            "the units of its clearance columns. Without units the well-stirred model "
            "cannot honestly be applied, so the score is a rank inside the range the "
            "file itself covers rather than a physiological fraction."
        ),
    },
    "free_fraction_band": {
        "function": rising_log(0.1, 10.0),
        "input": "percentage of the compound unbound in plasma",
        "explanation": (
            "Zero at a tenth of a percent free and one at ten percent, on a log scale. "
            "Only the unbound part of a drug in the blood can reach anything, so a "
            "compound that is almost entirely stuck to plasma protein needs a far "
            "larger amount in the blood to do the same work."
        ),
    },
    "potency_band": {
        "function": rising_linear(4.0, 8.0),
        "input": "pIC50 against the viral protease",
        "explanation": (
            "Zero at a pIC50 of four and one at eight. Four is where the antiviral "
            "release floors its reported SARS-CoV-2 values, so it is the bottom of what "
            "the assay can distinguish; eight is close to the top of the measured range "
            "and is where the best compounds in the file sit."
        ),
    },
    "enzyme_block_band": {
        "function": falling_linear(4.0, 7.0),
        "input": "pIC50 against one of the patient's liver enzymes",
        "explanation": (
            "One at a pIC50 of four and zero at seven, so a compound that barely touches "
            "the enzyme scores high and one that shuts it down scores zero. Four is the "
            "floor the challenge tutorial gives for reliable quantitation in this assay "
            "and seven is near the top of the measured range."
        ),
    },
    "induction_band": {
        "function": falling_linear(4.0, 7.0),
        "input": "pEC50 for activation of the pregnane X receptor",
        "explanation": (
            "One at a pEC50 of four and zero at seven. Activating this receptor makes "
            "the body build more of the enzyme, so the patient's other medicines drain "
            "away faster instead of backing up. The band matches the enzyme band so the "
            "two kinds of harm are scored on the same footing."
        ),
    },
    "greasiness_window": {
        "function": window(-1.0, 1.0, 3.0, 5.5),
        "input": "LogD at pH 7.4",
        "explanation": (
            "One between one and three, falling to zero at minus one and at 5.5. This "
            "is the only transformation shaped like a window rather than a slope, "
            "because a compound can be too water-loving to cross a membrane and too "
            "fat-loving to dissolve, and the measured releases show both failures."
        ),
    },
}

BAND_EDGES = [0.2, 0.4, 0.6, 0.8]


def band_of(score: float) -> int:
    """A one-to-five bucket, so the game can choose a picture without reading a
    number and so the verification file can report a distribution."""
    return sum(1 for edge in BAND_EDGES if score >= edge) + 1


def score_of(transform: str, value: float) -> float:
    return round(TRANSFORMS[transform]["function"](value), 4)


# --------------------------------------------------------------------------
# Readings and where they came from


class Provenance:
    """One entry per value the game holds, naming the file and the row it sits
    in. Row numbers are zero-based positions in the file as pandas reads it, so
    row zero is the first line after the header."""

    def __init__(self):
        self.entries = []

    def add(self, ward, compound_id, field, source_key, row, column, unit, modifier, value):
        source = ALL_SOURCES[source_key]
        absent = (
            "This compound has no row at all in this file, which is why the gate is untested."
            if row < 0
            else ""
        )
        self.entries.append(
            {
                "absent_from_file": absent,
                "ward": ward,
                "compound_id": compound_id,
                "field": field,
                "value": value,
                "unit": unit,
                "modifier": modifier,
                "source_key": source_key,
                "source_file": source.name,
                "source_repo": source.repo,
                "source_license": source.license,
                "source_url": source.url,
                "pandas_call": source.pandas_call,
                "row": row,
                "column": column,
            }
        )


def is_missing(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def reading(context, field, value, unit, transform, column, modifier="=", note=""):
    """Build one gate entry and record where its value came from.

    `context` carries the ward, the compound identifier, the source key and the
    row, because every reading for one compound shares them.
    """
    provenance, ward, compound_id, source_key, row = context
    if is_missing(value):
        provenance.add(ward, compound_id, field, source_key, row, column, unit, "", None)
        return {
            "status": "untested",
            "unit": unit,
            "transform": transform,
            "score": None,
            "band": None,
        }
    value = float(value)
    score = score_of(transform, value)
    provenance.add(ward, compound_id, field, source_key, row, column, unit, modifier, value)
    return {
        "status": "measured",
        "raw": value,
        "unit": unit,
        "modifier": modifier,
        "censored": modifier in ("<", ">"),
        "transform": transform,
        "score": score,
        "band": band_of(score),
        "note": note,
    }


def flag_reading(context, field, value, column, note=""):
    """A yes or no answer rather than a measurement, such as whether an enzyme
    stays blocked after the compound is washed away."""
    provenance, ward, compound_id, source_key, row = context
    if is_missing(value) or str(value) not in ("True", "False"):
        provenance.add(ward, compound_id, field, source_key, row, column, "flag", "", None)
        return {"status": "untested", "value": None, "note": "Not labelled for this compound."}
    answer = str(value) == "True"
    provenance.add(ward, compound_id, field, source_key, row, column, "flag", "=", answer)
    return {"status": "measured", "value": answer, "note": note}


# --------------------------------------------------------------------------
# Structure drawings


_STYLE = re.compile(r" style='([^']*)'")
_CLASS = re.compile(r" class='[^']*'")
_HEADER = re.compile(r"^.*?<!-- END OF HEADER -->\n", re.DOTALL)


def compact(svg: str, width: int, height: int) -> str:
    """RDKit repeats the same inline style on every bond and every label, which
    makes a card four times larger than it needs to be. The distinct styles are
    lifted into a stylesheet and the drawing classes, which nothing reads, are
    dropped. The picture is unchanged."""
    body = _HEADER.sub("", svg)
    body = _CLASS.sub("", body)
    styles: dict[str, str] = {}
    for declaration in _STYLE.findall(body):
        styles.setdefault(declaration, f"a{len(styles)}")
    for declaration, name in styles.items():
        body = body.replace(f" style='{declaration}'", f" class='{name}'")
    sheet = "".join(f".{name}{{{declaration}}}" for declaration, name in styles.items())
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' "
        f"viewBox='0 0 {width} {height}'><style>{sheet}</style>\n{body}"
    )


def draw(smiles: str) -> str | None:
    """A small 2D depiction for a game card. Coordinates are recomputed rather
    than reused, because a molecule carrying a 3D conformer otherwise draws as
    a flattened projection with atoms on top of each other."""
    mol = Chem.MolFromSmiles(clean_smiles(smiles))
    if mol is None:
        return None
    rdDepictor.Compute2DCoords(mol)
    # The last argument turns off FreeType, so atom labels come out as text
    # elements rather than as one vector path per letter. A card ends up about
    # a third of the size and the browser draws the same picture.
    drawer = rdMolDraw2D.MolDraw2DSVG(CARD_SIZE[0], CARD_SIZE[1], -1, -1, True)
    options = drawer.drawOptions()
    options.clearBackground = False
    options.bondLineWidth = 1
    options.addStereoAnnotation = False
    options.padding = 0.04
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
    drawer.FinishDrawing()
    return compact(drawer.GetDrawingText(), *CARD_SIZE)


def write_card(ward: str, compound_id: str, smiles: str) -> str | None:
    svg = draw(smiles)
    if svg is None:
        return None
    folder = os.path.join(STRUCTURES, ward)
    os.makedirs(folder, exist_ok=True)
    name = compound_id.replace("/", "_") + ".svg"
    with open(os.path.join(folder, name), "w") as handle:
        handle.write(svg)
    return f"structures/game/{ward}/{name}"


# --------------------------------------------------------------------------
# Recognisable drugs


def load_drugs() -> pd.DataFrame:
    return pd.read_csv(os.path.join(DATA, "drugs.csv"))


def drug_lookup(drugs: pd.DataFrame) -> dict:
    """Both the full InChIKey and the connectivity-only first block, so a
    structure that states less stereochemistry than the drug does is still
    recognised, and is marked as the weaker match that it is."""
    by_key = {row.inchikey: (row.drug_id, "full") for row in drugs.itertuples()}
    by_block = {row.inchikey_block: (row.drug_id, "connectivity") for row in drugs.itertuples()}
    return {"full": by_key, "block": by_block}


def recognise(lookup: dict, inchikey: str | None) -> dict | None:
    if not inchikey:
        return None
    if inchikey in lookup["full"]:
        drug_id, match = lookup["full"][inchikey]
        return {"drug_id": drug_id, "match": match}
    block = connectivity_block(inchikey)
    if block in lookup["block"]:
        drug_id, match = lookup["block"][block]
        return {"drug_id": drug_id, "match": match}
    return None


def measured_drug_ids(source_name: str) -> dict:
    """Which compound identifiers in one competition file are drugs the reader
    has heard of, taken from the join the earlier build already verified."""
    measured = pd.read_csv(os.path.join(DATA, "measured.csv"))
    rows = measured[measured.source_file == source_name]
    return {
        str(row.source_id): {"drug_id": row.drug_id, "match": row.match_type}
        for row in rows.itertuples()
    }


# --------------------------------------------------------------------------
# Antiviral ward


def censor_potency(value, floor=None, ceiling=None) -> tuple[str, str]:
    """The antiviral file has no censor column, but it clips: SARS-CoV-2 values
    are floored at exactly 4.0 and eleven MERS values sit at exactly 9.0. A
    value resting on the edge of the reported range is recorded as censored
    rather than as a measurement that happens to be round."""
    if is_missing(value):
        return "=", ""
    if floor is not None and float(value) <= floor:
        return "<", (
            "The file floors this column, so all this row says is that the compound was "
            "no more than barely active."
        )
    if ceiling is not None and float(value) >= ceiling:
        return ">", (
            "The file stops at this value, so the compound is at least this strong and "
            "may be stronger than the assay could read."
        )
    return "=", ""


def antiviral_compound(row, provenance, lookup) -> dict:
    compound_id = row["Molecule Name"]
    smiles = row["CXSMILES_potency"]
    potency = (provenance, "antiviral", compound_id, "asap_potency", int(row["row_potency"]))
    admet_row = row["row_admet"]
    has_admet = not is_missing(admet_row)
    admet = (
        provenance,
        "antiviral",
        compound_id,
        "asap_admet",
        int(admet_row) if has_admet else -1,
    )
    sars_modifier, sars_note = censor_potency(row["pIC50 (SARS-CoV-2 Mpro)"], floor=4.0)
    mers_modifier, mers_note = censor_potency(row["pIC50 (MERS-CoV Mpro)"], ceiling=9.0)
    gates = {
        "reach_target": reading(
            potency,
            "sars_potency",
            row["pIC50 (SARS-CoV-2 Mpro)"],
            "pIC50",
            "potency_band",
            "pIC50 (SARS-CoV-2 Mpro)",
            sars_modifier,
            sars_note,
        ),
        "dissolve": reading(
            admet, "solubility", row.get("KSOL"), "micromolar", "solubility_band", "KSOL"
        ),
        "cross_gut_wall": reading(
            admet,
            "permeability",
            row.get("MDR1-MDCKII"),
            "1e-6 cm/s, unit not stated by the source",
            "permeability_band",
            "MDR1-MDCKII",
        ),
        "survive_liver": reading(
            admet,
            "human_liver_clearance",
            row.get("HLM"),
            "not stated by the source",
            "microsome_band",
            "HLM",
        ),
    }
    extras = {
        "mers_potency": reading(
            potency,
            "mers_potency",
            row["pIC50 (MERS-CoV Mpro)"],
            "pIC50",
            "potency_band",
            "pIC50 (MERS-CoV Mpro)",
            mers_modifier,
            mers_note,
        ),
        "mouse_liver_clearance": reading(
            admet,
            "mouse_liver_clearance",
            row.get("MLM"),
            "not stated by the source",
            "microsome_band",
            "MLM",
        ),
        "greasiness": reading(
            admet, "greasiness", row.get("LogD"), "log10 at pH 7.4", "greasiness_window", "LogD"
        ),
    }
    return assemble(
        "antiviral", compound_id, smiles, gates, extras, lookup, row.get("Set_potency")
    )


def build_antiviral(provenance, lookup) -> dict:
    potency = ALL_SOURCES["asap_potency"].load().reset_index(names="row_potency")
    admet = ALL_SOURCES["asap_admet"].load().reset_index(names="row_admet")
    joined = potency.merge(
        admet, on="Molecule Name", how="left", suffixes=("_potency", "_admet")
    )
    playable = joined[joined.row_admet.notna() | joined["Molecule Name"].isin(ASAP_LANDMARKS)]
    pool = [antiviral_compound(row, provenance, lookup) for _, row in playable.iterrows()]
    for compound in pool:
        landmark = ASAP_LANDMARKS.get(compound["id"])
        if landmark:
            compound["landmark"] = {"name": landmark[0], "expected_inchikey": landmark[1]}
            compound["known_drug"] = {"drug_id": landmark[0], "match": "named in the literature"}
    return {"pool": pool}


# --------------------------------------------------------------------------
# Library ward

LIBRARY_ENDPOINTS = [
    ("solubility", "KSOL", "micromolar", "solubility_band"),
    ("permeability", "Caco-2 Permeability Papp A>B", "1e-6 cm/s", "permeability_band"),
    ("efflux", "Caco-2 Permeability Efflux", "ratio", "efflux_band"),
    ("human_liver_clearance", "HLM CLint", "mL/min/kg", "liver_escape_human"),
    ("mouse_liver_clearance", "MLM CLint", "mL/min/kg", "liver_escape_mouse"),
    ("plasma_free_fraction", "MPPB", "percent unbound", "free_fraction_band"),
    ("brain_free_fraction", "MBPB", "percent unbound", "free_fraction_band"),
    ("muscle_free_fraction", "MGMB", "percent unbound", "free_fraction_band"),
    ("greasiness", "LogD", "log10 at pH 7.4", "greasiness_window"),
]
LIBRARY_GATES = {
    "dissolve": "solubility",
    "cross_gut_wall": "permeability",
    "resist_the_pump": "efflux",
    "survive_liver": "human_liver_clearance",
    "stay_free_in_blood": "plasma_free_fraction",
}
LIBRARY_CORE = ["KSOL", "Caco-2 Permeability Papp A>B", "HLM CLint", "MPPB"]
ZERO_IS_BELOW_DETECTION = {
    "KSOL",
    "Caco-2 Permeability Papp A>B",
    "HLM CLint",
    "MLM CLint",
    "MPPB",
    "MBPB",
    "MGMB",
}


def library_modifier(column: str, value, stated) -> tuple[str, str]:
    """The raw file states its own modifier. The one thing it does not state is
    that a handful of rows carry an exact zero, which no assay can measure. A
    zero is read as a value below the assay's floor and recorded as `<`."""
    stated = "=" if is_missing(stated) else str(stated)
    if column in ZERO_IS_BELOW_DETECTION and not is_missing(value) and float(value) == 0.0:
        return "<", (
            "Reported as exactly zero. No assay measures zero, so this is read as a "
            "value somewhere below what the assay could detect."
        )
    return stated, ""


def library_compound(row, provenance, lookup) -> dict:
    compound_id = row["Molecule Name"]
    context = (provenance, "library", compound_id, "erx_train_raw", int(row["row"]))
    readings = {}
    for field, column, unit, transform in LIBRARY_ENDPOINTS:
        modifier, note = library_modifier(column, row.get(column), row.get(column + " modifier"))
        readings[field] = reading(
            context, field, row.get(column), unit, transform, column, modifier, note
        )
    gates = {gate: readings[field] for gate, field in LIBRARY_GATES.items()}
    extras = {
        field: entry for field, entry in readings.items() if field not in LIBRARY_GATES.values()
    }
    return assemble("library", compound_id, row["SMILES"], gates, extras, lookup, "Train")


def library_candidates(raw: pd.DataFrame) -> pd.DataFrame:
    """Everything with the four endpoints the gauntlet needs, plus every
    censored record, because a value at a ceiling is a real game state and the
    challenge's own ML-ready file is the one that throws those away."""
    columns = [column for _, column, _, _ in LIBRARY_ENDPOINTS]
    modifiers = raw[[column + " modifier" for column in columns]]
    core = raw[LIBRARY_CORE].notna().all(axis=1)
    censored = modifiers.isin(["<", ">"]).any(axis=1)
    present = raw[columns].notna().sum(axis=1)
    candidates = raw[core | censored].copy()
    candidates["endpoints_present"] = present
    candidates["carries_censored"] = censored
    candidates["has_core_four"] = core
    return candidates


def spread_across_logd(frame: pd.DataFrame, limit: int) -> list:
    """Take compounds a few at a time from each tenth of the LogD range, so a
    capped pool does not end up being all one kind of molecule. LogD drives
    solubility, clearance and protein binding at once, so spreading on it
    spreads the gates as well."""
    frame = frame.copy()
    frame["bucket"] = pd.qcut(frame["LogD"].rank(method="first"), 10, labels=False)
    frame["place"] = frame.groupby("bucket").cumcount()
    ordered = frame.sort_values(["place", "bucket", "Molecule Name"])
    return list(ordered.index[:limit])


def library_selection(candidates: pd.DataFrame, limit: int) -> pd.DataFrame:
    """Deterministic, and written out here so the same pool can be rebuilt by
    anyone. Compounds with all nine endpoints come first, then the censored
    records that also carry the four endpoints the gauntlet needs, then a
    spread across LogD, then the remaining censored records. Ties break on the
    compound identifier."""
    candidates = candidates.sort_values("Molecule Name")
    full = candidates[candidates.endpoints_present == len(LIBRARY_ENDPOINTS)]
    chosen = list(full.index)
    rich_censored = candidates[
        candidates.carries_censored
        & candidates.has_core_four
        & ~candidates.index.isin(chosen)
    ]
    chosen += list(rich_censored.index)
    remaining = candidates[~candidates.index.isin(chosen)]
    spread_room = max(0, (limit - len(chosen)) - int(remaining.carries_censored.sum()))
    chosen += spread_across_logd(
        remaining[remaining.has_core_four & ~remaining.carries_censored], spread_room
    )
    chosen += [
        index for index in remaining[remaining.carries_censored].index if index not in chosen
    ]
    return candidates.loc[chosen[:limit]]


def build_library(provenance, lookup) -> dict:
    raw = ALL_SOURCES["erx_train_raw"].load().reset_index(names="row")
    candidates = library_candidates(raw)
    selected = library_selection(candidates, LIBRARY_POOL_SIZE)
    pool = [library_compound(row, provenance, lookup) for _, row in selected.iterrows()]
    return {"pool": pool, "candidates": int(len(candidates))}


# --------------------------------------------------------------------------
# Safety ward


def safety_compound(row, pxr_row, octant_row, provenance, named) -> dict:
    compound_id = row["Molecule_Name"]
    cyp = (provenance, "safety", compound_id, "cyp_inhibition", int(row["row"]))
    tdi = (provenance, "safety", compound_id, "cyp_tdi", int(row["row_tdi"]))
    gates = {}
    for enzyme in ENZYMES:
        column = f"{enzyme}_pIC50_direct_inhibition"
        gates[f"spare_{enzyme.lower()}"] = reading(
            cyp, f"{enzyme}_potency", row.get(column), "pIC50", "enzyme_block_band", column
        )
    extras = {}
    for enzyme in ("CYP2D6", "CYP3A4"):
        extras[f"stays_blocked_{enzyme.lower()}"] = flag_reading(
            tdi,
            f"{enzyme}_is_TDI",
            row.get(f"{enzyme}_is_TDI"),
            f"{enzyme}_is_TDI",
            "True means the enzyme is still blocked after the compound is washed away, "
            "so the patient does not recover between doses.",
        )
    gates["leave_the_dial_alone"] = pxr_reading(pxr_row, provenance, compound_id)
    if octant_row is not None:
        extras["second_platform_cyp3a4"] = octant_reading(octant_row, provenance, compound_id)
    compound = assemble(
        "safety", compound_id, row["SMILES"], gates, extras, None, "Train"
    )
    if compound_id in named:
        compound["known_drug"] = named[compound_id]
    return compound


def pxr_reading(pxr_row, provenance, compound_id) -> dict:
    if pxr_row is None:
        return {
            "status": "untested",
            "unit": "pEC50",
            "transform": "induction_band",
            "score": None,
            "band": None,
            "note": "This compound was never run in the induction assay.",
        }
    context = (provenance, "safety", compound_id, "pxr_train", int(pxr_row["row"]))
    return reading(context, "PXR_pEC50", pxr_row["pEC50"], "pEC50", "induction_band", "pEC50")


def octant_reading(octant_row, provenance, compound_id) -> dict:
    context = (provenance, "safety", compound_id, "octant_inhibition", int(octant_row["row"]))
    entry = reading(
        context,
        "octant_CYP3A4_pIC50",
        octant_row["CYP3A4_pIC50"],
        "pIC50",
        "enzyme_block_band",
        "CYP3A4_pIC50",
        note="A second laboratory's measurement of the same enzyme, on a platform that "
        "pre-incubates the compound with the enzyme before reading.",
    )
    entry["curve_quality"] = str(octant_row["drc_qc_status"])
    entry["plate_quality"] = str(octant_row["plate_qc_status"])
    return entry


def safety_selection(inhibition: pd.DataFrame, in_pxr, named, limit: int) -> pd.DataFrame:
    """Compounds measured against more of the patient's four enzymes come
    first, because they make the ward a decision rather than a coin toss. Every
    recognisable drug is kept whatever its coverage, since the point of the
    ward is that the patient's medicines and the compound under test are the
    same kind of thing."""
    columns = [f"{enzyme}_pIC50_direct_inhibition" for enzyme in ENZYMES]
    counts = inhibition[columns].notna().sum(axis=1)
    frame = inhibition.copy()
    frame["enzymes_measured"] = counts
    frame["has_induction"] = in_pxr
    frame["is_drug"] = frame.Molecule_Name.isin(named)
    frame = frame[(counts >= 2) | frame.is_drug]
    frame = frame.sort_values(
        ["is_drug", "enzymes_measured", "has_induction", "Molecule_Name"],
        ascending=[False, False, False, True],
    )
    return frame.head(limit)


def build_safety(provenance) -> dict:
    inhibition = ALL_SOURCES["cyp_inhibition"].load().reset_index(names="row")
    tdi = ALL_SOURCES["cyp_tdi"].load().reset_index(names="row_tdi")
    pxr = ALL_SOURCES["pxr_train"].load().reset_index(names="row")
    octant = ALL_SOURCES["octant_inhibition"].load().reset_index(names="row")
    named = measured_drug_ids("cyp-challenge-TRAIN_inhibition.csv")

    tdi_columns = ["Molecule_Name", "row_tdi", "CYP2D6_is_TDI", "CYP3A4_is_TDI"]
    inhibition = inhibition.merge(tdi[tdi_columns], on="Molecule_Name", how="left")
    inhibition["smiles_key"] = inhibition.SMILES.str.strip()
    pxr_by_smiles = {
        row.SMILES.strip(): row._asdict() for row in pxr.itertuples() if isinstance(row.SMILES, str)
    }
    octant_by_smiles = {
        row.standardized_smiles.strip(): row._asdict()
        for row in octant.itertuples()
        if isinstance(row.standardized_smiles, str) and not is_missing(row.CYP3A4_pIC50)
    }
    in_pxr = inhibition.smiles_key.isin(pxr_by_smiles)
    selected = safety_selection(inhibition, in_pxr, named, SAFETY_POOL_SIZE)

    pool = []
    for _, row in selected.iterrows():
        key = row["smiles_key"]
        pool.append(
            safety_compound(
                row, pxr_by_smiles.get(key), octant_by_smiles.get(key), provenance, named
            )
        )
    return {"pool": pool, "medicines": build_medicines(provenance)}


def build_medicines(provenance) -> list:
    """The four drugs the patient is already taking. Each is drawn from the
    bundled drug table, and the enzyme it depends on comes from FDA's own
    table of drugs that interact with CYP enzymes."""
    drugs = load_drugs().set_index("drug_id")
    roles = pd.read_csv(os.path.join(DATA, "fda_roles.csv"))
    medicines = []
    for drug_id, enzyme in PATIENT_MEDICINES:
        row = drugs.loc[drug_id]
        # FDA writes the busiest of these enzymes as CYP3A, covering the whole
        # subfamily, while the competition files name the individual enzyme
        # CYP3A4. Both labels are kept so the provenance entry quotes the FDA
        # table exactly as it reads.
        match = roles[
            (roles.drug_id == drug_id)
            & (roles.role == "substrate")
            & roles.enzyme.map(enzyme.startswith)
        ]
        strength = match.strength.iloc[0] if len(match) else "unknown"
        fda_enzyme = match.enzyme.iloc[0] if len(match) else enzyme
        provenance.entries.append(
            {
                "ward": "safety",
                "compound_id": drug_id,
                "field": "depends_on_enzyme",
                "value": fda_enzyme,
                "unit": "FDA classification",
                "modifier": "=",
                "source_key": "fda_roles",
                "source_file": "data/fda_roles.csv",
                "source_repo": "built by build_fda_roles.py from FDA's public-domain table",
                "source_license": "public domain",
                "source_url": (
                    "https://www.fda.gov/drugs/drug-interactions-labeling/"
                    "drug-development-and-drug-interactions-table-substrates-inhibitors-and-inducers"
                ),
                "pandas_call": 'pd.read_csv("data/fda_roles.csv")',
                "row": int(match.index[0]) if len(match) else -1,
                "column": "enzyme",
            }
        )
        medicines.append(
            {
                "drug_id": drug_id,
                "display_name": row["display_name"],
                "enzyme": enzyme,
                "fda_enzyme": fda_enzyme,
                "sensitivity": strength,
                "smiles": row["smiles"],
                "inchikey": row["inchikey"],
                "structure": write_card("medicines", drug_id, row["smiles"]),
                "gate": f"spare_{enzyme.lower()}",
            }
        )
    return medicines


# --------------------------------------------------------------------------
# Shared assembly


def assemble(ward, compound_id, smiles, gates, extras, lookup, split) -> dict:
    canonical, inchikey = parent_identity(smiles)
    measured = [gate["score"] for gate in gates.values() if gate["status"] == "measured"]
    return {
        "id": compound_id,
        "ward": ward,
        "set": None if is_missing(split) else str(split),
        "smiles": clean_smiles(smiles),
        "canonical_smiles": canonical,
        "inchikey": inchikey,
        "structure": write_card(ward, compound_id, smiles),
        "known_drug": recognise(lookup, inchikey) if lookup else None,
        "gates": gates,
        "extras": extras,
        "gates_measured": len(measured),
        "gates_untested": len(gates) - len(measured),
        "weakest_gate_score": min(measured) if measured else None,
        "mean_gate_score": round(sum(measured) / len(measured), 4) if measured else None,
    }


# --------------------------------------------------------------------------
# Player-facing wording. No numbers, no chemistry words, nothing a reader has
# to look up. Each line says what is happening to the compound at that gate.

GATE_TEXT = {
    "dissolve": "The pill has to come apart in the stomach before anything else can happen.",
    "cross_gut_wall": "Whatever dissolved now has to get through the lining of the gut.",
    "resist_the_pump": "The lining pushes some things straight back out again.",
    "survive_liver": "Everything absorbed goes through the liver before it reaches the rest of you.",
    "stay_free_in_blood": "In the blood, some of it drifts free and the rest sticks to passing traffic.",
    "reach_target": "What is left has to hold on to the virus tightly enough to stop it working.",
    "spare_cyp1a2": "The patient's first medicine leaves the body through one particular door.",
    "spare_cyp2c9": "The second medicine leaves through a different door.",
    "spare_cyp2d6": "The third medicine leaves through a third door.",
    "spare_cyp3a4": "The fourth medicine leaves through the busiest door of all.",
    "leave_the_dial_alone": "Some things turn all four doors up, and the patient's medicines drain away.",
}

WARD_TEXT = {
    "antiviral": {
        "title": "The antiviral ward",
        "line": (
            "Every compound here was made to stop one virus, and every one was also put "
            "through the body's own obstacle course. You have to survive the course and "
            "still be strong enough at the end."
        ),
        "source": "ASAP Discovery, through the Polaris and OpenADMET antiviral challenge.",
    },
    "library": {
        "title": "The library ward",
        "line": (
            "Nothing here has a target. Winning is simply getting a useful amount of "
            "the compound into the blood and keeping it there."
        ),
        "source": "ExpansionRx, through the OpenADMET ADMET challenge.",
    },
    "safety": {
        "title": "The safety ward",
        "line": (
            "The patient is already taking four medicines, and each one leaves the body "
            "through a door of its own. Your compound has to get past without standing "
            "in any of those doorways."
        ),
        "source": "The OpenADMET enzyme challenge, the induction challenge, and Octant.",
    },
}

CONVENTION = {
    "score": (
        "Every gate carries a score between zero and one. Zero means the gate stops the "
        "compound and one means it passes without difficulty. The direction is the same "
        "for every gate in every ward, so the game can compare two gates without knowing "
        "which measurement is behind either of them."
    ),
    "band": (
        "The band is the score sorted into five buckets, at a fifth, two fifths, three "
        "fifths and four fifths. The game draws a band, never a score and never a raw "
        "value."
    ),
    "untested": (
        "A compound with no measurement for a gate is marked untested and nothing is "
        "filled in for it. The gate then resolves as a gamble the player can see."
    ),
    "modifier": (
        "A modifier of '<' means the real value lies somewhere below the number written "
        "beside it and '>' means it lies somewhere above. These come from the assay "
        "running out of range, and they are kept because a compound pinned at the top of "
        "an assay is a different thing from one measured in the middle of it."
    ),
    "raw_values": (
        "Every gate keeps the raw value and its unit next to the score, so the notebook "
        "can explain exactly how a gate was decided even though the game never shows a "
        "number."
    ),
}


def transform_documentation() -> dict:
    return {
        key: {"input": entry["input"], "explanation": entry["explanation"]}
        for key, entry in TRANSFORMS.items()
    }


def distribution(pool: list, gate: str) -> dict:
    bands = defaultdict(int)
    untested = 0
    for compound in pool:
        entry = compound["gates"].get(gate)
        if entry is None or entry["status"] != "measured":
            untested += 1
            continue
        bands[entry["band"]] += 1
    return {"bands": {str(k): bands[k] for k in sorted(bands)}, "untested": untested}


def ward_summary(pool: list) -> dict:
    gate_names = sorted({name for compound in pool for name in compound["gates"]})
    full = sum(1 for compound in pool if compound["gates_untested"] == 0)
    return {
        "compounds": len(pool),
        "fully_measured": full,
        "gates": {gate: distribution(pool, gate) for gate in gate_names},
        "recognisable_drugs": sum(1 for compound in pool if compound.get("known_drug")),
    }


def main() -> None:
    os.makedirs(STRUCTURES, exist_ok=True)
    provenance = Provenance()
    lookup = drug_lookup(load_drugs())

    print("antiviral ward", flush=True)
    antiviral = build_antiviral(provenance, lookup)
    print("library ward", flush=True)
    library = build_library(provenance, lookup)
    print("safety ward", flush=True)
    safety = build_safety(provenance)

    game = {
        "built": date.today().isoformat(),
        "convention": CONVENTION,
        "transforms": transform_documentation(),
        "gate_text": GATE_TEXT,
        "wards": {
            "antiviral": {
                **WARD_TEXT["antiviral"],
                "gate_order": [
                    "dissolve",
                    "cross_gut_wall",
                    "survive_liver",
                    "reach_target",
                ],
                "pool": antiviral["pool"],
                "summary": ward_summary(antiviral["pool"]),
            },
            "library": {
                **WARD_TEXT["library"],
                "gate_order": [
                    "dissolve",
                    "cross_gut_wall",
                    "resist_the_pump",
                    "survive_liver",
                    "stay_free_in_blood",
                ],
                "pool": library["pool"],
                "candidates_before_capping": library["candidates"],
                "summary": ward_summary(library["pool"]),
            },
            "safety": {
                **WARD_TEXT["safety"],
                "gate_order": [
                    "spare_cyp1a2",
                    "spare_cyp2c9",
                    "spare_cyp2d6",
                    "spare_cyp3a4",
                    "leave_the_dial_alone",
                ],
                "patient_medicines": safety["medicines"],
                "pool": safety["pool"],
                "summary": ward_summary(safety["pool"]),
            },
        },
    }
    with open(GAME_PATH, "w") as handle:
        json.dump(game, handle, indent=1)

    with open(PROVENANCE_PATH, "w") as handle:
        json.dump(
            {
                "built": date.today().isoformat(),
                "note": (
                    "One entry per value the game holds. `row` is the zero-based position "
                    "in the source file as pandas reads it, so row zero is the first line "
                    "after the header. An entry whose value is null records that the file "
                    "has that column but no value for that compound, which is why the game "
                    "marks the gate untested."
                ),
                "units_caveat": (
                    "The antiviral release does not state the units of its ADMET columns "
                    "anywhere in its dataset card. By convention HLM and MLM are microlitres "
                    "per minute per milligram of microsomal protein, KSOL is micromolar and "
                    "MDR1-MDCKII is apparent permeability in units of 1e-6 centimetres per "
                    "second, but none of that is written down by the source. Every antiviral "
                    "clearance entry below therefore carries the unit 'not stated by the "
                    "source', and its score comes from a band inside the file's own range "
                    "rather than from a physiological model that would need real units."
                ),
                "entries": provenance.entries,
            },
            handle,
            indent=1,
        )

    for ward, content in game["wards"].items():
        summary = content["summary"]
        print(
            f"{ward}: {summary['compounds']} compounds, "
            f"{summary['fully_measured']} with every gate measured, "
            f"{summary['recognisable_drugs']} recognisable drugs"
        )
    print(f"{len(provenance.entries)} provenance entries")


if __name__ == "__main__":
    main()
