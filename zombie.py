"""zombie.py - the Zombie enemy, a melee Enemy."""
import pygame

import state
from settings import (ZOMBIE_SPEED, ZOMBIE_HEALTH, ZOMBIE_ATTACK_RANGE,
                      ZOMBIE_ATTACK_DAMAGE, ZOMBIE_ATTACK_COOLDOWN, ZOMBIE_PATROL_FRAMES,
                      ZOMBIE_DROP_CHANCES)
from character import ACTION_IDLE, ACTION_RUN
from enemy import Enemy

# Animation indices (zombies can't jump, so there is no Jump animation).
# Idle (0) and Run (1) come from character.py.
ACTION_DEATH = 2
ACTION_ATTACK = 3
ZOMBIE_ANIMATIONS = ['Idle', 'Run', 'Death', 'Attack']   # order must match the ACTION_ numbers above


class Zombie(Enemy):
    """A melee enemy. Slower and tougher than a Soldier, it chases the player once it sees
    them and claws instead of shooting. On death it can drop a Mutated Stimulant
    (see ZOMBIE_DROP_CHANCES)."""

    animation_folder = 'images/enemy/zombie'
    animation_names = ZOMBIE_ANIMATIONS
    death_action = ACTION_DEATH
    enemy_type = 'zombie'
    drop_chances = ZOMBIE_DROP_CHANCES
    patrol_frames = ZOMBIE_PATROL_FRAMES

    def __init__(self, x, y, scale, speed=ZOMBIE_SPEED):
        # Set before Enemy.__init__ so they exist no matter what it calls
        self.attacking = False       # True while a swing is playing
        self.has_hit = False         # True once this swing's damage has been dealt
        self.attack_cooldown = 0     # frames until the next swing is allowed
        super().__init__(x, y, scale, speed, ZOMBIE_HEALTH)

    # ------------------------------------------------------------------
    # Animation hooks
    # ------------------------------------------------------------------
    def on_frame_advance(self, frames):
        # The claw lands halfway through the swing (only once per swing)
        if (self.action == ACTION_ATTACK and not self.has_hit
                and self.frame_index >= len(frames) // 2):
            self.has_hit = True
            self.deal_damage()

    def on_animation_end(self):
        if self.action == ACTION_ATTACK:   # swing finished
            self.attacking = False
            self.update_action(ACTION_IDLE)
        else:
            self.frame_index = 0

    def update(self):
        super().update()
        # Count down the delay between swings
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def on_death(self):
        super().on_death()   # loot + kill quota
        self.attacking = False

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------
    def attack_rect(self):
        """The area in front of the zombie that its claws can reach."""
        reach = self.rect.width // 2 + ZOMBIE_ATTACK_RANGE
        if self.direction == 1:
            left = self.rect.centerx
        else:
            left = self.rect.centerx - reach
        return pygame.Rect(left, self.rect.top, reach, self.rect.height)

    def start_attack(self):
        self.attacking = True
        self.has_hit = False
        self.attack_cooldown = ZOMBIE_ATTACK_COOLDOWN
        self.update_action(ACTION_ATTACK)

    def deal_damage(self):
        # Called mid-swing: only hurts if the player is STILL inside the claw area
        player = state.player
        if self.alive and player.alive and self.attack_rect().colliderect(player.rect):
            player.health -= ZOMBIE_ATTACK_DAMAGE

    # ------------------------------------------------------------------
    # AI
    # ------------------------------------------------------------------
    def think(self, player):
        # Commit to the swing: stand still until it finishes
        if self.attacking:
            return

        if self.vision.colliderect(player.rect):
            # Spotted the player: stop idling and go for them
            self.idling = False
            if self.attack_rect().colliderect(player.rect):
                # Close enough to claw
                if self.attack_cooldown == 0:
                    self.start_attack()
                else:
                    self.update_action(ACTION_IDLE)  # wait for the next swing
            else:
                # Too far: keep walking toward the player
                self.move(self.direction == -1, self.direction == 1)
                self.update_action(ACTION_RUN)
            return

        # Nothing in sight: shamble back and forth
        self.patrol()