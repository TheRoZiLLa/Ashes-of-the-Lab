"""
combat_system.py - Handles attack hitbox creation and hit detection.

The player calls CombatSystem.begin_attack() which spawns a temporary
hitbox. Each frame, CombatSystem.update() checks whether any enemy
overlaps the active hitbox, applies damage + knockback, and removes the
hitbox once its timer expires.
"""

import pygame
from engine.settings import (
    ATTACK_DAMAGE, ATTACK_DURATION, ATTACK_COOLDOWN,
    ATTACK_RANGE, ATTACK_HEIGHT,
    ATTACK_KNOCKBACK_X, ATTACK_KNOCKBACK_Y,
)
from engine.core.timer import Timer


class AttackHitbox:
    """A short-lived rectangular hitbox spawned by the player's attack."""

    def __init__(self, rect: pygame.Rect, direction: int):
        self.rect      = rect
        self.direction = direction          # +1 right / -1 left
        self.timer     = Timer(ATTACK_DURATION, auto_start=True)
        self.hit_ids: set = set()          # track which enemies were already hit

    @property
    def active(self) -> bool:
        return not self.timer.expired


class CombatSystem:
    """
    Manages the player's attack lifecycle.

    Typical usage (on player):
        self.combat = CombatSystem()
        # When attack button pressed:
        self.combat.begin_attack(self.rect, self.facing)
        # Every frame:
        self.combat.update(dt, enemies)
    """

    def __init__(self):
        self._hitbox: AttackHitbox | None = None
        self._cooldown = Timer(ATTACK_COOLDOWN)
        # Tally of enemies hit this frame (read and cleared by game.py)
        self.hits_this_frame: int = 0

    # ── Public API ───────────────────────────────────────────────────────────
    def begin_attack(self, owner_rect: pygame.Rect, direction: int) -> bool:
        """
        Try to start an attack.

        Returns True if the attack was launched (i.e. not on cooldown).
        direction: +1 = facing right, -1 = facing left.
        """
        if not self._cooldown.expired:
            return False

        # Position hitbox to the side the player is facing
        if direction >= 0:
            hx = owner_rect.right
        else:
            hx = owner_rect.left - ATTACK_RANGE

        hy = owner_rect.centery - ATTACK_HEIGHT // 2
        hitbox_rect = pygame.Rect(hx, hy, ATTACK_RANGE, ATTACK_HEIGHT)
        self._hitbox = AttackHitbox(hitbox_rect, direction)
        
        self._cooldown.reset()
        return True

    def update(self, dt: float, enemies: list) -> None:
        """Tick timers and check enemy collisions."""
        self._cooldown.update(dt)

        if self._hitbox is None:
            return

        self._hitbox.timer.update(dt)

        if self._hitbox.active:
            self._check_hits(enemies)
        else:
            self._hitbox = None

    def _check_hits(self, enemies: list) -> None:
        for enemy in enemies:
            if enemy.dead:
                continue
            eid = id(enemy)
            if eid in self._hitbox.hit_ids:
                continue
            if self._hitbox.rect.colliderect(enemy.rect):
                self._hitbox.hit_ids.add(eid)
                self.hits_this_frame += 1   # signal for HUD hit counter
                # Apply damage
                enemy.health.take_damage(ATTACK_DAMAGE)
                if enemy.health.is_dead:
                    enemy.die()
                else:
                    # Knockback
                    kx = ATTACK_KNOCKBACK_X * self._hitbox.direction
                    enemy.velocity[0] = kx
                    enemy.velocity[1] = ATTACK_KNOCKBACK_Y
                    enemy.receive_knockback()

    # ── Draw (debug / visual feedback) ───────────────────────────────────────
    def draw(self, surface: pygame.Surface, camera) -> None:
        """Draw the active hitbox as a semi-transparent rectangle."""
        if self._hitbox is None or not self._hitbox.active:
            return
        screen_rect = camera.apply(self._hitbox.rect)
        # Draw semi-transparent flash overlay
        surf = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
        alpha = int(180 * (1.0 - self._hitbox.timer.progress))
        surf.fill((255, 220, 60, alpha))
        surface.blit(surf, screen_rect.topleft)
        pygame.draw.rect(surface, (255, 255, 100), screen_rect, 2)

    @property
    def can_attack(self) -> bool:
        return self._cooldown.expired

    @property
    def is_attacking(self) -> bool:
        return self._hitbox is not None and self._hitbox.active
