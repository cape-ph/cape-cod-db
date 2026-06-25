# Database Models

## Architecture

All database models are defined in `cape_cod_db/models.py` using SQLModel.

## Base Class: CapeModel

All CAPE database tables inherit from `CapeModel`, which provides:

```python
class CapeModel(SQLModel):
    created_at: datetime     # Auto-set on creation (UTC)
    last_edited: datetime    # Auto-updated on modification (UTC)
```

**Key Features:**
- Automatic timestamp tracking
- UTC timezone enforcement
- `onupdate` hook for `last_edited` (ORM only, not raw SQL)

**Important:** When manipulating records via raw SQL, `created_at` and `last_edited` are NOT automatically handled.

## Current Models

### User

**Location:** `models.py:26-47`

**Fields:**
- `id: int | None` - Primary key (auto-increment)
- `first_name: str` - Required
- `last_name: str` - Required
- `email: str` - Required, unique, indexed
- `created_at: datetime` - Inherited from CapeModel
- `last_edited: datetime` - Inherited from CapeModel

**TODOs:**
1. Add email validation (need to select validator library)
2. Fix `__repr__` to exclude PII/PHI for safe logging

**Table Name:** `user` (lowercase, SQLModel default)

### Tributary

**Location:** `models.py:50-66`

**Fields:**
- `id: int | None` - Primary key (auto-increment)
- `name: str` - Required, unique, indexed (logical compartment name)
- `description: str | None` - Optional description
- `created_at: datetime` - Inherited from CapeModel
- `last_edited: datetime` - Inherited from CapeModel

**Purpose:** Represents a logical data compartment with associated AWS resources. Tributaries group users and resources together for authorization.

**Table Name:** `tributary`

### UserTributary

**Location:** `models.py:69-93`

**Fields:**
- `id: int | None` - Primary key (auto-increment)
- `user_id: int` - Foreign key to User (CASCADE on delete)
- `tributary_id: int` - Foreign key to Tributary (CASCADE on delete)
- `granted_by: int | None` - Foreign key to User (nullable, SET NULL on delete)
- `granted_at: datetime | None` - Timestamp when access was granted
- `created_at: datetime` - Inherited from CapeModel
- `last_edited: datetime` - Inherited from CapeModel

**Constraints:**
- Unique constraint on (user_id, tributary_id) - user can only be in tributary once
- Index on user_id for fast user → tributary lookups

**Purpose:** Many-to-many junction table between Users and Tributaries, with audit trail.

**Table Name:** `usertributary`

### Resource

**Location:** `models.py:96-122`

**Fields:**
- `id: int | None` - Primary key (auto-increment)
- `tributary_id: int` - Foreign key to Tributary (no CASCADE - explicit control)
- `resource_type: str` - Type of resource (e.g., "s3_bucket", "ec2_instance")
- `resource_identifier: str` - Platform-specific identifier (e.g., S3 path, ARN)
- `access_pattern: str` - Access mode (e.g., "read", "write", "connect")
- `metadata: dict | None` - JSONB field for flexible additional data (indexed with GIN)
- `created_at: datetime` - Inherited from CapeModel
- `last_edited: datetime` - Inherited from CapeModel

**Constraints:**
- Unique constraint on (tributary_id, resource_type, resource_identifier, access_pattern)
- Index on tributary_id for fast tributary → resource lookups
- GIN index on metadata JSONB field for efficient queries

**Purpose:** Platform-agnostic resource definitions linked to tributaries. Supports AWS, Azure, GCP, etc.

**Standard Pattern:** Each tributary typically has 4 S3 resources: raw_uploads (write), clean_uploads (read), raw_results (write), clean_results (read).

**Table Name:** `resource`

### UserAttribute

**Location:** `models.py:125-147`

**Fields:**
- `id: int | None` - Primary key (auto-increment)
- `user_id: int` - Foreign key to User (CASCADE on delete)
- `attribute_key: str` - Attribute name (e.g., "user_status", "role")
- `attribute_value: str` - Attribute value (e.g., "quarantine", "admin")
- `created_at: datetime` - Inherited from CapeModel
- `last_edited: datetime` - Inherited from CapeModel

**Constraints:**
- Unique constraint on (user_id, attribute_key) - one value per key per user
- Index on user_id for fast user → attribute lookups

**Purpose:** Key-value attributes for users to handle non-tributary authorization (quarantine, admin roles, suspension, etc.).

**Standard Attributes:**
- `user_status`: Values like "active", "quarantine", "suspended", "deactivated"
- `role`: Values like "admin", "analyst", "viewer"

**Table Name:** `userattribute`

## Model Conventions

1. **Inheritance:** All tables inherit from `CapeModel` with `table=True`
2. **Single File:** All models in one module for now
3. **Type Hints:** Use Python 3.10+ union syntax (`int | None`)
4. **Primary Keys:** Use auto-increment integers with `Field(default=None, primary_key=True)`
5. **Indexes:** Add `index=True` to Field() for commonly queried columns
6. **Unique Constraints:** Add `unique=True` to Field() as needed

## Adding New Models

When adding new models:
1. Create class inheriting from `CapeModel` with `table=True`
2. Define all fields with proper types and Field() constraints
3. Import the model in `migrations/env.py` (required for Alembic autogenerate)
4. Generate migration: `alembic revision --autogenerate -m "description"`
5. Review generated migration before applying
6. Update this note with new model documentation
7. **Update test data fixtures** in `fixtures/test/test_data.sql` and `fixtures/test/cleanup_test_data.sql`
