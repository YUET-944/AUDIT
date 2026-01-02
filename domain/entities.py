"""
Domain entities for the financial dashboard
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Transaction:
    """Financial transaction entity"""
    id: Optional[int]
    date: str
    description: str
    category: str
    amount: float
    type: str  # Income, Expense, Salary, Investment, Loan
    currency_code: str = "PKR"
    base_currency_amount: Optional[float] = None
    exchange_rate: Optional[float] = None


@dataclass
class User:
    """User entity for authentication and authorization"""
    id: Optional[int]
    username: str
    email: str
    role: str  # admin, accountant, viewer
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


@dataclass
class Budget:
    """Budget entity"""
    id: Optional[int]
    category: str
    monthly_budget: float
    actual_spent: float = 0.0


@dataclass
class Employee:
    """Employee entity"""
    id: Optional[int]
    name: str
    department: str
    base_salary: float
    tax_rate: float
    deductions: float


@dataclass
class Investment:
    """Company investment entity"""
    id: Optional[int]
    investor_name: str
    investment_type: str
    investment_date: str
    amount: float
    equity_percentage: Optional[float] = None
    status: str = "Active"


@dataclass
class Loan:
    """Loan entity"""
    id: Optional[int]
    lender_name: str
    loan_type: str
    loan_date: str
    principal_amount: float
    interest_rate: float
    monthly_payment: float
    total_payments: int
    remaining_payments: int
    loan_direction: str  # Inbound (company receives), Outbound (company gives)
    status: str = "Active"