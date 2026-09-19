"""Which drugs the notebook needs to know about, and what a reader might call them.

Three groups go into drugs.csv. The first is every drug named in FDA's table of
examples of drugs that interact with CYP enzymes, read straight out of that
table so the roster cannot drift from it. The second is the set of drugs the
notebook names in its own argument. The third is the medicine-cabinet list: the
things people actually have at home, which is what the cabinet widget is filled
from.

Aliases are lowercase search terms. They exist so that a reader who types
"Advil" reaches ibuprofen, so every everyday drug carries the brand names it is
sold under in the United States. A brand name here is a search key, not a claim
about who manufactures what.
"""

import re

import pandas as pd

# Drugs the notebook argues about by name, beyond whatever the FDA table holds.
NOTEBOOK_DRUGS = [
    "quinidine", "quinine", "voriconazole", "isavuconazole", "levothyroxine",
    "cisapride", "rifampicin", "terbinafine", "darifenacin", "duloxetine",
    "escitalopram", "desipramine", "bupropion", "paroxetine", "fluvoxamine",
    "sertraline", "ketoconazole", "cinacalcet", "bromhexine", "nifedipine",
    "methoxsalen", "clioquinol", "nisoldipine", "viloxazine", "loratadine",
    "diethylstilbestrol", "dabigatran etexilate", "candesartan cilexetil",
    "felodipine", "rupatadine", "nimodipine", "meclizine", "nefazodone",
    "mifepristone", "ritonavir", "mycophenolic acid", "mycophenolate mofetil",
    "adefovir dipivoxil", "tenofovir alafenamide", "doxorubicin", "atazanavir",
    "dipyridamole", "pazopanib", "perphenazine", "sunitinib", "ranolazine",
    "terfenadine", "mibefradil", "astemizole", "erythromycin", "clarithromycin",
    "bosentan", "efavirenz", "mitotane", "apalutamide", "midazolam",
    "alfentanil", "dextromethorphan",
]

# The medicine cabinet: common prescriptions and over-the-counter drugs, with
# the brand names they are sold under. drug_id is the key on the left.
CABINET = {
    "ibuprofen": ["advil", "motrin", "nurofen"],
    "acetaminophen": ["tylenol", "paracetamol", "panadol"],
    "aspirin": ["bayer aspirin", "acetylsalicylic acid"],
    "naproxen": ["aleve", "naprosyn"],
    "atorvastatin": ["lipitor"],
    "simvastatin": ["zocor"],
    "rosuvastatin": ["crestor"],
    "fluoxetine": ["prozac", "sarafem"],
    "sertraline": ["zoloft"],
    "escitalopram": ["lexapro", "cipralex"],
    "citalopram": ["celexa"],
    "duloxetine": ["cymbalta"],
    "venlafaxine": ["effexor"],
    "bupropion": ["wellbutrin", "zyban"],
    "trazodone": ["desyrel"],
    "omeprazole": ["prilosec", "losec"],
    "esomeprazole": ["nexium"],
    "pantoprazole": ["protonix"],
    "famotidine": ["pepcid"],
    "alprazolam": ["xanax"],
    "lorazepam": ["ativan"],
    "clonazepam": ["klonopin"],
    "zolpidem": ["ambien", "stilnox"],
    "clopidogrel": ["plavix"],
    "warfarin": ["coumadin", "jantoven"],
    "apixaban": ["eliquis"],
    "rivaroxaban": ["xarelto"],
    "levothyroxine": ["synthroid", "levoxyl", "euthyrox"],
    "amlodipine": ["norvasc"],
    "lisinopril": ["zestril", "prinivil"],
    "losartan": ["cozaar"],
    "metoprolol": ["lopressor", "toprol"],
    "hydrochlorothiazide": ["microzide", "hydrodiuril"],
    "metformin": ["glucophage", "fortamet"],
    "gabapentin": ["neurontin", "gralise"],
    "pregabalin": ["lyrica"],
    "montelukast": ["singulair"],
    "albuterol": ["ventolin", "proair", "salbutamol"],
    "fluticasone": ["flonase", "flovent"],
    "cetirizine": ["zyrtec"],
    "loratadine": ["claritin"],
    "diphenhydramine": ["benadryl"],
    "sildenafil": ["viagra", "revatio"],
    "tadalafil": ["cialis"],
    "prednisone": ["deltasone", "rayos"],
    "triamcinolone acetonide": ["kenalog", "nasacort"],
    "oxycodone": ["oxycontin", "percocet", "roxicodone"],
    "tramadol": ["ultram", "conzip"],
    "ondansetron": ["zofran"],
    "ciprofloxacin": ["cipro"],
    "azithromycin": ["zithromax", "z-pak"],
    "amoxicillin": ["amoxil"],
    "clarithromycin": ["biaxin"],
    "fluconazole": ["diflucan"],
    "terbinafine": ["lamisil"],
    "diltiazem": ["cardizem", "tiazac"],
    "verapamil": ["calan", "verelan"],
    "carbamazepine": ["tegretol"],
    "phenytoin": ["dilantin"],
    "tamsulosin": ["flomax"],
    "finasteride": ["propecia", "proscar"],
    "tacrolimus": ["prograf"],
    "cyclosporine": ["neoral", "sandimmune", "ciclosporin"],
    "quetiapine": ["seroquel"],
    "aripiprazole": ["abilify"],
    "methylphenidate": ["ritalin", "concerta"],
    "caffeine": ["no-doz"],
    "melatonin": [],
    "cisapride": ["propulsid"],
    "quinidine": ["nuedexta component"],
    "quinine": ["qualaquin", "tonic water"],
    "rifampicin": ["rifampin", "rifadin", "rimactane"],
    "voriconazole": ["vfend"],
    "isavuconazole": ["cresemba", "isavuconazonium"],
    "darifenacin": ["enablex"],
    "desipramine": ["norpramin"],
    "ketoconazole": ["nizoral"],
    "paroxetine": ["paxil"],
    "fluvoxamine": ["luvox"],
    "cinacalcet": ["sensipar"],
    "nefazodone": ["serzone"],
    "ritonavir": ["norvir"],
    "mifepristone": ["mifeprex", "korlym"],
}

# FDA's table names some entries that are not one molecule: fixed-dose
# combinations, a beverage, a herbal extract, a habit. They keep their rows in
# fda_roles.csv, because FDA's assertion about them is real, and they get no row
# in drugs.csv, because there is no single parent structure to give them.
NOT_A_SINGLE_STRUCTURE = {
    "atazanavir and ritonavir",
    "elvitegravir and ritonavir",
    "grapefruit juice",
    "indinavir and ritonavir",
    "lopinavir and ritonavir",
    "lumacaftor and ivacaftor",
    "oral contraceptives",
    "paritaprevir and ritonavir and (ombitasvir and/or dasabuvir)",
    "peginterferon alpha-2a",
    "saquinavir and ritonavir",
    "sofosbuvir and velpatasvir and voxilaprevir",
    "st. john’s wort",
    "tipranavir and ritonavir",
    "tobacco (smoking)",
}

# One drug, two accepted spellings. The left name folds into the right one so
# the roster does not carry the same structure twice.
SYNONYMS = {"rifampin": "rifampicin"}


def strip_footnotes(raw: str) -> str:
    """FDA glues footnote markers onto drug names: 'fluvoxamine8', 'ritonavir14,15'."""
    return re.sub(r"[\d,\s]+$", "", str(raw).strip()).strip().lower()


def drug_id(name: str) -> str:
    """Lowercase, spaceless key. 'Mycophenolate mofetil' -> 'mycophenolate_mofetil'."""
    slug = re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower())
    return slug.strip("_")


def fda_drug_names(fda_table_path: str) -> list[str]:
    """Every distinct drug named in FDA's table, footnote digits removed."""
    table = pd.read_csv(fda_table_path)
    names = []
    for raw in table["Drug or Other Substance"].dropna():
        name = strip_footnotes(raw)
        if name:
            names.append(name)
    return sorted(dict.fromkeys(names))


def roster(fda_table_path: str) -> dict[str, dict]:
    """drug_id -> {display_name, query, aliases, groups}. One entry per distinct drug."""
    entries: dict[str, dict] = {}

    def add(name: str, group: str, aliases: list[str] | None = None):
        key = drug_id(name)
        if key not in entries:
            entries[key] = {
                "display_name": name,
                "query": name,
                "aliases": set(),
                "groups": set(),
            }
        entries[key]["aliases"].update(a.lower() for a in (aliases or []))
        entries[key]["aliases"].add(name.lower())
        entries[key]["groups"].add(group)

    for name in fda_drug_names(fda_table_path):
        if name in NOT_A_SINGLE_STRUCTURE:
            continue
        canonical = SYNONYMS.get(name, name)
        add(canonical, "fda_table", [name] if canonical != name else None)
    for name in NOTEBOOK_DRUGS:
        add(name, "notebook")
    for name, aliases in CABINET.items():
        add(name, "cabinet", aliases)
    return entries
