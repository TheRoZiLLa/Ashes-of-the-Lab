"""
main.py - Entry point for the Platformer Engine demo.

Run with:
    python main.py
        (from the d:/GitHub/Python/game/ directory)
"""

import sys
import os

# Ensure the project root is on sys.path so `engine.*` imports resolve
# regardless of where Python is launched from.
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine.core.game import Game


if __name__ == "__main__":
    game = Game()
    game.run()
