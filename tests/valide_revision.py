"""VALIDATION revision.py (Vague 8). FAUX=0 : jamais 2 valeurs contradictoires ; remplacement justifié+tracé ; conflit indécidable non tranché."""
from __future__ import annotations
from revision import BaseCroyances, Croyance, NOUVEAU, REMPLACE, GARDE, CONFLIT

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

B = BaseCroyances()
check("première croyance -> NOUVEAU", B.integre(Croyance("dirigeant_X", "Alice", fiabilite=0.6, date=2020)) == NOUVEAU)

# neuf plus fiable + contradictoire -> remplace (avec rétractation tracée)
st = B.integre(Croyance("dirigeant_X", "Bob", fiabilite=0.9, date=2024))
check("nouvelle plus fiable et contradictoire -> REMPLACE", st == REMPLACE)
check("la valeur retenue est la nouvelle (Bob)", B.valeur("dirigeant_X") == "Bob")
check("rétractation tracée au journal", B.journal and B.journal[-1][:3] == ("dirigeant_X", "Alice", "Bob"))
check("jamais deux valeurs tenues (cohérence fonctionnelle)", B.coherente() and B.valeur("dirigeant_X") == "Bob")

# neuf moins fiable et contradictoire -> garde l'ancienne
check("nouvelle moins fiable -> GARDE (ancienne conservée)",
      B.integre(Croyance("dirigeant_X", "Carol", fiabilite=0.3, date=2025)) == GARDE and B.valeur("dirigeant_X") == "Bob")

# même fiabilité, plus récent -> remplace
B.integre(Croyance("prix", 10, fiabilite=0.5, date=2020))
check("même fiabilité mais plus récent -> REMPLACE", B.integre(Croyance("prix", 12, fiabilite=0.5, date=2024)) == REMPLACE)
check("valeur mise à jour vers la plus récente", B.valeur("prix") == 12)

# même fiabilité, même date, valeurs différentes -> CONFLIT indécidable (ne tranche pas au hasard)
B.integre(Croyance("couleur", "rouge", fiabilite=0.5, date=2021))
st2 = B.integre(Croyance("couleur", "bleu", fiabilite=0.5, date=2021))
check("fiabilité ET date égales, valeurs différentes -> CONFLIT (non tranché)", st2 == CONFLIT)
check("en conflit indécidable, on garde l'ancienne (aucune imposée au hasard)", B.valeur("couleur") == "rouge")

# même valeur -> GARDE (pas de contradiction), support renforcé
check("même valeur ré-affirmée -> GARDE", B.integre(Croyance("prix", 12, fiabilite=0.99, date=2025)) == GARDE)

print(f"\n=== valide_revision : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
