"""Add agent_calls table for cost + latency telemetry.

Revision ID: 0004_agent_calls
Revises: 0003_user_totp
Create Date: 2026-04-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_agent_calls"
down_revision = "0003_user_totp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_calls",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trace_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("session_id", sa.String(length=64), nullable=True, index=True),
        sa.Column("user_id", sa.String(length=128), nullable=False, index=True),
        sa.Column("intent", sa.String(length=32), nullable=True),
        sa.Column("answer_source", sa.String(length=32), nullable=True),
        sa.Column("stop_reason", sa.String(length=32), nullable=True),
        sa.Column("tool_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_read_input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_creation_input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("agent_calls")
