#!/usr/bin/env python3
"""
Agente 03 — Media Monitor (Arranque D)
Platea · El Gorila S2 · jul–sep 2026

Qué hace:
  1. Fetch: Meta Ads + Google Ads + Boletera (últimos 7 días)
  2. Analiza con Gemini (Vertex AI) aplicando reglas-de-decision.md
  3. Genera reporte semanal en formato Arranque D
  4. Aplica reglas de autonomía: DETECTA y PROPONE; nunca actúa solo en dinero
  5. Envía reporte + alertas a elgorilateatro@gmail.com vía Resend

Uso:
  python agent.py               → reporte semanal completo
  python agent.py --check-now  → check rápido sin email

Env (.env):
  SYSTEM_USER_ACCESS_TOKEN     → Meta Graph API token
  AD_ACCOUNT_ID                → act_389427487828383
  GOOGLE_ADS_DEVELOPER_TOKEN   → Google Ads dev token
  GOOGLE_ADS_CLIENT_ID         → OAuth client ID
  GOOGLE_ADS_CLIENT_SECRET     → OAuth client secret
  GOOGLE_ADS_REFRESH_TOKEN     → OAuth refresh token
  GOOGLE_ADS_CUSTOMER_ID       → 2681423694
  BOLETERA_URL                 → https://elgorila-api.dupeyronosterlen.workers.dev
  BOLETERA_READ_TOKEN          → token read-only /api/reporte (cuando exista)
  RESEND_API_KEY               → para envío de email
  ALERT_EMAIL                  → elgorilateatro@gmail.com
  GCP_PROJECT                  → agencia-mkt-ia
  GCP_LOCATION                 → us-central1
  GEMINI_MODEL                 → gemini-2.5-pro
"""

import os
import sys
import json
import datetime
import requests
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ─── CONFIG ──────────────────────────────────────────────────────────────────
META_TOKEN        = os.getenv("SYSTEM_USER_ACCESS_TOKEN")
AD_ACCOUNT_ID     = os.getenv("AD_ACCOUNT_ID", "act_389427487828383")
GADS_DEV_TOKEN    = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
GADS_CLIENT_ID    = os.getenv("GOOGLE_ADS_CLIENT_ID")
GADS_CLIENT_SECRET= os.getenv("GOOGLE_ADS_CLIENT_SECRET")
GADS_REFRESH_TOKEN= os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
GADS_CUSTOMER_ID  = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "2681423694")
BOLETERA_URL         = os.getenv("BOLETERA_URL", "https://elgorila-api.dupeyronosterlen.workers.dev")
BOLETERA_REPORTE_URL = os.getenv("BOLETERA_REPORTE_URL", "https://elgorila-api.dupeyronosterlen.workers.dev")
BOLETERA_TOKEN       = os.getenv("BOLETERA_READ_TOKEN", "")
TEATRO_ID            = os.getenv("TEATRO_ID", "gorila")  # tid del worker — fix 2026-07-01
RESEND_API_KEY    = os.getenv("RESEND_API_KEY")
ALERT_EMAIL       = os.getenv("ALERT_EMAIL", "elgorilateatro@gmail.com")
GCP_PROJECT       = os.getenv("GCP_PROJECT", "agencia-mkt-ia")
GCP_LOCATION      = os.getenv("GCP_LOCATION", "us-central1")
GEMINI_MODEL      = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

# KPIs objetivo (de CLAUDE.md y reglas-de-decision.md)
CPA_MAX_ACEPTABLE = 350    # MXN — límite duro (no objetivo; por encima de esto, 🔴)
CPA_REFERENCIA    = 260    # MXN — CPA real S1 · objetivo a igualar o mejorar
BUDGET_DIARIO_MAX = 1500   # MXN — máximo sin OK de Dirección
FRECUENCIA_MAX    = 3.5    # umbral de fatiga de anuncio
CTR_MIN           = 1.2    # % mínimo aceptable Meta
AFORO_VENDIBLE    = 280    # boletos vendibles por función


# ═══════════════════════════════════════════════════════════════════════════════
# 1. FETCH — Meta Ads
# ═══════════════════════════════════════════════════════════════════════════════

def get_meta_performance(days: int = 7) -> dict:
    """Métricas de Meta Ads: campañas y ads sets de los últimos N días."""
    base = f"https://graph.facebook.com/v19.0/{AD_ACCOUNT_ID}"
    params_base = {
        "access_token": META_TOKEN,
        "date_preset": f"last_{days}d",
    }

    # Nivel campaña
    camp_params = {
        **params_base,
        "fields": "campaign_name,impressions,clicks,spend,ctr,cpc,reach,frequency,actions",
        "level": "campaign",
        "limit": 50,
    }
    r = requests.get(f"{base}/insights", params=camp_params, timeout=15)
    r.raise_for_status()
    campaigns = r.json().get("data", [])

    # Nivel adset (para frecuencia por segmento)
    adset_params = {
        **params_base,
        "fields": "adset_name,campaign_name,impressions,reach,frequency,spend,actions",
        "level": "adset",
        "limit": 100,
    }
    r2 = requests.get(f"{base}/insights", params=adset_params, timeout=15)
    r2.raise_for_status()
    adsets = r2.json().get("data", [])

    # Extraer compras de actions
    def extract_purchases(actions: list) -> int:
        for a in (actions or []):
            if a.get("action_type") in ("purchase", "offsite_conversion.fb_pixel_purchase"):
                return int(float(a.get("value", 0)))
        return 0

    total_spend  = sum(float(c.get("spend", 0)) for c in campaigns)
    total_clicks = sum(int(c.get("clicks", 0)) for c in campaigns)
    total_reach  = sum(int(c.get("reach", 0)) for c in campaigns)
    total_purchases_meta = sum(extract_purchases(c.get("actions", [])) for c in campaigns)
    cpa_meta = round(total_spend / total_purchases_meta, 2) if total_purchases_meta else None

    # Adsets con frecuencia alta
    high_freq = [
        {
            "adset": a.get("adset_name"),
            "campaign": a.get("campaign_name"),
            "frecuencia": float(a.get("frequency", 0)),
            "spend": float(a.get("spend", 0)),
        }
        for a in adsets
        if float(a.get("frequency", 0)) >= FRECUENCIA_MAX
    ]

    return {
        "source": "meta",
        "days": days,
        "spend": round(total_spend, 2),
        "clicks": total_clicks,
        "reach": total_reach,
        "purchases_meta_reported": total_purchases_meta,
        "cpa_meta_reported": cpa_meta,
        "campaigns": campaigns,
        "adsets_high_frequency": high_freq,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. FETCH — Google Ads
# ═══════════════════════════════════════════════════════════════════════════════

def get_gads_token() -> Optional[str]:
    """Obtiene access token de Google Ads via refresh token."""
    if not all([GADS_CLIENT_ID, GADS_CLIENT_SECRET, GADS_REFRESH_TOKEN]):
        return None
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": GADS_CLIENT_ID,
        "client_secret": GADS_CLIENT_SECRET,
        "refresh_token": GADS_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }, timeout=10)
    if r.ok:
        return r.json().get("access_token")
    return None


def get_google_ads_performance(days: int = 7) -> dict:
    """Métricas de Google Ads via API REST (GAQL)."""
    if not GADS_DEV_TOKEN:
        return {"source": "google_ads", "status": "skipped", "reason": "no dev token"}

    token = get_gads_token()
    if not token:
        return {"source": "google_ads", "status": "skipped", "reason": "no oauth token"}

    customer_id = GADS_CUSTOMER_ID.replace("-", "")
    # Calcular fechas
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)

    query = f"""
        SELECT
            campaign.name,
            campaign.status,
            metrics.cost_micros,
            metrics.clicks,
            metrics.impressions,
            metrics.conversions,
            metrics.ctr,
            metrics.average_cpc
        FROM campaign
        WHERE segments.date BETWEEN '{start}' AND '{end}'
          AND campaign.status = 'ENABLED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 50
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "developer-token": GADS_DEV_TOKEN,
        "Content-Type": "application/json",
    }
    url = f"https://googleads.googleapis.com/v21/customers/{customer_id}/googleAds:search"
    r = requests.post(url, headers=headers, json={"query": query}, timeout=15)

    if not r.ok:
        return {"source": "google_ads", "status": "error", "error": r.text[:200]}

    results = r.json().get("results", [])

    total_spend = sum(
        int(row.get("metrics", {}).get("costMicros", 0)) / 1_000_000
        for row in results
    )
    total_clicks = sum(int(row.get("metrics", {}).get("clicks", 0)) for row in results)
    total_conversions = sum(float(row.get("metrics", {}).get("conversions", 0)) for row in results)
    cpa_google = round(total_spend / total_conversions, 2) if total_conversions else None

    campaigns = [
        {
            "name": row.get("campaign", {}).get("name"),
            "spend": round(int(row.get("metrics", {}).get("costMicros", 0)) / 1_000_000, 2),
            "clicks": int(row.get("metrics", {}).get("clicks", 0)),
            "conversions": float(row.get("metrics", {}).get("conversions", 0)),
            "ctr": round(float(row.get("metrics", {}).get("ctr", 0)) * 100, 2),
        }
        for row in results
    ]

    return {
        "source": "google_ads",
        "days": days,
        "spend": round(total_spend, 2),
        "clicks": total_clicks,
        "conversions_google_reported": round(total_conversions, 1),
        "cpa_google_reported": cpa_google,
        "campaigns": campaigns,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. FETCH — Boletera (fuente de verdad)
# ═══════════════════════════════════════════════════════════════════════════════

SNAPSHOT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "config", "boletera_snapshot.json"
)


def load_snapshot() -> Optional[dict]:
    """Baseline de vendidos por función (config/boletera_snapshot.json). Nunca borrar ese archivo."""
    try:
        with open(SNAPSHOT_PATH) as f:
            return json.load(f)
    except Exception:
        return None


def save_snapshot(vendidos_por_funcion: dict) -> None:
    """Guarda el nuevo baseline al cierre de un run completo (no en --check-now)."""
    data = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "periodo": "auto_ag03",
        "nota": "Snapshot escrito por Agente 03 al cierre del run semanal. Baseline para el delta del período siguiente.",
        "vendidos_por_funcion": vendidos_por_funcion,
        "total_acumulado": sum(vendidos_por_funcion.values()),
    }
    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_boletera_data() -> dict:
    """Lee funciones y disponibilidad de la boletera propia."""
    base = BOLETERA_URL
    result = {"source": "boletera", "funciones": [], "resumen": {}}

    try:
        # Funciones activas
        r = requests.get(f"{base}/api/{TEATRO_ID}/funciones", timeout=10)
        r.raise_for_status()
        funciones = r.json()
        result["funciones_raw"] = funciones
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        return result

    # Para cada función, obtener disponibilidad
    hoy = datetime.date.today()
    funciones_detail = []
    total_vendidos = 0
    total_ingresos = 0

    for fn in funciones[:15]:  # max 15 funciones
        fecha_str = fn.get("fecha_iso") or fn.get("fecha", "")
        if not fecha_str:
            continue
        try:
            fecha = datetime.date.fromisoformat(fecha_str[:10])
        except ValueError:
            continue

        # Solo funciones pasadas (últimos 7 días) o próximas (siguientes 60 días)
        delta = (fecha - hoy).days
        if delta < -7 or delta > 60:
            continue

        try:
            r2 = requests.get(f"{base}/api/{TEATRO_ID}/disponibilidad", params={"fecha": fecha_str[:10]}, timeout=10)
            r2.raise_for_status()
            disp = r2.json()
        except Exception:
            disp = {}

        vendidos    = int(disp.get("vendidos", fn.get("vendidos", 0)))
        disponibles = int(disp.get("disponibles", fn.get("disponibles", AFORO_VENDIBLE)))
        total_fn    = int(disp.get("total", AFORO_VENDIBLE))
        ocupacion   = round(vendidos / total_fn * 100, 1) if total_fn else 0
        precio_prom = 350  # base; mejorar cuando /api/reporte esté disponible
        ingresos_est = vendidos * precio_prom

        fn_data = {
            "fecha": fecha_str[:10],
            "nombre": fn.get("nombre", f"Función {fecha_str[:10]}"),
            "dias_para_funcion": delta,
            "vendidos": vendidos,
            "disponibles": disponibles,
            "total_aforo": total_fn,
            "ocupacion_pct": ocupacion,
            "ingresos_estimados": ingresos_est,
        }
        funciones_detail.append(fn_data)

        # Acumular ventas de los últimos 7 días
        if -7 <= delta <= 0:
            total_vendidos += vendidos
            total_ingresos += ingresos_est

    # Ventas del período = delta vs snapshot. Las funciones aún no ocurren, así que
    # "vendidos" por función es acumulado — sin baseline el delta semanal es incalculable
    # (por eso el viejo cálculo por fecha de función daba siempre 0 antes del estreno).
    vendidos_actual = {f["fecha"]: f["vendidos"] for f in funciones_detail}
    result["vendidos_por_funcion_actual"] = vendidos_actual
    snapshot = load_snapshot()
    if snapshot:
        base = snapshot.get("vendidos_por_funcion", {})
        delta = sum(max(0, v - int(base.get(fecha, 0))) for fecha, v in vendidos_actual.items())
        ventas_semana = {
            "boletos": delta,
            "ingresos_estimados": delta * 350,
            "metodo": "delta_snapshot",
            "snapshot_baseline": snapshot.get("timestamp"),
        }
    else:
        ventas_semana = {"boletos": total_vendidos, "ingresos_estimados": total_ingresos}
        # Sin snapshot: intentar /api/reporte como fallback (totales acumulados, no fechas de venta)
        if BOLETERA_TOKEN:
            try:
                r3 = requests.get(
                    f"{BOLETERA_REPORTE_URL}/api/reporte",
                    headers={"Authorization": f"Bearer {BOLETERA_TOKEN}"},
                    params={"desde": str(hoy - datetime.timedelta(days=7)), "hasta": str(hoy)},
                    timeout=10,
                )
                if r3.ok:
                    reporte = r3.json()
                    ventas_semana = {
                        "boletos": reporte.get("total_boletos", total_vendidos),
                        "ingresos_reales": reporte.get("total_ingresos", total_ingresos),
                        "ordenes": reporte.get("total_ordenes", 0),
                    }
            except Exception:
                pass  # fallback a estimados

    # Próxima función
    proximas = [f for f in funciones_detail if f["dias_para_funcion"] >= 0]
    proximas.sort(key=lambda x: x["dias_para_funcion"])
    proxima = proximas[0] if proximas else None

    # Función más débil (próximas 4 semanas)
    proximas_30 = [f for f in proximas if f["dias_para_funcion"] <= 30]
    mas_debil = min(proximas_30, key=lambda x: x["ocupacion_pct"]) if proximas_30 else None

    result["funciones"] = funciones_detail
    result["ventas_semana"] = ventas_semana
    result["proxima_funcion"] = proxima
    result["funcion_mas_debil"] = mas_debil
    result["status"] = "ok"
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 4. REGLAS DE AUTONOMÍA (reglas-de-decision.md)
# ═══════════════════════════════════════════════════════════════════════════════

def apply_autonomy_rules(meta: dict, gads: dict, boletera: dict) -> dict:
    """
    Aplica la fórmula maestra y circuit breakers de reglas-de-decision.md.
    Devuelve: nivel de alerta, alertas activas y acciones propuestas.

    Niveles:
      🟢 NORMAL    → sin acción, log solamente
      🟡 PROPONE   → email a Dirección con recomendación, esperar 24h
      🔴 URGENTE   → email urgente AHORA (circuit breaker)
      ❌ NUNCA      → jamás ejecutar por esta IA solo (cambios de precio, apagar todo, etc.)
    """
    alertas = []
    nivel = "🟢"

    spend_total = meta.get("spend", 0) + gads.get("spend", 0)
    ventas_boletera = boletera.get("ventas_semana", {}).get("boletos", 0)
    cpa_real = round(spend_total / ventas_boletera, 2) if ventas_boletera > 0 else None
    proxima = boletera.get("proxima_funcion")
    cpa_meta_rep = meta.get("cpa_meta_reported")
    high_freq_adsets = meta.get("adsets_high_frequency", [])

    # ─── CIRCUIT BREAKERS (🔴 URGENTE — no esperar) ──────────────────────────

    # Gasto > 2× CPA objetivo con 0 ventas
    if spend_total > (CPA_MAX_ACEPTABLE * 2) and ventas_boletera == 0:
        alertas.append({
            "nivel": "🔴",
            "tipo": "GASTO_SIN_VENTAS",
            "mensaje": f"Se gastaron ${spend_total:.0f} MXN sin registrar ventas en la boletera.",
            "accion": "Verificar pixel Purchase + revisar boletera INMEDIATAMENTE antes de gastar más.",
        })
        nivel = "🔴"

    # Boletera en error
    if boletera.get("status") == "error":
        alertas.append({
            "nivel": "🔴",
            "tipo": "BOLETERA_CAIDA",
            "mensaje": f"No se pudo conectar a la boletera: {boletera.get('error', 'sin detalle')}",
            "accion": "Verificar que elgorila-api.dupeyronosterlen.workers.dev responde. Avisar al Agente 13.",
        })
        nivel = "🔴"

    # CPA real > $500 (50% sobre objetivo)
    if cpa_real and cpa_real > 500:
        alertas.append({
            "nivel": "🔴",
            "tipo": "CPA_CRITICO",
            "mensaje": f"CPA real = ${cpa_real:.0f} MXN (objetivo ≤$350, referencia S1 $260).",
            "accion": "Proponer a Dirección pausar audiencias con peor desempeño. No pausar solo.",
        })
        nivel = "🔴"

    # ─── ALERTAS ESTÁNDAR (🟡 PROPONE — Dirección decide) ───────────────────────────

    # CPA real entre $350 y $500
    if cpa_real and 350 < cpa_real <= 500 and nivel != "🔴":
        alertas.append({
            "nivel": "🟡",
            "tipo": "CPA_ALTO",
            "mensaje": f"CPA real = ${cpa_real:.0f} MXN, sobre el objetivo de $350.",
            "accion": "Revisar qué adsets están empujando el CPA. Proponer ajustes a Dirección.",
        })
        nivel = "🟡"

    # Alta frecuencia en adsets
    for adset in high_freq_adsets:
        alertas.append({
            "nivel": "🟡",
            "tipo": "FRECUENCIA_ALTA",
            "mensaje": f"Adset '{adset['adset']}' tiene frecuencia {adset['frecuencia']:.1f} (límite 3.5).",
            "accion": "Proponer rotar creatividades en este adset.",
        })
        if nivel == "🟢":
            nivel = "🟡"

    # Función próxima con ocupación baja
    if proxima:
        ocp = proxima["ocupacion_pct"]
        dias = proxima["dias_para_funcion"]
        if ocp < 50 and dias <= 5:
            alertas.append({
                "nivel": "🟡",
                "tipo": "OCUPACION_BAJA",
                "mensaje": f"Función del {proxima['fecha']}: {ocp}% de ocupación a {dias} días.",
                "accion": "Proponer activar ESPEJO2/ACADEMIA o subir pauta. Dirección decide.",
            })
            if nivel == "🟢":
                nivel = "🟡"
        elif ocp < 60 and dias <= 10:
            alertas.append({
                "nivel": "🟡",
                "tipo": "OCUPACION_MEDIA",
                "mensaje": f"Función del {proxima['fecha']}: {ocp}% de ocupación a {dias} días.",
                "accion": "Monitorear. Si baja de 50% a 5 días, activar protocolo.",
            })
            if nivel == "🟢":
                nivel = "🟡"

    # ─── NORMAL (🟢) ─────────────────────────────────────────────────────────
    if not alertas:
        alertas.append({
            "nivel": "🟢",
            "tipo": "NORMAL",
            "mensaje": "Todo dentro de parámetros.",
            "accion": "Continuar monitoreando. Sin acciones requeridas.",
        })

    return {
        "nivel_general": nivel,
        "cpa_real": cpa_real,
        "spend_total": spend_total,
        "ventas_boletera_semana": ventas_boletera,
        "alertas": alertas,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ANÁLISIS GEMINI
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """
Eres el Media Buyer IA de Platea, agencia de marketing teatral.
Tu cliente: El Gorila — monólogo de Humberto Dupeyrón, CDMX 2026.
Tu obsesión: CPA ≤ $350 MXN medido en la boletera propia, no en Meta.
Eres numérico, conciso y citas siempre la fuente.
Respondes en español, con JSON válido, sin texto extra.
NUNCA recomiendas pausar campañas o cambiar presupuesto sin aprobación de Dirección.
"""

ANALYSIS_SCHEMA = """{
  "resumen_ejecutivo": ["bullet 1", "bullet 2", "bullet 3"],
  "score": "BUENO | REGULAR | MALO",
  "insight_principal": "string",
  "tendencia_ventas": "SUBIENDO | ESTABLE | BAJANDO",
  "lo_que_funciono": "string — 1 línea",
  "lo_que_no_funciono": "string — 1 línea o null",
  "accion_semana": {
    "descripcion": "string — acción concreta",
    "agente_responsable": "03 Media Buyer | 06 Analytics | 12 Boletera",
    "requiere_ok_os": true
  },
  "propuestas_para_os": [
    {
      "prioridad": "ALTA | MEDIA | BAJA",
      "propuesta": "string",
      "razon": "string",
      "impacto_esperado": "string"
    }
  ]
}"""


def analyze_with_gemini(meta: dict, gads: dict, boletera: dict, autonomy: dict) -> dict:
    """Análisis ejecutivo con Gemini Vertex AI."""
    client = genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION)

    prompt = f"""
Analiza el performance semanal de El Gorila S2 y devuelve un JSON con este esquema:

ESQUEMA:
{ANALYSIS_SCHEMA}

DATOS META ADS (últimos 7 días):
Gasto: ${meta.get('spend', 0):.0f} MXN
Compras reportadas por Meta: {meta.get('purchases_meta_reported', 0)}
CPA Meta: ${meta.get('cpa_meta_reported', 'N/D')} MXN
Reach: {meta.get('reach', 0):,}
Adsets con frecuencia alta (≥3.5): {len(meta.get('adsets_high_frequency', []))}

DATOS GOOGLE ADS (últimos 7 días):
Gasto: ${gads.get('spend', 0):.0f} MXN
Conversiones Google: {gads.get('conversions_google_reported', 0)}
CPA Google: ${gads.get('cpa_google_reported', 'N/D')} MXN

BOLETERA (fuente de verdad):
Boletos vendidos esta semana: {boletera.get('ventas_semana', {}).get('boletos', 'N/D')}
Estado: {boletera.get('status', 'desconocido')}
Próxima función: {boletera.get('proxima_funcion', {}).get('fecha', 'N/D')} — {boletera.get('proxima_funcion', {}).get('ocupacion_pct', '?')}% ocupación

CPA REAL (gasto total ÷ ventas boletera):
${autonomy.get('cpa_real', 'N/D')} MXN (objetivo ≤$350, referencia S1 $260)

ALERTAS ACTIVAS:
{json.dumps(autonomy.get('alertas', []), ensure_ascii=False, indent=2)}

REGLAS CRÍTICAS:
- Nunca recomendar pausar campañas o cambiar presupuesto sin OK de Dirección
- Toda propuesta de cambio debe ir al flujo de aprobación 24h
- Citar siempre la fuente de cada dato

Responde SOLO el JSON, sin markdown ni texto adicional.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. REPORTE — Formato Arranque D
# ═══════════════════════════════════════════════════════════════════════════════

def build_report(
    meta: dict,
    gads: dict,
    boletera: dict,
    autonomy: dict,
    analysis: dict,
    week_label: str,
) -> str:
    """Genera el reporte semanal en formato Arranque D / reporte-semanal.md."""

    cpa_real = autonomy.get("cpa_real")
    nivel = autonomy.get("nivel_general", "🟢")
    spend_total = autonomy.get("spend_total", 0)
    ventas = autonomy.get("ventas_semana", boletera.get("ventas_semana", {}).get("boletos", 0))
    proxima = boletera.get("proxima_funcion") or {}
    debil = boletera.get("funcion_mas_debil") or {}

    # Semáforo CPA
    if cpa_real is None:
        semaforo_cpa = "⚪ Sin datos"
    elif cpa_real <= CPA_MAX_ACEPTABLE:
        semaforo_cpa = f"🟢 ${cpa_real:.0f} MXN (objetivo ≤$350)"
    elif cpa_real <= 450:
        semaforo_cpa = f"🟡 ${cpa_real:.0f} MXN (sobre objetivo)"
    else:
        semaforo_cpa = f"🔴 ${cpa_real:.0f} MXN (CRÍTICO)"

    # Semáforo ocupación próxima función
    ocp = proxima.get("ocupacion_pct")
    if ocp is None:
        semaforo_ocp = "⚪ Sin datos"
    elif ocp >= 70:
        semaforo_ocp = f"🟢 {ocp}% próxima función ({proxima.get('fecha', '')})"
    elif ocp >= 50:
        semaforo_ocp = f"🟡 {ocp}% próxima función ({proxima.get('fecha', '')})"
    else:
        semaforo_ocp = f"🔴 {ocp}% próxima función ({proxima.get('fecha', '')})"

    tendencia = analysis.get("tendencia_ventas", "ESTABLE")
    semaforo_tend = {"SUBIENDO": "🟢 ↑", "ESTABLE": "🟡 →", "BAJANDO": "🔴 ↓"}.get(tendencia, "⚪")

    alertas_txt = ""
    for a in autonomy.get("alertas", []):
        if a["nivel"] != "🟢":
            alertas_txt += f"\n{a['nivel']} [{a['tipo']}] {a['mensaje']}\n   → {a['accion']}"
    if not alertas_txt:
        alertas_txt = "Sin alertas esta semana."

    propuestas_txt = ""
    for p in analysis.get("propuestas_para_os", []):
        propuestas_txt += (
            f"\n{p['prioridad']}: {p['propuesta']}\n"
            f"   Razón: {p['razon']}\n"
            f"   Impacto esperado: {p['impacto_esperado']}\n"
        )
    if not propuestas_txt:
        propuestas_txt = "Sin propuestas de cambio esta semana."

    resumen = "\n".join(f"• {b}" for b in analysis.get("resumen_ejecutivo", []))

    accion = analysis.get("accion_semana", {})
    accion_txt = (
        f"{accion.get('descripcion', 'N/D')}\n"
        f"   Agente: {accion.get('agente_responsable', 'N/D')} | "
        f"Requiere OK de Dirección: {'Sí' if accion.get('requiere_ok_os') else 'No'}"
    )

    report = f"""
╔══════════════════════════════════════════════════════════════════╗
║          REPORTE SEMANAL PLATEA — ARRANQUE D                    ║
║          El Gorila S2 · Teatro Wilberto Cantón                  ║
║          {week_label:<50}║
╚══════════════════════════════════════════════════════════════════╝

SEMÁFORO GENERAL: {nivel}
─────────────────────────────────
CPA:      {semaforo_cpa}
Ocupación:{semaforo_ocp}
Ventas:   {semaforo_tend} ventas

───────────────────────────────────────────────────────────────────
1. RESUMEN EJECUTIVO
───────────────────────────────────────────────────────────────────
{resumen}

───────────────────────────────────────────────────────────────────
2. VENTAS DE LA SEMANA (Boletera — fuente de verdad)
───────────────────────────────────────────────────────────────────
Boletos vendidos: {boletera.get('ventas_semana', {}).get('boletos', 'N/D')}
Ingresos estimados: ${boletera.get('ventas_semana', {}).get('ingresos_estimados', 'N/D'):,.0f} MXN
Próxima función: {proxima.get('fecha', 'N/D')} — {proxima.get('ocupacion_pct', '?')}% ocupación
Función más débil: {debil.get('fecha', 'N/D')} — {debil.get('ocupacion_pct', '?')}% en {debil.get('dias_para_funcion', '?')} días

───────────────────────────────────────────────────────────────────
3. CAMPAÑAS (Meta + Google)
───────────────────────────────────────────────────────────────────
                    Meta              Google
Gasto semanal:      ${meta.get('spend', 0):<10.0f}        ${gads.get('spend', 0):<10.0f}
CPA reportado:      ${meta.get('cpa_meta_reported') or 'N/D':<10}        ${gads.get('cpa_google_reported') or 'N/D':<10}
Conversiones ads:   {meta.get('purchases_meta_reported', 0):<10}        {gads.get('conversions_google_reported', 0):<10}
Ventas boletera:    {ventas} (ambas plataformas combinadas)
CPA REAL:           ${cpa_real or 'N/D'} MXN (gasto total ÷ ventas boletera)
Delta tracking:     {f'Meta reporta {meta.get("purchases_meta_reported", 0)} compras vs {ventas} en boletera' if ventas else 'Sin datos boletera'}

───────────────────────────────────────────────────────────────────
4. ALERTAS ACTIVAS
───────────────────────────────────────────────────────────────────
{alertas_txt}

───────────────────────────────────────────────────────────────────
5. LO QUE FUNCIONÓ / NO FUNCIONÓ
───────────────────────────────────────────────────────────────────
✅ {analysis.get('lo_que_funciono', 'Ver análisis completo')}
❌ {analysis.get('lo_que_no_funciono', 'Sin issues críticos identificados')}

───────────────────────────────────────────────────────────────────
6. ACCIÓN CONCRETA PARA ESTA SEMANA
───────────────────────────────────────────────────────────────────
{accion_txt}

───────────────────────────────────────────────────────────────────
7. PROPUESTAS PARA APROBACIÓN DE OS (regla 24h)
───────────────────────────────────────────────────────────────────
{propuestas_txt}

───────────────────────────────────────────────────────────────────
Score general: {analysis.get('score', 'N/D')} | Insight: {analysis.get('insight_principal', 'N/D')}
Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | Agente 03 Media Monitor + Agente 06 Analytics
───────────────────────────────────────────────────────────────────
"""
    return report


# ═══════════════════════════════════════════════════════════════════════════════
# 7. NOTIFICACIÓN — Email vía Resend
# ═══════════════════════════════════════════════════════════════════════════════

def send_email(subject: str, body: str, urgente: bool = False) -> bool:
    """Envía email a Dirección vía Resend."""
    if not RESEND_API_KEY:
        print(f"⚠️  RESEND_API_KEY no configurada — no se envió email")
        print(f"   Para: {ALERT_EMAIL}")
        print(f"   Asunto: {subject}")
        return False

    emoji = "🚨 " if urgente else "📊 "
    r = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": "platea@elgorilateatro.com.mx",
            "to": [ALERT_EMAIL],
            "subject": f"{emoji}{subject}",
            "text": body,
        },
        timeout=15,
    )
    if r.ok:
        print(f"✅ Email enviado a {ALERT_EMAIL}: {subject}")
        return True
    else:
        print(f"❌ Error enviando email: {r.status_code} {r.text[:100]}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# 8. LOG
# ═══════════════════════════════════════════════════════════════════════════════

def save_log(data: dict) -> str:
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(log_dir, f"monitor_{ts}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    return filepath


# ═══════════════════════════════════════════════════════════════════════════════
# 9. MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    check_only = "--check-now" in sys.argv
    hoy = datetime.date.today()
    semana_inicio = hoy - datetime.timedelta(days=7)
    week_label = f"Semana {semana_inicio.strftime('%d %b')} – {hoy.strftime('%d %b %Y')}"

    print("🤖 Agente 03 — Media Monitor (Arranque D)")
    print("=" * 55)
    print(f"   Período: {week_label}")
    print()

    # ── 1. Fetch ──────────────────────────────────────────
    print("📊 Fetching Meta Ads...")
    try:
        meta = get_meta_performance(days=7)
        print(f"   Meta: ${meta['spend']:.0f} gasto · {meta['purchases_meta_reported']} compras reportadas")
    except Exception as e:
        meta = {"source": "meta", "status": "error", "error": str(e), "spend": 0}
        print(f"   ❌ Error Meta: {e}")

    print("📊 Fetching Google Ads...")
    try:
        gads = get_google_ads_performance(days=7)
        if gads.get("status") == "skipped":
            print(f"   ⚪ Google Ads: {gads.get('reason', 'skipped')}")
        else:
            print(f"   Google: ${gads.get('spend', 0):.0f} gasto · {gads.get('conversions_google_reported', 0)} conversiones")
    except Exception as e:
        gads = {"source": "google_ads", "status": "error", "error": str(e), "spend": 0}
        print(f"   ❌ Error Google Ads: {e}")

    print("🎟️  Fetching Boletera...")
    try:
        boletera = get_boletera_data()
        ventas = boletera.get("ventas_semana", {}).get("boletos", "?")
        proxima = boletera.get("proxima_funcion") or {}
        print(f"   Boletera: {ventas} boletos esta semana · próxima {proxima.get('fecha', 'N/D')} {proxima.get('ocupacion_pct', '?')}%")
    except Exception as e:
        boletera = {"source": "boletera", "status": "error", "error": str(e)}
        print(f"   ❌ Error Boletera: {e}")

    # ── 2. Autonomy rules ─────────────────────────────────
    print("\n🔍 Aplicando reglas de autonomía...")
    autonomy = apply_autonomy_rules(meta, gads, boletera)
    nivel = autonomy["nivel_general"]
    print(f"   Nivel: {nivel}")
    for a in autonomy["alertas"]:
        if a["nivel"] != "🟢":
            print(f"   {a['nivel']} {a['tipo']}: {a['mensaje'][:60]}...")

    # ── 3. Check-only mode ────────────────────────────────
    if check_only:
        cpa = autonomy.get("cpa_real")
        print(f"\n⚡ CHECK RÁPIDO")
        print(f"   CPA real: ${cpa or 'N/D'} MXN (objetivo $350)")
        print(f"   Nivel: {nivel}")
        if nivel == "🔴":
            alerta_urgente = next((a for a in autonomy["alertas"] if a["nivel"] == "🔴"), None)
            if alerta_urgente:
                send_email(
                    f"[URGENTE] {alerta_urgente['tipo']} — El Gorila S2",
                    f"ALERTA URGENTE — Agente 03 Media Monitor\n\n"
                    f"{alerta_urgente['mensaje']}\n\nAcción: {alerta_urgente['accion']}\n\n"
                    f"CPA real: ${cpa or 'N/D'} MXN\nGasto: ${autonomy['spend_total']:.0f} MXN\n"
                    f"Ventas boletera: {autonomy['ventas_boletera_semana']} boletos\n\n"
                    f"— Agente 03 Media Monitor, {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    urgente=True
                )
        return

    # ── 4. Análisis Gemini ────────────────────────────────
    print("\n🧠 Consultando Gemini (Vertex AI)...")
    try:
        analysis = analyze_with_gemini(meta, gads, boletera, autonomy)
        print(f"   Score: {analysis.get('score', 'N/D')} | {analysis.get('insight_principal', '')[:60]}...")
    except Exception as e:
        print(f"   ❌ Error Gemini: {e}")
        analysis = {
            "resumen_ejecutivo": ["Error al conectar con Gemini — revisar credenciales GCP"],
            "score": "REGULAR",
            "insight_principal": f"Error Gemini: {e}",
            "tendencia_ventas": "ESTABLE",
            "lo_que_funciono": "N/D",
            "lo_que_no_funciono": "N/D",
            "accion_semana": {"descripcion": "Revisar conexión Gemini", "agente_responsable": "13 Programador", "requiere_ok_os": False},
            "propuestas_para_os": [],
        }

    # ── 5. Reporte ────────────────────────────────────────
    print("\n📋 Generando reporte Arranque D...")
    report_txt = build_report(meta, gads, boletera, autonomy, analysis, week_label)
    print(report_txt)

    # ── 6. Log ────────────────────────────────────────────
    log_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "week": week_label,
        "meta": meta,
        "google_ads": gads,
        "boletera": boletera,
        "autonomy": autonomy,
        "gemini_analysis": analysis,
    }
    filepath = save_log(log_data)
    print(f"💾 Log: {filepath}")

    # ── 7. Enviar email ───────────────────────────────────
    urgente = nivel == "🔴"
    subject = f"[{'URGENTE ' if urgente else ''}Arranque D] Reporte Semanal El Gorila S2 — {week_label}"
    send_email(subject, report_txt, urgente=urgente)

    # ── 8. Nuevo snapshot ─────────────────────────────────
    # Solo el run completo mueve el baseline; --check-now nunca lo toca.
    vendidos_actual = boletera.get("vendidos_por_funcion_actual")
    if vendidos_actual and boletera.get("status") == "ok":
        save_snapshot(vendidos_actual)
        print(f"💾 Snapshot actualizado: {sum(vendidos_actual.values())} boletos acumulados")

    print("\n✅ Arranque D completado.")


if __name__ == "__main__":
    main()
