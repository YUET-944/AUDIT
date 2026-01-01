"""
Calculations module for the financial dashboard application.
Contains helper functions for financial calculations and data processing.
"""

import pandas as pd
import numpy as np


def calculate_net_pay(base_salary, tax_rate, deductions):
    """
    Calculate net pay for an employee.
    
    Args:
        base_salary (float): Employee's base salary
        tax_rate (float): Tax rate as a decimal (e.g., 0.2 for 20%)
        deductions (float): Fixed deductions amount
    
    Returns:
        float: Net pay after taxes and deductions
    """
    return base_salary * (1 - tax_rate) - deductions


def calculate_total_expenses(transactions_df):
    """
    Calculate total expenses from transactions dataframe.
    
    Args:
        transactions_df (pd.DataFrame): DataFrame containing transaction data
    
    Returns:
        float: Total expenses
    """
    expense_types = ['Expense', 'Salary']
    expenses_df = transactions_df[transactions_df['type'].isin(expense_types)]
    return expenses_df['amount'].sum() if not expenses_df.empty else 0


def calculate_total_income(transactions_df):
    """
    Calculate total income from transactions dataframe.
    
    Args:
        transactions_df (pd.DataFrame): DataFrame containing transaction data
    
    Returns:
        float: Total income
    """
    income_types = ['Income']
    income_df = transactions_df[transactions_df['type'].isin(income_types)]
    return income_df['amount'].sum() if not income_df.empty else 0


def calculate_net_profit(transactions_df):
    """
    Calculate net profit from transactions dataframe.
    
    Args:
        transactions_df (pd.DataFrame): DataFrame containing transaction data
    
    Returns:
        float: Net profit
    """
    total_income = calculate_total_income(transactions_df)
    total_expenses = calculate_total_expenses(transactions_df)
    return total_income - total_expenses


def calculate_cash_balance(transactions_df):
    """
    Calculate current cash balance from transactions dataframe.
    
    Args:
        transactions_df (pd.DataFrame): DataFrame containing transaction data
    
    Returns:
        float: Current cash balance
    """
    total_income = calculate_total_income(transactions_df)
    total_expenses = calculate_total_expenses(transactions_df)
    return total_income - total_expenses


def get_monthly_data(transactions_df, months=12):
    """
    Aggregate transactions data by month.
    
    Args:
        transactions_df (pd.DataFrame): DataFrame containing transaction data
        months (int): Number of months to include
    
    Returns:
        pd.DataFrame: Monthly aggregated data
    """
    # Convert date column to datetime
    transactions_df['date'] = pd.to_datetime(transactions_df['date'])
    
    # Filter for the last N months
    current_date = pd.Timestamp.now()
    start_date = current_date - pd.DateOffset(months=months)
    filtered_df = transactions_df[transactions_df['date'] >= start_date]
    
    # Group by month and type
    monthly_df = filtered_df.groupby([filtered_df['date'].dt.to_period('M'), 'type'])['amount'].sum().reset_index()
    monthly_df['date'] = monthly_df['date'].dt.to_timestamp()
    
    return monthly_df


def calculate_budget_variance(budgets_df):
    """
    Calculate variance between budgeted and actual amounts.
    
    Args:
        budgets_df (pd.DataFrame): DataFrame containing budget data
    
    Returns:
        pd.DataFrame: Budget data with variance calculations
    """
    budgets_df['variance'] = budgets_df['actual_spent'] - budgets_df['monthly_budget']
    budgets_df['variance_percentage'] = (budgets_df['variance'] / budgets_df['monthly_budget'] * 100).fillna(0)
    return budgets_df


def format_currency(amount):
    """
    Format a number as currency.
    
    Args:
        amount (float): Amount to format
    
    Returns:
        str: Formatted currency string
    """
    return f"PKR {amount:,.2f}"


def format_percentage(percentage):
    """
    Format a number as percentage.
    
    Args:
        percentage (float): Percentage to format
    
    Returns:
        str: Formatted percentage string
    """
    return f"{percentage:.1f}%"


def check_budget_alerts(budgets_df):
    """
    Check which budget categories have exceeded 90% of their budget.
    
    Args:
        budgets_df (pd.DataFrame): DataFrame containing budget data
    
    Returns:
        pd.DataFrame: Budget categories that have exceeded 90% of their budget
    """
    alerts_df = budgets_df[budgets_df['actual_spent'] > budgets_df['monthly_budget'] * 0.9]
    if not alerts_df.empty:
        alerts_df['percentage_used'] = (alerts_df['actual_spent'] / alerts_df['monthly_budget'] * 100)
    return alerts_df


def calculate_total_investments(investments_df):
    """
    Calculate total investment value from investments dataframe.
    
    Args:
        investments_df (pd.DataFrame): DataFrame containing investment data
    
    Returns:
        float: Total investment value
    """
    if investments_df.empty:
        return 0
    return investments_df['amount'].sum()  # Using amount for company investments


def calculate_total_loans(loans_df):
    """
    Calculate total loan amount from loans dataframe.
    
    Args:
        loans_df (pd.DataFrame): DataFrame containing loan data
    
    Returns:
        float: Total loan amount
    """
    if loans_df.empty:
        return 0
    return loans_df['principal_amount'].sum()
