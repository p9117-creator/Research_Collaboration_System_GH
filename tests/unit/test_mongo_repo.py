import pytest
from unittest.mock import MagicMock, patch
from repositories.mongo_repo import MongoDBRepository
from datetime import datetime

@pytest.fixture
def mock_mongo():
    with patch('repositories.mongo_repo.MongoClient') as mock_client:
        yield mock_client

@pytest.fixture
def mongo_repo(mock_mongo):
    repo = MongoDBRepository("mongodb://localhost:27017", "test_db")
    repo.client = mock_mongo.return_value
    repo.db = repo.client["test_db"]
    return repo

class TestMongoDBRepository:

    def test_connect_success(self, mock_mongo):
        repo = MongoDBRepository("mongodb://localhost:27017", "test_db")
        repo.connect()
        
        mock_mongo.assert_called_once_with("mongodb://localhost:27017")
        repo.client.admin.command.assert_called_with('ping')
        
    def test_create_researcher(self, mongo_repo):
        # Setup
        researcher_data = {
            "personal_info": {"first_name": "Test", "last_name": "User"},
            "academic_profile": {"department": "CS"}
        }
        
        mock_result = MagicMock()
        mock_result.inserted_id = "12345"
        mongo_repo.db.researchers.insert_one.return_value = mock_result
        
        # Execute
        result_id = mongo_repo.create_researcher(researcher_data)
        
        # Verify
        assert result_id == "12345"
        mongo_repo.db.researchers.insert_one.assert_called_once()
        call_args = mongo_repo.db.researchers.insert_one.call_args[0][0]
        assert call_args['personal_info']['first_name'] == "Test"
        assert 'metadata' in call_args
        assert call_args['_id'] is not None

    def test_get_researcher_found(self, mongo_repo):
        # Setup
        researcher_id = "12345"
        mock_data = {"_id": researcher_id, "name": "Test User"}
        mongo_repo.db.researchers.find_one.return_value = mock_data
        
        # Execute
        result = mongo_repo.get_researcher(researcher_id)
        
        # Verify
        assert result == mock_data
        mongo_repo.db.researchers.find_one.assert_called_with({'_id': researcher_id})

    def test_get_researcher_not_found(self, mongo_repo):
        # Setup
        mongo_repo.db.researchers.find_one.return_value = None
        
        # Execute
        result = mongo_repo.get_researcher("99999")
        
        # Verify
        assert result is None
    
    def test_update_researcher(self, mongo_repo):
        # Setup
        researcher_id = "12345"
        update_data = {"personal_info.first_name": "Updated"}
        
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mongo_repo.db.researchers.update_one.return_value = mock_result
        
        # Execute
        success = mongo_repo.update_researcher(researcher_id, update_data)
        
        # Verify
        assert success is True
        mongo_repo.db.researchers.update_one.assert_called_once()
        
    def test_delete_researcher(self, mongo_repo):
        # Setup
        researcher_id = "12345"
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        mongo_repo.db.researchers.delete_one.return_value = mock_result
        
        # Execute
        success = mongo_repo.delete_researcher(researcher_id)
        
        # Verify
        assert success is True
        mongo_repo.db.researchers.delete_one.assert_called_with({'_id': researcher_id})
