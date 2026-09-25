# Rebuilding the notebook's data

The notebook reads small tables from `notebook/data/` and the game from
`notebook/widgets/drain.js`. The scripts here produce all of them.

```
pip install "rdkit>=2023.9" "pandas>=2.2" "numpy>=1.26" lxml
python build_all.py
```

By default the competition files are read straight from their Hugging Face URLs.
To read them from a local copy instead, point `OPENADMET_DATA` at a directory
holding the per-dataset subdirectories named in `sources.py`.

| Script | Writes | What it does |
| --- | --- | --- |
| `build_drugs.py` | `data/drugs.csv` | Resolves every named drug in the roster to a parent structure through PubChem, with RxNav as the fallback for brand names. |
| `build_measured.py` | `data/measured.csv`, `data/measured_full_provenance.json` | Joins `drugs.csv` to the competition files by parent InChIKey and records the file and row behind every value. This is how the notebook knows which anonymous compound is quinidine. |
| `build_drain_data.py` | `data/drain/*.csv` | Trims the CYP inhibition, time-dependent inhibition, single-concentration screen and PXR files to the columns the notebook charts. |
| `../game/build.py` | `widgets/drain.js`, `game/drain.html` | Builds the game from its sources as a marimo widget and as a standalone page. |

`roster.py`, `resolve.py`, `chem.py` and `sources.py` are shared pieces the
scripts import. `cache/name_cache.json` holds every PubChem and RxNav answer, so
a rerun makes no name-resolution requests. A failed lookup is never cached.

`fda_hcp_table.csv` is FDA's public-domain CYP table, saved on 2026-09-17. The
roster of named drugs comes from it.
