# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo==0.24.2",
#     "anywidget==0.11.0",
#     "traitlets==5.14.3",
#     "pandas==2.2.3",
#     "numpy==2.1.3",
#     "altair==5.5.0",
# ]
# ///

import marimo

__generated_with = "0.24.2"
app = marimo.App(
    width="medium",
    app_title="Does the plate predict the clinic?",
    css_file="theme.css",
)


@app.cell(hide_code=True)
def _():
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import numpy as np
    import pandas as pd

    from widgets import Cabinet, Gauntlet, Guess, StereoEditor, load_game

    DATA = Path(__file__).parent / "data"

    drugs = pd.read_csv(DATA / "drugs.csv")
    fda_roles = pd.read_csv(DATA / "fda_roles.csv")
    clinical_auc = pd.read_csv(DATA / "clinical_auc.csv")
    measured = pd.read_csv(DATA / "measured.csv")
    isoform_summary = pd.read_csv(DATA / "isoform_summary.csv")
    clearance_summary = pd.read_csv(DATA / "clearance_summary.csv")

    name_of = dict(zip(drugs.drug_id, drugs.display_name))
    return (
        Cabinet,
        DATA,
        Gauntlet,
        Guess,
        StereoEditor,
        alt,
        clearance_summary,
        clinical_auc,
        drugs,
        fda_roles,
        isoform_summary,
        measured,
        mo,
        name_of,
        np,
        pd,
    )


@app.cell(hide_code=True)
def _(DATA, mo, pd):
    def plain_table(rows, **kwargs):
        """One table style for the whole notebook. Rows arrive as dictionaries
        rather than as a DataFrame so that no index column is drawn."""
        records = rows.to_dict("records") if isinstance(rows, pd.DataFrame) else rows
        return mo.ui.table(
            records,
            selection=None,
            show_column_summaries=False,
            show_data_types=False,
            show_download=False,
            show_search=False,
            pagination=False,
            **kwargs,
        )

    def structure(drug_id: str, caption: str):
        """A molecule drawing, rendered at build time by build/build_structures.py
        so the notebook needs no chemistry toolkit to run."""
        svg = (DATA / "structures" / f"{drug_id}.svg").read_text()
        return mo.vstack(
            [mo.Html(svg), mo.md(f"<small>{caption}</small>")],
            align="center",
            gap=0.25,
        )

    def aside(title: str, body: str):
        """The long explanation, folded away. The page reads as pictures with short
        captions, and anyone who wants the full account opens one of these."""
        return mo.accordion({title: mo.md(body)})

    return aside, plain_table, structure


@app.cell(hide_code=True)
def _(
    Cabinet,
    DATA,
    Gauntlet,
    Guess,
    StereoEditor,
    catalog_records,
    guess_rounds,
    load_game,
    mo,
    pair_records,
    stereo_readout,
):
    # All four widgets are constructed together, with no slow work between them.
    # Marimo issue #10494 loses a widget's model on a cold boot when their
    # creation is spaced out by roughly half a second or more, which is exactly
    # what interleaving these with pandas work used to do.
    gauntlet_widget = Gauntlet(game=load_game(DATA / "game.json"))
    cabinet_widget = Cabinet(
        catalog=catalog_records,
        pair_index=pair_records,
        shelf=["simvastatin", "clarithromycin", "ibuprofen"],
    )
    guess_widget = Guess(rounds=guess_rounds)
    stereo_widget = StereoEditor(readout=stereo_readout("quinine"))

    gauntlet = mo.ui.anywidget(gauntlet_widget)
    cabinet = mo.ui.anywidget(cabinet_widget)
    guess = mo.ui.anywidget(guess_widget)
    stereo = mo.ui.anywidget(stereo_widget)
    return (
        cabinet,
        cabinet_widget,
        gauntlet,
        gauntlet_widget,
        guess,
        guess_widget,
        stereo,
        stereo_widget,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Does the plate predict the clinic?

    A robot drips a drug into a plastic well holding a human liver enzyme and measures
    how much the enzyme slows down. That measurement is cheap and there are thousands
    of them. The measurement anyone actually cares about, how much a drug piles up
    inside a person, needs a clinical study and exists for a few hundred drugs.

    Using OpenADMET's data, this notebook asks whether the cheap measurement predicts
    the expensive one. For one enzyme it does, to within about fifteen percent. For
    another it puts two antifungal drugs in the wrong order.

    *Written with AI assistance. Claude helped with the code and the drafting. Every
    number was recomputed from the source files and checked against the cited labels.*
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Send a compound through a body""")
    return








@app.cell(hide_code=True)
def _(gauntlet):
    gauntlet
    return


@app.cell(hide_code=True)
def _(aside):
    aside(
        "What the enzyme is, and why blocking it hurts people",
        """
    A drug that enters your blood has to leave again. For most small-molecule drugs
    that begins in the liver, where a family of enzymes modifies the drug into
    something the kidneys can flush away. The family is called cytochrome P450,
    written CYP. Humans have 57 of them, about a dozen do real work on medicines, and
    between them that dozen handles 70 to 80 percent of all drugs in clinical use.
    CYP3A4 alone handles more than 30 percent, which makes it the busiest disposal
    route in human pharmacology.

    A drug that blocks one of these enzymes need not be harmful by itself. It does its
    damage through everything else you take. Those other drugs keep arriving with each
    dose and stop departing on schedule, so their concentration climbs until a
    medicine somebody has taken safely for years is delivering far more than its label
    says.

    Felodipine shows the scale of it. Your gut absorbs essentially all of a felodipine
    tablet, but only about 15 percent reaches your bloodstream, because CYP3A4
    destroys the rest on the first pass through the liver. Block that enzyme and much
    more of the same tablet survives the trip. Nobody changed the pill, and the
    patient is now receiving several times the dose.
    """,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Put your own medicines on a shelf""")
    return


@app.cell(hide_code=True)
def _(cabinet):
    cabinet
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    The shelf opens with a statin, an ordinary antibiotic and a painkiller. Two of the
    three meet at the same enzyme. Clear it and type in your own medicines, brand
    names included.
    """
    )
    return


@app.cell(hide_code=True)
def _(drugs, fda_roles, measured, name_of):
    ROLE_SENTENCE = {
        ("inhibitor", "strong"): "Strongly blocks {enzyme}.",
        ("inhibitor", "moderate"): "Moderately blocks {enzyme}.",
        ("inhibitor", "weak"): "Weakly blocks {enzyme}.",
        ("inducer", "strong"): "Strongly speeds up {enzyme}.",
        ("inducer", "moderate"): "Moderately speeds up {enzyme}.",
        ("inducer", "weak"): "Weakly speeds up {enzyme}.",
        ("substrate", "sensitive"): "Cleared by {enzyme}, and sensitive to it.",
        ("substrate", "moderately_sensitive"): "Cleared by {enzyme}.",
    }

    FOLD_BANDS = {
        "strong": (5.0, 20.0),
        "moderate": (2.0, 5.0),
        "weak": (1.25, 2.0),
    }

    _direct = measured[measured.endpoint == "pIC50_direct"]
    POTENCY = {
        (row.drug_id, row.enzyme): float(row.value) for row in _direct.itertuples()
    }
    ROLES_BY_DRUG = {
        drug_id: frame for drug_id, frame in fda_roles.groupby("drug_id")
    }

    def fitted_potency(drug_id: str, enzyme: str) -> float | None:
        """The fitted pIC50 for one drug against one enzyme, or None.

        FDA writes CYP3A for the pair CYP3A4 and CYP3A5 while the assay measures
        CYP3A4 alone, so the two labels are matched here deliberately.
        """
        assay_enzyme = "CYP3A4" if enzyme == "CYP3A" else enzyme
        return POTENCY.get((drug_id, assay_enzyme))

    def evidence_state(drug_id: str) -> str:
        roles = ROLES_BY_DRUG.get(drug_id)
        if roles is None:
            return "unknown"
        measured_here = any(
            fitted_potency(drug_id, enzyme) is not None for enzyme in roles.enzyme
        )
        return "measured" if measured_here else "documented"

    def sublabel(drug_id: str) -> str:
        roles = ROLES_BY_DRUG.get(drug_id)
        if roles is None:
            return "No enzyme role on record with FDA."
        first = roles.iloc[0]
        template = ROLE_SENTENCE.get((first.role, first.strength))
        return (
            template.format(enzyme=first.enzyme)
            if template
            else f"Interacts with {first.enzyme}."
        )

    catalog_records = [
        {
            "drug_id": row.drug_id,
            "display_name": row.display_name.capitalize(),
            "aliases": sorted(set(str(row.aliases).split("|"))),
            "sublabel": sublabel(row.drug_id),
            "state": evidence_state(row.drug_id),
        }
        for row in drugs.itertuples()
    ]

    def build_pairs() -> list[dict]:
        """Every perpetrator and victim pair among drugs we hold a structure for.

        FDA's table lists a few combination products, such as elvitegravir with
        ritonavir, which have no single parent structure and so no row in drugs.csv.
        Those are skipped rather than guessed at.
        """
        roles = fda_roles[fda_roles.drug_id.isin(set(drugs.drug_id))]
        perpetrators = roles[roles.role.isin(["inhibitor", "inducer"])]
        victims = roles[roles.role == "substrate"]
        records = []
        for perp in perpetrators.itertuples():
            low, high = FOLD_BANDS.get(perp.strength, (1.0, 1.25))
            potency = fitted_potency(perp.drug_id, perp.enzyme)
            for victim in victims[victims.enzyme == perp.enzyme].itertuples():
                if victim.drug_id == perp.drug_id:
                    continue
                records.append(
                    {
                        "perpetrator": perp.drug_id,
                        "victim": victim.drug_id,
                        "enzyme": perp.enzyme,
                        "band": f"{perp.strength.replace('_', ' ')} {perp.role}",
                        "fold_low": low,
                        "fold_high": high,
                        "measured_pic50": potency,
                        "note": (
                            f"Halves {perp.enzyme} activity in a plate at pIC50 "
                            f"{potency:.2f}."
                            if potency is not None
                            else f"No laboratory potency against {perp.enzyme} here."
                        ),
                    }
                )
        return records

    pair_records = build_pairs()
    return (
        FOLD_BANDS,
        ROLE_SENTENCE,
        build_pairs,
        catalog_records,
        evidence_state,
        fitted_potency,
        pair_records,
        sublabel,
    )


@app.cell(hide_code=True)
def _(aside):
    aside(
        "The warning that was printed, and did not work",
        """
    In 1998 the makers of cisapride, a heartburn drug, wrote to doctors. The letter
    named nine medicines that raise cisapride's concentration in the blood by blocking
    CYP3A4, among them clarithromycin, erythromycin, ketoconazole and ritonavir, and
    it said some of the resulting events had been fatal.

    FDA scientists later reviewed their own adverse event database and counted 341
    patients who suffered serious heart rhythm disturbances while taking cisapride.
    Eighty of them died, and most were taking something else that blocked the enzyme.
    The drug was withdrawn from the United States market in 2000.

    The warning existed, the nine drugs were named, and eighty people died anyway.
    That is the argument for catching this in a laboratory rather than in a footnote,
    and whether a laboratory can catch it is what the rest of this notebook tests.
    """,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Guess what a plate reading does to a person""")
    return


@app.cell(hide_code=True)
def _(guess):
    guess
    return


@app.cell(hide_code=True)
def _(clinical_auc, fitted_potency, np):
    def build_rounds() -> list[dict]:
        """One round per drug. The line the reader competes against is refitted
        without the drug it is predicting, so it never sees its own answer."""
        frame = clinical_auc.assign(
            pic50=[
                fitted_potency(row.drug_id, row.enzyme)
                for row in clinical_auc.itertuples()
            ]
        )
        frame = frame.assign(log_fold=np.log10(frame.auc_fold))
        rounds = []
        for held_out in frame.index:
            rest = frame.drop(index=held_out)
            slope, intercept = np.polyfit(rest.pic50, rest.log_fold, 1)
            row = frame.loc[held_out]
            rounds.append(
                {
                    "drug": row.drug_id.capitalize(),
                    "pic50": round(float(row.pic50), 2),
                    "truth_fold": float(row.auc_fold),
                    "model_fold": round(
                        float(10 ** (slope * row.pic50 + intercept)), 2
                    ),
                    "blurb": f"Measured against {row.victim}, reported as {row.measure}.",
                }
            )
        return sorted(rounds, key=lambda entry: entry["pic50"])

    guess_rounds = build_rounds()
    return build_rounds, guess_rounds


@app.cell(hide_code=True)
def _(alt, clinical, mo):
    def parity_chart():
        base = alt.Chart(clinical)
        points = base.mark_circle(size=190, opacity=0.9).encode(
            x=alt.X(
                "pIC50:Q",
                scale=alt.Scale(domain=[4.0, 7.8]),
                title="Potency measured in a plate (pIC50)",
            ),
            y=alt.Y(
                "auc_fold:Q",
                scale=alt.Scale(type="log", domain=[1.5, 10]),
                title="Exposure increase measured in people (fold)",
            ),
            tooltip=["Drug", "Measured potency (pIC50)", "Human exposure increase"],
        )
        labels = base.mark_text(align="left", dx=12, dy=-8, fontSize=13).encode(
            x="pIC50:Q", y="auc_fold:Q", text="Drug:N"
        )
        line = (
            base.transform_regression("pIC50", "log_auc")
            .mark_line(strokeDash=[4, 4], opacity=0.55)
            .transform_calculate(auc_fold="pow(10, datum.log_auc)")
            .encode(x="pIC50:Q", y="auc_fold:Q")
        )
        return (points + labels + line).properties(height=320, width="container")

    mo.accordion(
        {
            "Show all five drugs on one plot, answers included": mo.ui.altair_chart(
                parity_chart()
            )
        }
    )
    return (parity_chart,)


@app.cell(hide_code=True)
def _(clinical_auc, fitted_potency, mo, np, pd):
    def clinical_frame() -> pd.DataFrame:
        rows = []
        for row in clinical_auc.itertuples():
            potency = fitted_potency(row.drug_id, row.enzyme)
            rows.append(
                {
                    "Drug": row.drug_id.capitalize(),
                    "Measured potency (pIC50)": potency,
                    "Human exposure increase": f"{row.auc_fold:g}-fold",
                    "auc_fold": row.auc_fold,
                    "log_auc": np.log10(row.auc_fold),
                    "pIC50": potency,
                }
            )
        return pd.DataFrame(rows).sort_values("pIC50", ascending=False)

    clinical = clinical_frame()

    def leave_one_out_errors(frame: pd.DataFrame) -> pd.Series:
        errors = {}
        for held_out in frame.index:
            rest = frame.drop(index=held_out)
            slope, intercept = np.polyfit(rest.pIC50, rest.log_auc, 1)
            predicted = slope * frame.loc[held_out, "pIC50"] + intercept
            errors[frame.loc[held_out, "Drug"]] = abs(
                predicted - frame.loc[held_out, "log_auc"]
            )
        return pd.Series(errors)

    loo = leave_one_out_errors(clinical)
    pearson_r = float(np.corrcoef(clinical.pIC50, clinical.log_auc)[0, 1])
    loo_median_fold = float(10 ** loo.median())
    loo_worst_fold = float(10 ** loo.max())
    loo_worst_drug = str(loo.idxmax())

    mo.md(
        f"""
    The plate reading and the human result move together with a correlation of
    {pearson_r:.2f}. A line fitted to four of the drugs predicts the fifth to within
    **{loo_median_fold:.2f}-fold**, and its worst miss, {loo_worst_drug.lower()}, is
    off by {loo_worst_fold:.2f}-fold.

    Five points can line up by luck, so this shows the two measurements describe the
    same physical event rather than establishing an accuracy.
    """
    )
    return (
        clinical,
        clinical_frame,
        leave_one_out_errors,
        loo,
        loo_median_fold,
        loo_worst_drug,
        loo_worst_fold,
        pearson_r,
    )


@app.cell(hide_code=True)
def _(aside):
    aside(
        "What each of the two numbers actually measures",
        """
    **The plate reading is called pIC50.** A lab puts the enzyme in a well with
    something it normally breaks down, adds the test compound across a range of
    concentrations, and watches how fast the enzyme works. The concentration that
    halves the enzyme's speed is the IC50. Those concentrations span an enormous
    range, so they are reported as a negative logarithm, written pIC50, which behaves
    like the pH scale. Each whole number is a factor of ten, and higher means more
    potent, because a more potent compound needs less of itself to do the same damage.
    A pIC50 of 5 means ten micromolar, 6 means one micromolar, and 7 means a tenth of
    a micromolar.

    **The human number is an exposure ratio.** Volunteers take the victim drug alone,
    then take it again alongside the blocker, and researchers follow its concentration
    in blood for hours afterwards. The total exposure over that period is the area
    under the concentration curve. If the blocker makes that area five times larger,
    the patient received five times the exposure from the same prescription. FDA sorts
    blockers on exactly this measure: strong means five-fold or more, moderate means
    two to five, and weak means 1.25 to two.

    All five studies used the same victim drug, desipramine, which matters because a
    blocker looks stronger against a victim that depends entirely on the blocked
    enzyme. One caveat belongs on quinidine: its human figure is a steady-state trough
    concentration from a combination product rather than an area under the curve,
    which makes it the least directly comparable of the five.
    """,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Two antifungals, ranked backwards""")
    return


@app.cell(hide_code=True)
def _(azole_values, mo, structure):
    mo.hstack(
        [
            structure(
                "voriconazole",
                "Voriconazole. FDA calls it strong, meaning it raises exposure "
                f"five-fold or more in people. This plate reads "
                f"{azole_values['voriconazole']:.2f}.",
            ),
            structure(
                "isavuconazole",
                "Isavuconazole. FDA calls it moderate, meaning two to five-fold. "
                f"This plate reads {azole_values['isavuconazole']:.2f}.",
            ),
        ],
        widths="equal",
        gap=2,
    )
    return


@app.cell(hide_code=True)
def _(concordance, fitted_potency, mo):
    azole_values = {
        "voriconazole": fitted_potency("voriconazole", "CYP3A"),
        "isavuconazole": fitted_potency("isavuconazole", "CYP3A"),
    }
    mo.md(
        f"""
    The drug FDA calls strong reads as the weakest CYP3A blocker in the file, and the
    drug FDA calls moderate reads as the strongest.

    For CYP2D6 this comparison can be run {concordance['CYP2D6']['n_pairs']} times and
    the plate gets {concordance['CYP2D6']['share']:.0%} of them right. For CYP3A it
    can be run {concordance['CYP3A']['n_pairs']} times in total, because only
    {concordance['CYP3A']['n_drugs']} drugs have both a published class and a measured
    potency, which is too few to call a success rate either way.
    """
    )
    return (azole_values,)


@app.cell(hide_code=True)
def _(fda_roles, fitted_potency):
    def concordance_for(enzyme: str) -> dict:
        """How often the plate ranks a clinically stronger blocker above a weaker
        one, counting every strong-or-moderate against weak pair."""
        rows = fda_roles[(fda_roles.enzyme == enzyme) & (fda_roles.role == "inhibitor")]
        scored = [
            (row.strength, fitted_potency(row.drug_id, enzyme))
            for row in rows.itertuples()
        ]
        scored = [(strength, value) for strength, value in scored if value is not None]
        stronger = [value for strength, value in scored if strength in ("strong", "moderate")]
        weaker = [value for strength, value in scored if strength == "weak"]
        comparisons = [(a, b) for a in stronger for b in weaker]
        correct = sum(1 for a, b in comparisons if a > b)
        return {
            "n_drugs": len(scored),
            "n_pairs": len(comparisons),
            "share": correct / len(comparisons) if comparisons else float("nan"),
        }

    concordance = {enzyme: concordance_for(enzyme) for enzyme in ["CYP2D6", "CYP3A"]}
    return concordance, concordance_for


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## One dataset, two opposite answers about the same enzyme""")
    return


@app.cell(hide_code=True)
def _(alt, isoform_summary, mo, pd):
    def selection_chart():
        long = pd.concat(
            [
                isoform_summary.assign(
                    measurement="Among compounds given a full curve",
                    share=isoform_summary.share_potent,
                ),
                isoform_summary.assign(
                    measurement="Among every compound screened once",
                    share=isoform_summary.share_hit,
                ),
            ]
        )
        return (
            alt.Chart(long)
            .mark_bar(cornerRadius=2)
            .encode(
                y=alt.Y("enzyme:N", title=None),
                x=alt.X("share:Q", title="Compounds that block the enzyme (%)"),
                yOffset="measurement:N",
                color=alt.Color(
                    "measurement:N", title=None, legend=alt.Legend(orient="top")
                ),
                tooltip=["enzyme", "measurement", alt.Tooltip("share:Q", format=".1f")],
            )
            .properties(height=230, width="container")
        )

    mo.ui.altair_chart(selection_chart())
    return (selection_chart,)


@app.cell(hide_code=True)
def _(aside, isoform_summary, measured_overlap, mo):
    _f = isoform_summary.set_index("enzyme")
    mo.vstack(
        [
            mo.md(
                f"""
    A full curve is expensive, so the laboratory ran one only where a cheap screen had
    already flagged activity. Read the curves and CYP3A4 blocks
    {_f.loc['CYP3A4', 'share_potent']:.0f} percent of compounds, the lowest of the
    four enzymes. Read the screen, where all
    {_f.loc['CYP3A4', 'compounds_screened']:,.0f} compounds met every enzyme at the
    same concentration, and CYP3A4 blocks {_f.loc['CYP3A4', 'share_hit']:.0f} percent,
    the highest by a wide margin. Which compounds got measured decides the answer.
    """
            ),
            aside(
                "Two more reasons the CYP3A4 test is thin",
                f"""
    FDA's table makes {measured_overlap['total_assertions']} assertions of the form
    "this drug does this to this enzyme". Of those,
    {measured_overlap['inhibitor_with_fit']} are blocker assertions that also carry a
    fitted potency here, and that is the entire overlap available across all four
    enzymes.

    Ketoconazole, the most famous CYP3A4 blocker in medicine, is the compound this
    assay uses as its positive control. It appears in 648 wells of the Octant release
    and carries no fitted value of its own, so the dataset cannot rate the drug it is
    calibrated against.
    """,
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(fda_roles, fitted_potency):
    def overlap_counts() -> dict:
        inhibitors = fda_roles[fda_roles.role == "inhibitor"]
        with_fit = sum(
            1
            for row in inhibitors.itertuples()
            if fitted_potency(row.drug_id, row.enzyme) is not None
        )
        return {
            "total_assertions": len(fda_roles),
            "inhibitor_assertions": len(inhibitors),
            "inhibitor_with_fit": with_fit,
        }

    measured_overlap = overlap_counts()
    return measured_overlap, overlap_counts


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Flip two corners of a molecule""")
    return


@app.cell(hide_code=True)
def _(stereo):
    stereo
    return


@app.cell(hide_code=True)
def _(measured):
    def stereo_readout(drug_id: str) -> dict:
        rows = measured[
            (measured.drug_id == drug_id) & (measured.endpoint == "pIC50_direct")
        ]
        return {
            "title": drug_id.capitalize(),
            "lines": [
                "Treats malaria. The bitter taste in tonic water."
                if drug_id == "quinine"
                else "Steadies heart rhythm. FDA lists it as a strong CYP2D6 blocker.",
                f"Matched to {rows.source_id.iloc[0]} in the competition data."
                if not rows.empty
                else "No fitted curve in the competition data.",
            ],
            "measured": [
                {"enzyme": row.enzyme, "value": round(float(row.value), 2)}
                for row in rows.itertuples()
            ],
        }

    return (stereo_readout,)


@app.cell(hide_code=True)
def _(aside, fitted_potency, mo):
    _quinidine = fitted_potency("quinidine", "CYP2D6")
    _quinine = fitted_potency("quinine", "CYP2D6")
    mo.vstack(
        [
            mo.md(
                f"""
    Quinine and quinidine contain the same atoms joined in the same order. Two corners
    are built the other way round, and the measured potency moves by a factor of
    {10 ** (_quinidine - _quinine):.0f}, from {_quinine:.2f} to {_quinidine:.2f}.
    """
            ),
            aside(
                "Why a mirror image is a different drug",
                """
    A carbon atom bonded to four different groups can be assembled in two arrangements
    that are mirror images of each other, in the way your left and right hands are
    mirror images. Such an atom is called a stereocentre. Both versions contain
    identical atoms joined in an identical order, so any comparison that looks only at
    which atom connects to which treats them as the same molecule. An enzyme
    disagrees, because its active site is a three-dimensional pocket, and a left hand
    does not fit a right glove.

    Quinine treats malaria and gives tonic water its bitter taste. Quinidine steadies
    heart rhythm. FDA lists quinidine as a strong CYP2D6 blocker and does not list
    quinine at all. Linking drug names to rows in a chemical dataset by connections
    alone, which is the quickest way to do it, merges these two and reports the average
    of a strong blocker and a weak one.
    """,
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## A mouse is not a small person""")
    return


@app.cell(hide_code=True)
def _(alt, clearance_summary, mo, pd):
    def species_chart():
        summary = clearance_summary.iloc[0]
        frame = pd.DataFrame(
            [
                {"species": "Human liver", "clearance": summary.median_human_clint},
                {"species": "Mouse liver", "clearance": summary.median_mouse_clint},
            ]
        )
        return (
            alt.Chart(frame)
            .mark_bar(cornerRadius=2, size=46)
            .encode(
                y=alt.Y("species:N", title=None),
                x=alt.X("clearance:Q", title="Typical clearance rate (mL/min/kg)"),
                tooltip=["species", alt.Tooltip("clearance:Q", format=".1f")],
            )
            .properties(height=150, width="container")
        )

    mo.ui.altair_chart(species_chart())
    return (species_chart,)


@app.cell(hide_code=True)
def _(clearance_summary, mo):
    _c = clearance_summary.iloc[0]
    mo.md(
        f"""
    Across the {_c.compounds_with_both:,.0f} compounds OpenADMET measured in both
    species, a mouse liver clears the typical compound
    {_c.median_mouse_over_human:.1f} times faster than a human liver does, and
    {_c.share_faster_in_mouse:.0f} percent of compounds are faster in the mouse. A
    dose a mouse shrugs off can accumulate in a person.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## The most dispensed drug in America carries no warning""")
    return


@app.cell(hide_code=True)
def _(mo, plain_table, ranking_rows, structure):
    mo.hstack(
        [
            structure(
                "levothyroxine",
                "Levothyroxine, a thyroid hormone replacement that tens of millions "
                "of people take every day.",
            ),
            plain_table(ranking_rows),
        ],
        widths=[1, 1],
        gap=2,
    )
    return


@app.cell(hide_code=True)
def _(aside, drugs, measured, mo):
    def cyp2c9_ranking() -> list[dict]:
        fitted = measured[
            (measured.enzyme == "CYP2C9") & (measured.endpoint == "pIC50_direct")
        ]
        ranked = (
            fitted.groupby("drug_id").value.max().sort_values(ascending=False).head(5)
        )
        names = dict(zip(drugs.drug_id, drugs.display_name))
        return [
            {
                "Blocks CYP2C9 most strongly": names[drug_id].capitalize(),
                "pIC50": f"{value:.2f}",
            }
            for drug_id, value in ranked.items()
        ]

    ranking_rows = cyp2c9_ranking()
    mo.vstack(
        [
            mo.md(
                """
    Levothyroxine blocks CYP2C9 harder than any other approved drug matched in this
    dataset, and FDA lists no enzyme role for it whatsoever.
    """
            ),
            aside(
                "Why this is not a reason to panic",
                """
    A treated patient carries a concentration of levothyroxine thousands of times
    below the concentration at which this blocking shows up in a well. The measurement
    is real and the risk is not.

    That gap is the most important idea in the notebook. A number measured on a plate
    describes a molecule, and it becomes a fact about a person only once you know how
    much of that molecule reaches the enzyme inside a living body. That quantity is
    missing from every dataset used here, and it is also the main reason the CYP3A4
    comparison fell apart, because CYP3A4 blocking happens partly in the gut wall at
    concentrations the plate never sees.
    """,
            ),
        ]
    )
    return cyp2c9_ranking, ranking_rows


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Your shelf, read again""")
    return


@app.cell(hide_code=True)
def _(cabinet, evidence_state, mo, name_of, plain_table):
    def shelf_summary() -> list[dict]:
        tiers = {
            "measured": "FDA published a class, and this dataset measured it",
            "documented": "FDA published a class, nothing measured here",
            "unknown": "No enzyme role on record with FDA",
        }
        return [
            {
                "Drug": name_of.get(drug_id, drug_id).capitalize(),
                "Evidence behind it": tiers[evidence_state(drug_id)],
            }
            for drug_id in cabinet.shelf
        ]

    _rows = shelf_summary()
    plain_table(_rows) if _rows else mo.md(
        "Your shelf is empty. Scroll back up and add something to it."
    )
    return (shelf_summary,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    Three kinds of claim sit on that shelf and the notebook has shown you what
    separates them. None of this predicts anybody's blood concentration, and none of
    it sees interactions that travel by any route other than these enzymes. Warfarin
    taken with ibuprofen shows nothing here and is genuinely dangerous.
    """
    )
    return


@app.cell(hide_code=True)
def _(aside, mo):
    mo.vstack(
        [
            mo.md(
                """
    ## What would make the cheap measurement trustworthy

    About 94.5 billion molecules can be bought on demand. The largest public dataset
    of CYP inhibition covers 16,560 compounds, and a commercial panel takes ten
    business days per compound. That is why anyone wants to predict this property
    rather than measure it.

    What this notebook found is that the property being predicted behaves differently
    between enzymes, and the missing ingredient is not more compounds. It is the human
    context for the compounds already measured: how much of the drug circulates
    unbound, and how much of the blocking happens in the gut rather than the liver.
    """
            ),
            aside(
                "Where every number came from",
                """
    Potencies come from the OpenADMET CYP challenge training files, induction values
    from the PXR challenge, and clearance from the ExpansionRx release. Clinical
    exposure increases are quoted from FDA labels retrieved through openFDA. Enzyme
    roles and strength bands come from FDA's public-domain table of drugs that
    interact with CYP enzymes.

    The competition datasets ship no drug names at all, so names were recovered by
    matching structures: salts stripped to the parent, stereochemistry preserved, and
    every match recorded with the file and row it came from. The quinine section
    exists because that decision changes answers.

    No model is fitted anywhere except the straight line you competed against, which
    is refitted without whichever drug it is predicting. Everything else shown is a
    measurement, or arithmetic on measurements.
    """,
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
