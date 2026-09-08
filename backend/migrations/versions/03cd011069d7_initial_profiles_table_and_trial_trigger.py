"""initial profiles table and trial trigger

Revision ID: 03cd011069d7
Revises:
Create Date: 2026-09-08 16:16:15.984355

Raw SQL rather than SQLAlchemy op.create_table(...): the trigger function
and RLS policy below have no ORM equivalent, and there's no SQLAlchemy model
layer in this app (Supabase is accessed via its REST API elsewhere, not a
direct DB connection) — a single op.execute() keeps the migration a 1:1 copy
of what actually runs, instead of splitting it across table-DSL + raw SQL.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '03cd011069d7'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        create table if not exists public.profiles (
          id uuid primary key references auth.users (id) on delete cascade,
          email text,
          trial_ends_at timestamptz not null,
          created_at timestamptz not null default now()
        );

        alter table public.profiles enable row level security;

        drop policy if exists "profiles are readable by their owner" on public.profiles;
        create policy "profiles are readable by their owner"
          on public.profiles for select
          using (auth.uid() = id);

        create or replace function public.handle_new_user()
        returns trigger
        language plpgsql
        security definer set search_path = public
        as $$
        begin
          insert into public.profiles (id, email, trial_ends_at)
          values (new.id, new.email, now() + interval '14 days');
          return new;
        end;
        $$;

        drop trigger if exists on_auth_user_created on auth.users;
        create trigger on_auth_user_created
          after insert on auth.users
          for each row execute function public.handle_new_user();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        drop trigger if exists on_auth_user_created on auth.users;
        drop function if exists public.handle_new_user();
        drop policy if exists "profiles are readable by their owner" on public.profiles;
        drop table if exists public.profiles;
        """
    )
