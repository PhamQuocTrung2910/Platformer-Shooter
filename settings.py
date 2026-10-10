"""settings.py - constants and one-time setup.

Every number you might want to tweak (gravity, weapon stats, zombie health...)
lives here, so you can balance the game without touching any game logic.
This file also starts pygame and creates the window, clock and fonts, which
every other file imports from here.
"""
import pygame
from pygame import mixer

# Start the sound system and pygame itself. This must happen before we load
# any sounds, fonts or images, which is why it is at the very top.
mixer.init()
pygame.init()

# ---------------------------------------------------------------------------
# Game constants
# ---------------------------------------------------------------------------
GRAVITY = 0.75                 # added to vertical speed every frame
SCROLL_THRESHOLD = 200         # how close (px) the player gets to the screen edge before the world scrolls
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)   # 640
ROWS = 16                      # tile rows in a level
COLUMNS = 150                  # tile columns in a level
TILE_SIZE = SCREEN_HEIGHT // ROWS         # size of one square tile in pixels (40)
TILE_TYPES = 22  # tile 21 = zombie spawn marker
MAX_LEVELS = 3
MAX_FALL_SPEED = 10            # terminal velocity so falling never gets too fast
ENEMY_BULLET_DAMAGE = 5        # soldiers always do this much per bullet
FPS = 60

# ---------------------------------------------------------------------------
# Display and clock
# ---------------------------------------------------------------------------
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ben's Third Game")
clock = pygame.time.Clock()  # Used for frame rate

# ---------------------------------------------------------------------------
# Weapons
# ---------------------------------------------------------------------------
# cooldown     : frames between shots
# damage       : damage per bullet (pellet) when fired by the player
# bullet_speed : pixels per frame
# pellets      : bullets fired per shot
# spread       : max vertical drift per frame for each pellet
# lifetime     : frames before a bullet disappears (None = until it leaves screen)
# pickup       : ammo gained from one ammo box
WEAPONS = {
    'pistol':  {'cooldown': 20, 'damage': 35, 'bullet_speed': 10, 'pellets': 1,
                'spread': 0.0, 'lifetime': None, 'pickup': 15},
    'rifle':   {'cooldown': 10,  'damage': 15, 'bullet_speed': 14, 'pellets': 1,
                'spread': 0.2, 'lifetime': None, 'pickup': 30},
    'shotgun': {'cooldown': 45, 'damage': 12, 'bullet_speed': 11, 'pellets': 5,
                'spread': 1.5, 'lifetime': 22, 'pickup': 6},
}
PLAYER_GUNS = ['pistol', 'rifle', 'shotgun']              # order = keys 1, 2, 3
PLAYER_START_AMMO = {'pistol': 20, 'rifle': 30, 'shotgun': 8}
ENEMY_GUNS = ['rifle']
ENEMY_START_AMMO = {'rifle': 5}
ANIMATION_TYPES = ['Idle', 'Run', 'Jump', 'Death']        # index in this list = action number

# ---------------------------------------------------------------------------
# Colours (R, G, B)
# ---------------------------------------------------------------------------
BACKGROUND_COLOUR = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)
HUD_ACTIVE_COLOUR = (255, 200, 40)
HUD_INACTIVE_COLOUR = (200, 200, 200)

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
font = pygame.font.SysFont('Century Gothic', 20)
small_font = pygame.font.SysFont('Century Gothic', 14)
big_font = pygame.font.SysFont('Century Gothic', 60)

# ---------------------------------------------------------------------------
# HUD layout
# ---------------------------------------------------------------------------
HUD_X = 10                     # left edge of the weapon HUD
SLOT_WIDTH = 98
SLOT_HEIGHT = 40
SLOT_GAP = 6
SLOT_Y = 40
HUD_WIDTH = 3 * SLOT_WIDTH + 2 * SLOT_GAP   # total width of the three slots

# ---------------------------------------------------------------------------
# Enemy loot drops
# ---------------------------------------------------------------------------
# Each item is rolled separately when an enemy dies (0.0 = never, 1.0 = always)
DROP_CHANCES = {
    'Magazine': 0.30,
    'Syringe': 0.20,
}
MAGAZINE_AMMO_FRACTION = 0.5  # fraction of an ammo box's refill, given to every weapon
SYRINGE_HEAL = 15             # health box heals 25

# ---------------------------------------------------------------------------
# Zombie
# ---------------------------------------------------------------------------
ZOMBIE_SPEED = 1              # soldiers use 2
ZOMBIE_HEALTH = 200           # double the soldier's 100
ZOMBIE_ATTACK_RANGE = 12      # px of claw reach in front of the zombie
ZOMBIE_ATTACK_DAMAGE = 15
ZOMBIE_ATTACK_COOLDOWN = 60   # frames between swings
ZOMBIE_PATROL_FRAMES = TILE_SIZE * 2   # how long a zombie walks before turning round
ZOMBIE_DROP_CHANCES = {'MutatedStimulant': 0.25}

# ---------------------------------------------------------------------------
# Mutated stimulant (player buff picked up from zombies)
# ---------------------------------------------------------------------------
STIM_DURATION = 20000         # ms
STIM_DRAIN_INTERVAL = 1000    # ms between health ticks
STIM_DRAIN_AMOUNT = 1         # health lost per tick (can kill the player)
STIM_SPEED_MULT = 1.4         # player speed 5 becomes 7
STIM_FIRE_RATE_MULT = 1.5     # shortens the cooldown between shots