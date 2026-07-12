# Sanitización para el repo público — barrido del 10 jul 2026
> Dueño: Ag-15 + Ag-13. **Regla absoluta: este repo Dropbox NUNCA se publica directo.**
> El repo de GitHub será una COPIA CURADA construida con una lista blanca (allowlist).

## Resultado del barrido (grep de patrones de tokens, 10 jul)

**🔴 Archivos con secretos FUERA de `privado/` (no publicables tal cual):**

| Archivo | Qué contiene |
|---|---|
| `00_Empresa/credenciales-api.md` | Todas las credenciales — JAMÁS público |
| `01_Agentes/13_Programador/agent.py` | ⚠️ Token HARDCODEADO en código — además de no publicarse, conviene moverlo a `.env` (deuda de seguridad interna) |
| `01_Agentes/*/.env` (8 archivos) | Tokens Meta, Gemini, Resend, Google, boletera |
| `06_Workflows/SETUP-whatsapp-phone-id.md`, `wf02_reporte_diario.py` | Tokens WA |
| `config/gcp-adc.json` | Credenciales GCP |
| `config/produccion-activa.yaml`, `reporte-semana-0.md`, `setup-n8n-env.sh`, `setup-webhook-meta.sh` | Tokens varios |
| `scripts/n8n/fix_gemini_final.py`, `update_key.py` | API keys |
| `PENDIENTES-OS.md` | Revisar contenido (matchea patrón) |
| `07_CartelesPeter/node_modules/...` | Falso positivo (librería) — igualmente no se publica `node_modules` |

## Estrategia: lista blanca (lo ÚNICO que va al repo público)

```
platea-public/
├── README.md                     ← nuevo, escrito para el jurado
├── 09_XPRIZE/                    ← ya nace limpio (regla del folder)
├── 01_Agentes/                   ← SOLO los .py y persona/playbook .md, SIN .env
│   (verificar uno por uno que no haya tokens hardcodeados — Ag-13 agent.py ya cayó)
├── taquilla/reporte-worker/      ← worker read-only (usa env bindings, verificar)
├── 06_Workflows/*.json           ← exportes n8n SANITIZADOS (quitar credentials/headers)
└── docs/                         ← arquitectura y VIBE, redactados sin IDs de cuentas
```

**Se excluye siempre:** `privado/`, todos los `.env`, `00_Empresa/credenciales-api.md`,
`config/`, `scripts/n8n/`, datos de compradores, y cualquier ID de cuenta publicitaria/pixel
(CLAUDE.md no se publica tal cual — tiene finanzas y IDs; se escribe versión pública).

## Proceso al publicar (Ag-13 + Claude Code, con OK de Dirección)

1. Construir la copia en folder aparte con la lista blanca (script de export, no copy manual)
2. Re-correr este mismo grep sobre la copia → CERO hits antes del primer push
3. Dirección revisa el contenido final → `git init` + push al repo que Dirección decida
4. Cada actualización posterior repite pasos 2-3 (nunca push directo)

## Bonus de seguridad interna (independiente del XPRIZE)

- [ ] Mover token hardcodeado de `01_Agentes/13_Programador/agent.py` a su `.env`
- [ ] Los tokens de Google van a regenerarse (ya expirados) — al regenerar, verificar que solo queden en `.env`
