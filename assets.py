import pygame

from settings import TILE_SIZE, TILE_TYPES, PLAYER_GUNS


def load_image(path, scale=1, size=None):
    """Load an image with per-pixel alpha.

    scale : multiply the original width/height by this factor
    size  : (width, height) tuple to scale to exactly (overrides scale)
    """
    image = pygame.image.load(path).convert_alpha()
    if size is not None:
        image = pygame.transform.scale(image, size)
    elif scale != 1:
        image = pygame.transform.scale(
            image, (int(image.get_width() * scale), int(image.get_height() * scale)))
    return image


# ---------------------------------------------------------------------------
# Music & sounds
# ---------------------------------------------------------------------------
def start_music():
    pygame.mixer.music.load('audio/music2.mp3')
    pygame.mixer.music.set_volume(0.3)
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

# Background images
pine1_image = load_image('images/Background/pine1.png')
pine2_image = load_image('images/Background/pine2.png')
mountain_image = load_image('images/Background/mountain.png')
sky_image = load_image('images/Background/sky_cloud.png')

# Tiles
image_list = [load_image(f'images/Tile/{tile_num}.png', size=(TILE_SIZE, TILE_SIZE))
              for tile_num in range(TILE_TYPES)]

# Bullet and grenade
bullet_image = load_image('images/icons/bullet.png')
grenade_image = load_image('images/icons/grenade.png')

# Pick up boxes
item_boxes = {
    'Health': load_image('images/icons/health_box.png'),
    'Ammo': load_image('images/icons/ammo_box.png'),
    'Grenade': load_image('images/icons/grenade_box.png'),
}

# Weapon icons (HUD): normal copy for the current weapon, faded copy for the others
weapon_icons = {}
faded_weapon_icons = {}
for weapon_name in PLAYER_GUNS:
    weapon_icon = load_image(f'images/icons/weapon_{weapon_name}.png')
    weapon_icons[weapon_name] = weapon_icon
    faded_icon = weapon_icon.copy()
    faded_icon.fill((255, 255, 255, 110), special_flags=pygame.BLEND_RGBA_MULT)
    faded_weapon_icons[weapon_name] = faded_icon