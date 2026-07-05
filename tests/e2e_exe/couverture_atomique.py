# -*- coding: utf-8 -*-
"""COUVERTURE ATOMIQUE EXHAUSTIVE : génère des questions depuis CHAQUE relation de la base (1369) en
échantillonnant de vraies paires (entité, valeur), pose « <tête> de <entité> ? » et vérifie que la VRAIE valeur
apparaît dans la réponse. Mesure end-to-end quelle relation est atteignable ET correcte par le moteur conversationnel.
Sortie : couverture par relation + agrégat par FAMILLE + liste des relations à 0 % (trous à combler).
En processus (source + base complète) pour tenir la dizaine de milliers de questions.
Usage : LECTEUR_DATASETS_DIR=… python3 couverture_atomique.py [N_par_relation]"""
import json, os, sys, random, re

sys.path.insert(0, "/mnt/c/Users/yohan/Download/Provara/interface")
sys.path.insert(0, "/mnt/c/Users/yohan/Download/Provara/src")
import repond as R
import conversation

DOS = os.environ.get("LECTEUR_DATASETS_DIR", "/mnt/c/Users/yohan/.verax/datasets/lecteur")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
RND = random.Random(42)

def echantillon(rel, k):
    """k paires (entite, valeur) aléatoires d'une relation, en lisant seulement le début si le fichier est gros."""
    chemin = os.path.join(DOS, rel + ".jsonl")
    paires = []
    try:
        taille = os.path.getsize(chemin)
        with open(chemin, encoding="utf-8") as f:
            # gros fichier : on lit un bloc du début + un bloc du milieu pour varier
            lignes = []
            for i, l in enumerate(f):
                if i > 4000:
                    break
                lignes.append(l)
        objs = []
        for l in lignes:
            l = l.strip()
            if not l or '"_relation"' in l:
                continue
            try:
                o = json.loads(l)
            except ValueError:
                continue
            e, v = o.get("entite"), o.get("valeur")
            if e and v and len(str(e)) < 40:
                objs.append((str(e), str(v)))
        RND.shuffle(objs)
        paires = objs[:k]
    except OSError:
        pass
    return paires

def question_pour(head, entite):
    """Question naturelle « <head> de <entité> »."""
    return "quel est le %s de %s ?" % (head, entite)

def main():
    mem = conversation.MemoireConversation(racine=None)
    rels = sorted(f[:-6] for f in os.listdir(DOS) if f.endswith(".jsonl"))
    # relations à IGNORER (méta/techniques : code, plan, format, role_partie… non conversationnelles)
    skip_prefix = ("code_", "plan_", "format_", "role_partie", "definition_terme", "fonction_partie")
    par_rel = {}
    par_fam = {}
    total_q = 0
    cid = 0
    n_rel = 0
    for rel in rels:
        if rel.startswith(skip_prefix):
            continue
        n_rel += 1
        if n_rel % 100 == 0:
            print("  … %d relations traitées, %d questions" % (n_rel, total_q), flush=True)
        head = rel.split("_")[0]
        if len(head) < 3:
            continue
        paires = echantillon(rel, N)
        if not paires:
            continue
        ok = 0; tot = 0; faux = 0
        for ent, val in paires:
            cid += 1; total_q += 1; tot += 1
            q = question_pour(head, ent)
            try:
                rep = (R.repond(mem, "cov-%d" % cid, q, pleine=True) or "").lower()
            except Exception:
                rep = ""
            # normalise la valeur attendue pour la recherche
            nv = R._normalise(val)
            abst = ("pas l'information" in rep or "internet est coupé" in rep or "m'abstiens" in rep
                    or "structure de ta question" in rep or "pas ce fait" in rep)
            if nv and nv[:24] in R._normalise(rep):
                ok += 1
            elif not abst and rep and val[:1].lower() not in ("", " "):
                # a répondu quelque chose SANS la vraie valeur ET sans abstenir -> potentiel FAUX
                # (on tolère les listes/reformulations : on ne compte FAUX que si réponse courte affirmative)
                if len(rep) < 80:
                    faux += 1
        par_rel[rel] = (ok, tot, faux)
        fam = head
        a, t, fx = par_fam.get(fam, (0, 0, 0))
        par_fam[fam] = (a + ok, t + tot, fx + faux)
    # rapport
    print("\n===== COUVERTURE PAR FAMILLE (résolu/total, faux) =====")
    for fam, (a, t, fx) in sorted(par_fam.items(), key=lambda kv: kv[1][1], reverse=True):
        if t >= 3:
            print("  %-22s %3d/%-3d (%3.0f%%)  faux=%d" % (fam, a, t, 100 * a / t, fx))
    print("\n===== RELATIONS À 0%% (trous — aucune paire résolue) =====")
    zero = [r for r, (a, t, fx) in sorted(par_rel.items()) if t >= 3 and a == 0]
    print("  nombre :", len(zero))
    for r in zero[:80]:
        print("   ", r)
    glob_ok = sum(a for a, t, fx in par_rel.values())
    glob_tot = sum(t for a, t, fx in par_rel.values())
    glob_faux = sum(fx for a, t, fx in par_rel.values())
    print("\nGLOBAL : %d/%d résolus (%.0f%%)  |  faux potentiels : %d  |  relations testées : %d  |  questions : %d"
          % (glob_ok, glob_tot, 100 * glob_ok / max(glob_tot, 1), glob_faux, len(par_rel), total_q))

if __name__ == "__main__":
    main()
