#!/usr/bin/env python3
"""
Generador de cartel — Ticketmaster, OPCIÓN B (arte pintado, mismo que
Cartelera de Teatro/SOGEM). Agente: 08 Productor Audiovisual.

A diferencia de generar_cartel_ticketmaster_social.py (Opción A: foto real,
dramática), esta opción reutiliza el mismo póster maestro pintado que ya se
usó para SOGEM y Cartelera de Teatro (03_Producciones/el-gorila/Cartele
editables/Poster.png) — misma paleta y tipografía que
generar_cartel_cartelera_teatro.py, para que la agencia use SIEMPRE la misma
receta de colores/fuentes y solo cambie la imagen según el canal (foto real
o el arte pintado).

El póster fuente trae las fechas de temporada pintadas dentro de la imagen
(no son texto que se pueda quitar por código). Para cumplir la instrucción de
Dirección de no mostrar fechas en el material de Ticketmaster, se recorta el póster
por ARRIBA de esa línea (título + subtítulo + separador) y se añade una barra
nueva abajo con horario/venue/CTA re-tipeados — mismo truco ya usado en el
banner ancho de SOGEM (04-twitter-1600x900.jpg).

Uso:
    python3 generar_cartel_ticketmaster_opcionB.py                  # los 3 formatos
    python3 generar_cartel_ticketmaster_opcionB.py --solo story

Auditoría (correr después, siempre):
    python3 .claude/skills/cartel-diseno-teoria/scripts/auditar_cartel.py <ruta.png>

Salida: 05_Activos/el-gorila/carteles-s2/ticketmaster-social/opcion-b/
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "05_Activos/el-gorila"
OUT_DIR = ASSETS / "carteles-s2/ticketmaster-social/opcion-b"
OUT_DIR_MEDIAKIT = OUT_DIR / "media-kit-real"

POSTER_FUENTE = REPO / "03_Producciones/el-gorila/Cartele editables/Poster.png"

TIPOGRAFIA = ASSETS / "tipografia"
F_PRIMARIA_BOLD = TIPOGRAFIA / "primaria/CormorantGaramond-Bold.ttf"
F_PRIMARIA_ITALIC = TIPOGRAFIA / "primaria/CormorantGaramond-Italic.ttf"
F_SECUNDARIA = TIPOGRAFIA / "secundaria/Lato-Regular.ttf"
F_SECUNDARIA_BOLD = TIPOGRAFIA / "secundaria/Lato-Bold.ttf"

# Misma paleta EXACTA que generar_cartel_cartelera_teatro.py (SOGEM/Cartelera) —
# no la de generar_cartel_ticketmaster_social.py (Opción A), para que ambas
# opciones compartan colores/fuentes y solo varíe la imagen.
NEGRO = (10, 7, 6)
CREMA = (245, 240, 232)
DORADO = (201, 168, 76)
ROJO = (212, 58, 26)

INFO = {
    "venue": "TEATRO WILBERTO CANTÓN",
    "horario": "SÁBADOS · 18:00 HRS",
    "cta": "BOLETOS DISPONIBLES EN TICKETMASTER",
}

# Fracción superior del póster fuente a mostrar (excluye fechas/entradas/tagline
# pintados más abajo en la imagen original) — incluye título + subtítulo +
# separador + horario/venue pintados, y se detiene justo ANTES de la línea de
# fechas ("Del 25 de julio al 19 de septiembre"). Calibrado visualmente contra
# Poster.png (5400x7200): el bloque de fechas empieza ~66% de la altura.
FRACCION_ALTO_FUENTE = 0.64

FORMATOS = {
    "story": (1080, 1920),
    "feed_cuadrado": (1080, 1080),
    "web_hero": (2048, 1152),
}


def _verificar_assets():
    faltantes = [p for p in [POSTER_FUENTE, F_PRIMARIA_BOLD, F_PRIMARIA_ITALIC, F_SECUNDARIA, F_SECUNDARIA_BOLD] if not p.exists()]
    if faltantes:
        detalle = "\n".join(f"  - {p}" for p in faltantes)
        raise SystemExit(f"Faltan assets:\n{detalle}")


def altura_linea(font) -> int:
    ascent, descent = font.getmetrics()
    return ascent + descent


def fuente_ajustada(texto, ruta_fuente, tam_deseado, ancho_max, tam_min=10):
    tam = tam_deseado
    while tam > tam_min:
        f = ImageFont.truetype(str(ruta_fuente), tam)
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        if draw.textlength(texto, font=f) <= ancho_max:
            return f
        tam -= max(1, int(tam * 0.05))
    return ImageFont.truetype(str(ruta_fuente), tam_min)


def texto_centrado(draw, texto, y, font, fill, cx):
    bbox = draw.textbbox((0, 0), texto, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw / 2, y), texto, font=font, fill=fill)
    return altura_linea(font)


def recorte_superior(poster: Image.Image, ancho_destino: int, fraccion_alto: float) -> Image.Image:
    """Recorta el poster desde arriba (sin tocar los lados) hasta la fracción
    de altura indicada, y lo escala al ancho destino conservando proporción."""
    w0, h0 = poster.size
    alto_fuente = int(h0 * fraccion_alto)
    recorte = poster.crop((0, 0, w0, alto_fuente))
    escala = ancho_destino / w0
    nuevo_alto = max(1, int(alto_fuente * escala))
    return recorte.resize((ancho_destino, nuevo_alto), Image.LANCZOS)


def construir(size) -> Image.Image:
    w, h = size
    s = w / 1080
    cartel = Image.new("RGB", size, NEGRO)
    draw = ImageDraw.Draw(cartel)
    cx = w // 2

    poster = Image.open(POSTER_FUENTE).convert("RGB")

    margen_marco = int(w * 0.035)
    ancho_imagen = w - 2 * margen_marco
    recorte = recorte_superior(poster, ancho_imagen, FRACCION_ALTO_FUENTE)

    # Tope de alto: si el recorte (a este ancho) no cabe, se ESCALA completo
    # hacia abajo (nunca se recorta) para no perder contenido a la mitad —
    # esto importa sobre todo en formatos anchos/bajos (web hero 2048x1152),
    # donde a ancho completo el recorte sale más alto de lo que cabe.
    alto_max_imagen = int(h * 0.72)
    if recorte.height > alto_max_imagen:
        factor = alto_max_imagen / recorte.height
        recorte = recorte.resize((max(1, int(recorte.width * factor)), alto_max_imagen), Image.LANCZOS)
        ancho_imagen = recorte.width  # la imagen quedó más angosta que el máximo disponible

    ancho_marco = max(2, int(3 * s))
    gap_cta = int(h * 0.05)
    f_cta = fuente_ajustada(INFO["cta"], F_SECUNDARIA_BOLD, int(h * 0.026), w - int(w * 0.12))
    linea_h = max(2, int(2 * s))
    bloque_cta_h = linea_h + int(h * 0.02) + altura_linea(f_cta)

    alto_total_bloque = recorte.height + 2 * ancho_marco + gap_cta + bloque_cta_h
    y0 = (h - alto_total_bloque) // 2

    x_img = (w - recorte.width) // 2
    y_img = y0 + ancho_marco
    cartel.paste(recorte, (x_img, y_img))

    # Marco fino dorado exactamente alrededor de la imagen pegada
    draw.rectangle(
        [x_img - ancho_marco, y_img - ancho_marco,
         x_img + recorte.width + ancho_marco, y_img + recorte.height + ancho_marco],
        outline=DORADO, width=ancho_marco,
    )

    # CTA — re-tipeado, sin fechas de temporada (venue/horario ya vienen pintados en el recorte)
    y = y_img + recorte.height + ancho_marco + gap_cta
    linea_w = int(w * 0.12)
    draw.rectangle([cx - linea_w // 2, y, cx + linea_w // 2, y + linea_h], fill=ROJO)
    y += linea_h + int(h * 0.02)
    texto_centrado(draw, INFO["cta"], y, f_cta, DORADO, cx)

    return cartel


# Región del póster SIN texto pintado encima — el arte de Poster.png trae el
# título/subtítulo/fechas pintados directamente en los píxeles (no son capas
# de texto que se puedan quitar), así que cualquier recorte fuera de esta
# ventana corta palabras a la mitad. Calibrado visualmente: solo el rostro
# (dcha. del lienzo), evitando la franja superior ("Humberto...en:"), la
# franja inferior ("...com.mx" / "37 años en escena") y el título dorado
# "EL GORILA" que invade desde la izquierda.
RECORTE_LIMPIO = (0.75, 0.11, 1.0, 0.82)  # (x0, y0, x1, y1) como fracción del lienzo


UMBRAL_PANORAMICO = 1.4  # w/h por encima de esto, "cover" recorta demasiado el rostro


def _sub_limpia() -> Image.Image:
    poster = Image.open(POSTER_FUENTE).convert("RGB")
    pw, ph = poster.size
    x0, y0, x1, y1 = RECORTE_LIMPIO
    return poster.crop((int(pw * x0), int(ph * y0), int(pw * x1), int(ph * y1)))


def _arte_limpio(size, centering=(0.5, 0.4), anchor="center") -> Image.Image:
    """Encuadre puro (sin texto propio ni CTA) recortado de la zona limpia del
    póster — esto es TODO lo que entregamos: el resto del texto/CTA/branding
    lo pone Ticketmaster en su propia plantilla, por instrucción de Dirección.

    La zona limpia del póster es una franja vertical angosta (retrato). Para
    formatos muy panorámicos (banners anchos), recortarla a sangre ('cover')
    deja solo un fragmento de textura de piel irreconocible — en su lugar se
    mete la franja completa sin recortar ('contain'), con fondo sólido a los
    lados. Ese fondo cae exactamente en la 'zona prohibida' que el propio
    media kit reserva para su overlay, así que no se pierde nada."""
    w, h = size
    sub = _sub_limpia()

    if w / h <= UMBRAL_PANORAMICO:
        return ImageOps.fit(sub, size, method=Image.LANCZOS, centering=centering)

    sw, sh = sub.size
    escala = h / sh
    nuevo = sub.resize((max(1, int(sw * escala)), h), Image.LANCZOS)
    canvas = Image.new("RGB", size, NEGRO)
    nw = nuevo.size[0]
    x = w - nw if anchor == "right" else (w - nw) // 2
    canvas.paste(nuevo, (x, 0))
    return canvas


def construir_cargado_derecha(size, centering=(0.5, 0.4)) -> Image.Image:
    """Web: Home (Image Hero) / EADP (Header) — 'el arte de venir principalmente
    cargado del lado derecho'. Solo el encuadre, sin texto ni CTA propios."""
    return _arte_limpio(size, centering=centering, anchor="right")


def construir_full_bleed(size, centering=(0.5, 0.4)) -> Image.Image:
    """Piezas 'centradas' (Medium/Small Image, EADP About/Gallery, Mailing,
    Push Notification, Ads) — solo el encuadre, sin texto ni CTA propios."""
    return _arte_limpio(size, centering=centering, anchor="center")


construir_ad = construir_full_bleed


# Formatos verificados contra el Media Kit 2025 real de Ticketmaster (PDF
# entregado por Dirección el 28 jul 2026) — reemplaza los tamaños que antes se habían
# investigado de guías de España/Australia por no tener el documento MX.
# clave -> (ancho, alto, nombre_archivo_exacto, constructor, kwargs)
FORMATOS_MEDIAKIT = {
    # Web: Ads — los 3 banners IAB que corren en el sitio de Ticketmaster
    "ads_728x90": (728, 90, "Ads_728x90", construir_ad, {}),
    "ads_300x250": (300, 250, "Ads_300x250", construir_ad, {}),
    "ads_300x600": (300, 600, "Ads_300x600", construir_ad, {}),
    # Web: Home
    "imagehero": (1440, 450, "ImageHero_1440x450_El-Gorila", construir_cargado_derecha, {}),
    "mediumimage": (720, 405, "MediumImage_720x405_El-Gorila", construir_full_bleed, {}),
    "smallimage": (368, 207, "SmallImage_368x207_El-Gorila", construir_full_bleed, {}),
    # Push notification
    "push": (305, 225, "PushNotification_305x225", construir_full_bleed, {}),
    # Web: EADP (Event/Artist Detail Page)
    "eadp_header_desktop": (1024, 432, "EADP_HeaderDesktop_1024x432", construir_cargado_derecha, {}),
    "eadp_header_mobile": (375, 310, "EADP_HeaderMobile_375x310", construir_full_bleed, {"centering": (0.5, 0.22)}),
    "eadp_about": (720, 568, "EADP_About_720x568", construir_full_bleed, {"centering": (0.5, 0.22)}),
    "eadp_gallery": (900, 600, "EADP_GalleryImage_900x600", construir_full_bleed, {}),
    # Mailing
    "mailing_header": (640, 360, "Mailing_HeaderSolus_640x360", construir_full_bleed, {}),
    "mailing_gallery": (248, 184, "Mailing_GaleriaFoto_248x184", construir_full_bleed, {}),
}


def main():
    _verificar_assets()
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", choices=list(FORMATOS.keys()), help="generar solo un formato (set viejo)")
    parser.add_argument("--mediakit", action="store_true", help="generar el set verificado contra el Media Kit 2025 real")
    parser.add_argument("--solo-mediakit", choices=list(FORMATOS_MEDIAKIT.keys()), help="generar solo una pieza del set mediakit")
    args = parser.parse_args()

    if args.mediakit or args.solo_mediakit:
        OUT_DIR_MEDIAKIT.mkdir(parents=True, exist_ok=True)
        items = (
            {args.solo_mediakit: FORMATOS_MEDIAKIT[args.solo_mediakit]}
            if args.solo_mediakit
            else FORMATOS_MEDIAKIT
        )
        for _clave, (w, h, nombre_archivo, constructor, kwargs) in items.items():
            print(f"Generando {nombre_archivo} ({w}x{h})...")
            cartel = constructor((w, h), **kwargs)
            out = OUT_DIR_MEDIAKIT / f"{nombre_archivo}.jpg"
            cartel.save(out, quality=92)
            print(f"  {out.relative_to(REPO)}")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    formatos = {args.solo: FORMATOS[args.solo]} if args.solo else FORMATOS

    for nombre, size in formatos.items():
        print(f"Generando {nombre} ({size[0]}x{size[1]})...")
        cartel = construir(size)
        out = OUT_DIR / f"ticketmaster-b-{nombre}-{size[0]}x{size[1]}.jpg"
        cartel.save(out, quality=92)
        print(f"  {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
