"""
game.py - Core game loop and top-level coordinator.

Responsibilities:
  - Initialise Pygame and create the window
  - Run the fixed-timestep game loop at 60 FPS
  - Orchestrate update and draw calls for all subsystems
  - Handle game-over / respawn state
"""

import sys
import pygame
from engine.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, BACKGROUND_COLOR
from engine.core.input    import InputManager
from engine.core.camera   import Camera
from engine.world.level   import Level, build_demo_level
from engine.entities.player import Player
from engine.ui.debug_ui   import DebugUI
from engine.ui.player_hud import HealthSystem as PlayerHUD
from engine.ui.pause_menu import PauseMenu


class Game:
    """
    Top-level game manager.

    Creates and owns:
      - Pygame window + clock
      - InputManager
      - Level (platforms + enemies)
      - Player
      - Camera
      - DebugUI
    """

    def __init__(self):
        pygame.init()
        self._screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self._clock  = pygame.time.Clock()

        from engine.settings import CAMERA_ZOOM
        self._world_width = int(SCREEN_WIDTH / CAMERA_ZOOM)
        self._world_height = int(SCREEN_HEIGHT / CAMERA_ZOOM)
        self._world_surface = pygame.Surface((self._world_width, self._world_height))

        self._input  = InputManager()
        self._debug  = DebugUI()
        self.show_debug  = False
        self.show_hud_bg = True
        # Syringe-style life HUD (persists across level reloads, reset on restart)
        self._hud    = PlayerHUD()
        self._pause_menu = PauseMenu()

        self._load_level()

    # ── Level / reset ─────────────────────────────────────────────────────────
    def _load_level(self) -> None:
        self._level  = build_demo_level()
        self._player = Player(*self._level.player_spawn)
        self._camera = Camera(self._level.width, self._level.height, self._world_width, self._world_height)
        self._hud.reset()          # restore lives + hit counter on restart

    # ── Main loop ─────────────────────────────────────────────────────────────
    def run(self) -> None:
        """Enter the game loop. Blocks until the window is closed."""
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        
        while True:
            # --- Real elapsed time (capped to avoid spiral-of-death) ---------
            raw_ms = self._clock.tick(FPS)
            dt     = min(raw_ms / 1000.0, 0.05)  # cap at 50ms

            # --- Input --------------------------------------------------------
            self._input.update()
            if self._input.quit_requested:
                pygame.quit()
                sys.exit()
                
            if self._input.just_pressed(pygame.K_F5):
                self.show_hud_bg = not self.show_hud_bg
                
            if self._input.just_pressed(pygame.K_F6):
                self.show_debug = not self.show_debug
                
            if self._input.just_pressed(pygame.K_ESCAPE):
                if not self._hud.game_over:
                    self._pause_menu.toggle()
                    if self._pause_menu.is_active:
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    else:
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)

            if self._hud.game_over:
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)
                if self._input.just_pressed(pygame.K_r):
                    self._load_level()
                # Still draw so the YOU DIED overlay is visible
                self._draw(dt)
                continue

            # Pause Menu logic
            if self._pause_menu.is_active:
                self._pause_menu.update(self._input)
                self._draw(0.0) # Draw with dt=0 to freeze animations
                continue

            # --- Update -------------------------------------------------------
            self._update(dt)

            # --- Draw ---------------------------------------------------------
            self._draw(dt)

    # ── Update ────────────────────────────────────────────────────────────────
    def _update(self, dt: float) -> None:
        # Prune dead enemies first
        self._level.enemies = [e for e in self._level.enemies if not e.dead]

        # Player
        self._player.update(
            dt,
            self._input,
            self._level.platforms,
            self._level.enemies,
        )

        # Tally new enemy hits → feed into HUD
        for _ in range(self._player.weapons.hits_this_frame):
            self._hud.add_hit()
            self._camera.start_shake(0.2, 5.0)

        if self._player.weapons.wants_screen_shake:
            self._camera.start_shake(0.1, 4.0)

        # Check if player was hurt this frame
        if self._player.was_hit_this_frame:
            self._hud.take_damage()
            self._camera.start_shake(0.3, 10.0)
            self._player.was_hit_this_frame = False

        # Enemies
        for enemy in self._level.enemies:
            enemy.update(dt, self._player, self._level.platforms)

        # Camera follows player
        ambient = 1.5 if self._hud.lives == 1 and not self._hud.game_over else 0.0
        self._camera.update(
            self._player.rect, dt,
            facing=self._player.facing,
            velocity=self._player.velocity,
            is_dashing=self._player._dashing,
            ambient_shake=ambient
        )

    # ── Draw ──────────────────────────────────────────────────────────────────
    def _draw(self, dt: float) -> None:
        self._world_surface.fill(BACKGROUND_COLOR)

        # World geometry
        self._level.draw(self._world_surface, self._camera)

        # Enemies
        for enemy in self._level.enemies:
            enemy.draw(self._world_surface, self._camera)

        # Player
        self._player.draw(self._world_surface, self._camera)

        # Scale and draw world to screen
        pygame.transform.scale(self._world_surface, (SCREEN_WIDTH, SCREEN_HEIGHT), self._screen)

        # Syringe life HUD (top-left, shakes on damage, draws game-over overlay)
        self._hud.draw(
            self._screen, dt, 
            show_bg_text=self.show_hud_bg, 
            camera_dx=self._camera.dx, camera_dy=self._camera.dy,
            weapon_mgr=self._player.weapons
        )

        # Debug overlay
        if self.show_debug:
            self._debug.draw(self._screen, self._clock, self._player, self._level.enemies)

        self._pause_menu.draw(self._screen)

        pygame.display.flip()
