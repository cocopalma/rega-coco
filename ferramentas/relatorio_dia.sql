-- Dados do relatório do dia para a pasta partilhada com o Dalmar (tarefa das 19:00; ver ferramentas/RELATORIO_DRIVE.md).
-- Só leitura. Antes de correr, substituir __DIA__ pela data (AAAA-MM-DD, hora de Maputo).
-- Devolve uma linha com uma coluna «dados» (JSON) que vai tal e qual para ferramentas/relatorio_dia.py.
with p as (select date '__DIA__' as dia),
eq as (
  select a.id, a.nome, a.tecnico, a.supervisor, a.comunidade_principal as comunidade, coalesce(a.sem_telefone, false) as sem_telefone
  from public.activistas a
  where a.activo and exists (select 1 from public.areas r where r.activista_id = a.id and r.activa)
),
rg as (
  select r.* from public.registos_rega r, p where r.data = p.dia and not r.teste
),
cons as (
  select c.registo_id, c.tipo, c.descricao, c.plantas from public.constrangimentos c join rg on rg.id = c.registo_id
),
mot as (
  select d.activista_id, d.motivo, d.descricao, d.todo_dia
  from public.dias_sem_rega d, p
  where not d.removido and not coalesce(d.substituido, false) and d.data <= p.dia and p.dia <= coalesce(d.ate, d.data)
),
jor as (
  select j.activista_id, max(j.pessoas) as pessoas, min(j.inicio_em) as inicio_em
  from public.jornadas j, p where j.data = p.dia and not j.teste group by 1
),
ron as (select * from privado.rondas()),
por_eq as (
  select e.*,
    (select count(*) from rg where rg.activista_id = e.id)::int as regas,
    (select count(distinct rg.area_id) from rg where rg.activista_id = e.id)::int as campos,
    (select coalesce(sum(rg.plantas_regadas), 0) from rg where rg.activista_id = e.id)::int as plantas,
    coalesce((select max(rg.pessoas) from rg where rg.activista_id = e.id), (select jor.pessoas from jor where jor.activista_id = e.id)) as pessoas,
    (select to_char(min(rg.entrada_em) at time zone 'Africa/Maputo', 'HH24:MI') from rg where rg.activista_id = e.id) as chegada_1o_campo,
    (select to_char(jor.inicio_em at time zone 'Africa/Maputo', 'HH24:MI') from jor where jor.activista_id = e.id) as inicio_dia,
    (select count(*) from rg where rg.activista_id = e.id and rg.campo_fechado = false)::int as campos_por_terminar_hoje,
    ron.lista as campos_na_lista, ron.ronda_actual, ron.regadas_ronda,
    (select coalesce(json_agg(json_build_object('motivo', mot.motivo, 'descricao', mot.descricao, 'todo_dia', mot.todo_dia)), '[]') from mot where mot.activista_id = e.id) as motivos,
    (select coalesce(json_agg(distinct jsonb_build_object('tipo', c.tipo, 'descricao', c.descricao, 'plantas', c.plantas, 'pr', ar.pr || '-' || ar.area_n)), '[]')
       from cons c join rg on rg.id = c.registo_id join public.areas ar on ar.id = rg.area_id where rg.activista_id = e.id) as constrangimentos
  from eq e left join ron on ron.activista_id = e.id
),
nunca as (
  select a.activista_id, count(*)::int n
  from public.areas a
  where a.activa and a.activista_id is not null
    and not exists (select 1 from public.registos_rega r where r.area_id = a.id and not r.teste)
    and (a.wa_ultima is null or coalesce(a.wa_por_pr, false))
    and (coalesce(cardinality(a.datas_rega_origem), 0) = 0 or coalesce(a.regas_origem_por_pr, false))
  group by 1
),
man as (
  select a.id, a.comunidade, privado.manut_plantas(a.id) as plantas, a.manut_sem_plantas,
         u.cavaroda, u.mulching, coalesce(f.feito, false) as feito
  from public.areas a join public.manutencao_comunidades c on c.comunidade = a.comunidade
  left join lateral (select r.cavaroda, r.mulching from public.manutencao_registos r
                     where r.area_id = a.id and not r.removido and privado.manut_conta(r.feito_em)
                     order by r.feito_em desc limit 1) u on true
  left join public.manutencao_feitos f on f.area_id = a.id and privado.manut_conta(f.marcado_em)
),
man_dia as (
  select d.area_id, d.data, greatest(d.cavaroda - d.ant_c, 0) as cavaroda, greatest(d.mulching - d.ant_m, 0) as mulching, d.pessoas
  from (select r.area_id, r.data, r.cavaroda, r.mulching, r.pessoas,
               coalesce(lag(r.cavaroda) over w, 0) as ant_c, coalesce(lag(r.mulching) over w, 0) as ant_m
        from public.manutencao_registos r where not r.removido and privado.manut_conta(r.feito_em)
        window w as (partition by r.area_id order by r.feito_em)) d
),
cini as (select coalesce((select (valor #>> '{}')::date from public.config where chave = 'cumprimento_inicio'), date '2026-10-29') as d),
hcheg as (select coalesce((select valor #>> '{}' from public.config where chave = 'hora_chegada_equipa'), '06:00') as h),
pess as (
  select pf.id, pf.nome, pf.papel from public.perfis pf
  where pf.id in (select privado.monitores()) and exists (select 1 from privado.equipas_de(pf.id))
),
pe as (select ps.id as perfil_id, t as activista_id from pess ps, lateral privado.equipas_de(ps.id) t),
dias as (
  select g::date as d from p, cini, generate_series(cini.d, p.dia, interval '1 day') g where extract(isodow from g) < 7
),
regd as (
  select r.activista_id, r.data, min(r.entrada_em) as primeira,
         count(*) filter (where r.alerta = 'fora_da_lista' and r.motivo_alerta like 'Sem justifica%') as fora_sem_motivo
  from public.registos_rega r, cini, p where not r.teste and r.data between cini.d and p.dia group by 1, 2
),
jord as (select distinct j.activista_id, j.data from public.jornadas j, cini, p where not j.teste and j.data between cini.d and p.dia),
pd as (
  select ps.id as perfil_id, ps.nome, ps.papel, dd.d,
    (select coalesce(json_agg(a.nome order by a.nome), '[]') from pe join public.activistas a on a.id = pe.activista_id
       where pe.perfil_id = ps.id
         and not exists (select 1 from regd where regd.activista_id = pe.activista_id and regd.data = dd.d)
         and not exists (select 1 from jord where jord.activista_id = pe.activista_id and jord.data = dd.d)
         and not exists (select 1 from privado.motivos_dia(pe.activista_id, dd.d))) as r1,
    (select to_char(f.fechado_em at time zone 'Africa/Maputo', 'HH24:MI') from public.fechos_dia f where f.perfil_id = ps.id and f.data = dd.d) as fecho,
    (select count(*) from public.monitoria_amostra m where m.verificador_id = ps.id and privado.dia_verif(m.data_rega) = dd.d
       and not exists (select 1 from public.monitorias mo where mo.amostra_id = m.id))::int as r3,
    -- v235: 'agua' = hora em que a equipa foi buscar água antes do campo (razão da chegada tardia), se registada
    (select coalesce(json_agg(json_build_object('nome', a.nome, 'hora', to_char(regd.primeira at time zone 'Africa/Maputo', 'HH24:MI'),
        'agua', (select to_char(min(w.em) at time zone 'Africa/Maputo', 'HH24:MI') from public.recolhas_agua w where w.activista_id = pe.activista_id and w.data = dd.d and not w.removido)) order by regd.primeira), '[]')
       from pe join regd on regd.activista_id = pe.activista_id and regd.data = dd.d join public.activistas a on a.id = pe.activista_id, hcheg
       where pe.perfil_id = ps.id and to_char(regd.primeira at time zone 'Africa/Maputo', 'HH24:MI') > hcheg.h) as r5,
    (select coalesce(sum(regd.fora_sem_motivo), 0) from pe join regd on regd.activista_id = pe.activista_id and regd.data = dd.d where pe.perfil_id = ps.id)::int as r6
  from pess ps, dias dd
)
select json_build_object(
  'data', (select dia from p),
  'gerado_em', to_char(now() at time zone 'Africa/Maputo', 'YYYY-MM-DD"T"HH24:MI'),
  'fonte', 'App Rega Coco (servidor), regas reais (sem testes)',
  'rega', json_build_object(
    'equipas_total', (select count(*) from eq),
    'equipas_com_rega', (select count(*) from por_eq where regas > 0),
    'regas', (select count(*) from rg),
    'campos_regados', (select count(distinct area_id) from rg),
    'plantas_regadas', (select coalesce(sum(plantas_regadas), 0) from rg),
    'pessoas', (select coalesce(sum(pessoas), 0) from por_eq where regas > 0),
    'plantas_acumuladas_app', (select coalesce(sum(r.plantas_regadas), 0) from public.registos_rega r, p
                               where not r.teste and r.data <= p.dia
                                 and r.data >= (select (valor #>> '{}')::date from public.config where chave = 'activistas_inicio')),
    'desde', (select valor #>> '{}' from public.config where chave = 'activistas_inicio'),
    'campos_na_rega', (select count(*) from public.areas where activa),
    'campos_sem_equipa', (select count(*) from public.areas where activa and activista_id is null),
    'campos_ronda_regados', (select coalesce(sum(regadas_ronda), 0) from ron),
    'campos_ronda_lista', (select coalesce(sum(lista), 0) from ron),
    'campos_nunca_receberam_agua', (select coalesce(sum(n), 0) from nunca),
    'hora_combinada_chegada', (select valor #>> '{}' from public.config where chave = 'hora_chegada_equipa'),
    'por_equipa', (select coalesce(json_agg(json_build_object(
        'activista', e.nome, 'tecnico', e.tecnico, 'supervisor', e.supervisor, 'comunidade', e.comunidade,
        'sem_telefone', e.sem_telefone, 'regas', e.regas, 'campos', e.campos, 'plantas', e.plantas, 'pessoas', e.pessoas,
        'chegada_1o_campo', e.chegada_1o_campo, 'inicio_dia', e.inicio_dia, 'campos_por_terminar_hoje', e.campos_por_terminar_hoje,
        'ronda_actual', e.ronda_actual, 'campos_na_lista', e.campos_na_lista, 'regados_na_ronda', e.regadas_ronda,
        'nunca_receberam_agua', coalesce((select n from nunca where nunca.activista_id = e.id), 0),
        'motivos_sem_rega', e.motivos, 'constrangimentos', e.constrangimentos)
        order by e.plantas desc, e.nome), '[]') from por_eq e),
    'por_comunidade', (select coalesce(json_agg(x order by x.plantas desc), '[]') from (
        select a.comunidade, count(*)::int as regas, count(distinct rg.area_id)::int as campos, sum(rg.plantas_regadas)::int as plantas
        from rg join public.areas a on a.id = rg.area_id group by a.comunidade) x)
  ),
  'manutencao', json_build_object(
    'inicio', (select valor #>> '{}' from public.config where chave = 'manutencao_inicio'),
    'por_comunidade', (select coalesce(json_agg(x order by x.comunidade), '[]') from (
        select comunidade, count(*)::int as campos, sum(plantas)::int as plantas,
          sum(least(coalesce(cavaroda, 0), plantas))::int as cavaroda,
          sum(least(coalesce(mulching, 0), plantas))::int as mulching,
          count(*) filter (where feito)::int as feitos,
          count(*) filter (where not feito and plantas > 0 and cavaroda >= plantas and mulching >= plantas)::int as completos,
          count(*) filter (where cavaroda is not null and manut_sem_plantas is null and not feito and not (cavaroda >= plantas and mulching >= plantas))::int as em_curso,
          count(*) filter (where cavaroda is null and manut_sem_plantas is null and not feito)::int as por_fazer,
          count(*) filter (where manut_sem_plantas is not null and not feito)::int as sem_plantas
        from man group by comunidade) x),
    'hoje', (select json_build_object('campos', count(distinct d.area_id), 'cavaroda', coalesce(sum(d.cavaroda), 0),
                                      'mulching', coalesce(sum(d.mulching), 0))
             from man_dia d, p where d.data = p.dia),
    'hoje_por_comunidade', (select coalesce(json_agg(x order by x.comunidade), '[]') from (
        select a.comunidade, count(distinct d.area_id)::int as campos, sum(d.cavaroda)::int as cavaroda, sum(d.mulching)::int as mulching
        from man_dia d join public.areas a on a.id = d.area_id, p where d.data = p.dia group by a.comunidade) x)
  ),
  'cumprimento', json_build_object(
    'inicio', (select d from cini),
    'hora_chegada', (select h from hcheg),
    -- 08/11/2026 (Valdo): monitoria parada até nova decisão; com a pausa o relatório não conta «campo da monitoria não verificado»
    'monitoria_pausa', coalesce((select (valor #>> '{}')::boolean from public.config where chave = 'monitoria_pausa'), false),
    'pessoas', (select coalesce(json_agg(x order by x.papel desc, x.nome), '[]') from (
      select ps.nome, ps.papel,
        (select count(*) from pe where pe.perfil_id = ps.id)::int as equipas,
        (select coalesce(json_agg(json_build_object('data', pd.d, 'r1', pd.r1, 'fecho', pd.fecho, 'r3', pd.r3, 'r5', pd.r5, 'r6', pd.r6) order by pd.d), '[]')
           from pd where pd.perfil_id = ps.id) as dias,
        (select count(*) from privado.regas_alerta((select (valor #>> '{}')::date from public.config where chave = 'activistas_inicio'), (select dia from p)) ra
           where not ra.tratado and ra.activista_id in (select activista_id from pe where pe.perfil_id = ps.id))::int as r4_por_tratar,
        (select count(*) from public.dias_sem_rega ds
           where ds.activista_id in (select activista_id from pe where pe.perfil_id = ps.id)
             and not ds.removido and not coalesce(ds.substituido, false)
             and privado.dsr_pc(ds.user_id, ds.confirmado_em, ds.data, ds.ate))::int as r8_por_confirmar
      from pess ps) x)
  ),
  -- 12/11/2026 (Valdo: "sim"): lista completa dos campos (na rega + retirados), para o painel do Dalmar usar a mesma base.
  -- Estado do campo = o de agora (quando os dados foram lidos); regas da app até ao dia do relatório. Sem telefones nem texto livre.
  'campos', (
    with ult as (select distinct on (area_id) area_id, valor_novo, em from public.alteracoes_areas where campo = 'activa' order by area_id, em desc),
    rgc as (select r.area_id, count(*)::int n, sum(coalesce(r.plantas_regadas, 0))::int plantas, min(r.data) primeira, max(r.data) ultima
            from public.registos_rega r, p where not r.teste and r.data <= p.dia group by r.area_id),
    b as (select a.*, t.nome as activista_nome, t.tecnico as tec, t.supervisor as sup, rgc.n as app_n, rgc.plantas as app_plantas,
            rgc.primeira as app_primeira, rgc.ultima as app_ultima,
            case when not a.activa and u.valor_novo in ('false', 'f') then (u.em at time zone 'Africa/Maputo')::date end as ret_em,
            (rgc.n is null and (a.wa_ultima is null or coalesce(a.wa_por_pr, false))
             and (coalesce(cardinality(a.datas_rega_origem), 0) = 0 or coalesce(a.regas_origem_por_pr, false))) as nunca
          from public.areas a left join public.activistas t on t.id = a.activista_id
          left join rgc on rgc.area_id = a.id left join ult u on u.area_id = a.id)
    select coalesce(json_agg(json_build_object(
        'campo', b.pr || coalesce('-' || b.area_n, ''), 'pr', b.pr, 'produtor', b.produtor, 'comunidade', b.comunidade, 'zona', b.zona,
        'situacao', case when not b.activa then 'retirado' when b.nunca then 'na_rega_nunca_recebeu_agua' else 'na_rega_ja_recebeu_agua' end,
        'origem', case when b.fonte ilike '%REGA=NÃO%' then 'acrescentado_na_app' when b.fonte ilike '%REGA=SIM%' then 'plano_0910' when b.fonte ilike 'Separado%' then 'campo_dividido' else 'outro' end,
        'posto_na_rega_em', (b.reactivada_em at time zone 'Africa/Maputo')::date,
        'activista', b.activista_nome, 'tecnico', b.tec, 'supervisor', b.sup,
        'vivas', b.vivas, 'instaladas', b.instaladas, 'lat', b.latitude, 'lon', b.longitude,
        'app_regas', coalesce(b.app_n, 0), 'app_plantas', coalesce(b.app_plantas, 0), 'app_primeira', b.app_primeira, 'app_ultima', b.app_ultima,
        'wa_regas', coalesce(b.wa_n, 0), 'wa_ultima', b.wa_ultima, 'wa_so_por_produtor', coalesce(b.wa_por_pr, false) and b.wa_ultima is not null,
        'antes_app_regas', case when coalesce(b.regas_origem_por_pr, false) then 0 else coalesce(cardinality(b.datas_rega_origem), 0) end,
        'campos_do_mesmo_pr', (select count(*) from public.areas z where z.pr = b.pr)::int,
        'retirado_em', b.ret_em, 'retirado_motivo', case when b.ret_em is not null then coalesce(b.retirado_motivo, 'decisao_do_gestor') end)
      order by b.activa desc, b.comunidade, b.produtor, b.area_n), '[]')
    from b where b.activa or b.ret_em is not null)
) as dados;
