#!/usr/bin/env python3
"""
Generador de assets — Categoría D: Oficial / plataformas de descuento.
Plataforma: Cartelera de Teatro (descuentos.carteleradeteatro.mx).
Agente: 08 Productor Audiovisual · dirección visual de 01 Director Creativo.
Sigue la skill .claude/skills/cartel-diseno-teoria/.

Dos formatos exigidos por el formulario de alta (26 jul 2026):
  - 250x300 px  — "pleca": arte de póster completo + barra roja inferior con
                  categoría y horario, replicando el patrón real observado en
                  el sitio (ver ejemplos como "El Libro de la Selva-Pleca").
  - 1260x300 px — banner ancho: mismo lenguaje visual ya usado en el banner de
                  Teatrando (foto + bloque de texto + doble marco dorado), pero
                  con más aire vertical porque el ratio es menos panorámico
                  (4.2:1 vs 6.4:1 de Teatrando).

Fuente del arte: el póster maestro ya aprobado para SOGEM
(05_Activos/el-gorila/carteles-s2/sogem-cartelera/02-fb-ig-1080x1080.jpg) y la
foto de acción real (banco-fotos/feed-1x1/16.jpg) — no se genera arte nuevo
desde cero, se reutiliza y adapta el que ya pasó el checklist de la skill.

Uso:
    python3 generar_cartel_cartelera_teatro.py            # ambos formatos
    python3 generar_cartel_cartelera_teatro.py --solo pleca
    python3 generar_cartel_cartelera_teatro.py --solo banner

Auditoría (correr después, siempre):
    python3 .claude/skills/cartel-diseno-teoria/scripts/auditar_cartel.py <ruta.png>

Salida: 03_Producciones/el-gorila/canales/cartelera-de-teatro/PARA-ENVIAR/
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "05_Activos/el-gorila"
OUT_DIR = REPO / "03_Producciones/el-gorila/canales/cartelera-de-teatro/PARA-ENVIAR"

POSTER_FUENTE = ASSETS / "carteles-s2/sogem-cartelera/02-fb-ig-1080x1080.jpg"
FOTO_HERO = ASSETS / "banco-fotos/feed-1x1/16.jpg"

TIPOGRAFIA = ASSETS / "tipografia"
F_PRIMARIA_BOLD = TIPOGRAFIA / "primaria/CormorantGaramond-Bold.ttf"
F_PRIMARIA_ITALIC = TIPOGRAFIA / "primaria/CormorantGaramond-Italic.ttf"
F_SECUNDARIA = TIPOGRAFIA / "secundaria/Lato-Regular.ttf"
F_SECUNDARIA_BOLD = TIPOGRAFIA / "secundaria/Lato-Bold.ttf"

NEGRO = (10, 7, 6)
CREMA = (245, 240, 232)
DORADO = (201, 168, 76)
ROJO = (212, 58, 26)

INFO = {
    "categoria": "MONÓLOGO",
    "horario": "SÁBADOS 18:00 HRS",
    "titulo": "EL GORILA",
    "tagline": "Humberto Dupeyrón  ·  37 años en escena  ·  basado en Kafka",
    "venue_linea": "TEATRO WILBERTO CANTÓN  ·  SÁBADOS 18:00 H",
}


def _verificar_assets():
    faltantes = [
        p for p in [POSTER_FUENTE, FOTO_HERO, F_PRIMARIA_BOLD, F_SECUNDARIA, F_SECUNDARIA_BOLD]
        if not p.exists()
    ]
    if faltantes:
        detalle = "\n".join(f"  - {p}" for p in faltantes)
        raise SystemExit(f"Faltan assets:\n{detalle}")


def fuente_ajustada(texto, ruta_fuente, tam_deseado, ancho_max, tam_min=8):
    tam = tam_deseado
    while tam > tam_min:
        f = ImageFont.truetype(str(ruta_fuente), tam)
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        if draw.textlength(texto, font=f) <= ancho_max:
            return f
        tam -= max(1, int(tam * 0.05))
    return ImageFont.truetype(str(ruta_fuente), tam_min)


def texto_centrado(draw, texto, cx, y, font, fill):
    bbox = draw.textbbox((0, 0), texto, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw / 2, y), texto, font=font, fill=fill)


# ============================================================ 250x300 pleca
def construir_pleca() -> Image.Image:
    W, H = 250, 300
    BARRA_H = 55
    img_h = H - BARRA_H  # 245

    cartel = Image.new("RGB", (W, H), NEGRO)
    draw = ImageDraw.Draw(cartel)

    poster = Image.open(POSTER_FUENTE).convert("RGB")
    # el póster fuente es cuadrado (1080x1080); recortamos ligeramente el
    # borde inferior (donde vive texto de fechas, menos crítico a esta escala)
    # para llenar el área 250x245 sin deformar proporciones.
    poster_fit = ImageOps.fit(poster, (W, img_h), method=Image.LANCZOS, centering=(0.5, 0.38))
    cartel.paste(poster_fit, (0, 0))

    draw.rectangle([0, img_h, W, H], fill=ROJO)
    cx = W // 2
    f_cat = fuente_ajustada(INFO["categoria"], F_SECUNDARIA_BOLD, 17, int(W * 0.9))
    f_hor = fuente_ajustada(INFO["horario"], F_SECUNDARIA, 13, int(W * 0.9))
    texto_centrado(draw, INFO["categoria"], cx, img_h + 6, f_cat, CREMA)
    texto_centrado(draw, INFO["horario"], cx, img_h + 28, f_hor, CREMA)

    return cartel


# ======================================================== 1260x300 banner
def construir_banner() -> Image.Image:
    W, H = 1260, 300
    cartel = Image.new("RGB", (W, H), NEGRO)
    draw = ImageDraw.Draw(cartel)

    margen = 14
    draw.rectangle([margen, margen, W - margen, H - margen], outline=DORADO, width=2)
    draw.rectangle([margen + 6, margen + 6, W - margen - 6, H - margen - 6], outline=DORADO, width=1)

    # ---- foto cuadrada a la izquierda ----
    lado = H - 2 * (margen + 24)
    foto = Image.open(FOTO_HERO).convert("RGB")
    foto = ImageOps.fit(foto, (lado, lado), method=Image.LANCZOS, centering=(0.5, 0.32))
    fx, fy = margen + 24, (H - lado) // 2
    cartel.paste(foto, (fx, fy))
    draw.rectangle([fx, fy, fx + lado, fy + lado], outline=DORADO, width=2)

    # ---- bloque de texto a la derecha ----
    tx = fx + lado + 40
    ancho_txt = W - margen - 30 - tx

    f_titulo = fuente_ajustada(INFO["titulo"], F_PRIMARIA_BOLD, 90, ancho_txt)
    f_tagline = fuente_ajustada(INFO["tagline"], F_SECUNDARIA, 22, ancho_txt)
    f_venue = fuente_ajustada(INFO["venue_linea"], F_SECUNDARIA_BOLD, 19, ancho_txt)

    y = H * 0.24
    draw.text((tx, y), INFO["titulo"], font=f_titulo, fill=ROJO)
    y += f_titulo.size + 18
    draw.text((tx, y), INFO["tagline"], font=f_tagline, fill=CREMA)
    y += f_tagline.size + 26
    draw.text((tx, y), INFO["venue_linea"], font=f_venue, fill=DORADO)

    return cartel


def main():
    _verificar_assets()
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", choices=["pleca", "banner"], help="generar solo un formato")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not args.solo or args.solo == "pleca":
        out = OUT_DIR / "cartelera-de-teatro-poster-250x300.jpg"
        construir_pleca().save(out, quality=95)
        print(f"  {out.relative_to(REPO)}")

    if not args.solo or args.solo == "banner":
        out = OUT_DIR / "cartelera-de-teatro-banner-1260x300.jpg"
        construir_banner().save(out, quality=95)
        print(f"  {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
