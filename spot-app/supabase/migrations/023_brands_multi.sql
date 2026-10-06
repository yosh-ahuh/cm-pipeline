-- 023_brands_multi.sql — 複数ブランド（アカウント＞ブランド＞コレクション＞動画）の実効化。
--   確定モデル（docs/brand-plan-limits-proposal.md §9/§13）: org＝アカウント、brands＝ブランド層（1ブランド＝1製品/クライアント）。
--   本ファイルで入るもの:
--     1) 既定ブランドの解決 default_brand(org) と、ブランド無し org への既定ブランド補完（バックフィル）
--     2) projects / collections の brand_id 自動補完（未指定なら既定ブランド）＋ 凍結ブランドへの書き込み拒否
--     3) create_brand: オーナー限定・plans.brands の上限（0=無制限・凍結中は数えない）
--     4) delete_brand: オーナー限定・最後の1ブランドは不可・中身は既定ブランドへ退避
--     5) set_brand_frozen: ダウングレード超過時の「読取のみ」凍結（解除は上限内のみ）
--     6) コレクション上限（plans.collections / ブランドあたり・0=無制限）
--     7) RLS: brands の INSERT/DELETE は RPC 経由のみ（UPDATE は can_write）
--   前提: 006〜022 適用済み（特に 021 の brands.frozen / collections.brand_id / plans.collections）。冪等。

-- ------------------------------------------------------------ 0) 021 の列が無い環境でも落ちないように（021 未適用の保険）
alter table public.plans       add column if not exists collections int not null default 0;
alter table public.brands      add column if not exists frozen boolean not null default false;
alter table public.collections add column if not exists brand_id uuid references public.brands(id) on delete cascade;
create index if not exists collections_brand_idx on public.collections(brand_id);
create index if not exists projects_brand_idx    on public.projects(brand_id);

-- ------------------------------------------------------------ 1) 既定ブランド（最古の非凍結 → 無ければ最古）
create or replace function public.default_brand(p_org uuid)
returns uuid language sql stable security definer set search_path = public as $$
  select coalesce(
    (select id from public.brands where org_id = p_org and not frozen order by created_at asc, id asc limit 1),
    (select id from public.brands where org_id = p_org order by created_at asc, id asc limit 1)
  );
$$;
grant execute on function public.default_brand(uuid) to authenticated;

-- ブランドを1つも持たない org に既定ブランド（org 名）を補完
insert into public.brands (org_id, name, assets)
select o.id, coalesce(nullif(btrim(o.name), ''), 'Brand'), '{}'::jsonb
from public.organizations o
where not exists (select 1 from public.brands b where b.org_id = o.id);

-- 新しい org に既定ブランドが無いときは「必要になった瞬間」に作る（サインアップ/オンボーディング/WS作成は各自ブランドを作るので二重化しない）
create or replace function public.ensure_default_brand(p_org uuid)
returns uuid language plpgsql security definer set search_path = public as $$
declare v_id uuid;
begin
  if not public.is_member(p_org) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  select id into v_id from public.brands where org_id = p_org order by created_at asc, id asc limit 1;
  if v_id is null then
    insert into public.brands (org_id, name, assets)
    select o.id, coalesce(nullif(btrim(o.name), ''), 'Brand'), '{}'::jsonb from public.organizations o where o.id = p_org
    returning id into v_id;
  end if;
  return v_id;
end; $$;
grant execute on function public.ensure_default_brand(uuid) to authenticated;
drop trigger if exists organizations_default_brand on public.organizations;   -- 旧案（org INSERT トリガ）は二重作成するため採用しない
drop function if exists public.org_default_brand();

-- 既存データの紐付け（brand_id が空の動画/コレクション → その org の既定ブランド）
update public.projects p set brand_id = public.default_brand(p.org_id)
 where p.brand_id is null and p.org_id is not null;
update public.collections c set brand_id = public.default_brand(c.org_id)
 where c.brand_id is null;

-- ------------------------------------------------------------ 2) brand_id の自動補完＋凍結ブランドの書き込み拒否
create or replace function public.fill_brand_id()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.brand_id is null and new.org_id is not null then
    new.brand_id := public.default_brand(new.org_id);
    if new.brand_id is null then   -- ブランド未作成の org（サインアップ直後の個人アカウント等）→ 既定ブランドを作る
      insert into public.brands (org_id, name, assets)
      select o.id, coalesce(nullif(btrim(o.name), ''), 'Brand'), '{}'::jsonb from public.organizations o where o.id = new.org_id
      returning id into new.brand_id;
    end if;
  end if;
  if new.brand_id is not null
     and (tg_op = 'INSERT' or new.brand_id is distinct from old.brand_id)
     and exists (select 1 from public.brands b where b.id = new.brand_id and b.frozen) then
    raise exception 'brand is frozen' using errcode = '42501';
  end if;
  return new;
end; $$;

drop trigger if exists projects_fill_brand on public.projects;
create trigger projects_fill_brand before insert or update of brand_id on public.projects
  for each row execute function public.fill_brand_id();
drop trigger if exists collections_fill_brand on public.collections;
create trigger collections_fill_brand before insert or update of brand_id on public.collections
  for each row execute function public.fill_brand_id();

-- ------------------------------------------------------------ 3) create_brand（オーナー限定・プラン上限）
create or replace function public.create_brand(p_org uuid, p_name text, p_assets jsonb default '{}'::jsonb)
returns uuid language plpgsql security definer set search_path = public as $$
declare v_max int; v_used int; v_id uuid; v_name text := nullif(btrim(coalesce(p_name, '')), '');
begin
  if not public.is_owner(p_org) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  if v_name is null then
    raise exception 'brand name is required';
  end if;
  select pl.brands into v_max from public.organizations o join public.plans pl on pl.id = o.plan where o.id = p_org;
  if coalesce(v_max, 1) <> 0 then                      -- 0 = 無制限
    select count(*) into v_used from public.brands where org_id = p_org and not frozen;   -- 凍結中は枠を使わない
    if v_used >= v_max then
      raise exception 'brand limit reached' using errcode = '53400';
    end if;
  end if;
  insert into public.brands (org_id, name, assets) values (p_org, v_name, coalesce(p_assets, '{}'::jsonb))
  returning id into v_id;
  return v_id;
end; $$;
grant execute on function public.create_brand(uuid, text, jsonb) to authenticated;

-- ------------------------------------------------------------ 4) delete_brand（オーナー限定・最後の1つは不可・中身は既定ブランドへ退避）
create or replace function public.delete_brand(p_brand uuid)
returns void language plpgsql security definer set search_path = public as $$
declare v_org uuid; v_count int; v_target uuid;
begin
  select org_id into v_org from public.brands where id = p_brand;
  if v_org is null then raise exception 'brand not found'; end if;
  if not public.is_owner(v_org) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  select count(*) into v_count from public.brands where org_id = v_org;
  if v_count <= 1 then
    raise exception 'keep at least one brand' using errcode = '53400';
  end if;
  -- 退避先 = 削除対象以外の既定ブランド（最古）。凍結でも退避は許す（トリガを避けて直接 UPDATE）
  select id into v_target from public.brands where org_id = v_org and id <> p_brand order by created_at asc, id asc limit 1;
  alter table public.projects    disable trigger projects_fill_brand;
  alter table public.collections disable trigger collections_fill_brand;
  update public.projects    set brand_id = v_target where brand_id = p_brand;
  update public.collections set brand_id = v_target where brand_id = p_brand;
  alter table public.projects    enable trigger projects_fill_brand;
  alter table public.collections enable trigger collections_fill_brand;
  delete from public.brands where id = p_brand;
end; $$;
grant execute on function public.delete_brand(uuid) to authenticated;

-- ------------------------------------------------------------ 5) set_brand_frozen（オーナー限定。解除は上限内のみ）
create or replace function public.set_brand_frozen(p_brand uuid, p_frozen boolean)
returns void language plpgsql security definer set search_path = public as $$
declare v_org uuid; v_max int; v_active int;
begin
  select org_id into v_org from public.brands where id = p_brand;
  if v_org is null then raise exception 'brand not found'; end if;
  if not public.is_owner(v_org) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  if not p_frozen then
    select pl.brands into v_max from public.organizations o join public.plans pl on pl.id = o.plan where o.id = v_org;
    if coalesce(v_max, 1) <> 0 then
      select count(*) into v_active from public.brands where org_id = v_org and not frozen and id <> p_brand;
      if v_active >= v_max then
        raise exception 'brand limit reached' using errcode = '53400';
      end if;
    end if;
  end if;
  update public.brands set frozen = p_frozen where id = p_brand;
end; $$;
grant execute on function public.set_brand_frozen(uuid, boolean) to authenticated;

-- ブランド数の状況（UI の残数表示用）: max(0=無制限) / active / total
create or replace function public.brand_quota(p_org uuid)
returns table(max_brands int, active int, total int, max_collections int)
language sql stable security definer set search_path = public as $$
  select coalesce(pl.brands, 1), 
         (select count(*)::int from public.brands b where b.org_id = p_org and not b.frozen),
         (select count(*)::int from public.brands b where b.org_id = p_org),
         coalesce(pl.collections, 0)
  from public.organizations o join public.plans pl on pl.id = o.plan
  where o.id = p_org and public.is_member(p_org);
$$;
grant execute on function public.brand_quota(uuid) to authenticated;

-- ------------------------------------------------------------ 6) コレクション上限（ブランドあたり・0=無制限・Free のみ 12）
create or replace function public.enforce_collection_limit()
returns trigger language plpgsql security definer set search_path = public as $$
declare v_max int; v_used int;
begin
  if new.brand_id is null then return new; end if;
  select pl.collections into v_max from public.organizations o join public.plans pl on pl.id = o.plan where o.id = new.org_id;
  if coalesce(v_max, 0) <> 0 then
    select count(*) into v_used from public.collections where brand_id = new.brand_id;
    if v_used >= v_max then
      raise exception 'collection limit reached' using errcode = '53400';
    end if;
  end if;
  return new;
end; $$;
drop trigger if exists collections_limit on public.collections;
create trigger collections_limit before insert on public.collections
  for each row execute function public.enforce_collection_limit();

-- ------------------------------------------------------------ 7) RLS: brands は作成/削除を RPC 経由に限定（上限とオーナー限定を迂回させない）
drop policy if exists "writer writes brands" on public.brands;
drop policy if exists "writer updates brands" on public.brands;
create policy "writer updates brands" on public.brands for update
  using (public.can_write(org_id)) with check (public.can_write(org_id));
-- INSERT / DELETE のポリシーは置かない（= create_brand / delete_brand の security definer のみ）
