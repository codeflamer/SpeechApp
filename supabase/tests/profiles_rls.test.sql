-- S01: the signup trigger creates a profile, and RLS lets each learner read only their own.
begin;
select plan(5);

insert into auth.users (id, email)
values
  ('11111111-1111-1111-1111-111111111111', 'ada@example.com'),
  ('22222222-2222-2222-2222-222222222222', 'kwame@example.com');

select is(
  (select count(*)::int from public.profiles where id in (
    '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222')),
  2,
  'signup trigger creates one profile per new user'
);

-- Act as Ada.
set local role authenticated;
select set_config('request.jwt.claims', '{"sub":"11111111-1111-1111-1111-111111111111","role":"authenticated"}', true);

select is((select count(*)::int from public.profiles), 1, 'a learner sees exactly one profile');
select is((select email from public.profiles), 'ada@example.com', 'and it is their own');
select is(
  (select count(*)::int from public.profiles where id = '22222222-2222-2222-2222-222222222222'),
  0,
  'a learner cannot read another learner''s profile'
);

-- Signed-out visitors see nothing.
set local role anon;
select is((select count(*)::int from public.profiles), 0, 'signed-out visitors cannot read profiles');

select * from finish();
rollback;
