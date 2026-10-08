import os
import random

import pygame

import state
from settings import (GRAVITY, MAX_FALL_SPEED, SCREEN_HEIGHT, SCREEN_WIDTH,
                      SCROLL_THRESHOLD, TILE_SIZE, WEAPONS, ENEMY_BULLET_DAMAGE,
                      ANIMATION_TYPES, DROP_CHANCES, screen)
from assets import load_image, gun_shot_sound
from groups import bullet_group, water_group, exit_group, item_box_group
from projectiles import Bullet
from objects import DroppedItem


def get_animation_path(character_type, gun_type, animation):
    """images/<char>/<gun>/<animation>, falling back to images/<char>/<animation>
    (useful if the enemy folder has no per-gun subfolders)."""
    path = f'images/{character_type}/{gun_type}/{animation}'
    if not os.path.isdir(path):
        path = f'images/{character_type}/{animation}'
    return path


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
                # Count number of files in a folder and load each frame
                frames = [load_image(f'{path}/{i}.png', scale)
                          for i in range(len(os.listdir(path)))]
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
        world = state.world

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
                    and state.background_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH) \
                    or (self.rect.left < SCROLL_THRESHOLD and state.background_scroll > abs(delta_x)):
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
            was_alive = self.alive
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)
            # Only drop loot once, on the frame the enemy dies
            if was_alive and self.character_type == 'enemy':
                self.drop_loot()

    def drop_loot(self):
        """Roll each item in DROP_CHANCES and spawn the ones that succeed."""
        drops = [item for item, chance in DROP_CHANCES.items() if random.random() < chance]
        for i, item_type in enumerate(drops):
            # Spread multiple drops apart so they don't sit on top of each other
            offset = (i - (len(drops) - 1) / 2) * 40
            item_box_group.add(DroppedItem(item_type, int(self.rect.centerx + offset), self.rect.centery))

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
        player = state.player

        # Scroll first so the vision box and rect stay in sync with the world
        self.rect.x += state.screen_scroll

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