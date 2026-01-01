"""
Script to initialize the database with sample data for demonstration purposes.
"""

from database import (
    init_db, add_transaction, add_employee, add_budget
)
from datetime import datetime, timedelta


def populate_sample_data():
    """Populate the database with sample data."""
    # Initialize the database
    init_db()
    
    # Add sample transactions
    transactions = [
        # Income transactions
        ("2023-01-15", "Product Sales", "Sales", 15000.00, "Income"),
        ("2023-02-20", "Service Revenue", "Services", 12000.00, "Income"),
        ("2023-03-10", "Investment Return", "Investments", 5000.00, "Income"),
        
        # Expense transactions
        ("2023-01-05", "Office Rent", "Rent", 3000.00, "Expense"),
        ("2023-01-10", "Marketing Campaign", "Marketing", 2500.00, "Expense"),
        ("2023-01-18", "Utilities", "Utilities", 800.00, "Expense"),
        ("2023-02-05", "Office Rent", "Rent", 3000.00, "Expense"),
        ("2023-02-12", "Software Licenses", "Operations", 1200.00, "Expense"),
        ("2023-02-25", "Utilities", "Utilities", 850.00, "Expense"),
        ("2023-03-05", "Office Rent", "Rent", 3000.00, "Expense"),
        ("2023-03-15", "Employee Training", "Operations", 1500.00, "Expense"),
        
        # Salary transactions
        ("2023-01-28", "Employee Salaries", "Salaries", 25000.00, "Salary"),
        ("2023-02-28", "Employee Salaries", "Salaries", 25000.00, "Salary"),
        ("2023-03-31", "Employee Salaries", "Salaries", 25000.00, "Salary"),
        
        # Investment transactions
        ("2023-01-10", "Server Equipment", "Equipment", 10000.00, "Investment"),
        ("2023-02-05", "Company Stocks", "Stocks", 20000.00, "Investment"),
    ]
    
    for date, desc, category, amount, trans_type in transactions:
        add_transaction(date, desc, category, amount, trans_type)
    
    # Add sample employees
    employees = [
        ("John Smith", "Engineering", 75000.00, 0.25, 500.00),
        ("Sarah Johnson", "Marketing", 65000.00, 0.22, 400.00),
        ("Michael Lee", "Sales", 70000.00, 0.23, 450.00),
        ("Emily Davis", "HR", 60000.00, 0.20, 350.00),
        ("Robert Wilson", "Finance", 68000.00, 0.24, 420.00),
    ]
    
    for name, dept, salary, tax, deduct in employees:
        add_employee(name, dept, salary, tax, deduct)
    
    # Add sample budgets
    budgets = [
        ("Marketing", 5000.00),
        ("Rent", 3500.00),
        ("Utilities", 1000.00),
        ("Operations", 2000.00),
        ("Salaries", 30000.00),
    ]
    
    for category, budget in budgets:
        add_budget(category, budget)
    
    print("Sample data populated successfully!")


if __name__ == "__main__":
    populate_sample_data()