#!/usr/bin/env python3
"""Monitor GA4 en tiempo real para validar el funnel durante una compra de prueba."""
import os, sys, time, datetime, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
CID = os.getenv("GOOGLE_ADS_CLIENT_ID")
CSEC = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
REF = os.getenv("GOOGLE_ANALYTICS_REFRESH_TOKEN")
PROP = os.getenv("GA4_PROPERTY_ID", "529010529")
FUNNEL = ["view_item", "add_to_cart", "begin_checkout", "add_payment_info", "purchase"]


def token():
    return requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": CID, "client_secret": CSEC,
        "refresh_token": REF, "grant_type": "refresh_token"}, timeout=15).json()["access_token"]


def realtime(tok):
    r = requests.post(
        f"https://analyticsdata.googleapis.com/v1beta/properties/{PROP}:runRealtimeReport",
        headers={"Authorization": f"Bearer {tok}"},
        json={"dimensions": [{"name": "eventName"}], "metrics": [{"name": "eventCount"}]}, timeout=20)
    if not r.ok:
        return None
    return {row["dimensionValues"][0]["value"]: int(row["metricValues"][0]["value"])
            for row in r.json().get("rows", [])}


minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 15
tok, tok_ts = token(), time.time()
print(f"GA4 {PROP} · monitor {minutes} min · haz la compra ahora\n", flush=True)
seen, deadline = {}, time.time() + minutes * 60
while time.time() < deadline:
    if time.time() - tok_ts > 3000:
        tok, tok_ts = token(), time.time()
    data = realtime(tok) or {}
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    fn = {k: data.get(k, 0) for k in FUNNEL if data.get(k, 0)}
    line = " · ".join(f"{k}={v}" for k, v in fn.items()) or "(sin eventos de funnel aun)"
    print(f"[{ts}] {line}", flush=True)
    for k, v in fn.items():
        if v > seen.get(k, 0):
            tag = "PURCHASE_OK" if k == "purchase" else "evento"
            print(f"   >>> {tag}: {k} -> {v}", flush=True)
        seen[k] = v
    time.sleep(15)
print(f"\nFin. Resumen funnel: {seen}", flush=True)
