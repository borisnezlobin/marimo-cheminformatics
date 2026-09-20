"""The scene drawing code, as a string the game widget embeds in its `_esm`.

`game_art.js` is a real ES module with named exports, kept in its own file so an
editor can lint and format it. anywidget wants one module string, so the engine
concatenates this source ahead of its own code and calls `makeRenderer` from
there. Reading the file at import time rather than pasting it into Python keeps
one copy of the drawing code.
"""

from pathlib import Path

ART_PATH = Path(__file__).with_name("game_art.js")


def art_module() -> str:
    """The contents of `game_art.js`, for embedding at the top of an `_esm`."""
    return ART_PATH.read_text(encoding="utf-8")


GAME_ART_JS = art_module()
