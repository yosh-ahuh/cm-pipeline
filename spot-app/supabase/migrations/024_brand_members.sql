-- 024_brand_members.sql — ブランド単位のアクセス範囲（招待・メンバー）。docs/brand-plan-limits-proposal.md §12。
--   モデル: 席（plan.seats）は従来どおり「アカウント（org）で抱える実メンバー数」＝ org_members の owner/member 数（変更なし）。
--   追加: brand_members = メンバーごとの「見える/作れるブランド」の範囲。
--     ・行が 1 つも無いメンバー＝アカウント内の全ブランドにアクセス（従来どおり）。
--     ・行があるメンバー＝その行のブランドだけ。オーナーは常に全ブランド。viewer も同じ範囲規則（読取のみ）。
--   招待は org_invites.brand_ids（null=全ブランド）で範囲を指定でき、accept_invite が範囲を書き込む。
--   RLS: brands / projects / collections / generations / renders / jobs に brand_visible() を追加（追加条件のみ・緩める方向の変更なし）。
--   前提: 006〜023 適用済み。冪等。

-- ------------------------------------------------------------ 1) テーブル・列
create table if not exists public.brand_members (
  brand_id uuid not null references public.brands(id) on delete cascade,
  user_id  uuid not null references auth.users(id) on delete cascade,
  added_at timestamptz not null default now(),
  primary key (brand_id, user_id)
);
create index if not exists brand_members_user_idx on public.brand_members(user_id);
alter table public.org_invites add column if not exists brand_ids uuid[];

-- ------------------------------------------------------------ 2) 可視性ヘルパ
-- そのユーザーが org 内で範囲指定されているブランド（未指定なら null）
create or replace function public.brand_scope(p_org uuid)
returns uuid[] language sql stable security definer set search_path = public as $$
  select nullif(array_agg(bm.brand_id), '{}')
  from public.brand_members bm join public.brands b on b.id = bm.brand_id
  where b.org_id = p_org and bm.user_id = auth.uid();
$$;
grant execute on function public.brand_scope(uuid) to authenticated;

create or replace function public.brand_visible(p_brand uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select p_brand is null                                   -- 旧データ（brand 未設定）は従来どおり
      or exists (
        select 1 from public.brands b
        where b.id = p_brand and (
              public.is_owner(b.org_id)
           or not exists (select 1 from public.brand_members bm join public.brands b2 on b2.id = bm.brand_id
                          where b2.org_id = b.org_id and bm.user_id = auth.uid())
           or exists (select 1 from public.brand_members bm where bm.brand_id = p_brand and bm.user_id = auth.uid())));
$$;
grant execute on function public.brand_visible(uuid) to authenticated;

create or replace function public.project_visible(p_project uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select p_project is null or exists (select 1 from public.projects p where p.id = p_project and public.brand_visible(p.brand_id));
$$;
grant execute on function public.project_visible(uuid) to authenticated;

-- ------------------------------------------------------------ 3) RLS（追加条件）
alter table public.brand_members enable row level security;
drop policy if exists "member reads brand_members" on public.brand_members;
create policy "member reads brand_members" on public.brand_members for select
  using (exists (select 1 from public.brands b where b.id = brand_id and public.is_member(b.org_id)));
-- 書込は RPC（security definer）のみ

drop policy if exists "member reads brands" on public.brands;
create policy "member reads brands" on public.brands for select
  using (public.is_member(org_id) and public.brand_visible(id));

drop policy if exists "writer writes projects" on public.projects;   -- 010 以前の粗い FOR ALL が残っていれば除去
drop policy if exists "member reads projects" on public.projects;
create policy "member reads projects" on public.projects for select
  using (public.is_member(org_id) and public.brand_visible(brand_id));
drop policy if exists "writer inserts projects" on public.projects;
create policy "writer inserts projects" on public.projects for insert
  with check (public.can_write(org_id) and public.brand_visible(brand_id));
drop policy if exists "writer updates projects" on public.projects;
create policy "writer updates projects" on public.projects for update
  using (public.can_write(org_id) and public.brand_visible(brand_id))
  with check (public.can_write(org_id) and public.brand_visible(brand_id));
drop policy if exists "owner deletes projects" on public.projects;
create policy "owner deletes projects" on public.projects for delete
  using (public.is_owner(org_id));

drop policy if exists "member reads collections" on public.collections;
create policy "member reads collections" on public.collections for select
  using (public.is_member(org_id) and public.brand_visible(brand_id));
drop policy if exists "writer writes collections" on public.collections;
create policy "writer writes collections" on public.collections for all
  using (public.can_write(org_id) and public.brand_visible(brand_id))
  with check (public.can_write(org_id) and public.brand_visible(brand_id));

drop policy if exists "member reads generations" on public.generations;
create policy "member reads generations" on public.generations for select
  using (public.is_member(org_id) and public.project_visible(project_id));
drop policy if exists "writer writes generations" on public.generations;
create policy "writer writes generations" on public.generations for all
  using (public.can_write(org_id) and public.project_visible(project_id))
  with check (public.can_write(org_id) and public.project_visible(project_id));

drop policy if exists "member reads renders" on public.renders;
create policy "member reads renders" on public.renders for select
  using (public.is_member(org_id) and public.project_visible(project_id));
drop policy if exists "writer writes renders" on public.renders;
create policy "writer writes renders" on public.renders for all
  using (public.can_write(org_id) and public.project_visible(project_id))
  with check (public.can_write(org_id) and public.project_visible(project_id));

drop policy if exists "member reads jobs" on public.jobs;
create policy "member reads jobs" on public.jobs for select
  using (public.is_member(org_id) and public.project_visible(project_id));
drop policy if exists "writer writes jobs" on public.jobs;
create policy "writer writes jobs" on public.jobs for all
  using (public.can_write(org_id) and public.project_visible(project_id))
  with check (public.can_write(org_id) and public.project_visible(project_id));

-- ------------------------------------------------------------ 4) 招待（範囲付き）
drop function if exists public.create_invite(uuid, text, text);
create or replace function public.create_invite(p_org uuid, p_email text default null, p_role text default 'member', p_brand_ids uuid[] default null)
returns text language plpgsql security definer set search_path = public as $$
declare v_token text; v_ids uuid[];
begin
  if public.member_role(p_org) <> 'owner' then
    raise exception 'only owner can invite' using errcode = '42501';
  end if;
  if p_role not in ('member','viewer') then
    raise exception 'invalid role' using errcode = '22023';
  end if;
  -- 範囲: この org のブランドだけを残す。空なら null（=全ブランド）
  select nullif(array_agg(b.id), '{}') into v_ids
    from public.brands b where b.org_id = p_org and p_brand_ids is not null and b.id = any(p_brand_ids);
  v_token := replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', '');
  insert into public.org_invites (org_id, email, role, token, invited_by, brand_ids)
  values (p_org, nullif(btrim(lower(p_email)), ''), p_role, v_token, auth.uid(), v_ids);
  return v_token;
end; $$;
grant execute on function public.create_invite(uuid, text, text, uuid[]) to authenticated;

drop function if exists public.get_invite(text);
create or replace function public.get_invite(p_token text)
returns table(org_id uuid, org_name text, role text, expired boolean, accepted boolean, brand_names text[])
language sql security definer stable set search_path = public as $$
  select i.org_id, o.name, i.role, (i.expires_at < now()), (i.accepted_at is not null),
         (select array_agg(b.name order by b.created_at) from public.brands b where i.brand_ids is not null and b.id = any(i.brand_ids))
  from public.org_invites i join public.organizations o on o.id = i.org_id
  where i.token = p_token;
$$;
grant execute on function public.get_invite(text) to authenticated, anon;

create or replace function public.accept_invite(p_token text)
returns uuid language plpgsql security definer set search_path = public as $$
declare v_inv public.org_invites; v_seats int; v_used int;
begin
  select * into v_inv from public.org_invites where token = p_token for update;
  if v_inv.id is null then raise exception 'invite not found' using errcode = 'P0002'; end if;
  if v_inv.accepted_at is not null then raise exception 'invite already used' using errcode = '22023'; end if;
  if v_inv.expires_at < now() then raise exception 'invite expired' using errcode = '22023'; end if;

  -- 席: owner/member はアカウント全体のユニーク人数で数える（ブランドをいくつ跨いでも 1 席）。viewer は無制限。
  if v_inv.role <> 'viewer' and not exists (select 1 from public.org_members where org_id = v_inv.org_id and user_id = auth.uid() and role in ('owner','member')) then
    select pl.seats into v_seats from public.organizations o join public.plans pl on pl.id = o.plan where o.id = v_inv.org_id;
    if coalesce(v_seats, 1) <> 0 then
      select count(*) into v_used from public.org_members where org_id = v_inv.org_id and role in ('owner','member');
      if v_used >= v_seats then
        raise exception 'seat limit reached' using errcode = '53400';
      end if;
    end if;
  end if;

  insert into public.org_members (org_id, user_id, role)
  values (v_inv.org_id, auth.uid(), v_inv.role)
  on conflict (org_id, user_id) do update set role = excluded.role;

  -- ブランド範囲: 招待に指定があればそれに置き換える（無指定＝全ブランド＝範囲行を消す）
  delete from public.brand_members bm using public.brands b
    where bm.brand_id = b.id and b.org_id = v_inv.org_id and bm.user_id = auth.uid();
  if v_inv.brand_ids is not null then
    insert into public.brand_members (brand_id, user_id)
    select b.id, auth.uid() from public.brands b where b.org_id = v_inv.org_id and b.id = any(v_inv.brand_ids)
    on conflict do nothing;
  end if;

  update public.org_invites set accepted_at = now() where id = v_inv.id;
  return v_inv.org_id;
end; $$;
grant execute on function public.accept_invite(text) to authenticated;

-- ------------------------------------------------------------ 5) メンバーの範囲変更（オーナー）・削除時の掃除・一覧
create or replace function public.set_member_brands(p_org uuid, p_user uuid, p_brand_ids uuid[] default null)
returns void language plpgsql security definer set search_path = public as $$
begin
  if public.member_role(p_org) <> 'owner' then
    raise exception 'only owner can change access' using errcode = '42501';
  end if;
  if not exists (select 1 from public.org_members where org_id = p_org and user_id = p_user) then
    raise exception 'not a member' using errcode = 'P0002';
  end if;
  if (select role from public.org_members where org_id = p_org and user_id = p_user) = 'owner' then
    return;   -- オーナーは常に全ブランド
  end if;
  delete from public.brand_members bm using public.brands b
    where bm.brand_id = b.id and b.org_id = p_org and bm.user_id = p_user;
  if p_brand_ids is not null and array_length(p_brand_ids, 1) > 0 then
    insert into public.brand_members (brand_id, user_id)
    select b.id, p_user from public.brands b where b.org_id = p_org and b.id = any(p_brand_ids)
    on conflict do nothing;
  end if;
end; $$;
grant execute on function public.set_member_brands(uuid, uuid, uuid[]) to authenticated;

create or replace function public.remove_member(p_org uuid, p_user uuid)
returns void language plpgsql security definer set search_path = public as $$
begin
  if public.member_role(p_org) <> 'owner' then
    raise exception 'only owner can remove members' using errcode = '42501';
  end if;
  if (select role from public.org_members where org_id = p_org and user_id = p_user) = 'owner'
     and (select count(*) from public.org_members where org_id = p_org and role = 'owner') <= 1 then
    raise exception 'cannot remove the last owner' using errcode = '42501';
  end if;
  delete from public.brand_members bm using public.brands b
    where bm.brand_id = b.id and b.org_id = p_org and bm.user_id = p_user;
  delete from public.org_members where org_id = p_org and user_id = p_user;
end; $$;
grant execute on function public.remove_member(uuid, uuid) to authenticated;

drop function if exists public.list_members(uuid);
create or replace function public.list_members(p_org uuid)
returns table(user_id uuid, display_name text, email text, avatar text, role text, added_at timestamptz, brand_ids uuid[])
language sql security definer stable set search_path = public as $$
  select m.user_id,
         p.display_name,
         u.email::text as email,
         coalesce(nullif(p.avatar_url, ''), u.raw_user_meta_data->>'avatar_url', u.raw_user_meta_data->>'picture') as avatar,
         m.role,
         m.added_at,
         (select nullif(array_agg(bm.brand_id), '{}') from public.brand_members bm join public.brands b on b.id = bm.brand_id
           where b.org_id = p_org and bm.user_id = m.user_id) as brand_ids
  from public.org_members m
    left join public.profiles p on p.id = m.user_id
    left join auth.users    u on u.id = m.user_id
  where m.org_id = p_org and public.is_member(p_org)
  order by (m.role = 'owner') desc, m.added_at;
$$;
grant execute on function public.list_members(uuid) to authenticated;
