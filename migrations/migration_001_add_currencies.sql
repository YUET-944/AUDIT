-- migration_001_add_currencies.sql
CREATE TABLE IF NOT EXISTS currencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    symbol TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert default currency
INSERT OR IGNORE INTO currencies (code, name, symbol, is_active) 
VALUES ('PKR', 'Pakistani Rupee', 'Rs', 1);