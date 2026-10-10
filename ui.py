"""ui.py - everything drawn on top of / behind the game: text, background, HUD,
health bar and the screen fades."""
import pygame

import state
from settings import (screen, SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_GUNS,
                      BACKGROUND_COLOUR, RED, WHITE, GREEN, BLACK,
                      HUD_ACTIVE_COLOUR, HUD_INACTIVE_COLOUR,
                      HUD_X, HUD_WIDTH, SLOT_WIDTH, SLOT_HEIGHT, SLOT_GAP, SLOT_Y,
                      font, small_font)
from assets import (sky_image, mountain_image, pine1_image, pine2_image,
                    bullet_image, grenade_image, weapon_icons, faded_weapon_icons)


def draw_text(text, font, text_colour, x, y):
    # Turn the text into an image, then draw it at (x, y)
    image = font.render(text, True, text_colour)
    screen.blit(image, (x, y))


def draw_background():
    screen.fill(BACKGROUND_COLOUR)
    width = sky_image.get_width()
    scroll = state.background_scroll
    # Parallax: each layer moves by a different fraction of the scroll.
    # Layers that move slower look farther away. Each is repeated 5 times
    # side by side so there is always background to see.
    for i in range(5):
        screen.blit(sky_image, ((i * width) - scroll * 0.5, 0))
        screen.blit(mountain_image, ((i * width) - scroll * 0.6, SCREEN_HEIGHT - mountain_image.get_height() - 300))
        screen.blit(pine1_image, ((i * width) - scroll * 0.7, SCREEN_HEIGHT - pine1_image.get_height() - 150))
        screen.blit(pine2_image, ((i * width) - scroll * 0.8, SCREEN_HEIGHT - pine2_image.get_height()))


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
        screen.blit(slot_surface, slot_rect)

        # Border (thick and coloured for the current weapon)
        border_colour = HUD_ACTIVE_COLOUR if is_active else HUD_INACTIVE_COLOUR
        pygame.draw.rect(screen, border_colour, slot_rect, 3 if is_active else 1)

        # Weapon icon on the left (faded when it isn't the current weapon)
        icon = weapon_icons[gun] if is_active else faded_weapon_icons[gun]
        screen.blit(icon, (slot_x + 4, SLOT_Y + (SLOT_HEIGHT - icon.get_height()) // 2))

        # Key number (top right) and rounds left (bottom right), right-aligned
        text_colour = WHITE if is_active else HUD_INACTIVE_COLOUR
        for text, text_y in ((str(slot_number + 1), SLOT_Y + 3), (str(player.ammo[gun]), SLOT_Y + 19)):
            text_width = small_font.size(text)[0]
            draw_text(text, small_font, text_colour, slot_x + SLOT_WIDTH - 6 - text_width, text_y)

    # One bullet icon per round for the current weapon (squeezed together if there are lots)
    ammo_y = SLOT_Y + SLOT_HEIGHT + 8
    ammo_count = player.ammo[player.gun_type]
    if ammo_count > 0:
        # Spacing shrinks when there are many bullets so they never overflow the HUD width
        bullet_spacing = min(10, HUD_WIDTH / ammo_count)
        for i in range(ammo_count):
            screen.blit(bullet_image, (HUD_X + i * bullet_spacing, ammo_y))

    # One grenade icon per grenade
    grenade_y = ammo_y + bullet_image.get_height() + 8
    draw_text('Grenades: ', font, WHITE, HUD_X, grenade_y)
    if player.grenades > 0:
        grenade_spacing = min(15, (HUD_WIDTH - 110) / player.grenades)
        for i in range(player.grenades):
            screen.blit(grenade_image, (HUD_X + 110 + i * grenade_spacing, grenade_y + 5))

    # Stimulant countdown (+999 rounds the milliseconds UP to whole seconds)
    if player.stimulated:
        seconds_left = (player.stim_end_time - pygame.time.get_ticks() + 999) // 1000
        draw_text(f'Stimulated: {seconds_left}s', font, HUD_ACTIVE_COLOUR, HUD_X, grenade_y + 30)


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
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))


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