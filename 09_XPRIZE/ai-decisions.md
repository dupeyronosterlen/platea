# 5 things AI decided, 1 human approved — Platea / El Gorila S2

> For judges: concrete instances where a Gemini-powered agent made a real operating decision
> from live data, inside a guardrail, with the founder approving only what's irreversible/public.
> Full evidence index: `evidencia.md`. Live rules: `../04_Operaciones/kpis-globales.md` +
> `../01_Agentes/03_Media-Buyer/persona.md`.

## 1. Meta ad spend was silently burning the daily budget at 3-5am with zero conversions
**AI decided:** the Media Buyer agent (`dayparting.py`) analyzed hourly Meta spend via the
`hourly_stats_aggregated_by_advertiser_time_zone` API and found the ad account's timezone is
America/Los_Angeles, not Mexico City — the bidding algorithm was chasing the cheapest CPM at
2-5am CDMX, consuming ~$460 of a $360/day budget in one overnight window with zero purchases,
add-to-carts, or checkouts, and leaving the funnel starved of budget during the evening hours
when the audience actually buys.
**Human approved:** the fix (pause the funnel 2-6am CDMX via two scheduled jobs, `dayparting_state.json`
tracks what it paused so it never re-enables something a human paused for another reason).
Source: `../CLAUDE.md` §14 "Dayparting manual".

## 2. Funnel leak diagnosis: checkout, not ads, was the problem
**AI decided:** the Analytics agent (`funnel.py`) pulled impression→click→visit→checkout→purchase
from Meta + GA4 + the box office API and found the funnel's single leak was at checkout
(2.7% conversion vs a 20% industry benchmark) — ruling out creative, targeting, or landing-page
copy as the cause, which is where a human would normally have started debugging.
**Human approved:** nothing to approve — this is autonomous read-only diagnosis surfaced daily at 8:05am.

## 3. Real CPA vs. the number the automated check was reporting
**AI decided:** cross-referencing Meta + Google + GA4 + Stripe + the box-office KV store, the
agent found the "32 tickets/week" figure used by the automatic CPA calculation included 20
manually-issued admin comps (press tickets, a manual cash sale) that were never ad-driven sales —
inflating the reported CPA downward to $48.76 MXN when the real Stripe-only CPA was $185-215 MXN.
**Human approved:** the corrected number became the one the agency acts on; no autonomous spend
change was made without this correction being surfaced first.

## 4. WhatsApp bot instruction failure — root cause, not symptom
**AI decided:** when the customer-facing WhatsApp bot (Gemini via Vertex AI, n8n) started
answering like a generic assistant instead of following its behavior rules, the agent traced it
to a pagination bug — the Notion-reading node fetched `page_size=100` without paging through a
300+ block source page, so the bot's own conduct instructions were being truncated before they
ever reached the model. Diagnosed and fixed with pagination + a guardrail that fails loudly if
the fetched content is under 2,000 characters, instead of failing silently.
**Human approved:** the page rewrite and the "va" to ship the fix to the production number
customers message. Source: `../CLAUDE.md` §14 "Casa del bot de WhatsApp".

## 5. Google Search budget escalation clock
**AI decided:** the Media Buyer agent runs a live 48-hour clock (`google-cable.yaml` +
`google-cable-state.json`) that only allows a +15% Search budget escalation when CPA stays
≤$250 AND impression share lost to budget is ≥15% AND the account-level CPA band reads ESCALAR —
otherwise it holds. If the founder manually moves the budget in the UI, the clock resets.
**Human approved:** the founder sets the ceiling and can move budget anytime; the agent enforces
the waiting period and the multi-condition check autonomously between founder actions.

---

**What's still human-only, on purpose:** anything public (posts, press sends), and any
single budget move over $1,500/day. That boundary is Regla de Oro #1 — see `../CLAUDE.md` §6.
