#!/usr/bin/env python3
"""
_crear_campanas_s2.py — El Gorila S2
Crea estructura completa de campañas Meta en estado PAUSED.

CAMPANAS QUE CREA:
  A) EG_S2_CORE    — CBO, Ventas, 4 ad sets  [ID existente: 52509577662626]
  B) EG_S2_FLEX    — ABO, Ventas, 2 ad sets
  C) EG_S2_NURTURE — ABO, Engagement, 1 ad set

Uso: python3 _crear_campanas_s2.py
"""

import os, json, time, sys, requests
from pathlib import Path
from dotenv import load_dotenv

# ─── Config ───────────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent / ".env")
TOKEN = os.getenv("SYSTEM_USER_ACCESS_TOKEN")
ACT   = "act_389427487828383"
PIXEL = "24471801772518505"
BASE  = "https://graph.facebook.com/v19.0"

# ─── IDs de audiencias ya existentes en Meta ──────────────────────────────────
LAL_COMPRADORES_1PCT   = "52502597939826"
LAL_PIXEL_S1_1PCT      = "6964235534622"
LAL_PIXEL_S1_2PCT      = "6948229463422"
LAL_PIXEL_S1_3PCT      = "6939226412422"

CA_COMPRADORES_EMAIL   = "52502597938626"
CA_COMPRADORES_PIXEL_1 = "6964231386822"
CA_COMPRADORES_PIXEL_2 = "6964226799622"

CA_VISITANTES_30D      = "6964081287022"
CA_PURCHASE_180D       = "6964081170622"
CA_ADDTOCART_30D       = "6964081110822"
CA_VISITANTES_7D       = "6939184242422"
CA_CHECKOUT_ABAND_14D  = "6939184203622"

EXCL = [
    {"id": CA_COMPRADORES_EMAIL},
    {"id": CA_COMPRADORES_PIXEL_1},
    {"id": CA_COMPRADORES_PIXEL_2},
]

INTERESES = [
    {"id": "6003154043305", "name": "Performing arts"},
    {"id": "6003351312828", "name": "Musical theatre"},
    {"id": "6003268302136", "name": "Broadway theatre"},
    {"id": "6003273904571", "name": "Stand-up comedy"},
    {"id": "6003313798791", "name": "teatro"},
    {"id": "6003375678577", "name": "Cultural heritage"},
]

# Budgets en centavos MXN
B_B1 = 3000   # $30/dia  — test creativos
B_B2 = 1500   # $15/dia  — urgencia (PAUSED, activar manual)
B_C1 = 2000   # $20/dia  — nurture mensajes

# ─── Helper ───────────────────────────────────────────────────────────────────
created = {}

def post(path, **kwargs):
    """POST a Meta Graph API via JSON body (soporta arrays como special_ad_categories)."""
    kwargs["access_token"] = TOKEN
    # Deserializar campos pre-serializados para enviarlos como objetos JSON reales
    for key in ("targeting", "promoted_object"):
        if key in kwargs and isinstance(kwargs[key], str):
            kwargs[key] = json.loads(kwargs[key])
    r = requests.post(f"{BASE}{path}", json=kwargs, timeout=60)
    body = r.json()
    if not r.ok or "error" in body:
        err = body.get("error", {})
        print(f"  FALLA {path}")
        print(f"  code={err.get('code')} type={err.get('type')}")
        print(f"  msg= {err.get('message', r.text[:400])}")
        print(f"  sub= {err.get('error_subcode','')} | {err.get('error_user_title','')}")
        return None
    return body

def t(spec):
    """Serializa targeting spec a JSON string. Inyecta advantage_audience=0."""
    spec.setdefault("targeting_automation", {"advantage_audience": 0})
    return json.dumps(spec, ensure_ascii=False)

def geo_cdmx():
    return {"regions": [{"key": "2513"}]}

def geo_mx():
    return {"countries": ["MX"]}

def prom_checkout():
    return json.dumps({"pixel_id": PIXEL, "custom_event_type": "INITIATED_CHECKOUT"})

def prom_purchase():
    return json.dumps({"pixel_id": PIXEL, "custom_event_type": "PURCHASE"})

def prom_pixel_only():
    """Solo pixel_id — para promoted_object a nivel campana."""
    return json.dumps({"pixel_id": PIXEL})

# ══════════════════════════════════════════════════════════════════════════════
# CAMPANA A — EG_S2_CORE (CBO, ya existe)
# ══════════════════════════════════════════════════════════════════════════════
CAMP_A_ID = "52509577662626"
created["CAMP_A"] = CAMP_A_ID
# A1, A2, A4 ya creados en run anterior
created["AS_A1"] = "52510309389226"
created["AS_A2"] = "52510309421626"
created["AS_A4"] = "52510309478426"
created["AS_A3"] = "52510312190026"

print(f"\n{'='*60}")
print(f"CAMPANA A — EG_S2_CORE (existente: {CAMP_A_ID})")
print(f"{'='*60}")
print(f"  AS-A1 ya existe: {created['AS_A1']} ✅")
print(f"  AS-A2 ya existe: {created['AS_A2']} ✅")
print(f"  AS-A3 ya existe: {created['AS_A3']} ✅")
print(f"  AS-A4 ya existe: {created['AS_A4']} ✅")

# ══════════════════════════════════════════════════════════════════════════════
# CAMPANA B — EG_S2_FLEX (ABO, Ventas)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("CAMPANA B — EG_S2_FLEX (ABO, Ventas)")
print(f"{'='*60}")

CAMP_B_ID = "52510312818026"
created["CAMP_B"] = CAMP_B_ID
print(f"Campana B (existente): {CAMP_B_ID} ✅")

# AS-B1 ya existe
AS_B1_ID = "52510367492026"
created["AS_B1"] = AS_B1_ID
print(f"  AS-B1 ya existe: {AS_B1_ID} ✅")
time.sleep(1)

# AS-B2 — Urgencia/Escasez (activar MANUAL cuando funcion < 70% aforo)
print("  AS-B2: Urgencia/Escasez (PAUSED manual)...")
r = post(f"/{ACT}/adsets",
    name="AS-B2_Urgencia-Escasez_MANUAL",
    campaign_id=CAMP_B_ID,
    status="PAUSED",
    daily_budget=5000,  # $50 MXN/dia — minimo Meta para PURCHASE optimization
    bid_strategy="LOWEST_COST_WITHOUT_CAP",
    optimization_goal="OFFSITE_CONVERSIONS",
    billing_event="IMPRESSIONS",
    destination_type="WEBSITE",
    promoted_object=prom_purchase(),
    targeting=t({
        "geo_locations": geo_cdmx(),
        "age_min": 25, "age_max": 54,
        "custom_audiences": [
            {"id": LAL_COMPRADORES_1PCT},
            {"id": LAL_PIXEL_S1_1PCT},
            {"id": CA_VISITANTES_30D},
            {"id": CA_CHECKOUT_ABAND_14D},
        ],
        "excluded_custom_audiences": EXCL,
    }),
)
if r:
    created["AS_B2"] = r["id"]; print(f"  OK: {r['id']}")
time.sleep(1)

# ══════════════════════════════════════════════════════════════════════════════
# CAMPANA C — EG_S2_NURTURE (ABO, Engagement/Mensajes)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("CAMPANA C — EG_S2_NURTURE (ABO, Engagement)")
print(f"{'='*60}")

CAMP_C_ID = "52510367498226"
created["CAMP_C"] = CAMP_C_ID
print(f"Campana C (existente): {CAMP_C_ID} ✅")

AS_C1_ID = "52510367502226"
created["AS_C1"] = AS_C1_ID
print(f"  AS-C1 ya existe: {AS_C1_ID} ✅")

# ══════════════════════════════════════════════════════════════════════════════
# RESUMEN
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("RESUMEN — IDs CREADOS")
print(f"{'='*60}")
for k, v in created.items():
    print(f"  {k:<12} = {v}")

ok = len([v for v in created.values() if v])
print(f"\n{ok}/{len(created)} recursos creados exitosamente.")
if ok < len(created):
    print("Los que fallaron se pueden crear manualmente en Ads Manager.")

print("""
PROXIMOS PASOS:
1. Ir a Ads Manager act_389427487828383
2. Entrar a cada ad set y agregar los creativos (ver SETUP-CAMPANA-META-S2.md)
3. Activar Campana A + AS-B1 + AS-C1
4. AS-B2 (urgencia): dejar PAUSED, activar solo manual cuando funcion < 70% aforo
5. Agregar UTMs en todas las URLs antes de activar
""")
