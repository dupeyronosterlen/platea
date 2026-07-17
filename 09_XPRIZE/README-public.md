# Platea — AI-Operated Theater Marketing Agency

> **XPRIZE "Build with Gemini" submission** · Proof of concept running in production:
> *El Gorila*, a monologue with 37 years on stage, Teatro Wilberto Cantón, Mexico City — real tickets, real money, one human in the loop.
>
> Status: **live and still being built**. Core loops run every morning; more agents and automations land as the season proves them.

**Platea** is a theater-marketing agency operated by AI agents (Gemini on Vertex AI / Google Cloud).
It is not a slide-deck demo: it sells real tickets for a real season, with one human (the producer) approving what goes public.

> This repository is the **agency brain** (agents + evidence). The live box-office site is separate:
> [elgorilateatro.com.mx](https://elgorilateatro.com.mx) · code: [`dupeyronosterlen/elgorila`](https://github.com/dupeyronosterlen/elgorila).
> Updating *this* repo never deploys the ticket site.

## What runs alone each morning

| Time | Agent | Job |
|------|--------|-----|
| 8:00 | 03 Media Buyer | Meta Ads API + own box office (Stripe) → real CPA → email if urgent |
| 8:03 | 12 Boletera | Occupancy by show; down-detection → alert |
| 8:05 | 06 Analytics | Funnel (impression→click→visit→checkout→purchase) → daily diagnosis |
| Sun 8:10 | 03 + Gemini | Weekly report |
| Sun 8:15 | Graphify | Repo knowledge-graph refresh (AST) |
| Sun 8:20 | Ag-15 | Flush session decisions → readable logbook |

Verifiable results (July 2026): CPA **$122 MXN** vs $350 target · funnel leak found by the agent (checkout 2.7% vs 20% benchmark) · WhatsApp bot in production on Vertex · decision logbook for the hackathon.

## Architecture (VIBE)

- **V**ision — one goal: CPA ≤ $350 measured at the box office, not inside ad platforms
- **I**nputs — identity, ICP, prices, show history
- **B**rain — every decision is logged (`session_decisions` → bitácora)
- **E**ngine — Python agents + launchd + n8n + Cloudflare Workers + Stripe box office

## What's in this repo

```
01_Agentes/              agent code + personas (no credentials, no .env)
taquilla/reporte-worker/ read-only worker that feeds agents
09_XPRIZE/               submission plan, evidence index, sanitization rules
09_XPRIZE/expediente/    Devpost checklist, finance, eligibility, deadlines, official rules
```

Rules: the human approves anything public; agents detect and propose; nothing touches live ticket sales without approval; every run leaves a trail.

— Built in Mexico City. Independent theater + AI.
