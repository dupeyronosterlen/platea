## Inspiration

I’m Dirección Dupeyrón. My father, Humberto, has performed the same Kafka monologue—*El Gorila*—in Mexican theaters for 37 years. This season we’re in a 325-seat house in Mexico City. I produce. He acts. There is no marketing department, no agency retainer, and no budget that looks like a Silicon Valley SaaS deck.

What we *do* have is a real problem: sell tickets without burning money, and know—honestly—whether the ads are working. Not “platform-reported purchases.” Tickets paid for in our own box office.

That’s why I built **Platea**: an AI-operated marketing agency for live theater. Gemini agents do the daily work of media buying, analytics, PR drafting, and ops. I stay in the loop for anything public or irreversible. One human. Real revenue. Real stage.

*(AdPilot is the media-buying layer inside Platea—Meta and Google agents—not a separate product.)*

## What it does

Platea runs the marketing stack for *El Gorila* Season 2:

- **Media Buyer agent** pulls Meta (and Google) spend, crosses it with **real box-office sales** from our Stripe checkout, and computes CPA against a hard ceiling ($350 MXN per purchase). If CPA blows past the kill threshold, it alerts—no vanity dashboards.
- **Funnel Monitor** found our real leak: people reached checkout but didn’t convert (far below a healthy benchmark). That diagnosis came from live APIs, not a slide.
- **WhatsApp bot** (n8n + Vertex/Gemini) answers real customers about dates, prices, and the show—while a CEO path escalates to me.
- **PR agent** drafts press pitches; with my explicit “go,” we send them (Resend). Presskit, UTMs, logbook.
- **Ops layer**: scheduled jobs every morning (CPA check, occupancy, funnel email), a decision logbook for the hackathon, and a sanitized public repo of the agency.

The product isn’t “another ads autopilot.” It’s an **agency that already has a client in production**—us—and a theater filling seats.

## How we built it

Stack in production:

- **Google Cloud / Vertex AI — Gemini** for agent reasoning (CEO, assistants, PR, analysis).
- **Meta Marketing API** + **Google Ads API** for spend and campaign reality.
- **Cloudflare Workers + Stripe** for our own ticketing (no Ticketmaster middleman).
- **n8n** for WhatsApp workflows; **Resend** for transactional and ops email.
- **Python agents** with launchd jobs so the agency wakes up without me opening a laptop.
- Public evidence repo: [github.com/dupeyronosterlen/platea](https://github.com/dupeyronosterlen/platea)

**What is new for this hackathon (after May 19, 2026):** Platea itself—the agent roster, autonomy rules, CPA-as-truth loop, funnel monitor, decision logbook, Vertex migration for the bot, PR send path, Graphify knowledge graph for the agency.

**What pre-existed (declared honestly):** the show, the venue relationship, and the ticketing website. *El Gorila* is the **customer / proof**, not the Project. We say that out loud so judges aren’t guessing.

## Challenges we ran into

1. **Attribution lies.** Ad platforms love optimistic conversion counts. We forced every serious decision through **box-office CPA**. That meant building reporting Workers, snapshots, and the discipline to pause spend when reality disagreed with the dashboard.

2. **“Autonomous” vs responsible.** Theater is reputation. Golden rule: I approve before anything public goes out. Agents propose, alert, draft, and execute *within* guardrails. Full autopilot that tweets nonsense would kill the brand faster than a high CPA.

3. **SSL, tokens, and Tuesday night ops.** On this Mac, Python HTTPS sometimes dies; we learned to route critical calls through `curl`. Google tokens expire. WhatsApp OTP stalls approval workflows. Production AI is 40% models and 60% boring reliability.

4. **Language and packaging for XPRIZE.** We built in Spanish for a Mexican audience. The submission must speak English. Translating without flattening the story—father, Kafka, 37 years, 325 seats—is its own craft.

5. **Not looking like every other “AI for Meta Ads” demo.** The crowded pitch is AdPilot-in-a-vacuum. Our edge is **Gemini agents operating a real agency with real ticket revenue**. That’s harder to fake and harder to ignore.

## What we learned

- Gemini is strongest when it has **tools + a ledger**: APIs, a kill rule on CPA, and a written decision trail.
- Small cultural businesses don’t need another dashboard. They need something that **sells** and tells the truth about cost.
- Human-in-the-loop isn’t a weakness for this prize track—it’s how you ship AI into a business that can’t afford a scandal.

## What’s next

Finish Season 2 with the agents running. Package Stripe revenue (arms-length vs related-party, cleanly), ship the &lt;3 min demo video, and keep morning jobs + logs as continuous proof that AI is live—not a weekend prototype.

If Platea works for a 37-year monologue in Mexico City, it can work for other independent productions that will never afford a traditional agency.

---

**Built with:** Python · Gemini (Vertex AI) · Google Cloud · Meta Marketing API · Google Ads API · Cloudflare Workers · Stripe · n8n · Resend
