"""
level_from_file.py  –  Level builder that reads from a map_editor export.

Drop this into engine/world/ alongside level.py.
Then in your game.py, swap:

    from engine.world.level import build_demo_level
    ...
    self._level = build_demo_level()

for:
    from engine.world.level_from_file import build_level_from_file
    ...
    self._level = build_level_from_file("export_map.json")

If the file is missing, it falls back to build_demo_level() automatically.
"""

import json
import os
import pygame
from engine.world.platform import Platform
from engine.entities.enemy  import Zombie
from engine.settings import SCREEN_WIDTH, SCREEN_HEIGHT


def build_level_from_file(path: str = "export_map.json"):
    """
    Factory: load a JSON map exported by map_editor.py and return a Level.

    Falls back to the procedural demo level if the file is not found.
    """
    if not os.path.exists(path):
        print(f"[Level] '{path}' not found – falling back to demo level.")
        from engine.world.level import build_demo_level
        return build_demo_level()

    with open(path) as f:
        data = json.load(f)

    return FileLevel(data)


class FileLevel:
    """
    A Level whose geometry and spawns come from a JSON file.

    Attributes mirror engine.world.level.Level so Game works unchanged.
    """

    def __init__(self, data: dict):
        world_info         = data.get("world", {})
        self.width         = world_info.get("width",  6400)
        self.height        = world_info.get("height", 1440)
        self.platforms: list = []
        self.enemies:   list = []

        # ── Player spawn ──────────────────────────────────────────────────────
        ps = data.get("player_spawn")
        if ps:
            self.player_spawn = (ps["x"], ps["y"])
        else:
            # Sensible default if designer forgot to place one
            self.player_spawn = (100, self.height - 200)
            print("[Level] Warning: no player_spawn in map file – using default.")

        # ── Platforms ─────────────────────────────────────────────────────────
        platform_color = (80, 70, 100)          # matches COL_PLATFORM in settings
        for p in data.get("platforms", []):
            self.platforms.append(
                Platform(p["x"], p["y"], p["w"], p["h"], platform_color)
            )

        # ── Ground sections ───────────────────────────────────────────────────
        ground_color = (60, 55, 80)
        for g in data.get("ground", []):
            self.platforms.append(
                Platform(g["x"], g["y"], g["w"], g["h"], ground_color)
            )

        # ── Decorations (non-solid visuals treated as platforms for now) ──────
        deco_color = (88, 155, 88)
        for d in data.get("decorations", []):
            self.platforms.append(
                Platform(d["x"], d["y"], d["w"], d["h"], deco_color)
            )

        # ── Invisible level walls ─────────────────────────────────────────────
        self.platforms.append(Platform(-60, 0, 60, self.height, (0, 0, 0)))
        self.platforms.append(Platform(self.width, 0, 60, self.height, (0, 0, 0)))

        # ── Enemy spawns ──────────────────────────────────────────────────────
        for e in data.get("enemy_spawns", []):
            self.enemies.append(Zombie(e["x"], e["y"]))

        # ── Pickups (stub – extend when pickup system exists) ─────────────────
        for pk in data.get("pickups", []):
            # Currently just logged; wire to your pickup entity when ready
            pass

        print(
            f"[Level] Loaded from file: "
            f"{len(self.platforms)} platforms, "
            f"{len(self.enemies)} enemies, "
            f"spawn @ {self.player_spawn}"
        )

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface, camera) -> None:
        for platform in self.platforms:
            platform.draw(surface, camera)