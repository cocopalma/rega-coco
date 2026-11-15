-- v239 (14/11/2026, Valdo): «deixa de haver chefes de manutenção. Em Quiwia e Farol o trabalho fica com o activista, o técnico e o
-- supervisor da equipa» (15/11: o activista regista a cava-roda e o mulching da sua equipa de rega; a manutenção de Quiwia e Farol
-- continua com o técnico e o supervisor). Nenhum acesso de chefe tinha sido criado. As tabelas manutencao_chefes e
-- areas.manut_chefe_id ficam (vazias); o papel deixa de dar acesso à manutenção e já não se atribui chefe a um campo.
create or replace function privado.manut_acesso()
 returns text language sql stable security definer set search_path to '' as $function$
  select case
    when privado.meu_papel() = 'gestor' then 'escreve'
    when privado.meu_papel() = 'supervisor' and exists (select 1 from public.manutencao_comunidades c join public.perfis p on p.nome = c.supervisor where p.id = auth.uid()) then 'escreve'
    when privado.meu_papel() = 'tecnico' and exists (select 1 from public.activistas ac join public.perfis p on p.nome = ac.tecnico
         join public.manutencao_comunidades c on c.comunidade = ac.comunidade_principal where p.id = auth.uid()) then 'regista'
    when privado.meu_papel() in ('director', 'me') then 'le'
    when privado.meu_papel() = 'supervisor' and privado.ve_tudo() then 'le'
    else null end;
$function$;

create or replace function public.atribuir_chefe_manut(p_area text, p_chefe uuid, p_motivo text)
 returns void language plpgsql security definer set search_path to '' as $function$
begin
  raise exception 'Já não há chefes de manutenção';
end $function$;
