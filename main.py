import enum
import json
import pygame
import random
import sys

pygame.init()

# Constants
SCREEN_DIMENSIONS = (1200, 896)
SCREEN_BUFFER = 0.5
BACKGROUND_COLOR = (150, 150, 255)
SPRITE_SCALE = (100, 100) # Resize all sprites to 100x100
FPS = 60


def get_rect_dimensions(sprite_meta):
    return (sprite_meta['x'],
            sprite_meta['y'],
            sprite_meta['width'],
            sprite_meta['height'])

class SpriteSheet:
    ENEMIES = 'students'
    TILE_SET = 'tile_set'

    def __init__(self):
        with open(f'jsons/{self.ENEMIES}.json') as enemies_file:
            enemies = json.load(enemies_file)
        with open(f'jsons/{self.TILE_SET}.json') as tile_set_file:
            tile_set = json.load(tile_set_file)
        self.sprites_meta = {self.ENEMIES: enemies,
                             self.TILE_SET: tile_set}
        self.sprite_sheets = {
            self.ENEMIES: pygame.image.load(f'graphics/{self.ENEMIES}.png').convert_alpha(),
            self.TILE_SET: pygame.image.load(f'graphics/{self.TILE_SET}.png').convert_alpha(),
        }
        self.cached = {}

    def get_sprite(self, sprite_type, sprite_id, size=SPRITE_SCALE, flip=False):
        try:
            return self.cached[sprite_type][sprite_id]
        except KeyError:
            # Nothing in the cache ;(
            pass
        sheet = self.sprite_sheets[sprite_type]
        sprite_meta = self.sprites_meta[sprite_type][sprite_id]
        rect = pygame.Rect(get_rect_dimensions(sprite_meta))
        sprite = pygame.Surface((sprite_meta['width'], sprite_meta['height']))
        sprite.blit(sheet, (0, 0), rect)
        sprite = pygame.transform.scale(sprite, size)
        sprite.set_colorkey((0, 0, 0))
        if flip:
            sprite = pygame.transform.flip(sprite, True, False)
        self.cached[(sprite_type, sprite_id, flip)] = sprite
        return sprite


class PlayerState(enum.Enum):
    STATIC = 1
    WALKING = 2
    JUMPING = 3
    FALLING = 4


class Player:
    MOVE_SPEED = 8
    JUMP_FORCE = 20
    GRAVITY = 2
    MAX_GRAVITY = 16
    MAX_JUMP = 20
    SPRITES = {PlayerState.WALKING: ['small_mario_{}'.format(i) for i in (1, 2, 3)],
               PlayerState.FALLING: ['small_mario_4'],
               PlayerState.JUMPING: ['small_mario_5'],
               PlayerState.STATIC: ['small_mario_7']}
    SPRITE_SHEET = SpriteSheet.TILE_SET
    ANIMATION_DELAY = 5

    def __init__(self, x, y, screen, sprite_sheet, world):
        # General-use instance setup
        self.screen = screen
        self.sprite_sheet = sprite_sheet
        self.world = world
        # Setup the rectangle for the collision
        self.rect = pygame.Rect(0, 0, *SPRITE_SCALE)
        self.rect.x, self.rect.y = x, y
        # Setup the player state and sprite
        self.can_jump = True
        self.velocity_x = 0
        self.velocity_y = 0
        self.jump_hold = 0
        # Stupid dependency towards generating the first frame of the player
        self.animation_count = 9001
        self.animation_frame = 0
        self.update_sprite()

    def update_sprite(self):
        if self.velocity_y < 0:
            animation_state = PlayerState.JUMPING
        elif self.velocity_y > 0:
            animation_state = PlayerState.FALLING
        elif self.velocity_x != 0:
            animation_state = PlayerState.WALKING
        else:
            animation_state = PlayerState.STATIC
        flip = self.velocity_x < 0
        sprites = self.SPRITES[animation_state]

        if self.animation_count >= self.ANIMATION_DELAY:
            # Safeguard when switching states
            if self.animation_frame >= len(sprites):
                self.animation_frame = 0
            sprite_name = sprites[self.animation_frame]
            self.sprite = self.sprite_sheet.get_sprite(self.SPRITE_SHEET,
                                                       sprite_name,
                                                       flip=flip)
            self.animation_frame += 1
            self.animation_count = 0
        else:
            self.animation_count += 1
        self.screen.blit(self.sprite, self.rect)
        pygame.draw.rect(self.screen, (255, 255, 255), self.rect, 5)
    
    def parse_controls(self):
        # Reset sideways velocity in order not to check if a key is released
        self.velocity_x = 0
        key = pygame.key.get_pressed()
        if key[pygame.K_a]:
            self.velocity_x = -self.MOVE_SPEED
        if key[pygame.K_d]:
            self.velocity_x = self.MOVE_SPEED
        if key[pygame.K_SPACE] and self.can_jump:
            self.velocity_y = -(self.JUMP_FORCE + self.jump_hold // self.JUMP_FORCE)
            self.jump_hold -= 1
            # Bug here with multiple jumps, oh well

    def update_movement(self):
        # Handle vertical movement
        if self.velocity_y <= self.MAX_GRAVITY:
            self.velocity_y += self.GRAVITY
        if self.jump_hold == 0:
            self.can_jump = False
        for world_object in self.world.collideable:
            if world_object.rect.colliderect(self.rect.x, self.rect.y + self.velocity_y, *SPRITE_SCALE) and self.velocity_y > 0:
                # Fix velocity to the distance between the sprites
                self.velocity_y = world_object.rect.top - self.rect.bottom
                self.can_jump = True
                self.jump_hold = self.MAX_JUMP
        self.rect.y += self.velocity_y

        # Handle horizontal movement
        for world_object in self.world.collideable:
            if world_object.rect.colliderect(self.rect.x + self.velocity_x, self.rect.y, *SPRITE_SCALE):
                # Fix velocity to the distance between the sprites
                if self.velocity_x > 0:
                    self.velocity_x = world_object.rect.left - self.rect.right
                else:
                    self.velocity_x = world_object.rect.right - self.rect.left
        if self.rect.right  >= SCREEN_DIMENSIONS[0] * SCREEN_BUFFER and self.velocity_x > 0:
            self.world.scroll(self.velocity_x)
            # Apart from scrolling the world, we need to keep the player in the screen
            # so no movement of the player occurs in this case
        else:
            self.rect.x += self.velocity_x

    def update(self):
        self.parse_controls()
        self.update_movement()
        self.update_sprite()


class WorldObject:
    def __init__(self, object_meta):
        self.rect = pygame.Rect(get_rect_dimensions(object_meta))


class Enemy(WorldObject):
    SPRITE_SHEET = SpriteSheet.ENEMIES
    ANIMATION_DELAY = 5
    FALL_LIKE_A_TREE_IN_THE_FOREST = 10
    # But if there is no one around to hear it, does it make a sound?
    SPEED = 2
    # GIVE ME WHAT I NEED
    # WHITE LIGHTNING

    def __init__(self, object_meta, screen, sprite_sheet, world):
        super().__init__(object_meta)
        # General-use instance setup
        self.screen = screen
        self.sprite_sheet = sprite_sheet
        self.world = world
        enemy_number = random.randint(1, 20)
        sprite_names = [f'student_{enemy_number}_enemy_1_step_1',
                        f'student_{enemy_number}_enemy_1_step_2']
        self.sprites = [self.sprite_sheet.get_sprite(self.SPRITE_SHEET, sprite_name)
                        for sprite_name in sprite_names]
        self.animation_count = 9001
        self.animation_frame = 0
        
    def draw(self):
        if self.animation_count >= self.ANIMATION_DELAY:
            self.animation_frame = not self.animation_frame
            self.sprite = self.sprites[self.animation_frame]
            self.animation_count = 0
        else:
            self.animation_count += 1
        self.screen.blit(self.sprite, self.rect)

    def update_movement(self):
        dy = self.FALL_LIKE_A_TREE_IN_THE_FOREST
        dx = self.SPEED
        for world_object in self.world.objects:
            if world_object.rect.colliderect(self.rect.x, self.rect.y + dy, *SPRITE_SCALE) and dy > 0:
                # Fix velocity to the distance between the sprites
                dy = world_object.rect.top - self.rect.bottom
            if world_object.rect.colliderect(self.rect.x + dx, self.rect.y, *SPRITE_SCALE):
                # Fix velocity to the distance between the sprites
                dx = 0
        self.rect.y -= dy
        self.rect.x -= dx


class GameWorld:
    OBJECTS_TO_GENERATE = ['ground', 'pipe', 'stairs']
    def __init__(self, screen, sprite_sheet):
        self.screen = screen
        # Setup background
        self.background = pygame.image.load(f'graphics/level_1.png')
        self.background_coordinates = [0, 0] # For scrolling
        # Setup world
        self.offset = 0
        with open('jsons/level_1.json') as level_file:
            world_meta = json.load(level_file)
        self.objects = [WorldObject(object_meta)
                        for object_to_generate in self.OBJECTS_TO_GENERATE
                        for object_meta in world_meta[object_to_generate]]
        self.enemies = [Enemy(enemy_meta, screen, sprite_sheet, self)
                        for enemy_meta in world_meta['enemy_1']]
        # Put a wall like in Trouman's Show
        self.backwall = WorldObject({'x': -10,'y' :0, 'width': 10, 'height': 1000})
        self.collideable = self.objects + self.enemies + [self.backwall]
    
    def render_world(self):
        """Description of the function/method.

        Parameters:
            <param>: Description of the parameter

        Returns:
            <variable>: Description of the return value
        """
        self.screen.blit(self.background, self.background_coordinates)
        for enemy in self.enemies:
            enemy.update_movement()
            enemy.draw()
        for world_object in self.collideable:
            pygame.draw.rect(self.screen, (0, 0, 255), world_object.rect, 8)
    
    def scroll(self, offset):
        self.offset += offset
        for world_object in self.objects:
            world_object.rect.x -= offset
        for enemy in self.enemies:
            enemy.rect.x -= offset
        self.background_coordinates[0] = -self.offset
        


def main(screen):
    clock = pygame.time.Clock()
    sprite_sheet = SpriteSheet()
    world = GameWorld(screen, sprite_sheet)
    player = Player(200, 600, screen, sprite_sheet, world)
    while True:
        clock.tick(FPS)
        world.render_world()
        player.update()
        if any(event.type == pygame.QUIT
            for event in pygame.event.get()):
            break
        pygame.display.update()


if __name__ == '__main__':
    screen = pygame.display.set_mode(SCREEN_DIMENSIONS)
    pygame.display.set_caption('Super Jorgtor')
    main(screen)
    pygame.quit()
    sys.exit(0)
