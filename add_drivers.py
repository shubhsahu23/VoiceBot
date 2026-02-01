
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "smart_battery_db")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
drivers = db['drivers']

new_drivers = [
    {
        "driverId": "DRV004",
        "name": "Arjun Singh",
        "phone": "9876543214",
        "language": "Hindi",
        "vehicle_no": "MH12DE1234"
    },
    {
        "driverId": "DRV005",
        "name": "Vikram Malhotra",
        "phone": "9876543215",
        "language": "English",
        "vehicle_no": "MH12DE5678"
    }
]

for d in new_drivers:
    if not drivers.find_one({"driverId": d["driverId"]}):
        drivers.insert_one(d)
        print(f"Added {d['driverId']}")
    else:
        print(f"{d['driverId']} already exists")

print("Done.")
