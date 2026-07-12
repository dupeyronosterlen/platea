#!/usr/bin/env python3
"""
Agente 02 — Copywriter
Recibe brief creativo del Agente 01 → genera copies para Meta y Google.

Uso:
    python3 agent.py '{"brief_creativo": {...}}'          # brief completo de Ag01
    python3 agent.py '{"brief_os": "escribe un copy frío para awareness"}'
    python3 agent.py --cuestionario

Output JSON:
    {
      "ok": bool,
      "copies": {
        "meta": {
          "variante_a": {"headline": "...", "body": "...", "cta": "..."},
          "variante_b": {"headline": "...", "body": "...", "cta": "..."}
        },
        "google": {
          "search": {
            "headlines": ["h1 ≤30", "h2 ≤30", "h3 ≤30"],
            "descriptions": ["d1 ≤90", "d2 ≤90"]
          }
        },
        "dm_response": "texto para responder DMs que preguntan precios/info",
        "stories_texto": ["copy slide 1", "copy slide 2", ...]
      },
      "notas_validacion": ["lista de checks cumplidos"],
      "advertencias": ["si algo viola una regla del playbook"]
    }
"""

import json
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE   = ROOT / "config" / "produccion-activa.yaml"
PLAYBOOK_FILE = Path(__file__).parent / "playbook.md"
PERSONA_FILE  = Path(__file__).parent / "persona.md"

load_dotenv(Path(__file__).parent / ".env")

GCP_PROJECT  = os.getenv("GCP_PROJECT", "agencia-mkt-ia")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")


def cargar_playbook() -> str:
    try:
        return PLAYBOOK_FILE.read_text()
    except FileNotFoundError:
        return ""


def cargar_persona() -> str:
    try:
        return PERSONA_FILE.read_text()
    except FileNotFoundError:
        return ""


def generar_copies(config: dict, brief_creativo: dict, brief_os: str) -> dict:
    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    model = GenerativeModel(GEMINI_MODEL)

    obra    = config.get("obra", {})
    precios = config.get("precios", {})
    ids_v   = config.get("identidad_visual", {})
    temp    = config.get("temporada", {})

    brief_texto = json.dumps(brief_creativo, ensure_ascii=False) if brief_creativo else brief_os or "Genera copies variados para El Gorila"

    prompt = f"""Eres el Agente 02 — Copywriter de la agencia de marketing de El Gorila.

{cargar_persona()}

## REGLAS ABSOLUTAS (nunca violar)
1. Meta headline: ≤ 40 caracteres (incluye espacios y puntuación)
2. Meta body: ≤ 125 caracteres
3. Google headline: ≤ 30 caracteres cada uno (3 requeridos)
4. Google description: ≤ 90 caracteres cada una (2 requeridas)
5. SIEMPRE generar mínimo 2 variantes A/B para Meta
6. PROHIBIDO: signos de exclamación, MAYÚSCULAS para gritar, "no te lo pierdas", "increíble", "espectacular", "asombroso"
7. Estilo: editorial oscura — no copy de propaganda, no vendedor de mercado
8. DMs: si preguntan por grupos/familias → dar link + código ESPEJO2 (${precios.get('espejo2')} la pareja)

## DATOS CLAVE
- Obra: {obra.get('nombre')} — {obra.get('subtitulo')}
- Actor: {obra.get('actor_principal')}
- Estreno: {temp.get('estreno')}  |  Teatro Wilberto Cantón  |  18:00h
- Precio general: ${precios.get('general')} MXN
- Código pareja: ESPEJO2 (${precios.get('espejo2')} los dos — NO llamar "2×1")
- URL boletos: {obra.get('url_boletos')}
- Instagram: {obra.get('instagram')}
- Concepto: {ids_v.get('concepto_central')}
- Sinopsis: {ids_v.get('sinopsis_corta', '').strip()}

## TONO DISPONIBLE
{json.dumps(ids_v.get('tonos_visuales', {}), ensure_ascii=False, indent=2)}

## BRIEF ESTA SEMANA
{brief_texto}

## PLAYBOOK COMPLETO
{cargar_playbook()}

## INSTRUCCIÓN
Genera copies en este JSON exacto (sin texto fuera del JSON):
{{
  "meta": {{
    "variante_a": {{
      "angulo": "describe en 1 frase qué está probando esta variante",
      "headline": "≤40 chars",
      "body": "≤125 chars",
      "cta": "uno de: Comprar entradas | Ver más | Reservar lugar | Obtener boletos"
    }},
    "variante_b": {{
      "angulo": "contraste con variante A",
      "headline": "≤40 chars",
      "body": "≤125 chars",
      "cta": "uno de: Comprar entradas | Ver más | Reservar lugar | Obtener boletos"
    }}
  }},
  "google": {{
    "search": {{
      "headlines": ["h1 ≤30", "h2 ≤30", "h3 ≤30"],
      "descriptions": ["d1 ≤90", "d2 ≤90"]
    }},
    "search_variante_b": {{
      "headlines": ["h1 ≤30", "h2 ≤30", "h3 ≤30"],
      "descriptions": ["d1 ≤90", "d2 ≤90"]
    }}
  }},
  "stories": [
    "copy slide 1 (muy corto, impacto visual)",
    "copy slide 2 (si aplica)",
    "copy slide 3 — CTA final"
  ],
  "dm_response_template": "Respuesta tipo para DMs preguntando info/precios. Debe incluir link y mencionar ESPEJO2 si aplica.",
  "notas_validacion": [
    "Meta A headline: X chars ✓",
    "Meta A body: X chars ✓",
    "Meta B headline: X chars ✓",
    "Meta B body: X chars ✓",
    "Google h1: X chars ✓",
    "Sin exclamaciones ✓",
    "Sin palabras prohibidas ✓"
  ],
  "advertencias": []
}}

Cuenta los caracteres tú mismo y verifica antes de responder.
Responde SOLO con JSON válido.
"""

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.6,
            "max_output_tokens": 2500,
            "response_mime_type": "application/json",
        }
    )

    try:
        copies = json.loads(response.text)
        return {"ok": True, "copies": copies}
    except json.JSONDecodeError:
        return {"ok": False, "error": "JSON inválido", "raw": response.text[:500]}


def main():
    if "--cuestionario" in sys.argv:
        print(json.dumps({
            "agente": "02_Copywriter",
            "inputs_requeridos": {
                "brief_creativo": "JSON del Agente 01 (o usar brief_os como alternativa)"
            },
            "inputs_opcionales": {
                "brief_os": "Instrucción directa si no viene brief del Ag01"
            },
            "como_llamar": "python3 agent.py '{\"brief_creativo\": {...}}' | python3 ../02_Copywriter/agent.py",
        }, ensure_ascii=False, indent=2))
        return

    payload = {}
    if len(sys.argv) > 1:
        try:
            payload = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            payload = {"brief_os": sys.argv[1]}
    elif not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            try:
                # Si viene de Ag01 (el output tiene "brief_creativo" anidado)
                data = json.loads(raw)
                if "brief_creativo" in data:
                    payload = {"brief_creativo": data["brief_creativo"]}
                else:
                    payload = data
            except json.JSONDecodeError:
                payload = {"brief_os": raw}

    config = yaml.safe_load((ROOT / "config" / "produccion-activa.yaml").read_text())
    resultado = generar_copies(
        config=config,
        brief_creativo=payload.get("brief_creativo", {}),
        brief_os=payload.get("brief_os", ""),
    )
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
