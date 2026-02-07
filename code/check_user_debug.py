from pymongo import MongoClient
import os
import sys

# Use environment variable or fallback
uri = os.getenv('MONGODB_URI', "mongodb://admin:research_admin_2024@localhost:27017/research_collaboration?authSource=admin")

try:
    client = MongoClient(uri)
    # Test connection
    client.admin.command('ping')
    print("Connected to MongoDB successfully.")
    
    db = client["research_collaboration"]
    user = db.users.find_one({"email": "basharwazwaz@gmail.com"})
    
    if user:
        print(f"User found: {user['email']}")
        print(f"Role: {user.get('role')}")
        print(f"Password Hash: {user.get('password')}")
        if 'password' in user:
            print(f"Hash length: {len(user['password'])}")
    else:
        print("User NOT found")
        
except Exception as e:
    print(f"Error: {e}")
