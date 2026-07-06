"""
INGESTION T8 — HISTOIRE, DATES & POLITIQUE -> datasets/lecteur/*.jsonl (ONLINE via QLever, offline ensuite).

Ouvre le PATRON DATE/ANNÉE du lecteur : une entité (État, organisation, événement) a une ANNÉE bornée par
l'histoire (fondation P571, dissolution P576, date d'un événement P585). On stocke l'ANNÉE (chaîne, 4 chiffres,
négative pour av. J.-C.) — pas la date complète : l'année est le grain stable et non disputé, la valeur scalaire
que le lecteur sait restituer (comme `numero_atomique`/`annee` du noyau).

  FAUX=0 DATE (4 garde-fous cumulés) :
    (a) le littéral date parse en ANNÉE (regex `(-?\\d{1,4})-…`), sinon REJET ;
    (b) `fonctionnel` (dans IQ.publie) : une entité à >1 année distincte (plusieurs dates de fondation
        contradictoires) part en HORS — JAMAIS d'année ambiguë écrite ;
    (c) PLAGE historique plausible [ymin, ymax] par relation : écarte les saisies aberrantes / dates futures ;
    (d) ANCRES vérité-terrain dans valide_lecteur_t8.py (France 843/987 selon source, ONU 1945, URSS dissoute
        1991…) — ancrage NON circulaire.

Relations politiques OUVERTES (vocabulaire d'entités, pas un ensemble fermé) : `predecesseur_etat` (P155, « suit »)
réutilise IQ._ingere_x_vers_entite (valeur = autre État) + `fonctionnel` (multi-prédécesseur -> HORS) + ancres.

Usage : python3 ingere_t8.py sonde   (inspecte sans écrire)   |   python3 ingere_t8.py   (ingère tout).
"""
from __future__ import annotations

import re
import sys

import ingere_qlever as IQ


# ============================================================================================
#  FABRIQUE DATE générique : entité (classe) -> ANNÉE (str) d'une propriété date littérale.
# ============================================================================================
_AN = re.compile(r"^(-?\d{1,4})-")  # "1776-07-04T..." -> "1776" ; "-0753-01-01T..." -> "-0753"


# Mois de calendriers connus (français, persan solaire, hébreu) : un libellé « <jour> <mois> <année> » NU
# (sans nom d'événement) est une entité « jour de calendrier » de Wikidata, PAS un événement historique.
# On les rejette pour `date_evenement` (honnêteté de libellé). Les VRAIS événements sont nommés descriptivement
# (« attentats du 11 septembre 2001 », « bataille d'Austerlitz ») et NE matchent jamais ce motif.
# Soundness : le filtre ne fait que SUPPRIMER du bruit — les années étaient déjà correctes, FAUX=0 préservé.
_MOIS_CALENDRIER = {
    # français
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
    "septembre", "octobre", "novembre", "décembre",
    # persan (calendrier solaire iranien)
    "farvardin", "ordibehesht", "khordad", "tir", "mordad", "shahrivar",
    "mehr", "aban", "azar", "dey", "bahman", "esfand",
    # hébreu
    "tishri", "tichri", "heshvan", "marheshvan", "kislev", "tevet", "tévet", "shevat", "chevat",
    "adar", "nisan", "iyar", "iyyar", "sivan", "tammuz", "tamouz", "av", "elul", "eloul",
}
_JOUR_MOIS_AN = re.compile(r"^\d{1,2}(?:er)?\s+(\S+)\s+\d{3,4}$")  # « 10 août 1583 », « 1er septembre 2001 »
_MOIS_AN = re.compile(r"^(\S+)\s+\d{3,4}$")                        # « septembre 2001 »
_ANNEE_NUE = re.compile(r"^-?\d{1,4}$")                            # « 1492 », « -753 » (l'année comme entité)


def _est_date_nue(libelle: str) -> bool:
    """True si `libelle` est une DATE/ANNÉE NUE (pas un événement nommé) : entité jour-de-calendrier
    (« 01 Aban 1279 », « 10 août 1583 »), mois+année (« septembre 2001 »), ou année seule (« 1492 »).
    Garde-fou anti-faux-négatif : pour les formes à mois, le mois DOIT appartenir à un calendrier connu —
    un vrai événement nommé (« attentats du 11 septembre 2001 », « bataille d'Austerlitz ») a d'autres mots
    et N'EST JAMAIS ancré ^...$ par ces motifs, donc jamais rejeté. Soundness : ne fait que retirer du bruit."""
    s = libelle.strip()
    if _ANNEE_NUE.match(s):                       # « 1492 » = l'année comme entité, pas un événement
        return True
    m = _JOUR_MOIS_AN.match(s)
    if m and m.group(1).casefold() in _MOIS_CALENDRIER:
        return True
    m = _MOIS_AN.match(s)
    if m and m.group(1).casefold() in _MOIS_CALENDRIER:
        return True
    return False


# Filtres d'honnêteté de libellé par relation (rejette les libellés non pertinents SANS jamais créer de faux).
FILTRES_LIBELLE = {
    "date_evenement": _est_date_nue,
}


def _annee(litteral: str):
    """Extrait l'année (str canonique, sans zéros de tête, signe conservé) d'un littéral date xsd:dateTime.
    Renvoie None si non parsable (FAUX=0 : on ne devine jamais une année)."""
    m = _AN.match(litteral.strip())
    if not m:
        return None
    try:
        return str(int(m.group(1)))  # normalise "-0753" -> "-753", "1776" -> "1776"
    except ValueError:
        return None


def _pull_date(relation, classe_qid, prop, sous_classes=True, filtre_libelle=None):
    """Tire (entité_fr, annee_str, sitelinks:int) pour la propriété date `prop` des instances de `classe_qid`.
    `filtre_libelle` (callable libellé->bool) : si fourni, les entités dont le libellé matche sont REJETÉES
    (honnêteté de libellé, ex. dates de calendrier nues pour date_evenement). Renvoie aussi le compte rejeté.
    SITELINKS (2026-07-06) : lus pour la dominance par NOTORIÉTÉ — « traité de Versailles » (1919, 135 wikis)
    était tué par ses homonymes historiques (1756/1768/1783/1787, ≤15 wikis) via le fonctionnel par libellé."""
    chemin = "wdt:P31/wdt:P279*" if sous_classes else "wdt:P31"
    q = f"""PREFIX wikibase: <http://wikiba.se/ontology#>
    SELECT ?eLabel ?v ?sl WHERE {{
      ?e {chemin} wd:{classe_qid} ; wdt:{prop} ?v .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
      OPTIONAL {{ ?e wikibase:sitelinks ?sl }}
    }}"""
    rows = IQ._charge_ou_fetch(relation, q)
    out = []
    rejet_libelle = 0
    for r in rows:
        e = IQ.val(r, "eLabel")
        v = IQ.val(r, "v")
        if not e or not v or IQ._est_qid(e):
            continue
        if filtre_libelle is not None and filtre_libelle(e):
            rejet_libelle += 1
            continue
        an = _annee(v)
        if an is not None:
            try:
                sl = int(float(IQ.val(r, "sl") or 0))
            except ValueError:
                sl = 0
            out.append((e, an, sl))
    return out, rejet_libelle


def _dominance_notoriete(paires_sl, ratio=8.0):
    """DOMINANCE PAR NOTORIÉTÉ sur libellés homonymes à ANNÉES distinctes : l'entité au max de sitelinks est
    retenue si elle domine la 2ᵉ d'un facteur >= ratio (traité de Versailles 1919 : 135 wikis vs 15). En
    dessous, l'ambiguïté est RÉELLE (bataille des Ardennes 1914 vs 1944) -> laissée au fonctionnel -> HORS."""
    import collections
    from base_faits import _sans_articles as _sa
    g = collections.defaultdict(list)
    for e, an, sl in paires_sl:
        g[_sa(e)].append((int(sl), an, e))
    out, domines = [], 0
    for cle, lst in g.items():
        annees = {an for _sl, an, _e in lst}
        if len(annees) == 1:
            _sl, an, e = lst[0]
            out.append((e, an))
            continue
        lst.sort(reverse=True)
        # 2ᵉ max de sitelinks parmi les entités d'une ANNÉE DIFFÉRENTE de la dominante
        dom_sl, dom_an, dom_e = lst[0]
        rival = max((sl for sl, an, _e in lst if an != dom_an), default=0)
        if dom_sl > 0 and (rival == 0 or dom_sl >= ratio * rival):
            out.append((dom_e, dom_an))
            domines += 1
        else:
            for _sl, an, e in lst:                        # ambigu réel -> le fonctionnel aval rejettera
                out.append((e, an))
    if domines:
        print(f"  [dominance-notoriété] {domines} libellés homonymes résolus par les sitelinks (≥{ratio:g}×)")
    return out


def ingere_date(relation, classe_qid, prop, source, ymin, ymax, categorie="passe", sous_classes=True):
    """Ingère une relation DATE/ANNÉE bornée. PLAGE [ymin, ymax] = garde-fou anti-saisie/anti-futur (HORS hors-plage).
    `fonctionnel` (publie) rejette toute entité à plusieurs années distinctes. Renvoie les stats publie()."""
    # Le filtre « libellé = date/année nue » s'applique à TOUTE relation DATE : l'entité d'un fait DATE est
    # une chose datée (pays, organisation, événement nommé), jamais une date/année nue (« 883 », « 1492 »).
    triples, rejet_libelle = _pull_date(relation, classe_qid, prop, sous_classes=sous_classes,
                                        filtre_libelle=FILTRES_LIBELLE.get(relation, _est_date_nue))
    bornes, hors_plage = [], 0
    for e, an, sl in triples:
        if ymin <= int(an) <= ymax:
            bornes.append((e, an, sl))
        else:
            hors_plage += 1
    paires = _dominance_notoriete(bornes)
    rej = f", {rejet_libelle} libellé-nu(HORS)" if rejet_libelle else ""
    print(f"== {relation} ({prop}, classe {classe_qid}) : {len(triples)} dates parsées, "
          f"plage[{ymin},{ymax}] -> {len(paires)} gardées, {hors_plage} hors-plage(HORS){rej} ==")
    return IQ.publie(relation, categorie, source, paires)


# ============================================================================================
#  PATRON DATE-QUALIFICATIF — règnes de souverains (P39 « fonction occupée » + qualificatif date).
#  Le pont DATE direct (`_pull_date`) lit les claims tronqués (wdt:) ; les dates de RÈGNE vivent dans les
#  QUALIFICATIFS d'un statement P39 (pq:P580 début / pq:P582 fin), inaccessibles à wdt:. On lit donc le
#  statement complet (p:P39 -> ps:P39 = la fonction ; pq:Pxxx = la date). On borne la fonction aux titres
#  de MONARQUE (?pos wdt:P279* wd:Q12097) pour rester sur du borné-historique propre, et on n'indexe QUE des
#  personnes (wdt:P31 wd:Q5). FAUX=0 : `fonctionnel` (publie) rejette tout souverain à >1 année distincte
#  (multi-règnes / multi-titres : Charles Quint roi 1516 + empereur 1519 -> HORS), homonymes idem.
#  URI complètes pour p:/ps:/pq: car IQ.PREFIXES ne déclare que wdt:/wd:/rdfs:.
_P_P39  = "<http://www.wikidata.org/prop/P39>"
_PS_P39 = "<http://www.wikidata.org/prop/statement/P39>"
def _pull_regne(relation, pos_classe_qid, pq_prop, exclure_qid=None):
    """`exclure_qid` (option) retire les fonctions qui sont AUSSI sous cette classe (anti-redondance : ministre
    Q83307 SAUF chef de gouvernement Q2285706 = PM, déjà couvert) via FILTER NOT EXISTS sur la sous-classe."""
    excl = (f"\n      FILTER NOT EXISTS {{ ?pos wdt:P279* wd:{exclure_qid} }}" if exclure_qid else "")
    q = f"""SELECT ?eLabel ?v WHERE {{
      ?e {_P_P39} ?st .
      ?st {_PS_P39} ?pos ; <http://www.wikidata.org/prop/qualifier/{pq_prop}> ?v .
      ?pos wdt:P279* wd:{pos_classe_qid} .{excl}
      ?e wdt:P31 wd:Q5 .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch(relation, q)
    out = []
    for r in rows:
        e = IQ.val(r, "eLabel"); v = IQ.val(r, "v")
        if not e or not v or IQ._est_qid(e):
            continue
        an = _annee(v)
        if an is not None:
            out.append((e, an))
    return out


def ingere_regne(relation, pos_classe_qid, pq_prop, source, ymin, ymax, categorie="passe", exclure_qid=None):
    """Ingère une date de RÈGNE/MANDAT (qualificatif pq_prop d'un statement P39). Mêmes garde-fous que ingere_date :
    plage [ymin,ymax] + fonctionnel (publie) multi->HORS. `exclure_qid` retire une sous-classe (anti-redondance)."""
    brut = _pull_regne(relation, pos_classe_qid, pq_prop, exclure_qid=exclure_qid)
    paires, hors_plage = [], 0
    for e, an in brut:
        if ymin <= int(an) <= ymax:
            paires.append((e, an))
        else:
            hors_plage += 1
    print(f"== {relation} (P39+pq:{pq_prop}, titre {pos_classe_qid}) : {len(brut)} dates parsées, "
          f"plage[{ymin},{ymax}] -> {len(paires)} gardées, {hors_plage} hors-plage(HORS) ==")
    return IQ.publie(relation, categorie, source, paires)


# (relation, classe-titre, qualificatif, source, ymin, ymax) — règnes de souverains.
REGNES = [
    ("annee_debut_regne", "Q12097", "P580",
     "Wikidata/QLever — année de début de règne (P39 monarque, qualificatif P580)", -4000, 2026),
    ("annee_fin_regne", "Q12097", "P582",
     "Wikidata/QLever — année de fin de règne (P39 monarque, qualificatif P582)", -4000, 2026),
]

# Même patron DATE-QUALIFICATIF appliqué aux FONCTIONS POLITIQUES (chef d'État / de gouvernement). On ne prend
# que la FIN de mandat (qualificatif P582) : un mandat terminé est un fait BORNÉ-historique (vs un mandat EN COURS
# = vérité-datée, qui n'a PAS de P582 → naturellement exclu). Fonctionnel : multi-mandats (ex. Churchill PM 1945
# & 1955) → années distinctes → HORS. ingere_regne est générique (classe de fonction + qualificatif).
MANDATS = [
    ("annee_fin_mandat_chef_etat", "Q48352", "P582",
     "Wikidata/QLever — année de fin de mandat d'un chef d'État (P39 Q48352, qualificatif P582)", -4000, 2026),
    ("annee_fin_mandat_chef_gouvernement", "Q2285706", "P582",
     "Wikidata/QLever — année de fin de mandat d'un chef de gouvernement (P39 Q2285706, qualificatif P582)", -4000, 2026),
    # DÉBUT de mandat (qualificatif P580) : la date de PRISE DE FONCTION est figée donc bornée, y compris pour un
    # mandat encore en cours (≠ la fin). Complète proprement les fins ci-dessus, sans redondance.
    ("annee_debut_mandat_chef_etat", "Q48352", "P580",
     "Wikidata/QLever — année de début de mandat d'un chef d'État (P39 Q48352, qualificatif P580)", -4000, 2026),
    ("annee_debut_mandat_chef_gouvernement", "Q2285706", "P580",
     "Wikidata/QLever — année de début de mandat d'un chef de gouvernement (P39 Q2285706, qualificatif P580)", -4000, 2026),
]

# Ministres (fonction Q83307) EN EXCLUANT les chefs de gouvernement (Q2285706 ⊂ Q83307 = PM, déjà couverts) pour
# éviter la redondance. (relation, classe, qualif, source, ymin, ymax, exclure_qid). Fonctionnel : les ministres
# multi-portefeuilles (années distinctes) -> HORS ; ne survivent que les mono-portefeuille = fait non ambigu.
MINISTRES = [
    ("annee_fin_mandat_ministre", "Q83307", "P582",
     "Wikidata/QLever — année de fin de mandat ministériel (P39 Q83307 hors chef de gouvernement, qualif P582)",
     -4000, 2026, "Q2285706"),
    ("annee_debut_mandat_ministre", "Q83307", "P580",
     "Wikidata/QLever — année de début de mandat ministériel (P39 Q83307 hors chef de gouvernement, qualif P580)",
     -4000, 2026, "Q2285706"),
]

# Autres fonctions de gouvernance (diplomatie / administration). Mêmes garde-fous ; les multi-postes (ambassadeur
# en poste successif dans plusieurs pays, gouverneur de plusieurs régions) → années distinctes → HORS (mono-poste
# survit). (relation, classe, qualif, source, ymin, ymax, exclure_qid).
FONCTIONS = [
    ("annee_fin_mandat_ambassadeur", "Q121998", "P582",
     "Wikidata/QLever — année de fin de mission d'un ambassadeur (P39 Q121998, qualif P582)", -4000, 2026, None),
    ("annee_debut_mandat_ambassadeur", "Q121998", "P580",
     "Wikidata/QLever — année de début de mission d'un ambassadeur (P39 Q121998, qualif P580)", -4000, 2026, None),
    ("annee_fin_mandat_gouverneur", "Q132050", "P582",
     "Wikidata/QLever — année de fin de mandat d'un gouverneur (P39 Q132050, qualif P582)", -4000, 2026, None),
    ("annee_debut_mandat_gouverneur", "Q132050", "P580",
     "Wikidata/QLever — année de début de mandat d'un gouverneur (P39 Q132050, qualif P580)", -4000, 2026, None),
]

# Juges (haute fonction judiciaire = branche de l'État, T8). Q16533. Multi-cours → HORS. Législateurs/députés
# ÉCARTÉS du patron : réélus → fins multiples → quasi tout HORS (rendement nul) ; vice-président Q42178 trop
# générique (VP d'organisations). (relation, classe, qualif, source, ymin, ymax, exclure_qid).
JUGES = [
    ("annee_fin_mandat_juge", "Q16533", "P582",
     "Wikidata/QLever — année de fin de charge d'un juge (P39 Q16533, qualif P582)", -4000, 2026, None),
    ("annee_debut_mandat_juge", "Q16533", "P580",
     "Wikidata/QLever — année de début de charge d'un juge (P39 Q16533, qualif P580)", -4000, 2026, None),
]


# ============================================================================================
#  PATRON ENTITÉ-QUALIFICATIF — succession de dirigeants (P39 « fonction occupée » + qualificatif ENTITÉ).
#  Cousin entité→entité du patron DATE-QUALIFICATIF (règnes) : la SUCCESSION dans une fonction vit dans les
#  QUALIFICATIFS d'un statement P39 — pq:P1365 (« remplace » = prédécesseur) / pq:P1366 (« remplacé par » =
#  successeur), inaccessibles à wdt:. On exige PERSONNE→PERSONNE (les deux wdt:P31 wd:Q5) + libellés FR.
#  FAUX=0 : `publie` applique le fonctionnel → une personne à >1 prédécesseur/successeur distinct (= plusieurs
#  fonctions occupées, ex. Macron ministre+président) → HORS ; l'homonyme (2 Q-ID, même libellé FR, valeurs
#  divergentes) → conflit → drop. Anti-auto-référence (e != v) comme ingere_etat_vers_etat. Seules survivent les
#  personnes à succession UNIQUE = fait non ambigu (Élisabeth II → George VI / → Charles III).
def _pull_succession(relation, pq_prop, objet_q5=True):
    """Tire (personne_fr, valeur_fr) depuis le qualificatif ENTITÉ pq_prop d'un statement P39. Le SUJET est
    toujours une personne (wd:Q5). `objet_q5` : True = l'objet est AUSSI une personne (succession P1365/P1366) ;
    False = l'objet est n'importe quelle entité nommée FR (circonscription P768, instance/institution…). Réutilise
    le snapshot _raw si présent (offline). _paires écarte Q-ID nus / libellés <2 car."""
    contrainte_obj = "wdt:P31 wd:Q5 ; " if objet_q5 else ""
    q = f"""SELECT ?eLabel ?vLabel WHERE {{
      ?e {_P_P39} ?st .
      ?st <http://www.wikidata.org/prop/qualifier/{pq_prop}> ?o .
      ?o {contrainte_obj}rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e wdt:P31 wd:Q5 ; rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch(relation, q)
    return IQ._paires(rows, "eLabel", "vLabel")


def ingere_succession(relation, pq_prop, source, categorie="passe", objet_q5=True):
    """Ingère une relation ENTITÉ-QUALIFICATIF d'un statement P39 (qualificatif entité pq_prop). `objet_q5` :
    True = objet personne (succession P1365/P1366) ; False = objet entité quelconque (circonscription P768…).
    Garde-fous comme ingere_etat_vers_etat : anti-auto-réf + fonctionnel (publie) multi→HORS + réconcil. homonymes."""
    cible = "personne→personne" if objet_q5 else "personne→entité"
    print(f"== {relation} (P39+pq:{pq_prop}, {cible}, anti-auto-réf) ==")
    paires = _pull_succession(relation, pq_prop, objet_q5=objet_q5)
    sans_auto = [(e, v) for e, v in paires if e != v]
    n_auto = len(paires) - len(sans_auto)
    print(f"  {len(paires)} paires brutes, {n_auto} auto-référence(s)(HORS).")
    return IQ.publie(relation, categorie, source, sans_auto)


# (relation, qualificatif, source, objet_q5). « passe » = fait historique borné (figé par la réalité).
SUCCESSIONS = [
    ("predecesseur_personne", "P1365",
     "Wikidata/QLever — prédécesseur d'une personne dans sa fonction (P39, qualificatif P1365)", True),
    ("successeur_personne", "P1366",
     "Wikidata/QLever — successeur d'une personne dans sa fonction (P39, qualificatif P1366)", True),
    # Circonscription électorale représentée par un élu (qualificatif pq:P768 d'un mandat P39). Objet = lieu/
    # district (PAS Q5). Fonctionnel : élu de plusieurs circonscriptions distinctes → HORS ; mono-circonscription
    # (y compris réélu dans la MÊME) survit = fait borné (la circonscription représentée est figée par la réalité).
    ("circonscription_electorale_personne", "P768",
     "Wikidata/QLever — circonscription électorale d'un élu (P39, qualificatif P768)", False),
    # Autres qualificatifs-entité bornés d'un mandat P39 (objet entité quelconque, fonctionnel multi→HORS).
    ("groupe_parlementaire_personne", "P4100",
     "Wikidata/QLever — groupe parlementaire d'un élu (P39, qualificatif P4100)", False),
    ("diocese_personne", "P708",
     "Wikidata/QLever — diocèse d'un ecclésiastique (P39, qualificatif P708)", False),
    # Nommé par (pq:P748 « appointed by ») RESTREINT à un appariteur PERSONNE (Q5→Q5) = nomination par un chef
    # d'État/de gouvernement, fait borné & non ambigu. Fonctionnel : nommé par >1 personne distincte → HORS.
    ("nomme_par_personne", "P748",
     "Wikidata/QLever — personne ayant nommé un titulaire de fonction (P39, qualificatif P748, appariteur Q5)", True),
    # Élection d'accès (pq:P2715 « élu lors de ») : l'élection par laquelle l'élu a obtenu son mandat. Objet TOUJOURS
    # une élection (homogène, vérifié). Fonctionnel : élu lors de >1 élection distincte (réélu) → HORS ; mono-élection
    # survit = fait borné-historique (l'élection passée est figée). ≠ date_evenement (sujet = élu, pas l'élection).
    ("election_acces_personne", "P2715",
     "Wikidata/QLever — élection lors de laquelle une personne a obtenu son mandat (P39, qualificatif P2715)", False),
    # DIFFÉRÉ : legislature_personne (pq:P2937, ~70k fonctionnels) — fait vrai mais procédural/peu utile + sous-
    # ensemble fonctionnel biaisé (élus mono-mandat) + ancrage indépendant difficile. Snapshot _raw prêt si repris.
]


# ============================================================================================
#  RELATIONS T8 — patron DATE : (relation, classe, prop, source, ymin, ymax[, categorie])
#  Plages LARGES mais historiques : but = écarter saisie aberrante / date future, pas filtrer le réel.
#  ymax = 2026 (présent) : aucune fondation/dissolution/événement n'est postérieur à aujourd'hui.
# ============================================================================================
DATES = [
    ("annee_fondation_pays", "Q6256", "P571",
     "Wikidata/QLever — année de fondation/création (P571) d'un pays", -4000, 2026),
    ("annee_creation_organisation", "Q43229", "P571",
     "Wikidata/QLever — année de création (P571) d'une organisation", -1000, 2026),
    ("annee_dissolution", "Q43229", "P576",
     "Wikidata/QLever — année de dissolution/abolition (P576) d'une organisation", -1000, 2026),
    ("date_evenement", "Q1190554", "P585",
     "Wikidata/QLever — année d'un événement (P585)", -4000, 2026),
]

# Dates de BATAILLES (Q178561) via P580 début / P582 fin — distinctes de date_evenement (P585, point unique) :
# les batailles pluri-journalières portent un début/fin propre. Fonctionnel (publie) -> homonymes multi-année HORS
# (« bataille des Ardennes » 1914 vs 1944 droppée). Borné-historique, objet homogène (la bataille nommée).
BATAILLES = [
    ("annee_debut_bataille", "Q178561", "P580",
     "Wikidata/QLever — année de début (P580) d'une bataille", -4000, 2026),
    ("annee_fin_bataille", "Q178561", "P582",
     "Wikidata/QLever — année de fin (P582) d'une bataille", -4000, 2026),
]


def ingere_batailles():
    for rel, cls, prop, src, lo, hi, *rest in BATAILLES:
        ingere_date(rel, cls, prop, src, lo, hi, categorie=(rest[0] if rest else "passe"))


# Date d'ENTRÉE EN VIGUEUR d'un traité (Q131569) via P7588 — distincte de annee_signature_traite (P585 signature).
# Un traité signé une année peut entrer en vigueur une autre (ex. Lisbonne signé 2007, en vigueur 2009). Fonctionnel.
TRAITES = [
    ("annee_entree_vigueur_traite", "Q131569", "P7588",
     "Wikidata/QLever — année d'entrée en vigueur (P7588) d'un traité", -1000, 2026),
    # SIGNATURE (P585) : re-produit via t8 moderne (l'ancien pipeline REST rejetait « traité de Versailles »
    # 1919 à cause des homonymes 1756/1768/1783/1787 — la dominance-notoriété tranche : 135 wikis vs ≤15).
    ("annee_signature_traite", "Q131569", "P585",
     "Wikidata/QLever — année de signature (P585) d'un traité ; homonymes tranchés par NOTORIÉTÉ "
     "(sitelinks ≥8×, ex. traité de Versailles = 1919), sinon HORS", -1000, 2026),
]

# GUERRES (Q198) via P580/P582 : l'ancien pipeline REST n'avait NI la Première NI la Seconde Guerre mondiale.
# Mêmes garde-fous que les batailles ; dominance-notoriété pour les homonymes.
GUERRES = [
    ("annee_debut_guerre", "Q198", "P580",
     "Wikidata/QLever — année de début (P580) d'une guerre ; homonymes tranchés par notoriété (sitelinks)",
     -4000, 2026),
    ("annee_fin_guerre", "Q198", "P582",
     "Wikidata/QLever — année de fin (P582) d'une guerre ; homonymes tranchés par notoriété (sitelinks)",
     -4000, 2026),
]


def ingere_guerres():
    for rel, cls, prop, src, lo, hi, *rest in GUERRES:
        ingere_date(rel, cls, prop, src, lo, hi, categorie=(rest[0] if rest else "passe"))


def ingere_traites():
    for rel, cls, prop, src, lo, hi, *rest in TRAITES:
        ingere_date(rel, cls, prop, src, lo, hi, categorie=(rest[0] if rest else "passe"))


# Dates de SIÈGES (Q188055) via P580/P582, en EXCLUANT à la source les sièges déjà typés bataille (Q178561,
# déjà couverts par annee_debut/fin_bataille) -> ZÉRO redondance. Mêmes garde-fous que ingere_date.
SIEGES = [
    ("annee_debut_siege", "Q188055", "P580",
     "Wikidata/QLever — année de début (P580) d'un siège (hors ceux déjà typés bataille)", -4000, 2026),
    ("annee_fin_siege", "Q188055", "P582",
     "Wikidata/QLever — année de fin (P582) d'un siège (hors ceux déjà typés bataille)", -4000, 2026),
]


def _labels_relation(rel):
    """Ensemble des libellés d'entité déjà publiés dans une relation (lecture offline du .jsonl)."""
    import os, json as _json
    chemin = os.path.join("datasets", "lecteur", f"{rel}.jsonl")
    out = set()
    if os.path.exists(chemin):
        for l in open(chemin, encoding="utf-8"):
            l = l.strip()
            if not l:
                continue
            o = _json.loads(l)
            if "entite" in o:
                out.add(o["entite"])
    return out


def ingere_sieges():
    # bataille correspondante (même borne temporelle) -> on exclut les libellés déjà présents pour éviter toute
    # ambiguïté cross-relation (« siège d'Almeida » = bataille 1762 ET siège 1810 = deux sièges réels distincts).
    bataille_de = {"annee_debut_siege": "annee_debut_bataille", "annee_fin_siege": "annee_fin_bataille"}
    for rel, cls, prop, src, lo, hi in SIEGES:
        exclus = _labels_relation(bataille_de[rel])
        q = f"""SELECT ?eLabel ?v WHERE {{
          ?e wdt:P31/wdt:P279* wd:{cls} ; wdt:{prop} ?v .
          FILTER NOT EXISTS {{ ?e wdt:P31/wdt:P279* wd:Q178561 }}
          ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
        }}"""
        rows = IQ._charge_ou_fetch(rel, q)
        paires, hors, collision = [], 0, 0
        for r in rows:
            e = IQ.val(r, "eLabel"); v = IQ.val(r, "v")
            if not e or not v or IQ._est_qid(e) or _est_date_nue(e):
                continue
            if e in exclus:                       # libellé déjà dans la relation bataille -> ambigu -> HORS
                collision += 1
                continue
            an = _annee(v)
            if an is None:
                continue
            if lo <= int(an) <= hi:
                paires.append((e, an))
            else:
                hors += 1
        print(f"== {rel} ({prop}, {cls} hors Q178561) : {len(paires)} gardées, {hors} hors-plage(HORS), "
              f"{collision} collision-libellé-bataille(HORS) ==")
        IQ.publie(rel, "passe", src, paires)


# Dates d'OPÉRATIONS MILITAIRES (Q645883) via P580/P582 — codenames (Overlord, Barbarossa...) ; on EXCLUT à la
# source bataille Q178561 ET siège Q188055 (déjà couverts) + les libellés déjà publiés dans ces relations = 0 ambiguïté.
OPERATIONS = [
    ("annee_debut_operation_militaire", "P580",
     "Wikidata/QLever — année de début (P580) d'une opération militaire (hors bataille/siège)",
     ["annee_debut_bataille", "annee_debut_siege"]),
    ("annee_fin_operation_militaire", "P582",
     "Wikidata/QLever — année de fin (P582) d'une opération militaire (hors bataille/siège)",
     ["annee_fin_bataille", "annee_fin_siege"]),
]


def ingere_operations():
    for rel, prop, src, rels_exclues in OPERATIONS:
        exclus = set()
        for r in rels_exclues:
            exclus |= _labels_relation(r)
        q = f"""SELECT ?eLabel ?v WHERE {{
          ?e wdt:P31/wdt:P279* wd:Q645883 ; wdt:{prop} ?v .
          FILTER NOT EXISTS {{ ?e wdt:P31/wdt:P279* wd:Q178561 }}
          FILTER NOT EXISTS {{ ?e wdt:P31/wdt:P279* wd:Q188055 }}
          ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
        }}"""
        rows = IQ._charge_ou_fetch(rel, q)
        paires, hors, collision = [], 0, 0
        for r in rows:
            e = IQ.val(r, "eLabel"); v = IQ.val(r, "v")
            if not e or not v or IQ._est_qid(e) or _est_date_nue(e):
                continue
            if e in exclus:
                collision += 1
                continue
            an = _annee(v)
            if an is None:
                continue
            if -4000 <= int(an) <= 2026:
                paires.append((e, an))
            else:
                hors += 1
        print(f"== {rel} ({prop}, Q645883 hors bataille/siège) : {len(paires)} gardées, {hors} hors-plage(HORS), "
              f"{collision} collision-libellé(HORS) ==")
        IQ.publie(rel, "passe", src, paires)

# Relations politiques OUVERTES (entité -> entité, fonctionnelles) : ancres + fonctionnel comme les lieu_*.
OUVERTES = [
    # (relation, propriété, catégorie, source, classe)
    ("predecesseur_etat", "P155", "passe",
     "Wikidata/QLever — État précédent (P155, « suit ») d'un État", "Q6256"),
    ("pays_election", "P17", "passe",
     "Wikidata/QLever — pays (P17) d'une élection (sujet Q40231)", "Q40231"),
    ("pays_referendum", "P17", "passe",
     "Wikidata/QLever — pays (P17) d'un référendum (sujet Q43109)", "Q43109"),
]


def ingere_etat_vers_etat(relation, propriete, categorie, source, classe_qid):
    """Comme IQ._ingere_x_vers_entite MAIS rejette les AUTO-RÉFÉRENCES (entité == valeur) : deux items Wikidata
    distincts au libellé FR identique (« taïfa d'Algésiras » refondée) rendraient le fait « X précède X »
    absurde/trompeur côté lecteur (qui indexe par libellé). FAUX=0 : on ne garde que e != v + le fonctionnel."""
    print(f"== {relation} (Wikidata/QLever {propriete}, anti-auto-réf) ==")
    filtre = f"?e wdt:P31/wdt:P279* wd:{classe_qid} ; " if classe_qid else "?e "
    q = f"""SELECT ?eLabel ?vLabel WHERE {{
      {filtre}wdt:{propriete} ?o .
      ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch(relation, q)
    paires = IQ._paires(rows, "eLabel", "vLabel")
    sans_auto = [(e, v) for e, v in paires if e != v]
    n_auto = len(paires) - len(sans_auto)
    print(f"  {len(rows)} lignes brutes, {n_auto} auto-référence(s)(HORS).")
    return IQ.publie(relation, categorie, source, sans_auto)


def ingere_vainqueur_election():
    """vainqueur_election : élection (Q40231) -> personne ÉLUE (P991 « candidat élu », objet borné à Q5).
    Direction INVERSE de election_acces_personne (personne->élection) -> complémentaire, non redondant.
    Fonctionnel (publie) : une élection à >1 élu distinct (législatives multi-sièges) -> HORS ; seuls les
    scrutins mono-vainqueur (présidentielles, partielles, circonscriptions uninominales) survivent.
    Double homogénéité : sujet = élection, objet = personne. Anti-auto-réf défensif (e!=v)."""
    relation = "vainqueur_election"
    source = "Wikidata/QLever — candidat élu (P991) d'une élection (sujet Q40231, objet personne Q5)"
    print(f"== {relation} (P991, sujet Q40231, objet Q5) ==")
    q = """SELECT ?eLabel ?vLabel WHERE {
      ?e wdt:P991 ?o ; wdt:P31/wdt:P279* wd:Q40231 .
      ?o wdt:P31 wd:Q5 .
      ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    rows = IQ._charge_ou_fetch(relation, q)
    paires = IQ._paires(rows, "eLabel", "vLabel")
    sans_auto = [(e, v) for e, v in paires if e != v]
    print(f"  {len(rows)} lignes brutes, {len(paires) - len(sans_auto)} auto-réf(HORS).")
    return IQ.publie(relation, "passe", source, sans_auto)


def ingere_fonction_brigue_election():
    """fonction_brigue_election : élection (Q40231) -> fonction/charge BRIGUÉE (P541 « office contested »).
    Complémentaire de vainqueur_election (qui gagne) et election_acces_personne. Fonctionnel (publie) : une
    élection à >1 fonction distincte (générales US = président + vice-président + collège électoral) -> HORS ;
    seules les élections mono-fonction (présidentielles : -> président de la République) survivent. BORNÉ : la
    charge briguée est FIXÉE par l'élection (vraie même avant le résultat). P541 a pour range une charge publique
    -> objet homogène ; on garde la sémantique P541 + fonctionnel + libellé FR (pas de filtre de classe objet
    qui risquerait de droper des charges non typées Q4164871). Anti-auto-réf défensif."""
    relation = "fonction_brigue_election"
    source = "Wikidata/QLever — fonction/charge briguée (P541) d'une élection (sujet Q40231)"
    print(f"== {relation} (P541, sujet Q40231) ==")
    q = """SELECT ?eLabel ?vLabel WHERE {
      ?e wdt:P541 ?o ; wdt:P31/wdt:P279* wd:Q40231 .
      ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    rows = IQ._charge_ou_fetch(relation, q)
    paires = IQ._paires(rows, "eLabel", "vLabel")
    sans_auto = [(e, v) for e, v in paires if e != v]
    print(f"  {len(rows)} lignes brutes, {len(paires) - len(sans_auto)} auto-réf(HORS).")
    return IQ.publie(relation, "passe", source, sans_auto)


# Famille pays_* (pays DE l'événement, P17) — extension : objet=pays homogène, fonctionnel (homonyme->HORS),
# NON redondant avec les dates (date_evenement donne l'année ; ici le pays). Un seul gate pour le lot.
PAYS_EVENEMENTS = [
    ("pays_revolution", "Q10931", "Wikidata/QLever — pays (P17) d'une révolution"),
    ("pays_massacre", "Q3199915", "Wikidata/QLever — pays (P17) d'un massacre"),
    # pays_rebellion (Q124757) REJETÉ : la classe subsume des « transports de déportation » (non-rébellions) = bruit sémantique.
    ("pays_manifestation", "Q273120", "Wikidata/QLever — pays (P17) d'une manifestation/protestation"),
    ("pays_siege", "Q188055", "Wikidata/QLever — pays (P17) d'un siège"),
    # pays_recensement (Q39825) REJETÉ : 92% = recensements MUNICIPAUX de masse (villages Bohême 1890) = trivia granulaire skewé, ≠ concept « recensement national ».
    ("pays_attentat", "Q2223653", "Wikidata/QLever — pays (P17) d'un attentat/attaque terroriste"),
    ("pays_greve", "Q49776", "Wikidata/QLever — pays (P17) d'une grève"),
    # pays_emeute (Q124734) REJETÉ : la classe subsume des « tentatives de coup d'État » (≠ émeutes) = bruit sémantique.
]


def ingere_pays_evenements():
    for rel, classe, src in PAYS_EVENEMENTS:
        ingere_etat_vers_etat(rel, "P17", "passe", src, classe)


def ingere_etat_vers_etat_exclu(relation, propriete, source, classe_qid, exclure_classes, exclure_relations=()):
    """Comme ingere_etat_vers_etat mais EXCLUT à la source les sujets aussi typés sous une des `exclure_classes`
    (FILTER NOT EXISTS) — pour les classes qui en subsument d'autres déjà couvertes (ex. opération militaire Q645883
    subsume bataille Q178561 + siège Q188055 -> évite la duplication cross-relation). `exclure_relations` retire en
    plus les libellés déjà publiés dans ces relations (dédup-libellé -> zéro ambiguïté cross-relation)."""
    excl = "".join(f"\n      FILTER NOT EXISTS {{ ?e wdt:P31/wdt:P279* wd:{q} }}" for q in exclure_classes)
    bannis = set()
    for r in exclure_relations:
        bannis |= _labels_relation(r)
    print(f"== {relation} ({propriete}, {classe_qid} hors {'+'.join(exclure_classes)}) ==")
    q = f"""SELECT ?eLabel ?vLabel WHERE {{
      ?e wdt:P31/wdt:P279* wd:{classe_qid} ; wdt:{propriete} ?o .{excl}
      ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if e != v and e not in bannis]
    return IQ.publie(relation, "passe", source, paires)


def ingere_tout():
    for rel, cls, prop, src, lo, hi, *rest in DATES:
        cat = rest[0] if rest else "passe"
        ingere_date(rel, cls, prop, src, lo, hi, categorie=cat)
    for rel, prop, cat, src, cls in OUVERTES:
        ingere_etat_vers_etat(rel, prop, cat, src, classe_qid=cls)


def republie():
    """REPUBLICATION 100 % OFFLINE (depuis les snapshots _raw) des relations dont on a durci le filtrage :
    date_evenement (filtre libellé étendu : dates/années nues) + predecesseur_etat (anti-auto-référence).
    Aucun fetch réseau. À lancer après une évolution des garde-fous, puis rejouer valide_lecteur_t8.py."""
    for rel, cls, prop, src, lo, hi, *rest in DATES:
        if rel == "annee_creation_organisation":
            continue  # pas de snapshot _raw (jamais fetché) -> rien à republier offline
        ingere_date(rel, cls, prop, src, lo, hi, categorie=(rest[0] if rest else "passe"))
    for rel, prop, cat, src, cls in OUVERTES:
        ingere_etat_vers_etat(rel, prop, cat, src, classe_qid=cls)


def sonde():
    """Inspecte chaque veine DATE SANS écrire : compte, étendue d'années, échantillon -> juger plage/honnêteté."""
    for rel, cls, prop, _src, lo, hi, *_ in DATES:
        triples, rej = _pull_date(rel, cls, prop, filtre_libelle=FILTRES_LIBELLE.get(rel))
        if not triples:
            print(f"  [{rel:28s}] 0 date (classe/prop vide ?)")
            continue
        ans = sorted(int(a) for _e, a, _b in triples)
        dans = sum(1 for a in ans if lo <= a <= hi)
        ech = triples[:4]
        print(f"  [{rel:28s}] n={len(triples):6d}  min={ans[0]}  max={ans[-1]}  "
              f"med={ans[len(ans)//2]}  dans[{lo},{hi}]={dans}  ex={[(e, a) for e, a, _b in ech]}")


def ingere_successions():
    """Patron ENTITÉ-QUALIFICATIF (succession personne→personne). Réutilise les snapshots _raw pré-fetchés
    (offline) ; à lancer SEUL (1 chargement lecteur)."""
    for rel, pq, src, objet_q5 in SUCCESSIONS:
        ingere_succession(rel, pq, src, objet_q5=objet_q5)


# Relations DIRECTES personne→entité (wdt:, hors P39) — patron entité→entité via ingere_etat_vers_etat (classe Q5,
# anti-auto-réf + fonctionnel). (relation, propriété, catégorie, source, classe_qid). Snapshots _raw pré-fetchés
# par `_prefetch_succession.py <arg>` (même requête → réutilisés offline).
DIRECTES_PERSONNE = [
    # Maison/famille noble (P53) : appartenance dynastique figée par la naissance ; objet homogène (maison/famille/
    # dynastie/clan noble). Multi (double maison par mariage/sous-branche) → HORS. Thème dynastique (cf annee_*_dynastie).
    ("maison_noble_personne", "P53", "passe",
     "Wikidata/QLever — maison/famille noble d'une personne (wdt:P53, ensemble fermé ; multi → HORS)", "Q5"),
    # Parti politique d'une personne (P102, « membre d'un parti politique ») : objet TOUJOURS un parti (homogène).
    # DISTINCT de membre_de (T6 = P463, organisations). Thème politique = T8. Multi-parti (transfuge) → HORS ;
    # mono-parti survit = affiliation bornée. Anti-auto-réf inutile (parti ≠ personne) mais conservé sans effet.
    ("parti_personne", "P102", "convention",
     "Wikidata/QLever — parti politique d'une personne (wdt:P102 ; multi-parti → HORS)", "Q5"),
]


def ingere_directes_personne():
    """Relations DIRECTES personne→entité (wdt: hors P39). Réutilise les snapshots _raw (offline) ; lancer SEUL."""
    for rel, prop, cat, src, cls in DIRECTES_PERSONNE:
        ingere_etat_vers_etat(rel, prop, cat, src, classe_qid=cls)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sonde":
        sonde()
    elif len(sys.argv) > 1 and sys.argv[1] == "republie":
        republie()
    elif len(sys.argv) > 1 and sys.argv[1] == "succession":
        ingere_successions()
    elif len(sys.argv) > 1 and sys.argv[1] == "directes":
        ingere_directes_personne()
    elif len(sys.argv) > 1 and sys.argv[1] == "batailles":
        ingere_batailles()
    elif len(sys.argv) > 1 and sys.argv[1] == "traites":
        ingere_traites()
    elif len(sys.argv) > 1 and sys.argv[1] == "guerres":
        ingere_guerres()
    elif len(sys.argv) > 1 and sys.argv[1] == "sieges":
        ingere_sieges()
    elif len(sys.argv) > 1 and sys.argv[1] == "operations":
        ingere_operations()
    elif len(sys.argv) > 1 and sys.argv[1] == "pays_evenements":
        ingere_pays_evenements()
    elif len(sys.argv) > 1 and sys.argv[1] == "election":
        ingere_vainqueur_election()
    elif len(sys.argv) > 1 and sys.argv[1] == "fonction_election":
        ingere_fonction_brigue_election()
    elif len(sys.argv) > 1 and sys.argv[1] == "pays_election":
        ingere_etat_vers_etat("pays_election", "P17", "passe",
                              "Wikidata/QLever — pays (P17) d'une élection (sujet Q40231)", "Q40231")
    elif len(sys.argv) > 1 and sys.argv[1] == "pays_referendum":
        ingere_etat_vers_etat("pays_referendum", "P17", "passe",
                              "Wikidata/QLever — pays (P17) d'un référendum (sujet Q43109)", "Q43109")
    else:
        ingere_tout()
