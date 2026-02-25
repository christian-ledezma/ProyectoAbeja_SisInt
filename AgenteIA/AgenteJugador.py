from AgenteIA.Agente import Agente
from collections import namedtuple


ElEstado = namedtuple('ElEstado', 'jugador, get_utilidad, tablero, movidas')

class AgenteJugador(Agente):

    def __init__(self):
        Agente.__init__(self)
        self.estado = None
        self.juego = None
        self.utilidad = None

    def jugadas(self, estado):
        raise Exception("Ahhh no se implemento")

    def get_utilidad(self, estado, jugador):
        raise Exception("Ahhh no se implemento")

    def test_terminal(self, estado):
        return not self.jugadas(estado)

    def get_resultado(self, estado, m):
        raise Exception("Ahhh no se implemento")

    def programa(self):
        self.set_acciones(self.minimax(self.estado, self.estado.jugador))

    def minimax(self, estado, jugador):
        # jugador = estado.jugador

        def valor_max(e):
            if self.test_terminal(e):
                return self.get_utilidad(e, jugador)
            v = -100
            for a in self.jugadas(e):
                v = max(v, valor_min(self.get_resultado(e, a)))
            return v

        def valor_min(e):
            if self.test_terminal(e):
                return self.get_utilidad(e, jugador)
            v = 100
            for a in self.jugadas(e):
                v = min(v, valor_max(self.get_resultado(e, a)))
            return v

        return max(self.jugadas(estado), key=lambda a : valor_min(self.get_resultado(estado, a)))