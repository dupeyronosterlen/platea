#!/usr/bin/env python3
"""
Agente 15 — Arquitecto de Procesos · Platea
============================================
Interlocutor conversacional para Dirección. No monitorea en tiempo real ni ejecuta cambios.
Sirve para entender el sistema, detectar fugas en el funnel, generar hipótesis y
proponer mejoras documentadas. Siempre Dirección / CEO 00 deciden.

USO:
  python agent.py --pregunta "¿en qué etapa del funnel se cae más gente?"
  python agent.py --auditoria            # auditoría completa del sistema
  python agent.py --hipotesis            # top hipótesis priorizadas (requiere datos boletera)
  python agent.py --flujo ciclo-campana  # explica un workflow específico
  python agent.py --gaps                 # agentes y flujos faltantes / incompletos
  python agent.py --estado               # estado actual de todos los agentes
"""

import os
import sys
import json
import subprocess
import argparse
import textwrap
from datetime import datetime
from pathlib import Path

# ─── CONFIG ──────────────────────────────────────────────────────────────────
GCP_PROJECT   = os.getenv("GCP_PROJECT", "agencia-mkt-ia")
GEMINI_MODEL  = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
BOLETERA_URL  = os.getenv("BOLETERA_URL", "https://elgorila-api.dupeyronosterlen.workers.dev")
RESEND_KEY    = os.getenv("RESEND_API_KEY")
ALERT_EMAIL   = os.getenv("ALERT_EMAIL", "elgorilateatro@gmail.com")

# Ruta raíz de la agencia (relativa al script)
AGENCIA_ROOT  = Path(__file__).parent.parent.parent  # → _PARA-AGENCIA/

# ─── CONTEXTO DE LA AGENCIA ──────────────────────────────────────────────────
AGENTES = {
    "00": ("CEO / Estratega",         "Descompone tareas, primer punto de contacto, aprobación final"),
    "01": ("Director Creativo",       "Brief creativo, dirección visual, aprobación de assets"),
    "02": ("Copywriter",              "Copy para ads, posts, emails, cartelería"),
    "03": ("Media Buyer",             "Campañas Meta Ads y Google Ads — autónomo con alertas"),
    "04": ("Community Manager",       "Calendario editorial, posts IG/TikTok/FB"),
    "05": ("PR / Prensa",             "Earned media, comunicados, relaciones con prensa"),
    "06": ("Analytics y BI",          "Reportes, análisis de CPA, dashboards"),
    "07": ("CRM / Email",             "Resend + lista BUYERS"),
    "08": ("Productor Audiovisual",   "Edición de video y foto"),
    "09": ("Investigador de Mercado", "Estudios de plaza, competencia, tendencias"),
    "10": ("Coordinación Booking",    "Coordina bolos cerrados, apoya a 11"),
    "11": ("Booking / Business Dev",  "Caza venues, festivales, coproductores"),
    "12": ("Boletera",                "Funciones, ocupación, alertas — autónomo con alertas"),
    "13": ("Programador",             "Worker Cloudflare, Stripe, sitio, APIs"),
    "14": ("Gorila Digital",          "Personaje IA El Gorila + carteles (Gemini Imagen)"),
    "15": ("Arquitecto de Procesos",  "Diseña/audita flujos, hipótesis priorizadas, gap analysis"),
}

WORKFLOWS_DIR = AGENCIA_ROOT / "06_Workflows"
OPERACIONES_DIR = AGENCIA_ROOT / "04_Operaciones"

FLUJOS_EXISTENTES = [
    "arranque/A-nueva-plaza.md",
    "arranque/B-activacion-campana.md",
    "arranque/C-alerta-rendimiento.md",
    "arranque/D-reporte-semanal.md",
    "ciclo-campana.md",
    "crisis.md",
    "lanzamiento-obra.md",
    "nueva-plaza.md",
    "onboarding-cliente-b2b.md",
    "preguntas-vivas.md",
    "produccion-contenido-organico.md",
    "protocolo-escalado-whatsapp.md",
    "reporte-semanal.md",
]

GAPS_CONOCIDOS = {
    "agentes_sin_script": [
        ("00", "CEO — solo persona.md + playbook, sin agent.py. ¿Quién ejecuta la orquestación?"),
        ("01", "Director Creativo — sin agent.py. Bloquea pipeline creativo autónomo"),
        ("02", "Copywriter — sin agent.py. Copy generado manualmente en cada sesión"),
        ("04", "Community Manager — sin agent.py. Calendario editorial no automatizado"),
        ("05", "PR — sin agent.py. Outreach a prensa es 100% manual"),
        ("06", "Analytics BI — sin agent.py. Reportes GA4/Meta requieren sesión manual"),
        ("07", "CRM — sin agent.py. Resend y lista BUYERS se gestionan manualmente"),
        ("08", "Audiovisual — sin agent.py. Edición es manual por diseño"),
        ("09", "Investigador — sin agent.py. El activo de datos históricos S1 no está procesado"),
        ("11", "Booking — sin agent.py. Pipeline B2B completamente manual"),
        ("14", "Gorila Digital — sin agent.py. Generación de personaje ad-hoc"),
    ],
    "flujos_faltantes": [
        ("Escalado de crisis B2B", "Qué pasa si un cliente externo tiene un incidente — no documentado"),
        ("Cierre de temporada", "Qué hace la agencia al terminar S2: archiving, postmortem, datos"),
        ("Pipeline de contenido orgánico → paid", "Cómo un post orgánico que funciona escala a anuncio"),
        ("Gestión de datos históricos", "Pipeline: CSV ventas S1 → Custom Audiences → Lookalike"),
        ("Onboarding nuevo activo creativo", "Cómo entra un video/foto nuevo al sistema y llega a ads"),
        ("Reporte express miércoles", "Función del día: ocupación previa + qué hacer antes de las 8:30pm"),
        ("Protocolo de descuento reactivo", "Cuándo y cómo activar ESPEJO2/ACADEMIA sin manual de Dirección"),
        ("Flujo de aprobación de copy", "Draft → Dirección aprueba → publica. Hoy no está formalizado"),
    ],
    "datos_bloqueantes": [
        ("Datos históricos S1", "154 emails de compradores no procesados — el activo más valioso sin usar"),
        ("/api/reporte endpoint", "Sin este endpoint, el CPA que reporta Agente 03 es estimado, no real"),
        ("Pixel Purchase", "Sin verificar en elgorilateatro.com.mx — bloquea Arranque B y audiencias"),
        ("Stripe modo producción", "No confirmado si está en cs_test_ o producción"),
        ("Variables de entorno", "SYSTEM_USER_ACCESS_TOKEN, GOOGLE_ADS_*, RESEND_API_KEY no confirmados"),
    ],
}

# ─── GEMINI ──────────────────────────────────────────────────────────────────
def llamar_gemini(prompt: str) -> str:
    try:
        import google.generativeai as genai
        from google.auth import default
        creds, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        genai.configure(credentials=creds)
        model = genai.GenerativeModel(GEMINI_MODEL)
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except ImportError:
        return _fallback_sin_gemini(prompt)
    except Exception as e:
        return f"[Gemini no disponible: {e}]\n\n{_fallback_sin_gemini(prompt)}"


def _fallback_sin_gemini(prompt: str) -> str:
    """Respuesta estructurada local si Gemini no está disponible."""
    return (
        "⚠️  Gemini no conectado — análisis local únicamente.\n"
        "Configura credenciales GCP: gcloud auth application-default login\n\n"
        + prompt[:200] + "..."
    )


# ─── DATOS EN VIVO ───────────────────────────────────────────────────────────
def obtener_boletera_json() -> dict:
    """Llama a Agente 12 en modo --json para datos de boletera."""
    agente12 = Path(__file__).parent.parent / "12_Boletera" / "agent.py"
    if not agente12.exists():
        return {"error": "Agente 12 no encontrado", "funciones": []}
    try:
        result = subprocess.run(
            [sys.executable, str(agente12), "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"error": result.stderr, "funciones": []}
    except Exception as e:
        return {"error": str(e), "funciones": []}


def leer_workflow(nombre: str) -> str:
    """Lee el contenido de un workflow por nombre parcial."""
    for flujo in FLUJOS_EXISTENTES:
        if nombre.lower() in flujo.lower():
            ruta = WORKFLOWS_DIR / flujo
            if ruta.exists():
                return ruta.read_text()
    return f"Workflow '{nombre}' no encontrado. Disponibles: {', '.join(FLUJOS_EXISTENTES)}"


def cargar_reglas_decision() -> str:
    ruta = OPERACIONES_DIR / "reglas-de-decision.md"
    return ruta.read_text() if ruta.exists() else ""


def cargar_contexto_completo() -> str:
    """Construye el contexto completo de la agencia para Gemini."""
    partes = []

    # Agentes
    partes.append("## AGENTES PLATEA (16 activos)")
    for num, (nombre, func) in AGENTES.items():
        partes.append(f"  {num}. {nombre}: {func}")

    # Reglas de decisión
    reglas = cargar_reglas_decision()
    if reglas:
        partes.append("\n## REGLAS DE DECISIÓN")
        partes.append(reglas[:2000])  # No saturar el contexto

    # Estado S2
    partes.append("\n## CONTEXTO S2 ACTIVO")
    partes.append("- Obra: El Gorila — Humberto Dupeyrón")
    partes.append("- Venue: Teatro Wilberto Cantón (SOGEM), CDMX")
    partes.append("- 11 funciones: sábados 18:00h, desde 18 jul 2026 (cierre por confirmar)")
    partes.append("- Aforo: 325 localidades (~280 vendibles)")
    partes.append("- Precio: $350 MXN general / $245 MXN descuento")
    partes.append("- CPA objetivo: ≤ $350 MXN (medido en boletera, no en Meta/Google)")
    partes.append("- CPA real S1: $279 MXN (ads ganadores documentados)")
    partes.append("- Campañas S2: 100% PAUSADAS — esperando pixel verification")
    partes.append("- Agente 03: ✅ reescrito con Meta+Google+Boletera+Gemini+Resend")
    partes.append("- Agente 12: ✅ creado, lee 11 funciones, alertas de ocupación")
    partes.append("- Scheduled task: lunes 8am CDMX (Arranque D)")

    # Gaps
    partes.append("\n## GAPS CONOCIDOS")
    partes.append("Sin agent.py: 00,01,02,04,05,06,07,08,09,11,14")
    partes.append("Datos bloqueantes: /api/reporte, pixel Purchase, datos S1, Stripe modo")

    return "\n".join(partes)


# ─── MODOS DE OPERACIÓN ──────────────────────────────────────────────────────
def modo_pregunta(pregunta: str):
    """Dirección hace una pregunta libre sobre la agencia."""
    print(f"\n🧠 Agente 15 · Arquitecto de Procesos")
    print(f"📌 Pregunta: {pregunta}")
    print("─" * 60)

    contexto = cargar_contexto_completo()
    boletera = obtener_boletera_json()
    boletera_str = json.dumps(boletera, ensure_ascii=False, indent=2)[:1500]

    prompt = f"""Eres el Agente 15 — Arquitecto de Procesos de Platea, agencia de marketing teatral IA.

CONTEXTO DE LA AGENCIA:
{contexto}

DATOS EN VIVO (boletera):
{boletera_str}

INSTRUCCIONES:
- Responde en español mexicano formal
- Sé directo, prioriza por impacto
- Si propones algo, incluye: lógica, impacto estimado, esfuerzo y cómo se mediría
- NUNCA propones ejecutar algo tú mismo — siempre "proponer a Dirección/CEO"
- Si no hay datos suficientes, dilo: "necesitamos más datos antes de decidir"
- Aplica la fórmula maestra: ventana + muestra + umbral antes de recomendar un cambio

PREGUNTA DE OS:
{pregunta}

Responde como Agente 15. Sé útil, concreto y ordenado por impacto/esfuerzo."""

    respuesta = llamar_gemini(prompt)
    print(respuesta)
    print()


def modo_hipotesis():
    """Genera hipótesis priorizadas con datos actuales de boletera."""
    print(f"\n🧠 Agente 15 · Hipótesis Priorizadas — {datetime.now():%d %b %Y}")
    print("─" * 60)

    boletera = obtener_boletera_json()
    if "error" in boletera:
        print(f"⚠️  Boletera no disponible: {boletera['error']}")
        print("   Hipótesis sin datos en vivo — base en contexto histórico S1\n")

    contexto = cargar_contexto_completo()
    boletera_str = json.dumps(boletera, ensure_ascii=False, indent=2)[:2000]

    prompt = f"""Eres el Agente 15 — Arquitecto de Procesos de Platea.

CONTEXTO:
{contexto}

DATOS BOLETERA ACTUALES:
{boletera_str}

Tu tarea: genera las TOP 5 hipótesis priorizadas para maximizar ventas de El Gorila S2.

Para cada hipótesis:
1. HIPÓTESIS: [qué creemos que pasa o podría pasar]
2. LÓGICA: [por qué tiene sentido, con qué dato se conecta]
3. IMPACTO: [cuántos boletos / cuánto CPA podría mover]
4. ESFUERZO: [bajo / medio / alto]
5. CÓMO MEDIR: [qué métrica confirmaría o refutaría la hipótesis]
6. ACCIÓN SUGERIDA A OS/CEO: [propuesta concreta, sin ejecutar]

Ordena por impacto/esfuerzo. Si hay circuit breakers activos, ponlos primero.
Aplica la fórmula maestra (ventana + muestra + umbral) antes de proponer cambios en ads."""

    respuesta = llamar_gemini(prompt)
    print(respuesta)
    print()


def modo_auditoria():
    """Auditoría completa del estado del sistema."""
    print(f"\n🏛️  Auditoría del Sistema — Platea · {datetime.now():%d %b %Y}")
    print("=" * 60)

    # Estado de archivos de agentes
    print("\n📋 ESTADO DE AGENTES (scripts):")
    agentes_dir = AGENCIA_ROOT / "01_Agentes"
    for num, (nombre, func) in AGENTES.items():
        carpetas = list(agentes_dir.glob(f"{num}_*"))
        if carpetas:
            carpeta = carpetas[0]
            tiene_script = (carpeta / "agent.py").exists()
            tiene_persona = (carpeta / "persona.md").exists()
            tiene_playbook = (carpeta / "playbook.md").exists()
            estado = "✅" if tiene_script else "📝"
            extras = []
            if not tiene_persona:  extras.append("sin persona")
            if not tiene_playbook: extras.append("sin playbook")
            extra_str = f" [{', '.join(extras)}]" if extras else ""
            print(f"  {estado} {num} {nombre}{extra_str}")
        else:
            print(f"  ❓ {num} {nombre} — carpeta no encontrada")

    # Gaps de datos
    print("\n🔴 DATOS BLOQUEANTES:")
    for nombre, desc in GAPS_CONOCIDOS["datos_bloqueantes"]:
        print(f"  • {nombre}: {desc}")

    # Flujos existentes
    print(f"\n📂 WORKFLOWS DOCUMENTADOS ({len(FLUJOS_EXISTENTES)}):")
    for flujo in FLUJOS_EXISTENTES:
        ruta = WORKFLOWS_DIR / flujo
        estado = "✅" if ruta.exists() else "❌"
        print(f"  {estado} {flujo}")

    # Flujos faltantes
    print(f"\n⚠️  WORKFLOWS FALTANTES ({len(GAPS_CONOCIDOS['flujos_faltantes'])}):")
    for nombre, desc in GAPS_CONOCIDOS["flujos_faltantes"]:
        print(f"  • {nombre}: {desc}")

    # Boletera en vivo
    print("\n📊 BOLETERA EN VIVO:")
    boletera = obtener_boletera_json()
    if "error" in boletera:
        print(f"  ⚠️  {boletera['error']}")
    else:
        funciones = boletera.get("funciones", [])
        alertas = boletera.get("alertas", [])
        print(f"  Funciones cargadas: {len(funciones)}")
        if alertas:
            print(f"  🔴 Alertas activas: {len(alertas)}")
            for a in alertas[:3]:
                print(f"     → {a.get('mensaje', a)}")
        else:
            print(f"  🟢 Sin alertas activas")

    # Análisis Gemini del estado
    print("\n🧠 ANÁLISIS GEMINI:")
    contexto = cargar_contexto_completo()
    prompt = f"""Eres el Agente 15 — Arquitecto de Procesos de Platea.

CONTEXTO COMPLETO:
{contexto}

GAPS IDENTIFICADOS:
Agentes sin script: {[f"{n} {AGENTES[n][0]}" for n, _ in GAPS_CONOCIDOS['agentes_sin_script']]}
Flujos faltantes: {[n for n, _ in GAPS_CONOCIDOS['flujos_faltantes']]}
Datos bloqueantes: {[n for n, _ in GAPS_CONOCIDOS['datos_bloqueantes']]}

Dame un análisis ejecutivo (máx 300 palabras) con:
1. Los 3 riesgos más urgentes para el lanzamiento S2 (18 jul 2026)
2. Las 3 oportunidades de mayor impacto que se pueden activar YA
3. Una recomendación de priorización para Dirección

Tono: directo, sin rodeos. Eres el arquitecto del sistema, no un consultor genérico."""

    respuesta = llamar_gemini(prompt)
    print(textwrap.indent(respuesta, "  "))
    print()


def modo_flujo(nombre: str):
    """Explica un workflow específico en detalle."""
    print(f"\n📋 Workflow: {nombre}")
    print("─" * 60)

    contenido = leer_workflow(nombre)
    if contenido.startswith("Workflow"):
        print(contenido)
        return

    prompt = f"""Eres el Agente 15 — Arquitecto de Procesos de Platea.

WORKFLOW A ANALIZAR: {nombre}

CONTENIDO DEL WORKFLOW:
{contenido}

CONTEXTO DE LA AGENCIA:
{cargar_contexto_completo()[:1500]}

Dame:
1. RESUMEN del flujo en 3-5 líneas (para Dirección que ya lo conoce)
2. AGENTES INVOLUCRADOS y qué hace cada uno
3. PUNTOS DE FALLA potenciales (dónde puede romperse)
4. MEJORAS SUGERIDAS (1-3, ordenadas por impacto/esfuerzo)
5. ESTADO ACTUAL: ¿está implementado, parcial o solo documentado?

Directo y útil. No expliques lo obvio."""

    print(llamar_gemini(prompt))
    print()


def modo_gaps():
    """Lista gaps de agentes y flujos faltantes."""
    print(f"\n⚠️  Gap Analysis — Platea · {datetime.now():%d %b %Y}")
    print("=" * 60)

    print(f"\n📝 AGENTES SIN SCRIPT EJECUTABLE ({len(GAPS_CONOCIDOS['agentes_sin_script'])}):")
    for num, desc in GAPS_CONOCIDOS["agentes_sin_script"]:
        nombre = AGENTES[num][0]
        print(f"  • {num} {nombre}: {desc}")

    print(f"\n🔴 FLUJOS NO DOCUMENTADOS ({len(GAPS_CONOCIDOS['flujos_faltantes'])}):")
    for nombre, desc in GAPS_CONOCIDOS["flujos_faltantes"]:
        print(f"  • {nombre}: {desc}")

    print(f"\n🚧 DATOS BLOQUEANTES ({len(GAPS_CONOCIDOS['datos_bloqueantes'])}):")
    for nombre, desc in GAPS_CONOCIDOS["datos_bloqueantes"]:
        print(f"  • {nombre}: {desc}")

    print("\n💡 PRIORIZACIÓN SUGERIDA (por impacto en S2):")
    prioridades = [
        ("CRÍTICO", "🔴", "Agente 13: /api/reporte + pixel → desbloquea CPA real y Arranque B"),
        ("CRÍTICO", "🔴", "Procesar datos S1 (154 emails) → Custom Audiences Meta antes de jul 8"),
        ("ALTO",    "🟡", "Agente 06 Analytics BI con script → CPA real automático cada semana"),
        ("ALTO",    "🟡", "Flujo: pipeline orgánico → paid (post que funciona → ad en 24h)"),
        ("ALTO",    "🟡", "Flujo: reporte express miércoles (día de función)"),
        ("MEDIO",   "🟠", "Agente 02 Copywriter con script → copy variantes sin sesión manual"),
        ("MEDIO",   "🟠", "Flujo: cierre de temporada → archiving automático post-S2"),
        ("BAJO",    "⚪", "Agente 05 PR + Agente 11 Booking → Fase 2 (B2B) no urgente para S2"),
    ]
    for nivel, emoji, texto in prioridades:
        print(f"  {emoji} [{nivel}] {texto}")
    print()


def modo_estado():
    """Estado rápido de todos los agentes."""
    print(f"\n📊 Estado de Agentes — {datetime.now():%d %b %Y %H:%M}")
    print("─" * 60)
    agentes_dir = AGENCIA_ROOT / "01_Agentes"
    agentes_con_script = []
    agentes_sin_script = []

    for num in sorted(AGENTES.keys()):
        nombre, func = AGENTES[num]
        carpetas = list(agentes_dir.glob(f"{num}_*"))
        if carpetas:
            tiene_script = (carpetas[0] / "agent.py").exists()
            if tiene_script:
                agentes_con_script.append(f"{num} {nombre}")
            else:
                agentes_sin_script.append(f"{num} {nombre}")

    print(f"✅ Con script ({len(agentes_con_script)}): {', '.join(agentes_con_script)}")
    print(f"📝 Solo docs ({len(agentes_sin_script)}): {', '.join(agentes_sin_script)}")
    print()
    print(f"🤖 Autónomos con alertas: 03 Media Buyer, 12 Boletera")
    print(f"⏰ Scheduled: lunes 8am → Agente 12 (--json) → Agente 03")
    print()


# ─── CLI ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Agente 15 — Arquitecto de Procesos · Platea"
    )
    parser.add_argument("--pregunta", "-p", type=str,
                        help="Pregunta libre sobre la agencia, flujos o sistema")
    parser.add_argument("--auditoria", "-a", action="store_true",
                        help="Auditoría completa del estado del sistema")
    parser.add_argument("--hipotesis", "-i", action="store_true",
                        help="Top hipótesis priorizadas con datos actuales")
    parser.add_argument("--flujo", "-f", type=str,
                        help="Explica un workflow específico (ej: ciclo-campana)")
    parser.add_argument("--gaps", "-g", action="store_true",
                        help="Gap analysis: agentes y flujos faltantes")
    parser.add_argument("--estado", "-e", action="store_true",
                        help="Estado rápido de todos los agentes")

    args = parser.parse_args()

    if args.pregunta:
        modo_pregunta(args.pregunta)
    elif args.auditoria:
        modo_auditoria()
    elif args.hipotesis:
        modo_hipotesis()
    elif args.flujo:
        modo_flujo(args.flujo)
    elif args.gaps:
        modo_gaps()
    elif args.estado:
        modo_estado()
    else:
        parser.print_help()
        print("\n💡 Ejemplo rápido:")
        print("  python agent.py --pregunta '¿qué debería priorizar esta semana?'")
        print("  python agent.py --gaps")
        print("  python agent.py --auditoria")


if __name__ == "__main__":
    main()
