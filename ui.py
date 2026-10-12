"""ui.py - everything drawn on top of / behind the game: text, background, HUD,
health bar and the screen fades."""
import pygame

import state
from settings import (screen, hud, SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_GUNS,
                      BACKGROUND_COLOURS, RED, WHITE, GREEN, BLACK,
                      HUD_ACTIVE_COLOUR, HUD_INACTIVE_COLOUR,
                      HUD_BG_COLOUR, HUD_LINE_COLOUR, GRENADE_X, HUD_HEIGHT,
                      HUD_X, HUD_WIDTH, SLOT_WIDTH, SLOT_HEIGHT, SLOT_GAP, SLOT_Y,
                      LOW_AMMO, LOW_AMMO_COLOUR, KILL_TEXT_X, ENEMY_SHORT_NAMES,
                      font, small_font)
from assets import (BACKGROUNDS, bullet_image, grenade_image,
                    weapon_icons, faded_weapon_icons)

# Bullet icon scaled 2x once (used by the ammo counter)
big_bullet = pygame.transform.scale(
    bullet_image, (bullet_image.get_width() * 2, bullet_image.get_height() * 2))

# Status bar colours (effect name -> bar colour)
STATUS_COLOURS = {
    'Normal':     (120, 120, 120),
    'Stimulated': (255, 200, 40),
    'Mutated':    (160, 64, 210),
    'Overdosed':  (220, 40, 40),
    'Boosted':    (60, 220, 200),
    'Shocked':    (110, 150, 255),
}


def draw_text(text, font, text_colour, x, y, surface=None):
    # Turn the text into an image, then draw it at (x, y) (on the game area unless told otherwise)
    image = font.render(text, True, text_colour)
    (surface or screen).blit(image, (x, y))


def draw_background():
    theme = state.background_theme
    screen.fill(BACKGROUND_COLOURS[theme])
    scroll = state.background_scroll
    # Parallax: each layer moves by a different fraction of the scroll, so slower
    # layers look farther away. Only the copies that are actually on screen are drawn.
    for image, speed, gap_from_bottom in BACKGROUNDS[theme]:
        width = image.get_width()
        y = 0 if gap_from_bottom is None else SCREEN_HEIGHT - image.get_height() - gap_from_bottom
        offset = scroll * speed
        first = int(offset // width)              # first copy that is on screen
        copies = SCREEN_WIDTH // width + 2        # enough copies to cover the screen
        for i in range(first, first + copies):
            screen.blit(image, (i * width - offset, y))


def draw_hud_background():
    """Blank HUD strip (also used on the menu / win screens)."""
    hud.fill(HUD_BG_COLOUR)
    pygame.draw.line(hud, HUD_LINE_COLOUR, (0, HUD_HEIGHT - 1), (SCREEN_WIDTH, HUD_HEIGHT - 1), 2)


def draw_hud():
    """The whole HUD strip: health bar, grenades, weapon slots + ammo, status bars."""
    draw_hud_background()
    state.health_bar.draw(state.player.health)
    draw_weapon_hud()
    draw_kill_counter()
    draw_status_bar()


def draw_weapon_hud():
    """Weapon slots (current one highlighted), ammo icons and grenade icons."""
    player = state.player

    # One slot per weapon showing its key, name and rounds left
    for slot_number, gun in enumerate(PLAYER_GUNS):
        slot_x = HUD_X + slot_number * (SLOT_WIDTH + SLOT_GAP)
        slot_rect = pygame.Rect(slot_x, SLOT_Y, SLOT_WIDTH, SLOT_HEIGHT)
        is_active = (gun == player.gun_type)

        # Translucent background so the text stays readable over the scenery
        slot_surface = pygame.Surface((SLOT_WIDTH, SLOT_HEIGHT), pygame.SRCALPHA)
        slot_surface.fill((255, 255, 255, 70) if is_active else (0, 0, 0, 110))
        hud.blit(slot_surface, slot_rect)

        # Border (thick and coloured for the current weapon)
        border_colour = HUD_ACTIVE_COLOUR if is_active else HUD_INACTIVE_COLOUR
        pygame.draw.rect(hud, border_colour, slot_rect, 3 if is_active else 1)

        # Weapon icon centred in the slot (faded when it isn't the current weapon)
        icon = weapon_icons[gun] if is_active else faded_weapon_icons[gun]
        hud.blit(icon, icon.get_rect(center=slot_rect.center))

    # One bullet icon + a "x20" counter for the current weapon
    ammo_y = SLOT_Y + SLOT_HEIGHT + 8
    ammo_count = player.ammo[player.gun_type]
    counter_colour = LOW_AMMO_COLOUR if ammo_count <= LOW_AMMO else WHITE
    hud.blit(big_bullet, (HUD_X, ammo_y))
    label = f'x{ammo_count}'
    label_y = ammo_y + (big_bullet.get_height() - font.get_height()) // 2
    draw_text(label, font, counter_colour, HUD_X + big_bullet.get_width() + 8, label_y, hud)

    # One grenade icon per grenade, in the left column under the health bar
    draw_text('Grenades', small_font, WHITE, GRENADE_X, 38, hud)
    if player.grenades > 0:
        grenade_spacing = min(15, 150 / player.grenades)
        for i in range(player.grenades):
            hud.blit(grenade_image, (GRENADE_X + i * grenade_spacing, 52))


def draw_kill_counter():
    """Kills / required for each enemy type in the level. Turns green per type when done,
    shows EXIT OPEN when all are done, and flashes red after touching a locked exit."""
    ammo_y = SLOT_Y + SLOT_HEIGHT + 8
    text_y = ammo_y + (big_bullet.get_height() - small_font.get_height()) // 2
    if state.quota_met():
        draw_text('EXIT OPEN', small_font, (60, 220, 90), KILL_TEXT_X, text_y, hud)
        return
    flashing = (pygame.time.get_ticks() < state.exit_blocked_until
                and (pygame.time.get_ticks() // 200) % 2 == 0)
    x = KILL_TEXT_X
    for kind, need in state.kills_required.items():
        have = min(state.kills.get(kind, 0), need)
        if have >= need:
            colour = (60, 220, 90)
        else:
            colour = RED if flashing else WHITE
        label = f'{ENEMY_SHORT_NAMES.get(kind, kind[:3].upper())} {have}/{need}'
        draw_text(label, small_font, colour, x, text_y, hud)
        x += small_font.size(label)[0] + 14


def draw_status_bar():
    """Top-right status bars. One grey 'Normal' bar when nothing is active; otherwise
    one bar per active effect (name, seconds left, and a bar that drains over time)."""
    x, w, h = SCREEN_WIDTH - 210, 200, 24
    for index, (name, ms_left, ms_total) in enumerate(state.player.get_statuses()):
        y = 5 + index * (h + 4)   # up to 3 effects can be active at once
        colour = STATUS_COLOURS[name]

        pygame.draw.rect(hud, BLACK, (x - 2, y - 2, w + 4, h + 4))
        pygame.draw.rect(hud, (50, 50, 50), (x, y, w, h))
        if ms_total:
            pygame.draw.rect(hud, colour, (x, y, w * ms_left / ms_total, h))
            label = f'{name}  {(ms_left + 999) // 1000}s'   # round UP to whole seconds
        else:
            pygame.draw.rect(hud, colour, (x, y, w, h))
            label = name
        text = font.render(label, True, WHITE)
        hud.blit(text, (x + (w - text.get_width()) // 2, y + (h - text.get_height()) // 2))


class HealthBar():
    WIDTH = 150
    HEIGHT = 20

    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health
        self.trail = float(health)   # pale bar that drains slowly after a hit

    def draw(self, health):
        self.health = max(health, 0)

        # Trail: jumps up instantly when healing, drains slowly after damage
        if self.trail < self.health:
            self.trail = float(self.health)
        else:
            self.trail = max(self.health, self.trail - self.max_health * 0.004)

        ratio = self.health / self.max_health
        trail_ratio = self.trail / self.max_health

        # Bar colour by amount left
        if ratio > 0.6:
            colour, light = (60, 220, 90), (150, 255, 170)
        elif ratio > 0.3:
            colour, light = (240, 200, 40), (255, 235, 130)
        else:
            colour, light = (230, 50, 50), (255, 130, 130)

        # Border flashes red when health is critical
        flashing = ratio < 0.25 and (pygame.time.get_ticks() // 250) % 2 == 0
        border = RED if flashing else BLACK

        x, y, w, h = self.x, self.y, self.WIDTH, self.HEIGHT
        pygame.draw.rect(hud, border, (x - 2, y - 2, w + 4, h + 4))
        pygame.draw.rect(hud, (55, 20, 20), (x, y, w, h))                        # empty part
        pygame.draw.rect(hud, (255, 235, 200), (x, y, int(w * trail_ratio), h))  # damage trail
        pygame.draw.rect(hud, colour, (x, y, int(w * ratio), h))                 # current health
        if ratio > 0:
            pygame.draw.line(hud, light, (x, y), (x + int(w * ratio) - 1, y))    # top highlight

        # "75 / 100" centred, with a dark shadow so it reads on any colour
        label = f'{int(self.health)} / {self.max_health}'
        text_x = x + (w - small_font.size(label)[0]) // 2
        text_y = y + (h - small_font.get_height()) // 2
        draw_text(label, small_font, BLACK, text_x + 1, text_y + 1, hud)
        draw_text(label, small_font, WHITE, text_x, text_y, hud)


class ScreenFade():
    def __init__(self, direction, colour, speed):
        self.direction = direction   # 1 = intro (opening), 2 = death (closing down)
        self.colour = colour
        self.speed = speed           # pixels the fade grows each frame
        self.fade_counter = 0

    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1:  # Whole Screen Fade (intro)
            # Four rectangles (left, right, top, bottom) slide outwards from the centre,
            # revealing the level
            pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.colour, (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
            if self.fade_counter >= SCREEN_WIDTH // 2:
                fade_complete = True
        elif self.direction == 2:  # Vertical Screen Fade Down (death)
            # One rectangle growing down from the top until it covers the screen
            pygame.draw.rect(screen, self.colour, (0, 0, SCREEN_WIDTH, self.fade_counter))
            if self.fade_counter >= SCREEN_HEIGHT:
                fade_complete = True

        return fade_complete