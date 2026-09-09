"""review store tables (projects, folders, jobs, segments)

Revision ID: b2b7a15b645c
Revises: cfd22d73a2ca
Create Date: 2026-09-09

Moves ReviewStore off local SQLite (babel_review.db) onto this same
Supabase Postgres database. Local SQLite lived on Railway's container
disk, which resets to empty on every redeploy — every project/job was
silently wiped each time the backend shipped. Same schema as the old
SQLite file, Postgres-flavored types (SERIAL instead of AUTOINCREMENT,
DOUBLE PRECISION instead of REAL for epoch-seconds timestamps).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b2b7a15b645c'
down_revision: Union[str, Sequence[str], None] = 'cfd22d73a2ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        create table if not exists public.review_projects (
            id text primary key,
            name text not null,
            job_type text not null default 'document',
            source_lang text,
            target_lang text,
            client text,
            vendor text,
            deadline double precision,
            status text not null default 'created',
            created_at double precision not null,
            created_by text
        );

        create table if not exists public.review_folders (
            id text primary key,
            project_id text not null references public.review_projects(id),
            name text not null,
            parent_folder_id text,
            created_at double precision not null
        );

        create table if not exists public.review_jobs (
            id text primary key,
            source text,
            output text,
            created_at double precision,
            meta_json text,
            original_filename text,
            file_hash text,
            file_size integer,
            duration_sec double precision,
            status text default 'complete',
            error text,
            project_id text,
            job_type text default 'document',
            folder_id text,
            created_by text
        );

        create table if not exists public.review_segments (
            job_id text not null,
            seg_id text not null,
            page integer,
            source text,
            target text,
            status text,
            disagreement integer,
            has_math_font integer,
            placeholders_json text,
            bbox_json text,
            notes_json text,
            approved integer,
            primary key (job_id, seg_id)
        );

        create table if not exists public.review_segment_events (
            id serial primary key,
            job_id text not null references public.review_jobs(id),
            seg_id text not null,
            action text not null,
            reviewer text not null default 'unknown',
            old_target text,
            new_target text,
            created_at double precision not null
        );

        create index if not exists idx_review_segment_events_job_seg
            on public.review_segment_events(job_id, seg_id);
        create index if not exists idx_review_segments_job_status
            on public.review_segments(job_id, status);

        -- RLS is enabled for consistency with the rest of this database, but
        -- these tables are only ever touched via the backend's service-role
        -- connection (direct Postgres, not the REST API), so no policies are
        -- needed beyond blocking the anon/authenticated roles entirely.
        alter table public.review_projects enable row level security;
        alter table public.review_folders enable row level security;
        alter table public.review_jobs enable row level security;
        alter table public.review_segments enable row level security;
        alter table public.review_segment_events enable row level security;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        drop table if exists public.review_segment_events;
        drop table if exists public.review_segments;
        drop table if exists public.review_jobs;
        drop table if exists public.review_folders;
        drop table if exists public.review_projects;
        """
    )
