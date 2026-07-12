# Evidencia XPRIZE — índice cronológico
> Todo verificable. Actualizar cada vez que haya un artefacto nuevo. Dueño: Ag-15.

| Fecha | Evidencia | Dónde está |
|-------|-----------|-----------|
| 2026-07-01 | Worker read-only `elgorila-reporte` desplegado para agentes | `taquilla/reporte-worker/index.js` |
| 2026-07-08 | Redistribución presupuesto F2 decidida con datos (CSV → decisión) | `session_decisions.json` |
| 2026-07-09 | Primer run real Ag-03 vs Meta API: CPA $122 calculado solo | `04_Operaciones/reportes/` + `session_decisions.json` |
| 2026-07-09 | Ag-06 Funnel Monitor diagnostica fuga checkout (2.7% vs 20%) | `01_Agentes/06_Analytics-BI/funnel.py` |
| 2026-07-09 | Agencia autónoma: 3 jobs launchd (`com.platea.*`) | logs en `04_Operaciones/reportes/ag*.log` |
| 2026-07-10 | Primer email automático de funnel enviado vía Resend | inbox elgorilateatro@gmail.com |
| 2026-07-11 | Fix del ruteo del bot WA en vivo: la agencia diagnosticó el bug leyendo la DB de n8n (If roto → clientes atendidos por el CEO), guió a Dirección en la corrección y VERIFICÓ inyectando un mensaje sintético de cliente al webhook — ruta Asistente confirmada, precios y estreno correctos | `session_decisions.json` + exec #2172 de n8n |

## Por capturar (screenshots pendientes)
- [ ] Inbox con los emails automáticos de las 8:00/8:05 (varios días seguidos = mejor)
- [ ] Ads Manager con las campañas activas y gasto real
- [ ] Stripe Dashboard con ventas reales
- [ ] Panel admin de la boletera con ocupación
- [ ] n8n con WF-07 (bot WA) ejecutándose con clientes reales
