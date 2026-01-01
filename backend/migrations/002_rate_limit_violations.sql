-- Migration: 002_rate_limit_violations.sql
-- Rate limit violation tracking for analysis

-- Rate limit violations table
CREATE TABLE IF NOT EXISTS rate_limit_violations (
    id SERIAL PRIMARY KEY,
    
    -- Request info
    client_ip VARCHAR(45) NOT NULL,  -- IPv6 can be up to 45 chars
    endpoint VARCHAR(100) NOT NULL,
    method VARCHAR(10) NOT NULL,
    
    -- Rate limit info
    limit_type VARCHAR(50) NOT NULL,  -- 'ip', 'session', 'concurrent'
    limit_value INTEGER NOT NULL,
    window_seconds INTEGER,
    
    -- Context
    session_id VARCHAR(255),
    user_agent TEXT,
    request_path TEXT,
    
    -- Timestamps
    violated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Indexes for analysis
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for querying by IP
CREATE INDEX IF NOT EXISTS idx_rate_violations_ip 
    ON rate_limit_violations(client_ip, violated_at DESC);

-- Index for querying by endpoint
CREATE INDEX IF NOT EXISTS idx_rate_violations_endpoint 
    ON rate_limit_violations(endpoint, violated_at DESC);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_rate_violations_time 
    ON rate_limit_violations(violated_at DESC);

-- Partial index for recent violations
CREATE INDEX IF NOT EXISTS idx_rate_violations_recent 
    ON rate_limit_violations(violated_at) 
    WHERE violated_at > NOW() - INTERVAL '24 hours';

-- Function to clean up old violations (keep last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_rate_violations()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM rate_limit_violations 
    WHERE violated_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Optional: View for analyzing frequent violators
CREATE OR REPLACE VIEW rate_limit_frequent_violators AS
SELECT 
    client_ip,
    endpoint,
    COUNT(*) as violation_count,
    MIN(violated_at) as first_violation,
    MAX(violated_at) as last_violation
FROM rate_limit_violations
WHERE violated_at > NOW() - INTERVAL '24 hours'
GROUP BY client_ip, endpoint
HAVING COUNT(*) >= 5
ORDER BY violation_count DESC;

COMMENT ON TABLE rate_limit_violations IS 'Tracks rate limit violations for security analysis';
