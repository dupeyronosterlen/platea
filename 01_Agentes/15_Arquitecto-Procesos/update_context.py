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
  - CLAUDE.md §0 (ESTADO-VIVO) entre tags <!-- DYNAMIC -->
  - 04_Operaciones/PENDIENTES-MAESTRO.md (resolved/new desde session)
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
MAESTRO_MD = BASE / "04_Operaciones" / "PENDIENTES-MAESTRO.md"

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def ts_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def normalize_session(raw) -> dict | None:
    """session_decisions.json puede ser lista (legacy) o dict con decisions[]."""
    if raw is None:
        return None
    if isinstance(raw, list):
        return {
            "session_date": ts_date(),
            "decisions": raw,
            "resolved_pendientes": [],
            "new_pendientes": [],
        }
    if isinstance(raw, dict):
        if "decisions" not in raw and raw.get("agent"):
            return {
                "session_date": ts_date(),
                "decisions": [raw],
                "resolved_pendientes": [],
                "new_pendientes": [],
            }
        raw.setdefault("decisions", [])
        raw.setdefault("resolved_pendientes", [])
        raw.setdefault("new_pendientes", [])
        return raw
    return None

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

BACKUP_DIR = BASE / "04_Operaciones" / "reportes" / "backups_claude_md"

def backup_claude_md():
    """Guarda una copia con fecha ANTES de escribir — evita perder para siempre
    la narrativa acumulada en §0 si algo en el flush sale mal (incidente 27 jul 2026)."""
    if not CLAUDE_MD.exists():
        return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dest = BACKUP_DIR / f"CLAUDE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    dest.write_text(CLAUDE_MD.read_text(encoding="utf-8"), encoding="utf-8")
    # Quedarse solo con las últimas 40 copias para no acumular basura sin límite
    backups = sorted(BACKUP_DIR.glob("CLAUDE_*.md"))
    for viejo in backups[:-40]:
        viejo.unlink()

def write_claude_md(content: str, dry_run: bool):
    if dry_run:
        print("\n── CLAUDE.md (dry-run, primeros 800 chars del nuevo contenido) ──")
        print(content[:800])
    else:
        backup_claude_md()
        CLAUDE_MD.write_text(content, encoding="utf-8")
        print(f"  ✅ CLAUDE.md actualizado ({ts()})")

# ─────────────────────────────────────────────
# ESTADO EN VIVO (§0)
# ─────────────────────────────────────────────

def build_estado_vivo(current_block: str, ag12_data: dict | None, ag03_data: dict | None) -> str | None:
    """Actualiza §0 de forma ADITIVA — nunca reemplaza ni borra la narrativa
    acumulada manualmente (incidente 27 jul 2026: la versión anterior reconstruía
    la tabla entera desde cero con placeholders "Sin datos" cada vez que Ag-12/
    Ag-03 no respondían, borrando semanas de contexto).

    Si ninguno de los dos agentes devolvió datos, no se toca §0 en absoluto
    (devuelve None) — "sin novedad" no debe verse como "se resetea todo".
    Si hay datos frescos, se agrega una línea nueva de chequeo automático al
    final del bloque existente, dejando todo lo anterior intacto.
    """
    if not ag12_data and not ag03_data:
        return None

    partes = []
    if ag12_data:
        snap = ag12_data.get("snapshot", {}) or {}
        prox = snap.get("proxima_funcion", {}) or {}
        resumen = snap.get("resumen", {}) or {}
        if prox:
            partes.append(f"próxima función {prox.get('fecha', '?')} "
                           f"({prox.get('ocupacion_pct', '?')}% ocupación, "
                           f"{prox.get('dias_restantes', '?')} días)")
        if resumen:
            partes.append(f"ocupación promedio {resumen.get('ocupacion_promedio', '?')}%")
    if ag03_data:
        partes.append(f"CPA ${ag03_data.get('cpa_real', '?')} MXN, "
                       f"gasto semana ${ag03_data.get('gasto_semana', '?')} MXN, "
                       f"semáforo {ag03_data.get('semaforo', '⬜')}")

    linea_nueva = f"| Chequeo automático {ts()} | {'; '.join(partes)} |"
    return current_block.rstrip() + "\n" + linea_nueva

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
        if not isinstance(item, dict):
            # Formato libre (string): no trae "keyword" separado, no se puede
            # tachar automáticamente una línea de §9 — queda registrado igual
            # en la bitácora vía flush_to_bitacora().
            continue
        keyword = _campo(item, "keyword", "id", "titulo")
        nota = _campo(item, "nota", "note", "descripcion")
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
        nuevos_str = "\n".join(
            f"{15 + i}. **{_pendiente_partes(p)[0]}** — {_pendiente_partes(p)[1]}"
            if isinstance(p, dict) else f"{15 + i}. {p}"
            for i, p in enumerate(nuevos)
        )
        bloque = bloque.rstrip() + "\n" + nuevos_str

    return bloque.strip()


def apply_maestro_updates(session: dict | None, content: str) -> str:
    """Marca resueltos y agrega nuevos en PENDIENTES-MAESTRO.md."""
    if not session:
        return content
    nuevos = session.get("new_pendientes", [])
    resueltos = session.get("resolved_pendientes", [])
    if not nuevos and not resueltos:
        return content

    for r in resueltos:
        if not isinstance(r, dict):
            continue
        keyword = _campo(r, "keyword", "id", "titulo")
        nota = _campo(r, "nota", "note", "descripcion")
        if keyword:
            content = re.sub(
                rf"(\*\*#?{re.escape(keyword)}[^|]*\*\*)",
                rf"✅ \1",
                content,
                count=1,
            )
            if nota:
                content = content.replace(f"✅ **#{keyword}", f"✅ **#{keyword}", 1)

    pattern = re.compile(
        r"(<!-- DYNAMIC:REGISTRO-AUTO:START -->)(.*?)(<!-- DYNAMIC:REGISTRO-AUTO:END -->)",
        re.DOTALL,
    )
    match = pattern.search(content)
    if match and nuevos:
        bloque = match.group(2)
        for p in nuevos:
            etiqueta, detalle = _pendiente_partes(p)
            bloque += f"\n- 🆕 **{etiqueta}** — {detalle} ({ts_date()})"
        content = (
            content[:match.start()]
            + match.group(1)
            + bloque
            + match.group(3)
            + content[match.end():]
        )
    return content


# ─────────────────────────────────────────────
# LECTURA TOLERANTE DE PENDIENTES
# Distintas sesiones escriben session_decisions.json con llaves distintas.
# ─────────────────────────────────────────────
def _campo(d, *llaves, default=""):
    """Devuelve el primer valor no vacío entre varias llaves posibles."""
    if not isinstance(d, dict):
        return str(d)
    for k in llaves:
        v = d.get(k)
        if v:
            return str(v)
    return default


def _pendiente_partes(item):
    """(etiqueta, detalle) de un pendiente, venga con el esquema que venga."""
    if not isinstance(item, dict):
        return str(item), ""
    etiqueta = _campo(item, "keyword", "titulo", "id", "text", default="?")
    detalle = _campo(item, "nota", "note", "descripcion", "text")
    if detalle == etiqueta:
        detalle = ""
    dueno = _campo(item, "dueño", "dueno", "owner")
    if dueno:
        detalle = f"{detalle} (dueño: {dueno})".strip()
    return etiqueta, detalle

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
        if isinstance(d, dict):
            agente = d.get("agent", "—")
            topic  = d.get("topic", "—")
            dec    = d.get("decision", "—")
            impact = d.get("impact", "")
            lineas.append(f"- **[{agente}] {topic}:** {dec}")
            if impact:
                lineas.append(f"  *Impacto: {impact}*")
        else:
            lineas.append(f"- {d}")

    for r in session.get("resolved_pendientes", []):
        if isinstance(r, dict):
            etiqueta, detalle = _pendiente_partes(r)
            lineas.append(f"- ✅ RESUELTO: {etiqueta}" + (f" — {detalle}" if detalle else ""))
        else:
            lineas.append(f"- ✅ RESUELTO: {r}")

    for n in session.get("new_pendientes", []):
        if isinstance(n, dict):
            etiqueta, detalle = _pendiente_partes(n)
            lineas.append(f"- 🆕 NUEVO PENDIENTE: {etiqueta}" + (f" — {detalle}" if detalle else ""))
        else:
            lineas.append(f"- 🆕 NUEVO PENDIENTE: {n}")

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
            raw = json.loads(SESSION_JSON.read_text(encoding="utf-8"))
            session = normalize_session(raw)
            n_dec = len(session.get("decisions", [])) if session else 0
            print(f"  📋 session_decisions.json: {n_dec} decisión(es) pendientes de flush")
        except Exception as e:
            print(f"  ⚠️  No se pudo leer session_decisions.json: {e}", file=sys.stderr)

    # ── Modo --session: solo flush ──
    if args.session:
        if session:
            if MAESTRO_MD.exists():
                maestro_content = MAESTRO_MD.read_text(encoding="utf-8")
                updated = apply_maestro_updates(session, maestro_content)
                if updated != maestro_content and not args.dry_run:
                    MAESTRO_MD.write_text(updated, encoding="utf-8")
                    print("  ✅ PENDIENTES-MAESTRO.md actualizado")
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

    # ── Actualizar §0 Estado en vivo (aditivo — ver build_estado_vivo) ──
    match_estado = re.search(
        r"<!-- DYNAMIC:ESTADO-VIVO:START -->(.*?)<!-- DYNAMIC:ESTADO-VIVO:END -->",
        content, re.DOTALL
    )
    bloque_actual = match_estado.group(1).strip() if match_estado else ""
    nuevo_estado = build_estado_vivo(bloque_actual, ag12_data, ag03_data)
    if nuevo_estado is not None:
        content = replace_dynamic_section(content, "ESTADO-VIVO", nuevo_estado)
        print("  ✅ §0 Estado en vivo actualizado (línea agregada, nada borrado)")
    else:
        print("  ℹ️  Ag-12 y Ag-03 sin datos — §0 se deja intacto, no se toca")

    # ── Actualizar PENDIENTES-MAESTRO.md (si hay session data) ──
    if not args.estado and session and MAESTRO_MD.exists():
        maestro_content = MAESTRO_MD.read_text(encoding="utf-8")
        updated = apply_maestro_updates(session, maestro_content)
        if updated != maestro_content:
            if args.dry_run:
                print("  [dry-run] PENDIENTES-MAESTRO.md se actualizaría")
            else:
                MAESTRO_MD.write_text(updated, encoding="utf-8")
            print("  ✅ PENDIENTES-MAESTRO.md actualizado (registro auto)")

    # ── Render vistas registry → maestro (siempre si no dry-run) ──
    render_script = BASE / "scripts" / "pendientes_maestro.py"
    if not args.dry_run and render_script.exists() and MAESTRO_MD.exists():
        import subprocess
        r = subprocess.run(
            [sys.executable, str(render_script), "render"],
            cwd=BASE,
            capture_output=True,
            text=True,
        )
        if r.returncode == 0:
            print("  ✅ Pendientes vistas (hilos/urgencia) renderizadas")
        else:
            print(f"  ⚠️  pendientes_maestro render: {r.stderr or r.stdout}")

    # ── Escribir CLAUDE.md ──
    write_claude_md(content, args.dry_run)

    # ── Flush sesión a bitácora ──
    if session and not args.estado:
        flush_to_bitacora(session, args.dry_run)
        reset_session_json(args.dry_run)

    print(f"\n✅ update_context.py completado ({ts()})\n")

if __name__ == "__main__":
    main()
