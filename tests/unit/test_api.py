import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
import sys
import os

# Ensure code is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../code'))

from api_server import app, get_db_manager

@pytest.fixture
def mock_db_manager():
    mock = AsyncMock()
    # Mock repositories inside manager
    mock.mongodb = MagicMock()
    mock.neo4j = MagicMock()
    mock.redis = MagicMock()
    mock.cassandra = MagicMock()
    return mock

@pytest.fixture
def client(mock_db_manager):
    app.dependency_overrides[get_db_manager] = lambda: mock_db_manager
    return TestClient(app)

class TestAPI:

    def test_read_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "Welcome" in response.json()['message']

    def test_create_researcher(self, client, mock_db_manager):
        # Setup
        researcher_data = {
            "personal_info": {"first_name": "Test", "last_name": "User", "email": "test@example.com"},
            "academic_profile": {"department": "CS", "position": "Student"},
            "collaboration_metrics": {"h_index": 0, "total_publications": 0}
        }
        mock_db_manager.create_researcher_comprehensive.return_value = "12345"
        
        # Execute
        response = client.post("/researchers/", json=researcher_data)
        
        # Verify
        assert response.status_code == 200
        assert response.json()['id'] == "12345"
        mock_db_manager.create_researcher_comprehensive.assert_called_once()

    def test_get_researcher(self, client, mock_db_manager):
        # Setup
        mock_profile = {"mongodb": {"_id": "123", "name": "Test"}, "collaborators": []}
        mock_db_manager.get_researcher_complete_profile.return_value = mock_profile
        
        # Execute
        response = client.get("/researchers/123")
        
        # Verify
        assert response.status_code == 200
        assert response.json()['mongodb']['name'] == "Test"

    def test_get_researcher_not_found(self, client, mock_db_manager):
        # Setup
        mock_db_manager.get_researcher_complete_profile.return_value = {}
        
        # Execute
        response = client.get("/researchers/999")
        
        # Verify
        assert response.status_code == 404

    def test_system_stats(self, client, mock_db_manager):
        # Setup
        mock_stats = {"summary": {"total_researchers": 10}}
        mock_db_manager.get_system_statistics.return_value = mock_stats
        
        # Execute
        response = client.get("/system/stats")
        
        # Verify
        assert response.status_code == 200
        assert response.json()['summary']['total_researchers'] == 10
