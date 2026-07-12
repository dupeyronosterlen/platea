#!/usr/bin/env python3
"""Verificación puntual de acciones de conversión (tags) en Google Ads."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
DEV_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "2681423694").replace("-", "")
LOGIN_CID = "8974056133"  # MCC
API = "v21"


def get_token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }, timeout=15)
    print(f"[oauth] status={r.status_code}")
    if not r.ok:
        print(r.text[:400])
        return None
    return r.json().get("access_token")


def search(token, query, login=True):
    headers = {
        "Authorization": f"Bearer {token}",
        "developer-token": DEV_TOKEN,
        "Content-Type": "application/json",
    }
    if login:
        headers["login-customer-id"] = LOGIN_CID
    url = f"https://googleads.googleapis.com/{API}/customers/{CUSTOMER_ID}/googleAds:search"
    return requests.post(url, headers=headers, json={"query": query}, timeout=30)


def main():
    token = get_token()
    if not token:
        return
    print("[oauth] OK\n")

    print("=== 1. ACCIONES DE CONVERSION (config) ===")
    q1 = """
        SELECT
            conversion_action.name,
            conversion_action.status,
            conversion_action.type,
            conversion_action.category,
            conversion_action.counting_type,
            conversion_action.primary_for_goal,
            conversion_action.origin
        FROM conversion_action
        ORDER BY conversion_action.status
    """
    r = search(token, q1)
    print(f"status={r.status_code}")
    if not r.ok:
        print(r.text[:1000])
        print("\n[retry sin login-customer-id]")
        r = search(token, q1, login=False)
        print(f"status={r.status_code}")
        if not r.ok:
            print(r.text[:1000])
            return
    for row in r.json().get("results", []):
        ca = row.get("conversionAction", {})
        print(f"  - {str(ca.get('name')):42} | {str(ca.get('status')):9} | {ca.get('type')} | {ca.get('category')} | count={ca.get('countingType')} | primary={ca.get('primaryForGoal')} | origin={ca.get('origin')}")

    print("\n=== 2. CONVERSIONES POR ACCION (ultimos 30 dias) ===")
    q2 = """
        SELECT
            segments.conversion_action_name,
            metrics.all_conversions,
            metrics.conversions
        FROM customer
        WHERE segments.date DURING LAST_30_DAYS
    """
    r2 = search(token, q2)
    print(f"status={r2.status_code}")
    if r2.ok:
        rows = r2.json().get("results", [])
        if not rows:
            print("  (sin conversiones registradas en 30 dias)")
        for row in rows:
            seg = row.get("segments", {})
            m = row.get("metrics", {})
            print(f"  - {str(seg.get('conversionActionName','?')):42} | all_conv={m.get('allConversions',0)} | conv={m.get('conversions',0)}")
    else:
        print(r2.text[:1000])

    print("\n=== 3. CONVERSIONES POR DIA (ultimos 7 dias) ===")
    q3 = """
        SELECT
            segments.date,
            segments.conversion_action_name,
            metrics.all_conversions
        FROM customer
        WHERE segments.date DURING LAST_7_DAYS
        ORDER BY segments.date DESC
    """
    r3 = search(token, q3)
    print(f"status={r3.status_code}")
    if r3.ok:
        rows = r3.json().get("results", [])
        if not rows:
            print("  (sin conversiones en 7 dias)")
        for row in rows:
            seg = row.get("segments", {})
            m = row.get("metrics", {})
            print(f"  - {seg.get('date')} | {str(seg.get('conversionActionName','?')):38} | {m.get('allConversions',0)}")
    else:
        print(r3.text[:1000])

    print("\n=== 4. CAMPANAS ACTIVAS (ultimos 30 dias) ===")
    q4 = """
        SELECT
            campaign.name,
            campaign.status,
            metrics.cost_micros,
            metrics.clicks,
            metrics.impressions,
            metrics.conversions
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS
        ORDER BY metrics.cost_micros DESC
    """
    r4 = search(token, q4)
    print(f"status={r4.status_code}")
    if r4.ok:
        rows = r4.json().get("results", [])
        if not rows:
            print("  (sin datos de campanas en 30 dias)")
        for row in rows:
            c = row.get("campaign", {})
            m = row.get("metrics", {})
            cost = int(m.get("costMicros", 0)) / 1_000_000
            print(f"  - {str(c.get('name')):38} | {c.get('status'):8} | ${cost:>8.0f} | clicks={m.get('clicks',0)} | impr={m.get('impressions',0)} | conv={m.get('conversions',0)}")
    else:
        print(r4.text[:1000])


if __name__ == "__main__":
    main()
