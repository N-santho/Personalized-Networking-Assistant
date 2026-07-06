"""
Service layer for theme extraction using DistilBERT Zero-Shot Classification.

This module houses the ThemeExtractor class which leverages a transformer model
to map event descriptions against candidate labels (user interests + networking taxomony).
It includes a regex-based keyword overlap matcher as a local fallback mechanism.
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)

# Standalone basic stopword list to use in fallback keyword extraction
STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
    'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should',
    "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't",
    'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
}

# Standard networking themes pool to enrich classifier candidates
DEFAULT_THEMES = [
    "AI", "Machine Learning", "Data Science", "Sustainability", "Urban Planning", 
    "Climate Change", "Technology", "Blockchain", "Healthcare", "Finance", 
    "Education", "Web Development", "Business", "Marketing", "Entrepreneurship", 
    "Energy", "Design", "Software Engineering", "Social Impact"
]

class ThemeExtractor:
    """
    Service that uses a DistilBERT zero-shot classifier to extract relevant themes
    from an event description based on user interests and a default taxonomy.
    """
    def __init__(self, model_name: str = "typeform/distilbert-base-uncased-mnli"):
        """
        Initializes the ThemeExtractor service with a zero-shot classification model.

        Args:
            model_name (str, optional): The zero-shot classification model name. 
                                        Defaults to "typeform/distilbert-base-uncased-mnli".
        """
        self.model_name = model_name
        self.pipeline = None
        self._initialized = False

    def initialize_model(self) -> bool:
        """
        Lazily loads the HuggingFace zero-shot classification pipeline.

        Returns:
            bool: True if the model loaded successfully, False if fallback is triggered.
        """
        if self._initialized:
            return True
        try:
            logger.info(f"Loading theme extraction model: {self.model_name}...")
            # Import pipeline here to avoid loading heavy dependencies on module load
            from transformers import pipeline
            self.pipeline = pipeline(
                "zero-shot-classification", 
                model=self.model_name
            )
            self._initialized = True
            logger.info("Theme extraction model loaded successfully.")
            return True
        except Exception as e:
            logger.warning(
                f"Failed to load zero-shot classification model: {e}. "
                "ThemeExtractor will fall back to rule-based keyword extraction."
            )
            self.pipeline = None
            self._initialized = False
            return False

    def extract_themes(self, event_description: str, interests: str, limit: int = 3) -> List[str]:
        """
        Extracts up to `limit` relevant themes. Combines user interests and default categories,
        classifies the description using the transformer pipeline, and filters by score.
        Falls back to rule-based keyword extraction if the neural network is unavailable.

        Args:
            event_description (str): Description text of the networking event.
            interests (str): Comma-separated user interest list.
            limit (int, optional): Maximum count of themes to return. Defaults to 3.

        Returns:
            List[str]: Extracted theme strings sorted by classification relevance score.
        """
        # Parse interests from comma-separated string
        parsed_interests = [i.strip() for i in re.split(r'[,\n;]', interests) if i.strip()]
        
        # Load model if possible
        model_loaded = self.initialize_model()

        if model_loaded and self.pipeline is not None:
            try:
                # Combine user interests and default networking categories as candidate labels
                candidate_labels = list(set(parsed_interests + DEFAULT_THEMES))
                
                # Perform zero-shot classification
                result = self.pipeline(
                    event_description,
                    candidate_labels=candidate_labels,
                    multi_label=True
                )
                
                # Fetch labels sorting by descending classification score
                labels = result.get("labels", [])
                scores = result.get("scores", [])
                
                # Sort themes by score
                sorted_themes = [label for label, score in zip(labels, scores) if score > 0.15]
                
                # Make sure we prioritize the user's interests if they match high enough
                # and return exactly up to the limit
                final_themes = sorted_themes[:limit]
                
                # Fallback check: if no themes scored highly enough, just return user interests
                if not final_themes:
                    final_themes = parsed_interests[:limit] if parsed_interests else ["Technology"]
                    
                return final_themes
                
            except Exception as e:
                logger.error(f"Error during neural theme extraction: {e}. Executing fallback...")
                return self._fallback_extract(event_description, parsed_interests, limit)
        else:
            return self._fallback_extract(event_description, parsed_interests, limit)

    def _fallback_extract(self, event_description: str, parsed_interests: List[str], limit: int) -> List[str]:
        """
        Rule-based fallback theme extraction using regex tokenization and stopword removal.

        Args:
            event_description (str): Description text of the networking event.
            parsed_interests (List[str]): List of parsed user interest strings.
            limit (int): The target count of themes.

        Returns:
            List[str]: Extracted themes based on keyword matching.
        """
        logger.info("Executing rule-based fallback theme extraction.")
        
        # Clean event description to individual words
        cleaned_event = re.sub(r'[^\w\s]', ' ', event_description.lower())
        event_words = set(w.strip() for w in cleaned_event.split() if w.strip() and w.strip() not in STOPWORDS)
        
        themes = []
        
        # 1. Look for user interests that overlap with event description
        for interest in parsed_interests:
            cleaned_interest = interest.lower()
            if cleaned_interest in event_description.lower() or any(w in cleaned_interest for w in event_words):
                if interest not in themes:
                    themes.append(interest)
                    
        # 2. Look for default categories that overlap with event description
        for default_cat in DEFAULT_THEMES:
            cleaned_cat = default_cat.lower()
            if cleaned_cat in event_description.lower() or any(w in cleaned_cat for w in event_words):
                if default_cat not in themes:
                    themes.append(default_cat)
                    
        # Fill rest with user interests directly
        for interest in parsed_interests:
            if len(themes) >= limit:
                break
            if interest not in themes:
                themes.append(interest)
                
        # Fill rest with words from description
        for word in event_words:
            if len(themes) >= limit:
                break
            cap_word = word.capitalize()
            if cap_word not in themes:
                themes.append(cap_word)
                
        # Hard fallback
        if not themes:
            themes = ["Networking", "Professional", "Innovation"]
            
        return themes[:limit]
