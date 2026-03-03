from AgenteIA.Entorno import Entorno
from AgenteHex import AgenteHex


class EntornoHex(Entorno):

    def __init__(self, game_state):
        Entorno.__init__(self)
        self.game_state = game_state
        self.ultimo_camino = []       # camino encontrado (lista de celdas)
        self.tecnica = "a_estrella"
        self.heuristica = "hexagonal"
        self.wasps = []

    # ------------------------------------------------------------------
    # Entrega percepciones y lanza la búsqueda
    # ------------------------------------------------------------------
    def get_percepciones(self, agente):
        gs = self.game_state

        # Actualizar referencias al estado del tablero
        agente.grid = gs.grid
        agente.cell_type = gs.cell_type
        agente.set_heuristica(self.heuristica)

        agente.set_estado_inicial(gs.player)
        agente.set_estado_meta(gs.pollen)
        agente.set_tecnica(self.tecnica)

        agente.wasps = set(self.wasps)

    # ------------------------------------------------------------------
    # Recupera el camino calculado y lo almacena
    # ------------------------------------------------------------------
    def ejecutar(self, agente):
        agente.programa()
        acciones = agente.get_acciones()
        if acciones:
            self.ultimo_camino = acciones
            mr = agente.get_medida_rendimiento()
            print(f"[EntornoHex] Técnica: {self.tecnica} | "
                  f"Heurística: {self.heuristica} | "
                  f"Pasos: {mr.get('pasos', '?')} | "
                  f"Nodos expandidos: {mr.get('nodos_expandidos', '?')} | "
                  f"Tiempo: {mr.get('tiempo', 0):.4f}s")
        else:
            self.ultimo_camino = []
            print("[EntornoHex] No se encontró solución.")
        agente.inhabilitar()

    # ------------------------------------------------------------------
    # Dispara UNA sola evolución (percibir → buscar → guardar camino)
    # ------------------------------------------------------------------
    def buscar(self):
        gs = self.game_state
        if gs.pollen is None or gs.player == gs.pollen:
            self.ultimo_camino = []
            return

        agente = AgenteHex(gs.grid, gs.cell_type, self.heuristica)
        self.get_agentes().clear()
        self.insertar(agente)

        self.get_percepciones(agente)
        self.ejecutar(agente)

    def finalizar(self):
        return True