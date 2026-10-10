"""objects.py - things sitting in the level: pickups, decorations, exit and water.

None of these move on their own (except dropped items falling). They only
scroll left/right with the world as the player moves.
"""
import pygame

import state
from settings import (TILE_SIZE, WEAPONS, GRAVITY, MAX_FALL_SPEED, SCREEN_HEIGHT,
                      MAGAZINE_AMMO_FRACTION, SYRINGE_HEAL)
from assets import item_boxes


class ItemBox(pygame.sprite.Sprite):
    """A pickup. When the player touches it, it applies its effect and disappears."""

    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        # Centre it horizontally in its tile and sit it on the bottom of the tile
        # (the images are smaller than a tile)
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def can_pick_up(self, player):
        """Mutated stimulants can't be picked up while already stimulated (no stacking)."""
        if self.item_type == 'MutatedStimulant':
            return player.alive and not player.stimulated
        return True

    def update(self):
        # Scroll with the world
        self.rect.x += state.screen_scroll
        # Checking if player has picked up box
        if pygame.sprite.collide_rect(self, state.player) and self.can_pick_up(state.player):
            self.apply_effect(state.player)
            # Delete item box
            self.kill()

    def apply_effect(self, player):
        """Give the player whatever this item type provides."""
        if self.item_type == 'Health':
            # min() stops health going above the maximum
            player.health = min(player.health + 25, player.max_health)
        elif self.item_type == 'Ammo':
            # Refill every weapon so you're never stuck on an empty gun
            for gun in player.guns:
                player.ammo[gun] += WEAPONS[gun]['pickup']
        elif self.item_type == 'Grenade':
            player.grenades += 3
        elif self.item_type == 'Magazine':
            # A smaller top-up than an ammo box, for every weapon
            # (max(1, ...) guarantees at least 1 round)
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
        # Start where the enemy died instead of on a tile
        self.rect.midbottom = (x, y)
        self.velocity_y = -6   # little pop upwards
        self.on_ground = False

    def update(self):
        # Only fall until we've landed once
        if not self.on_ground:
            self.fall()
        super().update()  # scroll + pickup check

    def fall(self):
        # Gravity pulls down each frame, capped at terminal velocity
        self.velocity_y = min(self.velocity_y + GRAVITY, MAX_FALL_SPEED)
        delta_y = self.velocity_y

        # Check where we WOULD be after moving; if that overlaps a tile, snap to its edge
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


# These three behave identically; separate classes just give them clear names
# and let each have its own group (water kills, exit ends the level).
class Decoration(_ScrollingTile):
    pass


class Exit(_ScrollingTile):
    pass


class Water(_ScrollingTile):
    pass