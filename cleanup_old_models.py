# pylint: disable=missing-module-docstring
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv("MONGODB_URI")
if not mongo_uri:
    raise ValueError("MONGODB_URI environment variable is required")

client = MongoClient(mongo_uri, server_api=ServerApi("1"))
db = client.get_database("charging_providers")

# Old pricing model names that should be marked as invalid
OLD_MODEL_NAMES = [
    "IONITY PASSPORT POWER",
    "IONITY PASSPORT MOTION",
    "CONTACTLESS",
    "DIRECT",
]

# Mark old models as invalid (set valid_to date)
archive_timestamp = datetime.now(ZoneInfo("UTC"))

for model_name in OLD_MODEL_NAMES:
    result = db.pricing.update_many(
        {
            "provider": "Ionity",
            "pricing_model_name": model_name,
            "valid_to": None  # Only update active records
        },
        {
            "$set": {"valid_to": archive_timestamp}
        }
    )
    print(f"Marked {result.modified_count} '{model_name}' records as invalid")

print(f"\nArchived old models with valid_to: {archive_timestamp}")
print("Old pricing models have been cleaned up successfully!")

client.close()
