"""
NOMENCLATURES NORMALISÉES — ISCO-08, Dewey, NACE : structures PUBLIÉES (ANNEXE T, B-CONV).

Ces classifications sont bornées par CONVENTION : ce sont des tables publiées par des institutions
(OIT, OCLC, Eurostat). Rien n'y est calculé, tout y est cité — mais chaque entrée est vérifiable.

CE QUE LE MODULE CONTIENT (contenu réel, énumérable) :
  • ISCO-08 (Organisation internationale du travail, 2008) : les 10 GRANDS GROUPES, leur intitulé français
    et leur NIVEAU DE COMPÉTENCE (skill level) tel que publié par l'OIT. Plus les cardinalités officielles
    de la hiérarchie : 10 grands groupes, 43 sous-grands groupes, 130 sous-groupes, 436 groupes de base.
    `grand_groupe_du_code` relie un code ISCO complet (ex. « 7512.1 », tel qu'ingéré depuis ESCO dans la
    table `code_isco_metier`) à son grand groupe.
  • DEWEY (OCLC) : les 10 classes principales sont dans `bibliotheconomie.py` (réutilisé, jamais dupliqué).
    Ce module ajoute les 10 DIVISIONS de la classe 500 (sciences), qui n'y étaient pas.
  • NACE Rév. 2 (Eurostat) : les 21 SECTIONS, de A à U.

CE QUE LE MODULE REFUSE DE PRÉTENDRE (le FAUX=0 de ce sujet) :
  Cinq classifications sont CITÉES par la carte des sujets sans que leur contenu soit ingéré : MSC2020 (AMS),
  ACM CCS, CIM-11 (OMS), et le ROME (France Travail). Pour elles, `structure(nom)` rend ce qu'on sait
  RÉELLEMENT — l'éditeur, la nature, et le fait que le contenu N'EST PAS embarqué — tandis que
  `classes(nom)` lève ValueError. Énumérer de mémoire 63 classes MSC ou 26 chapitres CIM-11 serait
  exactement le genre de faux plausible que ce projet interdit : au doute, on cite la source et on abstient.

GARANTIES (vérifiées en adverse par `valide_nomenclatures.py`) :
  - grand groupe ISCO hors 0..9 -> ValueError ; code ISCO mal formé -> ValueError ;
  - division Dewey hors {500,…,590} -> ValueError ; section NACE hors A..U -> ValueError ;
  - `classes()` d'une classification non ingérée -> ValueError explicite (contenu non embarqué) ;
  - classification hors catalogue -> ValueError ;
  - INVARIANT : les 10 grands groupes ISCO ont des intitulés DISTINCTS et des niveaux de compétence
    tous compris entre 1 et 4, sinon RuntimeError ;
  - déterministe, pur, stdlib seule.
"""
from __future__ import annotations

SOURCE = ("ISCO-08 (OIT, 2008) · Classification décimale de Dewey (OCLC) · NACE Rév. 2 (Eurostat, "
          "règlement CE n° 1893/2006)")

# ── ISCO-08 : les 10 grands groupes, intitulés et niveaux de compétence publiés par l'OIT ──────────────────
# Le « niveau de compétence » (skill level) est un tuple : le grand groupe 1 en couvre deux, le grand
# groupe 0 (forces armées) en couvre trois — c'est la table officielle, on ne la simplifie pas.
_ISCO_GRANDS_GROUPES = {
    "0": ("Forces armées", (1, 2, 4)),
    "1": ("Directeurs, cadres de direction et gérants", (3, 4)),
    "2": ("Professions intellectuelles et scientifiques", (4,)),
    "3": ("Professions intermédiaires", (3,)),
    "4": ("Employés de type administratif", (2,)),
    "5": ("Personnel des services directs aux particuliers, commerçants et vendeurs", (2,)),
    "6": ("Agriculteurs et ouvriers qualifiés de l'agriculture, de la sylviculture et de la pêche", (2,)),
    "7": ("Métiers qualifiés de l'industrie et de l'artisanat", (2,)),
    "8": ("Conducteurs d'installations et de machines, et ouvriers de l'assemblage", (2,)),
    "9": ("Professions élémentaires", (1,)),
}

# Cardinalités officielles de la hiérarchie ISCO-08 (OIT).
_ISCO_CARDINALITES = {"grands_groupes": 10, "sous_grands_groupes": 43,
                      "sous_groupes": 130, "groupes_de_base": 436}

# ── DEWEY : les 10 divisions de la classe 500 (sciences). Les 10 CLASSES sont dans bibliotheconomie. ──────
_DEWEY_500 = {
    500: "Sciences naturelles et mathématiques",
    510: "Mathématiques",
    520: "Astronomie et sciences connexes",
    530: "Physique",
    540: "Chimie et sciences connexes",
    550: "Sciences de la Terre",
    560: "Paléontologie et paléozoologie",
    570: "Sciences de la vie, biologie",
    580: "Plantes, botanique",
    590: "Animaux, zoologie",
}

# ── NACE Rév. 2 : les 21 sections (Eurostat) ──────────────────────────────────────────────────────────────
_NACE_SECTIONS = {
    "A": "Agriculture, sylviculture et pêche",
    "B": "Industries extractives",
    "C": "Industrie manufacturière",
    "D": "Production et distribution d'électricité, de gaz, de vapeur et d'air conditionné",
    "E": "Production et distribution d'eau ; assainissement, gestion des déchets et dépollution",
    "F": "Construction",
    "G": "Commerce ; réparation d'automobiles et de motocycles",
    "H": "Transports et entreposage",
    "I": "Hébergement et restauration",
    "J": "Information et communication",
    "K": "Activités financières et d'assurance",
    "L": "Activités immobilières",
    "M": "Activités spécialisées, scientifiques et techniques",
    "N": "Activités de services administratifs et de soutien",
    "O": "Administration publique",
    "P": "Enseignement",
    "Q": "Santé humaine et action sociale",
    "R": "Arts, spectacles et activités récréatives",
    "S": "Autres activités de services",
    "T": "Activités des ménages en tant qu'employeurs",
    "U": "Activités extraterritoriales",
}

# ── Les classifications CITÉES mais NON INGÉRÉES. On dit ce qu'on sait, et rien de plus. ─────────────────
_NON_INGEREES = {
    "MSC2020": ("Mathematics Subject Classification", "American Mathematical Society / zbMATH",
                "classification des domaines mathématiques, codes à deux chiffres puis raffinements"),
    "ACM CCS": ("ACM Computing Classification System", "Association for Computing Machinery",
                "classification hiérarchique des domaines de l'informatique"),
    "CIM-11": ("Classification internationale des maladies, 11ᵉ révision", "Organisation mondiale de la santé",
               "classification des maladies et problèmes de santé, en chapitres"),
    "ROME": ("Répertoire opérationnel des métiers et des emplois", "France Travail",
             "répertoire des métiers français, en grands domaines puis fiches métier"),
}

_INGEREES = ("ISCO-08", "Dewey", "NACE")


def _exige_str(x, nom: str) -> str:
    if isinstance(x, bool) or not isinstance(x, str) or not x.strip():
        raise ValueError("%s : une chaîne non vide est requise" % nom)
    return x.strip()


# ── ISCO-08 ───────────────────────────────────────────────────────────────────────────────────────────────
def grands_groupes_isco() -> dict:
    """Les 10 grands groupes ISCO-08 : code -> intitulé français."""
    return {k: v[0] for k, v in _ISCO_GRANDS_GROUPES.items()}


def grand_groupe_isco(code: str) -> str:
    """Intitulé du grand groupe ISCO-08 (code '0' à '9'). Hors catalogue -> ValueError."""
    c = _exige_str(code, "code de grand groupe")
    if c not in _ISCO_GRANDS_GROUPES:
        raise ValueError("grand groupe ISCO-08 inconnu : %r (attendu '0' à '9')" % c)
    return _ISCO_GRANDS_GROUPES[c][0]


def niveau_competence_isco(code: str) -> tuple:
    """Niveau(x) de compétence du grand groupe, tels que publiés par l'OIT.

    Le grand groupe 1 en couvre DEUX (3 et 4) et le grand groupe 0 en couvre TROIS (1, 2 et 4) :
    on rend un tuple, jamais un scalaire — réduire serait un faux."""
    c = _exige_str(code, "code de grand groupe")
    if c not in _ISCO_GRANDS_GROUPES:
        raise ValueError("grand groupe ISCO-08 inconnu : %r" % c)
    return _ISCO_GRANDS_GROUPES[c][1]


def grand_groupe_du_code(code_isco: str) -> str:
    """Grand groupe d'un code ISCO complet. « 7512.1 » (tel qu'ingéré d'ESCO) -> « 7 ».

    Le premier chiffre d'un code ISCO EST son grand groupe (propriété de la nomenclature)."""
    c = _exige_str(code_isco, "code ISCO")
    if not c[0].isdigit():
        raise ValueError("code ISCO mal formé : %r (il doit commencer par un chiffre)" % c)
    tete = c[0]
    if tete not in _ISCO_GRANDS_GROUPES:
        raise ValueError("code ISCO hors nomenclature : %r" % c)
    return tete


def cardinalites_isco() -> dict:
    """Cardinalités officielles de la hiérarchie ISCO-08 (OIT)."""
    return dict(_ISCO_CARDINALITES)


# ── DEWEY ─────────────────────────────────────────────────────────────────────────────────────────────────
def divisions_dewey_500() -> dict:
    """Les 10 divisions de la classe 500 (sciences) : 500, 510, … 590."""
    return dict(_DEWEY_500)


def division_dewey(numero: int) -> str:
    """Intitulé d'une division Dewey de la classe 500. Hors {500..590} -> ValueError."""
    if isinstance(numero, bool) or not isinstance(numero, int):
        raise ValueError("division Dewey : un entier est requis")
    if numero not in _DEWEY_500:
        raise ValueError("division Dewey inconnue : %d (attendu 500, 510, … 590)" % numero)
    return _DEWEY_500[numero]


def classe_principale_dewey(centaine: int) -> str:
    """Délègue à `bibliotheconomie` : les 10 classes principales y vivent déjà (aucune duplication)."""
    import bibliotheconomie as _B
    return _B.classe_dewey(centaine)


# ── NACE ──────────────────────────────────────────────────────────────────────────────────────────────────
def sections_nace() -> dict:
    """Les 21 sections de la NACE Rév. 2 (A à U)."""
    return dict(_NACE_SECTIONS)


def section_nace(lettre: str) -> str:
    """Intitulé d'une section NACE. Hors A..U -> ValueError."""
    s = _exige_str(lettre, "section NACE").upper()
    if s not in _NACE_SECTIONS:
        raise ValueError("section NACE inconnue : %r (attendu 'A' à 'U')" % s)
    return _NACE_SECTIONS[s]


# ── STRUCTURES CITÉES, CONTENU NON INGÉRÉ ─────────────────────────────────────────────────────────────────
def classifications() -> dict:
    """Toutes les classifications connues du module : nom -> contenu ingéré (bool)."""
    d = {n: True for n in _INGEREES}
    d.update({n: False for n in _NON_INGEREES})
    return d


def structure(nom: str) -> dict:
    """Ce qu'on sait RÉELLEMENT d'une classification : intitulé, éditeur, nature, et si le contenu est ingéré."""
    n = _exige_str(nom, "classification")
    if n in _INGEREES:
        tailles = {"ISCO-08": len(_ISCO_GRANDS_GROUPES), "Dewey": len(_DEWEY_500), "NACE": len(_NACE_SECTIONS)}
        editeurs = {"ISCO-08": "Organisation internationale du travail",
                    "Dewey": "OCLC", "NACE": "Eurostat"}
        return {"nom": n, "editeur": editeurs[n], "contenu_ingere": True,
                "entrees_embarquees": tailles[n]}
    if n in _NON_INGEREES:
        intitule, editeur, nature = _NON_INGEREES[n]
        return {"nom": intitule, "editeur": editeur, "nature": nature, "contenu_ingere": False}
    raise ValueError("classification inconnue : %r (connues : %s)" % (n, sorted(classifications())))


def classes(nom: str) -> dict:
    """Les classes de tête d'une classification INGÉRÉE.

    Pour une classification citée mais non ingérée -> ValueError. Énumérer de mémoire les 63 classes du
    MSC ou les chapitres de la CIM-11 produirait des faux plausibles : on cite l'éditeur et on abstient."""
    n = _exige_str(nom, "classification")
    if n == "ISCO-08":
        return grands_groupes_isco()
    if n == "Dewey":
        return {str(k): v for k, v in _DEWEY_500.items()}
    if n == "NACE":
        return sections_nace()
    if n in _NON_INGEREES:
        raise ValueError("contenu de « %s » NON INGÉRÉ : structure publiée par %s, mais ses classes ne sont "
                         "pas embarquées ici (abstention plutôt qu'une énumération de mémoire)"
                         % (n, _NON_INGEREES[n][1]))
    raise ValueError("classification inconnue : %r" % n)


def _verifie_invariants() -> None:
    """Invariants durs, vérifiés à l'import : intitulés distincts, niveaux de compétence dans 1..4."""
    intitules = [v[0] for v in _ISCO_GRANDS_GROUPES.values()]
    if len(set(intitules)) != len(intitules):
        raise RuntimeError("ISCO-08 : deux grands groupes portent le même intitulé")
    for code, (_, niveaux) in _ISCO_GRANDS_GROUPES.items():
        if not niveaux or any(n not in (1, 2, 3, 4) for n in niveaux):
            raise RuntimeError("ISCO-08 : niveau de compétence hors 1..4 pour le grand groupe %s" % code)
    if _ISCO_CARDINALITES["grands_groupes"] != len(_ISCO_GRANDS_GROUPES):
        raise RuntimeError("ISCO-08 : cardinalité des grands groupes incohérente")
    if len(_NACE_SECTIONS) != 21:
        raise RuntimeError("NACE Rév. 2 : 21 sections attendues, %d trouvées" % len(_NACE_SECTIONS))
    if len(_DEWEY_500) != 10:
        raise RuntimeError("Dewey : 10 divisions attendues dans la classe 500")


_verifie_invariants()
