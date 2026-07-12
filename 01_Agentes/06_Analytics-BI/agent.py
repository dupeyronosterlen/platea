#!/usr/bin/env python3
"""
Agente 06 — Analytics y BI
Modelo: gemini-2.5-pro (extracción de datos, diagnóstico)

Responsabilidad única:
- Pull de datos: Meta Ads + Google Ads (cuando esté disponible) + Boletera
- Cruzar conversiones de ads con ventas reales (fuente de verdad = boletera)
- Detectar alertas automáticas (CPA, ocupación)
- Output: JSON estructurado → CEO (Ruta D) o directo a Dirección

Rutas donde participa:
  B-1   Verificación bloqueante (pixel + GA4 activos antes de activar campaña)
  B-5   Reporte 72h post-activación
  D-1   Pull semanal de datos (latido regular, lunes)
  C-1   Diagnóstico de causa raíz cuando hay alerta
  C-5   Seguimiento 48h post-ajuste

Umbrales de alerta (de presupuesto-activo.md):
  CPA máx: $350 MXN
  CPA monitoreo: $300–$350 MXN
  Ocupación alerta: <60% en función próxima semana
  Ocupación urgente: <40% en función a ≤5 días

Uso:
  # Ruta D (pull semanal)
  python agent.py

  # Ruta C (diagnóstico de alerta)
  ROUTE=C STEP=C-1 python agent.py

  # Verificación B-1
  ROUTE=B STEP=B-1 python agent.py
"""

import json
import os
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
import google.genai as genai

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
AGENCIA_DIR = BASE_DIR.parent.parent
load_dotenv(BASE_DIR / ".env")

GCP_PROJECT = os.environ["GCP_PROJECT"]
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")

AD_ACCOUNT_ID = os.environ.get("AD_ACCOUNT_ID", "act_389427487828383")
META_TOKEN = os.environ.get("SYSTEM_USER_ACCESS_TOKEN")

# Logger (Python puro — cero tokens)
sys.path.insert(0, str(AGENCIA_DIR / "04_Operaciones"))
from logger import log_event

# Conexiones reales (Google Ads v21 + GA4) — ver conexiones.py
from conexiones import (
    google_ads_conversiones,
    ga4_eventos_recientes,
    verificar_tags,
)

# ── Cliente Vertex AI ─────────────────────────────────────────────────────────
client = genai.Client(
    vertexai=True,
    project=GCP_PROJECT,
    location=GCP_LOCATION,
)

# ── Umbrales ──────────────────────────────────────────────────────────────────
CPA_LIMITE = 350        # MXN — alerta roja
CPA_MONITOREO = 300     # MXN — alerta amarilla
OCUPACION_ALERTA = 0.60
OCUPACION_URGENTE = 0.40
META_API_VERSION = "v22.0"


# ── Pull Meta Ads ─────────────────────────────────────────────────────────────
def pull_meta_ads(days: int = 7) -> dict:
    """Extrae métricas de Meta Ads para los últimos N días."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    until = datetime.now().strftime("%Y-%m-%d")

    url = f"https://graph.facebook.com/{META_API_VERSION}/{AD_ACCOUNT_ID}/insights"
    params = {
        "access_token": META_TOKEN,
        "time_range": json.dumps({"since": since, "until": until}),
        "fields": (
            "spend,impressions,clicks,ctr,cpc,frequency,"
            "actions,cost_per_action_type"
        ),
        "level": "account",
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"meta": {"error": str(e), "periodo": f"{since}→{until}"}}

    if not data.get("data"):
        return {"meta": {"sin_datos": True, "periodo": f"{since}→{until}"}}

    row = data["data"][0]

    # Conversiones de compra (pixel)
    conversiones = sum(
        int(a.get("value", 0))
        for a in row.get("actions", [])
        if a["action_type"] in (
            "offsite_conversion.fb_pixel_purchase",
            "purchase",
            "omni_purchase",
        )
    )

    gasto = float(row.get("spend", 0))
    cpa_pixel = round(gasto / conversiones, 2) if conversiones > 0 else None

    return {
        "meta": {
            "periodo": f"{since}→{until}",
            "gasto_mxn": gasto,
            "impresiones": int(row.get("impressions", 0)),
            "clicks": int(row.get("clicks", 0)),
            "ctr_pct": round(float(row.get("ctr", 0)), 2),
            "cpc_mxn": round(float(row.get("cpc", 0)), 2),
            "frecuencia": round(float(row.get("frequency", 0)), 2),
            "conversiones_pixel": conversiones,
            "cpa_pixel_mxn": cpa_pixel,
        }
    }


def pull_meta_por_campana(days: int = 7) -> dict:
    """Desglose por campaña para diagnóstico C-1."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    until = datetime.now().strftime("%Y-%m-%d")

    url = f"https://graph.facebook.com/{META_API_VERSION}/{AD_ACCOUNT_ID}/insights"
    params = {
        "access_token": META_TOKEN,
        "time_range": json.dumps({"since": since, "until": until}),
        "fields": "campaign_name,spend,impressions,clicks,ctr,actions",
        "level": "campaign",
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return {"meta_por_campana": resp.json().get("data", [])}
    except Exception as e:
        return {"meta_por_campana": {"error": str(e)}}


# ── Pull Google Ads ───────────────────────────────────────────────────────────
def pull_google_ads(dias: int = 7) -> dict:
    """
    Google Ads vía API v21 (Basic Access activo).
    Devuelve la salud de las acciones de conversión (tags): estado + conversiones.
    """
    data = google_ads_conversiones(dias=30)
    if data.get("error"):
        return {"google": {"status": "error", "razon": data["error"]}}

    tags = data.get("tags", [])
    activos = [t for t in tags if t.get("estado") == "ENABLED"]
    con_datos = [
        t for t in activos
        if t.get("conversiones_periodo", {}).get("all_conversions", 0)
    ]
    return {
        "google": {
            "status": "ok",
            "customer_id": "2681423694",
            "acciones_totales": len(tags),
            "acciones_activas": len(activos),
            "acciones_con_conversiones": len(con_datos),
            "tags": tags,
        }
    }


# ── Pull Boletera ─────────────────────────────────────────────────────────────
def pull_boletera() -> dict:
    """
    Boletera propia integrada en elgorilateatro.com.mx.
    NO es Ticket Tailor — es sistema propio del sitio.

    TODO: Definir cómo se extrae la data:
      - ¿Hay un endpoint/API interno del sitio?
      - ¿Hay un panel admin con exportación?
      - ¿Se consulta directo a base de datos?

    La boletera es la fuente de verdad para ventas reales.
    CPA real = gasto total / boletos vendidos en boletera.
    """
    return {
        "boletera": {
            "status": "pendiente",
            "razon": "Integración con boletera propia de elgorilateatro.com.mx por definir (NO es TT)",
            "fuente": "elgorilateatro.com.mx",
            "preguntas_pendientes": [
                "¿Tiene API o endpoint consultable?",
                "¿Hay panel admin con exportación CSV/JSON?",
                "¿Acceso directo a BD del sitio?",
            ],
        }
    }


# ── Verificación pixel (para B-1) ─────────────────────────────────────────────
def verificar_pixel() -> dict:
    """
    Verifica que el pixel Meta esté recibiendo eventos.
    B-1 es bloqueante: si falla, no se activa la campaña.
    """
    url = f"https://graph.facebook.com/{META_API_VERSION}/{AD_ACCOUNT_ID}/ads_pixels"
    params = {"access_token": META_TOKEN, "fields": "id,name,last_fired_time"}

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if not data:
            return {"pixel": {"activo": False, "error": "No se encontró pixel"}}
        pixel = data[0]
        last_fired = pixel.get("last_fired_time")
        return {
            "pixel": {
                "id": pixel.get("id"),
                "nombre": pixel.get("name"),
                "ultimo_evento": last_fired,
                "activo": bool(last_fired),
            }
        }
    except Exception as e:
        return {"pixel": {"activo": False, "error": str(e)}}


# ── Análisis con Gemini Flash ─────────────────────────────────────────────────
def analizar_datos(raw_data: dict, route: str, step: str) -> dict:
    """
    Usa Flash para extraer insights, detectar alertas y estructurar el output.
    """
    instruccion_por_step = {
        "D-1": (
            "Analiza las métricas de la semana. "
            "Detecta si CPA > $350 MXN o si hay señales de bajo rendimiento. "
            "Output: tabla de métricas + alertas + semáforo. "
            "Este output va directo al CEO (D-2) para el reporte semanal."
        ),
        "C-1": (
            "Se activó una alerta de rendimiento. Haz diagnóstico de causa raíz. "
            "¿Es problema de: creativo, audiencia, presupuesto, tracking, o externo? "
            "Sé específico sobre qué campaña/adset está causando el problema."
        ),
        "B-1": (
            "Verificación previa a activación de campaña. "
            "Confirma que: pixel activo, GA4 configurado, boletera funcionando. "
            "Si falta cualquier cosa: resultado = BLOQUEADO, no proceder con B-2."
        ),
        "B-5": (
            "Reporte 72h post-activación de campaña. "
            "¿Cómo están los primeros datos? ¿CPA en rango? ¿Conversiones registradas? "
            "¿Algo que ajustar en las primeras 72h?"
        ),
        "C-5": (
            "Seguimiento 48h post-ajuste. "
            "¿El ajuste tuvo efecto? Compara CPA/conversiones antes y después. "
            "¿Se resolvió la alerta o sigue activa?"
        ),
    }

    instruccion = instruccion_por_step.get(
        step, f"Analiza los datos para el paso {step} de la ruta {route}."
    )

    prompt = f"""
Eres el analista de datos de la agencia. Analiza estos datos y extrae lo relevante.

DATOS CRUDOS:
{json.dumps(raw_data, ensure_ascii=False, indent=2)}

INSTRUCCIÓN — {route}/{step}:
{instruccion}

UMBRALES:
- CPA límite: ${CPA_LIMITE} MXN (alerta roja si se supera)
- CPA monitoreo: ${CPA_MONITOREO}–${CPA_LIMITE} MXN (alerta amarilla)
- Ocupación alerta: <{OCUPACION_ALERTA*100:.0f}%
- Ocupación urgente: <{OCUPACION_URGENTE*100:.0f}%

Output en JSON:
{{
  "resumen": "2–3 líneas de lo más importante",
  "metricas_clave": {{
    "gasto_total_mxn": 0,
    "conversiones_pixel": 0,
    "cpa_pixel_mxn": null,
    "cpa_real_mxn": null,
    "boletos_vendidos_boletera": null,
    "ocupacion_pct": null
  }},
  "alertas": [],
  "semaforo": {{
    "cpa": "🟢",
    "ocupacion": "🟢"
  }},
  "diagnostico_causa_raiz": null,
  "bloqueante": false,
  "raw_data": {{}}
}}

Incluye el raw_data completo tal cual lo recibiste.
Si "bloqueante" es true, el agente siguiente NO debe proceder.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )

    output = json.loads(response.text)
    output["raw_data"] = raw_data
    tokens = (
        response.usage_metadata.total_token_count
        if response.usage_metadata
        else 0
    )

    alertas = output.get("alertas", [])
    bloqueante = output.get("bloqueante", False)
    outcome = "blocked" if bloqueante else ("ok" if not alertas else "ok")

    log_event(
        route=route,
        step=step,
        agent="06 Analytics",
        model=GEMINI_MODEL,
        action=f"Pull + análisis datos (ruta {route})",
        result=(
            f"CPA pixel: {output.get('metricas_clave', {}).get('cpa_pixel_mxn', 'n/d')} MXN | "
            f"Alertas: {len(alertas)} | Bloqueante: {bloqueante}"
        ),
        tokens_used=tokens,
        outcome=outcome,
    )

    return output


# ── Pipeline principal ────────────────────────────────────────────────────────
def run_analytics(
    route: str = "D",
    step: str = "D-1",
    days: int = 7,
    desglose_campanas: bool = False,
) -> dict:
    """Pipeline completo: pull todas las fuentes → analizar → output JSON."""
    raw = {}
    raw.update(pull_meta_ads(days=days))
    raw.update(pull_google_ads())
    raw.update(pull_boletera())

    if step == "B-1":
        raw.update(verificar_pixel())
        # Verificación bloqueante de tags web (GA4 + Google Ads).
        # Si purchase no dispara, B-1 debe BLOQUEAR la activación de campaña.
        raw["tags_web"] = verificar_tags(dias=7)

    if step == "C-1" or desglose_campanas:
        raw.update(pull_meta_por_campana(days=days))

    return analizar_datos(raw, route=route, step=step)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    route = os.environ.get("ROUTE", "D")
    step = os.environ.get("STEP", "D-1")
    days = int(os.environ.get("DAYS", "7"))

    result = run_analytics(route=route, step=step, days=days)
    print(json.dumps(result, ensure_ascii=False, indent=2))
