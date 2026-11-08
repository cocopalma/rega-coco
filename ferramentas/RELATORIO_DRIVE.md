<!-- Instruções da tarefa agendada «Rega Coco — relatório do dia na pasta partilhada (19:00)». Aprovado pelo Valdo a 08/11/2026. Fonte única: a tarefa lê este ficheiro. -->

Relatório do dia na pasta partilhada com o Dalmar — Rega Coco

FINALIDADE
Valdo, 08/11/2026: "criamos uma pasta que partilho com ele os relatórios diários da rega, que vem do aplicativo… às 19h produzes um relatório em HTML e em PDF e colocas sempre dentro dessa pasta. Os relatórios do dia anterior passam para old… a pasta sempre que o ficheiro que vai estar vivo é o ficheiro do dia… ele consegue acessar nessa pasta e consegue puxar a informação para o painel dele… rega, mas também… manutenção… em Quiwia e Farol."
O Dalmar compara estes números (só da app) com os do WhatsApp no painel da operação dele. Este relatório não compara com o WhatsApp nem cobra incumprimentos (isso é o relatório das 22:30, ferramentas/RELATORIO_DIARIO.md, que continua).

PASTA NO GOOGLE DRIVE (conta do Valdo; partilhada com dalmar.jose.santos@gmail.com, leitor)
- «Rega Coco — relatório diário», id 1PPswhJRYONzeqiex1gpXtC3R9qTl4Ewl, dentro de «Projecto de plantio de coco › Rega de emergencia _2026» (movida para aí a 08/11/2026, pedido do Valdo; o id não mudou).
- Subpasta «_old», id 1sbce7U9CAAWCuDbyjlIWa-Fd1WBrWp12.
- Na pasta principal fica SÓ o relatório do dia: Rega_Coco_relatorio_AAAAMMDD.html e Rega_Coco_relatorio_AAAAMMDD.pdf.

PASSOS (de segunda a sábado, às 19:00 de Maputo)
1. Data do relatório = hoje em Maputo (Africa/Maputo, UTC+2), AAAA-MM-DD.
2. Clonar o repositório GitHub cocopalma/rega-coco (só leitura; não alterar o repositório).
3. Ler ferramentas/relatorio_dia.sql, substituir __DIA__ pela data e correr com o conector Supabase (execute_sql, projecto fgzdqnvobgfzjetbbxcm). Só leitura: não gravar, actualizar nem apagar nada no servidor. Gravar o valor da coluna «dados» (JSON) num ficheiro dados.json.
4. Correr «python3 ferramentas/relatorio_dia.py dados.json Rega_Coco_relatorio_AAAAMMDD» (precisa de playwright para Python; o Chromium já está instalado). Sai o .html e o .pdf.
5. Verificar antes de enviar: abrir o PDF (pdftoppm) e ver que nada está cortado; conferir que o nº de equipas, regas e plantas no HTML batem com o JSON (o script recusa se não baterem); sem telefones, senhas ou PINs.
6. Na pasta principal (search_files com parentId = '1PPswhJRYONzeqiex1gpXtC3R9qTl4Ewl', ler todas as páginas), passar para «_old» todos os ficheiros que não sejam o relatório de hoje (update_file com parentId = '1sbce7U9CAAWCuDbyjlIWa-Fd1WBrWp12'). Não apagar nada. Se já houver na pasta principal ficheiros com o nome do relatório de hoje (a tarefa correu outra vez no mesmo dia), passá-los também para «_old» antes de pôr os novos.
7. Enviar os dois ficheiros com create_file, parentId = '1PPswhJRYONzeqiex1gpXtC3R9qTl4Ewl', disableConversionToGoogleType = true, e o conteúdo por referência ao ficheiro: base64Content = «sha256:<sha256 do ficheiro>:<caminho absoluto>» (calcular com sha256sum). HTML: contentMimeType text/html; PDF: application/pdf. Confirmar no resultado que fileSize = tamanho do ficheiro local.
8. Confirmar que na pasta principal ficaram só os dois ficheiros de hoje.
9. Se algum passo falhar (consulta, script, envio), não deixar a pasta vazia: os ficheiros do dia anterior só passam para «_old» depois de os de hoje estarem prontos (passos 3 a 5 antes do 6). Escrever no fim do trabalho o que falhou.

O QUE O RELATÓRIO TEM (gerado pelo script; não escrever o HTML à mão)
Rega: equipas que regaram / total, campos e plantas regadas hoje, pessoas, plantas regadas na app desde 24/10, progresso da ronda, campos que nunca receberam água; plantas por equipa com a hora do 1.º campo; equipas sem rega agrupadas pelo motivo registado (e «Sem motivo registado»); o que dificultou a rega (registado na saída); plantas por comunidade; progresso da ronda por equipa. Manutenção (Quiwia e Farol): trabalho de hoje, % de plantas com cava-roda e com mulching, situação dos campos por comunidade. Tabela de todas as equipas. Os mesmos dados vão em JSON dentro do HTML (<script type="application/json" id="rega-coco-dados">) para o painel do Dalmar os ler.
