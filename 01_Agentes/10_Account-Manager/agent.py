#!/usr/bin/env python3
"""
Agente 10 — Account Manager / Coordinación de Bolos
Platea · El Gorila S2 · jul–sep 2026

Coordina el pipeline de bolos (presentaciones fuera de CDMX o eventos especiales).
Rastrea el estado de cada prospecto, próximas acciones, y deadlines de respuesta.
Trabaja en tándem con Agente 11 (Business Dev) que trae prospectos nuevos.

Uso:
  python agent.py                     → vista de pipeline completo
  python agent.py --pipeline          → tabla de prospectos con estado
  python agent.py --followup          → lista de follow-ups pendientes HOY
  python agent.py --prospecto NOMBRE  → detalle de un prospecto específico
  python agent.py --json              → output JSON para CEO (Agente 00)

REGLA: El agente propone, Dirección aprueba, Dirección hace el contacto.
       NUNCA enviar comunicaciones automáticas sin aprobación explícita.
"""

import os
import sys
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent.parent / "03_Media-Buyer" / ".env"
load_dotenv(ENV_PATH)

GCP_PROJECT = os.getenv("GCP_PROJECT", "agencia-mkt-ia")

# ─── PIPELINE FILE ───────────────────────────────────────────────────────────
# El pipeline vive en un archivo YAML/JSON externo para persistencia entre ejecuciones.
# Si no existe, se crea con ejemplo vacío.
PIPELINE_FILE = Path(__file__).parent / "pipeline.json"

ESTADOS_VALIDOS = [
    "nuevo",           # recién identificado por Ag11
    "contacto_inicial", # primer mensaje enviado
    "en_conversacion", # respondió, hay diálogo activo
    "propuesta_enviada", # Dirección mandó la propuesta de caché/condiciones
    "negociacion",     # discutiendo términos
    "confirmado",      # fechas y condiciones acordadas ✅
    "descartado",      # no se concretó (sin delete — solo marcar)
]

PIPELINE_EXAMPLE = {
    "prospectos": [
        {
            "id": "P001",
            "nombre": "Festival de Teatro Monterrey",
            "ciudad": "Monterrey",
            "contacto": "Por investigar",
            "estado": "nuevo",
            "fecha_primer_contacto": None,
            "ultima_interaccion": None,
            "proxima_accion": "Identificar programador del festival",
            "fecha_limite_accion": None,
            "notas": "Identificado por Agente 11. Aforo aprox 300.",
            "cache_cotizado": None,
            "fuente": "Agente 11 Business Dev",
        }
    ]
}


def load_pipeline() -> dict:
    if PIPELINE_FILE.exists():
        with open(PIPELINE_FILE) as f:
            return json.load(f)
    # Crear pipeline vacío con ejemplo
    save_pipeline(PIPELINE_EXAMPLE)
    return PIPELINE_EXAMPLE


def save_pipeline(data: dict):
    with open(PIPELINE_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def run_pipeline() -> str:
    hoy = datetime.date.today()
    data = load_pipeline()
    prospectos = data.get("prospectos", [])

    if not prospectos:
        return "Pipeline vacío — Agente 11 Business Dev aún no ha traído prospectos."

    # Agrupar por estado
    por_estado = {}
    for p in prospectos:
        e = p.get("estado", "nuevo")
        por_estado.setdefault(e, []).append(p)

    lines = [
        f"\n╔══════════════════════════════════════════════════════════════════╗",
        f"║  AGENTE 10 — PIPELINE DE BOLOS · {hoy}                         ║",
        f"╚══════════════════════════════════════════════════════════════════╝\n",
        f"Total prospectos: {len(prospectos)}",
        f"Confirmados:      {len(por_estado.get('confirmado', []))}",
        f"En conversación:  {len(por_estado.get('en_conversacion', [])) + len(por_estado.get('propuesta_enviada', [])) + len(por_estado.get('negociacion', []))}",
        f"Nuevos (sin contacto): {len(por_estado.get('nuevo', []) + por_estado.get('contacto_inicial', []))}",
    ]

    for estado in ESTADOS_VALIDOS:
        grupo = por_estado.get(estado, [])
        if not grupo:
            continue
        lines.append(f"\n── {estado.upper()} ({len(grupo)}) ──────────────────────")
        for p in grupo:
            alerta = ""
            if p.get("fecha_limite_accion"):
                try:
                    deadline = datetime.date.fromisoformat(str(p["fecha_limite_accion"]))
                    delta = (deadline - hoy).days
                    if delta < 0:
                        alerta = " 🔴 VENCIDO"
                    elif delta <= 2:
                        alerta = f" 🟡 {delta}d"
                except Exception:
                    pass
            cache_txt = f" · ${p['cache_cotizado']:,}" if p.get("cache_cotizado") else ""
            lines.append(
                f"  [{p['id']}] {p['nombre']} — {p.get('ciudad', '?')}{cache_txt}{alerta}"
            )
            if p.get("proxima_accion"):
                lines.append(f"        → {p['proxima_accion']}")

    lines.append(
        f"\nEjecutar 'python agent.py --followup' para ver acciones pendientes de hoy."
    )
    return "\n".join(lines)


def run_followup() -> str:
    hoy = datetime.date.today()
    data = load_pipeline()
    prospectos = data.get("prospectos", [])

    urgentes = []
    for p in prospectos:
        if p.get("estado") == "descartado" or p.get("estado") == "confirmado":
            continue
        if p.get("fecha_limite_accion"):
            try:
                deadline = datetime.date.fromisoformat(str(p["fecha_limite_accion"]))
                if deadline <= hoy + datetime.timedelta(days=3):
                    urgentes.append((deadline, p))
            except Exception:
                pass
        # Si lleva >7 días sin interacción y no tiene deadline
        elif p.get("ultima_interaccion"):
            try:
                ultima = datetime.date.fromisoformat(str(p["ultima_interaccion"]))
                if (hoy - ultima).days > 7 and p.get("estado") in ["en_conversacion", "propuesta_enviada"]:
                    urgentes.append((hoy, p))
            except Exception:
                pass

    if not urgentes:
        return f"\n✅ Sin follow-ups urgentes hoy ({hoy}). Pipeline al día.\n"

    urgentes.sort(key=lambda x: x[0])
    lines = [
        f"\n╔══════════════════════════════════════════════════════════════════╗",
        f"║  AGENTE 10 — FOLLOW-UPS PENDIENTES · {hoy}                     ║",
        f"╚══════════════════════════════════════════════════════════════════╝\n",
        f"⚠️  {len(urgentes)} acciones requieren atención\n",
    ]

    for deadline, p in urgentes:
        delta = (deadline - hoy).days
        if delta < 0:
            timing = "VENCIDO"
        elif delta == 0:
            timing = "HOY"
        elif delta <= 3:
            timing = f"en {delta} días"
        else:
            timing = f"antes de {deadline}"

        lines.append(f"  [{p['id']}] {p['nombre']} ({p.get('ciudad', '?')}) — {timing}")
        lines.append(f"       Estado: {p.get('estado', '?')}")
        lines.append(f"       Acción: {p.get('proxima_accion', 'Definir siguiente paso')}")
        lines.append(f"       Contacto: {p.get('contacto', 'Sin contacto registrado')}")
        if p.get("notas"):
            lines.append(f"       Notas: {p['notas'][:80]}...")
        lines.append("")

    lines.append("ℹ️  Recuerda: Dirección aprueba ANTES de enviar cualquier mensaje.")
    return "\n".join(lines)


def run_prospecto(nombre: str) -> str:
    data = load_pipeline()
    prospectos = data.get("prospectos", [])
    encontrado = None
    for p in prospectos:
        if nombre.lower() in p.get("nombre", "").lower() or nombre == p.get("id", ""):
            encontrado = p
            break

    if not encontrado:
        return f"\nProspecto '{nombre}' no encontrado en el pipeline.\n"

    hoy = datetime.date.today()
    return f"""
╔══════════════════════════════════════════════════════════════════╗
║  [{encontrado['id']}] {encontrado['nombre']:<52}║
╚══════════════════════════════════════════════════════════════════╝

Ciudad:         {encontrado.get('ciudad', 'No especificada')}
Contacto:       {encontrado.get('contacto', 'Por identificar')}
Estado:         {encontrado.get('estado', 'nuevo')}
Fuente:         {encontrado.get('fuente', 'Manual')}

TIMELINE
  Primer contacto:       {encontrado.get('fecha_primer_contacto', 'Pendiente')}
  Última interacción:    {encontrado.get('ultima_interaccion', 'N/A')}
  Límite próxima acción: {encontrado.get('fecha_limite_accion', 'Sin deadline')}

COTIZACIÓN
  Caché cotizado: {f"${encontrado['cache_cotizado']:,} MXN" if encontrado.get('cache_cotizado') else 'No cotizado aún'}
  (Referencia interna: $25,000 CDMX · $50,000 exterior — solo Dirección fija precio)

PRÓXIMA ACCIÓN
  {encontrado.get('proxima_accion', 'Definir siguiente paso')}

NOTAS
  {encontrado.get('notas', 'Sin notas.')}

Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | Agente 10 Account-Manager
"""


def run_status() -> str:
    hoy = datetime.date.today()
    data = load_pipeline()
    total = len(data.get("prospectos", []))
    confirmados = sum(1 for p in data.get("prospectos", []) if p.get("estado") == "confirmado")
    return f"""
╔══════════════════════════════════════════════════════════════════╗
║  AGENTE 10 — ACCOUNT MANAGER                                   ║
╚══════════════════════════════════════════════════════════════════╝

ESTADO — {hoy}
  Prospectos en pipeline: {total}
  Confirmados:            {confirmados}

COMANDOS
  python agent.py --pipeline              → vista completa
  python agent.py --followup              → acciones urgentes
  python agent.py --prospecto "Nombre"   → detalle de prospecto
  python agent.py --json                 → datos para Agente 00

PIPELINE FILE: {PIPELINE_FILE}
Para agregar un prospecto: editar pipeline.json directamente
o pedirle a la IA que lo agregue.
"""


def main():
    args = sys.argv[1:]

    if "--pipeline" in args:
        print(run_pipeline())
        return

    if "--followup" in args:
        print(run_followup())
        return

    if "--prospecto" in args:
        idx = args.index("--prospecto")
        nombre = args[idx + 1] if idx + 1 < len(args) else ""
        print(run_prospecto(nombre))
        return

    if "--json" in args:
        data = load_pipeline()
        data["agente"] = "10_Account-Manager"
        data["timestamp"] = datetime.datetime.now().isoformat()
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    print(run_status())


if __name__ == "__main__":
    main()
