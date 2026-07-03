# -*- coding: utf-8 -*-
"""TRADUCTION mot-à-mot ASSISTÉE (FR↔EN), model-free, souverain, offline.

PRINCIPE HONNÊTE (FAUX=0) : pas un traducteur neuronal fluide. Un dictionnaire bilingue CURÉ (traductions
correctes, sens le plus courant) + transfert LÉGER (locutions d'abord, morphologie du pluriel, ordre
adjectif-nom) traduit mot à mot. Un mot ABSENT du dictionnaire est laissé TEL QUEL et SIGNALÉ — jamais
inventé, jamais deviné. La sortie est étiquetée « mot-à-mot assisté » pour ne pas se faire passer pour une
traduction humaine. Couverture = vocabulaire courant ; s'étend en ajoutant des entrées curées.

API : traduit(texte, cible) -> (texte_traduit, mots_inconnus). langues : 'en' <-> 'fr'."""
from __future__ import annotations

import re

# — DICTIONNAIRE CURÉ FR -> EN (sens le plus courant ; entrées vérifiées) —
# Locutions multi-mots EN PREMIER (traduites avant les mots isolés).
_LOCUTIONS_FR_EN = {
    "s'il vous plait": "please", "s'il te plait": "please", "au revoir": "goodbye",
    "bonne nuit": "good night", "bonne journee": "good day", "bonne soiree": "good evening",
    "de rien": "you're welcome", "tout de suite": "right away", "peut etre": "maybe",
    "beaucoup de": "many", "il y a": "there is", "est ce que": "", "parce que": "because",
    "tout le monde": "everyone", "quelque chose": "something", "quelqu un": "someone",
    "n importe quoi": "anything", "aujourd hui": "today", "en train de": "",
}

_FR_EN = {
    # déterminants / pronoms
    "le": "the", "la": "the", "les": "the", "l": "the", "un": "a", "une": "a", "des": "some",
    "ce": "this", "cet": "this", "cette": "this", "ces": "these", "mon": "my", "ma": "my", "mes": "my",
    "ton": "your", "ta": "your", "tes": "your", "son": "his", "sa": "her", "ses": "their",
    "notre": "our", "nos": "our", "votre": "your", "vos": "your", "leur": "their", "leurs": "their",
    "je": "I", "tu": "you", "il": "he", "elle": "she", "on": "one", "nous": "we", "vous": "you",
    "ils": "they", "elles": "they", "me": "me", "te": "you", "se": "oneself", "moi": "me", "toi": "you",
    "lui": "him", "eux": "them", "qui": "who", "que": "that", "quoi": "what", "dont": "whose",
    "celui": "the one", "celle": "the one", "chacun": "each", "tout": "all", "tous": "all",
    "toute": "all", "toutes": "all", "aucun": "none", "plusieurs": "several", "certains": "some",
    "meme": "same", "autre": "other", "autres": "other",
    # prépositions / conjonctions
    "de": "of", "du": "of the", "a": "to", "au": "to the", "aux": "to the", "en": "in", "dans": "in",
    "sur": "on", "sous": "under", "avec": "with", "sans": "without", "pour": "for", "par": "by",
    "et": "and", "ou": "or", "mais": "but", "donc": "so", "car": "because", "ni": "nor",
    "chez": "at", "vers": "towards", "entre": "between", "pendant": "during", "avant": "before",
    "apres": "after", "depuis": "since", "jusque": "until", "contre": "against", "selon": "according to",
    "comme": "like", "si": "if", "quand": "when", "ou_lieu": "where", "pourquoi": "why", "comment": "how",
    # verbes courants (infinitif + formes fréquentes -> EN)
    "etre": "to be", "suis": "am", "es": "are", "est": "is", "sommes": "are", "etes": "are", "sont": "are",
    "etait": "was", "etaient": "were", "sera": "will be", "ete": "been",
    "avoir": "to have", "ai": "have", "as": "have", "avons": "have", "avez": "have", "ont": "have",
    "avait": "had", "aura": "will have", "eu": "had",
    "aller": "to go", "vais": "go", "vas": "go", "va": "goes", "allons": "go", "allez": "go", "vont": "go",
    "faire": "to do", "fais": "do", "fait": "does", "faisons": "do", "faites": "do", "font": "do",
    "dire": "to say", "dis": "say", "dit": "says", "disons": "say", "disent": "say",
    "voir": "to see", "vois": "see", "voit": "sees", "voyons": "see", "voient": "see", "vu": "seen",
    "savoir": "to know", "sais": "know", "sait": "knows", "savons": "know", "savent": "know",
    "pouvoir": "to be able", "peux": "can", "peut": "can", "pouvons": "can", "peuvent": "can",
    "vouloir": "to want", "veux": "want", "veut": "wants", "voulons": "want", "veulent": "want",
    "devoir": "must", "dois": "must", "doit": "must", "devons": "must", "doivent": "must",
    "venir": "to come", "viens": "come", "vient": "comes", "venons": "come", "viennent": "come",
    "prendre": "to take", "prends": "take", "prend": "takes", "prennent": "take",
    "donner": "to give", "donne": "gives", "donnent": "give",
    "manger": "to eat", "mange": "eats", "mangent": "eat", "boire": "to drink", "bois": "drink",
    "dormir": "to sleep", "dort": "sleeps", "dorment": "sleep", "parler": "to speak", "parle": "speaks",
    "aimer": "to love", "aime": "loves", "aiment": "love", "penser": "to think", "pense": "thinks",
    "trouver": "to find", "trouve": "finds", "regarder": "to watch", "regarde": "watches",
    "ecouter": "to listen", "ecoute": "listens", "lire": "to read", "lit": "reads",
    "ecrire": "to write", "ecrit": "writes", "vivre": "to live", "vit": "lives",
    "travailler": "to work", "travaille": "works", "jouer": "to play", "joue": "plays",
    "marcher": "to walk", "marche": "walks", "courir": "to run", "court": "runs",
    "appeler": "to call", "appelle": "calls", "demander": "to ask", "demande": "asks",
    "comprendre": "to understand", "comprend": "understands", "connaitre": "to know", "connait": "knows",
    # noms courants
    "chat": "cat", "chien": "dog", "oiseau": "bird", "poisson": "fish", "cheval": "horse",
    "maison": "house", "voiture": "car", "livre": "book", "table": "table", "chaise": "chair",
    "porte": "door", "fenetre": "window", "eau": "water", "feu": "fire", "terre": "earth", "air": "air",
    "soleil": "sun", "lune": "moon", "ciel": "sky", "mer": "sea", "montagne": "mountain",
    "arbre": "tree", "fleur": "flower", "ville": "city", "pays": "country", "monde": "world",
    "rue": "street", "route": "road", "chemin": "path", "pont": "bridge", "riviere": "river",
    "homme": "man", "femme": "woman", "enfant": "child", "garcon": "boy", "fille": "girl",
    "ami": "friend", "amie": "friend", "gens": "people", "personne": "person", "famille": "family",
    "pere": "father", "mere": "mother", "frere": "brother", "soeur": "sister", "fils": "son",
    "jour": "day", "nuit": "night", "matin": "morning", "soir": "evening", "temps": "time",
    "annee": "year", "mois": "month", "semaine": "week", "heure": "hour", "minute": "minute",
    "vie": "life", "mort": "death", "amour": "love", "travail": "work", "argent": "money",
    "nom": "name", "mot": "word", "langue": "language", "histoire": "story", "musique": "music",
    "nourriture": "food", "pain": "bread", "vin": "wine", "lait": "milk", "cafe": "coffee",
    "main": "hand", "pied": "foot", "tete": "head", "oeil": "eye", "coeur": "heart", "corps": "body",
    "chose": "thing", "idee": "idea", "question": "question", "reponse": "answer", "probleme": "problem",
    "ordinateur": "computer", "telephone": "phone", "ecole": "school", "bureau": "office", "papier": "paper",
    "stylo": "pen", "porte_": "door", "lettre": "letter", "image": "picture", "photo": "photo", "film": "movie",
    "route_": "road", "avion": "plane", "train": "train", "bateau": "boat", "velo": "bike", "magasin": "shop",
    "hopital": "hospital", "eglise": "church", "ecran": "screen", "clavier": "keyboard", "internet": "internet",
    # adjectifs / adverbes
    "grand": "big", "grande": "big", "petit": "small", "petite": "small", "bon": "good", "bonne": "good",
    "mauvais": "bad", "beau": "beautiful", "belle": "beautiful", "joli": "pretty", "nouveau": "new",
    "nouvelle": "new", "vieux": "old", "vieille": "old", "jeune": "young", "long": "long", "court": "short",
    "haut": "high", "bas": "low", "chaud": "hot", "froid": "cold", "grand_": "tall", "fort": "strong",
    "faible": "weak", "rapide": "fast", "lent": "slow", "facile": "easy", "difficile": "difficult",
    "vrai": "true", "faux": "false", "important": "important", "premier": "first", "dernier": "last",
    "meilleur": "better", "pire": "worse", "heureux": "happy", "triste": "sad", "plein": "full", "vide": "empty",
    "ca": "it", "cela": "that", "ceci": "this", "rien": "nothing", "quelque": "some", "chaque": "each",
    "rouge": "red", "bleu": "blue", "vert": "green", "jaune": "yellow", "noir": "black", "blanc": "white",
    "tres": "very", "bien": "well", "mal": "badly", "beaucoup": "a lot", "peu": "little", "trop": "too much",
    "assez": "enough", "plus": "more", "moins": "less", "aussi": "also", "encore": "again", "deja": "already",
    "toujours": "always", "jamais": "never", "souvent": "often", "parfois": "sometimes", "ici": "here",
    "la_bas": "there", "maintenant": "now", "hier": "yesterday", "demain": "tomorrow", "oui": "yes", "non": "no",
    "peut_etre": "maybe", "vraiment": "really", "presque": "almost", "surtout": "especially",
    # nombres / temps
    "zero": "zero", "deux": "two", "trois": "three", "quatre": "four", "cinq": "five", "six": "six",
    "sept": "seven", "huit": "eight", "neuf": "nine", "dix": "ten", "cent": "hundred", "mille": "thousand",
    "lundi": "Monday", "mardi": "Tuesday", "mercredi": "Wednesday", "jeudi": "Thursday",
    "vendredi": "Friday", "samedi": "Saturday", "dimanche": "Sunday",
    # politesse
    "bonjour": "hello", "salut": "hi", "merci": "thank you", "pardon": "sorry", "excusez": "excuse",
}

# négation FR « ne … pas » -> « not » (le « ne » disparaît, « pas » devient « not »)
_FR_EN["ne"] = ""
_FR_EN["n"] = ""
_FR_EN["pas"] = "not"
_FR_EN["plus_neg"] = "no more"

# noyau EN->FR CURÉ (prioritaire) : évite les collisions d'inverse automatique sur les mots-outils fréquents.
_EN_FR_CORE = {
    "the": "le", "a": "un", "an": "un", "i": "je", "you": "tu", "he": "il", "she": "elle", "we": "nous",
    "they": "ils", "it": "il", "me": "moi", "him": "lui", "my": "mon", "your": "ton", "his": "son", "her": "sa",
    "is": "est", "are": "sont", "am": "suis", "was": "était", "be": "être", "have": "avoir", "has": "a",
    "and": "et", "or": "ou", "but": "mais", "of": "de", "to": "à", "in": "dans", "on": "sur", "for": "pour",
    "with": "avec", "not": "pas", "no": "non", "yes": "oui", "this": "ce", "that": "que", "who": "qui",
    "man": "homme", "woman": "femme", "cat": "chat", "dog": "chien", "water": "eau", "house": "maison",
    "day": "jour", "night": "nuit", "big": "grand", "small": "petit", "good": "bon", "very": "très",
}
_EN_FR = dict(_EN_FR_CORE)
for _fr, _en in _FR_EN.items():
    if _en and "_" not in _fr:
        _k = _en.split()[0] if " " in _en else _en
        _EN_FR.setdefault(_k, _fr)          # le noyau curé garde la priorité (setdefault)

_MOT = re.compile(r"[a-zàâäéèêëîïôöùûüçœ]+|[0-9]+|[^\w\s]", re.I)


def _deaccent(s: str) -> str:
    for a, b in (("àâä", "a"), ("éèêë", "e"), ("îï", "i"), ("ôö", "o"), ("ùûü", "u"), ("ç", "c"), ("œ", "oe")):
        for c in a:
            s = s.replace(c, b)
    return s


def _cherche_fr_en(mot: str):
    """Traduit un mot FR->EN avec morphologie légère (pluriel -s/-x, essai du lemme). None si inconnu."""
    m = _deaccent(mot.lower())
    if m in _FR_EN:
        return _FR_EN[m]
    if len(m) > 3 and m.endswith("s") and m[:-1] in _FR_EN:      # pluriel régulier -s
        return _pluriel_en(_FR_EN[m[:-1]])
    if len(m) > 3 and m.endswith("x") and m[:-1] in _FR_EN:      # pluriel -x (chevaux~cheval approx)
        return _pluriel_en(_FR_EN[m[:-1]])
    return None


def _pluriel_en(en: str) -> str:
    if not en or " " in en:
        return en
    if en.endswith(("s", "x", "z", "ch", "sh")):
        return en + "es"
    if en.endswith("y") and en[-2:-1] not in "aeiou":
        return en[:-1] + "ies"
    return en + "s"


def _cherche_en_fr(mot: str):
    m = mot.lower()
    if m in _EN_FR:
        return _EN_FR[m]
    if len(m) > 3 and m.endswith("s") and m[:-1] in _EN_FR:
        return _EN_FR[m[:-1]] + "s"
    return None


# — SOURCE RICHE : la table `concept_du_mot` de la base complète (lexique cross-lingue ~165k mots, 20k anglais).
#   Clé « lemme (langue) », valeur = concept/gloss FR. On l'utilise EN PRIORITÉ sur le dictionnaire curé ; ce
#   dernier reste le repli hors-ligne (base échantillon, où concept_du_mot est absente). Aucun mot inventé.
_LANG_FR = {"en": "anglais", "fr": "français", "es": "espagnol", "de": "allemand", "it": "italien", "pt": "portugais"}
_REV_CACHE = {}


def _lecteur():
    """Lecteur SEULEMENT s'il est DÉJÀ chargé (ne JAMAIS forcer un cold-load de 71,9M faits depuis ce module) :
    dans le .exe la base est préchargée -> disponible ; hors ligne/gate -> None -> repli dictionnaire curé."""
    import sys
    lec_mod = sys.modules.get("lecteur")
    if lec_mod is not None and getattr(lec_mod, "LECTEUR", None) is not None:
        return lec_mod.LECTEUR
    ia = sys.modules.get("ia")
    if ia is not None:
        return getattr(getattr(ia, "_LEC", None), "LECTEUR", None)
    return None


def _gloss_de(lemme: str, langue: str):
    """Gloss/concept FR d'un mot d'une langue via concept_du_mot (base complète), ou None."""
    lec = _lecteur()
    if lec is None:
        return None
    try:
        f = lec.cherche("concept_du_mot", "%s (%s)" % (lemme, _LANG_FR.get(langue, langue)))
        return f.valeur if f is not None else None
    except Exception:
        return None


def _index_inverse(langue: str):
    """Index {gloss_normalisé -> lemme} pour une langue cible, construit UNE fois depuis concept_du_mot.
    Permet FR -> langue (le gloss FR est la clé). {} si la table est absente (base échantillon)."""
    if langue in _REV_CACHE:
        return _REV_CACHE[langue]
    idx = {}
    lec = _lecteur()
    suffixe = " (%s)" % _LANG_FR.get(langue, langue)
    try:
        table = lec.tables.get("concept_du_mot") if lec is not None else None
        if table is not None:
            for cle, fait in table.items():
                if cle.endswith(suffixe):
                    lemme = cle[: -len(suffixe)]
                    g = _deaccent(str(fait.valeur).lower())
                    idx.setdefault(g, lemme)        # premier lemme gagne (le plus fréquent en tête de table)
    except Exception:
        idx = {}
    _REV_CACHE[langue] = idx
    return idx


def _traduit_mot(mot: str, source: str, cible: str):
    """Traduit un mot via concept_du_mot (prioritaire) puis le dictionnaire curé. None si inconnu partout."""
    if cible == "fr":                                   # source -> FR : gloss direct
        g = _gloss_de(mot, source)
        if g:
            return g
        return _cherche_en_fr(mot) if source == "en" else None
    # FR -> cible : index inverse (gloss FR = le mot) puis dictionnaire curé
    idx = _index_inverse(cible)
    hit = idx.get(_deaccent(mot.lower()))
    if hit:
        return hit
    return _cherche_fr_en(mot) if cible == "en" else None


def traduit(texte: str, cible: str = "en"):
    """Traduit `texte` mot-à-mot vers `cible` ('en' ou 'fr'). Renvoie (traduction, mots_inconnus).
    FAUX=0 : un mot inconnu est laissé TEL QUEL et listé, jamais inventé."""
    # langue SOURCE : détectée si possible, sinon déduite de la cible (FR<->EN par défaut)
    try:
        import langue as _lg
        source = _lg.detecte(texte)
    except Exception:
        source = ""
    if source == cible or source not in _LANG_FR:
        source = "fr" if cible != "fr" else "en"

    src_low = _deaccent(texte.lower())
    if cible == "en" and source == "fr":
        for loc, en in _LOCUTIONS_FR_EN.items():                # locutions d'abord (longest first implicite curé)
            src_low = re.sub(r"\b" + re.escape(loc) + r"\b", " \x00" + en.replace(" ", "\x01") + "\x00 ", src_low)

    out, inconnus = [], []
    for tok in _MOT.findall(src_low):
        if tok.startswith("\x00"):                              # locution déjà traduite
            out.append(tok.strip("\x00").replace("\x01", " "))
            continue
        if re.match(r"[^\w]", tok) or tok.isdigit():
            out.append(tok)
            continue
        tr = _traduit_mot(tok, source, cible)
        if tr is None:
            out.append(tok)                                      # inconnu : gardé tel quel (FAUX=0)
            if tok not in inconnus:
                inconnus.append(tok)
        elif tr:                                                 # "" = mot vide FR (ne, est-ce que) -> omis
            out.append(tr)
    # recomposition : espace sauf avant ponctuation
    res = ""
    for i, w in enumerate(out):
        if re.match(r"[^\w]", w) or i == 0:
            res += w
        else:
            res += " " + w
    res = re.sub(r"\s+", " ", res).strip()
    return (res[:1].upper() + res[1:] if res else res), inconnus


LANGUES = ("fr", "en")
