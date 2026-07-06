"""
CLASSIFIEUR DE BORNAGE — le ROUTEUR DE STATUT du contrat d'atome, gardien anti-hallucination (2026-07-02).

VISION (Yohan) : « il est extrêmement important de définir CHIRURGICALEMENT ce qui est borné ou non sur toutes les
connaissances, afin que la réalité puisse trancher sur les sujets bornés et éviter les hallucinations ». Ce module
décide, pour une question/atome, quel RÉGIME du contrat d'atome (`atome.py`) s'applique — donc si la réalité a le
droit de trancher (fait) ou non (supposition).

DEUX AXES (les séparer résout le maillon méta) :
  • ONTOLOGIQUE : la réalité fixe-t-elle la réponse, indépendamment de qui la pose ? -> BORNÉ / NON_BORNÉ / INDÉCIDABLE.
  • ACCÈS : un juge réel peut-il trancher MAINTENANT ? -> JUGE_DISPO / PAS_DE_JUGE.
Routage -> régime atome :
  (BORNÉ, JUGE_DISPO)  -> FAIT (la réalité tranche via le juge)          [le SEUL chemin qui affirme]
  (BORNÉ, PAS_DE_JUGE) -> SUPPOSITION « une vérité existe, non vérifiée » -> à chercher (veille/web)
  (NON_BORNÉ, ·)       -> SUPPOSITION calibrée (opinion/jugement : pas de vérité à trancher)
  (INDÉCIDABLE, ·)     -> non-borné conservateur (au doute sur le STATUT, jamais borné)

FAUX=0 — ce module est SOUND PAR CONSTRUCTION : il ne PRODUIT jamais de réponse affirmée, il ROUTE. Le seul chemin
qui autorise un fait est (BORNÉ, JUGE_DISPO), et JUGE_DISPO n'est vrai QUE si un vrai juge (verdict passé par
l'appelant, ou un calcul interne vérifié) a réellement tranché — jamais déduit de marqueurs lexicaux. Donc une erreur
de classification dégrade au pire le CADRAGE (chercher vs opinion), jamais la véracité. Biais CONSERVATEUR : au moindre
doute sur le statut -> non-borné. Les marqueurs sont regroupés par TYPE DE PRÉDICAT (pas une liste de mots-clés brute).
Souverain, stdlib pur.
"""
from __future__ import annotations

import ast
import dataclasses
import operator
import re
import unicodedata

# ── statut ontologique ──
BORNE = "borne"
NON_BORNE = "non_borne"
INDECIDABLE = "indecidable"

# ── accès ──
JUGE_DISPO = "juge_dispo"
PAS_DE_JUGE = "pas_de_juge"

# ── régime atome résultant ──
R_FAIT = "fait"                         # borné + juge -> affirmable
R_SUPPOSITION_A_CHERCHER = "supposition_a_chercher"   # borné sans juge -> vérité existe, chercher
R_SUPPOSITION_OPINION = "supposition_opinion"          # non-borné -> jugement calibré


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode().lower()
    return " ".join(t.split())


# PRÉDICATS NON-BORNÉS (la réalité NE fixe PAS : jugement, goût, prescription, spéculation, fiction).
# Regroupés par TYPE de prédicat. DUR = préempte (sauf juge réel) ; SOUPLE = simple indice.
_NB_DUR = {
    "evaluation_subjective": r"\b(le meilleur|la meilleure|le pire|la pire|le mieux|vit-on le mieux|on vit le mieux|"
                             r"plus beau|plus belle|plus joli|le plus beau|plus sympa|plus agreable|le plus interessant|"
                             # notoriété = pas de mesure unique (streams ? ventes ? sondages ?) et « du moment » fluctue
                             r"plus connue?s?|plus populaires?|plus celebres?|plus stylee?s?|"
                             # recommandation évaluative au conditionnel (« quelle boisson serait vraiment
                             # rafraichissante ») : pas de mesure unique -> supposition cadrée, jamais une quête web
                             r"serait (vraiment |bien )?(rafraichissant|agreable|sympa|ideal|parfait)e?s?|"
                             r"nombre parfait|le plus parfait|le vrai (bonheur|sens))\b",
    "gout_preference": r"\b(preferes?-tu|ton gout|tes gouts|aimes?-tu le plus|quel est ton prefere|"
                       r"quelle est ta prefere)\b",
    "esthetique": r"\b(est-ce (que c'est |)beau|est-ce joli|trouves-tu (ca |cela |)beau)\b",
    "prescription_morale": r"\b(devrait-on|faut-il (moralement|)|est-ce (bien|mal|juste|moral) de|"
                           r"a-t-on le droit moral)\b",
    # NB : la mention d'une ANNÉE n'est plus dans ce motif — une année PASSÉE (« qui a gagné … en 2018 ») est un
    # fait borné, pas une prédiction. Le cas « année FUTURE » est traité dynamiquement par _annee_future() dans
    # classe() (faille confirmée par la passe adverse assistant_nl 2026-07-03 : « en 2[0-9]{3} » sur-classait
    # TOUTE année 2000-2999 en non-borné et court-circuitait la recherche du fait).
    "prediction_future_incertaine": r"\b(que va-t-il se passer|qui va gagner|quel sera l'avenir|"
                                     r"dans (10|20|50|cent) ans|va-t-il (arriver|se produire))\b",
    "fiction_hypothetique": r"\b(invente une histoire|imagine (que|un)|et si (le|la|les|on|nous)|"
                            r"raconte-moi une histoire|ecris (un poeme|une fiction|un roman))\b",
    "opinion_demandee": r"\b(a ton avis|selon toi|penses-tu que|qu'en penses-tu|ton opinion)\b",
}
# PRÉDICATS BORNÉS POSITIFS (la réalité fixe : quantité mesurable, date/lieu factuel, identité, définition, calcul).
_BORNE_POS = {
    "quantite_mesurable": r"\b(combien (de|d')|quelle est la (population|altitude|hauteur|masse|distance|superficie|"
                          r"vitesse|temperature|longueur|profondeur|largeur|densite)|quel est le (poids|diametre|volume|nombre))\b",
    "date_factuelle": r"\b(en quelle annee|quelle est la date|quand (a|est|a-t-il|a-t-elle|ont|furent|fut)|"
                      r"date de (naissance|deces|creation|fondation))\b",
    "lieu_geo": r"\b(quelle est la capitale|dans quel pays|ou (se trouve|est situe|se situe)|quel est le pays de)\b",
    "identite_fait": r"\b(qui a (invente|ecrit|decouvert|compose|peint|realise|fonde|gagne|remporte)|"
                     r"quel est l'auteur|quel est le createur)\b",
    "definition_convention": r"\b(qu'est-ce qu[e']|que signifie|definition de|que veut dire|quelle est la formule)\b",
    # MÉCANISME/EXPLICATION : « comment fonctionne une pompe à chaleur », « explique-moi le rôle des
    # mitochondries », « expose-moi les tenants de la photosynthèse » — une VÉRITÉ existe (le mécanisme est
    # documenté). Classé BORNÉ -> la recherche attribuée (« d'après Wikipédia… », gate de pertinence) peut
    # servir un RAPPORT sourcé au lieu d'une clarification en boucle. Jamais généré : rapporté ou rien.
    "mecanisme_explication": r"\b(comment (fonctionne|marche)|explique[- ]?(moi|nous)? (le|la|les|l')|"
                             r"quel(le)? est le (role|fonctionnement|mecanisme) (de|des|du|d')|"
                             r"les tenants (de la|du|des|de l')|decri(s|vez)([- ]moi)? (le|la|les|l')|"
                             r"comprendre (comment|en quoi|pourquoi)|en quoi .{3,60} a (bouleverse|change|transforme)|"
                             r"quelles? (furent|sont|ont ete) les consequences)\b",
}
_RX_NB_DUR = re.compile("|".join(_NB_DUR.values()))
_RX_BORNE_POS = re.compile("|".join(_BORNE_POS.values()))

# Année FUTURE mentionnée (« en 2050 », « d'ici 2100 ») -> prédiction incertaine. DYNAMIQUE : comparée à l'année
# COURANTE (une année passée est un fait borné). Import time au niveau module (stdlib, coût nul).
_RX_ANNEE = re.compile(r"\b(?:en|d ici|d'ici|pour|vers|avant|apres)\s+(2[0-9]{3})\b")


def _annee_future(q: str) -> bool:
    """True si la question mentionne une année STRICTEMENT future (prédiction), False sinon (année passée ou
    courante = factuel datable). Le futur ne peut pas être un fait -> non-borné conservateur."""
    import time
    an_courant = time.localtime().tm_year
    return any(int(a) > an_courant for a in _RX_ANNEE.findall(q))

# ── JUGE ARITHMÉTIQUE INTERNE : un VRAI juge (il ÉVALUE), pas un marqueur lexical. ──
# Leçon de la passe adversariale : matcher le VERBE « calculer » ou une plage « 1990-2000 » comme un calcul route
# une opinion/prédiction vers un fait affirmé = hallucination. Un juge n'accorde JUGE_DISPO que s'il évalue vraiment.
_AR_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
           ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow,
           ast.USub: operator.neg, ast.UAdd: operator.pos}
_RX_DECL_CALC = re.compile(r"\b(combien font|combien vaut|combien valent|resultat de|calcule[rz]?)\b")
_RX_EXPR_BINAIRE = re.compile(r"\d[\d\s.]*(?:[-+*/]\s*\d[\d\s.]*)+")


def _eval_noeud(n):
    if isinstance(n, ast.Expression):
        return _eval_noeud(n.body)
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
        return n.value
    if isinstance(n, ast.BinOp) and type(n.op) in _AR_OPS:
        return _AR_OPS[type(n.op)](_eval_noeud(n.left), _eval_noeud(n.right))
    if isinstance(n, ast.UnaryOp) and type(n.op) in _AR_OPS:
        return _AR_OPS[type(n.op)](_eval_noeud(n.operand))
    raise ValueError("expression non arithmétique")


# Opérations dites EN TOUTES LETTRES : si l'une apparaît, l'expression symbolique extraite ne couvre PAS toute la
# demande (« 2 + 2 fois 3 » -> extraire « 2 + 2 » et répondre 4 serait un FAUX servi comme fait). On refuse le juge.
_RX_OP_VERBALE = re.compile(r"\b(fois|divis\w+|multipli\w+|puissance|au carre|au cube|racine|modulo)\b")


def _juge_arith(q: str):
    """Retourne la VALEUR si la question est une vraie demande de calcul EFFECTIVEMENT ÉVALUÉE, sinon None (= pas de
    juge). Conditions cumulées : (a) une sous-expression binaire entre nombres qui s'évalue par l'AST sûr, ET (b) un
    déclencheur de calcul explicite (« combien font/calcule/résultat de ») OU la question EST une expression pure,
    ET (c) l'expression extraite COUVRE TOUT le contenu numérique de la question (aucun chiffre orphelin, aucune
    opération en toutes lettres) — sinon on évaluerait un FRAGMENT et on servirait un résultat FAUX comme fait
    (failles « 2,5 + 2,5 » / « 2*3**4 » / « 2 + 2 fois 3 » de la passe adverse assistant_nl 2026-07-03).
    Ni le verbe « calculer » seul, ni une plage « 1990-2000 » dans une phrase, n'accordent le juge."""
    q = re.sub(r"(?<=\d),(?=\d)", ".", q)            # virgule décimale française -> point (AVANT le match)
    m = _RX_EXPR_BINAIRE.search(q)
    if m is None:
        return None
    if _RX_OP_VERBALE.search(q):                     # opération en toutes lettres : l'extraction serait partielle
        return None
    if re.search(r"\d", q[:m.start()] + q[m.end():]):   # chiffre HORS de l'expression extraite -> fragment -> refus
        return None
    expr = m.group(0).strip()
    try:
        val = _eval_noeud(ast.parse(expr, mode="eval"))
    except Exception:
        return None
    if isinstance(val, float):                       # artefact binaire (0.1+0.2 -> 0.30000000000000004) : arrondi
        val = round(val, 12)                         # de RESTITUTION sûr (12 déc.), jamais un arrondi de calcul
    pure = re.fullmatch(r"[\s0-9.+\-*/()=?]+", q) is not None      # la question EST une expression
    if _RX_DECL_CALC.search(q) or pure:
        return val
    return None


@dataclasses.dataclass(frozen=True)
class Classement:
    statut_ontologique: str
    acces: str
    regime: str
    justification: str

    def route_fait(self) -> bool:
        """True SEULEMENT si la réalité peut trancher maintenant (borné + juge)."""
        return self.statut_ontologique == BORNE and self.acces == JUGE_DISPO


def _quel_predicat(rx_map, q):
    for nom, motif in rx_map.items():
        if re.search(motif, q):
            return nom
    return None


def classe(question: str, *, juge_verdict: bool = None, juge_nom: str = "") -> Classement:
    """Classe une question. `juge_verdict` (optionnel) = résultat d'un VRAI juge déjà exécuté par l'appelant
    (capacites/corpus/test) : s'il est fourni, il PRIME (une question tranchée par la réalité est bornée-accessible,
    même si son libellé contient un marqueur ambigu comme « meilleur coup aux échecs »). Sinon, analyse ontologique
    conservatrice. Ne produit JAMAIS de réponse — seulement un routage."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question non vide requise")
    q = _norm(question)

    # 1) JUGE RÉEL EXTERNE fourni et positif -> borné + accessible (le résultat prime le mot, ex. « meilleur coup »+minimax).
    if juge_verdict is True:
        return Classement(BORNE, JUGE_DISPO, R_FAIT,
                          f"un juge réel a tranché ({juge_nom or 'juge fourni'}) -> la réalité fixe la réponse")

    # 2) prédicat NON-BORNÉ dur -> non-borné : PRÉEMPTE le juge interne (biais conservateur). Une opinion/prédiction/
    #    fiction ne devient jamais un fait à cause d'un chiffre ou du verbe « calculer » qu'elle contiendrait.
    nb = _quel_predicat(_NB_DUR, q)
    if nb is not None:
        return Classement(NON_BORNE, PAS_DE_JUGE, R_SUPPOSITION_OPINION,
                          f"prédicat non-borné ({nb}) : la réalité ne fixe pas -> supposition calibrée")
    if _annee_future(q):
        return Classement(NON_BORNE, PAS_DE_JUGE, R_SUPPOSITION_OPINION,
                          "prédicat non-borné (prediction_future_incertaine) : année future mentionnée -> "
                          "le futur n'est pas un fait, supposition calibrée")

    # 3) JUGE INTERNE : calcul arithmétique EFFECTIVEMENT ÉVALUÉ (vrai juge, pas un marqueur). Sinon on n'affirme rien.
    if juge_verdict is None:
        val = _juge_arith(q)
        if val is not None:
            return Classement(BORNE, JUGE_DISPO, R_FAIT, f"calcul arithmétique évalué (juge interne) = {val}")

    # 4) prédicat BORNÉ positif -> une vérité existe, mais pas de juge exécuté ici -> à chercher.
    bp = _quel_predicat(_BORNE_POS, q)
    if bp is not None:
        acces = JUGE_DISPO if juge_verdict is True else PAS_DE_JUGE
        return Classement(BORNE, acces,
                          R_FAIT if acces == JUGE_DISPO else R_SUPPOSITION_A_CHERCHER,
                          f"prédicat borné ({bp}) : la réalité fixe la réponse ; "
                          f"{'juge dispo' if acces == JUGE_DISPO else 'pas de juge ici -> à chercher/vérifier'}")

    # 4) juge fourni négatif : la question était jugeable mais le juge n'a pas validé -> borné sans réponse (HORS).
    if juge_verdict is False:
        return Classement(BORNE, PAS_DE_JUGE, R_SUPPOSITION_A_CHERCHER,
                          "borné mais le juge n'a pas tranché -> vérité existe, non obtenue (chercher/HORS)")

    # 5) aucun signal net -> INDÉCIDABLE-sur-le-statut -> non-borné CONSERVATEUR (jamais borné au doute).
    return Classement(INDECIDABLE, PAS_DE_JUGE, R_SUPPOSITION_OPINION,
                      "statut indécidable (aucun signal net) -> traité comme non-borné (conservateur, anti-hallucination)")


def regime_atome_pour(question: str, **kw) -> str:
    """Raccourci : le régime du contrat d'atome à appliquer (R_FAIT / R_SUPPOSITION_A_CHERCHER / R_SUPPOSITION_OPINION)."""
    return classe(question, **kw).regime
