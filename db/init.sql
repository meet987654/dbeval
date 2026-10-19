-- ==========================================
-- Step 1: Create databases & reader role
-- Run against default 'postgres' database:
-- ==========================================

CREATE DATABASE olist;
CREATE DATABASE appdb;
CREATE ROLE reader LOGIN PASSWORD 'reader';
GRANT CONNECT ON DATABASE olist TO reader;
GRANT CONNECT ON DATABASE appdb TO reader;

-- ==========================================
-- Step 2: Grant permissions in 'olist' database
-- Connect with: \c olist
-- ==========================================
\c olist;
GRANT USAGE ON SCHEMA public TO reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO reader;

-- ==========================================
-- Step 3: Grant permissions in 'appdb' database
-- Connect with: \c appdb
-- ==========================================
\c appdb;
GRANT USAGE ON SCHEMA public TO reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO reader;
