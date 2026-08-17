#!/usr/bin/env python3
"""
Conexiones de datos del Agente 06 — Analytics y BI.

Esta es la conexión "viva" que el agente debe poseer:
  - Google Ads API (REST, GAQL, v21) vía OAuth refresh token
  - GA4 Data API (reportes estándar + tiempo real) vía OAuth refresh token

Uso como módulo:
    from conexiones import (
        google_ads_conversiones, ga4_eventos_recientes,
        ga4_tiempo_real, verificar_tags,
    )

Uso directo (diagnóstico rápido):
    python conexiones.py            -> verificación completa de tags
    python conexiones.py ga4        -> eventos GA4 últimos 30 min (tiempo real)
    python conexiones.py ads        -> acciones de conversión Google Ads
"""
import os
import sys
import datetime
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ── Google Ads ────────────────────────────────────────────────────────────────
GADS_CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID")
GADS_CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
GADS_REFRESH = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
GADS_DEV_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
GADS_CUSTOMER = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "2681423694").replace("-", "")
GADS_LOGIN = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "8974056133")
GADS_VERSION = os.getenv("GOOGLE_ADS_API_VERSION", "v21")

# ── GA4 ───────────────────────────────────────────────────────────────────────
GA4_REFRESH = os.getenv("GOOGLE_ANALYTICS_REFRESH_TOKEN")
GA4_PROPERTY = os.getenv("GA4_PROPERTY_ID", "529010529")

FUNNEL = ["view_item_list", "view_item", "select_item", "add_to_cart",
          "begin_checkout", "add_payment_info", "purchase"]


def _oauth_token(refresh_token: str) -> str | None:
    """Intercambia un refresh token por un access token."""
    if not all([GADS_CLIENT_ID, GADS_CLIENT_SECRET, refresh_token]):
        return None
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": GADS_CLIENT_ID,
        "client_secret": GADS_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }, timeout=15)
    return r.json().get("access_token") if r.ok else None


# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE ADS
# ══════════════════════════════════════════════════════════════════════════════
def google_ads_search(query: str) -> dict:
    """Ejecuta una consulta GAQL contra la cuenta de Google Ads."""
    token = _oauth_token(GADS_REFRESH)
    if not token:
        return {"error": "oauth_failed", "results": []}
    url = f"https://googleads.googleapis.com/{GADS_VERSION}/customers/{GADS_CUSTOMER}/googleAds:search"
    headers = {
        "Authorization": f"Bearer {token}",
        "developer-token": GADS_DEV_TOKEN,
        "login-customer-id": GADS_LOGIN,
        "Content-Type": "application/json",
    }
    r = requests.post(url, headers=headers, json={"query": query}, timeout=30)
    if not r.ok:
        return {"error": f"{r.status_code}: {r.text[:300]}", "results": []}
    return r.json()


def google_ads_conversiones(dias: int = 30) -> dict:
    """
    Salud de los tags de conversión en Google Ads:
      - lista de acciones de conversión con estado (ENABLED/REMOVED/HIDDEN)
      - conversiones registradas en los últimos N días (si 0 -> tag sin disparar)
    """
    acciones = google_ads_search("""
        SELECT conversion_action.name, conversion_action.status,
               conversion_action.type, conversion_action.category,
               conversion_action.primary_for_goal, conversion_action.origin
        FROM conversion_action ORDER BY conversion_action.status
    """)
    rango = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}.get(dias, "LAST_30_DAYS")
    conv = google_ads_search(f"""
        SELECT segments.conversion_action_name, metrics.all_conversions, metrics.conversions
        FROM customer WHERE segments.date DURING {rango}
    """)
    por_accion = {}
    for row in conv.get("results", []):
        nombre = row.get("segments", {}).get("conversionActionName", "?")
        m = row.get("metrics", {})
        por_accion[nombre] = {
            "all_conversions": m.get("allConversions", 0),
            "conversions": m.get("conversions", 0),
        }
    tags = []
    for row in acciones.get("results", []):
        ca = row.get("conversionAction", {})
        nombre = ca.get("name")
        tags.append({
            "nombre": nombre,
            "estado": ca.get("status"),
            "tipo": ca.get("type"),
            "categoria": ca.get("category"),
            "primaria": ca.get("primaryForGoal"),
            "origen": ca.get("origin"),
            "conversiones_periodo": por_accion.get(nombre, {}),
        })
    return {"dias": dias, "tags": tags, "error": acciones.get("error") or conv.get("error")}


# ══════════════════════════════════════════════════════════════════════════════
# GA4
# ══════════════════════════════════════════════════════════════════════════════
def ga4_tiempo_real() -> dict:
    """Eventos de GA4 en los últimos 30 min (tiempo real)."""
    token = _oauth_token(GA4_REFRESH)
    if not token:
        return {"error": "oauth_failed (¿token con scope analytics.readonly?)", "eventos": {}}
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{GA4_PROPERTY}:runRealtimeReport"
    r = requests.post(url, headers={"Authorization": f"Bearer {token}"},
                      json={"dimensions": [{"name": "eventName"}],
                            "metrics": [{"name": "eventCount"}]}, timeout=20)
    if not r.ok:
        return {"error": f"{r.status_code}: {r.text[:300]}", "eventos": {}}
    eventos = {row["dimensionValues"][0]["value"]: int(row["metricValues"][0]["value"])
               for row in r.json().get("rows", [])}
    return {"eventos": eventos}


def ga4_eventos_recientes(dias: int = 7) -> dict:
    """Conteo de eventos GA4 por nombre en los últimos N días (reporte estándar)."""
    token = _oauth_token(GA4_REFRESH)
    if not token:
        return {"error": "oauth_failed", "eventos": {}}
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{GA4_PROPERTY}:runReport"
    body = {
        "dateRanges": [{"startDate": f"{dias}daysAgo", "endDate": "today"}],
        "dimensions": [{"name": "eventName"}],
        "metrics": [{"name": "eventCount"}],
    }
    r = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json=body, timeout=20)
    if not r.ok:
        return {"error": f"{r.status_code}: {r.text[:300]}", "eventos": {}}
    eventos = {row["dimensionValues"][0]["value"]: int(row["metricValues"][0]["value"])
               for row in r.json().get("rows", [])}
    return {"dias": dias, "eventos": eventos}


# ══════════════════════════════════════════════════════════════════════════════
# VERIFICACIÓN DE TAGS (la usa B-1, bloqueante)
# ══════════════════════════════════════════════════════════════════════════════
def verificar_tags(dias: int = 7) -> dict:
    """
    Reporte de salud de tags cruzando Google Ads + GA4.
    Señala qué eventos del funnel de ecommerce están disparando y cuáles no.
    """
    ga4 = ga4_eventos_recientes(dias=dias)
    ads = google_ads_conversiones(dias=30)
    eventos_ga4 = ga4.get("eventos", {})
    funnel_estado = {ev: ("OK" if eventos_ga4.get(ev, 0) > 0 else "SIN_DISPARAR") for ev in FUNNEL}
    faltantes = [ev for ev, st in funnel_estado.items() if st == "SIN_DISPARAR"]
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "ga4_property": GA4_PROPERTY,
        "google_ads_customer": GADS_CUSTOMER,
        "funnel_ga4": funnel_estado,
        "eventos_faltantes": faltantes,
        "purchase_ok": funnel_estado.get("purchase") == "OK",
        "eventos_ga4_todos": eventos_ga4,
        "tags_google_ads": ads.get("tags", []),
        "errores": {"ga4": ga4.get("error"), "ads": ads.get("error")},
    }


if __name__ == "__main__":
    import json
    modo = sys.argv[1] if len(sys.argv) > 1 else "all"
    if modo == "ga4":
        print(json.dumps(ga4_tiempo_real(), ensure_ascii=False, indent=2))
    elif modo == "ads":
        print(json.dumps(google_ads_conversiones(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(verificar_tags(), ensure_ascii=False, indent=2))
