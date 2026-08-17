#!/bin/bash
# Construye la copia PÚBLICA sanitizada de Platea (lista blanca) y la escanea.
# Uso: ./build_public_repo.sh [destino]   (default: ./platea-public junto a este script)
# REGLA: si el escaneo final da hits, NO PUBLICAR. Ver sanitizacion-repo.md.
#
# ⛔ Este script NUNCA toca:
#    - el repo de la página/boletera (dupeyronosterlen/elgorila)
#    - Workers Cloudflare de checkout
#    - .env, privado/, credenciales
# Solo escribe en el destino (copia muerta para GitHub platea).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PUB="${1:-$(dirname "$0")/platea-public}"

rm -rf "$PUB"
mkdir -p "$PUB/01_Agentes" "$PUB/taquilla/reporte-worker"

# Agentes: solo código y personas — JAMÁS .env
# Excluye scripts one-shot _*.py (suelen tener paths a privado/ o IDs de ads)
# Excluye limpiar_notion_ceo.py (IDs Notion + teléfono personal)
for d in "$REPO/01_Agentes"/*/; do
  name=$(basename "$d")
  mkdir -p "$PUB/01_Agentes/$name"
  find "$d" -maxdepth 1 \( -name "*.py" -o -name "persona.md" -o -name "playbook.md" \) \
    ! -name "_*" \
    ! -name "limpiar_notion_ceo.py" \
    -exec cp {} "$PUB/01_Agentes/$name/" \; 2>/dev/null || true
done

cp "$REPO/taquilla/reporte-worker/index.js" "$PUB/taquilla/reporte-worker/" 2>/dev/null || true
cp -r "$REPO/09_XPRIZE" "$PUB/09_XPRIZE"
rm -rf "$PUB/09_XPRIZE/platea-public"   # no anidarse a sí mismo
cp "$REPO/09_XPRIZE/README-public.md" "$PUB/README.md" 2>/dev/null || true
find "$PUB" -type d -empty -delete

# Anonimizar: fundador → "Dirección"; teléfonos personales → [REDACTED]
find "$PUB" -type f \( -name "*.md" -o -name "*.py" -o -name "*.js" \) -print0 | while IFS= read -r -d '' f; do
  LC_ALL=C sed -i '' -E \
    -e 's/Osterlen Dupeyr[óo]n/Dirección/g' \
    -e 's/Osterlen/Dirección/g' \
    -e 's/[[:<:]]Os[[:>:]]/Dirección/g' \
    -e 's/5215512037223/[REDACTED]/g' \
    -e 's/5215671311191/[REDACTED]/g' \
    -e 's/\+52[[:space:]]*55[[:space:]]*1203[[:space:]]*7223/[REDACTED]/g' \
    -e 's/\+52[[:space:]]*56[[:space:]]*7131[[:space:]]*1191/[REDACTED]/g' \
    "$f"
done

echo "=== ESCANEO DE SECRETOS ==="
HITS=0
if grep -rlE --exclude="build_public_repo.sh" \
  "EAAV|AIzaSy|ghp_|gho_|re_[A-Za-z0-9]{8}|ntn_[0-9]|GOCSPX|QkgV3A|1//0[0-9A-Za-z]|rk_live|sk_live|sk_test|Bearer [A-Za-z0-9_-]{25}|52155[0-9]{8}|52156[0-9]{8}" \
  "$PUB" 2>/dev/null; then
  HITS=1
fi
if find "$PUB" \( -name '.env' -o -name '*BUYERS*' -o -name 'gcp-adc*' \) | grep -q .; then
  echo "🔴 Archivos prohibidos encontrados"
  HITS=1
fi
if [ "$HITS" -eq 1 ]; then
  echo "🔴 HITS — NO PUBLICAR"; exit 1
else
  echo "✅ cero hits — listo para push a dupeyronosterlen/platea ÚNICAMENTE"
fi
echo "Archivos: $(find "$PUB" -type f | wc -l | tr -d ' ') · Tamaño: $(du -sh "$PUB" | cut -f1)"
echo "⛔ No pushear a elgorila. No desplegar Workers desde aquí."
