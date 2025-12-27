"""add foreign key to customer_id in conversations

Revision ID: 2025_06_21_9999
Revises: z123456789abc
Create Date: 2025-06-21 23:59:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2025_06_21_9999'
down_revision = 'z123456789abc'
branch_labels = None
depends_on = None

def upgrade():
    op.create_foreign_key(
        'fk_conversations_customer_id_user',
        'conversations', 'user',
        ['customer_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade():
    op.drop_constraint('fk_conversations_customer_id_user', 'conversations', type_='foreignkey') 