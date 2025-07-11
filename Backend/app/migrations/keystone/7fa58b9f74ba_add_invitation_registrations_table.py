"""add invitation registrations table

Revision ID: 7fa58b9f74ba
Revises: 084a21914bc7
Create Date: 2024-12-05 23:07:58.904158

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7fa58b9f74ba"
down_revision = "084a21914bc7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "invitation_registrations",
        sa.Column("invitation_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["invitation_id"], ["invitation.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("invitation_id", "user_id"),
    )
    op.drop_constraint("user_invitation_id_fkey", "user", type_="foreignkey")
    op.drop_column("user", "invitation_id")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user",
        sa.Column("invitation_id", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "user_invitation_id_fkey", "user", "invitation", ["invitation_id"], ["id"]
    )
    op.drop_table("invitation_registrations")
    # ### end Alembic commands ###
