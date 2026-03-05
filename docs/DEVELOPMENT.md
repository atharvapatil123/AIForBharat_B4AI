# Development Guide

## Quick Start

```bash
# Clone and setup
git clone <repository>
cd healthcare-insurance-platform
./scripts/setup.sh

# Activate virtual environment
source venv/bin/activate

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start database
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Start development server
make dev
```

## Development Commands

### Application

```bash
# Start development server with auto-reload
make dev

# Start with Docker Compose
docker-compose up

# Stop Docker services
docker-compose down
```

### Testing

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run property-based tests only
make test-prop

# Run with coverage
pytest --cov=healthcare_insurance_platform --cov-report=html

# Run specific test file
pytest tests/core/test_errors.py

# Run tests matching pattern
pytest -k "test_validation"
```

### Code Quality

```bash
# Format code with black
make format

# Run linters
make lint

# Type checking
mypy healthcare_insurance_platform/

# All quality checks
make format && make lint && mypy healthcare_insurance_platform/
```

### Database

```bash
# Create new migration
make migration
# Or: alembic revision --autogenerate -m "description"

# Apply migrations
make migrate
# Or: alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

### Cleanup

```bash
# Remove temporary files
make clean

# Remove virtual environment
rm -rf venv/

# Remove database data (Docker)
docker-compose down -v
```

## Project Structure

### Adding New Components

#### 1. Adding a New Service

```python
# healthcare_insurance_platform/services/my_service.py
from healthcare_insurance_platform.services.base import BaseService

class MyService(BaseService):
    """Description of service."""
    
    async def my_method(self, param: str) -> dict:
        """Method description."""
        self._log_operation("my_method", param=param)
        try:
            # Implementation
            result = {"data": param}
            return result
        except Exception as e:
            self._log_error("my_method", e, param=param)
            raise
```

#### 2. Adding a New API Endpoint

```python
# healthcare_insurance_platform/api/my_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from healthcare_insurance_platform.db.base import get_db
from healthcare_insurance_platform.services.my_service import MyService

router = APIRouter()

@router.post("/my-endpoint")
async def my_endpoint(
    param: str,
    db: AsyncSession = Depends(get_db),
):
    """Endpoint description."""
    service = MyService(db=db)
    result = await service.my_method(param)
    return result
```

Then register in `main.py`:
```python
from healthcare_insurance_platform.api.my_router import router as my_router
app.include_router(my_router, prefix="/api/v1/my", tags=["my"])
```

#### 3. Adding a New Data Model

```python
# healthcare_insurance_platform/models/my_model.py
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    """Model description."""
    
    field1: str = Field(..., description="Field description")
    field2: int = Field(default=0, ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "field1": "example",
                "field2": 42,
            }
        }
```

#### 4. Adding Tests

Unit test:
```python
# tests/services/test_my_service.py
import pytest
from healthcare_insurance_platform.services.my_service import MyService

@pytest.mark.unit
async def test_my_method():
    """Test my_method with specific input."""
    service = MyService()
    result = await service.my_method("test")
    assert result["data"] == "test"
```

Property test:
```python
from hypothesis import given, strategies as st

@pytest.mark.property
@given(st.text())
async def test_my_method_property(text: str):
    """Test my_method with any text input.
    
    Feature: healthcare-insurance-intelligence, Property X: Description
    """
    service = MyService()
    result = await service.my_method(text)
    assert "data" in result
```

## Common Tasks

### Adding a New Dependency

1. Add to `requirements.txt`
2. Install: `pip install -r requirements.txt`
3. Update Docker image: `docker-compose build`

### Debugging

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()

# Run tests with debugging
pytest --pdb
```

### Viewing Logs

```bash
# Development server logs
# Logs appear in console

# Docker logs
docker-compose logs -f app

# Specific service logs
docker-compose logs -f postgres
```

### Database Operations

```python
# In Python shell or script
from healthcare_insurance_platform.db.base import AsyncSessionLocal

async def example():
    async with AsyncSessionLocal() as session:
        # Your database operations
        result = await session.execute(query)
        await session.commit()
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Test Failures

```bash
# Run with verbose output
pytest -vv

# Run with print statements
pytest -s

# Run specific test with debugging
pytest tests/test_file.py::test_name --pdb
```

## Best Practices

1. **Always write tests** for new functionality
2. **Use type hints** for all function signatures
3. **Write docstrings** for public functions and classes
4. **Log important operations** using the logger
5. **Handle errors gracefully** with appropriate exceptions
6. **Keep functions small** and focused
7. **Use async/await** for I/O operations
8. **Validate inputs** with Pydantic models
9. **Follow the existing code structure**
10. **Update documentation** when adding features

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
