#!/usr/bin/env python3
"""
_diag_meta.py — Diagnóstico rápido Meta API
Corre esto y pega el output completo.
"""
import os, json, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
TOKEN = os.getenv("SYSTEM_USER_ACCESS_TOKEN")
ACT   = "act_389427487828383"
CAMP_A = "52509577662626"
BASE  = "https://graph.facebook.com/v19.0"

def get(path, **params):
    params["access_token"] = TOKEN
    r = requests.get(f"{BASE}{path}", params=params)
    return r.json()

def post(path, **data):
    data["access_token"] = TOKEN
    r = requests.post(f"{BASE}{path}", data=data)
    return r.json()

print("="*60)
print("1. ESTADO ACTUAL DE CAMPAIGN A")
print("="*60)
info = get(f"/{CAMP_A}", fields="id,name,objective,status,daily_budget,promoted_object,buying_type")
print(json.dumps(info, indent=2, ensure_ascii=False))

print("\n" + "="*60)
print("2. INTENTO MINIMO — Campaign B sin params extras")
print("="*60)
r = post(f"/{ACT}/campaigns",
    name="EG_S2_FLEX_TEST",
    objective="OUTCOME_SALES",
    status="PAUSED",
)
print(json.dumps(r, indent=2, ensure_ascii=False))

if "id" in r:
    print(f"\n✅ Campaign B mínima CREADA: {r['id']}")
    print("Borrando test campaign...")
    d = requests.delete(f"{BASE}/{r['id']}", params={"access_token": TOKEN})
    print(f"Delete: {d.json()}")
else:
    print(f"\n❌ Fallo con subcode: {r.get('error',{}).get('error_subcode')}")
    print("→ Si subcode es 4834011: problema de PERMISOS del token o cuenta")

print("\n" + "="*60)
print("3. INTENTO MINIMO — Ad set bajo Campaign A")
print("="*60)
r2 = post(f"/{ACT}/adsets",
    name="DIAG_TEST_ADSET",
    campaign_id=CAMP_A,
    status="PAUSED",
    optimization_goal="OFFSITE_CONVERSIONS",
    billing_event="IMPRESSIONS",
    destination_type="WEBSITE",
    promoted_object=json.dumps({"pixel_id": "24471801772518505", "custom_event_type": "INITIATED_CHECKOUT"}),
    targeting=json.dumps({"geo_locations": {"countries": ["MX"]}, "age_min": 25, "age_max": 54}),
)
print(json.dumps(r2, indent=2, ensure_ascii=False))
if "id" in r2:
    print(f"\n✅ Ad set TEST CREADO: {r2['id']}")
    d = requests.delete(f"{BASE}/{r2['id']}", params={"access_token": TOKEN})
    print(f"Delete: {d.json()}")
else:
    err = r2.get("error", {})
    print(f"\n❌ Fallo: code={err.get('code')} sub={err.get('error_subcode')} msg={err.get('message')}")
