import pygame
import sys

# Niveles: (nombre, avispas, descripción corta)
NIVELES = [
    ("Explorador Novato",      2,  "¡Para empezar la aventura!"),
    ("Pequeño Aventurero",     4,  "Un poco más difícil..."),
    ("Gran Explorador",        8,  "¡Ya eres valiente!"),
    ("Héroe Valiente",        12,  "¡Solo para los más fuertes!"),
    ("Maestro de la Aventura",16,  "¡El reto supremo!"),
]

BG_COLOR        = (255, 240, 100)
PANEL_COLOR     = (255, 255, 220)
BORDER_COLOR    = (200, 160,  20)
TITLE_COLOR     = (180,  90,   0)
BTN_COLORS      = [
    (144, 238, 144),  # verde claro
    (100, 200, 100),
    ( 60, 160,  60),
    ( 30, 120,  30),
    ( 10,  80,  10),
]
BTN_HOVER       = (255, 220,  80)
BTN_BORDER      = (180, 130,   0)
TEXT_COLOR      = (255, 255, 255)
TEXT_DARK       = ( 50,  50,  50)
WASP_COLOR      = (255, 140,   0)


def mostrar_menu(wasp_img=None):
    pygame.init()
    W, H = 750, 750
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Panal de Sentimientos")
    clock  = pygame.time.Clock()

    try:
        font_title  = pygame.font.SysFont("segoeui", 28, bold=True)
        font_sub    = pygame.font.SysFont("segoeui", 13)
        font_btn    = pygame.font.SysFont("segoeui", 17, bold=True)
        font_wasp   = pygame.font.SysFont("segoeui", 13)
    except Exception:
        font_title  = pygame.font.SysFont(None, 28)
        font_sub    = pygame.font.SysFont(None, 13)
        font_btn    = pygame.font.SysFont(None, 17)
        font_wasp   = pygame.font.SysFont(None, 13)

    BTN_W, BTN_H = 380, 68
    BTN_X = (W - BTN_W) // 2
    BTN_START_Y = 170
    BTN_GAP     = 76

    # Pre-escalar imagen de avispa para los botones
    wasp_thumb = None
    if wasp_img:
        wasp_thumb = pygame.transform.smoothscale(wasp_img, (28, 28))

    selected = None
    while selected is None:
        clock.tick(60)
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i in range(len(NIVELES)):
                    by = BTN_START_Y + i * BTN_GAP
                    rect = pygame.Rect(BTN_X, by, BTN_W, BTN_H)
                    if rect.collidepoint(mx, my):
                        selected = i

        # ── Fondo degradado tipo panal ──
        screen.fill(BG_COLOR)
        # Panel central
        panel = pygame.Rect(20, 10, W - 40, H - 20)
        pygame.draw.rect(screen, PANEL_COLOR, panel, border_radius=18)
        pygame.draw.rect(screen, BORDER_COLOR, panel, 3, border_radius=18)

        # Título
        t1 = font_title.render("¡Que comience la ventura!", True, TITLE_COLOR)
        screen.blit(t1, (W // 2 - t1.get_width() // 2, 28))
        t2 = font_sub.render("Elige tu nivel de dificultad:", True, (120, 80, 0))
        screen.blit(t2, (W // 2 - t2.get_width() // 2, 68))

        # Dibujar abeja decorativa pequeña si hay sprite
        if wasp_img:
            bee_big = pygame.transform.smoothscale(wasp_img, (54, 54))
            screen.blit(bee_big, (W // 2 - 27, 90))

        # Botones
        for i, (nombre, avispas, desc) in enumerate(NIVELES):
            by    = BTN_START_Y + i * BTN_GAP
            rect  = pygame.Rect(BTN_X, by, BTN_W, BTN_H)
            hover = rect.collidepoint(mx, my)

            color = BTN_HOVER if hover else BTN_COLORS[i]
            text_col = TEXT_DARK if hover else TEXT_COLOR

            pygame.draw.rect(screen, color, rect, border_radius=14)
            pygame.draw.rect(screen, BTN_BORDER, rect, 2, border_radius=14)

            # Nombre del nivel
            lbl = font_btn.render(nombre, True, text_col)
            screen.blit(lbl, (BTN_X + 14, by + 8))

            # Descripción
            desc_s = font_sub.render(desc, True, text_col)
            screen.blit(desc_s, (BTN_X + 14, by + 30))

            # Icono(s) de avispa
            wasp_x = BTN_X + BTN_W - 14
            for w in range(avispas):
                wx = wasp_x - (w + 1) * 32
                if wx < BTN_X + BTN_W // 2:
                    # demasiadas para mostrar todas, mostrar número
                    cnt = font_wasp.render(f"", True, text_col)
                    screen.blit(cnt, (BTN_X + BTN_W - cnt.get_width() - 10, by + BTN_H // 2 - 8))
                    break
                wy = by + (BTN_H - 28) // 2
                if wasp_thumb:
                    screen.blit(wasp_thumb, (wx, wy))
                else:
                    pygame.draw.circle(screen, WASP_COLOR, (wx + 14, wy + 14), 10)
            else:
                # Si el bucle terminó sin break, mostrar todos los iconos
                pass

        pygame.display.flip()

    return selected