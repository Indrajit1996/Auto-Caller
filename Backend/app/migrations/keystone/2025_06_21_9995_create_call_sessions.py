"""create call_sessions and call_interactions tables

Revision ID: 2025_06_21_9996
Revises: 2025_06_21_9997
Create Date: 2025-06-21 12:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg


# revision identifiers, used by Alembic.
revision = '2025_06_21_9995'
down_revision = '2025_06_21_9997'
branch_labels = None
depends_on = None


def upgrade():
    # Create call_sessions table
    op.create_table(
        'call_sessions',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('call_sid', sa.String(50), unique=True, index=True, nullable=False),
        sa.Column('twilio_call_sid', sa.String(50), unique=True, index=True, nullable=True),
        sa.Column('from_number', sa.String(20), nullable=False),
        sa.Column('to_number', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='initiated'),
        sa.Column('duration', sa.Integer, nullable=False, default=0),
        sa.Column('start_time', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('end_time', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('initial_message', sa.Text, nullable=True),
        sa.Column('voice_id', sa.String(50), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    # Create call_interactions table
    op.create_table(
        'call_interactions',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('call_session_id', sa.String(36), sa.ForeignKey('call_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('interaction_type', sa.String(20), nullable=False),
        sa.Column('sequence_number', sa.Integer, nullable=False, default=0),
        sa.Column('speech_result', sa.Text, nullable=True),
        sa.Column('speech_confidence', sa.Float, nullable=True),
        sa.Column('speech_language', sa.String(10), nullable=True),
        sa.Column('recording_sid', sa.String(50), nullable=True),
        sa.Column('recording_url', sa.String(500), nullable=True),
        sa.Column('recording_duration', sa.Integer, nullable=True),
        sa.Column('s3_audio_url', sa.String(500), nullable=True),
        sa.Column('transcription_text', sa.Text, nullable=True),
        sa.Column('transcription_status', sa.String(20), nullable=True),
        sa.Column('transcription_source', sa.String(20), nullable=True),
        sa.Column('transcription_confidence', sa.Float, nullable=True),
        sa.Column('system_response', sa.Text, nullable=True),
        sa.Column('system_audio_url', sa.String(500), nullable=True),
        sa.Column('processing_time', sa.Float, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    # Add indexes
    op.create_index('idx_call_interactions_call_session_id', 'call_interactions', ['call_session_id'])
    op.create_index('idx_call_interactions_created_at', 'call_interactions', ['created_at'])


def downgrade():
    op.drop_index('idx_call_interactions_created_at', table_name='call_interactions')
    op.drop_index('idx_call_interactions_call_session_id', table_name='call_interactions')
    op.drop_table('call_interactions')
    op.drop_table('call_sessions') 