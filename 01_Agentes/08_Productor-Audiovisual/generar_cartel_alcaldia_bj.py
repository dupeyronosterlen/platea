#!/usr/bin/env python3
"""
Generador de assets — Canal Alcaldía Benito Juárez (difusión institucional gratuita).
Agente: 08 Productor Audiovisual · dirección visual de 01 Director Creativo.
Sigue la skill .claude/skills/cartel-diseno-teoria/ — Estructura C (minimalismo),
misma receta visual ya usada en SOGEM / Cartelera de Teatro / Ticketmaster
(paleta NEGRO/CREMA/DORADO/ROJO, Cormorant Garamond + Lato).

Sin formulario/formato exigido conocido (no hay proceso de alta público, ver
canales/alcaldia-benito-juarez/README.md) — se generan 2 formatos genéricos
que cubren los usos más probables:
  - 1080x1080 px — cuadrado, para adjuntar al correo / publicar en redes propias
                    de la alcaldía si lo piden en ese formato.
  - 1275x1650 px (Carta, 150dpi) — vertical, para imprimir y pegar en tablón
                    físico de una Casa de Cultura si la alcaldía lo pide impreso.

Datos verificados contra produccion.yaml (precios/fechas) al momento de generar.

Uso:
    python3 generar_cartel_alcaldia_bj.py            # ambos formatos
    python3 generar_cartel_alcaldia_bj.py --solo cuadrado
    python3 generar_cartel_alcaldia_bj.py --solo carta

Auditoría (correr después, siempre):
    python3 .claude/skills/cartel-diseno-teoria/scripts/auditar_cartel.py <ruta.png>

Salida: 03_Producciones/el-gorila/canales/alcaldia-benito-juarez/PARA-ENVIAR/
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "05_Activos/el-gorila"
OUT_DIR = REPO / "03_Producciones/el-gorila/canales/alcaldia-benito-juarez/PARA-ENVIAR"

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
    "titulo": "EL GORILA",
    "tagline": "Humberto Dupeyrón  ·  37 años en escena  ·  basado en Kafka",
    "venue_horario": "Teatro Wilberto Cantón  ·  Sábados 18:00 h  ·  hasta el 19 sep",
    "web": "elgorilateatro.com.mx",
}


def _verificar_assets():
    faltantes = [
        p for p in [POSTER_FUENTE, FOTO_HERO, F_PRIMARIA_BOLD, F_SECUNDARIA, F_SECUNDARIA_BOLD]
        if not p.exists()
    ]
    if faltantes:
        detalle = "\n".join(f"  - {p}" for p in faltantes)
        raise SystemExit(f"Faltan assets:\n{detalle}")


def fuente_ajustada(texto, ruta_fuente, tam_deseado, ancho_max, draw, tam_min=8):
    tam = tam_deseado
    while tam > tam_min:
        f = ImageFont.truetype(str(ruta_fuente), tam)
        if draw.textlength(texto, font=f) <= ancho_max:
            return f
        tam -= max(1, int(tam * 0.05))
    return ImageFont.truetype(str(ruta_fuente), tam_min)


def texto_centrado(draw, texto, cx, y, font, fill):
    bbox = draw.textbbox((0, 0), texto, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw / 2, y), texto, font=font, fill=fill)
    return bbox[3] - bbox[1]


# ============================================================ 1080x1080 cuadrado
def construir_cuadrado() -> Image.Image:
    W, H = 1080, 1080
    cartel = Image.new("RGB", (W, H), NEGRO)
    draw = ImageDraw.Draw(cartel)
    cx = W // 2

    # Sin marco decorativo — cada línea de borde le resta % de vacío real a la
    # grilla de auditoría sin aportar jerarquía (skill §2/§6). Estructura C:
    # foto ~30% del lienzo, punto focal en tercio superior, resto es aire.
    lado_foto = int(W * 0.40)
    foto = Image.open(FOTO_HERO).convert("RGB")
    foto = ImageOps.fit(foto, (lado_foto, lado_foto), method=Image.LANCZOS, centering=(0.5, 0.30))
    fx = cx - lado_foto // 2
    fy = int(H * 0.12)
    cartel.paste(foto, (fx, fy))

    y = fy + lado_foto + int(H * 0.10)
    ancho_txt = int(W * 0.78)

    f_titulo = fuente_ajustada(INFO["titulo"], F_PRIMARIA_BOLD, 100, ancho_txt, draw)
    y += texto_centrado(draw, INFO["titulo"], cx, y, f_titulo, ROJO) + 26

    f_tag = fuente_ajustada(INFO["tagline"], F_SECUNDARIA, 22, ancho_txt, draw)
    y += texto_centrado(draw, INFO["tagline"], cx, y, f_tag, CREMA) + 34

    f_venue = fuente_ajustada(INFO["venue_horario"], F_SECUNDARIA_BOLD, 22, ancho_txt, draw)
    y += texto_centrado(draw, INFO["venue_horario"], cx, y, f_venue, DORADO) + 34

    f_web = fuente_ajustada(INFO["web"], F_SECUNDARIA, 20, ancho_txt, draw)
    texto_centrado(draw, INFO["web"], cx, y, f_web, DORADO)

    return cartel


# ============================================================ Carta vertical (impreso)
def construir_carta() -> Image.Image:
    W, H = 1275, 1650  # 8.5x11in @150dpi
    cartel = Image.new("RGB", (W, H), NEGRO)
    draw = ImageDraw.Draw(cartel)
    cx = W // 2

    lado_foto = int(W * 0.46)
    foto = Image.open(FOTO_HERO).convert("RGB")
    foto = ImageOps.fit(foto, (lado_foto, lado_foto), method=Image.LANCZOS, centering=(0.5, 0.30))
    fx = cx - lado_foto // 2
    fy = int(H * 0.12)
    cartel.paste(foto, (fx, fy))

    y = fy + lado_foto + int(H * 0.09)
    ancho_txt = int(W * 0.76)

    f_titulo = fuente_ajustada(INFO["titulo"], F_PRIMARIA_BOLD, 150, ancho_txt, draw)
    y += texto_centrado(draw, INFO["titulo"], cx, y, f_titulo, ROJO) + 34

    f_tag = fuente_ajustada(INFO["tagline"], F_SECUNDARIA, 30, ancho_txt, draw)
    y += texto_centrado(draw, INFO["tagline"], cx, y, f_tag, CREMA) + 44

    f_venue = fuente_ajustada(INFO["venue_horario"], F_SECUNDARIA_BOLD, 28, ancho_txt, draw)
    y += texto_centrado(draw, INFO["venue_horario"], cx, y, f_venue, DORADO) + 44

    f_web = fuente_ajustada(INFO["web"], F_SECUNDARIA, 26, ancho_txt, draw)
    texto_centrado(draw, INFO["web"], cx, y, f_web, DORADO)

    return cartel


def main():
    _verificar_assets()
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", choices=["cuadrado", "carta"], help="generar solo un formato")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not args.solo or args.solo == "cuadrado":
        out = OUT_DIR / "alcaldia-bj-cuadrado-1080x1080.jpg"
        construir_cuadrado().save(out, quality=95)
        print(f"  {out.relative_to(REPO)}")

    if not args.solo or args.solo == "carta":
        out = OUT_DIR / "alcaldia-bj-carta-1275x1650.jpg"
        construir_carta().save(out, quality=95)
        print(f"  {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
