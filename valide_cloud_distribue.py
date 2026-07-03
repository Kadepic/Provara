"""VALIDE cloud_distribue.py — ADVERSE, FAUX=0. Hachage cohérent (placement déterministe + STABILITÉ : retirer un
nœud ne déplace que ses clés), quorum R+W>N, CAP + SOUNDNESS (aucun nœud / params invalides -> ValueError)."""
import cloud_distribue as D

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


NOEUDS = ["n1", "n2", "n3", "n4"]

# DÉTERMINISME du placement
check(D.noeud_responsable("cle-X", NOEUDS) == D.noeud_responsable("cle-X", NOEUDS), "placement déterministe")
check(D.noeud_responsable("cle-X", NOEUDS) in NOEUDS, "le responsable est un nœud existant")

# STABILITÉ : en retirant un nœud, SEULES les clés de ce nœud sont déplacées (propriété clé du consistent hashing)
cles = [f"objet-{i}" for i in range(200)]
avant = {c: D.noeud_responsable(c, NOEUDS) for c in cles}
sans_n4 = [n for n in NOEUDS if n != "n4"]
apres = {c: D.noeud_responsable(c, sans_n4) for c in cles}
deplaces = [c for c in cles if avant[c] != apres[c]]
check(all(avant[c] == "n4" for c in deplaces), "retrait de n4 : seules ses clés bougent (stabilité)")
check(all(apres[c] == avant[c] for c in cles if avant[c] != "n4"), "les clés des autres nœuds ne bougent pas")
check(len(deplaces) < len(cles), "la majorité des clés restent en place")

# QUORUM (R+W>N -> cohérence forte)
check(D.quorum_coherent(3, 2, 2) is True, "N=3,R=2,W=2 -> 4>3 cohérent")
check(D.quorum_coherent(3, 1, 1) is False, "N=3,R=1,W=1 -> 2<3 incohérent")
check(D.quorum_coherent(3, 3, 1) is True, "N=3,R=3,W=1 -> 4>3 cohérent")
check(D.quorum_coherent(5, 3, 3) is True and D.quorum_coherent(5, 2, 3) is False, "N=5 : R+W>5 requis")

# CAP
check(D.cap_choix(True, "coherence") == "CP", "partition + cohérence -> CP")
check(D.cap_choix(True, "disponibilite") == "AP", "partition + disponibilité -> AP")
check(D.cap_choix(False, "coherence") == "CA", "pas de partition -> CA")
check(D.facteur_replication_disponibilite(3, 2) is True and D.facteur_replication_disponibilite(3, 3) is False,
      "N=3 tolère 2 pannes mais pas 3")

# SOUNDNESS
check(leve(D.noeud_responsable, "x", []), "aucun nœud -> ValueError")
check(leve(D.quorum_coherent, 3, 4, 1), "R>N -> ValueError")
check(leve(D.quorum_coherent, 3, 0, 1), "R<1 -> ValueError")
check(leve(D.cap_choix, True, "autre"), "préférence inconnue -> ValueError")

print(f"\n=== valide_cloud_distribue : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
