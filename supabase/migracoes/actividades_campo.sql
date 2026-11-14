-- Melhoria 1 — Cava-roda e mulching quando não há rega (ramo cc-manutencao). NÃO APLICADA.
-- Aplicar com o conector Supabase (apply_migration, nome actividades_campo), ANTES de publicar a app. Testar primeiro com rollback.
-- Decisões do Valdo (13–14/11/2026):
--  - Quando falta o tuk-tuk, ou por outra razão não há rega, a equipa faz cava-roda e mulching nos campos da sua lista (ou em apoio).
--  - Segue o padrão da rega: entrada com GPS, pessoas e fotografia; fotografia durante; saída com GPS, plantas com cava-roda e com
--    mulching feitas NESSE DIA e fotografia. Pelo menos 1 planta numa das duas; sem mínimo de pessoas. Sem registo do material.
--  - O motivo (constrangimento) é sempre pedido ao abrir; pode ser no mesmo dia que uma rega. O técnico não confirma.
--  - Fim do trabalho no campo às 15:30 (config.hora_limite_inicio), para a rega e a cava-roda: depois disso não se começa nada novo, salvo
--    com «horas extras» activadas pelo técnico ou pelo supervisor para essa equipa nesse dia (tabela horas_extras). O que está em curso
--    pode ser terminado e conta para esse dia. «Fechar o dia» continua até às 18:00. As regas de teste não têm limite.
--  - Conta como dia de trabalho: o activista regista o início do dia (jornadas) antes de começar, como na rega; quando o registo é
--    do técnico/supervisor pela equipa, esta função cria o início do dia se ainda não houver nenhum (R1, «O meu dia», «Fechar o dia»
--    e cumprimento já aceitam o início do dia).
--  - Técnico, supervisor e gestor podem registar pela equipa (motivo_tecnico obrigatório), com as mesmas regras.
--  - Em Quiwia e Farol (manutencao_comunidades) soma-se ao último total da manutenção, com o limite das plantas do campo; o que
--    passar fica em *_excedente. Fora dessas comunidades guarda-se só o feito no dia.

-- ---------- tabela ----------
create table public.actividades_campo (
  id uuid primary key,
  area_id text not null references public.areas(id),
  activista_id uuid not null references public.activistas(id),
  data date not null,
  motivo text not null check (motivo = any (array['tuk_tuk','avaria_tuk_tuk','avaria_camiao','sem_agua','chuva','material','outro'])),
  motivo_texto text,
  motivo_tecnico text,                      -- registo do técnico/supervisor/gestor pela equipa (porquê)
  apoio_id uuid,
  entrada_em timestamptz not null, entrada_lat double precision, entrada_lon double precision, entrada_precisao_m int, entrada_dist_m int,
  saida_em timestamptz not null, saida_lat double precision, saida_lon double precision, saida_precisao_m int, saida_dist_m int,
  pessoas int,
  cavaroda int not null check (cavaroda >= 0),
  mulching int not null check (mulching >= 0),
  plantas_campo int,
  cavaroda_excedente int not null default 0,  -- Quiwia e Farol: o que passaria as plantas do campo no total da manutenção
  mulching_excedente int not null default 0,
  manut_registo_id uuid,                      -- linha acrescentada em manutencao_registos (Quiwia e Farol)
  foto_entrada text, foto_durante text, foto_saida text,   -- caminhos no bucket rega-fotos
  observacao text,
  user_id uuid not null default auth.uid(),
  papel text,
  criado_em timestamptz not null default now(),
  removido boolean not null default false
);
create index actividades_campo_area on public.actividades_campo (area_id, data);
create index actividades_campo_act_data on public.actividades_campo (activista_id, data);
alter table public.actividades_campo enable row level security;   -- sem políticas: só pelas RPC
create trigger guarda_so_teste before insert or delete or update on public.actividades_campo for each row execute function privado.guarda_so_teste();

insert into public.config (chave, valor)
select 'hora_limite_inicio', to_jsonb('15:30'::text)
where not exists (select 1 from public.config where chave = 'hora_limite_inicio');

-- ---------- horas extras (técnico ou supervisor da equipa, ou o gestor, activam na app, para esse dia) ----------
create table public.horas_extras (
  id uuid primary key,
  activista_id uuid not null references public.activistas(id),
  data date not null,
  activado_por uuid not null default auth.uid(),
  activado_em timestamptz not null,           -- hora do telefone de quem activou (pode ter sido sem rede)
  recebido_em timestamptz not null default now(),
  papel text,
  removido boolean not null default false
);
create unique index horas_extras_equipa_dia on public.horas_extras (activista_id, data) where not removido;
alter table public.horas_extras enable row level security;   -- sem políticas: só pelas RPC
create trigger guarda_so_teste before insert or delete or update on public.horas_extras for each row execute function privado.guarda_so_teste();

-- pode começar (rega ou cava-roda) a esta hora? até às 15:30, ou com horas extras dessa equipa nesse dia
create or replace function privado.pode_comecar(p_activista uuid, p_em timestamptz) returns boolean language sql stable security definer set search_path to '' as $$
  select to_char(p_em at time zone 'Africa/Maputo', 'HH24:MI') <= coalesce((select c.valor #>> '{}' from public.config c where c.chave = 'hora_limite_inicio'), '15:30')
      or exists (select 1 from public.horas_extras h where h.activista_id = p_activista and h.data = (p_em at time zone 'Africa/Maputo')::date and not h.removido);
$$;

create or replace function public.activar_horas_extras(p_id uuid, p_activista uuid, p_data date, p_em timestamptz)
returns json language plpgsql security definer set search_path to '' as $$
declare v_hoje date := (now() at time zone 'Africa/Maputo')::date; r record;
begin
  -- técnico e supervisor: as suas equipas; gestor: qualquer equipa (15/11/2026, Valdo)
  if privado.so_teste() or not (privado.meu_papel() = 'gestor' or (privado.meu_papel() in ('tecnico', 'supervisor') and privado.equipa_minha(p_activista))) then raise exception 'sem acesso'; end if;
  if p_data < v_hoje - 1 or p_data > v_hoje then raise exception 'Data inválida'; end if;
  select h.id, h.activado_em, pf.nome into r from public.horas_extras h left join public.perfis pf on pf.id = h.activado_por
    where h.activista_id = p_activista and h.data = p_data and not h.removido;
  if r.id is not null then return json_build_object('id', r.id, 'ja', true, 'por', r.nome, 'em', r.activado_em); end if;
  insert into public.horas_extras (id, activista_id, data, activado_por, activado_em, papel)
  values (p_id, p_activista, p_data, auth.uid(), least(coalesce(p_em, now()), now()), privado.meu_papel()) on conflict (id) do nothing;
  return json_build_object('id', p_id, 'ja', false);
end $$;
revoke all on function public.activar_horas_extras(uuid, uuid, date, timestamptz) from public, anon;
grant execute on function public.activar_horas_extras(uuid, uuid, date, timestamptz) to authenticated;

-- horas extras de hoje e de ontem das equipas que a pessoa vê (activista: a sua)
create or replace function public.horas_extras_lista() returns json language plpgsql stable security definer set search_path to '' as $$
declare v_papel text := privado.meu_papel(); v_meu uuid; v_hoje date := (now() at time zone 'Africa/Maputo')::date;
begin
  if v_papel is null then return '[]'::json; end if;
  if v_papel = 'activista' then select pf.activista_id into v_meu from public.perfis pf where pf.id = auth.uid(); end if;
  return coalesce((select json_agg(json_build_object('id', h.id, 'activista_id', h.activista_id, 'data', h.data, 'por', pf.nome, 'papel', h.papel, 'em', h.activado_em))
    from public.horas_extras h left join public.perfis pf on pf.id = h.activado_por
    where not h.removido and h.data >= v_hoje - 1
      and (case when v_papel = 'activista' then h.activista_id = v_meu
                when v_papel in ('tecnico', 'supervisor') then h.activista_id in (select privado.ids_visiveis())
                else v_papel in ('gestor', 'director', 'me') end)), '[]'::json);
end $$;
revoke all on function public.horas_extras_lista() from public, anon;
grant execute on function public.horas_extras_lista() to authenticated;

-- rega: a entrada de uma rega real depois das 15:30 só com horas extras (as de teste não têm limite)
create or replace function privado.rega_hora_limite() returns trigger language plpgsql security definer set search_path to '' as $$
begin
  if not new.teste and new.entrada_em is not null and not privado.pode_comecar(new.activista_id, new.entrada_em) then
    raise exception 'Depois das 15:30 só se começa uma rega com horas extras activadas pelo técnico ou pelo supervisor' using errcode = 'P0001';
  end if;
  return new;
end $$;
create trigger rega_hora_limite before insert on public.registos_rega for each row execute function privado.rega_hora_limite();

-- ---------- gravar (uma só chamada, no fim, como a rega) ----------
create or replace function public.gravar_actividade(p jsonb)
returns json language plpgsql security definer set search_path to '' as $$
declare
  v_id uuid := (p->>'id')::uuid; v_area text := p->>'area_id'; v_act uuid := (p->>'activista_id')::uuid;
  v_ent timestamptz := (p->>'entrada_em')::timestamptz; v_sai timestamptz := (p->>'saida_em')::timestamptz;
  v_cav int := coalesce((p->>'cavaroda')::int, 0); v_mul int := coalesce((p->>'mulching')::int, 0);
  v_mot text := p->>'motivo'; v_mtx text := nullif(trim(coalesce(p->>'motivo_texto', '')), '');
  v_mtec text := nullif(trim(coalesce(p->>'motivo_tecnico', '')), ''); v_apoio uuid := nullif(p->>'apoio_id', '')::uuid;
  v_papel text := privado.meu_papel(); v_meu uuid; v_d date; v_hoje date := (now() at time zone 'Africa/Maputo')::date;

  a record; n int; uc int; um int; nc int; nm int; v_man uuid; v_pess int := nullif(p->>'pessoas', '')::int;
begin
  if v_id is null or v_area is null or v_act is null or v_ent is null or v_sai is null then raise exception 'Dados em falta'; end if;
  if exists (select 1 from public.actividades_campo x where x.id = v_id) then return json_build_object('id', v_id, 'ja', true); end if;
  select ar.id, ar.activista_id, ar.comunidade, ar.activa into a from public.areas ar where ar.id = v_area;
  if a.id is null then raise exception 'Campo não encontrado'; end if;
  -- quem pode: o activista na sua lista (ou em apoio); técnico/supervisor/gestor pela equipa, com motivo
  if v_papel = 'activista' then
    select pf.activista_id into v_meu from public.perfis pf where pf.id = auth.uid();
    if v_meu is distinct from v_act then raise exception 'sem acesso'; end if;
  elsif v_papel in ('tecnico', 'supervisor', 'gestor') then
    if not (privado.rega_pela_equipa(v_act) or privado.regista_por(v_act)) then raise exception 'sem acesso'; end if;
    if v_mtec is null or length(v_mtec) < 3 then raise exception 'Escreva porque regista pela equipa'; end if;
  else raise exception 'sem acesso'; end if;
  if a.activista_id is distinct from v_act and not exists (
       select 1 from public.apoios ap where ap.id = v_apoio and ap.ajuda_activista_id = v_act and ap.terminado_em is null and v_area = any (ap.area_ids))
    then raise exception 'Este campo não é da lista da equipa'; end if;
  -- motivo (constrangimento) sempre
  if v_mot is null or v_mot <> all (array['tuk_tuk','avaria_tuk_tuk','avaria_camiao','sem_agua','chuva','material','outro']) then raise exception 'Escolha o motivo'; end if;
  if v_mot in ('outro', 'material') and (v_mtx is null or length(v_mtx) < 3) then raise exception 'Escreva o motivo'; end if;
  -- datas e hora: o dia é o da entrada (hora do telefone); não se começa depois das 15:30
  v_d := (v_ent at time zone 'Africa/Maputo')::date;
  if v_d < v_hoje - 7 or v_d > v_hoje + 1 then raise exception 'Data inválida'; end if;
  if not privado.pode_comecar(v_act, v_ent) then raise exception 'Depois das 15:30 só se começa a cava-roda e o mulching com horas extras activadas pelo técnico ou pelo supervisor'; end if;
  if v_sai < v_ent then raise exception 'A saída é antes da entrada'; end if;
  -- fotografias e plantas
  if coalesce(p->>'foto_entrada', '') = '' or coalesce(p->>'foto_durante', '') = '' or coalesce(p->>'foto_saida', '') = '' then raise exception 'Faltam fotografias'; end if;
  n := privado.manut_plantas(v_area);
  if v_cav < 0 or v_mul < 0 or v_cav > 20000 or v_mul > 20000 then raise exception 'Número inválido'; end if;
  if v_cav + v_mul < 1 then raise exception 'Escreva as plantas com cava-roda ou com mulching'; end if;
  if n > 0 and (v_cav > n or v_mul > n) then raise exception 'Mais plantas do que as % do campo', n; end if;
  if v_pess is not null and (v_pess < 1 or v_pess > 30) then raise exception 'Número de pessoas inválido'; end if;
  for k in 0..1 loop   -- pontos na zona
    if (p->>(case k when 0 then 'entrada_lat' else 'saida_lat' end)) is not null
       and (((p->>(case k when 0 then 'entrada_lat' else 'saida_lat' end))::double precision not between -12 and -9)
         or ((p->>(case k when 0 then 'entrada_lon' else 'saida_lon' end))::double precision not between 39 and 41.5))
      then raise exception 'Ponto fora da zona'; end if;
  end loop;

  insert into public.actividades_campo (id, area_id, activista_id, data, motivo, motivo_texto, motivo_tecnico, apoio_id,
    entrada_em, entrada_lat, entrada_lon, entrada_precisao_m, entrada_dist_m, saida_em, saida_lat, saida_lon, saida_precisao_m, saida_dist_m,
    pessoas, cavaroda, mulching, plantas_campo, foto_entrada, foto_durante, foto_saida, observacao, user_id, papel)
  values (v_id, v_area, v_act, v_d, v_mot, v_mtx, case when v_papel = 'activista' then null else v_mtec end, v_apoio,
    v_ent, (p->>'entrada_lat')::double precision, (p->>'entrada_lon')::double precision, (p->>'entrada_precisao_m')::int, (p->>'entrada_dist_m')::int,
    v_sai, (p->>'saida_lat')::double precision, (p->>'saida_lon')::double precision, (p->>'saida_precisao_m')::int, (p->>'saida_dist_m')::int,
    v_pess, v_cav, v_mul, n, p->>'foto_entrada', p->>'foto_durante', p->>'foto_saida', nullif(trim(coalesce(p->>'observacao', '')), ''), auth.uid(), v_papel);

  -- registo do técnico/supervisor pela equipa: o dia conta como trabalho (início do dia), se ainda não houver
  if v_papel <> 'activista' and not exists (select 1 from public.jornadas j where j.activista_id = v_act and j.data = v_d and not j.teste) then
    insert into public.jornadas (id, activista_id, data, pessoas, inicio_em, teste) values (gen_random_uuid(), v_act, v_d, coalesce(v_pess, 1), v_ent, false);
  end if;

  -- Quiwia e Farol: soma ao último total da manutenção, com o limite das plantas do campo
  if n > 0 and exists (select 1 from public.manutencao_comunidades c where c.comunidade = a.comunidade) then
    select r.cavaroda, r.mulching into uc, um from public.manutencao_registos r
      where r.area_id = v_area and not r.removido and privado.manut_conta(r.feito_em) order by r.feito_em desc limit 1;
    nc := least(n, coalesce(uc, 0) + v_cav); nm := least(n, coalesce(um, 0) + v_mul);
    v_man := gen_random_uuid();
    insert into public.manutencao_registos (id, area_id, data, cavaroda, mulching, plantas_campo, pessoas, obs, foto_path, lat, lon, precisao_m, feito_por, feito_em)
    values (v_man, v_area, v_d, nc, nm, n, v_pess,
      'Cava-roda e mulching da equipa (sem rega): +' || v_cav || ' cava-roda, +' || v_mul || ' mulching',
      'rega-fotos:' || (p->>'foto_saida'), (p->>'saida_lat')::double precision, (p->>'saida_lon')::double precision, (p->>'saida_precisao_m')::int, auth.uid(), v_sai);
    update public.actividades_campo set manut_registo_id = v_man,
      cavaroda_excedente = coalesce(uc, 0) + v_cav - nc, mulching_excedente = coalesce(um, 0) + v_mul - nm where id = v_id;
    if (nc < n or nm < n) then update public.manutencao_feitos set feito = false where area_id = v_area and feito; end if;
  end if;
  return json_build_object('id', v_id, 'manutencao', v_man is not null,
    'excedente', (select json_build_object('cavaroda', x.cavaroda_excedente, 'mulching', x.mulching_excedente) from public.actividades_campo x where x.id = v_id));
end $$;
revoke all on function public.gravar_actividade(jsonb) from public, anon;
grant execute on function public.gravar_actividade(jsonb) to authenticated;

-- ---------- ler: actividades de um campo (ficha) ----------
-- Devolve { lista (últimos 60 dias), cavaroda, mulching } — os dois totais somam TODOS os registos do campo (Valdo, 14/11/2026:
-- a ficha e a saída mostram «feitas A de B · faltam C»; continua a guardar-se só o feito em cada dia).
create or replace function public.actividades_campo_lista(p_area text)
returns json language plpgsql stable security definer set search_path to '' as $$
declare a record; v_papel text := privado.meu_papel(); v_meu uuid;
begin
  select ar.activista_id, ar.comunidade into a from public.areas ar where ar.id = p_area;
  if not found or not privado.le_area(a.activista_id, a.comunidade) then return json_build_object('lista', '[]'::json, 'cavaroda', 0, 'mulching', 0); end if;
  if v_papel = 'activista' then select pf.activista_id into v_meu from public.perfis pf where pf.id = auth.uid(); end if;
  return json_build_object('lista', coalesce((select json_agg(json_build_object('id', x.id, 'data', x.data, 'motivo', x.motivo, 'motivo_texto', x.motivo_texto,
      'motivo_tecnico', x.motivo_tecnico, 'entrada_em', x.entrada_em, 'saida_em', x.saida_em, 'pessoas', x.pessoas,
      'cavaroda', x.cavaroda, 'mulching', x.mulching, 'excedente', x.cavaroda_excedente + x.mulching_excedente, 'manutencao', x.manut_registo_id is not null,
      'equipa', ac.nome, 'quem', pf.nome, 'observacao', x.observacao,
      -- o activista só vê as fotografias que ele tirou (regra de 18/10/2026)
      'foto_entrada', case when v_papel <> 'activista' or x.user_id = auth.uid() then x.foto_entrada end,
      'foto_durante', case when v_papel <> 'activista' or x.user_id = auth.uid() then x.foto_durante end,
      'foto_saida', case when v_papel <> 'activista' or x.user_id = auth.uid() then x.foto_saida end) order by x.saida_em desc)
    from public.actividades_campo x join public.activistas ac on ac.id = x.activista_id left join public.perfis pf on pf.id = x.user_id
    where x.area_id = p_area and not x.removido and x.data >= (now() at time zone 'Africa/Maputo')::date - 60), '[]'::json),
    'cavaroda', (select coalesce(sum(x.cavaroda), 0) from public.actividades_campo x where x.area_id = p_area and not x.removido),
    'mulching', (select coalesce(sum(x.mulching), 0) from public.actividades_campo x where x.area_id = p_area and not x.removido));
end $$;
revoke all on function public.actividades_campo_lista(text) from public, anon;
grant execute on function public.actividades_campo_lista(text) to authenticated;

-- ---------- painel: uma linha por actividade no período ----------
create or replace function public.painel_actividades(p_de date, p_ate date)
returns json language plpgsql stable security definer set search_path to '' as $$
declare v_papel text := privado.meu_papel();
begin
  if v_papel is null or v_papel not in ('gestor', 'director', 'me', 'supervisor', 'tecnico', 'cliente') then return null; end if;
  return coalesce((select json_agg(json_build_object('id', x.id, 'data', x.data, 'area_id', x.area_id, 'produtor', ar.produtor,
      'comunidade', ar.comunidade, 'zona', ar.zona, 'equipa', ac.nome, 'activista_id', x.activista_id, 'tecnico', ac.tecnico, 'supervisor', ac.supervisor,
      'motivo', x.motivo, 'motivo_texto', x.motivo_texto, 'motivo_tecnico', x.motivo_tecnico, 'entrada_em', x.entrada_em, 'saida_em', x.saida_em,
      'pessoas', x.pessoas, 'cavaroda', x.cavaroda, 'mulching', x.mulching, 'plantas_campo', x.plantas_campo,
      'excedente', x.cavaroda_excedente + x.mulching_excedente, 'manutencao', x.manut_registo_id is not null, 'quem', pf.nome,
      'foto_entrada', case when v_papel <> 'cliente' then x.foto_entrada end, 'foto_durante', case when v_papel <> 'cliente' then x.foto_durante end,
      'foto_saida', case when v_papel <> 'cliente' then x.foto_saida end) order by x.data desc, x.saida_em desc)
    from public.actividades_campo x join public.areas ar on ar.id = x.area_id join public.activistas ac on ac.id = x.activista_id
      left join public.perfis pf on pf.id = x.user_id
    where not x.removido and (p_de is null or x.data >= p_de) and (p_ate is null or x.data <= p_ate)), '[]'::json);
end $$;
revoke all on function public.painel_actividades(date, date) from public, anon;
grant execute on function public.painel_actividades(date, date) to authenticated;

-- ---------- «O meu dia»: o que cada equipa fez hoje de cava-roda e mulching ----------
do $$ declare d text := pg_get_functiondef('public.meu_dia'::regproc);
  a text := $a$        'comecou', (select min(j.inicio_em) from public.jornadas j where j.activista_id = t.id and j.data = v_d and not j.teste),$a$;
  b text := $b$        'comecou', (select min(j.inicio_em) from public.jornadas j where j.activista_id = t.id and j.data = v_d and not j.teste),
        -- cava-roda e mulching (dias sem rega)
        'actividade', (select json_build_object('campos', count(distinct x.area_id), 'cavaroda', sum(x.cavaroda), 'mulching', sum(x.mulching))
          from public.actividades_campo x where x.activista_id = t.id and x.data = v_d and not x.removido having count(*) > 0),$b$;
begin if position(a in d) = 0 then raise exception 'meu_dia: texto não encontrado'; end if; execute replace(d, a, b); end $$;

-- ---------- VOLTAR ATRÁS ----------
-- (a app nova precisa destas funções; voltar primeiro a app à versão anterior)
-- do $$ declare d text := pg_get_functiondef('public.meu_dia'::regproc); i int := position(E'\n        -- cava-roda e mulching (dias sem rega)' in d); j int;
-- begin if i = 0 then return; end if; j := position('having count(*) > 0),' in substr(d, i)) + length('having count(*) > 0),');
--   execute substr(d, 1, i - 1) || substr(d, i + j - 1); end $$;
-- drop function public.painel_actividades(date, date); drop function public.actividades_campo_lista(text); drop function public.gravar_actividade(jsonb);
-- A tabela actividades_campo e as linhas acrescentadas a manutencao_registos podem ficar (a app anterior não as usa; as linhas da
-- manutenção são totais válidos). Para as tirar dos totais: update manutencao_registos set removido = true where id in (select manut_registo_id from actividades_campo);
-- drop trigger rega_hora_limite on public.registos_rega; drop function privado.rega_hora_limite();
-- drop function public.horas_extras_lista(); drop function public.activar_horas_extras(uuid, uuid, date, timestamptz); drop function privado.pode_comecar(uuid, timestamptz);
-- delete from public.config where chave = 'hora_limite_inicio';   (a tabela horas_extras pode ficar)
