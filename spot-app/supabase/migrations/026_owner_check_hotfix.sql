-- 026_owner_check_hotfix.sql — オーナー判定の NULL すり抜けを塞ぐ（セキュリティ修正）＋ Free のコレクション上限値。
--   問題: member_role(p_org) は非メンバーに NULL を返す。`if member_role(p_org) <> 'owner' then raise` は
--         NULL <> 'owner' = NULL → 偽扱いで raise されず、非メンバーが create_invite / remove_member /
--         set_org_domain / set_member_brands を実行できた（例: 他人の org への招待トークンを自分で作って参加）。
--   対策: member_role を NULL を返さない定義（非メンバー='none'）に置き換える。= 'owner' を使う RLS は従来どおり。
--   あわせて 021 の値投入が反映されていない環境向けに plans.collections（Free=12）を補正。冪等。

create or replace function public.member_role(p_org uuid)
returns text language sql security definer stable set search_path = public as $$
  select coalesce((select role from public.org_members where org_id = p_org and user_id = auth.uid() limit 1), 'none');
$$;
grant execute on function public.member_role(uuid) to authenticated;

-- 念のため、呼び出し側でも明示ガード（member_role の将来変更に依存しない）
create or replace function public.create_invite(p_org uuid, p_email text default null, p_role text default 'member', p_brand_ids uuid[] default null)
returns text language plpgsql security definer set search_path = public as $$
declare v_token text; v_ids uuid[];
begin
  if not public.is_owner(p_org) then
    raise exception 'only owner can invite' using errcode = '42501';
  end if;
  if p_role not in ('member','viewer') then
    raise exception 'invalid role' using errcode = '22023';
  end if;
  select nullif(array_agg(b.id), '{}') into v_ids
    from public.brands b where b.org_id = p_org and p_brand_ids is not null and b.id = any(p_brand_ids);
  v_token := replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', '');
  insert into public.org_invites (org_id, email, role, token, invited_by, brand_ids)
  values (p_org, nullif(btrim(lower(p_email)), ''), p_role, v_token, auth.uid(), v_ids);
  return v_token;
end; $$;
grant execute on function public.create_invite(uuid, text, text, uuid[]) to authenticated;

create or replace function public.remove_member(p_org uuid, p_user uuid)
returns void language plpgsql security definer set search_path = public as $$
begin
  if not public.is_owner(p_org) then
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

create or replace function public.set_member_brands(p_org uuid, p_user uuid, p_brand_ids uuid[] default null)
returns void language plpgsql security definer set search_path = public as $$
begin
  if not public.is_owner(p_org) then
    raise exception 'only owner can change access' using errcode = '42501';
  end if;
  if not exists (select 1 from public.org_members where org_id = p_org and user_id = p_user) then
    raise exception 'not a member' using errcode = 'P0002';
  end if;
  if (select role from public.org_members where org_id = p_org and user_id = p_user) = 'owner' then
    return;
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

-- set_org_domain（007）も同じ判定を使っていたため置き換える（本文は 007 と同じ・ガードのみ強化）
do $$
begin
  if exists (select 1 from pg_proc where proname = 'set_org_domain') then
    execute $f$
      create or replace function public.set_org_domain(p_org uuid, p_domain text)
      returns void language plpgsql security definer set search_path = public as $b$
      begin
        if not public.is_owner(p_org) then
          raise exception 'only owner can set domain' using errcode = '42501';
        end if;
        update public.organizations set email_domain = nullif(btrim(lower(p_domain)), '') where id = p_org;
      end; $b$;
    $f$;
  end if;
end $$;

-- Free のコレクション上限（021 の値投入が未反映の環境向け・値が入っていれば触らない）
update public.plans set collections = 12 where id = 'free' and collections = 0;
