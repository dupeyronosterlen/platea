#!/usr/bin/env python3
"""
Cartel — canal ITAM (2x1 estudiantes/trabajadores)
Agente: 08 Productor Audiovisual · dirección visual de 01 Director Creativo.

Formato vertical para celular (digital, IG/WA story). Reusa el retrato ya
existente (mono-pintura-recorte-poster-sin-marco.png, mismo arte que el
diploma de la Academia). Título y datos de función alineados a la izquierda
(zona oscura del retrato, sin pisar la cara); la línea dorada antes del
bloque ITAM cae aprox. donde termina la foto. El canvas se dibuja sobre un
lienzo alto de sobra y se recorta al final del contenido — sin espacio negro
muerto al final.

El logo de ITAM se pega en tiempo de ejecución si existe en LOGO_ITAM — si no,
deja un placeholder marcado para no bloquear la revisión del resto del cartel.

Uso:
    python3 generar_cartel_itam.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
RETRATO = REPO / "05_Activos/el-gorila/poster-elementos-sueltos/imagen/mono-pintura-recorte-poster-sin-marco.png"
LOGO_ITAM = REPO / "05_Activos/el-gorila/canales/itam/logo-itam.png"
OUT_DIR = REPO / "05_Activos/el-gorila/carteles-s2/itam"

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
    """Recorta/ajusta el retrato ya existente al ancho del cartel, anclado
    a la derecha (la cara), dejando la franja izquierda oscura libre para texto."""
    foto = Image.open(RETRATO).convert("RGB")
    foto = ImageOps.fit(foto, (w, h_zona), method=Image.LANCZOS, centering=(0.62, 0.32))
    return foto


def construir():
    w = W
    cartel = Image.new("RGB", (w, H_SCRATCH), NEGRO)

    # zona superior: retrato (arte ya existente)
    zona_foto_h = ZONA_FOTO_H
    foto = cargar_retrato_fondo(w, zona_foto_h)
    cartel.paste(foto, (0, 0))

    # degradado hacia negro en la base de la foto para que el texto que se
    # monta encima (título) no compita con la pintura
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
    f_itam_kicker = f(FUENTE_BASKERVILLE, 48)
    f_itam_titulo = f(FUENTE_DIDOT, 152)
    f_itam_detalle = f(FUENTE_BASKERVILLE, 50)
    f_footer = f(FUENTE_BASKERVILLE, 40)

    # kicker — centrado arriba, en la franja alta de la foto (no estorba la cara)
    y = 50
    texto_centrado(draw, "Humberto Dupeyrón en:", y, f_kicker, CREMA, cx)

    # título y datos — alineados a la izquierda, recorridos arriba, encima de
    # la franja oscura del retrato
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

    # ── línea divisoria — cae aprox. donde termina la foto ─────────────────
    box_top = zona_foto_h
    draw.line([(90, box_top), (w - 90, box_top)], fill=DORADO, width=1)
    y = box_top + 64

    # ── bloque ITAM 2x1 (centrado) ──────────────────────────────────────────
    if LOGO_ITAM.exists():
        logo = Image.open(LOGO_ITAM).convert("RGBA")
        logo.thumbnail((480, 150), Image.LANCZOS)
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
        texto_centrado(draw, "LOGO ITAM AQUÍ", y + logo_h // 2 - 20, f_footer, DORADO, cx)
        y += logo_h + 44

    y += texto_centrado(draw, "COMUNIDAD ITAM", y, f_itam_kicker, DORADO, cx, tracking=8)
    y += 40
    y += texto_centrado(draw, "2x1", y, f_itam_titulo, ROJO, cx)
    y += 155
    y += texto_centrado(draw, "Estudiantes y trabajadores ITAM", y, f_itam_detalle, CREMA, cx)
    y += 14
    y += texto_centrado(draw, "Presenta tu credencial en taquilla", y, f_itam_detalle, CREMA, cx)
    y += 14
    y += texto_centrado(draw, "o usa el código ITAM al comprar en línea", y, f_itam_detalle, CREMA, cx)

    y += 62
    draw.line([(90, y), (w - 90, y)], fill=DORADO, width=1)
    y += 52
    y += texto_centrado(draw, "elgorilateatro.com.mx", y, f_detalle, DORADO, cx)
    y += 34

    # footer — pegado al contenido, sin espacio muerto
    footer_h = 100
    footer_top = y
    h_final = footer_top + footer_h
    draw.rectangle([0, footer_top, w, h_final], fill=NEGRO)
    texto_centrado(
        draw, "El fenómeno teatral con 37 años en escena",
        footer_top + footer_h // 2 - 22, f_footer, CREMA, cx,
    )

    # recorte final — elimina cualquier lienzo sobrante debajo del footer
    return cartel.crop((0, 0, w, h_final))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cartel = construir()
    out = OUT_DIR / "cartel-itam-2x1-mobile.png"
    cartel.save(out)
    print(f"Generado: {out.relative_to(REPO)} ({cartel.width}x{cartel.height})")
    if not LOGO_ITAM.exists():
        print(f"⚠️  Falta el logo real en {LOGO_ITAM.relative_to(REPO)} — el cartel salió con placeholder.")


if __name__ == "__main__":
    main()
