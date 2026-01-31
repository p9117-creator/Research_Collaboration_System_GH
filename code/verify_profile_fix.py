import logging
import json
from database_manager import ResearchDatabaseManager, load_database_config
from query_engine import ResearchQueryEngine

# Configure logging
logging.basicConfig(level=logging.ERROR)

def verify_fix():
    config = load_database_config()
    db_manager = ResearchDatabaseManager(config)
    
    if not db_manager.connect_all():
        print("Failed to connect to databases")
        return

    try:
        query_engine = ResearchQueryEngine(db_manager)
        
        # 1. Get a researcher ID from MongoDB
        researchers = db_manager.mongodb.search_researchers({}, limit=1)
        if not researchers:
            print("No researchers found in MongoDB")
            return
        
        researcher_id = str(researchers[0]["_id"])
        print(f"Testing with Researcher ID: {researcher_id}")

        # 2. Clear cache for this researcher to ensure a "miss" first
        db_manager.redis.client.delete(f"researcher_profile:{researcher_id}")

        # 3. First fetch (MISS)
        print("\n--- Testing Cache MISS ---")
        profile_miss = query_engine.get_researcher_profile_complete(researcher_id)
        
        if "error" in profile_miss:
            print(f"Error on MISS: {profile_miss['error']}")
        else:
            print(f"Cache Status: {profile_miss.get('cache_status')}")
            print(f"Has basic_info: {'basic_info' in profile_miss}")
            if 'basic_info' in profile_miss:
                print(f"First Name: {profile_miss['basic_info'].get('first_name')}")

        # 4. Second fetch (HIT)
        print("\n--- Testing Cache HIT ---")
        profile_hit = query_engine.get_researcher_profile_complete(researcher_id)
        
        if "error" in profile_hit:
            print(f"Error on HIT: {profile_hit['error']}")
        else:
            print(f"Cache Status: {profile_hit.get('cache_status')}")
            print(f"Has basic_info: {'basic_info' in profile_hit}")
            if 'basic_info' in profile_hit:
                print(f"First Name: {profile_hit['basic_info'].get('first_name')}")
            
            # Final Check
            if 'basic_info' in profile_hit and profile_hit['basic_info'].get('first_name'):
                print("\n✅ Verification SUCCESS: Profile mapped correctly on cache hit.")
            else:
                print("\n❌ Verification FAILED: basic_info missing or empty on cache hit.")

    finally:
        db_manager.disconnect_all()

if __name__ == "__main__":
    verify_fix()
