"""
weapon_system.py - Modular weapon system for the player.

Supports switching between a melee Knife and a ranged Gun.
Handles ammo, reloading, shooting modes, and bullet entities.
"""

import pygame
import math
import random
from engine.core.timer import Timer
from engine.settings import (
    KNIFE_DAMAGE, KNIFE_DURATION, KNIFE_COOLDOWN,
    KNIFE_RANGE, KNIFE_HEIGHT, KNIFE_KNOCKBACK_X, KNIFE_KNOCKBACK_Y,
    GUN_DAMAGE, GUN_FIRE_RATE_SEMI, GUN_FIRE_RATE_AUTO, GUN_MAG_CAPACITY,
    BULLET_SPEED, BULLET_LIFETIME
)

# ── Projectiles ─────────────────────────────────────────────────────────────

class Bullet:
    """A fast-moving projectile fired by the gun."""
    def __init__(self, x: float, y: float, direction: int):
        self.rect = pygame.Rect(x, y - 2, 12, 4)
        self.direction = direction
        self.velocity_x = BULLET_SPEED * direction
        self.timer = Timer(BULLET_LIFETIME, auto_start=True)
        self.dead = False

    def update(self, dt: float, enemies: list, platforms: list) -> bool:
        if self.dead:
            return False
            
        self.timer.update(dt)
        if self.timer.expired:
            self.dead = True
            return False

        # Move
        self.rect.x += self.velocity_x * dt

        # Check collision with platforms
        for p in platforms:
            if self.rect.colliderect(p.rect):
                self.dead = True
                return False

        # Check collision with enemies
        for enemy in enemies:
            if enemy.dead:
                continue
            if self.rect.colliderect(enemy.rect):
                enemy.health.take_damage(GUN_DAMAGE)
                killed = False
                if enemy.health.is_dead:
                    enemy.die()
                    killed = True
                else:
                    enemy.velocity[0] = 150 * self.direction
                    enemy.velocity[1] = -100
                    enemy.receive_knockback()
                self.dead = True
                return killed
        return False

    def draw(self, surface: pygame.Surface, camera) -> None:
        if self.dead:
            return
        screen_rect = camera.apply(self.rect)
        pygame.draw.rect(surface, (255, 255, 150), screen_rect)


# ── Weapons ─────────────────────────────────────────────────────────────────

class Weapon:
    """Base class for all weapons."""
    def __init__(self, name: str):
        self.name = name
        self.wants_screen_shake = False
        self.recoil_impulse = 0.0

    def update(self, dt: float, enemies: list, platforms: list, owner_rect: pygame.Rect, owner_facing: int) -> None:
        pass

    def draw(self, surface: pygame.Surface, camera) -> None:
        pass

    def attack(self, owner_rect: pygame.Rect, owner_facing: int, is_held: bool = False, is_buffed: bool = False) -> bool:
        """Trigger the weapon attack. Returns True if successfully fired/swung."""
        return False
        
    def get_ui_text(self) -> str:
        return ""


class AttackHitbox:
    """A short-lived rectangular hitbox spawned by the melee weapon."""
    def __init__(self, rect: pygame.Rect, direction: int):
        self.rect      = rect
        self.direction = direction
        self.timer     = Timer(KNIFE_DURATION, auto_start=True)
        self.hit_ids: set = set()

    @property
    def active(self) -> bool:
        return not self.timer.expired


class Knife(Weapon):
    """Melee weapon that creates a short-lived hitbox."""
    def __init__(self):
        super().__init__("Knife")
        self._hitbox: AttackHitbox | None = None
        self._cooldown = Timer(KNIFE_COOLDOWN)
        self.hits_this_frame = 0
        self.kills_this_frame = 0

    def attack(self, owner_rect: pygame.Rect, owner_facing: int, is_held: bool = False, is_buffed: bool = False) -> bool:
        if is_held:  # Knife doesn't auto-swing
            return False
        if not self._cooldown.expired:
            return False

        if owner_facing >= 0:
            hx = owner_rect.right
        else:
            hx = owner_rect.left - KNIFE_RANGE

        hy = owner_rect.centery - KNIFE_HEIGHT // 2
        hitbox_rect = pygame.Rect(hx, hy, KNIFE_RANGE, KNIFE_HEIGHT)
        self._hitbox = AttackHitbox(hitbox_rect, owner_facing)
        
        # 10% faster attack speed = 10% shorter cooldown
        cd_multiplier = 0.9 if is_buffed else 1.0
        self._cooldown = Timer(KNIFE_COOLDOWN * cd_multiplier, auto_start=True)
        return True

    def update(self, dt: float, enemies: list, platforms: list, owner_rect: pygame.Rect, owner_facing: int) -> None:
        self._cooldown.update(dt)
        self.hits_this_frame = 0
        self.kills_this_frame = 0

        if self._hitbox is None:
            return
        self._hitbox.timer.update(dt)
        if self._hitbox.active:
            # Move with player
            self._hitbox.direction = owner_facing
            if owner_facing >= 0:
                self._hitbox.rect.left = owner_rect.right
            else:
                self._hitbox.rect.left = owner_rect.left - KNIFE_RANGE
            self._hitbox.rect.centery = owner_rect.centery - KNIFE_HEIGHT // 2

            # Check hits
            for enemy in enemies:
                if enemy.dead: continue
                eid = id(enemy)
                if eid in self._hitbox.hit_ids: continue
                if self._hitbox.rect.colliderect(enemy.rect):
                    self._hitbox.hit_ids.add(eid)
                    self.hits_this_frame += 1
                    enemy.health.take_damage(KNIFE_DAMAGE)
                    if enemy.health.is_dead:
                        enemy.die()
                        self.kills_this_frame += 1
                    else:
                        kx = KNIFE_KNOCKBACK_X * self._hitbox.direction
                        enemy.velocity[0] = kx
                        enemy.velocity[1] = KNIFE_KNOCKBACK_Y
                        enemy.receive_knockback()
        else:
            self._hitbox = None

    def draw(self, surface: pygame.Surface, camera) -> None:
        if self._hitbox is None or not self._hitbox.active:
            return
        screen_rect = camera.apply(self._hitbox.rect)
        surf = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
        alpha = int(180 * (1.0 - self._hitbox.timer.progress))
        surf.fill((255, 220, 60, alpha))
        surface.blit(surf, screen_rect.topleft)
        pygame.draw.rect(surface, (255, 255, 100), screen_rect, 2)


class Gun(Weapon):
    """Ranged weapon that fires bullets and has ammo/reload mechanics."""
    def __init__(self):
        super().__init__("Gun")
        self.mode = 1               # 1 = Semi, 2 = Auto
        self.bullets = []
        
        self.current_bullets = GUN_MAG_CAPACITY
        self.total_bullets = 40
        self.magazines = 5
        
        self._cooldown = Timer(GUN_FIRE_RATE_SEMI)
        self._muzzle_flash_timer = Timer(0.05)
        self._flash_pos = (0, 0)
        self._flash_dir = 1
        self.kills_this_frame = 0
        
    def get_ui_text(self) -> str:
        return f"Mode: {self.mode}   Bullet: {self.current_bullets}/{self.total_bullets}   Mag: {self.magazines}"

    def toggle_mode(self) -> None:
        self.mode = 2 if self.mode == 1 else 1
        rate = GUN_FIRE_RATE_AUTO if self.mode == 2 else GUN_FIRE_RATE_SEMI
        self._cooldown = Timer(rate)
        
    def reload(self) -> None:
        needed = GUN_MAG_CAPACITY - self.current_bullets
        
        # If we have no reserve bullets but do have spare magazines, crack one open
        if self.total_bullets == 0 and needed > 0 and self.magazines > 0:
            self.magazines -= 1
            self.current_bullets = GUN_MAG_CAPACITY
            self.total_bullets = 40
            return
            
        # Draw from the reserve pool to fill the gun
        if self.total_bullets > 0 and self.current_bullets < GUN_MAG_CAPACITY:
            reload_amount = min(needed, self.total_bullets)
            
            self.current_bullets += reload_amount
            self.total_bullets -= reload_amount
            
    def attack(self, owner_rect: pygame.Rect, owner_facing: int, is_held: bool = False, is_buffed: bool = False) -> bool:
        if is_held and self.mode == 1:
            return False  # Semi-auto requires clicking, not holding
            
        if not self._cooldown.expired:
            return False
            
        if self.current_bullets <= 0:
            return False  # Empty mag
            
        # Fire
        self.current_bullets -= 1
        
        # 5% faster attack speed = 5% shorter cooldown
        cd_multiplier = 0.95 if is_buffed else 1.0
        base_rate = GUN_FIRE_RATE_AUTO if self.mode == 2 else GUN_FIRE_RATE_SEMI
        self._cooldown = Timer(base_rate * cd_multiplier, auto_start=True)
        
        bx = owner_rect.right if owner_facing >= 0 else owner_rect.left
        by = owner_rect.centery - 6
        self.bullets.append(Bullet(bx, by, owner_facing))
        
        self.recoil_impulse = -250.0 * owner_facing
        self.wants_screen_shake = True
        
        self._flash_pos = (bx, by)
        self._flash_dir = owner_facing
        self._muzzle_flash_timer.reset()
        
        return True

    def update(self, dt: float, enemies: list, platforms: list, owner_rect: pygame.Rect, owner_facing: int) -> None:
        self._cooldown.update(dt)
        self._muzzle_flash_timer.update(dt)
        self.wants_screen_shake = False
        self.recoil_impulse = 0.0
        self.kills_this_frame = 0
        
        for b in self.bullets:
            if b.update(dt, enemies, platforms):
                self.kills_this_frame += 1
            
        self.bullets = [b for b in self.bullets if not b.dead]
        
    def draw(self, surface: pygame.Surface, camera) -> None:
        for b in self.bullets:
            b.draw(surface, camera)
            
        # Draw muzzle flash
        if not self._muzzle_flash_timer.expired:
            fx, fy = self._flash_pos
            screen_pos = camera.apply_point(fx, fy)
            radius = int(8 * (1.0 - self._muzzle_flash_timer.progress))
            pygame.draw.circle(surface, (255, 255, 200), screen_pos, radius)


# ── Manager ─────────────────────────────────────────────────────────────────

class WeaponManager:
    """Holds the player's weapons and manages switching/updating them."""
    def __init__(self):
        self.weapons = {
            1: Gun(),
            2: Knife()
        }
        self.active_id = 1
        self.kills_this_frame = 0
        
    @property
    def active_weapon(self) -> Weapon:
        return self.weapons[self.active_id]

    # Shared properties mapping to active weapon
    @property
    def hits_this_frame(self) -> int:
        if isinstance(self.active_weapon, Knife):
            return self.active_weapon.hits_this_frame
        return 0

    @property
    def wants_screen_shake(self) -> bool:
        return self.active_weapon.wants_screen_shake
        
    @property
    def recoil_impulse(self) -> float:
        return self.active_weapon.recoil_impulse

    def switch_weapon(self, slot: int) -> None:
        if slot in self.weapons:
            self.active_id = slot
            
    def update(self, dt: float, enemies: list, platforms: list, owner_rect: pygame.Rect, owner_facing: int) -> None:
        # We always update all weapons so bullets keep flying and cooldowns tick
        self.kills_this_frame = 0
        for w in self.weapons.values():
            w.update(dt, enemies, platforms, owner_rect, owner_facing)
            if hasattr(w, 'kills_this_frame'):
                self.kills_this_frame += w.kills_this_frame
            
    def draw(self, surface: pygame.Surface, camera) -> None:
        for w in self.weapons.values():
            w.draw(surface, camera)
