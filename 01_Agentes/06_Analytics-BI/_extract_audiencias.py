#!/usr/bin/env python3
"""DESCARGA (read-only) del inventario de audiencias en Meta, Google Ads y GA4."""
import os, json, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ── credenciales ──
META_TOKEN = os.getenv("SYSTEM_USER_ACCESS_TOKEN")
AD_ACCOUNT = os.getenv("AD_ACCOUNT_ID", "act_389427487828383")
META_V = "v19.0"

GADS_CID = os.getenv("GOOGLE_ADS_CLIENT_ID")
GADS_SEC = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
GADS_REF = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
GADS_DEV = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
GADS_CUST = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "2681423694").replace("-", "")
GADS_LOGIN = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "8974056133")
GADS_VER = os.getenv("GOOGLE_ADS_API_VERSION", "v21")

GA4_REF = os.getenv("GOOGLE_ANALYTICS_REFRESH_TOKEN")
GA4_PROP = os.getenv("GA4_PROPERTY_ID", "529010529")


def gtoken(refresh):
    return requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": GADS_CID, "client_secret": GADS_SEC,
        "refresh_token": refresh, "grant_type": "refresh_token"}, timeout=20).json().get("access_token")


print("=" * 70)
print("META — Custom Audiences")
print("=" * 70)
try:
    r = requests.get(
        f"https://graph.facebook.com/{META_V}/{AD_ACCOUNT}/customaudiences",
        params={"fields": "id,name,subtype,approximate_count_lower_bound,"
                          "approximate_count_upper_bound,description,operation_status,"
                          "retention_days,time_updated,data_source",
                "limit": 200, "access_token": META_TOKEN}, timeout=30)
    if not r.ok:
        print("  ERROR", r.status_code, r.text[:400])
    else:
        data = r.json().get("data", [])
        print(f"  {len(data)} custom audiences:")
        for a in data:
            lo = a.get("approximate_count_lower_bound", "?")
            hi = a.get("approximate_count_upper_bound", "?")
            st = (a.get("operation_status") or {}).get("description", "?")
            print(f"   · [{a['id']}] {a.get('name')}")
            print(f"        subtype={a.get('subtype')} · size≈{lo}-{hi} · estado={st} · retención={a.get('retention_days')}d")
except Exception as e:
    print("  EXC", e)

print("\n" + "=" * 70)
print("GOOGLE ADS — User Lists (audiencias)")
print("=" * 70)
try:
    tok = gtoken(GADS_REF)
    r = requests.post(
        f"https://googleads.googleapis.com/{GADS_VER}/customers/{GADS_CUST}/googleAds:search",
        headers={"Authorization": f"Bearer {tok}", "developer-token": GADS_DEV,
                 "login-customer-id": GADS_LOGIN, "Content-Type": "application/json"},
        json={"query": "SELECT user_list.id, user_list.name, user_list.type, "
                       "user_list.size_for_display, user_list.size_for_search, "
                       "user_list.membership_status, user_list.description "
                       "FROM user_list ORDER BY user_list.size_for_display DESC"}, timeout=30)
    if not r.ok:
        print("  ERROR", r.status_code, r.text[:400])
    else:
        rows = r.json().get("results", [])
        print(f"  {len(rows)} user lists:")
        for row in rows:
            ul = row.get("userList", {})
            print(f"   · [{ul.get('id')}] {ul.get('name')}  type={ul.get('type')} "
                  f"estado={ul.get('membershipStatus')} display≈{ul.get('sizeForDisplay')} search≈{ul.get('sizeForSearch')}")
except Exception as e:
    print("  EXC", e)

print("\n" + "=" * 70)
print("GA4 — Audiences (Admin API)")
print("=" * 70)
try:
    tok = gtoken(GA4_REF)
    r = requests.get(
        f"https://analyticsadmin.googleapis.com/v1beta/properties/{GA4_PROP}/audiences",
        headers={"Authorization": f"Bearer {tok}"}, timeout=30)
    if not r.ok:
        print("  ERROR", r.status_code, r.text[:400])
    else:
        auds = r.json().get("audiences", [])
        print(f"  {len(auds)} audiencias GA4:")
        for a in auds:
            print(f"   · {a.get('displayName')}  ({a.get('name','').split('/')[-1]}) "
                  f"membershipDurationDays={a.get('membershipDurationDays')}")
except Exception as e:
    print("  EXC", e)

print("\nDONE.")
