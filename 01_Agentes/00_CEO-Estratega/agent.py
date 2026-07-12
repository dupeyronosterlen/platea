#!/usr/bin/env python3
"""
Agente 00 — CEO / Estratega
Modelo: gemini-2.5-pro (razonamiento estratégico, consolidación)

Responsabilidad única:
- Recibir outputs JSON de agentes upstream
- Consolidar + generar narrativa + semáforo de salud
- Proponer acciones (siempre pending_approval — Dirección decide)
- NUNCA ejecutar nada sin aprobación explícita de Dirección

Rutas donde participa:
  A-7   Checklist final de nueva plaza
  B     Coordinador general de activación
  C-3   Consolida diagnóstico de rendimiento
  D-2   Reporte semanal (latido regular)
  F     Clasificador y escalador de crisis

Uso:
  # Ruta D (reporte semanal): recibe output de Analytics (D-1)
  python agent.py output_analytics.json

  # Por variables de entorno
  ROUTE=C STEP=C-3 python agent.py input.json
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import google.genai as genai

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
AGENCIA_DIR = BASE_DIR.parent.parent  # _PARA-AGENCIA/
load_dotenv(BASE_DIR / ".env")

GCP_PROJECT = os.environ["GCP_PROJECT"]
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")

# Logger (Python puro — cero tokens)
sys.path.insert(0, str(AGENCIA_DIR / "04_Operaciones"))
from logger import log_event

# ── Cliente Vertex AI ─────────────────────────────────────────────────────────
client = genai.Client(
    vertexai=True,
    project=GCP_PROJECT,
    location=GCP_LOCATION,
)

# ── Persona del CEO ────────────────────────────────────────────────────────────
CEO_PERSONA = """
Eres el CEO Estratega de la agencia de marketing de El Gorila.
Diriges a Dirección (productor teatral) directamente, sin rodeos.

Tu estilo:
- Directo y claro. Máximo 1 página por reporte.
- Semáforo siempre visible (🟢🟡🔴) al inicio.
- 1–2 acciones concretas: quién hace qué, cuándo.
- Si hay duda sobre los datos: lo dices, no inventas.
- Si detectas crisis: escalas a Dirección inmediatamente.

Principios inviolables:
1. Dirección es el único aprobador. Tú propones, él decide.
2. Nunca ejecutes cambios en campañas sin aprobación explícita.
3. Si algo no tiene datos suficientes, dilo y pide lo que falta.
"""

# ── Instrucciones por ruta/paso ───────────────────────────────────────────────
INSTRUCCIONES = {
    "D-2": (
        "Genera el reporte semanal para Dirección.\n"
        "Formato obligatorio:\n"
        "  SEMANA [rango de fechas]\n"
        "  SEMÁFORO: CPA 🟢/🟡/🔴 | Ocupación 🟢/🟡/🔴 | Tendencia ↑/→/↓\n"
        "  NÚMEROS CLAVE (3-5 métricas críticas)\n"
        "  LO QUE FUNCIONÓ (1 línea)\n"
        "  LO QUE NO FUNCIONÓ (1 línea)\n"
        "  ACCIÓN SUGERIDA (1 concreta, con agente responsable)\n"
        "  ALERTA (solo si requiere decisión de Dirección, omitir si no hay)"
    ),
    "C-3": (
        "El Analytics detectó una alerta de rendimiento. Consolida el diagnóstico.\n"
        "Propón UNA sola acción correctiva concreta.\n"
        "Clasifica urgencia: 🟡 monitoreo / 🟠 alerta / 🔴 urgente (función a ≤5 días).\n"
        "Presenta las opciones a Dirección para aprobación."
    ),
    "A-7": (
        "Checklist final para nueva plaza.\n"
        "Verifica que todos los pasos A-1 a A-6 estén completos.\n"
        "Lista lo que falta, lo que necesita aprobación de Dirección, y las dependencias bloqueantes.\n"
        "Output: checklist ejecutable listo para disparar Ruta B."
    ),
    "F": (
        "Se reportó una situación de crisis. Clasifica primero:\n"
        "🔴 Alta: cancelación, imposibilidad física, caída de sitio, controversia pública\n"
        "🟡 Media: CPA crítico, crítica viral, nota negativa, incidente en venue\n"
        "🟠 Baja: comentario negativo individual\n"
        "Escala a Dirección inmediatamente en crisis Alta. En Media/Baja: presenta opciones.\n"
        "NUNCA respondas públicamente sin aprobación de Dirección."
    ),
}


def get_instruccion(route: str, step: str) -> str:
    key = step if step in INSTRUCCIONES else route
    return INSTRUCCIONES.get(
        key,
        f"Procesa el input para la ruta {route}, paso {step}. "
        "Consolida la información y presenta a Dirección para aprobación."
    )


# ── Función principal ─────────────────────────────────────────────────────────
def run_ceo(input_data: dict, route: str = "D", step: str = "D-2") -> dict:
    """
    Recibe outputs de agentes upstream → genera reporte/decisión para Dirección.

    Returns:
        dict con reporte, semáforo, acciones propuestas, alertas y metadata.
    """
    prompt = f"""
{CEO_PERSONA}

---

DATOS RECIBIDOS DE LOS AGENTES:
{json.dumps(input_data, ensure_ascii=False, indent=2)}

---

INSTRUCCIÓN — RUTA {route} / PASO {step}:
{get_instruccion(route, step)}

---

Responde SOLO en JSON con esta estructura:
{{
  "reporte": "texto completo del reporte para Dirección",
  "semaforo": {{
    "cpa": "🟢|🟡|🔴",
    "ocupacion": "🟢|🟡|🔴",
    "tendencia": "🟢|🟡|🔴"
  }},
  "acciones_propuestas": [
    "Acción 1: agente responsable + qué hace + cuándo"
  ],
  "alertas": [],
  "escalar_a_os": true,
  "metadata": {{
    "route": "{route}",
    "step": "{step}",
    "modelo": "{GEMINI_MODEL}",
    "timestamp": "{datetime.now().isoformat()}"
  }}
}}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )

    output = json.loads(response.text)
    tokens = (
        response.usage_metadata.total_token_count
        if response.usage_metadata
        else 0
    )

    # Log automático (CEO siempre = pending_approval)
    log_event(
        route=route,
        step=step,
        agent="00 CEO",
        model=GEMINI_MODEL,
        action=f"Consolidó outputs → reporte {route}/{step}",
        result=json.dumps(output.get("semaforo", {})),
        tokens_used=tokens,
        outcome="pending_approval",
    )

    return output


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Input: archivo como argumento o JSON por stdin
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            input_data = json.load(f)
    else:
        raw = sys.stdin.read().strip()
        input_data = json.loads(raw) if raw else {}

    route = os.environ.get("ROUTE", "D")
    step = os.environ.get("STEP", "D-2")

    result = run_ceo(input_data, route=route, step=step)
    print(json.dumps(result, ensure_ascii=False, indent=2))
