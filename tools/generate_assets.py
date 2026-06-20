"""
Generiert Pixel-Art Sprites für das Medieval-Dorf-Verteidiger-Spiel.
Ausführen: python generate_assets.py
"""
from PIL import Image, ImageDraw
import os, random

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sprites")
os.makedirs(OUT, exist_ok=True)

RNG = random.Random(7)

def save(img, name):
    path = os.path.join(OUT, name)
    img.save(path)
    return path


# ─────────────────────────────────────────────
# TURM  (64 × 64)
# ─────────────────────────────────────────────
def make_tower():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    S1 = (90,  88,  95)   # stein dunkel
    S2 = (120, 118, 126)  # stein mittel
    S3 = (150, 148, 156)  # stein hell
    MO = (50,  40,  30)   # mörtel
    GT = (25,  18,  12)   # tor dunkel
    WD = (55,  75,  130, 210)  # fenster
    FL = (180, 25,  25)   # fahne rot
    FP = (90,  65,  35)   # fahnenstange
    GR = (55,  42,  28)   # boden
    GL = (75,  60,  40)

    # Turmbasis (Schatten)
    d.ellipse([14, 57, 50, 64], fill=(0, 0, 0, 60))

    # Turm-Körper
    d.rectangle([14, 20, 50, 60], fill=S2)

    # Steinblock-Muster
    for row in range(5):
        y = 20 + row * 8
        offset = 8 if row % 2 else 0
        for col in range(-1, 4):
            x  = offset + col * 16
            x0 = max(14, x)
            x1 = min(50, x + 14)
            if x1 > x0:
                d.rectangle([x0, y, x1, y + 6], fill=S1, outline=MO)

    # Zinnen oben (5 Zinnen)
    for i in range(5):
        x = 14 + i * 8
        if i % 2 == 0:
            d.rectangle([x, 10, x + 6, 22], fill=S1, outline=MO)
        else:
            d.rectangle([x, 16, x + 6, 22], fill=S2)

    # Helles oberes Band
    d.rectangle([14, 19, 50, 22], fill=S3)

    # Tor (Bogen)
    d.rectangle([26, 44, 38, 60], fill=GT)
    d.ellipse  ([26, 38, 38, 50], fill=GT)

    # Fenster links / rechts
    d.rectangle([17, 28, 23, 36], fill=WD)
    d.line     ([20, 28, 20, 36], fill=(80, 100, 180, 180), width=1)
    d.rectangle([41, 28, 47, 36], fill=WD)
    d.line     ([44, 28, 44, 36], fill=(80, 100, 180, 180), width=1)

    # Kleines Fenster Mitte
    d.rectangle([29, 30, 35, 37], fill=WD)

    # Fahnenstange
    d.line([32, 2, 32, 12], fill=FP, width=2)
    # Fahne (Dreieck)
    d.polygon([(32, 2), (44, 6), (32, 11)], fill=FL)
    d.line   ([32, 2, 44, 6], fill=(120, 15, 15), width=1)

    # Bodenbeschattung
    d.rectangle([14, 58, 50, 60], fill=GR)
    d.rectangle([12, 59, 52, 61], fill=GL)

    return img


# ─────────────────────────────────────────────
# ORK KRIEGER  (32 × 32)
# ─────────────────────────────────────────────
def make_orc():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    SK = (45,  95, 28)    # haut (dunkler, kriegsmüder)
    SD = (28,  62, 14)
    AR = (48,  38, 22)
    AD = (28,  20,  8)
    EY = (230,  40,  5)   # blutrot
    TK = (210, 188, 130)
    MT = (88,  88, 102)
    BR = (18,  12,  5)    # augenbrauen
    TE = (210, 200, 185)  # zähne
    BL = (100,  8,   8)   # blut

    d.ellipse([8, 28, 24, 32], fill=(0, 0, 0, 70))

    # Rumpf
    d.ellipse([9, 14, 23, 27], fill=AR)

    # Kopf
    d.ellipse([9, 5, 23, 18], fill=SK)

    # Helm (gezackt)
    d.rectangle([9,  5, 23, 10], fill=AD)
    d.rectangle([8,  8, 24, 11], fill=MT)
    # Helmzacken
    for hx in [9, 13, 17, 21]:
        d.polygon([(hx, 8), (hx+2, 4), (hx+4, 8)], fill=AD)

    # Augen — schmale wütende Schlitze
    d.rectangle([11, 10, 15, 12], fill=EY)
    d.rectangle([17, 10, 21, 12], fill=EY)
    d.rectangle([12, 10, 13, 12], fill=(0, 0, 0))   # pupille links
    d.rectangle([19, 10, 20, 12], fill=(0, 0, 0))   # pupille rechts

    # Wütende Augenbrauen (V-Form: innen tief, außen hoch)
    d.line([11, 8, 15, 10], fill=BR, width=2)   # links: außen hoch → innen tief
    d.line([17, 10, 21, 8], fill=BR, width=2)   # rechts: innen tief → außen hoch

    # Narbe (diagonal über linkes Auge)
    d.line([11, 8, 13, 14], fill=(70, 30, 25), width=1)

    # Hauer — schräg nach außen, bedrohlicher
    d.polygon([(12, 15), ( 9, 20), (12, 20)], fill=TK)  # links: nach außen-unten
    d.polygon([(20, 15), (20, 20), (23, 20)], fill=TK)  # rechts: nach außen-unten

    # Knurrender Mund mit Zähnen
    d.rectangle([12, 14, 20, 17], fill=(15, 8, 4))       # mund dunkel
    for tx in range(12, 20, 2):                            # zähne
        d.rectangle([tx, 14, tx+1, 16], fill=TE)

    # Blut auf Kiefer
    d.rectangle([14, 16, 15, 18], fill=BL)
    d.rectangle([18, 16, 19, 18], fill=BL)

    # Arme
    d.ellipse([ 4, 14, 12, 23], fill=SD)
    d.ellipse([20, 14, 28, 23], fill=SD)

    # Waffe — blutige Keule rechts
    d.rectangle([25,  8, 28, 22], fill=AD)
    d.ellipse  ([22,  4, 30, 12], fill=MT)
    d.ellipse  ([23,  5, 29, 11], fill=(115, 115, 128))
    # Stacheln auf Keule
    d.polygon([(22, 5),(19, 3),(22, 8)], fill=MT)
    d.polygon([(30, 5),(33, 3),(30, 8)], fill=MT)
    # Blutfleck auf Keule
    d.ellipse([24, 6, 28, 9], fill=BL)

    # Beine
    d.rectangle([11, 25, 15, 31], fill=AD)
    d.rectangle([17, 25, 21, 31], fill=AD)

    return img


# ─────────────────────────────────────────────
# ORK BERSERKER  (32 × 32)
# ─────────────────────────────────────────────
def make_orc_berserker():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    SK = (62, 22, 18)     # verbrannte rote haut
    SD = (42, 10, 10)
    AR = (28, 20, 10)
    MT = (82, 82,  94)
    ML = (145,145,158)
    EY = (255, 210,  0)   # leuchtend gelb
    TK = (195, 172, 118)
    PT = (160, 12, 12)    # blut-kriegsbemalung
    BR = (15,  8,   4)
    TE = (200, 192, 175)
    BL = (100,  6,   6)

    d.ellipse([8, 28, 24, 32], fill=(0, 0, 0, 70))

    # Rumpf (breiter, muskulöser)
    d.ellipse([6, 13, 26, 27], fill=AR)
    # Blut-Kriegsbemalung auf Körper
    d.line([10, 15, 14, 22], fill=PT, width=2)
    d.line([18, 22, 22, 15], fill=PT, width=2)

    # Kopf (breiter, bedrohlicher)
    d.ellipse([7, 3, 25, 17], fill=SK)

    # Blutige Kriegsbemalung (diagonale Striche)
    d.line([10, 4,  8, 10], fill=PT, width=2)   # linke Wange
    d.line([22, 4, 24, 10], fill=PT, width=2)   # rechte Wange
    d.line([14, 5, 18,  5], fill=PT, width=2)   # stirn-streifen

    # Augen — schmale wütende Schlitze, leuchtend
    d.rectangle([9,  9, 14, 11], fill=EY)
    d.rectangle([18, 9, 23, 11], fill=EY)
    d.rectangle([10, 9, 11, 11], fill=(0, 0, 0))
    d.rectangle([21, 9, 22, 11], fill=(0, 0, 0))
    # Glüh-Rand
    d.rectangle([8,  8, 15, 12], outline=(200,160,0), width=1)
    d.rectangle([17, 8, 24, 12], outline=(200,160,0), width=1)

    # Wütende dicke Augenbrauen
    d.line([ 9,  7, 14,  9], fill=BR, width=2)
    d.line([18,  9, 23,  7], fill=BR, width=2)

    # Narben (mehrere)
    d.line([12,  6, 10, 12], fill=(55, 22, 18), width=1)
    d.line([21,  7, 23, 11], fill=(55, 22, 18), width=1)

    # Hauer — riesig, nach außen gebogen
    d.polygon([( 9, 15),( 5, 22),( 9, 22)], fill=TK)   # links
    d.polygon([(23, 15),(23, 22),(27, 22)], fill=TK)    # rechts

    # Weit aufgerissener Mund, viele Zähne
    d.rectangle([10, 13, 22, 16], fill=(12, 5, 3))
    for tx in range(10, 22, 2):
        d.rectangle([tx, 13, tx+1, 15], fill=TE)
    # Blut tropft
    d.rectangle([13, 15, 14, 19], fill=BL)
    d.rectangle([19, 15, 20, 18], fill=BL)

    # Arme
    d.ellipse([ 1, 13, 10, 24], fill=SD)
    d.ellipse([22, 13, 31, 24], fill=SD)

    # Doppelaxt (blutig)
    d.rectangle([24,  5, 27, 24], fill=(62, 44, 18))
    d.polygon  ([(19, 3),(29, 5),(29, 13),(19, 15)], fill=MT)
    d.line     ([24, 3, 24, 15], fill=ML, width=1)
    # Blut auf Axt
    d.polygon([(19, 10),(19, 15),(23, 15)], fill=BL)

    # Beine
    d.rectangle([10, 25, 14, 31], fill=AR)
    d.rectangle([18, 25, 22, 31], fill=AR)

    return img


# ─────────────────────────────────────────────
# ORK BOSS  (64 × 64)
# ─────────────────────────────────────────────
def make_orc_boss():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    SK = (48,  105, 30)
    SD = (32,   72, 18)
    AR = (55,   44, 28)
    AD = (38,   28, 14)
    MT = (88,   88, 100)
    ML = (155, 155, 168)
    EY = (255,  45,   5)
    TK = (225, 205, 155)
    CR = (185, 145,   5)
    CL = (220, 185,  30)
    BL = (110,  10,  10)    # blut-akzent

    # Schatten
    d.ellipse([12, 58, 52, 64], fill=(0, 0, 0, 80))

    # Umhang
    d.ellipse([10, 28, 54, 58], fill=(28, 18, 10))

    # Schulterplatten mit Stacheln
    d.ellipse([ 6, 24, 22, 38], fill=MT)
    d.polygon([( 6, 24),( 2, 16),(10, 22)], fill=MT)
    d.polygon([( 6, 28),( 0, 24),(8, 26)],  fill=MT)
    d.ellipse([42, 24, 58, 38], fill=MT)
    d.polygon([(58, 24),(62, 16),(54, 22)],  fill=MT)
    d.polygon([(58, 28),(64, 24),(56, 26)],  fill=MT)

    # Körper (Rüstung)
    d.ellipse([14, 27, 50, 54], fill=AR)
    d.ellipse([18, 29, 46, 48], fill=MT)  # Brustplatte
    d.line   ([32, 29, 32, 48], fill=ML, width=1)
    d.line   ([22, 34, 42, 34], fill=ML, width=1)
    # Nieten
    for nx, ny in [(22,30),(32,30),(42,30),(22,44),(42,44)]:
        d.ellipse([nx-1,ny-1,nx+1,ny+1], fill=ML)

    # Kopf
    d.ellipse([18, 8, 46, 32], fill=SK)

    # Krone (Totenschädel-Motive)
    for cx in [20, 26, 32, 38, 44]:
        d.polygon([(cx, 10),(cx+2, 4),(cx+4, 10)], fill=CR)
    d.rectangle([20, 8, 44, 12], fill=CL)
    # Schädel-Nieten auf Krone
    for sx in [22, 28, 34, 40]:
        d.ellipse([sx, 8, sx+3, 11], fill=(30,20,10))

    # Augen — tiefe feurige Schlitze
    d.rectangle([21, 17, 28, 20], fill=EY)
    d.rectangle([36, 17, 43, 20], fill=EY)
    d.rectangle([23, 17, 25, 20], fill=(0, 0, 0))   # pupille
    d.rectangle([39, 17, 41, 20], fill=(0, 0, 0))
    # Feuer-Glüh-Rand
    d.rectangle([20, 16, 29, 21], outline=(255, 80, 10), width=1)
    d.rectangle([35, 16, 44, 21], outline=(255, 80, 10), width=1)

    # Wütende dicke Augenbrauen
    d.line([20, 14, 28, 17], fill=(15, 8, 4), width=3)   # links: außen→innen tief
    d.line([36, 17, 44, 14], fill=(15, 8, 4), width=3)   # rechts

    # Tiefe Narbe quer über Nase
    d.line([24, 16, 40, 22], fill=(60, 20, 18), width=2)

    # Nase (platt, brutal)
    d.ellipse([28, 21, 36, 26], fill=SD)
    d.ellipse([29, 22, 32, 25], fill=(20,10,5))   # nasenlöcher
    d.ellipse([33, 22, 36, 25], fill=(20,10,5))

    # Weit aufgerissener Mund mit Reißzähnen
    d.rectangle([22, 26, 42, 31], fill=(12, 5, 3))   # mund
    for tx in range(22, 42, 4):                        # obere zähne
        d.polygon([(tx,26),(tx+2,26),(tx+2,30)], fill=TK)
    for tx in range(24, 42, 4):                        # untere zähne
        d.polygon([(tx,31),(tx+2,31),(tx+1,27)], fill=TK)
    # Blut im Mund
    d.rectangle([28, 28, 36, 31], fill=BL)

    # Hauer — riesig, nach oben gebogen (wie Wildschwein)
    d.polygon([(22, 28),(16, 36),(22, 34)], fill=TK)   # links: oben-außen
    d.polygon([(42, 28),(42, 34),(48, 36)], fill=TK)   # rechts

    # Arme
    d.ellipse([ 4, 28, 16, 44], fill=SD)
    d.ellipse([48, 28, 60, 44], fill=SD)

    # Riesiges Schwert (rechts)
    d.rectangle([52, 6, 56, 46], fill=(72, 54, 26))   # griff
    d.rectangle([54, 24, 57, 28], fill=MT)              # parierstange
    d.polygon  ([(48, 4),(60, 8),(60, 40),(48, 44)],  fill=MT)   # klinge
    d.line     ([54, 4, 54, 44], fill=ML, width=1)     # glanz
    d.polygon  ([(48, 4),(50, 4),(50, 8)], fill=BL)    # blut-spitze

    # Beine
    d.rectangle([20, 51, 26, 62], fill=AD)
    d.rectangle([38, 51, 44, 62], fill=AD)
    d.ellipse  ([18, 59, 28, 64], fill=MT)
    d.ellipse  ([36, 59, 46, 64], fill=MT)

    return img



# ─────────────────────────────────────────────────────
# VORSCHAU-SHEET generieren und öffnen
# ─────────────────────────────────────────────────────
SCALE = 4

sprites = [
    (make_tower,          "tower.png",          "Turm"),
    (make_orc,            "orc.png",            "Ork"),
    (make_orc_berserker,  "orc_berserker.png",  "Berserker"),
    (make_orc_boss,       "orc_boss.png",       "Boss"),
]

if __name__ == "__main__":
    generated = []
    for fn, name, label in sprites:
        img  = fn()
        path = save(img, name)
        generated.append((img, label))
        print(f"  {label:12s} -> {path}")

    # Preview-Sheet
    BG     = (22, 18, 30)
    TEXT_C = (200, 180, 140)
    pad    = 20
    total_w = sum(img.width * SCALE + pad for img, _ in generated) + pad
    max_h   = max(img.height * SCALE for img, _ in generated)
    sheet   = Image.new("RGBA", (total_w, max_h + 60), BG + (255,))
    sd      = ImageDraw.Draw(sheet)

    x = pad
    for img, label in generated:
        scaled = img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST)
        y_off  = (max_h - scaled.height) // 2 + 10
        sheet.paste(scaled, (x, y_off), scaled)
        sd.rectangle([x - 2, y_off - 2,
                      x + scaled.width + 2, y_off + scaled.height + 2],
                     outline=(80, 70, 50), width=1)
        # Label unter dem Sprite
        tw = len(label) * 7
        sd.text((x + scaled.width // 2 - tw // 2, max_h + 18),
                label, fill=TEXT_C)
        x += scaled.width + pad

    preview_path = os.path.join(OUT, "preview.png")
    sheet.save(preview_path)
    print(f"\nVorschau: {preview_path}", flush=True)

    import subprocess
    subprocess.Popen(["explorer", preview_path])
