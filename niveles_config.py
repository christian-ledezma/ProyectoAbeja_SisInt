import random

# ─────────────────────────────────────────────
#  Mapas estáticos de paredes por nivel
#  Cada set contiene celdas (q, r) que serán muro
# ─────────────────────────────────────────────

PAREDES_POR_NIVEL = [

    # Nivel 0 – Explorador Novato
    {
        (2,0),(2,-1),(2,-2),
        (-2,0),(-2,1),(-2,2),

        (0,2),(1,1),
        (0,-2),(-1,-1),
    },

    # Nivel 1 – Pequeño Aventurero
    {
        (2,0),(2,-1),(2,-2),(1,-2),
        (-2,0),(-2,1),(-2,2),(-1,2),

        (0,3),(1,2),
        (0,-3),(-1,-2),

        (3,-1),(3,-2),
        (-3,1),(-3,2),
    },

    # Nivel 2 – Gran Explorador
    {
        (2,1),(2,0),(2,-1),
        (3,-1),(4,-1),

        (-2,-1),(-2,0),(-2,1),
        (-3,1),(-4,1),

        (1,3),(0,3),(-1,3),
        (1,-3),(0,-3),(-1,-3),

        (3,2),(3,1),
        (-3,-2),(-3,-1),
    },

    # Nivel 3 – Héroe Valiente
    {
        (3,1),(3,0),(3,-1),(3,-2),
        (2,-2),(1,-2),

        (-3,-1),(-3,0),(-3,1),(-3,2),
        (-2,2),(-1,2),

        (1,3),(0,3),(-1,3),

        (1,-3),(0,-3),(-1,-3),

        (4,0),(4,-1),(4,-2),
        (-4,0),(-4,1),(-4,2),
    },

    # Nivel 4 – Maestro de la Aventura
    {
        # columna derecha
        (4,1),(4,0),(4,-1),(4,-2),(4,-3),

        # columna izquierda
        (-4,-1),(-4,0),(-4,1),(-4,2),(-4,3),

        # techo
        (1,4),(0,4),(-1,4),(-2,4),

        # piso
        (1,-4),(0,-4),(-1,-4),(-2,-4),

        # laberinto interior
        (2,2),(2,1),
        (1,-1),(2,-1),
        (-1,1),(-2,1),
        (-1,-1),(-2,-1),

        (3,2),(3,1),
        (-3,-2),(-3,-1),

        (0,2),(0,-2)
    },
]

AVISPAS_POR_NIVEL = [2, 4, 8, 12, 16]


def configurar_nivel(game_state, nivel_idx):
    # 1. Resetear todas las celdas a floor
    for cell in game_state.grid:
        game_state.cell_type[cell] = "floor"

    # 2. Aplicar paredes del nivel (solo las que estén dentro del grid)
    paredes = PAREDES_POR_NIVEL[nivel_idx]
    for cell in paredes:
        if cell in game_state.grid:
            game_state.cell_type[cell] = "wall"

    # 3. Asegurar que la celda del jugador y pollen no queden tapadas
    game_state.cell_type[game_state.player] = "floor"

    # 4. Colocar avispas aleatoriamente en celdas floor libres
    n_avispas = AVISPAS_POR_NIVEL[nivel_idx]
    celdas_libres = [
        c for c in game_state.grid
        if game_state.cell_type[c] == "floor"
        and c != game_state.player
        and c != game_state.pollen
    ]
    random.shuffle(celdas_libres)
    avispas = celdas_libres[:n_avispas]
    return avispas