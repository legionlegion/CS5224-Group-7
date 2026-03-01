1. Users table for storing user details and the badges they have earned. (The badges/rewards can be separated into a stand alone table as well)
{
  "_id": ObjectId,
  "username": "string",
  "email": "string",
  "password_hash": "string",
  "district_id": "string", // e.g. "SG-BS" — reference to districts
  "created_at": ISODate,
  "points": int,           // integer of the points user accumulated
  "profile": {
    "display_name": "string",
    "avatar_url": "string"
  },
  "badges": [
    {
      "badge_type": "individual_top3" | "community",
      "month": "2025-01",
      "district_id": "string",
      "awarded_at": ISODate
    }
  ],
  "rewards": [{ // to be implemented}]   // the rewards the user redeemed with points
}

2. Transactions, storing each recycling action, the image uploaded can be saved on a shared folder. If S3 or any other file store is used, the value can be the link or index to the file accordingly. Saving the photo is actually optional to the functionality of the application as long as the result from the CV model is obtained.
{
  "_id": ObjectId,
  "user_id": ObjectId,              // ref to users
  "district_id": "string",          // denormalized for leaderboard queries
  "submitted_at": ISODate,
  "image_path": "/uploads/2025/01/abc123.jpg",
  "gps_location": {
    "type": "Point",
    "coordinates": [114.1694, 22.3193]   // [lng, lat] — GeoJSON format
  },
  "nearest_bin_id": ObjectId,       // ref to recycling_bins
  "cv_result": {
    "is_recyclable": true,
    "confidence": 0.97,
    "label": "plastic_bottle" // or other types of items based on CV classes
  },
  "location_check_passed": true,
  "is_counted": true,               // cv AND location both passed
  "points_awarded": 1
}

3. Recycling_bins. To store the recycling bin data from the data.gov.sg api. https://data.gov.sg/datasets?query=bin&resultId=d_4dde14826642f49eefff48b7832b90db
Probably will need a batch job to periodically call the api and check for data updates.
{
  "_id": ObjectId,
  "inc_crc": "A86545F66AF3A74E",        // gov's unique hash — use for upsert deduplication
  "source_name": "kml_1",               // original feature name from GeoJSON
  "location": {
    "type": "Point",
    "coordinates": [103.875052, 1.388540]  // [lng, lat] — elevation dropped, not needed
  },
  "address": {
    "block": "407",
    "building_name": "",
    "street": "FERNVALE ROAD",
    "floor": "",
    "unit": "",
    "postal_code": "790407",
    "type": "H"                          // H = HDB
  },
  "district_id": "string",              // derived by backend on ingest via postal code lookup
  "description": "To deposit recyclables such as paper...",
  "hyperlink": "www.nea.gov.sg/3R",
  "gov_last_updated": ISODate,          // parsed from FMEL_UPD_D "20170602165922"
  "last_synced_at": ISODate,            // when the batch job last touched this record
  "is_active": true
}

4. Districts. A look up of districts, probably with hard-coded values for prototyping. Or just use regions for initial POC.
{
  "_id": "string",                   // e.g. "SG-BS" used as key
  "name": "string",             // e.g. “Bishan”
  "region": "string"              // e.g. “Central”
}

5. Leaderboard. To store the leader board rankings. We can have a batch job to process the ranking daily or weekly, and control the data retain duration (i.e. past 6 months). Or we can update on each transaction to make it real-time.
The current structure is to rank the districts/communities first then rank individuals within the group. This can be revised depending on how we design the competition.
{
  "_id": ObjectId,
  "month": "2025-01",
  "computed_at": ISODate,

  "district_rankings": [
    {
      "rank": 1,
      "district_id": "SG-HG",
      "district_name": "Hougang",
      "total_score": 312,
      "user_rankings": [
        { "rank": 1, "user_id": ObjectId, "username": "alice", "score": 42, "badge_awarded": "individual_top3" },
        { "rank": 2, "user_id": ObjectId, "username": "bob",   "score": 38, "badge_awarded": "individual_top3" },
        { "rank": 3, "user_id": ObjectId, "username": "carol", "score": 35, "badge_awarded": "individual_top3" },
        { "rank": 4, "user_id": ObjectId, "username": "dave",  "score": 29, "badge_awarded": null }
      ]
    },
    {
      "rank": 2,
      "district_id": "SG-WDL",
      "district_name": "Woodlands",
      "total_score": 289,
      "user_rankings": [ ... ]
    }
  ]
}
