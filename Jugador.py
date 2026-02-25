from AgenteIA.AgenteBuscador import AgenteBuscador


class Jugador(AgenteBuscador):

    def __init__(self, heuristica="manhattan"):
        AgenteBuscador.__init__(self)
        self.tamanio = 3
        self.estado_objetivo = None
        self.heuristica_tipo = heuristica

    def set_heuristica(self, tipo):
        self.heuristica_tipo = tipo

    def generar_hijos(self, estado):
        hijos = []
        estado_lista = list(estado)
        pos_vacio = estado_lista.index(0)
        fila = pos_vacio // self.tamanio
        col = pos_vacio % self.tamanio
        
        movimientos = []
        if fila > 0:
            movimientos.append(-self.tamanio)
        if fila < self.tamanio - 1:
            movimientos.append(self.tamanio)
        if col > 0:
            movimientos.append(-1)
        if col < self.tamanio - 1:
            movimientos.append(1)
        
        for mov in movimientos:
            nueva_pos = pos_vacio + mov
            nuevo_estado = estado_lista[:]
            nuevo_estado[pos_vacio], nuevo_estado[nueva_pos] = nuevo_estado[nueva_pos], nuevo_estado[pos_vacio]
            hijos.append(tuple(nuevo_estado))
        
        return hijos

    def get_costo(self, camino):
        return len(camino) - 1

    def get_heuristica(self, camino):
        estado = camino[-1]
        
        if self.heuristica_tipo == "fichas_mal_colocadas":
            return self._heuristica_fichas_mal_colocadas(estado)
        elif self.heuristica_tipo == "manhattan":
            return self._heuristica_manhattan(estado)
        else:
            return 0

    def _heuristica_fichas_mal_colocadas(self, estado):
        return sum(1 for i in range(len(estado)) if estado[i] != 0 and estado[i] != self.estado_objetivo[i])

    def _heuristica_manhattan(self, estado):
        distancia = 0
        for i in range(len(estado)):
            if estado[i] != 0:
                pos_actual = i
                pos_objetivo = self.estado_objetivo.index(estado[i])
                
                fila_actual = pos_actual // self.tamanio
                col_actual = pos_actual % self.tamanio
                fila_objetivo = pos_objetivo // self.tamanio
                col_objetivo = pos_objetivo % self.tamanio
                
                distancia += abs(fila_actual - fila_objetivo) + abs(col_actual - col_objetivo)
        
        return distancia