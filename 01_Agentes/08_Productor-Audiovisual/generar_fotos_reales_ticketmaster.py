#!/usr/bin/env python3
"""
Recorta las fotos reales de producción (no el arte del póster) a las medidas
exactas que pide el media kit de Ticketmaster para las secciones que
requieren fotografía real: Mailing Galería y EADP (Gallery/About/Accessibility/
Experience). Ver 03_Producciones/el-gorila/canales/Ticketmaster/media-kit-specs.md.

Fotos fuente: 05_Activos/el-gorila/banco-fotos/personaje-aislado/ (22.png,
24.png, DSC03814.png) — verificadas visualmente el 28 jul 2026: no muestran
ningún elemento identificable del recinto (solo telón/fondo/mesa de utilería),
así que sirven aunque se hayan tomado en otro escenario.

Uso:
    python3 generar_fotos_reales_ticketmaster.py

Salida: 03_Producciones/el-gorila/canales/Ticketmaster/bases-frame/fotos-reales/
"""

from pathlib import Path

from PIL import Image, ImageOps

REPO = Path(__file__).resolve().parents[2]
FOTOS_DIR = REPO / "05_Activos/el-gorila/banco-fotos/personaje-aislado"
OUT_DIR = REPO / "03_Producciones/el-gorila/canales/Ticketmaster/bases-frame/fotos-reales"

# Mailing Galería: 248x184, una por foto
MAILING = [
    ("22.png", "Mailing_GaleriaFoto_248x184_a.jpg", (0.5, 0.32)),
    ("24.png", "Mailing_GaleriaFoto_248x184_b.jpg", (0.55, 0.30)),
    ("DSC03814.png", "Mailing_GaleriaFoto_248x184_c.jpg", (0.5, 0.35)),
]

# EADP: una foto principal (DSC03814, la más "de escena" — mesa+utilería visible)
EADP = [
    ("DSC03814.png", "EADP_GalleryImage_900x600.jpg", (900, 600), (0.5, 0.35)),
    ("DSC03814.png", "EADP_About_720x568.jpg", (720, 568), (0.5, 0.3)),
    ("22.png", "EADP_Accessibility_720x568.jpg", (720, 568), (0.5, 0.3)),
    ("24.png", "EADP_Experience_400x225.jpg", (400, 225), (0.55, 0.28)),
]


def recortar(foto_nombre, size, centering):
    im = Image.open(FOTOS_DIR / foto_nombre).convert("RGB")
    return ImageOps.fit(im, size, method=Image.LANCZOS, centering=centering)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for foto, nombre_out, centering in MAILING:
        img = recortar(foto, (248, 184), centering)
        out = OUT_DIR / nombre_out
        img.save(out, quality=92)
        print(f"{out.relative_to(REPO)}  <- {foto}")

    for foto, nombre_out, size, centering in EADP:
        img = recortar(foto, size, centering)
        out = OUT_DIR / nombre_out
        img.save(out, quality=92)
        print(f"{out.relative_to(REPO)}  <- {foto}")


if __name__ == "__main__":
    main()
