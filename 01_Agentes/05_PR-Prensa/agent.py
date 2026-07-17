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

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "03_Producciones" / "el-gorila" / "campanas" / "pr-briefs"
TRACKER = REPO / "03_Producciones" / "el-gorila" / "campanas" / "s2-medios-offline-lista.md"

# Fechas vivas (sincronizar con plaza-activa si cambian)
PRENSA = dt.date(2026, 7, 18)
ESTRENO = dt.date(2026, 7, 25)
CIERRE = dt.date(2026, 9, 19)
PRESSKIT = "https://elgorilateatro.com.mx/presskit/"
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
            f"{CLAIM_SEGURO} Función de prensa {PRENSA.strftime('%-d %b')}; "
            f"estreno al público {ESTRENO.strftime('%-d %b')} en el Teatro Wilberto Cantón (SOGEM). "
            f"Sábados 18:00 hasta el {CIERRE.strftime('%-d %b %Y')}."
        )
    if fase == "post-estreno":
        return (
            f"{CLAIM_SEGURO} Ya en temporada en el Wilberto Cantón — sábados 18:00. "
            f"Boletos: {BOLETOS}"
        )
    return (
        f"{CLAIM_SEGURO} Temporada en curso, Wilberto Cantón, sábados 18:00 "
        f"hasta el {CIERRE.strftime('%-d %b %Y')}."
    )


def pitches(fase: str) -> list[dict]:
    g = gancho(fase)
    return [
        {
            "canal": "Radio (UNAM / Educación / IMER)",
            "asunto": "Entrevista: 37 años con El Gorila — Humberto Dupeyrón",
            "cuerpo": (
                f"Buen día,\n\n"
                f"Les escribo por una nota de trayectoria, no de cartelera: {g}\n\n"
                f"¿Tendrían 20–30 min esta semana o la próxima para una entrevista "
                f"(presencial o remota) con Humberto Dupeyrón?\n\n"
                f"Presskit: {PRESSKIT}\n"
                f"Boletos (para mención): {BOLETOS}\n\n"
                f"Quedo atento.\n"
                f"— Producción El Gorila / comunicaciones@elgorilateatro.com.mx"
            ),
        },
        {
            "canal": "TV cultural (Once / 22 / TV UNAM)",
            "asunto": "Nota cultural: 37 años de El Gorila en el Wilberto Cantón",
            "cuerpo": (
                f"Buen día,\n\n"
                f"Propuesta de nota/cápsula: {g}\n\n"
                f"Disponemos de presskit, fotos y acceso a función de prensa "
                f"({PRENSA.strftime('%d/%m')}) o a temporada.\n\n"
                f"Presskit: {PRESSKIT}\n\n"
                f"¿Les interesa una pieza corta esta semana?\n"
                f"— Producción El Gorila"
            ),
        },
        {
            "canal": "Prensa escrita / digital",
            "asunto": "37 años con un monólogo de Kafka — temporada en SOGEM",
            "cuerpo": (
                f"Buen día,\n\n"
                f"{g}\n\n"
                f"Material: {PRESSKIT}\n"
                f"Datos: sábados 18:00 · Teatro Wilberto Cantón · "
                f"preventa $350 hasta el 25 jul · {BOLETOS}\n\n"
                f"¿Puedo mandar un párrafo + fotos en alta para su sección Cultura?\n"
                f"— Producción El Gorila"
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
