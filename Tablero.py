from AgenteIA.Entorno import Entorno


class Tablero(Entorno):

    def __init__(self, tamanio=3):
        Entorno.__init__(self)
        self.tamanio = tamanio
        self.estado_objetivo = tuple(range(tamanio * tamanio))

    def get_percepciones(self, agente):
        agente.set_percepciones(self.tamanio)
        agente.estado_objetivo = self.estado_objetivo
        agente.programa()

    def ejecutar(self, agente):
        print("Estado inicial:")
        self.mostrar_tablero(agente.get_estado_inicial())
        print("\nEstado objetivo:")
        self.mostrar_tablero(self.estado_objetivo)
        print("\nSolucion:")
        
        # for i, estado in enumerate(agente.get_acciones()):
        #     print(f"\nPaso {i}:")
        #     self.mostrar_tablero(estado)
        
        # print("\nDistancia total:", agente.get_medida_rendimiento()["Costo"])
        print("Pasos de la solucion:", agente.get_medida_rendimiento()["pasos"])
        print("Nodos expandidos:", agente.get_medida_rendimiento()["nodos_expandidos"])
        print("Profundidad maxima:", agente.get_medida_rendimiento()["max_profundidad"])
        print("Tiempo de respuesta:", agente.get_medida_rendimiento()["tiempo"])
        
        agente.inhabilitar()

    def mostrar_tablero(self, estado):
        for i in range(self.tamanio):
            fila = estado[i * self.tamanio:(i + 1) * self.tamanio]
            print(" ".join(str(x) if x != 0 else " " for x in fila))