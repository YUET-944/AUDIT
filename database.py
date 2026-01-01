"""
Database module for the financial dashboard application.
Handles all SQLite database operations for transactions, employees, and budgets.
"""

import sqlite3
import pandas as pd
import threading
import time

# Create a lock for database operations to prevent concurrent access
_db_lock = threading.Lock()

from database_pool import db_pool


def get_db_connection():
    """Get a database connection with timeout"""
    # Return a connection from the pool
    conn = sqlite3.connect('finance.db', timeout=10)
    return conn


def get_db_connection_pooled():
    """Get a database connection from the pool"""
    from database_pool import db_pool
    return db_pool.get_connection()


def init_db():
    """Initialize the database with required tables."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
    
    # Create currencies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS currencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            symbol TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default currency if not exists
    cursor.execute("INSERT OR IGNORE INTO currencies (code, name, symbol, is_active) VALUES ('PKR', 'Pakistani Rupee', 'Rs', 1)")
    
    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('Income', 'Expense', 'Salary', 'Investment', 'Loan')),
            currency_code TEXT DEFAULT 'PKR',
            base_currency_amount REAL,
            exchange_rate REAL
        )
    ''')
    
    # Create audit_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            old_values TEXT,
            new_values TEXT,
            user_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            session_id TEXT,
            hash_value TEXT NOT NULL
        )
    ''')
    
    # Create bank_accounts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            account_number TEXT,
            bank_name TEXT NOT NULL,
            currency_code TEXT DEFAULT 'PKR',
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create bank_transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bank_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_account_id INTEGER,
            external_transaction_id TEXT,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            currency_code TEXT DEFAULT 'PKR',
            status TEXT DEFAULT 'pending',
            matched_transaction_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id),
            FOREIGN KEY (matched_transaction_id) REFERENCES transactions(id)
        )
    ''')
    
    # Create investments table (for investments in the company)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_investments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investor_name TEXT NOT NULL,
            investment_type TEXT NOT NULL,
            investment_date TEXT NOT NULL,
            amount REAL NOT NULL,
            equity_percentage REAL,
            status TEXT NOT NULL DEFAULT 'Active'
        )
    ''')
    
    # Create loans table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lender_name TEXT NOT NULL,
            loan_type TEXT NOT NULL,
            loan_date TEXT NOT NULL,
            principal_amount REAL NOT NULL,
            interest_rate REAL NOT NULL,
            monthly_payment REAL NOT NULL,
            total_payments INTEGER NOT NULL,
            remaining_payments INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active'
        )
    ''')
    
    # Check if loan_direction column exists, if not, add it
    cursor.execute("PRAGMA table_info(loans)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'loan_direction' not in columns:
        cursor.execute("ALTER TABLE loans ADD COLUMN loan_direction TEXT NOT NULL DEFAULT 'Inbound'")
    
    # Create employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            base_salary REAL NOT NULL,
            tax_rate REAL NOT NULL,
            deductions REAL NOT NULL
        )
    ''')
    
    # Create budgets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL UNIQUE,
            monthly_budget REAL NOT NULL,
            actual_spent REAL DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()


def add_transaction(date, description, category, amount, trans_type):
    """Add a new transaction to the database."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO transactions (date, description, category, amount, type)
        VALUES (?, ?, ?, ?, ?)
    ''', (date, description, category, amount, trans_type))
    
    conn.commit()
    conn.close()


def get_transactions(page=1, page_size=50):
    """Retrieve all transactions from the database with pagination."""
    offset = (page - 1) * page_size
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC LIMIT ? OFFSET ?", conn, params=(page_size, offset))
        conn.close()
    return df


def get_transaction_count():
    """Get the total count of transactions in the database."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM transactions')
        count = cursor.fetchone()[0]
        conn.close()
    return count


def search_transactions(query=None, start_date=None, end_date=None, category=None, trans_type=None, page=1, page_size=50):
    """Search and filter transactions based on various criteria."""
    offset = (page - 1) * page_size
    
    # Build the query and parameters
    base_query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    # Add search query filter
    if query:
        base_query += " AND (description LIKE ? OR category LIKE ?)"
        params.extend([f'%{query}%', f'%{query}%'])
    
    # Add date range filter
    if start_date:
        base_query += " AND date >= ?"
        params.append(str(start_date))
    if end_date:
        base_query += " AND date <= ?"
        params.append(str(end_date))
    
    # Add category filter
    if category and category != 'All':
        base_query += " AND category = ?"
        params.append(category)
    
    # Add type filter
    if trans_type and trans_type != 'All':
        base_query += " AND type = ?"
        params.append(trans_type)
    
    # Order by date descending
    base_query += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params.extend([page_size, offset])
    
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        df = pd.read_sql_query(base_query, conn, params=params)
        conn.close()
    return df


def get_transaction_count_filtered(query=None, start_date=None, end_date=None, category=None, trans_type=None):
    """Get the count of transactions matching the filter criteria."""
    base_query = "SELECT COUNT(*) FROM transactions WHERE 1=1"
    params = []
    
    # Add search query filter
    if query:
        base_query += " AND (description LIKE ? OR category LIKE ?)"
        params.extend([f'%{query}%', f'%{query}%'])
    
    # Add date range filter
    if start_date:
        base_query += " AND date >= ?"
        params.append(str(start_date))
    if end_date:
        base_query += " AND date <= ?"
        params.append(str(end_date))
    
    # Add category filter
    if category and category != 'All':
        base_query += " AND category = ?"
        params.append(category)
    
    # Add type filter
    if trans_type and trans_type != 'All':
        base_query += " AND type = ?"
        params.append(trans_type)
    
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
        cursor.execute(base_query, params)
        count = cursor.fetchone()[0]
        conn.close()
    return count


def update_transaction(trans_id, date, description, category, amount, trans_type):
    """Update an existing transaction."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE transactions
        SET date = ?, description = ?, category = ?, amount = ?, type = ?
        WHERE id = ?
    ''', (date, description, category, amount, trans_type, trans_id))
    
    conn.commit()
    conn.close()


def delete_transaction(trans_id):
    """Delete a transaction from the database."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM transactions WHERE id = ?', (trans_id,))
        
        conn.commit()
        conn.close()


def add_employee(name, department, base_salary, tax_rate, deductions):
    """Add a new employee to the database."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO employees (name, department, base_salary, tax_rate, deductions)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, department, base_salary, tax_rate, deductions))
    
    conn.commit()
    conn.close()


def get_employees():
    """Retrieve all employees from the database."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        df = pd.read_sql_query("SELECT * FROM employees", conn)
        conn.close()
    return df


def update_employee(emp_id, name, department, base_salary, tax_rate, deductions):
    """Update an existing employee."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE employees
        SET name = ?, department = ?, base_salary = ?, tax_rate = ?, deductions = ?
        WHERE id = ?
    ''', (name, department, base_salary, tax_rate, deductions, emp_id))
    
    conn.commit()
    conn.close()


def delete_employee(emp_id):
    """Delete an employee from the database."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM employees WHERE id = ?', (emp_id,))
        
        conn.commit()
        conn.close()


def add_budget(category, monthly_budget):
    """Add a new budget category."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO budgets (category, monthly_budget, actual_spent)
        VALUES (?, ?, COALESCE((SELECT actual_spent FROM budgets WHERE category = ?), 0))
    ''', (category, monthly_budget, category))
    
    conn.commit()
    conn.close()


def get_budgets():
    """Retrieve all budget categories."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        df = pd.read_sql_query("SELECT * FROM budgets", conn)
        conn.close()
    return df


def update_budget(budget_id, category, monthly_budget):
    """Update an existing budget category."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE budgets
        SET category = ?, monthly_budget = ?
        WHERE id = ?
    ''', (category, monthly_budget, budget_id))
    
    conn.commit()
    conn.close()


def delete_budget(budget_id):
    """Delete a budget category."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM budgets WHERE id = ?', (budget_id,))
        
        conn.commit()
        conn.close()


def update_actual_spent():
    """Update actual spent amounts in budgets based on transactions."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
    
    # Get all budget categories
    cursor.execute("SELECT category FROM budgets")
    categories = [row[0] for row in cursor.fetchall()]
    
    # For each category, calculate actual spent and update
    for category in categories:
        cursor.execute("""
            SELECT SUM(amount) 
            FROM transactions 
            WHERE category = ? AND type IN ('Expense', 'Salary')
        """, (category,))
        
        result = cursor.fetchone()
        actual_spent = result[0] if result[0] else 0
        
        cursor.execute("""
            UPDATE budgets 
            SET actual_spent = ? 
            WHERE category = ?
        """, (actual_spent, category))
    
    conn.commit()
    conn.close()


def get_financial_summary():
    """Get financial summary data for dashboard."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
    
    # Calculate total revenue (Income + Company Investments + Inbound Loans)
    revenue_df = pd.read_sql_query("""
        SELECT SUM(amount) as total_revenue 
        FROM transactions 
        WHERE type IN ('Income')
    """, conn)
    
    investment_df = pd.read_sql_query("""
        SELECT SUM(amount) as total_investments 
        FROM company_investments
    """, conn)
    
    # Get inbound loans (loans received by company) as part of revenue
    inbound_loans_df = pd.read_sql_query("""
        SELECT SUM(principal_amount) as total_inbound_loans
        FROM loans
        WHERE loan_direction = 'Inbound'
    """, conn)
    
    total_revenue = revenue_df['total_revenue'].iloc[0] if not revenue_df.empty and revenue_df['total_revenue'].iloc[0] else 0
    total_investments = investment_df['total_investments'].iloc[0] if not investment_df.empty and investment_df['total_investments'].iloc[0] else 0
    total_inbound_loans = inbound_loans_df['total_inbound_loans'].iloc[0] if not inbound_loans_df.empty and inbound_loans_df['total_inbound_loans'].iloc[0] else 0
    
    total_revenue += total_investments  # Include company investments in total revenue
    total_revenue += total_inbound_loans  # Include inbound loans as revenue
    
    # Calculate total expenses (Expense + Salary)
    expenses_df = pd.read_sql_query("""
        SELECT SUM(amount) as total_expenses 
        FROM transactions 
        WHERE type IN ('Expense', 'Salary')
    """, conn)
    
    total_expenses = expenses_df['total_expenses'].iloc[0] if not expenses_df.empty and expenses_df['total_expenses'].iloc[0] else 0
    
    # Calculate net profit
    net_profit = total_revenue - total_expenses
    
    # Calculate current cash balance
    cash_balance_df = pd.read_sql_query("""
        SELECT 
            (SELECT SUM(amount) FROM transactions WHERE type IN ('Income')) +
            (SELECT SUM(amount) FROM company_investments) +
            (SELECT SUM(principal_amount) FROM loans WHERE loan_direction = 'Inbound') -
            (SELECT SUM(amount) FROM transactions WHERE type IN ('Expense', 'Salary')) as cash_balance
    """, conn)
    
    cash_balance = cash_balance_df['cash_balance'].iloc[0] if not cash_balance_df.empty and cash_balance_df['cash_balance'].iloc[0] else 0
    
    conn.close()
    
    return {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'cash_balance': cash_balance
    }


def get_monthly_financial_data(months=12):
    """Get monthly financial data for the last N months."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
    
    # Get income data by month
    income_df = pd.read_sql_query("""
        SELECT 
            strftime('%Y-%m', date) as month,
            SUM(amount) as income
        FROM transactions 
        WHERE type IN ('Income')
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month DESC
        LIMIT ?
    """, conn, params=(months,))
    
    # Get company investment data by month
    investment_df = pd.read_sql_query("""
        SELECT 
            strftime('%Y-%m', investment_date) as month,
            SUM(amount) as investments
        FROM company_investments
        GROUP BY strftime('%Y-%m', investment_date)
        ORDER BY month DESC
    """, conn)
    
    # Get inbound loan data by month
    inbound_loans_df = pd.read_sql_query("""
        SELECT 
            strftime('%Y-%m', loan_date) as month,
            SUM(principal_amount) as inbound_loans
        FROM loans
        WHERE loan_direction = 'Inbound'
        GROUP BY strftime('%Y-%m', loan_date)
        ORDER BY month DESC
    """, conn)
    
    # Get expense data by month
    expense_df = pd.read_sql_query("""
        SELECT 
            strftime('%Y-%m', date) as month,
            SUM(amount) as expenses
        FROM transactions 
        WHERE type IN ('Expense', 'Salary')
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month DESC
        LIMIT ?
    """, conn, params=(months,))
    
    conn.close()
    
    # Merge income and expense dataframes
    monthly_df = pd.merge(income_df, expense_df, on='month', how='outer').fillna(0)
    # Merge with investment data
    monthly_df = pd.merge(monthly_df, investment_df, on='month', how='outer').fillna(0)
    # Merge with inbound loan data
    monthly_df = pd.merge(monthly_df, inbound_loans_df, on='month', how='outer').fillna(0)
    # Combine income, investments, and inbound loans
    monthly_df['income'] = monthly_df['income'] + monthly_df['investments'] + monthly_df['inbound_loans']
    monthly_df = monthly_df.drop(['investments', 'inbound_loans'], axis=1)
    monthly_df = monthly_df.sort_values('month')
    
    return monthly_df


def get_expense_by_category():
    """Get expense data grouped by category."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
    
    expense_df = pd.read_sql_query("""
        SELECT 
            category,
            SUM(amount) as total_expense
        FROM transactions 
        WHERE type IN ('Expense', 'Salary')
        GROUP BY category
    """, conn)
    
    conn.close()
    return expense_df


def get_payroll_summary():
    """Get payroll summary for all employees."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
    
    payroll_df = pd.read_sql_query("""
        SELECT 
            id,
            name,
            department,
            base_salary as gross_salary,
            tax_rate,
            deductions,
            (base_salary * (1 - tax_rate) - deductions) as net_pay
        FROM employees
    """, conn)
    
    conn.close()
    return payroll_df


def get_salary_by_department():
    """Get total salary cost by department."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
    
    salary_df = pd.read_sql_query("""
        SELECT 
            department,
            SUM(base_salary) as total_salary
        FROM employees
        GROUP BY department
    """, conn)
    
    conn.close()
    return salary_df


def add_investment(investor_name, investment_type, investment_date, amount, equity_percentage, status='Active'):
    """Add a new investment in the company to the database."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO company_investments (investor_name, investment_type, investment_date, amount, equity_percentage, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (investor_name, investment_type, investment_date, amount, equity_percentage, status))
    
    conn.commit()
    conn.close()


def get_investments():
    """Retrieve all investments in the company from the database."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        df = pd.read_sql_query("SELECT * FROM company_investments", conn)
        conn.close()
    return df


def update_investment(inv_id, investor_name, investment_type, investment_date, amount, equity_percentage, status):
    """Update an existing investment in the company."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE company_investments
        SET investor_name = ?, investment_type = ?, investment_date = ?, amount = ?, equity_percentage = ?, status = ?
        WHERE id = ?
    ''', (investor_name, investment_type, investment_date, amount, equity_percentage, status, inv_id))
    
    conn.commit()
    conn.close()


def delete_investment(inv_id):
    """Delete an investment in the company from the database."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM company_investments WHERE id = ?', (inv_id,))
        
        conn.commit()
        conn.close()


def get_investment_transactions():
    """Get all investment records from transactions table for backward compatibility."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
    
    invest_df = pd.read_sql_query("""
        SELECT 
            description as investor_name,
            category as investment_type,
            date as investment_date,
            amount,
            amount as current_value
        FROM transactions 
        WHERE type = 'Investment'
    """, conn)
    
    conn.close()
    return invest_df


def get_investment_summary():
    """Get investment summary data for dashboard."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
    
    # Calculate total investment value
    invest_df = pd.read_sql_query("""
        SELECT SUM(amount) as total_investment_value 
        FROM company_investments
    """, conn)
    
    total_investment = invest_df['total_investment_value'].iloc[0] if not invest_df.empty and invest_df['total_investment_value'].iloc[0] else 0
    
    conn.close()
    
    return {
        'total_investment_value': total_investment
    }


def add_loan(lender_name, loan_type, loan_date, principal_amount, interest_rate, monthly_payment, total_payments, remaining_payments, loan_direction='Inbound', status='Active'):
    """Add a new loan to the database."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO loans (lender_name, loan_type, loan_date, principal_amount, interest_rate, monthly_payment, total_payments, remaining_payments, loan_direction, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (lender_name, loan_type, loan_date, principal_amount, interest_rate, monthly_payment, total_payments, remaining_payments, loan_direction, status))
    
    conn.commit()
    conn.close()


def get_loans():
    """Retrieve all loans from the database."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        df = pd.read_sql_query("SELECT * FROM loans", conn)
        conn.close()
    return df


def update_loan(loan_id, lender_name, loan_type, loan_date, principal_amount, interest_rate, monthly_payment, total_payments, remaining_payments, loan_direction, status):
    """Update an existing loan."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE loans
        SET lender_name = ?, loan_type = ?, loan_date = ?, principal_amount = ?, interest_rate = ?, monthly_payment = ?, total_payments = ?, remaining_payments = ?, loan_direction = ?, status = ?
        WHERE id = ?
    ''', (lender_name, loan_type, loan_date, principal_amount, interest_rate, monthly_payment, total_payments, remaining_payments, loan_direction, status, loan_id))
    
    conn.commit()
    conn.close()


def delete_loan(loan_id):
    """Delete a loan from the database."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM loans WHERE id = ?', (loan_id,))
        
        conn.commit()
        conn.close()


def get_loan_summary():
    """Get loan summary data for dashboard."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
    
    # Calculate total loan amounts by direction
    loan_df = pd.read_sql_query("""
        SELECT 
            loan_direction,
            SUM(principal_amount) as total_loan_amount,
            SUM(monthly_payment * remaining_payments) as total_remaining_payments
        FROM loans
        GROUP BY loan_direction
    """, conn)
    
    # Initialize values
    total_inbound_loan = 0
    total_outbound_loan = 0
    total_remaining = 0
    
    # Calculate based on loan direction
    if not loan_df.empty:
        for _, row in loan_df.iterrows():
            if row['loan_direction'] == 'Inbound':
                total_inbound_loan = row['total_loan_amount']
            elif row['loan_direction'] == 'Outbound':
                total_outbound_loan = row['total_loan_amount']
        
        total_remaining = loan_df['total_remaining_payments'].sum()
    
    conn.close()
    
    return {
        'total_inbound_loan': total_inbound_loan,
        'total_outbound_loan': total_outbound_loan,
        'total_remaining_payments': total_remaining
    }


def check_budget_alerts():
    """Check if any budget categories have exceeded 90% of their budget."""
    with _db_lock:
        conn = sqlite3.connect('finance.db', timeout=10)
    
    alerts_df = pd.read_sql_query("""
        SELECT 
            category,
            monthly_budget,
            actual_spent,
            (actual_spent / monthly_budget * 100) as percentage_used
        FROM budgets
        WHERE actual_spent > monthly_budget * 0.9
    """, conn)
    
    conn.close()
    return alerts_df