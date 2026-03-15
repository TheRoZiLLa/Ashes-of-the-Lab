"""
timer.py - Lightweight timer / countdown utilities.

Usage:
    t = Timer(duration=0.5)
    t.update(dt)
    if t.expired:
        ...
    t.reset()
"""


class Timer:
    """Counts down from `duration` to 0. Reports completion via `expired`."""

    def __init__(self, duration: float, auto_start: bool = False):
        self.duration = duration
        self._elapsed = duration  # starts as "already expired"
        if auto_start:
            self.reset()

    # ── Public API ──────────────────────────────────────────────────────────
    def reset(self, new_duration: float = None) -> None:
        """Restart the timer (optionally with a new duration)."""
        if new_duration is not None:
            self.duration = new_duration
        self._elapsed = 0.0

    def update(self, dt: float) -> None:
        """Advance the timer by `dt` seconds. Call every frame."""
        if self._elapsed < self.duration:
            self._elapsed += dt

    @property
    def expired(self) -> bool:
        """True when the full duration has elapsed."""
        return self._elapsed >= self.duration

    @property
    def remaining(self) -> float:
        """Seconds remaining until expiry (0 if already expired)."""
        return max(0.0, self.duration - self._elapsed)

    @property
    def progress(self) -> float:
        """Normalised 0→1 progress (1 = fully elapsed)."""
        if self.duration == 0:
            return 1.0
        return min(1.0, self._elapsed / self.duration)
