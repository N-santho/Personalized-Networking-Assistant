"""
Route handler for validating event topics/concepts.

This module exposes the `/factcheck` endpoint, which queries the Wikipedia API
to search for, retrieve summaries of, and provide external reference links 
for unfamiliar concepts or terms.
"""

import logging
from fastapi import APIRouter, HTTPException, status
from backend.schemas import FactCheckRequest, FactCheckResponse
from backend.services.wiki_service import WikipediaService

logger = logging.getLogger(__name__)
router = APIRouter()
wiki_service = WikipediaService()

@router.post(
    "/factcheck", 
    response_model=FactCheckResponse,
    summary="Verify a topic or concept using Wikipedia",
    description="Searches Wikipedia database to return page titles, introductory summaries, and direct web links for grounding.",
    tags=["Fact Checker"]
)
async def factcheck_topic(request_data: FactCheckRequest):
    """
    HTTP POST handler to process a factual verification search.

    Data Flow:
    1. Trims and parses the requested search keyword/topic.
    2. Invokes WikipediaService to search for the closest matching page.
    3. Retrieves summaries and returns them.
    4. Raises an HTTP 404 error if Wikipedia finds no relevant results.

    Args:
        request_data (FactCheckRequest): Pydantic request model holding the target topic text.

    Returns:
        FactCheckResponse: A validated response container with the title, summary, and article URL.

    Raises:
        HTTPException: HTTP 404 if the topic does not match any Wikipedia search records, 
                      or HTTP 500 for network connection failures.
    """
    topic_query = request_data.topic.strip()
    logger.info(f"Factcheck request received for topic: '{topic_query}'")
    
    try:
        # Fetch matching summary and links from Wikipedia service
        result = wiki_service.search_and_summarize(topic_query)
        
        if not result:
            logger.warning(f"Factcheck failed: Topic '{topic_query}' not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_query}' not found on Wikipedia. Please try a different or broader topic search."
            )
            
        return FactCheckResponse(
            title=result["title"],
            summary=result["summary"],
            wikipedia_link=result["wikipedia_link"]
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception(f"Unexpected exception during factcheck for topic '{topic_query}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal database or API connection error: {str(e)}"
        )
