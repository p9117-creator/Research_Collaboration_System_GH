import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Ensure code is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../code'))

from api_server import app, get_db_manager, get_query_engine, get_current_user

@pytest.fixture
def mock_db_manager():
    mock = AsyncMock()
    # Mock repositories inside manager
    mock.mongodb = MagicMock()
    mock.mongodb.search_researchers = MagicMock(return_value=[])
    mock.neo4j = MagicMock()
    mock.redis = MagicMock()
    mock.cassandra = MagicMock()
    mock.create_researcher_comprehensive = MagicMock(return_value="12345")
    return mock

@pytest.fixture
def mock_query_engine(mock_db_manager):
    mock = MagicMock()
    mock.db_manager = mock_db_manager
    mock.get_researcher_profile_complete = MagicMock()
    return mock

@pytest.fixture
def client(mock_db_manager, mock_query_engine):
    # Override dependencies
    app.dependency_overrides[get_db_manager] = lambda: mock_db_manager
    app.dependency_overrides[get_query_engine] = lambda: mock_query_engine
    # Bypass authentication for tests
    app.dependency_overrides[get_current_user] = lambda: {"email": "test@example.com", "role": "admin"}
    yield TestClient(app)
    # Clean up
    app.dependency_overrides.clear()

class TestAPI:

    def test_read_root(self, client):
        """Test health check endpoint (actual root is /health not /)"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()['status'] == "healthy"

    def test_create_researcher(self, client, mock_db_manager):
        # Setup
        researcher_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "department_id": "dept_cs",
            "position": "Student"
        }
        
        # Execute
        response = client.post("/researchers", json=researcher_data)
        
        # Verify
        assert response.status_code == 200
        assert response.json()['researcher_id'] == "12345"
        mock_db_manager.create_researcher_comprehensive.assert_called_once()

    def test_get_researcher(self, client, mock_query_engine):
        # Setup
        mock_profile = {
            "basic_info": {"first_name": "Test", "last_name": "User"},
            "mongodb_data": {"_id": "123"},
            "collaborators": []
        }
        mock_query_engine.get_researcher_profile_complete.return_value = mock_profile
        
        # Execute
        response = client.get("/researchers/123")
        
        # Verify
        assert response.status_code == 200
        assert "basic_info" in response.json()

    def test_get_researcher_not_found(self, client, mock_query_engine):
        # Setup - make query_engine return error to trigger 404
        from fastapi import HTTPException
        mock_query_engine.get_researcher_profile_complete.return_value = {"error": "Researcher not found"}
        
        # Execute
        response = client.get("/researchers/999")
        
        # Verify
        assert response.status_code == 404

    def test_system_stats(self, client, mock_db_manager):
        # Setup - mock search_researchers to return empty list
        mock_db_manager.mongodb.search_researchers.return_value = []
        
        # Execute
        response = client.get("/stats/overview")
        
        # Verify
        assert response.status_code == 200
        assert "total_researchers" in response.json()
