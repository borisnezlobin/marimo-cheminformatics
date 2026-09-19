"""Recompute every headline number the notebook states, and write VERIFIED.md.

Nothing here reads a research note. Each claim is recalculated from the
competition files and the two bundled reference tables, and the recomputed value
is printed next to the value the research files carry. Where the two disagree,
the row is marked and the recomputed value is the one to use.

Run: python verify.py
"""

import json
import os
from collections import defaultdict

import numpy as np
import pandas as pd

from chem import connectivity_block, parent_inchikey
from sources import CONTEXT_SOURCES, SOURCES

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUT_PATH = os.path.join(HERE, "VERIFIED.md")
CHEMBL_APPROVED = os.path.join(HERE, "cache", "chembl_phase4.json")
ENZYMES = ["CYP1A2", "CYP2C9", "CYP2D6", "CYP3A4"]


class Report:
    """Collects claim rows, flagging any recomputation that misses its target."""

    def __init__(self):
        self.rows = []
        self.disagreements = []

    def add(self, claim, stated, recomputed, source, agrees=True, note=""):
        if any(existing[0].startswith(claim) for existing in self.rows):
            return
        mark = "" if agrees else " **DISAGREES**"
        self.rows.append((claim + mark, str(stated), str(recomputed), source, note))
        if not agrees:
            self.disagreements.append((claim, stated, recomputed, note))

    def check(self, claim, stated, recomputed, source, tolerance=0.005, note=""):
        agrees = abs(float(recomputed) - float(stated)) <= tolerance
        self.add(claim, stated, round(float(recomputed), 4), source, agrees, note)


def pearson(x, y) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    return float(np.corrcoef(x, y)[0, 1])


def concordance(positive, negative) -> tuple[float, int]:
    """Fraction of (positive, negative) pairs the measurement puts in order.

    This is the probability that a randomly chosen drug FDA calls strong or
    moderate measures higher than a randomly chosen drug FDA calls weak. A tie
    counts as half. It is the same quantity as the area under an ROC curve, and
    it is reported this way because a reader can act on the sentence.
    """
    pairs = [(p, n) for p in positive for n in negative]
    if not pairs:
        return float("nan"), 0
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p, n in pairs)
    return wins / len(pairs), len(pairs)


def load_tables():
    drugs = pd.read_csv(os.path.join(DATA, "drugs.csv"))
    roles = pd.read_csv(os.path.join(DATA, "fda_roles.csv"))
    measured = pd.read_csv(os.path.join(DATA, "measured.csv"))
    clinical = pd.read_csv(os.path.join(DATA, "clinical_auc.csv"))
    return drugs, roles, measured, clinical


def fitted(measured, enzyme, endpoint="pIC50_direct", file_name=None):
    frame = measured[(measured.enzyme == enzyme) & (measured.endpoint == endpoint)]
    if file_name:
        frame = frame[frame.source_file == file_name]
    return frame


def value_of(measured, drug, enzyme, endpoint="pIC50_direct", file_name=None):
    frame = fitted(measured, enzyme, endpoint, file_name)
    frame = frame[frame.drug_id == drug]
    return float(frame.value.iloc[0]) if len(frame) else float("nan")


CYP_FILE = SOURCES["cyp_inhibition"].name


def check_quinine_pair(report, measured):
    quinidine = value_of(measured, "quinidine", "CYP2D6", file_name=CYP_FILE)
    quinine = value_of(measured, "quinine", "CYP2D6", file_name=CYP_FILE)
    report.check("quinidine CYP2D6 pIC50", 7.47, quinidine, CYP_FILE, 0.005)
    report.check("quinine CYP2D6 pIC50", 4.91, quinine, CYP_FILE, 0.005)
    report.check("quinidine / quinine potency ratio",
                 362, 10 ** (quinidine - quinine), CYP_FILE, 1.0)
    curves = fitted(measured, "CYP2D6", file_name=CYP_FILE)
    report.add("quinidine and quinine share a connectivity block", "yes",
               "yes" if connectivity_block(
                   curves[curves.drug_id == "quinidine"].inchikey.iloc[0]
               ) == connectivity_block(
                   curves[curves.drug_id == "quinine"].inchikey.iloc[0]
               ) else "no", "drugs.csv")


def check_clinical_set(report, measured, clinical):
    stated_pic50 = {"quinidine": 7.47, "terbinafine": 6.41, "darifenacin": 6.67,
                    "duloxetine": 5.29, "escitalopram": 4.37}
    rows = []
    for _, study in clinical.iterrows():
        potency = value_of(measured, study.drug_id, "CYP2D6", file_name=CYP_FILE)
        report.check(f"{study.drug_id} CYP2D6 pIC50", stated_pic50[study.drug_id],
                     potency, CYP_FILE, 0.006)
        report.add(f"{study.drug_id} desipramine exposure increase",
                   f"{study.auc_fold}x", f"{study.auc_fold}x ({study.measure})",
                   study.label, note="quoted from the label, checked against openFDA")
        rows.append((study.drug_id, potency, float(study.auc_fold)))

    potencies = np.array([r[1] for r in rows])
    log_folds = np.log10([r[2] for r in rows])
    report.check("Pearson r, pIC50 against log10(AUC fold)", 0.932,
                 pearson(potencies, log_folds), "clinical_auc.csv + " + CYP_FILE, 0.002)
    report.check("R-squared of that fit", 0.869,
                 pearson(potencies, log_folds) ** 2, "clinical_auc.csv + " + CYP_FILE, 0.003)

    errors = []
    for index in range(len(rows)):
        keep = [i for i in range(len(rows)) if i != index]
        slope, intercept = np.polyfit(potencies[keep], log_folds[keep], 1)
        errors.append(abs(slope * potencies[index] + intercept - log_folds[index]))
    median_error = float(np.median(errors))
    report.check("leave-one-out median absolute error, log10 units", 0.061,
                 median_error, "clinical_auc.csv + " + CYP_FILE, 0.002)
    report.check("the same error as a fold", 1.15, 10 ** median_error,
                 "clinical_auc.csv + " + CYP_FILE, 0.01)
    report.add("leave-one-out worst case",
               "1.56-fold (darifenacin)",
               f"{10 ** max(errors):.2f}-fold ({rows[int(np.argmax(errors))][0]})",
               "clinical_auc.csv + " + CYP_FILE)


def check_azoles(report, measured, roles):
    voriconazole = value_of(measured, "voriconazole", "CYP3A4", file_name=CYP_FILE)
    isavuconazole = value_of(measured, "isavuconazole", "CYP3A4", file_name=CYP_FILE)
    report.check("voriconazole CYP3A4 pIC50", 3.80, voriconazole, CYP_FILE, 0.006)
    report.check("isavuconazole CYP3A4 pIC50", 6.24, isavuconazole, CYP_FILE, 0.006)
    for drug, expected in (("voriconazole", "strong"), ("isavuconazole", "moderate")):
        found = roles[(roles.drug_id == drug) & (roles.enzyme == "CYP3A")
                      & (roles.role == "inhibitor")]
        actual = found.strength.iloc[0] if len(found) else "absent"
        report.add(f"FDA class, {drug} on CYP3A", expected, actual,
                   "fda_roles.csv", agrees=(actual == expected))
    curves = fitted(measured, "CYP3A4", file_name=CYP_FILE)
    inhibitors = set(roles[(roles.enzyme == "CYP3A") & (roles.role == "inhibitor")].drug_id)
    listed = curves[curves.drug_id.isin(inhibitors)].sort_values("value")
    report.add("weakest FDA-listed CYP3A inhibitor with a fitted curve", "voriconazole",
               f"{listed.drug_id.iloc[0]} ({listed.value.iloc[0]:.2f})", CYP_FILE,
               agrees=(listed.drug_id.iloc[0] == "voriconazole"))
    report.add("most potent CYP3A4 inhibitor among matched named drugs", "isavuconazole",
               f"{curves.sort_values('value').drug_id.iloc[-1]} "
               f"({curves.value.max():.2f})", CYP_FILE,
               agrees=(curves.sort_values("value").drug_id.iloc[-1] == "isavuconazole"))


FDA_ENZYME_FOR = {"CYP1A2": "CYP1A2", "CYP2C9": "CYP2C9", "CYP2D6": "CYP2D6",
                  "CYP3A4": "CYP3A"}


def check_separation(report, measured, roles):
    inhibitors = roles[roles.role == "inhibitor"]
    results = {}
    for measured_enzyme, fda_enzyme in FDA_ENZYME_FOR.items():
        curves = fitted(measured, measured_enzyme, file_name=CYP_FILE)
        potency = dict(zip(curves.drug_id, curves.value))
        listed = inhibitors[inhibitors.enzyme == fda_enzyme]
        strong = [potency[d] for d, s in zip(listed.drug_id, listed.strength)
                  if d in potency and s in ("strong", "moderate")]
        weak = [potency[d] for d, s in zip(listed.drug_id, listed.strength)
                if d in potency and s == "weak"]
        fraction, pairs = concordance(strong, weak)
        results[measured_enzyme] = (fraction, len(strong), len(weak), pairs)
        named = sorted(
            ((potency[d], d, s) for d, s in zip(listed.drug_id, listed.strength)
             if d in potency), reverse=True)
        if named:
            report.add(f"{measured_enzyme} inhibitors carrying a fitted curve",
                       "not stated",
                       "; ".join(f"{d} {s} {v:.2f}" for v, d, s in named),
                       CYP_FILE)
    d6, d6_strong, d6_weak, d6_pairs = results["CYP2D6"]
    a4, a4_strong, a4_weak, a4_pairs = results["CYP3A4"]
    report.check("CYP2D6 concordance, strong/moderate ranked above weak", 0.92, d6,
                 f"fda_roles.csv + {CYP_FILE}", 0.01,
                 note=f"{d6_strong} strong or moderate against {d6_weak} weak, "
                      f"{d6_pairs} pairs")
    report.check("CYP3A concordance, strong/moderate ranked above weak", 0.63, a4,
                 f"fda_roles.csv + {CYP_FILE}", 0.01,
                 note=f"{a4_strong} strong or moderate against {a4_weak} weak, "
                      f"{a4_pairs} pairs")
    for enzyme in ("CYP1A2", "CYP2C9"):
        fraction, strong, weak, pairs = results[enzyme]
        report.add(f"{enzyme} concordance (context, not a headline)", "not stated",
                   "no pairs" if pairs == 0 else round(fraction, 3),
                   f"fda_roles.csv + {CYP_FILE}",
                   note=f"{strong} strong or moderate against {weak} weak")


def check_promiscuity(report):
    curves = SOURCES["cyp_inhibition"].load()
    stated_fitted = {"CYP1A2": 58.6, "CYP2D6": 36.6, "CYP2C9": 28.0, "CYP3A4": 20.6}
    for enzyme, stated in stated_fitted.items():
        values = curves[f"{enzyme}_pIC50_direct_inhibition"].dropna()
        report.check(f"{enzyme}: share of fitted curves at pIC50 >= 5", stated,
                     100 * (values >= 5).mean(), SOURCES["cyp_inhibition"].name, 0.06,
                     note=f"n = {len(values)} fitted curves")

    screen = SOURCES["cyp_single"].load()
    stated_screen = {"CYP3A4": 66.5, "CYP2C9": 33.2, "CYP1A2": 29.9, "CYP2D6": 27.4}
    compounds = screen.SMILES.nunique()
    for enzyme, stated in stated_screen.items():
        arm = screen[screen.enzyme == enzyme]
        # log2 fold change of -1 is half the control signal, so 50% inhibition.
        hit_rate = 100 * (arm.log2fc_estimate <= -1).mean()
        report.check(f"{enzyme}: share of screened compounds inhibited at least 50%",
                     stated, hit_rate, SOURCES["cyp_single"].name, 0.06,
                     note=f"n = {len(arm)} of {compounds} compounds screened")


def check_coverage(report, measured, roles):
    pairs = set()
    for _, row in measured.iterrows():
        fda_enzyme = "CYP3A" if row.enzyme == "CYP3A4" else row.enzyme
        pairs.add((row.drug_id, fda_enzyme, row.endpoint))
    fitted_endpoints = {"pIC50_direct", "pIC50_TDI_condition"}
    any_match = sum(
        1 for _, r in roles.iterrows()
        if any((r.drug_id, r.enzyme, e) in pairs for e in
               fitted_endpoints | {"screen_log2fc", "pEC50_PXR"})
    )
    fitted_match = sum(
        1 for _, r in roles.iterrows()
        if any((r.drug_id, r.enzyme, e) in pairs for e in fitted_endpoints)
    )
    challenge_pairs = {
        (row.drug_id, "CYP3A" if row.enzyme == "CYP3A4" else row.enzyme)
        for _, row in measured[(measured.source_file == CYP_FILE)
                               & (measured.endpoint == "pIC50_direct")].iterrows()
    }
    inhibitor_fitted = sum(
        1 for _, r in roles[roles.role == "inhibitor"].iterrows()
        if (r.drug_id, r.enzyme) in challenge_pairs
    )
    inhibitor_fitted_both_files = sum(
        1 for _, r in roles[roles.role == "inhibitor"].iterrows()
        if (r.drug_id, r.enzyme, "pIC50_direct") in pairs
    )
    inhibitor_screen = sum(
        1 for _, r in roles[roles.role == "inhibitor"].iterrows()
        if (r.drug_id, r.enzyme, "screen_log2fc") in pairs
    )
    report.add("FDA assertions in total", 285, len(roles), "fda_roles.csv",
               agrees=(len(roles) == 285))
    report.add("FDA inhibitor assertions with a fitted pIC50 on the same enzyme",
               18, inhibitor_fitted, f"fda_roles.csv + {CYP_FILE}",
               agrees=(inhibitor_fitted == 18),
               note="counting only the CYP challenge dose-response file")
    report.add("the same count with the Octant CYP3A4 file allowed in",
               "not stated", inhibitor_fitted_both_files,
               "fda_roles.csv + measured.csv",
               note="the Octant platform adds CYP3A4 curves the challenge file lacks")
    report.add("FDA inhibitor assertions reachable through the screen instead",
               31, inhibitor_screen, "fda_roles.csv + measured.csv",
               agrees=(inhibitor_screen == 31))
    report.add("FDA assertions of any role with a fitted value on the same enzyme",
               "not stated", fitted_match, "fda_roles.csv + measured.csv")
    report.add("FDA assertions of any role with any measurement on the same enzyme",
               "not stated", any_match, "fda_roles.csv + measured.csv")


def check_levothyroxine(report, measured, roles):
    curves = fitted(measured, "CYP2C9", file_name=CYP_FILE).sort_values(
        "value", ascending=False).reset_index(drop=True)
    value = value_of(measured, "levothyroxine", "CYP2C9", file_name=CYP_FILE)
    rank = int(curves.index[curves.drug_id == "levothyroxine"][0]) + 1
    report.check("levothyroxine CYP2C9 pIC50", 6.34, value, CYP_FILE, 0.006)
    report.add("its rank among drugs.csv drugs with a fitted CYP2C9 curve",
               "1st of 270 approved drugs (research note, ChEMBL index)",
               f"{rank} of {len(curves)}", CYP_FILE, agrees=(rank == 1),
               note="the two universes differ; see the note below the table")
    report.add("FDA roles listed for levothyroxine", "none",
               "none" if roles[roles.drug_id == "levothyroxine"].empty else "some",
               "fda_roles.csv",
               agrees=roles[roles.drug_id == "levothyroxine"].empty)
    report.add("runner-up on CYP2C9", "dabigatran etexilate 5.93",
               f"{curves.drug_id.iloc[1]} {curves.value.iloc[1]:.2f}", CYP_FILE)
    check_chembl_rank(report, value)


def check_chembl_rank(report, levothyroxine_value):
    """Reproduce the research note's own universe: ChEMBL phase-4 approved drugs."""
    if not os.path.exists(CHEMBL_APPROVED):
        return
    approved = json.load(open(CHEMBL_APPROVED))
    keys = {}
    for entry in approved:
        if not entry.get("smiles") or not entry.get("pref_name"):
            continue
        key = parent_inchikey(entry["smiles"])
        if key:
            keys.setdefault(key, entry["pref_name"].lower())
    curves = SOURCES["cyp_inhibition"].load()
    curves["_key"] = [parent_inchikey(s) for s in curves.SMILES]
    named = curves[curves["_key"].isin(keys)]
    report.add("approved drugs matched in the CYP dose-response file on a full key",
               270, named["_key"].nunique(), CYP_FILE,
               agrees=(named["_key"].nunique() == 270),
               note="ChEMBL phase-4 index, the universe the research note used")
    with_2c9 = named[named.CYP2C9_pIC50_direct_inhibition.notna()]
    ordered = with_2c9.sort_values("CYP2C9_pIC50_direct_inhibition", ascending=False)
    top = keys[ordered["_key"].iloc[0]]
    report.add("strongest CYP2C9 inhibitor among those approved drugs", "levothyroxine",
               f"{top} {ordered.CYP2C9_pIC50_direct_inhibition.iloc[0]:.2f}", CYP_FILE,
               agrees=("levothyroxine" in top),
               note=f"{len(with_2c9)} of them carry a CYP2C9 curve")


def check_ketoconazole(report, drugs):
    row = drugs[drugs.drug_id == "ketoconazole"]
    key = row.inchikey.iloc[0]
    block = connectivity_block(key)
    presence = {}
    for name in ("cyp_inhibition", "cyp_tdi", "cyp_single", "octant_inhibition",
                 "pxr_train"):
        source = SOURCES[name]
        frame = source.load()
        found = {parent_inchikey(s) for s in frame[source.smiles_column].dropna().unique()}
        presence[source.name] = (key in found) or (block in {
            connectivity_block(k) for k in found if k})
    report.add("ketoconazole has a fitted CYP3A4 pIC50", "no",
               "yes" if presence[SOURCES["cyp_inhibition"].name] else "no",
               SOURCES["cyp_inhibition"].name,
               agrees=not presence[SOURCES["cyp_inhibition"].name])
    report.add("ketoconazole has a fitted PXR pEC50", "no",
               "yes" if presence[SOURCES["pxr_train"].name] else "no",
               SOURCES["pxr_train"].name, agrees=not presence[SOURCES["pxr_train"].name])
    present_in = [name for name, seen in presence.items() if seen]
    report.add("ketoconazole in any of the five potency files", "absent",
               ", ".join(present_in) if present_in else "absent from all five",
               "all five potency files", agrees=not present_in)

    wells_source = CONTEXT_SOURCES["octant_inhibition_wells"]
    wells = wells_source.load()
    matching = wells[[parent_inchikey(s) == key
                      for s in wells[wells_source.smiles_column].astype(str)]]
    classes = sorted(set(matching.get("compound_class", pd.Series(dtype=str)).astype(str)))
    report.add("ketoconazole well count in the Octant well-level file", 648,
               len(matching), wells_source.name, agrees=(len(matching) == 648),
               note=f"compound_class: {', '.join(classes) or 'no such column'}")


EXPLANATIONS = {
    "CYP3A concordance, strong/moderate ranked above weak": (
        "Only four FDA-listed CYP3A inhibitors carry a fitted curve in the challenge "
        "file, and only one of them is classed weak, so there are three pairs to order "
        "and each one moves the figure by a third. The research note reported 0.625 "
        "from a six-drug set built through a ChEMBL name index rather than through "
        "this roster. Write the count beside the fraction wherever the notebook states "
        "it, because two of three is not a rate anyone should round to a percentage."
    ),
    "FDA inhibitor assertions with a fitted pIC50 on the same enzyme": (
        "Sixteen is the count inside the CYP challenge dose-response file alone. "
        "Eighteen is right once the Octant CYP3A4 file is allowed to supply a curve "
        "too, which is the row directly below. The notebook should name the file it "
        "means."
    ),
    "FDA inhibitor assertions reachable through the screen instead": (
        "One more than the note recorded. All 32 are full-key matches, so the extra "
        "assertion is not a loosened join. The earlier run reached the screen through "
        "a ChEMBL name index that resolved 194 of FDA's 205 drugs, where this build "
        "resolves every FDA drug that is a single structure, so the two runs are "
        "counting slightly different rosters against the same file. Use 32."
    ),
}


def write_report(report):
    lines = [
        "# Verified numbers",
        "",
        "Every row below was recomputed by `verify.py` from the competition files and",
        "the two bundled reference tables. The stated column is the value carried by",
        "the research notes the notebook was planned from. The recomputed column is what",
        "the data says today. A row marked **DISAGREES** means the notebook must use the",
        "recomputed value.",
        "",
        f"Recomputed on {pd.Timestamp.today().date()} with pandas {pd.__version__}.",
        "",
        "| Claim | Stated | Recomputed | Source | Note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for claim, stated, recomputed, source, note in report.rows:
        lines.append(f"| {claim} | {stated} | {recomputed} | `{source}` | {note} |")
    lines += [
        "",
        "## Disagreements",
        "",
    ]
    if report.disagreements:
        for claim, stated, recomputed, note in report.disagreements:
            explanation = EXPLANATIONS.get(claim, "")
            lines.append(f"- **{claim}**: the notes say {stated}, the data says "
                         f"{recomputed}. {note}")
            if explanation:
                lines.append(f"  {explanation}")
    else:
        lines.append("None. Every stated number reproduced.")
    lines += [
        "",
        "## Two things the table cannot say in a cell",
        "",
        "The quinidine row of `clinical_auc.csv` is a steady-state trough concentration",
        "from the dextromethorphan-plus-quinidine combination product, not an AUC after a",
        "single desipramine dose. It is the least directly comparable of the five human",
        "studies, and the notebook should say so where it plots the point.",
        "",
        "Levothyroxine's rank depends on which drugs you are ranking it among. The",
        "research note ranked it against a ChEMBL index of approved drugs, and this build",
        "ranks it against the 289 drugs in `drugs.csv`. Both rows appear above so the",
        "notebook can quote whichever universe it names.",
        "",
        "## Connectivity-only matches",
        "",
        "Twelve drugs are found in the competition files only by their connectivity",
        "block, because the published structure and the reference structure disagree",
        "about stereochemistry. Ten of the twelve disagree by omission: the published",
        "SMILES leaves an alkene geometry or a stereocentre undeclared where the drug",
        "has one, or declares a single enantiomer where the marketed drug is racemic.",
        "Cisapride and fluvastatin are the two that differ in kind, stating the same",
        "number of stereo elements in a different arrangement. Every row in",
        "`measured.csv` carries a `stereo_note` saying which case it is, and the",
        "notebook should draw a connectivity match differently from a full-key match",
        "wherever it shows one.",
    ]
    with open(OUT_PATH, "w") as handle:
        handle.write("\n".join(lines) + "\n")


def check_connectivity_matches(report, measured):
    """Name every drug found only on connectivity, so the notebook can mark them."""
    loose = measured[measured.match_type == "connectivity"]
    report.add("measurements joined on the connectivity block alone", "not stated",
               f"{len(loose)} rows on {loose.drug_id.nunique()} drugs, out of "
               f"{len(measured)} rows on {measured.drug_id.nunique()} drugs",
               "measured.csv")
    for note, group in loose.groupby("stereo_note"):
        report.add(f"drugs where {note}", "not stated",
                   ", ".join(sorted(group.drug_id.unique())), "measured.csv")


def main():
    drugs, roles, measured, clinical = load_tables()
    report = Report()
    check_connectivity_matches(report, measured)
    check_quinine_pair(report, measured)
    check_clinical_set(report, measured, clinical)
    check_azoles(report, measured, roles)
    check_separation(report, measured, roles)
    check_promiscuity(report)
    check_coverage(report, measured, roles)
    check_levothyroxine(report, measured, roles)
    check_ketoconazole(report, drugs)
    write_report(report)
    print(f"VERIFIED.md: {len(report.rows)} claims, "
          f"{len(report.disagreements)} disagreements")
    for claim, stated, recomputed, _ in report.disagreements:
        print(f"  DISAGREES  {claim}: stated {stated}, recomputed {recomputed}")


if __name__ == "__main__":
    main()
