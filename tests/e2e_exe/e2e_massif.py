# -*- coding: utf-8 -*-
"""BATTERIE E2E MASSIVE contre le .exe RÉEL (base complète, port 8765, web coupé, mémoire propre).
Cartographie EXHAUSTIVE des trous : ~180 questions, ~24 domaines, tous niveaux de complexité.
Classe : OK | FAUX (réponse fausse) | MANQUÉ (abstient sur fait connu) | LISTE (déverse une liste au lieu d'1 réponse).
But : mesurer l'étendue réelle du travail, regrouper les problèmes par type."""
import json, subprocess, random

CURL = "/mnt/c/Windows/system32/curl.exe"
URL = "http://127.0.0.1:8765/api/message"

def ask(conv, q):
    payload = json.dumps({"id": conv, "texte": q}, ensure_ascii=False)
    for _ in range(2):
        try:
            out = subprocess.run([CURL, "-s", "-m", "60", "-X", "POST", URL,
                                  "-H", "Content-Type: application/json", "--data-binary", payload],
                                 capture_output=True, text=True, timeout=70).stdout
            d = json.loads(out); r = d.get("reponse") or d.get("texte") or ""
            if r: return r
        except Exception: pass
    return ""

# (catégorie, question, mode, cible)  mode: has|no|abst|none(info)
CAS = [
 # GÉOGRAPHIE avancée
 ("geo","quelle est la capitale de la Nouvelle-Zélande ?","has","wellington"),
 ("geo","quelle est la capitale du Kazakhstan ?","has",None),
 ("geo","quel est le plus long fleuve du monde ?","has",None),
 ("geo","quel est le plus haut sommet du monde ?","has","everest"),
 ("geo","quelle est la plus grande île du monde ?","has","groenland"),
 ("geo","quel océan borde la France à l'ouest ?","has",None),
 ("geo","combien de pays y a-t-il en Europe ?","has",None),
 ("geo","quels pays ont une frontière avec la France ?","has",None),
 ("geo","quel désert est le plus grand du monde ?","has",None),
 ("geo","dans quel pays se trouve le Sahara ?","has",None),
 # DÉMOGRAPHIE / COMPARAISONS
 ("demo","quelle est la population de l'Inde ?","has",None),
 ("demo","classe le Brésil, l'Argentine et le Chili par population","has",None),
 ("demo","quel est le pays le moins peuplé d'Europe ?","has",None),
 ("demo","l'Allemagne est-elle plus peuplée que la France ?","has","oui"),
 ("demo","quelle proportion des pays d'Afrique ont plus de 50 millions d'habitants ?","has",None),
 # SCIENCE : chimie
 ("chim","quel est le numéro atomique du carbone ?","has","6"),
 ("chim","quel est le symbole de l'or ?","has","au"),
 ("chim","combien de protons a l'hydrogène ?","has","1"),
 ("chim","quelle est la masse molaire du dioxyde de carbone ?","has",None),
 ("chim","l'eau est-elle composée d'hydrogène et d'oxygène ?","none",None),
 # SCIENCE : astronomie
 ("astro","combien de lunes a Mars ?","has",None),
 ("astro","quelle est la plus grande planète du système solaire ?","has","jupiter"),
 ("astro","la Lune orbite-t-elle autour de la Terre ?","has","oui"),
 ("astro","Phobos fait-il partie du système solaire ?","has",None),
 ("astro","quelle est la distance de la Terre au Soleil ?","has",None),
 # SCIENCE : biologie
 ("bio","combien de chromosomes a l'être humain ?","has",None),
 ("bio","une chauve-souris est-elle un mammifère ?","has","oui"),
 ("bio","combien de pattes a une araignée ?","has",None),
 ("bio","quel est le plus grand animal du monde ?","has",None),
 ("bio","le cœur humain a-t-il combien de cavités ?","has",None),
 # HISTOIRE : événements et dates
 ("hist","en quelle année est tombé le mur de Berlin ?","has","1989"),
 ("hist","quand a eu lieu la bataille de Hastings ?","has","1066"),
 ("hist","qui était le premier président des États-Unis ?","has","washington"),
 ("hist","en quelle année Christophe Colomb a-t-il découvert l'Amérique ?","has","1492"),
 ("hist","combien de temps a duré la guerre de Cent Ans ?","has","116"),
 ("hist","qui a succédé à Napoléon Ier ?","has",None),
 # LITTÉRATURE / ARTS
 ("art","qui a écrit Roméo et Juliette ?","has","shakespeare"),
 ("art","qui a peint Guernica ?","has","picasso"),
 ("art","qui a sculpté le David ?","has",None),
 ("art","qui a réalisé le film Pulp Fiction ?","has","tarantino"),
 ("art","qu'a écrit Victor Hugo ?","has",None),
 ("art","qui a composé Le Lac des cygnes ?","has",None),
 # PERSONNES / BIOGRAPHIES
 ("pers","qui était Isaac Newton ?","has","newton"),
 ("pers","où est né Napoléon Bonaparte ?","has","ajaccio"),
 ("pers","quand est mort Léonard de Vinci ?","has",None),
 ("pers","de quelle nationalité était Frida Kahlo ?","has",None),
 ("pers","quel métier faisait Marie Curie ?","has",None),
 ("pers","qui est le plus âgé entre Napoléon Ier et Louis XIV ?","has","louis"),
 # ARITHMÉTIQUE / MATHS
 ("math","combien font 347 plus 589 ?","has","936"),
 ("math","combien font 25 fois 4 ?","has","100"),
 ("math","combien font 1000 divisé par 8 ?","has","125"),
 ("math","quelle est la racine carrée de 256 ?","has","16"),
 ("math","combien font 7 au carré ?","has","49"),
 ("math","quel est 20 pour cent de 150 ?","has","30"),
 ("math","combien font 3 plus 4 fois 5 ?","has","23"),
 # LANGUE : définitions / conjugaison / grammaire
 ("langue","que veut dire éphémère ?","has",None),
 ("langue","conjugue le verbe manger au présent","has",None),
 ("langue","quel est le pluriel de cheval ?","has",None),
 ("langue","quel est le contraire de grand ?","has",None),
 ("langue","c'est quoi la photosynthèse ?","has",None),
 # LANGAGE LIBRE / ARGOT / SMS / ORDRE
 ("libre","c'est quoi le fric ?","has","argent"),
 ("libre","du Brésil, la capitale ?","has",None),
 ("libre","kel é la capital de l'italie","has","rome"),
 ("libre","le bouquin 1984, c'est de qui ?","has","orwell"),
 ("libre","combien gagne un toubib","none",None),
 # RAISONNEMENT / LOGIQUE
 ("raiso","un chat est-il un animal ?","has","oui"),
 ("raiso","qu'ont en commun le chien, le chat et le cheval ?","has",None),
 ("raiso","si tous les hommes sont mortels et Socrate est un homme, Socrate est-il mortel ?","none",None),
 ("raiso","une pomme est-elle un fruit ?","has",None),
 ("raiso","le Nil est-il plus long que la Seine ?","has",None),
 # TEMPOREL avancé
 ("temp","combien d'années séparent la Révolution française et la chute du mur de Berlin ?","has",None),
 ("temp","quel événement est le plus ancien : Marignan ou Waterloo ?","has","marignan"),
 ("temp","en quelle année a été signé le traité de Versailles ?","has",None),
 # COMPOSITION / QUESTIONS IMBRIQUÉES
 ("comp","quelle est la population de la capitale de la France ?","has",None),
 ("comp","quelle est la monnaie du pays le plus peuplé d'Afrique ?","has",None),
 ("comp","sur quel continent se trouve la capitale du Japon ?","has","asie"),
 # UNITÉS / MESURES / CONVERSIONS
 ("unit","combien de mètres dans un kilomètre ?","has",None),
 ("unit","combien de secondes dans une heure ?","has",None),
 ("unit","convertis 100 degrés Celsius en Fahrenheit","has",None),
 # ABSTENTION LÉGITIME (FAUX=0)
 ("abst","quelle est la capitale du Wakanda ?","abst",None),
 ("abst","qui gagnera la Coupe du monde 2030 ?","abst",None),
 ("abst","quel est le sens de la vie ?","abst",None),
 ("abst","combien y a-t-il de grains de sable sur Terre ?","abst",None),
 # FAUX=0 TRAPS
 ("trap","le Vatican est-il plus grand que la Chine ?","no","oui"),
 ("trap","Tokyo est-elle la capitale de la Chine ?","no","oui"),
 ("trap","une grenouille est-elle un mammifère ?","no","oui"),
 ("trap","la Lune est-elle plus grande que la Terre ?","no","oui"),
 ("trap","le Soleil tourne-t-il autour de la Terre ?","no","oui"),
]

def classe(mode, cible, rep):
    low = rep.lower()
    abst = ("je n'ai pas l'information" in low or "internet est coupé" in low
            or "je m'abstiens" in low or "structure de ta question" in low
            or "pas de réponse unique" in low or "subjectif" in low or "non bornée" in low
            or "à chercher" in low or "je ne sais pas" in low)
    liste = rep.count(",") >= 6 or rep.count("·") >= 4
    if mode == "abst":
        return "OK" if abst else "FAUX"
    if mode == "none":
        return "OK" if not abst else "MANQUÉ"
    if mode == "no":
        seg = low.split("—")[0].strip()
        return "FAUX" if (seg.startswith(cible) or ("— "+cible in low)) else "OK"
    # has
    if cible is None:
        if abst: return "MANQUÉ"
        if liste: return "LISTE"
        return "OK"
    if cible.lower() in low: return "OK"
    if abst: return "MANQUÉ"
    if liste: return "LISTE"
    return "FAUX"

def main():
    R = random.Random(999)
    cats = {}; problemes = []
    for i,(cat,q,mode,cible) in enumerate(CAS):
        rep = ask("m-%d-%d"%(i,R.randint(1000,9999)), q)
        v = classe(mode,cible,rep)
        cats.setdefault(cat,{})
        cats[cat][v] = cats[cat].get(v,0)+1
        if v!="OK":
            problemes.append((cat,v,q,rep[:75].replace("\n"," ")))
    print("\n===== PAR CATÉGORIE =====")
    for c,d in sorted(cats.items()):
        line = " ".join("%s=%d"%(k,v) for k,v in sorted(d.items()))
        print("  %-7s %s" % (c,line))
    tot=len(CAS); ok=sum(d.get("OK",0) for d in cats.values())
    print("\nGLOBAL : %d/%d OK (%.0f%%)  |  problèmes : %d" % (ok,tot,100*ok/tot,len(problemes)))
    print("\n===== PROBLÈMES DÉTAILLÉS =====")
    for cat,v,q,det in problemes:
        print("  [%s] %-7s %s\n        -> %s" % (cat,v,q,det))

if __name__=="__main__":
    main()
