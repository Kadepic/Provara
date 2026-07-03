# -*- coding: utf-8 -*-
"""LANGUE — détection + réponse factuelle MULTILINGUE, model-free, FAUX=0 (2026-07-03).

POURQUOI (mission Yohan « pouvoir switcher dans un MAXIMUM de langues ») : VERAX comprend une question factuelle
posée dans plusieurs langues et RÉPOND dans cette langue. Approche model-free et EXTENSIBLE : chaque langue est une
CONFIG DE DONNÉES (mots-relations, noms de pays, gabarits de réponse, traduction des valeurs). Ajouter une langue =
ajouter une entrée dans `_LANGUES` — aucune logique nouvelle.

Cycle : détecter la langue -> traduire la question en requête FR (relation + entité) -> résoudre par le pipeline
VÉRIFIÉ FR -> habiller la réponse dans la langue cible. FAUX=0 : la valeur vient toujours du vérifié ; relation/
entité inconnue -> None (jamais d'invention). Portée : questions factuelles bornées (la traduction LIBRE reste
hors périmètre, honnête).
"""
from __future__ import annotations

import re

# ————————————————— DÉTECTION : signatures de mots-outils très fréquents par langue —————————————————
_SIG = {
    "fr": "le la les un une des du de et est sont dans sur pour que qui quel quelle quelle est combien pourquoi comment où".split(),
    "en": "the a an of and is are in on for what which who how many why where when with your you this these does do".split(),
    "es": "el la los las un una de y es son en para que cual cuál como cuánto cuanto por dónde donde con su qué".split(),
    "de": "der die das ein eine und ist sind in auf für was wer wie viele warum wo mit den dem welche hauptstadt".split(),
    "it": "il lo la i gli le un una di e è sono in su per che quale come quanto quanti perché dove con qual".split(),
    "pt": "o a os as um uma de e é são em para que qual como quanto quantos por onde com sua qual é".split(),
}
_SIG = {lg: set(w) for lg, w in _SIG.items()}


def detecte(texte: str) -> str:
    """Langue dominante ('fr'|'en'|'es'|'de'|'it'|'pt'|'?') par recouvrement de mots-outils. '?' si indécis/ex æquo."""
    mots = re.findall(r"[a-zà-ÿ']+", (texte or "").lower())
    if not mots:
        return "?"
    scores = {lg: sum(1 for m in mots if m in sig) for lg, sig in _SIG.items()}
    ordonne = sorted(scores.items(), key=lambda kv: -kv[1])
    if ordonne[0][1] == 0 or (len(ordonne) > 1 and ordonne[0][1] == ordonne[1][1]):
        return "?"
    return ordonne[0][0]


# ————————————————— CONFIG PAR LANGUE : relations, pays, gabarits, valeurs (DONNÉES, extensible) —————————————————
# entités neutres (villes, nombres) -> identité. Seuls les PAYS diffèrent -> table native->FR par langue.
_PAYS = {
    "en": {"spain": "Espagne", "france": "France", "germany": "Allemagne", "italy": "Italie", "japan": "Japon",
           "china": "Chine", "russia": "Russie", "brazil": "Brésil", "canada": "Canada", "australia": "Australie",
           "india": "Inde", "mexico": "Mexique", "portugal": "Portugal", "belgium": "Belgique", "greece": "Grèce",
           "the united states": "États-Unis", "united states": "États-Unis", "usa": "États-Unis",
           "the united kingdom": "Royaume-Uni", "united kingdom": "Royaume-Uni", "england": "Angleterre",
           "switzerland": "Suisse", "netherlands": "Pays-Bas", "sweden": "Suède", "norway": "Norvège",
           "poland": "Pologne", "austria": "Autriche", "ireland": "Irlande", "morocco": "Maroc", "egypt": "Égypte",
           "turkey": "Turquie", "argentina": "Argentine", "bolivia": "Bolivie", "south korea": "Corée du Sud"},
    "es": {"españa": "Espagne", "francia": "France", "alemania": "Allemagne", "italia": "Italie", "japón": "Japon",
           "china": "Chine", "rusia": "Russie", "brasil": "Brésil", "canadá": "Canada", "méxico": "Mexique",
           "portugal": "Portugal", "bélgica": "Belgique", "grecia": "Grèce", "estados unidos": "États-Unis",
           "reino unido": "Royaume-Uni", "suiza": "Suisse", "países bajos": "Pays-Bas", "marruecos": "Maroc",
           "egipto": "Égypte", "argentina": "Argentine", "bolivia": "Bolivie", "inglaterra": "Angleterre"},
    "de": {"spanien": "Espagne", "frankreich": "France", "deutschland": "Allemagne", "italien": "Italie",
           "japan": "Japon", "china": "Chine", "russland": "Russie", "brasilien": "Brésil", "kanada": "Canada",
           "mexiko": "Mexique", "portugal": "Portugal", "belgien": "Belgique", "griechenland": "Grèce",
           "die vereinigten staaten": "États-Unis", "vereinigte staaten": "États-Unis", "usa": "États-Unis",
           "das vereinigte königreich": "Royaume-Uni", "vereinigtes königreich": "Royaume-Uni",
           "die schweiz": "Suisse", "schweiz": "Suisse", "österreich": "Autriche", "england": "Angleterre"},
    "it": {"spagna": "Espagne", "francia": "France", "germania": "Allemagne", "italia": "Italie", "giappone": "Japon",
           "cina": "Chine", "russia": "Russie", "brasile": "Brésil", "canada": "Canada", "messico": "Mexique",
           "portogallo": "Portugal", "belgio": "Belgique", "grecia": "Grèce", "stati uniti": "États-Unis",
           "regno unito": "Royaume-Uni", "svizzera": "Suisse", "paesi bassi": "Pays-Bas", "inghilterra": "Angleterre"},
    "pt": {"espanha": "Espagne", "frança": "France", "alemanha": "Allemagne", "itália": "Italie", "japão": "Japon",
           "china": "Chine", "rússia": "Russie", "brasil": "Brésil", "canadá": "Canada", "méxico": "Mexique",
           "portugal": "Portugal", "bélgica": "Belgique", "grécia": "Grèce", "estados unidos": "États-Unis",
           "reino unido": "Royaume-Uni", "suíça": "Suisse", "países baixos": "Pays-Bas", "inglaterra": "Angleterre"},
}

# PARSING : motifs de relation par langue de la QUESTION -> relation FR canonique.
_RELATIONS = {
    "fr": [(r"\bcapitale\b", "capitale"), (r"\bpopulation\b|combien d'habitants", "population"),
           (r"\bmonnaie\b", "monnaie"), (r"\blangue( officielle)?\b", "langue"),
           (r"\b(superficie|aire)\b", "superficie")],
    "en": [(r"\bcapital\b", "capitale"), (r"\bpopulation\b|how many people", "population"),
           (r"\b(currency|money)\b", "monnaie"), (r"\b(official )?language\b", "langue"),
           (r"\b(area|size)\b", "superficie")],
    "es": [(r"\bcapital\b", "capitale"), (r"\bpoblaci[óo]n\b|cu[áa]nt[oa]s? habitantes", "population"),
           (r"\bmoneda\b", "monnaie"), (r"\b(idioma|lengua)( oficial)?\b", "langue"),
           (r"\b(superficie|[áa]rea|tama[ñn]o)\b", "superficie")],
    "de": [(r"\bhauptstadt\b", "capitale"), (r"\b(bev[öo]lkerung|einwohner)\b", "population"),
           (r"\b(w[äa]hrung|geld)\b", "monnaie"), (r"\b(amtssprache|sprache)\b", "langue"),
           (r"\b(fl[äa]che|gr[öo]ße)\b", "superficie")],
    "it": [(r"\bcapitale\b", "capitale"), (r"\bpopolazione\b|quanti abitanti", "population"),
           (r"\b(moneta|valuta)\b", "monnaie"), (r"\blingua( ufficiale)?\b", "langue"),
           (r"\b(superficie|area)\b", "superficie")],
    "pt": [(r"\bcapital\b", "capitale"), (r"\bpopula[çc][ãa]o\b|quantos habitantes", "population"),
           (r"\bmoeda\b", "monnaie"), (r"\b(l[íi]ngua|idioma)( oficial)?\b", "langue"),
           (r"\b([áa]rea|superf[íi]cie|tamanho)\b", "superficie")],
}

# RENDU : gabarit de réponse par (langue CIBLE, relation FR). « %s = entité, %s = valeur ».
_TEMPLATES = {
    "en": {"capitale": "The capital of %s is %s.", "population": "The population of %s is %s.",
           "monnaie": "The currency of %s is %s.", "langue": "The official language of %s is %s.",
           "superficie": "The area of %s is %s."},
    "es": {"capitale": "La capital de %s es %s.", "population": "La población de %s es %s.",
           "monnaie": "La moneda de %s es %s.", "langue": "El idioma oficial de %s es %s.",
           "superficie": "La superficie de %s es %s."},
    "de": {"capitale": "Die Hauptstadt von %s ist %s.", "population": "Die Bevölkerung von %s beträgt %s.",
           "monnaie": "Die Währung von %s ist %s.", "langue": "Die Amtssprache von %s ist %s.",
           "superficie": "Die Fläche von %s beträgt %s."},
    "it": {"capitale": "La capitale di %s è %s.", "population": "La popolazione di %s è %s.",
           "monnaie": "La moneta di %s è %s.", "langue": "La lingua ufficiale di %s è %s.",
           "superficie": "La superficie di %s è %s."},
    "pt": {"capitale": "A capital de %s é %s.", "population": "A população de %s é %s.",
           "monnaie": "A moeda de %s é %s.", "langue": "A língua oficial de %s é %s.",
           "superficie": "A área de %s é %s."},
    "fr": {"capitale": "La capitale de %s est %s.", "population": "La population de %s est %s.",
           "monnaie": "La monnaie de %s est %s.", "langue": "La langue officielle de %s est %s.",
           "superficie": "La superficie de %s est %s."},
}

# prépositions introduisant l'entité, par langue de la QUESTION
_PREP_ENTITE = {
    "fr": r"\b(?:de\s+l['a]|du|des|de\s+la|de|d')\s*(.+?)\s*\??\s*$",
    "en": r"\b(?:of|in)\s+(.+?)\s*\??\s*$",
    "es": r"\bde\s+(.+?)\s*\??\s*$",
    "de": r"\bvon\s+(.+?)\s*\??\s*$",
    "it": r"\b(?:della|dello|degli|delle|del|dei|di|d')\s*(.+?)\s*\??\s*$",
    "pt": r"\bd[eo]\s+(.+?)\s*\??\s*$",
}

# traduction des VALEURS linguistiques FR -> langue cible (les lieux/nombres restent neutres)
_VALEURS = {
    "en": {"anglais": "English", "français": "French", "espagnol": "Spanish", "allemand": "German",
           "italien": "Italian", "portugais": "Portuguese", "arabe": "Arabic", "chinois": "Chinese",
           "japonais": "Japanese", "russe": "Russian", "néerlandais": "Dutch"},
    "es": {"anglais": "inglés", "français": "francés", "espagnol": "español", "allemand": "alemán",
           "italien": "italiano", "portugais": "portugués", "arabe": "árabe", "chinois": "chino", "japonais": "japonés"},
    "de": {"anglais": "Englisch", "français": "Französisch", "espagnol": "Spanisch", "allemand": "Deutsch",
           "italien": "Italienisch", "portugais": "Portugiesisch", "arabe": "Arabisch", "japonais": "Japanisch"},
    "it": {"anglais": "inglese", "français": "francese", "espagnol": "spagnolo", "allemand": "tedesco",
           "italien": "italiano", "portugais": "portoghese", "arabe": "arabo", "japonais": "giapponese"},
    "pt": {"anglais": "inglês", "français": "francês", "espagnol": "espanhol", "allemand": "alemão",
           "italien": "italiano", "portugais": "português", "arabe": "árabe", "japonais": "japonês"},
}

LANGUES_SUPPORTEES = tuple(k for k in _TEMPLATES if k != "fr")   # langues CIBLES non-FR où VERAX sait répondre
_NOMS = {"fr": "français", "en": "anglais", "es": "espagnol", "de": "allemand", "it": "italien", "pt": "portugais"}


def _entite_fr(brut: str, lang: str) -> str:
    b = " ".join(brut.strip().lower().split())
    table = _PAYS.get(lang, {})
    if b in table:
        return table[b]
    b2 = re.sub(r"^(the|le|la|el|il|lo|die|der|das|o|a)\s+", "", b)
    if b2 in table:
        return table[b2]
    return brut.strip().title()                     # ville/nom propre souvent identique


def analyse_question(question: str, source_lang: str):
    """Analyse une question factuelle écrite en `source_lang` -> (relation_fr, requete_fr, entité_affichée),
    ou None si la relation/entité n'est pas reconnue. Indépendant de la langue de RÉPONSE."""
    if source_lang not in _RELATIONS:
        return None
    q = question.strip()
    prep = _PREP_ENTITE[source_lang]
    for motif, rel_fr in _RELATIONS[source_lang]:
        if re.search(motif, q, re.I):
            m = re.search(prep, q, re.I)
            if not m:
                continue
            ent = m.group(1).strip(" ?.\"'")
            if not ent:
                continue
            return rel_fr, "%s de %s" % (rel_fr, _entite_fr(ent, source_lang)), ent.title()
    return None


def question_vers_fr(question: str, lang: str):
    """(rétro-compat) -> (requete_fr, gabarit_cible, entité) pour une question en `lang` répondue dans `lang`."""
    a = analyse_question(question, lang)
    if not a:
        return None
    rel_fr, requete, ent = a
    return requete, _TEMPLATES.get(lang, {}).get(rel_fr, "%s: %s"), ent


def repond_langue(question: str, resolveur, lang: str = None, source_lang: str = None):
    """Répond à une question factuelle DANS la langue `lang` (cible). La question peut être écrite dans une autre
    langue (`source_lang`, détectée sinon) : on ANALYSE dans la langue source, on RÉSOUT par le pipeline vérifié
    FR, on REND dans la langue cible. None si langue cible non gérée / relation-entité non reconnue / fait absent.
    FAUX=0 : la valeur vient toujours du vérifié."""
    src = source_lang or detecte(question)
    cible = lang or src
    if cible not in _TEMPLATES or cible == "fr" and lang is None:
        # cible FR par défaut = géré par le pipeline FR natif (sauf si explicitement demandé lang='fr')
        if not (lang == "fr"):
            return None
    a = analyse_question(question, src if src in _RELATIONS else "fr")
    if not a:
        return None
    rel_fr, requete, ent_aff = a
    valeur = resolveur(requete)
    if not valeur:
        return None
    m = re.match(r"^(.*?)\s*\((?:trouvé sur|found on)\s*(.+?)\)\s*$", valeur)
    val, source = (m.group(1).strip(), m.group(2).strip()) if m else (valeur.strip(), None)
    val = _VALEURS.get(cible, {}).get(val.lower(), val)
    gabarit = _TEMPLATES.get(cible, {}).get(rel_fr)
    if not gabarit:
        return None
    sortie = gabarit % (ent_aff, val)
    if source:
        sortie += " (source: %s)" % source
    return sortie


# rétro-compat (l'ancien nom): réponse en anglais
def repond_en(question_en: str, resolveur):
    return repond_langue(question_en, resolveur, lang="en")


_RE_SWITCH = re.compile(
    r"\b(?:r[ée]ponds?|parle|passe|switch|answer|respond|habla|responde|antworte|rispondi|responde)\b.*?\b"
    r"(fran[çc]ais|french|anglais|english|espagnol|spanish|espa[ñn]ol|allemand|german|deutsch|"
    r"italien|italian|italiano|portugais|portuguese|portugu[êe]s)\b", re.I)
_ALIAS = {"french": "fr", "français": "fr", "francais": "fr", "english": "en", "anglais": "en",
          "spanish": "es", "espagnol": "es", "español": "es", "espanol": "es", "german": "de", "allemand": "de",
          "deutsch": "de", "italian": "it", "italien": "it", "italiano": "it", "portuguese": "pt",
          "portugais": "pt", "portugues": "pt", "português": "pt"}


def demande_de_switch(texte: str):
    """Détecte « réponds en espagnol » / « answer in german »… -> code langue cible, ou None."""
    m = _RE_SWITCH.search(texte or "")
    if m:
        return _ALIAS.get(m.group(1).lower())
    return None


def nom_langue(code: str) -> str:
    return _NOMS.get(code, code)
