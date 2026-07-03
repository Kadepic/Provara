"""SAVOIR_MASSIF — le lexique branché comme ressource des briques SENS, VÉRIFIÉ sur une petite taxonomie inline
(reproductible, sans le fichier massif). Prouve que est_un/ancetre_commun/chemin/distance/intrus raisonnent via le
SOUS-GRAPHE extrait à la demande, et que syn/ant sont lus du lexique. Garde anti-cycle testée."""
from __future__ import annotations
from savoir_massif import SavoirMassif


def _e(hyper=None, syn=None, ant=None):
    return {"classe": "nom", "genre": None, "definition": "", "hyper": hyper, "syn": syn or [], "ant": ant or []}


# Petite taxonomie (mêmes branches que les valide_* : chat/chien -> mammifère -> animal ; voiture séparée) + un cycle.
LEX = {
    "chat": _e("félin", syn=["matou", "minet"]),
    "félin": _e("mammifère"),
    "mammifère": _e("animal"),
    "animal": _e(None),
    "chien": _e("canidé"),
    "canidé": _e("mammifère"),
    "voiture": _e("engin", syn=["auto", "bagnole"]),
    "engin": _e(None),
    "chaud": _e(None, ant=["froid"]),
    # cycle réel (a -> b -> a) : la remontée d'ascendance doit terminer (garde anti-cycle).
    "a": _e("b"),
    "b": _e("a"),
}


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    sav = SavoirMassif(LEX)
    r = []

    r.append(_check("est_un : chat->animal oui (transitif), animal->chat non (dirigé), chat->voiture non",
                    sav.est_un("chat", "animal") is True and sav.est_un("animal", "chat") is False
                    and sav.est_un("chat", "voiture") is False))

    r.append(_check("ancetre_commun(chat, chien) = mammifère ; (chat, voiture) = None (branches disjointes)",
                    sav.ancetre_commun("chat", "chien") == "mammifère"
                    and sav.ancetre_commun("chat", "voiture") is None))

    r.append(_check("chemin(chat, animal) = [chat, félin, mammifère, animal]",
                    sav.chemin("chat", "animal") == ["chat", "félin", "mammifère", "animal"]))

    r.append(_check("distance(chat, chien) = 4 (chat-félin-mammifère-canidé-chien, non dirigé)",
                    sav.distance("chat", "chien") == 4))

    r.append(_check("intrus([chat, chien, voiture]) = voiture (hors de la branche animal)",
                    sav.intrus(["chat", "chien", "voiture"]) == "voiture"))

    r.append(_check("syn/ant lus du lexique : synonymes(voiture) ⊇ {auto}, contraires(chaud) = [froid]",
                    "auto" in sav.synonymes("voiture") and sav.contraires("chaud") == ["froid"]))

    r.append(_check("ANTI-CYCLE : ancetres('a') termine sur le cycle a<->b",
                    sav.ancetres("a") == ["a", "b"]))

    print()
    print(f"SAVOIR_MASSIF VALIDÉ — {len(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
