from datetime import datetime
from types import SimpleNamespace

from app.models import Account, TransactionType
from app.routes.recurring import _generate_occurrences
from app.routes.transactions import apply_transaction_balance


def test_transaction_balance_application_and_reversal():
    account = Account(current_balance=100.0)

    apply_transaction_balance(account, TransactionType.EXPENSE, 25.0)
    assert account.current_balance == 75.0

    apply_transaction_balance(account, TransactionType.EXPENSE, 5.0, multiplier=-1)
    assert account.current_balance == 80.0

    apply_transaction_balance(account, TransactionType.INCOME, 20.0)
    assert account.current_balance == 100.0


def test_monthly_occurrences_handle_short_months():
    rule = SimpleNamespace(
        expected_date=datetime(2026, 1, 31),
        pattern="monthly",
        frequency=1,
    )

    occurrences = _generate_occurrences(
        rule,
        datetime(2026, 1, 1),
        datetime(2026, 4, 1),
    )

    assert [occurrence.date().isoformat() for occurrence in occurrences] == [
        "2026-01-31",
        "2026-02-28",
        "2026-03-28",
    ]
