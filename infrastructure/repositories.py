"""
Repository implementations for data access
"""
from typing import List, Optional
from domain.entities import Transaction
from abc import ABC, abstractmethod
import sqlite3
import pandas as pd
from database import get_db_connection, _db_lock
import logging

logger = logging.getLogger(__name__)


class TransactionRepository(ABC):
    """Abstract base class for transaction repository"""
    
    @abstractmethod
    def create(self, transaction: Transaction) -> int:
        pass

    @abstractmethod
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        pass

    @abstractmethod
    def get_all(self, page: int = 1, page_size: int = 50) -> List[Transaction]:
        pass

    @abstractmethod
    def update(self, transaction: Transaction) -> bool:
        pass

    @abstractmethod
    def delete(self, transaction_id: int) -> bool:
        pass


class SQLiteTransactionRepository(TransactionRepository):
    """SQLite implementation of transaction repository"""
    
    def create(self, transaction: Transaction) -> int:
        with _db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO transactions (date, description, category, amount, type, currency_code, base_currency_amount, exchange_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transaction.date,
                transaction.description,
                transaction.category,
                transaction.amount,
                transaction.type,
                transaction.currency_code,
                transaction.base_currency_amount,
                transaction.exchange_rate
            ))

            transaction_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return transaction_id

    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        with _db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, date, description, category, amount, type, currency_code, base_currency_amount, exchange_rate
                FROM transactions WHERE id = ?
            ''', (transaction_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return Transaction(
                    id=row[0],
                    date=row[1],
                    description=row[2],
                    category=row[3],
                    amount=row[4],
                    type=row[5],
                    currency_code=row[6],
                    base_currency_amount=row[7],
                    exchange_rate=row[8]
                )
            return None

    def get_all(self, page: int = 1, page_size: int = 50) -> List[Transaction]:
        offset = (page - 1) * page_size
        
        with _db_lock:
            conn = get_db_connection()
            df = pd.read_sql_query(
                "SELECT id, date, description, category, amount, type, currency_code, base_currency_amount, exchange_rate FROM transactions ORDER BY date DESC LIMIT ? OFFSET ?",
                conn,
                params=(page_size, offset)
            )
            conn.close()

        transactions = []
        for _, row in df.iterrows():
            transaction = Transaction(
                id=row['id'],
                date=row['date'],
                description=row['description'],
                category=row['category'],
                amount=row['amount'],
                type=row['type'],
                currency_code=row['currency_code'],
                base_currency_amount=row['base_currency_amount'],
                exchange_rate=row['exchange_rate']
            )
            transactions.append(transaction)

        return transactions

    def update(self, transaction: Transaction) -> bool:
        if not transaction.id:
            return False

        with _db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE transactions
                SET date = ?, description = ?, category = ?, amount = ?, type = ?, currency_code = ?, base_currency_amount = ?, exchange_rate = ?
                WHERE id = ?
            ''', (
                transaction.date,
                transaction.description,
                transaction.category,
                transaction.amount,
                transaction.type,
                transaction.currency_code,
                transaction.base_currency_amount,
                transaction.exchange_rate,
                transaction.id
            ))

            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()

            return updated

    def delete(self, transaction_id: int) -> bool:
        with _db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
            deleted = cursor.rowcount > 0

            conn.commit()
            conn.close()

            return deleted


class PostgreSQLTransactionRepository(TransactionRepository):
    """PostgreSQL implementation of transaction repository"""
    
    def create(self, transaction: Transaction) -> int:
        # This would be implemented with PostgreSQL-specific code
        # For now, we'll raise NotImplementedError as this is just a placeholder
        raise NotImplementedError("PostgreSQL implementation not yet complete")

    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        raise NotImplementedError("PostgreSQL implementation not yet complete")

    def get_all(self, page: int = 1, page_size: int = 50) -> List[Transaction]:
        raise NotImplementedError("PostgreSQL implementation not yet complete")

    def update(self, transaction: Transaction) -> bool:
        raise NotImplementedError("PostgreSQL implementation not yet complete")

    def delete(self, transaction_id: int) -> bool:
        raise NotImplementedError("PostgreSQL implementation not yet complete")