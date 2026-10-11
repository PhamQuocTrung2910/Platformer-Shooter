"""assets.py - loads every image and sound once, when the game starts.

Loading a file from disk is slow, so we do it here a single time and every
other file just imports the ready-made surfaces (e.g. bullet_image).
Everything below the helper functions runs automatically on import.
"""
import os
import re

import pygame

from settings import TILE_SIZE, TILE_TYPES, PLAYER_GUNS


def load_image(path, scale=1, size=None):
    """Load an image with per-pixel alpha.

    scale : multiply the original width/height by this factor
    size  : (width, height) tuple to scale to exactly (overrides scale)
    """
    # convert_alpha() converts the image to the display's pixel format
    # (faster to draw) while keeping transparency.
    image = pygame.image.load(path).convert_alpha()
    if size is not None:
        # Exact size wins over scale
        image = pygame.transform.scale(image, size)
    elif scale != 1:
        image = pygame.transform.scale(
            image, (int(image.get_width() * scale), int(image.get_height() * scale)))
    return image


_frame_cache = {}   # (path, scale) -> frames. Enemies of the same type share one set of images


def load_frames(path, scale=1):
    """Load an animation folder: every file named <number>.png, in numeric order.

    Other files (sheet previews, Thumbs.db, etc.) are ignored, and a missing or
    empty folder gives a clear error message instead of an obscure crash."""
    key = (path, scale)
    if key in _frame_cache:
        return list(_frame_cache[key])
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Animation folder not found: {path}")
    # re.fullmatch keeps only names like "0.png", "12.png" (digits then .png)
    names = [n for n in os.listdir(path) if re.fullmatch(r'\d+\.png', n)]
    if not names:
        raise FileNotFoundError(f"No numbered .png frames (0.png, 1.png, ...) in: {path}")
    # Sort by the NUMBER, not the text, so 10.png comes after 2.png (not before it)
    names.sort(key=lambda n: int(n.split('.')[0]))
    frames = [load_image(f'{path}/{n}', scale) for n in names]
    _frame_cache[key] = frames
    return list(frames)


# ---------------------------------------------------------------------------
# Music & sounds
# ---------------------------------------------------------------------------
def start_music():
    pygame.mixer.music.load('audio/music2.mp3')
    pygame.mixer.music.set_volume(0.3)
    # -1 = loop forever, 0.0 = start from the beginning, 5000 = fade in over 5 seconds
    pygame.mixer.music.play(-1, 0.0, 5000)


jump_sound = pygame.mixer.Sound('audio/jump.wav')
jump_sound.set_volume(0.3)
gun_shot_sound = pygame.mixer.Sound('audio/gunshot.wav')
gun_shot_sound.set_volume(0.3)
grenade_sound = pygame.mixer.Sound('audio/grenade.wav')
grenade_sound.set_volume(0.3)

# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------
# Button images
start_image = load_image('images/Menu/start_button.png')
exit_image = load_image('images/Menu/exit_button.png')
restart_image = load_image('images/Menu/restart_button.png')
# Full-window main menu picture (800 x 730: covers the game area AND the HUD strip)
menu_background_image = load_image('images/Menu/menu_background.png')

# Background layers, back to front: (image, parallax_speed, gap_from_bottom).
# Smaller speed = looks farther away. A gap of None pins the layer to the top of the screen.
# To add a theme: add an entry here, a colour in settings.BACKGROUND_COLOURS,
# and assign it to a level in settings.LEVEL_THEMES.
BACKGROUNDS = {
    'forest': [
        (load_image('images/Background/forest/sky_cloud.png'), 0.5, None),
        (load_image('images/Background/forest/mountain.png'),  0.6, 300),
        (load_image('images/Background/forest/pine1.png'),     0.7, 150),
        (load_image('images/Background/forest/pine2.png'),     0.8, 0),
    ],
    'lab': [
        (load_image('images/Background/lab/wall.png'),     0.5,  None),
        (load_image('images/Background/lab/windows.png'),  0.6,  250),
        (load_image('images/Background/lab/machines.png'), 0.75, 0),
    ],
}

# Tiles: image_list[n] is the picture for tile number n in the level CSV,
# all scaled to exactly TILE_SIZE x TILE_SIZE.
# 0-22 forest + markers, 23-28 effect blocks, 29-43 lab blocks (all in images/Tile/)
image_list = [load_image(f'images/Tile/{tile_num}.png', size=(TILE_SIZE, TILE_SIZE))
              for tile_num in range(TILE_TYPES)]

# Scientist Flask - Enemy
flask_image = load_image('images/icons/flask.png', 1.65)

# Bullet and grenade
bullet_image = load_image('images/icons/bullet.png')
grenade_image = load_image('images/icons/grenade.png')

# Pick up boxes: looked up by name in objects.ItemBox
item_boxes = {
    'Health': load_image('images/icons/health_box.png'),
    'Ammo': load_image('images/icons/ammo_box.png'),
    'Grenade': load_image('images/icons/grenade_box.png'),
    'Magazine': load_image('images/icons/magazine.png'),
    'Syringe': load_image('images/icons/syringe.png'),
    'MutatedStimulant': load_image('images/icons/mutated_stimulant.png'),
    'Stimulant': load_image('images/icons/stimulant.png'),
}

# Weapon icons (HUD): normal copy for the current weapon, faded copy for the others
weapon_icons = {}
faded_weapon_icons = {}
for weapon_name in PLAYER_GUNS:
    weapon_icon = load_image(f'images/icons/weapon_{weapon_name}.png')
    weapon_icons[weapon_name] = weapon_icon
    # Make the faded version: copy the icon, then multiply its alpha channel
    # by 110/255 so it becomes semi-transparent
    faded_icon = weapon_icon.copy()
    faded_icon.fill((255, 255, 255, 110), special_flags=pygame.BLEND_RGBA_MULT)
    faded_weapon_icons[weapon_name] = faded_icon