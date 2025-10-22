-- Migration: Add Server Classification Columns
-- Created: 2025-10-22
-- Description: Adds columns to track server type, tier, and category classification

-- Add classification columns to enriched_flows table
ALTER TABLE enriched_flows
ADD COLUMN IF NOT EXISTS source_server_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS source_server_tier VARCHAR(50),
ADD COLUMN IF NOT EXISTS source_server_category VARCHAR(50),
ADD COLUMN IF NOT EXISTS dest_server_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS dest_server_tier VARCHAR(50),
ADD COLUMN IF NOT EXISTS dest_server_category VARCHAR(50);

-- Add indexes for classification columns for fast querying
CREATE INDEX IF NOT EXISTS idx_enriched_flows_src_server_type
ON enriched_flows(source_server_type);

CREATE INDEX IF NOT EXISTS idx_enriched_flows_dst_server_type
ON enriched_flows(dest_server_type);

CREATE INDEX IF NOT EXISTS idx_enriched_flows_src_server_tier
ON enriched_flows(source_server_tier);

CREATE INDEX IF NOT EXISTS idx_enriched_flows_dst_server_tier
ON enriched_flows(dest_server_tier);

-- Create materialized view for server classification statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS server_classification_stats AS
SELECT
    dest_server_type,
    dest_server_tier,
    dest_server_category,
    COUNT(*) as flow_count,
    SUM(bytes_in + bytes_out) as total_bytes,
    COUNT(DISTINCT source_app_code) as unique_source_apps,
    COUNT(DISTINCT dest_ip) as unique_dest_ips
FROM enriched_flows
WHERE dest_server_type IS NOT NULL
GROUP BY dest_server_type, dest_server_tier, dest_server_category
ORDER BY flow_count DESC;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_server_classification_stats
ON server_classification_stats(dest_server_type, dest_server_tier, dest_server_category);

-- Add comment describing the columns
COMMENT ON COLUMN enriched_flows.source_server_type IS 'Server type classification (e.g., DNS, F5 Load Balancer, MySQL/Oracle)';
COMMENT ON COLUMN enriched_flows.source_server_tier IS 'Server tier (web, app, database, infrastructure, security, cloud)';
COMMENT ON COLUMN enriched_flows.source_server_category IS 'Server category for grouping';
COMMENT ON COLUMN enriched_flows.dest_server_type IS 'Destination server type classification';
COMMENT ON COLUMN enriched_flows.dest_server_tier IS 'Destination server tier';
COMMENT ON COLUMN enriched_flows.dest_server_category IS 'Destination server category';
