"""soldier.py - the Soldier enemy: patrols and shoots when it sees the player.
(The player lives in player.py.)"""
from settings import (TILE_SIZE, WEAPONS, ENEMY_BULLET_DAMAGE, ANIMATION_TYPES, DROP_CHANCES,
                      ENEMY_GUNS, ENEMY_START_AMMO, SOLDIER_SPEED, SOLDIER_HEALTH)
from character import ACTION_IDLE
from enemy import Enemy
from projectiles import spawn_bullets


class Soldier(Enemy):
    animation_folder = 'images/enemy/soldier'
    animation_names = ANIMATION_TYPES       # Idle, Run, Jump, Death
    death_action = 3
    enemy_type = 'soldier'
    drop_chances = DROP_CHANCES
    patrol_frames = TILE_SIZE

    def __init__(self, x, y, scale, speed=SOLDIER_SPEED):
        self.gun_type = ENEMY_GUNS[0]
        self.ammo = ENEMY_START_AMMO[self.gun_type]   # rounds left (enemies don't refill)
        self.shoot_cooldown = 0
        super().__init__(x, y, scale, speed, SOLDIER_HEALTH)

    def update(self):
        super().update()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown = max(0, self.shoot_cooldown - 1)

    def shoot(self):
        weapon = WEAPONS[self.gun_type]
        # Only fire if the gun has cooled down and there is ammo
        if self.shoot_cooldown <= 0 and self.ammo > 0:
            self.shoot_cooldown = weapon['cooldown']
            spawn_x = self.rect.centerx + 0.75 * self.rect.width * self.direction
            # Enemies always use the fixed enemy damage, not the weapon's
            spawn_bullets('enemy', weapon, spawn_x, self.rect.centery, self.direction,
                          ENEMY_BULLET_DAMAGE)
            self.ammo -= 1

    def think(self, player):
        """Shoot if the player is in the vision box, otherwise patrol."""
        self.roll_idle()
        if self.vision.colliderect(player.rect):
            self.update_action(ACTION_IDLE)   # stop running and shoot
            self.shoot()
        else:
            self.patrol_step()