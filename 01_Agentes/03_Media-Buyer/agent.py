#!/usr/bin/env python3
"""
Agente 03 — Media Monitor (Arranque D)
Platea · El Gorila S2 · jul–sep 2026

Qué hace:
  1. Fetch: Meta Ads + Google Ads + Boletera (últimos 7 días)
  2. Analiza con Gemini (Vertex AI) aplicando reglas-de-decision.md
  3. Genera reporte semanal en formato Arranque D
  4. Aplica reglas de autonomía: ejecuta presupuesto si reglas OK (escalado.yaml); alerta si circuit breaker
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
import yaml
import datetime
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).resolve().parents[2] / "privado" / "credenciales" / ".env")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "01_Agentes" / "_lib"))
from gemini_client import make_client
_PRODUCCION_ACTIVA = (ROOT / "config" / "produccion-activa.txt").read_text().strip()
CONFIG_FILE = ROOT / "03_Producciones" / _PRODUCCION_ACTIVA / "produccion.yaml"


def cargar_config() -> dict:
    return yaml.safe_load(CONFIG_FILE.read_text())


def cargar_escalado() -> dict:
    path = ROOT / "config" / "escalado.yaml"
    if path.exists():
        return yaml.safe_load(path.read_text()) or {}
    return {}


_config = cargar_config()
_escalado = cargar_escalado()
_esc_meta = _escalado.get("escalado_meta", {})
ESCALADO_INCREMENTO_PCT = int(_esc_meta.get("incremento_max_pct", 15))
ESCALADO_DIAS_MIN = int(_esc_meta.get("dias_entre_cambios_min", 3))
ESCALADO_DIAS_MAX = int(_esc_meta.get("dias_entre_cambios_max", 5))
ESCALADO_FUENTE = _escalado.get("fuente_humana", "config/reglas-algoritmos-ads.md")
_esc_gads = _escalado.get("escalado_google", {})
ESCALADO_GADS_PCT = int(_esc_gads.get("incremento_max_pct", 15))
ESCALADO_GADS_HORAS_MIN = int(_esc_gads.get("horas_entre_cambios_min", 48))
GOOGLE_CABLE_FILE = Path(__file__).resolve().parent / "google-cable.yaml"
GOOGLE_CABLE_STATE = Path(__file__).resolve().parent / "google-cable-state.json"


def texto_escalado_presupuesto() -> str:
    return (
        f"+{ESCALADO_INCREMENTO_PCT}% ({ESCALADO_DIAS_MIN}–{ESCALADO_DIAS_MAX}d entre cambios; "
        f"ver {ESCALADO_FUENTE})"
    )

FUNNEL_CABLE_FILE = Path(__file__).resolve().parent / "funnel-cable.yaml"
FUNNEL_SNAPSHOT_FILE = Path(__file__).resolve().parent / "funnel-cable-snapshot.json"


def cargar_funnel_cable() -> dict:
    if FUNNEL_CABLE_FILE.exists():
        return yaml.safe_load(FUNNEL_CABLE_FILE.read_text()) or {}
    return {}


def _funnel_set_ids(cable: dict) -> dict:
    """Aplana sets del yaml a clave → adset id. TOFU.ids → TOFU_ESPEJO, etc."""
    out = {}
    for key, spec in (cable.get("sets") or {}).items():
        if not isinstance(spec, dict):
            continue
        if spec.get("id"):
            out[key] = str(spec["id"])
        ids = spec.get("ids") or {}
        if isinstance(ids, dict):
            for sub, aid in ids.items():
                out[f"{key}_{sub}"] = str(aid)
    return out


def _funnel_actions(row: dict) -> dict:
    m = {a["action_type"]: float(a["value"]) for a in (row.get("actions") or [])}

    def pick(*keys):
        for k in keys:
            if k in m:
                return m[k]
        return 0.0

    return {
        "link_click": pick("link_click"),
        "lpv": pick("landing_page_view"),
        "vc": pick("offsite_conversion.fb_pixel_view_content", "view_content"),
        "ic": pick("offsite_conversion.fb_pixel_initiate_checkout", "initiate_checkout"),
        "atc": pick("offsite_conversion.fb_pixel_add_to_cart", "add_to_cart"),
        "purchase": pick("offsite_conversion.fb_pixel_purchase", "purchase"),
    }


def refresh_funnel_cable_snapshot() -> dict:
    """Pisa funnel-cable-snapshot.json con last_7d de Meta. Nunca inventa números."""
    cable = cargar_funnel_cable()
    ids = _funnel_set_ids(cable)
    if not META_TOKEN or not ids:
        return {}
    graph = "https://graph.facebook.com/v21.0"
    preset = cable.get("date_preset_snapshot") or "last_7d"
    out = {
        "pulled_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "date_preset": preset,
        "source": "Meta Graph API v21 + funnel-cable.yaml (agent.py)",
        "sets": {},
    }
    for key, aid in ids.items():
        meta = requests.get(
            f"{graph}/{aid}",
            params={
                "access_token": META_TOKEN,
                "fields": "name,status,effective_status,daily_budget,campaign{id,name,daily_budget}",
            },
            timeout=60,
        ).json()
        if meta.get("error"):
            out["sets"][key] = {"id": aid, "error": meta["error"].get("message")}
            continue
        ins = requests.get(
            f"{graph}/{aid}/insights",
            params={
                "access_token": META_TOKEN,
                "fields": "spend,impressions,clicks,ctr,actions",
                "date_preset": preset,
            },
            timeout=60,
        ).json()
        row = (ins.get("data") or [{}])[0]
        camp = meta.get("campaign") or {}
        daily = int(meta.get("daily_budget") or 0) / 100
        camp_daily = int(camp.get("daily_budget") or 0) / 100
        out["sets"][key] = {
            "id": aid,
            "name": meta.get("name"),
            "status": meta.get("status"),
            "effective_status": meta.get("effective_status"),
            "daily_budget_mxn": daily,
            "campaign_name": camp.get("name"),
            "campaign_daily_budget_mxn": camp_daily or None,
            "spend_7d": float(row.get("spend") or 0),
            "clicks_7d": int(float(row.get("clicks") or 0)),
            "ctr_7d": float(row["ctr"]) if row.get("ctr") else None,
            **_funnel_actions(row),
        }
    FUNNEL_SNAPSHOT_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    return out


def texto_google_cable() -> str:
    """Reglas + último state Search. Gemini no inventa budget ni pide a Dirección que suba Search."""
    cable = cargar_google_cable()
    state = cargar_google_state()
    spec = cable.get("search") or {}
    reglas = spec.get("reglas") or {}
    st = state.get("search") or {}
    return (
        "CABLE GOOGLE SEARCH (google-cable.yaml + state; Ag-03 escala o mantiene solo):\n"
        f"campaña {spec.get('campaign_name')} ENABLED · budget_vivo state=${st.get('daily_budget_mxn')}/d\n"
        f"último cambio: {st.get('last_change_from_mxn')}→{st.get('last_change_to_mxn')} "
        f"por {st.get('last_change_by')} @ {st.get('last_change_at')} · "
        f"acción={st.get('last_action')} · {st.get('last_action_reason')}\n"
        f"reglas: CPA Google ≤${reglas.get('cpa_search_escalar_max')} + lost IS budget "
        f"≥{float(reglas.get('lost_is_budget_min') or 0):.0%} + banda "
        f"{reglas.get('bandas_cuenta_ok')} + 48h. Stripe UTM corrobora (Google subcuenta). "
        "Adelantar 48h = solo va Dirección (día de función). No pedirle a Dirección que suba Search a mano.\n"
    )


def texto_funnel_cable() -> str:
    """Roles yaml + números del último snapshot. Gemini no debe inventar gasto."""
    cable = cargar_funnel_cable()
    snap = {}
    if FUNNEL_SNAPSHOT_FILE.exists():
        try:
            snap = json.loads(FUNNEL_SNAPSHOT_FILE.read_text())
        except Exception:
            snap = {}
    reglas = cable.get("reglas_movimiento") or {}
    compact = []
    for key, s in (snap.get("sets") or {}).items():
        if s.get("error"):
            compact.append(f"{key}: ERROR {s['error']}")
            continue
        compact.append(
            f"{key} ({s.get('name')}): status={s.get('effective_status')} "
            f"budget=${s.get('daily_budget_mxn')}/d"
            + (f" camp_cbo=${s.get('campaign_daily_budget_mxn')}/d" if s.get("campaign_daily_budget_mxn") else "")
            + f" spend_7d=${s.get('spend_7d')} LPV={s.get('lpv')} IC={s.get('ic')} "
            f"ATC={s.get('atc')} Purchase={s.get('purchase')}"
        )
    return (
        "CABLE FUNNEL VIVO (funnel-cable.yaml + snapshot API; no inventar números):\n"
        f"pulled_at: {snap.get('pulled_at', 'sin snapshot')} · preset: {snap.get('date_preset', '?')}\n"
        f"reglas: {json.dumps(reglas, ensure_ascii=False)}\n"
        f"hilos: {json.dumps(cable.get('cable'), ensure_ascii=False)}\n"
        + "\n".join(compact)
        + "\n"
        "Si ESCALAR: no TOFU ni AFIN para volumen. closer = BOFU_PURCHASE. SOCIAL90 no reencender. "
        "TOFU es captador: recorte máx 15% ABO, no pausar los 3, no tocar opt/URL/creativo. "
        "BOFU_PURCHASE: no tocar budget/audiencia/opt antes de bofu_no_tocar_hasta. "
        "No pausar MOFU_VC. HOT PAUSED. last_7d Meta = días cerrados (HOY no entra hasta mañana)."
    )


CORTESIAS_FILE = ROOT / "04_Operaciones" / "cortesias-conocidas.json"


def cortesias_conocidas(fecha_str: str) -> int:
    """Cortesías/altas manuales conocidas para una función — se restan de 'vendidos' antes de calcular CPA (manifiesto manual, ver 04_Operaciones/cortesias-conocidas.json)."""
    try:
        data = json.loads(CORTESIAS_FILE.read_text())
        return int(data.get("por_funcion", {}).get(fecha_str, {}).get("cortesias", 0))
    except Exception:
        return 0


def _bitacora(action: str, result: str, outcome: str = "ok") -> None:
    """Registro operativo — nunca tumba el agente."""
    try:
        ops = Path(__file__).resolve().parents[2] / "04_Operaciones"
        if str(ops) not in sys.path:
            sys.path.insert(0, str(ops))
        from platea_log import log_run
        log_run("03 Media Buyer", action, result, outcome=outcome, step="ag03")
    except Exception:
        pass


# ─── CONFIG ──────────────────────────────────────────────────────────────────
META_TOKEN        = os.getenv("SYSTEM_USER_ACCESS_TOKEN")
AD_ACCOUNT_ID     = os.getenv("AD_ACCOUNT_ID", _config["ads"]["meta"]["ad_account_id"])
GADS_DEV_TOKEN    = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
GADS_CLIENT_ID    = os.getenv("GOOGLE_ADS_CLIENT_ID")
GADS_CLIENT_SECRET= os.getenv("GOOGLE_ADS_CLIENT_SECRET")
GADS_REFRESH_TOKEN= os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
GADS_CUSTOMER_ID  = os.getenv("GOOGLE_ADS_CUSTOMER_ID", _config["ads"]["google"]["ads_customer_id"])
GADS_LOGIN_CUSTOMER_ID = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "8974056133")
BOLETERA_URL         = os.getenv("BOLETERA_URL", _config["boletera"]["worker_api"])
BOLETERA_REPORTE_URL = os.getenv("BOLETERA_REPORTE_URL", _config["boletera"]["worker_api"])
BOLETERA_TOKEN       = os.getenv("BOLETERA_READ_TOKEN", "")
TEATRO_ID            = os.getenv("TEATRO_ID", _config["temporada"]["venue"]["tid"])  # tid del worker — ya NO cae a "gorila" por default
RESEND_API_KEY    = os.getenv("RESEND_API_KEY")
ALERT_EMAIL       = os.getenv("ALERT_EMAIL", _config["comunicacion"]["email_reportes"])
WA_TOKEN          = os.getenv("WA_MESSAGING_TOKEN")
WA_PHONE_NUMBER_ID = os.getenv("WA_PHONE_NUMBER_ID", _config["comunicacion"]["whatsapp_api"]["phone_number_id"])
WA_DESTINO_OS     = os.getenv("WA_DESTINO_OS", _config["comunicacion"]["whatsapp_os_personal"]["numero"])
GCP_PROJECT       = os.getenv("GCP_PROJECT", "agencia-mkt-ia")
GCP_LOCATION      = os.getenv("GCP_LOCATION", "us-central1")
GEMINI_MODEL      = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
STRIPE_RESTRICTED_KEY = os.getenv("STRIPE_RESTRICTED_KEY")
UMBRAL_VENTA_REAL_MXN = 245  # regla de Dirección (19 jul): cualquier boleto pagado por debajo de esto (precio estudiante, el más bajo real) es cortesía/prueba, no venta


# ═══════════════════════════════════════════════════════════════════════════════
# STRIPE — clasificación real vs. cortesía por precio (regla Dirección 19 jul)
# ═══════════════════════════════════════════════════════════════════════════════

def _stripe_paginar(url: str, params: dict) -> list[dict]:
    out = []
    auth = (STRIPE_RESTRICTED_KEY, "")
    while True:
        r = requests.get(url, params=params, auth=auth, timeout=30)
        r.raise_for_status()
        data = r.json()
        out += data.get("data", [])
        if not data.get("has_more"):
            return out
        params["starting_after"] = out[-1]["id"]


def ventas_reales_stripe(dias: int = 7) -> dict | None:
    """
    Boletos PAGADOS reales de los últimos `dias` días, vía Stripe (no vía contador KV).
    Regla: precio_unitario = amount_total / cantidad. Si < UMBRAL_VENTA_REAL_MXN → cortesía/prueba,
    NO cuenta como venta ni entra al CPA ni a ingresos. Sirve tanto para el total del período como
    para desglose por función (metadata.fecha, escrito por el checkout al crear la sesión).
    Retorna None si no hay llave configurada (agente sigue funcionando con el método viejo).
    """
    if not STRIPE_RESTRICTED_KEY:
        return None
    try:
        desde_ts = int((datetime.datetime.now() - datetime.timedelta(days=dias)).timestamp())
        sesiones = _stripe_paginar(
            "https://api.stripe.com/v1/checkout/sessions",
            {"limit": 100, "created[gte]": desde_ts, "status": "complete"},
        )
    except Exception:
        return None

    boletos_reales = 0
    ingresos_reales = 0.0
    boletos_cortesia_stripe = 0
    detalle_cortesia = []
    por_funcion: dict[str, dict] = {}

    for s in sesiones:
        if s.get("payment_status") != "paid":
            continue
        md = s.get("metadata") or {}
        cantidad = int(md.get("cantidad", 1) or 1)
        monto = (s.get("amount_total") or 0) / 100
        precio_unit = monto / cantidad if cantidad else monto
        fecha_fn = md.get("fecha", "sin_fecha")
        fn = por_funcion.setdefault(fecha_fn, {"reales": 0, "cortesia": 0, "ingresos_reales": 0.0})

        if precio_unit >= UMBRAL_VENTA_REAL_MXN:
            boletos_reales += cantidad
            ingresos_reales += monto
            fn["reales"] += cantidad
            fn["ingresos_reales"] += monto
        else:
            boletos_cortesia_stripe += cantidad
            fn["cortesia"] += cantidad
            detalle_cortesia.append({
                "id": s["id"][-8:], "fecha_funcion": fecha_fn,
                "cantidad": cantidad, "monto": monto, "precio_unit": round(precio_unit, 2),
            })

    return {
        "dias": dias,
        "boletos_reales": boletos_reales,
        "ingresos_reales": ingresos_reales,
        "boletos_cortesia_stripe": boletos_cortesia_stripe,
        "detalle_cortesia_stripe": detalle_cortesia,
        "por_funcion": por_funcion,
    }

# KPIs / finanzas (produccion.yaml → campanas/00-MODELO-NEGOCIO.md + 00-EQUILIBRIO-CON-PAUTA.md)
# Techo de decisión = CPA boletera vs margen, NO un tope diario de gasto.
CPA_ESCALA          = _config["kpis"]["cpa_target"]              # MXN — < esto → proponer escalado (escalado.yaml)
CPA_MAX_ACEPTABLE   = _config["kpis"]["cpa_max_aceptable"]      # MXN — tablas exactas (= margen general)
CPA_CIRCUIT_BREAKER = _config["kpis"]["cpa_circuit_breaker"]    # MXN — pausar set si sostenido 3d
CPA_REFERENCIA      = _config["kpis"]["cpa_referencia_s1"]
MARGEN_BOLETO       = _config["finanzas"]["margen_boleto_general"]  # MXN — utilidad bruta/boleto zona renta fija
FIJO_POR_FUNCION    = _config["finanzas"].get(
    "fijo_por_funcion", _config["finanzas"].get("costo_por_funcion", 14200)
)  # MXN — alias costo_por_funcion en produccion.yaml
BE_TEATRO_BOLETOS   = max(1, round(FIJO_POR_FUNCION / MARGEN_BOLETO))  # ~41 sin ads
BE_BRUTO_BOLETOS   = _config["finanzas"].get("break_even_boletos", BE_TEATRO_BOLETOS)
BUDGET_DIARIO_SOFT  = _config["kpis"]["budget_diario_max"]       # soft: avisar a Dirección; no frena si CPA sano
FRECUENCIA_MAX      = _config["kpis"]["frecuencia_max"]
CTR_MIN             = 1.2
AFORO_VENDIBLE      = _config["temporada"]["venue"]["aforo_vendible"]
# Alias legado (algunos logs viejos)
BUDGET_DIARIO_MAX   = BUDGET_DIARIO_SOFT

# Fórmula maestra: reglas-de-decision.md + 00-EQUILIBRIO-CON-PAUTA.md
MIN_MUESTRA_CONVERSIONES = 10   # conversiones mínimas antes de escalar/pausar por CPA
VENTANA_TENDENCIA_DIAS   = 3    # promedio móvil — no juzgar con un solo snapshot


# ═══════════════════════════════════════════════════════════════════════════════
# 1. FETCH — Meta Ads
# ═══════════════════════════════════════════════════════════════════════════════

def get_meta_performance(days: int = 7, since: datetime.date | None = None) -> dict:
    """Métricas de Meta Ads: campañas y ads sets de los últimos N días o desde `since`."""
    base = f"https://graph.facebook.com/v19.0/{AD_ACCOUNT_ID}"
    if since:
        params_base = {
            "access_token": META_TOKEN,
            "time_range": json.dumps({
                "since": since.isoformat(),
                "until": datetime.date.today().isoformat(),
            }),
        }
    else:
        preset_days = days if days in (7, 14, 28, 30, 90) else 30
        params_base = {
            "access_token": META_TOKEN,
            "date_preset": f"last_{preset_days}d",
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
# 1B. ANÁLISIS — Cobertura de creativos (matemático, sin Gemini, sin adivinar)
# ═══════════════════════════════════════════════════════════════════════════════
# Nace del hallazgo del 22 jul: dos creativos idénticos (mismo creative_id) corrían
# duplicados entre adsets de la misma campaña mientras el mejor creativo (COMERCIAL)
# no llegaba a la audiencia fría de Interés Cultural. Esto lo detecta un humano solo
# si audita ad-por-ad a mano — el agente debe hacerlo cada semana, no una sesión de Claude Code.

CREATIVE_MIN_IMPRESIONES = 300  # bajo esto, la muestra es demasiado chica para juzgar CTR/CPC


def get_ad_level_creative_data(days: int = 14) -> list[dict]:
    """Trae, para campañas ACTIVAS, cada anuncio con su creative_id, adset, campaña,
    impresiones/clicks/spend/CTR/CPC y compras. Es el insumo de analyze_creative_coverage()."""
    base = f"https://graph.facebook.com/v19.0/{AD_ACCOUNT_ID}"

    # 1) Insights a nivel ad (spend/impresiones/clicks/acciones)
    insights_params = {
        "access_token": META_TOKEN,
        "date_preset": f"last_{days}d",
        "level": "ad",
        "fields": "ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,impressions,clicks,spend,actions",
        "filtering": json.dumps([{"field": "ad.effective_status", "operator": "IN", "value": ["ACTIVE"]}]),
        "limit": 200,
    }
    r = requests.get(f"{base}/insights", params=insights_params, timeout=20)
    r.raise_for_status()
    insights = r.json().get("data", [])

    if not insights:
        return []

    # 2) creative_id por ad (un solo request con todos los ad_ids activos de la cuenta)
    ads_params = {
        "access_token": META_TOKEN,
        "fields": "id,creative{id}",
        "filtering": json.dumps([{"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}]),
        "limit": 300,
    }
    r2 = requests.get(f"{base}/ads", params=ads_params, timeout=20)
    r2.raise_for_status()
    creative_by_ad = {a["id"]: a.get("creative", {}).get("id") for a in r2.json().get("data", [])}

    def extract_purchases(actions: list) -> int:
        for a in (actions or []):
            if a.get("action_type") in ("purchase", "offsite_conversion.fb_pixel_purchase"):
                return int(float(a.get("value", 0)))
        return 0

    rows = []
    for row in insights:
        # El parámetro "filtering" de /insights no siempre filtra por effective_status del ad
        # (API lo ignora en algunos niveles) — se cruza a mano contra el /ads?effective_status=ACTIVE
        # de arriba, que sí es confiable, para no arrastrar ads pausados (ej. con link roto).
        if row["ad_id"] not in creative_by_ad:
            continue
        impr = int(row.get("impressions", 0))
        clicks = int(row.get("clicks", 0))
        spend = float(row.get("spend", 0))
        rows.append({
            "ad_id": row["ad_id"],
            "ad_name": row.get("ad_name"),
            "adset_id": row.get("adset_id"),
            "adset_name": row.get("adset_name"),
            "campaign_id": row.get("campaign_id"),
            "campaign_name": row.get("campaign_name"),
            "creative_id": creative_by_ad.get(row["ad_id"]),
            "impressions": impr,
            "clicks": clicks,
            "spend": spend,
            "ctr": round(clicks / impr * 100, 2) if impr else 0.0,
            "cpc": round(spend / clicks, 2) if clicks else None,
            "purchases": extract_purchases(row.get("actions", [])),
        })
    return rows


def analyze_creative_coverage(ads: list[dict]) -> list[dict]:
    """Reglas puramente matemáticas (percentiles/comparación directa, sin LLM) sobre
    el output de get_ad_level_creative_data(). Devuelve hallazgos tipo alerta,
    listos para meterse a `autonomy['alertas']` y al reporte."""
    hallazgos = []
    if not ads:
        return hallazgos

    con_muestra = [a for a in ads if a["impressions"] >= CREATIVE_MIN_IMPRESIONES and a["cpc"]]
    if con_muestra:
        cpcs = sorted(a["cpc"] for a in con_muestra)
        mediana_cpc = cpcs[len(cpcs) // 2]
    else:
        mediana_cpc = None

    # 1) Creativo fuerte (CPC ≤ 85% de la mediana) ausente en un adset ACTIVO de la MISMA campaña
    #    donde sí corren otros creativos más débiles — oportunidad de "darle carne" con datos, no intuición.
    if mediana_cpc:
        fuertes = [a for a in con_muestra if a["cpc"] <= mediana_cpc * 0.85]
        por_campaign = {}
        for a in ads:
            por_campaign.setdefault(a["campaign_id"], {}).setdefault(a["adset_id"], set()).add(a["creative_id"])
        for f in fuertes:
            adsets_misma_campaign = por_campaign.get(f["campaign_id"], {})
            for adset_id, creatives in adsets_misma_campaign.items():
                if adset_id != f["adset_id"] and f["creative_id"] not in creatives:
                    hallazgos.append({
                        "nivel": "🟡",
                        "tipo": "CREATIVO_FUERTE_AUSENTE",
                        "mensaje": (
                            f"'{f['ad_name']}' (CTR {f['ctr']}%, CPC ${f['cpc']}) es de los mejores de la cuenta "
                            f"pero no corre en el adset '{adset_id}' de la misma campaña '{f['campaign_name']}'."
                        ),
                        "accion": "Proponer a Dirección agregar este creativo (mismo creative_id) a ese adset.",
                    })

    # 2) Anomalía: CPC muy por encima de la mediana (candidato a pausar/optimizar)
    if mediana_cpc:
        for a in con_muestra:
            if a["cpc"] >= mediana_cpc * 1.5:
                hallazgos.append({
                    "nivel": "🟡",
                    "tipo": "CREATIVO_CPC_ALTO",
                    "mensaje": (
                        f"'{a['ad_name']}' en '{a['adset_name']}': CPC ${a['cpc']} vs mediana de cuenta ${mediana_cpc} "
                        f"({a['impressions']} impresiones, muestra suficiente)."
                    ),
                    "accion": "Proponer a Dirección pausar o reemplazar este creativo en este adset.",
                })

    # 3) Mismo creative_id activo en 2+ CAMPAÑAS distintas (compite contra sí mismo cruzando presupuestos)
    creative_campaigns: dict[str, set] = {}
    creative_names: dict[str, set] = {}
    for a in ads:
        if not a["creative_id"]:
            continue
        creative_campaigns.setdefault(a["creative_id"], set()).add(a["campaign_id"])
        creative_names.setdefault(a["creative_id"], set()).add(f"{a['campaign_name']}/{a['ad_name']}")
    for cid, camps in creative_campaigns.items():
        if len(camps) > 1:
            hallazgos.append({
                "nivel": "🟡",
                "tipo": "CREATIVO_DUPLICADO_CROSS_CAMPAIGN",
                "mensaje": (
                    f"El mismo creativo corre activo en {len(camps)} campañas distintas: "
                    f"{', '.join(sorted(creative_names[cid]))}."
                ),
                "accion": "Verificar overlap real de audiencia en Ads Manager antes de decidir si consolidar.",
            })

    return hallazgos


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


def _gads_customer_id() -> str:
    return (GADS_CUSTOMER_ID or "").replace("-", "")


def _gads_headers(token: str) -> dict:
    h = {
        "Authorization": f"Bearer {token}",
        "developer-token": GADS_DEV_TOKEN,
        "Content-Type": "application/json",
    }
    if GADS_LOGIN_CUSTOMER_ID:
        h["login-customer-id"] = str(GADS_LOGIN_CUSTOMER_ID).replace("-", "")
    return h


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

    headers = _gads_headers(token)
    url = f"https://googleads.googleapis.com/v22/customers/{customer_id}/googleAds:search"
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


def cargar_google_cable() -> dict:
    if GOOGLE_CABLE_FILE.exists():
        return yaml.safe_load(GOOGLE_CABLE_FILE.read_text(encoding="utf-8")) or {}
    return {}


def cargar_google_state() -> dict:
    if GOOGLE_CABLE_STATE.exists():
        try:
            return json.loads(GOOGLE_CABLE_STATE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def guardar_google_state(state: dict) -> None:
    GOOGLE_CABLE_STATE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _gads_gaql(query: str) -> dict:
    token = get_gads_token()
    if not token or not GADS_DEV_TOKEN:
        return {"error": "no oauth/token"}
    cid = _gads_customer_id()
    url = f"https://googleads.googleapis.com/v22/customers/{cid}/googleAds:search"
    r = requests.post(url, headers=_gads_headers(token), json={"query": query}, timeout=20)
    if not r.ok:
        return {"error": r.text[:400]}
    return r.json()


def _gads_mutate(resource: str, body: dict) -> dict:
    token = get_gads_token()
    if not token or not GADS_DEV_TOKEN:
        return {"error": "no oauth/token"}
    cid = _gads_customer_id()
    url = f"https://googleads.googleapis.com/v22/customers/{cid}/{resource}:mutate"
    r = requests.post(url, headers=_gads_headers(token), json=body, timeout=30)
    if not r.ok:
        return {"error": r.text[:600]}
    return r.json()


def _parse_cdmx(ts: str | None) -> datetime.datetime | None:
    if not ts:
        return None
    try:
        from zoneinfo import ZoneInfo
        dt = datetime.datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("America/Mexico_City"))
        return dt
    except Exception:
        return None


def _now_cdmx() -> datetime.datetime:
    from zoneinfo import ZoneInfo
    return datetime.datetime.now(ZoneInfo("America/Mexico_City"))


def _search_watch_metrics() -> dict:
    """CPA + impression share de EG_S2_SEARCH, últimos 7 días (incluye hoy)."""
    cable = cargar_google_cable()
    name = ((cable.get("search") or {}).get("campaign_name") or "EG_S2_SEARCH")
    end = datetime.date.today()
    start = end - datetime.timedelta(days=7)
    res = _gads_gaql(f"""
        SELECT campaign.name, campaign.status, campaign_budget.amount_micros,
               metrics.cost_micros, metrics.clicks, metrics.impressions, metrics.conversions,
               metrics.search_impression_share, metrics.search_budget_lost_impression_share,
               metrics.search_rank_lost_impression_share
        FROM campaign
        WHERE campaign.name = '{name}'
          AND segments.date BETWEEN '{start}' AND '{end}'
    """)
    if res.get("error"):
        return {"status": "error", "error": res["error"]}
    spend = clicks = impr = conv = 0.0
    lost_b = ishare = None
    camp_status = None
    budget_mxn = None
    for row in res.get("results") or []:
        m = row.get("metrics") or {}
        spend += int(m.get("costMicros") or 0) / 1e6
        clicks += int(m.get("clicks") or 0)
        impr += int(m.get("impressions") or 0)
        conv += float(m.get("conversions") or 0)
        camp_status = (row.get("campaign") or {}).get("status") or camp_status
        b = (row.get("campaignBudget") or {}).get("amountMicros")
        if b is not None:
            budget_mxn = int(b) / 1e6
        if m.get("searchImpressionShare") is not None:
            ishare = float(m["searchImpressionShare"])
        if m.get("searchBudgetLostImpressionShare") is not None:
            lost_b = float(m["searchBudgetLostImpressionShare"])
    cpa = round(spend / conv, 2) if conv else None
    return {
        "status": "ok",
        "campaign_status": camp_status,
        "daily_budget_mxn": budget_mxn,
        "spend_7d": round(spend, 2),
        "clicks_7d": int(clicks),
        "impr_7d": int(impr),
        "conv_7d": round(conv, 2),
        "cpa_search": cpa,
        "impression_share": ishare,
        "lost_is_budget": lost_b,
    }


def maybe_scale_google_search(autonomy: dict) -> dict:
    """Tras 48h del último cambio: +15% Search o mantener. Mutación real."""
    cable = cargar_google_cable()
    spec = cable.get("search") or {}
    if not spec.get("watch"):
        return {"action": "skip", "reason": "watch off"}
    reglas = spec.get("reglas") or {}
    state = cargar_google_state()
    st = dict(state.get("search") or {})
    last_at = _parse_cdmx(st.get("last_change_at"))
    now = _now_cdmx()
    if last_at is None:
        return {"action": "skip", "reason": "sin last_change_at"}
    horas = (now - last_at).total_seconds() / 3600
    metrics = _search_watch_metrics()
    if metrics.get("status") != "ok":
        return {"action": "error", "reason": metrics.get("error")}
    budget_vivo = metrics.get("daily_budget_mxn")
    if budget_vivo is not None and st.get("daily_budget_mxn") and abs(budget_vivo - float(st["daily_budget_mxn"])) >= 1:
        st.update({
            "daily_budget_mxn": int(budget_vivo),
            "last_change_at": now.isoformat(timespec="seconds"),
            "last_change_from_mxn": st.get("daily_budget_mxn"),
            "last_change_to_mxn": int(budget_vivo),
            "last_change_by": "Os_UI",
            "last_action": "detectado_cambio_ui",
            "last_action_reason": f"Budget vivo ${budget_vivo:.0f} ≠ estado ${st.get('daily_budget_mxn')}. Reinicia ventana 48h.",
            "last_review_at": now.isoformat(timespec="seconds"),
        })
        state["search"] = st
        guardar_google_state(state)
        return {"action": "hold_reset_ventana", "reason": st["last_action_reason"], "metrics": metrics}

    st["last_review_at"] = now.isoformat(timespec="seconds")
    if horas < ESCALADO_GADS_HORAS_MIN:
        st["last_action"] = "esperando_ventana"
        st["last_action_reason"] = f"{horas:.1f}h de {ESCALADO_GADS_HORAS_MIN}h desde último cambio Search."
        state["search"] = st
        guardar_google_state(state)
        return {"action": "esperando", "horas": round(horas, 1), "faltan_h": round(ESCALADO_GADS_HORAS_MIN - horas, 1), "metrics": metrics}

    banda = autonomy.get("decision_band")
    no_escalar = set(reglas.get("no_escalar_si_banda") or ["APRETAR", "PAUSAR_SET", "SIN_DATO"])
    cpa_max = float(reglas.get("cpa_search_escalar_max") or 250)
    lost_min = float(reglas.get("lost_is_budget_min") or 0.15)
    cpa_s = metrics.get("cpa_search")
    lost_b = metrics.get("lost_is_budget")
    ok_cpa = cpa_s is not None and cpa_s <= cpa_max
    ok_is = lost_b is not None and lost_b >= lost_min
    ok_banda = banda in (reglas.get("bandas_cuenta_ok") or ["ESCALAR", "MANTENER"])
    ok_serving = (metrics.get("campaign_status") or "") == "ENABLED"

    if not (ok_serving and ok_cpa and ok_is and ok_banda and banda not in no_escalar):
        why = []
        if not ok_serving:
            why.append(f"status={metrics.get('campaign_status')}")
        if not ok_cpa:
            why.append(f"CPA Search {cpa_s} (techo ${cpa_max:.0f})")
        if not ok_is:
            why.append(f"lost IS budget {lost_b} (mín {lost_min:.0%})")
        if not ok_banda or banda in no_escalar:
            why.append(f"banda cuenta {banda}")
        st["last_action"] = "mantener"
        st["last_action_reason"] = "; ".join(why) or "sin señal para subir"
        state["search"] = st
        guardar_google_state(state)
        return {"action": "mantener", "reason": st["last_action_reason"], "metrics": metrics}

    actual = int(budget_vivo or st.get("daily_budget_mxn") or 77)
    nuevo = max(actual + 1, int(round(actual * (1 + ESCALADO_GADS_PCT / 100))))
    budget_rn = spec.get("budget_resource") or f"customers/{_gads_customer_id()}/campaignBudgets/{spec.get('budget_id')}"
    mut = _gads_mutate("campaignBudgets", {
        "operations": [{
            "updateMask": "amount_micros",
            "update": {"resourceName": budget_rn, "amountMicros": str(nuevo * 1_000_000)},
        }]
    })
    if mut.get("error"):
        st["last_action"] = "error_mutate"
        st["last_action_reason"] = mut["error"][:200]
        state["search"] = st
        guardar_google_state(state)
        return {"action": "error", "reason": mut["error"], "metrics": metrics}

    st.update({
        "daily_budget_mxn": nuevo,
        "last_change_at": now.isoformat(timespec="seconds"),
        "last_change_from_mxn": actual,
        "last_change_to_mxn": nuevo,
        "last_change_by": "Ag-03",
        "last_action": "escalado",
        "last_action_reason": (
            f"+{ESCALADO_GADS_PCT}% ${actual}→${nuevo}. CPA Search ${cpa_s} · "
            f"lost IS budget {lost_b:.0%} · banda {banda}."
        ),
    })
    state["search"] = st
    guardar_google_state(state)
    _bitacora("Search +15% autónomo", st["last_action_reason"], outcome="ok")
    return {"action": "escalado", "from": actual, "to": nuevo, "reason": st["last_action_reason"], "metrics": metrics}


def maybe_watch_demandgen() -> dict:
    """Si Demand Gen lleva 48h ON con 0 compras y gasto, la pausa (mismo motivo que Dirección)."""
    cable = cargar_google_cable()
    spec = cable.get("demandgen") or {}
    if not spec.get("watch"):
        return {"action": "skip", "reason": "watch off"}
    reglas = spec.get("reglas") or {}
    state = cargar_google_state()
    st = dict(state.get("demandgen") or {})
    last_on = _parse_cdmx(st.get("last_enabled_at"))
    now = _now_cdmx()
    st["last_review_at"] = now.isoformat(timespec="seconds")
    if last_on is None or (st.get("status") or "").upper() != "ENABLED":
        state["demandgen"] = st
        guardar_google_state(state)
        return {"action": "skip", "reason": "Demand Gen no está en watch-enabled"}
    horas = (now - last_on).total_seconds() / 3600
    horas_min = float(reglas.get("horas_sin_conv_pausar") or 48)
    if horas < horas_min:
        st["last_action"] = "esperando_ventana"
        st["last_action_reason"] = f"{horas:.1f}h de {horas_min:.0f}h desde encendido Demand Gen."
        state["demandgen"] = st
        guardar_google_state(state)
        return {"action": "esperando", "horas": round(horas, 1), "faltan_h": round(horas_min - horas, 1)}

    cid = spec.get("campaign_id")
    since = last_on.date().isoformat()
    until = datetime.date.today().isoformat()
    res = _gads_gaql(f"""
        SELECT campaign.id, campaign.status, metrics.cost_micros, metrics.conversions
        FROM campaign
        WHERE campaign.id = {cid}
          AND segments.date BETWEEN '{since}' AND '{until}'
    """)
    if res.get("error"):
        return {"action": "error", "reason": res["error"]}
    spend = conv = 0.0
    camp_status = None
    for row in res.get("results") or []:
        m = row.get("metrics") or {}
        spend += int(m.get("costMicros") or 0) / 1e6
        conv += float(m.get("conversions") or 0)
        camp_status = (row.get("campaign") or {}).get("status") or camp_status
    spend_min = float(reglas.get("spend_min_para_pausar") or 80)
    conv_max = float(reglas.get("conversiones_max_para_pausar") or 0)
    if camp_status != "ENABLED":
        st["status"] = camp_status
        st["last_action"] = "ya_pausada"
        state["demandgen"] = st
        guardar_google_state(state)
        return {"action": "ya_pausada", "status": camp_status}

    if conv > conv_max:
        st["last_action"] = "mantener_on"
        st["last_action_reason"] = f"Demand Gen {conv:.1f} conv / ${spend:.0f} desde encendido. Sigue."
        state["demandgen"] = st
        guardar_google_state(state)
        return {"action": "mantener_on", "conv": conv, "spend": round(spend, 2)}

    if spend < spend_min:
        st["last_action"] = "mantener_on"
        st["last_action_reason"] = f"0 conv pero solo ${spend:.0f} (mín ${spend_min:.0f} para pausar)."
        state["demandgen"] = st
        guardar_google_state(state)
        return {"action": "mantener_on_poco_gasto", "spend": round(spend, 2)}

    camp_rn = f"customers/{_gads_customer_id()}/campaigns/{cid}"
    mut = _gads_mutate("campaigns", {
        "operations": [{
            "updateMask": "status",
            "update": {"resourceName": camp_rn, "status": "PAUSED"},
        }]
    })
    if mut.get("error"):
        st["last_action"] = "error_pause"
        st["last_action_reason"] = mut["error"][:200]
        state["demandgen"] = st
        guardar_google_state(state)
        return {"action": "error", "reason": mut["error"]}
    st.update({
        "status": "PAUSED",
        "last_action": "pausada_cero_conv",
        "last_action_reason": f"0 conv / ${spend:.0f} en {horas:.0f}h. Mismo patrón que 13 ago.",
    })
    state["demandgen"] = st
    guardar_google_state(state)
    _bitacora("Demand Gen pausada 0 conv", st["last_action_reason"], outcome="ok")
    return {"action": "pausada", "spend": round(spend, 2), "horas": round(horas, 1)}


def maybe_operate_google(autonomy: dict) -> list[dict]:
    out = []
    try:
        out.append(maybe_scale_google_search(autonomy))
    except Exception as e:
        out.append({"action": "error", "where": "search", "reason": str(e)[:200]})
    try:
        out.append(maybe_watch_demandgen())
    except Exception as e:
        out.append({"action": "error", "where": "demandgen", "reason": str(e)[:200]})
    return out


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
        cortesias   = cortesias_conocidas(fecha_str[:10])
        vendidos_pagados = max(0, vendidos - cortesias)
        disponibles = int(disp.get("disponibles", fn.get("disponibles", AFORO_VENDIBLE)))
        total_fn    = int(disp.get("total", AFORO_VENDIBLE))
        ocupacion   = round(vendidos / total_fn * 100, 1) if total_fn else 0
        precio_prom = _config["precios"]["general"]  # base; mejorar cuando /api/reporte esté disponible
        ingresos_est = vendidos_pagados * precio_prom  # CPA/ingresos SOLO cuentan boletos pagados, no cortesías

        fn_data = {
            "fecha": fecha_str[:10],
            "nombre": fn.get("nombre", f"Función {fecha_str[:10]}"),
            "dias_para_funcion": delta,
            "vendidos": vendidos,
            "cortesias": cortesias,
            "vendidos_pagados": vendidos_pagados,
            "disponibles": disponibles,
            "total_aforo": total_fn,
            "ocupacion_pct": ocupacion,
            "ingresos_estimados": ingresos_est,
        }
        funciones_detail.append(fn_data)

        # Acumular ventas de los últimos 7 días (solo pagadas — el CPA no puede "comprar" cortesías)
        if -7 <= delta <= 0:
            total_vendidos += vendidos_pagados
            total_ingresos += ingresos_est

    # Ventas del período = delta vs snapshot. Las funciones aún no ocurren, así que
    # "vendidos" por función es acumulado — sin baseline el delta semanal es incalculable
    # (por eso el viejo cálculo por fecha de función daba siempre 0 antes del estreno).
    # Usamos vendidos_pagados (no vendidos crudo) para que una cortesía nueva no aparente ser una venta.
    vendidos_actual = {f["fecha"]: f["vendidos_pagados"] for f in funciones_detail}
    result["vendidos_por_funcion_actual"] = vendidos_actual
    snapshot = load_snapshot()
    if snapshot:
        base = snapshot.get("vendidos_por_funcion", {})
        delta = sum(max(0, v - int(base.get(fecha, 0))) for fecha, v in vendidos_actual.items())
        ventas_semana = {
            "boletos": delta,
            "ingresos_estimados": delta * _config["precios"]["general"],
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

    # Stripe manda sobre KV para "ventas de esta semana": el contador de la boletera mezcla
    # cortesías/altas manuales con ventas pagadas; Stripe trae precio real por transacción
    # (metadata.cantidad + amount_total) y permite aplicar la regla de Dirección (19 jul):
    # cualquier boleto pagado por debajo de $245/unidad es cortesía/prueba, no venta.
    stripe_reales = ventas_reales_stripe(dias=7)
    if stripe_reales:
        ventas_semana = {
            "boletos": stripe_reales["boletos_reales"],
            "ingresos_estimados": stripe_reales["ingresos_reales"],
            "metodo": "stripe_precio_real",
            "cortesias_detectadas_stripe": stripe_reales["boletos_cortesia_stripe"],
        }
        if stripe_reales["boletos_cortesia_stripe"]:
            result["alerta_cortesias_stripe"] = (
                f"{stripe_reales['boletos_cortesia_stripe']} boletos pagados en Stripe en los últimos "
                f"{stripe_reales['dias']} días están por debajo de ${UMBRAL_VENTA_REAL_MXN} MXN — "
                "excluidos de ventas/CPA por regla de Dirección (19 jul)."
            )

    result["funciones"] = funciones_detail
    result["ventas_semana"] = ventas_semana
    result["ventas_reales_stripe"] = stripe_reales
    result["proxima_funcion"] = proxima
    result["funcion_mas_debil"] = mas_debil
    result["status"] = "ok"
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 4. REGLAS DE AUTONOMÍA (reglas-de-decision.md)
# ═══════════════════════════════════════════════════════════════════════════════

def apply_autonomy_rules(meta: dict, gads: dict, boletera: dict, historial_cpa: list[float] | None = None) -> dict:
    """
    Fórmula maestra: 00-EQUILIBRIO-CON-PAUTA.md + reglas-de-decision.md.

    Techo de negocio = CPA boletera vs margen ($346). No hay tope duro de $/día:
    arranque fuerte ($960+) está OK mientras CPA_real ≤ margen; se escala si &lt; $250.

    Niveles: 🟢 NORMAL (autónomo si banda OK) · 🟡 PROPONE (muestra/edge) · 🔴 URGENTE · ❌ nunca solo: copy/campaña nueva
    """
    alertas = []
    nivel = "🟢"

    spend_total = meta.get("spend", 0) + gads.get("spend", 0)
    ventas_boletera = boletera.get("ventas_semana", {}).get("boletos", 0)
    cpa_real = round(spend_total / ventas_boletera, 2) if ventas_boletera > 0 else None
    proxima = boletera.get("proxima_funcion")
    high_freq_adsets = meta.get("adsets_high_frequency", [])

    # Utilidad de contribución del período (margen − ads). Fijos de función se miran aparte.
    util_contrib = round(ventas_boletera * MARGEN_BOLETO - spend_total, 2) if ventas_boletera or spend_total else None
    # BE real si TODO el spend del período se cargara a UNA función (cota pesimista).
    be_real_una_funcion = round((FIJO_POR_FUNCION + spend_total) / MARGEN_BOLETO, 1)
    be_teatro = BE_TEATRO_BOLETOS

    puntos = [v for v in (historial_cpa or []) if v is not None][-(VENTANA_TENDENCIA_DIAS - 1):]
    if cpa_real is not None:
        puntos = puntos + [cpa_real]
    cpa_tendencia = round(sum(puntos) / len(puntos), 2) if puntos else None
    muestra_suficiente = ventas_boletera >= MIN_MUESTRA_CONVERSIONES

    # Banda de decisión (vara = tendencia si hay muestra; si no, dato actual solo informativo)
    cpa_para_banda = cpa_tendencia if (muestra_suficiente and cpa_tendencia is not None) else cpa_real
    if cpa_para_banda is None:
        decision_band = "SIN_DATO"
    elif cpa_para_banda < CPA_ESCALA:
        decision_band = "ESCALAR"       # ver escalado.yaml (típ. +15% set ganador)
    elif cpa_para_banda <= CPA_MAX_ACEPTABLE:
        decision_band = "MANTENER"      # rentable / tablas
    elif cpa_para_banda <= CPA_CIRCUIT_BREAKER:
        decision_band = "APRETAR"       # aún no pausar; revisar sets
    else:
        decision_band = "PAUSAR_SET"    # >$400

    # ─── CIRCUIT BREAKERS (🔴) ───────────────────────────────────────────────

    if spend_total > (CPA_MAX_ACEPTABLE * 2) and ventas_boletera == 0:
        alertas.append({
            "nivel": "🔴",
            "tipo": "GASTO_SIN_VENTAS",
            "mensaje": f"Se gastaron ${spend_total:.0f} MXN sin ventas pagadas en boletera.",
            "accion": "Verificar pixel Purchase + boletera ANTES de seguir quemando. Arranque fuerte no justifica $0 ventas.",
        })
        nivel = "🔴"

    if boletera.get("status") == "error":
        alertas.append({
            "nivel": "🔴",
            "tipo": "BOLETERA_CAIDA",
            "mensaje": f"No se pudo conectar a la boletera: {boletera.get('error', 'sin detalle')}",
            "accion": f"Verificar {BOLETERA_URL}. Avisar Ag-13. Sin boletera no hay CPA_real → no escalar a ciegas.",
        })
        nivel = "🔴"

    if muestra_suficiente and cpa_tendencia and cpa_tendencia > CPA_CIRCUIT_BREAKER:
        alertas.append({
            "nivel": "🔴",
            "tipo": "CPA_CRITICO",
            "mensaje": (
                f"CPA_real tendencia ${cpa_tendencia:.0f} > circuit ${CPA_CIRCUIT_BREAKER:.0f} "
                f"(actual ${cpa_real:.0f}). Util contrib período: ${util_contrib:.0f}. "
                f"BE real si ads→1 función: ~{be_real_una_funcion:.0f} boletos (teatro solo={be_teatro})."
            ),
            "accion": "Proponer a Dirección PAUSAR el set perdedor. No pausar la cuenta entera. Techo=CPA, no el daily.",
        })
        nivel = "🔴"
    elif cpa_real and cpa_real > CPA_CIRCUIT_BREAKER and not muestra_suficiente:
        alertas.append({
            "nivel": "🟢",
            "tipo": "MUESTRA_INSUFICIENTE",
            "mensaje": (
                f"CPA instantáneo ${cpa_real:.0f} parece alto pero solo {ventas_boletera} venta(s) "
                f"(mín. {MIN_MUESTRA_CONVERSIONES}). Arranque fuerte: seguir midiendo."
            ),
            "accion": "No pausar aún. Re-evaluar con muestra.",
        })

    # ─── PROPONE (🟡) — escala / aprieta / ocupación ─────────────────────────

    if muestra_suficiente and cpa_tendencia is not None and cpa_tendencia < CPA_ESCALA and nivel != "🔴":
        alertas.append({
            "nivel": "🟡",
            "tipo": "ESCALAR_MAS",
            "mensaje": (
                f"CPA_real tendencia ${cpa_tendencia:.0f} < umbral escala ${CPA_ESCALA:.0f}. "
                f"Util contrib ${util_contrib:.0f}. Gasto período ${spend_total:.0f} — "
                f"NO hay tope diario mientras esto se sostenga."
            ),
            "accion": (
                f"Autónomo si ventana+muestra OK: {texto_escalado_presupuesto()} al set ganador IC "
                f"(funnel-cable.yaml → {cargar_funnel_cable().get('reglas_movimiento', {}).get('set_ganador_ic', 'SOCIAL90')}; "
                f"no TOFU/AFIN para volumen — sin 'va' si reglas cumplidas)."
            ),
        })
        if nivel == "🟢":
            nivel = "🟡"

    if (
        muestra_suficiente and cpa_tendencia
        and CPA_MAX_ACEPTABLE < cpa_tendencia <= CPA_CIRCUIT_BREAKER
        and nivel != "🔴"
    ):
        alertas.append({
            "nivel": "🟡",
            "tipo": "CPA_ALTO",
            "mensaje": (
                f"CPA_real tendencia ${cpa_tendencia:.0f} entre tablas (${CPA_MAX_ACEPTABLE:.0f}) "
                f"y pausa (${CPA_CIRCUIT_BREAKER:.0f}). Util contrib ${util_contrib:.0f}."
            ),
            "accion": "Mantener o bajar el set flojo. No subir daily hasta volver ≤$346.",
        })
        nivel = "🟡"

    # Soft burn: informar si el ritmo diario implícito > soft, SOLO si CPA no sano
    dias_periodo = max(1, int(meta.get("days") or gads.get("days") or 7))
    burn_diario = round(spend_total / dias_periodo, 0)
    if burn_diario > BUDGET_DIARIO_SOFT and cpa_real and cpa_real > CPA_MAX_ACEPTABLE and nivel != "🔴":
        alertas.append({
            "nivel": "🟡",
            "tipo": "BURN_ALTO_Y_CPA_FLOJO",
            "mensaje": (
                f"Ritmo ~${burn_diario:.0f}/día (> soft ${BUDGET_DIARIO_SOFT:.0f}) Y CPA_real "
                f"${cpa_real:.0f} > margen ${MARGEN_BOLETO:.0f}."
            ),
            "accion": "Aquí sí apretar: el gasto alto solo vale si CPA ≤ margen. Revisar sets.",
        })
        if nivel == "🟢":
            nivel = "🟡"

    for adset in high_freq_adsets:
        alertas.append({
            "nivel": "🟡",
            "tipo": "SOLICITUD_CREATIVO",
            "mensaje": f"Adset '{adset['adset']}' frecuencia {adset['frecuencia']:.1f} (límite {FRECUENCIA_MAX}).",
            "accion": "Pedir a Dirección/Ag-08 pieza nueva o rotación (00c-MANIOBRA). No tocar targeting en aprendizaje.",
        })
        if nivel == "🟢":
            nivel = "🟡"

    if proxima:
        ocp = proxima["ocupacion_pct"]
        dias = proxima["dias_para_funcion"]
        vendidos_prox = proxima.get("vendidos_pagados", proxima.get("vendidos"))
        hueco_be_teatro = max(0, be_teatro - int(vendidos_prox or 0)) if vendidos_prox is not None else None
        if ocp < 50 and dias <= 5:
            alertas.append({
                "nivel": "🟡",
                "tipo": "OCUPACION_BAJA",
                "mensaje": (
                    f"Función {proxima['fecha']}: {ocp}% a {dias}d. "
                    f"BE teatro≈{be_teatro} boletos"
                    + (f" (faltan ~{hueco_be_teatro} pagados)" if hueco_be_teatro is not None else "")
                    + f". BE real con ads de esta semana→1 función≈{be_real_una_funcion:.0f}."
                ),
                "accion": "Subir pauta solo si CPA_real del período aguanta ≤ margen. Dirección decide monto.",
            })
            if nivel == "🟢":
                nivel = "🟡"
        elif ocp < 60 and dias <= 10:
            alertas.append({
                "nivel": "🟡",
                "tipo": "OCUPACION_MEDIA",
                "mensaje": f"Función {proxima['fecha']}: {ocp}% a {dias}d.",
                "accion": "Monitorear. Meta = banda óptima (utilidad), no solo BE teatro.",
            })
            if nivel == "🟢":
                nivel = "🟡"

    if not alertas:
        msg_util = f" Util contrib ${util_contrib:.0f}." if util_contrib is not None else ""
        alertas.append({
            "nivel": "🟢",
            "tipo": "NORMAL",
            "mensaje": f"Dentro de parámetros. Banda={decision_band}.{msg_util}",
            "accion": (
                f"Continuar. Si banda ESCALAR y muestra OK → escala autónoma {texto_escalado_presupuesto()} al ganador."
                if decision_band == "ESCALAR"
                else "Continuar — presupuesto dinámico según modelo + respuesta público."
            ),
        })

    return {
        "nivel_general": nivel,
        "cpa_real": cpa_real,
        "cpa_tendencia": cpa_tendencia,
        "cpa_escala": CPA_ESCALA,
        "cpa_tablas": CPA_MAX_ACEPTABLE,
        "muestra_suficiente": muestra_suficiente,
        "spend_total": spend_total,
        "burn_diario_implicito": burn_diario,
        "ventas_boletera_semana": ventas_boletera,
        "margen_boleto": MARGEN_BOLETO,
        "util_contrib": util_contrib,
        "be_teatro_boletos": be_teatro,
        "be_real_una_funcion": be_real_una_funcion,
        "decision_band": decision_band,
        "escalado_incremento_pct": ESCALADO_INCREMENTO_PCT,
        "escalado_fuente": ESCALADO_FUENTE,
        "alertas": alertas,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ANÁLISIS GEMINI
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = f"""
Eres el Media Buyer IA de Platea, agencia de marketing teatral.
Tu cliente: {_config["obra"]["nombre"]} — {_config["obra"]["subtitulo"]}, CDMX 2026.

OBSESIÓN (equilibrio real, 00-EQUILIBRIO-CON-PAUTA.md):
- CPA_real = gasto ads ÷ boletos PAGADOS boletera (nunca solo pixel Meta).
- Tablas exactas: CPA_real ≤ ${CPA_MAX_ACEPTABLE:.0f} (= margen boleto).
- Escalar {texto_escalado_presupuesto()} set ganador si CPA_real &lt; ${CPA_ESCALA:.0f} sostenido.
- Pausar set si CPA_real &gt; ${CPA_CIRCUIT_BREAKER:.0f} × 3d.
- NO hay tope duro de $/día: arranque fuerte ($960+) es correcto mientras CPA ≤ margen.
- Maximizar utilidad (banda ~41–103 boletos/función), no solo “empatar 41 sin ads”.

Eres numérico, citas fuente. Respondes en español, JSON válido, sin texto extra.
NUNCA pausas campañas ni cambias presupuesto sin aprobación de Dirección (propones), salvo
escalado.yaml autonomía ya cumplida — y entonces el set ganador es el de funnel-cable.yaml
(nunca TOFU ni AFIN “para dar pool”; closer = BOFU_PURCHASE).
Lee CABLE FUNNEL VIVO y CABLE GOOGLE SEARCH: números solo de snapshot/state, no inventes.
Google Search: Ag-03 +15% o mantiene a las 48h (google-cable.yaml). No pedirle a Dirección que suba Search.
TOFU captador: máx −15% ABO. BOFU: no tocar hasta la fecha del cable.
Si falta creativo/test/tracking/va/geo, emite SOLICITUD_* según campanas/00c-MANIOBRA-AG03.md (no inventes el fix).
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
    """Análisis ejecutivo con Gemini Vertex AI (vía AI Gateway si está configurado)."""
    client = make_client(project=GCP_PROJECT, location=GCP_LOCATION)

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
${autonomy.get('cpa_real', 'N/D')} MXN (objetivo ≤${CPA_MAX_ACEPTABLE:.0f}, referencia S1 ${CPA_REFERENCIA:.0f})

ALERTAS ACTIVAS:
{json.dumps(autonomy.get('alertas', []), ensure_ascii=False, indent=2)}

{texto_funnel_cable()}

{texto_google_cable()}

REGLAS CRÍTICAS:
- Números de funnel solo del snapshot (API). Si un set no tiene spend_7d, no lo inventes.
- No TOFU/AFIN para volumen. TOFU recorte máx 15% ABO; no pausar los 3 sets.
- No pausar MOFU VC. closer = BOFU_PURCHASE — no tocar hasta bofu_no_tocar_hasta. HOT PAUSED. SOCIAL90 no reencender.
- Search: no pedir a Dirección que suba; Ag-03 lo hace a las 48h si CPA≤250 y lost IS budget≥15%.
- Nunca recomendar pausar campañas o cambiar presupuesto sin OK de Dirección, salvo autonomía ya cumplida.
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

    # Semáforo CPA (vara = margen / escala)
    if cpa_real is None:
        semaforo_cpa = "⚪ Sin datos"
    elif cpa_real < CPA_ESCALA:
        semaforo_cpa = f"🟢 ${cpa_real:.0f} ESCALAR (≤${CPA_ESCALA:.0f})"
    elif cpa_real <= CPA_MAX_ACEPTABLE:
        semaforo_cpa = f"🟢 ${cpa_real:.0f} TABLAS/OK (≤${CPA_MAX_ACEPTABLE:.0f})"
    elif cpa_real <= CPA_CIRCUIT_BREAKER:
        semaforo_cpa = f"🟡 ${cpa_real:.0f} APRETAR (pausar &gt;${CPA_CIRCUIT_BREAKER:.0f})"
    else:
        semaforo_cpa = f"🔴 ${cpa_real:.0f} PAUSAR SET"

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
║          {_config["obra"]["nombre"]} · {_config["temporada"]["venue"]["nombre"]:<20}║
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
CPA REAL:           ${cpa_real or 'N/D'} MXN (gasto ÷ boletos pagados boletera)
Banda decisión:     {autonomy.get('decision_band', 'N/D')}  (escala < ${CPA_ESCALA:.0f} · tablas ≤ ${CPA_MAX_ACEPTABLE:.0f} · pausa > ${CPA_CIRCUIT_BREAKER:.0f})
Util contrib:       ${autonomy.get('util_contrib') if autonomy.get('util_contrib') is not None else 'N/D'} MXN  (= boletos×${MARGEN_BOLETO:.0f} − ads)
BE teatro / BE real (ads→1 fn):  {autonomy.get('be_teatro_boletos', BE_TEATRO_BOLETOS)} / {autonomy.get('be_real_una_funcion', 'N/D')} boletos
Burn diario implícito: ${autonomy.get('burn_diario_implicito') or 'N/D'}  (soft info ${BUDGET_DIARIO_SOFT:.0f}; techo real = CPA)
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


def send_whatsapp(mensaje: str, urgente: bool = False) -> bool:
    """Envía WhatsApp a Dirección vía Meta Cloud API (mismo phone_number_id que usa WF-03 en n8n).
    Nunca deja al agente mudo: si falla (token, número sin verificar, etc.) cae a email."""
    if not WA_TOKEN or not WA_PHONE_NUMBER_ID:
        print("⚠️  WA_MESSAGING_TOKEN o phone_number_id no configurados — usando email")
        return send_email("[WA no disponible] " + mensaje[:60], mensaje, urgente=urgente)

    emoji = "🚨 " if urgente else "🔔 "
    try:
        r = requests.post(
            f"https://graph.facebook.com/v20.0/{WA_PHONE_NUMBER_ID}/messages",
            headers={
                "Authorization": f"Bearer {WA_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "to": WA_DESTINO_OS,
                "type": "text",
                "text": {"body": f"{emoji}{mensaje}"},
            },
            timeout=15,
        )
        if r.ok:
            print(f"✅ WhatsApp enviado a {WA_DESTINO_OS}")
            return True
        print(f"❌ Error enviando WhatsApp: {r.status_code} {r.text[:150]} — cae a email")
    except Exception as e:
        print(f"❌ Excepción enviando WhatsApp: {e} — cae a email")

    return send_email("[WA falló] " + mensaje[:60], mensaje, urgente=urgente)


def notificar(mensaje: str, urgente: bool = False) -> bool:
    """Canal de alerta por defecto para el check rápido: WhatsApp primero, email si falla."""
    return send_whatsapp(mensaje, urgente=urgente)


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


MODELO_DIARIO_PATH = ROOT / "config" / "modelo_diario.json"


def dias_desde_estreno() -> int:
    try:
        estreno = datetime.date.fromisoformat(_config["temporada"]["estreno"])
        return max(1, (datetime.date.today() - estreno).days)
    except Exception:
        return 30


def write_modelo_diario(meta: dict, gads: dict, boletera: dict, autonomy: dict) -> None:
    """Snapshot para cockpit / agentes — temporada + pauta Meta+Google (00-EQUILIBRIO-CON-PAUTA)."""
    meta_temp = None
    gads_temp = None
    pauta_temp = None
    try:
        estreno = datetime.date.fromisoformat(_config["temporada"]["estreno"])
        meta_temp = get_meta_performance(since=estreno)
        gads_temp = get_google_ads_performance(days=dias_desde_estreno())
        pauta_temp = meta_temp.get("spend", 0) + gads_temp.get("spend", 0)
    except Exception:
        pass

    funciones = boletera.get("funciones", [])
    def _dias_fn(f: dict) -> int:
        return f.get("dias_restantes", f.get("dias_para_funcion", 0))

    futuras = [f for f in funciones if _dias_fn(f) > 0]
    n_fut = len(futuras)
    pagados_fut = sum(f.get("vendidos_pagados", f.get("vendidos", 0)) for f in futuras)
    pagados_total = sum(f.get("vendidos_pagados", f.get("vendidos", 0)) for f in funciones)
    ingresos_est = boletera.get("ventas_semana", {}).get("ingresos_estimados", 0)
    if boletera.get("ventas_reales_stripe"):
        ingresos_est = boletera["ventas_reales_stripe"].get("ingresos_reales", ingresos_est)

    fijos_restantes = n_fut * FIJO_POR_FUNCION
    margen_acum = pagados_total * MARGEN_BOLETO
    pauta_semana = autonomy.get("spend_total", 0)
    meta_sem = meta.get("spend", 0)
    google_sem = gads.get("spend", 0)

    be_temporada_boletos = None
    faltan_temporada = None
    util_temporada = None
    pauta_por_func = 0.0
    if pauta_temp is not None:
        be_temporada_boletos = round((fijos_restantes + pauta_temp) / MARGEN_BOLETO, 0)
        faltan_temporada = max(0, int(be_temporada_boletos) - pagados_fut)
        util_temporada = round(margen_acum - fijos_restantes - pauta_temp, 0)
        pauta_por_func = pauta_temp / n_fut if n_fut else 0

    por_funcion_list = []
    for f in sorted(futuras, key=_dias_fn):
        pag = f.get("vendidos_pagados", f.get("vendidos", 0))
        be_real_fn = round((FIJO_POR_FUNCION + pauta_por_func) / MARGEN_BOLETO, 1)
        faltan_fn = max(0, int(round(be_real_fn)) - pag)
        por_funcion_list.append({
            "fecha": f.get("fecha"),
            "dias": _dias_fn(f),
            "pagados": pag,
            "be_bruto": BE_BRUTO_BOLETOS,
            "be_real_con_pauta": be_real_fn,
            "faltan": faltan_fn,
            "ocupacion_pct": f.get("ocupacion_pct"),
        })

    promedio_pagados = round(pagados_fut / n_fut, 1) if n_fut else 0
    promedio_faltan = round(sum(p["faltan"] for p in por_funcion_list) / n_fut, 1) if n_fut else 0
    be_real_prom = round((FIJO_POR_FUNCION + pauta_por_func) / MARGEN_BOLETO, 1) if n_fut else None

    snap = {
        "timestamp": datetime.datetime.now().isoformat(),
        "fuente": "00-MODELO-NEGOCIO.md + 00-EQUILIBRIO-CON-PAUTA.md",
        "margen_boleto": MARGEN_BOLETO,
        "fijo_por_funcion": FIJO_POR_FUNCION,
        "costo_por_funcion": FIJO_POR_FUNCION,
        "semana": {
            "dias": 7,
            "meta_spend": round(meta_sem, 2),
            "google_spend": round(google_sem, 2),
            "pauta_total": round(pauta_semana, 2),
            "ventas_boletera": autonomy.get("ventas_boletera_semana", 0),
            "cpa_real": autonomy.get("cpa_real"),
            "util_contrib": autonomy.get("util_contrib"),
            "decision_band": autonomy.get("decision_band"),
            "escalado_incremento_pct": autonomy.get("escalado_incremento_pct"),
        },
        "temporada": {
            "dias_desde_estreno": dias_desde_estreno(),
            "funciones_restantes": n_fut,
            "fijos_comprometidos_restantes": fijos_restantes,
            "boletos_pagados_futuros": pagados_fut,
            "boletos_pagados_total": pagados_total,
            "margen_bruto_acum_est": round(margen_acum, 0),
            "pauta_meta_acum": round(meta_temp.get("spend", 0), 2) if meta_temp else None,
            "pauta_google_acum": round(gads_temp.get("spend", 0), 2) if gads_temp else None,
            "pauta_total_acum": round(pauta_temp, 2) if pauta_temp is not None else None,
            "be_real_temporada_boletos": be_temporada_boletos,
            "faltan_boletos_temporada": faltan_temporada,
            "utilidad_productor_aprox": util_temporada,
        },
        "por_funcion": {
            "be_bruto_promedio": BE_BRUTO_BOLETOS,
            "be_real_promedio": be_real_prom,
            "promedio_pagados": promedio_pagados,
            "promedio_faltan": promedio_faltan,
            "pauta_asignada_por_funcion": round(pauta_por_func, 0),
            "funciones": por_funcion_list,
        },
    }
    MODELO_DIARIO_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODELO_DIARIO_PATH.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")


def save_check_log(
    cpa_real: float | None,
    nivel: str,
    spend_total: float,
    ventas: int,
    autonomy: dict | None = None,
) -> str:
    """Log ligero --check-now: tendencia CPA + bitácora equilibrio real (hackathon)."""
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(log_dir, f"check_{ts}.json")
    a = autonomy or {}
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.datetime.now().isoformat(),
            "cpa_real": cpa_real,
            "cpa_tendencia": a.get("cpa_tendencia"),
            "nivel": nivel,
            "decision_band": a.get("decision_band"),
            "spend_total": spend_total,
            "burn_diario_implicito": a.get("burn_diario_implicito"),
            "ventas_boletera_semana": ventas,
            "margen_boleto": a.get("margen_boleto", MARGEN_BOLETO),
            "util_contrib": a.get("util_contrib"),
            "be_teatro_boletos": a.get("be_teatro_boletos", BE_TEATRO_BOLETOS),
            "be_real_una_funcion": a.get("be_real_una_funcion"),
            "fuente": "00-EQUILIBRIO-CON-PAUTA.md",
        }, f, indent=2, ensure_ascii=False)
    return filepath


def historial_cpa_reciente(dias: int = 4) -> list[float]:
    """Lee los logs/check_*.json de los últimos `dias` días (orden cronológico, más nuevo
    al final) y devuelve la lista de cpa_real — insumo del promedio móvil de tendencia."""
    log_dir = Path(os.path.dirname(__file__)) / "logs"
    if not log_dir.exists():
        return []
    corte = datetime.datetime.now() - datetime.timedelta(days=dias)
    entradas = []
    for f in log_dir.glob("check_*.json"):
        try:
            data = json.loads(f.read_text())
            ts = datetime.datetime.fromisoformat(data["timestamp"])
            if ts >= corte:
                entradas.append((ts, data.get("cpa_real")))
        except Exception:
            continue
    entradas.sort(key=lambda x: x[0])
    return [v for _, v in entradas]


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
    historial_cpa = historial_cpa_reciente(dias=4)
    autonomy = apply_autonomy_rules(meta, gads, boletera, historial_cpa=historial_cpa)
    nivel = autonomy["nivel_general"]
    print(f"   Nivel: {nivel}")
    for a in autonomy["alertas"]:
        if a["nivel"] != "🟢":
            print(f"   {a['nivel']} {a['tipo']}: {a['mensaje'][:60]}...")

    # ── 2B. Cobertura de creativos (matemático — CTR/CPC por ad, sin Gemini) ──
    print("\n🎨 Analizando cobertura de creativos (creative gaps)...")
    try:
        ads_creative_data = get_ad_level_creative_data(days=14)
        creative_hallazgos = analyze_creative_coverage(ads_creative_data)
        if creative_hallazgos:
            autonomy["alertas"].extend(creative_hallazgos)
            if autonomy["nivel_general"] == "🟢":
                autonomy["nivel_general"] = "🟡"
            nivel = autonomy["nivel_general"]
            for h in creative_hallazgos:
                print(f"   {h['nivel']} {h['tipo']}: {h['mensaje'][:70]}...")
        else:
            print("   Sin hallazgos — cobertura de creativos OK")
    except Exception as e:
        print(f"   ❌ Error análisis de creativos: {e}")

    # ── 2C. Funnel cable (roles yaml + números API; Gemini y --check-now leen esto)
    print("\n🔌 Funnel cable snapshot (Meta last_7d)...")
    try:
        snap = refresh_funnel_cable_snapshot()
        s90 = (snap.get("sets") or {}).get("SOCIAL90") or {}
        print(
            f"   SOCIAL90 ${s90.get('daily_budget_mxn', '?')}/d · "
            f"IC_7d={s90.get('ic')} · {snap.get('pulled_at', '?')}"
        )
    except Exception as e:
        print(f"   ⚠️ funnel-cable snapshot: {e}")

    # ── 2D. Google Search 48h + Demand Gen watch (google-cable.yaml)
    print("\n🔎 Google cable (Search 48h / Demand Gen)...")
    try:
        gops = maybe_operate_google(autonomy)
        autonomy["google_ops"] = gops
        for op in gops:
            act = op.get("action")
            extra = op.get("reason") or op.get("faltan_h") or ""
            if act == "escalado":
                print(f"   ✅ Search {op.get('from')}→{op.get('to')}/d · {op.get('reason', '')[:80]}")
                autonomy["alertas"].append({
                    "nivel": "🟡",
                    "tipo": "GOOGLE_SEARCH_ESCALADO",
                    "mensaje": op.get("reason") or f"Search ${op.get('from')}→${op.get('to')}",
                    "accion": "Ventana 48h reiniciada. No tocar Search a mano.",
                })
                if autonomy["nivel_general"] == "🟢":
                    autonomy["nivel_general"] = "🟡"
            elif act == "pausada":
                print(f"   ⏸ Demand Gen pausada · ${op.get('spend')} / {op.get('horas')}h sin conv")
                autonomy["alertas"].append({
                    "nivel": "🟡",
                    "tipo": "DEMANDGEN_PAUSADA_CERO_CONV",
                    "mensaje": f"Demand Gen pausada: 0 conv / ${op.get('spend')} en {op.get('horas')}h.",
                    "accion": "No reencender sin creativo o señal nueva.",
                })
                if autonomy["nivel_general"] == "🟢":
                    autonomy["nivel_general"] = "🟡"
            elif act == "esperando":
                print(f"   ⏳ {op.get('faltan_h')}h para revisar · {act}")
            elif act in ("mantener", "mantener_on", "mantener_on_poco_gasto"):
                print(f"   → {act}: {str(extra)[:90]}")
            elif act not in ("skip",):
                print(f"   {act}: {str(extra)[:90]}")
        nivel = autonomy["nivel_general"]
    except Exception as e:
        print(f"   ⚠️ google-cable: {e}")

    # ── 3. Check-only mode ────────────────────────────────
    if check_only:
        cpa = autonomy.get("cpa_real")
        print(f"\n⚡ CHECK RÁPIDO · equilibrio real")
        print(f"   CPA_real: ${cpa or 'N/D'} (tendencia ${autonomy.get('cpa_tendencia') or 'N/D'})")
        print(f"   Banda: {autonomy.get('decision_band')} · escala&lt;${CPA_ESCALA:.0f} · tablas≤${CPA_MAX_ACEPTABLE:.0f} · pausa&gt;${CPA_CIRCUIT_BREAKER:.0f}")
        print(f"   Util contrib: ${autonomy.get('util_contrib') if autonomy.get('util_contrib') is not None else 'N/D'} · spend ${autonomy.get('spend_total', 0):.0f} · ventas {autonomy.get('ventas_boletera_semana')}")
        print(f"   BE teatro/real(1fn): {autonomy.get('be_teatro_boletos')}/{autonomy.get('be_real_una_funcion')} · burn/d ~${autonomy.get('burn_diario_implicito')}")
        print(f"   Nivel: {nivel}")
        if nivel == "🔴":
            alerta_urgente = next((a for a in autonomy["alertas"] if a["nivel"] == "🔴"), None)
            if alerta_urgente:
                notificar(
                    f"{alerta_urgente['tipo']} — El Gorila S2\n\n"
                    f"{alerta_urgente['mensaje']}\n\nAcción: {alerta_urgente['accion']}\n\n"
                    f"CPA_real: ${cpa or 'N/D'} · banda {autonomy.get('decision_band')}\n"
                    f"Util contrib: ${autonomy.get('util_contrib')}\n"
                    f"Gasto: ${autonomy['spend_total']:.0f} · ventas: {autonomy['ventas_boletera_semana']}\n\n"
                    f"— Agente 03, {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    urgente=True
                )
        save_check_log(
            cpa, nivel, autonomy.get("spend_total", 0),
            autonomy.get("ventas_boletera_semana", 0),
            autonomy=autonomy,
        )
        write_modelo_diario(meta, gads, boletera, autonomy)
        _bitacora(
            "check equilibrio CPA+util",
            f"CPA ${cpa or 'N/D'} · banda {autonomy.get('decision_band')} · util ${autonomy.get('util_contrib')} · "
            f"nivel {nivel} · ventas {autonomy.get('ventas_boletera_semana')} · spend ${autonomy.get('spend_total', 0):.0f}",
            outcome="ok" if nivel != "🔴" else "blocked",
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
    write_modelo_diario(meta, gads, boletera, autonomy)

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
    _bitacora(
        "reporte semanal Arranque D",
        f"CPA ${autonomy.get('cpa_real') or 'N/D'} · nivel {nivel} · score {analysis.get('score')} · {week_label}",
        outcome="ok" if nivel != "🔴" else "blocked",
    )


if __name__ == "__main__":
    main()

