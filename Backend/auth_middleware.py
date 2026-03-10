from functools import wraps
from flask import request, jsonify, g
from firebase_admin import auth

def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"status": "error", "message": "Missing or invalid Authorization header"}), 401

        id_token = auth_header.split(" ", 1)[1].strip()
        if not id_token:
            return jsonify({"status": "error", "message": "Missing token"}), 401

        try:
            g.user = auth.verify_id_token(id_token)
        except Exception as e:
            return jsonify({"status": "error", "message": "Invalid or expired token", "debug": str(e)}), 401

        return fn(*args, **kwargs)

    return wrapper