#!/usr/bin/env python3
"""Inventario del contenedor GTM: workspaces, tags, triggers, variables."""
import os, sys, json, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

CID = os.getenv("GOOGLE_ADS_CLIENT_ID")
CSEC = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
REF = os.getenv("GOOGLE_TAGMANAGER_REFRESH_TOKEN")
CONTAINER = "accounts/6346027247/containers/247272198"

tok = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CID, "client_secret": CSEC,
    "refresh_token": REF, "grant_type": "refresh_token"}, timeout=20).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}
B = "https://tagmanager.googleapis.com/tagmanager/v2"


def get(path):
    r = requests.get(f"{B}/{path}", headers=H, timeout=30)
    if not r.ok:
        print(f"[ERR {r.status_code}] {path}: {r.text[:200]}")
        return {}
    return r.json()


ws = get(f"{CONTAINER}/workspaces").get("workspace", [])
print("WORKSPACES:")
for w in ws:
    print(f"  - {w['name']}  (id {w['workspaceId']})  path={w['path']}")
wsp = ws[0]["path"] if ws else None
if not wsp:
    sys.exit("sin workspace")

print(f"\n=== usando workspace: {wsp} ===\n")

print("TRIGGERS:")
trg = {}
for t in get(f"{wsp}/triggers").get("trigger", []):
    trg[t["triggerId"]] = t["name"]
    extra = ""
    if t.get("customEventFilter"):
        vals = []
        for f in t["customEventFilter"]:
            for p in f.get("parameter", []):
                if p.get("key") == "arg1":
                    vals.append(p.get("value"))
        extra = f"  event~={vals}"
    print(f"  [{t['triggerId']}] {t['name']}  type={t.get('type')}{extra}")

print("\nTAGS:")
for t in get(f"{wsp}/tags").get("tag", []):
    fire = [trg.get(i, i) for i in t.get("firingTriggerId", [])]
    print(f"  [{t['tagId']}] {t['name']}  type={t.get('type')}  paused={t.get('paused', False)}")
    print(f"        firing: {fire}")
    # parametros clave (measurement id, event name, conversion id/label)
    for p in t.get("parameter", []):
        if p.get("key") in ("measurementId", "measurementIdOverride", "tagId", "eventName",
                             "conversionId", "conversionLabel", "sendTo"):
            print(f"        · {p['key']} = {p.get('value')}")

print("\nVARIABLES (user-defined):")
for v in get(f"{wsp}/variables").get("variable", []):
    print(f"  [{v['variableId']}] {v['name']}  type={v.get('type')}")

print("\nBUILT-IN VARIABLES:")
biv = get(f"{wsp}/built_in_variables").get("builtInVariable", [])
print("  " + ", ".join(sorted({b.get("name") for b in biv})))
