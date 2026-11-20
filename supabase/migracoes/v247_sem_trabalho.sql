-- v247 (20/11/2026, Valdo, decisões de 20/11 09:18): um dia de equipa sem rega e sem cava-roda e mulching fica por tratar até haver
-- registo (rega ou cava-roda) ou motivo; o início do dia sozinho já não chega (a partir de config.fecho_trabalho_inicio).
-- Quando o activista regista «não houve rega» e não faz cava-roda e mulching, diz porquê (dias_sem_rega.sem_act).
-- Afecta: fechar_dia, gestao_equipa_campo (painel «Equipa de campo»), painel_cumprimento, meu_dia e dias_sem_rega_lista (devolvem sem_act).
-- Só acrescenta (as funções antigas são alteradas por substituição de texto e o bloco pára se o texto esperado não existir).

alter table public.dias_sem_rega add column if not exists sem_act text;

-- data a partir da qual o início do dia sozinho deixa de contar: pôr o dia da publicação
insert into public.config (chave, valor) values ('fecho_trabalho_inicio', '"2026-11-21"') on conflict (chave) do nothing;

create or replace function privado.trabalho_inicio() returns date language sql stable security definer set search_path to ''
as $f$ select coalesce((select (valor #>> '{}')::date from public.config where chave = 'fecho_trabalho_inicio'), date '9999-12-31') $f$;
revoke all on function privado.trabalho_inicio() from public;

-- dia sem rega com a razão de não fazer cava-roda e mulching (gravar_dia_sem_rega4 + p_sem_act)
create or replace function public.gravar_dia_sem_rega5(p_id uuid, p_activista uuid, p_data date, p_motivo text, p_todo_dia boolean, p_descricao text,
  p_lat double precision, p_lon double precision, p_foto text, p_area text, p_entrada timestamp with time zone, p_ate date, p_sem_act text)
 returns json language plpgsql security definer set search_path to ''
as $function$
declare v json;
begin
  v := public.gravar_dia_sem_rega4(p_id, p_activista, p_data, p_motivo, p_todo_dia, p_descricao, p_lat, p_lon, p_foto, p_area, p_entrada, p_ate);
  if nullif(trim(coalesce(p_sem_act, '')), '') is not null then
    update public.dias_sem_rega set sem_act = left(trim(p_sem_act), 500) where id = p_id and user_id = auth.uid();
  end if;
  return v;
end $function$;
revoke all on function public.gravar_dia_sem_rega5(uuid, uuid, date, text, boolean, text, double precision, double precision, text, text, timestamp with time zone, date, text) from public, anon;
grant execute on function public.gravar_dia_sem_rega5(uuid, uuid, date, text, boolean, text, double precision, double precision, text, text, timestamp with time zone, date, text) to authenticated, service_role;

do $do$
declare d text; n text;
begin
  -- fechar_dia: o início do dia só conta antes de fecho_trabalho_inicio; a cava-roda e o mulching contam
  d := pg_get_functiondef('public.fechar_dia(date)'::regprocedure);
  if position('privado.trabalho_inicio()' in d) = 0 then
    n := replace(d, $x$and not exists (select 1 from public.jornadas j where j.activista_id = t.id and j.data = p_data and not j.teste)$x$,
      $x$and not exists (select 1 from public.jornadas j where j.activista_id = t.id and j.data = p_data and not j.teste and p_data < privado.trabalho_inicio())
    and not exists (select 1 from public.actividades_campo x where x.activista_id = t.id and x.data = p_data and not x.removido)$x$);
    if n = d then raise exception 'fechar_dia: texto esperado não encontrado'; end if;
    execute n;
  end if;
  -- painel «Equipa de campo»
  d := pg_get_functiondef('public.gestao_equipa_campo(date)'::regprocedure);
  if position('privado.trabalho_inicio()' in d) = 0 then
    n := replace(d, $x$and not exists (select 1 from jord where jord.activista_id = pe.activista_id and jord.data = dd.d)$x$,
      $x$and not exists (select 1 from jord where jord.activista_id = pe.activista_id and jord.data = dd.d and dd.d < privado.trabalho_inicio())
           and not exists (select 1 from public.actividades_campo x where x.activista_id = pe.activista_id and x.data = dd.d and not x.removido)$x$);
    if n = d then raise exception 'gestao_equipa_campo: texto esperado não encontrado'; end if;
    execute n;
  end if;
  -- painel › Cumprimento
  d := pg_get_functiondef('public.painel_cumprimento(date,date)'::regprocedure);
  if position('privado.trabalho_inicio()' in d) = 0 then
    n := replace(d, $x$or exists (select 1 from public.jornadas j where j.activista_id = eq.eid and j.data = dias.d and not j.teste) regou$x$,
      $x$or exists (select 1 from public.jornadas j where j.activista_id = eq.eid and j.data = dias.d and not j.teste and dias.d < privado.trabalho_inicio())
        or exists (select 1 from public.actividades_campo x where x.activista_id = eq.eid and x.data = dias.d and not x.removido) regou$x$);
    if n = d then raise exception 'painel_cumprimento: texto esperado não encontrado'; end if;
    execute n;
  end if;
  -- «O meu dia»: razão de não fazer cava-roda e mulching em cada motivo; data a partir da qual o início sozinho não chega
  d := pg_get_functiondef('public.meu_dia(date)'::regprocedure);
  if position('''sem_act''' in d) = 0 then
    n := replace(d, $x$'descricao', m.descricao, 'todo_dia', m.todo_dia,$x$, $x$'descricao', m.descricao, 'sem_act', m.sem_act, 'todo_dia', m.todo_dia,$x$);
    n := replace(n, $x$'hora_chegada', to_char(v_h, 'HH24:MI'),$x$, $x$'hora_chegada', to_char(v_h, 'HH24:MI'),
    'trabalho_inicio', privado.trabalho_inicio(),$x$);
    if n = d or position('trabalho_inicio' in n) = 0 then raise exception 'meu_dia: texto esperado não encontrado'; end if;
    execute n;
  end if;
  -- lista dos dias sem rega (painel)
  d := pg_get_functiondef('public.dias_sem_rega_lista(date,date)'::regprocedure);
  if position('d.sem_act' in d) = 0 then
    n := replace(d, 'a.produtor, d.entrada_em,', 'a.produtor, d.entrada_em, d.sem_act,');
    if n = d then raise exception 'dias_sem_rega_lista: texto esperado não encontrado'; end if;
    execute n;
  end if;
end $do$;
