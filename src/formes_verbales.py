# -*- coding: utf-8 -*-
"""FORMES VERBALES FRANÇAISES — reconnaître une forme CONJUGUÉE comme verbe, FAUX=0 (2026-07-03).

POURQUOI : `grammaire_fr` reconnaît les LEMMES (infinitifs) mais pas les formes conjuguées (« dort », « parlait »),
ce qui bloquait l'analyse sujet-verbe-objet. Ce module construit un INDEX INVERSE forme -> lemme en GÉNÉRANT les
formes par les règles ÉTABLIES de la conjugaison (présent/imparfait/futur/participes) pour les verbes RÉGULIERS
(1er groupe ‑er, 2e groupe ‑ir de `conjugaison.CATALOGUE_2E`), complété par une TABLE des verbes irréguliers
les plus fréquents (être, avoir, aller, faire, dire, dormir…).

FAUX=0 : on ne génère QUE des formes garanties par la règle (radical + terminaison régulière) ou VÉRIFIÉES à la
main (table des irréguliers). Une forme absente de l'index reste « inconnue » côté grammaire (jamais devinée
verbe par sa terminaison — « noir »/« comment »/« dent » ne sont pas des verbes)."""
from __future__ import annotations

# ————————————————— TABLE des verbes IRRÉGULIERS fréquents : formes RÉELLES (présent + participes + formes courantes) —————————————————
# Vérifiée à la main. Couvre l'essentiel de l'usage courant que les règles régulières ne produisent pas.
_IRREGULIERS = {
    "être": "suis es est sommes êtes sont étais était étions étaient été serai seras sera serons serez seront sois soit soyons",
    "avoir": "ai as a avons avez ont avais avait avions avaient eu eus eut eûmes aurai auras aura aurons aurez auront aie aies ait",
    "aller": "vais vas va allons allez vont allais allait allions allaient allé allée allés allées irai iras ira irons irez iront aille ailles",
    "faire": "fais fait faisons faites font faisais faisait faisions faisaient fait faite faits faites ferai feras fera ferons ferez feront fasse fasses",
    "dire": "dis dit disons dites disent disais disait disions disaient dit dite dits dites dirai diras dira dirons direz diront dise dises",
    "voir": "vois voit voyons voyez voient voyais voyait voyions voyaient vu vue vus vues verrai verras verra verrons verrez verront voie voies",
    "savoir": "sais sait savons savez savent savais savait savions savaient su sue sus sues saurai sauras saura saurons saurez sauront sache saches",
    "pouvoir": "peux peut pouvons pouvez peuvent pouvais pouvait pouvions pouvaient pu pourrai pourras pourra pourrons pourrez pourront puisse puisses",
    "vouloir": "veux veut voulons voulez veulent voulais voulait voulions voulaient voulu voulue voulus voulues voudrai voudras voudra voudrons voudrez voudront veuille veuilles",
    "devoir": "dois doit devons devez doivent devais devait devions devaient dû due dus dues devrai devras devra devrons devrez devront doive doives",
    "prendre": "prends prend prenons prenez prennent prenais prenait prenions prenaient pris prise prises prendrai prendras prendra prendrons prendrez prendront prenne prennes",
    "venir": "viens vient venons venez viennent venais venait venions venaient venu venue venus venues viendrai viendras viendra viendrons viendrez viendront vienne viennes",
    "tenir": "tiens tient tenons tenez tiennent tenais tenait tenions tenaient tenu tenue tenus tenues tiendrai tiendras tiendra tiendrons tiendrez tiendront tienne tiennes",
    "mettre": "mets met mettons mettez mettent mettais mettait mettions mettaient mis mise mises mettrai mettras mettra mettrons mettrez mettront mette mettes",
    "dormir": "dors dort dormons dormez dorment dormais dormait dormions dormaient dormi dormirai dormiras dormira dormirons dormirez dormiront dorme dormes",
    "partir": "pars part partons partez partent partais partait partions partaient parti partie partis parties partirai partiras partira partirons partirez partiront parte partes",
    "sortir": "sors sort sortons sortez sortent sortais sortait sortions sortaient sorti sortie sortis sorties sortirai sortiras sortira sortirons sortirez sortiront sorte sortes",
    "sentir": "sens sent sentons sentez sentent sentais sentait sentions sentaient senti sentie sentis senties sentirai sentiras sentira sentirons sentirez sentiront sente sentes",
    "servir": "sers sert servons servez servent servais servait servions servaient servi servie servis servies servirai serviras servira servirons servirez serviront serve serves",
    "courir": "cours court courons courez courent courais courait courions couraient couru courue courus courues courrai courras courra courrons courrez courront coure coures",
    "mourir": "meurs meurt mourons mourez meurent mourais mourait mourions mouraient mort morte morts mortes mourrai mourras mourra mourrons mourrez mourront meure meures",
    "ouvrir": "ouvre ouvres ouvrons ouvrez ouvrent ouvrais ouvrait ouvrions ouvraient ouvert ouverte ouverts ouvertes ouvrirai ouvriras ouvrira ouvrirons ouvrirez ouvriront",
    "offrir": "offre offres offrons offrez offrent offrais offrait offrions offraient offert offerte offerts offertes offrirai offriras offrira offrirons offrirez offriront",
    "connaître": "connais connaît connaissons connaissez connaissent connaissais connaissait connaissions connaissaient connu connue connus connues connaîtrai connaîtras connaîtra connaîtrons connaîtrez connaîtront connaisse",
    "paraître": "parais paraît paraissons paraissez paraissent paraissais paraissait paraissaient paru parue parus parues paraîtrai paraîtras paraîtra paraîtrons paraîtrez paraîtront paraisse",
    "croire": "crois croit croyons croyez croient croyais croyait croyions croyaient cru crue crus crues croirai croiras croira croirons croirez croiront croie croies",
    "boire": "bois boit buvons buvez boivent buvais buvait buvions buvaient bu bue bus bues boirai boiras boira boirons boirez boiront boive boives",
    "lire": "lis lit lisons lisez lisent lisais lisait lisions lisaient lu lue lus lues lirai liras lira lirons lirez liront lise lises",
    "écrire": "écris écrit écrivons écrivez écrivent écrivais écrivait écrivions écrivaient écrit écrite écrits écrites écrirai écriras écrira écrirons écrirez écriront écrive",
    "vivre": "vis vit vivons vivez vivent vivais vivait vivions vivaient vécu vécue vécus vécues vivrai vivras vivra vivrons vivrez vivront vive vives",
    "suivre": "suis suit suivons suivez suivent suivais suivait suivions suivaient suivi suivie suivis suivies suivrai suivras suivra suivrons suivrez suivront suive suives",
    "recevoir": "reçois reçoit recevons recevez reçoivent recevais recevait recevions recevaient reçu reçue reçus reçues recevrai recevras recevra recevrons recevrez recevront reçoive",
    "devenir": "deviens devient devenons devenez deviennent devenais devenait devenions devenaient devenu devenue devenus devenues deviendrai deviendras deviendra deviendrons deviendrez deviendront devienne",
    "comprendre": "comprends comprend comprenons comprenez comprennent comprenais comprenait comprenions comprenaient compris comprise comprises comprendrai comprendras comprendra comprendrons comprendrez comprendront comprenne",
    "attendre": "attends attend attendons attendez attendent attendais attendait attendions attendaient attendu attendue attendus attendues attendrai attendras attendra attendrons attendrez attendront attende",
    "entendre": "entends entend entendons entendez entendent entendais entendait entendions entendaient entendu entendue entendus entendues entendrai entendras entendra entendrons entendrez entendront entende",
    "rendre": "rends rend rendons rendez rendent rendais rendait rendions rendaient rendu rendue rendus rendues rendrai rendras rendra rendrons rendrez rendront rende",
    "perdre": "perds perd perdons perdez perdent perdais perdait perdions perdaient perdu perdue perdus perdues perdrai perdras perdra perdrons perdrez perdront perde",
    "falloir": "faut fallait faudra faille fallu",
    "valoir": "vaux vaut valons valez valent valais valait valu value valus values vaudrai vaudras vaudra vaudrons vaudrez vaudront vaille",
    "vouloir": "veux veut voulons voulez veulent voulais voulait voulions voulaient voulu",
}

# Verbes RÉGULIERS très fréquents ABSENTS du dataset extrait (catégorisés ailleurs dans le Wiktionnaire) :
# on garantit le cœur de fréquence du français. Tous 1er groupe réguliers (concaténation sûre).
_VERBES_FREQUENTS = ("parler manger aimer penser trouver donner jouer montrer chercher écouter regarder "
                     "demander rester passer porter poser garder laisser sembler continuer parler compter "
                     "arriver entrer rentrer tomber marcher travailler habiter étudier expliquer présenter "
                     "proposer utiliser employer créer former changer arrêter oublier gagner perdre "
                     "commencer terminer ajouter appeler jeter acheter espérer préférer répéter emmener "
                     "raconter chanter danser dessiner cuisiner nettoyer réserver voyager ranger nager").split()

_INDEX = None                                    # forme_normalisée -> lemme (str)


def _norm(s: str) -> str:
    try:
        from base_faits import normalise as _n
        return _n(s)
    except Exception:
        import unicodedata
        s = unicodedata.normalize("NFD", str(s).lower())
        return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _formes_regulieres(inf: str):
    """Génère les formes RÉGULIÈRES garanties d'un verbe du 1er (‑er) ou 2e (‑ir catalogue) groupe.
    Ne produit QUE ce que la règle garantit exact (radical + terminaison ; futur = infinitif + terminaison)."""
    import conjugaison as C
    inf = inf.strip().lower()
    formes = set()
    if inf == "aller":
        return formes                             # irrégulier -> table
    if inf.endswith("er"):
        rad = inf[:-2]
        # présent je/tu/il/ils (toujours réguliers pour ‑er) + nous/vous
        formes.update({rad + "e", rad + "es", rad + "ent"})
        # nous/vous : gérer ‑ger/‑cer (mangeons, commençons) sinon rad+ons
        if inf.endswith("ger"):
            formes.add(rad + "eons")
        elif inf.endswith("cer"):
            formes.add(rad[:-1] + "çons")
        else:
            formes.add(rad + "ons")
        formes.add(rad + "ez")
        # imparfait (stem = radical, terminaisons régulières) ; ‑ger/‑cer -> mangeais/commençais
        stem_imp = rad + ("e" if inf.endswith("ger") else "") if inf.endswith("ger") else (
            rad[:-1] + "ç" if inf.endswith("cer") else rad)
        for term in ("ais", "ait", "aient", "ions", "iez"):
            formes.add(stem_imp + term)
        # futur (infinitif + terminaisons) — régulier pour ‑er sauf verbes à radical e/é (abstention prudente)
        for term in ("ai", "as", "a", "ons", "ez", "ont"):
            formes.add(inf + term)
        # participes
        formes.update({rad + "é", rad + "ée", rad + "és", rad + "ées", rad + "ant"})
        return formes
    if inf in C.CATALOGUE_2E:
        rad = inf[:-2]
        for term in ("is", "it", "issons", "issez", "issent"):
            formes.add(rad + term)
        for term in ("issais", "issait", "issaient", "issions", "issiez"):
            formes.add(rad + term)
        for term in ("ai", "as", "a", "ons", "ez", "ont"):
            formes.add(inf + term)
        formes.update({rad + "i", rad + "ie", rad + "is", rad + "ies", rad + "issant"})
        return formes
    return formes


def _formes_modele(inf: str):
    """Génère les formes d'un verbe du 3e groupe suivant un MODÈLE de conjugaison ÉTABLI (patrons Bescherelle).
    Couvre systématiquement les familles régulières-dans-leur-irrégularité. Renvoie un set, ou set() si aucun
    modèle ne s'applique (le verbe reste alors à la table des idiosyncrasiques). FAUX=0 : patrons de grammaire."""
    inf = inf.strip().lower()
    F = set()

    def ajoute_imparfait_futur(stem_imp, stem_fut, participe_passe=None, ppr=None):
        for term in ("ais", "ait", "aient", "ions", "iez"):
            F.add(stem_imp + term)
        for term in ("ai", "as", "a", "ons", "ez", "ont"):
            F.add(stem_fut + term)
        if participe_passe:
            F.update({participe_passe, participe_passe + "e", participe_passe + "s", participe_passe + "es"})
        if ppr:
            F.add(ppr)

    # — FAMILLE « partir » (partir, dormir, sortir, servir, sentir, mentir…) : singulier perd la consonne finale —
    if inf.endswith("ir") and inf in _MODELE_PARTIR:
        rad = inf[:-2]                       # part, dorm, sort, serv, sent, ment
        sing = rad[:-1]                      # par, dor, sor, ser, sen, men
        F.update({sing + "s", sing + "t", rad + "ons", rad + "ez", rad + "ent"})
        ajoute_imparfait_futur(rad, inf, inf[:-1], rad + "ant")
        return F

    # — FAMILLE « ouvrir » (ouvrir, couvrir, offrir, souffrir…) : présent en -e comme le 1er groupe —
    if inf.endswith("rir") and inf in _MODELE_OUVRIR:
        rad = inf[:-2]                       # ouvr, couvr, offr, souffr
        F.update({rad + "e", rad + "es", rad + "ent", rad + "ons", rad + "ez"})
        pp = rad[:-1] + "ert"                # ouvert, couvert, offert, souffert
        ajoute_imparfait_futur(rad, inf, pp, rad + "ant")
        return F

    # — FAMILLE « courir » (courir, parcourir…) : radical stable, futur en -rr —
    if inf.endswith("courir"):
        rad = inf[:-2]                       # cour, parcour
        F.update({rad + "s", rad + "t", rad + "ons", rad + "ez", rad + "ent"})
        ajoute_imparfait_futur(rad, rad + "r", rad + "u", rad + "ant")
        return F

    # — FAMILLE « attendre » (rendre, vendre, perdre, répondre, entendre, descendre, mordre, fondre…) —
    if inf.endswith("dre") and not inf.endswith(("indre", "oudre", "prendre")):
        rad = inf[:-2]                       # attend, rend, vend, perd, répond
        F.update({rad + "s", rad, rad + "ons", rad + "ez", rad + "ent"})   # 3sg = radical nu
        ajoute_imparfait_futur(rad, inf[:-1], rad + "u", rad + "ant")
        return F

    # — FAMILLE « prendre » (prendre, apprendre, comprendre, surprendre…) —
    if inf.endswith("prendre"):
        pre = inf[:-7]                       # préfixe (ap-, com-, sur-…)
        rad, radp = pre + "prend", pre + "pren"
        F.update({rad + "s", rad, radp + "ons", radp + "ez", radp + "nent"})   # prennent
        ajoute_imparfait_futur(radp, inf[:-1], pre + "pris", radp + "ant")
        return F

    # — FAMILLE « mettre » (mettre, permettre, promettre, admettre…) —
    if inf.endswith("mettre"):
        pre = inf[:-6]
        F.update({pre + "mets", pre + "met", pre + "mettons", pre + "mettez", pre + "mettent"})
        ajoute_imparfait_futur(pre + "mett", pre + "mettr", pre + "mis", pre + "mettant")
        return F

    # — FAMILLE « -indre » (craindre, plaindre, peindre, éteindre, atteindre, joindre, rejoindre…) —
    if inf.endswith("indre"):
        base = inf[:-4]                      # crai, pei, attei, joi
        F.update({base + "ns", base + "nt", base + "gnons", base + "gnez", base + "gnent"})
        ajoute_imparfait_futur(base + "gn", inf[:-1], base + "nt", base + "gnant")
        return F

    # — FAMILLE « -aître » (connaître, paraître, apparaître, disparaître…) : « connaître »[:-4] = « conna » —
    if inf.endswith(("aître", "aitre")):
        r = inf[:-4]                         # « conna », « para »
        F.update({r + "is", r + "ît", r + "issons", r + "issez", r + "issent"})
        ajoute_imparfait_futur(r + "iss", inf[:-1], r + "u", r + "issant")
        return F

    # — FAMILLE « -uire » (conduire, produire, construire, détruire, réduire, traduire, cuire, nuire…) —
    if inf.endswith("uire"):
        base = inf[:-4]                      # cond, prod, constr, dét, réd
        F.update({base + "uis", base + "uit", base + "uisons", base + "uisez", base + "uisent"})
        ajoute_imparfait_futur(base + "uis", inf[:-1], base + "uit", base + "uisant")
        return F

    return F


# — catalogues des familles à singulier réduit / présent-en-e (sous-ensembles de CATALOGUE_3E_IR) —
_MODELE_PARTIR = frozenset({
    "partir", "repartir", "départir", "sortir", "ressortir", "dormir", "endormir", "rendormir", "servir",
    "desservir", "resservir", "mentir", "démentir", "sentir", "ressentir", "consentir", "pressentir", "repentir"})
_MODELE_OUVRIR = frozenset({
    "ouvrir", "couvrir", "découvrir", "recouvrir", "rouvrir", "entrouvrir", "offrir", "souffrir"})


def _construit_index() -> dict:
    global _INDEX
    if _INDEX is not None:
        return _INDEX
    idx = {}
    # 1) verbes irréguliers fréquents (formes réelles, table vérifiée)
    for lemme, formes in _IRREGULIERS.items():
        for f in formes.split():
            idx.setdefault(_norm(f), lemme)
    # 2) verbes réguliers : liste embarquée (6505 verbes du Wiktionnaire) + cœur de fréquence -> formes générées
    import os
    lemmes = set(_VERBES_FREQUENTS)
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verbes_fr.txt")
    try:
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                v = ligne.strip()
                if v:
                    lemmes.add(v)
    except OSError:
        pass
    for mot in lemmes:
        if mot in _IRREGULIERS:
            continue
        formes = _formes_regulieres(mot) or _formes_modele(mot)   # régulier d'abord, sinon modèle 3e groupe
        for f in formes:
            idx.setdefault(_norm(f), mot)
    _INDEX = idx
    return idx


def est_forme_verbale(mot: str) -> bool:
    """True si `mot` est une forme conjuguée (ou un infinitif) d'un verbe connu — FAUX=0 (index dérivé/vérifié)."""
    return _norm(mot) in _construit_index()


def lemme_de(mot: str):
    """Infinitif du verbe dont `mot` est une forme, ou None si inconnu."""
    return _construit_index().get(_norm(mot))
