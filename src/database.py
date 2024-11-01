import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the MongoDB URI from the .env file
MONGO_URI = os.getenv("MONGO_URI")

# Create an AsyncIOMotorClient instance
client = AsyncIOMotorClient(MONGO_URI)

# Access the "graph_database" database
db = client["graph_database"]

