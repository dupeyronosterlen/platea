#!/usr/bin/env python3
"""
Categoría A — Teaser / poca info (Ag-08).

Máximo 3 bloques de texto. Sin precio, sin venue completo, sin sinopsis.
Layout: minimalismo (estructura C de cartel-diseno-teoria §0 + §2bis).

Uso:
  python3 generar_cartel_teaser.py --frase "37 años. Misma jaula."
  python3 generar_cartel_teaser.py --frase "Kafka en esmoquin." --foto 24.png --formato story
  python3 generar_cartel_teaser.py --solo-titulo --ancla "con Humberto Dupeyrón"

Salida: 05_Activos/el-gorila/carteles-s2/teaser/
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
FOTOS_DIR = REPO / "07_CartelesPeter/public/assets/photos/personaje-aislado"
OUT_DIR = REPO / "05_Activos/el-gorila/carteles-s2/teaser"

NEGRO = (10, 7, 6)
ROJO = (212, 58, 26)
CREMA = (242, 237, 228)
DORADO = (212, 175, 55)

FUENTE_DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
FUENTE_BASKERVILLE = "/System/Library/Fonts/Supplemental/Baskerville.ttc"

FORMATOS = {
    "feed": (1080, 1350),    # 4:5
    "square": (1080, 1080),  # 1:1
    "story": (1080, 1920),   # 9:16
}

TITULO = "EL GORILA"
WEB = "elgorilateatro.com.mx"


def _slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9áéíóúñü]+", "-", s, flags=re.I)
    return s.strip("-")[:48] or "teaser"


def cargar_foto(nombre: str) -> Image.Image:
    ruta = FOTOS_DIR / nombre
    if not ruta.exists():
        raise SystemExit(f"No existe foto: {ruta}")
    foto = Image.open(ruta).convert("RGBA")
    bbox = foto.getbbox()
    if bbox:
        foto = foto.crop(bbox)
    r, g, b, a = foto.split()
    a = a.filter(ImageFilter.GaussianBlur(2))
    rgb = ImageOps.autocontrast(Image.merge("RGB", (r, g, b)), cutoff=1)
    rgb.putalpha(a)
    return rgb


def texto_centrado(draw, texto, y, font, fill, canvas_w):
    bbox = draw.textbbox((0, 0), texto, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((canvas_w - tw) / 2, y), texto, font=font, fill=fill)
    return th


def wrap_frase(texto: str, font, max_w: int, draw) -> list[str]:
    words = texto.split()
    if not words:
        return []
    lines, cur = [], words[0]
    for w in words[1:]:
        trial = f"{cur} {w}"
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    # máx 2 líneas — si no cabe, el agente debe acortar la frase
    if len(lines) > 2:
        raise SystemExit(
            f"Frase demasiado larga para teaser ({len(lines)} líneas). "
            "Máximo ~8 palabras / 2 líneas. Acorta --frase."
        )
    return lines


def construir(
    *,
    frase: str | None,
    solo_titulo: bool,
    ancla: str | None,
    con_web: bool,
    foto_name: str,
    size: tuple[int, int],
) -> Image.Image:
    """Máximo 3 bloques: dominante + ancla + web opcional."""
    w, h = size
    cartel = Image.new("RGB", size, NEGRO)

    foto = cargar_foto(foto_name)
    # foto grande, centrada arriba — ~55-60% del alto útil
    max_w, max_h = int(w * 0.88), int(h * 0.58)
    foto.thumbnail((max_w, max_h), Image.LANCZOS)
    fx = (w - foto.width) // 2
    fy = int(h * 0.08)
    cartel.paste(foto, (fx, fy), foto)

    draw = ImageDraw.Draw(cartel)
    s = h / 1350

    # Bloque tipográfico abajo — aire generoso
    y = int(h * 0.68)

    if solo_titulo or not frase:
        f_titulo = ImageFont.truetype(FUENTE_DIDOT, max(56, int(110 * s)))
        y += texto_centrado(draw, TITULO, y, f_titulo, ROJO, w)
        dominante_ok = True
    else:
        f_frase = ImageFont.truetype(FUENTE_DIDOT, max(36, int(52 * s)))
        lines = wrap_frase(frase, f_frase, int(w * 0.82), draw)
        for line in lines:
            y += texto_centrado(draw, line, y, f_frase, CREMA, w)
            y += int(10 * s)
        dominante_ok = True

    bloques = 1 if dominante_ok else 0

    if ancla:
        y += int(28 * s)
        f_ancla = ImageFont.truetype(FUENTE_BASKERVILLE, max(18, int(28 * s)))
        y += texto_centrado(draw, ancla, y, f_ancla, DORADO, w)
        bloques += 1

    if con_web:
        y += int(36 * s)
        f_web = ImageFont.truetype(FUENTE_BASKERVILLE, max(14, int(22 * s)))
        texto_centrado(draw, WEB, y, f_web, CREMA, w)
        bloques += 1

    if bloques > 3:
        raise SystemExit(
            f"Gate: {bloques} bloques de texto (máx 3). "
            "Quita --ancla o pasa --no-web."
        )

    return cartel


def main():
    p = argparse.ArgumentParser(description="Teaser Categoría A — poca info")
    p.add_argument("--frase", help="Frase dominante (≤8 palabras). Si omites, usa título.")
    p.add_argument("--solo-titulo", action="store_true", help="Dominante = EL GORILA")
    p.add_argument("--ancla", default=None, help='Un solo dato, ej. "37 años en escena"')
    p.add_argument("--no-web", action="store_true", help="Omite el bloque web")
    p.add_argument("--foto", default="20.png", help="Archivo en personaje-aislado/")
    p.add_argument(
        "--formato",
        choices=list(FORMATOS) + ["all"],
        default="feed",
        help="feed 4:5 · square 1:1 · story 9:16 · all",
    )
    args = p.parse_args()

    if not args.frase and not args.solo_titulo:
        args.solo_titulo = True

    # Default ancla suave si no hay frase (título solo se siente vacío)
    ancla = args.ancla
    if ancla is None and args.solo_titulo and not args.frase:
        ancla = "37 años en escena"

    formatos = list(FORMATOS) if args.formato == "all" else [args.formato]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tag = _slug(args.frase or "titulo")

    for key in formatos:
        img = construir(
            frase=args.frase,
            solo_titulo=args.solo_titulo or not args.frase,
            ancla=ancla,
            con_web=not args.no_web,
            foto_name=args.foto,
            size=FORMATOS[key],
        )
        out = OUT_DIR / f"teaser-{tag}-{key}.png"
        img.save(out, optimize=True)
        print(f"  {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
