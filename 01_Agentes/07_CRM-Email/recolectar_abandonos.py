#!/usr/bin/env python3
"""
Recolector de abandonos de checkout — alimenta la base para C3/C4 (ver registro-comunicaciones.md)
Lee Stripe (llave READ-ONLY) y acumula en privado/abandonos_checkout.csv:
  - Sesiones de checkout expiradas CON email (abandono de carrito)
  - Fichas OXXO sin pagar
NO envía nada. Solo junta. Deduplicado por email (conserva la fecha más reciente).
Programado: diario 8:09 (com.platea.abandonos-diario).
"""
import os, csv, datetime, requests
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE, "01_Agentes", "03_Media-Buyer", ".env"))
K = os.getenv("STRIPE_RESTRICTED_KEY")
AUTH = (K, "")
CSV_PATH = os.path.join(BASE, "privado", "abandonos_checkout.csv")
CAMPOS = ["email", "nombre", "tipo", "monto_mxn", "fecha_ultimo_intento", "enviado_batch"]


def paginar(url, params):
    out = []
    while True:
        r = requests.get(url, params=params, auth=AUTH, timeout=30).json()
        out += r.get("data", [])
        if not r.get("has_more"):
            return out
        params["starting_after"] = out[-1]["id"]


def main():
    desde = int((datetime.datetime.now() - datetime.timedelta(days=45)).timestamp())
    sesiones = paginar("https://api.stripe.com/v1/checkout/sessions",
                       {"limit": 100, "created[gte]": desde})

    nuevos = {}
    for s in sesiones:
        det = s.get("customer_details") or {}
        email = (det.get("email") or "").lower().strip()
        if not email:
            continue
        fecha = datetime.datetime.fromtimestamp(s["created"]).strftime("%Y-%m-%d")
        monto = (s.get("amount_total") or 0) / 100
        tipo = None
        if s["status"] == "expired":
            tipo = "carrito"
        elif s["status"] == "complete" and s.get("payment_status") == "unpaid":
            tipo = "oxxo_sin_pagar"
        elif s.get("payment_status") == "paid":
            # si alguien de la base ya compró, se marca para excluirlo
            tipo = "YA_COMPRO"
        if tipo:
            prev = nuevos.get(email)
            if not prev or fecha > prev["fecha_ultimo_intento"] or tipo == "YA_COMPRO":
                nuevos[email] = {"email": email, "nombre": det.get("name") or "",
                                 "tipo": tipo, "monto_mxn": monto,
                                 "fecha_ultimo_intento": fecha, "enviado_batch": ""}

    # merge con lo existente (conservar marca de enviado)
    base = {}
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH) as f:
            for row in csv.DictReader(f):
                base[row["email"]] = row
    for email, row in nuevos.items():
        if email in base:
            row["enviado_batch"] = base[email].get("enviado_batch", "")
        base[email] = row

    activos = {e: r for e, r in base.items() if r["tipo"] != "YA_COMPRO"}
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        for r in sorted(base.values(), key=lambda x: x["fecha_ultimo_intento"], reverse=True):
            w.writerow(r)
    print(f"✅ Base de abandonos: {len(activos)} recuperables ({sum(1 for r in activos.values() if r['tipo']=='carrito')} carrito, "
          f"{sum(1 for r in activos.values() if r['tipo']=='oxxo_sin_pagar')} OXXO) · {len(base)-len(activos)} ya compraron (excluidos) · {CSV_PATH}")


if __name__ == "__main__":
    main()
