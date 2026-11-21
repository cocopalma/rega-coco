-- v251 (21/11/2026, Valdo: "Sim"): inventário de plantas mórbidas (método do Paulo Dias, 20/11/2026, grupo Coordenação Agrícola):
-- em cada campo visitado, o técnico ou o supervisor observa uma amostra de plantas e conta as mórbidas (estioladas por falta de
-- água); % = mórbidas ÷ amostra × 100; fotografia do campo com as plantas mórbidas e a amostra; fotografia do técnico com o
-- activista. Fica com campo, data e GPS (Valdo: "sairmos dos relatórios manuais e WhatsApp para os sistemas").
create table if not exists public.inventarios_morbidas (
  id uuid primary key,
  area_id text not null references public.areas(id),
  activista_id uuid,
  data date not null,
  feito_em timestamptz not null,
  perfil_id uuid not null,
  papel text,
  amostra int not null check (amostra between 1 and 5000),
  morbidas int not null check (morbidas >= 0 and morbidas <= amostra),
  lat double precision, lon double precision, precisao_m int, distancia_m int,
  foto_campo text not null,
  foto_equipa text not null,
  observacao text,
  removido boolean not null default false,
  removido_por uuid, removido_em timestamptz,
  criado_em timestamptz not null default now()
);
create index if not exists inventarios_morbidas_area on public.inventarios_morbidas (area_id, data);
create index if not exists inventarios_morbidas_data on public.inventarios_morbidas (data);
alter table public.inventarios_morbidas enable row level security;
revoke all on public.inventarios_morbidas from anon, authenticated;
drop trigger if exists guarda_so_teste on public.inventarios_morbidas;
create trigger guarda_so_teste before insert or update or delete on public.inventarios_morbidas
  for each row execute function privado.guarda_so_teste();

create or replace function public.gravar_inventario_morbidas(p_id uuid, p_area text, p_feito_em timestamptz, p_amostra int, p_morbidas int,
  p_lat double precision, p_lon double precision, p_precisao int, p_distancia int, p_foto_campo text, p_foto_equipa text, p_obs text)
 returns jsonb language plpgsql security definer set search_path to '' as $function$
declare v_papel text := privado.meu_papel(); v_a record; v_data date; v_hoje date := (now() at time zone 'Africa/Maputo')::date;
begin
  if v_papel is null or v_papel not in ('tecnico','supervisor','gestor') then raise exception 'Só técnicos, supervisores e o gestor registam o inventário.'; end if;
  if exists (select 1 from public.inventarios_morbidas where id = p_id) then return jsonb_build_object('id', p_id, 'repetido', true); end if;
  select id, activista_id, comunidade into v_a from public.areas where id = p_area and activa;
  if v_a.id is null then raise exception 'Campo não encontrado.'; end if;
  if not privado.le_area(v_a.activista_id, v_a.comunidade) then raise exception 'Não pode ver este campo.'; end if;
  if coalesce(p_amostra, 0) < 1 then raise exception 'Escreva o número de plantas observadas.'; end if;
  if p_morbidas is null or p_morbidas < 0 or p_morbidas > p_amostra then raise exception 'As plantas mórbidas não podem passar as plantas observadas.'; end if;
  if p_foto_campo is null or p_foto_campo not like auth.uid()::text || '/%' then raise exception 'Falta a fotografia do campo.'; end if;
  if p_foto_equipa is null or p_foto_equipa not like auth.uid()::text || '/%' then raise exception 'Falta a fotografia do técnico com o activista.'; end if;
  v_data := (coalesce(p_feito_em, now()) at time zone 'Africa/Maputo')::date;
  if v_data > v_hoje or v_data < v_hoje - 7 then raise exception 'Data fora do prazo (últimos 7 dias).'; end if;
  if p_lat is not null and (p_lat not between -12 and -9 or p_lon not between 39 and 41.5) then raise exception 'Ponto fora da zona do projecto.'; end if;
  insert into public.inventarios_morbidas (id, area_id, activista_id, data, feito_em, perfil_id, papel, amostra, morbidas, lat, lon, precisao_m, distancia_m, foto_campo, foto_equipa, observacao)
  values (p_id, p_area, v_a.activista_id, v_data, coalesce(p_feito_em, now()), auth.uid(), v_papel, p_amostra, p_morbidas, p_lat, p_lon, p_precisao, p_distancia,
          p_foto_campo, p_foto_equipa, nullif(trim(coalesce(p_obs, '')), ''));
  return jsonb_build_object('id', p_id);
end $function$;

create or replace function public.inventarios_morbidas_campo(p_area text)
 returns table(id uuid, data date, feito_em timestamptz, quem text, papel text, amostra int, morbidas int, foto_campo text, foto_equipa text,
               observacao text, distancia_m int, meu boolean)
 language sql stable security definer set search_path to '' as $function$
  select c.id, c.data, c.feito_em, p.nome, c.papel, c.amostra, c.morbidas,
         case when privado.meu_papel() = 'activista' and c.foto_campo not like auth.uid()::text || '/%' then null else c.foto_campo end,
         case when privado.meu_papel() = 'activista' and c.foto_equipa not like auth.uid()::text || '/%' then null else c.foto_equipa end,
         c.observacao, c.distancia_m, c.perfil_id = auth.uid()
  from public.inventarios_morbidas c join public.areas a on a.id = c.area_id left join public.perfis p on p.id = c.perfil_id
  where c.area_id = p_area and not c.removido and privado.meu_papel() is not null and privado.meu_papel() <> 'oficial_me'
    and privado.le_area(a.activista_id, a.comunidade)
  order by c.feito_em desc limit 20
$function$;

create or replace function public.remover_inventario_morbidas(p_id uuid)
 returns void language plpgsql security definer set search_path to '' as $function$
begin
  update public.inventarios_morbidas set removido = true, removido_por = auth.uid(), removido_em = now()
   where id = p_id and not removido and (perfil_id = auth.uid() or privado.meu_papel() = 'gestor') and data >= (now() at time zone 'Africa/Maputo')::date - 7;
  if not found then raise exception 'Só quem registou (até 7 dias) ou o gestor pode remover.'; end if;
end $function$;

-- painel: uma linha por inventário no período (datas nulas = todo o histórico); null ao cliente, ao activista e ao oficial
create or replace function public.painel_morbidas(p_de date default null, p_ate date default null)
 returns jsonb language plpgsql stable security definer set search_path to '' as $function$
declare v_papel text := privado.meu_papel();
begin
  if v_papel is null or v_papel not in ('gestor','director','me','tecnico','supervisor') then return null; end if;
  return coalesce((select jsonb_agg(jsonb_build_object(
      'id', c.id, 'data', c.data, 'feito_em', c.feito_em, 'area_id', c.area_id, 'pr', a.pr, 'area_n', a.area_n, 'produtor', a.produtor,
      'comunidade', a.comunidade, 'zona', a.zona, 'equipa', ac.nome, 'quem', p.nome, 'papel', c.papel,
      'amostra', c.amostra, 'morbidas', c.morbidas, 'vivas', a.vivas, 'instaladas', a.instaladas,
      'foto_campo', c.foto_campo, 'foto_equipa', c.foto_equipa, 'observacao', c.observacao) order by c.data desc, c.feito_em desc)
    from public.inventarios_morbidas c join public.areas a on a.id = c.area_id
    left join public.activistas ac on ac.id = c.activista_id left join public.perfis p on p.id = c.perfil_id
    where not c.removido and (p_de is null or c.data >= p_de) and (p_ate is null or c.data <= p_ate)
      and privado.le_area(a.activista_id, a.comunidade)), '[]'::jsonb);
end $function$;

revoke all on function public.gravar_inventario_morbidas(uuid, text, timestamptz, int, int, double precision, double precision, int, int, text, text, text) from public, anon;
revoke all on function public.inventarios_morbidas_campo(text) from public, anon;
revoke all on function public.remover_inventario_morbidas(uuid) from public, anon;
revoke all on function public.painel_morbidas(date, date) from public, anon;
grant execute on function public.gravar_inventario_morbidas(uuid, text, timestamptz, int, int, double precision, double precision, int, int, text, text, text) to authenticated;
grant execute on function public.inventarios_morbidas_campo(text) to authenticated;
grant execute on function public.remover_inventario_morbidas(uuid) to authenticated;
grant execute on function public.painel_morbidas(date, date) to authenticated;
