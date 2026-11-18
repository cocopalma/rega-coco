-- v246 (18/11/2026, Valdo, decisões de 17/11 20:47 e 18/11 12:08): quando a equipa fica abaixo da meta do dia
-- (140 plantas por pessoa; 1 planta a 20 L = 4), a equipa escolhe o motivo numa lista (com «outro» para escrever).
-- Não se pede o motivo quando a app já sabe a causa: chegada ao 1.º campo depois da hora combinada, ou viagens de
-- tuk-tuk a menos: menos de config.meta_viagens_minimas (3) viagens nesse dia, OU viagens × litros_viagem_max < meta × litros_planta
-- (Valdo, 18/11/2026 17:35: «A e B»).
-- Também não se pede quando já há um motivo de dia sem rega para esse dia. Conta a partir de config.meta_motivo2_inicio.
-- Precisa da migração v245 (privado.meta_dias2, privado.agua_dias). Só acrescenta.

alter table public.meta_motivos add column if not exists tipo text;
alter table public.meta_motivos add column if not exists papel text;

insert into public.config (chave, valor) values ('meta_motivo2_inicio', '"2026-11-20"'), ('meta_viagens_minimas', '3') on conflict (chave) do nothing;

create or replace function privado.meta_dias3(p_de date, p_ate date)
 returns table(activista_id uuid, equipa text, tecnico text, supervisor text, data date, campos integer, plantas integer, pessoas integer, meta integer, pct numeric, base integer, mortas integer, vivas_havia integer, cobertura numeric, ini text, fim text, espera_min integer, causas text[], precisa_motivo boolean, motivo text, motivo_por text, motivo_em timestamp with time zone, plantas_20l integer, plantas_eq integer,
   viagens integer, litros_viagens_max integer, agua_meta integer, tarde boolean, poucas_viagens boolean, motivo_tipo text, precisa_motivo2 boolean)
 language sql stable security definer set search_path to ''
as $function$
  with cfg as (select
      coalesce((select (valor #>> '{}')::date from public.config where chave = 'meta_motivo2_inicio'), date '9999-12-31') ini2,
      coalesce((select (valor #>> '{}')::numeric from public.config where chave = 'litros_planta'), 5) l5,
      coalesce((select valor #>> '{}' from public.config where chave = 'hora_chegada_equipa'), '06:30') hc,
      (select (valor #>> '{}')::int from public.config where chave = 'meta_viagens_minimas') vmin)
  select m.*, coalesce(a.viagens, 0), coalesce(a.litros_viagens_max, 0), round(m.meta * cfg.l5)::int,
    coalesce(m.ini > cfg.hc, false), x.pv, mm.tipo,
    m.data >= cfg.ini2 and m.meta > 0 and m.plantas_eq < m.meta and not coalesce(m.ini > cfg.hc, false) and not x.pv
      and not ('dia_sem_rega' = any (m.causas))
  from privado.meta_dias2(p_de, p_ate) m cross join cfg
  left join privado.agua_dias(p_de, p_ate) a on a.activista_id = m.activista_id and a.data = m.data
  left join public.meta_motivos mm on mm.activista_id = m.activista_id and mm.data = m.data and not mm.removido
  -- poucas viagens: menos de config.meta_viagens_minimas viagens, ou viagens que não traziam a água da meta (as duas regras valem)
  cross join lateral (select (coalesce(a.viagens, 0) < coalesce(cfg.vmin, 0) or coalesce(a.litros_viagens_max, 0) < m.meta * cfg.l5)
      and not exists (select 1 from public.registos_rega r where r.activista_id = m.activista_id and r.data = m.data and not r.teste and r.tuk_chegada = 'ja_estava') as pv) x
$function$;
revoke all on function privado.meta_dias3(date, date) from public;

-- painel e «O meu dia» do técnico/supervisor passam a usar meta_dias3 (antes de meta_motivo2_inicio continua a regra da v226)
do $do$
declare d text;
begin
  d := pg_get_functiondef('public.painel_meta_causas(date,date)'::regprocedure);
  if position('privado.meta_dias3(' in d) = 0 then
    if position('privado.meta_dias2(' in d) = 0 then raise exception 'painel_meta_causas: aplicar primeiro a v245'; end if;
    d := replace(d, 'privado.meta_dias2(', 'privado.meta_dias3(');
    d := replace(d, $x$'motivo_inicio', (select valor #>> '{}' from public.config where chave = 'meta_motivo_inicio'),$x$,
      $x$'motivo_inicio', (select valor #>> '{}' from public.config where chave = 'meta_motivo_inicio'),
    'motivo2_inicio', (select valor #>> '{}' from public.config where chave = 'meta_motivo2_inicio'),$x$);
    execute d;
  end if;
end $do$;

create or replace function public.meta_por_explicar()
 returns json language plpgsql stable security definer set search_path to ''
as $function$
declare v_p text := privado.meu_papel(); v_agora timestamp := now() at time zone 'Africa/Maputo'; v_hoje date := v_agora::date;
  v_ini date := coalesce((select (valor #>> '{}')::date from public.config where chave = 'meta_motivo_inicio'), v_hoje);
  v_ate date := case when v_agora::time >= time '18:00' then v_hoje else v_hoje - 1 end;
begin
  if coalesce(v_p, '') not in ('tecnico', 'supervisor') or privado.ve_tudo() or privado.so_teste() then return '[]'::json; end if;
  return (select coalesce(json_agg(row_to_json(x) order by x.data desc, x.equipa), '[]')
          from privado.meta_dias3(greatest(v_ini, v_hoje - 7), v_ate) x
          where (x.precisa_motivo2 or (x.precisa_motivo and x.data < coalesce((select (valor #>> '{}')::date from public.config where chave = 'meta_motivo2_inicio'), date '9999-12-31')))
            and x.motivo is null and x.activista_id = any (privado.ids_visiveis()));
end $function$;

-- activista: dias da sua equipa abaixo da meta, sem causa conhecida e sem motivo (últimos 7 dias, desde meta_motivo2_inicio, até hoje)
create or replace function public.meta_pendentes_equipa()
 returns json language plpgsql stable security definer set search_path to ''
as $function$
declare v_act uuid; v_hoje date := (now() at time zone 'Africa/Maputo')::date;
  v_ini date := coalesce((select (valor #>> '{}')::date from public.config where chave = 'meta_motivo2_inicio'), date '9999-12-31');
begin
  if coalesce(privado.meu_papel(), '') <> 'activista' then return '[]'::json; end if;
  select p.activista_id into v_act from public.perfis p where p.id = auth.uid();
  if v_act is null or v_ini > v_hoje then return '[]'::json; end if;
  return (select coalesce(json_agg(row_to_json(x) order by x.data desc), '[]')
          from privado.meta_dias3(greatest(v_ini, v_hoje - 7), v_hoje) x
          where x.activista_id = v_act and x.precisa_motivo2 and x.motivo is null);
end $function$;
revoke all on function public.meta_pendentes_equipa() from public, anon;
grant execute on function public.meta_pendentes_equipa() to authenticated, service_role;

-- motivo escolhido na lista (activista da equipa, técnico/supervisor da equipa, gestor)
create or replace function public.gravar_meta_motivo2(p_id text, p_activista uuid, p_data date, p_tipo text, p_texto text)
 returns json language plpgsql security definer set search_path to ''
as $function$
declare v_p text := privado.meu_papel(); v_hoje date := (now() at time zone 'Africa/Maputo')::date; v_nome text; v_rot text; v_txt text := nullif(trim(coalesce(p_texto, '')), '');
begin
  if coalesce(v_p, '') not in ('activista', 'tecnico', 'supervisor', 'gestor') then raise exception 'sem acesso'; end if;
  if v_p = 'activista' and (select p.activista_id from public.perfis p where p.id = auth.uid()) is distinct from p_activista then raise exception 'Esta equipa não é sua.'; end if;
  if v_p in ('tecnico', 'supervisor') and not privado.equipa_minha(p_activista) then raise exception 'Esta equipa não é sua.'; end if;
  v_rot := case p_tipo
    when 'tuk_tarde' then 'O tuk-tuk chegou tarde'
    when 'avaria' then 'Avaria do tuk-tuk, do camião ou da bomba'
    when 'sem_agua_fonte' then 'Não havia água na fonte'
    when 'agua_acabou' then 'A água acabou'
    when 'chuva' then 'Choveu'
    when 'material' then 'Faltou material'
    when 'doenca' then 'Uma pessoa saiu a meio por doença'
    when 'outro' then 'Outro motivo' end;
  if v_rot is null then raise exception 'Escolha o motivo.'; end if;
  if p_tipo in ('material', 'outro') and length(coalesce(v_txt, '')) < 3 then raise exception 'Escreva o que aconteceu.'; end if;
  if p_data is null or p_data > v_hoje or p_data < v_hoje - 14 then raise exception 'Data fora do prazo (últimos 14 dias).'; end if;
  select nome into v_nome from public.perfis where id = auth.uid();
  update public.meta_motivos set removido = true where activista_id = p_activista and data = p_data and not removido and id <> p_id;
  insert into public.meta_motivos (id, activista_id, data, motivo, tipo, papel, registado_por, registado_nome)
  values (p_id, p_activista, p_data, v_rot || coalesce(': ' || v_txt, ''), p_tipo, v_p, auth.uid(), v_nome)
  on conflict (id) do update set motivo = excluded.motivo, tipo = excluded.tipo, papel = excluded.papel, em = now(), removido = false;
  return json_build_object('ok', true);
end $function$;
revoke all on function public.gravar_meta_motivo2(text, uuid, date, text, text) from public, anon;
grant execute on function public.gravar_meta_motivo2(text, uuid, date, text, text) to authenticated, service_role;
