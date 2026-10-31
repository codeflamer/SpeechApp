-- S01: one profile row per auth user. Later cards add learner fields (S03: L1, goal mode, voice).

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

-- Learners can read only their own profile. Rows are created by the trigger below,
-- so there is no insert policy; update/delete policies arrive with the cards that need them.
create policy "profiles: read own row"
  on public.profiles for select
  to authenticated
  using ((select auth.uid()) = id);

-- Create the profile when a user signs up. security definer so it can write past RLS;
-- search_path is pinned so the function can't be hijacked by objects in other schemas.
create function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id, email) values (new.id, new.email);
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
