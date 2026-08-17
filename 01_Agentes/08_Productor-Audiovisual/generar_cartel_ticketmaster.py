#!/usr/bin/env python3
"""
Generador de cartel — Categoría D: Oficial / impreso, formato Ticketmaster.
Agente: 08 Productor Audiovisual · dirección visual de 01 Director Creativo.
Sigue la skill .claude/skills/cartel-diseno-teoria/ (Estructura C, regla 60/30/10).

Formato físico: 64cm ancho × 73cm alto (vertical, ratio ~0.877:1) — pedido
puntual de Dirección (24 jul 2026) para subir a Ticketmaster. No confundir con la
lona 2.5×1.5m de generar_cartel_impreso.py (otro formato, otro script).

Foto: acción en vivo (feed-1x1/16.jpg, banco de fotos del repo — no requiere
el disco La Mancha). Regla de oro #10 (CLAUDE.md §6): a partir del 24 jul 2026
la campaña es de TEMPORADA (el estreno del 25 jul ya pasó la preventa), así
que este cartel NO lleva precio en el cuerpo principal — urgencia/escasez
("9 funciones") en su lugar. El precio real sigue viviendo en la boletera.

Uso:
    python3 generar_cartel_ticketmaster.py              # preview + print
    python3 generar_cartel_ticketmaster.py --solo preview

Auditoría (correr después de generar, siempre):
    python3 .claude/skills/cartel-diseno-teoria/scripts/auditar_cartel.py <ruta.png>

Salida: 05_Activos/el-gorila/carteles-s2/impreso/
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "05_Activos/el-gorila"
LOGO_SOGEM = ASSETS / "G/SOGEM50A.png"
OUT_DIR = ASSETS / "carteles-s2/impreso"

FOTO_HERO = ASSETS / "banco-fotos/feed-1x1/16.jpg"

TIPOGRAFIA = ASSETS / "tipografia"
FUENTE_PRIMARIA = TIPOGRAFIA / "primaria/CormorantGaramond-Bold.ttf"
FUENTE_SECUNDARIA = TIPOGRAFIA / "secundaria/Lato-Regular.ttf"
FUENTE_SECUNDARIA_BOLD = TIPOGRAFIA / "secundaria/Lato-Bold.ttf"

NEGRO = (10, 10, 10)
CREMA = (245, 240, 232)
DORADO = (201, 168, 76)
ROJO = (212, 58, 26)
GRIS_FINO = (120, 114, 102)

# Físico: 64cm ancho × 73cm alto. 300 DPI para impresión real; preview a escala.
ANCHO_CM, ALTO_CM = 64, 73
DPI_PRINT = 300


def _tamano(dpi):
    cm_a_in = 2.54
    return (round(ANCHO_CM / cm_a_in * dpi), round(ALTO_CM / cm_a_in * dpi))


FORMATOS = {
    "print": _tamano(DPI_PRINT),
    "preview": (1400, round(1400 * ALTO_CM / ANCHO_CM)),
}

INFO = {
    "titulo": "EL GORILA",
    "linea_info": "SÁBADOS 18:00H · TEATRO WILBERTO CANTÓN",
    "urgencia": "37 AÑOS EN CARTELERA · TEMPORADA EN CURSO",
    "cta": "elgorilateatro.com.mx",
    "creditos": (
        "Actuación y dirección: Humberto Dupeyrón  ·  Producción: Producciones Dupeyrón  ·  "
        "Música original: Odila Dupeyrón  ·  Duración: 1h 20min sin intermedio  ·  Clasificación +12"
    ),
}


def _verificar_assets():
    faltantes = [p for p in [FOTO_HERO, LOGO_SOGEM, FUENTE_PRIMARIA, FUENTE_SECUNDARIA] if not p.exists()]
    if faltantes:
        detalle = "\n".join(f"  - {p}" for p in faltantes)
        raise SystemExit(f"Faltan assets:\n{detalle}")


def cargar_foto_hero() -> Image.Image:
    return Image.open(FOTO_HERO).convert("RGB")


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
    s = h / FORMATOS["print"][1]
    cartel = Image.new("RGB", size, NEGRO)
    draw = ImageDraw.Draw(cartel)

    def linea(texto, y, font, fill, cx):
        bbox = draw.textbbox((0, 0), texto, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw / 2, y), texto, font=font, fill=fill)
        return altura_linea(font)

    # ============ Estructura C: columna central sobre eje, resto = aire ============
    cx = w // 2
    area_total = w * h

    zona_y0 = int(h * 0.15)
    zona_y1 = int(h * 0.85)
    zona_h = zona_y1 - zona_y0

    foto_side = int((area_total * 0.30) ** 0.5)
    foto_side = min(foto_side, int(zona_h * 0.56))
    marco_x0 = cx - foto_side // 2
    marco_x1 = marco_x0 + foto_side
    marco_y0 = zona_y0
    marco_y1 = marco_y0 + foto_side

    foto = cargar_foto_hero()
    # centering (0.5, 0.32): la foto de acción tiene el gesto/rostro en el tercio
    # superior — igual que el resto de piezas de esta toma (accion-IMG_7451-square).
    foto = ImageOps.fit(foto, (foto_side, foto_side), method=Image.LANCZOS, centering=(0.5, 0.32))
    cartel.paste(foto, (marco_x0, marco_y0))

    grosor = max(2, int(6 * s))
    draw.rectangle([marco_x0, marco_y0, marco_x1, marco_y1], outline=CREMA, width=grosor)

    # ============ Texto — presupuesto vertical del espacio que QUEDA ============
    ancho_titulo_max = int(w * 0.72)
    resto_h = zona_y1 - marco_y1

    presupuesto = {
        "gap1": 0.09, "titulo": 0.38, "gap2": 0.07,
        "info": 0.13, "gap3": 0.07, "urgencia": 0.12, "gap4": 0.05, "cta": 0.09,
    }

    def tam_desde_presupuesto(clave):
        return max(10, int(resto_h * presupuesto[clave] / 1.25))

    f_titulo = fuente_ajustada(INFO["titulo"], FUENTE_PRIMARIA, tam_desde_presupuesto("titulo"), ancho_titulo_max)
    f_info = fuente_ajustada(INFO["linea_info"], FUENTE_SECUNDARIA, tam_desde_presupuesto("info"), ancho_titulo_max)
    f_urgencia = fuente_ajustada(INFO["urgencia"], FUENTE_SECUNDARIA_BOLD, tam_desde_presupuesto("urgencia"), ancho_titulo_max)
    f_cta = fuente_ajustada(INFO["cta"], FUENTE_SECUNDARIA, tam_desde_presupuesto("cta"), ancho_titulo_max)

    y = marco_y1 + int(resto_h * presupuesto["gap1"])
    y += linea(INFO["titulo"], y, f_titulo, ROJO, cx)
    y += int(resto_h * presupuesto["gap2"])
    y += linea(INFO["linea_info"], y, f_info, CREMA, cx)
    y += int(resto_h * presupuesto["gap3"])
    y += linea(INFO["urgencia"], y, f_urgencia, DORADO, cx)
    y += int(resto_h * presupuesto["gap4"])
    linea(INFO["cta"], y, f_cta, DORADO, cx)

    # ============ Letra chica real — créditos, DENTRO del margen inferior ============
    f_creditos = fuente_ajustada(INFO["creditos"], FUENTE_SECUNDARIA, int(30 * s), int(w * 0.82))
    y_creditos = zona_y1 + (h - zona_y1 - altura_linea(f_creditos)) // 2
    linea(INFO["creditos"], y_creditos, f_creditos, GRIS_FINO, cx)

    if LOGO_SOGEM.exists():
        logo = Image.open(LOGO_SOGEM).convert("RGBA")
        logo_w = int(w * 0.07)
        logo.thumbnail((logo_w, logo_w), Image.LANCZOS)
        cartel.paste(
            logo,
            (w - int(w * 0.05) - logo.width, h - int(h * 0.03) - logo.height),
            logo,
        )

    return cartel


def main():
    _verificar_assets()
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", choices=["print", "preview"], help="generar solo un tamaño")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    formatos = {args.solo: FORMATOS[args.solo]} if args.solo else FORMATOS

    for nombre, size in formatos.items():
        print(f"Generando {nombre} ({size[0]}x{size[1]})...")
        cartel = construir(size)
        out = OUT_DIR / f"cartel-ticketmaster-64x73cm-{nombre}.png"
        cartel.save(out)
        print(f"  {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
