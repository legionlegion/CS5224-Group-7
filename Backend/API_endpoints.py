from flask import Flask, request, jsonify, g
from flask_cors import CORS
from datetime import datetime
import math

# Firebase Auth
import firebase_admin
from firebase_admin import credentials, firestore
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
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "serviceAccountKey.json"
    
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        import json
        with open(cred_path) as f:
            data = json.load(f)
            os.environ["GOOGLE_CLOUD_PROJECT"] = data.get("project_id")
            print(f"JSON: Pulled project_id from serviceAccountKey: {os.environ['GOOGLE_CLOUD_PROJECT']}")

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {'projectId': os.environ.get("GOOGLE_CLOUD_PROJECT")})
    print("Firebase initialized successfully.")

# Initialize Firestore
db = firestore.client()

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
def get_model_response(user_id, image_file):
    # For now, return mock ML model response
    # TODO: Integrate with actual computer vision model
     # default values
    detected_items = []
    cv_confidence_score = 0.0
    
    # REPLACE WITH CODE TO CALL MODEL AND GET RESPONSE
    detected_items = ["PET Bottle", "Cardboard Box"]    
    cv_confidence_score = 0.94
    
    is_recyclable = False
    # adjust threshold as needed based on model performance
    if cv_confidence_score >= 0.8:
        is_recyclable = True
    
    result = [detected_items, cv_confidence_score, is_recyclable]
    return result

# ===== FIRESTORE DATABASE FUNCTIONS =====

def get_all_bins():
    """Fetch all active recycling bins from Firestore."""
    try:
        bins_ref = db.collection('recycling_bins').where('is_active', '==', True)
        docs = bins_ref.stream()
        
        bins = []
        for doc in docs:
            data = doc.to_dict()
            bins.append({
                "id": doc.id,
                "address": {
                    "block": data.get('address', {}).get('block', ''),
                    "street": data.get('address', {}).get('street', ''),
                    "postal_code": data.get('address', {}).get('postal_code', '')
                },
                "lat": data.get('location', {}).get('coordinates', [0, 0])[1],
                "lng": data.get('location', {}).get('coordinates', [0, 0])[0],
                "district_id": data.get('district_id', ''),
                "description": data.get('description', '')
            })
        
        logger.info(f"Retrieved {len(bins)} active bins from Firestore")
        return bins
    except Exception as e:
        logger.error(f"Error fetching bins: {str(e)}")
        return []


def get_user_district(user_id):
    """Fetch user's district from Firestore."""
    try:
        user_doc = db.collection('users').document(user_id).get()
        
        if user_doc.exists:
            return user_doc.get('district_id')
        else:
            logger.warning(f"User {user_id} not found in Firestore")
            return None
    except Exception as e:
        logger.error(f"Error fetching user district: {str(e)}")
        return None


def get_all_users():
    """Fetch all users ordered by points (descending) from Firestore."""
    try:
        users_ref = db.collection('users').order_by('points', direction=firestore.Query.DESCENDING)
        docs = users_ref.stream()
        
        users = []
        for doc in docs:
            data = doc.to_dict()
            users.append({
                "username": data.get('username', ''),
                "points": data.get('points', 0),
                "district": data.get('district_id', ''),
                "uid": doc.id
            })
        
        logger.info(f"Retrieved {len(users)} users from Firestore")
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return []


def get_user_rank(user_id):
    """Calculate user's global rank based on points."""
    try:
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            logger.warning(f"User {user_id} not found")
            return -1
        
        user_points = user_doc.get('points', 0)
        
        # Count users with more points
        higher_points = db.collection('users').where('points', '>', user_points).count().get()[0][0].value
        rank = higher_points + 1
        
        return rank
    except Exception as e:
        logger.error(f"Error calculating user rank: {str(e)}")
        return -1


def get_user_db_stats(user_id):
    """Fetch user statistics from Firestore."""
    try:
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            logger.warning(f"User {user_id} not found")
            return None, 0, "Bronze", 0, None
        
        user_data = user_doc.to_dict()
        username = user_data.get('username', '')
        total_points = user_data.get('points', 0)
        
        # Determine level based on points (customizable)
        if total_points >= 1000:
            level = "Platinum"
        elif total_points >= 500:
            level = "Gold"
        elif total_points >= 200:
            level = "Silver"
        else:
            level = "Bronze"
        
        # Count total submissions (transactions where is_counted=true)
        transactions = db.collection('transactions').where('user_id', '==', user_id).where('is_counted', '==', True).stream()
        total_submissions = len(list(transactions))
        
        # Get last recycled timestamp
        last_txn = db.collection('transactions').where('user_id', '==', user_id).order_by('submitted_at', direction=firestore.Query.DESCENDING).limit(1).stream()
        last_recycled = None
        for txn in last_txn:
            last_recycled = txn.get('submitted_at')
            break
        
        logger.info(f"User {user_id} stats: {username}, {total_points} points, {total_submissions} submissions")
        return username, total_points, level, total_submissions, last_recycled
    except Exception as e:
        logger.error(f"Error fetching user stats: {str(e)}")
        return None, 0, "Bronze", 0, None


def save_transaction(user_id, district_id, gps_location, nearest_bin_id, cv_result, location_check_passed, points_awarded, image_path=None):
    """Save a new transaction (recycling submission) to Firestore."""
    try:
        transaction_data = {
            "user_id": user_id,
            "district_id": district_id,
            "submitted_at": datetime.utcnow(),
            "gps_location": {
                "type": "Point",
                "coordinates": [gps_location[1], gps_location[0]]  # [lng, lat]
            },
            "nearest_bin_id": nearest_bin_id,
            "cv_result": cv_result,
            "location_check_passed": location_check_passed,
            "is_counted": cv_result.get('is_recyclable', False) and location_check_passed,
            "points_awarded": points_awarded if (cv_result.get('is_recyclable', False) and location_check_passed) else 0,
            "image_path": image_path
        }
        
        docref = db.collection('transactions').document()
        docref.set(transaction_data)
        transaction_id = docref.id
        
        # Update user points if transaction is counted
        if transaction_data['is_counted']:
            user_ref = db.collection('users').document(user_id)
            user_ref.update({
                'points': firestore.Increment(points_awarded)
            })
            logger.info(f"User {user_id} awarded {points_awarded} points")
        
        logger.info(f"Transaction {transaction_id} saved successfully")
        return transaction_id
    except Exception as e:
        logger.error(f"Error saving transaction: {str(e)}")
        return None


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

        # Get CV model response
        cv_result = get_model_response(user_id, latitude, longitude, image_file)
        
        # Find nearest bin
        all_bins = get_all_bins()
        nearest_bin = None
        min_distance = float('inf')
        
        for bin_info in all_bins:
            dist = haversine_distance(latitude, longitude, bin_info['lat'], bin_info['lng'])
            if dist < min_distance:
                min_distance = dist
                nearest_bin = bin_info
        
        # Location check: within 50 meters of a bin
        location_check_passed = min_distance <= 50 if nearest_bin else False
        
        # Award points
        points_earned = 50 if (cv_result['is_recyclable'] and location_check_passed) else 0
        
        # Get user district
        user_district = get_user_district(user_id)
        
        # Save transaction to Firestore
        transaction_id = save_transaction(
            user_id=user_id,
            district_id=user_district,
            gps_location=(latitude, longitude),
            nearest_bin_id=nearest_bin['id'] if nearest_bin else None,
            cv_result=cv_result,
            location_check_passed=location_check_passed,
            points_awarded=points_earned
        )
        
        # Get updated user stats
        username, total_points, level, total_submissions, last_recycled = get_user_db_stats(user_id)
        
        # Get user rank
        user_rank = get_user_rank(user_id)

        # Respond based on verification results
        if cv_result['is_recyclable'] and location_check_passed:
            response_data = {
                "status": "success",
                "transaction_id": transaction_id,
                "user_id": user_id,
                "verification_details": {
                    "location_check_passed": location_check_passed,
                    "distance_metres": min_distance,
                    "cv_confidence_score": cv_result['confidence'],
                    "detected_items": cv_result['detected_items'],
                    "nearest_bin_distance": min_distance
                },
                "rewards": {
                    "points_earned": points_earned,
                    "new_total_balance": total_points
                },
                "community_impact": {
                    "district": user_district,
                    "user_rank": user_rank
                },
                "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            }
        else:
            response_data = {
                "status": "fail",
                "transaction_id": transaction_id,
                "user_id": user_id,
                "verification_details": {
                    "location_check_passed": location_check_passed,
                    "distance_metres": min_distance,
                    "cv_confidence_score": cv_result['confidence'],
                    "detected_items": cv_result['detected_items'],
                    "reason": "Not recyclable or too far from bin" if location_check_passed else "Location too far from recycling bin"
                },
                "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            }

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error in verify_activity: {str(e)}")
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
            "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        logger.info(f"User id: {g.user.get('uid')}")
        return jsonify(user_info), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8000)

