from database_manager import ResearchDatabaseManager, load_database_config
import json

def diagnose():
    config = load_database_config()
    db_manager = ResearchDatabaseManager(config)
    if not db_manager.connect_all():
        print("Failed to connect")
        return

    print("Checking Projects...")
    projects = list(db_manager.mongodb.db.projects.find().limit(5))
    for p in projects:
        print(f"\nProject: {p.get('title')}")
        pis = p.get('participants', {}).get('principal_investigators', [])
        print(f"PIs found: {len(pis)}")
        for pi in pis:
            rid = pi.get('researcher_id')
            print(f"  Looking for researcher_id: {rid} (type: {type(rid)})")
            researcher = db_manager.mongodb.get_researcher(rid)
            if researcher:
                name = f"{researcher['personal_info']['first_name']} {researcher['personal_info']['last_name']}"
                print(f"  FOUND: {name}")
            else:
                print(f"  NOT FOUND in MongoDB")
                # Try ObjectId as fallback
                from bson.objectid import ObjectId
                try:
                    researcher = db_manager.mongodb.db.researchers.find_one({'_id': ObjectId(rid)})
                    if researcher:
                        print(f"  FOUND by ObjectId conversion!")
                    else:
                        print(f"  STILL NOT FOUND")
                except:
                    print(f"  ID is not valid ObjectId")

    db_manager.disconnect_all()

if __name__ == "__main__":
    diagnose()
