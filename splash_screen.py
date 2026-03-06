import pygame
import sys
import time

def splash_screen(screen):
    # Colores y fuente
    YELLOW = (255, 255, 220)
    BLACK = (0, 0, 0)
    font = pygame.font.SysFont("segoeui", 40, bold=True)

    # Fondo
    screen.fill(YELLOW)

    # Texto
    text = font.render("Panal de Sentimientos", True, BLACK)
    # quiero colocar aquí una imagen
    rect = text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
    screen.blit(text, rect)

    logo = pygame.image.load("bee_meme.jpg")   # coloca aquí el nombre de tu archivo
    # Escalar la imagen si es muy grande
    logo = pygame.transform.smoothscale(logo, (150, 150))
    # Obtener rectángulo y centrarlo
    logo_rect = logo.get_rect(center=(screen.get_width()//2, screen.get_height()//2 - 100))
    screen.blit(logo, logo_rect)
    pygame.display.flip()

    # Esperar 3 segundos o hasta que se presione una tecla
    start_time = time.time()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False
        if time.time() - start_time > 3:  # 3 segundos
            waiting = False
