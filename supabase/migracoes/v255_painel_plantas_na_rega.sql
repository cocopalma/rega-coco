-- v255 (21/11/2026, Valdo: "O painel parece que não mostra o cartão de plantas regadas na totalidade e percentagem regada pelo menos 1 vez em relação ao total"):
-- painel_resumo_periodo passa a devolver também os campos e as plantas vivas que já receberam pelo menos uma rega contando só os campos que estão hoje na rega
-- (areas_regadas e vivas_regadas contam também campos já retirados, por isso não se podem dividir pelo universo, que só tem os campos na rega).
-- Só acrescenta duas chaves ao corpo que está no servidor; as outras não mudam.
do $m$
declare d text; n text; a text :=
  $x$'vivas_regadas', (select coalesce(sum(a.vivas),0) from por_area p join public.areas a on a.id = p.area_id),$x$;
begin
  d := pg_get_functiondef('public.painel_resumo_periodo(date,date)'::regprocedure);
  if strpos(d, 'vivas_regadas_na_rega') > 0 then return; end if;
  if strpos(d, a) = 0 then raise exception 'painel_resumo_periodo mudou: não encontrei a linha de vivas_regadas'; end if;
  n := replace(d, a, a || $x$
    'areas_regadas_na_rega', (select count(*) from por_area p join public.areas a on a.id = p.area_id where a.activa),
    'vivas_regadas_na_rega', (select coalesce(sum(a.vivas),0) from por_area p join public.areas a on a.id = p.area_id where a.activa),$x$);
  execute n;
end $m$;
