"""soldier.py - the Soldier class, used for BOTH the player and the soldier enemies.

It handles movement and physics, animation, health/death, shooting, the
mutated-stimulant buff and the enemy AI. Zombie (zombie.py) inherits from it.
"""
import random

import pygame

import state
from settings import (GRAVITY, MAX_FALL_SPEED, SCREEN_HEIGHT, SCREEN_WIDTH,
                      SCROLL_THRESHOLD, TILE_SIZE, WEAPONS, ENEMY_BULLET_DAMAGE,
                      ANIMATION_TYPES, DROP_CHANCES, screen,
                      STIM_DURATION, STIM_DRAIN_INTERVAL, STIM_DRAIN_AMOUNT,
                      STIM_SPEED_MULT, STIM_FIRE_RATE_MULT)
from assets import load_frames, gun_shot_sound
from groups import bullet_group, water_group, exit_group, item_box_group
from projectiles import Bullet
from objects import DroppedItem


def get_animation_path(character_type, gun_type, animation):
    """Player: images/player/<gun>/<animation>
    Enemy soldier: images/enemy/soldier/<animation> (no per-gun folders)."""
    if character_type == 'enemy':
        return f'images/enemy/soldier/{animation}'
    return f'images/{character_type}/{gun_type}/{animation}'


class Soldier(pygame.sprite.Sprite):
    drop_chances = DROP_CHANCES  # subclasses (e.g. Zombie) can override
    death_action = 3             # index of the Death animation (Zombie overrides this)

    def __init__(self, character_type, guns, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.character_type = character_type   # 'player' or 'enemy'
        self.guns = guns
        self.gun_type = guns[0]                # start with the first gun in the list
        self.health = 100
        self.max_health = self.health
        self.speed = speed
        self.ammo = dict(ammo)  # {gun_name: rounds}  (copied so characters don't share one dict)
        self.grenades = grenades
        self.shoot_cooldown = 0
        self.action = 0         # 0 = Idle, 1 = Run, 2 = Jump, 3 = Death
        self.direction = 1      # 1 = facing right, -1 = facing left
        self.velocity_y = 0
        self.jump = False
        self.in_air = True
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()   # when the animation frame last changed

        # Create AI Specific variables for Enemies
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)   # box in front of the enemy; if the player is in it, it reacts
        self.idling = False
        self.idling_counter = 0

        # Stimulant (buff) state
        self.base_speed = speed      # remembered so we can restore it when the buff ends
        self.stimulated = False
        self.stim_end_time = 0
        self.stim_next_drain = 0
        self.fire_rate_multiplier = 1.0

        # Load all images for the players
        # animations[gun][action] -> list of frames
        self.animations = {}
        self.load_animations(scale)

        self.image = self.current_frames()[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def load_animations(self, scale):
        # For every gun, load every animation (Idle, Run, Jump, Death)
        for gun in self.guns:
            gun_animations = []
            for animation in ANIMATION_TYPES:
                path = get_animation_path(self.character_type, gun, animation)
                frames = load_frames(path, scale)
                gun_animations.append(frames)
            self.animations[gun] = gun_animations

    def current_frames(self):
        # The list of frames for the current gun + current action
        return self.animations[self.gun_type][self.action]

    def switch_weapon(self, gun_type):
        # Only switch to a gun we own, and only if it's actually different
        if gun_type in self.guns and gun_type != self.gun_type:
            self.gun_type = gun_type
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()
            self.shoot_cooldown = 0   # no waiting after swapping

    def update(self):
        self.update_stimulant()
        self.update_animation()
        self.check_alive()
        # Update Cooldown (a stimulated soldier counts it down faster)
        if self.shoot_cooldown > 0:
            self.shoot_cooldown = max(0, self.shoot_cooldown - self.fire_rate_multiplier)

    # -- Mutated stimulant ---------------------------------------------
    def apply_stimulant(self):
        """Start the buff. Returns False (and does nothing) if already stimulated."""
        if self.stimulated or not self.alive:
            return False
        now = pygame.time.get_ticks()
        self.stimulated = True
        self.stim_end_time = now + STIM_DURATION
        self.stim_next_drain = now + STIM_DRAIN_INTERVAL
        self.fire_rate_multiplier = STIM_FIRE_RATE_MULT
        self.speed = round(self.base_speed * STIM_SPEED_MULT)
        return True

    def end_stimulant(self):
        # Back to normal speed and fire rate
        self.stimulated = False
        self.fire_rate_multiplier = 1.0
        if self.alive:
            self.speed = self.base_speed

    def update_stimulant(self):
        if not self.stimulated:
            return
        if not self.alive:
            self.end_stimulant()
            return
        now = pygame.time.get_ticks()
        # Apply one health tick for every interval that has passed. A while loop
        # (not an if) so that no ticks are missed if a frame takes a long time.
        while self.stim_next_drain <= min(now, self.stim_end_time):
            self.health -= STIM_DRAIN_AMOUNT   # check_alive() handles death
            self.stim_next_drain += STIM_DRAIN_INTERVAL
        if now >= self.stim_end_time:
            self.end_stimulant()

    def move(self, moving_left, moving_right):
        """Move one frame with gravity and collisions.
        Returns (scroll, level_complete): scroll is how far the WORLD should shift."""
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

        # Check Collision: test where we WOULD end up against every solid tile
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
        # If the player is in the scroll zone near either edge (and the level isn't at its end),
        # undo the player's movement and shift the whole world the opposite way instead
        if self.character_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESHOLD
                    and state.background_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH) \
                    or (self.rect.left < SCROLL_THRESHOLD and state.background_scroll > abs(delta_x)):
                self.rect.x -= delta_x
                scroll = -delta_x

        return scroll, level_complete

    def update_animation(self):
        # Update animation
        ANIMATION_COOLDOWN = 100   # milliseconds each frame is shown
        frames = self.current_frames()

        # Safety: if the frame list changed (new action/gun), don't index out of range
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
            if self.action == self.death_action:  # death animation holds its last frame
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
            self.update_action(self.death_action)
            # Only drop loot once, on the frame the enemy dies
            if was_alive and self.character_type == 'enemy':
                self.drop_loot()

    def drop_loot(self):
        """Roll each item in DROP_CHANCES and spawn the ones that succeed."""
        drops = [item for item, chance in self.drop_chances.items() if random.random() < chance]
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
        # Only fire if the gun has cooled down and there is ammo
        if self.shoot_cooldown <= 0 and self.ammo[self.gun_type] > 0:
            self.shoot_cooldown = weapon['cooldown']
            # Enemies always use the fixed enemy damage; the player uses the weapon's damage
            damage = weapon['damage'] if self.character_type == 'player' else ENEMY_BULLET_DAMAGE
            spawn_x = self.rect.centerx + (0.75 * self.rect.size[0] * self.direction)
            # One Bullet per pellet (the shotgun has 5), each with its own random vertical drift
            for _ in range(weapon['pellets']):
                velocity_y = random.uniform(-weapon['spread'], weapon['spread']) if weapon['spread'] else 0
                bullet = Bullet(spawn_x, self.rect.centery, self.direction, self.character_type,
                                weapon['bullet_speed'], damage, velocity_y, weapon['lifetime'])
                bullet_group.add(bullet)
            # Reduce Ammo (one per shot, not per pellet)
            self.ammo[self.gun_type] -= 1
            gun_shot_sound.play()

    def ai(self):
        """Soldier brain: shoot if the player is in the vision box, otherwise patrol."""
        player = state.player

        # Scroll first so the vision box and rect stay in sync with the world
        self.rect.x += state.screen_scroll

        if self.alive and player.alive:
            # Randomly stop to idle (about once every 200 frames)
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
                    # Patrol: walk in the current direction
                    ai_moving_right = (self.direction == 1)
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)  # 1: Run
                    self.move_counter += 1

                    # After walking one tile's worth of frames, turn around.
                    # Multiplying by -1 makes the counter count back up for the return trip.
                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    # Standing still for a short while before patrolling again
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False