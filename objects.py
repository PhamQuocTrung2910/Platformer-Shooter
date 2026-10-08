import pygame

import state
from settings import (TILE_SIZE, WEAPONS, GRAVITY, MAX_FALL_SPEED, SCREEN_HEIGHT,
                      MAGAZINE_AMMO_FRACTION, SYRINGE_HEAL)
from assets import item_boxes


class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def can_pick_up(self, player):
        """Mutated stimulants can't be picked up while already stimulated (no stacking)."""
        if self.item_type == 'MutatedStimulant':
            return player.alive and not player.stimulated
        return True

    def update(self):
        # Scroll
        self.rect.x += state.screen_scroll
        # Checking if player has picked up box
        if pygame.sprite.collide_rect(self, state.player) and self.can_pick_up(state.player):
            self.apply_effect(state.player)
            # Delete item box
            self.kill()

    def apply_effect(self, player):
        """Give the player whatever this item type provides."""
        if self.item_type == 'Health':
            player.health = min(player.health + 25, player.max_health)
        elif self.item_type == 'Ammo':
            # Refill every weapon so you're never stuck on an empty gun
            for gun in player.guns:
                player.ammo[gun] += WEAPONS[gun]['pickup']
        elif self.item_type == 'Grenade':
            player.grenades += 3
        elif self.item_type == 'Magazine':
            # A smaller top-up than an ammo box, for every weapon
            for gun in player.guns:
                player.ammo[gun] += max(1, int(WEAPONS[gun]['pickup'] * MAGAZINE_AMMO_FRACTION))
        elif self.item_type == 'Syringe':
            player.health = min(player.health + SYRINGE_HEAL, player.max_health)
        elif self.item_type == 'MutatedStimulant':
            player.apply_stimulant()


class DroppedItem(ItemBox):
    """An ItemBox dropped by a dead enemy: pops up, falls, lands on the ground,
    then behaves exactly like a normal item box."""

    def __init__(self, item_type, x, y):
        super().__init__(item_type, 0, 0)
        self.rect.midbottom = (x, y)
        self.velocity_y = -6   # little pop upwards
        self.on_ground = False

    def update(self):
        if not self.on_ground:
            self.fall()
        super().update()  # scroll + pickup check

    def fall(self):
        self.velocity_y = min(self.velocity_y + GRAVITY, MAX_FALL_SPEED)
        delta_y = self.velocity_y

        for tile in state.world.obstacle_list:
            if tile[1].colliderect(self.rect.x, self.rect.y + delta_y,
                                   self.rect.width, self.rect.height):
                if self.velocity_y < 0:    # bumped a ceiling
                    self.velocity_y = 0
                    delta_y = tile[1].bottom - self.rect.top
                else:                      # landed
                    self.velocity_y = 0
                    delta_y = tile[1].top - self.rect.bottom
                    self.on_ground = True

        self.rect.y += delta_y

        # Fell into a pit
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class _ScrollingTile(pygame.sprite.Sprite):
    """Base for static level objects that just scroll with the world."""

    def __init__(self, image, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += state.screen_scroll


class Decoration(_ScrollingTile):
    pass


class Exit(_ScrollingTile):
    pass


class Water(_ScrollingTile):
    pass