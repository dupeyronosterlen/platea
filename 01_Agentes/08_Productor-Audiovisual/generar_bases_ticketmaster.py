#!/usr/bin/env python3
"""
Genera las BASES (frames) que pide el Media Kit 2025 real de Ticketmaster —
un paso previo a decidir qué texto/CTA se le mete a cada una.

Regla de esta pasada (instrucción de Dirección, 28 jul 2026): full frame, SIN cortar
la imagen, y sin que se noten espacios vacíos/oscuros — se tiene que sentir
que la imagen llena el marco en cualquier proporción. Cada base es el lienzo
exacto que pide cada especificación, con el arte completo (las dos mitades
humano/gorila, sin recortar) escalado para que quepa entero y quede centrado.
El espacio sobrante (cuando la proporción del lienzo no coincide con la de la
imagen) se rellena con un fondo desenfocado/oscurecido de la MISMA imagen
(técnica de 'blurred backdrop' — Spotify/YouTube la usan para portadas que no
calzan con el contenedor), no con negro sólido: así no se ven "pedazos
oscuros" y el arte se siente continuo hasta el borde en cualquier framerate.

Fuente de la imagen: 05_Activos/el-gorila/poster-elementos-sueltos/imagen/
(extraída de las capas del PSD el 28 jul 2026 — ver README de esa carpeta).
No se usa Poster.png (JPEG aplanado, con texto pintado encima).

Uso:
    python3 generar_bases_ticketmaster.py            # las 13 bases
    python3 generar_bases_ticketmaster.py --solo imagehero

Salida: 03_Producciones/el-gorila/canales/Ticketmaster/bases-frame/
"""

import argparse
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

REPO = Path(__file__).resolve().parents[2]
IMAGEN_FUENTE = REPO / "05_Activos/el-gorila/poster-elementos-sueltos/imagen/mono-pintura-completa-sin-marco.png"
OUT_DIR = REPO / "03_Producciones/el-gorila/canales/Ticketmaster/bases-frame"

NEGRO = (10, 7, 6)

# clave -> (ancho, alto, nombre_archivo) — medidas verificadas contra el Media
# Kit 2025 real (PDF entregado por Dirección el 28 jul 2026).
FORMATOS = {
    "ads_728x90": (728, 90, "Ads_728x90"),
    "ads_300x250": (300, 250, "Ads_300x250"),
    "ads_300x600": (300, 600, "Ads_300x600"),
    "imagehero": (1440, 450, "ImageHero_1440x450_El-Gorila"),
    "mediumimage": (720, 405, "MediumImage_720x405_El-Gorila"),
    "smallimage": (368, 207, "SmallImage_368x207_El-Gorila"),
    "push": (305, 225, "PushNotification_305x225"),
    "eadp_header_desktop": (1024, 432, "EADP_HeaderDesktop_1024x432"),
    "eadp_header_mobile": (375, 310, "EADP_HeaderMobile_375x310"),
    "eadp_about": (720, 568, "EADP_About_720x568"),
    "eadp_gallery": (900, 600, "EADP_GalleryImage_900x600"),
    "mailing_header": (640, 360, "Mailing_HeaderSolus_640x360"),
    "mailing_gallery": (248, 184, "Mailing_GaleriaFoto_248x184"),
    # Web: Cortes (listados/buscador) — ⚠️ regla del PDF: sin texto/fechas/
    # logos de patrocinador en estas piezas, aquí van solo encuadre limpio.
    "cortes_pin": (2426, 1365, "PIN_2426x1365"),
    "cortes_artist1": (305, 225, "Artist1_305x225"),
    "cortes_artist2": (205, 115, "Artist2_205x115"),
    "cortes_generico": (1080, 1080, "Generico_1080x1080"),
    # Web: Guías
    "guias_header": (2500, 911, "Guias_Header_2500x911"),
    "guias_spotlight": (518, 292, "Guias_Spotlight_518x292"),
    "guias_arte_galeria": (1080, 1080, "Guias_ArteGaleria_1080x1080"),
    # Redes sociales (si Ticketmaster promueve el show en sus propias cuentas)
    "social_story_reel": (1080, 1920, "Social_StoryReel_1080x1920"),
    "social_feed_vertical": (1080, 1350, "Social_FeedVertical_1080x1350"),
    "social_feed_cuadrado": (1080, 1080, "Social_FeedCuadrado_1080x1080"),
    # Blog — único formato PNG-24 del set (spec del media kit), el resto son jpg
    "blog": (1473, 830, "Blog_1473x830_El-Gorila"),
}


def _fondo_desenfocado(arte: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Rellena TODO el lienzo (cover, recortando) con la misma imagen,
    desenfocada y oscurecida — así el espacio sobrante alrededor del arte
    nítido no se ve como un hueco negro, sino como una continuación borrosa
    de la propia pintura. Escala primero a un tamaño intermedio para que el
    blur no tarde una eternidad en los formatos grandes (2426px, etc.)."""
    w, h = size
    chico = arte.copy()
    chico.thumbnail((600, 600), Image.LANCZOS)
    fondo = ImageOps.fit(chico, size, method=Image.LANCZOS, centering=(0.5, 0.4))
    fondo = fondo.filter(ImageFilter.GaussianBlur(radius=max(w, h) * 0.03))
    fondo = ImageEnhance.Brightness(fondo).enhance(0.45)
    fondo = ImageEnhance.Contrast(fondo).enhance(0.9)
    return fondo


def construir_base(size: tuple[int, int]) -> Image.Image:
    """Full frame: la imagen completa (sin cortar) escalada para caber entera
    y centrada, sobre un fondo desenfocado de sí misma (no negro sólido) para
    que se sienta que llena el marco en cualquier proporción."""
    w, h = size
    arte = Image.open(IMAGEN_FUENTE).convert("RGB")
    aw, ah = arte.size

    base = _fondo_desenfocado(arte, size)

    escala = min(w / aw, h / ah)
    nuevo_w, nuevo_h = max(1, int(aw * escala)), max(1, int(ah * escala))
    nitida = arte.resize((nuevo_w, nuevo_h), Image.LANCZOS)

    x = (w - nuevo_w) // 2
    y = (h - nuevo_h) // 2
    base.paste(nitida, (x, y))
    return base


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", choices=list(FORMATOS.keys()), help="generar solo una base")
    args = parser.parse_args()

    if not IMAGEN_FUENTE.exists():
        raise SystemExit(f"Falta la imagen fuente: {IMAGEN_FUENTE}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    items = {args.solo: FORMATOS[args.solo]} if args.solo else FORMATOS

    for clave, (w, h, nombre) in items.items():
        print(f"Generando {nombre} ({w}x{h})...")
        base = construir_base((w, h))
        if clave == "blog":
            out = OUT_DIR / f"{nombre}.png"
            base.save(out, format="PNG")
        else:
            out = OUT_DIR / f"{nombre}.jpg"
            base.save(out, quality=95)
        print(f"  {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
