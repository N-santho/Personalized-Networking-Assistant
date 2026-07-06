"""
Route handler for generating networking conversation starters.

This module exposes the `/generate` endpoint, which coordinates extracting key 
themes using DistilBERT and generating customized conversation icebreakers using GPT-2.
It persists all inputs and generated outputs in the database history logs.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import GenerateRequest, GenerateResponse
from backend.services.theme_extractor import ThemeExtractor
from backend.services.conversation_generator import ConversationGenerator
from backend.services.history_service import HistoryService

logger = logging.getLogger(__name__)
router = APIRouter()

# Singletons for services to avoid loading models multiple times
theme_extractor = ThemeExtractor()
conversation_generator = ConversationGenerator()

@router.post(
    "/generate", 
    response_model=GenerateResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Generate conversation starters and extract themes",
    description="Generates exactly 3 conversation starters and extracts key themes from a networking event description using local ML models.",
    tags=["Conversation Starters"]
)
async def generate_starters_endpoint(
    request_data: GenerateRequest, 
    db: Session = Depends(get_db)
):
    """
    HTTP POST handler to process theme extraction and conversation starter generation.
    
    Data Flow:
    1. Receives event description and user interests from the request.
    2. Invokes ThemeExtractor (DistilBERT) to distill key themes.
    3. Invokes ConversationGenerator (GPT-2) to draft 3 relevant questions.
    4. Persists the generation log to the SQLite database.
    5. Returns the themes, conversation starters, and database record ID.

    Args:
        request_data (GenerateRequest): Pydantic validation model containing event description and user interests.
        db (Session, optional): SQLAlchemy database session dependency.

    Returns:
        GenerateResponse: A validated response object containing the generated starters, extracted themes, and history record ID.

    Raises:
        HTTPException: HTTP 500 status code if any unexpected error occurs during neural model pipeline execution.
    """
    logger.info(f"Received generation request for event: '{request_data.event_description}'")
    
    try:
        # Step 1: Extract themes using DistilBERT model
        themes = theme_extractor.extract_themes(
            event_description=request_data.event_description,
            interests=request_data.interests
        )
        logger.info(f"Extracted themes: {themes}")

        # Step 2: Generate conversation starters using GPT-2 model
        starters = conversation_generator.generate_starters(
            event_description=request_data.event_description,
            themes=themes,
            interests=request_data.interests
        )
        logger.info(f"Generated {len(starters)} conversation starters.")

        # Step 3: Persist generation details in history
        history_record = HistoryService.create_history(
            db=db,
            event_description=request_data.event_description,
            themes=themes,
            conversation_starters=starters
        )

        return GenerateResponse(
            id=history_record.id,
            themes=themes,
            conversation_starters=starters
        )

    except Exception as e:
        logger.exception("An error occurred during themes and starters generation.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal generator error: {str(e)}"
        )
