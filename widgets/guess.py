"""Guess: the reader predicts the clinic from the plate, one drug at a time.

Each round hands over a laboratory potency and nothing else, and asks how much
that drug raises another drug's exposure in a real person. The reader drags a
marker along a fold-change scale and locks it in. The published human figure
then travels out from where they left their marker to where it actually sits,
so the size of the error is a distance they watch open up rather than a second
number to compare. A straight line fitted to the other four drugs answers the
same question at the same moment, and the scoreboard above the round keeps the
running comparison.

Python supplies `rounds` and is never asked a question mid-game, so the whole
thing plays in a static export. `guesses` and `revealed` sync back for a
notebook that wants to talk about what the reader did.
"""

import anywidget
import traitlets

from ._theme import JS_PRELUDE, stylesheet

_CSS = stylesheet("""
.guess__head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 10px 24px;
  margin-bottom: 10px;
}

.guess__progress { display: flex; align-items: center; gap: 8px; }
.guess__pips { display: flex; gap: 5px; }

.guess__pip {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: var(--sunk);
}

.guess__pip--done { background: var(--ink-2); }
.guess__pip--now { background: var(--accent); transform: scale(1.18); }
.guess__count { font-size: 13px; color: var(--ink-2); }

.guess__score { display: flex; gap: 22px; margin: 0; }
.guess__score div { display: grid; gap: 0; justify-items: end; }
.guess__score dt { font-size: 12.5px; color: var(--ink-2); }
.guess__score dd {
  margin: 0;
  font-family: var(--num);
  font-variant-numeric: tabular-nums;
  font-size: 17px;
  font-weight: 600;
}

.guess__score .guess__lead dd { color: var(--accent); }

.guess__card {
  background: var(--card);
  border-radius: var(--r-outer);
  box-shadow: var(--lift);
  padding: 18px;
  margin-bottom: 12px;
}

.guess__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px 18px;
  margin-bottom: 6px;
}

.guess__drug { font-size: 22px; font-weight: 600; line-height: 1.2; }

.guess__plate {
  display: inline-flex;
  align-items: baseline;
  gap: 7px;
  padding: 3px 11px;
  border-radius: var(--r-pill);
  background: var(--sunk);
  font-size: 12.5px;
  color: var(--ink-2);
}

.guess__plate b {
  font-family: var(--num);
  font-variant-numeric: tabular-nums;
  font-size: 15px;
  color: var(--ink);
}

.guess__blurb { font-size: 13.5px; color: var(--ink-2); max-width: 68ch; margin-bottom: 20px; }

.guess__instrument { position: relative; height: 86px; }

.guess__rail { position: absolute; left: 13px; right: 13px; top: 0; bottom: 0; }

.guess__groove {
  position: absolute;
  left: -13px;
  right: -13px;
  top: 51px;
  height: 10px;
  border-radius: var(--r-pill);
  background: var(--sunk);
}

.guess__gap {
  position: absolute;
  top: 51px;
  height: 10px;
  border-radius: var(--r-pill);
  background: var(--accent-soft);
  transition: left 620ms cubic-bezier(0.2, 0.8, 0.25, 1),
              width 620ms cubic-bezier(0.2, 0.8, 0.25, 1);
}

.guess__slider {
  -webkit-appearance: none;
  appearance: none;
  position: absolute;
  left: 0;
  right: 0;
  top: 39px;
  width: 100%;
  height: 34px;
  background: none;
  cursor: grab;
}

.guess__slider:active { cursor: grabbing; }
.guess__slider::-webkit-slider-runnable-track { height: 34px; background: none; }
.guess__slider::-moz-range-track { height: 34px; background: none; }

.guess__slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 26px;
  height: 26px;
  margin-top: 4px;
  border-radius: 50%;
  background: var(--ink);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
}

.guess__slider::-moz-range-thumb {
  width: 26px;
  height: 26px;
  border: 0;
  border-radius: 50%;
  background: var(--ink);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
}

.guess__slider[disabled] { cursor: default; }
.guess__slider[disabled]::-webkit-slider-thumb { background: var(--ink-2); }
.guess__slider[disabled]::-moz-range-thumb { background: var(--ink-2); }

.guess__bubble {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  padding: 3px 10px;
  border-radius: var(--r-pill);
  background: var(--ink);
  color: var(--bg);
  font-family: var(--num);
  font-variant-numeric: tabular-nums;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  pointer-events: none;
}

.guess__mark {
  position: absolute;
  top: 12px;
  transform: translateX(-50%);
  display: grid;
  justify-items: center;
  gap: 2px;
  font-size: 11.5px;
  color: var(--ink-2);
  white-space: nowrap;
  pointer-events: none;
  transition: left 620ms cubic-bezier(0.2, 0.8, 0.25, 1);
}

.guess__mark b {
  font-family: var(--num);
  font-variant-numeric: tabular-nums;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
}

.guess__mark::after { content: ""; width: 2px; height: 30px; background: var(--ink-3); }
.guess__mark--truth { color: var(--accent); }
.guess__mark--truth b { color: var(--accent); }
.guess__mark--truth::after { background: var(--accent); width: 3px; height: 34px; }

.guess__ticks { position: relative; height: 18px; font-size: 12px; color: var(--ink-3); }
.guess__ticks .guess__rail { position: absolute; left: 13px; right: 13px; top: 0; bottom: 0; }

.guess__tick {
  position: absolute;
  transform: translateX(-50%);
  font-family: var(--num);
  font-variant-numeric: tabular-nums;
}

.guess__axis { font-size: 12.5px; color: var(--ink-3); margin-bottom: 16px; }
.guess__act { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
.guess__verdict { font-size: 13.5px; color: var(--ink-2); max-width: 62ch; }
.guess__upnext { font-size: 13px; color: var(--ink-3); }

.guess__done { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }

.guess__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) repeat(3, minmax(58px, auto));
  gap: 4px 20px;
  align-items: baseline;
  background: var(--card);
  border-radius: var(--r-inner);
  box-shadow: var(--lift);
  padding: 9px 14px;
  font-size: 13.5px;
}

.guess__row b {
  font-family: var(--num);
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  display: block;
  text-align: right;
}

.guess__row i {
  font-style: normal;
  color: var(--ink-3);
  font-size: 11.5px;
  display: block;
  text-align: right;
}

@container (max-width: 480px) {
  .guess__row { grid-template-columns: minmax(0, 1fr) repeat(3, auto); gap: 4px 12px; }
  .guess__drug { font-size: 19px; }
}
""")

_ESM = (
    JS_PRELUDE
    + """
const HIGH = 20;
const TICKS = [1, 2, 5, 10, 20];
const STEPS = 400;
const SPAN = Math.log10(HIGH);

const place = (fold) => (Math.log10(Math.min(Math.max(fold, 1), HIGH)) / SPAN) * 100;
const fromStep = (value) => 10 ** ((value / STEPS) * SPAN);
const toStep = (fold) => Math.round((Math.log10(fold) / SPAN) * STEPS);
const show = (fold) => (fold >= 10 ? fold.toFixed(0) : fold.toFixed(1));
const ratio = (a, b) => (a > b ? a / b : b / a);

const median = (values) => {
  const sorted = values.slice().sort((a, b) => a - b);
  if (!sorted.length) return null;
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
};

const errorsOf = (rounds, answers) => {
  const yours = [];
  const lines = [];
  answers.forEach((answer) => {
    const round = rounds.find((r) => r.drug === answer.drug);
    if (!round) return;
    yours.push(ratio(answer.guess_fold, round.truth_fold));
    lines.push(ratio(round.model_fold, round.truth_fold));
  });
  return { yours: median(yours), lines: median(lines) };
};

const scoreMarkup = (rounds, answers, index) => {
  const pips = rounds.map((round, i) => {
    const done = answers.some((a) => a.drug === round.drug);
    const kind = done ? "done" : (i === index ? "now" : "todo");
    return `<span class="guess__pip guess__pip--${kind}"></span>`;
  }).join("");
  const { yours, lines } = errorsOf(rounds, answers);
  const score = yours === null ? "" : `<dl class="guess__score">
      <div class="${yours <= lines ? "guess__lead" : ""}"><dt>You are out by</dt>
        <dd>${yours.toFixed(2)}x</dd></div>
      <div class="${lines < yours ? "guess__lead" : ""}"><dt>The line is out by</dt>
        <dd>${lines.toFixed(2)}x</dd></div>
    </dl>`;
  return `<div class="guess__head">
      <div class="guess__progress">
        <span class="guess__pips">${pips}</span>
        <span class="guess__count">${answers.length} of ${rounds.length} played</span>
      </div>
      ${score}
    </div>`;
};

const verdict = (round, guessFold) => {
  const you = ratio(guessFold, round.truth_fold);
  const line = ratio(round.model_fold, round.truth_fold);
  const head = `The published figure is ${show(round.truth_fold)} times.`;
  if (you < line) {
    return `${head} You were out by a factor of ${you.toFixed(2)} and the fitted line was out `
      + `by ${line.toFixed(2)}, so you beat it on this drug.`;
  }
  if (you > line) {
    return `${head} You were out by a factor of ${you.toFixed(2)} and the fitted line was out `
      + `by ${line.toFixed(2)}.`;
  }
  return `${head} You and the fitted line were both out by ${you.toFixed(2)}.`;
};

const ticks = () => `<div class="guess__rail">${TICKS
  .map((t) => `<span class="guess__tick" style="left:${place(t).toFixed(2)}%">${t}</span>`)
  .join("")}</div>`;

const roundCard = (round, answer, upNext) => {
  const revealed = Boolean(answer);
  const start = revealed ? place(answer.guess_fold) : 0;
  return `<div class="guess__card">
    <div class="guess__meta">
      <p class="guess__drug">${esc(round.drug)}</p>
      <p class="guess__plate">against the enzyme, pIC50 <b>${esc(String(round.pic50))}</b></p>
    </div>
    ${round.blurb ? `<p class="guess__blurb">${esc(round.blurb)}</p>` : ""}
    <div class="guess__instrument">
      <div class="guess__groove"></div>
      <div class="guess__rail">
        <div class="guess__gap" style="left:${start.toFixed(2)}%;width:0%"></div>
        ${revealed ? `<div class="guess__mark guess__mark--line"
            style="left:${start.toFixed(2)}%">the line <b>${show(round.model_fold)}</b></div>` : ""}
        ${revealed ? `<div class="guess__mark guess__mark--truth"
            style="left:${start.toFixed(2)}%">published <b>${show(round.truth_fold)}</b></div>`
          : ""}
        <div class="guess__bubble">2.0 times</div>
      </div>
      <label class="sr" for="guess-slider">How many times does ${esc(round.drug)} raise the
        other drug's exposure</label>
      <input class="guess__slider" id="guess-slider" type="range" min="0" max="${STEPS}"
             step="1" ${revealed ? "disabled" : ""}>
    </div>
    <div class="guess__ticks">${ticks()}</div>
    <p class="guess__axis">Times more of the other drug ends up in the blood. Each equal step
      along the scale doubles it.</p>
    <div class="guess__act">
      ${revealed
        ? `<button class="btn-solid guess__next" type="button">${
            upNext ? `Next drug, ${esc(upNext)}` : "See the whole round"}</button>`
        : `<button class="btn-solid guess__lock" type="button">Lock this in</button>`}
      ${revealed ? `<p class="guess__verdict">${esc(verdict(round, answer.guess_fold))}</p>` : ""}
    </div>
  </div>
  ${!revealed && upNext ? `<p class="guess__upnext">After this one, ${esc(upNext)}.</p>` : ""}`;
};

const doneMarkup = (rounds, answers) => {
  if (!answers.length) return "";
  const rows = answers.map((answer) => {
    const round = rounds.find((r) => r.drug === answer.drug) || {};
    return `<li class="guess__row">
      <span>${esc(answer.drug)}</span>
      <span><i>you</i><b>${show(answer.guess_fold)}</b></span>
      <span><i>the line</i><b>${show(round.model_fold)}</b></span>
      <span><i>published</i><b>${show(round.truth_fold)}</b></span>
    </li>`;
  }).join("");
  return `<h2>Every round so far</h2><ul class="guess__done">${rows}</ul>`;
};

const finished = (rounds, answers) => {
  const { yours, lines } = errorsOf(rounds, answers);
  const verdictLine = yours <= lines
    ? `You finished closer to the published figures than the fitted line did.`
    : `The fitted line finished closer to the published figures than you did.`;
  return `<div class="guess__card">
    <p class="guess__drug">${esc(verdictLine)}</p>
    <p class="guess__blurb">Each line was fitted to the other four drugs and then asked about
      the one it had not seen, so the numbers in its column are predictions rather than
      descriptions. Five points are far too few to claim that this works in general. They are
      enough to show that the number measured on a plate and the number measured in people are
      talking about the same event.</p>
    <button class="btn-solid guess__again" type="button">Play the five again</button>
  </div>`;
};

export default {
  render({ model, el, signal }) {
    const root = document.createElement("div");
    root.className = "w guess";
    root.innerHTML = `
      <section class="sect">
        <h2>Predict the person from the plate</h2>
        <div class="guess__board"></div>
        <div class="guess__now"></div>
      </section>
      <section class="sect guess__log"></section>
    `;
    el.appendChild(root);
    const unbindTheme = bindTheme(root, model);

    const boardBox = root.querySelector(".guess__board");
    const nowBox = root.querySelector(".guess__now");
    const logBox = root.querySelector(".guess__log");

    let rounds = (model.get("rounds") || []).filter((r) => r && r.drug);
    let answers = (model.get("guesses") || []).filter((g) => g && g.drug);
    let pending = toStep(2);
    let arriving = null;

    const answerFor = (drug) => answers.find((a) => a.drug === drug) || null;
    const nextRound = () => rounds.find((r) => !answerFor(r.drug)) || null;
    let showing = nextRound();

    const publish = () => {
      model.set("guesses", answers.map((a) => ({ ...a })));
      model.set("revealed", answers.map((a) => a.drug));
      model.save_changes();
    };

    const moveBubble = (fold) => {
      const bubble = nowBox.querySelector(".guess__bubble");
      if (!bubble) return;
      bubble.style.left = `${place(fold).toFixed(2)}%`;
      bubble.textContent = `${show(fold)} times`;
    };

    // The published figure and the line's answer both start where the reader
    // left their marker and travel to where they belong, so the error is a
    // distance that opens up rather than a second number to compare.
    const animateReveal = (round, guessFold) => {
      cancelAnimationFrame(arriving);
      arriving = requestAnimationFrame(() => {
        const truth = nowBox.querySelector(".guess__mark--truth");
        const line = nowBox.querySelector(".guess__mark--line");
        const gap = nowBox.querySelector(".guess__gap");
        if (truth) truth.style.left = `${place(round.truth_fold).toFixed(2)}%`;
        if (line) line.style.left = `${place(round.model_fold).toFixed(2)}%`;
        if (gap) {
          const from = Math.min(place(guessFold), place(round.truth_fold));
          const to = Math.max(place(guessFold), place(round.truth_fold));
          gap.style.left = `${from.toFixed(2)}%`;
          gap.style.width = `${(to - from).toFixed(2)}%`;
        }
      });
    };

    const paint = () => {
      if (!rounds.length) {
        boardBox.innerHTML = "";
        nowBox.innerHTML = `<p class="guess__blurb">No rounds were handed to this game.</p>`;
        logBox.innerHTML = "";
        return;
      }
      const index = showing ? rounds.indexOf(showing) : rounds.length;
      boardBox.innerHTML = scoreMarkup(rounds, answers, index);
      if (!showing) {
        nowBox.innerHTML = finished(rounds, answers);
      } else {
        const answer = answerFor(showing.drug);
        const remaining = rounds.filter((r) => !answerFor(r.drug) && r !== showing);
        nowBox.innerHTML = roundCard(showing, answer, remaining.length
          ? remaining[0].drug : "");
        const slider = nowBox.querySelector(".guess__slider");
        slider.value = String(answer ? toStep(answer.guess_fold) : pending);
        moveBubble(fromStep(Number(slider.value)));
        if (answer) animateReveal(showing, answer.guess_fold);
      }
      logBox.innerHTML = doneMarkup(rounds, answers);
    };

    const onInput = (event) => {
      const slider = event.target.closest(".guess__slider");
      if (!slider || slider.disabled) return;
      pending = Number(slider.value);
      moveBubble(fromStep(pending));
    };

    const onClick = (event) => {
      if (event.target.closest(".guess__lock") && showing) {
        answers = answers.concat([{ drug: showing.drug, guess_fold: fromStep(pending) }]);
        paint();
        publish();
        return;
      }
      if (event.target.closest(".guess__next")) {
        showing = nextRound();
        pending = toStep(2);
        paint();
        return;
      }
      if (event.target.closest(".guess__again")) {
        answers = [];
        showing = nextRound();
        pending = toStep(2);
        paint();
        publish();
      }
    };

    const onRounds = () => {
      rounds = (model.get("rounds") || []).filter((r) => r && r.drug);
      showing = nextRound();
      paint();
    };

    paint();
    root.addEventListener("input", onInput, { signal });
    root.addEventListener("click", onClick, { signal });
    model.on("change:rounds", onRounds);

    signal.addEventListener("abort", () => {
      cancelAnimationFrame(arriving);
      unbindTheme();
      model.off("change:rounds", onRounds);
      el.innerHTML = "";
    });
  },
};
"""
)


class Guess(anywidget.AnyWidget):
    """Five drugs, one prediction each, with a fitted line as the opponent.

    In from Python: `rounds`, `theme`. Back to Python: `guesses`, `revealed`.
    """

    _esm = _ESM
    _css = _CSS

    rounds = traitlets.List(traitlets.Dict()).tag(sync=True)
    guesses = traitlets.List(traitlets.Dict()).tag(sync=True)
    revealed = traitlets.List(traitlets.Unicode()).tag(sync=True)
    theme = traitlets.Unicode("").tag(sync=True)
