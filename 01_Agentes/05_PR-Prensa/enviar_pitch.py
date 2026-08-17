#!/usr/bin/env python3
"""
Ag-05 — Enviar pitch de prensa vía Resend (curl, no urllib).

Por qué curl: en este Mac urllib/requests a veces fallan por SSL de Python;
Resend + curl es el camino estable (mismo patrón que Graphify/Vertex).

Uso:
  # Dry-run (default): muestra payload, NO envía
  python3 enviar_pitch.py --preset canal22
  python3 enviar_pitch.py --preset jornada,timeout,chilango,cartelerateatro,revistacentral,adip

  # Enviar de verdad (requiere --confirm explícito)
  python3 enviar_pitch.py --preset canal22,once,unam --confirm
  python3 enviar_pitch.py --preset jornada,timeout,chilango,cartelerateatro,revistacentral,adip --confirm

  # Custom
  python3 enviar_pitch.py --to a@x.com --cc b@y.com --subject "..." --body-file msg.txt --confirm

Regla de oro #7: el agente/Cursor/bot solo llama esto DESPUÉS de un "va" de Dirección.
Nunca usar boletos@ como from.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENV_CANDIDATES = [
    REPO / "privado" / "credenciales" / ".env",
    REPO / "01_Agentes" / "03_Media-Buyer" / ".env",
    REPO / "01_Agentes" / "12_Boletera" / ".env",
    REPO / "01_Agentes" / "05_PR-Prensa" / ".env",
]
BITACORA = REPO / "03_Producciones" / "el-gorila" / "campanas" / "registro-mails-prensa.md"
TRACKER = REPO / "03_Producciones" / "el-gorila" / "campanas" / "s2-medios-offline-lista.md"

REPLY_TO = "comunicaciones@elgorilateatro.com.mx"
BCC_DEFAULT = ["dupeyronosterlen@gmail.com"]
# Orden: preferir comunicaciones@; fallbacks ya usados con Resend en la agencia
FROM_CANDIDATES = [
    "El Gorila <comunicaciones@elgorilateatro.com.mx>",
    "El Gorila <contacto@elgorilateatro.com.mx>",
    "El Gorila <platea@elgorilateatro.com.mx>",
]

TV_SUBJECT = "Propuesta de nota — El Gorila, 37 años"
TV_BODY = """Buen día,

Les comparto una posible nota cultural: Humberto Dupeyrón interpreta desde 1989 El Gorila (basado en Informe para una Academia de Franz Kafka). Son 37 años con el mismo texto — una de las trayectorias más largas entre un actor y una obra en el teatro mexicano.

Temporada en el Teatro Wilberto Cantón (SOGEM), sábados 18:00, del 25 de julio al 19 de septiembre. Estreno al público: 25 de julio.

Si les interesa cubrirlo o platicar con Humberto, con gusto les mando presskit y fotos. También podemos apartar cortesía de prensa en alguna función de temporada, cuando les acomode.

Presskit: https://elgorilateatro.com.mx/presskit/presskit2026.html

Quedo atento.
Dirección Dupeyrón
Producción El Gorila
comunicaciones@elgorilateatro.com.mx
"""

RADIO_SUBJECT = "Entrevista — Humberto Dupeyrón / El Gorila"
RADIO_BODY = """Buen día,

Les escribo por si les interesa una conversación de trayectoria: Humberto Dupeyrón lleva desde 1989 el monólogo El Gorila (Kafka), 37 años con el mismo texto — una de las trayectorias más largas actor–obra del teatro mexicano.

Está en temporada en el Wilberto Cantón (SOGEM), sábados 18:00, del 25 de julio al 19 de septiembre.

Si les acomoda una entrevista (presencial o remota), con gusto la coordinamos. También hay posibilidad de cortesía de prensa en alguna función de la temporada.

Presskit: https://elgorilateatro.com.mx/presskit/presskit2026.html

Quedo atento.
Dirección Dupeyrón
Producción El Gorila
comunicaciones@elgorilateatro.com.mx
"""

# Roundups de sábado (va Dirección 15 ago 2026) — GPT/Chilango/Time Out leen ESTAS listas, no el sitio.
SABADO_SUBJECT = (
    "Cartelera sábado 22 ago — El Gorila, Humberto Dupeyrón, 18:00 Wilberto Cantón"
)
SABADO_BODY = """Buen día,

Les escribo para pedir un renglón en la cartelera / lista de qué hacer del sábado 22 de agosto.

El Gorila — Humberto Dupeyrón
Monólogo basado en Informe para una academia, de Franz Kafka.
Solo se presenta los sábados a las 18:00 en el Teatro Wilberto Cantón (José María Velasco 59, Col. San José Insurgentes).
37 años en escena. La Jornada lo cubrió el 18 de julio de 2026 (Cultura).
Duración: 1 h 20. General $400. Credencial estudiante/INAPAM/maestro $280.

Próxima función: sábado 22 de agosto, 18:00.
Boletos y fechas: https://elgorilateatro.com.mx/funciones.html?utm_source=prensa&utm_medium=earned&utm_campaign=s2_cartelera_sabado
Presskit: https://elgorilateatro.com.mx/presskit/presskit2026.html

No es el montaje de Brontis Jodorowsky (INBAL, abril–mayo 2026, ya cerrado). Esta es la puesta de Humberto Dupeyrón, en temporada.

Si cubren fin de semana o cartelera teatral, ¿pueden incluirlo ese sábado?

Quedo atento.
Dirección Dupeyrón
Producción El Gorila
comunicaciones@elgorilateatro.com.mx
"""

ADIP_SUBJECT = "Alta manual Cartelera CDMX — El Gorila, sábados 18:00, Wilberto Cantón"
ADIP_BODY = """Buen día,

El botón «Anuncia tu evento aquí GRATIS» de cartelera.cdmx.gob.mx no carga el formulario (lo probamos la producción y la agencia el 28 de julio). Pedimos el alta manual.

Evento: El Gorila — Humberto Dupeyrón
Categoría: Artes escénicas / Teatro (evento de paga, no gratuito)
Basado en Informe para una academia, Franz Kafka
Lugar: Teatro Wilberto Cantón, José María Velasco 59, Col. San José Insurgentes, CP 03900, Benito Juárez, CDMX
Horario: sábados 18:00
Próxima función: sábado 22 de agosto de 2026
Temporada en curso (sábados)
Duración: 80 minutos
Precio: general $400 MXN · estudiante/INAPAM/maestro $280 MXN
Compra: https://elgorilateatro.com.mx/funciones.html
Presskit: https://elgorilateatro.com.mx/presskit/presskit2026.html

Identificar al intérprete: Humberto Dupeyrón. No confundir con el montaje de Brontis Jodorowsky en el CCB (abril–mayo 2026, cerrado).

Quedo atento a formato o materiales que necesiten.

Dirección Dupeyrón
Producción El Gorila
comunicaciones@elgorilateatro.com.mx
"""

# Destinos sacados de sitios oficiales (16 jul 2026) — ver registro-mails-prensa.md
PRESETS: dict[str, dict] = {
    "canal22": {
        "medio": "Canal 22",
        "to": ["comunicacion.social@canal22.org.mx"],
        "cc": ["jaime.mejia@canal22.org.mx"],
        "subject": TV_SUBJECT,
        "text": TV_BODY,
        "fuente": "canal22.org.mx/directorio.html",
    },
    "once": {
        "medio": "Canal Once",
        "to": ["info@canalonce.ipn.mx"],
        "cc": [],
        "subject": TV_SUBJECT,
        "text": TV_BODY,
        "fuente": "canalonce.mx/sobre-canal-once/contacto",
    },
    "unam": {
        "medio": "Radio UNAM",
        "to": ["primermovimientounam@gmail.com"],
        "cc": ["radio@unam.mx"],
        "subject": RADIO_SUBJECT,
        "text": RADIO_BODY,
        "fuente": "radio.unam.mx/preguntas-frecuentes (boletín) + /contacto",
    },
    "jornadasab": {
        "medio": "Cartelera La Jornada",
        "to": ["cartelerajornada@gmail.com"],
        "cc": [],
        "subject": SABADO_SUBJECT,
        "text": SABADO_BODY,
        "fuente": "s2-medios-offline-lista.md §3 (verificado 13 ago)",
    },
    "timeout": {
        "medio": "Time Out México",
        "to": ["ensazu_teatro@yahoo.com.mx"],
        "cc": [],
        "subject": SABADO_SUBJECT,
        "text": SABADO_BODY,
        "fuente": "s2-medios-offline-lista.md §3.6 Enrique Saavedra (Time Out / Cartelera de Teatro)",
    },
    "chilango": {
        "medio": "Chilango",
        "to": ["mayte.vs22@gmail.com"],
        "cc": [],
        "subject": SABADO_SUBJECT,
        "text": SABADO_BODY,
        "fuente": "s2-medios-offline-lista.md §3.6 Mayte Valencia (Chilango / Teatro My Love)",
    },
    "cartelerateatro": {
        "medio": "Cartelera de Teatro (listado)",
        "to": ["oscar@carteleradeteatro.mx"],
        "cc": ["monica@carteleradeteatro.mx"],
        "subject": SABADO_SUBJECT,
        "text": SABADO_BODY,
        "fuente": "canales/cartelera-de-teatro/README.md — Oscar listado general",
    },
    "revistacentral": {
        "medio": "Revista Central",
        "to": ["beatriz.esquivel@revistacentral.mx"],
        "cc": [],
        "subject": SABADO_SUBJECT,
        "text": SABADO_BODY,
        "fuente": "s2-medios-offline-lista.md §3.5",
    },
    "adip": {
        "medio": "Cartelera CDMX / ADIP",
        "to": ["infoadip@cdmx.gob.mx"],
        "cc": [],
        "subject": ADIP_SUBJECT,
        "text": ADIP_BODY,
        "fuente": "canales/cartelera-cdmx/README.md (botón de alta roto 28 jul)",
    },
}


def load_resend_key() -> str:
    for path in ENV_CANDIDATES:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("RESEND_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    env = os.getenv("RESEND_API_KEY", "").strip()
    if env:
        return env
    raise SystemExit("RESEND_API_KEY no encontrada en .env de Ag-03/12/05 ni en $env")


def resend_send(api_key: str, payload: dict) -> tuple[int, dict]:
    """POST /emails vía curl (evita SSL roto de Python en este Mac)."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
        tmp = f.name
    try:
        raw = subprocess.check_output(
            [
                "/usr/bin/curl",
                "-sS",
                "--max-time",
                "60",
                "-w",
                "\n__HTTP__%{http_code}",
                "https://api.resend.com/emails",
                "-H",
                f"Authorization: Bearer {api_key}",
                "-H",
                "Content-Type: application/json",
                "-d",
                f"@{tmp}",
            ],
            text=True,
            timeout=70,
        )
    finally:
        Path(tmp).unlink(missing_ok=True)
    if "__HTTP__" in raw:
        body, _, code_s = raw.rpartition("__HTTP__")
        code = int(code_s.strip() or "0")
    else:
        body, code = raw, 0
    try:
        data = json.loads(body.strip() or "{}")
    except json.JSONDecodeError:
        data = {"raw": body[:500]}
    return code, data


def append_bitacora(entries: list[dict]) -> None:
    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    lines = [
        f"## Envío {stamp}",
        "",
        "- Canal: Resend (`enviar_pitch.py` + curl)",
        f"- BCC: {', '.join(BCC_DEFAULT)}",
        f"- Reply-To: {REPLY_TO}",
        "",
    ]
    for e in entries:
        lines += [
            f"### {e['medio']} — **{e['status']}**",
            f"- To: {', '.join(e['to'])}",
            f"- Cc: {', '.join(e.get('cc') or []) or '—'}",
            f"- From: {e.get('from') or '—'}",
            f"- Asunto: {e['subject']}",
            f"- Resend ID: `{e.get('id') or '—'}`",
            f"- HTTP: {e.get('http')}",
            "",
        ]
        if e.get("error"):
            lines.append(f"- Error: `{e['error'][:400]}`")
            lines.append("")
    block = "\n".join(lines) + "\n"
    if BITACORA.exists():
        BITACORA.write_text(block + "---\n\n" + BITACORA.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        BITACORA.write_text("# Registro mails prensa\n\n" + block, encoding="utf-8")

    if TRACKER.exists():
        summary = "; ".join(f"{e['medio']}={e['status']}" for e in entries)
        note = f"- {stamp}: {summary} — ver registro-mails-prensa.md\n"
        t = TRACKER.read_text(encoding="utf-8")
        if "## Bitácora envíos" not in t:
            TRACKER.write_text(t.rstrip() + "\n\n## Bitácora envíos\n" + note, encoding="utf-8")
        else:
            TRACKER.write_text(t.rstrip() + "\n" + note, encoding="utf-8")


def build_jobs(args: argparse.Namespace) -> list[dict]:
    jobs: list[dict] = []
    if args.preset:
        for raw in args.preset.replace(" ", "").split(","):
            key = raw.lower().replace("-", "").replace("_", "")
            aliases = {
                "22": "canal22",
                "canal22": "canal22",
                "once": "once",
                "unam": "unam",
                "radiounam": "unam",
                "jornada": "jornadasab",
                "jornadasab": "jornadasab",
                "timeout": "timeout",
                "chilango": "chilango",
                "cartelerateatro": "cartelerateatro",
                "cartelera": "cartelerateatro",
                "revistacentral": "revistacentral",
                "central": "revistacentral",
                "adip": "adip",
                "carteleracdmx": "adip",
            }
            k = aliases.get(key) or (raw.lower() if raw.lower() in PRESETS else None)
            if not k or k not in PRESETS:
                raise SystemExit(
                    f"Preset desconocido: {raw}. Usa: canal22, once, unam, "
                    "jornada, timeout, chilango, cartelerateatro, revistacentral, adip"
                )
            p = PRESETS[k]
            jobs.append(
                {
                    "medio": p["medio"],
                    "to": list(p["to"]),
                    "cc": list(p["cc"]),
                    "subject": p["subject"],
                    "text": p["text"],
                }
            )
    if args.to:
        text = args.body or ""
        if args.body_file:
            text = Path(args.body_file).read_text(encoding="utf-8")
        if not text or not args.subject:
            raise SystemExit("--to requiere --subject y (--body o --body-file)")
        jobs.append(
            {
                "medio": args.label or args.to[0],
                "to": args.to,
                "cc": args.cc or [],
                "subject": args.subject,
                "text": text,
            }
        )
    if not jobs:
        raise SystemExit("Nada que enviar: usa --preset canal22,once,unam o --to …")
    return jobs


def main() -> int:
    ap = argparse.ArgumentParser(description="Enviar pitches prensa vía Resend (curl)")
    ap.add_argument("--preset", help="canal22,once,unam (coma-separados)")
    ap.add_argument("--to", nargs="+")
    ap.add_argument("--cc", nargs="*")
    ap.add_argument("--subject")
    ap.add_argument("--body")
    ap.add_argument("--body-file")
    ap.add_argument("--label", help="nombre en bitácora para --to custom")
    ap.add_argument(
        "--confirm",
        action="store_true",
        help="SIN esto solo dry-run. Con esto SÍ envía (tras va de Dirección).",
    )
    ap.add_argument("--from", dest="from_addr", help="forzar from Name <email>")
    args = ap.parse_args()

    jobs = build_jobs(args)
    print(f"Jobs: {len(jobs)} · confirm={args.confirm}")
    for j in jobs:
        print(f"  · {j['medio']} → {j['to']} cc={j.get('cc') or []}")
        print(f"    asunto: {j['subject']}")

    if not args.confirm:
        print("\nDry-run. Para enviar: añade --confirm (solo con va de Dirección).")
        return 0

    key = load_resend_key()
    froms = [args.from_addr] if args.from_addr else list(FROM_CANDIDATES)
    working_from: str | None = None
    results: list[dict] = []

    for j in jobs:
        sent = False
        last_err = ""
        candidates = [working_from] if working_from else froms
        for frm in candidates:
            if not frm:
                continue
            payload = {
                "from": frm,
                "to": j["to"],
                "bcc": BCC_DEFAULT,
                "reply_to": REPLY_TO,
                "subject": j["subject"],
                "text": j["text"],
            }
            if j.get("cc"):
                payload["cc"] = j["cc"]
            code, data = resend_send(key, payload)
            if code in (200, 201) and data.get("id"):
                working_from = frm
                results.append(
                    {
                        **j,
                        "from": frm,
                        "id": data["id"],
                        "http": code,
                        "status": "ENVIADO",
                    }
                )
                print(f"✅ {j['medio']} id={data['id']} from={frm}")
                sent = True
                break
            last_err = json.dumps(data, ensure_ascii=False)[:400]
            print(f"⚠️  {j['medio']} from={frm} http={code} {last_err}")
        if not sent:
            results.append(
                {
                    **j,
                    "from": None,
                    "id": None,
                    "http": None,
                    "status": "FALLÓ",
                    "error": last_err,
                }
            )
            print(f"❌ {j['medio']} no enviado")

    append_bitacora(results)
    print(f"\nBitácora → {BITACORA.relative_to(REPO)}")
    failed = sum(1 for r in results if r["status"] != "ENVIADO")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
