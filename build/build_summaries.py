"""Builds the two small aggregate tables the notebook displays but cannot
recompute from the bundled join table: per-isoform hit rates, and the
ExpansionRx clearance summary. Re-runnable; reads the downloaded competition
files and writes CSVs into ../data/."""

from pathlib import Path

import pandas as pd

SRC = Path(
    "/private/tmp/claude-501/-Users-randomletters-Documents-CurrentProjects-scratch-marimom6"
    "/17ccb2ef-ac21-4611-8718-d63a5adb6998/scratchpad/data"
)
OUT = Path(__file__).resolve().parent.parent / "data"
ENZYMES = ["CYP1A2", "CYP2C9", "CYP2D6", "CYP3A4"]
HIT_LOG2FC = -1.0
HIT_FDR = 0.05
POTENT_PIC50 = 5.0


def fitted_shares() -> pd.DataFrame:
    fitted = pd.read_csv(SRC / "cyp" / "cyp-challenge-TRAIN_inhibition.csv")
    rows = []
    for enzyme in ENZYMES:
        values = fitted[f"{enzyme}_pIC50_direct_inhibition"].dropna()
        rows.append(
            {
                "enzyme": enzyme,
                "fitted_curves": len(values),
                "share_potent": 100 * (values >= POTENT_PIC50).mean(),
            }
        )
    return pd.DataFrame(rows)


def screen_shares() -> pd.DataFrame:
    screen = pd.read_csv(SRC / "cyp" / "cyp-challenge-single-concentration-TRAIN.csv")
    hit = (screen["log2fc_estimate"] < HIT_LOG2FC) & (screen["log2fc_fdr"] < HIT_FDR)
    screen = screen.assign(is_hit=hit)
    grouped = screen.groupby("enzyme")["is_hit"]
    return pd.DataFrame(
        {
            "enzyme": grouped.mean().index,
            "compounds_screened": grouped.size().values,
            "share_hit": 100 * grouped.mean().values,
        }
    )


def clearance_summary() -> pd.DataFrame:
    erx = pd.read_csv(SRC / "erxfull" / "expansion_data_train.csv")
    human = next(c for c in erx.columns if "HLM" in c and "CLint" in c)
    mouse = next(c for c in erx.columns if "MLM" in c and "CLint" in c)
    paired = erx[[human, mouse]].dropna()
    paired = paired[(paired[human] > 0) & (paired[mouse] > 0)]
    ratio = paired[mouse] / paired[human]
    return pd.DataFrame(
        [
            {
                "compounds_with_both": len(paired),
                "median_human_clint": paired[human].median(),
                "median_mouse_clint": paired[mouse].median(),
                "median_mouse_over_human": ratio.median(),
                "share_faster_in_mouse": 100 * (ratio > 1).mean(),
                "share_more_than_tenfold_faster": 100 * (ratio > 10).mean(),
                "human_column": human,
                "mouse_column": mouse,
            }
        ]
    )


def main() -> None:
    isoforms = fitted_shares().merge(screen_shares(), on="enzyme", how="outer")
    isoforms.to_csv(OUT / "isoform_summary.csv", index=False)
    clearance_summary().to_csv(OUT / "clearance_summary.csv", index=False)
    print(isoforms.to_string(index=False))
    print()
    print(clearance_summary().to_string(index=False))


if __name__ == "__main__":
    main()
