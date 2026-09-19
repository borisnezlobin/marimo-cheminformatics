"""Pre-renders the handful of molecules the notebook draws, so the notebook
itself needs no chemistry toolkit at runtime. Writes one SVG per drug into
../data/structures/."""

from pathlib import Path

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D

OUT = Path(__file__).resolve().parent.parent / "data" / "structures"
DRUGS = [
    "voriconazole",
    "isavuconazole",
    "quinine",
    "quinidine",
    "cisapride",
    "simvastatin",
    "clarithromycin",
    "levothyroxine",
]
SIZE = (340, 260)


def draw(smiles: str) -> str:
    """A clean 2D depiction. Coordinates are recomputed rather than reused,
    because a molecule carrying a 3D conformer otherwise draws as a flattened
    projection with atoms on top of each other."""
    mol = Chem.MolFromSmiles(smiles)
    rdDepictor.Compute2DCoords(mol)
    drawer = rdMolDraw2D.MolDraw2DSVG(*SIZE)
    options = drawer.drawOptions()
    options.clearBackground = False
    options.bondLineWidth = 2
    options.addStereoAnnotation = True
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    drugs = pd.read_csv(OUT.parent / "drugs.csv").set_index("drug_id")
    for drug_id in DRUGS:
        if drug_id not in drugs.index:
            print(f"missing from drugs.csv: {drug_id}")
            continue
        (OUT / f"{drug_id}.svg").write_text(draw(drugs.loc[drug_id, "smiles"]))
        print(f"wrote {drug_id}.svg")


if __name__ == "__main__":
    main()
