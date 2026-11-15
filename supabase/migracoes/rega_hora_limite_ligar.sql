-- Ligar no servidor a recusa das regas reais começadas depois das 15:30 sem horas extras (v239; decisão do Valdo, 15/11/2026).
-- Só depois de os telefones estarem na v239 (ver a versão em sugestoes_proximo.versao, gravada em cada saída):
--   select a.nome, max(s.versao) from public.sugestoes_proximo s join public.activistas a on a.id = s.activista_id
--    where s.em > now() - interval '2 days' and not s.teste group by 1 order by 2;
-- A função privado.rega_hora_limite() vem de actividades_campo.sql. Aplicar com apply_migration, nome rega_hora_limite_ligar.
drop trigger if exists rega_hora_limite on public.registos_rega;
create trigger rega_hora_limite before insert on public.registos_rega for each row execute function privado.rega_hora_limite();
-- Desligar: drop trigger rega_hora_limite on public.registos_rega;
