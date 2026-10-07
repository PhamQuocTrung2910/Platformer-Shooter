import pygame
from sys import exit
import os
import random
import csv

pygame.init()

# Game Variables
GRAVITY = 0.75
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
ROWS = 16
COLLUMNS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
level = 1


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
# Load Images
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

#Define Colors
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

#define font
font = pygame.font.SysFont('Century Gothic', 20)

def draw_text(text, font, text_colour, x, y):
    image = font.render(text, True, text_colour)
    screen.blit(image, (x, y))


def draw_bg():
    screen.fill(BG)
    pygame.draw.line(screen, RED, (0, 500), (SCREEN_WIDTH, 500))

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

    def update(self):
        self.update_animation()
        self.check_alive()
        # Update Cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        # Reset Movement Variables
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

        # Check Collision with floor
        if self.rect.bottom + dy > 500:
            dy = 500 - self.rect.bottom
            self.in_air = False

        # Update Rectangle position
        self.rect.x += dx
        self.rect.y += dy

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
        self.rect.x += (self.direction * self.speed)
        # Check if bullet has gone off screen, if yes kill bullets
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
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


    def update(self):
        self.velocity_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.velocity_y

        # Check collision with floor
        if self.rect.bottom + dy > 500:
            dy = 500 - self.rect.bottom
            self.speed = 0

        # Check collision with walls
        if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
            self.direction *= -1
            dx = self.direction * self.speed

        # Update Grenade Position
        self.rect.x += dx
        self.rect.y += dy

        # Countdown Timer
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
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


# Create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()


#Temp - Create Item Boxes
item_box = ItemBox('Health', 100, 450)
item_box_group.add(item_box)
item_box = ItemBox('Ammo', 200, 450)
item_box_group.add(item_box)
item_box = ItemBox('Grenade', 300, 450)
item_box_group.add(item_box)

player = Soldier('player', 500, 200, 1.65, 5, 20, 10)
health_bar = HealthBar(10, 10, player.health, player.health)

enemy = Soldier('enemy', 500, 450, 1.65, 2, 5, 0)
enemy2 = Soldier('enemy', 100, 450, 1.65, 2, 5, 0)
enemy_group.add(enemy, enemy2)

# Create empty tile list
world_data = []
for row in range(ROWS):
    r = (-1) * COLLUMNS
    world_data.append(r)
# Load in the level data and create world
with open(f'level{level}_data.csv', newline = ' ') as csvfile:
    reader = csv.reader(csvfile, delimiter = ',')



while True:
    clock.tick(FPS)
    draw_bg()

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
    bullet_group.draw(screen)
    grenade_group.draw(screen)
    explosion_group.draw(screen)
    item_box_group.draw(screen)

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
        player.move(moving_left, moving_right)

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
