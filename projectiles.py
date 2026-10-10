"""projectiles.py - things that fly through the air: bullets, grenades, explosions."""
import pygame
import random  # noqa: F401  (kept in case you add randomness to projectiles later)

import state
from settings import GRAVITY, SCREEN_WIDTH, TILE_SIZE
from assets import load_image, bullet_image, grenade_image, grenade_sound
from groups import enemy_group, explosion_group


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, owner, speed, damage, velocity_y=0, lifetime=None):
        pygame.sprite.Sprite.__init__(self)
        self.speed = speed
        self.damage = damage
        self.owner = owner  # 'player' or 'enemy'
        self.velocity_y = velocity_y      # vertical drift (used for rifle/shotgun spread)
        self.lifetime = lifetime          # frames left to live (None = no limit)
        self.image = bullet_image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        # rect.y can only hold whole numbers, so keep the exact height as a float
        # or tiny spreads like 0.2 would be rounded away to nothing
        self.position_y = float(y)
        self.direction = direction        # 1 = right, -1 = left

    def update(self):
        player = state.player

        # Move Bullet: its own speed PLUS the world scroll so it stays put in the world
        self.rect.x += (self.direction * self.speed) + state.screen_scroll
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
        for tile in state.world.obstacle_list:
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
                    break   # one bullet only hurts one enemy


class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100        # frames until it explodes
        self.velocity_y = -11   # thrown upwards
        self.speed = 5          # horizontal speed
        self.image = grenade_image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        player = state.player

        # Gravity pulls the grenade down every frame
        self.velocity_y += GRAVITY
        delta_x = self.direction * self.speed
        delta_y = self.velocity_y

        # Check collision with level
        for tile in state.world.obstacle_list:
            # Check collision with the walls: bounce back the other way
            if tile[1].colliderect(self.rect.x + delta_x, self.rect.y, self.width, self.height):
                self.direction *= -1
                delta_x = self.direction * self.speed
            # Check collision in y axis
            if tile[1].colliderect(self.rect.x, self.rect.y + delta_y, self.width, self.height):
                self.speed = 0   # stop sliding once it touches floor/ceiling
                # Check if below is ground, i.e. thrown up
                if self.velocity_y < 0:
                    self.velocity_y = 0
                    delta_y = tile[1].bottom - self.rect.top
                # Check if above the ground, i.e. falling
                elif self.velocity_y >= 0:
                    self.velocity_y = 0
                    delta_y = tile[1].top - self.rect.bottom

        # Update Grenade Position (plus world scroll)
        self.rect.x += delta_x + state.screen_scroll
        self.rect.y += delta_y

        # Countdown Timer
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            grenade_sound.play()
            explosion = Explosion(self.rect.centerx, self.rect.centery, 0.5)
            explosion_group.add(explosion)
            # Grenade Damage - AOE (area of effect): anyone within 2 tiles takes 50
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
        # Load the 5 animation frames exp1.png ... exp5.png
        self.images = [load_image(f'images/explosion/exp{num}.png', scale)
                       for num in range(1, 6)]
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        # Scroll
        self.rect.x += state.screen_scroll
        EXPLOSION_SPEED = 4   # game frames per animation frame
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