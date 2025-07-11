"""drop password reset table

Revision ID: 8bf5c4da947b
Revises: 0dc635fc8cf0
Create Date: 2024-11-13 17:16:23.714643

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8bf5c4da947b"
down_revision = "0dc635fc8cf0"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("password_reset")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "password_reset",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("token", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "expires", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.Column("email_status_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "updated_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["email_status_id"],
            ["email_status.id"],
            name="password_reset_email_status_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name="password_reset_user_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id", name="password_reset_pkey"),
    )
    # ### end Alembic commands ###
