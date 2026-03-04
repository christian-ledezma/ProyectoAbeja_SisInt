import pygame
import math
import sys
import os
from menu_dificultad import mostrar_menu, NIVELES
from niveles_config import configurar_nivel

# ──────────────────────────────────────────────
#  ASEGURAR QUE LOS MÓDULOS DEL REPO SEAN VISIBLES
# ──────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from EntornoHex import EntornoHex

# ==============================
# CONFIGURACIÓN
# ==============================
WIDTH, HEIGHT = 750, 750
HEX_SIZE = 25
RADIUS = 7

SPRITES = {"player": "abeja2.png", "wasp": "avispa.png"}

BACKGROUND_COLOR  = (122, 155, 181)
HEX_COLOR         = (255, 217, 61)
HEX_HOVER_COLOR   = (255, 240, 160)
NEI_HOVER_COLOR   = (205, 240, 160)
BORDER_COLOR      = (200, 230, 201)
WALL_COLOR        = (102, 187, 106)
WALL_BORDER_COLOR = (56, 142, 60)
ITEM_COLOR        = (255, 255, 255)
HUD_TEXT          = (56, 142, 60)
HUD_DIM           = (100, 160, 80)
PATH_COLOR        = (180, 100, 255)    # Morado: celdas del camino
PATH_BORDER       = (120,  50, 200)
POLLEN_COLOR      = (255, 220,  50)    # Amarillo dorado: celda meta
POLLEN_BORDER     = (200, 150,   0)


# ==============================
# CARGA DE SPRITES
# ==============================
def load_sprites(sprite_dict, hex_size):
    loaded = {}
    sprite_size = int(hex_size * 1.55)
    for key, filename in sprite_dict.items():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)
        if os.path.exists(filepath):
            try:
                img = pygame.image.load(filepath).convert_alpha()
                img = pygame.transform.smoothscale(img, (sprite_size, sprite_size))
                loaded[key] = img
            except pygame.error as e:
                print(f"Error cargando '{filename}': {e}")
                loaded[key] = None
        else:
            loaded[key] = None
    return loaded


def draw_sprite(surface, sprite, center):
    rect = sprite.get_rect(center=(int(center[0]), int(center[1])))
    surface.blit(sprite, rect)


# ==============================
# COORDENADAS HEXAGONALES
# ==============================
def axial_to_pixel(q, r, size, offset_x, offset_y):
    x = size * math.sqrt(3) * (q + r / 2)
    y = size * 3 / 2 * r
    return x + offset_x, y + offset_y


def pixel_to_axial(px, py, size, offset_x, offset_y):
    px -= offset_x
    py -= offset_y
    q = (px * math.sqrt(3) / 3 - py / 3) / size
    r = py * 2 / 3 / size
    return axial_round(q, r)


def axial_round(q, r):
    s = -q - r
    rq, rr, rs = round(q), round(r), round(s)
    dq, dr, ds = abs(rq - q), abs(rr - r), abs(rs - s)
    if dq > dr and dq > ds:
        rq = -rr - rs
    elif dr > ds:
        rr = -rq - rs
    return (rq, rr)


def hex_neighbors(q, r):
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
    return [(q + dq, r + dr) for dq, dr in directions]


def hex_corner(center, size, i):
    angle_deg = 60 * i - 30
    angle_rad = math.radians(angle_deg)
    return (center[0] + size * math.cos(angle_rad),
            center[1] + size * math.sin(angle_rad))


def generate_hex_grid(radius):
    hexes = set()
    for q in range(-radius, radius + 1):
        for r in range(max(-radius, -q - radius), min(radius, -q + radius) + 1):
            hexes.add((q, r))
    return hexes


# ==============================
# DIBUJO
# ==============================
def draw_hex(surface, color, center, size, border_color=BORDER_COLOR, border_width=2):
    corners = [hex_corner(center, size, i) for i in range(6)]
    pygame.draw.polygon(surface, color, corners)
    if border_width > 0:
        pygame.draw.polygon(surface, border_color, corners, border_width)


def draw_pollen_dot(surface, center, size):
    cx, cy = int(center[0]), int(center[1])
    r = max(3, int(size * 0.18))
    pygame.draw.circle(surface, ITEM_COLOR, (cx, cy), r)
    pygame.draw.circle(surface, (255, 240, 120), (cx, cy), r, 1)


def draw_hud(surface, font_title, font_body,
             edit_mode, player_pos, pollen_pos,
             tecnica, heuristica, camino_len):

    hud_surf = pygame.Surface((340, 90), pygame.SRCALPHA)
    hud_surf.fill((255, 250, 255, 220))
    pygame.draw.rect(hud_surf, (200, 230, 201, 255), (0, 0, 370, 175), 3)
    surface.blit(hud_surf, (10, 10))

    title = font_title.render("Panal de Sentimientos", True, HUD_TEXT)
    surface.blit(title, (20, 16))

    pollen_str = str(pollen_pos) if pollen_pos else "sin colocar"
    surface.blit(font_body.render(f"Jugador: {player_pos}   Objetivo: {pollen_str}", True, HUD_DIM), (20, 40))

    tec_color = (100, 180, 255)
    surface.blit(font_body.render(f"Técnica: {tecnica} ", True, tec_color), (20, 58))
    surface.blit(font_body.render(f"Heurística: {heuristica}", True, tec_color), (180, 58))

    path_str = f"Camino: {camino_len} pasos" if camino_len > 0 else "Camino: —"
    surface.blit(font_body.render(path_str, True, PATH_COLOR), (20, 76))

# ==============================
# ESTADO DEL JUEGO
# ==============================
class GameState:
    def __init__(self, radius):
        self.grid = generate_hex_grid(radius)
        self.cell_type = {cell: "floor" for cell in self.grid}
        self.player = (0, 0)
        self.pollen = None

    def move_player(self, target):
        if (target in self.grid
                and self.cell_type[target] == "floor"
                and target in hex_neighbors(*self.player)):
            self.player = target
            return True
        return False

    def toggle_wall(self, cell):
        if cell in self.cell_type and cell != self.player and cell != self.pollen:
            if self.cell_type[cell] == "floor":
                self.cell_type[cell] = "wall"
            else:
                self.cell_type[cell] = "floor"

    def set_pollen(self, cell):
        """Coloca el polen en una celda de piso (quita el anterior si lo había)."""
        if cell in self.grid and self.cell_type[cell] == "floor" and cell != self.player:
            self.pollen = cell


# ==============================
# MAIN
# ==============================
TECNICAS    = ["costouniforme", "codicioso", "a_estrella"]
HEURISTICAS = ["hexagonal", "euclidiana"]

def _mostrar_game_over(screen, font_title, font_body):
    W, H = screen.get_size()
    clock = pygame.time.Clock()

    btn_retry = pygame.Rect(W//2 - 160, H//2 + 50,  145, 44)
    btn_exit  = pygame.Rect(W//2 + 15,  H//2 + 50,  145, 44)

    while True:
        clock.tick(60)
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_retry.collidepoint(mx, my):
                    return True
                if btn_exit.collidepoint(mx, my):
                    return False

        # Overlay oscuro
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        # Mensajes
        msg1 = font_title.render("¡Una avispa te picó!", True, (255, 80, 80))
        msg2 = font_body.render("¿Qué quieres hacer?", True, (255, 220, 80))
        screen.blit(msg1, (W//2 - msg1.get_width()//2, H//2 - 60))
        screen.blit(msg2, (W//2 - msg2.get_width()//2, H//2 - 20))

        # Botón reintentar
        hover_retry = btn_retry.collidepoint(mx, my)
        pygame.draw.rect(screen, (80, 200, 80) if hover_retry else (50, 160, 50),
                         btn_retry, border_radius=10)
        pygame.draw.rect(screen, (200, 255, 200), btn_retry, 2, border_radius=10)
        lbl_r = font_body.render("¡Otra vez!", True, (255, 255, 255))
        screen.blit(lbl_r, (btn_retry.centerx - lbl_r.get_width()//2,
                             btn_retry.centery - lbl_r.get_height()//2))

        # Botón salir
        hover_exit = btn_exit.collidepoint(mx, my)
        pygame.draw.rect(screen, (200, 60, 60) if hover_exit else (160, 40, 40),
                         btn_exit, border_radius=10)
        pygame.draw.rect(screen, (255, 200, 200), btn_exit, 2, border_radius=10)
        lbl_e = font_body.render("Salir", True, (255, 255, 255))
        screen.blit(lbl_e, (btn_exit.centerx - lbl_e.get_width()//2,
                             btn_exit.centery - lbl_e.get_height()//2))

        pygame.display.flip()

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Laberinto Hexagonal – Agente IA")
    clock = pygame.time.Clock()

    try:
        font_title = pygame.font.SysFont("segoeui", 18, bold=True)
        font_body  = pygame.font.SysFont("segoeui", 14)
    except Exception:
        font_title = pygame.font.SysFont(None, 18)
        font_body  = pygame.font.SysFont(None, 14)

    offset_x = WIDTH  // 2
    offset_y = HEIGHT // 2 + 30

    sprites   = load_sprites(SPRITES, HEX_SIZE)

    nivel_idx    = mostrar_menu(wasp_img=sprites.get("wasp"))
    nombre_nivel = NIVELES[nivel_idx][0]

    def iniciar_nivel():
        st = GameState(RADIUS)
        ent = EntornoHex(st)
        ws = configurar_nivel(st, nivel_idx)
        ent.wasps = ws
        print(f"Nivel: {nombre_nivel} ({len(ws)} avispas)")
        return st, ent, ws

    state, entorno, wasps = iniciar_nivel()

    hovered_cell  = None
    edit_mode     = False
    tec_idx       = 2          # a_estrella por defecto
    heu_idx       = 0          # hexagonal por defecto
    path_cells    = set()      # celdas del camino actual (sin inicio ni meta)
    camino_len    = 0
    move_count    = 0

    print("Controles:")
    print("  E        → alternar modo juego / edición")
    print("  T        → cambiar técnica de búsqueda")
    print("  H        → cambiar heurística")
    print("  SPACE    → lanzar búsqueda")
    print("  Clic izq (juego)   → mover abeja")
    print("  Clic izq (edición) → alternar pared")
    print("  Clic der (edición) → colocar/mover polen")
    print("  ESC      → salir")

    running = True
    while running:
        clock.tick(60)
        mouse_pos    = pygame.mouse.get_pos()
        hovered_cell = pixel_to_axial(*mouse_pos, HEX_SIZE, offset_x, offset_y)
        if hovered_cell not in state.grid:
            hovered_cell = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_e:
                    edit_mode = not edit_mode
                    print(f"Modo: {'Edición' if edit_mode else 'Juego'}")

                elif event.key == pygame.K_t:
                    tec_idx = (tec_idx + 1) % len(TECNICAS)
                    entorno.tecnica = TECNICAS[tec_idx]
                    path_cells = set()
                    camino_len = 0
                    print(f"Técnica: {entorno.tecnica}")

                elif event.key == pygame.K_h:
                    heu_idx = (heu_idx + 1) % len(HEURISTICAS)
                    entorno.heuristica = HEURISTICAS[heu_idx]
                    path_cells = set()
                    camino_len = 0
                    print(f"Heurística: {entorno.heuristica}")

                elif event.key == pygame.K_SPACE:
                    if state.pollen is not None:
                        print(f"\nBuscando: {state.player} → {state.pollen} "
                              f"[{entorno.tecnica} / {entorno.heuristica}]")
                        entorno.wasps = wasps
                        entorno.buscar()
                        camino = entorno.ultimo_camino
                        # Celdas intermedias del camino (sin inicio ni meta)
                        path_cells = set(camino[1:-1]) if len(camino) > 2 else set()
                        camino_len = len(camino) - 1 if camino else 0
                        if not camino:
                            print("No se encontró camino.")
                    else:
                        print("Primero coloca el polen (clic derecho en modo edición).")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if hovered_cell:
                    if event.button == 1:          # izquierdo
                        if edit_mode:
                            state.toggle_wall(hovered_cell)
                            path_cells = set()
                            camino_len = 0
                        else:
                            if state.move_player(hovered_cell):
                                move_count += 1 
                                path_cells = set()
                                camino_len = 0
                                # Comprobar colisión con avispa
                                if state.player in wasps:
                                    print("Te picó una avispa! Fin del juego.")
                                    reintentar = _mostrar_game_over(screen, font_title, font_body)
                                    _mostrar_game_over(screen, font_title, font_body)
                                    if reintentar:
                                        state, entorno, wasps = iniciar_nivel()
                                        path_cells = set()
                                        camino_len = 0
                                        move_count = 0
                                    else:
                                        running = False
                    elif event.button == 3:        # derecho
                        if edit_mode:
                            state.set_pollen(hovered_cell)
                            path_cells = set()
                            camino_len = 0
                            print(f"Polen colocado en {hovered_cell}")

        # ──────────────────────────────
        #  RENDERIZADO
        # ──────────────────────────────
        screen.fill(BACKGROUND_COLOR)
        neighbors_of_player = set(hex_neighbors(*state.player))

        # ── 1. Calcular color de cada celda ──
        cell_data = {}
        for cell in state.grid:
            q, r   = cell
            cx, cy = axial_to_pixel(q, r, HEX_SIZE, offset_x, offset_y)
            is_wall     = state.cell_type[cell] == "wall"
            is_hover    = cell == hovered_cell
            is_neighbor = (cell in neighbors_of_player
                           and not is_wall
                           and cell in state.grid)
            is_path     = cell in path_cells
            is_pollen   = cell == state.pollen

            if is_wall:
                color = WALL_COLOR
                bcol, bw = WALL_BORDER_COLOR, 2

            elif is_pollen:
                color = POLLEN_COLOR
                bcol, bw = POLLEN_BORDER, 3

            elif is_path:
                color = PATH_COLOR
                bcol, bw = PATH_BORDER, 2

            elif is_neighbor and not edit_mode:
                color = NEI_HOVER_COLOR if is_hover else HEX_COLOR
                bcol, bw = BORDER_COLOR, 2

            elif is_hover:
                color = HEX_HOVER_COLOR
                bcol, bw = BORDER_COLOR, 2

            else:
                dist = max(abs(q), abs(r), abs(-q - r))
                fade = min(dist * 6, 40)
                color = (max(HEX_COLOR[0] - fade, 0),
                         max(HEX_COLOR[1] - fade, 0),
                         max(HEX_COLOR[2] - fade // 2, 0))
                bcol, bw = BORDER_COLOR, 2

            cell_data[cell] = (cx, cy, color, bcol, bw)

        # ── 2. Dibujar relleno ──
        for cell, (cx, cy, color, bcol, bw) in cell_data.items():
            draw_hex(screen, color, (cx, cy), HEX_SIZE, bcol, 0)

        # ── 3. Dibujar bordes ──
        for cell, (cx, cy, color, bcol, bw) in cell_data.items():
            corners = [hex_corner((cx, cy), HEX_SIZE, i) for i in range(6)]
            pygame.draw.polygon(screen, bcol, corners, bw)

        # ── 4. Dibujar punto de polen encima ──
        if state.pollen and state.pollen in cell_data:
            cx, cy = cell_data[state.pollen][:2]
            draw_pollen_dot(screen, (cx, cy), HEX_SIZE)

        # ── 5. Dibujar abeja ──
        pq, pr = state.player
        px, py = axial_to_pixel(pq, pr, HEX_SIZE, offset_x, offset_y)
        if sprites.get("player"):
            draw_sprite(screen, sprites["player"], (px, py))
        else:
            pygame.draw.circle(screen, (255, 200, 0), (int(px), int(py)), HEX_SIZE // 2)

        # ── 5b. Dibujar avispas ──
        for wq, wr in wasps:
            wx, wy = axial_to_pixel(wq, wr, HEX_SIZE, offset_x, offset_y)
            if sprites.get("wasp"):
                draw_sprite(screen, sprites["wasp"], (wx, wy))
            else:
                pygame.draw.circle(screen, (255, 100, 0), (int(wx), int(wy)), HEX_SIZE // 2)

        # ── 6. HUD ──
        draw_hud(screen, font_title, font_body,
                 edit_mode, state.player, state.pollen,
                 TECNICAS[tec_idx], HEURISTICAS[heu_idx], camino_len)
        
        # ── 7. Contador de movimientos (esquina superior derecha) ──
        W_screen = screen.get_width()
        moves_surf = font_title.render(f"Movimientos: {move_count}", True, (56, 142, 60))
        moves_bg   = pygame.Surface((moves_surf.get_width() + 20, 36), pygame.SRCALPHA)
        moves_bg.fill((255, 255, 220, 210))
        screen.blit(moves_bg,   (W_screen - moves_bg.get_width() - 10, 10))
        screen.blit(moves_surf, (W_screen - moves_surf.get_width() - 20, 13))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()