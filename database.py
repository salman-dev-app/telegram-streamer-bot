from pymongo import MongoClient
from config import MONGO_URI
import datetime

client = MongoClient(MONGO_URI)
db = client.get_database("LinkerBotDB")

users_collection = db.get_collection("users")

def add_user(user_id, first_name, username):
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({
            "user_id": user_id,
            "first_name": first_name,
            "username": username,
            "date_joined": datetime.datetime.utcnow()
        })

def get_all_users():
    return users_collection.find()

def get_total_users():
    return users_collection.count_documents({})
