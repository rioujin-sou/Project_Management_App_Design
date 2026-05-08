"""Add task_precedence table

Revision ID: 006
Revises: 005
Create Date: 2026-05-08 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'task_precedence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('predecessor_task_id', sa.Integer(), nullable=False),
        sa.Column('successor_task_id', sa.Integer(), nullable=False),
        sa.Column('precedence_type', sa.String(length=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['predecessor_task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['successor_task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('predecessor_task_id', 'successor_task_id', name='uq_task_precedence_pair'),
    )
    op.create_index('ix_task_precedence_id', 'task_precedence', ['id'], unique=False)
    op.create_index('ix_task_precedence_successor', 'task_precedence', ['successor_task_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_task_precedence_successor', table_name='task_precedence')
    op.drop_index('ix_task_precedence_id', table_name='task_precedence')
    op.drop_table('task_precedence')
