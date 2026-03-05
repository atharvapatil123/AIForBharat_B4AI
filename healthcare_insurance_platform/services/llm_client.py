"""LLM client with support for multiple providers and robust error handling."""

import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from healthcare_insurance_platform.core.config import get_settings
from healthcare_insurance_platform.core.errors import LLMError, LLMProviderError
from healthcare_insurance_platform.core.logging import get_logger


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class LLMResponse(BaseModel):
    """Response from LLM with metadata."""
    
    content: str = Field(description="Generated text content")
    confidence_score: Optional[float] = Field(
        default=None,
        description="Confidence level (0-1) if available"
    )
    model: str = Field(description="Model used for generation")
    provider: str = Field(description="Provider used")
    tokens_used: Optional[int] = Field(
        default=None,
        description="Number of tokens used"
    )
    finish_reason: Optional[str] = Field(
        default=None,
        description="Reason for completion"
    )


class PromptTemplate(BaseModel):
    """Template for LLM prompts."""
    
    name: str = Field(description="Template identifier")
    system_message: str = Field(description="System prompt")
    user_template: str = Field(description="User message template with placeholders")
    variables: List[str] = Field(
        default_factory=list,
        description="List of variable names in template"
    )
    
    def format(self, **kwargs) -> tuple[str, str]:
        """Format template with provided variables.
        
        Args:
            **kwargs: Variable values to substitute
            
        Returns:
            Tuple of (system_message, formatted_user_message)
            
        Raises:
            ValueError: If required variables are missing
        """
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        
        user_message = self.user_template.format(**kwargs)
        return self.system_message, user_message


class LLMClient:
    """Client for interacting with various LLM providers.
    
    Supports OpenAI, Anthropic, and local models with:
    - Automatic retry logic with exponential backoff
    - Error handling and fallback mechanisms
    - Prompt template management
    - Response validation and metadata extraction
    """
    
    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """Initialize LLM client.
        
        Args:
            provider: LLM provider to use (defaults to config)
            model: Model name (defaults to config)
            temperature: Sampling temperature (defaults to config)
            max_tokens: Maximum tokens to generate (defaults to config)
            timeout: Request timeout in seconds (defaults to config)
            max_retries: Maximum retry attempts (defaults to config)
        """
        self.settings = get_settings()
        self.logger = get_logger(self.__class__.__name__)
        
        # Use provided values or fall back to config
        self.provider = provider or LLMProvider(self.settings.llm_provider)
        self.model = model or self.settings.llm_model
        self.temperature = temperature if temperature is not None else self.settings.llm_temperature
        self.max_tokens = max_tokens or self.settings.llm_max_tokens
        self.timeout = timeout or self.settings.llm_timeout
        self.max_retries = max_retries or self.settings.llm_max_retries
        
        # Initialize the appropriate LLM client
        self._client = self._initialize_client()
        
        # Template registry
        self._templates: Dict[str, PromptTemplate] = {}
        
        self.logger.info(
            "LLM client initialized",
            provider=self.provider.value,
            model=self.model,
        )
    
    def _initialize_client(self) -> Any:
        """Initialize the LLM client based on provider.
        
        Returns:
            Initialized LangChain chat model
            
        Raises:
            LLMProviderError: If provider initialization fails
        """
        try:
            if self.provider == LLMProvider.OPENAI:
                if not self.settings.openai_api_key:
                    raise LLMProviderError("OpenAI API key not configured")
                
                return ChatOpenAI(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout,
                    api_key=self.settings.openai_api_key,
                )
            
            elif self.provider == LLMProvider.ANTHROPIC:
                if not self.settings.anthropic_api_key:
                    raise LLMProviderError("Anthropic API key not configured")
                
                return ChatAnthropic(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout,
                    anthropic_api_key=self.settings.anthropic_api_key,
                )
            
            elif self.provider == LLMProvider.LOCAL:
                # For local models, use OpenAI-compatible API
                return ChatOpenAI(
                    model=self.settings.local_llm_model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout,
                    base_url=self.settings.local_llm_url,
                    api_key="not-needed",  # Local models typically don't need API keys
                )
            
            else:
                raise LLMProviderError(f"Unsupported provider: {self.provider}")
        
        except Exception as e:
            self.logger.error(
                "Failed to initialize LLM client",
                provider=self.provider.value,
                error=str(e),
            )
            raise LLMProviderError(f"Failed to initialize {self.provider.value} client: {e}")
    
    def register_template(self, template: PromptTemplate) -> None:
        """Register a prompt template.
        
        Args:
            template: Template to register
        """
        self._templates[template.name] = template
        self.logger.debug(f"Registered template: {template.name}")
    
    def get_template(self, name: str) -> PromptTemplate:
        """Get a registered template by name.
        
        Args:
            name: Template name
            
        Returns:
            Prompt template
            
        Raises:
            KeyError: If template not found
        """
        if name not in self._templates:
            raise KeyError(f"Template '{name}' not found")
        return self._templates[name]
    
    @retry(
        retry=retry_if_exception_type((asyncio.TimeoutError, ConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate text from prompt with retry logic.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            **kwargs: Additional parameters for the LLM
            
        Returns:
            LLM response with metadata
            
        Raises:
            LLMError: If generation fails after retries
        """
        try:
            messages: List[BaseMessage] = []
            
            if system_message:
                messages.append(SystemMessage(content=system_message))
            
            messages.append(HumanMessage(content=prompt))
            
            self.logger.debug(
                "Generating LLM response",
                provider=self.provider.value,
                model=self.model,
                prompt_length=len(prompt),
            )
            
            # Generate response
            response = await self._client.ainvoke(messages, **kwargs)
            
            # Extract metadata
            tokens_used = None
            finish_reason = None
            
            if hasattr(response, 'response_metadata'):
                metadata = response.response_metadata
                if 'token_usage' in metadata:
                    tokens_used = metadata['token_usage'].get('total_tokens')
                finish_reason = metadata.get('finish_reason')
            
            llm_response = LLMResponse(
                content=response.content,
                model=self.model,
                provider=self.provider.value,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
            )
            
            self.logger.info(
                "LLM response generated",
                provider=self.provider.value,
                model=self.model,
                tokens_used=tokens_used,
                response_length=len(response.content),
            )
            
            return llm_response
        
        except asyncio.TimeoutError as e:
            self.logger.error(
                "LLM request timeout",
                provider=self.provider.value,
                timeout=self.timeout,
            )
            raise LLMError(f"Request timeout after {self.timeout}s") from e
        
        except Exception as e:
            self.logger.error(
                "LLM generation failed",
                provider=self.provider.value,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise LLMError(f"Failed to generate response: {e}") from e
    
    async def generate_from_template(
        self,
        template_name: str,
        **variables,
    ) -> LLMResponse:
        """Generate text using a registered template.
        
        Args:
            template_name: Name of registered template
            **variables: Variables to substitute in template
            
        Returns:
            LLM response with metadata
            
        Raises:
            KeyError: If template not found
            ValueError: If required variables missing
            LLMError: If generation fails
        """
        template = self.get_template(template_name)
        system_message, user_message = template.format(**variables)
        
        return await self.generate(
            prompt=user_message,
            system_message=system_message,
        )
    
    async def generate_batch(
        self,
        prompts: List[str],
        system_message: Optional[str] = None,
        **kwargs,
    ) -> List[LLMResponse]:
        """Generate responses for multiple prompts concurrently.
        
        Args:
            prompts: List of user prompts
            system_message: Optional system message for all prompts
            **kwargs: Additional parameters for the LLM
            
        Returns:
            List of LLM responses
            
        Raises:
            LLMError: If any generation fails
        """
        tasks = [
            self.generate(prompt, system_message, **kwargs)
            for prompt in prompts
        ]
        
        return await asyncio.gather(*tasks)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.
        
        This is a rough estimate: ~4 characters per token for English.
        For production, use tiktoken or similar for accurate counts.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
