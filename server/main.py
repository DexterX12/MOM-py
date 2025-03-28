from flask import Flask, request, jsonify, Response
import threading
from collections import defaultdict
from message import Message
import jwt
import json
from DBscript import auth, get_user
app = Flask(__name__)

queues = defaultdict(list) #queues in exchanges dictionary 
exchanges = {} #dictionary that stores messages in queues with an associated exchange and routing_key

topics = defaultdict(list) #topics in topics_exchange dictionary 
topics_exchange = {} #dictionary that stores messages in topics with an associated exchange and routing_key
user_queues = defaultdict(list)

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
    print(data)
    username = data.get("user")
    pw = data.get("pass")
    user = auth(username, pw)

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
            history = []
            history.append(user)
            
        except jwt.exceptions.InvalidTokenError:
            return jsonify({"error": "Invalid token provided"}), 401
        

    
    if operation not in ["pull", "push", "subscribe"]:
        return jsonify({"error": "Invalid operation :("}), 400

    if operation in ["pull", "push", "subscribe"]:
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
            return pull(message, history)
        elif operation == "push" and msg_type=="t":
            return push_to_topic(message)
        elif operation == "pull" and msg_type=="t":
            return pull_topic(message, history)
        elif operation=="subscribe":
            return subscribe(msg_type, history,message)
    
        
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
                    "users_subscribed": [],
                    "queue": [message]
                })

        return jsonify({
            "status": "Message pushed",
            "queue_name": queue_name,
            "exchange": exchange,
            "routing_key": routing_key
        }), 200
    
#client requests a message in the queue
def pull(message, history):
    print("HOLAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    exchange = message.header["exchange"] 
    routing_key = message.header["routing_key"]

    if not exchange or not routing_key:
        return jsonify({"error": "Missing exchange or routing_key"}), 400
    
    else:
        queue_name = exchange+"_"+routing_key

        with lock:
            if exchange in exchanges:
                for queue in exchanges[exchange]:
                    print("hola",queue["users_subscribed"])
                    if queue["routing_key"] == routing_key and queue["queue"] and (history[0]["id"] in queue["users_subscribed"]):
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
# def check_user(username, password):
#     # BOILERPLATE, DO NOT USE IN FINAL

#     # Dummy user, this has to be a proper db check
#     if username == "admin" and password == "admin":
#         return {
#             "id": 1,
#             "username": "admin"
#         }

# # Check in DB which bearer the client claims to be
# def get_user(id):
#     # BOILERPLATE, DO NOT USE IN FINAL

#     # Dummy user, this has to be a proper db check
#     return {
#         "id": 1,
#         "username": "admin"
#     }

#-------------------------TOPICS--------------------------

def push_to_topic(message):
    exchange = message.header["exchange"] 
    routing_key = message.header["routing_key"]

    if not exchange or not routing_key:
        return jsonify({"error": "Missing exchange or routing_key"}), 400

    queue_name = f"{exchange}_{routing_key}"
    
    with lock:
        if exchange not in topics_exchange:
            topics_exchange[exchange] = []

        for topic in topics_exchange[exchange]:
            if topic["routing_key"] == routing_key:
                topic["topics"].append(message)

                for user in topic["users_subscribed"]:
                    user_queues[user].append(message)
                
                break
        else:
            topics_exchange[exchange].append({
                "routing_key": routing_key,
                "queue_name": queue_name,
                "topics": [message],
                "users_subscribed": []
            })
    print(topics_exchange)

    return jsonify({
        "status": "Message pushed",
        "queue_name": queue_name,
        "exchange": exchange,
        "routing_key": routing_key
    }), 200



def pull_topic(message, history):
    user_id = history[0]["id"] 
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400

    with lock:
        if user_id in user_queues and user_queues[user_id]:
            msg = user_queues[user_id].pop(0)  
            return jsonify({
                "status": "Message delivered",
                "message": {
                    "message_date": msg.header["message_date"],  
                    "routing_key": msg.header["routing_key"],  
                    "exchange": msg.header["exchange"], 
                    "body": msg.body
                }
            }), 200

    return jsonify({"error": "No messages available"}), 404


def subscribe(msg_type, history, message):
    user_id = history[0]["id"]
    exchange = message.header["exchange"] 
    routing_key = message.header["routing_key"]
    

    if not exchange or not routing_key:
        return jsonify({"error": "Missing exchange or routing_key"}), 400

    queue_name = f"{exchange}_{routing_key}"

    if msg_type == "t":
        with lock:
            if exchange not in topics_exchange or not any(topic["routing_key"] == routing_key for topic in topics_exchange[exchange]):
                return jsonify({"error": "Topic does not exist"}), 400 
            
            for topic in topics_exchange[exchange]:
                if topic["routing_key"] == routing_key:
                    if user_id not in topic["users_subscribed"]:
                        topic["users_subscribed"].append(user_id)
                        user_queues[user_id] = topic["topics"].copy()
                    break

        return jsonify({
            "status": "Subscribed to topic",
            "user_id": user_id,
            "queue_name": queue_name,
            "exchange": exchange,
            "routing_key": routing_key
        }), 200
    else:
        with lock:
            if exchange not in exchanges or not any(q["routing_key"] == routing_key for q in exchanges[exchange]):
                return jsonify({"error": "Queue does not exist"}), 400 
            
            for exchange in exchanges[exchange]:
                if exchange["routing_key"] == routing_key:
                    if user_id not in exchange["users_subscribed"]:
                        exchange["users_subscribed"].append(user_id)
                    break

        return jsonify({
            "status": "Subscribed to queue",
            "user_id": user_id,
            "queue_name": queue_name
        }), 200
