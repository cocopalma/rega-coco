-- v258 (23/11/2026, Valdo: "É uma função bastante útil"): o gestor principal manda uma mensagem a uma pessoa;
-- a pessoa vê-a ao abrir a app e no Hoje até tocar em «OK», e pode responder (Valdo, 23/11: "Consegues fazer com que a pessoa
-- possa também responder?"). A resposta vai a quem mandou a mensagem; pode-se responder a uma resposta. Só acrescenta.
create table if not exists public.mensagens (
  id uuid primary key default gen_random_uuid(),
  para_perfil_id uuid not null references public.perfis(id),
  de_perfil_id uuid not null references public.perfis(id),
  texto text not null check (length(btrim(texto)) between 3 and 2000),
  criada_em timestamptz not null default now(),
  vista_em timestamptz,
  removida boolean not null default false,
  removida_em timestamptz,
  resposta_a uuid references public.mensagens(id)
);
create index if not exists mensagens_para on public.mensagens (para_perfil_id, criada_em desc);
alter table public.mensagens enable row level security;   -- sem políticas: só pelas funções
revoke all on public.mensagens from anon, authenticated;

create or replace function privado.envia_mensagens() returns boolean
language sql stable security definer set search_path to '' as $$
  select coalesce((select p.papel = 'gestor' and p.gere_acessos is true and p.so_teste is not true
                   from public.perfis p where p.id = auth.uid()), false)
$$;

-- lista das pessoas a quem se pode mandar (só quem envia)
create or replace function public.destinatarios_mensagem() returns json
language sql stable security definer set search_path to '' as $$
  select case when privado.envia_mensagens() then coalesce((
    select json_agg(json_build_object('id', p.id, 'nome', p.nome, 'papel', p.papel) order by p.nome)
    from public.perfis p where p.id <> auth.uid()), '[]') else null end
$$;

create or replace function public.enviar_mensagem(p_id uuid, p_para uuid, p_texto text) returns json
language plpgsql security definer set search_path to '' as $$
declare v public.mensagens;
begin
  if not privado.envia_mensagens() then raise exception 'Só o gestor principal manda mensagens'; end if;
  if p_texto is null or length(btrim(p_texto)) < 3 then raise exception 'Escreva a mensagem'; end if;
  if length(p_texto) > 2000 then raise exception 'Mensagem demasiado longa (máximo 2000 letras)'; end if;
  if p_para = auth.uid() or not exists (select 1 from public.perfis where id = p_para) then raise exception 'Pessoa não encontrada'; end if;
  select * into v from public.mensagens where id = p_id;
  if found then return json_build_object('id', v.id, 'repetido', true); end if;   -- reenvio da fila
  insert into public.mensagens (id, para_perfil_id, de_perfil_id, texto)
  values (coalesce(p_id, gen_random_uuid()), p_para, auth.uid(), btrim(p_texto)) returning * into v;
  return json_build_object('id', v.id, 'repetido', false);
end $$;

-- as minhas: por ver e as vistas nos últimos 30 dias
create or replace function public.minhas_mensagens() returns json
language sql stable security definer set search_path to '' as $$
  select coalesce(json_agg(x order by x.criada_em desc), '[]') from (
    select m.id, m.texto, m.criada_em, m.vista_em, d.nome as de, m.resposta_a, left(o.texto, 160) as resposta_a_texto
    from public.mensagens m join public.perfis d on d.id = m.de_perfil_id
    left join public.mensagens o on o.id = m.resposta_a
    where m.para_perfil_id = auth.uid() and not m.removida
      and (m.vista_em is null or m.vista_em > now() - interval '30 days')
    order by m.criada_em desc limit 30) x
$$;

create or replace function public.mensagem_vista(p_id uuid, p_em timestamptz default null) returns boolean
language sql security definer set search_path to '' as $$
  with u as (update public.mensagens set vista_em = coalesce(least(p_em, now()), now())
             where id = p_id and para_perfil_id = auth.uid() and vista_em is null returning 1)
  select true
$$;

-- enviadas (quem envia): últimos 60 dias, com a hora em que foi vista
create or replace function public.mensagens_enviadas() returns json
language sql stable security definer set search_path to '' as $$
  select case when privado.envia_mensagens() then coalesce((
    select json_agg(x order by x.criada_em desc) from (
      select m.id, m.texto, m.criada_em, m.vista_em, p.nome as para, p.papel, left(o.texto, 160) as resposta_a_texto,
        (select coalesce(json_agg(json_build_object('id', r.id, 'texto', r.texto, 'criada_em', r.criada_em, 'vista_em', r.vista_em) order by r.criada_em), '[]')
           from public.mensagens r where r.resposta_a = m.id and not r.removida) as respostas
      from public.mensagens m join public.perfis p on p.id = m.para_perfil_id
      left join public.mensagens o on o.id = m.resposta_a
      where m.de_perfil_id = auth.uid() and not m.removida and m.criada_em > now() - interval '60 days'
      order by m.criada_em desc limit 100) x), '[]') else null end
$$;

-- responder: quem recebeu uma mensagem responde a quem a mandou (também funciona a partir da fila do telefone)
create or replace function public.responder_mensagem(p_id uuid, p_msg uuid, p_texto text, p_em timestamptz default null) returns json
language plpgsql security definer set search_path to '' as $$
declare o public.mensagens; v public.mensagens;
begin
  select * into v from public.mensagens where id = p_id;
  if found then return json_build_object('id', v.id, 'repetido', true); end if;   -- reenvio da fila
  select * into o from public.mensagens where id = p_msg and para_perfil_id = auth.uid() and not removida;
  if not found then raise exception 'Mensagem não encontrada'; end if;
  if p_texto is null or length(btrim(p_texto)) < 3 then raise exception 'Escreva a resposta'; end if;
  if length(p_texto) > 2000 then raise exception 'Resposta demasiado longa (máximo 2000 letras)'; end if;
  insert into public.mensagens (id, para_perfil_id, de_perfil_id, texto, resposta_a, criada_em)
  values (coalesce(p_id, gen_random_uuid()), o.de_perfil_id, auth.uid(), btrim(p_texto), o.id, coalesce(least(p_em, now()), now())) returning * into v;
  update public.mensagens set vista_em = coalesce(vista_em, v.criada_em) where id = o.id;
  return json_build_object('id', v.id, 'repetido', false);
end $$;

-- apagar uma mensagem enviada por engano (ainda não vista)
create or replace function public.remover_mensagem(p_id uuid) returns boolean
language plpgsql security definer set search_path to '' as $$
begin
  if not privado.envia_mensagens() then raise exception 'Só o gestor principal'; end if;
  update public.mensagens set removida = true, removida_em = now()
   where id = p_id and de_perfil_id = auth.uid() and vista_em is null and not removida;
  if not found then raise exception 'Esta mensagem já foi vista ou não existe'; end if;
  return true;
end $$;

revoke all on function public.destinatarios_mensagem(), public.enviar_mensagem(uuid, uuid, text), public.minhas_mensagens(),
  public.mensagem_vista(uuid, timestamptz), public.mensagens_enviadas(), public.remover_mensagem(uuid), public.responder_mensagem(uuid, uuid, text, timestamptz), privado.envia_mensagens() from public, anon;
grant execute on function public.destinatarios_mensagem(), public.enviar_mensagem(uuid, uuid, text), public.minhas_mensagens(),
  public.mensagem_vista(uuid, timestamptz), public.mensagens_enviadas(), public.remover_mensagem(uuid), public.responder_mensagem(uuid, uuid, text, timestamptz) to authenticated;
