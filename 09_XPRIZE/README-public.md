# Platea — AI-Operated Theater Marketing Agency

> **XPRIZE "Build with Gemini" submission** · Proof of concept running in production:
> *El Gorila*, a monologue with 37 years on stage, Teatro Wilberto Cantón, Mexico City — real tickets, real money, one human in the loop.

**Platea** es una agencia de marketing teatral operada por 16 agentes de IA (Gemini 2.5 Pro
en Vertex AI). No es un demo: vende boletos reales de una temporada teatral real, con un solo
humano (el productor) aprobando decisiones.

## Qué hace hoy, sola, cada mañana

| Hora | Agente | Función |
|------|--------|---------|
| 8:00 | 03 Media Buyer | Lee Meta Ads API + boletera propia (Stripe) → CPA real → alerta si urge |
| 8:03 | 12 Boletera | Ocupación por función, boletera caída → alerta |
| 8:05 | 06 Analytics | Funnel completo (impresión→click→visita→checkout→compra) → diagnóstico diario |
| dom 8:10 | 03 + Gemini | Reporte semanal con análisis y propuestas |

Resultados verificables (julio 2026): CPA **$122 MXN** vs objetivo $350 · fuga del funnel
identificada por el agente (checkout 2.7% vs benchmark 20%) · campaña de conversión construida
por el agente vía Graph API a partir de sus propios hallazgos.

## Arquitectura (VIBE)

- **V**isión — objetivo único: CPA ≤ $350 medido en taquilla, no en plataformas de ads
- **I**nsumos — identidad, ICP, precios, historia de la obra
- **B**rain — toda decisión queda registrada y auditable (`session_decisions.json`)
- **E**ngine — agentes Python + launchd + n8n + Cloudflare Workers + boletera Stripe propia

## Estructura de este repo

```
01_Agentes/            código y persona de cada agente (sin credenciales)
taquilla/reporte-worker/  worker read-only que alimenta a los agentes
09_XPRIZE/             plan de submission, guion del video, índice de evidencia
```

Las reglas del sistema: el humano aprueba todo lo público; los agentes detectan y proponen;
nada toca la venta en vivo sin aprobación; cada corrida deja bitácora.

— Hecho en CDMX. Teatro independiente + IA.
