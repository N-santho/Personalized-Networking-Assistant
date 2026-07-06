from unittest.mock import patch, MagicMock
from fastapi import status

def test_health_check(client):
    """
    Tests that the root endpoint returns a simple healthy status.
    """
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"

@patch("backend.routes.generate.theme_extractor.extract_themes")
@patch("backend.routes.generate.conversation_generator.generate_starters")
def test_generate_endpoint_success(mock_generate, mock_extract, client):
    """
    Tests that /generate extracts themes, generates starters, saves them to history,
    and returns a 201 Created payload.
    """
    # Mock services outputs
    mock_extract.return_value = ["AI", "Sustainability", "Urban Planning"]
    mock_generate.return_value = [
        "How do you think AI can improve sustainable urban planning?",
        "What innovations in smart cities interest you most?",
        "Have you seen any AI applications making cities greener?"
    ]
    
    payload = {
        "event_description": "AI for Sustainable Cities",
        "interests": "Climate Change, Urban Planning"
    }
    
    response = client.post("/generate", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    assert data["id"] is not None
    assert data["themes"] == ["AI", "Sustainability", "Urban Planning"]
    assert len(data["conversation_starters"]) == 3
    assert "smart cities" in data["conversation_starters"][1]

@patch("backend.routes.factcheck.wiki_service.search_and_summarize")
def test_factcheck_endpoint_success(mock_wiki, client):
    """
    Tests that /factcheck queries Wikipedia and returns structured results.
    """
    mock_wiki.return_value = {
        "title": "Blockchain",
        "summary": "A blockchain is a distributed ledger.",
        "wikipedia_link": "https://en.wikipedia.org/wiki/Blockchain"
    }
    
    payload = {"topic": "Blockchain"}
    response = client.post("/factcheck", json=payload)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Blockchain"
    assert "distributed ledger" in data["summary"]
    assert "wikipedia.org" in data["wikipedia_link"]

@patch("backend.routes.factcheck.wiki_service.search_and_summarize")
def test_factcheck_endpoint_not_found(mock_wiki, client):
    """
    Tests that /factcheck returns a 404 error if the topic is not found on Wikipedia.
    """
    mock_wiki.return_value = None
    
    payload = {"topic": "NonExistentTopic123"}
    response = client.post("/factcheck", json=payload)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"]

@patch("backend.routes.generate.theme_extractor.extract_themes")
@patch("backend.routes.generate.conversation_generator.generate_starters")
def test_history_and_feedback_integration(mock_generate, mock_extract, client):
    """
    Tests the integration lifecycle:
    1. Generate an item (which gets saved to history).
    2. Get history to verify the item is returned.
    3. Post feedback for that item to toggle the liked status.
    4. Fetch history again to verify the update persisted.
    """
    mock_extract.return_value = ["Cloud Computing"]
    mock_generate.return_value = ["Q1?", "Q2?", "Q3?"]
    
    # 1. Generate record
    gen_resp = client.post(
        "/generate", 
        json={"event_description": "Cloud Summit", "interests": "SaaS"}
    )
    assert gen_resp.status_code == status.HTTP_201_CREATED
    record_id = gen_resp.json()["id"]
    
    # 2. Get history logs
    hist_resp = client.get("/history")
    assert hist_resp.status_code == status.HTTP_200_OK
    logs = hist_resp.json()
    assert len(logs) == 1
    assert logs[0]["id"] == record_id
    assert logs[0]["liked"] is None
    
    # 3. Post feedback (liked = True)
    feed_payload = {"id": record_id, "liked": True, "comment": "Great job"}
    feed_resp = client.post("/feedback", json=feed_payload)
    assert feed_resp.status_code == status.HTTP_200_OK
    assert feed_resp.json()["success"] is True
    assert feed_resp.json()["liked"] is True
    assert feed_resp.json()["comment"] == "Great job"
    
    # 4. Fetch history again and verify change
    hist_resp2 = client.get("/history")
    assert hist_resp2.status_code == status.HTTP_200_OK
    logs2 = hist_resp2.json()
    assert logs2[0]["liked"] is True
    assert logs2[0]["comment"] == "Great job"
    
    # Test feedback update for invalid ID returns 404
    bad_feed_resp = client.post("/feedback", json={"id": 9999, "liked": False})
    assert bad_feed_resp.status_code == status.HTTP_404_NOT_FOUND
