"""add status to team_members for consent-gated invites

Revision ID: 1bb6d4c11844
Revises: a8ba1764d534
Create Date: 2026-09-08

Fixes a critical bug: invites used to grant access immediately, so
anyone could add an existing user to their "team" by email alone —
with the (also removed) bidirectional grant, the inviter instantly got
read access to the invitee's own private projects, with zero consent.

Now a row starts 'pending' and only counts toward access once the
invitee explicitly accepts it themselves.
"""
from typing import Sequence, Union

from alembic import op


revision: str = '1bb6d4c11844'
down_revision: Union[str, Sequence[str], None] = 'a8ba1764d534'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        alter table public.team_members
          add column if not exists status text not null default 'pending';

        alter table public.team_members
          drop constraint if exists team_members_status_check;
        alter table public.team_members
          add constraint team_members_status_check check (status in ('pending', 'accepted'));

        drop policy if exists "team members are readable by owner or member" on public.team_members;
        create policy "team members are readable by owner or member"
          on public.team_members for select
          using (auth.uid() = owner_id or auth.uid() = member_id);
        """
    )


def downgrade() -> None:
    op.execute("alter table public.team_members drop column if exists status;")
