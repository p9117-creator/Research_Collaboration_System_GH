#!/usr/bin/env python3
"""
Repopulate Database with High Quality Sample Data
Clears existing collections and runs the data generator
"""

import logging
from database_manager import ResearchDatabaseManager, load_database_config
from data_generator import ResearchDataGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def repopulate():
    try:
        config = load_database_config()
        db_manager = ResearchDatabaseManager(config)
        
        if not db_manager.connect_all():
            logger.error("Failed to connect to databases")
            return

        logger.info("Connected to databases. Clearing existing data...")
        
        # 1. Clear MongoDB collections
        db_manager.mongodb.db.researchers.delete_many({})
        db_manager.mongodb.db.projects.delete_many({})
        db_manager.mongodb.db.publications.delete_many({})
        logger.info("MongoDB collections cleared")
        
        # 2. Clear Neo4j
        with db_manager.neo4j.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("Neo4j database cleared")
        
        # 3. Clear Cassandra (Analytics)
        if hasattr(db_manager, 'cassandra') and db_manager.cassandra and db_manager.cassandra.session:
            try:
                db_manager.cassandra.session.execute("TRUNCATE publication_metrics")
                db_manager.cassandra.session.execute("TRUNCATE department_analytics")
                logger.info("Cassandra tables truncated")
            except Exception as e:
                logger.warning(f"Could not truncate Cassandra tables (might not exist yet): {e}")
        else:
            logger.warning("Cassandra not connected, skipping truncation")

        # 4. Generate New Data
        logger.info("Generating new high-quality data...")
        generator = ResearchDataGenerator(db_manager)
        
        # Generate a good amount of data for a realistic feel
        results = generator.load_all_data(
            researcher_count=15,
            project_count=12,
            publication_count=25
        )
        
        logger.info(f"Successfully repopulated database: {results}")
        
    except Exception as e:
        logger.error(f"Repopulation failed: {e}")
    finally:
        db_manager.disconnect_all()

if __name__ == "__main__":
    repopulate()
