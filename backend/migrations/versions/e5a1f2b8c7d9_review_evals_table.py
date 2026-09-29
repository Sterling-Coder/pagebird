"""store QA reports in the database

Revision ID: e5a1f2b8c7d9
Revises: d4e7a1c9b2f3
Create Date: 2026-09-30

QA reports were cached as files on the container's disk, so every redeploy
erased them and the Files list showed no scores again.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e5a1f2b8c7d9'
down_revision: Union[str, Sequence[str], None] = 'd4e7a1c9b2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        create table if not exists public.review_evals (
            job_id text primary key references public.review_jobs(id) on delete cascade,
            report_json text not null,
            updated_at double precision not null
        );
        alter table public.review_evals enable row level security;
        """
    )


def downgrade() -> None:
    op.execute("drop table if exists public.review_evals;")
