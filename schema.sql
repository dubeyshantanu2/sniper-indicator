-- Supabase SQL Schema for Sniper-Indicator Trading Assistant

-- Use IF NOT EXISTS to prevent the 'relation already exists' error
CREATE TABLE IF NOT EXISTS public.sniper_active_trades (
    id UUID NOT NULL PRIMARY KEY DEFAULT uuid_generate_v4(),
    trade_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    direction TEXT NOT NULL, -- 'LONG' or 'SHORT'
    entry_price NUMERIC NOT NULL,
    sl_price NUMERIC NOT NULL,
    t1_price NUMERIC NOT NULL,
    t2_price NUMERIC NOT NULL,
    t3_price NUMERIC NOT NULL,
    suggested_strike TEXT,
    status TEXT NOT NULL DEFAULT 'Active', -- 'Active', 'T1', 'T2', 'Closed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('Asia/Kolkata'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('Asia/Kolkata'::text, now()) NOT NULL
);

-- Set up Row Level Security (RLS)
ALTER TABLE public.sniper_active_trades ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to prevent 'policy already exists' errors if run multiple times
DROP POLICY IF EXISTS "Enable read access for all users" ON public.sniper_active_trades;
DROP POLICY IF EXISTS "Enable insert access for all users" ON public.sniper_active_trades;
DROP POLICY IF EXISTS "Enable update access for all users" ON public.sniper_active_trades;

-- Create policies
CREATE POLICY "Enable read access for all users" ON public.sniper_active_trades FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON public.sniper_active_trades FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON public.sniper_active_trades FOR UPDATE USING (true);

-- Create or Replace the function
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('Asia/Kolkata'::text, now());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop the trigger if it exists before creating it again
DROP TRIGGER IF EXISTS update_sniper_active_trades_modtime ON public.sniper_active_trades;

CREATE TRIGGER update_sniper_active_trades_modtime
    BEFORE UPDATE ON public.sniper_active_trades
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();