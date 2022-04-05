"""Add Project.mangadex_id

Revision ID: 7efd4129b076
Revises: bc70c72d27a0
Create Date: 2022-04-05 12:20:38.656704

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7efd4129b076"
down_revision = "bc70c72d27a0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("projects", sa.Column("mangadex_id", sa.String(), nullable=True))


def downgrade():
    op.drop_column("projects", "mangadex_id")
