"""
DÉVELOPPEMENT DÉCIMAL D'UN RATIONNEL — préfixe, période, finitude (arithmétique ENTIÈRE exacte).

Même posture FAUX=0 que `physique` / `chimie` / `geometries_non_euclidiennes` (le théorème juge, jamais un faux) :
  • Le MÉCANISME est un THÉORÈME EXACT, pas une corrélation :
      – Pour un rationnel p/q RÉDUIT, on écrit q = 2^a · 5^b · q' avec pgcd(q', 10) = 1.
      – Le développement décimal est FINI ssi q' = 1 (théorème classique : les seuls diviseurs de 10^n
        sont de la forme 2^a·5^b).
      – La longueur du PRÉFIXE (partie non périodique après la virgule) vaut s = max(a, b).
      – La longueur de la PÉRIODE vaut l'ORDRE MULTIPLICATIF de 10 modulo q' (par convention 0 si q' = 1,
        développement fini). C'est le théorème du développement décimal périodique (Gauss, Disquisitiones,
        art. 312-318 : la période de 1/q' est l'ordre de 10 dans (Z/q'Z)*).
  • AUCUN flottant : tout est calculé en arithmétique entière et en `fractions.Fraction`. Les chiffres
    du préfixe et de la période sont obtenus par divisions euclidiennes EXACTES :
        r/Q = (r·10^s) / (Q·10^s)  avec  r·2^(s−a)·5^(s−b) = D·q' + r2  ->  préfixe = D sur s chiffres,
        période = r2·(10^t − 1)/q' sur t chiffres (division EXACTE car 10^t ≡ 1 (mod q')).
  • BOUCLE FERMÉE : `reconstruit` est le chemin INVERSE (préfixe/période -> Fraction), indépendant du
    chemin direct, ce qui permet de prouver reconstruit(developpement(p, q)) == Fraction(p, q).

GARANTIES (vérifiées en adverse par `valide_developpement_decimal.py`) :
  - q = 0  -> ValueError  (division par zéro : pas de développement) ;
  - p ou q non entier (float, str, Fraction, complex, None) -> ValueError ;
  - bool REFUSÉ partout (True n'est pas 1) -> ValueError ;
  - pour longueur_periode / longueur_prefixe / est_fini : q ≤ 0 -> ValueError (un dénominateur canonique
    est strictement positif ; le signe se traite dans `developpement`) ;
  - `reconstruit` REFUSE tout dict mal formé (clés manquantes/en trop, signe hors {'+','-'}, entier
    négatif ou bool, préfixe/période non composés de chiffres, incohérence fini <-> période) ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` et `fractions` (stdlib).
"""
from __future__ import annotations

import math
from fractions import Fraction

SOURCE = ("théorème du développement décimal d'un rationnel : q = 2^a·5^b·q', préfixe = max(a,b), "
          "période = ordre multiplicatif de 10 mod q' (Gauss, Disquisitiones Arithmeticae, art. 312-318)")


# ── VALIDATION D'ENTRÉE ────────────────────────────────────────────────────────────────────────────────────────
def _exige_entier(x, nom: str) -> int:
    """Entier Python strict : bool REFUSÉ (True n'est pas 1), float/str/None REFUSÉS."""
    if isinstance(x, bool) or not isinstance(x, int):
        raise ValueError(f"{nom} invalide : un entier (int, pas bool/float/str) est requis")
    return x


def _exige_denominateur_positif(q) -> int:
    """Dénominateur canonique : entier strictement positif."""
    q = _exige_entier(q, "q")
    if q <= 0:
        raise ValueError("q invalide : un entier strictement positif est requis "
                         "(le signe se traite dans developpement(p, q))")
    return q


# ── DÉCOMPOSITION q = 2^a · 5^b · q' ───────────────────────────────────────────────────────────────────────────
def _decompose(q: int):
    """Retire les facteurs 2 et 5 : renvoie (a, b, q') avec q = 2^a·5^b·q' et pgcd(q', 10) = 1."""
    a = 0
    while q % 2 == 0:
        q //= 2
        a += 1
    b = 0
    while q % 5 == 0:
        q //= 5
        b += 1
    return a, b, q


def _ordre_multiplicatif_10(m: int) -> int:
    """Ordre de 10 dans (Z/mZ)* pour pgcd(m, 10) = 1 ; 0 par convention si m = 1 (pas de période)."""
    if m == 1:
        return 0
    t = 1
    x = 10 % m
    while x != 1:
        x = (x * 10) % m
        t += 1
    return t


# ── LONGUEURS ET FINITUDE (fonctions du dénominateur seul) ─────────────────────────────────────────────────────
def longueur_prefixe(q: int) -> int:
    """Longueur du préfixe non périodique de n/q (fraction réduite) : max(a, b) où q = 2^a·5^b·q'."""
    q = _exige_denominateur_positif(q)
    a, b, _ = _decompose(q)
    return max(a, b)


def longueur_periode(q: int) -> int:
    """Longueur de la période de n/q (fraction réduite) : ordre de 10 mod q' ; 0 si développement fini."""
    q = _exige_denominateur_positif(q)
    _, _, m = _decompose(q)
    return _ordre_multiplicatif_10(m)


def est_fini(q: int) -> bool:
    """True ssi le développement décimal de n/q (réduit) est FINI, i.e. q = 2^a·5^b (q' = 1)."""
    q = _exige_denominateur_positif(q)
    _, _, m = _decompose(q)
    return m == 1


# ── DÉVELOPPEMENT COMPLET ──────────────────────────────────────────────────────────────────────────────────────
def developpement(p: int, q: int) -> dict:
    """Développement décimal EXACT de p/q (arithmétique entière, aucun flottant).

    Renvoie {'signe': '+'|'-', 'entier': int ≥ 0 (magnitude), 'prefixe': str (chiffres non périodiques
    après la virgule), 'periode': str (chiffres de la période, '' si fini), 'fini': bool}.
    Lecture : p/q = signe · (entier . prefixe (periode)periodique).  q = 0 -> ValueError."""
    p = _exige_entier(p, "p")
    q = _exige_entier(q, "q")
    if q == 0:
        raise ValueError("q = 0 : division par zéro, pas de développement décimal")
    signe = '-' if (p < 0) != (q < 0) and p != 0 else '+'
    P, Q = abs(p), abs(q)
    g = math.gcd(P, Q)
    P //= g
    Q //= g
    entier, r = divmod(P, Q)                      # partie entière (magnitude) + reste fractionnaire r/Q
    a, b, m = _decompose(Q)
    s = max(a, b)                                 # longueur du préfixe (théorème : q = 2^a·5^b·q')
    # r/Q · 10^s a pour dénominateur m (coprime à 10) : numérateur N = r · 2^(s-a) · 5^(s-b)
    N = r * (2 ** (s - a)) * (5 ** (s - b))
    D, r2 = divmod(N, m)                          # D = chiffres du préfixe, r2/m = partie purement périodique
    prefixe = str(D).zfill(s) if s > 0 else ''
    if m == 1:                                    # q' = 1 -> développement FINI (r2 = 0 garanti)
        periode = ''
        fini = True
    else:
        t = _ordre_multiplicatif_10(m)            # longueur de la période = ordre de 10 mod q'
        chiffres = r2 * (10 ** t - 1) // m        # division EXACTE : m | r2·(10^t − 1) car 10^t ≡ 1 (mod m)
        periode = str(chiffres).zfill(t)
        fini = False
    return {'signe': signe, 'entier': entier, 'prefixe': prefixe, 'periode': periode, 'fini': fini}


# ── RECONSTRUCTION (chemin INVERSE, pour la boucle fermée) ─────────────────────────────────────────────────────
_CLES = frozenset({'signe', 'entier', 'prefixe', 'periode', 'fini'})


def _exige_chiffres(x, nom: str) -> str:
    if not isinstance(x, str) or (x != '' and not x.isascii()) or (x != '' and not x.isdigit()):
        raise ValueError(f"{nom} invalide : une chaîne de chiffres décimaux (éventuellement vide) est requise")
    return x


def reconstruit(dev: dict) -> Fraction:
    """INVERSE de `developpement` : (signe, entier, préfixe, période) -> Fraction EXACTE.

    Formule indépendante du chemin direct (série géométrique sommée) :
        valeur = entier + prefixe/10^s + periode / ((10^t − 1)·10^s),   s = len(prefixe), t = len(periode).
    Dict mal formé -> ValueError."""
    if not isinstance(dev, dict) or set(dev.keys()) != _CLES:
        raise ValueError("dev invalide : dict avec exactement les clés "
                         "{'signe','entier','prefixe','periode','fini'} requis")
    signe = dev['signe']
    if signe not in ('+', '-') or not isinstance(signe, str):
        raise ValueError("signe invalide : '+' ou '-' requis")
    entier = dev['entier']
    if isinstance(entier, bool) or not isinstance(entier, int) or entier < 0:
        raise ValueError("entier invalide : un entier ≥ 0 (magnitude) est requis")
    prefixe = _exige_chiffres(dev['prefixe'], "prefixe")
    periode = _exige_chiffres(dev['periode'], "periode")
    fini = dev['fini']
    if not isinstance(fini, bool):
        raise ValueError("fini invalide : un bool est requis")
    if fini != (periode == ''):
        raise ValueError("incohérence : fini doit valoir True ssi la période est vide")
    s = len(prefixe)
    t = len(periode)
    valeur = Fraction(entier)
    if s > 0:
        valeur += Fraction(int(prefixe), 10 ** s)
    if t > 0:
        valeur += Fraction(int(periode), (10 ** t - 1) * (10 ** s))
    return -valeur if signe == '-' else valeur
