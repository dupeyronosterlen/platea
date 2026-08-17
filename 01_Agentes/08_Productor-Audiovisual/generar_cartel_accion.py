#!/usr/bin/env python3
"""
Estilo Acción / Tono 3 "El Drama" — cartel para campaña de Google (awareness)
Agente: 08 Productor Audiovisual.

Activa dos documentos de identidad que ya existían pero nunca se habían conectado
a un script (ver memory/reference_sistema_visual_carteles.md):
  - Estilo 2 "Acción" (4. Publicidad/15. Guía de Diseño/estilos-visuales.md, disco):
    foto a sangre + overlay + texto directo encima. Sin marcos, sin columnas.
  - Tono 3 "El Drama" (03_Producciones/el-gorila/tonos-visuales.md, 9 jun 2026 —
    LA fuente de identidad más oficial): fondo negro, SOLO rojo #D43A1A de acento
    (nada de dorado), Cormorant Garamond, "una frase + un retrato", para awareness/frío.

Pedido de Dirección (16 jul 2026): foto del actor grande y bien encuadrada, con el mínimo
de texto posible encima — "EL GORILA" / "con Humberto Dupeyrón" / referencia a
Kafka — nada de fecha/precio (esto es awareness, no venta directa; para venta
directa ya existe generar_carteles.py con Tono 2 "Invitación").

Regla de IA (ver skill cartel-diseno-teoria): la foto real NUNCA se toca — solo se
recorta (crop, sin regenerar) y se le pone un overlay de oscurecimiento programático
para que el texto se lea, que es distinto de "modificar la foto".

Requiere el disco de producción montado en /Volumes/La Mancha/Elgorila.

Uso:
    python3 generar_cartel_accion.py                    # todos los formatos
    python3 generar_cartel_accion.py --foto IMG_7451.jpg --solo square

Salida: 05_Activos/el-gorila/carteles-s2/accion/
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registro_piezas import registrar_pieza

REPO = Path(__file__).resolve().parents[2]
DRIVE = Path("/Volumes/La Mancha/Elgorila/4. Publicidad")
OUT_DIR = REPO / "05_Activos/el-gorila/carteles-s2/accion"

FOTOS_DIR = DRIVE / "99. Assets RAW/Fotos/ESTUDIO"
BADGE_37 = DRIVE / "13. Elementos Gráficos/badges/37Anos.png"

TIPOGRAFIA = REPO / "05_Activos/el-gorila/tipografia"
FUENTE_PRIMARIA = TIPOGRAFIA / "primaria/CormorantGaramond-Bold.ttf"
FUENTE_PRIMARIA_ITALIC = TIPOGRAFIA / "primaria/CormorantGaramond-Italic.ttf"
FUENTE_SECUNDARIA = TIPOGRAFIA / "secundaria/Lato-Regular.ttf"

# Tono 3 "El Drama" — tonos-visuales.md: fondo negro, SOLO rojo de acento, sin dorado.
NEGRO = (10, 7, 6)
CREMA = (242, 237, 228)
ROJO = (212, 58, 26)

FOTO_DEFAULT = "IMG_7451.jpg"

FORMATOS = {
    "square": (1200, 1200),      # Google Responsive Display — cuadrado
    "landscape": (1200, 628),    # Google Responsive Display — horizontal
    "story": (1080, 1920),       # reusable en Meta/orgánico si hace falta
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


def cargar_badge_37(w):
    badge = Image.open(BADGE_37).convert("RGB")
    alpha = badge.convert("L").point(lambda v: min(255, int(v * 1.6)))
    badge_rgba = badge.copy()
    badge_rgba.putalpha(alpha)
    badge_w = int(w * 0.11)
    badge_rgba.thumbnail((badge_w, badge_w), Image.LANCZOS)
    return badge_rgba


def recorte_a_sangre(foto: Image.Image, size, foco_y=0.28) -> Image.Image:
    """Recorta a sangre anclando el punto de interés (el rostro) a una fracción
    FIJA de la altura de la foto ORIGINAL — no de centering=(x,y) de ImageOps.fit,
    que ancla relativo al recorte ya hecho y por eso da resultados distintos según
    el aspect ratio del formato de salida (bug real: en 1200x628, el recorte es una
    franja tan delgada que centering=0.28 aterrizaba en el cuello, no en la cara,
    aunque ese mismo valor funcionaba bien en el cuadrado). Con foco_y fijo sobre
    la imagen completa, la cara queda en el mismo lugar sin importar el formato."""
    w, h = size
    sw, sh = foto.size
    target_ratio = w / h
    if sw / sh > target_ratio:
        crop_h = sh
        crop_w = int(sh * target_ratio)
    else:
        crop_w = sw
        crop_h = int(sw / target_ratio)

    crop_top = int(foco_y * sh - crop_h / 2)
    crop_top = max(0, min(crop_top, sh - crop_h))
    crop_left = max(0, min((sw - crop_w) // 2, sw - crop_w))

    recorte = foto.crop((crop_left, crop_top, crop_left + crop_w, crop_top + crop_h))
    return recorte.resize((w, h), Image.LANCZOS)


def construir(foto_path: Path, size, foco_y=0.28) -> Image.Image:
    w, h = size
    s = h / 1200  # escala de referencia

    # --- foto a sangre, sin márgenes, sin recorte/retoque de contenido ---
    foto = Image.open(foto_path).convert("RGB")
    foto = recorte_a_sangre(foto, (w, h), foco_y)
    cartel = foto.convert("RGBA")

    # --- overlay oscuro pesado en el tercio inferior (zona de texto), no la foto entera ---
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    zona_texto_y0 = int(h * 0.58)
    pasos = 40
    for i in range(pasos):
        y0 = zona_texto_y0 + int((h - zona_texto_y0) * i / pasos)
        y1 = zona_texto_y0 + int((h - zona_texto_y0) * (i + 1) / pasos)
        t = i / pasos
        alpha = int(180 * min(1.0, t * 1.6))  # rampa hasta ~70% negro
        draw_ov.rectangle([0, y0, w, y1], fill=(*NEGRO, alpha))
    cartel = Image.alpha_composite(cartel, overlay)
    draw = ImageDraw.Draw(cartel)

    # --- badge 37 años, esquina superior — único elemento fuera de la zona de texto ---
    badge = cargar_badge_37(w)
    cartel.paste(badge, (w - badge.width - int(24 * s), int(24 * s)), badge)

    # --- texto: SOLO título + reparto + referencia. Nada de fecha/precio (Tono 3 = awareness) ---
    ancho_max = int(w * 0.88)
    cx = w // 2

    f_titulo = fuente_ajustada(INFO["titulo_el"] + " " + INFO["titulo_gorila"], FUENTE_PRIMARIA, int(220 * s), ancho_max)
    f_cast = fuente_ajustada(INFO["cast"], FUENTE_SECUNDARIA, int(56 * s), ancho_max)
    f_ref = fuente_ajustada(INFO["referencia"], FUENTE_PRIMARIA_ITALIC, int(46 * s), ancho_max)

    def linea_dos_colores(y):
        """'EL' en crema, 'GORILA' en rojo cursiva — el tratamiento que pide
        tonos-visuales.md Tono 3 ('Gorila en cursiva roja')."""
        f_el = f_titulo
        f_gorila_italic = ImageFont.truetype(str(FUENTE_PRIMARIA_ITALIC), f_titulo.size)
        w_el = draw.textlength(INFO["titulo_el"] + " ", font=f_el)
        w_gorila = draw.textlength(INFO["titulo_gorila"], font=f_gorila_italic)
        total = w_el + w_gorila
        x = cx - total / 2
        draw.text((x, y), INFO["titulo_el"] + " ", font=f_el, fill=(*CREMA, 255))
        draw.text((x + w_el, y), INFO["titulo_gorila"], font=f_gorila_italic, fill=(*ROJO, 255))
        return altura_linea(f_el)

    def linea(texto, y, font, color):
        tw = draw.textlength(texto, font=font)
        draw.text((cx - tw / 2, y), texto, font=font, fill=(*color, 255))
        return altura_linea(font)

    bloque_alto = altura_linea(f_titulo) + int(20 * s) + altura_linea(f_cast) + int(14 * s) + altura_linea(f_ref)
    y = h - int(40 * s) - bloque_alto

    y += linea_dos_colores(y)
    y += int(20 * s)
    y += linea(INFO["cast"], y, f_cast, CREMA)
    y += int(14 * s)
    linea(INFO["referencia"], y, f_ref, CREMA)

    return cartel.convert("RGB")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--foto", default=FOTO_DEFAULT)
    parser.add_argument("--solo", choices=list(FORMATOS.keys()))
    parser.add_argument("--foco-y", type=float, default=0.28, help="fracción de la altura ORIGINAL de la foto donde está la cara (0=arriba, 1=abajo)")
    args = parser.parse_args()

    foto_path = FOTOS_DIR / args.foto
    _verificar_disco(foto_path)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    formatos = {args.solo: FORMATOS[args.solo]} if args.solo else FORMATOS
    stem = Path(args.foto).stem

    for nombre, size in formatos.items():
        print(f"Generando {nombre} ({size[0]}x{size[1]})...")
        cartel = construir(foto_path, size, args.foco_y)
        out = OUT_DIR / f"accion-{stem}-{nombre}.png"
        cartel.save(out)
        print(f"  {out.relative_to(REPO)}")

        registrar_pieza(
            script="generar_cartel_accion.py",
            archivo=str(out.relative_to(REPO)),
            foto_fuente=args.foto,
            formato=nombre,
            tono_visual="Drama",
            categoria="A",
            copy_titulo=f"{INFO['titulo_el']} {INFO['titulo_gorila']}",
            copy_secundario=f"{INFO['cast']} · {INFO['referencia']}",
            registro="DRAMA",
            canal_destino="Google Ads",
        )


if __name__ == "__main__":
    main()
