import enum
import json
import itertools
import pygame
import sys

pygame.init()

# Constants
SCREEN_DIMENSIONS = (1200, 800)
BACKGROUND_COLOR = (150, 150, 255)
SPRITE_SCALE = (100, 100) # Resize all sprites to 100x100
FPS = 60


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

    def get_sprite(self, sprite_type, sprite_id, position, size=SPRITE_SCALE, mirror=False):
        sheet = self.sprite_sheets[sprite_type]
        sprite_meta = self.sprites_meta[sprite_type][sprite_id]
        rect = pygame.Rect(sprite_meta['x'],
                           sprite_meta['y'],
                           sprite_meta['width'],
                           sprite_meta['height'])
        sprite = pygame.Surface((sprite_meta['width'], sprite_meta['height']))
        sprite.blit(sheet, (0, 0), rect)
        sprite = pygame.transform.scale(sprite, size)
        sprite.set_colorkey((0, 0, 0))
        return sprite


class PlayerState(enum.Enum):
    STATIC = 1
    WALKING = 2
    AIRBORN = 3


class Player:
    MOVE_SPEED = 5
    JUMP_FORCE = 5
    MAX_VELOCITY = -15
    MAX_GRAVITY = 10
    SPRITES = {PlayerState.WALKING: ['small_mario_{}'.format(i) for i in (1, 2, 3)],
               PlayerState.AIRBORN: ['small_mario_5'],
               PlayerState.STATIC: ['small_mario_7']}
    SPRITE_SHEET = SpriteSheet.TILE_SET
    ANIMATION_DELAY = 10

    def __init__(self, x, y, screen, sprite_sheet):
        # General-use instance setup
        self.screen = screen
        self.sprite_sheet = sprite_sheet
        # Setup the rectangle for the collision
        self.rect = pygame.Rect(0, 0, *SPRITE_SCALE)
        self.rect.x, self.rect.y = x, y
        # Setup the player state and sprite
        self.velocity_x = 0
        self.velocity_y = 0
        self.animation_count = 9001
        self.animation_frame = 0
        self.update_sprite()

    def update_sprite(self):
        if self.velocity_y != 10:
            state = PlayerState.AIRBORN
        elif self.velocity_x != 0:
            state = PlayerState.WALKING
        else:
            state = PlayerState.STATIC
        sprites = self.SPRITES[state]

        if state != PlayerState.WALKING:
            # Always render static states
            self.animation_count = 9001
        if self.animation_count >= self.ANIMATION_DELAY:
            # Safeguard when switching states
            if self.animation_frame >= len(sprites):
                self.animation_frame = 0
            sprite_name = sprites[self.animation_frame]
            self.sprite = self.sprite_sheet.get_sprite(self.SPRITE_SHEET,
                                                       sprite_name,
                                                       (self.rect.x, self.rect.y))
            self.animation_frame += 1
            self.animation_count = 0
        else:
            self.animation_count += 1

    def update(self):
        self.velocity_x = 0
        key = pygame.key.get_pressed()
        if key[pygame.K_a]:
            self.velocity_x = -self.MOVE_SPEED
        if key[pygame.K_d]:
            self.velocity_x = self.MOVE_SPEED
        if key[pygame.K_SPACE] and self.velocity_y > self.MAX_VELOCITY:
            self.velocity_y -= self.JUMP_FORCE
        
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        # Temp :)
        if self.rect.bottom > SCREEN_DIMENSIONS[1]:
            self.rect.bottom = SCREEN_DIMENSIONS[1]
        if self.velocity_y < self.MAX_GRAVITY:
            self.velocity_y += 1

        self.update_sprite()
        self.screen.blit(self.sprite, self.rect)


def main(screen):
    clock = pygame.time.Clock()
    sprite_sheet = SpriteSheet()
    player = Player(600, 600, screen, sprite_sheet)
    while True:
        clock.tick(FPS)
        screen.fill(BACKGROUND_COLOR)
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
