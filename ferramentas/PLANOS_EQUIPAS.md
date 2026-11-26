# Planos das equipas — tarefa das 20:10 (v3, 22/11/2026, decisões do Valdo de 21–22/11)

Regras (o gerador `plano_equipa.py` já as aplica):
- Plantas de cada campo = as que a equipa regou nele na última ronda (sem passar a base); campo nunca regado: a base.
- Dia das 06:30 às 14:00 para todas as equipas. O tempo conta a espera pela água, a rega, a deslocação e as outras esperas,
  aprendidas com os últimos 30 dias da equipa. Nenhum dia passa das 14:00. Campos a mais de 1,5 km uns dos outros só ficam no
  mesmo dia quando não há outra forma.
- O último dia da ronda continua com o dia 1 da ronda seguinte (campos regados há mais tempo, perto de onde a equipa acaba).
- Cada equipa tem dois planos: o resto da ronda actual e a ronda seguinte. Os planos novos vão primeiro ao supervisor
  (estado por_supervisor) e depois ao gestor principal (Valdo).

Pedidos de plano novo feitos na app (v264, 26/11/2026, Valdo: "Gerar o plano de novo"; o gestor principal ou o supervisor pedem em
Planos das equipas › plano › «🔄 Pedir um plano novo», com motivo): tabela `planos_pedidos` (estado `por_fazer`).
- Antes do passo 1: para cada pedido `por_fazer`, gerar de novo o plano do resto da ronda actual dessa equipa (passo 2), mesmo que a
  equipa já tenha plano; gravar o novo (`por_supervisor`), passar os planos dessa equipa e dessa ronda que ainda não estão aprovados a
  `substituido` (um aprovado também passa a `substituido`, porque foi pedido um novo), e marcar o pedido `feito` (`feito_em`, `plano_novo_id`).
  Se não houver dados para gerar, marcar `feito` com `nota` a dizer porquê. Dizer ao Valdo no aviso quem pediu e o motivo.
- Os planos mudados na app (`planos_alteracoes`, `n_alteracoes` > 0) não se substituem sem pedido.

Passos:
1. Correr a consulta 1 de `plano_dados.sql`: equipas a quem falta o plano da ronda actual ou da seguinte.
2. Para cada uma: consulta 2 (trocar :act) → guardar o JSON num ficheiro (o conector pode guardá-lo num ficheiro: extrair o objecto)
   → `python3 -I plano_equipa.py dados.json > planos.json` (lista de 1 ou 2 planos).
3. Gravar só os planos que faltam (não substituir planos já aprovados): para textos grandes, gravar primeiro numa tabela de passagem
   com verificação md5 e depois inserir (`insert into public.planos_equipa (activista_id, ronda, capacidade, pessoas, dias,
   aprendizagem, notas) ...`, pessoas arredondado a inteiro). Nunca inventar campos nem números.
4. Avisar o Valdo: equipas com plano novo, dias, hora de fim de cada dia, dias com campos a mais de 5 km e equipas que acabam a ronda
   em poucos dias (candidatas a apoio entre equipas; a app sugere-o ao supervisor no «O meu dia»).
5. Ao domingo: resumo por equipa do que se aprende (espera pela água no 1.º campo, minutos de rega por planta, outras esperas por dia,
   erro do cálculo nos dias reais).
