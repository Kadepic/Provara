"""
ÉQUIVALENCES INTERNATIONALES DE DIPLÔMES — cadres de comparabilité PUBLIÉS, FAUX=0 (PARTIE VI, B-CONV).

Ce sujet fut classé « bloqué sur un corpus externe ». Il ne l'est pas : DEUX cadres de comparabilité sont
publiés, stables et officiels. Ce module les encode et les met en correspondance :
  • CITE / ISCED 2011 (UNESCO) : classement des PROGRAMMES d'éducation en 9 niveaux (0 à 8) —
        0 éducation de la petite enfance ; 1 primaire ; 2 premier cycle du secondaire ;
        3 second cycle du secondaire ; 4 post-secondaire non supérieur ; 5 supérieur de cycle court ;
        6 licence/bachelor ; 7 master ; 8 doctorat.
  • CEC / EQF (Union européenne, recommandation 2017/C 189/03) : 8 niveaux (1 à 8) fondés sur les ACQUIS
        d'apprentissage (savoirs, aptitudes, responsabilité/autonomie) — PAS sur la durée d'études.
  • CATALOGUE PAR PAYS (France, Allemagne, Royaume-Uni, Espagne, Italie, États-Unis) : diplômes NOMMÉS
        rattachés à leur niveau CITE (et, pour l'espace CEC, à leur niveau CEC).

HONNÊTETÉ CAPITALE (le cœur FAUX=0) : un même niveau CITE n'est **PAS** une équivalence juridique.
La reconnaissance académique et professionnelle relève des AUTORITÉS NATIONALES (réseau ENIC-NARIC) et,
pour les professions réglementées, de la directive 2005/36/CE. `equivalent()` ne rend qu'une comparabilité
de NIVEAU, assortie d'un avertissement explicite ; `reconnaissance_juridique()` s'ABSTIENT toujours.

GARANTIES (vérifiées en adverse par `valide_equivalences_diplomes.py`) :
  - CITE = 9 niveaux (0..8), CEC = 8 niveaux (1..8) : nombres DIFFÉRENTS (un module qui les égaliserait serait faux) ;
  - baccalauréat FR = CITE 3 (et NON 4) mais CEC 4 : les deux cadres DIVERGENT (programmes vs acquis) ;
  - licence = CITE 6, master = CITE 7, doctorat = CITE 8 ; bachelor's US = CITE 6 = licence FR ;
  - diplôme ou pays hors catalogue -> ValueError ; CITE hors 0..8 -> ValueError ; CEC hors 1..8 -> ValueError ;
  - `reconnaissance_juridique(...)` -> ValueError (ce module ne délivre AUCUNE reconnaissance) ;
  - types invalides (bool, non-chaîne, mauvaise arité) -> ValueError ; déterministe ; faux POSITIF interdit.

Toutes les fonctions sont PURES et déterministes ; stdlib uniquement (aucun import de dataset).
"""
from __future__ import annotations

SOURCE = ("CITE/ISCED 2011 (UNESCO) ; CEC/EQF recommandation UE 2017/C 189/03 ; "
          "reconnaissance : réseau ENIC-NARIC + directive 2005/36/CE (professions réglementées)")

# ── CITE / ISCED 2011 : 9 niveaux (0 à 8) — classement des PROGRAMMES ─────────────────────────────────────────────
_CITE = {
    0: "éducation de la petite enfance",
    1: "enseignement primaire",
    2: "premier cycle de l'enseignement secondaire",
    3: "second cycle de l'enseignement secondaire",
    4: "enseignement post-secondaire non supérieur",
    5: "enseignement supérieur de cycle court",
    6: "licence ou équivalent (niveau licence/bachelor)",
    7: "master ou équivalent",
    8: "doctorat ou équivalent",
}

# ── CEC / EQF : 8 niveaux (1 à 8) — descripteurs fondés sur les ACQUIS d'apprentissage ───────────────────────────
_CEC = {
    1: "savoirs et aptitudes générales de base",
    2: "savoirs factuels de base dans un domaine de travail ou d'études",
    3: "savoirs couvrant des faits, principes, processus et concepts généraux",
    4: "savoirs factuels et théoriques dans des contextes généraux d'un domaine de travail ou d'études",
    5: "savoirs détaillés, spécialisés, factuels et théoriques, et conscience de leurs limites",
    6: "savoirs approfondis dans un domaine, impliquant une compréhension critique (niveau licence)",
    7: "savoirs hautement spécialisés, en partie à la pointe des connaissances d'un domaine (niveau master)",
    8: "savoirs à la frontière la plus avancée d'un domaine et à l'interface de plusieurs domaines (niveau doctorat)",
}

_CITE_MIN, _CITE_MAX = 0, 8
_CEC_MIN, _CEC_MAX = 1, 8

_AVERTISSEMENT = (
    "comparabilité de NIVEAU (CITE) uniquement : elle n'emporte PAS reconnaissance académique ni "
    "professionnelle. La reconnaissance relève des autorités nationales (réseau ENIC-NARIC) et, pour les "
    "professions réglementées, de la directive 2005/36/CE."
)


# ── normalisation (déterministe, sans accents, sans apostrophes) ─────────────────────────────────────────────────
_ACCENTS = str.maketrans({
    "á": "a", "à": "a", "â": "a", "ä": "a", "ã": "a",
    "é": "e", "è": "e", "ê": "e", "ë": "e",
    "í": "i", "ì": "i", "î": "i", "ï": "i",
    "ó": "o", "ò": "o", "ô": "o", "ö": "o", "õ": "o",
    "ú": "u", "ù": "u", "û": "u", "ü": "u",
    "ç": "c", "ñ": "n",
})


def _norm(s) -> str:
    """Normalise une chaîne (pays ou diplôme) : minuscules, sans accents, apostrophes/traits d'union -> espace."""
    if not isinstance(s, str):
        raise ValueError(f"chaîne attendue, reçu {s!r}")
    t = s.strip().lower().translate(_ACCENTS)
    for ch in ("'", "’", "-", "/", ".", ","):
        t = t.replace(ch, " ")
    return " ".join(t.split())


# ── CATALOGUE PAR PAYS : diplômes NOMMÉS -> (CITE, CEC) ──────────────────────────────────────────────────────────
# CEC = None hors de l'espace CEC/EQF (ex. États-Unis, hors UE) : cec() s'abstient alors (ValueError).
# Chaque entrée : (nom canonique, niveau CITE, niveau CEC ou None, alias supplémentaires).
_CATALOGUE_BRUT = {
    "France": [
        ("baccalauréat", 3, 4, ["bac", "baccalaureat"]),
        ("BTS", 5, 5, ["brevet de technicien superieur", "brevet de technicien supérieur"]),
        ("DUT", 5, 5, ["diplome universitaire de technologie", "diplôme universitaire de technologie"]),
        ("licence", 6, 6, ["bachelor", "licence bachelor"]),
        ("master", 7, 7, []),
        ("doctorat", 8, 8, ["these", "thèse", "phd"]),
    ],
    "Allemagne": [
        ("Abitur", 3, 4, ["abitur"]),
        ("Bachelor", 6, 6, ["bachelorgrad"]),
        ("Master", 7, 7, ["mastergrad"]),
        ("Promotion (Doktorgrad)", 8, 8, ["promotion", "doktor", "doktorgrad", "phd"]),
    ],
    "Royaume-Uni": [
        ("A-levels", 3, 4, ["a level", "a levels", "gce a level"]),
        ("bachelor's degree", 6, 6, ["bachelor", "bachelors degree", "honours degree"]),
        ("master's degree", 7, 7, ["master", "masters degree"]),
        ("doctorate", 8, 8, ["phd", "doctoral degree", "dphil"]),
    ],
    "Espagne": [
        ("Bachillerato", 3, 4, ["bachillerato"]),
        ("Grado", 6, 6, ["titulo de grado", "título de grado", "grado"]),
        ("Máster", 7, 7, ["master", "master universitario"]),
        ("Doctorado", 8, 8, ["doctorado", "phd"]),
    ],
    "Italie": [
        ("Diploma di maturità", 3, 4, ["diploma di maturita", "maturita", "maturità"]),
        ("Laurea", 6, 6, ["laurea triennale"]),
        ("Laurea magistrale", 7, 7, ["laurea specialistica", "laurea magistrale"]),
        ("Dottorato di ricerca", 8, 8, ["dottorato", "dottorato di ricerca", "phd"]),
    ],
    "États-Unis": [
        ("high school diploma", 3, None, ["high school", "hs diploma"]),
        ("associate degree", 5, None, ["associate s degree", "associates degree", "associate degree"]),
        ("bachelor's degree", 6, None, ["bachelor", "bachelors degree", "college degree"]),
        ("master's degree", 7, None, ["master", "masters degree"]),
        ("doctorate", 8, None, ["phd", "doctoral degree"]),
    ],
}

# alias de pays -> nom canonique
_ALIAS_PAYS = {
    "france": "France",
    "allemagne": "Allemagne", "germany": "Allemagne", "deutschland": "Allemagne",
    "royaume uni": "Royaume-Uni", "uk": "Royaume-Uni", "united kingdom": "Royaume-Uni",
    "angleterre": "Royaume-Uni", "grande bretagne": "Royaume-Uni", "great britain": "Royaume-Uni",
    "espagne": "Espagne", "spain": "Espagne", "espana": "Espagne",
    "italie": "Italie", "italy": "Italie", "italia": "Italie",
    "etats unis": "États-Unis", "usa": "États-Unis", "us": "États-Unis",
    "united states": "États-Unis", "amerique": "États-Unis",
}


def _construire_index():
    """Construit, par pays, un dict {clé normalisée -> entrée} et la liste ordonnée des entrées."""
    par_pays = {}
    for pays, entrees in _CATALOGUE_BRUT.items():
        idx = {}
        ordonnees = []
        for nom, cite, cec, alias in entrees:
            entree = {"nom": nom, "cite": cite, "cec": cec, "pays": pays}
            ordonnees.append(entree)
            cles = [nom] + list(alias)
            for c in cles:
                idx[_norm(c)] = entree
        par_pays[pays] = {"index": idx, "entrees": ordonnees}
    return par_pays


_INDEX = _construire_index()


# ── résolution pays / diplôme (abstention stricte hors catalogue) ────────────────────────────────────────────────
def _resoudre_pays(pays) -> str:
    cle = _norm(pays)
    if cle in _ALIAS_PAYS:
        return _ALIAS_PAYS[cle]
    raise ValueError(f"pays hors catalogue (abstention) : {pays!r}")


def _resoudre_diplome(diplome, pays) -> dict:
    p = _resoudre_pays(pays)
    cle = _norm(diplome)
    idx = _INDEX[p]["index"]
    if cle not in idx:
        raise ValueError(f"diplôme hors catalogue pour {p} (abstention) : {diplome!r}")
    return _INDEX[p]["index"][cle]


# ── API : cadres CITE / CEC ──────────────────────────────────────────────────────────────────────────────────────
def _exige_entier(x, mini, maxi, nom):
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError(f"{nom} : entier attendu, reçu {x!r} (les bool sont refusés)")
    if x < mini or x > maxi:
        raise ValueError(f"{nom} hors domaine [{mini}..{maxi}] (abstention) : {x}")
    return x


def niveau_cite(code: int) -> str:
    """Intitulé du niveau CITE/ISCED 2011 `code` (0..8). Hors 0..8 -> ValueError."""
    _exige_entier(code, _CITE_MIN, _CITE_MAX, "niveau CITE")
    return _CITE[code]


def niveau_cec(n: int) -> str:
    """Descripteur du niveau CEC/EQF `n` (1..8), fondé sur les ACQUIS d'apprentissage. Hors 1..8 -> ValueError."""
    _exige_entier(n, _CEC_MIN, _CEC_MAX, "niveau CEC")
    return _CEC[n]


def nombre_niveaux_cite() -> int:
    """Nombre de niveaux CITE/ISCED 2011 = 9 (codes 0 à 8)."""
    return len(_CITE)


def nombre_niveaux_cec() -> int:
    """Nombre de niveaux CEC/EQF = 8 (codes 1 à 8)."""
    return len(_CEC)


# ── API : catalogue par pays ─────────────────────────────────────────────────────────────────────────────────────
def catalogue_pays() -> tuple:
    """Liste triée des pays du catalogue."""
    return tuple(sorted(_INDEX))


def diplomes(pays) -> tuple:
    """Noms canoniques des diplômes catalogués pour `pays` (triés). Pays inconnu -> ValueError."""
    p = _resoudre_pays(pays)
    return tuple(sorted(e["nom"] for e in _INDEX[p]["entrees"]))


def cite(diplome, pays) -> int:
    """Niveau CITE/ISCED 2011 du diplôme NOMMÉ `diplome` du `pays`. Diplôme/pays hors catalogue -> ValueError."""
    return _resoudre_diplome(diplome, pays)["cite"]


def cec(diplome, pays) -> int:
    """Niveau CEC/EQF du diplôme `diplome` du `pays`. S'ABSTIENT (ValueError) hors de l'espace CEC (ex. États-Unis)."""
    e = _resoudre_diplome(diplome, pays)
    if e["cec"] is None:
        raise ValueError(
            f"niveau CEC indéfini pour {e['nom']} ({e['pays']}) : pays hors de l'espace CEC/EQF (abstention)")
    return e["cec"]


# ── API : comparabilité de NIVEAU (JAMAIS reconnaissance) ────────────────────────────────────────────────────────
def equivalent(diplome1, pays1, pays2) -> dict:
    """Diplômes de `pays2` au MÊME niveau CITE que `diplome1` de `pays1`.

    Rend {'meme_niveau_cite': [noms triés], 'niveau_cite': int, 'avertissement': ...}. L'avertissement énonce
    que la comparabilité de NIVEAU n'emporte PAS reconnaissance (voir reconnaissance_juridique). Entrées hors
    catalogue -> ValueError.
    """
    e1 = _resoudre_diplome(diplome1, pays1)
    p2 = _resoudre_pays(pays2)
    niveau = e1["cite"]
    memes = sorted(e["nom"] for e in _INDEX[p2]["entrees"] if e["cite"] == niveau)
    return {
        "meme_niveau_cite": memes,
        "niveau_cite": niveau,
        "avertissement": _AVERTISSEMENT,
    }


def reconnaissance_juridique(diplome, pays_origine, pays_accueil):
    """ABSTENTION STRUCTURELLE : ce module ne délivre AUCUNE reconnaissance.

    Valide les entrées (pour ne pas masquer une faute de saisie), puis lève TOUJOURS ValueError : la
    reconnaissance académique/professionnelle relève des autorités nationales (ENIC-NARIC) et, pour les
    professions réglementées, de la directive 2005/36/CE.
    """
    _resoudre_diplome(diplome, pays_origine)
    _resoudre_pays(pays_accueil)
    raise ValueError(
        "la reconnaissance relève des autorités nationales — ENIC-NARIC ; ce module ne la délivre pas")
