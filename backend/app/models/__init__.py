"""SQLAlchemy ORM Models"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accounts = relationship("Account", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    name = Column(String, index=True)
    currency = Column(String, default="USD")
    initial_balance = Column(Float, default=0.0)
    current_balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
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
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
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
    user_id = Column(String, ForeignKey("users.id"), index=True)
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
    user_id = Column(String, ForeignKey("users.id"), index=True)
    type = Column(String, index=True)  # "cashflow", "runway", "anomaly", "budget"
    data = Column(String)  # JSON string with predictions
    generated_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)


class CorrectionLog(Base):
    __tablename__ = "correction_logs"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    description = Column(String)
    merchant = Column(String, nullable=True)
    suggested_category = Column(String)
    corrected_category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
