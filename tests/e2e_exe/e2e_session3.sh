#!/bin/bash
# E2E des DERNIÈRES briques (SVO libre, conflits, synonymes têtes, garde alias FAUX=0) sur serveur réel.
URL=http://127.0.0.1:8899/api/message
R=$RANDOM
ok=0; total=0
ask() {
  local conv="$1" q="$2" rep=""
  for i in 1 2 3; do
    rep=$(curl -s -m 120 -X POST "$URL" -H 'Content-Type: application/json' \
      --data "$(python3 -c "import json,sys;print(json.dumps({'id':sys.argv[1],'texte':sys.argv[2]}))" "$conv" "$q")" \
      | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('reponse') or d.get('texte') or '')" 2>/dev/null)
    [ -n "$rep" ] && break
    sleep 4
  done
  echo "$rep"
}
verif() {
  total=$((total+1))
  if echo "$3" | tr '\n' ' ' | grep -qiE "$2"; then ok=$((ok+1)); echo "  ✓ $1"
  else echo "  ✗ $1"; echo "      -> $(echo "$3" | tr '\n' ' ' | head -c 150)"; fi
}
# refus : ne DOIT PAS contenir le motif (FAUX=0)
refus() {
  total=$((total+1))
  if echo "$3" | tr '\n' ' ' | grep -qiE "$2"; then echo "  ✗ $1 (a produit le faux)"; echo "      -> $(echo "$3" | tr '\n' ' ' | head -c 150)";
  else ok=$((ok+1)); echo "  ✓ $1"; fi
}

echo "— parse SVO libre (ordre des mots) —"
verif "du Japon, dis-moi la capitale" "tokyo" "$(ask e3-$R-1 "du Japon, dis-moi la capitale")"
verif "pour le Japon, la monnaie"     "yen"   "$(ask e3-$R-1 "pour le Japon, la monnaie ?")"
verif "Japon : monnaie ?"             "yen"   "$(ask e3-$R-1 "le Japon : monnaie ?")"

echo "— transitif conflits —"
verif "de quelle guerre Marignan"   "cambrai" "$(ask e3-$R-2 "de quelle guerre fait partie la bataille de Marignan ?")"
verif "Tonga -> front Ouest (dériv)" "ouest"  "$(ask e3-$R-2 "de quelle bataille fait partie l'opération Tonga ?")"
verif "vérif Stalingrad front Est"  "oui"     "$(ask e3-$R-2 "est-ce que la bataille de Stalingrad fait partie du front de l'Est ?")"
refus "Marignan PAS guerre Cent Ans" "oui"     "$(ask e3-$R-2 "est-ce que la bataille de Marignan fait partie de la guerre de Cent Ans ?")"

echo "— synonymes de têtes —"
verif "richesse du Japon -> PIB"    "435"  "$(ask e3-$R-3 "quelle est la richesse du Japon ?")"
verif "taille de la France -> superf" "551" "$(ask e3-$R-3 "quelle est la taille de la France ?")"
verif "nombre d'habitants Japon"    "123"  "$(ask e3-$R-3 "le nombre d'habitants du Japon ?")"

echo "— garde FAUX=0 : patron pollué wakanda->france —"
refus "population wakanda != France" "population de la france" "$(ask e3-$R-4 "quelle est la population du wakanda ?")"
verif "wakanda -> abstention struct" "structure|compris|même chose|abstiens"      "$(ask e3-$R-4 "quelle est la population du wakanda ?")"

echo "— faits stables (non-régression) —"
verif "capitale France intact"      "paris" "$(ask e3-$R-5 "quelle est la capitale de la France ?")"

echo
echo "E2E dernières briques : $ok/$total"
