"""
REST API for Algo Hub Financial Dashboard
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
import os
import jwt
from pydantic import BaseModel
from typing import List, Optional
from database import get_db_connection
from currency_manager import CurrencyManager
from audit_trail import AuditTrail

app = FastAPI(title="Algo Hub Financial API", version="1.0.0")
security = HTTPBearer()

# Models
class TransactionCreate(BaseModel):
    date: str
    description: str
    category: str
    amount: float
    type: str
    currency_code: str = "PKR"

class TransactionUpdate(BaseModel):
    date: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    type: Optional[str] = None

# Authentication dependency
def verify_token(token: str = Depends(security)):
    try:
        # Verify JWT token using environment variable
        secret_key = os.getenv('JWT_SECRET_KEY', 'default-secret-key-change-in-production')
        payload = jwt.decode(token.credentials, secret_key, algorithms=["HS256"])
        return payload
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# API Endpoints
@app.get("/api/v1/transactions")
def get_transactions(skip: int = 0, limit: int = 100, currency: str = "PKR"):
    """Get all transactions with optional currency filter"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if currency and currency != "ALL":
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE currency_code = ? 
            ORDER BY date DESC 
            LIMIT ? OFFSET ?
        ''', (currency, limit, skip))
    else:
        cursor.execute('''
            SELECT * FROM transactions 
            ORDER BY date DESC 
            LIMIT ? OFFSET ?
        ''', (limit, skip))
    
    results = cursor.fetchall()
    conn.close()
    return results

@app.post("/api/v1/transactions")
def create_transaction(tx: TransactionCreate, user: dict = Depends(verify_token)):
    """Create a new transaction with audit logging"""
    currency_manager = CurrencyManager()
    base_amount = currency_manager.convert_amount(tx.amount, tx.currency_code, "PKR")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (date, description, category, amount, type, currency_code, base_currency_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (tx.date, tx.description, tx.category, tx.amount, tx.type, tx.currency_code, base_amount))
    
    transaction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Log the action
    AuditTrail.log_action('transaction', transaction_id, 'CREATE', None, tx.dict(), user.get('id'))
    
    return {"id": transaction_id, "status": "created"}

@app.get("/api/v1/currencies")
def get_currencies():
    """Get all supported currencies"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM currencies WHERE is_active = 1")
    results = cursor.fetchall()
    conn.close()
    return results

@app.get("/api/v1/audit-logs")
def get_audit_logs(entity_type: str = None, entity_id: int = None):
    """Get audit logs with optional filters"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if entity_type and entity_id:
        cursor.execute('''
            SELECT * FROM audit_logs 
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY timestamp DESC
        ''', (entity_type, entity_id))
    elif entity_type:
        cursor.execute('''
            SELECT * FROM audit_logs 
            WHERE entity_type = ?
            ORDER BY timestamp DESC
        ''', (entity_type,))
    else:
        cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC")
    
    results = cursor.fetchall()
    conn.close()
    return results