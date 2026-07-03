"""BASES DE DONNÉES — algèbre relationnelle EXACTE, FAUX=0 (mission formule/concept 2026-06-29).

Opérations de l'algèbre relationnelle sur des tables (listes de lignes = dictionnaires colonne→valeur) : sélection
(restriction par un prédicat), projection (sous-ensemble de colonnes), jointure interne (sur une clé commune),
union / différence ensemblistes, agrégats (count/sum/min/max/avg). Mécanisme EXACT, déterministe. Abstention
STRUCTURELLE : colonne absente, opérateur inconnu, schémas incompatibles -> ValueError.

Couvre le sujet borné « Bases de données » (volet algèbre relationnelle, calculable).
Vérifié en adverse par `valide_bases_donnees.py` (sélection/projection/jointure/agrégats connus).
"""
from __future__ import annotations

_OPS = {
    "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
}


def _table(t, nom="table"):
    if not isinstance(t, (list, tuple)) or any(not isinstance(r, dict) for r in t):
        raise ValueError(f"{nom} : liste de lignes (dictionnaires) attendue")
    return t


def selection(table, colonne, operateur, valeur):
    """Restriction σ : lignes où `colonne operateur valeur` est vrai. ValueError si colonne/opérateur invalide."""
    _table(table)
    if operateur not in _OPS:
        raise ValueError(f"opérateur inconnu : {operateur!r}")
    op = _OPS[operateur]
    out = []
    for r in table:
        if colonne not in r:
            raise ValueError(f"colonne absente : {colonne!r}")
        try:
            if op(r[colonne], valeur):
                out.append(dict(r))
        except TypeError:
            raise ValueError("comparaison de types incompatibles")
    return out


def projection(table, colonnes):
    """Projection π : ne garde que `colonnes` (dans l'ordre), en éliminant les doublons. ValueError si colonne absente."""
    _table(table)
    if not isinstance(colonnes, (list, tuple)) or not colonnes:
        raise ValueError("liste de colonnes non vide requise")
    out = []
    vus = set()
    for r in table:
        for c in colonnes:
            if c not in r:
                raise ValueError(f"colonne absente : {c!r}")
        ligne = {c: r[c] for c in colonnes}
        cle = tuple(ligne[c] for c in colonnes)
        if cle not in vus:
            vus.add(cle)
            out.append(ligne)
    return out


def jointure(t1, t2, cle):
    """Jointure interne ⋈ sur la colonne `cle` commune. Combine les lignes de même valeur de clé."""
    _table(t1, "t1")
    _table(t2, "t2")
    for r in t1:
        if cle not in r:
            raise ValueError(f"clé absente dans t1 : {cle!r}")
    index = {}
    for r in t2:
        if cle not in r:
            raise ValueError(f"clé absente dans t2 : {cle!r}")
        index.setdefault(r[cle], []).append(r)
    out = []
    for r in t1:
        for s in index.get(r[cle], []):
            fusion = dict(r)
            fusion.update(s)
            out.append(fusion)
    return out


def union(t1, t2):
    """Union ensembliste (lignes distinctes ; les deux tables doivent avoir le même schéma)."""
    _table(t1, "t1")
    _table(t2, "t2")
    if t1 and t2 and set(t1[0]) != set(t2[0]):
        raise ValueError("schémas incompatibles pour l'union")
    out, vus = [], set()
    for r in list(t1) + list(t2):
        cle = tuple(sorted(r.items()))
        if cle not in vus:
            vus.add(cle)
            out.append(dict(r))
    return out


def difference(t1, t2):
    """Différence t1 − t2 (lignes de t1 absentes de t2)."""
    _table(t1, "t1")
    _table(t2, "t2")
    cles_t2 = {tuple(sorted(r.items())) for r in t2}
    return [dict(r) for r in t1 if tuple(sorted(r.items())) not in cles_t2]


def agregat(table, colonne, fonction: str):
    """Agrégat sur `colonne` : 'count' | 'sum' | 'min' | 'max' | 'avg'. ValueError si fonction/colonne invalide."""
    _table(table)
    if fonction == "count":
        return len(table)
    valeurs = []
    for r in table:
        if colonne not in r:
            raise ValueError(f"colonne absente : {colonne!r}")
        valeurs.append(r[colonne])
    if not valeurs:
        raise ValueError("agrégat sur table vide")
    if fonction == "min":
        return min(valeurs)
    if fonction == "max":
        return max(valeurs)
    if fonction == "sum":
        return sum(valeurs)
    if fonction == "avg":
        return sum(valeurs) / len(valeurs)
    raise ValueError(f"fonction d'agrégat inconnue : {fonction!r}")


if __name__ == "__main__":
    employes = [{"id": 1, "nom": "Alice", "dept": "R&D"}, {"id": 2, "nom": "Bob", "dept": "Vente"},
                {"id": 3, "nom": "Carl", "dept": "R&D"}]
    salaires = [{"id": 1, "salaire": 50}, {"id": 2, "salaire": 40}, {"id": 3, "salaire": 60}]
    print("σ dept=R&D :", selection(employes, "dept", "==", "R&D"))
    print("π nom :", projection(employes, ["nom"]))
    print("⋈ sur id :", jointure(employes, salaires, "id"))
    print("avg salaire :", agregat(salaires, "salaire", "avg"))
    print("count R&D :", agregat(selection(employes, "dept", "==", "R&D"), "id", "count"))
