-- v263 (26/11/2026, Valdo: "Preciso de poder alterar o plano dos activistas, em vez de te pedir."):
-- o gestor principal e o supervisor da equipa mudam o plano na app (passar campos entre dias, mudar a ordem, tirar e acrescentar
-- campos) e pedem um plano novo; o plano fica no estado em que estava (aprovado continua aprovado), com histórico.
-- Só acrescenta: planos_lista ganha chaves novas, o resto é novo.

alter table public.planos_equipa add column if not exists alterado_em timestamptz, add column if not exists alterado_por uuid,
  add column if not exists n_alteracoes int not null default 0;

create table if not exists public.planos_alteracoes (
  id uuid primary key default gen_random_uuid(), plano_id uuid not null references public.planos_equipa(id),
  por uuid, papel text, em timestamptz not null default now(), motivo text, estado text, dias_antes jsonb, dias_depois jsonb);
alter table public.planos_alteracoes enable row level security;

create table if not exists public.planos_pedidos (
  id uuid primary key default gen_random_uuid(), activista_id uuid not null references public.activistas(id), plano_id uuid references public.planos_equipa(id),
  motivo text, pedido_por uuid, pedido_em timestamptz not null default now(), estado text not null default 'por_fazer'
    check (estado in ('por_fazer','feito','cancelado')), feito_em timestamptz, plano_novo_id uuid, nota text);
alter table public.planos_pedidos enable row level security;
create unique index if not exists planos_pedidos_um_por_equipa on public.planos_pedidos (activista_id) where estado = 'por_fazer';

drop trigger if exists guarda_so_teste on public.planos_alteracoes;
create trigger guarda_so_teste before insert or delete or update on public.planos_alteracoes for each row execute function privado.guarda_so_teste();
drop trigger if exists guarda_so_teste on public.planos_pedidos;
create trigger guarda_so_teste before insert or delete or update on public.planos_pedidos for each row execute function privado.guarda_so_teste();

-- quem muda: o gestor principal e o supervisor da equipa (sem ve_tudo), como na aprovação; nunca as contas de testes
create or replace function privado.pode_editar_plano(p_act uuid) returns boolean language sql stable security definer set search_path to '' as $$
  select not privado.so_teste() and (
    (privado.meu_papel() = 'gestor' and privado.gere_acessos())
    or (privado.meu_papel() = 'supervisor' and not privado.ve_tudo() and p_act = any(coalesce(privado.ids_visiveis(), '{}'))))
$$;

create or replace function public.editar_plano(p_id uuid, p_dias jsonb, p_motivo text)
returns text language plpgsql security definer set search_path to '' as $$
declare p record; d jsonb; c jsonb; v_ids text[] := '{}'; v_ns int[] := '{}'; v_id text; v_n int; f record; v_antes text[]; v_depois text[];
begin
  select * into p from public.planos_equipa where id = p_id for update;
  if not found then raise exception 'Plano não encontrado'; end if;
  if p.estado not in ('por_supervisor','por_gestor','aprovado') then raise exception 'Este plano já não pode ser mudado'; end if;
  if not privado.pode_editar_plano(p.activista_id) then raise exception 'Só o gestor principal e o supervisor da equipa podem mudar este plano'; end if;
  if coalesce(length(trim(p_motivo)), 0) < 3 then raise exception 'Escreva porque muda o plano'; end if;
  if jsonb_typeof(p_dias) <> 'array' or jsonb_array_length(p_dias) = 0 or jsonb_array_length(p_dias) > 60 then raise exception 'O plano tem de ter pelo menos um dia'; end if;
  for d in select * from jsonb_array_elements(p_dias) loop
    v_n := (d->>'n')::int;
    if v_n is null or v_n < 1 or v_n = any(v_ns) then raise exception 'Dias do plano repetidos'; end if;
    v_ns := v_ns || v_n;
    if jsonb_typeof(d->'campos') <> 'array' or jsonb_array_length(d->'campos') = 0 then raise exception 'O dia % não tem campos', v_n; end if;
    for c in select * from jsonb_array_elements(d->'campos') loop
      v_id := c->>'area_id';
      if v_id is null or v_id = any(v_ids) then raise exception 'Campo repetido no plano: %', coalesce(v_id, '?'); end if;
      if not exists (select 1 from public.areas a where a.id = v_id and a.activa and a.activista_id = p.activista_id) then
        raise exception 'O campo % não está na lista desta equipa', v_id; end if;
      v_ids := v_ids || v_id;
    end loop;
  end loop;
  -- os dias do itinerário já fechados pelo activista ficam como estavam
  for f in select distinct dia_n from public.itinerario_fechos where plano_id = p_id loop
    select array_agg(x->>'area_id' order by x->>'area_id') into v_antes from jsonb_array_elements(p.dias) dd, jsonb_array_elements(dd->'campos') x where (dd->>'n')::int = f.dia_n;
    select array_agg(x->>'area_id' order by x->>'area_id') into v_depois from jsonb_array_elements(p_dias) dd, jsonb_array_elements(dd->'campos') x where (dd->>'n')::int = f.dia_n;
    if v_antes is distinct from v_depois then raise exception 'O dia % já foi fechado pelo activista e não pode mudar', f.dia_n; end if;
  end loop;
  insert into public.planos_alteracoes (plano_id, por, papel, motivo, estado, dias_antes, dias_depois)
    values (p_id, auth.uid(), privado.meu_papel(), left(trim(p_motivo), 500), p.estado, p.dias, p_dias);
  update public.planos_equipa set dias = p_dias, alterado_em = now(), alterado_por = auth.uid(), n_alteracoes = n_alteracoes + 1 where id = p_id;
  return p.estado;
end $$;

create or replace function public.pedir_plano_novo(p_plano uuid, p_motivo text)
returns text language plpgsql security definer set search_path to '' as $$
declare p record; v_id uuid;
begin
  select * into p from public.planos_equipa where id = p_plano;
  if not found then raise exception 'Plano não encontrado'; end if;
  if not privado.pode_editar_plano(p.activista_id) then raise exception 'Só o gestor principal e o supervisor da equipa podem pedir um plano novo'; end if;
  if coalesce(length(trim(p_motivo)), 0) < 3 then raise exception 'Escreva porque pede um plano novo'; end if;
  select id into v_id from public.planos_pedidos where activista_id = p.activista_id and estado = 'por_fazer';
  if found then return 'ja_pedido'; end if;
  insert into public.planos_pedidos (activista_id, plano_id, motivo, pedido_por) values (p.activista_id, p_plano, left(trim(p_motivo), 500), auth.uid());
  return 'pedido';
end $$;

create or replace function public.cancelar_pedido_plano(p_plano uuid)
returns text language plpgsql security definer set search_path to '' as $$
declare p record;
begin
  select * into p from public.planos_equipa where id = p_plano;
  if not found or not privado.pode_editar_plano(p.activista_id) then raise exception 'Sem permissão'; end if;
  update public.planos_pedidos set estado = 'cancelado', feito_em = now() where activista_id = p.activista_id and estado = 'por_fazer';
  return 'cancelado';
end $$;

-- planos_lista: o mesmo de antes + a última mudança, o nº de mudanças, o pedido de plano novo e se a pessoa pode mudar o plano
create or replace function public.planos_lista()
 returns jsonb language plpgsql stable security definer set search_path to '' as $function$
declare v_papel text := privado.meu_papel(); v_meu uuid := privado.meu_activista(); v_vis uuid[] := coalesce(privado.ids_visiveis(), '{}');
begin
  if v_papel is null or v_papel in ('cliente','oficial_me') then return '[]'::jsonb; end if;
  return coalesce((select jsonb_agg(jsonb_build_object('id', p.id, 'activista_id', p.activista_id, 'activista', a.nome, 'supervisor', a.supervisor, 'ronda', p.ronda,
      'estado', p.estado, 'capacidade', p.capacidade, 'pessoas', p.pessoas, 'dias', p.dias, 'aprendizagem', p.aprendizagem, 'notas', p.notas, 'criado_em', p.criado_em,
      'supervisor_nome', ps.nome, 'supervisor_em', p.supervisor_em, 'gestor_nome', pg.nome, 'gestor_em', p.gestor_em,
      'recusado_nome', pr.nome, 'recusado_em', p.recusado_em, 'recusa_motivo', p.recusa_motivo,
      'n_alteracoes', p.n_alteracoes, 'alterado_em', p.alterado_em, 'alterado_nome', pa.nome,
      'alterado_motivo', (select x.motivo from public.planos_alteracoes x where x.plano_id = p.id order by x.em desc limit 1),
      'pedido_novo_em', (select q.pedido_em from public.planos_pedidos q where q.activista_id = p.activista_id and q.estado = 'por_fazer' limit 1),
      'pode_mudar', v_papel <> 'activista' and privado.pode_editar_plano(p.activista_id)) order by p.criado_em desc)
    from public.planos_equipa p join public.activistas a on a.id = p.activista_id
      left join public.perfis ps on ps.id = p.supervisor_por left join public.perfis pg on pg.id = p.gestor_por left join public.perfis pr on pr.id = p.recusado_por
      left join public.perfis pa on pa.id = p.alterado_por
    where p.estado <> 'substituido' and p.criado_em > now() - interval '60 days'
      and case when v_papel = 'activista' then p.activista_id = v_meu and p.estado = 'aprovado'
               when v_papel in ('gestor','director','me') then true
               else p.activista_id = any(v_vis) end), '[]'::jsonb);
end $function$;

revoke all on function public.editar_plano(uuid, jsonb, text), public.pedir_plano_novo(uuid, text), public.cancelar_pedido_plano(uuid) from public, anon;
grant execute on function public.editar_plano(uuid, jsonb, text), public.pedir_plano_novo(uuid, text), public.cancelar_pedido_plano(uuid) to authenticated;
revoke all on function privado.pode_editar_plano(uuid) from public, anon;
