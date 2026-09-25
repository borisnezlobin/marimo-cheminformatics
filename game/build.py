"""Build the Drain game from its sources.

Writes two files from the same code:

* ``game/drain.html``: a standalone page, for playing the game outside marimo.
* ``widgets/drain.js``: the anywidget module the notebook loads.

Run from anywhere: ``python game/build.py``.
"""

import re
from pathlib import Path

GAME = Path(__file__).parent
WIDGETS = GAME.parent / "widgets"
FONT_URL = "https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:wght@400;600;750&display=swap"
NODE_EXPORT = 'if (typeof module !== "undefined") module.exports = { Physics, WORLDS, LEVELS };'

STANDALONE_BOOT = """
const stage = document.querySelector("main.stage");
stage.tabIndex = -1;
mountDrain(stage);
stage.focus({ preventScroll: true });
"""

WIDGET_BOOT = """
function ensureFont() {
  if (document.querySelector("link[data-drain-font]")) return;
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = FONT_URL;
  link.dataset.drainFont = "";
  document.head.append(link);
}

function recordFinish(model, { level, stars, learned }) {
  const progress = { ...(model.get("progress") ?? {}) };
  progress[String(level)] = stars;
  model.set("progress", progress);
  if (learned) model.set("learned", learned);
  model.save_changes();
}

export default {
  render({ model, el }) {
    ensureFont();
    const root = document.createElement("div");
    root.className = "drain";
    root.tabIndex = -1;
    root.innerHTML = `<style>${CSS}</style>${MARKUP}`;
    el.append(root);
    return mountDrain(root, {
      initialBest: model.get("progress") ?? {},
      onFinish: (result) => recordFinish(model, result),
    });
  },
};
"""


def read(name):
    return (GAME / name).read_text()


def script_parts():
    physics = read("physics.js").replace(NODE_EXPORT, "")
    return read("assets.js") + physics + read("game.js")


def split_shell():
    shell = read("drain.src.html")
    style = re.search(r"<style>\n(.*?)</style>", shell, re.S).group(1)
    markup = re.search(r'(<main class="stage">.*?</main>)', shell, re.S).group(1)
    return shell, style, markup


def widget_css(style):
    style = re.sub(r"  @media \(prefers-color-scheme: dark\) \{.*?\n    \}\n  \}\n", "", style, flags=re.S)
    style = re.sub(r'  :root\[data-theme="dark"\] \{.*?\n  \}\n', "", style, flags=re.S)
    style = style.replace(":root {", ".drain {", 1)
    style = style.replace("  body {", "  .drain {", 1)
    style = style.replace("  h1 {", "  .level-heading {", 1)
    return style + """
  .drain {
    border-radius: var(--radius-board);
    padding-block: 20px;
  }
  .drain:focus { outline: none; }
"""


def widget_markup(markup):
    markup = re.sub(r'\s*<details class="about">.*?</details>', "", markup, flags=re.S)
    return markup.replace('<h1 id="level-title">', '<h2 id="level-title" class="level-heading">').replace("</h1>", "</h2>")


def build_standalone(shell):
    script = script_parts() + STANDALONE_BOOT
    page = shell.replace("/*ASSETS*/\n/*PHYSICS*/\n/*GAME*/", script)
    (GAME / "drain.html").write_text(page)
    return len(page)


def build_widget(style, markup):
    module = "\n".join([
        f"const FONT_URL = {FONT_URL!r};",
        f"const CSS = {js_string(widget_css(style))};",
        f"const MARKUP = {js_string(widget_markup(markup))};",
        script_parts(),
        WIDGET_BOOT,
    ])
    (WIDGETS / "drain.js").write_text(module)
    return len(module)


def js_string(text):
    return "`" + text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${") + "`"


if __name__ == "__main__":
    shell, style, markup = split_shell()
    print(f"drain.html {build_standalone(shell) // 1024} KB")
    print(f"widgets/drain.js {build_widget(style, markup) // 1024} KB")
