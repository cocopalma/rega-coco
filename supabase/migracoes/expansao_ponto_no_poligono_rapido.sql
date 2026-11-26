-- 26/11/2026: áreas de expansão do Luciano (Grandes Áreas, 655 pontos; Mondlane 200 ha). privado.ponto_no_poligono lia o limite
-- jsonb ponto a ponto e com 655 pontos a lista passava os 2 min; esta versão lê o limite uma vez. Só usada em areas_expansao_lista.
create or replace function privado.ponto_no_poligono_arr(x double precision, y double precision, p jsonb) returns boolean language plpgsql immutable set search_path to '' as $f$
declare xs float8[]; ys float8[]; n int; i int; j int; dentro boolean := false;
begin
  select array_agg((v->>0)::float8 order by o), array_agg((v->>1)::float8 order by o) into xs, ys from jsonb_array_elements(p) with ordinality t(v, o);
  n := coalesce(array_length(xs,1),0);
  if n < 3 then return false; end if;
  j := n;
  for i in 1..n loop
    if ((ys[i] > y) <> (ys[j] > y)) and (x < (xs[j] - xs[i]) * (y - ys[i]) / (ys[j] - ys[i]) + xs[i]) then dentro := not dentro; end if;
    j := i;
  end loop;
  return dentro;
end $f$;
-- areas_expansao_lista: caixa calculada uma vez por área (cross join lateral) e privado.ponto_no_poligono_arr; ordem por ano (nulls last) e nome.
