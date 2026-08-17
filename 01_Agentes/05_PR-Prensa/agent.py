#!/usr/bin/env python3
"""
Agente 05 — PR / Prensa
Platea · El Gorila S2

Genera brief semanal + pitches listos. NUNCA envía correos a medios.
Dirección aprueba y ejecuta el envío (Regla de oro #7).

Uso:
  python3 agent.py              → brief de la semana + top 5 medios
  python3 agent.py --pitches    → 3 pitches (radio / TV / prensa) listos para copiar
  python3 agent.py --json       → JSON para CEO
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "03_Producciones" / "el-gorila" / "campanas" / "pr-briefs"
TRACKER = REPO / "03_Producciones" / "el-gorila" / "campanas" / "s2-medios-offline-lista.md"
_PRODUCCION_ACTIVA = (REPO / "config" / "produccion-activa.txt").read_text().strip()
CONFIG_FILE = REPO / "03_Producciones" / _PRODUCCION_ACTIVA / "produccion.yaml"


def cargar_config() -> dict:
    return yaml.safe_load(CONFIG_FILE.read_text())


CFG = cargar_config()
_TEMPORADA = CFG["temporada"]
_PRECIOS = CFG["precios"]

VENUE_NOMBRE = _TEMPORADA["venue"]["nombre"]
HORARIO = _TEMPORADA["horario"]
DIA_FUNCION = _TEMPORADA["dia_funcion"].capitalize() + "s"   # "Sábado" → "Sábados"

PRECIO_GENERAL = _PRECIOS["general"]
PRECIO_GENERAL_POST = _PRECIOS["general_post_estreno"]
PRECIO_ACADEMIA = _PRECIOS["descuento_academia"]

# Fechas vivas — leídas de 03_Producciones/<produccion-activa>/produccion.yaml (puntero en config/produccion-activa.txt) (fuente única de verdad)
PRENSA = dt.date.fromisoformat(_TEMPORADA["estreno_prensa"])
ESTRENO = dt.date.fromisoformat(_TEMPORADA["estreno"])
CIERRE = dt.date.fromisoformat(_TEMPORADA["temporada_cierre"])
PRESSKIT = "https://elgorilateatro.com.mx/presskit/presskit2026.html"
BOLETOS = (
    "https://elgorilateatro.com.mx/boletos"
    "?utm_source=prensa&utm_medium=earned&utm_campaign=s2_estreno"
)

# Claim seguro (Ag-09 debe validar versión más fuerte)
CLAIM_SEGURO = (
    "Humberto Dupeyrón lleva desde 1989 el monólogo El Gorila "
    "(basado en Informe para una Academia de Franz Kafka): "
    "37 años con el mismo texto — una de las trayectorias más largas "
    "entre un actor y una obra en el teatro mexicano."
)

PRIORIDAD = [
    ("Canal 22", "Nota cultural — ya jaló antes; priorizar follow-up", "A+B"),
    ("Canal Once", "Once Noticias cultural — perfil ideal", "A+B"),
    ("Radio UNAM 96.1", "Entrevista larga Kafka + 37 años", "A+B"),
    ("Radio Educación / IMER", "Cultura / gremio teatral", "A"),
    ("TV UNAM", "Cápsula Kafka + monólogo", "B"),
    ("Chilango / Time Out", "Agenda fin de semana estreno", "C"),
    ("El Universal / La Jornada Cultura", "Nota aniversario/temporada", "A"),
    ("Podcasts teatro/cultura CDMX", "Entrevista remota Humberto 45–60 min", "A+B"),
    ("SOGEM / Wilberto Cantón", "Aliado de venue (no es 'medio'): difusión a socios si hay canal interno", "C"),
    # Cartelera de Teatro CDMX: Dirección reporta que no responden — no priorizar
]


def fase_hoy(hoy: dt.date) -> str:
    if hoy < PRENSA:
        return "pre-prensa"
    if hoy < ESTRENO:
        return "semana-prensa"
    if hoy <= ESTRENO + dt.timedelta(days=7):
        return "post-estreno"
    if hoy <= CIERRE:
        return "temporada"
    return "post-temporada"


def gancho(fase: str) -> str:
    if fase in ("pre-prensa", "semana-prensa"):
        return (
            f"{CLAIM_SEGURO} Estreno al público {ESTRENO.strftime('%-d %b')} "
            f"en el {VENUE_NOMBRE} (SOGEM). "
            f"{DIA_FUNCION} {HORARIO} hasta el {CIERRE.strftime('%-d %b %Y')}."
        )
    if fase == "post-estreno":
        return (
            f"{CLAIM_SEGURO} Ya en temporada en el {VENUE_NOMBRE} — "
            f"{DIA_FUNCION.lower()} {HORARIO}. "
            f"Boletos: {BOLETOS}"
        )
    return (
        f"{CLAIM_SEGURO} Temporada en curso, {VENUE_NOMBRE}, "
        f"{DIA_FUNCION.lower()} {HORARIO} "
        f"hasta el {CIERRE.strftime('%-d %b %Y')}."
    )


def pitches(fase: str) -> list[dict]:
    """Pitches listos para que Dirección copie/envíe.

    Timing (16 jul+): NO invitar a la función privada del 18 como gancho
    principal — queda ≤48h; es tarde para agenda de medios. Ángulo:
    entrevista/nota + cortesía al estreno público 25 jul (o temporada).
    El 18 solo se menciona si el medio ya estaba en lista / puede llegar.
    """
    g = gancho(fase)
    precios = (
        f"Preventa ${PRECIO_GENERAL} (hasta el {ESTRENO.strftime('%-d %b')} inclusive) · "
        f"regular ${PRECIO_GENERAL_POST} · "
        f"estudiante/maestro/INAPAM ${PRECIO_ACADEMIA}"
    )
    return [
        {
            "canal": "Radio (UNAM / Educación / IMER)",
            "asunto": "Entrevista: 37 años con El Gorila — Humberto Dupeyrón",
            "cuerpo": (
                f"Buen día,\n\n"
                f"Les escribo por una nota de trayectoria, no de cartelera: {g}\n\n"
                f"¿Tendrían 20–30 min esta semana o la próxima para una entrevista "
                f"(presencial o remota) con Humberto Dupeyrón?\n\n"
                f"Si les sirve cobertura en vivo: estreno al público "
                f"{ESTRENO.strftime('%d/%m')} · {DIA_FUNCION.lower()} {HORARIO} · {VENUE_NOMBRE}. "
                f"(La función del {PRENSA.strftime('%d/%m')} es privada de prensa; "
                f"si aún pueden llegar, avísennos y vemos cortesía.)\n\n"
                f"Presskit: {PRESSKIT}\n"
                f"Boletos (para mención): {BOLETOS}\n"
                f"{precios}\n\n"
                f"Quedo atento.\n"
                f"— Producción El Gorila / comunicaciones@elgorilateatro.com.mx"
            ),
        },
        {
            "canal": "TV cultural (Once / 22 / TV UNAM)",
            "asunto": f"Nota cultural: 37 años de El Gorila — estreno {ESTRENO.strftime('%-d %b')} {VENUE_NOMBRE}",
            "cuerpo": (
                f"Buen día,\n\n"
                f"Propuesta de nota/cápsula: {g}\n\n"
                f"Invitación principal: estreno al público "
                f"{ESTRENO.strftime('%d/%m')} ({DIA_FUNCION.lower()} {HORARIO}, temporada hasta "
                f"{CIERRE.strftime('%d/%m')}). Presskit y fotos listos; "
                f"cortesías de prensa disponibles para esa función o otra de temporada.\n\n"
                f"Nota: el {PRENSA.strftime('%d/%m')} es ensayo/prensa privada — "
                f"si su agenda ya estaba cerrada para ese día, no hay problema; "
                f"el 25 es el estreno que conviene cubrir.\n\n"
                f"Presskit: {PRESSKIT}\n"
                f"{precios}\n\n"
                f"¿Les interesa una pieza corta esta semana?\n"
                f"— Producción El Gorila / comunicaciones@elgorilateatro.com.mx"
            ),
        },
        {
            "canal": "Prensa escrita / digital",
            "asunto": "37 años con un monólogo de Kafka — temporada en SOGEM",
            "cuerpo": (
                f"Buen día,\n\n"
                f"{g}\n\n"
                f"Material: {PRESSKIT}\n"
                f"Datos: {DIA_FUNCION.lower()} {HORARIO} · {VENUE_NOMBRE} · "
                f"{precios} · {BOLETOS}\n"
                f"Estreno público: {ESTRENO.strftime('%d/%m')} "
                f"(mejor fecha para cobertura; el {PRENSA.strftime('%d/%m')} "
                f"es privado).\n\n"
                f"¿Puedo mandar un párrafo + fotos en alta para su sección Cultura?\n"
                f"— Producción El Gorila / comunicaciones@elgorilateatro.com.mx"
            ),
        },
    ]


def build_brief(hoy: dt.date) -> str:
    fase = fase_hoy(hoy)
    lines = [
        f"# Brief PR — {hoy.isoformat()} · fase **{fase}**",
        "> Agente 05 · BORRADOR — Dirección aprueba antes de contactar medios",
        "",
        "## Gancho de la semana",
        gancho(fase),
        "",
        "## ⛔ Claims prohibidos hasta Ag-09",
        "- «Récord mundial» / Guinness / «el más largo del mundo»",
        "- Función o placa el **26 de septiembre** (temporada cierra **19 sep**)",
        "",
        "## Top 5 medios a contactar (esta semana)",
    ]
    for i, (medio, accion, angulos) in enumerate(PRIORIDAD[:5], 1):
        lines.append(f"{i}. **{medio}** — {accion} · ángulos {angulos}")
    lines += [
        "",
        "## Material",
        f"- Presskit: {PRESSKIT}",
        f"- Boletos+UTM: {BOLETOS}",
        f"- Tracker: `{TRACKER.relative_to(REPO)}`",
        "",
        "## Siguiente paso humano",
        "1. Dirección elige 2–3 medios y pega el pitch de `--pitches`.",
        "2. Anota respuesta en el tracker.",
        "3. Si agendan: avisar Ag-03 (Search marca) + Ag-08 (fotos).",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pitches", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    hoy = dt.date.today()
    fase = fase_hoy(hoy)

    if args.json:
        print(
            json.dumps(
                {
                    "agente": "05",
                    "fecha": hoy.isoformat(),
                    "fase": fase,
                    "gancho": gancho(fase),
                    "top5": [
                        {"medio": m, "accion": a, "angulos": ang}
                        for m, a, ang in PRIORIDAD[:5]
                    ],
                    "pitches": pitches(fase),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.pitches:
        print(f"=== PITCHES PR · {hoy} · fase {fase} ===\n")
        print("⛔ No enviar sin OK de Dirección.\n")
        for p in pitches(fase):
            print(f"--- {p['canal']} ---")
            print(f"Asunto: {p['asunto']}\n")
            print(p["cuerpo"])
            print()
        return

    brief = build_brief(hoy)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{hoy.isoformat()}_ag05_brief-pr.md"
    out.write_text(brief, encoding="utf-8")
    print(brief)
    print(f"\n💾 {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
