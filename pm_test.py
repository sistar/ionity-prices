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

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import PyMongoError
from uri import URI

# Create a new client and connect to the server
client = MongoClient(URI, server_api=ServerApi("1"))
# Send a ping to confirm a successful connection
try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except PyMongoError as e:
    print(e)
