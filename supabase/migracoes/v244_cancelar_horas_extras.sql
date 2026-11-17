-- v244 (17/11/2026, sugestão do Essumaila pelo 💡: activou horas extras por engano e a app não deixava cancelar)
-- Cancelar as horas extras de hoje: técnico/supervisor da equipa ou gestor. Recusa se a equipa já começou
-- uma rega real ou cava-roda e mulching depois da hora limite (essas contam com as horas extras).
alter table public.horas_extras add column if not exists removido_por uuid, add column if not exists removido_em timestamptz;

create or replace function public.cancelar_horas_extras(p_id uuid)
returns json language plpgsql security definer set search_path to '' as $$
declare r record; v_hoje date := (now() at time zone 'Africa/Maputo')::date;
  v_lim text := coalesce((select c.valor #>> '{}' from public.config c where c.chave = 'hora_limite_inicio'), '15:30');
begin
  select h.* into r from public.horas_extras h where h.id = p_id;
  if r.id is null then return json_build_object('ok', true, 'nao_ha', true); end if;
  if r.removido then return json_build_object('ok', true, 'ja', true); end if;
  if privado.so_teste() or not (privado.meu_papel() = 'gestor' or (privado.meu_papel() in ('tecnico', 'supervisor') and privado.equipa_minha(r.activista_id))) then raise exception 'sem acesso'; end if;
  if r.data <> v_hoje then raise exception 'Só se cancelam as horas extras de hoje'; end if;
  if exists (select 1 from public.registos_rega g where g.activista_id = r.activista_id and not g.teste
               and (g.entrada_em at time zone 'Africa/Maputo')::date = r.data and to_char(g.entrada_em at time zone 'Africa/Maputo', 'HH24:MI') > v_lim)
     or exists (select 1 from public.actividades_campo ac where ac.activista_id = r.activista_id
               and (ac.entrada_em at time zone 'Africa/Maputo')::date = r.data and to_char(ac.entrada_em at time zone 'Africa/Maputo', 'HH24:MI') > v_lim) then
    raise exception 'A equipa já começou trabalho depois das %: as horas extras não se podem cancelar', v_lim;
  end if;
  update public.horas_extras set removido = true, removido_por = auth.uid(), removido_em = now() where id = p_id;
  return json_build_object('ok', true);
end $$;
revoke all on function public.cancelar_horas_extras(uuid) from public, anon;
grant execute on function public.cancelar_horas_extras(uuid) to authenticated;
