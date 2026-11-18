-- v245 (18/11/2026, Valdo, orientação do Luciano Lima de 18/11): as plantas mórbidas recebem 20 L, as outras 5 L.
-- Na saída da rega a equipa diz quantas plantas receberam 20 L (registos_rega.plantas_20l, dentro de plantas_regadas).
-- Meta: 1 planta a 20 L conta como 4 (config meta_20l_peso) a partir de config meta_20l_inicio (19/11/2026);
-- antes dessa data, e nas regas de versões antigas (plantas_20l null), todas contam como 5 L.
-- Só acrescenta: a app v244 continua a funcionar.

alter table public.registos_rega add column if not exists plantas_20l integer
  check (plantas_20l is null or plantas_20l between 0 and 20000);
comment on column public.registos_rega.plantas_20l is 'v245: plantas mórbidas que receberam 20 L nesta rega (parte de plantas_regadas); null = versão antiga (todas a 5 L)';

insert into public.config (chave, valor) values
  ('meta_20l_inicio', '"2026-11-19"'), ('meta_20l_peso', '4'),
  ('litros_planta', '5'), ('litros_planta_20', '20'),
  ('litros_viagem_min', '300'), ('litros_viagem_max', '350')
on conflict (chave) do nothing;

-- plantas que contam para a meta: as plantas a 20 L contam peso vezes (desde meta_20l_inicio)
create or replace function privado.plantas_eq(p_pl integer, p_20 integer, p_data date)
returns integer language sql stable security definer set search_path to '' as $$
  select coalesce(p_pl, 0) + case
    when p_data >= coalesce((select (valor #>> '{}')::date from public.config where chave = 'meta_20l_inicio'), date '9999-12-31')
    then (coalesce((select (valor #>> '{}')::int from public.config where chave = 'meta_20l_peso'), 4) - 1)
         * least(greatest(coalesce(p_20, 0), 0), coalesce(p_pl, 0))
    else 0 end
$$;
revoke all on function privado.plantas_eq(integer, integer, date) from public;

-- meta_dias2 = meta_dias + plantas_20l e plantas_eq; a % da meta e o pedido de motivo usam as plantas equivalentes.
-- (função nova para não apagar a antiga; painel_meta_causas e meta_por_explicar passam a usar a nova)
create or replace function privado.meta_dias2(p_de date, p_ate date)
 returns table(activista_id uuid, equipa text, tecnico text, supervisor text, data date, campos integer, plantas integer, pessoas integer, meta integer, pct numeric, base integer, mortas integer, vivas_havia integer, cobertura numeric, ini text, fim text, espera_min integer, causas text[], precisa_motivo boolean, motivo text, motivo_por text, motivo_em timestamp with time zone, plantas_20l integer, plantas_eq integer)
 language sql stable security definer set search_path to ''
as $function$
  with cfg as (select
      coalesce((select (valor #>> '{}')::int from public.config where chave = 'meta_plantas_pessoa_dia'), 140) mpp,
      coalesce((select valor #>> '{}' from public.config where chave = 'hora_chegada_equipa'), '06:30') hc,
      coalesce((select (valor #>> '{}')::numeric from public.config where chave = 'meta_limiar_motivo'), 70) lim,
      coalesce((select (valor #>> '{}')::numeric from public.config where chave = 'meta_espera_min'), 60) esp,
      coalesce((select (valor #>> '{}')::numeric from public.config where chave = 'meta_mortas_pct'), 20) mor),
  r as (
    select r.id, r.activista_id, r.data, r.area_id, coalesce(r.plantas_regadas, 0) pl,
      least(coalesce(r.plantas_20l, 0), coalesce(r.plantas_regadas, 0)) p20,
      privado.plantas_eq(r.plantas_regadas, r.plantas_20l, r.data) peq,
      r.pessoas, r.entrada_em, r.saida_em, r.agua_em, coalesce(a.vivas, 0) vb,
      (select coalesce(sum(c.plantas), 0) from public.constrangimentos c where c.registo_id = r.id and c.tipo = 'mudas_secas') mo,
      (select coalesce(bool_or(c.tipo in ('agua_acabou', 'sem_agua_fonte', 'agua_atrasada', 'avaria', 'falta_agua')), false) from public.constrangimentos c where c.registo_id = r.id) ag
    from public.registos_rega r join public.areas a on a.id = r.area_id
    where not r.teste and r.activista_id is not null and r.data between p_de and p_ate),
  d as (
    select r.activista_id, r.data, count(distinct r.area_id)::int campos, sum(r.pl)::int pl, sum(r.p20)::int p20, sum(r.peq)::int peq,
      greatest(coalesce(max(r.pessoas), 0), coalesce((select max(j.pessoas) from public.jornadas j where j.activista_id = r.activista_id and j.data = r.data and not j.teste), 0)) pes,
      sum(r.vb)::int base, sum(r.mo)::int mo,
      sum(greatest(r.vb - r.mo, r.pl))::int havia,
      to_char(min(r.entrada_em at time zone 'Africa/Maputo'), 'HH24:MI') ini, to_char(max(r.saida_em at time zone 'Africa/Maputo'), 'HH24:MI') fim,
      round(coalesce(sum(extract(epoch from (r.agua_em - r.entrada_em)) / 60) filter (where r.agua_em between r.entrada_em and r.saida_em), 0))::int esp,
      bool_or(r.ag) ag
    from r group by r.activista_id, r.data),
  e as (
    select d.*, t.nome, t.tecnico, t.supervisor, cfg.mpp * d.pes meta, cfg.lim, array_remove(array[
        case when d.ini > cfg.hc then 'tarde' end,
        case when d.esp >= cfg.esp then 'espera' end,
        case when d.ag then 'agua' end,
        case when d.mo > 0 and d.mo * 100 >= cfg.mor * d.base and d.base - d.mo < cfg.mpp * d.pes then 'mortas' end,
        case when exists (select 1 from public.dias_sem_rega s where s.activista_id = d.activista_id and not s.removido and not coalesce(s.substituido, false)
                           and d.data between s.data and coalesce(s.ate, s.data)) then 'dia_sem_rega' end], null) causas
    from d join public.activistas t on t.id = d.activista_id, cfg)
  select e.activista_id, e.nome, e.tecnico, e.supervisor, e.data, e.campos, e.pl, e.pes, e.meta,
    case when e.meta > 0 then round(100.0 * e.peq / e.meta, 1) end, e.base, e.mo, e.havia,
    case when e.havia > 0 then round(100.0 * e.pl / e.havia, 1) end, e.ini, e.fim, e.esp, e.causas,
    e.meta > 0 and 100.0 * e.peq / e.meta < e.lim and cardinality(e.causas) = 0,
    m.motivo, m.registado_nome, m.em, e.p20, e.peq
  from e left join public.meta_motivos m on m.activista_id = e.activista_id and m.data = e.data and not m.removido
$function$;
revoke all on function privado.meta_dias2(date, date) from public;

do $do$
declare f text; d text;
begin
  foreach f in array array['public.painel_meta_causas(date,date)', 'public.meta_por_explicar()'] loop
    d := pg_get_functiondef(f::regprocedure);
    if position('privado.meta_dias(' in d) = 0 then continue; end if;
    execute replace(d, 'privado.meta_dias(', 'privado.meta_dias2(');
  end loop;
end $do$;

-- painel › Meta: plantas a 20 L e plantas equivalentes por equipa e dia
create or replace function public.painel_plantas_dia_equipa(p_de date default null, p_ate date default null)
 returns json language plpgsql stable security definer set search_path to ''
as $function$
begin
  if privado.meu_papel() is null or privado.meu_papel() not in ('tecnico','supervisor','gestor','director','me','cliente') then raise exception 'sem acesso'; end if;
  return (select coalesce(json_agg(x order by x.comunidade, x.equipa, x.data), '[]') from (
    select r.data, t.nome as equipa, coalesce(t.comunidade_principal, '—') as comunidade, sum(r.plantas_regadas)::integer as plantas, count(*)::integer as campos,
           coalesce(max(r.pessoas), (select max(j.pessoas) from public.jornadas j where j.activista_id = t.id and j.data = r.data and not j.teste))::integer as pessoas,
           t.equipa_tamanho as tamanho,
           sum(least(coalesce(r.plantas_20l, 0), r.plantas_regadas))::integer as plantas_20l,
           sum(privado.plantas_eq(r.plantas_regadas, r.plantas_20l, r.data))::integer as plantas_eq
    from public.registos_rega r join public.activistas t on t.id = r.activista_id
    where not r.teste and r.plantas_regadas > 0 and (p_de is null or r.data >= p_de) and (p_ate is null or r.data <= p_ate)
    group by r.data, t.id, t.nome, t.comunidade_principal, t.equipa_tamanho) x);
end $function$;

-- água declarada (5 L × plantas a 5 L + 20 L × plantas a 20 L) e água das viagens de tuk-tuk registadas (300–350 L), por equipa e dia
create or replace function privado.agua_dias(p_de date, p_ate date)
 returns table(activista_id uuid, equipa text, tecnico text, supervisor text, data date, regas integer, plantas integer, plantas_20l integer,
   regas_sem_20l integer, litros_declarados integer, viagens integer, outras_voltas integer, regas_sem_tuk integer, litros_viagens_min integer, litros_viagens_max integer)
 language sql stable security definer set search_path to ''
as $function$
  with cfg as (select
      coalesce((select (valor #>> '{}')::numeric from public.config where chave = 'litros_planta'), 5) l5,
      coalesce((select (valor #>> '{}')::numeric from public.config where chave = 'litros_planta_20'), 20) l20,
      coalesce((select (valor #>> '{}')::numeric from public.config where chave = 'litros_viagem_min'), 300) vmin,
      coalesce((select (valor #>> '{}')::numeric from public.config where chave = 'litros_viagem_max'), 350) vmax),
  r as (
    select g.activista_id, g.data, count(*)::int regas, sum(coalesce(g.plantas_regadas, 0))::int pl,
      sum(least(coalesce(g.plantas_20l, 0), coalesce(g.plantas_regadas, 0)))::int p20,
      count(*) filter (where g.plantas_20l is null and coalesce(g.plantas_regadas, 0) > 0)::int sem20,
      count(*) filter (where g.agua_em is not null and g.tuk_codigo is null and g.tuk_outro is null)::int semtuk
    from public.registos_rega g
    where not g.teste and g.activista_id is not null and g.data between p_de and p_ate
    group by 1, 2),
  v as (
    select c.activista_id, c.data, count(*) filter (where c.chegada = 'nova')::int viagens, count(*) filter (where c.extra)::int outras
    from privado.tuk_chegadas(p_de, p_ate) c group by 1, 2)
  select r.activista_id, t.nome, t.tecnico, t.supervisor, r.data, r.regas, r.pl, r.p20, r.sem20,
    round(cfg.l5 * (r.pl - r.p20) + cfg.l20 * r.p20)::int,
    coalesce(v.viagens, 0), coalesce(v.outras, 0), r.semtuk,
    round(cfg.vmin * coalesce(v.viagens, 0))::int, round(cfg.vmax * coalesce(v.viagens, 0))::int
  from r join public.activistas t on t.id = r.activista_id left join v on v.activista_id = r.activista_id and v.data = r.data, cfg
$function$;
revoke all on function privado.agua_dias(date, date) from public;

create or replace function public.painel_agua(p_de date, p_ate date)
 returns json language plpgsql stable security definer set search_path to ''
as $function$
declare v_papel text := privado.meu_papel(); v_hoje date := (now() at time zone 'Africa/Maputo')::date;
  v_ini date := (select (valor #>> '{}')::date from public.config where chave = 'tuktuk_inicio');
begin
  if v_papel is null or v_papel not in ('gestor', 'director', 'me', 'supervisor', 'tecnico', 'cliente') then return null; end if;
  if v_ini is null then return null; end if;
  return json_build_object('inicio', v_ini,
    'meta_20l_inicio', (select valor #>> '{}' from public.config where chave = 'meta_20l_inicio'),
    'litros_planta', (select (valor #>> '{}')::numeric from public.config where chave = 'litros_planta'),
    'litros_planta_20', (select (valor #>> '{}')::numeric from public.config where chave = 'litros_planta_20'),
    'viagem_min', (select (valor #>> '{}')::numeric from public.config where chave = 'litros_viagem_min'),
    'viagem_max', (select (valor #>> '{}')::numeric from public.config where chave = 'litros_viagem_max'),
    'dias', (select coalesce(json_agg(row_to_json(x) order by x.data desc, x.equipa), '[]'::json)
             from privado.agua_dias(greatest(v_ini, coalesce(p_de, v_ini)), least(coalesce(p_ate, v_hoje), v_hoje)) x));
end $function$;
revoke all on function public.painel_agua(date, date) from public, anon;
grant execute on function public.painel_agua(date, date) to authenticated, service_role;

-- «O meu dia»: plantas a 20 L, plantas equivalentes e pessoas por equipa (para a % da meta)
do $do$
declare d text := pg_get_functiondef('public.meu_dia(date)'::regprocedure);
  o text := $x$'plantas', (select coalesce(sum(r.plantas_regadas), 0) from public.registos_rega r where r.activista_id = t.id and r.data = v_d and not r.teste),$x$;
begin
  if position('plantas_eq' in d) > 0 then return; end if;
  if position(o in d) = 0 then raise exception 'meu_dia: linha das plantas não encontrada'; end if;
  d := replace(d, o, o || $x$
        'plantas_20l', (select coalesce(sum(least(coalesce(r.plantas_20l, 0), coalesce(r.plantas_regadas, 0))), 0) from public.registos_rega r where r.activista_id = t.id and r.data = v_d and not r.teste),
        'plantas_eq', (select coalesce(sum(privado.plantas_eq(r.plantas_regadas, r.plantas_20l, r.data)), 0) from public.registos_rega r where r.activista_id = t.id and r.data = v_d and not r.teste),
        'pessoas', greatest((select coalesce(max(r.pessoas), 0) from public.registos_rega r where r.activista_id = t.id and r.data = v_d and not r.teste),
                            (select coalesce(max(j.pessoas), 0) from public.jornadas j where j.activista_id = t.id and j.data = v_d and not j.teste)),
        'meta_pessoa', coalesce((select (valor #>> '{}')::int from public.config where chave = 'meta_plantas_pessoa_dia'), 140),$x$);
  execute d;
end $do$;
