"""Structure handling for the build, using RDKit only.

A drug is bought and recorded as a salt or a co-crystal ("metoprolol tartrate",
"atorvastatin calcium"), but the thing that enters a liver enzyme is the parent
molecule. Every structure that passes through the build is therefore reduced to
its parent first: the largest organic fragment, neutralised. Stereochemistry is
kept, because quinine and quinidine differ only there and differ 362-fold in the
measured data.

Two identifiers come out of that parent. The full standard InChIKey is 27
characters and encodes stereochemistry in its second block. The connectivity
block is the first 14 characters and encodes only which atom is bonded to which,
so two stereoisomers share it. Matching on the full key is correct; matching on
the connectivity block alone finds more rows but can merge stereoisomers, which
is why every such match is flagged rather than silently accepted.
"""

import re

from rdkit import Chem, RDLogger
from rdkit.Chem.MolStandardize import rdMolStandardize

RDLogger.DisableLog("rdApp.*")

_largest_fragment = rdMolStandardize.LargestFragmentChooser()
_uncharger = rdMolStandardize.Uncharger()
_cx_extension = re.compile(r"\s*\|[^|]*\|\s*$")
_cache: dict[str, tuple[str | None, str | None]] = {}


def clean_smiles(smiles: str) -> str:
    """Drop the CXSMILES extension block some files append after the SMILES."""
    return _cx_extension.sub("", str(smiles)).strip()


def parent_mol(smiles: str):
    mol = Chem.MolFromSmiles(clean_smiles(smiles))
    if mol is None:
        return None
    try:
        return _uncharger.uncharge(_largest_fragment.choose(mol))
    except Exception:
        return None


def parent_identity(smiles: str) -> tuple[str | None, str | None]:
    """(parent canonical SMILES, parent full InChIKey), or (None, None) if unparseable."""
    key = clean_smiles(smiles)
    if key in _cache:
        return _cache[key]
    mol = parent_mol(key)
    result = (None, None)
    if mol is not None:
        try:
            result = (Chem.MolToSmiles(mol), Chem.MolToInchiKey(mol))
        except Exception:
            result = (None, None)
    _cache[key] = result
    return result


def parent_inchikey(smiles: str) -> str | None:
    return parent_identity(smiles)[1]


def connectivity_block(inchikey: str | None) -> str | None:
    return inchikey[:14] if inchikey else None


def defined_stereo_count(smiles: str) -> int:
    """Stereocentres plus double bonds whose arrangement the SMILES actually states."""
    mol = parent_mol(smiles)
    if mol is None:
        return 0
    centres = Chem.FindMolChiralCenters(mol, includeUnassigned=True,
                                        useLegacyImplementation=False)
    assigned = sum(1 for _, label in centres if label != "?")
    bonds = sum(1 for bond in mol.GetBonds()
                if bond.GetStereo() != Chem.BondStereo.STEREONONE)
    return assigned + bonds


def stereo_relationship(dataset_smiles: str, reference_smiles: str) -> str:
    """How a connectivity-block match differs, in words the notebook can print."""
    in_data = defined_stereo_count(dataset_smiles)
    in_reference = defined_stereo_count(reference_smiles)
    if in_data < in_reference:
        return "the published structure states less stereochemistry than the drug has"
    if in_data > in_reference:
        return "the published structure states more stereochemistry than the reference"
    return "the published structure states a different arrangement at the same centres"


def undefined_stereocentres(smiles: str) -> int:
    mol = parent_mol(smiles)
    if mol is None:
        return 0
    found = Chem.FindMolChiralCenters(mol, includeUnassigned=True, useLegacyImplementation=False)
    return sum(1 for _, label in found if label == "?")
