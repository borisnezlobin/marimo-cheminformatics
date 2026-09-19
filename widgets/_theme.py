"""Shared design tokens and base rules for the notebook's two custom widgets.

Everything visual that both widgets use lives here so a change lands in one
file. marimo mounts an anywidget inside a shadow root, so these rules are
scoped to a `.w` root element rather than to the document, and the dark
palette is written twice on purpose: once behind `prefers-color-scheme` for a
reader who never touches the theme control, and once behind the `data-theme`
attribute the widget sets from the `theme` trait. An empty `theme` follows the
reader's own setting; "light" or "dark" pins the widget to that palette.

`@import` is silently dropped inside an anywidget stylesheet, so no font is
fetched. Body text uses the reader's own interface font.
"""

TOKENS = """
.w {
  --bg: #f6f5f3;
  --card: #ffffff;
  --sunk: #eceae6;
  --ink: #17171a;
  --ink-2: #56555e;
  --ink-3: #7b7a83;
  --hair: rgba(20, 20, 25, 0.12);
  --hatch: rgba(20, 20, 25, 0.13);
  --accent: #b3450f;
  --accent-soft: rgba(179, 69, 15, 0.13);
  --lift: 0 1px 2px rgba(20, 20, 25, 0.07), 0 5px 16px rgba(20, 20, 25, 0.05);
  --ui: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --num: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  --r-outer: 14px;
  --r-inner: 9px;
  --r-pill: 999px;
  --step: 180ms cubic-bezier(0.2, 0.7, 0.3, 1);
}

@media (prefers-color-scheme: dark) {
  .w:not([data-theme="light"]) {
    --bg: #141416;
    --card: #1e1e21;
    --sunk: #292930;
    --ink: #f3f2f0;
    --ink-2: #a9a8b1;
    --ink-3: #85848d;
    --hair: rgba(255, 255, 255, 0.14);
    --hatch: rgba(255, 255, 255, 0.2);
    --accent: #ff8f55;
    --accent-soft: rgba(255, 143, 85, 0.17);
    --lift: 0 1px 2px rgba(0, 0, 0, 0.45), 0 6px 22px rgba(0, 0, 0, 0.35);
  }
}

.w[data-theme="dark"] {
  --bg: #141416;
  --card: #1e1e21;
  --sunk: #292930;
  --ink: #f3f2f0;
  --ink-2: #a9a8b1;
  --ink-3: #85848d;
  --hair: rgba(255, 255, 255, 0.14);
  --hatch: rgba(255, 255, 255, 0.2);
  --accent: #ff8f55;
  --accent-soft: rgba(255, 143, 85, 0.17);
  --lift: 0 1px 2px rgba(0, 0, 0, 0.45), 0 6px 22px rgba(0, 0, 0, 0.35);
}
"""

BASE = """
.w {
  font-family: var(--ui);
  font-size: 14px;
  line-height: 1.55;
  color: var(--ink);
  background: var(--bg);
  border-radius: var(--r-outer);
  padding: 18px;
  container-type: inline-size;
  -webkit-font-smoothing: antialiased;
}

.w *, .w *::before, .w *::after { box-sizing: border-box; }

.w h2 {
  font-size: 17px;
  font-weight: 600;
  line-height: 1.3;
  margin: 0 0 10px;
  color: var(--ink);
}

.w h3 { font-size: 15px; font-weight: 600; line-height: 1.35; margin: 0; }
.w p { margin: 0; }
.w .muted { color: var(--ink-2); font-size: 13px; }
.w .num { font-family: var(--num); font-variant-numeric: tabular-nums; }
.w .sect + .sect { margin-top: 22px; }

.w button, .w input {
  font-family: inherit;
  font-size: 14px;
  color: inherit;
}

.w button {
  cursor: pointer;
  border: 0;
  background: none;
  transition: background var(--step), color var(--step), transform var(--step);
}

.w button:active { transform: translateY(1px); }

.w :focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.w .btn-solid {
  min-height: 36px;
  padding: 0 15px;
  border-radius: var(--r-inner);
  background: var(--ink);
  color: var(--bg);
  font-weight: 550;
}

.w .btn-solid:hover { background: var(--ink-2); }

.w .btn-quiet {
  min-width: 34px;
  min-height: 34px;
  border-radius: var(--r-inner);
  color: var(--ink-2);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.w .btn-quiet:hover { background: var(--sunk); color: var(--ink); }

.w .card {
  background: var(--card);
  border-radius: var(--r-outer);
  box-shadow: var(--lift);
  padding: 14px 15px;
}

.w .pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  background: var(--sunk);
  color: var(--ink-2);
  font-size: 12.5px;
  line-height: 1.5;
  white-space: nowrap;
}

.w .sr {
  position: absolute;
  width: 1px; height: 1px;
  margin: -1px; padding: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

@media (prefers-reduced-motion: reduce) {
  .w *, .w *::before, .w *::after {
    transition-duration: 1ms !important;
    animation-duration: 1ms !important;
  }
}
"""


JS_PRELUDE = """
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => (
  { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
));

// Returns the function that detaches the listener again, for the abort handler.
const bindTheme = (root, model) => {
  const apply = () => {
    const theme = model.get("theme");
    if (theme === "light" || theme === "dark") root.setAttribute("data-theme", theme);
    else root.removeAttribute("data-theme");
  };
  apply();
  model.on("change:theme", apply);
  return () => model.off("change:theme", apply);
};

"""


def stylesheet(extra: str) -> str:
    """Tokens, base rules, then one widget's own rules."""
    return TOKENS + BASE + extra
