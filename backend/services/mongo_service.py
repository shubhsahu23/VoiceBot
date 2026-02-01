
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
    # Use a short server selection timeout to fail fast if unreachable
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Trigger server selection to validate the connection immediately
    client.server_info()
    db = client[DB_NAME]
    drivers_collection = db['drivers']
    escalations_collection = db['escalations']
    messages_collection = db['messages']
    logger.info("Connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    drivers_collection = None
    escalations_collection = None
    messages_collection = None

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


# --- Phone lookup helpers ---
import re

def _normalize_phone(phone):
    if phone is None:
        return ''
    return ''.join(ch for ch in str(phone) if ch.isdigit())


def get_driver_by_phone(phone):
    """Return driver document (without _id) matching a phone number.
    Tries exact fields and last-10-digits matching to handle varied formats.
    """
    if drivers_collection is None:
        logger.error("Database connection is not available.")
        return None

    pn = _normalize_phone(phone)
    if not pn:
        return None

    # Build queries for exact and suffix (last 10 digits) matches
    last10 = pn[-10:]
    try:
        query = {"$or": [
            {"phone": phone},
            {"phone_number": phone},
            {"mobile": phone},
            {"mobile_no": phone},
            {"driverMobileNumber": phone},
            {"phone": {"$regex": last10}},
            {"phone_number": {"$regex": last10}},
            {"mobile": {"$regex": last10}},
            {"mobile_no": {"$regex": last10}},
            {"driverMobileNumber": {"$regex": last10}}
        ]}
        driver = drivers_collection.find_one(query, {"_id": 0})
        return driver
    except Exception as e:
        logger.error(f"Error fetching driver by phone: {e}")
        return None


def verify_phone(phone):
    """Return True if phone exists for any driver, False otherwise."""
    d = get_driver_by_phone(phone)
    return d is not None

from datetime import datetime
from bson.objectid import ObjectId

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

def get_escalations(status=None):
    """
    Retrieves escalation tickets, optionally filtered by status.
    """
    if escalations_collection is None:
        return []
        
    try:
        query = {}
        if status:
            query["status"] = status
            
        # Sort by newest first
        tickets = list(escalations_collection.find(query).sort("created_at", -1))
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

# --- Live Chat Helpers ---

def save_message(driver_id, sender, text):
    """
    Saves a chat message to the database.
    sender: 'user', 'bot', or 'agent'
    """
    if messages_collection is None:
        return None
    try:
        msg = {
            "driver_id": driver_id,
            "sender": sender,
            "text": text,
            "timestamp": datetime.utcnow()
        }
        result = messages_collection.insert_one(msg)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error saving message: {e}")
        return None

def get_chat_history(driver_id, limit=50):
    """
    Retrieves chat history for a driver.
    """
    if messages_collection is None:
        return []
    try:
        msgs = list(messages_collection.find({"driver_id": driver_id}).sort("timestamp", 1).limit(limit))
        for m in msgs:
            m["id"] = str(m["_id"])
            del m["_id"]
            if "timestamp" in m:
                m["timestamp"] = m["timestamp"].isoformat()
        return msgs
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        return []

def update_escalation_status(ticket_id, status):
    """
    Updates the status of an escalation ticket.
    """
    if escalations_collection is None:
        return False
    try:
        escalations_collection.update_one(
            {"_id": ObjectId(ticket_id)},
            {"$set": {"status": status}}
        )
        return True
    except Exception as e:
        logger.error(f"Error updating escalation: {e}")
        return False

def check_active_escalation(driver_id):
    """
    Checks if there is an active (IN_PROGRESS) escalation for the driver.
    Returns the ticket ID if active, else None.
    """
    if escalations_collection is None:
        return None
    try:
        active = escalations_collection.find_one({
            "driver_id": driver_id, 
            "status": "IN_PROGRESS"
        })
        if active:
            return str(active["_id"])
        return None
    except Exception as e:
        logger.error(f"Error checking active escalation: {e}")
        return None
