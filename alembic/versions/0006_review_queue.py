"""Add review_queue for active-learning escalations.

Revision ID: 0006_review_queue
Revises: 0005_auth_audit
Create Date: 2026-04-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006_review_queue"
down_revision = "0005_auth_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review_queue",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trace_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("session_id", sa.String(length=64), nullable=True, index=True),
        sa.Column("user_id", sa.String(length=128), nullable=True, index=True),
        sa.Column("intent", sa.String(length=32), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("model_answer", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="pending",
            index=True,
        ),  # pending | labeled | discarded
        sa.Column("label", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("review_queue")
