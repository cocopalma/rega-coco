-- v235 (12/11/2026, decisões do Valdo no grupo de alinhamento). NÃO APLICADA: só depois de o Valdo aprovar os testes do ramo teste-v235.
-- Aplicar com o conector Supabase (apply_migration, nome v235), antes de publicar a app.
-- 1. «🚰 Fomos buscar água»   2. ⚠️ de ritmo contra a mediana de todas as equipas   3. papel «chefe de manutenção»
-- (o motivo «Fonte de água secou» ao voltar a pôr um campo na rega é só na app: voltar_a_regar já aceita texto.)

-- ---------- 1. Ida buscar água (Valdo: "Para quem vai buscar água o início é o mesmo… saberemos a razão de terem chegado ao campo tarde") ----------
create table public.recolhas_agua (
  id uuid primary key,
  activista_id uuid not null references public.activistas(id),
  data date not null,
  em timestamptz not null,
  lat double precision, lon double precision, precisao_m int,
  user_id uuid not null default auth.uid(),
  criado_em timestamptz not null default now(),
  removido boolean not null default false
);
create index recolhas_agua_act_data on public.recolhas_agua (activista_id, data);
alter table public.recolhas_agua enable row level security;   -- sem políticas: só pela RPC
create trigger guarda_so_teste before insert or delete or update on public.recolhas_agua for each row execute function privado.guarda_so_teste();

create or replace function public.gravar_recolha_agua(p_id uuid, p_activista uuid, p_em timestamptz, p_lat double precision, p_lon double precision, p_precisao int)
returns void language plpgsql security definer set search_path to '' as $$
declare v_hoje date := (now() at time zone 'Africa/Maputo')::date; v_d date := (coalesce(p_em, now()) at time zone 'Africa/Maputo')::date;
begin
  if not ((privado.meu_papel() = 'activista' and p_activista = (select p.activista_id from public.perfis p where p.id = auth.uid()))
          or privado.regista_por(p_activista)) then raise exception 'sem acesso'; end if;
  if v_d < v_hoje - 7 or v_d > v_hoje + 1 then raise exception 'Data inválida'; end if;
  if p_lat is not null and (p_lat not between -12 and -9 or p_lon not between 39 and 41.5) then raise exception 'Ponto fora da zona'; end if;
  insert into public.recolhas_agua (id, activista_id, data, em, lat, lon, precisao_m, user_id)
  values (p_id, p_activista, v_d, coalesce(p_em, now()), p_lat, p_lon, p_precisao, auth.uid())
  on conflict (id) do nothing;
end $$;
revoke all on function public.gravar_recolha_agua(uuid, uuid, timestamptz, double precision, double precision, int) from public, anon;
grant execute on function public.gravar_recolha_agua(uuid, uuid, timestamptz, double precision, double precision, int) to authenticated;

-- «O meu dia»: hora da 1.ª ida à água de cada equipa (ao lado da chegada tardia)
do $$ declare d text := pg_get_functiondef('public.meu_dia'::regproc);
  a text := $a$        'comecou', (select min(j.inicio_em) from public.jornadas j where j.activista_id = t.id and j.data = v_d and not j.teste),$a$;
  b text := $b$        'comecou', (select min(j.inicio_em) from public.jornadas j where j.activista_id = t.id and j.data = v_d and not j.teste),
        -- v235: a equipa foi buscar água antes do campo (razão da chegada tardia)
        'agua', (select min(w.em) from public.recolhas_agua w where w.activista_id = t.id and w.data = v_d and not w.removido),$b$;
begin if position(a in d) = 0 then raise exception 'meu_dia: texto não encontrado'; end if; execute replace(d, a, b); end $$;

-- ---------- 2. ⚠️ de ritmo contra a mediana de todas as equipas (Valdo: "Sim") ----------
-- Antes cada equipa era comparada com a sua própria mediana: uma equipa que rega sempre depressa nunca era assinalada
-- (Alafo: mediana dele 101 plantas por pessoa por hora; mediana de todas as equipas 29).
do $$ declare d text := pg_get_functiondef('privado.regas_alerta'::regproc);
  a1 text := 'med as (select activista_id, percentile_cont(0.5) within group (order by ritmo) m, count(ritmo) n from rr group by activista_id)';
  b1 text := 'med as (select percentile_cont(0.5) within group (order by ritmo) m, count(ritmo) n from rr)   -- v235: todas as equipas';
  a2 text := 'from rr left join med on med.activista_id = rr.activista_id';
  b2 text := 'from rr cross join med';
begin if position(a1 in d) = 0 or position(a2 in d) = 0 then raise exception 'regas_alerta: texto não encontrado'; end if;
  execute replace(replace(d, a1, b1), a2, b2); end $$;

-- ---------- 3. Chefe de manutenção (Valdo: "O cargo fica chefe de manutenção. E só terão acesso à manutenção, cada um apenas dos seus
-- campos. Caso um campo esteja mais próximo de uma equipa que não é a dona do campo, o técnico ou o supervisor pode atribuí-lo") ----------
alter table public.perfis drop constraint perfis_papel_check;
alter table public.perfis add constraint perfis_papel_check check (papel = any (array['activista','tecnico','supervisor','gestor','cliente','director','me','oficial_me','chefe_manutencao']));
alter table public.pessoas_acesso drop constraint pessoas_acesso_papel_check;
alter table public.pessoas_acesso add constraint pessoas_acesso_papel_check check (papel = any (array['tecnico','supervisor','director','me','cliente','oficial_me','chefe_manutencao']));

-- grupo de cada chefe = uma comunidade da manutenção (criado pela função gestor-activistas ao criar o acesso)
create table public.manutencao_chefes (
  perfil_id uuid primary key references public.perfis(id) on delete cascade,
  comunidade text not null references public.manutencao_comunidades(comunidade),
  criado_em timestamptz not null default now(), criado_por uuid
);
alter table public.manutencao_chefes enable row level security;   -- sem políticas: só pelas RPC e pela função

-- campo passado para outro grupo pelo técnico ou pelo supervisor (null = o chefe da comunidade do campo)
alter table public.areas add column manut_chefe_id uuid references public.perfis(id);
alter table public.alteracoes_areas drop constraint alteracoes_areas_campo_check;
alter table public.alteracoes_areas add constraint alteracoes_areas_campo_check check (campo = any (array['activista_id','coordenada','zona','activa','poligono','comunidade','limites','vivas','instaladas','produtor','manut_sem_plantas','manut_chefe']));

create or replace function privado.chefe_manut(p_area text) returns uuid language sql stable security definer set search_path to '' as $$
  select coalesce(a.manut_chefe_id, (select c.perfil_id from public.manutencao_chefes c where c.comunidade = a.comunidade order by c.criado_em limit 1))
  from public.areas a where a.id = p_area
$$;

create or replace function privado.manut_acesso() returns text language sql stable security definer set search_path to '' as $$
  select case
    when privado.meu_papel() = 'chefe_manutencao' then 'chefe'   -- v235: só os campos do seu grupo, só regista
    when privado.meu_papel() = 'gestor' then 'escreve'
    when privado.meu_papel() = 'supervisor' and exists (select 1 from public.manutencao_comunidades c join public.perfis p on p.nome = c.supervisor where p.id = auth.uid()) then 'escreve'
    when privado.meu_papel() = 'tecnico' and exists (select 1 from public.activistas ac join public.perfis p on p.nome = ac.tecnico
         join public.manutencao_comunidades c on c.comunidade = ac.comunidade_principal where p.id = auth.uid()) then 'regista'
    when privado.meu_papel() in ('director', 'me') then 'le'
    when privado.meu_papel() = 'supervisor' and privado.ve_tudo() then 'le'
    else null end;
$$;

create or replace function public.manutencao_campos() returns json language plpgsql stable security definer set search_path to '' as $$
declare v text := privado.manut_acesso();
begin
  if v is null then return null; end if;
  return json_build_object('acesso', v, 'inicio', (select valor #>> '{}' from public.config where chave = 'manutencao_inicio'), 'teste', now() < privado.manut_inicio(),
    'comunidades', (select coalesce(json_agg(c.comunidade order by c.comunidade), '[]') from public.manutencao_comunidades c
                    where v <> 'chefe' or exists (select 1 from public.areas a where a.comunidade = c.comunidade and privado.chefe_manut(a.id) = auth.uid())),
    -- v235: lista dos chefes para o técnico, o supervisor e o gestor mudarem o chefe de um campo
    'chefes', case when v = 'chefe' then null else (select coalesce(json_agg(json_build_object('id', p.id, 'nome', p.nome, 'comunidade', c.comunidade) order by c.comunidade, p.nome), '[]')
               from public.manutencao_chefes c join public.perfis p on p.id = c.perfil_id where p.papel = 'chefe_manutencao') end,
    'campos', (select coalesce(json_agg(x order by x.comunidade, x.produtor, x.id), '[]') from (
      select a.id, a.pr, a.produtor, a.comunidade, a.zona, a.latitude, a.longitude, a.poligono, a.vivas, a.instaladas, a.activa,
             privado.manut_plantas(a.id) as plantas, a.manut_sem_plantas as sem_plantas, ac.nome as activista,
             u.cavaroda, u.mulching, u.data as ultima, u.feito_em as ultima_em, coalesce(n.n, 0) as n,
             coalesce(f.feito, false) as feito, f.marcado_em as feito_em, pf.nome as feito_por,
             privado.chefe_manut(a.id) as chefe_id, (select pc.nome from public.perfis pc where pc.id = privado.chefe_manut(a.id)) as chefe
      from public.areas a
      join public.manutencao_comunidades c on c.comunidade = a.comunidade
      left join public.activistas ac on ac.id = a.activista_id
      left join lateral (select r.cavaroda, r.mulching, r.data, r.feito_em from public.manutencao_registos r
                         where r.area_id = a.id and not r.removido and privado.manut_conta(r.feito_em) order by r.feito_em desc limit 1) u on true
      left join lateral (select count(*)::int as n from public.manutencao_registos r where r.area_id = a.id and not r.removido and privado.manut_conta(r.feito_em)) n on true
      left join public.manutencao_feitos f on f.area_id = a.id and privado.manut_conta(f.marcado_em)
      left join public.perfis pf on pf.id = f.marcado_por
      where v <> 'chefe' or privado.chefe_manut(a.id) = auth.uid()) x));
end $$;

create or replace function public.gravar_manutencao(p_id uuid, p_area text, p_data date, p_cavaroda integer, p_mulching integer, p_pessoas integer, p_obs text, p_foto text, p_lat double precision, p_lon double precision, p_precisao integer, p_em timestamp with time zone)
returns void language plpgsql security definer set search_path to '' as $$
declare n int; com text;
begin
  if coalesce(privado.manut_acesso(), '') not in ('escreve', 'regista', 'chefe') then raise exception 'sem acesso'; end if;
  if privado.manut_acesso() = 'chefe' and privado.chefe_manut(p_area) is distinct from auth.uid() then raise exception 'Este campo não é do seu grupo'; end if;
  select a.comunidade into com from public.areas a where a.id = p_area;
  if com is null or not exists (select 1 from public.manutencao_comunidades c where c.comunidade = com) then raise exception 'Campo fora das comunidades da manutenção'; end if;
  n := privado.manut_plantas(p_area);
  if p_cavaroda < 0 or p_mulching < 0 then raise exception 'Número inválido'; end if;
  if n > 0 and (p_cavaroda > n or p_mulching > n) then raise exception 'Mais plantas do que as % do campo', n; end if;
  if p_foto is null then raise exception 'Falta a fotografia'; end if;
  if p_data > (now() at time zone 'Africa/Maputo')::date + 1 then raise exception 'Data inválida'; end if;
  insert into public.manutencao_registos (id, area_id, data, cavaroda, mulching, plantas_campo, pessoas, obs, foto_path, lat, lon, precisao_m, feito_por, feito_em)
  values (p_id, p_area, p_data, p_cavaroda, p_mulching, n, p_pessoas, nullif(trim(coalesce(p_obs, '')), ''), p_foto, p_lat, p_lon, p_precisao, auth.uid(), coalesce(p_em, now()))
  on conflict (id) do nothing;
  -- deixou de estar completo: deixa de estar "Feito"
  if (p_cavaroda < n or p_mulching < n) then update public.manutencao_feitos set feito = false where area_id = p_area and feito; end if;
end $$;

-- remover: o chefe, como o técnico, só os registos que fez
do $$ declare d text := pg_get_functiondef('public.remover_manutencao'::regproc);
  a1 text := $x$not in ('escreve', 'regista')$x$;  b1 text := $x$not in ('escreve', 'regista', 'chefe')$x$;
  a2 text := $x$privado.manut_acesso() = 'regista' and$x$;  b2 text := $x$privado.manut_acesso() in ('regista', 'chefe') and$x$;
begin if position(a1 in d) = 0 or position(a2 in d) = 0 then raise exception 'remover_manutencao: texto não encontrado'; end if;
  execute replace(replace(d, a1, b1), a2, b2); end $$;

-- registos de um campo: o chefe só os campos do seu grupo
do $$ declare d text := pg_get_functiondef('public.manutencao_registos_campo'::regproc);
  a text := $x$if privado.manut_acesso() is null then raise exception 'sem acesso'; end if;$x$;
  b text := $x$if privado.manut_acesso() is null then raise exception 'sem acesso'; end if;
  if privado.manut_acesso() = 'chefe' and privado.chefe_manut(p_area) is distinct from auth.uid() then raise exception 'Este campo não é do seu grupo'; end if;$x$;
begin if position(a in d) = 0 then raise exception 'manutencao_registos_campo: texto não encontrado'; end if; execute replace(d, a, b); end $$;

-- painel: o chefe não vê o painel
do $$ declare d text := pg_get_functiondef('public.painel_manutencao'::regproc);
  a text := $x$if privado.manut_acesso() is null then return null; end if;$x$;
  b text := $x$if privado.manut_acesso() is null or privado.manut_acesso() = 'chefe' then return null; end if;$x$;
begin if position(a in d) = 0 then raise exception 'painel_manutencao: texto não encontrado'; end if; execute replace(d, a, b); end $$;

-- mudar o chefe de um campo: técnico, supervisor e gestor com acesso à manutenção; motivo obrigatório; histórico em alteracoes_areas
create or replace function public.atribuir_chefe_manut(p_area text, p_chefe uuid, p_motivo text)
returns void language plpgsql security definer set search_path to '' as $$
declare v_ant uuid; v_com text;
begin
  if coalesce(privado.manut_acesso(), '') not in ('escreve', 'regista') then raise exception 'sem acesso'; end if;
  if length(trim(coalesce(p_motivo, ''))) < 3 then raise exception 'Escreva o motivo'; end if;
  select a.manut_chefe_id, a.comunidade into v_ant, v_com from public.areas a where a.id = p_area;
  if v_com is null or not exists (select 1 from public.manutencao_comunidades c where c.comunidade = v_com) then raise exception 'Campo fora das comunidades da manutenção'; end if;
  if p_chefe is not null and not exists (select 1 from public.perfis p where p.id = p_chefe and p.papel = 'chefe_manutencao') then raise exception 'Escolha um chefe de manutenção'; end if;
  if v_ant is not distinct from p_chefe then return; end if;
  update public.areas set manut_chefe_id = p_chefe where id = p_area;
  insert into public.alteracoes_areas (area_id, campo, valor_antigo, valor_novo, user_id, motivo)
  values (p_area, 'manut_chefe', v_ant::text, p_chefe::text, auth.uid(), trim(p_motivo));
end $$;
revoke all on function public.atribuir_chefe_manut(text, uuid, text) from public, anon;
grant execute on function public.atribuir_chefe_manut(text, uuid, text) to authenticated;

-- fotografias do trabalho: o chefe envia para a sua pasta (ler já está: manut_fotos_ler)
create policy manut_fotos_enviar_chefe on storage.objects for insert to authenticated
  with check (bucket_id = 'manutencao-fotos' and privado.manut_acesso() = 'chefe' and (storage.foldername(name))[1] = (auth.uid())::text);
create policy manut_fotos_actualizar_chefe on storage.objects for update to authenticated
  using (bucket_id = 'manutencao-fotos' and privado.manut_acesso() = 'chefe' and (storage.foldername(name))[1] = (auth.uid())::text);
