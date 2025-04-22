import requests
import json
from time import time, sleep

class Connection:
    def __init__(self, type, exchange, routing_key, config):
        self.type = type
        self.exchange = exchange
        self.routing_key = routing_key
        self.location = config["MOM_SERVER_LOCATION"]
        self.__connection_token = None

        response = requests.post(f"{self.location}/auth", json={
            "user": config["USERNAME"],
            "pass": config["PASSWORD"]
        })

        token = response.json()["token"]

        if (token):
            self.__connection_token = token

    def consume(self, callback):
        if not self.__connection_token:
            return PermissionError("No authorization token has been provided")

        while True:
            response = requests.post(self.location+"/send", json={
                "operation": "pull",
                "type": self.type,
                "data": {
                    "headers": {
                        "exchange": self.exchange,
                        "routing_key": self.routing_key,
                        "message_date": None
                    },
                    "body": None
                }
            }, headers={
                "Authorization": f"Bearer {self.__connection_token}"
            })
            callback(response)
            sleep(5)
            
    def publish(self, message, callback):
        if not self.__connection_token:
            return PermissionError("No authorization token has been provided")
        
        response = requests.post(self.location+"/send", json={
            "operation": "push",
            "type": self.type,
            "data": {
                "headers": {
                    "exchange": self.exchange,
                    "routing_key": self.routing_key,
                    "message_date": int(time())
                },
                "body": message
            }
        }, headers={
            "Authorization": f"Bearer {self.__connection_token}"
        })
        
        callback(response)
    
    def subscribe(self, callback):
        if not self.__connection_token:
            return PermissionError("No authorization token has been provided")
        
        response = requests.post(self.location+"/send", json={
            "operation": "subscribe",
            "type": self.type,
            "username": "asd",
            "data": {
                "headers": {
                    "exchange": self.exchange,
                    "routing_key": self.routing_key,
                    "message_date": None
                },
                "body": None
            }
        }, headers={
            "Authorization": f"Bearer {self.__connection_token}"
        })
        callback(response)
