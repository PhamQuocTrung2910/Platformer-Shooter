import pygame

enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

ALL_GROUPS = (enemy_group, bullet_group, grenade_group, explosion_group,
              item_box_group, decoration_group, water_group, exit_group)