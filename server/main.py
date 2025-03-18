from flask import Flask, request, jsonify
import threading
from collections import defaultdict
from message import Message

app = Flask(__name__)
exchanges = defaultdict(lambda:defaultdict(list))
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
        return bind_queue(message)
    else:
        return jsonify({"auth": "fkor5oj34mgFdojFGhpAdme#"}), 200
        
queues_pre = [
        {"queue_name": "queue_1","exchange": "logs","routing_key": "info"},
        {"queue_name": "queue_2","exchange": "logs","routing_key": "error"},
        {"queue_name": "queue_3","exchange": "events","routing_key": "user_login"}
    ]

 #Creation of the queue - exchange, routing key   
def bind_queue(message):
    
    exchange = message.header["exchange"] 
    routing_key = message.header["routing_key"]
    print(exchange, " ", routing_key)

    if not exchange or not routing_key:
        return jsonify({"error": "Missing exchange or routing_key"}), 400
    
    for queue in queues_pre:
        if queue["exchange"] == exchange and queue["routing_key"] == routing_key:
            queue_name = queue["queue_name"]

            with lock:
                queues[queue_name].append(message)
                print(f"Mensaje  {message.body} encolado en {queue_name}")

            return jsonify({
                "status": "Message pushed",
                "queue_name": queue_name,
                "exchange": exchange,
                "routing_key": routing_key
            }), 200
    return  jsonify({"error": "Queue does not exist"}), 404
    




