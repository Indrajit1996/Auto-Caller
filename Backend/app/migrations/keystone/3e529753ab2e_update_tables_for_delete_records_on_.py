"""Update tables for delete records on delete user

Revision ID: 3e529753ab2e
Revises: f10793afdf57
Create Date: 2024-12-05 23:13:40.264235

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "3e529753ab2e"
down_revision = "f10793afdf57"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("notification_user_id_fkey", "notification", type_="foreignkey")
    op.create_foreign_key(
        None, "notification", "user", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.drop_constraint("user_groups_group_id_fkey", "user_groups", type_="foreignkey")
    op.drop_constraint("user_groups_user_id_fkey", "user_groups", type_="foreignkey")
    op.create_foreign_key(
        None, "user_groups", "user", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        None, "user_groups", "group", ["group_id"], ["id"], ondelete="CASCADE"
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "user_groups", type_="foreignkey")
    op.drop_constraint(None, "user_groups", type_="foreignkey")
    op.create_foreign_key(
        "user_groups_user_id_fkey", "user_groups", "user", ["user_id"], ["id"]
    )
    op.create_foreign_key(
        "user_groups_group_id_fkey", "user_groups", "group", ["group_id"], ["id"]
    )
    op.drop_constraint(None, "notification", type_="foreignkey")
    op.create_foreign_key(
        "notification_user_id_fkey", "notification", "user", ["user_id"], ["id"]
    )
    # ### end Alembic commands ###
