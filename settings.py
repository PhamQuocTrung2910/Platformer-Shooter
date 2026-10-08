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
TILE_TYPES = 21
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
    'pistol':  {'cooldown': 20, 'damage': 25, 'bullet_speed': 10, 'pellets': 1,
                'spread': 0.0, 'lifetime': None, 'pickup': 15},
    'rifle':   {'cooldown': 8,  'damage': 15, 'bullet_speed': 14, 'pellets': 1,
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