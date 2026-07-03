"""VALIDE transfert.py — l'assembleur inter-domaines. FAUX=0, adverse.

Vérifie : (1) composition de candidats-stacks ; (2) GARDE PHYSIQUE — aucun candidat réfuté ni sans puits ;
(3) ASYMÉTRIE — tout candidat reste une SUPPOSITION (jamais FAIT) ; (4) classement par score ; (5) « voir ce qui
manque » non vide ; (6) GÉNÉRICITÉ — besoin inconnu -> HORS (pas câblé en dur sur le refroidissement)."""
import atome as A
import transfert as T

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


r = T.transfere("rafraichir une piece")
check(r["statut"] == "candidats", "besoin connu -> candidats")
cands = r["candidats"]
check(len(cands) >= 1, "au moins un candidat composé")

# (3) ASYMÉTRIE : tout candidat est une SUPPOSITION, jamais un FAIT
check(all(c.atome.statut == A.SUPPOSITION for c in cands), "tout candidat reste SUPPOSITION (jamais promu en FAIT)")
check(all(0.0 < c.atome.confiance < 1.0 for c in cands), "confiance de chaque candidat dans ]0,1[")

# (2) GARDE PHYSIQUE : aucun principe RÉFUTÉ dans les candidats, et un PUITS réel partout
titres = " ".join(c.titre.lower() for c in cands)
check("boîte fermée" not in titres and "coolzy" not in titres, "aucun candidat n'utilise le principe RÉFUTÉ (boîte fermée)")
check("cop 40" not in titres and "magique" not in titres, "aucun candidat n'utilise le principe RÉFUTÉ (COP 40)")
check(all(c.puits and "aucun" not in c.puits.lower() for c in cands), "chaque candidat nomme un PUITS réel (pas de froid gratuit)")

# (4) classement par score décroissant
check(all(cands[i].score >= cands[i + 1].score for i in range(len(cands) - 1)), "candidats classés par score décroissant")
# le meilleur cible le corps (livraison rayonnement/conduction) -> efficience
check(cands[0].livraison in ("rayonnement", "conduction"), "meilleur candidat livre au CORPS (surface/contact frais)")
# chaque candidat porte une inspiration naturelle (transfert inter-domaines)
check(all(c.inspiration_nature for c in cands), "chaque candidat porte une inspiration naturelle (biomimétisme)")
# composants explicites (dont réduction d'apports)
check(all(any("principe" in x for x in c.composants) for c in cands), "composants explicites listés")

# (5) « voir ce qui manque »
check(isinstance(r["manque"], list) and len(r["manque"]) >= 1, "diagnostic 'ce qui manque' non vide")

# (6) GÉNÉRICITÉ / honnêteté : besoin inconnu -> HORS (pas d'invention à l'aveugle, pas hardcodé)
check(T.transfere("faire du pain")["statut"] == T.HORS, "besoin inconnu -> HORS (transfere)")
check(T.transfere("piloter un avion")["statut"] == T.HORS, "autre besoin inconnu -> HORS (générique)")
check(T.manque("faire du pain")[0].lower().find("non modélis") >= 0, "manque() sur inconnu -> signale le besoin non modélisé")

# déterminisme
r2 = T.transfere("rafraichir une piece")
check([c.titre for c in r2["candidats"]] == [c.titre for c in cands], "composition déterministe")

print(f"\n=== valide_transfert : {ok}/{ok + ko} ===")
import sys

sys.exit(0 if ko == 0 else 1)
