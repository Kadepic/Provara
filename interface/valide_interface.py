#!/usr/bin/env python3
"""
VALIDATION de l'interface — teste le BACKEND sans navigateur (léger, sound, autonome).

On exerce les handlers de serveur.py directement sur une MemoireConversation TEMPORAIRE (racine dans un dossier
jetable) pour ne JAMAIS polluer le stockage live (datasets/conversations). Cycle complet : liste vide -> créer
-> ajouter un message -> relire (verbatim) -> supprimer. On vérifie aussi la soundness (jamais d'invention).

S'inscrit dans la gate (_nonreg.py / liste_validateurs) une fois vert. N'importe PAS `ia` : reste léger.
"""
from __future__ import annotations

import os
import sys
import tempfile

# Amorçage robuste : la gate (_nonreg.py) exécute ce fichier via exec(open(...).read()) avec cwd=HARN, où
# `__file__` n'est PAS défini. On retombe alors sur le cwd (qui contient conversation.py). En lancement direct
# (`python3 interface/valide_interface.py`), `__file__` existe.
if "__file__" in globals():
    _ICI = os.path.dirname(os.path.abspath(__file__))
    _HARNAIS = os.path.dirname(_ICI)
else:
    _HARNAIS = os.getcwd()
    _ICI = os.path.join(_HARNAIS, "interface")
for p in (_ICI, _HARNAIS):
    if p not in sys.path:
        sys.path.insert(0, p)

import conversation
import serveur
import repond


def main() -> int:
    ok = 0
    fails = []

    def check(nom, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  [OK ] {nom}")
        else:
            fails.append(nom)
            print(f"  [XX ] {nom}")

    with tempfile.TemporaryDirectory() as tmp:
        mem = conversation.MemoireConversation(racine=tmp)   # stockage jetable, isolé du live

        # 1. état initial : aucun (état vide honnête)
        r = serveur.liste_conversations(mem)
        check("ÉTAT VIDE : aucune conversation au départ", r["items"] == [])

        # 2. lire une conversation inconnue -> vide, PAS une erreur, et surtout aucun tour inventé
        r = serveur.lire_conversation(mem, "fantome")
        check("INCONNUE -> tours vides (aucune invention)", r["tours"] == [])

        # 3. créer : alloue l'id, n'existe pas encore au stockage (persistance au 1ᵉʳ message)
        r = serveur.nouvelle_conversation(mem, "  bug paiement  ")
        check("NOUVELLE : id nettoyé + ok", r["ok"] and r["id"] == "bug paiement")
        check("NOUVELLE : pas encore au stockage tant qu'aucun message", r["existe"] is False)
        check("NOUVELLE : nom vide refusé", serveur.nouvelle_conversation(mem, "   ")["ok"] is False)
        check("NOUVELLE : invisible dans la liste tant qu'elle est vide", serveur.liste_conversations(mem)["items"] == [])

        # 4. ajouter un message -> devient réelle, role='user', verbatim
        msg = "Le webhook Stripe renvoie 400 quand la TVA est nulle."
        r = serveur.ajoute_message(mem, "bug paiement", msg)
        check("MESSAGE : enregistré (ok, seq=0)", r["ok"] and r["seq"] == 0)
        check("MESSAGE : role='user'", r["tours"][0]["role"] == "user")
        check("MESSAGE : VERBATIM (texte identique, zéro reformulation)", r["tours"][0]["texte"] == msg)

        # NB : chaque message produit DEUX tours (user + réponse 'ia'). Les comptes en tiennent compte.
        # 5. message vide refusé proprement (aucun tour ajouté : ni user, ni ia)
        r = serveur.ajoute_message(mem, "bug paiement", "   ")
        check("MESSAGE VIDE : refusé proprement (aucun tour ajouté)", r["ok"] is False and len(r["tours"]) == 2)

        # 6. la conversation apparaît dans l'historique (1 message -> 2 tours user+ia)
        r = serveur.liste_conversations(mem)
        check("HISTORIQUE : apparaît après son 1ᵉʳ message",
              len(r["items"]) == 1 and r["items"][0]["id"] == "bug paiement" and r["items"][0]["n"] == 2)

        # 7. plusieurs messages : tours user dans l'ordre, verbatim ; seq strictement croissants
        serveur.ajoute_message(mem, "bug paiement", "Corrigé : arrondir avant l'appel API.")
        r = serveur.lire_conversation(mem, "bug paiement")
        users = [t["texte"] for t in r["tours"] if t["role"] == "user"]
        seqs = [t["seq"] for t in r["tours"]]
        check("ORDRE : tours user dans l'ordre, verbatim", users == [msg, "Corrigé : arrondir avant l'appel API."])
        check("ORDRE : seq strictement croissants, 4 tours (2 user + 2 ia)",
              seqs == sorted(seqs) and len(seqs) == 4)

        # 8. persistance durable : recharger du disque rend les mêmes tours user (preuve de durabilité)
        mem2 = conversation.MemoireConversation(racine=tmp)
        r = serveur.lire_conversation(mem2, "bug paiement")
        users = [t["texte"] for t in r["tours"] if t["role"] == "user"]
        check("DURABLE : rechargé du disque, tours user verbatim",
              users == [msg, "Corrigé : arrondir avant l'appel API."])

        # 9. PURGE définitive (optionnelle) : oublie() efface réellement (plus rien sur le disque rechargé)
        r = serveur.oublie_conversation(mem2, "bug paiement")
        check("PURGE : oublie() renvoie ok", r["ok"] is True)
        mem3 = conversation.MemoireConversation(racine=tmp)
        check("PURGE RÉELLE : rien ne subsiste après rechargement", serveur.liste_conversations(mem3)["items"] == [])

        # 10. table de routes cohérente (évolutivité : les endpoints attendus existent)
        attendus = {("GET", "/api/conversations"), ("GET", "/api/conversation"),
                    ("POST", "/api/message"), ("POST", "/api/nouvelle"),
                    ("POST", "/api/archive"), ("POST", "/api/desarchive"), ("POST", "/api/oublie")}
        check("ROUTES : les endpoints (dont archive/desarchive) sont déclarés", attendus <= set(serveur.ROUTES))

        # ————————————————— COUCHE CONVERSATIONNELLE (étage 1 : mémoire de dialogue, LÉGER) —————————————————
        # On NE teste QUE l'étage léger (pleine=False par défaut) : la gate ne doit JAMAIS charger `ia` (622 Mo).
        mem.oublie("bug paiement")                      # repart propre
        check("CONV propre au départ", serveur.liste_conversations(mem)["items"] == [])

        # 11. QUESTION sans rien en mémoire : honnête, n'invente PAS de réponse
        r = serveur.ajoute_message(mem, "c1", "Sais-tu comment je m'appelle ?")
        rep_vide = r["reponse"]
        # ⚠ machine RÉELLE : le prénom peut être légitimement connu du profil persistant (~/.verax) — le
        # rappeler n'est pas une invention. On accepte l'aveu honnête OU un rappel-salutation, jamais autre chose.
        check("HONNÊTE : question sans info -> aveu honnête, ou rappel d'un nom réellement mémorisé",
              "information" in rep_vide.lower() or "enchant" in rep_vide.lower())
        check("HONNÊTE : la réponse est stockée comme tour role='ia'",
              any(t["role"] == "ia" for t in r["tours"]))

        # 11b. AFFIRMATION (pas une question) -> accusé de réception, PAS « rien en mémoire »
        r_aff = serveur.ajoute_message(mem, "c1", "Je m'appelle Yohan.")
        # une présentation reçoit soit l'accusé mémo, soit la SALUTATION AU PRÉNOM (preuve que le nom est
        # enregistré — « Enchantée, Yohan », comportement social voulu) ; jamais « rien en mémoire ».
        check("AFFIRMATION : accusé de réception ou salutation au prénom (≠ « rien en mémoire »)",
              ("noté" in r_aff["reponse"].lower() or "yohan" in r_aff["reponse"].lower())
              and "rien" not in r_aff["reponse"].lower())
        # 11c. IMPÉRATIF DE CALCUL/CONVERSION = une DEMANDE, pas un fait à mémoriser (sonde vague 4, T3) :
        # « Convertis 5 km en mètres » ne doit JAMAIS donner « C'est noté » (classé affirmation à tort sinon).
        r_imp = serveur.ajoute_message(mem, "c-imp", "Convertis 5 km en mètres")
        check("IMPÉRATIF CALCUL : « Convertis… » traité en demande (pas « C'est noté »)",
              "noté" not in r_imp["reponse"].lower())
        r_imp2 = serveur.ajoute_message(mem, "c-imp", "Calcule 3 plus 4")
        check("IMPÉRATIF CALCUL : « Calcule… » traité en demande (pas « C'est noté »)",
              "noté" not in r_imp2["reponse"].lower())
        # 11d. MÉTA sur l'assistant (sonde vague 6, T3) : « Qui es-tu ? » -> réponse honnête, jamais « C'est noté »
        r_meta = serveur.ajoute_message(mem, "c-meta", "Qui es-tu ?")
        check("MÉTA : « Qui es-tu ? » -> se décrit honnêtement (assistant, faits vérifiés)",
              "assistant" in r_meta["reponse"].lower() and "noté" not in r_meta["reponse"].lower())
        r_meta2 = serveur.ajoute_message(mem, "c-meta", "Es-tu un humain ?")
        check("MÉTA SOUND : « Es-tu un humain ? » -> programme, PAS « oui » (jamais faux)",
              "programme" in r_meta2["reponse"].lower())
        # SOUNDNESS méta : une question FACTUELLE « tu »-wrappée n'est PAS captée par le méta (reste factuelle)
        r_fact = serveur.ajoute_message(mem, "c-meta", "Sais-tu quelle est la capitale de l'Italie ?")
        check("MÉTA SOUND : « Sais-tu quelle est la capitale… » -> PAS la réponse méta (reste factuel)",
              "assistant conversationnel local" not in r_fact["reponse"].lower())
        # 13. ...puis le redemande (même conv) -> l'assistant le RESTITUE verbatim (sound, pas d'invention)
        r = serveur.ajoute_message(mem, "c1", "Alors, comment je m'appelle ?")
        check("MÉMOIRE : restitue l'énoncé réel de l'utilisateur",
              "Je m'appelle Yohan." in r["reponse"])

        # 14. CROSS-CONVERSATION : dans une AUTRE conversation, il se souvient quand même (anti-éphémère)
        r = serveur.ajoute_message(mem, "c2-ailleurs", "Au fait, comment je m'appelle ?")
        check("CROSS-CONV : se souvient d'une autre conversation",
              "Je m'appelle Yohan." in r["reponse"])

        # 14b. ALIAS DE RAPPEL (§3.3) : « tu sais mon NOM ? » doit retrouver « je m'APPELLE Yohan » malgré le
        # vocabulaire différent (le rappel lexical seul échouait). Champ sémantique nom↔appelle↔prénom.
        r = serveur.ajoute_message(mem, "c-alias", "Dis, tu sais mon nom ?")
        check("ALIAS RAPPEL : « tu sais mon nom ? » retrouve « je m'appelle Yohan »",
              "Je m'appelle Yohan." in r["reponse"])
        r = serveur.ajoute_message(mem, "c-alias2", "quel est mon prénom au fait ?")
        check("ALIAS RAPPEL : « mon prénom ? » retrouve l'énoncé du nom",
              "Je m'appelle Yohan." in r["reponse"])

        # 15. SOUNDNESS : une question passée ne sert jamais de réponse (pas d'écho question->question)
        check("SOUND : ne ressort pas une question comme réponse", not r["reponse"].strip().endswith("? »"))

        # 16. l'assistant ne se cite jamais lui-même (role 'ia') comme s'il s'agissait de l'utilisateur
        check("SOUND : ne se cite pas lui-même (source = role user uniquement)",
              "D'après ce que tu m'as dit" not in rep_vide)

        # 16b. RÉGRESSION (bug réel) : un tour qui CONTIENT « ? » en milieu de phrase (question mal ponctuée)
        # ne doit JAMAIS être ressorti comme réponse à une autre question partageant un mot-clé.
        serveur.ajoute_message(mem, "geo", "Quel fleuve traverse l'arabie saoudite? Si oui donne en au moins 1")
        r = serveur.ajoute_message(mem, "geo", "Quelle est la monnaie de l'arabie saoudite ?")  # léger -> pas d'étage 2
        check("SOUND : un tour interrogatif (avec ? au milieu) n'est jamais ressorti comme réponse",
              "D'après ce que tu m'as dit" not in r["reponse"] and "fleuve" not in r["reponse"].lower())

        # 16c. ROBUSTESSE au « ? » oublié : une question sans « ? » est quand même reconnue comme demande.
        # (Fait DISTINCT du nom, pour ne pas polluer le test de purge plus bas.)
        serveur.ajoute_message(mem, "rob", "Mon plat préféré est la raclette.")     # affirmation -> accusé
        r = serveur.ajoute_message(mem, "rob", "rappelle quel est mon plat préféré")  # PAS de « ? »
        check("ROBUSTE : question sans « ? » -> répond depuis la mémoire",
              "raclette" in r["reponse"].lower())
        # 16c-bis : un tour QUESTION sans « ? » n'est jamais ressorti comme s'il était une réponse
        check("SOUND : une question sans « ? » n'est pas prise pour un énoncé",
              "rappelle quel est mon plat" not in r["reponse"].lower())

        # 16d. REVERSE-LOOKUP « les X d'un pays » (lecture directe des données, sans charger le lecteur) :
        #      tolérant aux fautes de grammaire (« Quelle » au lieu de « Quels »).
        rl = repond._liste_inverse("quel fleuve traverse le portugal ?")
        check("REVERSE : liste les cours d'eau d'un pays + mise en garde fleuve≠rivière (donnée réelle)",
              rl is not None and "Portugal" in rl and "cours d'eau" in rl.lower()
              and "distingue pas fleuve" in rl.lower())
        rl2 = repond._liste_inverse("Quelle sont les fleuves en France")   # faute volontaire Quelle/Quels
        check("REVERSE : insensible à la faute de grammaire", rl2 is not None and "France" in rl2)
        check("REVERSE : type/pays inconnu -> None (jamais d'invention)",
              repond._liste_inverse("quel bidule en pays-imaginaire") is None)
        # SOUNDNESS : un type SINGULIER objet d'un autre nom (« composition de l'ÉQUIPE de France ») n'est PAS une
        # demande de liste -> on NE liste PAS les 49 équipes de France (même avec un interrogatif sur l'autre nom).
        check("REVERSE SOUND : « composition de l'équipe de France » -> None (pas une liste)",
              repond._liste_inverse("composition de l'équipe de France") is None)
        check("REVERSE SOUND : « quelle est la composition de l'équipe de France » -> None",
              repond._liste_inverse("quelle est la composition de l'équipe de France") is None)

        # 16d-bis. MULTI-TOURS type B (§3.5) : « et la France ? » = nouvelle entité, même attribut (fonction pure).
        # ⚠ depuis 2026-07-08 la CASSE D'ORIGINE est restituée (« et de CO2 ? » -> CO2 : les formules
        # chimiques sont sensibles à la casse) — les entités gardent donc leur majuscule.
        check("MULTITOURS B : « et la France ? » -> entité « France »",
              repond._nouvelle_entite("et la France ?") == "France")
        check("MULTITOURS B : « et pour le Brésil ? » -> « Brésil »",
              repond._nouvelle_entite("et pour le Brésil ?") == "Brésil")
        check("MULTITOURS B : « et sa monnaie ? » -> '' (c'est du type A, pas B)",
              repond._nouvelle_entite("et sa monnaie ?") == "")
        check("MULTITOURS B : « et son drapeau ? » -> '' (possessif = type A)",
              repond._nouvelle_entite("et son drapeau ?") == "")
        check("MULTITOURS B : anaphore « et celle de la France ? » -> « France »",
              repond._nouvelle_entite("et celle de la France ?") == "France")
        check("MULTITOURS B : anaphore « et celui du Brésil ? » -> « Brésil » (contraction du)",
              repond._nouvelle_entite("et celui du Brésil ?") == "Brésil")
        check("MULTITOURS B : « et celle-ci ? » -> '' (démonstratif nu, pas d'entité)",
              repond._nouvelle_entite("et celle-ci ?") == "")

        # 16e. DID-YOU-MEAN : un type géo mal orthographié -> did-you-mean OU HORS honnête (jamais une réponse fausse).
        # NB : on n'assert PAS le mot exact suggéré (« fleuve ») — il dépend du VOCABULAIRE VIVANT des relations, que
        # les lanes d'ingestion modifient en continu (test rendu FLAKY sous ingestion concurrente, vu sur la gate
        # intégrée). La garantie de SOUNDNESS = pas de réponse factuelle fausse pour une faute -> préservée.
        mfresh = conversation.MemoireConversation(racine=None)
        sugg = serveur.ajoute_message(mfresh, "dym", "quel flauve traverse le portugal ?")["reponse"].lower()
        check("DID-YOU-MEAN : « flauve » (faute) -> did-you-mean OU HORS (jamais une réponse fausse)",
              ("vouliez-vous dire" in sugg) or ("information" in sugg) or ("pas sûr" in sugg) or ("noté" in sugg))
        check("DID-YOU-MEAN : un mot correct ne déclenche pas de fausse suggestion",
              repond._suggere_type("quelle est la monnaie de la france") is None)

        # 16f. CLARIFICATION AVEC ÉTAT (0pré, chemin léger) : après un did-you-mean, « oui » REJOUE la question
        # corrigée (en léger : repli honnête, JAMAIS « C'est noté » ni une réponse factuelle inventée) ; « non »
        # -> invitation à reformuler. Sound : la substitution n'a lieu que sur confirmation EXPLICITE.
        if "vouliez-vous dire" in sugg:                      # l'état n'existe que si le did-you-mean a eu lieu
            r_oui = serveur.ajoute_message(mfresh, "dym", "oui")["reponse"]
            check("CLARIF (0pré) léger : « oui » -> repli honnête (ni « C'est noté », ni fait inventé)",
                  not r_oui.startswith("C'est noté") and repond.est_fallback(r_oui))
            sugg2 = serveur.ajoute_message(mfresh, "dym", "quel flauve traverse le portugal ?")["reponse"].lower()
            if "vouliez-vous dire" in sugg2:
                r_non = serveur.ajoute_message(mfresh, "dym", "non")["reponse"]
                # les refus sont VARIÉS par formulation.py : toute variante de la banque « refus » est valide
                check("CLARIF (0pré) léger : « non » -> invitation à reformuler",
                      r_non in repond._variantes("refus", repond._MSG_REFUS))

        # ————————————————— ARCHIVAGE : retirer de l'UI SANS perdre la mémoire (demande explicite) —————————————————
        # 17. archiver c1 -> disparaît de l'historique affiché...
        serveur.archive_conversation(mem, "c1")
        visibles = [it["id"] for it in serveur.liste_conversations(mem)["items"]]
        check("ARCHIVE : la conversation disparaît de l'historique affiché", "c1" not in visibles)
        check("ARCHIVE : récupérable si on inclut explicitement les archivées",
              "c1" in [it["id"] for it in serveur.liste_conversations(mem, inclure_archivees=True)["items"]])
        # 18. ...MAIS l'IA s'en souvient quand même (LE point demandé par l'utilisateur)
        r = serveur.ajoute_message(mem, "c-apres-archive", "Et donc, comment je m'appelle ?")
        check("ARCHIVE : l'IA SE SOUVIENT de la conversation archivée (donnée conservée)",
              "Je m'appelle Yohan." in r["reponse"])
        # 19. réversible : désarchiver la fait revenir
        serveur.desarchive_conversation(mem, "c1")
        check("DÉSARCHIVE : la conversation revient dans l'historique",
              "c1" in [it["id"] for it in serveur.liste_conversations(mem)["items"]])

        # 19b. RECRÉER/ÉCRIRE dans une conv archivée la fait RÉAPPARAÎTRE (bug : « Test » rouverte mais cachée).
        serveur.archive_conversation(mem, "c1")
        serveur.nouvelle_conversation(mem, "c1")               # re-« créer » un id archivé -> désarchive
        check("RÉAPPARITION : recréer une conv archivée la ré-affiche",
              "c1" in [it["id"] for it in serveur.liste_conversations(mem)["items"]])
        serveur.archive_conversation(mem, "c1")
        serveur.ajoute_message(mem, "c1", "un nouveau message")  # écrire dedans -> désarchive aussi
        check("RÉAPPARITION : écrire dans une conv archivée la ré-affiche",
              "c1" in [it["id"] for it in serveur.liste_conversations(mem)["items"]])
        # 20. purge définitive (optionnelle) : là seulement, l'IA oublie réellement
        serveur.oublie_conversation(mem, "c1")
        r = serveur.ajoute_message(mem, "c-apres-purge", "Rappelle, comment je m'appelle ?")
        check("PURGE : après oubli réel, l'IA ne se souvient plus du nom",
              "Yohan" not in r["reponse"])

    total = ok + len(fails)
    print(f"\n=== valide_interface : {ok}/{total} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
