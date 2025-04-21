from kazoo.client import KazooClient
from time import sleep
from functools import partial
#from util import get_machine_ip
import kazoo.exceptions
import threading
import uuid
import socket
import json
import pathlib

watched_partitions = set()

class ZooKeeperClient():
    def __init__(self, FLASK_PORT):
        path = pathlib.Path("config.json")
        with open(f"{pathlib.Path.absolute(path)}", "r") as file:
            self.CONFIG = json.load(file)

        self.BASE_PATH = self.CONFIG["PARTITIONS_LOCATION"]
        self.NODES_PATH = self.CONFIG["NODES_LOCATION"]
        self.FLASK_PORT = FLASK_PORT

        self.zk = KazooClient(hosts=self.CONFIG["ZOOKEEPER_LOCATION"])
        self.zk.start(timeout=5)
        self.zk.ensure_path(self.BASE_PATH)
        
        self.node_name = str(uuid.uuid4())
        self.machine_ip = get_machine_ip()

        self.zk.ensure_path(self.NODES_PATH)
        self.zk.create(f"{self.NODES_PATH}{self.node_name}/", value=bytes(f"{self.machine_ip}:{self.FLASK_PORT}", encoding="utf-8"), ephemeral=True)

        @self.zk.ChildrenWatch(path=self.BASE_PATH)
        def change_awareness(children):
            self.follower_function()

            partitions = self.zk.get_children(self.BASE_PATH)
            for part in partitions:
                if part not in watched_partitions:
                    self.setWatcher(part)
                    watched_partitions.add(part)

    def leader_function(self, partition):
        while True:
            election = self.zk.Election(f"{self.BASE_PATH}{partition}/", identifier=self.node_name)
            print(f"I am the leader of {partition}, identified as:\n{self.node_name}\n")
            print("Contenders of leader for this partition:")
            for contender in election.lock.contenders():
                print("----Node name: ", contender)
            print("\n\n\n")
            sleep(2)

    # Followers do nothing, just receive information about possible crashes in some node
    def follower_function(self):
        print(self.zk.get_children(self.NODES_PATH))
        partitions = self.zk.get_children(self.BASE_PATH)
        for part in partitions:
            election = self.zk.Election(f"{self.BASE_PATH}{part}/", identifier=self.node_name)
            contenders = election.lock.contenders()
            children = self.zk.get_children(self.BASE_PATH + part)

            # if the first contender is THIS node, then just omit it, you're already the leader
            if (len(contenders)>0):
                if (contenders[0] == str(self.node_name)):
                    pass
                    #print("Already a leader")
                else:
                    if (str(self.node_name) not in contenders):
                        process = threading.Thread(target=election.run, args=[partial(self.leader_function, part)], daemon=True)
                        process.start()
                    else:
                        pass
                        #print("I am already a contender/follower for this partition")
            else:
                if (len(children)>0 and children[0] == "leader"):
                    process = threading.Thread(target=election.run, args=[partial(self.leader_function, part)], daemon=True)
                    process.start()

    def track_partition(self, routing_key):
        self.zk.ensure_path(f"{self.BASE_PATH}{routing_key}/")
        election = self.zk.Election(self.BASE_PATH + routing_key, identifier=self.node_name)

        if (str(self.node_name) in election.lock.contenders()):
            #print("You're already there, so it means you're either a follower or a leader.")
            return

        path = f"{self.BASE_PATH}{routing_key}/leader"
        try:
            self.zk.create(path, ephemeral=True, value=bytes(str(self.node_name), encoding="utf-8"))
        except kazoo.exceptions.NodeExistsError:
            pass

        process = threading.Thread(target=election.run, args=[partial(self.leader_function, routing_key)], daemon=True)
        process.start()

    def setWatcher(self, partition):
        @self.zk.ChildrenWatch(path=self.BASE_PATH+partition)
        def call_follower(children):
            self.follower_function()