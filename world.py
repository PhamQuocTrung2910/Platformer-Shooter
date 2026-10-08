import csv

import state  # noqa: F401  (World reads state.screen_scroll)
from settings import (screen, ROWS, COLUMNS, TILE_SIZE, PLAYER_GUNS, PLAYER_START_AMMO,
                      ENEMY_GUNS, ENEMY_START_AMMO)
from assets import image_list
import groups
from groups import (water_group, decoration_group, enemy_group, item_box_group,
                    exit_group)
from objects import ItemBox, Decoration, Exit, Water
from soldier import Soldier
from zombie import Zombie
from ui import HealthBar


class World():
    def __init__(self):
        self.obstacle_list = []
        self.level_length = 0

    def process_data(self, data):
        player = None
        health_bar = None
        self.level_length = len(data[0])
        # Iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    image = image_list[tile]
                    image_rect = image.get_rect()
                    image_rect.x = x * TILE_SIZE
                    image_rect.y = y * TILE_SIZE
                    tile_data = (image, image_rect)
                    if 0 <= tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif 9 <= tile <= 10:
                        water_group.add(Water(image, x * TILE_SIZE, y * TILE_SIZE))
                    elif 11 <= tile <= 14:
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
        return player, health_bar

    def draw(self):
        for tile in self.obstacle_list:
            tile[1].x += state.screen_scroll
            screen.blit(tile[0], tile[1])


def load_level(level_num):
    """Clear every group, read the level CSV, and build the world.
    Returns (world, player, health_bar)."""
    for group in groups.ALL_GROUPS:
        group.empty()

    # Create empty tile list
    data = [[-1] * COLUMNS for _ in range(ROWS)]
    # Load in the level data and create world
    with open(f'level{level_num}_data.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row_index, row in enumerate(reader):
            for column_index, tile in enumerate(row):
                data[row_index][column_index] = int(tile)

    new_world = World()
    new_player, new_health_bar = new_world.process_data(data)
    return new_world, new_player, new_health_bar