-- ============================================================================
-- Network Segmentation Analyzer - Database Initialization Script
-- ============================================================================
-- PostgreSQL Database Setup
--
-- This script:
-- 1. Creates the database (if not exists)
-- 2. Creates all required tables
-- 3. Creates indexes for performance
-- 4. Creates users and roles
-- 5. Grants appropriate permissions
--
-- Usage:
--   psql -U postgres -f init_db.sql
--
-- Or use the Python wrapper:
--   python scripts/init_db.py
--
-- ============================================================================

-- ============================================================================
-- SECTION 1: Database Creation
-- ============================================================================

-- Drop database if exists (commented out for safety)
-- DROP DATABASE IF EXISTS network_analysis;

-- Create database
SELECT 'Creating database...' as status;
CREATE DATABASE network_analysis
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

COMMENT ON DATABASE network_analysis IS 'Network Segmentation Analyzer - Application & Network Topology Database';

-- Connect to the database
\c network_analysis

SELECT 'Database created successfully' as status;

-- ============================================================================
-- SECTION 2: Extensions
-- ============================================================================

-- Enable UUID extension (optional but useful)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for better text search (optional)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

SELECT 'Extensions enabled' as status;

-- ============================================================================
-- SECTION 3: Schema and Tables
-- ============================================================================

-- Applications table
SELECT 'Creating applications table...' as status;
CREATE TABLE IF NOT EXISTS applications (
    app_id VARCHAR(255) PRIMARY KEY,
    app_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

COMMENT ON TABLE applications IS 'Application registry with metadata';
COMMENT ON COLUMN applications.app_id IS 'Unique application identifier (e.g., XECHK, DM_BLZE)';
COMMENT ON COLUMN applications.metadata IS 'Additional application metadata in JSON format';

-- Flow records table
SELECT 'Creating flow_records table...' as status;
CREATE TABLE IF NOT EXISTS flow_records (
    id SERIAL PRIMARY KEY,
    app_id VARCHAR(255) REFERENCES applications(app_id) ON DELETE CASCADE,
    src_ip VARCHAR(45),
    src_hostname VARCHAR(255),
    dst_ip VARCHAR(45),
    dst_hostname VARCHAR(255),
    protocol VARCHAR(50),
    port INTEGER,
    bytes_in BIGINT DEFAULT 0,
    bytes_out BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

COMMENT ON TABLE flow_records IS 'Network flow records between applications';
COMMENT ON COLUMN flow_records.src_ip IS 'Source IP address (IPv4 or IPv6)';
COMMENT ON COLUMN flow_records.dst_ip IS 'Destination IP address (IPv4 or IPv6)';

-- Analysis results table
SELECT 'Creating analysis_results table...' as status;
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    app_id VARCHAR(255) REFERENCES applications(app_id) ON DELETE CASCADE,
    analysis_type VARCHAR(100),
    result JSONB,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE analysis_results IS 'AI/ML analysis results for applications';
COMMENT ON COLUMN analysis_results.analysis_type IS 'Type of analysis (e.g., zone_classification, dependency_detection)';
COMMENT ON COLUMN analysis_results.confidence IS 'Confidence score (0.0 to 1.0)';

-- Topology data table
SELECT 'Creating topology_data table...' as status;
CREATE TABLE IF NOT EXISTS topology_data (
    id SERIAL PRIMARY KEY,
    app_id VARCHAR(255) REFERENCES applications(app_id) ON DELETE CASCADE,
    security_zone VARCHAR(100),
    dependencies JSONB,
    characteristics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(app_id)
);

COMMENT ON TABLE topology_data IS 'Application topology with security zones and dependencies';
COMMENT ON COLUMN topology_data.security_zone IS 'Security zone (WEB_TIER, APP_TIER, DATA_TIER, etc.)';
COMMENT ON COLUMN topology_data.dependencies IS 'Application dependencies in JSON array format';
COMMENT ON COLUMN topology_data.characteristics IS 'Application characteristics (protocols, ports, etc.)';

-- Model metadata table
SELECT 'Creating model_metadata table...' as status;
CREATE TABLE IF NOT EXISTS model_metadata (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100),
    version VARCHAR(50),
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE model_metadata IS 'Machine learning model metadata and performance metrics';
COMMENT ON COLUMN model_metadata.model_type IS 'Model type (GNN, RNN, CNN, Attention, Ensemble)';
COMMENT ON COLUMN model_metadata.metrics IS 'Model performance metrics (accuracy, precision, recall, etc.)';

SELECT 'All tables created successfully' as status;

-- ============================================================================
-- SECTION 4: Indexes for Performance
-- ============================================================================

SELECT 'Creating indexes...' as status;

-- Flow records indexes
CREATE INDEX IF NOT EXISTS idx_flow_app_id ON flow_records(app_id);
CREATE INDEX IF NOT EXISTS idx_flow_src_ip ON flow_records(src_ip);
CREATE INDEX IF NOT EXISTS idx_flow_dst_ip ON flow_records(dst_ip);
CREATE INDEX IF NOT EXISTS idx_flow_protocol ON flow_records(protocol);
CREATE INDEX IF NOT EXISTS idx_flow_port ON flow_records(port);
CREATE INDEX IF NOT EXISTS idx_flow_created_at ON flow_records(created_at DESC);

-- Analysis results indexes
CREATE INDEX IF NOT EXISTS idx_analysis_app_id ON analysis_results(app_id);
CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis_results(analysis_type);
CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON analysis_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_confidence ON analysis_results(confidence DESC);

-- Topology data indexes
CREATE INDEX IF NOT EXISTS idx_topology_app_id ON topology_data(app_id);
CREATE INDEX IF NOT EXISTS idx_topology_zone ON topology_data(security_zone);
CREATE INDEX IF NOT EXISTS idx_topology_updated_at ON topology_data(updated_at DESC);

-- Model metadata indexes
CREATE INDEX IF NOT EXISTS idx_model_name ON model_metadata(model_name);
CREATE INDEX IF NOT EXISTS idx_model_type ON model_metadata(model_type);
CREATE INDEX IF NOT EXISTS idx_model_created_at ON model_metadata(created_at DESC);

-- JSONB indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_app_metadata ON applications USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_flow_metadata ON flow_records USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_analysis_result ON analysis_results USING GIN (result);
CREATE INDEX IF NOT EXISTS idx_topology_dependencies ON topology_data USING GIN (dependencies);
CREATE INDEX IF NOT EXISTS idx_topology_characteristics ON topology_data USING GIN (characteristics);

SELECT 'Indexes created successfully' as status;

-- ============================================================================
-- SECTION 5: Roles and Users
-- ============================================================================

SELECT 'Creating roles and users...' as status;

-- Create read-only role
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'network_analyzer_readonly') THEN
        CREATE ROLE network_analyzer_readonly;
    END IF;
END
$$;

COMMENT ON ROLE network_analyzer_readonly IS 'Read-only access to network analysis data';

-- Create read-write role
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'network_analyzer_readwrite') THEN
        CREATE ROLE network_analyzer_readwrite;
    END IF;
END
$$;

COMMENT ON ROLE network_analyzer_readwrite IS 'Read-write access to network analysis data';

-- Create admin role
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'network_analyzer_admin') THEN
        CREATE ROLE network_analyzer_admin;
    END IF;
END
$$;

COMMENT ON ROLE network_analyzer_admin IS 'Full admin access to network analysis database';

-- Create application user (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'network_analyzer') THEN
        CREATE USER network_analyzer WITH PASSWORD 'postgres';
    END IF;
END
$$;

COMMENT ON ROLE network_analyzer IS 'Application database user';

-- Update postgres user password (run this separately if needed)
-- ALTER USER postgres WITH PASSWORD 'postgres';

SELECT 'Roles and users created' as status;

-- ============================================================================
-- SECTION 6: Grant Permissions
-- ============================================================================

SELECT 'Granting permissions...' as status;

-- Grant read-only permissions
GRANT CONNECT ON DATABASE network_analysis TO network_analyzer_readonly;
GRANT USAGE ON SCHEMA public TO network_analyzer_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO network_analyzer_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO network_analyzer_readonly;

-- Grant read-write permissions
GRANT CONNECT ON DATABASE network_analysis TO network_analyzer_readwrite;
GRANT USAGE ON SCHEMA public TO network_analyzer_readwrite;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO network_analyzer_readwrite;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO network_analyzer_readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO network_analyzer_readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO network_analyzer_readwrite;

-- Grant admin permissions
GRANT ALL PRIVILEGES ON DATABASE network_analysis TO network_analyzer_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO network_analyzer_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO network_analyzer_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO network_analyzer_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO network_analyzer_admin;

-- Assign role to network_analyzer user
GRANT network_analyzer_readwrite TO network_analyzer;

-- Grant necessary permissions to postgres user (already superuser)
GRANT ALL PRIVILEGES ON DATABASE network_analysis TO postgres;

SELECT 'Permissions granted' as status;

-- ============================================================================
-- SECTION 7: Triggers for Updated Timestamps
-- ============================================================================

SELECT 'Creating triggers...' as status;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for applications table
DROP TRIGGER IF EXISTS update_applications_updated_at ON applications;
CREATE TRIGGER update_applications_updated_at
    BEFORE UPDATE ON applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for topology_data table
DROP TRIGGER IF EXISTS update_topology_updated_at ON topology_data;
CREATE TRIGGER update_topology_updated_at
    BEFORE UPDATE ON topology_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

SELECT 'Triggers created' as status;

-- ============================================================================
-- SECTION 8: Initial Data (Optional)
-- ============================================================================

SELECT 'Inserting initial data...' as status;

-- Insert default security zones (as reference data)
-- Note: This is optional and for documentation purposes

-- Example: Insert a test application (commented out)
-- INSERT INTO applications (app_id, app_name, metadata)
-- VALUES ('TEST_APP', 'Test Application', '{"type": "test", "environment": "development"}')
-- ON CONFLICT (app_id) DO NOTHING;

SELECT 'Initial data inserted (if any)' as status;

-- ============================================================================
-- SECTION 9: Statistics and Verification
-- ============================================================================

SELECT 'Database initialization complete!' as status;
SELECT '============================================' as separator;
SELECT 'Database Statistics:' as title;
SELECT '============================================' as separator;

-- Show table counts
SELECT 'Tables:' as metric, COUNT(*) as count
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

SELECT 'Indexes:' as metric, COUNT(*) as count
FROM pg_indexes
WHERE schemaname = 'public';

SELECT 'Roles:' as metric, COUNT(*) as count
FROM pg_roles
WHERE rolname LIKE 'network_analyzer%';

-- Show table list
SELECT '============================================' as separator;
SELECT 'Tables Created:' as title;
SELECT '============================================' as separator;
SELECT tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Show index list
SELECT '============================================' as separator;
SELECT 'Indexes Created:' as title;
SELECT '============================================' as separator;
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Show role list
SELECT '============================================' as separator;
SELECT 'Roles Created:' as title;
SELECT '============================================' as separator;
SELECT rolname, rolcanlogin, rolsuper
FROM pg_roles
WHERE rolname LIKE '%network%' OR rolname = 'postgres'
ORDER BY rolname;

SELECT '============================================' as separator;
SELECT 'Setup Instructions:' as title;
SELECT '============================================' as separator;
SELECT '1. Database: network_analysis' as step;
SELECT '2. Default user: postgres / postgres' as step;
SELECT '3. App user: network_analyzer / postgres' as step;
SELECT '4. Connection string: postgresql://postgres:postgres@localhost:5432/network_analysis' as step;
SELECT '5. Update config.yaml with database credentials' as step;
SELECT '============================================' as separator;

-- ============================================================================
-- END OF SCRIPT
-- ============================================================================

SELECT 'Database initialization completed successfully!' as status;
SELECT 'You can now connect using: psql -U postgres -d network_analysis' as info;
