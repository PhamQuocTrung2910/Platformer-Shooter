"""character.py - Character: the base class for everything that walks around the level.

It holds ONLY what every character shares: health and death, animation, gravity and tile
collision, hazards (water, pits) and drawing. Everything else lives in a subclass:

    player.py   Player  - keyboard driven, world scrolling, weapons, stimulants, pad effects
    enemy.py    Enemy   - AI, patrol, loot drops, kill quota
                 soldier.py / zombie.py / scientist.py inherit from Enemy

To add a new character: subclass Player or Enemy, set the class attributes below, and
override the hooks (on_death, on_wall_hit, adjust_motion, on_frame_advance, ...).
"""
import pygame

import state
from settings import GRAVITY, MAX_FALL_SPEED, SCREEN_HEIGHT, CONVEYOR_SPEED, screen
from assets import load_frames
from groups import water_group

# Action numbers every character shares (the index into its animation list)
ACTION_IDLE = 0
ACTION_RUN = 1

JUMP_VELOCITY = -11   # about 2 tiles high


class Character(pygame.sprite.Sprite):
    # ---- Set these in a subclass --------------------------------------
    animation_folder = None     # images/<...>/ ; each animation is a sub-folder of <n>.png frames
    animation_names = []        # folder names in action-number order, e.g. ['Idle', 'Run', 'Death']
    death_action = 3            # index in animation_names of the Death animation
    animation_cooldown = 100    # ms each animation frame is shown
    hitbox_width = None         # None = hitbox is the sprite's own rect (drawn top-left on it);
                                # a number = narrower hitbox, sprite drawn centred on it

    def __init__(self, x, y, scale, speed, health=100):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.health = health
        self.max_health = health
        self.speed = speed
        self.base_speed = speed      # remembered so effects (buffs) can restore it
        self.x_remainder = 0.0       # sub-pixel movement saved up between frames (for speeds like 0.5)
        self.action = ACTION_IDLE
        self.direction = 1           # 1 = facing right, -1 = facing left
        self.velocity_y = 0
        self.jump = False
        self.in_air = True
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()   # when the animation frame last changed

        self.animations = self.load_animations(scale)
        self.image = self.current_frames()[self.frame_index]
        if self.hitbox_width is None:
            self.rect = self.image.get_rect()
        else:
            self.rect = pygame.Rect(0, 0, self.hitbox_width, self.image.get_height())
        self.rect.center = (x, y)
        self.width = self.rect.width
        self.height = self.rect.height

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------
    def load_animations(self, scale):
        """One list of frames per animation, in the same order as animation_names."""
        return [load_frames(f'{self.animation_folder}/{name}', scale)
                for name in self.animation_names]

    def current_frames(self):
        return self.animations[self.action]

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def update_animation(self):
        frames = self.current_frames()

        # Safety: if the frame list changed (new action/gun), don't index out of range
        if self.frame_index >= len(frames):
            self.frame_index = 0
        self.image = frames[self.frame_index]

        if pygame.time.get_ticks() - self.update_time > self.animation_cooldown:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
            self.on_frame_advance(frames)

        if self.frame_index >= len(frames):
            if self.action == self.death_action:   # death holds its last frame
                self.frame_index = len(frames) - 1
            else:
                self.on_animation_end()

    def on_frame_advance(self, frames):
        """Hook: called each time the animation moves to its next frame
        (e.g. the zombie's claw landing part-way through the swing)."""

    def on_animation_end(self):
        """Hook: called when a non-death animation runs past its last frame."""
        self.frame_index = 0

    # ------------------------------------------------------------------
    # Life and death
    # ------------------------------------------------------------------
    def update(self):
        self.update_animation()
        self.check_alive()

    def check_alive(self):
        if self.health <= 0:
            was_alive = self.alive
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(self.death_action)
            if was_alive:
                self.on_death()   # only on the frame the character dies

    def on_death(self):
        """Hook: called once, on the frame the character dies."""

    # ------------------------------------------------------------------
    # Physics
    # ------------------------------------------------------------------
    def move(self, moving_left, moving_right):
        """Move one frame with gravity and tile collisions. Returns the x distance moved.
        (Player.move wraps this and returns (scroll, level_complete) instead.)"""
        world = state.world
        delta_x = 0
        delta_y = 0

        if moving_left:
            delta_x = -self.speed
            self.direction = -1
        if moving_right:
            delta_x = self.speed
            self.direction = 1

        # Conveyor belt: standing on one carries you along
        if not self.in_air:
            feet = pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, 2)
            for belt_rect, belt_direction in world.conveyor_list:
                if belt_rect.colliderect(feet):
                    delta_x += belt_direction * CONVEYOR_SPEED
                    break

        # Fractional speeds (e.g. a zombie's 0.5): rect positions are whole pixels, so save
        # the fraction up and move 1 px once enough has built up.
        total_x = delta_x + self.x_remainder
        delta_x = int(total_x)
        self.x_remainder = total_x - delta_x if (moving_left or moving_right) else 0.0

        # Jump
        if self.jump and not self.in_air:
            self.velocity_y = JUMP_VELOCITY
            self.jump = False
            self.in_air = True

        # Gravity (with terminal velocity)
        self.velocity_y += GRAVITY
        if self.velocity_y > MAX_FALL_SPEED:
            self.velocity_y = MAX_FALL_SPEED
        delta_y += self.velocity_y

        # Test where we WOULD end up against every solid tile
        for tile in world.near_tiles:
            if tile[1].colliderect(self.rect.x + delta_x, self.rect.y, self.width, self.height):
                delta_x = 0
                self.x_remainder = 0.0
                self.on_wall_hit()
            if tile[1].colliderect(self.rect.x, self.rect.y + delta_y, self.width, self.height):
                if self.velocity_y < 0:      # hitting a ceiling
                    self.velocity_y = 0
                    delta_y = tile[1].bottom - self.rect.top
                elif self.velocity_y >= 0:   # landing
                    self.velocity_y = 0
                    self.in_air = False
                    delta_y = tile[1].top - self.rect.bottom

        delta_x, delta_y = self.adjust_motion(delta_x, delta_y)
        self.check_hazards()

        self.rect.x += delta_x
        self.rect.y += delta_y
        return delta_x

    def on_wall_hit(self):
        """Hook: the character walked into a wall (enemies turn around)."""

    def adjust_motion(self, delta_x, delta_y):
        """Hook: last chance to change this frame's movement before it is applied.
        Returns (delta_x, delta_y)."""
        return delta_x, delta_y

    def check_hazards(self):
        # Water kills anything that touches it
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0
        # Fell off the map
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self):
        # Always face the way the character is facing (direction)
        image = pygame.transform.flip(self.image, self.direction == -1, False)
        if self.hitbox_width is None:
            screen.blit(image, self.rect)
        else:
            # Narrow hitbox: centre the sprite on it, feet on the bottom edge
            screen.blit(image, image.get_rect(midbottom=self.rect.midbottom))