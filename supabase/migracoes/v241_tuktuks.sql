-- v241 (15/11/2026, Valdo: "tem de ficar registado, todos os dias, que tuk-tuk serviu que equipa"): tuk-tuk em cada chegada da água.
-- Só acrescenta: a v240 continua a funcionar (as regas dela chegam sem tuk-tuk).
-- Códigos: painel operacional do Dalmar (dados gerados a 14/11/2026 20:55), tipo TUK, sem os 3 abatidos (04, 18, 22). Só leitura lá.

create table if not exists public.tuktuks (
  codigo text primary key, ordem int not null default 0, activo boolean not null default true,
  fonte text, actualizado_em timestamptz not null default now());
alter table public.tuktuks enable row level security;
drop policy if exists tuktuks_ler on public.tuktuks;
create policy tuktuks_ler on public.tuktuks for select to authenticated using ((select privado.meu_papel()) is not null);
grant select on public.tuktuks to authenticated;
insert into public.tuktuks (codigo, ordem) values
  ('01', 1),
  ('02', 2),
  ('03', 3),
  ('05', 4),
  ('06', 5),
  ('07', 6),
  ('08', 7),
  ('09', 8),
  ('10', 9),
  ('11', 10),
  ('12', 11),
  ('13', 12),
  ('14', 13),
  ('15', 14),
  ('16', 15),
  ('17', 16),
  ('19', 17),
  ('20', 18),
  ('21', 19),
  ('23', 20),
  ('30', 21),
  ('31', 22),
  ('32', 23),
  ('GL01', 24),
  ('GLL2', 25),
  ('TTO1', 26),
  ('TTO2', 27),
  ('VGB1', 28),
  ('VGB2', 29),
  ('VGB4', 30),
  ('VGB5', 31)
on conflict (codigo) do nothing;
update public.tuktuks set fonte = 'Painel operacional do Dalmar, dados de 14/11/2026' where fonte is null;

-- tuk_chegada: 'nova' = o tuk-tuk chegou agora com água (conta como viagem); 'mesmo_tanque' = o mesmo tuk-tuk e a mesma água do
-- campo anterior da equipa (não conta); 'ja_estava' = a água já estava no campo (não conta). tuk_outro = «não sei o código / outro».
alter table public.registos_rega add column if not exists tuk_codigo text;
alter table public.registos_rega add column if not exists tuk_outro text;
alter table public.registos_rega add column if not exists tuk_chegada text;
alter table public.registos_rega add column if not exists tuk_corrigido_em timestamptz;
alter table public.registos_rega add column if not exists tuk_corrigido_por uuid;
alter table public.registos_rega drop constraint if exists registos_rega_tuk_chegada_check;
alter table public.registos_rega add constraint registos_rega_tuk_chegada_check check (tuk_chegada is null or tuk_chegada in ('nova', 'mesmo_tanque', 'ja_estava'));

insert into public.config (chave, valor) values ('tuktuk_inicio', to_jsonb(to_char((now() at time zone 'Africa/Maputo')::date, 'YYYY-MM-DD')))
on conflict (chave) do nothing;

-- corrigir o tuk-tuk de uma rega: técnico, supervisor e gestor (como a correcção das plantas); o activista não
create or replace function public.corrigir_tuk_rega(p_id uuid, p_codigo text, p_outro text, p_chegada text, p_motivo text, p_em timestamptz default null)
returns void language plpgsql security definer set search_path to '' as $$
declare v_papel text := privado.meu_papel(); r record; a record; v_em timestamptz := least(coalesce(p_em, now()), now());
  v_cod text := nullif(trim(coalesce(p_codigo, '')), ''); v_out text := nullif(trim(coalesce(p_outro, '')), '');
begin
  if v_papel is null or v_papel not in ('tecnico','supervisor','gestor') then raise exception 'Só o técnico, o supervisor ou o gestor podem corrigir o tuk-tuk'; end if;
  if v_cod is not null and not exists (select 1 from public.tuktuks t where t.codigo = v_cod) then raise exception 'Tuk-tuk desconhecido'; end if;
  if v_cod is null and length(coalesce(v_out, '')) < 2 then raise exception 'Escolha o tuk-tuk'; end if;
  if p_chegada is null or p_chegada not in ('nova', 'mesmo_tanque', 'ja_estava') then raise exception 'Diga se foi uma viagem nova'; end if;
  if length(trim(coalesce(p_motivo,''))) < 3 then raise exception 'Escreva o motivo da correcção'; end if;
  select * into r from public.registos_rega where id = p_id for update;
  if not found then raise exception 'Rega não encontrada'; end if;
  select activista_id, comunidade into a from public.areas where id = r.area_id;
  if not found or not privado.ve_area(a.activista_id, a.comunidade) then raise exception 'Sem acesso a este campo'; end if;
  if r.tuk_corrigido_em is not null and r.tuk_corrigido_em > v_em then return; end if;
  update public.registos_rega set tuk_codigo = v_cod, tuk_outro = case when v_cod is null then v_out end, tuk_chegada = p_chegada,
    tuk_corrigido_em = v_em, tuk_corrigido_por = auth.uid() where id = p_id;
  insert into public.alteracoes_registos (registo_id, campo, valor_antigo, valor_novo, motivo, feito_por, feito_no_telefone_em)
  values (p_id, 'tuk', concat_ws(' · ', coalesce(r.tuk_codigo, r.tuk_outro), r.tuk_chegada), concat_ws(' · ', coalesce(v_cod, v_out), p_chegada), trim(p_motivo), auth.uid(), p_em);
end $$;
revoke all on function public.corrigir_tuk_rega(uuid, text, text, text, text, timestamptz) from public, anon;
grant execute on function public.corrigir_tuk_rega(uuid, text, text, text, text, timestamptz) to authenticated;

-- painel: uma linha por chegada da água (regas reais desde config.tuktuk_inicio)
create or replace function public.painel_tuktuks(p_de date, p_ate date)
returns json language plpgsql stable security definer set search_path to '' as $$
declare v_papel text := privado.meu_papel(); v_ini date := (select (valor #>> '{}')::date from public.config where chave = 'tuktuk_inicio');
begin
  if v_papel is null or v_papel not in ('gestor', 'director', 'me', 'supervisor', 'tecnico', 'cliente') then return null; end if;
  if v_ini is null then return null; end if;
  return json_build_object('inicio', v_ini,
    'lista', (select coalesce(json_agg(t.codigo order by t.ordem, t.codigo), '[]'::json) from public.tuktuks t where t.activo),
    'chegadas', (select coalesce(json_agg(json_build_object('data', g.data, 'hora', g.agua_em, 'equipa', ac.nome, 'activista_id', g.activista_id,
        'tecnico', ac.tecnico, 'supervisor', ac.supervisor, 'campo', g.area_id, 'produtor', ar.produtor, 'comunidade', ar.comunidade, 'zona', ar.zona,
        'tuk', g.tuk_codigo, 'outro', g.tuk_outro, 'chegada', g.tuk_chegada, 'viagem', coalesce(g.tuk_chegada = 'nova', false),
        'corrigido', g.tuk_corrigido_em is not null) order by g.data, g.agua_em), '[]'::json)
      from public.registos_rega g join public.areas ar on ar.id = g.area_id left join public.activistas ac on ac.id = g.activista_id
      where not g.teste and g.agua_em is not null and g.data >= v_ini
        and (p_de is null or g.data >= p_de) and (p_ate is null or g.data <= p_ate)));
end $$;
revoke all on function public.painel_tuktuks(date, date) from public, anon;
grant execute on function public.painel_tuktuks(date, date) to authenticated;

-- ficha do campo: «Regas deste campo» com a hora da água e o tuk-tuk
create or replace function public.regas_campo(p_area text)
 returns json language plpgsql stable security definer set search_path to '' as $$
declare v_papel text := privado.meu_papel(); a record; eu text := auth.uid()::text;
begin
  if v_papel is null then raise exception 'sem acesso'; end if;
  select activista_id, comunidade into a from public.areas where id = p_area;
  if not found or not privado.le_area(a.activista_id, a.comunidade) then return '[]'::json; end if;
  return (select coalesce(json_agg(x order by x.entrada_em desc), '[]') from (
    select r.id, r.data, r.entrada_em, r.saida_em, r.plantas_regadas, r.pessoas, r.teste,
           coalesce(t.nome, p.nome) as quem,
           case when v_papel <> 'activista' or split_part(r.foto_entrada,'/',1) = eu then r.foto_entrada end as foto_entrada, r.foto_entrada_em,
           case when v_papel <> 'activista' or split_part(r.foto_rega,'/',1) = eu then r.foto_rega end as foto_rega, r.foto_rega_em,
           case when v_papel <> 'activista' or split_part(r.foto_saida,'/',1) = eu then r.foto_saida end as foto_saida, r.foto_saida_em,
           (v_papel = 'activista' and coalesce(r.foto_entrada, r.foto_rega, r.foto_saida) is not null
              and coalesce(split_part(r.foto_entrada,'/',1), split_part(r.foto_rega,'/',1), split_part(r.foto_saida,'/',1)) <> eu) as fotos_outro,
           r.plantas_originais, r.plantas_corrigidas_em, pc.nome as corrigido_por,
           (select al.motivo from public.alteracoes_registos al where al.registo_id = r.id and al.campo = 'plantas_regadas' order by al.feito_em desc limit 1) as motivo_correccao,
           r.motivo_repetir, r.motivo_tecnico, case when not r.teste and p.papel <> 'activista' then p.nome end as registada_por,
           r.agua_em, r.tuk_codigo, r.tuk_outro, r.tuk_chegada, r.tuk_corrigido_em
    from public.registos_rega r
    left join public.activistas t on t.id = r.activista_id
    left join public.perfis p on p.id = r.user_id
    left join public.perfis pc on pc.id = r.plantas_corrigidas_por
    where r.area_id = p_area
    order by r.entrada_em desc limit 10) x);
end $$;

-- conector: quadro «tuktuks» e o tuk-tuk em cada linha de «regas»
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
  elsif p_tipo = 'tuktuks' then r := public.painel_tuktuks(p_de, p_ate);
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
  elsif p_tipo = 'regas' then
    -- v241: tuk-tuk que trouxe a água a cada rega
    select coalesce(json_agg((x.v::jsonb || jsonb_build_object('tuk_tuk', coalesce(g.tuk_codigo, g.tuk_outro), 'tuk_chegada', g.tuk_chegada))::json order by x.n), '[]'::json)
      into r
      from json_array_elements(r) with ordinality x(v, n)
      left join public.registos_rega g on g.id = (x.v->>'id')::uuid;
  elsif p_tipo = 'chuva' and v_papel = 'cliente' then
    -- o painel não mostra as fotografias da chuva ao cliente
    select coalesce(json_agg((x::jsonb - 'foto')::json), '[]'::json) into r from json_array_elements(r) x;
  end if;
  return r;
end $$;
revoke all on function public.api_dados2(uuid, text, date, date, text, text) from public, anon, authenticated;
grant execute on function public.api_dados2(uuid, text, date, date, text, text) to service_role;
