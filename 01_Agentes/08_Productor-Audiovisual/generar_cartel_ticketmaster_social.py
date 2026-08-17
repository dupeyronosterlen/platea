#!/usr/bin/env python3
"""
Generador de cartel — refresh Ticketmaster, formatos digitales (Social + Web).
Agente: 08 Productor Audiovisual · dirección visual de 01 Director Creativo.
Sigue la skill .claude/skills/cartel-diseno-teoria/, Estructura B (Dinámica /
regla de tercios) — elegida por Dirección el 26 jul 2026 sobre la Estructura C
(Minimalismo) que usan Teatrando/SOGEM, para parecerse más al formato denso
que usa Ticketmaster en sus propios anuncios pagados (bloque de créditos
arriba, venue+horario, foto grande, título, barra de CTA abajo).

Ver brief completo: 03_Producciones/el-gorila/canales/Ticketmaster/brief-arte-ticketmaster.md
Ver datos verificados: 03_Producciones/el-gorila/canales/Ticketmaster/ficha-datos-completos.md

Regla de oro #10 / instrucción de Dirección (26 jul 2026): SIN fecha de inicio/fin de
temporada en estas piezas — se usa legado ("37 años en cartelera") como dato
de urgencia en su lugar. SIN precio (Ticketmaster vende por su cuenta).

Uso:
    python3 generar_cartel_ticketmaster_social.py                 # genera todos los formatos
    python3 generar_cartel_ticketmaster_social.py --solo story    # un formato

Auditoría (correr después de generar, siempre):
    python3 .claude/skills/cartel-diseno-teoria/scripts/auditar_cartel.py <ruta.png>

Salida: 05_Activos/el-gorila/carteles-s2/ticketmaster-social/
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "05_Activos/el-gorila"
OUT_DIR = ASSETS / "carteles-s2/ticketmaster-social"

FOTO_HERO = ASSETS / "banco-fotos/stories-9x16/DSC03886.jpg"  # perfil dramático, luz roja — 26 jul, reemplaza la foto genérica

TIPOGRAFIA = ASSETS / "tipografia"
FUENTE_TITULO = TIPOGRAFIA / "primaria/CormorantGaramond-Bold.ttf"
FUENTE_ITALICA = TIPOGRAFIA / "primaria/CormorantGaramond-Italic.ttf"
FUENTE_REGULAR = TIPOGRAFIA / "primaria/CormorantGaramond-Regular.ttf"
# Toda la pieza usa la familia serif Cormorant Garamond (editorial, con personalidad) —
# se quitó Lato (sans genérico tipo plantilla) excepto donde se marca explícitamente.
FUENTE_TEXTO = FUENTE_REGULAR
FUENTE_TEXTO_BOLD = FUENTE_TITULO

NEGRO = (10, 7, 6)
CREMA = (242, 237, 228)
DORADO = (212, 175, 55)
ROJO = (212, 58, 26)

INFO = {
    "presenta": "PRODUCCIONES DUPEYRÓN PRESENTA",
    "tagline": "UNA DE LAS TRAYECTORIAS MÁS LARGAS ACTOR-OBRA DEL TEATRO MEXICANO",
    "venue_linea1": "TEATRO",
    "venue_linea2": "WILBERTO CANTÓN",
    "horario": "SÁBADOS 18:00H",
    "titulo": "EL GORILA",
    "subtitulo": "UN MONÓLOGO BASADO EN FRANZ KAFKA",
    "credito": "Por Humberto Dupeyrón · 37 años en cartelera",
    "cta": "BOLETOS DISPONIBLES EN TICKETMASTER",
}

# (nombre, ancho, alto) — prioridad definida en el brief
FORMATOS = {
    "story": (1080, 1920),
    "feed_cuadrado": (1080, 1080),
    "web_hero": (2048, 1152),
}


def _verificar_assets():
    faltantes = [p for p in [FOTO_HERO, FUENTE_TITULO, FUENTE_TEXTO, FUENTE_TEXTO_BOLD] if not p.exists()]
    if faltantes:
        detalle = "\n".join(f"  - {p}" for p in faltantes)
        raise SystemExit(f"Faltan assets:\n{detalle}")


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


def texto_centrado(draw, texto, y, font, fill, cx, tracking=0):
    if tracking:
        # tracking manual: dibuja letra por letra para permitir espaciado positivo (texto chico)
        anchos = [draw.textlength(c, font=font) + tracking for c in texto]
        total = sum(anchos) - tracking
        x = cx - total / 2
        for c, aw in zip(texto, anchos):
            draw.text((x, y), c, font=font, fill=fill)
            x += aw
    else:
        bbox = draw.textbbox((0, 0), texto, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw / 2, y), texto, font=font, fill=fill)
    return altura_linea(font)


def gradiente_vertical(w, h, color_transparente_arriba, color_opaco_abajo):
    """Overlay RGBA que va de transparente (arriba) a oscuro-opaco (abajo),
    para que el texto sobre la foto sea legible sin tapar la imagen completa."""
    grad = Image.new("L", (1, h), color=0)
    for y in range(h):
        grad.putpixel((0, y), int(255 * (y / h) ** 1.6))
    alpha = grad.resize((w, h))
    overlay = Image.new("RGBA", (w, h), color_opaco_abajo + (0,))
    overlay.putalpha(alpha)
    return overlay


def construir(size) -> Image.Image:
    w, h = size
    s = w / 1080  # escala relativa al diseño base (story, 1080 de ancho)
    cartel = Image.new("RGB", size, NEGRO)
    draw = ImageDraw.Draw(cartel)
    cx = w // 2
    margen = int(w * 0.08)

    # ============ Zona superior (créditos + tagline en itálica editorial) ============
    y = int(h * 0.05)

    f_presenta = fuente_ajustada(INFO["presenta"], FUENTE_REGULAR, int(28 * s), w - 2 * margen)
    y += texto_centrado(draw, INFO["presenta"], y, f_presenta, CREMA, cx, tracking=int(3 * s))
    y += int(16 * s)

    # Regla fina roja bajo la línea "presenta" — acento gráfico, no decoración pesada
    linea_w = int(w * 0.14)
    draw.rectangle([cx - linea_w // 2, y, cx + linea_w // 2, y + max(2, int(2 * s))], fill=ROJO)
    y += int(28 * s)

    f_tagline = fuente_ajustada(INFO["tagline"], FUENTE_ITALICA, int(34 * s), w - 2 * margen)
    palabras = INFO["tagline"].split()
    medio = len(palabras) // 2
    linea1, linea2 = " ".join(palabras[:medio]), " ".join(palabras[medio:])
    for linea in (linea1, linea2):
        y += texto_centrado(draw, linea, y, f_tagline, DORADO, cx)
        y += int(6 * s)
    y += int(36 * s)

    # Venue + horario — bloque a la izquierda con marca gráfica: línea vertical roja
    f_venue = fuente_ajustada(INFO["venue_linea2"], FUENTE_TITULO, int(52 * s), w - 2 * margen - int(20 * s))
    f_venue_label = fuente_ajustada(INFO["venue_linea1"], FUENTE_REGULAR, int(26 * s), w - 2 * margen)
    f_horario = fuente_ajustada(INFO["horario"], FUENTE_TITULO, int(36 * s), w - 2 * margen)

    barra_x = margen
    texto_x = margen + int(16 * s)
    bloque_y0 = y
    draw.text((texto_x, y), INFO["venue_linea1"], font=f_venue_label, fill=CREMA)
    y += altura_linea(f_venue_label) + int(2 * s)
    draw.text((texto_x, y), INFO["venue_linea2"], font=f_venue, fill=DORADO)
    y += altura_linea(f_venue) + int(10 * s)
    draw.text((texto_x, y), INFO["horario"], font=f_horario, fill=CREMA)
    y += altura_linea(f_horario)
    draw.rectangle([barra_x, bloque_y0 + int(4 * s), barra_x + max(3, int(3 * s)), y - int(4 * s)], fill=ROJO)

    zona_superior_fin = y + int(34 * s)

    # ============ Zona media/baja: foto grande a sangre + título ============
    foto_y0 = zona_superior_fin
    foto_y1 = int(h * 0.92)
    foto_h = foto_y1 - foto_y0

    foto = Image.open(FOTO_HERO).convert("RGB")
    # centering (0.42, 0.4): la foto ya viene en formato 9:16 casi idéntico al story —
    # se preserva el encuadre original del perfil, no se re-centra al rostro completo.
    foto = ImageOps.fit(foto, (w, foto_h), method=Image.LANCZOS, centering=(0.42, 0.40))
    cartel.paste(foto, (0, foto_y0))

    # Vignette solo en el tercio inferior de la foto — la imagen ya es oscura/roja,
    # no necesita oscurecerse toda, solo donde se posa el título.
    overlay = gradiente_vertical(w, foto_h, NEGRO, NEGRO)
    cartel.paste(Image.alpha_composite(foto.convert("RGBA"), overlay).convert("RGB"), (0, foto_y0))

    # Título + subtítulo + crédito — CREMA (no rojo: la foto ya es roja, un título rojo
    # se perdería contra ella) con tracking negativo para sensación de peso editorial.
    ancho_titulo_max = w - 2 * margen
    f_titulo = fuente_ajustada(INFO["titulo"], FUENTE_TITULO, int(210 * s), ancho_titulo_max)
    f_subtitulo = fuente_ajustada(INFO["subtitulo"], FUENTE_ITALICA, int(32 * s), ancho_titulo_max)
    f_credito = fuente_ajustada(INFO["credito"], FUENTE_ITALICA, int(28 * s), ancho_titulo_max)

    alto_bloque_texto = (
        altura_linea(f_titulo) + int(16 * s) + altura_linea(f_subtitulo) + int(12 * s) + altura_linea(f_credito)
    )
    y_texto = foto_y1 - int(26 * s) - alto_bloque_texto

    y_texto += texto_centrado(draw, INFO["titulo"], y_texto, f_titulo, CREMA, cx, tracking=int(-2 * s))
    y_texto += int(16 * s)
    y_texto += texto_centrado(draw, INFO["subtitulo"], y_texto, f_subtitulo, CREMA, cx)
    y_texto += int(12 * s)
    texto_centrado(draw, INFO["credito"], y_texto, f_credito, DORADO, cx)

    # ============ Barra inferior — CTA con acento rojo, no bloque dorado plano ============
    barra_y0 = foto_y1
    draw.rectangle([0, barra_y0, w, barra_y0 + max(3, int(4 * s))], fill=ROJO)
    draw.rectangle([0, barra_y0 + max(3, int(4 * s)), w, h], fill=NEGRO)
    f_cta = fuente_ajustada(INFO["cta"], FUENTE_TITULO, int(38 * s), w - 2 * margen)
    cta_y = barra_y0 + (h - barra_y0 - altura_linea(f_cta)) // 2
    texto_centrado(draw, INFO["cta"], cta_y, f_cta, DORADO, cx, tracking=int(2 * s))

    return cartel


def construir_cuadrado(size) -> Image.Image:
    """Feed 1080x1080 — Estructura B: columna de texto a la izquierda (tercio de
    la grilla 3x3), foto a sangre a la derecha. Misma paleta/tipografía que story."""
    w, h = size
    s = h / 1080
    cartel = Image.new("RGB", size, NEGRO)
    draw = ImageDraw.Draw(cartel)

    col_w = int(w * 0.40)
    margen = int(col_w * 0.14)
    texto_x = margen
    ancho_texto_max = col_w - 2 * margen

    # Foto a sangre en el 60% derecho
    foto = Image.open(FOTO_HERO).convert("RGB")
    foto = ImageOps.fit(foto, (w - col_w, h), method=Image.LANCZOS, centering=(0.42, 0.38))
    cartel.paste(foto, (col_w, 0))
    overlay = gradiente_vertical(w - col_w, h, NEGRO, NEGRO)
    foto_oscura = Image.alpha_composite(foto.convert("RGBA"), overlay).convert("RGB")
    cartel.paste(foto_oscura, (col_w, 0))
    # Degradado suave en el borde donde la foto se une a la columna de texto
    fundido = gradiente_vertical(int(w * 0.06), h, NEGRO, NEGRO).rotate(-90, expand=True)
    fundido = fundido.resize((int(w * 0.06), h))

    y = int(h * 0.07)
    f_presenta = fuente_ajustada(INFO["presenta"], FUENTE_REGULAR, int(22 * s), ancho_texto_max)
    draw.text((texto_x, y), "PRODUCCIONES", font=f_presenta, fill=CREMA)
    y += altura_linea(f_presenta) + int(2 * s)
    draw.text((texto_x, y), "DUPEYRÓN PRESENTA", font=f_presenta, fill=CREMA)
    y += altura_linea(f_presenta) + int(14 * s)
    draw.rectangle([texto_x, y, texto_x + int(col_w * 0.22), y + max(2, int(2 * s))], fill=ROJO)
    y += int(26 * s)

    f_venue_label = fuente_ajustada(INFO["venue_linea1"], FUENTE_REGULAR, int(22 * s), ancho_texto_max)
    f_venue = fuente_ajustada(INFO["venue_linea2"], FUENTE_TITULO, int(30 * s), ancho_texto_max)
    f_horario = fuente_ajustada(INFO["horario"], FUENTE_TITULO, int(24 * s), ancho_texto_max)
    draw.text((texto_x, y), INFO["venue_linea1"], font=f_venue_label, fill=CREMA)
    y += altura_linea(f_venue_label) + int(2 * s)
    for palabra in INFO["venue_linea2"].split():
        draw.text((texto_x, y), palabra, font=f_venue, fill=DORADO)
        y += altura_linea(f_venue) + int(2 * s)
    y += int(8 * s)
    draw.text((texto_x, y), INFO["horario"], font=f_horario, fill=CREMA)

    # Título + subtítulo anclados al tercio inferior de la columna
    f_titulo = fuente_ajustada("EL", FUENTE_TITULO, int(90 * s), ancho_texto_max)
    f_subtitulo = fuente_ajustada(INFO["subtitulo"], FUENTE_ITALICA, int(20 * s), ancho_texto_max)
    f_credito = fuente_ajustada(INFO["credito"], FUENTE_ITALICA, int(18 * s), ancho_texto_max)

    y_titulo = int(h * 0.62)
    draw.text((texto_x, y_titulo), "EL", font=f_titulo, fill=CREMA)
    y_titulo += altura_linea(f_titulo) + int(-6 * s)
    draw.text((texto_x, y_titulo), "GORILA", font=f_titulo, fill=CREMA)
    y_titulo += altura_linea(f_titulo) + int(14 * s)

    # subtítulo envuelto en 2 líneas cortas dentro de la columna
    palabras = INFO["subtitulo"].split()
    medio = len(palabras) // 2
    for linea in (" ".join(palabras[:medio]), " ".join(palabras[medio:])):
        draw.text((texto_x, y_titulo), linea, font=f_subtitulo, fill=CREMA)
        y_titulo += altura_linea(f_subtitulo) + int(2 * s)
    y_titulo += int(10 * s)
    draw.text((texto_x, y_titulo), "Por Humberto Dupeyrón", font=f_credito, fill=DORADO)

    # CTA — barra angosta al pie de la columna de texto
    barra_y0 = int(h * 0.94)
    draw.rectangle([0, barra_y0, col_w, barra_y0 + max(3, int(3 * s))], fill=ROJO)
    f_cta = fuente_ajustada("TICKETMASTER", FUENTE_TITULO, int(24 * s), ancho_texto_max)
    draw.text((texto_x, barra_y0 + int(12 * s)), "TICKETMASTER", font=f_cta, fill=DORADO)

    return cartel


def construir_web_hero(size) -> Image.Image:
    """Web hero 2048x1152 — Ticketmaster pide estas piezas 'preferentemente sin
    texto' (guía de estilo oficial). Solo foto + título, nada de venue/horario/CTA."""
    w, h = size
    s = h / 1152
    cartel = Image.new("RGB", size, NEGRO)

    foto = Image.open(FOTO_HERO).convert("RGB")
    foto = ImageOps.fit(foto, size, method=Image.LANCZOS, centering=(0.32, 0.35))
    cartel.paste(foto, (0, 0))

    overlay = gradiente_vertical(w, h, NEGRO, NEGRO)
    cartel = Image.alpha_composite(cartel.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(cartel)
    margen = int(w * 0.06)
    ancho_max = int(w * 0.5)
    f_titulo = fuente_ajustada(INFO["titulo"], FUENTE_TITULO, int(140 * s), ancho_max)
    f_credito = fuente_ajustada("Humberto Dupeyrón", FUENTE_ITALICA, int(30 * s), ancho_max)

    y = h - int(60 * s) - altura_linea(f_titulo) - int(10 * s) - altura_linea(f_credito)
    draw.text((margen, y), INFO["titulo"], font=f_titulo, fill=CREMA)
    y += altura_linea(f_titulo) + int(10 * s)
    draw.text((margen, y), "Humberto Dupeyrón", font=f_credito, fill=DORADO)

    return cartel


CONSTRUCTORES = {
    "story": construir,
    "feed_cuadrado": construir_cuadrado,
    "web_hero": construir_web_hero,
}


def main():
    _verificar_assets()
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", choices=list(FORMATOS.keys()), help="generar solo un formato")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    formatos = {args.solo: FORMATOS[args.solo]} if args.solo else FORMATOS

    for nombre, size in formatos.items():
        print(f"Generando {nombre} ({size[0]}x{size[1]})...")
        cartel = CONSTRUCTORES[nombre](size)
        out = OUT_DIR / f"ticketmaster-{nombre}-{size[0]}x{size[1]}.jpg"
        cartel.save(out, quality=92)
        print(f"  {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
