-- PostgreSQL Table Creation Script
-- =================================
-- Schema: activenet
-- Database: prutech_bais
-- User: activenet_admin
--
-- INSTRUCTIONS FOR DBA:
-- 1. Review this script
-- 2. Connect to database: psql -h udideapdb01.unix.rgbk.com -U postgres -d prutech_bais
-- 3. Run this script: \i create_tables.sql
-- 4. Verify tables: \dt activenet.*
--
-- NOTE: This script is SAFE to run multiple times (uses IF NOT EXISTS)

-- 1. Create main enriched flows table with server classification
-- Using fully qualified name: database.schema.table
CREATE TABLE IF NOT EXISTS prutech_bais.activenet.enriched_flows (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Source information
    source_app_code VARCHAR(50) NOT NULL,
    source_ip INET NOT NULL,
    source_hostname VARCHAR(255),
    source_device_type VARCHAR(50),

    -- Destination information
    dest_ip INET NOT NULL,
    dest_hostname VARCHAR(255),
    dest_device_type VARCHAR(50),
    dest_app_code VARCHAR(50),

    -- Flow details
    protocol VARCHAR(20),
    port INTEGER,
    bytes_in BIGINT DEFAULT 0,
    bytes_out BIGINT DEFAULT 0,

    -- Metadata
    flow_direction VARCHAR(20),
    flow_count INTEGER DEFAULT 1,
    has_missing_data BOOLEAN DEFAULT FALSE,
    missing_fields TEXT[],

    -- Server Classification (added for enhanced diagrams)
    source_server_type VARCHAR(50),
    source_server_tier VARCHAR(50),
    source_server_category VARCHAR(50),
    dest_server_type VARCHAR(50),
    dest_server_tier VARCHAR(50),
    dest_server_category VARCHAR(50),

    -- Batch tracking
    batch_id VARCHAR(100),
    file_source VARCHAR(255)
);

-- 2. Create DNS cache table
CREATE TABLE IF NOT EXISTS prutech_bais.activenet.dns_cache (
    ip INET PRIMARY KEY,
    hostname VARCHAR(255),
    resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ttl INTEGER DEFAULT 86400
);

-- 3. Create flow aggregates table
CREATE TABLE IF NOT EXISTS prutech_bais.activenet.flow_aggregates (
    id SERIAL PRIMARY KEY,
    source_app_code VARCHAR(50),
    dest_app_code VARCHAR(50),
    flow_direction VARCHAR(20),
    total_flows INTEGER,
    total_bytes_in BIGINT,
    total_bytes_out BIGINT,
    unique_source_ips INTEGER,
    unique_dest_ips INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(source_app_code, dest_app_code, flow_direction)
);

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_enriched_flows_src_app ON activenet.enriched_flows(source_app_code);
CREATE INDEX IF NOT EXISTS idx_enriched_flows_dst_app ON activenet.enriched_flows(dest_app_code);
CREATE INDEX IF NOT EXISTS idx_enriched_flows_src_ip ON activenet.enriched_flows(source_ip);
CREATE INDEX IF NOT EXISTS idx_enriched_flows_dst_ip ON activenet.enriched_flows(dest_ip);
CREATE INDEX IF NOT EXISTS idx_enriched_flows_flow_direction ON activenet.enriched_flows(flow_direction);
CREATE INDEX IF NOT EXISTS idx_enriched_flows_created_at ON activenet.enriched_flows(created_at);

-- Server classification indexes (for post-processing diagrams)
CREATE INDEX IF NOT EXISTS idx_enriched_flows_src_server_type ON activenet.enriched_flows(source_server_type);
CREATE INDEX IF NOT EXISTS idx_enriched_flows_dst_server_type ON activenet.enriched_flows(dest_server_type);
CREATE INDEX IF NOT EXISTS idx_enriched_flows_src_server_tier ON activenet.enriched_flows(source_server_tier);
CREATE INDEX IF NOT EXISTS idx_enriched_flows_dst_server_tier ON activenet.enriched_flows(dest_server_tier);

-- 5. Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON activenet.enriched_flows TO activenet_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON activenet.dns_cache TO activenet_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON activenet.flow_aggregates TO activenet_admin;
GRANT USAGE, SELECT ON SEQUENCE activenet.enriched_flows_id_seq TO activenet_admin;
GRANT USAGE, SELECT ON SEQUENCE activenet.flow_aggregates_id_seq TO activenet_admin;

-- 6. Verification queries
SELECT 'Tables created successfully!' as status;

SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'activenet'
ORDER BY tablename;

-- 7. Verify permissions
SELECT
    table_schema,
    table_name,
    privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'activenet_admin'
  AND table_schema = 'activenet'
ORDER BY table_name, privilege_type;
