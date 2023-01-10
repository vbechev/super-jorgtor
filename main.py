import pygame

pygame.init()

# Constants
SCREEN_SIZE = (1200, 800)
BACKGROUND_COLOR = (150, 150, 255)

# Setup screen
screen = pygame.display.set_mode(SCREEN_SIZE)
screen.fill(BACKGROUND_COLOR)
pygame.display.set_caption('Super Jorgtor')

jorgtor_img = pygame.image.load('graphics/jorgtor.png')
jorgtor_scaled = pygame.transform.scale(jorgtor_img, (100, 100))

while True:
    screen.blit(jorgtor_scaled, (0, 0))
    
    if any(event.type == pygame.QUIT for event in pygame.event.get()):
        break
    pygame.display.update()

pygame.quit()