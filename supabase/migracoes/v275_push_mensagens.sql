-- v275 (28/11/2026, Valdo: "sempre que alguem receber mensagem o telefone emitir um som?" → "As 2."):
-- avisos das mensagens com a app fechada (Web Push). Só acrescenta.
-- O telefone guarda a sua subscrição (gravar_push). Cada mensagem nova (enviada ou resposta) chama, pelo gatilho
-- mensagens_push (pg_net), a função push-mensagem, que manda a notificação às subscrições de quem recebe.
-- As chaves VAPID ficam só em privado.push_config (a função cria-as na 1.ª chamada); o segredo do gatilho também.

create extension if not exists pg_net;

create table if not exists privado.push_config (
  id int primary key default 1 check (id = 1),
  vapid_publica text,
  vapid_privada text,
  segredo text not null default encode(extensions.gen_random_bytes(24), 'hex')
);
insert into privado.push_config (id) values (1) on conflict do nothing;
revoke all on privado.push_config from public, anon, authenticated;

create table if not exists public.push_subscricoes (
  endpoint text primary key,
  perfil_id uuid not null references public.perfis(id) on delete cascade,
  p256dh text not null,
  auth text not null,
  lingua text,
  agente text,
  criada_em timestamptz not null default now(),
  actualizada_em timestamptz not null default now(),
  activa boolean not null default true,
  falhas int not null default 0,
  ultimo_envio timestamptz
);
create index if not exists push_subscricoes_perfil on public.push_subscricoes (perfil_id) where activa;
alter table public.push_subscricoes enable row level security;
revoke all on public.push_subscricoes from anon, authenticated;

alter table public.mensagens add column if not exists push_em timestamptz;
alter table public.mensagens add column if not exists push_enviados int;

-- telefone: guardar / tirar a subscrição
create or replace function public.gravar_push(p_endpoint text, p_p256dh text, p_auth text, p_lingua text default null, p_agente text default null)
returns json language plpgsql security definer set search_path = '' as $$
begin
  if auth.uid() is null or not exists (select 1 from public.perfis where id = auth.uid()) then raise exception 'Sem sessão'; end if;
  if p_endpoint is null or p_endpoint !~ '^https://' or length(p_endpoint) > 1000 then raise exception 'Subscrição inválida'; end if;
  if coalesce(length(p_p256dh), 0) not between 20 and 200 or coalesce(length(p_auth), 0) not between 8 and 100 then raise exception 'Subscrição inválida'; end if;
  insert into public.push_subscricoes (endpoint, perfil_id, p256dh, auth, lingua, agente)
  values (p_endpoint, auth.uid(), p_p256dh, p_auth, left(p_lingua, 5), left(p_agente, 300))
  on conflict (endpoint) do update set perfil_id = excluded.perfil_id, p256dh = excluded.p256dh, auth = excluded.auth,
    lingua = excluded.lingua, agente = excluded.agente, actualizada_em = now(), activa = true, falhas = 0;
  -- no máximo 5 telefones/navegadores por pessoa (ficam os mais recentes)
  delete from public.push_subscricoes s where s.perfil_id = auth.uid() and s.endpoint in (
    select endpoint from public.push_subscricoes where perfil_id = auth.uid() order by actualizada_em desc offset 5);
  return json_build_object('ok', true);
end $$;

create or replace function public.remover_push(p_endpoint text)
returns json language plpgsql security definer set search_path = '' as $$
begin
  delete from public.push_subscricoes where endpoint = p_endpoint and perfil_id = auth.uid();
  return json_build_object('ok', true);
end $$;

create or replace function public.push_chave_publica()
returns text language sql stable security definer set search_path = '' as $$
  select vapid_publica from privado.push_config where id = 1 and auth.uid() is not null;
$$;

-- função push-mensagem (só service_role)
create or replace function public.push_chaves(p_segredo text, p_publica text default null, p_privada text default null)
returns json language plpgsql security definer set search_path = '' as $$
declare c privado.push_config;
begin
  select * into c from privado.push_config where id = 1;
  if c.segredo is distinct from p_segredo then raise exception 'Sem acesso'; end if;
  if c.vapid_publica is null and p_publica is not null and p_privada is not null then
    update privado.push_config set vapid_publica = p_publica, vapid_privada = p_privada where id = 1 returning * into c;
  end if;
  return json_build_object('publica', c.vapid_publica, 'privada', c.vapid_privada);
end $$;

create or replace function public.push_preparar(p_id uuid, p_segredo text)
returns json language plpgsql security definer set search_path = '' as $$
declare c privado.push_config; m public.mensagens; r json;
begin
  select * into c from privado.push_config where id = 1;
  if c.segredo is distinct from p_segredo then raise exception 'Sem acesso'; end if;
  update public.mensagens set push_em = now()
   where id = p_id and push_em is null and not removida and criada_em > now() - interval '1 day'
   returning * into m;
  if not found then return json_build_object('nada', true); end if;
  select json_build_object(
    'id', m.id, 'texto', m.texto, 'resposta', m.resposta_a is not null,
    'de', (select nome from public.perfis where id = m.de_perfil_id),
    'publica', c.vapid_publica, 'privada', c.vapid_privada,
    'subs', coalesce((select json_agg(json_build_object('endpoint', s.endpoint, 'p256dh', s.p256dh, 'auth', s.auth, 'lingua', s.lingua))
                       from public.push_subscricoes s where s.perfil_id = m.para_perfil_id and s.activa), '[]'::json))
  into r;
  return r;
end $$;

create or replace function public.push_resultado(p_id uuid, p_segredo text, p_enviados int, p_expirados text[] default '{}', p_falhados text[] default '{}')
returns json language plpgsql security definer set search_path = '' as $$
declare c privado.push_config;
begin
  select * into c from privado.push_config where id = 1;
  if c.segredo is distinct from p_segredo then raise exception 'Sem acesso'; end if;
  update public.mensagens set push_enviados = p_enviados where id = p_id;
  update public.push_subscricoes set activa = false where endpoint = any (coalesce(p_expirados, '{}'));
  update public.push_subscricoes set falhas = falhas + 1, activa = (falhas + 1) < 5 where endpoint = any (coalesce(p_falhados, '{}'));
  update public.push_subscricoes s set ultimo_envio = now(), falhas = 0
   where s.activa and s.perfil_id = (select para_perfil_id from public.mensagens where id = p_id)
     and not (s.endpoint = any (coalesce(p_expirados, '{}') || coalesce(p_falhados, '{}')));
  return json_build_object('ok', true);
end $$;

revoke all on function public.gravar_push(text, text, text, text, text) from public, anon;
revoke all on function public.remover_push(text) from public, anon;
revoke all on function public.push_chave_publica() from public, anon;
grant execute on function public.gravar_push(text, text, text, text, text) to authenticated;
grant execute on function public.remover_push(text) to authenticated;
grant execute on function public.push_chave_publica() to authenticated;
revoke all on function public.push_chaves(text, text, text) from public, anon, authenticated;
revoke all on function public.push_preparar(uuid, text) from public, anon, authenticated;
revoke all on function public.push_resultado(uuid, text, int, text[], text[]) from public, anon, authenticated;
grant execute on function public.push_chaves(text, text, text) to service_role;
grant execute on function public.push_preparar(uuid, text) to service_role;
grant execute on function public.push_resultado(uuid, text, int, text[], text[]) to service_role;

-- gatilho: cada mensagem nova chama a função (só se quem recebe tem telefones com os avisos ligados)
create or replace function privado.push_mensagem_gatilho()
returns trigger language plpgsql security definer set search_path = '' as $$
declare s text;
begin
  if new.removida then return new; end if;
  if not exists (select 1 from public.push_subscricoes where perfil_id = new.para_perfil_id and activa) then return new; end if;
  select segredo into s from privado.push_config where id = 1;
  perform net.http_post(
    url := 'https://fgzdqnvobgfzjetbbxcm.supabase.co/functions/v1/push-mensagem',
    body := jsonb_build_object('id', new.id),
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-segredo', s),
    timeout_milliseconds := 10000);
  return new;
exception when others then return new;   -- o aviso nunca impede a mensagem de ser gravada
end $$;

drop trigger if exists mensagens_push on public.mensagens;
create trigger mensagens_push after insert on public.mensagens for each row execute function privado.push_mensagem_gatilho();
