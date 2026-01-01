"""
Migration script to move from SQLite to PostgreSQL
"""
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import os

class SQLiteToPostgreSQLMigration:
    def __init__(self, sqlite_path, postgres_config):
        self.sqlite_conn = sqlite3.connect(sqlite_path)
        self.postgres_conn = psycopg2.connect(**postgres_config)
    
    def migrate_table(self, table_name, postgres_schema):
        """Migrate a single table from SQLite to PostgreSQL"""
        # Create table in PostgreSQL
        with self.postgres_conn.cursor() as cursor:
            cursor.execute(postgres_schema)
        
        # Read from SQLite
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", self.sqlite_conn)
        
        # Insert into PostgreSQL
        if not df.empty:
            with self.postgres_conn.cursor() as cursor:
                columns = ', '.join(df.columns)
                placeholders = ', '.join(['%s'] * len(df.columns))
                insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                
                for _, row in df.iterrows():
                    cursor.execute(insert_query, tuple(row))
        
        self.postgres_conn.commit()
    
    def migrate_all_tables(self):
        """Migrate all tables with appropriate PostgreSQL schemas"""
        tables_schemas = {
            'currencies': '''
                CREATE TABLE currencies (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(3) UNIQUE NOT NULL,
                    name VARCHAR(50) NOT NULL,
                    symbol VARCHAR(5),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'transactions': '''
                CREATE TABLE transactions (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    type VARCHAR(20) NOT NULL,
                    currency_code VARCHAR(3) DEFAULT 'PKR',
                    base_currency_amount DECIMAL(15,2),
                    exchange_rate DECIMAL(10,6),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'audit_logs': '''
                CREATE TABLE audit_logs (
                    id SERIAL PRIMARY KEY,
                    entity_type VARCHAR(50) NOT NULL,
                    entity_id INTEGER NOT NULL,
                    action VARCHAR(20) NOT NULL,
                    old_values JSONB,
                    new_values JSONB,
                    user_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address INET,
                    session_id VARCHAR(100),
                    hash_value VARCHAR(64) NOT NULL
                )
            ''',
            'bank_accounts': '''
                CREATE TABLE bank_accounts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    account_number VARCHAR(50),
                    bank_name VARCHAR(100) NOT NULL,
                    currency_code VARCHAR(3) DEFAULT 'PKR',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'bank_transactions': '''
                CREATE TABLE bank_transactions (
                    id SERIAL PRIMARY KEY,
                    bank_account_id INTEGER REFERENCES bank_accounts(id),
                    external_transaction_id VARCHAR(100),
                    date DATE NOT NULL,
                    description TEXT NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    currency_code VARCHAR(3) DEFAULT 'PKR',
                    status VARCHAR(20) DEFAULT 'pending',
                    matched_transaction_id INTEGER REFERENCES transactions(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'company_investments': '''
                CREATE TABLE company_investments (
                    id SERIAL PRIMARY KEY,
                    investor_name TEXT NOT NULL,
                    investment_type TEXT NOT NULL,
                    investment_date DATE NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    equity_percentage DECIMAL(5,2),
                    status VARCHAR(20) NOT NULL DEFAULT 'Active'
                )
            ''',
            'loans': '''
                CREATE TABLE loans (
                    id SERIAL PRIMARY KEY,
                    lender_name TEXT NOT NULL,
                    loan_type TEXT NOT NULL,
                    loan_date DATE NOT NULL,
                    principal_amount DECIMAL(15,2) NOT NULL,
                    interest_rate DECIMAL(5,4) NOT NULL,
                    monthly_payment DECIMAL(15,2) NOT NULL,
                    total_payments INTEGER NOT NULL,
                    remaining_payments INTEGER NOT NULL,
                    loan_direction VARCHAR(10) NOT NULL DEFAULT 'Inbound',
                    status VARCHAR(20) NOT NULL DEFAULT 'Active'
                )
            ''',
            'employees': '''
                CREATE TABLE employees (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    department TEXT NOT NULL,
                    base_salary DECIMAL(10,2) NOT NULL,
                    tax_rate DECIMAL(5,4) NOT NULL,
                    deductions DECIMAL(10,2) NOT NULL
                )
            ''',
            'budgets': '''
                CREATE TABLE budgets (
                    id SERIAL PRIMARY KEY,
                    category TEXT NOT NULL UNIQUE,
                    monthly_budget DECIMAL(10,2) NOT NULL,
                    actual_spent DECIMAL(10,2) DEFAULT 0
                )
            '''
        }
        
        for table_name, schema in tables_schemas.items():
            print(f"Migrating {table_name}...")
            self.migrate_table(table_name, schema)
        
        self.sqlite_conn.close()
        self.postgres_conn.close()

if __name__ == "__main__":
    # Example usage
    postgres_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'database': os.getenv('POSTGRES_DB', 'algohub'),
        'user': os.getenv('POSTGRES_USER', 'user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password')
    }
    
    migrator = SQLiteToPostgreSQLMigration('finance.db', postgres_config)
    migrator.migrate_all_tables()