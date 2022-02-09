"""add notes revision

Revision ID: 165c784b1613
Revises: 59a4fd3e8013
Create Date: 2022-02-05 00:16:01.698750

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "165c784b1613"
down_revision = "59a4fd3e8013"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "note",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "chapter_id", sa.Integer, sa.ForeignKey("chapters.id"), nullable=False
        ),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("author_id", sa.Integer, sa.ForeignKey("staff.id"), nullable=False),
        sa.Column("created_on", sa.DateTime, default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("note")
