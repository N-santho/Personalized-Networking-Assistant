from unittest.mock import patch, MagicMock
from backend.services.conversation_generator import ConversationGenerator

def test_conversation_generator_model():
    """
    Tests that ConversationGenerator properly parses GPT-2 completions
    into exactly three distinct questions when the model runs successfully.
    """
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    # Mock inputs encoding shape
    mock_tokenizer.return_value = MagicMock(input_ids=MagicMock(shape=[1, 10]))
    
    # Mock return of decoder - containing 3 questions matching standard list patterns
    mock_tokenizer.decode.return_value = (
        " How do you think AI affects smart cities?\n"
        "- What innovations in green tech interest you?\n"
        "* Are there AI models that reduce emission rates?"
    )
    
    generator = ConversationGenerator()
    generator.model = mock_model
    generator.tokenizer = mock_tokenizer
    generator._initialized = True  # Avoid loading real model

    starters = generator.generate_starters(
        event_description="AI for Sustainable Cities",
        themes=["AI", "Sustainability"],
        interests="Climate Change, Urban Planning",
        num_starters=3
    )
    
    assert len(starters) == 3
    assert starters[0] == "How do you think AI affects smart cities?"
    assert starters[1] == "What innovations in green tech interest you?"
    assert starters[2] == "Are there AI models that reduce emission rates?"

def test_conversation_generator_fallback():
    """
    Tests that ConversationGenerator falls back to dynamic templates
    when the model fails to load or execute.
    """
    generator = ConversationGenerator()
    
    with patch.object(generator, 'initialize_model', return_value=False):
        starters = generator.generate_starters(
            event_description="AI for Sustainable Cities",
            themes=["AI", "Sustainability"],
            interests="Climate Change, Urban Planning",
            num_starters=3
        )
        
        # Verify exactly 3 strings are generated
        assert len(starters) == 3
        for s in starters:
            assert isinstance(s, str)
            assert len(s) > 15
            assert s.endswith("?")
