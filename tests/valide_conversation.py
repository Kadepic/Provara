"""
MÉMOIRE DE CONVERSATION — validation (mandat Yohan 2026-06-25, « fossé de l'intelligence éphémère »).

Critères de MORT (chaque check = un échec possible) — la brique doit résoudre EXACTEMENT le problème du post :
  1. RÉTENTION + REPRISE VERBATIM : on retrouve ce qui a été dit, dans l'ordre, mot pour mot.
  2. FENÊTRE DE REPRISE bornée : `reprend(n)` ne rend que les n derniers (coût constant sur un historique immense).
  3. NON BORNÉ PAR LE CONTEXTE : le bon tour est rappelé parmi un historique massif (1000+ tours de bruit).
  4. SOUNDNESS / FAUX=0 : une requête sans rapport ne ramène RIEN (jamais une invention/reformulation).
  5. DÉPÔT-POUR-LE-SUIVANT (cross-conversation) : l'agent B retrouve la réponse déposée par l'agent A.
  6. FRONTIÈRE PUBLIC/PRIVÉ : un rappel global (public) ne fuite JAMAIS une conversation privée.
  7. PERSISTANCE DURABLE : rechargé depuis le disque, le contenu est identique (survit aux runs / au /clear).
  8. RGPD — EFFACEMENT RÉEL : `oublie` supprime mémoire + index + fichier (plus aucune trace, plus aucun rappel).
  9. PERTINENCE ORDONNÉE : le tour le plus pertinent sort en tête (score idf décroissant).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from garde_ressources import borne
from conversation import MemoireConversation


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    with tempfile.TemporaryDirectory() as d:
        racine = str(Path(d) / "conv")
        m = MemoireConversation(racine=racine)

        # — Agent A règle un bug, conversation PUBLIQUE (déposée pour les suivants). —
        m.ajoute("agentA", "user", "le build casse avec ELIFECYCLE sur npm run build", scope="public")
        m.ajoute("agentA", "ia", "supprime node_modules et package-lock puis npm ci regle le ELIFECYCLE", scope="public")
        # bruit massif : 1200 tours sans rapport (l'historique « déborde » une fenêtre LLM).
        for i in range(1200):
            m.ajoute("agentA", "user", f"remarque anodine numero {i} sur la meteo et les nuages gris", scope="public")

        # 1. RÉTENTION + REPRISE VERBATIM.
        tous = m.reprend("agentA")
        r.append(_check("RÉTENTION + REPRISE VERBATIM : 1er tour intact, ordre préservé",
                        len(tous) == 1202 and tous[0]["texte"] == "le build casse avec ELIFECYCLE sur npm run build"
                        and tous[1]["role"] == "ia" and tous[0]["seq"] == 0 and tous[-1]["seq"] == 1201))

        # 2. FENÊTRE DE REPRISE bornée.
        fenetre = m.reprend("agentA", n=3)
        r.append(_check("FENÊTRE DE REPRISE bornée : reprend(n=3) -> 3 derniers tours seulement",
                        len(fenetre) == 3 and fenetre[-1]["seq"] == 1201))

        # 3. NON BORNÉ PAR LE CONTEXTE : retrouver le bug parmi 1202 tours.
        res = m.rappelle("npm run build ELIFECYCLE casse", conv_id="agentA", k=3)
        textes = [x["texte"] for x in res]
        r.append(_check(f"NON BORNÉ PAR LE CONTEXTE : bug rappelé parmi {len(m)} tours ({len(res)} hits)",
                        any("ELIFECYCLE" in t for t in textes)))

        # 4. SOUNDNESS / FAUX=0 : requête sans rapport -> rien.
        rien = m.rappelle("recette de tarte aux pommes et caramel", conv_id="agentA", k=5)
        r.append(_check("SOUNDNESS FAUX=0 : requête sans rapport -> AUCUN tour (zéro invention)", rien == []))

        # 5. DÉPÔT-POUR-LE-SUIVANT : agent B (autre conversation publique) retrouve la réponse d'agent A.
        m.ajoute("agentB", "user", "comment importer un module python depuis un sous-dossier", scope="public")
        global_res = m.rappelle("ELIFECYCLE npm ci node_modules", k=2)   # conv_id=None -> toutes (public)
        r.append(_check("DÉPÔT-POUR-LE-SUIVANT : rappel cross-conversation retrouve le fix d'agentA",
                        any(x["conv"] == "agentA" and "ELIFECYCLE" in x["texte"] for x in global_res)))

        # 6. FRONTIÈRE PUBLIC/PRIVÉ : un secret privé ne fuite pas dans un rappel global (public par défaut).
        m.ajoute("agentC", "user", "mon token secret de prod est ELIFECYCLE-xyz-konami-42", scope="prive")
        fuite = m.rappelle("ELIFECYCLE", k=10)                            # global => public uniquement
        r.append(_check("FRONTIÈRE PUBLIC/PRIVÉ : le rappel global ne fuite AUCUNE conversation privée",
                        all(x["conv"] != "agentC" for x in fuite)
                        and m.rappelle("ELIFECYCLE", conv_id="agentC", scope="prive") != []))  # mais accessible ciblé

        # 7. PERSISTANCE DURABLE : recharger depuis le disque -> contenu identique.
        m2 = MemoireConversation(racine=racine)
        rel = m2.rappelle("ELIFECYCLE npm ci", k=2)
        r.append(_check("PERSISTANCE DURABLE : rechargé du disque, le fix est toujours rappelable",
                        len(m2) == len(m) and any("ELIFECYCLE" in x["texte"] for x in rel)
                        and m2.reprend("agentA")[0]["texte"] == tous[0]["texte"]))

        # 8. RGPD — EFFACEMENT RÉEL.
        avant = len(m2)
        efface = m2.oublie("agentA")
        m3 = MemoireConversation(racine=racine)                          # re-relecture disque = preuve de suppression
        r.append(_check("RGPD EFFACEMENT RÉEL : oublie() purge mémoire + index + disque (plus aucun rappel)",
                        efface and "agentA" not in m2.conversations() and len(m2) < avant
                        and m3.rappelle("ELIFECYCLE", conv_id="agentA") == []
                        and "agentA" not in m3.conversations()))

        # 9. PERTINENCE ORDONNÉE : le tour le plus spécifique sort en tête. Corpus de 5 (en corpus de 2, tout terme
        #    partagé a le même idf -> pas d'ordre testable ; 5 tours dont 2 pertinents donnent un classement net).
        m4 = MemoireConversation(racine=None)
        m4.ajoute("x", "ia", "le chat noir dort", scope="public")
        m4.ajoute("x", "ia", "le chat noir dort sur le tapis rouge du salon", scope="public")
        m4.ajoute("x", "ia", "la voiture rouge roule vite", scope="public")
        m4.ajoute("x", "ia", "le soleil brille fort aujourd hui", scope="public")
        m4.ajoute("x", "ia", "il pleut dehors ce matin", scope="public")
        ord_res = m4.rappelle("chat noir tapis rouge salon", conv_id="x", k=5)
        scores = [x["score"] for x in ord_res]
        r.append(_check("PERTINENCE ORDONNÉE : le tour le plus pertinent sort en tête (score idf décroissant)",
                        len(ord_res) >= 2 and "tapis rouge" in ord_res[0]["texte"]
                        and scores == sorted(scores, reverse=True)))

    n = len(r)
    print()
    print(f"=== valide_conversation : {sum(r)}/{n} ===" if all(r) else f"ÉCHEC — {sum(r)}/{n}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
