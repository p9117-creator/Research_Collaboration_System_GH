from pymongo import MongoClient
import os

# Use environment variable or fallback
uri = os.getenv('MONGODB_URI', "mongodb://admin:research_admin_2024@localhost:27017/research_collaboration?authSource=admin")

try:
    client = MongoClient(uri)
    db = client["research_collaboration"]
    count = db.users.count_documents({})
    print(f"Total users: {count}")
    
    users = db.users.find({}, {"email": 1, "_id": 0})
    for u in users:
        print(f"User: {u.get('email')}")
        
except Exception as e:
    print(f"Error: {e}")
