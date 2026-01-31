
import os
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "smart_battery_db")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    drivers_collection = db['drivers']
    escalations_collection = db['escalations']
    logger.info("Connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    drivers_collection = None
    escalations_collection = None

def verify_driver(driver_id):
    """
    Verifies if a driver exists in the database.
    Checks 'driver_id' (snake_case) and 'driverId' (camelCase).
    """
    if drivers_collection is None:
        logger.error("Database connection is not available.")
        return False
    
    try:
        # Check snake_case
        if drivers_collection.find_one({"driver_id": driver_id}):
            return True
        # Check camelCase
        if drivers_collection.find_one({"driverId": driver_id}):
            return True
        
        # Check int versions if string provided
        if str(driver_id).isdigit():
             if drivers_collection.find_one({"driver_id": int(driver_id)}): return True
             if drivers_collection.find_one({"driverId": int(driver_id)}): return True
        
        return False
    except Exception as e:
        logger.error(f"Error verifying driver: {e}")
        return False

def get_driver_details(driver_id):
    """
    Fetches driver details for context.
    Returns a dictionary or None.
    """
    if drivers_collection is None:
        return None

    try:
        # Try finding by driver_id or driverId
        query = {"$or": [
            {"driver_id": driver_id},
            {"driverId": driver_id}
        ]}
        
        # Handle potential int/str mismatch
        if str(driver_id).isdigit():
            query["$or"].extend([
                {"driver_id": int(driver_id)},
                {"driverId": int(driver_id)}
            ])

        driver = drivers_collection.find_one(query, {"_id": 0}) # Exclude _id
        return driver
    except Exception as e:
        logger.error(f"Error fetching driver details: {e}")
        return None

from datetime import datetime

def create_escalation(driver_id, intent, confidence, summary=None):
    """
    Creates a new escalation ticket in the database.
    """
    if escalations_collection is None:
        return False
        
    try:
        ticket = {
            "driver_id": driver_id,
            "intent": intent,
            "confidence": confidence,
            "summary": summary or "Automated escalation",
            "status": "OPEN",
            "created_at": datetime.utcnow()
        }
        result = escalations_collection.insert_one(ticket)
        logger.info(f"Escalation ticket created: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error creating escalation: {e}")
        return None

def get_pending_escalations():
    """
    Retrieves all OPEN escalation tickets.
    """
    if escalations_collection is None:
        return []
        
    try:
        # Sort by newest first
        tickets = list(escalations_collection.find({"status": "OPEN"}).sort("created_at", -1))
        # Convert ObjectId and datetime to string for JSON serialization
        for t in tickets:
            t["id"] = str(t["_id"])
            del t["_id"]
            if "created_at" in t:
                t["created_at"] = t["created_at"].isoformat()
                
        return tickets
    except Exception as e:
        logger.error(f"Error fetching escalations: {e}")
        return []
