import pygame
from pygame import mixer
from sys import exit
import os
import random
import csv
import button

mixer.init()
pygame.init()

# ---------------------------------------------------------------------------
# Game Variables
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

screen_scroll = 0
background_scroll = 0
level = 1
start_game = False
start_intro = False
game_won = False

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ben's Third Game")

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

# Player Action Variables
moving_left = False
moving_right = False
shooting = False
throwing_grenade = False
grenade_thrown = False

# ---------------------------------------------------------------------------
# Load Music & Sounds
# ---------------------------------------------------------------------------
# Background Music
pygame.mixer.music.load('audio/music2.mp3')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000)

# Sound Effects
jump_sound = pygame.mixer.Sound('audio/jump.wav')
jump_sound.set_volume(0.3)
gun_shot_sound = pygame.mixer.Sound('audio/gunshot.wav')
gun_shot_sound.set_volume(0.3)
grenade_sound = pygame.mixer.Sound('audio/grenade.wav')
grenade_sound.set_volume(0.3)

# ---------------------------------------------------------------------------
# Load Images
# ---------------------------------------------------------------------------
# Button Images
start_image = pygame.image.load('images/Menu/start_button.png').convert_alpha()
exit_image = pygame.image.load('images/Menu/exit_button.png').convert_alpha()
restart_image = pygame.image.load('images/Menu/restart_button.png').convert_alpha()

# Background Image
pine1_image = pygame.image.load('images/Background/pine1.png').convert_alpha()
pine2_image = pygame.image.load('images/Background/pine2.png').convert_alpha()
mountain_image = pygame.image.load('images/Background/mountain.png').convert_alpha()
sky_image = pygame.image.load('images/Background/sky_cloud.png').convert_alpha()

# Store Tile in a list
image_list = []
for tile_num in range(TILE_TYPES):
    tile_image = pygame.image.load(f'images/Tile/{tile_num}.png')
    tile_image = pygame.transform.scale(tile_image, (TILE_SIZE, TILE_SIZE))
    image_list.append(tile_image)

# Bullet
bullet_image = pygame.image.load('images/icons/bullet.png').convert_alpha()

# Grenade
grenade_image = pygame.image.load('images/icons/grenade.png').convert_alpha()

# Pick Up Boxes
health_box_image = pygame.image.load('images/icons/health_box.png').convert_alpha()
ammo_box_image = pygame.image.load('images/icons/ammo_box.png').convert_alpha()
grenade_box_image = pygame.image.load('images/icons/grenade_box.png').convert_alpha()
item_boxes = {
    'Health': health_box_image,
    'Ammo': ammo_box_image,
    'Grenade': grenade_box_image
}

# Weapon Icons (HUD): normal copy for the current weapon, faded copy for the others
weapon_icons = {}
faded_weapon_icons = {}
for weapon_name in PLAYER_GUNS:
    weapon_icon = pygame.image.load(f'images/icons/weapon_{weapon_name}.png').convert_alpha()
    weapon_icons[weapon_name] = weapon_icon
    faded_icon = weapon_icon.copy()
    faded_icon.fill((255, 255, 255, 110), special_flags=pygame.BLEND_RGBA_MULT)
    faded_weapon_icons[weapon_name] = faded_icon

clock = pygame.time.Clock()  # Used for frame rate
FPS = 60

# Define Colours
BACKGROUND_COLOUR = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)
HUD_ACTIVE_COLOUR = (255, 200, 40)
HUD_INACTIVE_COLOUR = (200, 200, 200)

# Define font
font = pygame.font.SysFont('Century Gothic', 20)
small_font = pygame.font.SysFont('Century Gothic', 14)
big_font = pygame.font.SysFont('Century Gothic', 60)

# HUD layout
HUD_X = 10
SLOT_WIDTH = 98
SLOT_HEIGHT = 40
SLOT_GAP = 6
SLOT_Y = 40
HUD_WIDTH = 3 * SLOT_WIDTH + 2 * SLOT_GAP


def draw_text(text, font, text_colour, x, y):
    image = font.render(text, True, text_colour)
    screen.blit(image, (x, y))


def draw_background():
    screen.fill(BACKGROUND_COLOUR)
    width = sky_image.get_width()
    for i in range(5):
        screen.blit(sky_image, ((i * width) - background_scroll * 0.5, 0))
        screen.blit(mountain_image, ((i * width) - background_scroll * 0.6, SCREEN_HEIGHT - mountain_image.get_height() - 300))
        screen.blit(pine1_image, ((i * width) - background_scroll * 0.7, SCREEN_HEIGHT - pine1_image.get_height() - 150))
        screen.blit(pine2_image, ((i * width) - background_scroll * 0.8, SCREEN_HEIGHT - pine2_image.get_height()))


def draw_weapon_hud():
    """Weapon slots (current one highlighted), ammo icons and grenade icons."""
    # One slot per weapon showing its key, name and rounds left
    for slot_number, gun in enumerate(PLAYER_GUNS):
        slot_x = HUD_X + slot_number * (SLOT_WIDTH + SLOT_GAP)
        slot_rect = pygame.Rect(slot_x, SLOT_Y, SLOT_WIDTH, SLOT_HEIGHT)
        is_active = (gun == player.gun_type)

        # Translucent background so the text stays readable over the scenery
        slot_surface = pygame.Surface((SLOT_WIDTH, SLOT_HEIGHT), pygame.SRCALPHA)
        slot_surface.fill((255, 255, 255, 70) if is_active else (0, 0, 0, 110))
        screen.blit(slot_surface, slot_rect)

        # Border (thick and coloured for the current weapon)
        border_colour = HUD_ACTIVE_COLOUR if is_active else HUD_INACTIVE_COLOUR
        pygame.draw.rect(screen, border_colour, slot_rect, 3 if is_active else 1)

        # Weapon icon on the left (faded when it isn't the current weapon)
        icon = weapon_icons[gun] if is_active else faded_weapon_icons[gun]
        screen.blit(icon, (slot_x + 4, SLOT_Y + (SLOT_HEIGHT - icon.get_height()) // 2))

        # Key number (top right) and rounds left (bottom right), right-aligned
        text_colour = WHITE if is_active else HUD_INACTIVE_COLOUR
        for text, text_y in ((str(slot_number + 1), SLOT_Y + 3), (str(player.ammo[gun]), SLOT_Y + 19)):
            text_width = small_font.size(text)[0]
            draw_text(text, small_font, text_colour, slot_x + SLOT_WIDTH - 6 - text_width, text_y)

    # One bullet icon per round for the current weapon (squeezed together if there are lots)
    ammo_y = SLOT_Y + SLOT_HEIGHT + 8
    ammo_count = player.ammo[player.gun_type]
    if ammo_count > 0:
        bullet_spacing = min(10, HUD_WIDTH / ammo_count)
        for i in range(ammo_count):
            screen.blit(bullet_image, (HUD_X + i * bullet_spacing, ammo_y))

    # One grenade icon per grenade
    grenade_y = ammo_y + bullet_image.get_height() + 8
    draw_text('Grenades: ', font, WHITE, HUD_X, grenade_y)
    if player.grenades > 0:
        grenade_spacing = min(15, (HUD_WIDTH - 110) / player.grenades)
        for i in range(player.grenades):
            screen.blit(grenade_image, (HUD_X + 110 + i * grenade_spacing, grenade_y + 5))


def get_animation_path(character_type, gun_type, animation):
    """images/<char>/<gun>/<animation>, falling back to images/<char>/<animation>
    (useful if the enemy folder has no per-gun subfolders)."""
    path = f'images/{character_type}/{gun_type}/{animation}'
    if not os.path.isdir(path):
        path = f'images/{character_type}/{animation}'
    return path


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------
class Soldier(pygame.sprite.Sprite):
    def __init__(self, character_type, guns, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.character_type = character_type
        self.guns = guns
        self.gun_type = guns[0]
        self.health = 100
        self.max_health = self.health
        self.speed = speed
        self.ammo = dict(ammo)  # {gun_name: rounds}
        self.grenades = grenades
        self.shoot_cooldown = 0
        self.action = 0
        self.direction = 1
        self.velocity_y = 0
        self.jump = False
        self.in_air = True
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

        # Create AI Specific variables for Enemies
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0

        # Load all images for the players
        # animations[gun][action] -> list of frames
        self.animations = {}
        for gun in self.guns:
            gun_animations = []
            for animation in ANIMATION_TYPES:
                path = get_animation_path(self.character_type, gun, animation)
                # Reset temporary list of images
                frames = []
                # Count number of files in a folder
                for i in range(len(os.listdir(path))):
                    image = pygame.image.load(f'{path}/{i}.png').convert_alpha()
                    image = pygame.transform.scale(image, (int(image.get_width() * scale),
                                                       int(image.get_height() * scale)))
                    frames.append(image)
                gun_animations.append(frames)
            self.animations[gun] = gun_animations

        self.image = self.current_frames()[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def current_frames(self):
        return self.animations[self.gun_type][self.action]

    def switch_weapon(self, gun_type):
        if gun_type in self.guns and gun_type != self.gun_type:
            self.gun_type = gun_type
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()
            self.shoot_cooldown = 0

    def update(self):
        self.update_animation()
        self.check_alive()
        # Update Cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        # Reset Movement Variables
        scroll = 0
        delta_x = 0
        delta_y = 0

        # Assign movement variables if moving left or right
        if moving_left:
            delta_x = -self.speed
            self.direction = -1
        if moving_right:
            delta_x = self.speed
            self.direction = 1

        # Jump
        if self.jump and not self.in_air:
            self.velocity_y = -11
            self.jump = False
            self.in_air = True

        # Apply Gravity (with terminal velocity)
        self.velocity_y += GRAVITY
        if self.velocity_y > MAX_FALL_SPEED:
            self.velocity_y = MAX_FALL_SPEED
        delta_y += self.velocity_y

        # Check Collision
        for tile in world.obstacle_list:
            # Check collision in x axis
            if tile[1].colliderect(self.rect.x + delta_x, self.rect.y, self.width, self.height):
                delta_x = 0
                # If the AI hit a wall turn around
                if self.character_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            # Check collision in y axis
            if tile[1].colliderect(self.rect.x, self.rect.y + delta_y, self.width, self.height):
                # Check if below is ground, i.e. jumping
                if self.velocity_y < 0:  # hitting a ceiling
                    self.velocity_y = 0
                    delta_y = tile[1].bottom - self.rect.top
                # Check if above the ground, i.e. falling
                elif self.velocity_y >= 0:  # landing
                    self.velocity_y = 0
                    self.in_air = False
                    delta_y = tile[1].top - self.rect.bottom

        # Check for collision with Water
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0

        # Check for collision with Exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        # Check if player fell off the map
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

        # Check if going off the edge of the screen
        if self.character_type == 'player':
            if self.rect.left + delta_x < 0 or self.rect.right + delta_x > SCREEN_WIDTH:
                delta_x = 0

        # Update Rectangle position
        self.rect.x += delta_x
        self.rect.y += delta_y

        # Update Scroll based on player position
        if self.character_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESHOLD
                    and background_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH) \
                    or (self.rect.left < SCROLL_THRESHOLD and background_scroll > abs(delta_x)):
                self.rect.x -= delta_x
                scroll = -delta_x

        return scroll, level_complete

    def update_animation(self):
        # Update animation
        ANIMATION_COOLDOWN = 100
        frames = self.current_frames()

        if self.frame_index >= len(frames):
            self.frame_index = 0
        # Update image depending on current frame
        self.image = frames[self.frame_index]

        # Check if enough time has passed since the last frame update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

        # Reset the animation back to the start index[0]
        if self.frame_index >= len(frames):
            if self.action == 3:  # death animation holds its last frame
                self.frame_index = len(frames) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        # Check if the new action is different from previous
        if new_action != self.action:
            self.action = new_action
            # Update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    def draw(self):
        # Always face the way the soldier aims and shoots (direction), so the sprite can't
        # be left facing one way while the bullets and vision point the other
        screen.blit(pygame.transform.flip(self.image, self.direction == -1, False), self.rect)

    def shoot(self):
        weapon = WEAPONS[self.gun_type]
        if self.shoot_cooldown == 0 and self.ammo[self.gun_type] > 0:
            self.shoot_cooldown = weapon['cooldown']
            damage = weapon['damage'] if self.character_type == 'player' else ENEMY_BULLET_DAMAGE
            spawn_x = self.rect.centerx + (0.75 * self.rect.size[0] * self.direction)
            for _ in range(weapon['pellets']):
                velocity_y = random.uniform(-weapon['spread'], weapon['spread']) if weapon['spread'] else 0
                bullet = Bullet(spawn_x, self.rect.centery, self.direction, self.character_type,
                                weapon['bullet_speed'], damage, velocity_y, weapon['lifetime'])
                bullet_group.add(bullet)
            # Reduce Ammo
            self.ammo[self.gun_type] -= 1
            gun_shot_sound.play()

    def ai(self):
        # Scroll first so the vision box and rect stay in sync with the world
        self.rect.x += screen_scroll

        if self.alive and player.alive:
            if not self.idling and random.randint(1, 200) == 1:
                self.update_action(0)  # 0: Idle
                self.idling = True
                self.idling_counter = 50

            # Update AI Vision (always follows the enemy, moving or idle)
            self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

            # Check if AI is near player
            if self.vision.colliderect(player.rect):
                # Stop Running and Face Player
                self.update_action(0)  # 0: Idle
                # Shoot
                self.shoot()
            else:
                if not self.idling:
                    ai_moving_right = (self.direction == 1)
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)  # 1: Run
                    self.move_counter += 1

                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, owner, speed, damage, velocity_y=0, lifetime=None):
        pygame.sprite.Sprite.__init__(self)
        self.speed = speed
        self.damage = damage
        self.owner = owner  # 'player' or 'enemy'
        self.velocity_y = velocity_y
        self.lifetime = lifetime
        self.image = bullet_image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.position_y = float(y)
        self.direction = direction

    def update(self):
        # Move Bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll
        self.position_y += self.velocity_y
        self.rect.centery = round(self.position_y)

        # Range limit (shotgun pellets)
        if self.lifetime is not None:
            self.lifetime -= 1
            if self.lifetime <= 0:
                self.kill()
                return

        # Check if bullet has gone off screen, if yes kill bullets
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
            return

        # Check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()
                return

        # Check collision with characters
        # (only THIS bullet is tested, and only the opposing side)
        if self.owner == 'enemy':
            if player.alive and self.rect.colliderect(player.rect):
                player.health -= self.damage
                self.kill()
        else:
            for enemy in enemy_group:
                if enemy.alive and self.rect.colliderect(enemy.rect):
                    enemy.health -= self.damage
                    self.kill()
                    break


class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.velocity_y = -11
        self.speed = 5
        self.image = grenade_image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.velocity_y += GRAVITY
        delta_x = self.direction * self.speed
        delta_y = self.velocity_y

        # Check collision with level
        for tile in world.obstacle_list:
            # Check collision with the walls
            if tile[1].colliderect(self.rect.x + delta_x, self.rect.y, self.width, self.height):
                self.direction *= -1
                delta_x = self.direction * self.speed
            # Check collision in y axis
            if tile[1].colliderect(self.rect.x, self.rect.y + delta_y, self.width, self.height):
                self.speed = 0
                # Check if below is ground, i.e. thrown up
                if self.velocity_y < 0:
                    self.velocity_y = 0
                    delta_y = tile[1].bottom - self.rect.top
                # Check if above the ground, i.e. falling
                elif self.velocity_y >= 0:
                    self.velocity_y = 0
                    delta_y = tile[1].top - self.rect.bottom

        # Update Grenade Position
        self.rect.x += delta_x + screen_scroll
        self.rect.y += delta_y

        # Countdown Timer
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            grenade_sound.play()
            explosion = Explosion(self.rect.centerx, self.rect.centery, 0.5)
            explosion_group.add(explosion)
            # Grenade Damage - AOE
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
               abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
                player.health -= 50

            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
                   abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
                    enemy.health -= 50


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            image = pygame.image.load(f'images/explosion/exp{num}.png').convert_alpha()
            image = pygame.transform.scale(image, (int(image.get_width() * scale),
                                               int(image.get_height() * scale)))
            self.images.append(image)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        # Scroll
        self.rect.x += screen_scroll
        EXPLOSION_SPEED = 4
        # Update explosion animation
        self.counter += 1
        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            # If animation is complete delete explosion
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]


class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        # Scroll
        self.rect.x += screen_scroll
        # Checking if player has picked up box
        if pygame.sprite.collide_rect(self, player):
            # Check what type the box is
            if self.item_type == 'Health':
                player.health = min(player.health + 25, player.max_health)
            elif self.item_type == 'Ammo':
                # Refill every weapon so you're never stuck on an empty gun
                for gun in player.guns:
                    player.ammo[gun] += WEAPONS[gun]['pickup']
            elif self.item_type == 'Grenade':
                player.grenades += 3
            # Delete item box
            self.kill()


class Decoration(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class Exit(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class Water(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class World():
    def __init__(self):
        self.obstacle_list = []
        self.level_length = 0

    def process_data(self, data):
        player = None
        health_bar = None
        self.level_length = len(data[0])
        # Iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    image = image_list[tile]
                    image_rect = image.get_rect()
                    image_rect.x = x * TILE_SIZE
                    image_rect.y = y * TILE_SIZE
                    tile_data = (image, image_rect)
                    if 0 <= tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif 9 <= tile <= 10:
                        water_group.add(Water(image, x * TILE_SIZE, y * TILE_SIZE))
                    elif 11 <= tile <= 14:
                        decoration_group.add(Decoration(image, x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 15:  # Create Player
                        player = Soldier('player', PLAYER_GUNS, x * TILE_SIZE, y * TILE_SIZE,
                                         1.65, 5, PLAYER_START_AMMO, 10)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16:  # Create Enemies
                        enemy = Soldier('enemy', ENEMY_GUNS, x * TILE_SIZE, y * TILE_SIZE,
                                        1.65, 2, ENEMY_START_AMMO, 0)
                        enemy_group.add(enemy)
                    elif tile == 17:  # Create Ammo Box
                        item_box_group.add(ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 18:  # Create Grenade Box
                        item_box_group.add(ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 19:  # Create Health Box
                        item_box_group.add(ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 20:  # Create Exit
                        exit_group.add(Exit(image, x * TILE_SIZE, y * TILE_SIZE))
        return player, health_bar

    def draw(self):
        for tile in self.obstacle_list:
            tile[1].x += screen_scroll
            screen.blit(tile[0], tile[1])


class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        # Update with new health
        self.health = health
        # Calculate health ratio
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))


class ScreenFade():
    def __init__(self, direction, colour, speed):
        self.direction = direction
        self.colour = colour
        self.speed = speed
        self.fade_counter = 0

    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1:  # Whole Screen Fade (intro)
            pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.colour, (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
            if self.fade_counter >= SCREEN_WIDTH // 2:
                fade_complete = True
        elif self.direction == 2:  # Vertical Screen Fade Down (death)
            pygame.draw.rect(screen, self.colour, (0, 0, SCREEN_WIDTH, self.fade_counter))
            if self.fade_counter >= SCREEN_HEIGHT:
                fade_complete = True

        return fade_complete


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
# Create Screen Fades
intro_fade = ScreenFade(1, BLACK, 3)
death_fade = ScreenFade(2, PINK, 4)

# Create Buttons
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_image, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_image, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_image, 2)

# Create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()


def load_level(level_num):
    """Clear every group, read the level CSV, and build the world.
    Returns (world, player, health_bar)."""
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    # Create empty tile list
    data = [[-1] * COLUMNS for _ in range(ROWS)]
    # Load in the level data and create world
    with open(f'level{level_num}_data.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row_index, row in enumerate(reader):
            for column_index, tile in enumerate(row):
                data[row_index][column_index] = int(tile)

    new_world = World()
    new_player, new_health_bar = new_world.process_data(data)
    return new_world, new_player, new_health_bar


world, player, health_bar = load_level(level)

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
while True:
    clock.tick(FPS)

    if not start_game:
        # Draw Menu
        screen.fill(BACKGROUND_COLOUR)
        # Add button
        if start_button.draw(screen):
            start_game = True
            start_intro = True
        if exit_button.draw(screen):
            pygame.quit()
            exit()

    elif game_won:
        # End screen
        draw_background()
        draw_text('YOU WIN!', big_font, WHITE, SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150)
        if restart_button.draw(screen):
            game_won = False
            level = 1
            background_scroll = 0
            screen_scroll = 0
            start_intro = True
            intro_fade.fade_counter = 0
            world, player, health_bar = load_level(level)

    else:
        # Update Background
        draw_background()
        # Draw world map
        world.draw()

        # Show player health, weapons, ammo and grenades
        health_bar.draw(player.health)
        draw_weapon_hud()

        player.update()
        player.draw()

        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()

        # Update and Draw Groups
        bullet_group.update()
        grenade_group.update()
        explosion_group.update()
        item_box_group.update()
        decoration_group.update()
        water_group.update()
        exit_group.update()

        bullet_group.draw(screen)
        grenade_group.draw(screen)
        explosion_group.draw(screen)
        item_box_group.draw(screen)
        decoration_group.draw(screen)
        water_group.draw(screen)
        exit_group.draw(screen)

        # Show Intro
        if start_intro:
            if intro_fade.fade():
                start_intro = False
                intro_fade.fade_counter = 0

        # Update Player Actions
        if player.alive:
            # Shooting and grenades
            if shooting:
                player.shoot()
            # Throw Grenade
            if throwing_grenade and not grenade_thrown and player.grenades > 0:
                new_grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),
                                      player.rect.top, player.direction)
                grenade_group.add(new_grenade)
                # Reduce Grenade
                player.grenades -= 1
                grenade_thrown = True

            # Animation state (independent of shooting / grenades)
            if player.in_air:
                player.update_action(2)  # 2 = Jump
            elif moving_left or moving_right:
                player.update_action(1)  # 1 = Run
            else:
                player.update_action(0)  # 0 = Idle

            screen_scroll, level_complete = player.move(moving_left, moving_right)
            background_scroll -= screen_scroll

            # Check if player has completed the level
            if level_complete:
                level += 1
                background_scroll = 0
                screen_scroll = 0
                if level > MAX_LEVELS:
                    game_won = True
                else:
                    start_intro = True
                    intro_fade.fade_counter = 0
                    # Load in the level data and create world
                    world, player, health_bar = load_level(level)
        else:  # If player is dead
            screen_scroll = 0
            if death_fade.fade():
                if restart_button.draw(screen):
                    death_fade.fade_counter = 0
                    start_intro = True
                    background_scroll = 0
                    # Load in the level data and create world
                    world, player, health_bar = load_level(level)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # User clicking X button in window
            pygame.quit()
            exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                moving_right = True
            if (event.key == pygame.K_UP or event.key == pygame.K_w) and player.alive:
                player.jump = True
                jump_sound.play()
            if event.key == pygame.K_SPACE:
                shooting = True
            if event.key == pygame.K_q:
                throwing_grenade = True
            # Weapon selection
            if player.alive:
                if event.key == pygame.K_1:
                    player.switch_weapon('pistol')
                if event.key == pygame.K_2:
                    player.switch_weapon('rifle')
                if event.key == pygame.K_3:
                    player.switch_weapon('shotgun')
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                exit()

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_SPACE:
                shooting = False
            if event.key == pygame.K_q:
                throwing_grenade = False
                grenade_thrown = False

    pygame.display.update()