# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo>=0.25.0",
#     "anywidget==0.11.0",
#     "traitlets==5.16.1",
#     "pandas==3.0.6",
#     "numpy==1.26.4",
#     "altair==6.3.0",
#     "rdkit==2023.9.6",
# ]
# ///

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="Drain", css_file="theme.css")


@app.cell(hide_code=True)
def _():
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
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdDepictor, rdMolDescriptors
    from rdkit.Chem.Draw import rdMolDraw2D

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
    BLUE = "#2A78C2"
    AMBER = "#B7741A"
    ENZYMES = ["CYP1A2", "CYP2C9", "CYP2D6", "CYP3A4"]
    return (
        AMBER,
        BLUE,
        Chem,
        Descriptors,
        ENZYMES,
        INK,
        MUTED,
        POPULATION,
        alt,
        anywidget,
        json,
        mo,
        np,
        pd,
        rdDepictor,
        rdMolDescriptors,
        rdMolDraw2D,
        re,
        read_table,
        read_text,
        traitlets,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Drain

    Every medicine you swallow has to leave your body again, and most of them leave
    through a handful of enzymes in your liver. When two medicines fight over those
    enzymes, one of them can build up until a safe dose becomes an overdose. The game
    below lets you feel that happen. Everything under it shows the laboratory
    measurements the game is built on.
    """)
    return


@app.cell(hide_code=True)
def _(anywidget, mo, read_text, traitlets):
    class Drain(anywidget.AnyWidget):
        _esm = read_text("widgets/drain.js")
        progress = traitlets.Dict({}).tag(sync=True)
        learned = traitlets.Unicode("").tag(sync=True)

    drain = mo.ui.anywidget(Drain())
    drain
    return (drain,)


@app.cell(hide_code=True)
def _(drain, mo):
    CONCEPTS = [
        ("drug clearance", "enzymes"),
        ("half-life", "enzymes"),
        ("drug interactions", "inhibition"),
        ("first-pass metabolism", "screen"),
        ("enzyme inhibition", "inhibition"),
        ("boosting", "screen"),
        ("enzyme induction", "induction"),
        ("time-dependent inhibition", "tdi"),
        ("managing interactions", "tastes"),
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
        mo.md("Each level you finish marks its idea below. Every idea links to the data behind it."),
        mo.Html(f'<ul class="concepts">{_chips}</ul>'),
    ])
    return


@app.cell(hide_code=True)
def _(ENZYMES, json, pd, re, read_table, read_text):
    inhibition = read_table("data/drain/inhibition.csv")
    tdi = read_table("data/drain/tdi.csv")
    screen = read_table("data/drain/screen.csv")
    pxr = read_table("data/drain/pxr.csv")
    measured = read_table("data/measured.csv")

    _sprites_json = re.search(r"const SPRITES = (\{.*?\});\n", read_text("widgets/drain.js"), re.S).group(1)
    SPRITES = json.loads(_sprites_json)

    GAME_DRUGS = ["quinidine", "paroxetine", "ritonavir", "isavuconazole", "rifampicin", "quinine"]

    def measurement(drug, endpoint, enzyme=None):
        rows = measured[(measured.drug_id == drug) & (measured.endpoint == endpoint)]
        if enzyme is not None:
            rows = rows[rows.enzyme == enzyme]
        return float(rows.value.iloc[0]) if len(rows) else None

    screen_long = pd.concat(
        [
            pd.DataFrame({"Molecule_Name": screen.Molecule_Name, "SMILES": screen.SMILES, "enzyme": enzyme,
                          "log2fc": screen[f"{enzyme}_log2fc"], "fdr": screen[f"{enzyme}_fdr"]})
            for enzyme in ENZYMES
        ],
        ignore_index=True,
    )
    return (
        SPRITES,
        inhibition,
        measured,
        measurement,
        pxr,
        screen,
        screen_long,
        tdi,
    )


@app.cell(hide_code=True)
def _(SPRITES, inhibition, mo):
    _counts = {enzyme: int(inhibition[enzyme].notna().sum()) for enzyme in ["CYP2D6", "CYP3A4"]}
    mo.vstack([
        mo.md(
            r"""
            <a id="enzymes"></a>
            ## The drain in the game

            The row of molecules at the bottom of the game is a family of liver enzymes
            called cytochrome P450, written CYP. Each one grabs a drug molecule, attaches
            an oxygen atom to it, and lets it go in a form the kidneys can flush out. The
            red disc in the middle of each drawing is the heme, an iron-holding ring where
            that chemistry happens and where most blocking drugs sit.

            How fast the enzymes work sets a medicine's **half-life**, the time it takes
            for half of a dose to leave your blood. A short half-life means frequent doses,
            which is what the tapping rhythm in the first level is.
            """
        ),
        mo.Html(
            f"""
            <div class="enzymes">
              <figure><img src="{SPRITES['cyp2d6']}" alt="CYP2D6 enzyme, cut open to show the heme">
                <figcaption><strong>CYP2D6</strong><br>{_counts['CYP2D6']:,} compounds measured by OpenADMET</figcaption></figure>
              <figure><img src="{SPRITES['cyp3a4']}" alt="CYP3A4 enzyme, cut open to show the heme">
                <figcaption><strong>CYP3A4</strong><br>acts on about half of known drugs, and {_counts['CYP3A4']:,} compounds were measured</figcaption></figure>
            </div>
            """
        ),
        mo.md(
            """
            The drawings are the real crystal structures (PDB 2F9Q and 1TQN), drawn with
            David Goodsell's Illustrate program and sliced through the iron atom.
            """
        ),
    ])
    return


@app.cell(hide_code=True)
def _(ENZYMES, mo):
    enzyme_picker = mo.ui.dropdown(options=ENZYMES, value="CYP2D6", label="Enzyme")
    return (enzyme_picker,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <a id="inhibition"></a>
    ## How strongly a drug blocks the drain

    OpenADMET put each compound in a well with one enzyme and something that enzyme
    normally breaks down, then measured how much the compound slowed the enzyme
    across a range of concentrations. The result is reported as a **pIC50**. It works
    like the pH scale: each whole step means ten times less drug is needed to cut
    the enzyme's speed in half.

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
def _(INK, MUTED, POPULATION, alt, enzyme_picker, inhibition, measured, mo):
    _enzyme = enzyme_picker.value
    _values = inhibition[[_enzyme]].dropna().rename(columns={_enzyme: "pIC50"})
    _named = measured[(measured.endpoint == "pIC50_direct") & (measured.enzyme == _enzyme)]
    _named = _named.drop_duplicates("drug_id")[["drug_id", "value"]].rename(columns={"drug_id": "drug", "value": "pIC50"})
    _named = _named[_named.drug.isin(["quinidine", "paroxetine", "ritonavir", "isavuconazole", "quinine", "terbinafine", "fluvoxamine"])]
    _named = _named.sort_values("pIC50").reset_index(drop=True)
    _named["label_y"] = 14 + 16 * (_named.index % 3)

    _bars = (
        alt.Chart(_values)
        .mark_bar(color=POPULATION, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("pIC50:Q", bin=alt.Bin(step=0.25, extent=[1.5, 9]), title="pIC50 (higher blocks harder)"),
            y=alt.Y("count():Q", title="Compounds"),
            tooltip=[alt.Tooltip("count():Q", title="Compounds")],
        )
    )
    _rules = alt.Chart(_named).mark_rule(color=INK, strokeWidth=2).encode(x="pIC50:Q", tooltip=["drug", alt.Tooltip("pIC50:Q", format=".2f")])
    _labels = (
        alt.Chart(_named)
        .mark_text(align="left", dx=4, dy=-4, angle=0, color=INK, fontSize=12, fontWeight=600)
        .encode(x="pIC50:Q", y=alt.Y("label_y:Q", scale=None, axis=None), text="drug")
    )
    _chart = (_bars + _rules + _labels).properties(width="container", height=260).configure_axis(
        labelColor=MUTED, titleColor=MUTED, gridColor="#E4EAE8", domainColor="#C9D1CE"
    ).configure_view(strokeWidth=0)

    _strong = float((_values.pIC50 >= 6).mean())
    _weak = float((_values.pIC50 < 4.3).mean())
    mo.vstack([
        enzyme_picker,
        _chart,
        mo.md(
            f"""
            Of the {len(_values):,} compounds measured against {_enzyme}, {_strong:.0%} block it
            at a pIC50 of 6 or more, and {_weak:.0%} need more than 50 micromolar to
            half-block it. Treat those as weak or inactive, since 50 micromolar is the
            concentration OpenADMET used for its screen. The black lines are drugs from the game.
            """
        ),
    ])
    return


@app.cell(hide_code=True)
def _(Chem, measurement, mo, rdDepictor, rdMolDraw2D, read_table):
    _drugs = read_table("data/drugs.csv").set_index("drug_id")
    QUININE = _drugs.loc["quinine", "smiles"]
    QUINIDINE = _drugs.loc["quinidine", "smiles"]

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
        return drawer.GetDrawingText().replace("<?xml version='1.0' encoding='iso-8859-1'?>", ""), len(differing)

    _quinine_svg, _differences = draw_with_differences(QUININE, QUINIDINE)
    _quinidine_svg, _ = draw_with_differences(QUINIDINE, QUININE)
    _quinine = measurement("quinine", "pIC50_direct", "CYP2D6")
    _quinidine = measurement("quinidine", "pIC50_direct", "CYP2D6")
    _fold = 10 ** (_quinidine - _quinine)

    mo.vstack([
        mo.md(
            r"""
            <a id="stereo"></a>
            ## Mirror-image molecules

            Quinine, the bitter taste in tonic water, and quinidine, a heart-rhythm drug,
            are built from the same atoms joined in the same order. They differ only in how
            two of those atoms point in 3D, highlighted below. CYP2D6 can tell the difference.
            """
        ),
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
            Flipping those {_differences} centres makes the molecule {_fold:,.0f} times more potent
            against CYP2D6. That is why the game uses quinidine as a blocker. It is also why a
            model that ignores 3D shape can't predict these numbers.
            """
        ),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    tdi_picker = mo.ui.dropdown(options=["CYP3A4", "CYP2D6"], value="CYP2D6", label="Enzyme")
    return (tdi_picker,)


@app.cell(hide_code=True)
def _(AMBER, BLUE, INK, MUTED, alt, measured, mo, pd, tdi, tdi_picker):
    _enzyme = tdi_picker.value
    _rows = tdi[["Molecule_Name", f"{_enzyme}_direct", f"{_enzyme}_TDI", f"{_enzyme}_is_TDI"]].dropna()
    _rows.columns = ["compound", "direct", "after", "flagged"]
    _rows["flagged"] = _rows.flagged.astype(str).str.lower().eq("true")
    _rows["group"] = _rows.flagged.map({True: "Gets worse with time", False: "Stays the same"})

    _ritonavir_id = measured[(measured.drug_id == "ritonavir") & (measured.endpoint == "is_TDI")].source_id.iloc[0]
    _highlight = _rows[_rows.compound == _ritonavir_id].assign(label="ritonavir")

    _domain = [1.5, 8.5]
    _diagonal = alt.Chart(pd.DataFrame({"x": _domain, "y": _domain})).mark_line(color="#C9D1CE", strokeWidth=2, strokeDash=[4, 4]).encode(x="x:Q", y="y:Q")
    _points = (
        alt.Chart(_rows)
        .mark_circle(size=34, opacity=0.75, stroke="#FFFFFF", strokeWidth=1)
        .encode(
            x=alt.X("direct:Q", scale=alt.Scale(domain=_domain), title="pIC50 measured straight away"),
            y=alt.Y("after:Q", scale=alt.Scale(domain=_domain), title="pIC50 after time with the enzyme"),
            color=alt.Color("group:N", scale=alt.Scale(domain=["Stays the same", "Gets worse with time"], range=[BLUE, AMBER]), legend=alt.Legend(title=None, orient="top")),
            tooltip=["compound", alt.Tooltip("direct:Q", format=".2f"), alt.Tooltip("after:Q", format=".2f"), "group"],
        )
    )
    _marker = alt.Chart(_highlight).mark_circle(size=140, color=INK, stroke="#FFFFFF", strokeWidth=2).encode(x="direct:Q", y="after:Q")
    _label = alt.Chart(_highlight).mark_text(align="left", dx=10, color=INK, fontWeight=600, fontSize=13).encode(x="direct:Q", y="after:Q", text="label")
    _chart = (_diagonal + _points + _marker + _label).properties(width="container", height=340).configure_axis(
        labelColor=MUTED, titleColor=MUTED, gridColor="#E4EAE8", domainColor="#C9D1CE"
    ).configure_view(strokeWidth=0).configure_legend(labelColor=INK)

    _share = float(_rows.flagged.mean())
    mo.vstack([
        mo.md(
            r"""
            <a id="tdi"></a>
            ## Blocking that gets worse with time

            Some drugs don't just sit in the enzyme. The enzyme starts to process them, and
            the half-finished product latches onto it and wrecks it for good. The liver then
            has to build new enzyme, which takes days. OpenADMET tested this by measuring
            each compound twice, once straight away and once after it had spent time with
            the enzyme. Points above the dashed line blocked harder the second time. This is
            **time-dependent inhibition**, and it is why the drain stayed slow in the game
            after ritonavir stopped.
            """
        ),
        tdi_picker,
        _chart,
        mo.md(f"OpenADMET flagged {_share:.0%} of the {len(_rows):,} compounds tested on {_enzyme} as getting worse with time."),
    ])
    return


@app.cell(hide_code=True)
def _(INK, MUTED, POPULATION, alt, measured, mo, np, screen_long):
    _cyp3a4 = screen_long[screen_long.enzyme == "CYP3A4"].copy()
    _cyp3a4["left"] = np.clip(2 ** _cyp3a4.log2fc * 100, 0, 150)
    _named = measured[(measured.endpoint == "screen_log2fc") & (measured.enzyme == "CYP3A4") & measured.drug_id.isin(["ritonavir", "isavuconazole"])]
    _named = _named.drop_duplicates("drug_id").assign(left=lambda frame: 2 ** frame.value * 100)

    _bars = (
        alt.Chart(_cyp3a4)
        .mark_bar(color=POPULATION, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("left:Q", bin=alt.Bin(step=5, extent=[0, 150]), title="CYP3A4 activity left at 50 micromolar (%)"),
            y=alt.Y("count():Q", title="Compounds"),
            tooltip=[alt.Tooltip("count():Q", title="Compounds")],
        )
    )
    _rules = alt.Chart(_named).mark_rule(color=INK, strokeWidth=2).encode(x="left:Q", tooltip=["drug_id", alt.Tooltip("left:Q", format=".0f", title="% left")])
    _labels = alt.Chart(_named).mark_text(align="left", dx=4, color=INK, fontSize=12, fontWeight=600).encode(x="left:Q", y=alt.value(12 + 0), text="drug_id")
    _chart = (_bars + _rules + _labels).properties(width="container", height=240).configure_axis(
        labelColor=MUTED, titleColor=MUTED, gridColor="#E4EAE8", domainColor="#C9D1CE"
    ).configure_view(strokeWidth=0)

    _ritonavir = float(_named[_named.drug_id == "ritonavir"].left.iloc[0])
    _stronger = float((_cyp3a4.left < _ritonavir).mean())
    mo.vstack([
        mo.md(
            r"""
            <a id="screen"></a>
            ## The liver's first bite

            A swallowed pill is absorbed from your gut into a vein that runs straight to the
            liver, so CYP3A4 gets a first bite before the drug reaches the rest of your blood.
            That is **first-pass metabolism**. For some drugs most of each dose is gone before
            it can work, which is why an injection, which skips the liver, delivered an exact
            amount in the game.

            Paxlovid turns this around on purpose. Its COVID drug, nirmatrelvir, is cleared so
            fast that it struggles to reach a useful level on its own, so every dose comes with
            ritonavir to block CYP3A4. That trick is called **boosting**. The chart shows
            OpenADMET's screen, which tested each compound once at 50 micromolar.
            """
        ),
        _chart,
        mo.md(f"Ritonavir left only {_ritonavir:.0f}% of CYP3A4's activity. Just {_stronger:.0%} of the {len(_cyp3a4):,} screened compounds left less."),
    ])
    return


@app.cell(hide_code=True)
def _(INK, MUTED, POPULATION, alt, measured, mo, pxr):
    _named = measured[(measured.endpoint == "pEC50_PXR") & measured.drug_id.isin(["rifampicin", "ritonavir", "isavuconazole"])]
    _named = _named.sort_values("value", ascending=False).drop_duplicates("drug_id")[["drug_id", "value"]]
    _bars = (
        alt.Chart(pxr.dropna(subset=["pEC50"]))
        .mark_bar(color=POPULATION, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("pEC50:Q", bin=alt.Bin(step=0.25, extent=[1.5, 8]), title="pEC50 for switching on PXR (higher is stronger)"),
            y=alt.Y("count():Q", title="Compounds"),
            tooltip=[alt.Tooltip("count():Q", title="Compounds")],
        )
    )
    _rules = alt.Chart(_named).mark_rule(color=INK, strokeWidth=2).encode(x="value:Q", tooltip=["drug_id", alt.Tooltip("value:Q", format=".2f", title="pEC50")])
    _labels = alt.Chart(_named).mark_text(align="left", dx=4, color=INK, fontSize=12, fontWeight=600).encode(x="value:Q", y=alt.value(12), text="drug_id")
    _chart = (_bars + _rules + _labels).properties(width="container", height=240).configure_axis(
        labelColor=MUTED, titleColor=MUTED, gridColor="#E4EAE8", domainColor="#C9D1CE"
    ).configure_view(strokeWidth=0)

    _scored = pxr.dropna(subset=["pEC50"])
    _value = lambda drug: float(_named[_named.drug_id == drug].value.iloc[0])
    _percentile = lambda drug: float((_scored.pEC50 < _value(drug)).mean())
    _stronger_than_rifampicin = int((_scored.pEC50 > _value("rifampicin")).sum())
    mo.vstack([
        mo.md(
            f"""
            <a id="induction"></a>
            ## Drugs that make the liver build more enzyme

            A protein called PXR works as a switch inside liver cells. When a drug flips it,
            the cell makes more CYP3A4, so every medicine that CYP3A4 clears starts leaving
            faster. That is **enzyme induction**. The extra enzyme takes days to fade after
            the last dose, which is the trap in the Blind level. OpenADMET measured how
            strongly {len(_scored):,} compounds flip the switch.
            """
        ),
        _chart,
        mo.md(
            f"""
            Rifampicin, a tuberculosis antibiotic and the textbook example of an inducer, reached
            a pEC50 of {_value('rifampicin'):.2f}. Only {_stronger_than_rifampicin} of the {len(_scored):,}
            compounds flipped the switch harder.
            Ritonavir beats {_percentile('ritonavir'):.0%} of them, so it blocks CYP3A4 and tells
            the liver to make more of it at the same time.
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
        .properties(width=250, height=130)
        .facet(facet=alt.Facet("feature:N", title=None, header=alt.Header(labelColor=INK, labelFontWeight=600, labelFontSize=13, labelAnchor="start")), columns=2)
        .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#E4EAE8", domainColor="#C9D1CE")
        .configure_view(strokeWidth=0)
    )

    _rate = lambda feature, enzyme, group: float(tastes.query("feature == @feature and enzyme == @enzyme and group == @group").hit_rate.iloc[0])
    mo.vstack([
        mo.md(
            r"""
            <a id="tastes"></a>
            ## Four enzymes, four tastes

            Each CYP enzyme has a pocket with its own shape and charge, so each one tends to
            grab a different kind of molecule. Knowing those tastes is how chemists design
            new drugs that avoid them, which is the first and cheapest way of **managing
            interactions**. The chart counts a compound as a blocker when it removed at least
            half of an enzyme's activity in OpenADMET's screen, a result the lab rated
            significant (false discovery rate under 5%). Each feature is found with an RDKit
            substructure search you can read in the code.
            """
        ),
        _chart,
        mo.md(
            f"""
            Basic amines, nitrogen atoms that carry a positive charge in the body, raise the
            share of CYP2D6 blockers from {_rate('Basic amine', 'CYP2D6', 'Without it'):.0%} to
            {_rate('Basic amine', 'CYP2D6', 'With the feature'):.0%}. CYP2D6's pocket holds a
            negatively charged amino acid that pairs with them. Flat slabs of aromatic rings
            favour CYP1A2, which has a narrow, flat pocket.

            Carboxylic acids cut blocking for all four enzymes, including CYP2C9. That enzyme
            is usually described as preferring acids, but that description comes from the
            drugs it breaks down, not the ones that block it. All {len(screen) - unparsed:,} of
            {len(screen):,} screen structures parsed in RDKit.
            """
        ),
        mo.accordion({"Table view": mo.ui.table(tastes.assign(hit_rate=tastes.hit_rate.round(3)), selection=None)}),
    ])
    return


@app.cell(hide_code=True)
def _(inhibition, mo):
    _below = float((inhibition.CYP3A4.dropna() < 4.3).mean())
    mo.md(
        f"""
        <a id="limits"></a>
        ## What the game makes up

        The game is honest about which drug does what and dishonest about how much.

        * **Measured.** Which drugs block, destroy or multiply each enzyme, and the
          compounds and enzymes named on screen, come from OpenADMET's data.
        * **Invented.** The speeds, doses and green bands are tuned so each level plays
          well. A lab potency can't be turned into a real drug level without knowing how
          much free drug circulates, how much of it each enzyme clears, and how much the
          gut removes. None of those are in these files.
        * **Lab conditions.** The screen used 50 micromolar, far above the blood level of
          most medicines, so it flags more blockers than a patient would ever feel.
        * **Censored values.** {_below:.0%} of the CYP3A4 pIC50 values are below 4.3, which
          means the compound barely touched the enzyme within the tested range. Those
          numbers are best read as "weak or none" rather than as exact potencies.
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

    **Data.** OpenADMET's CYP inhibition challenge release and PXR challenge release
    on Hugging Face (Apache-2.0). The trimmed tables in `data/drain/` are rebuilt from
    those files by `build/build_drain_data.py`.

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
