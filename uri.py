import os

# MongoDB connection URI
# Retrieve MongoDB connection URI from environment variable
URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://USER:PASSWORD@cluster0.pdcle.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
)
