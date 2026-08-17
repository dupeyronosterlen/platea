#!/usr/bin/env python3
"""
Headers/Solus con TODO el texto del cartel (instrucción de Dirección, 29 jul 2026:
"esta es la info que debe venir en el cartel de todos los headers and souls,
no te comas el texto, acomódalo donde deba ser") — EXCEPTO la fecha de
temporada, que se sigue omitiendo (decisión confirmada 29 jul: Ticketmaster
gestiona fechas directo con Dirección).

Elementos de texto usados (extraídos del PSD, ver 05_Activos/el-gorila/
poster-elementos-sueltos/texto/):
  Humberto Dupeyron en: / EL GORILA / De Franz Kafka / Sábados · 18 hrs /
  Teatro Wilberto Cantón / · Entradas · / elgorilateatro.com.mx /
  El fenómeno teatral con 37 años en escena

Layout: columna de texto a la izquierda (todo el stack, escalado para que
quepa completo — nunca se recorta ni se omite una línea), imagen a sangre a
la derecha (recorte limpio de poster-elementos-sueltos, sin texto pintado).

Uso:
    python3 generar_headers_con_texto.py --solo mailing_header
    python3 generar_headers_con_texto.py   # todos los headers/solus

Salida: 03_Producciones/el-gorila/canales/Ticketmaster/bases-frame/con-texto/
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

REPO = Path(__file__).resolve().parents[2]
TEXTO_DIR = REPO / "05_Activos/el-gorila/poster-elementos-sueltos/texto"
IMAGEN_LIMPIA = REPO / "05_Activos/el-gorila/poster-elementos-sueltos/imagen/mono-pintura-completa-sin-marco.png"
OUT_DIR = REPO / "03_Producciones/el-gorila/canales/Ticketmaster/bases-frame/con-texto"

NEGRO = (10, 7, 6)

# "es:" no "en:" (decisión de Dirección, 29 jul 2026) — asset generado aparte
# (humberto-dupeyron-es.png) porque el PSD original solo trae "en:".
STACK_TEXTO = [
    "humberto-dupeyron-es.png",
    "el-gorila.png",
    "de-franz-kafka.png",
    "horario-sabados-18hrs.png",
    "venue-teatro-wilberto-canton.png",
]

# Formato reducido (Dirección, 29 jul 2026): solo crédito+título+subtítulo, sin
# horario/venue/legado — usado en Hero/Medium/Small (piezas hechas por Dirección) y
# ahora también en EADP Header y Push, por instrucción explícita.
STACK_REDUCIDO = [
    "humberto-dupeyron-es.png",
    "el-gorila.png",
    "de-franz-kafka.png",
]

# clave -> (ancho, alto, nombre_archivo, "completo"|"reducido")
FORMATOS = {
    "mailing_header": (640, 360, "Mailing_HeaderSolus_640x360", "completo"),
    "eadp_header_desktop": (1024, 432, "EADP_HeaderDesktop_1024x432", "reducido"),
    "eadp_header_mobile": (375, 310, "EADP_HeaderMobile_375x310", "reducido"),
    "push": (305, 225, "PushNotification_305x225", "reducido"),
    "imagehero": (1440, 450, "ImageHero_1440x450_El-Gorila", "reducido"),
    "mediumimage": (720, 405, "MediumImage_720x405_El-Gorila", "reducido"),
    "smallimage": (368, 207, "SmallImage_368x207_El-Gorila", "reducido"),
}


def _col_texto(stack, ancho_col, alto_disponible):
    """Arma el stack de texto escalado a `ancho_col`, reduciendo la escala
    global las veces que haga falta hasta que quepa TODO en
    `alto_disponible` sin recortar ni omitir ninguna línea."""
    gap_frac = 0.10  # gap entre líneas, relativo al alto de cada línea

    for escala in (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.42, 0.35):
        imgs = []
        for nombre in stack:
            im = Image.open(TEXTO_DIR / nombre).convert("RGBA")
            nuevo_w = max(1, int(ancho_col * escala))
            nuevo_h = max(1, int(im.height * (nuevo_w / im.width)))
            imgs.append(im.resize((nuevo_w, nuevo_h), Image.LANCZOS))

        gaps = [max(1, int(im.height * gap_frac)) for im in imgs[:-1]]
        total_h = sum(im.height for im in imgs) + sum(gaps)
        if total_h <= alto_disponible:
            return imgs, gaps, total_h

    return imgs, gaps, total_h  # devuelve la más chica aunque no quepa del todo


def construir_header(size) -> Image.Image:
    """Formato COMPLETO — texto integrado sobre la imagen: título+créditos
    arriba a la izquierda, barra negra al pie con la línea de legado
    ('El fenómeno teatral...'). Usado solo en Mailing Header/Solus."""
    w, h = size
    margen = max(8, int(w * 0.04))

    arte = Image.open(IMAGEN_LIMPIA).convert("RGB")
    cartel = ImageOps.fit(arte, size, method=Image.LANCZOS, centering=(0.62, 0.38))

    fenomeno = Image.open(TEXTO_DIR / "fenomeno-37-anos-en-escena.png").convert("RGBA")
    barra_h = max(20, int(h * 0.14))
    fen_w = int(w * 0.86)
    fen_h = max(1, int(fenomeno.height * (fen_w / fenomeno.width)))
    if fen_h > barra_h * 0.62:
        fen_h = int(barra_h * 0.62)
        fen_w = max(1, int(fenomeno.width * (fen_h / fenomeno.height)))
    fenomeno = fenomeno.resize((fen_w, fen_h), Image.LANCZOS)

    draw = ImageDraw.Draw(cartel)
    draw.rectangle([0, h - barra_h, w, h], fill=NEGRO)
    cartel.paste(fenomeno, ((w - fen_w) // 2, h - barra_h + (barra_h - fen_h) // 2), fenomeno)

    ancho_texto = int(w * 0.6)
    alto_disponible = (h - barra_h) - 2 * margen
    imgs, gaps, total_h = _col_texto(STACK_TEXTO, ancho_texto, alto_disponible)
    y = margen
    for i, im in enumerate(imgs):
        cartel.paste(im, (margen, y), im)
        y += im.height + (gaps[i] if i < len(gaps) else 0)

    return cartel


def construir_reducido(size) -> Image.Image:
    """Formato REDUCIDO — solo crédito+título+subtítulo, sin horario/venue/
    legado, sin barra inferior. Mismo estilo que Hero/Medium/Small (Dirección,
    29 jul 2026). Imagen a sangre completa, texto arriba a la izquierda."""
    w, h = size
    margen = max(8, int(w * 0.045))

    arte = Image.open(IMAGEN_LIMPIA).convert("RGB")
    cartel = ImageOps.fit(arte, size, method=Image.LANCZOS, centering=(0.62, 0.38))

    ancho_texto = int(w * 0.6)
    alto_disponible = h - 2 * margen
    imgs, gaps, total_h = _col_texto(STACK_REDUCIDO, ancho_texto, alto_disponible)
    y = (h - total_h) // 2
    for i, im in enumerate(imgs):
        cartel.paste(im, (margen, y), im)
        y += im.height + (gaps[i] if i < len(gaps) else 0)

    return cartel


CONSTRUCTORES = {"completo": construir_header, "reducido": construir_reducido}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", choices=list(FORMATOS.keys()))
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    items = {args.solo: FORMATOS[args.solo]} if args.solo else FORMATOS

    for _clave, (w, h, nombre, modo) in items.items():
        print(f"Generando {nombre} ({w}x{h}, {modo})...")
        cartel = CONSTRUCTORES[modo]((w, h))
        out = OUT_DIR / f"{nombre}.jpg"
        cartel.save(out, quality=95)
        print(f"  {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
