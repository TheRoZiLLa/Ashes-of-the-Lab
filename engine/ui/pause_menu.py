"""
pause_menu.py - In-game pause menu with settings.

Provides a simple overlay with options to resume, change resolution/window mode,
and quit the game.
"""

import pygame
import engine.settings as settings

class PauseMenu:
    def __init__(self):
        pygame.font.init()
        self._font_title = pygame.font.SysFont("Consolas,Courier New,monospace", 64, bold=True)
        self._font_item = pygame.font.SysFont("Consolas,Courier New,monospace", 32)
        
        self.options = [
            "Resume",
            "Windows Type: Windowed",
            f"Resolution: {settings.SCREEN_WIDTH}x{settings.SCREEN_HEIGHT}",
            "Quit"
        ]
        
        self.resolutions = [
            ("Windowed", 0),
            ("Fullscreen", pygame.FULLSCREEN),
            ("Windowed Fullscreen", pygame.NOFRAME)  # borderless window
        ]
        self.current_res_index = 0
        
        self.sizes = [
            (1920, 1080),
            (1600, 900),
            (1280, 720),
            (1024, 768),
            (800, 600)
        ]
        
        # Try to find the initial size index
        self.current_size_index = 0
        for i, (w, h) in enumerate(self.sizes):
            if w == settings.SCREEN_WIDTH and h == settings.SCREEN_HEIGHT:
                self.current_size_index = i
                break
                
        self._update_option_strings()
        
        self.selected_index = 0
        self.is_active = False

    def _update_option_strings(self):
        w_name, _ = self.resolutions[self.current_res_index]
        w, h = self.sizes[self.current_size_index]
        self.options[1] = f"Windows Type: < {w_name} >"
        self.options[2] = f"Resolution: < {w}x{h} >"

    def toggle(self):
        self.is_active = not self.is_active
        if self.is_active:
            self.selected_index = 0

    def cycle_display_mode(self, direction=1):
        self.current_res_index = (self.current_res_index + direction) % len(self.resolutions)
        self._update_option_strings()
        
    def cycle_resolution_size(self, direction=1):
        self.current_size_index = (self.current_size_index + direction) % len(self.sizes)
        self._update_option_strings()

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
            
        # Left/Right cycling for current highlighted option
        direction = 0
        if input_mgr.just_pressed(pygame.K_a) or input_mgr.just_pressed(pygame.K_LEFT):
            direction = -1
        elif input_mgr.just_pressed(pygame.K_d) or input_mgr.just_pressed(pygame.K_RIGHT):
            direction = 1
            
        if direction != 0:
            if self.selected_index == 1:
                self.cycle_display_mode(direction)
            elif self.selected_index == 2:
                self.cycle_resolution_size(direction)

        if input_mgr.just_pressed(pygame.K_RETURN) or input_mgr.just_pressed(pygame.K_SPACE):
            self._select_option()

    def _apply_display_settings(self):
        # Apply the chosen resolution and window mode
        flags = self.get_current_display_flags()
        w, h = self.sizes[self.current_size_index]
        
        # We need to update global constants dynamically (not ideal, but required here)
        import engine.settings as settings
        settings.SCREEN_WIDTH = w
        settings.SCREEN_HEIGHT = h
        
        pygame.display.set_mode((w, h), flags)

    def _select_option(self):
        if self.selected_index == 0:  # Resume
            self.toggle()
        elif self.selected_index == 1:  # Windows Type
            self._apply_display_settings()
        elif self.selected_index == 2:  # Resolution size
            self._apply_display_settings()
        elif self.selected_index == 3:  # Quit
            # Just post a quit event to be handled by the main loop
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def draw(self, surface: pygame.Surface):
        """Draw the pause menu overlay."""
        if not self.is_active:
            return

        screen_w = surface.get_width()
        screen_h = surface.get_height()

        # Semi-transparent dark overlay
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Draw Title
        title_surf = self._font_title.render("PAUSED", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(screen_w // 2, screen_h // 4))
        surface.blit(title_surf, title_rect)

        # Draw Options
        start_y = screen_h // 2 - 20
        spacing = 50

        for i, option in enumerate(self.options):
            color = (255, 215, 0) if i == self.selected_index else (180, 180, 180)
            text = f"> {option} <" if i == self.selected_index else option
            
            opt_surf = self._font_item.render(text, True, color)
            opt_rect = opt_surf.get_rect(center=(screen_w // 2, start_y + i * spacing))
            surface.blit(opt_surf, opt_rect)
