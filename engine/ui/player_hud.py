"""
player_hud.py - Silksong-style syringe life system HUD for the main engine.

Extracted from health_system_demo.py and adapted for the engine:
  - Uses SCREEN_WIDTH / SCREEN_HEIGHT from engine.settings
  - ASSETS_DIR resolves to  <project_root>/assets/
  - ShakeEffect and HealthSystem live here; import both as needed.

Integration:
    # In Game.__init__:
    from engine.ui.player_hud import HealthSystem as PlayerHUD
    self._hud = PlayerHUD()

    # When player takes a hit (ai_system.py):
    self._hud.take_damage()

    # When player lands a hit on an enemy (combat_system.py):
    self._hud.add_hit()

    # In Game._draw():
    self._hud.draw(self._screen, dt)
"""

import os
import math
import pygame
from engine.settings import SCREEN_WIDTH, SCREEN_HEIGHT

# ── HUD constants ─────────────────────────────────────────────────────────────
MAX_LIVES    = 5
HITS_TO_HEAL = 5

HUD_X, HUD_Y  = -50, 24      # top-left anchor (before shake)

LIFE_ICON_W   = 48
LIFE_ICON_H   = 66
LIFE_SPACING  = 6
ICON_OFFSET_X = 150          # indent from bar left (leaves room for healthBar art)
ICON_OFFSET_Y = 16

# Resolve assets folder relative to the project root (two levels up from this file)
_ENGINE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROJECT_DIR = os.path.dirname(_ENGINE_DIR)
ASSETS_DIR   = os.path.join(_PROJECT_DIR, "assets")


# ── Procedural art helpers ────────────────────────────────────────────────────

def _make_fallback_bar() -> pygame.Surface:
    """Bone-joint dark plate background bar."""
    bar_w = ICON_OFFSET_X * 2 + MAX_LIVES * (LIFE_ICON_W + LIFE_SPACING) - LIFE_SPACING
    bar_h = ICON_OFFSET_Y * 2 + LIFE_ICON_H + 34
    surf  = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)

    pygame.draw.rect(surf, (28, 22, 40, 240), (0, 0, bar_w, bar_h), border_radius=12)

    knob_col = (160, 148, 120)
    for kx, ky in [(0, 0), (bar_w, 0), (0, bar_h), (bar_w, bar_h)]:
        pygame.draw.circle(surf, knob_col, (kx, ky), 10)
        pygame.draw.circle(surf, (200, 190, 160), (kx, ky), 6)

    for stripe_y in [bar_h // 3, bar_h * 2 // 3]:
        pygame.draw.line(surf, (80, 58, 90, 180), (10, stripe_y), (bar_w - 10, stripe_y), 3)

    pygame.draw.rect(surf, (100, 80, 130, 200), (0, 0, bar_w, bar_h), 2, border_radius=12)
    return surf


def _make_fallback_life() -> pygame.Surface:
    """Syringe / vial icon drawn with pygame primitives."""
    W, H   = LIFE_ICON_W, LIFE_ICON_H
    surf   = pygame.Surface((W, H), pygame.SRCALPHA)
    GLASS  = (190, 235, 200, 220)
    GLASS_H= (230, 255, 240, 150)
    BARREL = (180, 170, 140)
    NEEDLE = (200, 200, 210)
    LIQUID = (80, 220, 130, 210)
    RING   = (140, 130, 110)
    cx     = W // 2

    # Needle
    needle_bot = 16
    pygame.draw.polygon(surf, NEEDLE, [(cx, 2), (cx - 2, needle_bot), (cx + 2, needle_bot)])
    pygame.draw.rect(surf, RING, (cx - 5, needle_bot, 10, 5), border_radius=2)

    # Barrel
    barrel_top  = needle_bot + 5
    barrel_bot  = H - 14
    barrel_l, barrel_r = cx - 10, cx + 10
    barrel_rect = pygame.Rect(barrel_l, barrel_top, barrel_r - barrel_l, barrel_bot - barrel_top)
    pygame.draw.rect(surf, GLASS, barrel_rect, border_radius=5)

    liquid_rect = pygame.Rect(barrel_l + 2, barrel_top + 4,
                              barrel_r - barrel_l - 4, barrel_bot - barrel_top - 8)
    pygame.draw.rect(surf, LIQUID, liquid_rect, border_radius=3)

    for i in range(1, 4):
        ty = barrel_top + i * ((barrel_bot - barrel_top) // 4)
        pygame.draw.line(surf, (80, 100, 90, 160), (barrel_l + 2, ty), (barrel_l + 7, ty), 1)

    pygame.draw.rect(surf, GLASS_H,
                     pygame.Rect(barrel_l + 2, barrel_top + 2, 4, barrel_bot - barrel_top - 4),
                     border_radius=2)
    pygame.draw.rect(surf, BARREL, barrel_rect, 2, border_radius=5)

    # Plunger
    grip_y = barrel_bot + 1
    pygame.draw.rect(surf, RING,   (cx - 9, grip_y,     18, 4))
    pygame.draw.rect(surf, BARREL, (cx - 5, grip_y + 4, 10, 6), border_radius=2)
    pygame.draw.rect(surf, RING, (cx - 11, grip_y + 2,  5, 8), border_radius=2)
    pygame.draw.rect(surf, RING, (cx +  6, grip_y + 2,  5, 8), border_radius=2)
    return surf


# ── ShakeEffect ───────────────────────────────────────────────────────────────

class ShakeEffect:
    """Decaying sinusoidal HUD shake. Call trigger() on hit, tick(dt) each frame."""

    def __init__(self, duration: float = 0.50, magnitude: float = 12.0):
        self.duration  = duration
        self.magnitude = magnitude
        self._elapsed  = duration      # start expired

    def trigger(self) -> None:
        self._elapsed = 0.0

    def tick(self, dt: float) -> tuple:
        if self._elapsed >= self.duration:
            return (0, 0)
        self._elapsed += dt
        t     = 1.0 - (self._elapsed / self.duration)
        amp   = self.magnitude * t
        angle = self._elapsed * 60 * math.pi
        return (int(amp * math.sin(angle)), int(amp * math.cos(angle * 0.7)))

    @property
    def active(self) -> bool:
        return self._elapsed < self.duration


# ── HealthSystem ──────────────────────────────────────────────────────────────

class HealthSystem:
    """
    Silksong-style lives HUD with syringe icons and shake on damage.

    Usage
    -----
    hud = HealthSystem()
    hud.take_damage()          # player hit by enemy
    hud.add_hit()              # player hit an enemy
    hud.draw(screen, dt)       # call every frame

    Properties
    ----------
    lives       : int   current lives remaining
    game_over   : bool  True when lives == 0
    """

    def __init__(self):
        self.lives:       int  = MAX_LIVES
        self.hit_counter: int  = 0
        self.game_over:   bool = False

        self._shake = ShakeEffect()
        
        self.parallax_x = 0.0
        self.parallax_y = 0.0

        # Animations
        self.anim_timers = [0.0] * MAX_LIVES
        self.anim_dirs   = [0] * MAX_LIVES

        # Load PNG assets if present, else procedural fallbacks
        self._bar_img    = self._load_bar()
        self._life_full  = self._load_life()
        self._life_empty = self._load_life_empty()
        self._vignette   = self._load_vignette()
        
        # Load weapon PNG assets
        self._gun_img = self._load_image("ok49.png")
        self._knife_img = self._load_image("kinfe.png")
        
        ew, eh = max(1, int(LIFE_ICON_W * 0.85)), max(1, int(LIFE_ICON_H * 0.85))
        self._life_empty_resting = pygame.transform.smoothscale(self._life_empty, (ew, eh))

        pygame.font.init()
        self._font_go    = pygame.font.SysFont("Consolas", 64, bold=True)
        self._font_hint  = pygame.font.SysFont("Consolas", 22)
        self._font_small = pygame.font.SysFont("Consolas", 16)

    # ── API ──────────────────────────────────────────────────────────────────

    def take_damage(self) -> None:
        """Lose 1 life and trigger HUD shake. Ignored during game over."""
        if self.game_over or self.lives == 0:
            return
            
        # Trigger shrink and fade-to-empty animation on the lost life
        slot = self.lives - 1
        if slot >= 0:
            self.anim_timers[slot] = 1.0
            self.anim_dirs[slot] = -1

        self.lives -= 1
        self._shake.trigger()
        if self.lives == 0:
            self.game_over = True

    def add_hit(self) -> None:
        """Register 1 enemy hit. Every HITS_TO_HEAL hits restores 1 life."""
        if self.game_over:
            return
        self.hit_counter += 1
        if self.hit_counter >= HITS_TO_HEAL:
            self.heal()
            self.hit_counter = 0

    def heal(self) -> None:
        """Restore 1 life (capped at MAX_LIVES)."""
        if self.lives < MAX_LIVES:
            # Trigger grow and fade-to-full animation on the gained life
            slot = self.lives
            self.anim_timers[slot] = 1.0
            self.anim_dirs[slot] = 1
            
            self.lives += 1

    def reset(self) -> None:
        """Restore to full health — call this on level restart."""
        self.lives       = MAX_LIVES
        self.hit_counter = 0
        self.game_over   = False

    @property
    def is_dead(self) -> bool:
        return self.game_over

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface, dt: float, 
             show_bg_text: bool = True, 
             camera_dx: float = 0.0, camera_dy: float = 0.0,
             weapon_mgr=None) -> None:
        """Render HUD each frame. `dt` must be in seconds."""
        if dt > 0:
            target_px = -camera_dx * 2.5
            target_py = -camera_dy * 2.5
            
            target_px = max(-20.0, min(20.0, target_px))
            target_py = max(-20.0, min(20.0, target_py))

            t = 1.0 - (1.0 / (1.0 + 12.0 * dt))
            self.parallax_x += (target_px - self.parallax_x) * t
            self.parallax_y += (target_py - self.parallax_y) * t

        sx, sy = self._shake.tick(dt)
        hx = HUD_X + sx + int(self.parallax_x)
        hy = HUD_Y + sy + int(self.parallax_y)

        # Critical health vignette (pulsing)
        if self.lives == 1 and not self.game_over and self._vignette:
            panic_t = pygame.time.get_ticks() / 1000.0
            # Pulse alpha between 80 and 220
            alpha = int(150 + math.sin(panic_t * 6.0) * 70)
            self._vignette.set_alpha(alpha)
            screen.blit(self._vignette, (0, 0))

        # Background bar
        if show_bg_text:
            screen.blit(self._bar_img, (hx, hy))

        # Update animation timers
        for i in range(MAX_LIVES):
            if self.anim_timers[i] > 0:
                self.anim_timers[i] = max(0.0, self.anim_timers[i] - dt * 3.0)  # ~0.33s duration

        # Life icons
        for i in range(MAX_LIVES):
            ix = hx + ICON_OFFSET_X + i * (LIFE_ICON_W + LIFE_SPACING)
            iy = hy + ICON_OFFSET_Y
            
            # Simple continuous "panic" shake if only 1 life remains
            if self.lives == 1 and i == 0 and not self.game_over:
                # Use a fast sine wave for a nervous vibration
                panic_t = pygame.time.get_ticks() / 1000.0
                ix += int(math.sin(panic_t * 90) * 2)
                iy += int(math.cos(panic_t * 105) * 2)
            
            if self.anim_timers[i] > 0:
                t = self.anim_timers[i]
                if self.anim_dirs[i] == -1:
                    # Losing a life: Full shrinks and fades out; Empty grows and fades in
                    progress = 1.0 - t
                    full_alpha  = int(255 * t)
                    empty_alpha = int(255 * progress)
                    full_scale  = 0.85 + 0.15 * t
                    empty_scale = 0.50 + 0.35 * progress

                    # empty grows and fades in
                    if empty_alpha > 0:
                        eh = max(1, int(LIFE_ICON_H * empty_scale))
                        ew = max(1, int(LIFE_ICON_W * empty_scale))
                        emp = pygame.transform.smoothscale(self._life_empty, (ew, eh))
                        emp.set_alpha(empty_alpha)
                        cx, cy = ix + LIFE_ICON_W // 2, iy + LIFE_ICON_H // 2
                        screen.blit(emp, (cx - ew // 2, cy - eh // 2))

                    # full scales down and fades out
                    if full_alpha > 0:
                        fh = max(1, int(LIFE_ICON_H * full_scale))
                        fw = max(1, int(LIFE_ICON_W * full_scale))
                        ful = pygame.transform.smoothscale(self._life_full, (fw, fh))
                        ful.set_alpha(full_alpha)
                        cx, cy = ix + LIFE_ICON_W // 2, iy + LIFE_ICON_H // 2
                        screen.blit(ful, (cx - fw // 2, cy - fh // 2))

                else:
                    # Gaining a life: Empty shrinks and fades out; Full grows and fades in
                    progress = 1.0 - t
                    full_alpha  = int(255 * progress)
                    empty_alpha = int(255 * t)
                    full_scale  = 0.85 + 0.15 * progress
                    empty_scale = 0.50 + 0.35 * t

                    # empty shrinks and fades out
                    if empty_alpha > 0:
                        eh = max(1, int(LIFE_ICON_H * empty_scale))
                        ew = max(1, int(LIFE_ICON_W * empty_scale))
                        emp = pygame.transform.smoothscale(self._life_empty, (ew, eh))
                        emp.set_alpha(empty_alpha)
                        cx, cy = ix + LIFE_ICON_W // 2, iy + LIFE_ICON_H // 2
                        screen.blit(emp, (cx - ew // 2, cy - eh // 2))

                    # full scales up and fades in
                    if full_alpha > 0:
                        fh = max(1, int(LIFE_ICON_H * full_scale))
                        fw = max(1, int(LIFE_ICON_W * full_scale))
                        ful = pygame.transform.smoothscale(self._life_full, (fw, fh))
                        ful.set_alpha(full_alpha)
                        cx, cy = ix + LIFE_ICON_W // 2, iy + LIFE_ICON_H // 2
                        screen.blit(ful, (cx - fw // 2, cy - fh // 2))
            else:
                if i < self.lives:
                    screen.blit(self._life_full, (ix, iy))
                else:
                    ew, eh = self._life_empty_resting.get_size()
                    cx, cy = ix + LIFE_ICON_W // 2, iy + LIFE_ICON_H // 2
                    screen.blit(self._life_empty_resting, (cx - ew // 2, cy - eh // 2))

        # Game-over overlay
        if self.game_over:
            self._draw_game_over(screen)
            
        # Weapon UI
        if weapon_mgr:
            self._draw_weapon_ui(screen, weapon_mgr, int(self.parallax_x), int(self.parallax_y))

    def _draw_weapon_ui(self, screen: pygame.Surface, weapon_mgr, px: int, py: int) -> None:
        """Draw active weapon text and scaled boxes."""
        screen_w = screen.get_width()
        screen_h = screen.get_height()
        
        w_text = weapon_mgr.active_weapon.get_ui_text()
        if w_text:
            text_surf = self._font_hint.render(w_text, True, (240, 240, 240))
            # Bottom left corner
            vx, vy = 20 + px, screen_h - 40 + py
            screen.blit(text_surf, (vx, vy))

        # Draw weapon icons
        box_spacing = 110
        base_x = 70 + px
        base_y = screen_h - 120 + py

        for wid, wname, img in [(1, "GUN", self._gun_img), (2, "KNIFE", self._knife_img)]:
            is_active = (weapon_mgr.active_id == wid)
            scale = 1.3 if is_active else 0.8
            
            # Constrain size to a max of 60x60 base before scaling
            if img:
                iw, ih = img.get_size()
                fit_scale = min(60.0 / iw, 60.0 / ih)
                w = int(iw * fit_scale * scale)
                h = int(ih * fit_scale * scale)
            else:
                w = int(40 * scale)
                h = int(40 * scale)
            
            x = base_x + (wid - 1) * box_spacing
            y = base_y - h // 2
            
            if img:
                scaled_img = pygame.transform.smoothscale(img, (w, h))
                if not is_active:
                    scaled_img.set_alpha(150) # Dim inactive weapon
                screen.blit(scaled_img, (x, y))
            else:
                # Fallback Box
                color = (200, 200, 200) if is_active else (100, 100, 100)
                pygame.draw.rect(screen, color, (x, y, w, h), 2)
            
            # Label below the icon
            color = (240, 240, 240) if is_active else (150, 150, 150)
            lbl = self._font_small.render(wname, True, color)
            screen.blit(lbl, (x + w//2 - lbl.get_width()//2, y + h + 5))

    def _draw_game_over(self, screen: pygame.Surface) -> None:
        screen_w = screen.get_width()
        screen_h = screen.get_height()
        
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        text_surf = self._font_large.render("YOU DIED", True, (255, 50, 50))
        rect = text_surf.get_rect(center=(screen_w // 2, screen_h // 2 - 40))
        screen.blit(text_surf, rect)

        hint_surf = self._font_hint.render("Press 'R' to Restart", True, (200, 200, 200))
        h_rect = hint_surf.get_rect(center=(screen_w // 2, screen_h // 2 + 20))
        screen.blit(hint_surf, h_rect)

    # ── Asset loaders ────────────────────────────────────────────────────────

    @staticmethod
    def _load_bar() -> pygame.Surface:
        path = os.path.join(ASSETS_DIR, "healthBar.png")
        if os.path.exists(path):
            try:
                return pygame.image.load(path).convert_alpha()
            except Exception as e:
                print(f"[PlayerHUD] healthBar.png: {e}")
        return _make_fallback_bar()

    @staticmethod
    def _load_life() -> pygame.Surface:
        path = os.path.join(ASSETS_DIR, "life.png")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(img, (LIFE_ICON_W, LIFE_ICON_H))
            except Exception as e:
                print(f"[PlayerHUD] life.png: {e}")
        return _make_fallback_life()

    @staticmethod
    def _make_empty() -> pygame.Surface:
        surf = _make_fallback_life()
        surf.set_alpha(35)
        return surf

    @staticmethod
    def _load_life_empty() -> pygame.Surface:
        path = os.path.join(ASSETS_DIR, "life_empty.png")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(img, (LIFE_ICON_W, LIFE_ICON_H))
            except Exception as e:
                print(f"[PlayerHUD] life_empty.png: {e}")
        return HealthSystem._make_empty()

    @staticmethod
    def _load_vignette() -> pygame.Surface:
        path = os.path.join(ASSETS_DIR, "vignette.png")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                # Scale to fit the screen
                return pygame.transform.smoothscale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except Exception as e:
                print(f"[PlayerHUD] vignette.png: {e}")
        return None
        
    @staticmethod
    def _load_image(filename: str) -> pygame.Surface | None:
        path = os.path.join(ASSETS_DIR, filename)
        if os.path.exists(path):
            try:
                return pygame.image.load(path).convert_alpha()
            except Exception as e:
                print(f"[PlayerHUD] {filename}: {e}")
        return None
