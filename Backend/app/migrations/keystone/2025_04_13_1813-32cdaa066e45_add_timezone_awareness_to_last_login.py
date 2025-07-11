"""add timezone awareness to last_login

Revision ID: 32cdaa066e45
Revises: 5e8ac6e9ff0e
Create Date: 2025-04-13 18:13:40.429756+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "32cdaa066e45"
down_revision = "5e8ac6e9ff0e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "user",
        "last_login",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
    op.create_index(op.f("ix_user_last_login"), "user", ["last_login"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_user_last_login"), table_name="user")
    op.alter_column(
        "user",
        "last_login",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
    # ### end Alembic commands ###
