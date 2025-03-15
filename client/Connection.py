import requests

class Connection:
    def __init__(self, type, exchange, location):
        self.type = type
        self.exchange = exchange
        self.location = location

        # Logic for checking if the connection was successfull and can be used

    def consume(self, callback):
        while True:
            response = requests.post(self.location, {
                "operation": "pull",
                "exchange": self.exchange
            })
            callback(response)
            
    def publish(self, callback):
        response = requests.post(self.location, {
            "operation": "push",
            "exchange": self.exchange
        })
        
        callback(response)