
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "smart_battery_db")

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    drivers = db['drivers']
    
    driver_id = "DRV005"
    print(f"Checking for driver: {driver_id}")
    
    # Check string match
    d1 = drivers.find_one({"driver_id": driver_id})
    print(f"Match by driver_id (str): {d1 is not None}")
    
    d2 = drivers.find_one({"driverId": driver_id})
    print(f"Match by driverId (str): {d2 is not None}")

    # Check snake_case/camelCase
    all_drivers = list(drivers.find({}, {"driver_id": 1, "driverId": 1, "_id": 0}))
    print(f"All drivers in DB: {all_drivers}")

except Exception as e:
    print(f"Error: {e}")
