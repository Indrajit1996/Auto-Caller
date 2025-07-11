"""add is_active to group model

Revision ID: 0c85b04e328d
Revises: eefbd3f2312f
Create Date: 2024-12-14 06:39:50.596825

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0c85b04e328d"
down_revision = "eefbd3f2312f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("group", sa.Column("is_active", sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("group", "is_active")
    # ### end Alembic commands ###
