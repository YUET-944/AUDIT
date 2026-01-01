-- migration_002_extend_transactions.sql
-- Add currency-related columns to transactions table
ALTER TABLE transactions ADD COLUMN currency_code TEXT DEFAULT 'PKR';
ALTER TABLE transactions ADD COLUMN base_currency_amount REAL;
ALTER TABLE transactions ADD COLUMN exchange_rate REAL;

-- Update existing transactions to have PKR as default currency
UPDATE transactions SET currency_code = 'PKR' WHERE currency_code IS NULL;
UPDATE transactions SET base_currency_amount = amount WHERE base_currency_amount IS NULL;
UPDATE transactions SET exchange_rate = 1.0 WHERE exchange_rate IS NULL;