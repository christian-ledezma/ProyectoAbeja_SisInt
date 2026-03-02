import pygame
import math
import sys
import os

# ──────────────────────────────────────────────
#  ASEGURAR QUE LOS MÓDULOS DEL REPO SEAN VISIBLES
# ──────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from EntornoHex import EntornoHex
from reconocimiento_emociones import ReconocedorEmociones, EMOCIONES, NOMBRE_LEGIBLE

# ==============================
# CONFIGURACIÓN GENERAL
# ==============================
WIDTH, HEIGHT = 800, 880
HEX_SIZE = 25
RADIUS = 7
PANEL_Y = 720                 # Inicio del panel inferior (mascota)

SPRITES = {"player": "abeja2.png"}

# ── Colores generales ──
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
PATH_COLOR        = (180, 100, 255)
PATH_BORDER       = (120,  50, 200)
POLLEN_COLOR      = (255, 220,  50)
POLLEN_BORDER     = (200, 150,   0)

# ── Colores de emociones ──
COLOR_IRA       = (220,  60,  60)
COLOR_ALEGRIA   = (255, 220,  50)
COLOR_VERGUENZA = ( 50, 190,  80)
COLOR_TRISTEZA  = ( 70, 130, 220)

# ── Zonas de emociones (flores / estaciones) ──
ZONAS_EMOCIONES = {
    "ira": {
        "centro": (5, -2),
        "celdas": [(5, -2), (4, -2), (5, -3), (4, -1), (6, -3)],
        "color":       COLOR_IRA,
        "color_suave": (240, 150, 150),
        "border":      (170,  30,  30),
        "nombre": "Zona de Calma",
    },
    "alegria": {
        "centro": (-5, 2),
        "celdas": [(-5, 2), (-4, 2), (-5, 3), (-4, 1), (-6, 3)],
        "color":       COLOR_ALEGRIA,
        "color_suave": (255, 240, 150),
        "border":      (200, 170,   0),
        "nombre": "Zona de Celebración",
    },
    "verguenza": {
        "centro": (-2, -4),
        "celdas": [(-2, -4), (-1, -4), (-2, -3), (-3, -3), (-1, -5)],
        "color":       COLOR_VERGUENZA,
        "color_suave": (150, 220, 160),
        "border":      ( 30, 140,  50),
        "nombre": "Zona de Confianza",
    },
    "tristeza": {
        "centro": (2, 4),
        "celdas": [(2, 4), (3, 4), (2, 5), (1, 5), (3, 3)],
        "color":       COLOR_TRISTEZA,
        "color_suave": (150, 180, 240),
        "border":      ( 40,  80, 170),
        "nombre": "Zona de Juego",
    },
}

# ── Flores decorativas extra (posición, color) ──
FLORES_DECORATIVAS = [
    ((3, -5),  COLOR_IRA),
    ((-3, -1), COLOR_ALEGRIA),
    ((0, -6),  COLOR_VERGUENZA),
    ((-1, 6),  COLOR_TRISTEZA),
    ((6, -5),  COLOR_IRA),
    ((-6, 1),  COLOR_ALEGRIA),
    ((1, -3),  COLOR_VERGUENZA),
    ((4, 2),   COLOR_TRISTEZA),
]

# ── Fases del juego ──
FASE_IDLE       = "idle"
FASE_ESCUCHANDO = "escuchando"
FASE_PROCESANDO = "procesando"
FASE_DETECTADO  = "detectado"
FASE_CAMINANDO  = "caminando"
FASE_LLEGADA    = "llegada"
FASE_ERROR      = "error"

# ── Auto-caminado ──
AUTO_WALK_MS = 200             # milisegundos entre pasos

# ── Técnicas de búsqueda ──
TECNICAS    = ["costouniforme", "codicioso", "a_estrella"]
HEURISTICAS = ["hexagonal", "euclidiana"]


# ==============================
# CARGA DE SPRITES
# ==============================
def load_sprites(sprite_dict, hex_size):
    loaded = {}
    sprite_size = int(hex_size * 1.55)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for key, filename in sprite_dict.items():
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


def load_mascot_sprite(hex_size):
    """Sprite más grande de la abeja para el panel de la mascota."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, "abeja2.png")
    size = int(hex_size * 2.5)
    if os.path.exists(filepath):
        try:
            img = pygame.image.load(filepath).convert_alpha()
            return pygame.transform.smoothscale(img, (size, size))
        except pygame.error:
            return None
    return None


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
# DIBUJO – HEXÁGONOS
# ==============================
def draw_hex(surface, color, center, size, border_color=BORDER_COLOR, border_width=2):
    corners = [hex_corner(center, size, i) for i in range(6)]
    pygame.draw.polygon(surface, color, corners)
    if border_width > 0:
        pygame.draw.polygon(surface, border_color, corners, border_width)


# ==============================
# DIBUJO – FLORES
# ==============================
def draw_flower_icon(surface, center, color, size):
    """Ícono de flor de 5 pétalos sobre la celda central de una zona."""
    cx, cy = int(center[0]), int(center[1])
    petal_r  = max(3, int(size * 0.18))
    center_r = max(2, int(size * 0.12))
    dist     = int(petal_r * 1.2)
    petal_c  = (min(255, color[0] + 70),
                min(255, color[1] + 70),
                min(255, color[2] + 70))
    for i in range(5):
        a  = math.radians(72 * i - 90)
        px = cx + int(dist * math.cos(a))
        py = cy + int(dist * math.sin(a))
        pygame.draw.circle(surface, petal_c, (px, py), petal_r)
        pygame.draw.circle(surface, color,   (px, py), petal_r, 1)
    pygame.draw.circle(surface, (255, 255, 220), (cx, cy), center_r)
    pygame.draw.circle(surface, color,           (cx, cy), center_r, 1)


def draw_flower_small(surface, center, color, size):
    """Flor decorativa pequeña."""
    cx, cy = int(center[0]), int(center[1])
    r = max(2, int(size * 0.12))
    for i in range(5):
        a  = math.radians(72 * i - 90)
        px = cx + int(r * 1.1 * math.cos(a))
        py = cy + int(r * 1.1 * math.sin(a))
        pygame.draw.circle(surface, color, (px, py), r)
    pygame.draw.circle(surface, (255, 255, 230), (cx, cy), max(1, r - 1))


# ==============================
# DIBUJO – TEXTO CON AJUSTE
# ==============================
def render_text_wrapped(font, text, color, max_width):
    """Divide *text* en líneas que quepan en *max_width*."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return [font.render(l, True, color) for l in lines]


# ==============================
# DIBUJO – PANEL MASCOTA
# ==============================
def draw_panel_mascota(surface, fonts, mascot_sprite,
                       mensaje, sub_mensaje, hint, fase,
                       emocion_color, tick):
    """Panel inferior con la mascota-abeja y burbuja de diálogo."""
    font_t, font_b = fonts

    # ── Fondo ──
    panel = pygame.Surface((WIDTH, HEIGHT - PANEL_Y), pygame.SRCALPHA)
    panel.fill((245, 240, 230, 235))
    surface.blit(panel, (0, PANEL_Y))
    pygame.draw.line(surface, (190, 180, 160), (0, PANEL_Y), (WIDTH, PANEL_Y), 3)

    # ── Mascota ──
    mx, my = 55, PANEL_Y + 60
    if mascot_sprite:
        draw_sprite(surface, mascot_sprite, (mx, my))
    else:
        pygame.draw.circle(surface, (255, 200, 0), (mx, my), 28)

    # ── Burbuja ──
    bx, by, bw, bh = 115, PANEL_Y + 12, WIDTH - 145, 105
    bubble = pygame.Rect(bx, by, bw, bh)
    pygame.draw.rect(surface, (255, 255, 255), bubble, border_radius=14)
    pygame.draw.rect(surface, (180, 180, 180), bubble, 2, border_radius=14)
    # Triángulo apuntando a la mascota
    tri = [(bx, by + 30), (bx - 14, by + 45), (bx, by + 55)]
    pygame.draw.polygon(surface, (255, 255, 255), tri)
    pygame.draw.lines(surface, (180, 180, 180), False, tri, 2)

    # ── Indicador de micrófono ──
    if fase == FASE_ESCUCHANDO:
        mic_x, mic_y = WIDTH - 50, PANEL_Y + 28
        pulse = int(4 * math.sin(tick * 0.008)) + 14
        pygame.draw.circle(surface, (220, 50, 50), (mic_x, mic_y), pulse)
        pygame.draw.circle(surface, (255, 120, 120), (mic_x, mic_y), 6)
        lbl = font_b.render("REC", True, (255, 255, 255))
        surface.blit(lbl, (mic_x - lbl.get_width() // 2, mic_y + 16))

    # ── Texto principal ──
    msg_color = emocion_color if emocion_color else (50, 50, 50)
    lines = render_text_wrapped(font_t, mensaje, msg_color, bw - 30)
    for i, surf in enumerate(lines):
        surface.blit(surf, (bx + 15, by + 12 + i * 22))

    # ── Sub-mensaje ──
    if sub_mensaje:
        y_sub = by + 12 + len(lines) * 22 + 2
        for i, surf in enumerate(
            render_text_wrapped(font_b, sub_mensaje, (100, 100, 100), bw - 30)
        ):
            surface.blit(surf, (bx + 15, y_sub + i * 18))

    # ── Hint ──
    if hint:
        hint_s = font_b.render(hint, True, (150, 150, 150))
        surface.blit(hint_s, (bx + 15, by + bh - 22))


# ==============================
# DIBUJO – HUD
# ==============================
def draw_hud(surface, font_title, font_body,
             edit_mode, player_pos, target_name,
             tecnica, heuristica, camino_len):

    hud_surf = pygame.Surface((360, 90), pygame.SRCALPHA)
    hud_surf.fill((255, 250, 255, 220))
    pygame.draw.rect(hud_surf, (200, 230, 201, 255), (0, 0, 360, 90), 3)
    surface.blit(hud_surf, (10, 10))

    title = font_title.render("Panal de Sentimientos", True, HUD_TEXT)
    surface.blit(title, (20, 16))

    target_str = target_name if target_name else "---"
    mode_str = "[Edición]" if edit_mode else "[Juego]"
    surface.blit(font_body.render(
        f"{mode_str}  Objetivo: {target_str}", True, HUD_DIM), (20, 40))

    tec_c = (100, 180, 255)
    surface.blit(font_body.render(f"Técnica: {tecnica}", True, tec_c), (20, 58))
    surface.blit(font_body.render(f"Heurística: {heuristica}", True, tec_c), (200, 58))

    path_str = f"Camino: {camino_len} pasos" if camino_len > 0 else "Camino: —"
    surface.blit(font_body.render(path_str, True, PATH_COLOR), (20, 76))


# ==============================
# DIBUJO – ETIQUETAS DE ZONA
# ==============================
def draw_zona_labels(surface, font, zonas, hex_size,
                     offset_x, offset_y, emocion_resaltada, tick):
    for emo, info in zonas.items():
        cq, cr = info["centro"]
        cx, cy = axial_to_pixel(cq, cr, hex_size, offset_x, offset_y)
        color = info["color"]
        if emo == emocion_resaltada:
            b = int(40 * math.sin(tick * 0.006))
            color = (min(255, max(0, color[0] + b)),
                     min(255, max(0, color[1] + b)),
                     min(255, max(0, color[2] + b)))
        lbl = font.render(info["nombre"], True, color)
        lx = int(cx - lbl.get_width() / 2)
        ly = int(cy - hex_size * 1.7)
        bg = pygame.Surface((lbl.get_width() + 8, lbl.get_height() + 4), pygame.SRCALPHA)
        bg.fill((255, 255, 255, 180))
        surface.blit(bg, (lx - 4, ly - 2))
        surface.blit(lbl, (lx, ly))


# ==============================
# ESTADO DEL JUEGO
# ==============================
class GameState:
    def __init__(self, radius):
        self.grid = generate_hex_grid(radius)
        self.cell_type = {cell: "floor" for cell in self.grid}
        self.player = (0, 0)
        self.pollen = None

        # Celdas que pertenecen a una zona de emoción
        self.zona_celdas = {}           # (q,r) → emoción
        for emo, info in ZONAS_EMOCIONES.items():
            for celda in info["celdas"]:
                if celda in self.grid:
                    self.zona_celdas[celda] = emo

        # Flores decorativas
        self.flores_deco = {}           # (q,r) → color
        for pos, color in FLORES_DECORATIVAS:
            if pos in self.grid:
                self.flores_deco[pos] = color

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
        """Coloca el objetivo en una celda de piso."""
        if cell in self.grid and self.cell_type[cell] == "floor" and cell != self.player:
            self.pollen = cell


# ==============================
# MAIN
# ==============================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Panal de Sentimientos – Agente IA")
    clock = pygame.time.Clock()

    try:
        font_title = pygame.font.SysFont("segoeui", 18, bold=True)
        font_body  = pygame.font.SysFont("segoeui", 14)
        font_zona  = pygame.font.SysFont("segoeui", 12, bold=True)
    except Exception:
        font_title = pygame.font.SysFont(None, 18)
        font_body  = pygame.font.SysFont(None, 14)
        font_zona  = pygame.font.SysFont(None, 12)

    offset_x = WIDTH  // 2
    offset_y = PANEL_Y // 2 + 15

    sprites       = load_sprites(SPRITES, HEX_SIZE)
    mascot_sprite = load_mascot_sprite(HEX_SIZE)
    state         = GameState(RADIUS)
    entorno       = EntornoHex(state)
    reconocedor   = ReconocedorEmociones()

    # ── Variables de interfaz ──
    hovered_cell    = None
    edit_mode       = False
    tec_idx         = 2          # a_estrella
    heu_idx         = 0          # hexagonal
    path_cells      = set()
    camino_len      = 0
    fase            = FASE_IDLE
    emocion_actual  = None
    target_name     = None

    # Auto-caminado
    auto_walk       = False
    auto_walk_path  = []
    auto_walk_idx   = 0
    auto_walk_timer = 0

    # Mensajes del panel
    msg_mascota  = "¿Cómo te sientes hoy?"
    sub_mascota  = ""
    hint_mascota = "Presiona ESPACIO para hablar"

    print("=" * 52)
    print("  Panal de Sentimientos – Controles")
    print("=" * 52)
    print("  ESPACIO  -> hablar (reconocimiento de voz)")
    print("  S / Y    -> confirmar ir a zona")
    print("  N        -> cancelar")
    print("  E        -> alternar edición / juego")
    print("  T        -> cambiar técnica de búsqueda")
    print("  H        -> cambiar heurística")
    print("  ENTER    -> búsqueda manual al objetivo")
    print("  Clic izq -> mover (juego) / pared (edición)")
    print("  Clic der -> colocar objetivo (edición)")
    print("  ESC      -> salir")
    print("=" * 52)

    running = True
    while running:
        tick  = pygame.time.get_ticks()
        clock.tick(60)

        mouse_pos    = pygame.mouse.get_pos()
        hovered_cell = pixel_to_axial(*mouse_pos, HEX_SIZE, offset_x, offset_y)
        if hovered_cell not in state.grid:
            hovered_cell = None

        # ──────────────────────────────────────
        #  Polling del reconocedor de voz
        # ──────────────────────────────────────
        if fase in (FASE_ESCUCHANDO, FASE_PROCESANDO):
            r_est = reconocedor.estado
            if r_est == "processing" and fase == FASE_ESCUCHANDO:
                fase = FASE_PROCESANDO
                msg_mascota  = "Procesando tu respuesta..."
                sub_mascota  = ""
                hint_mascota = ""
            elif r_est == "done":
                fase = FASE_DETECTADO
                emocion_actual = reconocedor.emocion
                info_e = EMOCIONES[emocion_actual]
                zona   = ZONAS_EMOCIONES[emocion_actual]
                nombre = NOMBRE_LEGIBLE[emocion_actual]
                msg_mascota  = f"Sientes {nombre}. {info_e['consejo']}"
                sub_mascota  = f"¿Quieres ir a la {zona['nombre']}?"
                hint_mascota = "Presiona S para ir  |  N para cancelar"
                target_name  = zona["nombre"]
                state.set_pollen(zona["centro"])
            elif r_est == "error":
                fase = FASE_ERROR
                msg_mascota  = reconocedor.mensaje_error
                sub_mascota  = ""
                hint_mascota = "Presiona ESPACIO para intentar de nuevo"

        # ──────────────────────────────────────
        #  Auto-caminado
        # ──────────────────────────────────────
        if auto_walk and auto_walk_path:
            if tick - auto_walk_timer >= AUTO_WALK_MS:
                if auto_walk_idx < len(auto_walk_path):
                    state.player = auto_walk_path[auto_walk_idx]
                    auto_walk_idx += 1
                    auto_walk_timer = tick
                else:
                    auto_walk = False
                    fase = FASE_LLEGADA
                    zona = ZONAS_EMOCIONES.get(emocion_actual, {})
                    consejo = EMOCIONES.get(emocion_actual, {}).get("consejo", "")
                    msg_mascota  = f"¡Llegamos a la {zona.get('nombre', '')}!"
                    sub_mascota  = consejo
                    hint_mascota = "Presiona ESPACIO para hablar de nuevo"

        # ──────────────────────────────────────
        #  Eventos
        # ──────────────────────────────────────
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
                    path_cells = set(); camino_len = 0
                    print(f"Técnica: {entorno.tecnica}")

                elif event.key == pygame.K_h:
                    heu_idx = (heu_idx + 1) % len(HEURISTICAS)
                    entorno.heuristica = HEURISTICAS[heu_idx]
                    path_cells = set(); camino_len = 0
                    print(f"Heurística: {entorno.heuristica}")

                # ── ESPACIO → iniciar reconocimiento de voz ──
                elif event.key == pygame.K_SPACE:
                    if fase not in (FASE_ESCUCHANDO, FASE_PROCESANDO, FASE_CAMINANDO):
                        fase = FASE_ESCUCHANDO
                        msg_mascota  = "¡Habla! Cuéntame cómo te sientes..."
                        sub_mascota  = '(Di algo como "Estoy triste" o "Me siento feliz")'
                        hint_mascota = ""
                        emocion_actual = None
                        path_cells = set(); camino_len = 0
                        auto_walk = False
                        reconocedor.reset()
                        reconocedor.iniciar_escucha()

                # ── ENTER → búsqueda manual (debug) ──
                elif event.key == pygame.K_RETURN:
                    if state.pollen is not None:
                        entorno.buscar()
                        camino = entorno.ultimo_camino
                        path_cells = set(camino[1:-1]) if len(camino) > 2 else set()
                        camino_len = len(camino) - 1 if camino else 0

                # ── S / Y → confirmar ir a zona ──
                elif event.key in (pygame.K_s, pygame.K_y):
                    if fase == FASE_DETECTADO and emocion_actual:
                        zona = ZONAS_EMOCIONES[emocion_actual]
                        state.set_pollen(zona["centro"])
                        entorno.buscar()
                        camino = entorno.ultimo_camino
                        if camino and len(camino) > 1:
                            path_cells = set(camino[1:-1]) if len(camino) > 2 else set()
                            camino_len = len(camino) - 1
                            auto_walk       = True
                            auto_walk_path  = camino
                            auto_walk_idx   = 1
                            auto_walk_timer = tick
                            fase = FASE_CAMINANDO
                            msg_mascota  = f"¡Vamos a la {zona['nombre']}!"
                            sub_mascota  = ""
                            hint_mascota = ""
                        else:
                            fase = FASE_ERROR
                            msg_mascota  = "No encontré un camino. Intenta quitar paredes."
                            sub_mascota  = ""
                            hint_mascota = "Presiona ESPACIO para hablar de nuevo"

                # ── N → cancelar ──
                elif event.key == pygame.K_n:
                    if fase == FASE_DETECTADO:
                        fase = FASE_IDLE
                        emocion_actual = None
                        target_name    = None
                        msg_mascota  = "¿Qué necesitas? Estoy aquí para ti."
                        sub_mascota  = ""
                        hint_mascota = "Presiona ESPACIO para hablar"
                        path_cells = set(); camino_len = 0

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if hovered_cell and not auto_walk:
                    if event.button == 1:
                        if edit_mode:
                            state.toggle_wall(hovered_cell)
                        else:
                            state.move_player(hovered_cell)
                        path_cells = set(); camino_len = 0
                    elif event.button == 3 and edit_mode:
                        state.set_pollen(hovered_cell)
                        path_cells = set(); camino_len = 0
                        print(f"Objetivo colocado en {hovered_cell}")

        # ──────────────────────────────
        #  RENDERIZADO
        # ──────────────────────────────
        screen.fill(BACKGROUND_COLOR)
        neighbors_of_player = set(hex_neighbors(*state.player))

        # Precalcular celdas de zona
        zona_map = {}   # celda → (color, border, es_centro, emo)
        for emo, info in ZONAS_EMOCIONES.items():
            for celda in info["celdas"]:
                es_centro = (celda == info["centro"])
                c = info["color"] if es_centro else info["color_suave"]
                zona_map[celda] = (c, info["border"], es_centro, emo)

        # ── 1. Color de cada celda ──
        cell_data = {}
        for cell in state.grid:
            q, r   = cell
            cx, cy = axial_to_pixel(q, r, HEX_SIZE, offset_x, offset_y)

            is_wall     = state.cell_type[cell] == "wall"
            is_hover    = cell == hovered_cell
            is_neighbor = cell in neighbors_of_player and not is_wall
            is_path     = cell in path_cells
            is_pollen   = cell == state.pollen
            is_zona     = cell in zona_map

            if is_wall:
                color = WALL_COLOR
                bcol, bw = WALL_BORDER_COLOR, 2

            elif is_zona:
                zc, zb, es_cen, emo = zona_map[cell]
                if emo == emocion_actual and fase in (
                    FASE_DETECTADO, FASE_CAMINANDO, FASE_LLEGADA
                ):
                    b = int(30 * math.sin(tick * 0.005))
                    zc = (min(255, max(0, zc[0] + b)),
                          min(255, max(0, zc[1] + b)),
                          min(255, max(0, zc[2] + b)))
                color = zc
                bcol, bw = zb, (3 if es_cen else 2)

            elif is_path:
                color = PATH_COLOR
                bcol, bw = PATH_BORDER, 2

            elif is_pollen:
                color = POLLEN_COLOR
                bcol, bw = POLLEN_BORDER, 3

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

        # ── 2. Relleno ──
        for cell, (cx, cy, color, bcol, bw) in cell_data.items():
            draw_hex(screen, color, (cx, cy), HEX_SIZE, bcol, 0)

        # ── 3. Bordes ──
        for cell, (cx, cy, color, bcol, bw) in cell_data.items():
            corners = [hex_corner((cx, cy), HEX_SIZE, i) for i in range(6)]
            pygame.draw.polygon(screen, bcol, corners, bw)

        # ── 4. Flores principales (centro de zona) ──
        for emo, info in ZONAS_EMOCIONES.items():
            cq, cr = info["centro"]
            if (cq, cr) in cell_data:
                cx, cy = cell_data[(cq, cr)][:2]
                draw_flower_icon(screen, (cx, cy), info["color"], HEX_SIZE)

        # ── 5. Flores decorativas ──
        for pos, col in FLORES_DECORATIVAS:
            if pos in cell_data:
                cx, cy = cell_data[pos][:2]
                draw_flower_small(screen, (cx, cy), col, HEX_SIZE)

        # ── 6. Etiquetas de zona ──
        emo_resaltada = emocion_actual if fase in (
            FASE_DETECTADO, FASE_CAMINANDO, FASE_LLEGADA
        ) else None
        draw_zona_labels(screen, font_zona, ZONAS_EMOCIONES,
                         HEX_SIZE, offset_x, offset_y, emo_resaltada, tick)

        # ── 7. Abeja ──
        pq, pr = state.player
        px, py = axial_to_pixel(pq, pr, HEX_SIZE, offset_x, offset_y)
        if sprites.get("player"):
            draw_sprite(screen, sprites["player"], (px, py))
        else:
            pygame.draw.circle(screen, (255, 200, 0),
                               (int(px), int(py)), HEX_SIZE // 2)

        # ── 8. HUD ──
        draw_hud(screen, font_title, font_body,
                 edit_mode, state.player, target_name,
                 TECNICAS[tec_idx], HEURISTICAS[heu_idx], camino_len)

        # ── 9. Panel de la mascota ──
        emo_color = None
        if emocion_actual and emocion_actual in ZONAS_EMOCIONES:
            emo_color = ZONAS_EMOCIONES[emocion_actual]["color"]
        draw_panel_mascota(screen, (font_title, font_body), mascot_sprite,
                           msg_mascota, sub_mascota, hint_mascota,
                           fase, emo_color, tick)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()