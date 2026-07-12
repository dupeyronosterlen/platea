#!/usr/bin/env python3
"""
_crear_ads_s2.py — El Gorila S2
Crea los 7 ads (creativos + anuncios) dentro de cada ad set.
Los ads quedan en PAUSED con imagen placeholder.
→ Tú solo entras a Ads Manager, cambias la imagen/video, listo.

Uso: python3 _crear_ads_s2.py
"""

import os, json, time, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
TOKEN = os.getenv("SYSTEM_USER_ACCESS_TOKEN")
ACT   = "act_389427487828383"
BASE  = "https://graph.facebook.com/v19.0"
URL_BOLETOS = "https://elgorila.mx/boletos"

# ─── IDs de ad sets (todos ya creados) ────────────────────────────────────────
AD_SETS = {
    "AS_A1": "52510309389226",  # → VIDEO: a — Comercial
    "AS_A2": "52510309421626",  # → VIDEO: c — Jaulas
    "AS_A3": "52510312190026",  # → VIDEO: d — Salvajes
    "AS_A4": "52510309478426",  # → VIDEO: e — Feel
    "AS_B1": "52510367492026",  # → VIDEO: b — Público
    "AS_B2": "52510367504226",  # → VIDEO: f — Invitación  (se actualizará si AS-B2 recién creado)
    "AS_C1": "52510367502226",  # → VIDEO: e — Feel
}

# ─── Copy por ad set ──────────────────────────────────────────────────────────
ADS_CONFIG = [
    {
        "key":      "AD_A1",
        "adset_id": AD_SETS["AS_A1"],
        "name":     "AD-A1_Comercial_LAL-Stack",
        "video":    "a — Comercial",
        "angulo":   "UNA SALIDA",
        "copy":     (
            "Una bestia libre en escena.\n\n"
            "37 años de teatro. Un solo hombre. Una sola función sin red de seguridad.\n\n"
            "Humberto Dupeyrón regresa al Teatro Wilberto Cantón con El Gorila.\n"
            "📅 Sábados desde el 18 de julio."
        ),
        "headline": "El Gorila — Una Salida",
        "utm":      "utm_source=facebook&utm_medium=paid&utm_campaign=EG_S2_CORE&utm_content=A1_LAL-Stack",
    },
    {
        "key":      "AD_A2",
        "adset_id": AD_SETS["AS_A2"],
        "name":     "AD-A2_Jaulas_Mujeres",
        "video":    "c — Jaulas",
        "angulo":   "UNA SALIDA",
        "copy":     (
            "¿Cuántas jaulas elegimos nosotros mismos?\n\n"
            "El Gorila te confronta con lo que eres — y con lo que decidiste ser.\n\n"
            "Humberto Dupeyrón en el Teatro Wilberto Cantón.\n"
            "📅 Sábados del 18 de julio al 26 de septiembre."
        ),
        "headline": "El Gorila — Una Salida",
        "utm":      "utm_source=facebook&utm_medium=paid&utm_campaign=EG_S2_CORE&utm_content=A2_Mujeres",
    },
    {
        "key":      "AD_A3",
        "adset_id": AD_SETS["AS_A3"],
        "name":     "AD-A3_Salvajes_Intereses",
        "video":    "d — Salvajes",
        "angulo":   "NO ES UNA FÁBULA",
        "copy":     (
            "No es una fábula. No hay moraleja.\n\n"
            "Solo Humberto Dupeyrón y un espejo enorme apuntando hacia ti.\n\n"
            "El Gorila — Teatro Wilberto Cantón.\n"
            "📅 11 funciones, sábados del 18 julio al 26 septiembre."
        ),
        "headline": "El Gorila — No es una fábula",
        "utm":      "utm_source=facebook&utm_medium=paid&utm_campaign=EG_S2_CORE&utm_content=A3_Interes-Cultural",
    },
    {
        "key":      "AD_A4",
        "adset_id": AD_SETS["AS_A4"],
        "name":     "AD-A4_Feel_Retargeting",
        "video":    "e — Feel",
        "angulo":   "37 AÑOS EN ESCENA",
        "copy":     (
            "37 años en escena. El antes y el ahora.\n\n"
            "Este es el show que esperabas. Humberto Dupeyrón regresa con El Gorila "
            "al Teatro Wilberto Cantón.\n\n"
            "Boletos disponibles — funciones limitadas."
        ),
        "headline": "37 Años en Escena",
        "utm":      "utm_source=facebook&utm_medium=paid&utm_campaign=EG_S2_CORE&utm_content=A4_Retargeting",
    },
    {
        "key":      "AD_B1",
        "adset_id": AD_SETS["AS_B1"],
        "name":     "AD-B1_Publico_Test-Creativos",
        "video":    "b — Público",
        "angulo":   "EL ACLAMADO MONÓLOGO",
        "copy":     (
            "El show que la gente no para de recomendar.\n\n"
            "El Gorila de Humberto Dupeyrón está de regreso en el Teatro Wilberto Cantón.\n\n"
            "📅 11 sábados únicamente — del 18 de julio al 26 de septiembre.\n"
            "Boletos disponibles ahora."
        ),
        "headline": "El Aclamado Monólogo",
        "utm":      "utm_source=facebook&utm_medium=paid&utm_campaign=EG_S2_FLEX&utm_content=B1_Test-Creativos",
    },
    {
        "key":      "AD_B2",
        "adset_id": AD_SETS["AS_B2"],
        "name":     "AD-B2_Invitacion_Urgencia",
        "video":    "f — Invitación",
        "angulo":   "URGENCIA / ESCASEZ",
        "copy":     (
            "Quedan pocas funciones disponibles.\n\n"
            "El Gorila regresa al Teatro Wilberto Cantón por tiempo limitado — 11 sábados únicamente.\n\n"
            "⚡ Asegura tu lugar antes de que se agote."
        ),
        "headline": "Últimas funciones disponibles",
        "utm":      "utm_source=facebook&utm_medium=paid&utm_campaign=EG_S2_FLEX&utm_content=B2_Urgencia",
    },
    {
        "key":      "AD_C1",
        "adset_id": AD_SETS["AS_C1"],
        "name":     "AD-C1_Feel_Nurture-50plus",
        "video":    "e — Feel",
        "angulo":   "37 AÑOS EN ESCENA",
        "copy":     (
            "37 años en escena. Un artista que lo ha dado todo.\n\n"
            "Humberto Dupeyrón regresa con El Gorila al Teatro Wilberto Cantón.\n\n"
            "Una experiencia de teatro que no olvidarás.\n"
            "📅 Sábados del 18 de julio al 26 de septiembre."
        ),
        "headline": "37 Años de Teatro",
        "utm":      "utm_source=facebook&utm_medium=paid&utm_campaign=EG_S2_NURTURE&utm_content=C1_Nurture-50",
    },
]

# ─── Helpers ──────────────────────────────────────────────────────────────────
def get(path, **params):
    params["access_token"] = TOKEN
    r = requests.get(f"{BASE}{path}", params=params, timeout=30)
    return r.json()

def post_json(path, payload):
    payload["access_token"] = TOKEN
    r = requests.post(f"{BASE}{path}", json=payload, timeout=60)
    body = r.json()
    if not r.ok or "error" in body:
        err = body.get("error", {})
        print(f"  FALLA {path}")
        print(f"  code={err.get('code')} sub={err.get('error_subcode')} | {err.get('error_user_title','')}")
        print(f"  msg= {err.get('message', str(body)[:300])}")
        return None
    return body

# ─── 1. Obtener Page ID ────────────────────────────────────────────────────────
print("="*60)
print("1. OBTENIENDO PAGE ID")
print("="*60)
pages_r = get("/me/accounts", fields="id,name")
pages = pages_r.get("data", [])
if not pages:
    print(f"ERROR: No se encontraron páginas. Respuesta: {pages_r}")
    exit(1)
PAGE_ID = pages[0]["id"]
PAGE_NAME = pages[0]["name"]
print(f"  Página: {PAGE_NAME} (ID: {PAGE_ID})")
if len(pages) > 1:
    print(f"  ⚠️  Hay {len(pages)} páginas. Usando la primera. Si no es correcta, edita PAGE_ID en el script.")

# ─── 2. Obtener imagen placeholder ────────────────────────────────────────────
print("\n" + "="*60)
print("2. BUSCANDO IMAGEN PLACEHOLDER")
print("="*60)
imgs_r = get(f"/{ACT}/adimages", fields="hash,name,url", limit="5")
imgs = imgs_r.get("data", [])
if imgs:
    IMG_HASH = imgs[0]["hash"]
    print(f"  Usando imagen existente: {imgs[0].get('name','sin nombre')} → hash {IMG_HASH[:12]}...")
else:
    # Subir imagen desde URL del sitio
    print("  No hay imágenes en la cuenta. Subiendo desde elgorila.mx...")
    upload_r = post_json(f"/{ACT}/adimages", {
        "url": "https://elgorila.mx/img/el-gorila-og.jpg"
    })
    if not upload_r:
        print("  ERROR: No se pudo subir imagen placeholder.")
        print("  Solución: sube manualmente una imagen en Ads Manager y anota su hash.")
        exit(1)
    IMG_HASH = list(upload_r.get("images", {}).values())[0]["hash"]
    print(f"  Imagen subida → hash {IMG_HASH[:12]}...")

# ─── 3. Crear creativos y ads ─────────────────────────────────────────────────
print("\n" + "="*60)
print("3. CREANDO ADS (creativos + anuncios)")
print("="*60)

created_ads = {}

for cfg in ADS_CONFIG:
    key      = cfg["key"]
    adset_id = cfg["adset_id"]
    url_dest = f"{URL_BOLETOS}?{cfg['utm']}"

    print(f"\n  {key} — {cfg['name']}")
    print(f"  Video: {cfg['video']} | Ángulo: {cfg['angulo']}")

    # 3a. Crear ad creative
    creative_payload = {
        "name": f"CREATIVE_{cfg['name']}",
        "object_story_spec": {
            "page_id": PAGE_ID,
            "link_data": {
                "image_hash": IMG_HASH,
                "link": url_dest,
                "message": cfg["copy"],
                "name": cfg["headline"],
                "call_to_action": {
                    "type": "LEARN_MORE",
                    "value": {"link": url_dest}
                }
            }
        }
    }
    creative_r = post_json(f"/{ACT}/adcreatives", creative_payload)
    if not creative_r:
        print(f"  ❌ Fallo al crear creative de {key}")
        continue
    creative_id = creative_r["id"]
    print(f"  Creative OK: {creative_id}")
    time.sleep(0.5)

    # 3b. Crear ad
    ad_payload = {
        "name": cfg["name"],
        "adset_id": adset_id,
        "creative": {"creative_id": creative_id},
        "status": "PAUSED",
    }
    ad_r = post_json(f"/{ACT}/ads", ad_payload)
    if not ad_r:
        print(f"  ❌ Fallo al crear ad {key}")
        continue
    ad_id = ad_r["id"]
    created_ads[key] = ad_id
    print(f"  Ad OK: {ad_id} ✅")
    time.sleep(1)

# ─── 4. Resumen ────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("RESUMEN — ADS CREADOS")
print("="*60)
for k, v in created_ads.items():
    print(f"  {k:<8} = {v}")

print(f"\n{len(created_ads)}/{len(ADS_CONFIG)} ads creados.")

print("""
╔══════════════════════════════════════════════════════════╗
║  SIGUIENTE PASO EN ADS MANAGER                           ║
╠══════════════════════════════════════════════════════════╣
║  AD-A1  →  sube video  a — Comercial                    ║
║  AD-A2  →  sube video  c — Jaulas                       ║
║  AD-A3  →  sube video  d — Salvajes                     ║
║  AD-A4  →  sube video  e — Feel                         ║
║  AD-B1  →  sube video  b — Público                      ║
║  AD-B2  →  sube video  f — Invitación  (PAUSED manual)  ║
║  AD-C1  →  sube video  e — Feel                         ║
╠══════════════════════════════════════════════════════════╣
║  ACTIVAR: Campana A + B (AS-B1) + C                     ║
║  DEJAR PAUSED: AS-B2 hasta función < 70% aforo          ║
╚══════════════════════════════════════════════════════════╝
""")
