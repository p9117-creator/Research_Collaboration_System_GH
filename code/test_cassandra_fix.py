import logging
import sys
from cassandra.cluster import Cluster

# Configure logging to see errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    print(f"Python version: {sys.version}")
    
    try:
        from cassandra.io.asyncioreactor import AsyncioConnection
        print("Found AsyncioConnection")
        
        # Try creating a cluster object without connecting (to see if it fails at init)
        cluster = Cluster(['127.0.0.1'], connection_class=AsyncioConnection)
        print("Cluster object created with AsyncioConnection")
        
        # We won't actually connect because we don't know if Cassandra is running
        # and we don't want to hang. But the error happened at import/init.
        
    except ImportError as e:
        print(f"AsyncioConnection not found: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
