import hashlib
import bisect
from kazoo.client import KazooClient

IP_ZOOKEEPER = "158.247.127.78:6666" #IP que nos dio delvincin

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


#Nos conectamos a ZooKeeper
zk = KazooClient(hosts=IP_ZOOKEEPER)
zk.start()
ruta = "connected/"

#Prueba creando n nodos
informacion = "192.168.1.1:12345"
zk.create(f"{ruta}nodo1", value=bytes(informacion, "utf-8"), ephemeral=True)
informacion = "192.168.1.2:12345"
zk.create(f"{ruta}nodo2", value=bytes(informacion, "utf-8"), ephemeral=True)
informacion = "192.168.1.3:12345"
zk.create(f"{ruta}nodo3", value=bytes(informacion, "utf-8"), ephemeral=True)
informacion = "192.168.1.4:12345"
zk.create(f"{ruta}nodo4", value=bytes(informacion, "utf-8"), ephemeral=True)
informacion = "192.168.1.5:12345"
zk.create(f"{ruta}nodo5", value=bytes(informacion, "utf-8"), ephemeral=True)
informacion = "192.168.1.6:12345"
zk.create(f"{ruta}nodo6", value=bytes(informacion, "utf-8"), ephemeral=True)

#Nodos disponibles
nodos = zk.get_children(ruta)
print("Nodos disponibles:", nodos)

#Inicializar anillo de Consistent Hashing
ring = ConsistentHashRing(replicas=100)  #Mientras más réplicas, más uniforme la distribución, se puede cambiar si quieren

#Añadir nodos al anillo
for nodo in nodos:
    ring.add_node(nodo)

#Lista de routing_keys de prueba
routing_keys = [
    "logs", "warning", "info", "processed", "error", "successful","detention", "passed", "parsed", "signin", "logout", "information"
]

#Asignar cada routing_key a un nodo
for key in routing_keys:
    nodo_asignado = ring.get_node(key)
    print(f"routing_key '{key}' → nodo '{nodo_asignado}'")

#Cerrar conexión con ZooKeeper
zk.stop()
