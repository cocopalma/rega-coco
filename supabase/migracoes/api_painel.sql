-- Conector «dados da rega»: quadros do painel, percursos, limites e planos (13/11/2026, Valdo: "Sim, pode avançar").
-- api_painel lê com as permissões de quem pede: põe o utilizador (perfil) como sessão só dentro desta chamada e chama
-- as mesmas funções que o painel e a app usam. Só o servidor (função dados-rega, service_role) a pode chamar, e só
-- para pessoas da lista api_utilizadores. Só leitura.
create or replace function public.api_painel(p_perfil uuid, p_tipo text, p_de date, p_ate date)
returns json
language plpgsql
security definer
set search_path = public
as $$
declare
  r json;
  pc record;
  lst json[] := '{}';
begin
  if not exists (select 1 from api_utilizadores where perfil_id = p_perfil and activo) then
    raise exception 'Esta conta não tem acesso aos dados';
  end if;
  perform set_config('request.jwt.claims', json_build_object('sub', p_perfil, 'role', 'authenticated')::text, true);
  perform set_config('request.jwt.claim.sub', p_perfil::text, true);

  if p_tipo = 'cumprimento' then r := painel_cumprimento(p_de, p_ate);
  elsif p_tipo = 'meta' then r := painel_meta_causas(p_de, p_ate);
  elsif p_tipo = 'tempos' then r := painel_tempos_equipa2(p_de, p_ate);
  elsif p_tipo = 'nunca_agua' then r := painel_nunca_agua(p_de, p_ate);
  elsif p_tipo = 'plantas_vivas' then r := painel_plantas_vivas(p_de, p_ate);
  elsif p_tipo = 'constrangimentos' then r := painel_constrangimentos(p_de, p_ate);
  elsif p_tipo = 'painel_resumo' then r := painel_resumo_periodo(p_de, p_ate)::json;
  elsif p_tipo = 'planos' then
    -- uma linha por campo do itinerário (plano › dia › ordem), com o nome do produtor e a comunidade
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
      from jsonb_array_elements(coalesce(planos_lista(), '[]'::jsonb)) p
      cross join lateral jsonb_array_elements(p->'dias') d
      cross join lateral jsonb_array_elements(d->'campos') with ordinality c(v, ordem)
      left join areas a on a.id = c.v->>'area_id';
  elsif p_tipo = 'percursos' then
    -- percursos GPS de um dia (equipas; os de teste não entram)
    for pc in select * from json_to_recordset(coalesce(percursos_dia(p_de), '[]'::json))
        as x(activista_id uuid, user_id uuid, nome text, teste boolean, n int, primeiro timestamptz, ultimo timestamptz)
      where not coalesce(x.teste, false)
    loop
      lst := lst || json_build_object('activista_id', pc.activista_id, 'equipa', pc.nome, 'n', pc.n,
        'percurso', percurso_dia(p_de, pc.activista_id, pc.user_id));
    end loop;
    r := array_to_json(lst);
  elsif p_tipo = 'limites' then
    -- os mesmos papéis que vêem todos os campos no mapa (activista e oficial de M&E não)
    if coalesce(privado.meu_papel(), '') not in ('gestor', 'director', 'me', 'cliente', 'supervisor', 'tecnico') then
      raise exception 'Sem acesso aos limites dos campos';
    end if;
    select json_build_object(
      'campos', (select coalesce(json_agg(json_build_object(
          'campo', a.id, 'produtor', a.produtor, 'comunidade', a.comunidade, 'zona', a.zona, 'equipa', ac.nome,
          'tecnico', ac.tecnico, 'supervisor', ac.supervisor, 'vivas', a.vivas, 'instaladas', a.instaladas,
          'area_m2', round(coalesce(a.area_m2, case when a.poligono is not null then privado.area_poligono_m2(a.poligono) end)::numeric),
          'fonte_limite', a.poligono_fonte, 'lat', coalesce(cg.lat, a.latitude), 'lon', coalesce(cg.lon, a.longitude), 'poligono', a.poligono)
          order by a.comunidade, a.id), '[]'::json)
        from areas a left join activistas ac on ac.id = a.activista_id
        -- centro = média dos vértices do limite (o ponto da base pode estar longe do limite medido); sem limite, o ponto da base
        left join lateral (select avg((v->>1)::float8) lat, avg((v->>0)::float8) lon
          from jsonb_array_elements(case when jsonb_typeof(a.poligono) = 'array' then a.poligono else '[]'::jsonb end) v) cg on true
        where a.activa),
      'pocos', (select coalesce(json_agg(json_build_object('codigo', codigo, 'comunidade', comunidade, 'fonte', fonte, 'lat', lat, 'lon', lon) order by codigo), '[]'::json) from pocos),
      'pluviometros', (select coalesce(json_agg(json_build_object('nome', nome, 'comunidade', comunidade, 'zona', zona, 'lat', lat, 'lon', lon) order by nome), '[]'::json) from pluviometros where activo))
      into r;
  else
    raise exception 'Tipo desconhecido';
  end if;

  perform set_config('request.jwt.claims', '', true);
  perform set_config('request.jwt.claim.sub', '', true);
  return r;
end;
$$;

revoke all on function public.api_painel(uuid, text, date, date) from public, anon, authenticated;
grant execute on function public.api_painel(uuid, text, date, date) to service_role;
