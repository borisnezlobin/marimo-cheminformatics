# Verified numbers

Every row below was recomputed by `verify.py` from the competition files and
the two bundled reference tables. The stated column is the value carried by
the research notes the notebook was planned from. The recomputed column is what
the data says today. A row marked **DISAGREES** means the notebook must use the
recomputed value.

Recomputed on 2026-09-19 with pandas 2.3.3.

| Claim | Stated | Recomputed | Source | Note |
| --- | --- | --- | --- | --- |
| measurements joined on the connectivity block alone | not stated | 57 rows on 12 drugs, out of 752 rows on 122 drugs | `measured.csv` |  |
| drugs where the published structure states a different arrangement at the same centres | not stated | cisapride, fluvastatin | `measured.csv` |  |
| drugs where the published structure states less stereochemistry than the drug has | not stated | clopidogrel, colchicine, curcumin, everolimus, rifampicin, tacrolimus, teriflunomide | `measured.csv` |  |
| drugs where the published structure states more stereochemistry than the reference | not stated | glimepiride, ibuprofen, lansoprazole | `measured.csv` |  |
| quinidine CYP2D6 pIC50 | 7.47 | 7.4663 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| quinine CYP2D6 pIC50 | 4.91 | 4.9071 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| quinidine / quinine potency ratio | 362 | 362.4295 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| quinidine and quinine share a connectivity block | yes | yes | `drugs.csv` |  |
| quinidine desipramine exposure increase | 8.0x | 8.0x (steady-state Cmin) | `Nuedexta (dextromethorphan hydrobromide and quinidine sulfate)` | quoted from the label, checked against openFDA |
| terbinafine CYP2D6 pIC50 | 6.41 | 6.4112 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| terbinafine desipramine exposure increase | 5.0x | 5.0x (AUC) | `Lamisil (terbinafine hydrochloride)` | quoted from the label, checked against openFDA |
| darifenacin CYP2D6 pIC50 | 6.67 | 6.6733 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| darifenacin desipramine exposure increase | 3.6x | 3.6x (AUC) | `Enablex (darifenacin extended-release tablets)` | quoted from the label, checked against openFDA |
| duloxetine CYP2D6 pIC50 | 5.29 | 5.2872 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| duloxetine desipramine exposure increase | 3.0x | 3.0x (AUC) | `Cymbalta (duloxetine delayed-release capsules)` | quoted from the label, checked against openFDA |
| escitalopram CYP2D6 pIC50 | 4.37 | 4.3728 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| escitalopram desipramine exposure increase | 2.0x | 2.0x (AUC) | `Lexapro (escitalopram oxalate)` | quoted from the label, checked against openFDA |
| Pearson r, pIC50 against log10(AUC fold) | 0.932 | 0.9321 | `clinical_auc.csv + cyp-challenge-TRAIN_inhibition.csv` |  |
| R-squared of that fit | 0.869 | 0.8689 | `clinical_auc.csv + cyp-challenge-TRAIN_inhibition.csv` |  |
| leave-one-out median absolute error, log10 units | 0.061 | 0.0609 | `clinical_auc.csv + cyp-challenge-TRAIN_inhibition.csv` |  |
| the same error as a fold | 1.15 | 1.1505 | `clinical_auc.csv + cyp-challenge-TRAIN_inhibition.csv` |  |
| leave-one-out worst case | 1.56-fold (darifenacin) | 1.56-fold (darifenacin) | `clinical_auc.csv + cyp-challenge-TRAIN_inhibition.csv` |  |
| voriconazole CYP3A4 pIC50 | 3.8 | 3.8008 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| isavuconazole CYP3A4 pIC50 | 6.24 | 6.2409 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| FDA class, voriconazole on CYP3A | strong | strong | `fda_roles.csv` |  |
| FDA class, isavuconazole on CYP3A | moderate | moderate | `fda_roles.csv` |  |
| weakest FDA-listed CYP3A inhibitor with a fitted curve | voriconazole | voriconazole (3.80) | `cyp-challenge-TRAIN_inhibition.csv` |  |
| most potent CYP3A4 inhibitor among matched named drugs | isavuconazole | isavuconazole (6.24) | `cyp-challenge-TRAIN_inhibition.csv` |  |
| CYP1A2 inhibitors carrying a fitted curve | not stated | methoxsalen moderate 6.69; mexiletine moderate 5.82 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| CYP2D6 inhibitors carrying a fitted curve | not stated | quinidine strong 7.47; cinacalcet moderate 7.24; terbinafine strong 6.41; paroxetine strong 5.79; duloxetine moderate 5.29; fluvoxamine weak 5.01; sertraline weak 4.98; mirabegron moderate 4.62; celecoxib weak 4.41; escitalopram weak 4.37 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| CYP3A4 inhibitors carrying a fitted curve | not stated | isavuconazole moderate 6.24; nefazodone strong 5.50; ivacaftor weak 5.42; voriconazole strong 3.80 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| CYP2D6 concordance, strong/moderate ranked above weak | 0.92 | 0.9167 | `fda_roles.csv + cyp-challenge-TRAIN_inhibition.csv` | 6 strong or moderate against 4 weak, 24 pairs |
| CYP3A concordance, strong/moderate ranked above weak **DISAGREES** | 0.63 | 0.6667 | `fda_roles.csv + cyp-challenge-TRAIN_inhibition.csv` | 3 strong or moderate against 1 weak, 3 pairs |
| CYP1A2 concordance (context, not a headline) | not stated | no pairs | `fda_roles.csv + cyp-challenge-TRAIN_inhibition.csv` | 2 strong or moderate against 0 weak |
| CYP2C9 concordance (context, not a headline) | not stated | no pairs | `fda_roles.csv + cyp-challenge-TRAIN_inhibition.csv` | 0 strong or moderate against 0 weak |
| CYP1A2: share of fitted curves at pIC50 >= 5 | 58.6 | 58.5694 | `cyp-challenge-TRAIN_inhibition.csv` | n = 1412 fitted curves |
| CYP2D6: share of fitted curves at pIC50 >= 5 | 36.6 | 36.5707 | `cyp-challenge-TRAIN_inhibition.csv` | n = 1493 fitted curves |
| CYP2C9: share of fitted curves at pIC50 >= 5 | 28.0 | 28.0156 | `cyp-challenge-TRAIN_inhibition.csv` | n = 1285 fitted curves |
| CYP3A4: share of fitted curves at pIC50 >= 5 | 20.6 | 20.5996 | `cyp-challenge-TRAIN_inhibition.csv` | n = 2335 fitted curves |
| CYP3A4: share of screened compounds inhibited at least 50% | 66.5 | 66.5219 | `cyp-challenge-single-concentration-TRAIN.csv` | n = 4376 of 4376 compounds screened |
| CYP2C9: share of screened compounds inhibited at least 50% | 33.2 | 33.181 | `cyp-challenge-single-concentration-TRAIN.csv` | n = 4376 of 4376 compounds screened |
| CYP1A2: share of screened compounds inhibited at least 50% | 29.9 | 29.8675 | `cyp-challenge-single-concentration-TRAIN.csv` | n = 4376 of 4376 compounds screened |
| CYP2D6: share of screened compounds inhibited at least 50% | 27.4 | 27.3766 | `cyp-challenge-single-concentration-TRAIN.csv` | n = 4376 of 4376 compounds screened |
| FDA assertions in total | 285 | 285 | `fda_roles.csv` |  |
| FDA inhibitor assertions with a fitted pIC50 on the same enzyme **DISAGREES** | 18 | 16 | `fda_roles.csv + cyp-challenge-TRAIN_inhibition.csv` | counting only the CYP challenge dose-response file |
| the same count with the Octant CYP3A4 file allowed in | not stated | 18 | `fda_roles.csv + measured.csv` | the Octant platform adds CYP3A4 curves the challenge file lacks |
| FDA inhibitor assertions reachable through the screen instead **DISAGREES** | 31 | 32 | `fda_roles.csv + measured.csv` |  |
| FDA assertions of any role with a fitted value on the same enzyme | not stated | 32 | `fda_roles.csv + measured.csv` |  |
| FDA assertions of any role with any measurement on the same enzyme | not stated | 59 | `fda_roles.csv + measured.csv` |  |
| levothyroxine CYP2C9 pIC50 | 6.34 | 6.3429 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| its rank among drugs.csv drugs with a fitted CYP2C9 curve | 1st of 270 approved drugs (research note, ChEMBL index) | 1 of 20 | `cyp-challenge-TRAIN_inhibition.csv` | the two universes differ; see the note below the table |
| FDA roles listed for levothyroxine | none | none | `fda_roles.csv` |  |
| runner-up on CYP2C9 | dabigatran etexilate 5.93 | dabigatran_etexilate 5.93 | `cyp-challenge-TRAIN_inhibition.csv` |  |
| approved drugs matched in the CYP dose-response file on a full key | 270 | 270 | `cyp-challenge-TRAIN_inhibition.csv` | ChEMBL phase-4 index, the universe the research note used |
| strongest CYP2C9 inhibitor among those approved drugs | levothyroxine | levothyroxine 6.34 | `cyp-challenge-TRAIN_inhibition.csv` | 66 of them carry a CYP2C9 curve |
| ketoconazole has a fitted CYP3A4 pIC50 | no | no | `cyp-challenge-TRAIN_inhibition.csv` |  |
| ketoconazole has a fitted PXR pEC50 | no | no | `pxr-challenge_TRAIN.csv` |  |
| ketoconazole in any of the five potency files | absent | absent from all five | `all five potency files` |  |
| ketoconazole well count in the Octant well-level file | 648 | 648 | `inhibition_wells.tsv` | compound_class: Positive Control |

## Disagreements

- **CYP3A concordance, strong/moderate ranked above weak**: the notes say 0.63, the data says 0.6667. 3 strong or moderate against 1 weak, 3 pairs
  Only four FDA-listed CYP3A inhibitors carry a fitted curve in the challenge file, and only one of them is classed weak, so there are three pairs to order and each one moves the figure by a third. The research note reported 0.625 from a six-drug set built through a ChEMBL name index rather than through this roster. Write the count beside the fraction wherever the notebook states it, because two of three is not a rate anyone should round to a percentage.
- **FDA inhibitor assertions with a fitted pIC50 on the same enzyme**: the notes say 18, the data says 16. counting only the CYP challenge dose-response file
  Sixteen is the count inside the CYP challenge dose-response file alone. Eighteen is right once the Octant CYP3A4 file is allowed to supply a curve too, which is the row directly below. The notebook should name the file it means.
- **FDA inhibitor assertions reachable through the screen instead**: the notes say 31, the data says 32. 
  One more than the note recorded. All 32 are full-key matches, so the extra assertion is not a loosened join. The earlier run reached the screen through a ChEMBL name index that resolved 194 of FDA's 205 drugs, where this build resolves every FDA drug that is a single structure, so the two runs are counting slightly different rosters against the same file. Use 32.

## Two things the table cannot say in a cell

The quinidine row of `clinical_auc.csv` is a steady-state trough concentration
from the dextromethorphan-plus-quinidine combination product, not an AUC after a
single desipramine dose. It is the least directly comparable of the five human
studies, and the notebook should say so where it plots the point.

Levothyroxine's rank depends on which drugs you are ranking it among. The
research note ranked it against a ChEMBL index of approved drugs, and this build
ranks it against the 289 drugs in `drugs.csv`. Both rows appear above so the
notebook can quote whichever universe it names.

## Connectivity-only matches

Twelve drugs are found in the competition files only by their connectivity
block, because the published structure and the reference structure disagree
about stereochemistry. Ten of the twelve disagree by omission: the published
SMILES leaves an alkene geometry or a stereocentre undeclared where the drug
has one, or declares a single enantiomer where the marketed drug is racemic.
Cisapride and fluvastatin are the two that differ in kind, stating the same
number of stereo elements in a different arrangement. Every row in
`measured.csv` carries a `stereo_note` saying which case it is, and the
notebook should draw a connectivity match differently from a full-key match
wherever it shows one.
