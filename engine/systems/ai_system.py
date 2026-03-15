"""
ai_system.py - Simple finite state machine AI for enemies.

States:
    IDLE   – stands still, watches for the player
    CHASE  – walks toward the player
    ATTACK – swings when adjacent to the player

Transitions are driven by distance to the player.
"""

from enum import Enum, auto
from engine.settings import (
    ZOMBIE_CHASE_RANGE, ZOMBIE_ATTACK_RANGE,
    ZOMBIE_ATTACK_DAMAGE, ZOMBIE_ATTACK_COOLDOWN,
    ZOMBIE_SPEED,
)
from engine.core.timer import Timer


class AIState(Enum):
    IDLE   = auto()
    CHASE  = auto()
    ATTACK = auto()


class ZombieAI:
    """
    Finite state machine controller for the Zombie enemy.

    Parameters
    ----------
    enemy : The Zombie entity this AI drives.
    """

    def __init__(self, enemy):
        self.enemy  = enemy
        self.state  = AIState.IDLE
        self._attack_cooldown = Timer(ZOMBIE_ATTACK_COOLDOWN)

    # ── Per-frame update ─────────────────────────────────────────────────────
    def update(self, dt: float, player) -> None:
        """Evaluate state machine and drive enemy velocity."""
        self._attack_cooldown.update(dt)

        if self.enemy.is_stunned:
            return   # in knockback – don't override velocity

        dx = player.rect.centerx - self.enemy.rect.centerx
        dy = player.rect.centery - self.enemy.rect.centery
        dist_x = abs(dx)
        dist_y = abs(dy)

        # ── State transitions ────────────────────────────────────────────────
        # Only engage if the player is roughly on the same vertical level
        # (e.g., within 1.5x the enemy's height)
        vertical_range = self.enemy.rect.height * 1.5

        if dist_x <= ZOMBIE_ATTACK_RANGE and dist_y <= vertical_range:
            self.state = AIState.ATTACK
        elif dist_x <= ZOMBIE_CHASE_RANGE and dist_y <= vertical_range:
            self.state = AIState.CHASE
        else:
            self.state = AIState.IDLE

        # ── State actions ────────────────────────────────────────────────────
        if self.state == AIState.IDLE:
            self._apply_idle()
        elif self.state == AIState.CHASE:
            self._apply_chase(dx)
        elif self.state == AIState.ATTACK:
            self._apply_attack(player)

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _apply_idle(self) -> None:
        self.enemy.velocity[0] = 0.0

    def _apply_chase(self, dx: float) -> None:
        direction = 1 if dx > 0 else -1
        self.enemy.velocity[0] = ZOMBIE_SPEED * direction
        self.enemy.facing = direction

    def _apply_attack(self, player) -> None:
        # Stop moving while attacking
        self.enemy.velocity[0] = 0.0
        if self._attack_cooldown.expired:
            player.health.take_damage(ZOMBIE_ATTACK_DAMAGE)
            player.receive_hit()
            self._attack_cooldown.reset()
