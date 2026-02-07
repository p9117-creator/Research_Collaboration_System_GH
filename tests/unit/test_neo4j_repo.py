import pytest
from unittest.mock import MagicMock, patch
from repositories.neo4j_repo import Neo4jRepository

@pytest.fixture
def mock_driver():
    with patch('repositories.neo4j_repo.GraphDatabase.driver') as mock:
        yield mock

@pytest.fixture
def neo4j_repo(mock_driver):
    repo = Neo4jRepository("bolt://localhost:7687", "neo4j", "password")
    repo.driver = mock_driver.return_value
    return repo

class TestNeo4jRepository:

    def test_connect_success(self, mock_driver):
        repo = Neo4jRepository("bolt://localhost:7687", "neo4j", "password")
        repo.connect()
        
        mock_driver.assert_called_once_with("bolt://localhost:7687", auth=("neo4j", "password"))
        # Verify connectivity check
        repo.driver.session.return_value.__enter__.return_value.run.assert_called_with("RETURN 1")

    def test_create_researcher_node(self, neo4j_repo):
        # Setup
        researcher_data = {
            "_id": "123",
            "personal_info": {
                "first_name": "Taha",
                "last_name": "Hussein",
                "email": "taha.hussein@example.com"  # Added missing email field
            },
            "academic_profile": {"department_id": "DEP1", "position": "Professor"},
            "collaboration_metrics": {"h_index": 10, "total_publications": 50},
            "orcid_id": "0000-0000"
        }
        
        session_mock = neo4j_repo.driver.session.return_value.__enter__.return_value
        
        #Execute
        success = neo4j_repo.create_researcher_node(researcher_data)
        
        # Verify
        assert success is True
        session_mock.run.assert_called_once()
        query_args = session_mock.run.call_args[1]['props']
        assert query_args['name'] == "Taha Hussein"
        assert query_args['id'] == "123"

    def test_add_collaboration(self, neo4j_repo):
        # Setup
        r1_id = "1"
        r2_id = "2"
        session_mock = neo4j_repo.driver.session.return_value.__enter__.return_value
        
        # Execute
        success = neo4j_repo.add_collaboration(r1_id, r2_id)
        
        # Verify
        assert success is True
        session_mock.run.assert_called_once()
        call_kwargs = session_mock.run.call_args[1]
        assert call_kwargs['id1'] == r1_id
        assert call_kwargs['id2'] == r2_id

    def test_find_collaborators(self, neo4j_repo):
        # Setup
        session_mock = neo4j_repo.driver.session.return_value.__enter__.return_value
        
        mock_record1 = MagicMock()
        mock_record1.__getitem__.side_effect = lambda k: {'name': 'Collab 1'} if k == 'collaborator' else 1
        
        session_mock.run.return_value = [mock_record1]
        
        # Execute
        results = neo4j_repo.find_collaborators("123")
        
        # Verify
        assert len(results) == 1
        assert results[0]['name'] == 'Collab 1'
        assert results[0]['distance'] == 1

    def test_create_supervision_relationship(self, neo4j_repo):
        # Setup
        supervisor_id = "sup1"
        student_id = "stu1"
        session_mock = neo4j_repo.driver.session.return_value.__enter__.return_value
        
        # Execute
        success = neo4j_repo.create_supervision_relationship(supervisor_id, student_id, "phd")
        
        # Verify
        assert success is True
        session_mock.run.assert_called()
        call_kwargs = session_mock.run.call_args[1]
        assert call_kwargs['supervisor_id'] == supervisor_id
        assert call_kwargs['student_id'] == student_id
        assert call_kwargs['props']['supervision_type'] == "phd"
