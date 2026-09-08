-- Run once in the Supabase SQL editor (Project → SQL Editor → New query).
-- Creates a profiles table that mirrors auth.users, auto-starts a 14-day
-- trial on signup (password or Google — both go through auth.users insert),
-- and locks each row down to its own owner.

create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text,
  trial_ends_at timestamptz not null,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "profiles are readable by their owner"
  on public.profiles for select
  using (auth.uid() = id);

-- No insert/update/delete policies for regular users — profiles are
-- written only by the trigger below and read only by the service role
-- (used by the backend's trial check) or the owning user.

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
