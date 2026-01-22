"""init

Revision ID: 0001_init
Revises:
Create Date: 2026-01-21 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("role_id", sa.String(), sa.ForeignKey("roles.id"), primary_key=True),
    )

    op.create_table(
        "datasets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("license", sa.String(), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("description", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_datasets_name", "datasets", ["name"], unique=True)

    op.create_table(
        "documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default=sa.text("'upload'")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_documents_filename", "documents", ["filename"])
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"])

    op.create_table(
        "rag_chunks",
        sa.Column("chunk_id", sa.String(), primary_key=True),
        sa.Column("doc_id", sa.String(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.create_index("ix_rag_chunks_doc_id", "rag_chunks", ["doc_id"])

    op.create_table(
        "rag_query_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("top_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("avg_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_type", sa.String(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("artifacts", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_runs_run_type", "runs", ["run_type"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("task_id", sa.String(), nullable=True),
        sa.Column("job_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("progress", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("message", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_jobs_job_type", "jobs", ["job_type"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("target", sa.String(), nullable=False, server_default=sa.text("''")),
        sa.Column("meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])

    op.create_table(
        "incidents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("incident_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False, server_default=sa.text("'low'")),
        sa.Column("description", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_incidents_incident_type", "incidents", ["incident_type"])


def downgrade() -> None:
    op.drop_index("ix_incidents_incident_type", table_name="incidents")
    op.drop_table("incidents")

    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_job_type", table_name="jobs")
    op.drop_table("jobs")

    op.drop_index("ix_runs_run_type", table_name="runs")
    op.drop_table("runs")

    op.drop_table("rag_query_logs")

    op.drop_index("ix_rag_chunks_doc_id", table_name="rag_chunks")
    op.drop_table("rag_chunks")

    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.drop_index("ix_documents_filename", table_name="documents")
    op.drop_table("documents")

    op.drop_index("ix_datasets_name", table_name="datasets")
    op.drop_table("datasets")

    op.drop_table("user_roles")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_table("roles")
