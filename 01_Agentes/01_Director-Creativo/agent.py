#!/usr/bin/env python3
"""
Agente 01 — Director Creativo
Lee identidad + performance data + brief de Dirección → genera brief creativo estructurado.

Uso:
    python3 agent.py                          # modo interactivo (lee stdin)
    python3 agent.py '{"brief_os": "...", "performance_resumen": "..."}'
    python3 agent.py --cuestionario           # imprime qué inputs necesita

Output JSON:
    {
      "ok": bool,
      "brief_creativo": {
        "semana": "2026-W28",
        "angulo_principal": "...",
        "emocion_objetivo": "...",
        "formatos": [...],
        "tono": "drama_negro|archivo_papel|invitacion_cafe",
        "palabras_clave": [...],
        "prohibido_esta_semana": [...],
        "brief_para_copywriter": "...",
        "brief_para_gorila_digital": "...",
        "assets_requeridos": {...}
      },
      "razonamiento": "...",
      "siguiente_paso": "..."
    }
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

# ─── Config ────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE   = ROOT / "config" / "produccion-activa.yaml"
PLAYBOOK_FILE = Path(__file__).parent / "playbook.md"
PERSONA_FILE  = Path(__file__).parent / "persona.md"

load_dotenv(Path(__file__).parent / ".env")

GCP_PROJECT  = os.getenv("GCP_PROJECT", "agencia-mkt-ia")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")


# ─── Carga de contexto ─────────────────────────────────────────────
def cargar_config() -> dict:
    return yaml.safe_load(CONFIG_FILE.read_text())


def cargar_playbook() -> str:
    try:
        return PLAYBOOK_FILE.read_text()
    except FileNotFoundError:
        return "(playbook no disponible)"


def cargar_persona() -> str:
    try:
        return PERSONA_FILE.read_text()
    except FileNotFoundError:
        return ""


# ─── Llamada a Gemini ──────────────────────────────────────────────
def generar_brief(config: dict, brief_os: str, performance_resumen: str) -> dict:
    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    model = GenerativeModel(GEMINI_MODEL)

    obra       = config.get("obra", {})
    identidad  = config.get("identidad_visual", {})
    temporada  = config.get("temporada", {})
    precios    = config.get("precios", {})
    kpis       = config.get("kpis", {})
    reglas     = config.get("reglas_operacion", {})

    semana_actual = datetime.now().strftime("W%W de %Y")

    prompt = f"""Eres el Agente 01 — Director Creativo de la agencia de marketing de El Gorila.

{cargar_persona()}

## OBRA
- Nombre: {obra.get('nombre')}
- Actor: {obra.get('actor_principal')}
- Género: {obra.get('genero')}
- Estreno: {temporada.get('estreno')} | Teatro Wilberto Cantón
- Precio general: ${precios.get('general')} MXN
- Precio pareja (ESPEJO2): ${precios.get('espejo2')} MXN

## IDENTIDAD VISUAL
Estilo: {identidad.get('estilo')}
Palabras clave: {', '.join(identidad.get('palabras_clave', []))}
Lo que NO es: {identidad.get('lo_que_NO_es')}
Concepto central: {identidad.get('concepto_central')}
Eje narrativo S2: {identidad.get('eje_narrativo')}

Tonos disponibles:
- drama_negro: awareness frío, fondo negro, solo rojo, frase de golpe
- archivo_papel: consideración, legado (37 años/Kafka), no CTA agresivo
- invitacion_cafe: conversión, remarketing caliente, CTA directo con datos

NO mencionar: {', '.join(identidad.get('NO_mencionar', []))}

## PLAYBOOK COMPLETO
{cargar_playbook()}

## DATOS DE PERFORMANCE ESTA SEMANA
{performance_resumen or 'Sin datos de performance (primera semana)'}

## BRIEF DEL CEO (Dirección)
{brief_os or 'Sin brief específico — genera brief semanal estándar'}

## SEMANA
{semana_actual}

## KPIs OBJETIVO
- CPA objetivo: ${kpis.get('cpa_target')} MXN
- CPA máximo: ${kpis.get('cpa_max_aceptable')} MXN
- Frecuencia máxima: {kpis.get('frecuencia_max')}

## INSTRUCCIÓN
Genera un brief creativo semanal completo en JSON con esta estructura exacta:
{{
  "semana": "{semana_actual}",
  "angulo_principal": "el eje narrativo más potente para esta semana en 1 frase",
  "emocion_objetivo": "la emoción que buscamos provocar",
  "tono": "drama_negro | archivo_papel | invitacion_cafe (el principal de la semana)",
  "formatos_prioritarios": ["feed_imagen", "reel", "stories", "google_search", "google_display"],
  "palabras_clave": ["max 5 palabras/frases para esta semana"],
  "palabras_prohibidas": ["lo que NO debe aparecer en ningún copy esta semana"],
  "brief_para_copywriter": "instrucción clara de 2-3 párrafos: ángulo, tono, qué debe lograr cada pieza",
  "brief_para_gorila_digital": "instrucción para Agente 14: tipo de frases, tag predominante (DRAMA/HUMOR/EXPERIMENTO), objetivo",
  "assets_requeridos": {{
    "imagen_feed": "descripción visual exacta (composición, paleta, texto on-image si aplica)",
    "reel_concepto": "concepto para video corto",
    "stories": "descripción de stories secuenciales si aplica"
  }},
  "hipotesis_semana": "qué estamos probando esta semana y por qué",
  "metricas_a_vigilar": ["CPA", "frecuencia", "CTR", ...]
}}

Responde SOLO con JSON válido, sin texto antes ni después.
"""

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 2000,
            "response_mime_type": "application/json",
        }
    )

    try:
        brief = json.loads(response.text)
        return {"ok": True, "brief_creativo": brief, "razonamiento": "Gemini 2.5 Pro", "siguiente_paso": "Enviar a Agente 02 (Copywriter) y Agente 14 (Gorila Digital)"}
    except json.JSONDecodeError:
        return {"ok": False, "error": "JSON inválido de Gemini", "raw": response.text[:500]}


# ─── Main ─────────────────────────────────────────────────────────
def main():
    if "--cuestionario" in sys.argv:
        print(json.dumps({
            "agente": "01_Director-Creativo",
            "inputs_requeridos": {
                "brief_os": "Instrucción o contexto del CEO para la semana (opcional)",
                "performance_resumen": "Resumen de performance de la semana anterior (CPA, frecuencia, qué funcionó, qué no)"
            },
            "inputs_opcionales": {},
            "como_llamar": "python3 agent.py '{\"brief_os\": \"...\", \"performance_resumen\": \"CPA $280, frecuencia 2.1...\"}'",
        }, ensure_ascii=False, indent=2))
        return

    payload = {}
    if len(sys.argv) > 1:
        try:
            payload = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            pass
    elif not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"brief_os": raw}

    config = cargar_config()
    resultado = generar_brief(
        config=config,
        brief_os=payload.get("brief_os", ""),
        performance_resumen=payload.get("performance_resumen", ""),
    )
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
