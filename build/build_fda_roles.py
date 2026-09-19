"""Write notebook/data/fda_roles.csv from FDA's public-domain CYP table.

The source is FDA's page of examples of drugs that interact with CYP enzymes,
written for healthcare professionals. It is a 245-row, 11-column HTML table that
`pandas.read_html` parses cleanly. FDA's website policy puts the contents of
fda.gov in the public domain, so the parsed table is bundled with the notebook
rather than fetched at run time.

Two parsing hazards, both of which silently corrupted an earlier run. Footnote
markers are glued onto drug names ("fluvoxamine8") and onto enzyme tokens
("1A220" is CYP1A2 followed by footnote 20), so enzyme tokens are matched
longest-first and trailing digits are then consumed. Missing that dropped
ciprofloxacin's CYP1A2 role entirely.

Run: python build_fda_roles.py
Pass --refetch to re-download the table from fda.gov and overwrite the bundled
copy; without it the bundled copy is parsed and nothing touches the network.
"""

import os
import re
import sys

import pandas as pd

from roster import NOT_A_SINGLE_STRUCTURE, SYNONYMS, drug_id, strip_footnotes

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE_PATH = os.path.join(HERE, "fda_hcp_table.csv")
OUT_PATH = os.path.join(HERE, "..", "data", "fda_roles.csv")
FDA_URL = (
    "https://www.fda.gov/drugs/drug-interactions-labeling/"
    "healthcare-professionals-fdas-examples-drugs-interact-cyp-enzymes-and-"
    "transporter-systems"
)

ROLE_COLUMNS = {
    "CYP Strg INH": ("inhibitor", "strong"),
    "CYP Mod INH": ("inhibitor", "moderate"),
    "CYP WK INH": ("inhibitor", "weak"),
    "CYP Strg IND": ("inducer", "strong"),
    "CYP Mod IND": ("inducer", "moderate"),
    "CYP WK IND": ("inducer", "weak"),
    "CYP SENS SUB": ("substrate", "sensitive"),
    "CYP Mod SENS SUB": ("substrate", "moderately_sensitive"),
}
# Longest first, so "2C19" is not read as "2C1" plus a stray digit.
ENZYME_TOKENS = ["2C19", "3A4/5", "1A2", "2B6", "2C8", "2C9", "2D6", "3A5", "3A4", "3A"]
_TOKEN = re.compile("|".join(re.escape(token) for token in ENZYME_TOKENS) + r"\d*")

# The four enzymes the competition measures, in FDA's own spelling. FDA writes
# CYP3A for the 3A4/3A5 pair, which is the label kept here.
MEASURED_ENZYMES = {"CYP1A2", "CYP2C9", "CYP2D6", "CYP3A"}


def enzymes_in(cell: str) -> list[str]:
    found = []
    for raw in _TOKEN.findall(str(cell)):
        for token in ENZYME_TOKENS:
            if raw.startswith(token):
                found.append("CYP" + ("3A" if token in ("3A4/5", "3A4") else token))
                break
    return list(dict.fromkeys(found))


def fetch_table() -> pd.DataFrame:
    tables = pd.read_html(FDA_URL)
    widest = max(tables, key=lambda t: t.shape[1] * t.shape[0])
    widest.to_csv(TABLE_PATH, index=False)
    return widest


def tidy(table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, record in table.iterrows():
        name = strip_footnotes(record["Drug or Other Substance"])
        if not name:
            continue
        name = SYNONYMS.get(name, name)
        key = drug_id(name)
        for column, (role, strength) in ROLE_COLUMNS.items():
            cell = record.get(column)
            if pd.isna(cell):
                continue
            for enzyme in enzymes_in(cell):
                rows.append((key, enzyme, role, strength))
    frame = pd.DataFrame(rows, columns=["drug_id", "enzyme", "role", "strength"])
    return frame.drop_duplicates().sort_values(["drug_id", "enzyme", "role"])


def main() -> None:
    table = fetch_table() if "--refetch" in sys.argv else pd.read_csv(TABLE_PATH)
    roles = tidy(table)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    roles.to_csv(OUT_PATH, index=False)

    combination_ids = {drug_id(name) for name in NOT_A_SINGLE_STRUCTURE}
    without_structure = roles[roles.drug_id.isin(combination_ids)]
    measured = roles[roles.enzyme.isin(MEASURED_ENZYMES)]
    print(f"fda_roles.csv: {len(roles)} assertions over {roles.drug_id.nunique()} drugs")
    print(f"  on the four enzymes the competition measures: {len(measured)}")
    print(f"  on entries that are not a single structure: {len(without_structure)}")
    print(roles.groupby(["role", "strength"]).drug_id.nunique().to_string())


if __name__ == "__main__":
    main()
