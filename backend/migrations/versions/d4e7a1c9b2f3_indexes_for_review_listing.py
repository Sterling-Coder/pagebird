"""indexes for review listing queries

Revision ID: d4e7a1c9b2f3
Revises: c8b3cee68ae7
Create Date: 2026-09-30

Project/folder/file listings filter review_jobs by created_by, project_id and
folder_id, and review_folders by project_id; none were indexed.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd4e7a1c9b2f3'
down_revision: Union[str, Sequence[str], None] = 'c8b3cee68ae7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("create index if not exists idx_review_jobs_created_by on public.review_jobs (created_by, created_at desc);")
    op.execute("create index if not exists idx_review_jobs_project_folder on public.review_jobs (project_id, folder_id);")
    op.execute("create index if not exists idx_review_folders_project_parent on public.review_folders (project_id, parent_folder_id);")
    op.execute("create index if not exists idx_review_projects_created_by on public.review_projects (created_by);")


def downgrade() -> None:
    op.execute("drop index if exists public.idx_review_projects_created_by;")
    op.execute("drop index if exists public.idx_review_folders_project_parent;")
    op.execute("drop index if exists public.idx_review_jobs_project_folder;")
    op.execute("drop index if exists public.idx_review_jobs_created_by;")
