"""Add pm and sa roles to userrole enum

Revision ID: 004
Revises: 003
Create Date: 2026-04-02 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL requires explicit enum type alteration
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'pm'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'sa'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # To downgrade, reassign any pm/sa users to pending first, then
    # recreate the enum without the new values.
    op.execute("UPDATE users SET role = 'pending' WHERE role IN ('pm', 'sa')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50)")
    op.execute("DROP TYPE userrole")
    op.execute("CREATE TYPE userrole AS ENUM ('pending', 'tdl', 'tpm')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole")