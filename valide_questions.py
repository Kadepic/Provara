"""RÉPONDEUR IA — questions/réponses unifiées model-free (démonstration de l'étendue SANS modèle).
VARIÉTÉ : 7 types de questions naturelles, chacune routée vers sa capacité et correcte. HONNÊTE : hors-portée ->
« je ne sais pas » / inconnu (jamais d'invention)."""
from __future__ import annotations

from questions import FAITS, RepondeurIA


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    ia = RepondeurIA(FAITS)
    r = []
    cas = [
        ("définition", "qu'est-ce qu'un chat ?", "petit mammifère félin domestique"),
        ("antonyme", "quel est le contraire de grand ?", "petit"),
        ("inférence oui", "le chat est-il un mammifère ?", "oui"),
        ("inférence inconnu", "le chat est-il un véhicule ?", "inconnu"),
        ("explication", "pourquoi le chat est-il un animal ?", "parce que chat → félin → mammifère → animal"),
        ("localisation", "où est le chat ?", "jardin"),
        ("ancêtre commun", "qu'ont en commun le chat et le chien ?", "mammifère"),
        ("comptage", "combien de chat, chien et voiture sont des animaux ?", 2),
        ("rôle SVO", "qui mange la souris ?", "chat"),
        ("rôle SVO 2", "qui chasse le chat ?", "chien"),
        ("temps premier", "qu'est-ce qui vient en premier ?", "lever"),
        ("temps avant", "le lever est-il avant le travail ?", "oui"),
        ("honnête hors-portée", "quelle est la capitale de la France ?", "je ne sais pas"),
    ]
    for nom, q, att in cas:
        rep = ia.repond(q)
        r.append(_check(f"{nom:<22} « {q} » -> {rep!r}", rep == att))

    # held-out : questions JAMAIS posées en démo, sur d'autres mots du lexique élargi.
    held = [
        ("le lion est-il un animal ?", "oui"),                 # transitif lion->félin->mammifère->animal
        ("quel est le contraire de chaud ?", "froid"),
        ("qu'ont en commun la rose et le chêne ?", "plante"),  # rose->fleur->plante ; chêne->arbre->plante
        ("combien de lion, tigre et voiture sont des félins ?", 2),
    ]
    for q, att in held:
        rep = ia.repond(q)
        r.append(_check(f"{'held-out':<22} « {q} » -> {rep!r}", rep == att))

    print()
    print(f"RÉPONDEUR IA VALIDÉ — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
