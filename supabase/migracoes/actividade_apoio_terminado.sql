-- 18/11/2026: cava-roda e mulching feitos durante um apoio que depois foi terminado (e renovado)
-- eram recusados para sempre ("Este campo não é da lista da equipa"). Passa a valer a mesma regra
-- das regas (privado.marca_fora_lista): o apoio conta se o dia da entrada está entre o início e o dia em que terminou.
do $do$
declare d text;
  v_old text := 'ap.ajuda_activista_id = v_act and ap.terminado_em is null and v_area = any (ap.area_ids))';
  v_new text := 'ap.ajuda_activista_id = v_act and v_area = any (ap.area_ids)
         and (v_ent at time zone ''Africa/Maputo'')::date >= ap.inicio
         and (ap.terminado_em is null or (v_ent at time zone ''Africa/Maputo'')::date <= (ap.terminado_em at time zone ''Africa/Maputo'')::date))';
begin
  d := pg_get_functiondef('public.gravar_actividade(jsonb)'::regprocedure);
  if position(v_old in d) = 0 then raise exception 'gravar_actividade mudou: não aplicado'; end if;
  execute replace(d, v_old, v_new);
end $do$;
