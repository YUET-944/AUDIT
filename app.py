"""
Main Streamlit application for the financial dashboard.
This is the entry point for the financial dashboard application.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import sqlite3
import os
from fpdf import FPDF
import traceback
import logging
from contextlib import contextmanager

# Import our custom modules
from database import (
    init_db, add_transaction, get_transactions, update_transaction, delete_transaction,
    add_employee, get_employees, update_employee, delete_employee,
    add_budget, get_budgets, update_budget, delete_budget,
    add_investment, get_investments, update_investment, delete_investment,
    add_loan, get_loans, update_loan, delete_loan,
    get_investment_transactions,
    update_actual_spent, get_financial_summary, get_monthly_financial_data,
    get_expense_by_category, get_payroll_summary, get_salary_by_department,
    check_budget_alerts, get_transaction_count, search_transactions, get_transaction_count_filtered
)
from calculations import (
    calculate_net_pay, format_currency, format_percentage, calculate_budget_variance
)
from backup_restore import (
    create_database_backup, get_available_backups, restore_from_backup, delete_backup
)
from datetime import datetime


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the database
init_db()

# Set page configuration
st.set_page_config(
    page_title="Algo Hub Finance Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #0A2540;
        --secondary-color: #2ECC71;
        --accent-color: #E74C3C;
        --background-color: #F8F9FA;
        --card-bg: #FFFFFF;
        --text-dark: #0A2540;
        --text-light: #7f8c8d;
    }
    
    /* Header styling */
    h1, h2, h3, h4 {
        color: var(--primary-color);
        font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
    }
    
    /* Metric cards */
    .metric-card {
        background-color: var(--card-bg);
        padding: 20px;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border-bottom: 3px solid var(--primary-color);
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        margin: 12px 0;
        color: var(--primary-color);
    }
    
    .metric-label {
        font-size: 16px;
        color: var(--text-light);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .positive {
        color: var(--secondary-color);
    }
    
    .negative {
        color: var(--accent-color);
    }
    
    .warning {
        color: #f39c12;
        font-weight: 600;
    }
    
    /* Section headers */
    .section-header {
        border-bottom: 2px solid var(--primary-color);
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
        transition: background-color 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #081d33;
    }
    
    /* Danger button */
    .danger-button {
        background-color: var(--accent-color) !important;
    }
    
    .danger-button:hover {
        background-color: #c0392b !important;
    }
    
    /* Data frames */
    .stDataFrame {
        border-radius: 6px;
        overflow: hidden;
    }
    
    /* Sidebar */
    [data-testid=stSidebar] {
        background-color: var(--primary-color);
    }
    
    [data-testid=stSidebar] * {
        color: white;
    }
    
    /* Progress bars for budget alerts */
    .budget-progress {
        height: 10px;
        border-radius: 5px;
        margin-top: 8px;
    }
    
    /* Top navigation bar */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 24px;
        background-color: var(--primary-color);
        color: white;
        margin-bottom: 24px;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application function."""
    # Display company logo if it exists
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if os.path.exists("Algohub.png"):
            st.image("Algohub.png", width=150)
    
    with col2:
        st.title("💰 Algo Hub Finance Dashboard")
    
    with col3:
        # Date range picker
        date_range = st.selectbox(
            "Select Date Range",
            ["Today", "This Week", "This Month", "This Quarter", "This Year", "Custom"],
            key="date_range"
        )
    
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    
    # Display company logo in sidebar if it exists
    if os.path.exists("Algohub.png"):
        st.sidebar.image("Algohub.png", width=150)
    
    menu = st.sidebar.radio(
        "Go to",
        ["Dashboard", "Add Transaction", "Manage Employees", "Set Budgets", "Manage Investments", "Manage Loans", "View Reports"]
    )
    
    # Initialize session state for data editor
    if 'transactions_edited' not in st.session_state:
        st.session_state.transactions_edited = False
    if 'employees_edited' not in st.session_state:
        st.session_state.employees_edited = False
    if 'budgets_edited' not in st.session_state:
        st.session_state.budgets_edited = False
    
    # Initialize session state for editing transactions
    if 'editing_transaction' not in st.session_state:
        st.session_state.editing_transaction = None
    if 'editing_transaction_data' not in st.session_state:
        st.session_state.editing_transaction_data = None
    
    # Initialize loading states
    if 'loading' not in st.session_state:
        st.session_state.loading = False
    
    # Initialize search and filter states
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ''
    if 'date_filter_start' not in st.session_state:
        st.session_state.date_filter_start = None
    if 'date_filter_end' not in st.session_state:
        st.session_state.date_filter_end = None
    if 'category_filter' not in st.session_state:
        st.session_state.category_filter = 'All'
    if 'type_filter' not in st.session_state:
        st.session_state.type_filter = 'All'
    
    # Display budget alerts
    display_budget_alerts()
    
    # Route to selected page
    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Add Transaction":
        show_add_transaction()
    elif menu == "Manage Employees":
        show_manage_employees()
    elif menu == "Set Budgets":
        show_set_budgets()
    elif menu == "Manage Investments":
        show_manage_investments()
    elif menu == "Manage Loans":
        show_manage_loans()
    elif menu == "View Reports":
        show_reports()


def display_budget_alerts():
    """Display warnings for budget categories that have exceeded 90% of their budget."""
    alerts_df = check_budget_alerts()
    
    if not alerts_df.empty:
        st.sidebar.warning("⚠️ Budget Alerts")
        st.sidebar.markdown("---")
        for _, row in alerts_df.iterrows():
            percentage = (row['actual_spent'] / row['monthly_budget']) * 100
            # Display budget alert with progress bar
            st.sidebar.markdown(f"**{row['category']}**")
            st.sidebar.progress(min(percentage/100, 1.0))
            st.sidebar.markdown(f"{format_percentage(percentage)} of {format_currency(row['monthly_budget'])} used")
            st.sidebar.markdown("---")


def show_dashboard():
    """Display the main dashboard with financial overview and charts."""
    # Date range filter
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("📈 Financial Overview")
    with col2:
        date_range = st.selectbox(
            "Period",
            ["This Month", "Last Month", "This Quarter", "This Year"],
            key="dashboard_date_range"
        )
    
    st.markdown("---")
    
    # Get financial summary
    summary = get_financial_summary()
    
    # Display KPI cards in a horizontal row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Revenue</div>
            <div class="metric-value positive">{format_currency(summary['total_revenue'])}</div>
            <div style="color: #2ECC71;">↑ 12% vs last period</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Net Profit</div>
            <div class="metric-value {'positive' if summary['net_profit'] >= 0 else 'negative'}">
                {format_currency(summary['net_profit'])}
            </div>
            <div style="color: #2ECC71;">↑ 8% vs last period</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Operating Expenses</div>
            <div class="metric-value negative">{format_currency(summary['total_expenses'])}</div>
            <div style="color: #E74C3C;">↑ 5% vs last period</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Cash Balance</div>
            <div class="metric-value {'positive' if summary['cash_balance'] >= 0 else 'negative'}">
                {format_currency(summary['cash_balance'])}
            </div>
            <div style="color: #2ECC71;">↑ 3% vs last period</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Outstanding Receivables</div>
            <div class="metric-value positive">PKR 0.00</div>
            <div style="color: #2ECC71;">↓ 100% vs last period</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Two-column layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Monthly Net Profit/Loss chart
        st.subheader("📊 Monthly Net Profit/Loss")
        monthly_data = get_monthly_financial_data(12)
        
        if not monthly_data.empty:
            # Calculate net profit/loss for each month
            monthly_data['net_profit'] = monthly_data['income'] - monthly_data['expenses']
            
            fig = go.Figure()
            colors = ['#2ECC71' if x >= 0 else '#E74C3C' for x in monthly_data['net_profit']]
            fig.add_trace(go.Bar(
                x=monthly_data['month'], 
                y=monthly_data['net_profit'],
                marker_color=colors,
                text=[format_currency(x) for x in monthly_data['net_profit']],
                textposition='outside'
            ))
            fig.update_layout(
                title="Monthly Net Profit/Loss", 
                xaxis_title="Month", 
                yaxis_title="Amount (PKR)",
                showlegend=False
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No data available for the net profit/loss chart.")
        
        # Cash Flow Timeline
        st.subheader("💳 Cash Flow Timeline")
        if not monthly_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=monthly_data['month'], 
                y=monthly_data['income'],
                mode='lines+markers', 
                name='Cash In', 
                line=dict(color='#2ECC71', width=3)
            ))
            fig.add_trace(go.Scatter(
                x=monthly_data['month'], 
                y=monthly_data['expenses'],
                mode='lines+markers', 
                name='Cash Out', 
                line=dict(color='#E74C3C', width=3)
            ))
            fig.update_layout(
                title="Cash Flow Timeline", 
                xaxis_title="Month", 
                yaxis_title="Amount (PKR)"
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No data available for the cash flow chart.")
    
    with col2:
        # Budget vs Actual
        st.subheader("💰 Budget vs Actual")
        budgets_df = get_budgets()
        
        if not budgets_df.empty:
            budgets_df = calculate_budget_variance(budgets_df)
            # Create a donut chart
            fig = go.Figure(data=[go.Pie(
                labels=budgets_df['category'], 
                values=budgets_df['monthly_budget'],
                hole=.3,
                textinfo='label+percent'
            )])
            fig.update_layout(title="Budget Allocation by Department")
            st.plotly_chart(fig, width='stretch')
            
            # Show budget usage
            st.write("Budget Usage:")
            for _, row in budgets_df.iterrows():
                usage_percent = (row['actual_spent'] / row['monthly_budget']) * 100 if row['monthly_budget'] > 0 else 0
                st.progress(min(usage_percent/100, 1.0))
                st.write(f"{row['category']}: {format_currency(row['actual_spent'])} / {format_currency(row['monthly_budget'])} ({usage_percent:.1f}%)")
        else:
            st.info("No budget data available.")
        
        # Top 5 Expense Categories
        st.subheader("🛒 Top 5 Expense Categories")
        expense_data = get_expense_by_category()
        
        if not expense_data.empty:
            # Sort by expense amount and take top 5
            expense_data = expense_data.sort_values('total_expense', ascending=False).head(5)
            
            fig = go.Figure(go.Bar(
                x=expense_data['total_expense'],
                y=expense_data['category'],
                orientation='h',
                marker_color='#3498db',
                text=[format_currency(x) for x in expense_data['total_expense']],
                textposition='auto'
            ))
            fig.update_layout(
                title="Top Expense Categories",
                xaxis_title="Amount (PKR)",
                yaxis_title="Category",
                yaxis={'categoryorder':'total ascending'}
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No expense data available.")
        
        # Recent Alerts
        st.subheader("⚠️ Recent Alerts")
        alerts_df = check_budget_alerts()
        
        if not alerts_df.empty:
            for _, row in alerts_df.head(3).iterrows():
                percentage = (row['actual_spent'] / row['monthly_budget']) * 100
                st.warning(f"⚠️ {row['category']} expense {percentage:.1f}% of budget used")
        else:
            st.info("No active alerts.")
        
        # Sample alerts for demonstration
        st.info("💡 Client XYZ payment received: PKR 12,400 (Today)")
        st.info("📅 Vendor invoice due in 2 days: PKR 4,200")

    # Payroll Management Section
    st.header("👥 Payroll Management")
    st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)
    
    # Employee payroll summary
    st.subheader("📝 Employee Payroll Summary")
    payroll_df = get_payroll_summary()
    
    if not payroll_df.empty:
        st.dataframe(payroll_df.style.format({
            'gross_salary': 'PKR {:,.2f}',
            'tax_rate': '{:.2%}',
            'deductions': 'PKR {:,.2f}',
            'net_pay': 'PKR {:,.2f}'
        }))
        
        # Export payroll data
        csv = convert_df_to_csv(payroll_df)
        st.download_button(
            label="📥 Download Payroll Data as CSV",
            data=csv,
            file_name='payroll_summary.csv',
            mime='text/csv'
        )
    else:
        st.info("No employee data available.")
    
    # Salary cost by department
    st.subheader("🏢 Salary Cost by Department")
    salary_dept_df = get_salary_by_department()
    
    if not salary_dept_df.empty:
        fig = px.pie(salary_dept_df, values='total_salary', names='department',
                    title="Total Salary Cost by Department", hole=0.3)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No salary data available.")
    
    # Investment & Assets Section
    st.header("💼 Company Investments")
    st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)
    
    # Investments table
    st.subheader("📊 Investment Portfolio")
    investments_df = get_investments()
    
    if not investments_df.empty:
        # Display investments with delete option
        for index, row in investments_df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 1])
            col1.write(row['investor_name'])
            col2.write(row['investment_type'])
            col3.write(str(row['investment_date']))
            col4.write(format_currency(row['amount']))
            col5.write(f"{row['equity_percentage']:.2f}%" if not pd.isna(row['equity_percentage']) else "N/A")
            
            # Delete button for each investment
            if col6.button("🗑️", key=f"del_inv_{row['id']}"):
                delete_investment(row['id'])
                st.success(f"Investment by '{row['investor_name']}' deleted successfully!")
                st.rerun()
        
        # Export investments data
        csv = convert_df_to_csv(investments_df)
        st.download_button(
            label="📥 Download Investment Data as CSV",
            data=csv,
            file_name='company_investments.csv',
            mime='text/csv'
        )
    else:
        st.info("No investment data available.")
    
    # Investment growth chart
    st.subheader("📈 Investment Growth Over Time")
    # For simplicity, we'll show a static chart here
    # In a real application, you would track investment value changes over time
    st.info("Investment growth tracking would be implemented with more detailed data.")
    
    # Loans Section
    st.header("💳 Company Loans")
    st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)
    
    # Loans table
    st.subheader("📋 Loan Portfolio")
    loans_df = get_loans()
    
    if not loans_df.empty:
        # Display loans with edit and delete options
        for index, row in loans_df.iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 1, 2, 2, 2, 1])
            col1.write(row['lender_name'])
            col2.write(row['loan_direction'])
            col3.write(row['loan_type'])
            col4.write(format_currency(row['principal_amount']))
            col5.write(f"{row['interest_rate']*100:.2f}%")
            col6.write(row['status'])
            
            # Delete button for each loan
            if col7.button("🗑️", key=f"del_loan_{row['id']}"):
                delete_loan(row['id'])
                st.success(f"Loan from '{row['lender_name']}' deleted successfully!")
                st.rerun()
        
        # Export loans data
        csv = convert_df_to_csv(loans_df)
        st.download_button(
            label="📥 Download Loan Data as CSV",
            data=csv,
            file_name='company_loans.csv',
            mime='text/csv'
        )
    else:
        st.info("No loan data available.")


def show_add_transaction():
    """Display the form to add a new transaction."""
    st.header("💸 Add New Transaction")
    st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)
    
    # Validation function
    def validate_transaction(date, description, category, amount, trans_type):
        errors = []
        if not description or description.strip() == "":
            errors.append("Description is required")
        if not category or category.strip() == "":
            errors.append("Category is required")
        if amount <= 0:
            errors.append("Amount must be greater than 0")
        if not date:
            errors.append("Date is required")
        return errors
    
    # Quick-add common transactions
    st.subheader("Quick Add Common Transactions")
    
    # Client Payment section
    with st.expander("💳 Add Client Payment", expanded=True):
        client_col1, client_col2 = st.columns(2)
        with client_col1:
            client_payment_date = st.date_input("Date", datetime.now(), key="client_payment_date")
            client_payment_amount = st.number_input("Amount", min_value=0.0, format="%.2f", key="client_payment_amount")
        with client_col2:
            client_name = st.text_input("Client Name", key="client_name")
            project_name = st.text_input("Project Name", key="project_name")
        
        if st.button("Add Client Payment") and client_payment_amount > 0 and client_name:
            description = f"Payment received from {client_name} for {project_name if project_name else 'services'}"
            add_transaction(client_payment_date, description, "Income", client_payment_amount, "Income")
            st.success(f"Client payment of {format_currency(client_payment_amount)} from {client_name} added successfully!")
            st.rerun()
    
    # Vendor Payment section
    with st.expander("🛒 Add Vendor Payment", expanded=True):
        vendor_col1, vendor_col2 = st.columns(2)
        with vendor_col1:
            vendor_payment_date = st.date_input("Date", datetime.now(), key="vendor_payment_date")
            vendor_payment_amount = st.number_input("Amount", min_value=0.0, format="%.2f", key="vendor_payment_amount")
        with vendor_col2:
            vendor_name = st.text_input("Vendor Name", key="vendor_name")
            expense_category = st.text_input("Expense Category", key="expense_category")
        
        if st.button("Add Vendor Payment") and vendor_payment_amount > 0 and vendor_name:
            description = f"Payment to {vendor_name} for {expense_category if expense_category else 'services'}"
            add_transaction(vendor_payment_date, description, expense_category if expense_category else "Expense", vendor_payment_amount, "Expense")
            st.success(f"Vendor payment of {format_currency(vendor_payment_amount)} to {vendor_name} added successfully!")
            st.rerun()
    
    # Loan Received section
    with st.expander("💰 Add Loan Received", expanded=True):
        loan_col1, loan_col2 = st.columns(2)
        with loan_col1:
            loan_received_date = st.date_input("Date", datetime.now(), key="loan_received_date")
            loan_received_amount = st.number_input("Amount", min_value=0.0, format="%.2f", key="loan_received_amount")
        with loan_col2:
            lender_name = st.text_input("Lender Name", key="lender_name")
            loan_type = st.selectbox("Loan Type", ["Personal", "Business", "Mortgage", "Equipment", "Vehicle", "Other"], key="loan_type")
        
        if st.button("Add Loan Received") and loan_received_amount > 0 and lender_name:
            description = f"Loan received from {lender_name} ({loan_type})"
            add_transaction(loan_received_date, description, loan_type, loan_received_amount, "Income")
            st.success(f"Loan of {format_currency(loan_received_amount)} from {lender_name} added successfully!")
            st.rerun()
    
    # Transaction form
    st.subheader("Manual Transaction Entry")
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", datetime.now())
            description = st.text_input("Description")
            category = st.text_input("Category")
            
        with col2:
            amount = st.number_input("Amount", min_value=0.0, format="%.2f")
            trans_type = st.selectbox("Type", ["Income", "Expense", "Salary", "Investment", "Loan"])
        
        submitted = st.form_submit_button("Add Transaction")
        
        if submitted:
            try:
                validation_errors = validate_transaction(date, description, category, amount, trans_type)
                if validation_errors:
                    for error in validation_errors:
                        st.error(error)
                else:
                    add_transaction(date, description, category, amount, trans_type)
                    st.success("Transaction added successfully!")
                    st.rerun()
            except Exception as e:
                logger.error(f"Error adding transaction: {str(e)}\n{traceback.format_exc()}")
                st.error(f"Failed to add transaction: {str(e)}")

    # Display existing transactions with edit and delete options
    st.subheader("📋 Existing Transactions")
    
    # Check if we're editing a transaction
    if st.session_state.editing_transaction:
        # Get the transaction to edit
        edit_row = st.session_state.editing_transaction_data
        
        st.subheader(f"Editing Transaction #{edit_row['id']}")
        with st.form("edit_transaction_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                edit_date = st.date_input("Date", value=pd.to_datetime(edit_row['date']).date())
                edit_description = st.text_input("Description", value=edit_row['description'])
                edit_category = st.text_input("Category", value=edit_row['category'])
                
            with col2:
                edit_amount = st.number_input("Amount", value=float(edit_row['amount']), format="%.2f")
                edit_type = st.selectbox("Type", ["Income", "Expense", "Salary", "Investment", "Loan"], index=["Income", "Expense", "Salary", "Investment", "Loan"].index(edit_row['type']))
            
            submitted = st.form_submit_button("Update Transaction")
            
            if submitted:
                update_transaction(edit_row['id'], edit_date, edit_description, edit_category, edit_amount, edit_type)
                st.success("Transaction updated successfully!")
                # Reset editing state
                st.session_state.editing_transaction = None
                st.session_state.editing_transaction_data = None
                st.rerun()
            
            if st.form_submit_button("Cancel", type="secondary"):
                # Reset editing state
                st.session_state.editing_transaction = None
                st.session_state.editing_transaction_data = None
                st.rerun()
    
    # Initialize pagination in session state if not already set
    if 'transaction_page' not in st.session_state:
        st.session_state.transaction_page = 1
    
    # Add search and filter controls
    st.subheader("🔍 Search & Filter Transactions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.session_state.search_query = st.text_input("Search Description/Category", value=st.session_state.search_query)
    with col2:
        st.session_state.date_filter_start = st.date_input("Start Date", value=st.session_state.date_filter_start)
    with col3:
        st.session_state.date_filter_end = st.date_input("End Date", value=st.session_state.date_filter_end)
    with col4:
        # Get all available categories
        all_transactions = get_transactions()  # Get all for category options
        categories = ['All'] + sorted(all_transactions['category'].unique().tolist()) if not all_transactions.empty else ['All']
        st.session_state.category_filter = st.selectbox("Category", options=categories, index=categories.index(st.session_state.category_filter) if st.session_state.category_filter in categories else 0)
        
        # Get all available types
        types = ['All'] + sorted(all_transactions['type'].unique().tolist()) if not all_transactions.empty else ['All']
        st.session_state.type_filter = st.selectbox("Type", options=types, index=types.index(st.session_state.type_filter) if st.session_state.type_filter in types else 0)
    
    # Refresh transactions dataframe after potential edit/deletion
    page_size = 20  # Show 20 transactions per page
    
    # Apply search and filters
    transactions_df = search_transactions(
        query=st.session_state.search_query if st.session_state.search_query else None,
        start_date=st.session_state.date_filter_start,
        end_date=st.session_state.date_filter_end,
        category=st.session_state.category_filter if st.session_state.category_filter != 'All' else None,
        trans_type=st.session_state.type_filter if st.session_state.type_filter != 'All' else None,
        page=st.session_state.transaction_page,
        page_size=page_size
    )
    
    # Get total count for pagination
    total_transactions = get_transaction_count_filtered(
        query=st.session_state.search_query if st.session_state.search_query else None,
        start_date=st.session_state.date_filter_start,
        end_date=st.session_state.date_filter_end,
        category=st.session_state.category_filter if st.session_state.category_filter != 'All' else None,
        trans_type=st.session_state.type_filter if st.session_state.type_filter != 'All' else None
    )
    total_pages = (total_transactions + page_size - 1) // page_size  # Ceiling division
    
    if not transactions_df.empty:
        # Display transactions with edit and delete buttons
        st.subheader(f"All Transactions (Page {st.session_state.transaction_page} of {total_pages})")
        for index, row in transactions_df.iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 2, 1, 2, 1, 1])
            col1.write(str(row['date']))
            col2.write(row['description'])
            col3.write(row['category'])
            col4.write(format_currency(row['amount']))
            col5.write(row['type'])
            
            # Edit button
            with col6:
                if st.button(f"✏️", key=f"edit_trans_{row['id']}"):
                    st.session_state.editing_transaction = row['id']
                    st.session_state.editing_transaction_data = row
                    st.rerun()
            
            # Delete button for each transaction
            with col7:
                if st.button("🗑️", key=f"del_trans_{row['id']}"):
                    delete_transaction(row['id'])
                    st.success(f"Transaction '{row['description']}' deleted successfully!")
                    st.rerun()
        
        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("◀️ Previous", disabled=(st.session_state.transaction_page <= 1)):
                st.session_state.transaction_page -= 1
                st.rerun()
        with col2:
            st.write(f"Page {st.session_state.transaction_page} of {total_pages}")
        with col3:
            if st.button("Next ▶️", disabled=(st.session_state.transaction_page >= total_pages)):
                st.session_state.transaction_page += 1
                st.rerun()
        
        # Export transactions data
        csv = convert_df_to_csv(transactions_df)
        st.download_button(
            label="📥 Download Transactions Data as CSV",
            data=csv,
            file_name='transactions.csv',
            mime='text/csv'
        )
    else:
        st.info("No transactions found. Add transactions using the form above.")


def show_manage_employees():
    """Display the employee management interface."""
    st.header("👥 Manage Employees")
    st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)
    
    # Add new employee form
    st.subheader("➕ Add New Employee")
    with st.form("employee_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name")
            department = st.text_input("Department")
            base_salary = st.number_input("Base Salary", min_value=0.0, format="%.2f")
            
        with col2:
            tax_rate = st.number_input("Tax Rate (decimal)", min_value=0.0, max_value=1.0, format="%.3f", 
                                     help="Enter as decimal (e.g., 0.2 for 20%)")
            deductions = st.number_input("Deductions", min_value=0.0, format="%.2f")
        
        submitted = st.form_submit_button("Add Employee")
        
        if submitted:
            try:
                if name and department and base_salary > 0:
                    add_employee(name, department, base_salary, tax_rate, deductions)
                    st.success("Employee added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all fields with valid values.")
            except Exception as e:
                logger.error(f"Error adding employee: {str(e)}\n{traceback.format_exc()}")
                st.error(f"Failed to add employee: {str(e)}")
    
    # Display and edit employees
    st.subheader("📋 Employee Records")
    employees_df = get_employees()
    
    if not employees_df.empty:
        # Make the dataframe editable
        edited_employees = st.data_editor(
            employees_df,
            width='stretch',
            num_rows="dynamic",
            column_config={
                "id": st.column_config.NumberColumn(disabled=True),
                "name": st.column_config.TextColumn("Name"),
                "department": st.column_config.TextColumn("Department"),
                "base_salary": st.column_config.NumberColumn("Base Salary", format="PKR %.2f"),
                "tax_rate": st.column_config.NumberColumn("Tax Rate", format="%.3f"),
                "deductions": st.column_config.NumberColumn("Deductions", format="PKR %.2f")
            }
        )
        
        # Save changes button
        if st.button("💾 Save Changes") and not employees_df.equals(edited_employees):
            # Handle additions, updates, and deletions
            for index, row in edited_employees.iterrows():
                if pd.isna(row['id']):  # New employee
                    add_employee(row['name'], row['department'], row['base_salary'], 
                               row['tax_rate'], row['deductions'])
                else:  # Existing employee
                    update_employee(row['id'], row['name'], row['department'], 
                                  row['base_salary'], row['tax_rate'], row['deductions'])
            
            # Handle deletions (employees in original but not in edited)
            deleted_employees = employees_df[~employees_df['id'].isin(edited_employees['id'])]
            for _, row in deleted_employees.iterrows():
                delete_employee(row['id'])
            
            st.success("Employee records updated successfully!")
            st.rerun()
        
        # Export employees data
        csv = convert_df_to_csv(employees_df)
        st.download_button(
            label="📥 Download Employee Data as CSV",
            data=csv,
            file_name='employees.csv',
            mime='text/csv'
        )
    else:
        st.info("No employees found. Add employees using the form above.")


def show_set_budgets():
    """Display the budget management interface."""
    st.header("💰 Set Budgets")
    st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)
    
    # Add new budget form
    st.subheader("➕ Add New Budget Category")
    with st.form("budget_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.text_input("Category")
            
        with col2:
            monthly_budget = st.number_input("Monthly Budget", min_value=0.0, format="%.2f")
        
        submitted = st.form_submit_button("Add Budget")
        
        if submitted:
            try:
                if category and monthly_budget > 0:
                    add_budget(category, monthly_budget)
                    st.success("Budget category added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all fields with valid values.")
            except Exception as e:
                logger.error(f"Error adding budget: {str(e)}\n{traceback.format_exc()}")
                st.error(f"Failed to add budget: {str(e)}")
    
    # Display and edit budgets
    st.subheader("📋 Budget Categories")
    budgets_df = get_budgets()
    
    if not budgets_df.empty:
        # Calculate variance for display
        budgets_df = calculate_budget_variance(budgets_df)
        
        # Make the dataframe editable
        edited_budgets = st.data_editor(
            budgets_df,
            width='stretch',
            num_rows="dynamic",
            column_config={
                "id": st.column_config.NumberColumn(disabled=True),
                "category": st.column_config.TextColumn("Category"),
                "monthly_budget": st.column_config.NumberColumn("Monthly Budget", format="PKR %.2f"),
                "actual_spent": st.column_config.NumberColumn("Actual Spent", format="PKR %.2f", disabled=True),
                "variance": st.column_config.NumberColumn("Variance", format="PKR %.2f", disabled=True),
                "variance_percentage": st.column_config.NumberColumn("Variance %", format="%.1f%%", disabled=True)
            }
        )
        
        # Save changes button
        if st.button("💾 Save Changes") and not budgets_df[['id', 'category', 'monthly_budget']].equals(
                edited_budgets[['id', 'category', 'monthly_budget']]):
            # Handle additions, updates, and deletions
            for index, row in edited_budgets.iterrows():
                if pd.isna(row['id']):  # New budget
                    add_budget(row['category'], row['monthly_budget'])
                else:  # Existing budget
                    update_budget(row['id'], row['category'], row['monthly_budget'])
            
            # Handle deletions (budgets in original but not in edited)
            deleted_budgets = budgets_df[~budgets_df['id'].isin(edited_budgets['id'])]
            for _, row in deleted_budgets.iterrows():
                delete_budget(row['id'])
            
            st.success("Budget records updated successfully!")
            st.rerun()
        
        # Export budgets data
        csv = convert_df_to_csv(budgets_df)
        st.download_button(
            label="📥 Download Budget Data as CSV",
            data=csv,
            file_name='budgets.csv',
            mime='text/csv'
        )
    else:
        st.info("No budget categories found. Add budget categories using the form above.")


def show_reports():
    """Display the reports section."""
    st.header("📈 Reports & Exports")
    st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)
    
    st.info("📊 Generate comprehensive financial reports and export data in various formats.")
    
    # Export all data
    st.subheader("📤 Export All Data")
    
    # Export transactions
    transactions_df = get_transactions()
    if not transactions_df.empty:
        csv = convert_df_to_csv(transactions_df)
        st.download_button(
            label="💼 Download Transactions Data as CSV",
            data=csv,
            file_name='transactions.csv',
            mime='text/csv'
        )
    
    # Export employees
    employees_df = get_employees()
    if not employees_df.empty:
        csv = convert_df_to_csv(employees_df)
        st.download_button(
            label="👥 Download Employees Data as CSV",
            data=csv,
            file_name='employees.csv',
            mime='text/csv'
        )
    
    # Export budgets
    budgets_df = get_budgets()
    if not budgets_df.empty:
        csv = convert_df_to_csv(budgets_df)
        st.download_button(
            label="💰 Download Budgets Data as CSV",
            data=csv,
            file_name='budgets.csv',
            mime='text/csv'
        )
    
    # Export investments
    investments_df = get_investments()
    if not investments_df.empty:
        csv = convert_df_to_csv(investments_df)
        st.download_button(
            label="💼 Download Investments Data as CSV",
            data=csv,
            file_name='investments.csv',
            mime='text/csv'
        )
    
    # Export loans
    loans_df = get_loans()
    if not loans_df.empty:
        csv = convert_df_to_csv(loans_df)
        st.download_button(
            label="💳 Download Loans Data as CSV",
            data=csv,
            file_name='loans.csv',
            mime='text/csv'
        )
    
    st.subheader("📄 Generate PDF Report")
    if st.button("🖨️ Generate PDF Report"):
        try:
            with st.spinner('Generating PDF report...'):
                # Generate PDF report
                pdf = generate_pdf_report()
            st.success("PDF report generated successfully!")
            
            # Provide download button for the PDF
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf,
                file_name='financial_report.pdf',
                mime='application/pdf'
            )
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}\n{traceback.format_exc()}")
            st.error(f"Failed to generate PDF report: {str(e)}")
    
    # Database backup and restore section
    st.subheader("💾 Database Backup & Restore")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Create Database Backup"):
            try:
                with st.spinner('Creating backup...'):
                    backup_path = create_database_backup()
                st.success(f"Backup created successfully: {os.path.basename(backup_path)}")
            except Exception as e:
                logger.error(f"Error creating backup: {str(e)}\n{traceback.format_exc()}")
                st.error(f"Failed to create backup: {str(e)}")
    
    with col2:
        # Show available backups
        try:
            backups = get_available_backups()
            if backups:
                selected_backup = st.selectbox("Select Backup to Restore", 
                                              options=[b['name'] for b in backups],
                                              format_func=lambda x: f"{x} ({datetime.fromisoformat(backups[0]['created']).strftime('%Y-%m-%d %H:%M:%S') if backups else ''})")
                
                if st.button("Restore Selected Backup", type="secondary"):
                    try:
                        with st.spinner('Restoring backup... This will overwrite current data!'):
                            success = restore_from_backup(selected_backup)
                        if success:
                            st.success(f"Database restored successfully from: {selected_backup}")
                            st.rerun()
                    except Exception as e:
                        logger.error(f"Error restoring backup: {str(e)}\n{traceback.format_exc()}")
                        st.error(f"Failed to restore backup: {str(e)}")
            else:
                st.info("No backups available")
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}\n{traceback.format_exc()}")
            st.error(f"Failed to list backups: {str(e)}")


def generate_pdf_report():
    """Generate a comprehensive financial PDF report."""
    # Create PDF instance
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Algo Hub Financial Report', 0, 1, 'C')
    
    # Add date
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Report Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
    pdf.ln(10)
    
    # Financial Summary
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Financial Summary', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    # Get financial summary
    summary = get_financial_summary()
    
    pdf.cell(0, 8, f'Total Revenue: {format_currency(summary["total_revenue"])}', 0, 1)
    pdf.cell(0, 8, f'Total Expenses: {format_currency(summary["total_expenses"])}', 0, 1)
    pdf.cell(0, 8, f'Net Profit: {format_currency(summary["net_profit"])}', 0, 1)
    pdf.cell(0, 8, f'Cash Balance: {format_currency(summary["cash_balance"])}', 0, 1)
    pdf.ln(10)
    
    # Transactions
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'All Transactions', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    transactions_df = get_transactions()
    if not transactions_df.empty:
        for _, row in transactions_df.iterrows():
            pdf.cell(0, 8, f'{row["date"]} - {row["description"]}: {format_currency(row["amount"])} ({row["type"]})', 0, 1)
    else:
        pdf.cell(0, 8, 'No transactions found', 0, 1)
    pdf.ln(10)
    
    # Investments
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Investments', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    investments_df = get_investments()
    if not investments_df.empty:
        for _, row in investments_df.iterrows():
            pdf.cell(0, 8, f'{row["investor_name"]}: {format_currency(row["amount"])} - {row["investment_type"]}', 0, 1)
    else:
        pdf.cell(0, 8, 'No investments found', 0, 1)
    pdf.ln(10)
    
    # Loans
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Loans', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    loans_df = get_loans()
    if not loans_df.empty:
        for _, row in loans_df.iterrows():
            pdf.cell(0, 8, f'{row["lender_name"]}: {format_currency(row["principal_amount"])} - {row["loan_direction"]} Loan', 0, 1)
    else:
        pdf.cell(0, 8, 'No loans found', 0, 1)
    pdf.ln(10)
    
    # Employees
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Employees', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    employees_df = get_employees()
    if not employees_df.empty:
        for _, row in employees_df.iterrows():
            pdf.cell(0, 8, f'{row["name"]} - {row["department"]}: {format_currency(row["base_salary"])}', 0, 1)
    else:
        pdf.cell(0, 8, 'No employees found', 0, 1)
    
    # Return PDF as bytes in a format that Streamlit can handle
    pdf_string = pdf.output(dest='S')
    # Convert to bytes
    if isinstance(pdf_string, str):
        pdf_bytes = pdf_string.encode('latin-1')
    elif isinstance(pdf_string, bytearray):
        pdf_bytes = bytes(pdf_string)
    else:
        pdf_bytes = pdf_string
    return pdf_bytes


def convert_df_to_csv(df):
    """Convert a dataframe to CSV format."""
    return df.to_csv(index=False).encode('utf-8')


def show_manage_investments():
    """Display the investment management interface."""
    st.header("💼 Manage Company Investments")
    st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)
    
    # Add new investment form
    st.subheader("➕ Add New Investment")
    with st.form("investment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            investor_name = st.text_input("Investor Name")
            investment_type = st.selectbox("Investment Type", ["Equity", "Debt", "Convertible", "Other"])
            investment_date = st.date_input("Investment Date", datetime.now())
            amount = st.number_input("Investment Amount", min_value=0.0, format="%.2f")
            
        with col2:
            equity_percentage = st.number_input("Equity Percentage (%)", min_value=0.0, max_value=100.0, format="%.2f")
            status = st.selectbox("Status", ["Active", "Completed", "Cancelled"])
        
        submitted = st.form_submit_button("Add Investment")
        
        if submitted:
            try:
                if investor_name and amount > 0:
                    add_investment(investor_name, investment_type, investment_date, amount, equity_percentage, status)
                    st.success("Investment added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all fields with valid values.")
            except Exception as e:
                logger.error(f"Error adding investment: {str(e)}\n{traceback.format_exc()}")
                st.error(f"Failed to add investment: {str(e)}")
    
    # Display and edit investments
    st.subheader("📋 Investment Records")
    investments_df = get_investments()
    
    if not investments_df.empty:
        # Make the dataframe editable
        edited_investments = st.data_editor(
            investments_df,
            width='stretch',
            num_rows="dynamic",
            column_config={
                "id": st.column_config.NumberColumn(disabled=True),
                "investor_name": st.column_config.TextColumn("Investor Name"),
                "investment_type": st.column_config.TextColumn("Investment Type"),
                "investment_date": st.column_config.TextColumn("Investment Date"),
                "amount": st.column_config.NumberColumn("Investment Amount", format="PKR %.2f"),
                "equity_percentage": st.column_config.NumberColumn("Equity %", format="%.2f"),
                "status": st.column_config.SelectboxColumn("Status", options=["Active", "Completed", "Cancelled"])
            }
        )
        
        # Save changes button
        if st.button("💾 Save Changes") and not investments_df.equals(edited_investments):
            # Handle additions, updates, and deletions
            for index, row in edited_investments.iterrows():
                if pd.isna(row['id']):  # New investment
                    add_investment(row['investor_name'], row['investment_type'], row['investment_date'], 
                                 row['amount'], row['equity_percentage'], row['status'])
                else:  # Existing investment
                    update_investment(row['id'], row['investor_name'], row['investment_type'], row['investment_date'], 
                                   row['amount'], row['equity_percentage'], row['status'])
            
            # Handle deletions (investments in original but not in edited)
            deleted_investments = investments_df[~investments_df['id'].isin(edited_investments['id'])]
            for _, row in deleted_investments.iterrows():
                delete_investment(row['id'])
            
            st.success("Investment records updated successfully!")
            st.rerun()
        
        # Export investments data
        csv = convert_df_to_csv(investments_df)
        st.download_button(
            label="📥 Download Investment Data as CSV",
            data=csv,
            file_name='company_investments.csv',
            mime='text/csv'
        )
    else:
        st.info("No investments found. Add investments using the form above.")


def show_manage_loans():
    """Display the loan management interface."""
    st.header("💳 Manage Loans")
    st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)
    
    # Add new loan form
    st.subheader("➕ Add New Loan")
    with st.form("loan_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            lender_name = st.text_input("Lender/Borrower Name")
            loan_direction = st.selectbox("Loan Direction", ["Inbound", "Outbound"], help="Inbound: Company receives loan from lender. Outbound: Company gives loan to borrower")
            loan_type = st.selectbox("Loan Type", ["Personal", "Business", "Mortgage", "Equipment", "Vehicle", "Other"])
            loan_date = st.date_input("Loan Date", datetime.now())
            principal_amount = st.number_input("Principal Amount", min_value=0.0, format="%.2f")
            
        with col2:
            interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=100.0, format="%.2f")
            monthly_payment = st.number_input("Monthly Payment", min_value=0.0, format="%.2f")
            total_payments = st.number_input("Total Payments", min_value=1, format="%d")
            remaining_payments = st.number_input("Remaining Payments", min_value=0, format="%d")
            status = st.selectbox("Status", ["Active", "Paid Off", "Defaulted"])
        
        submitted = st.form_submit_button("Add Loan")
        
        if submitted:
            try:
                if lender_name and principal_amount > 0 and monthly_payment > 0 and total_payments > 0:
                    add_loan(lender_name, loan_type, loan_date, principal_amount, interest_rate/100, monthly_payment, total_payments, remaining_payments, loan_direction, status)
                    st.success("Loan added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all fields with valid values.")
            except Exception as e:
                logger.error(f"Error adding loan: {str(e)}\n{traceback.format_exc()}")
                st.error(f"Failed to add loan: {str(e)}")
    
    # Display and edit loans
    st.subheader("📋 Loan Records")
    loans_df = get_loans()
    
    if not loans_df.empty:
        # Make the dataframe editable
        edited_loans = st.data_editor(
            loans_df,
            width='stretch',
            num_rows="dynamic",
            column_config={
                "id": st.column_config.NumberColumn(disabled=True),
                "lender_name": st.column_config.TextColumn("Lender/Borrower Name"),
                "loan_direction": st.column_config.SelectboxColumn("Loan Direction", options=["Inbound", "Outbound"]),
                "loan_type": st.column_config.TextColumn("Loan Type"),
                "loan_date": st.column_config.TextColumn("Loan Date"),
                "principal_amount": st.column_config.NumberColumn("Principal Amount", format="PKR %.2f"),
                "interest_rate": st.column_config.NumberColumn("Interest Rate (%)", format="%.2f"),
                "monthly_payment": st.column_config.NumberColumn("Monthly Payment", format="PKR %.2f"),
                "total_payments": st.column_config.NumberColumn("Total Payments", format="%d"),
                "remaining_payments": st.column_config.NumberColumn("Remaining Payments", format="%d"),
                "status": st.column_config.SelectboxColumn("Status", options=["Active", "Paid Off", "Defaulted"])
            }
        )
        
        # Save changes button
        if st.button("💾 Save Changes") and not loans_df.equals(edited_loans):
            # Handle additions, updates, and deletions
            for index, row in edited_loans.iterrows():
                if pd.isna(row['id']):  # New loan
                    add_loan(row['lender_name'], row['loan_type'], row['loan_date'], 
                           row['principal_amount'], row['interest_rate']/100, row['monthly_payment'], 
                           row['total_payments'], row['remaining_payments'], row['loan_direction'], row['status'])
                else:  # Existing loan
                    update_loan(row['id'], row['lender_name'], row['loan_type'], row['loan_date'], 
                              row['principal_amount'], row['interest_rate']/100, row['monthly_payment'], 
                              row['total_payments'], row['remaining_payments'], row['loan_direction'], row['status'])
            
            # Handle deletions (loans in original but not in edited)
            deleted_loans = loans_df[~loans_df['id'].isin(edited_loans['id'])]
            for _, row in deleted_loans.iterrows():
                delete_loan(row['id'])
            
            st.success("Loan records updated successfully!")
            st.rerun()
        
        # Export loans data
        csv = convert_df_to_csv(loans_df)
        st.download_button(
            label="📥 Download Loan Data as CSV",
            data=csv,
            file_name='loans.csv',
            mime='text/csv'
        )
    else:
        st.info("No loans found. Add loans using the form above.")

if __name__ == "__main__":
    main()