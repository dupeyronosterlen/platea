#!/usr/bin/env python3
"""
Generador de boceto PSD — cartel de calle 140 x 197.5 cm (formato ~A0, 1:√2)
Agente: 08 Productor Audiovisual. Sigue .claude/skills/cartel-diseno-teoria/
(Estructura C — Minimalismo Áureo, la misma lógica aprobada para el cartel
2.5x1.5m: foto + título sobre el eje central, resto = espacio negativo real).

Este script NO entrega un cartel terminado — entrega un .psd con CAPAS
SEPARADAS y EDITABLES (fondo, foto, marco, título, info, créditos, logos)
para que Dirección lo termine de ajustar directamente en Photoshop.

Importante sobre las capas de texto: son texto RASTERIZADO en su propia capa
transparente (no capas de tipo "Texto" vivas de Photoshop — generar esas
correctamente desde cero es frágil y con alto riesgo de corromper el archivo).
Se puede reemplazar cada capa de texto con una capa de tipo real en Photoshop
usando la misma posición/tamaño como guía.

Requiere: pip install pytoshop (ver requirements más abajo)
Requiere el disco de producción montado en /Volumes/La Mancha/Elgorila.

Uso:
    python3 generar_cartel_psd.py
    python3 generar_cartel_psd.py --dpi 150   # default 150

Salida: 05_Activos/el-gorila/carteles-s2/impreso/cartel-calle-140x197.5cm.psd
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pytoshop import enums
from pytoshop.user import nested_layers

# pytoshop 1.2.1 tiene un bug real: codecs.py hace `from . import packbits`
# (un submódulo compilado que no viene incluido en el paquete de PyPI) y traga
# el ImportError en silencio, así que la compresión RLE truena en tiempo de
# ejecución con NameError. El paquete "packbits" de PyPI (pip install packbits)
# expone la misma API (encode/decode) — se inyecta a mano donde pytoshop lo
# esperaba encontrar.
import packbits as _packbits
from pytoshop import codecs as _pytoshop_codecs

_pytoshop_codecs.packbits = _packbits

REPO = Path(__file__).resolve().parents[2]
DRIVE = Path("/Volumes/La Mancha/Elgorila/4. Publicidad")
LOGO_SOGEM = REPO / "05_Activos/el-gorila/G/SOGEM50A.png"
OUT_DIR = REPO / "05_Activos/el-gorila/carteles-s2/impreso"

FOTO_HERO = DRIVE / "99. Assets RAW/Fotos/ESTUDIO/IMG_7451.jpg"
BADGE_37 = DRIVE / "13. Elementos Gráficos/badges/37Anos.png"

TIPOGRAFIA = REPO / "05_Activos/el-gorila/tipografia"
FUENTE_PRIMARIA = TIPOGRAFIA / "primaria/CormorantGaramond-Bold.ttf"
FUENTE_SECUNDARIA = TIPOGRAFIA / "secundaria/Lato-Regular.ttf"
FUENTE_SECUNDARIA_BOLD = TIPOGRAFIA / "secundaria/Lato-Bold.ttf"

NEGRO = (10, 10, 10)
CREMA = (245, 240, 232)
DORADO = (201, 168, 76)
ROJO = (212, 58, 26)
GRIS_FINO = (120, 114, 102)

ANCHO_CM = 140.0
ALTO_CM = 197.5

INFO = {
    "titulo": "EL GORILA",
    "linea_info": "ESTRENO 25 DE JULIO · TEATRO WILBERTO CANTÓN",
    "cta": "elgorilateatro.com.mx",
    "precio": "Preventa $350 · Estudiantes/INAPAM $245",
    "creditos": (
        "Actuación y dirección: Humberto Dupeyrón  ·  Producción: Producciones Dupeyrón  ·  "
        "Música original: Odila Dupeyrón  ·  Duración: 1h 20min sin intermedio  ·  Clasificación +12"
    ),
}


def cm_a_px(cm, dpi):
    return round(cm / 2.54 * dpi)


def _verificar_disco():
    faltantes = [p for p in [FOTO_HERO, BADGE_37, FUENTE_PRIMARIA, FUENTE_SECUNDARIA] if not p.exists()]
    if faltantes:
        detalle = "\n".join(f"  - {p}" for p in faltantes)
        raise SystemExit(f"Falta montar el disco de producción (La Mancha). No se encontró:\n{detalle}")


def fuente_ajustada(texto, ruta_fuente, tam_deseado, ancho_max, tam_min=10):
    tam = tam_deseado
    while tam > tam_min:
        f = ImageFont.truetype(str(ruta_fuente), tam)
        if f.getlength(texto) <= ancho_max:
            return f
        tam -= max(1, int(tam * 0.05))
    return ImageFont.truetype(str(ruta_fuente), tam_min)


def altura_linea(font):
    a, d = font.getmetrics()
    return a + d


def capa_texto(texto, font, color) -> Image.Image:
    """Renderiza SOLO el texto sobre fondo transparente, recortado a su
    bounding box — así la capa PSD resultante es del tamaño del texto, no del
    lienzo completo (práctica estándar de capas en Photoshop)."""
    tmp = Image.new("RGBA", (10, 10))
    draw_tmp = ImageDraw.Draw(tmp)
    bbox = draw_tmp.textbbox((0, 0), texto, font=font)
    pad = 6
    w = bbox[2] - bbox[0] + pad * 2
    h = bbox[3] - bbox[1] + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.text((pad - bbox[0], pad - bbox[1]), texto, font=font, fill=(*color, 255))
    return im


def imagen_a_capa(nombre, im: Image.Image, left, top, preview=None) -> nested_layers.Image:
    im = im.convert("RGBA")
    if preview is not None:
        preview.paste(im, (left, top), im)
    arr = np.array(im)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    return nested_layers.Image(
        name=nombre,
        top=top,
        left=left,
        bottom=top + im.height,
        right=left + im.width,
        channels={0: r, 1: g, 2: b, -1: a},
    )


def construir_capas(dpi):
    w = cm_a_px(ANCHO_CM, dpi)
    h = cm_a_px(ALTO_CM, dpi)
    s = h / 11663  # escala de referencia sobre 150dpi/197.5cm

    capas = []
    preview = Image.new("RGB", (w, h), NEGRO)  # composite plano, solo para QA visual rápida

    # -------- Fondo --------
    fondo = Image.new("RGB", (w, h), NEGRO)
    capas.append(imagen_a_capa("Fondo", fondo, 0, 0, preview))

    # -------- Foto (Estructura C: ~30% del área del lienzo) --------
    cx = w // 2
    zona_y0 = int(h * 0.12)
    zona_y1 = int(h * 0.86)
    zona_h = zona_y1 - zona_y0

    foto_side = int((w * h * 0.32) ** 0.5)
    foto_side = min(foto_side, int(w * 0.86), int(zona_h * 0.52))
    marco_x0 = cx - foto_side // 2
    marco_y0 = zona_y0

    foto_full = Image.open(FOTO_HERO).convert("RGB")
    foto = ImageOps.fit(foto_full, (foto_side, foto_side), method=Image.LANCZOS, centering=(0.5, 0.35))
    capas.append(imagen_a_capa("Foto — IMG_7451 (ESTUDIO)", foto, marco_x0, marco_y0, preview))

    # marco (rectángulo, capa aparte para poder cambiar grosor/color fácil)
    grosor = max(2, int(6 * s))
    marco_im = Image.new("RGBA", (foto_side, foto_side), (0, 0, 0, 0))
    ImageDraw.Draw(marco_im).rectangle([0, 0, foto_side - 1, foto_side - 1], outline=(*CREMA, 255), width=grosor)
    capas.append(imagen_a_capa("Marco foto", marco_im, marco_x0, marco_y0, preview))

    # badge 37 años
    badge_src = Image.open(BADGE_37).convert("RGB")
    alpha = badge_src.convert("L").point(lambda v: min(255, int(v * 1.6)))
    badge = badge_src.copy()
    badge.putalpha(alpha)
    badge_w = int(w * 0.09)
    badge.thumbnail((badge_w, badge_w), Image.LANCZOS)
    badge_x = marco_x0 + foto_side - badge.width - int(20 * s)
    badge_y = marco_y0 + int(20 * s)
    capas.append(imagen_a_capa("Badge 37 años", badge, badge_x, badge_y, preview))

    marco_y1 = marco_y0 + foto_side

    # -------- Bloque de texto — presupuesto vertical del espacio restante --------
    ancho_titulo_max = int(w * 0.86)
    resto_h = zona_y1 - marco_y1
    presupuesto = {
        "gap1": 0.08, "titulo": 0.40, "gap2": 0.06,
        "info": 0.12, "gap3": 0.05, "precio": 0.10, "gap4": 0.04, "cta": 0.09,
    }

    def tam(clave):
        return max(10, int(resto_h * presupuesto[clave] / 1.25))

    f_titulo = fuente_ajustada(INFO["titulo"], FUENTE_PRIMARIA, tam("titulo"), ancho_titulo_max)
    f_info = fuente_ajustada(INFO["linea_info"], FUENTE_SECUNDARIA, tam("info"), ancho_titulo_max)
    f_precio = fuente_ajustada(INFO["precio"], FUENTE_SECUNDARIA_BOLD, tam("precio"), ancho_titulo_max)
    f_cta = fuente_ajustada(INFO["cta"], FUENTE_SECUNDARIA, tam("cta"), ancho_titulo_max)

    y = marco_y1 + int(resto_h * presupuesto["gap1"])

    for nombre, texto, font, color, gap_key in [
        ("Título", INFO["titulo"], f_titulo, ROJO, "gap2"),
        ("Info evento", INFO["linea_info"], f_info, CREMA, "gap3"),
        ("Precio", INFO["precio"], f_precio, DORADO, "gap4"),
        ("CTA web", INFO["cta"], f_cta, DORADO, None),
    ]:
        capa_im = capa_texto(texto, font, color)
        left = cx - capa_im.width // 2
        capas.append(imagen_a_capa(nombre, capa_im, left, y, preview))
        y += capa_im.height
        if gap_key:
            y += int(resto_h * presupuesto[gap_key])

    # -------- Créditos técnicos — letra chica, dentro del margen inferior --------
    f_creditos = fuente_ajustada(INFO["creditos"], FUENTE_SECUNDARIA, int(34 * s), int(w * 0.8))
    creditos_im = capa_texto(INFO["creditos"], f_creditos, GRIS_FINO)
    y_creditos = zona_y1 + (h - zona_y1 - creditos_im.height) // 2
    capas.append(imagen_a_capa("Créditos técnicos", creditos_im, cx - creditos_im.width // 2, y_creditos, preview))

    # -------- Logo SOGEM --------
    if LOGO_SOGEM.exists():
        logo = Image.open(LOGO_SOGEM).convert("RGBA")
        logo_w = int(w * 0.07)
        logo.thumbnail((logo_w, logo_w), Image.LANCZOS)
        lx = w - int(w * 0.05) - logo.width
        ly = h - int(h * 0.025) - logo.height
        capas.append(imagen_a_capa("Logo SOGEM", logo, lx, ly, preview))

    return capas, (w, h), preview


def main():
    _verificar_disco()
    parser = argparse.ArgumentParser()
    parser.add_argument("--dpi", type=int, default=150)
    args = parser.parse_args()

    ancho_px = cm_a_px(ANCHO_CM, args.dpi)
    alto_px = cm_a_px(ALTO_CM, args.dpi)
    print(f"Lienzo: {ANCHO_CM}cm x {ALTO_CM}cm @ {args.dpi}dpi = {ancho_px}x{alto_px}px")

    capas, size, preview = construir_capas(args.dpi)
    print(f"{len(capas)} capas:")
    for c in capas:
        print(f"  - {c.name}  ({c.right - c.left}x{c.bottom - c.top}px @ {c.left},{c.top})")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    preview_out = OUT_DIR / "cartel-calle-140x197.5cm-QA-preview.png"
    preview.save(preview_out)
    print(f"Preview de QA (composite plano, revisar ANTES de abrir el PSD): {preview_out.relative_to(REPO)}")

    psd = nested_layers.nested_layers_to_psd(
        capas, color_mode=enums.ColorMode.rgb, size=size, depth=enums.ColorDepth.depth8
    )

    out = OUT_DIR / "cartel-calle-140x197.5cm.psd"
    with open(out, "wb") as fh:
        psd.write(fh)
    print(f"Guardado: {out.relative_to(REPO)} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
