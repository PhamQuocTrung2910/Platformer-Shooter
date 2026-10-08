import pygame
from pygame import mixer
from sys import exit
import os
import random
import csv
import button

mixer.init()
pygame.init()

# Game Variables
GRAVITY = 0.75
SCROLL_THRESHOLD = 200
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
ROWS = 16
COLLUMNS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 3
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ben's Third Game")

# Player Variables
x = SCREEN_WIDTH/2
y = SCREEN_HEIGHT/2

# Player Action Variables
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False

# Load Music & Sounds
#Background Music
pygame.mixer.music.load('audio/music2.mp3')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000)

# Sound Effects
jump_sfx = pygame.mixer.Sound('audio/jump.wav')
jump_sfx.set_volume(0.3)
gun_shot_sfx = pygame.mixer.Sound('audio/gunshot.wav')
gun_shot_sfx.set_volume(0.3)
grenade_sfx = pygame.mixer.Sound('audio/grenade.wav')
grenade_sfx.set_volume(0.3)

# Load Images
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
for x in range(TILE_TYPES):
    image = pygame.image.load(f'images/Tile/{x}.png')
    image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
    image_list.append(image)

# Bullet
bullet_image = pygame.image.load('images/icons/bullet.png').convert_alpha()

# Grenade
grenade_image = pygame.image.load('images/icons/grenade.png').convert_alpha()

#Pcik Up Boxes
health_box_image = pygame.image.load('images/icons/health_box.png').convert_alpha()
ammo_box_image = pygame.image.load('images/icons/ammo_box.png').convert_alpha()
grenade_box_image = pygame.image.load('images/icons/grenade_box.png').convert_alpha()
item_boxes = {
    'Health' : health_box_image,
    'Ammo': ammo_box_image,
    'Grenade': grenade_box_image
}


clock = pygame.time.Clock() #Used for frame rate
FPS = 60

#Define Colours
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)

#define font
font = pygame.font.SysFont('Century Gothic', 20)

def draw_text(text, font, text_colour, x, y):
    image = font.render(text, True, text_colour)
    screen.blit(image, (x, y))

def draw_bg():
    screen.fill(BG)
    width = sky_image.get_width()
    for x in range(5):
        screen.blit(sky_image, ((x * width) - bg_scroll * 0.5, 0))
        screen.blit(mountain_image, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_image.get_height() - 300))
        screen.blit(pine1_image, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - pine1_image.get_height() - 150))
        screen.blit(pine2_image, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_image.get_height()))
# Function to Reset Level
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    # Create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLLUMNS
        data.append(r)

    return data

# Classes
class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.health = 100
        self.max_health = self.health
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.grenades = grenades
        self.shoot_cooldown = 0
        self.action = 0
        self.direction = 1
        self.velocity_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()


        # Create AI Specific variables for Enemies
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0



        #Load all images for the players
        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for animation in animation_types:
            #reset temporary list of images
            temp_list = []
            # Count number of files in a folder
            num_of_frames = len(os.listdir(f'images/{self.char_type}/{animation}'))
            for i in range(num_of_frames):
                image = pygame.image.load(f'images/{self.char_type}/{animation}/{i}.png').convert_alpha()
                image = pygame.transform.scale(image, (image.get_width() * scale, image.get_height() * scale))
                temp_list.append(image)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        # Update Cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        # Reset Movement Variables
        screen_scroll = 0
        dx = 0
        dy = 0

        # Assign movement variables if moving left or right
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        # Jump
        if self.jump == True and self.in_air == False:
            self.velocity_y = -11
            self.jump = False
            self.in_air = True

        # Apply Gravity
        self.velocity_y += GRAVITY
        if self.velocity_y > 10:
            self.velocity_y
        dy += self.velocity_y

        # Check Collision
        for tile in world.obstacle_list:
            #check collision in x axis
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                #if the Ai hot wall turn around
                if self.char_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            #check collision in y axis
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #check if below is ground, i.e. jumping
                if self.velocity_y < 0:
                    self.velocity_y = 0
                    dy = tile[1].bottom - self.rect.top
                #check if above the ground, i.e. falling
                elif self.velocity_y >= 0:
                    self.velocity_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        # Check for collision with Water
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0

        # CHeck for collision with Exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        # Check if player fell off the map
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

        #Check if going off the edge of the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
               dx = 0
        # Update Rectangle position
        self.rect.x += dx
        self.rect.y += dy

        #Update Scroll based on player position
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH  - SCROLL_THRESHOLD and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH) \
                or (self.rect.left < SCROLL_THRESHOLD and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll, level_complete

    def update_animation(self):
        # Update animation
        ANIMATION_COOLDOWN = 100

        # Update image depending on current frame
        self.image = self.animation_list[self.action][self.frame_index]

        # Check if enough time has passed to trigger idle animation
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

        #reset the animation back to the start index[0]
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) -1
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
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
            bullet_group.add(bullet)
            # Reduce Ammo
            self.ammo -= 1
            gun_shot_sfx.play()

    def ai(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0) # 0: Idle
                self.idling = True
                self.idling_counter = 50
            # Check if AI is near player
            if self.vision.colliderect(player.rect):
                # Stop Running and Face Player
                 self.update_action(0) # 0: Idle
                 #shoot
                 self.shoot()
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1) # 1: Run
                    self. move_counter += 1
                    # Update AI Vision as it moves
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False
        #scroll
        self.rect.x += screen_scroll
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction


    def update(self):
        # Move Bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll
        # Check if bullet has gone off screen, if yes kill bullets
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        # Check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()
        # Check collision with characters
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                self.kill()
                player.health -= 5
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    print(enemy.health)
                    self.kill()
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
        dx = self.direction * self.speed
        dy = self.velocity_y

        # Check collision with level
        for tile in world.obstacle_list:
            #check collision with the walls
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed
            #check collision in y axis
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                #check if below is ground, i.e. thrown up
                if self.velocity_y < 0:
                    self.velocity_y = 0
                    dy = tile[1].bottom - self.rect.top
                #check if above the ground, i.e. falling
                elif self.velocity_y >= 0:
                    self.velocity_y = 0
                    dy = tile[1].top - self.rect.bottom

        # Update Grenade Position
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        # Countdown Timer
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            grenade_sfx.play()
            explosion = Explosion(self.rect.x, self.rect.y, 0.5)
            explosion_group.add(explosion)
            # Grenade Damage - AOE
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and\
               abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
                   player.health -= 50

            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and\
                   abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
                    enemy.health -= 50
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            image = pygame.image.load(f'images/explosion/exp{num}.png').convert_alpha()
            image = pygame.transform.scale(image, (image.get_width() * scale, image.get_height() * scale))
            self.images.append(image)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        #Scroll
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
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Ammo':
                player.ammo += 15
            elif self.item_type == 'Grenade':
                player.grenades += 3
            #delete item box
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

    def process_data(self, data):
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
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 9 and tile <= 10:
                         water = Water(image, x * TILE_SIZE, y * TILE_SIZE)
                         water_group.add(water)
                    elif tile >= 11 and tile <= 14:
                        decoration = Decoration(image, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15: # Create Player
                        player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 20, 10)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16: # Create Enemies
                        enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, 2, 5, 0)
                        enemy_group.add(enemy)
                    elif tile == 18: #Create Grenade Box
                        item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 17: #Create Ammo Box
                        item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19: #Create Health Box
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20: #Create Exit
                        exit = Exit(image, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)
        return player, health_bar
    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
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
        # Calculate health raatio
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
        self.fade_counter += self.speed
        pygame.draw.rect(screen, self.colour, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))

# Create Screen Fades
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



# Create empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * COLLUMNS
    world_data.append(r)
# Load in the level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)

while True:
    clock.tick(FPS)

    if start_game == False:
        # Draw Menu
        screen.fill(BG)
        # Add button
        if start_button.draw(screen):
            start_game = True
        if exit_button.draw(screen):
            exit()
    else:
        # Update Background
        draw_bg()
        # Draw world map
        world.draw()

        #show player health
        health_bar.draw(player.health)

        draw_text('Ammo: ', font, WHITE, 10, 35)
        for x in range(player.ammo):
            screen.blit(bullet_image, (90 + (x * 10), 45))

        draw_text('Grenades: ', font, WHITE, 10, 60)
        for x in range(player.grenades):
                screen.blit(grenade_image, (120 + (x * 15), 65))

        player.update()
        player.draw()

        for enemy in enemy_group:
            enemy.update()
            enemy.draw()
            enemy.ai()

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


        # Update Player Actions
        if player.alive:
            if shoot:
                player.shoot()
            # Throw Grenade
            elif grenade and grenade_thrown == False and player.grenades > 0:
                grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),\
                            player.rect.top, player.direction)
                grenade_group.add(grenade)
                # Reduce Grenade
                player.grenades -= 1
                grenade_thrown = True

            elif player.in_air:
                player.update_action(2) # 2 = Jump
            elif moving_left or moving_right:
                player.update_action(1) # 1 = Run
            else:
                player.update_action(0) # 0 = Idle
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
             # Check if player has completed the level
            if level_complete == True:
                level += 1
                bg_scroll = 0
                world_data = reset_level()
                if level <= MAX_LEVELS:
                    # Load in the level data and create world
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)
        else: # If player is dead
            screen_scroll = 0
            if restart_button.draw(screen):
                bg_scroll = 0
                world_data = reset_level()
                # Load in the level data and create world
                with open(f'level{level}_data.csv', newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)
                world = World()
                player, health_bar = world.process_data(world_data)


    for event in pygame.event.get():
        if event.type == pygame.QUIT: #User clicking X button in window
            pygame.quit()
            exit()


        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                moving_right = True
            if (event.key == pygame.K_UP or event.key == pygame.K_w) and player.alive:
                player.jump = True
                jump_sfx.play()
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_q:
                grenade = True
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                exit()

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_SPACE:
                shoot = False
            if event.key == pygame.K_q:
                grenade = False
                grenade_thrown = False


    pygame.display.update()
