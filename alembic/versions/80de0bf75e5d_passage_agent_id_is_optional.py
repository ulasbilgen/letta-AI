"""Passage: agent_id is optional

Revision ID: 80de0bf75e5d
Revises: 8939dc3a219e
Create Date: 2024-12-10 10:06:41.903073

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80de0bf75e5d'
down_revision: Union[str, None] = '8939dc3a219e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('passages', 'agent_id',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('passages', 'agent_id',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###
