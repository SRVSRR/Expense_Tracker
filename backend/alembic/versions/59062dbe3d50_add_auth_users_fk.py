"""add_auth_users_fk

Revision ID: 59062dbe3d50
Revises: 928e74198543
Create Date: 2026-09-07 09:56:17.641165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '59062dbe3d50'
down_revision: Union[str, Sequence[str], None] = '928e74198543'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add auth_user_id columns with FK to auth.users.id (cross-schema)."""
    # Add auth_user_id column to accounts
    op.add_column(
        "accounts",
        sa.Column("auth_user_id", UUID(as_uuid=False), nullable=True)
    )
    op.create_foreign_key(
        "fk_accounts_auth_user_id",
        "accounts",
        "users",
        ["auth_user_id"],
        ["id"],
        source_schema="public",
        referent_schema="auth",
    )

    # Add auth_user_id column to transactions
    op.add_column(
        "transactions",
        sa.Column("auth_user_id", UUID(as_uuid=False), nullable=True)
    )
    op.create_foreign_key(
        "fk_transactions_auth_user_id",
        "transactions",
        "users",
        ["auth_user_id"],
        ["id"],
        source_schema="public",
        referent_schema="auth",
    )

    # Add auth_user_id column to categories
    op.add_column(
        "categories",
        sa.Column("auth_user_id", UUID(as_uuid=False), nullable=True)
    )
    op.create_foreign_key(
        "fk_categories_auth_user_id",
        "categories",
        "users",
        ["auth_user_id"],
        ["id"],
        source_schema="public",
        referent_schema="auth",
    )

    # Add auth_user_id column to recurring_rules
    op.add_column(
        "recurring_rules",
        sa.Column("auth_user_id", UUID(as_uuid=False), nullable=True)
    )
    op.create_foreign_key(
        "fk_recurring_rules_auth_user_id",
        "recurring_rules",
        "users",
        ["auth_user_id"],
        ["id"],
        source_schema="public",
        referent_schema="auth",
    )

    # Add auth_user_id column to predictions
    op.add_column(
        "predictions",
        sa.Column("auth_user_id", UUID(as_uuid=False), nullable=True)
    )
    op.create_foreign_key(
        "fk_predictions_auth_user_id",
        "predictions",
        "users",
        ["auth_user_id"],
        ["id"],
        source_schema="public",
        referent_schema="auth",
    )

    # Add auth_user_id column to correction_logs
    op.add_column(
        "correction_logs",
        sa.Column("auth_user_id", UUID(as_uuid=False), nullable=True)
    )
    op.create_foreign_key(
        "fk_correction_logs_auth_user_id",
        "correction_logs",
        "users",
        ["auth_user_id"],
        ["id"],
        source_schema="public",
        referent_schema="auth",
    )


def downgrade() -> None:
    """Remove auth_user_id columns and their FKs."""
    op.drop_constraint("fk_correction_logs_auth_user_id", "correction_logs", type_="foreignkey")
    op.drop_column("correction_logs", "auth_user_id")

    op.drop_constraint("fk_predictions_auth_user_id", "predictions", type_="foreignkey")
    op.drop_column("predictions", "auth_user_id")

    op.drop_constraint("fk_recurring_rules_auth_user_id", "recurring_rules", type_="foreignkey")
    op.drop_column("recurring_rules", "auth_user_id")

    op.drop_constraint("fk_categories_auth_user_id", "categories", type_="foreignkey")
    op.drop_column("categories", "auth_user_id")

    op.drop_constraint("fk_transactions_auth_user_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "auth_user_id")

    op.drop_constraint("fk_accounts_auth_user_id", "accounts", type_="foreignkey")
    op.drop_column("accounts", "auth_user_id")