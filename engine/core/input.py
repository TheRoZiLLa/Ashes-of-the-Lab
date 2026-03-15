"""
input.py - Centralised input manager.

Wraps Pygame's event queue and keyboard/mouse state so that the rest of
the engine never needs to import pygame directly for input queries.

Every frame the game loop must call InputManager.update() BEFORE processing
game logic.
"""

import pygame


class InputManager:
    """
    Centralised input cache updated once per frame.

    Attributes
    ----------
    keys_held   : set[int]  – scancodes currently pressed
    keys_just_pressed  : set[int]  – keys pressed THIS frame
    keys_just_released : set[int]  – keys released THIS frame
    mouse_buttons : tuple[bool, bool, bool]  – L / M / R
    mouse_buttons_just_pressed : set[int]   – buttons pressed THIS frame
    mouse_pos   : tuple[int, int]
    quit_requested : bool
    """

    def __init__(self):
        self.keys_held: set = set()
        self.keys_just_pressed: set = set()
        self.keys_just_released: set = set()

        self.mouse_buttons: tuple = (False, False, False)
        self.mouse_buttons_just_pressed: set = set()
        self.mouse_pos: tuple = (0, 0)

        self.quit_requested: bool = False

    # ── Frame update ────────────────────────────────────────────────────────
    def update(self) -> None:
        """Process Pygame events and snapshot input state for this frame."""
        self.keys_just_pressed.clear()
        self.keys_just_released.clear()
        self.mouse_buttons_just_pressed.clear()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_requested = True

            elif event.type == pygame.KEYDOWN:
                self.keys_held.add(event.key)
                self.keys_just_pressed.add(event.key)

            elif event.type == pygame.KEYUP:
                self.keys_held.discard(event.key)
                self.keys_just_released.add(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_buttons_just_pressed.add(event.button)

        self.mouse_buttons = pygame.mouse.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()

    # ── Query helpers ───────────────────────────────────────────────────────
    def is_held(self, key: int) -> bool:
        return key in self.keys_held

    def just_pressed(self, key: int) -> bool:
        return key in self.keys_just_pressed

    def just_released(self, key: int) -> bool:
        return key in self.keys_just_released

    def mouse_just_pressed(self, button: int = 1) -> bool:
        """button: 1=left, 2=middle, 3=right (Pygame convention)."""
        return button in self.mouse_buttons_just_pressed

    def mouse_is_held(self, button: int = 1) -> bool:
        """Check if a mouse button is currently held down. 1=left, 2=middle, 3=right."""
        # pygame.mouse.get_pressed() returns a tuple of 3 bools (L, M, R)
        if 1 <= button <= 3:
            return self.mouse_buttons[button - 1]
        return False
