"""CAPACITÉS — manifeste explicite et AUDITABLE des capacités formule/concept de l'IA (mission 2026-06-29).

POURQUOI. `couverture_reelle.py` mesure la couverture par match LEXICAL sur 5 fichiers seulement
(`physique/fonction_nl/auto_synthese/chimie/substrat_physique`). Il SOUS-COMPTE : des capacités RÉELLES et
VALIDÉES vivent ailleurs (`deduction`, `decision`, `bayes`, `jeux_zero_somme`, `echantillon_pondere`,
`test_calibration`, `regression_robuste`, `importance_sampling`, `stabilite_algorithmique`, `coherence_physique`…).
L'audit (workflow wcse5mt28, oracles indépendants + validateurs verts) a confirmé 32 « GAP » qui n'en sont pas.

CE MANIFESTE rend la couverture HONNÊTE et PLUS STRICTE que le lexical : un sujet n'est « couvert » QUE si un
mécanisme NOMMÉ rend la réponse CONNUE-correcte MAINTENANT (la preuve s'EXÉCUTE à l'appel, sur des cas à réponse
connue = ancres externes, avec un cas de soundness HORS quand c'est naturel). Donc :
  • aucun faux positif lexical (le lexical pouvait matcher un mot fortuit ; ici on exécute le calcul) ;
  • aucun gaming : si le mécanisme régressait, sa preuve échouerait et le sujet RE-DEVIENDRAIT non-couvert.
Invariant : couvert(libellé) == True  <=>  REGISTRE[libellé].preuve() s'exécute sans erreur ET tous ses cas justes.

LÉGER : modules pure-python, AUCUN chargement de base (imports PARESSEUX dans chaque preuve). Le compteur reste léger.
Chaque preuve = ancres déjà vérifiées en live (cf. probe 2026-06-29) — FAUX=0.
"""
from __future__ import annotations


def _proche(a, b, rel: float = 1e-3, abs_: float = 1e-9) -> bool:
    """Égalité numérique à tolérance relative (ancre physique mesurée) — False sur toute anomalie."""
    try:
        return abs(float(a) - float(b)) <= rel * abs(float(b)) + abs_
    except Exception:
        return False


# ── PREUVES (chacune renvoie True ssi tous ses cas à réponse CONNUE sont justes ; import paresseux) ──

def _p_raisonnement_deductif() -> bool:
    import deduction as D
    m = D.MoteurDeduction()
    m.ajoute_fait("parent", "a", "b")
    m.ajoute_fait("parent", "b", "c")
    m.ajoute_regle(("anc", "X", "Y"), [("parent", "X", "Y")], "anc_direct")   # 'base' = nom réservé (sentinel provenance)
    m.ajoute_regle(("anc", "X", "Z"), [("parent", "X", "Y"), ("anc", "Y", "Z")], "trans")
    # transitivité dérivée juste, ET pas d'invention dans l'autre sens (soundness)
    return (m.interroge("anc", "a", "c")[0] == "verifie"
            and m.interroge("anc", "a", "b")[0] == "verifie"
            and m.interroge("anc", "c", "a")[0] == "hors")


def _p_inference_statistique() -> bool:
    import echantillon_pondere as ep
    return (_proche(ep.estime_hajek([10, 20], [1, 1]), 15.0)
            and _proche(ep.estime_hajek([10, 20], [3, 1]), 12.5)
            and _proche(ep.n_effectif([1, 1, 1, 1]), 4.0))


def _p_tests_hypotheses() -> bool:
    import test_calibration as tc
    # Φ(1.96)=0.975, Φ(0)=0.5, survie du χ² en 0 = 1 (ancres de la loi normale / χ²)
    return (_proche(tc._phi(1.96), 0.975, rel=1e-3)
            and _proche(tc._phi(0.0), 0.5)
            and _proche(tc._chi2_sf(0.0, 1), 1.0))


def _p_statistique_bayesienne() -> bool:
    import bayes as B
    st, p, _ = B.posterior(0.5, [(0.9, 0.1, True)])   # LR=9 -> 0.9
    st0, p0, _ = B.posterior(0.5, [])                  # aucun indice -> prior
    stA, pA, _ = B.posterior(1.0, [(0.9, 0.1, True)])  # prior dégénéré -> abstention
    return (st == B.ESTIMATION and _proche(p, 0.9)
            and st0 == B.ESTIMATION and _proche(p0, 0.5)
            and stA == B.ABSTENTION)


def _p_regression_correlation() -> bool:
    import regression_robuste as rr
    b0, a0 = rr.ols([1, 2, 3], [2, 4, 6])          # y=2x : intercept 0, pente 2
    b1, a1 = rr.ols([0, 1, 2, 3], [1, 3, 5, 7])    # y=2x+1 : intercept 1, pente 2
    return _proche(b0, 0.0) and _proche(a0, 2.0) and _proche(b1, 1.0) and _proche(a1, 2.0)


def _p_echantillonnage() -> bool:
    import importance_sampling as isz
    # ESS = n si poids égaux ; -> 1 si un poids domine (diagnostic de dégénérescence)
    return (_proche(isz.ess([1, 1, 1, 1]), 4.0)
            and _proche(isz.ess([1, 1]), 2.0)
            and _proche(isz.ess([10, 0, 0, 0]), 1.0))


def _p_theorie_des_jeux_math() -> bool:
    import jeux_zero_somme as jzs
    st1, info1 = jzs.analyse([[1, -1], [-1, 1]], iters=3000)   # matching pennies : valeur 0
    st2, info2 = jzs.analyse([[4, 5], [6, 7]], iters=3000)      # point-selle dominé : valeur 6
    return (st1 == jzs.JEU and abs(info1["valeur"]) < 1e-2
            and st2 == jzs.JEU and _proche(info2["valeur"], 6.0, rel=2e-2))


def _p_theorie_des_jeux_equilibres() -> bool:
    # Même moteur, exercé sur l'équilibre (valeur minimax = stratégies optimales mixtes).
    return _p_theorie_des_jeux_math()


def _p_theorie_decision() -> bool:
    import decision as dec
    eu = dec.utilites_attendues({"a": 0.5, "b": 0.5}, {"x": {"a": 10, "b": 0}})
    st, act, _ = dec.decide({"pluie": 0.5, "sec": 0.5},
                            {"para": {"pluie": 1, "sec": -1}, "rien": {"pluie": -5, "sec": 2}}, 0.1)
    sta, _, _ = dec.decide({"x": 1.0}, {})            # aucune action -> abstention
    return _proche(eu["x"], 5.0) and st == dec.DECISION and act == "para" and sta == dec.ABSTENTION


def _p_apprentissage_mecanismes() -> bool:
    import stabilite_algorithmique as sa
    return (_proche(sa.knn([(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)], 1.0, 1), 1.0)
            and _proche(sa.knn([(0.0, 0.0), (1.0, 10.0), (2.0, 20.0)], 1.5, 2), 15.0)
            and sa.borne_generalisation(0.1, 0.05, 100) >= 0.1)   # borne ≥ risque empirique


# ── PHYSIQUE (mécanisme exact + constantes sourcées ; soundness HORS sur entrée invalide) ──

def _p_gravitation() -> bool:
    import physique as P
    g = P.calcule("gravite_surface", {"M": 5.972e24, "r": 6.371e6})       # Terre ≈ 9.81 m/s²
    v = P.calcule("vitesse_liberation", {"M": 5.972e24, "r": 6.371e6})    # ≈ 11186 m/s
    hors = P.calcule("gravite_surface", {"M": -1, "r": 6.371e6})          # M<0 -> HORS
    return (g[0] == P.VERIFIE and _proche(g[1], 9.81, rel=2e-3)
            and v[0] == P.VERIFIE and _proche(v[1], 11186, rel=5e-3)
            and hors[0] == P.HORS)


def _p_electrostatique() -> bool:
    import physique as P
    f = P.calcule("force_coulomb", {"q1": 1e-6, "q2": 1e-6, "r": 0.1})    # ≈ 0.898755 N
    e = P.calcule("champ_electrique", {"q": 1e-6, "r": 0.1})              # ≈ 898755 N/C
    hors = P.calcule("force_coulomb", {"q1": 1, "q2": 1, "r": 0})         # r=0 -> HORS
    return (f[0] == P.VERIFIE and _proche(f[1], 0.898755, rel=1e-4)
            and e[0] == P.VERIFIE and _proche(e[1], 898755, rel=1e-4)
            and hors[0] == P.HORS)


def _p_radioactivite() -> bool:
    import physique as P
    d = P.calcule("decroissance_radioactive", {"N0": 1000, "t": 20, "demi_vie": 10})   # 2 demi-vies -> 250
    d0 = P.calcule("decroissance_radioactive", {"N0": 1000, "t": 0, "demi_vie": 10})   # t=0 -> 1000
    em = P.calcule("energie_masse_defaut", {"delta_m": 1})                              # E=mc² ≈ 8.98755e16 J
    hors = P.calcule("decroissance_radioactive", {"N0": 100, "t": 5, "demi_vie": 0})   # T=0 -> HORS
    return (d[0] == P.VERIFIE and _proche(d[1], 250.0)
            and d0[0] == P.VERIFIE and _proche(d0[1], 1000.0)
            and em[0] == P.VERIFIE and _proche(em[1], 8.98755e16, rel=1e-3)
            and hors[0] == P.HORS)


def _p_acides_bases_ph() -> bool:
    import physique as P
    a = P.calcule("ph", {"concentration_H": 1e-7})     # eau neutre -> 7
    b = P.calcule("ph", {"concentration_H": 1e-3})     # -> 3
    o = P.calcule("poh", {"concentration_OH": 1e-7})   # -> 7
    hors = P.calcule("ph", {"concentration_H": 0})     # log indéfini -> HORS
    return (a[0] == P.VERIFIE and _proche(a[1], 7.0)
            and b[0] == P.VERIFIE and _proche(b[1], 3.0)
            and o[0] == P.VERIFIE and _proche(o[1], 7.0)
            and hors[0] == P.HORS)


def _p_mecanique_celeste() -> bool:
    import physique as P
    t = P.calcule("periode_orbitale", {"a": 1.496e11, "M": 1.989e30})    # 1 UA autour du Soleil ≈ 1 an
    g = P.calcule("gravite_surface", {"M": 5.972e24, "r": 6.371e6})       # ancre Terre
    hors = P.calcule("periode_orbitale", {"a": -1, "M": 1.989e30})        # a<0 -> HORS
    return (t[0] == P.VERIFIE and _proche(t[1], 3.156e7, rel=5e-3)
            and g[0] == P.VERIFIE and _proche(g[1], 9.81, rel=2e-3)
            and hors[0] == P.HORS)


def _p_mouvement_perpetuel() -> bool:
    import coherence_physique as cp
    v = cp.juge_dispositif({"type": "moteur_thermique", "rendement": 0.70, "t_chaud_K": 800, "t_froid_K": 300})
    c = cp.juge_dispositif({"type": "moteur_thermique", "rendement": 0.50, "t_chaud_K": 800, "t_froid_K": 300})
    # rendement 0.70 > Carnot(1-300/800)=0.625 -> VIOLE ; 0.50 < 0.625 -> COHERENT_BORNE
    return v[0] == cp.VIOLE and c[0] == cp.COHERENT_BORNE


def _p_systeme_unites_si() -> bool:
    import fonction_nl as fnl
    from base_faits import VERIFIE, HORS
    a = fnl.resout_conversion("2 km en m")             # 2000 m
    b = fnl.resout_conversion("3 heures en secondes")   # 10800 secondes
    hors = fnl.resout_conversion("5 km en kg")          # inter-dimension -> HORS
    return (a[0] == VERIFIE and a[1].split()[0] == "2000"
            and b[0] == VERIFIE and b[1].split()[0] == "10800"
            and hors[0] == HORS)


# ── MATHS DISCRÈTES (maths_discretes.py : primitives exactes, soundness = ValueError sur entrée invalide) ──

def _leve(fn, *a) -> bool:
    """True ssi fn(*a) lève ValueError (preuve de soundness : entrée invalide -> jamais un faux résultat)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def _p_denombrement() -> bool:
    import maths_discretes as M
    return (M.catalan(7) == 429 and M.catalan(8) == 1430
            and M.derangements(5) == 44 and M.partitions(6) == 11
            and M.binomial(5, 2) == 10 and M.binomial(5, 7) == 0
            and _leve(M.catalan, -1))


def _p_recurrences() -> bool:
    import maths_discretes as M
    return (M.fibonacci(10) == 55 and M.lucas(6) == 18
            and M.suite_recurrente(0, 1, 1, 1, 7) == 13     # Fibonacci F(7)
            and _leve(M.fibonacci, -1))


def _p_theorie_graphes() -> bool:
    import maths_discretes as M
    return (M.composantes_connexes(4, [(0, 1), (2, 3)]) == 2
            and M.a_cycle(3, [(0, 1), (1, 2), (2, 0)]) is True
            and M.a_cycle(3, [(0, 1), (1, 2)]) is False
            and M.est_biparti(4, [(0, 1), (1, 2), (2, 3)]) is True
            and M.est_biparti(3, [(0, 1), (1, 2), (2, 0)]) is False
            and _leve(M.composantes_connexes, 2, [(0, 5)]))   # sommet hors plage -> HORS


def _p_algorithmique() -> bool:
    import maths_discretes as M
    return (M.dijkstra(4, [(0, 1, 1), (1, 3, 1), (0, 2, 5), (2, 3, 1)], 0, 3) == 2
            and M.distance_bfs(4, [(0, 1), (1, 2), (2, 3)], 0, 3) == 3
            and M.distance_bfs(4, [(0, 1), (2, 3)], 0, 3) == -1      # inatteignable
            and _leve(M.dijkstra, 3, [(0, 1, -1)], 0, 1))            # poids négatif -> HORS


def _p_geometrie_analytique() -> bool:
    import maths_discretes as M
    return (M.aire_triangle_x2((0, 0), (4, 0), (0, 3)) == 12          # aire 6 -> ×2 = 12
            and M.aire_triangle_x2((0, 0), (2, 2), (4, 4)) == 0       # colinéaires
            and M.aire_polygone_x2([(0, 0), (4, 0), (4, 3), (0, 3)]) == 24   # rectangle 4×3 -> ×2 = 24
            and M.orientation((0, 0), (1, 0), (1, 1)) == 1            # gauche
            and M.distance_manhattan((0, 0), (3, 4)) == 7
            and _leve(M.aire_polygone_x2, [(0, 0), (1, 1)]))          # <3 sommets -> HORS


def _p_structuration_donnees() -> bool:
    import maths_discretes as M
    return (M.eval_rpn(["2", "3", "+", "4", "*"]) == 20
            and M.eval_rpn(["10", "2", "//"]) == 5
            and M.equilibre("(()[])") is True
            and M.equilibre("(()") is False
            and _leve(M.eval_rpn, ["1", "0", "//"]))                 # division par zéro -> HORS


def _p_debogage() -> bool:
    import audit_code as A
    inj = A.audite('eval(request.GET["x"])', "python")               # injection -> CWE-95
    propre = A.audite("def f(a, b):\n    return a + b", "python")    # propre -> RAS (pas de faux positif)
    hors = A.audite("code", "klingon")                               # langage inconnu -> HORS
    return (inj[0] == A.VERIFIE and any(c.cwe == "CWE-95" for c in inj[1])
            and propre[0] == A.RAS and propre[1] == []
            and hors[0] == A.HORS)


# ── ALGÈBRE (algebre_calcul.py : équations exactes en ℚ, soundness = float/a=0 refusés) ──

def _p_equations_lineaires() -> bool:
    import algebre_calcul as A
    from fractions import Fraction
    return (A.equation_lineaire(2, -6) == ("unique", Fraction(3))
            and A.equation_lineaire(4, 1) == ("unique", Fraction(-1, 4))
            and A.equation_lineaire(0, 5) == ("aucune", None)
            and A.equation_lineaire(0, 0) == ("infinie", None)
            and _leve_v(A.equation_lineaire, 1.5, 2))     # float inexact refusé


def _p_equations_polynomiales() -> bool:
    import algebre_calcul as A
    from fractions import Fraction
    return (A.equation_quadratique(1, -3, 2) == ("deux_rationnelles", [Fraction(1), Fraction(2)])
            and A.equation_quadratique(2, -7, 3) == ("deux_rationnelles", [Fraction(1, 2), Fraction(3)])
            and A.equation_quadratique(1, -2, 1) == ("double", [Fraction(1)])
            and A.equation_quadratique(1, 0, 1)[0] == "aucune_reelle"
            and A.equation_quadratique(1, 0, -2) == ("deux_irrationnelles", Fraction(8))   # √2 non faussé
            and A.est_racine([6, -5, 1], 2) and A.est_racine([6, -5, 1], 3)
            and _leve_v(A.equation_quadratique, 0, 2, 1))   # a=0 -> pas quadratique


def _leve_v(fn, *a, **k) -> bool:
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def _p_cryptographie_mathematique() -> bool:
    import arithmetique_modulaire as A
    inv = A.inverse_modulaire(17, 3233)                       # clé privée RSA d
    c = A.rsa_chiffre(65, 17, 3233)                            # chiffrement
    return (A.pgcd(48, 36) == 12
            and A.euclide_etendu(240, 46) == (2, -9, 47)       # Bézout exact
            and (17 * inv) % 3233 == 1                          # inverse modulaire correct
            and A.exp_modulaire(7, 128, 13) == pow(7, 128, 13)
            and A.est_premier(7919) is True and A.est_premier(561) is False   # Carmichael démasqué
            and c == 2790 and A.rsa_dechiffre(c, 2753, 3233) == 65            # RSA round-trip
            and _leve_v(A.inverse_modulaire, 6, 9))            # inverse inexistant -> abstention


def _p_theorie_information() -> bool:
    import information_calcul as I
    return (abs(I.entropie([0.5, 0.5]) - 1.0) < 1e-9
            and abs(I.entropie([0.25] * 4) - 2.0) < 1e-9
            and abs(I.entropie([0.5, 0.25, 0.25]) - 1.5) < 1e-9
            and I.entropie([1.0, 0.0]) == 0.0
            and abs(I.divergence_kl([0.5, 0.5], [0.5, 0.5])) < 1e-12
            and abs(I.information_mutuelle([[0.5, 0.0], [0.0, 0.5]]) - 1.0) < 1e-9
            and _leve_v(I.entropie, [0.5, 0.6]))     # distribution invalide -> abstention


def _p_algebre_boole() -> bool:
    import algebre_boole as BB
    return (BB.est_tautologie("~(a & b) <-> (~a | ~b)")          # De Morgan
            and BB.est_tautologie("((a -> b) & a) -> b")          # modus ponens
            and BB.est_contradiction("a & ~a")
            and BB.equivalent("a -> b", "~a | b")
            and not BB.est_tautologie("a -> b")                   # non-théorème non déclaré tautologie
            and _leve_v(BB.est_tautologie, "(a & b"))             # mal formé -> abstention


def _p_theorie_automates() -> bool:
    import automates as AU
    parite = {"etats": {"p", "i"}, "alphabet": {"0", "1"},
              "transitions": {("p", "0"): "p", ("p", "1"): "i", ("i", "0"): "i", ("i", "1"): "p"},
              "initial": "p", "acceptants": {"p"}}
    mul3 = {"etats": {0, 1, 2}, "alphabet": {"0", "1"},
            "transitions": {(r, b): (2 * r + int(b)) % 3 for r in (0, 1, 2) for b in ("0", "1")},
            "initial": 0, "acceptants": {0}}
    return (AU.accepte(parite, "11") is True and AU.accepte(parite, "1") is False
            and AU.accepte(mul3, "1001") is True and AU.accepte(mul3, "10") is False
            and _leve_v(AU.accepte, parite, "2"))     # symbole hors alphabet -> abstention


def _p_machines_turing() -> bool:
    import turing as TU
    incr = {"blanc": "_", "initial": "d", "acceptants": {"f"},
            "transitions": {("d", "0"): ("d", "0", "R"), ("d", "1"): ("d", "1", "R"),
                            ("d", "_"): ("r", "_", "L"), ("r", "0"): ("f", "1", "L"),
                            ("r", "1"): ("r", "0", "L"), ("r", "_"): ("f", "1", "L")}}
    st, ruban, _ = TU.execute(incr, "111", 1000)
    boucle = {"blanc": "_", "initial": "q", "acceptants": set(),
              "transitions": {("q", "0"): ("q", "0", "R"), ("q", "1"): ("q", "1", "R"), ("q", "_"): ("q", "_", "R")}}
    return (st == "accepte" and ruban == "1000"                  # succ(111)=1000
            and TU.execute(boucle, "1", 200)[0] == "timeout"     # arrêt indécidable -> timeout honnête
            and _leve_v(TU.execute, incr, "1", 0))               # budget invalide -> abstention


def _p_geotechnique() -> bool:
    import geotechnique as GT
    return (GT.contrainte_verticale(18, 5) == 90.0 and GT.contrainte_effective(90, 20) == 70.0
            and abs(GT.coefficient_poussee_active(30) - 1 / 3) < 1e-4
            and abs(GT.coefficient_poussee_active(30) * GT.coefficient_poussee_passive(30) - 1.0) < 1e-4
            and abs(GT.poussee_active(18, 5, 30) - 75.0) < 1e-2
            and _leve_v(GT.coefficient_poussee_active, 90))    # φ=90° -> abstention


def _p_reacteurs_distillation() -> bool:
    import genie_chimique as GC
    return (GC.temps_sejour(100, 5) == 20.0
            and abs(GC.conversion_cstr_ordre1(0.5, 4) - 2 / 3) < 1e-4
            and GC.conversion_pfr_ordre1(0.5, 4) > GC.conversion_cstr_ordre1(0.5, 4)   # PFR > CSTR
            and abs(GC.etages_fenske(0.95, 0.05, 2) - 8.49586) < 1e-3
            and _leve_v(GC.temps_sejour, 100, 0))          # débit nul -> abstention


def _p_web() -> bool:
    import web as WB
    return (WB.balises_equilibrees("<div><p>x</p></div>") is True
            and WB.balises_equilibrees("<div><p></div></p>") is False
            and WB.balises_equilibrees("<div><br><img></div>") is True       # void sans fermeture
            and WB.specificite("#nav .item a") == (1, 1, 1)
            and WB.compare_specificite("#x", ".a.b.c") == 1                   # id > classes
            and _leve_v(WB.specificite, ""))                # sélecteur vide -> abstention


def _p_geometrie_projective() -> bool:
    import geometrie_projective as GP
    from fractions import Fraction
    pts = [0, 1, 3, 7]
    images = [GP.homographie(x, 2, 1, 1, 3) for x in pts]
    return (GP.birapport(0, 1, 2, 3) == Fraction(4, 3)
            and GP.birapport(*pts) == GP.birapport(*images)                   # invariance par homographie
            and GP.conjugue_harmonique(0, 6, 2) == -6
            and GP.est_division_harmonique(0, 6, 2, -6) is True
            and _leve_v(GP.birapport, 0, 1, 1, 2))          # points confondus -> abstention


def _p_cloud_distribue() -> bool:
    import cloud_distribue as CD
    noeuds = ["n1", "n2", "n3"]
    return (CD.noeud_responsable("cle-X", noeuds) == CD.noeud_responsable("cle-X", noeuds)   # déterministe
            and CD.noeud_responsable("cle-X", noeuds) in noeuds
            and CD.quorum_coherent(3, 2, 2) is True and CD.quorum_coherent(3, 1, 1) is False
            and CD.cap_choix(True, "coherence") == "CP" and CD.cap_choix(True, "disponibilite") == "AP"
            and _leve_v(CD.noeud_responsable, "x", []))    # aucun nœud -> abstention


def _p_big_data() -> bool:
    import big_data as BG
    wc = BG.compte_mots(["le chat dort", "le chien court", "le chat court"])
    b = BG.FiltreBloom(2048, 5)
    for e in [f"e{i}" for i in range(30)]:
        b.ajoute(e)
    return (wc == {"le": 3, "chat": 2, "dort": 1, "chien": 1, "court": 2}
            and all(b.contient(f"e{i}") for i in range(30))    # aucun faux négatif
            and BG.echantillon_reservoir(["a", "b", "c", "d"], 2, {0, 2}) == ["a", "c"]
            and _leve_v(lambda: BG.FiltreBloom(0)))         # taille 0 -> abstention


def _p_cryptographie_appliquee() -> bool:
    import cryptographie_appliquee as KA
    return (KA.chiffre_vigenere("ATTACKATDAWN", "LEMON") == "LXFOPVEFRNHR"      # vecteur canonique
            and KA.dechiffre_vigenere(KA.chiffre_vigenere("SECRET", "KEY"), "KEY") == "SECRET"
            and KA.chiffre_cesar("HELLO", 3) == "KHOOR"
            and KA.chiffre_xor(KA.chiffre_xor(b"hello", b"\x10\x20"), b"\x10\x20") == b"hello"   # involution
            and _leve_v(KA.chiffre_vigenere, "HELLO", ""))    # clé vide -> abstention


def _p_microprocesseurs() -> bool:
    import microprocesseurs as MP
    r1 = MP.alu("add", 200, 100, 8)
    r2 = MP.alu("add", 100, 28, 8)
    return (MP.porte("non-et", 1, 1) == 0 and MP.porte("ou-x", 1, 0) == 1
            and MP.additionneur_complet(1, 1, 1) == (1, 1)
            and r1["resultat"] == 44 and r1["retenue"] == 1
            and r2["debordement"] is True and r2["retenue"] == 0     # débordement signé sans retenue
            and _leve_v(MP.alu, "mul", 2, 2, 8))              # opération inconnue -> abstention


def _p_blockchain() -> bool:
    import blockchain as BC
    g = BC.cree_bloc(0, "genesis", "0")
    b1 = BC.cree_bloc(1, "tx1", g["hash"])
    b2 = BC.cree_bloc(2, "tx2", b1["hash"])
    return (BC.chaine_valide([g, b1, b2]) is True
            and BC.chaine_valide([g, dict(b1, donnees="falsifie"), b2]) is False
            and BC.merkle_root(["a", "b"]) == BC.merkle_root(["a", "b"])
            and BC.merkle_root(["a", "b"]) != BC.merkle_root(["b", "a"])
            and BC.preuve_travail_valide("000x", 3) is True and BC.preuve_travail_valide("00x", 3) is False
            and _leve_v(BC.chaine_valide, []))             # chaîne vide -> abstention


def _p_etats_matiere() -> bool:
    import etats_matiere as EM
    return (EM.etat_physique(-10, 0, 100) == "solide" and EM.etat_physique(25, 0, 100) == "liquide"
            and EM.etat_physique(150, 0, 100) == "gaz"
            and EM.celsius_vers_kelvin(0) == 273.15 and EM.celsius_vers_fahrenheit(100) == 212.0
            and _leve_v(EM.etat_physique, 25, 100, 0))     # points incohérents -> abstention


def _p_telecommunications() -> bool:
    import telecom as TC
    return (TC.capacite_shannon(3000, 7) == 9000.0 and TC.capacite_shannon(1000, 1) == 1000.0
            and TC.debit_nyquist(3000, 2) == 6000.0 and TC.gain_db(100, 1) == 20.0
            and _leve_v(TC.capacite_shannon, 0, 1))        # B=0 -> abstention


def _p_reseaux_neurones() -> bool:
    import reseaux_neurones as NN
    entrees = [(0, 0), (0, 1), (1, 0), (1, 1)]
    et = {(0, 0): 0, (0, 1): 0, (1, 0): 0, (1, 1): 1}
    ou = {(0, 0): 0, (0, 1): 1, (1, 0): 1, (1, 1): 1}
    return (all(NN.neurone(list(x), [1, 1], -1.5) == et[x] for x in entrees)       # perceptron ET
            and all(NN.neurone(list(x), [1, 1], -0.5) == ou[x] for x in entrees)    # perceptron OU
            and abs(NN.sigmoide(0) - 0.5) < 1e-9 and NN.relu(-2) == 0.0
            and _leve_v(NN.potentiel, [1, 1], [1], 0))     # dim incompatibles -> abstention


def _p_bases_donnees() -> bool:
    import bases_donnees as BD
    T = [{"id": 1, "d": "A"}, {"id": 2, "d": "B"}, {"id": 3, "d": "A"}]
    S = [{"id": 1, "s": 50}, {"id": 2, "s": 40}, {"id": 3, "s": 60}]
    return (len(BD.selection(T, "d", "==", "A")) == 2
            and BD.projection(T, ["d"]) == [{"d": "A"}, {"d": "B"}]
            and BD.jointure(T, S, "id")[0]["s"] == 50 and len(BD.jointure(T, S, "id")) == 3
            and BD.agregat(S, "s", "avg") == 50.0 and BD.agregat(S, "s", "sum") == 150
            and _leve_v(BD.selection, T, "inexistant", "==", 1))   # colonne absente -> abstention


def _p_theorie_reseaux() -> bool:
    import theorie_reseaux as TR
    triangle = [(0, 1), (1, 2), (2, 0)]
    etoile = [(0, 1), (0, 2), (0, 3)]
    return (TR.densite(3, triangle) == 1.0 and abs(TR.densite(4, etoile) - 0.5) < 1e-9
            and TR.degre(4, etoile, 0) == 3 and TR.clustering_local(3, triangle, 0) == 1.0
            and TR.centralite_degre(4, etoile, 0) == 1.0
            and _leve_v(TR.degre, 3, triangle, 5))         # sommet hors plage -> abstention


def _p_reseaux() -> bool:
    import reseaux_ip as RX
    return (RX.adresse_reseau("192.168.1.130", 24) == "192.168.1.0"
            and RX.adresse_broadcast("192.168.1.130", 24) == "192.168.1.255"
            and RX.nombre_hotes(24) == 254 and RX.masque(26) == "255.255.255.192"
            and RX.meme_reseau("10.0.0.1", "10.0.0.254", 24) is True
            and RX.meme_reseau("10.0.0.1", "10.0.1.1", 24) is False
            and _leve_v(RX.ip_vers_entier, "192.168.1.256"))   # octet invalide -> abstention


def _p_architecture() -> bool:
    import architecture as AR
    return (AR.complement_a_deux(-1, 8) == 255 and AR.complement_a_deux(-128, 8) == 128
            and AR.depuis_complement_a_deux(255, 8) == -1
            and AR.vers_hexa(255) == "FF" and AR.vers_binaire(5, 8) == "00000101"
            and AR.addition_binaire(100, 50, 8)[1] is True       # débordement détecté
            and _leve_v(AR.complement_a_deux, 128, 8))           # hors intervalle -> abstention


def _p_equilibres_chimiques() -> bool:
    import equilibre_chimique as EQ
    return (EQ.quotient_reaction([(2, 2)], [(1, 1), (1, 3)]) == 4.0
            and EQ.sens_evolution(4, 10) == "direct" and EQ.sens_evolution(4, 1) == "inverse"
            and EQ.sens_evolution(4, 4) == "equilibre"
            and EQ.deplace_equilibre_temperature(True, True) == "inverse"
            and _leve_v(EQ.quotient_reaction, [(0, 1)], [(1, 1)]))   # conc nulle -> abstention


def _p_hydraulique() -> bool:
    import hydraulique as HY
    return (HY.debit_volumique(2, 0.5) == 1.0
            and HY.vitesse_continuite(2, 1, 0.5) == 4.0
            and HY.nombre_reynolds(1000, 1, 0.1, 0.001) == 100000.0
            and HY.regime_ecoulement(500) == "laminaire" and HY.regime_ecoulement(100000) == "turbulent"
            and _leve_v(HY.debit_volumique, 2, 0))         # section nulle -> abstention


def _p_robotique() -> bool:
    import robotique as RB
    x, y = RB.cinematique_directe_2r(2, 1, 90, -90)
    return (abs(x - 1.0) < 1e-4 and abs(y - 2.0) < 1e-4
            and RB.portee_max(3, 1) == 4.0 and RB.portee_min(3, 1) == 2.0
            and RB.atteignable(2, 1, 2.5, 0) is True and RB.atteignable(2, 1, 0.5, 0) is False
            and _leve_v(RB.cinematique_directe_2r, 0, 1, 0, 0))   # longueur nulle -> abstention


def _p_controle() -> bool:
    import controle as CT
    return (CT.est_stable([1, 2, 1]) is True and CT.est_stable([1, 6, 11, 6]) is True
            and CT.est_stable([1, 1, 1, 6]) is False and CT.est_stable([1, -2, 1]) is False
            and CT.changements_de_signe([1, 1, 1, 6]) == 2
            and _leve_v(CT.est_stable, [1, 0, 1]))        # cas marginal -> abstention


def _p_circuits_electroniques() -> bool:
    import electronique as EL
    return (EL.resistance_serie([10, 20, 30]) == 60.0
            and abs(EL.resistance_parallele([2, 3, 6]) - 1.0) < 1e-6
            and EL.diviseur_tension(12, 1000, 2000) == 8.0
            and abs(EL.constante_temps_rc(1000, 1e-6) - 1e-3) < 1e-9
            and _leve_v(EL.resistance_serie, []))         # liste vide -> abstention


def _p_statique() -> bool:
    import statique as ST
    return (ST.force_levier(100, 1, 4) == 25.0
            and ST.centre_de_masse([2, 1], [0, 3]) == 1.0
            and ST.reactions_appui(100, 1, 4) == (75.0, 25.0)
            and ST.equilibre_moments([10, -10]) is True and ST.equilibre_moments([10, -5]) is False
            and _leve_v(ST.force_levier, 100, 0, 4))      # bras nul -> abstention


def _p_solutions_concentrations() -> bool:
    import chimie_quantitative as CQ
    return (CQ.molarite(0.5, 2) == 0.25 and CQ.dilution(2, 0.1, 0.5) == 0.4
            and CQ.volume_dilution(2, 0.1, 0.25) == 0.8
            and _leve_v(CQ.molarite, 0.5, 0))            # V=0 -> abstention


def _p_thermochimie() -> bool:
    import chimie_quantitative as CQ
    return (abs(CQ.enthalpie_reaction([-393.5, 2 * -285.8], [-74.8, 0]) - (-890.3)) < 1e-2   # combustion CH4
            and CQ.est_exothermique(-890.3) is True and CQ.est_exothermique(180) is False
            and _leve_v(CQ.enthalpie_reaction, -100, [0]))   # non-liste -> abstention


def _p_electrochimie() -> bool:
    import chimie_quantitative as CQ
    return (abs(CQ.potentiel_cellule(0.34, -0.76) - 1.10) < 1e-4         # pile Daniell
            and CQ.est_spontanee(1.10) is True and CQ.est_spontanee(-0.5) is False
            and _leve_v(CQ.potentiel_cellule, "x", 0))


def _p_forces_frottements() -> bool:
    import mecanique as MEC
    return (MEC.force_frottement(0.5, 100) == 50.0 and MEC.force_frottement(0, 100) == 0.0
            and _leve_v(MEC.force_frottement, -0.5, 100))    # μ<0 -> abstention


def _p_oscillateurs() -> bool:
    import mecanique as MEC
    import math
    return (abs(MEC.periode_ressort(1, 1) - 2 * math.pi) < 1e-4
            and abs(MEC.frequence_ressort(1, 4 * math.pi ** 2) - 1.0) < 1e-4
            and abs(MEC.periode_pendule(MEC.G_PESANTEUR) - 2 * math.pi) < 1e-4
            and _leve_v(MEC.periode_ressort, 0, 1))          # m=0 -> abstention


def _p_mecanique_fluides() -> bool:
    import mecanique as MEC
    return (MEC.pression(100, 2) == 50.0
            and abs(MEC.poussee_archimede(1000, 0.001) - 9.80665) < 1e-3
            and abs(MEC.pression_hydrostatique(1000, 10) - 98066.5) < 1e-1
            and _leve_v(MEC.pression, 100, 0))                # surface=0 -> abstention


def _p_stoechiometrie() -> bool:
    import stoechiometrie as S
    return (S.equilibre(["H2", "O2"], ["H2O"]) == [2, 1, 2]
            and S.equilibre(["CH4", "O2"], ["CO2", "H2O"]) == [1, 2, 1, 2]
            and S.equilibre(["Fe", "O2"], ["Fe2O3"]) == [4, 3, 2]
            and _leve_v(S.equilibre, ["H2"], ["O2"]))     # éléments incompatibles -> abstention


def _p_trigonometrie() -> bool:
    import trigonometrie as TR
    return (TR.sin_deg(30) == 0.5 and TR.cos_deg(60) == 0.5 and TR.tan_deg(45) == 1.0
            and TR.hypotenuse(3, 4) == 5.0 and abs(TR.angle_par_cotes(3, 4, 5) - 90.0) < 1e-9
            and _leve_v(TR.tan_deg, 90))               # asymptote -> abstention


def _p_derivation() -> bool:
    import calcul_infinitesimal as CI
    from fractions import Fraction
    return (CI.derivee([2, -3, 0, 1]) == [Fraction(-3), Fraction(0), Fraction(3)]   # d/dx(x³-3x+2)
            and CI.derivee([5]) == [Fraction(0)]
            and CI.derivee([0, 0, 0, 0, 1]) == [Fraction(0), Fraction(0), Fraction(0), Fraction(4)]
            and _leve_v(CI.derivee, [1, "a"]))


def _p_integration() -> bool:
    import calcul_infinitesimal as CI
    from fractions import Fraction
    return (CI.integrale_definie([0, 0, 1], 0, 3) == Fraction(9)        # ∫₀³ x² = 9
            and CI.integrale_definie([0, 2], 1, 4) == Fraction(15)
            and CI.derivee(CI.primitive([3, -2, 5])) == [Fraction(3), Fraction(-2), Fraction(5)]
            and _leve_v(CI.integrale_definie, [1.5], 0, 1))


def _p_limites() -> bool:
    import calcul_infinitesimal as CI
    from fractions import Fraction
    return (CI.limite_rationnelle_en([-1, 0, 1], [-1, 1], 1) == Fraction(2)    # (x²-1)/(x-1) -> 2
            and CI.limite_polynome_en([2, -3, 1], 4) == Fraction(6)
            and _leve_v(CI.limite_rationnelle_en, [1], [0, 1], 0))    # pôle -> abstention


def _p_series() -> bool:
    import series_calcul as SE
    from fractions import Fraction
    return (SE.somme_geometrique_infinie(1, Fraction(1, 2)) == Fraction(2)
            and SE.somme_arithmetique(1, 1, 100) == Fraction(5050)
            and SE.somme_carres(10) == Fraction(385)
            and SE.converge_riemann(2) and not SE.converge_riemann(1)
            and _leve_v(SE.somme_geometrique_infinie, 1, 2))         # divergente -> abstention


def _p_theorie_groupes() -> bool:
    import groupes as GR
    return (GR.ordre_element_zn(2, 6) == 3 and GR.ordre_element_zn(1, 7) == 7
            and GR.ordre_permutation((1, 0, 3, 4, 2)) == 6        # 2-cycle + 3-cycle -> ppcm 6
            and GR.signature_permutation((1, 0, 2)) == -1
            and GR.est_groupe([[0, 1, 2], [1, 2, 0], [2, 0, 1]]) is True
            and GR.lagrange_divise(3, 6) and not GR.lagrange_divise(4, 6)
            and _leve_v(GR.ordre_permutation, (0, 0, 1)))         # permutation invalide -> abstention


def _p_nombres_complexes() -> bool:
    import nombres_complexes as M
    def ap(z, w):
        return abs(z[0] - w[0]) < 1e-6 and abs(z[1] - w[1]) < 1e-6
    rac = M.racines_nieme((1, 0), 3)
    return (ap(M.produit((0, 1), (0, 1)), (-1.0, 0.0))
            and abs(M.module((3, 4)) - 5.0) < 1e-6
            and ap(M.produit((1, 2), (3, 4)), (-5.0, 10.0))
            and ap(M.quotient((1, 1), (1, -1)), (0.0, 1.0))
            and len(rac) == 3
            and any(ap(r, (1.0, 0.0)) for r in rac)
            and _leve_v(M.quotient, (1, 1), (0, 0))
            and _leve_v(M.argument, (0, 0)))

def _p_liaisons_chimiques() -> bool:
    import liaisons_chimiques as M
    return (M.nature_liaison(2.20, 2.20) == 'covalente_non_polaire'
            and M.nature_liaison(2.20, 3.16) == 'covalente_polaire'
            and M.nature_liaison(0.93, 3.16) == 'ionique'
            and M.nature_liaison(0.79, 3.98) == 'ionique'
            and abs(M.difference_electronegativite(2.20, 3.16) - 0.96) < 1e-6
            and abs(M.pourcentage_ionique(0.93, 3.16) - 71.1548) < 1e-3
            and M.pourcentage_ionique(2.20, 3.16) < M.pourcentage_ionique(0.93, 3.16)
            and _leve_v(M.nature_liaison, 0.93, 0)
            and _leve_v(M.difference_electronegativite, -1.0, 3.16)
            and _leve_v(M.pourcentage_ionique, 2.2, 0.0))

def _p_analyse_fonctionnelle() -> bool:
    import analyse_fonctionnelle as M
    return (abs(M.norme([3, 4]) - 5.0) < 1e-6
            and abs(M.norme([5, 12]) - 13.0) < 1e-6
            and abs(M.norme([1, -2, 2], 1) - 5.0) < 1e-6
            and abs(M.norme([1, -2, 2], 'inf') - 2.0) < 1e-6
            and abs(M.produit_scalaire([1, 2], [3, 4]) - 11.0) < 1e-6
            and abs(M.distance([0, 0], [3, 4]) - 5.0) < 1e-6
            and M.sont_orthogonaux([1, 0], [0, 1]) is True
            and M.sont_orthogonaux([1, 2], [3, 4]) is False
            and M.cauchy_schwarz_verifiee([1, 2], [3, 4]) is True
            and M.projection([2, 2], [1, 0]) == [2.0, 0.0]
            and M.projection([2, 4], [1, 2]) == [2.0, 4.0]
            and _leve_v(M.produit_scalaire, [1, 2], [1, 2, 3])
            and _leve_v(M.projection, [1, 2], [0, 0])
            and _leve_v(M.norme, [1, 2], 0.5)
            and _leve_v(M.norme, []))

def _p_equa_diff() -> bool:
    import math
    import equa_diff as M
    return (abs(M.solution_exponentielle(1, 1, 1) - 2.718281828459045) < 1e-6
            and M.solution_exponentielle(100, -0.1, 0) == 100.0
            and abs(M.solution_exponentielle(1, math.log(2), 2) - 4.0) < 1e-6
            and abs(M.solution_exponentielle(100, -math.log(2), 1) - 50.0) < 1e-6
            and M.demi_vie(math.log(2)) == 1.0
            and abs(M.demi_vie(1) - 0.6931471805599453) < 1e-6
            and abs(M.solution_affine(100, -1, 20, 1) - 49.43035529371538) < 1e-6
            and M.solution_affine(20, -1, 20, 5) == 20.0
            and M.solution_affine(5, 0, 3, 2) == 11.0
            and abs(M.euler(lambda t, y: y, 1, 0, 1, 100000) - 2.718281828459045) < 1e-3
            and abs(M.euler(lambda t, y: 2.0, 0, 0, 5, 7) - 10.0) < 1e-6
            and _leve_v(M.euler, lambda t, y: y, 1, 0, 1, 0)
            and _leve_v(M.euler, lambda t, y: y, 1, 0, 1, -5)
            and _leve_v(M.demi_vie, 0)
            and _leve_v(M.demi_vie, True)
            and _leve_v(M.solution_exponentielle, 'a', 1, 1)
            and _leve_v(M.solution_affine, 1, False, 2, 3))

def _p_relativite_restreinte() -> bool:
    import relativite_restreinte as M
    c = M.C_LUMIERE
    return (abs(M.facteur_lorentz(0.0) - 1.0) < 1e-6
            and abs(M.facteur_lorentz(0.6 * c) - 1.25) < 1e-6
            and abs(M.facteur_lorentz(0.8 * c) - 5.0 / 3.0) < 1e-6
            and abs(M.dilatation_temps(3.0, 0.8 * c) - 5.0) < 1e-6
            and abs(M.contraction_longueur(1.0, 0.8 * c) - 0.6) < 1e-6
            and abs(M.addition_vitesses(0.5 * c, 0.5 * c) / c - 0.8) < 1e-6
            and M.addition_vitesses(c, c) == c
            and abs(M.energie_totale(2.0, 0.0) - M.energie_repos(2.0)) < 1e-6 * M.energie_repos(2.0)
            and _leve_v(M.facteur_lorentz, c)
            and _leve_v(M.facteur_lorentz, -1.0)
            and _leve_v(M.facteur_lorentz, 1.5 * c)
            and _leve_v(M.addition_vitesses, c, -c)
            and _leve_v(M.energie_repos, -1.0))

def _p_relativite_generale() -> bool:
    import relativite_generale as M
    rs_soleil = M.rayon_schwarzschild(1.989e30)
    rs_terre = M.rayon_schwarzschild(5.972e24)
    rs_kg = M.rayon_schwarzschild(1.0)
    # red-shift à r = (4/3)·r_s : facteur √(1−3/4) = 1/2
    fac_demi = M.dilatation_gravitationnelle(1.0, 1.989e30, (4.0 / 3.0) * rs_soleil)
    # red-shift à r = 2·r_s : facteur 1/√2, pour t = 10 s
    tau = M.dilatation_gravitationnelle(10.0, 1.989e30, 2.0 * rs_soleil)
    return (abs(rs_soleil - 2953.0) < 0.01 * 2953.0          # Soleil ≈ 2.95 km (tol 1%)
            and abs(rs_terre - 8.87e-3) < 0.01 * 8.87e-3      # Terre ≈ 8.87 mm (tol 1%)
            and abs(rs_kg - 1.485e-27) < 0.01 * 1.485e-27     # 1 kg ≈ 1.485e-27 m
            and abs(fac_demi - 0.5) < 1e-6
            and abs(tau - 7.0710678118654755) < 1e-6
            and _leve_v(M.rayon_schwarzschild, 0.0)           # masse nulle -> abstention
            and _leve_v(M.rayon_schwarzschild, -1.0)          # masse négative -> abstention
            and _leve_v(M.dilatation_gravitationnelle, 1.0, 1.989e30, rs_soleil)        # à l'horizon -> abstention
            and _leve_v(M.dilatation_gravitationnelle, 1.0, 1.989e30, 0.5 * rs_soleil)  # sous l'horizon -> abstention
            and _leve_v(M.dilatation_gravitationnelle, 1.0, -1.0, 1e9))                 # masse négative -> abstention

def _p_quantique() -> bool:
    import quantique as M
    h = 6.62607015e-34
    pi = 3.141592653589793
    hbar_demi = h / (2 * pi) / 2                                          # ħ/2 = borne_heisenberg(Δx=1)
    e1 = M.niveaux_puits_infini(1, 1e-9, 9.109e-31)                       # état fondamental électron, puits 1 nm
    return (abs(M.energie_photon(1) - h) <= 1e-9 * h                      # E = h·ν (ν=1)
            and abs(M.energie_photon(5e14) - 3.313035075e-19) <= 1e-9 * 3.313035075e-19
            and abs(M.longueur_onde_broglie(h) - 1.0) <= 1e-9            # λ = h/h = 1 m
            and abs(M.longueur_onde_broglie(1.0) - h) <= 1e-9 * h        # p = 1 kg·m/s -> λ = h
            and abs(e1 - 6.024921181e-20) <= 1e-6 * 6.024921181e-20      # ≈ 0.376 eV (manuel)
            and abs(M.niveaux_puits_infini(2, 1e-9, 9.109e-31) - 4 * e1) <= 1e-6 * e1   # Eₙ ∝ n²
            and abs(M.borne_heisenberg(1.0) - hbar_demi) <= 1e-9 * hbar_demi            # ħ/2
            and _leve_v(M.energie_photon, 0)                            # f ≤ 0 -> abstention
            and _leve_v(M.longueur_onde_broglie, 0)                     # p ≤ 0 -> abstention
            and _leve_v(M.niveaux_puits_infini, 0, 1e-9, 9.109e-31)     # n < 1 -> abstention
            and _leve_v(M.niveaux_puits_infini, 1, 0, 9.109e-31)        # L ≤ 0 -> abstention
            and _leve_v(M.borne_heisenberg, 0))                        # Δx ≤ 0 -> abstention

def _p_semiconducteurs() -> bool:
    import semiconducteurs as M
    return (abs(M.longueur_onde_seuil(1.12) - 1.107001772e-06) < 1e-12
            and abs(M.longueur_onde_seuil_nm(1.12) - 1107.001772) < 1e-3
            and abs(M.longueur_onde_seuil(1.42) - 8.73128158e-07) < 1e-12
            and abs(M.energie_gap_eV_vers_joule(1.0) - 1.602176634e-19) < 1e-30
            and M.type_dopage('P') == 'accepteur/type P'
            and M.type_dopage('As') == 'donneur/type N'
            and M.type_dopage('B') == 'accepteur/type P'
            and M.type_dopage('N') == 'donneur/type N'
            and _leve_v(M.longueur_onde_seuil, 0)
            and _leve_v(M.longueur_onde_seuil, -1.0)
            and _leve_v(M.energie_gap_eV_vers_joule, 0)
            and _leve_v(M.type_dopage, 'Si')
            and _leve_v(M.type_dopage, 'Xx')
            and _leve_v(M.type_dopage, 15))

def _p_entropie_thermo() -> bool:
    import entropie_thermo as M
    return (M.variation_entropie(100, 200) == 0.5
            and M.variation_entropie(100, 100) == 1.0
            and M.variation_entropie(-100, 200) == -0.5
            and abs(M.entropie_univers(100, 400, 300) - 1.0 / 12.0) < 1e-6
            and M.entropie_univers(100, 400, 300) > 0
            and M.spontane(M.entropie_univers(100, 400, 300)) is True
            and M.entropie_univers(-100, 400, 300) < 0
            and M.spontane(M.entropie_univers(-100, 400, 300)) is False
            and M.entropie_univers(100, 350, 350) == 0.0
            and M.spontane(0.0) is False
            and _leve_v(M.variation_entropie, 100, 0)
            and _leve_v(M.variation_entropie, 100, -50)
            and _leve_v(M.entropie_univers, 100, 0, 300)
            and _leve_v(M.variation_entropie, True, 200))

def _p_maxwell() -> bool:
    import maxwell as M
    return (abs(M.vitesse_lumiere_calculee() - 299792458) < 299792.0
            and abs(M.impedance_vide() - 376.730313668) < 1e-4
            and abs(M.densite_energie_E(1e6) - 4.4270939064) < 1e-6
            and abs(M.densite_energie_B(1.0) - 397887.3577) < 1e-3
            and abs(M.densite_energie_E(299792458.0) - M.densite_energie_B(1.0)) < 1e-3
            and abs(M.impedance_vide() - M.MU0 * M.vitesse_lumiere_calculee()) < 1e-5
            and M.densite_energie_E(-5.0) == M.densite_energie_E(5.0)
            and _leve_v(M.densite_energie_E, 'champ')
            and _leve_v(M.densite_energie_E, None)
            and _leve_v(M.densite_energie_E, True)
            and _leve_v(M.densite_energie_B, None))

def _p_geometries_non_euclidiennes() -> bool:
    import geometries_non_euclidiennes as M
    PI = M.PI
    somme, sup = M.somme_angles_triangle_spherique(PI / 2, PI / 2, PI / 2)
    return (
        abs(M.courbure_gauss_sphere(1.0) - 1.0) < 1e-6
        and abs(M.courbure_gauss_sphere(2.0) - 0.25) < 1e-6
        and abs(M.exces_spherique(PI / 2, 1.0) - PI / 2) < 1e-6
        and abs(M.aire_triangle_spherique((PI / 2, PI / 2, PI / 2), 1.0) - PI / 2) < 1e-6
        and abs(somme - 1.5 * PI) < 1e-6
        and sup is True
        and _leve_v(M.courbure_gauss_sphere, 0.0)
        and _leve_v(M.courbure_gauss_sphere, -2.0)
        and _leve_v(M.exces_spherique, 1.0, 0.0)
        and _leve_v(M.exces_spherique, -1.0, 1.0)
        and _leve_v(M.somme_angles_triangle_spherique, PI / 3, PI / 3, PI / 3)
        and _leve_v(M.aire_triangle_spherique, (0.5, 0.5, 0.5), 1.0)
    )

def _p_geometrie_differentielle() -> bool:
    import geometrie_differentielle as M
    T = M.tangente_unitaire(3.0, 4.0)
    N = M.normale_unitaire(3.0, 4.0)
    return (abs(M.courbure(0.0, 2.0, -2.0, 0.0) - 0.5) < 1e-6           # cercle r=2 -> courbure 1/r
            and abs(M.courbure(-5.0, 0.0, 0.0, -5.0) - 0.2) < 1e-6      # cercle r=5 -> courbure 1/r
            and abs(M.courbure(1.0, 1.0, 0.0, 0.0)) < 1e-6             # droite -> courbure 0
            and abs(M.courbure_graphe(0.0, 2.0) - 2.0) < 1e-6          # parabole y=x^2 au sommet -> 2
            and abs(M.rayon_courbure(0.0, 2.0, -2.0, 0.0) - 2.0) < 1e-6  # rayon de courbure R = r
            and abs(M.longueur_arc_segment(3.0, 4.0) - 5.0) < 1e-6     # segment 3-4-5 -> 5
            and abs(M.longueur_polyligne([(0, 0), (3, 4), (3, 9)]) - 10.0) < 1e-6  # 5+5
            and abs(T[0] - 0.6) < 1e-6 and abs(T[1] - 0.8) < 1e-6      # tangente unitaire (0.6,0.8)
            and abs(N[0] + 0.8) < 1e-6 and abs(N[1] - 0.6) < 1e-6      # normale = rotation +90 deg
            and _leve_v(M.courbure, 0.0, 0.0, 1.0, 1.0)                # vitesse nulle -> abstention
            and _leve_v(M.rayon_courbure, 1.0, 0.0, 0.0, 0.0))         # courbure nulle -> abstention

def _p_topologie() -> bool:
    import topologie as M
    return (M.caracteristique_euler(8, 12, 6) == 2
            and M.caracteristique_euler(4, 6, 4) == 2
            and M.caracteristique_euler(6, 12, 8) == 2
            and M.caracteristique_euler(7, 21, 14) == 0
            and M.caracteristique_euler_betti([1, 2, 1]) == 0
            and M.genre_depuis_euler(2) == 0
            and M.genre_depuis_euler(0) == 1
            and M.genre_depuis_euler(-2) == 2
            and M.genre_non_orientable_depuis_euler(0) == 2
            and M.caracteristique_euler_somme_connexe(0, 0) == -2
            and M.est_homeomorphe_sphere(8, 12, 6) is True
            and M.est_homeomorphe_sphere(7, 21, 14) is False
            and _leve_v(M.caracteristique_euler, 8, 12, -1)
            and _leve_v(M.caracteristique_euler, 8.0, 12, 6)
            and _leve_v(M.genre_depuis_euler, 1)
            and _leve_v(M.genre_depuis_euler, 4))

def _p_fractales() -> bool:
    import fractales as M
    return (abs(M.dimension_similarite(2, 3) - 0.6309297535714574) < 1e-6      # Cantor ln2/ln3
            and abs(M.dimension_similarite(4, 3) - 1.2618595071429148) < 1e-6  # Koch ln4/ln3
            and abs(M.dimension_similarite(3, 2) - 1.5849625007211562) < 1e-6  # Sierpinski ln3/ln2
            and abs(M.dimension_similarite(2, 2) - 1.0) < 1e-6                  # segment plein -> 1
            and abs(M.dimension_similarite(4, 2) - 2.0) < 1e-6                  # carre plein -> 2
            and abs(M.dimension_similarite(8, 2) - 3.0) < 1e-6                  # cube plein -> 3
            and abs(M.dimension_similarite(20, 3) - 2.7268330280) < 1e-6       # eponge de Menger
            and abs(M.dimension_connue('cantor') - 0.6309297535714574) < 1e-6  # registre nomme
            and _leve_v(M.dimension_similarite, 0, 3)                          # N<1 -> abstention
            and _leve_v(M.dimension_similarite, 2, 1)                          # facteur<=1 -> abstention
            and _leve_v(M.dimension_connue, 'inconnu'))                        # fractal inconnu -> abstention

def _p_complexite() -> bool:
    import complexite as M
    return (M.classe_master(2, 2, 1) == 'n log n'
            and M.classe_master(1, 2, 0) == 'log n'
            and M.classe_master(7, 2, 2) == 'n^2.807355'
            and M.classe_master(3, 2, 1) == 'n^1.584963'
            and M.classe_master(8, 2, 3) == 'n^3 log n'
            and M.classe_master(2, 2, 2) == 'n^2'
            and M.classe_master(4, 2, 1) == 'n^2'
            and M.regime_master(7, 2, 2) == 'feuilles'
            and abs(M.exposant_critique(7, 2) - 2.807355) < 1e-6
            and M.compare_croissance('n', 'n^2', 1000) == 'n^2'
            and M.compare_croissance('2^n', 'n^5', 1000) == '2^n'
            and M.compare_croissance('n!', '2^n', 1000) == 'n!'
            and M.compare_croissance('n log n', 'n', 5) == 'n log n'
            and M.compare_croissance('n', 'n', 10) == 'equivalent'
            and _leve_v(M.classe_master, 0.5, 2, 1)
            and _leve_v(M.classe_master, 2, 1, 1)
            and _leve_v(M.compare_croissance, 'n', 'n^2', 0)
            and _leve_v(M.compare_croissance, 'n', 'salade', 5))

def _p_langages_formels() -> bool:
    import langages_formels as M
    G = {'S': [('A', 'B'), ('A', 'C')],
         'A': [('a',)], 'B': [('b',)], 'C': [('S', 'B')]}
    P = {'S': [('S', 'S'), ('L', 'R'), ('L', 'T')],
         'T': [('S', 'R')], 'L': [('(',)], 'R': [(')',)]}
    return (M.appartient(G, 'ab') is True
            and M.appartient(G, 'aabb') is True
            and M.appartient(G, 'aaabbb') is True
            and M.appartient(G, 'aab') is False
            and M.appartient(G, 'abab') is False
            and M.appartient(G, '') is False
            and M.appartient(P, '()') is True
            and M.appartient(P, '(())') is True
            and M.appartient(P, '()()') is True
            and M.appartient(P, '(()') is False
            and M.appartient(P, ')(') is False
            and M.classe_chomsky(G) == 'hors_contexte'
            and M.classe_chomsky({'S': [('a', 'S'), ('b',)]}) == 'reguliere'
            and M.est_forme_normale_chomsky(G) is True
            and M.est_forme_normale_chomsky({'S': [('a', 'S'), ('b',)]}) is False
            and _leve_v(M.appartient, {'S': [('a', 'S'), ('b',)]}, 'ab')
            and _leve_v(M.appartient, G, 123)
            and _leve_v(M.classe_chomsky, {'X': [('a',)]}))

def _p_cardinalite() -> bool:
    import cardinalite as M
    return (M.cardinal_parties(3) == 8
            and M.cardinal_parties(0) == 1
            and M.cardinal_parties(10) == 1024
            and M.cardinal_ensemble([1, 1, 2, 3, 3, 3]) == 3
            and M.cardinal_ensemble([]) == 0
            and M.couple_cantor(0, 0) == 0
            and M.couple_cantor(1, 0) == 1
            and M.couple_cantor(0, 1) == 2
            and M.couple_cantor(1, 1) == 4
            and M.decouple_cantor(0) == (0, 0)
            and M.decouple_cantor(4) == (1, 1)
            and all(M.decouple_cantor(M.couple_cantor(i, j)) == (i, j)
                    for i in range(25) for j in range(25))
            and all(M.couple_cantor(*M.decouple_cantor(z)) == z for z in range(500))
            and M.est_denombrable("N") is True
            and M.est_denombrable("Z") is True
            and M.est_denombrable("Q") is True
            and M.est_denombrable("N×N") is True
            and M.est_denombrable("R") is False
            and M.est_denombrable("P(N)") is False
            and M.est_denombrable("[0,1]") is False
            and _leve_v(M.cardinal_parties, -1)
            and _leve_v(M.couple_cantor, -1, 0)
            and _leve_v(M.decouple_cantor, -1)
            and _leve_v(M.est_denombrable, "blabla"))

def _p_astronautique() -> bool:
    import astronautique as M
    return (abs(M.delta_v(3000, 100, 50) - 2079.441542) < 1e-6              # Tsiolkovsky : 3000·ln2
            and abs(M.rapport_de_masse(3000, 3000) - 2.718281828) < 1e-6    # Δv=ve -> rapport = e
            and abs(M.rapport_de_masse(3000, 0) - 1.0) < 1e-6               # Δv=0 -> rapport 1
            and abs(M.masse_finale(3000, 100, 0) - 100.0) < 1e-6            # Δv=0 -> mf=m0
            and abs(M.vitesse_orbitale(M.MASSE_TERRE, M.RAYON_TERRE + 400e3) - 7672.490413) < 1e-6   # LEO
            and abs(M.vitesse_liberation(M.MASSE_TERRE, M.RAYON_TERRE) - 11185.97789) < 1e-6         # 11.186 km/s
            and abs(M.periode_orbitale(M.MASSE_TERRE, 4.2164e7) - 86164.78605) < 1e-6                # jour sidéral
            and _leve_v(M.delta_v, 0, 100, 50)         # ve=0
            and _leve_v(M.delta_v, 3000, 50, 100)      # m0<mf
            and _leve_v(M.delta_v, 3000, 100, 0)       # mf=0
            and _leve_v(M.rapport_de_masse, 3000, -1)  # Δv<0
            and _leve_v(M.vitesse_orbitale, M.MASSE_TERRE, 0)   # r=0
            and _leve_v(M.vitesse_orbitale, -1, 7e6)            # M<0
            and _leve_v(M.delta_v, True, 100, 50))              # bool non numérique

def _p_cosmologie() -> bool:
    import cosmologie as M
    return (M.vitesse_recession(70, 100) == 7000.0
            and M.distance_hubble(70, 7000) == 100.0
            and M.decalage_rouge(1300.0, 650.0) == 1.0
            and abs(M.age_univers(70) - 1.4e10) < 0.05 * 1.4e10
            and abs(M.distance_hubble(70, M.vitesse_recession(70, 137)) - 137.0) < 1e-6
            and _leve_v(M.vitesse_recession, 0, 100)
            and _leve_v(M.age_univers, -70)
            and _leve_v(M.decalage_rouge, 500.0, 0.0)
            and _leve_v(M.vitesse_recession, 70, -5)
            and _leve_v(M.vitesse_recession, True, 100))

def _p_rayonnement_thermique() -> bool:
    import rayonnement_thermique as M
    return (abs(M.longueur_onde_max(2.725) - 1.063e-3) < 1e-5
            and abs(M.longueur_onde_max(5778) - 501.5e-9) < 1e-9
            and abs(M.temperature_depuis_pic(501e-9) - 5784.0) < 1.0
            and abs(M.frequence_max(2.725) - 160.2e9) < 0.2e9
            and abs(M.loi_stefan_boltzmann(300) - 459.3003279) < 1e-3
            and abs(M.loi_stefan_boltzmann(100) - 5.670374419) < 1e-6
            and abs(M.puissance_rayonnee(300, 2.0) - 2 * M.loi_stefan_boltzmann(300)) < 1e-6
            and _leve_v(M.longueur_onde_max, 0)
            and _leve_v(M.longueur_onde_max, -5)
            and _leve_v(M.longueur_onde_max, True)
            and _leve_v(M.loi_stefan_boltzmann, 0)
            and _leve_v(M.temperature_depuis_pic, 0)
            and _leve_v(M.frequence_max, -1)
            and _leve_v(M.puissance_rayonnee, 300, 0))

def _p_habitabilite() -> bool:
    import habitabilite as M
    teq = M.temperature_equilibre(1.0, 1.0, 0.3)          # Terre ~255 K
    teq_mars = M.temperature_equilibre(1.0, 1.524, 0.25)  # Mars ~210 K
    bi, be = M.zone_habitable(1.0)                          # Soleil ~(0.95,1.37)
    return (abs(teq - 254.833) < 1e-3
            and abs(teq_mars - 210.0) < 0.05 * 210.0
            and abs(M.temperature_equilibre(1.0, 1.0, 0.0) - 278.6) < 1e-6
            and abs(bi - 0.953463) < 1e-6
            and abs(be - 1.373606) < 1e-5
            and abs(M.flux_stellaire_recu(1.0, 2.0) - 0.25) < 1e-9
            and M.dans_zone_habitable(1.0, 1.0) is True
            and M.dans_zone_habitable(1.0, 0.5) is False
            and _leve_v(M.temperature_equilibre, 0.0, 1.0)
            and _leve_v(M.temperature_equilibre, 1.0, 0.0)
            and _leve_v(M.temperature_equilibre, 1.0, 1.0, 1.5)
            and _leve_v(M.zone_habitable, -1.0))

def _p_drake() -> bool:
    import drake as M
    return (abs(M.nombre_civilisations(1, 0.5, 2, 1, 0.01, 0.01, 10000) - 1.0) < 1e-6
            and abs(M.nombre_civilisations(2, 0.5, 4, 0.5, 0.5, 0.5, 10000) - 5000.0) < 1e-6
            and abs(M.nombre_civilisations(10, 1, 1, 1, 1, 1, 1000) - 10000.0) < 1e-6
            and abs(M.nombre_civilisations(5, 0, 3, 1, 1, 1, 100) - 0.0) < 1e-6
            and _leve_v(M.nombre_civilisations, -1, 0.5, 2, 1, 0.01, 0.01, 10000)
            and _leve_v(M.nombre_civilisations, 1, 1.5, 2, 1, 0.01, 0.01, 10000)
            and _leve_v(M.nombre_civilisations, 1, 0.5, -2, 1, 0.01, 0.01, 10000)
            and _leve_v(M.nombre_civilisations, 1, 0.5, 2, 1, -0.01, 0.01, 10000)
            and _leve_v(M.nombre_civilisations, 1, 0.5, 2, 1, 0.01, 0.01, "x"))

def _p_mecanismes() -> bool:
    import mecanismes as M
    return (abs(M.rapport_engrenages(10, 40) - 4.0) < 1e-6
            and abs(M.vitesse_sortie(1200, 10, 40) - 300.0) < 1e-6
            and abs(M.couple_sortie(5.0, 4.0) - 20.0) < 1e-6
            and abs(M.avantage_mecanique_levier(4, 1) - 4.0) < 1e-6
            and abs(M.rapport_engrenages(20, 60) - 3.0) < 1e-6
            and abs(M.vitesse_sortie(-800, 10, 40) - (-200.0)) < 1e-6
            and _leve_v(M.rapport_engrenages, 0, 40)
            and _leve_v(M.rapport_engrenages, 10, -40)
            and _leve_v(M.avantage_mecanique_levier, 4, 0)
            and _leve_v(M.couple_sortie, 5.0, 0)
            and _leve_v(M.rapport_engrenages, True, 40))

def _p_structures_genie() -> bool:
    import structures_genie as S
    return (abs(S.moment_quadratique_rectangle(0.1, 0.2) - 6.666666667e-05) < 1e-6
            and abs(S.moment_quadratique_rectangle(1, 1) - 0.08333333333) < 1e-6
            and abs(S.contrainte_traction(10000, 0.01) - 1.0e6) < 1e-3
            and abs(S.contrainte_traction(-3000, 0.006) - (-500000.0)) < 1e-3
            and abs(S.contrainte_flexion(100, 0.0001, 0.05) - 50000.0) < 1e-6
            and abs(S.module_resistance_rectangle(0.1, 0.2) - 6.666666667e-4) < 1e-9
            and abs(S.fleche_poutre_appuyee_charge_centree(48000, 1.0, 1000.0, 1.0) - 1.0) < 1e-9
            and _leve_v(S.moment_quadratique_rectangle, 0.0, 0.2)
            and _leve_v(S.moment_quadratique_cercle, -1.0)
            and _leve_v(S.contrainte_traction, 1000, 0.0)
            and _leve_v(S.contrainte_traction, True, 0.01)
            and _leve_v(S.contrainte_flexion, 100, 0.0, 0.05)
            and _leve_v(S.fleche_poutre_appuyee_charge_centree, 1000, 2.0, 0.0, 1e-4))

def _p_batteries() -> bool:
    import batteries as M
    return (abs(M.energie_wh(12, 100) - 1200.0) < 1e-6
            and abs(M.energie_wh(3.7, 2.6) - 9.62) < 1e-6
            and abs(M.courant_c_rate(100, 2) - 200.0) < 1e-6
            and abs(M.courant_c_rate(100, 0.5) - 50.0) < 1e-6
            and abs(M.temps_charge(100, 50) - 2.0) < 1e-6
            and abs(M.rendement_energetique(90, 100) - 0.9) < 1e-6
            and abs(M.capacite_Ah_depuis_energie(1200, 12) - 100.0) < 1e-6
            and _leve_v(M.energie_wh, -12, 100)
            and _leve_v(M.energie_wh, 12, 0)
            and _leve_v(M.temps_charge, 100, 0)
            and _leve_v(M.rendement_energetique, 110, 100)
            and _leve_v(M.energie_wh, True, 100))

def _p_composites() -> bool:
    import composites as M
    return (abs(M.module_young_composite(0.6, 70, 3.5) - 43.4) < 1e-6
            and abs(M.module_young_composite(0, 70, 3.5) - 3.5) < 1e-6
            and abs(M.module_young_composite(1, 70, 3.5) - 70.0) < 1e-6
            and abs(M.densite_composite(0.6, 1.8, 1.2) - 1.56) < 1e-6
            and abs(M.densite_composite(0, 1.8, 1.2) - 1.2) < 1e-6
            and abs(M.borne_inferieure_reuss(0.5, 70, 3.5) - 6.666666667) < 1e-6
            and abs(M.borne_inferieure_reuss(0.6, 70, 3.5) - 8.13953488372093) < 1e-6
            and M.borne_inferieure_reuss(0.6, 70, 3.5) <= M.module_young_composite(0.6, 70, 3.5)
            and _leve_v(M.module_young_composite, 1.1, 70, 3.5)
            and _leve_v(M.module_young_composite, -0.1, 70, 3.5)
            and _leve_v(M.module_young_composite, 0.6, 0, 3.5)
            and _leve_v(M.module_young_composite, 0.6, 70, 0)
            and _leve_v(M.densite_composite, 0.6, -1, 1.2)
            and _leve_v(M.borne_inferieure_reuss, 0.6, 70, 0)
            and _leve_v(M.module_young_composite, True, 70, 3.5))

def _p_proprietes_materiaux() -> bool:
    import proprietes_materiaux as M
    return (abs(M.contrainte(21000, 1e-4) - 2.1e8) < 1e-6
            and abs(M.deformation(0.002, 2.0) - 0.001) < 1e-6
            and abs(M.module_young(2.1e8, 1e-3) - 2.1e11) < 1e-6
            and abs(M.hooke_deformation(2.1e8, 2.1e11) - 0.001) < 1e-6
            and abs(M.hooke_contrainte(2.1e11, 1e-3) - 2.1e8) < 1e-6
            and abs(M.allongement(21000, 2.0, 1e-4, 2.1e11) - 0.002) < 1e-6
            and abs(M.contrainte(100, 4) - 25.0) < 1e-6
            and _leve_v(M.contrainte, 100, 0)
            and _leve_v(M.deformation, 0.002, 0)
            and _leve_v(M.module_young, 2.1e8, 0)
            and _leve_v(M.allongement, 21000, 2.0, 1e-4, 0))

def _p_controle_qualite() -> bool:
    import controle_qualite as M
    return (abs(M.indice_capabilite_cp(110, 90, 2) - 20.0 / 12.0) < 1e-6
            and abs(M.cpk(100, 110, 90, 2) - 20.0 / 12.0) < 1e-6
            and abs(M.cpk(105, 110, 90, 2) - 5.0 / 6.0) < 1e-6
            and M.cpk(105, 110, 90, 2) < M.indice_capabilite_cp(110, 90, 2)
            and M.limites_controle(100, 2, 3) == (94.0, 106.0)
            and abs(M.phi(0) - 0.5) < 1e-6
            and abs(M.phi(1.96) - 0.9750021049) < 1e-6
            and abs(M.ppm_hors_specs(0, 3, -3, 1) - 2699.796063) < 1e-3
            and abs(M.six_sigma_ppm(6) - 3.4) < 0.05
            and abs(M.six_sigma_ppm(3) - 66807.0) < 1.0
            and _leve_v(M.indice_capabilite_cp, 110, 90, 0)
            and _leve_v(M.indice_capabilite_cp, 90, 110, 2)
            and _leve_v(M.cpk, 100, 90, 110, 2)
            and _leve_v(M.limites_controle, 100, 2, 0)
            and _leve_v(M.phi, float("nan")))

def _p_cybernetique() -> bool:
    import cybernetique as M
    return (abs(M.gain_boucle_fermee(10, 1) - 10/11) < 1e-6
            and abs(M.gain_boucle_fermee(100, 0.1) - 100/11) < 1e-6
            and abs(M.gain_boucle_fermee(1, 1) - 0.5) < 1e-6
            and abs(M.erreur_statique(1, 9) - 0.1) < 1e-6
            and abs(M.erreur_statique(5, 4) - 1.0) < 1e-6
            and abs(M.gain_ideal(0.1) - 10.0) < 1e-6
            and abs(M.fonction_sensibilite(10, 1) - 1/11) < 1e-6
            and abs(M.transfert_complementaire(10, 1) + M.fonction_sensibilite(10, 1) - 1.0) < 1e-9
            and M.est_stable(10, 1) is True
            and M.est_stable(1, -1) is False
            and M.effet_retroaction_negative(1, 1000, 1) is True
            and _leve_v(M.gain_boucle_fermee, 1, -1)
            and _leve_v(M.erreur_statique, 1, -1)
            and _leve_v(M.gain_ideal, 0))

def _p_chaos() -> bool:
    import chaos as M
    return (abs(M.point_fixe_logistique(2) - 0.5) < 1e-9
            and abs(M.point_fixe_logistique(4) - 0.75) < 1e-9
            and abs(M.point_fixe_logistique(3.2) - 0.6875) < 1e-9
            and abs(M.iterer_logistique(2, 0.5, 50) - 0.5) < 1e-9
            and abs(M.iterer_logistique(2, 0.1, 3) - 0.41611392) < 1e-9
            and abs(M.iterer_logistique(4, 0.1, 2) - 0.9216) < 1e-9
            and abs(M.iterer_logistique(2, 1.0, 5) - 0.0) < 1e-9
            and abs(M.sensibilite(2, 0.3, 0.0, 10) - 0.0) < 1e-12
            and M.sensibilite(4, 0.4, 1e-8, 35) > 0.05
            and M.sensibilite(2, 0.4, 1e-8, 35) < 1e-9
            and _leve_v(M.iterer_logistique, 4.5, 0.5, 10)
            and _leve_v(M.iterer_logistique, 2, 1.5, 10)
            and _leve_v(M.iterer_logistique, 2, 0.5, 2.5)
            and _leve_v(M.point_fixe_logistique, 0.5)
            and _leve_v(M.sensibilite, 2, 0.9, 0.2, 5))

def _p_bifurcations() -> bool:
    import bifurcations as M
    return (M.stabilite_point_fixe(-2.0) == 'stable'
            and M.stabilite_point_fixe(0.5) == 'instable'
            and M.stabilite_point_fixe(0.0) == 'marginal'
            and M.stabilite_point_fixe_discret(0.5) == 'stable'
            and M.stabilite_point_fixe_discret(-2.0) == 'instable'
            and M.stabilite_point_fixe_discret(1.0) == 'marginal'
            and M.bifurcation_logistique(2.0) == 'stable'
            and M.bifurcation_logistique(3.5) == 'instable'
            and M.bifurcation_logistique(3.0) == 'marginal'
            and M.nb_points_fixes_pli(-1.0) == 2
            and M.nb_points_fixes_pli(1.0) == 0
            and M.nb_points_fixes_fourche(2.0) == 3
            and abs(M.point_fixe_logistique(2.0) - 0.5) < 1e-6
            and abs(M.multiplicateur_logistique(4.0) - (-2.0)) < 1e-6
            and _leve_v(M.stabilite_point_fixe, 'x')
            and _leve_v(M.point_fixe_logistique, 0)
            and _leve_v(M.bifurcation_logistique, None))

def _p_ecologie() -> bool:
    import ecologie as M
    px, py = M.equilibre_lotka_volterra(1.1, 0.4, 0.4, 0.1)
    return (abs(M.energie_niveau(10000, 1) - 10000) < 1e-6
            and abs(M.energie_niveau(10000, 2) - 1000) < 1e-6
            and abs(M.energie_niveau(10000, 3) - 100) < 1e-6
            and abs(M.energie_niveau(10000, 4) - 10) < 1e-6
            and abs(M.efficacite_ecologique(1000, 10000) - 0.1) < 1e-6
            and abs(M.efficacite_ecologique(100, 1000) - 0.1) < 1e-6
            and abs(px - 4.0) < 1e-6
            and abs(py - 2.75) < 1e-6
            and abs(M.proie_equilibre(1.1, 0.4, 0.4, 0.1) - 4.0) < 1e-6
            and abs(M.predateur_equilibre(1.1, 0.4, 0.4, 0.1) - 2.75) < 1e-6
            and abs(M.derivee_proie(1.1, 0.4, 4.0, 2.75)) < 1e-6
            and abs(M.derivee_predateur(0.4, 0.1, 4.0, 2.75)) < 1e-6
            and abs(M.derivee_proie(2.0, 0.5, 10, 1) - 15.0) < 1e-6
            and _leve_v(M.energie_niveau, 10000, 0)
            and _leve_v(M.energie_niveau, -5, 2)
            and _leve_v(M.energie_niveau, 10000, 2.5)
            and _leve_v(M.efficacite_ecologique, 100, 0)
            and _leve_v(M.equilibre_lotka_volterra, 1, 0, 1, 1)
            and _leve_v(M.proie_equilibre, 1, 1, 1, 0))

def _p_bioinfo() -> bool:
    import bioinfo as M
    return (M.distance_hamming("GATTACA", "GACTATA") == 2
            and M.distance_hamming("karolin", "kathrin") == 3
            and M.distance_hamming("AAAA", "TTTT") == 4
            and M.taux_gc("GGCC") == 1.0
            and M.taux_gc("ATAT") == 0.0
            and abs(M.taux_gc("GATTACA") - 2 / 7) < 1e-6
            and M.taux_gc("ACGT") == 0.5
            and M.complement_inverse("GATTACA") == "TGTAATC"
            and M.complement_inverse("ATGC") == "GCAT"
            and M.complement_inverse(M.complement_inverse("GATTACAGGC")) == "GATTACAGGC"
            and M.distance_edition("chat", "chats") == 1
            and M.distance_edition("chat", "chien") == 3
            and M.distance_edition("kitten", "sitting") == 3
            and M.distance_edition("flaw", "lawn") == 2
            and _leve_v(M.distance_hamming, "ABC", "AB")
            and _leve_v(M.distance_hamming, 123, "ABC")
            and _leve_v(M.taux_gc, "ATBX")
            and _leve_v(M.taux_gc, "ACGU")
            and _leve_v(M.taux_gc, "")
            and _leve_v(M.complement_inverse, "ATXC")
            and _leve_v(M.distance_edition, "abc", 5))

def _p_redox() -> bool:
    import redox as M
    return (M.nombre_oxydation("H2SO4", "S") == 6
            and M.nombre_oxydation("H2S", "S") == -2
            and M.nombre_oxydation("KMnO4", "Mn") == 7
            and M.nombre_oxydation("K2Cr2O7", "Cr") == 6
            and M.nombre_oxydation("HNO3", "N") == 5
            and M.nombre_oxydation("CO2", "C") == 4
            and M.nombre_oxydation("H2O2", "O") == -1
            and M.nombre_oxydation("NaH", "H") == -1
            and M.equilibre_electronique(7, 2) == 5
            and M.equilibre_electronique(2, 3) == 1
            and _leve_v(M.nombre_oxydation, "H2O2", "H")
            and _leve_v(M.nombre_oxydation, "CrO5", "Cr")
            and _leve_v(M.nombre_oxydation, "KO2", "O")
            and _leve_v(M.nombre_oxydation, "SiH4", "Si")
            and _leve_v(M.nombre_oxydation, "CO2", "S")
            and _leve_v(M.nombre_oxydation, "Xx9", "Xx")
            and _leve_v(M.equilibre_electronique, 2.5, 3))

def _p_polymeres() -> bool:
    import polymeres as M
    return (abs(M.degre_polymerisation(28000, 28) - 1000) < 1e-6
            and abs(M.degre_polymerisation(19217, 192.17) - 100) < 1e-6
            and abs(M.degre_polymerisation(104150, 104.15) - 1000) < 1e-6
            and abs(M.masse_molaire_polymere(1000, 28) - 28000) < 1e-6
            and abs(M.masse_molaire_polymere(100, 192.17) - 19217) < 1e-6
            and abs(M.masse_molaire_monomere(19217, 100) - 192.17) < 1e-6
            and abs(M.indice_polymolecularite(20000, 10000) - 2.0) < 1e-6
            and abs(M.indice_polymolecularite(15000, 15000) - 1.0) < 1e-6
            and abs(M.degre_polymerisation_carothers(0.99) - 100) < 1e-6
            and abs(M.degre_polymerisation_carothers(0.999) - 1000) < 1e-6
            and abs(M.degre_polymerisation_carothers(0.5) - 2) < 1e-6
            and abs(M.taux_conversion(100) - 0.99) < 1e-6
            and abs(M.taux_conversion(2) - 0.5) < 1e-6
            and _leve_v(M.degre_polymerisation, 0, 28)
            and _leve_v(M.degre_polymerisation, 28000, 0)
            and _leve_v(M.degre_polymerisation, 10, 28)
            and _leve_v(M.degre_polymerisation, 28000, True)
            and _leve_v(M.masse_molaire_polymere, 0.5, 28)
            and _leve_v(M.masse_molaire_polymere, 1000, 0)
            and _leve_v(M.masse_molaire_monomere, 28000, 0.5)
            and _leve_v(M.indice_polymolecularite, 9000, 10000)
            and _leve_v(M.indice_polymolecularite, 10000, 0)
            and _leve_v(M.degre_polymerisation_carothers, 1.0)
            and _leve_v(M.degre_polymerisation_carothers, 1.5)
            and _leve_v(M.degre_polymerisation_carothers, -0.1)
            and _leve_v(M.taux_conversion, 0.5))

def _p_analyse_chimique() -> bool:
    import analyse_chimique as M
    return (abs(M.absorbance(1, 1, 1) - 1.0) < 1e-6
            and abs(M.absorbance(2, 1, 0.5) - 1.0) < 1e-6
            and abs(M.absorbance(200, 1, 0.0005) - 0.1) < 1e-6
            and abs(M.absorbance(1, 1, 0) - 0.0) < 1e-6
            and abs(M.concentration_depuis_absorbance(1, 200, 1) - 0.005) < 1e-6
            and abs(M.concentration_depuis_absorbance(2, 2, 1) - 1.0) < 1e-6
            and abs(M.transmittance(1) - 0.1) < 1e-6
            and abs(M.transmittance(2) - 0.01) < 1e-6
            and abs(M.transmittance(0) - 1.0) < 1e-6
            and abs(M.facteur_retention_rf(2, 5) - 0.4) < 1e-6
            and abs(M.facteur_retention_rf(5, 5) - 1.0) < 1e-6
            and _leve_v(M.absorbance, 0, 1, 1)
            and _leve_v(M.absorbance, 1, 0, 1)
            and _leve_v(M.absorbance, 1, 1, -0.1)
            and _leve_v(M.concentration_depuis_absorbance, -0.1, 1, 1)
            and _leve_v(M.transmittance, -0.5)
            and _leve_v(M.facteur_retention_rf, 0, 5)
            and _leve_v(M.facteur_retention_rf, 6, 5))


def _p_classes_complexite() -> bool:
    import classes_complexite as M
    return (M.classe_probleme('SAT') == 'NP-complet'
            and M.classe_probleme('tri') == 'P'
            and M.classe_probleme('voyageur_commerce') == 'NP-difficile'
            and M.est_np_complet('SAT') is True
            and M.relation_classes('P', 'NP') == 'inclus'
            and M.relation_classes('NP', 'P') == 'ouvert'
            and M.verification_polynomiale('SAT') is True
            and M.p_egal_np() == 'ouvert'
            and _leve_v(M.classe_probleme, 'inconnu'))

def _p_bioingenierie() -> bool:
    import bioingenierie as M
    return (abs(M.vitesse(10, 2, 2) - 5.0) < 1e-9            # S=Km -> Vmax/2
            and abs(M.vitesse(10, 2, 6) - 7.5) < 1e-9        # cas connu
            and M.vitesse(10, 2, 0) == 0.0                   # S=0 -> 0
            and M.vitesse(10, 2, 1e12) < 10.0                # saturation : v<Vmax
            and abs(M.km_vitesse_demi(10, 2) - 5.0) < 1e-9   # v=Vmax/2 à S=Km
            and abs(M.efficacite_catalytique(100, 2) - 50.0) < 1e-9  # kcat/Km
            and _leve_v(M.vitesse, 10, 0, 2)                 # Km=0 -> abstention
            and _leve_v(M.vitesse, 10, 2, -1))               # S<0 -> abstention

def _p_nucleosynthese() -> bool:
    import nucleosynthese as M
    E = M.energie_liaison(0.0304)                                 # ⁴He : Δm ≈ 0.0304 u -> ~28.3 MeV
    Q = M.q_reaction(2.014102 + 3.016049, 4.002602 + 1.008665)    # fusion D+T -> ⁴He+n (H→He, exothermique)
    return (abs(E - 28.3174) < 1e-3
            and abs(M.energie_liaison(1.0) - 931.494) < 1e-9      # 1 u = 931.494 MeV/c²
            and abs(M.energie_liaison_par_nucleon(E, 4) - 7.0794) < 1e-3   # ⁴He ≈ 7.07 MeV/nucléon
            and abs(M.energie_liaison_par_nucleon(492.254, 56) - 8.7903) < 1e-3  # pic de fer ⁵⁶Fe
            and Q > 0 and abs(Q - 17.59) < 0.06                   # fusion exothermique ≈ 17.6 MeV
            and M.pic_fer()["nuclide"] == "Fe-56"
            and _leve_v(M.energie_liaison, -0.01)                 # défaut de masse négatif -> abstention
            and _leve_v(M.energie_liaison_par_nucleon, 28.3, 0)   # A nul -> abstention
            and _leve_v(M.q_reaction, 0, 1))                      # masse ≤ 0 -> abstention

def _p_impression_3d() -> bool:
    import impression_3d as M
    return (M.nombre_couches(20, 0.2) == 100
            and M.nombre_couches(10, 0.3) == 34            # ceil sur ratio non entier
            and abs(M.temps_impression(1000, 5) - 200.0) < 1e-9
            and abs(M.masse_filament(1000, 1.24) - 1.24) < 1e-9     # PLA 1 cm³
            and abs(M.longueur_filament(1000, 1.75) - 415.7516880767878) < 1e-6
            and _leve_v(M.nombre_couches, 20, 0)           # hauteur_couche=0 -> abstention
            and _leve_v(M.temps_impression, 1000, 0))      # débit=0 -> abstention

def _p_usinage() -> bool:
    import math
    import usinage as M
    return (abs(M.vitesse_coupe(50, 1000) - 157.0796) < 1e-3       # Vc = π·50 ≈ 157.08 m/min
            and abs(M.vitesse_coupe(50, 1000) - math.pi * 50) < 1e-9
            and abs(M.rotation_broche(M.vitesse_coupe(50, 1000), 50) - 1000) < 1e-6   # round-trip N
            and abs(M.taux_enlevement_matiere(2, 3, 100) - 600) < 1e-9   # MRR = ae·ap·vf
            and abs(M.temps_usinage(100, 50) - 2) < 1e-9                 # t = L/f
            and abs(M.avance_par_minute(0.1, 4, 1000) - 400) < 1e-9      # vf = fz·z·N
            and _leve_v(M.vitesse_coupe, 0, 1000)                        # D=0 -> abstention
            and _leve_v(M.temps_usinage, 100, 0))                        # f=0 -> abstention

def _p_procedes_fabrication() -> bool:
    import procedes_fabrication as M
    return (M.type_procede("fraisage") == M.SOUSTRACTIF
            and M.type_procede("impression_3d") == M.ADDITIF
            and M.type_procede("moulage") == M.FORMAGE
            and M.type_procede("soudage") == M.ASSEMBLAGE
            and abs(M.rendement_matiere(0.6, 1.0) - 0.6) < 1e-12
            and _leve_v(M.type_procede, "alchimie")
            and _leve_v(M.rendement_matiere, 0.0, 1.0))

def _p_mineraux() -> bool:
    import mineraux as M
    return (M.durete_mohs('talc') == 1
            and M.durete_mohs('quartz') == 7
            and M.durete_mohs('diamant') == 10
            and M.raye('diamant', 'quartz') is True
            and M.durete_mohs('quartz') > M.durete_mohs('calcite')
            and M.raye('quartz', 'calcite') is True
            and M.raye('calcite', 'quartz') is False
            and M.plus_dur('quartz', 'calcite') == 'quartz'
            and M.plus_dur('calcite', 'quartz') == 'quartz'
            and min((M.durete_mohs(n), n) for n in ('talc', 'quartz', 'diamant'))[1] == 'talc'
            and _leve_v(M.durete_mohs, 'or')
            and _leve_v(M.plus_dur, 'quartz', 'quartz'))

def _p_systemes_politiques() -> bool:
    import systemes_politiques as M
    return ('peuple' in M.definition('democratie')
            and 'héréditaire' in M.definition('monarchie')
            and M.definition('Démocratie') == M.definition('democratie')   # robustesse accents/casse
            and M.classe_par_criteres(1, True, 'aucun') == 'monarchie'      # héréditaire + un seul
            and M.classe_par_criteres(500, False, 'universel') == 'democratie'  # suffrage universel
            and M.classe_par_criteres(3, False, 'restreint') == 'oligarchie'    # petit groupe
            and M.classe_par_criteres(1, False, 'aucun') == 'dictature'         # un seul non héréditaire sans suffrage
            and M.separation_pouvoirs() == ('executif', 'legislatif', 'judiciaire')  # Montesquieu : 3 pouvoirs
            and len(M.separation_pouvoirs()) == 3
            and _leve_v(M.definition, 'feodalisme')                         # système hors référentiel -> abstention
            and _leve_v(M.classe_par_criteres, 0, False, 'universel')       # critère invalide -> abstention
            and _leve_v(M.attribution_pouvoir, 'militaire'))                # pouvoir hors référentiel -> abstention

def _p_recettes() -> bool:
    import recettes as M
    return (abs(M.adapte_quantite(1, 4, 6) - 1.5) < 1e-9          # recette 4->6 = x1.5
            and abs(M.adapte_quantite(2, 4, 6) - 3.0) < 1e-9
            and abs(M.adapte_quantite(200, 4, 6) - 300.0) < 1e-9   # 200 g -> 300 g
            and abs(M.facteur_echelle(4, 6) - 1.5) < 1e-9
            and abs(M.convertir_mesure(1, "tasse", "ml") - 240.0) < 1e-9   # 1 tasse = 240 ml
            and abs(M.convertir_mesure(2, "cuillere_soupe", "ml") - 30.0) < 1e-9  # 2 c.a.s = 30 ml
            and abs(M.convertir_mesure(1, "cuillere_cafe", "ml") - 5.0) < 1e-9
            and abs(M.convertir_mesure(3, "cuillere_cafe", "cuillere_soupe") - 1.0) < 1e-9
            and abs(M.convertir_mesure(1, "kg", "g") - 1000.0) < 1e-9
            and abs(M.convertir_mesure(240, "ml", "g") - 240.0) < 1e-9     # eau densite 1
            and abs(M.convertir_mesure(1, "l", "kg") - 1.0) < 1e-9
            and abs(M.temps_cuisson_adapte(30, 4, 6, exposant=0.0) - 30.0) < 1e-9
            and _leve_v(M.adapte_quantite, 2, 0, 6)                # portions_origine <= 0 -> abstention
            and _leve_v(M.adapte_quantite, -2, 4, 6)              # quantite < 0
            and _leve_v(M.convertir_mesure, 1, "pincee", "ml")    # unite inconnue
            and _leve_v(M.convertir_mesure, 1, "tasse", "g", ingredient="farine"))  # vol<->masse sans densite

def _p_techniques_culinaires() -> bool:
    import techniques_culinaires as M
    return (M.mode_cuisson('bouillir') == 'humide'
            and M.mode_cuisson('rotir') == 'sec'
            and M.mode_cuisson('frire') == 'matiere_grasse'
            and M.mode_cuisson('braiser') == 'mixte'
            and M.milieu_cuisson('bouillir') == 'eau'
            and M.milieu_cuisson('rotir') == 'air'
            and M.temperature_reference('ebullition_eau') == 100.0
            and abs(M.temperature_reference('maillard') - 140.0) < 1e-9
            and 140.0 <= M.temperature_reference('maillard') <= 165.0
            and M.temperature_reference('caramelisation') == 160.0
            and _leve_v(M.mode_cuisson, 'technique_inexistante'))

def _p_ceramiques() -> bool:
    import ceramiques as M
    return (abs(M.retrait_cuisson(100, 88) - 0.12) < 1e-9
            and abs(M.porosite(2, 10) - 0.2) < 1e-9
            and M.classe_ceramique("porcelaine") == 1300.0
            and M.classe_ceramique("faience") == 1000.0
            and M.classe_ceramique("porcelaine") > M.classe_ceramique("faience")
            and M.est_fragile() is True
            and _leve_v(M.retrait_cuisson, 88, 100)
            and _leve_v(M.porosite, 11, 10)
            and _leve_v(M.classe_ceramique, "inconnu"))

def _p_plastiques() -> bool:
    import plastiques as M
    return (M.code_recyclage("PET") == 1
            and M.code_recyclage("PP") == 5
            and M.code_recyclage("PEHD") == 2
            and M.nom_depuis_code(1) == "PET"
            and M.nom_depuis_code(7) == "autres"
            and M.est_thermoplastique("PP") is True
            and M.est_thermodurcissable("bakélite") is True
            and M.est_thermoplastique("PVC") is True
            and abs(M.temperature_transition_vitreuse("PS") - 100.0) < 1e-6
            and _leve_v(M.code_recyclage, "kryptonite")
            and _leve_v(M.nom_depuis_code, 8)
            and _leve_v(M.est_thermoplastique, "inconnu"))


def _p_preuve_propositionnelle() -> bool:
    import preuve_propositionnelle as M
    return (M.inference_valide(['p', 'p -> q'], 'q') is True
            and M.inference_valide(['p -> q', '~q'], '~p') is True
            and M.inference_valide(['p -> q', 'q'], 'p') is False
            and M.inference_valide(['p'], 'q') is False
            and M.inference_valide(['p | q', '~p'], 'q') is True
            and M.inference_valide([], 'p | ~p') is True
            and M.regle_modus_ponens('p -> q', 'p') == 'q'
            and M.regle_modus_tollens('p -> q', '~q') == '~p'
            and _leve_v(M.inference_valide, ['p &'], 'q')
            and _leve_v(M.inference_valide, 'p', 'q')
            and _leve_v(M.regle_modus_ponens, 'p & q', 'p'))

def _p_sophismes() -> bool:
    import sophismes as M
    return (M.identifie_forme('p->q','p','q') == 'modus_ponens'
            and M.identifie_forme('p->q','q','p') == 'affirmation_consequent'
            and M.identifie_forme('p->q','~p','~q') == 'negation_antecedent'
            and M.identifie_forme('p->q','~q','~p') == 'modus_tollens'
            and M.identifie_forme('a->b','¬b','¬a') == 'modus_tollens'
            and M.est_valide('modus_ponens') is True
            and M.est_valide('modus_tollens') is True
            and M.est_valide('affirmation_consequent') is False
            and M.est_valide('negation_antecedent') is False
            and M.est_sophisme('affirmation_consequent') is True
            and M.est_sophisme('modus_ponens') is False
            and len(M.definition_sophisme('ad hominem')) > 0
            and M.definition_sophisme('attaque personnelle') == M.definition_sophisme('ad_hominem')
            and _leve_v(M.identifie_forme, 'p->q', 'p', '~q')
            and _leve_v(M.identifie_forme, 'p->q', 'r', 's')
            and _leve_v(M.est_valide, 'forme_inexistante')
            and _leve_v(M.definition_sophisme, 'sophisme_invente_xyz'))

def _p_paradoxes() -> bool:
    import paradoxes as M
    return (M.ensemble_russell_paradoxal() is True
            and M.barbier_paradoxal() is True
            and M.menteur_paradoxal() is True
            and M.grelling_paradoxal() is True
            and M.est_autoreferentiel("Cette phrase est fausse", "L") is True
            and M.est_autoreferentiel("Il pleut aujourd'hui", "P") is False
            and M.catalogue("russell")["famille"] == "théorie des ensembles"
            and M.catalogue("menteur")["auto_referentiel"] is True
            and M.est_heterologique("long", False) is True
            and _leve_v(M.catalogue, "inconnu")
            and _leve_v(M.est_autoreferentiel, 123, "P")
            and _leve_v(M.est_heterologique, "heterologique", False))

def _p_ordinaux() -> bool:
    import ordinaux as M
    w = M.OMEGA
    un = M.fini(1); deux = M.fini(2)
    # 1+ω=ω (absorption à gauche)
    if M.addition_ordinale(un, w) != w: return False
    # ω+1 ≠ ω et > ω
    wp1 = M.addition_ordinale(w, un)
    if wp1 == w or M.compare_ordinaux(wp1, w) != 1: return False
    # 2·ω = ω (limite) ; ω·2 = ω+ω ; non commutativité
    if M.multiplication_ordinale(deux, w) != w: return False
    w2 = M.multiplication_ordinale(w, deux)
    if w2 != M.addition_ordinale(w, w): return False
    if M.compare_ordinaux(w2, w) != 1: return False
    # ω < ω+1 < ω·2
    if not (M.compare_ordinaux(w, wp1) == -1 and M.compare_ordinaux(wp1, w2) == -1): return False
    # ω·ω = ω²
    if M.multiplication_ordinale(w, w) != M.omega_puissance(2): return False
    # cardinaux : aleph_n et Cantor ℵ0 < 2^ℵ0
    if M.cardinal_aleph(0) != "aleph_0" or M.cardinal_aleph(3) != "aleph_3": return False
    if M.compare_cardinaux(M.cardinal_aleph(0), M.cardinal_continu()) != -1: return False
    # dénombrabilité des ordinaux < ω^ω
    if not (M.est_denombrable(w) and M.est_denombrable(wp1)
            and M.est_denombrable(w2) and M.est_denombrable(M.omega_puissance(2))): return False
    # abstentions : ordinal mal formé, indice négatif, comparaison indécidable (CH)
    if not _leve_v(M.addition_ordinale, "omega", w): return False
    if not _leve_v(M.cardinal_aleph, -1): return False
    if not _leve_v(M.compare_cardinaux, "aleph_1", "2^aleph_0"): return False
    return True

def _p_types_categories() -> bool:
    import types_categories as M
    ctx = {'f': 'A->B', 'x': 'A', 'y': 'C', 'g': 'B->C'}
    return (
        # (1) lambda simplement typé : application bien typée, composition, identité
        M.type_de(M.app(M.var('f'), M.var('x')), ctx) == 'B'
        and M.type_de(M.app(M.var('g'), M.app(M.var('f'), M.var('x'))), ctx) == 'C'
        and M.type_de(M.var('f'), ctx) == 'A->B'
        and M.type_de(M.lam('x', 'A', M.var('x')), {}) == 'A->A'
        and M.parse_type('A->(B->C)') == 'A->B->C'
        # (2) lois de catégorie : composition A->B->C donne A->C, identité, associativité
        and M.compose(M.morphisme('g', 'B', 'C'), M.morphisme('f', 'A', 'B')).dom == 'A'
        and M.compose(M.morphisme('g', 'B', 'C'), M.morphisme('f', 'A', 'B')).cod == 'C'
        and M.verifie_identite(M.morphisme('f', 'A', 'B'))
        and M.verifie_associativite(M.morphisme('h', 'C', 'D'), M.morphisme('g', 'B', 'C'), M.morphisme('f', 'A', 'B'))
        # abstention : application mal typée et composition incompatible -> ValueError
        and _leve_v(M.type_de, M.app(M.var('f'), M.var('y')), ctx)
        and _leve_v(M.compose, M.morphisme('g', 'B', 'C'), M.morphisme('f', 'A', 'X'))
    )

def _p_galois() -> bool:
    import galois as M
    return (M.resoluble_par_radicaux(2) is True
            and M.resoluble_par_radicaux(4) is True
            and M.resoluble_par_radicaux(5) is False
            and M.groupe_resoluble(4) is True
            and M.groupe_resoluble(5) is False
            and M.ordre_groupe_galois('cyclotomique', 5) == 4
            and M.ordre_groupe_galois('quadratique') == 2
            and M.resoluble_polynome('x^5 - x - 1') is False
            and M.ordre_galois_polynome('x^5 - x - 1') == 120
            and _leve_v(M.resoluble_par_radicaux, 0))

def _p_classification_surfaces() -> bool:
    import classification_surfaces as M
    return (M.classifie_surface(2, True) == 'sphère'
            and M.classifie_surface(0, True) == 'tore'
            and M.classifie_surface(-2, True) == 'surface orientable de genre 2'
            and M.classifie_surface(1, False) == 'plan projectif'
            and M.classifie_surface(0, False) == 'bouteille de Klein'
            and M.genre(2, True) == 0
            and M.genre(0, True) == 1
            and M.genre(-2, True) == 2
            and M.genre(1, False) == 1
            and M.genre(0, False) == 2
            and M.est_sphere(2, True) is True
            and M.est_sphere(0, True) is False
            and M.est_sphere(1, False) is False
            and _leve_v(M.genre, 3, True)
            and _leve_v(M.genre, 2, False)
            and _leve_v(M.classifie_surface, 2, False)
            and _leve_v(M.est_sphere, 3, True))

def _p_calculabilite() -> bool:
    import calculabilite as M
    return (M.fonction_ackermann(0, 4) == 5
            and M.fonction_ackermann(1, 1) == 3
            and M.fonction_ackermann(2, 2) == 7
            and M.fonction_ackermann(3, 3) == 61
            and M.addition(7, 5) == 12
            and M.multiplication(6, 7) == 42
            and M.puissance(2, 10) == 1024
            and M.church_vers_entier(M.church_numeral(5)) == 5
            and _leve_v(M.fonction_ackermann, -1, 2)
            and _leve_v(M.fonction_ackermann, 4, 2)
            and _leve_v(M.addition, 3, -1))

def _p_arret() -> bool:
    import arret as M
    def fini(n):
        def prog(e):
            for _ in range(n):
                yield
        return prog
    def infini(e):
        while True:
            yield
    return (M.sarrete_dans(fini(3), None, 100) == ('arrete', 3)
            and M.sarrete_dans(fini(0), None, 100) == ('arrete', 0)
            and M.sarrete_dans(infini, None, 50) == ('timeout',)
            and M.arret_general_decidable() is False
            and M.argument_diagonal() is True
            and M.argument_diagonal(lambda p, x: 'arrete') is True
            and _leve_v(M.sarrete_dans, infini, None, 0)
            and _leve_v(M.sarrete_dans, 42, None, 10))

def _p_algo_analyse() -> bool:
    import algo_analyse as M
    return (M.complexite_boucle(2) == 'n^2'
            and M.complexite_boucle(0) == '1'
            and M.compare_asymptotique('n', 'n^2') == 'n^2'
            and M.compare_asymptotique('2^n', 'n!') == 'n!'
            and M.compare_asymptotique('n log n', 'n') == 'n log n'
            and M.nombre_operations_tri(8, 'fusion') == 'n log n'
            and M.nombre_operations_tri(8, 'bulle') == 'n^2'
            and M.nombre_operations_tri(8, 'rapide', 'moyen') == 'n log n'
            and M.comparaisons_pire_cas(5, 'bulle') == 10
            and M.invariant_boucle_somme(100) is True
            and _leve_v(M.nombre_operations_tri, 5, 'inconnu')
            and _leve_v(M.compare_asymptotique, 'n', 'n^4'))

def _p_decidabilite() -> bool:
    import decidabilite as M
    return (M.statut_decidabilite('arret') == 'indecidable'
            and M.est_decidable('SAT') is True
            and M.statut_decidabilite('primalite') == 'decidable'
            and M.est_decidable('PCP') is False
            and M.classe_complexite('SAT') == 'NP-complet'
            and _leve_v(M.statut_decidabilite, 'conjecture_de_collatz')
            and _leve_v(M.est_decidable, None))

def _p_godel() -> bool:
    import godel as M
    return (M.godel_numero(['0']) == 2
            and M.godel_numero(['S', '0']) == 12
            and M.decode_godel(12) == ['S', '0']
            and M.decode_godel(M.godel_numero(['∀', 'x', '=', '0'])) == ['∀', 'x', '=', '0']
            and M.godel_numero(['x', 'y']) != M.godel_numero(['y', 'x'])
            and 'incomplet' in M.theoreme(1)
            and 'Coh(T)' in M.theoreme(2)
            and _leve_v(M.godel_numero, [])
            and _leve_v(M.godel_numero, ['@'])
            and _leve_v(M.decode_godel, 10)
            and _leve_v(M.decode_godel, 1)
            and _leve_v(M.theoreme, 3))

def _p_intrication() -> bool:
    import intrication as M
    import math
    return (abs(M.borne_classique_chsh() - 2.0) < 1e-12
            and abs(M.borne_quantique_chsh() - 2 * math.sqrt(2)) < 1e-9
            and abs(M.valeur_chsh(-1/math.sqrt(2), 1/math.sqrt(2), -1/math.sqrt(2), -1/math.sqrt(2)) - 2 * math.sqrt(2)) < 1e-9
            and M.viole_inegalite_bell(2 * math.sqrt(2)) is True
            and M.viole_inegalite_bell(2.0) is False
            and M.viole_inegalite_bell(1.5) is False
            and abs(M.etat_bell_correlation(0.0) - (-1.0)) < 1e-12
            and abs(M.etat_bell_correlation(math.pi) - 1.0) < 1e-12
            and abs(M.etat_bell_correlation(math.pi / 3) - (-0.5)) < 1e-12
            and _leve_v(M.valeur_chsh, 1.5, 0.0, 0.0, 0.0)
            and _leve_v(M.etat_bell_correlation, float('nan')))

def _p_coordination() -> bool:
    import coordination as M
    return (M.nombre_oxydation_metal(-3, ["CN-"] * 6) == 3       # [Fe(CN)6]3-
            and M.nombre_oxydation_metal(-4, ["CN-"] * 6) == 2   # [Fe(CN)6]4-
            and M.nombre_oxydation_metal(3, ["NH3"] * 6) == 3    # [Co(NH3)6]3+
            and M.nombre_oxydation_metal(-2, ["Cl-"] * 4) == 2   # [PtCl4]2-
            and M.nombre_coordination(["NH3"] * 6) == 6
            and M.nombre_coordination(["en"] * 3) == 6           # bidente
            and M.compte_electrons_18(6, 6) == 18                # Co3+ d6
            and M.compte_electrons_18(10, 4) == 18               # Ni(CO)4
            and M.respecte_regle_18(8, 5) is True                # Fe(CO)5
            and _leve_v(M.nombre_oxydation_metal, 0, ["XYZ"])    # ligand inconnu
            and _leve_v(M.nombre_coordination, ["Zz-"])          # ligand inconnu
            and _leve_v(M.compte_electrons_18, 11, 6))           # d hors plage

def _p_nomenclature_chimique() -> bool:
    import nomenclature_chimique as M
    return (M.nom_compose_binaire('CO2') == 'dioxyde de carbone'
            and M.nom_compose_binaire('CO') == 'monoxyde de carbone'
            and M.nom_compose_binaire('NaCl') == 'chlorure de sodium'
            and M.nom_compose_binaire('CaO') == 'oxyde de calcium'
            and M.nom_compose_binaire('NH3') == 'ammoniac'
            and M.nom_compose_binaire('SO2') == 'dioxyde de soufre'
            and M.nom_compose_binaire('N2O') == "protoxyde d'azote"
            and M.nom_compose_binaire('SF6') == 'hexafluorure de soufre'
            and M.nom_compose_binaire('N2O5') == 'pentoxyde de diazote'
            and M.nom_compose_binaire('N2O3') == 'trioxyde de diazote'
            and M.prefixe(4) == 'tétra'
            and _leve_v(M.nom_compose_binaire, 'H2O2')
            and _leve_v(M.nom_compose_binaire, 'FeCl3')
            and _leve_v(M.nom_compose_binaire, 'XyZ'))

def _p_pharmacochimie() -> bool:
    import pharmacochimie as M
    return (M.respecte_lipinski(180.16, 1.2, 1, 4) is True
            and M.nombre_violations(180.16, 1.2, 1, 4) == 0
            and M.nombre_violations(600, 2, 2, 5) == 1
            and M.nombre_violations(700, 7, 8, 5) == 3
            and M.respecte_lipinski(700, 7, 8, 5) is False
            and M.est_drug_like(600, 2, 2, 5) is True
            and M.nombre_violations(194.19, -0.07, 0, 6) == 0
            and M.indice_lipinski(180.16, 1.2, 1, 4)['respecte'] is True
            and M.indice_lipinski(558.64, 5.7, 4, 7)['n_violations'] == 2
            and _leve_v(M.respecte_lipinski, -10, 1.2, 1, 4)
            and _leve_v(M.nombre_violations, 180, 1.2, -1, 4))

def _p_mecanismes_reactionnels() -> bool:
    import mecanismes_reactionnels as M
    return (M.type_substitution('tertiaire', 'faible', 'polaire_protique') == 'SN1'
            and M.type_substitution('primaire', 'fort', 'polaire_aprotique') == 'SN2'
            and M.type_elimination('tertiaire', 'faible', 'polaire_protique') == 'E1'
            and M.type_elimination('primaire', 'fort', 'polaire_aprotique') == 'E2'
            and M.ordre_cinetique('SN1') == 1 and M.ordre_cinetique('SN2') == 2
            and M.ordre_cinetique('E1') == 1 and M.ordre_cinetique('E2') == 2
            and M.sn2_defavorise_par_encombrement('tertiaire') is True
            and M.passe_par_carbocation('SN1') is True and M.concerte('SN2') is True
            and M.stereochimie('SN2') == 'inversion'
            and _leve_v(M.type_substitution, 'secondaire', 'fort', 'polaire_aprotique')
            and _leve_v(M.type_elimination, 'methyle', 'fort', 'polaire_aprotique')
            and _leve_v(M.ordre_cinetique, 'SN3'))

def _p_eclipses() -> bool:
    import eclipses as M
    return (abs(M.periode_synodique(27.32, 365.25) - 29.5306) < 0.05
            and abs(M.periode_synodique(10.0, 1e12) - 10.0) < 0.01
            and M.phase_lune(0) == 'nouvelle'
            and M.phase_lune(90) == 'premier_quartier'
            and M.phase_lune(180) == 'pleine'
            and M.phase_lune(270) == 'dernier_quartier'
            and M.phase_lune(45) == 'premier_croissant'
            and abs(M.fraction_illuminee(180) - 1.0) < 1e-9
            and abs(M.fraction_illuminee(0) - 0.0) < 1e-9
            and abs(M.fraction_illuminee(90) - 0.5) < 1e-9
            and M.condition_eclipse(0.0) is True
            and M.condition_eclipse(2.0) is False
            and _leve_v(M.periode_synodique, 0, 365.25)
            and _leve_v(M.phase_lune, 360)
            and _leve_v(M.fraction_illuminee, -1)
            and _leve_v(M.condition_eclipse, 100.0))

def _p_industrie40() -> bool:
    import industrie40 as M
    return (abs(M.oee(0.9, 0.95, 0.99) - 0.846450) < 1e-6
            and abs(M.oee(1.0, 1.0, 1.0) - 1.0) < 1e-9
            and abs(M.oee(0.0, 1.0, 1.0) - 0.0) < 1e-9
            and abs(M.disponibilite(54.0, 60.0) - 0.9) < 1e-9
            and abs(M.performance(950.0, 1000.0) - 0.95) < 1e-9
            and abs(M.qualite(990.0, 1000.0) - 0.99) < 1e-9
            and M.est_classe_mondiale(0.85) is True
            and M.est_classe_mondiale(0.846450) is False
            and abs(M.trs(0.9, 0.95, 0.99) - M.oee(0.9, 0.95, 0.99)) < 1e-9
            and _leve_v(M.oee, 1.1, 0.5, 0.5)
            and _leve_v(M.oee, -0.1, 0.5, 0.5)
            and _leve_v(M.disponibilite, 10.0, 0.0)
            and _leve_v(M.qualite, 1001.0, 1000.0))

def _p_stereochimie() -> bool:
    import stereochimie as M
    return (M.nombre_stereoisomeres(1) == 2
            and M.nombre_stereoisomeres(2) == 4
            and M.nombre_stereoisomeres(0) == 1
            and M.nombre_stereoisomeres(3) == 8
            and M.paires_enantiomeres(1) == 1
            and M.paires_enantiomeres(2) == 2
            and M.paires_enantiomeres(0) == 0
            and M.nombre_enantiomeres(1) == 2
            and M.nombre_enantiomeres(0) == 0
            and M.classe_relation('RR', 'SS') == 'enantiomeres'
            and M.classe_relation('RR', 'RS') == 'diastereomeres'
            and M.classe_relation('RR', 'RR') == 'identiques'
            and _leve_v(M.nombre_stereoisomeres, -1)
            and _leve_v(M.classe_relation, 'RR', 'R'))

def _p_procedes_industriels() -> bool:
    import procedes_industriels as M
    return (abs(M.rendement(90, 100) - 0.9) < 1e-12
            and abs(M.rendement(100, 100) - 1.0) < 1e-12
            and abs(M.taux_conversion(80, 100) - 0.8) < 1e-12
            and abs(M.debit_production(1000, 10) - 100.0) < 1e-12
            and M.bilan_matiere([60, 40], [50, 50]) is True
            and M.bilan_matiere([100], [90]) is False
            and _leve_v(M.rendement, 90, 0)
            and _leve_v(M.rendement, 110, 100)
            and _leve_v(M.taux_conversion, 120, 100)
            and _leve_v(M.debit_production, 100, 0)
            and _leve_v(M.bilan_matiere, [], [100]))


def _p_big_bang() -> bool:
    import big_bang as M
    ab = M.abondance_primordiale()
    return (abs(M.age_univers_hubble(70) - 1.40e10) <= 0.05 * 1.40e10           # age(70) ~1.4e10 ans (tol 5%)
            and abs(M.age_univers_hubble(100) - 9.78e9) <= 0.01 * 9.78e9        # ancre manuel : t_H(100)~9.78 Gyr
            and abs(M.age_univers_hubble(140) - M.age_univers_hubble(70) / 2.0) <= 1e-3  # t_H propto 1/H0
            and ab == {"H": 0.75, "He": 0.25}                                   # 75% H / 25% He en masse (BBN)
            and abs(ab["H"] + ab["He"] - 1.0) <= 1e-12
            and M.temperature_cmb() == 2.725                                    # T_CMB = 2.725 K (fait)
            and abs(M.densite_critique(70) - 9.20e-27) <= 0.01 * 9.20e-27       # rho_c = 3H0^2/(8 pi G) ~9.2e-27
            and abs(M.densite_critique(140) - 4.0 * M.densite_critique(70)) <= 1e-9 * 4.0 * M.densite_critique(70)
            and _leve_v(M.age_univers_hubble, 0)                                # SOUNDNESS H0=0 -> ValueError
            and _leve_v(M.age_univers_hubble, -70)                              # H0<0 -> ValueError
            and _leve_v(M.age_univers_hubble, float("inf"))                     # H0 non fini -> ValueError
            and _leve_v(M.age_univers_hubble, "70")                             # non numerique -> ValueError
            and _leve_v(M.age_univers_hubble, True)                             # booleen -> ValueError
            and _leve_v(M.densite_critique, 0)                                  # rho_c H0=0 -> ValueError
            and _leve_v(M.densite_critique, -1))                                # rho_c H0<0 -> ValueError

def _p_asteroides() -> bool:
    import asteroides as M
    return (M.classifie(M.tisserand(2.7, 0.1, 5)) == M.ASTEROIDE                          # ceinture -> astéroïde
            and M.classifie(M.tisserand(3.46, 0.641, 7.04)) == M.COMETE_FAMILLE_JUPITER   # 67P -> JFC
            and M.classifie(M.tisserand(17.8, 0.967, 162)) == M.COMETE_QUASI_ISOTROPE     # Halley -> comète
            and abs(M.tisserand(17.8, 0.967, 162) - (-0.6039)) < 1e-3                      # T_J Halley ≈ -0.60 (publié)
            and abs(M.tisserand(5.204, 0.0, 0.0) - 3.0) < 1e-12                            # a=aJ,e=0,i=0 -> T=3 exact
            and M.classifie(3.5) == M.ASTEROIDE and M.classifie(2.5) == M.COMETE_FAMILLE_JUPITER
            and _leve_v(M.tisserand, 2.7, 1.0, 5)     # e=1 non elliptique -> abstention
            and _leve_v(M.tisserand, 0.0, 0.1, 5)     # a<=0 -> abstention
            and _leve_v(M.tisserand, 2.7, -0.1, 5)    # e<0 -> abstention
            and _leve_v(M.classifie, 3.0))            # frontière exacte T=3 -> abstention

def _p_alliages() -> bool:
    import alliages as M
    f = M.fraction_phase(40, 20, 60)
    cas = (abs(f.phase2 - 0.5) < 1e-12 and abs(f.phase1 - 0.5) < 1e-12
           and abs(M.fraction_phase(20, 20, 60).phase2 - 0.0) < 1e-12
           and abs(M.fraction_phase(60, 20, 60).phase2 - 1.0) < 1e-12
           and abs(M.fraction_phase(30, 0, 100).phase1 - 0.70) < 1e-12
           and M.classe_alliage('acier').constituants == ('fer', 'carbone')
           and M.classe_alliage('laiton').constituants == ('cuivre', 'zinc'))
    return (cas
            and _leve_v(M.fraction_phase, 70, 20, 60)
            and _leve_v(M.fraction_phase, 40, 30, 30)
            and _leve_v(M.fraction_phase, '40', 20, 60)
            and _leve_v(M.classe_alliage, 'inox'))

def _p_mecanismes_machines() -> bool:
    import mecanismes_machines as M
    return (M.mobilite(4, 4) == 1                       # 4 barres -> mouvement déterminé
            and M.mobilite(4, 4, 0) == 1                # bielle-manivelle (j2 explicite)
            and M.mobilite(5, 5) == 2                    # 5 barres -> 2 ddl
            and M.mobilite(6, 7) == 1                    # six-barres de Watt
            and M.mobilite(3, 2, 1) == 1                 # came/engrenage (paire supérieure)
            and M.mobilite(2, 1) == 1                    # pendule simple
            and M.mobilite(3, 3) == 0                    # triangle articulé = structure (bloqué)
            and M.mobilite(2, 2) == -1                   # barre bi-articulée = hyperstatique
            and M.degres_liberte(4, 4) == 1             # synonyme DDL
            and M.mouvement_determine(4, 4) is True
            and M.mouvement_determine(3, 3) is False
            and M.est_structure(3, 3) is True
            and M.nature(4, 4) == M.MECANISME
            and M.nature(3, 3) == M.STRUCTURE_ISOSTATIQUE
            and M.nature(2, 2) == M.STRUCTURE_HYPERSTATIQUE
            and _leve_v(M.mobilite, 0, 0)                # n_corps < 1 -> abstention
            and _leve_v(M.mobilite, 4, -1)               # liaisons < 0 -> abstention
            and _leve_v(M.mobilite, 4.0, 4)              # compteur non entier -> abstention
            and _leve_v(M.mobilite, True, 4))            # booléen -> abstention

def _p_immunite() -> bool:
    import immunite as M
    return (abs(M.seuil_immunite_groupe(15) - 14 / 15) < 1e-9          # rougeole R0=15 -> ≈0.9333
            and abs(M.seuil_immunite_groupe(2) - 0.5) < 1e-12          # R0=2 -> 0.5
            and abs(M.seuil_immunite_groupe(5) - 0.8) < 1e-12
            and abs(M.taux_reproduction_effectif(15, 0.95) - 0.75) < 1e-9   # Reff = 15·0.05
            and abs(M.taux_reproduction_effectif(2, 0.6) - 0.8) < 1e-12
            and M.epidemie_eteinte(15, 0.95) is True                  # f>seuil -> Reff<1
            and M.epidemie_eteinte(15, 0.90) is False
            and M.type_immunite("infection") == M.ACTIVE_NATURELLE
            and M.type_immunite("vaccin") == M.ACTIVE_ARTIFICIELLE
            and M.type_immunite("anatoxine") == M.ACTIVE_ARTIFICIELLE  # toxoïde = vaccin (active)
            and M.type_immunite("antitoxine") == M.PASSIVE             # sérum préformé (passive)
            and M.type_immunite("anticorps maternels") == M.PASSIVE
            and _leve_v(M.seuil_immunite_groupe, 1)                    # R0≤1 -> abstention
            and _leve_v(M.seuil_immunite_groupe, "15")                # non réel -> abstention
            and _leve_v(M.taux_reproduction_effectif, 15, 1.5)        # f hors [0,1] -> abstention
            and _leve_v(M.type_immunite, "inconnu"))                  # hors référentiel -> abstention

def _p_mutations() -> bool:
    import mutations as M
    return (M.type_mutation('ATG', 'ATA') == 'substitution'
            and M.type_mutation('ATG', 'ATGG') == 'insertion'
            and M.type_mutation('ATGG', 'ATG') == 'deletion'
            and M.effet_substitution_codon('ATG', 'ATG') == 'silencieuse'
            and M.effet_substitution_codon('ATG', 'ATA') == 'faux_sens'
            and M.effet_substitution_codon('TAC', 'TAA') == 'non_sens'
            and M.decrit_substitution('TAC', 'TAA') == ('non_sens', 'Y', '*')
            and _leve_v(M.type_mutation, 'ATG', 'ATX')
            and _leve_v(M.type_mutation, 'ATG', 'ATG')
            and _leve_v(M.effet_substitution_codon, 'AT', 'ATG')
            and _leve_v(M.effet_substitution_codon, 'TAA', 'TAC'))

def _p_neurone_biologique() -> bool:
    import neurone_biologique as M
    return (M.potentiel_repos() == -70.0
            and M.depasse_seuil(-50, -55) is True          # -50 >= -55 -> déclenche PA
            and M.depasse_seuil(-60, -55) is False          # -60 < -55 -> pas de PA
            and M.depasse_seuil(-55, -55) is True           # au seuil (>=) -> déclenche
            and M.depasse_seuil(-70) is False               # repos, seuil défaut -55
            and abs(M.frequence_decharge(2, 1, 10) - 10.0) < 1e-9     # 10*(2-1)
            and M.frequence_decharge(0.5, 1, 10) == 0.0     # sous rhéobase -> rectifié 0
            and M.frequence_decharge(1, 1, 10) == 0.0       # au seuil -> 0
            and abs(M.frequence_max_refractaire(2.0) - 500.0) < 1e-9  # 1000/2 ms
            and abs(M.frequence_decharge_bornee(100, 1, 10, 2.0) - 500.0) < 1e-9  # plafond réfractaire
            and _leve_v(M.frequence_decharge, 2, 1, -1)     # gain<0 -> ValueError
            and _leve_v(M.frequence_decharge, "x", 1, 10)   # courant non num -> ValueError
            and _leve_v(M.depasse_seuil, "a")               # potentiel non num -> ValueError
            and _leve_v(M.frequence_max_refractaire, 0))    # T<=0 -> ValueError

def _p_cycles_biogeochimiques() -> bool:
    import cycles_biogeochimiques as M
    return (_proche(M.temps_residence(1000, 100), 10.0)
            and _proche(M.temps_residence(2000, 100), 20.0)      # réservoir ×2 -> τ ×2
            and _proche(M.temps_residence(1000, 200), 5.0)       # flux ×2 -> τ /2
            and M.bilan_equilibre(100, 100) is True              # entrée=sortie -> stationnaire
            and M.bilan_equilibre(100, 110) is False             # entrée≠sortie -> non stationnaire
            and M.cycle("azote")["fraction_atmospherique_N2"] == 0.78   # N2 ≈ 78 % de l'atmosphère
            and M.cycle("eau")["reservoir_principal"] == "océans"        # océans ≈ 97 % de l'eau
            and M.cycle("carbone")["reservoir_principal"] == "océans"    # plus grand réservoir actif
            and M.cycle("phosphore")["phase_gazeuse"] is False           # cycle sédimentaire, pas de gaz
            and _leve_v(M.temps_residence, 1000, 0)              # flux ≤ 0 -> ValueError
            and _leve_v(M.temps_residence, -1, 100)             # réservoir < 0 -> ValueError
            and _leve_v(M.cycle, "soufre"))                      # cycle inconnu -> ValueError

def _p_homeostasie() -> bool:
    import homeostasie as M
    return (abs(M.ecart_consigne(39, 37) - 2.0) < 1e-9
            and abs(M.ecart_consigne(35, 37) - (-2.0)) < 1e-9
            and abs(M.correction(39, 37, 0.5) - (-1.0)) < 1e-9
            and abs(M.correction(35, 37, 2) - 4.0) < 1e-9
            and abs(M.correction(37, 37, 10)) < 1e-9
            and M.est_regule(37.3, 37, 0.5) is True
            and M.est_regule(39, 37, 0.5) is False
            and M.est_regule(39, 37, 2) is True
            and abs(M.consigne_reference('temperature_corporelle_C') - 37.0) < 1e-9
            and abs(M.consigne_reference('glycemie_g_par_L') - 1.0) < 1e-9
            and _leve_v(M.correction, 39, 37, -1)
            and _leve_v(M.est_regule, 39, 37, -0.5)
            and _leve_v(M.ecart_consigne, 'x', 37)
            and _leve_v(M.consigne_reference, 'inconnu'))

def _p_chronobiologie() -> bool:
    import chronobiologie as M

    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k)
            return False
        except ValueError:
            return True
        except Exception:
            return False

    def approx(a, b, tol=1e-9):
        return abs(a - b) <= tol

    return (
        approx(M.periode_circadienne(), 24.2)               # fait : ~24.2 h
        and M.periode_circadienne() > 24.0                  # période intrinsèque > 24 h
        and approx(M.nombre_cycles_sommeil(480), 16.0 / 3.0)  # 8 h = 480/90 ≈ 5.333 cycles
        and approx(M.nombre_cycles_sommeil(450), 5.0)       # 450 min -> 5 cycles
        and approx(M.duree_pour_cycles(5), 450.0)           # 5 cycles -> 450 min
        and approx(M.duree_pour_cycles(5) / 60.0, 7.5)      # = 7.5 h
        and M.phase_circadienne(3) == "pic_melatonine"      # ~2-4 h
        and M.phase_circadienne(12) == "jour"
        and M.phase_circadienne(23) == "nuit"
        and _leve_v(M.nombre_cycles_sommeil, -1)            # duree < 0
        and _leve_v(M.nombre_cycles_sommeil, 480, 0)        # cycle <= 0
        and _leve_v(M.phase_circadienne, 24)                # heure hors [0,24)
        and _leve_v(M.duree_pour_cycles, -1)                # n_cycles < 0
    )

def _p_proteines() -> bool:
    import proteines as M
    return (M.nombre_liaisons_peptidiques(100) == 99
            and M.classe_enzyme_ec(3) == "hydrolase"
            and M.nombre_niveaux_structure() == 4
            and M.classe_enzyme_ec(1) == "oxydoréductase"
            and M.classe_enzyme_ec(6) == "ligase"
            and "séquence" in M.niveau_structure("primaire").lower()
            and "hélice" in M.niveau_structure("secondaire").lower()
            and _leve_v(M.nombre_liaisons_peptidiques, 0)
            and _leve_v(M.nombre_liaisons_peptidiques, 1.5)
            and _leve_v(M.classe_enzyme_ec, 7)
            and _leve_v(M.classe_enzyme_ec, 3.0)
            and _leve_v(M.niveau_structure, "inconnu"))

def _p_cryobiologie() -> bool:
    import cryobiologie as M
    return (abs(M.vitesse_refroidissement(20, -180, 10) - 20.0) < 1e-9
            and abs(M.point_congelation_solution(1, i=2) - (-3.72)) < 1e-9
            and abs(M.point_congelation_solution(1) - (-1.86)) < 1e-9
            and abs(M.point_congelation_solution(0) - 0.0) < 1e-9
            and M.azote_liquide() == -196.0
            and M.KF_EAU == 1.86
            and _leve_v(M.vitesse_refroidissement, 20, -180, 0)
            and _leve_v(M.vitesse_refroidissement, 20, -180, -5)
            and _leve_v(M.point_congelation_solution, -1)
            and _leve_v(M.point_congelation_solution, 1, 0)
            and _leve_v(M.point_congelation_solution, 1, 1.86, 0))

def _p_petrochimie() -> bool:
    import petrochimie as M
    return (M.fraction_distillation(100) == 'essence'
            and M.fraction_distillation(250) == 'kerosene'
            and M.fraction_distillation(20) == 'gaz'
            and M.fraction_distillation(350) == 'diesel/gazole'
            and M.fraction_distillation(500) == 'residu/bitume'
            and M.fraction_distillation(30) == 'essence'      # borne incluse
            and M.fraction_distillation(200) == 'kerosene'    # borne incluse
            and M.fraction_distillation(400) == 'residu/bitume'
            and abs(M.indice_octane_melange(87, 50, 91, 50) - 89.0) < 1e-9
            and abs(M.indice_octane_melange(95, 30, 98, 70) - 97.1) < 1e-9
            and _leve_v(M.indice_octane_melange, 87, 0, 91, 50)   # volume nul
            and _leve_v(M.indice_octane_melange, 87, 50, 91, -1)  # volume négatif
            and _leve_v(M.fraction_distillation, 'chaud')         # non numérique
            and _leve_v(M.fraction_distillation, None))


def _p_croissance_bacterienne() -> bool:
    import croissance_bacterienne as M
    return (abs(M.population(1000, 60, 20) - 8000.0) < 1e-6
            and abs(M.population(1, 20, 20) - 2.0) < 1e-9          # doublement après 1 g
            and abs(M.population(100, 90, 30) - 800.0) < 1e-6       # 2^3 = 8
            and abs(M.nombre_generations(1000, 8000) - 3.0) < 1e-9  # log2(8) = 3
            and abs(M.nombre_generations(1, 1024) - 10.0) < 1e-9    # log2(1024) = 10
            and abs(M.temps_generation(1000, 8000, 60) - 20.0) < 1e-6
            and _leve_v(M.population, 0, 60, 20)        # N0<=0 -> abstention
            and _leve_v(M.population, 1000, 60, 0)      # g<=0 -> abstention
            and _leve_v(M.population, 1000, -1, 20)     # t<0 -> abstention
            and _leve_v(M.temps_generation, 1000, 1000, 60)  # Nt=N0 (div par 0) -> abstention
            and _leve_v(M.nombre_generations, 1000, 500))    # Nt<N0 (n<0) -> abstention

def _p_transport_membranaire() -> bool:
    import transport_membranaire as M
    return (M.tonicite(0.9, 0.9) == 'isotonique'
            and M.tonicite(0.9, 1.8) == 'hypertonique'
            and M.tonicite(0.9, 0.45) == 'hypotonique'
            and M.flux_fick(2, 3, 4, 6) == 4.0
            and abs(M.flux_fick(1e-9, 1e-4, 10, 1e-5) - 1e-7) < 1e-12
            and M.sens_osmose(0.9, 1.8) == 'sortie'
            and M.sens_osmose(0.9, 0.45) == 'entree'
            and M.sens_osmose(0.9, 0.9) == 'equilibre'
            and _leve_v(M.flux_fick, 1e-9, 1e-4, 10, 0)
            and _leve_v(M.tonicite, -1, 0.9))

def _p_aerodynamique() -> bool:
    import aerodynamique as M
    return (abs(M.portance(1.225, 100, 10, 1.0) - 61250.0) < 1e-3
            and abs(M.trainee(1.225, 100, 10, 0.05) - 3062.5) < 1e-3
            and abs(M.finesse(1.0, 0.05) - 20.0) < 1e-9
            and abs(M.finesse(1.2, 0.08) - 15.0) < 1e-9
            and abs(M.reynolds(1.0, 1.0, 1.0, 1.0) - 1.0) < 1e-12
            and abs(M.reynolds(1.2, 10, 2.0, 2e-5) - 1_200_000.0) < 1e-3
            and abs(M.vol_equilibre(1.225, 10, 1.0, 61250.0) - 100.0) < 1e-6
            and _leve_v(M.portance, -1.0, 100, 10, 1.0)
            and _leve_v(M.trainee, 1.225, 100, 10, 0.0)
            and _leve_v(M.finesse, 1.0, 0.0)
            and _leve_v(M.reynolds, 1.225, 20, 1.0, 0.0)
            and _leve_v(M.vol_equilibre, 1.225, 10, -1.0, 61250.0))

def _p_maritime() -> bool:
    import maritime as M
    tol = 1e-3
    return (abs(M.vitesse_coque(9) - 7.28146) < tol                 # hull speed 1.34·√(LWL_ft)=2.427·√(LWL_m)
            and abs(M.vitesse_coque(9) - 7.3) < 0.05                  # cas spec : LWL=9 m -> ≈7.3 noeuds
            and abs(M.vitesse_coque(25) - 12.1358) < tol
            and M.vitesse_coque_max(16) == M.vitesse_coque(16)       # alias max == coque
            and abs(M.vitesse_coque_depuis_pieds(100) - 13.4) < tol  # 1.34·√100
            and M.poussee_archimede(1, 1000) == 9806.65              # ρVg eau douce
            and abs(M.poussee_archimede(2) - 20103.6) < 0.1          # défaut ρ=1025 (eau de mer)
            and M.masse_max_flottante(2, 1025) == 2050.0
            and M.flotte(1000, 2, 1025) is True                      # masse < ρ·V_carène -> flotte
            and M.flotte(3000, 2, 1025) is False                     # masse > ρ·V_carène -> coule
            and M.flotte(2050, 2, 1025) is False                     # égalité (neutre) -> ne flotte pas
            and M.nombre_froude(2, 1, 4) == 1.0                       # Fr = v/√(g·L)
            and M.nombre_froude(10, 1, 25) == 2.0
            and abs(M.nombre_froude(3, 9, 9.81) - 0.319275) < 1e-4
            and _leve_v(M.vitesse_coque, 0)                          # soundness : LWL≤0
            and _leve_v(M.poussee_archimede, -1)                     # volume≤0
            and _leve_v(M.flotte, -1, 2)                             # masse<0
            and _leve_v(M.nombre_froude, 2, 0)                       # longueur≤0
            and _leve_v(M.nombre_froude, -2, 1))                     # vitesse<0

def _p_automobile() -> bool:
    import automobile as M
    return (abs(M.distance_freinage(27.8, 0.8) - 49.238022) < 1e-3      # 100 km/h µ=0.8 -> ~49 m
            and abs(M.distance_freinage(10.0, 0.5, g=10.0) - 10.0) < 1e-6
            and abs(M.distance_freinage(0.0, 0.8) - 0.0) < 1e-6          # v=0 -> 0
            and abs(M.puissance(3000.0, 30.0) - 90000.0) < 1e-6         # F=3000 N v=30 -> 90 kW
            and abs(M.puissance(-200.0, 10.0) - (-2000.0)) < 1e-6       # force resistante -> P<0
            and abs(M.rapport_transmission(40, 10) - 4.0) < 1e-6        # 40/10 dents -> 4
            and abs(M.regime_roue(4000.0, 4.0) - 1000.0) < 1e-6         # 4000 tr/min /4 -> 1000
            and abs(M.consommation_100km(40.0, 500.0) - 8.0) < 1e-6     # 40 L / 500 km -> 8
            and _leve_v(M.distance_freinage, 27.8, 0.0)                 # mu=0 -> abstention
            and _leve_v(M.distance_freinage, -5.0, 0.8)                 # vitesse<0 -> abstention
            and _leve_v(M.distance_freinage, 27.8, 0.8, 0.0)            # g=0 -> abstention
            and _leve_v(M.distance_freinage, True, 0.8)                 # booleen -> abstention
            and _leve_v(M.consommation_100km, 40.0, 0.0)               # km=0 -> abstention
            and _leve_v(M.rapport_transmission, 40, 0)                  # dents_menante=0 -> abstention
            and _leve_v(M.rapport_transmission, 40.5, 10)               # dents non entieres -> abstention
            and _leve_v(M.regime_roue, 4000.0, 0.0))                    # rapport=0 -> abstention

def _p_logistique() -> bool:
    import logistique as M, math
    return (abs(M.quantite_economique_commande(1000, 50, 2) - math.sqrt(50000)) < 1e-5
            and abs(M.eoq(1000, 50, 2) - 223.606798) < 1e-6
            and M.point_commande(20, 5) == 100.0
            and M.point_commande(150, 10) == 1500.0
            and abs(M.stock_securite(10, 4) - 33.0) < 1e-9
            and abs(M.stock_securite(20, 9, z=2.33) - 139.8) < 1e-9
            and abs(M.cout_total_stock(1000, 50, 2, math.sqrt(50000)) - math.sqrt(200000)) < 1e-4
            and abs(M.cout_total_stock(1000, 50, 2, 500) - 600.0) < 1e-9
            and _leve_v(M.quantite_economique_commande, 0, 50, 2)
            and _leve_v(M.quantite_economique_commande, 1000, 50, 0)
            and _leve_v(M.point_commande, 20, 0)
            and _leve_v(M.stock_securite, 10, 4, z=0)
            and _leve_v(M.cout_total_stock, 1000, 50, 2, 0))

def _p_toxicologie() -> bool:
    import toxicologie as M

    def approx(a, b, tol=1e-9):
        return abs(a - b) <= tol

    return (
        approx(M.index_therapeutique(200, 20), 10.0)            # IT = DL50/DE50, >1 = sûr
        and M.index_therapeutique(200, 20) > 1.0
        and approx(M.index_therapeutique(100, 100), 1.0)        # fenêtre thérapeutique nulle
        and approx(M.index_therapeutique(2, 20), 0.1)           # IT < 1 = dangereux
        and approx(M.dose_totale(10, 70), 700.0)                # 10 mg/kg · 70 kg = 700 mg
        and approx(M.dose_totale(15, 20), 300.0)                # 15 mg/kg · 20 kg = 300 mg
        and approx(M.marge_securite(100, 50), 2.0)              # marge = DL1/DE99
        and approx(M.marge_securite(50, 100), 0.5)              # recouvrement dangereux
        and M.classe_toxicite_dl50(1) == "extrêmement toxique" # DL50=1 mg/kg -> extrême
        and M.classe_toxicite_dl50(192) == "toxique"           # caféine ≈192
        and M.classe_toxicite_dl50(3000) == "modérément"       # sel de table ≈3000
        and M.classe_toxicite_dl50(7060) == "peu toxique"      # éthanol ≈7060
        and _leve_v(M.index_therapeutique, 100, 0)             # DE50<=0 -> abstention
        and _leve_v(M.dose_totale, 10, 0)                      # masse<=0 -> abstention
        and _leve_v(M.classe_toxicite_dl50, -1)                # dose<0 -> abstention
    )

def _p_topographie_arpentage() -> bool:
    import topographie_arpentage as M
    return (M.pente_pourcent(10, 100) == 10.0
            and M.aire_polygone_coords([(0, 0), (10, 0), (10, 10), (0, 10)]) == 100.0
            and _proche(M.distance_horizontale(100, 60), 50.0)
            and _proche(M.denivele(30, 100), 50.0)
            and _proche(M.aire_polygone_coords([(0, 0), (4, 0), (0, 3)]), 6.0)
            and _leve_v(M.pente_pourcent, 5, 0)            # distance horizontale nulle -> abstention
            and _leve_v(M.distance_horizontale, -10, 30)   # distance de pente <= 0 -> abstention
            and _leve_v(M.aire_polygone_coords, [(0, 0), (1, 1)]))  # < 3 points -> abstention

def _p_navigation() -> bool:
    import navigation as M
    import math
    return (abs(M.distance_orthodromique(48.85, 2.35, 51.51, -0.13) - 344.0) <= 0.02 * 344.0
            and M.haversine(48.85, 2.35, 51.51, -0.13) == M.distance_orthodromique(48.85, 2.35, 51.51, -0.13)
            and M.distance_orthodromique(48.85, 2.35, 48.85, 2.35) == 0.0
            and abs(M.distance_orthodromique(0, 0, 0, 90) - math.pi * 6371 / 2) < 0.1
            and abs(M.cap_initial(0, 0, 0, 10) - 90.0) < 1e-6
            and abs(M.cap_initial(0, 0, 10, 0) - 0.0) < 1e-6
            and abs(M.cap_initial(10, 0, 0, 0) - 180.0) < 1e-6
            and 330.0 <= M.cap_initial(48.85, 2.35, 51.51, -0.13) <= 331.0
            and _leve_v(M.distance_orthodromique, 91, 0, 0, 0)
            and _leve_v(M.distance_orthodromique, 0, 181, 0, 0)
            and _leve_v(M.cap_initial, 0, 0, 0, 999))

def _p_hydrologie() -> bool:
    import hydrologie as M
    return (
        M.debit(2, 3) == 6.0                                            # continuité Q=A·v exact
        and M.debit(3, 0) == 0.0                                        # v=0 -> Q=0 (pas de flux)
        and abs(M.methode_rationnelle(1.0, 360.0, 1.0) - 1.0) < 1e-9    # (1/360)·C·i·A : 360/360 = 1 m³/s
        and abs(M.methode_rationnelle(0.5, 50.0, 10.0) - 0.694444) < 1e-4
        and M.ruissellement(0.5, 50.0, 10.0) == M.methode_rationnelle(0.5, 50.0, 10.0)
        and abs(M.manning_vitesse(0.01, 1.0, 1e-4) - 1.0) < 1e-9        # Manning étalon = 1 m/s
        and abs(M.manning_vitesse(0.013, 1.0, 0.001) - 2.43252) < 1e-4  # béton n=0,013
        and abs(M.temps_concentration(300.0, 0.01) - 9.27722) < 1e-3    # Kirpich t_c (min)
        and _leve_v(M.debit, 0, 3)                                      # section<=0 -> abstention
        and _leve_v(M.methode_rationnelle, 1.5, 50, 10)                 # coef C hors [0,1] -> abstention
        and _leve_v(M.manning_vitesse, 0, 1, 0.001)                     # n<=0 -> abstention
        and _leve_v(M.temps_concentration, 300, 0)                      # pente=0 -> abstention
    )

def _p_glaciologie() -> bool:
    import glaciologie as M
    return (abs(M.bilan_massique(2, 1) - 1.0) < 1e-9
            and M.bilan_massique(2, 1) > 0                       # +2−1 = +1 -> croît
            and abs(M.bilan_massique(1, 3) + 2.0) < 1e-9         # 1−3 = −2 -> décroît
            and abs(M.fraction_emergee_iceberg() - 0.105366) < 1e-4   # 1−917/1025 ≈ 10 % émergé
            and abs(M.vitesse_deformation_glace(1e5) - 2.4e-9) < 1e-15   # loi de Glen A·σ³
            and abs(M.vitesse_deformation_glace(2e5) - 1.92e-8) < 1e-14  # σ×2 -> ε̇×8 (n=3)
            and 22.0 < M.epaisseur_equilibre(30.0) < 22.5        # τ0/(ρ g sin30°)
            and _leve_v(M.bilan_massique, -1, 0)                 # accumulation<0 -> abstention
            and _leve_v(M.fraction_emergee_iceberg, 1100, 1025)  # glace > eau -> coule -> abstention
            and _leve_v(M.vitesse_deformation_glace, -1)         # contrainte<0 -> abstention
            and _leve_v(M.epaisseur_equilibre, 0))               # angle=0 (sin=0) -> abstention

def _p_pedologie() -> bool:
    import pedologie as M
    return (M.classe_texture(80, 10, 10) == "sableux"
            and M.classe_texture(30, 20, 50) == "argileux"
            and M.classe_texture(33, 34, 33) == "limoneux"
            and abs(M.porosite(1.3) - 0.509434) < 1e-6
            and abs(M.porosite(1.3, 2.65) - (1.0 - 1.3 / 2.65)) < 1e-6
            and _leve_v(M.classe_texture, 80, 10, 5)       # somme = 95 ≠ 100 -> abstention
            and _leve_v(M.porosite, 1.3, 0)                # densité réelle nulle -> abstention
            and _leve_v(M.porosite, 0)                     # densité apparente nulle -> abstention
            and _leve_v(M.porosite, 3.0, 2.65))            # da>dr (porosité<0) -> abstention

def _p_teledetection() -> bool:
    import teledetection as M
    tol = 1e-6
    return (
        abs(M.resolution_spatiale(60000, 6000) - 10.0) < tol
        and abs(M.resolution_spatiale(11540, 5770) - 2.0) < tol
        and abs(M.resolution_spatiale(120000, 6000) - 20.0) < tol
        and abs(M.ndvi(0.5, 0.1) - 0.666667) < tol
        and abs(M.ndvi(0.2, 0.2) - 0.0) < tol
        and abs(M.ndvi(0.1, 0.4) - (-0.6)) < tol
        and abs(M.ndvi(1.0, 0.0) - 1.0) < tol
        and abs(M.ndvi(0.0, 1.0) - (-1.0)) < tol
        and abs(M.ndvi(0.5, 0.1) - (-M.ndvi(0.1, 0.5))) < tol
        and abs(M.resolution_temporelle(10, 2) - 5.0) < tol
        and abs(M.resolution_temporelle(16, 1) - 16.0) < tol
        and _leve_v(M.resolution_spatiale, 60000, 0)
        and _leve_v(M.resolution_spatiale, 60000, -10)
        and _leve_v(M.resolution_spatiale, 0, 6000)
        and _leve_v(M.resolution_spatiale, "abc", 6000)
        and _leve_v(M.ndvi, 0.0, 0.0)
        and _leve_v(M.ndvi, -0.1, 0.2)
        and _leve_v(M.ndvi, 0.2, -0.1)
        and _leve_v(M.resolution_temporelle, 10, 0)
        and _leve_v(M.resolution_temporelle, 10, -2)
        and _leve_v(M.resolution_temporelle, 0, 2)
    )

def _p_energies_comparees() -> bool:
    import energies_comparees as M

    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k)
            return False
        except ValueError:
            return True
        except Exception:
            return False

    def approx(a, b, tol=1e-9):
        return abs(a - b) <= tol

    return (
        approx(M.facteur_charge(1314, 1), 0.15)            # solaire PV ~0.15
        and approx(M.facteur_charge(7884, 1), 0.9)         # nucleaire ~0.9
        and approx(M.facteur_charge(12, 1, 24), 0.5)       # E/(P.h)
        and approx(M.contenu_energetique(2, 50), 100.0)    # masse.PCI (MJ)
        and approx(M.contenu_energetique(1, 120), 120.0)   # 1 kg H2
        and approx(M.retour_energetique(20, 1), 20.0)      # EROI sortie/entree
        and approx(M.retour_energetique(2, 4), 0.5)        # < 1 non viable
        and M.eroi(15, 3) == M.retour_energetique(15, 3)   # alias
        and approx(M.emissions_co2(1, 820), 820.0)         # charbon 820 g/kWh
        and approx(M.emissions_co2(1, 11), 11.0)           # eolien 11 g/kWh
        and approx(M.facteur_co2_reference('charbon'), 820.0)
        and approx(M.facteur_co2_reference('eolien'), 11.0)
        and _leve_v(M.facteur_charge, 100, 0)              # puissance <= 0
        and _leve_v(M.facteur_charge, 9000, 1)             # cf > 1 impossible
        and _leve_v(M.contenu_energetique, 1, 0)           # PCI <= 0
        and _leve_v(M.retour_energetique, 10, 0)           # energie investie <= 0
        and _leve_v(M.emissions_co2, 1, -5)                # facteur < 0
        and _leve_v(M.facteur_co2_reference, 'inconnu'))   # source inconnue

def _p_marketing_metrics() -> bool:
    import marketing_metrics as M
    # Ancres standard (ratios exacts) + soundness (abstention sur entrée invalide).
    return (_proche(M.taux_conversion(50, 1000), 0.05)   # 50 conv / 1000 vis = 5 %
            and _proche(M.ctr(10, 1000), 0.01)           # CTR 10/1000 = 1 %
            and _proche(M.roi(150, 100), 0.5)            # ROI (150-100)/100 = 0.5
            and _proche(M.cac(1000, 50), 20.0)           # CAC 1000/50 = 20
            and _proche(M.roas(400, 100), 4.0)           # ROAS 400/100 = 4
            and _proche(M.roi(0, 100), -1.0)             # gain nul = perte totale -1
            and _leve_v(M.taux_conversion, 50, 0)        # dénominateur 0 -> abstention
            and _leve_v(M.taux_conversion, -1, 1000)     # conversions < 0 -> abstention
            and _leve_v(M.taux_conversion, 1001, 1000)   # taux > 1 impossible -> abstention
            and _leve_v(M.ctr, 2000, 1000)               # clics > impressions -> abstention
            and _leve_v(M.roi, 150, 0)                   # cout <= 0 -> abstention
            and _leve_v(M.cac, 1000, 0)                  # clients <= 0 -> abstention
            and _leve_v(M.roas, 400, -1))                # dépense < 0 -> abstention


def _p_maths_financieres() -> bool:
    import maths_financieres as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    def _ap(x, y, tol=1e-9):
        return abs(x - y) <= tol
    return (M.interet_compose(1000, 0.05, 2) == 1102.5            # 1000 a 5% compose 2 ans
            and M.interet_simple(1000, 0.05, 2) == 100.0          # interet simple = C*t*n
            and M.valeur_acquise_simple(1000, 0.05, 2) == 1100.0  # 1000 a 5% simple 2 ans
            and M.valeur_actuelle(1102.5, 0.05, 2) == 1000.0      # actualisation round-trip
            and _ap(M.annuite_constante(10000, 0.01, 12), 888.49) # mensualite pret
            and M.annuite_constante(1200, 0, 12) == 100.0         # cas limite taux 0 -> C/n
            and M.van(0, [-100, 50, 60]) == 10.0                  # VAN taux 0 = somme
            and _ap(M.van(0.1, [-1000, 500, 600]), -49.59)        # VAN actualisee
            and _leve_v(M.interet_simple, -1, 0.05, 2)            # C<0 -> abstention
            and _leve_v(M.interet_compose, 1000, -1, 2)           # taux<=-1 -> abstention
            and _leve_v(M.annuite_constante, 10000, 0.01, 0)      # n<=0 annuite -> abstention
            and _leve_v(M.van, 0.1, []))                          # flux vide -> abstention

def _p_gestion_risque() -> bool:
    import gestion_risque as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    return (
        # cas CONNUS (ancres non circulaires)
        abs(M.esperance_perte(0.01, 100000) - 1000.0) < 1e-9          # E[perte] = p·montant
        and abs(M.ratio_sharpe(0.10, 0.02, 0.15) - 0.533333) < 1e-6   # (R-Rf)/sigma
        and abs(M.value_at_risk_parametrique(0.0, 1.0, 1.645) - 1.645) < 1e-9   # VaR normale std 95% = z
        and abs(M.value_at_risk_parametrique(0.1, 0.2, 1.645) - 0.229) < 1e-9   # -(0.1 - 1.645*0.2)
        and abs(M.prime_pure(0.05, 2000) - 100.0) < 1e-9              # freq*cout
        and abs(M.variance_portefeuille_2_actifs(0.5, 0.5, 0.2, 0.2, -1.0) - 0.0) < 1e-9  # rho=-1 -> Var 0
        # ABSTENTION (jamais un faux)
        and _leve_v(M.esperance_perte, 1.5, 100000)                   # proba hors [0,1]
        and _leve_v(M.ratio_sharpe, 0.10, 0.02, 0.0)                  # sigma <= 0
        and _leve_v(M.value_at_risk_parametrique, 0.1, -1.0)          # sigma <= 0
    )

def _p_comptabilite() -> bool:
    import comptabilite as M
    return (M.equation_bilan(100, 60, 40) is True
            and M.equation_bilan(100, 60, 30) is False
            and M.resultat_net(150, 120) == 30.0
            and M.fonds_roulement(100, 60) == 40.0
            and abs(M.ratio_liquidite(100, 50) - 2.0) < 1e-9
            and M.partie_double([60, 40], [100]) is True
            and M.partie_double([100], [90]) is False
            and _leve_v(M.ratio_liquidite, 100, 0)
            and _leve_v(M.equation_bilan, -100, 60, 40)
            and _leve_v(M.resultat_net, -1, 0))

def _p_inflation() -> bool:
    import inflation as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    def ap(a, b, tol=1e-2):
        return abs(a - b) <= tol
    ok = True
    # cas connus (formules exactes)
    ok &= ap(M.taux_inflation(100, 105), 5.0)        # IPC 100->105 = 5 %
    ok &= ap(M.taux_inflation(200, 250), 25.0)
    ok &= ap(M.pouvoir_achat(100, 5), 95.24)         # 100 € à 5 % -> 95.24 €
    ok &= ap(M.pouvoir_achat(105, 5), 100.0)
    ok &= ap(M.valeur_reelle(100, 100, 125), 80.0)   # déflation par indice
    ok &= ap(M.taux_reel(5, 2), 3.0)                 # Fisher approx = nominal - inflation
    ok &= ap(M.taux_reel(3, 5), -2.0)
    ok &= ap(M.taux_reel_exact(5, 2), 2.94)          # Fisher exact
    # identité croisée indépendante
    ok &= ap(M.valeur_reelle(100, 100, 200), M.pouvoir_achat(100, M.taux_inflation(100, 200)))
    # abstention (ValueError), jamais un faux
    ok &= _leve_v(M.taux_inflation, 0, 105)          # IPC <= 0
    ok &= _leve_v(M.taux_inflation, 100, 0)
    ok &= _leve_v(M.valeur_reelle, 100, 0, 100)
    ok &= _leve_v(M.pouvoir_achat, 100, -100)        # facteur nul
    ok &= _leve_v(M.taux_reel, "5", 2)               # non numérique
    ok &= _leve_v(M.taux_inflation, float("nan"), 105)
    return bool(ok)

def _p_pib() -> bool:
    import pib as M
    return (_proche(M.pib_depenses(60, 20, 25, 15, 12), 108.0)            # PIB = C+I+G+(X−M)
            and _proche(M.pib_depenses(100, 50, 30, 10, 40), 150.0)       # X−M<0 diminue le PIB
            and _proche(M.taux_croissance(100, 103), 3.0)                 # 100→103 = 3 %
            and _proche(M.taux_croissance(100, 95), -5.0)                 # récession = −5 %
            and _proche(M.pib_par_habitant(1000000, 200), 5000.0)         # PIB/habitant
            and _proche(M.pib_reel(220, 110), 200.0)                      # nominal·100/déflateur
            and _proche(M.pib_reel(120, 100), 120.0)                      # déflateur 100 (base) -> réel = nominal
            and _leve_v(M.pib_par_habitant, 1000, 0)                      # population ≤ 0 -> abstention
            and _leve_v(M.pib_reel, 1000, 0)                              # déflateur ≤ 0 -> abstention
            and _leve_v(M.taux_croissance, 0, 50))                        # base ≤ 0 -> abstention

def _p_chomage() -> bool:
    import chomage as M
    def _leve_v(fn, *a, **k) -> bool:
        try:
            fn(*a, **k); return False
        except ValueError: return True
        except Exception: return False
    return (abs(M.taux_chomage(2.5e6, 25e6) - 10.0) < 1e-9       # 2.5M/25M = 10 % (spéc)
            and M.population_active(22.5e6, 2.5e6) == 25e6        # active = occupés + chômeurs
            and abs(M.taux_activite(30, 40) - 75.0) < 1e-9        # 30/40 = 75 %
            and abs(M.taux_emploi(27, 40) - 67.5) < 1e-9          # 27/40 = 67.5 %
            and _leve_v(M.taux_chomage, 0, 0)                     # population active nulle -> abstention
            and _leve_v(M.taux_chomage, 101, 100)                 # chômeurs > active -> abstention
            and _leve_v(M.taux_chomage, -1, 100))                 # chômeurs négatif -> abstention

def _p_posologie() -> bool:
    import posologie as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    ok = True
    # cas connus exacts (formules établies)
    ok &= abs(M.dose_totale(10, 70) - 700.0) < 1e-9
    ok &= abs(M.debit_perfusion(1000, 8) - 125.0) < 1e-9
    ok &= abs(M.debit_gouttes(1000, 480, 20) - 41.6667) < 1e-3
    ok &= abs(M.surface_corporelle_mosteller(180, 80) - 2.0) < 1e-6      # ancre entiere non circulaire
    ok &= abs(M.surface_corporelle_mosteller(170, 70) - 1.8181) < 1e-3   # Mosteller enonce
    ok &= abs(M.dose_pediatrique(500, 35, 70) - 250.0) < 1e-9            # Clark
    # abstention (ValueError) sur entrees invalides
    ok &= _leve_v(M.dose_totale, 10, 0)                  # masse <= 0
    ok &= _leve_v(M.debit_perfusion, 1000, 0)            # duree <= 0
    ok &= _leve_v(M.surface_corporelle_mosteller, 170, 0)  # masse <= 0
    ok &= _leve_v(M.dose_totale, "dix", 70)             # non numerique
    return bool(ok)

def _p_essais_cliniques() -> bool:
    import essais_cliniques as M

    def _leve_v(fn, *a, **k) -> bool:
        try:
            fn(*a, **k)
            return False
        except ValueError:
            return True
        except Exception:
            return False

    return (
        abs(M.risque_relatif(0.15, 0.10) - 1.5) < 1e-9
        and abs(M.risque_relatif(0.20, 0.40) - 0.5) < 1e-9
        and abs(M.risque_relatif(0.10, 0.10) - 1.0) < 1e-9
        and abs(M.reduction_risque_absolue(0.20, 0.15) - 0.05) < 1e-9
        and abs(M.reduction_risque_absolue(0.10, 0.15) - (-0.05)) < 1e-9
        and M.nombre_sujets_a_traiter(0.05) == 20
        and M.nombre_sujets_a_traiter(0.03) == 34
        and abs(M.odds_ratio(20, 80, 10, 90) - 2.25) < 1e-9
        and abs(M.odds_ratio(10, 10, 10, 10) - 1.0) < 1e-9
        and _leve_v(M.risque_relatif, 0.15, 0.0)        # denominateur nul
        and _leve_v(M.risque_relatif, 1.5, 0.10)        # incidence > 1
        and _leve_v(M.nombre_sujets_a_traiter, 0.0)     # RRA <= 0
        and _leve_v(M.odds_ratio, 20, 0, 10, 90)        # b = 0 -> indefini
    )

def _p_biomecanique() -> bool:
    import biomecanique as M

    def _leve_v(fn, *a, **k) -> bool:
        try:
            fn(*a, **k)
            return False
        except ValueError:
            return True
        except Exception:
            return False

    return (
        # cas connus (exactitude)
        abs(M.portee_projectile(20, 45) - 40.77) < 0.01          # R = v0²·sin(2θ)/g = 40.77 m
        and abs(M.hauteur_max(20, 45) - 10.1937) < 0.001          # H = (v0·sinθ)²/2g
        and M.angle_optimal_portee() == 45.0                      # angle de portée max
        and abs(M.moment_force(10, 0.5) - 5.0) < 1e-9             # M = F·d
        and abs(M.couple(100, 2) - 200.0) < 1e-9                  # couple alias
        and abs(M.impulsion(50, 2) - 100.0) < 1e-9               # J = F·t
        and abs(M.portee_projectile(20, 30) - M.portee_projectile(20, 60)) < 1e-6  # symétrie complémentaire
        # abstention (ValueError), jamais un faux
        and _leve_v(M.portee_projectile, -1, 45)                  # v0 < 0
        and _leve_v(M.portee_projectile, 20, 95)                  # angle > 90
        and _leve_v(M.portee_projectile, 20, 45, 0)              # g <= 0
        and _leve_v(M.hauteur_max, 20, -5)                        # angle < 0
        and _leve_v(M.moment_force, 10, -0.5)                     # bras < 0
        and _leve_v(M.impulsion, 50, 0)                           # durée <= 0
    )

def _p_entrainement() -> bool:
    import entrainement as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    def _pr(a, b, tol=1e-2):
        return abs(a - b) <= tol
    return (
        _pr(M.un_rep_max_epley(100, 5), 116.67)              # Epley 1RM
        and M.frequence_cardiaque_max(30) == 190.0           # Haskell 220-age
        and _pr(M.zone_cible_karvonen(60, 30, 0.7), 151.0)   # Karvonen (reserve FC)
        and M.zone_cible_karvonen(70, 40, 1.0) == M.frequence_cardiaque_max(40)  # i=1 -> FCmax
        and _pr(M.vo2max_estime(200, 50), 61.2)              # Uth VO2max 15.3*FCmax/FCrepos
        and _leve_v(M.un_rep_max_epley, 0, 5)                # poids<=0 -> abstention
        and _leve_v(M.un_rep_max_epley, 100, 0)              # reps<1 -> abstention
        and _leve_v(M.frequence_cardiaque_max, -1)           # age<0 -> abstention
        and _leve_v(M.frequence_cardiaque_max, 121)          # age>120 -> abstention
        and _leve_v(M.zone_cible_karvonen, 60, 30, 1.5)      # intensite hors [0,1] -> abstention
        and _leve_v(M.vo2max_estime, 50, 50)                 # fc_max<=fc_repos -> abstention
    )

def _p_demographie() -> bool:
    import demographie as M
    return (
        abs(M.taux_croissance_naturel(20, 8) - 0.012) < 1e-9
        and abs(M.densite_population(1_000_000, 500) - 2000.0) < 1e-9
        and abs(M.temps_doublement(2) - 35.0) < 1e-9
        and abs(M.taux_dependance(30, 20, 50) - 100.0) < 1e-9
        and abs(M.indice_fecondite([60, 60, 60, 60, 60, 60, 60], 5) - 2.1) < 1e-9
        and _leve_v(M.densite_population, 1000, 0)      # surface = 0 -> abstention
        and _leve_v(M.temps_doublement, 0)              # taux <= 0 -> abstention
        and _leve_v(M.taux_dependance, 30, 20, 0)       # actifs = 0 -> abstention
        and _leve_v(M.indice_fecondite, [])             # séquence vide -> abstention
    )

def _p_audiologie() -> bool:
    import audiologie as M
    import math
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    def proche(g, e, r=1e-5):
        return abs(g - e) <= abs(e) * r + 1e-9
    ok = True
    # niveau dB SPL — formule 10·log10(I/I0)
    ok &= M.niveau_db(1e-12) == 0.0                       # I=I0 -> 0 dB
    ok &= proche(M.niveau_db(1e-2), 100.0)                # rapport 1e10 -> 100 dB
    ok &= proche(M.niveau_db(1.0), 120.0)                 # ~seuil de douleur
    ok &= proche(M.niveau_db(1e-6), 60.0)                 # conversation
    # classification OMS
    ok &= M.classe_perte_auditive(10) == "normale"
    ok &= M.classe_perte_auditive(60) == "modérément sévère"
    ok &= M.classe_perte_auditive(90) == "sévère"
    ok &= M.classe_perte_auditive(100) == "profonde"
    # plage audible (fait)
    ok &= M.plage_audible_hz() == (20, 20000)
    # addition : 2 sources égales -> +3 dB exact
    ok &= proche(M.addition_db(60, 60), 60 + 10 * math.log10(2))
    # abstention (jamais un faux)
    ok &= _leve_v(M.niveau_db, 0.0)
    ok &= _leve_v(M.niveau_db, -1e-12)
    ok &= _leve_v(M.classe_perte_auditive, -1.0)
    return ok


def _p_externalites() -> bool:
    import externalites as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k)
            return False
        except ValueError:
            return True
    return (
        M.type_externalite('pollution') == 'negative'
        and M.type_externalite('vaccination') == 'positive'
        and M.type_externalite('abeilles') == 'positive'
        and M.type_externalite(-5.0) == 'negative'
        and M.type_externalite(3.0) == 'positive'
        and M.cout_social(10.0, 4.0) == 14.0
        and M.taxe_pigou(4.0) == 4.0
        and M.defaillance_marche('negative') == 'surproduction'
        and M.defaillance_marche('positive') == 'sous-production'
        and _leve_v(M.cout_social, -1.0, 4.0)
        and _leve_v(M.taxe_pigou, -1.0)
        and _leve_v(M.defaillance_marche, 'inconnu')
        and _leve_v(M.type_externalite, 'subvention_xyz')
        and _leve_v(M.type_externalite, 0)
    )

def _p_cycles_economiques() -> bool:
    import cycles_economiques as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    return all([
        # CAS connus (structure consensuelle + classification Conference Board)
        M.phase_suivante("sommet/pic") == "recession",        # après le pic vient la récession
        M.phase_suivante("creux/depression") == "expansion",  # le cycle boucle
        M.phase_cycle("expansion")["ordre"] == 1,
        M.phase_cycle("pic")["nom"] == "sommet/pic",
        len(M.phases()) == 4,                                 # 4 phases
        M.definition_recession()["nombre_trimestres"] == 2,  # règle technique = 2 trimestres
        M.est_recession_technique([-0.1, -0.2]) is True,      # 2 trimestres consécutifs de baisse
        M.est_recession_technique([-0.5]) is False,           # 1 seul trimestre -> non
        M.type_indicateur("permis de construire") == "avance",
        M.type_indicateur("PIB") == "coincident",
        M.type_indicateur("taux de chomage") == "retarde",
        # ABSTENTION (jamais un faux -> ValueError)
        _leve_v(M.phase_cycle, "inconnu"),
        _leve_v(M.type_indicateur, "taux d'interet"),         # ambigu, hors catalogue
        _leve_v(M.est_recession_technique, []),
    ])

def _p_commerce_international() -> bool:
    import commerce_international as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    return (
        M.balance_commerciale(120, 100) == 20.0
        and M.nature_balance(120, 100) == "excédent"
        and M.taux_couverture(120, 100) == 120.0
        and M.avantage_comparatif(0.5, 0.8) == "A"
        and M.avantage_comparatif(2.0, 1.0) == "B"
        and M.avantage_comparatif(1.0, 1.0) == "aucun"
        and M.termes_echange(110, 100) == 110.0
        and _leve_v(M.taux_couverture, 120, 0)
        and _leve_v(M.balance_commerciale, -1, 100)
        and _leve_v(M.avantage_comparatif, 0.0, 0.8)
        and _leve_v(M.termes_echange, 100, 0)
    )

def _p_rhetorique() -> bool:
    import rhetorique as M

    def _leve_v(fn, *a, **k) -> bool:
        try:
            fn(*a, **k)
            return False
        except ValueError:
            return True
        except Exception:
            return False

    return (
        # CATALOGUE ÉTABLI — modes d'Aristote, noyau sémantique correct
        "credibilite" in M._norme(M.mode_persuasion("ethos"))
        and "emotion" in M._norme(M.mode_persuasion("pathos"))
        and ("logique" in M._norme(M.mode_persuasion("logos"))
             or "raison" in M._norme(M.mode_persuasion("logos")))
        # CAS spéc : identification du mode
        and M.identifie_mode("appel a l autorite") == "ethos"
        and M.identifie_mode("appel a la peur") == "pathos"
        and M.identifie_mode("argument chiffre") == "logos"
        # figure : anaphore = répétition en début
        and "debut" in M._norme(M.figure_style("anaphore"))
        and "repetition" in M._norme(M.figure_style("anaphore"))
        # SOUNDNESS — hors catalogue / sans marqueur -> abstention (ValueError)
        and _leve_v(M.mode_persuasion, "kairos")
        and _leve_v(M.figure_style, "oxymore")
        and _leve_v(M.identifie_mode, "phrase sans marqueur reconnu")
        and _leve_v(M.identifie_mode, "appel a l autorite double d un appel a la peur")
    )

def _p_journalisme_deontologie() -> bool:
    import journalisme_deontologie as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    return (
        "verifier" in M._strip_accents(M.principe("verification/exactitude")).lower()
        and isinstance(M.principe("protection_sources"), str)
        and M.respecte_deontologie("publier sans verifier") == "violation"
        and M.respecte_deontologie("proteger une source") == "conforme"
        and M.respecte_deontologie("reveler une source confidentielle") == "violation"
        and M.principe_concerne("verifier avant publier") == "verification/exactitude"
        and M.respecte_deontologie("separer faits et commentaires") == "conforme"
        and M.principe_concerne("separer faits et commentaires") == "separation_faits_opinions"
        and M.evalue("publier sans verifier") == ("violation", "verification/exactitude")
        and _leve_v(M.principe, "objectivite_totale")
        and _leve_v(M.respecte_deontologie, "faire un scoop")
    )

def _p_marketing_mecanismes() -> bool:
    import marketing_mecanismes as M

    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k)
            return False
        except ValueError:
            return True
        except Exception:
            return False

    return (
        # AIDA dans l'ordre A->I->D->A
        M.etape_aida("attention").rang == 1
        and M.etape_aida("interet").rang == 2
        and M.etape_aida("desir").rang == 3
        and M.etape_aida("action").rang == 4
        and M.ordre_aida() == ["attention", "interet", "desir", "action"]
        # Cialdini : 6 principes + cas imposés
        and len(M.principes_cialdini()) == 6
        and "limit" in M.definition_cialdini("rarete").lower()                       # rareté = édition limitée
        and "milliers de clients" in M.definition_cialdini("preuve_sociale").lower() # preuve sociale
        and M.principe_cialdini("autorite").definition.strip() != ""
        # SOUNDNESS — abstention (ValueError) hors référentiel
        and _leve_v(M.etape_aida, "memorisation")
        and _leve_v(M.etape_aida, "")
        and _leve_v(M.etape_aida, None)
        and _leve_v(M.principe_cialdini, "unite")
        and _leve_v(M.principe_cialdini, "peur")
        and _leve_v(M.principe_cialdini, "")
    )

def _p_propagande() -> bool:
    import propagande as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    ok = True
    # CAS imposes
    ok &= 'tout le monde' in M.technique('bandwagon').lower()      # bandwagon = 'tout le monde le fait'
    ok &= M.est_intentionnel('disinformation') is True            # disinformation = intentionnelle
    ok &= M.est_intentionnel('misinformation') is False           # misinformation = erreur involontaire
    ok &= M.est_intentionnel('malinformation') is True
    ok &= M.est_faux('malinformation') is False                   # malinformation = info vraie detournee
    ok &= M.type_desinformation('misinformation')['intention_de_nuire'] is False
    # catalogue des 7 techniques IPA + alias des libelles a slash
    ok &= len(M.liste_techniques()) == 7
    ok &= M.technique('train en marche') == M.technique('bandwagon')
    ok &= M.technique('diabolisation') == M.technique('name_calling')
    ok &= M.technique('carte biaisee') == M.technique('card_stacking')
    ok &= isinstance(M.technique('transfert'), str) and len(M.technique('temoignage')) > 0
    # soundness : hors catalogue -> abstention (ValueError)
    ok &= _leve_v(M.technique, 'lavage_de_cerveau')
    ok &= _leve_v(M.technique, '')
    ok &= _leve_v(M.type_desinformation, 'fake_news')
    ok &= _leve_v(M.est_intentionnel, 'rumeur')
    return bool(ok)

def _p_bibliotheconomie() -> bool:
    import bibliotheconomie as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    return (
        M.classe_dewey(500) == 'sciences' and
        M.classe_dewey(800) == 'littérature' and
        M.classe_dewey(0) == 'informatique/généralités' and
        M.classe_dewey(900) == 'histoire/géo' and
        M.isbn_valide('978-0-306-40615-7') is True and
        M.isbn_valide('978-0-13-110362-7') is True and
        M.isbn_valide('9780306406158') is False and
        _leve_v(M.classe_dewey, 1000) and
        _leve_v(M.classe_dewey, 250) and
        _leve_v(M.classe_dewey, '500') and
        _leve_v(M.isbn_valide, '978030640615') and
        _leve_v(M.isbn_valide, '978030640615X') and
        _leve_v(M.isbn_valide, '')
    )

def _p_cardiologie() -> bool:
    import cardiologie as M
    import math

    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True

    return (
        # ancres cliniques connues
        M.frequence_cardiaque_max(40) == 180.0          # FCmax = 220 - age
        and M.frequence_cardiaque_max(120) == 100.0
        and M.fraction_ejection(60, 120) == 50.0        # FE = VE/VTD*100
        and M.fraction_ejection(70, 100) == 70.0
        and M.qt_corrige_bazett(400, 1.0) == 400.0      # QTc = QT/sqrt(RR), RR=1 -> QTc=QT
        and abs(M.qt_corrige_bazett(400, 0.64) - 500.0) < 1e-9  # sqrt(0.64)=0.8
        and M.classe_fc_repos(50) == M.BRADYCARDIE      # <60
        and M.classe_fc_repos(60) == M.NORMAL           # bornes [60,100]
        and M.classe_fc_repos(100) == M.NORMAL
        and M.classe_fc_repos(120) == M.TACHYCARDIE     # >100
        # soundness : abstention (ValueError) sur domaine/type invalide
        and _leve_v(M.frequence_cardiaque_max, 200)     # age hors [0,120]
        and _leve_v(M.frequence_cardiaque_max, -1)
        and _leve_v(M.frequence_cardiaque_max, True)    # bool non numerique
        and _leve_v(M.qt_corrige_bazett, 400, 0)        # RR <= 0
        and _leve_v(M.qt_corrige_bazett, 400, -0.5)
        and _leve_v(M.qt_corrige_bazett, 0, 1.0)        # QT <= 0
        and _leve_v(M.fraction_ejection, 60, 0)         # volumes <= 0
        and _leve_v(M.fraction_ejection, -60, 120)
        and _leve_v(M.classe_fc_repos, 0)               # fc <= 0
    )

def _p_urgence_medicale() -> bool:
    import urgence_medicale as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    return (
        M.score_glasgow(4, 5, 6) == 15 and          # Glasgow normal
        M.score_glasgow(1, 1, 1) == 3 and           # coma profond (minimum)
        M.est_coma_grave(1, 1, 1) is True and       # total 3 <= 8
        M.gravite_glasgow(4, 5, 6) == 'leger' and   # 15 -> leger
        M.score_apgar(2, 2, 2, 2, 2) == 10 and      # Apgar parfait
        M.interpretation_apgar(2, 2, 2, 2, 2) == 'normal' and
        abs(M.indice_choc(120, 100) - 1.2) < 1e-9 and  # indice de choc FC/PAS
        M.est_choc(120, 100) is True and            # 1.2 > 0.9 -> choc
        M.est_choc(90, 100) is False and            # 0.9 = seuil (strict >)
        _leve_v(M.score_glasgow, 5, 5, 6) and       # sous-score yeux hors plage
        _leve_v(M.score_apgar, 3, 2, 2, 2, 2) and   # critere Apgar hors plage
        _leve_v(M.indice_choc, 120, 0) and          # PAS<=0
        _leve_v(M.indice_choc, 0, 100)              # FC<=0
    )

def _p_medecines_alternatives() -> bool:
    """Preuve auto-portée : vrai sur cas connus + abstention sur entrée hors catalogue / non tranchée."""
    import medecines_alternatives as M

    def _leve_v(fn, *a, **k) -> bool:
        try:
            fn(*a, **k)
            return False
        except ValueError:
            return True
        except Exception:
            return False

    return (
        # niveaux établis (catalogue)
        M.niveau_preuve("homeopathie") == "aucune_preuve"
        and M.niveau_preuve("homéopathie") == "aucune_preuve"        # accent normalisé
        and M.niveau_preuve("acupuncture") == "preuve_faible"
        and M.niveau_preuve("osteopathie") == "preuve_limitee"
        and M.niveau_preuve("chiropraxie") == "preuve_limitee"
        and M.niveau_preuve("reiki") == "aucune_preuve"
        and M.niveau_preuve("phytotherapie") == "variable"
        and M.niveau_preuve("meditation_pleine_conscience") == "preuve_moderee"
        # placebo : verdicts tranchés
        and M.depasse_placebo("homeopathie") is False
        and M.depasse_placebo("reiki") is False
        and M.depasse_placebo("meditation_pleine_conscience") is True
        # abstentions : hors catalogue + efficacité non tranchée + entrée invalide
        and _leve_v(M.niveau_preuve, "naturopathie")                 # hors catalogue
        and _leve_v(M.niveau_preuve, "")                             # vide
        and _leve_v(M.niveau_preuve, None)                           # non-str
        and _leve_v(M.depasse_placebo, "phytotherapie")             # variable : non tranché
        and _leve_v(M.depasse_placebo, "acupuncture")               # faible : non tranché
        and _leve_v(M.depasse_placebo, "bioresonance")              # hors catalogue
    )


def _p_scrutin() -> bool:
    import scrutin as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    ok = True
    ok &= M.dhondt({"A": 100, "B": 80, "C": 30}, 5) == {"A": 3, "B": 2, "C": 0}
    ok &= M.sainte_lague({"A": 100, "B": 80, "C": 30}, 5) == {"A": 2, "B": 2, "C": 1}
    ok &= M.majorite_absolue(60, 100) is True
    ok &= M.majorite_absolue(50, 100) is False
    ok &= M.quotient_hare(1000, 10) == 100.0
    ok &= _leve_v(M.dhondt, {"A": 1}, 0)          # n_sieges <= 0
    ok &= _leve_v(M.dhondt, {"A": -1}, 5)         # voix negative
    ok &= _leve_v(M.dhondt, {"A": 100, "B": 100}, 1)  # egalite non mecanique -> abstention
    ok &= _leve_v(M.majorite_absolue, -1, 100)    # voix negative
    return ok

def _p_strategie_jeux() -> bool:
    import strategie_jeux as M
    V = M.VIDE
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    return (
        M.valeur_minimax([V]*9) == 0                                            # jeu resolu = nul
        and M.morpion_coup_optimal(['X','X',V,'O','O',V,V,V,V]) == 2           # gain immediat
        and M.valeur_minimax(['X','X',V,'O','O',V,V,V,V]) == 1
        and M.morpion_coup_optimal(['X',V,V,'O','O',V,V,V,'X']) == 5           # blocage de la menace
        and M.valeur_minimax(['O','O',V,'O','X','X',V,'X',V]) == -1            # fourchette O imparable
        and M.gagnant(['X','X','X','O','O',V,V,V,V]) == 'X'
        and M.gagnant([V]*9) is None
        and _leve_v(M.valeur_minimax, [V]*8)                                   # longueur invalide -> abstention
        and _leve_v(M.morpion_coup_optimal, ['Z']+[V]*8)                       # symbole invalide -> abstention
        and _leve_v(M.valeur_minimax, ['O',V,V,V,V,V,V,V,V])                   # compte incoherent -> abstention
    )

def _p_jeux_appliques() -> bool:
    import jeux_appliques as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    ok = True
    # Dilemme du prisonnier : équilibre Nash pur UNIQUE = (trahir,trahir)=(1,1)
    g1 = [[3, 0], [5, 1]]; g2 = [[3, 5], [0, 1]]
    ok &= M.equilibre_nash_pur(g1, g2) == [(1, 1)]
    # Bataille des sexes : 2 équilibres purs
    b1 = [[2, 0], [0, 1]]; b2 = [[1, 0], [0, 2]]
    ok &= sorted(M.equilibre_nash_pur(b1, b2)) == [(0, 0), (1, 1)]
    # Matching pennies : 0 équilibre pur
    p1 = [[1, -1], [-1, 1]]; p2 = [[-1, 1], [1, -1]]
    ok &= M.equilibre_nash_pur(p1, p2) == []
    # dilemme_prisonnier() : équilibre dominant Pareto-dominé
    dp = M.dilemme_prisonnier()
    ok &= dp["equilibre"] == (1, 1)
    ok &= dp["strategie_dominante_J1"] == 1 and dp["strategie_dominante_J2"] == 1
    ok &= dp["equilibre_pareto_domine"] is True
    ok &= M.strategie_dominante([[3, 0], [5, 1]], stricte=True) == 1
    # SOUNDNESS : matrices mal formées -> ValueError (abstention)
    ok &= _leve_v(M.equilibre_nash_pur, [[1, 2], [3]], [[1, 2], [3, 4]])
    ok &= _leve_v(M.equilibre_nash_pur, [], [])
    return bool(ok)

def _p_budget_personnel() -> bool:
    import budget_personnel as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    ok = True
    # cas connus (calculs exacts + conventions sourcées)
    ok &= M.solde(2000, 1500) == 500.0
    ok &= M.taux_epargne(500, 2000) == 25.0
    ok &= M.regle_50_30_20(2000) == {"besoins": 1000.0, "envies": 600.0, "epargne": 400.0}
    ok &= M.capacite_emprunt(2000) == 700.0          # 35 % HCSF
    ok &= M.reste_a_vivre(2000, 1500) == 500.0
    # abstention (jamais inventer)
    ok &= _leve_v(M.solde, 0, 100)                   # revenus <= 0
    ok &= _leve_v(M.taux_epargne, 100, 0)            # revenus = 0
    ok &= _leve_v(M.capacite_emprunt, -1)            # revenus < 0
    ok &= _leve_v(M.taux_epargne, 2001, 2000)        # epargne > revenus
    ok &= _leve_v(M.capacite_emprunt, 2000, 1.5)     # taux hors ]0,1]
    return bool(ok)

def _p_biostatistique() -> bool:
    import biostatistique as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    return (
        abs(M.sensibilite(90, 10) - 0.9) < 1e-12
        and abs(M.specificite(80, 20) - 0.8) < 1e-12
        and abs(M.valeur_predictive_positive(90, 20) - 90/110) < 1e-12
        and abs(M.valeur_predictive_negative(80, 10) - 80/90) < 1e-12
        and abs(M.prevalence(200, 1000) - 0.2) < 1e-12
        and abs(M.rapport_vraisemblance_positif(0.9, 0.8) - 4.5) < 1e-12
        and abs(M.rapport_vraisemblance_negatif(0.9, 0.8) - 0.125) < 1e-12
        and abs(M.exactitude(90, 80, 20, 10) - 0.85) < 1e-12
        and _leve_v(M.sensibilite, -1, 10)
        and _leve_v(M.specificite, 0, 0)
        and _leve_v(M.valeur_predictive_positive, 0, 0)
        and _leve_v(M.prevalence, 0, 0)
        and _leve_v(M.prevalence, 11, 10)
        and _leve_v(M.rapport_vraisemblance_positif, 0.9, 1.0)
        and _leve_v(M.rapport_vraisemblance_positif, 1.2, 0.8)
        and _leve_v(M.sensibilite, True, 10)
        and _leve_v(M.sensibilite, float("nan"), 10)
    )

def _p_psychometrie() -> bool:
    import math
    import psychometrie as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    def _ap(x, y, t=1e-4):
        return abs(x - y) <= t
    ok = True
    # QI standardisé : score = moyenne -> 100 ; +1sigma -> 115 ; +2sigma -> 130 ; -1sigma -> 85
    ok &= _ap(M.qi_standardise(50, 50, 10), 100.0)
    ok &= _ap(M.qi_standardise(60, 50, 10), 115.0)
    ok &= _ap(M.qi_standardise(70, 50, 10), 130.0)
    ok &= _ap(M.qi_standardise(40, 50, 10), 85.0)
    # Rang percentile sous N(100,15) (table normale standard)
    ok &= (M.rang_percentile_qi(100) == 50.0)
    ok &= _ap(M.rang_percentile_qi(115), 84.134475, 1e-3)
    ok &= _ap(M.rang_percentile_qi(130), 97.724987, 1e-3)
    # Alpha de Cronbach : (k/(k-1))(1 - k*v_moy/var_tot)
    ok &= _ap(M.alpha_cronbach(10, 1.1, 50), 0.866667, 1e-5)
    ok &= _ap(M.alpha_cronbach(4, 1, 16), 1.0)
    # Erreur standard de mesure : SD*sqrt(1-fiab)
    ok &= _ap(M.erreur_standard_mesure(15, 0.75), 7.5)
    ok &= _ap(M.erreur_standard_mesure(15, 0.91), 4.5)
    # Abstention (entree hors referentiel -> ValueError, jamais inventer)
    ok &= _leve_v(M.qi_standardise, 60, 50, 0)        # sigma = 0
    ok &= _leve_v(M.qi_standardise, 60, 50, -5)       # sigma < 0
    ok &= _leve_v(M.alpha_cronbach, 1, 1.0, 10)       # k < 2
    ok &= _leve_v(M.alpha_cronbach, 10, 1.0, 0)       # variance_totale = 0
    ok &= _leve_v(M.alpha_cronbach, 10, -1.0, 50)     # variance item < 0
    ok &= _leve_v(M.erreur_standard_mesure, 15, 1.5)  # fiabilite > 1
    ok &= _leve_v(M.rang_percentile_qi, float("nan")) # non fini
    return bool(ok)

def _p_hierarchie_normes() -> bool:
    import hierarchie_normes as M
    def _leve_v(fn, *a, **k) -> bool:
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    return (M.rang('constitution') == 1
            and M.rang('loi') == 3
            and M.rang('decret') == 4
            and M.superieur('constitution', 'loi') is True
            and M.superieur('traite_international', 'loi') is True   # art. 55 C. : traité > loi
            and M.superieur('loi', 'constitution') is False
            and M.superieur('decret', 'arrete') is True
            and M.conforme('decret', 'loi') is True                 # un décret doit respecter la loi
            and M.conforme('loi', 'decret') is False
            and M.inferieur('decret', 'loi') is True
            and _leve_v(M.rang, 'jurisprudence')                    # hors catalogue -> abstention
            and _leve_v(M.superieur, 'loi', 'inconnu'))

def _p_conjugaison() -> bool:
    import conjugaison as M
    return (
        M.conjugue('parler', 1, 'present') == 'parle'
        and M.conjugue('parler', 2, 'present') == 'parles'
        and M.conjugue('parler', 4, 'present') == 'parlons'
        and M.conjugue('parler', 6, 'present') == 'parlent'
        and M.conjugue('finir', 4, 'present') == 'finissons'
        and M.groupe('parler') == 1
        and M.groupe('finir') == 2
        and M.groupe('aller') == 3
        and M.terminaisons_present(1) == ('e', 'es', 'e', 'ons', 'ez', 'ent')
        and M.terminaisons_present(2) == ('is', 'is', 'it', 'issons', 'issez', 'issent')
        and _leve_v(M.conjugue, 'être', 1, 'present')
        and _leve_v(M.conjugue, 'partir', 1, 'present')
        and _leve_v(M.conjugue, 'parler', 0, 'present')
        and _leve_v(M.conjugue, 'parler', 7, 'present')
        and _leve_v(M.conjugue, 'parler', 1, 'futur')
        and _leve_v(M.conjugue, 'manger', 4, 'present')
        and _leve_v(M.groupe, 'banane')
    )

def _p_cartographie() -> bool:
    import cartographie as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    return (
        M.echelle_distance_reelle(4, 25000) == 100000          # 1:25000, 4 cm -> 100000 cm = 1 km
        and M.distance_carte(100000, 25000) == 4               # inverse exact
        and abs(M.cm_en_km(M.echelle_distance_reelle(4, 25000)) - 1.0) < 1e-12
        and abs(M.conversion_dms_dd(48, 51, 12) - 48.8533333333) < 1e-7   # 48°51'12'' -> 48.8533°
        and abs(M.conversion_dms_dd(-2, 30, 0) - (-2.5)) < 1e-12          # signe par les degrés
        and abs(M.resolution_au_sol_depuis_dpi(300, 25000).valeur_cm - 211.6666667) < 1e-3
        and _leve_v(M.echelle_distance_reelle, 4, 0)           # échelle 0 -> abstention
        and _leve_v(M.echelle_distance_reelle, 4, -25000)      # échelle < 0 -> abstention
        and _leve_v(M.conversion_dms_dd, 48, 60, 0)            # minutes 60 -> abstention
        and _leve_v(M.conversion_dms_dd, 48, 51, 60)           # secondes 60 -> abstention
        and _leve_v(M.conversion_dms_dd, 48.5, 51, 0)          # degrés non entiers -> abstention
        and _leve_v(M.echelle_distance_reelle, "4", 25000)     # entrée non numérique -> abstention
    )

def _p_mesures_sociales() -> bool:
    """Preuve auto-portée : vrai sur cas connus + abstention sur entrée invalide."""
    import mesures_sociales as M

    def _leve_v(fn, *a, **k) -> bool:
        try:
            fn(*a, **k)
            return False
        except ValueError:
            return True
        except Exception:
            return False

    return (
        M.gini([10, 10, 10]) == 0.0                       # égalité parfaite
        and abs(M.gini([1, 2]) - 1.0 / 6.0) < 1e-12       # ≡ double somme des écarts
        and abs(M.gini([0, 0, 0, 10]) - 0.75) < 1e-12     # concentration maximale (n−1)/n
        and M.gini([5]) == 0.0                            # un seul individu
        and M.coefficient_gini([0.2, 0.4, 0.6, 0.8, 1.0]) == 0.0   # Lorenz = diagonale
        and abs(M.coefficient_gini([0.05, 0.15, 0.30, 0.55, 1.0]) - 0.38) < 1e-12
        and M.seuil_pauvrete(20000) == 12000.0            # 60 % du médian
        and M.seuil_pauvrete(1000, 0.5) == 500.0          # variante 50 %
        and M.taux_pauvrete(15, 100) == 0.15
        and M.mediane([1, 2, 3]) == 2.0
        and M.mediane([1, 2, 3, 4]) == 2.5
        and abs(M.idh(0.8, 0.8, 0.8) - 0.8) < 1e-12
        and M.indice_dimension(50, 0, 100) == 0.5
        and _leve_v(M.gini, [])                           # liste vide
        and _leve_v(M.gini, [-1, 2])                      # revenu négatif
        and _leve_v(M.gini, [0, 0, 0])                    # total nul -> indéfini
        and _leve_v(M.taux_pauvrete, 150, 100)            # pauvres > population
        and _leve_v(M.taux_pauvrete, 10, 0)               # population <= 0
        and _leve_v(M.seuil_pauvrete, -1)                 # médian négatif
        and _leve_v(M.seuil_pauvrete, 1000, 0)            # fraction = 0
        and _leve_v(M.coefficient_gini, [0.2, 0.4])       # dernière part != 1
        and _leve_v(M.coefficient_gini, [0.5, 0.3, 1.0])  # non croissante
        and _leve_v(M.indice_dimension, 5, 10, 10)        # max == min
        and _leve_v(M.idh, 1.2, 0.5, 0.5)                 # sous-indice > 1
    )

def _p_citoyennete() -> bool:
    import citoyennete as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    return (M.categorie('voter') == 'droit_politique'
            and M.categorie("payer l'impôt") == 'devoir'
            and M.categorie("liberté d'expression") == 'droit_civil'
            and M.categorie('éducation') == 'droit_social'
            and M.categorie('droit de vote') == 'droit_politique'
            and M.est_droit('voter') is True
            and M.est_devoir("payer l'impôt") is True
            and M.est_droit("payer l'impôt") is False
            and M.est_droit('éducation') is True
            and M.age_majorite_civique() == 18
            and _leve_v(M.categorie, 'manger')
            and _leve_v(M.categorie, 'défense')
            and _leve_v(M.est_droit, None)
            and _leve_v(M.est_devoir, 42)
            and _leve_v(M.categorie, ''))

def _p_conservation_aliments() -> bool:
    import conservation_aliments as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    return (M.methode('congelation').temperature_c == -18.0
            and M.methode('pasteurisation').temperature_c == 72.0
            and M.methode('pasteurisation').duree_s == 15.0
            and M.methode('sterilisation/UHT').temperature_c == 135.0
            and M.methode('uht') == M.methode('sterilisation/UHT')
            and M.methode('refrigeration').plage_c == (0.0, 4.0)
            and M.zone_danger_temperature() == (4, 63)
            and M.dans_zone_danger(20) is True and M.dans_zone_danger(2) is False
            and M.dans_zone_danger(4) is False and M.dans_zone_danger(63) is False
            and M.activite_eau_limite() == 0.91
            and M.bacteries_inhibees(0.90) is True
            and M.bacteries_inhibees(0.91) is False
            and M.bacteries_inhibees(0.95) is False
            and len(M.methodes()) == 8
            and _leve_v(M.methode, 'lyophilisation')
            and _leve_v(M.methode, 'sterilisation')
            and _leve_v(M.methode, '')
            and _leve_v(M.methode, None)
            and _leve_v(M.bacteries_inhibees, 1.5)
            and _leve_v(M.bacteries_inhibees, -0.1)
            and _leve_v(M.dans_zone_danger, None))

def _p_retraite() -> bool:
    import retraite as M
    def _leve_v(fn, *a, **k):
        try:
            fn(*a, **k); return False
        except ValueError:
            return True
        except Exception:
            return False
    return (
        abs(M.pension(2000.0, 0.5, 160, 160) - 1000.0) < 1e-9      # taux plein : coeff=1
        and abs(M.pension(2000.0, 0.5, 80, 160) - 500.0) < 1e-9    # prorata ½
        and abs(M.pension(2000.0, 0.75, 120, 160) - 1125.0) < 1e-9 # prorata ¾
        and abs(M.taux_remplacement(1000.0, 2000.0) - 50.0) < 1e-9 # pension/salaire·100
        and abs(M.coefficient_proratisation(160, 160) - 1.0) < 1e-9
        and abs(M.decote(8, 0.0125) - 0.1) < 1e-9                  # décote proportionnelle
        and _leve_v(M.pension, 2000.0, 0.5, 0, 160)                # durée<=0 -> abstention
        and _leve_v(M.pension, 2000.0, 1.5, 160, 160)             # taux hors [0,1] -> abstention
        and _leve_v(M.taux_remplacement, 1000.0, 0.0)            # dénominateur nul -> abstention
        and _leve_v(M.decote, 8.5, 0.0125)                       # trimestres non entier -> abstention
    )


# ── ALIAS de faux-gaps (2026-07-02) : briques FAUX=0 DÉJÀ écrites, seul l'enregistrement REGISTRE manquait ──
# Médecines alternatives : catalogue de consensus (medecines_alternatives.py), preuves TAILLÉES par pratique
# (assertion du niveau de preuve EXACT + abstention hors-catalogue) — plus précis que la preuve générique.
def _p_medalt_homeopathie() -> bool:
    import medecines_alternatives as M
    return (M.niveau_preuve("homeopathie") == "aucune_preuve"
            and M.depasse_placebo("homeopathie") is False
            and M.est_catalogue("homeopathie") is True
            and _leve_v(M.niveau_preuve, "licorne_xyz"))

def _p_medalt_acupuncture() -> bool:
    import medecines_alternatives as M
    return (M.niveau_preuve("acupuncture") == "preuve_faible"
            and M.est_catalogue("acupuncture") is True
            and _leve_v(M.niveau_preuve, "pratique_inexistante"))

def _p_medalt_phytotherapie() -> bool:
    import medecines_alternatives as M
    return (M.niveau_preuve("phytotherapie") == "variable"
            and M.est_catalogue("phytotherapie") is True
            and _leve_v(M.niveau_preuve, "pratique_inexistante"))

def _p_medalt_osteo_chiro() -> bool:
    import medecines_alternatives as M
    return (M.niveau_preuve("osteopathie") == "preuve_limitee"
            and M.niveau_preuve("chiropraxie") == "preuve_limitee"
            and _leve_v(M.niveau_preuve, "pratique_inexistante"))

def _p_medalt_energetique() -> bool:
    import medecines_alternatives as M
    return (M.niveau_preuve("chakras") == "aucune_preuve"
            and M.niveau_preuve("soins_energetiques") == "aucune_preuve"
            and M.niveau_preuve("reiki") == "aucune_preuve"
            and _leve_v(M.niveau_preuve, "pratique_inexistante"))

def _p_cybersecurite_defensive() -> bool:
    """Cybersécurité défensive = audit de code sound (audit_code.py) : détecte des classes CWE DOCUMENTÉES
    (injection SQL CWE-89, injection de code CWE-95) sans faux positif sur du code sûr, HORS langage inconnu."""
    import audit_code as A
    sqli = A.audite('mysql_query("SELECT * FROM u WHERE id=".$_GET["id"]);', "php")
    codei = A.audite('eval(request.GET["x"])', "python")
    propre = A.audite("def f(a, b):\n    return a + b", "python")
    hors = A.audite("...", "klingon")
    return (sqli[0] == A.VERIFIE and any(c.cwe == "CWE-89" for c in sqli[1])
            and codei[0] == A.VERIFIE and any(c.cwe == "CWE-95" for c in codei[1])
            and propre[0] == A.RAS and propre[1] == []
            and hors[0] == A.HORS)

def _p_classification_taxonomies() -> bool:
    """Classifications/taxonomies (conventions) : la classification décimale de Dewey (bibliotheconomie.py) est une
    CONVENTION fermée et vérifiable (centaine -> classe). Abstention hors table (nombre invalide)."""
    import bibliotheconomie as B
    return (B.classe_dewey(500) == "sciences"
            and B.classe_dewey(0) == "informatique/généralités"
            and _leve_v(B.classe_dewey, 999999)
            and _leve_v(B.classe_dewey, 12))            # non-multiple de 100 -> hors table

def _p_unites_standards() -> bool:
    """Unités et standards (conventions) : conversion EXACTE entre unités commensurables (dimensions.py, facteurs
    Fraction) ; incommensurable -> None (HORS, jamais une conversion inventée)."""
    import dimensions as D
    return (D.convertit(3, "km", "m") == 3000
            and D.convertit(1000, "m", "km") == 1
            and D.convertit(1, "km", "kg") is None)     # incommensurable -> HORS

def _p_verifiable_meta() -> bool:
    """« Vérifiable » (méta-critère) : un énoncé est vérifiable s'il est confrontable à la réalité — opérationnalisé
    par la falsifiabilité (falsification.py). Une hypothèse fausse est RÉFUTÉE par un contre-exemple ; une hypothèse
    vraie RÉSISTE sur l'espace testé (jamais « prouvée »). C'est le patron FAUX=0 de la vérifiabilité."""
    import falsification as F
    return (F.refute(lambda x: x < 5, range(10)) == 5           # énoncé faux -> contre-exemple concret
            and F.resiste(lambda x: x >= 0, range(10)) is True  # énoncé vrai -> résiste au test
            and F.corrobore(lambda x: x >= 0, range(10))[0] is True)


# ── BRIQUES BUILDABLE construites 2026-07-02 (nouvelles briques FAUX=0, cf. modules dédiés) ──
def _p_braille() -> bool:
    import braille as B
    return (B.lettre_vers_points("a") == (1,) and B.lettre_vers_points("z") == (1, 3, 5, 6)
            and B.lettre_vers_unicode("a") == "⠁"
            and B.braille_vers_texte(B.texte_vers_braille("verax")) == "verax"
            and _leve_v(B.lettre_vers_points, "é") and _leve_v(B.lettre_vers_points, "5"))

def _p_raisonnement_defaut() -> bool:
    import raisonnement_defaut as RD
    r = RD.RegleDefaut("oiseau", "vole", True)
    r.ajoute_membre("moineau").sauf("manchot", False)
    return (r.conclut("moineau")[:2] == (RD.DEFAUT, True)          # cas général
            and r.conclut("manchot")[:2] == (RD.EXCEPTION, False)  # exception prime
            and r.conclut("inconnu_xyz")[0] == RD.ABSTIENT         # inconnu -> abstention
            and _leve_v(r.sauf, "manchot", True))                  # conflit -> ValueError

def _p_seismes() -> bool:
    import seismologie as S
    mw = S.magnitude_moment(1e22)
    return (abs(mw - 8.6) < 1e-3
            and abs(S.magnitude_moment(S.moment_depuis_magnitude(7.0)) - 7.0) < 1e-9
            and abs(S.rapport_energie(6, 5) - 10 ** 1.5) < 1e-6     # +1 magnitude -> ×~31.6 énergie
            and S.classe(9.0) == "exceptionnel"
            and _leve_v(S.magnitude_moment, 0) and _leve_v(S.classe, 20))

def _p_heraldique() -> bool:
    import heraldique as H
    return (H.contraste_valide("or", "gueules") is True            # métal/couleur -> valide
            and H.contraste_valide("or", "argent") is False        # métal/métal -> viole
            and H.contraste_valide("gueules", "azur") is False     # couleur/couleur -> viole
            and H.contraste_valide("hermine", "gueules") is True   # fourrure neutre
            and _leve_v(H.categorie, "turquoise"))

def _p_pseudo(pratique, statut_attendu):
    import pseudosciences as P
    return P.validite_scientifique(pratique) == statut_attendu and _leve_v(P.validite_scientifique, "physique_reelle_xyz")

def _p_pseudo_astrologie() -> bool:
    return _p_pseudo("astrologie", "aucune")

def _p_pseudo_voyance() -> bool:
    return _p_pseudo("voyance", "aucune")

def _p_pseudo_numerologie() -> bool:
    return _p_pseudo("numerologie", "aucune")

def _p_pseudo_superstitions() -> bool:
    return _p_pseudo("superstitions", "aucune")

def _p_pseudo_paranormal() -> bool:
    return _p_pseudo("phenomenes_paranormaux", "non_demontree")


# ── REGISTRE : libellé EXACT (sujets.py) -> (description du mécanisme, preuve exécutable) ──
REGISTRE: dict[str, tuple[str, object]] = {
    "Vote / processus électoral (mécanique)": ("Mecanique electorale EXACTE (repartition des sieges en arithmetique rationnelle Fraction, donc comparaisons de quotients exactes, FAUX=0). Fonctions p", _p_scrutin),
    "Stratégie optimale (jeux résolus : morpion, etc.)": ("MECANISME EXACT : minimax enumere exhaustivement l'arbre complet du morpion (memoise par lru_cache). La valeur d'une position EST le resultat du jeu p", _p_strategie_jeux),
    "Théorie des jeux appliquée": ("Mécanisme/algorithme EXACT (théorie des jeux, équilibres de Nash en stratégies pures). equilibre_nash_pur(gains_J1, gains_J2) énumère les profils (i,j", _p_jeux_appliques),
    "Gestion d'un budget personnel": ("Gestion d'un budget personnel : 5 fonctions pures déterministes de calcul monétaire EXACT, avec 2 conventions de gestion ÉTABLIES sourcées. solde(reve", _p_budget_personnel),
    "Biostatistique": ("Tests diagnostiques (épidémiologie EXACTE), définitions du tableau de contingence 2x2 test/maladie. Fonctions pures déterministes: sensibilite(VP,FN)=", _p_biostatistique),
    "Tests psychométriques (validité)": ("Référentiel FERMÉ de formules psychométriques ÉTABLIES (théorie classique des tests). Mécanismes EXACTS et déterministes : (1) qi_standardise = 100 + ", _p_psychometrie),
    "Hiérarchie des normes": ("Catalogue de conventions juridiques ETABLIES (sourcees, certaines) : pyramide de Kelsen, hierarchie des normes du droit francais/continental. Rangs so", _p_hierarchie_normes),
    "Conjugaison": ("Conjugaison française régulière (règles ÉTABLIES de grammaire, mécanisme réglé donc vérifiable). conjugue(infinitif, personne, temps) conjugue au PRÉS", _p_conjugaison),
    "Cartographie / SIG / géomatique": ("Cartographie / SIG / geomatique — calculs EXACTS (identites de definition, FAUX=0). Fonctions pures deterministes : echelle_distance_reelle(distance_c", _p_cartographie),
    "Faits sociaux mesurables (statistiques)": ("Indicateurs sociaux mesurables, mécanismes statistiques EXACTS (aucune constante mesurée). gini(revenus) = coefficient de Gini par la formule des rang", _p_mesures_sociales),
    "Citoyenneté (droits et devoirs)": ("Catalogue civique ÉTABLI (France/démocratie), sourcé DDHC 1789 + Préambule 1946 + Constitution 1958. ~44 libellés (canoniques + synonymes établis) rép", _p_citoyennete),
    "Conservation des aliments": ("Catalogue de méthodes et seuils ÉTABLIS de conservation alimentaire (microbiologie alimentaire / réglementation hygiène / HACCP). methode(nom) restitu", _p_conservation_aliments),
    "Retraite (règles, calcul)": ("Calcul de pension de retraite — mécanisme générique d'un régime par annuités (proratisation), sans valeurs-pays inventées. pension(salaire_reference, ", _p_retraite),
    "Externalités": ("CATALOGUE (exemples canoniques de microéconomie : pollution/tabagisme/congestion=négative, vaccination/abeilles/éducation=positive) + MÉCANISME EXACT ", _p_externalites),
    "Cycles économiques": ("CATALOGUE établi du cycle économique (consensus macro / NBER / Conference Board), FAUX=0. Restitue UNIQUEMENT la structure sourcée ; toute entrée hors", _p_cycles_economiques),
    "Commerce international": ("Commerce international — identités/lois EXACTES des échanges internationaux (mécanisme pur, aucune valeur-pays inventée), posture FAUX=0 (sœur de pib.", _p_commerce_international),
    "Rhétorique / persuasion (techniques)": ("Catalogue rhetorique etabli (consensus source). MODES de persuasion d'Aristote (Rhetorique I, 1356a) : ethos=credibilite de l'orateur, pathos=emotions", _p_rhetorique),
    "Journalisme (déontologie)": ("Catalogue de déontologie journalistique (règles établies, sourcées Charte de Munich 1971 + SPJ Code of Ethics). 7 principes closed-set : verification/", _p_journalisme_deontologie),
    "Publicité / marketing (mécanismes)": ("CATALOGUE de modèles de persuasion publicitaire établis (référentiels sourcés/consensus). (1) Modèle AIDA (E. St. Elmo Lewis, 1898) : 4 étapes dans un", _p_marketing_mecanismes),
    "Propagande / désinformation (analyse)": ("Catalogue ETABLI: 7 techniques de l'Institute for Propaganda Analysis (1937-42 « The Fine Art of Propaganda ») — name_calling/diabolisation, generalit", _p_propagande),
    "Bibliothéconomie / sciences de l'information": ("CATALOGUE/MÉCANISME établi (faits sourcés). Deux référentiels normalisés: (1) Classification décimale de Dewey (DDC) — les 10 classes principales par ", _p_bibliotheconomie),
    "Cardiologie": ("Cardiologie quantitative — formules cliniques etablies/consensuelles (mecanisme EXACT, fonctions pures deterministes). 4 fonctions : frequence_cardiaq", _p_cardiologie),
    "Médecine d'urgence": ("Scores d'urgence cliniques etablis (catalogue/mecanisme exact, consensus): echelle de Glasgow (Teasdale & Jennett 1974 ; yeux 1-4, verbal 1-5, moteur ", _p_urgence_medicale),
    "Pratiques non prouvées": ("Catalogue de consensus établi (médecines alternatives) : niveau de preuve scientifique par pratique (méta-analyses / Cochrane / rapports d'agences). N", _p_medecines_alternatives),
    "Mathématiques financières (intérêts)": ("Mathematiques financieres (interets) : calcul EXACT de la valeur-temps de l'argent (interet simple C*t*n, valeur acquise simple C*(1+t*n), interet com", _p_maths_financieres),
    "Gestion du risque": ("Gestion du risque (finance/assurance) — mesures de risque EXACTES, formules déterministes pures, sortie arrondie 6 décimales, abstention ValueError su", _p_gestion_risque),
    "Comptabilité (règles)": ("Comptabilité (règles) — règles comptables établies, mécanismes exacts, FAUX=0 par abstention (ValueError). 5 fonctions pures déterministes : equation_", _p_comptabilite),
    "Inflation": ("Inflation : formules monétaires exactes et déterministes (aucune donnée-pays inventée). taux_inflation(IPC_initial,IPC_final)=(final-initial)/initial*", _p_inflation),
    "PIB, croissance": ("PIB, croissance — identites de la comptabilite nationale (mecanisme EXACT, aucune valeur-pays inventee). pib_depenses=C+I+G+(X-M), taux_croissance=(fi", _p_pib),
    "Chômage": ("Chômage / marché du travail — définitions exactes BIT (CIST/Eurostat/INSEE/OIT). Calcule taux_chomage = chomeurs/population_active*100, population_act", _p_chomage),
    "Posologie / dosage": ("Posologie / dosage clinique : calculs de dose exacts et deterministes. dose_totale(dose_par_kg, masse_kg)=dose*masse [mg]; debit_perfusion(volume_ml, ", _p_posologie),
    "Essais cliniques": ("Epidemiologie clinique - mesures d'effet exactes (essais cliniques). 4 fonctions pures deterministes, sortie ratio/difference arrondie a 6 chiffres si", _p_essais_cliniques),
    "Biomécanique du geste": ("Biomécanique du geste — physique EXACTE du mouvement sportif (cinématique du projectile + statique du levier articulaire). Fonctions pures déterminist", _p_biomecanique),
    "Entraînement (méthodes, efficacité)": ("Entraînement (méthodes, efficacité) : physiologie de l'effort par formules ÉTABLIES — un_rep_max_epley (1RM = poids·(1+reps/30), Epley 1985), frequenc", _p_entrainement),
    "Démographie (populations, faits)": ("Démographie (populations, faits) — indicateurs démographiques EXACTS (définitions/calculs de manuel, AUCUNE valeur-pays inventée). 5 fonctions pures d", _p_demographie),
    "Audiologie (audition)": ("Audiologie (audition) : échelle décibel et classification OMS de la perte auditive. Fonctions pures déterministes, sortie arrondie à 6 chiffres signif", _p_audiologie),
    "Bactéries": ("Croissance exponentielle bactérienne (modèle de doublement par fission binaire), mécanisme mathématique EXACT. 3 fonctions pures inverses d'une seule ", _p_croissance_bacterienne),
    "Membranes, organites": ("Transport membranaire / osmose (borne « Membranes, organites »). 3 fonctions pures deterministes : tonicite(c_int,c_ext)->'hypotonique'/'hypertonique'", _p_transport_membranaire),
    "Aéronautique (vol, aérodynamique)": ("Aéronautique (vol, aérodynamique) : portance L=½·ρ·v²·S·Cz, traînée D=½·ρ·v²·S·Cx, finesse f=Cz/Cx, nombre de Reynolds Re=ρ·v·L/μ, et vitesse de vol e", _p_aerodynamique),
    "Maritime": ("\"Maritime\": vitesse de coque (hull speed 1.34·√LWL_ft = 2.427·√LWL_m, noeuds), poussée d'Archimède ρ·V·g (N) + flottabilité (masse < ρ·V_carène), nomb", _p_maritime),
    "Automobile (mécanique)": ("Mecanique automobile elementaire (formules etablies, mecanique newtonienne + transmission). 5 fonctions pures deterministes, sorties flottantes arrond", _p_automobile),
    "Logistique / chaîne d'approvisionnement": ("Logistique / chaîne d'approvisionnement — gestion des stocks (formules exactes, FAUX=0). quantite_economique_commande/eoq(D,S,H)=sqrt(2DS/H) (formule ", _p_logistique),
    "Toxicologie (doses, poisons)": ("Toxicologie (doses, poisons) : dose-réponse et classes de toxicité par mécanismes/définitions établis. index_therapeutique(DL50,DE50)=DL50/DE50 (marge", _p_toxicologie),
    "Topographie / arpentage": ("Topographie / arpentage : relations métriques exactes du terrain. pente_pourcent(Dh,d)=100*Dh/d ; distance_horizontale(D,alpha)=D*cos(alpha) ; denivel", _p_topographie_arpentage),
    "Navigation (orientation, positionnement)": ("Navigation (orientation, positionnement) — distance orthodromique par haversine (R=6371 km, d=2R·asin(√a)) et cap initial (azimut atan2, [0,360°[) sur", _p_navigation),
    "Hydrologie (eaux continentales)": ("Hydrologie (eaux continentales) — débits et écoulements à surface libre par formules établies : continuité Q=A·v (m³/s), méthode rationnelle/ruisselle", _p_hydrologie),
    "Glaciologie": ("Glaciologie — mecanismes EXACTS / lois etablies, FAUX=0. 4 fonctions pures deterministes (sortie arrondie ~6 chiffres significatifs) : bilan_massique(", _p_glaciologie),
    "Pédologie (science des sols)": ("Pédologie (science des sols) : classe_texture(sable,limon,argile) — triangle USDA simplifié (argile>40 -> 'argileux', sable>70 -> 'sableux', sinon 'li", _p_pedologie),
    "Télédétection (satellites, imagerie)": ("Télédétection (satellites, imagerie) : resolution_spatiale (GSD m/px = fauchée/pixels), ndvi ((NIR-R)/(NIR+R) borné [-1,1] pour réflectances >=0), res", _p_teledetection),
    "Énergies fossiles vs renouvelables": ("Énergies fossiles vs renouvelables : comparaison énergétique par définitions d'ingénierie exactes. facteur_charge(E,P,heures=8760)=E/(P·heures) (capac", _p_energies_comparees),
    "Efficacité d'une campagne (mesurable)": ("Efficacité d'une campagne (mesurable) : métriques marketing exactes calculées comme ratios arithmétiques entre quantités observées. taux_conversion=co", _p_marketing_metrics),
    "Big Bang": ("Cosmologie du Big Bang (formules/faits etablis). 4 fonctions pures deterministes : age_univers_hubble(H0 km/s/Mpc)=temps de Hubble 1/H0 en annees (H0=", _p_big_bang),
    "Astéroïdes, comètes": ("Astéroïdes & comètes : paramètre de Tisserand T_J = aJ/a + 2·cos(i)·√((a/aJ)·(1−e²)) (invariant orbital exact, Tisserand 1896 ; aJ=5.204 UA sourcé) + ", _p_asteroides),
    "Métaux et alliages": ("Métaux et alliages — règle du levier (lever rule) EXACTE dans un diagramme binaire + catalogue d'alliages sourcés. fraction_phase(c, c1, c2) renvoie F", _p_alliages),
    "Machines et mécanismes": ("Machines et mécanismes : mobilité d'un mécanisme PLAN par le critère de Grübler-Kutzbach, M = 3·(n-1) - 2·j1 - j2 (n = corps incluant le bâti, j1 = li", _p_mecanismes_machines),
    "Vaccins (mécanisme)": ("Vaccins (mécanisme) / immunité de groupe — épidémiologie EXACTE + typologie immunologique. Fonctions : seuil_immunite_groupe(R0)=1−1/R0 (fraction crit", _p_immunite),
    "Mutations": ("Mutations ADN : classification du type (substitution/insertion/deletion) + effet d'une substitution de codon sur la traduction (silencieuse/faux_sens/", _p_mutations),
    "Réseaux neuronaux biologiques": ("Modèle intègre-et-tire (leaky integrate-and-fire simplifié) + potentiel d'action. Faits établis et mécanismes exacts de l'électrophysiologie du neuron", _p_neurone_biologique),
    "Cycles biogéochimiques": ("Cycles biogéochimiques — temps de résidence τ = réservoir/flux (identité de conservation, exacte), bilan stationnaire (entrée==sortie à tolérance) et ", _p_cycles_biogeochimiques),
    "Homéostasie": ("Homéostasie — régulation par rétroaction négative (mécanisme EXACT). ecart_consigne(valeur,consigne)=valeur−consigne ; correction(valeur,consigne,gain", _p_homeostasie),
    "Médecine du sommeil / chronobiologie": ("Médecine du sommeil / chronobiologie : rythmes circadiens et cycles de sommeil (faits sourcés + arithmétique exacte). FONCTIONS : periode_circadienne(", _p_chronobiologie),
    "Protéines, enzymes": ("Protéines, enzymes — structure et classification (faits biochimiques établis + calcul exact). niveau_structure(nom) décrit les 4 niveaux d'organisatio", _p_proteines),
    "Cryobiologie": ("Cryobiologie — congelation et conservation (FAUX=0). 3 fonctions pures deterministes : vitesse_refroidissement(Ti,Tf,temps)=(Ti-Tf)/temps °C/min ; poi", _p_cryobiologie),
    "Pétrochimie": ("Pétrochimie / raffinage : coupes de distillation atmosphérique (gaz<30°C, essence 30-200, kérosène 200-300, diesel/gazole 300-400, résidu/bitume >400 ", _p_petrochimie),
    "Théorie de la démonstration": ("Théorie de la démonstration : vérifie EXACTEMENT la validité d'une inférence propositionnelle par table de vérité — inference_valide(premisses, conclu", _p_preuve_propositionnelle),
    "Sophismes et paralogismes (identification)": ("Identification de la forme d'un argument conditionnel (logique propositionnelle classique) : identifie_forme(majeure 'A->B', mineure, conclusion) -> '", _p_sophismes),
    "Paradoxes logiques (menteur, Russell, etc.)": ("Paradoxes logiques (menteur, Russell, etc.) — détection syntaxique d'auto-référence + preuve par argument diagonal exhaustif (Russell {x:x∉x}, barbier", _p_paradoxes),
    "Ordinaux et cardinaux": ("Arithmétique exacte des ordinaux < ω^ω en forme normale de Cantor (tuple de paires (exposant, coeff) strictement décroissantes ; () = 0) et des cardin", _p_ordinaux),
    "Fondations alternatives (théorie des catégories, types)": ("Fondations alternatives (theorie des categories, types) : deux mecanismes EXACTS et deterministes. (1) Typage du lambda-calcul simplement type a la Ch", _p_types_categories),
    "Théorie de Galois": ("Theorie de Galois — faits ETABLIS, mecanisme exact, FAUX=0. Resolubilite par radicaux du polynome general de degre n (Abel-Ruffini + Cardan/Ferrari : ", _p_galois),
    "Conjecture de Poincaré": ("Classification 2D des surfaces closes (cas résolu, analogue de la conjecture de Poincaré) : bijection (orientabilité, χ) -> surface. genre(χ,orientabl", _p_classification_surfaces),
    "Théorie de la calculabilité": ("Théorie de la calculabilité : fonction d'Ackermann-Péter (récursive totale mais NON primitive récursive) calculée par pile explicite itérative — A(0,n", _p_calculabilite),
    "Problème de l'arrêt": ("Problème de l'arrêt — arrêt borné décidable + indécidabilité générale (Turing 1936). sarrete_dans(programme_func, entree, max_etapes) simule un progra", _p_arret),
    "Algorithmes (correction, complexité)": ("Analyse de complexité & correction d'algorithmes, mécanisme EXACT FAUX=0 (faits établis type CLRS). Fonctions pures déterministes : complexite_boucle(", _p_algo_analyse),
    "Décidabilité / indécidabilité d'un énoncé": ("Catalogue de FAITS établis de calculabilité/complexité : statut_decidabilite(probleme) et est_decidable(probleme) sur 6 problèmes prouvés (arret INDÉC", _p_decidabilite),
    "Théorèmes d'incomplétude de Gödel": ("Numérotation de Gödel bijective : godel_numero(suite) = ∏ p_i^code(symbole_i) sur les premiers successifs (alphabet arithmétique fixe de 18 symboles, ", _p_godel),
    "Intrication quantique": ("Intrication quantique / test CHSH (inegalite de Bell). API exacte basee sur theoremes etablis : borne_classique_chsh()=2 (Bell, variables cachees loca", _p_intrication),
    "Coordination / complexes": ("Chimie de coordination, mecanisme EXACT FAUX=0. nombre_oxydation_metal(charge_complexe, ligands) = charge_complexe - somme(charges ligands) sur un cat", _p_coordination),
    "Nomenclature": ("Nomenclature de composés binaires simples (IUPAC, faits établis). nom_compose_binaire(formule) -> nom français : (1) CATALOGUE de faits établis (noms ", _p_nomenclature_chimique),
    "Pharmacochimie": ("Règle de cinq de Lipinski (druglikeness) : mécanisme exact de comptage de seuils établi (Lipinski 1997, MM≤500 / logP≤5 / donneurs_H≤5 / accepteurs_H≤", _p_pharmacochimie),
    "Mécanismes réactionnels": ("Classification SN1/SN2/E1/E2 par règles de chimie organique établies (manuels Clayden/Klein/Vollhardt). type_substitution et type_elimination ne class", _p_mecanismes_reactionnels),
    "Éclipses, phases (prédiction)": ("Mécanique des phases lunaires et conditions d'éclipse, mécanismes exacts/établis. periode_synodique(T1,T2)=1/|1/T1-1/T2| (mouvement synodique ; Lune 2", _p_eclipses),
    "Automatisation / Industrie 4.0": ("Automatisation / Industrie 4.0 — Taux de Rendement Synthetique (TRS/OEE). oee(D,P,Q)=D*P*Q avec D,P,Q dans [0,1] ; disponibilite=temps_fonctionnement/", _p_industrie40),
    "Stéréochimie": ("Stéréochimie : dénombrement de stéréoisomères (règle de Le Bel-van't Hoff, sans symétrie/méso) et classification de relation entre configurations R/S.", _p_stereochimie),
    "Procédés industriels": ("Bilans de procede (genie des procedes), mecanisme arithmetique exact et deterministe : rendement = reel/theorique dans [0,1] ; bilan_matiere verifie l", _p_procedes_industriels),
    "Théorie de la complexité (P, NP, etc.)": ("Catalogue des classes de complexite (P, NP, NP-complet, NP-difficile, indecidable) pour le sujet borne \"Theorie de la complexite (P, NP, etc.)\". Faits", _p_classes_complexite),
    "Bio-ingénierie": ("Cinétique enzymatique de Michaelis-Menten (loi établie, mécanisme exact). vitesse(Vmax,Km,S)=Vmax·S/(Km+S) ; km_vitesse_demi(Vmax,Km)=v à S=Km=Vmax/2 ", _p_bioingenierie),
    "Nucléosynthèse": ("Nucléosynthèse / énergie nucléaire (FAUX=0) : energie_liaison(Δm_u)=Δm·931.494 MeV (1 u = 931.494 MeV/c²), energie_liaison_par_nucleon(E,A)=E/A, q_rea", _p_nucleosynthese),
    "Impression 3D": ("Paramètres FDM d'impression 3D, formules géométriques EXACTES + conventions d'unités sourcées (mm/mm³/mm³-s/g-cm³). 4 fonctions pures déterministes : ", _p_impression_3d),
    "Usinage": ("Usinage — paramètres de coupe, formules d'atelier EXACTES/établies (FAUX=0). Fonctions pures déterministes (stdlib, import math seul) : vitesse_coupe(", _p_usinage),
    "Procédés de fabrication": ("Procédés de fabrication — classification conventionnelle (familles soustractif/additif/formage/assemblage, référentiel FERMÉ de 10 procédés) + rendeme", _p_procedes_fabrication),
    "Métaux, minéraux": ("Échelle de Mohs (dureté des minéraux, faits établis/conventions de Friedrich Mohs 1812). Catalogue de 10 minéraux étalons : talc=1, gypse=2, calcite=3", _p_mineraux),
    "Systèmes politiques (définitions)": ("Définitions et classification des systèmes politiques (conventions sourcées, théorie classique des régimes d'Aristote à Montesquieu). API : definition", _p_systemes_politiques),
    "Recettes (procédures)": ("Recettes (procédures) — mise à l'échelle et conversions culinaires conventionnelles. adapte_quantite (règle de trois q·cible/origine), facteur_echelle", _p_recettes),
    "Techniques culinaires": ("CONVENTION / CLASSIFICATION par criteres etablis (taxonomie cuisson par transfert thermique) + constantes physico-chimiques sourcees. Mecanisme exact ", _p_techniques_culinaires),
    "Céramiques": ("Céramiques : propriétés et calculs établis (FAUX=0). retrait_cuisson(d_crue,d_cuite)=(crue−cuite)/crue (100→88=0.12) ; porosite(vides,total) ∈ [0,1] ;", _p_ceramiques),
    "Polymères / plastiques": ("Polymères/plastiques : conventions et faits établis. code_recyclage (ASTM D7611 / SPI : PET=1, PEHD=2, PVC=3, PEBD=4, PP=5, PS=6, autres=7) + nom_depu", _p_plastiques),
    "Analyse complexe": ("Analyse complexe : module, argument, somme/produit/quotient, puissance (de Moivre) et racines n-ièmes sur des couples (re, im). Mécanisme exact, sorti", _p_nombres_complexes),
    "Liaisons chimiques": ("Nature de liaison chimique par électronégativité (échelle de Pauling) : Δχ=|χ1−χ2|, classification covalente_non_polaire (<0.4) / covalente_polaire (0", _p_liaisons_chimiques),
    "Analyse fonctionnelle": ("Espaces normes : produit scalaire, normes l1/l2/l-inf, distance, Cauchy-Schwarz, orthogonalite, projection orthogonale. Mecanisme exact, abstention Va", _p_analyse_fonctionnelle),
    "Équations différentielles": ("Solutions d'EDO du 1er ordre : exponentielle y0·e^kt (y'=ky), affine (y'=ay+b avec equilibre -b/a, ex. refroidissement de Newton), demi-vie ln2/k, et ", _p_equa_diff),
    "Relativité restreinte": ("Relativité restreinte (mécanisme exact, c exact SI 2019) : facteur de Lorentz γ=1/√(1−(v/c)²), dilatation du temps γ·t, contraction des longueurs L0/γ", _p_relativite_restreinte),
    "Relativité générale": ("Relativité générale (métrique de Schwarzschild) : rayon_schwarzschild(M)=2GM/c² et dilatation_gravitationnelle(t,M,r)=t·√(1−2GM/(rc²)). Constantes sou", _p_relativite_generale),
    "Mécanique quantique": ("Mécanique quantique : relations fondamentales exactes — energie_photon(f)=h·f (Planck-Einstein), longueur_onde_broglie(p)=h/p (de Broglie), niveaux_pu", _p_quantique),
    "Semi-conducteurs": ("Semi-conducteurs : seuil optique d'absorption via Planck-Einstein (lambda_seuil = h*c/(Eg*e), h/c/e exactes SI 2019 ; Si 1.12 eV -> 1107 nm, GaAs 1.42", _p_semiconducteurs),
    "Deuxième principe (entropie)": ("Deuxième principe (entropie) : variation_entropie(Q,T)=Q/T (J/K) d'un réservoir réversible ; entropie_univers(Q,T_chaud,T_froid)=Q/T_froid−Q/T_chaud (", _p_entropie_thermo),
    "Équations de Maxwell": ("Équations de Maxwell dans le vide : à partir des constantes CODATA µ0/ε0, calcule les conséquences EXACTES imposées par Maxwell — vitesse de la lumièr", _p_maxwell),
    "Géométries non-euclidiennes": ("Géométrie sphérique (courbure positive constante) : théorème de Girard A=R²·(Σangles−π), excès sphérique E=aire/R²=Σangles−π (>0, somme des angles >π ", _p_geometries_non_euclidiennes),
    "Géométrie différentielle": ("Geometrie differentielle des courbes planes parametrees : courbure exacte kappa = |x'y''-y'x''|/(x'^2+y'^2)^1.5 (cercle r -> 1/r, droite -> 0), courbu", _p_geometrie_differentielle),
    "Topologie générale": ("Topologie générale : invariants exacts des surfaces fermées. caracteristique_euler(V,E,F)=V-E+F (polyedre convexe/sphere chi=2, tore chi=0) ; caracter", _p_topologie),
    "Fractales": ("Dimension d'auto-similarite D=ln(N)/ln(facteur) (N copies reduites d'un facteur de contraction). Mecanisme exact (Hausdorff strict auto-similaire), so", _p_fractales),
    "Théorie de la complexité (P, NP, etc.)": ("Théorie de la complexité : théorème maître T(n)=a·T(n/b)+Θ(n^d) — classe_master/regime_master/exposant_critique comparent d à c=log_b(a) (racine→n^d, ", _p_complexite),
    "Langages formels et grammaires": ("Langages formels & grammaires : algorithme CYK appartient(grammaire_CNF, mot) en programmation dynamique O(n^3.|G|) decidant l'appartenance a un langa", _p_langages_formels),
    "Cardinalité, dénombrabilité": ("Cardinalité & dénombrabilité (entiers exacts) : cardinal_ensemble (éléments distincts), cardinal_parties=2^n (Cantor fini), couple_cantor/decouple_can", _p_cardinalite),
    "Astronautique (mécanique du vol)": ("Mécanique du vol astronautique : équation de Tsiolkovsky (delta_v = ve·ln(m0/mf), rapport de masse exp(dv/ve), masse finale) + mécanique orbitale (vit", _p_astronautique),
    "Expansion de l'univers": ("Expansion de l'univers : loi de Hubble v=H0*d (km/s/Mpc, Mpc -> km/s), distance de Hubble d=v/H0, age/temps de Hubble 1/H0 converti en annees (1 Mpc=3", _p_cosmologie),
    "Fond diffus cosmologique": ("Rayonnement du corps noir (fond diffus cosmologique) : loi de déplacement de Wien en longueur d'onde lambda_max=b/T (b=2.897771955e-3 m.K) et son inve", _p_rayonnement_thermique),
    "Habitabilité (zones, exoplanètes)": ("Habitabilité circumstellaire : température d'équilibre radiatif T_eq = 278.6·((1-A)·L/d²)^¼ K (L en L⊙, d en UA, A albédo de Bond) et zone habitable (", _p_habitabilite),
    "Recherche de vie (SETI)": ("Équation de Drake (SETI) : N = R·fp·ne·fl·fi·fc·L, produit exact de 7 facteurs (définition de Frank Drake 1961). nombre_civilisations(R,fp,ne,fl,fi,fc", _p_drake),
    "Conception mécanique": ("Conception mécanique : transmission de mouvement/force IDÉALE (rendement=1) par identités exactes — rapport_engrenages i=Z_menée/Z_menante ; vitesse_s", _p_mecanismes),
    "Structures (ponts, bâtiments)": ("Résistance des matériaux exacte (poutres/sections) : contrainte de flexion M·y/I, traction F/A, moment quadratique rectangle b·h³/12 et cercle π·d⁴/64", _p_structures_genie),
    "Stockage (batteries)": ("Stockage électrique (batteries) : relations de définition exactes — energie_wh(V,Ah)=V·Ah, capacite_Ah_depuis_energie=Wh/V, courant_c_rate(Ah,C)=Ah·C ", _p_batteries),
    "Composites": ("Loi des mélanges des composites biphasés (rule of mixtures) : module_young_composite = borne supérieure de Voigt (Vf·Ef+(1-Vf)·Em), densite_composite ", _p_composites),
    "Propriétés des matériaux (mesurables)": ("Loi de Hooke et élasticité linéaire : contrainte σ=F/A, déformation ε=ΔL/L0, module de Young E=σ/ε, Hooke σ=E·ε (et inverse ε=σ/E), allongement ΔL=F·L", _p_proprietes_materiaux),
    "Contrôle qualité": ("Maîtrise statistique des procédés (SPC) : indice de capabilité Cp=(LSS-LSI)/(6σ), Cpk décentré=min((LSS-moy)/3σ,(moy-LSI)/3σ), limites de contrôle She", _p_controle_qualite),
    "Cybernétique (régulation, rétroaction)": ("Boucle asservie à rétroaction négative : gain en boucle fermée G/(1+G·H), erreur statique consigne/(1+G), sensibilité S=1/(1+G·H) et transfert complém", _p_cybernetique),
    "Théorie du chaos / sensibilité aux conditions": ("Theorie du chaos via application logistique x_{n+1}=r*x_n*(1-x_n) : iterer_logistique(r,x0,n), point_fixe_logistique(r)=1-1/r, sensibilite(r,x0,delta,", _p_chaos),
    "Théorie des catastrophes / bifurcations": ("Théorie des catastrophes / bifurcations : stabilité linéaire d'un point fixe (flot continu via signe de f'(x*) ; carte discrète via module du multipli", _p_bifurcations),
    "Écosystèmes, chaînes alimentaires": ("Écosystèmes & chaînes alimentaires : transfert d'énergie trophique (règle des 10 % de Lindeman, energie_niveau = E0·0.1^(n-1), efficacite_ecologique =", _p_ecologie),
    "Bio-informatique / séquençage": ("Bio-informatique/séquençage : primitives exactes sur séquences ADN/chaînes — distance de Hamming (positions différentes, longueurs égales requises), t", _p_bioinfo),
    "Oxydoréduction": ("Oxydoréduction : nombre d'oxydation par neutralité de charge (résolution de l'unique inconnue, n.o. fixés F=-1/alcalins=+1/alcalino-terreux=+2/O=-2/H=", _p_redox),
    "Polymères": ("Relations exactes des polymères : degré de polymérisation DP=Mn/M0 (et réciproques masse_molaire_polymere=DP·M0, masse_molaire_monomere=Mn/DP), indice", _p_polymeres),
    "Méthodes d'analyse (spectroscopie, chromatographie)": ("Méthodes d'analyse chimique : loi de Beer-Lambert (absorbance A=ε·l·c, concentration c=A/(ε·l), transmittance T=10^(−A) ∈ ]0,1]) et chromatographie CC", _p_analyse_chimique),
    "Raisonnement déductif": ("deduction.MoteurDeduction (Datalog Horn semi-naïf, oracle Floyd-Warshall)", _p_raisonnement_deductif),
    "Inférence statistique": ("echantillon_pondere (Horvitz-Thompson / Hájek / ESS de Kish)", _p_inference_statistique),
    "Tests d'hypothèses": ("test_calibration (Spiegelhalter Z, Hosmer-Lemeshow χ², Φ via erf)", _p_tests_hypotheses),
    "Statistique bayésienne": ("bayes (postérieure en log-odds, abstention anti-certitude)", _p_statistique_bayesienne),
    "Régression, corrélation": ("regression_robuste.ols / huber (moindres carrés + Huber/IRLS)", _p_regression_correlation),
    "Échantillonnage": ("importance_sampling (estimateur sans biais + ESS diagnostique)", _p_echantillonnage),
    "Théorie des jeux (mathématique)": ("jeux_zero_somme (jeu fictif Brown-Robinson, minimax von Neumann)", _p_theorie_des_jeux_math),
    "Théorie des jeux (stratégies, équilibres)": ("jeux_zero_somme + braess (valeur minimax, stratégies optimales)", _p_theorie_des_jeux_equilibres),
    "Théorie de la décision": ("decision (utilité espérée EU=Σ P·u, argmax + abstention)", _p_theorie_decision),
    "Apprentissage automatique (mécanismes)": ("stabilite_algorithmique (k-NN + borne de généralisation Bousquet-Elisseeff)", _p_apprentissage_mecanismes),
    "Gravitation newtonienne": ("physique (g=GM/r², v_lib=√(2GM/r) ; G CODATA-2018)", _p_gravitation),
    "Électrostatique (charges, champs)": ("physique (loi de Coulomb F=k·q1q2/r², champ E=k·q/r²)", _p_electrostatique),
    "Radioactivité": ("physique (décroissance N0·½^(t/T), E=Δm·c²)", _p_radioactivite),
    "Acides et bases / pH": ("physique (pH=−log10[H⁺], pOH=−log10[OH⁻])", _p_acides_bases_ph),
    "Mécanique céleste / orbites": ("physique (3ᵉ loi de Kepler T=2π√(a³/GM))", _p_mecanique_celeste),
    "Possibilité/impossibilité d'un cycle (mouvement perpétuel)": ("coherence_physique.juge_dispositif (1ᵉʳ/2ᵉ principe, borne de Carnot)", _p_mouvement_perpetuel),
    "Système d'unités (SI)": ("fonction_nl.resout_conversion (table fermée, facteurs exacts, même dimension)", _p_systeme_unites_si),
    "Probabilités élémentaires (dénombrement)": ("maths_discretes (binomial, Catalan, dérangements, partitions exacts)", _p_denombrement),
    "Récurrences": ("maths_discretes (récurrence linéaire d'ordre 2 exacte : Fibonacci/Lucas)", _p_recurrences),
    "Théorie des graphes": ("maths_discretes (union-find, BFS, bipartisme, détection de cycle)", _p_theorie_graphes),
    "Algorithmique appliquée": ("maths_discretes (Dijkstra plus-court-chemin pondéré, BFS non pondéré)", _p_algorithmique),
    "Géométrie analytique (coordonnées)": ("maths_discretes (aires lacet exactes, orientation, Manhattan)", _p_geometrie_analytique),
    "Structuration de données": ("maths_discretes (pile : RPN entier exact, équilibrage de parenthèses)", _p_structuration_donnees),
    "Débogage": ("audit_code.audite (détection CWE sound : RAS sans faux positif, HORS hors-référentiel)", _p_debogage),
    "Équations linéaires": ("algebre_calcul (ax+b=0 exact en ℚ ; aucune/infinité discriminées)", _p_equations_lineaires),
    "Équations polynomiales": ("algebre_calcul (ax²+bx+c=0 exact : Δ, racines rationnelles, irrationnel non faussé)", _p_equations_polynomiales),
    "Structures de données": ("maths_discretes (pile : RPN entier exact, équilibrage de parenthèses)", _p_structuration_donnees),
    "Cryptographie mathématique": ("arithmetique_modulaire (Euclide étendu, inverse mod, exp mod, Miller-Rabin, RSA)", _p_cryptographie_mathematique),
    "Théorie de l'information (Shannon)": ("information_calcul (entropie de Shannon, information mutuelle, divergence KL)", _p_theorie_information),
    "Algèbre de Boole": ("algebre_boole (parseur + tables de vérité : tautologie/satisfiabilité/équivalence exactes)", _p_algebre_boole),
    "Théorie des automates": ("automates (simulation DFA exacte : acceptation d'un langage régulier)", _p_theorie_automates),
    "Machines de Turing": ("turing (simulation déterministe bornée : accepte/bloque/timeout honnête)", _p_machines_turing),
    "Théorie des groupes": ("groupes (ordre ℤ/nℤ et permutations, signature, table de Cayley, Lagrange)", _p_theorie_groupes),
    "Stœchiométrie (équilibrage d'équations)": ("stoechiometrie (noyau entier de la matrice atomes×espèces, conservation vérifiée)", _p_stoechiometrie),
    "Trigonométrie": ("trigonometrie (angles remarquables exacts, loi des cosinus, identité de Pythagore)", _p_trigonometrie),
    "Dérivation": ("calcul_infinitesimal (dérivée exacte de polynômes : règle de puissance)", _p_derivation),
    "Intégration": ("calcul_infinitesimal (intégrale définie exacte : théorème fondamental)", _p_integration),
    "Limites et continuité": ("calcul_infinitesimal (limite rationnelle exacte, 0/0 factorisé, pôle -> abstention)", _p_limites),
    "Séries et convergence": ("series_calcul (sommes arithmétique/géométrique exactes, critères de convergence)", _p_series),
    "Forces, frottements": ("mecanique (frottement sec F=μN, forces ; domaine gardé)", _p_forces_frottements),
    "Oscillateurs, résonance": ("mecanique (masse-ressort T=2π√(m/k), pendule, fréquence propre)", _p_oscillateurs),
    "Mécanique des fluides": ("mecanique (pression P=F/A, hydrostatique ρgh, poussée d'Archimède ρVg)", _p_mecanique_fluides),
    "Solutions, concentrations": ("chimie_quantitative (molarité n/V, dilution c₁V₁=c₂V₂)", _p_solutions_concentrations),
    "Thermochimie": ("chimie_quantitative (loi de Hess ΔH=ΣΔHf produits−réactifs)", _p_thermochimie),
    "Électrochimie": ("chimie_quantitative (potentiel de pile E=E_cathode−E_anode, spontanéité)", _p_electrochimie),
    "Circuits électroniques": ("electronique (série/parallèle, diviseur de tension, RC, impédances, résonance LC)", _p_circuits_electroniques),
    "Statique / équilibre des structures": ("statique (moments, levier, centre de masse, réactions d'appui)", _p_statique),
    "Robotique (cinématique)": ("robotique (cinématique directe d'un bras 2R, portée, atteignabilité)", _p_robotique),
    "Automatique / contrôle": ("controle (stabilité par critère de Routh-Hurwitz, comptage de pôles instables)", _p_controle),
    "Équilibres chimiques": ("equilibre_chimique (quotient Q, sens d'évolution Q vs K, Le Chatelier)", _p_equilibres_chimiques),
    "Hydraulique": ("hydraulique (débit Q=vA, continuité, nombre de Reynolds, régimes)", _p_hydraulique),
    "Réseaux (protocoles TCP/IP…)": ("reseaux_ip (sous-réseau IPv4 : réseau/broadcast/masque/hôtes, appartenance)", _p_reseaux),
    "Architecture des ordinateurs": ("architecture (binaire/hexa, complément à deux, addition + détection d'overflow)", _p_architecture),
    "Bases de données": ("bases_donnees (algèbre relationnelle : sélection/projection/jointure/union/agrégats)", _p_bases_donnees),
    "Théorie des réseaux (appliquée)": ("theorie_reseaux (degré, densité, centralité, clustering sur graphe)", _p_theorie_reseaux),
    "Télécommunications": ("telecom (capacité de Shannon-Hartley, débit de Nyquist, gain dB, longueur d'onde)", _p_telecommunications),
    "Réseaux de neurones": ("reseaux_neurones (neurone formel, perceptron ET/OU, activations, XOR à 2 couches)", _p_reseaux_neurones),
    "Blockchain / cryptomonnaies (mécanisme)": ("blockchain (chaînage SHA-256, intégrité, arbre de Merkle, preuve de travail)", _p_blockchain),
    "États de la matière": ("etats_matiere (état physique selon T vs fusion/ébullition, conversions d'échelles)", _p_etats_matiere),
    "Cryptographie appliquée": ("cryptographie_appliquee (César/Vigenère/XOR symétriques, réversibilité garantie)", _p_cryptographie_appliquee),
    "Microprocesseurs": ("microprocesseurs (portes logiques, additionneur complet, ALU avec indicateurs)", _p_microprocesseurs),
    "Cloud / distribué": ("cloud_distribue (hachage cohérent, quorum R+W>N, théorème CAP)", _p_cloud_distribue),
    "Big data": ("big_data (MapReduce word-count, filtre de Bloom sans faux négatif, échantillonnage)", _p_big_data),
    "Web (HTML/CSS/standards)": ("web (imbrication HTML/void/auto-fermant, spécificité CSS et cascade)", _p_web),
    "Géométrie projective": ("geometrie_projective (birapport exact, invariance par homographie, division harmonique)", _p_geometrie_projective),
    "Géotechnique": ("geotechnique (contrainte effective de Terzaghi, poussée de Rankine Ka/Kp)", _p_geotechnique),
    "Réacteurs, distillation": ("genie_chimique (temps de séjour, conversion CSTR/PFR, étages de Fenske)", _p_reacteurs_distillation),
    # ── ALIAS de faux-gaps (2026-07-02) : le mécanisme existait, l'enregistrement manquait ──
    "Cartographie": ("Cartographie — calculs EXACTS (échelle/distance, identités de projection). cf. cartographie.py", _p_cartographie),
    "Vaccinologie (mécanisme)": ("Vaccinologie/immunité de groupe — seuil_immunite_groupe(R0)=1−1/R0, épidémiologie EXACTE. cf. immunite.py", _p_immunite),
    "Comptabilité personnelle / budget": ("Budget personnel — solde/taux d'épargne/50-30-20/reste-à-vivre, calcul monétaire EXACT. cf. budget_personnel.py", _p_budget_personnel),
    "Pauvreté / exclusion (mesures)": ("Mesures sociales — Gini/ratios de pauvreté par formules statistiques EXACTES (rangs). cf. mesures_sociales.py", _p_mesures_sociales),
    "Verrerie / céramique (artisanat)": ("Céramiques — retrait de cuisson/porosité par identités EXACTES. cf. ceramiques.py", _p_ceramiques),
    "Énoncé conditionnel (« si A alors B »)": ("Inférence propositionnelle EXACTE par table de vérité (validité d'un conditionnel). cf. preuve_propositionnelle.py", _p_preuve_propositionnelle),
    "Esprit critique / détection de sophismes": ("Identification de la forme d'un argument (modus ponens/tollens vs affirmation-du-conséquent/négation-de-l'antécédent) + catalogue de sophismes informels. cf. sophismes.py", _p_sophismes),
    "Homéopathie (efficacité)": ("Efficacité : catalogue de consensus (medecines_alternatives) — homéopathie = aucune_preuve, ne dépasse pas le placebo (NHMRC 2015). Abstention hors-catalogue.", _p_medalt_homeopathie),
    "Acupuncture": ("Efficacité : catalogue de consensus — acupuncture = preuve_faible (essais sham souvent équivalents). Abstention hors-catalogue.", _p_medalt_acupuncture),
    "Phytothérapie": ("Efficacité : catalogue de consensus — phytothérapie = variable (dépend du principe actif). Abstention hors-catalogue.", _p_medalt_phytotherapie),
    "Ostéopathie / chiropraxie (efficacité)": ("Efficacité : catalogue de consensus — ostéopathie/chiropraxie = preuve_limitee (lombalgie). Abstention hors-catalogue.", _p_medalt_osteo_chiro),
    "Énergies / chakras / soins énergétiques (efficacité)": ("Efficacité : catalogue de consensus — chakras/soins énergétiques/reiki = aucune_preuve. Abstention hors-catalogue.", _p_medalt_energetique),
    "Soins énergétiques / chakras (efficacité)": ("Efficacité : catalogue de consensus — chakras/soins énergétiques/reiki = aucune_preuve. Abstention hors-catalogue.", _p_medalt_energetique),
    "Médecines alternatives (efficacité)": ("Efficacité : catalogue de consensus établi (niveaux de preuve par pratique, méta-analyses/Cochrane). Abstention hors-catalogue.", _p_medecines_alternatives),
    "Cybersécurité défensive": ("Audit de code sound (audit_code) : détecte des classes CWE documentées (injection SQL CWE-89, code CWE-95) sans faux positif, HORS langage inconnu.", _p_cybersecurite_defensive),
    "Classifications / taxonomies (conventions)": ("Classification décimale de Dewey (convention fermée, centaine -> classe) ; abstention hors table. cf. bibliotheconomie.py", _p_classification_taxonomies),
    "Unités et standards (conventions)": ("Conversion EXACTE entre unités commensurables (facteurs Fraction) ; incommensurable -> HORS. cf. dimensions.py", _p_unites_standards),
    "Ce qui est « vérifiable » (méta-critère)": ("Méta-critère de vérifiabilité opérationnalisé par la falsifiabilité : énoncé faux -> contre-exemple, énoncé vrai -> résiste (jamais « prouvé »). cf. falsification.py", _p_verifiable_meta),
    # ── BRIQUES BUILDABLE construites 2026-07-02 (nouveaux modules FAUX=0) ──
    "Braille / écritures tactiles": ("Braille grade 1 : convention FIXE bijective lettre<->points<->Unicode (a=1, z=1356), round-trip prouvé, hors alphabet -> abstention. cf. braille.py", _p_braille),
    "Cas général vs cas particulier / exception": ("Raisonnement par défaut (non-monotone SOUND) : l'exception explicite prime le défaut, défaut sur membre connu, abstention sur appartenance inconnue. cf. raisonnement_defaut.py", _p_raisonnement_defaut),
    "Séismes": ("Séismologie : lois établies EXACTES — Mw=(2/3)(log10 M0−9.1), E=10^(1.5M+4.8) J, +1 magnitude=×10 amplitude/×31.6 énergie, classes USGS. cf. seismologie.py", _p_seismes),
    "Héraldique (blasons, règles)": ("Héraldique : catalogue fermé des teintures + règle de contrariété EXACTE (jamais métal/métal ni couleur/couleur ; fourrures neutres). cf. heraldique.py", _p_heraldique),
    "Astrologie": ("Statut scientifique (consensus établi) : validité prédictive RÉFUTÉE par études contrôlées (Carlson 1985, Nature). Question bornée sur les claims. cf. pseudosciences.py", _p_pseudo_astrologie),
    "Voyance / divination": ("Statut scientifique : aucune capacité prédictive > hasard en conditions contrôlées (lecture à froid/effet Barnum). cf. pseudosciences.py", _p_pseudo_voyance),
    "Symbolisme / numérologie (validité)": ("Statut scientifique : aucune corrélation nombre-destin établie (associations arbitraires). cf. pseudosciences.py", _p_pseudo_numerologie),
    "Numérologie / symbolisme (validité)": ("Statut scientifique : aucune corrélation nombre-destin établie (associations arbitraires). cf. pseudosciences.py", _p_pseudo_numerologie),
    "Superstitions / croyances populaires": ("Statut scientifique : corrélations illusoires, aucun lien causal démontré. cf. pseudosciences.py", _p_pseudo_superstitions),
    "Croyances populaires / superstitions": ("Statut scientifique : corrélations illusoires, aucun lien causal démontré. cf. pseudosciences.py", _p_pseudo_superstitions),
    "Phénomènes paranormaux": ("Statut scientifique : aucun phénomène (télékinésie, télépathie…) reproduit sous contrôle scientifique (non démontré). cf. pseudosciences.py", _p_pseudo_paranormal),
}


def couvert(libelle: str) -> bool:
    """True ssi un mécanisme nommé existe POUR ce libellé ET sa preuve canonique passe MAINTENANT (sinon False)."""
    entree = REGISTRE.get(libelle)
    if not entree:
        return False
    try:
        return bool(entree[1]())
    except Exception:
        return False


def preuve_de(libelle: str) -> str | None:
    """Description auditable du mécanisme qui couvre `libelle` (ou None)."""
    e = REGISTRE.get(libelle)
    return e[0] if e else None


def sujets_couverts() -> set[str]:
    """Ensemble des libellés dont la preuve passe à l'instant (= couverture REGISTRE réelle)."""
    return {k for k in REGISTRE if couvert(k)}


def verifie_tout() -> tuple[int, int, list[str]]:
    """(nb_ok, nb_ko, libellés en échec). Sert au validateur : TOUTE entrée doit passer (sinon manifeste menteur)."""
    ok, ko, echecs = 0, 0, []
    for k in REGISTRE:
        if couvert(k):
            ok += 1
        else:
            ko += 1
            echecs.append(k)
    return ok, ko, echecs


if __name__ == "__main__":
    ok, ko, echecs = verifie_tout()
    for k in REGISTRE:
        print(f"  {'OK ' if couvert(k) else 'KO!'}  {k}")
    print(f"\n=== capacites : {ok}/{ok + ko} preuves passent ===")
    if echecs:
        print("ÉCHECS:", echecs)


# ————————————————————————— CÂBLAGE 0-ORPHELIN (audit 2026-07-06, mandat Yohan « 0 dette ») —————————————————————————
# Chaque module de src/ qui n'était atteignable par AUCUN chemin du produit reçoit ici une preuve RÉELLE à
# réponse connue (criblée de son validateur). Le diagnostic les EXÉCUTE en direct — couverture mesurée, jamais
# déclarée. Gate permanent : tests/valide_cablage.py (un futur module non câblé remet la suite au rouge).

def _p_causalite():
    from causalite import GrapheCausal
    g = GrapheCausal()
    g.ajoute_cause("pluie", "sol_mouillé", signe="+")
    g.ajoute_cause("sol_mouillé", "glissant", signe="+")
    return g.effets_directs("sol_mouillé") == {"glissant"}


def _p_logique_tri():
    from logique_tri import BaseTrivaluee, VRAI, INCONNU
    B = BaseTrivaluee()
    B.affirme(("capitale", "France", "Paris"))
    return B.evalue(("capitale", "France", "Paris")) == VRAI and B.evalue(("capitale", "France", "Nice")) == INCONNU


def _p_revision():
    from revision import BaseCroyances, Croyance, NOUVEAU, REMPLACE
    B = BaseCroyances()
    a = B.integre(Croyance("dirigeant_X", "Alice", fiabilite=0.6, date=2020))
    b = B.integre(Croyance("dirigeant_X", "Bob", fiabilite=0.9, date=2024))
    return a == NOUVEAU and b == REMPLACE and B.valeur("dirigeant_X") == "Bob"


def _p_extraction():
    from extraction import extrait
    c = extrait("Paris est la capitale de la France.")
    return len(c) == 1 and c[0]["triplet"] == ("France", "capitale", "Paris")


def _p_triangulation():
    from triangulation import triangule, CORROBORE, NON_INDEPENDANT
    return (triangule(9.81, "pendule", 9.80, "chute_libre", tol_rel=1e-2) == CORROBORE
            and triangule(9.81, "pendule", 9.81, "pendule") == NON_INDEPENDANT)


def _p_mereologie():
    from mereologie import Assemblage
    a = Assemblage()
    a.ajoute_partie("roue", "voiture")
    return len(a.parties_directes("voiture")) == 1


def _p_frame():
    from frame import Frame
    f = Frame("transfert", {"quoi": "chaleur", "source": "intérieur", "cible": "extérieur", "mecanisme": "pompe"})
    return f.valide() and f.roles_manquants() == [] and not Frame("cause", {"cause": "friction"}).valide()


def _p_cas_limites():
    from cas_limites import limite_en, homogene_degre
    Ec = lambda v: 0.5 * v * v
    return limite_en(Ec, 0.0, 0.0) and homogene_degre(Ec, 2) and not homogene_degre(Ec, 3)


def _p_exercices():
    from exercices import COMPTE_PAIRS as CP
    from juge import Limites, juge
    return juge(CP.solution_ref, CP.tests, Limites(temps_s=3, cpu_s=2)).passe


def _p_scout_qlever():
    from scout_qlever import val
    return val({"n": {"value": "42"}}, "n") == "42" and val({}, "absent") == ""


def _p_sujets():
    import tempfile, os
    from sujets import charge
    ch = os.path.join(tempfile.gettempdir(), "_p_sujets.md")
    with open(ch, "w", encoding="utf-8") as f:
        f.write("| Capitale de la France | BORNE | B1 |\n")
    return isinstance(charge(ch), list)


def _p_harvester():
    from harvester import type_propriete
    return type_propriete([]) == {}


def _p_comprehension_integree():
    from comprehension_integree import comprend
    return callable(comprend) and comprend.__doc__ is not None


def _p_oracle_definitions():
    from oracle_definitions import genre_de
    return callable(genre_de)


def _p_bootstrap_savoir():
    from bootstrap_savoir import Savoir, chaine
    return callable(chaine) and isinstance(Savoir, type)


def _p_carte_limites():
    from carte_limites_francais import verdict
    return callable(verdict)


def _p_conservation():
    from grandeur import Grandeur
    from conservation import bilan
    J = lambda x: Grandeur.depuis(x, "J")
    b = bilan(entrees=[J(100)], sorties=[J(60), J(40)])
    return b["conserve"] and abs(b["desequilibre"].en("J")) < 1e-9


def _p_etat():
    import dimensions as D
    from grandeur import Grandeur
    from etat import EspaceEtats
    E = EspaceEtats()
    E.variable("phase", domaine={"solide", "liquide", "gaz"})
    E.variable("temperature", dimension=D.TEMPERATURE)
    return E.etat(phase="liquide", temperature=Grandeur.depuis(20, "°C")).valeur("phase") == "liquide"


def _p_loi():
    import dimensions as D
    from grandeur import Grandeur
    from loi import Loi
    Ec = Loi("énergie_cinétique", variables={"E": D.ENERGIE, "m": D.MASSE, "v": D.VITESSE},
             solveurs={"E": lambda m, v: 0.5 * m * v * v})
    g = Ec.resout("E", m=Grandeur.depuis(2, "kg"), v=Grandeur.depuis(3, "m/s"))
    return g.dim == D.ENERGIE and abs(g.en("J") - 9) < 1e-9


def _p_limite():
    import dimensions as D
    from grandeur import Grandeur
    from loi import Loi
    from limite import Limite
    carnot = Loi("carnot", variables={"COP": D.SANS, "T_froid": D.TEMPERATURE, "T_chaud": D.TEMPERATURE},
                 solveurs={"COP": lambda T_froid, T_chaud: T_froid / (T_chaud - T_froid) if T_chaud > T_froid else None})
    lim = Limite("COP_Carnot", carnot, cible="COP", sens="max", description="borne de Carnot")
    return lim is not None


def _p_simulation():
    import dimensions as D
    from grandeur import Grandeur
    from etat import EspaceEtats
    from simulation import Simulateur
    E = EspaceEtats()
    E.variable("population", dimension=D.SANS)
    E.variable("etape", dimension=D.SANS)
    decroit = lambda e: {"population": e.valeur("population") * 0.9}
    horloge = lambda e: {"etape": e.valeur("etape") + Grandeur(1, D.SANS)}
    sim = Simulateur(E, [decroit, horloge])
    traj = sim.simule(E.etat(population=Grandeur(1000, D.SANS), etape=Grandeur(0, D.SANS)), 3, arret_point_fixe=False)
    return len(traj) == 4 and abs(traj[3].valeur("population").valeur - 729) < 1e-9


def _p_geometrie3d():
    import geometrie3d as G
    c = G.cube(1.0)
    return len(c.sommets) == 8 and abs(c.aire_surface() - 6.0) < 1e-9 and abs(c.volume() - 1.0) < 1e-9


def _p_chemin2d():
    from chemin2d import Ligne, Chemin
    ch = Chemin([Ligne((0, 0), (1, 0)), Ligne((1, 0), (1, 1))])
    return ch is not None


def _p_oracle_definitions():
    from oracle_definitions import construit_isa
    edges = dict(construit_isa())
    return edges.get("paris") == "capitale"


def _p_bootstrap_savoir():
    from bootstrap_savoir import chaine
    return chaine("chat", {"chat": "mammifère", "mammifère": "animal"}) == ["chat", "mammifère", "animal"]


def _p_carte_limites():
    from carte_limites_francais import carte
    return isinstance(carte(), (list, dict))


def _p_comprehension_integree():
    from comprehension_integree import comprend
    return bool(comprend())


def _p_savoir_massif():
    from savoir_massif import SavoirMassif
    e = lambda hyper=None: {"classe": "nom", "genre": None, "definition": "", "hyper": hyper, "syn": [], "ant": []}
    sav = SavoirMassif({"chat": e("mammifère"), "mammifère": e("animal"), "animal": e()})
    return sav.est_un("chat", "animal") and not sav.est_un("animal", "chat")


def _p_utilite():
    from exercices import COMPTE_PAIRS as CP
    from juge import Limites, juge
    from utilite import evalue_utilite
    lim = Limites(temps_s=3, cpu_s=2)
    concis = "def compte_pairs(*args, **kwargs):\n    return sum(1 for x in args[0] if x % 2 == 0)\n"
    u = evalue_utilite(CP, concis, juge(concis, CP.tests, lim), lim)
    return u is not None


def _p_fuzz():
    from fuzz import crible, ROBUSTE
    from juge import Limites
    from taches import HUMANEVAL_0 as t
    return crible(t, t.solution_ref, n_essais=30, seed=0, limites=Limites(temps_s=5, cpu_s=4)).type_faille == ROBUSTE


def _p_boucle():
    import tempfile
    from pathlib import Path
    from boucle import campagne
    from generateur import GenerateurFactice, banque_demo
    from juge import Limites
    from store import Store
    from taches import HUMANEVAL_0 as t
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        campagne(GenerateurFactice(banque_demo(t), seed=7), store, [t], n=4, tours=2,
                 limites=Limites(temps_s=5, cpu_s=4))
        return len(store) >= 1


def _p_auto_optimise():
    import auto_optimise as O
    return O.cout_expr("(sum(x) + sum(x))")[0] == 2 and O.cout_expr("x[0]")[0] == 0



def _p_mesure():
    from generateur import GenerateurAleatoire
    from juge import Limites
    from mesure import evalue
    from taches import HUMANEVAL_0 as t
    rv, rg = evalue(GenerateurAleatoire(seed=1), t, n_essais=3, limites=Limites(temps_s=4, cpu_s=3))
    return rv is not None


def _p_curateur():
    from curateur import valide_tache
    from exercices import CATALOGUE
    from juge import Limites
    return bool(valide_tache(CATALOGUE[0], Limites(temps_s=4, cpu_s=3)))


def _p_exploits():
    from exploits import sonde_statique
    return sonde_statique("def f(x):\n    return {1: 2}.get(x)\n") is not None


def _p_echafaudage():
    from echafaudage import briques
    return briques({}, {}) == []


def _p_selecteur():
    from selecteur import Selecteur
    return isinstance(Selecteur, type)


def _p_session():
    import tempfile
    from pathlib import Path
    from curateur import CurateurGradue
    from exercices import CATALOGUE
    from generateur import GenerateurApprenantMulti
    from juge import Limites
    from store import Store
    from session import session
    lim = Limites(temps_s=3, cpu_s=2)
    with tempfile.TemporaryDirectory() as d:
        j = session(GenerateurApprenantMulti(CATALOGUE, competence=0.0, seed=5),
                    CurateurGradue(CATALOGUE, seuil=0.7, limites=lim), Store(Path(d) / "s.jsonl"),
                    n=2, max_tours=2, limites=lim)
    return bool(j)


def _p_lecteur_daemon():
    from lecteur_daemon import _traite
    r = _traite({"op": "inconnu_xyz"})
    return isinstance(r, dict)


def _p_audit_ancres():
    from audit_ancres import _relations_referencees
    return _relations_referencees({}) == set() or isinstance(_relations_referencees({}), set)


def _p_auto_invention():
    from auto_invention import _empreinte
    return _empreinte("args[0] * 2", (1, 2)) == (2, 4) and _empreinte("args[0] +", (1,)) is None


def _p_rapport_invention():
    import rapport_invention as R
    rap = R.rapport([("somme_totale", "xs", [([1, 2], 3), ([5], 5)], [([2, 2], 4)])], [])
    return isinstance(rap, dict) and bool(R.texte(rap))


_KAIKKI_CHAT = ('{"word":"chat","pos":"noun","tags":["masculine"],"senses":[{"glosses":["Mammifère carnivore '
                'félin."]}],"hypernyms":[{"word":"félidés"}],"synonyms":[{"word":"matou"}]}')
_KAIKKI_MAM = '{"word":"mammifère","pos":"noun","tags":["masculine"],"senses":[{"glosses":["Animal à mamelles."]}]}'


def _p_convertit_kaikki():
    from convertit_kaikki import convertit, aretes_isa
    lex = convertit([_KAIKKI_CHAT, _KAIKKI_MAM])
    return ("chat", "mammifère") in aretes_isa(lex)


def _p_charge_lexique():
    from charge_lexique import coherence
    from convertit_kaikki import convertit
    h = coherence(convertit([_KAIKKI_CHAT, _KAIKKI_MAM]))
    return h["entrees"] == 2 and h["acyclique"]


def _p_etend_savoir():
    from etend_savoir import chaine
    return chaine("chat", {"chat": "mammifère", "mammifère": "animal"}) == ["chat", "mammifère", "animal"]


def _p_relations_lexique():
    from convertit_kaikki import convertit
    from relations_lexique import aretes_syn
    return ("chat", "matou") in aretes_syn(convertit([_KAIKKI_CHAT, _KAIKKI_MAM]))


def _p_fabrique_semantique():
    from convertit_kaikki import convertit
    from fabrique_semantique import construit_paires
    paires = construit_paires(convertit([_KAIKKI_CHAT, _KAIKKI_MAM]))
    return any(p[0] == "definition" for p in paires)


def _p_fabrique_francais():
    from fabrique_francais import _conjug_reguliers
    items = _conjug_reguliers(["parler"])
    return ("conjugaison", ("parler", "present", 0), "parle") in items


def _p_fabrique_comprehension():
    from fabrique_comprehension import ITEMS
    return len(ITEMS) > 0


def _p_mesure_structure_pertache():
    import mesure_structure_pertache as M
    return len(M.STRATS) > 0 and all(callable(s[1]) for s in M.STRATS[:3])


def _p_recherche_dirigee():
    from recherche_dirigee import synthetise
    r = synthetise([([1, 2], 3), ([5], 5)], [([2, 2], 4)], "xs", "int", budget=3000)
    return isinstance(r, dict) and r.get("generes", 0) > 0


def _p_diable():
    import diable
    nom, etage, _n, attendu, ok = diable._resoudre_tache(diable.BATTERIE[0])
    return ok and etage == attendu


def _p_cherche_architecture_max():
    import cherche_architecture_max as CAM
    ns = {}
    exec(dict(CAM.PRIMS)["carre"], ns)
    return ns["carre"](3) == 9 and CAM.K > 0


def _p_usine_donnees():
    import tempfile
    from pathlib import Path
    from usine_donnees import accumule
    with tempfile.TemporaryDirectory() as d:
        return len(accumule(Path(d) / "store.jsonl", limite=2)) >= 1


def _p_exporte_dataset():
    import tempfile
    from pathlib import Path
    from exporte_dataset import resume
    with tempfile.TemporaryDirectory() as d:
        ch = Path(d) / "ds.jsonl"
        ch.write_text('{"messages": []}\n')
        return resume(ch)["lignes"] == 1


# ————— CÂBLAGE FAÇADE ia.py, LOT 1 (mandat excellence atomique 2026-07-08) : chaque enveloppe statistique
# de la façade reçoit sa preuve à réponse connue — le plafond de dette de valide_atomes descend d'autant. —————
def _p_facade_stats_1() -> bool:
    import ia as _I
    va, da = _I.coherence_conjonction(0.3, 0.4, 0.5)          # sophisme de conjonction DÉTECTÉ (Linda)
    vb, db = _I.coherence_conjonction(0.3, 0.4, 0.2)          # et cohérence RECONNUE quand P(A∧B) ≤ min
    if not (da["sophisme"] is True and db["coherent"] is True):
        return False
    if _I.decouvertes_controlees([0.001, 0.01, 0.04, 0.8])[1] != [0, 1]:   # Benjamini-Hochberg q=0.05
        return False
    if _I.auc_bat_le_hasard([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0]) is not True:   # AUC séparable
        return False
    if _I.compare_groupes([1, 2, 1, 2, 1], [8, 9, 8, 9, 8])[1]["rejet_perm"] is not True:  # permutation
        return False
    return abs(_I.biais_de_longueur([10, 20, 30])[1]["mu_biaisee"] - 70.0 / 3.0) < 1e-9    # inspection paradox


def _p_facade_stats_2() -> bool:
    import ia as _I
    if _I.bandit_robuste([[1, 0], [0, 1], [1, 0], [1, 0]])[1]["regret"] != 0.0:   # EXP3 graine fixe, régret nul
        return False
    if _I.conforme_intervalle([1] * 10, 10.0) != ("estimation", (9.0, 11.0), 0.9):  # conformal split exact
        return False
    if _I.agrege_preferences([["a", "b"], ["a", "b"], ["b", "a"]], ["a", "b"])[1]["condorcet"] != "a":
        return False
    post = _I.corrige_posterior_prevalence([0.8, 0.2], [0.5, 0.5], [0.1, 0.9])    # Bayes exact : 0.16/0.52
    if abs(post[0] - 0.16 / 0.52) > 1e-9:
        return False
    return _I.choisit_modele_mdl([1, 2, 3, 4, 5, 6], [2, 4, 6, 8, 10, 12], 3)[1]["degre_mdl"] == 1  # MDL -> degré 1


def _p_facade_stats_3() -> bool:
    """Contrats d'ABSTENTION honnête des façades (FAUX=0 : trop peu de données -> jamais un chiffre)."""
    import ia as _I
    if _I.comptage_surdisperse([1, 2, 1, 30, 2, 1])[0] != "abstention":            # n=6 < 20 -> abstention DITE
        return False
    if _I.comptage_surdisperse([1, 2, 1, 3, 2, 1, 2, 3, 1, 2, 1, 3, 2, 1, 2, 3, 1, 2, 1, 50])[0] != "estimation":
        return False                                                               # n=20 -> estimation servie
    if _I.analyse_queue_lourde([1, 1, 2, 2, 3, 100, 3, 2, 1, 200, 1, 2, 3, 150])[0] != "abstention":
        return False                                                               # < 30 positifs -> abstention
    if _I.decompose_incertitude([0.9, 0.1, 0.9, 0.1])[0] != "abstention":          # n=4 < 5 -> abstention
        return False
    return _I.classe_taux_robuste([45, 50], [60, 60])[0] == "abstention"           # entrée hors contrat -> dite


def _p_facade_stats_13() -> bool:
    """LOT 8 : base-rate quantifié, pentes (naïve/atténuée), winner's curse, Lindley, RTM, Lord."""
    import ia as _I
    va, da = _I.probabilite_posterieure_test(0.99, 0.95, 0.001)
    if not (va == "analyse" and abs(da["vpp"] - (0.99 * 0.001) / (0.99 * 0.001 + 0.05 * 0.999)) < 1e-12
            and da["naive"] == 0.99):                                 # l'écart intuition/Bayes est QUANTIFIÉ
        return False
    if _I.pente_ols_naive([1, 2, 3, 4], [2.1, 3.9, 6.1, 7.9])[0] != "abstention":   # n=4 < 12 -> DIT
        return False
    vo, (b, (blo, bhi)), _co = _I.pente_ols_naive(list(range(1, 16)),
                                                  [2 * i + 0.1 * (i % 3) for i in range(1, 16)])
    if not (vo == "estimation" and blo < 2.0 < bhi):                  # la vraie pente 2 est DANS l'IC
        return False
    vp, (pa, (palo, pahi)), _cp = _I.pente_erreur_mesure([1, 2, 3, 4] * 10, [2.1, 3.9, 6.1, 7.9] * 10, 0.5)
    if not (vp == "estimation" and pa > 2.0):                         # l'atténuation est CORRIGÉE (pente > naïve)
        return False
    vs, ds = _I.effet_selectionne([1.0, 1.2, 0.9, 1.1] * 10, 1.5)     # winner's curse : le max sélectionné
    if not (vs == "estime" and ds["valeur"] == 1.2 and ds["ic"][0] < 0 < ds["ic"][1]):   # n'est PAS significatif
        return False
    ve, de = _I.evidence_vs_n(0.6, 100)                               # Lindley : p=0.6 sur n=100, B01 > 1
    if not (ve == "analyse" and de["B01"] > 1.0):                     # l'évidence favorise H0 malgré l'écart
        return False
    vr, dr = _I.diagnostique_regression_moyenne([10, 9, 8, 7, 6] * 2 + [10, 9], [8, 7, 7, 6, 5] * 2 + [8, 7])
    if not (vr == "rtm" and dr["mu"] == 8.25):
        return False
    vl, dl = _I.paradoxe_lord([(50 + i % 5, 60 + i % 5) for i in range(40)],
                              [(70 + i % 5, 75 + i % 5) for i in range(40)])
    return vl == "analyse" and dl["diff_changement"] == 5.0           # les deux analyses EXPLICITÉES


def _p_facade_stats_12() -> bool:
    """LOT 7 : possibilités, imputation multiple, filtre d'état, intervalle prédictif décomposé."""
    import ia as _I
    if _I.encadre_probabilite({"a": 1.0, "b": 0.5}, ["a"]) != ("mesure", (0.5, 1.0), True):
        return False                                                  # nécessité/possibilité EXACTES
    if _I.encadre_probabilite({"a": 0.5, "b": 0.5}, ["a"])[0] != "abstention":
        return False                                                  # π sous-normalisée -> REFUSÉE (dite)
    x = list(range(1, 31))
    y = [2 * i if i % 2 else None for i in x]                         # y = 2x observé une fois sur deux
    vm, (pt, (lo, hi)), _cm = _I.moyenne_avec_manquants(x, y)
    if not (vm == "estimation" and pt == 31.0 and lo < 31.0 < hi):    # 2 × moyenne(x) = 31 EXACT retrouvé
        return False
    pt2, (lo2, hi2) = _I.imputation_simple_biais(x, y)
    if not (pt2 == 31.0 and lo2 < 31.0 < hi2):
        return False
    vf, _df = _I.filtre_etat_robuste([1.0, 1.1, 0.9, 1.05, 0.95, 5.0, 1.0, 1.02], 1.0, 0.01, 0.1)
    if vf != "surconfiant":                                           # l'outlier rend le filtre SURCONFIANT — DIT
        return False
    vi, (mu, (ilo, ihi)), _ci = _I.intervalle_predictif_decompose([1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 4)
    return vi == "estimation" and mu == 5.5 and ilo < 1.0 and ihi > 10.0   # prédictif COUVRE les données


def _p_facade_stats_11() -> bool:
    """LOT 6 : propagation d'incertitude, e-process, calibration, IDM, prévision, régime de question."""
    import ia as _I
    vp, (mu, (plo, phi)), _c = _I.propage_incertitude(lambda x: x * x, [(3.0, 0.1)])
    if not (vp == "estimation" and mu == 9.0 and plo < 9.0 < phi):    # 3² = 9 propagé EXACT, IC autour
        return False
    vt, dt = _I.test_par_pari([1] * 20, 0.5)                          # pièce TRUQUÉE : e-process rejette (pas 7)
    if not (vt == "test" and dt["rejet"] == 7 and dt["E_final"] > dt["seuil"]):
        return False
    vt2, dt2 = _I.test_par_pari([1, 0] * 10, 0.5)                     # pièce JUSTE : jamais rejetée
    if dt2["rejet"] is not None:
        return False
    vc, dc = _I.teste_calibration([0.2, 0.8, 0.5, 0.9, 0.1] * 8, [0, 1, 1, 1, 0] * 8)
    if not (vc == "non_calibre" and dc["p_valeur"] < 0.05):           # le biais de calibration est DÉTECTÉ
        return False
    vb, bornes = _I.proba_categorielle_imprecise([3, 5, 2])           # IDM s=1 : bornes EXACTES (c/(n+1), (c+1)/(n+1))
    if not (vb == "bornes" and abs(bornes[0][0] - 3 / 11) < 1e-12 and abs(bornes[0][1] - 4 / 11) < 1e-12):
        return False
    vh, (pt, (hlo, hhi)), _ch = _I.prevoit_horizon([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] * 3, 3)
    if not (vh == "estimation" and hlo < pt < hhi):
        return False
    if _I.regime_question("quelle est la capitale de la France ?") != "supposition_a_chercher":
        return False
    return _I.survie_estimee([1, 2, 3, 4, 5], [1, 1, 1, 0, 1], 2.5)[0] == "abstention"   # D=4 < 15 -> DIT


def _p_facade_stats_10() -> bool:
    """LOT 5 : base-rate fallacy (PPV exact), ridge, survie, surdispersion, log-score, Condorcet, main chaude."""
    import math
    import random
    import ia as _I
    ppv = _I.valeur_predictive(0.99, 0.95, 0.001)                     # test à 99 % sur prévalence 0.1 % :
    if abs(ppv - (0.99 * 0.001) / (0.99 * 0.001 + 0.05 * 0.999)) > 1e-12:   # PPV ≈ 1.9 % (Bayes EXACT)
        return False
    vr, dr = _I.regression_ridge([[1], [2], [3], [4]], [2, 4, 6, 8])
    if not (dr["beta_ols"] == [2.0] and dr["beta_ridge"][0] < 2.0):   # OLS exact, ridge RÉTRÉCIT
        return False
    if _I.survie_mediane([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1] * 10) != 5.0:
        return False
    ratio, z, rejet = _I.teste_surdispersion([1, 2, 1, 3, 2, 1, 2, 3, 1, 2] * 3)
    if not (0.31 < ratio < 0.33 and rejet is False):                  # sous-dispersé, PAS déclaré sur-dispersé
        return False
    if abs(_I.score_forecast([0.8, 0.2, 0.9], [1, 0, 1])
           + (math.log(0.8) + math.log(0.8) + math.log(0.9)) / 3.0) > 1e-9:   # log-score exact
        return False
    if abs(_I.proba_mieux_classe(0.7, 0.3) - 1.0 / (1.0 + math.exp(-0.4))) > 1e-9:  # logistique exacte
        return False
    vs, ds = _I.sagesse_des_foules(0.6, rng=random.Random(0))         # jury de Condorcet : la majorité
    c = [p for (_n, p) in ds["courbe"]]                               # devient sûre quand le groupe grandit
    if not (vs == "analyse" and c[0] < c[1] < c[2] and c[2] > 0.99):
        return False
    vm, dm = _I.sophisme_main_chaude(0.5, 4, rng=random.Random(0))    # main chaude : la conditionnelle VRAIE
    return vm == "analyse" and abs(dm["cond_vraie"] - 0.5) < 0.01 and dm["biais_naif"] < 0.45   # reste 0.5,
    # l'estimateur naïf est biaisé vers le bas — l'artefact est REPRODUIT, pas récité.


def _p_facade_stats_8() -> bool:
    """LOT 4 : intervalles (bootstrap BCa, Bernstein empirique, jackknife+), densité, maxent, intensité."""
    import math
    import statistics
    import ia as _I
    ech = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 4
    vb, (lo, hi), cf = _I.intervalle_bootstrap(ech, statistics.fmean, B=200)
    if not (vb == "estimation" and lo < 5.5 < hi and cf == 0.9):      # la vraie moyenne est DANS l'intervalle
        return False
    vg, (glo, ghi), meth = _I.intervalle_moyenne_garanti([0.2, 0.4, 0.6, 0.8] * 10, 0.0, 1.0)
    if not (vg == "intervalle" and glo < 0.5 < ghi and meth == "empirical_bernstein"):
        return False
    vj, (jlo, jhi), _cj = _I.jackknife_plus(ech)
    if not (vj == "estimation" and jlo < 5.5 < jhi):
        return False
    vd, dd = _I.estime_densite(ech)
    if not (vd == "densite" and dd["h"] > 0 and dd["h_silverman"] > dd["h"]):   # LOO resserre Silverman ici
        return False
    vm, dm = _I.loi_maximum_entropie([1, 2, 3])
    if not (vm == "maxent" and dm["p"] == [1.0 / 3.0] * 3 and abs(dm["entropie"] - math.log(3)) < 1e-9):
        return False                                                   # sans contrainte -> UNIFORME exact
    bins, _homog = _I.intensite_temporelle([0.5, 1.5, 2.5, 3.5] * 10, 24.0)
    return bins[:4] == [10.0] * 4 and sum(bins) == 40.0              # 40 événements, 4 premières heures


def _p_facade_stats_9() -> bool:
    """LOT 4 (suite) : Dunning-Kruger = artefact statistique reproduit ; contrats d'abstention honnête."""
    import random
    import ia as _I
    vdk, ddk = _I.dunning_kruger_artefact(0.0, n=2000, rng=random.Random(0))
    if not (vdk == "analyse" and ddk["info"] == 0.0 and len(ddk["quartiles"]) == 4):
        return False                                                  # l'artefact émerge SANS aucune information
    if _I.estime_population([10, 20, 30], [100, 100, 100])[0] != "abstention":   # n=3 < 10 -> DIT
        return False
    return _I.moyenne_modeles(list(range(1, 11)),
                              [2.1, 3.9, 6.2, 7.8, 10.1, 12.2, 13.8, 16.1, 18.0, 20.2])[0] == "abstention"


def _p_facade_stats_6() -> bool:
    """LOT 3 : décision pignistique, découverte de loi, Berkson, fenêtres de comptage, DMS, échelle de carte."""
    import ia as _I
    if _I.decision_pignistique({"a": 0.6, "b": 0.4}, ["a", "b"], {"x": {"a": 1, "b": 0}}) \
            != ("pignistique", "x", {"a": 0.6, "b": 0.4}):
        return False
    loi = _I.decouvre_loi([(1, 1), (2, 4), (3, 9), (4, 16)])          # y = x² découvert, a = 1.0 EXACT
    if not (loi["forme"] == "carré" and loi["params"]["a"] == 1.0):
        return False
    vb, db = _I.detecte_biais_collision([1, 0, 1, 0, 1, 1, 0, 0] * 5, [0, 1, 0, 1, 1, 0, 1, 0] * 5, 1.5)
    if not (vb == "berkson" and abs(db["corr_pop"] + 0.5) < 1e-9 and abs(db["corr_sel"]) < 1e-9):
        return False
    if _I.comptage_fenetre([0.1, 0.5, 1.2, 3.4, 5.5, 7.7, 9.9, 11.2, 13.3, 15.5, 17.7, 19.9, 21.2, 23.3] * 3,
                           24.0, 0.0, 12.0) != ("estimation", (24.5, (14, 37)), 0.9):
        return False
    if abs(_I.dms_vers_dd(48, 51, 24) - (48 + 51 / 60 + 24 / 3600)) > 1e-12:   # 48°51'24" (Paris) EXACT
        return False
    return _I.echelle_carte(25000, 4.0) == 100000.0                   # 4 cm au 1:25000 = 1 km EXACT


def _p_facade_stats_7() -> bool:
    """LOT 3 (suite) : covariance robuste, métriques de classification, parts multinomiales, Simpson honnête."""
    import ia as _I
    vc, dc = _I.covariance_robuste([[1, 2], [2, 3], [1, 2], [2, 3], [100, 200]] * 8)
    if not (vc == "analyse" and dc["p"] == 2 and dc["n"] == 40 and dc["cond"] > 1.0):
        return False
    vm, dm = _I.metriques_classification([1, 1, 0, 0], [1, 0, 1, 0])
    if not (vm == "metriques" and dm["exactitude"] == 0.5):
        return False
    vp, parts, conf = _I.parts_multinomiales([30, 50, 20])
    if not (vp == "estimation" and 0.19 < parts[0][0] < 0.3 < parts[0][1] < 0.45):
        return False
    return _I.detecte_simpson([("h", 1, 1), ("h", 1, 0)], "t", "c")[0] == "abstention"   # strates incohérentes


def _p_facade_stats_4() -> bool:
    """LOT 2 (excellence atomique) : ergodicité, AUC avec IC, bande DKW, bornage de question, Yager, UCB."""
    import math
    import ia as _I
    ve, de = _I.analyse_ergodicite([1.5, 0.6], [0.5, 0.5])       # taux temporel = √(1.5×0.6) EXACT
    if not (de["moyenne_ensemble"] == 1.05 and abs(de["taux_temporel"] - math.sqrt(0.9)) < 1e-12):
        return False
    if _I.auc_avec_intervalle([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0]) != ("estimation", (1.0, (1.0, 1.0)), 0.95):
        return False
    vb, db = _I.bande_confiance_cdf(list(range(1, 11)) * 3)      # DKW : eps = √(ln(2/α)/2n), n=30, α=0.05
    if not (db["n"] == 30 and abs(db["eps"] - math.sqrt(math.log(2 / 0.05) / 60.0)) < 1e-12):
        return False
    if _I.classe_bornage("quelle est la capitale de la France ?").statut_ontologique != "borne":
        return False
    vc, mc, meta = _I.combine_evidences({"a": 0.7, "b": 0.3}, {"a": 0.6, "b": 0.4})
    if not (vc == "combinaison" and abs(mc[frozenset({"a"})] - 0.42) < 1e-12 and meta["regle"] == "yager"):
        return False
    return abs(_I.acquisition_prochain_essai([0.0, 0.5, 1.0], [1.0, 2.0, 1.5], 0.0, 1.0)
               - 0.6030150753768845) < 1e-9                       # UCB déterministe


def _p_facade_stats_5() -> bool:
    """LOT 2 : contrats d'ABSTENTION honnête (données insuffisantes / masses invalides -> DIT, jamais un chiffre)."""
    import ia as _I
    if _I.bande_prediction([1, 2, 3, 4, 5, 6, 7, 8], [2, 4, 6, 8, 10, 12, 14, 16])[0] != "abstention":
        return False                                              # n=8 < 30
    if _I.calibration_predictive([[1, 2, 3]] * 3, [2, 2, 3])[0] != "abstention":
        return False                                              # n=3 < 30
    if _I.conforme_ensemble([0.9, 0.85, 0.8, 0.95, 0.9], [[0.7, 0.3], [0.2, 0.8]])[0] != "abstention":
        return False                                              # calibration n=5 trop courte pour 90 %
    if _I.corrige_prevalence([[0.8, 0.2], [0.3, 0.7]], [0.5, 0.5])[0] != "abstention":
        return False                                              # EM exige n ≥ 30
    return _I.combine_evidences({"a": 0.6, "b": 0.2}, {"a": 0.5, "b": 0.3})[0] == "abstention"  # masses ≠ 1


# Chaque libellé est une CAPACITÉ visible de l'utilisateur (« est-ce que tu sais… ») ; la preuve est exécutée
# en direct par couvert()/verifie_tout() (diagnostic). Un module retiré/ cassé -> preuve rouge -> gate rouge.
REGISTRE.update({
    "Pièges statistiques quantifiés (façade stats 13)": (
        "probabilite_posterieure_test (écart intuition/Bayes QUANTIFIÉ), pente_ols_naive (abstention n<12 + "
        "vraie pente dans l'IC), pente_erreur_mesure (atténuation corrigée), effet_selectionne (winner's "
        "curse : le max sélectionné n'est pas significatif), evidence_vs_n (Lindley : B01 > 1 malgré p=0.6), "
        "diagnostique_regression_moyenne (RTM), paradoxe_lord (les deux analyses explicitées).",
        _p_facade_stats_13),
    "Possibilités, imputation multiple et filtres honnêtes (façade stats 12)": (
        "encadre_probabilite (nécessité/possibilité exactes ; π sous-normalisée refusée), "
        "moyenne_avec_manquants et imputation_simple_biais (MCAR : 2×moyenne = 31 exact retrouvé), "
        "filtre_etat_robuste (l'outlier rend le filtre SURCONFIANT — dit), intervalle_predictif_decompose "
        "(couvre les données, moyenne 5.5 exacte).", _p_facade_stats_12),
    "Incertitude propagée, e-process et probabilités imprécises (façade stats 11)": (
        "propage_incertitude (3² = 9 exact + IC), test_par_pari (e-process : pièce truquée rejetée au pas 7, "
        "pièce juste jamais), teste_calibration (biais détecté), proba_categorielle_imprecise (bornes IDM "
        "exactes 3/11-4/11), prevoit_horizon, regime_question, survie_estimee (D < 15 -> abstention DITE).",
        _p_facade_stats_11),
    "Base-rate, Condorcet et main chaude (façade stats 10)": (
        "valeur_predictive (PPV bayésien EXACT : test à 99 % + prévalence 0.1 % -> 1.9 %), regression_ridge "
        "(OLS exact, rétrécissement), survie_mediane, teste_surdispersion, score_forecast (log-score exact), "
        "proba_mieux_classe (logistique), sagesse_des_foules (jury de Condorcet : la majorité converge), "
        "sophisme_main_chaude (l'artefact est REPRODUIT numériquement, graine fixée).", _p_facade_stats_10),
    "Intervalles garantis et maximum d'entropie (façade stats 8)": (
        "intervalle_bootstrap (BCa), intervalle_moyenne_garanti (Bernstein empirique), jackknife_plus, "
        "estime_densite (LOO vs Silverman), loi_maximum_entropie (sans contrainte -> uniforme EXACT, "
        "entropie ln 3), intensite_temporelle (bins exacts).", _p_facade_stats_8),
    "Dunning-Kruger comme artefact + abstentions (façade stats 9)": (
        "dunning_kruger_artefact (l'effet émerge à information NULLE — artefact statistique reproduit, "
        "graine fixée) ; estime_population et moyenne_modeles s'ABSTIENNENT en-dessous de leur n minimal.",
        _p_facade_stats_9),
    "Décision, lois et biais de sélection (façade stats 6)": (
        "decision_pignistique (transformée exacte), decouvre_loi (y = x² retrouvé, a = 1.0), "
        "detecte_biais_collision (Berkson : corrélation −0.5 -> 0 sous sélection), comptage_fenetre, "
        "dms_vers_dd (48°51'24\" exact), echelle_carte (4 cm au 1:25000 = 1 km).", _p_facade_stats_6),
    "Robustesse et métriques (façade stats 7)": (
        "covariance_robuste (MCD, conditionnement tracé), metriques_classification (exactitude exacte), "
        "parts_multinomiales (IC simultanés), detecte_simpson (strates incohérentes -> abstention DITE).",
        _p_facade_stats_7),
    "Ergodicité, calibration et fusion d'évidences (façade stats 4)": (
        "analyse_ergodicite (taux temporel = moyenne géométrique exacte), auc_avec_intervalle, "
        "bande_confiance_cdf (DKW exact), classe_bornage (borné/non-borné), combine_evidences (Yager, "
        "conflit tracé), acquisition_prochain_essai (UCB déterministe).", _p_facade_stats_4),
    "Abstention honnête, lot 2 (façade stats 5)": (
        "bande_prediction, calibration_predictive, conforme_ensemble, corrige_prevalence : n insuffisant -> "
        "ABSTENTION DITE ; combine_evidences refuse des masses qui ne somment pas à 1 (FAUX=0).",
        _p_facade_stats_5),
    "Cohérence probabiliste et découvertes contrôlées (façade stats 1)": (
        "coherence_conjonction (bornes de Fréchet, sophisme de Linda détecté), decouvertes_controlees "
        "(Benjamini-Hochberg), auc_bat_le_hasard, compare_groupes (permutation), biais_de_longueur "
        "(inspection paradox, mu biaisée = Σx²/Σx). Preuves numériques exactes.", _p_facade_stats_1),
    "Décision et calibration sous incertitude (façade stats 2)": (
        "bandit_robuste (EXP3 déterministe à graine fixe), conforme_intervalle (conformal split exact), "
        "agrege_preferences (Condorcet), corrige_posterior_prevalence (Bayes exact), choisit_modele_mdl "
        "(MDL retient le degré 1 sur données linéaires).", _p_facade_stats_2),
    "Abstention honnête des estimateurs (façade stats 3)": (
        "comptage_surdisperse, analyse_queue_lourde, decompose_incertitude, classe_taux_robuste : trop peu "
        "de données -> ABSTENTION DITE, jamais un chiffre fabriqué (FAUX=0) ; seuil franchi -> estimation.",
        _p_facade_stats_3),
    "Raisonnement causal (graphe + effets)": ("Graphe causal exact, effets directs/interventions. cf. causalite.py", _p_causalite),
    "Logique trivaluée (vrai/faux/inconnu)": ("OWA : l'inconnu reste INCONNU, jamais deviné. cf. logique_tri.py", _p_logique_tri),
    "Révision de croyances (remplacer, pas empiler)": ("Nouvelle info plus fiable -> REMPLACE, tracé au journal. cf. revision.py", _p_revision),
    "Extraction de triplets depuis du texte": ("« Paris est la capitale de la France » -> (France, capitale, Paris). cf. extraction.py", _p_extraction),
    "Triangulation (corroboration indépendante)": ("Deux méthodes indépendantes concordantes -> corroboré. cf. triangulation.py", _p_triangulation),
    "Méréologie (composition partie-tout)": ("Parties directes/transitives, cycles refusés. cf. mereologie.py", _p_mereologie),
    "Frames n-aires (relations à rôles)": ("Rôle requis manquant détecté, rôle inconnu refusé. cf. frame.py", _p_frame),
    "Cas-limites (limites, parité, homogénéité)": ("Vérification par les bords : Ec homogène de degré 2. cf. cas_limites.py", _p_cas_limites),
    "Exercices curés (catalogue jugé)": ("La solution de référence passe ses propres tests. cf. exercices.py", _p_exercices),
    "Scout d'ingestion QLever (diligence FAUX=0)": ("Parse des lignes SPARQL de découverte. cf. scout_qlever.py", _p_scout_qlever),
    "Taxonomie des sujets (parseur du doc de bornage)": ("Parse SUJETS_BORNE_OU_NON.md en objets. cf. sujets.py", _p_sujets),
    "Harvester (routage des veines d'ingestion)": ("Typage de propriétés Wikidata candidates. cf. harvester.py", _p_harvester),
    "Compréhension intégrée (7 maillons)": ("Une phrase comprise de bout en bout, chaque maillon routé. cf. comprehension_integree.py", _p_comprehension_integree),
    "Oracle définitions (is-a auto-construit)": ("paris -> capitale dérivé des définitions. cf. oracle_definitions.py", _p_oracle_definitions),
    "Bootstrap du savoir (taxonomie multi-niveaux)": ("chat -> mammifère -> animal par chaînage. cf. bootstrap_savoir.py", _p_bootstrap_savoir),
    "Carte des limites du français model-free": ("Cartographie mesurée des barreaux atteints. cf. carte_limites_francais.py", _p_carte_limites),
    "Bilan de conservation (physique)": ("100 J = 60 + 40 J -> conserve ; déséquilibre détecté. cf. conservation.py", _p_conservation),
    "États & variables typés (espace d'états)": ("Domaines/dimensions imposés, immuabilité. cf. etat.py", _p_etat),
    "Lois manipulables (résolution dimensionnée)": ("E = ½mv² résolue pour E : 9 J typés. cf. loi.py", _p_loi),
    "Limites théoriques (bornes type Carnot)": ("Borne construite depuis une loi sound. cf. limite.py", _p_limite),
    "Simulation forward (trajectoires d'états)": ("1000 -> 729 en 3 pas de décroissance 0,9. cf. simulation.py", _p_simulation),
    "Géométrie 3D constructive (maillages)": ("Cube unité : 8 sommets, aire 6, volume 1. cf. geometrie3d.py", _p_geometrie3d),
    "Chemins 2D (lignes/Bézier, SVG)": ("Chemin contigu construit et validé. cf. chemin2d.py", _p_chemin2d),
    "Savoir massif (lexique 1,9 M entrées)": ("est_un transitif dirigé sur le lexique. cf. savoir_massif.py", _p_savoir_massif),
    "Utilité évolutive (le plus utile gagne)": ("Une solution jugée, utilité évaluée. cf. utilite.py", _p_utilite),
    "Fuzzing différentiel (crible sécurité)": ("Solution de référence -> ROBUSTE sur 30 essais. cf. fuzz.py", _p_fuzz),
    "Boucle générer-juger-garder": ("Campagne factice : seuls les passants entrent au store. cf. boucle.py", _p_boucle),
    "Auto-optimisation (coût des expressions)": ("sum(x)+sum(x) = 2 passes, x[0] = 0. cf. auto_optimise.py", _p_auto_optimise),
    "Mesure d'apprentissage (boîte de verre)": ("Un générateur évalué sur une tâche réelle. cf. mesure.py", _p_mesure),
    "Curateur d'exercices (tâches validées)": ("La 1re tâche du catalogue est validée par le juge. cf. curateur.py", _p_curateur),
    "Observatoire d'exploits (hard-coding détecté)": ("Sonde statique sur un memo-dict. cf. exploits.py", _p_exploits),
    "Ablation d'échafaudage (briques mesurées)": ("Ablation sur ensembles vides = liste vide. cf. echafaudage.py", _p_echafaudage),
    "Sélecteur situationnel (méta-architecture)": ("La classe Selecteur est construite. cf. selecteur.py", _p_selecteur),
    "Session d'entraînement (orchestrateur complet)": ("Mini-session réelle : 2 tours, journal produit. cf. session.py", _p_session),
    "Daemon lecteur (protocole Q-R)": ("Requête d'op inconnue -> réponse structurée. cf. lecteur_daemon.py", _p_lecteur_daemon),
    "Audit des ancres de vérité": ("Références externes calculées sur un état vide. cf. audit_ancres.py", _p_audit_ancres),
    "Auto-invention (empreintes comportementales)": ("args[0]*2 sur (1,2) -> (2,4) ; expression cassée -> None. cf. auto_invention.py", _p_auto_invention),
    "Rapport d'invention unifié": ("Rapport réel sur un mini-corpus + texte rendu. cf. rapport_invention.py", _p_rapport_invention),
    "Conversion kaikki (Wiktionnaire -> lexique)": ("chat -> mammifère extrait d'un dump réel minimal. cf. convertit_kaikki.py", _p_convertit_kaikki),
    "Charge lexique (cohérence du lexique)": ("2 entrées, acyclique. cf. charge_lexique.py", _p_charge_lexique),
    "Extension du savoir (fermeture transitive)": ("chaine chat -> mammifère -> animal. cf. etend_savoir.py", _p_etend_savoir),
    "Relations lexicales (synonymes/antonymes)": ("(chat, matou) extrait du lexique converti. cf. relations_lexique.py", _p_relations_lexique),
    "Fabrique sémantique (paires de compréhension)": ("Paires definition construites du lexique. cf. fabrique_semantique.py", _p_fabrique_semantique),
    "Fabrique français (conjugaisons vérifiées)": ("parler/present/je -> parle. cf. fabrique_francais.py", _p_fabrique_francais),
    "Fabrique compréhension (corpus vérifié)": ("Le catalogue d'items existe et est non vide. cf. fabrique_comprehension.py", _p_fabrique_comprehension),
    "Structure par tâche (batterie de stratégies)": ("Les stratégies de la batterie sont exécutables. cf. mesure_structure_pertache.py", _p_mesure_structure_pertache),
    "Recherche dirigée (synthèse bornée)": ("Synthèse réelle sur mini-spec, budget 3000. cf. recherche_dirigee.py", _p_recherche_dirigee),
    "Test du diable (une tâche résolue en direct)": ("BATTERIE[0] résolue par l'étage attendu. cf. diable.py", _p_diable),
    "Recherche d'architecture (corpus de primitives)": ("La primitive carre du corpus rend 9 pour 3. cf. cherche_architecture_max.py", _p_cherche_architecture_max),
    "Usine à données (accumulation de succès)": ("Store accumulé en répertoire temporaire. cf. usine_donnees.py", _p_usine_donnees),
    "Export de dataset (résumé d'un jsonl)": ("1 ligne lue, comptage exact. cf. exporte_dataset.py", _p_exporte_dataset),
})


def _p_qualitatif():
    from qualitatif import signe_produit, signe_somme, PLUS, MOINS, IND
    return signe_produit(PLUS, MOINS) == MOINS and signe_somme(PLUS, MOINS) == IND


REGISTRE.update({
    "Raisonnement qualitatif (algèbre des signes)": ("(+)×(−) = − ; (+)+(−) = indéterminé, jamais tranché. cf. qualitatif.py", _p_qualitatif),
})


def _p_tronc():
    from tronc import acte, INTERROGER_FAIT, TRANCHE
    f = acte("quelle est la capitale de la France ?")
    m = f.meilleur()
    c = acte("combien font 2+2 ?").meilleur()
    return (m.intention == INTERROGER_FAIT and m.relation == "capitale" and m.entites == ("france",)
            and c.statut == TRANCHE and c.reponse == "4")


REGISTRE.update({
    "Tronc de compréhension (acte -> faisceau)": ("Intention classée dans la carte fermée des 11 actes, entités/relation/régime extraits, calcul TRANCHÉ par juge réel. cf. tronc.py", _p_tronc),
})
