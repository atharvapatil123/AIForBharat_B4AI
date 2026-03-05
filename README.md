# Healthcare Insurance Intelligence Platform

A multilingual AI-powered system designed to help users navigate the entire health insurance journey - from selection to claims.

## Features

- **Insurance Plan Comparison**: Compare health insurance plans across multiple providers
- **Pre-Existing Disease Analysis**: Evaluate how medical history affects insurance options
- **Policy Document Interpretation**: Complex policy documents explained in simple language
- **Multilingual Support**: Support for Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, and English
- **Claim Acceptance Prediction**: Predict likelihood of claim acceptance
- **Medical History Summarization**: Automatic summarization of patient medical history
- **Workflow Automation**: Generate automation solutions from natural language descriptions

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Virtual environment tool (venv or virtualenv)

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and configure your environment variables:
   ```bash
   cp .env.example .env
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the development server:
   ```bash
   uvicorn healthcare_insurance_platform.main:app --reload
   ```

## Project Structure

```
healthcare_insurance_platform/
├── api/                    # API endpoints and routing
├── core/                   # Core infrastructure (config, logging, errors)
├── models/                 # Data models and schemas
├── services/               # Business logic services
├── db/                     # Database configuration and models
├── utils/                  # Utility functions
└── tests/                  # Test suite
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=healthcare_insurance_platform

# Run property-based tests only
pytest -m property

# Run unit tests only
pytest -m unit
```

### Code Quality

```bash
# Format code
black healthcare_insurance_platform/

# Lint code
ruff check healthcare_insurance_platform/

# Type checking
mypy healthcare_insurance_platform/
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

Proprietary - All rights reserved
