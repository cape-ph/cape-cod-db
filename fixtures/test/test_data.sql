-- Test Data for CAPE Authorization System
-- 
-- PURPOSE: Provides realistic test data for development and testing.
--          Includes users, tributaries, memberships, resources, and attributes.
--
-- LOADING TEST DATA:
--   Method 1 - Permanent (keeps data until manually cleaned):
--     psql cape_env_db < fixtures/test/test_data.sql
--
--   Method 2 - Temporary (auto-rollback, no cleanup needed):
--     psql cape_env_db <<EOF
--     BEGIN;
--     \i fixtures/test/test_data.sql
--     -- Inspect/test here
--     ROLLBACK;  -- Or COMMIT to keep
--     EOF
--
--   Method 3 - Using savepoint (partial rollback):
--     psql cape_env_db <<EOF
--     SAVEPOINT before_test_data;
--     \i fixtures/test/test_data.sql
--     -- Work/test here
--     ROLLBACK TO SAVEPOINT before_test_data;
--     EOF
--
-- REMOVING TEST DATA:
--   psql cape_env_db < fixtures/test/cleanup_test_data.sql
--
-- NOTE: Test data uses @example.com emails for easy identification.

BEGIN;

-- Insert users (4 users with varied scenarios)
INSERT INTO "user" (created_at, last_edited, first_name, last_name, email) VALUES
(NOW(), NOW(), 'Alice', 'Engineer', 'alice.engineer@example.com'),
(NOW(), NOW(), 'Bob', 'DataScientist', 'bob.datascientist@example.com'),
(NOW(), NOW(), 'Charlie', 'Operator', 'charlie.operator@example.com'),
(NOW(), NOW(), 'Diana', 'MultiRole', 'diana.multirole@example.com'),
(NOW(), NOW(), 'Admin', 'User', 'admin.user@example.com'),
(NOW(), NOW(), 'Quinn', 'Quarantine', 'quinn.quarantine@example.com');

-- Insert tributaries (4 tributaries including hierarchy example)
-- Note: Insert parent tributaries first, then children
INSERT INTO tributary (created_at, last_edited, name, code, description, parent_id, attributes) VALUES
(NOW(), NOW(), 'Engineering', 'ENG', 'Engineering team - application development and infrastructure', NULL, '{"department": "technology", "cost_center": "eng-001"}'::jsonb),
(NOW(), NOW(), 'Data Science', 'DS', 'Data science and analytics team', NULL, '{"department": "research", "cost_center": "ds-001"}'::jsonb),
(NOW(), NOW(), 'Operations', 'OPS', 'Operations and infrastructure management', NULL, '{"department": "technology", "cost_center": "ops-001"}'::jsonb);

-- Insert Platform Engineering as child of Engineering (requires Engineering's ID)
INSERT INTO tributary (created_at, last_edited, name, code, description, parent_id, attributes)
SELECT NOW(), NOW(), 'Platform Engineering', 'PLAT-ENG', 'Platform and DevOps team', 
       t.id, '{"department": "technology", "cost_center": "plat-001"}'::jsonb
FROM tributary t WHERE t.code = 'ENG';

-- Insert S3 resources (demonstrates 4-bucket pattern for ENG, varied for others)
-- Engineering: All 4 standard buckets
INSERT INTO resource (created_at, last_edited, resource_type, resource_identifier, display_name, tributary_id, access_type, attributes)
SELECT NOW(), NOW(), 's3', 's3://cape-datalake/eng/raw-uploads/', 'Engineering Raw Data Uploads', t.id, 'write', '{"bucket": "cape-datalake", "path_prefix": "eng/raw-uploads/", "category": "raw_uploads"}'::jsonb
FROM tributary t WHERE t.code = 'ENG'
UNION ALL
SELECT NOW(), NOW(), 's3', 's3://cape-datalake/eng/clean-uploads/', 'Engineering Cleaned Upload Data', t.id, 'read', '{"bucket": "cape-datalake", "path_prefix": "eng/clean-uploads/", "category": "clean_uploads"}'::jsonb
FROM tributary t WHERE t.code = 'ENG'
UNION ALL
SELECT NOW(), NOW(), 's3', 's3://cape-datalake/eng/raw-results/', 'Engineering Raw Analysis Results', t.id, 'write', '{"bucket": "cape-datalake", "path_prefix": "eng/raw-results/", "category": "raw_results"}'::jsonb
FROM tributary t WHERE t.code = 'ENG'
UNION ALL
SELECT NOW(), NOW(), 's3', 's3://cape-datalake/eng/clean-results/', 'Engineering Cleaned Analysis Results', t.id, 'read', '{"bucket": "cape-datalake", "path_prefix": "eng/clean-results/", "category": "clean_results"}'::jsonb
FROM tributary t WHERE t.code = 'ENG'
UNION ALL
-- Platform Engineering: Subset of resources
SELECT NOW(), NOW(), 's3', 's3://cape-datalake/plat-eng/deployments/', 'Platform Engineering Deployments', t.id, 'both', '{"bucket": "cape-datalake", "path_prefix": "plat-eng/deployments/", "category": "deployments"}'::jsonb
FROM tributary t WHERE t.code = 'PLAT-ENG'
UNION ALL
-- Data Science: Varied resources
SELECT NOW(), NOW(), 's3', 's3://cape-datalake/ds/raw-uploads/', 'Data Science Raw Uploads', t.id, 'write', '{"bucket": "cape-datalake", "path_prefix": "ds/raw-uploads/", "category": "raw_uploads"}'::jsonb
FROM tributary t WHERE t.code = 'DS'
UNION ALL
SELECT NOW(), NOW(), 's3', 's3://cape-datalake/ds/models/', 'Data Science ML Models', t.id, 'both', '{"bucket": "cape-datalake", "path_prefix": "ds/models/", "category": "models"}'::jsonb
FROM tributary t WHERE t.code = 'DS'
UNION ALL
SELECT NOW(), NOW(), 's3', 's3://cape-datalake/ds/notebooks/', 'Data Science Jupyter Notebooks', t.id, 'both', '{"bucket": "cape-datalake", "path_prefix": "ds/notebooks/", "category": "notebooks"}'::jsonb
FROM tributary t WHERE t.code = 'DS'
UNION ALL
-- Operations: Basic resources
SELECT NOW(), NOW(), 's3', 's3://cape-datalake/ops/logs/', 'Operations System Logs', t.id, 'both', '{"bucket": "cape-datalake", "path_prefix": "ops/logs/", "category": "logs"}'::jsonb
FROM tributary t WHERE t.code = 'OPS';

-- Shared resources (no tributary ownership)
INSERT INTO resource (created_at, last_edited, resource_type, resource_identifier, display_name, tributary_id, access_type, attributes) VALUES
(NOW(), NOW(), 's3', 's3://cape-datalake/shared/', 'Shared Resources - All Access', NULL, 'read', '{"bucket": "cape-datalake", "path_prefix": "shared/", "category": "shared"}'::jsonb);

-- Non-S3 resource examples
INSERT INTO resource (created_at, last_edited, resource_type, resource_identifier, display_name, tributary_id, access_type, attributes)
SELECT NOW(), NOW(), 'ec2', 'arn:aws:ec2:us-east-1:123456789012:instance/i-eng001', 'Engineering Web Server', t.id, 'ssh', '{"instance_id": "i-eng001", "instance_type": "t3.medium", "vpc_id": "vpc-eng"}'::jsonb
FROM tributary t WHERE t.code = 'ENG';

INSERT INTO resource (created_at, last_edited, resource_type, resource_identifier, display_name, tributary_id, access_type, attributes) VALUES
(NOW(), NOW(), 'application', 'cape-web-app-prod', 'CAPE Web Application (Production)', NULL, 'admin', '{"url": "https://app.cape.example.com", "environment": "prod"}'::jsonb);

-- Insert user-tributary memberships
-- Alice: Engineering admin
INSERT INTO usertributary (user_id, tributary_id, role, granted_at, granted_by, expires_at)
SELECT u.id, t.id, 'admin', NOW(), NULL, NULL
FROM "user" u, tributary t
WHERE u.email = 'alice.engineer@example.com' AND t.code = 'ENG';

-- Bob: Data Science admin
INSERT INTO usertributary (user_id, tributary_id, role, granted_at, granted_by, expires_at)
SELECT u.id, t.id, 'admin', NOW(), NULL, NULL
FROM "user" u, tributary t
WHERE u.email = 'bob.datascientist@example.com' AND t.code = 'DS';

-- Charlie: Operations member
INSERT INTO usertributary (user_id, tributary_id, role, granted_at, granted_by, expires_at)
SELECT u.id, t.id, 'member', NOW(), NULL, NULL
FROM "user" u, tributary t
WHERE u.email = 'charlie.operator@example.com' AND t.code = 'OPS';

-- Diana: Multi-tributary (ENG member + PLAT-ENG admin + DS viewer)
INSERT INTO usertributary (user_id, tributary_id, role, granted_at, granted_by, expires_at)
SELECT diana.id, eng.id, 'member', NOW(), alice.id, NULL::timestamp
FROM "user" diana, "user" alice, tributary eng
WHERE diana.email = 'diana.multirole@example.com' 
  AND alice.email = 'alice.engineer@example.com'
  AND eng.code = 'ENG'
UNION ALL
SELECT diana.id, plat.id, 'admin', NOW(), alice.id, NULL::timestamp
FROM "user" diana, "user" alice, tributary plat
WHERE diana.email = 'diana.multirole@example.com'
  AND alice.email = 'alice.engineer@example.com'
  AND plat.code = 'PLAT-ENG'
UNION ALL
SELECT diana.id, ds.id, 'viewer', NOW(), bob.id, NULL::timestamp
FROM "user" diana, "user" bob, tributary ds
WHERE diana.email = 'diana.multirole@example.com'
  AND bob.email = 'bob.datascientist@example.com'
  AND ds.code = 'DS';

-- Insert user attributes (demonstrates various attribute patterns)
-- Admin user with is_admin attribute
INSERT INTO userattribute (created_at, last_edited, user_id, attribute_key, attribute_value, source)
SELECT NOW(), NOW(), u.id, 'is_admin', 'true', 'manual'
FROM "user" u WHERE u.email = 'admin.user@example.com'
UNION ALL
SELECT NOW(), NOW(), u.id, 'system_role', 'org_admin', 'manual'
FROM "user" u WHERE u.email = 'admin.user@example.com'
UNION ALL
SELECT NOW(), NOW(), u.id, 'user_status', 'active', 'system'
FROM "user" u WHERE u.email = 'admin.user@example.com';

-- Quinn: Quarantined new user (no tributary memberships)
INSERT INTO userattribute (created_at, last_edited, user_id, attribute_key, attribute_value, source)
SELECT NOW(), NOW(), u.id, 'user_status', 'quarantine', 'system'
FROM "user" u WHERE u.email = 'quinn.quarantine@example.com';

-- Alice: Active user with clearance
INSERT INTO userattribute (created_at, last_edited, user_id, attribute_key, attribute_value, source)
SELECT NOW(), NOW(), u.id, 'user_status', 'active', 'system'
FROM "user" u WHERE u.email = 'alice.engineer@example.com'
UNION ALL
SELECT NOW(), NOW(), u.id, 'clearance_level', 'secret', 'ad'
FROM "user" u WHERE u.email = 'alice.engineer@example.com';

-- Bob: Active user
INSERT INTO userattribute (created_at, last_edited, user_id, attribute_key, attribute_value, source)
SELECT NOW(), NOW(), u.id, 'user_status', 'active', 'system'
FROM "user" u WHERE u.email = 'bob.datascientist@example.com';

-- Charlie: Suspended user (demonstrates suspended state)
INSERT INTO userattribute (created_at, last_edited, user_id, attribute_key, attribute_value, source)
SELECT NOW(), NOW(), u.id, 'user_status', 'suspended', 'manual'
FROM "user" u WHERE u.email = 'charlie.operator@example.com';

-- Diana: Active user
INSERT INTO userattribute (created_at, last_edited, user_id, attribute_key, attribute_value, source)
SELECT NOW(), NOW(), u.id, 'user_status', 'active', 'system'
FROM "user" u WHERE u.email = 'diana.multirole@example.com';

COMMIT;

-- Verification queries
\echo ''
\echo '=== Test Data Loaded Successfully ==='
\echo ''

\echo 'Users:'
SELECT id, first_name, last_name, email FROM "user" ORDER BY id;

\echo ''
\echo 'Tributaries:'
SELECT id, code, name, parent_id, description FROM tributary ORDER BY id;

\echo ''
\echo 'User Memberships:'
SELECT 
    u.id as user_id,
    u.first_name || ' ' || u.last_name as user_name,
    t.code as tributary,
    ut.role,
    ut.granted_at
FROM usertributary ut
JOIN "user" u ON ut.user_id = u.id
JOIN tributary t ON ut.tributary_id = t.id
ORDER BY u.id, t.id;

\echo ''
\echo 'User Attributes:'
SELECT 
    u.id as user_id,
    u.first_name || ' ' || u.last_name as user_name,
    ua.attribute_key,
    ua.attribute_value,
    ua.source
FROM userattribute ua
JOIN "user" u ON ua.user_id = u.id
ORDER BY u.id, ua.attribute_key;

\echo ''
\echo 'Resources (first 10):'
SELECT 
    r.id,
    r.resource_type,
    r.resource_identifier,
    t.code as tributary,
    r.access_type
FROM resource r
LEFT JOIN tributary t ON r.tributary_id = t.id
ORDER BY r.resource_type, r.resource_identifier
LIMIT 10;

\echo ''
\echo 'Resource count by type:'
SELECT resource_type, COUNT(*) as count 
FROM resource 
GROUP BY resource_type 
ORDER BY resource_type;

\echo ''
\echo '=== Test Data Summary ==='
SELECT 
    (SELECT COUNT(*) FROM "user") as users,
    (SELECT COUNT(*) FROM tributary) as tributaries,
    (SELECT COUNT(*) FROM usertributary) as memberships,
    (SELECT COUNT(*) FROM resource) as resources,
    (SELECT COUNT(*) FROM userattribute) as user_attributes;
