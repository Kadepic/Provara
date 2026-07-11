"""VALIDATION blackboard.py (Vague 7). FAUX=0 : provenance obligatoire, append-only, conflit visible, aucune valeur inventée."""
from __future__ import annotations
from blackboard import Blackboard

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)
def leve(fn, exc):
    try: fn(); return False
    except exc: return True

bb = Blackboard()
bb.poste("COP_max", 19.7, source="limite.Carnot", confiance=1.0)
bb.poste("COP_reel", 3.5, source="fiche_produit")
check("lecture d'un sujet posté", bb.dernier("COP_max").valeur == 19.7)
check("provenance conservée", bb.dernier("COP_max").source == "limite.Carnot")
check("sujet non posté -> [] (rien inventé)", bb.lis("inexistant") == [])
check("sujets() liste les topics", bb.sujets() == {"COP_max", "COP_reel"})

# provenance obligatoire
check("poster sans source -> refus", leve(lambda: bb.poste("x", 1, source=""), ValueError))

# append-only + conflit visible pour l'arbitre
bb.poste("gravite", 9.81, source="pendule")
bb.poste("gravite", 9.83, source="capteur_defectueux")
check("append-only : 2 entrées conservées (pas d'écrasement)", len(bb.lis("gravite")) == 2)
check("en_conflit détecte 2 valeurs distinctes", bb.en_conflit("gravite"))
check("valeurs distinctes listées pour arbitrage", set(bb.valeurs("gravite")) == {9.81, 9.83})
check("pas de conflit quand une seule valeur", not bb.en_conflit("COP_max"))

# ── COUCHE ATOMES (Phase 2 axes ①+②) : le tableau parle le contrat d'atome, FAUX=0 à la relecture ──
import atome as A

bb2 = Blackboard()
fait = A.atteste("le COP de Carnot borne tout cycle", A.Portee(A.DOMAINE, "thermodynamique des cycles"),
                 A.Verdict("coherence_physique", True, "2nd principe — borne de Carnot"))
sup = A.suppose("un caloduc au CO2 suffirait ici", A.GENERATIF,
                A.Portee(A.DOMAINE, "candidat non jugé"), 0.4, base="composition plausible, efficacité non jugée")
bb2.poste_atome("cop", fait, source="coherence_physique")
bb2.poste_atome("cop", sup, source="transfert")
bb2.poste("cop", 3.5, source="fiche_produit")   # valeur NUE : jamais relue comme fait

check("poste_atome refuse un non-Atome", leve(lambda: bb2.poste_atome("x", 42, source="s"), ValueError))
check("atomes() ne rend que les atomes (pas la valeur nue)", len(bb2.atomes("cop")) == 2)
check("faits() ne rend QUE le fait (jamais la supposition ni la valeur nue)",
      [e.valeur for e in bb2.faits("cop")] == [fait])
check("suppositions() rend la supposition seule", [e.valeur for e in bb2.suppositions("cop")] == [sup])
check("la confiance de l'entrée = celle de l'atome", bb2.atomes("cop")[1].confiance == 0.4)
check("faits(contexte) respecte la portée : contexte non couvert -> fait NON servi",
      bb2.faits("cop", {"portee": "un autre domaine"}) == [])
check("faits(contexte couvert) sert le fait",
      [e.valeur for e in bb2.faits("cop", {"portee": "thermodynamique des cycles"})] == [fait])

refute = A.refute(sup, "réfuté par mesure : ne tient pas la charge")
bb2.poste_atome("cop", refute, source="veille")
check("un atome RÉFUTÉ n'est jamais un fait relu", all(e.valeur is not refute for e in bb2.faits("cop")))

# durci : un atome MUTÉ (contournement frozen) est filtré à la relecture (défense en profondeur)
mute = A.atteste("fait à corrompre", A.Portee(A.DOMAINE, "test"), A.Verdict("test", True, "trace de test"))
bb2.poste_atome("corrompu", mute, source="test")
object.__setattr__(mute, "confiance", 0.2)      # viole l'invariant FAIT => confiance 1.0
check("un atome corrompu (mutation frozen) n'est JAMAIS relu comme fait", bb2.faits("corrompu") == [])

print(f"\n=== valide_blackboard : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
