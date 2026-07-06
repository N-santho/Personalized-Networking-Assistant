from unittest.mock import patch, MagicMock
from backend.services.theme_extractor import ThemeExtractor

def test_theme_extractor_zero_shot():
    """
    Tests that ThemeExtractor parses the output of the zero-shot classification model
    correctly when the pipeline returns high-confidence predictions.
    """
    mock_pipeline = MagicMock()
    # Mock return values for zero-shot classification
    mock_pipeline.return_value = {
        "labels": ["AI", "Sustainability", "Urban Planning", "Finance"],
        "scores": [0.95, 0.88, 0.82, 0.05]
    }
    
    extractor = ThemeExtractor()
    extractor.pipeline = mock_pipeline
    extractor._initialized = True  # Avoid loading the real model

    themes = extractor.extract_themes(
        event_description="AI for Sustainable Cities",
        interests="Climate Change, Urban Planning",
        limit=3
    )
    
    # Assert top 3 sorted themes with score > 0.15 are returned
    assert len(themes) == 3
    assert "AI" in themes
    assert "Sustainability" in themes
    assert "Urban Planning" in themes
    assert "Finance" not in themes

def test_theme_extractor_fallback():
    """
    Tests that ThemeExtractor successfully falls back to regex-based extraction
    when pipeline loading or execution fails.
    """
    extractor = ThemeExtractor()
    
    # Patch initialize_model to simulate failure/offline mode
    with patch.object(extractor, 'initialize_model', return_value=False):
        themes = extractor.extract_themes(
            event_description="AI for Sustainable Cities",
            interests="Climate Change, Urban Planning",
            limit=3
        )
        
        # Verify fallback logic handles capitalization and overlap
        assert len(themes) <= 3
        # "Climate Change" or "Urban Planning" should be in the extracted list as interests
        assert any(t in ["Climate Change", "Urban Planning", "AI", "Sustainability", "Urban Planning"] for t in themes)
        assert len(themes) > 0
