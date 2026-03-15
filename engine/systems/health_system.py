"""
health_system.py - Manages HP for any entity that has health.

Designed as a mixin/component: attach a HealthComponent to an entity
rather than putting HP logic directly in Entity.

Usage:
    self.health = HealthComponent(max_hp=100)
    self.health.take_damage(25)
    if self.health.is_dead:
        self.die()
"""


class HealthComponent:
    """
    Tracks hit points for a single entity.

    Parameters
    ----------
    max_hp : Maximum (and initial) hit points.
    """

    def __init__(self, max_hp: int):
        self.max_hp     = max_hp
        self.current_hp = max_hp

    # ── Public API ───────────────────────────────────────────────────────────
    def take_damage(self, amount: int) -> int:
        """
        Subtract `amount` from current HP (clamped to 0).

        Returns the actual damage dealt (after clamping).
        """
        actual = min(amount, self.current_hp)
        self.current_hp -= actual
        return actual

    def heal(self, amount: int) -> None:
        """Add HP up to max_hp."""
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    def kill(self) -> None:
        """Set HP to zero immediately."""
        self.current_hp = 0

    @property
    def is_dead(self) -> bool:
        return self.current_hp <= 0

    @property
    def ratio(self) -> float:
        """Current HP as a fraction 0.0 → 1.0."""
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0.0
