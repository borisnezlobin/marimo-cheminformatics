"""Where every competition file comes from, and how to load it.

Each entry names the Hugging Face dataset repository, the file inside it, the
column that holds the structure, the column that holds the compound identifier,
and the exact `pandas` call that loads it straight from the web. The notebook
quotes these so a reader can reproduce any row without downloading the build's
derived table.

Set the environment variable `OPENADMET_DATA` to a directory holding the same
files (in the per-dataset subdirectories named below) and the build reads from
disk instead of the network. Everything else is identical either way.
"""

import os
from dataclasses import dataclass

import pandas as pd

HF_BASE = "https://huggingface.co/datasets/{repo}/resolve/main/{name}"


@dataclass(frozen=True)
class Source:
    key: str
    repo: str
    name: str
    subdir: str
    smiles_column: str
    id_column: str
    license: str
    description: str

    @property
    def separator(self) -> str:
        return "\t" if self.name.endswith(".tsv") else ","

    @property
    def url(self) -> str:
        return HF_BASE.format(repo=self.repo, name=self.name)

    @property
    def pandas_call(self) -> str:
        if self.separator == "\t":
            return f'pd.read_csv("{self.url}", sep="\\t")'
        return f'pd.read_csv("{self.url}")'

    def load(self) -> pd.DataFrame:
        local_root = os.environ.get("OPENADMET_DATA")
        if local_root:
            path = os.path.join(local_root, self.subdir, self.name)
            if os.path.exists(path):
                return pd.read_csv(path, sep=self.separator, low_memory=False)
        return pd.read_csv(self.url, sep=self.separator, low_memory=False)


SOURCES: dict[str, Source] = {
    source.key: source
    for source in [
        Source(
            key="cyp_inhibition",
            repo="openadmet/cyp-challenge-train-test",
            name="cyp-challenge-TRAIN_inhibition.csv",
            subdir="cyp",
            smiles_column="SMILES",
            id_column="Molecule_Name",
            license="apache-2.0",
            description=(
                "Fitted dose-response pIC50 for CYP1A2, CYP2C9, CYP2D6 and CYP3A4, "
                "one row per compound, 4,905 compounds."
            ),
        ),
        Source(
            key="cyp_tdi",
            repo="openadmet/cyp-challenge-train-test",
            name="cyp-challenge-TRAIN_TDI.csv",
            subdir="cyp",
            smiles_column="SMILES",
            id_column="Molecule_Name",
            license="apache-2.0",
            description=(
                "pIC50 measured after a 30-minute preincubation with active enzyme, "
                "plus the CYP2D6 and CYP3A4 time-dependent-inhibition flags."
            ),
        ),
        Source(
            key="cyp_single",
            repo="openadmet/cyp-challenge-train-test",
            name="cyp-challenge-single-concentration-TRAIN.csv",
            subdir="cyp",
            smiles_column="SMILES",
            id_column="Molecule_Name",
            license="apache-2.0",
            description=(
                "Primary screen: every compound against all four enzymes at one "
                "concentration, reported as log2 fold change against control."
            ),
        ),
        Source(
            key="octant_inhibition",
            repo="openadmet/Octant_CYP_inhibition_reactivity_blog_release",
            name="inhibition.tsv",
            subdir="oct",
            smiles_column="standardized_smiles",
            id_column="ocnt_batch",
            license="cc-by-4.0",
            description=(
                "A second CYP3A4 inhibition platform, 1,340 compounds, with curve-level "
                "and plate-level quality flags."
            ),
        ),
        Source(
            key="pxr_train",
            repo="openadmet/pxr-challenge-train-test",
            name="pxr-challenge_TRAIN.csv",
            subdir="pxr",
            smiles_column="SMILES",
            id_column="Molecule Name",
            license="cc-by-4.0",
            description=(
                "Fitted pEC50 for activation of the pregnane X receptor, the receptor "
                "that drives CYP3A induction, 4,139 compounds."
            ),
        ),
        Source(
            key="pxr_counter",
            repo="openadmet/pxr-challenge-train-test",
            name="pxr-challenge_counter-assay_TRAIN.csv",
            subdir="pxr",
            smiles_column="SMILES",
            id_column="Molecule Name",
            license="cc-by-4.0",
            description=(
                "The same reporter plate without the PXR receptor, so a compound that "
                "scores here is hitting the readout rather than the target."
            ),
        ),
    ]
}

# Read but not joined into measured.csv: no CYP or PXR potency, or no structures.
CONTEXT_SOURCES: dict[str, Source] = {
    source.key: source
    for source in [
        Source(
            key="octant_reactivity",
            repo="openadmet/Octant_CYP_inhibition_reactivity_blog_release",
            name="reactivity.tsv",
            subdir="oct",
            smiles_column="",
            id_column="ocnt_batch",
            license="cc-by-4.0",
            description=(
                "Substrate depletion by CYP3A4 and CYP2J2. Keyed by batch identifier "
                "only, with no structure column, so it joins through inhibition.tsv."
            ),
        ),
        Source(
            key="octant_inhibition_wells",
            repo="openadmet/Octant_CYP_inhibition_reactivity_blog_release",
            name="inhibition_wells.tsv",
            subdir="oct",
            smiles_column="standardized_smiles",
            id_column="ocnt_batch",
            license="cc-by-4.0",
            description=(
                "Every well behind inhibition.tsv, including the control wells. This is "
                "where ketoconazole lives: 648 wells labelled Positive Control, and no "
                "fitted value anywhere."
            ),
        ),
        Source(
            key="erx_train",
            repo="openadmet/openadmet-expansionrx-challenge-train-data",
            name="expansion_data_train.csv",
            subdir="erx",
            smiles_column="SMILES",
            id_column="Molecule Name",
            license="cc-by-4.0",
            description=(
                "ExpansionRx ADMET series. The Hugging Face card gates downloads behind "
                "a form, but the resolve URL serves anonymously; nothing in it is an "
                "approved drug, so no row joins."
            ),
        ),
        Source(
            key="asap_admet",
            repo="openadmet/ASAP_Polaris_OpenADMET_challenge",
            name="ADMET.csv",
            subdir="asap",
            smiles_column="CXSMILES",
            id_column="Molecule Name",
            license="mit",
            description=(
                "ASAP antiviral series. Shares two structures with the CYP files and "
                "one with PXR, so there is no cross-dataset story."
            ),
        ),
    ]
}
