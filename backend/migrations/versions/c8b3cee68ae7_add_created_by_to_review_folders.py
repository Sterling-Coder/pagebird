"""add created_by to review_folders

Revision ID: c8b3cee68ae7
Revises: b2b7a15b645c
Create Date: 2026-09-20

The Files table already shows "Created by" / "Created" for documents
(review_jobs.created_by) but folders never recorded who made them, so
that column always rendered blank for folder rows.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c8b3cee68ae7'
down_revision: Union[str, Sequence[str], None] = 'b2b7a15b645c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("alter table public.review_folders add column if not exists created_by text;")


def downgrade() -> None:
    op.execute("alter table public.review_folders drop column if exists created_by;")
