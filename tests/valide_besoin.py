"""VALIDE besoin.py — couche objectif/besoin du moteur d'invention. FAUX=0, adverse.

Vérifie : (1) le REFRAMING (le but réel = évacuer les ~100 W du corps, pas refroidir l'air) ; (2) la décomposition
en canaux physiques établis ; (3) l'ASYMÉTRIE contrat d'atome : coherence_physique RÉFUTE l'impossible et ne
promeut JAMAIS en fait (les principes cohérents restent des SUPPOSITIONS) ; (4) le besoin inconnu -> HORS (le manque
visible) ; (5) le transfert inter-domaines (stratégies naturelles réduites à des leviers) ; (6) le pont physique."""
import atome as A
import besoin as B

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


# ── 1) REFRAMING + 2) décomposition ──
d = B.decompose("rafraichir une piece")
check(d["statut"] == "decompose", "besoin connu -> decompose")
check("corps" in d["objectif_reel"].lower() and "100" in d["objectif_reel"], "objectif réel = évacuer ~100 W du corps")
check(d["charge_corps_W"] == 100, "charge du corps ~100 W")
canaux = {c.canal for c in d["canaux"]}
check(canaux == {"rayonnement", "conduction", "convection", "evaporation"}, f"4 canaux d'échange du corps ({canaux})")
check(all(c.grandeur == "chaleur" for c in d["canaux"]), "chaque canal nomme la grandeur physique (chaleur)")
# le mouvement d'air (convection) est le seul non silencieux -> cohérent avec l'exigence de silence
conv = [c for c in d["canaux"] if c.canal == "convection"][0]
check(conv.silencieux is False, "convection (mouvement d'air) marquée NON silencieuse (ventilateur = bruit)")
ray = [c for c in d["canaux"] if c.canal == "rayonnement"][0]
check(ray.silencieux is True, "rayonnement (surface froide) silencieux")

# ── 3) ASYMÉTRIE : réfute l'impossible, ne promeut jamais en fait ──
pr = B.principes("rafraichir une piece")
check(pr["statut"] == "principes", "principes pour besoin connu")
par_nom = {e["nom"]: e for e in pr["liste"]}
# les impossibles -> atome RÉFUTÉ
coolzy = par_nom["boîte fermée sans évacuation (type Coolzy)"]
check(coolzy["atome"].statut == A.REFUTE, "boîte fermée sans rejet -> RÉFUTÉ (2nd principe)")
check(A.est_refute(coolzy["atome"].contenu), "contenu réfuté enregistré dans la garde anti-blanchiment")
carnot = par_nom["pompe magique COP 40 (ΔT 10 K)"]
check(carnot["atome"].statut == A.REFUTE, "COP 40 > Carnot -> RÉFUTÉ")
# les cohérents -> SUPPOSITION (JAMAIS FAIT) + confiance dans ]0,1[
for nom in ("échange direct avec l'eau du réseau (~15 °C)", "magnétocalorique (réfrigération magnétique)",
            "compression de vapeur (clim classique)"):
    e = par_nom[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION (cohérent ≠ prouvé)")
    check(0.0 < e["atome"].confiance < 1.0, f"{nom} confiance dans ]0,1[")
# INVARIANT CLÉ : coherence_physique ne promeut JAMAIS un principe en FAIT
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in pr["liste"]),
      "aucun principe promu en FAIT (la cohérence n'est pas une preuve d'efficacité)")
# effets sous-exploités présents (magnéto/élasto/électro caloriques)
noms = set(par_nom)
check(any("magnétocalorique" in n for n in noms) and any("mécanocalorique" in n for n in noms)
      and any("électrocalorique" in n for n in noms), "effets caloriques sous-exploités présents")
# métadonnées silence/solide honnêtes
eau = par_nom["échange direct avec l'eau du réseau (~15 °C)"]
check(eau["silencieux"] is True and eau["solide_sans_gaz"] is True, "échange eau = silencieux + sans gaz")
clim = par_nom["compression de vapeur (clim classique)"]
check(clim["silencieux"] is False, "clim à compression marquée bruyante (référence à dépasser)")

# ── 4) besoin INCONNU -> HORS (le manque visible) ──
check(B.decompose("faire pousser des plantes")["statut"] == B.HORS, "besoin inconnu -> HORS (décompose)")
check(B.principes("cuire un gateau")["statut"] == B.HORS, "besoin inconnu -> HORS (principes)")
check(B.HORS in B.objectif_reel("voyager dans le temps"), "objectif d'un besoin inconnu -> HORS")

# ── 5) transfert inter-domaines (stratégies naturelles) ──
nat = B.strategies_naturelles()
check(len(nat) >= 4, "plusieurs stratégies naturelles")
check(any("forêt" in s["exemple"] for s in nat), "la forêt est une stratégie répertoriée")
check(all(s["leviers"] and s["lecon"] for s in nat), "chaque stratégie réduite à des leviers + une leçon")

# ── 6) pont physique vers substrat_physique ──
ch = B.chaines_physiques(sources=("magnetisme", "lumiere"), cible="chaleur")
check(any(c["source"] == "magnetisme" and c["statut"] for c in ch), "pont substrat_physique renvoie un statut")
check(B.chaines_physiques(sources=("grandeur_bidon",), cible="chaleur")[0]["statut"] == B.HORS,
      "grandeur inconnue -> HORS (pas d'invention à l'aveugle)")

# ── déterminisme ──
check(B.decompose("rafraichir une piece")["objectif_reel"] == B.decompose("rafraichir une piece")["objectif_reel"],
      "décomposition déterministe")

print(f"\n=== valide_besoin : {ok}/{ok + ko} ===")
import sys

sys.exit(0 if ko == 0 else 1)
