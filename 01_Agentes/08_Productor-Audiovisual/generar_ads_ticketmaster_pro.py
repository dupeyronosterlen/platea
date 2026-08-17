#!/usr/bin/env python3
"""
Mockup de los 3 banners "Web: Ads" del media kit real de Ticketmaster
(728x90 / 300x250 / 300x600) con tratamiento profesional — logotipo dorado
"EL GORILA" + crédito + venue + CTA propio, sobre la base full-frame ya
generada (generar_bases_ticketmaster.py).

Referencias reales usadas (Dirección pidió buscar ejemplos reales de Ticketmaster
antes de diseñar, 28 jul 2026 — visto en vivo en ticketmaster.com.mx):
- Hero de ticketmaster.com.mx: foto a sangre + degradado inferior + título
  blanco bold + botón CTA sólido — misma receta que aquí, adaptada a nuestra
  paleta (dorado/rojo, no el azul de marca de Ticketmaster).
- EADP "El Rey León": lockup "Presenta:" + logotipo del show arriba del
  título — aquí el logotipo es nuestro "EL GORILA" (extraído del PSD).
- Tarjetas de evento (home): bloque de texto compacto + CTA visible.

IMPORTANTE (instrucción explícita de Dirección, 28 jul 2026): SIN CTA ni botón de
ningún tipo — eso lo pone Ticketmaster en su propia plantilla. Nosotros
entregamos SOLO la información de la pieza (título/logotipo, crédito,
legado) sobre el arte. Ver la página en vivo de Ticketmaster fue solo para
entender el ACOMODO de la información (jerarquía, dónde va el logotipo, dónde
el crédito) — no para copiar su CTA ni su marca.

Uso:
    python3 generar_ads_ticketmaster_pro.py
    python3 generar_ads_ticketmaster_pro.py --solo ads_300x250

Salida: 03_Producciones/el-gorila/canales/Ticketmaster/bases-frame/pro/
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
BASES_DIR = REPO / "03_Producciones/el-gorila/canales/Ticketmaster/bases-frame"
TEXTO_DIR = REPO / "05_Activos/el-gorila/poster-elementos-sueltos/texto"
OUT_DIR = BASES_DIR / "pro"

TIPOGRAFIA = REPO / "05_Activos/el-gorila/tipografia"
F_BOLD = TIPOGRAFIA / "primaria/CormorantGaramond-Bold.ttf"
F_ITALIC = TIPOGRAFIA / "primaria/CormorantGaramond-Italic.ttf"
F_SECUNDARIA_BOLD = TIPOGRAFIA / "secundaria/Lato-Bold.ttf"

DORADO = (201, 168, 76)
ROJO = (212, 58, 26)
CREMA = (245, 240, 232)
NEGRO = (10, 7, 6)

LOGOTIPO = TEXTO_DIR / "el-gorila.png"
CREDITO_IMG = TEXTO_DIR / "humberto-dupeyron-en.png"

FORMATOS = {
    "ads_728x90": ("Ads_728x90", "franja"),
    "ads_300x250": ("Ads_300x250", "apilado"),
    "ads_300x600": ("Ads_300x600", "apilado"),
}


def _gradiente_inferior(w, h, frac=0.55):
    """Overlay negro que va de transparente (arriba) a opaco (abajo) en el
    frac inferior del lienzo — para que el texto sea legible sobre la foto."""
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = overlay.load()
    y0 = int(h * (1 - frac))
    for y in range(y0, h):
        t = (y - y0) / max(1, h - y0)
        alpha = int(235 * (t ** 1.3))
        for x in range(w):
            px[x, y] = (0, 0, 0, alpha)
    return overlay


def _pegar_logotipo(cartel, ancho_destino, y, cx=None, x=None):
    logo = Image.open(LOGOTIPO).convert("RGBA")
    escala = ancho_destino / logo.width
    logo = logo.resize((ancho_destino, max(1, int(logo.height * escala))), Image.LANCZOS)
    px = cx - logo.width // 2 if cx is not None else x
    cartel.paste(logo, (px, y), logo)
    return logo.height


def construir_apilado(size) -> Image.Image:
    """300x250 / 300x600 — bloque inferior con degradado, logotipo centrado,
    crédito arriba y abajo. SIN CTA ni botón: eso lo pone Ticketmaster en su
    propia plantilla (instrucción explícita de Dirección, 28 jul 2026) — nosotros
    solo entregamos la información de la pieza (título, crédito, legado).
    El alto del bloque se mide ANTES de dibujar nada, para anclarlo desde
    abajo y que nunca se salga del lienzo."""
    w, h = size
    base_path = BASES_DIR / f"{FORMATOS_INV[size]}.jpg"
    cartel = Image.open(base_path).convert("RGBA")
    draw = ImageDraw.Draw(cartel)
    cx = w // 2
    margen_abajo = max(10, int(h * 0.06))

    for escala in (1.0, 0.85, 0.7, 0.58):
        f_credito = ImageFont.truetype(str(F_ITALIC), max(10, int(h * 0.052 * escala)))
        f_sub = ImageFont.truetype(str(F_ITALIC), max(9, int(h * 0.042 * escala)))

        logo = Image.open(LOGOTIPO).convert("RGBA")
        logo_w = int(w * 0.72 * escala)
        logo_h = max(1, int(logo.height * (logo_w / logo.width)))

        credito_txt = "Humberto Dupeyron en:"
        sub_txt = "37 años en cartelera"

        gap = max(2, int(h * 0.02 * escala))
        h_credito = sum(f_credito.getmetrics())
        h_sub = sum(f_sub.getmetrics())

        total = h_credito + gap + logo_h + gap + h_sub
        if total <= h - margen_abajo - int(h * 0.06):
            break

    y0 = h - margen_abajo - total
    frac = min(0.9, (total + margen_abajo + int(h * 0.06)) / h)
    cartel.alpha_composite(_gradiente_inferior(w, h, frac=frac))
    draw = ImageDraw.Draw(cartel)  # redibujar sobre el compuesto con el overlay ya aplicado

    y = y0
    tw = draw.textlength(credito_txt, font=f_credito)
    draw.text((cx - tw / 2, y), credito_txt, font=f_credito, fill=CREMA)
    y += h_credito + gap

    logo_h_real = _pegar_logotipo(cartel, logo_w, y, cx=cx)
    y += logo_h_real + gap

    tw = draw.textlength(sub_txt, font=f_sub)
    draw.text((cx - tw / 2, y), sub_txt, font=f_sub, fill=DORADO)

    return cartel.convert("RGB")


def construir_franja(size) -> Image.Image:
    """728x90 — una sola franja: logotipo + crédito a la izquierda, arte
    visible a la derecha. SIN CTA ni botón: eso lo pone Ticketmaster en su
    propia plantilla — nosotros solo entregamos la información de la pieza."""
    w, h = size
    base_path = BASES_DIR / f"{FORMATOS_INV[size]}.jpg"
    cartel = Image.open(base_path).convert("RGBA")

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = overlay.load()
    for x in range(w):
        # más oscuro a la izquierda (donde va el texto), más claro hacia la derecha (se ve el arte)
        t = min(1.0, max(0.0, (x / w - 0.15) / 0.55))
        alpha = int(150 * (1 - t))
        for y in range(h):
            px[x, y] = (0, 0, 0, alpha)
    cartel.alpha_composite(overlay)
    draw = ImageDraw.Draw(cartel)

    margen = int(h * 0.14)
    logo_h_destino = int(h * 0.5)
    logo = Image.open(LOGOTIPO).convert("RGBA")
    escala = logo_h_destino / logo.height
    logo = logo.resize((max(1, int(logo.width * escala)), logo_h_destino), Image.LANCZOS)
    cartel.paste(logo, (margen, (h - logo.height) // 2), logo)

    f_credito = ImageFont.truetype(str(F_ITALIC), max(10, int(h * 0.22)))
    credito_txt = "37 años en cartelera"
    draw.text((margen + logo.width + int(h * 0.18), (h - sum(f_credito.getmetrics())) // 2),
               credito_txt, font=f_credito, fill=DORADO)

    return cartel.convert("RGB")


FORMATOS_INV = {}


def main():
    global FORMATOS_INV
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", choices=list(FORMATOS.keys()))
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    items = {args.solo: FORMATOS[args.solo]} if args.solo else FORMATOS

    tamanos = {
        "ads_728x90": (728, 90),
        "ads_300x250": (300, 250),
        "ads_300x600": (300, 600),
    }
    for clave, (nombre_archivo, _layout) in items.items():
        size = tamanos[clave]
        FORMATOS_INV[size] = nombre_archivo
        print(f"Generando {nombre_archivo} pro ({size[0]}x{size[1]})...")
        constructor = construir_franja if _layout == "franja" else construir_apilado
        cartel = constructor(size)
        out = OUT_DIR / f"{nombre_archivo}.jpg"
        cartel.save(out, quality=95)
        print(f"  {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
