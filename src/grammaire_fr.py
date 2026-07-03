# -*- coding: utf-8 -*-
"""GRAMMAIRE FRANÇAISE — analyse de phrase directement appelable, FAUX=0 (2026-07-03).

POURQUOI (mandat Yohan « l'IA doit converser vraiment, pas au ras des pâquerettes ») : comprendre une phrase, ce
n'est pas la reconnaître par motif — c'est en lire la STRUCTURE. Ce module étiquette chaque mot par sa CLASSE
grammaticale (nature) et en déduit le TYPE de phrase (question / affirmation / ordre) et une structure
sujet-verbe-objet. Model-free, déterministe, souverain.

FONDATION FAUX=0 : les mots-OUTILS (déterminants, pronoms, prépositions, conjonctions, interrogatifs, auxiliaires,
négation) forment un ensemble FINI et FERMÉ du français — on les énumère exactement (aucune supposition). Les mots
PLEINS (noms/verbes/adjectifs) sont reconnus par le lexique certifié `lexique_fr`, puis, à défaut, par une
morphologie BORNÉE (terminaisons régulières) qui rend « inconnu » plutôt que de deviner faux. La classe d'un mot
ambigu hors mots-outils n'est jamais inventée : au doute -> 'inconnu' (honnête).
"""
from __future__ import annotations

import re

try:
    from base_faits import normalise as _normalise
except Exception:
    def _normalise(s):
        import unicodedata
        s = unicodedata.normalize("NFD", str(s).lower())
        return "".join(c for c in s if unicodedata.category(c) != "Mn")

# ————————————————————————— MOTS-OUTILS : ensembles FERMÉS et FINIS du français (FAUX=0) —————————————————————————
_DETERMINANTS = set("le la les l un une des du de d au aux ce cet cette ces mon ton son ma ta sa mes tes ses "
                    "notre votre leur nos vos leurs quel quelle quels quelles chaque plusieurs quelque quelques "
                    "tout toute tous toutes aucun aucune certain certains certaine certaines".split())
_PRONOMS = set("je j tu il elle on nous vous ils elles me te se lui leur moi toi soi eux y en "
               "ceci cela ca celui celle ceux celles celui-ci celle-la qui que quoi dont ou lequel laquelle "
               "lesquels lesquelles rien personne tout chacun chacune quelqu quelque-chose".split())
_PREPOSITIONS = set("a de en dans sur sous vers avec sans pour par chez entre depuis pendant avant apres contre "
                    "selon malgre parmi hormis outre envers derriere devant pres loin jusque jusqu des-lors "
                    "au-dela au-dessus au-dessous grace-a a-cause-de afin-de".split())
_CONJONCTIONS = set("et ou mais donc or ni car que quand comme si lorsque puisque quoique bien-que "
                    "afin-que parce-que tandis-que alors-que".split())
_INTERROGATIFS = set("qui que quoi quel quelle quels quelles ou quand comment combien pourquoi "
                     "lequel laquelle lesquels lesquelles est-ce".split())
_AUXILIAIRES = set("suis es est sommes etes sont etais etait etions etiez etaient serai seras sera serons serez "
                   "seront serais serait fus fut furent sois soit soyons soyez soient "
                   "ai as a avons avez ont avais avait avions aviez avaient aurai auras aura aurons aurez auront "
                   "aurais aurait eus eut eurent aie aies ait ayons ayez aient etre avoir ete eu".split())
_ADVERBES = set("ne pas plus jamais rien tres bien mal peu beaucoup trop assez si tant tellement aussi encore "
                "deja toujours souvent parfois ici la ailleurs partout dehors dedans dessus dessous "
                "aujourd-hui hier demain maintenant alors ensuite enfin ainsi surtout notamment vraiment "
                "presque environ seulement meme non oui certes evidemment probablement peut-etre "
                "rapidement lentement vite doucement fortement".split())
_NEGATION = set("ne pas plus jamais rien personne aucun aucune nul nulle guere point".split())

# — morphologie BORNÉE : uniquement les terminaisons SÛRES (ne servent QU'à défaut du lexique). On a retiré
#   ‑ir/‑re/‑er (« noir », « amer », « hiver » ne sont PAS des verbes) : au doute -> 'inconnu' (jamais faux).
_FIN_ADV = re.compile(r".{2,}ment$")          # ‑ment = adverbe (très fiable : « rapidement », « clairement »)

_LEXIQUE_POS = None                            # {mot_normalisé: {"classe":..., "genre":...}} chargé paresseusement


def _charge_lexique_pos() -> dict:
    """Charge le lexique POS français embarqué (~19 200 mots non ambigus, extraits du Wiktionnaire) : mot -> classe
    (+ genre). Les homographes multi-classes ont été ÉCARTÉS à l'extraction (FAUX=0 : on ne tranche pas)."""
    global _LEXIQUE_POS
    if _LEXIQUE_POS is not None:
        return _LEXIQUE_POS
    import json
    import os
    _LEXIQUE_POS = {}
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lexique_fr_pos.jsonl")
    try:
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                try:
                    o = json.loads(ligne)
                except Exception:
                    continue
                m = o.get("mot")
                if m:
                    _LEXIQUE_POS[m] = {"classe": o.get("classe"), "genre": o.get("genre")}
    except OSError:
        pass
    return _LEXIQUE_POS


def genre_mot(mot: str):
    """Genre grammatical d'un nom (masculin/féminin) si connu, sinon None. Lexique certifié puis lexique massif."""
    norm = _normalise(mot)
    try:
        from lexique_fr import LEXIQUE
        e = LEXIQUE.get(norm)
        if e and e.get("genre"):
            return e["genre"]
    except Exception:
        pass
    return (_charge_lexique_pos().get(norm) or {}).get("genre")


def _mot_plein(brut: str, norm: str) -> str:
    """Classe d'un mot PLEIN (hors mots-outils) : lexique certifié, puis lexique massif (19k), puis morphologie
    SÛRE (‑ment), puis majuscule initiale = nom propre, sinon 'inconnu' (jamais deviné faux)."""
    try:
        from lexique_fr import LEXIQUE
        e = LEXIQUE.get(norm)
        if e:
            return e["classe"]
    except Exception:
        pass
    lex = _charge_lexique_pos().get(norm)
    if lex and lex.get("classe"):
        return lex["classe"]
    # FORME CONJUGUÉE reconnue (index inverse dérivé/vérifié) : « dort », « parlait », « mangeons » -> verbe
    try:
        import formes_verbales
        if formes_verbales.est_forme_verbale(norm):
            return "verbe"
    except Exception:
        pass
    if _FIN_ADV.search(norm):
        return "adverbe"
    if len(brut) > 1 and brut[0].isupper() and norm not in _INTERROGATIFS:
        return "nom propre"
    return "inconnu"


_JETON_RE = re.compile(r"[0-9]+(?:[.,][0-9]+)?|[^\W\d_]+(?:['-][^\W\d_]+)*|[?!.,;:]", re.UNICODE)


def _jetons(phrase: str):
    """Découpe en jetons (mots avec apostrophe/trait d'union, nombres, ponctuation forte)."""
    return _JETON_RE.findall(phrase or "")


def classe_mot(mot: str) -> str:
    """Classe grammaticale d'UN mot isolé (mots-outils = ensembles fermés ; mots pleins = lexique+morphologie).
    L'ambiguïté d'un mot-outil polyfonctionnel est levée en contexte par `analyse` ; ici, priorité stable."""
    brut = mot.strip()
    if not brut:
        return "inconnu"
    if brut in "?!.,;:":
        return "ponctuation"
    if brut.replace(",", "").replace(".", "").isdigit():
        return "numéral"
    norm = _normalise(brut)
    # mots-outils (ordre = désambiguïsation par défaut la plus fréquente ; le contexte affine dans analyse)
    if norm in _AUXILIAIRES:
        return "auxiliaire"
    if norm in _DETERMINANTS and norm not in _PRONOMS:
        return "déterminant"
    if norm in _PRONOMS:
        return "pronom"
    if norm in _PREPOSITIONS:
        return "préposition"
    if norm in _CONJONCTIONS:
        return "conjonction"
    if norm in _ADVERBES:
        return "adverbe"
    return _mot_plein(brut, norm)


def analyse(phrase: str):
    """Étiquette chaque mot de la phrase : liste de (mot, classe). Désambiguïsation CONTEXTUELLE légère :
    un mot ambigu déterminant/pronom (« le », « la », « les », « leur ») est déterminant s'il précède un mot
    plein, pronom s'il précède un verbe/auxiliaire."""
    jetons = _jetons(phrase)
    brut_classes = [(j, classe_mot(j)) for j in jetons]
    out = []
    for i, (mot, cl) in enumerate(brut_classes):
        norm = _normalise(mot)
        if norm in ("le", "la", "les", "l", "leur") and i + 1 < len(brut_classes):
            suivant = brut_classes[i + 1][1]
            cl = "pronom" if suivant in ("verbe", "auxiliaire") else "déterminant"
        out.append((mot, cl))
    return out


_NEG_CLITIC = re.compile(r"\bne\b|\bn['’]", re.I)
_NEG_PARTICULE = re.compile(r"\b(pas|plus|jamais|rien|personne|aucune?|nulle?|gu[eè]re|point)\b", re.I)
_NEG_FORT = re.compile(r"\b(jamais|personne|aucune?|nulle?|gu[eè]re)\b", re.I)
_MOTS_QUESTION_TETE = {"qui", "que", "quoi", "quel", "quelle", "quels", "quelles", "ou", "quand", "comment",
                       "combien", "pourquoi", "lequel", "laquelle", "lesquels", "lesquelles", "est-ce"}
_VERBES_ORDRE_INDICE = re.compile(r"^(donne|dis|montre|explique|fais|va|viens|prends|mets|arrete|ecoute|"
                                  r"regarde|calcule|convertis|traduis|cherche|trouve|ecris|liste|cite|"
                                  r"raconte|decris|compare|resume|analyse)", re.I)


def type_phrase(phrase: str) -> dict:
    """Type de la phrase : {type: question|ordre|exclamation|affirmation, negative: bool, interrogatif: mot|None}.
    Signaux : « ? », mot interrogatif de tête, inversion sujet-verbe (« viens-tu »), impératif de tête, négation."""
    p = (phrase or "").strip()
    jetons = _jetons(p)
    norms = [_normalise(j) for j in jetons if j not in "?!.,;:"]
    # NÉGATION : clitique « ne »/« n' » (élision) + particule (ne...pas/jamais/plus/rien…), OU négatif FORT
    # autonome (jamais/personne/aucun/nul/guère). Robuste à l'élision « n'a » (jeton unique).
    clitique = bool(_NEG_CLITIC.search(p))
    particule = bool(_NEG_PARTICULE.search(p))
    fort = bool(_NEG_FORT.search(p))
    negative = (clitique and particule) or fort
    interrogatif = next((n for n in norms[:1] if n in _MOTS_QUESTION_TETE), None)
    if not interrogatif and len(norms) >= 2 and norms[0] in _MOTS_QUESTION_TETE:
        interrogatif = norms[0]
    est_question = "?" in p or interrogatif is not None or bool(re.search(r"\b\w+-(?:tu|vous|il|elle|on|ils|elles|je|nous)\b", _normalise(p)))
    if p.endswith("!"):
        typ = "exclamation"
    elif est_question:
        typ = "question"
    elif norms and _VERBES_ORDRE_INDICE.match(norms[0]):
        typ = "ordre"
    else:
        typ = "affirmation"
    return {"type": typ, "negative": bool(negative), "interrogatif": interrogatif}


def structure(phrase: str) -> dict:
    """Structure sujet-verbe-objet (best-effort, positionnel autour du 1er verbe/auxiliaire) :
    {sujet, verbe, objet} en chaînes, ou verbe=None si aucune forme verbale détectée (honnête : pas de rôle
    inventé). Utile pour « qui fait quoi » sur une phrase simple SVO."""
    paires = [(m, c) for m, c in analyse(phrase) if c != "ponctuation"]
    classes = [c for _, c in paires]
    mots = [m for m, _ in paires]
    vi = next((i for i, c in enumerate(classes) if c in ("verbe", "auxiliaire")), None)
    if vi is None:
        return {"sujet": " ".join(mots).strip() or None, "verbe": None, "objet": None}
    return {"sujet": " ".join(mots[:vi]).strip() or None,
            "verbe": mots[vi],
            "objet": " ".join(mots[vi + 1:]).strip() or None}


def resume_analyse(phrase: str) -> str:
    """Rendu lisible pour le chat : nature de chaque mot + type de phrase (réponse honnête, jamais inventée)."""
    paires = analyse(phrase)
    if not paires:
        return "Phrase vide."
    tp = type_phrase(phrase)
    lignes = ["· %s : %s" % (m, c) for m, c in paires if c != "ponctuation"]
    entete = "Type : %s%s." % (tp["type"], " (négative)" if tp["negative"] else "")
    return entete + "\n" + "\n".join(lignes)
