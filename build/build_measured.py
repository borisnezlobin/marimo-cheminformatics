"""Write notebook/data/measured.csv and measured_full_provenance.json.

The competition files ship no drug names. They ship structures, so the only way
to find a known drug in them is to reduce both sides to the same identifier and
look. That is what this script does: every structure in every potency-bearing
file is stripped to its parent and turned into a standard InChIKey, and any key
that also appears in drugs.csv produces a measurement row.

Two kinds of match come out, and the notebook has to show them differently. A
full-key match agrees on stereochemistry and is the one to trust. A
connectivity-block match agrees only on which atom is bonded to which, so it can
join two stereoisomers that behave nothing alike, which is exactly what quinine
and quinidine do at 362-fold apart. Full matches are taken first; a connectivity
match is only recorded where no full match exists, and it is labelled.

Run: python build_measured.py
Reads the competition files from the Hugging Face URLs in sources.py, or from a
local directory if OPENADMET_DATA is set.
"""

import json
import os
from collections import defaultdict

import pandas as pd

from chem import connectivity_block, parent_inchikey, stereo_relationship
from sources import SOURCES

HERE = os.path.dirname(os.path.abspath(__file__))
DRUGS_PATH = os.path.join(HERE, "..", "data", "drugs.csv")
MEASURED_PATH = os.path.join(HERE, "..", "data", "measured.csv")
PROVENANCE_PATH = os.path.join(HERE, "..", "data", "measured_full_provenance.json")

ENZYMES = ["CYP1A2", "CYP2C9", "CYP2D6", "CYP3A4"]
REFERENCE_SMILES: dict[str, str] = {}
COLUMNS = [
    "drug_id", "inchikey", "inchikey_block", "match_type",
    "source_file", "source_id", "enzyme", "endpoint", "value", "stereo_note",
]


def wide_columns(template: str, endpoint: str) -> list[tuple[str, str, str]]:
    """(column, enzyme, endpoint) for a file with one column per enzyme."""
    return [(template.format(enzyme=e), e, endpoint) for e in ENZYMES]


# How each file is read: the columns that carry a value, and what that value is.
LAYOUTS = {
    "cyp_inhibition": {
        "kind": "wide",
        "columns": wide_columns("{enzyme}_pIC50_direct_inhibition", "pIC50_direct"),
    },
    "cyp_tdi": {
        "kind": "wide",
        "columns": (
            wide_columns("{enzyme}_pIC50_TDI_condition", "pIC50_TDI_condition")
            + [("CYP2D6_is_TDI", "CYP2D6", "is_TDI"), ("CYP3A4_is_TDI", "CYP3A4", "is_TDI")]
        ),
    },
    "cyp_single": {
        "kind": "long",
        "enzyme_column": "enzyme",
        "value_column": "log2fc_estimate",
        "endpoint": "screen_log2fc",
    },
    "octant_inhibition": {
        "kind": "wide",
        "columns": [("CYP3A4_pIC50", "CYP3A4", "pIC50_direct")],
    },
    "pxr_train": {
        "kind": "wide",
        "columns": [("pEC50", "PXR", "pEC50_PXR")],
    },
    "pxr_counter": {
        "kind": "wide",
        "columns": [("pEC50", "PXR", "pEC50_PXR_counter")],
    },
}


def load_drug_keys() -> tuple[dict[str, str], dict[str, list[str]]]:
    drugs = pd.read_csv(DRUGS_PATH)
    by_key = dict(zip(drugs.inchikey, drugs.drug_id))
    REFERENCE_SMILES.update(zip(drugs.drug_id, drugs.smiles))
    by_block: dict[str, list[str]] = defaultdict(list)
    for block, drug in zip(drugs.inchikey_block, drugs.drug_id):
        by_block[block].append(drug)
    return by_key, dict(by_block)


def key_column(frame: pd.DataFrame, smiles_column: str) -> pd.Series:
    unique = frame[smiles_column].dropna().astype(str).unique()
    mapping = {smiles: parent_inchikey(smiles) for smiles in unique}
    return frame[smiles_column].astype(str).map(mapping)


def matches_for(inchikey, by_key, by_block) -> list[tuple[str, str]]:
    """[(drug_id, match_type)] for one structure. Full-key matches win outright."""
    if not isinstance(inchikey, str):
        return []
    if inchikey in by_key:
        return [(by_key[inchikey], "full")]
    block = connectivity_block(inchikey)
    return [(drug, "connectivity") for drug in by_block.get(block, [])]


def coerce(value):
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "false"):
            return 1.0 if lowered == "true" else 0.0
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(number) else number


def value_cells(layout: dict, row: pd.Series):
    """[(enzyme, endpoint, raw value)] for one row of one file."""
    if layout["kind"] == "long":
        return [(row.get(layout["enzyme_column"]), layout["endpoint"],
                 row.get(layout["value_column"]))]
    return [
        (enzyme, endpoint, row.get(column))
        for column, enzyme, endpoint in layout["columns"]
        if column in row.index
    ]


def harvest(source, layout, by_key, by_block) -> tuple[list[dict], list[dict]]:
    frame = source.load()
    frame["_key"] = key_column(frame, source.smiles_column)
    unparseable = int(frame["_key"].isna().sum())
    print(f"  {source.name}: {len(frame)} rows, "
          f"{frame['_key'].nunique()} parent structures, {unparseable} unparseable")

    rows, provenance = [], []
    matched = frame[frame["_key"].isin(set(by_key) | {
        k for k in frame["_key"].dropna().unique()
        if connectivity_block(k) in by_block
    })]
    for position, row in matched.iterrows():
        pairs = matches_for(row["_key"], by_key, by_block)
        if not pairs:
            continue
        for enzyme, endpoint, raw in value_cells(layout, row):
            number = coerce(raw)
            if number is None or not isinstance(enzyme, str):
                continue
            for drug, match_type in pairs:
                record = {
                    "drug_id": drug,
                    "inchikey": row["_key"],
                    "inchikey_block": connectivity_block(row["_key"]),
                    "match_type": match_type,
                    "source_file": source.name,
                    "source_id": str(row.get(source.id_column, "")),
                    "enzyme": enzyme,
                    "endpoint": endpoint,
                    "value": number,
                    "stereo_note": "" if match_type == "full" else stereo_relationship(
                        str(row[source.smiles_column]), REFERENCE_SMILES[drug]),
                }
                rows.append(record)
                provenance.append({
                    **record,
                    "source_repo": source.repo,
                    "source_url": source.url,
                    "row_index": int(position),
                    "smiles_as_published": str(row[source.smiles_column]),
                })
    return rows, provenance


def main() -> None:
    by_key, by_block = load_drug_keys()
    print(f"drugs.csv: {len(by_key)} parent keys, {len(by_block)} connectivity blocks")

    all_rows, all_provenance = [], []
    for key, layout in LAYOUTS.items():
        source = SOURCES[key]
        rows, provenance = harvest(source, layout, by_key, by_block)
        print(f"    -> {len(rows)} measurements on {len({r['drug_id'] for r in rows})} drugs")
        all_rows.extend(rows)
        all_provenance.extend(provenance)

    frame = pd.DataFrame(all_rows, columns=COLUMNS)
    frame = frame.sort_values(["drug_id", "source_file", "enzyme", "endpoint"])
    frame.to_csv(MEASURED_PATH, index=False)
    with open(PROVENANCE_PATH, "w") as handle:
        json.dump({
            "description": (
                "One entry per row of measured.csv, naming the file and the row it came "
                "from so any value can be traced back to the published data."
            ),
            "sources": {
                k: {"repo": s.repo, "file": s.name, "url": s.url,
                    "license": s.license, "pandas": s.pandas_call}
                for k, s in SOURCES.items()
            },
            "rows": all_provenance,
        }, handle, indent=1)

    connectivity = frame[frame.match_type == "connectivity"]
    print(f"\nmeasured.csv: {len(frame)} measurements on {frame.drug_id.nunique()} drugs")
    print(f"  connectivity-only matches: {len(connectivity)} rows, "
          f"{connectivity.drug_id.nunique()} drugs")
    print(frame.groupby(["endpoint", "enzyme"]).size().to_string())


if __name__ == "__main__":
    main()
