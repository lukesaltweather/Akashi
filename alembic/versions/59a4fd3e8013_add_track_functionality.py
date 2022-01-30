"""Add track functionality

Revision ID: 59a4fd3e8013
Revises: 
Create Date: 2022-01-30 16:58:22.418140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59a4fd3e8013'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'monitorrequest',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('chapter_id', sa.Integer, sa.ForeignKey("chapters.id")),
        sa.Column('project_id', sa.Integer, sa.ForeignKey("projects.id")),
        sa.Column('staff_id',sa.Integer,  sa.ForeignKey("staff.id"), nullable=False),
    )


def downgrade():
    op.drop_table('monitorrequest')
