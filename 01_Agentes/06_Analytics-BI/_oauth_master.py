#!/usr/bin/env python3
"""OAuth maestro: una sola autorización para TODOS los scopes de Google que sirven.
Levanta servidor loopback, captura el code, intercambia por refresh_token y lo guarda.
No expone secretos en logs."""
import os, sys, json, time, urllib.parse, threading, http.server, requests
from pathlib import Path
from dotenv import load_dotenv

ENV = Path(__file__).parent / ".env"
load_dotenv(ENV)
CID = os.getenv("GOOGLE_ADS_CLIENT_ID")
SEC = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
PORT = 8765
REDIRECT = f"http://localhost:{PORT}/"

SCOPES = [
    "https://www.googleapis.com/auth/adwords",
    "https://www.googleapis.com/auth/datamanager",
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/tagmanager.edit.containers",
    "https://www.googleapis.com/auth/tagmanager.publish",
    "https://www.googleapis.com/auth/cloud-platform",
]

auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": CID, "redirect_uri": REDIRECT, "response_type": "code",
    "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent",
    "include_granted_scopes": "true",
})

print("=" * 70)
print("ABRE ESTE LINK EN TU NAVEGADOR (sesión dueña de la cuenta Google Ads/GA4):")
print("URL_OAUTH>>>", auth_url)
print("=" * 70, flush=True)

result = {}


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):  # silenciar
        pass

    def do_GET(self):
        q = urllib.parse.urlparse(self.path).query
        params = dict(urllib.parse.parse_qsl(q))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        if "code" in params:
            result["code"] = params["code"]
            self.wfile.write("<h2>✅ Listo. Ya puedes cerrar esta pestaña y volver al chat.</h2>".encode())
        else:
            self.wfile.write(f"<h2>Error: {params}</h2>".encode())


srv = http.server.HTTPServer(("localhost", PORT), H)
threading.Thread(target=srv.handle_request, daemon=True).start()

print("Esperando autorización (hasta 5 min)…", flush=True)
for _ in range(300):
    if "code" in result:
        break
    time.sleep(1)

if "code" not in result:
    print("TIMEOUT: no llegó el code. Reintenta.", flush=True)
    sys.exit(1)

tok = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CID, "client_secret": SEC, "code": result["code"],
    "grant_type": "authorization_code", "redirect_uri": REDIRECT}, timeout=30).json()

if "refresh_token" not in tok:
    print("ERROR en intercambio:", json.dumps(tok)[:400], flush=True)
    sys.exit(1)

rt = tok["refresh_token"]
# guardar/reemplazar en .env
lines = ENV.read_text().splitlines()
lines = [l for l in lines if not l.startswith("GOOGLE_MASTER_REFRESH_TOKEN=")]
lines.append(f"GOOGLE_MASTER_REFRESH_TOKEN={rt}")
ENV.write_text("\n".join(lines) + "\n")

# verificar scopes concedidos (sin exponer el token)
info = requests.get("https://oauth2.googleapis.com/tokeninfo",
                    params={"access_token": tok["access_token"]}, timeout=20).json()
print("OAUTH_OK>>> scopes concedidos:", info.get("scope"), flush=True)
print("Refresh token maestro guardado en .env como GOOGLE_MASTER_REFRESH_TOKEN.", flush=True)
