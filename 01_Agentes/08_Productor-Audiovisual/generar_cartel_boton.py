#!/usr/bin/env python3
"""
Generador de cartel — botón/thumbnail para listados de boletera (ej. Ticketmaster).
Agente: 08 Productor Audiovisual · dirección visual de 01 Director Creativo.
Sigue la skill .claude/skills/cartel-diseno-teoria/, Modo poca info (§0): máximo
3 bloques de texto, sin precio, sin créditos técnicos, sin logo de coproducción.

Estructura: foto a sangre completa (full-bleed) + texto superpuesto abajo-izquierda,
badge "37 años" arriba-derecha (zona muerta de Gutenberg) — replica el layout que
Dirección pidió como referencia (pedido 24 jul 2026), no la Estructura C de columna
central que usan generar_cartel_impreso.py / generar_cartel_ticketmaster.py.

Foto: personaje-aislado/DSC03878.png (banco de fotos del repo) — gesto dramático
bañado en luz roja, más "interesante" que la foto de acción usada en el primer
intento (pedido explícito de Dirección de cambiarla).

Uso:
    python3 generar_cartel_boton.py                 # 1200x1200 (default)
    python3 generar_cartel_boton.py --size 1500x1500

Salida: 05_Activos/el-gorila/carteles-s2/impreso/cartel-boton-{size}.png
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "05_Activos/el-gorila"
OUT_DIR = ASSETS / "carteles-s2/impreso"

FOTO_HERO = ASSETS / "banco-fotos/_subidas-chat/personaje-baqueta-cortina-roja.webp"

# Físico pedido por Dirección (24 jul 2026): 64cm ancho × 73cm alto. La foto que Dirección pegó
# en el chat es de baja resolución nativa (902×822px) — a 300dpi de impresión real
# (7559×8622px) se vería visiblemente suave/pixelada al ampliarse ~8x. Como el uso
# es un listado digital de Ticketmaster (no una lona física), se genera a una
# resolución más honesta con el material fuente en vez de fingir calidad de
# impresión que la foto no tiene. Si esto se imprime físicamente, pedir a Dirección la
# foto original en alta resolución.
ANCHO_CM, ALTO_CM = 64, 73
_ESCALA_WEB = 2000 / ANCHO_CM  # ~31px/cm — nítido en pantalla, no finge 300dpi
BADGE_37 = Path("/Volumes/La Mancha/Elgorila/4. Publicidad/13. Elementos Gráficos/badges/37Anos.png")

TIPOGRAFIA = ASSETS / "tipografia"
FUENTE_PRIMARIA = TIPOGRAFIA / "primaria/CormorantGaramond-Bold.ttf"
FUENTE_PRIMARIA_ITALIC = TIPOGRAFIA / "primaria/CormorantGaramond-Italic.ttf"
FUENTE_SECUNDARIA_ITALIC = TIPOGRAFIA / "secundaria/Lato-Regular.ttf"

CREMA = (245, 240, 232)
ROJO = (212, 58, 26)
GRIS_CLARO = (200, 195, 188)

INFO = {
    "titulo_1": "EL",
    "titulo_2": "GORILA",
    "actor": "con Humberto Dupeyrón",
    "referencia": "basado en «Informe para una Academia» de Franz Kafka",
}


def _verificar_assets():
    faltantes = [p for p in [FOTO_HERO, FUENTE_PRIMARIA, FUENTE_PRIMARIA_ITALIC] if not p.exists()]
    if faltantes:
        detalle = "\n".join(f"  - {p}" for p in faltantes)
        raise SystemExit(f"Faltan assets:\n{detalle}")


def cargar_badge_37(w) -> Image.Image | None:
    if not BADGE_37.exists():
        return None
    badge = Image.open(BADGE_37).convert("RGB")
    alpha = badge.convert("L").point(lambda v: min(255, int(v * 1.4)))
    badge_rgba = badge.copy()
    badge_rgba.putalpha(alpha)
    badge_w = int(w * 0.16)
    badge_rgba.thumbnail((badge_w, badge_w), Image.LANCZOS)
    return badge_rgba


def altura_linea(font) -> int:
    ascent, descent = font.getmetrics()
    return ascent + descent


def fuente_ajustada(texto, ruta_fuente, tam_deseado, ancho_max, tam_min=10) -> ImageFont.FreeTypeFont:
    tam = tam_deseado
    while tam > tam_min:
        f = ImageFont.truetype(str(ruta_fuente), tam)
        if f.getlength(texto) <= ancho_max:
            return f
        tam -= max(1, int(tam * 0.05))
    return ImageFont.truetype(str(ruta_fuente), tam_min)


def construir(size) -> Image.Image:
    w, h = size
    s = w / 1200
    cartel = Image.new("RGB", size, (0, 0, 0))
    draw = ImageDraw.Draw(cartel)

    # ============ Foto a sangre completa ============
    foto = Image.open(FOTO_HERO).convert("RGB")
    foto = ImageOps.fit(foto, (w, h), method=Image.LANCZOS, centering=(0.5, 0.32))
    cartel.paste(foto, (0, 0))

    # ============ Scrim inferior — garantiza contraste WCAG para el texto ============
    # Zona de transición (fade foto->negro) solo en el primer tramo del scrim;
    # el resto queda negro sólido para que el texto NUNCA quede rojo-sobre-rojo
    # (la foto tiene tonos rojos intensos que tragaban el título en la v1).
    scrim_h = int(h * 0.50)
    transicion = 0.30
    scrim = Image.new("L", (1, scrim_h), 255)
    for y in range(scrim_h):
        frac = y / scrim_h
        if frac < transicion:
            scrim.putpixel((0, y), int(255 * (frac / transicion) ** 1.3))
        else:
            scrim.putpixel((0, y), 255)
    scrim = scrim.resize((w, scrim_h))
    negro = Image.new("RGB", (w, scrim_h), (0, 0, 0))
    cartel.paste(negro, (0, h - scrim_h), scrim)

    # ============ Badge arriba-derecha (zona muerta de Gutenberg) ============
    badge = cargar_badge_37(w)
    if badge:
        margen = int(w * 0.05)
        cartel.paste(badge, (w - badge.width - margen, margen), badge)

    # ============ Texto — abajo-izquierda (área terminal de Gutenberg) ============
    margen_x = int(w * 0.07)
    ancho_max = int(w * 0.86)

    f_titulo = fuente_ajustada("GORILA", FUENTE_PRIMARIA, int(h * 0.115), int(ancho_max * 0.75))
    f_titulo_it = ImageFont.truetype(str(FUENTE_PRIMARIA_ITALIC), f_titulo.size)
    f_actor = fuente_ajustada(INFO["actor"], FUENTE_PRIMARIA, int(h * 0.045), ancho_max)
    f_ref = fuente_ajustada(INFO["referencia"], FUENTE_SECUNDARIA_ITALIC, int(h * 0.026), ancho_max)

    y = h - scrim_h + int(scrim_h * 0.38)

    x = margen_x
    draw.text((x, y), INFO["titulo_1"] + " ", font=f_titulo, fill=CREMA)
    x += draw.textlength(INFO["titulo_1"] + " ", font=f_titulo)
    draw.text((x, y), INFO["titulo_2"], font=f_titulo_it, fill=ROJO)
    y += altura_linea(f_titulo) + int(h * 0.02)

    draw.text((margen_x, y), INFO["actor"], font=f_actor, fill=CREMA)
    y += altura_linea(f_actor) + int(h * 0.018)

    draw.text((margen_x, y), INFO["referencia"], font=f_ref, fill=GRIS_CLARO)

    return cartel


def main():
    _verificar_assets()
    parser = argparse.ArgumentParser()
    default_size = f"{round(ANCHO_CM * _ESCALA_WEB)}x{round(ALTO_CM * _ESCALA_WEB)}"
    parser.add_argument("--size", default=default_size, help="ej. 2000x2281 (default: 64x73cm a escala web)")
    args = parser.parse_args()

    w, h = (int(v) for v in args.size.lower().split("x"))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cartel = construir((w, h))
    out = OUT_DIR / f"cartel-boton-{w}x{h}.png"
    cartel.save(out)
    print(f"Generado: {out.relative_to(REPO)} ({w}x{h})")


if __name__ == "__main__":
    main()
