"""main.py - the game loop. Run this file to play.

Each frame it decides which screen to show (menu / win screen / gameplay),
updates and draws everything, then reads keyboard events.
"""
import pygame
from sys import exit

import button
import state
from settings import (screen, clock, FPS, SCREEN_WIDTH, SCREEN_HEIGHT, MAX_LEVELS,
                      BACKGROUND_COLOUR, BLACK, PINK, big_font)
from assets import (start_image, exit_image, restart_image, jump_sound, start_music)
from groups import (bullet_group, grenade_group, explosion_group, item_box_group,
                    decoration_group, water_group, exit_group, enemy_group)
from projectiles import Grenade
from ui import draw_text, draw_background, draw_weapon_hud, ScreenFade
from world import load_level

# ---------------------------------------------------------------------------
# Game flow variables
# ---------------------------------------------------------------------------
level = 1
start_game = False    # False while the main menu is showing
start_intro = False   # True while the opening screen fade is playing
game_won = False      # True after finishing the last level

# Player action variables (set by key presses, cleared by key releases)
moving_left = False
moving_right = False
shooting = False
throwing_grenade = False
grenade_thrown = False   # stops one Q press throwing a grenade every frame

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
start_music()

# ScreenFade(direction, colour, speed): 1 = intro (opens up), 2 = death (closes down)
intro_fade = ScreenFade(1, BLACK, 3)
death_fade = ScreenFade(2, PINK, 4)

# Menu buttons (x, y, image, scale)
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_image, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_image, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_image, 2)

# Build level 1: returns the world, the player and the player's health bar
state.world, state.player, state.health_bar = load_level(level)

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
while True:
    clock.tick(FPS)   # cap the game at 60 frames per second

    if not start_game:
        # Draw Menu
        screen.fill(BACKGROUND_COLOUR)
        # Add button (draw() returns True on the frame it is clicked)
        if start_button.draw(screen):
            start_game = True
            start_intro = True
        if exit_button.draw(screen):
            pygame.quit()
            exit()

    elif game_won:
        # End screen
        draw_background()
        draw_text('YOU WIN!', big_font, BLACK, SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150)
        if restart_button.draw(screen):
            # Reset everything back to level 1
            game_won = False
            level = 1
            state.background_scroll = 0
            state.screen_scroll = 0
            start_intro = True
            intro_fade.fade_counter = 0
            state.world, state.player, state.health_bar = load_level(level)

    else:
        # ----- Gameplay -----
        # Update Background
        draw_background()
        # Draw world map
        state.world.draw()

        # Show player health, weapons, ammo and grenades
        state.health_bar.draw(state.player.health)
        draw_weapon_hud()

        state.player.update()
        state.player.draw()

        # Each enemy: think (ai), update timers/animation, then draw
        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()

        # Update and Draw Groups
        bullet_group.update()
        grenade_group.update()
        explosion_group.update()
        item_box_group.update()
        decoration_group.update()
        water_group.update()
        exit_group.update()

        bullet_group.draw(screen)
        grenade_group.draw(screen)
        explosion_group.draw(screen)
        item_box_group.draw(screen)
        decoration_group.draw(screen)
        water_group.draw(screen)
        exit_group.draw(screen)

        # Show Intro
        if start_intro:
            if intro_fade.fade():
                start_intro = False
                intro_fade.fade_counter = 0

        # Update Player Actions
        if state.player.alive:
            # Shooting and grenades
            if shooting:
                state.player.shoot()
            # Throw Grenade
            if throwing_grenade and not grenade_thrown and state.player.grenades > 0:
                new_grenade = Grenade(
                    state.player.rect.centerx + (0.5 * state.player.rect.size[0] * state.player.direction),
                    state.player.rect.top, state.player.direction)
                grenade_group.add(new_grenade)
                # Reduce Grenade
                state.player.grenades -= 1
                grenade_thrown = True

            # Animation state (independent of shooting / grenades)
            if state.player.in_air:
                state.player.update_action(2)  # 2 = Jump
            elif moving_left or moving_right:
                state.player.update_action(1)  # 1 = Run
            else:
                state.player.update_action(0)  # 0 = Idle

            # move() returns how far the world should scroll this frame
            state.screen_scroll, level_complete = state.player.move(moving_left, moving_right)
            state.background_scroll -= state.screen_scroll

            # Check if player has completed the level
            if level_complete:
                level += 1
                state.background_scroll = 0
                state.screen_scroll = 0
                if level > MAX_LEVELS:
                    game_won = True
                else:
                    start_intro = True
                    intro_fade.fade_counter = 0
                    # Load in the level data and create world
                    state.world, state.player, state.health_bar = load_level(level)
        else:  # If player is dead
            state.screen_scroll = 0
            # Red fade comes down the screen, then the Restart button appears
            if death_fade.fade():
                if restart_button.draw(screen):
                    death_fade.fade_counter = 0
                    start_intro = True
                    state.background_scroll = 0
                    # Load in the level data and create world
                    state.world, state.player, state.health_bar = load_level(level)

    # ----- Keyboard / window events -----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # User clicking X button in window
            pygame.quit()
            exit()

        # Key pressed down: turn the matching action on
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                moving_right = True
            if (event.key == pygame.K_UP or event.key == pygame.K_w) and state.player.alive:
                state.player.jump = True
                jump_sound.play()
            if event.key == pygame.K_SPACE:
                shooting = True
            if event.key == pygame.K_q:
                throwing_grenade = True
            # Weapon selection
            if state.player.alive:
                if event.key == pygame.K_1:
                    state.player.switch_weapon('pistol')
                if event.key == pygame.K_2:
                    state.player.switch_weapon('rifle')
                if event.key == pygame.K_3:
                    state.player.switch_weapon('shotgun')
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                exit()

        # Key released: turn the matching action off
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_SPACE:
                shooting = False
            if event.key == pygame.K_q:
                throwing_grenade = False
                grenade_thrown = False   # allow the next Q press to throw again

    # Show everything we drew this frame
    pygame.display.update()