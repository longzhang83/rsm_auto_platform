"""make_hashed_password_nullable

Revision ID: 98b37281c92b
Revises: e56799c6d3bd
Create Date: 2025-11-12 13:00:39.317966

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98b37281c92b'
down_revision: Union[str, Sequence[str], None] = 'e56799c6d3bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Make hashed_password nullable for WeWork login support."""
    # SQLite doesn't support ALTER COLUMN, so we use batch operations to recreate the table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('hashed_password',
                              existing_type=sa.String(length=255),
                              nullable=True)


def downgrade() -> None:
    """Downgrade schema - Make hashed_password NOT NULL again."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('hashed_password',
                              existing_type=sa.String(length=255),
                              nullable=False)
