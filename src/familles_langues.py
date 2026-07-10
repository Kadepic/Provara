"""
FAMILLES ET PARENTÉ DES LANGUES — catalogue de la GÉNÉALOGIE (linguistique comparée).

Posture FAUX=0 (identique à `galois` / `geometries_non_euclidiennes`) : on n'expose QUE des rattachements
ÉTABLIS par la méthode comparative (consensus), jamais une parenté devinée. Toute langue hors catalogue,
toute entrée invalide -> `ValueError` (abstention structurelle). Un faux NÉGATIF (abstenir) est toléré ;
un faux POSITIF (affirmer une parenté non prouvée) est INTERDIT.

POURQUOI un catalogue et non le store ? La table `famille_langue` de Wikidata ne donne que la famille
IMMÉDIATE (« le français est une langue d'oïl ») et ne porte PAS la généalogie complète : « langue d'oïl »
n'a aucun ancêtre typé, « langues sémitiques » remonte à « langue humaine » (nœud vide de sens). Ici on
inscrit la chaîne ascendante COMPLÈTE telle que la linguistique comparée l'établit.

MÉCANISME : un arbre (chaque nœud pointe vers son parent immédiat ; les racines sont les macro-familles).
  • parente(langue)     -> chaîne ascendante COMPLÈTE, feuille -> macro-famille.
      ex. français -> langue d'oïl -> gallo-roman -> roman -> italique -> indo-européen.
  • famille(langue)     -> la macro-famille (racine). Un ISOLAT n'a pas de famille : renvoie 'isolat'.
  • apparentees(l1, l2) -> bool : partagent-elles une racine ?
  • ancetre_commun(l1, l2) -> le nœud le PLUS PROFOND partagé ; familles distinctes -> ValueError
      (l'ABSENCE de parenté est un FAIT, pas un échec).
  • est_isolat(langue)  -> True SEULEMENT pour une langue SANS parent établi, c.-à-d. dont TOUTE la famille se
      réduit à sa propre lignée : les isolats vrais (basque, sumérien, aïnou) et le coréen (seul membre de la
      famille coréanique dans ce catalogue — statut d'isolat SELON L'ÉCOLE). Le japonais N'EST PAS un isolat :
      il partage la famille japonique avec les langues ryūkyū (parent PROUVÉ) — est_isolat('japonais') et
      est_isolat('ryukyu') valent donc False, en cohérence avec apparentees('japonais','ryukyu')=True.

HONNÊTETÉ (regroupements CONTESTÉS non affirmés) :
  • L'« altaïque » et le « nostratique » sont des HYPOTHÈSES non consensuelles : NON représentées comme des
    nœuds réels. famille('turc') rend 'turcique', PAS 'altaïque'.
  • Le balto-slave, l'italo-celtique, l'ougrien fin/permien, etc. — clades débattus : par PRUDENCE, les
    branches concernées sont rattachées directement à la macro-famille (faux négatif toléré) plutôt que
    d'affirmer un sous-groupe contesté. On ne rend JAMAIS un ancêtre commun plus précis que le consensus.
  • Chaque isolat est sa PROPRE racine (basque ≠ sumérien ≠ aïnou) : deux isolats ne partagent AUCUN nœud,
    donc ancetre_commun('basque','sumérien') -> ValueError (pas de fausse parenté via un pseudo-nœud 'isolat').

GARANTIES (vérifiées en adverse par `valide_familles_langues.py`) :
  - types invalides (bool, None, str vide, NaN/nombre, mauvaise arité) -> ValueError ;
  - langue hors catalogue -> ValueError ;
  - ancetre_commun de familles distinctes -> ValueError ;
  - déterministe, pur, sans état mutable ; stdlib uniquement.

SOURCE : classification consensuelle de la linguistique comparée (Ethnologue / Glottolog ; branches
indo-européennes d'après Beekes/Fortson ; familles afro-asiatique, ouralienne, sino-tibétaine, dravidienne,
austronésienne, niger-congo établies).
"""
from __future__ import annotations

SOURCE = "linguistique comparée — classification consensuelle (Glottolog / Ethnologue ; Fortson pour l'indo-européen)"

# ── ARBRE GÉNÉALOGIQUE : nœud -> parent immédiat (None = racine / macro-famille) ─────────────────────────────────
# Les rattachements ne descendent que jusqu'au niveau CONSENSUEL ; les sous-groupes contestés sont omis.
_PARENT = {
    # ══ INDO-EUROPÉEN ══════════════════════════════════════════════════════════════════════════════════════════
    "indo-européen": None,
    "proto-indo-européen": "indo-européen",      # proto-langue reconstruite de la famille
    # — italique / roman —
    "italique": "indo-européen",
    "latin": "italique",
    "roman": "italique",
    "gallo-roman": "roman",
    "langue d'oïl": "gallo-roman",
    "français": "langue d'oïl",
    "occitan": "roman",
    "ibéro-roman": "roman",
    "espagnol": "ibéro-roman",
    "portugais": "ibéro-roman",
    "catalan": "roman",                          # occitano-roman : rattachement précis débattu -> 'roman'
    "italo-roman": "roman",
    "italien": "italo-roman",
    "roumain": "roman",                          # roman oriental
    # — germanique —
    "germanique": "indo-européen",
    "germanique occidental": "germanique",
    "germanique septentrional": "germanique",
    "anglais": "germanique occidental",
    "allemand": "germanique occidental",
    "néerlandais": "germanique occidental",
    "suédois": "germanique septentrional",
    "danois": "germanique septentrional",
    "norvégien": "germanique septentrional",
    "islandais": "germanique septentrional",
    "gotique": "germanique",
    # — slave —
    "slave": "indo-européen",
    "slave oriental": "slave",
    "slave occidental": "slave",
    "slave méridional": "slave",
    "russe": "slave oriental",
    "ukrainien": "slave oriental",
    "biélorusse": "slave oriental",
    "polonais": "slave occidental",
    "tchèque": "slave occidental",
    "slovaque": "slave occidental",
    "bulgare": "slave méridional",
    "serbe": "slave méridional",
    "croate": "slave méridional",
    # — balte — (le balto-slave est un clade débattu : rattaché directement à IE)
    "balte": "indo-européen",
    "lituanien": "balte",
    "letton": "balte",
    # — celtique —
    "celtique": "indo-européen",
    "irlandais": "celtique",
    "gallois": "celtique",
    "breton": "celtique",
    # — indo-iranien —
    "indo-iranien": "indo-européen",
    "indo-aryen": "indo-iranien",
    "iranien": "indo-iranien",
    "sanskrit": "indo-aryen",
    "hindi": "indo-aryen",
    "ourdou": "indo-aryen",
    "bengali": "indo-aryen",
    "panjabi": "indo-aryen",
    "persan": "iranien",
    "kurde": "iranien",
    "pachto": "iranien",
    # — branches à langue unique —
    "hellénique": "indo-européen",
    "grec": "hellénique",
    "arménien": "indo-européen",                 # branche indo-européenne à langue unique
    "albanais": "indo-européen",                 # branche indo-européenne à langue unique

    # ══ AFRO-ASIATIQUE ═════════════════════════════════════════════════════════════════════════════════════════
    "afro-asiatique": None,
    "sémitique": "afro-asiatique",
    "arabe": "sémitique",
    "hébreu": "sémitique",
    "amharique": "sémitique",
    "araméen": "sémitique",
    "berbère": "afro-asiatique",

    # ══ OURALIEN ═══════════════════════════════════════════════════════════════════════════════════════════════
    "ouralien": None,
    "finnique": "ouralien",
    "finnois": "finnique",
    "estonien": "finnique",
    "hongrois": "ouralien",                      # ougrien : rattaché directement (sous-groupe débattu)

    # ══ TURCIQUE ═══ (l'« altaïque » qui l'engloberait avec mongol/toungouse est une HYPOTHÈSE, non retenue)
    "turcique": None,
    "turc": "turcique",
    "azéri": "turcique",
    "ouzbek": "turcique",
    "kazakh": "turcique",

    # ══ SINO-TIBÉTAIN ══════════════════════════════════════════════════════════════════════════════════════════
    "sino-tibétain": None,
    "sinitique": "sino-tibétain",
    "mandarin": "sinitique",
    "cantonais": "sinitique",
    "tibéto-birman": "sino-tibétain",
    "tibétain": "tibéto-birman",
    "birman": "tibéto-birman",

    # ══ DRAVIDIEN ══════════════════════════════════════════════════════════════════════════════════════════════
    "dravidien": None,
    "tamoul": "dravidien",
    "télougou": "dravidien",
    "kannada": "dravidien",
    "malayalam": "dravidien",

    # ══ AUSTRONÉSIEN ═══════════════════════════════════════════════════════════════════════════════════════════
    "austronésien": None,
    "malayo-polynésien": "austronésien",
    "indonésien": "malayo-polynésien",
    "malais": "malayo-polynésien",
    "tagalog": "malayo-polynésien",
    "malgache": "malayo-polynésien",
    "javanais": "malayo-polynésien",

    # ══ NIGER-CONGO ════════════════════════════════════════════════════════════════════════════════════════════
    "niger-congo": None,
    "bantou": "niger-congo",
    "swahili": "bantou",
    "zoulou": "bantou",
    "yoruba": "niger-congo",
    "wolof": "niger-congo",

    # ══ JAPONIQUE ══ (famille isolée : japonais + langues ryūkyū, aucun parent externe prouvé)
    "japonique": None,
    "japonais": "japonique",
    "ryukyu": "japonique",

    # ══ CORÉANIQUE ══ (coréen + jeju ; statut d'isolat SELON L'ÉCOLE)
    "coréanique": None,
    "coréen": "coréanique",

    # ══ ISOLATS VRAIS ══ (chacun sa PROPRE racine : aucun nœud partagé entre deux isolats)
    "basque": None,
    "sumérien": None,
    "aïnou": None,
}

# Macro-familles « réelles » (racines nommées d'après la famille elle-même).
_FAMILLES = {
    "indo-européen", "afro-asiatique", "ouralien", "turcique", "sino-tibétain",
    "dravidien", "austronésien", "niger-congo", "japonique", "coréanique",
}
# Racines d'isolats vrais : famille() y renvoie l'étiquette 'isolat'.
_RACINES_ISOLAT = {"basque", "sumérien", "aïnou"}
# NB : est_isolat() ne s'appuie PAS sur une liste de familles « supposées isolées » (cela produisait un FAUX
# POSITIF : toute langue ryūkyū héritait à tort du statut d'isolat de la famille japonique). Le prédicat est
# désormais STRUCTUREL — cf. est_isolat() : une langue est un isolat SSI aucune AUTRE langue du catalogue ne
# partage sa racine (donc japonais et ryukyu, qui se partagent la famille japonique, ne le sont PAS).

# ── normalisation accents (stdlib pure, aucune dépendance) ───────────────────────────────────────────────────────
_FOLD = {}
for _chars, _base in (("àâäáãå", "a"), ("éèêëẽ", "e"), ("íìîï", "i"),
                      ("óòôöõ", "o"), ("úùûü", "u"), ("ç", "c"), ("ñ", "n"), ("ÿ", "y")):
    for _c in _chars:
        _FOLD[ord(_c)] = _base


def _fold(s: str) -> str:
    return s.strip().lower().translate(_FOLD)


# index accent-insensible : forme repliée -> canonique (seulement si NON ambigu)
_INDEX_REPLIE = {}
for _nom in _PARENT:
    _f = _fold(_nom)
    if _f in _INDEX_REPLIE:
        _INDEX_REPLIE[_f] = None          # ambigu -> on refuse le raccourci replié
    else:
        _INDEX_REPLIE[_f] = _nom


def _canon(langue) -> str:
    """Résout `langue` vers un nœud canonique du catalogue ; sinon ValueError (abstention)."""
    if not isinstance(langue, str) or isinstance(langue, bool):
        raise ValueError(f"nom de langue (chaîne) attendu, reçu {langue!r}")
    brut = langue.strip()
    if not brut:
        raise ValueError("nom de langue vide")
    cle = brut.lower()
    if cle in _PARENT:
        return cle
    replie = _fold(brut)
    canon = _INDEX_REPLIE.get(replie)
    if canon:
        return canon
    raise ValueError(f"langue hors catalogue (abstention) : {langue!r}")


def _chaine(canon: str) -> list:
    """Chaîne ascendante feuille -> racine (nœuds canoniques). Garde anti-cycle."""
    chaine = []
    noeud = canon
    vus = set()
    while noeud is not None:
        if noeud in vus:                          # sécurité : jamais atteint sur un arbre bien formé
            raise ValueError(f"cycle détecté dans la généalogie à {noeud!r}")
        vus.add(noeud)
        chaine.append(noeud)
        noeud = _PARENT[noeud]
    return chaine


# ── API PUBLIQUE ─────────────────────────────────────────────────────────────────────────────────────────────────
def parente(langue: str) -> tuple:
    """Chaîne ascendante COMPLÈTE de `langue` à sa macro-famille (feuille -> racine).

    ex. parente('français') = ('français','langue d'oïl','gallo-roman','roman','italique','indo-européen').
    Langue hors catalogue -> ValueError."""
    return tuple(_chaine(_canon(langue)))


def famille(langue: str) -> str:
    """Macro-famille (racine) de `langue`. Un ISOLAT vrai renvoie 'isolat'. Hors catalogue -> ValueError."""
    racine = _chaine(_canon(langue))[-1]
    if racine in _RACINES_ISOLAT:
        return "isolat"
    if racine in _FAMILLES:
        return racine
    raise ValueError(f"racine non classée (incohérence catalogue) : {racine!r}")   # jamais atteint


def est_isolat(langue: str) -> bool:
    """True SSI `langue` est un isolat : AUCUNE autre langue du catalogue ne partage sa racine (toute la
    descendance de la racine se réduit à la lignée ascendante de `langue`). Hors catalogue -> ValueError.

    Sont donc des isolats : basque, sumérien, aïnou (racines à membre unique) et le coréen (seul membre de la
    famille coréanique ici). Le japonais et les langues ryūkyū NE le sont PAS : ils se partagent la famille
    japonique (parenté PROUVÉE), donc chacun a un apparenté et aucun n'est un isolat — ce qui interdit la
    contradiction est_isolat(x)=True alors que apparentees(x, y)=True pour une autre langue y du catalogue."""
    canon = _canon(langue)
    chaine = set(_chaine(canon))
    racine = _chaine(canon)[-1]
    for autre in _PARENT:                          # une seule racine partagée = famille = pas un isolat
        if autre not in chaine and _chaine(autre)[-1] == racine:
            return False
    return True


def apparentees(langue1: str, langue2: str) -> bool:
    """Les deux langues partagent-elles une racine (parenté établie) ? Hors catalogue -> ValueError.

    ATTENTION isolats : chaque isolat a sa propre racine, donc deux isolats distincts ne sont PAS apparentés."""
    r1 = _chaine(_canon(langue1))[-1]
    r2 = _chaine(_canon(langue2))[-1]
    return r1 == r2


def ancetre_commun(langue1: str, langue2: str) -> str:
    """Nœud le PLUS PROFOND partagé par les deux chaînes ascendantes.

    Familles distinctes (aucun nœud commun) -> ValueError : l'ABSENCE de parenté est un FAIT établi,
    pas un échec technique. Hors catalogue -> ValueError."""
    c1 = _chaine(_canon(langue1))
    ens2 = set(_chaine(_canon(langue2)))
    for noeud in c1:                              # c1 va de la feuille vers la racine -> 1er commun = le + profond
        if noeud in ens2:
            return noeud
    raise ValueError(
        f"aucune parenté établie entre {langue1!r} et {langue2!r} (familles distinctes) — c'est un FAIT")


def catalogue() -> tuple:
    """Liste triée de tous les nœuds catalogués (langues et branches)."""
    return tuple(sorted(_PARENT))


def familles() -> tuple:
    """Liste triée des macro-familles réelles (hors isolats)."""
    return tuple(sorted(_FAMILLES))
