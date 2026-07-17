# Evidencia XPRIZE — índice cronológico
> Todo verificable. Actualizar cada vez que haya un artefacto nuevo. Dueño: Ag-15.
> Norma: `04_Operaciones/norma-bitacora.md`

| Fecha | Evidencia | Dónde está |
|-------|-----------|-----------|
| 2026-07-01 | Worker read-only `elgorila-reporte` desplegado para agentes | `taquilla/reporte-worker/index.js` |
| 2026-07-08 | Redistribución presupuesto F2 decidida con datos (CSV → decisión) | `04_Operaciones/backups/session_decisions_preflush_20260716.json` |
| 2026-07-09 | Primer run real Ag-03 vs Meta API: CPA $122 calculado solo | `04_Operaciones/reportes/` + backup session_decisions |
| 2026-07-09 | Ag-06 Funnel Monitor diagnostica fuga checkout (2.7% vs benchmark 20%) | `01_Agentes/06_Analytics-BI/funnel.py` |
| 2026-07-09 | Agencia autónoma: jobs launchd (`com.platea.*`) | logs en `04_Operaciones/reportes/ag*.log` |
| 2026-07-10 | Primer email automático de funnel enviado vía Resend | inbox elgorilateatro@gmail.com |
| 2026-07-11 | Fix ruteo bot WA: If clientes→Asistente verificado (exec #2172) | backup session_decisions + n8n |
| 2026-07-12 | Repo público sanitizado XPRIZE | https://github.com/dupeyronosterlen/platea |
| 2026-07-14 | Campañas Google S2 creadas; Search encendida | Ag-03 + Ads |
| 2026-07-15 | Fix IC solo en click a Stripe (PR #2) + CAPI Purchase vivo | repo `elgorila` |
| 2026-07-15–16 | Meta economía: CORE pausada; PURCHASE activa | Ads Manager + session backup |
| 2026-07-16 | WF-07 migrado a Vertex (créditos XPRIZE) | n8n + scripts/n8n/ |
| 2026-07-16 | Casa XPRIZE unificada (`10` → `09/expediente`) + push `a8ebd12` | https://github.com/dupeyronosterlen/platea |
| 2026-07-16 | Bitácora viva: flush 63 decisiones → `bitacora-sesiones.md`; logger cableado Ag-03/06/12; launchd flush domingo | `04_Operaciones/norma-bitacora.md` |
| 2026-07-16 | Ag-08 teasers←campañas (Meta read-only) | `generar_teasers_desde_campanas.py` + `carteles-s2/propuestas/` |

## Por capturar (screenshots pendientes)
- [ ] Inbox con los emails automáticos de las 8:00/8:05 (varios días seguidos = mejor)
- [ ] Ads Manager con las campañas activas y gasto real
- [ ] Stripe Dashboard con ventas reales
- [ ] Panel admin de la boletera con ocupación
- [ ] n8n con WF-07 (bot WA) ejecutándose con clientes reales
- [ ] Log JSONL de julio tras primer run matutino post-cableado (`04_Operaciones/logs/2026-07.jsonl`)
