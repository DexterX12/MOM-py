from flask import Flask, request, jsonify, Response
import threading
from collections import defaultdict
from message import Message
import jwt

app = Flask(__name__)
queues = defaultdict(list)

app.config.from_prefixed_env() # ENVIROMENT VARIABLE FLASK_SECRET_KEY
lock = threading.Lock()

@app.route("/")
def welcoming():
    return "<h1>MOM test</h1>"

@app.route("/auth", methods=["POST"])
def log_in():
    data = request.json
    username = data.get("user")
    pw = data.get("pass")

    user = check_user(username, pw)

    if not user:
        return jsonify({"error": "Invalid credentials!"}), 401
    
    # expects and ID from user as bearer identifier
    auth_token = jwt.encode({"id": user["id"]}, app.secret_key, algorithm="HS256")
    return jsonify({"token": auth_token}), 200

@app.route("/", methods=["POST"])
def post():
    data = request.json
    operation = data.get("operation")
    auth = request.headers.get("Authorization");
    user = None

    if not auth:
        response = Response()
        response.status_code = 401;
        response.headers["WWW-Authenticate"] = "Bearer"

        return response
    elif len(auth.split(" ")) < 2:
        return jsonify({"error": "No token provided"}), 401
    else:
        try:
            token = auth.split(" ")[1]

            # Not failing means they are who they claim to be
            user = jwt.decode(token, app.secret_key, algorithms="HS256")
            
        except jwt.exceptions.InvalidTokenError:
            return jsonify({"error": "Invalid token provided"}), 401
        
    
    if operation not in ["pull", "push"]:
        return jsonify({"error": "Invalid operation :("}), 400

    if operation in ["pull", "push"]:
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


# Check in DB if the client is indeed a registered user
def check_user(username, password):
    # BOILERPLATE, DO NOT USE IN FINAL

    # Dummy user, this has to be a proper db check
    if username == "admin" and password == "admin":
        return {
            "id": 1,
            "username": "admin"
        }

# Check in DB which bearer the client claims to be
def get_user(id):
    # BOILERPLATE, DO NOT USE IN FINAL

    # Dummy user, this has to be a proper db check
    return {
        "id": 1,
        "username": "admin"
    }


