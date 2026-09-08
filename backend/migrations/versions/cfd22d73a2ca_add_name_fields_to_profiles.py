"""add name fields to profiles

Revision ID: cfd22d73a2ca
Revises: 1bb6d4c11844
Create Date: 2026-09-08

Signup now collects first/last name (passed as auth.users metadata);
this stores them on the profile row so the rest of the app can read a
display name without re-parsing metadata every time.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'cfd22d73a2ca'
down_revision: Union[str, Sequence[str], None] = '1bb6d4c11844'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        alter table public.profiles
          add column if not exists first_name text,
          add column if not exists last_name text,
          add column if not exists full_name text;

        create or replace function public.handle_new_user()
        returns trigger
        language plpgsql
        security definer set search_path = public
        as $$
        begin
          insert into public.profiles (id, email, trial_ends_at, first_name, last_name, full_name)
          values (
            new.id,
            new.email,
            now() + interval '14 days',
            new.raw_user_meta_data ->> 'first_name',
            new.raw_user_meta_data ->> 'last_name',
            new.raw_user_meta_data ->> 'full_name'
          );
          return new;
        end;
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
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

        alter table public.profiles
          drop column if exists first_name,
          drop column if exists last_name,
          drop column if exists full_name;
        """
    )
