"""
settings.py - Global configuration constants for the game engine.
All tunable values are centralized here for easy tweaking.
"""

# ── Window ─────────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 1920
SCREEN_HEIGHT = 1080
TITLE         = "Ashes of the Lab - Demo"
FPS           = 120
BACKGROUND_COLOR = (15, 12, 20)   # deep dark purple

# Base internal resolution (the game logic and world size are built for this)
BASE_WIDTH = 1280
BASE_HEIGHT = 720

# ── Physics ────────────────────────────────────────────────────────────────
GRAVITY         = 1800            # pixels / s²  (applied every frame)
TERMINAL_VELOCITY = 900           # max fall speed  (px/s)

# ── Player ─────────────────────────────────────────────────────────────────
PLAYER_WIDTH    = 28
PLAYER_HEIGHT   = 48
PLAYER_COLOR    = (100, 180, 255)  # light blue

PLAYER_RUN_SPEED    = 340         # px/s  (max horizontal speed)
PLAYER_ACCELERATION = 2400        # px/s²  (ground acceleration)
PLAYER_FRICTION     = 2000        # px/s²  (ground deceleration when no input)
PLAYER_AIR_ACCEL    = 1200        # px/s²  (reduced air control)
PLAYER_AIR_FRICTION = 600         # px/s²  (light air resistance)

PLAYER_JUMP_SPEED   = -760        # px/s  (negative = upward)
PLAYER_DOUBLE_JUMP_SPEED = -680   # px/s

PLAYER_DASH_SPEED    = 700        # px/s  (horizontal dash impulse)
PLAYER_DASH_DURATION = 0.18       # seconds  (how long dash lasts)
PLAYER_DASH_COOLDOWN = 0.55       # seconds  (time between dashes)

COYOTE_TIME         = 0.12        # seconds after leaving a ledge that jump still works
JUMP_BUFFER_TIME    = 0.12        # seconds before landing that jump input is buffered

PLAYER_MAX_HP  = 100
PLAYER_INVINCIBILITY_DURATION = 0.6  # seconds of i-frames after being hit

# ── Weapons ────────────────────────────────────────────────────────────────
KNIFE_DAMAGE       = 25
KNIFE_DURATION     = 0.15          # seconds  (hitbox lives this long)
KNIFE_COOLDOWN     = 0.35          # seconds
KNIFE_RANGE        = 70            # pixels  (width of hitbox)
KNIFE_HEIGHT       = 36            # pixels  (height of hitbox)
KNIFE_KNOCKBACK_X  = 380           # px/s  (horizontal knockback)
KNIFE_KNOCKBACK_Y  = -250          # px/s  (upward knockback)

GUN_DAMAGE         = 15
GUN_FIRE_RATE_SEMI = 0.2           # seconds per shot
GUN_FIRE_RATE_AUTO = 0.1           # seconds per shot
GUN_MAG_CAPACITY   = 20
BULLET_SPEED       = 1200          # px/s
BULLET_LIFETIME    = 1.0           # seconds

# ── Enemy – Zombie ─────────────────────────────────────────────────────────
ZOMBIE_WIDTH   = 30
ZOMBIE_HEIGHT  = 46
ZOMBIE_COLOR   = (80, 200, 80)    # green

ZOMBIE_MAX_HP       = 60
ZOMBIE_SPEED        = 120         # px/s
ZOMBIE_CHASE_RANGE  = 380         # pixels  (player detection radius)
ZOMBIE_ATTACK_RANGE = 40          # pixels  (melee reach)
ZOMBIE_ATTACK_DAMAGE   = 12
ZOMBIE_ATTACK_COOLDOWN = 1.2      # seconds
ZOMBIE_KNOCKBACK_DURATION = 0.25  # seconds (stun after being hit)

# ── Camera ─────────────────────────────────────────────────────────────────
CAMERA_SMOOTHING = 8.0            # higher = snappier follow
CAMERA_ZOOM = 1.25
CAMERA_LOOKAHEAD_X = 100
CAMERA_LOOKAHEAD_Y_DOWN = 80
CAMERA_LOOKAHEAD_Y_UP = 40
CAMERA_DASH_OFFSET = 150
CAMERA_FOLLOW_INTENSITY = 0.2     # 0.0 = static center, 1.0 = full lookahead (motion sickness setting)

# ── Health Bar ─────────────────────────────────────────────────────────────
HEALTH_BAR_WIDTH   = 50
HEALTH_BAR_HEIGHT  = 6
HEALTH_BAR_OFFSET_Y = 10         # pixels above entity

# ── Colors shared across UI ────────────────────────────────────────────────
COL_HP_FULL    = (60, 220, 100)
COL_HP_EMPTY   = (180, 30, 30)
COL_HP_BACK    = (30, 30, 30)
COL_DEBUG_TEXT = (240, 240, 80)
COL_PLATFORM   = (80, 70, 100)
