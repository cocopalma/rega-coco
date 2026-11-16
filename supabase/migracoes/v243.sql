-- v243 (16/11/2026, Valdo: "Pode executar o ponto 1 e 2"; pedido do Dalmar por email de 16/11: "ter dois campos, responsável
-- (o activista da comunidade) e executor (quem regou, incluindo o reforço). Assim os relatórios ficam iguais e o reforço aparece").
-- Responsável = equipa dona do campo na rega (apoio_para nas regas em apoio; senão a própria equipa); executor = equipa que regou.
-- Só acrescenta: RPC painel_apoios e três chaves novas nas linhas de 'regas' do conector (responsavel, executor, em_apoio).

create or replace function public.painel_apoios(p_de date, p_ate date)
 returns json language plpgsql stable security definer set search_path to '' as $function$
declare v_papel text := privado.meu_papel();
begin
  if v_papel is null or v_papel not in ('gestor', 'director', 'me', 'supervisor', 'tecnico', 'cliente') then return null; end if;
  return json_build_object(
    'regas', (select coalesce(json_agg(json_build_object('data', r.data, 'campo', r.area_id, 'produtor', a.produtor, 'comunidade', a.comunidade,
          'zona', a.zona, 'responsavel', dn.nome, 'executor', ex.nome, 'tecnico_responsavel', dn.tecnico, 'tecnico_executor', ex.tecnico,
          'plantas', r.plantas_regadas, 'pessoas', r.pessoas) order by r.data, ex.nome, r.area_id), '[]'::json)
        from public.registos_rega r
        join public.areas a on a.id = r.area_id
        left join public.activistas ex on ex.id = r.activista_id
        left join public.activistas dn on dn.id = r.apoio_para
       where not r.teste and r.apoio_id is not null and r.apoio_para is not null
         and (p_de is null or r.data >= p_de) and (p_ate is null or r.data <= p_ate)),
    'activos', (select coalesce(json_agg(json_build_object('executor', a1.nome, 'responsavel', a2.nome,
          'campos', coalesce(array_length(ap.area_ids, 1), 0), 'inicio', ap.inicio, 'so_actividade', coalesce(ap.so_actividade, false))
          order by ap.inicio, a1.nome), '[]'::json)
        from public.apoios ap
        join public.activistas a1 on a1.id = ap.ajuda_activista_id
        join public.activistas a2 on a2.id = ap.para_activista_id
       where ap.terminado_em is null));
end $function$;
revoke all on function public.painel_apoios(date, date) from public, anon;
grant execute on function public.painel_apoios(date, date) to authenticated;

-- Conector: as linhas de 'regas' passam a trazer responsavel, executor e em_apoio (api_dados2, a partir da definição do servidor).
do $do$
declare d text; n text; v_old text := $o$jsonb_build_object('tuk_tuk', coalesce(g.tuk_codigo, g.tuk_outro), 'tuk_chegada', g.tuk_chegada))::json order by x.n), '[]'::json)
      into r from json_array_elements(r) with ordinality x(v, n) left join public.registos_rega g on g.id = (x.v->>'id')::uuid;$o$;
  v_new text := $o$jsonb_build_object('tuk_tuk', coalesce(g.tuk_codigo, g.tuk_outro), 'tuk_chegada', g.tuk_chegada,
          'responsavel', coalesce(dn.nome, ex.nome), 'executor', ex.nome, 'em_apoio', (g.apoio_id is not null and g.apoio_para is not null)))::json order by x.n), '[]'::json)
      into r from json_array_elements(r) with ordinality x(v, n) left join public.registos_rega g on g.id = (x.v->>'id')::uuid
      left join public.activistas ex on ex.id = g.activista_id left join public.activistas dn on dn.id = g.apoio_para;$o$;
begin
  select pg_get_functiondef(p.oid) into d from pg_proc p join pg_namespace s on s.oid = p.pronamespace where s.nspname = 'public' and p.proname = 'api_dados2';
  if position('''responsavel''' in d) > 0 then return; end if;
  if position(v_old in d) = 0 then raise exception 'v243: api_dados2 no servidor não é a esperada (regas)'; end if;
  n := replace(d, v_old, v_new);
  execute n;
end $do$;
