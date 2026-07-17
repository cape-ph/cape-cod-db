-- Cleanup Test Data for CAPE Authorization System
--
-- PURPOSE: Removes test data loaded by fixtures/test/test_data.sql
--
-- USAGE:
--   psql cape_env_db < fixtures/test/cleanup_test_data.sql
--
-- WHAT THIS DOES:
--   - Deletes all users with @example.com emails
--   - Deletes tributaries by known test codes
--   - CASCADE deletes automatically remove:
--     - user_tributary memberships (FK CASCADE on user_id, tributary_id)
--     - user_attribute records (FK CASCADE on user_id)
--     - resourcegrant records (FK CASCADE on user_id, tributary_id, resource_id)
--     - resources owned by deleted tributaries (FK to tributary_id)
--
-- SAFETY:
--   - Only deletes data matching test patterns (@example.com, known codes)
--   - Uses transaction (can ROLLBACK if something looks wrong)
--   - Verification queries at end show what was removed

BEGIN;

-- Count before deletion (for verification)
\echo ''
\echo '=== Before Cleanup ==='
SELECT
    (SELECT COUNT(*) FROM "user") as users,
    (SELECT COUNT(*) FROM tributary) as tributaries,
    (SELECT COUNT(*) FROM usertributary) as memberships,
    (SELECT COUNT(*) FROM resource) as resources,
    (SELECT COUNT(*) FROM resourcegrant) as resource_grants,
    (SELECT COUNT(*) FROM userattribute) as user_attributes;

-- Delete in proper order to avoid FK constraint violations

-- First: Set granted_by to NULL for memberships and grants granted by test
-- users (avoids FK violation when deleting users; granted_by has no CASCADE)
UPDATE usertributary SET granted_by = NULL
WHERE granted_by IN (SELECT id FROM "user" WHERE email LIKE '%@example.com');

UPDATE resourcegrant SET granted_by = NULL
WHERE granted_by IN (SELECT id FROM "user" WHERE email LIKE '%@example.com');

-- Second: Delete resources owned by test tributaries
-- (must happen before deleting tributaries due to FK constraint)
DELETE FROM resource WHERE tributary_id IN (
    SELECT id FROM tributary WHERE code IN ('ENG', 'PLAT-ENG', 'DS', 'OPS')
);

-- Also delete test resources with no tributary owner
DELETE FROM resource WHERE resource_identifier IN (
    'arn:aws:ec2:us-east-1:123456789012:instance/i-eng001',
    'cape-web-app-prod',
    's3://cape-datalake/shared/'
);

-- Third: Delete test tributaries (by known test codes)
-- This will CASCADE delete:
--   - usertributary records (tributary_id FK CASCADE)
--   - resourcegrant records (tributary_id FK CASCADE) - any remaining
DELETE FROM tributary WHERE code IN ('ENG', 'PLAT-ENG', 'DS', 'OPS');

-- Fourth: Delete test users (by email pattern)
-- This will CASCADE delete:
--   - usertributary records (user_id FK CASCADE) - any remaining
--   - userattribute records (user_id FK CASCADE)
--   - resourcegrant records (user_id FK CASCADE) - any remaining
DELETE FROM "user" WHERE email LIKE '%@example.com';

COMMIT;

-- Verification after deletion
\echo ''
\echo '=== After Cleanup ==='
SELECT
    (SELECT COUNT(*) FROM "user") as users,
    (SELECT COUNT(*) FROM tributary) as tributaries,
    (SELECT COUNT(*) FROM usertributary) as memberships,
    (SELECT COUNT(*) FROM resource) as resources,
    (SELECT COUNT(*) FROM resourcegrant) as resource_grants,
    (SELECT COUNT(*) FROM userattribute) as user_attributes;

\echo ''
\echo '=== Test Data Cleanup Complete ==='
\echo ''
\echo 'If counts above are not what you expected, you can:'
\echo '  1. Check what remains: SELECT * FROM "user"; SELECT * FROM tributary;'
\echo '  2. Re-run cleanup if needed (script is idempotent)'
\echo ''
