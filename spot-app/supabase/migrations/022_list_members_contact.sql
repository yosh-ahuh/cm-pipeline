-- 022_list_members_contact.sql — メンバー一覧に「メール」と「アイコン」を出すため、list_members を拡張。
--   返す列を増やすため一度 DROP して作り直す（CREATE OR REPLACE は OUT 列の変更不可）。
--   email は auth.users から、avatar は自前設定(profiles.avatar_url)→無ければ OAuth画像(Google等の user_metadata)。
--   公開範囲は従来どおり is_member(p_org) のメンバーのみ（チーム内でメール/アイコンを見せるのは想定内）。冪等。

drop function if exists public.list_members(uuid);

create or replace function public.list_members(p_org uuid)
returns table(user_id uuid, display_name text, email text, avatar text, role text, added_at timestamptz)
language sql security definer stable set search_path = public as $$
  select m.user_id,
         p.display_name,
         u.email::text as email,
         coalesce(
           nullif(p.avatar_url, ''),
           u.raw_user_meta_data->>'avatar_url',
           u.raw_user_meta_data->>'picture'
         ) as avatar,
         m.role,
         m.added_at
  from public.org_members m
    left join public.profiles p on p.id = m.user_id
    left join auth.users    u on u.id = m.user_id
  where m.org_id = p_org and public.is_member(p_org)
  order by (m.role = 'owner') desc, m.added_at;
$$;

grant execute on function public.list_members(uuid) to authenticated;
