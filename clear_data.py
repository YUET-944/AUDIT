"""
Script to clear all data from the financial dashboard database.
"""

import sqlite3
import os


def clear_database():
    """Clear all data from the finance.db database."""
    # Check if database file exists
    if os.path.exists('finance.db'):
        try:
            # Connect to the database
            conn = sqlite3.connect('finance.db')
            cursor = conn.cursor()
            
            # Delete all data from tables
            cursor.execute("DELETE FROM transactions")
            cursor.execute("DELETE FROM employees")
            cursor.execute("DELETE FROM budgets")
            
            # Reset autoincrement counters
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='employees'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='budgets'")
            
            # Commit changes and close connection
            conn.commit()
            conn.close()
            
            print("All data cleared successfully!")
            
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
    else:
        print("Database file 'finance.db' not found.")


def reset_database():
    """Reset the database by dropping and recreating tables."""
    # Check if database file exists
    if os.path.exists('finance.db'):
        try:
            # Connect to the database
            conn = sqlite3.connect('finance.db')
            cursor = conn.cursor()
            
            # Drop existing tables
            cursor.execute("DROP TABLE IF EXISTS transactions")
            cursor.execute("DROP TABLE IF EXISTS employees")
            cursor.execute("DROP TABLE IF EXISTS budgets")
            
            # Commit changes
            conn.commit()
            conn.close()
            
            print("Database tables dropped successfully!")
            print("Restart the application to recreate tables with fresh schema.")
            
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
    else:
        print("Database file 'finance.db' not found.")


if __name__ == "__main__":
    print("Choose an option:")
    print("1. Clear all data (keep table structure)")
    print("2. Reset database (drop tables)")
    
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == "1":
        clear_database()
    elif choice == "2":
        reset_database()
    else:
        print("Invalid choice. Please run the script again and choose 1 or 2.")