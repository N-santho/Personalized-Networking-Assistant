"""
Route handler for submitting recommendation feedback.

This module exposes the `/feedback` endpoint, enabling users to rate previously 
generated conversation starters (thumbs up/down) and submit descriptive text feedback comments.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import FeedbackRequest, FeedbackResponse
from backend.services.history_service import HistoryService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/feedback", 
    response_model=FeedbackResponse,
    summary="Submit user feedback (useful/not useful) and comments for a history item",
    description="Updates a history log record with user liked/disliked validation flags and optional text comments.",
    tags=["History Feedback"]
)
async def update_feedback_endpoint(
    feedback: FeedbackRequest, 
    db: Session = Depends(get_db)
):
    """
    HTTP POST handler to submit feedback for a specific history log entry.

    Data Flow:
    1. Parses history ID, liked state, and optional comment text.
    2. Invokes HistoryService to modify the record in SQLite database.
    3. Raises a 404 exception if the target history log ID is not found.

    Args:
        feedback (FeedbackRequest): Pydantic request model including history ID, rating, and comment.
        db (Session, optional): SQLAlchemy database session dependency.

    Returns:
        FeedbackResponse: Standard response confirming successful operation along with saved details.

    Raises:
        HTTPException: HTTP 404 if the requested history ID does not exist in the database, 
                      or HTTP 500 for general unexpected failures.
    """
    logger.info(f"Received feedback update for log ID {feedback.id} -> liked: {feedback.liked}, comment: {feedback.comment}")
    
    try:
        updated_record = HistoryService.update_feedback(
            db=db, 
            history_id=feedback.id, 
            liked=feedback.liked,
            comment=feedback.comment
        )
        
        if not updated_record:
            logger.warning(f"Failed to submit feedback: ID {feedback.id} does not exist.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"History log entry with ID {feedback.id} was not found."
            )
            
        return FeedbackResponse(
            success=True,
            message="Feedback saved successfully.",
            id=updated_record.id,
            liked=updated_record.liked,
            comment=updated_record.comment
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception(f"Unexpected error updating feedback for ID {feedback.id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {str(e)}"
        )
