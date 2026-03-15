"""
collision.py - AABB (Axis-Aligned Bounding Box) collision utilities.

Provides:
    resolve_aabb  – pushes 'mover' out of 'obstacle' and returns which sides
                    collided (top/bottom/left/right).
    get_collisions – returns all obstacles a rect overlaps from a list.
"""

import pygame
from typing import List, Tuple


# ── Data structures ──────────────────────────────────────────────────────────

class CollisionResult:
    """Stores which faces of the mover were blocked this frame."""
    __slots__ = ("top", "bottom", "left", "right")

    def __init__(self):
        self.top    = False
        self.bottom = False
        self.left   = False
        self.right  = False

    def __repr__(self):
        return (f"CollisionResult(top={self.top}, bottom={self.bottom}, "
                f"left={self.left}, right={self.right})")


# ── Core resolution ─────────────────────────────────────────────────────────

def resolve_aabb(
    mover:    pygame.Rect,
    velocity: list,          # [vx, vy]  – mutated in-place
    obstacles: List[pygame.Rect],
) -> CollisionResult:
    """
    Move 'mover' by 'velocity' and push it out of every obstacle.

    Resolution is split into X then Y axes to allow sliding along walls.
    Velocity components are zeroed on collision.

    Parameters
    ----------
    mover     : The entity's world-space Rect (mutated in-place).
    velocity  : [vx, vy] list (mutated in-place).
    obstacles : Solid rectangles in world space.

    Returns
    -------
    CollisionResult with flags for each blocked face.
    """
    result = CollisionResult()

    # ── X axis ──────────────────────────────────────────────────────────────
    mover.x += int(velocity[0])
    for obs in obstacles:
        if mover.colliderect(obs):
            if velocity[0] > 0:          # moving right → push left
                mover.right = obs.left
                result.right = True
            elif velocity[0] < 0:        # moving left → push right
                mover.left = obs.right
                result.left = True
            velocity[0] = 0

    # ── Y axis ──────────────────────────────────────────────────────────────
    mover.y += int(velocity[1])
    for obs in obstacles:
        if mover.colliderect(obs):
            if velocity[1] > 0:          # falling → push up (landing)
                mover.bottom = obs.top
                result.bottom = True
            elif velocity[1] < 0:        # moving up → push down (ceiling)
                mover.top = obs.bottom
                result.top = True
            velocity[1] = 0

    return result


def get_overlapping(
    rect: pygame.Rect,
    candidates: List[pygame.Rect],
) -> List[pygame.Rect]:
    """Return every Rect in `candidates` that overlaps `rect`."""
    return [r for r in candidates if rect.colliderect(r)]
