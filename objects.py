import pygame

import state
from settings import TILE_SIZE, WEAPONS
from assets import item_boxes


class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        player = state.player

        # Scroll
        self.rect.x += state.screen_scroll
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