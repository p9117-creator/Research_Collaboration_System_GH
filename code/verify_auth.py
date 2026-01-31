import logging
from database_manager import ResearchDatabaseManager, load_database_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_auth_logic():
    try:
        config = load_database_config()
        db_manager = ResearchDatabaseManager(config)
        
        if not db_manager.connect_all():
            print("Failed to connect to databases")
            return

        print("\n--- Testing Authentication Logic ---")
        
        # Test User Data
        email = "test_user@example.com"
        password = "secure_password_123"
        full_name = "مستخدم تجريبي"
        
        # 1. Clear existing test user if exists
        db_manager.mongodb.db.users.delete_one({'email': email})
        print(f"Cleared existing user with email: {email}")
        
        # 2. Create User
        user_data = {
            'email': email,
            'full_name': full_name,
            'password': password
        }
        user_id = db_manager.mongodb.create_user(user_data)
        print(f"User created with ID: {user_id}")
        
        # 3. Verify Retrieval
        fetched_user = db_manager.mongodb.get_user_by_email(email)
        if fetched_user and fetched_user['full_name'] == full_name:
            print("User retrieval by email: SUCCESS")
        else:
            print("User retrieval by email: FAILED")
            
        # 4. Verify Password
        is_valid = db_manager.mongodb.verify_password(fetched_user['password'], password)
        if is_valid:
            print("Password verification: SUCCESS")
        else:
            print("Password verification: FAILED")
            
        # 5. Verify wrong password
        is_invalid = db_manager.mongodb.verify_password(fetched_user['password'], "wrong_password")
        if not is_invalid:
            print("Wrong password check: SUCCESS")
        else:
            print("Wrong password check: FAILED")
            
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        db_manager.disconnect_all()

if __name__ == "__main__":
    test_auth_logic()
