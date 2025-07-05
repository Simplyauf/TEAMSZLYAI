-- Initialize Knowledge Base Database
-- This script sets up the initial database structure

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_source_type ON documents(source_type);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_sync_logs_source_name ON sync_logs(source_name);
CREATE INDEX IF NOT EXISTS idx_sync_logs_created_at ON sync_logs(created_at);

-- Insert default data sources
INSERT INTO data_sources (name, source_type, config, status)
VALUES
    ('slack-workspace', 'slack', '{}', 'active')
ON CONFLICT (name) DO NOTHING;