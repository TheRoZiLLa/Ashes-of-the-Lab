"""
player.py - Player entity with Hollow Knight-inspired movement feel.

Features:
  - Horizontal movement with acceleration/friction (separate air values)
  - Jump + double-jump
  - Coyote time (jump grace period after walking off a ledge)
  - Jump buffering (queued jump input lands just before touching ground)
  - Dash with cooldown and invincibility window
  - Left-mouse melee attack via CombatSystem
  - Invincibility frames after being hit
"""

import pygame
from engine.entities.entity_base import Entity
from engine.systems.health_system import HealthComponent
from engine.systems.weapon_system import WeaponManager
from engine.physics.physics_engine import PhysicsEngine
from engine.core.timer import Timer
from engine.settings import (
    PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_COLOR,
    PLAYER_RUN_SPEED, PLAYER_ACCELERATION, PLAYER_FRICTION,
    PLAYER_AIR_ACCEL, PLAYER_AIR_FRICTION,
    PLAYER_JUMP_SPEED, PLAYER_DOUBLE_JUMP_SPEED,
    PLAYER_DASH_SPEED, PLAYER_DASH_DURATION, PLAYER_DASH_COOLDOWN,
    COYOTE_TIME, JUMP_BUFFER_TIME,
    PLAYER_MAX_HP, PLAYER_INVINCIBILITY_DURATION,
)


class Player(Entity):
    """
    Player-controlled character.

    Parameters
    ----------
    x, y : Spawn position (top-left of bounding box).
    """

    def __init__(self, x: float, y: float):
        super().__init__(x, y, PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_COLOR)

        # ── Subsystems ───────────────────────────────────────────────────────
        self.health = HealthComponent(PLAYER_MAX_HP)
        self.weapons = WeaponManager()
        self.physics = PhysicsEngine()

        # ── State flags ──────────────────────────────────────────────────────
        self.on_ground    = False
        self.facing       = 1           # +1 right / -1 left
        self._jumps_left  = 2           # resets on landing

        # ── Advanced movement timers ─────────────────────────────────────────
        self._coyote_timer      = Timer(COYOTE_TIME)
        self._jump_buffer_timer = Timer(JUMP_BUFFER_TIME)
        self._dash_timer        = Timer(PLAYER_DASH_DURATION)
        self._dash_cooldown     = Timer(PLAYER_DASH_COOLDOWN)
        self._invincibility_timer = Timer(PLAYER_INVINCIBILITY_DURATION)

        # ── Dash state ───────────────────────────────────────────────────────
        self._dashing        = False
        self._dash_direction = 1

        # ── Signal flags (consumed by game.py each frame) ────────────────────
        self.was_hit_this_frame = False   # set by receive_hit(); cleared in game.py

    # ── Update ───────────────────────────────────────────────────────────────
    def update(self, dt: float, input_mgr, platforms: list, enemies: list) -> None:
        """
        Main per-frame update.

        Parameters
        ----------
        dt        : Delta time in seconds.
        input_mgr : InputManager instance.
        platforms : List of Platform objects.
        enemies   : List of active enemy entities.
        """
        self._update_timers(dt)
        self._handle_input(input_mgr)
        self._apply_movement(dt, platforms)
        self.weapons.update(dt, enemies, platforms, self.rect, self.facing)
        self._check_death()

    def _update_timers(self, dt: float) -> None:
        self._coyote_timer.update(dt)
        self._jump_buffer_timer.update(dt)
        self._dash_timer.update(dt)
        self._dash_cooldown.update(dt)
        self._invincibility_timer.update(dt)

        # End dash when timer expires
        if self._dashing and self._dash_timer.expired:
            self._dashing = False

    def _handle_input(self, input_mgr) -> None:
        import pygame as _pg

        # Horizontal direction
        move_x = 0
        if input_mgr.is_held(_pg.K_a) or input_mgr.is_held(_pg.K_LEFT):
            move_x -= 1
        if input_mgr.is_held(_pg.K_d) or input_mgr.is_held(_pg.K_RIGHT):
            move_x += 1
        if move_x != 0:
            self.facing = move_x
        self._move_x = move_x

        # Jump input
        if input_mgr.just_pressed(_pg.K_SPACE) or input_mgr.just_pressed(_pg.K_w):
            self._jump_buffer_timer.reset()

        # Dash input
        if input_mgr.just_pressed(_pg.K_LSHIFT) or input_mgr.just_pressed(_pg.K_RSHIFT):
            self._try_dash()

        # Weapon switching
        if input_mgr.just_pressed(_pg.K_1):
            self.weapons.switch_weapon(1)
        if input_mgr.just_pressed(_pg.K_2):
            self.weapons.switch_weapon(2)
            
        # Weapon actions
        if input_mgr.just_pressed(_pg.K_f):
            if hasattr(self.weapons.active_weapon, 'toggle_mode'):
                self.weapons.active_weapon.toggle_mode()
        if input_mgr.just_pressed(_pg.K_r):
            if hasattr(self.weapons.active_weapon, 'reload'):
                self.weapons.active_weapon.reload()

        # Attack input (left mouse button)
        fired = False
        if input_mgr.mouse_just_pressed(1):
            fired = self.weapons.active_weapon.attack(self.rect, self.facing, is_held=False)
        elif input_mgr.mouse_is_held(1):
            fired = self.weapons.active_weapon.attack(self.rect, self.facing, is_held=True)
            
        if fired and self.weapons.recoil_impulse != 0:
            self.velocity[0] += self.weapons.recoil_impulse

    def _try_dash(self) -> None:
        if not self._dash_cooldown.expired or self._dashing:
            return
        self._dashing = True
        self._dash_direction = self.facing
        self._dash_timer.reset()
        self._dash_cooldown.reset()
        # Give a burst in facing direction
        self.velocity[0] = PLAYER_DASH_SPEED * self._dash_direction
        self.velocity[1] = 0   # cancel vertical momentum during dash

    def _apply_movement(self, dt: float, platforms: list) -> None:
        obstacle_rects = [p.rect for p in platforms]

        if self._dashing:
            # During dash: lock horizontal velocity, suppress gravity briefly
            self.velocity[0] = PLAYER_DASH_SPEED * self._dash_direction
            result = self.physics.step(self.rect, self.velocity, obstacle_rects, dt,
                                       apply_gravity=False)
        else:
            # Horizontal acceleration / friction
            self._apply_horizontal(dt)
            result = self.physics.step(self.rect, self.velocity, obstacle_rects, dt)

        self.sync_rect()

        # Landing
        if result.bottom:
            self.velocity[1] = 0
            if not self.on_ground:
                # Just landed – restore jumps and dash
                self._jumps_left = 2
            self.on_ground = True
            self._coyote_timer.reset()
        else:
            if self.on_ground:
                # Just left the ground – start coyote window
                self._coyote_timer.reset()
            self.on_ground = False

        # Ceiling bump
        if result.top:
            self.velocity[1] = 0

        # Try to consume buffered jump
        self._try_jump()

    def _apply_horizontal(self, dt: float) -> None:
        target = self._move_x * PLAYER_RUN_SPEED
        accel  = PLAYER_ACCELERATION if self.on_ground else PLAYER_AIR_ACCEL
        fric   = PLAYER_FRICTION      if self.on_ground else PLAYER_AIR_FRICTION

        if self._move_x != 0:
            # Accelerate toward target speed
            diff = target - self.velocity[0]
            self.velocity[0] += min(abs(diff), accel * dt) * (1 if diff > 0 else -1)
        else:
            # Decelerate (friction)
            if abs(self.velocity[0]) < fric * dt:
                self.velocity[0] = 0.0
            else:
                self.velocity[0] -= fric * dt * (1 if self.velocity[0] > 0 else -1)

    def _try_jump(self) -> None:
        if self._jump_buffer_timer.expired:
            return
        can_jump = (
            self.on_ground
            or not self._coyote_timer.expired
            or self._jumps_left > 0
        )
        if not can_jump:
            return

        if self.on_ground or not self._coyote_timer.expired:
            self.velocity[1] = PLAYER_JUMP_SPEED
            self._jumps_left = max(0, self._jumps_left - 1)
        elif self._jumps_left > 0:
            self.velocity[1] = PLAYER_DOUBLE_JUMP_SPEED
            self._jumps_left -= 1

        self._jump_buffer_timer = Timer(JUMP_BUFFER_TIME)  # consume buffer

    def receive_hit(self) -> None:
        """Called when an enemy damages the player. Starts i-frames and flags the hit."""
        if not self._invincibility_timer.expired:
            return   # already invincible – eat the hit
        self._invincibility_timer.reset()
        self.was_hit_this_frame = True

    @property
    def is_invincible(self) -> bool:
        return not self._invincibility_timer.expired

    def _check_death(self) -> None:
        pass   # Death is now managed by the HUD (lives == 0)

    # ── Draw ─────────────────────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface, camera) -> None:
        screen_rect = camera.apply(self.rect)

        # Flash white during invincibility frames
        if self.is_invincible:
            flash_t = self._invincibility_timer.progress
            alpha   = int(200 * abs(1.0 - flash_t * 2 % 2 - 1))
            col = tuple(min(255, c + alpha) for c in self.color)
        else:
            col = self.color

        pygame.draw.rect(surface, col, screen_rect)

        # Draw a small facing indicator (eye / direction dot)
        eye_x = screen_rect.left + (screen_rect.width - 4) if self.facing < 0 else screen_rect.right - 8
        eye_y = screen_rect.top + 10
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, eye_y), 3)

        # Draw active weapon effects/hitboxes
        self.weapons.draw(surface, camera)
