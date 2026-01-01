"""
Migration runner script to apply database migrations
"""
import sqlite3
import os

def run_migrations():
    """Run all migration files in the migrations directory"""
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    # List of migration files to run in order
    migration_files = [
        'migrations/migration_001_add_currencies.sql',
        'migrations/migration_002_extend_transactions.sql',
        'migrations/migration_003_audit_logs.sql',
        'migrations/migration_004_bank_integration.sql'
    ]
    
    for migration_file in migration_files:
        if os.path.exists(migration_file):
            print(f"Running migration: {migration_file}")
            with open(migration_file, 'r') as f:
                sql_commands = f.read()
                
            # Split and execute commands (separated by semicolons)
            commands = sql_commands.split(';')
            for command in commands:
                command = command.strip()
                if command:
                    try:
                        cursor.execute(command)
                    except sqlite3.Error as e:
                        print(f"Error executing command: {command[:50]}... - Error: {e}")
            
            print(f"Completed migration: {migration_file}")
        else:
            print(f"Migration file not found: {migration_file}")
    
    conn.commit()
    conn.close()
    print("All migrations completed!")

if __name__ == "__main__":
    run_migrations()