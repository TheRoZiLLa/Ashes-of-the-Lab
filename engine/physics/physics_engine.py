"""
physics_engine.py - Applies gravity and integrates velocity each frame.

This is intentionally kept simple: a single PhysicsEngine.step() call
applies gravity, clamps terminal velocity, then delegates collision
resolution to collision.py.
"""

import pygame
from engine.settings import GRAVITY, TERMINAL_VELOCITY
from engine.physics.collision import resolve_aabb, CollisionResult
from typing import List


class PhysicsEngine:
    """
    Stateless physics processor.

    Call `step()` once per entity per frame to advance its physics.
    """

    def step(
        self,
        rect:      pygame.Rect,
        velocity:  list,            # [vx, vy] – mutated in-place
        obstacles: List[pygame.Rect],
        dt:        float,
        apply_gravity: bool = True,
    ) -> CollisionResult:
        """
        Advance physics for one entity over `dt` seconds.

        1. Optionally apply gravity to vy.
        2. Clamp vy to terminal velocity.
        3. Convert velocity to pixel displacement (velocity × dt).
        4. Resolve AABB collisions.

        Parameters
        ----------
        rect      : Entity bounding box (mutated in-place).
        velocity  : [vx, vy] in pixels/second (mutated in-place).
        obstacles : All solid platform rects the entity can collide with.
        dt        : Delta time in seconds.
        apply_gravity : Set False for entities that fly/float.

        Returns
        -------
        CollisionResult indicating which faces were blocked.
        """
        if apply_gravity:
            velocity[1] += GRAVITY * dt
            velocity[1]  = min(velocity[1], TERMINAL_VELOCITY)

        # Scale velocity to per-frame displacement before resolving
        frame_velocity = [velocity[0] * dt, velocity[1] * dt]
        result = resolve_aabb(rect, frame_velocity, obstacles)

        # reflect any zeroing back into the persistent velocity list
        if frame_velocity[0] == 0 and velocity[0] != 0:
            velocity[0] = 0
        if frame_velocity[1] == 0 and velocity[1] != 0:
            velocity[1] = 0

        return result
