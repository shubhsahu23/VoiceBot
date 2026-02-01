
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "smart_battery_db")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
drivers_collection = db['drivers']

def verify_driver(driver_id):
    print(f"Verifying {driver_id}...")
    try:
        # Check snake_case
        if drivers_collection.find_one({"driver_id": driver_id}):
            print("Found via driver_id")
            return True
        # Check camelCase
        if drivers_collection.find_one({"driverId": driver_id}):
            print("Found via driverId")
            return True
        
        # Check int versions if string provided
        if str(driver_id).isdigit():
             if drivers_collection.find_one({"driver_id": int(driver_id)}): return True
             if drivers_collection.find_one({"driverId": int(driver_id)}): return True
        
        print("Not found")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

verify_driver("DRV005")
verify_driver("DRV001")
