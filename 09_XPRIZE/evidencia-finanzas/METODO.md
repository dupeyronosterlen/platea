# Método Stripe → Devpost (15 ago 2026)

Fuente: `unified_payments.csv` (Stripe Payments, Live). **CSV con PII: no se versiona.**

Ventana: **19 may 2026 – 15 ago 2026** (periodo del hackathon; agosto se actualiza al submit).

## Qué cuenta

- Status `Paid` o `Refunded`. Neto = Amount − Amount Refunded.
- `Failed` / `requires_payment_method` / `processing` = $0.
- Pruebas del founder (emails Dupeyrón / El Gorila) casi todas **reembolsadas** → neto $0.

## Related-party (sacado del Total Revenue)

| Qué | Neto MXN | Por qué |
|-----|----------|---------|
| QA founder no reembolsada (7 jul, PRUEBA99 $10) | 10 | Equipo |
| Cupón “Amigos de producción” (1 ago, 2 boletos) | 400 | Relación de producción |
| Resto de pruebas QA | 0 | Reembolsadas |

**No metí** a related-party (salvo que Dirección lo pida): 2 compradores que también estaban en la lista S1 ($2,145 MXN / ~$124 USD). No son familia. El FAQ de XPRIZE habla de “pre-existing customer relationships” — son recompra de la **obra**, no clientes viejos de Platea. Van en el Total con nota.

Función prensa 18 jul: hay cargos de $10 y $20 de terceros (precio especial de esa función). Son pagos reales; entran al Total al peso de Stripe.

## FX

| Mes | Tasa MXN/USD | Fuente |
|-----|----------------|--------|
| Jun 30 | 17.468 | Frankfurter (cierre; Banxico FIX de ese día no se bajó en esta sesión) |
| Jul 31 | 17.3288 | Banxico FIX |
| Ago 14 | 17.0218 | Banxico FIX (15 ago inhábil) |

Mayo: $0 (no aplica tasa).

## Pegar en Devpost (arms-length)

Ver números en `expediente/03-finanzas-rendicion.md`. Actualizar agosto si hay más pagos antes del 17 ago.
