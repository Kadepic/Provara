"""
PALIER 2 — RÉVÉLATION BAYÉSIENNE & DÉPENDANCE AU PROTOCOLE (Monty Hall) : ignorer COMMENT l'information a été révélée est
sur-confiant (brique 99, 2026-06-27).

Face à une donnée, la vraisemblance P(donnée | hypothèse) dépend du PROTOCOLE qui l'a produite — pas seulement de ce qui
est observé en surface. Le réflexe « deux possibilités restantes ⇒ 50/50 » est SUR-CONFIANT : il assigne 0.5 à un
événement dont la vraie probabilité peut être 1/3 ou 2/3, parce qu'il ne CONDITIONNE pas sur le mécanisme de révélation.

Monty Hall : 3 portes, une voiture, le joueur choisit la porte 1, une porte-CHÈVRE s'ouvre.
  • Protocole ANIMATEUR INFORMÉ (ouvre toujours une chèvre, jamais la porte du joueur) : P(voiture derrière l'autre porte
    fermée | observation) = 2/3 ⇒ il FAUT changer.
  • Protocole ALÉATOIRE (l'animateur ouvre une porte au hasard parmi les deux autres ; on conditionne sur « c'était une
    chèvre ») : posterior = 1/2 ⇒ changer ou rester est indifférent.
La MÊME observation de surface (« une chèvre est révélée ») donne des posteriors DIFFÉRENTS selon le protocole. Assumer un
protocole — ou n'en tenir aucun compte (« 50/50 ») — est donc sur-confiant : le réel fixe la réponse via le mécanisme.

LE MODE D'ÉCHEC DÉMASQUÉ : le forecaster naïf « 50/50 » est mal calibré (Brier/log-loss pires que le bayésien correct
sous le protocole animateur). Conditionner sur le protocole rétablit la calibration. ABSTENTION si protocole inconnu.
Pur Python ; vérifié par simulation (rng seedé).
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ANALYSE = "analyse"
PROTOCOLES = ("animateur", "aleatoire")


def _vraisemblance(protocole, voiture, joueur, ouverte):
    """P(l'animateur ouvre 'ouverte' ET c'est une chèvre | voiture, choix du joueur) selon le protocole."""
    if ouverte == joueur or ouverte == voiture:
        # l'animateur n'ouvre jamais la porte du joueur ; s'il ouvre la voiture ce n'est pas une chèvre
        if ouverte == voiture:
            return 0.0 if protocole == "animateur" else 0.0  # condition « chèvre révélée » ⇒ exclut la voiture
        return 0.0
    autres = [d for d in (0, 1, 2) if d != joueur]            # portes que l'animateur peut envisager
    if protocole == "animateur":
        chevres = [d for d in autres if d != voiture]         # il ne choisit qu'entre les chèvres
        return 1.0 / len(chevres) if ouverte in chevres else 0.0
    else:  # aléatoire : ouvre uniformément parmi 'autres' ; on garde le cas « chèvre »
        return 1.0 / len(autres) if ouverte != voiture else 0.0


def posterior(protocole, joueur, ouverte):
    """Loi a posteriori de la position de la voiture, sachant le protocole, le choix du joueur et la porte ouverte."""
    prior = 1.0 / 3.0
    post = {}
    for voiture in (0, 1, 2):
        post[voiture] = prior * _vraisemblance(protocole, voiture, joueur, ouverte)
    z = sum(post.values())
    if z == 0:
        return None
    return {k: v / z for k, v in post.items()}


def prob_gain_changer(protocole, joueur=0, ouverte=2):
    """P(gagner en CHANGEANT) = posterior sur la porte fermée autre que celle du joueur."""
    post = posterior(protocole, joueur, ouverte)
    if post is None:
        return None
    fermee = [d for d in (0, 1, 2) if d != joueur and d != ouverte][0]
    return post[fermee]


def simule(protocole, n, rng, changer=True, joueur=0):
    """Vérification Monte-Carlo : taux de gain de la stratégie (changer/rester) sous le protocole."""
    gains = 0
    valides = 0
    for _ in range(n):
        voiture = rng.randrange(3)
        autres = [d for d in (0, 1, 2) if d != joueur]
        if protocole == "animateur":
            chevres = [d for d in autres if d != voiture]
            ouverte = chevres[rng.randrange(len(chevres))]
        else:
            ouverte = autres[rng.randrange(len(autres))]
            if ouverte == voiture:
                continue                                      # on conditionne sur « chèvre révélée »
        valides += 1
        fermee = [d for d in (0, 1, 2) if d != joueur and d != ouverte][0]
        choix = fermee if changer else joueur
        gains += (choix == voiture)
    return gains / valides


def brier_naif_vs_bayes(protocole, joueur=0, ouverte=2):
    """Score de Brier du forecaster naïf (50/50) vs bayésien correct, sur l'issue 'changer gagne' sous le protocole."""
    p_vrai = prob_gain_changer(protocole, joueur, ouverte)
    # Brier attendu = E[(p_prevu − issue)²] avec issue~Bernoulli(p_vrai)
    def brier(p_prevu):
        return p_vrai * (p_prevu - 1) ** 2 + (1 - p_vrai) * (p_prevu - 0) ** 2
    return brier(0.5), brier(p_vrai)


def analyse(protocole):
    """Façade. (ANALYSE, {protocole, post, p_changer, brier_naif, brier_bayes}) ou (ABSTENTION, raison)."""
    if protocole not in PROTOCOLES:
        return (ABSTENTION, "protocole de révélation inconnu — la vraisemblance n'est pas définie")
    post = posterior(protocole, 0, 2)
    p_ch = prob_gain_changer(protocole)
    b_naif, b_bayes = brier_naif_vs_bayes(protocole)
    return (ANALYSE, {"protocole": protocole, "post": post, "p_changer": p_ch,
                      "brier_naif": b_naif, "brier_bayes": b_bayes})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    if i["brier_naif"] > i["brier_bayes"] + 1e-9:
        diag = (f"le réflexe « 50/50 » est sur-confiant (Brier naïf {i['brier_naif']:.3f} > bayésien "
                f"{i['brier_bayes']:.3f})")
    else:
        diag = "ici le « 50/50 » se trouve correct — mais par coïncidence du protocole, pas par raisonnement valide"
    return (f"Protocole « {i['protocole']} » : P(gagner en changeant) = {i['p_changer']:.3f} ; {diag}. La même "
            f"observation de surface donne un posterior DIFFÉRENT selon le MÉCANISME de révélation — ignorer le protocole "
            f"est sur-confiant.")


if __name__ == "__main__":
    import random
    print("=== RÉVÉLATION BAYÉSIENNE / DÉPENDANCE AU PROTOCOLE (Monty Hall) ===\n")
    for proto in PROTOCOLES:
        st, info = analyse(proto)
        sim = simule(proto, 200000, random.Random(0), changer=True)
        print(f"  {proto:10s}: P(changer gagne) théorie={info['p_changer']:.3f} simulation={sim:.3f}")
        print("            ", formule((st, info)))
