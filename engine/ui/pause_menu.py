"""
pause_menu.py - In-game pause menu with settings.

Provides a simple overlay with options to resume, change resolution/window mode,
and quit the game.
"""

import pygame
from engine.settings import SCREEN_WIDTH, SCREEN_HEIGHT

class PauseMenu:
    def __init__(self):
        pygame.font.init()
        self._font_title = pygame.font.SysFont("Consolas,Courier New,monospace", 64, bold=True)
        self._font_item = pygame.font.SysFont("Consolas,Courier New,monospace", 32)
        
        self.options = [
            "Resume",
            "Resolution: Windowed",
            "Quit"
        ]
        
        self.resolutions = [
            ("Windowed", 0),
            ("Fullscreen", pygame.FULLSCREEN),
            ("Windowed Fullscreen", pygame.NOFRAME)  # borderless window
        ]
        self.current_res_index = 0
        
        self.selected_index = 0
        self.is_active = False

    def toggle(self):
        self.is_active = not self.is_active
        if self.is_active:
            self.selected_index = 0

    def cycle_resolution(self):
        self.current_res_index = (self.current_res_index + 1) % len(self.resolutions)
        name, _ = self.resolutions[self.current_res_index]
        self.options[1] = f"Resolution: {name}"

    def get_current_display_flags(self):
        _, flags = self.resolutions[self.current_res_index]
        return flags

    def update(self, input_mgr):
        """Handle menu navigation and selection."""
        if not self.is_active:
            return

        if input_mgr.just_pressed(pygame.K_w) or input_mgr.just_pressed(pygame.K_UP):
            self.selected_index = (self.selected_index - 1) % len(self.options)
        elif input_mgr.just_pressed(pygame.K_s) or input_mgr.just_pressed(pygame.K_DOWN):
            self.selected_index = (self.selected_index + 1) % len(self.options)

        if input_mgr.just_pressed(pygame.K_RETURN) or input_mgr.just_pressed(pygame.K_SPACE):
            self._select_option()

    def _select_option(self):
        if self.selected_index == 0:  # Resume
            self.toggle()
        elif self.selected_index == 1:  # Resolution
            self.cycle_resolution()
            # Apply new resolution immediately
            flags = self.get_current_display_flags()
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        elif self.selected_index == 2:  # Quit
            # Just post a quit event to be handled by the main loop
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def draw(self, surface: pygame.Surface):
        """Draw the pause menu overlay."""
        if not self.is_active:
            return

        # Semi-transparent dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Draw Title
        title_surf = self._font_title.render("PAUSED", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        surface.blit(title_surf, title_rect)

        # Draw Options
        start_y = SCREEN_HEIGHT // 2 - 20
        spacing = 50

        for i, option in enumerate(self.options):
            color = (255, 215, 0) if i == self.selected_index else (180, 180, 180)
            text = f"> {option} <" if i == self.selected_index else option
            
            opt_surf = self._font_item.render(text, True, color)
            opt_rect = opt_surf.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * spacing))
            surface.blit(opt_surf, opt_rect)
