from flask import Flask, request, jsonify
from datetime import datetime
import math
import firebase_admin
from firebase_admin import credentials, auth

app = Flask(__name__)
default_app = firebase_admin.initialize_app()

# REPLACE WITH CODE TO SEARCH BIN IN DATABASE
BINS_DATABASE = [
    {"id": "bin_sg_882", "address": "123 Orchard Rd, Singapore", "lat": 1.3015, "lng": 103.8378},
    {"id": "bin_sg_104", "address": "Somerset MRT, Exit B", "lat": 1.3002, "lng": 103.8390},
    {"id": "bin_sg_999", "address": "Tampines Hub", "lat": 1.3525, "lng": 103.9446},
]

# REPLACE WITH CODE TO SEARCH USER IN DATABASE
USERS_DB = [
    {"username": "EcoWarrior88", "points": 1250, "district": "Tampines"},
    {"username": "GreenMachine", "points": 1100, "district": "Tampines"},
    {"username": "RecycleQueen", "points": 950, "district": "Orchard"},
    {"username": "NatureLover", "points": 800, "district": "Tampines"},
    {"username": "SolarPower", "points": 750, "district": "Orchard"},
]


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate haversine distance in meters."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    dist = 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return dist

# TO EDIT WHEN INTEGRATING WITH MODEL
def get_model_response(user_id, latitude, longitude, image_file):
    # default values
    detected_items = []
    gps_match = False
    transaction_id = ""
    distance_metres = 0.0
    cv_confidence_score = 0.0
    points_earned = 0
    bonus_applied = ""
    new_total_balance = 0
    district = ""
    district_rank = -1
    
    # REPLACE WITH CODE TO CALL MODEL AND GET RESPONSE
    detected_items = ["PET Bottle", "Cardboard Box"]
    gps_match = True
    transaction_id = "cdcc2ef"
    distance_metres = 2.4
    cv_confidence_score = 0.94
    points_earned = 50
    bonus_applied = "First-of-the-Week"
    new_total_balance = 1250
    district = "Tampines"
    district_rank = 4

    result = [detected_items, gps_match, transaction_id, distance_metres, cv_confidence_score, 
              points_earned, bonus_applied, new_total_balance, district, district_rank]
    return result

# TO EDIT WHEN INTEGRATING WITH DATABASE
def get_all_bins():
    return BINS_DATABASE

# TO EDIT WHEN INTEGRATING WITH DATABASE
def get_user_district(user_id):
    user_district = "Tampines"
    return user_district

# TO EDIT WHEN INTEGRATING WITH DATABASE
def get_all_users():
    return USERS_DB

# TO EDIT WHEN INTEGRATING WITH DATABASE
def get_user_rank(user_id):
    user_rank = 27
    return user_rank

# TO EDIT WHEN INTEGRATING WITH DATABASE
def get_user_db_stats(userId):
    # default values
    username = ""
    totalPoints = 0
    level = 0
    totalSubmissions = 0
    lastRecycled = 0

    # REPLACE WITH CODE TO CALL DATABASE AND GET RESPONSE
    username = "ZeroWasteHero"
    totalPoints = 450
    level = "Silver"
    totalSubmissions = 24
    lastRecycled = "2026-02-25T14:30:00Z"

    return username, totalPoints, level, totalSubmissions, lastRecycled


'''
VERIFY USER RECYCLING SUBMISSION
'''
@app.route('/api/v1/verify-activity', methods=['POST'])
def verify_activity():
    try:
        # form fields
        user_id = request.form.get('UserId')
        latitude = request.form.get('Latitude', type=float)
        longitude = request.form.get('Longitude', type=float)
        
        # image file
        image_file = request.files.get('Image')

        # check if all fields present
        if not all([user_id, latitude, longitude, image_file]):
            return jsonify({"error": "Missing required fields or file"}), 400

        # get model response
        detected_items, gps_match, transaction_id, distance_metres, cv_confidence_score, \
            points_earned, bonus_applied, new_total_balance, district, \
                district_rank = get_model_response(user_id, latitude, longitude, image_file)

        # respond based on model response
        if detected_items and gps_match:
            response_data = {
                "status": "success",
                "transaction_id": transaction_id,
                "user_id": user_id,
                "verification_details": {
                    "gps_match": gps_match,
                    "distance_metres": distance_metres,
                    "cv_confidence_score": cv_confidence_score,
                    "detected_items": detected_items
                },
                "rewards": {
                    "points_earned": points_earned,
                    "bonus_applied": bonus_applied,
                    "new_total_balance": new_total_balance
                },
                "community_impact": {
                    "district": district,
                    "district_rank": district_rank
                },
                "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            }
        else:
            response_data = {
            "status": "fail",
            "transaction_id": transaction_id,
            "user_id": user_id,
            "verification_details": {
                "gps_match": gps_match,
                "distance_metres": distance_metres,
                "cv_confidence_score": cv_confidence_score,
                "detected_items": detected_items
            },
            "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


'''
GET NEARBY BINS
'''
@app.route('/api/v1/nearby-bins', methods=['GET'])
def get_nearby_bins():
    try:
        # parameters
        user_lat = request.args.get('Latitude', type=float)
        user_lng = request.args.get('Longitude', type=float)
        radius = request.args.get('Radius', type=float)

        if user_lat is None or user_lng is None or radius is None:
            return jsonify({"status": "error", "message": "Missing Latitude, Longitude, or Radius"}), 400

        nearby = []
        all_bins = get_all_bins()
        for bin in all_bins:
            dist = haversine_distance(user_lat, user_lng, bin['lat'], bin['lng'])
            if dist <= radius:
                nearby.append({
                    "id": bin['id'],
                    "address": bin['address'],
                    "coordinates": {"lat": bin['lat'], "lng": bin['lng']},
                    "distance_meters": dist
                })
        if nearby:
            nearby.sort(key=lambda x: x['distance_meters'])
            response_data = {
                "status": "success",
                "count": len(nearby),
                "data": nearby
            }
            return jsonify(response_data), 200
        else:
            response_data = {
                "status": "fail",
                "count": 0,
                "data": []
            }
            return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


'''
GET LEADERBOARD
'''
@app.route('/api/v1/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        # parameters
        user_id = request.args.get('UserId')
        scope = request.args.get('Scope', 'global').lower() # Default scope global
        limit = request.args.get('Limit', default=10, type=int)

        user_district = get_user_district(user_id)
        user_rank = get_user_rank(user_id)
        all_users = get_all_users()
        
        if scope == "local":
            filtered_list = [u for u in all_users if u['district'] == user_district]
        else:
            filtered_list = all_users

        sorted_users = sorted(filtered_list, key=lambda x: x['points'], reverse=True)

        leaderboard_data = []
        for index, user in enumerate(sorted_users[:limit]):
            leaderboard_data.append({
                "rank": index + 1,
                "username": user['username'],
                "points": user['points']
            })

        response = {
            "scope": scope,
            "user_current_rank": user_rank, 
            "leaderboard": leaderboard_data
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


'''
GET USER STATS
'''
@app.route('/api/v1/users/<userId>/stats', methods=['GET'])
def get_user_stats(userId):
    try:
        # REPLACE WITH USER STATISTICS FROM DATABASE
        username, totalPoints, level, totalSubmissions, lastRecycled = get_user_db_stats(userId)
        user_data = {
            "userId": userId,
            "username": username,
            "totalPoints": totalPoints,
            "level": level,
            "stats": {
                "totalSubmissions": totalSubmissions,
                "lastRecycled": lastRecycled
            }
        }

        return jsonify(user_data), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True, port=5000)

