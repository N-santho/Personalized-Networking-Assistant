"""
Service layer for MediaWiki/Wikipedia query API integration.

This module provides the WikipediaService class, which performs text-based 
search lookup against the Wikipedia API to retrieve resolved page titles, 
brief summaries, and canonical URLs for grounding unknown topics.
"""

import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WikipediaService:
    """
    Service to interact with the Wikipedia API to search for topics,
    retrieve summaries, and generate article links.
    """
    def __init__(self):
        """
        Initializes the WikipediaService with default MediaWiki endpoint 
        and descriptive User-Agent header to comply with API policies.
        """
        self.api_url = "https://en.wikipedia.org/w/api.php"
        # Wikipedia requires a descriptive User-Agent header to avoid throttling/blocking
        self.headers = {
            "User-Agent": "PersonalizedNetworkingAssistant/1.0 (contact: admin@networkingassistant.com)"
        }

    def search_and_summarize(self, topic: str) -> Optional[Dict[str, Any]]:
        """
        Performs a two-step Wikipedia query:
        1. Searches for the topic to find the best matching page title.
        2. Retrieves the page's summary and canonical URL.

        Args:
            topic (str): The keyword or phrase to search.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing keys:
                - "title": Resolved Wikipedia page title.
                - "summary": Cleaned introductory summary (truncated to max 600 chars).
                - "wikipedia_link": Canonical URL of the article.
                Returns None if no matches are found or lookup fails.

        Raises:
            RuntimeError: If a request network failure or non-200 HTTP code occurs.
        """
        if not topic or not topic.strip():
            return None

        try:
            # Step 1: Search Wikipedia for the closest page title
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": topic,
                "format": "json",
                "srlimit": 1
            }
            
            logger.info(f"Searching Wikipedia for topic: '{topic}'")
            response = requests.get(
                self.api_url, 
                params=search_params, 
                headers=self.headers, 
                timeout=10
            )
            response.raise_for_status()
            search_data = response.json()
            
            search_results = search_data.get("query", {}).get("search", [])
            if not search_results:
                logger.warning(f"No Wikipedia pages found matching: '{topic}'")
                return None
                
            best_match_title = search_results[0]["title"]
            logger.info(f"Best Wikipedia match found: '{best_match_title}'")
            
            # Step 2: Fetch details (summary + URL) for the best match title
            detail_params = {
                "action": "query",
                "prop": "extracts|info",
                "exintro": 1,
                "explaintext": 1,
                "inprop": "url",
                "titles": best_match_title,
                "format": "json"
            }
            
            detail_response = requests.get(
                self.api_url, 
                params=detail_params, 
                headers=self.headers, 
                timeout=10
            )
            detail_response.raise_for_status()
            detail_data = detail_response.json()
            
            pages = detail_data.get("query", {}).get("pages", {})
            if not pages:
                return None
                
            # Wikipedia API keys the page dictionary by its internal Page ID
            page_id = list(pages.keys())[0]
            if page_id == "-1":
                logger.warning(f"Page detail lookup failed for title: '{best_match_title}'")
                return None
                
            page_info = pages[page_id]
            summary = page_info.get("extract", "").strip()
            # If summary is very long, truncate to first few sentences or a reasonable length
            if len(summary) > 600:
                # Find the last period within the limit to avoid half sentences
                truncated = summary[:600]
                last_period = truncated.rfind('.')
                if last_period != -1:
                    summary = truncated[:last_period + 1]
                else:
                    summary = truncated + "..."
            
            return {
                "title": page_info.get("title", best_match_title),
                "summary": summary if summary else "No summary description available.",
                "wikipedia_link": page_info.get("fullurl", f"https://en.wikipedia.org/wiki/{best_match_title.replace(' ', '_')}")
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error querying Wikipedia API: {e}")
            raise RuntimeError("Could not connect to Wikipedia API.") from e
        except Exception as e:
            logger.error(f"Unexpected error in WikipediaService: {e}")
            return None
