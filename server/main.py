from flask import Flask, request, jsonify
import threading
from collections import defaultdict
from message import Message

app = Flask(__name__)
queues = defaultdict(list)

lock = threading.Lock()

@app.route("/")
def welcoming():
    return "<h1>MOM test</h1>"

@app.route("/", methods=["POST"])
def post():
    data = request.json
    operation = data.get("operation")

    print(operation)
    
    if (operation not in ["auth", "pull", "push"]):
        return jsonify({"error": "Invalid operation :("}), 400

    if (operation in ["pull", "push"]):
        message_data = data.get("data")
        
        message = Message(
            message_date=message_data["headers"].get("message_date"),
            routing_key=message_data["headers"].get("routing_key"),
            exchange=message_data["headers"].get("exchange"),
            content=message_data.get("body")
        )
        if operation == "push":
            return bind_queue(message)
        else:
            return pull(message)
    else:
        return jsonify({"auth": "fkor5oj34mgFdojFGhpAdme#"}), 200
        

 #Creation of the queue - exchange, routing key   
def bind_queue(message):
    exchange = message.header["exchange"] 
    routing_key = message.header["routing_key"]

    if not exchange or not routing_key:
        return jsonify({"error": "Missing exchange or routing_key"}), 400
    
    else:
        queue_name = exchange+"_"+routing_key

        with lock:
            queues[queue_name].append(message)
        #     print(f"Mensaje  {message.body} encolado en {queue_name}")
        # for queue_name, messages in queues.items():
        #     print(f"Mensajes en la cola '{queue_name}':")
        #     for message in messages:
        #         print(f"- {message.body}")

        return jsonify({
            "status": "Message pushed",
            "queue_name": queue_name,
            "exchange": exchange,
            "routing_key": routing_key
        }), 200

def pull(message):
    exchange = message.header["exchange"] 
    routing_key = message.header["routing_key"]

    if not exchange or not routing_key:
        return jsonify({"error": "Missing exchange or routing_key"}), 400
    
    else:
        queue_name = exchange+"_"+routing_key

        with lock:
            if queue_name in queues and queues[queue_name]:
                message = queues[queue_name].pop(0)
                print(f"Mensaje entregado a cliente desde {queue_name}: {message.body}")

                return jsonify({
                "status": "Message delivered",
                "queue_name": queue_name,
                "message": {
                    "message_date": message.header["message_date"],  
                    "routing_key": message.header["routing_key"],  
                    "exchange": message.header["exchange"], 
                    "body": message.body
                }
            }), 200
        return jsonify({"error": "No messages available in the queue"}), 404




