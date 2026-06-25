# Authorization Design

## Overview

Authorization layer using ABAC (Attribute-Based Access Control) with OPA (Open Policy Agent) for policy decisions.

## Status

**Last Updated**: 2026-06-24

**Confirmed Decisions**:
- ✅ ABAC with OPA (vs. RBAC/TBAC)
- ✅ Generic Resource model (vs. AWS-specific tables)
- ✅ Resource records only (no S3 path arrays on Tributary)
- ✅ OPA bundle pull model for data sync
- ✅ Pulumi outputs → JSON file → Ansible sync script
- ⏳ UserAttribute table timing (under review: add now vs. post-demo)

**Implementation Status**:
- 🔄 Database schema design (in progress)
- ⏹️ OPA policies (not started, design in `.design/`)
- ⏹️ Pulumi sync (not started, design in `.design/`)
- ⏹️ Ansible sync script (not started, design in `.design/`)

## Timeline & Scope

- **Demo Deadline**: 4 weeks
- **Demo Focus**: Internal users with tributary-based S3 access
- **Future**: External users via SAML federation
- **Resources**: Limited, multiple parallel efforts
- **Infrastructure**: Pulumi (IaC) + Ansible (environment) in separate repos

## Use Case: Tributary Model

### Concept
- **Tributaries**: Organizational units within the organization
- **Membership**: Users belong to one or more tributaries
- **Data Ownership**: Tributaries produce data → AWS Data Lake
- **Base Permissions**: Tributary membership grants S3 read/write, EC2 access
- **Flexibility**: Org restructures = attribute updates, not schema changes

### Demo MVP Use Case
**Primary Flow**: Users select S3 upload location based on tributary membership

1. User wants to upload data
2. Query API: "What S3 buckets can this user write to?"
3. User selects from allowed locations (based on tributary membership)
4. Upload request gated by OPA policy decision
5. **Stretch Goal**: Download reports with similar flow

**Current Problem**: Hard-coded single S3 location (not viable)

## Architecture Decision: ABAC + OPA (CONFIRMED)

### Why ABAC over RBAC/TBAC

**Decision**: Use ABAC (Attribute-Based Access Control) with OPA, not RBAC or pure tributary-based access control.

**Rationale**:
1. Tributary model fits ABAC naturally (membership is a user attribute)
2. External users need attribute-based rules (future requirement)
3. Document-based access grants → Rego policies (flexible policy language)
4. Flexible for complex future scenarios without schema changes
5. Separation of concerns (policies in OPA, not hardcoded in app)
6. Audit-friendly (policy versioning in OPA bundles)
7. Team has skills for both approaches
8. Handles non-tributary users (admins, auditors) via user attributes

**What This Means**:
- Authorization decisions evaluate user attributes (tributary membership, admin status, clearance level, etc.)
- Policies are NOT fixed role-permission mappings (no "Engineer role has S3 write permission")
- Policies evaluate attributes dynamically: "Allow if user.tributaries contains resource.owner_tributary"

### Resource Model Decision: Generic (CONFIRMED)

**Decision**: Single generic `Resource` table with JSONB attributes, not AWS-specific tables (S3Resource, EC2Instance, etc.).

**Why Generic over AWS-Specific**:
1. **Platform-agnostic**: Works for AWS, Azure, GCP, on-prem resources
2. **Hundreds of resources**: Managing many resource types (S3, EC2, Lambda, Glue, etc.)
3. **Future-proof**: Platform migrations don't require schema changes
4. **Single source of truth**: All resources in one table
5. **Easy to extend**: New resource types = insert rows, not schema migrations
6. **OPA-friendly**: Generic attributes map naturally to ABAC policies

**Trade-offs Accepted**:
- Lose type safety (no explicit `bucket_name` column, it's in JSONB)
- JSONB queries required for resource-specific filtering
- PostgreSQL JSONB is mature and performant (GIN indexes support fast queries)

### Tributary Path Storage: Resource Records Only (CONFIRMED)

**Decision**: Do NOT add `s3_write_paths` or `s3_read_paths` arrays to Tributary table. All resource access defined via Resource records.

**Why Resource Records Only**:
1. **Single source of truth**: All authorization data in Resource table
2. **Uniform treatment**: Standard buckets and exceptions handled identically
3. **Flexible metadata**: Each resource can have description, expiration, custom attributes
4. **Simpler OPA policies**: Query one place, not Tributary arrays + Resource records
5. **Easy to extend**: Add resource = insert record, no schema change

**Implementation Note**:
- Every tributary gets 4 standard Resource records (raw_uploads, clean_uploads, raw_results, clean_results)
- Can be auto-created via application code, database trigger, or sync script

### Components
- **User Attributes**: Stored in PostgreSQL (UserTributary for memberships, potentially UserAttribute for flexible attributes)
- **Policy Decisions**: OPA evaluates Rego policies
- **Data Sync**: Bundle-based pull model (PostgreSQL → JSON → OPA)
- **Infrastructure**: 
  - OPA on EC2 (currently v1.4.2, needs upgrade to v1.17.1)
  - PostgreSQL in AWS RDS (future, currently local dev)
  - API Gateway + Cognito identity provider
  - Pulumi (IaC) deploys resources, tags them for sync
  - Ansible deploys environment (including database)

## Database Schema

### Design Decisions Summary

1. **Generic Resource Model**: Single `Resource` table for all resource types (S3, EC2, Lambda, applications, etc.)
2. **No Tributary Path Arrays**: Tributaries do NOT have `s3_write_paths` or `s3_read_paths` fields
3. **Resource Records Define Access**: All resource access via Resource table records
4. **4 Standard Buckets**: Every tributary gets 4 Resource records for standard data pipeline buckets

### Core Tables (Demo Focus)

#### Tributary
Organizational units that own resources and have user members.

**Fields:**
- `id` - Primary key
- `name` - Display name (unique, indexed)
- `code` - Short code, e.g., "ENG", "DS" (unique, indexed)
- `description` - Purpose/details (optional)
- `parent_id` - Self-reference for hierarchy (optional, FK to tributary.id)
- `attributes` - JSONB for flexible metadata (department, cost_center, etc.)
- `created_at`, `last_edited` - Timestamps (inherited from CapeModel)

**Note**: Does NOT include S3 path arrays - all resource access defined via Resource table.

**4 Standard Buckets Pattern**:
Every tributary has 4 buckets allocated to it:
1. Raw user data uploads (triggers ETL when data placed here)
2. Cleaned user upload data (cataloged in datalake)
3. Raw analysis results (triggers ETL)
4. Cleaned analysis result data (cataloged in datalake)

These are represented as 4 Resource records, not fields on Tributary.

#### UserTributary (Join Table)
Many-to-many relationship with roles.

**Fields:**
- `user_id` - FK to user (CASCADE delete)
- `tributary_id` - FK to tributary (CASCADE delete)
- `role` - "member", "admin", "viewer" (default: "member")
- `granted_at` - When membership started
- `granted_by` - User who granted (FK to user)
- `expires_at` - Optional expiration
- **Primary Key**: (user_id, tributary_id)

**Indexes:**
- `idx_user_tributary_user` on user_id
- `idx_user_tributary_trib` on tributary_id

#### S3Resource → Resource (Generic Model)
Platform-agnostic resource registry supporting all resource types.

**Fields:**
- `id` - Primary key
- `resource_type` - Indexed string: "s3", "ec2", "lambda", "glue_table", "application", etc.
- `resource_identifier` - Unique identifier: ARN, URI, or canonical ID (unique, indexed)
- `display_name` - Human-readable name for UI
- `tributary_id` - Owning tributary (FK to tributary.id, nullable for shared resources)
- `access_type` - "read", "write", "both", "execute", "admin", etc.
- `attributes` - JSONB for resource-specific fields (bucket name, instance ID, etc.)
- `created_at`, `last_edited` - Timestamps (inherited from CapeModel)

**Indexes:**
- `idx_resource_type` on resource_type (B-tree)
- `idx_resource_identifier` on resource_identifier (B-tree, via UNIQUE)
- `idx_resource_tributary` on tributary_id (B-tree)
- `idx_resource_attributes` on attributes (GIN with jsonb_path_ops)

**Example Data**:
```
S3 Bucket:
  resource_type: "s3"
  resource_identifier: "s3://cape-datalake/eng/uploads/"
  display_name: "Engineering Raw Uploads"
  tributary_id: 1
  access_type: "write"
  attributes: {"bucket": "cape-datalake", "path_prefix": "eng/uploads/", "category": "raw_uploads"}

EC2 Instance:
  resource_type: "ec2"
  resource_identifier: "arn:aws:ec2:us-east-1:123456:instance/i-abc123"
  display_name: "Engineering Web Server"
  tributary_id: 1
  access_type: "ssh"
  attributes: {"instance_id": "i-abc123", "instance_type": "t3.medium", "vpc_id": "vpc-xyz"}

Application:
  resource_type: "application"
  resource_identifier: "cape-web-app-prod"
  display_name: "CAPE Web Application (Production)"
  tributary_id: NULL (shared)
  access_type: "admin"
  attributes: {"url": "https://app.cape.example.com", "environment": "prod"}
```

**Note**: This replaces the originally planned "S3Resource" table. Generic model chosen for platform-agnosticism and flexibility.

### Future Tables (Post-Demo or Under Consideration)

#### UserAttribute (TIMING UNDER REVIEW)
Flexible attribute storage for advanced ABAC.

**Status**: Originally planned for post-demo, but under consideration to add now to handle non-tributary users (admins, auditors, students with partial permissions).

**Purpose**: Store user-level attributes like `is_admin`, `clearance_level`, `system_role` for authorization decisions.

**Fields:**
- `id` - Primary key
- `user_id` - FK to user.id (CASCADE delete)
- `attribute_key` - Attribute name (e.g., "is_admin", "clearance_level")
- `attribute_value` - Attribute value (string representation)
- `source` - "ad", "saml", "manual", "computed"
- `created_at`, `last_edited` - Timestamps
- **UNIQUE**: (user_id, attribute_key)

**Use Cases**:
- Organizational admins who don't belong to any tributary
- Security auditors who need read access across all tributaries without membership
- Students with limited admin permissions
- Clearance levels for classified data access (future)
- AD/SAML synced attributes (future)

**Alternative Considered**: Adding `is_admin` boolean and `system_role` string to User table. Rejected to avoid schema churn (add fields → remove fields post-demo).

**Decision Pending**: Add now (cleaner long-term) or add post-demo (simpler demo)?

**Options Analyzed**:

**Option A - Special "Admin" Tributary**: Create system tributary that admins belong to
- Pros: Works with existing schema
- Cons: Semantic mismatch (admins aren't a tributary), doesn't handle partial permissions

**Option B - Add UserAttribute Table Now**: Store user-level attributes like `is_admin`, `system_role`
- Pros: Proper ABAC, handles all scenarios, no future refactoring
- Cons: Slightly more complex demo, one more table to implement

**Option C - Direct User-Resource Grants (AccessGrant Table)**: Grant specific users access outside tributary model
- Pros: Handles exceptions cleanly
- Cons: Complex, doesn't solve "admin needs everything" efficiently

**Option D - Add Role Fields to User Table**: Add `is_admin` boolean and `system_role` string to User
- Pros: Simplest addition (2 columns), handles full admins
- Cons: Schema churn post-demo (add fields → remove when UserAttribute added)

**Recommendation**: Option B (add UserAttribute table now) to avoid schema churn and demonstrate full ABAC capability.

#### PartnerOrganization
External organizations with SAML federation.

**Fields:**
- `id`, `name` (unique)
- `saml_entity_id` (unique)
- `contact_email`
- `attributes` - JSONB
- `created_at`, `last_edited`

#### ExternalUser
Users from partner organizations.

**Fields:**
- `id`, `partner_org_id` (FK)
- `external_id` - ID from partner system
- `email`
- `attributes` - JSONB
- `created_at`, `last_edited`
- **Unique**: (partner_org_id, external_id)

#### Resource
Generic resource tracking (beyond S3).

**Status**: MERGED INTO CORE SCHEMA - this is now the main Resource table described above, not a future addition.

~~**Fields:**~~
~~- `id`, `resource_type`~~
~~- `resource_arn` (unique)~~
~~- `tributary_id` (FK, nullable)~~
~~- `attributes` - JSONB~~
~~- `created_at`, `last_edited`~~

#### AccessGrant
Exception-based access grants (manual overrides).

**Fields:**
- `id`
- `grantee_type` - "user", "tributary", "partner_org"
- `grantee_id` - Polymorphic reference
- `resource_id` (FK) or `resource_pattern` (flexible matching)
- `permissions` - JSONB array: ["read", "write", "delete"]
- `granted_by` (FK to user), `granted_at`
- `expires_at` - Optional expiration
- `justification` - Text explanation
- `grant_document_url` - Link to agreement document
- `revoked_at`, `revoked_by` - Audit trail

## OPA Integration

### Data Sync: Bundle Strategy (Pull Model) - CONFIRMED

**Decision**: Use bundle-based pull model for demo.

**Process:**
1. Python script queries PostgreSQL
2. Generates JSON data snapshot
3. Packages as OPA bundle (tar.gz with data.json + manifest)
4. OPA polls bundle location every 30-60 seconds
5. OPA hot-reloads data automatically

**Why Bundle over Push:**
- Built-in OPA support (no custom endpoints)
- Lowest maintenance overhead
- Good enough for demo (tributary changes infrequent)
- Easy to upgrade to push/hybrid later if needed
- Fastest implementation (1-2 days)

**Bundle Location**:
- Local file for demo (simplest)
- S3 bucket for production (future)

**Demo Requirement**: OPA data sync is nice-to-have but NOT required for demo. Can demonstrate with static bundle or manual bundle generation.

### Authorization Flow

```
1. User Request → Application
2. Application enriches context:
   - Query PostgreSQL for user attributes
   - Build authorization input
3. Application → OPA Decision Request:
   POST /v1/data/cape/authorize
   {
     "input": {
       "user": {
         "id": 123,
         "tributaries": ["trib-1", "trib-2"],
         "attributes": {...}
       },
       "action": "read" | "write",
       "resource": {
         "type": "s3",
         "path": "s3://bucket/prefix/file.csv",
         "owner_tributary": "trib-1"
       }
     }
   }
4. OPA evaluates Rego policies against data bundle
5. OPA returns: {"result": {"allow": true/false}}
6. Application enforces decision
```

### Sample Rego Policies

See `.scratch/session_context.md:248-297` for detailed policy examples.

**Key Policies:**
- `user_writeable_resources` - Lists S3 paths user can write to
- `allow` - Authorizes specific read/write actions

**Policy Logic:**
- Default deny
- Write allowed if user in owning tributary + resource has write access
- Read allowed if user in tributary with read permissions
- Future: Access grant overrides

## Infrastructure → Database Sync (Pulumi → PostgreSQL)

### Decision: Pulumi Outputs → JSON File → Ansible Sync Script (CONFIRMED)

**Problem**: Pulumi deploys hundreds of AWS resources. Database needs metadata about these resources for authorization. How does resource data get from Pulumi state into PostgreSQL?

**Solution Chosen**: Pulumi exports structured JSON file → Ansible ingestion script populates database

**Flow**:
1. **Pulumi program** (infrastructure repo):
   - Creates AWS resources (S3 buckets, EC2 instances, etc.)
   - Tags resources consistently (`tributary`, `resource_category`, `access_type`, etc.)
   - Exports stack outputs as JSON: `pulumi stack output tributary_resources --json > tributary-resources.json`
   
2. **Intermediate JSON file**:
   - Format: JSON (native Pulumi support)
   - Structure: Tributaries → Resources with metadata
   - Stored: Local file or S3 (accessible to Ansible)
   
3. **Ansible deployment** (environment repo):
   - Reads JSON file (no Pulumi CLI dependency in Ansible environment)
   - Python script transforms JSON → Resource records
   - Populates PostgreSQL database

**Why This Approach**:
- **Decoupled**: Ansible doesn't need Pulumi CLI installed (different deployment systems possible)
- **Flexible**: As these are separate public repos, one can be used without the other if valid JSON file provided
- **Structured data**: Pulumi defines clear schema for exports
- **Auditable**: JSON file can be versioned, inspected, validated

**Tagging Strategy**: Required for resource discovery and billing (in scope for Pulumi repo, recommendations documented in team discussion summary)

**For Demo**: May manually create JSON file with ~16 resource records (4 tributaries × 4 buckets) rather than full Pulumi export automation.

## Implementation Plan (4 Weeks)

**Note**: This plan covers all repos. cape-cod-db repo is only responsible for database schema (Week 1 database tasks).

### Week 1: Database + OPA Setup
**Database (cape-cod-db repo)**:
- Create Alembic migrations (Tributary, UserTributary, Resource, optionally UserAttribute)
- Seed dev database with test data (fixtures/test/test_data.sql)
- Update documentation (README, notes/)

**OPA (infrastructure repo)**:
- Upgrade OPA (v1.4.2 → v1.17.1)
- Configure OPA bundle loading

**Deliverable**: Database schema ready, OPA upgraded

### Week 2: Core OPA Policies
**OPA policies (infrastructure or dedicated repo)**:
- Write `user_writeable_resources` policy
- Write `allow` policy for S3 read/write
- Create OPA policy tests
- Setup bundle auto-reload (cron/systemd)

**Deliverable**: Working OPA policies for S3 authorization
**Deliverable**: Working OPA policies for S3 authorization

### Week 3: API Integration & Sync Scripts
**API (Pulumi repo - Lambda functions)**:
- API endpoint: `GET /user/upload-locations`
- API endpoint: `POST /data/upload` (OPA-gated)
- Optional: Download endpoints
- Add OPA middleware
- Wire Cognito JWT → user_id

**Sync Scripts**:
- Pulumi: Export resource metadata to JSON
- Ansible: Python script to ingest JSON → PostgreSQL
- Bundle generator: PostgreSQL → OPA bundle (optional for demo)

**Deliverable**: Working API with S3 permissions, sync infrastructure

### Week 4: Testing + Demo Polish
- Integration tests
- Load demo data (real tributary/resource data)
- Documentation
- Optional: Svelte admin UI for tributary membership
- Demo script prep

**Deliverable**: Polished demo

## Testing Setup (Local Development)

**Local PostgreSQL**: PostgreSQL 18.4 on development machine

**Database Connection**:
```bash
# From .env file
DB_URL="postgresql:///cape_env_db"

# Test connection
source .env && psql "$DB_URL" -c "SELECT version();"
```

**Running Migrations**:
```bash
# Current migration state
source .env && capedb -c cape_cod_db/alembic.ini -x db_url="$DB_URL" current --verbose

# Apply migrations
source .env && capedb -c cape_cod_db/alembic.ini -x db_url="$DB_URL" upgrade head

# Downgrade
source .env && capedb -c cape_cod_db/alembic.ini -x db_url="$DB_URL" downgrade -1
```

**Loading Test Data**:
```bash
source .env && psql "$DB_URL" < fixtures/test/test_data.sql
```

## Demo Data Structure

See `.scratch/session_context.md:340-364` for complete demo data SQL.

**Example Setup:**
- **Tributaries**: Engineering (ENG), Data Science (DS), Operations (OPS)
- **S3 Resources**: 
  - Write: eng/uploads/, ds/uploads/
  - Read: eng/reports/, shared/
- **Memberships**: 
  - Alice: ENG admin + DS member
  - Bob: DS admin
  - Charlie: OPS member

## Outstanding Questions

**Updated**: 2026-06-24

1. **UserAttribute Table Timing**: Add now (with core tables) or post-demo? Decision pending.
2. **S3 Bucket Structure**: What's the actual naming/path structure for the 4 standard buckets per tributary?
   - Same bucket with different prefixes? `s3://cape-datalake/raw-uploads/{tributary-code}/`
   - Different buckets per tributary? `s3://cape-raw-uploads-{tributary-code}/`
3. **Access Type Mapping**: How to determine `access_type` for resources?
   - From Pulumi tags? (`access_type=write`)
   - From naming convention? (raw-uploads → write, clean-uploads → read)
   - Hardcoded mapping in sync script?
4. **Cognito Attributes**: What user attributes in JWT? (email, user_id, groups?)
5. **OPA Bundle**: Local file or S3 for demo?
6. **Demo Audience**: Internal stakeholders or end users?

## Compliance & Audit (Future)

- Audit trail of policy changes (OPA bundle versioning)
- Track authorization decisions (OPA decision logs)
- Access grant justifications (access_grant table)
- Critical for production, not demo scope
