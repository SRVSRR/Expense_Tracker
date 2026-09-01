"""Pydantic request/response schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class CategoryBase(BaseModel):
    name: str
    type: TransactionType
    parent_id: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: str
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AccountBase(BaseModel):
    name: str
    currency: str = "USD"
    initial_balance: float = 0.0


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    currency: Optional[str] = None
    current_balance: Optional[float] = None


class Account(AccountBase):
    id: str
    user_id: str
    current_balance: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    type: TransactionType
    amount: float = Field(gt=0)
    category: str
    description: str
    merchant: Optional[str] = None
    date: datetime
    is_recurring: int = 0


class TransactionCreate(TransactionBase):
    account_id: str


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    date: Optional[datetime] = None
    is_recurring: Optional[int] = None


class Transaction(TransactionBase):
    id: str
    user_id: str
    account_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: str = Field(min_length=1)


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RecurringRuleBase(BaseModel):
    pattern: str
    frequency: int = 1
    expected_amount: float
    expected_date: datetime


class RecurringRuleCreate(RecurringRuleBase):
    transaction_id: Optional[str] = None


class RecurringRule(RecurringRuleBase):
    id: str
    user_id: str
    last_matched: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PredictionBase(BaseModel):
    type: str  # "cashflow", "runway", "anomaly", "budget"
    data: dict


class Prediction(PredictionBase):
    id: str
    user_id: str
    generated_at: datetime
    valid_until: datetime
    
    class Config:
        from_attributes = True
