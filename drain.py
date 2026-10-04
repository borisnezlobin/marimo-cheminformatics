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
        ('<span class="glyph glyph--band"></span>', "Therapeutic window", "The band holds enough drug to work and too little to harm, and doctors aim every dose at it."),
        ('<span class="glyph glyph--toxic"></span>', "Toxic level", "Above this line the drug does harm. The game calls crossing it an overdose."),
        (f'<img class="glyph" src="{SPRITES["cyp2d6"]}" alt="">', "Liver enzymes", "These CYP enzymes clear the drug. A blocked copy wears the blocking drug, and a destroyed copy fades away."),
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
            The row of molecules at the bottom is a family of liver enzymes called cytochrome
            P450, written CYP. Each one grabs a drug molecule, attaches an oxygen atom to it,
            and lets it go in a form the kidneys can flush out. The red patch in the middle of
            each drawing is the heme. It's a ring that holds an iron atom, and the oxygen gets
            attached at that iron. Many blocking drugs work by sitting on it.

            A medicine's **half-life** is the time it takes for half of it to leave your blood.
            The faster the enzymes clear a medicine, the shorter its half-life. Half-life also
            depends on how widely the drug spreads through your body, and the game leaves that
            part out. The first level makes you tap in a steady rhythm because its medicine has
            a short half-life.

            CYP3A4 alone breaks down about half of all medicines, so three of the four levels
            run on it.
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
            Both drawings come from real crystal structures (PDB 2F9Q and 1TQN). David Goodsell's
            Illustrate program drew each one as a slice through the iron atom.
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

    OpenADMET put each compound in a well with one enzyme and a substance that enzyme
    normally breaks down. Then it measured how much the compound slowed the enzyme at
    12 different concentrations. The concentration that cuts the enzyme's speed in half
    is called the **IC50**. Paroxetine, an antidepressant, half-blocks
    CYP2D6 at {10 ** (6 - _paroxetine):.1f} micromolar.

    IC50s span a huge range, so labs report them on a log scale called **pIC50**. It works
    like the pH scale, so each whole step up means ten times less drug does the same job.
    Paroxetine's pIC50 is {_paroxetine:.2f}.

    | pIC50 | Concentration that half-blocks the enzyme |
    |---|---|
    | 4 | 100 micromolar |
    | 5 | 10 micromolar |
    | 6 | 1 micromolar |
    | 7 | 0.1 micromolar |

    When a second medicine sits in the enzyme like this, the first one stops leaving
    and builds up. That is a **drug interaction**, and **enzyme inhibition** is the
    mechanism behind most of them.
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
            1 micromolar or less (pIC50 6 and up). OpenADMET says its assay can't measure anything
            below 4 reliably, so the {_weak:.0%} of compounds that score lower share the pale bar on
            the left. All anyone knows about them is that they need more than 100 micromolar.
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

        Quinine, the bitter taste in tonic water, and quinidine, a heart-rhythm drug, are built
        from the same atoms joined in the same order. A **stereocentre** is a carbon atom that can
        hold its four groups in either of two 3D arrangements. Each drug has {_centres} of them, and
        the two drugs differ at {_differences}. Make a guess before you see the measurement.
        """
    )

    _reveal = mo.vstack([
        mo.md(f"You guessed {stereo_guess.value.lower() if stereo_guess.value else ''}. The measured gap is **{_fold:,.0f} times**."),
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
            The highlighted atoms are the two flipped centres. The other two point the same way in
            both, so the molecules are not mirror images of each other. Mirror images flip every
            centre. Molecules like these, which flip only some, are called **diastereomers**.
            CYP2D6's pocket is a 3D shape, and only quinidine fits it well.

            This difference is easy for software to lose. A molecule's **InChIKey** is a standard ID
            whose first block encodes the atoms and bonds and whose second block encodes the 3D
            arrangement. The two drugs share the first block:

            {key_markup("quinine")} quinine<br>
            {key_markup("quinidine")} quinidine

            Many prediction models describe a molecule with a Morgan fingerprint, a list of the
            small atom neighbourhoods it contains. RDKit's default fingerprint ignores 3D arrangement,
            so it scores these two drugs as identical, with a similarity of {similarity(False):.2f} on a
            scale from 0 to 1. Switching chirality on drops the score to {similarity(True):.2f}. A model
            fed the default fingerprint has to predict the same potency for both, so it will be off
            by a factor of {_fold:,.0f} for at least one of them.
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
        else "OpenADMET did not run this test on ritonavir for CYP3A4, so it has no point here."
    )
    mo.vstack([
        mo.md(
            r"""
            <a id="tdi"></a>
            ## Time-dependent inhibition

            Some drugs don't just sit in the enzyme. The enzyme starts to process them, and the
            half-finished product latches onto it and wrecks it for good. The liver then has to
            build new enzyme, and that takes days. This is **time-dependent inhibition**. In the
            optional level "Blind, and broken", the drain stays slow after ritonavir stops.

            OpenADMET tested it by measuring each compound twice, once straight away and once
            after it had spent time with the enzyme. A compound counts as time-dependent when its
            IC50 shrinks more than 2-fold after the wait, which puts it above the dashed line.
            The shaded strips mark values below pIC50 4, where the assay stops being reliable.
            """
        ),
        tdi_picker,
        _chart,
        mo.md(
            f"""
            OpenADMET flagged {_share:.0%} of the {len(_rows):,} compounds tested on {_enzyme} as
            getting worse with time. {_ritonavir_note} The game shows ritonavir doing this to
            CYP2D6 because that is what this data measured. Ritonavir is better known for doing it
            to CYP3A4, and Paxlovid depends on that effect. That result comes from clinical studies
            rather than from this data.
            """
        ),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <a id="first-pass"></a>
    ## First-pass metabolism

    A swallowed pill has to cross the gut wall and then pass through the liver before it
    reaches the rest of your blood, and both are lined with CYP3A4. That first bite is
    **first-pass metabolism**. Felodipine is the blood-pressure pill in the second level,
    and its FDA label says only about 20% of each tablet reaches the blood. The bite also
    varies from person to person and from day to day, so each pill in the game loses a
    different amount.

    First-pass metabolism depends on the gut and the liver working together, and no single
    well can reproduce that. OpenADMET's files have no measurement of it.
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

            Paxlovid's COVID drug, nirmatrelvir, is cleared so fast that it can't reach a useful
            level on its own. Every dose therefore comes with ritonavir, which blocks CYP3A4 and
            slows that clearance. Blocking one drug's clearance with another on purpose is called
            **boosting**.

            OpenADMET's cheapest test shows how hard ritonavir hits CYP3A4. Octant, the lab that
            ran it, tested each compound once at a single high concentration and recorded how much
            enzyme activity was left. Octant gives that concentration as typically 30 micromolar.
            """
        ),
        _chart,
        mo.md(
            f"""
            Ritonavir left {_ritonavir:.0f}% of CYP3A4's activity. Only {_stronger:.0%} of the
            {len(_cyp3a4):,} screened compounds left less. Felodipine left even less, because CYP3A4
            also breaks felodipine down and the two compete for the enzyme.
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

            A protein called PXR works as a switch inside liver cells. When a drug flips it, the
            cell makes more CYP3A4, so every medicine that CYP3A4 clears starts leaving faster.
            That is **enzyme induction**. The extra enzyme takes days to fade after the last dose,
            and the third and fourth levels both turn on that delay. OpenADMET measured how strongly
            {len(_scored):,} compounds flip the switch.
            """
        ),
        _chart,
        mo.md(
            f"""
            Rifampicin, a tuberculosis antibiotic and the textbook example of an inducer, was
            measured twice, at {_rif_low:.2f} and {_rif_high:.2f}, and the chart marks the average.
            Only {_beat_high} of the {len(_scored):,} compounds beat its higher result, and
            {_beat_low} beat its lower one. Two runs of the same compound can differ by this much,
            so small gaps between compounds on this chart mean little. Ritonavir scores {_ritonavir:.2f},
            higher than {float((_scored.pEC50 < _ritonavir).mean()):.0%} of them. It blocks CYP3A4 and
            tells the liver to make more CYP3A4 at the same time.
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

            Doctors **manage interactions** after the fact, by pausing or swapping a medicine.
            Chemists manage them before a drug exists, by designing
            molecules the enzymes don't grab. That works because each CYP enzyme has a pocket with
            its own shape and charge, so each one tends to grab a different kind of molecule.

            The chart counts a compound as a blocker when it removed at least half of an enzyme's
            activity in OpenADMET's screen. The lab also had to rate the result significant, which
            means a false discovery rate under 5%. Each feature is found with an RDKit substructure
            search you can read in the code.
            """
        ),
        _chart,
        mo.md(
            f"""
            A basic amine is a nitrogen atom that carries a positive charge in the body. Basic amines
            raise the share of CYP2D6 blockers from {_rate('Basic amine', 'CYP2D6', 'Without it'):.0%} to
            {_rate('Basic amine', 'CYP2D6', 'With the feature'):.0%}, because CYP2D6's pocket holds a
            negatively charged amino acid that pairs with them. CYP1A2 has a narrow, flat pocket, and
            flat slabs of aromatic rings block it more often.

            Carboxylic acids cut blocking for all four enzymes, including CYP2C9. That enzyme is usually
            described as preferring acids, but that description comes from the drugs it breaks down, not
            the ones that block it. RDKit parsed {len(screen) - unparsed:,} of the {len(screen):,} screen
            structures.
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

    This section answers the question from the top of the notebook. A pIC50 tells you how much of a drug it takes to
    half-block an enzyme in a well. To get from there to a person you need two more numbers:
    how much of the blocker actually reaches the enzyme, and how much the other medicine
    depends on that enzyme to leave your body. FDA's simplest model combines the three:

    $$
    \text{exposure increase} = \frac{1}{\dfrac{f}{1 + I/\text{IC50}} + (1 - f)}
    $$

    Here $I$ is the concentration of the blocker at the enzyme and $f$ is the share of the
    other medicine's clearance that runs through that enzyme. FDA's version uses a slightly
    different potency constant, and treating the IC50 as that constant is a common first
    approximation. Pick a compound, then set the two numbers the lab can't give you.
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
            Slide the second number to 80% and drag the blocker as high as it goes. The exposure
            increase levels off just under 5 times, because a medicine with a fifth of its clearance elsewhere
            still leaves through that other route. No blocker can push exposure past $1/(1-f)$.
            FDA draws its "sensitive" line at the same spot. It calls a medicine sensitive when a
            strong blocker raises its exposure five times or more, and that requires $f$ of at least 80%.
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

                Each row of `inhibition` is one compound, with a SMILES string and a pIC50
                column per enzyme. Values below 4 are outside the reliable range.
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

        The game is right about which drug does what to which enzyme, but its speeds and doses are made up.

        * **Measured.** Isavuconazole and paroxetine block their enzymes in OpenADMET's inhibition
          assay, rifampicin flips PXR, and ritonavir gets worse with time on CYP2D6.
        * **From FDA and the clinic.** The medicines being cleared (metoprolol, midazolam, felodipine
          and simvastatin) come from FDA's list of drugs those enzymes clear, and OpenADMET did not
          test them. Nirmatrelvir's fast clearance and ritonavir's damage to CYP3A4 come from
          clinical studies.
        * **Compressed time.** In a real body, induction takes days to build up and days to fade.
          The third level squeezes that into seconds so you can watch it happen.
        * **Invented.** The speeds, doses and green bands are tuned so each level plays well. Turning
          a lab potency into a real drug level takes the two numbers the interaction model above asks you
          for, and neither is in these files.
        * **Lab conditions.** The screen used one high concentration, far above the blood level of
          most medicines, so it flags more blockers than a patient would ever feel.
        * **Censored values.** {_below:.0%} of the CYP3A4 pIC50 values are below 4, outside the range
          the assay measures reliably. They mean "weaker than 100 micromolar" rather than an exact potency.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## How this notebook was made

    **AI use.** This notebook was built with heavy help from Claude, Anthropic's
    model, running in Claude Code. Claude wrote most of the code, the game and the
    text, and ran the simulations used to balance each level, working from the
    author's direction and play-testing.

    **Data.** OpenADMET's CYP inhibition challenge release (Apache-2.0) and PXR
    challenge release (CC BY 4.0) on Hugging Face. The trimmed tables in `data/drain/`
    are rebuilt from those files by `build/build_drain_data.py`. The reliable range
    (pIC50 4 and up) and the 2-fold rule for time-dependent inhibition come from
    OpenADMET's CYP challenge tutorial. The screen concentration comes from Octant's
    write-up of the assay. The list of drugs each enzyme clears is FDA's table of
    substrates, inhibitors and inducers, and felodipine's bioavailability is from its
    FDA label.

    **Drawings.** Enzymes from PDB entries 2F9Q (CYP2D6) and 1TQN (CYP3A4), and drug
    shapes from RDKit, rendered with Illustrate by David S. Goodsell (Apache-2.0). The
    CYP3A4 fact is from PDB-101's Molecule of the Month on cytochrome P450. Icons are
    Phosphor (MIT).

    **Keyboard.** Click the game first. Space doses the first beaker, 1 to 3 dose or
    pause the others, and R, I or B uses the tokens in the corner.
    """)
    return


if __name__ == "__main__":
    app.run()
