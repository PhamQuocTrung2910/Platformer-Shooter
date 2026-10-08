import pygame
from pygame import mixer

mixer.init()
pygame.init()

# ---------------------------------------------------------------------------
# Game constants
# ---------------------------------------------------------------------------
GRAVITY = 0.75
SCROLL_THRESHOLD = 200
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
ROWS = 16
COLUMNS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 22  # tile 21 = zombie spawn marker
MAX_LEVELS = 3
MAX_FALL_SPEED = 10
ENEMY_BULLET_DAMAGE = 5
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
PLAYER_GUNS = ['pistol', 'rifle', 'shotgun']
PLAYER_START_AMMO = {'pistol': 20, 'rifle': 30, 'shotgun': 8}
ENEMY_GUNS = ['rifle']
ENEMY_START_AMMO = {'rifle': 5}
ANIMATION_TYPES = ['Idle', 'Run', 'Jump', 'Death']

# ---------------------------------------------------------------------------
# Colours
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
HUD_X = 10
SLOT_WIDTH = 98
SLOT_HEIGHT = 40
SLOT_GAP = 6
SLOT_Y = 40
HUD_WIDTH = 3 * SLOT_WIDTH + 2 * SLOT_GAP

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
ZOMBIE_PATROL_FRAMES = TILE_SIZE * 2
ZOMBIE_DROP_CHANCES = {'MutatedStimulant': 0.25}

# ---------------------------------------------------------------------------
# Mutated stimulant (player buff picked up from zombies)
# ---------------------------------------------------------------------------
STIM_DURATION = 20000         # ms
STIM_DRAIN_INTERVAL = 1000    # ms between health ticks
STIM_DRAIN_AMOUNT = 1         # health lost per tick (can kill the player)
STIM_SPEED_MULT = 1.4         # player speed 5 becomes 7
STIM_FIRE_RATE_MULT = 1.5     # shortens the cooldown between shots