-- v252 (21/11/2026, Valdo: "Sim"): campos com inventário de plantas mórbidas na lista (filtro), no mapa (🩺) e na tabela do painel.
-- Uma linha por campo com inventário: nº de inventários e o último (data, amostra, mórbidas). Mesmos papéis do painel.
create or replace function public.morbidas_por_campo()
 returns table(area_id text, n int, ultima date, amostra int, morbidas int)
 language sql stable security definer set search_path to '' as $function$
  select distinct on (c.area_id) c.area_id, (count(*) over (partition by c.area_id))::int, c.data, c.amostra, c.morbidas
  from public.inventarios_morbidas c join public.areas a on a.id = c.area_id
  where not c.removido and privado.meu_papel() in ('gestor','director','me','tecnico','supervisor','cliente')
    and privado.le_area(a.activista_id, a.comunidade)
  order by c.area_id, c.feito_em desc
$function$;
revoke all on function public.morbidas_por_campo() from public, anon;
grant execute on function public.morbidas_por_campo() to authenticated;
