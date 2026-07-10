"""
COMPRESSION SANS PERTE — garanties EXACTES du codage de source (Kraft, Huffman, tiroirs).

Même posture FAUX=0 que `geometries_non_euclidiennes` / `galois` (le théorème juge, jamais un faux) :
  • Le MÉCANISME est un ensemble de THÉORÈMES EXACTS, pas des heuristiques :
      – INÉGALITÉ DE KRAFT (Kraft 1949, McMillan 1956) : un code binaire PRÉFIXE de longueurs de mots
        l₁,…,l_n existe SI ET SEULEMENT SI  Σᵢ 2^(−lᵢ) ≤ 1.  La somme est calculée en `fractions.Fraction`
        (EXACTE, aucune erreur d'arrondi possible sur la comparaison à 1).
      – CODAGE DE HUFFMAN (Huffman 1952) : construction gloutonne par fusion des deux poids minimaux ;
        elle produit un code préfixe de longueur moyenne MINIMALE parmi tous les codes préfixes.
        Les ex æquo sont départagés par un ordre STABLE et DOCUMENTÉ (cf. `huffman`) : la construction
        est REPRODUCTIBLE au bit près (déterminisme exigé, sinon le code n'est pas un code).
      – THÉORÈME DU CODAGE DE SOURCE (Shannon 1948) : l'entropie H(X) borne toute longueur moyenne, et
        Huffman satisfait  H(X) ≤ L < H(X) + 1  (bits/symbole). `encadre_huffman` VÉRIFIE cet encadrement
        et lève RuntimeError s'il était violé — un invariant cassé n'est JAMAIS rendu comme résultat.
        L'entropie H est calculée par `information_calcul.entropie` (module réservé, chemin indépendant).
      – IMPOSSIBILITÉ UNIVERSELLE (principe des tiroirs, comptage exact) : il existe 2ⁿ messages de n bits
        mais seulement 2⁰+2¹+…+2^(n−1) = 2ⁿ − 1 chaînes binaires STRICTEMENT plus courtes ; aucune
        injection de l'un dans l'autre n'existe, donc TOUT compresseur sans perte envoie au moins un
        message de n bits vers une sortie de longueur ≥ n (il NE RACCOURCIT PAS ce message). Le comptage
        ne prouve PAS qu'un message grossit strictement : le compresseur IDENTITÉ est sans perte et ne
        fait grossir aucun message (contre-modèle exact). `compression_universelle_impossible` rend ce
        comptage chiffré, avec la clé honnête `au_moins_un_message_ne_raccourcit_pas`.
  • Les longueurs de mots et les comptages sont des ENTIERS EXACTS ; la somme de Kraft est une Fraction
    EXACTE. Seules l'entropie et la longueur moyenne sont des flottants (arrondis à 12 décimales, précision
    honnête héritée d'`information_calcul` ; les valeurs dyadiques tombent exactes).

GARANTIES (vérifiées en adverse par `valide_compression_sans_perte.py`) :
  - longueur de mot non entière, < 1, bool, NaN/inf, str  -> ValueError (Kraft est un théorème sur des
    entiers ≥ 1 ; on ne devine pas) ;
  - fréquence ≤ 0, bool, NaN/inf, str  -> ValueError ;
  - alphabet vide ou UN SEUL symbole -> ValueError explicite (un unique symbole donnerait un mot de
    longueur 0 : « compresser » vers le vide n'est pas un code, on s'abstient) ;
  - symboles non ordonnables entre eux -> ValueError (l'ordre stable du départage serait indéfini) ;
  - mot de code vide, caractère hors {0,1}, structure invalide -> ValueError ;
  - décodage : code non préfixe (ambigu) -> ValueError ; flux inachevé (suffixe qui n'est le début
    d'aucun mot complet) -> ValueError ; jamais un message deviné ;
  - encadrement de Shannon violé -> RuntimeError (invariant, pas un résultat) ;
  - fonctions PURES et déterministes ; conservateur (abstention tolérée, faux POSITIF interdit).

Le module n'importe que `math`, `heapq`, `fractions` (stdlib) et `information_calcul` (la BORNE, réservé).
"""
from __future__ import annotations

import heapq
import math
from fractions import Fraction

import information_calcul

SOURCE = ("inégalité de Kraft-McMillan (Kraft 1949, McMillan 1956) ; code de Huffman (Huffman 1952, "
          "« A Method for the Construction of Minimum-Redundancy Codes ») ; théorème du codage de source "
          "H ≤ L < H+1 (Shannon 1948) ; impossibilité universelle par principe des tiroirs (comptage exact)")

# Tolérance d'arrondi flottant sur la borne INFÉRIEURE de l'encadrement (cas d'égalité L = H atteint
# exactement pour les distributions dyadiques ; le théorème est exact, seul le flottant vacille).
_TOL_ENCADREMENT = 1e-9

# Borne de domaine pour le comptage des tiroirs : 2^n reste un entier exact mais on refuse les n
# déraisonnables (garde-fou mémoire, documenté ; la démonstration vaut pour tout n ≥ 1).
_N_MAX_TIROIRS = 10_000


# ── VALIDATION D'ENTRÉE ────────────────────────────────────────────────────────────────────────────────────────
def _est_entier(x) -> bool:
    """True ssi x est un entier authentique (bool REFUSÉ : True n'est pas 1)."""
    return isinstance(x, int) and not isinstance(x, bool)


def _exige_longueurs(longueurs) -> list:
    """Séquence non vide d'entiers ≥ 1 (longueurs de mots de code) ; sinon ValueError."""
    if not isinstance(longueurs, (list, tuple)) or len(longueurs) == 0:
        raise ValueError("longueurs invalides : une liste/tuple NON VIDE d'entiers >= 1 est requise")
    for l in longueurs:
        if not _est_entier(l) or l < 1:
            raise ValueError(f"longueur de mot invalide : {l!r} (un entier >= 1 est requis, "
                             "pas de bool/flottant/longueur nulle)")
    return list(longueurs)


def _exige_frequence(v) -> Fraction:
    """Fréquence/poids strictement positif (int, float fini ou Fraction) -> Fraction exacte ; sinon ValueError."""
    if isinstance(v, bool):
        raise ValueError("fréquence invalide : bool refusé (True n'est pas un poids)")
    if isinstance(v, float):
        if not math.isfinite(v):
            raise ValueError("fréquence invalide : NaN/inf refusés")
        f = Fraction(v)
    elif isinstance(v, (int, Fraction)):
        f = Fraction(v)
    else:
        raise ValueError(f"fréquence invalide : {v!r} (int, float fini ou Fraction requis)")
    if f <= 0:
        raise ValueError(f"fréquence invalide : {v!r} (strictement positive requise ; "
                         "un symbole de fréquence nulle n'a pas sa place dans le code)")
    return f


def _exige_frequences(frequences) -> dict:
    """Dict symbole -> Fraction > 0, AU MOINS DEUX symboles (un seul -> mot de longueur 0 -> abstention)."""
    if not isinstance(frequences, dict) or len(frequences) == 0:
        raise ValueError("fréquences invalides : un dict NON VIDE symbole -> fréquence est requis")
    if len(frequences) == 1:
        raise ValueError("un SEUL symbole : le code optimal aurait des mots de longueur 0 (flux vide, "
                         "indécodable en tant que code) ; abstention explicite")
    return {s: _exige_frequence(v) for s, v in frequences.items()}


def _exige_mot(mot) -> str:
    """Mot de code : chaîne binaire NON VIDE sur l'alphabet {0,1} ; sinon ValueError."""
    if not isinstance(mot, str) or len(mot) == 0:
        raise ValueError(f"mot de code invalide : {mot!r} (chaîne binaire non vide requise)")
    for c in mot:
        if c not in ("0", "1"):
            raise ValueError(f"mot de code invalide : {mot!r} (caractère {c!r} hors de l'alphabet {{0,1}})")
    return mot


def _exige_codes(codes) -> dict:
    """Dict symbole -> mot binaire valide, non vide ; sinon ValueError."""
    if not isinstance(codes, dict) or len(codes) == 0:
        raise ValueError("codes invalides : un dict NON VIDE symbole -> mot binaire est requis")
    return {s: _exige_mot(m) for s, m in codes.items()}


# ── (a) INÉGALITÉ DE KRAFT ─────────────────────────────────────────────────────────────────────────────────────
def kraft_somme(longueurs) -> Fraction:
    """Somme de Kraft  Σᵢ 2^(−lᵢ)  en Fraction EXACTE (aucun arrondi).

    Théorème de Kraft-McMillan : un code binaire PRÉFIXE de longueurs lᵢ existe ssi cette somme est ≤ 1.
    Longueur non entière, < 1, bool -> ValueError."""
    ls = _exige_longueurs(longueurs)
    return sum((Fraction(1, 2 ** l) for l in ls), Fraction(0))


def kraft_satisfaite(longueurs) -> bool:
    """True ssi Σ 2^(−lᵢ) ≤ 1 (comparaison EXACTE en Fraction) : un code préfixe de ces longueurs existe."""
    return kraft_somme(longueurs) <= 1


# ── (b) VÉRIFICATION PRÉFIXE (exhaustive) ──────────────────────────────────────────────────────────────────────
def est_prefixe(codes) -> bool:
    """True ssi AUCUN mot n'est préfixe d'un autre (vérification EXHAUSTIVE de toutes les paires).

    `codes` : dict symbole -> mot, ou liste/tuple de mots. Deux mots IDENTIQUES violent la propriété
    (chacun est préfixe de l'autre) -> False. Mot vide ou non binaire -> ValueError (mal formé, on ne
    juge pas un objet qui n'est pas un code)."""
    if isinstance(codes, dict):
        mots = list(codes.values())
    elif isinstance(codes, (list, tuple)):
        mots = list(codes)
    else:
        raise ValueError("codes invalides : dict symbole -> mot, ou liste/tuple de mots, requis")
    if len(mots) == 0:
        raise ValueError("codes invalides : au moins un mot est requis")
    mots = [_exige_mot(m) for m in mots]
    for i in range(len(mots)):
        for j in range(len(mots)):
            if i != j and mots[j].startswith(mots[i]):
                return False
    return True


# ── (c) HUFFMAN (construction déterministe) ────────────────────────────────────────────────────────────────────
def huffman(frequences) -> dict:
    """Code de Huffman : dict symbole -> mot binaire, longueur moyenne MINIMALE (Huffman 1952).

    Construction gloutonne : fusionner les deux nœuds de poids minimal jusqu'à l'arbre complet.
    DÉTERMINISME (ordre stable des ex æquo, documenté) :
      • les FEUILLES reçoivent un rang 0..n−1 dans l'ordre CROISSANT des symboles (`sorted`) ;
      • chaque nœud FUSIONNÉ reçoit le rang suivant (n, n+1, …) dans l'ordre de création ;
      • le tas ordonne par (poids exact en Fraction, rang) — à poids égal, le plus ancien rang sort d'abord ;
      • le premier nœud extrait reçoit le bit '0', le second le bit '1'.
    Deux appels sur les mêmes fréquences rendent donc EXACTEMENT le même code, bit à bit.
    Fréquence ≤ 0 / bool / NaN / inf -> ValueError ; un seul symbole -> ValueError explicite ;
    symboles mutuellement non ordonnables -> ValueError (l'ordre stable serait indéfini)."""
    freqs = _exige_frequences(frequences)
    try:
        symboles_tries = sorted(freqs.keys())
    except TypeError:
        raise ValueError("symboles non ordonnables entre eux : le départage stable des ex æquo est "
                         "indéfini (déterminisme impossible) ; abstention")
    codes = {s: "" for s in freqs}
    tas = [(freqs[s], rang, (s,)) for rang, s in enumerate(symboles_tries)]
    heapq.heapify(tas)
    rang_suivant = len(symboles_tries)
    while len(tas) > 1:
        poids0, _, groupe0 = heapq.heappop(tas)   # poids minimal (rang minimal si ex æquo) -> bit '0'
        poids1, _, groupe1 = heapq.heappop(tas)   # second minimal -> bit '1'
        for s in groupe0:
            codes[s] = "0" + codes[s]
        for s in groupe1:
            codes[s] = "1" + codes[s]
        heapq.heappush(tas, (poids0 + poids1, rang_suivant, groupe0 + groupe1))
        rang_suivant += 1
    return codes


def longueur_moyenne(codes, frequences) -> float:
    """Longueur moyenne pondérée  L = Σ fᵢ·|mot(i)| / Σ fᵢ  (bits/symbole).

    Calculée en Fraction EXACTE puis arrondie à 12 décimales (précision honnête ; les cas dyadiques
    tombent exacts). Les clés de `codes` et `frequences` doivent coïncider EXACTEMENT."""
    cs = _exige_codes(codes)
    if not isinstance(frequences, dict) or len(frequences) == 0:
        raise ValueError("fréquences invalides : un dict NON VIDE symbole -> fréquence est requis")
    fs = {s: _exige_frequence(v) for s, v in frequences.items()}
    if set(cs.keys()) != set(fs.keys()):
        raise ValueError("codes et fréquences incohérents : les ensembles de symboles diffèrent")
    total = sum(fs.values(), Fraction(0))
    pondere = sum((fs[s] * len(cs[s]) for s in fs), Fraction(0))
    return round(float(pondere / total), 12)


# ── (d) OPTIMALITÉ : ENCADREMENT DE SHANNON  H ≤ L < H+1 ──────────────────────────────────────────────────────
def encadre_huffman(frequences) -> tuple:
    """Construit le code de Huffman et VÉRIFIE l'encadrement du théorème du codage de source :
        H(X) ≤ L_Huffman < H(X) + 1   (bits/symbole).

    Renvoie (H, L) après vérification. H est calculée par `information_calcul.entropie` (chemin
    INDÉPENDANT, module réservé) sur les fréquences normalisées en probabilités exactes (Fraction).
    Si l'encadrement était violé -> RuntimeError (invariant du théorème cassé : on ne rend JAMAIS un
    résultat qui contredit le théorème). Tolérance flottante de 1e-9 sur la borne inférieure seulement
    (cas d'égalité L = H des distributions dyadiques)."""
    freqs = _exige_frequences(frequences)
    total = sum(freqs.values(), Fraction(0))
    probabilites = [float(freqs[s] / total) for s in freqs]
    h = information_calcul.entropie(probabilites)          # la BORNE, chemin indépendant
    codes = huffman(frequences)
    longueur = longueur_moyenne(codes, frequences)
    if not (h - _TOL_ENCADREMENT <= longueur < h + 1.0):
        raise RuntimeError(f"encadrement de Shannon VIOLÉ : H={h}, L={longueur} "
                           f"(attendu H <= L < H+1) — invariant du théorème cassé, résultat refusé")
    return (h, longueur)


# ── (e) IMPOSSIBILITÉ UNIVERSELLE (principe des tiroirs) ───────────────────────────────────────────────────────
def compression_universelle_impossible(n) -> dict:
    """Démonstration CHIFFRÉE (comptage exact) qu'aucun compresseur sans perte ne raccourcit TOUS
    les messages de n bits :
      • messages de n bits          : 2ⁿ ;
      • chaînes STRICTEMENT plus courtes (longueurs 0..n−1) : 2⁰+…+2^(n−1) = 2ⁿ − 1 ;
      • déficit : 1 -> par le principe des tiroirs, toute fonction sans perte (INJECTIVE) envoie au
        moins un message de n bits vers une chaîne de longueur ≥ n (il NE RACCOURCIT PAS : il grossit
        ou stagne). Le comptage ne prouve RIEN de plus : l'identité est un compresseur sans perte qui
        ne fait grossir aucun message — affirmer « au moins un grossit » serait un FAUX POSITIF.

    n : entier de 1 à 10 000 (_N_MAX_TIROIRS ; bool refusé). Renvoie le comptage exact (entiers)."""
    if not _est_entier(n) or n < 1:
        raise ValueError("n invalide : un entier >= 1 est requis (bool/flottant refusés)")
    if n > _N_MAX_TIROIRS:
        raise ValueError(f"n invalide : {n} > {_N_MAX_TIROIRS} (garde-fou de domaine documenté)")
    messages = 2 ** n
    plus_courts = 2 ** n - 1                     # somme géométrique 2^0 + ... + 2^(n-1), exacte
    return {
        "n": n,
        "messages_de_n_bits": messages,
        "messages_strictement_plus_courts": plus_courts,
        "deficit": messages - plus_courts,       # = 1 : le tiroir manquant
        # Exactement ce que le comptage prouve, RIEN DE PLUS : au moins un message reçoit une sortie
        # de longueur >= n. « Grossit strictement » serait faux (contre-modèle : l'identité).
        "au_moins_un_message_ne_raccourcit_pas": True,
    }


# ── (f) ENCODAGE / DÉCODAGE PRÉFIXE ────────────────────────────────────────────────────────────────────────────
def encode(codes, symboles) -> str:
    """Encode une séquence de symboles en flux binaire (concaténation des mots). Symbole inconnu -> ValueError."""
    cs = _exige_codes(codes)
    if not isinstance(symboles, (list, tuple, str)):
        raise ValueError("symboles invalides : liste/tuple/chaîne de symboles requis")
    morceaux = []
    for s in symboles:
        if s not in cs:
            raise ValueError(f"symbole inconnu du code : {s!r} (on n'invente pas de mot)")
        morceaux.append(cs[s])
    return "".join(morceaux)


def decode(codes, flux) -> list:
    """Décode un flux binaire avec un code PRÉFIXE. Renvoie la liste des symboles.

    Code non préfixe -> ValueError (décodage ambigu : on refuse plutôt que de choisir une lecture).
    Flux contenant un caractère hors {0,1} -> ValueError. Flux INACHEVÉ (suffixe restant qui n'est
    pas un mot complet) -> ValueError (message tronqué : on ne devine pas la fin). Flux vide -> []."""
    cs = _exige_codes(codes)
    if not est_prefixe(cs):
        raise ValueError("code NON PRÉFIXE : décodage ambigu, abstention (aucune lecture n'est prouvée)")
    if not isinstance(flux, str):
        raise ValueError("flux invalide : une chaîne binaire est requise")
    inverse = {mot: s for s, mot in cs.items()}
    resultat = []
    tampon = ""
    for c in flux:
        if c not in ("0", "1"):
            raise ValueError(f"flux invalide : caractère {c!r} hors de l'alphabet {{0,1}}")
        tampon += c
        if tampon in inverse:                    # unique possible : le code est préfixe
            resultat.append(inverse[tampon])
            tampon = ""
    if tampon:
        raise ValueError(f"flux inachevé : suffixe {tampon!r} sans mot de code complet (message tronqué)")
    return resultat
