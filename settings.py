"""settings.py - constants and one-time setup.

Every number you might want to tweak (gravity, weapon stats, zombie health...)
lives here, so you can balance the game without touching any game logic.
This file also starts pygame and creates the window, clock and fonts, which
every other file imports from here.
"""
import os

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
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)   # 640: height of the GAME area
HUD_HEIGHT = 90                # extra strip ABOVE the game area for health, weapons, grenades and status
ROWS = 16                      # tile rows in a level
COLUMNS = 150                  # tile columns in a level
TILE_SIZE = SCREEN_HEIGHT // ROWS         # size of one square tile in pixels (40)
TILE_TYPES = 44                # tiles 0-43 (see TILE_NAMES at the bottom)
MAX_LEVELS = 4
MAX_FALL_SPEED = 10            # terminal velocity so falling never gets too fast
ENEMY_BULLET_DAMAGE = 5        # soldiers always do this much per bullet
FPS = 60

# ---------------------------------------------------------------------------
# Display and clock
# ---------------------------------------------------------------------------
# The window is the game area plus the HUD strip on top. `screen` is just the game-area
# part of it (its own coordinates start at 0,0), so everything that draws the world works
# unchanged and nothing can overlap the HUD. `hud` is the strip above it.
window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT + HUD_HEIGHT))
screen = window.subsurface((0, HUD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT))
hud = window.subsurface((0, 0, SCREEN_WIDTH, HUD_HEIGHT))
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
BACKGROUND_COLOUR = (144, 201, 120)   # menu screen
# Which background set each level uses (levels not listed fall back to 'forest')
LEVEL_THEMES = {1: 'lab', 2: 'forest', 3: 'forest', 4: 'lab'}
# Fill colour shown behind the background layers of each theme
BACKGROUND_COLOURS = {'forest': (144, 201, 120), 'lab': (25, 30, 40)}
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
PIXEL_FONT_PATH = 'fonts/PressStart2P.ttf'   # free from Google Fonts (Press Start 2P)


def make_font(size, pixel_size):
    """Pixel font if the file exists, otherwise the old system font."""
    if os.path.exists(PIXEL_FONT_PATH):
        return pygame.font.Font(PIXEL_FONT_PATH, pixel_size)
    return pygame.font.SysFont('Century Gothic', size)


font = make_font(20, 12)
small_font = make_font(14, 8)
big_font = pygame.font.SysFont('Century Gothic', 60)   # unchanged: "YOU WIN!" is positioned for this size

LOW_AMMO = 5                          # at or below this the ammo number turns red
LOW_AMMO_COLOUR = (235, 65, 54)

# ---------------------------------------------------------------------------
# HUD layout
# ---------------------------------------------------------------------------
HUD_BG_COLOUR = (28, 32, 38)
HUD_LINE_COLOUR = (90, 100, 112)
GRENADE_X = 10                 # left edge of the grenade counter (under the health bar)
HUD_X = 190                    # left edge of the weapon slots
SLOT_WIDTH = 98
SLOT_HEIGHT = 40
SLOT_GAP = 6
SLOT_Y = 8
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
ZOMBIE_SPEED = 0.5              # soldiers use 2
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

# ---------------------------------------------------------------------------
# Scientist
# ---------------------------------------------------------------------------
SCIENTIST_SPEED = ZOMBIE_SPEED / 2
SCIENTIST_HEALTH = 75                          # 75% of the soldier's 100
SCIENTIST_PATROL_FRAMES = ZOMBIE_PATROL_FRAMES * 2   # same distance as a zombie, at half speed
SCIENTIST_THROW_COOLDOWN = 150
SCIENTIST_RELEASE_FRAME = 4
SCIENTIST_DROP_CHANCES = {'Stimulant': 0.20}
FLASK_SPEED = 7
FLASK_VELOCITY_Y = -8
SLUDGE_DURATION = 10000
SLUDGE_FADE_MS = 2000
SLUDGE_TICK_INTERVAL = 500
SLUDGE_TICK_DAMAGE = 2
SLUDGE_GROW_FRAMES = 6
SLUDGE_SPREAD_DELAY = 10

# ---------------------------------------------------------------------------
# Overdose
# ---------------------------------------------------------------------------
OVERDOSE_HEALTH_LOSS = 0.7
OVERDOSE_DURATION = 4000   # ms the player can't move

# ---------------------------------------------------------------------------
# Lab effect tiles (23-28)
# ---------------------------------------------------------------------------
PAD_HITBOX_HEIGHT = 14       # px: pads only trigger when you touch the bottom of their tile
SHOCK_DURATION = 3000        # ms of slowness after touching an electric trap (refreshes while on it)
SHOCK_SPEED_MULT = 0.5       # move speed while shocked
SHOCK_FIRE_RATE_MULT = 0.5   # shooting speed while shocked (cooldown ticks down at half rate)
BOOST_DURATION = 5000        # ms of speed boost from a speed pad
BOOST_SPEED_MULT = 1.3       # move speed while boosted (stacks with a stimulant)
LAUNCHER_VELOCITY = -13.75   # upward speed from a launcher pad: about 3 tiles high (a normal jump is -11, about 2)
CONVEYOR_SPEED = 2           # px per frame a conveyor belt carries you
MEDPAD_HEAL = 2              # health restored per tick while standing on a med pad
MEDPAD_INTERVAL = 500        # ms between med pad ticks

# Names shown in the level editor
TILE_NAMES = {
    0: 'Ground top', 1: 'Ground top (2)', 2: 'Ground top (3)',
    3: 'Ground fill', 4: 'Ground fill (2)', 5: 'Ground fill (3)',
    6: 'Platform (underside)', 7: 'Platform (2)', 8: 'Platform (3)',
    9: 'Water / acid top (kills)', 10: 'Water / acid (kills)',
    11: 'Decoration 1', 12: 'Decoration 2', 13: 'Decoration 3', 14: 'Decoration 4',
    15: 'Player spawn', 16: 'Soldier', 17: 'Ammo box', 18: 'Grenade box',
    19: 'Health box', 20: 'Exit', 21: 'Zombie', 22: 'Scientist',
    23: 'Electric trap (slows)', 24: 'Speed pad (2x speed 5s)', 25: 'Launcher pad (3 tiles up)',
    26: 'Conveyor ->', 27: 'Conveyor <-', 28: 'Med pad (heals)',
    # Lab blocks (same roles as the forest ones, so forest and lab can be mixed in any level)
    29: 'Lab ground top', 30: 'Lab ground top (hazard)', 31: 'Lab ground top (vent)',
    32: 'Lab fill (pipe)', 33: 'Lab fill', 34: 'Lab fill (vent)',
    35: 'Lab platform (truss)', 36: 'Lab platform (posts)', 37: 'Lab platform (pipe)',
    38: 'Acid top (kills)', 39: 'Acid (kills)',
    40: 'Ceiling light', 41: 'Computer console', 42: 'Chemical barrels', 43: 'Hanging wires',
}

# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------
ACTIVE_MARGIN = 100          # px: enemies further than this off-screen are frozen (no AI / physics / drawing)
NEAR_TILE_MARGIN = 200       # px: solid tiles within this of the screen are used for collision (keep > ACTIVE_MARGIN)