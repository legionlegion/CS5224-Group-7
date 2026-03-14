from flask import Flask, request, jsonify, g
from flask_cors import CORS
from datetime import datetime
import math

# Firebase Auth
import firebase_admin
from firebase_admin import credentials
from auth_middleware import require_auth

# Logging and env
import logging
import os
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

if not firebase_admin._apps:
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "secrets/serviceAccountKey.json"
    
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        import json
        with open(cred_path) as f:
            data = json.load(f)
            os.environ["GOOGLE_CLOUD_PROJECT"] = data.get("project_id")
            print(f"JSON: Pulled project_id from serviceAccountKey: {os.environ['GOOGLE_CLOUD_PROJECT']}")

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {'projectId': os.environ.get("GOOGLE_CLOUD_PROJECT")})
    print("Firebase initialized successfully.")

'''
if not firebase_admin._apps:
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path:
        logger.info(f"Initializing Firebase with credentials from: {cred_path}")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        logger.info("GOOGLE_APPLICATION_CREDENTIALS not set. Initializing Firebase with default credentials.")
        firebase_admin.initialize_app()
'''

# DELETE UPON INTEGRATION
BINS_DATABASE = [
    {"id": "bin_sg_882", "address": "123 Orchard Rd, Singapore", "lat": 1.3015, "lng": 103.8378},
    {"id": "bin_sg_104", "address": "Somerset MRT, Exit B", "lat": 1.3002, "lng": 103.8390},
    {"id": "bin_sg_999", "address": "Tampines Hub", "lat": 1.3525, "lng": 103.9446},
]

# DELETE UPON INTEGRATION
USERS_DB = [
    {"username": "EcoWarrior88", "points": 1250, "district": "Tampines"},
    {"username": "GreenMachine", "points": 1100, "district": "Tampines"},
    {"username": "RecycleQueen", "points": 950, "district": "Orchard"},
    {"username": "NatureLover", "points": 800, "district": "Tampines"},
    {"username": "SolarPower", "points": 750, "district": "Orchard"},
]

# DELETE UPON INTEGRATION
USER_TRANSACTIONS = "GET_user_stats.json"


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

# TO EDIT WHEN INTEGRATING WITH DATABASE
def get_all_user_transactions(userId):
    '''
    Returns all user transactions encompassed in a JSON file
    '''
    return USER_TRANSACTIONS


'''
VERIFY USER RECYCLING SUBMISSION
'''
@app.route('/api/v1/verify-activity', methods=['POST'])
@require_auth
def verify_activity():
    try:
        # get authenticated user
        user_id = g.user['uid']
        
        # form fields
        latitude = request.form.get('Latitude', type=float)
        longitude = request.form.get('Longitude', type=float)
        
        # image file
        image_file = request.files.get('Image')

        # check if all fields present
        if not all([latitude, longitude, image_file]):
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
@require_auth
def get_nearby_bins():
    try:
        # get authenticated user
        user_id = g.user['uid']
        
        # parameters
        user_lat = request.args.get('lat', type=float)
        user_lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', type=float)

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
@require_auth
def get_leaderboard():
    try:
        # get authenticated user
        user_id = g.user['uid']
        
        # parameters
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
@app.route('/api/v1/users/stats', methods=['GET'])
@require_auth
def get_user_stats():
    try:
        # get authenticated user
        user_id = g.user['uid']
        
        # REPLACE WITH USER STATISTICS FROM DATABASE
        username, totalPoints, level, totalSubmissions, lastRecycled = get_user_db_stats(user_id)
        user_data = {
            "userId": user_id,
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
    

'''
GET ALL USER TRANSACTIONS
'''
@app.route('/api/v1/users/transactions', methods=['GET'])
@require_auth
def get_user_transactions():
    try:
        # get authenticated user
        user_id = g.user['uid']
        
        transactions = get_all_user_transactions(user_id) # transactions should be a JSON file

        return transactions, 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


'''
TEST AUTH ENDPOINT
'''
@app.route('/api/v1/test-auth', methods=['GET'])
@require_auth
def test_auth():
    try:
        user_info = {
            "status": "success",
            "message": "Authentication successful",
            "user": {
                "uid": g.user.get('uid'),
                "email": g.user.get('email'),
                "email_verified": g.user.get('email_verified', False)
            },
            "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        logger.info(f"User id: {g.user.get('uid')}")
        return jsonify(user_info), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8000)

