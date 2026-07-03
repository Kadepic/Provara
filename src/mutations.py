"""
MUTATIONS — classification de mutations de l'ADN + effet d'une substitution sur la traduction.

Domaine BORNÉ (cat PHYSIQUE/CONVENTION) : à partir de deux séquences (référence / mutée) le TYPE
de mutation est EXACTEMENT déterminé par la longueur et le nombre de différences ; l'effet d'une
substitution dans un codon est EXACTEMENT déterminé par le CODE GÉNÉTIQUE STANDARD (NCBI table 1),
réutilisé tel quel depuis `genetique` (même table, même posture « mécanisme garanti, contenu sourcé »).

POSTURE FAUX=0 : abstention (ValueError) sur toute entrée invalide OU ambiguë — JAMAIS un faux.
  • séquence/codon non-ADN (hors A/C/G/T) -> ValueError ;
  • codon de longueur != 3 -> ValueError ;
  • séquence vide ou non-str -> ValueError ;
  • type_mutation : même longueur sans différence (pas de mutation) OU >1 différence (multi-changements
    ambigus, ni substitution simple ni indel) -> ValueError (abstention, on ne devine pas) ;
  • effet_substitution_codon : codon de référence STOP -> ValueError (read-through hors des 3 catégories
    standard silencieuse/faux-sens/non-sens : on s'abstient plutôt que d'étiqueter à tort).

DÉFINITIONS (textbook) :
  - type_mutation(ref, mut) :
        'substitution' si len(ref) == len(mut) et EXACTEMENT 1 base diffère ;
        'insertion'    si len(mut)  > len(ref) ;
        'deletion'     si len(mut)  < len(ref).
  - effet_substitution_codon(codon_ref, codon_mut) — par TRADUCTION des deux codons :
        'silencieuse' (synonyme) si même acide aminé ;
        'non_sens'    (nonsense) si le codon muté est STOP (et le codon de réf. code un acide aminé) ;
        'faux_sens'   (missense) si acides aminés différents et codon muté non-STOP.

Déterministe, insensible à la casse et aux espaces en entrée (normalisées en majuscules).
"""
from __future__ import annotations

SUBSTITUTION = "substitution"
INSERTION = "insertion"
DELETION = "deletion"

SILENCIEUSE = "silencieuse"
FAUX_SENS = "faux_sens"
NON_SENS = "non_sens"

STOP = "*"
_BASES = "ACGT"

# Réutilise le CODE GÉNÉTIQUE STANDARD de `genetique` si disponible ; sinon table interne identique
# (NCBI table 1, codon ADN -> acide aminé 1-lettre, * = STOP). Aucun « contenu » inventé.
try:  # pragma: no cover - chemin nominal
    import genetique as _genetique
    _CODE = dict(_genetique.CODE)
except Exception:  # pragma: no cover - repli autonome
    _genetique = None
    _AAS = "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"
    _B1 = "TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG"
    _B2 = "TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG"
    _B3 = "TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG"
    _CODE = {_B1[i] + _B2[i] + _B3[i]: _AAS[i] for i in range(64)}


def _norm_seq(seq) -> str:
    """Normalise une séquence ADN (majuscules, espaces retirés). ValueError si non-str/vide/hors ACGT."""
    if not isinstance(seq, str):
        raise ValueError(f"séquence non-str : {type(seq).__name__}")
    s = seq.strip().upper().replace(" ", "")
    if not s:
        raise ValueError("séquence vide")
    bad = {c for c in s if c not in _BASES}
    if bad:
        raise ValueError(f"séquence non-ADN (bases hors ACGT : {sorted(bad)})")
    return s


def _norm_codon(codon) -> str:
    """Normalise un codon ADN (3 bases ACGT). ValueError si non-str/longueur!=3/hors ACGT."""
    if not isinstance(codon, str):
        raise ValueError(f"codon non-str : {type(codon).__name__}")
    c = codon.strip().upper().replace(" ", "")
    if len(c) != 3:
        raise ValueError(f"codon de longueur {len(c)} != 3")
    bad = {b for b in c if b not in _BASES}
    if bad:
        raise ValueError(f"codon non-ADN (bases hors ACGT : {sorted(bad)})")
    return c


def _aa_du_codon(codon: str) -> str:
    """Acide aminé (1-lettre, * = STOP) du codon ADN normalisé via le code standard."""
    return _CODE[codon]


def type_mutation(seq_ref, seq_mut) -> str:
    """Classe le type d'une mutation à partir des séquences ADN de référence et mutée.

    Renvoie 'substitution' (même longueur, exactement 1 base différente),
    'insertion' (séquence mutée plus longue) ou 'deletion' (séquence mutée plus courte).
    ValueError si : base non-ADN, séquence vide/non-str, OU même longueur avec 0 différence
    (pas de mutation) ou >1 différence (multi-changements ambigus) -> abstention FAUX=0."""
    r = _norm_seq(seq_ref)
    m = _norm_seq(seq_mut)
    if len(m) > len(r):
        return INSERTION
    if len(m) < len(r):
        return DELETION
    # même longueur : compter les différences.
    diff = sum(1 for a, b in zip(r, m) if a != b)
    if diff == 1:
        return SUBSTITUTION
    if diff == 0:
        raise ValueError("séquences identiques : aucune mutation (abstention)")
    raise ValueError(f"même longueur mais {diff} différences : multi-substitution ambiguë (abstention)")


def effet_substitution_codon(codon_ref, codon_mut) -> str:
    """Effet sur la traduction d'une substitution remplaçant codon_ref par codon_mut.

    Renvoie 'silencieuse' (même acide aminé), 'faux_sens' (acide aminé différent, non-STOP)
    ou 'non_sens' (codon muté STOP). ValueError si : codon non-ADN, longueur != 3, OU codon de
    référence STOP (read-through hors des 3 catégories -> abstention FAUX=0)."""
    cr = _norm_codon(codon_ref)
    cm = _norm_codon(codon_mut)
    aa_ref = _aa_du_codon(cr)
    aa_mut = _aa_du_codon(cm)
    if aa_ref == STOP:
        raise ValueError("codon de référence STOP : classification non standard (abstention)")
    if aa_mut == STOP:
        return NON_SENS
    if aa_mut == aa_ref:
        return SILENCIEUSE
    return FAUX_SENS


def decrit_substitution(codon_ref, codon_mut) -> tuple[str, str, str]:
    """(effet, aa_ref, aa_mut) pour une substitution de codon. Mêmes garanties/abstentions que
    effet_substitution_codon. aa = lettre d'acide aminé, '*' pour un codon STOP muté."""
    cr = _norm_codon(codon_ref)
    cm = _norm_codon(codon_mut)
    effet = effet_substitution_codon(cr, cm)
    return (effet, _aa_du_codon(cr), _aa_du_codon(cm))


if __name__ == "__main__":
    print("type ATG->ATA :", type_mutation("ATG", "ATA"))
    print("type ATG->ATGG:", type_mutation("ATG", "ATGG"))
    print("type ATGG->ATG:", type_mutation("ATGG", "ATG"))
    print("effet ATG->ATG :", effet_substitution_codon("ATG", "ATG"))
    print("effet ATG->ATA :", effet_substitution_codon("ATG", "ATA"))
    print("effet TAC->TAA :", effet_substitution_codon("TAC", "TAA"))
    print("décrit TAC->TAA:", decrit_substitution("TAC", "TAA"))
