"""profile avatars: avatar_url column and the public avatars bucket

Revision ID: f3a9c2d1e8b4
Revises: e5a1f2b8c7d9
Create Date: 2026-10-09

Profile pictures are uploaded by the API (service role) into a public
Supabase Storage bucket and the resulting public URL is kept on the profile
row, so the sidebar, Profile and Team pages can show it without a signed URL.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f3a9c2d1e8b4'
down_revision: Union[str, Sequence[str], None] = 'e5a1f2b8c7d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        alter table public.profiles
          add column if not exists avatar_url text;

        insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
        values ('avatars', 'avatars', true, 2097152,
                array['image/png', 'image/jpeg', 'image/webp', 'image/gif'])
        on conflict (id) do nothing;
        """
    )


def downgrade() -> None:
    # The bucket is left in place: dropping it would require deleting every
    # uploaded picture first, and an unused empty bucket costs nothing.
    op.execute("alter table public.profiles drop column if exists avatar_url;")
