"""player.py - the Player: keyboard-driven character with weapons, grenades,
stimulant buffs, lab pad effects, overdose and the world-scrolling camera.
(Enemies live in enemy.py and the files that inherit from it.)"""
import pygame

import state
from settings import (SCREEN_WIDTH, SCROLL_THRESHOLD, TILE_SIZE, WEAPONS, ANIMATION_TYPES,
                      PLAYER_HEALTH, EXIT_BLOCKED_FLASH_MS,
                      STIM_DURATION, STIM_DRAIN_INTERVAL, STIM_DRAIN_AMOUNT,
                      STIM_SPEED_MULT, STIM_FIRE_RATE_MULT,
                      OVERDOSE_HEALTH_LOSS, OVERDOSE_DURATION,
                      SHOCK_DURATION, SHOCK_SPEED_MULT, SHOCK_FIRE_RATE_MULT,
                      BOOST_DURATION, BOOST_SPEED_MULT)
from assets import load_frames
from groups import exit_group, grenade_group
from character import Character
from projectiles import Grenade, spawn_bullets


class Player(Character):
    animation_names = ANIMATION_TYPES      # Idle, Run, Jump, Death
    death_action = 3
    hitbox_width = TILE_SIZE - 10          # narrower than a tile so the player fits through 1-tile gaps

    def __init__(self, x, y, scale, speed, guns, ammo, grenades):
        # Set before Character.__init__ because it loads animations (which need the guns)
        self.guns = guns
        self.gun_type = guns[0]                # start with the first gun in the list
        self.ammo = dict(ammo)                 # {gun_name: rounds} (copied so nothing shares one dict)
        self.grenades = grenades
        self.shoot_cooldown = 0
        self.fire_rate_multiplier = 1.0

        # Stimulant (buff) state
        self.stimulated = False
        self.stim_end_time = 0
        self.stim_next_drain = 0
        self.mutated = False         # True = the stimulant came from a zombie (drains health)

        # Lab pad effects
        self.shocked = False         # electric trap: slower movement and shooting
        self.shock_end_time = 0
        self.boosted = False         # speed pad: faster movement
        self.boost_end_time = 0

        # Overdose state (normal stimulant taken while mutated)
        self.overdosed = False
        self.overdose_end_time = 0

        super().__init__(x, y, scale, speed, PLAYER_HEALTH)

    # ------------------------------------------------------------------
    # Animations: the player has one full set per gun
    # ------------------------------------------------------------------
    def load_animations(self, scale):
        """images/player/<gun>/<Idle|Run|Jump|Death>/<n>.png"""
        animations = {}
        for gun in self.guns:
            animations[gun] = [load_frames(f'images/player/{gun}/{name}', scale)
                               for name in self.animation_names]
        return animations

    def current_frames(self):
        return self.animations[self.gun_type][self.action]

    def switch_weapon(self, gun_type):
        # Only switch to a gun we own, and only if it's actually different
        if gun_type in self.guns and gun_type != self.gun_type:
            self.gun_type = gun_type
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()
            self.shoot_cooldown = 0   # no waiting after swapping

    def update(self):
        self.update_overdose()
        self.update_stimulant()
        self.update_pad_effects()
        super().update()   # animation + alive check
        # Update cooldown (a stimulated player counts it down faster)
        if self.shoot_cooldown > 0:
            self.shoot_cooldown = max(0, self.shoot_cooldown - self.fire_rate_multiplier)

    # ------------------------------------------------------------------
    # Weapons
    # ------------------------------------------------------------------
    def shoot(self):
        weapon = WEAPONS[self.gun_type]
        # Only fire if the gun has cooled down and there is ammo
        if self.shoot_cooldown <= 0 and self.ammo[self.gun_type] > 0:
            self.shoot_cooldown = weapon['cooldown']
            spawn_x = self.rect.centerx + 0.75 * self.rect.width * self.direction
            spawn_bullets('player', weapon, spawn_x, self.rect.centery, self.direction,
                          weapon['damage'])
            self.ammo[self.gun_type] -= 1   # one per shot, not per pellet

    def throw_grenade(self):
        """Throw one grenade. Returns False if there are none left."""
        if self.grenades <= 0:
            return False
        grenade_group.add(Grenade(self.rect.centerx + 0.5 * self.rect.width * self.direction,
                                  self.rect.top, self.direction))
        self.grenades -= 1
        return True

    # ------------------------------------------------------------------
    # Stimulants
    # ------------------------------------------------------------------
    def apply_stimulant(self, mutated=True):
        """Start the buff. mutated=True (zombie drop) drains health while it lasts;
        mutated=False (scientist drop) is a clean buff. Returns False if it can't start."""
        if self.stimulated or self.overdosed or not self.alive:
            return False
        now = pygame.time.get_ticks()
        self.stimulated = True
        self.mutated = mutated
        self.stim_end_time = now + STIM_DURATION
        self.stim_next_drain = now + STIM_DRAIN_INTERVAL
        self.recalc_stats()
        return True

    def end_stimulant(self):
        # Back to normal speed and fire rate
        self.stimulated = False
        self.mutated = False
        self.recalc_stats()

    def update_stimulant(self):
        if not self.stimulated:
            return
        if not self.alive:
            self.end_stimulant()
            return
        now = pygame.time.get_ticks()
        # Only the MUTATED stimulant drains health. A while loop (not an if) so that
        # no ticks are missed if a frame takes a long time.
        while self.mutated and self.stim_next_drain <= min(now, self.stim_end_time):
            self.health -= STIM_DRAIN_AMOUNT   # check_alive() handles death
            self.stim_next_drain += STIM_DRAIN_INTERVAL
        if now >= self.stim_end_time:
            self.end_stimulant()

    def can_take_stimulant(self, mutated):
        """Can this kind of stimulant be picked up right now?
        Same kind twice = no stacking. Different kinds together = overdose (allowed)."""
        if not self.alive or self.overdosed:
            return False
        return (not self.stimulated) or (self.mutated != mutated)

    def take_stimulant(self, mutated):
        """Single entry point for pickups. Mutated + normal active together, in
        EITHER order, always causes an overdose."""
        if not self.can_take_stimulant(mutated):
            return False
        if self.stimulated:          # the other kind is already active
            self.apply_overdose()
            return True
        return self.apply_stimulant(mutated)

    # ------------------------------------------------------------------
    # Speed / fire rate from every active effect
    # ------------------------------------------------------------------
    def recalc_stats(self):
        """Combine all active effects (stimulant, speed boost, shock) into the
        speed and fire-rate multipliers. Call whenever an effect starts or ends."""
        speed_mult = 1.0
        fire_mult = 1.0
        if self.stimulated:
            speed_mult *= STIM_SPEED_MULT
            fire_mult *= STIM_FIRE_RATE_MULT
        if self.boosted:
            speed_mult *= BOOST_SPEED_MULT
        if self.shocked:
            speed_mult *= SHOCK_SPEED_MULT
            fire_mult *= SHOCK_FIRE_RATE_MULT
        self.fire_rate_multiplier = fire_mult
        if not self.alive:
            self.speed = 0
        elif speed_mult == 1.0:
            self.speed = self.base_speed
        else:
            # rect positions are whole pixels, so round (and never stop completely)
            self.speed = max(1, int(self.base_speed * speed_mult + 0.5))

    # ------------------------------------------------------------------
    # Lab pad effects
    # ------------------------------------------------------------------
    def apply_shock(self):
        if not self.alive:
            return
        self.shock_end_time = pygame.time.get_ticks() + SHOCK_DURATION   # refreshes while on the trap
        if not self.shocked:
            self.shocked = True
            self.recalc_stats()

    def apply_speed_boost(self):
        if not self.alive:
            return
        self.boost_end_time = pygame.time.get_ticks() + BOOST_DURATION
        if not self.boosted:
            self.boosted = True
            self.recalc_stats()

    def launch(self, velocity):
        """Launcher pad: shoot upward (negative = up)."""
        self.velocity_y = velocity
        self.in_air = True
        self.jump = False

    def update_pad_effects(self):
        now = pygame.time.get_ticks()
        changed = False
        if self.shocked and (not self.alive or now >= self.shock_end_time):
            self.shocked = False
            changed = True
        if self.boosted and (not self.alive or now >= self.boost_end_time):
            self.boosted = False
            changed = True
        if changed:
            self.recalc_stats()

    # ------------------------------------------------------------------
    # Overdose
    # ------------------------------------------------------------------
    def apply_overdose(self):
        """Normal stimulant on top of a mutated one: lose 70% of current health
        (never below 1), lose the buff, and be unable to move for a few seconds."""
        self.end_stimulant()
        self.health = max(1, round(self.health * (1 - OVERDOSE_HEALTH_LOSS)))
        self.overdosed = True
        self.overdose_end_time = pygame.time.get_ticks() + OVERDOSE_DURATION
        self.jump = False

    def update_overdose(self):
        if self.overdosed and (not self.alive or pygame.time.get_ticks() >= self.overdose_end_time):
            self.overdosed = False

    # ------------------------------------------------------------------
    # Status (read by the HUD status bar)
    # ------------------------------------------------------------------
    def get_statuses(self):
        """List of (name, ms_left, ms_total) for every active effect.
        If nothing is active: [('Normal', None, None)]."""
        now = pygame.time.get_ticks()
        statuses = []
        if self.overdosed:
            statuses.append(('Overdosed', max(0, self.overdose_end_time - now), OVERDOSE_DURATION))
        if self.stimulated:
            name = 'Mutated' if self.mutated else 'Stimulated'
            statuses.append((name, max(0, self.stim_end_time - now), STIM_DURATION))
        if self.boosted:
            statuses.append(('Boosted', max(0, self.boost_end_time - now), BOOST_DURATION))
        if self.shocked:
            statuses.append(('Shocked', max(0, self.shock_end_time - now), SHOCK_DURATION))
        return statuses or [('Normal', None, None)]

    # ------------------------------------------------------------------
    # Movement: Character.move() plus the exit and the scrolling camera
    # ------------------------------------------------------------------
    def move(self, moving_left, moving_right):
        """Returns (scroll, level_complete): scroll is how far the WORLD should shift."""
        # Overdosed: frozen in place (gravity still applies)
        if self.overdosed:
            moving_left = moving_right = False
            self.jump = False

        level_complete = self.check_exit()
        delta_x = super().move(moving_left, moving_right)

        # Scroll: if the player is in the scroll zone near either edge (and the level isn't
        # at its end), undo the player's movement and shift the whole world the other way
        scroll = 0
        world = state.world
        if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESHOLD
                and state.background_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH) \
                or (self.rect.left < SCROLL_THRESHOLD and state.background_scroll > abs(delta_x)):
            self.rect.x -= delta_x
            scroll = -delta_x
        return scroll, level_complete

    def check_exit(self):
        """True if the player is on the exit AND the kill quota is met."""
        if pygame.sprite.spritecollide(self, exit_group, False):
            if state.quota_met():
                return True
            # Locked: make the HUD kill counter flash
            state.exit_blocked_until = pygame.time.get_ticks() + EXIT_BLOCKED_FLASH_MS
        return False

    def adjust_motion(self, delta_x, delta_y):
        # Can't walk off the edge of the screen
        if self.rect.left + delta_x < 0 or self.rect.right + delta_x > SCREEN_WIDTH:
            delta_x = 0
        # Never rise above the top of the level (stops heads going through the ceiling art)
        if self.rect.top + delta_y < 0:
            delta_y = -self.rect.top
            self.velocity_y = 0
        return delta_x, delta_y