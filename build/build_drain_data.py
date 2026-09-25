"""Trim the OpenADMET releases to the columns the Drain notebook reads.

Writes four small CSVs into ``data/drain/``. Each keeps the release's own
compound identifiers and values, rounded to three decimals, so any row can be
traced back to the original file named in ``sources.py``.
"""

from pathlib import Path

import pandas as pd

from sources import SOURCES

OUT = Path(__file__).resolve().parent.parent / "data" / "drain"
ENZYMES = ["CYP1A2", "CYP2C9", "CYP2D6", "CYP3A4"]


def inhibition():
    frame = SOURCES["cyp_inhibition"].load()
    columns = [f"{enzyme}_pIC50_direct_inhibition" for enzyme in ENZYMES]
    frame = frame[["Molecule_Name", "SMILES", *columns]]
    return frame.rename(columns={f"{enzyme}_pIC50_direct_inhibition": enzyme for enzyme in ENZYMES})


def time_dependent():
    frame = SOURCES["cyp_tdi"].load()
    keep = {"Molecule_Name": "Molecule_Name"}
    for enzyme in ["CYP2D6", "CYP3A4"]:
        keep[f"{enzyme}_is_TDI"] = f"{enzyme}_is_TDI"
        keep[f"{enzyme}_pIC50_TDI_condition"] = f"{enzyme}_TDI"
        keep[f"{enzyme}_pIC50_direct_inhibition"] = f"{enzyme}_direct"
    return frame[list(keep)].rename(columns=keep)


def screen():
    frame = SOURCES["cyp_single"].load()
    wide = frame.pivot_table(index=["Molecule_Name", "SMILES"], columns="enzyme", values=["log2fc_estimate", "log2fc_fdr"])
    wide.columns = [f"{enzyme}_{'log2fc' if value == 'log2fc_estimate' else 'fdr'}" for value, enzyme in wide.columns]
    return wide.reset_index()


def pxr():
    frame = SOURCES["pxr_train"].load()
    return frame[["Molecule Name", "OCNT_ID", "pEC50"]].rename(columns={"Molecule Name": "Molecule_Name"})


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, build in [("inhibition", inhibition), ("tdi", time_dependent), ("screen", screen), ("pxr", pxr)]:
        table = build().round(3)
        table.to_csv(OUT / f"{name}.csv", index=False)
        print(f"{name}: {len(table)} rows, {(OUT / f'{name}.csv').stat().st_size // 1024} KB")
