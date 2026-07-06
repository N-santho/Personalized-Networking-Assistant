from backend.services.history_service import HistoryService
from backend.models import History

def test_history_crud(db_session):
    """
    Tests history entry insertion, listing, ordering, and feedback updates.
    """
    # 1. Test insertion
    record = HistoryService.create_history(
        db=db_session,
        event_description="AI Sustainable Cities",
        themes=["AI", "Sustainability"],
        conversation_starters=["S1", "S2", "S3"]
    )
    
    assert record.id is not None
    assert record.event_description == "AI Sustainable Cities"
    assert record.themes == ["AI", "Sustainability"]
    assert record.liked is None  # Check default rating is None
    
    # 2. Test retrieving logs
    # Insert another log to test sorting
    HistoryService.create_history(
        db=db_session,
        event_description="Second Event",
        themes=["Tech"],
        conversation_starters=["S4", "S5", "S6"]
    )
    
    logs = HistoryService.get_history(db=db_session, limit=10)
    assert len(logs) == 2
    # Check descending chronological order (newest first)
    assert logs[0].event_description == "Second Event"
    assert logs[1].event_description == "AI Sustainable Cities"
    
    # 3. Test feedback updates
    updated = HistoryService.update_feedback(
        db=db_session,
        history_id=record.id,
        liked=True,
        comment="Great recommendations."
    )
    assert updated is not None
    assert updated.liked is True
    assert updated.comment == "Great recommendations."
    
    # Check invalid log ID returns None
    invalid_update = HistoryService.update_feedback(
        db=db_session,
        history_id=9999,
        liked=False
    )
    assert invalid_update is None
