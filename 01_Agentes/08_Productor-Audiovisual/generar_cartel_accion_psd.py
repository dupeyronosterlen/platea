#!/usr/bin/env python3
"""
Boceto PSD editable — Estilo Acción / Tono 3 "El Drama" (campaña Google)
Agente: 08 Productor Audiovisual. Hermano de generar_cartel_accion.py (mismo
diseño) y de generar_cartel_psd.py (misma técnica de capas PSD) — ver ese
archivo para el detalle de los 2 bugs de pytoshop ya parcheados aquí igual.

Entrega capas separadas: Foto, Overlay (oscurecimiento), Badge 37 años,
"EL" (crema), "GORILA" (rojo cursiva), Reparto, Referencia — para que Dirección las
mueva/edite en Photoshop sin tener que regenerar desde cero.

Texto rasterizado en su propia capa transparente (no es texto vivo de
Photoshop — ver nota en generar_cartel_psd.py sobre por qué).

Requiere el disco de producción montado en /Volumes/La Mancha/Elgorila.

Uso:
    python3 generar_cartel_accion_psd.py                      # square + landscape, escala 2x
    python3 generar_cartel_accion_psd.py --solo square --scale 1

Salida: 05_Activos/el-gorila/carteles-s2/accion/*.psd
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pytoshop import enums
from pytoshop.user import nested_layers

import packbits as _packbits
from pytoshop import codecs as _pytoshop_codecs

_pytoshop_codecs.packbits = _packbits

REPO = Path(__file__).resolve().parents[2]
DRIVE = Path("/Volumes/La Mancha/Elgorila/4. Publicidad")
OUT_DIR = REPO / "05_Activos/el-gorila/carteles-s2/accion"

FOTOS_DIR = DRIVE / "99. Assets RAW/Fotos/ESTUDIO"
BADGE_37 = DRIVE / "13. Elementos Gráficos/badges/37Anos.png"

TIPOGRAFIA = REPO / "05_Activos/el-gorila/tipografia"
FUENTE_PRIMARIA = TIPOGRAFIA / "primaria/CormorantGaramond-Bold.ttf"
FUENTE_PRIMARIA_ITALIC = TIPOGRAFIA / "primaria/CormorantGaramond-Italic.ttf"
FUENTE_SECUNDARIA = TIPOGRAFIA / "secundaria/Lato-Regular.ttf"

NEGRO = (10, 7, 6)
CREMA = (242, 237, 228)
ROJO = (212, 58, 26)

FOTO_DEFAULT = "IMG_7451.jpg"

FORMATOS_BASE = {
    "square": (1200, 1200),
    "landscape": (1200, 628),
}

INFO = {
    "titulo_el": "EL",
    "titulo_gorila": "GORILA",
    "cast": "con Humberto Dupeyrón",
    "referencia": "basado en «Informe para una Academia» de Franz Kafka",
}


def _verificar_disco(foto_path):
    faltantes = [p for p in [foto_path, BADGE_37, FUENTE_PRIMARIA, FUENTE_SECUNDARIA] if not p.exists()]
    if faltantes:
        detalle = "\n".join(f"  - {p}" for p in faltantes)
        raise SystemExit(f"Falta montar el disco de producción (La Mancha). No se encontró:\n{detalle}")


def altura_linea(font):
    a, d = font.getmetrics()
    return a + d


def fuente_ajustada(texto, ruta_fuente, tam_deseado, ancho_max, tam_min=10):
    tam = tam_deseado
    while tam > tam_min:
        f = ImageFont.truetype(str(ruta_fuente), tam)
        if f.getlength(texto) <= ancho_max:
            return f
        tam -= max(1, int(tam * 0.05))
    return ImageFont.truetype(str(ruta_fuente), tam_min)


def capa_texto(texto, font, color) -> Image.Image:
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
        preview.alpha_composite(im, (left, top))
    arr = np.array(im)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    return nested_layers.Image(
        name=nombre, top=top, left=left, bottom=top + im.height, right=left + im.width,
        channels={0: r, 1: g, 2: b, -1: a},
    )


def construir_capas(foto_path, size):
    w, h = size
    s = h / 1200

    capas = []
    preview = Image.open(foto_path).convert("RGB")
    preview = ImageOps.fit(preview, (w, h), method=Image.LANCZOS, centering=(0.5, 0.28)).convert("RGBA")

    # -------- Foto (capa completa, ocupa todo el lienzo — Estilo Acción "a sangre") --------
    foto = Image.open(foto_path).convert("RGB")
    foto = ImageOps.fit(foto, (w, h), method=Image.LANCZOS, centering=(0.5, 0.28))
    capas.append(imagen_a_capa("Foto — a sangre", foto, 0, 0))

    # -------- Overlay de oscurecimiento (capa aparte, opacidad ajustable en PS) --------
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    zona_texto_y0 = int(h * 0.58)
    pasos = 40
    for i in range(pasos):
        y0 = zona_texto_y0 + int((h - zona_texto_y0) * i / pasos)
        y1 = zona_texto_y0 + int((h - zona_texto_y0) * (i + 1) / pasos)
        t = i / pasos
        alpha = int(180 * min(1.0, t * 1.6))
        draw_ov.rectangle([0, y0, w, y1], fill=(*NEGRO, alpha))
    capas.append(imagen_a_capa("Overlay oscurecimiento", overlay, 0, 0, preview))

    # -------- Badge 37 años --------
    badge_src = Image.open(BADGE_37).convert("RGB")
    alpha = badge_src.convert("L").point(lambda v: min(255, int(v * 1.6)))
    badge = badge_src.copy()
    badge.putalpha(alpha)
    badge_w = int(w * 0.11)
    badge.thumbnail((badge_w, badge_w), Image.LANCZOS)
    bx, by = w - badge.width - int(24 * s), int(24 * s)
    capas.append(imagen_a_capa("Badge 37 años", badge, bx, by, preview))

    # -------- Texto: título en 2 capas (EL crema / GORILA rojo cursiva) + reparto + referencia --------
    ancho_max = int(w * 0.88)
    cx = w // 2

    f_titulo = fuente_ajustada(INFO["titulo_el"] + " " + INFO["titulo_gorila"], FUENTE_PRIMARIA, int(220 * s), ancho_max)
    f_gorila = ImageFont.truetype(str(FUENTE_PRIMARIA_ITALIC), f_titulo.size)
    f_cast = fuente_ajustada(INFO["cast"], FUENTE_SECUNDARIA, int(56 * s), ancho_max)
    f_ref = fuente_ajustada(INFO["referencia"], FUENTE_PRIMARIA_ITALIC, int(46 * s), ancho_max)

    im_el = capa_texto(INFO["titulo_el"] + " ", f_titulo, CREMA)
    im_gorila = capa_texto(INFO["titulo_gorila"], f_gorila, ROJO)
    im_cast = capa_texto(INFO["cast"], f_cast, CREMA)
    im_ref = capa_texto(INFO["referencia"], f_ref, CREMA)

    bloque_alto = im_el.height + int(20 * s) + im_cast.height + int(14 * s) + im_ref.height
    y = h - int(40 * s) - bloque_alto

    total_titulo_w = im_el.width + im_gorila.width
    x_el = cx - total_titulo_w // 2
    capas.append(imagen_a_capa("Título — EL", im_el, x_el, y, preview))
    capas.append(imagen_a_capa("Título — GORILA", im_gorila, x_el + im_el.width, y, preview))
    y += im_el.height + int(20 * s)

    capas.append(imagen_a_capa("Reparto", im_cast, cx - im_cast.width // 2, y, preview))
    y += im_cast.height + int(14 * s)

    capas.append(imagen_a_capa("Referencia Kafka", im_ref, cx - im_ref.width // 2, y, preview))

    return capas, (w, h), preview.convert("RGB")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--foto", default=FOTO_DEFAULT)
    parser.add_argument("--solo", choices=list(FORMATOS_BASE.keys()))
    parser.add_argument("--scale", type=int, default=2, help="multiplicador de resolución (default 2x para dar margen de edición)")
    args = parser.parse_args()

    foto_path = FOTOS_DIR / args.foto
    _verificar_disco(foto_path)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    formatos = {args.solo: FORMATOS_BASE[args.solo]} if args.solo else FORMATOS_BASE
    stem = Path(args.foto).stem

    for nombre, (bw, bh) in formatos.items():
        size = (bw * args.scale, bh * args.scale)
        print(f"Generando {nombre} @ {args.scale}x ({size[0]}x{size[1]})...")
        capas, psd_size, preview = construir_capas(foto_path, size)
        for c in capas:
            print(f"  - {c.name}  ({c.right - c.left}x{c.bottom - c.top}px @ {c.left},{c.top})")

        preview_out = OUT_DIR / f"accion-{stem}-{nombre}-QA-preview.png"
        preview.save(preview_out)

        psd = nested_layers.nested_layers_to_psd(
            capas, color_mode=enums.ColorMode.rgb, size=psd_size, depth=enums.ColorDepth.depth8
        )
        out = OUT_DIR / f"accion-{stem}-{nombre}.psd"
        with open(out, "wb") as fh:
            psd.write(fh)
        print(f"  Guardado: {out.relative_to(REPO)} ({out.stat().st_size / 1e6:.1f} MB)")
        print(f"  QA preview: {preview_out.relative_to(REPO)}\n")


if __name__ == "__main__":
    main()
