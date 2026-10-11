"""objects.py - things sitting in the level: pickups, decorations, exit and water.

None of these move on their own (except dropped items falling). They only
scroll left/right with the world as the player moves.
"""
import pygame

import state
from settings import (TILE_SIZE, WEAPONS, GRAVITY, MAX_FALL_SPEED, SCREEN_HEIGHT,
                      MAGAZINE_AMMO_FRACTION, SYRINGE_HEAL, PAD_HITBOX_HEIGHT,
                      LAUNCHER_VELOCITY, MEDPAD_HEAL, MEDPAD_INTERVAL)
from assets import item_boxes, jump_sound


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
        if self.item_type == 'MutatedStimulant':
            return player.can_take_stimulant(mutated=True)
        if self.item_type == 'Stimulant':
            return player.can_take_stimulant(mutated=False)
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
            player.take_stimulant(mutated=True)    # overdoses if a normal one is active
        elif self.item_type == 'Stimulant':
            player.take_stimulant(mutated=False)   # overdoses if a mutated one is active


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


# ---------------------------------------------------------------------------
# Lab effect pads (tiles 23-28). Not solid: you walk over them and they act on
# the PLAYER while you touch the bottom strip of the tile.
# ---------------------------------------------------------------------------
class EffectPad(_ScrollingTile):
    def __init__(self, image, x, y):
        super().__init__(image, x, y)
        # Only the bottom strip of the tile counts, so jumping through the empty
        # top of the cell doesn't trigger it
        self.hitbox = pygame.Rect(0, 0, TILE_SIZE, PAD_HITBOX_HEIGHT)
        self.hitbox.midbottom = self.rect.midbottom

    def update(self):
        super().update()   # scroll with the world
        self.hitbox.midbottom = self.rect.midbottom
        player = state.player
        if player.alive and self.hitbox.colliderect(player.rect):
            self.trigger(player)

    def trigger(self, player):
        pass


class ElectricTrap(EffectPad):
    """Slows movement AND shooting for a few seconds (refreshes while you stand on it)."""
    def trigger(self, player):
        player.apply_shock()


class SpeedPad(EffectPad):
    """Doubles movement speed for a few seconds."""
    def trigger(self, player):
        player.apply_speed_boost()


class LauncherPad(EffectPad):
    """Fires the player about 3 tiles straight up."""
    def __init__(self, image, x, y):
        super().__init__(image, x, y)

    def trigger(self, player):
        # Only launch when not already rising, so one touch = one launch
        if player.velocity_y >= 0:
            player.launch(LAUNCHER_VELOCITY)
            jump_sound.play()


class MedPad(EffectPad):
    """Heals a little every half second while you stand on it."""
    def __init__(self, image, x, y):
        super().__init__(image, x, y)
        self.next_heal = 0

    def trigger(self, player):
        now = pygame.time.get_ticks()
        if now >= self.next_heal and player.health < player.max_health:
            player.health = min(player.health + MEDPAD_HEAL, player.max_health)
            self.next_heal = now + MEDPAD_INTERVAL