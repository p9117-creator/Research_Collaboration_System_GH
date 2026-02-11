#!/usr/bin/env python3
"""
Research Database Manager - مدير قواعد البيانات
Refactored to use dedicated repositories (Facade Pattern).
Coordinators operations across separate repositories.
"""

import os
import logging
import uuid
from datetime import datetime, date
from typing import Dict, List, Optional, Union

# Import new repositories
from repositories.mongo_repo import MongoDBRepository
from repositories.neo4j_repo import Neo4jRepository
from repositories.redis_repo import RedisRepository
from repositories.cassandra_repo import CassandraRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchDatabaseManager:
    """Main database manager coordinating all NoSQL databases acting as a Facade"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.mongodb = None
        self.neo4j = None
        self.redis = None
        self.cassandra = None
        
    def connect_all(self):
        """Establish connections to all databases via repositories"""
        try:
            # MongoDB
            self.mongodb = MongoDBRepository(
                self.config['MONGODB_URI'],
                self.config.get('MONGODB_DATABASE', 'research_collaboration')
            )
            self.mongodb.connect()
            
            # Neo4j
            self.neo4j = Neo4jRepository(
                self.config['NEO4J_URI'],
                self.config['NEO4J_USER'],
                self.config['NEO4J_PASSWORD']
            )
            self.neo4j.connect()
            
            # Redis
            self.redis = RedisRepository(self.config['REDIS_URL'])
            self.redis.connect()
            
            # Cassandra (Optional - analytics only, failure should not block startup)
            try:
                self.cassandra = CassandraRepository(
                    self.config.get('CASSANDRA_HOST', 'localhost'),
                    int(self.config.get('CASSANDRA_PORT', 9042))
                )
                self.cassandra.connect()
            except Exception as cassandra_err:
                logger.warning(f"Cassandra connection failed (non-fatal for web startup): {cassandra_err}")
                self.cassandra = None
            
            logger.info("All core database connections established via Repositories")
            return True
        except Exception as e:
            logger.error(f"Critical database connection failed: {e}")
            self.disconnect_all()
            return False

    def disconnect_all(self):
        """Close all database connections"""
        if self.mongodb:
            self.mongodb.disconnect()
        if self.neo4j:
            self.neo4j.disconnect()
        if self.redis:
            self.redis.disconnect()
        if self.cassandra:
            self.cassandra.disconnect()
        logger.info("All database connections closed")

    # ==================== COMPREHENSIVE OPERATIONS (ORCHESTRATION) ====================
    
    def create_researcher_comprehensive(self, researcher_data: Dict) -> str:
        """Create researcher across all databases"""
        try:
            # Create in MongoDB (primary storage)
            researcher_id = self.mongodb.create_researcher(researcher_data)
            
            # Create in Neo4j (graph relationships)
            researcher_data['_id'] = researcher_id
            self.neo4j.create_researcher_node(researcher_data)
            
            # Cache in Redis
            if 'collaboration_metrics' in researcher_data:
                stats = {
                    'publications_count': researcher_data['collaboration_metrics']['total_publications'],
                    'h_index': researcher_data['collaboration_metrics']['h_index'],
                    'collaboration_score': researcher_data['collaboration_metrics']['collaboration_score']
                }
                self.redis.update_researcher_stats(researcher_id, stats)
            
            self.redis.cache_researcher_profile(researcher_id, researcher_data)
            
            logger.info(f"Created comprehensive researcher record: {researcher_id}")
            return researcher_id
            
        except Exception as e:
            logger.error(f"Failed to create comprehensive researcher: {e}")
            raise

    def update_researcher_comprehensive(self, researcher_id: str, update_data: Dict) -> bool:
        """Update researcher across all databases"""
        try:
            # Update in MongoDB
            success = self.mongodb.update_researcher(researcher_id, update_data)
            
            # Update in Neo4j
            self.neo4j.update_researcher_node(researcher_id, update_data)
            
            # Update Redis cache (invalidate then re-cache or partially update)
            # Simplest strategy: Invalidate
            self.redis.invalidate_researcher_cache(researcher_id)
            
            # If stats changed, update them specifically
            if 'collaboration_metrics' in update_data:
                metrics = update_data['collaboration_metrics']
                stats = {}
                if 'total_publications' in metrics:
                    stats['publications_count'] = metrics['total_publications']
                if 'h_index' in metrics:
                    stats['h_index'] = metrics['h_index']
                if 'collaboration_score' in metrics:
                    stats['collaboration_score'] = metrics['collaboration_score']
                
                if stats:
                    self.redis.update_researcher_stats(researcher_id, stats)
            
            logger.info(f"Updated comprehensive researcher record: {researcher_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update comprehensive researcher: {e}")
            raise

    def get_researcher_complete_profile(self, researcher_id: str) -> Dict:
        """Get complete researcher profile from all databases"""
        try:
            profile = {}
            
            # Try Redis cache first
            cached_profile = self.redis.get_cached_researcher_profile(researcher_id)
            if cached_profile:
                profile['cached'] = True
                profile['mongodb'] = cached_profile
            else:
                # Get from MongoDB
                mongodb_profile = self.mongodb.get_researcher(researcher_id)
                if mongodb_profile:
                    profile['mongodb'] = mongodb_profile
                    # Cache for future use
                    self.redis.cache_researcher_profile(researcher_id, mongodb_profile)
            
            # Get collaboration network from Neo4j
            collaborators = self.neo4j.find_collaborators(researcher_id)
            profile['collaborators'] = collaborators
            
            # Get cached statistics to ensure latest numbers
            # (Sometimes Redis has simpler/faster stats counters than traversing MongoDoc)
            # stats_key = f"researcher_stats:{researcher_id}"
            # stats = self.redis.client.hgetall(stats_key) # Need to access client or add method
            # For strict layering, we should add a method to RedisRepo. 
            # But let's assume checking the profile dict is enough for this example.
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get complete researcher profile: {e}")
            return {}

    def delete_researcher_comprehensive(self, researcher_id: str) -> bool:
        """Delete researcher from all databases"""
        try:
            # Delete from MongoDB
            mongo_success = self.mongodb.delete_researcher(researcher_id)
            
            # Delete from Neo4j (node and all relationships)
            self.neo4j.delete_researcher_node(researcher_id)
            
            # Invalidate Redis cache
            self.redis.invalidate_researcher_cache(researcher_id)
            
            logger.info(f"Deleted comprehensive researcher record: {researcher_id}")
            return mongo_success
            
        except Exception as e:
            logger.error(f"Failed to delete comprehensive researcher: {e}")
            return False

    def create_project_comprehensive(self, project_data: Dict) -> str:
        """Create project across databases"""
        try:
            # Create in MongoDB
            project_id = self.mongodb.create_project(project_data)
            logger.info(f"Created comprehensive project record: {project_id}")
            return project_id
        except Exception as e:
            logger.error(f"Failed to create comprehensive project: {e}")
            raise

    def update_project_comprehensive(self, project_id: str, update_data: Dict) -> bool:
        try:
            success = self.mongodb.update_project(project_id, update_data)
            return success
        except Exception as e:
            logger.error(f"Failed to update comprehensive project: {e}")
            return False

    def delete_project_comprehensive(self, project_id: str) -> bool:
        try:
            success = self.mongodb.delete_project(project_id)
            return success
        except Exception as e:
            logger.error(f"Failed to delete comprehensive project: {e}")
            return False

    def create_publication_comprehensive(self, publication_data: Dict) -> str:
        """Create publication across databases"""
        try:
            # Create in MongoDB
            pub_id = self.mongodb.create_publication(publication_data)
            # Future: Add to Cassandra via self.cassandra.insert_publication_metrics(...)
            logger.info(f"Created comprehensive publication record: {pub_id}")
            return pub_id
        except Exception as e:
            logger.error(f"Failed to create comprehensive publication: {e}")
            raise

    def update_publication_comprehensive(self, publication_id: str, update_data: Dict) -> bool:
        try:
            success = self.mongodb.update_publication(publication_id, update_data)
            return success
        except Exception as e:
            logger.error(f"Failed to update comprehensive publication: {e}")
            return False

    def delete_publication_comprehensive(self, publication_id: str) -> bool:
        try:
            success = self.mongodb.delete_publication(publication_id)
            return success
        except Exception as e:
            logger.error(f"Failed to delete comprehensive publication: {e}")
            return False

    def add_collaboration(self, researcher1_id: str, researcher2_id: str, 
                          collaboration_type: str = "CO_AUTHORED_WITH", properties: Dict = None) -> bool:
        """Add collaboration relationship between researchers"""
        try:
            if collaboration_type == "CO_AUTHORED_WITH":
                success = self.neo4j.add_collaboration(researcher1_id, researcher2_id)
            elif collaboration_type == "SUPERVISES":
                success = self.neo4j.create_supervision_relationship(researcher1_id, researcher2_id, properties=properties)
            elif collaboration_type == "MENTORS":
                success = self.neo4j.create_mentorship_relationship(researcher1_id, researcher2_id, properties=properties)
            else:
                success = self.neo4j.create_collaboration_relationship(
                    researcher1_id, researcher2_id, collaboration_type, properties
                )
            
            # Invalidate cache for both researchers
            self.redis.invalidate_researcher_cache(researcher1_id)
            self.redis.invalidate_researcher_cache(researcher2_id)
            
            logger.info(f"Added {collaboration_type} relationship: {researcher1_id} <-> {researcher2_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to add collaboration: {e}")
            return False

    def get_system_statistics(self) -> Dict:
        """Get comprehensive system statistics from all databases"""
        try:
            stats = {
                'mongodb': {},
                'neo4j': {},
                'redis': {},
                'summary': {}
            }
            
            # MongoDB statistics
            stats['mongodb']['researchers_count'] = self.mongodb.count_documents('researchers')
            stats['mongodb']['projects_count'] = self.mongodb.count_documents('projects')
            stats['mongodb']['publications_count'] = self.mongodb.count_documents('publications')
            
            # Neo4j statistics
            neo4j_stats = self.neo4j.get_collaboration_statistics()
            stats['neo4j'] = neo4j_stats
            
            # Redis statistics
            redis_stats = self.redis.get_cache_statistics()
            stats['redis'] = redis_stats
            
            # Summary
            stats['summary'] = {
                'total_entities': (
                    stats['mongodb']['researchers_count'] +
                    stats['mongodb']['projects_count'] +
                    stats['mongodb']['publications_count']
                ),
                'total_collaborations': neo4j_stats.get('total_collaborations', 0),
                'cache_hit_rate': redis_stats.get('hit_rate', 0)
            }
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get system statistics: {e}")
            return {}


# Configuration loader
def load_database_config() -> Dict[str, str]:
    return {
        'MONGODB_URI': os.getenv('MONGODB_URI', 'mongodb://admin:research_admin_2024@mongodb:27017/research_collaboration?authSource=admin'),
        'MONGODB_DATABASE': os.getenv('MONGODB_DATABASE', 'research_collaboration'),
        
        'NEO4J_URI': os.getenv('NEO4J_URI', 'bolt://neo4j:7687'),
        'NEO4J_USER': os.getenv('NEO4J_USER', 'neo4j'),
        'NEO4J_PASSWORD': os.getenv('NEO4J_PASSWORD', 'research_neo4j_2024'),
        
        'REDIS_URL': os.getenv('REDIS_URL', 'redis://:research_redis_2024@redis:6379'),
        
        'CASSANDRA_HOST': os.getenv('CASSANDRA_HOST', 'cassandra'),
        'CASSANDRA_PORT': os.getenv('CASSANDRA_PORT', '9042')
    }

if __name__ == "__main__":
    # Test database connections
    config = load_database_config()
    db_manager = ResearchDatabaseManager(config)
    
    try:
        if db_manager.connect_all():
            print("All database connections successful!")
            print("\nTesting database operations...")
            print("MongoDB: Connected")
            print("Neo4j: Connected")
            print("Redis: Connected")
            if db_manager.cassandra.session:
                print("Cassandra: Connected")
            else:
                print("Cassandra: Not Available (Optional)")
            
            print("\nAll databases operational via Repositories!")
        else:
            print("Failed to connect to one or more databases")
            
    finally:
        db_manager.disconnect_all()
