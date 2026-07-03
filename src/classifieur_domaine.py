"""
CLASSIFIEUR DE NATURE DE DOMAINE — le GAP de [[project-ia-domaines-realite]], le KEYSTONE.

Pour une demande, décide QUELLE contrainte de réalité s'applique -> bascule le bon JUGE, ou
s'abstient honnêtement. Anti-LLM : il ne PRÉDIT pas le mot probable, il VÉRIFIE ce qu'il peut et
REFUSE le reste. C'est un AIGUILLEUR vers un juge, pas un oracle de vérité.

5 natures (cf. taxonomie Yohan) et leur juge :
  1 NÉCESSITÉ  — déductible/calculable. JUGE = exécuteur (resoudre_tout / calcul arithmétique).
  2 PHYSIQUE   — fait du monde observé.   JUGE = base de faits vérifiés (base_faits).
  3 PASSÉ      — fait historique figé.     JUGE = base de faits vérifiés (base_faits).
  4 CONVENTION — langue/définition/unité.  JUGE = base de faits vérifiés (base_faits).
  5 NON-BORNÉ  — opinion/goût/futur/fiction/éthique. PAS de vérité -> ABSTENTION de prétention.
  (INCONNU)    — nature indécidable / fait non couvert -> HORS honnête (jamais de devinette).

GARANTIE DE SOUNDNESS (structurelle, « sûr avant rapide ») : seules les branches NÉCESSITÉ et
faits-vérifiés émettent une valeur, et UNIQUEMENT après qu'un juge l'a confirmée (held-out pour le
code, lookup exact pour les faits, évaluation pour l'arithmétique). Toutes les autres branches
renvoient HORS ou ABSTENTION. Donc une ERREUR DE CLASSIFICATION ne produit JAMAIS un faux : au
pire un « je ne sais pas » de la mauvaise saveur. La nature 2/3/5 est advisory (qualité du message
d'honnêteté), pas une affirmation.
"""
from __future__ import annotations

import ast
import dataclasses
import re

import base_faits
import regle as _regle
import audit_code as _audit
import chimie as _chimie
import genetique as _genetique

# --- Natures ----------------------------------------------------------------
NECESSITE = "necessite"
PHYSIQUE = base_faits.CAT_PHYSIQUE        # "physique"
PASSE = base_faits.CAT_PASSE              # "passe"
CONVENTION = base_faits.CAT_CONVENTION    # "convention"
REGLE = "regle"                           # règle posée (loi/métier/hygiène/procédure/norme) -> moteur regle
AUDIT = "audit_code"                       # code source vs règles de codage/sécurité (CWE) -> moteur audit_code
CHIMIE = "chimie"                          # stœchiométrie bornée (masse molaire…) -> moteur chimie
GENETIQUE = "genetique"                    # génétique moléculaire bornée (complément/traduction) -> moteur genetique
NON_BORNE = "non-borne"
INCONNU = "inconnu"

# --- Statuts du verdict -----------------------------------------------------
VERIFIE = "verifie"        # un juge a confirmé une valeur
HORS = "hors"              # nature reconnue verifiable mais réponse non disponible / non synthétisable
ABSTENTION = "abstention"  # nature SANS vérité unique : on refuse d'affirmer un « vrai »


@dataclasses.dataclass(frozen=True)
class Reponse:
    nature: str
    statut: str
    valeur: str | None = None
    source: str | None = None
    justification: str = ""

    def __str__(self) -> str:
        if self.statut == VERIFIE:
            src = f"  (source : {self.source})" if self.source else ""
            return f"[{self.nature}/VÉRIFIÉ] {self.valeur}{src}"
        if self.statut == ABSTENTION:
            return f"[{self.nature}/ABSTENTION] {self.justification}"
        return f"[{self.nature}/HORS] {self.justification}"


# --- Marqueurs de NON-BORNÉ, en DEUX régimes (raffinement pensée-machine 2026-07-02) --------------------
# DURS — préemption inconditionnelle : le monde interrogé n'est PAS le monde réel présent (futur,
# contrefactuel, création narrative). Une réponse factuelle au présent pourrait être MATÉRIELLEMENT
# FAUSSE pour le monde demandé (« en 2100 », « que se passerait-il si ») ou hors-monde (fiction)
# -> abstention AVANT tout juge (c'est la seule classe où un fait vérifié ne prime pas).
_MARQUEURS_NON_BORNE_DUR = [
    r"\bimagine\b", r"\bracont", r"\becris (?:un poeme|une histoire|une chanson)\b",
    r"\bdans le futur\b", r"\ben 2100\b", r"\bque se passerait il si\b",
]
# SOUPLES — gate sur le RÉSULTAT, pas la catégorie : opinion/goût/déontique/philosophie. Le marqueur
# n'est qu'un INDICE ; si un juge borné VÉRIFIE une réponse (fait exact du monde réel), elle est vraie
# et PRIME l'abstention (« à ton avis, quelle est la capitale de la France ? » -> Paris). Sans réponse
# vérifiée, l'abstention garde sa saveur non-bornée. Corrige la collision « qui a INVENTÉ le téléphone »
# (factuel, était avorté à tort) vs « INVENTE une histoire » (créatif, aucun fait ne vérifie -> abstention) :
# le RÉSULTAT tranche, pas le mot. FAUX=0 intact : seules les branches à juge émettent une valeur.
_MARQUEURS_NON_BORNE_SOUPLE = [
    r"\ba ton avis\b", r"\bselon toi\b", r"\bd apres toi\b", r"\bpenses tu\b", r"\bcrois tu\b",
    r"\bprefere", r"\bprefer", r"\baimes tu\b", r"\btu aimes\b", r"\bque ressens\b",
    r"\ble meilleur\b", r"\bla meilleure\b", r"\ble plus beau\b", r"\ble plus belle\b", r"\bplus jolie?\b",
    r"\bdevrait on\b", r"\bfaut il\b", r"\bdevrais je\b", r"\best il moral\b", r"\best ce bien de\b",
    r"\binvente\b", r"\bsens de la vie\b",
    r"\bquel est ton\b", r"\bquelle est ta\b", r"\bton plat\b", r"\bta couleur\b",
]
_RX_NON_BORNE_DUR = re.compile("|".join(_MARQUEURS_NON_BORNE_DUR))
_RX_NON_BORNE_SOUPLE = re.compile("|".join(_MARQUEURS_NON_BORNE_SOUPLE))

# Marqueurs qu'une question VISE un fait du monde/passé (pour donner la bonne saveur au HORS).
_RX_FACTUEL = re.compile(
    r"\b(capitale|population|superficie|qui a (?:invente|decouvert|ecrit|peint)|en quelle annee|"
    r"quelle annee|quand|combien d habitants|distance|hauteur|altitude|temperature|masse|densite|"
    r"symbole|formule|president|roi|empereur|guerre|bataille|traite)\b"
)

# NÉCESSITÉ calculable. ON NE CALCULE QUE SUR INTENTION EXPLICITE (« combien font », « calcule »,
# « = »…) ou si la requête EST une expression nue. Sinon un « 20-21 » noyé dans une phrase factuelle
# donnerait « -1 » (calcul juste, mais réponse à la mauvaise question = faux de fait). « sûr avant rapide ».
_RX_INTENT_CALC = re.compile(r"\b(combien (?:font|fait|vaut)|calcule|calculer|resultat|egal|vaut|=)\b|=")
_RX_RUN_ARITH = re.compile(r"[0-9.+\-*/%() ]+")
_ARITH_AUTORISE = set("0123456789.+-*/%() ")


def _extrait_arith(texte: str):
    """Plus longue sous-chaîne arithmétique PARSABLE contenant ≥1 opérateur. None sinon."""
    candidats = []
    for m in _RX_RUN_ARITH.finditer(texte):
        s = m.group(0).strip()
        if len(s) > 60 or not re.search(r"\d", s) or not re.search(r"[+\-*/%]", s):
            continue
        candidats.append(s)
    candidats.sort(key=len, reverse=True)
    for s in candidats:
        try:
            ast.parse(s, mode="eval")
            return s
        except SyntaxError:
            continue
    return None


def _calcule_arith(texte: str):
    """Évalue une expression arithmétique si la requête le DEMANDE. Sound : AST restreint (littéraux
    numériques + opérateurs), exécution gardée (longueur + exposant bornés), aucune exécution libre."""
    q = base_faits.normalise(texte)
    expr_nue = texte.strip().rstrip("?.! ")
    intention = bool(_RX_INTENT_CALC.search(q)) or all(c in _ARITH_AUTORISE for c in expr_nue) and expr_nue
    if not intention:
        return None
    expr = _extrait_arith(texte)
    if not expr or len(expr) > 60 or any(c not in _ARITH_AUTORISE for c in expr):
        return None   # borne de longueur = garde anti-DoS (pas de monstre numérique)
    try:
        noeud = ast.parse(expr, mode="eval")
    except SyntaxError:
        return None
    autorises = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.USub, ast.UAdd,
                 ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
    for n in ast.walk(noeud):
        if not isinstance(n, autorises):
            return None
        if isinstance(n, ast.Constant) and not isinstance(n.value, (int, float)):
            return None
        # Garde anti-DoS : un exposant doit être une petite constante (sinon 2**1e9 explose la mémoire).
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow):
            e = n.right
            if not (isinstance(e, ast.Constant) and isinstance(e.value, int) and abs(e.value) <= 64):
                return None
    try:
        val = eval(compile(noeud, "<arith>", "eval"), {"__builtins__": {}}, {})
    except (ArithmeticError, ValueError):
        return None
    return str(int(val) if isinstance(val, float) and val.is_integer() else val)


_RX_MAP = {base_faits.CAT_PHYSIQUE: PHYSIQUE, base_faits.CAT_PASSE: PASSE, base_faits.CAT_CONVENTION: CONVENTION}


def repond(texte: str | None = None, *, point_entree: str | None = None, signature: str | None = None,
           exemples=None, exemples_held=None, budget: int = 2000,
           scope: str | None = None, ident: str | None = None, cas: dict | None = None,
           base=None, date: str | None = None,
           code: str | None = None, langage: str | None = None) -> Reponse:
    """Aiguille la demande vers le bon juge. Voir la garantie de soundness en tête de module."""
    # 0bis) AUDIT DE CODE (dév/sécurité) : code source + langage -> moteur audit_code (règles CWE).
    #   constats trouvés -> VÉRIFIÉ (faits vérifiables) ; aucun motif connu -> ABSTENTION (PAS une preuve
    #   de sécurité, jamais on n'affirme « sûr ») ; langage hors référentiel -> HORS (jamais deviné).
    if code is not None and langage is not None:
        st, constats = _audit.audite(code, langage)
        if st == _audit.HORS:
            return Reponse(AUDIT, HORS, justification="langage hors référentiel d'audit (non deviné)")
        if st == _audit.RAS:
            return Reponse(AUDIT, ABSTENTION,
                           justification="aucun motif de vulnérabilité connu — PAS une preuve de sécurité")
        return Reponse(AUDIT, VERIFIE, valeur=constats, source="référentiel CWE/règles de codage",
                       justification=f"{len(constats)} constat(s) vérifiable(s) : "
                                     + ", ".join(f"{c.cwe} L{c.ligne}" for c in constats))

    # 0) RÈGLE POSÉE (loi/métier/hygiène/procédure/norme) : route STRUCTURÉE sound vers le moteur de
    #    règles. scope+ident = lookup EXACT scopé + daté (règle absente -> HORS, jamais inventée).
    #    cas fourni -> jugement de conformité par PRÉDICAT EXPLICITE ; cas absent -> on rend la LETTRE
    #    (donnée vérifiée, lookup exact). Règle d'interprétation / donnée manquante / non en vigueur
    #    -> ABSTENTION (jamais une fausse conformité). Une erreur ici ne produit donc jamais un faux.
    if scope is not None and ident is not None:
        d = date or _regle.AUJOURDHUI
        r = _regle.cherche_partout(scope, ident, base=base, date=d)
        if r is None:
            return Reponse(REGLE, HORS,
                           justification="règle introuvable dans les référentiels appris (non inventée)")
        if cas is None:
            return Reponse(REGLE, VERIFIE, valeur=r.contenu, source=f"{r.ref} (depuis {r.depuis})",
                           justification="lettre de la règle (lookup exact, scopé + daté)")
        jug = _regle.applique(r, cas, date=d)
        if jug.statut == _regle.ABSTENTION:
            return Reponse(REGLE, ABSTENTION, source=r.ref, justification=jug.justification)
        return Reponse(REGLE, VERIFIE, valeur=jug.statut.upper(), source=r.ref,
                       justification=jug.justification)

    # 1) DEMANDE STRUCTURÉE (signature + exemples) = NÉCESSITÉ : on tente l'exécuteur (held-out exigé).
    if exemples is not None and point_entree and signature:
        from resoudre_tout import resoudre_tout   # import paresseux (cycle + coût de chargement)
        origine, code = resoudre_tout(point_entree, signature, exemples, exemples_held, budget=budget)
        if origine != "HORS" and code:
            return Reponse(NECESSITE, VERIFIE, valeur=code.strip(), source=f"exécuteur ({origine})",
                           justification="solution synthétisée et vérifiée sur le held-out")
        return Reponse(NECESSITE, HORS,
                       justification="tâche calculable mais aucune solution vérifiée n'a été synthétisée")

    if not texte or not texte.strip():
        return Reponse(INCONNU, HORS, justification="demande vide")

    q = base_faits.normalise(texte)

    # 2) NON-BORNÉ DUR d'abord : futur/contrefactuel/fiction -> ABSTENTION avant tout juge (un fait
    #    présent vérifié pourrait être matériellement FAUX pour le monde demandé).
    if _RX_NON_BORNE_DUR.search(q):
        return Reponse(NON_BORNE, ABSTENTION,
                       justification="pas de vérité unique ici (futur/contrefactuel/fiction) : "
                                     "je peux en discuter, je n'affirme pas un « vrai ».")
    # NON-BORNÉ SOUPLE (opinion/goût/déontique) : simple INDICE — les juges bornés passent d'abord ;
    # un fait VÉRIFIÉ prime (gate sur le résultat), sinon l'abstention tombera après les juges (2fin).
    souple = bool(_RX_NON_BORNE_SOUPLE.search(q))

    # 3) FAIT VÉRIFIÉ (cat 2/3/4) : juge = base de faits. Présent -> VÉRIFIÉ ; sinon on continue.
    statut, fait = base_faits.repond_nl(texte)
    if statut == base_faits.VERIFIE:
        return Reponse(_RX_MAP.get(fait.categorie, INCONNU), VERIFIE, valeur=fait.valeur,
                       source=fait.source, justification="lookup dans la base de faits vérifiés")

    # 3bis) CHIMIE bornée : « masse molaire de <FORMULE> ». Extraction VALIDÉE par le parseur (formule
    #       invalide/élément inconnu -> HORS, jamais un faux). Gabarit étroit, sound (pas de NL fuzzy).
    st_c, val_c, formule_c = _chimie.repond_nl(texte)
    if st_c == _chimie.VERIFIE:
        return Reponse(CHIMIE, VERIFIE, valeur=f"{val_c} g/mol", source=_chimie.SOURCE,
                       justification=f"masse molaire de {formule_c} (parse + somme des masses atomiques)")

    # 3ter) GÉNÉTIQUE bornée : « complément ADN de <SEQ> » / « traduis ARN <SEQ> ». Extraction VALIDÉE par le
    #       parseur (séquence invalide -> HORS, pas de NL fuzzy). Gabarit étroit, sound.
    quoi_g, st_g, val_g = _genetique.repond_nl(texte)
    if st_g == _genetique.VERIFIE:
        lib = "complément ADN" if quoi_g == "complement" else "traduction (protéine)"
        return Reponse(GENETIQUE, VERIFIE, valeur=val_g, source=_genetique.SOURCE,
                       justification=f"{lib} (appariement / code génétique standard)")

    # 4) ARITHMÉTIQUE fermée = NÉCESSITÉ calculable (juge = évaluation déterministe).
    val = _calcule_arith(texte)
    if val is not None:
        return Reponse(NECESSITE, VERIFIE, valeur=val, source="évaluation arithmétique",
                       justification="calcul déterministe (nécessité logique)")

    # 5) Question FACTUELLE reconnue mais NON couverte -> HORS honnête à saveur factuelle. Passe AVANT
    #    l'abstention souple : « qui a INVENTÉ le téléphone » (marqueur souple par collision, mais question
    #    factuelle) reçoit « il faudrait étendre la base », pas une fausse saveur d'opinion.
    if _RX_FACTUEL.search(q):
        return Reponse(INCONNU, HORS,
                       justification="question factuelle (monde/passé) hors de ma base de faits vérifiés : "
                                     "je n'invente pas — il faudrait étendre la base.")

    # 2fin) NON-BORNÉ SOUPLE : aucun juge borné n'a vérifié -> l'abstention garde sa saveur non-bornée.
    if souple:
        return Reponse(NON_BORNE, ABSTENTION,
                       justification="pas de vérité unique ici (goût/opinion/éthique) : "
                                     "je peux en discuter, je n'affirme pas un « vrai ».")

    # 6) Indécidable -> HORS honnête.
    return Reponse(INCONNU, HORS,
                   justification="je ne sais pas classer cette demande avec certitude ; je m'abstiens d'affirmer.")


if __name__ == "__main__":
    from garde_ressources import borne
    borne()
    print("=== CLASSIFIEUR DE NATURE DE DOMAINE (aiguille -> juge, ou abstention) ===\n")
    # NL
    for t in ["Quelle est la capitale de la France ?",
              "Quel est le pluriel de cheval ?",
              "En quelle année la révolution française ?",
              "Combien font 17 * 23 + 4 ?",
              "Quel est ton plat préféré ?",
              "Devrait-on coloniser Mars ?",
              "Quelle est la capitale de la Mongolie ?",
              "Qui a peint la Joconde ?"]:
        print(f"  « {t} »\n      {repond(t)}")
    # Structurée (nécessité, vérifiée par l'exécuteur)
    r = repond(point_entree="somme_carres", signature="xs", exemples=[([1, 2, 3], 14), ([2, 3], 13)],
               exemples_held=[([5], 25), ([0, 4], 16)])
    print(f"\n  [structurée somme_carres]\n      {r}")
