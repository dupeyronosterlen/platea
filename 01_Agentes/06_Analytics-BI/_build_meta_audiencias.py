#!/usr/bin/env python3
"""Meta: refresca CRM de compradores (hash SHA-256), crea lookalike y ensambla
los públicos anichados (saved audiences) listos para presupuesto. No imprime PII."""
import os, csv, re, json, hashlib, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
T = os.getenv("SYSTEM_USER_ACCESS_TOKEN")
ACT = os.getenv("AD_ACCOUNT_ID", "act_389427487828383")
V = "v19.0"
G = f"https://graph.facebook.com/{V}"
BUYERS = Path("/Volumes/La Mancha/Elgorila/_PARA-AGENCIA/privado/BUYERS FINAL.csv")

# claves descubiertas
GEO_CDMX = {"regions": [{"key": "2513"}]}            # Distrito Federal
INTERESES_CULTURA = [
    {"id": "6003154043305", "name": "Performing arts"},
    {"id": "6003351312828", "name": "Musical theatre"},
    {"id": "6003268302136", "name": "Broadway theatre"},
    {"id": "6003273904571", "name": "Stand-up comedy"},
    {"id": "6003376307381", "name": "Franz Kafka"},
    {"id": "6003313798791", "name": "teatro"},
    {"id": "6003375678577", "name": "Cultural heritage"},
]
# LALs ya existentes (de temporada pasada)
LAL_EXISTENTES = ["6964235534622", "6948229463422", "6939226412422"]
# públicos cálidos de sitio/engagement
WARM = ["6964081287022", "6964081170622", "6964081110822", "6939184242422", "6939184203622"]
# compradores (a excluir en acquisition)
BUYERS_CA = ["6964231386822", "6964226799622"]


def post(path, **data):
    data["access_token"] = T
    r = requests.post(f"{G}{path}", data=data, timeout=60)
    if not r.ok:
        print(f"  [ERR {r.status_code}] {path}: {r.text[:400]}")
        return None
    return r.json()


def sha(s):
    return hashlib.sha256(s.strip().lower().encode()).hexdigest()


created = {}

# ── 1) CRM compradores (refresh) ──
print("1) Custom Audience compradores (CRM)…")
emails = []
with open(BUYERS, encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        e = (row.get("Email") or "").strip().lower()
        if re.match(r"^[^@]+@[^@]+\.[^@]+$", e):
            emails.append(e)
emails = sorted(set(emails))
ca = post(f"/{ACT}/customaudiences",
          name="EG_S2_Compradores_S1 (email)",
          subtype="CUSTOM", customer_file_source="USER_PROVIDED_ONLY",
          description="Compradores S1 boletera — subido por API 18 jun 2026")
if ca and ca.get("id"):
    crm_id = ca["id"]; created["CRM compradores"] = crm_id
    print(f"   ✅ creada id={crm_id} — subiendo {len(emails)} emails hasheados…")
    payload = json.dumps({"schema": ["EMAIL"], "data": [[sha(e)] for e in emails]})
    up = post(f"/{crm_id}/users", payload=payload)
    if up:
        print(f"   ✅ recibidos={up.get('num_received')} · invalidos={up.get('num_invalid_entries')}")
else:
    crm_id = None

# ── 2) Lookalike 1% MX desde el CRM nuevo ──
lal_new = None
if crm_id:
    print("2) Lookalike 1% MX desde CRM…")
    lk = post(f"/{ACT}/customaudiences",
              name="EG_S2_Lookalike_Compradores_1pct_MX",
              subtype="LOOKALIKE", origin_audience_id=crm_id,
              lookalike_spec=json.dumps({"type": "similarity", "ratio": 0.01, "country": "MX"}))
    if lk and lk.get("id"):
        lal_new = lk["id"]; created["Lookalike 1% compradores"] = lal_new
        print(f"   ✅ creado id={lal_new} (procesa en horas)")

# ── 3) Saved audiences (públicos anichados) ──
print("3) Saved audiences anichados…")
lal_stack = ([{"id": lal_new}] if lal_new else []) + [{"id": i} for i in LAL_EXISTENTES]


def saved(name, targeting):
    r = post(f"/{ACT}/saved_audiences", name=name, targeting=json.dumps(targeting))
    if r and r.get("id"):
        created[name] = r["id"]
        print(f"   ✅ {name} → id={r['id']}")
    else:
        print(f"   ✗ {name}")


# A) Stack de lookalikes ∩ CDMX ∩ 25-54
saved("EG_S2_LAL-Stack_CDMX_25-54", {
    "geo_locations": GEO_CDMX, "age_min": 25, "age_max": 54,
    "custom_audiences": lal_stack,
    "targeting_optimization": "none",
})

# B) Interés cultural/Kafka ∩ CDMX ∩ 25-54
saved("EG_S2_Cultura-Kafka_CDMX_25-54", {
    "geo_locations": GEO_CDMX, "age_min": 25, "age_max": 54,
    "flexible_spec": [{"interests": INTERESES_CULTURA}],
})

# C) Mujeres 25-44 ∩ CDMX ∩ cultura
saved("EG_S2_Mujeres_25-44_CDMX_Cultura", {
    "geo_locations": GEO_CDMX, "age_min": 25, "age_max": 44, "genders": [2],
    "flexible_spec": [{"interests": INTERESES_CULTURA}],
})

# D) Retargeting cálido (sitio/engagement) excluyendo compradores
saved("EG_S2_Retargeting_Calido_excl-compradores", {
    "geo_locations": {"countries": ["MX"]},
    "custom_audiences": [{"id": i} for i in WARM],
    "excluded_custom_audiences": [{"id": i} for i in BUYERS_CA] + ([{"id": crm_id}] if crm_id else []),
})

print("\n=== RESUMEN creado ===")
for k, v in created.items():
    print(f"  · {k}: {v}")
