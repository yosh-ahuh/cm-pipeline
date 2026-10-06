-- 025_share_notify.sql — 共有リンク（project_shares）と完了通知の設定（profiles.notify_*）。
--   共有: 書き出し済み動画をサインイン不要で見せる。トークンは推測不能、30 日で失効、取り消し可。
--     実ファイルの署名 URL は Edge Function `share`（service_role）がトークン検証のうえ発行する（DB からは出さない）。
--   通知: 制作完了メール（ワーカーが Resend で送信）の ON/OFF を profiles に持つ（従来は localStorage のみ＝送られないメールを約束していた）。
--   前提: 006〜024 適用済み。冪等。

-- ------------------------------------------------------------ 1) 共有リンク
create table if not exists public.project_shares (
  id         uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  org_id     uuid not null references public.organizations(id) on delete cascade,
  token      text not null unique,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '30 days',
  revoked_at timestamptz
);
create index if not exists project_shares_project_idx on public.project_shares(project_id);

alter table public.project_shares enable row level security;
drop policy if exists "member reads shares" on public.project_shares;
create policy "member reads shares" on public.project_shares for select
  using (public.is_member(org_id) and public.project_visible(project_id));
-- 作成・取消は RPC のみ

-- 有効な共有があればそれを返し、無ければ作る（can_write のメンバー）。
create or replace function public.create_share(p_project uuid)
returns text language plpgsql security definer set search_path = public as $$
declare v_org uuid; v_token text;
begin
  select org_id into v_org from public.projects where id = p_project;
  if v_org is null then raise exception 'project not found' using errcode = 'P0002'; end if;
  if not (public.can_write(v_org) and public.project_visible(p_project)) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  select token into v_token from public.project_shares
    where project_id = p_project and revoked_at is null and expires_at > now()
    order by created_at desc limit 1;
  if v_token is not null then return v_token; end if;
  v_token := replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', '');
  insert into public.project_shares (project_id, org_id, token, created_by) values (p_project, v_org, v_token, auth.uid());
  return v_token;
end; $$;
grant execute on function public.create_share(uuid) to authenticated;

create or replace function public.revoke_share(p_project uuid)
returns void language plpgsql security definer set search_path = public as $$
declare v_org uuid;
begin
  select org_id into v_org from public.projects where id = p_project;
  if v_org is null or not public.can_write(v_org) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  update public.project_shares set revoked_at = now() where project_id = p_project and revoked_at is null;
end; $$;
grant execute on function public.revoke_share(uuid) to authenticated;

-- ------------------------------------------------------------ 2) 通知設定（profiles）
alter table public.profiles add column if not exists notify_done boolean not null default true;
alter table public.profiles add column if not exists notify_news boolean not null default false;
alter table public.projects add column if not exists notified_at timestamptz;   -- 完了メールの二重送信防止

create or replace function public.update_notify_prefs(p_done boolean, p_news boolean)
returns void language plpgsql security definer set search_path = public as $$
begin
  update public.profiles set notify_done = coalesce(p_done, notify_done), notify_news = coalesce(p_news, notify_news)
   where id = auth.uid();
end; $$;
grant execute on function public.update_notify_prefs(boolean, boolean) to authenticated;
