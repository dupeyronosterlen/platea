#!/usr/bin/env python3
"""
Agente 14 — Gorila Digital (Social Content)
Genera lotes de frases/copies para redes sociales, etiquetados por tipo.

Ciclo: Invent → Propose → (Dirección aprueba) → Publish → Measure → Learn

Uso:
    python3 agent.py                               # genera batch semanal estándar
    python3 agent.py '{"brief_creativo": {...}, "aprendizajes": "...", "n": 8}'
    python3 agent.py --medir '{"posts_ids": [...], "performance": {...}}'
    python3 agent.py --cuestionario

Tags de frases:
    DRAMA        — emocional oscuro, peso literario, Kafka
    HUMOR        — ironía inteligente, no comedia blanda
    EXPERIMENTO  — concepto arriesgado, puede generar polémica/debate

Output JSON (batch):
    {
      "ok": bool,
      "batch": [
        {
          "id": "gd-2026W28-01",
          "tag": "DRAMA",
          "frase_ig": "texto para post de Instagram (caption completo)",
          "frase_corta": "versión de ≤280 chars para stories/X",
          "concepto_visual": "descripción de imagen o reel sugerido",
          "hipotesis": "qué esperamos que haga este post (engagement, shares, DMs...)"
        },
        ...
      ],
      "registro_ganadores": [...],
      "hipotesis_proxima_semana": "..."
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

ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE   = ROOT / "config" / "produccion-activa.yaml"
PLAYBOOK_FILE = Path(__file__).parent / "playbook.md"
PERSONA_FILE  = Path(__file__).parent / "persona.md"
REGISTRO_FILE = Path(__file__).parent / "registro_ganadores.json"

load_dotenv(Path(__file__).parent / ".env")

GCP_PROJECT  = os.getenv("GCP_PROJECT", "agencia-mkt-ia")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")


def cargar_registro() -> list:
    if REGISTRO_FILE.exists():
        try:
            return json.loads(REGISTRO_FILE.read_text())
        except Exception:
            return []
    return []


def guardar_registro(ganadores: list):
    existing = cargar_registro()
    all_ganadores = existing + ganadores
    # Keep last 20
    REGISTRO_FILE.write_text(json.dumps(all_ganadores[-20:], ensure_ascii=False, indent=2))


def generar_batch(config: dict, brief_creativo: dict, aprendizajes: str, n: int) -> dict:
    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    model = GenerativeModel(GEMINI_MODEL)

    obra   = config.get("obra", {})
    ids_v  = config.get("identidad_visual", {})
    precios = config.get("precios", {})
    temp   = config.get("temporada", {})
    semana = datetime.now().strftime("W%W")
    año    = datetime.now().year

    registro = cargar_registro()
    registro_texto = json.dumps(registro[-5:], ensure_ascii=False) if registro else "Ninguno aún"

    brief_texto = json.dumps(brief_creativo, ensure_ascii=False) if brief_creativo else "Brief estándar: genera variedad de tonos"

    playbook = ""
    try:
        playbook = PLAYBOOK_FILE.read_text()
    except FileNotFoundError:
        pass

    persona = ""
    try:
        persona = PERSONA_FILE.read_text()
    except FileNotFoundError:
        pass

    prompt = f"""Eres el Agente 14 — Gorila Digital. Creas contenido social para El Gorila.

{persona}

## REGLAS
- Genera EXACTAMENTE {n} frases/posts
- Cada uno lleva tag: DRAMA | HUMOR | EXPERIMENTO
- DRAMA: peso emocional, Kafka, literario, oscuro
- HUMOR: ironía inteligente, auto-consciencia del simio, nunca comedia blanda
- EXPERIMENTO: rompe formato, puede dividir opiniones, concepto arriesgado
- Distribución sugerida: ~50% DRAMA, 25% HUMOR, 25% EXPERIMENTO
- NO exclamaciones, NO "increíble/espectacular/asombroso"
- Los captions de IG pueden tener hashtags (al final, ≤5, relevantes)
- Siempre que haya precio o fecha → verificar vs datos actuales

## DATOS
- Obra: {obra.get('nombre')} | {obra.get('actor_principal')}
- Estreno: {temp.get('estreno')} | Teatro Wilberto Cantón | 18:00h
- Precio: ${precios.get('general')} MXN | ESPEJO2: ${precios.get('espejo2')} la pareja
- Url boletos: {obra.get('url_boletos')}
- Instagram: {obra.get('instagram')}
- Concepto central: {ids_v.get('concepto_central')}
- Sinopsis: {ids_v.get('sinopsis_corta', '').strip()}
- Eje S2: {ids_v.get('eje_narrativo')}
- Palabras clave permitidas: {', '.join(ids_v.get('palabras_clave', []))}
- NO mencionar: {', '.join(ids_v.get('NO_mencionar', []))}

## BRIEF CREATIVO ESTA SEMANA
{brief_texto}

## POSTS GANADORES (últimas semanas)
{registro_texto}

## APRENDIZAJES
{aprendizajes or 'Sin aprendizajes previos registrados'}

## PLAYBOOK
{playbook}

## INSTRUCCIÓN
Responde SOLO con JSON:
{{
  "semana": "{año}-{semana}",
  "batch": [
    {{
      "id": "{año}-{semana}-01",
      "tag": "DRAMA",
      "frase_ig": "Caption completo para Instagram. Puede ser largo. Hashtags al final si aplica.",
      "frase_corta": "Versión ≤280 chars para stories o X",
      "concepto_visual": "Descripción de imagen o reel que acompaña (paleta, composición, si lleva texto on-image)",
      "hipotesis": "Qué esperamos medir: engagement, saves, DMs, shares, debates en comments"
    }}
  ],
  "hipotesis_proxima_semana": "Qué queremos aprender la próxima semana basado en este batch",
  "nota_aprobacion": "PENDIENTE APROBACIÓN DE Dirección — no publicar sin confirmación SÍ por WA"
}}
Genera exactamente {n} items en el array batch.
"""

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.9,
            "max_output_tokens": 3000,
            "response_mime_type": "application/json",
        }
    )

    try:
        result = json.loads(response.text)
        return {"ok": True, **result}
    except json.JSONDecodeError:
        return {"ok": False, "error": "JSON inválido", "raw": response.text[:500]}


def registrar_ganadores(posts_performance: list) -> dict:
    """
    Actualiza el registro de ganadores basado en performance real.
    posts_performance: [{"id": "...", "frase_ig": "...", "likes": X, "saves": X, "dms": X}]
    """
    # Ordenar por score simple: saves*3 + dms*5 + likes
    def score(p):
        return p.get("saves", 0) * 3 + p.get("dms", 0) * 5 + p.get("likes", 0)

    ordenados = sorted(posts_performance, key=score, reverse=True)
    ganadores = ordenados[:3]  # top 3

    for g in ganadores:
        g["registrado"] = datetime.now().isoformat()

    guardar_registro(ganadores)
    return {
        "ok": True,
        "ganadores_registrados": len(ganadores),
        "top_1": ganadores[0] if ganadores else None,
    }


def main():
    if "--cuestionario" in sys.argv:
        print(json.dumps({
            "agente": "14_Gorila-Digital",
            "modos": {
                "batch": "Genera lote de posts → python3 agent.py '{\"n\": 8, \"brief_creativo\": {...}}'",
                "medir": "Registra performance → python3 agent.py --medir '{\"posts_performance\": [{...}]}'"
            }
        }, ensure_ascii=False, indent=2))
        return

    if "--medir" in sys.argv:
        idx = sys.argv.index("--medir")
        payload_raw = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "{}"
        payload = json.loads(payload_raw)
        resultado = registrar_ganadores(payload.get("posts_performance", []))
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return

    payload = {}
    if len(sys.argv) > 1 and sys.argv[1] != "--medir":
        try:
            payload = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            pass
    elif not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            try:
                data = json.loads(raw)
                if "brief_creativo" in data:
                    payload = {"brief_creativo": data["brief_creativo"]}
                else:
                    payload = data
            except json.JSONDecodeError:
                pass

    config = yaml.safe_load((ROOT / "config" / "produccion-activa.yaml").read_text())
    resultado = generar_batch(
        config=config,
        brief_creativo=payload.get("brief_creativo", {}),
        aprendizajes=payload.get("aprendizajes", ""),
        n=payload.get("n", 6),
    )
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
