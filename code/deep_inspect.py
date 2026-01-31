from database_manager import MongoDBManager, load_database_config
from bson.objectid import ObjectId

def inspect():
    config = load_database_config()
    mongo = MongoDBManager(config['mongodb']['connection_string'], config['mongodb']['database_name'])
    mongo.connect()
    
    print("--- Researchers (1st document) ---")
    res = mongo.db.researchers.find_one()
    if res:
        print(f"ID: {res['_id']} (Type: {type(res['_id'])})")
        print(f"Name: {res.get('personal_info', {}).get('first_name')} {res.get('personal_info', {}).get('last_name')}")
    else:
        print("No researchers found")
        
    print("\n--- Projects (1st document) ---")
    prj = mongo.db.projects.find_one()
    if prj:
        print(f"ID: {prj['_id']} (Type: {type(prj['_id'])})")
        pis = prj.get('participants', {}).get('principal_investigators', [])
        print(f"PI Count: {len(pis)}")
        for pi in pis:
            rid = pi.get('researcher_id')
            print(f"  PI Researcher ID: {rid} (Type: {type(rid)})")
            # Try lookup
            direct = mongo.db.researchers.find_one({'_id': rid})
            print(f"  Direct lookup match: {direct is not None}")
            if not direct and isinstance(rid, str) and len(rid) == 24:
                obj_lookup = mongo.db.researchers.find_one({'_id': ObjectId(rid)})
                print(f"  ObjectId lookup match: {obj_lookup is not None}")
    else:
        print("No projects found")
        
    mongo.disconnect()

if __name__ == "__main__":
    inspect()
