-- Entrada por utilizador e senha no endereço só de leitura (13/11/2026, Valdo: "a entrada tem que ser por senha";
-- "não precisas mudar a chave todos os meses"). Quem pode ler: só as pessoas desta lista, que entram com o utilizador e a
-- senha da app (OAuth 2.1 do Supabase Auth). As chaves no endereço (api_chaves) deixam de ser aceites pela função.

create table public.api_utilizadores (
  perfil_id uuid primary key references public.perfis(id),
  nome text not null,
  activo boolean not null default true,
  limite_hora int not null default 300,
  autorizado_em timestamptz not null default now(),
  desligado_em timestamptz
);
alter table public.api_utilizadores enable row level security;   -- sem políticas: só a função do servidor lê

alter table public.api_acessos add column if not exists perfil_id uuid references public.perfis(id);
alter table public.api_acessos add column if not exists client_id text;
create index if not exists api_acessos_perfil_em on public.api_acessos (perfil_id, em);

-- dar e tirar o acesso: só no SQL Editor (o Valdo). p_utilizador = utilizador da app (ex.: 'dalmar') ou o email.
create or replace function public.api_autorizar(p_utilizador text, p_limite int default 300) returns text
language plpgsql security definer set search_path to '' as $$
declare v_id uuid; v_nome text;
begin
  select u.id into v_id from auth.users u
   where lower(u.email) in (lower(trim(p_utilizador)), lower(trim(p_utilizador)) || '@rega-coco.example.com') limit 1;
  if v_id is null then raise exception 'Utilizador não encontrado: %', p_utilizador; end if;
  select p.nome into v_nome from public.perfis p where p.id = v_id;
  if v_nome is null then raise exception 'Este utilizador não tem perfil na app'; end if;
  insert into public.api_utilizadores (perfil_id, nome, limite_hora) values (v_id, v_nome, coalesce(p_limite, 300))
  on conflict (perfil_id) do update set activo = true, desligado_em = null, limite_hora = excluded.limite_hora, autorizado_em = now();
  return 'autorizado: ' || v_nome;
end $$;

create or replace function public.api_desautorizar(p_utilizador text) returns text
language plpgsql security definer set search_path to '' as $$
declare v_nome text;
begin
  update public.api_utilizadores a set activo = false, desligado_em = now()
   from auth.users u where u.id = a.perfil_id and a.activo
    and lower(u.email) in (lower(trim(p_utilizador)), lower(trim(p_utilizador)) || '@rega-coco.example.com')
  returning a.nome into v_nome;
  return coalesce('desligado: ' || v_nome, 'nada a desligar');
end $$;

create or replace function public.api_validar_perfil(p_perfil uuid) returns json
language sql stable security definer set search_path to '' as $$
  select json_build_object('id', a.perfil_id, 'nome', a.nome, 'limite', a.limite_hora,
    'pedidos_hora', (select count(*) from public.api_acessos x where x.perfil_id = a.perfil_id and x.em > now() - interval '1 hour'))
  from public.api_utilizadores a where a.activo and a.perfil_id = p_perfil;
$$;

create or replace function public.api_registar2(p_perfil uuid, p_client text, p_ip text, p_agente text, p_via text, p_accao text,
  p_param jsonb, p_linhas int, p_ms int, p_estado int)
returns void language sql security definer set search_path to '' as $$
  insert into public.api_acessos (perfil_id, client_id, ip, agente, via, accao, parametros, linhas, ms, estado)
  values (p_perfil, left(p_client, 80), left(p_ip, 80), left(p_agente, 200), p_via, left(p_accao, 60), p_param, p_linhas, p_ms, p_estado);
$$;

revoke all on function public.api_autorizar(text, int) from public, anon, authenticated;
revoke all on function public.api_desautorizar(text) from public, anon, authenticated;
revoke all on function public.api_validar_perfil(uuid) from public, anon, authenticated;
revoke all on function public.api_registar2(uuid, text, text, text, text, text, jsonb, int, int, int) from public, anon, authenticated;

-- alarme: mesma ideia, agora por pessoa; com entradas (via 'entrada' = o navegador de quem entra, com o IP verdadeiro)
create or replace function public.api_alertas(p_desde timestamptz) returns json language sql stable security definer set search_path to '' as $$
  select json_build_object(
    'muitos_pedidos', (select coalesce(json_agg(z), '[]') from (select coalesce(u.nome, '?') nome, date_trunc('hour', a.em) hora, count(*) n
        from public.api_acessos a left join public.api_utilizadores u on u.perfil_id = a.perfil_id
        where a.em >= p_desde and a.perfil_id is not null group by 1, 2 having count(*) > 200) z),
    'fora_de_horas', (select coalesce(json_agg(z), '[]') from (select coalesce(u.nome, '?') nome, count(*) n, privado.hl(min(a.em)) primeiro
        from public.api_acessos a left join public.api_utilizadores u on u.perfil_id = a.perfil_id
        where a.em >= p_desde and a.perfil_id is not null and a.estado < 400
        and ((a.em at time zone 'Africa/Maputo')::time >= '22:00' or (a.em at time zone 'Africa/Maputo')::time < '05:00') group by 1) z),
    'entradas', (select coalesce(json_agg(z), '[]') from (select coalesce(u.nome, p.nome, '?') nome, a.ip, left(a.agente, 80) agente,
        privado.hl(a.em) em, a.estado,
        not exists (select 1 from public.api_acessos b where b.perfil_id = a.perfil_id and b.via = 'entrada' and b.ip = a.ip
                    and b.em < a.em and b.em > a.em - interval '30 days') endereco_novo
        from public.api_acessos a left join public.api_utilizadores u on u.perfil_id = a.perfil_id left join public.perfis p on p.id = a.perfil_id
        where a.em >= p_desde and a.via = 'entrada') z),
    'ligacoes_novas', (select coalesce(json_agg(z), '[]') from (select coalesce(u.nome, '?') nome, a.client_id, privado.hl(min(a.em)) primeiro
        from public.api_acessos a left join public.api_utilizadores u on u.perfil_id = a.perfil_id
        where a.em >= p_desde and a.client_id is not null
        and not exists (select 1 from public.api_acessos b where b.client_id = a.client_id and b.em < p_desde)
        group by 1, 2) z),
    'recusados_sem_permissao', (select coalesce(json_agg(z), '[]') from (select coalesce(p.nome, '?') nome, a.via, a.accao, count(*) n
        from public.api_acessos a left join public.perfis p on p.id = a.perfil_id
        where a.em >= p_desde and a.estado = 403 group by 1, 2, 3) z),
    'sem_sessao_valida', (select count(*) from public.api_acessos a where a.perfil_id is null and a.estado = 401 and a.em >= p_desde and a.accao <> 'mcp:sem-token'),
    'pedidos_recusados_por_limite', (select count(*) from public.api_acessos a where a.estado = 429 and a.em >= p_desde));
$$;
revoke all on function public.api_alertas(timestamptz) from public, anon, authenticated;
