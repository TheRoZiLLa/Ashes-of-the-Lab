"""
debug_ui.py - On-screen debug overlay.

Displays engine telemetry in the top-left corner:
  - FPS
  - Player world position
  - Player current HP / max HP
  - Number of enemies alive
  - Active input hints

If Pygame supports it, uses a monospaced font for clarity.
"""

import pygame
from engine.settings import COL_DEBUG_TEXT, SCREEN_WIDTH


class DebugUI:
    """
    Renders a one-frame debug panel to the top-left of the screen.

    Call `draw()` at the end of each frame, after all game objects are drawn.
    """

    _FONT_SIZE = 18
    _LINE_H    = 22
    _MARGIN_X  = 12
    _MARGIN_Y  = 10

    def __init__(self):
        pygame.font.init()
        # Prefer a monospaced font; fall back to SysFont
        self._font = pygame.font.SysFont("Consolas,Courier New,monospace", self._FONT_SIZE)

    # ── Draw ─────────────────────────────────────────────────────────────────
    def draw(
        self,
        surface: pygame.Surface,
        clock:   pygame.time.Clock,
        player,
        enemies: list,
    ) -> None:
        fps      = clock.get_fps()
        px, py   = player.rect.topleft
        hp       = player.health.current_hp
        max_hp   = player.health.max_hp
        n_alive  = sum(1 for e in enemies if not e.dead)
        dashing  = "DASH" if player._dashing else ""
        invic    = "I-FRAME" if player.is_invincible else ""
        
        # Determine if attacking based on current weapon
        attacking = ""
        weap = player.weapons.active_weapon
        if hasattr(weap, "_hitbox") and weap._hitbox is not None and weap._hitbox.active:
            attacking = "ATK"
        elif hasattr(weap, "_muzzle_flash_timer") and not weap._muzzle_flash_timer.expired:
            attacking = "ATK"

        lines = [
            f"FPS      : {fps:5.1f}",
            f"Player   : ({px:5d}, {py:5d})",
            f"HP       : {hp} / {max_hp}",
            f"Enemies  : {n_alive}",
            f"State    : {dashing} {attacking} {invic}".strip(),
            "",
            "[A/D] Move  [Space] Jump  [Shift] Dash  [LMB] Attack",
        ]

        # Draw a semi-transparent background panel
        panel_w  = 420
        panel_h  = len(lines) * self._LINE_H + self._MARGIN_Y * 2
        panel    = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        surface.blit(panel, (self._MARGIN_X - 4, self._MARGIN_Y - 4))

        for i, line in enumerate(lines):
            col = (160, 160, 160) if line.startswith("[") else COL_DEBUG_TEXT
            text_surf = self._font.render(line, True, col)
            y = self._MARGIN_Y + i * self._LINE_H
            surface.blit(text_surf, (self._MARGIN_X, y))
