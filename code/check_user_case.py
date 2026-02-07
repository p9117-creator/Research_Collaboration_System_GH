from pymongo import MongoClient
import os

uri = os.getenv('MONGODB_URI', "mongodb://admin:research_admin_2024@localhost:27017/research_collaboration?authSource=admin")

try:
    client = MongoClient(uri)
    db = client["research_collaboration"]
    # Search for case-insensitive
    import re
    user = db.users.find_one({"email": re.compile("basharwazwaz@gmail.com", re.IGNORECASE)})
    
    if user:
        print(f"User found: {user['email']}")
        print(f"Password Hash: {user.get('password')}")
        if 'password' in user:
            print(f"Hash length: {len(user['password'])}")
            print(f"Is bcrypt? {user['password'].startswith('$2')}")
    else:
        print("User NOT found")
        
except Exception as e:
    print(f"Error: {e}")
