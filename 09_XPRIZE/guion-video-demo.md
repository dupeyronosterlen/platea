# Guion — Video demo XPRIZE (< 3 min) · v0.1 borrador
> Dueño: Ag-15 coordina · Ag-08 produce · Dirección aprueba. 10 jul 2026.
> Regla: todo lo que se muestra debe ser REAL y verificable. Cero mockups.

## Estructura (2:45 target)

**0:00–0:20 — El problema (Dirección a cámara o voz + teatro vacío)**
"Una obra con 37 años en cartelera. Un teatro de 325 butacas. Cero equipo de marketing.
Soy el productor, el actor es mi padre, y no hay presupuesto para una agencia."

**0:20–0:45 — La solución (pantalla: CLAUDE.md + roster de agentes)**
"Así que construí Platea: una agencia de marketing completa operada por 16 agentes de IA
sobre Gemini 2.5 Pro. Un solo humano en el loop: yo, para aprobar."

**0:45–1:30 — La demo (pantalla real, sin cortes tramposos)**
1. Email de las 8:00 AM llega solo: reporte del Media Buyer con CPA real ($122 vs objetivo $350)
2. Email de las 8:05: Funnel Monitor señala la fuga exacta (checkout) y qué agente la ataca
3. Terminal: `python funnel.py` en vivo — Meta API + boletera Stripe propia respondiendo
4. `session_decisions.json`: cada decisión de la IA, registrada y auditable

**1:30–2:10 — La prueba de fuego (material función de prensa 18 jul + estreno 25 jul)**
Boletos vendiéndose en la boletera propia. Público real entrando al teatro.
"Cada boleto de esta sala lo vendió un sistema de agentes. CPA medido en taquilla, no en ads."

**2:10–2:45 — El cierre (Dirección + su padre en el escenario vacío)**
"El teatro independiente en México no puede pagar agencias. Ahora no lo necesita.
Platea es replicable para cualquier producción. Esta temporada es la prueba."

## Material a capturar
- [ ] 18 jul: llegada de invitados/prensa, sala, backstage (Ag-08)
- [ ] 25 jul: fila de entrada, butacas ocupadas, aplauso final
- [ ] Screen recordings: emails automáticos llegando, terminal, Ads Manager, Stripe
- [ ] Dirección a cámara: 3 frases del pitch (grabar varias tomas)
