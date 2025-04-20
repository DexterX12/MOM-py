import hashlib
import bisect
class ConsistentHashRing:
    def __init__(self, replicas=5):
        self.replicas = replicas  #Número de nodos virtuales por nodo físico (para mejor balanceo), se supone que entre mas, mejor
        self.ring = dict() #Diccionario donde la clave es un hash y el valor es el id del nodo físico
        self.sorted_keys = [] #Lista ordenada de los hashes para recorrer el anillo eficientemente
        #Mis muchachos se usan nodos virtuales ya que sin estos algunas claves podrían caer siempre en los mismos nodos ¡Desbalancee!

    def _hash(self, key):
        #Devuelve un entero hash a partir de una clave string (virtual_node_id)
        return int(hashlib.sha256(key.encode('utf-8')).hexdigest(), 16)
        #El anillo de hash necesita enteros para ubicar claves y nodos

    def add_node(self, node_id):
        #Añade un nodo con n réplicas virtuales al anillo 
        for i in range(self.replicas):
            virtual_node_id = f"{node_id}#{i}" #Diferencias nodos virtuales del nodo físico
            key = self._hash(virtual_node_id) 
            self.ring[key] = node_id #Asocia el hash del nodo virtual con el nodo real
            bisect.insort(self.sorted_keys, key) #Inserta el hash manteniendo el orden
        #El anillo debe estar ordenado para que podamos buscar eficientemente el nodo que sigue a cada clave :)

    def remove_node(self, node_id):
        #Elimina un nodo (y sus réplicas) del anillo
        for i in range(self.replicas):
            virtual_node_id = f"{node_id}#{i}"
            key = self._hash(virtual_node_id)
            del self.ring[key]
            self.sorted_keys.remove(key)
        #Para mantener el anillo actualizado si un nodo se cae

    def get_node(self, key):
        #Asigna una routing_key al nodo más cercano en el anillo
        if not self.ring:
            return None #Si el anillo está vacío
        hashed_key = self._hash(key)
        idx = bisect.bisect(self.sorted_keys, hashed_key) % len(self.sorted_keys) #Busca el índice donde esta clave debería insertarse (nodo más cercano hacia la derecha), si es el ultimo vuelve al principio (es un anillo o)
        return self.ring[self.sorted_keys[idx]] #Devuelve el nodo con esta clave


