#!/usr/bin/env python3
"""
VALIDATION de la résolution floue d'entités (resolution.py) — tolérance aux fautes, FAUX=0.

Charge le lecteur (LOURD) puis vérifie :
  • une faute proche est corrigée vers l'UNIQUE entité voisine (protugal -> portugal) et le fait est juste ;
  • l'exact n'est jamais marqué « corrigé » ;
  • un mot trop court ou sans voisin proche -> AUCUNE correction (HORS honnête) ;
  • la cohérence : la valeur obtenue après correction == la valeur de l'entité correcte (pas d'invention).
"""
from __future__ import annotations

import sys

import resolution
import lecteur
from base_faits import VERIFIE, HORS


def main() -> int:
    ok, fails = 0, []

    def check(nom, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  [OK ] {nom}")
        else:
            fails.append(nom)
            print(f"  [XX ] {nom}")

    L = lecteur.LECTEUR

    # On choisit une relation réellement servie par un gabarit NL et dont l'entité est un pays.
    # « monnaie du portugal » fonctionne (cf. interface) -> on teste la faute « protugal ».
    statut, fait, corr = resolution.repond_floue("quelle est la monnaie du protugal")
    ref = L.cherche("monnaie", "portugal")
    check("FUZZY : « protugal » corrigé -> réponse vérifiée", statut == VERIFIE and fait is not None)
    check("FUZZY : la correction proposée est « portugal »", corr == "portugal")
    check("FUZZY : valeur cohérente avec l'entité correcte (pas d'invention)",
          ref is not None and fait is not None and fait.valeur == ref.valeur)

    # Exact -> pas de « correction ».
    statut, fait, corr = resolution.repond_floue("quelle est la monnaie du portugal")
    check("EXACT : aucune correction signalée sur une entité correcte", statut == VERIFIE and corr is None)

    # Faute sur une autre entité/relation (langue) — robustesse multi-relation.
    s2, f2, c2 = resolution.repond_floue("quelle langue officielle en allemagne")
    check("FUZZY : autre relation OK en exact (langue/allemagne)", s2 == VERIFIE)

    # SOUNDNESS : entité absurde, aucun voisin proche -> pas de correction (HORS).
    res = resolution.corrige("monnaie", "xqzwklmpt-pays-imaginaire")
    check("SOUND : entité absurde -> aucune correction (None)", res is None)

    # SOUNDNESS : mot trop court -> pas de fuzzy (anti-ambiguïté).
    check("SOUND : entité ≤3 lettres -> pas de fuzzy", resolution.corrige("monnaie", "fr") is None)

    # SOUNDNESS : une correction, si elle existe, doit RÉELLEMENT pointer une clé connue.
    c = resolution.corrige("monnaie", "protugal")
    check("SOUND : la correction pointe une entité réellement connue",
          c is None or L.cherche("monnaie", c[0]) is not None)

    # ————————————————— RÉSOLVEUR NL GÉNÉRIQUE (toutes relations, sans gabarit) —————————————————
    def gen(q):
        return resolution.resout_nl_generique(q)

    s, f, _ = gen("quelle est la capitale du japon")
    check("GÉNÉRIQUE : capitale du Japon comprise (sans gabarit)", s == VERIFIE and f is not None)
    s, f, _ = gen("quel est le numero atomique du fer")
    check("GÉNÉRIQUE : numéro atomique du fer (autre domaine)", s == VERIFIE and f is not None and f.valeur == "26")
    s, f, corr = gen("quelle est la capitale du protugal")
    check("GÉNÉRIQUE+FUZZY : capitale du « protugal » corrigé", s == VERIFIE and corr == "portugal")

    # SOUNDNESS du générique : ces questions DOIVENT rester HORS (jamais une réponse fausse).
    pieges = ["quelle est la capitale de la lune", "monnaie de mon chien", "quelle heure est-il",
              "raconte moi une blague", "capitale de superman", "numero atomique de la joie",
              "pourquoi le ciel est bleu", "quel est le sens de la vie",
              # coïncidence ENTITÉ-TYPE (attribut réel absent) : « montagne de la montagne » -> Ontario via
              # subdivision_montagne ; « capitale de l'océan » -> « 2 » via rang_ocean. Doivent rester HORS.
              "quelle est la montagne de la montagne", "quelle est la capitale de l'océan atlantique",
              # coïncidence ENTITÉ=VOCAB-RELATION (vague 7) : « synonyme de maison » -> « maison » matchait une
              # clé-œuvre de maison_edition_oeuvre_ecrite -> éditeur « Syros ». Doit rester HORS.
              "quel est le synonyme de maison", "quel est le contraire de grand",
              # fuzzy multi-mots (T3 #72) : « fondation France » NE doit PAS se corriger en « fondation Francke »
              # (org allemande, 1695). Un mot CONNU (« france ») ne disparaît jamais d'une correction. Doit rester HORS.
              "quelle est l annee de fondation de la france",
              # REVERSE (#95/#96) : « quel pays A POUR capitale New York », « ... DONT la capitale est New York »,
              # « New York EST LA capitale DE QUEL pays », « DE QUOI New York est la capitale » sont des requêtes
              # INVERSES — forward-résoudre capitale[New York]=Albany (capitale de l'ÉTAT) serait FAUX. Toutes -> HORS.
              "quel pays a pour capitale new york", "quel pays a pour capitale lyon", "quelle ville a comme pays la france",
              "le pays dont la capitale est new york", "new york est la capitale de quel pays",
              "de quoi new york est-elle la capitale",
              # TAUTOLOGIE (#98) : « couleur de la France » -> « couleur » (film « France », couleur_film[france]=
              # « couleur ») = réponse dégénérée (valeur = attribut). Doit rester HORS (jamais « la couleur de X est couleur »).
              "quelle est la couleur de la france",
              # PIVOT-HOMONYME-NON-GÉO (#99/#100) : un PAYS/VILLE répondu par une relation d'ŒUVRE/PERSONNE/ÉQUIPE est un
              # homonyme -> HORS. « couleur de l'Espagne »->couleur_film=« noir et blanc » (FILM), « sport de la France »
              # ->sport_athlete=« cyclisme », « sexe de Paris »->sexe_personne=« masculin » (Pâris le prince). FAUX pour le
              # LIEU. (langue_officielle/capitale/continent/climat_localite NON-homonyme répondent : testés VERIFIE plus bas.)
              "quelle est la couleur de l espagne", "quel est le realisateur de l espagne",
              "quel est le sport de la france", "quel est le sexe de paris",
              # #101 : résidus non-géo (catégorie-erreur absurde) — un pays n'a ni lieu de naissance ni forme juridique.
              "quel est le lieu de naissance du maroc", "quelle est la forme juridique du chili",
              # #102 : pivots ASTRE/ÉLÉMENT — « sexe de Mars » (Mars le dieu), « auteur de Mercure » (roman Nothomb).
              "quel est le sexe de mars", "quel est l auteur de mercure",
              # #113 : « cap blanc » (vrai lieu ambigu : France/Canada/Algérie selon la relation) NE doit PAS être
              # fuzzy-corrigé en « cap blanco » (USA, autre lieu réel) -> ambigu -> HORS (jamais « États-Unis »).
              "quel est le pays de cap blanc",
              # #116 ATTRIBUT-PRIMAIRE : « materiau de PHARE de l'ÎLE Machias » -> phare_sur_ile gagne via « phare »+
              # « ile » (mots de l'entité) et répond l'ÎLE, pas le matériau -> HORS (l'attribut demandé est « materiau »).
              "quel est le materiau de phare de l ile machias seal",
              # #118 : « nom de PERSE » -> « perse » (entité, après « de ») NE doit PAS être fuzzy-corrigé en attribut
              # « pere » -> pere_divinite[perse]=Océan = FAUX. La fuzzy d'attribut ne touche que la région-attribut.
              "quel est le nom de perse",
              # ANTI-HOMONYME DATA-DÉRIVÉ (2026-07-02) : 2 FAUX+ RÉELS découverts par la campagne de mesure puis
              # corrigés par taxonomie.population_compatible (densité pays < 0.3 = collisions accidentelles) :
              # « altitude du Soudan » répondait 437,08 m = le VILLAGE de Loire-Atlantique, pas le pays ;
              # « statut patrimonial de Montserrat » répondait pour une STRUCTURE homonyme, pas le territoire.
              "quelle est l altitude du soudan", "quel est le statut patrimonial de montserrat"]
    faux = [q for q in pieges if gen(q)[0] == VERIFIE]
    check(f"GÉNÉRIQUE SOUND : {len(pieges)} pièges restent HORS (FAUX={len(faux)})", not faux)

    # ANTI-HOMONYME DATA-DÉRIVÉ — CONTRE-ÉPREUVE (pas de sur-abstention) : les réponses LÉGITIMES d'un pivot via
    # une population COMPATIBLE restent servies (valeurs ancrées sur le lecteur, robustes aux ré-ingestions).
    # Monaco (cité-État) : `capitale[monaco]`='Monaco-Ville' -> « monaco » n'est dans AUCUN registre ville/capitale
    # (la donnée distingue les deux noms) -> population_ville[monaco] est bloquée par le garde = ABSTENTION sur une
    # valeur vraie, acceptée (FAUX=0 > couverture). Contrôle négatif : jamais une valeur FAUSSE ; HORS est correct.
    # La vraie levée passera par l'ingestion de la population PAYS de Monaco (table `population`, compatible pays).
    _pm = L.cherche("population_ville", "monaco")
    if _pm is not None:
        sp, fp, _ = gen("quelle est la population de monaco")
        check("DATA-COMPAT : « population de Monaco » -> HORS honnête OU la vraie valeur (jamais un autre nombre)",
              sp != VERIFIE or (fp is not None and str(fp.valeur) == str(_pm.valeur)))
    _cb = L.cherche("annee_creation_organisation", "bangladesh")
    if _cb is not None:
        sb2, fb2, _ = gen("quelle est l annee de creation du bangladesh")
        check("DATA-COMPAT : « année de création du Bangladesh » répond (les pays SONT des organisations)",
              sb2 == VERIFIE and fb2 is not None and str(fb2.valeur) == str(_cb.valeur))
    _pc = L.cherche("pluriel", "chypre")
    if _pc is not None:
        sc2, fc2, _ = gen("quel est le pluriel de chypre")
        check("DATA-COMPAT : « pluriel de Chypre » répond (source lexicale : le nom est aussi un mot)",
              sc2 == VERIFIE and fc2 is not None and str(fc2.valeur) == str(_pc.valeur))

    # FILLER DANS TITRE (#115) : « Salut l'artiste » (film fr.) — « salut » est un filler-salutation, mais AU MILIEU il
    # fait partie du titre -> ne PAS le stripper (sinon « l artiste » = autre film russe = FAUX). On vérifie si la donnée
    # est présente (robuste). Les fillers de DÉBUT/FIN restent retirés (testé après).
    import lecteur as _lec
    if _lec.LECTEUR.cherche("langue_film", "salut l artiste") is not None:
        sf, ff, _ = gen("quelle est la langue de salut l artiste")
        check("FILLER-TITRE #115 : « langue de Salut l'artiste » -> français (« salut » non strippé au milieu)",
              sf == VERIFIE and ff is not None and ff.valeur == "français")
    sb, fb, _ = gen("salut quelle est la capitale du japon")   # filler en DÉBUT -> toujours retiré
    check("FILLER-BORD #115 : « salut quelle est la capitale du Japon » -> Tokyo (filler de début retiré)",
          sb == VERIFIE and fb is not None and fb.valeur == "Tokyo")

    # AMBIGUÏTÉ INTER-PALIER (T3 #79) : une clé NUE partagée par 2 relations avec des valeurs DIFFÉRENTES doit
    # abstenir, MÊME si une relation gagne le palier de tête par un token de NOM coïncidant avec un mot de l'entité
    # (« exploitant de LIGNE 3 » : `exploitant_ligne_ferry` capte « ligne » -> +1 vs `exploitant_telepherique`, mais
    # « ligne 3 » est aussi sa clé -> valeur différente). On n'asserte QUE si la donnée-piège est présente (robuste
    # aux évolutions des lanes) ; sinon le mécanisme reste couvert par _test_roundtrip (data-driven).
    import lecteur as _lec
    _a = _lec.LECTEUR.cherche("exploitant_ligne_ferry", "ligne 3")
    _b = _lec.LECTEUR.cherche("exploitant_telepherique", "ligne 3")
    if _a is not None and _b is not None and str(_a.valeur) != str(_b.valeur):
        check("INTER-PALIER : clé nue ambiguë (« exploitant de ligne 3 ») -> HORS (≠ choix silencieux)",
              gen("quel est le exploitant de ligne 3")[0] != VERIFIE)
        # et la MÊME question DÉSAMBIGUÏSÉE par le token discriminant répond bien (pas de sur-abstention)
        sd, fd, _ = gen("quel est le exploitant du telepherique ligne 3")
        check("INTER-PALIER : désambiguïsé (« exploitant du téléphérique ligne 3 ») -> répond",
              sd == VERIFIE and fd is not None and fd.valeur == _b.valeur)

    # AMBIGUÏTÉ PAR FAMILLE D'ATTRIBUT (T3 #80) : le conflictuel a souvent un score 0 (son token de TYPE n'est pas
    # dans la question) -> invisible aux candidats scorés. On scanne TOUTE la famille (« pays » -> pays_chateau,
    # pays_volcan…). « pays de château fort » : château EN Tunisie (pays_chateau) ET volcan EN France (pays_volcan)
    # -> ambigu -> HORS (avant le fix, choisissait Tunisie silencieusement). Robuste : asserte si la donnée présente.
    _ca = _lec.LECTEUR.cherche("pays_chateau", "château fort")
    _cv = _lec.LECTEUR.cherche("pays_volcan", "château fort")
    if _ca is not None and _cv is not None and str(_ca.valeur) != str(_cv.valeur):
        check("FAMILLE-ATTR : clé partagée même attribut, types ≠ (« pays de château fort ») -> HORS",
              gen("quel est le pays de château fort")[0] != VERIFIE)

    # ————————————————— CLASSIFIEUR LINGUISTIQUE (« le mot/verbe X » -> tête du syntagme) —————————————————
    # Tête du syntagme après un classifieur (« genre du MOT table » -> entité « table », pas « mot table »).
    s, f, _ = gen("quel est le genre du mot table")
    check("CLASSIF : « genre du mot table » -> féminin", s == VERIFIE and f is not None and f.valeur == "féminin")
    # Désambiguïsation lexicale : un mot polysémique (maison_mere existe) -> on garde la relation LEXICALE.
    s, f, _ = gen("quel est le genre du mot maison")
    check("CLASSIF : « genre du mot maison » désambiguïsé -> féminin",
          s == VERIFIE and f is not None and f.valeur == "féminin")
    # « mère » est désormais dans le lexème (clé « mère (français) »). DEUX invariants : (1) la VRAIE réponse
    # lexicale sort (« féminin ») ; (2) JAMAIS un FAUX+ par fuzzy abusif (« mère »->« mede »->« nom », ou ->un film).
    # Le fix : `_est_mot_connu` reconnaît les lemmes des tables « lemme (langue) » -> « mère » n'est plus corrigée.
    s, f, _ = gen("genre du mot mère")
    check("CLASSIF : « genre du mot mère » -> féminin (lemme français résolu)",
          s == VERIFIE and f is not None and f.valeur == "féminin")
    check("CLASSIF SOUND : « genre du mot mère » jamais un FAUX+ (ni « nom », ni un film)",
          f is None or f.valeur not in ("nom", "verbe", "adjectif") and "film" not in (f.source or "").lower())
    # SOUNDNESS : un classifieur sans entité réelle reste HORS.
    faux2 = [q for q in ("le mot de la fin", "quel est le mot magique", "genre du mot xyzqwklm")
             if gen(q)[0] == VERIFIE]
    check(f"CLASSIF SOUND : pièges classifieur restent HORS (FAUX={len(faux2)})", not faux2)

    # A1 — RAISONNEMENT SUPERLATIF : via une RELATION EXPLICITE (point_culminant), JAMAIS un argmax sur base
    # incomplète (« altitude_montagne ⋈ pays » donnerait « mont blanc du tacul », le vrai mont Blanc étant taggé
    # Italie). Sound : une vraie réponse de la source, ou HORS.
    sup = resolution.resout_superlatif
    check("SUPERLATIF : « la plus haute montagne de France » -> mont Blanc",
          "blanc" in (sup("la plus haute montagne de France") or "").lower())
    check("SUPERLATIF : « le plus haut sommet du Japon » -> mont Fuji",
          "fuji" in (sup("le plus haut sommet du Japon") or "").lower())
    check("SUPERLATIF SOUND : « plus haute CHAINE de montagne de France » -> HORS (≠ un pic)",
          sup("la plus haute chaine de montagne de France") is None)
    check("SUPERLATIF SOUND : superlatif sans relation explicite (« plus grand lac ») -> HORS (pas d'argmax incomplet)",
          sup("le plus grand lac de France") is None)
    # le GARDE de `resout_nl_generique` ne laisse jamais un superlatif accrocher une clé par coïncidence
    check("SUPERLATIF SOUND : générique s'abstient sur superlatif (pas de faux à-côté)",
          gen("la plus haute chaine de montagne de France")[0] != VERIFIE)

    # C — FICHE ENTITÉ (synthèse longueur variable). SOUND anti-homonyme : fiche riche seulement pour un type-pivot
    # cohérent (pays/élément), sinon DÉFINITION seule -> JAMAIS de mélange d'entités homonymes (superman DC + un
    # humain cubain ; le sentiment « amour » + le fleuve Amour).
    fiche = resolution.resout_fiche
    fr = fiche("parle-moi de la France") or ""
    check("FICHE : « parle-moi de la France » -> synthèse pays (capitale Paris, ≥3 faits)",
          "paris" in fr.lower() and fr.count(";") >= 2)
    sm = fiche("parle-moi de superman") or ""
    check("FICHE SOUND : « superman » sans mélange homonyme (ni Cuba ni Mexico)",
          "cuba" not in sm.lower() and "mexico" not in sm.lower())
    am = fiche("qu'est-ce que l'amour") or ""
    check("FICHE SOUND : « l'amour » -> définition seule (pas le fleuve « Asie »)", "asie" not in am.lower())
    # PIVOTS VILLE / ASTRE (anti-homonyme lexical) : « Paris/Lyon » = villes, « Jupiter » = planète, « Mercure » =
    # élément. Le fallback lexical (homonyme « nom de famille »/« anglais »/« exoplanète ») est INTERDIT pour une
    # entité typée -> on ne donne que des faits cohérents avec le type-pivot.
    pa = fiche("parle-moi de Paris") or ""
    check("FICHE VILLE : « Paris » -> fiche urbaine (France), jamais « nom de famille »",
          "france" in pa.lower() and "nom de famille" not in pa.lower())
    ly = fiche("parle-moi de Lyon") or ""
    check("FICHE VILLE : « Lyon » -> fiche urbaine (France), jamais « anglais »",
          "france" in ly.lower() and "anglais" not in ly.lower())
    ju = fiche("qu'est-ce que Jupiter") or ""
    check("FICHE ASTRE : « Jupiter » -> fiche planète (pas la ville US, pas un homonyme lexical)",
          ("planete" in ju.lower() or "diametre" in ju.lower()) and "etats-unis" not in ju.lower()
          and "états-unis" not in ju.lower())
    me = fiche("parle-moi de Mercure") or ""
    check("FICHE SOUND : « Mercure » -> fiche élément cohérente (symbole/numéro), pas de mélange",
          "symbole chimique" in me.lower() or "numero atomique" in me.lower())

    # A2 — COMPARAISON : compare DEUX faits numériques vérifiés (pas d'argmax/complétude). Entité absente -> HORS ;
    # attributs contradictoires -> HORS.
    cmp = resolution.resout_comparaison
    check("COMPARAISON : « France plus grande que Espagne » -> Oui",
          (cmp("la France est-elle plus grande que l'Espagne ?") or "").lower().startswith("oui"))
    check("COMPARAISON : « Espagne plus grande que France » -> Non",
          (cmp("l'Espagne est-elle plus grande que la France ?") or "").lower().startswith("non"))
    check("COMPARAISON SOUND : « lune plus grande que soleil » -> HORS (pas dans les données)",
          cmp("la lune est-elle plus grande que le soleil ?") is None)
    check("COMPARAISON SOUND : entités de fiction inconnues -> HORS",
          cmp("superman est-il plus grand que batman ?") is None)

    # FAUX+ révélés par la sonde multi-domaines (durcis) :
    # (1) « qui a ÉCRIT X » ne doit JAMAIS renvoyer l'illustrateur (« ecrite » qualifie « œuvre », pas l'attribut).
    se, fe, _ = gen("Qui a écrit Les Misérables ?")
    check("SONDE SOUND : « qui a écrit Les Misérables » ≠ illustrateur (pas « Bayard »)",
          fe is None or "bayard" not in (fe.valeur or "").lower())
    # (2) « quel EST le pays de X » (singulier) ne déclenche PAS un listage qui prend « est » comme valeur-ancre.
    check("SONDE SOUND : « quel est le pays de l'athlète Usain Bolt » -> pas de faux listage (≠ estonie)",
          "estonie" not in (resolution.resout_liste("Quel est le pays de l'athlète Usain Bolt ?") or "").lower())
    check("NON-RÉG listage : « quels sont les pays de l'Europe » -> liste",
          (resolution.resout_liste("Quels sont les pays de l'Europe ?") or "").lower().count("," ) >= 3)
    # NOMBRE DEMANDÉ respecté (vécu 2026-07-08 : « cite-moi trois pays » servait les 53) : n items + total dit.
    _l3 = resolution.resout_liste("cite-moi trois pays d'Europe") or ""
    check("LISTE COMPTÉE : « trois pays d'Europe » -> exactement 3 + « parmi N »",
          _l3.count(",") == 2 and "en voici 3 parmi" in _l3)
    _l5 = resolution.resout_liste("cite 5 pays d'Afrique") or ""
    check("LISTE COMPTÉE : « 5 pays d'Afrique » -> 5 + « parmi N »",
          _l5.count(",") == 4 and "en voici 5 parmi" in _l5)
    # QUALIFICATIF non résolu -> DIT, jamais ignoré en silence (« mammifère MARIN » servait les chauves-souris)
    _lm = resolution.resout_liste("cite les mammifères marins") or ""
    check("QUALIFICATIF DIT : « mammifères marins » -> liste + aveu « je ne sais pas filtrer »",
          "Je ne sais pas filtrer « marins »" in _lm)
    _lo = resolution.resout_liste("cite les mammifères") or ""
    check("SANS qualificatif -> pas d'aveu parasite", _lo and "filtrer" not in _lo)

    # DÉSAMBIGUÏSATION par attribut nommé : « quel PAYS de l'athlète X » départage pays_sportif_athlete (vs
    # sport_athlete) -> on récupère la vraie réponse au lieu d'un HORS prudent, sans faire fuir un piège.
    sa, fa, _ = gen("Quel est le pays de l'athlète Usain Bolt ?")
    check("DÉSAMBIG : « pays de l'athlète Usain Bolt » -> Jamaïque (attribut « pays » départage)",
          fa is not None and "jama" in (fa.valeur or "").lower())
    # GARDE anti-coïncidence type-entité : une relation à attribut GÉNÉRIQUE (pays_tour…) ne répond que si l'attribut
    # est nommé -> « qui a construit la tour Eiffel » ne renvoie plus le PAYS (« France ») par coïncidence sur « tour ».
    st, ft, _ = gen("Qui a construit la tour Eiffel ?")
    check("ANTI-COÏNCIDENCE : « qui a construit la tour Eiffel » ≠ pays (pas « France »)",
          ft is None or "france" not in (ft.valeur or "").lower())

    print(f"\n=== valide_resolution : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
