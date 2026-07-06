"""
Route handler for accessing historical networking starter recommendations.

This module exposes the `/history` endpoint, allowing the frontend to fetch 
the latest logs of event descriptions, extracted themes, generated starters, 
and user feedback records.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import HistoryItem
from backend.services.history_service import HistoryService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/history", 
    response_model=List[HistoryItem],
    summary="Get recent conversation generation logs",
    description="Retrieves a list of previous generation queries and outcomes, ordered by creation date descending.",
    tags=["Conversation History"]
)
async def get_history_logs(
    limit: int = 50, 
    db: Session = Depends(get_db)
):
    """
    HTTP GET handler to fetch previous generation histories.

    Fetches the history of previous conversation generation prompts and outputs from SQLite.
    Returned items are sorted newest to oldest.

    Args:
        limit (int, optional): The maximum number of history records to return. Defaults to 50.
        db (Session, optional): SQLAlchemy database session dependency.

    Returns:
        List[HistoryItem]: A list of validated history logs.

    Raises:
        HTTPException: HTTP 500 status code if database fetching fails.
    """
    logger.info(f"Fetching history logs (limit={limit})")
    try:
        history_records = HistoryService.get_history(db=db, limit=limit)
        return history_records
    except Exception as e:
        logger.exception("Failed to retrieve history records from route.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve history logs: {str(e)}"
        )
