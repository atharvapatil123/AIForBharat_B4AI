# Policy Versioning System

## Overview

The Policy Versioning System tracks changes to insurance policy documents over time, enabling:

- **Version History Tracking**: Complete audit trail of policy evolution
- **Change Detection**: Automatic identification of changes between versions
- **Impact Analysis**: Classification of changes by impact level (critical, high, medium, low)
- **Affected Analysis Flagging**: Notification system for analyses that need updating
- **Version Comparison**: Side-by-side comparison of any two policy versions

## Architecture

### Components

1. **PolicyVersion Model** (`models/policy_version.py`)
   - Represents a specific version of a policy document
   - Tracks version metadata and changes from previous version
   - Stores snapshot of key policy data

2. **PolicyVersioningService** (`services/policy_versioning.py`)
   - Core service for version management
   - Handles version creation, comparison, and change detection
   - Manages affected analysis flagging

3. **Database Models** (`db/models.py`)
   - `PolicyVersionDB`: Persists version history
   - `AffectedAnalysisDB`: Tracks analyses affected by updates

4. **Knowledge Base Integration** (`services/knowledge_base.py`)
   - Automatic version creation during policy ingestion
   - Version history retrieval
   - Version comparison API

## Key Features

### 1. Automatic Change Detection

When a new policy version is ingested, the system automatically detects:

- **Coverage Changes**: Changes in coverage amount
- **Premium Changes**: Changes in premium amount
- **Exclusion Changes**: Added or removed exclusions
- **Inclusion Changes**: Added or removed coverage items
- **Waiting Period Changes**: Changes in waiting periods
- **Terms Changes**: Changes in PED policy or claim process

### 2. Impact Classification

Each change is classified by impact level:

- **Critical**: Major changes that significantly affect policy value
  - New exclusions added
  - Coverage decreased by >20%
  - PED policy changes
  
- **High**: Important changes requiring attention
  - Coverage increased by >10%
  - Premium increased by >20%
  - New coverage added
  - Exclusions removed
  
- **Medium**: Moderate changes
  - Coverage changes 5-10%
  - Premium changes 10-20%
  
- **Low**: Minor changes
  - Small adjustments
  - Text clarifications

### 3. Affected Analysis Flagging

When a policy is updated with critical or high-impact changes:

1. System identifies all analyses using the old version
2. Creates `AffectedAnalysis` records for each
3. Flags analyses for user notification
4. Provides details on what changed and why reanalysis is needed

## Usage Examples

### Creating a Version

```python
from healthcare_insurance_platform.services.policy_versioning import PolicyVersioningService

# Initialize service
versioning_service = PolicyVersioningService(db_session=session)

# Create version (automatically done during ingestion)
version = await versioning_service.create_version(
    policy_document=new_policy,
    previous_version=old_policy,  # Optional
    created_by="admin"
)

# Check for critical changes
if version.has_critical_changes():
    print("Policy has critical changes requiring user notification")
```

### Comparing Versions

```python
# Compare two versions
comparison = await versioning_service.compare_versions(
    policy_id="policy-123",
    old_version_number="1.0",
    new_version_number="2.0"
)

print(f"Total changes: {len(comparison.changes)}")
print(f"Affects analyses: {comparison.affects_existing_analyses}")

# Get critical changes
critical = comparison.get_critical_changes()
for change in critical:
    print(f"- {change.description}")
```

### Getting Version History

```python
# Get complete version history
history = await versioning_service.get_version_history("policy-123")

print(f"Total versions: {len(history.versions)}")

# Get current version
current = history.get_current_version()
print(f"Current version: {current.version_number}")

# Get versions since a date
recent = history.get_versions_since(datetime(2024, 1, 1))
```

### Flagging Affected Analyses

```python
# Flag analyses affected by update
affected = await versioning_service.flag_affected_analyses(
    policy_id="policy-123",
    new_version=version,
    analysis_ids=["analysis-1", "analysis-2", "analysis-3"]
)

print(f"Flagged {len(affected)} analyses")

# Check which require reanalysis
for analysis in affected:
    if analysis.requires_reanalysis():
        print(f"Analysis {analysis.analysis_id} requires reanalysis")
```

### Knowledge Base Integration

```python
from healthcare_insurance_platform.services.knowledge_base import KnowledgeBaseService

kb_service = KnowledgeBaseService(db_session=session)

# Ingest new version (versioning happens automatically)
policy = await kb_service.ingest_policy_document(
    file_path=Path("policy_v2.pdf"),
    provider_id="star-health",
    policy_name="Health Plus",
    policy_type="individual",
    version="2.0",
    effective_date=date(2024, 7, 1),
    previous_policy=old_policy,  # For change detection
    created_by="admin"
)

# Get version history
history = await kb_service.get_policy_version_history("policy-123")

# Compare versions
comparison = await kb_service.compare_policy_versions(
    policy_id="policy-123",
    old_version="1.0",
    new_version="2.0"
)

# Get affected analyses
affected = await kb_service.get_affected_analyses(
    policy_id="policy-123",
    user_id="user-456"  # Optional filter
)
```

## Data Models

### PolicyVersion

```python
{
    "version_id": "uuid",
    "policy_id": "policy-123",
    "version_number": "2.0",
    "effective_date": "2024-07-01T00:00:00Z",
    "created_at": "2024-06-15T10:30:00Z",
    "created_by": "admin",
    "coverage_amount": 750000.0,
    "premium": 18500.0,
    "exclusions_count": 4,
    "inclusions_count": 6,
    "changes_from_previous": [
        {
            "change_type": "coverage_change",
            "field_name": "coverage_amount",
            "old_value": "Rs. 500,000",
            "new_value": "Rs. 750,000",
            "description": "Coverage increased by 50%",
            "impact_level": "critical"
        }
    ],
    "is_current": true
}
```

### VersionComparison

```python
{
    "policy_id": "policy-123",
    "policy_name": "Health Plus",
    "old_version": "1.0",
    "new_version": "2.0",
    "old_effective_date": "2024-01-01T00:00:00Z",
    "new_effective_date": "2024-07-01T00:00:00Z",
    "changes": [...],
    "summary": "Total changes: 5. 2 critical changes. 3 high impact changes...",
    "affects_existing_analyses": true
}
```

### AffectedAnalysis

```python
{
    "analysis_id": "analysis-123",
    "analysis_type": "claim_prediction",
    "user_id": "user-456",
    "created_at": "2024-05-01T00:00:00Z",
    "policy_id": "policy-123",
    "old_version": "1.0",
    "new_version": "2.0",
    "affected_by_changes": [...],
    "flagged_at": "2024-07-01T00:00:00Z",
    "notification_sent": false
}
```

## Change Types

| Change Type | Description | Typical Impact |
|-------------|-------------|----------------|
| `coverage_change` | Coverage amount modified | Critical (>20%), High (>10%), Medium |
| `premium_change` | Premium amount modified | High (>20%), Medium (>10%), Low |
| `exclusion_added` | New exclusion added | Critical |
| `exclusion_removed` | Exclusion removed | High |
| `inclusion_added` | New coverage added | High |
| `inclusion_removed` | Coverage removed | Critical |
| `waiting_period_change` | Waiting periods modified | High |
| `terms_change` | Policy terms modified | Critical/High |
| `minor_update` | Minor text changes | Low |

## Best Practices

### 1. Always Provide Previous Version

When ingesting an updated policy, always provide the previous version for accurate change detection:

```python
policy = await kb_service.ingest_policy_document(
    ...,
    previous_policy=old_policy,  # Important!
    created_by="admin"
)
```

### 2. Check for Critical Changes

After creating a version, check for critical changes that require immediate action:

```python
if version.has_critical_changes():
    # Send notifications
    # Flag affected analyses
    # Update documentation
```

### 3. Regular Version Audits

Periodically review version history to understand policy evolution:

```python
history = await versioning_service.get_version_history(policy_id)
for version in history.versions:
    if version.has_high_impact_changes():
        # Review and document
```

### 4. User Notifications

When analyses are flagged as affected:

```python
affected = await kb_service.get_affected_analyses(policy_id, user_id)
for analysis in affected:
    if analysis.requires_reanalysis():
        # Send notification to user
        # Provide comparison link
        # Suggest reanalysis
```

## Database Schema

### policy_versions Table

```sql
CREATE TABLE policy_versions (
    id INTEGER PRIMARY KEY,
    version_id VARCHAR(255) UNIQUE NOT NULL,
    policy_id VARCHAR(255) NOT NULL,
    version_number VARCHAR(50) NOT NULL,
    effective_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_by VARCHAR(255),
    coverage_amount FLOAT NOT NULL,
    premium FLOAT NOT NULL,
    exclusions_count INTEGER NOT NULL,
    inclusions_count INTEGER NOT NULL,
    changes_from_previous JSON NOT NULL,
    document_snapshot TEXT,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX idx_policy_id (policy_id),
    INDEX idx_version_id (version_id)
);
```

### affected_analyses Table

```sql
CREATE TABLE affected_analyses (
    id INTEGER PRIMARY KEY,
    analysis_id VARCHAR(255) UNIQUE NOT NULL,
    analysis_type VARCHAR(100) NOT NULL,
    user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    policy_id VARCHAR(255) NOT NULL,
    old_version VARCHAR(50) NOT NULL,
    new_version VARCHAR(50) NOT NULL,
    affected_by_changes JSON NOT NULL,
    flagged_at TIMESTAMP WITH TIME ZONE NOT NULL,
    notification_sent BOOLEAN NOT NULL DEFAULT FALSE,
    policy_version_id INTEGER,
    INDEX idx_policy_id (policy_id),
    INDEX idx_user_id (user_id),
    INDEX idx_analysis_id (analysis_id),
    FOREIGN KEY (policy_version_id) REFERENCES policy_versions(id)
);
```

## Testing

Run the versioning tests:

```bash
# Simple unit tests
PYTHONPATH=. python tests/services/test_policy_versioning_simple.py

# Integration test with workflow demo
PYTHONPATH=. python tests/services/test_knowledge_base_versioning_integration.py
```

## Requirements Validation

This implementation validates:

- **Requirement 12.3**: Version history tracking for policy documents
- **Requirement 12.4**: Version comparison and affected analysis flagging

## Future Enhancements

1. **Automated Notifications**: Email/SMS notifications for affected users
2. **Version Rollback**: Ability to revert to previous versions
3. **Diff Visualization**: Visual diff tool for comparing versions
4. **Bulk Operations**: Batch version creation and comparison
5. **Analytics**: Version change analytics and trends
6. **API Endpoints**: REST API for version management
