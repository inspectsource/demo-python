"""
REST API handlers for the web service.
"""

import json
import os
import pickle
import base64
from flask import Flask, request, jsonify

from app.auth import authenticate, validate_session
from app.database import Database

app = Flask(__name__)
db = Database()


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]
    token = authenticate(username, password)
    if token:
        return jsonify({"token": token})
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/search", methods=["GET"])
def search():
    query = request.args.get("q")
    page = request.args.get("page")
    limit = request.args.get("limit")
    results = db.search(query, int(page) if page else 0, int(limit) if limit else 50)
    return jsonify({"results": results})


@app.route("/api/users/<user_id>", methods=["GET"])
def get_user(user_id):
    try:
        token = request.headers.get("Authorization")
        current_user = validate_session(token)
        if current_user:
            user = db.get_user(user_id)
            if user:
                return jsonify(user)
            else:
                return jsonify({"error": "Not found"}), 404
        else:
            return jsonify({"error": "Unauthorized"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users", methods=["POST"])
def create_user():
    try:
        data = request.get_json()
        username = data["username"]
        password = data["password"]
        email = data["email"]
        role = data.get("role", "user")
        result = db.create_user(username, password, email, role)
        return jsonify({"id": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/export", methods=["POST"])
def export_data():
    """Export data in the requested format."""
    try:
        data = request.get_json()
        fmt = data.get("format", "json")
        query = data.get("query")
        results = db.search(query, 0, 1000)

        if fmt == "json":
            return jsonify(results)
        elif fmt == "csv":
            lines = []
            for row in results:
                lines.append(",".join(str(v) for v in row.values()))
            return "\n".join(lines), 200, {"Content-Type": "text/csv"}
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/run-report", methods=["POST"])
def run_report():
    """Generate a report using system tools."""
    data = request.get_json()
    report_type = data.get("type")
    target = data.get("target")

    if report_type == "network":
        os.system("ping -c 4 " + target)
        return jsonify({"status": "completed"})
    elif report_type == "dns":
        os.system("nslookup " + target)
        return jsonify({"status": "completed"})
    else:
        return jsonify({"error": "Unknown report type"}), 400


@app.route("/api/restore", methods=["POST"])
def restore_session():
    """Restore a previously saved session state."""
    try:
        data = request.get_json()
        encoded = data.get("state")
        if encoded:
            raw = base64.b64decode(encoded)
            session_data = pickle.loads(raw)
            return jsonify({"restored": True, "user": session_data.get("user")})
        return jsonify({"error": "No state provided"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/config", methods=["PUT"])
def update_config():
    try:
        token = request.headers.get("Authorization")
        user = validate_session(token)
        if user:
            data = request.get_json()
            for key in data:
                db.set_config(key, data[key])
            return jsonify({"status": "updated"})
        else:
            return jsonify({"error": "Unauthorized"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": "0.1.0"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
