# Aplicar as sugestões da app — procedimento diário

Pedido do Valdo (31/10/2026): "Temos sugestões por aplicar. Cria uma skill que corre todos os dias para ler as sugestões e aplicar."
Corre todos os dias às 21:37 de Maputo (tarefa agendada "Rega Coco — aplicar as sugestões") e também quando o Valdo pedir.
Responder sempre em português europeu, claro, conciso e directo. Não inventar nada. Nunca escrever telefones, senhas, PIN nem números de documentos.

## 0. Preparar
1. Repositório: `gh repo clone cocopalma/rega-coco /home/claude/rega-coco` (ou `git -C /home/claude/rega-coco pull`). Ler o `CLAUDE.md` todo: tem as regras e as decisões do Valdo. O GitHub é a única versão de referência.
2. Testes: `mkdir -p /home/claude/rega-test && cp /home/claude/rega-coco/testes/* /home/claude/rega-test/ && cd /home/claude/rega-test && npm install`. Os testes usam Playwright (já instalado) e os caminhos `/home/claude/rega-coco` e `/home/claude/rega-test`. Testes novos fazem-se em `/home/claude/rega-test` e copiam-se para `testes/` no repositório.
3. Servidor: Supabase, projecto `fgzdqnvobgfzjetbbxcm` (conector Supabase).

## 1. Ler
```sql
select s.id, s.estado, s.criada_em at time zone 'Africa/Maputo' em, p.nome, s.papel, s.ecra, s.area_id, s.versao, s.texto, s.nota,
       s.foto_path is not null tem_foto, coalesce(array_length(s.fotos_extra,1),0) fotos_extra, s.diag
from sugestoes s left join perfis p on p.id = s.perfil_id
where s.estado in ('nova','aprovada') order by s.criada_em;
```
E os problemas técnicos das últimas 24 h: `select tipo, mensagem, ecra, sum(vezes) vezes, count(distinct perfil_id) pessoas, max(versao) versao from problemas_app where recebido_em >= now() - interval '1 day' group by 1,2,3 order by vezes desc;`
As fotografias estão em buckets privados e não se vêem daqui: dizer "tem fotografia (não vista)" quando a fotografia for precisa para perceber.

## 2. Perceber cada sugestão antes de mexer
Para cada uma: ler o texto, o `diag` (papel, filtros, campo aberto, posição, versão), os dados do servidor desse campo/equipa (regas, dias sem rega, alterações, `problemas_app` da mesma pessoa) e o código. Muitas vêm de uma versão antiga da app ou de um engano de uso. Verificar sempre antes de concluir.

Classificar:
- **A. Erro da app, ou dificuldade de uso que se resolve sem mudar regras** (texto confuso, botão escondido, ecrã que bloqueia, falta de aviso): corrigir.
- **B. Dúvida, engano de uso, ou a app já faz isso**: não mudar a app; responder à pessoa com o que deve fazer.
- **C. Para o Valdo decidir** — não aplicar: muda regras (quem vê o quê, rondas, cumprimento, monitoria, motivos), mexe em dados da rega (retirar ou repor campos, mudar activista, apagar ou alterar registos, criar acessos), contraria uma decisão do Valdo no `CLAUDE.md`, é grande ou tem mais de uma leitura. Vai para o relatório com uma recomendação. Não responder à pessoa ainda.
- **D. Aprovada pelo Valdo** (`estado = 'aprovada'`): aplicar, como A, seguindo o texto e a nota do Valdo. Se a nota já responde e não há nada a mudar, marcar como feita. Se continuar ambígua, perguntar no relatório.
Sugestões repetidas tratam-se juntas, com resposta a cada pessoa.

## 3. Aplicar (A e D)
- Seguir o `CLAUDE.md`: subir `VERSAO` em `sw.js` e todos os `?v=` em `index.html` e `painel.html` (iguais à VERSAO); traduzir cada texto novo em `i18n.js` (inglês) e `i18n-sw.js` (suaíli); RPC nova também em `demo.js`; mudanças no servidor por migração (`apply_migration`), com `security definer`, `search_path ''` e as verificações de papel; nunca apagar dados sem autorização do Valdo.
- Testar: teste novo em `/home/claude/rega-test/teste_vNNN.py` (português, `LING=en` e `LING=sw`) e os testes antigos ligados à mudança. Se um teste falhar e não se resolver, não publicar essa mudança: passa para o relatório.
- Publicar: uma versão por execução (juntar as mudanças), secção nova no `CLAUDE.md` (versão, data, quem sugeriu, o que mudou, teste), copiar os testes novos para `testes/`, commit com as linhas de autoria pedidas, `git push origin main`, e confirmar com `gh api repos/cocopalma/rega-coco/contents/sw.js --jq .content | base64 -d | head -3`.
- Não mexer em coqueiros (congelados pelo Valdo a 27/10/2026).

## 4. Responder a quem enviou (A, B, D)
A resposta aparece à pessoa no Hoje ("Resposta à sua sugestão"). Por SQL:
```sql
update sugestoes set estado = :estado, nota = :mensagem, avaliada_por = '8a1b9364-5b17-464a-b30b-f52136036c2f', avaliada_em = now() where id = :id;
```
- `feita`: a app mudou. Dizer o que mudou e "Abra a app com rede para receber a versão nova."
- `recusada`: a app não vai mudar. Explicar o que fazer na app (passos curtos). Usar para dúvidas e enganos de uso.
- Mensagem em português simples, sem termos técnicos, até 4 frases. Não prometer nada que não esteja feito.
- As sugestões do tipo C ficam como estão (`nova`).

## 5. Relatório ao Valdo
No fim, uma mensagem curta (é a que chega por notificação) e o mesmo texto por email (conector Gmail, `send_message`, para etevaldo.cheveia@jfs.co.mz, assunto "Rega Coco — sugestões aplicadas DD/MM/AAAA (vNNN)"):
1. Aplicadas: versão publicada e, por sugestão, quem pediu e o que mudou.
2. Respondidas sem mudar a app: quem e o que se respondeu.
3. Para o Valdo decidir: uma linha por sugestão (quem, o pedido, a recomendação, o que muda se aprovar). Lembrar: aprova-se em Gestão › 💡 Sugestões e problemas (Aprovada) e a próxima execução aplica.
4. Problemas técnicos que se repetem (erro, quantas vezes, quantas pessoas, versão).
Se não houver sugestões nem problemas, não enviar nada.

## Limites
- Não enviar mensagens a activistas, técnicos ou supervisores (só a resposta dentro da app).
- Não criar acessos, não mudar senhas nem PIN, não mexer na função `gestor-activistas`.
- Não apagar dados. Não correr SQL destrutivo.
- Se o Supabase ou o GitHub não responderem, terminar com o erro no relatório, sem tentar outras vias.
