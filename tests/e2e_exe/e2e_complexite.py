# -*- coding: utf-8 -*-
"""BATTERIE COMPLEXITÉ / COMPRÉHENSION / MÉMOIRE MASSIVE (en processus, source + base complète).
Teste ce que les batteries factuelles ne couvrent pas : compositions à N sauts, raisonnement multi-étapes,
compréhension de phrases longues/tordues, et MÉMOIRE MASSIVE (longue conversation, rappel du bon élément)."""
import sys, random
sys.path.insert(0, "/mnt/c/Users/yohan/Download/Provara/interface")
sys.path.insert(0, "/mnt/c/Users/yohan/Download/Provara/src")
import repond as R
import conversation

RND = random.Random(7)

def ask(mem, cid, q):
    try:
        return (R.repond(mem, cid, q, pleine=True) or "")
    except Exception as e:
        return "EXC %r" % e

def bloc(nom, cas):
    mem = conversation.MemoireConversation(racine=None)
    ok = 0; probs = []
    for i,(q,exp) in enumerate(cas):
        rep = ask(mem, "%s-%d"%(nom,i), q)
        low = rep.lower()
        abst = ("pas l'information" in low or "internet est coupé" in low or "m'abstiens" in low
                or "structure de ta question" in low or "pas ce fait" in low)
        if exp is None:
            good = not abst
        elif exp.startswith("!"):
            good = exp[1:] not in low.split("—")[0]
        else:
            good = exp.lower() in low
        if good: ok += 1
        else: probs.append((q, rep[:70].replace("\n"," ")))
    print("\n--- %s : %d/%d ---" % (nom, ok, len(cas)))
    for q,d in probs: print("  ✗ %s\n      -> %s" % (q,d))
    return ok, len(cas)

# COMPOSITION / N-SAUTS / RAISONNEMENT COMPLEXE
COMPO = [
 ("quelle est la population de la capitale de la France ?", None),
 ("quelle est la monnaie du pays le plus peuplé d'Afrique ?", None),
 ("sur quel continent se trouve le pays dont la capitale est Tokyo ?", "asie"),
 ("quelle est la capitale du pays le plus vaste du monde ?", "moscou"),
 ("quelle est la langue du pays où se trouve la tour Eiffel ?", None),
 ("le pays le plus peuplé d'Europe est-il plus peuplé que le Japon ?", None),
 ("quelle est la superficie du plus grand pays d'Amérique du Sud ?", None),
 ("qui dirige le pays dont la capitale est Berlin ?", None),
]
# COMPRÉHENSION : phrases longues, tordues, indirectes
COMPREH = [
 ("dis-moi, si tu le sais, quelle pourrait bien être la capitale de ce grand pays qu'est l'Australie", "canberra"),
 ("j'aimerais beaucoup savoir qui a bien pu écrire ce fameux roman qu'est 1984", "orwell"),
 ("entre nous, tu saurais pas par hasard combien de gens vivent en France ?", None),
 ("bon alors, cette histoire de capitale du Japon, c'est quoi déjà ?", "tokyo"),
 ("franchement je me demande quelle est la monnaie utilisée là-bas au Japon", "yen"),
 ("une question qui me trotte : le chat, c'est bien un félin non ?", "oui"),
]
# MÉMOIRE MASSIVE : longue conversation, rappel
def memoire_massive():
    mem = conversation.MemoireConversation(racine=None)
    cid = "mem-massive"
    # on INJECTE beaucoup d'énoncés utilisateur — par le VRAI chemin serveur (ajoute_message INDEXE le
    # message ; repond() seul ne l'indexe pas -> un harness qui l'appelle directement mesure 0/6 à tort)
    import serveur as S
    faits = [
     "je m'appelle Yohan", "mon plat préféré est la raclette", "ma couleur préférée est le bleu",
     "j'habite à Lyon", "mon chien s'appelle Rex", "je travaille dans l'informatique",
     "ma voiture est une Peugeot", "mon film préféré est Inception", "je suis né en 1990",
     "mon sport préféré est le tennis",
    ]
    for f in faits:
        S.ajoute_message(mem, cid, f)
    # QUESTIONS de rappel — le bon élément parmi 10
    checks = [
     ("comment je m'appelle ?", "yohan"),
     ("quel est mon plat préféré ?", "raclette"),
     ("quelle est ma couleur préférée ?", "bleu"),
     ("où j'habite ?", "lyon"),
     ("comment s'appelle mon chien ?", "rex"),
     ("quel est mon sport préféré ?", "tennis"),
    ]
    ok=0; probs=[]
    for q,exp in checks:
        rep = R.repond(mem, cid, q, pleine=True) or ""
        if exp in rep.lower(): ok+=1
        else: probs.append((q, rep[:60]))
    print("\n--- MÉMOIRE MASSIVE : %d/%d ---" % (ok,len(checks)))
    for q,d in probs: print("  ✗ %s -> %s" % (q,d))
    return ok, len(checks)

def main():
    t=[0,0]
    for nom,cas in [("COMPOSITION",COMPO),("COMPRÉHENSION",COMPREH)]:
        a,b = bloc(nom,cas); t[0]+=a; t[1]+=b
    a,b = memoire_massive(); t[0]+=a; t[1]+=b
    print("\n===== TOTAL complexité/compréhension/mémoire : %d/%d =====" % (t[0],t[1]))

if __name__=="__main__":
    main()
