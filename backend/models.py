import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from backend.database import Base

class History(Base):
    """
    SQLAlchemy Database model for persisting generated conversation starters,
    extracted themes, user inputs, feedback indicators, and timestamps.
    """
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    event_description = Column(String, nullable=False)
    themes = Column(JSON, nullable=False)  # Stored as a list of strings
    conversation_starters = Column(JSON, nullable=False)  # Stored as a list of strings
    liked = Column(Boolean, nullable=True, default=None)  # True = Useful, False = Not Useful, None = Unrated
    comment = Column(String, nullable=True, default=None)  # Optional text feedback/comment from user
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    def to_dict(self):
        """Helper to convert model instance to dictionary."""
        return {
            "id": self.id,
            "event_description": self.event_description,
            "themes": self.themes,
            "conversation_starters": self.conversation_starters,
            "liked": self.liked,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
