#!/usr/bin/env python3
"""
Agente 11 — Business Development
Platea · El Gorila S2 · jul–sep 2026

Identifica y califica oportunidades de bolos (festivales, giras, eventos especiales,
teatros socios). Propone prospectos calificados a Dirección → él aprueba → Agente 10 coordina.

Criterios de calificación:
  - Aforo: 80-500 personas (viable para El Gorila)
  - Ventana: disponibilidad compatible con calendario S2
  - Rider: requiere solo 1 actor + escenografía mínima (Humberto)
  - Fit narrativo: audiencia teatral/cultural

⚠️ PRICING — INFORMACIÓN INTERNA CONFIDENCIAL:
  $25,000 MXN CDMX (incluye técnico)
  $50,000 MXN exterior (sin viáticos)
  Precio adhoc: ×3 para teatros grandes o festivales premium
  NUNCA revelar a prospectos. Dirección fija y negocia el precio.

Uso:
  python agent.py                     → estado del pipeline de prospección
  python agent.py --nichos            → nichos calientes a explorar
  python agent.py --calificar NOMBRE  → calificar un prospecto específico
  python agent.py --reporte           → reporte de oportunidades activas
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

GCP_PROJECT = os.getenv("GCP_PROJECT", "agencia-mkt-ia")

# ─── PRICING (INTERNO — NUNCA REVELAR A PROSPECTOS) ──────────────────────────
_PRICING_INTERNO = {
    "cdmx_base": 25000,
    "exterior_base": 50000,
    "adhoc_multiplier": 3,
    "nota": "CONFIDENCIAL — Dirección fija precio y negocia. No incluir en ningún output externo.",
}

# ─── CRITERIOS DE CALIFICACIÓN ────────────────────────────────────────────────
CRITERIOS = {
    "aforo_min": 80,
    "aforo_max": 500,
    "rider_tecnico": "1 actor, escenografía mínima, 1 foco cenitial, sistema de audio básico",
    "duracion_funcion_min": 60,
    "duracion_funcion_max": 90,
    "publico_objetivo": ["teatro", "cultura", "literatura", "adultos 30-65"],
    "idioma": "español",
}

# ─── NICHOS CALIENTES ─────────────────────────────────────────────────────────
NICHOS = [
    {
        "nicho": "Festivales de teatro iberoamericano",
        "ejemplos": ["FIT Cádiz", "FIBA Buenos Aires", "Festival Cervantino Guanajuato"],
        "razon": "Perfil exacto: monólogo literario, actor reconocido, obra con referencia kafkiana",
        "timing": "Convocatorias oct-dic para ciclo siguiente — prospección fuera de temporada S2",
        "prioridad": "ALTA",
    },
    {
        "nicho": "Teatros socios CDMX (función especial)",
        "ejemplos": ["Teatro Insurgentes", "Teatro Milán", "Teatro de los Insurgentes"],
        "razon": "Función especial gala/beneficio sin conflicto con Wilberto Cantón",
        "timing": "Flexible — agendar después de octubre 2026",
        "prioridad": "MEDIA",
    },
    {
        "nicho": "Corporativos culturales / RSE",
        "ejemplos": ["Bancomer/BBVA Cultura", "Fundación Televisa", "empresas con programas culturales"],
        "razon": "Función privada con Q&A → ingreso adicional sin conflicto boletería",
        "timing": "Flexible, checar disponibilidad Humberto",
        "prioridad": "MEDIA",
    },
    {
        "nicho": "Gira Monterrey / Guadalajara",
        "ejemplos": ["Teatro Monterrey", "Teatro Diana GDL", "Auditorio Telmex (sala pequeña)"],
        "razon": "Mercados naturales de expansión post-CDMX, base de fans de Humberto",
        "timing": "Post-temporada S2 (oct 2026 en adelante)",
        "prioridad": "ALTA",
    },
    {
        "nicho": "Universidades / UNAM / Ibero / TEC",
        "ejemplos": ["Teatro Juan Ruiz de Alarcón UNAM", "Auditorio Ibero", "salas TEC campus"],
        "razon": "Precio accesible, audiencia joven + académica, cuadra con narrativa kafkiana",
        "timing": "Semestres ago-nov 2026 o ene-may 2027",
        "prioridad": "MEDIA",
    },
]

# ─── LISTA DE INVESTIGACIÓN (archivo de prospectos BD) ───────────────────────
LISTA_FILE = Path(__file__).parent / "lista-investigacion.md"


def load_lista() -> str:
    if LISTA_FILE.exists():
        return LISTA_FILE.read_text()
    return ""


def calificar_prospecto(nombre: str) -> str:
    hoy = datetime.date.today()
    return f"""
╔══════════════════════════════════════════════════════════════════╗
║  AGENTE 11 — CALIFICACIÓN: {nombre.upper():<36}║
║  {hoy}                                                          ║
╚══════════════════════════════════════════════════════════════════╝

CHECKLIST DE CALIFICACIÓN
─────────────────────────────────────────────────────────────────
Para calificar "{nombre}", se necesita responder:

□ ¿Cuál es el aforo del espacio? (objetivo: {CRITERIOS['aforo_min']}-{CRITERIOS['aforo_max']} personas)
□ ¿Qué tipo de audiencia tiene? (objetivo: {', '.join(CRITERIOS['publico_objetivo'])})
□ ¿Tienen programación cultural o de teatro?
□ ¿Cuál es la ventana de disponibilidad? (¿compatible con S2 El Gorila?)
□ ¿Quién es el contacto/programador?
□ ¿Tienen presupuesto para cachet? (sin revelar nuestro precio)
□ ¿El rider técnico es viable? ({CRITERIOS['rider_tecnico']})

CALIFICACIÓN (completar manualmente con Dirección):
  Aforo:        [ ] OK  [ ] No aplica   Dato: ___
  Audiencia:    [ ] OK  [ ] No aplica
  Ventana:      [ ] OK  [ ] No aplica   Fechas: ___
  Presupuesto:  [ ] OK  [ ] No aplica   (aproximado sin revelar precio)
  Rider:        [ ] OK  [ ] No aplica

RESULTADO POSIBLE:
  ✅ VERDE  — 4-5 criterios OK → enviar a Agente 10 para coordinar
  🟡 AMARILLO — 2-3 criterios OK → requiere más información antes de proceder
  🔴 ROJO   — <2 criterios OK → descartar o posponer

⚠️ RECUERDA: Dirección fija el precio. No cotizar hasta que Dirección lo apruebe.
Para este prospecto: pedir brief a Dirección antes de hacer contacto.
"""


def run_nichos() -> str:
    hoy = datetime.date.today()
    lines = [
        f"\n╔══════════════════════════════════════════════════════════════════╗",
        f"║  AGENTE 11 — NICHOS CALIENTES · {hoy}                          ║",
        f"╚══════════════════════════════════════════════════════════════════╝\n",
        f"Criterios de calificación:",
        f"  Aforo:   {CRITERIOS['aforo_min']}-{CRITERIOS['aforo_max']} personas",
        f"  Público: {', '.join(CRITERIOS['publico_objetivo'])}",
        f"  Rider:   {CRITERIOS['rider_tecnico']}",
        "",
    ]

    for n in sorted(NICHOS, key=lambda x: 0 if x["prioridad"] == "ALTA" else 1):
        icon = "🔥" if n["prioridad"] == "ALTA" else "🎯"
        lines.append(f"{icon} [{n['prioridad']}] {n['nicho'].upper()}")
        lines.append(f"   Razón:   {n['razon']}")
        lines.append(f"   Timing:  {n['timing']}")
        lines.append(f"   Ejemplos: {', '.join(n['ejemplos'][:2])}")
        lines.append("")

    lines.append("Para investigar un prospecto específico:")
    lines.append("  python agent.py --calificar 'Nombre del lugar'")
    return "\n".join(lines)


def run_reporte() -> str:
    hoy = datetime.date.today()
    lista = load_lista()
    lista_preview = lista[:500] + "..." if len(lista) > 500 else lista if lista else "(sin prospectos en lista)"

    return f"""
╔══════════════════════════════════════════════════════════════════╗
║  AGENTE 11 — REPORTE BUSINESS DEV · {hoy}                      ║
╚══════════════════════════════════════════════════════════════════╝

TEMPORADA S2 ACTIVA: 18 jul – 26 sep 2026
Los bolos confirmados para S2 deben NO conflictuar con funciones de sábado en Wilberto Cantón.
Los bolos de gira (exterior) son para POST S2: octubre 2026 en adelante.

NICHOS PRIORITARIOS ACTIVOS
  🔥 Festivales de teatro iberoamericano — prospección Q4 2026
  🔥 Gira MTY/GDL — post-temporada oct 2026
  🎯 Corporativos culturales — flexible, cualquier momento
  🎯 Universidades — según semestre

LISTA DE INVESTIGACIÓN ACTUAL
──────────────────────────────
{lista_preview}

SIGUIENTE ACCIÓN RECOMENDADA
  1. Verificar si lista-investigacion.md tiene prospectos activos
  2. Calificar los TOP 3 con más potencial
  3. Proponer a Dirección los calificados → él aprueba → Agente 10 coordina

Precio siempre lo fija Dirección. Nunca cotizar de forma autónoma.

Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | Agente 11 Business Dev
"""


def run_status() -> str:
    hoy = datetime.date.today()
    lista = load_lista()
    return f"""
╔══════════════════════════════════════════════════════════════════╗
║  AGENTE 11 — BUSINESS DEVELOPMENT                              ║
╚══════════════════════════════════════════════════════════════════╝

ESTADO — {hoy}
  Lista investigación: {'✅ Con datos' if lista else '⏳ Vacía — llenar lista-investigacion.md'}
  Nichos identificados: {len(NICHOS)}
  Alta prioridad: {sum(1 for n in NICHOS if n['prioridad'] == 'ALTA')}

COMANDOS
  python agent.py --nichos                  → nichos calientes
  python agent.py --calificar "Nombre"      → calificar prospecto
  python agent.py --reporte                 → resumen de oportunidades
  python agent.py --json                    → datos para Agente 00

REGLA: Prospectos calificados → Dirección aprueba → Agente 10 coordina
       Precio: CONFIDENCIAL — solo Dirección fija y negocia
"""


def main():
    args = sys.argv[1:]

    if "--nichos" in args:
        print(run_nichos())
        return

    if "--calificar" in args:
        idx = args.index("--calificar")
        nombre = args[idx + 1] if idx + 1 < len(args) else "Prospecto sin nombre"
        print(calificar_prospecto(nombre))
        return

    if "--reporte" in args:
        print(run_reporte())
        return

    if "--json" in args:
        print(json.dumps({
            "agente": "11_Business-Dev",
            "nichos": NICHOS,
            "criterios_calificacion": CRITERIOS,
            "timestamp": datetime.datetime.now().isoformat(),
            # NOTA: _PRICING_INTERNO NO se incluye en JSON externo
        }, ensure_ascii=False, indent=2))
        return

    print(run_status())


if __name__ == "__main__":
    main()
