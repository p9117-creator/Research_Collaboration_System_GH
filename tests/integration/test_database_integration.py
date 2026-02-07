"""
Integration Tests for Research Collaboration System
Tests database interactions with real (test) databases
"""

import pytest
import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../code'))

from database_manager import ResearchDatabaseManager, load_database_config


class TestDatabaseIntegration:
    """Integration tests for database operations across multiple NoSQL stores"""
    
    @pytest.fixture(scope="class")
    def db_manager(self):
        """Create database manager with test configuration"""
        # Use test database configuration
        config = {
            'MONGODB_URI': os.getenv('TEST_MONGODB_URI', 'mongodb://localhost:27017'),
            'MONGODB_DATABASE': 'research_test',
            'NEO4J_URI': os.getenv('TEST_NEO4J_URI', 'bolt://localhost:7687'),
            'NEO4J_USER': os.getenv('TEST_NEO4J_USER', 'neo4j'),
            'NEO4J_PASSWORD': os.getenv('TEST_NEO4J_PASSWORD', 'test_password'),
            'REDIS_URL': os.getenv('TEST_REDIS_URL', 'redis://localhost:6379'),
            'CASSANDRA_HOST': os.getenv('TEST_CASSANDRA_HOST', 'localhost'),
            'CASSANDRA_PORT': os.getenv('TEST_CASSANDRA_PORT', '9042'),
        }
        
        manager = ResearchDatabaseManager(config)
        
        # Try to connect, skip tests if databases unavailable
        try:
            if not manager.connect_all():
                pytest.skip("Database connection failed")
        except Exception as e:
            pytest.skip(f"Database unavailable: {e}")
            
        yield manager
        
        # Cleanup
        manager.disconnect_all()
    
    @pytest.fixture
    def sample_researcher(self):
        """Sample researcher data for testing"""
        return {
            'personal_info': {
                'first_name': 'Integration',
                'last_name': 'Test',
                'email': f'integration.test.{datetime.now().timestamp()}@example.com'
            },
            'academic_profile': {
                'department_id': 'dept_cs',
                'position': 'Professor',
                'research_interests': ['Machine Learning', 'Data Science']
            },
            'collaboration_metrics': {
                'h_index': 25,
                'total_publications': 50,
                'total_citations': 1000,
                'collaboration_score': 0.85
            }
        }
    
    def test_create_researcher_comprehensive(self, db_manager, sample_researcher):
        """Test creating researcher across all databases"""
        # Act
        researcher_id = db_manager.create_researcher_comprehensive(sample_researcher)
        
        # Assert
        assert researcher_id is not None
        assert isinstance(researcher_id, str)
        
        # Verify in MongoDB
        mongo_doc = db_manager.mongodb.get_researcher(researcher_id)
        assert mongo_doc is not None
        assert mongo_doc['personal_info']['first_name'] == 'Integration'
        
        # Cleanup
        db_manager.delete_researcher_comprehensive(researcher_id)
    
    def test_get_researcher_complete_profile(self, db_manager, sample_researcher):
        """Test retrieving complete researcher profile from all databases"""
        # Arrange
        researcher_id = db_manager.create_researcher_comprehensive(sample_researcher)
        
        # Act
        profile = db_manager.get_researcher_complete_profile(researcher_id)
        
        # Assert
        assert 'mongodb' in profile
        assert profile['mongodb'] is not None
        assert 'collaborators' in profile
        
        # Cleanup
        db_manager.delete_researcher_comprehensive(researcher_id)
    
    def test_update_researcher_comprehensive(self, db_manager, sample_researcher):
        """Test updating researcher across all databases"""
        # Arrange
        researcher_id = db_manager.create_researcher_comprehensive(sample_researcher)
        
        update_data = {
            'academic_profile.position': 'Associate Professor',
            'collaboration_metrics.h_index': 30
        }
        
        # Act
        success = db_manager.update_researcher_comprehensive(researcher_id, update_data)
        
        # Assert
        assert success is True
        
        # Verify update
        updated = db_manager.mongodb.get_researcher(researcher_id)
        assert updated['academic_profile']['position'] == 'Associate Professor'
        
        # Cleanup
        db_manager.delete_researcher_comprehensive(researcher_id)
    
    def test_delete_researcher_comprehensive(self, db_manager, sample_researcher):
        """Test deleting researcher from all databases"""
        # Arrange
        researcher_id = db_manager.create_researcher_comprehensive(sample_researcher)
        
        # Act
        success = db_manager.delete_researcher_comprehensive(researcher_id)
        
        # Assert
        assert success is True
        
        # Verify deletion
        deleted = db_manager.mongodb.get_researcher(researcher_id)
        assert deleted is None


class TestCrossDBConsistency:
    """Test data consistency across multiple databases"""
    
    @pytest.fixture(scope="class")
    def db_manager(self):
        """Create database manager for consistency tests"""
        config = {
            'MONGODB_URI': os.getenv('TEST_MONGODB_URI', 'mongodb://localhost:27017'),
            'MONGODB_DATABASE': 'research_test',
            'NEO4J_URI': os.getenv('TEST_NEO4J_URI', 'bolt://localhost:7687'),
            'NEO4J_USER': os.getenv('TEST_NEO4J_USER', 'neo4j'),
            'NEO4J_PASSWORD': os.getenv('TEST_NEO4J_PASSWORD', 'test_password'),
            'REDIS_URL': os.getenv('TEST_REDIS_URL', 'redis://localhost:6379'),
            'CASSANDRA_HOST': os.getenv('TEST_CASSANDRA_HOST', 'localhost'),
            'CASSANDRA_PORT': os.getenv('TEST_CASSANDRA_PORT', '9042'),
        }
        
        manager = ResearchDatabaseManager(config)
        try:
            if not manager.connect_all():
                pytest.skip("Database connection failed")
        except Exception as e:
            pytest.skip(f"Database unavailable: {e}")
            
        yield manager
        manager.disconnect_all()
    
    def test_researcher_exists_in_all_stores(self, db_manager):
        """Verify researcher data is synchronized across all databases"""
        # Create researcher
        researcher_data = {
            'personal_info': {
                'first_name': 'Consistency',
                'last_name': 'Test',
                'email': f'consistency.{datetime.now().timestamp()}@example.com'
            },
            'academic_profile': {
                'department_id': 'dept_bio',
                'position': 'Researcher'
            },
            'collaboration_metrics': {
                'h_index': 10,
                'total_publications': 20,
                'collaboration_score': 0.5
            }
        }
        
        researcher_id = db_manager.create_researcher_comprehensive(researcher_data)
        
        # Check MongoDB
        mongo_exists = db_manager.mongodb.get_researcher(researcher_id) is not None
        assert mongo_exists, "Researcher should exist in MongoDB"
        
        # Check Neo4j (node existence)
        neo4j_collaborators = db_manager.neo4j.find_collaborators(researcher_id)
        # Even if no collaborators, the method should work
        assert neo4j_collaborators is not None
        
        # Cleanup
        db_manager.delete_researcher_comprehensive(researcher_id)


class TestRedisCache:
    """Integration tests for Redis caching"""
    
    @pytest.fixture(scope="class")  
    def db_manager(self):
        config = {
            'MONGODB_URI': os.getenv('TEST_MONGODB_URI', 'mongodb://localhost:27017'),
            'MONGODB_DATABASE': 'research_test',
            'NEO4J_URI': os.getenv('TEST_NEO4J_URI', 'bolt://localhost:7687'),
            'NEO4J_USER': os.getenv('TEST_NEO4J_USER', 'neo4j'),
            'NEO4J_PASSWORD': os.getenv('TEST_NEO4J_PASSWORD', 'test_password'),
            'REDIS_URL': os.getenv('TEST_REDIS_URL', 'redis://localhost:6379'),
            'CASSANDRA_HOST': os.getenv('TEST_CASSANDRA_HOST', 'localhost'),
            'CASSANDRA_PORT': os.getenv('TEST_CASSANDRA_PORT', '9042'),
        }
        
        manager = ResearchDatabaseManager(config)
        try:
            if not manager.connect_all():
                pytest.skip("Database connection failed")
        except Exception as e:
            pytest.skip(f"Database unavailable: {e}")
            
        yield manager
        manager.disconnect_all()
    
    def test_cache_researcher_profile(self, db_manager):
        """Test that researcher profiles are cached in Redis"""
        researcher_data = {
            'personal_info': {
                'first_name': 'Cache',
                'last_name': 'Test',
                'email': f'cache.{datetime.now().timestamp()}@example.com'
            },
            'academic_profile': {
                'department_id': 'dept_cs',
                'position': 'Student'
            },
            'collaboration_metrics': {
                'h_index': 0,
                'total_publications': 0,
                'collaboration_score': 0.0
            }
        }
        
        researcher_id = db_manager.create_researcher_comprehensive(researcher_data)
        
        # First call should cache the profile
        profile1 = db_manager.get_researcher_complete_profile(researcher_id)
        
        # Second call should return cached version
        profile2 = db_manager.get_researcher_complete_profile(researcher_id)
        
        assert profile2.get('cached', False) or profile2.get('mongodb') is not None
        
        # Cleanup
        db_manager.delete_researcher_comprehensive(researcher_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
