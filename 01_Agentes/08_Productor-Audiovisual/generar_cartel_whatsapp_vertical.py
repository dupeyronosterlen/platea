#!/usr/bin/env python3
"""
Versión vertical (9:16) del póster general para el ad de WhatsApp de
EG_S2_MENSAJES. Agente: 08 Productor Audiovisual.

La primera versión de este script recortaba Poster.png (ya aplanado, formato
retrato 5400x7200) desde arriba — igual que generar_cartel_ticketmaster_
opcionB.py — pero Poster.png solo muestra la MITAD humana de la cara (la
mitad gorila queda fuera de su encuadre, ver README de poster-elementos-
sueltos/). Para un formato vertical nuevo eso se veía peor que el póster
general de referencia (que sí muestra las dos mitades).

Esta versión arma la pieza desde los ELEMENTOS SUELTOS (imagen sin marco +
capas de texto extraídas del PSD, en 05_Activos/el-gorila/poster-elementos-
sueltos/) en vez de recortar el JPEG aplanado:
- La imagen (mono-pintura-completa-sin-marco.png) se usa completa —ambas
  mitades— recortando solo fondo sobrante a los lados (nunca la cara), y se
  ESCALA (no se comprime ni se recorta el sujeto) para caber a lo ancho.
- El texto va en bloques apilados arriba/abajo de la imagen, cada uno en su
  propia banda vertical — nunca encima de la imagen ni de otro bloque — así
  no hay riesgo de que se encime como pasaba al forzar el recorte horizontal
  original a un lienzo vertical.

Uso:
    python3 generar_cartel_whatsapp_vertical.py

Auditoría (correr después, siempre):
    python3 .claude/skills/cartel-diseno-teoria/scripts/auditar_cartel.py <ruta.png>
"""

from pathlib import Path
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "05_Activos/el-gorila"
ELEMENTOS = ASSETS / "poster-elementos-sueltos"
OUT_DIR = ASSETS / "carteles-s2/whatsapp-mensajes"

IMG_FUENTE = ELEMENTOS / "imagen/mono-pintura-completa-sin-marco.png"
TXT = ELEMENTOS / "texto"

NEGRO = (10, 7, 6)

SIZE = (1080, 1920)

# Recorte SOLO de fondo sobrante a los lados (fracciones del ancho original,
# 10680px) — calibrado visualmente contra el thumbnail: la figura (cara +
# birrete + hombros) vive entre ~0.15 y ~0.95 del ancho. No se toca el alto,
# así nunca se corta cabeza/torso.
RECORTE_X = (0.15, 0.95)

# Ancho de cada capa de texto como fracción del canvas (1080) — controla el
# tamaño relativo entre bloques sin depender del tamaño de fuente original.
ANCHO_HUMBERTO_EN = 0.68
ANCHO_TITULO = 0.62
ANCHO_KAFKA = 0.40
ANCHO_HORARIO = 0.42
ANCHO_VENUE = 0.58

GAP_CHICO = 16
GAP_MEDIANO = 36


def _cargar(nombre: str) -> Image.Image:
    return Image.open(TXT / nombre).convert("RGBA")


def _escalar_a_ancho(im: Image.Image, ancho_destino: int) -> Image.Image:
    escala = ancho_destino / im.width
    return im.resize((ancho_destino, max(1, int(im.height * escala))), Image.LANCZOS)


def construir() -> Image.Image:
    w, h = SIZE
    cartel = Image.new("RGB", SIZE, NEGRO)

    # --- imagen: ambas mitades completas, solo se recorta fondo lateral ---
    fuente = Image.open(IMG_FUENTE).convert("RGBA")
    fw, fh = fuente.size
    x0, x1 = int(fw * RECORTE_X[0]), int(fw * RECORTE_X[1])
    figura = fuente.crop((x0, 0, x1, fh))
    figura = _escalar_a_ancho(figura, w)

    # --- capas de texto, cada una escalada a su propio ancho relativo ---
    humberto_en = _escalar_a_ancho(_cargar("humberto-dupeyron-en.png"), int(w * ANCHO_HUMBERTO_EN))
    titulo = _escalar_a_ancho(_cargar("el-gorila.png"), int(w * ANCHO_TITULO))
    kafka = _escalar_a_ancho(_cargar("de-franz-kafka.png"), int(w * ANCHO_KAFKA))
    horario = _escalar_a_ancho(_cargar("horario-sabados-18hrs.png"), int(w * ANCHO_HORARIO))
    venue = _escalar_a_ancho(_cargar("venue-teatro-wilberto-canton.png"), int(w * ANCHO_VENUE))

    bloque_arriba_h = humberto_en.height + GAP_CHICO + titulo.height + GAP_CHICO + kafka.height
    bloque_abajo_h = horario.height + GAP_CHICO + venue.height

    alto_total = bloque_arriba_h + GAP_MEDIANO + figura.height + GAP_MEDIANO + bloque_abajo_h
    y = (h - alto_total) // 2  # centrado vertical → aire parejo arriba/abajo

    def pegar_centrado(capa: Image.Image, y: int) -> int:
        x = (w - capa.width) // 2
        cartel.paste(capa, (x, y), capa)
        return y + capa.height

    y = pegar_centrado(humberto_en, y) + GAP_CHICO
    y = pegar_centrado(titulo, y) + GAP_CHICO
    y = pegar_centrado(kafka, y) + GAP_MEDIANO

    x_img = (w - figura.width) // 2
    cartel.paste(figura.convert("RGB"), (x_img, y))
    y += figura.height + GAP_MEDIANO

    y = pegar_centrado(horario, y) + GAP_CHICO
    y = pegar_centrado(venue, y)

    return cartel


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cartel = construir()
    out = OUT_DIR / f"whatsapp-vertical-{SIZE[0]}x{SIZE[1]}.jpg"
    cartel.save(out, quality=92)
    print(f"Generado: {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
