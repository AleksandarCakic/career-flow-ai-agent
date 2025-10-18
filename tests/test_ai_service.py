import pytest
from unittest.mock import Mock, patch

def test_ai_service_generate_response():
    """Test AI service response generation."""
    # Mock at the module level before importing
    with patch('src.services.ai_service.OpenAI') as mock_openai_class:
        # Setup mock response
        mock_message = Mock()
        mock_message.content = "Test AI response"
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        # Mock the client methods
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        from src.services.ai_service import AIService
        service = AIService()
        result = service.generate_response("Test message")
        
        assert result == "Test AI response"
        mock_client.chat.completions.create.assert_called_once()