-- v254 (21/11/2026, Valdo: "O técnico supervisor, quando abrir a ficha do campo, tem que saber quantas plantas vai verificar e tem
-- que dizer qual foi o método que usou… a aplicação já tem que lhe dizer quantas plantas vai verificar."):
-- o inventário de plantas mórbidas guarda o percurso (X, W, Z, Diagonal, como a monitoria), as plantas no campo usadas no cálculo
-- e as plantas a verificar que a app calculou (Cochran 95 %, ±15 %, p = 50 % — a amostragem mais segura, Valdo 21/11/2026 — com correcção para população finita).
-- Só acrescenta: a gravar_inventario_morbidas antiga fica para versões em cache (sem método).
alter table public.inventarios_morbidas add column if not exists metodo text;
alter table public.inventarios_morbidas add column if not exists plantas_campo int;
alter table public.inventarios_morbidas add column if not exists plantas_alvo int;
alter table public.inventarios_morbidas add column if not exists campo_corrigido boolean;

create or replace function public.gravar_inventario_morbidas2(p_id uuid, p_area text, p_feito_em timestamptz, p_amostra int, p_morbidas int,
  p_lat double precision, p_lon double precision, p_precisao int, p_distancia int, p_foto_campo text, p_foto_equipa text, p_obs text,
  p_metodo text, p_plantas_campo int, p_plantas_alvo int, p_campo_corrigido boolean)
 returns jsonb language plpgsql security definer set search_path to '' as $function$
declare v jsonb;
begin
  if p_metodo is null or p_metodo not in ('X','W','Z','Diagonal') then raise exception 'Escolha o percurso que usou no campo (X, W, Z ou Diagonal).'; end if;
  if p_plantas_campo is not null and (p_plantas_campo < 1 or p_plantas_campo > 50000) then raise exception 'Número de plantas no campo fora do limite.'; end if;
  if p_plantas_alvo is not null and (p_plantas_alvo < 1 or p_plantas_alvo > 5000) then raise exception 'Número de plantas a verificar fora do limite.'; end if;
  v := public.gravar_inventario_morbidas(p_id, p_area, p_feito_em, p_amostra, p_morbidas, p_lat, p_lon, p_precisao, p_distancia, p_foto_campo, p_foto_equipa, p_obs);
  if coalesce((v->>'repetido')::boolean, false) then return v; end if;
  update public.inventarios_morbidas set metodo = p_metodo, plantas_campo = p_plantas_campo, plantas_alvo = p_plantas_alvo,
         campo_corrigido = coalesce(p_campo_corrigido, false)
   where id = p_id;
  return v;
end $function$;

drop function if exists public.inventarios_morbidas_campo(text);
create function public.inventarios_morbidas_campo(p_area text)
 returns table(id uuid, data date, feito_em timestamptz, quem text, papel text, amostra int, morbidas int, foto_campo text, foto_equipa text,
               observacao text, distancia_m int, meu boolean, metodo text, plantas_campo int, plantas_alvo int)
 language sql stable security definer set search_path to '' as $function$
  select c.id, c.data, c.feito_em, p.nome, c.papel, c.amostra, c.morbidas,
         case when privado.meu_papel() = 'activista' and c.foto_campo not like auth.uid()::text || '/%' then null else c.foto_campo end,
         case when privado.meu_papel() = 'activista' and c.foto_equipa not like auth.uid()::text || '/%' then null else c.foto_equipa end,
         c.observacao, c.distancia_m, c.perfil_id = auth.uid(), c.metodo, c.plantas_campo, c.plantas_alvo
  from public.inventarios_morbidas c join public.areas a on a.id = c.area_id left join public.perfis p on p.id = c.perfil_id
  where c.area_id = p_area and not c.removido and privado.meu_papel() is not null and privado.meu_papel() <> 'oficial_me'
    and privado.le_area(a.activista_id, a.comunidade)
  order by c.feito_em desc limit 20
$function$;

create or replace function public.painel_morbidas(p_de date default null, p_ate date default null)
 returns jsonb language plpgsql stable security definer set search_path to '' as $function$
declare v_papel text := privado.meu_papel();
begin
  if v_papel is null or v_papel not in ('gestor','director','me','tecnico','supervisor','cliente') then return null; end if;
  return coalesce((select jsonb_agg(jsonb_build_object(
      'id', c.id, 'data', c.data, 'feito_em', c.feito_em, 'area_id', c.area_id, 'pr', a.pr, 'area_n', a.area_n, 'produtor', a.produtor,
      'comunidade', a.comunidade, 'zona', a.zona, 'equipa', ac.nome, 'quem', p.nome, 'papel', c.papel,
      'amostra', c.amostra, 'morbidas', c.morbidas, 'vivas', a.vivas, 'instaladas', a.instaladas,
      'metodo', c.metodo, 'plantas_campo', c.plantas_campo, 'plantas_alvo', c.plantas_alvo,
      'foto_campo', c.foto_campo, 'foto_equipa', c.foto_equipa, 'observacao', c.observacao) order by c.data desc, c.feito_em desc)
    from public.inventarios_morbidas c join public.areas a on a.id = c.area_id
    left join public.activistas ac on ac.id = c.activista_id left join public.perfis p on p.id = c.perfil_id
    where not c.removido and (p_de is null or c.data >= p_de) and (p_ate is null or c.data <= p_ate)
      and privado.le_area(a.activista_id, a.comunidade)), '[]'::jsonb);
end $function$;

revoke all on function public.gravar_inventario_morbidas2(uuid, text, timestamptz, int, int, double precision, double precision, int, int, text, text, text, text, int, int, boolean) from public, anon;
revoke all on function public.inventarios_morbidas_campo(text) from public, anon;
grant execute on function public.gravar_inventario_morbidas2(uuid, text, timestamptz, int, int, double precision, double precision, int, int, text, text, text, text, int, int, boolean) to authenticated;
grant execute on function public.inventarios_morbidas_campo(text) to authenticated;
