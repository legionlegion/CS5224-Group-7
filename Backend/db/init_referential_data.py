"""
Referential Data Initialization Script
=======================================
This script manages static/reference data that doesn't change frequently:
- Regions: Top-level geographic divisions
- Districts: Sub-divisions within regions
- Recycling Bins: Sourced from data.gov.sg, synced periodically

Usage:
    python init_referential_data.py
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from html.parser import HTMLParser

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
    """Initialize Firebase Admin SDK."""
    if firebase_admin._apps:
        return firestore.client()
    
    # Look for credentials in environment variable, or default location
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    else:
        # Default: look in parent directory (Backend/)
        script_dir = Path(__file__).parent.parent
        cred_path = str(script_dir / "serviceAccountKey.json")
    
    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Firebase credentials not found at: {cred_path}")
    
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        with open(cred_path) as f:
            data = json.load(f)
            os.environ["GOOGLE_CLOUD_PROJECT"] = data.get("project_id")
    
    logger.info(f"Using credentials from: {cred_path}")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {'projectId': os.environ.get("GOOGLE_CLOUD_PROJECT")})
    
    return firestore.client()


def delete_collection(db, collection_name):
    """
    Delete all documents in a collection.
    Safe pattern: delete-and-recreate allows idempotent seeding.
    """
    try:
        docs = db.collection(collection_name).stream()
        deleted = 0
        for doc in docs:
            doc.reference.delete()
            deleted += 1
        if deleted > 0:
            logger.info(f"Deleted {deleted} documents from '{collection_name}'")
        return True
    except Exception as e:
        logger.error(f"✗ Error deleting collection '{collection_name}': {str(e)}")
        return False


def postal_code_to_region(postal_code):
    """
    Map Singapore postal code to region.
    Regions: central, north, north-east, east, west
    """
    try:
        pc_int = int(postal_code[:2])
    except (ValueError, IndexError):
        return "central"  # Default fallback
    
    # Postal code prefixes to region mapping (Singapore standard)
    if pc_int in [1, 2, 3, 4, 5, 6, 8]:
        return "central"
    elif pc_int in [14, 15, 16, 17, 53, 54, 55, 56]:  # North-East (Hougang, Punggol)
        return "north-east"
    elif pc_int in [7, 73, 74, 75, 76, 77, 78]:  # North (Woodlands, Yishun)
        return "north"
    elif pc_int in [18, 19, 43, 44, 45, 46]:  # East (Tampines, Pasir Ris)
        return "east"
    elif pc_int in [9, 10, 20, 21, 22, 23, 24, 25, 26, 27, 28]:  # West (Jurong, Clementi)
        return "west"
    else:
        return "central"  # Default


def parse_html_description(html_string):
    """
    Extract ALL fields from HTML table-formatted description from data.gov.sg.
    Returns dict with parsed fields: INC_CRC, ADDRESSPOSTALCODE, DESCRIPTION, etc.
    """
    if not html_string:
        return {}
    
    class TableParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.data = {}
            self.current_key = None
            self.current_value = ""
            self.in_th = False
            self.in_td = False
        
        def handle_starttag(self, tag, attrs):
            if tag == "th":
                self.in_th = True
            elif tag == "td":
                self.in_td = True
        
        def handle_endtag(self, tag):
            if tag == "th":
                self.in_th = False
                self.current_key = self.current_value.strip()
                self.current_value = ""
            elif tag == "td":
                self.in_td = False
                if self.current_key:
                    self.data[self.current_key] = self.current_value.strip()
                    self.current_key = None
                self.current_value = ""
        
        def handle_data(self, data):
            if self.in_th or self.in_td:
                self.current_value += data
    
    try:
        parser = TableParser()
        parser.feed(html_string)
        return parser.data
    except Exception as e:
        logger.warning(f"Could not parse HTML description: {str(e)}")
        return {}


def load_recycling_bins_from_file():
    """
    Load recycling bin data from local RecyclingBins.geojson file.
    Returns GeoJSON FeatureCollection or None if load fails.
    
    The static GeoJSON file is managed manually and doesn't require frequent API syncing.
    """
    try:
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        geojson_path = script_dir / "RecyclingBins.geojson"
        
        if not geojson_path.exists():
            logger.error(f"GeoJSON file not found at: {geojson_path}")
            return None
        
        logger.info(f"Loading recycling bins from {geojson_path.name}...")
        
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        feature_count = len(geojson_data.get('features', []))
        logger.info(f"Loaded GeoJSON with {feature_count} features")
        
        return geojson_data
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in GeoJSON file: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error loading GeoJSON file: {str(e)}")
        return None


def fetch_recycling_bins_from_gov():
    """
    [DEPRECATED] Fetch recycling bin data from data.gov.sg API.
    
    This method is kept for reference but is no longer used.
    Use load_recycling_bins_from_file() instead to load from the static RecyclingBins.geojson file.
    The API approach had rate-limiting issues and poor reliability for bulk data.
    """
    logger.warning("fetch_recycling_bins_from_gov() is deprecated. Use load_recycling_bins_from_file() instead.")
    return None


def seed_regions(db):
    """Seed region data into Firestore."""
    try:
        logger.info("\n Seeding regions...")
        
        # Delete existing
        delete_collection(db, 'regions')
        
        # Define regions
        regions = {
            'central': {'name': 'Central', 'code': 'CTR'},
            'north': {'name': 'North', 'code': 'NTH'},
            'north-east': {'name': 'North-East', 'code': 'NTE'},
            'east': {'name': 'East', 'code': 'EST'},
            'west': {'name': 'West', 'code': 'WST'}
        }
        
        batch = db.batch()
        for region_id, region_data in regions.items():
            batch.set(db.collection('regions').document(region_id), {
                'name': region_data['name'],
                'code': region_data['code'],
                'created_at': datetime.utcnow().isoformat() + 'Z'
            })
        
        batch.commit()
        logger.info(f"Successfully seeded {len(regions)} regions")
        return len(regions)
    
    except Exception as e:
        logger.error(f"Error seeding regions: {str(e)}")
        return 0


def seed_districts(db):
    """Seed district data into Firestore."""
    try:
        logger.info("\n Seeding districts...")
        
        # Delete existing
        delete_collection(db, 'districts')
        
        # Define districts (sample - expand as needed)
        districts = [
            {'id': 'dist-central', 'name': 'Downtown Core', 'region_id': 'central'},
            {'id': 'dist-north', 'name': 'Yishun', 'region_id': 'north'},
            {'id': 'dist-ne', 'name': 'Hougang', 'region_id': 'north-east'},
            {'id': 'dist-east', 'name': 'Tampines', 'region_id': 'east'},
            {'id': 'dist-west', 'name': 'Jurong', 'region_id': 'west'}
        ]
        
        batch = db.batch()
        for district in districts:
            batch.set(db.collection('districts').document(district['id']), {
                'name': district['name'],
                'region_id': district['region_id'],
                'created_at': datetime.utcnow().isoformat() + 'Z'
            })
        
        batch.commit()
        logger.info(f"Successfully seeded {len(districts)} districts")
        return len(districts)
    
    except Exception as e:
        logger.error(f"Error seeding districts: {str(e)}")
        return 0


def seed_recycling_bins(db):
    """Seed recycling bin data from local RecyclingBins.geojson file."""
    try:
        # Load from local file instead of API
        geojson = load_recycling_bins_from_file()
        if not geojson or 'features' not in geojson:
            logger.error("Failed to load recycling bins. Skipping seed.")
            return 0
        
        features = geojson['features']
        
        logger.info(f"Processing {len(features)} bins...")
        
        # Delete existing bins
        if not delete_collection(db, 'recycling_bins'):
            logger.error("Failed to delete existing bins. Aborting seed.")
            return 0
        
        # Parse and insert bins
        batch = db.batch()
        bin_count = 0
        skipped = 0
        
        for idx, feature in enumerate(features):
            try:
                geom = feature.get('geometry', {})
                coords = geom.get('coordinates', [0, 0])
                
                # Parse HTML description to extract all fields
                raw_html = feature.get('properties', {}).get('Description', '')
                parsed = parse_html_description(raw_html)
                
                # Get unique ID from parsed data
                inc_crc = parsed.get('INC_CRC') or parsed.get('INC_CRC', '')
                if not inc_crc:
                    skipped += 1
                    if skipped <= 5:
                        logger.warning(f"Bin {idx}: No INC_CRC found. Parsed keys: {list(parsed.keys())[:5]}")
                    continue
                
                # Parse timestamp
                fmel_upd = parsed.get('FMEL_UPD_D', '')
                gov_last_updated = None
                if fmel_upd and len(str(fmel_upd)) >= 14:
                    try:
                        dt = datetime.strptime(str(fmel_upd)[:14], '%Y%m%d%H%M%S')
                        gov_last_updated = dt.isoformat() + 'Z'
                    except ValueError:
                        pass
                
                postal_code = parsed.get('ADDRESSPOSTALCODE', '')
                region = postal_code_to_region(postal_code)
                
                # Get description text
                description = parsed.get('DESCRIPTION', 'Recycling bin')
                
                bin_data = {
                    'source_name': feature.get('properties', {}).get('Name', 'kml'),
                    'location': {
                        'type': 'Point',
                        'coordinates': [float(coords[0]), float(coords[1])]  # [lng, lat]
                    },
                    'address': {
                        'block': parsed.get('ADDRESSBLOCKHOUSENUMBER', ''),
                        'building_name': parsed.get('ADDRESSBUILDINGNAME', ''),
                        'street': parsed.get('ADDRESSSTREETNAME', ''),
                        'floor': parsed.get('ADDRESSFLOORNUMBER', ''),
                        'unit': parsed.get('ADDRESSUNITNUMBER', ''),
                        'postal_code': postal_code,
                        'type': parsed.get('ADDRESSTYPE', '')
                    },
                    'region_id': region,
                    'district_id': region,
                    'description': description,
                    'hyperlink': parsed.get('HYPERLINK', ''),
                    'gov_last_updated': gov_last_updated,
                    'last_synced_at': datetime.utcnow().isoformat() + 'Z',
                    'is_active': True
                }
                
                # Use inc_crc as document ID
                batch.set(db.collection('recycling_bins').document(str(inc_crc)), bin_data)
                bin_count += 1
                
                # Commit in batches of 500
                if bin_count % 500 == 0:
                    batch.commit()
                    batch = db.batch()
                    logger.info(f"  Committed {bin_count} bins...")
            
            except Exception as e:
                logger.warning(f"Error processing bin {idx}: {str(e)}")
                continue
        
        # Commit remaining
        if bin_count % 500 != 0:
            batch.commit()
        
        logger.info(f"Successfully seeded {bin_count} recycling bins (skipped {skipped})")
        return bin_count
    
    except Exception as e:
        logger.error(f"Error seeding recycling bins: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 0


def main():
    """Run all seed operations."""
    logger.info("=" * 60)
    logger.info("EcoBin Referential Data Initialization")
    logger.info("=" * 60)
    
    try:
        db = init_firebase()
        logger.info("Firebase initialized\n")
        
        # Seed in order
        results = {
            'regions': seed_regions(db),
            'districts': seed_districts(db),
            'recycling_bins': seed_recycling_bins(db)
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("Seeding Summary:")
        for task, count in results.items():
            logger.info(f"  {task}: {count} records")
        logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
