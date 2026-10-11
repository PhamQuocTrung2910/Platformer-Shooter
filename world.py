"""world.py - turns a level CSV file into actual game objects.

Each level is a grid of numbers (16 rows x 150 columns). Each number says what
sits in that cell: -1 = empty, 0-8 = solid ground, 15 = player spawn, and so on.
"""
import csv

import state  # World reads state.screen_scroll; load_level sets state.background_theme
from settings import (screen, ROWS, COLUMNS, TILE_SIZE, PLAYER_GUNS, PLAYER_START_AMMO,
                      ENEMY_GUNS, ENEMY_START_AMMO, LEVEL_THEMES, SCREEN_WIDTH, NEAR_TILE_MARGIN)
from assets import image_list
import groups
from groups import (water_group, decoration_group, enemy_group, item_box_group,
                    exit_group, pad_group)
from objects import (ItemBox, Decoration, Exit, Water,
                     ElectricTrap, SpeedPad, LauncherPad, MedPad)
from soldier import Soldier
from zombie import Zombie
from scientist import Scientist
from ui import HealthBar


class World():
    def __init__(self):
        self.obstacle_list = []   # (image, rect) for every solid tile; used for all collisions
        self.level_length = 0     # number of columns in the level
        self.near_tiles = []      # solid tiles on / near the screen, rebuilt every frame by draw()
        self.conveyor_list = []   # (rect, direction) for conveyor tiles; the rect is shared with obstacle_list

    def process_data(self, data):
        player = None
        health_bar = None
        self.level_length = len(data[0])
        # Iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:   # -1 means empty, so skip it
                    image = image_list[tile]
                    image_rect = image.get_rect()
                    # Convert grid position to pixel position
                    image_rect.x = x * TILE_SIZE
                    image_rect.y = y * TILE_SIZE
                    tile_data = (image, image_rect)
                    # The tile number decides what gets created:
                    if 0 <= tile <= 8 or 29 <= tile <= 37:        # solid ground/blocks
                        self.obstacle_list.append(tile_data)
                    elif 9 <= tile <= 10 or 38 <= tile <= 39:     # water (kills the player)
                        water_group.add(Water(image, x * TILE_SIZE, y * TILE_SIZE))
                    elif 11 <= tile <= 14 or 40 <= tile <= 43:    # scenery
                        decoration_group.add(Decoration(image, x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 15:  # Create Player
                        player = Soldier('player', PLAYER_GUNS, x * TILE_SIZE, y * TILE_SIZE,
                                         1.65, 5, PLAYER_START_AMMO, 10)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16:  # Create Enemies
                        enemy = Soldier('enemy', ENEMY_GUNS, x * TILE_SIZE, y * TILE_SIZE,
                                        1.65, 2, ENEMY_START_AMMO, 0)
                        enemy_group.add(enemy)
                    elif tile == 17:  # Create Ammo Box
                        item_box_group.add(ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 18:  # Create Grenade Box
                        item_box_group.add(ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 19:  # Create Health Box
                        item_box_group.add(ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 20:  # Create Exit
                        exit_group.add(Exit(image, x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 21:  # Create Zombie
                        enemy_group.add(Zombie(x * TILE_SIZE, y * TILE_SIZE, 1.65))
                    elif tile == 22:  # Create Scientist
                        enemy_group.add(Scientist(x * TILE_SIZE, y * TILE_SIZE, 1.65))
                    elif tile == 23:  # Electric trap
                        pad_group.add(ElectricTrap(image, x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 24:  # Speed pad
                        pad_group.add(SpeedPad(image, x * TILE_SIZE, y * TILE_SIZE))
                    elif tile == 25:  # Launcher pad
                        pad_group.add(LauncherPad(image, x * TILE_SIZE, y * TILE_SIZE))
                    elif tile in (26, 27):  # Conveyor belt (solid, and carries whoever stands on it)
                        self.obstacle_list.append(tile_data)
                        self.conveyor_list.append((image_rect, 1 if tile == 26 else -1))
                    elif tile == 28:  # Med pad
                        pad_group.add(MedPad(image, x * TILE_SIZE, y * TILE_SIZE))
        self.near_tiles = self.obstacle_list   # until the first draw() builds the short list
        return player, health_bar

    def draw(self):
        scroll = state.screen_scroll
        near = []
        for tile in self.obstacle_list:
            rect = tile[1]
            # Every tile still scrolls with the world...
            rect.x += scroll
            # ...but only the ones on or near the screen are kept for collisions,
            # and only the visible ones are drawn
            if rect.right > -NEAR_TILE_MARGIN and rect.left < SCREEN_WIDTH + NEAR_TILE_MARGIN:
                near.append(tile)
                if rect.right > 0 and rect.left < SCREEN_WIDTH:
                    screen.blit(tile[0], rect)
        self.near_tiles = near


def load_level(level_num):
    """Clear every group, read the level CSV, and build the world.
    Returns (world, player, health_bar)."""
    # Pick this level's background set (read by ui.draw_background)
    state.background_theme = LEVEL_THEMES.get(level_num, 'forest')

    # Remove everything left over from the previous level
    for group in groups.ALL_GROUPS:
        group.empty()

    # Create empty tile list (-1 everywhere = nothing)
    data = [[-1] * COLUMNS for _ in range(ROWS)]
    # Load in the level data and create world
    with open(f'levels/level{level_num}_data.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row_index, row in enumerate(reader):
            for column_index, tile in enumerate(row):
                data[row_index][column_index] = int(tile)

    new_world = World()
    new_player, new_health_bar = new_world.process_data(data)
    if new_player is None:
        raise ValueError(f'levels/level{level_num}_data.csv has no player spawn. '
                         'Place the green soldier tile (15) somewhere in the level and save it.')
    return new_world, new_player, new_health_bar