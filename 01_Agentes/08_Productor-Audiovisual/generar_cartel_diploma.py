#!/usr/bin/env python3
"""
Generador de cartel — plantilla "Diploma de la Academia" (parodia)
Agente: 08 Productor Audiovisual · dirección visual de 01 Director Creativo.

Segunda plantilla visual (además de la clásica negro/rojo de generar_carteles.py):
parodia de diploma/certificado — remite directo a "Informe para una Academia" de
Kafka (la obra en la que se basa El Gorila). Reusa el marco dorado ornamentado que
ya existe en 05_Activos/el-gorila/LONA - Cartel Gorila Teatro/assets/, pero en vez
del retrato pintado por IA (ape.png) usa una FOTO REAL del personaje (cutout de
07_CartelesPeter/personaje-aislado), a pedido de Dirección (13 jul 2026).

Uso:
    python3 generar_cartel_diploma.py                # todas las variantes de RETRATOS
    python3 generar_cartel_diploma.py --solo clasico  # solo esa variante

Salida: 05_Activos/el-gorila/carteles-s2/diploma/{id}.png
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
FOTOS_DIR = REPO / "07_CartelesPeter/public/assets/photos/personaje-aislado"
LONA_DIR = REPO / "05_Activos/el-gorila/LONA - Cartel Gorila Teatro"
LOGO_SOGEM = REPO / "05_Activos/el-gorila/G/SOGEM50A.png"
OUT_DIR = REPO / "05_Activos/el-gorila/carteles-s2/diploma"

CREMA = (242, 237, 228)
CREMA_OSCURO = (223, 214, 196)
NEGRO = (26, 21, 14)
ROJO = (212, 58, 26)
DORADO = (170, 138, 60)
VERDE_OSCURO = (36, 40, 30)  # fondo tipo "óleo" detrás del retrato

FUENTE_DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
FUENTE_BASKERVILLE = "/System/Library/Fonts/Supplemental/Baskerville.ttc"

SIZE = (1800, 1500)  # mismo canvas que el frame ornamentado ya existente

INFO = {
    "kicker": "L A   A C A D E M I A   C E R T I F I C A",
    "titulo": ["EL", "GORILA"],
    "subtitulo": "con Humberto Dupeyrón · 37 años en escena",
    "referencia": "basada en «Informe para una Academia» de Franz Kafka",
    "evento": "ESTRENO 25 DE JULIO",
    "detalle1": "Sábados · 18:00 hrs",
    "detalle2": "Teatro Wilberto Cantón",
    "cta": "Preventa $350 · elgorilateatro.com.mx",
    "firma_izq": "El Rector de la Academia",
    "firma_der": "El Secretario Perpetuo",
}

# Variantes de retrato — cambiar aquí para probar otra foto sin tocar el resto.
RETRATOS = [
    {"id": "clasico", "foto": "1.png"},
    {"id": "alterno", "foto": "24.png"},
]


def cargar_retrato(nombre_archivo: str) -> Image.Image:
    ruta = FOTOS_DIR / nombre_archivo
    foto = Image.open(ruta).convert("RGBA")
    bbox = foto.getbbox()
    if bbox:
        foto = foto.crop(bbox)
    r, g, b, a = foto.split()
    a = a.filter(ImageFilter.GaussianBlur(3))
    foto = Image.merge("RGBA", (r, g, b, a))
    # tono ligeramente pictórico: baja saturación, sube contraste — para que
    # combine con el aire de "retrato al óleo" en vez de foto de prensa
    rgb = foto.convert("RGB")
    rgb = ImageOps.autocontrast(rgb, cutoff=1)
    from PIL import ImageEnhance

    rgb = ImageEnhance.Color(rgb).enhance(0.85)
    rgb.putalpha(a)
    return rgb


def marco_retrato(canvas: Image.Image, box, foto: Image.Image):
    """Pinta el 'cuadro dentro del cuadro': fondo oscuro tipo lienzo + foto +
    doble filete dorado/negro, como el retrato enmarcado del hero de referencia."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0

    lienzo = Image.new("RGB", (w, h), VERDE_OSCURO)
    draw_l = ImageDraw.Draw(lienzo)
    # viñeta simple radial (esquinas más oscuras) para que no se vea plano
    for i in range(0, min(w, h) // 2, 4):
        alpha = int(60 * (i / (min(w, h) / 2)))
        draw_l.rectangle(
            [i, i, w - i, h - i], outline=tuple(max(0, c - alpha // 6) for c in VERDE_OSCURO)
        )

    f = foto.copy()
    f.thumbnail((int(w * 0.94), int(h * 0.94)), Image.LANCZOS)
    fx = (w - f.width) // 2
    fy = h - f.height  # anclado abajo, como un retrato de medio cuerpo
    lienzo.paste(f, (fx, fy), f)

    canvas.paste(lienzo, (x0, y0))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([x0, y0, x1, y1], outline=NEGRO, width=10)
    draw.rectangle([x0 + 12, y0 + 12, x1 - 12, y1 - 12], outline=DORADO, width=3)


def sello_cera(canvas: Image.Image, center, radio=58):
    x, y = center
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(radio, 0, -2):
        t = i / radio
        color = (
            int(140 + (ROJO[0] - 140) * (1 - t)),
            int(20 + (ROJO[1] - 20) * (1 - t) * 0.4),
            int(15 + (ROJO[2] - 15) * (1 - t) * 0.4),
            255,
        )
        draw.ellipse([x - i, y - i, x + i, y + i], fill=color)
    draw.ellipse([x - radio, y - radio, x + radio, y + radio], outline=(90, 15, 10), width=3)
    f = ImageFont.truetype(FUENTE_DIDOT, 34)
    txt = "EG"
    bbox = draw.textbbox((0, 0), txt, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x - tw / 2, y - th / 2 - bbox[1]), txt, font=f, fill=(235, 210, 180, 255))
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB"), (0, 0))


def construir(retrato: dict) -> Image.Image:
    w, h = SIZE
    cartel = Image.new("RGB", SIZE, CREMA)
    draw = ImageDraw.Draw(cartel)

    foto = cargar_retrato(retrato["foto"])
    box = (int(w * 0.075), int(h * 0.16), int(w * 0.44), int(h * 0.80))
    marco_retrato(cartel, box, foto)

    draw = ImageDraw.Draw(cartel)
    tx0 = int(w * 0.50)
    tx1 = int(w * 0.90)
    tcx = (tx0 + tx1) // 2

    def linea(texto, y, font, fill, cx=tcx):
        bbox = draw.textbbox((0, 0), texto, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw / 2, y), texto, font=font, fill=fill)
        return bbox[3] - bbox[1]

    f_kicker = ImageFont.truetype(FUENTE_BASKERVILLE, 26)
    f_titulo = ImageFont.truetype(FUENTE_DIDOT, 148)
    f_sub = ImageFont.truetype(FUENTE_BASKERVILLE, 32)
    f_ref = ImageFont.truetype(FUENTE_BASKERVILLE, 24)
    f_evento = ImageFont.truetype(FUENTE_DIDOT, 52)
    f_detalle = ImageFont.truetype(FUENTE_BASKERVILLE, 34)
    f_cta = ImageFont.truetype(FUENTE_BASKERVILLE, 28)
    f_firma = ImageFont.truetype(FUENTE_BASKERVILLE, 22)

    y = int(h * 0.155)
    linea(INFO["kicker"], y, f_kicker, DORADO)
    y += 46
    draw.line([(tcx - 40, y), (tcx + 40, y)], fill=DORADO, width=1)

    y += 34
    for renglon in INFO["titulo"]:
        y += linea(renglon, y, f_titulo, ROJO)

    y += 20
    y += linea(INFO["subtitulo"], y, f_sub, NEGRO)
    y += 6
    y += linea(INFO["referencia"], y, f_ref, (90, 80, 60))

    y += 40
    draw.line([(tx0 + 20, y), (tx1 - 20, y)], fill=DORADO, width=1)

    y += 40
    y += linea(INFO["evento"], y, f_evento, NEGRO)
    y += 16
    y += linea(INFO["detalle1"], y, f_detalle, (20, 16, 12))
    y += 6
    y += linea(INFO["detalle2"], y, f_detalle, (20, 16, 12))
    y += 18
    y += linea(INFO["cta"], y, f_cta, ROJO)

    # firmas + sello, al pie del bloque de texto
    y_firma = int(h * 0.86)
    draw.line([(tx0 + 10, y_firma), (tx0 + 180, y_firma)], fill=(60, 55, 45), width=2)
    linea(INFO["firma_izq"], y_firma + 10, f_firma, (60, 55, 45), cx=tx0 + 95)
    draw.line([(tx1 - 180, y_firma), (tx1 - 10, y_firma)], fill=(60, 55, 45), width=2)
    linea(INFO["firma_der"], y_firma + 10, f_firma, (60, 55, 45), cx=tx1 - 95)
    sello_cera(cartel, (tcx, y_firma - 4))

    # marco ornamentado (asset ya existente, reusado tal cual)
    frame = Image.open(LONA_DIR / "assets/frame-composited.png").convert("RGBA")
    if frame.size != SIZE:
        frame = frame.resize(SIZE, Image.LANCZOS)
    cartel = cartel.convert("RGBA")
    cartel.alpha_composite(frame)

    # crédito institucional — pequeño, solo si no estorba (pedido de Dirección)
    if LOGO_SOGEM.exists():
        logo = Image.open(LOGO_SOGEM).convert("RGBA")
        logo.thumbnail((160, 90), Image.LANCZOS)
        cartel.alpha_composite(logo, (int(w * 0.50) - logo.width // 2, int(h * 0.895) - logo.height))

    return cartel.convert("RGB")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", help="generar solo esta variante (id de RETRATOS)")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    retratos = RETRATOS
    if args.solo:
        retratos = [r for r in RETRATOS if r["id"] == args.solo]
        if not retratos:
            raise SystemExit(f"No existe la variante '{args.solo}' en RETRATOS")

    for retrato in retratos:
        print(f"Generando diploma-{retrato['id']}...")
        cartel = construir(retrato)
        out = OUT_DIR / f"diploma-{retrato['id']}.png"
        cartel.save(out)
        print(f"  {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
