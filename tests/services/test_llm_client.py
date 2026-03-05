"""Unit tests for LLM client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from healthcare_insurance_platform.core.errors import LLMError, LLMProviderError
from healthcare_insurance_platform.services.llm_client import (
    LLMClient,
    LLMProvider,
    LLMResponse,
    PromptTemplate,
)


class TestPromptTemplate:
    """Tests for PromptTemplate."""
    
    def test_template_format_success(self):
        """Test successful template formatting."""
        template = PromptTemplate(
            name="test_template",
            system_message="You are a helpful assistant.",
            user_template="Hello {name}, you are {age} years old.",
            variables=["name", "age"],
        )
        
        system, user = template.format(name="Alice", age=30)
        
        assert system == "You are a helpful assistant."
        assert user == "Hello Alice, you are 30 years old."
    
    def test_template_format_missing_variable(self):
        """Test template formatting with missing variable."""
        template = PromptTemplate(
            name="test_template",
            system_message="System message",
            user_template="Hello {name}",
            variables=["name"],
        )
        
        with pytest.raises(ValueError, match="Missing required variables"):
            template.format()
    
    def test_template_format_extra_variables(self):
        """Test template formatting with extra variables (should work)."""
        template = PromptTemplate(
            name="test_template",
            system_message="System",
            user_template="Hello {name}",
            variables=["name"],
        )
        
        system, user = template.format(name="Bob", extra="ignored")
        assert user == "Hello Bob"


class TestLLMClient:
    """Tests for LLMClient."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('healthcare_insurance_platform.services.llm_client.get_settings') as mock:
            settings = MagicMock()
            settings.llm_provider = "openai"
            settings.openai_api_key = "test-key"
            settings.anthropic_api_key = ""
            settings.llm_model = "gpt-4"
            settings.llm_temperature = 0.7
            settings.llm_max_tokens = 2000
            settings.llm_timeout = 60
            settings.llm_max_retries = 3
            settings.local_llm_url = "http://localhost:8080"
            settings.local_llm_model = "llama2"
            mock.return_value = settings
            yield settings
    
    @patch('healthcare_insurance_platform.services.llm_client.ChatOpenAI')
    def test_initialize_openai_client(self, mock_chat_openai, mock_settings):
        """Test OpenAI client initialization."""
        client = LLMClient(provider=LLMProvider.OPENAI)
        
        assert client.provider == LLMProvider.OPENAI
        assert client.model == "gpt-4"
        mock_chat_openai.assert_called_once()
    
    @patch('healthcare_insurance_platform.services.llm_client.ChatAnthropic')
    def test_initialize_anthropic_client(self, mock_chat_anthropic, mock_settings):
        """Test Anthropic client initialization."""
        mock_settings.llm_provider = "anthropic"
        mock_settings.anthropic_api_key = "test-anthropic-key"
        
        client = LLMClient(provider=LLMProvider.ANTHROPIC)
        
        assert client.provider == LLMProvider.ANTHROPIC
        mock_chat_anthropic.assert_called_once()
    
    @patch('healthcare_insurance_platform.services.llm_client.ChatOpenAI')
    def test_initialize_local_client(self, mock_chat_openai, mock_settings):
        """Test local model client initialization."""
        client = LLMClient(provider=LLMProvider.LOCAL)
        
        assert client.provider == LLMProvider.LOCAL
        mock_chat_openai.assert_called_once()
        # Verify it was called with local URL
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs['base_url'] == "http://localhost:8080"
    
    def test_initialize_missing_api_key(self, mock_settings):
        """Test initialization fails with missing API key."""
        mock_settings.openai_api_key = ""
        
        with pytest.raises(LLMProviderError, match="OpenAI API key not configured"):
            LLMClient(provider=LLMProvider.OPENAI)
    
    @patch('healthcare_insurance_platform.services.llm_client.ChatOpenAI')
    def test_register_template(self, mock_chat_openai, mock_settings):
        """Test template registration."""
        client = LLMClient()
        
        template = PromptTemplate(
            name="test",
            system_message="System",
            user_template="User {var}",
            variables=["var"],
        )
        
        client.register_template(template)
        
        retrieved = client.get_template("test")
        assert retrieved.name == "test"
    
    @patch('healthcare_insurance_platform.services.llm_client.ChatOpenAI')
    def test_get_template_not_found(self, mock_chat_openai, mock_settings):
        """Test getting non-existent template."""
        client = LLMClient()
        
        with pytest.raises(KeyError, match="Template 'nonexistent' not found"):
            client.get_template("nonexistent")
    
    @patch('healthcare_insurance_platform.services.llm_client.ChatOpenAI')
    @pytest.mark.asyncio
    async def test_generate_success(self, mock_chat_openai, mock_settings):
        """Test successful text generation."""
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = "Generated response"
        mock_response.response_metadata = {
            'token_usage': {'total_tokens': 100},
            'finish_reason': 'stop',
        }
        
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_openai.return_value = mock_client
        
        client = LLMClient()
        response = await client.generate("Test prompt")
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Generated response"
        assert response.tokens_used == 100
        assert response.finish_reason == "stop"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
    
    @patch('healthcare_insurance_platform.services.llm_client.ChatOpenAI')
    @pytest.mark.asyncio
    async def test_generate_with_system_message(self, mock_chat_openai, mock_settings):
        """Test generation with system message."""
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_response.response_metadata = {}
        
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_openai.return_value = mock_client
        
        client = LLMClient()
        await client.generate("User prompt", system_message="System prompt")
        
        # Verify ainvoke was called with both messages
        call_args = mock_client.ainvoke.call_args[0][0]
        assert len(call_args) == 2  # System + User messages
    
    @patch('healthcare_insurance_platform.services.llm_client.ChatOpenAI')
    @pytest.mark.asyncio
    async def test_generate_timeout(self, mock_chat_openai, mock_settings):
        """Test generation timeout handling."""
        import asyncio
        
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_chat_openai.return_value = mock_client
        
        client = LLMClient()
        
        with pytest.raises(LLMError, match="Request timeout"):
            await client.generate("Test prompt")
    
    @patch('healthcare_insurance_platform.services.llm_client.ChatOpenAI')
    @pytest.mark.asyncio
    async def test_generate_from_template(self, mock_chat_openai, mock_settings):
        """Test generation from template."""
        mock_response = MagicMock()
        mock_response.content = "Template response"
        mock_response.response_metadata = {}
        
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_openai.return_value = mock_client
        
        client = LLMClient()
        
        # Register template
        template = PromptTemplate(
            name="greeting",
            system_message="Be friendly",
            user_template="Say hello to {name}",
            variables=["name"],
        )
        client.register_template(template)
        
        # Generate from template
        response = await client.generate_from_template("greeting", name="Alice")
        
        assert response.content == "Template response"
    
    @patch('healthcare_insurance_platform.services.llm_client.ChatOpenAI')
    @pytest.mark.asyncio
    async def test_generate_batch(self, mock_chat_openai, mock_settings):
        """Test batch generation."""
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_response.response_metadata = {}
        
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat_openai.return_value = mock_client
        
        client = LLMClient()
        
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        responses = await client.generate_batch(prompts)
        
        assert len(responses) == 3
        assert all(isinstance(r, LLMResponse) for r in responses)
    
    @patch('healthcare_insurance_platform.services.llm_client.ChatOpenAI')
    def test_estimate_tokens(self, mock_chat_openai, mock_settings):
        """Test token estimation."""
        client = LLMClient()
        
        text = "This is a test string with some words"
        tokens = client.estimate_tokens(text)
        
        # Should be roughly len(text) / 4
        assert tokens > 0
        assert tokens == len(text) // 4
    
    @patch('healthcare_insurance_platform.services.llm_client.ChatOpenAI')
    @pytest.mark.asyncio
    async def test_generate_error_handling(self, mock_chat_openai, mock_settings):
        """Test error handling during generation."""
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(side_effect=Exception("API Error"))
        mock_chat_openai.return_value = mock_client
        
        client = LLMClient()
        
        with pytest.raises(LLMError, match="Failed to generate response"):
            await client.generate("Test prompt")
    
    @patch('healthcare_insurance_platform.services.llm_client.ChatOpenAI')
    def test_custom_parameters(self, mock_chat_openai, mock_settings):
        """Test client initialization with custom parameters."""
        client = LLMClient(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=1000,
            timeout=30,
            max_retries=5,
        )
        
        assert client.model == "gpt-3.5-turbo"
        assert client.temperature == 0.5
        assert client.max_tokens == 1000
        assert client.timeout == 30
        assert client.max_retries == 5
