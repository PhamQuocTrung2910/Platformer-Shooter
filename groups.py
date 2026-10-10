"""groups.py - the pygame sprite groups.

A Group is a container of sprites. Calling group.update() runs update() on every
sprite inside it, and group.draw(screen) draws them all, so main.py doesn't
have to loop over each bullet, grenade, etc. by hand.
"""
import pygame

enemy_group = pygame.sprite.Group()       # soldiers and zombies
bullet_group = pygame.sprite.Group()      # bullets from both player and enemies
grenade_group = pygame.sprite.Group()     # grenades in flight
explosion_group = pygame.sprite.Group()   # explosion animations
item_box_group = pygame.sprite.Group()    # pickups (placed in the level or dropped by enemies)
decoration_group = pygame.sprite.Group()  # scenery with no collision
water_group = pygame.sprite.Group()       # touching it kills the player
exit_group = pygame.sprite.Group()        # touching it completes the level

# Used by world.load_level() to empty everything when a level is (re)loaded
ALL_GROUPS = (enemy_group, bullet_group, grenade_group, explosion_group,
              item_box_group, decoration_group, water_group, exit_group)