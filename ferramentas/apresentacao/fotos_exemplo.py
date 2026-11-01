# Ilustrações para usar como «fotografias» no modo apresentação (01/11/2026, pedido do Valdo).
# Desenhadas aqui (sem imagens da internet), 1280x960, cada uma com a legenda «Fotografia de exemplo · apresentação».
import math, random, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1280, 960
OUT = os.path.join(os.path.dirname(__file__), 'out'); os.makedirs(OUT, exist_ok=True)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f = lambda s, b=True: ImageFont.truetype(FB if b else FR, s)
CEU, CEU2, TERRA, TERRA2, VERDE, VERDE2 = (176, 214, 236), (222, 238, 246), (196, 160, 112), (170, 134, 90), (64, 132, 58), (40, 96, 40)

def fundo(d, horizonte=430, ceu=True):
    for y in range(horizonte):
        t = y / horizonte; d.line([(0, y), (W, y)], fill=tuple(int(CEU[i] * (1 - t) + CEU2[i] * t) for i in range(3)))
    d.rectangle([0, horizonte, W, H], fill=TERRA)
    random.seed(horizonte)
    for _ in range(900):
        x, y = random.randint(0, W), random.randint(horizonte, H); r = random.randint(1, 3)
        d.ellipse([x - r, y - r, x + r, y + r], fill=TERRA2)
    # árvores ao longe
    for x in range(-40, W + 80, 140):
        d.ellipse([x, horizonte - 60 + (x % 3) * 8, x + 150, horizonte + 20], fill=(96, 140, 80))

def muda(d, x, y, s=1.0, molhada=False, cor=VERDE, seca=False):
    if molhada: d.ellipse([x - 70 * s, y - 16 * s, x + 70 * s, y + 18 * s], fill=(120, 88, 58))
    c = (150, 120, 60) if seca else cor; c2 = (120, 96, 50) if seca else VERDE2
    d.line([(x, y), (x, y - 70 * s)], fill=(110, 84, 50), width=max(3, int(7 * s)))
    for ang in (-150, -115, -65, -30, -95):
        a = math.radians(ang); ex, ey = x + math.cos(a) * 90 * s, y - 70 * s + math.sin(a) * 60 * s
        mx, my = (x + ex) / 2, (y - 70 * s + ey) / 2 - 20 * s
        d.polygon([(x, y - 70 * s), (mx - 10 * s, my), (ex, ey), (mx + 10 * s, my + 8 * s)], fill=c, outline=c2)

def pessoa(d, x, y, s=1.0, camisa=(30, 90, 160), calca=(50, 50, 60), braco=None):
    pele = (110, 70, 45)
    d.ellipse([x - 18 * s, y - 210 * s, x + 18 * s, y - 172 * s], fill=pele)                    # cabeça
    d.rounded_rectangle([x - 30 * s, y - 170 * s, x + 30 * s, y - 80 * s], radius=int(12 * s), fill=camisa)
    d.rectangle([x - 26 * s, y - 82 * s, x - 4 * s, y], fill=calca); d.rectangle([x + 4 * s, y - 82 * s, x + 26 * s, y], fill=calca)
    if braco == 'frente': d.line([(x + 26 * s, y - 160 * s), (x + 80 * s, y - 120 * s)], fill=camisa, width=int(16 * s))
    elif braco == 'cima': d.line([(x + 26 * s, y - 160 * s), (x + 60 * s, y - 220 * s)], fill=camisa, width=int(16 * s))
    else:
        d.line([(x - 28 * s, y - 160 * s), (x - 40 * s, y - 90 * s)], fill=camisa, width=int(16 * s)); d.line([(x + 28 * s, y - 160 * s), (x + 40 * s, y - 90 * s)], fill=camisa, width=int(16 * s))

def regador(d, x, y, s=1.0):
    d.rounded_rectangle([x, y, x + 90 * s, y + 60 * s], radius=10, fill=(40, 120, 200), outline=(20, 70, 130), width=3)
    d.line([(x + 88 * s, y + 20 * s), (x + 150 * s, y - 10 * s)], fill=(40, 120, 200), width=int(10 * s))
    d.arc([x + 15 * s, y - 35 * s, x + 75 * s, y + 25 * s], 180, 360, fill=(20, 70, 130), width=6)

def gotas(d, x, y, n=14):
    random.seed(x + y)
    for _ in range(n):
        gx, gy = x + random.randint(-25, 40), y + random.randint(0, 110)
        d.ellipse([gx - 4, gy - 7, gx + 4, gy + 7], fill=(70, 150, 230))

def legenda(img, titulo):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([30, 28, 30 + d.textlength(titulo, font=f(40)) + 40, 98], radius=14, fill=(255, 255, 255))
    d.text((50, 38), titulo, font=f(40), fill=(30, 60, 40))
    d.rectangle([0, H - 64, W, H], fill=(30, 74, 48))
    d.text((W / 2, H - 32), 'Fotografia de exemplo · apresentação da app Rega Coco', font=f(28, False), fill=(243, 239, 229), anchor='mm')

def guardar(img, nome, titulo):
    legenda(img, titulo); img.convert('RGB').save(os.path.join(OUT, nome), quality=88); print(nome)

def campo(d, cols, rows, x0=170, y0=520, dx=200, dy=120, molhada=False, s=0.9):
    for r in range(rows):
        for c in range(cols):
            muda(d, x0 + c * dx + (r % 2) * 60, y0 + r * dy, s * (0.8 + r * 0.12), molhada)

# 1 Entrada
img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img); fundo(d); campo(d, 5, 3)
pessoa(d, 1110, 900, 1.5, braco='frente'); d.rectangle([980, 520, 990, 700], fill=(120, 90, 60)); d.rectangle([900, 520, 1070, 590], fill=(250, 245, 230), outline=(120, 90, 60), width=4)
d.text((985, 555), 'PR900101-1', font=f(26), fill=(60, 60, 60), anchor='mm')
guardar(img, '01 Entrada no campo.jpg', 'Entrada no campo')
# 2 Rega
img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img); fundo(d, 380)
muda(d, 560, 820, 2.6, molhada=True); pessoa(d, 860, 900, 2.2, braco='frente'); regador(d, 880 - 220, 560, 1.4); gotas(d, 870 - 210 - 10, 560, 26)
guardar(img, '02 Rega.jpg', 'Rega (evidência)')
# 3 Saída
img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img); fundo(d); campo(d, 5, 3, molhada=True)
pessoa(d, 120, 900, 1.4); regador(d, 160, 800, 0.9)
guardar(img, '03 Saida do campo.jpg', 'Saída do campo (plantas regadas)')
# 4 Queimada
img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img); fundo(d)
d.polygon([(0, 560), (W, 500), (W, H), (0, H)], fill=(60, 52, 46))
random.seed(4)
for _ in range(600):
    x, y = random.randint(0, W), random.randint(540, H); r = random.randint(2, 6); d.ellipse([x - r, y - r, x + r, y + r], fill=(30, 28, 26))
for i, (x, y) in enumerate([(200, 640), (420, 700), (640, 620), (860, 720), (1060, 650), (320, 840), (760, 860)]):
    muda(d, x, y, 1.0, seca=True)
for x, y in [(1000, 600), (1080, 590), (180, 600)]:
    d.polygon([(x - 30, y), (x, y - 90), (x + 30, y)], fill=(240, 120, 30)); d.polygon([(x - 14, y), (x, y - 50), (x + 14, y)], fill=(255, 210, 70))
smoke = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(smoke)
for i in range(9): sd.ellipse([900 + i * 25, 420 - i * 45, 1060 + i * 40, 540 - i * 40], fill=(120, 120, 120, 90))
img = Image.alpha_composite(img.convert('RGBA'), smoke.filter(ImageFilter.GaussianBlur(14)))
guardar(img, '04 Queimada.jpg', 'Queimada')
# 5 Pluviómetro
img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img); fundo(d, 500)
d.rectangle([610, 470, 650, 900], fill=(130, 100, 70))
d.rounded_rectangle([540, 170, 720, 520], radius=20, fill=(225, 240, 250), outline=(80, 100, 120), width=5)
d.rectangle([548, 400, 712, 512], fill=(110, 170, 230))
for i in range(9):
    yy = 500 - i * 36; d.line([(560, yy), (600 if i % 2 else 620, yy)], fill=(40, 60, 80), width=3); d.text((630, yy), f'{i * 5}', font=f(22, False), fill=(40, 60, 80), anchor='lm')
d.polygon([(520, 170), (740, 170), (690, 120), (570, 120)], fill=(200, 220, 235), outline=(80, 100, 120))
guardar(img, '05 Pluviometro.jpg', 'Leitura do pluviómetro')
# 6 Monitoria
img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img); fundo(d, 300)
muda(d, 420, 800, 2.4, molhada=True)
d.rounded_rectangle([760, 380, 1140, 860], radius=16, fill=(240, 235, 220), outline=(110, 90, 60), width=5)
d.rectangle([900, 360, 1000, 400], fill=(110, 90, 60))
for i, t in enumerate(['Planta 1  húmido ✓', 'Planta 2  húmido ✓', 'Planta 3  seco ✗', 'Planta 4  húmido ✓', 'Planta 5  húmido ✓']):
    d.text((790, 430 + i * 80), t, font=f(30, False), fill=(40, 40, 40))
guardar(img, '06 Monitoria.jpg', 'Monitoria: solo húmido')
# 7 Recontagem no campo (produtor e oficial)
img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img); fundo(d); campo(d, 5, 2, y0=560)
pessoa(d, 480, 920, 1.9, camisa=(180, 90, 40)); pessoa(d, 780, 920, 1.9, camisa=(30, 110, 70), braco='frente')
d.rounded_rectangle([850, 600, 940, 700], radius=6, fill=(250, 250, 245), outline=(80, 80, 80), width=3)
d.text((480, 500), 'Produtor', font=f(30), fill=(255, 255, 255), anchor='mm', stroke_width=3, stroke_fill=(40, 40, 40))
d.text((780, 500), 'Oficial de M&E', font=f(30), fill=(255, 255, 255), anchor='mm', stroke_width=3, stroke_fill=(40, 40, 40))
guardar(img, '07 Recontagem no campo.jpg', 'Recontagem: produtor e oficial no campo')
# 8 Declaração
img = Image.new('RGB', (W, H), (205, 190, 160)); d = ImageDraw.Draw(img)
d.polygon([(330, 110), (960, 140), (930, 900), (300, 870)], fill=(252, 251, 246), outline=(160, 150, 130))
d.text((420, 190), 'DECLARAÇÃO DE CONTAGEM', font=f(34), fill=(30, 30, 30))
for i, t in enumerate(['Produtor: ____________________', 'Campo: PR900101-1', 'Plantas vivas: ______', 'Plantas mortas: ______', 'Data: ___/___/______']):
    d.text((400, 300 + i * 70), t, font=f(28, False), fill=(50, 50, 50))
d.line([(400, 760), (620, 760)], fill=(60, 60, 60), width=2); d.line([(680, 770), (880, 770)], fill=(60, 60, 60), width=2)
d.text((400, 775), 'Produtor', font=f(22, False), fill=(80, 80, 80)); d.text((680, 785), 'Oficial de M&E', font=f(22, False), fill=(80, 80, 80))
d.line([(420, 745), (470, 720), (500, 750), (560, 715), (600, 740)], fill=(30, 50, 140), width=4)
d.line([(700, 755), (740, 725), (780, 760), (830, 730), (870, 750)], fill=(30, 50, 140), width=4)
guardar(img, '08 Declaracao de contagem.jpg', 'Declaração de contagem assinada')
# 9 Manutenção
img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img); fundo(d, 320)
d.ellipse([300, 690, 980, 900], fill=(140, 104, 66))                     # cava-roda
random.seed(9)
for _ in range(260):                                                     # mulching (palha)
    a = random.uniform(0, 2 * math.pi); r = random.uniform(80, 300); x, y = 640 + math.cos(a) * r, 795 + math.sin(a) * r * 0.3
    b = random.uniform(0, math.pi); d.line([(x, y), (x + math.cos(b) * 26, y + math.sin(b) * 8)], fill=(214, 190, 120), width=3)
muda(d, 640, 800, 2.4)
guardar(img, '09 Manutencao.jpg', 'Manutenção: cava-roda e mulching')
# 10 Dia sem rega (tuk-tuk avariado)
img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img); fundo(d, 420)
d.rounded_rectangle([340, 520, 760, 760], radius=30, fill=(230, 180, 40), outline=(120, 90, 20), width=5)
d.rectangle([560, 440, 880, 760], fill=(60, 140, 200)); d.text((720, 600), 'ÁGUA', font=f(44), fill=(255, 255, 255), anchor='mm')
d.ellipse([370, 720, 470, 820], fill=(40, 40, 40)); d.ellipse([700, 720, 800, 820], fill=(40, 40, 40)); d.ellipse([790, 750, 890, 800], fill=(40, 40, 40))
d.polygon([(980, 560), (1080, 740), (880, 740)], fill=(240, 200, 30), outline=(60, 40, 0)); d.text((980, 690), '!', font=f(80), fill=(40, 30, 0), anchor='mm')
guardar(img, '10 Dia sem rega.jpg', 'Dia sem rega: tuk-tuk avariado')
# 11 Acompanhamento (equipa a regar)
img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img); fundo(d); campo(d, 5, 2, y0=600, molhada=True)
for i, (x, c) in enumerate([(300, (180, 60, 60)), (620, (40, 120, 160)), (940, (120, 80, 160))]):
    pessoa(d, x, 920, 1.5, camisa=c, braco='frente'); regador(d, x + 40, 690, 0.8)
guardar(img, '11 Acompanhamento.jpg', 'Acompanhamento: equipa a regar')
