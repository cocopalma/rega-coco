-- Plano da equipa (Valdo, 23/10/2026). Duas consultas para o Claude correr no Supabase (execute_sql).

-- 1) Equipas que acabaram uma ronda (desde o início do trabalho dos activistas) e ainda não têm plano para a seguinte.
with ini as (select coalesce((select (valor #>> '{}')::date from public.config where chave = 'activistas_inicio'), '2026-10-24') d),
lista as (select activista_id, count(*) n from public.areas where activa and activista_id is not null group by 1),
r as (select g.activista_id, g.ronda, count(distinct g.area_id) feitas, min(g.data) de, max(g.data) ate
      from public.registos_rega g join public.areas a on a.id = g.area_id and a.activa and a.activista_id = g.activista_id
      where not g.teste and g.data >= (select d from ini) group by 1, 2)
select r.activista_id, ac.nome, ac.supervisor, r.ronda, r.feitas, l.n campos, r.de, r.ate
from r join lista l using (activista_id) join public.activistas ac on ac.id = r.activista_id
where r.feitas >= l.n
  and not exists (select 1 from public.planos_equipa p where p.activista_id = r.activista_id and p.ronda = r.ronda + 1 and p.estado in ('por_supervisor','por_gestor','aprovado'))
  and not exists (select 1 from public.registos_rega g2 where g2.activista_id = r.activista_id and not g2.teste and g2.ronda > r.ronda + 1)
order by r.ate;

-- 2) Dados de uma equipa para o plano_equipa.py (trocar :act e :ronda).
select jsonb_build_object(
  'activista_id', ac.id, 'activista', ac.nome, 'equipa_tamanho', ac.equipa_tamanho, 'ronda', :ronda, 'meta',
  coalesce((select (valor #>> '{}')::int from public.config where chave = 'meta_plantas_pessoa_dia'), 140),
  'areas', (select coalesce(jsonb_agg(jsonb_build_object('id', a.id, 'produtor', a.produtor, 'lat', a.latitude, 'lon', a.longitude,
      'plantas', case when coalesce(a.vivas, 0) > 0 then a.vivas else coalesce(a.instaladas, 0) end)), '[]') from public.areas a where a.activa and a.activista_id = ac.id),
  'regas', (select coalesce(jsonb_agg(jsonb_build_object('area_id', g.area_id, 'data', g.data, 'ronda', g.ronda, 'entrada_em', g.entrada_em, 'saida_em', g.saida_em,
      'entrada_lat', g.entrada_lat, 'entrada_lon', g.entrada_lon, 'plantas_regadas', g.plantas_regadas, 'pessoas', g.pessoas) order by g.entrada_em), '[]')
      from public.registos_rega g where g.activista_id = ac.id and not g.teste and g.ronda = :ronda),
  'jornadas', (select coalesce(jsonb_agg(jsonb_build_object('data', j.data, 'pessoas', j.pessoas)), '[]') from public.jornadas j where j.activista_id = ac.id and not j.teste
      and j.data in (select data from public.registos_rega where activista_id = ac.id and not teste and ronda = :ronda)),
  'percursos', (select coalesce(jsonb_agg(jsonb_build_object('data', p.data, 'pontos', p.pontos)), '[]') from public.percursos p where p.activista_id = ac.id and not p.teste
      and p.data in (select data from public.registos_rega where activista_id = ac.id and not teste and ronda = :ronda))
) from public.activistas ac where ac.id = :act;

-- 3) Gravar o plano (o JSON que o plano_equipa.py devolve), à espera do supervisor:
-- insert into public.planos_equipa (activista_id, ronda, capacidade, pessoas, dias, aprendizagem, notas)
-- select (j->>'activista_id')::uuid, (j->>'ronda')::int, (j->>'capacidade')::int, (j->>'pessoas')::numeric::int, j->'dias', j->'aprendizagem', j->>'notas'
-- from (select '<json>'::jsonb j) x;
