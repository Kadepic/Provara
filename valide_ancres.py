"""VALIDATION ancres.py (Vague 6). FAUX=0 : source indépendante requise, contradiction détectée, non-circularité."""
from __future__ import annotations
from ancres import BanqueAncres, Incoherence, CONFIRME, CONTREDIT, INCONNU, CIRCULAIRE

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)
def leve(fn, exc):
    try: fn(); return False
    except exc: return True

B = BanqueAncres()
B.ajoute(("capitale", "France"), "Paris", source="Atlas géographique 2020")
check("réponse correcte + source indépendante -> CONFIRME",
      B.verifie(("capitale", "France"), "Paris", source_reponse="Wikidata") == CONFIRME)
check("réponse fausse -> CONTREDIT", B.verifie(("capitale", "France"), "Lyon", source_reponse="Wikidata") == CONTREDIT)
check("pas d'ancre -> INCONNU (rien affirmé)", B.verifie(("capitale", "Xyz"), "Abc") == INCONNU)

# NON-CIRCULARITÉ : réponse issue de la MÊME source que l'ancre -> refus
check("même source que l'ancre -> CIRCULAIRE (auto-corroboration interdite)",
      B.verifie(("capitale", "France"), "Paris", source_reponse="Atlas géographique 2020") == CIRCULAIRE)
check("independante() détecte l'indépendance",
      B.independante("Wikidata", ("capitale", "France")) and not B.independante("Atlas géographique 2020", ("capitale", "France")))

# Source obligatoire + cohérence des ancres
check("ancre sans source -> refus", leve(lambda: B.ajoute(("x",), "y", source=""), ValueError))
check("ré-ajout identique OK (idempotent)", (B.ajoute(("capitale", "France"), "Paris", "Atlas géographique 2020") is B))
check("ancre contradictoire sur la même clé -> Incoherence",
      leve(lambda: B.ajoute(("capitale", "France"), "Marseille", "autre source"), Incoherence))
check("taille cohérente", len(B) == 1)

print(f"\n=== valide_ancres : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
