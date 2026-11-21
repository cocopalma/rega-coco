-- v255 (21/11/2026, Valdo: "O painel parece que não mostra o cartão de plantas regadas na totalidade e percentagem regada pelo menos 1 vez em relação ao total";
-- "Não podem ser 90%. Esta manhã faltavam apenas 2 campos"): painel_resumo_periodo passa a devolver 'agua' = campos na rega (activos) que já receberam água
-- pela mesma regra da secção «Campos que nunca receberam água» (rega real na app, rega do WhatsApp do próprio campo ou rega antes da app do próprio campo;
-- as regas registadas só por produtor não contam), com as plantas vivas desses campos e a divisão: na app / só no WhatsApp ou antes da app /
-- só regas na app sem plantas vivas para regar / nunca. Só acrescenta uma chave ao corpo que está no servidor; as outras não mudam.
do $m$
declare d text; n text; a text :=
  $x$'vivas_regadas', (select coalesce(sum(a.vivas),0) from por_area p join public.areas a on a.id = p.area_id),$x$;
begin
  d := pg_get_functiondef('public.painel_resumo_periodo(date,date)'::regprocedure);
  if strpos(d, '''agua'', (select jsonb_build_object(''campos''') > 0 then return; end if;
  if strpos(d, a) = 0 then raise exception 'painel_resumo_periodo mudou: não encontrei a linha de vivas_regadas'; end if;
  n := replace(d, a, a || $x$
    'agua', (select jsonb_build_object('campos', count(*) filter (where app or wa or orig), 'vivas', coalesce(sum(vivas) filter (where app or wa or orig), 0),
        'app', count(*) filter (where app), 'so_fora', count(*) filter (where not app and (wa or orig)),
        'sem_vivas', count(*) filter (where not app and not wa and not orig and app_qq), 'nunca', count(*) filter (where not app_qq and not wa and not orig))
      from (select ar.vivas,
          exists (select 1 from public.registos_rega r where r.area_id = ar.id and not r.teste) app_qq,
          exists (select 1 from public.registos_rega r where r.area_id = ar.id and not r.teste and r.plantas_regadas > 0) app,
          (ar.wa_ultima is not null and not coalesce(ar.wa_por_pr, false)) wa,
          (coalesce(cardinality(ar.datas_rega_origem), 0) > 0 and not coalesce(ar.regas_origem_por_pr, false)) orig
        from public.areas ar where ar.activa) ag),$x$);
  execute n;
end $m$;
