#!/usr/bin/env python3
"""
Generador de carteles — El Gorila S2
Agente: 08 Productor Audiovisual (ensambla) · dirección visual de 01 Director Creativo.

Reusa la misma base que generó cartel-estreno-25jul-feed-v1.png (fondo negro, marco
dorado, título rojo Didot, foto de personaje-aislado de 07_CartelesPeter) pero como
script parametrizable: agregar/quitar variantes editando EPOCAS abajo, sin tocar el
resto del código.

Uso:
    python3 generar_carteles.py                  # genera todas las variantes en EPOCAS
    python3 generar_carteles.py --solo 1989       # solo esa variante
    python3 generar_carteles.py --sizes google    # solo tamaños Google Ads

Salida: 05_Activos/el-gorila/carteles-s2/google-ads/{id}-{formato}.png
"""

import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
FOTOS_DIR = REPO / "07_CartelesPeter/public/assets/photos/personaje-aislado"
OUT_DIR = REPO / "05_Activos/el-gorila/carteles-s2/google-ads"

# ---------------------------------------------------------------------------
# Paleta e identidad (ver identidad.md / direccion-diseno-carteles-s2.md)
# ---------------------------------------------------------------------------
NEGRO = (10, 7, 6)
ROJO = (212, 58, 26)
CREMA = (242, 237, 228)
DORADO = (212, 175, 55)

FUENTE_DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
FUENTE_BASKERVILLE = "/System/Library/Fonts/Supplemental/Baskerville.ttc"

# ---------------------------------------------------------------------------
# Info canónica del cartel (fuente: carteleria-y-formatos.md / plaza-activa.md)
# ---------------------------------------------------------------------------
INFO = {
    "titulo": "EL GORILA",
    "actor": "con Humberto Dupeyrón",
    "fecha_evento": "ESTRENO · 25 DE JULIO",
    "detalle": "Sábados · 18:00 hrs · Teatro Wilberto Cantón",
    "cta": "Preventa $350 · elgorilateatro.com.mx",
    "trayectoria": "37 AÑOS EN ESCENA",
}

# ---------------------------------------------------------------------------
# Variantes por "época" — cada una es un creativo distinto para probar en
# Google Ads. treatment: "sepia" (look vintage) o "color" (2026, full color).
# Para agregar una variante nueva: agrega una entrada aquí con un archivo de
# 07_CartelesPeter/public/assets/photos/personaje-aislado/.
# ---------------------------------------------------------------------------
EPOCAS = [
    {"id": "1989-sepia", "foto": "24.png", "treatment": "sepia", "año": "1989"},
    {"id": "2026-color-a", "foto": "20.png", "treatment": "color", "año": "2026"},
    {"id": "2026-color-b", "foto": "1.png", "treatment": "color", "año": "2026"},
]

# Tamaños de salida. "master" es el cartel base (mismas proporciones que v1);
# los de Google se recortan/escalan a partir del master conservando el foco
# en la figura (crop centrado, no distorsiona).
FORMATOS = {
    "master": (1080, 1350),        # 4:5 — feed / fuente para los demás
    "google-landscape": (1200, 628),   # Responsive Display Ads — horizontal
    "google-square": (1200, 1200),     # Responsive Display Ads — cuadrado
}


def cargar_foto_tratada(nombre_archivo: str, treatment: str) -> Image.Image:
    ruta = FOTOS_DIR / nombre_archivo
    foto = Image.open(ruta).convert("RGBA")

    # recortar al contenido real (las fotos traen mucho margen transparente)
    bbox = foto.getbbox()
    if bbox:
        foto = foto.crop(bbox)

    # suavizar el borde del recorte (pendiente histórico: "blur/blend en fotos")
    r, g, b, a = foto.split()
    a = a.filter(ImageFilter.GaussianBlur(3))
    foto = Image.merge("RGBA", (r, g, b, a))

    if treatment == "sepia":
        gris = ImageOps.grayscale(foto)
        gris = ImageOps.autocontrast(gris, cutoff=1)
        sepia = ImageOps.colorize(gris, black=(35, 24, 15), white=(210, 180, 140))
        sepia.putalpha(a)
        foto = sepia
        # grano leve
        ruido = Image.effect_noise(foto.size, 22).convert("L")
        foto_rgb = foto.convert("RGB")
        foto_rgb = Image.blend(foto_rgb, Image.merge("RGB", (ruido, ruido, ruido)), 0.06)
        foto_rgb.putalpha(a)
        foto = foto_rgb
    else:
        # color 2026: un poco más de contraste/punch, sin pasarse
        rgb = foto.convert("RGB")
        rgb = ImageOps.autocontrast(rgb, cutoff=1)
        rgb.putalpha(a)
        foto = rgb

    return foto


def dibujar_marco(draw: ImageDraw.ImageDraw, size, margen=36, grosor=2):
    w, h = size
    draw.rectangle(
        [margen, margen, w - margen, h - margen], outline=DORADO, width=grosor
    )


def texto_centrado(draw, texto, y, font, fill, size, cx=None):
    w = cx if cx is not None else size[0]
    bbox = draw.textbbox((0, 0), texto, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) / 2, y), texto, font=font, fill=fill)
    return bbox[3] - bbox[1]


def construir_vertical(epoca: dict, size) -> Image.Image:
    """Layout tipo cartel: foto arriba, bloque de texto abajo. Usado para el
    feed 4:5 y el cuadrado de Google (proporciones distintas, mismo lenguaje)."""
    w, h = size
    s = h / 1350  # escala de referencia sobre el master original
    cartel = Image.new("RGB", size, NEGRO)

    foto = cargar_foto_tratada(epoca["foto"], epoca["treatment"])
    max_w, max_h = int(w * 0.82), int(h * 0.60)
    foto.thumbnail((max_w, max_h), Image.LANCZOS)
    fx = (w - foto.width) // 2
    fy = int(h * 0.05)
    cartel.paste(foto, (fx, fy), foto)

    draw = ImageDraw.Draw(cartel)
    dibujar_marco(draw, size, margen=int(36 * s) or 20)

    f_trayectoria = ImageFont.truetype(FUENTE_BASKERVILLE, max(16, int(26 * s)))
    f_titulo = ImageFont.truetype(FUENTE_DIDOT, max(48, int(128 * s)))
    f_actor = ImageFont.truetype(FUENTE_BASKERVILLE, max(18, int(34 * s)))
    f_evento = ImageFont.truetype(FUENTE_DIDOT, max(22, int(42 * s)))
    f_detalle = ImageFont.truetype(FUENTE_BASKERVILLE, max(14, int(26 * s)))
    f_cta = ImageFont.truetype(FUENTE_BASKERVILLE, max(13, int(24 * s)))

    y = int(h * 0.66)
    label_trayectoria = f"{epoca['año']} · {INFO['trayectoria']}"
    y += texto_centrado(draw, label_trayectoria, y, f_trayectoria, DORADO, size)

    y += int(28 * s)
    y += texto_centrado(draw, INFO["titulo"], y, f_titulo, ROJO, size)

    y += int(24 * s)
    y += texto_centrado(draw, INFO["actor"], y, f_actor, CREMA, size)

    y += int(30 * s)
    draw.line([(w * 0.32, y), (w * 0.68, y)], fill=DORADO, width=1)

    y += int(18 * s)
    y += texto_centrado(draw, INFO["fecha_evento"], y, f_evento, CREMA, size)

    y += int(16 * s)
    y += texto_centrado(draw, INFO["detalle"], y, f_detalle, CREMA, size)

    y += int(10 * s)
    texto_centrado(draw, INFO["cta"], y, f_cta, DORADO, size)

    return cartel


def construir_horizontal(epoca: dict, size) -> Image.Image:
    """Layout foto-izquierda / texto-derecha, para el formato 1200x628 de
    Google Responsive Display Ads (muy poca altura para apilar como el vertical)."""
    w, h = size
    s = h / 628
    cartel = Image.new("RGB", size, NEGRO)

    foto = cargar_foto_tratada(epoca["foto"], epoca["treatment"])
    max_w, max_h = int(w * 0.42), int(h * 0.92)
    foto.thumbnail((max_w, max_h), Image.LANCZOS)
    fx = int(w * 0.03)
    fy = h - foto.height
    cartel.paste(foto, (fx, fy), foto)

    draw = ImageDraw.Draw(cartel)
    dibujar_marco(draw, size, margen=max(10, int(20 * s)))

    cx0 = int(w * 0.48)
    cx_w = w - cx0 - int(30 * s)  # ancho disponible del bloque de texto

    f_trayectoria = ImageFont.truetype(FUENTE_BASKERVILLE, max(14, int(20 * s)))
    f_titulo = ImageFont.truetype(FUENTE_DIDOT, max(40, int(78 * s)))
    f_actor = ImageFont.truetype(FUENTE_BASKERVILLE, max(15, int(22 * s)))
    f_evento = ImageFont.truetype(FUENTE_DIDOT, max(18, int(28 * s)))
    f_detalle = ImageFont.truetype(FUENTE_BASKERVILLE, max(12, int(17 * s)))
    f_cta = ImageFont.truetype(FUENTE_BASKERVILLE, max(12, int(17 * s)))

    def linea(texto, y, font, fill):
        bbox = draw.textbbox((0, 0), texto, font=font)
        tw = bbox[2] - bbox[0]
        x = cx0 + (cx_w - tw) / 2
        draw.text((x, y), texto, font=font, fill=fill)
        return bbox[3] - bbox[1]

    y = int(h * 0.12)
    label_trayectoria = f"{epoca['año']} · {INFO['trayectoria']}"
    y += linea(label_trayectoria, y, f_trayectoria, DORADO)

    y += int(10 * s)
    y += linea(INFO["titulo"], y, f_titulo, ROJO)

    y += int(8 * s)
    y += linea(INFO["actor"], y, f_actor, CREMA)

    y += int(14 * s)
    draw.line([(cx0 + cx_w * 0.15, y), (cx0 + cx_w * 0.85, y)], fill=DORADO, width=1)

    y += int(12 * s)
    y += linea(INFO["fecha_evento"], y, f_evento, CREMA)

    y += int(6 * s)
    y += linea(INFO["detalle"], y, f_detalle, CREMA)

    y += int(6 * s)
    linea(INFO["cta"], y, f_cta, DORADO)

    return cartel


def generar(epoca: dict, sizes: list[str]):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    nombres = {
        "master": "feed-4x5",
        "google-square": "google-square",
        "google-landscape": "google-landscape",
    }

    for key in sizes:
        size = FORMATOS[key]
        if key == "google-landscape":
            pieza = construir_horizontal(epoca, size)
        else:
            pieza = construir_vertical(epoca, size)
        out = OUT_DIR / f"{epoca['id']}-{nombres[key]}.png"
        pieza.save(out)
        print(f"  {out.relative_to(REPO)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", help="generar solo esta variante (id de EPOCAS)")
    parser.add_argument(
        "--sizes",
        choices=["all", "google", "master"],
        default="all",
        help="all = master+google · google = solo tamaños Google Ads · master = solo el 4:5",
    )
    args = parser.parse_args()

    if args.sizes == "google":
        sizes = ["google-landscape", "google-square"]
    elif args.sizes == "master":
        sizes = ["master"]
    else:
        sizes = ["master", "google-landscape", "google-square"]

    epocas = EPOCAS
    if args.solo:
        epocas = [e for e in EPOCAS if e["id"] == args.solo]
        if not epocas:
            raise SystemExit(f"No existe la variante '{args.solo}' en EPOCAS")

    for epoca in epocas:
        print(f"Generando {epoca['id']} ({epoca['treatment']}, {epoca['año']})...")
        generar(epoca, sizes)


if __name__ == "__main__":
    main()
