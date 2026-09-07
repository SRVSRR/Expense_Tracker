"""drop_local_users_table

Revision ID: b3028a70b346
Revises: 59062dbe3d50
Create Date: 2026-09-07 14:08:32.940569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3028a70b346'
down_revision: Union[str, Sequence[str], None] = '59062dbe3d50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop local users table from public schema (Supabase Auth is now the auth provider)."""
    # Drop foreign key constraints first
    op.drop_constraint('accounts_user_id_fkey', 'accounts', type_='foreignkey')
    op.drop_constraint('fk_accounts_auth_user_id', 'accounts', type_='foreignkey')
    op.drop_constraint('fk_transactions_auth_user_id', 'transactions', type_='foreignkey')
    op.drop_constraint('transactions_account_id_fkey', 'transactions', type_='foreignkey')
    op.drop_constraint('transactions_user_id_fkey', 'transactions', type_='foreignkey')
    op.drop_constraint('categories_parent_id_fkey', 'categories', type_='foreignkey')
    op.drop_constraint('categories_user_id_fkey', 'categories', type_='foreignkey')
    op.drop_constraint('fk_categories_auth_user_id', 'categories', type_='foreignkey')
    op.drop_constraint('fk_recurring_rules_auth_user_id', 'recurring_rules', type_='foreignkey')
    op.drop_constraint('recurring_rules_transaction_id_fkey', 'recurring_rules', type_='foreignkey')
    op.drop_constraint('recurring_rules_user_id_fkey', 'recurring_rules', type_='foreignkey')
    op.drop_constraint('fk_predictions_auth_user_id', 'predictions', type_='foreignkey')
    op.drop_constraint('predictions_user_id_fkey', 'predictions', type_='foreignkey')
    op.drop_constraint('correction_logs_user_id_fkey', 'correction_logs', type_='foreignkey')
    op.drop_constraint('fk_correction_logs_auth_user_id', 'correction_logs', type_='foreignkey')
    
    # Drop user_id columns
    op.drop_column('accounts', 'user_id')
    op.drop_column('transactions', 'user_id')
    op.drop_column('categories', 'user_id')
    op.drop_column('recurring_rules', 'user_id')
    op.drop_column('predictions', 'user_id')
    op.drop_column('correction_logs', 'user_id')
    
    # Drop the local users table
    op.drop_table('users')


def downgrade() -> None:
    """Recreate local users table and foreign keys."""
    # Recreate users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Re-add user_id columns
    op.add_column('accounts', sa.Column('user_id', sa.String(), nullable=True))
    op.add_column('transactions', sa.Column('user_id', sa.String(), nullable=True))
    op.add_column('categories', sa.Column('user_id', sa.String(), nullable=True))
    op.add_column('recurring_rules', sa.Column('user_id', sa.String(), nullable=True))
    op.add_column('predictions', sa.Column('user_id', sa.String(), nullable=True))
    op.add_column('correction_logs', sa.Column('user_id', sa.String(), nullable=True))
    
    # Recreate foreign keys
    op.create_foreign_key('fk_accounts_user_id', 'accounts', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_transactions_user_id', 'transactions', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_categories_user_id', 'categories', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_recurring_rules_user_id', 'recurring_rules', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_predictions_user_id', 'predictions', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_correction_logs_user_id', 'correction_logs', 'users', ['user_id'], ['id'])