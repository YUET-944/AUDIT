"""
Advanced reporting and analytics module for the financial dashboard
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from database import get_db_connection, get_transactions, get_investments, get_loans, get_budgets
from calculations import format_currency
import logging
from datetime import datetime, timedelta
import traceback
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score
import warnings
warnings.filterwarnings('ignore')

# Import caching and monitoring
from caching import cache_report_data, cache_financial_summary
from monitoring import log_performance

logger = logging.getLogger(__name__)

class AdvancedReporting:
    def __init__(self):
        self.conn = get_db_connection()
    
    @cache_report_data(ttl=900)  # Cache for 15 minutes
    @log_performance
    def cash_flow_forecasting(self, months_ahead=6):
        """Generate cash flow forecast based on historical trends"""
        try:
            # Get historical transaction data
            transactions_df = get_transactions()
            
            if transactions_df.empty:
                logger.warning("No transaction data available for cash flow forecasting")
                return pd.DataFrame()
            
            # Convert date to datetime if needed
            transactions_df['date'] = pd.to_datetime(transactions_df['date'])
            
            # Group by month and type
            transactions_df['year_month'] = transactions_df['date'].dt.to_period('M')
            monthly_data = transactions_df.groupby(['year_month', 'type']).agg({
                'amount': 'sum'
            }).reset_index()
            
            # Pivot to have Income and Expense as columns
            monthly_pivot = monthly_data.pivot(index='year_month', columns='type', values='amount').fillna(0)
            
            # Prepare data for forecasting
            historical_months = len(monthly_pivot)
            if historical_months < 3:
                logger.warning("Insufficient historical data for forecasting")
                return pd.DataFrame()
            
            # Prepare X (time periods) and Y (amounts) for regression
            X = np.array(range(historical_months)).reshape(-1, 1)
            
            # Forecast income if available
            if 'Income' in monthly_pivot.columns:
                income_y = monthly_pivot['Income'].values
                income_model = Pipeline([
                    ('poly', PolynomialFeatures(degree=2)),
                    ('linear', LinearRegression())
                ])
                income_model.fit(X, income_y)
                
                # Predict future income
                future_X = np.array(range(historical_months, historical_months + months_ahead)).reshape(-1, 1)
                future_income = income_model.predict(future_X)
            else:
                future_income = np.zeros(months_ahead)
            
            # Forecast expenses if available
            if 'Expense' in monthly_pivot.columns:
                expense_y = monthly_pivot['Expense'].values
                expense_model = Pipeline([
                    ('poly', PolynomialFeatures(degree=2)),
                    ('linear', LinearRegression())
                ])
                expense_model.fit(X, expense_y)
                
                # Predict future expenses
                future_expense = expense_model.predict(future_X)
            else:
                future_expense = np.zeros(months_ahead)
            
            # Create forecast dataframe
            last_month = monthly_pivot.index[-1]
            forecast_dates = []
            for i in range(1, months_ahead + 1):
                # Convert period to timestamp, add months, then back to period
                last_month_ts = last_month.to_timestamp()
                next_month_ts = last_month_ts + pd.DateOffset(months=i)
                next_month = next_month_ts.to_period('M')
                forecast_dates.append(next_month)
            
            forecast_df = pd.DataFrame({
                'date': forecast_dates,
                'forecasted_income': future_income,
                'forecasted_expense': future_expense,
                'forecasted_net': future_income - future_expense
            })
            
            logger.info(f"Generated cash flow forecast for {months_ahead} months ahead")
            return forecast_df
            
        except Exception as e:
            logger.error(f"Error in cash flow forecasting: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    @cache_report_data(ttl=900)  # Cache for 15 minutes
    @log_performance
    def budget_variance_analysis(self, variance_threshold=0.1):
        """Analyze budget vs actual performance with variance reporting"""
        try:
            from calculations import calculate_budget_variance
            
            budgets_df = get_budgets()
            if budgets_df.empty:
                logger.warning("No budget data available for variance analysis")
                return pd.DataFrame()
            
            # Calculate variance
            variance_df = calculate_budget_variance(budgets_df)
            
            # Filter categories with significant variance
            significant_variance = variance_df[
                abs(variance_df['variance_percentage']) > variance_threshold * 100
            ].copy()
            
            logger.info(f"Found {len(significant_variance)} budget categories with significant variance")
            return significant_variance
            
        except Exception as e:
            logger.error(f"Error in budget variance analysis: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    @cache_report_data(ttl=900)  # Cache for 15 minutes
    @log_performance
    def financial_ratios_analysis(self):
        """Calculate key financial ratios"""
        try:
            transactions_df = get_transactions()
            if transactions_df.empty:
                logger.warning("No transaction data available for ratio analysis")
                return {}
            
            # Calculate total income and expenses
            total_income = transactions_df[transactions_df['type'] == 'Income']['amount'].sum()
            total_expenses = transactions_df[transactions_df['type'] == 'Expense']['amount'].sum()
            net_income = total_income - total_expenses
            
            # Calculate ratios
            ratios = {}
            
            if total_income > 0:
                # Profit margin
                ratios['profit_margin'] = (net_income / total_income) * 100
                
                # Income to expense ratio
                ratios['income_expense_ratio'] = total_income / max(total_expenses, 1)
            
            # Calculate current ratio (simplified as income to expenses)
            ratios['current_ratio'] = total_income / max(total_expenses, 1) if total_expenses > 0 else float('inf')
            
            # Debt to equity - need to get this from loans and investments
            investments_df = get_investments()
            total_investments = investments_df['amount'].sum() if not investments_df.empty else 0
            
            loans_df = get_loans()
            total_loans = loans_df['principal_amount'].sum() if not loans_df.empty else 0
            
            ratios['debt_to_equity'] = total_loans / max(total_investments, 1) if total_investments > 0 else float('inf')
            
            logger.info("Calculated financial ratios")
            return ratios
            
        except Exception as e:
            logger.error(f"Error in financial ratios analysis: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    @cache_report_data(ttl=900)  # Cache for 15 minutes
    @log_performance
    def generate_custom_report(self, start_date=None, end_date=None, categories=None, report_type='detailed'):
        """Generate custom report based on specified parameters"""
        try:
            transactions_df = get_transactions()
            if transactions_df.empty:
                logger.warning("No transaction data available for custom report")
                return pd.DataFrame()
            
            # Apply date filters
            if start_date:
                transactions_df = transactions_df[transactions_df['date'] >= start_date]
            if end_date:
                transactions_df = transactions_df[transactions_df['date'] <= end_date]
            
            # Apply category filters
            if categories:
                transactions_df = transactions_df[transactions_df['category'].isin(categories)]
            
            if report_type == 'summary':
                # Group by type and category for summary
                summary = transactions_df.groupby(['type', 'category']).agg({
                    'amount': ['sum', 'count', 'mean']
                }).round(2)
                summary.columns = ['total_amount', 'transaction_count', 'average_amount']
                return summary.reset_index()
            else:
                # Return detailed transaction list
                return transactions_df.sort_values('date', ascending=False)
                
        except Exception as e:
            logger.error(f"Error in custom report generation: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    @cache_report_data(ttl=900)  # Cache for 15 minutes
    @log_performance
    def trend_analysis(self, comparison_period='year_over_year'):
        """Analyze financial trends with comparative period views"""
        try:
            transactions_df = get_transactions()
            if transactions_df.empty:
                logger.warning("No transaction data available for trend analysis")
                return pd.DataFrame()
            
            # Convert date to datetime
            transactions_df['date'] = pd.to_datetime(transactions_df['date'])
            
            # Group by month and type for trend analysis
            transactions_df['year_month'] = transactions_df['date'].dt.to_period('M')
            monthly_trends = transactions_df.groupby(['year_month', 'type']).agg({
                'amount': 'sum'
            }).reset_index()
            
            # Pivot to show trends
            trend_pivot = monthly_trends.pivot(index='year_month', columns='type', values='amount').fillna(0)
            
            # Calculate month-over-month changes
            for col in trend_pivot.columns:
                trend_pivot[f'{col}_mom_change'] = trend_pivot[col].pct_change() * 100
            
            logger.info("Generated trend analysis")
            return trend_pivot
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    @cache_report_data(ttl=900)  # Cache for 15 minutes
    @log_performance
    def create_visual_report(self, report_type='cash_flow'):
        """Create visual report using Plotly"""
        try:
            if report_type == 'cash_flow':
                # Generate cash flow forecast
                forecast_df = self.cash_flow_forecasting(months_ahead=6)
                
                if forecast_df.empty:
                    logger.warning("No data available for cash flow visual report")
                    return None
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=forecast_df['date'].astype(str),
                    y=forecast_df['forecasted_income'],
                    mode='lines+markers',
                    name='Forecasted Income',
                    line=dict(color='#2ECC71', width=3)
                ))
                
                fig.add_trace(go.Scatter(
                    x=forecast_df['date'].astype(str),
                    y=forecast_df['forecasted_expense'],
                    mode='lines+markers',
                    name='Forecasted Expense',
                    line=dict(color='#E74C3C', width=3)
                ))
                
                fig.add_trace(go.Scatter(
                    x=forecast_df['date'].astype(str),
                    y=forecast_df['forecasted_net'],
                    mode='lines+markers',
                    name='Forecasted Net',
                    line=dict(color='#3498DB', width=3)
                ))
                
                fig.update_layout(
                    title="Cash Flow Forecast",
                    xaxis_title="Month",
                    yaxis_title="Amount (PKR)",
                    hovermode='x unified'
                )
                
                return fig
                
            elif report_type == 'ratios':
                ratios = self.financial_ratios_analysis()
                
                if not ratios:
                    logger.warning("No data available for ratios visual report")
                    return None
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=list(ratios.keys()),
                        y=list(ratios.values()),
                        text=[f"{v:.2f}%" if k.endswith('margin') or k.endswith('ratio') else f"{v:.2f}" for k, v in ratios.items()],
                        textposition='auto'
                    )
                ])
                
                fig.update_layout(
                    title="Financial Ratios Analysis",
                    xaxis_title="Ratio",
                    yaxis_title="Value",
                    yaxis_tickformat=".2f"
                )
                
                return fig
                
        except Exception as e:
            logger.error(f"Error in creating visual report: {str(e)}\n{traceback.format_exc()}")
            raise e

# Helper functions for the main app
def generate_cash_flow_forecast():
    """Generate cash flow forecast for the main app"""
    try:
        reporter = AdvancedReporting()
        forecast = reporter.cash_flow_forecasting(months_ahead=6)
        return forecast
    except Exception as e:
        logger.error(f"Error generating cash flow forecast: {str(e)}\n{traceback.format_exc()}")
        return pd.DataFrame()

def generate_budget_variance_report():
    """Generate budget variance report for the main app"""
    try:
        reporter = AdvancedReporting()
        variance_report = reporter.budget_variance_analysis()
        return variance_report
    except Exception as e:
        logger.error(f"Error generating budget variance report: {str(e)}\n{traceback.format_exc()}")
        return pd.DataFrame()

def get_financial_ratios():
    """Get financial ratios for the main app"""
    try:
        reporter = AdvancedReporting()
        ratios = reporter.financial_ratios_analysis()
        return ratios
    except Exception as e:
        logger.error(f"Error getting financial ratios: {str(e)}\n{traceback.format_exc()}")
        return {}