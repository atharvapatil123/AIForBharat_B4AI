.PHONY: help install dev test lint format clean run migrate

help:
	@echo "Healthcare Insurance Intelligence Platform - Development Commands"
	@echo ""
	@echo "install     - Install dependencies"
	@echo "dev         - Run development server"
	@echo "test        - Run all tests"
	@echo "test-unit   - Run unit tests only"
	@echo "test-prop   - Run property-based tests only"
	@echo "lint        - Run linters"
	@echo "format      - Format code"
	@echo "clean       - Clean temporary files"
	@echo "migrate     - Run database migrations"
	@echo "migration   - Create new migration"

install:
	pip install -r requirements.txt

dev:
	uvicorn healthcare_insurance_platform.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

test-unit:
	pytest -m unit

test-prop:
	pytest -m property

lint:
	ruff check healthcare_insurance_platform/
	mypy healthcare_insurance_platform/

format:
	black healthcare_insurance_platform/ tests/
	ruff check --fix healthcare_insurance_platform/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".hypothesis" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

migrate:
	alembic upgrade head

migration:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"
