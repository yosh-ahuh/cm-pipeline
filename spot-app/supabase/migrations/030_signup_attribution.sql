-- 030_signup_attribution.sql — 登録時の流入元（ランディング/サイトの CTA が付ける utm_* と plan）を保存（2026-10-08）。
--   ・profiles.signup_attribution jsonb: {utm_source, utm_medium, utm_campaign, utm_content, utm_term, plan, ref, landed_at, referrer}
--   ・トリガ on_auth_user_created_attr: メール登録は signUp の metadata(attribution) から写す（handle_new_user の後に発火＝名前順）。
--   ・RPC set_signup_attribution(jsonb): OAuth 登録など metadata を渡せない経路の本線。本人のみ・未設定のときだけ書く（上書き不可）。
--   集計例: select signup_attribution->>'utm_campaign', count(*) from profiles where signup_attribution is not null group by 1;
--   前提: 006〜029 適用済み。冪等。

alter table public.profiles add column if not exists signup_attribution jsonb;

-- 既知のキーだけ・短い文字列だけに絞る（任意 JSON をそのまま入れない）
create or replace function public._clean_attribution(p jsonb)
returns jsonb language sql immutable as $$
  select coalesce(jsonb_object_agg(k, left(v, 200)) filter (where v is not null and v <> ''), '{}'::jsonb)
  from jsonb_each_text(coalesce(p, '{}'::jsonb)) as t(k, v)
  where k in ('utm_source','utm_medium','utm_campaign','utm_content','utm_term','plan','ref','landed_at','referrer');
$$;

create or replace function public.handle_new_user_attribution()
returns trigger language plpgsql security definer set search_path = public as $$
declare v jsonb;
begin
  v := public._clean_attribution(new.raw_user_meta_data->'attribution');
  if v <> '{}'::jsonb then
    update public.profiles set signup_attribution = v where id = new.id and signup_attribution is null;
  end if;
  return new;
end; $$;

drop trigger if exists on_auth_user_created_attr on auth.users;
create trigger on_auth_user_created_attr
  after insert on auth.users
  for each row execute function public.handle_new_user_attribution();

create or replace function public.set_signup_attribution(p_attr jsonb)
returns void language plpgsql security definer set search_path = public as $$
declare v jsonb;
begin
  if auth.uid() is null then
    raise exception 'not signed in' using errcode = '42501';
  end if;
  v := public._clean_attribution(p_attr);
  if v = '{}'::jsonb then return; end if;
  update public.profiles set signup_attribution = v where id = auth.uid() and signup_attribution is null;
end; $$;
grant execute on function public.set_signup_attribution(jsonb) to authenticated;
