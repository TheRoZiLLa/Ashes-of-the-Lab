"""
health_bar.py - Renders an HP bar above an entity.

Draws two overlapping rectangles:
  background (dark) → full width
  foreground (green→red) → proportional to current HP
"""

import pygame
from engine.settings import (
    HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT, HEALTH_BAR_OFFSET_Y,
    COL_HP_FULL, COL_HP_EMPTY, COL_HP_BACK,
)


def lerp_color(a: tuple, b: tuple, t: float) -> tuple:
    """Linear interpolate between two RGB colours."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_health_bar(
    surface: pygame.Surface,
    camera,
    entity,                     # any object with .rect and .health (HealthComponent)
    width:  int = HEALTH_BAR_WIDTH,
    height: int = HEALTH_BAR_HEIGHT,
) -> None:
    """
    Draw a health bar centred above `entity`.

    Parameters
    ----------
    surface : Target pygame surface.
    camera  : Camera instance for world→screen transform.
    entity  : Entity with a `.rect` and `.health` HealthComponent.
    width   : Bar pixel width.
    height  : Bar pixel height.
    """
    ratio = entity.health.ratio
    screen_rect = camera.apply(entity.rect)

    # Position bar centred above the entity's screen rect
    bar_x = screen_rect.centerx - width // 2
    bar_y = screen_rect.top - HEALTH_BAR_OFFSET_Y - height

    # Background
    bg_rect = pygame.Rect(bar_x, bar_y, width, height)
    pygame.draw.rect(surface, COL_HP_BACK, bg_rect)

    # Foreground – colour shifts from green (full) to red (empty)
    fg_width = max(0, int(width * ratio))
    fg_rect  = pygame.Rect(bar_x, bar_y, fg_width, height)
    fg_color = lerp_color(COL_HP_EMPTY, COL_HP_FULL, ratio)
    if fg_width > 0:
        pygame.draw.rect(surface, fg_color, fg_rect)

    # Thin border
    pygame.draw.rect(surface, (200, 200, 200), bg_rect, 1)
