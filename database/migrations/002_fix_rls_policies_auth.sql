-- Migration 002: Fix RLS Policies for Authentication API Access
-- Date: 2025-08-26
-- Purpose: Fix authentication issues by allowing service_role access to auth tables
-- 
-- PROBLEM: API authentication was failing because RLS policies only allowed 'authenticated' role
-- but the API uses 'service_role' to access the database.
--
-- SOLUTION: Create production-ready RLS policies that allow service_role to perform necessary
-- authentication operations while maintaining security.

-- ========================================
-- Step 1: Grant necessary permissions to service_role
-- ========================================

-- Grant SELECT and UPDATE permissions on ivo_api_tokens
-- This allows the API to validate tokens and update usage counters
GRANT SELECT, UPDATE ON ivo_api_tokens TO service_role;

-- Grant SELECT permission on ivo_users  
-- This allows the API to validate user existence and status during login
GRANT SELECT ON ivo_users TO service_role;

-- ========================================
-- Step 2: Create RLS policies for ivo_api_tokens
-- ========================================

-- Policy for SELECT operations (token validation)
-- Allows service_role to read active, non-expired tokens
CREATE POLICY "service_role_select_tokens" ON ivo_api_tokens 
FOR SELECT 
TO service_role 
USING (
    is_active = true AND 
    (expires_at IS NULL OR expires_at > NOW())
);

-- Policy for UPDATE operations (usage tracking)
-- Allows service_role to update token usage statistics and last_used_at
CREATE POLICY "service_role_update_tokens" ON ivo_api_tokens 
FOR UPDATE 
TO service_role 
USING (is_active = true)
WITH CHECK (is_active = true);

-- ========================================
-- Step 3: Create RLS policies for ivo_users
-- ========================================

-- Policy for SELECT operations (user validation during authentication)
-- Allows service_role to read active users during login process
CREATE POLICY "service_role_select_users" ON ivo_users 
FOR SELECT 
TO service_role 
USING (is_active = true);

-- ========================================
-- Step 4: Verification queries
-- ========================================

-- Check all policies are created correctly
-- Run this after migration to verify
/*
SELECT schemaname, tablename, policyname, roles, cmd, qual, with_check
FROM pg_policies 
WHERE tablename IN ('ivo_api_tokens', 'ivo_users')
  AND policyname LIKE '%service_role%'
ORDER BY tablename, policyname;
*/

-- ========================================
-- Step 5: Test queries (run manually to verify)
-- ========================================

-- Test 1: Check if service_role can read tokens
/*
SET ROLE service_role;
SELECT COUNT(*) as active_tokens_count 
FROM ivo_api_tokens 
WHERE is_active = true;
RESET ROLE;
*/

-- Test 2: Check if service_role can read users
/*
SET ROLE service_role;
SELECT COUNT(*) as active_users_count 
FROM ivo_users 
WHERE is_active = true;
RESET ROLE;
*/

-- Test 3: Test actual token lookup (use real token from your database)
/*
SET ROLE service_role;
SELECT id, token_ivo, user_id, is_active, expires_at
FROM ivo_api_tokens 
WHERE token_ivo = 'ivo_test_token_dev_only_remove_in_prod'
  AND is_active = true;
RESET ROLE;
*/

-- ========================================
-- IMPORTANT NOTES:
-- ========================================
--
-- 1. This migration maintains security by:
--    - Only allowing access to active (is_active = true) records
--    - Only allowing token updates, not token creation/deletion
--    - Restricting access to non-expired tokens
--    - Not exposing sensitive fields unnecessarily
--
-- 2. The service_role should be used by your API configuration in:
--    config/database.py - make sure your Supabase client uses service_role
--
-- 3. After running this migration, test authentication endpoints:
--    POST /api/auth/login - should work with proper credentials
--    GET /api/auth/validate-token - should validate tokens correctly
--
-- 4. Monitor logs after deployment to ensure no security issues
--
-- 5. If you need to revoke access later:
--    DROP POLICY "service_role_select_tokens" ON ivo_api_tokens;
--    DROP POLICY "service_role_update_tokens" ON ivo_api_tokens;
--    DROP POLICY "service_role_select_users" ON ivo_users;
--    REVOKE SELECT, UPDATE ON ivo_api_tokens FROM service_role;
--    REVOKE SELECT ON ivo_users FROM service_role;