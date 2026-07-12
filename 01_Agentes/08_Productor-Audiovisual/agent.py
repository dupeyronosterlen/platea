#!/usr/bin/env python3
"""
Agente 08 — Productor Audiovisual / Content
Platea · El Gorila S2 · jul–sep 2026

Genera briefs de contenido para IG/video, analiza performance de IG,
propone conceptos de reel y carrusel alineados con la narrativa de la obra.

Uso:
  python agent.py                     → resumen y checklist de contenido activo
  python agent.py --brief SEMANA      → brief de contenido para la semana indicada
  python agent.py --contenido-base    → conceptos raíz para toda la temporada
  python agent.py --json              → output JSON para CEO (Agente 00)
"""

import os
import sys
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent.parent / "03_Media-Buyer" / ".env"
load_dotenv(ENV_PATH)

IG_USER_ID  = os.getenv("IG_USER_ID", "17841405953353649")
GCP_PROJECT = os.getenv("GCP_PROJECT", "agencia-mkt-ia")

# ─── BASE NARRATIVA S2 ───────────────────────────────────────────────────────
NARRATIVA = {
    "titulo": "El Gorila",
    "subtitulo": "Un monólogo de Humberto Dupeyrón",
    "gancho_principal": "37 años encerrado. Una noche para salir.",
    "referencias": ["Kafka — La Metamorfosis", "identidad", "libertad", "memoria"],
    "tono": "íntimo, provocador, literario con toques de humor oscuro",
    "colores": {"fondo": "#0a0706", "acento": "#D43A1A", "texto": "#F2EDE4"},
    "venue": "Teatro Wilberto Cantón, CDMX",
    "fechas": "Sábados 18:00h — 18 jul a 26 sep 2026",
    "precio": "$350 general / $245 estudiantes",
}

# ─── CONCEPTOS BASE (toda la temporada) ──────────────────────────────────────
CONCEPTOS_BASE = [
    {
        "id": "C01",
        "nombre": "El Conteo",
        "descripcion": "Cuenta regresiva visual: 'Faltan X días para que salga el gorila'",
        "formato": ["Story", "Reel 15s"],
        "cadencia": "Diario, Semana -2 hasta estreno",
        "copy_seed": "37 años esperando. Ya casi.",
        "hashtags": ["#ElGorila", "#MonólogoCDMX", "#TeatroWilbertoCantón"],
    },
    {
        "id": "C02",
        "nombre": "Frases Kafka",
        "descripcion": "Cita de Kafka tipografiada sobre fondo oscuro, sin contexto, que resuena con la obra",
        "formato": ["Post feed cuadrado", "Carrusel 3-5 slides"],
        "cadencia": "2x semana",
        "copy_seed": "Texto de Kafka → silencio → 'El gorila lo entendió'",
        "hashtags": ["#Kafka", "#Teatro", "#Monólogo"],
    },
    {
        "id": "C03",
        "nombre": "Detrás del Gorila",
        "descripcion": "Humberto en proceso: ensayo, backstage, reflexión. Humaniza al actor.",
        "formato": ["Reel 30-60s", "Story serie"],
        "cadencia": "1x semana",
        "copy_seed": "37 años de espera. Estas semanas son los últimos ensayos.",
        "hashtags": ["#Humberto", "#Backstage", "#Teatro"],
    },
    {
        "id": "C04",
        "nombre": "Testimonios S1",
        "descripcion": "Screenshots/reseñas de espectadores de la temporada anterior (con permiso)",
        "formato": ["Carrusel 'Lo que dijeron'", "Story highlight"],
        "cadencia": "1x semana, Semana -1 al estreno",
        "copy_seed": "Ellos ya lo vieron. ¿Y tú?",
        "hashtags": ["#Reseñas", "#ElGorila"],
    },
    {
        "id": "C05",
        "nombre": "Urgencia Boletos",
        "descripcion": "Visual de palcos/butacas disponibles. Número concreto. CTA directo.",
        "formato": ["Story con link", "Reel 15s con texto"],
        "cadencia": "Cada función, 48h y 24h antes",
        "copy_seed": "Quedan X lugares para el sábado. Link en bio.",
        "hashtags": ["#Boletos", "#ElGorila"],
    },
]

# ─── BRIEF SEMANAL ───────────────────────────────────────────────────────────

FUNCIONES_S2 = [
    datetime.date(2026, 7, 18),
    datetime.date(2026, 7, 25),
    datetime.date(2026, 8, 1),
    datetime.date(2026, 8, 8),
    datetime.date(2026, 8, 15),
    datetime.date(2026, 8, 22),
    datetime.date(2026, 8, 29),
    datetime.date(2026, 9, 5),
    datetime.date(2026, 9, 12),
    datetime.date(2026, 9, 19),
    datetime.date(2026, 9, 26),
]


def get_proxima_funcion(hoy: datetime.date) -> tuple:
    """Retorna (proxima_funcion, numero, dias_restantes)."""
    for i, f in enumerate(FUNCIONES_S2):
        if f >= hoy:
            return f, i + 1, (f - hoy).days
    return None, None, None


def run_brief(semana_label: str = "esta semana") -> str:
    hoy = datetime.date.today()
    proxima, num, dias = get_proxima_funcion(hoy)

    urgencia = ""
    if dias is not None:
        if dias <= 2:
            urgencia = f"🔴 URGENTE: Función {num} en {dias} días — activar C05 Urgencia Boletos"
        elif dias <= 7:
            urgencia = f"🟡 Función {num} el sábado — push de boletos esta semana"
        else:
            urgencia = f"🟢 Función {num} en {dias} días — modo calentamiento"

    # Qué publicar según el timing
    if dias is not None and dias > 14:
        plan = [
            "Lun: C02 Frase Kafka — post feed cuadrado",
            "Mié: C03 Detrás del Gorila — reel backstage",
            "Vie: C01 Conteo — story + post feed",
            "Sáb/Dom: C02 segunda frase + story interactivo (pregunta al público)",
        ]
        fase = "Calentamiento"
    elif dias is not None and dias > 7:
        plan = [
            "Lun: C04 Testimonios S1 — carrusel 'Lo que dijeron'",
            "Mar: C01 Conteo — story urgencia",
            "Mié: C03 Detrás del Gorila — reel íntimo",
            "Jue: C02 Frase Kafka",
            "Vie: C05 Urgencia Boletos — story + link en bio",
            "Sáb: Post estreno / recap función anterior (si aplica)",
        ]
        fase = "Pre-función (semana -1)"
    else:
        plan = [
            "48h antes: C05 Urgencia Boletos — '¿Cuántos lugares quedan?'",
            "24h antes: C05 + story countdown",
            "Día función: Story/Reel desde el teatro (call to action último momento)",
            "Post función: Testimonio en tiempo real + agradecimiento",
        ]
        fase = "Función inminente"

    plan_str = "\n".join(f"  {p}" for p in plan)
    conceptos_str = "\n".join(
        f"  [{c['id']}] {c['nombre']} — {c['formato'][0]}\n"
        f"       Copy: \"{c['copy_seed']}\""
        for c in CONCEPTOS_BASE
    )

    return f"""
╔══════════════════════════════════════════════════════════════════╗
║  AGENTE 08 — BRIEF DE CONTENIDO · {semana_label.upper():<28}║
║  El Gorila S2 · {hoy}                                           ║
╚══════════════════════════════════════════════════════════════════╝

ESTADO
  Fase: {fase}
  {urgencia}
  Próxima función: {f'#{num} el {proxima} ({dias} días)' if proxima else 'Temporada concluida'}

PLAN DE PUBLICACIÓN
{plan_str}

SPECS TÉCNICOS IG
  Stories:    1080×1920px · MP4 ≤15s o JPG/PNG
  Reels:      1080×1920px · MP4 30-90s · subtítulos ON (85% sin audio)
  Feed cuad:  1080×1080px
  Carrusel:   hasta 10 slides · 1080×1080px o 1080×1350px
  Colores:    fondo #0a0706 · acento #D43A1A · texto #F2EDE4
  Font:       Georgia / serif elegante

CONCEPTOS BASE DISPONIBLES
{conceptos_str}

REGLAS DE CONTENIDO
  ✓ Precio SIEMPRE visible en posts de conversión ($350 / $245 est.)
  ✓ Link en bio apunta a landing de boletos SIEMPRE
  ✓ Mínimo 1 CTA claro por post de conversión
  ✓ Máx 3-5 hashtags relevantes (no spam)
  ✗ No mencionar aforo total (evitar dar señal de "poca demanda")
  ✗ No postear sin revisar ortografía y tildes

MÉTRICAS A VIGILAR (pedir a Agente 03)
  • Alcance orgánico por formato (reel vs post)
  • CTR stories → link bio
  • Saves + shares (contenido valioso)
  • Comentarios con intención de compra

Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | Agente 08 Productor-AV
"""


def run_contenido_base() -> str:
    hoy = datetime.date.today()
    conceptos_str = ""
    for c in CONCEPTOS_BASE:
        formatos = " | ".join(c["formato"])
        tags = " ".join(c["hashtags"])
        conceptos_str += f"""
  [{c['id']}] {c['nombre'].upper()}
  Descripción: {c['descripcion']}
  Formatos:    {formatos}
  Cadencia:    {c['cadencia']}
  Copy seed:   "{c['copy_seed']}"
  Tags:        {tags}
"""

    return f"""
╔══════════════════════════════════════════════════════════════════╗
║  AGENTE 08 — CONCEPTOS BASE TEMPORADA S2                       ║
║  El Gorila · {hoy}                                              ║
╚══════════════════════════════════════════════════════════════════╝

NARRATIVA CENTRAL
  Gancho:      "{NARRATIVA['gancho_principal']}"
  Tono:        {NARRATIVA['tono']}
  Referencias: {', '.join(NARRATIVA['referencias'])}

{len(CONCEPTOS_BASE)} CONCEPTOS PARA TODA LA TEMPORADA
{conceptos_str}

CALENDARIO DE FUNCIONES (11 sábados 18h)
  {chr(10).join(f"  Función {i+1}: {f}" for i, f in enumerate(FUNCIONES_S2))}

REGLA DE ORO
  Cada semana sin función próxima → contenido de autoridad/narrativa (C01, C02, C03)
  Semana con función → mezclar narrativa + conversión (C04, C05)
  48-24h antes de función → solo conversión urgente (C05)
"""


def run_status() -> str:
    hoy = datetime.date.today()
    proxima, num, dias = get_proxima_funcion(hoy)
    return f"""
╔══════════════════════════════════════════════════════════════════╗
║  AGENTE 08 — PRODUCTOR AUDIOVISUAL                             ║
╚══════════════════════════════════════════════════════════════════╝

ESTADO — {hoy}
  Próxima función: #{num} el {proxima} ({dias} días)
  IG User ID: {IG_USER_ID}

COMANDOS
  python agent.py --brief             → plan de contenido esta semana
  python agent.py --contenido-base    → 5 conceptos para toda la temporada
  python agent.py --json              → datos para Agente 00

CONCEPTOS ACTIVOS: {len(CONCEPTOS_BASE)}
  {', '.join(f"[{c['id']}] {c['nombre']}" for c in CONCEPTOS_BASE)}
"""


def main():
    args = sys.argv[1:]

    if "--contenido-base" in args:
        print(run_contenido_base())
        return

    if "--brief" in args:
        idx = args.index("--brief")
        semana = args[idx + 1] if idx + 1 < len(args) else "esta semana"
        print(run_brief(semana))
        return

    if "--json" in args:
        hoy = datetime.date.today()
        proxima, num, dias = get_proxima_funcion(hoy)
        print(json.dumps({
            "agente": "08_Productor-AV",
            "narrativa": NARRATIVA,
            "conceptos_base": CONCEPTOS_BASE,
            "proxima_funcion": {"fecha": str(proxima), "numero": num, "dias": dias},
            "timestamp": datetime.datetime.now().isoformat(),
        }, ensure_ascii=False, indent=2))
        return

    print(run_status())


if __name__ == "__main__":
    main()
