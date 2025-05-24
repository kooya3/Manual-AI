-- Create the manuals table
CREATE TABLE IF NOT EXISTS manuals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    size BIGINT NOT NULL,
    upload_date TIMESTAMP DEFAULT NOW(),
    status TEXT DEFAULT 'pending',
    metadata JSONB,
    content TEXT,
    processing_status TEXT DEFAULT 'unprocessed'
);

-- Enable Row-Level Security (RLS)
ALTER TABLE manuals ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow access to authenticated users
CREATE POLICY "Allow authenticated users" ON manuals
    FOR ALL
    USING (auth.uid() IS NOT NULL);
