"""Turn a drug name into a structure, through NLM's RxNav and PubChem.

Both services are free and need no key, and both throttle. An earlier run of
this pipeline lost the last twenty names of a batch to throttling and, because
the failures were written into the cache, reported four drugs as absent from the
data when they were present. Two rules follow from that, and both are enforced
here: every request backs off and retries, and a failure is never cached.

RxNorm has two ways of naming an ingredient and the build needs both. PIN, the
precise ingredient, names the exact salt or ester, so "triamcinolone acetonide"
stays itself instead of collapsing to triamcinolone, which is a different
molecule. IN, the plain ingredient, is how reference tables such as FDA's spell
the drug, so it is what the name join uses. Asking only for IN substitutes the
wrong structure; asking only for PIN breaks the join.
"""

import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(HERE, "cache", "name_cache.json")
MIN_INTERVAL_SECONDS = 0.35
_last_request_at = 0.0


def _load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as handle:
            return json.load(handle)
    return {}


def _save_cache(cache: dict) -> None:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as handle:
        json.dump(cache, handle, indent=1, sort_keys=True)


def _throttle() -> None:
    global _last_request_at
    wait = MIN_INTERVAL_SECONDS - (time.monotonic() - _last_request_at)
    if wait > 0:
        time.sleep(wait)
    _last_request_at = time.monotonic()


def _get_json(url: str, attempts: int = 6):
    delay = 1.0
    for attempt in range(attempts):
        _throttle()
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            if error.code not in (429, 503) or attempt == attempts - 1:
                return None
        except Exception:
            if attempt == attempts - 1:
                return None
        time.sleep(delay + random.random() * 0.4)
        delay *= 2
    return None


def rxnorm_names(name: str) -> dict:
    """{'PIN': precise ingredient, 'IN': ingredient}, either value possibly None."""
    base = "https://rxnav.nlm.nih.gov/REST"
    quoted = urllib.parse.quote(name)
    identifiers = _get_json(f"{base}/rxcui.json?name={quoted}&search=2")
    rxcui_list = (identifiers or {}).get("idGroup", {}).get("rxnormId") or []
    if not rxcui_list:
        return {}
    related = _get_json(f"{base}/rxcui/{rxcui_list[0]}/related.json?tty=IN+PIN")
    groups = (related or {}).get("relatedGroup", {}).get("conceptGroup", []) or []
    by_type = {g["tty"]: (g.get("conceptProperties") or []) for g in groups}
    return {
        tty: (by_type[tty][0]["name"] if by_type.get(tty) else None)
        for tty in ("PIN", "IN")
    }


def pubchem_structure(name: str) -> dict | None:
    quoted = urllib.parse.quote(name)
    url = (
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quoted}"
        "/property/Title,InChIKey,SMILES/JSON"
    )
    data = _get_json(url)
    try:
        properties = data["PropertyTable"]["Properties"][0]
    except Exception:
        return None
    if not properties.get("SMILES"):
        return None
    return {
        "cid": properties["CID"],
        "title": properties.get("Title"),
        "smiles": properties.get("SMILES"),
        "pubchem_inchikey": properties.get("InChIKey"),
    }


def resolve(name: str, use_rxnav: bool = True) -> dict:
    """Cached name lookup. Returns {query, ingredient, ingredient_base, ...structure}."""
    cache = _load_cache()
    if name in cache and cache[name].get("resolved"):
        return cache[name]

    # PubChem is asked for the literal name first. RxNorm's PIN is the fallback
    # for names PubChem does not index, chiefly brand names, and it has to be a
    # fallback rather than the first step: the PIN of "adefovir dipivoxil" is
    # "adefovir", which is the parent drug and a different structure.
    structure = pubchem_structure(name)
    terms = (rxnorm_names(name) if (use_rxnav and structure is None) else {}) or {}
    precise, base = terms.get("PIN"), terms.get("IN")
    if structure is None and precise:
        structure = pubchem_structure(precise)
    if structure is None and base and base != name:
        structure = pubchem_structure(base)

    record = {
        "query": name,
        "ingredient": precise,
        "ingredient_base": base,
        "resolved": structure is not None,
    }
    if structure is None:
        return record  # never cached: a miss is usually throttling, not absence
    record.update(structure)
    cache[name] = record
    _save_cache(cache)
    return record
