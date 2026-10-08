import random

import pygame

import state
from settings import (ZOMBIE_SPEED, ZOMBIE_HEALTH, ZOMBIE_ATTACK_RANGE,
                      ZOMBIE_ATTACK_DAMAGE, ZOMBIE_ATTACK_COOLDOWN, ZOMBIE_PATROL_FRAMES,
                      ZOMBIE_DROP_CHANCES)
from assets import load_frames
from soldier import Soldier

# Animation indices (zombies can't jump, so there is no Jump animation).
# Soldier uses its own death_action index, which Zombie overrides below.
ACTION_IDLE = 0
ACTION_RUN = 1
ACTION_DEATH = 2
ACTION_ATTACK = 3
ZOMBIE_ANIMATIONS = ['Idle', 'Run', 'Death', 'Attack']

ANIMATION_COOLDOWN = 100  # ms per frame, same as Soldier


class Zombie(Soldier):
    """A melee enemy. Same physics, vision box and collision as a Soldier, but it is
    slower, tougher, chases the player once it sees them, and claws instead of shooting.
    On death it can drop a Mutated Stimulant (see ZOMBIE_DROP_CHANCES)."""

    drop_chances = ZOMBIE_DROP_CHANCES  # Soldier.drop_loot() reads this
    death_action = ACTION_DEATH         # Soldier.check_alive() plays this on death

    def __init__(self, x, y, scale, speed=ZOMBIE_SPEED):
        # Set before Soldier.__init__ so they exist no matter what it calls
        self.attacking = False
        self.has_hit = False
        self.attack_cooldown = 0

        # One dummy 'weapon' so Soldier's per-gun animation lookup keeps working.
        # Zombies never shoot, so no ammo or grenades.
        super().__init__('enemy', ['melee'], x, y, scale, speed, {'melee': 0}, 0)

        self.health = ZOMBIE_HEALTH
        self.max_health = self.health

    # ------------------------------------------------------------------
    # Animations
    # ------------------------------------------------------------------
    def load_animations(self, scale):
        """images/enemy/zombie/<Idle|Run|Death|Attack>/<n>.png"""
        animations = []
        for animation in ZOMBIE_ANIMATIONS:
            path = f'images/enemy/zombie/{animation}'
            frames = load_frames(path, scale)
            animations.append(frames)
        self.animations[self.gun_type] = animations

    def update_animation(self):
        frames = self.current_frames()

        if self.frame_index >= len(frames):
            self.frame_index = 0
        self.image = frames[self.frame_index]

        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

            # The claw lands halfway through the swing
            if (self.action == ACTION_ATTACK and not self.has_hit
                    and self.frame_index >= len(frames) // 2):
                self.has_hit = True
                self.deal_damage()

        if self.frame_index >= len(frames):
            if self.action == ACTION_DEATH:      # hold the last frame
                self.frame_index = len(frames) - 1
            elif self.action == ACTION_ATTACK:   # swing finished
                self.attacking = False
                self.update_action(ACTION_IDLE)
            else:
                self.frame_index = 0

    def update(self):
        super().update()
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

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
        player = state.player
        if self.alive and player.alive and self.attack_rect().colliderect(player.rect):
            player.health -= ZOMBIE_ATTACK_DAMAGE

    def check_alive(self):
        super().check_alive()
        if not self.alive:
            self.attacking = False

    # ------------------------------------------------------------------
    # AI
    # ------------------------------------------------------------------
    def ai(self):
        player = state.player

        # Scroll first so the vision box and rect stay in sync with the world
        self.rect.x += state.screen_scroll

        if not (self.alive and player.alive):
            return

        # Same vision box as a Soldier (150 x 20, centred 75px in front)
        self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

        # Commit to the swing: stand still until it finishes
        if self.attacking:
            return

        if self.vision.colliderect(player.rect):
            # Spotted the player: stop idling and go for them
            self.idling = False
            if self.attack_rect().colliderect(player.rect):
                if self.attack_cooldown == 0:
                    self.start_attack()
                else:
                    self.update_action(ACTION_IDLE)  # wait for the next swing
            else:
                self.move(self.direction == -1, self.direction == 1)
                self.update_action(ACTION_RUN)
            return

        # Nothing in sight: shamble back and forth like a Soldier patrol
        if not self.idling and random.randint(1, 200) == 1:
            self.update_action(ACTION_IDLE)
            self.idling = True
            self.idling_counter = 50

        if not self.idling:
            self.move(self.direction == -1, self.direction == 1)
            self.update_action(ACTION_RUN)
            self.move_counter += 1
            if self.move_counter > ZOMBIE_PATROL_FRAMES:
                self.direction *= -1
                self.move_counter *= -1
        else:
            self.idling_counter -= 1
            if self.idling_counter <= 0:
                self.idling = False