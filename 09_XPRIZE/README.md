# 09_XPRIZE — Build with Gemini · Proyecto de submission
> **Dueño: Agente 15 (Arquitecto de Procesos)** — coordina; Dirección aprueba todo lo público.
> **Deadline: 17 agosto 2026, 1:00 PM PT** · Premio $2M USD
> Creado 10 jul 2026. Detalle histórico: `memory/project_hackathon_xprize.md` y CLAUDE.md §13.

## Qué se entrega (checklist)

- [ ] **C1 — Repo público GitHub** con el código de la agencia (sanitizado: sin tokens, sin PII, sin `privado/`)
- [ ] **C3 — Video demo < 3 min**, público en YouTube/Vimeo → guion: `guion-video-demo.md`
- [ ] **Formulario de submission** XPRIZE
- [x] **Evidencia continua** de agentes operando con dinero real → `evidencia.md` (YA acumulándose sola desde 9 jul)

## La historia que contamos (elevator pitch)

**Platea**: una agencia de marketing teatral operada por agentes de IA (Gemini 2.5 Pro en Vertex AI)
que vende boletos reales de una obra real — *El Gorila*, 37 años en cartelera, Teatro Wilberto Cantón,
CDMX — con dinero real y un solo humano en el loop.

Prueba viva (todo verificable):
- Media Buyer (Ag-03) lee Meta Ads API + boletera propia (Stripe) y calcula CPA real: **$122 MXN vs objetivo $350**
- Funnel Monitor (Ag-06) diagnosticó la fuga exacta del embudo (checkout 2.7% vs benchmark 20%) y a qué agente le toca atacarla
- Corren solos (launchd) cada mañana y reportan por email sin intervención humana
- Bot de WhatsApp (WF-07/n8n) atiende clientes reales en producción
- Toda decisión queda registrada en `config/session_decisions.json` — el "Brain" auditable

## Reglas de este folder

1. Nada de tokens/PII aquí — este folder será público en el repo de GitHub.
2. Todo screenshot/log de evidencia se indexa en `evidencia.md` con fecha.
3. El guion del video se versiona en `guion-video-demo.md` — Dirección aprueba versión final.

## Pendientes en orden

1. Grabar material la noche de la función de prensa (18 jul) y el estreno (25 jul)
2. Decidir cuenta GitHub y crear repo (Dirección) → Ag-13/Claude Code sanitiza y sube
3. Ensamblar video (Ag-08 Productor Audiovisual) con el guion aprobado
4. Screenshots de dashboards (Meta, Stripe, emails automáticos) → `evidencia/`
5. Submission form — última semana de julio para no llegar al límite
