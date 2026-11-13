-- Conector «dados da rega» v2.2 (13/11/2026, Valdo: "Aprovo as correcções A e B").
-- A: os dados seguem as permissões da app de quem pede (api_dados2, api_foto_ok); recontagens por validar escondidas,
--    salvo ao M&E e a quem tem api_utilizadores.ve_recontagens_por_validar (Valdo e Dalmar, decisão de 13/11/2026).
-- B: api_painel com search_path vazio e nomes completos; pedidos sem sessão gravam no máximo 1 linha por IP e minuto.
-- Compatível com a função dados-rega v2.1 (versão 3): não muda api_dados; só acrescenta. Ver ORDEM no fim.

-- 1. excepção por pessoa: ver as recontagens antes da validação
alter table public.api_utilizadores add column if not exists ve_recontagens_por_validar boolean not null default false;
-- por perfil_id (revisão do Claude Code, 13/11/2026), os dois já estão em api_utilizadores:
-- 8a1b9364-… = Etevaldo Cheveia (Valdo), e99218fc-… = Dalmar Santos
update public.api_utilizadores set ve_recontagens_por_validar = true
 where perfil_id in ('8a1b9364-5b17-464a-b30b-f52136036c2f', 'e99218fc-573d-48c2-8f79-7a24c3d5ba59');

-- 2. papéis que podem ler pelo conector (os mesmos que vêem todos os campos na app; activista, oficial de M&E e
--    chefe de manutenção não) e sessão de quem pede, só dentro da chamada
create or replace function privado.api_papel(p_perfil uuid) returns text
language sql stable security definer set search_path to '' as $$
  select p.papel from public.api_utilizadores a join public.perfis p on p.id = a.perfil_id
   where a.activo and a.perfil_id = p_perfil
     and p.papel in ('gestor', 'director', 'me', 'cliente', 'supervisor', 'tecnico');
$$;
create or replace function privado.api_sessao(p_perfil uuid) returns void
language sql volatile set search_path to '' as $$
  select set_config('request.jwt.claims', case when p_perfil is null then '' else json_build_object('sub', p_perfil, 'role', 'authenticated')::text end, true),
         set_config('request.jwt.claim.sub', coalesce(p_perfil::text, ''), true);
$$;
revoke all on function privado.api_papel(uuid) from public, anon, authenticated;
revoke all on function privado.api_sessao(uuid) from public, anon, authenticated;

-- 3. dados com as permissões da app (a api_dados antiga fica para a versão 3 da função até ser substituída)
create or replace function public.api_dados2(p_perfil uuid, p_tipo text, p_de date, p_ate date,
  p_comunidade text default null, p_equipa text default null)
returns json language plpgsql security definer set search_path to '' as $$
declare
  v_papel text := privado.api_papel(p_perfil);
  v_ve_rec boolean;
  v_manut text;
  r json;
begin
  if v_papel is null then raise exception 'Esta conta não tem acesso aos dados'; end if;
  select a.ve_recontagens_por_validar into v_ve_rec from public.api_utilizadores a where a.perfil_id = p_perfil;
  -- monitoria: o cliente não a vê no painel
  if p_tipo = 'monitorias' and v_papel = 'cliente' then return '[]'::json; end if;
  -- manutenção: como privado.manut_acesso() na app
  if p_tipo = 'manutencao' then
    perform privado.api_sessao(p_perfil);
    v_manut := privado.manut_acesso();
    perform privado.api_sessao(null);
    if v_manut is null then return '[]'::json; end if;
  end if;

  r := public.api_dados(p_tipo, p_de, p_ate, p_comunidade, p_equipa);

  if p_tipo = 'recontagens' then
    -- como recontagens_lista: sem as canceladas; técnico, supervisor e cliente só nos campos da sua lista;
    -- antes da validação sem contagem, data da contagem nem fotografias (salvo M&E e a excepção)
    perform privado.api_sessao(p_perfil);
    select coalesce(json_agg(
             case when x->>'estado' = 'validada' or v_papel = 'me' or coalesce(v_ve_rec, false) then x
                  else (x::jsonb || '{"vivas": null, "mortas": null, "contada_em": null, "fotos": null}'::jsonb)::json end
             order by x->>'pedida_em'), '[]'::json)
      into r
      from json_array_elements(r) x
      join public.areas a on a.id = x->>'campo'
     where x->>'estado' <> 'cancelada'
       and (v_papel in ('me', 'gestor', 'director') or coalesce(privado.ve_area(a.activista_id, a.comunidade), false));
    perform privado.api_sessao(null);
  elsif p_tipo = 'chuva' and v_papel = 'cliente' then
    -- o painel não mostra as fotografias da chuva ao cliente
    select coalesce(json_agg((x::jsonb - 'foto')::json), '[]'::json) into r from json_array_elements(r) x;
  end if;
  return r;
end $$;
revoke all on function public.api_dados2(uuid, text, date, date, text, text) from public, anon, authenticated;
grant execute on function public.api_dados2(uuid, text, date, date, text, text) to service_role;

-- 4. fotografias: só as de registos que a pessoa vê nos dados
create or replace function public.api_foto_ok(p_perfil uuid, p_ref text) returns boolean
language plpgsql security definer set search_path to '' as $$
declare
  v_papel text := privado.api_papel(p_perfil);
  v_ve_rec boolean;
  b text := split_part(p_ref, '/', 1);
  c text := substr(p_ref, length(split_part(p_ref, '/', 1)) + 2);
  ok boolean := false;
  v_manut text;
begin
  if v_papel is null or c = '' then return false; end if;
  select a.ve_recontagens_por_validar into v_ve_rec from public.api_utilizadores a where a.perfil_id = p_perfil;
  if b = 'rega-fotos' then
    ok := exists (select 1 from public.registos_rega g where not g.teste and c in (g.foto_entrada, g.foto_rega, g.foto_saida))
       or exists (select 1 from public.dias_sem_rega s where not s.removido and s.foto_path = c)
       or exists (select 1 from public.acompanhamentos o where not o.removido and not coalesce(o.teste, false) and o.foto_path = c)
       or exists (select 1 from public.queimadas q where not coalesce(q.removida, false) and q.foto_path = c);
  elsif b = 'recontagem-fotos' then
    perform privado.api_sessao(p_perfil);
    ok := exists (select 1 from public.recontagens k join public.areas a on a.id = k.area_id
                   where k.estado <> 'cancelada' and c in (k.foto_path, k.foto_campo_path)
                     and (k.estado = 'validada' or v_papel = 'me' or coalesce(v_ve_rec, false))
                     and (v_papel in ('me', 'gestor', 'director') or coalesce(privado.ve_area(a.activista_id, a.comunidade), false)));
    perform privado.api_sessao(null);
  elsif b = 'manutencao-fotos' then
    perform privado.api_sessao(p_perfil);
    v_manut := privado.manut_acesso();
    perform privado.api_sessao(null);
    ok := v_manut is not null and exists (select 1 from public.manutencao_registos m where not m.removido and m.foto_path = c);
  elsif b = 'chuva-fotos' then
    ok := v_papel <> 'cliente' and exists (select 1 from public.chuva h where not h.teste and h.foto_path = c);
  elsif b = 'monitoria-fotos' then
    ok := v_papel <> 'cliente' and exists (select 1 from public.monitorias m where m.foto_path = c);
  end if;
  return ok;
end $$;
revoke all on function public.api_foto_ok(uuid, text) from public, anon, authenticated;
grant execute on function public.api_foto_ok(uuid, text) to service_role;

-- 5. api_painel: search_path vazio, nomes completos e os mesmos papéis que a api_dados2
create or replace function public.api_painel(p_perfil uuid, p_tipo text, p_de date, p_ate date)
returns json
language plpgsql
security definer
set search_path = ''
as $$
declare
  r json;
  pc record;
  lst json[] := '{}';
begin
  if privado.api_papel(p_perfil) is null then
    raise exception 'Esta conta não tem acesso aos dados';
  end if;
  perform privado.api_sessao(p_perfil);

  if p_tipo = 'cumprimento' then r := public.painel_cumprimento(p_de, p_ate);
  elsif p_tipo = 'meta' then r := public.painel_meta_causas(p_de, p_ate);
  elsif p_tipo = 'tempos' then r := public.painel_tempos_equipa2(p_de, p_ate);
  elsif p_tipo = 'nunca_agua' then r := public.painel_nunca_agua(p_de, p_ate);
  elsif p_tipo = 'plantas_vivas' then r := public.painel_plantas_vivas(p_de, p_ate);
  elsif p_tipo = 'constrangimentos' then r := public.painel_constrangimentos(p_de, p_ate);
  elsif p_tipo = 'painel_resumo' then r := public.painel_resumo_periodo(p_de, p_ate)::json;
  elsif p_tipo = 'planos' then
    select coalesce(json_agg(json_build_object(
        'plano_id', p->>'id', 'equipa', p->>'activista', 'supervisor', p->>'supervisor', 'ronda', (p->>'ronda')::int,
        'estado', p->>'estado', 'criado_em', p->>'criado_em', 'aprovado_supervisor_em', p->>'supervisor_em',
        'aprovado_supervisor_por', p->>'supervisor_nome', 'aprovado_gestor_em', p->>'gestor_em', 'aprovado_gestor_por', p->>'gestor_nome',
        'recusado_em', p->>'recusado_em', 'recusa_motivo', p->>'recusa_motivo', 'pessoas', (p->>'pessoas')::numeric,
        'capacidade_plantas_dia', (p->>'capacidade')::numeric, 'notas', p->>'notas',
        'dia', (d->>'n')::int, 'dias_no_plano', jsonb_array_length(p->'dias'), 'dia_plantas', (d->>'plantas')::numeric,
        'dia_km', round(((d->>'dist_m')::numeric) / 1000, 2), 'dia_minutos', (d->>'minutos')::numeric,
        'ordem', c.ordem, 'campo', c.v->>'area_id', 'produtor', a.produtor, 'comunidade', a.comunidade,
        'plantas', (c.v->>'plantas')::numeric, 'sem_coordenada', (c.v->>'sem_coordenada')::boolean)
        order by p->>'activista', (p->>'ronda')::int, p->>'criado_em', (d->>'n')::int, c.ordem), '[]'::json)
      into r
      from jsonb_array_elements(coalesce(public.planos_lista(), '[]'::jsonb)) p
      cross join lateral jsonb_array_elements(p->'dias') d
      cross join lateral jsonb_array_elements(d->'campos') with ordinality c(v, ordem)
      left join public.areas a on a.id = c.v->>'area_id';
  elsif p_tipo = 'percursos' then
    for pc in select * from json_to_recordset(coalesce(public.percursos_dia(p_de), '[]'::json))
        as x(activista_id uuid, user_id uuid, nome text, teste boolean, n int, primeiro timestamptz, ultimo timestamptz)
      where not coalesce(x.teste, false)
    loop
      lst := lst || json_build_object('activista_id', pc.activista_id, 'equipa', pc.nome, 'n', pc.n,
        'percurso', public.percurso_dia(p_de, pc.activista_id, pc.user_id));
    end loop;
    r := array_to_json(lst);
  elsif p_tipo = 'limites' then
    select json_build_object(
      'campos', (select coalesce(json_agg(json_build_object(
          'campo', a.id, 'produtor', a.produtor, 'comunidade', a.comunidade, 'zona', a.zona, 'equipa', ac.nome,
          'tecnico', ac.tecnico, 'supervisor', ac.supervisor, 'vivas', a.vivas, 'instaladas', a.instaladas,
          'area_m2', round(coalesce(a.area_m2, case when a.poligono is not null then privado.area_poligono_m2(a.poligono) end)::numeric),
          'fonte_limite', a.poligono_fonte, 'lat', coalesce(cg.lat, a.latitude), 'lon', coalesce(cg.lon, a.longitude), 'poligono', a.poligono)
          order by a.comunidade, a.id), '[]'::json)
        from public.areas a left join public.activistas ac on ac.id = a.activista_id
        -- centro = média dos vértices do limite (o ponto da base pode estar longe do limite medido); sem limite, o ponto da base
        left join lateral (select avg((v->>1)::float8) lat, avg((v->>0)::float8) lon
          from jsonb_array_elements(case when jsonb_typeof(a.poligono) = 'array' then a.poligono else '[]'::jsonb end) v) cg on true
        where a.activa),
      'pocos', (select coalesce(json_agg(json_build_object('codigo', o.codigo, 'comunidade', o.comunidade, 'fonte', o.fonte, 'lat', o.lat, 'lon', o.lon) order by o.codigo), '[]'::json) from public.pocos o),
      'pluviometros', (select coalesce(json_agg(json_build_object('nome', l.nome, 'comunidade', l.comunidade, 'zona', l.zona, 'lat', l.lat, 'lon', l.lon) order by l.nome), '[]'::json) from public.pluviometros l where l.activo))
      into r;
  else
    raise exception 'Tipo desconhecido';
  end if;

  perform privado.api_sessao(null);
  return r;
end;
$$;
revoke all on function public.api_painel(uuid, text, date, date) from public, anon, authenticated;
grant execute on function public.api_painel(uuid, text, date, date) to service_role;

-- 6. pedidos sem sessão: no máximo 1 linha por IP e minuto (para não encher api_acessos)
create or replace function public.api_registar2(p_perfil uuid, p_client text, p_ip text, p_agente text, p_via text, p_accao text,
  p_param jsonb, p_linhas int, p_ms int, p_estado int)
returns void language sql security definer set search_path to '' as $$
  insert into public.api_acessos (perfil_id, client_id, ip, agente, via, accao, parametros, linhas, ms, estado)
  select p_perfil, left(p_client, 80), left(p_ip, 80), left(p_agente, 200), p_via, left(p_accao, 60), p_param, p_linhas, p_ms, p_estado
   where p_perfil is not null or p_estado <> 401
      or not exists (select 1 from public.api_acessos x where x.perfil_id is null and x.estado = 401
                       and x.ip is not distinct from left(p_ip, 80) and x.em > now() - interval '1 minute');
$$;
revoke all on function public.api_registar2(uuid, text, text, text, text, text, jsonb, int, int, int) from public, anon, authenticated;

-- ORDEM DA PUBLICAÇÃO: (1) este ficheiro na base de dados; (2) função dados-rega v2.2; (3) autorizar.html no main.
-- VOLTAR ATRÁS: função → publicar de novo supabase/functions/dados-rega/index.ts do commit 9cf379a (v2.1; não usa nada
-- deste ficheiro); api_painel → correr de novo supabase/migracoes/api_painel.sql (commit 9cf379a); api_registar2 → correr
-- de novo a sua definição em supabase/migracoes/api_oauth.sql. api_dados2, api_foto_ok, privado.api_papel/api_sessao e a
-- coluna nova podem ficar (a v2.1 não as usa).
