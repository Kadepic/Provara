"""
VALIDATION — MOTEUR D'INVENTION MULTI-ARGUMENT (invention_multi) : le cap mono→binaire.

Le moteur mono-arg (examine_cible) ne voyait que f(x). examine_cible_multi ouvre la classe des inventions à
DEUX arguments f(a, b), chemin SÉPARÉ (le mono-arg ne bouge pas), MÊMES gardes de soundness → FAUX=0.

Méthode SOUND : labels générés par la fonction de référence, paires adversariales (incl. asymétriques a≠b et
valeurs négatives), réalisation RE-VÉRIFIÉE hors moteur.

Prouve : (1) LES 5 VERDICTS — EXISTE_DEJA (registre), INVENTION (nouveau : a²+b²), AMBIGU (≥2 réalisations
divergent), BRIQUE_MANQUANTE (affine hors vocab), INCOHERENT ; (2) COMMUTATIVITÉ sound — b−a est distingué de
a−b par la sonde SWAP (jamais un faux EXISTE_DEJA=difference), et max(a,b) commutatif ne crée PAS d'ambiguïté ;
(3) INVENTION CORRECTE — la réalisation reproduit toutes les paires + des paires fraîches (hors moteur) ;
(4) DÉTERMINISME ; (5) SÉPARATION — le mono-arg examine_cible reste intact (une cible mono classique inchangée).
"""
from __future__ import annotations

from garde_ressources import borne
borne(max_cpu_s=400)
import ia
import invention_multi as IM
import moteur_invention as MI

ok = total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def _fnn(expr, params):
    ns: dict = {}
    exec(f"def _f({', '.join(params)}):\n    return {expr}\n", ns)
    return ns["_f"]


def _reproduit2(expr, paires):
    f = _fnn(expr, ["a", "b"])
    for (a, b), o in paires:
        r = f(a, b)
        if r != o or isinstance(r, bool) != isinstance(o, bool):
            return False
    return True


def _reproduit3(expr, paires):
    f = _fnn(expr, ["a", "b", "c"])
    for (a, b, c), o in paires:
        r = f(a, b, c)
        if r != o or isinstance(r, bool) != isinstance(o, bool):
            return False
    return True


def P(f, pairs):
    return [((a, b), f(a, b)) for a, b in pairs]


PAIRS = [(3, 5), (7, 2), (4, 9), (9, 1), (2, 8), (1, 6)]

# ── (1) LES 5 VERDICTS ───────────────────────────────────────────────────────────────────────────────────
ps = P(lambda a, b: a + b, PAIRS)
check("EXISTE_DEJA : a+b couvert par le registre binaire",
      IM.examine_cible_multi("s", ps[:4], ps[4:]).statut == MI.EXISTE_DEJA)

ps = P(lambda a, b: a * a + b * b, PAIRS)
vinv = IM.examine_cible_multi("sommes_carres", ps[:4], ps[4:])
check("INVENTION : a²+b² (nouveau, hors registre)", vinv.statut == MI.INVENTION)
check("INVENTION : réalisation reproduit toutes les paires (hors moteur)",
      vinv.par and _reproduit2(vinv.par, ps))
check("INVENTION : correcte sur des paires FRAÎCHES (pas une coïncidence)",
      _reproduit2(vinv.par, P(lambda a, b: a * a + b * b, [(0, 7), (5, 5), (-2, 3)])))

vamb = IM.examine_cible_multi("amb", [((3, -4), -7)], [((2, -3), -5)])
check("AMBIGU : ≥2 réalisations binaires divergent (a²−b² vs b−a)",
      vamb.statut == MI.AMBIGU and vamb.sonde is not None)

ps = P(lambda a, b: a - 2 * b, PAIRS)
check("BRIQUE_MANQUANTE : a−2b (affine hors vocabulaire) = frontière honnête",
      IM.examine_cible_multi("affine", ps[:4], ps[4:]).statut == MI.BRIQUE_MANQUANTE)

check("INCOHERENT : même entrée, deux sorties",
      IM.examine_cible_multi("inc", [((1, 2), 5)], [((1, 2), 9)]).statut == MI.INCOHERENT)

# ── (2) COMMUTATIVITÉ sound ──────────────────────────────────────────────────────────────────────────────
ps = P(lambda a, b: b - a, PAIRS)
vba = IM.examine_cible_multi("reverse_diff", ps[:4], ps[4:])
check("commutativité : b−a distingué de a−b par la sonde SWAP (invention b−a, pas existe a−b)",
      vba.statut == MI.INVENTION and vba.par is not None and _reproduit2(vba.par, ps))
ps = P(lambda a, b: max(a, b), PAIRS)
check("commutativité : max(a,b) commutatif -> EXISTE_DEJA, PAS d'ambiguïté",
      IM.examine_cible_multi("mx", ps[:4], ps[4:]).statut == MI.EXISTE_DEJA)

# ── (4) DÉTERMINISME ─────────────────────────────────────────────────────────────────────────────────────
ps = P(lambda a, b: a * b + a + b, PAIRS)
v1 = IM.examine_cible_multi("t", ps[:4], ps[4:])
v2 = IM.examine_cible_multi("t", ps[:4], ps[4:])
check("déterminisme : deux passes, même verdict et même réalisation",
      (v1.statut, v1.par) == (v2.statut, v2.par) and v1.statut == MI.INVENTION)

# ── (5) SÉPARATION : le mono-arg examine_cible reste intact ──────────────────────────────────────────────
vm = MI.examine_cible("amplitude", "x", [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)],
                      [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4)])
check("séparation : le moteur mono-arg (amplitude) reste INVENTION, inchangé",
      vm.statut == MI.INVENTION and vm.par is not None)

# ── (6) FAÇADE INTÉGRÉE : ia.invente_multi (la porte de première classe, pas seulement le module isolé) ──
ps = P(lambda a, b: a * a + b * b, PAIRS)
vf = ia.invente_multi("sommes_carres", ps[:4], ps[4:])
check("façade : ia.invente_multi rend l'invention binaire (intégré, pas isolé)",
      vf.statut == MI.INVENTION and vf.par is not None and _reproduit2(vf.par, ps))
check("façade : ia.invente_multi sur a+b -> EXISTE_DEJA (registre binaire câblé)",
      ia.invente_multi("s", P(lambda a, b: a + b, PAIRS)[:4], P(lambda a, b: a + b, PAIRS)[4:]).statut == MI.EXISTE_DEJA)

# ══ RUNG ARITÉ 3 (TERNAIRE) — patron reproductible ═══════════════════════════════════════════════════════
def P3(f, triples):
    return [((a, b, c), f(a, b, c)) for a, b, c in triples]


TR = [(3, 5, 2), (7, 2, 9), (4, 4, 1), (9, 1, 6), (2, 8, 3), (1, 6, 5), (0, 3, 7)]

for nom, f in [("somme3", lambda a, b, c: a + b + c),
               ("produit3", lambda a, b, c: a * b * c),
               ("mediane3", lambda a, b, c: sorted([a, b, c])[1])]:
    ps = P3(f, TR)
    check(f"ternaire EXISTE_DEJA : {nom} couvert par le registre ternaire",
          IM.examine_cible_multi(nom, ps[:5], ps[5:]).statut == MI.EXISTE_DEJA)

ps = P3(lambda a, b, c: a * a + b * b + c * c, TR)
vt = IM.examine_cible_multi("sommes_carres3", ps[:5], ps[5:])
check("ternaire INVENTION : a²+b²+c² (nouveau)", vt.statut == MI.INVENTION)
check("ternaire INVENTION : reproduit toutes les paires (hors moteur)", vt.par and _reproduit3(vt.par, ps))
check("ternaire INVENTION : correcte sur des triplets FRAIS (pas une coïncidence)",
      _reproduit3(vt.par, P3(lambda a, b, c: a * a + b * b + c * c, [(1, 0, 2), (5, 5, 5), (-1, 3, 2)])))

ps = P3(lambda a, b, c: (a + b) * c, TR)
vp = IM.examine_cible_multi("somme_fois_c", ps[:5], ps[5:])
check("ternaire INVENTION : (a+b)*c (assemblage en arbre)", vp.statut == MI.INVENTION and _reproduit3(vp.par, ps))

ps = P3(lambda a, b, c: a + 2 * b + 3 * c, TR)
check("ternaire BRIQUE_MANQUANTE : a+2b+3c (affine hors vocabulaire) = frontière honnête",
      IM.examine_cible_multi("affine3", ps[:5], ps[5:]).statut == MI.BRIQUE_MANQUANTE)

check("ternaire INCOHERENT : même entrée, deux sorties",
      IM.examine_cible_multi("inc3", [((1, 2, 3), 5)], [((1, 2, 3), 9)]).statut == MI.INCOHERENT)

# ORDRE : a-b-c est sensible à l'ordre (a distingué de b,c) -> la réalisation dépend de l'ordre
ps = P3(lambda a, b, c: a - b - c, TR)
vo = IM.examine_cible_multi("a_moins_b_moins_c", ps[:5], ps[5:])
check("ternaire ordre : a−b−c résolu, réalisation reproduit tout", vo.par and _reproduit3(vo.par, ps))
fo = _fnn(vo.par, ["a", "b", "c"])
check("ternaire ordre : la réalisation dépend BIEN de l'ordre (a↔b diffère)", fo(5, 1, 2) != fo(1, 5, 2))

# SÉPARATION inter-arités : registre ternaire pas pollué par le binaire (somme3 ≠ EXISTANT_BINAIRE)
check("séparation : le registre par arité est routé (binaire pour 2, ternaire pour 3)",
      IM.EXISTANT_TERNAIRE is IM._REGISTRES[3] and IM.EXISTANT_BINAIRE is IM._REGISTRES[2])

print(f"\n== VALIDE_INVENTION_MULTI : {ok}/{total} ==")
assert ok == total
