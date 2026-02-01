
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "smart_battery_db")

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    drivers = list(db.drivers.find({}, {"_id": 0, "driver_id": 1, "driverId": 1, "phone": 1, "phone_number": 1, "mobile": 1, "mobile_no": 1}))
    
    print(f"Found {len(drivers)} drivers.")
    for d in drivers:
        print(d)

except Exception as e:
    print(f"Error: {e}")
