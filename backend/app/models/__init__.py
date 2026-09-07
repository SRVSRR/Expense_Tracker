"""SQLAlchemy ORM Models"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
import os

Base = declarative_base()

# Helper to conditionally add auth_user_id column (only in production PostgreSQL)
# Tests use SQLite in-memory which doesn't support UUID or auth schema
TESTING = os.getenv("TESTING") == "1"

def auth_user_id_column():
    """Return auth_user_id column for production, or String column for tests."""
    if TESTING:
        # SQLite doesn't support UUID, use String for testing
        return Column(String, nullable=True, index=True)
    return Column(UUID(as_uuid=False), ForeignKey("auth.users.id"), nullable=True, index=True)


class User(Base):
    """Minimal user model for Supabase auth.users lookup."""
    __tablename__ = "users"
    
    # Only use auth schema in production (not tests)
    if not TESTING:
        __table_args__ = {"schema": "auth"}
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    # password_hash only for local testing (TESTING=1); Supabase manages auth in production
    if TESTING:
        password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(String, primary_key=True)
    auth_user_id = auth_user_id_column()
    name = Column(String, index=True)
    currency = Column(String, default="USD")
    initial_balance = Column(Float, default=0.0)
    current_balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="account")


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True)
    auth_user_id = auth_user_id_column()
    account_id = Column(String, ForeignKey("accounts.id"), index=True)
    type = Column(SQLEnum(TransactionType), index=True)
    amount = Column(Float)
    category = Column(String, index=True)
    description = Column(String)
    merchant = Column(String, nullable=True)
    date = Column(DateTime, index=True)
    is_recurring = Column(Integer, default=0)  # Boolean as integer for compatibility
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True)
    auth_user_id = auth_user_id_column()
    name = Column(String, index=True)
    parent_id = Column(String, ForeignKey("categories.id"), nullable=True)
    type = Column(SQLEnum(TransactionType))
    color = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Self-referencing relationship for subcategories
    subcategories = relationship("Category", remote_side=[id])


class RecurringRule(Base):
    __tablename__ = "recurring_rules"
    
    id = Column(String, primary_key=True)
    auth_user_id = auth_user_id_column()
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=True)
    pattern = Column(String)  # e.g., "monthly", "weekly", "daily"
    frequency = Column(Integer, default=1)  # Every N periods
    expected_amount = Column(Float)
    expected_date = Column(DateTime)
    last_matched = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(String, primary_key=True)
    auth_user_id = auth_user_id_column()
    type = Column(String, index=True)  # "cashflow", "runway", "anomaly", "budget"
    data = Column(String)  # JSON string with predictions
    generated_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)


class CorrectionLog(Base):
    __tablename__ = "correction_logs"

    id = Column(String, primary_key=True)
    auth_user_id = auth_user_id_column()
    description = Column(String)
    merchant = Column(String, nullable=True)
    suggested_category = Column(String)
    corrected_category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)