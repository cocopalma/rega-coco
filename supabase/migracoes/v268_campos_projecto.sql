-- v268 (27/11/2026, Valdo: "coloca todos os campos que existem no projecto, mas só visíveis para mim";
--   10:04: "Deixa visível também para o Paulo e para Luciano e para o Dalmar")
-- 0) perfis.ve_campos_projecto: quem vê os campos fora da rega (Valdo, Dalmar, Paulo, Luciano). Muda-se por SQL.
-- 1) privado.gestor_principal(): papel gestor + gere_acessos + sem so_teste (hoje só o Valdo).
-- 2) campos_projecto(): todos os campos fora da rega (activa = false) com a situação: 'retirado' (já esteve na rega;
--    a última alteração de 'activa' foi para false) ou 'fora' (nunca entrou na rega: importados com REGA=NÃO).
--    Só para quem tem ve_campos_projecto; os outros recebem null.
-- 3) gestao_equipa_campo: só o gestor principal (antes bastava gere_acessos, que é true por defeito em quase todos os perfis).
alter table public.perfis add column if not exists ve_campos_projecto boolean not null default false;
update public.perfis set ve_campos_projecto = true
 where nome in ('Etevaldo Cheveia (Valdo)', 'Dalmar Santos', 'Paulo Dias', 'Luciano Lima');
create or replace function privado.ve_campos_projecto() returns boolean
language sql stable security definer set search_path to '' as $f$
  select coalesce((select p.ve_campos_projecto from public.perfis p where p.id = auth.uid()), false)
$f$;

create or replace function privado.gestor_principal() returns boolean
language sql stable security definer set search_path to '' as $f$
  select coalesce((select p.papel = 'gestor' and p.gere_acessos is true and p.so_teste is not true
                   from public.perfis p where p.id = auth.uid()), false)
$f$;

create or replace function public.campos_projecto() returns json
language plpgsql stable security definer set search_path to '' as $f$
declare v json;
begin
  if not privado.ve_campos_projecto() then return null; end if;
  with ult as (
    select distinct on (x.area_id) x.area_id, x.valor_novo, x.em, x.motivo, x.user_id
    from public.alteracoes_areas x where x.campo = 'activa' order by x.area_id, x.em desc),
  rg as (
    select r.area_id, count(*) n, count(distinct r.data) filter (where r.plantas_regadas > 0) dias, max(r.data) ultima, sum(r.plantas_regadas) plantas
    from public.registos_rega r join public.areas a on a.id = r.area_id
    where not r.teste and not a.activa group by r.area_id)
  select coalesce(json_agg(json_build_object(
    'id', a.id, 'pr', a.pr, 'area_n', a.area_n, 'comunidade', a.comunidade, 'zona', a.zona, 'produtor', a.produtor,
    'instaladas', a.instaladas, 'vivas', a.vivas, 'latitude', a.latitude, 'longitude', a.longitude,
    'activista_id', a.activista_id, 'activista', ac.nome, 'activista_origem', a.activista_origem, 'data_plantio', a.data_plantio,
    'poligono', a.poligono, 'area_m2', coalesce(round(a.area_m2), case when a.poligono is not null then round(privado.area_poligono_m2(a.poligono)) end),
    'area_medida', a.area_m2 is not null,
    'n_regas_origem', a.n_regas_origem, 'ultima_rega_origem', a.ultima_rega_origem, 'regas_origem_por_pr', a.regas_origem_por_pr,
    'wa_ultima', a.wa_ultima, 'wa_n', a.wa_n, 'wa_por_pr', a.wa_por_pr,
    'situacao_origem', a.situacao_origem, 'agua_origem', a.agua_origem, 'nao_existe', coalesce(a.nao_existe, false),
    'situacao', case when u.area_id is not null then 'retirado' else 'fora' end,
    'retirado_em', coalesce(a.retirado_em, u.em), 'retirado_motivo', a.retirado_motivo, 'retirado_texto', u.motivo,
    'retirado_por', coalesce(pr.nome, pu.nome), 'reactivada_em', a.reactivada_em,
    'regas_app', coalesce(rg.n, 0), 'dias_app', coalesce(rg.dias, 0), 'ultima_app', rg.ultima, 'plantas_app', coalesce(rg.plantas, 0)
  ) order by a.comunidade, a.produtor), '[]'::json) into v
  from public.areas a
  left join ult u on u.area_id = a.id and u.valor_novo ilike 'f%'
  left join public.activistas ac on ac.id = a.activista_id
  left join public.perfis pr on pr.id = a.retirado_por
  left join public.perfis pu on pu.id = u.user_id
  left join rg on rg.area_id = a.id
  where not a.activa;
  return v;
end $f$;
revoke all on function public.campos_projecto() from public, anon;
grant execute on function public.campos_projecto() to authenticated;
revoke all on function privado.gestor_principal() from public, anon;
grant execute on function privado.gestor_principal() to authenticated;

do $d$ declare s text;
begin
  s := pg_get_functiondef('public.gestao_equipa_campo(date)'::regprocedure);
  if position('if not coalesce(privado.gere_acessos(), false) then return null; end if;' in s) = 0 then raise exception 'gestao_equipa_campo mudou: rever'; end if;
  execute replace(s, 'if not coalesce(privado.gere_acessos(), false) then return null; end if;', 'if not privado.gestor_principal() then return null; end if;');
end $d$;
