#!/usr/bin/env python3
"""
Agente 04 — Community Manager
Responde DMs, gestiona comentarios, propone posting schedule semanal.

Modos:
    1. responder_dm   — genera respuesta a DM recibido
    2. responder_comentario — genera respuesta a comentario en feed
    3. schedule_semanal — propone horario y contenido de posts para la semana

Uso:
    python3 agent.py --dm '{"texto": "¿Cuánto cuesta?", "canal": "instagram"}'
    python3 agent.py --comentario '{"texto": "Se ve increíble", "post_contexto": "..."}'
    python3 agent.py --schedule '{"posts_aprobados": [...]}'
    python3 agent.py --cuestionario

Reglas de posting:
    - 3-4 posts/semana (feed)
    - Stories todos los días de función
    - Óptimo: Mar-Jue 19-21h CDMX, Vie 18h, Dom 12h (día de función)

DM protocol:
    - Responder <2h
    - Grupos/familias → dar link + código ESPEJO2
    - No dar precios sin verificar este config

Output JSON:
    {
      "ok": bool,
      "respuesta": "..." | "schedule": [...],
      "accion_requerida": "ninguna | escalar_a_os | enviar_link",
      "notas": "..."
    }
"""

import json
import os
import sys
from datetime import datetime, timedelta
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


def responder_dm(config: dict, texto_dm: str, canal: str, contexto_extra: str) -> dict:
    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    model = GenerativeModel(GEMINI_MODEL)

    obra    = config.get("obra", {})
    precios = config.get("precios", {})
    temp    = config.get("temporada", {})
    ids_v   = config.get("identidad_visual", {})

    prompt = f"""Eres el Agente 04 — Community Manager de El Gorila.

{cargar_persona()}

## DATOS ACTUALIZADOS
- Obra: {obra.get('nombre')} | {obra.get('actor_principal')}
- Estreno: {temp.get('estreno')} | Teatro Wilberto Cantón | 18:00h
- Precio general: ${precios.get('general')} MXN
- Precio pareja: ${precios.get('espejo2')} MXN (código ESPEJO2)
- Descuento académico: ${precios.get('descuento_academia')} MXN (código ACADEMIA)
- URL boletos: {obra.get('url_boletos')}
- Instagram: {obra.get('instagram')}

## REGLAS DE DM
- Respuesta cálida pero no vendedora de bazar
- Tiempo de respuesta objetivo: <2h
- Si preguntan por grupos o parejas → dar link + mencionar ESPEJO2
- Si preguntan por precio de grupo grande (>6) → escalar a Dirección
- Nunca inventar información de horarios o precio no confirmada en este config
- Tono: como el theatre person que conoce bien el show, no como chatbot de ventas

## PLAYBOOK
{cargar_playbook()}

## CANAL
{canal} (adaptar registro al canal: IG más visual/emocional, email más formal)

## MENSAJE RECIBIDO
"{texto_dm}"

## CONTEXTO ADICIONAL
{contexto_extra or 'Sin contexto adicional'}

## INSTRUCCIÓN
Genera respuesta en JSON:
{{
  "respuesta": "Texto exacto para responder (listo para copiar/pegar o enviar vía API)",
  "accion_requerida": "ninguna | escalar_a_os | enviar_link_automatico",
  "link_incluir": "{obra.get('url_boletos')}" si aplica,
  "codigo_incluir": "ESPEJO2 o ACADEMIA si aplica, o null",
  "razon_accion": "por qué se requiere acción adicional si aplica",
  "notas_cm": "observaciones internas (no se envían al usuario)"
}}

Responde SOLO con JSON válido.
"""

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.5,
            "max_output_tokens": 800,
            "response_mime_type": "application/json",
        }
    )

    try:
        resp = json.loads(response.text)
        return {"ok": True, **resp}
    except json.JSONDecodeError:
        return {"ok": False, "error": "JSON inválido", "raw": response.text[:300]}


def responder_comentario(config: dict, texto_comentario: str, post_contexto: str) -> dict:
    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    model = GenerativeModel(GEMINI_MODEL)

    obra    = config.get("obra", {})
    precios = config.get("precios", {})

    prompt = f"""Eres el CM de El Gorila respondiendo comentarios en Instagram.

{cargar_persona()}

OBRA: {obra.get('nombre')} | {obra.get('actor_principal')}
URL BOLETOS: {obra.get('url_boletos')}
PRECIO: ${precios.get('general')} MXN | ESPEJO2: ${precios.get('espejo2')} la pareja

PLAYBOOK: {cargar_playbook()}

POST CONTEXTO: {post_contexto or 'Post general de El Gorila'}

COMENTARIO RECIBIDO: "{texto_comentario}"

Genera la respuesta al comentario:
{{
  "respuesta": "Texto corto (comentarios de IG deben ser breves y orgánicos), ≤3 líneas",
  "tipo_comentario": "positivo | pregunta | negativo | spam | debate",
  "accion": "responder | ignorar | escalar_a_os | ocultar",
  "razon": "si la acción no es 'responder', explicar por qué"
}}

Responde SOLO JSON.
"""

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.5,
            "max_output_tokens": 400,
            "response_mime_type": "application/json",
        }
    )

    try:
        resp = json.loads(response.text)
        return {"ok": True, **resp}
    except json.JSONDecodeError:
        return {"ok": False, "error": "JSON inválido", "raw": response.text[:300]}


def generar_schedule(config: dict, posts_aprobados: list) -> dict:
    """Propone horario de publicación para los posts aprobados."""
    temp = config.get("temporada", {})

    # Próxima función
    funciones = temp.get("funciones", [])
    hoy = datetime.now().date()
    proxima_funcion = None
    for f in funciones:
        from datetime import date
        fd = date.fromisoformat(f)
        if fd >= hoy:
            proxima_funcion = fd
            break

    # Horarios óptimos por día de semana (lunes=0)
    HORARIOS_OPTIMOS = {
        1: "19:00",  # Martes
        2: "20:00",  # Miércoles
        3: "19:30",  # Jueves
        4: "18:00",  # Viernes
        6: "12:00",  # Domingo (función)
    }

    schedule = []
    hoy_dt = datetime.now()
    dias_intentados = 0
    posts_idx = 0

    while posts_idx < len(posts_aprobados) and dias_intentados < 14:
        candidato = hoy_dt + timedelta(days=dias_intentados + 1)
        dow = candidato.weekday()

        if dow in HORARIOS_OPTIMOS:
            # Stories en día de función
            es_funcion = proxima_funcion and candidato.date() == proxima_funcion
            hora = HORARIOS_OPTIMOS[dow]

            entry = {
                "fecha": candidato.strftime("%Y-%m-%d"),
                "hora_cdmx": hora,
                "dia_semana": ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"][dow],
                "post": posts_aprobados[posts_idx] if posts_idx < len(posts_aprobados) else None,
                "tipo": "feed",
                "nota": "Incluir stories durante el día" if es_funcion else "",
            }

            if es_funcion:
                entry["stories_funcion"] = True

            schedule.append(entry)
            posts_idx += 1

        dias_intentados += 1

    return {
        "ok": True,
        "schedule": schedule,
        "proxima_funcion": str(proxima_funcion) if proxima_funcion else None,
        "posts_programados": posts_idx,
        "nota": "Horarios en CDMX (UTC-6). Programar en Meta Business Suite o Hootsuite."
    }


def main():
    if "--cuestionario" in sys.argv:
        print(json.dumps({
            "agente": "04_Community-Manager",
            "modos": {
                "--dm": "Responder DM: --dm '{\"texto\": \"...\", \"canal\": \"instagram\"}'",
                "--comentario": "Responder comentario: --comentario '{\"texto\": \"...\", \"post_contexto\": \"\"}'",
                "--schedule": "Generar calendario: --schedule '{\"posts_aprobados\": [...]}'",
            }
        }, ensure_ascii=False, indent=2))
        return

    config = yaml.safe_load((ROOT / "config" / "produccion-activa.yaml").read_text())

    if "--dm" in sys.argv:
        idx = sys.argv.index("--dm")
        raw = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "{}"
        payload = json.loads(raw)
        resultado = responder_dm(
            config,
            texto_dm=payload.get("texto", ""),
            canal=payload.get("canal", "instagram"),
            contexto_extra=payload.get("contexto", ""),
        )

    elif "--comentario" in sys.argv:
        idx = sys.argv.index("--comentario")
        raw = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "{}"
        payload = json.loads(raw)
        resultado = responder_comentario(
            config,
            texto_comentario=payload.get("texto", ""),
            post_contexto=payload.get("post_contexto", ""),
        )

    elif "--schedule" in sys.argv:
        idx = sys.argv.index("--schedule")
        raw = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "{}"
        payload = json.loads(raw)
        resultado = generar_schedule(config, posts_aprobados=payload.get("posts_aprobados", []))

    else:
        # Default: stdin o help
        if not sys.stdin.isatty():
            raw = sys.stdin.read().strip()
            payload = {}
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"texto": raw}

            if "posts_aprobados" in payload:
                resultado = generar_schedule(config, payload["posts_aprobados"])
            elif "texto" in payload:
                resultado = responder_dm(config, payload["texto"], payload.get("canal", "instagram"), "")
            else:
                resultado = {"ok": False, "error": "Modo no detectado. Usa --dm, --comentario o --schedule"}
        else:
            resultado = {"ok": False, "error": "Usa --dm, --comentario, --schedule o --cuestionario"}

    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
