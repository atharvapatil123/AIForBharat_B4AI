# Architecture Overview

## Project Structure

```
healthcare_insurance_platform/
├── api/                          # API endpoints and routing
│   └── __init__.py
├── core/                         # Core infrastructure
│   ├── __init__.py
│   ├── config.py                # Configuration management
│   ├── errors.py                # Error handling and exceptions
│   └── logging.py               # Structured logging setup
├── db/                          # Database layer
│   ├── __init__.py
│   ├── base.py                  # SQLAlchemy base and session management
│   └── vector_store.py          # ChromaDB vector store for policies
├── models/                      # Data models and schemas
│   └── __init__.py
├── services/                    # Business logic services
│   ├── __init__.py
│   └── base.py                  # Base service class
├── utils/                       # Utility functions
│   └── __init__.py
└── main.py                      # FastAPI application entry point
```

## Core Components

### Configuration Management (`core/config.py`)

- Uses Pydantic Settings for type-safe configuration
- Loads settings from environment variables and .env file
- Provides environment-specific configurations (development, testing, production)
- Validates required settings (e.g., OpenAI API key)

### Error Handling (`core/errors.py`)

- Defines custom exception hierarchy for different error types
- Provides standardized error response format
- Includes exception handlers for FastAPI
- Error types: Validation, Availability, Processing, Business Logic, Security

### Logging (`core/logging.py`)

- Uses structlog for structured logging
- Supports JSON and console output formats
- Configurable log levels
- Includes context information in logs

### Database Layer (`db/`)

- **base.py**: SQLAlchemy async engine and session management
- **vector_store.py**: ChromaDB integration for policy document storage and semantic search
- Supports both structured data (PostgreSQL) and vector embeddings

### Services (`services/`)

- **base.py**: Base service class with common functionality
- All services inherit from BaseService
- Provides logging, database access, and vector store access

## Configuration

### Environment Variables

Key environment variables (see `.env.example`):

- `ENVIRONMENT`: development, testing, or production
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key for LLM integration
- `CHROMA_PERSIST_DIRECTORY`: ChromaDB data directory
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Database Configuration

- **Primary Database**: PostgreSQL for structured data
- **Vector Database**: ChromaDB for policy document embeddings
- **Migrations**: Alembic for database schema management

## Development Workflow

### Setup

1. Run setup script: `./scripts/setup.sh`
2. Configure `.env` file
3. Start PostgreSQL: `docker-compose up -d postgres`
4. Run migrations: `alembic upgrade head`
5. Start dev server: `make dev`

### Testing

- Unit tests: `make test-unit`
- Property tests: `make test-prop`
- All tests: `make test`
- Coverage report: `pytest --cov=healthcare_insurance_platform --cov-report=html`

### Code Quality

- Format: `make format` (uses black)
- Lint: `make lint` (uses ruff)
- Type check: `mypy healthcare_insurance_platform/`

## API Design

### Endpoint Structure

```
/api/v1/
├── policies/          # Policy comparison and analysis
├── claims/            # Claim prediction and analysis
├── medical/           # Medical summarization and research
├── workflows/         # Workflow automation
└── education/         # Patient education content
```

### Request/Response Format

- All requests validated with Pydantic models
- All responses include proper error handling
- Multilingual support via language parameter
- Structured error responses with error codes

## Security

### Data Protection

- Encryption at rest (database encryption)
- Encryption in transit (TLS)
- Sensitive field encryption in user profiles
- Consent-based data sharing

### Authentication

- JWT-based authentication
- API key management
- Rate limiting per user

### Error Handling

- Secure error messages (no sensitive data leakage)
- Detailed technical logs for debugging
- User-friendly error messages

## Deployment

### Docker

```bash
# Build image
docker build -t healthcare-insurance-platform .

# Run with Docker Compose
docker-compose up
```

### Environment-Specific Configuration

- Development: Debug logging, auto-reload, CORS enabled
- Testing: Test database, mock external services
- Production: Optimized settings, restricted CORS, monitoring

## Monitoring and Logging

### Structured Logging

- All logs in JSON format (production)
- Console format for development
- Context information included (user_id, request_id, etc.)
- Log levels: DEBUG, INFO, WARNING, ERROR

### Health Checks

- `/health`: Application health status
- `/`: Root endpoint with version info

## Next Steps

1. Implement data models (Task 2)
2. Implement Knowledge Base component (Task 3)
3. Implement LLM Orchestration Engine (Task 4)
4. Implement Translation Service (Task 5)
5. Implement domain services (Tasks 7-14)
6. Implement API endpoints (Task 18)
7. Add comprehensive testing (throughout)
