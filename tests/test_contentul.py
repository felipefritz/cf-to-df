import pytest
from unittest.mock import Mock, patch
from services.contentful_service import ContentfulService
from clients.contentful_client import ContentfulClient


# Mocking AbstractContentfulClient
class MockContentfulClient():
    def content_types(self):
        # Return a mock response
        mock_content_types = Mock()
        mock_content_types.items = [Mock(id="flow"), Mock(id="entityTypes")]
        return mock_content_types

    def entries(self, limit=1000):
        # Return a mock response
        mock_entry1 = Mock(id="id1", raw={'fields':{}, 'sys':{'locale':'es'}}, content_type=Mock(id="type1"))
        mock_entry2 = Mock(id="id2", raw={'fields':{}, 'sys':{'locale':'es'}}, content_type=Mock(id="type2"))
        return [mock_entry1, mock_entry2]


def test_contentful_client():
    with patch('clients.contentful_client.Client') as mock:
        space_id = "dummy_space_id"
        access_token = "dummy_access_token"
        environment = "master"

        client = ContentfulClient(space_id, access_token, environment)
        mock.assert_called_once_with(space_id, access_token, environment=environment)


@pytest.fixture
def setup_contentful_service():
    client = MockContentfulClient()
    service = ContentfulService(client)
    return service


def test_get_content_type_names(setup_contentful_service):
    result = setup_contentful_service.get_content_type_names()
    assert result == ["flow", "entityTypes"]


def test_get_all_entries(setup_contentful_service):
    result = setup_contentful_service.get_all_entries()
    assert len(result) == 2


def test_get_entry_by_id(setup_contentful_service):
    id = 'id1'
    setup_contentful_service.get_all_entries()  
    result = setup_contentful_service.get_entry_by_id(id)
    assert result.id == id


def test_extract_values_from_all_entries(setup_contentful_service):
    data = setup_contentful_service.get_all_entries()
    export_to_excel = False
    result = setup_contentful_service.extract_values_from_all_entries(data, export_to_excel)
  
    assert isinstance(result, dict)
    

