from Jugador import Jugador
from Tablero import Tablero



if __name__=="__main__":
    tablero = Tablero(tamanio=3)
    
    jugador = Jugador(heuristica="fichas_mal_colocadas")
    jugador.set_estado_inicial((1, 2, 3, 4, 5, 6, 0, 7, 8))
    jugador.set_estado_meta((0, 1, 2, 3, 4, 5, 6, 7, 8))
    # jugador.set_tecnica("a_estrella")
    jugador.set_tecnica("costouniforme")
    # jugador.set_tecnica("codicioso")
    
    tablero.insertar(jugador)
    tablero.run()
