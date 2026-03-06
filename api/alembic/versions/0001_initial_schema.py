"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("url", sa.String(255), nullable=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("date_posted", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index("ix_jobs_id", "jobs", ["id"], unique=False)
    op.create_index("ix_jobs_title", "jobs", ["title"], unique=False)
    op.create_index("ix_jobs_url", "jobs", ["url"], unique=True)

    op.create_table(
        "last_sync",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_index("ix_jobs_url", table_name="jobs")
    op.drop_index("ix_jobs_title", table_name="jobs")
    op.drop_index("ix_jobs_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("last_sync")
