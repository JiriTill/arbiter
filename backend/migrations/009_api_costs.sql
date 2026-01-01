-- Migration: Add API costs tracking
CREATE TABLE IF NOT EXISTS api_costs (
  id BIGSERIAL PRIMARY KEY,
  request_id UUID NOT NULL,
  endpoint TEXT NOT NULL,  -- '/ask' | '/ingest'
  model TEXT NOT NULL,
  input_tokens INT NOT NULL,
  output_tokens INT NOT NULL,
  cost_usd DECIMAL(10, 6) NOT NULL,
  cache_hit BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX api_costs_created_idx ON api_costs(created_at);
CREATE INDEX api_costs_endpoint_idx ON api_costs(endpoint);
