"""Increase task column lengths

Revision ID: 003
Revises: 001
Create Date: 2026-03-26 08:12:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Increase VARCHAR column lengths in tasks table to accommodate real-world data.

    This is a safe operation - increasing column lengths does not lose existing data.
    """
    # Long field: WP descriptions can be very long
    op.alter_column('tasks', 'wp', type_=sa.String(500), existing_type=sa.String(100))

    # Medium fields: increase to 255
    op.alter_column('tasks', 'product', type_=sa.String(255), existing_type=sa.String(100))
    op.alter_column('tasks', 'unit', type_=sa.String(255), existing_type=sa.String(50))
    op.alter_column('tasks', 'resource_name', type_=sa.String(255), existing_type=sa.String(255))

    # Short fields: adjust to 50 where appropriate
    op.alter_column('tasks', 'site', type_=sa.String(50), existing_type=sa.String(100))
    op.alter_column('tasks', 'category', type_=sa.String(50), existing_type=sa.String(100))
    op.alter_column('tasks', 'spc', type_=sa.String(50), existing_type=sa.String(100))


def downgrade() -> None:
    """Revert column lengths to original values.

    WARNING: This may cause data truncation if existing data exceeds original limits.
    """
    op.alter_column('tasks', 'wp', type_=sa.String(100), existing_type=sa.String(500))
    op.alter_column('tasks', 'product', type_=sa.String(100), existing_type=sa.String(255))
    op.alter_column('tasks', 'unit', type_=sa.String(50), existing_type=sa.String(255))
    op.alter_column('tasks', 'resource_name', type_=sa.String(255), existing_type=sa.String(255))
    op.alter_column('tasks', 'site', type_=sa.String(100), existing_type=sa.String(50))
    op.alter_column('tasks', 'category', type_=sa.String(100), existing_type=sa.String(50))
    op.alter_column('tasks', 'spc', type_=sa.String(100), existing_type=sa.String(50))
