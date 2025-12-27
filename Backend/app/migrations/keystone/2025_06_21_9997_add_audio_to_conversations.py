"""add audio column to conversations table

Revision ID: 2025_06_21_9999
Revises: z123456789abc
Create Date: 2025-06-21 12:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_06_21_9997'
down_revision = '2025_06_21_9999'
branch_labels = None
depends_on = None


def upgrade():
    # Add audio column to conversations table
    op.add_column('conversations', sa.Column('audio', sa.Text(), nullable=True))


def downgrade():
    # Remove audio column from conversations table
    op.drop_column('conversations', 'audio') 