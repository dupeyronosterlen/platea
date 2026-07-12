#!/usr/bin/env python3
"""
Monitor GA4 en tiempo real — para validar que los tags disparan durante una venta de prueba.

Requiere un refresh token con scope de Analytics:
  https://www.googleapis.com/auth/analytics.readonly
(ademas del de adwords). Generar en OAuth Playground con AMBOS scopes y pegar en .env como:
  GOOGLE_ANALYTICS_REFRESH_TOKEN=1//....   (si no existe, usa GOOGLE_ADS_REFRESH_TOKEN)

Uso:
  python3 _monitor_ga4_realtime.py            -> sondea cada 15s durante 10 min
  python3 _monitor_ga4_realtime.py 5 30       -> 5 min, cada 30s
"""
import os
import sys
import time
import datetime
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
REFRESH = os.getenv("GOOGLE_ANALYTICS_REFRESH_TOKEN") or os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "529010529")

# Eventos del funnel que esperamos ver disparar
FUNNEL = ["page_view", "view_item_list", "view_item", "select_item",
          "add_to_cart", "begin_checkout", "add_payment_info", "purchase", "generate_lead"]


def get_token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH, "grant_type": "refresh_token"}, timeout=15)
    if not r.ok:
        print(f"[oauth] ERROR {r.status_code}: {r.text[:300]}")
        return None
    scopes = r.json().get("scope", "")
    if "analytics" not in scopes:
        print("[oauth] ⚠️  El token NO tiene scope de Analytics.")
        print(f"        scopes actuales: {scopes}")
        print("        Genera un refresh token nuevo con scope analytics.readonly.")
        return None
    return r.json().get("access_token")


def realtime(token):
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{PROPERTY_ID}:runRealtimeReport"
    body = {
        "dimensions": [{"name": "eventName"}],
        "metrics": [{"name": "eventCount"}],
    }
    r = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json=body, timeout=20)
    if not r.ok:
        return None, f"{r.status_code}: {r.text[:300]}"
    data = {}
    for row in r.json().get("rows", []):
        name = row["dimensionValues"][0]["value"]
        cnt = int(row["metricValues"][0]["value"])
        data[name] = cnt
    return data, None


def main():
    minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    token = get_token()
    if not token:
        return
    print(f"✅ Conectado a GA4 property {PROPERTY_ID}")
    print(f"   Monitoreando {minutes} min (cada {interval}s). Usuarios activos en ultimos 30 min.\n")
    print("   Haz la venta de prueba ahora. Veras cada evento al dispararse.\n")

    seen = {}
    deadline = time.time() + minutes * 60
    token_ts = time.time()
    while time.time() < deadline:
        if time.time() - token_ts > 3000:  # refrescar token cada ~50 min
            token = get_token(); token_ts = time.time()
        data, err = realtime(token)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        if err:
            print(f"[{ts}] error: {err}")
        else:
            funnel_now = {k: data.get(k, 0) for k in FUNNEL if data.get(k, 0)}
            otros = {k: v for k, v in data.items() if k not in FUNNEL}
            linea = " · ".join(f"{k}={v}" for k, v in funnel_now.items()) or "(sin eventos de funnel aun)"
            print(f"[{ts}] FUNNEL: {linea}")
            # Avisar de eventos nuevos
            for k, v in funnel_now.items():
                if v > seen.get(k, 0):
                    flag = "🎯" if k in ("purchase", "begin_checkout", "add_to_cart") else "•"
                    print(f"         {flag} NUEVO/INCREMENTO: {k} -> {v}")
                seen[k] = v
            if otros:
                print(f"         otros: {', '.join(f'{k}={v}' for k,v in list(otros.items())[:8])}")
        time.sleep(interval)
    print("\n⏹  Fin del monitoreo.")
    print(f"   Resumen funnel: {seen}")


if __name__ == "__main__":
    main()
