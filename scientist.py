"""scientist.py - the Scientist enemy, a flask-throwing Enemy.

It also holds the two things that only the scientist creates:
  Flask  - the projectile he throws. It shatters when it lands (or hits the player).
  Sludge - the green puddle left behind. Anything standing in it takes damage over time.
"""
import math

import pygame

import state
from settings import (GRAVITY, SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, screen,
                      SCIENTIST_SPEED, SCIENTIST_HEALTH, SCIENTIST_PATROL_FRAMES,
                      SCIENTIST_THROW_COOLDOWN, SCIENTIST_RELEASE_FRAME,
                      SCIENTIST_DROP_CHANCES, FLASK_SPEED, FLASK_VELOCITY_Y,
                      SLUDGE_DURATION, SLUDGE_FADE_MS, SLUDGE_TICK_INTERVAL,
                      SLUDGE_TICK_DAMAGE, SLUDGE_GROW_FRAMES, SLUDGE_SPREAD_DELAY)
from assets import flask_image
from groups import bullet_group, sludge_group, enemy_group
from character import ACTION_IDLE
from enemy import Enemy

# Animation indices (Idle 0 and Run 1 come from character.py)
ACTION_DEATH = 2
ACTION_ATTACK = 3
SCIENTIST_ANIMATIONS = ['Idle', 'Run', 'Death', 'Attack']   # order must match the ACTION_ numbers


# ---------------------------------------------------------------------------
# Finding the tile a flask / sludge belongs on
# ---------------------------------------------------------------------------
def find_ground_tile(x, y, max_drop=TILE_SIZE):
    """Return the rect of the solid tile you would land on if you dropped from the point (x, y).

    Returns None if the point is inside a wall, or if there is no ground within
    max_drop pixels below it (e.g. a pit). The rect is the world's own rect object,
    so it keeps scrolling with the level."""
    best = None
    for _, rect in state.world.obstacle_list:
        if not (rect.left <= x < rect.right):
            continue
        if rect.top <= y < rect.bottom:
            return None                         # the point is inside a solid tile
        if rect.top >= y and rect.top - y <= max_drop:
            if best is None or rect.top < best.top:
                best = rect
    return best


# ---------------------------------------------------------------------------
# Sludge
# ---------------------------------------------------------------------------
SLUDGE_HEIGHT = 12
SLUDGE_DARK = (84, 124, 70)
SLUDGE_MID = (118, 164, 88)
SLUDGE_LIGHT = (160, 204, 112)
SLUDGE_SHINE = (238, 228, 120)


def make_sludge_surface(width):
    """Draw a flat green puddle, `width` pixels wide, using the flask's own colours."""
    surface = pygame.Surface((width, SLUDGE_HEIGHT), pygame.SRCALPHA)
    for row in range(SLUDGE_HEIGHT):
        # Rows near the top are narrower so the puddle looks like a low dome
        fraction = math.sqrt(1 - ((SLUDGE_HEIGHT - 1 - row) / SLUDGE_HEIGHT) ** 2)
        row_width = max(2, int(width * fraction))
        left = (width - row_width) // 2
        if row >= SLUDGE_HEIGHT - 3:
            colour = SLUDGE_DARK
        elif row >= 5:
            colour = SLUDGE_MID
        else:
            colour = SLUDGE_LIGHT
        pygame.draw.line(surface, colour, (left, row), (left + row_width - 1, row))
    # A few bubbles
    for fraction_x, bubble_y in ((0.3, 4), (0.55, 6), (0.72, 3)):
        surface.set_at((int(width * fraction_x), bubble_y), SLUDGE_SHINE)
    return surface


# Pre-built once: the puddle growing outwards, ending with the full-size one
SLUDGE_FRAMES = [make_sludge_surface(int(TILE_SIZE * (0.3 + 0.7 * i / SLUDGE_GROW_FRAMES)))
                 for i in range(SLUDGE_GROW_FRAMES)]
SLUDGE_FRAMES.append(make_sludge_surface(TILE_SIZE))
NO_IMAGE = pygame.Surface((1, 1), pygame.SRCALPHA)   # shown while waiting to spread


class Sludge(pygame.sprite.Sprite):
    """A puddle sitting on top of one tile. Anything touching it (the player or any
    enemy) loses SLUDGE_TICK_DAMAGE health every SLUDGE_TICK_INTERVAL ms."""

    def __init__(self, tile, delay=0):
        pygame.sprite.Sprite.__init__(self)
        self.tile = tile            # the tile's rect; we follow it so we scroll with the world
        self.delay = delay          # frames to wait before appearing (the spreading effect)
        self.age = 0                # frames since appearing (drives the grow-in)
        self.expire_time = 0
        self.next_tick = {}         # {entity: time of its next damage tick}
        self.image = NO_IMAGE
        self.rect = self.image.get_rect(midbottom=tile.midtop)
        if delay <= 0:
            self.refresh()

    def refresh(self):
        """(Re)start the puddle's lifetime, e.g. when a second flask lands on the same tile."""
        self.expire_time = pygame.time.get_ticks() + SLUDGE_DURATION

    def update(self):
        # Waiting its turn to spread out from the middle tile
        if self.delay > 0:
            self.delay -= 1
            self.rect.midbottom = self.tile.midtop
            if self.delay == 0:
                self.refresh()
            return

        now = pygame.time.get_ticks()
        remaining = self.expire_time - now
        if remaining <= 0:
            self.kill()
            return

        # Grow in, and fade out during the last SLUDGE_FADE_MS
        image = SLUDGE_FRAMES[min(self.age, len(SLUDGE_FRAMES) - 1)]
        self.age += 1
        if remaining < SLUDGE_FADE_MS:
            image = image.copy()
            image.set_alpha(int(255 * remaining / SLUDGE_FADE_MS))
        self.image = image
        self.rect = self.image.get_rect(midbottom=self.tile.midtop)

        self.damage_entities(now)

    def damage_entities(self, now):
        for entity in [state.player] + list(enemy_group):
            if entity.alive and self.rect.colliderect(entity.rect):
                # First contact starts that entity's timer; then one tick per interval
                next_tick = self.next_tick.setdefault(entity, now + SLUDGE_TICK_INTERVAL)
                while now >= next_tick:
                    entity.health -= SLUDGE_TICK_DAMAGE   # check_alive() handles death
                    next_tick += SLUDGE_TICK_INTERVAL
                self.next_tick[entity] = next_tick
            else:
                self.next_tick.pop(entity, None)          # stepped out: reset


def spawn_sludge(tile, delay=0):
    """Put sludge on a tile. If it already has some, just top up its timer."""
    for sludge in sludge_group:
        if sludge.tile is tile:
            if sludge.delay <= 0:
                sludge.refresh()
            return sludge
    sludge = Sludge(tile, delay)
    sludge_group.add(sludge)
    return sludge


# ---------------------------------------------------------------------------
# Flask (the projectile)
# ---------------------------------------------------------------------------
class Flask(pygame.sprite.Sprite):
    """Lobbed like a grenade but on a flatter arc. It shatters on the first ground it
    touches, or on the player, and leaves sludge on the tile it landed on.
    Lives in bullet_group, so main.py updates and draws it for free."""

    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.flip(flask_image, direction == -1, False)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.speed = FLASK_SPEED
        self.velocity_y = FLASK_VELOCITY_Y   # grenade is -11; this is lower and flatter
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        player = state.player

        self.velocity_y += GRAVITY
        delta_x = self.direction * self.speed
        delta_y = self.velocity_y
        landed_on = None

        for _, tile in state.world.obstacle_list:
            # Hit a wall: stop moving sideways and drop straight down
            if tile.colliderect(self.rect.x + delta_x, self.rect.y, self.width, self.height):
                delta_x = 0
                self.speed = 0
            if tile.colliderect(self.rect.x, self.rect.y + delta_y, self.width, self.height):
                if self.velocity_y < 0:       # bumped a ceiling
                    self.velocity_y = 0
                    delta_y = tile.bottom - self.rect.top
                else:                         # coming down onto ground
                    landed_on = tile
                    delta_y = tile.top - self.rect.bottom

        # Move, plus the world scroll so it stays put in the world
        self.rect.x += delta_x + state.screen_scroll
        self.rect.y += delta_y

        # Hit the player: shatter and put sludge on the tile under them
        if player.alive and self.rect.colliderect(player.rect):
            self.shatter(find_ground_tile(player.rect.centerx, player.rect.bottom - 2,
                                          max_drop=SCREEN_HEIGHT))
        elif landed_on is not None:
            self.shatter(landed_on)
        elif self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def shatter(self, tile):
        if tile is not None:
            spawn_sludge(tile)
        self.kill()


# ---------------------------------------------------------------------------
# Scientist
# ---------------------------------------------------------------------------
class Scientist(Enemy):
    """Slow (half a zombie's speed), frail (75% of a soldier's health) enemy with the same
    vision box as a soldier. When it sees the player it throws a flask. When it dies it
    spills sludge across three tiles and may drop a Stimulant (see SCIENTIST_DROP_CHANCES)."""

    animation_folder = 'images/enemy/scientist'
    animation_names = SCIENTIST_ANIMATIONS
    death_action = ACTION_DEATH
    enemy_type = 'scientist'
    drop_chances = SCIENTIST_DROP_CHANCES
    patrol_frames = SCIENTIST_PATROL_FRAMES

    def __init__(self, x, y, scale, speed=SCIENTIST_SPEED):
        # Set before Enemy.__init__ so they exist no matter what it calls
        self.attacking = False       # True while the throw animation is playing
        self.has_thrown = False      # True once this throw's flask has left his hand
        self.attack_cooldown = 0     # frames until he may throw again
        super().__init__(x, y, scale, speed, SCIENTIST_HEALTH)

    # ------------------------------------------------------------------
    # Animation hooks & drawing
    # ------------------------------------------------------------------
    def on_frame_advance(self, frames):
        # The flask leaves his hand part-way through the throw (only once per throw)
        release_frame = min(SCIENTIST_RELEASE_FRAME, len(frames) - 1)
        if (self.action == ACTION_ATTACK and not self.has_thrown and self.alive
                and self.frame_index >= release_frame):
            self.has_thrown = True
            self.throw_flask()

    def on_animation_end(self):
        if self.action == ACTION_ATTACK:   # throw finished
            self.attacking = False
            self.update_action(ACTION_IDLE)
        else:
            self.frame_index = 0

    def draw(self):
        """The Attack frames are wider than Idle/Run (the arm and flask stick out), so
        draw by the body's edge instead of the rect's top-left. Otherwise the scientist
        would slide sideways whenever he turned to face left."""
        image = pygame.transform.flip(self.image, self.direction == -1, False)
        if self.direction == 1:
            x = self.rect.left
        else:
            x = self.rect.right - image.get_width()
        screen.blit(image, (x, self.rect.bottom - image.get_height()))

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------
    def start_attack(self):
        self.attacking = True
        self.has_thrown = False
        self.attack_cooldown = SCIENTIST_THROW_COOLDOWN
        self.update_action(ACTION_ATTACK)

    def throw_flask(self):
        # From his raised hand, a little in front of him
        x = self.rect.centerx + self.direction * self.rect.width * 0.6
        y = self.rect.top + self.rect.height * 0.2
        bullet_group.add(Flask(x, y, self.direction))

    def update(self):
        super().update()
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def on_death(self):
        super().on_death()   # loot + kill quota
        self.attacking = False
        self.spill_sludge()

    def spill_sludge(self):
        """Sludge on the tile he dies on, then the tiles either side of it a moment later,
        so it looks like it spreads outwards from the middle."""
        x = self.rect.centerx
        y = self.rect.bottom - 2
        for tile_offset, delay in ((0, 0), (-1, SLUDGE_SPREAD_DELAY), (1, SLUDGE_SPREAD_DELAY)):
            tile = find_ground_tile(x + tile_offset * TILE_SIZE, y)
            if tile is not None:   # skip walls and pits
                spawn_sludge(tile, delay)

    # ------------------------------------------------------------------
    # AI
    # ------------------------------------------------------------------
    def think(self, player):
        # Commit to the throw: stand still until it finishes
        if self.attacking:
            return

        if self.vision.colliderect(player.rect):
            if self.attack_cooldown == 0:
                self.start_attack()
            else:
                self.update_action(ACTION_IDLE)   # wait until he can throw again
            return

        # Nothing in sight: shuffle back and forth
        self.patrol()