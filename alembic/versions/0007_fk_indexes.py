"""Add FK constraints and composite indexes for data integrity and query performance.

- review_queue.user_id -> users.id (SET NULL on delete)
- agent_calls.user_id  -> users.id (RESTRICT on delete)
- Composite index: agent_calls(user_id, created_at)
- Composite index: review_queue(status, created_at)
- Index: rag_query_logs(created_at)

Revision ID: 0007_fk_indexes
Revises: 0006_review_queue
Create Date: 2026-05-10
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0007_fk_indexes"
down_revision = "0006_review_queue"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- FK: review_queue.user_id -> users.id (SET NULL so user deletion is allowed) ---
    op.create_foreign_key(
        "fk_review_queue_user_id",
        "review_queue",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- FK: agent_calls.user_id -> users.id (RESTRICT to protect call history) ---
    op.create_foreign_key(
        "fk_agent_calls_user_id",
        "agent_calls",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # --- Composite index: agent_calls(user_id, created_at) ---
    op.create_index(
        "ix_agent_calls_user_id_created_at",
        "agent_calls",
        ["user_id", "created_at"],
    )

    # --- Composite index: review_queue(status, created_at) ---
    op.create_index(
        "ix_review_queue_status_created_at",
        "review_queue",
        ["status", "created_at"],
    )

    # --- Index: rag_query_logs(created_at) for time-series queries ---
    op.create_index(
        "ix_rag_query_logs_created_at",
        "rag_query_logs",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_rag_query_logs_created_at", table_name="rag_query_logs")
    op.drop_index("ix_review_queue_status_created_at", table_name="review_queue")
    op.drop_index("ix_agent_calls_user_id_created_at", table_name="agent_calls")
    op.drop_constraint("fk_agent_calls_user_id", "agent_calls", type_="foreignkey")
    op.drop_constraint("fk_review_queue_user_id", "review_queue", type_="foreignkey")
