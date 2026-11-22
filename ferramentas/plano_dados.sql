-- Planos das equipas (v3, 22/11/2026, Valdo). Consultas para o Claude correr no Supabase (execute_sql). Instruções: PLANOS_EQUIPAS.md.

-- 1) Equipas que precisam de plano: falta o plano (por aprovar ou aprovado) da ronda em que estão ou da ronda seguinte.
with ro as (select activista_id, ronda_actual from privado.rondas()),
lista as (select activista_id, count(*) n from public.areas where activa and activista_id is not null group by 1),
pl as (select activista_id, ronda from public.planos_equipa where estado in ('por_supervisor','por_gestor','aprovado'))
select ro.activista_id, ac.nome, ac.supervisor, ro.ronda_actual,
       exists (select 1 from pl where pl.activista_id = ro.activista_id and pl.ronda = ro.ronda_actual) tem_plano_actual,
       exists (select 1 from pl where pl.activista_id = ro.activista_id and pl.ronda = ro.ronda_actual + 1) tem_plano_seguinte
from ro join lista l using (activista_id) join public.activistas ac on ac.id = ro.activista_id and ac.activo
where exists (select 1 from public.registos_rega g where g.activista_id = ro.activista_id and not g.teste and g.data >= current_date - 14)
  and not (exists (select 1 from pl where pl.activista_id = ro.activista_id and pl.ronda = ro.ronda_actual)
       and exists (select 1 from pl where pl.activista_id = ro.activista_id and pl.ronda = ro.ronda_actual + 1))
order by ac.nome;

-- 2) Dados de uma equipa para o plano_equipa.py (trocar :act). O resultado é grande: o conector guarda-o num ficheiro.
with ro as (select activista_id, ronda_actual ra from privado.rondas() where activista_id = :act),
ar as (select a.* from public.areas a where a.activa and a.activista_id = :act),
rg as (select g.*, row_number() over (partition by g.data order by g.entrada_em) k from public.registos_rega g
       where g.activista_id = :act and not g.teste and g.saida_em is not null and g.data >= current_date - 30
         and g.saida_em - g.entrada_em < interval '8 hours')
select jsonb_build_object(
  'activista_id', ac.id, 'activista', ac.nome, 'equipa_tamanho', ac.equipa_tamanho, 'ronda', ro.ra,
  'meta', coalesce((select (valor #>> '{}')::int from public.config where chave = 'meta_plantas_pessoa_dia'), 140),
  'tem_plano_actual', exists (select 1 from public.planos_equipa p where p.activista_id = ac.id and p.ronda = ro.ra and p.estado in ('por_supervisor','por_gestor','aprovado')),
  'areas', (select coalesce(jsonb_agg(jsonb_build_object('id', a.id, 'produtor', a.produtor, 'lat', a.latitude, 'lon', a.longitude,
      'plantas', case when coalesce(a.vivas, 0) > 0 then a.vivas else coalesce(a.instaladas, 0) end,
      -- feito nesta ronda (pela regra da app: campo fechado), quando, e plantas regadas nesta ronda e na ronda anterior em que foi regado
      'feito_ronda', exists (select 1 from privado.regas_contadas() c where c.area_id = a.id and c.dono = ac.id and c.ronda = ro.ra and coalesce(c.campo_fechado, true)),
      'feito_em', (select min(g.data) from public.registos_rega g where g.area_id = a.id and not g.teste and g.ronda = ro.ra),
      'pl_actual', (select sum(g.plantas_regadas) from public.registos_rega g where g.area_id = a.id and not g.teste and g.ronda = ro.ra and g.data >= '2026-10-24'),
      'pl_anterior', (select sum(g.plantas_regadas) from public.registos_rega g where g.area_id = a.id and not g.teste and g.data >= '2026-10-24'
          and g.ronda = (select max(g2.ronda) from public.registos_rega g2 where g2.area_id = a.id and not g2.teste and g2.ronda < ro.ra and g2.data >= '2026-10-24'))
    )), '[]') from ar a),
  'regas', (select coalesce(jsonb_agg(jsonb_build_object('d', g.data, 'a', g.area_id, 'k', g.k, 'e', extract(epoch from g.entrada_em)::int, 's', extract(epoch from g.saida_em)::int,
      'w', case when g.agua_em between g.entrada_em and g.saida_em then extract(epoch from g.agua_em)::int end, 'p', g.plantas_regadas, 'n', g.pessoas) order by g.entrada_em), '[]') from rg g),
  'pos', (select coalesce(jsonb_object_agg(a.id, jsonb_build_array(a.latitude, a.longitude)), '{}') from public.areas a
      where a.latitude is not null and a.id in (select area_id from rg))
) from public.activistas ac, ro where ac.id = :act;

-- 3) Gravar (o JSON que o plano_equipa.py devolve é uma lista de planos): os planos por aprovar da mesma equipa e ronda passam a
-- «substituido» e entram os novos, à espera do supervisor (depois o gestor principal).
-- update public.planos_equipa set estado = 'substituido' where activista_id = '<act>' and ronda = <ronda> and estado in ('por_supervisor','por_gestor');
-- insert into public.planos_equipa (activista_id, ronda, capacidade, pessoas, dias, aprendizagem, notas)
-- select (j->>'activista_id')::uuid, (j->>'ronda')::int, (j->>'capacidade')::int, round((j->>'pessoas')::numeric)::int, j->'dias', j->'aprendizagem', j->>'notas'
-- from jsonb_array_elements('<json>'::jsonb) j;
