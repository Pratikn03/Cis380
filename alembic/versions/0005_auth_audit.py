"""Add auth_audit table for security events.

Revision ID: 0005_auth_audit
Revises: 0004_agent_calls
Create Date: 2026-04-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0005_auth_audit"
down_revision = "0004_agent_calls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_audit",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=128), nullable=True, index=True),
        sa.Column("username", sa.String(length=256), nullable=True),
        sa.Column(
            "event_type",
            sa.String(length=32),
            nullable=False,
            index=True,
        ),  # login_success | login_failure | logout | refresh | role_change | mfa_enroll | mfa_verify
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("auth_audit")
