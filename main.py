import sys
import pygame

pygame.init()

# Constants
FPS = 60
SCREEN_SIZE = (1200, 800)
BACKGROUND_COLOR = (150, 150, 255)

# Setup screen


class Player:
    MAX_VELOCITY = -10
    MAX_GRAVITY = 20

    def __init__(self, x, y, screen):
        raw_image = pygame.image.load('graphics/jorgtor.png')
        self.image = pygame.transform.scale(raw_image, (100, 100))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.velocity_y = 0
        self.screen = screen
    
    def update(self):
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            self.rect.x -= 5
        if key[pygame.K_RIGHT]:
            self.rect.x += 5
        if key[pygame.K_SPACE] and self.velocity_y > self.MAX_VELOCITY:
            self.velocity_y -= 10
            
        self.rect.y += self.velocity_y
        if self.velocity_y < self.MAX_GRAVITY:
            self.velocity_y += 1
            
        self.screen.blit(self.image, self.rect)


def main(screen):
    clock = pygame.time.Clock()
    player = Player(300, 600, screen)
    while True:
        clock.tick(FPS)
        screen.fill(BACKGROUND_COLOR)
        player.update()
        if any(event.type == pygame.QUIT for event in pygame.event.get()):
            break
        pygame.display.update()


if __name__ == '__main__':
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption('Super Jorgtor')
    main(screen)
    pygame.quit()
    sys.exit(0)
