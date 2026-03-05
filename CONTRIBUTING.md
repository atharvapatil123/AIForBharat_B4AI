# Contributing to Healthcare Insurance Intelligence Platform

Thank you for your interest in contributing to the Healthcare Insurance Intelligence Platform!

## Development Setup

1. Clone the repository
2. Run the setup script:
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```
3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

## Development Workflow

### Running the Application

```bash
# Start development server
make dev

# Or with Docker Compose
docker-compose up
```

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run property-based tests only
make test-prop

# Run with coverage report
pytest --cov=healthcare_insurance_platform --cov-report=html
```

### Code Quality

Before submitting a pull request, ensure your code passes all quality checks:

```bash
# Format code
make format

# Run linters
make lint

# Run type checking
mypy healthcare_insurance_platform/
```

## Testing Guidelines

### Unit Tests

- Write unit tests for specific examples and edge cases
- Use descriptive test names that explain what is being tested
- Mark unit tests with `@pytest.mark.unit`
- Focus on integration points and known edge cases

### Property-Based Tests

- Write property tests for universal correctness guarantees
- Use Hypothesis library for property-based testing
- Each property test must run minimum 100 iterations
- Include property reference in test docstring
- Mark property tests with `@pytest.mark.property`

Example:
```python
from hypothesis import given, strategies as st
import pytest

@pytest.mark.property
@given(st.text(), st.text())
def test_property_example(text1: str, text2: str):
    """Test property X from design document.
    
    Feature: healthcare-insurance-intelligence, Property 3: Language consistency
    """
    # Test implementation
    pass
```

## Code Style

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Use meaningful variable names

## Commit Messages

- Use clear and descriptive commit messages
- Start with a verb in present tense (Add, Fix, Update, etc.)
- Reference issue numbers when applicable

Example:
```
Add claim prediction service

- Implement acceptance probability calculation
- Add document requirement generator
- Include unit and property tests

Refs: #123
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with appropriate tests
3. Ensure all tests pass and code quality checks succeed
4. Update documentation if needed
5. Submit a pull request with a clear description
6. Address review feedback

## Project Structure

```
healthcare_insurance_platform/
├── api/          # API endpoints and routing
├── core/         # Core infrastructure (config, logging, errors)
├── models/       # Data models and schemas
├── services/     # Business logic services
├── db/           # Database configuration
├── utils/        # Utility functions
└── tests/        # Test suite
```

## Questions?

If you have questions or need help, please open an issue or reach out to the maintainers.
