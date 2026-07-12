#!/usr/bin/env python3
"""
Fix #2 — Construye el ecommerce en GTM (workspace NUEVO, SIN publicar).
Crea: variables DLV, triggers customEvent y tags GA4 Event para el funnel.
Idempotente por nombre: si ya existe algo con el mismo nombre en el workspace, lo reusa.
"""
import os, json, sys, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
CONTAINER = "accounts/6346027247/containers/247272198"
GA4 = "G-NXF8093MDJ"
B = "https://tagmanager.googleapis.com/tagmanager/v2"

tok = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
    "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
    "refresh_token": os.getenv("GOOGLE_TAGMANAGER_REFRESH_TOKEN"),
    "grant_type": "refresh_token"}, timeout=20).json()["access_token"]
H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def api(method, path, body=None):
    r = requests.request(method, f"{B}/{path}", headers=H,
                         json=body, timeout=30)
    if not r.ok:
        print(f"[ERR {r.status_code}] {method} {path}\n{r.text[:500]}")
        sys.exit(1)
    return r.json()


# 1) Workspace nuevo (o reusar si ya existe por nombre)
WS_NAME = "Fix ecommerce tracking (Agente 06)"
existing = api("GET", f"{CONTAINER}/workspaces").get("workspace", [])
ws = next((w for w in existing if w["name"] == WS_NAME), None)
if not ws:
    ws = api("POST", f"{CONTAINER}/workspaces",
             {"name": WS_NAME, "description": "Consolida funnel de ecommerce a GTM. Creado por API."})
    print(f"✅ Workspace creado: {ws['name']} (id {ws['workspaceId']})")
else:
    print(f"↺ Workspace ya existía: {ws['name']} (id {ws['workspaceId']})")
WS = ws["path"]


def existing_by_name(kind):
    return {x["name"]: x for x in api("GET", f"{WS}/{kind}").get(kind[:-1], [])}


# 2) Variables Data Layer
vars_now = existing_by_name("variables")


def dlv(name, key, version="2"):
    if name in vars_now:
        print(f"   ↺ var {name}")
        return
    api("POST", f"{WS}/variables", {
        "name": name, "type": "v",
        "parameter": [
            {"type": "integer", "key": "dataLayerVersion", "value": version},
            {"type": "boolean", "key": "setDefaultValue", "value": "false"},
            {"type": "template", "key": "name", "value": key},
        ]})
    print(f"   ✅ var {name}  (dataLayer '{key}', v{version})")


print("VARIABLES:")
dlv("DLV - ecommerce", "ecommerce", "2")
dlv("DLV - cantidad", "cantidad", "2")

# 3) Triggers customEvent
EVENTS = ["view_item", "add_to_cart", "begin_checkout", "add_payment_info", "purchase", "grupo_grande"]
trg_now = existing_by_name("triggers")
trigger_id = {}
print("TRIGGERS:")
for ev in EVENTS:
    tname = f"CE - {ev}"
    if tname in trg_now:
        trigger_id[ev] = trg_now[tname]["triggerId"]
        print(f"   ↺ trigger {tname} (id {trigger_id[ev]})")
        continue
    t = api("POST", f"{WS}/triggers", {
        "name": tname, "type": "customEvent",
        "customEventFilter": [{
            "type": "equals",
            "parameter": [
                {"type": "template", "key": "arg0", "value": "{{_event}}"},
                {"type": "template", "key": "arg1", "value": ev},
            ]}]})
    trigger_id[ev] = t["triggerId"]
    print(f"   ✅ trigger {tname} (id {t['triggerId']})")

# 4) Tags GA4 Event
tags_now = existing_by_name("tags")
print("TAGS:")


def ga4_tag(name, event_name, trigger, ecommerce=True, params=None):
    if name in tags_now:
        print(f"   ↺ tag {name}")
        return
    parameter = [
        {"type": "boolean", "key": "sendEcommerceData", "value": "true" if ecommerce else "false"},
        {"type": "template", "key": "eventName", "value": event_name},
        {"type": "template", "key": "measurementIdOverride", "value": GA4},
    ]
    if ecommerce:
        parameter.insert(1, {"type": "template", "key": "ecommerceMacroData", "value": "{{DLV - ecommerce}}"})
    if params:
        parameter.append({"type": "list", "key": "eventParameters", "list": params})
    api("POST", f"{WS}/tags", {
        "name": name, "type": "gaawe", "parameter": parameter,
        "firingTriggerId": [trigger], "tagFiringOption": "oncePerEvent"})
    print(f"   ✅ tag {name}  (event {event_name})")


for ev in ["view_item", "add_to_cart", "begin_checkout", "add_payment_info", "purchase"]:
    ga4_tag(f"GA4 EC - {ev}", ev, trigger_id[ev], ecommerce=True)

ga4_tag("GA4 - grupo_grande", "grupo_grande", trigger_id["grupo_grande"], ecommerce=False,
        params=[{"type": "map", "map": [
            {"type": "template", "key": "name", "value": "cantidad"},
            {"type": "template", "key": "value", "value": "{{DLV - cantidad}}"}]}])

# 5) Verificación: leer de vuelta el tag purchase
print("\n=== VERIFICACIÓN (tag purchase tal como quedó en GTM) ===")
for t in api("GET", f"{WS}/tags").get("tag", []):
    if t["name"] == "GA4 EC - purchase":
        print(json.dumps(t["parameter"], indent=2, ensure_ascii=False))

print(f"\nWorkspace de revisión:\n  https://tagmanager.google.com/#/container/{WS}")
print("⚠️  NADA publicado todavía. Revisar y luego publicar.")
