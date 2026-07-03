"""
PALIER 2 — PARADOXE DE SIMPSON : une tendance vraie dans CHAQUE sous-groupe peut s'INVERSER une fois agrégée (brique
87, 2026-06-27).

Un traitement A peut avoir un meilleur taux de succès que B dans CHAQUE strate (petits calculs ET gros calculs) et
pourtant un taux GLOBAL inférieur — parce que A a été davantage administré à la strate la plus DIFFICILE. Conclure à
partir de l'agrégat (« B est meilleur ») OU des strates (« A est meilleur ») SANS identifier la variable confondante
est SUR-CONFIANT : la bonne réponse dépend de la STRUCTURE CAUSALE (la strate est-elle un confondeur — alors stratifier
— ou un médiateur — alors agréger ?). Les données SEULES ne tranchent pas.

LE MODE D'ÉCHEC DÉMASQUÉ : prendre l'agrégat (ou les sous-groupes) au pied de la lettre quand il y a renversement est
sur-confiant ; l'attitude honnête est de DÉTECTER le renversement et de SIGNALER que la conclusion dépend du modèle
causal (cf. [[causal]] pour l'estimation de l'effet sous confusion). ABSTENTION si données incohérentes. Pur Python.
"""
from __future__ import annotations

ABSTENTION = "abstention"
SIMPSON = "simpson"
COHERENT = "coherent"


def taux(succes, total):
    return succes / total if total > 0 else 0.0


def taux_strates(donnees, traitement):
    """Taux par strate pour un traitement. `donnees` = {traitement: {strate: (succès, total)}}."""
    return {s: taux(*donnees[traitement][s]) for s in donnees[traitement]}


def taux_agrege(donnees, traitement):
    """Taux global (poolé) d'un traitement."""
    sc = sum(donnees[traitement][s][0] for s in donnees[traitement])
    tt = sum(donnees[traitement][s][1] for s in donnees[traitement])
    return taux(sc, tt)


def gagnant_par_strate(donnees, a, b):
    """Renvoie 'a'/'b'/None : le traitement qui gagne dans TOUTES les strates (None si pas unanime)."""
    ta, tb = taux_strates(donnees, a), taux_strates(donnees, b)
    if all(ta[s] > tb[s] for s in ta):
        return a
    if all(tb[s] > ta[s] for s in tb):
        return b
    return None


def gagnant_agrege(donnees, a, b):
    return a if taux_agrege(donnees, a) > taux_agrege(donnees, b) else b


def analyse(donnees, a, b):
    """Façade : (SIMPSON, infos) s'il y a renversement, (COHERENT, infos) sinon, ou (ABSTENTION, raison)."""
    if a not in donnees or b not in donnees or not donnees[a] or set(donnees[a]) != set(donnees[b]):
        return (ABSTENTION, "traitements/strates incohérents")
    g_str = gagnant_par_strate(donnees, a, b)
    g_agg = gagnant_agrege(donnees, a, b)
    info = {"gagnant_strates": g_str, "gagnant_agrege": g_agg,
            "agrege": {a: taux_agrege(donnees, a), b: taux_agrege(donnees, b)},
            "strates": {a: taux_strates(donnees, a), b: taux_strates(donnees, b)}}
    if g_str is not None and g_str != g_agg:
        return (SIMPSON, info)
    return (COHERENT, info)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    if res[0] == SIMPSON:
        return (f"⚠ PARADOXE DE SIMPSON : {i['gagnant_strates']} gagne dans CHAQUE strate, mais {i['gagnant_agrege']} "
                f"gagne globalement. Conclure d'un seul niveau serait sur-confiant — la réponse dépend du modèle causal.")
    return f"Pas de renversement : {i['gagnant_agrege']} gagne (strates et agrégat concordent)."


if __name__ == "__main__":
    print("=== PARADOXE DE SIMPSON (calculs rénaux) ===\n")
    d = {"A": {"petit": (81, 87), "gros": (192, 263)},
         "B": {"petit": (234, 270), "gros": (55, 80)}}
    print(f"  petits : A={taux(81,87):.2f} vs B={taux(234,270):.2f} ; gros : A={taux(192,263):.2f} vs B={taux(55,80):.2f}")
    print(f"  agrégé : A={taux_agrege(d,'A'):.2f} vs B={taux_agrege(d,'B'):.2f}")
    print(" ", formule(analyse(d, "A", "B")))
