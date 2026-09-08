"""team_members table for workspace invites

Revision ID: a8ba1764d534
Revises: 03cd011069d7
Create Date: 2026-09-08

A member row grants member_id full access to owner_id's projects/jobs —
"invite a teammate" means they see and can translate everything in your
workspace, same as you. The backend (service role) is the only writer;
regular users can only read rows involving themselves.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a8ba1764d534'
down_revision: Union[str, Sequence[str], None] = '03cd011069d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        create table if not exists public.team_members (
          owner_id uuid not null references auth.users (id) on delete cascade,
          member_id uuid not null references auth.users (id) on delete cascade,
          email text not null,
          created_at timestamptz not null default now(),
          primary key (owner_id, member_id)
        );

        alter table public.team_members enable row level security;

        drop policy if exists "team members are readable by owner or member" on public.team_members;
        create policy "team members are readable by owner or member"
          on public.team_members for select
          using (auth.uid() = owner_id or auth.uid() = member_id);
        """
    )


def downgrade() -> None:
    op.execute("drop table if exists public.team_members;")
