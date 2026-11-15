-- v242 (15/11/2026, Valdo). Só acrescenta: a v241 continua a funcionar.
-- 1. «Chegou mais água»: outras voltas do tuk-tuk ao mesmo campo durante a rega (registos_rega.tuk_extra); cada uma é uma viagem.
-- 2. Apoio entre equipas para equipas sem campos (Olumbe): só para cava-roda e mulching (apoios.so_actividade).
-- 3. tuks_hoje(): última chegada da água de hoje de cada equipa, para o telefone do técnico ou do supervisor que regista pela equipa.

-- ---------- 1. outras voltas ----------
alter table public.registos_rega add column if not exists tuk_extra jsonb;
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'registos_rega_tuk_extra_lista') then
    alter table public.registos_rega add constraint registos_rega_tuk_extra_lista
      check (tuk_extra is null or (jsonb_typeof(tuk_extra) = 'array' and jsonb_array_length(tuk_extra) <= 20));
  end if;
end $$;

-- todas as chegadas da água (a da rega e as outras voltas), uma linha cada
create or replace function privado.tuk_chegadas(p_de date, p_ate date)
returns table (registo_id uuid, data date, hora timestamptz, activista_id uuid, area_id text, tuk text, outro text, chegada text, extra boolean, corrigido boolean)
language sql stable security definer set search_path to '' as $$
  select g.id, g.data, g.agua_em, g.activista_id, g.area_id, g.tuk_codigo, g.tuk_outro, g.tuk_chegada, false, g.tuk_corrigido_em is not null
  from public.registos_rega g
  where not g.teste and g.agua_em is not null and (p_de is null or g.data >= p_de) and (p_ate is null or g.data <= p_ate)
  union all
  select g.id, g.data, coalesce(nullif(x->>'em', '')::timestamptz, g.agua_em), g.activista_id, g.area_id,
         nullif(x->>'codigo', ''), nullif(x->>'outro', ''), 'nova', true, false
  from public.registos_rega g, jsonb_array_elements(g.tuk_extra) x
  where not g.teste and g.tuk_extra is not null and jsonb_typeof(g.tuk_extra) = 'array'
    and (p_de is null or g.data >= p_de) and (p_ate is null or g.data <= p_ate)
$$;
revoke all on function privado.tuk_chegadas(date, date) from public, anon, authenticated;

create or replace function public.painel_tuktuks(p_de date, p_ate date)
returns json language plpgsql stable security definer set search_path to '' as $function$
declare v_papel text := privado.meu_papel(); v_ini date := (select (valor #>> '{}')::date from public.config where chave = 'tuktuk_inicio');
begin
  if v_papel is null or v_papel not in ('gestor', 'director', 'me', 'supervisor', 'tecnico', 'cliente') then return null; end if;
  if v_ini is null then return null; end if;
  return json_build_object('inicio', v_ini,
    'lista', (select coalesce(json_agg(t.codigo order by t.ordem, t.codigo), '[]'::json) from public.tuktuks t where t.activo),
    'chegadas', (select coalesce(json_agg(json_build_object('data', g.data, 'hora', g.hora, 'equipa', ac.nome, 'activista_id', g.activista_id,
        'tecnico', ac.tecnico, 'supervisor', ac.supervisor, 'campo', g.area_id, 'produtor', ar.produtor, 'comunidade', ar.comunidade, 'zona', ar.zona,
        'tuk', g.tuk, 'outro', g.outro, 'chegada', g.chegada, 'viagem', coalesce(g.chegada = 'nova', false),
        'outra_volta', g.extra, 'corrigido', g.corrigido) order by g.data, g.hora), '[]'::json)
      from privado.tuk_chegadas(greatest(v_ini, coalesce(p_de, v_ini)), p_ate) g
      join public.areas ar on ar.id = g.area_id left join public.activistas ac on ac.id = g.activista_id));
end $function$;

-- ---------- 3. última chegada de hoje por equipa ----------
create or replace function public.tuks_hoje()
returns json language plpgsql stable security definer set search_path to '' as $function$
declare v_papel text := privado.meu_papel(); v_hoje date := (now() at time zone 'Africa/Maputo')::date; v_meu uuid;
begin
  if v_papel is null or v_papel not in ('activista', 'tecnico', 'supervisor', 'gestor') then return '[]'::json; end if;
  if v_papel = 'activista' then select pf.activista_id into v_meu from public.perfis pf where pf.id = auth.uid(); end if;
  return (select coalesce(json_agg(json_build_object('activista_id', u.activista_id, 'codigo', u.tuk, 'outro', u.outro, 'em', u.hora, 'area_id', u.area_id)), '[]'::json)
    from (select distinct on (c.activista_id) c.activista_id, c.tuk, c.outro, c.hora, c.area_id
          from privado.tuk_chegadas(v_hoje, v_hoje) c
          where c.chegada in ('nova', 'mesmo_tanque') and (c.tuk is not null or c.outro is not null)
            and (v_papel = 'gestor' or (v_papel = 'activista' and c.activista_id = v_meu)
              or (v_papel in ('tecnico', 'supervisor') and c.activista_id = any (privado.ids_visiveis())))
          order by c.activista_id, c.hora desc) u);
end $function$;
revoke all on function public.tuks_hoje() from public, anon;
grant execute on function public.tuks_hoje() to authenticated;

-- ---------- 2. apoio de uma equipa sem campos: só cava-roda e mulching ----------
alter table public.apoios add column if not exists so_actividade boolean not null default false;

create or replace function privado.sem_campos(p_act uuid) returns boolean
language sql stable security definer set search_path to '' as $$
  select not exists (select 1 from public.areas a where a.activista_id = p_act and a.activa)
$$;
revoke all on function privado.sem_campos(uuid) from public, anon, authenticated;

create or replace function public.criar_apoio(p_ajuda uuid, p_para uuid, p_areas text[], p_nota text default null::text)
returns uuid language plpgsql security definer set search_path to '' as $function$
declare v_papel text := privado.meu_papel(); v_max double precision; v_id uuid; v_mal text; v_n int; v_sem boolean;
begin
  if v_papel is null or v_papel not in ('tecnico','supervisor','gestor') then raise exception 'Só o técnico, o supervisor ou o gestor activam o apoio.'; end if;
  if p_ajuda is null or p_para is null or p_ajuda = p_para then raise exception 'Escolha duas equipas diferentes.'; end if;
  if v_papel <> 'gestor' and not (p_ajuda = any(privado.ids_visiveis()) or p_para = any(privado.ids_visiveis())) then
    raise exception 'Só pode activar o apoio quando uma das equipas é sua.'; end if;
  if not exists (select 1 from public.activistas where id = p_ajuda and activo) or not exists (select 1 from public.activistas where id = p_para and activo) then
    raise exception 'Equipa inactiva.'; end if;
  if exists (select 1 from public.apoios where ajuda_activista_id = p_ajuda and terminado_em is null) then
    raise exception 'Esta equipa já está a apoiar outra equipa: termine esse apoio primeiro.'; end if;
  select count(*) into v_n from (select distinct unnest(coalesce(p_areas, '{}'::text[]))) s;
  if v_n = 0 then raise exception 'Escolha pelo menos um campo.'; end if;
  v_sem := privado.sem_campos(p_ajuda);
  if v_sem then
    -- v242 (Valdo, 15/11/2026): equipa sem campos (ex.: Olumbe, sem material de rega) ajuda uma equipa da mesma comunidade,
    -- só na cava-roda e no mulching; qualquer campo da equipa apoiada, com ou sem coordenada, regado ou não.
    if (select comunidade_principal from public.activistas where id = p_ajuda) is distinct from (select comunidade_principal from public.activistas where id = p_para) then
      raise exception 'A equipa que ajuda não tem campos: só pode ajudar uma equipa da mesma comunidade.'; end if;
    select string_agg(x, ', ') into v_mal from unnest(p_areas) x
    where not exists (select 1 from public.areas t where t.id = x and t.activa and t.activista_id = p_para);
    if v_mal is not null then raise exception 'Campos que não são da equipa apoiada: %', v_mal; end if;
  else
    v_max := coalesce((select (valor #>> '{}')::double precision from public.config where chave = 'apoio_distancia_m'), 5000);
    select string_agg(x, ', ') into v_mal from unnest(p_areas) x
    where not exists (
      select 1 from public.areas t where t.id = x and t.activa and t.activista_id = p_para and t.latitude is not null
        and exists (select 1 from public.areas h where h.activista_id = p_ajuda and h.activa and h.latitude is not null
                    and privado.dist_m(h.latitude, h.longitude, t.latitude, t.longitude) <= v_max));
    if v_mal is not null then raise exception 'Campos que não são da equipa apoiada ou ficam a mais de % km dos campos da equipa que ajuda: %', round((v_max/1000)::numeric, 1), v_mal; end if;
  end if;
  insert into public.apoios (ajuda_activista_id, para_activista_id, area_ids, nota, criado_por, so_actividade)
  values (p_ajuda, p_para, (select array_agg(distinct x) from unnest(p_areas) x), nullif(trim(coalesce(p_nota,'')), ''), auth.uid(), v_sem)
  returning id into v_id;
  return v_id;
end $function$;

-- campos que se podem escolher: como antes, ou (equipa sem campos) todos os campos da equipa apoiada fora de outro apoio
create or replace function public.apoio_candidatos2(p_ajuda uuid, p_para uuid)
returns jsonb language plpgsql stable security definer set search_path to '' as $function$
declare v_papel text := privado.meu_papel(); v_sem boolean;
begin
  if v_papel is null or v_papel not in ('tecnico','supervisor','gestor') then return null; end if;
  v_sem := privado.sem_campos(p_ajuda);
  if not v_sem then
    return jsonb_build_object('so_actividade', false, 'campos',
      coalesce((select jsonb_agg(to_jsonb(c) order by c.nunca desc, c.dist_m) from privado.apoio_candidatos(p_ajuda, p_para) c), '[]'::jsonb));
  end if;
  return jsonb_build_object('so_actividade', true,
    'mesma_comunidade', (select comunidade_principal from public.activistas where id = p_ajuda) is not distinct from (select comunidade_principal from public.activistas where id = p_para),
    'campos', coalesce((select jsonb_agg(jsonb_build_object('area_id', t.id, 'produtor', t.produtor, 'pr', t.pr, 'area_n', t.area_n, 'comunidade', t.comunidade,
        'plantas', coalesce(nullif(t.vivas, 0), t.instaladas, 0), 'dist_m', null, 'nunca', false, 'sem_coordenada', t.latitude is null)
        order by t.comunidade, t.produtor, t.id)
      from public.areas t
      where t.activista_id = p_para and t.activa
        and t.id not in (select x from public.apoios p, unnest(p.area_ids) x where p.terminado_em is null)), '[]'::jsonb));
end $function$;
revoke all on function public.apoio_candidatos2(uuid, uuid) from public, anon;
grant execute on function public.apoio_candidatos2(uuid, uuid) to authenticated;

-- apoios_lista: + so_actividade e o trabalho de cava-roda e mulching feito no apoio
create or replace function public.apoios_lista()
returns jsonb language sql stable security definer set search_path to '' as $function$
  select coalesce(jsonb_agg(jsonb_build_object(
    'id', p.id, 'ajuda_activista_id', p.ajuda_activista_id, 'ajuda_nome', ha.nome, 'para_activista_id', p.para_activista_id, 'para_nome', pa.nome,
    'area_ids', p.area_ids, 'inicio', p.inicio, 'nota', p.nota, 'criado_em', p.criado_em, 'criado_por_nome', pc.nome,
    'terminado_em', p.terminado_em, 'terminado_por_nome', pt.nome, 'so_actividade', p.so_actividade,
    'feitas', (select count(distinct r.area_id) from public.registos_rega r where r.area_id = any(p.area_ids) and not r.teste and r.plantas_regadas > 0 and r.data >= p.inicio),
    'regas_apoio', (select count(*) from public.registos_rega r where r.apoio_id = p.id),
    'plantas_apoio', (select coalesce(sum(r.plantas_regadas),0) from public.registos_rega r where r.apoio_id = p.id),
    'campos_actividade', (select count(distinct x.area_id) from public.actividades_campo x where x.apoio_id = p.id and not x.removido)
  ) order by p.criado_em desc), '[]'::jsonb)
  from public.apoios p
  join public.activistas ha on ha.id = p.ajuda_activista_id
  join public.activistas pa on pa.id = p.para_activista_id
  left join public.perfis pc on pc.id = p.criado_por
  left join public.perfis pt on pt.id = p.terminado_por
  where auth.uid() is not null
    and (p.terminado_em is null or p.terminado_em > now() - interval '14 days')
    and (privado.meu_papel() in ('gestor','director','me')
      or (privado.meu_papel() = 'activista' and privado.meu_activista() in (p.ajuda_activista_id, p.para_activista_id))
      or (privado.meu_papel() in ('tecnico','supervisor') and (privado.ve_tudo() or p.ajuda_activista_id = any(privado.ids_visiveis()) or p.para_activista_id = any(privado.ids_visiveis()))))
$function$;

-- uma rega num apoio só de cava-roda e mulching não conta como rega em apoio (fica «fora da lista», com motivo pedido)
create or replace function privado.marca_fora_lista()
returns trigger language plpgsql security definer set search_path to '' as $function$
declare v_dono uuid; v_ok boolean := false;
begin
  select activista_id into v_dono from public.areas where id = new.area_id;
  if new.apoio_id is not null then
    select true into v_ok from public.apoios p
    where p.id = new.apoio_id and p.ajuda_activista_id = new.activista_id and p.para_activista_id = v_dono
      and not p.so_actividade
      and new.area_id = any(p.area_ids) and new.data >= p.inicio
      and (p.terminado_em is null or new.data <= (p.terminado_em at time zone 'Africa/Maputo')::date);
    if coalesce(v_ok, false) and not new.teste then
      new.apoio_para := v_dono;
      new.ronda := coalesce((select ro.ronda_actual from privado.rondas() ro where ro.activista_id = v_dono), 1);
      return new;
    end if;
    new.apoio_id := null; new.apoio_para := null;
  else
    new.apoio_para := null;
  end if;
  if v_dono is distinct from new.activista_id then
    new.alerta := 'fora_da_lista';
    if length(trim(coalesce(new.motivo_alerta, ''))) < 3 then
      new.motivo_alerta := 'Sem justificação: no servidor o campo não está na lista deste activista';
    end if;
  end if;
  return new;
end $function$;

-- regas_campo: as outras voltas do tuk-tuk em cada rega (alterada a partir da definição do servidor)
do $$
declare d text; n text;
begin
  select pg_get_functiondef(p.oid) into d from pg_proc p join pg_namespace s on s.oid = p.pronamespace where s.nspname = 'public' and p.proname = 'regas_campo';
  if d not like '%tuk_extra%' then
    n := replace(d, 'r.tuk_chegada, r.tuk_corrigido_em', 'r.tuk_chegada, r.tuk_extra, r.tuk_corrigido_em');
    if n = d then raise exception 'regas_campo: marca não encontrada'; end if;
    execute n;
  end if;
end $$;
