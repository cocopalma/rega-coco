-- v248 (20/11/2026, Valdo, decisões de 20/11; partes 2 e 3 do pacote da v247). Só acrescenta.
-- Parte 2: sobrevivência indicativa pela cava-roda e mulching. Quando o técnico ou o supervisor conclui um campo (todas as plantas vivas
--   encontradas com cava-roda), a sobrevivência indicativa = plantas com cava-roda ÷ plantas instaladas (no máximo 100 %). Não muda as vivas
--   da base; quem dá a sobrevivência real é o M&E: se as plantas com cava-roda forem menos do que as vivas da base, fica pedida
--   automaticamente uma recontagem ao M&E. Cada registo de cava-roda pode ir até às plantas instaladas (antes: até às vivas da base).
-- Parte 3: campos do itinerário do plano que ficaram por regar no dia: o activista diz o motivo de cada um e o dia do itinerário fecha;
--   os campos que ficaram passam para o dia seguinte do plano. Equipas sem plano aprovado continuam pela ronda (nada muda).

-- ===== Parte 2 =====
create table if not exists public.conclusoes_campo (
  id uuid primary key default gen_random_uuid(),
  area_id text not null,
  concluido_em timestamptz not null default now(),
  concluido_por uuid not null,
  papel text,
  cavaroda integer not null,
  mulching integer not null,
  instaladas integer,
  vivas_base integer,
  fonte text,                       -- 'actividades' (cava-roda da equipa) ou 'manutencao' (Quiwia e Farol)
  recontagem_id uuid,
  removido boolean not null default false,
  removido_em timestamptz, removido_por uuid, motivo_remocao text);
alter table public.conclusoes_campo enable row level security;
create unique index if not exists conclusoes_campo_activa on public.conclusoes_campo (area_id) where not removido;
create trigger guarda_so_teste before insert or delete or update on public.conclusoes_campo for each row execute function privado.guarda_so_teste();

-- plantas com cava-roda e mulching num campo: em Quiwia e Farol o último total da manutenção; nos outros a soma da cava-roda da equipa
create or replace function privado.cavaroda_campo(p_area text, out cavaroda integer, out mulching integer, out fonte text)
 language plpgsql stable security definer set search_path to ''
as $function$
declare a record;
begin
  select ar.comunidade into a from public.areas ar where ar.id = p_area;
  if exists (select 1 from public.manutencao_comunidades c where c.comunidade = a.comunidade) then
    select r.cavaroda, r.mulching into cavaroda, mulching from public.manutencao_registos r
      where r.area_id = p_area and not r.removido and privado.manut_conta(r.feito_em) order by r.feito_em desc limit 1;
    fonte := 'manutencao';
  else
    select coalesce(sum(x.cavaroda), 0), coalesce(sum(x.mulching), 0) into cavaroda, mulching from public.actividades_campo x
      where x.area_id = p_area and not x.removido;
    fonte := 'actividades';
  end if;
  cavaroda := coalesce(cavaroda, 0); mulching := coalesce(mulching, 0);
end $function$;
revoke all on function privado.cavaroda_campo(text) from public;

create or replace function privado.pode_concluir(p_area text) returns boolean
 language sql stable security definer set search_path to ''
as $function$
  select coalesce(privado.meu_papel(), '') in ('tecnico', 'supervisor', 'gestor') and not coalesce(privado.so_teste(), false)
    and (privado.meu_papel() = 'gestor'
      or exists (select 1 from public.areas a where a.id = p_area and privado.ve_area(a.activista_id, a.comunidade))
      or (exists (select 1 from public.areas a join public.manutencao_comunidades c on c.comunidade = a.comunidade where a.id = p_area)
          and coalesce(privado.manut_acesso(), '') in ('escreve', 'regista')))
$function$;
revoke all on function privado.pode_concluir(text) from public;

-- o que a ficha mostra: totais, plantas do campo, conclusão (se houver) e se a pessoa pode concluir
create or replace function public.conclusao_campo(p_area text) returns json
 language plpgsql stable security definer set search_path to ''
as $function$
declare a record; t record; c record;
begin
  select ar.id, ar.activista_id, ar.comunidade, ar.instaladas, ar.vivas into a from public.areas ar where ar.id = p_area;
  if a.id is null or not (privado.le_area(a.activista_id, a.comunidade) or coalesce(privado.manut_acesso(), '') <> '') then return null; end if;
  select * into t from privado.cavaroda_campo(p_area);
  select k.*, pf.nome quem, r.estado rec_estado into c from public.conclusoes_campo k left join public.perfis pf on pf.id = k.concluido_por
    left join public.recontagens r on r.id = k.recontagem_id where k.area_id = p_area and not k.removido;
  return json_build_object('cavaroda', t.cavaroda, 'mulching', t.mulching, 'fonte', t.fonte, 'instaladas', a.instaladas, 'vivas', a.vivas,
    'pode', privado.pode_concluir(p_area),
    'conclusao', case when c.id is null then null else json_build_object('id', c.id, 'em', c.concluido_em, 'quem', c.quem, 'meu', c.concluido_por = auth.uid(),
      'cavaroda', c.cavaroda, 'mulching', c.mulching, 'instaladas', c.instaladas, 'vivas_base', c.vivas_base,
      'sobrevivencia', case when coalesce(c.instaladas, 0) > 0 then round(100.0 * least(c.cavaroda, c.instaladas) / c.instaladas, 1) end,
      'recontagem', c.recontagem_id is not null, 'recontagem_estado', c.rec_estado) end);
end $function$;
revoke all on function public.conclusao_campo(text) from public, anon;
grant execute on function public.conclusao_campo(text) to authenticated, service_role;

create or replace function public.concluir_cavaroda(p_area text, p_em timestamptz default null) returns json
 language plpgsql security definer set search_path to ''
as $function$
declare a record; t record; v_id uuid; v_rec uuid; v_ja uuid; v_em timestamptz := least(coalesce(p_em, now()), now());
begin
  if not privado.pode_concluir(p_area) then raise exception 'Só o técnico, o supervisor ou o gestor do campo concluem a cava-roda e o mulching'; end if;
  select ar.id, ar.comunidade, ar.instaladas, ar.vivas into a from public.areas ar where ar.id = p_area;
  if a.id is null then raise exception 'Campo não encontrado'; end if;
  select k.id into v_ja from public.conclusoes_campo k where k.area_id = p_area and not k.removido;
  if v_ja is not null then return json_build_object('id', v_ja, 'ja', true); end if;
  select * into t from privado.cavaroda_campo(p_area);
  if t.cavaroda < 1 then raise exception 'Este campo ainda não tem plantas com cava-roda registadas'; end if;
  if coalesce(a.instaladas, 0) < 1 then raise exception 'Este campo não tem plantas instaladas na base: não se calcula a sobrevivência'; end if;
  insert into public.conclusoes_campo (area_id, concluido_em, concluido_por, papel, cavaroda, mulching, instaladas, vivas_base, fonte)
    values (p_area, v_em, auth.uid(), privado.meu_papel(), least(t.cavaroda, a.instaladas), least(t.mulching, a.instaladas), a.instaladas, a.vivas, t.fonte)
    returning id into v_id;
  -- menos plantas com cava-roda do que as vivas da base: recontagem pedida ao M&E (se ainda não houver uma em curso)
  if least(t.cavaroda, a.instaladas) < coalesce(a.vivas, 0)
     and not exists (select 1 from public.recontagens r where r.area_id = p_area and r.estado in ('por_encaminhar', 'encaminhada', 'enviada', 'recusada')) then
    insert into public.recontagens (area_id, motivo, estado, pedido_por, pedido_em)
      values (p_area, 'Cava-roda e mulching concluídos com ' || least(t.cavaroda, a.instaladas) || ' plantas vivas encontradas; na base ' || a.vivas || ' vivas (pedido automático)',
        'por_encaminhar', auth.uid(), now()) returning id into v_rec;
    update public.conclusoes_campo set recontagem_id = v_rec where id = v_id;
  end if;
  -- Quiwia e Farol: concluir é o mesmo que «feito» na manutenção
  if t.fonte = 'manutencao' then
    insert into public.manutencao_feitos (area_id, feito, marcado_por, marcado_em) values (p_area, true, auth.uid(), v_em)
      on conflict (area_id) do update set feito = true, marcado_por = excluded.marcado_por, marcado_em = excluded.marcado_em;
  end if;
  return json_build_object('id', v_id, 'recontagem', v_rec is not null,
    'sobrevivencia', round(100.0 * least(t.cavaroda, a.instaladas) / a.instaladas, 1));
end $function$;
revoke all on function public.concluir_cavaroda(text, timestamptz) from public, anon;
grant execute on function public.concluir_cavaroda(text, timestamptz) to authenticated, service_role;

create or replace function public.anular_conclusao_cavaroda(p_id uuid, p_motivo text) returns json
 language plpgsql security definer set search_path to ''
as $function$
declare c record;
begin
  select * into c from public.conclusoes_campo where id = p_id and not removido;
  if c.id is null then return json_build_object('ja', true); end if;
  if not (c.concluido_por = auth.uid() or privado.meu_papel() = 'gestor') then raise exception 'Só quem concluiu ou o gestor anula a conclusão'; end if;
  if length(trim(coalesce(p_motivo, ''))) < 3 then raise exception 'Escreva o motivo'; end if;
  update public.conclusoes_campo set removido = true, removido_em = now(), removido_por = auth.uid(), motivo_remocao = trim(p_motivo) where id = p_id;
  update public.recontagens set estado = 'cancelada' where id = c.recontagem_id and estado = 'por_encaminhar';
  if c.fonte = 'manutencao' then update public.manutencao_feitos set feito = false where area_id = c.area_id and feito; end if;
  return json_build_object('ok', true);
end $function$;
revoke all on function public.anular_conclusao_cavaroda(uuid, text) from public, anon;
grant execute on function public.anular_conclusao_cavaroda(uuid, text) to authenticated, service_role;

-- painel › Sobrevivência indicativa (campos concluídos no período; sem período = todos)
create or replace function public.painel_sobrevivencia(p_de date, p_ate date) returns json
 language plpgsql stable security definer set search_path to ''
as $function$
declare v_p text := privado.meu_papel();
begin
  if coalesce(v_p, '') not in ('gestor', 'director', 'me', 'supervisor', 'tecnico', 'cliente') then return null; end if;
  return json_build_object(
    'campos', (select coalesce(json_agg(json_build_object('area_id', a.id, 'pr', a.pr, 'area_n', a.area_n, 'produtor', a.produtor, 'comunidade', a.comunidade,
        'zona', a.zona, 'equipa', t.nome, 'tecnico', t.tecnico, 'supervisor', t.supervisor, 'instaladas', k.instaladas, 'vivas_base', k.vivas_base,
        'cavaroda', k.cavaroda, 'mulching', k.mulching, 'fonte', k.fonte,
        'sobrevivencia', case when coalesce(k.instaladas, 0) > 0 then round(100.0 * least(k.cavaroda, k.instaladas) / k.instaladas, 1) end,
        'data', (k.concluido_em at time zone 'Africa/Maputo')::date, 'quem', pf.nome, 'recontagem', k.recontagem_id is not null, 'recontagem_estado', r.estado,
        'vivas_recontadas', case when r.estado = 'validada' then r.vivas end) order by k.concluido_em desc), '[]')
      from public.conclusoes_campo k join public.areas a on a.id = k.area_id left join public.activistas t on t.id = a.activista_id
        left join public.perfis pf on pf.id = k.concluido_por left join public.recontagens r on r.id = k.recontagem_id
      where not k.removido and (p_de is null or (k.concluido_em at time zone 'Africa/Maputo')::date >= p_de)
        and (p_ate is null or (k.concluido_em at time zone 'Africa/Maputo')::date <= p_ate)
        and (v_p in ('gestor', 'director', 'me', 'cliente') or privado.le_area(a.activista_id, a.comunidade))),
    -- campos marcados «feito» na manutenção antes da v248 (o total era posto igual às vivas da base): ficam de fora da sobrevivência
    'feitos_antigos', (select count(*) from public.manutencao_feitos f where f.feito and not exists (select 1 from public.conclusoes_campo k where k.area_id = f.area_id and not k.removido)));
end $function$;
revoke all on function public.painel_sobrevivencia(date, date) from public, anon;
grant execute on function public.painel_sobrevivencia(date, date) to authenticated, service_role;

-- cada registo de cava-roda pode ir até às plantas instaladas (para registar plantas vivas encontradas a mais do que a base)
do $do$
declare d text; n text;
begin
  d := pg_get_functiondef('public.gravar_actividade(jsonb)'::regprocedure);
  if position('greatest(n, coalesce' in d) = 0 then
    n := replace(d, $x$if n > 0 and (v_cav > n or v_mul > n) then raise exception 'Mais plantas do que as % do campo', n; end if;$x$,
      $x$if n > 0 and (v_cav > greatest(n, coalesce((select ar.instaladas from public.areas ar where ar.id = v_area), 0)) or v_mul > greatest(n, coalesce((select ar.instaladas from public.areas ar where ar.id = v_area), 0)))
    then raise exception 'Mais plantas do que as % instaladas no campo', greatest(n, coalesce((select ar.instaladas from public.areas ar where ar.id = v_area), 0)); end if;$x$);
    if n = d then raise exception 'gravar_actividade: texto esperado não encontrado'; end if;
    execute n;
  end if;
end $do$;

-- ===== Parte 3 =====
create table if not exists public.itinerario_fechos (
  plano_id uuid not null, dia_n integer not null, data date not null, activista_id uuid not null,
  user_id uuid not null, fechado_em timestamptz not null default now(), primary key (plano_id, dia_n));
create table if not exists public.itinerario_falhas (
  id uuid primary key default gen_random_uuid(), plano_id uuid not null, dia_n integer not null, data date not null,
  area_id text not null, activista_id uuid not null, motivo text not null, texto text, user_id uuid not null, em timestamptz not null default now());
alter table public.itinerario_fechos enable row level security;
alter table public.itinerario_falhas enable row level security;
create unique index if not exists itinerario_falhas_um on public.itinerario_falhas (plano_id, dia_n, area_id);
create trigger guarda_so_teste before insert or delete or update on public.itinerario_fechos for each row execute function privado.guarda_so_teste();
create trigger guarda_so_teste before insert or delete or update on public.itinerario_falhas for each row execute function privado.guarda_so_teste();

-- estado do itinerário de um plano: dias fechados, campos que ficaram (com o motivo) e o último dia em que cada dia do plano teve regas
create or replace function public.itinerario_estado(p_plano uuid) returns json
 language plpgsql stable security definer set search_path to ''
as $function$
declare p record; v_pp text := privado.meu_papel(); v_meu uuid;
begin
  select pl.id, pl.activista_id into p from public.planos_equipa pl where pl.id = p_plano;
  if p.id is null then return null; end if;
  if v_pp = 'activista' then select pf.activista_id into v_meu from public.perfis pf where pf.id = auth.uid(); if v_meu is distinct from p.activista_id then return null; end if;
  elsif not (v_pp in ('gestor', 'director', 'me') or p.activista_id = any (coalesce(privado.ids_visiveis(), '{}'))) then return null; end if;
  return json_build_object(
    'fechos', (select coalesce(json_agg(json_build_object('dia_n', f.dia_n, 'data', f.data) order by f.dia_n), '[]') from public.itinerario_fechos f where f.plano_id = p_plano),
    'falhas', (select coalesce(json_agg(json_build_object('dia_n', x.dia_n, 'data', x.data, 'area_id', x.area_id, 'produtor', a.produtor, 'motivo', x.motivo, 'texto', x.texto, 'quem', pf.nome) order by x.dia_n, x.em), '[]')
      from public.itinerario_falhas x left join public.areas a on a.id = x.area_id left join public.perfis pf on pf.id = x.user_id where x.plano_id = p_plano),
    'trabalhados', (select coalesce(json_agg(json_build_object('dia_n', q.plano_dia, 'data', q.d) order by q.plano_dia), '[]')
      from (select r.plano_dia, max(r.data) d from public.registos_rega r where r.plano_id = p_plano and not r.teste and r.plano_dia is not null group by r.plano_dia) q));
end $function$;
revoke all on function public.itinerario_estado(uuid) from public, anon;
grant execute on function public.itinerario_estado(uuid) to authenticated, service_role;

-- fim do dia do itinerário: um motivo por campo que ficou por regar (p_falhas = [{area_id, motivo, texto}]); o dia fecha
create or replace function public.fechar_itinerario_dia(p_plano uuid, p_dia integer, p_data date, p_falhas jsonb) returns json
 language plpgsql security definer set search_path to ''
as $function$
declare p record; v_pp text := privado.meu_papel(); v_meu uuid; f jsonb; v_m text; v_t text; v_hoje date := (now() at time zone 'Africa/Maputo')::date;
begin
  select pl.id, pl.activista_id, pl.estado into p from public.planos_equipa pl where pl.id = p_plano;
  if p.id is null then raise exception 'Plano não encontrado'; end if;
  if v_pp = 'activista' then
    select pf.activista_id into v_meu from public.perfis pf where pf.id = auth.uid();
    if v_meu is distinct from p.activista_id then raise exception 'Este plano não é da sua equipa'; end if;
  elsif not (v_pp = 'gestor' or (v_pp in ('tecnico', 'supervisor') and privado.equipa_minha(p.activista_id))) then raise exception 'sem acesso';
  end if;
  if exists (select 1 from public.itinerario_fechos x where x.plano_id = p_plano and x.dia_n = p_dia) then return json_build_object('ja', true); end if;
  if p_data is null or p_data > v_hoje or p_data < v_hoje - 14 then raise exception 'Data fora do prazo (últimos 14 dias)'; end if;
  for f in select * from jsonb_array_elements(coalesce(p_falhas, '[]'::jsonb)) loop
    v_m := f->>'motivo'; v_t := nullif(trim(coalesce(f->>'texto', '')), '');
    if v_m is null or v_m <> all (array['tuk_tuk', 'material', 'sem_agua_fonte', 'sem_vivas', 'produtor', 'sem_acesso', 'outro']) then raise exception 'Escolha o motivo de cada campo'; end if;
    if v_m in ('material', 'sem_agua_fonte', 'outro') and length(coalesce(v_t, '')) < 3 then
      raise exception '%', case v_m when 'material' then 'Escreva que material faltou' when 'sem_agua_fonte' then 'Escreva qual fonte não tinha água' else 'Escreva o motivo' end; end if;
    insert into public.itinerario_falhas (plano_id, dia_n, data, area_id, activista_id, motivo, texto, user_id)
      values (p_plano, p_dia, p_data, f->>'area_id', p.activista_id, v_m, v_t, auth.uid()) on conflict (plano_id, dia_n, area_id) do nothing;
  end loop;
  insert into public.itinerario_fechos (plano_id, dia_n, data, activista_id, user_id) values (p_plano, p_dia, p_data, p.activista_id, auth.uid());
  return json_build_object('ok', true);
end $function$;
revoke all on function public.fechar_itinerario_dia(uuid, integer, date, jsonb) from public, anon;
grant execute on function public.fechar_itinerario_dia(uuid, integer, date, jsonb) to authenticated, service_role;
