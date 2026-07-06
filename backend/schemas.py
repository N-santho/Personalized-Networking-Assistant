"""
Pydantic schemas defining request and response schemas for the FastAPI application.

Provides structured payload validation and serialization schemas for the 
event generator, fact checker, log history, and feedback endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Generate Starters Schemas ---
class GenerateRequest(BaseModel):
    """
    Schema for a request payload to generate networking conversation starters.

    Attributes:
        event_description (str): The description or title of the networking event. Minimum length: 3 characters.
        interests (str): User's personal or professional interests (comma-separated). Minimum length: 2 characters.
    """
    event_description: str = Field(
        ..., 
        description="The description or title of the networking event.",
        min_length=3,
        examples=["AI for Sustainable Cities"]
    )
    interests: str = Field(
        ..., 
        description="User's personal or professional interests, comma-separated or text.",
        min_length=2,
        examples=["Climate Change, Urban Planning"]
    )

class GenerateResponse(BaseModel):
    """
    Schema for the response payload containing generated conversation starters.

    Attributes:
        id (int): The unique database identifier for the newly created history log.
        themes (List[str]): List of key themes extracted from the event description.
        conversation_starters (List[str]): Exactly 3 generated icebreaker questions.
    """
    id: int = Field(..., description="The database history record ID.")
    themes: List[str] = Field(..., description="Important themes extracted from the event description.")
    conversation_starters: List[str] = Field(..., description="Exactly 3 generated conversation starters.")

# --- Fact Checker Schemas ---
class FactCheckRequest(BaseModel):
    """
    Schema for a request payload to search and verify a concept on Wikipedia.

    Attributes:
        topic (str): The term or concept query to search. Minimum length: 2 characters.
    """
    topic: str = Field(..., description="Topic/concept to search on Wikipedia.", min_length=2)

class FactCheckResponse(BaseModel):
    """
    Schema for the response payload of a Wikipedia search.

    Attributes:
        title (str): The official, resolved page title on Wikipedia.
        summary (str): A concise, cleaned introductory summary of the Wikipedia article.
        wikipedia_link (str): The canonical URL pointing to the Wikipedia web article.
    """
    title: str = Field(..., description="Wikipedia page title.")
    summary: str = Field(..., description="Wikipedia page summary.")
    wikipedia_link: str = Field(..., description="URL to the Wikipedia article.")

# --- Feedback Schemas ---
class FeedbackRequest(BaseModel):
    """
    Schema for a request payload to submit or update feedback for a history record.

    Attributes:
        id (int): The history database entry ID to update feedback for.
        liked (Optional[bool]): Thumbs up/down signal (True = Useful, False = Not Useful, null = Clear rating).
        comment (Optional[str]): Optional short text comment providing qualitative feedback context.
    """
    id: int = Field(..., description="The history entry ID to update.")
    liked: Optional[bool] = Field(..., description="True if useful, False if not useful, null to clear feedback.")
    comment: Optional[str] = Field(default=None, description="Optional short text comment providing context on why the user liked or disliked the generation.")

class FeedbackResponse(BaseModel):
    """
    Schema for the response payload confirming the feedback update.

    Attributes:
        success (bool): Indicates if the database operation succeeded.
        message (str): Explanatory status description string.
        id (int): The database entry ID that was modified.
        liked (Optional[bool]): The feedback status that was saved.
        comment (Optional[str]): The feedback comment that was saved.
    """
    success: bool = Field(..., description="Whether the feedback update succeeded.")
    message: str = Field(..., description="Status description.")
    id: int = Field(..., description="The entry ID that was modified.")
    liked: Optional[bool] = Field(..., description="The feedback status that was saved.")
    comment: Optional[str] = Field(default=None, description="The feedback comment that was saved.")

# --- History Logs Schemas ---
class HistoryItem(BaseModel):
    """
    Schema representing a single historical conversation generation log retrieved from the database.

    Attributes:
        id (int): The unique primary key of the history log.
        event_description (str): The original description of the event.
        themes (List[str]): List of key themes extracted from the event.
        conversation_starters (List[str]): List of generated icebreakers.
        liked (Optional[bool]): The user feedback status (liked/disliked) associated with the generation.
        comment (Optional[str]): The user text comment associated with the generation feedback.
        created_at (datetime): The timestamp indicating when the history record was created.
    """
    id: int = Field(..., description="The unique history record ID.")
    event_description: str = Field(..., description="The original event description submitted by the user.")
    themes: List[str] = Field(..., description="The themes extracted from the event description.")
    conversation_starters: List[str] = Field(..., description="The conversation starters generated for the event.")
    liked: Optional[bool] = Field(None, description="The user feedback status (liked/disliked) associated with the generation.")
    comment: Optional[str] = Field(None, description="The user comment associated with the generation feedback.")
    created_at: datetime = Field(..., description="The timestamp when this generation history log was created.")

    class Config:
        from_attributes = True
