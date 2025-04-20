from flask import Flask, request, jsonify
from kazoo.client import KazooClient
from partitioning import ConsistentHashRing

app = Flask(__name__)

IP_ZOOKEEPER = "158.247.127.78:6666"
ZK_PATH = "connected/"

zk = KazooClient(hosts=IP_ZOOKEEPER)
zk.start()

informacion = "192.168.1.1:12345"
zk.create(f"{ZK_PATH}nodo1", value=bytes(informacion, "utf-8"), ephemeral=True)
informacion = "192.168.1.2:12345"
zk.create(f"{ZK_PATH}nodo2", value=bytes(informacion, "utf-8"), ephemeral=True)

if not zk.exists(ZK_PATH):
    zk.ensure_path(ZK_PATH) #Verificamos que la ruta exista, si no, la creamos para evitar errores

ring = ConsistentHashRing(replicas=100) #Inicializamos el anillo (Se puede cambiar el número de replicas)

def cargar_nodos():
    ring.ring.clear()
    ring.sorted_keys.clear() #Limpiamos el anillo para que no se acumulen los nodos cada vez que se actualice
    nodos = zk.get_children(ZK_PATH) #Obtenemos los nodos registrados en el path
    for nodo in nodos:
        ring.add_node(nodo) #Agregamos los nodos y sus réplicas
    return nodos
cargar_nodos()

@app.route("/nodos", methods=["POST"])
def nodos():
    nodos = cargar_nodos() #Para ver que nodos están activos
    return jsonify({"nodos": nodos})

@app.route("/routing", methods=["POST"])
def routing():
    data = request.get_json()
    routing_key = data.get("routing_key") #Tomamos la routing_key del json

    if not routing_key:
        return jsonify({"error": "Missing 'routing_key'"}), 400 #Si no hay routing_key

    nodo = ring.get_node(routing_key) #Calcula a que nodo va la clave
    if not nodo:
        return jsonify({"error": "No nodes available"}), 503 #Si no hay nosdos disponibles
    print(routing_key +" pertenece a " + nodo)
    return jsonify({
        "routing_key": routing_key,
        "assigned_node": nodo
    }) #Devuelve la routing_key y el nodo asignado

@app.teardown_appcontext
def cerrar_zookeeper(exception):
    zk.stop()

