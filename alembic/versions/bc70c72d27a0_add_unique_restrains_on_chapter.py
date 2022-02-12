"""add unique restrains on chapter

Revision ID: bc70c72d27a0
Revises: 165c784b1613
Create Date: 2022-02-05 00:16:18.780786

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "bc70c72d27a0"
down_revision = "165c784b1613"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint("uq_chapter", "chapters", ["number", "project_id"])


def downgrade():
    op.drop_constraint("uq_chapter", "chapters", type_="unique")
