# -*- coding: utf-8 -*-
"""
TRONC DE COMPRÉHENSION — Phase 1 (clé de voûte) : `acte(signal, contexte) -> Faisceau` (SPEC_TRONC_COMPREHENSION §7-§10).

Le moteur UNIQUE qui remplace, à terme, la cascade des ~60 caps : toute entrée est classée dans EXACTEMENT un
(ou plusieurs, tenus en PARALLÈLE — G2) des 11 ACTES DE PAROLE FERMÉS (§8), avec entités/relation/régime
extraits UNE fois et un routage déclaré vers la faculté EXISTANTE qui sait servir l'acte. Phase 1 = le motif :
  • `acte()`         : signal -> Faisceau (population de Candidats parallèles, jamais un sens collapsé en silence) ;
  • `repli()`        : acte INCONNU / cascade épuisée -> REPLI HONNÊTE intent-aware (§10.4, garde G6) :
                       « voici ce que j'ai compris + ce que je sais faire » — jamais de garbage (ni fausse
                       correction ortho, ni recherche web du texte littéral) ;
  • `attunement()`   : acte EXPRIMER_ÉTAT -> lecture d'état en SUPPOSITION (§13 : jamais « je ressens »).

NB nommage : `comprehension.py` existe déjà (abstraction par compression du harnais d'invention) — le moteur
conversationnel de la spec vit donc ici sous le nom du document : le TRONC.

DEUX ÉTAGES DE CLASSIFICATION (« explicite au cœur, appris seulement en périphérie ») :
  1. CŒUR EXPLICITE : détecteurs fermés par acte (motifs versionnés, auditables) — seuls eux donnent une
     confiance élevée ; le régime vient du gardien `classifieur_bornage` (réutilisé, jamais dupliqué).
  2. PÉRIPHÉRIE gzip-kNN (U13, « compression = intelligence ») : quand AUCUN détecteur ne matche, la distance
     de compression (NCD, zlib, zéro entraînement) PROPOSE un acte voisin des exemples embarqués — toujours
     typée PROPOSITION à confiance bornée (≤ 0,45), jamais routée comme un fait : c'est l'humain qui vérifie
     (boucle de rétroaction du repli).

FAUX=0 STRUCTUREL (G1/G7) : un Candidat n'est TRANCHÉ que si un VRAI juge a évalué (ici : le juge arithmétique
AST du classifieur de bornage, seul juge interne). Tout le reste est NON-TRANCHÉ et porte une RECETTE (« quelle
faculté invoquer »), pas une valeur. Ce module ne FABRIQUE jamais une réponse factuelle.

IMPORT LÉGER (OOM-safe, même discipline qu'assistant_nl) : stdlib + classifieur_bornage (stdlib pur). Aucun
import du lecteur/pipeline — les facultés sont ROUTÉES par nom, les consommateurs existants les exécutent.
"""
from __future__ import annotations

import dataclasses
import json
import os
import re
import time
import unicodedata
import zlib

import classifieur_bornage as _CB

# ── LA CARTE FERMÉE DES 11 ACTES (§8) — s'étend par décision explicite, jamais par dérive ──
INTERROGER_FAIT = "interroger_fait"   # un fait vérifié          -> lecteur / lookup vérifié
CALCULER = "calculer"                 # un calcul exact           -> juge arithmétique AST
RAISONNER = "raisonner"               # inférence sur des faits   -> moteur de raisonnement
DEMANDER_AVIS = "demander_avis"       # avis sur du non-tranché   -> _cap_avis (Pareto/Condorcet) + pour/contre
CREER = "creer"                       # inventer/brainstormer     -> amplificateur de besoin (redirige)
META = "meta"                         # sur l'échange lui-même    -> méta/clarification
SOCIAL = "social"                     # politesse pure            -> politesse
EXPRIMER_ETAT = "exprimer_etat"       # émotion/état exprimé      -> attunement (supposition)
QUOTIDIEN = "quotidien"               # météo/heure/date/site     -> _cap_quotidien / _cap_site
AGIR = "agir"                         # un ordre                  -> outils
INCONNU = "inconnu"                   # rien avec confiance       -> repli honnête intent-aware (§10.4)

ACTES = (INTERROGER_FAIT, CALCULER, RAISONNER, DEMANDER_AVIS, CREER, META, SOCIAL,
         EXPRIMER_ETAT, QUOTIDIEN, AGIR, INCONNU)

# ── statuts du Candidat (§7) : TRANCHÉ exige un juge réel ; le reste n'affirme RIEN ──
TRANCHE = "tranche"
NON_TRANCHE = "non_tranche"
STATUT_INCONNU = "inconnu"

# Faculté consommatrice EXISTANTE par acte (§8, colonne « Faculté ») + ce que Provara SAIT FAIRE pour cet acte
# (phrase du repli honnête : montrer la capacité RÉELLE, jamais une promesse).
FACULTES = {
    INTERROGER_FAIT: ("lecteur / lookup vérifié",
                      "répondre un fait vérifié avec sa provenance — « capitale de l'Espagne », "
                      "« population du Japon », « qui a écrit 1984 ? »"),
    CALCULER: ("juge arithmétique (AST évalué)",
               "calculer exactement — « combien font 12*7 ? », « 3+4*5 »"),
    RAISONNER: ("moteur de raisonnement (déduction/comparaison/transitif)",
                "comparer, déduire, classer sur des faits vérifiés — « quelle différence entre X et Y ? », "
                "« le plus peuplé d'Afrique »"),
    DEMANDER_AVIS: ("_cap_avis (Pareto/Condorcet) + pour/contre sourcé",
                    "trancher par CRITÈRES mesurables (jamais par goût) et montrer le pour/contre sourcé — "
                    "« le meilleur entre X et Y ? »"),
    CREER: ("amplificateur de besoin (moteur d'invention)",
            "décomposer un besoin CONCRET en leviers physiques — « comment faire X sans Y ? » (je ne sors "
            "pas d'idée du chapeau : j'amplifie la tienne)"),
    META: ("méta/clarification",
           "dire honnêtement qui je suis, ce que je sais faire, reformuler ou corriger l'échange"),
    SOCIAL: ("politesse",
             "répondre au salut/merci — puis répondre à ta vraie question"),
    EXPRIMER_ETAT: ("attunement (supposition, jamais affirmé)",
                    "entendre ton état (sans prétendre le ressentir) et t'aider sur le point concret qui bloque"),
    QUOTIDIEN: ("_cap_quotidien / _cap_site",
                "la météo réelle sourcée, l'heure et la date locales, lire un site que tu nommes"),
    AGIR: ("outils (traduction, schéma, lecture, oubli RGPD, réglages)",
           "exécuter un ordre outillé — traduire, tracer un schéma, lire un document, oublier tes données"),
    INCONNU: ("repli honnête intent-aware",
              "te dire ce que j'ai compris et te laisser me corriger — jamais deviner"),
}

# Intitulé HUMAIN de chaque acte (membrane §10.3 : forme humaine uniquement à la sortie).
_INTITULES = {
    INTERROGER_FAIT: "tu demandes un FAIT vérifiable",
    CALCULER: "tu demandes un CALCUL",
    RAISONNER: "tu demandes un RAISONNEMENT (comparaison/déduction) sur des faits",
    DEMANDER_AVIS: "tu demandes mon AVIS sur du non-tranché",
    CREER: "tu veux INVENTER / créer quelque chose",
    META: "tu m'interroges sur MOI ou sur notre échange",
    SOCIAL: "tu me salues / me remercies",
    EXPRIMER_ETAT: "tu exprimes un ÉTAT ou un ressenti",
    QUOTIDIEN: "tu demandes du QUOTIDIEN (météo, heure, date, un site nommé)",
    AGIR: "tu me donnes un ORDRE outillé",
    INCONNU: "je n'arrive pas à rattacher ta demande à un de mes actes",
}


# ═══════════════ LE FAISCEAU (§7) — population de candidats parallèles, jamais collapsée en silence ═══════════════
@dataclasses.dataclass(frozen=True)
class Candidat:
    """Un sens candidat tenu en parallèle. G1 : ne pose JAMAIS un fait absent du store — `reponse` n'est une
    valeur que si `statut == TRANCHE` (juge réel exécuté) ; sinon c'est une RECETTE (la faculté à invoquer)."""
    intention: str
    entites: tuple = ()
    relation: str | None = None
    regime: str = ""                       # borne | non_borne | indecidable (classifieur_bornage)
    statut: str = NON_TRANCHE              # TRANCHÉ(fait) | NON-TRANCHÉ(supposition) | inconnu
    reponse: str = ""                      # valeur (si TRANCHÉ) ou recette-de-calcul (faculté)
    ancrage: str = "non ancré"             # source/preuve, ou « non ancré »
    signal_discriminant: str = ""          # ce qui séparerait ce candidat des autres (question minimale, §10)
    confiance: float = 0.0                 # [0,1] — élevée seulement pour le cœur explicite
    provenance: str = ""                   # lignée : quel détecteur/proposeur a produit ce sens


@dataclasses.dataclass(frozen=True)
class Faisceau:
    """Le « sens tenu » d'un signal : candidats PARALLÈLES (≥2 si ambiguïté réelle — G2) + contexte."""
    candidats: tuple = ()
    contexte: dict = dataclasses.field(default_factory=dict)

    def meilleur(self) -> Candidat | None:
        return self.candidats[0] if self.candidats else None

    def est_inconnu(self) -> bool:
        """True si AUCUNE hypothèse d'intention n'est tenable (même pas une proposition de périphérie)."""
        m = self.meilleur()
        return m is None or m.intention == INCONNU


# ═══════════════ Normalisation + extraction (individuation d'abord — G3) ═══════════════
def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", t or "").encode("ascii", "ignore").decode().lower()
    t = t.replace("'", " ").replace("’", " ")
    return " ".join(t.split())


# Mots-outils à écarter pour isoler les ENTITÉS (déterminants, interrogatifs, verbes creux, politesse) —
# même famille que assistant_nl._STOP_SUJET (extraction descriptive, jamais une réponse).
_STOP = frozenset(
    "le la les l un une des du de d au aux en dans sur sous pour par avec sans et ou puis donc alors que qui "
    "quoi qu quel quelle quels quelles comment combien quand pourquoi est sont etait sera ce cette ces cet c "
    "il elle on ne pas plus tu te toi moi je nous vous mon ma mes ton ta tes son sa ses stp svp bonjour merci "
    "dis dis-moi donne donnez sais peux pourrais saurais connais cherche trouve montre explique parle parler "
    "veut veux dire signifie fait faire ete avoir etre y a t entre font vaut valent me lui leur se s "
    "rien tout suis pense penses pensez crois avis opinion meilleur meilleure mieux pire penses-tu "
    "aurais aurait auriez truc trucs machin machins bidule bidules chose choses".split())

# « R de E » : la tête nominale AVANT « de » = relation candidate, ce qui suit = entité(s).
_REL_RE = re.compile(r"\b([a-z][a-z-]{2,})\s+(?:de|du|des|d)\s+(?:la\s+|le\s+|les\s+|l\s+)?(.+?)\s*$")
_ENTRE_RE = re.compile(r"\bentre\s+(.+?)\s+et\s+(.+?)(?:\s*[,?]|$)")
_PRONOM_SEUL_RE = re.compile(r"\b(il|elle|ca|cela|lui)\b")


def _mots_contenu(nq: str) -> list:
    return [w for w in nq.split() if len(w) >= 3 and w not in _STOP]


def _relation_entites(nq: str, contexte: dict) -> tuple:
    """Extrait (relation, entités) UNE fois — partagées ensuite par tous les candidats (§7). Descriptif, jamais
    une réponse. L'anaphore du contexte remplace un pronom nu (« il est mort quand ? » + dernier sujet)."""
    q = nq.rstrip(" ?.!")
    m = _ENTRE_RE.search(q)
    if m:                                                     # « entre X et Y » -> deux entités comparées
        e1 = " ".join(_mots_contenu(m.group(1))) or m.group(1).strip()
        e2 = " ".join(_mots_contenu(m.group(2))) or m.group(2).strip()
        rel = next(iter(_mots_contenu(q[:m.start()])), None)
        return rel, tuple(e for e in (e1, e2) if e)
    m = _REL_RE.search(q)
    if m and m.group(1) not in _STOP:
        ent = " ".join(_mots_contenu(m.group(2)))
        if ent:
            return m.group(1), (ent,)
    if contexte.get("anaphore") and _PRONOM_SEUL_RE.search(q):
        return None, (str(contexte["anaphore"]),)            # anaphore résolue depuis le contexte (§7)
    ents = _mots_contenu(q)
    return None, ((" ".join(ents[:6]),) if ents else ())


# ═══════════════ CŒUR EXPLICITE : détecteurs fermés par acte (auditables, versionnés) ═══════════════
_POLI_VOCAB = frozenset(
    "bonjour bonsoir salut coucou hello hey hi merci mercis remercie beaucoup au revoir bientot adieu bye "
    "ca va vas tu bien toi et comment allez vous va tres bonne journee nuit soiree matinee plaisir enchante "
    "super cool ok d accord a plus tard tchao ciao".split())

_META_RE = re.compile(
    r"\b(qui es[- ]?tu|tu es qui|presente[- ]?toi|comment t appelles?[- ]?tu|ton nom|que sais[- ]?tu faire|"
    r"que peux[- ]?tu faire|tu sais faire quoi|quelles sont tes capacites|a quoi sers[- ]?tu|"
    r"comment fonctionnes?[- ]?tu|comment tu fonctionnes|tes sources|d ou viennent tes|"
    r"es[- ]?tu (?:une? )?(?:ia|robot|machine|humaine?|programme|chatbot)|"
    r"que veux[- ]?tu dire|qu est[- ]?ce que tu veux dire|qu entends[- ]?tu par|"
    r"(?:ce n est|c est) pas ce que j (?:ai demande|avais demande)|tu n as pas compris|"
    r"reformule|repete|tu peux repeter)\b")

_METEO_RE = re.compile(r"\b(meteo|quel temps|temps fait[- ]?il|il pleut|il neige|previsions?|degres dehors|"
                       r"parapluie)\b")
_HEURE_RE = re.compile(r"\b(quelle heure|l heure qu il est|heure est[- ]?il)\b")
_DATE_RE = re.compile(r"\b(quel jour sommes[- ]?nous|on est quel jour|quelle est la date|date d aujourd hui|"
                      r"quel jour on est)\b")
# Site NOMMÉ (URL ou domaine à TLD courant) : détecté sur le texte BRUT (les points survivent à la normalisation
# mais la casse/le tiret comptent) — même carte fermée de TLD que repond._SITE_RE, jamais un mot à point accidentel.
_SITE_RE = re.compile(
    r"\b(https?://[^\s»«\"']+"
    r"|(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:fr|com|org|net|io|dev|app|eu|be|ch|ca|ai|info|me)\b"
    r"(?:/[^\s»«\"']*)?)", re.I)

_AGIR_RE = re.compile(
    r"^(?:s il te plait |stp |peux[- ]?tu |pourrais[- ]?tu |tu peux )?"
    r"(traduis|traduire|dessine|trace|affiche|lis|lire|ouvre|visite|oublie|efface|supprime|"
    r"reponds en|regle|active|desactive|quitte|montre[- ]?moi ce que tu sais)\b")

_CREER_RE = re.compile(
    r"\b(invente|inventer|inventons|brainstorm\w*|idees? (?:de|pour)|que (?:puis[- ]?je|pourrais[- ]?je) creer|"
    r"aide[- ]?moi a (?:creer|inventer|concevoir|imaginer)|qu est[- ]?ce que je peux creer|"
    r"comment (?:faire|fabriquer|obtenir) .{2,60} sans )\b")

_ETAT_RE = re.compile(
    r"\b(je suis (?:perdue?|fatiguee?|epuisee?|triste|contente?|heureuse|heureux|enervee?|stressee?|decue?|"
    r"frustree?|nulle?|largue|larguee|decouragee?)|j en ai marre|je n y arrive pas|j y arrive pas|"
    r"ca me (?:soule|saoule|fatigue|stresse|deprime|depasse)|je me sens \w+|"
    r"je trouve (?:ca|cela) (?:dur|difficile|penible|complique|injuste))\b")

_AVIS_RE = re.compile(
    r"\b(que penses[- ]?tu|qu en penses[- ]?tu|t en penses quoi|tu en penses quoi|t en dis quoi|"
    r"ton avis|a ton avis|selon toi|ton opinion|"
    r"le meilleur|la meilleure|le pire|la pire|plus (?:beau|belle|sympa|agreable|interessante?)|"
    r"preferes[- ]?tu|(?:me |tu )(?:recommandes?|conseilles?)|vaut[- ]?il mieux|c est mieux|"
    # jugement évaluatif nu (« il est génial non ? ») : une demande d'accord = une demande d'avis
    r"(?:il|elle|c) est (?:geniale?|nulle?|super|horrible|magnifique|moche|top|incroyable)s?)\b")

_RAISONNER_RE = re.compile(
    r"\b(plus \w+ que|moins \w+ que|difference entre|point commun|en commun|"
    r"est[- ]?(?:ce|il|elle) (?:une?|le|la) |si .{3,60} alors|classe(?:ment)?\b|compare\w*|"
    r"combien de \w+ (?:dans|en|sur)|les? plus \w+ (?:de|du|des|d) )")

_FAIT_TETE_RE = re.compile(
    r"^(qui|quand|combien|quel|quelle|quels|quelles|c est quoi|qu est[- ]?ce que|"
    r"comment s appelle|dans quel|sur quel|a quelle)\b"
    r"|^ou\b(?! (?:bien|alors))"
    r"|\b(quand|comment|pourquoi|combien)[\s?.!]*$")          # interrogatif POSTPOSÉ (« il est mort quand ? »)


def _detecte(nq: str, brut: str, relation: str | None = None) -> list:
    """Détecteurs EXPLICITES (le cœur). Renvoie [(acte, confiance, indice)] — PLUSIEURS entrées si plusieurs
    lectures tiennent (G2 : jamais un sens choisi en silence quand l'ambiguïté est réelle). `relation` = la
    tête « R de E » DÉJÀ filtrée des mots-outils par `_relation_entites` (jamais le motif brut)."""
    out = []
    toks = [w for w in (t.strip(",.!?;:") for t in nq.split()) if w]
    # SOCIAL : message ENTIÈREMENT dans le vocabulaire de politesse (même règle que repond._politesse).
    if toks and len(toks) <= 6 and all(w in _POLI_VOCAB for w in toks):
        out.append((SOCIAL, 0.95, "vocabulaire de politesse pur"))
    if _META_RE.search(nq):
        out.append((META, 0.9, "marqueur méta (sur moi / sur l'échange)"))
    # CALCULER : le SEUL chemin TRANCHÉ interne — le juge AST évalue vraiment (statut décidé dans acte()).
    if _CB._RX_DECL_CALC.search(nq) or _CB._RX_EXPR_BINAIRE.search(nq):
        out.append((CALCULER, 0.9, "déclencheur/expression de calcul"))
    if _METEO_RE.search(nq) or _HEURE_RE.search(nq) or _DATE_RE.search(nq) or _SITE_RE.search(brut):
        out.append((QUOTIDIEN, 0.9, "météo/heure/date/site nommé"))
    if _AGIR_RE.search(nq) and not _SITE_RE.search(brut):     # « regarde X.fr » = QUOTIDIEN/site, pas AGIR
        out.append((AGIR, 0.8, "verbe d'ordre outillé en tête"))
    if _CREER_RE.search(nq):
        out.append((CREER, 0.8, "demande créative (invention/brainstorm)"))
    if _ETAT_RE.search(nq):
        out.append((EXPRIMER_ETAT, 0.85, "expression d'état à la 1re personne"))
    if _AVIS_RE.search(nq):
        out.append((DEMANDER_AVIS, 0.85, "marqueur d'avis/jugement"))
    if _RAISONNER_RE.search(nq):
        out.append((RAISONNER, 0.7, "marqueur de comparaison/déduction"))
    if _CB._RX_BORNE_POS.search(nq):
        out.append((INTERROGER_FAIT, 0.75, "prédicat borné positif (classifieur_bornage)"))
    elif _FAIT_TETE_RE.search(nq) or relation is not None:
        out.append((INTERROGER_FAIT, 0.6, "tête interrogative / forme « R de E »"))
    return out


# ═══════════════ PÉRIPHÉRIE gzip-kNN (U13) : proposition par distance de compression, JAMAIS affirmée ═══════════════
# Exemples FERMÉS et versionnés par acte (pas un entraînement : une carte). Le proposeur ne parle que si le
# voisinage est NET (vote majoritaire + distance sous seuil) — sinon INCONNU honnête.
_EXEMPLES = (
    (INTERROGER_FAIT, "quelle est la capitale de la france"),
    (INTERROGER_FAIT, "qui a ecrit les miserables"),
    (INTERROGER_FAIT, "population du japon"),
    (INTERROGER_FAIT, "en quelle annee a eu lieu la revolution francaise"),
    (INTERROGER_FAIT, "tu connais la hauteur de la tour eiffel"),
    (CALCULER, "combien font 12 fois 7"),
    (CALCULER, "calcule 3 plus 4"),
    (CALCULER, "ca fait combien 100 divise par 4"),
    (RAISONNER, "quelle est la difference entre un fleuve et une riviere"),
    (RAISONNER, "lequel est le plus grand entre le nil et l amazone"),
    (RAISONNER, "est ce qu un chat est un mammifere"),
    (DEMANDER_AVIS, "que penses tu des voitures electriques"),
    (DEMANDER_AVIS, "c est quoi le mieux entre la mer et la montagne"),
    (DEMANDER_AVIS, "tu me conseilles quoi comme livre"),
    (CREER, "aide moi a inventer un objet pour la cuisine"),
    (CREER, "j aimerais creer un truc nouveau"),
    (META, "dis moi ce que tu sais faire"),
    (META, "je n ai pas compris ta reponse"),
    (SOCIAL, "bonjour comment vas tu"),
    (SOCIAL, "merci beaucoup bonne journee"),
    (EXPRIMER_ETAT, "je suis un peu perdu la"),
    (EXPRIMER_ETAT, "ca me stresse tout ca"),
    (QUOTIDIEN, "il fait quel temps aujourd hui"),
    (QUOTIDIEN, "quelle heure il est"),
    (AGIR, "traduis bonjour en espagnol"),
    (AGIR, "oublie tout ce que je t ai dit"),
)
_SEUIL_NCD = 0.60      # distance MOYENNE max du vainqueur ; au-delà -> INCONNU honnête (calibré par le banc)


def _ncd(a: str, b: str) -> float:
    """Normalized Compression Distance (zlib) — 0 = quasi identiques, ~1 = rien de commun."""
    ca = len(zlib.compress(a.encode(), 9))
    cb = len(zlib.compress(b.encode(), 9))
    cab = len(zlib.compress((a + " " + b).encode(), 9))
    return (cab - min(ca, cb)) / float(max(ca, cb))


# Longueurs COMPRESSÉES des exemples, calculées UNE fois à l'import (les exemples sont figés) : divise le coût
# du proposeur par ~2 (26 compressions économisées par appel — mesuré 0,98 ms -> ~0,5 ms, chemin INCONNU).
_EXEMPLES_C = tuple((a, ex, len(zlib.compress(ex.encode(), 9))) for a, ex in _EXEMPLES)


def _propose_gzip(nq: str, k: int = 3):
    """Propose (acte, confiance, indice) par plus proches voisins de compression, ou None si le voisinage
    n'est pas net. PÉRIPHÉRIE : la proposition n'est jamais affirmée — elle nourrit le repli honnête qui
    demande à l'humain de confirmer/corriger (propose -> vérifie)."""
    if len(nq) < 8:
        return None
    bq = nq.encode()
    cq = len(zlib.compress(bq, 9))
    voisins = []
    for a, ex, cx in _EXEMPLES_C:
        cab = len(zlib.compress((nq + " " + ex).encode(), 9))
        voisins.append(((cab - min(cq, cx)) / float(max(cq, cx)), a))
    voisins = sorted(voisins)[:k]
    votes: dict = {}
    for _d, a in voisins:
        votes[a] = votes.get(a, 0) + 1
    acte_gagnant, n = max(votes.items(), key=lambda kv: kv[1])
    if n < 2:                                                 # pas de majorité -> pas de proposition
        return None
    d_moy = sum(d for d, a in voisins if a == acte_gagnant) / n
    if d_moy > _SEUIL_NCD:                                    # voisinage trop lointain -> pas de proposition
        return None
    confiance = round(min(0.45, max(0.15, (1.0 - d_moy) * 0.6)), 3)   # bornée : jamais une certitude
    return acte_gagnant, confiance, "voisinage de compression gzip-kNN (%d/%d voisins, NCD %.2f)" % (n, k, d_moy)


# ═══════════════ acte() — l'entrée unique : signal -> Faisceau ═══════════════
# Cache BORNÉ des candidats par (signal, anaphore) : acte() tourne jusqu'à 2× par message (routage de la
# cascade + repli) — les Candidats sont immuables (frozen), le partage est sûr. Vidé quand plein (simple, sans
# horloge — cristallisation §15 : un calcul stable se replie dans la structure et cesse de coûter).
_CACHE_ACTE: dict = {}
_CACHE_ACTE_MAX = 256


def acte(signal: str, contexte: dict | None = None) -> Faisceau:
    """Classe l'intention du `signal` parmi les 11 actes fermés (§8), extrait entités/relation UNE fois,
    attache le régime du gardien de bornage, et ROUTE chaque candidat vers sa faculté (recette). Ne collapse
    jamais une ambiguïté réelle (G2) et n'affirme jamais sans juge (G1/G7)."""
    ctx = dict(contexte or {})
    brut = (signal or "").strip()
    if not brut:
        return Faisceau((), ctx)
    cle = (brut, str(ctx.get("anaphore") or ""))
    en_cache = _CACHE_ACTE.get(cle)
    if en_cache is not None:
        return Faisceau(en_cache, ctx)
    nq = _norm(brut)
    try:
        regime = _CB.classe(brut).statut_ontologique
    except ValueError:
        regime = ""
    relation, entites = _relation_entites(nq, ctx)
    cands = []
    for act, conf, indice in _detecte(nq, brut, relation):
        statut, reponse, ancrage = NON_TRANCHE, "faculté : %s" % FACULTES[act][0], "non ancré"
        if act == CALCULER:
            val = _CB._juge_arith(nq)                         # le SEUL juge interne : il ÉVALUE vraiment
            if val is not None:
                if isinstance(val, float) and val.is_integer():
                    val = int(val)
                statut, reponse, ancrage = TRANCHE, str(val), "calcul arithmétique (AST évalué, couvrant)"
        cands.append(Candidat(intention=act, entites=entites, relation=relation, regime=regime,
                              statut=statut, reponse=reponse, ancrage=ancrage,
                              signal_discriminant=indice, confiance=conf,
                              provenance="détecteur explicite (cœur) : %s" % indice))
    if not cands:                                             # périphérie : PROPOSER, jamais affirmer
        prop = _propose_gzip(nq)
        if prop is not None:
            act, conf, indice = prop
            cands.append(Candidat(intention=act, entites=entites, relation=relation, regime=regime,
                                  reponse="faculté : %s" % FACULTES[act][0],
                                  signal_discriminant="confirme ou corrige mon hypothèse d'intention",
                                  confiance=conf, provenance="proposition périphérie : %s" % indice))
        else:
            cands.append(Candidat(intention=INCONNU, entites=entites, relation=relation, regime=regime,
                                  statut=STATUT_INCONNU, reponse="faculté : %s" % FACULTES[INCONNU][0],
                                  signal_discriminant="reformulation ou choix d'une famille d'actes",
                                  confiance=0.0, provenance="aucun détecteur, voisinage gzip trop lointain"))
    cands.sort(key=lambda c: -c.confiance)
    if len(_CACHE_ACTE) >= _CACHE_ACTE_MAX:
        _CACHE_ACTE.clear()
    _CACHE_ACTE[cle] = tuple(cands)
    return Faisceau(tuple(cands), ctx)


# ═══════════════ LE COMPOSITEUR DE SORTIE (§10) — le « coup calculé », JAMAIS un choix silencieux ═══════════════
# Têtes de mesure AMBIGUËS (carte FERMÉE, Phase 2) : un mot qui recouvre PLUSIEURS relations vérifiées distinctes.
# Vécu 2026-07-07 : « la taille de la France » était collapsée en silence sur superficie (_SYN_TETE codé en dur)
# et « la taille de la tour Eiffel » échouait alors que la hauteur (330 m) est en base. Le compositeur tient les
# lectures EN PARALLÈLE : chaque branche est résolue par les caps vérifiés existants, puis composée (§10.1).
RELATIONS_AMBIGUES = {
    "taille": ("hauteur", "superficie", "population"),
    "grandeur": ("hauteur", "superficie", "population"),
    "dimension": ("hauteur", "longueur", "superficie"),
}


def compose(faisceau: Faisceau, terme: str | None = None) -> str | None:
    """Compose la sortie d'un faisceau dont les candidats ont été RÉSOLUS par l'appelant (réponse remplie +
    statut TRANCHE pour les branches vérifiées). Le coup est CALCULÉ sur la forme du faisceau (§10.2), les
    couches sont piochées ENSEMBLE (§10.1 : le certain + les suppositions typées + l'invitation — une porte,
    jamais un mur). FAUX=0 : seules les branches TRANCHÉES (juge/lookup réel) sont servies comme faits ; les
    lectures non résolues ne sont mentionnées QUE comme lectures. None si aucune branche n'est servie
    (l'appelant garde sa cascade)."""
    servis = [c for c in faisceau.candidats if c.statut == TRANCHE and c.reponse]
    if not servis:
        return None
    quoi = ("« %s »" % terme) if terme else "ta demande"
    autres = [c.relation for c in faisceau.candidats if (c.statut != TRANCHE or not c.reponse) and c.relation]
    # ── CONVERGENCE (ou lecture unique servable) : mener avec le tronc commun, en SIGNALANT les lectures ──
    if len({c.reponse for c in servis}) == 1:
        rep = servis[0].reponse
        lectures_ok = [c.relation or _INTITULES.get(c.intention, c.intention) for c in servis]
        if len(servis) > 1:                                   # plusieurs lectures, MÊME réponse : le dire
            return ("%s  (NB : %s pouvait se lire %s — toutes les lectures concordent ici.)"
                    % (rep, quoi, " ou ".join(lectures_ok)))
        if autres:                                            # une seule lecture ancrée : signaler les autres
            return ("%s  (NB : %s peut aussi vouloir dire %s — je n'ai que la lecture « %s » vérifiée pour "
                    "cette entité ; dis-moi si tu voulais autre chose.)"
                    % (rep, quoi, " ou ".join(autres), lectures_ok[0]))
        return rep
    # ── TROP DE BRANCHES : lister les lectures et laisser choisir (§10.2, dernier cas) ──
    if len(servis) > 4:
        noms = ", ".join(c.relation or c.intention for c in servis)
        return ("%s peut vouloir dire trop de choses pour tout servir d'un coup (%s). "
                "Dis-moi la lecture que tu veux et je réponds avec le fait vérifié." % (quoi, noms))
    # ── DIVERGENCE : répondre TOUTES les branches conditionnellement + invitation (le certain de chaque
    #    lecture est servi ; l'interprétation reste typée comme lecture, jamais collapsée) ──
    lignes = ["%s peut vouloir dire plusieurs choses — voici le vérifié pour chaque lecture :" % quoi]
    for c in servis:
        lignes.append("· %s" % c.reponse)
    invite = "Précise la lecture voulue si tu n'en veux qu'une"
    if autres:
        invite += " (« %s » : pas de fait vérifié pour cette entité)" % " », « ".join(autres)
    lignes.append(invite + ".")
    return "\n".join(lignes)


# ═══════════════ Le REPLI HONNÊTE (§10.4, garde G6) — la brique qui tue le « il comprend rien » ═══════════════
_PFX_REPLI = "Voici ce que j'ai compris"


def repli(signal: str, faisceau: Faisceau | None = None) -> str:
    """« Voici ce que j'ai compris de ton intention + ce que je sais faire. » JAMAIS de garbage : ni fausse
    correction orthographique, ni recherche web du texte littéral. L'hypothèse est TYPÉE hypothèse (G7) et
    l'humain corrige (boucle de rétroaction). Renvoie TOUJOURS une vraie question (porte, pas mur — §10.1)."""
    f = faisceau if faisceau is not None else acte(signal)
    m = f.meilleur()
    if m is not None and m.intention != INCONNU:
        sujet = ""
        ents = [e for e in m.entites if e]
        if ents:
            sujet = ", à propos de « %s »" % " » et « ".join(ents[:2])
        certitude = "" if m.confiance >= 0.6 else " — hypothèse peu sûre, corrige-moi"
        deux = ""
        if len(f.candidats) >= 2 and f.candidats[1].intention != m.intention:
            deux = " (autre lecture possible : %s)" % _INTITULES[f.candidats[1].intention]
        return ("%s de ta demande (hypothèse, pas une certitude) : %s%s%s%s. "
                "Ce que je sais faire pour ça : %s. Peux-tu préciser ou me corriger ?"
                % (_PFX_REPLI, _INTITULES[m.intention], sujet, deux, certitude, FACULTES[m.intention][1]))
    return ("%s : honnêtement, pas assez pour agir — ta demande ne rentre nettement dans aucun de mes actes. "
            "Voici ce que je sais faire : un fait vérifié (« capitale de l'Espagne »), un calcul exact "
            "(« combien font 12*7 ? »), une comparaison raisonnée (« quelle différence entre X et Y ? »), "
            "un avis par critères, la météo et l'heure, lire un site nommé, traduire. "
            "Peux-tu préciser ta demande dans une de ces familles ?" % _PFX_REPLI)


# ═══════════════ REGISTRE DU ROUTAGE (§16 « registre de ses modes d'échec » · substrat du bandit §11) ═══════════════
# Quand repond.py route la cascade par acte (Phase 5), chaque décision RÉELLEMENT tranchée par un cap est
# journalisée : famille servie (hit) ou cap HORS-famille (miss = la classification/la carte s'est trompée —
# c'est la SURPRISE dont on apprend, §9). Ce journal est le signal de récompense du futur séquenceur appris
# (Phase 4) : une politique ne se construit que sur des erreurs MESURÉES, jamais sur l'intuition.
def _chemin_routage() -> str:
    p = os.environ.get("TRONC_ROUTAGE_PATH")
    if p:
        return p
    base = os.environ.get("VERAX_HOME") or os.path.join(os.path.expanduser("~"), ".verax")
    try:
        os.makedirs(base, exist_ok=True)
    except OSError:
        pass
    return os.path.join(base, "tronc_routage.jsonl")


def note_routage(acte_nom: str, cap: str, dans_famille: bool, position: int = -1) -> None:
    """Journalise une décision de routage tranchée (append-only, dégradation silencieuse : le journal est un
    BONUS d'apprentissage, jamais un point de panne de la réponse). `position` = index (0-based) du cap gagnant
    dans l'ordre RÉELLEMENT servi = le COÛT de calcul de la décision (nb de caps essayés avant le hit) = le
    terme « − coût » de l'utilité §12, mesuré POST-HOC (anti-Goodhart). -1 si non fourni (compat)."""
    try:
        with open(_chemin_routage(), "a", encoding="utf-8") as f:
            f.write(json.dumps({"date": time.strftime("%Y-%m-%d"), "acte": acte_nom, "cap": cap,
                                "famille": bool(dans_famille), "pos": int(position)}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def stats_routage() -> tuple:
    """(total, hors_famille, profondeur_moyenne) des décisions journalisées — pour le diagnostic (mesuré, jamais
    déclaré). profondeur_moyenne = coût de calcul moyen (nb de caps essayés avant le hit) = le « − coût » de
    l'utilité §12 rendu OBSERVABLE ; 0.0 si aucune position enregistrée."""
    total = hors = 0
    somme_pos = n_pos = 0
    try:
        with open(_chemin_routage(), encoding="utf-8") as f:
            for ligne in f:
                try:
                    o = json.loads(ligne)
                except ValueError:
                    continue
                total += 1
                if not o.get("famille"):
                    hors += 1
                p = o.get("pos", -1)
                if isinstance(p, int) and p >= 0:
                    somme_pos += p
                    n_pos += 1
    except OSError:
        return (0, 0, 0.0)
    return (total, hors, (somme_pos / n_pos) if n_pos else 0.0)


# ═══════════════ ATTUNEMENT (§13) — lire l'état comme VARIABLE, jamais le feindre ═══════════════
_PFX_ATTUNEMENT = "Il se peut que"


def attunement(signal: str, faisceau: Faisceau | None = None) -> str | None:
    """Acte EXPRIMER_ÉTAT -> réponse d'attunement : l'état est une SUPPOSITION (« il se peut que tu… »),
    jamais « je ressens » (anti-anthropomorphisme, §13). Offre une prise CONCRÈTE (amplification, pas
    consolation creuse). None si le signal n'exprime pas d'état (l'appelant garde son chemin)."""
    f = faisceau if faisceau is not None else acte(signal)
    m = f.meilleur()
    if m is None or m.intention != EXPRIMER_ETAT or m.confiance < 0.8:
        return None
    return ("%s tu te sentes comme tu le dis — je ne le ressens pas moi-même, je te lis (et je ne juge pas). "
            "Dis-moi le point PRÉCIS qui bloque et je t'aide dessus — un fait à vérifier, un calcul, "
            "une comparaison." % _PFX_ATTUNEMENT)
