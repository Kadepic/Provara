"""
MÉTRIQUE ET VERSIFICATION FRANÇAISES — convention CLASSIQUE, nommée (PARTIE VIII, B-CONV).

Le sujet est BORNÉ par CONVENTION : la métrique classique française est un système de règles publiées, pas
une opinion. Mais deux de ses règles sont, dans la langue elle-même, AMBIGUËS — et c'est là que se joue le
FAUX=0 de ce module.

CE QUI EST DÉTERMINÉ (compté exactement) :
  • Une syllabe par GROUPE DE VOYELLES. Les digrammes (ai, ei, au, eau, ou, oi, eu, œu, ui…) font UNE voyelle.
  • ÉLISION du « e » final d'un mot devant une voyelle ou un « h » muet, et devant la fin du vers.
    Un mot dont le « e » est l'UNIQUE voyelle (« ce », « le », « je ») ne s'élide jamais par cette règle :
    l'orthographe l'aurait déjà écrit avec une apostrophe.
  • Le « e » final du DERNIER mot du vers est toujours muet (il ne compte pas).

CE QUI NE L'EST PAS, ET QU'ON REFUSE DE TRANCHER (le cœur du module) :
  • La SYNÉRÈSE et la DIÉRÈSE. « lion », « hier », « nuage » valent UNE ou DEUX syllabes selon le poète et
    selon le vers. Aucune règle orthographique ne le décide. Le module rend donc un INTERVALLE (min, max),
    jamais un nombre unique inventé, et `est_alexandrin` rend `'indéterminé'` quand 12 est DANS l'intervalle
    sans y être forcé. Rendre « 12 » là où le vers peut valoir 11 ou 12 serait précisément le faux que ce
    module existe pour empêcher.
  • La finale « -ent ». Elle est MUETTE quand c'est la désinence verbale de 3ᵉ personne du pluriel
    (« ils chantent » = 2 syllabes) et SONORE partout ailleurs (« souvent » = 2 syllabes). L'orthographe
    seule ne les distingue pas : « chantent » et « souvent » ont la même finale. Une première version de ce
    module appliquait la règle verbale à tous les mots, et comptait 11 syllabes à l'alexandrin de Verlaine
    « Je fais souvent ce rêve étrange et pénétrant ». Le compte est donc AMBIGU par défaut (mini = muette,
    maxi = sonore), sauf pour la liste fermée `_ENT_SONORE` des mots non verbaux courants, où il est certain.
    Élargir cette liste rend le module plus précis ; inventer une règle morphologique le rendrait FAUX.
  • Les RIMES sont analysées sur l'ORTHOGRAPHE, pas sur la phonétique (aucun dictionnaire phonétique n'est
    embarqué). `type_rime` le DIT dans sa docstring et dans sa valeur de retour : c'est une approximation
    orthographique, utilisable pour « pauvre / suffisante / riche » sur des finales régulières, et rien de plus.

GARANTIES (vérifiées en adverse par `valide_versification_fr.py`) :
  - vers vide, ou sans aucune voyelle -> ValueError ;
  - entrée non-str, bool, None -> ValueError ;
  - `hemistiche` sur un vers qui n'est pas un alexandrin certain -> ValueError (on ne coupe pas au hasard) ;
  - `nom_metre` d'un compte hors catalogue -> ValueError ;
  - `schema_rimes` sur moins de 2 vers, ou un schéma non reconnu -> ValueError ;
  - déterministe, pur, stdlib seule (`unicodedata`, `re`).

Toutes les fonctions sont PURES et déterministes.
"""
from __future__ import annotations

import re
import unicodedata

SOURCE = ("métrique française classique (traité de versification : compte syllabique, élision du e muet, "
          "diérèse/synérèse laissées indéterminées)")

VOYELLES = "aeiouyàâäéèêëîïôöùûüÿœæ"

# Digrammes/trigrammes qui valent UNE voyelle : ils ne créent jamais d'ambiguïté de diérèse.
_SOUDES = ("eau", "œu", "ai", "ei", "au", "ou", "oi", "eu", "ui", "an", "en", "in", "on", "un")

# Groupes AMBIGUS (synérèse ou diérèse) : i/u/ou suivis d'une autre voyelle. « ui » est EXCLU : il est
# toujours monosyllabique en usage classique (« nuit », « lui »). Le doute porte sur « lion », « hier »,
# « nuage », « jouer », « viande ».
# « ui » est EXCLU de la classe : la classe de u NE contient PAS « i » (« nuit », « lui » = 1 syllabe).
_AMBIGU = re.compile(r"(?:ou[aeiy]|i[aeouy]|u[aeoy])")

_METRES = {12: "alexandrin", 10: "décasyllabe", 8: "octosyllabe", 7: "heptasyllabe",
           6: "hexasyllabe", 5: "pentasyllabe", 4: "tétrasyllabe"}

_H_MUET_EXCEPTIONS = ("héros", "hérisson", "hasard", "haine", "haut", "honte", "hibou")

# Mots NON VERBAUX finissant par « -ent » : leur finale est SONORE, sans ambiguïté. Liste fermée et sourcée
# (lexique courant). Hors de cette liste, une finale « -ent » est traitée comme AMBIGUË (voir la docstring).
_ENT_SONORE = frozenset((
    "souvent", "vent", "cent", "dent", "lent", "argent", "moment", "comment", "accent", "sergent",
    "serpent", "parent", "client", "patient", "orient", "occident", "ciment", "torrent", "présent",
    "absent", "content", "violent", "évident", "urgent", "agent", "talent", "aliment",
    "instrument", "gouvernement", "sentiment", "mouvement", "changement", "événement", "document",
))


def _exige_texte(x, nom: str = "vers") -> str:
    if isinstance(x, bool) or not isinstance(x, str):
        raise ValueError("%s invalide : une chaîne de caractères est requise" % nom)
    t = x.strip()
    if not t:
        raise ValueError("%s vide" % nom)
    return t


def _sans_accents(mot: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", mot) if unicodedata.category(c) != "Mn")


def _mots(vers: str) -> list:
    """Découpe en mots, en RÉSOLVANT l'élision orthographique (« l'aube » -> « aube »)."""
    t = vers.lower().replace("’", "'")
    t = re.sub(r"\b\w+'", " ", t)                      # « l' », « d' », « qu' » : la voyelle est déjà tombée
    t = re.sub(r"[^%s\w\s-]" % VOYELLES, " ", t)
    mots = [m for m in re.split(r"[\s-]+", t) if m]
    if not mots:
        raise ValueError("vers sans mot exploitable")
    return mots


def _groupes_voyelles(mot: str) -> list:
    """Les groupes de voyelles du mot, dans l'ordre. « campagne » -> ['a', 'a', 'e']."""
    return re.findall(r"[%s]+" % VOYELLES, mot)


def _commence_par_voyelle(mot: str) -> bool:
    m = _sans_accents(mot)
    if not m:
        return False
    if m[0] == "h":
        return not any(m.startswith(_sans_accents(h)) for h in _H_MUET_EXCEPTIONS)
    return m[0] in "aeiouy"


def _syllabes_mot(mot: str, dernier: bool, suivant: str | None) -> tuple:
    """(min, max) de syllabes pour un mot, dans son contexte. min = toutes les élisions/synérèses.

    Trois sources de variation, traitées séparément :
      • « e » / « -es » final : MUET devant voyelle ou en fin de vers (certain) ;
      • « -ent » final : muet si désinence verbale, sonore sinon — AMBIGU hors de `_ENT_SONORE` ;
      • groupes i/u/ou + voyelle : synérèse (1) ou diérèse (2) — AMBIGU."""
    groupes = _groupes_voyelles(mot)
    n = len(groupes)
    if n == 0:
        return (0, 0)
    mini = maxi = n

    if mot.endswith("ent") and n >= 2:
        if mot in _ENT_SONORE:
            pass                                        # « souvent » : la finale compte, sans ambiguïté
        else:
            mini -= 1                                   # désinence verbale possible -> peut être muette
    elif n >= 2 and (mot.endswith("e") or mot.endswith("es")):
        # « ce », « je » ont un seul groupe : jamais élidés par cette règle (l'apostrophe l'aurait dit).
        if dernier or (suivant is not None and _commence_par_voyelle(suivant)):
            mini -= 1
            maxi -= 1                                   # certain : le « e » ne compte pas

    ambigus = len(_AMBIGU.findall(_sans_accents(mot)))
    return (mini, maxi + ambigus)


def compte_syllabes(vers: str) -> tuple:
    """Compte syllabique CLASSIQUE d'un vers -> (minimum, maximum).

    Le minimum suppose partout la synérèse et la finale « -ent » muette ; le maximum, partout la diérèse et
    la finale « -ent » sonore. Quand min == max, le compte est CERTAIN. Quand min < max, le vers contient au
    moins une ambiguïté que la langue elle-même ne tranche pas — et le module ne la tranche pas non plus."""
    vers = _exige_texte(vers)
    mots = _mots(vers)
    if not any(_groupes_voyelles(m) for m in mots):
        raise ValueError("vers sans voyelle : aucune syllabe à compter")

    mini = maxi = 0
    for i, mot in enumerate(mots):
        dernier = (i == len(mots) - 1)
        suivant = mots[i + 1] if not dernier else None
        a, b = _syllabes_mot(mot, dernier, suivant)
        mini += a
        maxi += b
    if mini < 1:
        raise ValueError("compte syllabique nul : vers non métrique")
    return (mini, maxi)


def est_alexandrin(vers: str):
    """True / False / 'indéterminé'. L'indétermination est une RÉPONSE, pas un échec."""
    mini, maxi = compte_syllabes(vers)
    if mini == maxi:
        return mini == 12
    if mini <= 12 <= maxi:
        return "indéterminé"
    return False


def nom_metre(n: int) -> str:
    """Nom du mètre pour un compte syllabique donné. Hors catalogue -> ValueError."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError("compte syllabique : entier requis")
    if n not in _METRES:
        raise ValueError("mètre hors catalogue : %d syllabes (connus : %s)"
                         % (n, sorted(_METRES)))
    return _METRES[n]


def hemistiche(vers: str) -> tuple:
    """Les deux hémistiches d'un ALEXANDRIN certain, coupés à la 6ᵉ syllabe.

    Un vers dont le compte est indéterminé n'a pas de césure calculable : ValueError (on ne coupe pas au
    hasard un vers qu'on n'a pas su compter)."""
    if est_alexandrin(vers) is not True:
        raise ValueError("césure indéfinie : ce vers n'est pas un alexandrin CERTAIN "
                         "(compte %s)" % (compte_syllabes(vers),))
    mots = _mots(vers)
    cumul = 0
    for i, mot in enumerate(mots):
        dernier = (i == len(mots) - 1)
        suivant = mots[i + 1] if not dernier else None
        a, b = _syllabes_mot(mot, dernier, suivant)
        if a != b:
            raise ValueError("césure indéfinie : ambiguïté syllabique dans « %s »" % mot)
        cumul += a
        if cumul == 6:
            return (" ".join(mots[:i + 1]), " ".join(mots[i + 1:]))
        if cumul > 6:
            raise ValueError("césure à la 6ᵉ syllabe tombant à l'intérieur d'un mot : "
                             "césure lyrique, hors du périmètre classique")
    raise ValueError("césure introuvable")


def genre_rime(mot: str) -> str:
    """'féminine' si le mot finit par un « e » muet (ou -es, -ent), 'masculine' sinon."""
    m = _exige_texte(mot, "mot").lower()
    if not _groupes_voyelles(m):
        raise ValueError("mot sans voyelle")
    return "féminine" if (m.endswith("e") or m.endswith("es") or m.endswith("ent")) else "masculine"


def type_rime(mot1: str, mot2: str) -> str:
    """'pauvre' (1 lettre commune en finale), 'suffisante' (2), 'riche' (3 et plus).

    APPROXIMATION ORTHOGRAPHIQUE assumée : la richesse d'une rime se mesure en PHONÈMES, et aucun
    dictionnaire phonétique n'est embarqué. Deux mots sans finale commune -> ValueError (ils ne riment pas :
    on ne rend pas « pauvre » pour une non-rime)."""
    a = _sans_accents(_exige_texte(mot1, "mot1").lower())
    b = _sans_accents(_exige_texte(mot2, "mot2").lower())
    commun = 0
    for x, y in zip(reversed(a), reversed(b)):
        if x != y:
            break
        commun += 1
    if commun == 0:
        raise ValueError("ces deux mots n'ont aucune finale commune : ils ne riment pas")
    return "pauvre" if commun == 1 else ("suffisante" if commun == 2 else "riche")


def schema_rimes(vers_list) -> str:
    """'AABB' (plates), 'ABAB' (croisées), 'ABBA' (embrassées) pour un QUATRAIN.

    Deux vers riment si leurs derniers mots partagent au moins 2 lettres finales (rime suffisante).
    Un agencement non reconnu -> ValueError (on ne baptise pas un schéma qui n'en est pas un)."""
    if not isinstance(vers_list, (list, tuple)) or len(vers_list) != 4:
        raise ValueError("schéma de rimes : exactement 4 vers (quatrain) sont requis")
    finales = []
    for v in vers_list:
        mots = _mots(_exige_texte(v))
        finales.append(_sans_accents(mots[-1]))

    def rime(i, j) -> bool:
        a, b = finales[i], finales[j]
        n = 0
        for x, y in zip(reversed(a), reversed(b)):
            if x != y:
                break
            n += 1
        return n >= 2

    if rime(0, 1) and rime(2, 3) and not rime(1, 2):
        return "AABB"
    if rime(0, 2) and rime(1, 3) and not rime(0, 1):
        return "ABAB"
    if rime(0, 3) and rime(1, 2) and not rime(0, 1):
        return "ABBA"
    raise ValueError("schéma de rimes non reconnu (ni plates, ni croisées, ni embrassées)")
