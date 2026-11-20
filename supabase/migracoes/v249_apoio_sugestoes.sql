-- v249 (20/11/2026): apoio_sugestoes() mais rápida. A versão anterior chamava privado.apoio_candidatos() por cada par de equipas,
-- e cada chamada voltava a calcular privado.rondas() e privado.regas_contadas() (6,7 s para o Nuro).
-- Esta calcula as rondas e as regas contadas uma só vez. Mesmo resultado (mesmos campos, filtros e ordem).
create or replace function public.apoio_sugestoes()
 returns jsonb
 language plpgsql
 stable security definer
 set search_path to ''
as $function$
declare v_papel text := privado.meu_papel(); v_ids uuid[];
begin
  if v_papel is null or v_papel not in ('tecnico','supervisor','gestor') then return null; end if;
  v_ids := case when v_papel = 'gestor' or privado.ve_tudo() then (select array_agg(id) from public.activistas) else coalesce(privado.ids_visiveis(), '{}'::uuid[]) end;
  return coalesce((
    with cfg as (select coalesce((select (valor #>> '{}')::double precision from public.config where chave = 'apoio_distancia_m'), 5000) mx),
    ro as materialized (select * from privado.rondas()),
    pares as materialized (
      select h.activista_id ajuda, ha.nome ajuda_nome, h.ronda_actual ajuda_ronda, t.activista_id para, pa.nome para_nome, t.ronda_actual para_ronda,
             t.lista para_lista, t.regadas_ronda para_regadas
      from ro h join public.activistas ha on ha.id = h.activista_id and ha.activo
      join ro t on t.ronda_actual < h.ronda_actual and t.activista_id <> h.activista_id
      join public.activistas pa on pa.id = t.activista_id and pa.activo
      where (h.activista_id = any(v_ids) or t.activista_id = any(v_ids))
        and not exists (select 1 from public.apoios p where p.ajuda_activista_id = h.activista_id and p.terminado_em is null)),
    feitos as materialized (
      select distinct c.dono, c.area_id from privado.regas_contadas() c join ro on ro.activista_id = c.dono
      where coalesce(c.campo_fechado, true) and c.ronda = coalesce(ro.ronda_actual, 1)),
    em_apoio as materialized (select distinct x from public.apoios p, unnest(p.area_ids) x where p.terminado_em is null),
    regadas as materialized (select distinct r.area_id from public.registos_rega r where not r.teste and r.plantas_regadas > 0),
    cand as (
      select p.ajuda, p.para, t.id, coalesce(nullif(t.vivas,0), t.instaladas, 0)::int plantas,
             round(min(privado.dist_m(h.latitude, h.longitude, t.latitude, t.longitude)))::int dist_m,
             t.id not in (select area_id from regadas)
               and (coalesce(array_length(t.datas_rega_origem,1),0) = 0 or coalesce(t.regas_origem_por_pr,false)) nunca
      from pares p
      join public.areas t on t.activista_id = p.para and t.activa and t.latitude is not null
      join public.areas h on h.activista_id = p.ajuda and h.activa and h.latitude is not null
      cross join cfg
      where t.id not in (select x from em_apoio)
        and not exists (select 1 from feitos f where f.dono = p.para and f.area_id = t.id)
      group by p.ajuda, p.para, t.id, t.vivas, t.instaladas, t.datas_rega_origem, t.regas_origem_por_pr, cfg.mx
      having min(privado.dist_m(h.latitude, h.longitude, t.latitude, t.longitude)) <= cfg.mx),
    agg as (
      select ajuda, para, count(*)::int campos, count(*) filter (where nunca)::int nunca, coalesce(sum(plantas),0)::int plantas, min(dist_m)::int dist_min
      from cand group by ajuda, para),
    s as (
      select p.ajuda ajuda_id, p.ajuda_nome, p.ajuda_ronda, p.para para_id, p.para_nome, p.para_ronda, p.para_lista, p.para_regadas,
             a.campos, a.nunca, a.plantas, a.dist_min
      from pares p join agg a on a.ajuda = p.ajuda and a.para = p.para)
    select jsonb_agg(to_jsonb(s) order by s.nunca desc, s.campos desc) from s), '[]'::jsonb);
end $function$;
