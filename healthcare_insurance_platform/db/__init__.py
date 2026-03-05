"""Database configuration and models."""

from healthcare_insurance_platform.db.ombudsman_offices import (
    OmbudsmanOfficeDatabase,
    ombudsman_db,
    OMBUDSMAN_OFFICES,
)

__all__ = [
    'OmbudsmanOfficeDatabase',
    'ombudsman_db',
    'OMBUDSMAN_OFFICES',
]
