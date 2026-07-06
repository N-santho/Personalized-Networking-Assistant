from unittest.mock import patch, MagicMock
from backend.services.wiki_service import WikipediaService

@patch("requests.get")
def test_wiki_service_success(mock_get):
    """
    Tests that WikipediaService successfully coordinates the search and retrieval requests,
    returning structured page summaries and links.
    """
    # Configure mock responses for the two API calls
    mock_response_search = MagicMock()
    mock_response_search.json.return_value = {
        "query": {
            "search": [
                {"title": "Blockchain in healthcare"}
            ]
        }
    }
    
    mock_response_detail = MagicMock()
    mock_response_detail.json.return_value = {
        "query": {
            "pages": {
                "54321": {
                    "title": "Blockchain in healthcare",
                    "extract": "Blockchain in healthcare describes the application of cryptographic ledgers to medical records.",
                    "fullurl": "https://en.wikipedia.org/wiki/Blockchain_in_healthcare"
                }
            }
        }
    }
    
    # Apply mock responses sequentially to requests.get
    mock_get.side_effect = [mock_response_search, mock_response_detail]
    
    service = WikipediaService()
    result = service.search_and_summarize("Blockchain in Healthcare")
    
    assert result is not None
    assert result["title"] == "Blockchain in healthcare"
    assert "cryptographic ledgers" in result["summary"]
    assert result["wikipedia_link"] == "https://en.wikipedia.org/wiki/Blockchain_in_healthcare"

@patch("requests.get")
def test_wiki_service_not_found(mock_get):
    """
    Tests that WikipediaService returns None when the search query returns zero matches.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "query": {
            "search": []
        }
    }
    mock_get.return_value = mock_response
    
    service = WikipediaService()
    result = service.search_and_summarize("NonExistentTopic123456789")
    
    assert result is None
