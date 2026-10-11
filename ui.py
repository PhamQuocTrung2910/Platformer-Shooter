"""ui.py - everything drawn on top of / behind the game: text, background, HUD,
health bar and the screen fades."""
import pygame

import state
from settings import (screen, hud, SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_GUNS,
                      BACKGROUND_COLOURS, RED, WHITE, GREEN, BLACK,
                      HUD_ACTIVE_COLOUR, HUD_INACTIVE_COLOUR,
                      HUD_BG_COLOUR, HUD_LINE_COLOUR, GRENADE_X, HUD_HEIGHT,
                      HUD_X, HUD_WIDTH, SLOT_WIDTH, SLOT_HEIGHT, SLOT_GAP, SLOT_Y,
                      font, small_font)
from assets import (BACKGROUNDS, bullet_image, grenade_image,
                    weapon_icons, faded_weapon_icons)

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

        # Weapon icon on the left (faded when it isn't the current weapon)
        icon = weapon_icons[gun] if is_active else faded_weapon_icons[gun]
        hud.blit(icon, (slot_x + 4, SLOT_Y + (SLOT_HEIGHT - icon.get_height()) // 2))

        # Key number (top right) and rounds left (bottom right), right-aligned
        text_colour = WHITE if is_active else HUD_INACTIVE_COLOUR
        for text, text_y in ((str(slot_number + 1), SLOT_Y + 3), (str(player.ammo[gun]), SLOT_Y + 19)):
            text_width = small_font.size(text)[0]
            draw_text(text, small_font, text_colour, slot_x + SLOT_WIDTH - 6 - text_width, text_y, hud)

    # One bullet icon per round for the current weapon (squeezed together if there are lots)
    ammo_y = SLOT_Y + SLOT_HEIGHT + 8
    ammo_count = player.ammo[player.gun_type]
    if ammo_count > 0:
        # Spacing shrinks when there are many bullets so they never overflow the HUD width
        bullet_spacing = min(10, HUD_WIDTH / ammo_count)
        for i in range(ammo_count):
            hud.blit(bullet_image, (HUD_X + i * bullet_spacing, ammo_y))

    # One grenade icon per grenade, in the left column under the health bar
    draw_text('Grenades', small_font, WHITE, GRENADE_X, 36, hud)
    if player.grenades > 0:
        grenade_spacing = min(15, 150 / player.grenades)
        for i in range(player.grenades):
            hud.blit(grenade_image, (GRENADE_X + i * grenade_spacing, 58))


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
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        # Update with new health
        self.health = health
        # Calculate health ratio
        ratio = self.health / self.max_health
        # Black border, then a full red bar, then a green bar covering the remaining health
        pygame.draw.rect(hud, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(hud, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(hud, GREEN, (self.x, self.y, 150 * ratio, 20))


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