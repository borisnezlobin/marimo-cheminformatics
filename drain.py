# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo>=0.25.0",
#     "anywidget==0.11.0",
#     "traitlets==5.16.1",
#     "pandas==3.0.6",
#     "numpy==2.3.5",
#     "altair==6.3.0",
#     "rdkit==2026.3.6",
# ]
# ///

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="Drain")


@app.cell(hide_code=True)
def _():
    import functools
    import io
    import json
    import re
    import urllib.request
    from pathlib import Path

    import altair as alt
    import anywidget
    import marimo as mo
    import numpy as np
    import pandas as pd
    import traitlets
    from rdkit import Chem, DataStructs, RDLogger
    from rdkit.Chem import Descriptors, rdDepictor, rdFingerprintGenerator, rdMolDescriptors
    from rdkit.Chem.Draw import rdMolDraw2D
    from rdkit.Chem.MolStandardize import rdMolStandardize

    RDLogger.DisableLog("rdApp.*")

    REPO_RAW = "https://raw.githubusercontent.com/borisnezlobin/marimo-cheminformatics/main/"

    def read_text(relative_path):
        """Read a file that ships with this repository, or fetch it from GitHub."""
        local = Path(mo.notebook_dir() or ".") / relative_path
        if local.exists():
            return local.read_text()
        with urllib.request.urlopen(REPO_RAW + relative_path) as response:
            return response.read().decode()

    def read_table(relative_path):
        return pd.read_csv(io.StringIO(read_text(relative_path)))

    INK = "#1A2124"
    MUTED = "#56636A"
    POPULATION = "#B8C2BE"
    CENSORED = "#DCE2E0"
    BLUE = "#2A78C2"
    AMBER = "#B7741A"
    ENZYMES = ["CYP1A2", "CYP2C9", "CYP2D6", "CYP3A4"]
    RELIABLE_FLOOR = 4.0
    INHIBITION_FILE = "cyp-challenge-TRAIN_inhibition.csv"
    return (
        AMBER,
        BLUE,
        CENSORED,
        Chem,
        DataStructs,
        Descriptors,
        ENZYMES,
        INHIBITION_FILE,
        INK,
        MUTED,
        POPULATION,
        RELIABLE_FLOOR,
        alt,
        anywidget,
        functools,
        json,
        mo,
        np,
        pd,
        rdDepictor,
        rdFingerprintGenerator,
        rdMolDescriptors,
        rdMolDraw2D,
        rdMolStandardize,
        re,
        read_table,
        read_text,
        traitlets,
    )


@app.cell(hide_code=True)
def _(mo, read_text):
    mo.vstack([mo.Html(f"<style>{read_text('theme.css')}</style>"), mo.md(r"""
    # Drain

    *By Boris Nezlobin, built with help from Claude Code.*

    A handful of enzymes in your liver break down most medicines you swallow.
    When two medicines are broken down by the same enzymes, one of them can build up and
    turn a safe dose into a dangerous overdose.

    OpenADMET measured how strongly thousands of compounds block four of those enzymes.
    This notebook's question is simple: can a number measured in a plastic well tell you that two
    medicines will clash in a person?

    The game below is built on OpenADMET measurements and will help you get a visual understanding
    of what's going on—play a couple of levels!
    """)])
    return


@app.cell(hide_code=True)
def _(drain):
    drain
    return


@app.cell(hide_code=True)
def _(drain, mo):
    CONCEPTS = [
        ("drug clearance", "enzymes"),
        ("first-pass metabolism", "first-pass"),
        ("drug interactions", "inhibition"),
        ("drug monitoring", "enzymes"),
    ]
    CHECK = '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M232.49,80.49l-128,128a12,12,0,0,1-17,0l-56-56a12,12,0,1,1,17-17L96,183,215.51,63.51a12,12,0,0,1,17,17Z"/></svg>'

    def concept_chip(index, concept, anchor, progress):
        done = progress.get(str(index), 0) > 0
        mark = CHECK if done else f"{index + 1}"
        state = "concept concept--done" if done else "concept"
        label = f"{concept}, learned" if done else f"{concept}, level {index + 1}"
        return f'<li><a class="{state}" href="#{anchor}" aria-label="{label}">{mark} {concept}</a></li>'

    _progress = drain.value.get("progress", {})
    _chips = "".join(concept_chip(index, concept, anchor, _progress) for index, (concept, anchor) in enumerate(CONCEPTS))
    mo.vstack([
        mo.md("Finish a level to check off its idea. Each idea links to the section that explains it."),
        mo.Html(f'<ul class="concepts">{_chips}</ul>'),
    ])
    return


@app.cell(hide_code=True)
def _(ENZYMES, INHIBITION_FILE, json, pd, re, read_table, read_text):
    inhibition = read_table("data/drain/inhibition.csv")
    tdi = read_table("data/drain/tdi.csv")
    screen = read_table("data/drain/screen.csv")
    pxr = read_table("data/drain/pxr.csv")
    measured = read_table("data/measured.csv")
    drugs = read_table("data/drugs.csv").set_index("drug_id")

    _game_js = read_text("widgets/drain.js")
    SPRITES = json.loads(re.search(r"const SPRITES = (\{.*?\});\n", _game_js, re.S).group(1))
    ICONS = json.loads(re.search(r"const ICONS = (\{.*?\});\n", _game_js, re.S).group(1))

    def measurement(drug, endpoint, enzyme=None):
        rows = measured[(measured.drug_id == drug) & (measured.endpoint == endpoint)]
        if enzyme is not None:
            rows = rows[rows.enzyme == enzyme]
        return float(rows.value.iloc[0]) if len(rows) else None

    direct_potency = (
        measured[(measured.endpoint == "pIC50_direct") & (measured.source_file == INHIBITION_FILE)]
        .groupby(["drug_id", "enzyme"]).value.mean().unstack()
    )

    screen_long = pd.concat(
        [
            pd.DataFrame({"Molecule_Name": screen.Molecule_Name, "SMILES": screen.SMILES, "enzyme": enzyme,
                          "log2fc": screen[f"{enzyme}_log2fc"], "fdr": screen[f"{enzyme}_fdr"]})
            for enzyme in ENZYMES
        ],
        ignore_index=True,
    )
    return (
        ICONS,
        SPRITES,
        direct_potency,
        drugs,
        inhibition,
        measured,
        measurement,
        pxr,
        screen,
        screen_long,
        tdi,
    )


@app.cell(hide_code=True)
def _(ENZYMES, anywidget, direct_potency, drugs, mo, read_text, traitlets):
    def compound_record(drug_id):
        row = direct_potency.loc[drug_id]
        return {
            "name": drugs.loc[drug_id, "display_name"],
            "pic50": {enzyme: round(float(row[enzyme]), 3) for enzyme in ENZYMES if enzyme in row and row[enzyme] == row[enzyme]},
        }

    class Drain(anywidget.AnyWidget):
        _esm = read_text("widgets/drain.js")
        progress = traitlets.Dict({}).tag(sync=True)
        learned = traitlets.Unicode("").tag(sync=True)

    class Clash(anywidget.AnyWidget):
        _esm = read_text("widgets/clash.js")
        compound = traitlets.Dict({}).tag(sync=True)

    clash_model = Clash(compound=compound_record("isavuconazole"))
    drain = mo.ui.anywidget(Drain())
    clash = mo.ui.anywidget(clash_model)
    return clash, clash_model, compound_record, drain


@app.cell(hide_code=True)
def _(ICONS, SPRITES, inhibition, mo):
    _counts = {enzyme: int(inhibition[enzyme].notna().sum()) for enzyme in ["CYP2D6", "CYP3A4"]}
    _key = [
        ('<span class="glyph glyph--level"></span>', "Medicine in your blood", "How much of the drug is circulating right now."),
        ('<span class="glyph glyph--band"></span>', "Therapeutic window", "Inside this band there's enough drug to work but not enough to hurt you. Doctors aim every dose at it."),
        ('<span class="glyph glyph--toxic"></span>', "Toxic level", "Above this line the drug does harm. The game calls crossing it an overdose."),
        (f'<img class="glyph" src="{SPRITES["cyp2d6"]}" alt="">', "Liver enzymes", "These CYP enzymes clear the drug. A blocked enzyme wears the blocking drug like a hat. A destroyed one fades away."),
        (f'<span class="glyph glyph--icon">{ICONS["pill"]}</span>', "A dose by mouth", "Each tap swallows a pill."),
        ('<span class="glyph glyph--gate"></span>', "Gut wall and liver", "In the second level, the band at the top takes a bite of each swallowed pill before it reaches your blood."),
        (f'<span class="glyph glyph--icon glyph--blood">{ICONS["drop"]}</span>', "A blood test", "In the fourth level a blood test is the only way to see the level, as it is in a clinic."),
    ]
    _rows = "".join(f"<div><dt>{glyph}{name}</dt><dd>{meaning}</dd></div>" for glyph, name, meaning in _key)
    mo.vstack([
        mo.md(
            r"""
            <a id="enzymes"></a>
            ## The game's pieces

            The game is a small model of your blood and liver.
            """
        ),
        mo.Html(f'<dl class="key">{_rows}</dl>'),
        mo.md(
            r"""
            The row of molecules at the bottom of the game is a family of liver enzymes called
            cytochrome P450 (CYP for short, pronounced "sip"). Each enzyme grabs a drug molecule.
            Then it sticks an oxygen atom onto it! That oxygen makes the drug easier to dissolve
            in water, so your kidneys can flush it out.

            The red patch in the middle of each drawing is called the heme. It holds the iron atom
            that does the oxygen-sticking. Many blocking drugs work by parking right on top of that
            iron!

            A medicine's **half-life** is how long it takes for half of it to leave your blood.
            Faster enzymes mean a shorter half-life. (Half-life also depends on how far a drug
            spreads through your body, but the game ignores that.) The first level keeps you
            tapping because its medicine has a short half-life.

            CYP3A4 alone breaks down about half of all medicines, so three of the four levels run
            on it.
            """
        ),
        mo.Html(
            f"""
            <div class="enzymes">
              <figure><img src="{SPRITES['cyp2d6']}" alt="CYP2D6 enzyme, cut open to show the heme">
                <figcaption><strong>CYP2D6</strong><br>{_counts['CYP2D6']:,} compounds measured</figcaption></figure>
              <figure><img src="{SPRITES['cyp3a4']}" alt="CYP3A4 enzyme, cut open to show the heme">
                <figcaption><strong>CYP3A4</strong><br>{_counts['CYP3A4']:,} compounds measured</figcaption></figure>
            </div>
            """
        ),
        mo.md(
            """
            Both drawings are real enzymes. Scientists mapped every atom by shining X-rays through
            crystals of each protein (PDB entries 2F9Q and 1TQN).
            """
        ),
    ])
    return


@app.cell(hide_code=True)
def _(INK, MUTED, alt):
    def finish_chart(chart, height):
        return (
            chart.properties(width="container", height=height)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#E4EAE8", domainColor="#C9D1CE")
            .configure_view(strokeWidth=0)
            .configure_legend(labelColor=INK, title=None, orient="top")
        )

    def named_markers(frame, x, label, title):
        frame = frame.sort_values(x).reset_index(drop=True)
        frame = frame.assign(label_y=14 + 16 * (frame.index % 3))
        rules = alt.Chart(frame).mark_rule(color=INK, strokeWidth=2).encode(
            x=f"{x}:Q", tooltip=[label, alt.Tooltip(f"{x}:Q", format=".2f", title=title)]
        )
        labels = alt.Chart(frame).mark_text(align="left", dx=4, dy=-4, color=INK, fontSize=12, fontWeight=600).encode(
            x=f"{x}:Q", y=alt.Y("label_y:Q", scale=None, axis=None), text=label
        )
        return rules + labels

    return finish_chart, named_markers


@app.cell(hide_code=True)
def _(ENZYMES, mo):
    enzyme_picker = mo.ui.dropdown(options=ENZYMES, value="CYP2D6", label="Enzyme")
    return (enzyme_picker,)


@app.cell(hide_code=True)
def _(direct_potency, mo):
    _paroxetine = direct_potency.loc["paroxetine", "CYP2D6"]
    mo.md(f"""
    <a id="inhibition"></a>
    ## Enzyme inhibition

    How do you measure whether a drug blocks an enzyme? OpenADMET put each compound in a
    tiny well with one enzyme plus a substance that enzyme normally breaks down. Then they
    watched how much the compound slowed the enzyme down, at 12 different concentrations.

    Those concentrations are measured in **micromolar** (µM). You don't need its exact
    size here, because all that matters is that smaller numbers mean less drug. The
    concentration that cuts the enzyme's speed in half is called the **IC50**. For example,
    paroxetine (an antidepressant) half-blocks CYP2D6 at {10 ** (6 - _paroxetine):.1f} micromolar.

    IC50s run from tiny to huge, so labs usually put them on a log scale called **pIC50**.
    It works like the pH scale: every step up means you need ten times less drug to do the
    same job. Paroxetine's pIC50 is {_paroxetine:.2f}. A higher pIC50 means a stronger blocker!

    | pIC50 | Concentration that half-blocks the enzyme |
    |---|---|
    | 4 | 100 micromolar |
    | 5 | 10 micromolar |
    | 6 | 1 micromolar |
    | 7 | 0.1 micromolar |

    When a blocker sits in an enzyme like this, any other medicine that needs that enzyme
    leaves your body more slowly. So the other medicine builds up! That's a **drug
    interaction**. Most drug interactions happen through this kind of **enzyme inhibition**.
    """)
    return


@app.cell(hide_code=True)
def _(
    CENSORED,
    POPULATION,
    RELIABLE_FLOOR,
    alt,
    direct_potency,
    drugs,
    enzyme_picker,
    finish_chart,
    inhibition,
    mo,
    named_markers,
    np,
    pd,
):
    _enzyme = enzyme_picker.value
    _values = inhibition[[_enzyme]].dropna().rename(columns={_enzyme: "pIC50"})
    _values["shown"] = _values.pIC50.clip(lower=RELIABLE_FLOOR - 0.2)
    _values["range"] = np.where(_values.pIC50 < RELIABLE_FLOOR, "Weaker than 100 µM", "Measured")

    _showcase = ["quinidine", "paroxetine", "ritonavir", "fluvoxamine", "isavuconazole", "felodipine"]
    _named = direct_potency.reindex(_showcase)[_enzyme].dropna()
    _named = pd.DataFrame({"drug": [drugs.loc[drug, "display_name"] for drug in _named.index], "pIC50": _named.to_numpy()})

    _bars = (
        alt.Chart(_values)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("shown:Q", bin=alt.Bin(step=0.25, extent=[RELIABLE_FLOOR - 0.25, 9]), title="pIC50 (higher blocks harder)"),
            y=alt.Y("count():Q", title="Compounds"),
            color=alt.Color("range:N", scale=alt.Scale(domain=["Weaker than 100 µM", "Measured"], range=[CENSORED, POPULATION])),
            tooltip=["range:N", alt.Tooltip("count():Q", title="Compounds")],
        )
    )
    _chart = finish_chart(_bars + named_markers(_named, "pIC50", "drug", "pIC50"), 260)

    _strong = float((_values.pIC50 >= 6).mean())
    _weak = float((_values.pIC50 < RELIABLE_FLOOR).mean())
    mo.vstack([
        enzyme_picker,
        _chart,
        mo.md(
            f"""
            Of the {len(_values):,} compounds measured against {_enzyme}, {_strong:.0%} block it at
            1 micromolar or less (a pIC50 of 6 or more). OpenADMET says its test can't reliably
            measure anything below 4. So the {_weak:.0%} of compounds that score lower all share the
            pale bar on the left. All anyone knows about them is that they need more than 100
            micromolar to half-block the enzyme.
            """
        ),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    stereo_guess = mo.ui.radio(
        options=["About the same", "About 3 times", "About 30 times", "More than 300 times"],
        label="How many times harder does quinidine block CYP2D6 than quinine?",
    )
    return (stereo_guess,)


@app.cell(hide_code=True)
def _(
    Chem,
    DataStructs,
    direct_potency,
    drugs,
    mo,
    rdDepictor,
    rdFingerprintGenerator,
    rdMolDraw2D,
    stereo_guess,
):
    QUININE = drugs.loc["quinine", "smiles"]
    QUINIDINE = drugs.loc["quinidine", "smiles"]

    def stereo_labels(mol):
        return {atom.GetIdx(): atom.GetProp("_CIPCode") for atom in mol.GetAtoms() if atom.HasProp("_CIPCode")}

    def draw_with_differences(smiles, other_smiles):
        mol = Chem.MolFromSmiles(smiles)
        other = Chem.MolFromSmiles(other_smiles)
        Chem.AssignStereochemistry(mol, cleanIt=True, force=True)
        Chem.AssignStereochemistry(other, cleanIt=True, force=True)
        here, there = stereo_labels(mol), stereo_labels(other)
        differing = [index for index, code in here.items() if there.get(index) != code]
        rdDepictor.Compute2DCoords(mol)
        drawer = rdMolDraw2D.MolDraw2DSVG(340, 240)
        options = drawer.drawOptions()
        options.addStereoAnnotation = True
        options.clearBackground = False
        drawer.DrawMolecule(mol, highlightAtoms=differing, highlightAtomColors={i: (0.72, 0.45, 0.10) for i in differing})
        drawer.FinishDrawing()
        return drawer.GetDrawingText().replace("<?xml version='1.0' encoding='iso-8859-1'?>", ""), len(differing), len(here)

    def similarity(include_chirality):
        generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048, includeChirality=include_chirality)
        a, b = (generator.GetFingerprint(Chem.MolFromSmiles(smiles)) for smiles in (QUININE, QUINIDINE))
        return DataStructs.TanimotoSimilarity(a, b)

    def key_markup(drug_id):
        block, rest = drugs.loc[drug_id, "inchikey"].split("-", 1)
        return f'<code class="inchikey"><mark>{block}</mark>-{rest}</code>'

    _quinine_svg, _differences, _centres = draw_with_differences(QUININE, QUINIDINE)
    _quinidine_svg, _, _ = draw_with_differences(QUINIDINE, QUININE)
    _quinine = direct_potency.loc["quinine", "CYP2D6"]
    _quinidine = direct_potency.loc["quinidine", "CYP2D6"]
    _fold = 10 ** (_quinidine - _quinine)

    _question = mo.md(
        f"""
        <a id="stereo"></a>
        ## Quinine and quinidine

        Quinine (the bitter taste in tonic water) and quinidine (a heart-rhythm drug) are made
        of exactly the same atoms, bonded in exactly the same order. So how can they be two
        different drugs? The answer is their 3D shape.

        Some carbon atoms hold their four neighbours in a way that comes in a left-handed and a
        right-handed version, like a pair of gloves. Chemists call these carbons
        **stereocentres**. Each of these drugs has {_centres} of them. Quinine and quinidine
        match at {_centres - _differences} of those carbons but point the opposite way at the
        other {_differences}.

        Before you scroll on, take a guess!
        """
    )

    _reveal = mo.vstack([
        mo.md(f"You guessed {stereo_guess.value.lower() if stereo_guess.value else ''}. The real gap is **{_fold:,.0f} times**!"),
        mo.Html(
            f"""
            <div class="pair">
              <figure>{_quinine_svg}<figcaption><strong>Quinine</strong><br>CYP2D6 pIC50 {_quinine:.2f}</figcaption></figure>
              <figure>{_quinidine_svg}<figcaption><strong>Quinidine</strong><br>CYP2D6 pIC50 {_quinidine:.2f}</figcaption></figure>
            </div>
            """
        ),
        mo.md(
            f"""
            The orange highlights mark the {_differences} carbons that flipped. The other
            {_centres - _differences} point the same way in both drugs. That means these two molecules
            are not mirror images of each other, because a mirror image would flip every
            stereocentre. Chemists call a pair like this **diastereomers**. CYP2D6's pocket has a
            3D shape of its own. Quinidine just fits it much better than quinine does.

            Software loses this difference all the time! Chemistry databases give every molecule a
            standard ID called an **InChIKey**. It comes in two blocks. The first block describes
            which atoms are bonded to which. The second block describes the 3D arrangement. Here
            are both drugs:

            {key_markup("quinine")} quinine<br>
            {key_markup("quinidine")} quinidine

            The first blocks match exactly.

            Lots of prediction models describe a molecule with a **Morgan fingerprint**. It's
            basically a checklist of the small groups of atoms a molecule contains. RDKit (the
            chemistry library this notebook uses) leaves 3D shape out of its fingerprints by
            default. So it scores these two drugs as identical, with a similarity of
            {similarity(False):.2f} on a scale from 0 to 1! If you switch 3D shape on, the score drops
            to {similarity(True):.2f}.

            A model that reads the default fingerprint has to predict the same potency for both
            drugs. It will be off by a factor of {_fold:,.0f} for at least one of them.
            """
        ),
    ])
    mo.vstack([_question, stereo_guess, _reveal if stereo_guess.value else mo.md("")])
    return


@app.cell(hide_code=True)
def _(mo):
    tdi_picker = mo.ui.dropdown(options=["CYP3A4", "CYP2D6"], value="CYP2D6", label="Enzyme")
    return (tdi_picker,)


@app.cell(hide_code=True)
def _(
    AMBER,
    BLUE,
    INK,
    RELIABLE_FLOOR,
    alt,
    finish_chart,
    measured,
    mo,
    np,
    pd,
    tdi,
    tdi_picker,
):
    _enzyme = tdi_picker.value
    _rows = tdi[["Molecule_Name", f"{_enzyme}_direct", f"{_enzyme}_TDI", f"{_enzyme}_is_TDI"]].dropna()
    _rows.columns = ["compound", "direct", "after", "flagged"]
    _rows["flagged"] = _rows.flagged.astype(str).str.lower().eq("true")
    _rows["group"] = _rows.flagged.map({True: "Gets worse with time", False: "Stays the same"})

    _ritonavir_id = measured[(measured.drug_id == "ritonavir") & (measured.endpoint == "is_TDI")].source_id.iloc[0]
    _highlight = _rows[_rows.compound == _ritonavir_id].assign(label="ritonavir")

    _low, _high = 1.5, 8.5
    _shift = float(np.log10(2))
    _unreliable = pd.DataFrame({"x": [_low, _low], "x2": [RELIABLE_FLOOR, _high], "y": [_low, _low], "y2": [_high, RELIABLE_FLOOR]})
    _shade = alt.Chart(_unreliable).mark_rect(color="#E4EAE8", opacity=0.7).encode(x="x:Q", x2="x2:Q", y="y:Q", y2="y2:Q")
    _threshold = alt.Chart(pd.DataFrame({"x": [_low, _high - _shift], "y": [_low + _shift, _high]})).mark_line(
        color="#9AA7A2", strokeWidth=2, strokeDash=[4, 4]
    ).encode(x="x:Q", y="y:Q")
    _points = (
        alt.Chart(_rows)
        .mark_circle(size=34, opacity=0.75, stroke="#FFFFFF", strokeWidth=1)
        .encode(
            x=alt.X("direct:Q", scale=alt.Scale(domain=[_low, _high]), title="pIC50 measured straight away"),
            y=alt.Y("after:Q", scale=alt.Scale(domain=[_low, _high]), title="pIC50 after time with the enzyme"),
            color=alt.Color("group:N", scale=alt.Scale(domain=["Stays the same", "Gets worse with time"], range=[BLUE, AMBER])),
            tooltip=["compound", alt.Tooltip("direct:Q", format=".2f"), alt.Tooltip("after:Q", format=".2f"), "group"],
        )
    )
    _marker = alt.Chart(_highlight).mark_circle(size=140, color=INK, stroke="#FFFFFF", strokeWidth=2).encode(x="direct:Q", y="after:Q")
    _label = alt.Chart(_highlight).mark_text(align="left", dx=10, color=INK, fontWeight=600, fontSize=13).encode(x="direct:Q", y="after:Q", text="label")
    _chart = finish_chart(_shade + _threshold + _points + _marker + _label, 340)

    _share = float(_rows.flagged.mean())
    _ritonavir_note = (
        f"Ritonavir's IC50 shrank about {10 ** float(_highlight.after.iloc[0] - _highlight.direct.iloc[0]):.0f}-fold after the wait."
        if len(_highlight)
        else "OpenADMET didn't run this test on ritonavir for CYP3A4, so it has no point here."
    )
    mo.vstack([
        mo.md(
            r"""
            <a id="tdi"></a>
            ## Time-dependent inhibition

            Some drugs don't just sit in the enzyme. The enzyme tries to process them like any
            other drug, by sticking an oxygen atom onto them. For a few drugs, that half-processed
            molecule turns out to be reactive. It glues itself to the enzyme and breaks it for good!
            Your liver then has to build brand-new enzyme from scratch. That takes days.

            This is called **time-dependent inhibition**. You can watch it in the optional level
            "Blind, and broken": the drain stays slow even after ritonavir is gone.

            OpenADMET tested for it by measuring each compound twice. The first measurement
            happened right away. The second came after the compound had spent some time alone with
            the enzyme. If the IC50 shrank by more than 2 times after the wait, the compound counts
            as time-dependent. Those compounds land above the dashed line. The shaded strips mark
            values below pIC50 4, where the test stops being reliable.
            """
        ),
        tdi_picker,
        _chart,
        mo.md(
            f"""
            OpenADMET flagged {_share:.0%} of the {len(_rows):,} compounds tested on {_enzyme} as
            getting worse with time. {_ritonavir_note} The game shows ritonavir doing this to
            CYP2D6 because that's what this data measured. Ritonavir is more famous for doing it to
            CYP3A4 (Paxlovid depends on it!), but that result comes from clinical studies, not from
            these files.
            """
        ),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <a id="first-pass"></a>
    ## First-pass metabolism

    A swallowed pill has to get through your gut wall and then your liver before it reaches
    the rest of your blood. Both are packed with CYP3A4, so both take a bite. That bite is
    called **first-pass metabolism**. Take felodipine, the blood-pressure pill in the second
    level. According to its FDA label, only about 20% of each tablet makes it into your
    blood! The size of the bite also changes from person to person and from day to day.
    That's why each pill in the game loses a different amount.

    No single lab well can measure first-pass metabolism, because it takes a whole gut and
    liver working together. So OpenADMET's files have nothing on it.
    """)
    return


@app.cell(hide_code=True)
def _(
    POPULATION,
    alt,
    drugs,
    finish_chart,
    measured,
    mo,
    named_markers,
    np,
    screen_long,
):
    _cyp3a4 = screen_long[screen_long.enzyme == "CYP3A4"].copy()
    _cyp3a4["left"] = np.clip(2 ** _cyp3a4.log2fc * 100, 0, 150)
    _named = measured[(measured.endpoint == "screen_log2fc") & (measured.enzyme == "CYP3A4") & measured.drug_id.isin(["ritonavir", "isavuconazole", "felodipine"])]
    _named = _named.drop_duplicates("drug_id").assign(
        left=lambda frame: 2 ** frame.value * 100,
        drug=lambda frame: [drugs.loc[drug, "display_name"] for drug in frame.drug_id],
    )

    _bars = (
        alt.Chart(_cyp3a4)
        .mark_bar(color=POPULATION, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("left:Q", bin=alt.Bin(step=5, extent=[0, 150]), title="CYP3A4 activity left in the screen (%)"),
            y=alt.Y("count():Q", title="Compounds"),
            tooltip=[alt.Tooltip("count():Q", title="Compounds")],
        )
    )
    _chart = finish_chart(_bars + named_markers(_named[["drug", "left"]], "left", "drug", "% left"), 240)

    _ritonavir = float(_named[_named.drug_id == "ritonavir"].left.iloc[0])
    _stronger = float((_cyp3a4.left < _ritonavir).mean())
    mo.vstack([
        mo.md(
            r"""
            <a id="boosting"></a>
            ## Boosting

            Sometimes doctors block an enzyme on purpose! Paxlovid's COVID drug, nirmatrelvir, gets
            cleared so fast that it can't reach a useful level on its own. So every Paxlovid pack
            also includes ritonavir, whose whole job is to block CYP3A4. Using one drug to slow down
            another drug's clearance (how fast your body removes it) is called **boosting**.

            OpenADMET's cheapest test shows how hard ritonavir hits CYP3A4. Octant, the lab that ran
            it, tested each compound once at a single high concentration. Octant says that
            concentration was typically 30 micromolar. Then the lab measured how much enzyme
            activity was left.
            """
        ),
        _chart,
        mo.md(
            f"""
            Ritonavir left only {_ritonavir:.0f}% of CYP3A4's activity. Just {_stronger:.0%} of the
            {len(_cyp3a4):,} screened compounds left less. Felodipine left even less! CYP3A4 also
            breaks felodipine down, so the two molecules compete for the same enzyme.
            """
        ),
    ])
    return


@app.cell(hide_code=True)
def _(POPULATION, alt, drugs, finish_chart, measured, mo, named_markers, pxr):
    _scored = pxr.dropna(subset=["pEC50"])
    _rows = measured[(measured.endpoint == "pEC50_PXR") & measured.drug_id.isin(["rifampicin", "ritonavir", "isavuconazole"])]
    _replicates = _rows.groupby("drug_id").value.agg(["min", "max", "count"])
    _named = _rows.groupby("drug_id").value.mean().reset_index()
    _named["drug"] = [drugs.loc[drug, "display_name"] for drug in _named.drug_id]

    _bars = (
        alt.Chart(_scored)
        .mark_bar(color=POPULATION, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("pEC50:Q", bin=alt.Bin(step=0.25, extent=[1.5, 8]), title="pEC50 for switching on PXR (higher is stronger)"),
            y=alt.Y("count():Q", title="Compounds"),
            tooltip=[alt.Tooltip("count():Q", title="Compounds")],
        )
    )
    _chart = finish_chart(_bars + named_markers(_named[["drug", "value"]], "value", "drug", "pEC50"), 240)

    _rif_low, _rif_high = _replicates.loc["rifampicin", ["min", "max"]]
    _beat_high = int((_scored.pEC50 > _rif_high).sum())
    _beat_low = int((_scored.pEC50 > _rif_low).sum())
    _ritonavir = float(_named[_named.drug_id == "ritonavir"].value.iloc[0])
    mo.vstack([
        mo.md(
            f"""
            <a id="induction"></a>
            ## Enzyme induction

            A protein called **PXR** works like a switch inside your liver cells. When a drug flips
            it, the cell starts making more CYP3A4. More enzyme means every medicine that CYP3A4
            clears now leaves faster. That's **enzyme induction**. The extra enzyme sticks around
            for days after the last dose. The third and fourth levels both play with that delay.

            OpenADMET measured how strongly {len(_scored):,} compounds flip the switch. They report it
            as a **pEC50**, which works just like pIC50: a higher number means less drug is needed
            to flip the switch.
            """
        ),
        _chart,
        mo.md(
            f"""
            Rifampicin (a tuberculosis antibiotic) is the textbook example of an inducer. OpenADMET
            measured it twice, getting {_rif_low:.2f} one time and {_rif_high:.2f} the other, so the
            chart marks the average. Only {_beat_high} of the {len(_scored):,} compounds beat its
            higher result. {_beat_low} beat its lower one! Two runs of the same compound can differ
            that much, so don't read too much into small gaps on this chart.

            Ritonavir scores {_ritonavir:.2f}, higher than {float((_scored.pEC50 < _ritonavir).mean()):.0%} of
            them. So ritonavir blocks CYP3A4 while also telling the liver to make more of it. Talk
            about mixed signals!
            """
        ),
    ])
    return


@app.cell(hide_code=True)
def _(Chem, Descriptors, ENZYMES, pd, rdMolDescriptors, screen):
    FEATURES = {
        "Carboxylic acid": lambda mol: mol.HasSubstructMatch(Chem.MolFromSmarts("[CX3](=O)[OX2H1,OX1-]")),
        "Basic amine": lambda mol: mol.HasSubstructMatch(Chem.MolFromSmarts("[NX3;H2,H1,H0;!$(NC=O);!$(NS=O);!$(N-a);!$(N-C=N)]([#6])")),
        "Flat aromatic slab": lambda mol: rdMolDescriptors.CalcNumAromaticRings(mol) >= 3 and rdMolDescriptors.CalcFractionCSP3(mol) < 0.2,
        "Large (over 400 Da)": lambda mol: Descriptors.MolWt(mol) > 400,
    }

    _molecules = [Chem.MolFromSmiles(smiles) for smiles in screen.SMILES]
    _flags = pd.DataFrame({name: [bool(mol is not None and test(mol)) for mol in _molecules] for name, test in FEATURES.items()})
    _hits = pd.DataFrame({enzyme: (screen[f"{enzyme}_log2fc"] <= -1) & (screen[f"{enzyme}_fdr"] < 0.05) for enzyme in ENZYMES})

    _rows = []
    for _feature in FEATURES:
        for _enzyme in ENZYMES:
            for _has, _group in [(True, "With the feature"), (False, "Without it")]:
                _mask = _flags[_feature] == _has
                _rows.append({"feature": _feature, "enzyme": _enzyme, "group": _group,
                              "hit_rate": float(_hits.loc[_mask, _enzyme].mean()), "compounds": int(_mask.sum())})
    tastes = pd.DataFrame(_rows)
    unparsed = sum(mol is None for mol in _molecules)
    return tastes, unparsed


@app.cell(hide_code=True)
def _(AMBER, BLUE, INK, MUTED, alt, mo, screen, tastes, unparsed):
    _chart = (
        alt.Chart(tastes)
        .mark_bar(cornerRadiusEnd=3, height=9)
        .encode(
            y=alt.Y("enzyme:N", title=None, sort=["CYP1A2", "CYP2C9", "CYP2D6", "CYP3A4"]),
            yOffset=alt.YOffset("group:N", sort=["With the feature", "Without it"]),
            x=alt.X("hit_rate:Q", title="Share of compounds that block the enzyme", axis=alt.Axis(format="%")),
            color=alt.Color("group:N", scale=alt.Scale(domain=["With the feature", "Without it"], range=[AMBER, BLUE]), legend=alt.Legend(title=None, orient="top")),
            tooltip=["feature", "enzyme", "group", alt.Tooltip("hit_rate:Q", format=".0%", title="Blocks"), alt.Tooltip("compounds:Q", title="Compounds")],
        )
        .properties(width=280, height=130)
        .facet(facet=alt.Facet("feature:N", title=None, header=alt.Header(labelColor=INK, labelFontWeight=600, labelFontSize=13, labelAnchor="start")), columns=2)
        .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#E4EAE8", domainColor="#C9D1CE")
        .configure_view(strokeWidth=0)
    )

    _rate = lambda feature, enzyme, group: float(tastes.query("feature == @feature and enzyme == @enzyme and group == @group").hit_rate.iloc[0])
    mo.vstack([
        mo.md(
            r"""
            <a id="tastes"></a>
            ## What each enzyme grabs

            Doctors **manage interactions** after they show up, by pausing or swapping a medicine.
            Chemists try to prevent them before a drug even exists, by designing molecules the
            enzymes won't grab. That works because each CYP enzyme's pocket has its own shape and
            electric charge. So each enzyme prefers different kinds of molecules.

            OpenADMET's screen tested every compound once against each enzyme. The chart counts a
            compound as a blocker if it removed at least half of the enzyme's activity. The lab
            also had to be confident the result wasn't a fluke (a false discovery rate under 5%).
            You can read the RDKit search behind each feature in the code.
            """
        ),
        _chart,
        mo.md(
            f"""
            A **basic amine** is a nitrogen atom that picks up a positive charge inside your body.
            Basic amines raise the share of CYP2D6 blockers from {_rate('Basic amine', 'CYP2D6', 'Without it'):.0%} to
            {_rate('Basic amine', 'CYP2D6', 'With the feature'):.0%}! CYP2D6's pocket holds a negatively
            charged amino acid. Opposite charges attract, so amines stick. CYP1A2 has a narrow,
            flat pocket instead. Flat slabs of aromatic rings (rings of carbon like the one in
            benzene) block it more often.

            Big molecules (over 400 daltons, the unit chemists use for molecular weight) block
            CYP3A4 {_rate('Large (over 400 Da)', 'CYP3A4', 'With the feature'):.0%} of the time, against
            {_rate('Large (over 400 Da)', 'CYP3A4', 'Without it'):.0%} for smaller ones. CYP3A4 has the
            roomiest pocket of the four, so it can fit bigger molecules.

            Carboxylic acids (the acidic group in vinegar) cut blocking for all four enzymes, even
            CYP2C9. That's surprising, because textbooks describe CYP2C9 as preferring acids! The
            textbooks are describing the drugs CYP2C9 breaks down, though, not the drugs that block
            it. (RDKit read {len(screen) - unparsed:,} of the {len(screen):,} screen structures without
            errors.)
            """
        ),
        mo.accordion({"Table view": mo.ui.table(tastes.assign(hit_rate=tastes.hit_rate.round(3)), selection=None)}),
    ])
    return


@app.cell(hide_code=True)
def _(direct_potency, drugs, mo):
    _names = {drugs.loc[drug_id, "display_name"]: drug_id for drug_id in direct_potency.index}
    drug_picker = mo.ui.dropdown(options=dict(sorted(_names.items())), value="isavuconazole", searchable=True, label="A named medicine")
    smiles_box = mo.ui.text(placeholder="CC(=O)Oc1ccccc1C(=O)O", label="Or paste a SMILES string", full_width=True)
    return drug_picker, smiles_box


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <a id="clash"></a>
    ## Predicting an interaction

    Time to answer the question from the top! A pIC50 tells you how much of a drug it takes
    to half-block an enzyme in a well. To get from there to a real person, you need two
    more numbers. The first is how much of the blocker actually reaches the enzyme inside
    your body. The second is how much the other medicine depends on that enzyme to leave.
    FDA's simplest model combines all three:

    $$
    \text{exposure increase} = \frac{1}{\dfrac{f}{1 + I/\text{IC50}} + (1 - f)}
    $$

    Here $I$ is the blocker's concentration at the enzyme. $f$ is the share of the other
    medicine's clearance (how fast your body removes it) that runs through that enzyme.
    "Exposure" means how much of the other medicine your body sees over time. So an
    exposure increase of 2 works like doubling its dose. (FDA's real formula uses a
    slightly different potency number. Plugging in the IC50 instead is a common first
    guess.)

    Pick a compound below, then set the two numbers the lab can't give you. If you'd rather
    paste a molecule, use a **SMILES string**, which writes a molecule as one line of text.
    For example, CCO is ethanol.
    """)
    return


@app.cell(hide_code=True)
def _(
    Chem,
    DataStructs,
    ENZYMES,
    drugs,
    functools,
    inhibition,
    pd,
    rdFingerprintGenerator,
    rdMolStandardize,
):
    NAMES_BY_KEY = dict(zip(drugs.inchikey, drugs.display_name))
    FINGERPRINTS = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048, includeChirality=True)
    CHOOSER = rdMolStandardize.LargestFragmentChooser()

    @functools.cache
    def compound_index():
        molecules = [Chem.MolFromSmiles(smiles) for smiles in inhibition.SMILES]
        keep = [index for index, mol in enumerate(molecules) if mol is not None]
        index = inhibition.iloc[keep].reset_index(drop=True)
        keys = [Chem.MolToInchiKey(molecules[i]) for i in keep]
        names = [NAMES_BY_KEY.get(key, name) for key, name in zip(keys, index.Molecule_Name)]
        index = index.assign(inchikey=keys, block=[key.split("-")[0] for key in keys], name=names)
        return index, [FINGERPRINTS.GetFingerprint(molecules[i]) for i in keep]

    def potency_of(row):
        return {enzyme: round(float(row[enzyme]), 3) for enzyme in ENZYMES if pd.notna(row[enzyme])}

    def nearest(parent, count=3):
        index, fingerprints = compound_index()
        scores = DataStructs.BulkTanimotoSimilarity(FINGERPRINTS.GetFingerprint(parent), fingerprints)
        top = index.assign(similarity=scores).nlargest(count, "similarity")
        table = top[["name", "similarity", *ENZYMES]].round(2).astype(object).where(top[["name", "similarity", *ENZYMES]].notna(), "–")
        return table.rename(columns={"name": "Compound", "similarity": "Similarity"}).reset_index(drop=True)

    def match_notes(parent, stripped):
        index, _ = compound_index()
        key = Chem.MolToInchiKey(parent)
        notes = ["The tool is using the pasted structure. Clear the box to go back to the list."]
        if stripped:
            notes.append("RDKit kept the largest fragment and dropped the rest, which removes salts like hydrochloride.")
        exact = index[index.inchikey == key]
        if len(exact):
            return exact.iloc[0], notes + [f"Found in OpenADMET's inhibition set as {exact.iloc[0].Molecule_Name}."]
        cousins = index[index.block == key.split("-")[0]]
        if len(cousins):
            notes.append(f"{cousins.iloc[0]['name']} has the same atoms and bonds but a different 3D arrangement. Its numbers may not apply, as quinine and quinidine showed, so they are not used.")
        notes.append("This exact structure was not measured. Below are the most similar compounds that were, scored from 0 to 1 with the chirality-aware fingerprint. Even a close match can differ a lot, as quinine and quinidine showed.")
        return None, notes

    def resolve_smiles(text):
        mol = Chem.MolFromSmiles(text)
        if mol is None:
            return {"error": "RDKit could not read that SMILES. Check the brackets and ring-closure numbers, or pick a named medicine instead."}
        parent = CHOOSER.choose(mol)
        row, notes = match_notes(parent, parent.GetNumAtoms() < mol.GetNumAtoms())
        found = row is not None
        return {
            "name": row["name"] if found else "Your structure",
            "pic50": potency_of(row) if found else {},
            "notes": notes,
            "neighbours": None if found else nearest(parent),
            "mol": parent,
        }

    return (resolve_smiles,)


@app.cell(hide_code=True)
def _(
    Chem,
    clash_model,
    compound_record,
    drug_picker,
    rdDepictor,
    rdMolDraw2D,
    resolve_smiles,
    smiles_box,
    drugs,
):
    def structure_svg(mol):
        mol = Chem.Mol(mol)
        rdDepictor.Compute2DCoords(mol)
        drawer = rdMolDraw2D.MolDraw2DSVG(300, 200)
        drawer.drawOptions().clearBackground = False
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        return drawer.GetDrawingText().replace("<?xml version='1.0' encoding='iso-8859-1'?>", "")

    def named_lookup(drug_id):
        record = compound_record(drug_id)
        return {**record, "notes": [], "neighbours": None, "mol": Chem.MolFromSmiles(drugs.loc[drug_id, "smiles"])}

    _typed = smiles_box.value.strip()
    lookup = resolve_smiles(_typed) if _typed else named_lookup(drug_picker.value)
    if "error" not in lookup:
        clash_model.compound = {"name": lookup["name"], "pic50": lookup["pic50"]}
    lookup_svg = structure_svg(lookup["mol"]) if "mol" in lookup else ""
    return lookup, lookup_svg


@app.cell(hide_code=True)
def _(clash, drug_picker, lookup, lookup_svg, mo, smiles_box):
    def lookup_panel():
        if "error" in lookup:
            return mo.callout(mo.md(lookup["error"]), kind="warn")
        parts = [mo.Html(f'<figure class="lookup-structure">{lookup_svg}</figure>')]
        parts += [mo.md(note) for note in lookup["notes"]]
        if lookup["neighbours"] is not None:
            parts.append(mo.ui.table(lookup["neighbours"], selection=None, show_column_summaries=False))
        return mo.vstack(parts)

    mo.vstack([
        mo.hstack([drug_picker, smiles_box], widths=[1, 2], align="end"),
        lookup_panel(),
        clash,
        mo.md(
            r"""
            Try this: set the second slider to 80%, then drag the blocker as high as it goes. The
            exposure increase stops just under 5 times! The other medicine still sends a fifth of
            its clearance through other routes, so it can always leave that way. In general, no
            blocker can push exposure past $1/(1-f)$. FDA draws its "sensitive" line in the same
            place. It calls a medicine sensitive when a strong blocker raises its exposure 5 times
            or more. That only happens when $f$ is at least 80%.
            """
        ),
        mo.accordion({
            "Load the data yourself": mo.md(
                r"""
                ```python
                import pandas as pd

                base = "hf://datasets/openadmet/cyp-challenge-train-test/"
                inhibition = pd.read_csv(base + "cyp-challenge-TRAIN_inhibition.csv")
                screen = pd.read_csv(base + "cyp-challenge-single-concentration-TRAIN.csv")
                ```

                Each row of `inhibition` is one compound. It has a SMILES string plus one
                pIC50 column per enzyme. Values below 4 are outside the reliable range.
                """
            )
        }),
    ])
    return


@app.cell(hide_code=True)
def _(RELIABLE_FLOOR, inhibition, mo):
    _below = float((inhibition.CYP3A4.dropna() < RELIABLE_FLOOR).mean())
    mo.md(
        f"""
        <a id="limits"></a>
        ## What the game makes up

        The game gets right which drug does what to which enzyme. Its speeds and doses are made
        up, though!

        * **Measured.** Isavuconazole and paroxetine block their enzymes in OpenADMET's tests.
          Rifampicin flips the PXR switch. Ritonavir gets worse with time on CYP2D6.
        * **From FDA and the clinic.** The medicines being cleared (metoprolol, midazolam,
          felodipine and simvastatin) come from FDA's list of drugs those enzymes clear.
          OpenADMET didn't test them. Nirmatrelvir's fast clearance comes from clinical
          studies, as does ritonavir's damage to CYP3A4.
        * **Compressed time.** In a real body, induction takes days to build up and days to
          fade. The third level squeezes that into seconds so you can watch it happen.
        * **Invented.** The speeds, doses and green bands are tuned so each level plays well.
          Turning a lab potency into a real drug level would take the two numbers from the
          interaction model above. Neither one is in these files.
        * **Lab conditions.** The screen used one high concentration, way above the blood level
          of most medicines. So it flags more blockers than a patient would ever notice.
        * **Censored values.** {_below:.0%} of the CYP3A4 pIC50 values are below 4, outside the
          range the test measures reliably. Read those as "weaker than 100 micromolar," not as
          exact potencies.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## How this notebook was made

    **AI use.** I built this notebook with heavy help from Claude (Anthropic's AI model) in
    Claude Code. Claude wrote most of the code, the game and the text. It also ran the
    simulations I used to balance each level, working from my direction and playtesting.

    **Data.** The data comes from OpenADMET's CYP inhibition challenge release (Apache-2.0)
    and PXR challenge release (CC BY 4.0) on Hugging Face. `build/build_drain_data.py`
    rebuilds the trimmed tables in `data/drain/` from those files. The reliable range
    (pIC50 4 and up) and the 2-fold rule for time-dependent inhibition come from
    OpenADMET's CYP challenge tutorial. The screen concentration comes from Octant's
    write-up of the test. The list of drugs each enzyme clears is FDA's table of
    substrates, inhibitors and inducers. Felodipine's 20% figure is from its FDA label.

    **Drawings.** The enzyme drawings use PDB entries 2F9Q (CYP2D6) and 1TQN (CYP3A4). The
    drug shapes come from RDKit. David S. Goodsell's Illustrate program rendered all of them
    (Apache-2.0). The fact that CYP3A4 handles about half of all medicines is from PDB-101's
    Molecule of the Month on cytochrome P450. Icons are Phosphor (MIT).

    **Keyboard.** Click the game first. Space doses the first beaker. Keys 1 to 3 dose or
    pause the other beakers. R, I or B uses the token in the corner.
    """)
    return


if __name__ == "__main__":
    app.run()
