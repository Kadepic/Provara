#!/usr/bin/env bash
# VERAX — installation / vérification. VERAX ne dépend QUE de Python 3.10+ (zéro bibliothèque tierce).
set -e
cd "$(dirname "$0")"
echo "──────────────  VERAX : installation  ──────────────"
if ! command -v python3 >/dev/null 2>&1; then
  echo "✗ Python 3 introuvable. Installe Python 3.10+ : https://www.python.org/downloads/"; exit 1
fi
PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
python3 -c 'import sys;sys.exit(0 if sys.version_info[:2]>=(3,10) else 1)' \
  || { echo "✗ Python 3.10+ requis (détecté $PYV)."; exit 1; }
echo "✓ Python $PYV"
echo "✓ Aucune dépendance tierce à installer (VERAX = bibliothèque standard uniquement)"
echo "── Auto-test des moteurs FAUX=0 (sans données ni réseau)…"
python3 verifie_demo.py || { echo "✗ Auto-test échoué."; exit 1; }
echo "── Optionnel (démos polyglottes examples/) :"
for rt in node perl; do command -v $rt >/dev/null 2>&1 && echo "  ✓ $rt" || echo "  · $rt absent (facultatif)"; done
echo ""
echo "✅ VERAX est prêt."
echo "   Démo :        python3 demo_verax.py"
echo "   Lancer l'IA : python3 lance.py    →  http://127.0.0.1:8765"
