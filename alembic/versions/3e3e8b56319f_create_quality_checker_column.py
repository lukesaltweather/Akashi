"""create quality checker column

Revision ID: 3e3e8b56319f
Revises: 7efd4129b076
Create Date: 2023-02-12 17:00:50.099313

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3e3e8b56319f"
down_revision = "7efd4129b076"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "chapters",
        sa.Column(
            "qualitychecker_id", sa.Integer, sa.ForeignKey("staff.id"), nullable=True
        ),
    )
    op.add_column("chapters", sa.Column("link_qc", sa.String, nullable=True))


def downgrade():
    op.drop_column("chapters", "qualitychecker")
