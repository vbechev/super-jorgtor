import enum
import json
import pygame
import sys

pygame.init()

# Constants
SCREEN_DIMENSIONS = (1200, 896)
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
    JUMP_FORCE = 10
    GRAVITY = 1
    MAX_GRAVITY = 16
    MAX_JUMP = 30
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
            # Bug here with multiple jupms, oh well

    def update_movement(self):
        if self.velocity_y <= self.MAX_GRAVITY:
            self.velocity_y += self.GRAVITY
        if self.jump_hold == 0:
            self.can_jump = False
        for ground in self.world.ground:
            if ground.colliderect(self.rect.x, self.rect.y + self.velocity_y, *SPRITE_SCALE) and self.velocity_y > 0:
                # Fix velocity to the distance between the sprites
                self.velocity_y = ground.top - self.rect.bottom
                self.can_jump = True
                self.jump_hold = self.MAX_JUMP
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y

    def update(self):
        self.parse_controls()
        self.update_movement()
        self.update_sprite()


class Tile:
    pass


class GameWorld:
    def __init__(self, screen):
        self.screen = screen
        # Setup background
        self.background = pygame.image.load(f'graphics/level_1.png')
        # Setup world
        with open('jsons/level_1.json') as level_file:
            world_meta = json.load(level_file)
        self.ground = [pygame.Rect(get_rect_dimensions(ground)) for ground in world_meta['ground']]
    
    def render_world(self):
        self.screen.blit(self.background, (0, 0))
        for ground_rect in self.ground:
            pygame.draw.rect(self.screen, (0, 0, 255), ground_rect, 8)


def main(screen):
    clock = pygame.time.Clock()
    sprite_sheet = SpriteSheet()
    world = GameWorld(screen)
    player = Player(600, 600, screen, sprite_sheet, world)
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
