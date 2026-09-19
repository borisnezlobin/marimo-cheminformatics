"""Write notebook/data/clinical_auc.csv: five human studies, one victim drug.

Each row is a published drug-interaction study in healthy volunteers, taken from
the perpetrator drug's own FDA label. All five use the same victim, desipramine,
which is an index substrate of CYP2D6, so the five exposure changes are the same
kind of quantity and can be compared to each other. Mixing victims would not be.

The quotes are fetched from openFDA, which serves FDA's structured product
labels and is public domain, and the build checks that each quote is still
present in a current label before writing the file. The fetched text is cached
in build/cache/label_quotes.json so a rebuild needs no network.

Run: python build_clinical_auc.py

One caveat travels with the quinidine row and is written into the file. Its
8-fold figure is a steady-state trough concentration (Cmin) from the
dextromethorphan-plus-quinidine combination product, not an AUC measured after a
single desipramine dose, so it is the least directly comparable of the five.
"""

import csv
import json
import os
import re
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(HERE, "cache", "label_quotes.json")
OUT_PATH = os.path.join(HERE, "..", "data", "clinical_auc.csv")
OPENFDA = "https://api.fda.gov/drug/label.json?search={query}&limit=5"
LABEL_SECTIONS = (
    "drug_interactions", "clinical_pharmacology", "warnings_and_cautions",
    "precautions", "dosage_and_administration", "spl_product_data_elements",
)

STUDIES = [
    {
        "drug_id": "quinidine",
        "victim": "desipramine",
        "enzyme": "CYP2D6",
        "auc_fold": 8.0,
        "measure": "steady-state Cmin",
        "quote": (
            "Co-administration of dextromethorphan 30 mg/quinidine 30 mg with the "
            "tricyclic antidepressant desipramine, a CYP2D6 substrate, when desipramine "
            "was given at a dose of 25 mg once daily in 13 healthy volunteers resulted in "
            "an approximately 8-fold increase in steady state desipramine exposure"
        ),
        "match": "8-fold increase in steady state desipramine exposure",
        "label": "Nuedexta (dextromethorphan hydrobromide and quinidine sulfate)",
    },
    {
        "drug_id": "terbinafine",
        "victim": "desipramine",
        "enzyme": "CYP2D6",
        "auc_fold": 5.0,
        "measure": "AUC",
        "quote": (
            "In a study to assess the effects of terbinafine on desipramine in healthy "
            "volunteers characterized as normal metabolizers, the administration of "
            "terbinafine resulted in a 2-fold increase in Cmax and a 5-fold increase in "
            "area under the curve (AUC)."
        ),
        "match": "5-fold increase in area under the curve",
        "label": "Lamisil (terbinafine hydrochloride)",
    },
    {
        "drug_id": "darifenacin",
        "victim": "desipramine",
        "enzyme": "CYP2D6",
        "auc_fold": 3.6,
        "measure": "AUC",
        "quote": (
            "The mean Cmax and AUC of desipramine, the active metabolite of imipramine, "
            "were increased by 260%."
        ),
        "match": "increased by 260",
        "label": "Enablex (darifenacin extended-release tablets)",
    },
    {
        "drug_id": "duloxetine",
        "victim": "desipramine",
        "enzyme": "CYP2D6",
        "auc_fold": 3.0,
        "measure": "AUC",
        "quote": (
            "When duloxetine was administered (at a dose of 60 mg twice daily) in "
            "conjunction with a single 50 mg dose of desipramine, a CYP2D6 substrate, the "
            "AUC of desipramine increased 3-fold."
        ),
        "match": "AUC of desipramine increased 3-fold",
        "label": "Cymbalta (duloxetine delayed-release capsules)",
    },
    {
        "drug_id": "escitalopram",
        "victim": "desipramine",
        "enzyme": "CYP2D6",
        "auc_fold": 2.0,
        "measure": "AUC",
        "quote": (
            "Coadministration of escitalopram (20 mg/day for 21 days) with the tricyclic "
            "antidepressant desipramine (single dose of 50 mg), a substrate for CYP2D6, "
            "resulted in a 40% increase in Cmax and a 100% increase in AUC of desipramine."
        ),
        "match": "100% increase in AUC of desipramine",
        "label": "Lexapro (escitalopram oxalate)",
    },
]

# Published against the same victim, quoted here for completeness, and excluded
# from clinical_auc.csv because the CYP challenge file has no fitted curve for it.
BUPROPION_NOTE = (
    "bupropion reports an approximately 5-fold desipramine AUC increase in the "
    "Wellbutrin label and has no fitted CYP2D6 curve in the competition data."
)


def query_url(drug_id: str) -> str:
    query = f'openfda.generic_name:"{drug_id}" AND "desipramine"'
    return OPENFDA.format(query=urllib.parse.quote(query))


def _load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as handle:
            return json.load(handle)
    return {}


def label_text(drug_id: str, cache: dict) -> str:
    if drug_id in cache:
        return cache[drug_id]
    with urllib.request.urlopen(query_url(drug_id), timeout=30) as response:
        payload = json.load(response)
    chunks = []
    for record in payload.get("results", []):
        for section in LABEL_SECTIONS:
            chunks.extend(record.get(section, []))
    text = re.sub(r"\s+", " ", " ".join(chunks))
    cache[drug_id] = text
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as handle:
        json.dump(cache, handle, indent=1)
    time.sleep(0.6)
    return text


def main() -> None:
    cache = _load_cache()
    rows, failures = [], []
    for study in STUDIES:
        text = label_text(study["drug_id"], cache)
        confirmed = study["match"].lower() in text.lower()
        if not confirmed:
            failures.append(study["drug_id"])
        rows.append({
            "drug_id": study["drug_id"],
            "victim": study["victim"],
            "enzyme": study["enzyme"],
            "auc_fold": study["auc_fold"],
            "measure": study["measure"],
            "quote": study["quote"],
            "label": study["label"],
            "quote_confirmed_in_current_label": confirmed,
            "source_url": query_url(study["drug_id"]),
        })
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"clinical_auc.csv: {len(rows)} studies, victim desipramine, enzyme CYP2D6")
    print("quotes confirmed against a current openFDA label: "
          f"{sum(r['quote_confirmed_in_current_label'] for r in rows)}/{len(rows)}")
    if failures:
        print(f"NOT CONFIRMED: {', '.join(failures)}")
    print(BUPROPION_NOTE)


if __name__ == "__main__":
    main()
