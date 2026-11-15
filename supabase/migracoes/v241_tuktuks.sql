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

-- ficha do campo (regas_campo), conector (api_painel: quadro «tuktuks»; api_dados2: tuk-tuk em cada linha de «regas»):
-- as três funções são alteradas a partir da definição que está no servidor (não muda mais nada nelas)
do $mig$
declare d text; n text;
begin
  select pg_get_functiondef(p.oid) into d from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace where ns.nspname = 'public' and p.proname = 'regas_campo';
  if position('tuk_codigo' in d) = 0 then
    n := replace(d, 'end as registada_por', 'end as registada_por, r.agua_em, r.tuk_codigo, r.tuk_outro, r.tuk_chegada, r.tuk_corrigido_em');
    if n = d then raise exception 'regas_campo: não encontrei onde acrescentar'; end if;
    execute n;
  end if;
  select pg_get_functiondef(p.oid) into d from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace where ns.nspname = 'public' and p.proname = 'api_painel';
  if position('tuktuks' in d) = 0 then
    n := replace(d, 'elsif p_tipo = ''painel_resumo''', 'elsif p_tipo = ''tuktuks'' then r := public.painel_tuktuks(p_de, p_ate);' || chr(10) || '  elsif p_tipo = ''painel_resumo''');
    if n = d then raise exception 'api_painel: não encontrei onde acrescentar'; end if;
    execute n;
  end if;
  select pg_get_functiondef(p.oid) into d from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace where ns.nspname = 'public' and p.proname = 'api_dados2';
  if position('tuk_codigo' in d) = 0 then
    n := replace(d, 'elsif p_tipo = ''chuva'' and v_papel = ''cliente'' then',
      'elsif p_tipo = ''regas'' then' || chr(10) ||
      '    select coalesce(json_agg((x.v::jsonb || jsonb_build_object(''tuk_tuk'', coalesce(g.tuk_codigo, g.tuk_outro), ''tuk_chegada'', g.tuk_chegada))::json order by x.n), ''[]''::json)' || chr(10) ||
      '      into r from json_array_elements(r) with ordinality x(v, n) left join public.registos_rega g on g.id = (x.v->>''id'')::uuid;' || chr(10) ||
      '  elsif p_tipo = ''chuva'' and v_papel = ''cliente'' then');
    if n = d then raise exception 'api_dados2: não encontrei onde acrescentar'; end if;
    execute n;
  end if;
end $mig$;
