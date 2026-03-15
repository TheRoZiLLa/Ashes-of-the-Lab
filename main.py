"""
main.py - Root entry point for the Platformer Engine demo.

Run from the project root:
    python main.py

Controls:
    A / D       – Move left / right
    Space / W   – Jump (press again in air = double jump)
    Left Shift  – Dash
    Left Mouse  – Attack
    R           – Restart (after game over)
"""

import sys
import os

# Ensure the project root is on sys.path so `engine.*` imports resolve.
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine.core.game import Game

if __name__ == "__main__":
    game = Game()
    game.run()
