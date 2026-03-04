from AgenteIA.AgenteBuscador import AgenteBuscador
import math


def hex_distance(a, b):
#numero de pasos mínimos)
    aq, ar = a
    bq, br = b
    return max(abs(aq - bq), abs(ar - br), abs((-aq - ar) - (-bq - br)))


def euclidean_distance(a, b):
    #distancia entre dos celdas axiales (proyectadas a pixel)
    aq, ar = a
    bq, br = b
    ax = math.sqrt(3) * (aq + ar / 2)
    ay = 3 / 2 * ar
    bx = math.sqrt(3) * (bq + br / 2)
    by = 3 / 2 * br
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


class AgenteHex(AgenteBuscador):

    def __init__(self, grid, cell_type, heuristica="hexagonal"):
        AgenteBuscador.__init__(self)
        self.grid = grid                  # set de tuplas (q, r) válidas
        self.cell_type = cell_type        # dict (q,r) -> "floor" | "wall"
        self.heuristica_tipo = heuristica  # "hexagonal" | "euclidiana"
        self.wasps = set()

    def set_heuristica(self, tipo):
        self.heuristica_tipo = tipo

    # ------------------------------------------------------------------
    # Sucesores: los 6 vecinos que estén en el grid y no sean pared
    # ------------------------------------------------------------------
    def generar_hijos(self, estado):
        q, r = estado
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
        hijos = []
        for dq, dr in directions:
            vecino = (q + dq, r + dr)
            if vecino in self.grid and self.cell_type.get(vecino) == "floor":
                if vecino not in self.wasps:
                    hijos.append(vecino)
        return hijos

    # ------------------------------------------------------------------
    # Costo: número de pasos (cada arista vale 1)
    # ------------------------------------------------------------------
    def get_costo(self, camino):
        return len(camino) - 1

    # ------------------------------------------------------------------
    # Heurística hacia la meta
    # ------------------------------------------------------------------
    def get_heuristica(self, camino):
        estado = camino[-1]
        meta = self.get_estado_meta()
        if self.heuristica_tipo == "euclidiana":
            return euclidean_distance(estado, meta)
        else:
            return hex_distance(estado, meta)