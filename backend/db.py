import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ui_templates")

client = MongoClient(MONGODB_URI)
db = client[MONGO_DB_NAME]

def get_db():
    return db 