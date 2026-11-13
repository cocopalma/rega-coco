-- Endereço só de leitura e conector para o Claude (13/11/2026, Valdo: "só leitura", "só para o Dalmar", "entra tudo o que está na app",
-- "uma chave para cada um", alarme por email). Telefones, utilizadores, senhas e PIN ficam de fora. Nada aqui escreve nos dados da rega.

-- ---------- chaves (só se guarda a impressão SHA-256; a chave vê-se uma vez, ao criar) ----------
create table public.api_chaves (
  id uuid primary key default gen_random_uuid(),
  nome text not null unique,
  impressao text not null unique,
  activa boolean not null default true,
  limite_hora int not null default 300,
  criada_em timestamptz not null default now(),
  revogada_em timestamptz
);
alter table public.api_chaves enable row level security;   -- sem políticas: só a função do servidor lê

create table public.api_acessos (
  id bigint generated always as identity primary key,
  chave_id uuid references public.api_chaves(id),
  em timestamptz not null default now(),
  ip text, agente text, via text, accao text, parametros jsonb, linhas int, ms int, estado int
);
create index api_acessos_chave_em on public.api_acessos (chave_id, em);
alter table public.api_acessos enable row level security;

-- criar e desligar chaves: só no SQL Editor do Supabase (o Valdo); ninguém da app consegue
create or replace function public.api_criar_chave(p_nome text) returns text language plpgsql security definer set search_path to '' as $$
declare k text := 'rc_' || encode(extensions.gen_random_bytes(24), 'hex');
begin
  if length(trim(coalesce(p_nome, ''))) < 2 then raise exception 'Escreva o nome'; end if;
  insert into public.api_chaves (nome, impressao) values (trim(p_nome), encode(extensions.digest(k, 'sha256'), 'hex'));
  return k;
end $$;
create or replace function public.api_desligar_chave(p_nome text) returns text language sql security definer set search_path to '' as $$
  update public.api_chaves set activa = false, revogada_em = now() where nome = p_nome and activa returning 'desligada: ' || nome;
$$;
revoke all on function public.api_criar_chave(text) from public, anon, authenticated;
revoke all on function public.api_desligar_chave(text) from public, anon, authenticated;

-- validar a chave e contar os pedidos da última hora (chamada pela função do servidor)
create or replace function public.api_validar(p_chave text) returns json language sql stable security definer set search_path to '' as $$
  select json_build_object('id', c.id, 'nome', c.nome, 'limite', c.limite_hora,
    'pedidos_hora', (select count(*) from public.api_acessos a where a.chave_id = c.id and a.em > now() - interval '1 hour'))
  from public.api_chaves c where c.activa and c.impressao = encode(extensions.digest(coalesce(p_chave, ''), 'sha256'), 'hex');
$$;
create or replace function public.api_registar(p_chave uuid, p_ip text, p_agente text, p_via text, p_accao text, p_param jsonb, p_linhas int, p_ms int, p_estado int)
returns void language sql security definer set search_path to '' as $$
  insert into public.api_acessos (chave_id, ip, agente, via, accao, parametros, linhas, ms, estado)
  values (p_chave, left(p_ip, 80), left(p_agente, 200), p_via, left(p_accao, 60), p_param, p_linhas, p_ms, p_estado);
$$;
revoke all on function public.api_validar(text) from public, anon, authenticated;
revoke all on function public.api_registar(uuid, text, text, text, text, jsonb, int, int, int) from public, anon, authenticated;

-- ---------- leitura dos dados (só select) ----------
create or replace function privado.ref_foto(b text, c text) returns text language sql immutable set search_path to '' as $$
  select case when c is null or c = '' then null else b || '/' || c end $$;

create or replace function privado.hl(t timestamptz) returns text language sql immutable set search_path to '' as $$
  select to_char(t at time zone 'Africa/Maputo', 'YYYY-MM-DD HH24:MI') $$;

create or replace function public.api_dados(p_tipo text, p_de date, p_ate date, p_comunidade text default null, p_equipa text default null)
returns json language plpgsql stable security definer set search_path to '' as $$
declare r json;
begin
  if p_tipo = 'regas' then
    select coalesce(json_agg(x order by x.data, x.equipa, x.entrada), '[]') into r from (
      select g.id, g.data, a.id campo, a.produtor, a.comunidade, a.zona, ac.nome equipa, ac.tecnico, ac.supervisor,
        pr.nome registada_por, g.ronda, privado.hl(g.entrada_em) entrada, privado.hl(g.agua_em) chegada_agua, privado.hl(g.saida_em) saida,
        case when g.agua_em between g.entrada_em and g.saida_em then round(extract(epoch from g.agua_em - g.entrada_em) / 60) end espera_min,
        round(extract(epoch from g.saida_em - coalesce(case when g.agua_em between g.entrada_em and g.saida_em then g.agua_em end, g.entrada_em)) / 60) duracao_rega_min,
        g.plantas_regadas, g.plantas_originais, g.pessoas,
        case when g.pessoas > 0 and g.saida_em > coalesce(case when g.agua_em between g.entrada_em and g.saida_em then g.agua_em end, g.entrada_em)
          then round(g.plantas_regadas / (g.pessoas * extract(epoch from g.saida_em - coalesce(case when g.agua_em between g.entrada_em and g.saida_em then g.agua_em end, g.entrada_em)) / 3600.0)) end ritmo_plantas_pessoa_hora,
        coalesce(a.vivas, a.instaladas) plantas_vivas_base, g.campo_fechado,
        (select json_agg(json_build_object('tipo', c.tipo, 'descricao', c.descricao, 'plantas', c.plantas)) from public.constrangimentos c where c.registo_id = g.id) constrangimentos,
        g.alerta, g.motivo_alerta, g.motivo_repetir, g.motivo_sugestao, g.motivo_itinerario, g.motivo_tecnico, g.observacao,
        g.gps_valido, round(g.distancia_area_m) distancia_campo_m, g.entrada_lat, g.entrada_lon,
        json_build_object('entrada', privado.ref_foto('rega-fotos', g.foto_entrada), 'rega', privado.ref_foto('rega-fotos', g.foto_rega), 'saida', privado.ref_foto('rega-fotos', g.foto_saida)) fotos, g.fotos_origem
      from public.registos_rega g join public.areas a on a.id = g.area_id
      left join public.activistas ac on ac.id = g.activista_id left join public.perfis pr on pr.id = g.user_id
      where not g.teste and g.data between p_de and p_ate
        and (p_comunidade is null or a.comunidade ilike p_comunidade) and (p_equipa is null or ac.nome ilike '%' || p_equipa || '%')) x;

  elsif p_tipo = 'dias_sem_rega' then
    select coalesce(json_agg(x order by x.data, x.equipa), '[]') into r from (
      select s.id, s.data, s.ate, ac.nome equipa, ac.comunidade_principal comunidade, s.motivo, s.todo_dia, s.descricao, s.area_id campo,
        pr.nome registado_por, privado.hl(s.criado_em) registado_em, pc.nome confirmado_por, privado.hl(s.confirmado_em) confirmado_em, s.confirmacao_nota,
        privado.ref_foto('rega-fotos', s.foto_path) foto
      from public.dias_sem_rega s join public.activistas ac on ac.id = s.activista_id
      left join public.perfis pr on pr.id = s.user_id left join public.perfis pc on pc.id = s.confirmado_por
      where not coalesce(s.removido, false) and not coalesce(s.substituido, false) and s.data <= p_ate and coalesce(s.ate, s.data) >= p_de
        and (p_comunidade is null or ac.comunidade_principal ilike p_comunidade) and (p_equipa is null or ac.nome ilike '%' || p_equipa || '%')) x;

  elsif p_tipo = 'equipas' then
    select coalesce(json_agg(x order by x.data, x.equipa), '[]') into r from (
      select d::date data, ac.nome equipa, ac.comunidade_principal comunidade, ac.tecnico, ac.supervisor, ac.equipa_tamanho tamanho,
        greatest((select max(g.pessoas) from public.registos_rega g where g.activista_id = ac.id and g.data = d::date and not g.teste),
                 (select max(j.pessoas) from public.jornadas j where j.activista_id = ac.id and j.data = d::date and not j.teste)) pessoas,
        (select privado.hl(min(j.inicio_em)) from public.jornadas j where j.activista_id = ac.id and j.data = d::date and not j.teste) inicio_do_dia,
        (select privado.hl(min(w.em)) from public.recolhas_agua w where w.activista_id = ac.id and w.data = d::date and not w.removido) foi_buscar_agua,
        (select privado.hl(min(g.entrada_em)) from public.registos_rega g where g.activista_id = ac.id and g.data = d::date and not g.teste) chegada_1o_campo,
        (select privado.hl(max(g.saida_em)) from public.registos_rega g where g.activista_id = ac.id and g.data = d::date and not g.teste) saida_ultimo_campo,
        (select count(*) from public.registos_rega g where g.activista_id = ac.id and g.data = d::date and not g.teste) regas,
        (select coalesce(sum(g.plantas_regadas), 0) from public.registos_rega g where g.activista_id = ac.id and g.data = d::date and not g.teste) plantas_regadas,
        (select string_agg(s.motivo, ', ') from public.dias_sem_rega s where s.activista_id = ac.id and not coalesce(s.removido, false)
           and not coalesce(s.substituido, false) and d::date between s.data and coalesce(s.ate, s.data)) motivo_sem_rega
      from public.activistas ac cross join generate_series(p_de, p_ate, interval '1 day') d
      where ac.activo and extract(isodow from d) < 7 and exists (select 1 from public.areas a where a.activista_id = ac.id and a.activa)
        and (p_comunidade is null or ac.comunidade_principal ilike p_comunidade) and (p_equipa is null or ac.nome ilike '%' || p_equipa || '%')) x;

  elsif p_tipo = 'campos' then
    select coalesce(json_agg(x order by x.comunidade, x.produtor, x.campo), '[]') into r from (
      select a.id campo, a.produtor, a.comunidade, a.zona,
        case when a.activa then 'na_rega' when u.valor_novo = 'false' then 'retirado' else 'fora_do_plano' end situacao,
        privado.hl(case when not a.activa and u.valor_novo = 'false' then u.em end) retirado_em,
        case when not a.activa and u.valor_novo = 'false' then coalesce(a.retirado_motivo || coalesce(': ' || u.motivo, ''), u.motivo) end retirado_motivo,
        ac.nome equipa, ac.tecnico, ac.supervisor, a.instaladas, a.vivas, a.latitude, a.longitude, a.agua_origem fonte_agua_base,
        (select count(*) from public.registos_rega g where g.area_id = a.id and not g.teste) regas_app,
        (select max(g.data) from public.registos_rega g where g.area_id = a.id and not g.teste) ultima_rega_app,
        a.wa_n regas_whatsapp, a.wa_ultima ultima_rega_whatsapp, coalesce(a.wa_por_pr, false) whatsapp_so_por_produtor
      from public.areas a left join public.activistas ac on ac.id = a.activista_id
      left join lateral (select z.valor_novo, z.em, z.motivo from public.alteracoes_areas z where z.area_id = a.id and z.campo = 'activa' order by z.em desc limit 1) u on true
      where (a.activa or u.valor_novo = 'false') and (p_comunidade is null or a.comunidade ilike p_comunidade)
        and (p_equipa is null or ac.nome ilike '%' || p_equipa || '%')) x;

  elsif p_tipo = 'recontagens' then
    select coalesce(json_agg(x order by x.pedida_em), '[]') into r from (
      select k.id, k.area_id campo, a.produtor, a.comunidade, k.motivo, k.estado, privado.hl(k.pedido_em) pedida_em, pp.nome pedida_por,
        po.nome oficial, privado.hl(k.contada_em) contada_em, k.vivas_antes, k.vivas, k.mortas, k.navuna oficial_confirmou_navuna,
        privado.hl(k.validada_em) validada_em, pv.nome validada_por, k.recusa_motivo,
        json_build_object('declaracao', privado.ref_foto('recontagem-fotos', k.foto_path), 'campo', privado.ref_foto('recontagem-fotos', k.foto_campo_path)) fotos
      from public.recontagens k join public.areas a on a.id = k.area_id
      left join public.perfis pp on pp.id = k.pedido_por left join public.perfis po on po.id = k.oficial_id left join public.perfis pv on pv.id = k.validada_por
      where (k.pedido_em at time zone 'Africa/Maputo')::date <= p_ate and coalesce((k.validada_em at time zone 'Africa/Maputo')::date, p_ate) >= p_de
        and (p_comunidade is null or a.comunidade ilike p_comunidade)) x;

  elsif p_tipo = 'manutencao' then
    select coalesce(json_agg(x order by x.data, x.campo), '[]') into r from (
      select m.id, m.data, m.area_id campo, a.produtor, a.comunidade, m.cavaroda cavaroda_total_campo, m.mulching mulching_total_campo,
        m.plantas_campo, m.pessoas sazonais, m.obs, pf.nome registado_por, privado.hl(m.feito_em) registado_em,
        coalesce(f.feito, false) campo_marcado_feito, privado.ref_foto('manutencao-fotos', m.foto_path) foto
      from public.manutencao_registos m join public.areas a on a.id = m.area_id left join public.perfis pf on pf.id = m.feito_por
      left join public.manutencao_feitos f on f.area_id = m.area_id
      where not m.removido and m.data between p_de and p_ate and (p_comunidade is null or a.comunidade ilike p_comunidade)) x;

  elsif p_tipo = 'acompanhamentos' then
    select coalesce(json_agg(x order by x.data), '[]') into r from (
      select o.id, o.data, o.area_id campo, a.produtor, a.comunidade, ac.nome equipa, p.nome feito_por, o.papel, privado.hl(o.feito_em) feito_em,
        o.distancia_m, o.observacao, privado.ref_foto('rega-fotos', o.foto_path) foto
      from public.acompanhamentos o join public.areas a on a.id = o.area_id left join public.activistas ac on ac.id = o.activista_id
      left join public.perfis p on p.id = o.perfil_id
      where not o.removido and not coalesce(o.teste, false) and o.data between p_de and p_ate and (p_comunidade is null or a.comunidade ilike p_comunidade)) x;

  elsif p_tipo = 'queimadas' then
    select coalesce(json_agg(x order by x.data), '[]') into r from (
      select q.id, q.data, q.area_id campo, a.produtor, a.comunidade, q.plantas_afectadas, q.plantas_mortas, q.observacao, p.nome registada_por,
        privado.ref_foto('rega-fotos', q.foto_path) foto
      from public.queimadas q join public.areas a on a.id = q.area_id left join public.perfis p on p.id = q.registada_por
      where not coalesce(q.removida, false) and q.data between p_de and p_ate and (p_comunidade is null or a.comunidade ilike p_comunidade)) x;

  elsif p_tipo = 'chuva' then
    select coalesce(json_agg(x order by x.data, x.comunidade), '[]') into r from (
      select c.id, c.data, c.comunidade, c.zona, c.pluviometro_id, c.mm, privado.hl(c.lida_em) lida_em, ac.nome equipa, c.observacao, privado.ref_foto('chuva-fotos', c.foto_path) foto
      from public.chuva c left join public.activistas ac on ac.id = c.activista_id
      where not c.teste and c.data between p_de and p_ate and (p_comunidade is null or c.comunidade ilike p_comunidade)) x;

  elsif p_tipo = 'monitorias' then
    select coalesce(json_agg(x order by x.data_rega), '[]') into r from (
      select m.id, m.data_rega, m.area_id campo, a.produtor, a.comunidade, p.nome verificador, privado.hl(m.feito_em) feito_em, m.metodo,
        m.plantas_alvo, m.pct_humido, m.nota, m.solo_regado, m.n_vivas, m.n_secas, m.n_mortas, m.observacao, privado.ref_foto('monitoria-fotos', m.foto_path) foto
      from public.monitorias m join public.areas a on a.id = m.area_id left join public.perfis p on p.id = m.verificador_id
      where m.data_rega between p_de and p_ate and (p_comunidade is null or a.comunidade ilike p_comunidade)) x;

  elsif p_tipo = 'idas_agua' then
    select coalesce(json_agg(x order by x.em), '[]') into r from (
      select w.data, ac.nome equipa, ac.comunidade_principal comunidade, privado.hl(w.em) em, w.lat, w.lon
      from public.recolhas_agua w join public.activistas ac on ac.id = w.activista_id
      where not w.removido and w.data between p_de and p_ate and (p_comunidade is null or ac.comunidade_principal ilike p_comunidade)) x;

  elsif p_tipo = 'resumo' then
    select json_build_object(
      'periodo', json_build_object('de', p_de, 'ate', p_ate),
      'campos_na_rega', (select count(*) from public.areas a where a.activa),
      'plantas_vivas_na_rega', (select sum(coalesce(nullif(a.vivas, 0), a.instaladas)) from public.areas a where a.activa),
      'regas', (select count(*) from public.registos_rega g where not g.teste and g.data between p_de and p_ate),
      'plantas_regadas', (select coalesce(sum(g.plantas_regadas), 0) from public.registos_rega g where not g.teste and g.data between p_de and p_ate),
      'campos_regados', (select count(distinct g.area_id) from public.registos_rega g where not g.teste and g.data between p_de and p_ate),
      'equipas_dia_com_rega', (select count(distinct (g.activista_id, g.data)) from public.registos_rega g where not g.teste and g.data between p_de and p_ate),
      'dias_sem_rega_por_motivo', (select json_object_agg(m, n) from (select s.motivo m, count(*) n from public.dias_sem_rega s
          where not coalesce(s.removido, false) and not coalesce(s.substituido, false) and s.data between p_de and p_ate group by 1) z),
      'nota', 'Ritmo = plantas regadas ÷ (pessoas × horas de rega, da chegada da água à saída). Datas e horas de Maputo. Regas de teste fora.') into r;
  else
    raise exception 'tipo desconhecido';
  end if;
  return r;
end $$;
revoke all on function public.api_dados(text, date, date, text, text) from public, anon, authenticated;

-- ---------- alarme: pedidos fora do normal (lido pela tarefa agendada, que envia o email) ----------
create or replace function public.api_alertas(p_desde timestamptz) returns json language sql stable security definer set search_path to '' as $$
  select json_build_object(
    'muitos_pedidos', (select coalesce(json_agg(z), '[]') from (select c.nome, date_trunc('hour', a.em) hora, count(*) n from public.api_acessos a
        join public.api_chaves c on c.id = a.chave_id where a.em >= p_desde group by 1, 2 having count(*) > 200) z),
    'fora_de_horas', (select coalesce(json_agg(z), '[]') from (select c.nome, count(*) n, privado.hl(min(a.em)) primeiro from public.api_acessos a
        join public.api_chaves c on c.id = a.chave_id where a.em >= p_desde
        and ((a.em at time zone 'Africa/Maputo')::time >= '22:00' or (a.em at time zone 'Africa/Maputo')::time < '05:00') group by 1) z),
    'ip_novo_endereco_directo', (select coalesce(json_agg(z), '[]') from (select c.nome, a.ip, privado.hl(min(a.em)) primeiro, count(*) n from public.api_acessos a
        join public.api_chaves c on c.id = a.chave_id where a.em >= p_desde and a.via = 'http'
        and not exists (select 1 from public.api_acessos b where b.chave_id = a.chave_id and b.ip = a.ip and b.em < p_desde and b.em > p_desde - interval '30 days')
        group by 1, 2) z),
    'chaves_erradas', (select count(*) from public.api_acessos a where a.chave_id is null and a.em >= p_desde),
    'pedidos_recusados_por_limite', (select count(*) from public.api_acessos a where a.estado = 429 and a.em >= p_desde));
$$;
revoke all on function public.api_alertas(timestamptz) from public, anon, authenticated;
