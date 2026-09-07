"""Pydantic request/response schemas"""
from datetime import datetime
from typing import Optional, List, Dict
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
    auth_user_id: str
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
    auth_user_id: str
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
    auth_user_id: str
    account_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: str = Field(min_length=1)


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: str = Field(min_length=1)
    password: str


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
    auth_user_id: str
    transaction_id: Optional[str] = None
    last_matched: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PredictionBase(BaseModel):
    type: str  # "cashflow", "runway", "anomaly", "budget"
    data: dict


class Prediction(PredictionBase):
    id: str
    auth_user_id: str
    generated_at: datetime
    valid_until: datetime
    
    class Config:
        from_attributes = True


class CashflowForecastDay(BaseModel):
    date: str
    projected_balance: float
    expected_income: float
    expected_expense: float
    income_confidence_interval: Optional[Dict[str, float]] = None
    expense_confidence_interval: Optional[Dict[str, float]] = None


class CashflowForecast(BaseModel):
    period_days: int
    avg_daily_income: float
    avg_daily_expense: float
    forecast: List[CashflowForecastDay]

    class Config:
        json_schema_extra = {
            "example": {
                "period_days": 30,
                "avg_daily_income": 100.0,
                "avg_daily_expense": 85.5,
                "forecast": [
                    {"date": "2026-09-07", "projected_balance": 5114.5, "expected_income": 100.0, "expected_expense": 85.5},
                    {"date": "2026-09-08", "projected_balance": 5129.0, "expected_income": 100.0, "expected_expense": 85.5}
                ]
            }
        }


class RunwayForecast(BaseModel):
    current_balance: float
    avg_daily_income: float
    avg_daily_expense: float
    net_daily_burn: float
    threshold: float
    days_until_threshold: Optional[int]

    class Config:
        json_schema_extra = {
            "example": {
                "current_balance": 5000.0,
                "avg_daily_income": 100.0,
                "avg_daily_expense": 85.5,
                "net_daily_burn": -14.5,
                "threshold": 0.0,
                "days_until_threshold": None
            }
        }


class AnomalyItem(BaseModel):
    transaction_id: str
    amount: float
    category: str
    description: str
    date: str
    category_avg: float
    deviation_ratio: float


class AnomaliesResponse(BaseModel):
    total_transactions_analyzed: int
    anomalies_found: int
    anomalies: List[AnomalyItem]

    class Config:
        json_schema_extra = {
            "example": {
                "total_transactions_analyzed": 45,
                "anomalies_found": 2,
                "anomalies": [
                    {
                        "transaction_id": "abc123",
                        "amount": 500.0,
                        "category": "Food & Dining",
                        "description": "Expensive dinner",
                        "date": "2026-09-01T19:30:00",
                        "category_avg": 45.0,
                        "deviation_ratio": 11.11
                    }
                ]
            }
        }


class BudgetRecommendationItem(BaseModel):
    category: str
    monthly_average: float
    percent_of_income: float
    status: str
    suggested_budget: float


class BudgetRecommendations(BaseModel):
    avg_monthly_income: float
    avg_monthly_expense: float
    savings_rate_percent: float
    recommendations: List[BudgetRecommendationItem]

    class Config:
        json_schema_extra = {
            "example": {
                "avg_monthly_income": 5000.0,
                "avg_monthly_expense": 3500.0,
                "savings_rate_percent": 30.0,
                "recommendations": [
                    {
                        "category": "Food & Dining",
                        "monthly_average": 600.0,
                        "percent_of_income": 12.0,
                        "status": "moderate",
                        "suggested_budget": 540.0
                    }
                ]
            }
        }


class CategoryAnalysisItem(BaseModel):
    category: str
    total_spent: float
    monthly_average: float
    transaction_count: int
    percent_of_total: float


class CategoryAnalysis(BaseModel):
    period: str
    total_income: float
    total_expense: float
    net_flow: float
    categories: List[CategoryAnalysisItem]

    class Config:
        json_schema_extra = {
            "example": {
                "period": "last_3_months",
                "total_income": 15000.0,
                "total_expense": 10500.0,
                "net_flow": 4500.0,
                "categories": [
                    {
                        "category": "Food & Dining",
                        "total_spent": 1800.0,
                        "monthly_average": 600.0,
                        "transaction_count": 45,
                        "percent_of_total": 17.1
                    }
                ]
            }
        }


class CategorizeSuggestRequest(BaseModel):
    description: str
    merchant: Optional[str] = None


class CategorizeSuggestResponse(BaseModel):
    suggested_category: Optional[str]
    confidence: str
    all_categories: List[str]
    source: str

    class Config:
        json_schema_extra = {
            "example": {
                "suggested_category": "Food & Dining",
                "confidence": "high",
                "all_categories": ["Food & Dining", "Transportation", "Shopping"],
                "source": "ml"
            }
        }


class CategorizeCorrectionRequest(BaseModel):
    description: str
    merchant: Optional[str] = None
    suggested_category: str
    corrected_category: str


class CategorizeTrainResponse(BaseModel):
    status: str
    samples: int
    accuracy: Optional[float] = None
    num_classes: Optional[int] = None
    required: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "trained",
                "samples": 150,
                "accuracy": 0.92,
                "num_classes": 14,
                "required": 30
            }
        }


class CategorizeModelInfo(BaseModel):
    is_trained: bool
    training_samples: int
    model_exists: bool

    class Config:
        json_schema_extra = {
            "example": {
                "is_trained": True,
                "training_samples": 150,
                "model_exists": True
            }
        }


class RecurringUpcomingItem(BaseModel):
    id: str
    rule_id: str
    pattern: str
    frequency: int
    expected_amount: float
    expected_date: str
    transaction_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "rule123_2026-10-01T00:00:00",
                "rule_id": "rule123",
                "pattern": "monthly",
                "frequency": 1,
                "expected_amount": 100.0,
                "expected_date": "2026-10-01T00:00:00",
                "transaction_id": "tx456"
            }
        }
