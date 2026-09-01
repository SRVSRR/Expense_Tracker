"""initial schema

Revision ID: 928e74198543
Revises: 
Create Date: 2026-09-01 12:22:45.312821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '928e74198543'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables from scratch."""
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('email', sa.String(), unique=True, index=True),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'accounts',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), index=True),
        sa.Column('name', sa.String(), index=True),
        sa.Column('currency', sa.String(), server_default='USD'),
        sa.Column('initial_balance', sa.Float(), server_default='0.0'),
        sa.Column('current_balance', sa.Float(), server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'transactions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), index=True),
        sa.Column('account_id', sa.String(), sa.ForeignKey('accounts.id'), index=True),
        sa.Column('type', sa.String(), index=True),
        sa.Column('amount', sa.Float()),
        sa.Column('category', sa.String(), index=True),
        sa.Column('description', sa.String()),
        sa.Column('merchant', sa.String(), nullable=True),
        sa.Column('date', sa.DateTime(), index=True),
        sa.Column('is_recurring', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'categories',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), index=True),
        sa.Column('name', sa.String(), index=True),
        sa.Column('parent_id', sa.String(), sa.ForeignKey('categories.id'), nullable=True),
        sa.Column('type', sa.String()),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'recurring_rules',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), index=True),
        sa.Column('transaction_id', sa.String(), sa.ForeignKey('transactions.id'), nullable=True),
        sa.Column('pattern', sa.String()),
        sa.Column('frequency', sa.Integer(), server_default='1'),
        sa.Column('expected_amount', sa.Float()),
        sa.Column('expected_date', sa.DateTime()),
        sa.Column('last_matched', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'predictions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), index=True),
        sa.Column('type', sa.String(), index=True),
        sa.Column('data', sa.String()),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('valid_until', sa.DateTime()),
    )

    op.create_table(
        'correction_logs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), index=True),
        sa.Column('description', sa.String()),
        sa.Column('merchant', sa.String(), nullable=True),
        sa.Column('suggested_category', sa.String()),
        sa.Column('corrected_category', sa.String()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('correction_logs')
    op.drop_table('predictions')
    op.drop_table('recurring_rules')
    op.drop_table('categories')
    op.drop_table('transactions')
    op.drop_table('accounts')
    op.drop_table('users')
