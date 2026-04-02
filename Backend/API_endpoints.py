from flask import Flask, request, jsonify, g
from flask_cors import CORS
from datetime import datetime
import math
import requests

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
CORS(app, origins=["http://localhost:3000", "https://recycling-frontend-dev-306363185631.us-west2.run.app"])

DEFAULT_BIN_DISTANCE_THRESHOLD_METERS = 50.0

#
def get_bin_distance_threshold_meters():
    """Read verify-activity distance threshold from env with safe fallback."""
    raw_value = os.getenv("BIN_DISTANCE_THRESHOLD_METERS", str(DEFAULT_BIN_DISTANCE_THRESHOLD_METERS))
    try:
        threshold = float(raw_value)
        if threshold < 0:
            raise ValueError("Distance threshold must be non-negative")
        return threshold
    except (TypeError, ValueError):
        logger.warning(
            "Invalid BIN_DISTANCE_THRESHOLD_METERS='%s'. Falling back to %.1f",
            raw_value,
            DEFAULT_BIN_DISTANCE_THRESHOLD_METERS,
        )
        return DEFAULT_BIN_DISTANCE_THRESHOLD_METERS

if not firebase_admin._apps:
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "serviceAccountKey.json"
    
    # Check if credential file exists
    if os.path.exists(cred_path):
        if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
            import json
            try:
                with open(cred_path) as f:
                    data = json.load(f)
                    os.environ["GOOGLE_CLOUD_PROJECT"] = data.get("project_id")
                    logger.info("Project ID loaded from credentials file")
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load credentials file: {e}")
                raise

        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {'projectId': os.environ.get("GOOGLE_CLOUD_PROJECT")})
            logger.info("Firebase initialized with credentials file")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase with credentials: {e}")
            raise
    else:
        # Fallback to Application Default Credentials (ADC) / emulator
        logger.info("Credentials file not found. Using Application Default Credentials")
        try:
            firebase_admin.initialize_app()
            logger.info("Firebase initialized with default credentials")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase with default credentials: {e}")
            raise

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

    # Call FastAPI ML server that returns a list of recyclable items
    ml_predict_url = os.getenv("ML_PREDICT_URL", "http://127.0.0.1:5001/predict")
    detected_items = []
    try:
        files = {"file": image_file.stream}
        response = requests.post(ml_predict_url, files=files, timeout=10)
        response.raise_for_status()
        ml_result = response.json()
        if isinstance(ml_result, list):
            detected_items = ml_result
        else:
            logger.warning(f"Unexpected ML response format: {ml_result}")
    except Exception as e:
        logger.error(f"ML server call failed: {e}")
    
    is_recyclable = any(item != "Bluebins" for item in detected_items)

    bin_detected = True if "Bluebins" in detected_items else False

    return {
        "detected_items": detected_items,
        "is_recyclable": is_recyclable,
        "bin_detected": bin_detected,
    }

# ===== FIRESTORE DATABASE FUNCTIONS =====

def format_address(address_obj):
    """Format structured address object into a single string."""
    parts = []
    block = address_obj.get('block', '').strip()
    street = address_obj.get('street', '').strip()
    postal_code = address_obj.get('postal_code', '').strip()
    
    if block:
        parts.append(f"Block {block}")
    if street:
        parts.append(street)
    if postal_code:
        parts.append(postal_code)
    
    return ", ".join(parts) if parts else "Address not available"


def get_all_bins():
    """Fetch all active recycling bins from Firestore."""
    try:
        bins_ref = db.collection('recycling_bins').where('is_active', '==', True)
        docs = bins_ref.stream()
        
        bins = []
        for doc in docs:
            data = doc.to_dict()
            address_formatted = format_address(data.get('address', {}))
            
            bins.append({
                "id": doc.id,
                "address": address_formatted,
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


def get_user_region(user_id):
    """Fetch user's region from Firestore."""
    try:
        user_doc = db.collection('users').document(user_id).get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict() or {}
            return user_data.get('region_id')
        else:
            logger.warning(f"User {user_id} not found in Firestore")
            return None
    except Exception as e:
        logger.error(f"Error fetching user region: {str(e)}")
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
                "region_id": data.get('region_id', ''),
                "uid": doc.id
            })
        
        logger.info(f"Retrieved {len(users)} users from Firestore")
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return []


def get_user_region_rank(user_id, region_id=None):
    """Calculate user's rank within region based on points."""
    try:
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            logger.warning(f"User {user_id} not found")
            return -1
        
        user_data = user_doc.to_dict() or {}
        user_points = user_data.get('points', 0)
        user_region_id = region_id or user_data.get('region_id')

        if not user_region_id:
            logger.warning(f"User {user_id} does not have a region_id")
            return -1
        
        # Avoid index-dependent aggregation/order queries by calculating rank in Python.
        same_region_users = db.collection('users').where('region_id', '==', user_region_id).stream()
        higher_points = 0
        for region_user in same_region_users:
            region_user_data = region_user.to_dict() or {}
            if region_user_data.get('points', 0) > user_points:
                higher_points += 1

        rank = higher_points + 1
        
        return rank
    except Exception as e:
        logger.error(f"Error calculating user region rank: {str(e)}")
        return -1


def get_user_global_rank(user_id):
    """Calculate user's global rank based on points without index-dependent queries."""
    try:
        user_doc = db.collection('users').document(user_id).get()

        if not user_doc.exists:
            logger.warning(f"User {user_id} not found")
            return -1

        user_data = user_doc.to_dict() or {}
        user_points = user_data.get('points', 0)

        all_users = db.collection('users').stream()
        higher_points = 0
        for other_user in all_users:
            other_user_data = other_user.to_dict() or {}
            if other_user_data.get('points', 0) > user_points:
                higher_points += 1

        return higher_points + 1
    except Exception as e:
        logger.error(f"Error calculating user global rank: {str(e)}")
        return -1

# TO EDIT WHEN INTEGRATING WITH DATABASE
def get_all_user_transactions(userId):
    '''
    Returns all user transactions as a JSON object with proper mapping.
    
    Maps from Firestore transaction documents to frontend SubmissionHistoryItem structure:
    - id: transaction document ID
    - datetime: submitted_at timestamp
    - status: derived from is_counted and cv_result.is_recyclable
    - pointsEarned: points_awarded from database
    - detectedItems: cv_result.detected_items array
    '''
    try:
        transactions_from_db = db.collection('transactions').where('user_id', '==', userId).stream()
        
        transactions_list = []
        
        for transaction_doc in transactions_from_db:
            txn_data = transaction_doc.to_dict()
            
            # Determine status based on is_counted and cv_result.is_recyclable
            is_counted = txn_data.get('is_counted', False)
            cv_result = txn_data.get('cv_result') or {}
            
            if is_counted and txn_data.get('points_awarded', 0) > 0:
                status = "approved"
            else:
                status = "rejected"
            
            # Extract detected items from cv_result, default to empty list
            detected_items = cv_result.get('detected_items', [])

            # Parse submitted_at datetime string
            submitted_at = txn_data.get('submitted_at')
            if hasattr(submitted_at, 'isoformat'):
                submitted_at_value = submitted_at.isoformat()
            elif hasattr(submitted_at, 'to_datetime'):
                # Handle Firestore Timestamp objects
                submitted_at_value = submitted_at.to_datetime().isoformat()
            else:
                submitted_at_value = submitted_at or ''
            
            # Map to SubmissionHistoryItem structure
            submission_item = {
                'id': transaction_doc.id,  # Document ID
                'datetime': submitted_at_value,
                'status': status,
                'pointsEarned': txn_data.get('points_awarded', 0),
                'detectedItems': detected_items
            }
            
            transactions_list.append(submission_item)

        transactions_list.sort(key=lambda x: x.get('datetime') or '', reverse=True)
        
        # Return as JSON response
        return jsonify({
            'status': 'success',
            'data': transactions_list
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching user transactions for {userId}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 


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
        count_result = db.collection('transactions').where('user_id', '==', user_id).where('is_counted', '==', True).count().get()
        total_submissions = 0
        if count_result:
            first_result = count_result[0]
            if isinstance(first_result, list):
                first_result = first_result[0] if first_result else None
            if first_result is not None:
                total_submissions = getattr(first_result, 'value', 0)
        
        # Get last recycled timestamp
        last_txn = db.collection('transactions').where('user_id', '==', user_id).stream()
        latest_submitted_at = None
        last_recycled = None
        for txn in last_txn:
            submitted_at = txn.get('submitted_at')
            if submitted_at is None:
                continue

            comparable = submitted_at.to_datetime() if hasattr(submitted_at, 'to_datetime') else submitted_at
            if latest_submitted_at is None or comparable > latest_submitted_at:
                latest_submitted_at = comparable

        if latest_submitted_at is not None:
            if hasattr(latest_submitted_at, 'isoformat'):
                last_recycled = latest_submitted_at.isoformat()
            else:
                last_recycled = str(latest_submitted_at)
        
        logger.info(f"User {user_id} stats: {username}, {total_points} points, {total_submissions} submissions")
        return username, total_points, level, total_submissions, last_recycled
    except Exception as e:
        logger.error(f"Error fetching user stats: {str(e)}")
        return None, 0, "Bronze", 0, None


def save_transaction(user_id, region_id, gps_location, nearest_bin_id, cv_result, location_check_passed, points_awarded, image_path=None):
    """Save a new transaction (recycling submission) to Firestore."""
    try:
        transaction_data = {
            "user_id": user_id,
            "region_id": region_id,
            "submitted_at": datetime.utcnow(),
            "gps_location": {
                "type": "Point",
                "coordinates": [gps_location[1], gps_location[0]]  # [lng, lat]
            },
            "nearest_bin_id": nearest_bin_id,
            "cv_result": cv_result,
            "location_check_passed": location_check_passed,
            "is_counted": points_awarded > 0,
            "points_awarded": points_awarded,
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


def init_user_profile(user_id, username, email, region_id):
    """Initialize user profile in Firestore after successful auth signup."""
    try:
        # Check if user already exists
        existing = db.collection('users').document(user_id).get()
        if existing.exists:
            logger.warning(f"User {user_id} already initialized")
            return None
        
        # Check if username is already taken
        username_exists = db.collection('users').where('username', '==', username).limit(1).stream()
        if any(username_exists):
            logger.warning(f"Username '{username}' is already taken")
            raise ValueError(f"Username '{username}' is already taken")
        
        # Create user document with defaults
        user_data = {
            "username": username,
            "email": email,
            "region_id": region_id,
            # "district_id": None,  # TODO: Add when implementing districts
            "created_at": datetime.utcnow(),
            "points": 0,
            "badges": [],
            "rewards": []
        }
        
        db.collection('users').document(user_id).set(user_data)
        logger.info(f"User profile initialized: {user_id}")
        return user_data
    except Exception as e:
        logger.error(f"Error initializing user profile: {str(e)}")
        return None


def flatten_dict(d, parent_key='', sep='.'):
    """Flatten a nested dictionary into dot-path format."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def update_user_profile(user_id, update_fields):
    """Update user profile fields.
    
    Accepts flat keys (e.g., 'region_id')
    or nested objects (e.g., {'region_id': 'north'}).

    Returns:
    - (True, None) on success
    - (False, <error_message>) on failure
    """
    try:
        allowed_fields = ['region_id', 'username']
        
        # Flatten nested objects into dot-paths
        flattened = flatten_dict(update_fields)
        
        # Filter to only allowed fields
        filtered_updates = {}
        for field, value in flattened.items():
            if field in allowed_fields:
                filtered_updates[field] = value

        # Normalize and validate username updates
        if 'username' in filtered_updates:
            normalized_username = str(filtered_updates['username']).strip().lower()

            if not normalized_username:
                logger.warning(f"Invalid empty username update for user {user_id}")
                return False, "Username cannot be empty"

            username_exists = db.collection('users').where('username', '==', normalized_username).limit(1).stream()
            for existing_doc in username_exists:
                if existing_doc.id != user_id:
                    logger.warning(f"Username '{normalized_username}' is already taken")
                    return False, "Username is already taken"

            filtered_updates['username'] = normalized_username
        
        if not filtered_updates:
            logger.warning(f"No valid fields to update for user {user_id}")
            return False, "No valid fields to update"
        
        db.collection('users').document(user_id).update(filtered_updates)
        logger.info(f"User profile updated: {user_id} - {list(filtered_updates.keys())}")
        return True, None
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        return False, "Unable to update profile"


def get_all_regions():
    """Fetch all regions from Firestore."""
    try:
        docs = db.collection('regions').stream()
        
        regions = []
        for doc in docs:
            data = doc.to_dict()
            regions.append({
                "id": doc.id,
                "name": data.get('name', ''),
                "code": data.get('code', '')
            })
        
        logger.info(f"Retrieved {len(regions)} regions from Firestore")
        return regions
    except Exception as e:
        logger.error(f"Error fetching regions: {str(e)}")
        return []


def get_all_districts():
    """Fetch all districts from Firestore."""
    try:
        docs = db.collection('districts').stream()
        
        districts = []
        for doc in docs:
            data = doc.to_dict()
            districts.append({
                "id": doc.id,
                "name": data.get('name', ''),
                "region_id": data.get('region_id', '')
            })
        
        logger.info(f"Retrieved {len(districts)} districts from Firestore")
        return districts
    except Exception as e:
        logger.error(f"Error fetching districts: {str(e)}")
        return []

# ===== API ENDPOINTS =====
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
        cv_result = get_model_response(user_id, image_file)
        
        # Find nearest bin
        all_bins = get_all_bins()
        nearest_bin = None
        min_distance = float('inf')
        
        for bin_info in all_bins:
            dist = haversine_distance(latitude, longitude, bin_info['lat'], bin_info['lng'])
            if dist < min_distance:
                min_distance = dist
                nearest_bin = bin_info
        
        # Location check: within configured threshold distance from a bin
        distance_threshold_meters = get_bin_distance_threshold_meters()
        location_check_passed = min_distance <= distance_threshold_meters if nearest_bin else False
        
        # Award points
        points_earned = 50 if (cv_result['bin_detected'] and cv_result['is_recyclable'] and location_check_passed) else 0
        
        # Get user region
        user_region_id = get_user_region(user_id)
        
        # Save transaction to Firestore
        transaction_id = save_transaction(
            user_id=user_id,
            region_id=user_region_id,
            gps_location=(latitude, longitude),
            nearest_bin_id=nearest_bin['id'] if nearest_bin else None,
            cv_result=cv_result,
            location_check_passed=location_check_passed,
            points_awarded=points_earned
        )
        
        # Get updated user stats
        username, total_points, level, total_submissions, last_recycled = get_user_db_stats(user_id)
        
        # Get user rank within region
        user_rank = get_user_region_rank(user_id, user_region_id)

        distance_metres = min_distance if nearest_bin else None
        base_response = {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "verification_details": {
                "gps_match": location_check_passed,
                "distance_metres": distance_metres,
                "detected_items": cv_result.get('detected_items', [])
            },
            "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }

        # Respond based on verification results
        if cv_result['bin_detected'] and cv_result['is_recyclable'] and location_check_passed:
            response_data = {
                "status": "success",
                **base_response,
                "rewards": {
                    "points_earned": points_earned,
                    "bonus_applied": "",
                    "new_total_balance": total_points
                },
                "community_impact": {
                    "district": user_region_id,
                    "district_rank": user_rank
                },
                "message": "Recycling submission verified successfully"
            }
        elif not location_check_passed:
            response_data = {
                "status": "fail",
                **base_response,
                "message": "Location too far from recycling bin"
            }
        elif not cv_result['bin_detected']:
            response_data = {
                "status": "fail",
                **base_response,
                "message": "Image does not contain recycling bin"
            }
        else:
            response_data = {
                "status": "fail",
                **base_response,
                "message": "No recyclable items detected"
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
                "data": [],
                "message": "No nearby bins found"
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
        region = request.args.get('Region', '', type=str).strip().lower()
        limit = request.args.get('Limit', default=10, type=int)

        user_region_id = get_user_region(user_id)
        if not region:
            region = user_region_id or 'all'

        all_users = get_all_users()
        
        if region == "all":
            filtered_list = all_users
        else:
            filtered_list = [u for u in all_users if (u.get('region_id') or '').lower() == region]

        sorted_users = sorted(filtered_list, key=lambda x: x['points'], reverse=True)

        normalized_user_region = (user_region_id or '').lower()
        if region == 'all':
            user_rank = get_user_global_rank(user_id)
        elif normalized_user_region and region == normalized_user_region:
            user_rank = get_user_region_rank(user_id, user_region_id)
        else:
            user_rank = None

        leaderboard_data = []
        current_rank = 0
        last_points = None

        for position, user in enumerate(sorted_users[:limit], start=1):
            points = user['points']
            if last_points is None or points < last_points:
                current_rank = position
                last_points = points

            leaderboard_data.append({
                "rank": current_rank,
                "username": user['username'],
                "points": points
            })

        response = {
            "region": region,
            "user_region": user_region_id,
            "user_current_rank": user_rank, 
            "leaderboard": leaderboard_data
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/users/region', methods=['GET'])
@require_auth
def get_user_region_info():
    """Fetch authenticated user's region id."""
    try:
        user_id = g.user['uid']
        region_id = get_user_region(user_id)

        return jsonify({
            "status": "success",
            "user_id": user_id,
            "region_id": region_id
        }), 200
    except Exception as e:
        logger.error(f"Error fetching user region info: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/users/rank/global', methods=['GET'])
@require_auth
def get_user_global_rank_info():
    """Fetch authenticated user's global rank."""
    try:
        user_id = g.user['uid']
        rank = get_user_global_rank(user_id)

        return jsonify({
            "status": "success",
            "user_id": user_id,
            "rank": rank
        }), 200
    except Exception as e:
        logger.error(f"Error fetching user global rank info: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/users/rank/region', methods=['GET'])
@require_auth
def get_user_region_rank_info():
    """Fetch authenticated user's rank in region."""
    try:
        user_id = g.user['uid']
        region_id = get_user_region(user_id)
        rank = get_user_region_rank(user_id, region_id)

        return jsonify({
            "status": "success",
            "user_id": user_id,
            "region_id": region_id,
            "rank": rank
        }), 200
    except Exception as e:
        logger.error(f"Error fetching user region rank info: {str(e)}")
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

        return transactions

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


'''
TEST ENDPOINT - CALLS get_model_response
'''
@app.route('/api/v1/test-model', methods=['POST'])
def test_model():
    try:
        image_file = request.files.get('Image')
        if not image_file:
            return jsonify({"error": "Missing image file"}), 400
        
        cv_result = get_model_response("test-user", image_file)
        
        logger.info(f"Detected items: {cv_result['detected_items']}, Is recyclable: {cv_result['is_recyclable']}")
        return jsonify({
            "status": "success" if cv_result['is_recyclable'] else "fail",
            "detected_items": cv_result['detected_items'],
            "is_recyclable": cv_result['is_recyclable']
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

'''
GET REGIONS
'''
@app.route('/api/v1/regions', methods=['GET'])
def get_regions():
    """Fetch all available regions for user selection."""
    try:
        regions = get_all_regions()
        
        response_data = {
            "status": "success",
            "data": regions
        }
        return jsonify(response_data), 200
    
    except Exception as e:
        logger.error(f"Error fetching regions: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


'''
GET DISTRICTS
'''
@app.route('/api/v1/districts', methods=['GET'])
def get_districts():
    """Fetch all available districts for user selection."""
    try:
        districts = get_all_districts()
        
        response_data = {
            "status": "success",
            "data": districts
        }
        return jsonify(response_data), 200
    
    except Exception as e:
        logger.error(f"Error fetching districts: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


'''
INITIALIZE USER PROFILE
'''
@app.route('/api/v1/users/init', methods=['POST'])
@require_auth
def init_user():
    """
    Initialize user profile after successful signup.
    Called once after Firebase Auth creates the user account.
    
    Required fields in request body:
    - username: User's username (for display)
    - region_id: Selected region ID (default: "central")
    """
    try:
        user_id = g.user['uid']
        email = g.user.get('email', '')
        
        # Parse request body
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Request body required"}), 400
        
        username = data.get('username', '')
        region_id = data.get('region_id', 'central')  # Default to 'central'
        
        if not username:
            return jsonify({"status": "error", "message": "Username is required"}), 400
        
        # Initialize user profile
        user_data = init_user_profile(user_id, username, email, region_id)
        
        if user_data is None:
            return jsonify({"status": "error", "message": "User already initialized or initialization failed"}), 400
        
        response_data = {
            "status": "success",
            "message": "User profile initialized",
            "user_id": user_id,
            "data": user_data
        }
        return jsonify(response_data), 201
    
    except Exception as e:
        logger.error(f"Error initializing user: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


'''
UPDATE USER PROFILE
'''
@app.route('/api/v1/users/profile', methods=['PUT'])
@require_auth
def update_profile():
    """
    Update user profile information.
    
    Supported fields in request body:
    - username: Update user's username (must be unique)
    - region_id: Update user's region
    """
    try:
        user_id = g.user['uid']
        
        # Parse request body
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Request body required"}), 400
        
        # Update profile
        success, error_message = update_user_profile(user_id, data)
        
        if not success:
            return jsonify({"status": "error", "message": error_message or "No valid fields to update"}), 400
        
        response_data = {
            "status": "success",
            "message": "User profile updated"
        }
        return jsonify(response_data), 200
    
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host="0.0.0.0", port=port)