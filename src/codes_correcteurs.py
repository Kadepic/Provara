"""
CODES CORRECTEURS D'ERREURS — théorie des codes en blocs, EXACTE sur GF(2).

ATTENTION AUX PIÈGES DE NOM : `bioinfo.distance_hamming` est une métrique de SÉQUENCES ADN ;
`raster_png` n'utilise le CRC que pour DÉTECTER. Ici : théorie des codes correcteurs, arithmétique
entière exacte sur l'alphabet binaire {0, 1} — aucun flottant, aucune approximation.

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (le théorème juge, jamais un faux) :
  • DISTANCE DE HAMMING d(u, v) = nombre de positions où u et v diffèrent (mots binaires de MÊME longueur).
  • DISTANCE MINIMALE d'un code = min des d(u, v) sur TOUTES les paires de mots distincts (exhaustif).
  • CAPACITÉS (théorèmes classiques de la théorie des codes) :
      – un code de distance minimale d DÉTECTE jusqu'à  d − 1  erreurs ;
      – un code de distance minimale d CORRIGE jusqu'à  ⌊(d − 1)/2⌋  erreurs (décodage au plus proche).
  • CODE DE HAMMING(7,4) — construction canonique, positions 1..7, bits de parité aux positions
    puissances de 2 (1, 2, 4), bits de données aux positions 3, 5, 6, 7 :
      codeword = p1 p2 d1 p3 d2 d3 d4  avec  p1 = d1⊕d2⊕d4, p2 = d1⊕d3⊕d4, p3 = d2⊕d3⊕d4.
    Le SYNDROME (s4 s2 s1 en binaire) vaut la POSITION de l'erreur unique (0 = aucun bit faux).
    d_min = 3 : corrige EXACTEMENT 1 erreur ; DEUX erreurs -> le décodeur se trompe, c'est le comportement
    attendu d'un code de distance 3 (documenté, jamais masqué).
  • PARITÉ (convention parité PAIRE) : bit_parite(mot) complète le mot à poids pair ;
    detecte_parite(mot) -> True ssi le poids est IMPAIR (erreur détectée). d = 2 : détecte 1, corrige 0.
  • BORNE DE SINGLETON :  d ≤ n − k + 1 ; un code atteignant l'ÉGALITÉ est dit MDS.
    THÉORÈME (binaire) : sur GF(2), les SEULS codes MDS sont les familles TRIVIALES
    [n, n, 1] (espace entier), [n, n−1, 2] (parité) et [n, 1, n] (répétition) — vrai même pour les
    codes NON linéaires (MacWilliams & Sloane, The Theory of Error-Correcting Codes, ch. 11).
    `est_mds(n, k, d)` répond donc à « existe-t-il un code BINAIRE (n, k, d) MDS ? » :
    True ssi d = n − k + 1 ET (k = n, d = 1) ou (k = n−1, d = 2) ou (k = 1, d = n) ;
    False si d < n − k + 1 (pas MDS) OU si l'égalité est INATTEIGNABLE en binaire
    (ex. (7,4,4) : le meilleur [7,4] binaire a d = 3) ; ValueError si d > n − k + 1
    (Singleton violée : aucun code binaire (n, k, d) n'existe).
  • BORNE DE HAMMING (empilement de sphères, binaire) :  2^k · Σ_{i=0}^{t} C(n, i) ≤ 2^n.
    Un code atteignant l'égalité est PARFAIT (Hamming(7,4) et Golay(23,12) le sont).

GARANTIES (vérifiées en adverse par `valide_codes_correcteurs.py`) :
  - mots de longueurs différentes -> ValueError ; alphabet non binaire -> ValueError ;
  - mot vide -> ValueError ; mot qui n'est pas une chaîne '0'/'1' -> ValueError ;
  - moins de 2 mots pour la distance minimale -> ValueError ; code vide -> ValueError ;
  - mots DUPLIQUÉS dans un code -> ValueError (d = 0 : pas un code, on s'abstient) ;
  - paramètres n, k, d, t non entiers, bool, NaN/inf, hors domaine -> ValueError ;
  - extraction des données d'un mot de 7 bits NON codeword (syndrome ≠ 0) -> ValueError (jamais des
    données potentiellement fausses) ; est_mds sur un code violant Singleton -> ValueError (code impossible) ;
  - est_mds ne qualifie JAMAIS de MDS des paramètres binairement inexistants : (7,4,4), (23,12,12),
    (10,5,6) -> False (l'égalité de Singleton seule ne suffit PAS en binaire) ;
  - fonctions PURES, déterministes, arithmétique entière exacte ; conservateur (faux négatif toléré,
    faux POSITIF interdit).

Le module n'importe que `math` (stdlib, pour math.comb).
"""
from __future__ import annotations

import math

SOURCE = ("théorie des codes correcteurs classique : distance de Hamming (Hamming 1950), "
          "code de Hamming(7,4), bornes de Singleton (1964) et de Hamming (empilement de sphères) ; "
          "trivialité des MDS binaires : MacWilliams & Sloane, The Theory of Error-Correcting Codes, ch. 11")


# ── VALIDATION D'ENTRÉE ────────────────────────────────────────────────────────────────────────────────────────
def _exige_mot(m, longueur: int | None = None) -> str:
    """Mot binaire : chaîne non vide sur l'alphabet {'0','1'}, longueur imposée si demandée."""
    if not isinstance(m, str):
        raise ValueError("mot invalide : une chaîne de '0'/'1' est requise")
    if len(m) == 0:
        raise ValueError("mot vide : un mot binaire non vide est requis")
    if any(c not in "01" for c in m):
        raise ValueError("alphabet non binaire : seuls les caractères '0' et '1' sont admis")
    if longueur is not None and len(m) != longueur:
        raise ValueError(f"longueur invalide : {longueur} bits sont requis, {len(m)} reçus")
    return m


def _exige_entier(x, mini: int, nom: str) -> int:
    """Entier ≥ mini ; les bool sont REFUSÉS (True n'est pas 1) ; float/str/NaN/inf refusés."""
    if not isinstance(x, int) or isinstance(x, bool) or x < mini:
        raise ValueError(f"{nom} invalide : un entier >= {mini} est requis")
    return x


# ── (a) DISTANCE DE HAMMING ────────────────────────────────────────────────────────────────────────────────────
def distance_hamming(u: str, v: str) -> int:
    """d(u, v) = nombre de positions où u et v diffèrent. Longueurs différentes -> ValueError."""
    u = _exige_mot(u)
    v = _exige_mot(v)
    if len(u) != len(v):
        raise ValueError("mots de longueurs différentes : la distance de Hamming n'est pas définie")
    return sum(1 for a, b in zip(u, v) if a != b)


# ── (b) DISTANCE MINIMALE (exhaustif sur toutes les paires) ────────────────────────────────────────────────────
def distance_minimale(mots) -> int:
    """d_min du code = min d(u, v) sur toutes les paires de mots distincts (comparaison exhaustive).

    Code vide ou < 2 mots -> ValueError ; mots dupliqués -> ValueError (d = 0 : pas un code)."""
    if not isinstance(mots, (list, tuple)):
        raise ValueError("code invalide : une liste/tuple de mots binaires est requise")
    if len(mots) == 0:
        raise ValueError("code vide : au moins 2 mots sont requis pour une distance minimale")
    if len(mots) < 2:
        raise ValueError("moins de 2 mots : la distance minimale d'un code exige au moins 2 mots")
    n = None
    for m in mots:
        m = _exige_mot(m)
        if n is None:
            n = len(m)
        elif len(m) != n:
            raise ValueError("mots de longueurs différentes : un code en bloc a une longueur unique")
    if len(set(mots)) != len(mots):
        raise ValueError("mots dupliqués : d_min serait 0, ce n'est pas un code (abstention)")
    return min(distance_hamming(mots[i], mots[j])
               for i in range(len(mots)) for j in range(i + 1, len(mots)))


# ── (c) CAPACITÉS (théorèmes) ──────────────────────────────────────────────────────────────────────────────────
def detecte_jusqu_a(d: int) -> int:
    """Un code de distance minimale d détecte jusqu'à d − 1 erreurs (théorème). d entier ≥ 1."""
    d = _exige_entier(d, 1, "distance minimale d")
    return d - 1


def corrige_jusqu_a(d: int) -> int:
    """Un code de distance minimale d corrige jusqu'à ⌊(d − 1)/2⌋ erreurs (théorème). d entier ≥ 1."""
    d = _exige_entier(d, 1, "distance minimale d")
    return (d - 1) // 2


# ── (d) CODE DE HAMMING(7,4) — construction canonique ─────────────────────────────────────────────────────────
def hamming74_encode(donnees: str) -> str:
    """Encode 4 bits de données en un codeword de 7 bits : p1 p2 d1 p3 d2 d3 d4.

    p1 = d1⊕d2⊕d4, p2 = d1⊕d3⊕d4, p3 = d2⊕d3⊕d4 (parités des positions 1, 2, 4)."""
    donnees = _exige_mot(donnees, 4)
    d1, d2, d3, d4 = (int(c) for c in donnees)
    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4
    return f"{p1}{p2}{d1}{p3}{d2}{d3}{d4}"


def hamming74_syndrome(mot: str) -> int:
    """Syndrome d'un mot de 7 bits : la POSITION (1..7) de l'erreur unique, 0 si aucune.

    s1 = parité des positions {1,3,5,7}, s2 = {2,3,6,7}, s4 = {4,5,6,7} ; syndrome = s1 + 2·s2 + 4·s4."""
    mot = _exige_mot(mot, 7)
    b = [int(c) for c in mot]              # b[0] = position 1, ..., b[6] = position 7
    s1 = b[0] ^ b[2] ^ b[4] ^ b[6]
    s2 = b[1] ^ b[2] ^ b[5] ^ b[6]
    s4 = b[3] ^ b[4] ^ b[5] ^ b[6]
    return s1 + 2 * s2 + 4 * s4


def hamming74_corrige(mot: str) -> str:
    """Corrige AU PLUS UNE erreur : inverse le bit à la position donnée par le syndrome (0 = rien à faire).

    d_min = 3 : DEUX erreurs ou plus produisent une correction FAUSSE — c'est la limite prouvée du code,
    le module ne prétend jamais corriger au-delà de ⌊(3−1)/2⌋ = 1 erreur."""
    mot = _exige_mot(mot, 7)
    pos = hamming74_syndrome(mot)
    if pos == 0:
        return mot
    b = list(mot)
    b[pos - 1] = "1" if b[pos - 1] == "0" else "0"
    return "".join(b)


def hamming74_extrait(mot: str) -> str:
    """Extrait les 4 bits de données (positions 3, 5, 6, 7) d'un CODEWORD valide.

    Syndrome ≠ 0 -> ValueError : on n'extrait JAMAIS des données d'un mot erroné (corriger d'abord)."""
    mot = _exige_mot(mot, 7)
    if hamming74_syndrome(mot) != 0:
        raise ValueError("mot erroné (syndrome non nul) : corriger avant d'extraire les données")
    return mot[2] + mot[4] + mot[5] + mot[6]


# ── (e) PARITÉ (convention parité PAIRE) ───────────────────────────────────────────────────────────────────────
def bit_parite(mot: str) -> str:
    """Bit de parité PAIRE : '1' si le poids de mot est impair, '0' sinon (mot + bit a un poids pair)."""
    mot = _exige_mot(mot)
    return "1" if mot.count("1") % 2 == 1 else "0"


def detecte_parite(mot: str) -> bool:
    """True ssi une erreur est DÉTECTÉE : poids IMPAIR sous la convention parité paire.

    La parité (d = 2) détecte toute erreur simple mais n'en corrige AUCUNE (et un nombre PAIR
    d'erreurs passe inaperçu — limite documentée du code)."""
    mot = _exige_mot(mot)
    return mot.count("1") % 2 == 1


# ── (f) BORNE DE SINGLETON ─────────────────────────────────────────────────────────────────────────────────────
def verifie_singleton(n: int, k: int, d: int) -> bool:
    """Borne de Singleton : True ssi d ≤ n − k + 1 (condition nécessaire d'existence d'un code (n,k,d))."""
    n = _exige_entier(n, 1, "longueur n")
    k = _exige_entier(k, 1, "dimension k")
    d = _exige_entier(d, 1, "distance d")
    if k > n:
        raise ValueError("dimension k > longueur n : paramètres de code impossibles")
    if d > n:
        raise ValueError("distance d > longueur n : paramètres de code impossibles")
    return d <= n - k + 1


def est_mds(n: int, k: int, d: int) -> bool:
    """True ssi il EXISTE un code BINAIRE (n, k, d) MDS (égalité de Singleton d = n − k + 1 ATTEINTE sur GF(2)).

    THÉORÈME (MacWilliams & Sloane, ch. 11, vrai même pour les codes non linéaires) : sur GF(2),
    les seuls codes MDS sont les familles triviales [n, n, 1], [n, n−1, 2] et [n, 1, n].
    L'égalité paramétrique d = n − k + 1 seule ne suffit donc PAS : est_mds(7, 4, 4) est False
    (le meilleur [7,4] binaire a d = 3). Si d > n − k + 1 (Singleton violée), aucun code binaire
    (n, k, d) n'existe -> ValueError (abstention)."""
    if not verifie_singleton(n, k, d):
        raise ValueError("borne de Singleton violée (d > n − k + 1) : aucun code binaire (n, k, d) n'existe")
    if d != n - k + 1:
        return False                                    # égalité de Singleton non atteinte : pas MDS
    # Égalité atteinte : MDS binaire ssi famille triviale (théorème, GF(2)).
    return (k == n and d == 1) or (k == n - 1 and d == 2) or (k == 1 and d == n)


# ── (g) BORNE DE HAMMING (empilement de sphères, binaire) ─────────────────────────────────────────────────────
def verifie_hamming(n: int, k: int, t: int) -> bool:
    """Borne de Hamming binaire : True ssi 2^k · Σ_{i=0}^{t} C(n, i) ≤ 2^n.

    Condition nécessaire pour qu'un code binaire (n, k) corrigeant t erreurs existe. t = 0 admis."""
    n = _exige_entier(n, 1, "longueur n")
    k = _exige_entier(k, 1, "dimension k")
    if not isinstance(t, int) or isinstance(t, bool) or t < 0:
        raise ValueError("capacité t invalide : un entier >= 0 est requis")
    if k > n:
        raise ValueError("dimension k > longueur n : paramètres de code impossibles")
    if t > n:
        raise ValueError("capacité t > longueur n : paramètres impossibles")
    volume_sphere = sum(math.comb(n, i) for i in range(t + 1))
    return (2 ** k) * volume_sphere <= 2 ** n
