from flask import Flask, request, jsonify
from kazoo.client import KazooClient
from partitioning import ConsistentHashRing
import requests

app = Flask(__name__)

IP_ZOOKEEPER = "127.0.0.1:2181"
ZK_PATH = "connected/"

zk = KazooClient(hosts=IP_ZOOKEEPER)
zk.start()

if not zk.exists(ZK_PATH):
    zk.ensure_path(ZK_PATH) #Verificamos que la ruta exista, si no, la creamos para evitar errores

ring = ConsistentHashRing(replicas=100) #Inicializamos el anillo (Se puede cambiar el número de replicas)


@zk.ChildrenWatch(path=ZK_PATH)
def cargar_nodos(children):
    ring.ring.clear()
    ring.sorted_keys.clear() #Limpiamos el anillo para que no se acumulen los nodos cada vez que se actualice
    nodos = zk.get_children(ZK_PATH) #Obtenemos los nodos registrados en el path
    for nodo in nodos:
        ring.add_node(nodo) #Agregamos los nodos y sus réplicas
    return nodos

@app.route("/routing", methods=["POST"])
def routing():
    data = request.get_json()
    routing_key = data.get("routing_key") #Tomamos la routing_key del json

    if not routing_key:
        return jsonify({"error": "Missing 'routing_key'"}), 400 #Si no hay routing_key

    nodo = ring.get_node(routing_key) #Calcula a que nodo va la clave
    contenders = zk.Election(f"/partitions/{routing_key}").lock.contenders()

    if len(contenders) > 0:
        # Only check this if it node already exists, if not, then ZooKeeper didn't do anything.
        if nodo and contenders[0] != nodo: # ZooKeeper made fail over, it takes precedence
            return jsonify({
                "routing_key": routing_key,
                "assigned_node": contenders[0],
                "node_location": zk.get(f"{ZK_PATH}{contenders[0]}")[0].decode('utf-8')
            })

    if not nodo:
        return jsonify({"error": "No nodes available"}), 503 #Si no hay nosdos disponibles
    
    print(routing_key +" pertenece a " + nodo)

    return jsonify({
        "routing_key": routing_key,
        "assigned_node": nodo,
        "node_location": zk.get(f"{ZK_PATH}{nodo}")[0].decode('utf-8')
    }) #Devuelve la routing_key y el nodo asignado

