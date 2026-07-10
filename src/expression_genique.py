"""
EXPRESSION GÉNIQUE — RÉPLICATION de l'ADN + orchestration du DOGME CENTRAL (réplication -> transcription
-> traduction). Domaine BORNÉ (cat PHYSIQUE/CONVENTION), même posture FAUX=0 que `genetique` et `chimie` :
la biologie moléculaire classique JUGE, jamais une devinette. Un fait vérifié, ou une abstention explicite
(ValueError). Le faux POSITIF est INTERDIT ; l'abstention (faux négatif) est tolérée.

MÉCANISMES (faits établis, EXACTS) :
  • RÉPLICATION : l'ADN est bicaténaire et ANTIPARALLÈLE (un brin 5'->3', l'autre 3'->5'). Le brin fille
    est le COMPLÉMENT (A↔T, G↔C) lu dans le sens 5'->3', c'est-à-dire le complément INVERSE (reverse
    complement) du brin parental. `replique` renvoie TOUJOURS le brin fille lu 5'->3'. Double application =
    identité : replique(replique(x)) == x (le complément inverse est une involution).
  • SEMI-CONSERVATIVE (Meselson & Stahl, 1958) : après UN cycle, CHAQUE duplex fille est HYBRIDE
    (1 brin parental conservé + 1 brin néosynthétisé). 100 % des duplex sont hybrides — PAS 50/50.
  • SENS DE SYNTHÈSE : l'ADN/ARN-polymérase synthétise TOUJOURS dans le sens 5'->3'. D'où, à la fourche,
    UN brin MENEUR (leading) synthétisé en CONTINU et UN brin RETARDÉ (lagging) synthétisé de façon
    DISCONTINUE en FRAGMENTS D'OKAZAKI. C'est un FAIT structurel : exactement un des deux brins est discontinu.
  • BRIN MATRICE / BRIN CODANT : l'ARNm a la séquence du brin CODANT (T remplacé par U) ; le brin MATRICE
    (template) est le complément du brin codant, lu 3'->5' (c'est lui que lit la polymérase).
  • DOGME CENTRAL : réplique/transcrit/traduit enchaînés, en RÉUTILISANT `genetique` (code génétique NCBI
    table 1) — jamais réimplémenté ici.

Le CODE GÉNÉTIQUE, `transcrit` et `traduit` viennent de `genetique` (importés, NON dupliqués).

ABSTENTION (ValueError) : base hors {A,C,G,T} (ADN) ou {A,C,G,U} (ARN) ; brin/chaîne vide ; type invalide
(bool, non-str, NaN...) ; longueur non multiple de 3 pour la traduction (aucun codon tronqué inventé).

GARANTIES vérifiées en adverse par `valide_expression_genique.py` (ancres NON circulaires : biologie
moléculaire classique + calcul à la main + boucle fermée reverse-complement involutive).
"""
from __future__ import annotations

from fractions import Fraction

import genetique
from genetique import VERIFIE, complement_adn, complement_inverse

SOURCE = (
    "réplication semi-conservative (Meselson & Stahl 1958) + appariement antiparallèle des bases + "
    "synthèse polymérase 5'->3' (fragments d'Okazaki) + code génétique NCBI table 1 (via genetique)"
)

# Sens IMMUABLE de la synthèse par la polymérase (fait de biologie moléculaire).
SENS = "5'->3'"

# Noms à 3 lettres des 20 acides aminés standard (1-lettre -> 3-lettres), pour nommer un peptide.
_AA3 = {
    "A": "Ala", "R": "Arg", "N": "Asn", "D": "Asp", "C": "Cys", "E": "Glu",
    "Q": "Gln", "G": "Gly", "H": "His", "I": "Ile", "L": "Leu", "K": "Lys",
    "M": "Met", "F": "Phe", "P": "Pro", "S": "Ser", "T": "Thr", "W": "Trp",
    "Y": "Tyr", "V": "Val",
}


# ── helpers d'abstention (convertissent le (HORS, None) de genetique en ValueError STRUCTURELLE) ─────────────
def _norm_arn(seq) -> str | None:
    """Normalise un ARNm sur l'alphabet {A,C,G,U}. None si type/base invalide ou vide (T INTERDIT en ARN)."""
    if not isinstance(seq, str):
        return None
    s = seq.strip().upper().replace(" ", "")
    if not s or any(c not in "ACGU" for c in s):
        return None
    return s


def _exige_arn(seq) -> str:
    s = _norm_arn(seq)
    if s is None:
        raise ValueError("ARNm invalide : chaîne non vide sur l'alphabet {A,C,G,U} requise (pas de T)")
    return s


# ── (a) RÉPLICATION : brin fille lu 5'->3' = complément inverse (reverse complement) ─────────────────────────
def replique(brin_adn: str) -> str:
    """Brin FILLE lu 5'->3' issu de `brin_adn` (parental, 5'->3').

    L'ADN étant ANTIPARALLÈLE, le brin fille est le COMPLÉMENT (A↔T, G↔C) lu 5'->3' = complément inverse.
    Ex. brin parental 5'-ATGC-3' -> brin fille 5'-GCAT-3'. Involutive : replique(replique(x)) == x.
    Base hors {A,C,G,T}, brin vide, type invalide -> ValueError (jamais deviné)."""
    st, fille = complement_inverse(brin_adn)
    if st != VERIFIE or fille is None:
        raise ValueError("brin d'ADN invalide : chaîne non vide sur l'alphabet {A,C,G,T} requise")
    return fille


def _norm_adn(brin: str) -> str:
    """Forme normalisée (majuscules, validée A/C/G/T) d'un brin d'ADN, via double complément inverse."""
    return replique(replique(brin))  # reverse-complement involutive -> brin d'origine normalisé


# ── (b) RÉPLICATION SEMI-CONSERVATIVE (Meselson & Stahl 1958) ────────────────────────────────────────────────
def semi_conservative(brin: str) -> dict:
    """Décrit les DEUX duplex filles d'une réplication semi-conservative de `brin` (5'->3').

    Chaque duplex = 1 brin PARENTAL conservé + 1 brin NÉOSYNTHÉTISÉ. FAIT de Meselson & Stahl (1958) :
    après UN cycle, 100 % des duplex sont HYBRIDES (jamais 50/50). Base/chaîne invalide -> ValueError."""
    brin1 = _norm_adn(brin)          # brin parental n°1 (5'->3'), normalisé
    brin2 = replique(brin1)          # brin parental n°2 = partenaire antiparallèle (5'->3')
    return {
        "modele": "semi-conservative",
        "source": "Meselson & Stahl, 1958",
        # duplex n°1 : brin parental n°1 conservé + copie néosynthétisée de son partenaire
        "duplex_1": {"parental": brin1, "neosynthetise": brin2},
        # duplex n°2 : brin parental n°2 conservé + copie néosynthétisée de brin1
        "duplex_2": {"parental": brin2, "neosynthetise": brin1},
        "fraction_hybride": Fraction(1, 1),  # 100 % : chaque duplex fille est hybride
        "commentaire": (
            "après 1 cycle : 100% des duplex sont HYBRIDES (1 brin parental + 1 brin neosynthetise), "
            "PAS 50/50"
        ),
    }


# ── (c) BRIN MATRICE (template) / BRIN CODANT depuis un ARNm ─────────────────────────────────────────────────
def brin_codant(arnm: str) -> str:
    """Brin CODANT (ADN, 5'->3') correspondant à un ARNm : U -> T (même séquence que l'ARNm).

    Ex. ARNm 5'-AUG-3' -> brin codant 5'-ATG-3'. Base hors {A,C,G,U}/vide/type invalide -> ValueError."""
    return _exige_arn(arnm).replace("U", "T")


def brin_matrice(arnm: str) -> str:
    """Brin MATRICE (template) lu 3'->5', complément du brin codant : c'est lui que lit la polymérase.

    Ex. ARNm 5'-AUG-3' -> brin codant 5'-ATG-3' -> brin matrice 3'-TAC-5' (complément, base à base).
    Orientation : la valeur renvoyée est alignée base-à-base avec le brin codant, donc lue 3'->5'.
    Base hors {A,C,G,U}/vide/type invalide -> ValueError."""
    codant = brin_codant(arnm)
    st, mat = complement_adn(codant)
    if st != VERIFIE or mat is None:  # défensif : codant est déjà validé, ne devrait jamais échouer
        raise ValueError("brin matrice indéterminable")
    return mat


# ── (d) SENS DE SYNTHÈSE + FRAGMENTS D'OKAZAKI ───────────────────────────────────────────────────────────────
def sens_synthese() -> str:
    """FAIT : « la polymérase synthétise TOUJOURS dans le sens 5'->3' »."""
    return "la polymérase synthétise TOUJOURS dans le sens " + SENS


def fragments_okazaki(brin: str) -> dict:
    """Identifie le brin DISCONTINU (retardé/lagging, en fragments d'Okazaki) à la fourche de réplication.

    Puisque la polymérase ne synthétise QUE 5'->3', exactement UN des deux nouveaux brins est CONTINU
    (meneur/leading) et l'AUTRE est DISCONTINU (retardé/lagging), fait de fragments d'Okazaki.
    Convention d'orientation : `brin` (5'->3') est pris comme matrice du brin MENEUR (lu 3'->5' par la
    fourche) ; le brin complémentaire est alors la matrice du brin RETARDÉ (discontinu).
    Base/chaîne invalide -> ValueError."""
    brin1 = _norm_adn(brin)          # matrice du brin meneur (convention)
    brin2 = replique(brin1)          # matrice du brin retardé (partenaire antiparallèle)
    return {
        "sens_polymerase": SENS,
        "brin_meneur_continu": {
            "matrice": brin1,
            "neosynthetise": brin2,
            "synthese": "continue",
        },
        "brin_retarde_discontinu": {
            "matrice": brin2,
            "neosynthetise": brin1,
            "synthese": "discontinue (fragments d'Okazaki)",
        },
        "reponse": (
            "le brin RETARDE (lagging) est discontinu : il est synthetise en fragments d'Okazaki, "
            "car la polymerase ne synthetise que " + SENS
        ),
    }


# ── (e) DOGME CENTRAL : réplication -> transcription -> traduction (réutilise genetique) ──────────────────────
def dogme_central(adn: str) -> dict:
    """Enchaîne réplication, transcription et traduction sur un brin CODANT `adn` (5'->3').

    Réutilise `genetique.transcrit` / `genetique.traduit` (code NCBI table 1). Renvoie le brin fille,
    l'ARNm, la protéine (1-lettre) et le peptide nommé (3-lettres, ex. 'Met-Ala'). La traduction s'arrête
    au premier codon STOP (exclu). Base invalide OU longueur non multiple de 3 -> ValueError."""
    st_t, arnm = genetique.transcrit(adn)
    if st_t != VERIFIE or arnm is None:
        raise ValueError("ADN invalide : chaîne non vide sur l'alphabet {A,C,G,T} requise")
    adn_norm = arnm.replace("U", "T")  # brin codant normalisé (majuscules, validé)

    st_p, prot = genetique.traduit(adn_norm, arret_au_stop=True)
    if st_p != VERIFIE or prot is None:
        raise ValueError("longueur non multiple de 3 (ou codon inconnu) : aucun codon tronqué inventé")

    # STOP rencontré ? (traduction complète, sans arrêt, contient '*' ssi un codon stop existe)
    st_f, full = genetique.traduit(adn_norm, arret_au_stop=False)
    stop_rencontre = bool(full) and "*" in full

    peptide = "-".join(_AA3[a] for a in prot)  # prot ne contient que des AA (STOP déjà exclu)
    return {
        "adn_codant": adn_norm,
        "brin_fille_5_3": replique(adn_norm),
        "arnm": arnm,
        "proteine_1lettre": prot,
        "peptide": peptide,
        "stop_rencontre": stop_rencontre,
    }


if __name__ == "__main__":
    print("replique ATGC ->", replique("ATGC"))
    print("involution replique(replique(GATTACA)) ->", replique(replique("GATTACA")))
    print("semi_conservative ATGC ->", semi_conservative("ATGC"))
    print("brin_codant AUG ->", brin_codant("AUG"), "| brin_matrice AUG ->", brin_matrice("AUG"))
    print("sens_synthese ->", sens_synthese())
    print("fragments_okazaki ATGC ->", fragments_okazaki("ATGC")["reponse"])
    print("dogme_central ATGGCTTAA ->", dogme_central("ATGGCTTAA"))
