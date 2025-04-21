from flask import Flask, request, jsonify, Response
from DBscript import auth, get_user
import jwt

app = Flask(__name__)
app.secret_key = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

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
    auth_token = jwt.encode({"user": user["username"]}, app.secret_key, algorithm="HS256")
    return jsonify({"token": auth_token}), 200

@app.route("/validate", methods=["POST"])
def check_token():
    auth = request.headers.get("Authorization")

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
            jwt.decode(token, app.secret_key, algorithms="HS256")
            return jsonify({"success": "si"}), 200
            
        except jwt.exceptions.InvalidTokenError:
            return jsonify({"error": "Invalid token provided"}), 401