
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "smart_battery_db")

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # Update DRV001 with a phone number
    result = db.drivers.update_one(
        {"driverId": "DRV001"},
        {"$set": {"phone": "9876543210"}}
    )
    
    if result.modified_count > 0:
        print("Updated DRV001 with phone number 9876543210")
    else:
        print("Driver DRV001 not found or already has this phone number.")
        
    # Verify
    driver = db.drivers.find_one({"driverId": "DRV001"})
    print("Updated driver:", driver)

except Exception as e:
    print(f"Error: {e}")
