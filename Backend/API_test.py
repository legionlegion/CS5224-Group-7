import requests
import json

# REPLACE WITH CODE TO DETERMINE USER_ID
user_id = "u_99123"

'''
TEST POST VERIFY ACTIVITY
'''
# Configuration
URL = "http://127.0.0.1:5000/api/v1/verify-activity"
IMAGE_PATH = "recycled_items.jpg"

# Data payload
payload = {
    'UserId': "u_99123",
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
        response = requests.post(URL, data=payload, files=files)

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
URL = "http://127.0.0.1:5000/api/v1/nearby-bins"
params = {
    'Latitude': 1.3000,
    'Longitude': 103.8380,
    'Radius': 500   # dist in metres
}

response = requests.get(URL, params=params)
with open('GET_nearby_bins_api_response.json', 'w') as f: 
    json.dump(response.json(), f, indent=4)
print(response.json())


'''
TEST GET LEADERBOARD
'''
print("\nRetrieving leaderboard...")
URL = "http://127.0.0.1:5000/api/v1/leaderboard"
params = {
    'UserId': '123XYZ456',
    'Scope': 'local',
    'Limit': 3
}

response = requests.get(URL, params=params)

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
USER_ID = "u_99123"
URL = f"http://127.0.0.1:5000/api/v1/users/{USER_ID}/stats"

response = requests.get(URL)

if response.status_code == 200:
    filename = f"GET_user_stats_{USER_ID}.json"
    with open(filename, 'w') as f:
        json.dump(response.json(), f, indent=4)
    print(response.json())
else:
    print(f"Failed: {response.status_code}")
