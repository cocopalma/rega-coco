-- Conector «dados da rega»: acesso da Kathleen (M&E) e alarme de aparelho novo (14/11/2026, Valdo: "Aprovo").
-- 1. tipos_fora: quadros que uma pessoa não vê pelo conector (vazio = como o papel dela na app).
-- 2. Kathleen: acesso, limite de 300 pedidos por hora, recontagens por validar com números, sem planos nem percursos.
-- 3. api_alertas: cada entrada diz também se o navegador/aparelho é novo para essa pessoa (30 dias).
alter table public.api_utilizadores add column if not exists tipos_fora text[] not null default '{}';

select public.api_autorizar('kathleen', 300);
update public.api_utilizadores set ve_recontagens_por_validar = true, tipos_fora = array['planos', 'percursos']
 where perfil_id = '8146447a-b8d6-41f6-a211-517182d5b17c';

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
  -- tipos que esta pessoa não vê pelo conector (Kathleen: planos e percursos, Valdo 14/11/2026)
  if exists (select 1 from public.api_utilizadores a where a.perfil_id = p_perfil and p_tipo = any(a.tipos_fora)) then
    raise exception 'Esta conta não tem acesso a este quadro';
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

create or replace function public.api_alertas(p_desde timestamp with time zone)
 returns json language sql stable security definer set search_path to '' as $function$
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
                    and b.em < a.em and b.em > a.em - interval '30 days') endereco_novo,
        not exists (select 1 from public.api_acessos b where b.perfil_id = a.perfil_id and b.via = 'entrada' and b.agente = a.agente
                    and b.em < a.em and b.em > a.em - interval '30 days') aparelho_novo
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
$function$;
