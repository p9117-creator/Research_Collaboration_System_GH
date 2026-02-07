import os
import re
from pymongo import MongoClient
from passlib.context import CryptContext
from datetime import datetime

# Use environment variable or fallback
uri = os.getenv('MONGODB_URI', "mongodb://admin:research_admin_2024@localhost:27017/research_collaboration?authSource=admin")

try:
    client = MongoClient(uri)
    db = client["research_collaboration"]
    
    # Setup hashing
    # schemes=["scrypt", "bcrypt"] matching our repo update
    pwd_context = CryptContext(schemes=["scrypt", "bcrypt"], deprecated="auto")
    
    new_password = "123456"
    hashed_password = pwd_context.hash(new_password)
    
    target_email = "basharwazwaz@gmail.com"
    
    print(f"Attempting to fix account for: {target_email}")
    
    # 1. Check exact match
    exact_user = db.users.find_one({"email": target_email})
    
    if exact_user:
        print(f"User {target_email} found (exact match). Updating password...")
        db.users.update_one(
            {"_id": exact_user["_id"]}, 
            {"$set": {"password": hashed_password}}
        )
        print("Password reset successfully.")
        
    else:
        # 2. Check case-insensitive match
        regex = re.compile(f"^{re.escape(target_email)}$", re.IGNORECASE)
        case_user = db.users.find_one({"email": regex})
        
        if case_user:
            print(f"Found user with different casing: {case_user['email']}")
            # Update email to lowercase AND password
            db.users.update_one(
                {"_id": case_user["_id"]}, 
                {
                    "$set": {
                        "email": target_email,
                        "password": hashed_password
                    }
                }
            )
            print(f"Converted email to {target_email} and reset password.")
            
        else:
            print("User not found. Creating new user...")
            new_user = {
                "email": target_email,
                "full_name": "Bashar Wazwaz",
                "password": hashed_password,
                "role": "user",
                "created_at": datetime.utcnow(),
                "status": "active"
            }
            db.users.insert_one(new_user)
            print("Created new user successfully.")

except Exception as e:
    print(f"Error: {e}")
