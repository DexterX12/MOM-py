import requests
import json
from time import time, sleep

class Connection:
    def __init__(self, type, exchange, routing_key, location):
        self.type = type
        self.exchange = exchange
        self.routing_key = routing_key
        self.location = location

        requests.post(self.location, json={
            "operation": "auth"
        })


        # Logic for checking if the connection was successfull and can be used

    def consume(self, callback):
        while True:
            response = requests.post(self.location, json={
                "operation": "pull",
                "data": {
                    "headers": {
                        "exchange": self.exchange,
                        "routing_key": self.routing_key,
                        "message_date": None
                    },
                    "body": None
                }
            })
            callback(response)
            sleep(5)
            
    def publish(self, message, callback):
        response = requests.post(self.location, json={
            "operation": "push",
            "data": {
                "headers": {
                    "exchange": self.exchange,
                    "routing_key": self.routing_key,
                    "message_date": int(time())
                },
                "body": message
            }
        })
        
        callback(response)