# LLM Integration Documentation

## Overview

The Healthcare Insurance Intelligence Platform includes a flexible LLM (Large Language Model) integration that supports multiple providers with robust error handling, retry logic, and prompt template management.

## Supported Providers

The platform supports three LLM providers:

1. **OpenAI** - GPT-4, GPT-3.5-turbo, and other OpenAI models
2. **Anthropic** - Claude models (Claude-3, Claude-2, etc.)
3. **Local Models** - Any OpenAI-compatible local model (e.g., Ollama, LM Studio)

## Architecture

### Components

#### 1. LLMClient (`healthcare_insurance_platform/services/llm_client.py`)

The core client for interacting with LLM providers.

**Key Features:**
- Multi-provider support (OpenAI, Anthropic, local models)
- Automatic retry logic with exponential backoff
- Prompt template management
- Response validation and metadata extraction
- Batch generation support
- Token estimation

**Main Classes:**
- `LLMProvider`: Enum for supported providers
- `LLMResponse`: Response model with metadata
- `PromptTemplate`: Template for managing prompts
- `LLMClient`: Main client class

**Example Usage:**

```python
from healthcare_insurance_platform.services import LLMClient, LLMProvider

# Initialize client
client = LLMClient(
    provider=LLMProvider.OPENAI,
    model="gpt-4-turbo-preview",
    temperature=0.7,
)

# Generate response
response = await client.generate(
    prompt="Explain this insurance policy in simple terms",
    system_message="You are an expert insurance advisor",
)

print(response.content)
print(f"Tokens used: {response.tokens_used}")
```

#### 2. LLMEngine (`healthcare_insurance_platform/services/llm_engine.py`)

Orchestration engine that manages prompts, context assembly, and response generation.

**Key Features:**
- Context assembly from knowledge base
- Citation tracking
- Explanation generation
- Default prompt templates for common tasks
- Fallback mechanisms

**Main Classes:**
- `ContextDocument`: Document from knowledge base
- `ContextBundle`: Collection of context documents
- `Citation`: Source citation for responses
- `EnhancedLLMResponse`: Response with citations and explanations
- `LLMEngine`: Main orchestration engine

**Example Usage:**

```python
from healthcare_insurance_platform.services import LLMEngine

# Initialize engine
engine = LLMEngine(vector_store=vector_store)

# Assemble context from knowledge base
context = await engine.assemble_context(
    query="What does this policy cover?",
    max_documents=5,
)

# Generate response with context
response = await engine.generate_response(
    prompt="Explain the coverage details",
    context=context,
)

print(response.content)
for citation in response.citations:
    print(f"Source: {citation.document_id}")
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# LLM Provider Selection
LLM_PROVIDER=openai  # Options: openai, anthropic, local

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Model Configuration
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=60
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY=1.0

# Local LLM Configuration (for local models)
LOCAL_LLM_URL=http://localhost:8080
LOCAL_LLM_MODEL=llama2
```

### Configuration Class

The `Settings` class in `healthcare_insurance_platform/core/config.py` manages all LLM configuration:

```python
from healthcare_insurance_platform.core.config import get_settings

settings = get_settings()
print(f"Provider: {settings.llm_provider}")
print(f"Model: {settings.llm_model}")
```

## Prompt Templates

The LLM engine includes default templates for common tasks:

### 1. Policy Comparison Template

Used for comparing insurance policies.

```python
response = await engine.generate_from_template(
    "policy_comparison",
    user_profile="Age: 35, PED: Diabetes",
    policies="Policy A: ...\nPolicy B: ...",
)
```

### 2. Claim Prediction Template

Used for predicting claim acceptance probability.

```python
response = await engine.generate_from_template(
    "claim_prediction",
    claim_details="Hospitalization for surgery",
    policy_terms="Policy coverage details...",
)
```

### 3. Policy Explanation Template

Used for explaining complex policy terms.

```python
response = await engine.generate_from_template(
    "policy_explanation",
    policy_content="Policy document text...",
)
```

### 4. Medical Summary Template

Used for summarizing patient medical history.

```python
response = await engine.generate_from_template(
    "medical_summary",
    medical_records="Patient records...",
)
```

### Custom Templates

You can register custom templates:

```python
from healthcare_insurance_platform.services import PromptTemplate

template = PromptTemplate(
    name="custom_analysis",
    system_message="You are an expert analyst",
    user_template="Analyze this: {content}",
    variables=["content"],
)

engine.register_template(template)

response = await engine.generate_from_template(
    "custom_analysis",
    content="Data to analyze",
)
```

## Error Handling

The LLM integration includes comprehensive error handling:

### Error Types

1. **LLMProviderError**: Provider initialization or configuration issues
2. **LLMError**: Generation failures, timeouts, or API errors

### Retry Logic

The client automatically retries failed requests with exponential backoff:

- Maximum retries: 3 (configurable)
- Initial delay: 1 second
- Exponential multiplier: 2x
- Maximum delay: 10 seconds

### Fallback Mechanisms

Use fallback responses for critical operations:

```python
response = await engine.generate_with_retry_fallback(
    prompt="Analyze this claim",
    fallback_response="Unable to analyze at this time. Please try again later.",
)
```

## Best Practices

### 1. Provider Selection

- **OpenAI**: Best for general-purpose tasks, good multilingual support
- **Anthropic**: Excellent for long-context tasks, strong reasoning
- **Local**: Best for privacy-sensitive deployments, no API costs

### 2. Temperature Settings

- **0.0-0.3**: Deterministic, factual responses (policy analysis, claims)
- **0.4-0.7**: Balanced creativity and accuracy (explanations, summaries)
- **0.8-1.0**: Creative responses (education content, examples)

### 3. Token Management

```python
# Estimate tokens before generation
estimated = client.estimate_tokens(prompt)
if estimated > 4000:
    # Split or truncate prompt
    pass

# Check actual usage
response = await client.generate(prompt)
print(f"Used {response.tokens_used} tokens")
```

### 4. Context Assembly

```python
# Limit context size to avoid token limits
context = await engine.assemble_context(
    query="user query",
    max_documents=5,  # Limit number of documents
    min_relevance=0.7,  # Filter low-relevance docs
)

# Get context text with token limit
context_text = context.get_context_text(max_tokens=3000)
```

### 5. Batch Processing

For multiple prompts, use batch generation:

```python
prompts = [
    "Explain policy A",
    "Explain policy B",
    "Explain policy C",
]

responses = await client.generate_batch(prompts)
```

## Testing

### Unit Tests

Run LLM client and engine tests:

```bash
# Validation tests (syntax and structure)
python -m pytest tests/services/test_llm_validation.py -v

# Full unit tests (requires compatible Python version)
python -m pytest tests/services/test_llm_client.py -v
python -m pytest tests/services/test_llm_engine.py -v
```

### Integration Tests

Test with actual LLM providers:

```python
import pytest
from healthcare_insurance_platform.services import LLMClient, LLMProvider

@pytest.mark.integration
async def test_openai_integration():
    """Test actual OpenAI API call."""
    client = LLMClient(provider=LLMProvider.OPENAI)
    response = await client.generate("Say hello")
    assert len(response.content) > 0
```

## Monitoring and Logging

The LLM integration includes comprehensive logging:

```python
# Logs include:
# - Provider and model used
# - Token usage
# - Response times
# - Errors and retries

# Example log output:
# INFO: LLM client initialized provider=openai model=gpt-4
# INFO: Generating LLM response prompt_length=150
# INFO: LLM response generated tokens_used=250 response_length=500
```

## Performance Optimization

### 1. Caching

Implement response caching for repeated queries:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def cached_generate(prompt: str):
    return await client.generate(prompt)
```

### 2. Streaming

For long responses, consider streaming (future enhancement):

```python
# Future API
async for chunk in client.generate_stream(prompt):
    print(chunk.content, end="")
```

### 3. Parallel Processing

Use batch generation for independent prompts:

```python
# Processes prompts concurrently
responses = await client.generate_batch(prompts)
```

## Security Considerations

1. **API Key Management**
   - Store keys in environment variables
   - Never commit keys to version control
   - Rotate keys regularly

2. **Input Validation**
   - Validate and sanitize user inputs
   - Limit prompt length to prevent abuse
   - Filter sensitive information

3. **Output Validation**
   - Verify response format and content
   - Check for hallucinations or errors
   - Implement content filtering if needed

4. **Rate Limiting**
   - Implement per-user rate limits
   - Monitor API usage and costs
   - Set up alerts for unusual activity

## Troubleshooting

### Common Issues

#### 1. API Key Not Configured

```
Error: OpenAI API key not configured
Solution: Set OPENAI_API_KEY in .env file
```

#### 2. Timeout Errors

```
Error: Request timeout after 60s
Solution: Increase LLM_TIMEOUT or reduce prompt size
```

#### 3. Token Limit Exceeded

```
Error: Maximum context length exceeded
Solution: Reduce context size or use a model with larger context window
```

#### 4. Provider Initialization Failed

```
Error: Failed to initialize openai client
Solution: Check API key, network connection, and provider status
```

## Future Enhancements

1. **Streaming Support**: Real-time response streaming
2. **Function Calling**: Structured output with function calls
3. **Fine-tuning**: Custom model fine-tuning for domain-specific tasks
4. **Multi-modal**: Support for image and document inputs
5. **Cost Tracking**: Detailed cost monitoring and optimization
6. **A/B Testing**: Compare responses from different providers/models

## References

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic API Documentation](https://docs.anthropic.com)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [Tenacity Retry Documentation](https://tenacity.readthedocs.io/)
