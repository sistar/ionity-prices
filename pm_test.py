"""
This script connects to a MongoDB deployment using the provided connection URI and pings the server to confirm a successful connection.

Modules:
    pymongo.mongo_client: Provides the MongoClient class to connect to MongoDB.
    pymongo.server_api: Provides the ServerApi class to specify the server API version.

Constants:
    uri (str): The MongoDB connection URI.

Functions:
    None

Exceptions:
    Exception: Catches any exception that occurs during the connection attempt and prints the error message.

Usage:
    Run this script to test the connection to your MongoDB deployment. If the connection is successful, a confirmation message will be printed.
"""

import os
import argparse
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import PyMongoError
from dotenv import load_dotenv


def main():
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        raise ValueError("MONGODB_URI environment variable is not set")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--erase",
        choices=["nothing", "testdata", "everything"],
        default="nothing",
        help="Choose what data to erase from the database.",
    )
    args = parser.parse_args()

    client = MongoClient(mongo_uri, server_api=ServerApi("1"))
    try:
        client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB!")
        db_l = client.get_database("charging_providers")

        if args.erase == "testdata":
            # Erase only test data
            db_l.pricing.delete_many(
                {
                    "country": "TestCountry",
                    "provider": "TestProvider",
                    "pricing_model_name": "TestModel",
                }
            )
            print("Test data removed from pricing collection.")
        elif args.erase == "everything":
            # Erase everything
            db_l.pricing.delete_many({})
            print("All data removed from pricing collection.")
        else:
            print("No data erased.")

    except PyMongoError as e:
        print(e)

    finally:
        client.close()


if __name__ == "__main__":
    main()
