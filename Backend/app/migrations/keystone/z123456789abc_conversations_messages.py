"""create conversations and messages tables for 1:1 chat

Revision ID: z123456789abc
Revises: f10793afdf57
Create Date: 2025-06-21 06:45:00.000000
"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg


# revision identifiers, used by Alembic.
revision = 'z123456789abc'
down_revision = 'f10793afdf57'
branch_labels = None
depends_on = None


def upgrade():
    # Ensure pgcrypto extension is enabled for gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', pg.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('customer_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('agent_id', 'customer_id', name='uq_agent_customer')
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', pg.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_role', sa.String(10), nullable=False),  # 'agent' or 'customer'
        sa.Column('message_type', sa.String(50), nullable=False), # 'text', 'audio', etc.
        sa.Column('text_content', sa.Text, nullable=True),
        sa.Column('audio_url', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    # Add indexes
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])


def downgrade():
    op.drop_index('idx_messages_created_at', table_name='messages')
    op.drop_index('idx_messages_conversation_id', table_name='messages')
    op.drop_table('messages')
    op.drop_table('conversations')
