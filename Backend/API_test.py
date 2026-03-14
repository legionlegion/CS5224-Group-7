import requests
import json
import os
from datetime import datetime
import firebase_admin
from firebase_admin import auth, credentials
from dotenv import load_dotenv

SECRETS_DIR = "secrets"
SERVICE_ACCOUNT_FILE = os.path.join(SECRETS_DIR, "serviceAccountKey.json")

# Try both locations for service account key
if not os.path.exists(SERVICE_ACCOUNT_FILE):
    # Try in Backend directory directly
    SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")

# Load environment from .env.local in Backend directory
env_path = os.path.join(os.path.dirname(__file__), ".env.local")
load_dotenv(env_path)

# --- CONFIGURATION ---
WEB_API_KEY = os.getenv("NEXT_PUBLIC_FIREBASE_API_KEY")
BASE_URL = "http://127.0.0.1:8000" + "/api/v1"
TEST_USER_ID = "TEST_USER_123"

def get_authenticated_headers(uid):
    """
    Uses the Service Account to generate a valid Firebase ID Token
    """
    if not WEB_API_KEY:
        raise ValueError("Critical Error: NEXT_PUBLIC_FIREBASE_API_KEY not found in .env.local")

    # Initialize Firebase Admin
    if not firebase_admin._apps:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(f"Missing {SERVICE_ACCOUNT_FILE}")
        cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        firebase_admin.initialize_app(cred)

    # Generate Custom Token
    custom_token = auth.create_custom_token(uid).decode('utf-8')

    # Exchange for ID Token
    exchange_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={WEB_API_KEY}"
    payload = {"token": custom_token, "returnSecureToken": True}
    
    response = requests.post(exchange_url, json=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to exchange token: {response.text}")
    
    return {"Authorization": f"Bearer {response.json()['idToken']}"}

# Get token
print("Generating secure credentials...")
HEADERS = get_authenticated_headers(TEST_USER_ID)
print("Successfully authenticated.\n")


'''
TEST POST VERIFY ACTIVITY
'''
# Configuration
URL = f"{BASE_URL}/verify-activity"
IMAGE_PATH = "recycled_items.jpg"

# Data payload
payload = {
    'Latitude': 1.3521,
    'Longitude': 103.9447
}

# Format: {'Field_Name': ('filename', file_object, 'content_type')}
try:
    with open(IMAGE_PATH, 'rb') as img:
        files = {
            'Image': (IMAGE_PATH, img, 'image/jpeg')
        }

        # POST request
        print(f"Sending recycling submission request to {URL}...")
        response = requests.post(URL, data=payload, files=files, headers=HEADERS)

    if response.status_code == 200:
        print("Success!")
        with open('POST_verify_activity_api_response.json', 'w') as f: 
            json.dump(response.json(), f, indent=4)
        print(response.json())
    else:
        print(f"Failed with status code: {response.status_code}")
        print(response.json())

except FileNotFoundError:
    print(f"Error: Could not find the file '{IMAGE_PATH}'. Please check the path.")
except Exception as e:
    print(f"An error occurred: {e}")


'''
TEST GET NEARBY BINS
'''
print("\nRetrieving nearby bins based on current position...")
URL = f"{BASE_URL}/nearby-bins"
params = {
    'lat': 1.3000,
    'lng': 103.8380,
    'radius': 500   # dist in metres
}

response = requests.get(URL, params=params, headers=HEADERS)
with open('GET_nearby_bins_api_response.json', 'w') as f: 
    json.dump(response.json(), f, indent=4)
print(response.json())


'''
TEST GET LEADERBOARD
'''
print("\nRetrieving leaderboard...")
URL = f"{BASE_URL}/leaderboard"
params = {
    'Scope': 'local',
    'Limit': 3
}

response = requests.get(URL, params=params, headers=HEADERS)

if response.status_code == 200:
    with open('GET_leaderboard_response.json', 'w') as f:
        json.dump(response.json(), f, indent=4)
    print(response.json())
else:
    print(f"Error: {response.status_code}")


'''
TEST GET USER STATISTICS
'''
print("\nRetrieving user statistics...")
URL = f"{BASE_URL}/users/stats"

response = requests.get(URL, headers=HEADERS)

if response.status_code == 200:
    filename = f"GET_user_stats.json"
    with open(filename, 'w') as f:
        json.dump(response.json(), f, indent=4)
    print(response.json())
else:
    print(f"Failed: {response.status_code}")
