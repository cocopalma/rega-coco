# Vídeo das novidades da v239 (sem voz): render.py activista|tecnico saida.mp4
import sys, os, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont
Q, OUT = sys.argv[1], sys.argv[2]
D = os.path.dirname(os.path.abspath(__file__)); CAP = D + "/cap/"; TMP = D + "/tmp_" + Q; os.makedirs(TMP, exist_ok=True)
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
f = lambda n, b=False: ImageFont.truetype(F + ("-Bold" if b else "") + ".ttf", n)
CREME, VERDE, TINTA, CINZA, LARANJA = (250, 246, 236), (22, 84, 48), (30, 34, 30), (95, 100, 95), (200, 90, 20)
RODAPE = "Projeto de Desenvolvimento da Cadeia de Valor do Coco · Palma"
QUEM = {"activista": "Para o activista", "tecnico": "Para o técnico e o supervisor"}[Q]
ACT = [
 ("capa", "Novidades da versão 239", [QUEM], None),
 ("Antes de começar", "Actualize a app", ["Abra a app com rede.", "Feche a app e volte a abrir.", "Em Definições (a engrenagem), no fim, deve dizer «Versão da app: v239»."], None),
 ("Cava-roda e mulching", "Quando não há rega", ["Não há rega agora? A equipa faz cava-roda e mulching nos campos.", "Conta como dia de trabalho.", "Na ficha do campo, toque em «Cava-roda e mulching (sem rega)»."], "a1_ficha"),
 ("Cava-roda e mulching", "Diga porque não há rega", ["O motivo é obrigatório.", "Em «Falta de material» e «Outro motivo», escreva a observação.", "Depois toque em «Continuar»."], "a2_motivo_ok"),
 ("Cava-roda e mulching", "Quem veio hoje", ["Se ainda não começou o dia, a app pergunta quem veio.", "Marque as pessoas da equipa que estão presentes."], "a3_inicio"),
 ("Cava-roda e mulching", "Fotografia do início", ["Tem de estar no campo: a app verifica o GPS.", "Tire a fotografia da equipa no campo, ao começar."], "a4_foto_entrada"),
 ("Cava-roda e mulching", "Durante o trabalho", ["Tire a fotografia durante o trabalho.", "Quando acabar, toque em «Terminei — marcar o fim»."], "a5_curso2"),
 ("Cava-roda e mulching", "No fim, conte as plantas", ["Plantas com cava-roda feitas hoje.", "Plantas com mulching feitas hoje.", "Pessoas que trabalharam e a fotografia do fim.", "A app diz quantas plantas faltam no campo."], "a6_fim"),
 ("Cava-roda e mulching", "Fica na ficha do campo", ["A ficha mostra o que já foi feito e o que falta.", "Funciona sem rede: é enviado quando houver rede."], "a7_ficha_depois"),
 ("Fim do trabalho às 15:30", "Depois das 15:30 não se começa", ["Nem rega, nem cava-roda e mulching.", "O que já está em curso termina e conta.", "Para começar depois das 15:30 são precisas horas extras."], "a9_depois_1530"),
 ("Fim do trabalho às 15:30", "Horas extras", ["Peça ao técnico ou ao supervisor.", "Ele activa as horas extras da sua equipa para esse dia.", "Com rede, os botões voltam a aparecer no seu telefone."], "a10_com_he"),
 ("Mapa", "Etiquetas só ao toque", ["Primeiro toque no campo: mostra o nome e as plantas.", "Segundo toque: abre a ficha.", "«Esconder etiquetas» fecha todas."], "a8_etiqueta"),
 ("Regras de ouro", "Para não esquecer", ["Registe sempre no campo, com as três fotografias.", "Conte as plantas: não escreva de cabeça.", "Comece o último campo antes das 15:30.", "Problema na app? Toque na lâmpada no topo."], None),
]
TEC = [
 ("capa", "Novidades da versão 239", [QUEM], None),
 ("Antes de começar", "Actualize a app", ["Abra a app com rede.", "Feche a app e volte a abrir.", "Em Definições (a engrenagem), no fim, deve dizer «Versão da app: v239».", "Peça o mesmo aos seus activistas."], None),
 ("O meu dia", "A equipa em cava-roda aparece", ["Quando não há rega, a equipa regista cava-roda e mulching.", "No «O meu dia» vê as plantas feitas e em quantos campos.", "Conta como equipa a trabalhar: não pede motivo de dia sem rega."], "t1_meudia"),
 ("Fim do trabalho às 15:30", "Depois das 15:30 não se começa", ["Nem rega, nem cava-roda e mulching.", "O que já está em curso termina e conta.", "Até às 15:30, a equipa sem rega aparece «pode começar até às 15:30».", "«Fechar o dia» continua até às 18:00."], "t1_meudia"),
 ("Horas extras", "É você que activa", ["«O meu dia» › equipa › «Activar horas extras hoje».", "Vale só para essa equipa e só para esse dia.", "Activam o técnico e o supervisor da equipa (e o gestor)."], "t3_he_btn"),
 ("Horas extras", "Fica registado", ["A app guarda quem activou e a que horas.", "O activista vê os botões de novo quando o telefone tiver rede."], "t4_he_ok"),
 ("Registar pela equipa", "Cava-roda e mulching pela equipa", ["Na ficha do campo, toque em «Cava-roda e mulching (sem rega)».", "Diga porque regista pela equipa (obrigatório).", "Depois é igual ao activista: início, fotografias, fim e plantas."], "t2_pela_equipa"),
 ("Ficha do campo", "O que foi feito e o que falta", ["A ficha soma todos os dias: plantas com cava-roda e com mulching.", "Mostra quantas faltam no campo."], "a7_ficha_depois"),
 ("Quiwia e Farol", "Manutenção", ["Já não há chefes de manutenção.", "A cava-roda e o mulching das equipas de rega somam aos totais da manutenção.", "O modo Manutenção continua com o técnico e o supervisor."], None),
 ("Mapa", "Etiquetas só ao toque", ["Primeiro toque no campo: mostra o nome e as plantas.", "Segundo toque: abre a ficha.", "«Esconder etiquetas» fecha todas."], "a8_etiqueta"),
 ("Regras de ouro", "Para não esquecer", ["Depois das 15:30, só com horas extras activadas por si.", "Acompanhe as equipas em cava-roda no «O meu dia».", "Feche o dia até às 18:00.", "Problema na app? Toque na lâmpada no topo."], None),
]
CENAS = ACT if Q == "activista" else TEC
def quebra(d, t, fo, larg):
    out, lin = [], ""
    for p in t.split():
        x = (lin + " " + p).strip()
        if d.textlength(x, font=fo) <= larg: lin = x
        else: out.append(lin); lin = p
    out.append(lin); return out
def slide(i, tag, tit, pts, cap):
    im = Image.new("RGB", (1920, 1080), CREME); d = ImageDraw.Draw(im)
    d.rectangle([0, 1020, 1920, 1080], fill=VERDE); d.text((60, 1036), RODAPE, font=f(24), fill=(235, 240, 230))
    d.text((1860, 1036), f"Rega Coco · v239 · {i + 1}/{len(CENAS)}", font=f(24), fill=(235, 240, 230), anchor="ra")
    if tag == "capa":
        d.text((960, 330), "Rega Coco", font=f(120, True), fill=VERDE, anchor="mm")
        d.text((960, 480), tit, font=f(64, True), fill=TINTA, anchor="mm")
        d.rounded_rectangle([960 - 420, 580, 960 + 420, 670], 45, fill=LARANJA); d.text((960, 625), pts[0], font=f(44, True), fill="white", anchor="mm")
        d.text((960, 770), "Cava-roda e mulching sem rega · fim do trabalho às 15:30 · horas extras · etiquetas do mapa", font=f(30), fill=CINZA, anchor="mm")
        return im
    larg = 1120 if cap else 1700
    tw = d.textlength(tag.upper(), font=f(28, True)); d.rounded_rectangle([90, 90, 90 + tw + 48, 146], 28, fill=LARANJA); d.text((114, 100), tag.upper(), font=f(28, True), fill="white")
    y = 190
    for l in quebra(d, tit, f(68, True), larg): d.text((90, y), l, font=f(68, True), fill=VERDE); y += 86
    y += 40
    for n, p in enumerate(pts):
        d.ellipse([90, y + 4, 142, y + 56], fill=VERDE); d.text((116, y + 30), str(n + 1), font=f(30, True), fill="white", anchor="mm")
        for l in quebra(d, p, f(42), larg - 90): d.text((170, y), l, font=f(42), fill=TINTA); y += 58
        y += 34
    if cap:
        ph = Image.open(CAP + cap + ".png").convert("RGB"); h = 900; w = round(ph.width * h / ph.height); ph = ph.resize((w, h), Image.LANCZOS)
        x0 = 1920 - 110 - w; y0 = 60
        d.rounded_rectangle([x0 - 18, y0 - 18, x0 + w + 18, y0 + h + 18], 44, fill=(25, 25, 25))
        m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w, h], 28, fill=255); im.paste(ph, (x0, y0), m)
    return im
if len(sys.argv) > 3:   # só as imagens, para rever
    for i in map(int, sys.argv[3].split(",")): slide(i, *CENAS[i]).save(f"{TMP}/rev_{i}.jpg", quality=88)
    sys.exit()
lst = []
for i, c in enumerate(CENAS):
    png = f"{TMP}/s{i}.png"; slide(i, *c).save(png)
    dur = 5 if c[0] == "capa" else 5.5 + 2.2 * len(c[2]); mp4 = f"{TMP}/s{i}.mp4"; t = f"{TMP}/s{i}.tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", png, "-vf", f"format=yuv420p,loop=-1:1,trim=duration={dur},fade=in:0:9,fade=out:st={dur - 0.3}:d=0.3", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", "30", t], check=True)
    os.rename(t, mp4); lst.append(f"file '{mp4}'")
open(TMP + "/l.txt", "w").write("\n".join(lst))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", TMP + "/l.txt", "-c", "copy", "-movflags", "+faststart", OUT], check=True); print("feito", OUT)
