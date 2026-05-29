-- Supabase SQL Schema for Sniper-Indicator Trading Assistant

-- Create the active_trades table
CREATE TABLE public.active_trades (
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
-- By default, we enable RLS to secure the data.
ALTER TABLE public.active_trades ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows all authenticated and anon roles to insert/select/update
-- (Modify this in production if you want strictly authenticated access)
CREATE POLICY "Enable read access for all users" ON public.active_trades FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON public.active_trades FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON public.active_trades FOR UPDATE USING (true);

-- Create a function and trigger to automatically update the 'updated_at' column
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_active_trades_modtime
    BEFORE UPDATE ON public.active_trades
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();