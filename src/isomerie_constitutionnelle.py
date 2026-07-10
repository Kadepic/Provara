"""
ISOMÉRIE CONSTITUTIONNELLE — dénombrement EXACT des isomères d'ALCANES CnH(2n+2) par ÉNUMÉRATION EXHAUSTIVE.

Même posture FAUX=0 que `physique` / `chimie` (la réalité/le théorème juge, jamais un faux) :
  • Le MÉCANISME est un THÉORÈME EXACT, pas une corrélation ni une formule close devinée :
      – Un alcane CnH(2n+2) est acyclique et saturé ; son squelette carboné est exactement un ARBRE
        non enraciné à n sommets dont TOUS les sommets ont un degré ≤ 4 (valence du carbone), et deux
        alcanes sont le même isomère constitutionnel ssi leurs squelettes sont ISOMORPHES.
        Dénombrer les isomères = dénombrer ces arbres à isomorphisme près (suite OEIS A000602).
      – ÉNUMÉRATION : tout arbre de degré ≤ 4 à k+1 sommets s'obtient en greffant une feuille sur un
        arbre de degré ≤ 4 à k sommets (retirer une feuille ne fait jamais croître un degré). On étend
        donc niveau par niveau depuis l'arbre à 1 sommet, en greffant une feuille sur chaque sommet de
        degré < 4, et on DÉDOUBLONNE par CERTIFICAT CANONIQUE.
      – CERTIFICAT CANONIQUE (AHU) : l'ensemble des CENTRES d'un arbre (1 ou 2 sommets, obtenus par
        effeuillage) est invariant par isomorphisme ; le certificat = min des encodages AHU de l'arbre
        enraciné en chacun de ses centres, où AHU(v) = "(" + concaténation TRIÉE des AHU des enfants + ")".
        Deux arbres sont isomorphes ssi leurs certificats sont égaux (théorème d'Aho-Hopcroft-Ullman).
  • Tout est ENTIER et EXACT : aucun flottant, aucune approximation, aucun arrondi.
  • BUDGET D'ÉNUMÉRATION HONNÊTE : n ≤ 12 (355 squelettes). Au-delà -> ValueError (abstention), on ne
    prétend pas à un dénombrement qu'on n'a pas réellement effectué dans un temps borné.

GARANTIES (vérifiées en adverse par `valide_isomerie_constitutionnelle.py`) :
  - n non entier (bool, float, str, NaN/inf, None) -> ValueError (True n'est PAS 1) ;
  - n < 1 -> ValueError (pas d'alcane sans carbone) ; n > 12 -> ValueError (budget d'énumération, DIT) ;
  - formule non alcane (C2H4, C6H6, H2O, …) -> ValueError explicite
    ('hors périmètre : seuls les alcanes CnH2n+2 sont dénombrés exactement') ;
  - formule mal formée (casse, zéros de tête, texte arbitraire) -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

NOTE DE PÉRIMÈTRE : on dénombre les isomères CONSTITUTIONNELS (connectivité), PAS les stéréoisomères
(voir src/stereochimie.py, module distinct et réservé) ; les squelettes ignorent les hydrogènes, qui
sont entièrement déterminés par le squelette (chaque carbone complète sa valence 4 avec des H).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `re` (stdlib).
"""
from __future__ import annotations

import re

SOURCE = ("OEIS A000602 (isomères d'alcanes) ; théorème arbre = squelette d'alcane (Cayley 1875) ; "
          "certificat canonique AHU (Aho-Hopcroft-Ullman, The Design and Analysis of Computer Algorithms, 1974)")

N_MAX = 12          # budget d'énumération honnête : au-delà, abstention (ValueError), jamais une devinette
_DEGRE_MAX = 4      # valence du carbone

_RE_ALCANE = re.compile(r"C([1-9]\d*)?H([1-9]\d*)")  # zéros de tête refusés ; 'CH4' == 'C1H4'


# ── VALIDATION ─────────────────────────────────────────────────────────────────────────────────────────────────
def _exige_n(n) -> int:
    """n = nombre de carbones : entier (bool REFUSÉ) dans [1, N_MAX]. Sinon ValueError."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError("n invalide : un entier (int) est requis (bool/float/str refusés)")
    if n < 1:
        raise ValueError("n < 1 : pas d'alcane sans atome de carbone")
    if n > N_MAX:
        raise ValueError(f"n > {N_MAX} : hors budget d'énumération honnête (abstention plutôt qu'une devinette)")
    return n


# ── CENTRES D'UN ARBRE (effeuillage) ───────────────────────────────────────────────────────────────────────────
def _centres(adj: dict) -> list:
    """Centre(s) de l'arbre (1 ou 2 sommets) par effeuillage successif — invariant par isomorphisme."""
    n = len(adj)
    if n <= 2:
        return sorted(adj.keys())
    deg = {v: len(adj[v]) for v in adj}
    feuilles = [v for v in adj if deg[v] == 1]
    restants = n
    while restants > 2:
        restants -= len(feuilles)
        prochaines = []
        for f in feuilles:
            deg[f] = 0
            for u in adj[f]:
                if deg[u] > 1:
                    deg[u] -= 1
                    if deg[u] == 1:
                        prochaines.append(u)
        feuilles = prochaines
    return sorted(feuilles)


# ── ENCODAGE AHU (arbre enraciné -> chaîne canonique) ──────────────────────────────────────────────────────────
def _ahu(adj: dict, racine: int) -> str:
    """Encodage canonique AHU de l'arbre enraciné en `racine` : parenthésage trié récursivement."""
    def rec(v: int, parent: int) -> str:
        fils = sorted(rec(u, v) for u in adj[v] if u != parent)
        return "(" + "".join(fils) + ")"
    return rec(racine, -1)


def _certificat(adj: dict) -> str:
    """Certificat canonique de l'arbre NON enraciné : min des AHU enracinés aux centres."""
    return min(_ahu(adj, c) for c in _centres(adj))


# ── ÉNUMÉRATION EXHAUSTIVE DES SQUELETTES (arbres de degré ≤ 4) ────────────────────────────────────────────────
def _enumere(n: int) -> dict:
    """Tous les arbres à n sommets de degré ≤ 4, à isomorphisme près : {certificat: adjacence représentante}.

    Extension niveau par niveau (greffe d'une feuille sur chaque sommet de degré < 4) + déduplication
    par certificat canonique. EXHAUSTIF : retirer une feuille d'un arbre de degré ≤ 4 redonne un arbre
    de degré ≤ 4, donc chaque arbre du niveau k+1 est bien atteint depuis le niveau k."""
    arbres = {_certificat({0: []}): {0: []}}          # n=1 : le sommet isolé (méthane)
    for k in range(1, n):
        suivants: dict = {}
        for adj in arbres.values():
            for v in range(k):                        # greffer la feuille k sur chaque sommet possible
                if len(adj[v]) < _DEGRE_MAX:
                    nouveau = {u: list(vs) for u, vs in adj.items()}
                    nouveau[v].append(k)
                    nouveau[k] = [v]
                    cert = _certificat(nouveau)
                    if cert not in suivants:
                        suivants[cert] = nouveau
        arbres = suivants
    return arbres


# ── API PUBLIQUE ───────────────────────────────────────────────────────────────────────────────────────────────
def squelettes_alcane(n: int) -> list:
    """Liste TRIÉE des certificats canoniques des squelettes carbonés de CnH(2n+2).

    Chaque certificat représente exactement UN isomère constitutionnel (arbre de degré ≤ 4 à n sommets,
    à isomorphisme près). n hors [1, 12] ou non entier -> ValueError."""
    n = _exige_n(n)
    return sorted(_enumere(n).keys())


def nombre_isomeres_alcane(n: int) -> int:
    """Nombre EXACT d'isomères constitutionnels de l'alcane CnH(2n+2) (suite OEIS A000602).

    Obtenu par énumération exhaustive + certificat canonique, PAS par une formule close.
    n hors [1, 12] ou non entier -> ValueError."""
    n = _exige_n(n)
    return len(_enumere(n))


def nombre_isomeres(formule: str) -> int:
    """Nombre d'isomères constitutionnels depuis la formule brute (ex. 'CH4', 'C4H10' -> 2).

    Seuls les alcanes CnH(2n+2), 1 ≤ n ≤ 12, sont dénombrés exactement. Toute autre formule
    (C2H4, C6H6, H2O, …) -> ValueError (abstention explicite, jamais une devinette)."""
    if not isinstance(formule, str):
        raise ValueError("formule invalide : une chaîne (str) est requise, ex. 'C4H10'")
    m = _RE_ALCANE.fullmatch(formule)
    if m is None:
        raise ValueError("hors périmètre : seuls les alcanes CnH2n+2 sont dénombrés exactement "
                         "(format attendu : 'CH4', 'C4H10', …)")
    n = int(m.group(1)) if m.group(1) else 1
    h = int(m.group(2))
    if h != 2 * n + 2:
        raise ValueError(f"hors périmètre : seuls les alcanes CnH2n+2 sont dénombrés exactement "
                         f"(C{n}H{h} n'est pas un alcane : H attendu = {2 * n + 2})")
    return nombre_isomeres_alcane(n)
