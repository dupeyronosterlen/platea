#!/usr/bin/env python3
"""Google Customer Match: crea lista CRM, sube los compradores S1 (emails hasheados) y lanza lookalike.
No imprime PII. Hashea SHA-256."""
import os, csv, re, json, hashlib, time, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
CID = os.getenv("GOOGLE_ADS_CLIENT_ID"); SEC = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
REF = os.getenv("GOOGLE_ADS_REFRESH_TOKEN"); DEV = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
CUST = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "2681423694").replace("-", "")
LOGIN = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "8974056133")
VER = os.getenv("GOOGLE_ADS_API_VERSION", "v21")
BUYERS = Path("/Volumes/La Mancha/Elgorila/_PARA-AGENCIA/privado/BUYERS FINAL.csv")

tok = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CID, "client_secret": SEC, "refresh_token": REF,
    "grant_type": "refresh_token"}, timeout=20).json()["access_token"]
H = {"Authorization": f"Bearer {tok}", "developer-token": DEV,
     "login-customer-id": LOGIN, "Content-Type": "application/json"}
B = f"https://googleads.googleapis.com/{VER}/customers/{CUST}"


def api(path, body):
    r = requests.post(f"{B}{path}", headers=H, json=body, timeout=60)
    if not r.ok:
        print(f"[ERR {r.status_code}] {path}\n{r.text[:600]}")
        return None
    return r.json()


def sha(s):
    return hashlib.sha256(s.strip().lower().encode()).hexdigest()


# emails únicos normalizados
emails = set()
with open(BUYERS, encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        e = (row.get("Email") or "").strip().lower()
        if re.match(r"^[^@]+@[^@]+\.[^@]+$", e):
            emails.add(e)
print(f"Emails únicos a subir: {len(emails)}")

# 1) Crear lista CRM
res = api("/userLists:mutate", {"operations": [{"create": {
    "name": "EG_S2_Compradores_S1 (CM email)",
    "description": "Compradores S1 boletera, subidos por API 18 jun 2026",
    "membershipLifeSpan": 540,
    "crmBasedUserList": {"uploadKeyType": "CONTACT_INFO", "dataSourceType": "FIRST_PARTY"},
}}]})
if not res:
    raise SystemExit("no se pudo crear la lista")
list_rn = res["results"][0]["resourceName"]
list_id = list_rn.split("/")[-1]
print(f"✅ Lista creada: {list_rn}")

# 2) Crear job de Customer Match
job = api("/offlineUserDataJobs:create", {"job": {
    "type": "CUSTOMER_MATCH_USER_LIST",
    "customerMatchUserListMetadata": {"userList": list_rn}}})
if not job:
    raise SystemExit("no se pudo crear el job")
job_rn = job["resourceName"]
print(f"✅ Job creado: {job_rn}")

# 3) addOperations (emails hasheados)
ops = [{"create": {"userIdentifiers": [{"hashedEmail": sha(e)}]}} for e in emails]
add = api(f"/{job_rn}:addOperations", {"enablePartialFailure": True, "operations": ops})
if add is None:
    raise SystemExit("fallo addOperations")
print(f"✅ {len(ops)} identificadores enviados al job")
if add.get("partialFailureError"):
    print("  ⚠️ partialFailure:", json.dumps(add["partialFailureError"])[:300])

# 4) run
run = api(f"/{job_rn}:run", {})
print("✅ Job lanzado (procesa en minutos/horas).")

# 5) Lookalike / similar (puede requerir match mínimo ~100 y horas de proceso)
print("\nIntentando crear lookalike segment del seed…")
lal = api("/userLists:mutate", {"operations": [{"create": {
    "name": "EG_S2_Lookalike_Compradores_S1",
    "description": "Lookalike de compradores S1 (seed CM)",
    "membershipLifeSpan": 540,
    "lookalikeUserList": {
        "seedUserListIds": [int(list_id)],
        "expansionLevel": "BALANCED",
        "countryCodes": ["MX"],
    }}}]})
if lal:
    print(f"✅ Lookalike creado: {lal['results'][0]['resourceName']}")
else:
    print("  (El lookalike puede fallar hasta que el seed tenga match suficiente; reintentar en unas horas.)")

print(f"\nLista CRM id={list_id}. Verificar tamaño en unas horas (size_for_display/search).")
