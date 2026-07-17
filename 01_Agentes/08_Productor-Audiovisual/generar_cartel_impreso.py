#!/usr/bin/env python3
"""
Generador de cartel — Categoría D: Oficial / impreso para calle (lona)
Agente: 08 Productor Audiovisual · dirección visual de 01 Director Creativo.
Sigue la skill .claude/skills/cartel-diseno-teoria/ — léela antes de tocar este
archivo, en particular §2 (regla 60/30/10) y §2bis (las 3 estructuras).

Formato físico: 2.5m × 1.5m (horizontal, ratio 5:3) — lona para exterior.

v4 (13 jul 2026): las v2 y v3 seguían "llenando" el lienzo — cada corrección
agregaba elementos para no dejar espacio vacío, cuando el problema real era el
opuesto. Reconstruido con la Estructura C (Minimalismo Áureo, ver skill §2bis):
una sola columna central — como un cartel vertical clásico (parecido en espíritu
al primer cartel que se hizo, v1) — flotando en el lienzo horizontal, con las
franjas izquierda/derecha como espacio negativo REAL (no "lo que sobró"). Foto +
título ocupan ~30%+10% del área total del lienzo (no de la columna), el resto es
aire deliberado, calculado con la regla 60/30/10, no ajustado a ojo.

Regla de IA (13 jul 2026): la foto real de Humberto NUNCA se toca/regenera.
Este script es 100% determinístico (Pillow).

Requiere el disco de producción montado en /Volumes/La Mancha/Elgorila.

Uso:
    python3 generar_cartel_impreso.py              # preview (2000x1200) + print (12000x7200)
    python3 generar_cartel_impreso.py --solo preview

Auditoría (correr después de generar, siempre):
    python3 .claude/skills/cartel-diseno-teoria/scripts/auditar_cartel.py <ruta.png>

Salida: 05_Activos/el-gorila/carteles-s2/impreso/
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
DRIVE = Path("/Volumes/La Mancha/Elgorila/4. Publicidad")
LOGO_SOGEM = REPO / "05_Activos/el-gorila/G/SOGEM50A.png"
OUT_DIR = REPO / "05_Activos/el-gorila/carteles-s2/impreso"

FOTO_HERO = DRIVE / "99. Assets RAW/Fotos/ESTUDIO/IMG_7451.jpg"
BADGE_37 = DRIVE / "13. Elementos Gráficos/badges/37Anos.png"

TIPOGRAFIA = REPO / "05_Activos/el-gorila/tipografia"
FUENTE_PRIMARIA = TIPOGRAFIA / "primaria/CormorantGaramond-Bold.ttf"
FUENTE_PRIMARIA_ITALIC = TIPOGRAFIA / "primaria/CormorantGaramond-Italic.ttf"
FUENTE_SECUNDARIA = TIPOGRAFIA / "secundaria/Lato-Regular.ttf"
FUENTE_SECUNDARIA_BOLD = TIPOGRAFIA / "secundaria/Lato-Bold.ttf"

NEGRO = (10, 10, 10)
CREMA = (245, 240, 232)
DORADO = (201, 168, 76)
ROJO = (212, 58, 26)
GRIS_FINO = (120, 114, 102)

FORMATOS = {
    "print": (12000, 7200),
    "preview": (2000, 1200),
}

INFO = {
    "titulo": "EL GORILA",
    "linea_info": "ESTRENO 25 DE JULIO · TEATRO WILBERTO CANTÓN",
    "cta": "elgorilateatro.com.mx",
    "creditos": (
        "Actuación y dirección: Humberto Dupeyrón  ·  Producción: Producciones Dupeyrón  ·  "
        "Música original: Odila Dupeyrón  ·  Duración: 1h 20min sin intermedio  ·  Clasificación +12"
    ),
    "precio": "Preventa $350 · Estudiantes/INAPAM $245",
}


def _verificar_disco():
    faltantes = [p for p in [FOTO_HERO, BADGE_37, FUENTE_PRIMARIA, FUENTE_SECUNDARIA] if not p.exists()]
    if faltantes:
        detalle = "\n".join(f"  - {p}" for p in faltantes)
        raise SystemExit(f"Falta montar el disco de producción (La Mancha). No se encontró:\n{detalle}")


def cargar_foto_hero() -> Image.Image:
    return Image.open(FOTO_HERO).convert("RGB")


def cargar_badge_37() -> Image.Image:
    badge = Image.open(BADGE_37).convert("RGB")
    alpha = badge.convert("L").point(lambda v: min(255, int(v * 1.6)))
    badge_rgba = badge.copy()
    badge_rgba.putalpha(alpha)
    return badge_rgba


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
    s = h / 7200
    cartel = Image.new("RGB", size, NEGRO)
    draw = ImageDraw.Draw(cartel)

    def linea(texto, y, font, fill, cx):
        bbox = draw.textbbox((0, 0), texto, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw / 2, y), texto, font=font, fill=fill)
        return altura_linea(font)

    # ============ Estructura C: columna central sobre eje, resto = aire ============
    # Presupuesto de área sobre el LIENZO COMPLETO (no la columna): foto ~30%,
    # tipografía principal ~10%, el resto (~60%) queda negro a propósito.
    #
    # Todo el contenido principal (foto + título + info) vive DENTRO de la zona
    # seguro 15%-85% de alto — nunca se calcula una posición "desde arriba" y
    # otra "desde abajo" de forma independiente, porque así fue como el título
    # y los créditos terminaron encimados en el intento anterior. Un solo
    # presupuesto vertical, de arriba hacia abajo, sin excepciones.
    cx = w // 2
    area_total = w * h

    zona_y0 = int(h * 0.15)
    zona_y1 = int(h * 0.85)
    zona_h = zona_y1 - zona_y0

    foto_side = int((area_total * 0.30) ** 0.5)
    foto_side = min(foto_side, int(zona_h * 0.56))  # deja room real para el texto debajo
    marco_x0 = cx - foto_side // 2
    marco_x1 = marco_x0 + foto_side
    marco_y0 = zona_y0
    marco_y1 = marco_y0 + foto_side

    foto = cargar_foto_hero()
    foto = ImageOps.fit(foto, (foto_side, foto_side), method=Image.LANCZOS, centering=(0.5, 0.35))
    cartel.paste(foto, (marco_x0, marco_y0))

    grosor = max(2, int(6 * s))
    draw.rectangle([marco_x0, marco_y0, marco_x1, marco_y1], outline=CREMA, width=grosor)

    badge = cargar_badge_37()
    badge_w = int(w * 0.06)
    badge.thumbnail((badge_w, badge_w), Image.LANCZOS)
    cartel.paste(badge, (marco_x1 - badge.width - int(15 * s), marco_y0 + int(15 * s)), badge)

    # ============ Texto — presupuesto vertical del espacio que QUEDA, no del lienzo ============
    ancho_titulo_max = int(w * 0.60)
    resto_h = zona_y1 - marco_y1  # todo lo que hay entre el pie de la foto y el borde de la zona segura

    # proporciones del espacio restante (suman ~1.0, con gaps incluidos)
    presupuesto = {
        "gap1": 0.09, "titulo": 0.42, "gap2": 0.07,
        "info": 0.13, "gap3": 0.06, "precio": 0.11, "gap4": 0.05, "cta": 0.10,
    }

    def tam_desde_presupuesto(clave):
        return max(10, int(resto_h * presupuesto[clave] / 1.25))  # /1.25: pt -> altura de línea aprox.

    f_titulo = fuente_ajustada(INFO["titulo"], FUENTE_PRIMARIA, tam_desde_presupuesto("titulo"), ancho_titulo_max)
    f_info = fuente_ajustada(INFO["linea_info"], FUENTE_SECUNDARIA, tam_desde_presupuesto("info"), ancho_titulo_max)
    f_precio = fuente_ajustada(INFO["precio"], FUENTE_SECUNDARIA_BOLD, tam_desde_presupuesto("precio"), ancho_titulo_max)
    f_cta = fuente_ajustada(INFO["cta"], FUENTE_SECUNDARIA, tam_desde_presupuesto("cta"), ancho_titulo_max)

    y = marco_y1 + int(resto_h * presupuesto["gap1"])
    y += linea(INFO["titulo"], y, f_titulo, ROJO, cx)
    y += int(resto_h * presupuesto["gap2"])
    y += linea(INFO["linea_info"], y, f_info, CREMA, cx)
    y += int(resto_h * presupuesto["gap3"])
    y += linea(INFO["precio"], y, f_precio, DORADO, cx)
    y += int(resto_h * presupuesto["gap4"])
    linea(INFO["cta"], y, f_cta, DORADO, cx)

    # ============ Letra chica real — créditos técnicos, DENTRO del margen inferior ============
    # Zona exclusiva h*0.85 a h*1.0 — nunca se mezcla con el presupuesto de arriba.
    f_creditos = fuente_ajustada(INFO["creditos"], FUENTE_SECUNDARIA, int(30 * s), int(w * 0.7))
    y_creditos = zona_y1 + (h - zona_y1 - altura_linea(f_creditos)) // 2
    linea(INFO["creditos"], y_creditos, f_creditos, GRIS_FINO, cx)

    if LOGO_SOGEM.exists():
        logo = Image.open(LOGO_SOGEM).convert("RGBA")
        logo_w = int(w * 0.05)
        logo.thumbnail((logo_w, logo_w), Image.LANCZOS)
        cartel.paste(
            logo,
            (w - int(w * 0.05) - logo.width, h - int(h * 0.03) - logo.height),
            logo,
        )

    return cartel


def main():
    _verificar_disco()
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", choices=["print", "preview"], help="generar solo un tamaño")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    formatos = {args.solo: FORMATOS[args.solo]} if args.solo else FORMATOS

    for nombre, size in formatos.items():
        print(f"Generando {nombre} ({size[0]}x{size[1]})...")
        cartel = construir(size)
        out = OUT_DIR / f"cartel-oficial-impreso-2.5x1.5m-{nombre}.png"
        cartel.save(out)
        print(f"  {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
