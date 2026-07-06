"""
Service layer for managing database CRUD actions on generation logs.

This module houses the HistoryService class, which wraps creation, retrieval, and 
feedback update (liked state and text comment comments) commands using SQLAlchemy Session operations.
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models import History

logger = logging.getLogger(__name__)

class HistoryService:
    """
    CRUD Service that manages conversation generation logs and feedback
    persistence in the SQLite database using SQLAlchemy.
    """
    @staticmethod
    def create_history(
        db: Session, 
        event_description: str, 
        themes: List[str], 
        conversation_starters: List[str]
    ) -> History:
        """
        Creates a new history log entry and persists it.

        Args:
            db (Session): Active SQLAlchemy database session.
            event_description (str): Description/title of the networking event.
            themes (List[str]): List of key themes extracted from the event.
            conversation_starters (List[str]): List of generated starters.

        Returns:
            History: The persisted SQLAlchemy History model instance.

        Raises:
            Exception: If database commit fails (triggers a rollback).
        """
        try:
            db_history = History(
                event_description=event_description,
                themes=themes,
                conversation_starters=conversation_starters,
                liked=None  # Explicitly starts as unrated
            )
            db.add(db_history)
            db.commit()
            db.refresh(db_history)
            logger.info(f"Successfully saved generation history to DB with ID: {db_history.id}")
            return db_history
        except Exception as e:
            db.rollback()
            logger.exception("Failed to insert history record into database.")
            raise e

    @staticmethod
    def get_history(db: Session, limit: int = 50) -> List[History]:
        """
        Fetches the latest history log entries ordered by creation date descending.

        Args:
            db (Session): Active SQLAlchemy database session.
            limit (int, optional): The maximum number of entries to fetch. Defaults to 50.

        Returns:
            List[History]: List of historical log records from SQLite.

        Raises:
            Exception: If the query fails to execute.
        """
        try:
            return db.query(History).order_by(History.created_at.desc()).limit(limit).all()
        except Exception as e:
            logger.exception("Failed to fetch history logs from database.")
            raise e

    @staticmethod
    def update_feedback(db: Session, history_id: int, liked: Optional[bool], comment: Optional[str] = None) -> Optional[History]:
        """
        Updates the feedback status ('liked') and optional comment for a specific history ID.

        Args:
            db (Session): Active SQLAlchemy database session.
            history_id (int): Database record primary key.
            liked (Optional[bool]): Rating boolean state.
            comment (Optional[str], optional): Qualitative feedback comment. Defaults to None.

        Returns:
            Optional[History]: The updated History model instance if found, else None.

        Raises:
            Exception: If the update query fails to commit (triggers a rollback).
        """
        try:
            db_history = db.query(History).filter(History.id == history_id).first()
            if db_history:
                db_history.liked = liked
                db_history.comment = comment
                db.commit()
                db.refresh(db_history)
                logger.info(f"Successfully updated feedback status for ID {history_id} to: {liked}, comment: {comment}")
                return db_history
            logger.warning(f"History log with ID {history_id} not found in database.")
            return None
        except Exception as e:
            db.rollback()
            logger.exception(f"Failed to update feedback for ID {history_id}.")
            raise e
