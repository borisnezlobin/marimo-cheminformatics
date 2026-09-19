"""Write notebook/data/drugs.csv: one row per drug, with a parent structure.

Run: python build_drugs.py
Every network lookup is cached in build/cache/name_cache.json, so a second run
does no network work at all and produces the same file.
"""

import csv
import os
import sys

from chem import parent_identity, connectivity_block
from resolve import resolve
from roster import roster

HERE = os.path.dirname(os.path.abspath(__file__))
FDA_TABLE = os.path.join(HERE, "fda_hcp_table.csv")
OUT_PATH = os.path.join(HERE, "..", "data", "drugs.csv")
COLUMNS = ["drug_id", "display_name", "aliases", "smiles", "inchikey", "inchikey_block"]


def build() -> tuple[list[dict], list[str]]:
    entries = roster(FDA_TABLE)
    rows, unresolved = [], []
    for index, (key, entry) in enumerate(sorted(entries.items()), start=1):
        record = resolve(entry["query"])
        if not record.get("resolved"):
            unresolved.append(key)
            print(f"  [{index}/{len(entries)}] {key}: unresolved", file=sys.stderr)
            continue
        smiles, inchikey = parent_identity(record["smiles"])
        if inchikey is None:
            unresolved.append(f"{key} (unparseable SMILES)")
            continue
        # The drug's own name is an alias too, so a lookup is one membership test.
        aliases = set(entry["aliases"]) | {key, key.replace("_", " ")}
        for extra in (record.get("ingredient"), record.get("ingredient_base"), record.get("title")):
            if extra:
                aliases.add(str(extra).lower())
        rows.append({
            "drug_id": key,
            "display_name": entry["display_name"],
            "aliases": "|".join(sorted(aliases)),
            "smiles": smiles,
            "inchikey": inchikey,
            "inchikey_block": connectivity_block(inchikey),
        })
        if index % 25 == 0:
            print(f"  [{index}/{len(entries)}] resolved so far: {len(rows)}", file=sys.stderr)
    return rows, unresolved


def main() -> None:
    rows, unresolved = build()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    distinct_keys = len({row["inchikey"] for row in rows})
    print(f"drugs.csv: {len(rows)} drugs, {distinct_keys} distinct parent InChIKeys")
    if unresolved:
        print(f"unresolved ({len(unresolved)}): {', '.join(unresolved)}")


if __name__ == "__main__":
    main()
