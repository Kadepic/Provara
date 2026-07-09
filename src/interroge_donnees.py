# -*- coding: utf-8 -*-
"""INTERROGER DES DONNÉES STRUCTURÉES (CSV/TSV/JSON attachés) — opérations EXACTES, FAUX=0 (2026-07-09, Route 3).

POURQUOI (audit 2026-07-09, item 8 : « fichiers lus mais pas INTERROGEABLES ») : un CSV/JSON importé était
parfaitement parsé (parseur_fichiers 5/5) puis MUET — « quel est le max de la colonne prix ? » → abstention.
Ce module ajoute les OPÉRATIONS déterministes sur le document structuré attaché à la conversation :
  • TABLEAU (csv/tsv) : colonnes, nombre de lignes, max / min / somme / moyenne d'une colonne, comptage
    conditionnel (« combien de lignes ont X »), extraction ciblée d'une cellule (« quel est le prix de X ? »).
  • ARBRE (json) : comptage (éléments au sommet, ou d'une clé-liste), liste des clés, valeur d'une clé.

Approche NLIDB classique (mots-clés d'agrégat → opération, résolution de colonne par le SCHÉMA réel) — pas de
grammaire fragile : on cherche dans la question les NOMS RÉELS de colonnes/clés/valeurs du document.

FAUX=0 — garanties :
  • Chaque réponse porte sa PREUVE : la valeur exacte + où elle vit (ligne du fichier, étiquette de ligne,
    chemin JSON) + ce qui a été compté (« sur N valeurs numériques, M cellules ignorées »).
  • ZÉRO capture indue : hors périmètre (pas de mot-clé d'opération, colonne/clé irrésoluble sans référence
    explicite au fichier) → None, le pipeline normal continue. Jamais de détournement d'une question générale.
  • Unités MÉLANGÉES dans une colonne (« 2 kg » et « 500 g ») → refus honnête de l'agrégat (on ne compare pas
    des grandeurs hétérogènes) ; unité uniforme → calcul + unité affichée.
  • Nombres : virgule = décimale FR (« 12,5 »), point = décimale, « 1 234 »/« 1.234,56 » = milliers ; une
    cellule qui n'est pas un nombre NET est ignorée ET COMPTÉE comme telle dans la réponse. Ambigu → ignoré.
  • Déterministe, souverain, stdlib pur, model-free.
"""
from __future__ import annotations

import json
import re

from base_faits import normalise

# ── nombres : parsing STRICT d'une cellule (unité courte optionnelle) ────────────────────────────────────────
#   groupes : signe, partie entière (avec séparateurs de milliers éventuels), décimales, unité.
_RE_CELL_NUM = re.compile(
    r"^\s*(-?)\s*("
    r"\d{1,3}(?:[   ]\d{3})+"      # milliers à l'espace : 1 234 567
    r"|\d{1,3}(?:\.\d{3})+(?=,)"             # milliers au point SEULEMENT si décimale à la virgule suit : 1.234,56
    r"|\d+"                                   # entier nu
    r")(?:[.,](\d+))?\s*"
    r"([€$£%]|[a-zA-Zµ°][a-zA-Z0-9µ°/²³%€]{0,7})?\s*$")


def _nombre(cellule) -> tuple:
    """(valeur float, unité str) si la cellule est un nombre NET, sinon (None, None). Jamais deviné :
    « 12,5 » → 12.5 ; « 1 234 » → 1234 ; « 45 % » → 45 ; « abc » / « 12-14 » / vide → None."""
    if isinstance(cellule, (int, float)) and not isinstance(cellule, bool):
        return float(cellule), ""
    s = str(cellule or "").strip()
    if not s:
        return None, None
    m = _RE_CELL_NUM.match(s)
    if not m:
        return None, None
    signe, entier, dec, unite = m.groups()
    entier = re.sub(r"[   .]", "", entier)
    try:
        v = float(entier + ("." + dec if dec else ""))
    except ValueError:                        # défensif — le motif garantit déjà la forme
        return None, None
    return (-v if signe else v), (unite or "")


def _fmt(v: float) -> str:
    """Affichage FR exact : entier sans décimales, sinon décimales réelles (virgule), jamais de bruit binaire."""
    if v == int(v) and abs(v) < 1e15:
        return str(int(v))
    return ("%.10f" % v).rstrip("0").rstrip(".").replace(".", ",")


# ── TABLEAU (csv/tsv) ─────────────────────────────────────────────────────────────────────────────────────────
class Tableau:
    """Table interrogeable bâtie sur les lignes BRUTES du parseur csv (list[list[str]]).

    En-tête : la ligne 0 est l'en-tête si aucune de ses cellules non vides n'est un nombre net (convention CSV) ;
    sinon les colonnes s'appellent « colonne 1..N » et TOUTES les lignes sont des données."""

    def __init__(self, lignes, titre: str = ""):
        lignes = [l for l in (lignes or []) if isinstance(l, (list, tuple)) and any(str(c).strip() for c in l)]
        self.titre = titre or "le fichier"
        if lignes and len(lignes) > 1 and not any(_nombre(c)[0] is not None for c in lignes[0] if str(c).strip()):
            self.entete = [str(c).strip() for c in lignes[0]]
            self.donnees = [list(l) for l in lignes[1:]]
            self._decalage = 2                # 1-based + ligne d'en-tête : donnée i → ligne i+2 du fichier
        else:
            larg = max((len(l) for l in lignes), default=0)
            self.entete = ["colonne %d" % (i + 1) for i in range(larg)]
            self.donnees = [list(l) for l in lignes]
            self._decalage = 1
        self.n = len(self.donnees)

    # — résolution de colonne par le SCHÉMA réel (jamais deviné : irrésoluble → None) —
    def resoud_colonne(self, question: str):
        """Index de LA colonne visée par la question, en cherchant les noms RÉELS de colonnes dans le texte
        normalisé (le plus LONG gagne : « prix unitaire » bat « prix »). « colonne 3 » marche aussi. None si
        aucune / ambiguïté réelle."""
        q = " " + normalise(question) + " "
        m = re.search(r"\bcolonne (\d{1,3})\b", q)
        if m and 1 <= int(m.group(1)) <= len(self.entete):
            return int(m.group(1)) - 1
        hits = []
        for i, nom in enumerate(self.entete):
            n = normalise(nom)
            if len(n) >= 2 and (" " + n + " ") in q:
                hits.append((len(n), i))
        if not hits:
            return None
        hits.sort(reverse=True)
        meilleurs = [i for l, i in hits if l == hits[0][0]]
        return meilleurs[0] if len(meilleurs) == 1 else None

    def _numerique(self, idx: int):
        """Valeurs numériques NETTES de la colonne : (liste [(i_donnée, valeur)], nb ignorées, unités vues)."""
        vals, ignorees, unites = [], 0, set()
        for i, ligne in enumerate(self.donnees):
            cell = ligne[idx] if idx < len(ligne) else ""
            v, u = _nombre(cell)
            if v is None:
                if str(cell).strip():
                    ignorees += 1
                continue
            vals.append((i, v))
            unites.add(u)
        return vals, ignorees, unites

    def _etiquette(self, i_donnee: int, idx_colonne: int) -> str:
        """Preuve de LOCALISATION d'une ligne : numéro de ligne réel du fichier + étiquette (1ʳᵉ colonne texte)."""
        loc = "ligne %d du fichier" % (i_donnee + self._decalage)
        ligne = self.donnees[i_donnee]
        if idx_colonne != 0 and ligne and str(ligne[0]).strip() and _nombre(ligne[0])[0] is None:
            loc += ", « %s »" % str(ligne[0]).strip()
        return loc

    def agregat(self, op: str, idx: int):
        """max/min/somme/moyenne EXACTS d'une colonne, avec preuve. Refus honnête si pas de nombres ou unités
        mélangées. Renvoie un texte prêt à afficher."""
        nom = self.entete[idx]
        vals, ignorees, unites = self._numerique(idx)
        if not vals:
            return ("Dans « %s », la colonne « %s » ne contient aucun nombre net — je ne calcule pas de %s "
                    "sur du texte." % (self.titre, nom, op))
        unites.discard("")
        if len(unites) > 1:
            return ("Dans « %s », la colonne « %s » mélange les unités (%s) : je ne compare pas des grandeurs "
                    "hétérogènes sans conversion sûre." % (self.titre, nom, ", ".join(sorted(unites))))
        unite = (" " + unites.pop()) if unites else ""
        note = " (%d cellule(s) non numérique(s) ignorée(s))" % ignorees if ignorees else ""
        if op in ("max", "min"):
            i, v = (max if op == "max" else min)(vals, key=lambda iv: iv[1])
            return ("Dans « %s » : %s de « %s » = %s%s (%s), sur %d valeur(s) numérique(s)%s." %
                    (self.titre, op, nom, _fmt(v), unite, self._etiquette(i, idx), len(vals), note))
        if op == "somme":
            return ("Dans « %s » : somme de « %s » = %s%s, sur %d valeur(s) numérique(s)%s." %
                    (self.titre, nom, _fmt(sum(v for _, v in vals)), unite, len(vals), note))
        if op == "moyenne":
            moy = sum(v for _, v in vals) / len(vals)
            return ("Dans « %s » : moyenne de « %s » = %s%s, sur %d valeur(s) numérique(s)%s." %
                    (self.titre, nom, _fmt(moy), unite, len(vals), note))
        return None

    def _lignes_de_valeur(self, question: str):
        """Lignes dont une cellule TEXTE (non numérique, ≥ 2 caractères) apparaît telle quelle dans la question.
        → [(i_donnée, idx_colonne, cellule)] ; sert au lookup ciblé et au comptage conditionnel."""
        q = " " + normalise(question) + " "
        hits = []
        for i, ligne in enumerate(self.donnees):
            for j, cell in enumerate(ligne):
                c = str(cell).strip()
                n = normalise(c)
                if len(n) >= 2 and _nombre(c)[0] is None and (" " + n + " ") in q:
                    hits.append((len(n), i, j, c))
        if not hits:
            return []
        hits.sort(reverse=True)               # la valeur la plus LONGUE d'abord (« pomme verte » bat « pomme »)
        lmax = hits[0][0]
        return [(i, j, c) for l, i, j, c in hits if l == lmax]

    def cellule(self, question: str):
        """EXTRACTION CIBLÉE : « quel est le prix de la pomme ? » → cellule (colonne résolue × ligne résolue par
        une valeur du tableau présente dans la question). Ambigu → demande de précision honnête. None si hors
        périmètre (le pipeline continue)."""
        idx = self.resoud_colonne(question)
        if idx is None:
            return None
        lignes = [(i, j, c) for i, j, c in self._lignes_de_valeur(question) if j != idx]
        if not lignes:
            return None
        i0 = sorted({i for i, _, _ in lignes})
        if len(i0) > 1:
            etiqs = ", ".join("« %s » (%s)" % (c, self._etiquette(i, j)) for i, j, c in lignes[:5])
            return ("Dans « %s », plusieurs lignes correspondent : %s. Précise laquelle et je te donne son "
                    "« %s » exact." % (self.titre, etiqs, self.entete[idx]))
        i, _, cle = lignes[0]
        cell = str(self.donnees[i][idx]).strip() if idx < len(self.donnees[i]) else ""
        if not cell:
            return ("Dans « %s », la cellule « %s » de la ligne « %s » (%s) est VIDE — je n'invente pas de "
                    "valeur." % (self.titre, self.entete[idx], cle, self._etiquette(i, idx)))
        return ("Dans « %s » : « %s » de « %s » = %s (%s)." %
                (self.titre, self.entete[idx], cle, cell, self._etiquette(i, idx)))

    def compte_valeur(self, question: str):
        """COMPTAGE CONDITIONNEL : « combien de lignes ont pomme ? » → nombre de lignes portant cette valeur
        (colonne réelle nommée dans la preuve). None si aucune valeur du tableau n'est dans la question."""
        lignes = self._lignes_de_valeur(question)
        if not lignes:
            return None
        valeur = lignes[0][2]
        colonnes = sorted({j for _, j, _ in lignes})
        n = len({i for i, _, _ in lignes})
        ou = "colonne « %s »" % self.entete[colonnes[0]] if len(colonnes) == 1 else \
             "colonnes %s" % ", ".join("« %s »" % self.entete[j] for j in colonnes)
        return ("Dans « %s » : %d ligne(s) portent « %s » (%s), sur %d ligne(s) de données." %
                (self.titre, n, valeur, ou, self.n))


# ── ARBRE (json) ──────────────────────────────────────────────────────────────────────────────────────────────
class Arbre:
    """Structure JSON interrogeable : comptages exacts, clés réelles, valeur d'une clé (chemin en preuve)."""

    def __init__(self, contenu, titre: str = ""):
        self.racine = contenu
        self.titre = titre or "le fichier"

    def _cles(self):
        """Clés du SOMMET : dict → ses clés ; liste de dicts → les clés (unies) de ses éléments."""
        if isinstance(self.racine, dict):
            return list(self.racine.keys()), "au sommet"
        if isinstance(self.racine, list) and self.racine and all(isinstance(e, dict) for e in self.racine):
            vues, ordre = set(), []
            for e in self.racine:
                for k in e:
                    if k not in vues:
                        vues.add(k); ordre.append(k)
            return ordre, "de chaque élément"
        return [], ""

    def _cherche(self, cle_normalisee: str, noeud=None, chemin="racine", vus=None):
        """Toutes les occurrences (chemin, valeur) d'une clé (normalisée, pluriel toléré) — parcours borné."""
        if vus is None:
            noeud, vus = self.racine, [0]
        out = []
        vus[0] += 1
        if vus[0] > 100000:                   # borne dure : jamais d'emballement sur un JSON pathologique
            return out
        if isinstance(noeud, dict):
            for k, v in noeud.items():
                nk = normalise(str(k))
                if nk == cle_normalisee or nk.rstrip("sx") == cle_normalisee.rstrip("sx"):
                    out.append((chemin + "." + str(k), v))
                out.extend(self._cherche(cle_normalisee, v, chemin + "." + str(k), vus))
        elif isinstance(noeud, list):
            for i, v in enumerate(noeud):
                out.extend(self._cherche(cle_normalisee, v, chemin + "[%d]" % i, vus))
        return out

    @staticmethod
    def _decrit(v) -> str:
        if isinstance(v, dict):
            return "un objet à %d clé(s) (%s)" % (len(v), ", ".join(list(map(str, v))[:6]))
        if isinstance(v, list):
            return "une liste de %d élément(s)" % len(v)
        if isinstance(v, bool):
            return "vrai" if v else "faux"
        if v is None:
            return "null"
        return json.dumps(v, ensure_ascii=False) if isinstance(v, str) else _fmt(float(v))

    def compte(self, question: str):
        """« combien de X ? » → longueur EXACTE de la liste/objet X (ou du sommet). None hors périmètre."""
        q = normalise(question)
        m = re.search(r"combien (?:de |d )?([a-z0-9 ]{2,40})", q)
        if m:
            brut = m.group(1).strip()
            # essaie le segment entier puis son 1er mot (« combien de livres dans le fichier » → « livres »)
            for cand in (brut, brut.split()[0] if brut.split() else ""):
                if not cand or cand in ("elements", "element", "entrees", "entree", "objets", "objet",
                                        "lignes", "ligne", "items", "item", "cles", "cle"):
                    break
                hits = [(c, v) for c, v in self._cherche(normalise(cand)) if isinstance(v, (list, dict))]
                if len(hits) == 1:
                    c, v = hits[0]
                    return ("Dans « %s » : « %s » contient exactement %d élément(s) (%s)." %
                            (self.titre, c.split(".")[-1], len(v), c))
                if len(hits) > 1:
                    det = " ; ".join("%s : %d" % (c, len(v)) for c, v in hits[:5])
                    return ("Dans « %s », « %s » apparaît %d fois : %s." % (self.titre, cand, len(hits), det))
        if re.search(r"combien (?:d |de )?(elements?|entrees?|objets?|items?|lignes?)\b", q) or \
           re.search(r"\bcombien\b.*\b(contient|compte|dedans|fichier|json|document)\b", q):
            if isinstance(self.racine, list):
                return "Dans « %s » : la liste au sommet contient exactement %d élément(s)." % (self.titre, len(self.racine))
            if isinstance(self.racine, dict):
                return "Dans « %s » : l'objet au sommet contient exactement %d clé(s) (%s)." % (
                    self.titre, len(self.racine), ", ".join(list(map(str, self.racine))[:10]))
        return None

    def cles(self, question: str):
        """« quelles sont les clés / quels champs ? » → clés réelles. None hors périmètre."""
        q = normalise(question)
        if not re.search(r"\b(cles?|champs?|attributs?|proprietes?)\b", q):
            return None
        cles, ou = self._cles()
        if not cles:
            return "Dans « %s », le sommet n'est ni un objet ni une liste d'objets — pas de clés à lister." % self.titre
        return "Dans « %s », les clés %s : %s." % (self.titre, ou, ", ".join(map(str, cles[:40])))

    def valeur(self, question: str):
        """« quel est le X ? / que vaut X ? » → valeur EXACTE de la clé X (chemin en preuve). Plusieurs
        occurrences → toutes listées (bornées à 5), jamais un choix silencieux. None si aucune clé du fichier
        n'est dans la question."""
        q = " " + normalise(question) + " "
        cles_vues = {}
        for chemin, v in self._cherche_toutes_cles():
            n = normalise(chemin.rsplit(".", 1)[-1])
            if len(n) >= 2 and (" " + n + " ") in q:
                cles_vues.setdefault(n, []).append((chemin, v))
        if not cles_vues:
            return None
        n = max(cles_vues, key=len)            # la clé la plus LONGUE nommée dans la question
        occ = cles_vues[n]
        if len(occ) == 1:
            c, v = occ[0]
            return "Dans « %s » : %s = %s." % (self.titre, c, self._decrit(v))
        det = " ; ".join("%s = %s" % (c, self._decrit(v)) for c, v in occ[:5])
        plus = " (+%d autres)" % (len(occ) - 5) if len(occ) > 5 else ""
        return "Dans « %s », « %s » apparaît %d fois : %s%s." % (self.titre, n, len(occ), det, plus)

    def _cherche_toutes_cles(self, noeud=None, chemin="racine", vus=None):
        """Toutes les paires (chemin, valeur) de l'arbre (bornées) — support de `valeur`."""
        if vus is None:
            noeud, vus = self.racine, [0]
        out = []
        vus[0] += 1
        if vus[0] > 100000:
            return out
        if isinstance(noeud, dict):
            for k, v in noeud.items():
                out.append((chemin + "." + str(k), v))
                out.extend(self._cherche_toutes_cles(v, chemin + "." + str(k), vus))
        elif isinstance(noeud, list):
            for i, v in enumerate(noeud):
                out.extend(self._cherche_toutes_cles(v, chemin + "[%d]" % i, vus))
        return out


# ── ROUTEUR : question → opération (None = hors périmètre, AUCUNE capture indue) ────────────────────────────
_RE_OP = [("max", re.compile(r"\b(max|maximum|plus (?:grand|grande|eleve|elevee|haut|haute|cher|chere|long|longue))\b")),
          ("min", re.compile(r"\b(min|minimum|plus (?:petit|petite|bas|basse|faible)|moins (?:cher|chere|eleve|elevee))\b")),
          ("somme", re.compile(r"\b(somme|total|totale|cumul|additionne)\b")),
          ("moyenne", re.compile(r"\bmoyenne?\b"))]
_RE_LIGNES = re.compile(r"\bcombien\b.*\b(lignes?|entrees?|enregistrements?|elements?|items?)\b|"
                        r"\bnombre (?:de |d )(lignes?|entrees?|enregistrements?|elements?)\b")
_RE_COLONNES = re.compile(r"\b(quelles? (?:sont )?(?:les )?colonnes?|liste (?:des |les )?colonnes?|"
                          r"combien (?:de |d )colonnes?|quels? (?:sont )?(?:les )?champs?)\b")
_RE_REF_DOC = re.compile(r"\b(fichier|csv|tsv|json|tableau|document|donnees|colonne)\b")


def repond(question: str, donnees):
    """Point d'entrée : réponse EXACTE depuis le document structuré attaché, ou None (hors périmètre — le
    pipeline normal continue). `donnees` = Tableau | Arbre | None."""
    if donnees is None or not str(question or "").strip():
        return None
    q = normalise(question)
    if isinstance(donnees, Tableau):
        if donnees.n == 0:
            return None
        if _RE_COLONNES.search(q):
            if re.search(r"\bcombien\b", q):
                return "Dans « %s » : %d colonne(s) (%s)." % (donnees.titre, len(donnees.entete),
                                                              ", ".join(donnees.entete))
            return "Dans « %s », les colonnes sont : %s (%d ligne(s) de données)." % (
                donnees.titre, ", ".join(donnees.entete), donnees.n)
        if _RE_LIGNES.search(q) and donnees._lignes_de_valeur(question) == []:
            return "Dans « %s » : exactement %d ligne(s) de données (hors en-tête)." % (donnees.titre, donnees.n)
        for op, motif in _RE_OP:
            if motif.search(q):
                idx = donnees.resoud_colonne(question)
                if idx is not None:
                    return donnees.agregat(op, idx)
                # pas de colonne résolue : on ne capte QUE si la question référence explicitement le fichier
                if _RE_REF_DOC.search(q):
                    return ("Je vois « %s » dans ta question mais aucune colonne de « %s » ne s'y trouve. "
                            "Colonnes disponibles : %s." % (op, donnees.titre, ", ".join(donnees.entete)))
                return None
        if re.search(r"\bcombien\b", q):
            r = donnees.compte_valeur(question)
            if r:
                return r
            if _RE_LIGNES.search(q):
                return "Dans « %s » : exactement %d ligne(s) de données (hors en-tête)." % (donnees.titre, donnees.n)
            return None
        return donnees.cellule(question)
    if isinstance(donnees, Arbre):
        for methode in (donnees.cles, donnees.compte, donnees.valeur):
            r = methode(question)
            if r:
                return r
    return None
