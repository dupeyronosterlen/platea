#!/usr/bin/env python3
"""
Cartel genérico — canal institucional con 2x1 (ITAM, UNAM, etc.)
Agente: 08 Productor Audiovisual · dirección visual de 01 Director Creativo.

Generaliza generar_cartel_itam.py para cualquier canal institucional con el
mismo trato: exactamente 2 boletos generales = $400, código con el nombre del
canal. Mismo arte (mono-pintura-recorte-poster-sin-marco.png), mismo layout
(título alineado a la izquierda sobre la franja oscura del retrato, línea
dorada donde termina la foto, bloque del canal centrado abajo, canvas
recortado al final del contenido — sin espacio negro muerto).

Uso:
    python3 generar_cartel_canal_2x1.py --canal UNAM \
        --logo 05_Activos/el-gorila/canales/unam/logo-unam.png \
        --out 05_Activos/el-gorila/carteles-s2/unam/cartel-unam-2x1-mobile.png

    python3 generar_cartel_canal_2x1.py --canal ITAM \
        --logo 05_Activos/el-gorila/canales/itam/logo-itam.png \
        --out 05_Activos/el-gorila/carteles-s2/itam/cartel-itam-2x1-mobile.png
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
RETRATO = REPO / "05_Activos/el-gorila/poster-elementos-sueltos/imagen/mono-pintura-recorte-poster-sin-marco.png"

NEGRO = (10, 9, 7)
DORADO = (196, 162, 87)
CREMA = (238, 231, 216)
ROJO = (196, 58, 39)

FUENTE_DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
FUENTE_BASKERVILLE = "/System/Library/Fonts/Supplemental/Baskerville.ttc"

W = 1080
H_SCRATCH = 3400  # lienzo de sobra para dibujar sin recortes; se recorta al final
ZONA_FOTO_H = 980  # altura de la franja del retrato — la línea dorada cae aquí
LEFT_X = 76  # margen izquierdo del bloque de título (zona oscura, no pisa la cara)


def f(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


def texto_izq(draw, texto, y, font, fill, x=LEFT_X, tracking=0):
    if tracking:
        cursor = x
        for ch in texto:
            draw.text((cursor, y), ch, font=font, fill=fill)
            cursor += draw.textlength(ch, font=font) + tracking
        bbox = draw.textbbox((0, 0), texto, font=font)
        return bbox[3] - bbox[1]
    draw.text((x, y), texto, font=font, fill=fill)
    bbox = draw.textbbox((0, 0), texto, font=font)
    return bbox[3] - bbox[1]


def texto_centrado(draw, texto, y, font, fill, cx, tracking=0):
    if tracking:
        anchos = [draw.textlength(ch, font=font) for ch in texto]
        total = sum(anchos) + tracking * (len(texto) - 1)
        x = cx - total / 2
        for ch, wch in zip(texto, anchos):
            draw.text((x, y), ch, font=font, fill=fill)
            x += wch + tracking
        bbox = draw.textbbox((0, 0), texto, font=font)
        return bbox[3] - bbox[1]
    bbox = draw.textbbox((0, 0), texto, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw / 2, y), texto, font=font, fill=fill)
    return bbox[3] - bbox[1]


def cargar_retrato_fondo(w, h_zona):
    foto = Image.open(RETRATO).convert("RGB")
    foto = ImageOps.fit(foto, (w, h_zona), method=Image.LANCZOS, centering=(0.62, 0.32))
    return foto


def construir(canal: str, logo_path: Path):
    w = W
    cartel = Image.new("RGB", (w, H_SCRATCH), NEGRO)

    zona_foto_h = ZONA_FOTO_H
    foto = cargar_retrato_fondo(w, zona_foto_h)
    cartel.paste(foto, (0, 0))

    grad = Image.new("L", (1, zona_foto_h), 0)
    for y in range(zona_foto_h):
        t = max(0, (y - zona_foto_h * 0.42) / (zona_foto_h * 0.58))
        grad.putpixel((0, y), int(255 * min(1, t)))
    grad = grad.resize((w, zona_foto_h))
    negro_layer = Image.new("RGB", (w, zona_foto_h), NEGRO)
    zona = Image.composite(negro_layer, foto, grad)
    cartel.paste(zona, (0, 0))

    draw = ImageDraw.Draw(cartel)
    cx = w // 2

    f_kicker = f(FUENTE_DIDOT, 54)
    f_titulo = f(FUENTE_DIDOT, 176)
    f_sub = f(FUENTE_BASKERVILLE, 50)
    f_detalle = f(FUENTE_BASKERVILLE, 52)
    f_fecha = f(FUENTE_DIDOT, 59, index=1)
    f_canal_kicker = f(FUENTE_BASKERVILLE, 48)
    f_canal_titulo = f(FUENTE_DIDOT, 152)
    f_canal_detalle = f(FUENTE_BASKERVILLE, 50)
    f_footer = f(FUENTE_BASKERVILLE, 40)

    y = 50
    texto_centrado(draw, "Humberto Dupeyrón en:", y, f_kicker, CREMA, cx)

    y = 320
    y += texto_izq(draw, "EL", y, f_titulo, DORADO)
    y += 16
    y += texto_izq(draw, "GORILA", y, f_titulo, DORADO)

    y += 44
    y += texto_izq(draw, "De Franz Kafka", y, f_sub, CREMA)
    y += 50

    draw.line([(LEFT_X, y), (LEFT_X + 56, y)], fill=DORADO, width=2)
    draw.ellipse([LEFT_X + 76 - 7, y - 7, LEFT_X + 76 + 7, y + 7], fill=DORADO)
    draw.line([(LEFT_X + 96, y), (LEFT_X + 152, y)], fill=DORADO, width=2)
    y += 50

    y += texto_izq(draw, "Sábados · 18 hrs", y, f_detalle, CREMA)
    y += 14
    y += texto_izq(draw, "Teatro Wilberto Cantón", y, f_detalle, CREMA)
    y += 30
    y += texto_izq(draw, "25 de julio al 19 de septiembre", y, f_fecha, DORADO)

    box_top = zona_foto_h
    draw.line([(90, box_top), (w - 90, box_top)], fill=DORADO, width=1)
    y = box_top + 64

    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((440, 230), Image.LANCZOS)
        pad_x, pad_y = 42, 30
        plaque_w, plaque_h = logo.width + pad_x * 2, logo.height + pad_y * 2
        plaque = Image.new("RGBA", (plaque_w, plaque_h), (0, 0, 0, 0))
        pdraw = ImageDraw.Draw(plaque)
        pdraw.rounded_rectangle([0, 0, plaque_w - 1, plaque_h - 1], radius=20, fill=(255, 255, 255, 255))
        plaque.paste(logo, (pad_x, pad_y), logo)
        cartel.paste(plaque, (cx - plaque_w // 2, y), plaque)
        y += plaque_h + 44
    else:
        logo_h = 150
        draw.rectangle([cx - 240, y, cx + 240, y + logo_h], outline=DORADO, width=2)
        texto_centrado(draw, f"LOGO {canal} AQUÍ", y + logo_h // 2 - 20, f_footer, DORADO, cx)
        y += logo_h + 44

    y += texto_centrado(draw, f"COMUNIDAD {canal}", y, f_canal_kicker, DORADO, cx, tracking=8)
    y += 40
    y += texto_centrado(draw, "2x1", y, f_canal_titulo, ROJO, cx)
    y += 155
    y += texto_centrado(draw, f"Estudiantes y trabajadores {canal}", y, f_canal_detalle, CREMA, cx)
    y += 14
    y += texto_centrado(draw, "Presenta tu credencial en taquilla", y, f_canal_detalle, CREMA, cx)
    y += 14
    y += texto_centrado(draw, f"o usa el código {canal} al comprar en línea", y, f_canal_detalle, CREMA, cx)

    y += 62
    draw.line([(90, y), (w - 90, y)], fill=DORADO, width=1)
    y += 52
    y += texto_centrado(draw, "elgorilateatro.com.mx", y, f_detalle, DORADO, cx)
    y += 34

    footer_h = 100
    footer_top = y
    h_final = footer_top + footer_h
    draw.rectangle([0, footer_top, w, h_final], fill=NEGRO)
    texto_centrado(
        draw, "El fenómeno teatral con 37 años en escena",
        footer_top + footer_h // 2 - 22, f_footer, CREMA, cx,
    )

    return cartel.crop((0, 0, w, h_final))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--canal", required=True, help="Nombre del canal/código, ej. ITAM, UNAM")
    parser.add_argument("--logo", required=True, help="Ruta al logo (PNG, idealmente transparente)")
    parser.add_argument("--out", required=True, help="Ruta de salida del PNG")
    args = parser.parse_args()

    logo_path = REPO / args.logo if not Path(args.logo).is_absolute() else Path(args.logo)
    out_path = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cartel = construir(args.canal.upper(), logo_path)
    cartel.save(out_path)
    print(f"Generado: {out_path.relative_to(REPO)} ({cartel.width}x{cartel.height})")
    if not logo_path.exists():
        print(f"⚠️  Falta el logo real en {logo_path} — el cartel salió con placeholder.")


if __name__ == "__main__":
    main()
