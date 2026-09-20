"""Custom anywidget components for the plate-or-clinic notebook."""

from .cabinet import Cabinet
from .game import Gauntlet, load_game
from .gate import Gate
from .guess import Guess
from .stereo import StereoEditor

__all__ = ["Cabinet", "Gate", "Gauntlet", "Guess", "StereoEditor", "load_game"]
