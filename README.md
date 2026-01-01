# Algo Hub Financial Dashboard

A comprehensive financial management application with multi-currency support, audit trails, bank integration, and AI-powered automation.

## Features

### Core Financial Management
- Income/Expense tracking
- Employee payroll management
- Budget planning and monitoring
- Investment and loan tracking
- Real-time dashboard with KPIs

### Enterprise Features
- **Multi-Currency Support**: Real-time currency conversion with exchange rates
- **Immutable Audit Trail**: Complete tracking of all changes with SHA256 hashing
- **Bank Integration**: Automated reconciliation with fuzzy matching
- **REST API**: FastAPI-based API with JWT authentication
- **AI & Automation**: OCR for receipts, anomaly detection, category prediction
- **Security**: Encrypted sensitive data, secure authentication

## Architecture

### Technology Stack
- **Backend**: Python 3.9+
- **Web Framework**: Streamlit (UI), FastAPI (REST API)
- **Database**: SQLite (with migration support)
- **Data Processing**: Pandas, NumPy
- **Visualizations**: Plotly
- **Security**: Cryptography, bcrypt
- **AI/ML**: Scikit-learn, Tesseract OCR

### File Structure
```
algo-hub-audit/
├── app.py                    # Main Streamlit application
├── api/
│   └── main.py             # FastAPI REST endpoints
├── currency_manager.py     # Multi-currency support
├── audit_trail.py          # Immutable audit logging
├── bank_integration.py     # Bank reconciliation
├── ai_automation.py        # OCR and anomaly detection
├── security.py             # Encryption and auth
├── database.py             # Database operations
├── calculations.py         # Financial calculations
├── migrations/             # Database migration scripts
├── tests/                  # Test suite
├── requirements.txt        # Dependencies
├── Dockerfile              # Containerization
└── docker-compose.yml      # Multi-container setup
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- pip package manager

### Installation
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```bash
   python -c "from database import init_db; init_db()"
   ```

4. Run database migrations:
   ```bash
   python run_migrations.py
   ```

### Running the Application

#### Web Application (Streamlit)
```bash
streamlit run app.py
```

#### REST API (FastAPI)
```bash
uvicorn api.main:app --reload
```

### Docker Deployment
```bash
docker-compose up --build
```

## API Endpoints

### Transactions
- `GET /api/v1/transactions` - Get all transactions
- `POST /api/v1/transactions` - Create new transaction
- `GET /api/v1/currencies` - Get supported currencies
- `GET /api/v1/audit-logs` - Get audit trail

## Database Schema

### Core Tables
- `transactions` - Financial transactions with multi-currency support
- `currencies` - Supported currencies
- `audit_logs` - Immutable audit trail
- `bank_accounts` - Bank account information
- `bank_transactions` - Bank transaction records
- `company_investments` - Company investment tracking
- `loans` - Loan management
- `employees` - Employee information
- `budgets` - Budget planning

## Security Features

- Encrypted sensitive data (bank tokens, API keys)
- JWT-based authentication
- Parameterized SQL queries to prevent injection
- Immutable audit logs with SHA256 hashing

## Testing

Run the test suite:
```bash
pytest tests/
```

## Enterprise Compliance

- Complete audit trail with immutable logs
- Multi-currency support with real-time exchange rates
- Automated bank reconciliation
- AI-powered anomaly detection
- Secure data encryption
- REST API with authentication and rate limiting

## Development

### Adding New Features
1. Create migration script in `migrations/`
2. Update database functions in `database.py`
3. Add business logic in appropriate modules
4. Create API endpoints in `api/main.py`
5. Add tests in `tests/`
6. Update documentation

### Database Migrations
Migration scripts are located in `migrations/` directory and run in numerical order.