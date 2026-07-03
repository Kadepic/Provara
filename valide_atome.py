"""VALIDE atome.py — contrat FAUX=0 : invariants, asymétrie par Verdict, anti-glissement, portée conservatrice,
évolutivité + garde anti-blanchiment. Inclut un test de NON-RÉGRESSION par faille reproduite en passe adversariale.
"""
import dataclasses

import atome as A

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


A._reset_gardes()
P_DOM = A.Portee(A.DOMAINE, "Tc>Tf>0")
P_REF = A.Portee(A.REFERENTIEL, "périmètre OIV/SecNumCloud")
V_OK = A.Verdict("test.held_out", True, "42/42 cas passés")
V_KO = A.Verdict("coherence_physique", False, "rendement>1 -> VIOLE")

# ── 1) Portée : condition obligatoire, couvre() EXACT (pas de sous-chaîne) ──
check(leve(A.Portee, A.DOMAINE, ""), "portée sans condition -> ValueError")
check(leve(A.Portee, "galaxie", "x"), "type de portée inconnu -> ValueError")
check(A.Portee(A.UNIVERSEL, "tautologie").couvre({}) is True, "portée universelle couvre tout")
check(P_REF.couvre({"portee": "périmètre OIV/SecNumCloud"}) is True, "portée couvre le contexte qui l'affirme exactement")
check(P_REF.couvre({}) is False, "portée NE couvre PAS un contexte muet")
# FAILLE #1/#8/#11/#15/#19 : sous-chaîne / négation
p_chaud = A.Portee(A.DOMAINE, "chaud")
check(p_chaud.couvre({"conditions": "il fait froid, pas chaud du tout"}) is False, "couvre() : contexte qui NIE la condition -> False (pas de sous-chaîne)")
check(A.Portee(A.REFERENTIEL, "à 1 atm").couvre({"conditions": "5 atm de CO2"}) is False, "couvre() : sous-chaîne str rejetée")
check(p_chaud.couvre({"conditions": ["chaud", "sec"]}) is True, "couvre() : membership exact dans une collection")
check(p_chaud.couvre({"conditions": ["très chaud"]}) is False, "couvre() : pas de sous-chaîne dans une collection")

# ── 2) FAIT via Verdict (asymétrie) ; preuve nue / bool refusés ──
f = A.atteste("eau bout à 100°C", A.Portee(A.DOMAINE, "à 1 atm"), V_OK)
check(f.statut == A.FAIT and f.confiance == 1.0, "atteste(Verdict) -> FAIT")
check(f.est_servable_comme_fait() is True, "un fait est servable comme fait")
# FAILLE #3 : atteste avec une str/preuve nue
check(leve(A.atteste, "x", P_DOM, "preuve nue"), "atteste() sans Verdict (str) -> ValueError")
check(leve(A.atteste, "x", P_DOM, V_KO), "atteste() avec verdict NÉGATIF -> ValueError")
check(leve(A.Atome, "x", A.FAIT, P_DOM, 0.9, "p"), "FAIT direct conf<1 -> ValueError")
check(leve(A.Atome, "x", A.FAIT, P_DOM, 1.0, ""), "FAIT sans preuve -> ValueError")

# ── 3) CONVENTION : référentiel + source ──
c = A.convention("Constitution > loi", "droit français", source="pyramide de Kelsen")
check(c.statut == A.CONVENTION and c.portee.type == A.REFERENTIEL, "convention -> portée référentielle")
check(leve(A.Atome, "x", A.CONVENTION, P_DOM, 1.0, "src"), "CONVENTION hors référentiel -> ValueError")

# ── 4) SUPPOSITION : ]0,1[, régime + base, jamais servable comme fait ──
s = A.suppose("dispositif thermo-photo cohérent", A.GENERATIF, P_DOM, 0.6, base="chaîne cohérente")
check(s.statut == A.SUPPOSITION and 0 < s.confiance < 1, "suppose -> SUPPOSITION dans ]0,1[")
check(s.est_servable_comme_fait() is False, "une SUPPOSITION n'est JAMAIS servable comme fait")
check("SUPPOSITION" in s.sert(), "sert() expose le statut (anti-glissement)")
check(leve(A.Atome, "x", A.SUPPOSITION, P_DOM, 1.0, "b", A.GENERATIF), "SUPPOSITION conf 1.0 -> ValueError")
check(leve(A.Atome, "x", A.SUPPOSITION, P_DOM, 0.0, "b", A.GENERATIF), "SUPPOSITION conf 0 -> ValueError")
check(leve(A.Atome, "x", A.SUPPOSITION, P_DOM, 0.5, "b", ""), "SUPPOSITION sans régime -> ValueError")
check(leve(A.suppose, "x", A.GENERATIF, P_DOM, 0.5, ""), "SUPPOSITION sans base -> ValueError")

# ── 5) portée obligatoire ; contenu validé (FAILLE #24) ──
check(leve(A.Atome, "x", A.FAIT, None, 1.0, "p"), "atome sans Portee -> ValueError")
check(leve(A.atteste, None, P_DOM, V_OK), "contenu None -> ValueError")
check(leve(A.atteste, "  ", P_DOM, V_OK), "contenu vide -> ValueError")

# ── 6) ASYMÉTRIE : promotion via Verdict seulement (FAILLE #2) ──
promu = A.promeut(s, V_OK, quand="t1")
check(promu.statut == A.FAIT and promu.confiance == 1.0, "promeut(Verdict positif) -> FAIT")
check(any("->fait" in p for p in promu.provenance), "promotion tracée + juge dans la provenance")
check(leve(A.promeut, s, True), "promeut(bool nu) -> ValueError (Verdict requis)")
check(leve(A.promeut, s, "oui"), "promeut(str) -> ValueError")
check(leve(A.promeut, f, V_OK), "promouvoir un FAIT -> ValueError")
rej = A.promeut(A.suppose("hypothèse fausse", A.GENERATIF, P_DOM, 0.4, base="test plausibilité"), V_KO, quand="t1")
check(rej.statut == A.REFUTE, "promeut(Verdict négatif) -> RÉFUTÉ")

# ── 7) régime interdit hors supposition -> ferme replace() (FAILLE #6/#16/#20) ──
check(leve(A.Atome, "x", A.FAIT, P_DOM, 1.0, "preuve", A.GENERATIF), "FAIT avec régime -> ValueError")
# replace() qui garde le régime 'generatif' est rejeté À LA CONSTRUCTION (la garde de régime le catche)
check(leve(dataclasses.replace, s, statut=A.FAIT, confiance=1.0), "replace(SUPPOSITION->FAIT) gardant le régime -> ValueError à la construction")

# ── 8) preuve invisible rejetée (FAILLE #4) ──
check(leve(A.Atome, "x", A.FAIT, P_DOM, 1.0, "​"), "preuve zero-width (U+200B) -> ValueError")
check(leve(A.Atome, "x", A.FAIT, P_DOM, 1.0, "ab"), "preuve trop courte -> ValueError")

# ── 9) object.__setattr__ mute frozen -> revalidation à la lecture attrape (FAILLE #5/#14/#21) ──
mut = A.suppose("bidon", A.GENERATIF, P_DOM, 0.2, base="test plausibilité")
object.__setattr__(mut, "statut", A.FAIT)
object.__setattr__(mut, "confiance", 1.0)   # laisse regime='generatif' incohérent
check(mut.est_servable_comme_fait() is False, "mutation frozen incohérente -> non servable (revalidation invariants)")
check("INVALIDE" in mut.sert() or mut.est_servable_comme_fait() is False, "sert() signale/rejette l'état incohérent")

# ── 10) sert() porte TOUJOURS la portée + confiance honnête (FAILLE #7/#9/#10/#13/#18/#23) ──
check("valable si" in f.sert() or "universel" in f.sert(), "sert() d'un FAIT expose sa portée")
hors = f.sert({"portee": "autre chose"})
check("HORS PORTÉE" in hors, "sert(contexte non couvert) signale un fait hors de sa portée")
check(f.est_servable_comme_fait({"portee": "à 1 atm"}) is True, "fait servable DANS sa portée")
check(f.est_servable_comme_fait({"portee": "autre"}) is False, "fait NON servable hors de sa portée")
s999 = A.suppose("presque sûr", A.GENERATIF, P_DOM, 0.999, base="test plausibilité")
check("1.00" not in s999.sert() and "conf=" in s999.sert(), "sert() n'arrondit JAMAIS une supposition à conf=1.00")

# ── 11) garde anti-re-proposition / anti-blanchiment (FAILLE #16/#17) ──
A._reset_gardes()
sr = A.suppose("les licornes existent", A.GENERATIF, P_DOM, 0.3, base="j'y crois")
refute_atome = A.promeut(sr, A.Verdict("falsification", False, "contre-exemple trouvé"))
check(refute_atome.statut == A.REFUTE and A.est_refute("les licornes existent"), "réfutation enregistre la garde")
check(leve(A.atteste, "les licornes existent", P_DOM, V_OK), "ré-attester un contenu réfuté -> ValueError (anti-blanchiment)")
sr2 = A.suppose("les licornes existent", A.GENERATIF, P_DOM, 0.3, base="re-tenté")  # supposer reste libre
check(sr2.statut == A.SUPPOSITION, "supposer un contenu réfuté reste LIBRE (asymétrie)")
check(leve(A.promeut, sr2, V_OK), "mais re-PROMOUVOIR un contenu réfuté -> ValueError")
A.rouvre("les licornes existent", "nouvelles preuves hypothétiques")
check(A.promeut(sr2, V_OK).statut == A.FAIT, "après rouvre() explicite, la promotion redevient possible")

# ── 12) revise_confiance borné + réfutation exige preuve (FAILLE #22) ──
check(A.revise_confiance(s, 0.85, "nouvelles preuves").confiance == 0.85, "revise_confiance reste supposition")
check(leve(A.revise_confiance, s, 1.0, "b"), "revise_confiance -> 1.0 interdit")
check(leve(A.refute, f, ""), "réfutation sans preuve -> ValueError")
check(leve(A.Atome, "x", A.REFUTE, P_DOM, 0.0, ""), "REFUTE direct sans preuve -> ValueError")

# ── 13) ANCRE RÉELLE (veille) : thérapie cellulaire du diabète, cadrée par le contrat ──
A._reset_gardes()
fait_instance = A.atteste(
    "la patiente de Tianjin (T1D) n'a plus besoin d'injections, stable > 1 an",
    A.Portee(A.REFERENTIEL, "ce cas clinique précis, ce protocole"),
    A.Verdict("suivi_clinique", True, "résultat observé et suivi > 1 an"))
check(fait_instance.est_servable_comme_fait() is True, "résultat sur un patient = FAIT à portée individuelle")
generalisation = A.suppose(
    "des cellules autologues reprogrammées en îlots guérissent le diabète",
    A.GENERATIF,
    A.Portee(A.EPISTEMIQUE, "sous réserve d'essais randomisés à grande échelle reproduits"),
    0.35, base="2 cas rapportés (Tianjin T1D, Shanghai T2D)")
check(generalisation.est_servable_comme_fait() is False, "généralisation : SUPPOSITION, jamais 'le diabète est guéri'")
monte = A.revise_confiance(generalisation, 0.5, "2e cas concordant", quand="2025")
check(monte.statut == A.SUPPOSITION, "un 2e cas monte la confiance mais NE promeut PAS")
remede = A.promeut(generalisation, A.Verdict("RCT_multicentrique", True, "reproduit à grande échelle"), quand="futur")
check(remede.statut == A.FAIT, "SEUL un juge réel (RCT reproduits) promeut en fait universel")

print(f"\n=== valide_atome : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
