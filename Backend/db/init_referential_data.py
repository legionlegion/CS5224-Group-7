"""
Referential Data Seeding Script
================================
This script manages static/reference data that doesn't change frequently.
It supports:
- Deleting and reinitializing collections
- Batch inserting static data
- Easy extension for new referential data types

Usage:
    python seed_referential_data.py
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Firebase
def init_firebase():
    """Initialize Firebase connection."""
    if firebase_admin._apps:
        return firestore.client()
    
    # Get credentials path
    script_dir = Path(__file__).parent.parent  # Backend directory
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or str(script_dir / "serviceAccountKey.json")
    
    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Firebase credentials not found at: {cred_path}")
    
    logger.info(f"Initializing Firebase with credentials from: {cred_path}")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    
    return firestore.client()


def delete_collection(db, collection_name, batch_size=100):
    """
    Delete all documents in a collection.
    WARNING: This is destructive and cannot be undone!
    
    Args:
        db: Firestore client
        collection_name: Name of collection to delete
        batch_size: Number of documents to delete per batch
    """
    logger.info(f"Deleting collection: {collection_name}")
    
    docs = db.collection(collection_name).limit(batch_size).stream()
    deleted = 0
    
    for doc in docs:
        doc.reference.delete()
        deleted += 1
    
    if deleted >= batch_size:
        return delete_collection(db, collection_name, batch_size)
    
    logger.info(f"Deleted {deleted} documents from collection: {collection_name}")
    return deleted


def seed_regions(db):
    """
    Seed region referential data.
    
    Regions are broad geographic groupings. Each region document contains:
    - name: Display name
    - code: Region code (optional)
    
    Define your regions data below:
    """
    
    # ===== HARDCODE YOUR REGIONS DATA HERE =====
    REGIONS_DATA = [
        # Syntax: (ID, data_dict)
        # ("central", {"name": "Central", "code": "CTR"}),
        # ("north", {"name": "North", "code": "N"}),
        # ("north-east", {"name": "North-East", "code": "NE"}),
        # ("east", {"name": "East", "code": "E"}),
        # ("west", {"name": "West", "code": "W"}),
        
        # TODO: Fill in the above with actual region data
        ("central", {"name": "Central", "code": "CT"}),
        ("north", {"name": "North", "code": "NO"}),
        ("north-east", {"name": "North-East", "code": "NE"}),
        ("east", {"name": "East", "code": "EA"}),
        ("west", {"name": "West", "code": "WE"}),
    ]
    
    if not REGIONS_DATA:
        logger.warning("No regions data defined. Please fill in REGIONS_DATA.")
        return 0
    
    collection_name = "regions"
    logger.info(f"Seeding {len(REGIONS_DATA)} regions...")
    
    # Delete existing collection
    delete_collection(db, collection_name)
    
    # Insert new data
    inserted = 0
    for region_id, region_data in REGIONS_DATA:
        try:
            # Add metadata
            region_data['created_at'] = datetime.utcnow().isoformat()
            
            # Insert document
            db.collection(collection_name).document(region_id).set(region_data)
            logger.info(f"Inserted region: {region_id}")
            inserted += 1
        except Exception as e:
            logger.error(f"Failed to insert region {region_id}: {str(e)}")
    
    logger.info(f"Successfully seeded {inserted}/{len(REGIONS_DATA)} regions")
    return inserted


def seed_districts(db):
    """
    Seed district referential data.
    Districts map to regions and contain location information.
    
    Future implementation - define districts data below:
    """
    
    # ===== HARDCODE YOUR DISTRICTS DATA HERE =====
    DISTRICTS_DATA = [
        # Syntax: (district_id, data_dict)
        # ("SG-BS", {"name": "Bishan", "region_id": "central", ...}),
        # ("SG-HG", {"name": "Hougang", "region_id": "east", ...}),
        
        # TODO: Fill in the above with actual district data
    ]
    
    if not DISTRICTS_DATA:
        logger.warning("No districts data defined. Skipping districts seeding.")
        return 0
    
    collection_name = "districts"
    logger.info(f"Seeding {len(DISTRICTS_DATA)} districts...")
    
    # Delete existing collection
    delete_collection(db, collection_name)
    
    # Insert new data
    inserted = 0
    for district_id, district_data in DISTRICTS_DATA:
        try:
            # Add metadata
            district_data['created_at'] = datetime.utcnow().isoformat()
            
            # Insert document
            db.collection(collection_name).document(district_id).set(district_data)
            logger.info(f"Inserted district: {district_id}")
            inserted += 1
        except Exception as e:
            logger.error(f" Failed to insert district {district_id}: {str(e)}")
    
    logger.info(f"Successfully seeded {inserted}/{len(DISTRICTS_DATA)} districts")
    return inserted


def seed_recycling_bins(db):
    """
    Seed recycling bin location data from data.gov.sg or local source.
    
    Future implementation - define bins data below:
    """
    
    # ===== HARDCODE YOUR RECYCLING BINS DATA HERE =====
    BINS_DATA = [
        # Syntax: (inc_crc, data_dict)
        # ("A86545F66AF3A74E", {
        #     "location": {"type": "Point", "coordinates": [103.875052, 1.388540]},
        #     "address": {"block": "407", "street": "FERNVALE ROAD", ...},
        #     ...
        # }),
        
        # TODO: Fill in the above with actual bin data
    ]
    
    if not BINS_DATA:
        logger.warning("No recycling bins data defined. Skipping bins seeding.")
        return 0
    
    collection_name = "recycling_bins"
    logger.info(f"Seeding {len(BINS_DATA)} recycling bins...")
    
    # Delete existing collection
    delete_collection(db, collection_name)
    
    # Insert new data
    inserted = 0
    for bin_id, bin_data in BINS_DATA:
        try:
            # Add metadata
            bin_data['last_synced_at'] = datetime.utcnow().isoformat()
            
            # Insert document
            db.collection(collection_name).document(bin_id).set(bin_data)
            logger.info(f"Inserted bin: {bin_id}")
            inserted += 1
        except Exception as e:
            logger.error(f" Failed to insert bin {bin_id}: {str(e)}")
    
    logger.info(f"Successfully seeded {inserted}/{len(BINS_DATA)} recycling bins")
    return inserted


def main():
    """Main entry point for seeding referential data."""
    logger.info("=" * 60)
    logger.info("Starting Referential Data Seeding")
    logger.info("=" * 60)
    
    try:
        # Initialize Firebase
        db = init_firebase()
        logger.info("Firebase initialized")
        
        # Seed referential data
        results = {
            "regions": seed_regions(db),
            "districts": seed_districts(db),
            "recycling_bins": seed_recycling_bins(db),
        }
        
        # Summary
        logger.info("=" * 60)
        logger.info("Seeding Summary:")
        for data_type, count in results.items():
            logger.info(f"  {data_type}: {count} records")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
