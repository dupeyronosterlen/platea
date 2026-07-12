#!/bin/bash
# Construye la copia PÚBLICA sanitizada de Platea (lista blanca) y la escanea.
# Uso: ./build_public_repo.sh [destino]   (default: ./platea-public junto a este script)
# REGLA: si el escaneo final da hits, NO PUBLICAR. Ver sanitizacion-repo.md.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PUB="${1:-$(dirname "$0")/platea-public}"

rm -rf "$PUB"
mkdir -p "$PUB/01_Agentes" "$PUB/taquilla/reporte-worker"

# Agentes: solo código y personas — JAMÁS .env
for d in "$REPO/01_Agentes"/*/; do
  name=$(basename "$d")
  mkdir -p "$PUB/01_Agentes/$name"
  find "$d" -maxdepth 1 \( -name "*.py" -o -name "persona.md" -o -name "playbook.md" \) \
    -exec cp {} "$PUB/01_Agentes/$name/" \; 2>/dev/null || true
done

cp "$REPO/taquilla/reporte-worker/index.js" "$PUB/taquilla/reporte-worker/" 2>/dev/null || true
cp -r "$REPO/09_XPRIZE" "$PUB/09_XPRIZE"
rm -rf "$PUB/09_XPRIZE/platea-public"   # no anidarse a sí mismo
cp "$REPO/09_XPRIZE/README-public.md" "$PUB/README.md" 2>/dev/null || true
find "$PUB" -type d -empty -delete

# Anonimizar: el nombre del fundador no aparece en la copia pública — se usa "Dirección"
find "$PUB" -type f \( -name "*.md" -o -name "*.py" -o -name "*.js" \) -print0 | while IFS= read -r -d '' f; do
  LC_ALL=C sed -i '' -E \
    -e 's/Osterlen Dupeyr[óo]n/Dirección/g' \
    -e 's/Osterlen/Dirección/g' \
    -e 's/[[:<:]]Os[[:>:]]/Dirección/g' \
    "$f"
done

echo "=== ESCANEO DE SECRETOS ==="
if grep -rlE --exclude="build_public_repo.sh" "EAAV|AIzaSy|re_[A-Za-z0-9]{8}|ntn_[0-9]|GOCSPX|QkgV3A|1//0[0-9A-Za-z]|rk_live|sk_live|Bearer [A-Za-z0-9_-]{25}" "$PUB" 2>/dev/null; then
  echo "🔴 HITS ARRIBA — NO PUBLICAR"; exit 1
else
  echo "✅ cero hits — listo para push"
fi
echo "Archivos: $(find "$PUB" -type f | wc -l | tr -d ' ') · Tamaño: $(du -sh "$PUB" | cut -f1)"
