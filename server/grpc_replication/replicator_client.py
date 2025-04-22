from . import replicator_pb2
from . import replicator_pb2_grpc
from util import get_machine_ip
from kazoo.client import KazooClient
import grpc
import json
import pathlib

IP_ZOOKEEPER = "127.0.0.1:2181"
ZK_PATH = "connected/"

path = pathlib.Path("config.json")
with open(f"{pathlib.Path.absolute(path)}", "r") as file:
    CONFIG = json.load(file)
    IP_ZOOKEEPER = CONFIG["ZOOKEEPER_LOCATION"]
    ZK_PATH = CONFIG["NODES_LOCATION"]

def get_message(datos):
    zk = KazooClient(hosts=IP_ZOOKEEPER)
    zk.start()

    if ("replication" in datos): # Stop replicating yourself endlessly!
        return

    zk.ensure_path(ZK_PATH)
    nodos = zk.get_children(ZK_PATH)
    znodes = []
    for nodo in nodos:
        znode = zk.get(f"{ZK_PATH}{nodo}")
        ip = znode[0].decode("utf-8").split(":")[0]
        znodes.append(ip)
    for i in znodes:
        if (i == get_machine_ip()):
            continue
        
        with grpc.insecure_channel(f"{i}:50051") as channel:
            stub = replicator_pb2_grpc.ReplicateStub(channel)
            response = stub.PopulateReplication(replicator_pb2.MessageMOM(
            body=datos["data"]["body"],
            exchange=datos["data"]["headers"]["exchange"],
            routing_key=datos["data"]["headers"]["routing_key"],
            type=datos["type"],
            operation=datos["operation"],
            username=datos["user"]["username"],
            message_date=datos["data"]["headers"]["message_date"]
            ))
    zk.stop()
    zk.close()