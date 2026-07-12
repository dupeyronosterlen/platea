#!/usr/bin/env python3
"""
update_context.py — Agente 15 · Arquitecto de Procesos
=========================================================
Actualiza secciones dinámicas de CLAUDE.md con datos frescos.

FUENTES:
  - Agente 12 (--json)  → ocupación por función
  - Agente 03 (--json)  → CPA real, presupuesto gastado
  - session_decisions.json → decisiones de la última sesión Cowork/Claude Code

ESCRIBE:
  - CLAUDE.md §0 (ESTADO-VIVO) y §9 (PENDIENTES) entre tags <!-- DYNAMIC -->
  - 04_Operaciones/bitacora-sesiones.md → log histórico de decisiones
  - Resetea session_decisions.json después de flush

USO:
  python update_context.py              # update completo
  python update_context.py --dry-run   # muestra qué cambiaría sin escribir
  python update_context.py --session   # solo flush session_decisions.json → bitácora
  python update_context.py --estado    # solo actualiza §0 Estado en vivo

LLAMADO DESDE n8n:
  WF-02 (Reporte Diario) → último nodo Code → execSync('python update_context.py')
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import re

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE = Path(__file__).parent.parent.parent  # _PARA-AGENCIA/
CLAUDE_MD = BASE / "CLAUDE.md"
AG12_SCRIPT = BASE / "01_Agentes" / "12_Boletera" / "agent.py"
AG03_SCRIPT = BASE / "01_Agentes" / "03_Media-Buyer" / "agent.py"
SESSION_JSON = BASE / "config" / "session_decisions.json"
BITACORA = BASE / "04_Operaciones" / "bitacora-sesiones.md"

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def ts_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def run_agent(script: Path, args: list[str]) -> dict | None:
    """Corre un agente Python y parsea su JSON output."""
    if not script.exists():
        return None
    try:
        result = subprocess.run(
            [sys.executable, str(script)] + args,
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
    except Exception as e:
        print(f"  ⚠️  {script.name}: {e}", file=sys.stderr)
    return None

def replace_dynamic_section(content: str, tag: str, new_body: str) -> str:
    """Reemplaza el contenido entre <!-- DYNAMIC:TAG:START --> y <!-- DYNAMIC:TAG:END -->."""
    start_tag = f"<!-- DYNAMIC:{tag}:START -->"
    end_tag   = f"<!-- DYNAMIC:{tag}:END -->"
    pattern = re.compile(
        rf"{re.escape(start_tag)}.*?{re.escape(end_tag)}",
        re.DOTALL
    )
    replacement = f"{start_tag}\n{new_body.strip()}\n{end_tag}"
    if pattern.search(content):
        return pattern.sub(replacement, content)
    print(f"  ⚠️  Tag DYNAMIC:{tag} no encontrado en CLAUDE.md", file=sys.stderr)
    return content

def read_claude_md() -> str:
    return CLAUDE_MD.read_text(encoding="utf-8")

def write_claude_md(content: str, dry_run: bool):
    if dry_run:
        print("\n── CLAUDE.md (dry-run, primeros 800 chars del nuevo contenido) ──")
        print(content[:800])
    else:
        CLAUDE_MD.write_text(content, encoding="utf-8")
        print(f"  ✅ CLAUDE.md actualizado ({ts()})")

# ─────────────────────────────────────────────
# ESTADO EN VIVO (§0)
# ─────────────────────────────────────────────

def build_estado_vivo(ag12_data: dict | None, ag03_data: dict | None) -> str:
    """Construye la tabla de estado en vivo para §0."""

    now = ts()

    # Ag-12: ocupación
    if ag12_data:
        proxima = ag12_data.get("proxima_funcion", "Sin datos")
        ocupacion = ag12_data.get("resumen_ocupacion", "Sin datos")
        estado_wa = ag12_data.get("alerta_wa", "—")
    else:
        proxima = "Sin datos (Ag-12 no disponible)"
        ocupacion = "Sin datos"
        estado_wa = "Sin datos"

    # Ag-03: CPA y presupuesto
    if ag03_data:
        cpa = f"${ag03_data.get('cpa_real', '?')} MXN"
        presupuesto = f"${ag03_data.get('gasto_semana', '?')} MXN"
        semaforo = ag03_data.get("semaforo", "⬜")
    else:
        cpa = "Sin datos (Ag-03 / `/api/reporte` pendiente)"
        presupuesto = "Sin datos"
        semaforo = "⬜ Sin datos"

    # Estado de infraestructura (estático — actualizar manualmente cuando cambie)
    infra = {
        "WA OTP número oficial": "⚠️ Pendiente de verificación",
        "Gemini CEO (WF-07)": "❌ Bug bypass — pendiente fix Code node",
        "/api/reporte Worker": "🔴 PENDIENTE — bloqueante",
    }
    infra_rows = "\n".join(f"| {k} | {v} |" for k, v in infra.items())

    return f"""## 0. ESTADO EN VIVO
> ⚡ Actualizado por `update_context.py` — no editar manualmente

| Campo | Valor |
|-------|-------|
| Última actualización | {now} |
| Semáforo agencia | {semaforo} |
| CPA real | {cpa} |
| Presupuesto gastado esta semana | {presupuesto} |
| Función próxima | {proxima} |
| Ocupación general | {ocupacion} |
{infra_rows}"""

# ─────────────────────────────────────────────
# PENDIENTES (§9) — actualización de ítems resueltos
# ─────────────────────────────────────────────

def build_pendientes(session: dict | None, current_content: str) -> str:
    """
    Extrae el bloque de pendientes actual y marca como ✅ los ítems resueltos
    que vengan de session_decisions.json.
    Si no hay session data, devuelve el bloque actual sin cambios.
    """
    # Extraer bloque actual entre los tags
    pattern = re.compile(
        r"<!-- DYNAMIC:PENDIENTES:START -->(.*?)<!-- DYNAMIC:PENDIENTES:END -->",
        re.DOTALL
    )
    match = pattern.search(current_content)
    if not match:
        return ""

    bloque = match.group(1)

    if not session or not session.get("resolved_pendientes"):
        return bloque.strip()

    # Marcar resueltos
    for item in session.get("resolved_pendientes", []):
        keyword = item.get("keyword", "")
        nota = item.get("nota", "")
        if keyword:
            # Busca la línea con ese keyword y la marca resuelta
            bloque = re.sub(
                rf"(\d+\. \*\*[^*]*{re.escape(keyword)}[^*]*\*\*)",
                rf"~~\1~~ ✅ {nota} ({ts_date()})",
                bloque
            )

    # Agregar nuevos pendientes si los hay
    nuevos = session.get("new_pendientes", [])
    if nuevos:
        nuevos_str = "\n".join(f"{15 + i}. **{p['titulo']}** — {p['descripcion']}"
                               for i, p in enumerate(nuevos))
        bloque = bloque.rstrip() + "\n" + nuevos_str

    return bloque.strip()

# ─────────────────────────────────────────────
# BITÁCORA DE SESIONES
# ─────────────────────────────────────────────

def flush_to_bitacora(session: dict, dry_run: bool):
    """Appenda las decisiones de sesión al archivo de bitácora."""
    if not session.get("decisions") and not session.get("resolved_pendientes"):
        print("  ℹ️  Sin decisiones para registrar en bitácora.")
        return

    fecha = session.get("session_date", ts_date())
    lineas = [f"\n## Sesión {fecha}\n"]

    for d in session.get("decisions", []):
        agente = d.get("agent", "—")
        topic  = d.get("topic", "—")
        dec    = d.get("decision", "—")
        impact = d.get("impact", "")
        lineas.append(f"- **[{agente}] {topic}:** {dec}")
        if impact:
            lineas.append(f"  *Impacto: {impact}*")

    for r in session.get("resolved_pendientes", []):
        lineas.append(f"- ✅ RESUELTO: {r.get('keyword','?')} — {r.get('nota','')}")

    for n in session.get("new_pendientes", []):
        lineas.append(f"- 🆕 NUEVO PENDIENTE: {n.get('titulo','?')} — {n.get('descripcion','')}")

    entry = "\n".join(lineas) + "\n"

    if dry_run:
        print("\n── bitacora-sesiones.md (dry-run) ──")
        print(entry)
        return

    BITACORA.parent.mkdir(parents=True, exist_ok=True)
    if not BITACORA.exists():
        BITACORA.write_text("# Bitácora de Sesiones — Platea · El Gorila\n\n"
                            "> Log histórico de decisiones y cambios por sesión.\n", encoding="utf-8")
    with open(BITACORA, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"  ✅ Bitácora actualizada ({BITACORA.name})")

def reset_session_json(dry_run: bool):
    """Resetea session_decisions.json después del flush."""
    empty = {
        "session_date": ts_date(),
        "decisions": [],
        "resolved_pendientes": [],
        "new_pendientes": []
    }
    if dry_run:
        print("  ℹ️  session_decisions.json se resetearía (dry-run)")
        return
    SESSION_JSON.parent.mkdir(parents=True, exist_ok=True)
    SESSION_JSON.write_text(json.dumps(empty, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✅ session_decisions.json reseteado")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Agente 15 · update_context")
    parser.add_argument("--dry-run", action="store_true", help="Muestra cambios sin escribir")
    parser.add_argument("--session", action="store_true", help="Solo flush session_decisions → bitácora")
    parser.add_argument("--estado", action="store_true", help="Solo actualiza §0 Estado en vivo")
    args = parser.parse_args()

    print(f"\n🔄 update_context.py — {ts()}")

    # ── Leer session_decisions.json ──
    session = None
    if SESSION_JSON.exists():
        try:
            session = json.loads(SESSION_JSON.read_text(encoding="utf-8"))
            n_dec = len(session.get("decisions", []))
            print(f"  📋 session_decisions.json: {n_dec} decisión(es) pendientes de flush")
        except Exception as e:
            print(f"  ⚠️  No se pudo leer session_decisions.json: {e}", file=sys.stderr)

    # ── Modo --session: solo flush ──
    if args.session:
        if session:
            flush_to_bitacora(session, args.dry_run)
            reset_session_json(args.dry_run)
        else:
            print("  ℹ️  Sin session_decisions.json — nada que hacer.")
        return

    # ── Correr agentes para datos frescos ──
    ag12_data = None
    ag03_data = None

    if not args.estado or True:  # siempre intentar
        print("  🤖 Consultando Agente 12 (Boletera)...")
        ag12_data = run_agent(AG12_SCRIPT, ["--json"])
        if ag12_data:
            print(f"     ✅ Datos: {ag12_data.get('proxima_funcion', '?')}")
        else:
            print("     ⚠️  Ag-12 sin datos (normal si /api/reporte no está listo)")

        print("  🤖 Consultando Agente 03 (Media Buyer)...")
        ag03_data = run_agent(AG03_SCRIPT, ["--check-now", "--json"])
        if ag03_data:
            print(f"     ✅ CPA: ${ag03_data.get('cpa_real','?')}")
        else:
            print("     ⚠️  Ag-03 sin datos (normal si ads pausados o boletera sin /api/reporte)")

    # ── Leer CLAUDE.md ──
    if not CLAUDE_MD.exists():
        print(f"  ❌ CLAUDE.md no encontrado en {CLAUDE_MD}", file=sys.stderr)
        sys.exit(1)

    content = read_claude_md()

    # ── Actualizar §0 Estado en vivo ──
    nuevo_estado = build_estado_vivo(ag12_data, ag03_data)
    content = replace_dynamic_section(content, "ESTADO-VIVO", nuevo_estado)
    print("  ✅ §0 Estado en vivo actualizado")

    # ── Actualizar §9 Pendientes (si hay session data) ──
    if not args.estado:
        nuevo_pendientes = build_pendientes(session, content)
        if nuevo_pendientes:
            content = replace_dynamic_section(content, "PENDIENTES", nuevo_pendientes)
            print("  ✅ §9 Pendientes actualizado")

    # ── Escribir CLAUDE.md ──
    write_claude_md(content, args.dry_run)

    # ── Flush sesión a bitácora ──
    if session and not args.estado:
        flush_to_bitacora(session, args.dry_run)
        reset_session_json(args.dry_run)

    print(f"\n✅ update_context.py completado ({ts()})\n")

if __name__ == "__main__":
    main()
