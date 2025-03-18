class Message:
    def __init__(self, message_date, routing_key, exchange, content):
        self.header = {
            "message_date": message_date,
            "routing_key": routing_key,
            "exchange": exchange
        }
        self.body = content