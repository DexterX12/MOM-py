from flask import Flask, request, jsonify, Response
import threading
from collections import defaultdict
from message import Message
import jwt
import json
app = Flask(__name__)

queues = defaultdict(list) #queues in exchanges dictionary 
exchanges = {} #dictionary that stores messages in queues with an associated exchange and routing_key

#app.config.from_prefixed_env() # ENVIROMENT VARIABLE FLASK_SECRET_KEY
app.secret_key = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
lock = threading.Lock()

@app.route("/")
def welcoming():
    return "<h1>MOM test</h1>"


#-------------------------Log in--------------------------

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

#-------------------------Post--------------------------

@app.route("/", methods=["POST"])
def post():
    data = request.json
    msg_type = data.get("type")
    operation = data.get("operation")
    auth = request.headers.get("Authorization")
    user = None

    if not auth:
        response = Response()
        response.status_code = 401
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
        
    if operation == "subscribe":

        pass

    
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
        if operation == "push" and msg_type=="q":
            return bind_queue(message)
        elif operation == "pull" and msg_type=="q":
            return pull(message)
        elif operation == "push" and msg_type=="t":
            return push_to_topic(message)
        elif operation == "pull" and msg_type=="t":
            return pull_topic(message)
    
        
#-------------------------Queues--------------------------

#creation of the queue - exchange, routing key (productor)  
def bind_queue(message):
    exchange = message.header["exchange"] 
    routing_key = message.header["routing_key"]

    if not exchange or not routing_key:
        return jsonify({"error": "Missing exchange or routing_key"}), 400
    
    else:
        queue_name = exchange+"_"+routing_key
        with lock:
            if exchange not in exchanges:
                exchanges[exchange] = []

            for queue in exchanges[exchange]:
                if queue["routing_key"] == routing_key:
                    queue["queue"].append(message)
                    break
            else:
                queue_name = f"{exchange}_{routing_key}"
                exchanges[exchange].append({
                    "routing_key": routing_key,
                    "queue_name": queue_name,
                    "queue": [message]
                })

        return jsonify({
            "status": "Message pushed",
            "queue_name": queue_name,
            "exchange": exchange,
            "routing_key": routing_key
        }), 200
    
#client requests a message in the queue
def pull(message):
    exchange = message.header["exchange"] 
    routing_key = message.header["routing_key"]

    if not exchange or not routing_key:
        return jsonify({"error": "Missing exchange or routing_key"}), 400
    
    else:
        queue_name = exchange+"_"+routing_key

        with lock:
            if exchange in exchanges:
                for queue in exchanges[exchange]:
                    if queue["routing_key"] == routing_key and queue["queue"]:
                        message = queue["queue"].pop(0)
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


#-------------------------USER--------------------------

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

#-------------------------TOPICS--------------------------

def push_to_topic(message):
    pass


def pull_topic(message):
    pass