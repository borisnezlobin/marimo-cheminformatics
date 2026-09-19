"""Write notebook/data/sources.json: the URL and the pandas call for every file.

The notebook ships a small derived join table so a reader is not asked to
download gigabytes. This file is how the notebook stays citable anyway: it names
the Hugging Face repository, the exact URL, the licence and the one line of
pandas that loads the published file straight from the web.

Run: python build_sources_doc.py
Pass --check to fetch the first bytes of every URL and confirm it still serves.
"""

import json
import os
import sys
import urllib.error
import urllib.request

from sources import CONTEXT_SOURCES, SOURCES

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "..", "data", "sources.json")


def describe(source, joined: bool) -> dict:
    return {
        "repo": source.repo,
        "file": source.name,
        "url": source.url,
        "license": source.license,
        "structure_column": source.smiles_column or None,
        "identifier_column": source.id_column,
        "pandas": source.pandas_call,
        "joined_into_measured_csv": joined,
        "description": source.description,
    }


def reachable(url: str) -> bool:
    request = urllib.request.Request(url, headers={"Range": "bytes=0-256"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status in (200, 206)
    except urllib.error.HTTPError as error:
        return error.code in (200, 206, 416)
    except Exception:
        return False


def main() -> None:
    entries = {key: describe(source, True) for key, source in SOURCES.items()}
    entries.update({key: describe(source, False) for key, source in CONTEXT_SOURCES.items()})

    if "--check" in sys.argv:
        for key, entry in entries.items():
            entry["url_reachable_anonymously"] = reachable(entry["url"])
            print(f"{'ok  ' if entry['url_reachable_anonymously'] else 'FAIL'} {key}")

    with open(OUT_PATH, "w") as handle:
        json.dump({
            "note": (
                "Every competition file the build touches. Loading any of them needs "
                "nothing but the pandas call given here."
            ),
            "files": entries,
        }, handle, indent=1)
    print(f"sources.json: {len(entries)} files")


if __name__ == "__main__":
    main()
