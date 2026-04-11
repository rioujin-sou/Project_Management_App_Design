"""Add project_visibility table

Revision ID: 005
Revises: 004
Create Date: 2026-04-02 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'project_visibility',
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('project_id', 'user_id'),
    )

    # Grant all existing projects visibility to all current TDL users
    op.execute("""
        INSERT INTO project_visibility (project_id, user_id)
        SELECT p.id, u.id
        FROM projects p
        CROSS JOIN users u
        WHERE u.role = 'tdl'
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table('project_visibility')