# Rebuilding the notebook's data

Everything in `notebook/data/` is produced by the scripts in this directory. The
notebook reads only the built files, so a judge running the notebook touches no
network and no chemistry toolkit. This directory is what produced them.

## Running it

```
pip install "rdkit>=2024.3" "pandas>=2.2" "numpy>=1.26" lxml
python build_all.py
```

`build_all.py` runs the eight steps below in order and finishes by rewriting
`VERIFIED.md`. From a warm cache the whole thing takes about five minutes, most
of it spent turning structures into InChIKeys.

By default the competition files are read straight from their Hugging Face URLs.
To read them from a local copy instead, point `OPENADMET_DATA` at a directory
holding the per-dataset subdirectories `cyp/`, `pxr/`, `oct/`, `erx/`, `asap/`:

```
OPENADMET_DATA=/path/to/data python build_all.py
```

## The steps

| Script | Writes | What it does |
| --- | --- | --- |
| `build_drugs.py` | `data/drugs.csv` | Resolves every drug in the roster to a parent structure through PubChem, with RxNav as the fallback for brand names. |
| `build_fda_roles.py` | `data/fda_roles.csv` | Parses FDA's public-domain CYP table into one row per drug, enzyme, role and strength. |
| `build_clinical_auc.py` | `data/clinical_auc.csv` | Holds the five human desipramine studies and checks each quote against a current FDA label through openFDA. |
| `build_measured.py` | `data/measured.csv`, `data/measured_full_provenance.json` | Joins `drugs.csv` to the competition files by parent InChIKey and records the file and row index behind every value. |
| `build_sources_doc.py` | `data/sources.json` | Writes the URL, licence and pandas call for each competition file. `--check` confirms each URL still serves. |
| `build_game.py` | `data/game.json`, `data/game_provenance.json`, `data/structures/game/` | Assembles the three compound pools the game draws from, turns each measurement into a score between zero and one through a named transformation, and records the file and row behind every value. |
| `verify.py` | `VERIFIED.md` | Recomputes every headline number the notebook states and marks any that no longer holds. |
| `verify_game.py` | `GAME_VERIFIED.md` | Opens every game value against its source row, recomputes every score, and reports what each ward's gates actually do. |

`roster.py`, `resolve.py`, `chem.py` and `sources.py` are the shared pieces the
scripts import. Nothing in this directory is imported by the notebook itself.

## Caches, and why they matter

`cache/name_cache.json` holds every PubChem and RxNav answer, and
`cache/label_quotes.json` holds every openFDA label. A rerun with both present
makes no name-resolution requests at all.

A failed lookup is never written to the cache. Both services throttle, and an
earlier version of this pipeline cached its throttled failures, which made four
drugs that are present in the data look absent from it. If a drug resolves on
one run and not the next, the answer is to run it again, not to record the miss.

## Inputs kept in this directory

`fda_hcp_table.csv` is FDA's table as `pandas.read_html` parses it, saved on
2026-09-17 from the healthcare-professionals page. FDA's website policy puts the
contents of fda.gov in the public domain, so it is bundled rather than fetched at
run time. `build_fda_roles.py --refetch` downloads a fresh copy and overwrites
it. The table is maintained by hand and its formatting is not stable, so a
refetch should be followed by reading `VERIFIED.md` for changed counts.

`cache/chembl_phase4.json` is a ChEMBL list of approved drugs, used by `verify.py`
for one check only: reproducing the 270-approved-drug universe an earlier
analysis ranked levothyroxine within. Nothing else reads it.

## Reading `VERIFIED.md` first

`VERIFIED.md` is regenerated on every build and it is the authority on what the
notebook may claim. Three numbers in the planning notes did not reproduce, and
each one has a row, a recomputed value and an explanation of the difference.
