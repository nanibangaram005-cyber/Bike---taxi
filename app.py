# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# In-memory storage (for prototype/testing)
USERS = []          # {id, name, phone, is_driver}
RIDES = []          # {id, rider_id, driver_id, origin, destination, status, fare, created_at}
DRIVER_LOC = {}     # driver_id -> {"lat":..., "lng":..., "updated_at":...}

def new_user_id():
    return len(USERS) + 1

def new_ride_id():
    return len(RIDES) + 1

# ---------- Endpoints ----------

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "pong", "time": datetime.utcnow().isoformat()})

@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    name = data.get("name")
    phone = data.get("phone")
    is_driver = bool(data.get("is_driver", False))
    if not name:
        return jsonify({"error": "name required"}), 400
    uid = new_user_id()
    USERS.append({"id": uid, "name": name, "phone": phone, "is_driver": is_driver})
    return jsonify({"message": "registered", "user_id": uid}), 201

@app.route("/users", methods=["GET"])
def list_users():
    return jsonify(USERS)

@app.route("/request_ride", methods=["POST"])
def request_ride():
    data = request.json or {}
    rider_id = data.get("rider_id")
    origin = data.get("origin")        # {"lat":..,"lng":..}
    destination = data.get("destination")
    if not (rider_id and origin and destination):
        return jsonify({"error":"rider_id, origin and destination required"}), 400
    ride_id = new_ride_id()
    ride = {
        "id": ride_id,
        "rider_id": rider_id,
        "driver_id": None,
        "origin": origin,
        "destination": destination,
        "status": "waiting",   # waiting -> accepted -> started -> completed -> cancelled
        "fare": None,
        "created_at": datetime.utcnow().isoformat()
    }
    RIDES.append(ride)
    return jsonify({"message":"ride_requested", "ride": ride}), 201

@app.route("/available_rides", methods=["GET"])
def available_rides():
    return jsonify([r for r in RIDES if r["status"] == "waiting"])

@app.route("/accept_ride", methods=["POST"])
def accept_ride():
    data = request.json or {}
    driver_id = data.get("driver_id")
    ride_id = data.get("ride_id")
    if not (driver_id and ride_id):
        return jsonify({"error":"driver_id and ride_id required"}), 400
    for r in RIDES:
        if r["id"] == ride_id:
            if r["status"] != "waiting":
                return jsonify({"error":"ride not available"}), 400
            r["driver_id"] = driver_id
            r["status"] = "accepted"
            return jsonify({"message":"ride_accepted", "ride": r}), 200
    return jsonify({"error":"ride not found"}), 404

@app.route("/start_ride", methods=["POST"])
def start_ride():
    data = request.json or {}
    ride_id = data.get("ride_id")
    for r in RIDES:
        if r["id"] == ride_id:
            r["status"] = "started"
            return jsonify({"message":"ride_started","ride":r}), 200
    return jsonify({"error":"ride not found"}), 404

@app.route("/complete_ride", methods=["POST"])
def complete_ride():
    data = request.json or {}
    ride_id = data.get("ride_id")
    for r in RIDES:
        if r["id"] == ride_id:
            r["status"] = "completed"
            return jsonify({"message":"ride_completed","ride":r}), 200
    return jsonify({"error":"ride not found"}), 404

@app.route("/ride_history/<int:user_id>", methods=["GET"])
def ride_history(user_id):
    as_rider = [r for r in RIDES if r["rider_id"] == user_id]
    as_driver = [r for r in RIDES if r.get("driver_id") == user_id]
    return jsonify({"as_rider": as_rider, "as_driver": as_driver})

# Driver location endpoints
@app.route("/update_location", methods=["POST"])
def update_location():
    data = request.json or {}
    driver_id = data.get("driver_id")
    lat = data.get("lat")
    lng = data.get("lng")
    if not (driver_id and lat is not None and lng is not None):
        return jsonify({"error":"driver_id, lat, lng required"}), 400
    DRIVER_LOC[int(driver_id)] = {"lat": float(lat), "lng": float(lng), "updated_at": datetime.utcnow().isoformat()}
    return jsonify({"message":"location_updated"}), 200

@app.route("/get_driver_location/<int:ride_id>", methods=["GET"])
def get_driver_location(ride_id):
    for r in RIDES:
        if r["id"] == ride_id and r.get("driver_id"):
            loc = DRIVER_LOC.get(int(r["driver_id"]))
            if loc:
                return jsonify(loc)
            return jsonify({"message":"no_location_yet"}), 404
    return jsonify({"message":"ride_not_found_or_no_driver"}), 404

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
