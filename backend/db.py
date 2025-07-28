import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Try to load .env file, but don't fail if it doesn't exist or is corrupted
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Using default environment variables")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ui_templates")

client = MongoClient(MONGODB_URI)
db = client[MONGO_DB_NAME]

def get_db():
    return db 