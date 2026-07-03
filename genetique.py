"""
GÉNÉTIQUE MOLÉCULAIRE BORNÉE (mandat Yohan 2026-06-23 : « tous les domaines bornés, cités ou jamais »).

Domaine BORNÉ (cat PHYSIQUE/CONVENTION) : l'appariement des bases (A–T, G–C) et le CODE GÉNÉTIQUE STANDARD
(table NCBI n°1 : 64 codons -> acide aminé) sont des faits établis. À partir d'eux, des opérations sont
EXACTEMENT calculables :
  • complément d'un brin d'ADN (A↔T, G↔C) ;
  • transcription brin codant ADN -> ARNm (T -> U) ;
  • traduction ARNm/ADN -> protéine (codons -> acides aminés, * = STOP).

CE QUI EST BORNÉ (sound) : le MÉCANISME (appariement + table) est EXACT. La table est une DONNÉE sourcée
(code génétique standard NCBI table 1) ; même posture que `chimie`/`regle` (mécanisme garanti, contenu sourcé).

GARANTIES (vérifiées en adverse par `valide_genetique.py`) :
  - base invalide (hors A/C/G/T pour l'ADN, A/C/G/U pour l'ARN) -> (HORS, None) : jamais deviné ;
  - longueur non multiple de 3 pour la traduction -> (HORS, None) (pas de codon tronqué inventé) ;
  - codon inconnu -> (HORS, None) ; déterministe ; insensible à la casse en entrée (normalisée en majuscules).
"""
from __future__ import annotations

VERIFIE = "verifie"
HORS = "hors"

SOURCE = "appariement des bases + code génétique standard (NCBI table 1)"

# Code génétique standard (NCBI table 1), encodage canonique : codon = B1[i]+B2[i]+B3[i] (lettres ADN) -> AAs[i].
_AAS = "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"
_B1 = "TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG"
_B2 = "TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG"
_B3 = "TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG"
# table DNA-codon (3 lettres ADN) -> acide aminé (lettre, * = stop).
CODE = {_B1[i] + _B2[i] + _B3[i]: _AAS[i] for i in range(64)}

_COMPL = {"A": "T", "T": "A", "G": "C", "C": "G"}
STOP = "*"


def _norm(seq, alphabet) -> str | None:
    if not isinstance(seq, str):
        return None
    s = seq.strip().upper().replace(" ", "")
    if not s or any(c not in alphabet for c in s):
        return None
    return s


def complement_adn(adn: str) -> tuple[str, str | None]:
    """Brin complémentaire d'un ADN (A↔T, G↔C). (VERIFIE, seq) ou (HORS, None) si base invalide."""
    s = _norm(adn, "ACGT")
    if s is None:
        return (HORS, None)
    return (VERIFIE, "".join(_COMPL[c] for c in s))


def complement_inverse(adn: str) -> tuple[str, str | None]:
    """Brin complémentaire INVERSE (5'->3' de l'autre brin) = complément lu à l'envers."""
    st, c = complement_adn(adn)
    return (st, c[::-1] if c is not None else None)


def transcrit(adn_codant: str) -> tuple[str, str | None]:
    """Transcription du brin CODANT ADN -> ARNm (substitution T -> U). (VERIFIE, arn) ou (HORS, None)."""
    s = _norm(adn_codant, "ACGT")
    if s is None:
        return (HORS, None)
    return (VERIFIE, s.replace("T", "U"))


def codon_vers_aa(codon: str) -> tuple[str, str | None]:
    """Un codon (ADN ou ARN, 3 bases) -> acide aminé (lettre, * = stop). (HORS, None) si invalide/inconnu."""
    if not isinstance(codon, str):
        return (HORS, None)
    c = codon.strip().upper().replace(" ", "").replace("U", "T")
    if len(c) != 3 or any(b not in "ACGT" for b in c) or c not in CODE:
        return (HORS, None)
    return (VERIFIE, CODE[c])


def traduit(seq: str, *, arret_au_stop: bool = True) -> tuple[str, str | None]:
    """Traduit une séquence ARN ou ADN -> protéine (chaîne d'acides aminés 1-lettre).
    (VERIFIE, proteine) ou (HORS, None). Longueur non multiple de 3 -> HORS (pas de codon tronqué inventé).
    `arret_au_stop` : si True, s'arrête au premier codon STOP (exclu de la protéine) — convention biologique."""
    if not isinstance(seq, str):
        return (HORS, None)
    s = seq.strip().upper().replace(" ", "").replace("U", "T")
    if not s or len(s) % 3 != 0 or any(b not in "ACGT" for b in s):
        return (HORS, None)
    prot = []
    for i in range(0, len(s), 3):
        aa = CODE.get(s[i:i + 3])
        if aa is None:
            return (HORS, None)
        if aa == STOP:
            if arret_au_stop:
                return (VERIFIE, "".join(prot))
            prot.append(STOP)
        else:
            prot.append(aa)
    return (VERIFIE, "".join(prot))


# --- Gabarits NL SOUND : extraction VALIDÉE par le parseur (séquence invalide -> HORS, pas de NL fuzzy). ---
import re as _re
_NL_COMPL = _re.compile(r"compl[ée]ment(?:aire)?\s+(?:adn\s+)?(?:de\s+|d['’]\s*)?\b([ACGT]+)\b", _re.I)
_NL_TRAD = _re.compile(r"(?:tradui[ts]|traduire|protéine)\s+(?:l['’]?\s*)?(?:arn|adn)?\s*[:de]*\s*\b([ACGTU]+)\b", _re.I)


def repond_nl(texte: str):
    """(quoi, statut, valeur) pour « complément ADN de X » ou « traduis ARN X ». HORS si rien/invalide."""
    if not isinstance(texte, str):
        return ("aucun", HORS, None)
    m = _NL_COMPL.search(texte)
    if m:
        st, v = complement_adn(m.group(1))
        return ("complement", st, v)
    m = _NL_TRAD.search(texte)
    if m:
        st, v = traduit(m.group(1))
        return ("traduction", st, v)
    return ("aucun", HORS, None)


if __name__ == "__main__":
    print("complément ATGC ->", complement_adn("ATGC"))
    print("compl. inverse ATGC ->", complement_inverse("ATGC"))
    print("transcrit ATGC ->", transcrit("ATGC"))
    print("codon AUG ->", codon_vers_aa("AUG"), "| ATG ->", codon_vers_aa("ATG"), "| UAA ->", codon_vers_aa("UAA"))
    print("traduit AUGUUUUAA ->", traduit("AUGUUUUAA"))
    print("traduit (ADN) ATGGGATAA ->", traduit("ATGGGATAA"))
    print("invalide ATBX ->", complement_adn("ATBX"), "| len%3 AUGU ->", traduit("AUGU"))
    print("NL:", repond_nl("Quel est le complément ADN de ATGC ?"))
