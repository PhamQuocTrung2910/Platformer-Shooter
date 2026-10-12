"""enemy.py - Enemy: the base class for every computer-controlled character.

Adds, on top of Character: the vision box, idle/patrol behaviour, turning at walls and
platform edges, loot drops, and counting towards the level's kill quota.

A subclass only has to describe itself (class attributes) and implement think(player),
which runs every frame while both it and the player are alive.
"""
import random

import pygame

import state
from settings import TILE_SIZE
from character import Character, ACTION_IDLE, ACTION_RUN
from groups import item_box_group
from objects import DroppedItem


class Enemy(Character):
    enemy_type = 'enemy'        # kill-quota bucket (also the key in settings.ENEMY_SHORT_NAMES)
    drop_chances = {}           # {item_name: chance 0-1}, each rolled separately on death
    patrol_frames = TILE_SIZE   # frames walked before turning round
    vision_size = (150, 20)     # box in front of the enemy; if the player is in it, it reacts
    vision_offset = 75          # how far in front of the enemy that box is centred

    def __init__(self, x, y, scale, speed, health=100):
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, *self.vision_size)
        self.idling = False
        self.idling_counter = 0
        super().__init__(x, y, scale, speed, health)

    # ------------------------------------------------------------------
    # Death
    # ------------------------------------------------------------------
    def on_death(self):
        self.drop_loot()
        # Counts towards the level's kill quota
        state.kills[self.enemy_type] = state.kills.get(self.enemy_type, 0) + 1

    def drop_loot(self):
        """Roll each item in drop_chances and spawn the ones that succeed."""
        drops = [item for item, chance in self.drop_chances.items() if random.random() < chance]
        for i, item_type in enumerate(drops):
            # Spread multiple drops apart so they don't sit on top of each other
            offset = (i - (len(drops) - 1) / 2) * 40
            item_box_group.add(DroppedItem(item_type, int(self.rect.centerx + offset), self.rect.centery))

    # ------------------------------------------------------------------
    # Movement tweaks: enemies turn round instead of walking into walls or off ledges
    # ------------------------------------------------------------------
    def on_wall_hit(self):
        self.direction *= -1
        self.move_counter = 0

    def adjust_motion(self, delta_x, delta_y):
        # Look just under the leading foot: if there is no solid tile there, don't step.
        # (Skipped while falling, e.g. when first spawning, so they can still drop to the ground.)
        if delta_x != 0 and self.velocity_y < 2:
            step = 1 if delta_x > 0 else -1
            probe_x = self.rect.centerx + step * (self.rect.width // 4) + delta_x
            probe = pygame.Rect(probe_x - 1, self.rect.bottom - 2, 3, 6)
            if not any(tile[1].colliderect(probe) for tile in state.world.near_tiles):
                delta_x = 0
                self.x_remainder = 0.0
                self.direction *= -1
                self.move_counter = 0
        return delta_x, delta_y

    # ------------------------------------------------------------------
    # AI
    # ------------------------------------------------------------------
    def ai(self):
        """Called by main.py every frame. Scrolls with the world, then lets the subclass think."""
        player = state.player

        # Scroll first so the vision box and rect stay in sync with the world
        self.rect.x += state.screen_scroll

        if not (self.alive and player.alive):
            return

        self.vision.center = (self.rect.centerx + self.vision_offset * self.direction,
                              self.rect.centery)
        self.think(player)

    def think(self, player):
        """Override: decide what to do this frame."""

    # Building blocks subclasses can mix and match inside think()
    def roll_idle(self):
        """Randomly stop to idle (about once every 200 frames)."""
        if not self.idling and random.randint(1, 200) == 1:
            self.update_action(ACTION_IDLE)
            self.idling = True
            self.idling_counter = 50

    def patrol_step(self):
        """Walk back and forth, or stand still while idling."""
        if not self.idling:
            self.move(self.direction == -1, self.direction == 1)
            self.update_action(ACTION_RUN)
            self.move_counter += 1
            # After walking patrol_frames, turn round. Multiplying by -1 makes the
            # counter count back up for the return trip.
            if self.move_counter > self.patrol_frames:
                self.direction *= -1
                self.move_counter *= -1
        else:
            self.idling_counter -= 1
            if self.idling_counter <= 0:
                self.idling = False

    def patrol(self):
        self.roll_idle()
        self.patrol_step()