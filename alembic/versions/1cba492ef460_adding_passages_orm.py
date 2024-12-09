"""adding Passages ORM

Revision ID: 1cba492ef460
Revises: 95badb46fdf9
Create Date: 2024-12-07 14:21:30.327034

"""
from typing import Sequence, Union

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from letta.metadata import EmbeddingConfigColumn

# revision identifiers, used by Alembic.
revision: str = '1cba492ef460'
down_revision: Union[str, None] = '95badb46fdf9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('passages_legacy',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('file_id', sa.String(), nullable=True),
    sa.Column('agent_id', sa.String(), nullable=True),
    sa.Column('source_id', sa.String(), nullable=True),
    sa.Column('embedding', Vector(dim=4096), nullable=True),
    sa.Column('embedding_config', EmbeddingConfigColumn(), nullable=True),
    sa.Column('metadata_', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('passage_idx_user_legacy', 'passages_legacy', ['user_id', 'agent_id', 'file_id'], unique=False)
    op.add_column('passages', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('passages', sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False))
    op.add_column('passages', sa.Column('_created_by_id', sa.String(), nullable=True))
    op.add_column('passages', sa.Column('_last_updated_by_id', sa.String(), nullable=True))
    op.add_column('passages', sa.Column('organization_id', sa.String(), nullable=False))
    op.alter_column('passages', 'text',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('passages', 'embedding_config',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=False)
    op.alter_column('passages', 'metadata_',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=False)
    op.alter_column('passages', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=False)
    op.alter_column('passages', 'agent_id',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.drop_index('passage_idx_user', table_name='passages')
    op.create_foreign_key(None, 'passages', 'files', ['file_id'], ['id'])
    op.create_foreign_key(None, 'passages', 'organizations', ['organization_id'], ['id'])
    op.create_foreign_key(None, 'passages', 'agents', ['agent_id'], ['id'])
    op.drop_column('passages', 'user_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('passages', sa.Column('user_id', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'passages', type_='foreignkey')
    op.drop_constraint(None, 'passages', type_='foreignkey')
    op.drop_constraint(None, 'passages', type_='foreignkey')
    op.create_index('passage_idx_user', 'passages', ['user_id', 'agent_id', 'file_id'], unique=False)
    op.alter_column('passages', 'agent_id',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('passages', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=True)
    op.alter_column('passages', 'metadata_',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=True)
    op.alter_column('passages', 'embedding_config',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=True)
    op.alter_column('passages', 'text',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.drop_column('passages', 'organization_id')
    op.drop_column('passages', '_last_updated_by_id')
    op.drop_column('passages', '_created_by_id')
    op.drop_column('passages', 'is_deleted')
    op.drop_column('passages', 'updated_at')
    op.drop_index('passage_idx_user_legacy', table_name='passages_legacy')
    op.drop_table('passages_legacy')
    # ### end Alembic commands ###