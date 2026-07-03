"""
Brique 3 — LE GÉNÉRATEUR.

Celui qui PROPOSE des solutions. Dans le projet final, ce sera le LLM ouvert
qu'on fait s'auto-améliorer. Ici on pose surtout l'INTERFACE — propre et
swappable — pour pouvoir tester toute la boucle SANS GPU, avec un factice.

Principes (cf. PROJET-AUTO-AMELIORATION-CODE.md §3, §7, §9) :
  - Le générateur ne reçoit QUE le prompt (l'énoncé). Il ne voit JAMAIS les
    tests cachés : c'est ça qui rend le juge incorruptible côté générateur.
  - Interface minimale et stable : `propose(prompt, n) -> list[str]`. Le vrai
    LLM, plus tard, satisfait la MÊME interface -> on le branche sans toucher
    au juge, au store, ni à la boucle (Décision : frontière étanche).
  - Déterministe par défaut (RNG seedé) : runs reproductibles, sinon on ne sait
    pas distinguer une vraie amélioration d'un coup de chance.
"""

from __future__ import annotations

import ast
import copy
import functools
import random
import re
from typing import Protocol, runtime_checkable


@runtime_checkable
class Generateur(Protocol):
    """
    Le contrat que TOUT générateur doit respecter (factice aujourd'hui, LLM demain).

    propose(prompt, n) -> renvoie jusqu'à n candidats (du code Python, sous forme
    de chaînes) pour l'énoncé donné. N'a accès qu'au prompt : aucun test caché.
    """
    def propose(self, prompt: str, n: int) -> list[str]: ...


class GenerateurFactice:
    """
    Un générateur de test, adossé à une BANQUE de candidats pré-écrits par prompt.

    Sert à exercer la boucle entière (générer -> juger -> garder) sans modèle :
    on y met exprès un mélange réaliste (corrects variés, faux, lents, invalides)
    pour vérifier que le juge et le store se comportent bien sur chaque cas.

    Déterministe : à seed égale, même ordre de candidats -> run reproductible.
    """

    def __init__(self, banque: dict[str, list[str]], seed: int = 0):
        self._banque = banque
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        candidats = self._banque.get(prompt, [])
        if not candidats:
            return []
        # Ordre mélangé de façon déterministe (le RNG dépend de la seed + du prompt).
        rng = random.Random(f"{self._seed}\0{prompt}")
        melange = candidats[:]
        rng.shuffle(melange)
        # On "tire" n candidats ; si n > banque, on resample (un vrai modèle
        # ré-échantillonne et répète parfois -> le store dé-dupliquera).
        return [melange[i % len(melange)] for i in range(n)]


class GenerateurApprenant:
    """
    Faux générateur dont la COMPÉTENCE monte à chaque appel à apprendre() — simule
    sans GPU l'effet du fine-tuning sur les succès vérifiés. À compétence c (0..1),
    chaque proposition est tirée dans `montantes` (ce qu'il sait de mieux en mieux
    produire) avec probabilité c, sinon dans `brouillons` (ses ratés du début).

    Selon ce qu'on met dans `montantes`, le MÊME objet simule deux mondes — c'est
    ce qui permet à B7 de prouver qu'il distingue l'un de l'autre :
      - VRAI apprentissage   : montantes = solutions qui généralisent ;
      - PIÈGE d'auto-illusion : montantes = hard-coders (passent le visible,
        échouent le held-out) -> il se croit meilleur sans l'être.

    Déterministe (RNG seedé par compétence + prompt) : courbe reproductible.
    """

    def __init__(self, prompt: str, montantes: list[str], brouillons: list[str],
                 competence: float = 0.0, seed: int = 0):
        self._prompt = prompt
        self._montantes = list(montantes)
        self._brouillons = list(brouillons)
        self.competence = competence
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        if prompt != self._prompt or not self._montantes:
            return []
        rng = random.Random(f"{self._seed}|{self.competence:.4f}|{prompt}")
        out = []
        for _ in range(n):
            pool = self._montantes if rng.random() < self.competence else self._brouillons
            if pool:
                out.append(rng.choice(pool))
        return out

    def apprendre(self, delta: float = 0.2) -> float:
        """Monte d'un cran de compétence (ce que ferait un tour de fine-tuning)."""
        self.competence = min(1.0, self.competence + delta)
        return self.competence


class GenerateurAmeliorant:
    """
    Démo de consolidation : par tâche, une liste de solutions CORRECTES du moins au
    plus utile. À mesure que la compétence monte (apprendre()), il débloque de
    meilleures solutions -> la Selection (utilité évolutive) supplante l'ancienne.
    Simule un modèle qui produit « de mieux en mieux » au fil de l'entraînement.
    """

    def __init__(self, paliers: dict[str, list[str]], competence: float = 0.0):
        self._paliers = paliers   # prompt -> [du moins utile ... au plus utile]
        self.competence = competence

    def propose(self, prompt: str, n: int) -> list[str]:
        sols = self._paliers.get(prompt)
        if not sols:
            return []
        k = min(len(sols) - 1, int(self.competence * len(sols)))
        return [sols[k]] * n   # la meilleure solution débloquée à ce niveau

    def apprendre(self, delta: float = 0.6) -> float:
        self.competence = min(1.0, self.competence + delta)
        return self.competence


class GenerateurAleatoire:
    """
    G0 — LE PLANCHER du générateur maison.

    Produit du code "au hasard" : il lit juste le nom de la fonction dans l'énoncé
    et renvoie un corps trivial tiré d'un petit vocabulaire. AUCUNE connaissance,
    AUCUN apprentissage, AUCUN accès au store. C'est le pire générateur honnête.

    Son unique rôle : établir le PLANCHER de réussite — ce qu'on obtient sans rien
    savoir. Toute brique de générateur suivante (G1 = recombinaison du store, etc.)
    devra le BATTRE, et le prouver via la courbe de B7. C'est aussi la mesure
    EMPIRIQUE du mur du démarrage à froid : du code aléatoire ne passe ~rien.
    """

    # Le "best effort" d'un ignorant : des corps qui parsent mais ne savent rien.
    _VOCAB = [
        "None", "0", "1", "True", "False", "''", "[]", "{}",
        "args[0] if args else None",
        "len(args[0]) if args else 0",
        "not args[0] if args else False",
    ]

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        # Le nom de la fonction est dans l'énoncé (légitimement disponible).
        m = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not m:
            return []
        fn = m.group(1)
        rng = random.Random(f"{self._seed}|{prompt}")
        return [f"def {fn}(*args, **kwargs):\n    return {rng.choice(self._VOCAB)}\n"
                for _ in range(n)]


def _mute(code: str, rng: random.Random) -> str:
    """
    Mutation légère d'un code qui marche : échange UN opérateur de comparaison.
    La plupart des mutations cassent la correction (le juge les filtre) ; certaines
    sont inoffensives. C'est l'exploration "autour" d'un succès connu — peu rentable,
    mais gratuite, et c'est le juge qui tranche ce qui survit.
    """
    for a, b in (("<=", "<"), (">=", ">"), ("==", "!="), ("<", ">")):
        if a in code and rng.random() < 0.5:
            return code.replace(a, b, 1)
    return code


class GenerateurBriques:
    """
    G2 — SYNTHÈSE PAR ASSEMBLAGE DE BRIQUES (l'échafaudage initial).

    Une petite bibliothèque GÉNÉRALE de squelettes + remplisseurs, semée à la main
    (c'est moi, le curateur/échafaudage). G2 assemble des candidats en combinant ces
    briques ; le juge sélectionne ce qui marche. Son rôle unique : BOOTSTRAPER un
    store FROID — produire les premiers succès, ce que G1 (réutilisation) ne peut
    pas faire seul. Une fois le store amorcé, G1 prend le relais (mémoire).

    Honnêteté (le mur, mesurable) : la bibliothèque est VOLONTAIREMENT petite et
    générale. Elle ne couvre donc PAS tout. Ce que G2 ne résout pas = le mur — à
    repousser (plus de briques = plus d'échafaudage, G3) ou à confier au vrai modèle.
    On ne code pas l'answer de chaque tâche : on code des PRIMITIVES, et on mesure.
    """

    # (squelette avec un trou, nom du trou). Le corps utilise args[0] = 1re entrée.
    _SQUELETTES = [
        ("return {E}", "E"),
        ("return sum(1 for x in args[0] if {P})", "P"),
        ("return any({P} for x in args[0])", "P"),
        ("return all({P} for x in args[0])", "P"),
    ]
    _REMPLISSEURS = {
        "E": ["len(args[0])", "sum(args[0])", "args[0]", "0", "True", "False", "len(args[0]) > 0"],
        "P": ["x % 2 == 0", "x % 2 == 1", "x > 0", "x < 0", "x == 0"],
    }

    def __init__(self, seed: int = 0, squelettes=None, remplisseurs=None):
        # Bibliothèque paramétrable : par défaut la pleine, mais G3 (ablation)
        # peut en passer des sous-ensembles pour mesurer ce qui est porteur.
        self._seed = seed
        self.squelettes = squelettes if squelettes is not None else list(self._SQUELETTES)
        self.remplisseurs = remplisseurs if remplisseurs is not None else {
            trou: list(vals) for trou, vals in self._REMPLISSEURS.items()}
        self._combos = [sq.replace("{" + trou + "}", r)
                        for sq, trou in self.squelettes
                        for r in self.remplisseurs.get(trou, [])]

    def propose(self, prompt: str, n: int) -> list[str]:
        m = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not m or not self._combos:
            return []   # pas de fonction, ou bibliothèque vide (ablation poussée à bout)
        fn = m.group(1)
        rng = random.Random(f"{self._seed}|{prompt}")
        corps = self._combos[:]
        rng.shuffle(corps)
        tires = corps[:n] if n <= len(corps) else [corps[i % len(corps)] for i in range(n)]
        return [f"def {fn}(*args, **kwargs):\n    {c}\n" for c in tires]

    def apprendre(self, delta: float = 0.0) -> int:
        return 0  # G2 est statique : ses briques sont fixes (c'est l'échafaudage).


# Le VOCABULAIRE de fragments minables, du plus pauvre (logique pure) au plus riche.
# C'est le seul levier : élargir ce tuple suffit à donner à la recombinaison (et à la
# compréhension) accès à plus de concepts, SANS toucher au moteur lui-même.
TYPES_CONDITIONS = (ast.Compare, ast.BoolOp)                    # le « sens » historique : un test booléen
TYPES_RICHES = (ast.Compare, ast.BoolOp, ast.BinOp, ast.Call)  # + opérations binaires (a+b, a*b) ET agrégations (sum(...), max(...))


def fragments_riches(code: str, types=TYPES_CONDITIONS):
    """
    Mine les fragments d'une solution, via AST (pas du texte) :
      - l'EXPRESSION de retour (le « quoi ») ;
      - ses SOUS-EXPRESSIONS des `types` demandés = les morceaux interchangeables (le « sens »).

    `types` règle la RICHESSE du vocabulaire de concepts — c'est LA racine :
      - TYPES_CONDITIONS : uniquement la logique booléenne (comportement historique) ;
      - TYPES_RICHES     : + opérations binaires (`a + b`, `x * x`) et agrégations
        (`sum(...)`, `max(...)`) -> de quoi recombiner des solutions que la logique
        seule ne pouvait pas atteindre (ex. `max(x * x for x in args[0])`).

    Renvoie (expr_source, (fragments_source...)) dans l'ordre de parcours de l'arbre.
    Le squelette = l'expression avec un trou {C} à la place d'un fragment -> recombinable
    avec un fragment d'ailleurs.

    MÉMOÏSÉ (lru_cache) : fonction PURE (code+types -> sortie déterministe), appelée des dizaines de
    milliers de fois sur les MÊMES solutions du store (abstrais re-mine tout le store en boucle). Le
    parse + double walk + ast.unparse (sérialisation AST->source, lourde) est le hot-spot n°1 mesuré
    (cProfile valide_vague8). Le cache l'élimine pour toute l'IA. Retour IMMUABLE (tuple) -> partage sûr.
    """
    return _fragments_riches(code, types)


@functools.lru_cache(maxsize=1 << 17)
def _fragments_riches(code: str, types):
    try:
        arbre = ast.parse(code)
    except SyntaxError:
        return None, ()
    retour = None
    for n in ast.walk(arbre):
        if isinstance(n, ast.Return) and n.value is not None:
            retour = n.value
    if retour is None:
        return None, ()
    expr = ast.unparse(retour)
    fragments = tuple(ast.unparse(n) for n in ast.walk(retour) if isinstance(n, types))
    return expr, fragments


class GenerateurRecombinant:
    """
    G5 — RECOMBINAISON (vers « il construit sa logique seul »).

    Au-delà de G1 qui REUTILISE une solution telle quelle, G5 DÉCOMPOSE les succès
    du store en fragments (squelettes + conditions) et les RECOMBINE pour fabriquer
    des solutions à des tâches JAMAIS résolues. La logique d'une tâche neuve émerge
    en combinant des morceaux appris sur d'AUTRES tâches.

    Honnêteté : il ne peut recombiner que ce qu'il a déjà miné. Si le bon fragment
    n'est nulle part dans le store, il ne peut pas le sortir du chapeau (ce n'est pas
    de l'invention — c'est de la recombinaison). C'est le juge qui valide ce qui marche.

    `types` règle la RICHESSE du vocabulaire de fragments (cf. `fragments_riches`) :
    par défaut les conditions (historique) ; avec `TYPES_RICHES`, le MÊME moteur recombine
    aussi des opérations binaires et des agrégations -> il atteint des solutions hors de
    portée de la logique seule, sans qu'une ligne du moteur ne change.
    """

    def __init__(self, store, seed: int = 0, types=TYPES_CONDITIONS):
        self._store = store
        self._seed = seed
        self._types = types

    def _pool(self):
        squelettes, sens = set(), set()
        for s in self._store:
            try:
                expr, frags = fragments_riches(s.solution, self._types)
            except SyntaxError:
                continue
            if expr is None:
                continue
            for c in frags:
                sens.add(c)
                if c in expr:
                    sk = expr.replace(c, "{C}", 1)              # squelette = trou à la place d'un fragment
                    if sk != "{C}":                            # trou == TOUTE l'expr -> squelette dégénéré :
                        squelettes.add(sk)                     # rebouché par un sens nu (`x*x`) = variable libre
        return squelettes, sens                                # -> NameError systématique. On l'écarte (candidat mort).

    def propose(self, prompt: str, n: int) -> list[str]:
        m = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not m:
            return []
        fn = m.group(1)
        squelettes, sens = self._pool()
        candidats = []
        for sq in sorted(squelettes):
            for c in sorted(sens):
                expr = sq.replace("{C}", c)
                candidats.append(f"def {fn}(*args, **kwargs):\n    return {expr}\n")
        candidats = list(dict.fromkeys(candidats))   # dé-dup
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(candidats)
        return candidats[:n] if n <= len(candidats) else candidats

    def apprendre(self, delta: float = 0.0) -> int:
        return len(list(self._store))   # G5 apprend via le store qui grandit (passif)


def _pieces_comprehension(solution: str, collections: bool = True):
    """
    Extrait les PIÈCES composables d'un succès bâti sur une compréhension à UN générateur :
      - forme AGRÉGÉE  : `AGG(elt for v in it [if conds])`  (sum/max/min/any/all/...) ;
      - forme LISTE    : `[elt for v in it [if conds]]`      (couvre aussi le domaine chaînes) ;
      - formes ENSEMBLE/DICT (si `collections`) : `{elt for ...}` / `{k: v for ...}` (élargissement).
    On en tire :
      - le CADRE d'itération = ce que deux succès doivent PARTAGER pour être fusionnables :
          ("call", agg, variable, itérable)  ou  ("list", variable, itérable) ;
      - l'ÉLÉMENT (le « quoi » transformé) ;
      - les FILTRES (le « lesquels » gardés).
    Renvoie [(cadre, element_src, [filtre_src])] (vide si la solution n'a pas cette forme).
    C'est la matière de la fusion d'expressions : un succès apporte un élément, un autre un
    filtre, sur le MÊME cadre -> on les compose.
    """
    try:
        arbre = ast.parse(solution)
    except SyntaxError:
        return []
    retour = None
    for n in ast.walk(arbre):
        if isinstance(n, ast.Return) and n.value is not None:
            retour = n.value
    if retour is None:
        return []
    # forme AGRÉGÉE : AGG(elt for v in it [if ...]), agg = nom simple
    if (isinstance(retour, ast.Call) and isinstance(retour.func, ast.Name)
            and len(retour.args) == 1 and not retour.keywords
            and isinstance(retour.args[0], ast.GeneratorExp)):
        gen = retour.args[0]
        if len(gen.generators) == 1 and not gen.generators[0].is_async:
            comp = gen.generators[0]
            cadre = ("call", retour.func.id, ast.unparse(comp.target), ast.unparse(comp.iter))
            return [(cadre, ast.unparse(gen.elt), [ast.unparse(c) for c in comp.ifs])]
    # forme LISTE : [elt for v in it [if ...]]
    if isinstance(retour, ast.ListComp) and len(retour.generators) == 1 \
            and not retour.generators[0].is_async:
        comp = retour.generators[0]
        cadre = ("list", ast.unparse(comp.target), ast.unparse(comp.iter))
        return [(cadre, ast.unparse(retour.elt), [ast.unparse(c) for c in comp.ifs])]
    if collections:
        # forme ENSEMBLE : {elt for v in it [if ...]} — élargissement du vocabulaire (étage 1).
        if isinstance(retour, ast.SetComp) and len(retour.generators) == 1 \
                and not retour.generators[0].is_async:
            comp = retour.generators[0]
            cadre = ("set", ast.unparse(comp.target), ast.unparse(comp.iter))
            return [(cadre, ast.unparse(retour.elt), [ast.unparse(c) for c in comp.ifs])]
        # forme DICT : {k: v for v in it [if ...]} — l'élément porte la paire `clé: valeur`.
        if isinstance(retour, ast.DictComp) and len(retour.generators) == 1 \
                and not retour.generators[0].is_async:
            comp = retour.generators[0]
            cadre = ("dict", ast.unparse(comp.target), ast.unparse(comp.iter))
            element = f"{ast.unparse(retour.key)}: {ast.unparse(retour.value)}"
            return [(cadre, element, [ast.unparse(c) for c in comp.ifs])]
    return []


def _reconstruit_cadre(cadre, noyau: str) -> str:
    """Réassemble le corps depuis un cadre et le noyau « elt for v in it [if f] »."""
    if cadre[0] == "call":
        return f"{cadre[1]}({noyau})"
    if cadre[0] == "list":
        return f"[{noyau}]"
    return f"{{{noyau}}}"   # set / dict : mêmes accolades ; le noyau porte la différence (`k: v`)


class GenerateurFusion:
    """
    FUSION VERTICALE (1er étage : fusion d'EXPRESSIONS) — composer, pas juste substituer.

    Le mur mesuré (`valide_carte.py`) : la recombinaison est d'ARITÉ UN (un trou) ; elle ne
    sait pas COMBINER deux sous-compétences. La fusion la dépasse : elle prend deux succès
    confirmés qui PARTAGENT un cadre d'itération `AGG(... for v in it ...)` et compose
    l'ÉLÉMENT de l'un avec le FILTRE de l'autre -> une expression à DEUX variations que la
    recombinaison ne pouvait pas atteindre (ex. `sum(x*x for x in args[0] if x>0)`).

    Honnêteté (la frontière, tenue) : il ne compose que des pièces DÉJÀ confirmées et de
    cadre COMPATIBLE — il ne sort rien du chapeau. Et il reste dans le monde des
    expressions : il ne franchit PAS le mur multi-étapes (boucle à état, récursion) — ça,
    c'est l'étage suivant (primitives appelables). C'est le juge qui valide ce qui marche.
    """

    def __init__(self, store, seed: int = 0, collections: bool = True):
        self._store = store
        self._seed = seed
        self._collections = collections   # set/dict-comp dans le vocabulaire de fusion (toggle A/B)

    def _cadres(self):
        # cadre -> (éléments vus, filtres vus) — agrégés sur tout le store
        cadres: dict[tuple, tuple[set, set]] = {}
        for s in self._store:
            for cadre, element, filtres in _pieces_comprehension(s.solution, self._collections):
                elems, filts = cadres.setdefault(cadre, (set(), set()))
                elems.add(element)
                filts.update(filtres)
        return cadres

    def propose(self, prompt: str, n: int) -> list[str]:
        m = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not m:
            return []
        fn = m.group(1)
        candidats = []
        for cadre, (elements, filtres) in self._cadres().items():
            var, it = cadre[-2], cadre[-1]
            options_filtre = [None] + sorted(filtres)   # None = pas de filtre (cas arité 1)
            for elem in sorted(elements):
                for filtre in options_filtre:
                    noyau = f"{elem} for {var} in {it}" + (f" if {filtre}" if filtre else "")
                    corps = _reconstruit_cadre(cadre, noyau)
                    candidats.append(f"def {fn}(*args, **kwargs):\n    return {corps}\n")
        candidats = list(dict.fromkeys(candidats))   # dé-dup
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(candidats)
        return candidats[:n] if n <= len(candidats) else candidats

    def apprendre(self, delta: float = 0.0) -> int:
        return len(list(self._store))   # passif : grandit avec le store, comme G5


class GenerateurCompose:
    """
    FUSION VERTICALE (2e étage : SÉQUENÇAGE de primitives appelables) — le saut de nature.

    Un succès confirmé devient une PRIMITIVE nommée et appelable. Ce générateur fabrique des
    solutions en NIDIFIANT deux primitives : `g(x) = p2(p1(x))`. Le candidat est AUTONOME — il
    embarque les sources des primitives puis définit `g` qui les appelle — donc le juge l'exécute
    tel quel, sans dépendance externe.

    C'est ce qui franchit ce que l'expression unique ne peut pas : des pipelines NON réductibles
    à une compréhension (ex. `avant_dernier(trie(xs))` = `sorted(xs)[-2]`). Et — le cœur de la
    fusion verticale — un composé confirmé peut être REVERSÉ dans la liste des primitives : il
    devient une brique d'un étage supérieur (tours de skills). Le crédit long horizon se résout
    ainsi : on cherche de COURTES nidifications de primitives profondes, pas la solution entière.

    Honnêteté : il ne nidifie que des primitives DÉJÀ confirmées — il ne sort rien du chapeau.
    C'est le juge qui valide la composition qui marche.

    Profondeur (industrialisée) : `profondeur` règle la longueur MAX des chaînes nidifiées (défaut 2 =
    comportement historique `p2(p1(x))`). À 3+, il nidifie `p3(p2(p1(x)))` en UN coup — il franchit ce
    que la profondeur 2 ne peut PAS sans tremplin intermédiaire (mur mesuré par `valide_compounding_stress`).
    Primitives DISTINCTES dans une chaîne (anti-explosion, anti-dégénérescence p(p(x))).
    """

    def __init__(self, primitives, seed: int = 0, profondeur: int = 2):
        # primitives : liste de (nom, source) — des succès confirmés rendus appelables.
        self._primitives = list(primitives)
        self._seed = seed
        self._profondeur = max(2, profondeur)

    def propose(self, prompt: str, n: int) -> list[str]:
        m = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not m:
            return []
        g = m.group(1)
        prims = [(nom, src) for nom, src in self._primitives if nom != g]
        candidats = []
        # chaînes de primitives DISTINCTES de longueur 2..profondeur : g(x) = pk(...p2(p1(x))...).
        chaines = [(i,) for i in range(len(prims))]              # longueur 1 (amorce)
        for _ in range(2, self._profondeur + 1):
            chaines = [ch + (i,) for ch in chaines for i in range(len(prims)) if i not in ch]
            for ch in chaines:
                srcs = "".join(dict.fromkeys(prims[i][1] for i in ch))   # sources embarquées (dé-dup)
                expr = "args[0]"
                for i in ch:                                            # cascade inner-first
                    expr = f"{prims[i][0]}({expr})"
                candidats.append(f"{srcs}def {g}(*args, **kwargs):\n    return {expr}\n")
        candidats = list(dict.fromkeys(candidats))   # dé-dup
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(candidats)
        return candidats[:n] if n <= len(candidats) else candidats

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._primitives)   # passif : grandit quand un composé rejoint les primitives


class GenerateurPli:
    """
    FUSION VERTICALE (2e étage, variante 2b : COMBINATEURS d'ordre supérieur) — le stateful pur.

    Le séquençage (2a) ne franchit pas l'ÉTAT (factorielle, max courant). Ici on REPLIE une
    OPÉRATION BINAIRE confirmée sur une séquence, via deux combinateurs GÉNÉRAUX (échafaudage,
    pas des réponses par tâche) :
      - `reduce(op, seq, init)`        -> un scalaire (ex. factorielle = reduce(mul, range(1,n+1), 1)) ;
      - `list(accumulate(seq, op))`    -> une liste (ex. max courant = list(accumulate(xs, max2))).
    L'op binaire vient d'un succès CONFIRMÉ (ex. `mul`, `max2`) ; le candidat est AUTONOME
    (imports + source de l'op + g). Le pli porte l'état que l'expression unique ne pouvait pas.

    Honnêteté : `reduce`/`accumulate` sont des combinateurs UNIVERSELS (pas l'answer d'une tâche) ;
    l'op est confirmée ; c'est le juge qui valide le pli qui marche. Sans op confirmée, rien ne sort.
    """

    _SEQUENCES = ["args[0]", "range(args[0])", "range(1, args[0] + 1)"]
    _INITS = ["0", "1"]

    def __init__(self, ops, seed: int = 0):
        # ops : liste de (nom, source) — des OPÉRATIONS BINAIRES confirmées (op(a, b)).
        self._ops = list(ops)
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        m = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not m:
            return []
        g = m.group(1)
        entete = "from functools import reduce\nfrom itertools import accumulate\n"
        candidats = []
        for nom, src in self._ops:
            if nom == g:
                continue
            for seq in self._SEQUENCES:
                for init in self._INITS:
                    corps = f"reduce({nom}, {seq}, {init})"
                    candidats.append(f"{entete}{src}def {g}(*args, **kwargs):\n    return {corps}\n")
                corps = f"list(accumulate({seq}, {nom}))"
                candidats.append(f"{entete}{src}def {g}(*args, **kwargs):\n    return {corps}\n")
        candidats = list(dict.fromkeys(candidats))   # dé-dup
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(candidats)
        return candidats[:n] if n <= len(candidats) else candidats

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._ops)   # passif : grandit avec les opérations confirmées disponibles


class GenerateurJointure:
    """
    FUSION VERTICALE (cap 2) — COMPOSITION d'ARITÉ 2 : joindre deux sous-résultats.

    Le séquençage (`GenerateurCompose`) est un PIPELINE UNAIRE `p2(p1(x))` : un seul fil. Il ne
    sait pas COMBINER deux extractions. Le stress (`valide_compounding_stress.py`) a mesuré ce mur :
    `xs[0] * xs[-1]` reste hors de portée *même* avec `premier`, `dernier` et `mul` fournis.

    Ici on franchit l'arité 2 : pour une OP binaire CONFIRMÉE (du registre `ops`, comme le pli) et
    deux primitives CONFIRMÉES `p1`, `p2`, on fabrique `g(x) = op(p1(x), p2(x))` — candidat autonome
    (sources embarquées). C'est la SYMÉTRIE du pli (qui replie UNE op sur une séquence) : ici on
    applique UNE op à DEUX projections du même argument. On réutilise le registre vivant (décision
    Yohan) — aucune source d'atomes neuve, on COMPOSE l'existant.

    Honnêteté : ne joint que du confirmé (primitives + op du registre). Sans l'op, ou sans une des
    projections, rien ne sort — c'est le juge qui valide la jointure qui marche.
    """

    def __init__(self, primitives, ops, seed: int = 0):
        self._primitives = list(primitives)
        self._ops = list(ops)
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        m = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not m:
            return []
        g = m.group(1)
        prims = [(nom, src) for nom, src in self._primitives if nom != g]
        ops = [(nom, src) for nom, src in self._ops if nom != g]
        candidats = []
        for opn, opsrc in ops:
            for n1, s1 in prims:
                for n2, s2 in prims:
                    # g(x) = op(p1(x), p2(x)) ; sources embarquées, dé-dupliquées par nom.
                    pieces = {n1: s1, n2: s2, opn: opsrc}
                    corps = "".join(pieces.values())
                    candidats.append(f"{corps}def {g}(*args, **kwargs):\n"
                                     f"    return {opn}({n1}(args[0]), {n2}(args[0]))\n")
        candidats = list(dict.fromkeys(candidats))   # dé-dup
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(candidats)
        return candidats[:n] if n <= len(candidats) else candidats

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._primitives) + len(self._ops)   # passif : grandit avec le registre


class GenerateurMultiEntree:
    """
    COMPOSITION MULTI-ENTRÉE — joindre PLUSIEURS arguments (arité ≥ 2).

    La jointure reste à UN argument (`op(p1(x), p2(x))`, deux projections du même `args[0]`). Le stress
    a mesuré le mur : les tâches à PLUSIEURS arguments (`moyenne_deux(a,b)`, `clamp(x,lo,hi)`) sont hors de
    portée car TOUT générateur n'opère que sur `args[0]`. Ici on lève ce mur : on bâtit des arbres d'OPS
    binaires CONFIRMÉES (du registre, comme le pli/la jointure) sur les arguments BRUTS `args[0..m-1]`,
    en profondeur bornée -> ex. `clamp = max2(args[1], min2(args[0], args[2]))`.

    Ne s'active que pour l'arité ≥ 2 (le mono-argument est le domaine de la jointure) -> aucun effet sur
    les tâches mono-argument. Honnête : n'emploie que des ops confirmées ; sans op, rien.
    """

    def __init__(self, ops, seed: int = 0, profondeur: int = 2):
        self._ops = list(ops)
        self._seed = seed
        self._prof = profondeur

    @staticmethod
    def _arite(prompt: str) -> int:
        m = re.search(r"def\s+\w+\s*\(([^)]*)\)", prompt)
        if not m:
            return 0
        return len([p for p in m.group(1).split(",") if p.strip()])

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        arite = self._arite(prompt)
        ops = [(nom, src) for nom, src in self._ops if nom != g]
        if arite < 2 or not ops:           # mono-argument -> domaine de la jointure ; rien sans op
            return []
        feuilles = [f"args[{i}]" for i in range(arite)]
        d1 = [f"{on}({a}, {b})" for on, _ in ops for a in feuilles for b in feuilles]
        exprs = list(d1)
        if self._prof >= 2:
            exprs += [f"{on}({a}, {d})" for on, _ in ops for a in feuilles for d in d1]
            exprs += [f"{on}({d}, {a})" for on, _ in ops for a in feuilles for d in d1]
        preambule = "".join(dict.fromkeys(src for _, src in ops))   # sources des ops (dé-dup)
        cands = [f"{preambule}def {g}(*args, **kwargs):\n    return {e}\n"
                 for e in dict.fromkeys(exprs)]
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._ops)


class GenerateurBranche:
    """
    BRANCHEMENT — le contrôle, en périmètre ÉTROIT (ternaire, pas de boucle).

    Dernier mur du plafond : le CONTRÔLE (`signe`, etc.). Admettre du contrôle, c'est risquer de
    rouvrir tout l'espace des programmes. On le cadre donc serré (décision Yohan « branchement seul
    d'abord ») : un TERNAIRE `a if pred(x) else b`, éventuellement imbriqué une fois, où `pred` est un
    PRÉDICAT CONFIRMÉ (un atome booléen unaire du registre, comme une op est un atome confirmé) et a/b
    viennent d'un petit jeu de valeurs. AUCUNE boucle (différée : brique séparée).

    Honnête : n'emploie que des prédicats confirmés ; sans prédicat, rien. Borné : profondeur ≤ 2,
    valeurs en petit nombre -> pas d'explosion. `signe = 1 if est_positif(x) else (-1 if est_negatif(x) else 0)`.
    """

    VALEURS = ("0", "1", "-1", "args[0]")

    def __init__(self, predicats, valeurs=None, seed: int = 0):
        # predicats : liste de (nom, source) — atomes booléens unaires confirmés.
        self._predicats = list(predicats)
        self._valeurs = tuple(valeurs) if valeurs is not None else self.VALEURS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        preds = [(nom, src) for nom, src in self._predicats if nom != g]
        if not preds:
            return []
        vals = self._valeurs
        preambule = "".join(dict.fromkeys(src for _, src in preds))
        exprs = []
        # profondeur 1 : a if pred(x) else b  (a == b -> ternaire INERTE = constante, prédicat sans effet : écarté)
        for pn, _ in preds:
            for a in vals:
                for b in vals:
                    if a == b:
                        continue
                    exprs.append(f"{a} if {pn}(args[0]) else {b}")
        # profondeur 2 : a if pred1(x) else (b if pred2(x) else c)  (a == b == c -> entièrement constant : écarté)
        for pn1, _ in preds:
            for pn2, _ in preds:
                if pn1 == pn2:
                    continue
                for a in vals:
                    for b in vals:
                        for c in vals:
                            if a == b == c:
                                continue
                            exprs.append(f"{a} if {pn1}(args[0]) else ({b} if {pn2}(args[0]) else {c})")
        cands = [f"{preambule}def {g}(*args, **kwargs):\n    return {e}\n" for e in dict.fromkeys(exprs)]
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._predicats)


class GenerateurBoucle:
    """
    BOUCLE BORNÉE — l'arrêt anticipé, en UN schéma figé (ce que le pli ne peut pas).

    Le pli replie une op sur TOUTE la séquence ; il ne sait pas S'ARRÊTER en cours (`somme_jusqua_neg`).
    Admettre des boucles, c'est le terrain le plus explosif (Turing-complet). On le cadre au maximum
    (suite de « branchement seul d'abord ») : UN SEUL schéma, accumuler-jusqu'à-arrêt, à slots CONFIRMÉS —

        acc = {init}
        for _x in args[0]:
            if {pred}(_x): break        # prédicat CONFIRMÉ
            acc = {op}(acc, _x)         # op CONFIRMÉE
        return acc

    Pas de boucle libre, pas d'imbrication, pas de `while` : juste ce schéma, instancié sur op + prédicat
    confirmés + un petit jeu d'inits. Borné (|ops|×|prédicats|×|inits|), honnête (sans op/prédicat, rien).
    """

    def __init__(self, ops, predicats, inits=(0, 1), seed: int = 0):
        self._ops = list(ops)
        self._predicats = list(predicats)
        self._inits = tuple(inits)
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        ops = [(nom, src) for nom, src in self._ops if nom != g]
        preds = [(nom, src) for nom, src in self._predicats if nom != g]
        if not ops or not preds:
            return []
        cands = []
        for init in self._inits:
            for opn, opsrc in ops:
                for pn, psrc in preds:
                    pre = "".join(dict.fromkeys([opsrc, psrc]))
                    cands.append(
                        f"{pre}def {g}(*args, **kwargs):\n"
                        f"    acc = {init}\n"
                        f"    for _x in args[0]:\n"
                        f"        if {pn}(_x):\n            break\n"
                        f"        acc = {opn}(acc, _x)\n"
                        f"    return acc\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._ops) + len(self._predicats)


class GenerateurRecurrence:
    """
    CONTRÔLE — RÉCURRENCE à DEUX ÉTATS sur un compte (ce que le pli/boucle ne font pas : l'état MULTIPLE).

    Le pli et la boucle bornée n'ont qu'UN accumulateur. Beaucoup d'algorithmes ont DEUX états couplés qui
    se mettent à jour ensemble (fibonacci, Lucas, …). On l'admet en UN SEUL schéma figé (suite du « un schéma
    à la fois », comme la boucle) — itération BORNÉE par un compte (pas de `while`, pas de non-terminaison) :

        a, b = {i0}, {i1}
        for _ in range(args[0]):
            a, b = b, {op}(a, b)        # op CONFIRMÉE
        return {a|b}

    Borné (|ops|×|inits|²×2), honnête (sans op, rien). fibonacci = op=add, inits=(0,1), return a ; Lucas =
    inits=(2,1). Un seul schéma de récurrence linéaire à 2 états — le `while`/condition viendra après (séparé).
    """

    INITS = (0, 1, 2)

    def __init__(self, ops, inits=None, seed: int = 0):
        self._ops = list(ops)
        self._inits = tuple(inits) if inits is not None else self.INITS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        ops = [(nom, src) for nom, src in self._ops if nom != g]
        if not ops:
            return []
        cands = []
        for opn, opsrc in ops:
            for i0 in self._inits:
                for i1 in self._inits:
                    for ret in ("a", "b"):
                        cands.append(
                            f"{opsrc}def {g}(*args, **kwargs):\n"
                            f"    a, b = {i0}, {i1}\n"
                            f"    for _ in range(args[0]):\n"
                            f"        a, b = b, {opn}(a, b)\n"
                            f"    return {ret}\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._ops)


class GenerateurWhile:
    """
    CONTRÔLE — boucle WHILE pilotée par une CONDITION (ce que la récurrence/boucle, comptées, ne font pas).

    gcd & co. ne bouclent pas sur un compte ni une séquence : ils itèrent TANT QU'une condition tient. C'est
    le terrain le plus explosif (non-terminaison). On le cadre DEUX fois : (1) UN schéma figé, (2) le JUGE
    lui-même — une boucle qui ne termine pas dépasse le timeout du sandbox -> écartée par la RÉALITÉ, pas par
    nous. Schéma (Euclid-classe) :

        a, b = args[0], args[1]
        while b:                     # condition = vérité du 2e état (0 -> stop)
            a, b = b, {op}(a, b)     # op CONFIRMÉE
        return {a|b}

    Borné (|ops|×2), honnête (sans op, rien). gcd = op=mod (`a, b = b, a % b`), return a. Les ops qui font
    diverger (add, mul) -> timeout -> rejetées par le juge. Un seul schéma ; la condition générale (prédicat
    confirmé) sera un raffinement ultérieur.
    """

    def __init__(self, ops, seed: int = 0):
        self._ops = list(ops)
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        ops = [(nom, src) for nom, src in self._ops if nom != g]
        if not ops:
            return []
        cands = []
        for opn, opsrc in ops:
            for ret in ("a", "b"):
                cands.append(
                    f"{opsrc}def {g}(*args, **kwargs):\n"
                    f"    a, b = args[0], args[1]\n"
                    f"    while b:\n"
                    f"        a, b = b, {opn}(a, b)\n"
                    f"    return {ret}\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._ops)


class GenerateurMapRepli:
    """
    MAP-PUIS-REPLI — replier un AGRÉGATEUR sur une séquence TRANSFORMÉE par une primitive (le map-reduce).

    Le pli replie une op binaire sur la séquence BRUTE ; la fusion prend un élément du STORE. Aucun ne replie
    sur `f(x)` où f est une PRIMITIVE appelable confirmée (ex. `sum(cube(x) for x in xs)`). On l'admet en un
    schéma figé : `AGG(prim(x) for x in args[0])` — AGG agrégateur universel (sum/max/min), prim CONFIRMÉE.

    Borné (|aggs|×|prims|), honnête (sans la primitive, rien). C'est le pont map-reduce : transformer chaque
    élément par un atome (éventuellement INVENTÉ) puis replier. Compose l'existant, ne conjure rien.
    """

    AGGS = ("sum", "max", "min")

    def __init__(self, primitives, aggs=None, seed: int = 0):
        self._prims = list(primitives)
        self._aggs = tuple(aggs) if aggs is not None else self.AGGS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        prims = [(nom, src) for nom, src in self._prims if nom != g]
        cands = []
        for agg in self._aggs:
            for pn, ps in prims:
                cands.append(f"{ps}def {g}(*args, **kwargs):\n    return {agg}({pn}(x) for x in args[0])\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._prims)


class GenerateurInvariant:
    """
    PRÉDICAT STRUCTUREL — « x est-il INVARIANT sous une primitive ? » : `x == prim(x)` (famille B).

    Le branchement teste des prédicats donnés ; il ne sait pas comparer une entrée à sa PROPRE structure
    transformée. Beaucoup de « is_X » sont exactement ça : x est un POINT FIXE de prim. Un schéma figé :

        return args[0] == {prim}(args[0])     # prim CONFIRMÉE

    Un seul schéma, DEUX classes d'un coup : `is_palindrome` = invariant sous `inverse_chaine` (s == s[::-1]) ;
    `is_sorted` = invariant sous `trie` (xs == sorted(xs)). Borné (|prims|), honnête (sans la primitive, rien).
    """

    def __init__(self, primitives, seed: int = 0):
        self._prims = list(primitives)
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        prims = [(nom, src) for nom, src in self._prims if nom != g]
        cands = [f"{ps}def {g}(*args, **kwargs):\n    return args[0] == {pn}(args[0])\n"
                 for pn, ps in prims]
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._prims)


class GenerateurJointureProfonde:
    """
    JOINTURE PROFONDE (ciblée) — joindre deux sous-résultats PROFONDS par une op, en DEUX familles CIBLÉES (au lieu
    d'un produit croisé obèse `côtés × côtés` qui explose en O(prims⁴)) :

      A. deux AGRÉGATS de liste : `op(AGG1(args[0]), AGG2(args[0]))` — ex. max_minus_min = sub(max, min).
      B. transforms POSITIONNELS sur premier/dernier, éventuellement ASYMÉTRIQUES : `op(f(args[0][0]), g(args[0][-1]))`
         (f, g ∈ {identité} ∪ primitives, indépendants) — ex. produit_carres_bouts = mul(carre(xs[0]), carre(xs[-1])),
         ou asymétrique mul(carre(xs[0]), double(xs[-1])).

    Lean ET complète : couvre agrégats-pairs + jointures positionnelles (sym. ET asym.) en standalone, à coût
    O(prims²) (pas O(prims⁴)). La profondeur ARBITRAIRE (deux pipelines quelconques sur la liste entière) reste
    déléguée à la VERTICALITÉ (le compounding verse les sous-pipelines). op CONFIRMÉE. Honnête (sans la brique, rien).
    """

    AGGS = ("max", "min", "sum")
    POSITIONS = ("args[0][0]", "args[0][-1]")   # premier, dernier (positions intégrées)

    def __init__(self, primitives, ops, aggs=None, seed: int = 0):
        self._prims = list(primitives)
        self._ops = list(ops)
        self._aggs = tuple(aggs) if aggs is not None else self.AGGS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        prims = [(nom, src) for nom, src in self._prims if nom != g]
        ops = [(nom, src) for nom, src in self._ops if nom != g]
        if not ops:
            return []
        p0, p1 = self.POSITIONS
        cands = []
        for opn, opsrc in ops:
            # A. deux agrégats DISTINCTS de la liste
            for a1 in self._aggs:
                for a2 in self._aggs:
                    if a1 == a2:
                        continue
                    cands.append(f"{opsrc}def {g}(*args, **kwargs):\n    return {opn}({a1}(args[0]), {a2}(args[0]))\n")
            # B. transforms positionnels sur premier/dernier (f, g indépendants -> symétriques ET asymétriques).
            #    transform = (nom|None, source) ; None = identité (la position brute).
            transforms = [(None, "")] + prims
            for fn, fsrc in transforms:
                for hn, hsrc in transforms:
                    gauche = p0 if fn is None else f"{fn}({p0})"
                    droite = p1 if hn is None else f"{hn}({p1})"
                    srcs = "".join(dict.fromkeys([opsrc] + [s for s in (fsrc, hsrc) if s]))
                    cands.append(f"{srcs}def {g}(*args, **kwargs):\n    return {opn}({gauche}, {droite})\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._prims) + len(self._ops)


class GenerateurPredicatMesures:
    """
    PRÉDICAT STRUCTUREL sur des MESURES de x — `m1(x) CMP m2(x)` (renvoie un booléen).

    Le branchement teste des prédicats DONNÉS ; il ne compare pas deux PROPRIÉTÉS agrégées de l'entrée.
    Beaucoup de validations sont ça : `all_unique` = len(x) == len(set(x)) ; « tous identiques » = len(set(x)) == 1 ;
    etc. Un schéma : comparer deux mesures (len, len∘set, sum, max, min) par un opérateur. Borné, honnête
    (mesures universelles ; le juge écarte les comparaisons qui plantent — ex. max sur autre chose).
    """

    MESURES = ("len(args[0])", "len(set(args[0]))", "sum(args[0])", "max(args[0])", "min(args[0])")
    CMPS = ("==", "!=", ">", "<", ">=", "<=")
    # TAUTOLOGIES indépendantes du domaine (toujours vraies / fausses / redondantes avec ==) : len >= len(set)
    # toujours vrai (set ⊆), len < len(set) jamais, len <= len(set) ⟺ ==  ; idem max/min. Élaguées (poids mort).
    TAUTOLOGIES = frozenset({
        ("len(args[0])", ">=", "len(set(args[0]))"), ("len(args[0])", "<", "len(set(args[0]))"),
        ("len(args[0])", "<=", "len(set(args[0]))"),
        ("max(args[0])", ">=", "min(args[0])"), ("max(args[0])", "<", "min(args[0])"),
        ("max(args[0])", "<=", "min(args[0])"),
    })

    def __init__(self, mesures=None, cmps=None, seed: int = 0):
        self._mesures = tuple(mesures) if mesures is not None else self.MESURES
        self._cmps = tuple(cmps) if cmps is not None else self.CMPS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        # PAIRES CANONIQUES (i < j) : `m1 CMP m2` sur les 6 comparateurs couvre déjà le miroir `m2 CMP m1`
        # (b > a ≡ a < b…). Émettre les deux ordres = 60 doublons sémantiques. On n'émet que l'ordre canonique.
        for i in range(len(self._mesures)):
            for j in range(i + 1, len(self._mesures)):
                m1, m2 = self._mesures[i], self._mesures[j]
                for cmp in self._cmps:
                    if (m1, cmp, m2) in self.TAUTOLOGIES:    # tautologie/redondance -> candidat mort
                        continue
                    cands.append(f"def {g}(*args, **kwargs):\n    return {m1} {cmp} {m2}\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._mesures)


class GenerateurPositionnel:
    """
    LOGIQUE POSITIONNELLE — combiner les agrégats des positions PAIRES vs IMPAIRES : `op(AGG(xs[::2]), AGG(xs[1::2]))`.

    Rien dans le moteur ne dépend de l'INDICE/de la parité de position. Un schéma figé qui l'admet (sur slices
    pair/impair) : `alternating_sum` = sum(xs[::2]) - sum(xs[1::2]) (somme positions paires - impaires). AGG ∈
    sum/max/min, op CONFIRMÉE. Borné, honnête (sans op, rien).
    """

    AGGS = ("sum", "max", "min")

    def __init__(self, ops, aggs=None, seed: int = 0):
        self._ops = list(ops)
        self._aggs = tuple(aggs) if aggs is not None else self.AGGS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        ops = [(nom, src) for nom, src in self._ops if nom != g]
        if not ops:
            return []
        cands = []
        for opn, opsrc in ops:
            for agg in self._aggs:
                cands.append(f"{opsrc}def {g}(*args, **kwargs):\n"
                             f"    return {opn}({agg}(args[0][::2]), {agg}(args[0][1::2]))\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._ops)


class GenerateurMots:
    """
    PARSING CHAÎNE — `SEP.join(transform(args[0].split()))` : découper en mots, transformer la liste, rejoindre.

    Le substrat fait des méthodes UNAIRES (`.upper()`) ; il ne sait pas découper-transformer-rejoindre. Un schéma
    figé sur les MOTS : `' '.join(args[0].split()[::-1])` (inverser l'ordre des mots), ou `sorted` (trier les mots).
    Borné (|seps|×transforms), honnête (sur une chaîne de mots). reverse_words = ' '.join(s.split()[::-1]).
    """

    SEPS = ("' '",)

    def __init__(self, seps=None, seed: int = 0):
        self._seps = tuple(seps) if seps is not None else self.SEPS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for sep in self._seps:
            for corps in (f"{sep}.join(args[0].split()[::-1])",      # mots inversés
                          f"{sep}.join(sorted(args[0].split()))",    # mots triés
                          f"{sep}.join(args[0].split())"):           # normaliser les espaces
                cands.append(f"def {g}(*args, **kwargs):\n    return {corps}\n")
        cands.append(f"def {g}(*args, **kwargs):\n    return len(args[0].split())\n")  # compte de mots (gap_probe 8)
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._seps)


class GenerateurMultiPasse:
    """
    MULTI-PASSE — filtrer/replier selon un AGRÉGAT du TOUT (DEUX passes : agréger la liste, puis filtrer chaque
    élément PAR RAPPORT à cet agrégat).

    La fusion filtre par un prédicat SIMPLE (x > 0) ; elle ne peut pas filtrer par une mesure de la liste ENTIÈRE
    (`x > moyenne(xs)`). C'est une 2e passe : le filtre référence un agrégat calculé sur tout l'input. Un schéma :
    `REDUC(x for x in args[0] if x CMP AGG(args[0]))` avec AGG ∈ {moyenne, max, min}, CMP ∈ {>,<,>=,<=}, REDUC ∈
    {compter, sommer, lister}. au_dessus_moyenne = sum(1 for x in xs if x > sum(xs)/len(xs)). Borné, honnête.
    """

    AGGS = ("sum(args[0]) / len(args[0])", "max(args[0])", "min(args[0])")
    CMPS = (">", "<", ">=", "<=")
    REDUCS = ("sum(1 for x in args[0] if {C})", "sum(x for x in args[0] if {C})", "[x for x in args[0] if {C}]")
    # filtres DÉGÉNÉRÉS (cohérence avec GenerateurComprehensionGenerale) : toujours-vides (>max, <min) ou
    # toujours-vrais = sans-filtre (>=min, <=max). On ne les émet jamais (candidats morts / inutiles).
    DEGENERES = frozenset({(">", "max(args[0])"), ("<", "min(args[0])"),
                           (">=", "min(args[0])"), ("<=", "max(args[0])")})

    def __init__(self, aggs=None, cmps=None, seed: int = 0):
        self._aggs = tuple(aggs) if aggs is not None else self.AGGS
        self._cmps = tuple(cmps) if cmps is not None else self.CMPS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for agg in self._aggs:
            for cmp in self._cmps:
                if (cmp, agg) in self.DEGENERES:        # élagage des filtres morts/redondants
                    continue
                cond = f"x {cmp} _m"                     # agrégat HOISTÉ dans _m -> O(n) au lieu de O(n²)
                for reduc in self.REDUCS:
                    cands.append(f"def {g}(*args, **kwargs):\n    _m = {agg}\n    return {reduc.replace('{C}', cond)}\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._aggs)


class GenerateurAdjacence:
    """
    ADJACENCE — agréger une relation entre éléments VOISINS : `AGG(args[0][i] REL args[0][i-1] for i in 1..len)`.

    Rien ne compare des éléments ADJACENTS (xs[i], xs[i-1]). Beaucoup de tâches sont ça : `count_transitions` =
    sum(xs[i] != xs[i-1]), `est_croissant` = all(xs[i] > xs[i-1]). Un schéma : AGG ∈ {all, any, sum}, REL ∈
    comparaisons. Borné, honnête.
    """

    AGGS = ("all", "any", "sum")
    RELS = (">", "<", ">=", "<=", "==", "!=")

    def __init__(self, aggs=None, rels=None, seed: int = 0):
        self._aggs = tuple(aggs) if aggs is not None else self.AGGS
        self._rels = tuple(rels) if rels is not None else self.RELS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for agg in self._aggs:
            for rel in self._rels:
                cands.append(
                    f"def {g}(*args, **kwargs):\n"
                    f"    return {agg}(args[0][i] {rel} args[0][i - 1] for i in range(1, len(args[0])))\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._aggs)


class GenerateurImbrique:
    """
    DONNÉES IMBRIQUÉES — itérer DEUX niveaux (liste de listes) : `REDUC(elt for x in args[0] for y in x)`.

    Tout le moteur itère UN niveau (séquence plate). Les données imbriquées (listes de listes) lui échappent.
    Un schéma : double boucle de compréhension, élément `y` (ou `prim(y)`), replié par REDUC ∈ {lister, sommer,
    max, min}. flatten = [y for x in xs for y in x] ; sum_nested = sum(y for x in xs for y in x). Borné, honnête.
    """

    REDUCS = ("[{E} for x in args[0] for y in x]", "sum({E} for x in args[0] for y in x)",
              "max({E} for x in args[0] for y in x)", "min({E} for x in args[0] for y in x)")

    def __init__(self, primitives=None, seed: int = 0):
        self._prims = list(primitives or [])
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        prims = [(nom, src) for nom, src in self._prims if nom != g]
        cands = []
        for reduc in self.REDUCS:
            cands.append(f"def {g}(*args, **kwargs):\n    return {reduc.replace('{E}', 'y')}\n")  # élément brut
            for pn, ps in prims:                                                                  # élément transformé
                cands.append(f"{ps}def {g}(*args, **kwargs):\n    return {reduc.replace('{E}', f'{pn}(y)')}\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 1 + len(self._prims)


class GenerateurDictAccumulateur:
    """
    DICT comme ACCUMULATEUR — bâtir un dictionnaire clé -> mesure : `{k: REDUC(k) for k in set(args[0])}`.

    Le moteur produit des scalaires/listes, pas des DICTS dont la valeur dépend de la clé et du tout. Un schéma :
    `{x: args[0].count(x) for x in set(args[0])}` (compter les occurrences) — word_count. (Aussi `.index` = 1re
    position.) Borné, honnête.
    """

    VALEURS = ("args[0].count(x)", "args[0].index(x)")
    # FORMES O(n) en UNE passe (accumulateur) par valeur connue — la dict-comp `{x: args[0].count(x) ...}` est
    # O(n²) (count/index re-parcourt la liste PAR clé ; pire cas tous distincts -> ×2000+, peut timeout le juge).
    # Repli sur la dict-comp d'origine pour toute valeur CUSTOM inconnue (rare). Résultat identique.
    _OPTIM = {
        "args[0].count(x)": "    c = {}\n    for x in args[0]:\n        c[x] = c.get(x, 0) + 1\n    return c\n",
        "args[0].index(x)": "    c = {}\n    for i, x in enumerate(args[0]):\n        if x not in c:\n            c[x] = i\n    return c\n",
    }

    def __init__(self, valeurs=None, seed: int = 0):
        self._valeurs = tuple(valeurs) if valeurs is not None else self.VALEURS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{self._OPTIM[v]}" if v in self._OPTIM
                 else f"def {g}(*args, **kwargs):\n    return {{x: {v} for x in set(args[0])}}\n"
                 for v in self._valeurs]
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._valeurs)


class GenerateurGroupBy:
    """
    GROUPER + agréger PAR CLÉ — `{k: AGG(p[1] for p in args[0] if p[0] == k) for k in set(p[0] for p in args[0])}`.

    Grouper des paires (clé, valeur) par clé et replier les valeurs de chaque groupe : le pattern group-by, que
    rien ne couvrait. AGG ∈ {max, min, sum}. max_par_cle = max ; somme_par_cle = sum. Borné, honnête.
    """

    AGGS = ("max", "min", "sum")
    # COMBINE O(n) en UNE passe par AGG connu — la dict-comp `{k: AGG(... if p[0]==k) ...}` est O(n²) (re-filtre
    # toutes les paires PAR clé ; pire cas clés distinctes -> ×6000+, peut timeout le juge). Repli sur la dict-comp
    # pour tout AGG custom. Résultat identique (dict comparé sans ordre).
    _COMBINE = {
        "max": "v if k not in d else (d[k] if d[k] >= v else v)",
        "min": "v if k not in d else (d[k] if d[k] <= v else v)",
        "sum": "d.get(k, 0) + v",
    }

    def __init__(self, aggs=None, seed: int = 0):
        self._aggs = tuple(aggs) if aggs is not None else self.AGGS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for agg in self._aggs:
            if agg in self._COMBINE:
                cands.append(f"def {g}(*args, **kwargs):\n    d = {{}}\n    for k, v in args[0]:\n"
                             f"        d[k] = {self._COMBINE[agg]}\n    return d\n")
            else:
                cands.append(f"def {g}(*args, **kwargs):\n    return "
                             f"{{k: {agg}((p[1] for p in args[0] if p[0] == k)) for k in set((p[0] for p in args[0]))}}\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._aggs)


class GenerateurComprehensionGenerale:
    """
    COMPRÉHENSION GÉNÉRALE — transform + filtre(agrégat du TOUT) + reduce, dans UNE compréhension unifiée :

        REDUC(f(x) for x in args[0] [if x CMP AGG(args[0])])

    f ∈ {identité} ∪ primitives confirmées ; REDUC ∈ {sum, max, min, list, count(=sum(1…))} ; le filtre est
    OPTIONNEL et porte sur un agrégat de la liste ENTIÈRE (CMP ∈ {>,<,>=,<=}, AGG ∈ {moyenne, max, min}).

    Débloque les composites « transform + filtre + reduce » qu'aucune brique ne couvrait d'un seul tenant —
    ex. somme des cubes AU-DESSUS de la moyenne : sum(cube(x) for x in xs if x > sum(xs)/len(xs)). map-repli
    transforme+replie mais sans filtre ; multipasse filtre+replie mais sans transform : le composite des deux
    leur échappait.

    Ce schéma SUBSUME `map-repli` (REDUC(prim(x)), filtre absent) ET `multipasse` (REDUC(x|1), f=identité) →
    candidat naturel à la DÉDUPLICATION (passe d'excellence : 1 brique générale pour 2). Borné (|REDUC| ·
    (1+|prims|) · (1+|CMP|·|AGG|)), honnête (transform confirmée ; le juge écarte max/min sur séquence vide).

    GRADIENT DE COÛT (excellence de la dédup) : `propose` émet les candidats en TIERS du moins cher au plus
    cher — T0 identité/sans-filtre, T1 transform/sans-filtre (= map-repli), T2 identité/filtre (= multipasse),
    T3 transform+filtre (le composite neuf) — mélangés DANS chaque tier. Ainsi, en absorbant map-repli et
    multipasse, l'orchestrateur retombe sur la solution simple dans le PRÉFIXE cheap (coût ≤ standalone à un
    facteur constant près, le `list`-reduc en plus), et ne paie le surcoût combinatoire que si la tâche l'exige.
    (En régime chaud, le `Predicteur` raffine cet ordre ; les tiers sont le prior à froid.)
    """

    AGGS = ("sum(args[0]) / len(args[0])", "max(args[0])", "min(args[0])")
    CMPS = (">", "<", ">=", "<=")
    # FILTRES DÉGÉNÉRÉS (élagage chirurgical : 0 perte de couverture, -ressource) — paires (CMP, AGG) soit
    # TOUJOURS VIDES (aucun élément ne les satisfait), soit TOUJOURS VRAIES (= le cas sans-filtre, déjà en tier
    # cheap). On ne les émet jamais : candidats morts ou redondants.
    DEGENERES = frozenset({
        (">",  "max(args[0])"),   # x > max : jamais (vide)
        ("<",  "min(args[0])"),   # x < min : jamais (vide)
        (">=", "min(args[0])"),   # x >= min : toujours (= sans filtre)
        ("<=", "max(args[0])"),   # x <= max : toujours (= sans filtre)
    })
    # REDUC : (utilise_element, gabarit) ; {E} = élément (f(x) ou x), {C} = clause de filtre ('' ou ' if …').
    REDUCS = (
        (True,  "sum({E} for x in args[0]{C})"),
        (True,  "max({E} for x in args[0]{C})"),
        (True,  "min({E} for x in args[0]{C})"),
        (True,  "[{E} for x in args[0]{C}]"),
        (False, "sum(1 for x in args[0]{C})"),   # comptage : élément ignoré (subsume multipasse-compter)
    )

    def __init__(self, primitives=None, aggs=None, cmps=None, seed: int = 0, composite_dabord: bool = False):
        self._prims = list(primitives or [])
        self._aggs = tuple(aggs) if aggs is not None else self.AGGS
        self._cmps = tuple(cmps) if cmps is not None else self.CMPS
        self._seed = seed
        # composite_dabord : ordre des tiers. False = gradient cheap->cher (T0->T3) ; True = T3 d'abord (le
        # transform+filtre, RAISON D'ÊTRE du noyau). Pertinent quand le noyau est l'étage FALLBACK (dernier) :
        # il n'est atteint que pour le NEUF (composites T3), donc émettre T3 d'abord minimise le coût quand il
        # est réellement utile. À trancher PAR LE RÉEL (mesure), pas par opinion. Défaut prudent = gradient.
        self._composite_dabord = composite_dabord

    def _emet(self, g, elements, clauses):
        """Tous les corps pour un sous-ensemble (éléments × clauses) — un TIER de coût.
        clauses = liste de (cond, prefixe) : cond = texte du filtre dans la compréhension ('' ou ' if x CMP _m') ;
        prefixe = pré-calcul HOISTÉ de l'agrégat ('' ou '_m = AGG\\n    ') -> l'agrégat est calculé UNE FOIS,
        pas par élément. O(n) au lieu de O(n²), résultat identique (l'agrégat est constant sur la liste)."""
        out = []
        for utilise_elt, gab in self.REDUCS:
            elts = elements if utilise_elt else [("x", "")]   # comptage : élément ignoré -> 1 variante
            for ex, esrc in elts:
                for cond, prefixe in clauses:
                    corps = gab.replace("{E}", ex).replace("{C}", cond)
                    out.append(f"{esrc}def {g}(*args, **kwargs):\n    {prefixe}return {corps}\n")
        return out

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        prims = [(nom, src) for nom, src in self._prims if nom != g]
        id_elt = [("x", "")]                                              # élément identité
        tr_elt = [(f"{pn}(x)", ps) for pn, ps in prims]                  # éléments transformés (primitives)
        sans_filtre = [("", "")]                              # (cond, prefixe) ; pas de filtre -> pas de pré-calcul
        avec_filtre = [(f" if x {cmp} _m", f"_m = {agg}\n    ")   # agrégat HOISTÉ dans _m (calculé 1 fois)
                       for cmp in self._cmps for agg in self._aggs
                       if (cmp, agg) not in self.DEGENERES]   # élagage des filtres morts/redondants
        # TIERS du moins cher au plus cher (gradient de coût). T0 subsume le trivial, T1 = map-repli,
        # T2 = multipasse, T3 = transform+filtre (le composite que la fusion des deux ouvre).
        tiers = [
            self._emet(g, id_elt, sans_filtre),   # T0 : identité, sans filtre
            self._emet(g, tr_elt, sans_filtre),   # T1 : transform, sans filtre  (= map-repli)
            self._emet(g, id_elt, avec_filtre),   # T2 : identité, filtre         (= multipasse)
            self._emet(g, tr_elt, avec_filtre),   # T3 : transform + filtre       (composite neuf)
        ]
        if self._composite_dabord:                # fallback : le NEUF (T3) d'abord, le reste en repli
            tiers = tiers[::-1]
        rng = random.Random(f"{self._seed}|{prompt}")
        cands, vus = [], set()
        for tier in tiers:                        # ordre des tiers = gradient ; mélange DANS le tier
            rng.shuffle(tier)
            for c in tier:
                if c not in vus:                  # dé-dup en gardant le tier le moins cher (ex. comptage en T0)
                    vus.add(c)
                    cands.append(c)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._prims)


class GenerateurFenetre:
    """
    FENÊTRE GLISSANTE — agrégat sur les sous-séquences CONTIGUËS de taille k :

        REDUC(AGG(args[0][i:i+k]) for i in range(len(args[0]) - k + 1))   avec k = args[1]

    REDUC ∈ {max, min, sum, list} (replie les agrégats de fenêtre) ; AGG ∈ {sum, max, min} (agrège DANS la
    fenêtre). k vient de l'ENTRÉE (args[1]) -> la brique est paramétrée par la taille de fenêtre, pas figée.

    NOUVEAU TERRITOIRE : aucune brique ne découpe de sous-séquence contiguë. `positionnel` strie par parité
    (xs[::2]) ; `adjacence` agrège des paires voisines (i, i-1) ; `multipasse`/`comprehension-generale` replient
    sur des ÉLÉMENTS (filtrés par un agrégat du tout), jamais sur des TRANCHES. max_window = max des sommes de
    fenêtre = max(sum(xs[i:i+k]) for i in …).

    Borné (|REDUC|·|AGG| - dégénérés = 10), honnête (que des candidats fenêtre ; k pris à l'entrée). k est HOISTÉ
    dans `_k` (lu une fois). DÉGÉNÉRÉS élagués (tautologies vs un étage plus simple) : max∘max et min∘min — toute
    valeur appartient à au moins une fenêtre (k ≤ len), donc max des max-de-fenêtre = max(xs), min des min = min(xs).
    """

    AGGS = ("sum", "max", "min")        # agrégat DANS la fenêtre
    REDUCS = ("max", "min", "sum")      # repli des agrégats de fenêtre (+ `list` traité à part)
    # (REDUC, AGG) tautologiques = un étage plus simple les couvre déjà -> jamais émis.
    DEGENERES = frozenset({("max", "max"), ("min", "min")})

    def __init__(self, aggs=None, seed: int = 0):
        self._aggs = tuple(aggs) if aggs is not None else self.AGGS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for agg in self._aggs:
            fenetre = f"{agg}(args[0][i:i+_k])"
            gen = f"({fenetre} for i in range(len(args[0]) - _k + 1))"
            for reduc in (*self.REDUCS, "list"):
                if (reduc, agg) in self.DEGENERES:
                    continue
                corps = f"[{fenetre} for i in range(len(args[0]) - _k + 1)]" if reduc == "list" else f"{reduc}{gen}"
                cands.append(f"def {g}(*args, **kwargs):\n    _k = args[1]\n    return {corps}\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._aggs)


class GenerateurMatrice2D:
    """
    MATRICE 2D — opérations STRUCTURELLES sur une liste de listes (réindexation croisée), en deux familles :

      • AXE      : `[AGG(ligne) for ligne in AXE(args[0])]`  — AXE ∈ {lignes = args[0], colonnes = zip(*args[0])},
                   AGG ∈ {sum, max, min, list}. `list`∘colonnes = TRANSPOSE ; `sum`∘lignes = sommes de lignes ;
                   `max`∘colonnes = max par colonne, etc.
      • DIAGONALE: `REDUC(args[0][i][IDX] for i in range(len(args[0])))` — IDX ∈ {i (principale), len-1-i (anti)},
                   REDUC ∈ {sum, max, min, list}. `sum`∘principale = matrix_diag_sum ; `list` = extraire la diagonale.

    NOUVEAU TERRITOIRE : aucune brique ne réindexe en 2D. `imbrique` APLATIT (REDUC(elt for x for y)) → un scalaire ou
    une liste à plat, jamais une transposée ni une diagonale ni un agrégat PAR colonne. Borné (7 axe + 8 diag = 15),
    honnête (que des formes 2D). DÉGÉNÉRÉ élagué : `[list(ligne) for ligne in args[0]]` = identité (copie de m).
    """

    AGGS = ("sum", "max", "min")        # agrégat par ligne / colonne (+ `list` = pas d'agrégat -> transpose/copie)
    REDUCS_DIAG = ("sum", "max", "min")  # repli de la diagonale (+ `list` = extraire la diagonale)
    # EXTENSION 2026-06-19 (5ᵉ vague) : transformations 2D fermées que les axes/diagonales ne couvrent pas —
    # rotation 90° horaire (zip des lignes inversées) et test de SYMÉTRIE (m == transposée).
    EXTRA = (("rotation90", "[list(_r) for _r in zip(*args[0][::-1])]"),
             ("est_symetrique",
              "all(args[0][_i][_j] == args[0][_j][_i] for _i in range(len(args[0])) for _j in range(len(args[0])))"),
             ("matmul",
              "[[sum(_a * _b for _a, _b in zip(_row, _col)) for _col in zip(*args[1])] for _row in args[0]]"),
             # somme des DEUX diagonales sans double-compter le centre (n impair) — gap_probe 31ᵉ vague.
             ("matrix_diagonal_sum",
              "sum(args[0][_i][_i] for _i in range(len(args[0])))"
              " + sum(args[0][_i][len(args[0]) - 1 - _i] for _i in range(len(args[0]))"
              " if _i != len(args[0]) - 1 - _i)"),
             # LUCKY NUMBERS : min de sa ligne ET max de sa colonne — gap_probe 38ᵉ vague.
             ("lucky_numbers_matrix",
              "[_v for _v in (min(_r) for _r in args[0]) if _v in {max(_c) for _c in zip(*args[0])}]"),
             # TOEPLITZ : toute diagonale (haut-gauche -> bas-droite) constante — gap_probe 38ᵉ vague.
             ("toeplitz_matrix",
              "all(args[0][_i][_j] == args[0][_i - 1][_j - 1]"
              " for _i in range(1, len(args[0])) for _j in range(1, len(args[0][0])))"),
             # FLIP & INVERT : inverser chaque ligne puis complémenter les bits — gap_probe 38ᵉ vague.
             ("flip_and_invert_image",
              "[[1 - _x for _x in _row[::-1]] for _row in args[0]]"),
             # SET ZEROES : toute case d'une ligne/colonne contenant un 0 passe à 0 — gap_probe 43ᵉ vague.
             ("set_zeroes",
              "(lambda _m, _R, _C: [[0 if any(_m[_i][_y] == 0 for _y in range(_C))"
              " or any(_m[_x][_j] == 0 for _x in range(_R)) else _m[_i][_j] for _j in range(_C)]"
              " for _i in range(_R)])(args[0], len(args[0]), len(args[0][0]))"),
             # DIAGONAL TRAVERSE : parcours en diagonales alternées (zig-zag) — gap_probe 43ᵉ vague.
             ("diagonal_traverse",
              "(lambda _m, _R, _C: [_v for _d in range(_R + _C - 1) for _v in"
              " ([_m[_i][_d - _i] for _i in range(_R) if 0 <= _d - _i < _C][::(-1 if _d % 2 == 0 else 1)])])"
              "(args[0], len(args[0]), len(args[0][0]))"))

    def __init__(self, aggs=None, seed: int = 0):
        self._aggs = tuple(aggs) if aggs is not None else self.AGGS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for axe_src, axe_nom in (("args[0]", "lignes"), ("zip(*args[0])", "colonnes")):
            for agg in (*self._aggs, "list"):
                if axe_nom == "lignes" and agg == "list":
                    continue                          # [list(ligne) for ligne in m] = identité (dégénéré)
                ligne = "list(_l)" if agg == "list" else f"{agg}(_l)"
                cands.append(f"def {g}(*args, **kwargs):\n    return [{ligne} for _l in {axe_src}]\n")
        for idx, idx_nom in (("i", "principale"), ("len(args[0]) - 1 - i", "anti")):
            for reduc in (*self.REDUCS_DIAG, "list"):
                diag = f"args[0][i][{idx}] for i in range(len(args[0]))"
                corps = f"[{diag}]" if reduc == "list" else f"{reduc}({diag})"
                cands.append(f"def {g}(*args, **kwargs):\n    return {corps}\n")
        for _, expr in self.EXTRA:
            cands.append(f"def {g}(*args, **kwargs):\n    return {expr}\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._aggs)


class GenerateurRepetition:
    """
    RÉPÉTITION COMPTÉE — appliquer une op binaire `args[1]` fois à un accumulateur, sur l'opérande `args[0]` :

        acc = INIT ; for _ in range(args[1]): acc = op(acc, args[0]) ; return acc

    (op, INIT) ∈ {(`acc * args[0]`, 1)  -> puissance a^b,  (`acc + args[0]`, 0)  -> produit répété a*b}.

    NOUVEAU : le COMPTE d'itérations vient d'une 2ᵉ ENTRÉE (args[1]), pas d'une structure ni d'un compte interne.
    `recurrence`/`while` itèrent sur UN seul argument (compte interne) ; `multi-entrée` bâtit des arbres d'ops de
    profondeur BORNÉE sur les args bruts (il ne peut pas faire b multiplications quand b est une valeur runtime) ;
    `pli` replie sur une SÉQUENCE dérivée d'un arg. b=0 -> INIT (a^0=1, a*0=0) : domaine cohérent. Borné (2), honnête.
    """

    SCHEMAS = (("acc * args[0]", "1"), ("acc + args[0]", "0"))   # (op, init) : puissance, produit répété

    def __init__(self, schemas=None, seed: int = 0):
        self._schemas = tuple(schemas) if schemas is not None else self.SCHEMAS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for op, init in self._schemas:
            cands.append(f"def {g}(*args, **kwargs):\n    acc = {init}\n    for _ in range(args[1]):\n"
                         f"        acc = {op}\n    return acc\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._schemas)


class GenerateurIndexOrdonne:
    """
    INDEXATION ORDONNÉE — accès piloté par une 2ᵉ entrée sur une liste, en deux familles :

      • RANG    : `sorted(args[0])[IDX]` — IDX ∈ {args[1]-1 (k-ième plus petit, 1-indexé), -args[1] (k-ième plus
                  grand), args[1] (n-ième, 0-indexé)}. kth_largest(xs,k) = sorted(xs)[-k].
      • RECHERCHE: recherche DICHOTOMIQUE de args[1] dans la liste triée -> index trouvé, sinon -1 (binary_search).

    NOUVEAU : l'index/la cible vient d'une 2ᵉ ENTRÉE (args[1]). `composition` enchaîne des primitives UNAIRES
    (sorted(xs)[-2] figé) mais ne sait pas indexer par un k RUNTIME ; `multi-entrée` ne trie pas ; aucune brique
    ne fait de dichotomie. Borné (3 rang + 1 recherche = 4), honnête (n'utilise que args[0] trié + args[1]).
    """

    IDX = ("args[1] - 1", "-args[1]", "args[1]")   # k-ième plus petit (1-idx), k-ième plus grand, n-ième (0-idx)

    def __init__(self, idx=None, seed: int = 0):
        self._idx = tuple(idx) if idx is not None else self.IDX
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return sorted(args[0])[{e}]\n" for e in self._idx]
        cands.append(                                                      # recherche dichotomique (cible = args[1])
            f"def {g}(*args, **kwargs):\n    _lo, _hi = 0, len(args[0]) - 1\n"
            f"    while _lo <= _hi:\n        _mid = (_lo + _hi) // 2\n"
            f"        if args[0][_mid] == args[1]:\n            return _mid\n"
            f"        if args[0][_mid] < args[1]:\n            _lo = _mid + 1\n"
            f"        else:\n            _hi = _mid - 1\n    return -1\n")
        cands.append(                          # dichotomie en tableau trié PIVOTÉ (rotated) — gap_probe 46ᵉ vague
            f"def {g}(*args, **kwargs):\n    _ns, _t = args[0], args[1]\n    _lo, _hi = 0, len(_ns) - 1\n"
            f"    while _lo <= _hi:\n        _mid = (_lo + _hi) // 2\n"
            f"        if _ns[_mid] == _t:\n            return _mid\n"
            f"        if _ns[_lo] <= _ns[_mid]:\n"
            f"            if _ns[_lo] <= _t < _ns[_mid]:\n                _hi = _mid - 1\n"
            f"            else:\n                _lo = _mid + 1\n"
            f"        else:\n"
            f"            if _ns[_mid] < _t <= _ns[_hi]:\n                _lo = _mid + 1\n"
            f"            else:\n                _hi = _mid - 1\n    return -1\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._idx)


class GenerateurSousSuite:
    """
    PLUS LONGUE SOUS-SUITE MONOTONE (programmation dynamique O(n²)) — la plus longue sous-suite (NON contiguë)
    où une relation REL tient entre éléments choisis :

        dp[i] = 1 + max(dp[j] for j<i if args[0][j] REL args[0][i]) ; return max(dp)  (0 si vide)

    REL ∈ {<, <=, >, >=}. longest_increasing = `<` (strictement croissante) ; longest_decreasing = `>`.

    NOUVEAU : SOUS-SUITE (saute des éléments), pas un run CONTIGU. `serie` ne mesure que la plus longue suite
    CONSÉCUTIVE (run-length) ; `adjacence` agrège des paires voisines. LIS([1,3,2,4]) = 3 (1,2,4) alors que le run
    croissant contigu max = 2 -> `serie` échoue. Borné (4 relations), honnête (renvoie une longueur DP, pas un len).
    """

    RELS = ("<", "<=", ">", ">=")

    def __init__(self, rels=None, seed: int = 0):
        self._rels = tuple(rels) if rels is not None else self.RELS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for rel in self._rels:
            cands.append(
                f"def {g}(*args, **kwargs):\n    _xs = args[0]\n    if not _xs:\n        return 0\n"
                f"    _dp = [1] * len(_xs)\n    for _i in range(len(_xs)):\n        for _j in range(_i):\n"
                f"            if _xs[_j] {rel} _xs[_i] and _dp[_j] + 1 > _dp[_i]:\n"
                f"                _dp[_i] = _dp[_j] + 1\n    return max(_dp)\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._rels)


class GenerateurPaires:
    """
    PAIRES — quantification ∃ sur tous les COUPLES (i, j), i < j, d'une liste :

        any(args[0][i] OP args[0][j] == args[1] for i in range(len) for j in range(i+1, len))   OP ∈ {+, *, -}

    two_sum_exists(xs, t) = il existe i<j tel que xs[i]+xs[j] == t.

    NOUVEAU : balaie TOUS les couples (double boucle), pas seulement les voisins. `adjacence` n'agrège que des
    paires CONSÉCUTIVES (i, i-1) ; `predicat-mesures` compare des AGRÉGATS du tout, pas des éléments deux à deux.
    i<j strict -> pas d'auto-appariement (un élément seul ne forme pas une paire). Borné (3 ops), honnête.
    """

    OPS = ("+", "*", "-")

    def __init__(self, ops=None, seed: int = 0):
        self._ops = tuple(ops) if ops is not None else self.OPS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return any(args[0][_i] {op} args[0][_j] == args[1]"
                 f" for _i in range(len(args[0])) for _j in range(_i + 1, len(args[0])))\n"
                 for op in self._ops]
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._ops)


class GenerateurRunLength:
    """
    RUN-LENGTH ENCODE — comprimer les runs consécutifs en parcourant avec ÉTAT (élément courant + compteur), et
    CONSTRUIRE une sortie au fil de l'eau. Deux formats :

      • CHAÎNE : 'aaabb' -> 'a3b2'                 (concatène `élément + str(compte)`)
      • PAIRES : 'aaabb' -> [('a',3), ('b',2)]     (accumule des couples (élément, compte))

    NOUVEAU : produit une SORTIE structurée stateful, pas une mesure scalaire. `serie` ne renvoie que la LONGUEUR
    du plus long run ; `mots` découpe/rejoint sur des séparateurs. Borné (2 formats), honnête (vide -> '' / []).
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _corps(self, g, init, maj, fin, ret):
        return (f"def {g}(*args, **kwargs):\n    _s = args[0]\n    if not _s:\n        return {init}\n"
                f"    _out = {init}\n    _prev = _s[0]\n    _cnt = 1\n    for _c in _s[1:]:\n"
                f"        if _c == _prev:\n            _cnt += 1\n        else:\n            {maj}\n"
                f"            _prev = _c\n            _cnt = 1\n    {fin}\n    return {ret}\n")

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [
            self._corps(g, "''", "_out += _prev + str(_cnt)", "_out += _prev + str(_cnt)", "_out"),       # chaîne 'a3b2'
            self._corps(g, "[]", "_out.append((_prev, _cnt))", "_out.append((_prev, _cnt))", "_out"),      # paires
            # DÉCODAGE (inverse) : 'a3b2' -> 'aaabb' (complétude, phase 2)
            f"def {g}(*args, **kwargs):\n    import re\n    return ''.join(_c * int(_n) for _c, _n in re.findall(r'(.)(\\d+)', args[0]))\n",
        ]
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 2


class GenerateurDictTransform:
    """
    TRANSFORMATION DE DICTIONNAIRE — réécrire un dict EXISTANT clé/valeur par clé/valeur :

        {KEY: VAL for k, v in args[0].items()}   KEY ∈ {k, v} ; VAL ∈ {k, v, v+v, v+1}

    invert_dict = {v: k …} (échange clé/valeur) ; double_valeurs = {k: v+v …}.

    NOUVEAU : prend un DICT en entrée et le transforme. `dict-accu` et `group-by` CONSTRUISENT un dict depuis une
    LISTE/des paires (comptage, agrégat par clé) ; ils ne réécrivent pas un dict donné. Borné (2·4 - 1 identité = 7),
    honnête (n'émet que des dict-compréhensions sur d.items()). DÉGÉNÉRÉ élagué : {k: v …} = copie identique.
    """

    KEYS = ("_k", "_v")
    VALS = ("_k", "_v", "_v + _v", "_v + 1")

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for key in self.KEYS:
            for val in self.VALS:
                if key == "_k" and val == "_v":
                    continue                                  # {k: v …} = copie identique (dégénéré)
                cands.append(f"def {g}(*args, **kwargs):\n    return {{{key}: {val} for _k, _v in args[0].items()}}\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.KEYS) * len(self.VALS)


class GenerateurRecord:
    """
    RECORD À COMPLÉTUDE GRADUABLE — la 1ʳᵉ brique du FRONT GÉNÉRATIF (2026-06-17, vision Yohan « sélectionner
    ce qu'on veut : bonne réponse OU complète »). Sortie = un dict {clé_fixe: agrégat} dont la COMPLÉTUDE croît :

        niveau 1 -> {"somme": sum(xs)}        niveau 4 -> {"somme":…, "n":…, "max":…, "min":…}

    Émet les PRÉFIXES du VOCABULAIRE ordonné -> le moteur produit EXACTEMENT la complétude que la spec demande
    (chaque niveau = un record CORRECT, juste moins/plus complet). C'est le 1er terrain où le gradient de richesse
    est GÉNUINE : la richesse vit dans le GÉNÉRATIF (combien de détail), pas dans la fonction pure (correct/faux).

    NOUVEAU TERRITOIRE : `dict-accu`/`group-by` font des dicts CLÉS-DONNÉES (fréquences/groupes par valeur) ; ici
    les clés sont FIXES (noms de champs) -> records. Borné (|VOCAB| candidats = un par complétude), honnête (ne
    minte QUE des records du vocab ; sur une tâche non-record -> rien). ORDRE des candidats = complétude croissante
    (significatif : la spec sélectionne le bon ; on ne shuffle pas)."""

    # Vocabulaire ORDONNÉ (clé, agrégat). Agrégats totaux/sûrs sur liste non vide (max/min exigent non vide).
    VOCAB = (("somme", "sum(args[0])"), ("n", "len(args[0])"),
             ("max", "max(args[0])"), ("min", "min(args[0])"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for L in range(1, len(self.VOCAB) + 1):
            champs = ", ".join(f"{cle!r}: {expr}" for cle, expr in self.VOCAB[:L])
            cands.append(f"def {g}(*args, **kwargs):\n    return {{{champs}}}\n")
        # PAS de shuffle : l'ordre court->long (complétude) est porteur de sens ; la spec choisit le bon préfixe.
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.VOCAB)


class GenerateurAnticipation:
    """
    ANTICIPATION — prédire le TERME SUIVANT d'une séquence (2026-06-17, insight Yohan « l'anticipation est une brique
    cross-domaine »). Forme tractable et VÉRIFIABLE de l'anticipation : donné un historique `args[0]`, rendre le
    prochain élément selon la RÈGLE que les exemples établissent (le held-out prouve qu'on a saisi la règle, pas
    mémorisé). Cognitive et agnostique : toute séquence d'entiers à motif (arithmétique, Fibonacci, géométrique…).

    NOUVEAU TERRITOIRE : aucun étage n'EXTRAPOLE un terme à venir. `adjacence` agrège des relations de voisins ;
    `serie` compte des runs ; `map-repli`/`comprehension-generale` replient le PASSÉ — aucun ne PROJETTE le futur.
    Borné (|REGLES| candidats), honnête (ne minte que des prédictions de terme suivant ; séquence len>=2)."""

    # Règles de TERME SUIVANT (sur args[0] = l'historique). Chacune une hypothèse de motif, le juge tranche laquelle.
    REGLES = (("ari", "args[0][-1] + (args[0][-1] - args[0][-2])"),   # arithmétique : différence constante
              ("fib", "args[0][-1] + args[0][-2]"),                    # somme des deux derniers (Fibonacci-like)
              ("geo", "args[0][-1] * (args[0][-1] // args[0][-2])"),   # géométrique (ratio ENTIER)
              ("dbl", "args[0][-1] * 2"),                              # doublement
              ("sq",  "args[0][-1] ** 2"))                             # carré du dernier

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return {expr}\n" for _, expr in self.REGLES]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REGLES)


class GenerateurOptimisation:
    """
    DÉCISION / OPTIMISATION — choisir le MEILLEUR élément d'une liste selon un CRITÈRE dérivé (2026-06-17, brique
    cognitive) : `max|min(args[0], key=lambda _x: f(_x))`. C'est le cœur de « décider » (vers la planification).

    NOUVEAU vs `index-ordonne` (qui ordonne par VALEUR brute, `sorted(xs)[k]`) : ici le critère est une mesure
    DÉRIVÉE de l'élément — longueur (plus long mot), magnitude (plus grand en valeur absolue), somme (sous-liste la
    plus lourde). Borné (|SENS|·|CRITÈRES|), honnête (un critère hors-domaine lève -> candidat rejeté par le juge ;
    on ne minte que la décision que les exemples valident)."""

    CRITERES = (("len", "len(_x)"), ("abs", "abs(_x)"), ("sum", "sum(_x)"))   # mesures dérivées d'un élément
    SENS = ("max", "min")

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return {sens}(args[0], key=lambda _x: {expr})\n"
                 for sens in self.SENS for _, expr in self.CRITERES]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.SENS) * len(self.CRITERES)


class GenerateurRanking:
    """
    CLASSEMENT / PRIORISATION — ordonner TOUTE la liste selon un CRITÈRE dérivé (2026-06-17, brique cognitive) :
    `sorted(args[0], key=lambda _x: f(_x)[, reverse=True])`. Distinct d'`optimisation` (qui rend UN meilleur) : ici
    la liste ORDONNÉE entière (prioriser/classer). NOUVEAU vs le tri par VALEUR brute (`sorted(xs)`) : le critère est
    une mesure DÉRIVÉE (longueur, magnitude, somme), asc ou desc. Borné (|SENS|·|CRITÈRES|), honnête."""

    CRITERES = (("len", "len(_x)"), ("abs", "abs(_x)"), ("sum", "sum(_x)"))
    SENS = ("", ", reverse=True")

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return sorted(args[0], key=lambda _x: {expr}{rev})\n"
                 for rev in self.SENS for _, expr in self.CRITERES]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.SENS) * len(self.CRITERES)


class GenerateurBits:
    """
    DOMAINE BINAIRE / BITS — opérations bit-à-bit sur des entiers (2026-06-17, élargir les domaines vérifiables).
    Deux familles : BINAIRE `a OP b` (ET `&`, OU `|`, XOR `^`, décalages `<<`/`>>`) et UNAIRE (popcount = nb de bits
    à 1, puissance-de-2). NOUVEAU TERRITOIRE : aucun étage ne fait d'arithmétique BINAIRE — `multi-entrée` ne compose
    que des ops du registre (mul/add/sub/mod/max2/min2), jamais `&`/`|`/`^`. Borné (|BIN|+|UN|), honnête."""

    BIN = (("et", "args[0] & args[1]"), ("ou", "args[0] | args[1]"), ("xor", "args[0] ^ args[1]"),
           ("gauche", "args[0] << args[1]"), ("droite", "args[0] >> args[1]"),
           ("hamming", "bin(args[0] ^ args[1]).count('1')"))   # distance de Hamming = popcount du XOR
    UN = (("popcount", "bin(args[0]).count('1')"),
          ("est_puissance2", "args[0] > 0 and (args[0] & (args[0] - 1)) == 0"),
          ("bit_bas", "args[0] & -args[0]"),                        # plus bas bit allumé (n & -n)
          ("zeros_bas", "(args[0] & -args[0]).bit_length() - 1"),   # nb de zéros de poids faible (ctz)
          ("est_puissance4", "args[0] > 0 and (args[0] & (args[0] - 1)) == 0 and (args[0] - 1) % 3 == 0"),
          ("gray_code", "args[0] ^ (args[0] >> 1)"),                # code de Gray du rang n
          ("max_xor_pair", "max((args[0][_i] ^ args[0][_j] for _i in range(len(args[0]))"
                           " for _j in range(_i + 1, len(args[0]))), default=0)"),
          # plus petite puissance de 2 >= n (gap_probe 13ᵉ vague) ; bit_length du prédécesseur.
          ("next_power_of_two", "1 if args[0] <= 1 else 1 << (args[0] - 1).bit_length()"),
          # Nim : le premier joueur gagne ssi le XOR des tas est non nul (théorème de Sprague-Grundy) — 18ᵉ vague.
          ("nim_win", "__import__('functools').reduce(lambda _a, _b: _a ^ _b, args[0], 0) != 0"),
          # nombre total de bits à 1 sur les entiers 0..n — 18ᵉ vague.
          ("count_bits_range", "sum(bin(_i).count('1') for _i in range(args[0] + 1))"),
          # bits INVERSÉS sur une largeur fixe (gap_probe 22ᵉ vague).
          ("reverse_bits_width", "int(bin(args[0])[2:].zfill(args[1])[::-1], 2)"),
          # ET binaire de tous les entiers de m à n (réduction par &) — gap_probe 24ᵉ vague.
          ("bitwise_and_range",
           "__import__('functools').reduce(lambda _a, _b: _a & _b, range(args[0] + 1, args[1] + 1), args[0])"),
          # COMPLÉMENT base-10 : inverse les bits dans la largeur de n (gap_probe 25ᵉ vague).
          ("complement_base10", "args[0] ^ ((1 << args[0].bit_length()) - 1)"),
          # plus grand ÉCART entre deux bits à 1 consécutifs (gap_probe 26ᵉ vague).
          ("binary_gap",
           "max([_j - _i for _i, _j in zip([_p for _p, _c in enumerate(bin(args[0])[2:]) if _c == '1'],"
           " [_p for _p, _c in enumerate(bin(args[0])[2:]) if _c == '1'][1:])], default=0)"),
          # liste des popcounts de 0..n (chaque entier compté) — gap_probe 27ᵉ vague.
          ("count_bits_list", "[bin(_i).count('1') for _i in range(args[0] + 1)]"),
          # SÉQUENCE de Gray sur n bits (liste de 2**n entiers) -> distinct du gray_code SCALAIRE — gap_probe 42ᵉ vague.
          ("gray_code_seq", "[_i ^ (_i >> 1) for _i in range(2 ** args[0])]"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return {expr}\n" for _, expr in (*self.BIN, *self.UN)]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.BIN) + len(self.UN)


class GenerateurLogique:
    """
    DOMAINE LOGIQUE — QUANTIFICATEURS de comptage sur une liste de vérités (2026-06-17, élargir les domaines
    vérifiables) : `exactement_un`, `au_moins_deux`, `aucun`, `parité impaire`, `majorité`. NOUVEAU : `all`/`any`
    sont déjà `min`/`max` (couverts par comprehension-generale), MAIS un PRÉDICAT sur le COMPTE (`sum(xs) == k`,
    `2·sum > len`) ne l'est pas (comprehension-generale rend la somme, pas `somme==k`). Borné, honnête."""

    LOG = (("exactement_un", "sum(args[0]) == 1"),
           ("au_moins_deux", "sum(args[0]) >= 2"),
           ("aucun", "sum(args[0]) == 0"),
           ("parite_impaire", "sum(args[0]) % 2 == 1"),
           ("majorite", "sum(args[0]) * 2 > len(args[0])"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return {expr}\n" for _, expr in self.LOG]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.LOG)


class GenerateurEnsembles:
    """
    DOMAINE ENSEMBLISTE — algèbre de DEUX ensembles (2026-06-17, élargir les domaines vérifiables) : intersection,
    union, différence, différence symétrique (rendues TRIÉES -> déterministes) + prédicats (sous-ensemble, disjoints).
    NOUVEAU : aucun étage ne fait d'algèbre ensembliste à deux listes — `dedup` ne dédoublonne qu'UNE liste, et
    `multi-entrée` compose des ops scalaires. Borné (|OPS|+|PRED|), honnête (exige une 2ᵉ entrée)."""

    OPS = (("inter", "sorted(set(args[0]) & set(args[1]))"),
           ("union", "sorted(set(args[0]) | set(args[1]))"),
           ("diff", "sorted(set(args[0]) - set(args[1]))"),
           ("sym", "sorted(set(args[0]) ^ set(args[1]))"),
           # intersection MULTISET (multiplicité = min des occurrences) -> set-inter perd la multiplicité — 39ᵉ vague.
           ("inter_multi",
            "sorted(_v for _v in set(args[0]) & set(args[1]) for _ in range(min(args[0].count(_v), args[1].count(_v))))"))
    PRED = (("sous_ensemble", "set(args[0]) <= set(args[1])"),
            ("disjoints", "set(args[0]).isdisjoint(set(args[1]))"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return {expr}\n" for _, expr in (*self.OPS, *self.PRED)]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.OPS) + len(self.PRED)


class GenerateurStatistiques:
    """
    ANALYSE STATISTIQUE — résumés statistiques d'une liste d'entiers (2026-06-17, faculté « analyse ») : médiane
    (élément central de la liste triée), mode (valeur la plus fréquente), moyenne entière (sum//len), amplitude
    centrée (somme des écarts absolus à la médiane). NOUVEAU : `index-ordonne` ordonne par un k VENANT DE L'ENTRÉE ;
    ici l'indice est CALCULÉ (len//2) ; `group-by` compte mais rend un dict, pas la valeur modale. Borné, honnête
    (liste non vide)."""

    STATS = (("mediane", "sorted(args[0])[len(args[0]) // 2]"),
             ("mode", "max(set(args[0]), key=args[0].count)"),
             ("moyenne", "sum(args[0]) // len(args[0])"),
             ("ecart_median", "sum(abs(_x - sorted(args[0])[len(args[0]) // 2]) for _x in args[0])"),
             # numérateur ENTIER de la variance = n·Σx² − (Σx)²  (= n²·variance, sans fraction) — gap_probe 12ᵉ vague.
             ("variance_num", "len(args[0]) * sum(_x * _x for _x in args[0]) - sum(args[0]) ** 2"),
             # bonbons distribuables = min(nb de types DISTINCTS, moitié de la taille) — gap_probe 39ᵉ vague.
             ("distribuer_bonbons", "min(len(set(args[0])), len(args[0]) // 2)"),
             # 3ᵉ maximum DISTINCT (sinon le max si < 3 distincts) — statistique d'ordre — gap_probe 40ᵉ vague.
             ("tiers_max", "sorted(set(args[0]), reverse=True)[2] if len(set(args[0])) >= 3 else max(args[0])"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return {expr}\n" for _, expr in self.STATS]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.STATS)


class GenerateurConversion:
    """
    CONVERSION / NUMÉRATION — retranscrire un entier entre systèmes (2026-06-17, faculté « retranscription ») :
    décimal<->binaire (chaîne), décimal<->hexa. EXTENSION 2026-06-19 (gap_probe 4ᵉ vague, lacunes MESURÉES) :
    décomposition en chiffres d'une base ARBITRAIRE (to_base_digits, MSB d'abord), et NUMÉRATION ROMAINE dans les
    deux sens (int<->romain, algorithme glouton / valeurs soustractives). NOUVEAU : aucun étage ne convertit de base
    arbitraire ni ne traite les chiffres romains — `bits` fait du bit-à-bit, `cesar` décale des lettres. Borné (7),
    honnête."""

    CONV = (("vers_binaire", "    return bin(args[0])[2:]"),
            ("vers_hex", "    return format(args[0], 'x')"),
            ("depuis_binaire", "    return int(args[0], 2)"),
            ("depuis_hex", "    return int(args[0], 16)"),
            ("to_base_digits",
             "    _n, _b = args[0], args[1]\n    if _n == 0:\n        return [0]\n    _r = []\n"
             "    while _n:\n        _r.append(_n % _b)\n        _n //= _b\n    return _r[::-1]"),
            ("int_to_roman",
             "    _v = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'), (50, 'L'),"
             " (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]\n    _n, _s = args[0], ''\n"
             "    for _q, _sym in _v:\n        while _n >= _q:\n            _s += _sym\n            _n -= _q\n    return _s"),
            ("roman_to_int",
             "    _m = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}\n    _s = args[0]\n"
             "    _t = 0\n    for _i in range(len(_s)):\n        _val = _m[_s[_i]]\n"
             "        if _i + 1 < len(_s) and _m[_s[_i + 1]] > _val:\n            _t -= _val\n"
             "        else:\n            _t += _val\n    return _t"),
            ("zigzag_encode", "    return args[0] * 2 if args[0] >= 0 else -args[0] * 2 - 1"),
            # somme des chiffres d'un entier dans une base ARBITRAIRE — gap_probe 20ᵉ vague.
            ("digit_sum_base",
             "    _n, _b = args[0], args[1]\n    _s = 0\n    while _n > 0:\n        _s += _n % _b\n        _n //= _b\n    return _s"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.CONV]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.CONV)


class GenerateurParsing:
    """
    PARSING STRUCTURÉ — extraire une STRUCTURE d'une chaîne (2026-06-17, faculté « analyse/retranscription ») :
    paires clé=valeur (`'a=1,b=2'`->dict), liste d'entiers (`'1 2 3'`->[1,2,3]), découpe sur un séparateur (args[1]).
    NOUVEAU : `mots` fait split+join (rend une CHAÎNE) ; `dict-accu` compte des fréquences. Ici on PARSE une chaîne
    en dict/liste structurée. Borné (3), honnête."""

    PARSE = (("paires_kv", "dict(_p.split('=') for _p in args[0].split(','))"),
             ("entiers", "[int(_x) for _x in args[0].split()]"),
             ("decoupe", "args[0].split(args[1])"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return {expr}\n" for _, expr in self.PARSE]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.PARSE)


class GenerateurChiffres:
    """
    DÉCOMPOSITION DÉCIMALE — opérer sur les CHIFFRES d'un entier (2026-06-17, faculté « analyse ») : somme des
    chiffres, nombre de chiffres, entier inversé, plus grand chiffre. NOUVEAU : aucun étage ne décompose un entier
    en ses chiffres décimaux (`str(n)` caractère par caractère). EXTENSION 2026-06-19 (gap_probe 5ᵉ vague) : nombre
    d'Armstrong (somme des chiffres élevés à la puissance du nombre de chiffres == n). Borné (5), honnête (entiers >= 0)."""

    CHIFFRES = (("somme_chiffres", "sum(int(_c) for _c in str(args[0]))"),
                ("nb_chiffres", "len(str(args[0]))"),
                ("inverse_chiffres", "int(str(args[0])[::-1])"),
                ("chiffre_max", "max(int(_c) for _c in str(args[0]))"),
                ("est_armstrong", "sum(int(_c) ** len(str(args[0])) for _c in str(args[0])) == args[0]"),
                ("digit_factorial_sum", "sum(__import__('math').factorial(int(_c)) for _c in str(args[0]))"),
                # entier INVERSÉ en préservant le signe (gap_probe 21ᵉ vague).
                ("reverse_integer", "(-1 if args[0] < 0 else 1) * int(str(abs(args[0]))[::-1])"),
                # l'entier est-il un PALINDROME (négatif -> faux) (gap_probe 21ᵉ vague).
                ("is_palindrome_number", "args[0] >= 0 and str(args[0]) == str(args[0])[::-1]"),
                # FIZZBUZZ : 1..n -> 'Fizz'/'Buzz'/'FizzBuzz'/chiffre (gap_probe 30ᵉ vague).
                ("fizzbuzz",
                 "['FizzBuzz' if _i % 15 == 0 else 'Fizz' if _i % 3 == 0 else 'Buzz' if _i % 5 == 0"
                 " else str(_i) for _i in range(1, args[0] + 1)]"),
                # PRODUIT des chiffres MOINS leur somme (gap_probe 31ᵉ vague).
                ("subtract_product_and_sum",
                 "__import__('math').prod(int(_c) for _c in str(args[0])) - sum(int(_c) for _c in str(args[0]))"),
                # MAXIMISER en changeant au plus un 6 en 9 (le 1er 6) — gap_probe 35ᵉ vague.
                ("maximum_69_number", "int(str(args[0]).replace('6', '9', 1))"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return {expr}\n" for _, expr in self.CHIFFRES]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.CHIFFRES)


class GenerateurListeTransforms:
    """
    TRANSFORMS STRUCTURELS DE LISTE (2026-06-17) : rotation de k (args[1]), découpe en BLOCS de taille k,
    entrelacement de DEUX listes. NOUVEAU : `fenetre` agrège des sous-séquences (scalaire) ; `positionnel` strie par
    parité ; aucun ne ROTATIONNE, ne CHUNK, ni n'entrelace deux listes. Borné (3), honnête (2ᵉ entrée requise)."""

    LT = (("rotation", "args[0][args[1]:] + args[0][:args[1]]"),
          ("blocs", "[args[0][_i:_i + args[1]] for _i in range(0, len(args[0]), args[1])]"),
          ("entrelace", "[_x for _p in zip(args[0], args[1]) for _x in _p]"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return {expr}\n" for _, expr in self.LT]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.LT)


class GenerateurMathAvance:
    """
    MATH AVANCÉ — théorie des nombres (2026-06-17, faculté « analyse/calcul ») : racine entière `isqrt`, PPCM `lcm`,
    combinaisons `C(n,k)`, exponentiation modulaire `pow(a,b,m)`. NOUVEAU : aucun étage ne fait de racine, de PPCM,
    de combinatoire ni d'exponentiation modulaire (`while` fait gcd, `pli` fait factorielle, mais pas ceux-ci).
    Borné (4), honnête. La stdlib `math` est importable dans la sandbox (vérifié)."""

    MATH = (("isqrt", "    import math\n    return math.isqrt(args[0])"),
            ("lcm", "    import math\n    return args[0] * args[1] // math.gcd(args[0], args[1])"),
            ("comb", "    import math\n    return math.comb(args[0], args[1])"),
            ("pow_mod", "    return pow(args[0], args[1], args[2])"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.MATH]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.MATH)


class GenerateurChainesAvancees:
    """
    OPÉRATIONS DE CHAÎNE AVANCÉES (2026-06-17) : anagramme (mêmes lettres ?), compter une sous-chaîne, remplacer,
    INDICE de première occurrence (find -> -1 si absent, gap_probe 4ᵉ vague). NOUVEAU : `mots` fait split/join,
    `parsing` extrait une structure, `cesar` décale — aucun ne teste l'anagramme, ne compte/localise une sous-chaîne,
    ni ne remplace. EXTENSION 2026-06-19 (5ᵉ vague) : rotation circulaire (b == rotation de a), toutes les occurrences
    (positions, chevauchantes), longueur du plus long sous-palindrome. Borné (7), honnête."""

    CHAINES = (("anagramme", "sorted(args[0]) == sorted(args[1])"),
               ("compte_sous_chaine", "args[0].count(args[1])"),
               ("remplace", "args[0].replace(args[1], args[2])"),
               ("indice_sous_chaine", "args[0].find(args[1])"),
               ("est_rotation", "len(args[0]) == len(args[1]) and args[1] in args[0] + args[0]"),
               ("toutes_occurrences",
                "[_i for _i in range(len(args[0])) if args[0][_i:_i + len(args[1])] == args[1]]"),
               ("longueur_palindrome_max",
                "max((_j - _i for _i in range(len(args[0])) for _j in range(len(args[0]), _i, -1)"
                " if args[0][_i:_j] == args[0][_i:_j][::-1]), default=0)"),
               ("longueur_sous_chaine_commune",
                "max((_j - _i for _i in range(len(args[0])) for _j in range(_i + 1, len(args[0]) + 1)"
                " if args[0][_i:_j] in args[1]), default=0)"),
               ("est_pangramme",
                "len(set(_c for _c in args[0].lower() if _c.isalpha())) == 26"),
               ("hamming_str", "sum(_c1 != _c2 for _c1, _c2 in zip(args[0], args[1]))"),
               ("valid_palindrome_alnum",
                "[_c.lower() for _c in args[0] if _c.isalnum()] == [_c.lower() for _c in args[0] if _c.isalnum()][::-1]"),
               # s est-il la répétition d'un motif (astuce (s+s)[1:-1]) (gap_probe 23ᵉ vague).
               ("repeated_substring_pattern", "args[0] in (args[0] + args[0])[1:-1]"),
               # longueur du DERNIER mot (gap_probe 26ᵉ vague).
               ("length_of_last_word", "len(args[0].split()[-1]) if args[0].split() else 0"),
               # caractère AJOUTÉ : t = s mélangé + 1 lettre (XOR des ordinaux, les paires s'annulent) — gap_probe 30ᵉ vague.
               ("find_the_difference",
                "chr(__import__('functools').reduce(lambda _a, _c: _a ^ ord(_c), args[0] + args[1], 0))"),
               # JUGE CIRCLE : le robot revient à l'origine ssi #L==#R et #U==#D — gap_probe 32ᵉ vague.
               ("judge_circle",
                "args[0].count('L') == args[0].count('R') and args[0].count('U') == args[0].count('D')"),
               # DÉFANGER une IP : chaque '.' -> '[.]' — gap_probe 33ᵉ vague.
               ("defanging_ip", "args[0].replace('.', '[.]')"),
               # INTERPRÉTEUR : '()' -> 'o', '(al)' -> 'al', 'G' inchangé — gap_probe 34ᵉ vague.
               ("interpret", "args[0].replace('()', 'o').replace('(al)', 'al')"),
               # SCORE : somme des |Δ code ASCII| entre caractères adjacents — gap_probe 36ᵉ vague.
               ("score_of_string",
                "sum(abs(ord(args[0][_i]) - ord(args[0][_i + 1])) for _i in range(len(args[0]) - 1))"),
               # MAJUSCULE valide : tout maj, tout min, ou 1ʳᵉ maj + reste min — gap_probe 36ᵉ vague.
               ("detect_capital",
                "args[0].isupper() or args[0].islower() or (args[0][:1].isupper() and args[0][1:].islower())"),
               # inverser CHAQUE mot (ordre des mots préservé) — gap_probe 36ᵉ vague.
               ("reverse_words_iii", "' '.join(_w[::-1] for _w in args[0].split(' '))"),
               # PLUS GRAND NOMBRE par concaténation (tri comparateur a+b vs b+a, '0' si tout nul) — gap_probe 43ᵉ vague.
               ("largest_number",
                "(lambda _s: '0' if _s[0] == '0' else _s)(''.join(sorted(map(str, args[0]),"
                " key=__import__('functools').cmp_to_key(lambda _a, _b: (_a + _b < _b + _a) - (_a + _b > _b + _a)))))"),
               # nombre de GROUPES d'anagrammes (clé canonique = lettres triées) — gap_probe 49ᵉ vague.
               ("group_anagrams_count", "len(set(''.join(sorted(_s)) for _s in args[0]))"),
               # nombre de SOUS-CHAÎNES DISTINCTES (ensemble de toutes les tranches non vides) — gap_probe 49ᵉ vague.
               ("count_distinct_substrings",
                "len({args[0][_i:_j] for _i in range(len(args[0])) for _j in range(_i + 1, len(args[0]) + 1)})"))

    # plus longue SOUS-SÉQUENCE palindrome (DP = LCS de s et de son miroir) — corps multi-lignes, ajouté en propose.
    LPS = ("    _s = args[0]\n    _t = _s[::-1]\n    _m, _n = len(_s), len(_t)\n"
           "    _dp = [[0] * (_n + 1) for _ in range(_m + 1)]\n    for _i in range(1, _m + 1):\n"
           "        for _j in range(1, _n + 1):\n            if _s[_i - 1] == _t[_j - 1]:\n"
           "                _dp[_i][_j] = _dp[_i - 1][_j - 1] + 1\n            else:\n"
           "                _dp[_i][_j] = max(_dp[_i - 1][_j], _dp[_i][_j - 1])\n    return _dp[_m][_n]")

    # appariement avec JOKERS '?' (un caractère) et '*' (toute sous-chaîne) — DP, corps ajouté en propose.
    WILD = ("    _s, _p = args[0], args[1]\n    _m, _n = len(_s), len(_p)\n"
            "    _dp = [[False] * (_n + 1) for _ in range(_m + 1)]\n    _dp[0][0] = True\n"
            "    for _j in range(1, _n + 1):\n        if _p[_j - 1] == '*':\n            _dp[0][_j] = _dp[0][_j - 1]\n"
            "    for _i in range(1, _m + 1):\n        for _j in range(1, _n + 1):\n            if _p[_j - 1] == '*':\n"
            "                _dp[_i][_j] = _dp[_i - 1][_j] or _dp[_i][_j - 1]\n"
            "            elif _p[_j - 1] == '?' or _p[_j - 1] == _s[_i - 1]:\n"
            "                _dp[_i][_j] = _dp[_i - 1][_j - 1]\n    return _dp[_m][_n]")

    # FONCTION D'ÉCHEC KMP / fonction préfixe (gap_probe 12ᵉ vague) — f[i] = longueur du plus long bord propre.
    KMP = ("    _s = args[0]\n    _n = len(_s)\n    _f = [0] * _n\n    _k = 0\n    for _i in range(1, _n):\n"
           "        while _k > 0 and _s[_i] != _s[_k]:\n            _k = _f[_k - 1]\n"
           "        if _s[_i] == _s[_k]:\n            _k += 1\n        _f[_i] = _k\n    return _f")

    # Z-FUNCTION (gap_probe 12ᵉ vague) — z[i] = longueur du plus long préfixe commun entre s et s[i:] (z[0]=0).
    ZFUN = ("    _s = args[0]\n    _n = len(_s)\n    _z = [0] * _n\n    _l = _r = 0\n    for _i in range(1, _n):\n"
            "        if _i < _r:\n            _z[_i] = min(_r - _i, _z[_i - _l])\n"
            "        while _i + _z[_i] < _n and _s[_z[_i]] == _s[_i + _z[_i]]:\n            _z[_i] += 1\n"
            "        if _i + _z[_i] > _r:\n            _l, _r = _i, _i + _z[_i]\n    return _z")

    # SEGMENTATION EN MOTS / word break (gap_probe 13ᵉ vague) — la chaîne se découpe-t-elle en mots du dico (DP) ?
    WB = ("    _s, _words = args[0], set(args[1])\n    _n = len(_s)\n    _dp = [True] + [False] * _n\n"
          "    for _i in range(1, _n + 1):\n        for _j in range(_i):\n"
          "            if _dp[_j] and _s[_j:_i] in _words:\n                _dp[_i] = True\n                break\n    return _dp[_n]")

    def __init__(self, seed: int = 0):
        self._seed = seed

    # SUITE LOOK-AND-SAY : n-ième terme (1, 11, 21, 1211, …) — gap_probe 17ᵉ vague.
    CSAY = ("    _s = '1'\n    for _ in range(args[0] - 1):\n        _res = ''\n        _i = 0\n"
            "        while _i < len(_s):\n            _j = _i\n            while _j < len(_s) and _s[_j] == _s[_i]:\n"
            "                _j += 1\n            _res += str(_j - _i) + _s[_i]\n            _i = _j\n        _s = _res\n    return _s")

    # MULTIPLICATION de grands entiers en CHAÎNE (méthode scolaire, chiffre par chiffre) — gap_probe 17ᵉ vague.
    MULT = ("    _a, _b = args[0], args[1]\n    if _a == '0' or _b == '0':\n        return '0'\n"
            "    _res = [0] * (len(_a) + len(_b))\n    for _i in range(len(_a) - 1, -1, -1):\n"
            "        for _j in range(len(_b) - 1, -1, -1):\n            _mul = int(_a[_i]) * int(_b[_j])\n"
            "            _p1, _p2 = _i + _j, _i + _j + 1\n            _sum = _mul + _res[_p2]\n"
            "            _res[_p2] = _sum % 10\n            _res[_p1] += _sum // 10\n"
            "    _r = ''.join(map(str, _res)).lstrip('0')\n    return _r if _r else '0'")

    # LONGUEUR de la PLUS PETITE FENÊTRE de s contenant tous les caractères de t (avec multiplicité) ; 0 si
    # aucune (fenêtre glissante à compteur de manques) — gap_probe 49ᵉ vague.
    MWL = ("    _s, _t = args[0], args[1]\n    if not _t:\n        return 0\n"
           "    from collections import Counter\n    _need = Counter(_t)\n    _miss = len(_t)\n    _l = 0\n"
           "    _best = len(_s) + 1\n    for _r in range(len(_s)):\n        if _need[_s[_r]] > 0:\n            _miss -= 1\n"
           "        _need[_s[_r]] -= 1\n        while _miss == 0:\n            if _r - _l + 1 < _best:\n"
           "                _best = _r - _l + 1\n            _need[_s[_l]] += 1\n            if _need[_s[_l]] > 0:\n"
           "                _miss += 1\n            _l += 1\n    return _best if _best <= len(_s) else 0")

    # NOMBRE de combinaisons de lettres d'un numéro de téléphone (produit des tailles de touches) — 50ᵉ vague.
    LCC = ("    _m = {'2': 3, '3': 3, '4': 3, '5': 3, '6': 3, '7': 4, '8': 3, '9': 4}\n"
           "    if not args[0]:\n        return 0\n    _r = 1\n    for _c in args[0]:\n        _r *= _m[_c]\n    return _r")

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return {expr}\n" for _, expr in self.CHAINES]
        cands.append(f"def {g}(*args, **kwargs):\n{self.MWL}\n")    # plus petite fenêtre couvrante (gap_probe 49ᵉ vague)
        cands.append(f"def {g}(*args, **kwargs):\n{self.LCC}\n")    # nb combinaisons clavier téléphone (gap_probe 50ᵉ vague)
        cands.append(f"def {g}(*args, **kwargs):\n{self.LPS}\n")   # plus longue sous-séquence palindrome (DP)
        cands.append(f"def {g}(*args, **kwargs):\n{self.WILD}\n")  # appariement à jokers ?/* (DP)
        cands.append(f"def {g}(*args, **kwargs):\n{self.KMP}\n")   # fonction d'échec KMP / préfixe
        cands.append(f"def {g}(*args, **kwargs):\n{self.ZFUN}\n")  # Z-function
        cands.append(f"def {g}(*args, **kwargs):\n{self.WB}\n")    # segmentation en mots (word break, DP)
        cands.append(f"def {g}(*args, **kwargs):\n{self.CSAY}\n")  # suite look-and-say
        cands.append(f"def {g}(*args, **kwargs):\n{self.MULT}\n")  # multiplication de chaînes
        cands.append(f"def {g}(*args, **kwargs):\n{self.RV}\n")    # voyelles inversées
        cands.append(f"def {g}(*args, **kwargs):\n{self.ECT}\n")   # titre de colonne Excel (int->str)
        cands.append(f"def {g}(*args, **kwargs):\n{self.LPB}\n")   # plus long palindrome constructible
        cands.append(f"def {g}(*args, **kwargs):\n{self.LAB}\n")   # plus longue plage binaire alternée
        cands.append(f"def {g}(*args, **kwargs):\n{self.ISO}\n")   # isomorphisme de chaînes
        cands.append(f"def {g}(*args, **kwargs):\n{self.STOI}\n")  # chaîne -> entier (atoi)
        cands.append(f"def {g}(*args, **kwargs):\n{self.RN}\n")    # note de rançon (construire avec les lettres)
        cands.append(f"def {g}(*args, **kwargs):\n{self.ADDS}\n")  # addition décimale en chaîne
        cands.append(f"def {g}(*args, **kwargs):\n{self.ADDB}\n")  # addition binaire en chaîne
        cands.append(f"def {g}(*args, **kwargs):\n{self.ISUB}\n")  # s sous-séquence de t (gap_probe 29ᵉ vague)
        cands.append(f"def {g}(*args, **kwargs):\n{self.PLAB}\n")  # tailles des partitions par lettre (gap_probe 29ᵉ vague)
        cands.append(f"def {g}(*args, **kwargs):\n{self.VPAL}\n")  # palindrome en retirant <=1 char (gap_probe 29ᵉ vague)
        cands.append(f"def {g}(*args, **kwargs):\n{self.BSS}\n")   # split équilibré R/L (gap_probe 31ᵉ vague)
        cands.append(f"def {g}(*args, **kwargs):\n{self.MDP}\n")   # profondeur max de parenthèses (gap_probe 34ᵉ vague)
        cands.append(f"def {g}(*args, **kwargs):\n{self.ROL}\n")   # inverser seulement les lettres (gap_probe 36ᵉ vague)
        cands.append(f"def {g}(*args, **kwargs):\n{self.MPOW}\n")  # plus long run de caractère (gap_probe 36ᵉ vague)
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    # voyelles INVERSÉES sur place (gap_probe 19ᵉ vague).
    RV = ("    _v = [_c for _c in args[0] if _c in 'aeiouAEIOU']\n    _res = []\n    for _c in args[0]:\n"
          "        if _c in 'aeiouAEIOU':\n            _res.append(_v.pop())\n        else:\n            _res.append(_c)\n"
          "    return ''.join(_res)")
    # TITRE de colonne Excel (numération bijective base-26 inverse) : 1->A, 28->AB (gap_probe 19ᵉ vague).
    ECT = ("    _n = args[0]\n    _s = ''\n    while _n > 0:\n        _n, _rem = divmod(_n - 1, 26)\n"
           "        _s = chr(65 + _rem) + _s\n    return _s")
    # longueur du plus long PALINDROME constructible à partir des lettres (gap_probe 19ᵉ vague).
    LPB = ("    from collections import Counter\n    _cnt = Counter(args[0])\n    _res = 0\n    _odd = 0\n"
           "    for _v in _cnt.values():\n        _res += _v - (_v % 2)\n        if _v % 2:\n            _odd = 1\n"
           "    return _res + _odd")
    # plus longue plage de caractères ALTERNÉS (gap_probe 20ᵉ vague).
    LAB = ("    if not args[0]:\n        return 0\n    _best = 1\n    _cur = 1\n    for _i in range(1, len(args[0])):\n"
           "        if args[0][_i] != args[0][_i-1]:\n            _cur += 1\n        else:\n            _cur = 1\n"
           "        _best = max(_best, _cur)\n    return _best")
    # ISOMORPHISME de deux chaînes (bijection de caractères) (gap_probe 21ᵉ vague).
    ISO = ("    _s, _t = args[0], args[1]\n    if len(_s) != len(_t):\n        return False\n    _m1, _m2 = {}, {}\n"
           "    for _a, _b in zip(_s, _t):\n        if _a in _m1 and _m1[_a] != _b:\n            return False\n"
           "        if _b in _m2 and _m2[_b] != _a:\n            return False\n        _m1[_a] = _b\n        _m2[_b] = _a\n"
           "    return True")
    # CHAÎNE -> ENTIER façon atoi (espaces, signe, chiffres jusqu'au 1er non-chiffre) (gap_probe 21ᵉ vague).
    STOI = ("    _s = args[0].lstrip()\n    if not _s:\n        return 0\n    _i = 0\n    _sign = 1\n"
            "    if _s[0] in '+-':\n        _sign = -1 if _s[0] == '-' else 1\n        _i = 1\n    _num = 0\n"
            "    while _i < len(_s) and _s[_i].isdigit():\n        _num = _num * 10 + int(_s[_i])\n        _i += 1\n"
            "    return _sign * _num")
    # NOTE DE RANÇON : note constructible à partir des lettres du magazine (gap_probe 22ᵉ vague).
    RN = ("    from collections import Counter\n    _nc, _mc = Counter(args[0]), Counter(args[1])\n"
          "    return all(_mc[_c] >= _v for _c, _v in _nc.items())")
    # ADDITION en CHAÎNE chiffre par chiffre, base 10 (gap_probe 23ᵉ vague).
    ADDS = ("    _a, _b = args[0], args[1]\n    _i, _j = len(_a)-1, len(_b)-1\n    _carry = 0\n    _res = []\n"
            "    while _i >= 0 or _j >= 0 or _carry:\n"
            "        _d = _carry + (int(_a[_i]) if _i >= 0 else 0) + (int(_b[_j]) if _j >= 0 else 0)\n"
            "        _res.append(str(_d % 10))\n        _carry = _d // 10\n        _i -= 1\n        _j -= 1\n"
            "    return ''.join(reversed(_res))")
    # ADDITION en CHAÎNE base 2 (gap_probe 23ᵉ vague).
    ADDB = ("    _a, _b = args[0], args[1]\n    _i, _j = len(_a)-1, len(_b)-1\n    _carry = 0\n    _res = []\n"
            "    while _i >= 0 or _j >= 0 or _carry:\n"
            "        _d = _carry + (int(_a[_i]) if _i >= 0 else 0) + (int(_b[_j]) if _j >= 0 else 0)\n"
            "        _res.append(str(_d % 2))\n        _carry = _d // 2\n        _i -= 1\n        _j -= 1\n"
            "    return ''.join(reversed(_res))")
    # s est-il une SOUS-SÉQUENCE de t (deux pointeurs via itérateur consommé) — gap_probe 29ᵉ vague.
    ISUB = ("    _it = iter(args[1])\n    return all(_c in _it for _c in args[0])")
    # PARTITION LABELS : tailles des tranches où chaque lettre tient dans une seule tranche — gap_probe 29ᵉ vague.
    PLAB = ("    _s = args[0]\n    _last = {_c: _i for _i, _c in enumerate(_s)}\n    _res = []\n    _start = _end = 0\n"
            "    for _i, _c in enumerate(_s):\n        _end = max(_end, _last[_c])\n        if _i == _end:\n"
            "            _res.append(_i - _start + 1)\n            _start = _i + 1\n    return _res")
    # PALINDROME VALIDE II : devient palindrome en retirant AU PLUS un caractère (deux pointeurs + essai) — 29ᵉ vague.
    VPAL = ("    _s = args[0]\n"
            "    def _pal(_a, _b):\n        while _a < _b:\n            if _s[_a] != _s[_b]:\n                return False\n"
            "            _a += 1\n            _b -= 1\n        return True\n"
            "    _i, _j = 0, len(_s) - 1\n    while _i < _j:\n        if _s[_i] != _s[_j]:\n"
            "            return _pal(_i + 1, _j) or _pal(_i, _j - 1)\n        _i += 1\n        _j -= 1\n    return True")
    # SPLIT ÉQUILIBRÉ : nb max de tranches où #R == #L (balance ramenée à 0) — gap_probe 31ᵉ vague.
    BSS = ("    _bal = 0\n    _cnt = 0\n    for _c in args[0]:\n        _bal += 1 if _c == 'R' else -1\n"
           "        if _bal == 0:\n            _cnt += 1\n    return _cnt")
    # PROFONDEUR MAX de parenthèses imbriquées — gap_probe 34ᵉ vague.
    MDP = ("    _d = _b = 0\n    for _c in args[0]:\n        if _c == '(':\n            _d += 1\n            _b = max(_b, _d)\n"
           "        elif _c == ')':\n            _d -= 1\n    return _b")
    # inverser SEULEMENT les lettres (non-lettres restent en place) — gap_probe 36ᵉ vague.
    ROL = ("    _lettres = [_c for _c in args[0] if _c.isalpha()]\n    _r = []\n"
           "    for _c in args[0]:\n        _r.append(_lettres.pop() if _c.isalpha() else _c)\n    return ''.join(_r)")
    # plus long RUN d'un même caractère — gap_probe 36ᵉ vague.
    MPOW = ("    _s = args[0]\n    if not _s:\n        return 0\n    _best = _cur = 1\n"
            "    for _i in range(1, len(_s)):\n        _cur = _cur + 1 if _s[_i] == _s[_i - 1] else 1\n"
            "        _best = max(_best, _cur)\n    return _best")

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.CHAINES) + 20


class GenerateurDiviseurs:
    """
    THÉORIE DES NOMBRES ÉLÉMENTAIRE (2026-06-17, faculté « analyse/calcul ») : liste des diviseurs, nombre de
    diviseurs, FACTORISATION en facteurs premiers (stateful). NOUVEAU : aucun étage n'énumère les diviseurs ni ne
    factorise (`generer-tester` trouve le n-ième satisfaisant ; `comprehension-generale` itère args[0], pas
    `range(1, n+1)`). EXTENSION 2026-06-19 (gap_probe 2ᵉ vague, lacunes MESURÉES) : agrégats arithmétiques sur
    `range(1, n+1)` — somme des diviseurs (σ), primalité (compte == 2), perfection (Σ propres == n), indicatrice
    d'Euler (compte des coprimes via gcd). Même squelette « scan 1..n + agrégat par prédicat arithmétique » que les
    diviseurs ; aucun autre étage ne les génère (HORS mesuré). Borné (7), honnête (entiers >= 1)."""

    DIV = (("diviseurs", "    return [_d for _d in range(1, args[0] + 1) if args[0] % _d == 0]"),
           ("nb_diviseurs", "    return sum(1 for _d in range(1, args[0] + 1) if args[0] % _d == 0)"),
           ("somme_diviseurs", "    return sum(_d for _d in range(1, args[0] + 1) if args[0] % _d == 0)"),
           ("est_premier", "    return args[0] > 1 and sum(1 for _d in range(2, args[0]) if args[0] % _d == 0) == 0"),
           ("est_parfait",
            "    return args[0] > 0 and sum(_d for _d in range(1, args[0]) if args[0] % _d == 0) == args[0]"),
           ("indicatrice_euler",
            "    import math\n    return sum(1 for _k in range(1, args[0] + 1) if math.gcd(_k, args[0]) == 1)"),
           ("est_carre_parfait",
            "    _r = 0\n    while _r * _r < args[0]:\n        _r += 1\n    return _r * _r == args[0]"),
           ("compte_premiers_sous",
            "    return sum(1 for _k in range(2, args[0]) if all(_k % _d != 0 for _d in range(2, _k)))"),
           ("zeros_factorielle",
            "    _n, _t, _p = args[0], 0, 5\n    while _p <= _n:\n        _t += _n // _p\n        _p *= 5\n    return _t"),
           ("est_puissance_parfaite",
            "    _n = args[0]\n    for _b in range(2, int(_n ** 0.5) + 2):\n        _p = _b\n        while _p <= _n:\n"
            "            _p *= _b\n            if _p == _n:\n                return True\n    return False"),
           ("est_heureux",
            "    _n, _seen = args[0], set()\n    while _n != 1 and _n not in _seen:\n        _seen.add(_n)\n"
            "        _n = sum(int(_c) ** 2 for _c in str(_n))\n    return _n == 1"),
           ("est_automorphe", "    return str(args[0] * args[0]).endswith(str(args[0]))"),
           ("inverse_modulaire",
            "    for _x in range(args[1]):\n        if (args[0] * _x) % args[1] == 1:\n            return _x\n    return -1"),
           ("crt2",
            "    import math\n    _a1, _m1, _a2, _m2 = args[0], args[1], args[2], args[3]\n"
            "    _l = _m1 * _m2 // math.gcd(_m1, _m2)\n    for _x in range(_l):\n"
            "        if _x % _m1 == _a1 % _m1 and _x % _m2 == _a2 % _m2:\n            return _x\n    return -1"),
           # somme de DEUX CARRÉS : existe-t-il a,b >= 0 avec a²+b² == n ? (recherche bornée + isqrt exact) — 12ᵉ vague.
           ("est_somme_deux_carres",
            "    import math\n    _n = args[0]\n    _a = 0\n    while _a * _a <= _n:\n        _b2 = _n - _a * _a\n"
            "        _r = math.isqrt(_b2)\n        if _r * _r == _b2:\n            return True\n        _a += 1\n    return False"),
           # fonction de MÖBIUS μ(n) : 0 si carré-divisible, sinon (-1)^(nb de facteurs premiers distincts) — 13ᵉ vague.
           ("mobius",
            "    _n = args[0]\n    if _n == 1:\n        return 1\n    _p = 0\n    _d = 2\n    _m = _n\n"
            "    while _d * _d <= _m:\n        if _m % _d == 0:\n            _m //= _d\n"
            "            if _m % _d == 0:\n                return 0\n            _p += 1\n        _d += 1\n"
            "    if _m > 1:\n        _p += 1\n    return -1 if _p % 2 else 1"),
           # somme de l'indicatrice d'Euler Σ_{k=1..n} φ(k) — 13ᵉ vague.
           ("euler_phi_sum",
            "    import math\n    return sum(sum(1 for _k in range(1, _j + 1) if math.gcd(_k, _j) == 1)"
            " for _j in range(1, args[0] + 1))"),
           # nombre LAID : positif dont les seuls facteurs premiers sont 2, 3, 5 — gap_probe 19ᵉ vague.
           ("is_ugly",
            "    _n = args[0]\n    if _n <= 0:\n        return False\n    for _f in (2, 3, 5):\n"
            "        while _n % _f == 0:\n            _n //= _f\n    return _n == 1"),
           # somme ALIQUOTE : somme des diviseurs PROPRES (exclut n) — gap_probe 22ᵉ vague.
           ("aliquot_sum", "    return sum(_d for _d in range(1, args[0]) if args[0] % _d == 0)"),
           # paire AMICALE : a != b et chacun = somme aliquote de l'autre — gap_probe 22ᵉ vague.
           ("amicable_pair",
            "    def _s(_x):\n        return sum(_d for _d in range(1, _x) if _x % _d == 0)\n"
            "    return args[0] != args[1] and _s(args[0]) == args[1] and _s(args[1]) == args[0]"),
           # puissance de 3 ? (gap_probe 23ᵉ vague).
           ("power_of_three",
            "    _n = args[0]\n    if _n < 1:\n        return False\n    while _n % 3 == 0:\n        _n //= 3\n    return _n == 1"),
           ("facteurs_premiers",
            "    _n, _f, _d = args[0], [], 2\n    while _d * _d <= _n:\n        while _n % _d == 0:\n"
            "            _f.append(_d)\n            _n //= _d\n        _d += 1\n    if _n > 1:\n        _f.append(_n)\n    return _f"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.DIV]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.DIV)


class GenerateurGeometrie:
    """
    GÉOMÉTRIE COMPUTATIONNELLE ENTIÈRE (2026-06-19, gap_probe 2ᵉ vague, faculté « analyse/calcul ») — primitives de
    géométrie discrète à jugement EXACT (entiers, pas de flottant) : distance de Manhattan entre deux points (4 args),
    DOUBLE de l'aire d'un triangle par produit en croix (6 args), DOUBLE de l'aire d'un polygone par la formule du
    lacet/shoelace (1 arg = liste de points). NOUVEAU : aucun étage ne fait de géométrie 2D — `multi-entrée` compose
    des ops binaires sans `abs` (d'où chebyshev capté par max d'écarts mais manhattan = somme de |·| HORS de portée) ;
    aucun étage ne fait de produit en croix ni de balayage shoelace. On garde le DOUBLE de l'aire pour rester ENTIER
    (l'aire vraie est un demi-entier). Borné (3), honnête (coordonnées entières)."""

    GEO = (("manhattan", "    return abs(args[0] - args[2]) + abs(args[1] - args[3])"),
           ("triangle_aire2",
            "    return abs(args[0] * (args[3] - args[5]) + args[2] * (args[5] - args[1])"
            " + args[4] * (args[1] - args[3]))"),
           ("polygone_aire2",
            "    _p = args[0]\n    return abs(sum(_p[_i][0] * _p[(_i + 1) % len(_p)][1]"
            " - _p[(_i + 1) % len(_p)][0] * _p[_i][1] for _i in range(len(_p))))"),
           # déterminant 2×2 = produit en croix SIGNÉ (aire orientée) ; entrée = matrice [[a,b],[c,d]].
           ("det2", "    _m = args[0]\n    return _m[0][0] * _m[1][1] - _m[0][1] * _m[1][0]"),
           # appartenance d'un point (entrée scalaire) à un rectangle aligné [x1,y1]-[x2,y2] (bornes incluses).
           ("point_in_rectangle",
            "    return args[2] <= args[0] <= args[4] and args[3] <= args[1] <= args[5]"),
           # appartenance d'un point à un disque de centre (cx,cy) et rayon r (comparaison des carrés -> exact).
           ("point_in_circle",
            "    return (args[0] - args[2]) ** 2 + (args[1] - args[3]) ** 2 <= args[4] ** 2"),
           # type de triangle par le nombre de côtés distincts (3 égaux / 2 égaux / tous différents).
           ("triangle_type",
            "    return 'equilateral' if args[0] == args[1] == args[2]"
            " else 'scalene' if len({args[0], args[1], args[2]}) == 3 else 'isosceles'"),
           # triangle RECTANGLE ? (Pythagore sur les côtés triés ; entier exact) — gap_probe 22ᵉ vague.
           ("is_right_triangle",
            "    _s = sorted([args[0], args[1], args[2]])\n    return _s[0]**2 + _s[1]**2 == _s[2]**2"),
           # nombre de sommets de l'enveloppe convexe (chaîne monotone d'Andrew ; colinéaires intérieurs exclus).
           ("convex_hull_size",
            "    _pts = sorted(set(map(tuple, args[0])))\n    if len(_pts) <= 2:\n        return len(_pts)\n"
            "    def _cr(_o, _a, _b):\n        return (_a[0]-_o[0])*(_b[1]-_o[1]) - (_a[1]-_o[1])*(_b[0]-_o[0])\n"
            "    _lo = []\n    for _p in _pts:\n        while len(_lo) >= 2 and _cr(_lo[-2], _lo[-1], _p) <= 0:\n"
            "            _lo.pop()\n        _lo.append(_p)\n    _up = []\n    for _p in reversed(_pts):\n"
            "        while len(_up) >= 2 and _cr(_up[-2], _up[-1], _p) <= 0:\n            _up.pop()\n        _up.append(_p)\n"
            "    return len(_lo) + len(_up) - 2"),
           # intersection de deux segments (orientations + colinéarité sur segment).
           ("segments_intersect",
            "    _p = [(args[0], args[1]), (args[2], args[3]), (args[4], args[5]), (args[6], args[7])]\n"
            "    def _o(_a, _b, _c):\n        _v = (_b[0]-_a[0])*(_c[1]-_a[1]) - (_b[1]-_a[1])*(_c[0]-_a[0])\n"
            "        return 0 if _v == 0 else (1 if _v > 0 else -1)\n"
            "    def _on(_a, _b, _c):\n        return min(_a[0],_b[0]) <= _c[0] <= max(_a[0],_b[0])"
            " and min(_a[1],_b[1]) <= _c[1] <= max(_a[1],_b[1])\n"
            "    _a, _b, _c, _d = _p\n    _o1, _o2, _o3, _o4 = _o(_a,_b,_c), _o(_a,_b,_d), _o(_c,_d,_a), _o(_c,_d,_b)\n"
            "    if _o1 != _o2 and _o3 != _o4:\n        return True\n"
            "    if _o1 == 0 and _on(_a,_b,_c): return True\n    if _o2 == 0 and _on(_a,_b,_d): return True\n"
            "    if _o3 == 0 and _on(_c,_d,_a): return True\n    if _o4 == 0 and _on(_c,_d,_b): return True\n    return False"),
           # appartenance d'un point à un polygone (lancer de rayon / parité des croisements).
           ("point_in_polygon",
            "    _x, _y, _poly = args[0], args[1], args[2]\n    _n = len(_poly)\n    _ins = False\n    _j = _n - 1\n"
            "    for _i in range(_n):\n        _xi, _yi = _poly[_i]\n        _xj, _yj = _poly[_j]\n"
            "        if (_yi > _y) != (_yj > _y) and _x < (_xj-_xi)*(_y-_yi)/(_yj-_yi) + _xi:\n"
            "            _ins = not _ins\n        _j = _i\n    return _ins"),
           # DIAMÈTRE de Manhattan d'un nuage de points (1 arg = liste [x,y]) : plus grande distance L1
           # entre deux points — gap_probe 44ᵉ vague. Distinct de `manhattan` (4 args, deux points donnés) ;
           # aucun étage ne balayait les paires en L1 (HORS mesuré à froid).
           ("manhattan_diameter",
            "    _p = args[0]\n    _best = 0\n    for _i in range(len(_p)):\n        for _j in range(len(_p)):\n"
            "            _best = max(_best, abs(_p[_i][0] - _p[_j][0]) + abs(_p[_i][1] - _p[_j][1]))\n    return _best"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.GEO]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.GEO)


class GenerateurComptageCombinatoire:
    """
    COMPTAGE COMBINATOIRE (2026-06-19, gap_probe 2ᵉ vague, faculté « analyse/recherche ») — COMPTER les structures
    combinatoires classiques (séquences entières), là où `combinatoire` ÉNUMÈRE (permutations/parties/produit) et
    `math-avance` ne donne que C(n,k) atomique. NOUVEAU : aucun étage ne compose ces formules (HORS mesuré) :
      - catalan(n) = C(2n,n)/(n+1) — chemins de Dyck, parenthésages, arbres binaires.
      - derangements(n) = Σ_{k≤n} (-1)^k · n!/k! — permutations sans point fixe (sous-factorielle).
      - stars_bars(n,k) = C(n+k-1, k-1) — compositions faibles (n objets, k boîtes).
      - partitions(n) = p(n) par DP « pièces » (partitions d'entier non ordonnées).
      - subset_sum_count(xs,t) = nb de sous-ensembles de somme t (énumération bornée).
    Borné (5), honnête (entiers >= 0)."""

    COMB = (("catalan", "    import math\n    return math.comb(2 * args[0], args[0]) // (args[0] + 1)"),
            ("derangements",
             "    import math\n    return sum((-1) ** _k * math.factorial(args[0]) // math.factorial(_k)"
             " for _k in range(args[0] + 1))"),
            ("stars_bars", "    import math\n    return math.comb(args[0] + args[1] - 1, args[1] - 1)"),
            ("partitions",
             "    _n = args[0]\n    _dp = [1] + [0] * _n\n    for _c in range(1, _n + 1):\n"
             "        for _s in range(_c, _n + 1):\n            _dp[_s] += _dp[_s - _c]\n    return _dp[_n]"),
            ("subset_sum_count",
             "    import itertools\n    _xs = args[0]\n    return sum(1 for _r in range(len(_xs) + 1)"
             " for _c in itertools.combinations(_xs, _r) if sum(_c) == args[1])"),
            ("unique_paths", "    import math\n    return math.comb(args[0] + args[1] - 2, args[0] - 1)"),
            ("pascal_row", "    import math\n    return [math.comb(args[0], _k) for _k in range(args[0] + 1)]"),
            # nombre de Bell B(n) = nb de partitions d'un ensemble de n éléments (triangle de Bell) — 13ᵉ vague.
            ("bell_number",
             "    _n = args[0]\n    if _n == 0:\n        return 1\n    _row = [1]\n    for _ in range(_n):\n"
             "        _nr = [_row[-1]]\n        for _v in _row:\n            _nr.append(_nr[-1] + _v)\n        _row = _nr\n"
             "    return _row[0]"),
            # nombre de Stirling de 2ᵉ espèce S(n,k) = partitions de n éléments en k parts non vides (DP) — 13ᵉ vague.
            ("stirling_second",
             "    _n, _k = args[0], args[1]\n    _dp = [[0] * (_k + 1) for _ in range(_n + 1)]\n    _dp[0][0] = 1\n"
             "    for _i in range(1, _n + 1):\n        for _j in range(1, _k + 1):\n"
             "            _dp[_i][_j] = _j * _dp[_i - 1][_j] + _dp[_i - 1][_j - 1]\n    return _dp[_n][_k]"),
            # EXISTE-t-il un sous-ensemble de somme cible (DP par ensemble de sommes atteignables) — gap_probe 20ᵉ vague.
            ("subset_sum_exists",
             "    _nums, _t = args[0], args[1]\n    _dp = {0}\n    for _x in _nums:\n"
             "        _dp |= {_s + _x for _s in _dp}\n    return _t in _dp"),
            # nombre de solutions des N reines — BACKTRACKING (colonnes + 2 diagonales) — gap_probe 50ᵉ vague.
            ("n_queens_count",
             "    _n = args[0]\n    _cols = set()\n    _d1 = set()\n    _d2 = set()\n"
             "    def _bt(_r):\n        if _r == _n:\n            return 1\n        _t = 0\n        for _c in range(_n):\n"
             "            if _c in _cols or (_r - _c) in _d1 or (_r + _c) in _d2:\n                continue\n"
             "            _cols.add(_c); _d1.add(_r - _c); _d2.add(_r + _c)\n            _t += _bt(_r + 1)\n"
             "            _cols.discard(_c); _d1.discard(_r - _c); _d2.discard(_r + _c)\n        return _t\n    return _bt(0)"),
            # nombre de TRIPLETS DISTINCTS de somme 0 (tri + deux pointeurs, dédup par ensemble) — gap_probe 51ᵉ vague.
            ("three_sum_count",
             "    _xs = sorted(args[0])\n    _n = len(_xs)\n    _res = set()\n    for _i in range(_n):\n"
             "        _l, _r = _i + 1, _n - 1\n        while _l < _r:\n            _s = _xs[_i] + _xs[_l] + _xs[_r]\n"
             "            if _s == 0:\n                _res.add((_xs[_i], _xs[_l], _xs[_r]))\n                _l += 1\n                _r -= 1\n"
             "            elif _s < 0:\n                _l += 1\n            else:\n                _r -= 1\n    return len(_res)"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.COMB]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.COMB)


class GenerateurPile:
    """
    PILE / MONOTONE — algorithmes à PILE en une passe (2026-06-19, gap_probe 3ᵉ vague, faculté « analyse »).
    NOUVEAU : aucun étage ne simule une pile — `equilibre` ne fait qu'un compteur de profondeur, `multipasse` agrège.
      - eval_rpn(tokens) : ÉVALUER une expression en notation polonaise inverse (liste de jetons str ; +, -, *) via
        une pile d'opérandes.
      - next_greater(xs) : pour chaque élément, le PROCHAIN élément à droite STRICTEMENT plus grand (sinon -1) —
        pile DÉCROISSANTE monotone, le motif canonique « next greater element ».
      - multi_balanced(s) : parenthésage équilibré MULTI-délimiteurs (), [], {} — appariement par pile (au-delà
        d'`equilibre` qui ne compte qu'UN type en profondeur). (gap_probe 6ᵉ vague)
    Borné (3), honnête (jetons valides / liste d'entiers / chaîne de délimiteurs)."""

    PILE = (("eval_rpn",
             "    _st = []\n    for _t in args[0]:\n        if _t in ('+', '-', '*'):\n"
             "            _b = _st.pop()\n            _a = _st.pop()\n"
             "            _st.append(_a + _b if _t == '+' else _a - _b if _t == '-' else _a * _b)\n"
             "        else:\n            _st.append(int(_t))\n    return _st[0]"),
            ("next_greater",
             "    _xs = args[0]\n    _res = [-1] * len(_xs)\n    _st = []\n"
             "    for _i, _v in enumerate(_xs):\n        while _st and _xs[_st[-1]] < _v:\n"
             "            _res[_st.pop()] = _v\n        _st.append(_i)\n    return _res"),
            ("multi_balanced",
             "    _st = []\n    _m = {')': '(', ']': '[', '}': '{'}\n    for _c in args[0]:\n"
             "        if _c in '([{':\n            _st.append(_c)\n        elif _c in _m:\n"
             "            if not _st or _st.pop() != _m[_c]:\n                return False\n    return not _st"),
            # plus grand rectangle dans un histogramme (pile monotone croissante + sentinelle 0) — gap_probe 15ᵉ vague.
            ("largest_rectangle_histogram",
             "    _h = list(args[0]) + [0]\n    _st = []\n    _best = 0\n    for _i, _x in enumerate(_h):\n"
             "        while _st and _h[_st[-1]] >= _x:\n            _top = _st.pop()\n"
             "            _w = _i if not _st else _i - _st[-1] - 1\n            _best = max(_best, _h[_top] * _w)\n"
             "        _st.append(_i)\n    return _best"),
            # températures journalières : nb de jours jusqu'à plus chaud (pile monotone décroissante, distances) — 15ᵉ vague.
            ("daily_temperatures",
             "    _t = args[0]\n    _res = [0] * len(_t)\n    _st = []\n    for _i, _v in enumerate(_t):\n"
             "        while _st and _t[_st[-1]] < _v:\n            _j = _st.pop()\n            _res[_j] = _i - _j\n"
             "        _st.append(_i)\n    return _res"),
            # décodage de chaîne k[...] imbriqué via pile (3[a2[c]] -> accaccacc) — gap_probe 16ᵉ vague.
            ("decode_string",
             "    _st = []\n    _cur = ''\n    _num = 0\n    for _c in args[0]:\n        if _c.isdigit():\n"
             "            _num = _num * 10 + int(_c)\n        elif _c == '[':\n            _st.append((_cur, _num))\n"
             "            _cur, _num = '', 0\n        elif _c == ']':\n            _prev, _k = _st.pop()\n"
             "            _cur = _prev + _cur * _k\n        else:\n            _cur += _c\n    return _cur"),
            # comparaison de deux chaînes avec '#' = retour arrière (deux piles) — gap_probe 23ᵉ vague.
            ("backspace_compare",
             "    def _b(_x):\n        _s = []\n        for _c in _x:\n            if _c == '#':\n"
             "                if _s:\n                    _s.pop()\n            else:\n                _s.append(_c)\n"
             "        return _s\n    return _b(args[0]) == _b(args[1])"),
            # retirer k chiffres pour le plus PETIT nombre (pile monotone croissante) — gap_probe 26ᵉ vague.
            ("remove_k_digits",
             "    _num, _k = args[0], args[1]\n    _st = []\n    for _c in _num:\n"
             "        while _k > 0 and _st and _st[-1] > _c:\n            _st.pop()\n            _k -= 1\n"
             "        _st.append(_c)\n    _st = _st[:len(_st)-_k] if _k else _st\n"
             "    _res = ''.join(_st).lstrip('0')\n    return _res if _res else '0'"),
            # plus longue sous-chaîne de parenthèses VALIDE (pile d'indices, sentinelle -1) — gap_probe 27ᵉ vague.
            ("longest_valid_parentheses",
             "    _st = [-1]\n    _best = 0\n    for _i, _c in enumerate(args[0]):\n"
             "        if _c == '(':\n            _st.append(_i)\n        else:\n            _st.pop()\n"
             "            if not _st:\n                _st.append(_i)\n            else:\n"
             "                _best = max(_best, _i - _st[-1])\n    return _best"),
            # collision d'astéroïdes : simulation à pile (signe = direction, |valeur| = taille) — gap_probe 45ᵉ vague.
            ("asteroid_collision",
             "    _st = []\n    for _x in args[0]:\n        _alive = True\n"
             "        while _alive and _x < 0 and _st and _st[-1] > 0:\n"
             "            if _st[-1] < -_x:\n                _st.pop()\n"
             "            elif _st[-1] == -_x:\n                _st.pop()\n                _alive = False\n"
             "            else:\n                _alive = False\n"
             "        if _alive:\n            _st.append(_x)\n    return _st"),
            # simplification de chemin Unix (.. = remonte, . = ignore) via pile de segments — gap_probe 45ᵉ vague.
            ("simplify_path",
             "    _st = []\n    for _t in args[0].split('/'):\n        if _t == '' or _t == '.':\n            continue\n"
             "        if _t == '..':\n            if _st:\n                _st.pop()\n        else:\n            _st.append(_t)\n"
             "    return '/' + '/'.join(_st)"),
            # score de parenthésage imbriqué ('()'->1, 'AB'->A+B, '(A)'->2*A) via pile d'accumulateurs — 45ᵉ vague.
            ("score_parentheses",
             "    _st = [0]\n    for _c in args[0]:\n        if _c == '(':\n            _st.append(0)\n"
             "        else:\n            _v = _st.pop()\n            _st[-1] += max(2 * _v, 1)\n    return _st[0]"),
            # ajouts minimaux pour un parenthésage valide (compteur d'ouvrants + déficit de fermants) — 45ᵉ vague.
            ("min_add_valid",
             "    _open = 0\n    _add = 0\n    for _c in args[0]:\n        if _c == '(':\n            _open += 1\n"
             "        else:\n            if _open > 0:\n                _open -= 1\n            else:\n                _add += 1\n"
             "    return _add + _open"),
            # RPN avec DIVISION (tronquée vers 0) — superset d'eval_rpn (+,-,*) ; sur +,-,* seul l'original gagne (Occam).
            # gap_probe DUR 2026-06-24.
            ("eval_rpn_div",
             "    _st = []\n    for _t in args[0]:\n        if _t in ('+', '-', '*', '/'):\n"
             "            _b = _st.pop()\n            _a = _st.pop()\n"
             "            _st.append(_a + _b if _t == '+' else _a - _b if _t == '-' else _a * _b if _t == '*' else int(_a / _b))\n"
             "        else:\n            _st.append(int(_t))\n    return _st[0]"),
            # CALCULATRICE à PRÉCÉDENCE (sans parenthèses) : +,-,*,/ avec * et / prioritaires, deux piles
            # (nombres / opérateurs), nombres multi-chiffres. Division tronquée vers 0. gap_probe DUR 2026-06-24.
            ("evaluate_expr",
             "    _s = args[0].replace(' ', '')\n    _nums = []\n    _ops = []\n    _i = 0\n"
             "    _prec = {'+': 1, '-': 1, '*': 2, '/': 2}\n"
             "    def _ap():\n        _b = _nums.pop()\n        _a = _nums.pop()\n        _o = _ops.pop()\n"
             "        _nums.append(_a + _b if _o == '+' else _a - _b if _o == '-' else _a * _b if _o == '*' else int(_a / _b))\n"
             "    while _i < len(_s):\n        _c = _s[_i]\n        if _c.isdigit():\n            _j = _i\n"
             "            while _j < len(_s) and _s[_j].isdigit():\n                _j += 1\n"
             "            _nums.append(int(_s[_i:_j]))\n            _i = _j\n            continue\n"
             "        while _ops and _prec[_ops[-1]] >= _prec[_c]:\n            _ap()\n        _ops.append(_c)\n        _i += 1\n"
             "    while _ops:\n        _ap()\n    return _nums[0]"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.PILE]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.PILE)


class GenerateurSuite:
    """
    SUITES & MOTIFS NUMÉRIQUES (2026-06-19, gap_probe 3ᵉ vague, faculté « anticipation/analyse »).
      - tribonacci(n) : récurrence linéaire d'ORDRE 3 (T0=0,T1=0,T2=1 ; T(n)=T(n-1)+T(n-2)+T(n-3)). `recurrence` est
        figé à 2 états -> ne l'atteint pas (HORS mesuré) ; ici l'ordre 3.
      - is_arithmetic(xs) : la suite est-elle ARITHMÉTIQUE (différences consécutives toutes égales) ? Vrai si < 2
        éléments. Prédicat de motif qu'aucun étage ne calcule.
    Borné (2), honnête (entiers)."""

    SUITE = (("tribonacci",
              "    _a, _b, _c = 0, 0, 1\n    for _ in range(args[0]):\n        _a, _b, _c = _b, _c, _a + _b + _c\n"
              "    return _a"),
             ("is_arithmetic",
              "    _xs = args[0]\n    return all(_xs[_i + 1] - _xs[_i] == _xs[1] - _xs[0]"
              " for _i in range(len(_xs) - 1))"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.SUITE]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.SUITE)


class GenerateurCalendrier:
    """
    CALENDRIER (2026-06-19, gap_probe 3ᵉ vague, faculté « savoir computationnel ») — arithmétique du calendrier
    grégorien. NOUVEAU : aucun étage n'a de table des mois ni de règle bissextile.
      - is_leap_year(y) : année bissextile (y%4==0 et (y%100!=0 ou y%400==0)).
      - days_in_month(y, m) : nombre de jours du mois m de l'année y (réutilise la règle bissextile pour février).
    NB is_leap_year : `recombinaison` ne le résolvait qu'OPPORTUNÉMENT (dépendant d'un store chaud — fragments
    accumulés) et ÉCHOUE à froid (mesuré : 2755 cand., HORS). On l'ancre ici en formule de PREMIÈRE CLASSE -> robuste
    à froid, donc ce n'est PAS du masquage (l'autre voie n'est pas une couverture fiable). Borné (2, graine d'un
    domaine extensible : jour_semaine, jour_annee…), honnête."""

    CAL = (("is_leap_year", "    return args[0] % 4 == 0 and (args[0] % 100 != 0 or args[0] % 400 == 0)"),
           ("days_in_month",
            "    _dm = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][args[1] - 1]\n"
            "    _bis = args[0] % 4 == 0 and (args[0] % 100 != 0 or args[0] % 400 == 0)\n"
            "    return _dm + (1 if args[1] == 2 and _bis else 0)"),
           # nombre de jours entre deux dates grégoriennes (date2 - date1) — gap_probe 18ᵉ vague.
           ("days_between",
            "    import datetime\n    return (datetime.date(args[3], args[4], args[5])"
            " - datetime.date(args[0], args[1], args[2])).days"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.CAL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.CAL)


class GenerateurGraphe:
    """
    GRAPHES (2026-06-17, faculté « analyse », classe d'algo manquante) — opérations sur une liste d'ARÊTES (couples
    `(a, b)`) : voisins d'un sommet, degré, nombre de sommets, présence d'une arête. NOUVEAU : aucun étage ne traite
    de graphe — `group-by` rend un dict de groupes, `ensembles` fait de l'algèbre de 2 listes. Borné (4), honnête."""

    GRAPH = (("voisins", "[_b for _a, _b in args[0] if _a == args[1]]"),
             ("degre", "sum(1 for _e in args[0] if args[1] in _e)"),
             ("nb_sommets", "len(set(_x for _e in args[0] for _x in _e))"),
             ("a_arete", "(args[1], args[2]) in args[0]"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return {expr}\n" for _, expr in self.GRAPH]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.GRAPH)


class GenerateurGrapheConnexite:
    """
    CONNEXITÉ DE GRAPHE par UNION-FIND (2026-06-19, gap_probe 4ᵉ vague, faculté « analyse »). Entrée = (n, edges) où
    n = nombre de sommets 0..n-1 et edges = liste d'arêtes NON orientées. NOUVEAU : `graphe` fait du local (voisins,
    degré) ; aucun étage ne calcule une propriété GLOBALE de connectivité.
      - num_components(n, edges) : nombre de composantes connexes (compte des racines distinctes).
      - has_cycle(n, edges) : le graphe non orienté contient-il un cycle (une arête relie deux sommets déjà unis) ?
    Union-find avec compression de chemin (borné, terminaison garantie). EXTENSION 2026-06-19 (6ᵉ vague) : parcours
    en LARGEUR (BFS) -> distances depuis une source (bfs_dist, -1 si inatteignable) et test de BIPARTITION (2-coloration).
    Borné (4), honnête."""

    _UF = ("    _n, _e = args[0], args[1]\n    _p = list(range(_n))\n    def _f(_x):\n"
           "        while _p[_x] != _x:\n            _p[_x] = _p[_p[_x]]\n            _x = _p[_x]\n        return _x\n")
    _ADJ = ("    _n, _e = args[0], args[1]\n    _adj = [[] for _ in range(_n)]\n"
            "    for _a, _b in _e:\n        _adj[_a].append(_b)\n        _adj[_b].append(_a)\n")
    GRAPH = (("num_components",
              _UF + "    for _a, _b in _e:\n        _p[_f(_a)] = _f(_b)\n"
                    "    return len(set(_f(_i) for _i in range(_n)))"),
             ("has_cycle",
              _UF + "    for _a, _b in _e:\n        _ra, _rb = _f(_a), _f(_b)\n"
                    "        if _ra == _rb:\n            return True\n        _p[_ra] = _rb\n    return False"),
             ("bfs_dist",
              _ADJ + "    _d = [-1] * _n\n    _d[args[2]] = 0\n    _q = [args[2]]\n    while _q:\n"
                     "        _u = _q.pop(0)\n        for _v in _adj[_u]:\n            if _d[_v] == -1:\n"
                     "                _d[_v] = _d[_u] + 1\n                _q.append(_v)\n    return _d"),
             # NON pondéré : plus court chemin (nb d'arêtes) entre DEUX sommets s->t, -1 inatteignable, 0 si s==t —
             # gap_probe DUR 2026-06-24. Comble le trou entre bfs_dist (liste depuis une source) et dijkstra (PONDÉRÉ).
             ("bfs_dist_st",
              _ADJ + "    _d = [-1] * _n\n    _d[args[2]] = 0\n    _q = [args[2]]\n    while _q:\n"
                     "        _u = _q.pop(0)\n        for _v in _adj[_u]:\n            if _d[_v] == -1:\n"
                     "                _d[_v] = _d[_u] + 1\n                _q.append(_v)\n    return _d[args[3]]"),
             ("is_bipartite",
              _ADJ + "    _col = [-1] * _n\n    for _s in range(_n):\n        if _col[_s] == -1:\n"
                     "            _col[_s] = 0\n            _q = [_s]\n            while _q:\n"
                     "                _u = _q.pop(0)\n                for _v in _adj[_u]:\n"
                     "                    if _col[_v] == -1:\n                        _col[_v] = 1 - _col[_u]\n"
                     "                        _q.append(_v)\n                    elif _col[_v] == _col[_u]:\n"
                     "                        return False\n    return True"),
             # arêtes DIRIGÉES : DAG par tri topologique de Kahn (acyclique ssi tous les sommets sont traités).
             ("is_dag",
              "    _n, _e = args[0], args[1]\n    _indeg = [0] * _n\n    _adj = [[] for _ in range(_n)]\n"
              "    for _a, _b in _e:\n        _adj[_a].append(_b)\n        _indeg[_b] += 1\n"
              "    _q = [_i for _i in range(_n) if _indeg[_i] == 0]\n    _cnt = 0\n    while _q:\n"
              "        _u = _q.pop()\n        _cnt += 1\n        for _v in _adj[_u]:\n            _indeg[_v] -= 1\n"
              "            if _indeg[_v] == 0:\n                _q.append(_v)\n    return _cnt == _n"),
             # arêtes NON dirigées : suite des degrés triée par ordre décroissant.
             ("degree_sequence",
              "    _n, _e = args[0], args[1]\n    _deg = [0] * _n\n    for _a, _b in _e:\n        _deg[_a] += 1\n"
              "        _deg[_b] += 1\n    return sorted(_deg, reverse=True)"),
             # ARBRE = connexe ET exactement n-1 arêtes (union-find).
             ("is_tree",
              "    _n, _e = args[0], args[1]\n    if len(_e) != _n - 1:\n        return False\n    _p = list(range(_n))\n"
              "    def _f(_x):\n        while _p[_x] != _x:\n            _p[_x] = _p[_p[_x]]\n            _x = _p[_x]\n"
              "        return _x\n    for _a, _b in _e:\n        _p[_f(_a)] = _f(_b)\n"
              "    return len(set(_f(_i) for _i in range(_n))) == 1"),
             # PONDÉRÉS : arêtes (u, v, w). Dijkstra (plus court chemin src->dst, -1 inatteignable).
             ("dijkstra",
              "    import heapq\n    _n, _e, _s, _t = args[0], args[1], args[2], args[3]\n"
              "    _adj = [[] for _ in range(_n)]\n    for _u, _v, _w in _e:\n        _adj[_u].append((_v, _w))\n"
              "        _adj[_v].append((_u, _w))\n    _dist = [float('inf')] * _n\n    _dist[_s] = 0\n    _pq = [(0, _s)]\n"
              "    while _pq:\n        _d, _u = heapq.heappop(_pq)\n        if _d > _dist[_u]:\n            continue\n"
              "        for _v, _w in _adj[_u]:\n            if _d + _w < _dist[_v]:\n                _dist[_v] = _d + _w\n"
              "                heapq.heappush(_pq, (_d + _w, _v))\n"
              "    return _dist[_t] if _dist[_t] != float('inf') else -1"),
             # PONDÉRÉS : poids total de l'arbre couvrant minimal (Kruskal + union-find).
             ("mst_weight",
              "    _n, _e = args[0], args[1]\n    _p = list(range(_n))\n    def _f(_x):\n"
              "        while _p[_x] != _x:\n            _p[_x] = _p[_p[_x]]\n            _x = _p[_x]\n        return _x\n"
              "    _tot = 0\n    for _w, _u, _v in sorted((_w, _u, _v) for _u, _v, _w in _e):\n"
              "        _ru, _rv = _f(_u), _f(_v)\n        if _ru != _rv:\n            _p[_ru] = _rv\n            _tot += _w\n"
              "    return _tot"),
             # DIRIGÉ pondéré, poids éventuellement négatifs : Bellman-Ford (plus court chemin src->dst, -1 si inatteignable).
             ("bellman_ford",
              "    _n, _e, _s, _t = args[0], args[1], args[2], args[3]\n    _INF = float('inf')\n"
              "    _dist = [_INF] * _n\n    _dist[_s] = 0\n    for _ in range(_n - 1):\n        for _u, _v, _w in _e:\n"
              "            if _dist[_u] != _INF and _dist[_u] + _w < _dist[_v]:\n                _dist[_v] = _dist[_u] + _w\n"
              "    return _dist[_t] if _dist[_t] != _INF else -1"),
             # NON dirigé pondéré : somme des plus courtes distances sur toutes les paires i<j (Floyd-Warshall) — 12ᵉ vague.
             ("apsp_sum",
              "    _n, _e = args[0], args[1]\n    _INF = float('inf')\n"
              "    _d = [[0 if _i == _j else _INF for _j in range(_n)] for _i in range(_n)]\n"
              "    for _u, _v, _w in _e:\n        _d[_u][_v] = min(_d[_u][_v], _w)\n        _d[_v][_u] = min(_d[_v][_u], _w)\n"
              "    for _k in range(_n):\n        for _i in range(_n):\n            for _j in range(_n):\n"
              "                if _d[_i][_k] + _d[_k][_j] < _d[_i][_j]:\n                    _d[_i][_j] = _d[_i][_k] + _d[_k][_j]\n"
              "    return sum(int(_d[_i][_j]) for _i in range(_n) for _j in range(_i + 1, _n))"),
             # DIRIGÉ : premier sommet d'un ordre topologique (plus petit sommet de degré entrant nul) — 12ᵉ vague.
             ("topo_first",
              "    _n, _e = args[0], args[1]\n    _indeg = [0] * _n\n    for _u, _v in _e:\n        _indeg[_v] += 1\n"
              "    _avail = sorted(_i for _i in range(_n) if _indeg[_i] == 0)\n    return _avail[0] if _avail else -1"),
             # NON dirigé : nombre de TRIANGLES (triplets tous reliés) via matrice d'adjacence booléenne — 13ᵉ vague.
             ("count_triangles",
              "    _n, _e = args[0], args[1]\n    _adj = [[False] * _n for _ in range(_n)]\n"
              "    for _u, _v in _e:\n        _adj[_u][_v] = _adj[_v][_u] = True\n"
              "    return sum(1 for _i in range(_n) for _j in range(_i + 1, _n) for _k in range(_j + 1, _n)\n"
              "               if _adj[_i][_j] and _adj[_j][_k] and _adj[_i][_k])"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.GRAPH]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.GRAPH)


class GenerateurTableaux:
    """
    ALGORITHMES DE TABLEAU (2026-06-19, gap_probe 5ᵉ vague, faculté « analyse »). NOUVEAU : ni `acc-courant` (Kadane,
    sous-tableau contigu) ni `liste-transforms` ne couvrent ces motifs.
      - house_robber(xs) : somme maximale d'éléments NON adjacents (DP à deux états : exclu/inclus).
      - rotate_left(xs, k) : rotation circulaire de k crans vers la gauche (k modulo la longueur).
      - missing_number(xs) : entier manquant dans une permutation de 0..n (somme attendue − somme réelle).
      - knapsack01(weights, values, cap) : sac à dos 0/1, valeur max sous contrainte de capacité (DP 1D).
      - max_product_subarray(xs) : produit maximal d'un sous-tableau contigu (suivre max ET min courants, signes).
      - min_path_sum(grid) : somme minimale d'un chemin haut-gauche -> bas-droite (déplacements droite/bas, DP 2D).
        (tableau 2D = aussi un « tableau » ; min_path_sum « résolu » par coïncidence via matrice-reduce -> HORS à froid
        sur held-out durci, donc ancré ici en 1ʳᵉ classe, cf. règle anti-coïncidence.)
    Borné (6), honnête."""

    TAB = (("house_robber",
            "    _a, _b = 0, 0\n    for _x in args[0]:\n        _a, _b = _b, max(_b, _a + _x)\n    return _b"),
           ("rotate_left",
            "    _xs = args[0]\n    _k = args[1] % len(_xs) if _xs else 0\n    return _xs[_k:] + _xs[:_k]"),
           ("missing_number",
            "    _n = len(args[0])\n    return _n * (_n + 1) // 2 - sum(args[0])"),
           ("knapsack01",
            "    _w, _v, _cap = args[0], args[1], args[2]\n    _dp = [0] * (_cap + 1)\n"
            "    for _i in range(len(_w)):\n        for _c in range(_cap, _w[_i] - 1, -1):\n"
            "            _dp[_c] = max(_dp[_c], _dp[_c - _w[_i]] + _v[_i])\n    return _dp[_cap]"),
           ("max_product_subarray",
            "    _xs = args[0]\n    _best = _hi = _lo = _xs[0]\n    for _x in _xs[1:]:\n"
            "        _c = (_hi * _x, _lo * _x, _x)\n        _hi = max(_c)\n        _lo = min(_c)\n"
            "        _best = max(_best, _hi)\n    return _best"),
           ("min_path_sum",
            "    _g = args[0]\n    _R, _C = len(_g), len(_g[0])\n    _dp = [[0] * _C for _ in range(_R)]\n"
            "    for _i in range(_R):\n        for _j in range(_C):\n"
            "            _prev = [_x for _x in (_dp[_i - 1][_j] if _i > 0 else None,"
            " _dp[_i][_j - 1] if _j > 0 else None) if _x is not None]\n"
            "            _dp[_i][_j] = _g[_i][_j] + (min(_prev) if _prev else 0)\n    return _dp[_R - 1][_C - 1]"),
           ("count_islands",
            "    _g = args[0]\n    if not _g or not _g[0]:\n        return 0\n    _R, _C = len(_g), len(_g[0])\n"
            "    _seen = [[False] * _C for _ in range(_R)]\n    _cnt = 0\n    for _i in range(_R):\n        for _j in range(_C):\n"
            "            if _g[_i][_j] == 1 and not _seen[_i][_j]:\n                _cnt += 1\n                _stk = [(_i, _j)]\n"
            "                while _stk:\n                    _x, _y = _stk.pop()\n"
            "                    if 0 <= _x < _R and 0 <= _y < _C and _g[_x][_y] == 1 and not _seen[_x][_y]:\n"
            "                        _seen[_x][_y] = True\n"
            "                        _stk += [(_x + 1, _y), (_x - 1, _y), (_x, _y + 1), (_x, _y - 1)]\n    return _cnt"),
           # AIRE de la plus grande composante connexe de 1 (flood-fill + suivi de taille max) — gap_probe
           # 44ᵉ vague. Sœur de count_islands : même parcours, on retourne la plus grande taille (HORS à froid).
           ("max_island_area",
            "    _g = args[0]\n    if not _g or not _g[0]:\n        return 0\n    _R, _C = len(_g), len(_g[0])\n"
            "    _seen = [[False] * _C for _ in range(_R)]\n    _best = 0\n    for _i in range(_R):\n        for _j in range(_C):\n"
            "            if _g[_i][_j] == 1 and not _seen[_i][_j]:\n                _area = 0\n                _stk = [(_i, _j)]\n"
            "                while _stk:\n                    _x, _y = _stk.pop()\n"
            "                    if 0 <= _x < _R and 0 <= _y < _C and _g[_x][_y] == 1 and not _seen[_x][_y]:\n"
            "                        _seen[_x][_y] = True\n                        _area += 1\n"
            "                        _stk += [(_x + 1, _y), (_x - 1, _y), (_x, _y + 1), (_x, _y - 1)]\n"
            "                _best = max(_best, _area)\n    return _best"),
           # nombre de chemins haut-gauche -> bas-droite (droite/bas) en ÉVITANT les obstacles (1), DP — 50ᵉ vague.
           ("count_paths_obstacles",
            "    _g = args[0]\n    if _g[0][0] == 1:\n        return 0\n    _R, _C = len(_g), len(_g[0])\n"
            "    _dp = [[0] * _C for _ in range(_R)]\n    _dp[0][0] = 1\n    for _i in range(_R):\n        for _j in range(_C):\n"
            "            if _g[_i][_j] == 1:\n                _dp[_i][_j] = 0\n                continue\n"
            "            if _i > 0:\n                _dp[_i][_j] += _dp[_i - 1][_j]\n"
            "            if _j > 0:\n                _dp[_i][_j] += _dp[_i][_j - 1]\n    return _dp[_R - 1][_C - 1]"),
           # index de l'élément DOMINANT (max ≥ 2× tous les autres), sinon -1 — gap_probe 51ᵉ vague.
           ("dominant_index",
            "    _xs = args[0]\n    if not _xs:\n        return -1\n    _m = max(_xs)\n    _mi = _xs.index(_m)\n"
            "    return _mi if all(_m >= 2 * _x for _j, _x in enumerate(_xs) if _j != _mi) else -1"),
           ("partition_equal_subset",
            "    _s = sum(args[0])\n    if _s % 2:\n        return False\n    _t = _s // 2\n    _dp = [True] + [False] * _t\n"
            "    for _x in args[0]:\n        for _c in range(_t, _x - 1, -1):\n            _dp[_c] = _dp[_c] or _dp[_c - _x]\n"
            "    return _dp[_t]"),
           ("count_inversions",
            "    _xs = args[0]\n    return sum(1 for _i in range(len(_xs)) for _j in range(_i + 1, len(_xs))"
            " if _xs[_i] > _xs[_j])"),
           ("merge_sorted", "    return sorted(args[0] + args[1])"),
           # PERMUTATION LEXICOGRAPHIQUE SUIVANTE in-place (pivot montant par la droite, swap, renverse le suffixe) ;
           # si déjà décroissante -> plus petite permutation. gap_probe DUR 2026-06-24. Sortie = liste permutée.
           ("next_permutation",
            "    _a = list(args[0])\n    _i = len(_a) - 2\n    while _i >= 0 and _a[_i] >= _a[_i + 1]:\n        _i -= 1\n"
            "    if _i >= 0:\n        _j = len(_a) - 1\n        while _a[_j] <= _a[_i]:\n            _j -= 1\n"
            "        _a[_i], _a[_j] = _a[_j], _a[_i]\n    _a[_i + 1:] = _a[_i + 1:][::-1]\n    return _a"),
           ("matrix_chain_min",
            "    _d = args[0]\n    _n = len(_d) - 1\n    if _n <= 0:\n        return 0\n"
            "    _dp = [[0] * _n for _ in range(_n)]\n    for _L in range(2, _n + 1):\n"
            "        for _i in range(_n - _L + 1):\n            _j = _i + _L - 1\n"
            "            _dp[_i][_j] = min(_dp[_i][_k] + _dp[_k+1][_j] + _d[_i]*_d[_k+1]*_d[_j+1]"
            " for _k in range(_i, _j))\n    return _dp[0][_n - 1]"),
           ("max_sum_increasing_subseq",
            "    _xs = args[0]\n    if not _xs:\n        return 0\n    _dp = list(_xs)\n"
            "    for _i in range(len(_xs)):\n        for _j in range(_i):\n            if _xs[_j] < _xs[_i]:\n"
            "                _dp[_i] = max(_dp[_i], _dp[_j] + _xs[_i])\n    return max(_dp)"),
           ("spiral_order",
            "    _m = [list(_r) for _r in args[0]]\n    _res = []\n    while _m:\n        _res += list(_m.pop(0))\n"
            "        _m = [list(_r) for _r in zip(*_m)][::-1]\n    return _res"),
           ("subarray_sum_count",
            "    _xs, _k, _cnt = args[0], args[1], 0\n    for _i in range(len(_xs)):\n        _s = 0\n"
            "        for _j in range(_i, len(_xs)):\n            _s += _xs[_j]\n            if _s == _k:\n"
            "                _cnt += 1\n    return _cnt"),
           ("product_except_self",
            "    _xs = args[0]\n    _n = len(_xs)\n    _res = [1] * _n\n    _pre = 1\n    for _i in range(_n):\n"
            "        _res[_i] = _pre\n        _pre *= _xs[_i]\n    _suf = 1\n    for _i in range(_n - 1, -1, -1):\n"
            "        _res[_i] *= _suf\n        _suf *= _xs[_i]\n    return _res"),
           ("trapping_rain_water",
            "    _h = args[0]\n    _l, _r = 0, len(_h) - 1\n    _lm = _rm = _t = 0\n    while _l < _r:\n"
            "        if _h[_l] < _h[_r]:\n            _lm = max(_lm, _h[_l])\n            _t += _lm - _h[_l]\n            _l += 1\n"
            "        else:\n            _rm = max(_rm, _h[_r])\n            _t += _rm - _h[_r]\n            _r -= 1\n    return _t"),
           # plus longue suite d'entiers CONSÉCUTIFS (set + démarrage de série, O(n)) — gap_probe 12ᵉ vague.
           ("longest_consecutive",
            "    _s = set(args[0])\n    _best = 0\n    for _x in _s:\n        if _x - 1 not in _s:\n            _y = _x\n"
            "            while _y + 1 in _s:\n                _y += 1\n            _best = max(_best, _y - _x + 1)\n    return _best"),
           # profit boursier — UNE transaction (min courant) — gap_probe 13ᵉ vague.
           ("max_profit",
            "    _mn = float('inf')\n    _best = 0\n    for _p in args[0]:\n        _mn = min(_mn, _p)\n"
            "        _best = max(_best, _p - _mn)\n    return _best"),
           # profit boursier — transactions ILLIMITÉES (somme des montées) — 13ᵉ vague.
           ("max_profit_multi",
            "    return sum(max(0, args[0][_i] - args[0][_i - 1]) for _i in range(1, len(args[0])))"),
           # nombre de décodages A-Z d'une chaîne de chiffres (1..26 -> lettre), DP — 13ᵉ vague.
           ("decode_ways",
            "    _s = args[0]\n    if not _s or _s[0] == '0':\n        return 0\n    _n = len(_s)\n"
            "    _dp = [0] * (_n + 1)\n    _dp[0] = _dp[1] = 1\n    for _i in range(2, _n + 1):\n"
            "        if _s[_i - 1] != '0':\n            _dp[_i] += _dp[_i - 1]\n"
            "        if 10 <= int(_s[_i - 2:_i]) <= 26:\n            _dp[_i] += _dp[_i - 2]\n    return _dp[_n]"),
           # plus longue sous-séquence CONTIGUË de somme k (préfixes + 1ʳᵉ occurrence) — gap_probe 14ᵉ vague.
           ("longest_subarray_sum_k",
            "    _xs, _k = args[0], args[1]\n    _first = {0: -1}\n    _pre = 0\n    _best = 0\n"
            "    for _i, _v in enumerate(_xs):\n        _pre += _v\n        if _pre - _k in _first:\n"
            "            _best = max(_best, _i - _first[_pre - _k])\n        if _pre not in _first:\n"
            "            _first[_pre] = _i\n    return _best"),
           # jump game : peut-on atteindre le dernier index (glouton, portée max courante) — gap_probe 15ᵉ vague.
           ("jump_game",
            "    _reach = 0\n    for _i, _v in enumerate(args[0]):\n        if _i > _reach:\n            return False\n"
            "        _reach = max(_reach, _i + _v)\n    return True"),
           # station-service : index de départ pour boucler le circuit, sinon -1 (glouton) — 15ᵉ vague.
           ("gas_station",
            "    _gas, _cost = args[0], args[1]\n    if sum(_gas) < sum(_cost):\n        return -1\n"
            "    _start = 0\n    _tank = 0\n    for _i in range(len(_gas)):\n        _tank += _gas[_i] - _cost[_i]\n"
            "        if _tank < 0:\n            _start = _i + 1\n            _tank = 0\n    return _start"),
           # min de carrés parfaits sommant à n (DP) — gap_probe 16ᵉ vague.
           ("min_perfect_squares",
            "    _n = args[0]\n    _dp = [0] + [float('inf')] * _n\n    for _i in range(1, _n + 1):\n        _j = 1\n"
            "        while _j * _j <= _i:\n            _dp[_i] = min(_dp[_i], _dp[_i - _j * _j] + 1)\n            _j += 1\n"
            "    return _dp[_n]"),
           # aire du plus grand carré de 1 dans une grille binaire (DP) — 16ᵉ vague.
           ("maximal_square",
            "    _g = args[0]\n    if not _g or not _g[0]:\n        return 0\n    _R, _C = len(_g), len(_g[0])\n"
            "    _dp = [[0] * _C for _ in range(_R)]\n    _best = 0\n    for _i in range(_R):\n        for _j in range(_C):\n"
            "            if _g[_i][_j] == 1:\n                _dp[_i][_j] = 1 if _i == 0 or _j == 0 else"
            " min(_dp[_i-1][_j], _dp[_i][_j-1], _dp[_i-1][_j-1]) + 1\n                _best = max(_best, _dp[_i][_j])\n"
            "    return _best * _best"),
           # récipient le plus grand (deux pointeurs, aire = min(h)*largeur) — 16ᵉ vague.
           ("container_with_most_water",
            "    _h = args[0]\n    _l, _r = 0, len(_h) - 1\n    _best = 0\n    while _l < _r:\n"
            "        _best = max(_best, min(_h[_l], _h[_r]) * (_r - _l))\n"
            "        if _h[_l] < _h[_r]:\n            _l += 1\n        else:\n            _r -= 1\n    return _best"),
           # plus longue sous-chaîne sans caractère répété (fenêtre glissante) — 16ᵉ vague.
           ("longest_substring_without_repeat",
            "    _s = args[0]\n    _seen = {}\n    _start = 0\n    _best = 0\n    for _i, _c in enumerate(_s):\n"
            "        if _c in _seen and _seen[_c] >= _start:\n            _start = _seen[_c] + 1\n"
            "        _seen[_c] = _i\n        _best = max(_best, _i - _start + 1)\n    return _best"),
           # sauts minimaux pour atteindre la fin (greedy par niveaux BFS) — gap_probe 17ᵉ vague.
           ("min_jumps",
            "    _nums = args[0]\n    _jumps = 0\n    _cur_end = 0\n    _far = 0\n    for _i in range(len(_nums) - 1):\n"
            "        _far = max(_far, _i + _nums[_i])\n        if _i == _cur_end:\n            _jumps += 1\n"
            "            _cur_end = _far\n    return _jumps"),
           # bonbons : min total, chaque enfant >= 1, plus que ses voisins de note inférieure (deux passes) — 17ᵉ vague.
           ("candy",
            "    _r = args[0]\n    _n = len(_r)\n    _c = [1] * _n\n    for _i in range(1, _n):\n"
            "        if _r[_i] > _r[_i-1]:\n            _c[_i] = _c[_i-1] + 1\n    for _i in range(_n - 2, -1, -1):\n"
            "        if _r[_i] > _r[_i+1]:\n            _c[_i] = max(_c[_i], _c[_i+1] + 1)\n    return sum(_c)"),
           # entrelacement : s3 est-il un mélange de s1 et s2 en préservant l'ordre (DP 2D) — 17ᵉ vague.
           ("interleaving_string",
            "    _s1, _s2, _s3 = args[0], args[1], args[2]\n    if len(_s1) + len(_s2) != len(_s3):\n        return False\n"
            "    _m, _n = len(_s1), len(_s2)\n    _dp = [[False] * (_n + 1) for _ in range(_m + 1)]\n    _dp[0][0] = True\n"
            "    for _i in range(_m + 1):\n        for _j in range(_n + 1):\n"
            "            if _i > 0 and _s1[_i-1] == _s3[_i+_j-1]:\n                _dp[_i][_j] = _dp[_i][_j] or _dp[_i-1][_j]\n"
            "            if _j > 0 and _s2[_j-1] == _s3[_i+_j-1]:\n                _dp[_i][_j] = _dp[_i][_j] or _dp[_i][_j-1]\n"
            "    return _dp[_m][_n]"),
           # plus longue plage d'une même lettre après <= k remplacements (fenêtre glissante) — 17ᵉ vague.
           ("longest_repeating_char_replace",
            "    _s, _k = args[0], args[1]\n    _count = {}\n    _left = 0\n    _maxf = 0\n    _best = 0\n"
            "    for _right in range(len(_s)):\n        _count[_s[_right]] = _count.get(_s[_right], 0) + 1\n"
            "        _maxf = max(_maxf, _count[_s[_right]])\n        while (_right - _left + 1) - _maxf > _k:\n"
            "            _count[_s[_left]] -= 1\n            _left += 1\n        _best = max(_best, _right - _left + 1)\n    return _best"),
           # k éléments les plus fréquents (fréquence décroissante, valeur croissante en cas d'égalité) — 17ᵉ vague.
           ("top_k_frequent",
            "    from collections import Counter\n    _cnt = Counter(args[0])\n"
            "    _items = sorted(_cnt.items(), key=lambda _x: (-_x[1], _x[0]))\n    return [_v for _v, _ in _items[:args[1]]]"),
           # une étape du Jeu de la Vie de Conway sur grille binaire bornée — gap_probe 18ᵉ vague.
           ("game_of_life_alive",
            "    _g = args[0]\n    _R, _C = len(_g), len(_g[0])\n    _res = [[0] * _C for _ in range(_R)]\n"
            "    for _i in range(_R):\n        for _j in range(_C):\n"
            "            _n = sum(_g[_i+_di][_j+_dj] for _di in (-1, 0, 1) for _dj in (-1, 0, 1)\n"
            "                     if (_di or _dj) and 0 <= _i+_di < _R and 0 <= _j+_dj < _C)\n"
            "            _res[_i][_j] = 1 if (_g[_i][_j] and _n in (2, 3)) or (not _g[_i][_j] and _n == 3) else 0\n"
            "    return _res"),
           # étiquettes de partition : tailles des tranches où chaque lettre reste confinée (greedy dernière occurrence) — 19ᵉ vague.
           ("partition_labels",
            "    _last = {_c: _i for _i, _c in enumerate(args[0])}\n    _res = []\n    _start = _end = 0\n"
            "    for _i, _c in enumerate(args[0]):\n        _end = max(_end, _last[_c])\n        if _i == _end:\n"
            "            _res.append(_i - _start + 1)\n            _start = _i + 1\n    return _res"),
           # profit boursier avec AU PLUS 2 transactions (DP à 4 états) — 19ᵉ vague.
           ("max_profit_2_transactions",
            "    _buy1 = _buy2 = float('-inf')\n    _sell1 = _sell2 = 0\n    for _p in args[0]:\n"
            "        _buy1 = max(_buy1, -_p)\n        _sell1 = max(_sell1, _buy1 + _p)\n"
            "        _buy2 = max(_buy2, _sell1 - _p)\n        _sell2 = max(_sell2, _buy2 + _p)\n    return _sell2"),
           # peinture de maisons : coût min sans deux voisins de même couleur (DP 3 états) — 19ᵉ vague.
           # NB anti-coïncidence : ce N'EST PAS « somme des min de lignes » (qui ignore la contrainte voisins).
           ("paint_house",
            "    _costs = args[0]\n    if not _costs:\n        return 0\n    _prev = list(_costs[0])\n"
            "    for _i in range(1, len(_costs)):\n        _cur = [_costs[_i][0] + min(_prev[1], _prev[2]),\n"
            "                _costs[_i][1] + min(_prev[0], _prev[2]),\n"
            "                _costs[_i][2] + min(_prev[0], _prev[1])]\n        _prev = _cur\n    return min(_prev)"),
           # longueur de la plus longue sous-séquence en ZIGZAG (wiggle) — gap_probe 21ᵉ vague.
           ("wiggle_max_length",
            "    _nums = args[0]\n    if len(_nums) < 2:\n        return len(_nums)\n    _up = _down = 1\n"
            "    for _i in range(1, len(_nums)):\n        if _nums[_i] > _nums[_i-1]:\n            _up = _down + 1\n"
            "        elif _nums[_i] < _nums[_i-1]:\n            _down = _up + 1\n    return max(_up, _down)"),
           # rendu de monnaie à la limonade (billets 5/10/20, glouton) — gap_probe 21ᵉ vague.
           ("lemonade_change",
            "    _five = _ten = 0\n    for _b in args[0]:\n        if _b == 5:\n            _five += 1\n"
            "        elif _b == 10:\n            if _five == 0:\n                return False\n            _five -= 1\n"
            "            _ten += 1\n        else:\n            if _ten > 0 and _five > 0:\n                _ten -= 1\n"
            "                _five -= 1\n            elif _five >= 3:\n                _five -= 3\n"
            "            else:\n                return False\n    return True"),
           # découpe de barre : revenu max (prices[i] = prix de la longueur i+1), DP — gap_probe 22ᵉ vague.
           ("rod_cutting",
            "    _p = args[0]\n    _n = len(_p)\n    _dp = [0] * (_n + 1)\n    for _i in range(1, _n + 1):\n"
            "        _dp[_i] = max(_p[_j] + _dp[_i - _j - 1] for _j in range(_i))\n    return _dp[_n]"),
           # nombre minimal de coupes pour partitionner s en palindromes (DP) — gap_probe 22ᵉ vague.
           ("min_palindrome_cuts",
            "    _s = args[0]\n    _n = len(_s)\n    if _n == 0:\n        return 0\n"
            "    _pal = [[False] * _n for _ in range(_n)]\n    for _i in range(_n):\n        _pal[_i][_i] = True\n"
            "    for _L in range(2, _n + 1):\n        for _i in range(_n - _L + 1):\n            _j = _i + _L - 1\n"
            "            if _s[_i] == _s[_j] and (_L == 2 or _pal[_i+1][_j-1]):\n                _pal[_i][_j] = True\n"
            "    _cut = [0] * _n\n    for _i in range(_n):\n        if _pal[0][_i]:\n            _cut[_i] = 0\n"
            "        else:\n            _cut[_i] = min(_cut[_j] + 1 for _j in range(_i) if _pal[_j+1][_i])\n    return _cut[_n-1]"),
           # entiers MANQUANTS dans 1..n (n = longueur), liste triée — gap_probe 23ᵉ vague.
           ("find_disappeared_numbers",
            "    _n = len(args[0])\n    _vus = set(args[0])\n    return [_x for _x in range(1, _n + 1) if _x not in _vus]"),
           # découpe d'un entier en somme d'au moins 2 entiers, PRODUIT max (DP) — gap_probe 24ᵉ vague.
           ("integer_break",
            "    _dp = [0, 1] + [0] * (args[0] - 1)\n    for _i in range(2, args[0] + 1):\n        for _j in range(1, _i):\n"
            "            _dp[_i] = max(_dp[_i], _j * (_i - _j), _j * _dp[_i - _j])\n    return _dp[args[0]]"),
           # n-ième nombre LAID (facteurs 2/3/5) par DP à 3 pointeurs — gap_probe 24ᵉ vague.
           ("nth_ugly_number",
            "    _ugly = [1]\n    _i2 = _i3 = _i5 = 0\n    while len(_ugly) < args[0]:\n"
            "        _nxt = min(_ugly[_i2]*2, _ugly[_i3]*3, _ugly[_i5]*5)\n        _ugly.append(_nxt)\n"
            "        if _nxt == _ugly[_i2]*2:\n            _i2 += 1\n        if _nxt == _ugly[_i3]*3:\n            _i3 += 1\n"
            "        if _nxt == _ugly[_i5]*5:\n            _i5 += 1\n    return _ugly[args[0]-1]"),
           # indice d'un PIC (élément >= ses voisins ; premier trouvé) — gap_probe 24ᵉ vague.
           ("find_peak_element",
            "    _n = len(args[0])\n    for _i in range(_n):\n"
            "        if (_i == 0 or args[0][_i] > args[0][_i-1]) and (_i == _n-1 or args[0][_i] > args[0][_i+1]):\n"
            "            return _i\n    return -1"),
           # plages-résumé d'une liste triée : '0->2', '4', … (gap_probe 24ᵉ vague).
           ("summary_ranges",
            "    _nums = args[0]\n    _res = []\n    _i = 0\n    _n = len(_nums)\n    while _i < _n:\n        _j = _i\n"
            "        while _j + 1 < _n and _nums[_j+1] == _nums[_j] + 1:\n            _j += 1\n        if _i == _j:\n"
            "            _res.append(str(_nums[_i]))\n        else:\n"
            "            _res.append(str(_nums[_i]) + '->' + str(_nums[_j]))\n        _i = _j + 1\n    return _res"),
           # indices de début des ANAGRAMMES de p dans s (fenêtre + Counter) — gap_probe 24ᵉ vague.
           ("find_anagram_indices",
            "    from collections import Counter\n    _s, _p = args[0], args[1]\n    _pl = len(_p)\n"
            "    _pc = Counter(_p)\n    _res = []\n    for _i in range(len(_s) - _pl + 1):\n"
            "        if Counter(_s[_i:_i+_pl]) == _pc:\n            _res.append(_i)\n    return _res"),
           # CAMBRIOLEUR CIRCULAIRE : max non-adjacents, 1er et dernier sont voisins (2 passes linéaires) — 25ᵉ vague.
           ("house_robber_circular",
            "    _n = args[0]\n    if len(_n) == 1:\n        return _n[0]\n    def _rob(_a):\n        _p = _c = 0\n"
            "        for _x in _a:\n            _p, _c = _c, max(_c, _p + _x)\n        return _c\n"
            "    return max(_rob(_n[1:]), _rob(_n[:-1]))"),
           # nombre de façons d'assigner +/- pour atteindre la cible (DP sur sommes) — gap_probe 25ᵉ vague.
           ("target_sum_ways",
            "    from collections import defaultdict\n    _dp = defaultdict(int)\n    _dp[0] = 1\n"
            "    for _x in args[0]:\n        _nd = defaultdict(int)\n        for _s, _cnt in _dp.items():\n"
            "            _nd[_s + _x] += _cnt\n            _nd[_s - _x] += _cnt\n        _dp = _nd\n    return _dp[args[1]]"),
           # nb de sous-tableaux contigus de PRODUIT < k (fenêtre glissante) — gap_probe 25ᵉ vague.
           ("subarray_product_less_than_k",
            "    _nums, _k = args[0], args[1]\n    if _k <= 1:\n        return 0\n    _prod = 1\n    _left = 0\n    _cnt = 0\n"
            "    for _right in range(len(_nums)):\n        _prod *= _nums[_right]\n        while _prod >= _k:\n"
            "            _prod //= _nums[_left]\n            _left += 1\n        _cnt += _right - _left + 1\n    return _cnt"),
           # ORANGES POURRIES : minutes pour tout pourrir (BFS multi-source), -1 si impossible — gap_probe 25ᵉ vague.
           ("rotting_oranges",
            "    from collections import deque\n    _g = [list(_r) for _r in args[0]]\n    _R, _C = len(_g), len(_g[0])\n"
            "    _q = deque()\n    _fresh = 0\n    for _i in range(_R):\n        for _j in range(_C):\n"
            "            if _g[_i][_j] == 2:\n                _q.append((_i, _j, 0))\n"
            "            elif _g[_i][_j] == 1:\n                _fresh += 1\n    _t = 0\n    while _q:\n"
            "        _i, _j, _t = _q.popleft()\n        for _di, _dj in ((1,0),(-1,0),(0,1),(0,-1)):\n"
            "            _x, _y = _i+_di, _j+_dj\n"
            "            if 0 <= _x < _R and 0 <= _y < _C and _g[_x][_y] == 1:\n                _g[_x][_y] = 2\n"
            "                _fresh -= 1\n                _q.append((_x, _y, _t+1))\n    return _t if _fresh == 0 else -1"),
           # plus longue MONTAGNE (monte puis descend) — gap_probe 25ᵉ vague.
           ("longest_mountain",
            "    _arr = args[0]\n    _n = len(_arr)\n    _best = 0\n    _i = 1\n    while _i < _n - 1:\n"
            "        if _arr[_i-1] < _arr[_i] > _arr[_i+1]:\n            _l = _i - 1\n"
            "            while _l > 0 and _arr[_l-1] < _arr[_l]:\n                _l -= 1\n            _r = _i + 1\n"
            "            while _r < _n - 1 and _arr[_r] > _arr[_r+1]:\n                _r += 1\n"
            "            _best = max(_best, _r - _l + 1)\n            _i = _r + 1\n        else:\n            _i += 1\n    return _best"),
           # PLUS UN sur un nombre représenté en liste de chiffres — gap_probe 26ᵉ vague.
           ("plus_one",
            "    _d = list(args[0])\n    _i = len(_d) - 1\n    while _i >= 0:\n        if _d[_i] < 9:\n"
            "            _d[_i] += 1\n            return _d\n        _d[_i] = 0\n        _i -= 1\n    return [1] + _d"),
           # POUSSER les zéros en fin (ordre des non-nuls préservé) — gap_probe 26ᵉ vague.
           ("move_zeroes",
            "    _nz = [_x for _x in args[0] if _x != 0]\n    return _nz + [0] * (len(args[0]) - len(_nz))"),
           # indice PIVOT (somme gauche == somme droite), -1 sinon — gap_probe 26ᵉ vague.
           ("find_pivot_index",
            "    _total = sum(args[0])\n    _left = 0\n    for _i, _x in enumerate(args[0]):\n"
            "        if _left == _total - _left - _x:\n            return _i\n        _left += _x\n    return -1"),
           # somme min d'un chemin DESCENDANT dans une grille (DP) — gap_probe 26ᵉ vague.
           ("min_falling_path_sum",
            "    _g = [list(_r) for _r in args[0]]\n    _R, _C = len(_g), len(_g[0])\n    for _i in range(1, _R):\n"
            "        for _j in range(_C):\n            _best = _g[_i-1][_j]\n            if _j > 0:\n"
            "                _best = min(_best, _g[_i-1][_j-1])\n            if _j < _C - 1:\n"
            "                _best = min(_best, _g[_i-1][_j+1])\n            _g[_i][_j] += _best\n    return min(_g[_R-1])"),
           # plus court sous-tableau à TRIER pour que tout soit trié (bornes via tableau trié) — gap_probe 27ᵉ vague.
           ("shortest_unsorted_subarray",
            "    _xs = args[0]\n    _s = sorted(_xs)\n"
            "    _lo = next((_i for _i in range(len(_xs)) if _xs[_i] != _s[_i]), None)\n"
            "    if _lo is None:\n        return 0\n"
            "    _hi = next(_i for _i in range(len(_xs) - 1, -1, -1) if _xs[_i] != _s[_i])\n    return _hi - _lo + 1"),
           # distance MAX au siège occupé le plus proche (bords + milieu des trous) — gap_probe 27ᵉ vague.
           ("max_distance_to_closest",
            "    _s = args[0]\n    _occ = [_i for _i, _v in enumerate(_s) if _v == 1]\n    _best = _occ[0]\n"
            "    for _i in range(1, len(_occ)):\n        _best = max(_best, (_occ[_i] - _occ[_i - 1]) // 2)\n"
            "    return max(_best, len(_s) - 1 - _occ[-1])"),
           # h-index : max h tel qu'au moins h articles ont >= h citations (tri décroissant) — gap_probe 28ᵉ vague.
           ("h_index",
            "    _c = sorted(args[0], reverse=True)\n    _h = 0\n    for _i, _v in enumerate(_c):\n"
            "        if _v >= _i + 1:\n            _h = _i + 1\n        else:\n            break\n    return _h"),
           # plus petit entier POSITIF absent (ensemble + balayage depuis 1) — gap_probe 28ᵉ vague.
           ("first_missing_positive",
            "    _s = set(args[0])\n    _i = 1\n    while _i in _s:\n        _i += 1\n    return _i"),
           # les DEUX éléments uniques (les autres en double), triés croissant — gap_probe 30ᵉ vague.
           ("single_number_iii",
            "    from collections import Counter\n"
            "    return sorted(_k for _k, _v in Counter(args[0]).items() if _v == 1)"),
           # coups min pour égaliser (chaque coup +1 à n-1 éléments) = somme - n*min — gap_probe 30ᵉ vague.
           ("min_moves",
            "    return sum(args[0]) - len(args[0]) * min(args[0])"),
           # tableau MONOTONE (croissant OU décroissant) — gap_probe 32ᵉ vague.
           ("monotonic",
            "    _a = args[0]\n    _inc = all(_a[_i] <= _a[_i + 1] for _i in range(len(_a) - 1))\n"
            "    _dec = all(_a[_i] >= _a[_i + 1] for _i in range(len(_a) - 1))\n    return _inc or _dec"),
           # PÉRIMÈTRE de l'île (4 par cellule terre, -2 par arête partagée) — gap_probe 32ᵉ vague.
           ("island_perimeter",
            "    _g = args[0]\n    _R, _C = len(_g), len(_g[0])\n    _p = 0\n"
            "    for _i in range(_R):\n        for _j in range(_C):\n            if _g[_i][_j] == 1:\n"
            "                _p += 4\n                if _i > 0 and _g[_i - 1][_j] == 1:\n                    _p -= 2\n"
            "                if _j > 0 and _g[_i][_j - 1] == 1:\n                    _p -= 2\n    return _p"),
           # SET MISMATCH : [le doublon, le manquant] dans une permutation 1..n abîmée — gap_probe 32ᵉ vague.
           ("set_mismatch",
            "    from collections import Counter\n    _c = Counter(args[0])\n    _n = len(args[0])\n"
            "    _dup = next(_k for _k, _v in _c.items() if _v == 2)\n"
            "    _miss = next(_x for _x in range(1, _n + 1) if _x not in _c)\n    return [_dup, _miss]"),
           # produit MAX de trois éléments (max des 3 plus grands OU 2 plus négatifs × le plus grand) — gap_probe 32ᵉ vague.
           ("maximum_product_of_three",
            "    _a = sorted(args[0])\n    return max(_a[-1] * _a[-2] * _a[-3], _a[0] * _a[1] * _a[-1])"),
           # ARRAY PAIR SUM : somme des min de paires = somme des éléments de rang pair (trié) — gap_probe 32ᵉ vague.
           ("array_pair_sum",
            "    return sum(sorted(args[0])[::2])"),
           # FIND LUCKY : plus grand v dont la fréquence == v, sinon -1 — gap_probe 32ᵉ vague.
           ("find_lucky",
            "    from collections import Counter\n    _c = Counter(args[0])\n"
            "    _g = [_v for _v, _n in _c.items() if _v == _n]\n    return max(_g) if _g else -1"),
           # HEIGHT CHECKER : nb de positions différentes de la version triée — gap_probe 32ᵉ vague.
           ("height_checker",
            "    return sum(_x != _y for _x, _y in zip(args[0], sorted(args[0])))"),
           # TRI PAR PARITÉ : pairs (ordre préservé) puis impairs — gap_probe 33ᵉ vague.
           ("sort_array_by_parity",
            "    _a = args[0]\n    return [_x for _x in _a if _x % 2 == 0] + [_x for _x in _a if _x % 2 == 1]"),
           # TABLEAU MONTAGNE VALIDE : strictement monte puis descend, sommet hors bords — gap_probe 33ᵉ vague.
           ("valid_mountain_array",
            "    _a = args[0]\n    _n = len(_a)\n    if _n < 3:\n        return False\n    _i = 0\n"
            "    while _i + 1 < _n and _a[_i] < _a[_i + 1]:\n        _i += 1\n"
            "    if _i == 0 or _i == _n - 1:\n        return False\n"
            "    while _i + 1 < _n and _a[_i] > _a[_i + 1]:\n        _i += 1\n    return _i == _n - 1"),
           # NB de négatifs dans une grille — gap_probe 33ᵉ vague.
           ("count_negatives",
            "    return sum(1 for _row in args[0] for _x in _row if _x < 0)"),
           # plus grand PÉRIMÈTRE de triangle valide (tri décroissant, 1ʳᵉ triplette valide) — gap_probe 33ᵉ vague.
           ("largest_perimeter_triangle",
            "    _a = sorted(args[0], reverse=True)\n    for _i in range(len(_a) - 2):\n"
            "        if _a[_i + 1] + _a[_i + 2] > _a[_i]:\n            return _a[_i] + _a[_i + 1] + _a[_i + 2]\n    return 0"),
           # remplacer chaque élément par le plus grand à sa DROITE (-1 pour le dernier) — gap_probe 33ᵉ vague.
           ("replace_elements_with_greatest_on_right",
            "    _a = args[0]\n    _r = [-1] * len(_a)\n    _m = -1\n"
            "    for _i in range(len(_a) - 1, -1, -1):\n        _r[_i] = _m\n        _m = max(_m, _a[_i])\n    return _r"),
           # produit des 2 plus grands MOINS produit des 2 plus petits — gap_probe 34ᵉ vague.
           ("max_product_difference",
            "    _a = sorted(args[0])\n    return _a[-1] * _a[-2] - _a[0] * _a[1]"),
           # somme MAX d'un sous-tableau strictement croissant CONTIGU — gap_probe 34ᵉ vague.
           ("max_ascending_sum",
            "    _a = args[0]\n    _best = _cur = _a[0]\n    for _i in range(1, len(_a)):\n"
            "        _cur = _cur + _a[_i] if _a[_i] > _a[_i - 1] else _a[_i]\n        _best = max(_best, _cur)\n    return _best"),
           # nb de bonnes paires i<j avec a[i]==a[j] (somme des C(v,2)) — gap_probe 34ᵉ vague.
           ("count_good_pairs",
            "    from collections import Counter\n    return sum(_v * (_v - 1) // 2 for _v in Counter(args[0]).values())"),
           # somme des éléments apparaissant EXACTEMENT une fois — gap_probe 34ᵉ vague.
           ("sum_of_unique",
            "    from collections import Counter\n    return sum(_k for _k, _v in Counter(args[0]).items() if _v == 1)"),
           # altitude MAX (somme de préfixe à partir de 0) — gap_probe 34ᵉ vague.
           ("largest_altitude",
            "    _h = _best = 0\n    for _x in args[0]:\n        _h += _x\n        _best = max(_best, _h)\n    return _best"),
           # plus petite sous-séquence (tri décroissant) dont la somme dépasse STRICTEMENT le reste — gap_probe 34ᵉ vague.
           ("min_subsequence",
            "    _a = sorted(args[0], reverse=True)\n    _tot = sum(_a)\n    _s = 0\n    _r = []\n"
            "    for _x in _a:\n        _s += _x\n        _r.append(_x)\n        if _s > _tot - _s:\n            break\n    return _r"),
           # le tableau trié forme-t-il une PROGRESSION ARITHMÉTIQUE — gap_probe 35ᵉ vague.
           ("can_make_arithmetic_progression",
            "    _a = sorted(args[0])\n    _d = _a[1] - _a[0] if len(_a) > 1 else 0\n"
            "    return all(_a[_i + 1] - _a[_i] == _d for _i in range(len(_a) - 1))"),
           # trois IMPAIRS consécutifs présents — gap_probe 35ᵉ vague.
           ("three_consecutive_odds",
            "    _a = args[0]\n    return any(_a[_i] % 2 and _a[_i + 1] % 2 and _a[_i + 2] % 2 for _i in range(len(_a) - 2))"),
           # plus grand nombre apparaissant EXACTEMENT une fois, sinon -1 — gap_probe 35ᵉ vague.
           ("largest_unique_number",
            "    from collections import Counter\n    _u = [_k for _k, _v in Counter(args[0]).items() if _v == 1]\n"
            "    return max(_u) if _u else -1"),
           # nb de nombres ayant un nombre PAIR de chiffres — gap_probe 35ᵉ vague.
           ("find_numbers_with_even_digits",
            "    return sum(1 for _x in args[0] if len(str(_x)) % 2 == 0)"),
           # nb de sous-tableaux contigus (len>=3) en progression arithmétique — gap_probe 35ᵉ vague.
           ("number_of_arithmetic_slices",
            "    _a = args[0]\n    _cnt = _cur = 0\n    for _i in range(2, len(_a)):\n"
            "        if _a[_i] - _a[_i - 1] == _a[_i - 1] - _a[_i - 2]:\n            _cur += 1\n            _cnt += _cur\n"
            "        else:\n            _cur = 0\n    return _cnt"),
           # incréments min pour rendre STRICTEMENT croissant — gap_probe 35ᵉ vague.
           ("min_operations",
            "    _a = args[0]\n    _ops = 0\n    _prev = _a[0]\n    for _i in range(1, len(_a)):\n"
            "        if _a[_i] <= _prev:\n            _ops += _prev + 1 - _a[_i]\n            _prev = _prev + 1\n"
            "        else:\n            _prev = _a[_i]\n    return _ops"),
           # somme de TOUS les sous-tableaux contigus de longueur IMPAIRE — gap_probe 35ᵉ vague.
           ("sum_odd_length_subarrays",
            "    _a = args[0]\n    _n = len(_a)\n    _tot = 0\n    for _i in range(_n):\n        for _j in range(_i, _n):\n"
            "            if (_j - _i + 1) % 2 == 1:\n                _tot += sum(_a[_i:_j + 1])\n    return _tot"),
           # COÛT MIN d'escalier (payer step i, monter de 1 ou 2 ; départ libre 0/1) — gap_probe 38ᵉ vague.
           ("min_cost_climbing_stairs",
            "    _c = args[0]\n    _a = _b = 0\n    for _i in range(2, len(_c) + 1):\n"
            "        _a, _b = _b, min(_b + _c[_i - 1], _a + _c[_i - 2])\n    return _b"),
           # peut-on planter n fleurs sans 2 adjacentes (greedy, bords vides) — gap_probe 40ᵉ vague.
           ("can_place_flowers",
            "    _b = [0] + list(args[0]) + [0]\n    _c = 0\n    for _i in range(1, len(_b) - 1):\n"
            "        if _b[_i - 1] == 0 and _b[_i] == 0 and _b[_i + 1] == 0:\n            _b[_i] = 1\n            _c += 1\n"
            "    return _c >= args[1]"),
           # nb MIN de sauts pour atteindre la fin (greedy BFS O(n)) -> évite le gouffre means-end ~19.5k cand — 42ᵉ vague.
           ("jump_game_ii",
            "    _f = _e = _j = 0\n    for _i in range(len(args[0]) - 1):\n        _f = max(_f, _i + args[0][_i])\n"
            "        if _i == _e:\n            _j += 1\n            _e = _f\n    return _j"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.TAB]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.TAB)


class GenerateurNumerique:
    """
    RÉDUCTIONS NUMÉRIQUES (2026-06-19, gap_probe 6ᵉ vague, faculté « calcul »). NOUVEAU : `pli` ne replie qu'avec des
    ops binaires confirmées (add/mul/…) ; ces réductions ont une RÈGLE propre que le pli n'atteint pas.
      - horner(coeffs, x) : évaluation d'un polynôme par schéma de Horner (r = r·x + coeff), coeffs du + significatif
        au moins significatif.
      - lcm_list(xs) : PPCM de toute la liste (repli via le PGCD).
    Borné (2), honnête (entiers)."""

    NUM = (("horner", "    _r = 0\n    for _c in args[0]:\n        _r = _r * args[1] + _c\n    return _r"),
           ("lcm_list",
            "    import math\n    _r = 1\n    for _x in args[0]:\n        _r = _r * _x // math.gcd(_r, _x)\n    return _r"),
           ("josephus",
            "    _r = 0\n    for _i in range(2, args[0] + 1):\n        _r = (_r + args[1]) % _i\n    return _r"),
           ("dot3d", "    return sum(_x * _y for _x, _y in zip(args[0], args[1]))"),
           # produit VECTORIEL 3D (a × b) — gap_probe 18ᵉ vague.
           ("cross_product_3d",
            "    _a, _b = args[0], args[1]\n    return [_a[1]*_b[2] - _a[2]*_b[1], _a[2]*_b[0] - _a[0]*_b[2],"
            " _a[0]*_b[1] - _a[1]*_b[0]]"),
           # distance euclidienne AU CARRÉ entre deux points (entier exact) — 18ᵉ vague.
           ("dist_squared_3d", "    return sum((_x - _y) ** 2 for _x, _y in zip(args[0], args[1]))"),
           # DÉTERMINANT entier d'une matrice n×n par élimination FRACTION-FREE de Bareiss (reste exact) — 13ᵉ vague.
           ("determinant_int",
            "    _m = [list(_r) for _r in args[0]]\n    _n = len(_m)\n    _sign = 1\n    _prev = 1\n"
            "    for _i in range(_n - 1):\n        if _m[_i][_i] == 0:\n"
            "            _sw = next((_r for _r in range(_i + 1, _n) if _m[_r][_i] != 0), None)\n"
            "            if _sw is None:\n                return 0\n            _m[_i], _m[_sw] = _m[_sw], _m[_i]\n"
            "            _sign = -_sign\n        for _r in range(_i + 1, _n):\n            for _c in range(_i + 1, _n):\n"
            "                _m[_r][_c] = (_m[_r][_c] * _m[_i][_i] - _m[_r][_i] * _m[_i][_c]) // _prev\n"
            "        _prev = _m[_i][_i]\n    return _sign * _m[_n - 1][_n - 1]"),
           # PGCD de toute une liste (repli par math.gcd) — gap_probe 14ᵉ vague.
           ("gcd_list", "    import math\n    _r = 0\n    for _x in args[0]:\n        _r = math.gcd(_r, _x)\n    return _r"),
           # numéro de colonne Excel (base-26 BIJECTIVE) : "A"->1, "AB"->28 — gap_probe 19ᵉ vague.
           ("excel_column_number",
            "    _r = 0\n    for _c in args[0]:\n        _r = _r * 26 + (ord(_c) - 64)\n    return _r"),
           # n-ième chiffre (1-indexé) de la suite 1234567891011… (par largeur de palier) — gap_probe 27ᵉ vague.
           ("nth_digit",
            "    _n = args[0]\n    _d = 1\n    _count = 9\n    _start = 1\n"
            "    while _n > _d * _count:\n        _n -= _d * _count\n        _d += 1\n        _count *= 10\n        _start *= 10\n"
            "    _num = _start + (_n - 1) // _d\n    return int(str(_num)[(_n - 1) % _d])"),
           # min d'opérations pour ramener n à 1 (÷2 si pair, ±1 si impair — règle des bits bas) — 27ᵉ vague.
           ("integer_replacement",
            "    _n = args[0]\n    _c = 0\n    while _n != 1:\n        if _n % 2 == 0:\n            _n //= 2\n"
            "        elif _n == 3 or _n % 4 == 1:\n            _n -= 1\n        else:\n            _n += 1\n"
            "        _c += 1\n    return _c"),
           # division entière TRONQUÉE vers zéro (signe par xor des signes) — gap_probe 27ᵉ vague.
           ("divide_integers",
            "    _a, _b = args[0], args[1]\n    _q = abs(_a) // abs(_b)\n"
            "    return _q if (_a < 0) == (_b < 0) else -_q"),
           # ÉCHANGE MAXIMAL : un seul swap de deux chiffres pour le plus grand nombre (glouton) — gap_probe 29ᵉ vague.
           ("maximum_swap",
            "    _d = list(str(args[0]))\n    _last = {_c: _i for _i, _c in enumerate(_d)}\n"
            "    for _i, _c in enumerate(_d):\n        for _x in '9876543210':\n"
            "            if _x > _c and _last.get(_x, -1) > _i:\n                _j = _last[_x]\n"
            "                _d[_i], _d[_j] = _d[_j], _d[_i]\n                return int(''.join(_d))\n    return args[0]"),
           # ARRANGE COINS : nb de rangées PLEINES d'un escalier de n pièces (1+2+…) — gap_probe 29ᵉ vague.
           ("arrange_coins",
            "    _n = args[0]\n    _k = 0\n    while _k + 1 <= _n:\n        _k += 1\n        _n -= _k\n    return _k"),
           # NB D'ÉTAPES pour réduire n à 0 (÷2 si pair, -1 si impair) — gap_probe 31ᵉ vague.
           ("number_of_steps",
            "    _n = args[0]\n    _c = 0\n    while _n:\n        _n = _n // 2 if _n % 2 == 0 else _n - 1\n"
            "        _c += 1\n    return _c"),
           # NB d'entiers IMPAIRS dans [low, high] — gap_probe 33ᵉ vague.
           ("count_odds",
            "    return (args[1] + 1) // 2 - args[0] // 2"),
           # CONVERSION en base 7 (chaîne, signe préservé) — gap_probe 37ᵉ vague.
           ("base_7",
            "    _n = args[0]\n    if _n == 0:\n        return '0'\n    _neg = _n < 0\n    _n = abs(_n)\n    _s = ''\n"
            "    while _n:\n        _s = str(_n % 7) + _s\n        _n //= 7\n    return '-' + _s if _neg else _s"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.NUM]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.NUM)


class GenerateurChecksum:
    """
    SOMMES DE CONTRÔLE / VALIDATION (2026-06-19, gap_probe 6ᵉ vague). NOUVEAU : aucun étage ne calcule une somme de
    contrôle à pondération positionnelle. ROBUSTESSE : luhn_valid était « résolu » par coïncidence via
    `predicat-mesures` sur un held-out faible -> ÉCHEC à froid sur un held-out durci (mesuré, HORS). On l'ancre ici
    en algorithme de 1ʳᵉ classe (donc PAS du masquage : l'autre voie n'était pas fiable).
      - luhn_valid(digits) : algorithme de Luhn (double un chiffre sur deux depuis la droite, retranche 9 si > 9,
        somme totale multiple de 10).
    Borné (1, graine d'un domaine extensible : ISBN, parité…), honnête (liste de chiffres)."""

    CHK = (("luhn_valid",
            "    _t = 0\n    for _i, _d in enumerate(reversed(args[0])):\n        if _i % 2 == 1:\n"
            "            _d *= 2\n            if _d > 9:\n                _d -= 9\n        _t += _d\n    return _t % 10 == 0"),)

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.CHK]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.CHK)


class GenerateurCombinatoire:
    """
    COMBINATOIRE GÉNÉRATIVE (2026-06-17, faculté « analyse/recherche ») — GÉNÉRER les structures combinatoires :
    toutes les permutations, tous les sous-ensembles (parties), le produit cartésien de deux listes. NOUVEAU :
    `comb` (math-avance) COMPTE C(n,k) ; ici on ÉNUMÈRE les structures. Borné (3), honnête (itertools en sandbox OK)."""

    COMB = (("permutations", "    import itertools\n    return [list(_p) for _p in itertools.permutations(args[0])]"),
            ("sous_ensembles", "    import itertools\n    return [list(_s) for _r in range(len(args[0]) + 1)"
                               " for _s in itertools.combinations(args[0], _r)]"),
            ("produit", "    import itertools\n    return [list(_p) for _p in itertools.product(args[0], args[1])]"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.COMB]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.COMB)


class GenerateurProfond:
    """RÉCURSION SUR STRUCTURE — réduit les FEUILLES d'une imbrication de profondeur ARBITRAIRE :
    `REDUC(feuilles(args[0]))` où `feuilles` descend récursivement dans les sous-listes. flatten_deep = list ;
    somme_deep = sum. Au-delà d'`imbrique` (qui n'aplatit qu'UN niveau). Borné (5 REDUC), honnête (sur des feuilles)."""

    REDUCS = (("list", "list(_f(args[0]))"), ("sum", "sum(_f(args[0]))"), ("max", "max(_f(args[0]))"),
              ("min", "min(_f(args[0]))"), ("count", "sum(1 for _ in _f(args[0]))"))
    _PRE = ("    def _f(_x):\n        for _e in _x:\n            if isinstance(_e, list):\n"
            "                yield from _f(_e)\n            else:\n                yield _e\n")

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{self._PRE}    return {corps}\n" for _, corps in self.REDUCS]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REDUCS)


class GenerateurFiltreSeuil:
    """FILTRE PARAMÉTRÉ — filtrer/réduire selon un seuil VENANT DE L'ENTRÉE (args[1]), pas d'un agrégat du tout :
    `REDUC(x for x in args[0] if x CMP args[1])`. count_above = sum(1 … if x > args[1]). Généralise `multipasse`
    (qui ne filtre que par un agrégat de la liste). Borné (|REDUC|·|CMP|), honnête (exige une 2ᵉ entrée).
    CMP couvre la famille COMPLÈTE des comparaisons, == / != inclus (compter/sommer les occurrences de la valeur
    interrogée args[1] — scalaire neuf que `group_by`/`dict-accu`, qui rendent un dict, ne mintent pas)."""

    CMPS = (">", "<", ">=", "<=", "==", "!=")
    REDUCS = ("sum(1 for x in args[0] if x {c} args[1])", "sum(x for x in args[0] if x {c} args[1])",
              "[x for x in args[0] if x {c} args[1]]")

    def __init__(self, cmps=None, seed: int = 0):
        self._cmps = tuple(cmps) if cmps is not None else self.CMPS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return {r.replace('{c}', cmp)}\n"
                 for cmp in self._cmps for r in self.REDUCS]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._cmps) * len(self.REDUCS)


class GenerateurMatriceReduce:
    """COMPOSITION 2D + REDUCE — réduire les agrégats de lignes/colonnes en UN scalaire :
    `REDUC(AGG(ligne) for ligne in AXE(m))`. max_row_sum = max(sum(r) for r in m). Empile matrice (par axe) ET
    une réduction — ce que `matrice` (qui rend la LISTE des agrégats) ne fait pas seul. Borné, honnête.
    DÉGÉNÉRÉS élagués (même précédent que `GenerateurFenetre`) : max∘max et min∘min — chaque élément appartient
    à exactement une ligne ET une colonne, donc max des max-de-ligne = max global (idem min), couvert par un étage
    plus simple. Jamais émis -> pas de poids mort. Reste 2 axes · (9 − 2) = 14 candidats."""

    AGGS = ("sum", "max", "min")
    REDUCS = ("max", "min", "sum")
    # (REDUC, AGG) tautologiques = max/min global, déjà couverts par un étage plus simple -> jamais émis.
    DEGENERES = frozenset({("max", "max"), ("min", "min")})

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for axe in ("args[0]", "zip(*args[0])"):
            for agg in self.AGGS:
                for reduc in self.REDUCS:
                    if (reduc, agg) in self.DEGENERES:
                        continue
                    cands.append(f"def {g}(*args, **kwargs):\n    return {reduc}({agg}(_l) for _l in {axe})\n")
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return (len(self.AGGS) * len(self.REDUCS) - len(self.DEGENERES)) * 2


class GenerateurDedup:
    """ÉTAT ENSEMBLISTE — parcourir en mémorisant les DÉJÀ-VUS : dedup_preserve (liste sans doublons, ordre gardé)
    ou nb_distinct (len(set)). Aucun étage ne déduplique en préservant l'ordre. Borné (2), honnête."""

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        dedup = (f"def {g}(*args, **kwargs):\n    _vu = set()\n    _out = []\n    for _x in args[0]:\n"
                 f"        if _x not in _vu:\n            _vu.add(_x)\n            _out.append(_x)\n    return _out\n")
        distinct = f"def {g}(*args, **kwargs):\n    return len(set(args[0]))\n"
        cands = [dedup, distinct]
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 2


class GenerateurPrefixeCommun:
    """RÉDUCTION CROISÉE DE CHAÎNES — plus long préfixe (ou suffixe) commun d'une LISTE de chaînes. Aucun étage ne
    réduit une liste de chaînes caractère par caractère. Borné (2), honnête (vide -> '')."""

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        pref = (f"def {g}(*args, **kwargs):\n    _s = args[0]\n    if not _s:\n        return ''\n    _p = _s[0]\n"
                f"    for _t in _s[1:]:\n        while not _t.startswith(_p):\n            _p = _p[:-1]\n"
                f"            if not _p:\n                return ''\n    return _p\n")
        suff = (f"def {g}(*args, **kwargs):\n    _s = args[0]\n    if not _s:\n        return ''\n    _p = _s[0]\n"
                f"    for _t in _s[1:]:\n        while not _t.endswith(_p):\n            _p = _p[1:]\n"
                f"            if not _p:\n                return ''\n    return _p\n")
        cands = [pref, suff]
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 2


class GenerateurMonnaie:
    """DP D'OPTIMISATION — rendu de monnaie : min de pièces pour atteindre args[1] avec les valeurs args[0]
    (-1 si impossible), ou possible (bool). Programmation dynamique 1D. Au-delà de generer-tester/while. Borné (2)."""

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        mincoins = (
            f"def {g}(*args, **kwargs):\n    _c, _m = args[0], args[1]\n    _inf = _m + 1\n"
            f"    _dp = [0] + [_inf] * _m\n    for _a in range(1, _m + 1):\n        for _p in _c:\n"
            f"            if _p <= _a and _dp[_a - _p] + 1 < _dp[_a]:\n                _dp[_a] = _dp[_a - _p] + 1\n"
            f"    return _dp[_m] if _dp[_m] <= _m else -1\n")
        possible = (
            f"def {g}(*args, **kwargs):\n    _c, _m = args[0], args[1]\n    _dp = [True] + [False] * _m\n"
            f"    for _a in range(1, _m + 1):\n        _dp[_a] = any(_p <= _a and _dp[_a - _p] for _p in _c)\n"
            f"    return _dp[_m]\n")
        # NOMBRE de FAÇONS (combinaisons, ordre indifférent) de rendre args[1] — DP par pièce (gap_probe 8ᵉ vague).
        ways = (
            f"def {g}(*args, **kwargs):\n    _c, _m = args[0], args[1]\n    _dp = [1] + [0] * _m\n"
            f"    for _p in _c:\n        for _a in range(_p, _m + 1):\n            _dp[_a] += _dp[_a - _p]\n"
            f"    return _dp[_m]\n")
        cands = [mincoins, possible, ways]
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 3


class GenerateurCesar:
    """CHIFFREMENTS SUR LETTRES — César sur a-z : décaler chaque lettre de args[1] (mod 26), chiffrer ou déchiffrer.
    ord/chr + modulo — au-delà du substrat (méthodes/littéraux). EXTENSION 2026-06-19 (9ᵉ vague) : ATBASH (réflexion
    a<->z, b<->y… ; chr(219 - ord) sur les lettres). Borné (3), honnête (sur des minuscules)."""

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        enc = (f"def {g}(*args, **kwargs):\n    return ''.join(chr((ord(_ch) - 97 + args[1]) % 26 + 97)"
               f" for _ch in args[0])\n")
        dec = (f"def {g}(*args, **kwargs):\n    return ''.join(chr((ord(_ch) - 97 - args[1]) % 26 + 97)"
               f" for _ch in args[0])\n")
        atb = (f"def {g}(*args, **kwargs):\n    return ''.join(chr(219 - ord(_ch)) if _ch.isalpha() else _ch"
               f" for _ch in args[0])\n")
        cands = [enc, dec, atb]
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 2


class GenerateurConjugaison:
    """
    CONJUGAISON (1ʳᵉ brique « FORME du langage » — 2026-06-18, défi Yohan « comprendre/ressortir le langage »).

    Le SENS ouvert n'a pas de juge mécanique (cf. mur de la NLP symbolique) ; la FORME, si : conjuguer est RÉGLÉ
    donc VÉRIFIABLE. La brique encode les RÈGLES (pas une liste de formes), prouvé par le held-out : elle conjugue
    des verbes JAMAIS vus. Signature : `conjugue(infinitif, temps, personne)` -> forme ; personne ∈ 0..5
    (je, tu, il, nous, vous, ils).

    Candidats à COMPLÉTUDE CROISSANTE (idiome `record`/`niveau_richesse` : le juge sélectionne le PLUS ÉTROIT
    correct, PAS de shuffle) : niveau 0 = présent ; 1 = +imparfait +futur ; 2 = +table irrégulière
    (être/avoir/aller au présent).

    PORTÉE HONNÊTE (bornée) : verbes du 1ᵉʳ groupe (-er) réguliers SANS alternance orthographique
    (manger/commencer/appeler HORS), aux temps présent/imparfait/futur, + 3 irréguliers fréquents au présent.
    Hors portée (groupes 2/3, autres temps) -> la brique propose une forme FAUSSE que le juge REJETTE via le
    held-out : jamais de faux « vérifié ».
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        head = f"def {g}(*args, **kwargs):\n    inf, t, p = args[0], args[1], args[2]\n"
        irr = ""
        if niveau >= 2:
            irr = ("    _irr = {('être', 'present'): ['suis', 'es', 'est', 'sommes', 'êtes', 'sont'],\n"
                   "            ('avoir', 'present'): ['ai', 'as', 'a', 'avons', 'avez', 'ont'],\n"
                   "            ('aller', 'present'): ['vais', 'vas', 'va', 'allons', 'allez', 'vont']}\n"
                   "    if (inf, t) in _irr:\n        return _irr[(inf, t)][p]\n")
        body = ("    rad = inf[:-2]\n"
                "    if t == 'present':\n        return rad + ['e', 'es', 'e', 'ons', 'ez', 'ent'][p]\n")
        if niveau >= 1:
            body += ("    if t == 'imparfait':\n        return rad + ['ais', 'ais', 'ait', 'ions', 'iez', 'aient'][p]\n"
                     "    if t == 'futur':\n        return inf + ['ai', 'as', 'a', 'ons', 'ez', 'ont'][p]\n")
        body += "    return ''\n"
        return head + irr + body

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        # Complétude CROISSANTE, PAS de shuffle : le juge garde le plus étroit qui passe (cf. record).
        cands = [self._src(g, niveau) for niveau in (0, 1, 2)]
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 3


class GenerateurConjugaison2:
    """
    CONJUGAISON GROUPE 2 (-ir en -iss-, 2026-06-18) — abat le mur `finir` documenté par valide_conjugaison (groupe 2
    = HORS pour la brique groupe 1). Rung suivant de l'échelle FORME : même nature (réglé donc vérifiable), règle
    différente (infixe -iss- au pluriel/imparfait). `conjugue(infinitif, temps, personne)`.

    PORTÉE HONNÊTE & LIMITE RÉVÉLÉE : ne couvre que le VRAI 2ᵉ groupe (finir, choisir, grandir…). Les -ir du 3ᵉ
    groupe (partir, venir, dormir) suivent un AUTRE schéma → la brique propose une forme FAUSSE rejetée par le juge.
    Distinguer 2ᵉ vs 3ᵉ groupe à la seule orthographe est IMPOSSIBLE par règle (info LEXICALE, à mémoriser) — c'est
    une frontière nette du model-free, que la carte des limites documente.
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        head = f"def {g}(*args, **kwargs):\n    inf, t, p = args[0], args[1], args[2]\n    rad = inf[:-2]\n"
        body = "    if t == 'present':\n        return rad + ['is', 'is', 'it', 'issons', 'issez', 'issent'][p]\n"
        if niveau >= 1:
            body += ("    if t == 'imparfait':\n"
                     "        return rad + ['issais', 'issais', 'issait', 'issions', 'issiez', 'issaient'][p]\n"
                     "    if t == 'futur':\n        return inf + ['ai', 'as', 'a', 'ons', 'ez', 'ont'][p]\n")
        return head + body + "    return ''\n"

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = list(dict.fromkeys(self._src(g, niveau) for niveau in (0, 1, 2)))
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 2


class GenerateurPasseCompose:
    """
    PASSÉ COMPOSÉ (rung FORME COMPOSÉ — 2026-06-18). Temps composé = auxiliaire AVOIR conjugué + participe passé.
    Réglé donc vérifiable : -er -> participe -é, -ir (2ᵉ groupe) -> participe -i. `passe_compose(infinitif, personne)`
    -> "ai parlé". Complétude CROISSANTE (idiome record, le juge garde le plus étroit) : niveau 0 = -er ; 1 = + -ir.

    PORTÉE HONNÊTE & LIMITE RÉVÉLÉE : auxiliaire AVOIR seul, participes RÉGULIERS. Hors portée (forme FAUSSE
    rejetée par le held-out) : verbes à auxiliaire ÊTRE (aller -> 'suis allé', la brique dit 'ai allé'), participes
    irréguliers (prendre -> 'pris'), 3ᵉ groupe. Choix de l'auxiliaire + participes irréguliers = info LEXICALE ->
    frontière nette du model-free, documentée par la carte des limites.
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        head = (f"def {g}(*args, **kwargs):\n"
                "    inf, p = args[0], args[1]\n"
                "    aux = ['ai', 'as', 'a', 'avons', 'avez', 'ont'][p]\n")
        body = "    if inf.endswith('er'):\n        return aux + ' ' + inf[:-2] + 'é'\n"
        if niveau >= 1:
            body += "    if inf.endswith('ir'):\n        return aux + ' ' + inf[:-2] + 'i'\n"
        return head + body + "    return ''\n"

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = list(dict.fromkeys(self._src(g, niveau) for niveau in (0, 1)))
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 2


class GenerateurAdverbe:
    """
    ADVERBE EN -MENT (rung FORME DÉRIVATION — 2026-06-18). Premier saut hors de l'inflexion : DÉRIVER un adverbe
    depuis un adjectif (changement de catégorie adj -> adv). Réglé donc vérifiable : la règle de base = forme
    FÉMININE + 'ment' (grand -> grandement, lent -> lentement, fort -> fortement). `adverbe(adjectif)` -> adverbe.
    Complétude CROISSANTE : niveau 0 = consonne finale (adj+'e'+ment) ; 1 = + adjectifs en -eux (-euse+ment).

    PORTÉE HONNÊTE & LIMITE RÉVÉLÉE : adjectifs à finale consonne (ou -eux). Hors portée (forme FAUSSE rejetée par
    le held-out) : adjectifs à voyelle finale qui élident le e (vrai -> 'vraiment', poli -> 'poliment'), les
    -ant/-ent -> -amment/-emment (constant -> 'constamment'), les suppletifs (bon -> 'bien'). Sous-règles LEXICALES
    -> frontière nette du model-free, documentée par la carte des limites.
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        head = f"def {g}(*args, **kwargs):\n    adj = args[0]\n"
        body = ""
        if niveau >= 1:
            body += "    if adj.endswith('eux'):\n        return adj[:-3] + 'eusement'\n"
        body += "    return adj + 'ement'\n"
        return head + body

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = list(dict.fromkeys(self._src(g, niveau) for niveau in (0, 1)))
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 2


class GenerateurParticipePresent:
    """
    PARTICIPE PRÉSENT (rung FORME — 2026-06-18). Forme verbale en -ant. Réglé donc vérifiable : -er -> radical+ant
    (parler -> parlant), -ir 2ᵉ groupe -> radical+issant (finir -> finissant). `participe_present(infinitif)` -> forme.
    Complétude CROISSANTE : niveau 0 = -er ; 1 = + -ir (2ᵉ groupe).

    PORTÉE HONNÊTE & LIMITE RÉVÉLÉE : -er réguliers et -ir 2ᵉ groupe. Hors portée (forme FAUSSE rejetée par le
    held-out) : irréguliers (avoir -> 'ayant', être -> 'étant', savoir -> 'sachant'), 3ᵉ groupe et -re. Radicaux
    irréguliers = info LEXICALE -> frontière nette du model-free.
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        head = f"def {g}(*args, **kwargs):\n    inf = args[0]\n"
        body = ""
        if niveau >= 1:
            body += "    if inf.endswith('ir'):\n        return inf[:-2] + 'issant'\n"
        body += "    if inf.endswith('er'):\n        return inf[:-2] + 'ant'\n    return ''\n"
        return head + body

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = list(dict.fromkeys(self._src(g, niveau) for niveau in (0, 1)))
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 2


class GenerateurImperatif:
    """
    IMPÉRATIF (rung FORME, mode — 2026-06-18). Mode de l'ordre, 3 personnes (tu, nous, vous). Réglé donc vérifiable :
    -er -> radical+[e, ons, ez] (parle/parlons/parlez — le -s tombe à la 2ᵉ sing.), -ir 2ᵉ groupe ->
    radical+[is, issons, issez] (finis/finissons/finissez). `imperatif(infinitif, personne)`, personne ∈ 0..2.
    Complétude CROISSANTE : niveau 0 = -er ; 1 = + -ir.

    PORTÉE HONNÊTE & LIMITE RÉVÉLÉE : -er réguliers et -ir 2ᵉ groupe. Hors portée (forme FAUSSE rejetée par le
    held-out) : irréguliers (être -> 'sois', avoir -> 'aie'), 3ᵉ groupe. Formes lexicales -> frontière nette.
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        head = f"def {g}(*args, **kwargs):\n    inf, p = args[0], args[1]\n    rad = inf[:-2]\n"
        body = ""
        if niveau >= 1:
            body += "    if inf.endswith('ir'):\n        return rad + ['is', 'issons', 'issez'][p]\n"
        body += "    if inf.endswith('er'):\n        return rad + ['e', 'ons', 'ez'][p]\n    return ''\n"
        return head + body

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = list(dict.fromkeys(self._src(g, niveau) for niveau in (0, 1)))
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 2


class GenerateurConditionnel:
    """
    CONDITIONNEL PRÉSENT (rung FORME, mode — 2026-06-18). Comme le futur, se bâtit sur l'INFINITIF, mais avec les
    terminaisons de l'imparfait : inf + [ais, ais, ait, ions, iez, aient]. Une SEULE règle couvre -er ET -ir
    réguliers (parler -> parlerais, finir -> finirait). `conditionnel(infinitif, personne)`, personne ∈ 0..5.

    PORTÉE HONNÊTE & LIMITE RÉVÉLÉE : verbes dont l'infinitif EST le radical du futur (-er, -ir réguliers). Hors
    portée (forme FAUSSE rejetée par le held-out) : -re (prendre -> 'prendrais', e élidé), radicaux irréguliers
    (être -> 'serais', aller -> 'irais'). Radical de futur irrégulier = info LEXICALE -> frontière nette.
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str) -> str:
        return (f"def {g}(*args, **kwargs):\n    inf, p = args[0], args[1]\n"
                "    return inf + ['ais', 'ais', 'ait', 'ions', 'iez', 'aient'][p]\n")

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        return [self._src(mg.group(1))][:max(1, n)]

    def apprendre(self, delta: float = 0.0) -> int:
        return 1


class GenerateurSubjonctif:
    """
    SUBJONCTIF PRÉSENT (rung FORME, mode — 2026-06-18). Mode du doute/souhait : « que je parle ». Réglé donc
    vérifiable : -er -> radical+[e, es, e, ions, iez, ent], -ir 2ᵉ groupe -> radical+[isse, isses, isse, issions,
    issiez, issent]. `subjonctif(infinitif, personne)`, personne ∈ 0..5. Complétude CROISSANTE : niveau 0 = -er ; 1 = + -ir.

    PORTÉE HONNÊTE & LIMITE RÉVÉLÉE : -er réguliers et -ir 2ᵉ groupe. Hors portée (forme FAUSSE rejetée par le
    held-out) : irréguliers (être -> 'sois', avoir -> 'aie', aller -> 'aille'), 3ᵉ groupe. Radicaux lexicaux -> mur net.
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        head = f"def {g}(*args, **kwargs):\n    inf, p = args[0], args[1]\n    rad = inf[:-2]\n"
        body = ""
        if niveau >= 1:
            body += "    if inf.endswith('ir'):\n        return rad + ['isse', 'isses', 'isse', 'issions', 'issiez', 'issent'][p]\n"
        body += "    if inf.endswith('er'):\n        return rad + ['e', 'es', 'e', 'ions', 'iez', 'ent'][p]\n    return ''\n"
        return head + body

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = list(dict.fromkeys(self._src(g, niveau) for niveau in (0, 1)))
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 2


class GenerateurPluriel:
    """
    PLURIEL (brique « FORME du langage » : accord en NOMBRE — 2026-06-18). Régler, donc vérifiable. Encode les
    RÈGLES du pluriel français (pas une liste), prouvé par le held-out (mots jamais vus). `pluriel(mot)` -> pluriel.

    Candidats à COMPLÉTUDE CROISSANTE (le juge garde le plus étroit correct) : niveau 0 = +s ; 1 = +invariants
    en -s/-x/-z ; 2 = +(-al -> -aux) +(-eau/-au/-eu -> +x).

    PORTÉE HONNÊTE : réguliers + ces familles. Exceptions (bal->bals, œil->yeux, travail->travaux...) HORS -> la
    brique propose une forme FAUSSE que le juge REJETTE. Jamais de faux « vérifié ».
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        head = f"def {g}(*args, **kwargs):\n    m = args[0]\n"
        if niveau == 0:
            return head + "    return m + 's'\n"
        if niveau == 1:
            return head + "    if m[-1:] in ('s', 'x', 'z'):\n        return m\n    return m + 's'\n"
        return (head + "    if m[-1:] in ('s', 'x', 'z'):\n        return m\n"
                "    if m.endswith('al'):\n        return m[:-2] + 'aux'\n"
                "    if m.endswith(('eau', 'au', 'eu')):\n        return m + 'x'\n"
                "    return m + 's'\n")

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [self._src(g, niveau) for niveau in (0, 1, 2)]
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 3


class GenerateurFeminin:
    """
    FÉMININ (brique « FORME du langage » : accord en GENRE des adjectifs — 2026-06-18). Réglé, donc vérifiable.
    Encode les RÈGLES (pas une liste), prouvé par le held-out. `feminin(adjectif)` -> forme au féminin.

    Candidats à COMPLÉTUDE CROISSANTE : niveau 0 = +e ; 1 = +invariants en -e ; 2 = +(-eux -> -euse)
    +(-er -> -ère) +(-f -> -ve).

    PORTÉE HONNÊTE : réguliers + ces familles. Irréguliers (beau->belle, vieux->vieille, doux->douce...) HORS ->
    forme FAUSSE que le juge REJETTE. Jamais de faux « vérifié ».
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        head = f"def {g}(*args, **kwargs):\n    a = args[0]\n"
        if niveau == 0:
            return head + "    return a + 'e'\n"
        if niveau == 1:
            return head + "    if a.endswith('e'):\n        return a\n    return a + 'e'\n"
        return (head + "    if a.endswith('eux'):\n        return a[:-3] + 'euse'\n"
                "    if a.endswith('er'):\n        return a[:-2] + 'ère'\n"
                "    if a.endswith('f'):\n        return a[:-1] + 've'\n"
                "    if a.endswith('e'):\n        return a\n"
                "    return a + 'e'\n")

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [self._src(g, niveau) for niveau in (0, 1, 2)]
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 3


class GenerateurRelationLexicale:
    """
    RELATIONS LEXICALES (brique « SENS — niveau 2 » : raisonner sur un graphe de relations — 2026-06-18, défi Yohan).

    1er pas vers le SENS qui a un juge : le sens d'un mot vit dans ses RELATIONS (is-a, synonyme, antonyme). Le
    CONTENU lexical (les arêtes) est DONNÉ en exemples ; la brique fournit le RAISONNEMENT qui GÉNÉRALISE = la
    CLOSURE (atteignabilité transitive), prouvé par le held-out : répond sur des paires JAMAIS données en direct
    (chat→félin→mammifère ⟹ est_un(chat, mammifère) sans arête directe). Au-delà de `graphe` (voisins DIRECTS, aucune
    transitivité — un `a_arete` passe le visible mais ÉCHOUE le held-out transitif → distinction prouvée).

    Famille bornée (3, idiome `graphe` : points d'entrée distincts) :
      - est_un(aretes, x, y)      -> bool : y atteignable depuis x via les arêtes DIRIGÉES (hyperonymie transitive)
      - ancetres(aretes, x)       -> list : tous les ancêtres atteignables, triés (closure complète)
      - est_synonyme(aretes, x,y) -> bool : atteignable en traitant les arêtes comme NON DIRIGÉES (classe d'équiv.)

    HONNÊTE : ne fait que de la closure sur un graphe fourni — n'invente aucun fait lexical.
    """

    _REACH_DIR = ("    aretes, x, y = args[0], args[1], args[2]\n"
                  "    seen, pile = set(), [x]\n"
                  "    while pile:\n"
                  "        n = pile.pop()\n"
                  "        if n == y:\n            return True\n"
                  "        if n in seen:\n            continue\n"
                  "        seen.add(n)\n"
                  "        pile += [_b for _a, _b in aretes if _a == n]\n"
                  "    return False")
    _ANCETRES = ("    aretes, x = args[0], args[1]\n"
                 "    seen, pile, out = set(), [x], []\n"
                 "    while pile:\n"
                 "        n = pile.pop()\n"
                 "        for _a, _b in aretes:\n"
                 "            if _a == n and _b not in seen:\n"
                 "                seen.add(_b)\n                pile.append(_b)\n                out.append(_b)\n"
                 "    return sorted(out)")
    _REACH_UNDIR = ("    aretes, x, y = args[0], args[1], args[2]\n"
                    "    seen, pile = set(), [x]\n"
                    "    while pile:\n"
                    "        n = pile.pop()\n"
                    "        if n == y:\n            return True\n"
                    "        if n in seen:\n            continue\n"
                    "        seen.add(n)\n"
                    "        pile += [_b for _a, _b in aretes if _a == n]\n"
                    "        pile += [_a for _a, _b in aretes if _b == n]\n"
                    "    return False")
    REL = (("est_un", _REACH_DIR), ("ancetres", _ANCETRES), ("est_synonyme", _REACH_UNDIR))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurSensExecutable:
    """
    SENS EXÉCUTABLE (brique « SENS — niveau 3 », le cœur du défi Yohan — 2026-06-18). Intuition d'éducateur canin :
    associer un MOT à une ACTION lui donne du sens. Ici un VERBE (mot) -> un COMPORTEMENT exécutable ; le juge LANCE
    l'action et la réalité tranche. `agir(verbe, x)` -> résultat de l'action nommée par `verbe` appliquée à `x`.

    La RÈGLE apprise = la liaison mot↔action ; le held-out la prouve en appliquant les MÊMES verbes à des arguments
    JAMAIS vus (agir('trie',[9,5,7]) après n'avoir vu que [3,1,2]) → c'est l'action qui est apprise, pas une paire
    entrée/sortie mémorisée. Un substrat qui renverrait sorted(x) passe `trie` mais ÉCHOUE `somme` (autre verbe) →
    le juge force la VRAIE dispatch sur le mot. MUR prouvé.

    Candidats à COMPLÉTUDE CROISSANTE (idiome `record`, PAS de shuffle : le juge garde le vocabulaire le plus
    ÉTROIT qui passe) : niveau 0 = {trie, somme} ; 1 = +{inverse, longueur} ; 2 = +{max, min}.

    PORTÉE HONNÊTE : verbe HORS vocabulaire (ex. 'mediane') -> KeyError -> non résolu -> HORS (jamais de faux).
    """

    _VERBES = (
        ("trie", "sorted(x)"), ("somme", "sum(x)"),
        ("inverse", "x[::-1]"), ("longueur", "len(x)"),
        ("max", "max(x)"), ("min", "min(x)"),
    )

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        nb = {0: 2, 1: 4, 2: 6}[niveau]
        entrees = ",\n".join(f"        {v!r}: (lambda x: {expr})" for v, expr in self._VERBES[:nb])
        return (f"def {g}(*args, **kwargs):\n"
                "    verbe, x = args[0], args[1]\n"
                "    actions = {\n" + entrees + ",\n    }\n"
                "    return actions[verbe](x)\n")

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [self._src(g, niveau) for niveau in (0, 1, 2)]
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._VERBES)


class GenerateurIntention:
    """
    INTENTION / BUT (brique « SENS — au-dessus de l'action » — 2026-06-18, transposition du grounding canin de Yohan :
    l'INTENTION mise dans l'ordre). Au lieu de NOMMER l'action (sens-executable), on donne le BUT = un état visé
    VÉRIFIABLE, et la brique fait du MOYEN-FIN : elle essaie ses actions et renvoie celle dont le RÉSULTAT satisfait
    le prédicat-but. `atteindre(but, x)` -> x transformé pour satisfaire `but`.

    C'est un cap : l'IA ne suit plus l'ordre littéral, elle VISE un résultat et le VÉRIFIE. Le held-out le prouve
    (même but, arguments JAMAIS vus -> la post-condition tient toujours). Un substrat sans recherche moyen-fin échoue ;
    un sorted(x) figé passe `croissant` mais ÉCHOUE `decroissant`/`sans_doublon` (autres buts) -> MUR prouvé.

    Candidats à COMPLÉTUDE CROISSANTE (le juge garde le vocabulaire de buts le plus ÉTROIT qui passe) :
    niveau 0 = {croissant, decroissant} ; 1 = +{sans_doublon}.

    PORTÉE HONNÊTE : but HORS vocabulaire (ex. 'palindrome') -> KeyError -> HORS (jamais de faux).
    """

    _BUTS = (
        ("croissant", "all(r[_i] <= r[_i + 1] for _i in range(len(r) - 1))"),
        ("decroissant", "all(r[_i] >= r[_i + 1] for _i in range(len(r) - 1))"),
        ("sans_doublon", "len(set(r)) == len(r)"),
    )
    _MOYENS = "[sorted(x), sorted(x, reverse=True), list(dict.fromkeys(x)), x]"

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        nb = {0: 2, 1: 3, 2: 3}[niveau]
        buts = ",\n".join(f"        {nom!r}: (lambda r: {pred})" for nom, pred in self._BUTS[:nb])
        return (f"def {g}(*args, **kwargs):\n"
                "    but, x = args[0], args[1]\n"
                "    buts = {\n" + buts + ",\n    }\n"
                f"    for r in {self._MOYENS}:\n"
                "        if buts[but](r):\n            return r\n"
                "    return x\n")

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = list(dict.fromkeys(self._src(g, niveau) for niveau in (0, 1, 2)))
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._BUTS)


class GenerateurDesambiguisation:
    """
    DÉSAMBIGUÏSATION MULTI-CANAL (brique « SENS » — 2026-06-18, transposition des GESTES de Yohan : un même mot précisé
    par un 2ᵉ canal). Un mot ambigu seul, levé par un GESTE (2ᵉ signal). `commande(mot, geste, x)` -> action choisie
    par le COUPLE (mot, geste). NOUVEAU vs sens-executable (un seul canal) : ici le sens NAÎT de la combinaison.

    MUR fort intrinsèque : un corps qui ignore `geste` ne peut PAS distinguer ('tri','haut') de ('tri','bas') ->
    la brique prouve qu'il FAUT les deux canaux. Held-out = mêmes couples, arguments JAMAIS vus.

    Candidats à COMPLÉTUDE CROISSANTE : niveau 0 = famille `tri` (haut/bas) ; 1 = +famille `bout` (debut/fin).

    PORTÉE HONNÊTE : couple (mot, geste) inconnu -> KeyError -> HORS.
    """

    _CANAUX = (
        ("('tri', 'haut')", "sorted(x)"), ("('tri', 'bas')", "sorted(x, reverse=True)"),
        ("('bout', 'debut')", "x[0]"), ("('bout', 'fin')", "x[-1]"),
    )

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        nb = {0: 2, 1: 4, 2: 4}[niveau]
        table = ",\n".join(f"        {cle}: (lambda: {expr})" for cle, expr in self._CANAUX[:nb])
        return (f"def {g}(*args, **kwargs):\n"
                "    mot, geste, x = args[0], args[1], args[2]\n"
                "    table = {\n" + table + ",\n    }\n"
                "    return table[(mot, geste)]()\n")

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = list(dict.fromkeys(self._src(g, niveau) for niveau in (0, 1, 2)))
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._CANAUX)


class GenerateurNormalisation:
    """
    NORMALISATION / ROBUSTESSE (brique « SENS » — 2026-06-18, transposition de la CLARTÉ de Yohan : le signal passe
    malgré le bruit). Des variantes bruitées d'un ordre (casse, espaces, SYNONYMES) -> la même action canonique.
    `agir_robuste(verbe, x)` -> action après normalisation de `verbe`.

    Le held-out le prouve avec des variantes JAMAIS vues -> c'est la RÈGLE de normalisation qui est apprise, pas une
    liste de chaînes exactes. Un corps sans normalisation échoue sur ' TRIE ' (casse/espace) ou 'Ranger' (synonyme)
    -> MUR prouvé.

    Candidats à COMPLÉTUDE CROISSANTE : niveau 0 = strip+lower ; 1 = +table de SYNONYMES.

    PORTÉE HONNÊTE : verbe sans mapping canonique -> KeyError -> HORS.
    """

    _SYN = "{'trier': 'trie', 'tri': 'trie', 'ranger': 'trie', 'inverser': 'inverse', 'retourner': 'inverse'}"
    _ACTIONS = "{'trie': (lambda: sorted(x)), 'inverse': (lambda: x[::-1])}"

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        head = (f"def {g}(*args, **kwargs):\n"
                "    verbe, x = args[0], args[1]\n"
                "    v = verbe.strip().lower()\n")
        syn = f"    v = {self._SYN}.get(v, v)\n" if niveau >= 1 else ""
        return head + syn + f"    actions = {self._ACTIONS}\n    return actions[v]()\n"

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = list(dict.fromkeys(self._src(g, niveau) for niveau in (0, 1, 2)))
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 2


class GenerateurAncetreCommun:
    """
    ANCÊTRE COMMUN / LIEN (brique COMPRÉHENSION — 2026-06-18, « comprendre le sens des mots »). Raisonne sur le graphe
    de sens (hyperonymie is-a) : ce que DEUX mots ont en commun. `ancetre_commun(aretes, x, y)` -> le plus PROCHE
    ancêtre partagé (LCA, par parcours en largeur = distance croissante) ; `ont_lien(aretes, x, y)` -> partagent-ils
    un ancêtre ? Au-delà de relation-lexicale (atteignabilité x→y) : ici on CROISE deux remontées (vrai raisonnement
    de catégorie). Held-out = paires jamais directes (chat/chien -> mammifère sans arête directe).

    Famille bornée (2, idiome graphe/relation-lexicale : points d'entrée distincts). HONNÊTE : pas de lien -> None / False.
    """

    _PRE = ("    aretes, x, y = args[0], args[1], args[2]\n"
            "    def _anc(n):\n"
            "        out, seen, file, i = [], {n}, [n], 0\n"
            "        while i < len(file):\n"
            "            c = file[i]; i += 1\n"
            "            for _a, _b in aretes:\n"
            "                if _a == c and _b not in seen:\n"
            "                    seen.add(_b); file.append(_b); out.append(_b)\n"
            "        return out\n"
            "    ay = set(_anc(y))\n")
    _LCA = _PRE + "    for _z in _anc(x):\n        if _z in ay:\n            return _z\n    return None"
    _LIEN = _PRE + "    return any(_z in ay for _z in _anc(x))"
    REL = (("ancetre_commun", _LCA), ("ont_lien", _LIEN))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurIntrus:
    """
    INTRUS / CATÉGORIE COMMUNE (brique COMPRÉHENSION — 2026-06-18, logique de catégorie). Sur une LISTE de mots et le
    graphe de sens : `intrus(aretes, mots)` -> le mot qui ne partage PAS la catégorie des autres ; `categorie_commune(
    aretes, mots)` -> le plus proche ancêtre commun à TOUS. Vrai raisonnement ensembliste (intersection des remontées),
    généralise à toute liste/graphe. Held-out = listes jamais vues, intrus en position variable.

    Famille bornée (2). HONNÊTE : aucun intrus / aucune catégorie commune -> None.
    """

    _PRE = ("    aretes, mots = args[0], args[1]\n"
            "    def _anc(n):\n"
            "        out, seen, file, i = [], {n}, [n], 0\n"
            "        while i < len(file):\n"
            "            c = file[i]; i += 1\n"
            "            for _a, _b in aretes:\n"
            "                if _a == c and _b not in seen:\n"
            "                    seen.add(_b); file.append(_b); out.append(_b)\n"
            "        return out\n"
            "    def _set(n):\n        return set(_anc(n)) | {n}\n")
    _INTRUS = (_PRE + "    for _w in mots:\n"
               "        _autres = [_set(_o) for _o in mots if _o != _w]\n"
               "        _commun = set.intersection(*_autres) if _autres else set()\n"
               "        if _commun and not (_commun & _set(_w)):\n            return _w\n"
               "    return None")
    _CAT = (_PRE + "    _commun = set.intersection(*[_set(_m) for _m in mots])\n"
            "    for _z in [mots[0]] + _anc(mots[0]):\n"
            "        if _z in _commun:\n            return _z\n"
            "    return None")
    REL = (("intrus", _INTRUS), ("categorie_commune", _CAT))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurAnalysePhrase:
    """
    ANALYSE DE PHRASE (brique COMPRÉHENSION — phrase, 2026-06-18). 1ère marche pour comprendre une phrase : la
    DÉCOMPOSER. Sur une table classe officielle (mot->nom/verbe/adjectif/déterminant) passée en argument :
    `analyse(classes, phrase)` -> la suite des classes ; `noms(classes, phrase)` -> les noms de la phrase. Mapping
    réglé sur tokens, généralise à toute phrase/table. Held-out = phrases jamais vues.

    Famille bornée (2). HONNÊTE : hors famille -> rejeté par le juge.
    """

    _ANALYSE = ("    classes, phrase = args[0], args[1]\n"
                "    return [classes.get(_m, 'inconnu') for _m in phrase.split()]")
    _NOMS = ("    classes, phrase = args[0], args[1]\n"
             "    return [_m for _m in phrase.split() if classes.get(_m) == 'nom']")
    REL = (("analyse", _ANALYSE), ("noms", _NOMS))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurComprehensionPhrase:
    """
    COMPRÉHENSION DE PHRASE (brique COMPRÉHENSION — sens + LOGIQUE, 2026-06-18). Comprendre QUI fait QUOI : attribue
    les rôles d'une phrase sujet-verbe-objet par rapport au VERBE. `sujet(classes, phrase)` -> groupe avant le verbe ;
    `action(classes, phrase)` -> le verbe ; `objet(classes, phrase)` -> groupe après le verbe. Logique positionnelle
    réglée, généralise à toute phrase SVO + table. Held-out = phrases jamais vues, groupes de longueur variable.

    Famille bornée (3). HONNÊTE/LIMITE : phrase SANS verbe -> pas d'action -> erreur rejetée par le juge (on ne
    devine pas un rôle qui n'existe pas).
    """

    _PRE = ("    classes, phrase = args[0], args[1]\n"
            "    toks = phrase.split()\n"
            "    cl = [classes.get(_t, 'inconnu') for _t in toks]\n"
            "    vi = cl.index('verbe')\n")
    REL = (("sujet", _PRE + "    return ' '.join(toks[:vi])"),
           ("action", _PRE + "    return toks[vi]"),
           ("objet", _PRE + "    return ' '.join(toks[vi + 1:])"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurAccordPhrase:
    """
    ACCORD DANS LE GROUPE NOMINAL (brique COMPRÉHENSION — phrase structurelle, 2026-06-18). Comble le mur STRUCTUREL
    de la carte des limites : propage le PLURIEL sur tout le groupe (déterminant + nom + adjectifs). `accorder_pluriel(
    phrase)` -> le groupe au pluriel. COMPOSE la règle du pluriel (familles) avec une table de déterminants officielle.
    Held-out = groupes jamais vus, incluant les familles (-al/-eau/-eu).

    Candidats à COMPLÉTUDE CROISSANTE : niveau 0 = déterminants + (+s) ; 1 = +invariants -s/-x/-z ; 2 = +familles.
    HONNÊTE : ne fait pas l'inverse (dépluraliser) -> rejeté.
    """

    _DET = "{'le': 'les', 'la': 'les', 'un': 'des', 'une': 'des'}"

    def __init__(self, seed: int = 0):
        self._seed = seed

    def _src(self, g: str, niveau: int) -> str:
        rules = "        if _m in det:\n            return det[_m]\n"
        if niveau >= 1:
            rules += "        if _m[-1:] in ('s', 'x', 'z'):\n            return _m\n"
        if niveau >= 2:
            rules += ("        if _m.endswith('al'):\n            return _m[:-2] + 'aux'\n"
                      "        if _m.endswith(('eau', 'au', 'eu')):\n            return _m + 'x'\n")
        return (f"def {g}(*args, **kwargs):\n    phrase = args[0]\n    det = {self._DET}\n"
                "    def _p(_m):\n" + rules + "        return _m + 's'\n"
                "    return ' '.join(_p(_w) for _w in phrase.split())\n")

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = list(dict.fromkeys(self._src(g, niveau) for niveau in (0, 1, 2)))
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 3


class GenerateurInference:
    """
    INFÉRENCE LOGIQUE (brique COMPRÉHENSION — LOGIQUE, 2026-06-18). « Une logique derrière » : déduit une conclusion
    à partir de PRÉMISSES (sujet, relation, objet) avec relation ∈ {'est','nest_pas'}. `deduit(premisses, x, y)` ->
    'oui' (y atteignable depuis x par les 'est'), 'non' (un ancêtre atteignable de x est explicitement 'nest_pas' y →
    contradiction), 'inconnu' (ni l'un ni l'autre n'est dérivable).

    AU-DELÀ de relation-lexicale (simple atteignabilité booléenne) : faits NÉGATIFS + logique à TROIS valeurs. Le
    'inconnu' est la marque d'HONNÊTETÉ — l'IA ne conclut JAMAIS ce qu'elle ne peut pas prouver. Held-out = prémisses
    et questions jamais vues. Le juge tranche la déduction par exécution.
    """

    _BODY = ("    premisses, x, y = args[0], args[1], args[2]\n"
             "    pos = [(_a, _b) for _a, _r, _b in premisses if _r == 'est']\n"
             "    neg = [(_a, _b) for _a, _r, _b in premisses if _r == 'nest_pas']\n"
             "    seen, pile = set(), [x]\n"
             "    while pile:\n"
             "        _n = pile.pop()\n"
             "        if _n in seen:\n            continue\n"
             "        seen.add(_n)\n"
             "        pile += [_b for _a, _b in pos if _a == _n]\n"
             "    if y in seen:\n        return 'oui'\n"
             "    if any((_z, y) in neg for _z in seen):\n        return 'non'\n"
             "    return 'inconnu'\n")

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        return [f"def {g}(*args, **kwargs):\n{self._BODY}"]

    def apprendre(self, delta: float = 0.0) -> int:
        return 1


class GenerateurComprehensionDefinition:
    """
    COMPRÉHENSION DE DÉFINITION (brique COMPRÉHENSION — 2026-06-18, « comprendre les définitions »). Une définition de
    dictionnaire a une structure GENRE + DIFFÉRENCE (« chat = petit [mammifère] félin domestique » : genre = la
    catégorie, le 1er nom ; différence = les traits qui distinguent). Sur une table de classes officielle :
    `genus(classes, definition)` -> la catégorie (1er nom) ; `differentia(classes, definition)` -> les traits
    (adjectifs). Comprendre une définition = la décomposer ainsi. Généralise à toute définition + table. Held-out =
    définitions jamais vues.

    Famille bornée (2). HONNÊTE : hors famille -> rejeté.
    """

    _GENUS = ("    classes, definition = args[0], args[1]\n"
              "    for _w in definition.split():\n"
              "        if classes.get(_w) == 'nom':\n            return _w\n"
              "    return None")
    _DIFF = ("    classes, definition = args[0], args[1]\n"
             "    return [_w for _w in definition.split() if classes.get(_w) == 'adjectif']")
    REL = (("genus", _GENUS), ("differentia", _DIFF))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurDistanceSemantique:
    """
    DISTANCE SÉMANTIQUE (brique COMPRÉHENSION — 2026-06-18). Mesure la PROXIMITÉ de sens sur le graphe is-a :
    `distance(aretes, x, y)` -> nombre de pas (x→ancêtre commun) + (y→ancêtre commun), minimal ; `plus_proche(aretes,
    x, candidats)` -> le candidat sémantiquement le plus proche de x. Escalade (les briques précédentes EXCLUAIENT la
    distance) : « chat » est plus proche de « chien » (mammifères) que de « voiture ». Généralise à tout graphe.

    Famille bornée (2). HONNÊTE : aucun ancêtre commun -> distance None ; aucun candidat lié -> None.
    """

    _DEPTH = ("    def _depth(s):\n"
              "        prof, file, i = {s: 0}, [s], 0\n"
              "        while i < len(file):\n"
              "            _n = file[i]; i += 1\n"
              "            for _a, _b in aretes:\n"
              "                if _a == _n and _b not in prof:\n"
              "                    prof[_b] = prof[_n] + 1; file.append(_b)\n"
              "        return prof\n")
    _DIST = ("    aretes, x, y = args[0], args[1], args[2]\n" + _DEPTH +
             "    dx, dy = _depth(x), _depth(y)\n"
             "    communs = [dx[_z] + dy[_z] for _z in dx if _z in dy]\n"
             "    return min(communs) if communs else None")
    _PROCHE = ("    aretes, x, cands = args[0], args[1], args[2]\n" + _DEPTH +
               "    dx = _depth(x)\n"
               "    best, bd = None, None\n"
               "    for _c in cands:\n"
               "        dc = _depth(_c)\n"
               "        _ds = [dx[_z] + dc[_z] for _z in dx if _z in dc]\n"
               "        if _ds:\n"
               "            _m = min(_ds)\n"
               "            if bd is None or _m < bd:\n                bd, best = _m, _c\n"
               "    return best")
    REL = (("distance", _DIST), ("plus_proche", _PROCHE))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurAccordCorrect:
    """
    DÉTECTION D'ERREUR D'ACCORD (brique COMPRÉHENSION — 2026-06-18). Comprendre le français = savoir quand il est FAUX.
    Sur un groupe nominal : `est_accorde(phrase)` -> l'accord en nombre est-il correct ? ; `mot_fautif(phrase)` -> le
    1er mot mal accordé (ou None). Règle : après un déterminant pluriel (les/des), chaque mot porte la marque du pluriel
    (-s/-x/-z). Généralise à tout groupe. C'est de la compréhension de la NORME (au-delà de produire : juger).

    Famille bornée (2). HONNÊTE : groupe non pluriel -> rien à signaler (True / None) ; hors famille -> rejeté.
    """

    _PRE = "    phrase = args[0]\n    mots = phrase.split()\n    plur = {'les', 'des'}\n"
    _EST = (_PRE + "    if not mots or mots[0] not in plur:\n        return True\n"
            "    return all(_w[-1:] in ('s', 'x', 'z') for _w in mots[1:])")
    _FAUTIF = (_PRE + "    if not mots or mots[0] not in plur:\n        return None\n"
               "    for _w in mots[1:]:\n        if _w[-1:] not in ('s', 'x', 'z'):\n            return _w\n    return None")
    REL = (("est_accorde", _EST), ("mot_fautif", _FAUTIF))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurAntonyme:
    """
    ANTONYMES (brique COMPRÉHENSION — axe du sens : les contraires, 2026-06-18). Sur une table de paires d'antonymes
    (officielle) : `contraire(antonymes, mot)` -> le mot opposé ; `sont_contraires(antonymes, x, y)` -> sont-ils
    opposés ? L'antonymie est SYMÉTRIQUE et NON transitive (≠ synonymie) — d'où une brique propre. Généralise à toute
    table. Held-out = mots/paires jamais vus.

    Famille bornée (2). HONNÊTE : pas d'antonyme connu -> None / False.
    """

    _CONTRAIRE = ("    antonymes, mot = args[0], args[1]\n"
                  "    for _a, _b in antonymes:\n"
                  "        if _a == mot:\n            return _b\n"
                  "        if _b == mot:\n            return _a\n"
                  "    return None")
    _SONT = ("    antonymes, x, y = args[0], args[1], args[2]\n"
             "    return (x, y) in antonymes or (y, x) in antonymes")
    REL = (("contraire", _CONTRAIRE), ("sont_contraires", _SONT))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurParaphrase:
    """
    PARAPHRASE / MÊME SENS (brique COMPRÉHENSION — 2026-06-18). Deux formulations ont le MÊME sens si elles coïncident
    après remplacement des synonymes par leur forme canonique. Sur une table de synonymes (mot->canonique) :
    `canonise(synonymes, phrase)` -> la forme canonique ; `meme_sens(synonymes, p1, p2)` -> ont-elles le même sens ?
    Comprendre = voir au-delà des mots de surface. Généralise à toute table/phrase. Held-out = phrases jamais vues.

    Famille bornée (2). HONNÊTE : sens différent -> False (ne confond pas rapide et lent).
    """

    _CANON = ("    synonymes, phrase = args[0], args[1]\n"
              "    return ' '.join(synonymes.get(_w, _w) for _w in phrase.split())")
    _MEME = ("    synonymes, p1, p2 = args[0], args[1], args[2]\n"
             "    return [synonymes.get(_w, _w) for _w in p1.split()] == [synonymes.get(_w, _w) for _w in p2.split()]")
    REL = (("canonise", _CANON), ("meme_sens", _MEME))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurNegation:
    """
    NÉGATION (brique COMPRÉHENSION — phrase, 2026-06-18). Comprendre « ne…pas » : `est_negative(phrase)` -> la phrase
    est-elle niée (marqueur `ne`/`n'` + `pas`/`plus`/`jamais`/`rien`) ? ; `enleve_negation(phrase)` -> le NOYAU
    affirmatif (retire la négation, « n'est » -> « est »). Clé du discours : « le chat n'est pas un oiseau » devient un
    fait NÉGATIF pour l'inférence. Règle généralisant à toute phrase. Held-out = phrases jamais vues.

    Famille bornée (2). HONNÊTE : hors famille -> rejeté.
    """

    _EST = ("    phrase = args[0]\n"
            "    toks = phrase.split()\n"
            "    a = ('ne' in toks) or any(_t.startswith(\"n'\") for _t in toks)\n"
            "    b = any(_t in ('pas', 'plus', 'jamais', 'rien') for _t in toks)\n"
            "    return a and b")
    _ENLEVE = ("    phrase = args[0]\n"
               "    enleves = {'ne', 'pas', 'plus', 'jamais', 'rien'}\n"
               "    toks = [(_t[2:] if _t.startswith(\"n'\") else _t) for _t in phrase.split() if _t not in enleves]\n"
               "    return ' '.join(toks)")
    REL = (("est_negative", _EST), ("enleve_negation", _ENLEVE))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurQuantificateur:
    """
    QUANTIFICATEURS (brique COMPRÉHENSION — LOGIQUE, 2026-06-18). Au-delà de l'inférence à sujet unique : la logique
    QUANTIFIÉE sur un ENSEMBLE de mots, via la closure is-a. `tous(aretes, membres, categorie)` -> tous sont-ils de
    cette catégorie ? ; `certains(...)` -> au moins un ? ; `aucun(...)` -> aucun ? Généralise à tout ensemble/graphe.
    Held-out = ensembles jamais vus. « tous les chats/lions/tigres sont des félins » -> vrai.

    Famille bornée (3). HONNÊTE : un membre hors graphe ne remonte à rien -> compté correctement (tous=False).
    """

    _REACH = ("    aretes, membres, cat = args[0], args[1], args[2]\n"
              "    if not isinstance(membres, list):\n        return None\n"   # quantifier = sur une COLLECTION (pas une chaîne)
              "    def _atteint(s):\n"
              "        seen, pile = set(), [s]\n"
              "        while pile:\n"
              "            _n = pile.pop()\n"
              "            if _n == cat:\n                return True\n"
              "            if _n in seen:\n                continue\n"
              "            seen.add(_n)\n"
              "            pile += [_b for _a, _b in aretes if _a == _n]\n"
              "        return False\n")
    REL = (("tous", _REACH + "    return all(_atteint(_m) for _m in membres)"),
           ("certains", _REACH + "    return any(_atteint(_m) for _m in membres)"),
           ("aucun", _REACH + "    return not any(_atteint(_m) for _m in membres)"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurCoreference:
    """
    CORÉFÉRENCE (brique COMPRÉHENSION — discours, 2026-06-18). Résoudre un pronom : « le chat voit la souris. IL dort »
    -> « il » = chat. Sur une table de genres : `antecedent(genres, mentions, pronom)` -> le nom le plus RÉCENT
    compatible en genre ; `compatible(genres, nom, pronom)` -> ce nom peut-il être l'antécédent ? il/ils->masculin,
    elle/elles->féminin. Généralise à tout discours/table. Held-out = mentions jamais vues.

    Famille bornée (2). HONNÊTE : aucun antécédent compatible -> None / False.
    """

    _G = "    g = 'masculin' if pronom in ('il', 'ils') else 'féminin'\n"
    _ANTE = ("    genres, mentions, pronom = args[0], args[1], args[2]\n" + _G +
             "    for _m in reversed(mentions):\n"
             "        if genres.get(_m) == g:\n            return _m\n"
             "    return None")
    _COMPAT = ("    genres, nom, pronom = args[0], args[1], args[2]\n" + _G +
               "    return genres.get(nom) == g")
    REL = (("antecedent", _ANTE), ("compatible", _COMPAT))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurTemporel:
    """
    LOGIQUE TEMPORELLE (brique COMPRÉHENSION — LOGIQUE, 2026-06-18). Ordonner des événements selon « avant ». Sur des
    relations (a, b) = « a avant b » : `ordonne(relations, evenements)` -> les événements en ORDRE chronologique (tri
    topologique) ; `premier(relations, evenements)` -> le tout premier. NOUVEAU vs relation-lexicale (atteignabilité
    booléenne) : ici on PRODUIT un ordre (pas un oui/non). Généralise à tout ensemble de relations. Held-out = neuf.

    Famille bornée (2). HONNÊTE : cycle -> s'arrête (ordre partiel) sans inventer.
    """

    _SORT = ("    relations, evenements = args[0], args[1]\n"
             "    reste, out = list(evenements), []\n"
             "    while reste:\n"
             "        for _e in reste:\n"
             "            if not any(_b == _e and _a in reste for _a, _b in relations):\n"
             "                out.append(_e); reste.remove(_e); break\n"
             "        else:\n"
             "            break\n")
    REL = (("ordonne", _SORT + "    return out"),
           ("premier", _SORT + "    return out[0] if out else None"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurComptage:
    """
    COMPTAGE (brique COMPRÉHENSION — quantitatif, 2026-06-18). « COMBIEN de membres sont d'une catégorie ? » via la
    closure is-a. `combien(aretes, membres, cat)` -> le NOMBRE de membres atteignant cat ; `lesquels(aretes, membres,
    cat)` -> la SOUS-LISTE de ceux qui l'atteignent. Distinct des quantificateurs (booléen) : ici on PRODUIT un nombre
    / une liste. Généralise à tout ensemble/graphe. Held-out = ensembles neufs.

    Famille bornée (2). HONNÊTE : membres non-collection -> None.
    """

    _REACH = ("    aretes, membres, cat = args[0], args[1], args[2]\n"
              "    if not isinstance(membres, list):\n        return None\n"
              "    def _atteint(s):\n"
              "        seen, pile = set(), [s]\n"
              "        while pile:\n"
              "            _n = pile.pop()\n"
              "            if _n == cat:\n                return True\n"
              "            if _n in seen:\n                continue\n"
              "            seen.add(_n)\n"
              "            pile += [_b for _a, _b in aretes if _a == _n]\n"
              "        return False\n")
    REL = (("combien", _REACH + "    return sum(1 for _m in membres if _atteint(_m))"),
           ("lesquels", _REACH + "    return [_m for _m in membres if _atteint(_m)]"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurChemin:
    """
    CHEMIN / EXPLICATION (brique COMPRÉHENSION — 2026-06-18). EXPLIQUER une relation = donner la CHAÎNE qui la relie.
    `chemin(aretes, x, y)` -> la suite de nœuds de x à y (le « parce que ») ; `intermediaires(aretes, x, y)` -> les
    étapes entre les deux. Distinct de relation-lexicale (booléen), distance (nombre), ancetre-commun (un seul nœud) :
    ici on PRODUIT le parcours ordonné. Généralise à tout graphe. Held-out = paires neuves.

    Famille bornée (2). HONNÊTE : pas de chemin -> None / [].
    """

    _BFS = ("    aretes, x, y = args[0], args[1], args[2]\n"
            "    parent, file, i = {x: None}, [x], 0\n"
            "    while i < len(file):\n"
            "        _n = file[i]; i += 1\n"
            "        if _n == y:\n"
            "            _ch = []\n"
            "            while _n is not None:\n                _ch.append(_n); _n = parent[_n]\n"
            "            return _ch[::-1]\n"
            "        for _a, _b in aretes:\n"
            "            if _a == _n and _b not in parent:\n"
            "                parent[_b] = _n; file.append(_b)\n"
            "    return None\n")
    REL = (("chemin", _BFS + "    return None"),
           ("intermediaires", _BFS.replace("            return _ch[::-1]\n",
                                           "            return _ch[::-1][1:-1]\n") + "    return []"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurGeneration:
    """
    GÉNÉRATION DE PHRASE (brique COMPRÉHENSION — PRODUCTION, 2026-06-18). L'IA ÉCRIT une phrase française complète à
    partir d'un sens structuré : `phrase(sujet, verbe, objet, genres)` -> « le chat mange la souris » ; `intransitif(
    sujet, verbe, genres)` -> « le chat chante ». Détermine l'article (le/la/l'), conjugue (3ᵉ pers. sing. présent,
    -er/-ir). Généralise à tout vocabulaire. Vérifiable : la phrase produite se RÉ-ANALYSE en le sens d'origine
    (génération ∘ compréhension = identité) — c'est la cohérence prouvée.

    Famille bornée (2). Portée : noms + verbes réguliers -er / 2ᵉ groupe -ir.
    """

    _DEF = ("    def _gn(_nom):\n"
            "        if _nom[:1] in 'aeiouéèêà':\n            return \"l'\" + _nom\n"
            "        return ('le ' if genres.get(_nom) == 'masculin' else 'la ') + _nom\n"
            "    def _conj(_v):\n"
            "        return _v[:-2] + 'e' if _v.endswith('er') else (_v[:-2] + 'it' if _v.endswith('ir') else _v)\n")
    _PHRASE = ("    sujet, verbe, objet, genres = args[0], args[1], args[2], args[3]\n" + _DEF +
               "    return _gn(sujet) + ' ' + _conj(verbe) + ' ' + _gn(objet)")
    _INTRANS = ("    sujet, verbe, genres = args[0], args[1], args[2]\n" + _DEF +
                "    return _gn(sujet) + ' ' + _conj(verbe)")
    REL = (("phrase", _PHRASE), ("intransitif", _INTRANS))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurInterrogation:
    """
    INTERROGATION (brique COMPRÉHENSION — PRODUCTION, 2026-06-18). ABOLIT le mur documenté de la génération (« la
    brique ne sait pas tourner une phrase en question »). Transforme un sens structuré en QUESTION par inversion
    complexe + pronom de reprise : `question(sujet, verbe, objet, genres)` -> « le chat mange-t-il la souris ? ».
    Gère le -t- euphonique (verbe en voyelle -> mange-t-il ; en -t -> finit-il) et le pronom selon le genre du sujet.
    Vérifiable : forme RÉGLÉE (mêmes helpers article/conjugaison que la génération).

    PORTÉE HONNÊTE : noms + verbes réguliers -er / 2ᵉ groupe -ir, sujet à genre connu. Hors portée (forme FAUSSE
    rejetée par le held-out) : verbes irréguliers (prendre -> 'prend', la brique laisse 'prendre').
    """

    _DEF = GenerateurGeneration._DEF
    _Q = ("    sujet, verbe, objet, genres = args[0], args[1], args[2], args[3]\n" + _DEF +
          "    vc = _conj(verbe)\n"
          "    pron = 'il' if genres.get(sujet) == 'masculin' else 'elle'\n"
          "    liaison = '-t-' if vc[-1:] in 'aeéè' else '-'\n"
          "    return _gn(sujet) + ' ' + vc + liaison + pron + ' ' + _gn(objet) + ' ?'")
    REL = (("question", _Q),)

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = list(dict.fromkeys(f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL))
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurNegationPhrase:
    """
    NÉGATION (PRODUCTION — 2026-06-18). 3ᵉ modalité de phrase (après déclaratif/interrogatif) : tourner un sens en
    phrase NÉGATIVE par encadrement ne…pas. `nier(sujet, verbe, objet, genres)` -> « le chat ne mange pas la souris ».
    Gère l'élision n' devant voyelle (aimer -> « n'aime pas »). Mêmes helpers article/conjugaison que la génération.

    PORTÉE HONNÊTE : noms + verbes réguliers -er / 2ᵉ groupe -ir. Hors portée (forme FAUSSE rejetée par le held-out) :
    verbes irréguliers (prendre -> 'prend' ; la brique laisse 'prendre').
    """

    _DEF = GenerateurGeneration._DEF
    _N = ("    sujet, verbe, objet, genres = args[0], args[1], args[2], args[3]\n" + _DEF +
          "    vc = _conj(verbe)\n"
          "    neg = \"n'\" if vc[:1] in 'aeiouéèêh' else 'ne '\n"
          "    return _gn(sujet) + ' ' + neg + vc + ' pas ' + _gn(objet)")
    REL = (("nier", _N),)

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = list(dict.fromkeys(f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL))
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurComparatif:
    """
    COMPARATIF (PRODUCTION + COGNITION — 2026-06-18). Exprime une COMPARAISON entre deux entités via un adjectif :
    `comparatif(a, b, adjectif, genres, degre)` -> « le chat est plus grand que la souris ». degre ∈ {plus, moins,
    aussi}. L'adjectif S'ACCORDE au sujet a (féminin régulier = +e : « la souris est plus grande que le chat »).
    Mêmes helpers article que la génération.

    PORTÉE HONNÊTE : noms + adjectifs à féminin RÉGULIER (+e). Hors portée (forme FAUSSE rejetée par le held-out) :
    féminins irréguliers (beau -> 'belle', la brique dit 'beaue'). Féminin irrégulier = info LEXICALE -> mur net.
    """

    _DEF = GenerateurGeneration._DEF
    _C = ("    a, b, adj, genres, degre = args[0], args[1], args[2], args[3], args[4]\n" + _DEF +
          "    acc = adj + 'e' if genres.get(a) == 'féminin' else adj\n"
          "    return _gn(a) + ' est ' + degre + ' ' + acc + ' que ' + _gn(b)")
    REL = (("comparatif", _C),)

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = list(dict.fromkeys(f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL))
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurAnalogie:
    """
    ANALOGIE / TRANSFERT (brique COMPRÉHENSION — 2026-06-18, insight Yohan : un motif appris dans un domaine se réutilise
    et s'adapte dans un autre). « a est à b ce que c est à ? » : on identifie la RELATION qui lie a→b, puis on l'applique
    à c. `analogie(relations, a, b, c)` -> d ; `meme_relation(relations, a, b, c, d)` -> a→b et c→d partagent-ils une
    relation ? `relations` = triplets (sujet, relation, objet). AGNOSTIQUE : le même mécanisme transfère un motif
    GÉOGRAPHIE (capitale_de) comme un motif FAMILLE (mère_de) — la réflexion n'est pas bornée par domaine.

    Famille bornée (2). HONNÊTE : aucune relation commune / pas d'image -> None / False.
    """

    _ANALOGIE = ("    relations, a, b, c = args[0], args[1], args[2], args[3]\n"
                 "    rels = {_r for _x, _r, _y in relations if _x == a and _y == b}\n"
                 "    for _x, _r, _y in relations:\n"
                 "        if _x == c and _r in rels:\n            return _y\n"
                 "    return None")
    _MEME = ("    relations, a, b, c, d = args[0], args[1], args[2], args[3], args[4]\n"
             "    rab = {_r for _x, _r, _y in relations if _x == a and _y == b}\n"
             "    rcd = {_r for _x, _r, _y in relations if _x == c and _y == d}\n"
             "    return bool(rab & rcd)")
    REL = (("analogie", _ANALOGIE), ("meme_relation", _MEME))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.REL]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.REL)


class GenerateurSerie:
    """
    PLUS LONGUE SÉRIE — état à travers la séquence (run-length) : la plus longue suite consécutive où une RELATION
    entre voisins tient. Un schéma stateful figé (best/cur), RELS ∈ comparaisons. plus_longue_serie = run de
    `==` ; plus_longue_croissante = run de `>`. Borné (|rels|), honnête.
    """

    RELS = ("==", ">", "<", ">=", "<=")

    def __init__(self, rels=None, seed: int = 0):
        self._rels = tuple(rels) if rels is not None else self.RELS
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [
            (f"def {g}(*args, **kwargs):\n    best = cur = 1 if args[0] else 0\n"   # liste vide -> 0 (pas 1)
             f"    for i in range(1, len(args[0])):\n"
             f"        cur = cur + 1 if args[0][i] {rel} args[0][i - 1] else 1\n"
             f"        best = best if best > cur else cur\n    return best\n")
            for rel in self._rels]
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._rels)


class GenerateurGenererTester:
    """
    GÉNÉRER-ET-TESTER — le n-ième entier satisfaisant un PRÉDICAT confirmé (recherche bornée par le compte).

    Schéma : `count=0; k=0; while count < n: k+=1; if pred(k): count+=1; return k`. k commence à 0 puis est
    incrémenté AVANT le test -> la valeur k=1 EST testée (sinon off-by-one : un prédicat vrai en 1 serait sauté).
    Le while est cadré par le JUGE (une recherche qui ne termine pas dépasse le timeout). nieme_premier =
    pred=is_prime ; nieme_pair = pred=is_pair. Borné (|prédicats|), honnête (sans prédicat, rien).
    """

    def __init__(self, predicats, seed: int = 0):
        self._predicats = list(predicats)
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        preds = [(nom, src) for nom, src in self._predicats if nom != g]
        cands = [
            (f"{psrc}def {g}(*args, **kwargs):\n    count = 0\n    k = 0\n"
             f"    while count < args[0]:\n        k += 1\n        if {pn}(k):\n            count += 1\n    return k\n")
            for pn, psrc in preds]
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._predicats)


class GenerateurInvention:
    """
    INVENTION par MUTATION — minter un atome NEUF (le mur d'APRÈS, voie interne).

    Tout le reste COMPOSE des atomes donnés. Ici on en FABRIQUE un nouveau, sans modèle externe :
    on PERTURBE structurellement un atome CONFIRMÉ (change un pas de slice, un opérateur, une
    constante, un indice, allonge une chaîne de produits) et on laisse le JUGE garder ce qui marche.
    C'est borné (on part du confirmé, on n'énumère pas tout le langage) et honnête : sans l'atome
    source, rien à muter -> rien ne sort. Ce n'est pas « seeder la réponse » : `reverse` n'est pas
    donné, il ÉMERGE en mutant le pas d'un slice générique ; `cube` émerge en allongeant `x*x`.

    Décision (fork invention, tranchée avec Yohan) : MUTATION de l'existant, pas énumération d'un
    substrat (le moins cher, le moins explosif, dans l'esprit brique par brique). Tenu SÉPARÉ de
    l'orchestrateur : l'invention est la couche du mur d'après, pas un étage de la composition.

    Un atome minté et confirmé est unaire-appelable (`g(args[0])`) -> il rejoint le registre comme
    n'importe quel succès (compounding) : on peut ensuite COMPOSER sur de l'INVENTÉ.
    """

    def __init__(self, atomes, seed: int = 0, comparaisons: bool = True):
        # atomes : liste de (nom, source) — des primitives/ops/prédicats CONFIRMÉS, la matière à muter.
        self._atomes = list(atomes)
        self._seed = seed
        # comparaisons : M5 (échange d'opérateur de COMPARAISON) — togglable pour l'A/B « mutation
        # des comparaisons ». ON par défaut ; inerte sur les atomes sans nœud Compare.
        self._comparaisons = comparaisons

    @staticmethod
    def _expr_retour(source: str):
        """L'expression du `return` de l'atome (ce qu'on mute), ou None."""
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Return) and node.value is not None:
                return node.value
        return None

    @staticmethod
    def _par_site(expr, applicable, mute):
        """Applique `mute` au i-ème nœud `applicable`, pour CHAQUE i -> une variante par SITE.
        (Un atome a souvent plusieurs sites mutables — ex. `args[0] + 1` a deux constantes : l'indice
        `0` ET l'opérande `1`. Ne muter que le premier raterait `args[0] + 2`.) Comptage et mutation
        partagent le MÊME parcours (post-ordre) -> les index s'alignent."""
        def parcours(cible, st):
            class V(ast.NodeTransformer):
                def visit(self, node):
                    node = self.generic_visit(node)
                    if applicable(node):
                        if st["i"] == cible:
                            node = mute(node); st["fait"] = True
                        st["i"] += 1
                    return node
            return V().visit(copy.deepcopy(expr))

        compte = {"i": 0, "fait": False}
        parcours(-1, compte)                       # -1 : ne mute rien, compte les sites
        variantes = []
        for cible in range(compte["i"]):
            st = {"i": 0, "fait": False}
            arbre = parcours(cible, st)
            if st["fait"]:
                variantes.append(arbre)
        return variantes

    def _mutations(self, expr):
        """Variantes de `expr` par mutations structurelles GÉNÉRIQUES, sur CHAQUE site applicable.
        Chaque variante est un AST complet indépendant, prêt à être unparse."""
        variantes = []

        def est_const_int(n):
            return isinstance(n, ast.Constant) and isinstance(n.value, int) and not isinstance(n.value, bool)

        # M1 — pas de slice (None -> -1, 2, -2) : fait émerger reverse/échantillonnage.
        def pose_pas(_pas):
            def mute(n):
                n.step = ast.Constant(_pas); return n
            return mute
        for pas in (-1, 2, -2):
            variantes += self._par_site(expr, lambda n: isinstance(n, ast.Slice), pose_pas(pas))

        # M2 — allonger une chaîne de produits (x*x -> x*x*x) : fait émerger cube, etc.
        def allonge(n):
            return ast.BinOp(left=copy.deepcopy(n), op=ast.Mult(), right=copy.deepcopy(n.right))
        variantes += self._par_site(
            expr, lambda n: isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult), allonge)

        # M3 — bricoler une constante numérique (c -> c±1, 2c, -c).
        def pose_const(_fab):
            def mute(n):
                try:
                    n.value = _fab(n.value)
                except Exception:
                    pass
                return n
            return mute
        for fab in (lambda c: c + 1, lambda c: c - 1, lambda c: c * 2, lambda c: -c):
            variantes += self._par_site(expr, est_const_int, pose_const(fab))

        # M4 — échanger un opérateur binaire (Mult/Add/Sub/Pow/FloorDiv/Mod).
        def pose_op(_Op):
            def mute(n):
                n.op = _Op(); return n
            return mute
        for OpCls in (ast.Mult, ast.Add, ast.Sub, ast.Pow, ast.FloorDiv, ast.Mod):
            variantes += self._par_site(
                expr, lambda n, _O=OpCls: isinstance(n, ast.BinOp) and not isinstance(n.op, _O), pose_op(OpCls))

        # M5 — échanger un opérateur de COMPARAISON (Gt/Lt/GtE/LtE/Eq/NotEq) : fait émerger les
        # prédicats inverses (`x > 0` -> `x < 0` = est_negatif). Togglable (A/B) ; le mur d'avant.
        if self._comparaisons:
            def pose_cmp(_Op):
                def mute(n):
                    n.ops = [_Op()] + list(n.ops[1:]); return n
                return mute
            for OpCls in (ast.Lt, ast.Gt, ast.GtE, ast.LtE, ast.Eq, ast.NotEq):
                variantes += self._par_site(
                    expr, lambda n, _O=OpCls: isinstance(n, ast.Compare) and not isinstance(n.ops[0], _O),
                    pose_cmp(OpCls))

        return variantes

    def _variantes_atome(self, g: str, src: str) -> list[str]:
        """Les variantes de mutation d'UN atome (sa source) pour la cible nommée `g`, dé-dupliquées.
        Isolé pour que l'invention DIRIGÉE puisse muter atome par atome dans son propre ordre."""
        expr = self._expr_retour(src)
        if expr is None:
            return []
        out = []
        for variante in self._mutations(expr):
            try:
                corps = ast.unparse(variante)
            except Exception:
                continue
            out.append(f"def {g}(*args, **kwargs):\n    return {corps}\n")
        return list(dict.fromkeys(out))

    def propose(self, prompt: str, n: int) -> list[str]:
        m = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not m:
            return []
        g = m.group(1)
        candidats = []
        for _, src in self._atomes:
            candidats += self._variantes_atome(g, src)
        candidats = list(dict.fromkeys(candidats))   # dé-dup global
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(candidats)
        return candidats[:n] if n <= len(candidats) else candidats

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._atomes)   # passif : plus d'atomes confirmés = plus de matière à muter


class GenerateurInventionDirige:
    """
    CURIOSITÉ DIRIGÉE — diriger l'invention vers le trou, par la DISCORDE cerveau/cœur.

    L'invention de base (`GenerateurInvention`) mute TOUS les atomes et SHUFFLE : l'ordre du bon
    atome est laissé au hasard. Quand le registre grandit (compounding), le bon atome se noie ->
    coût qui explose. Ici on RÉORDONNE les atomes-à-muter AVANT de muter (comme `GenerateurDirige`
    réordonne des candidats : rien jeté, couverture intacte), avec DEUX signaux :
      - CERVEAU (`predicteur.rang` sur la source) : syntaxique, bon marché, PRÉCIS sur le connu,
        FAIBLE sur la nouveauté (mesuré : il ENTERRE le neuf).
      - CŒUR (`coeur(src)` injecté = crédit partiel rendu par le JUGE sur les tests visibles) :
        behavioral, CONSULTATIF, coûte une exécution -> calculé seulement sur les top-N du cerveau.
    La DISCORDE = un atome que le cerveau enterre mais que le cœur trouve CHAUD : on le mute EN
    PREMIER. Honnêteté (la ligne rouge tranchée) : le cœur lit le crédit du juge, JAMAIS le texte
    des asserts ; il ne fait que RÉORDONNER -> au pire il fait perdre des appels, jamais un faux
    skill (seul le held-out promeut). La discorde dit OÙ chercher ; le juge seul dit QUOI garder.
    """

    def __init__(self, base: "GenerateurInvention", predicteur, coeur, topn: int = 5):
        self._base = base            # la matière (atomes) + la mécanique de mutation
        self._pred = predicteur      # le cerveau
        self._coeur = coeur          # callable src -> crédit partiel (le cœur, injecté)
        self._topn = topn            # borne de coût du cœur (Fork C)

    def _ordre_atomes(self):
        """Renvoie les atomes réordonnés par discorde, sans rien jeter (rang cerveau pour le reste)."""
        atomes = self._base._atomes
        par_cerveau = sorted(atomes, key=lambda a: self._pred.rang(a[1]))
        retenus, reste = par_cerveau[:self._topn], par_cerveau[self._topn:]
        # DISCORDE : cœur décroissant (le chaud d'abord), puis rang cerveau croissant à cœur égal.
        ordre = sorted(retenus, key=lambda a: (-self._coeur(a[1]), self._pred.rang(a[1])))
        return ordre + reste

    def propose(self, prompt: str, n: int) -> list[str]:
        m = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not m:
            return []
        g = m.group(1)
        candidats = []
        for _, src in self._ordre_atomes():
            candidats += self._base._variantes_atome(g, src)
        candidats = list(dict.fromkeys(candidats))   # dé-dup global, garde la priorité (1ère occurrence)
        return candidats[:n] if n <= len(candidats) else candidats

    def apprendre(self, delta: float = 0.0) -> int:
        return self._base.apprendre(delta)


class GenerateurSubstrat:
    """
    INVENTION par ÉNUMÉRATION D'UN SUBSTRAT — le mur d'APRÈS la mutation.

    `valide_invention_portee` a MESURÉ le mur de la mutation : elle perturbe un nœud confirmé, donc
    elle ne crée pas de TOKEN de langage ABSENT de tous les atomes (méthode `.upper`, littéral `'aeiou'`
    + appartenance). La voie tranchée pour le franchir n'est PAS la mutation mais l'ÉNUMÉRATION d'un
    petit SUBSTRAT énumérable de gabarits — borné, sans modèle externe. On n'altère pas le confirmé :
    on ÉNUMÈRE un vocabulaire FIXE et explicite, et le juge garde ce qui marche.

    Borné et honnête : le substrat est petit et nommé ; ce qui n'y est pas n'est PAS atteint (il ne
    conjure pas un token arbitraire — il énumère un vocabulaire choisi). Un atome minté rejoint le
    registre comme tout succès (route) -> on peut composer dessus. C'est la couche d'invention la plus
    chère/explosive : à garder en DERNIER recours, derrière la mutation (qui, elle, part du confirmé).
    """

    # Le substrat : petit, explicite, énumérable. (Élargissable comme TYPES_RICHES : un seul levier.)
    METHODES = ("upper", "lower", "strip", "title", "capitalize", "swapcase")
    LITTERAUX = ("'aeiou'", "'0123456789'")

    def __init__(self, methodes=None, litteraux=None, seed: int = 0):
        self._methodes = tuple(methodes) if methodes is not None else self.METHODES
        self._litteraux = tuple(litteraux) if litteraux is not None else self.LITTERAUX
        self._seed = seed

    def _gabarits(self):
        # méthode unaire sur l'argument (token `.M()` absent du confirmé)
        for m in self._methodes:
            yield f"args[0].{m}()"
        # appartenance d'un caractère à un littéral énuméré (token littéral + `in` absents)
        for lit in self._litteraux:
            yield f"any(c in {lit} for c in args[0])"
            yield f"all(c in {lit} for c in args[0])"
            yield f"sum(c in {lit} for c in args[0])"   # COMPTAGE par appartenance (count_vowels)

    def propose(self, prompt: str, n: int) -> list[str]:
        m = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not m:
            return []
        g = m.group(1)
        cands = [f"def {g}(*args, **kwargs):\n    return {corps}\n"
                 for corps in dict.fromkeys(self._gabarits())]
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self._methodes) + len(self._litteraux)


class GenerateurDirige:
    """
    DIRECTION par la compréhension — « diriger au lieu de brasser ».

    Enveloppe N'IMPORTE QUEL générateur de base et RÉORDONNE ses candidats avec un
    `Predicteur` : les prédits-utiles d'abord, le reste ensuite, les réfutés-récents
    en dernier. Il ne JETTE jamais rien (réordonne, ne filtre pas) -> la couverture
    reste EXACTEMENT celle du générateur de base (au pire même résultat, jamais moins).
    La boucle, qui juge dans l'ordre et s'arrête au 1er succès, atteint donc le succès
    en MOINS d'appels au juge : c'est là, et seulement là, qu'on économise.

    Honnêteté : la direction ne décide JAMAIS de la réussite — seul le juge tranche.
    Le prédicteur ne fait que proposer un ORDRE ; un faux pari coûte un appel au juge,
    puis nourrit la mémoire courte (`note_echec`) pour ne pas être re-tenté en premier.
    """

    def __init__(self, base: Generateur, predicteur):
        self._base = base
        self._predicteur = predicteur

    def propose(self, prompt: str, n: int) -> list[str]:
        candidats = self._base.propose(prompt, n)
        # Tri STABLE par promesse croissante (rang 0 d'abord) : à rang égal, l'ordre
        # du générateur de base est préservé -> aucune information inventée.
        return sorted(candidats, key=self._predicteur.rang)

    def apprendre(self, delta: float = 0.0):
        return self._base.apprendre(delta) if hasattr(self._base, "apprendre") else 0


class GenerateurReutilisateur:
    """
    G1 — RÉUTILISATION DU STORE (la mémoire).

    Au lieu de deviner au hasard (G0), il PUISE dans les succès vérifiés du store
    pour la tâche demandée, et en propose des copies (+ mutations légères). Il
    n'invente rien : il REUTILISE ce qui a déjà marché. C'est « ne jamais réoublier
    ce qu'on a déjà réussi », et construire dessus.

    Apprentissage PASSIF : G1 ne s'entraîne pas par étape — il s'améliore tout seul
    à mesure que le store grandit (la boucle y archive les succès). Plus de matière
    vérifiée -> plus de couverture, automatiquement.

    Honnêteté (démarrage à froid) : sur un store VIDE, ou pour une tâche jamais
    réussie, G1 n'a rien à réutiliser -> il retombe au plancher. D'où G2 ensuite,
    qui sème la première matière.
    """

    def __init__(self, store, seed: int = 0, p_mutation: float = 0.3):
        self._store = store
        self._seed = seed
        self._p_mutation = p_mutation

    def propose(self, prompt: str, n: int) -> list[str]:
        connues = [s.solution for s in self._store if s.prompt == prompt]
        if not connues:
            return []  # rien de vérifié à réutiliser pour cette tâche
        rng = random.Random(f"{self._seed}|{len(connues)}|{prompt}")
        sorties = []
        for _ in range(n):
            base = rng.choice(connues)
            sorties.append(_mute(base, rng) if rng.random() < self._p_mutation else base)
        return sorties

    def apprendre(self, delta: float = 0.0) -> int:
        """No-op : G1 apprend en CONTINU via le store, pas par étape. Présent pour
        rester branchable dans la session (B9). Renvoie la taille du store."""
        return len(self._store)


class GenerateurApprenantMulti:
    """
    Comme GenerateurApprenant, mais sur PLUSIEURS tâches à la fois — pour piloter
    la session complète (B9) avec un curriculum. À compétence c, pour la tâche
    demandée, rend sa solution de RÉFÉRENCE (correcte, généralise) avec proba c,
    sinon un stub faux. Simule UN SEUL modèle qui s'améliore globalement (la vision).

    Connaît les tâches (référence + point d'entrée) : c'est un factice de test, qui
    sera remplacé par le vrai LLM (lequel n'aura PAS accès aux références).
    """

    def __init__(self, taches, competence: float = 0.0, seed: int = 0):
        self._par_prompt = {t.prompt: t for t in taches}
        self.competence = competence
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        tache = self._par_prompt.get(prompt)
        if tache is None:
            return []
        stub = f"def {tache.point_entree}(*args, **kwargs):\n    return None\n"
        rng = random.Random(f"{self._seed}|{self.competence:.4f}|{prompt}")
        return [tache.solution_ref if rng.random() < self.competence else stub
                for _ in range(n)]

    def apprendre(self, delta: float = 0.2) -> float:
        self.competence = min(1.0, self.competence + delta)
        return self.competence


class GenerateurIteration:
    """
    ITÉRATION / POINT-FIXE — répéter une transformation scalaire JUSQU'À une condition (2026-06-19, lacune MESURÉE par
    gap_probe : digital_root, collatz_steps, hors de portée des autres étages). La non-terminaison est cadrée par le
    JUGE (timeout) — la réalité écarte les pas divergents, pas nous (même garde que GenerateurWhile). Deux schémas :

        A (valeur au point fixe) : n = args[0]; while n {cmp} {seuil}: n = {pas} ; return n
        B (compte jusqu'à cible) : n = args[0]; c = 0; while n != {cible}: n = {pas}; c += 1 ; return c

    `pas` ∈ petit jeu d'ops scalaires (somme des chiffres -> digital_root ; collatz ; moitié ; -1). Borné
    (|pas|×(|stops|+|cibles|)), honnête (un pas qui diverge -> timeout -> rejeté). digital_root = A(somme_chiffres,
    n>=10) ; collatz_steps = B(collatz, cible=1).
    """

    PAS = (
        ("somme_chiffres", "sum(int(d) for d in str(n))"),
        ("collatz", "(n // 2 if n % 2 == 0 else 3 * n + 1)"),
        ("moitie", "n // 2"),
        ("moins_un", "n - 1"),
    )
    STOPS = ((">=", "10"), (">", "1"), ("!=", "0"))
    CIBLES = ("1", "0")

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for _, pas in self.PAS:
            for cmp_, seuil in self.STOPS:
                cands.append(f"def {g}(*args, **kwargs):\n    n = args[0]\n    while n {cmp_} {seuil}:\n"
                             f"        n = {pas}\n    return n\n")
            for cible in self.CIBLES:
                cands.append(f"def {g}(*args, **kwargs):\n    n = args[0]\n    c = 0\n    while n != {cible}:\n"
                             f"        n = {pas}\n        c += 1\n    return c\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.PAS)


class GenerateurAccumulateurCourant:
    """
    ACCUMULATEUR COURANT (Kadane & co) — balayage à DEUX états : `cur` (ÉTEND vs REDÉMARRE) et `best` (extremum
    courant). Lacune MESURÉE par gap_probe (max_subarray, hors de portée des plis/fenêtres simples). Schéma borné :

        xs = args[0]; cur = best = xs[0]
        for x in xs[1:]:
            cur  = {ext}(x, cur + x)     # étendre la sous-séquence vs repartir de x
            best = {agg}(best, cur)
        return best

    ext/agg ∈ {max, min} -> 4 candidats. max_subarray = ext=max, agg=max (max sous-tableau contigu) ; la variante
    min donne le min sous-tableau. Honnête (liste vide -> IndexError -> rejeté par le juge). C'est le pont vers la
    famille DP « accumulateur à un état glissant ».
    """

    AGG = ("max", "min")

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for ext in self.AGG:
            for agg in self.AGG:
                cands.append(f"def {g}(*args, **kwargs):\n    xs = args[0]\n    cur = best = xs[0]\n"
                             f"    for x in xs[1:]:\n        cur = {ext}(x, cur + x)\n"
                             f"        best = {agg}(best, cur)\n    return best\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.AGG) ** 2


class GenerateurEquilibre:
    """
    SCAN À COMPTEUR DE PROFONDEUR (équilibrage) — balayer une chaîne en maintenant une profondeur (ouvrant +1, fermant
    -1) avec COURT-CIRCUIT dès que `d < 0`, puis tester `d == 0`. Lacune MESURÉE par gap_probe (is_balanced, hors de
    portée des plis/fenêtres : l'état `d` est SÉQUENTIEL et le rejet-négatif est un retour anticipé). Un seul schéma,
    sur 3 paires de délimiteurs :

        d=0 ; pour ch : +1 si {o}, (-1 si {c}, return False si d<0) ; return d == 0

    NB : la simple « profondeur max » (sans court-circuit) est déjà couverte par l'étage `serie` (mesuré, généralise) ->
    NON incluse ici (pas de masquage, cf. test du diable). Borné (|paires|=3). Honnête : input non-itérable -> TypeError
    -> rejeté par le juge. is_balanced = paire ('(',')').
    """

    PAIRES = (("(", ")"), ("[", "]"), ("{", "}"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = []
        for o, c in self.PAIRES:
            cands.append(f"def {g}(*args, **kwargs):\n    s = args[0]\n    d = 0\n    for ch in s:\n"
                         f"        if ch == {o!r}:\n            d += 1\n        elif ch == {c!r}:\n"
                         f"            d -= 1\n            if d < 0:\n                return False\n    return d == 0\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.PAIRES)


class GenerateurPremierUnique:
    """
    FRÉQUENCE PUIS PREMIER SATISFAISANT — deux passes sur une séquence : compter, puis rendre le 1er élément de
    fréquence 1 (avec un défaut « rien trouvé »). Lacune MESURÉE par gap_probe (first_unique_char). Deux schémas :

        A (l'élément, défaut '') : pour ch dans s : si s.count(ch) == 1 : return ch ; return ''
        B (son index, défaut -1) : pour i,ch : si s.count(ch) == 1 : return i ; return -1

    Borné (2). Honnête : la sémantique exacte du défaut est tranchée par les exemples (réalité). first_unique_char = A.
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [
            f"def {g}(*args, **kwargs):\n    s = args[0]\n    for ch in s:\n        if s.count(ch) == 1:\n"
            f"            return ch\n    return ''\n",
            f"def {g}(*args, **kwargs):\n    s = args[0]\n    for i, ch in enumerate(s):\n        if s.count(ch) == 1:\n"
            f"            return i\n    return -1\n",
        ]
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 2


class GenerateurChevauchement:
    """
    BALAYAGE D'INTERVALLES (sweep-line) — événements ±1 aux bornes, tri, max courant du compte simultané. Lacune
    MESURÉE par gap_probe (max_overlap : nombre max d'intervalles se chevauchant). La subtilité = le départage des
    bornes égales (intervalles FERMÉS [s,e] : ouvre avant ferme ; ou DEMI-OUVERTS [s,e) : ferme avant ouvre) -> 2
    variantes, la réalité tranche :

        evts = [(s, ORDRE_OUV), (e, ORDRE_FERM) ...] ; tri ; cur ±1 ; best = max
    Borné (2). Honnête (input non-itérable ou bornes non-paires -> erreur -> rejet). max_overlap = variante fermée.
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        # (ordre_ouverture, ordre_fermeture) au sein d'une même coordonnée : (0,1)=fermé (ouvre d'abord), (1,0)=demi-ouvert.
        cands = []
        for oo, of in ((0, 1), (1, 0)):
            cands.append(
                f"def {g}(*args, **kwargs):\n    intervals = args[0]\n    evts = []\n"
                f"    for s, e in intervals:\n        evts.append((s, {oo}))\n        evts.append((e, {of}))\n"
                f"    evts.sort()\n    cur = 0\n    best = 0\n    for _, typ in evts:\n"
                f"        cur += 1 if typ == {oo} else -1\n        if cur > best:\n            best = cur\n    return best\n")
        # INTERVAL SCHEDULING (gap_probe 14ᵉ vague, transfer web) — fusion, ordonnancement, insertion, longueur d'union.
        cands.append(
            f"def {g}(*args, **kwargs):\n    _iv = sorted([list(_x) for _x in args[0]])\n    _res = []\n"
            f"    for _s, _e in _iv:\n        if _res and _s <= _res[-1][1]:\n            _res[-1][1] = max(_res[-1][1], _e)\n"
            f"        else:\n            _res.append([_s, _e])\n    return _res\n")                       # merge_intervals
        cands.append(
            f"def {g}(*args, **kwargs):\n    _iv = sorted(args[0], key=lambda _x: _x[1])\n    _cnt = 0\n"
            f"    _end = float('-inf')\n    for _s, _e in _iv:\n        if _s >= _end:\n            _cnt += 1\n"
            f"            _end = _e\n    return _cnt\n")                                                   # max_non_overlapping
        cands.append(
            f"def {g}(*args, **kwargs):\n    _iv = [list(_x) for _x in args[0]]\n    _new = list(args[1])\n"
            f"    _res = []\n    _i, _n = 0, len(_iv)\n    while _i < _n and _iv[_i][1] < _new[0]:\n"
            f"        _res.append(_iv[_i])\n        _i += 1\n    while _i < _n and _iv[_i][0] <= _new[1]:\n"
            f"        _new[0] = min(_new[0], _iv[_i][0])\n        _new[1] = max(_new[1], _iv[_i][1])\n        _i += 1\n"
            f"    _res.append(_new)\n    while _i < _n:\n        _res.append(_iv[_i])\n        _i += 1\n    return _res\n")  # insert_interval
        cands.append(
            f"def {g}(*args, **kwargs):\n    _iv = sorted([list(_x) for _x in args[0]])\n    _tot = 0\n"
            f"    _cs = _ce = None\n    for _s, _e in _iv:\n        if _cs is None:\n            _cs, _ce = _s, _e\n"
            f"        elif _s <= _ce:\n            _ce = max(_ce, _e)\n        else:\n            _tot += _ce - _cs\n"
            f"            _cs, _ce = _s, _e\n    if _cs is not None:\n        _tot += _ce - _cs\n    return _tot\n")  # union_length
        cands.append(
            f"def {g}(*args, **kwargs):\n    _iv = sorted(args[0])\n"
            f"    return all(_iv[_i][0] >= _iv[_i - 1][1] for _i in range(1, len(_iv)))\n")               # can_attend_meetings
        cands.append(
            f"def {g}(*args, **kwargs):\n    _p = sorted(args[0], key=lambda _x: _x[1])\n"
            f"    if not _p:\n        return 0\n    _a = 1\n    _end = _p[0][1]\n    for _s, _e in _p[1:]:\n"
            f"        if _s > _end:\n            _a += 1\n            _end = _e\n    return _a\n")          # min_arrows (burst balloons)
        cands.append(
            f"def {g}(*args, **kwargs):\n    _iv = sorted(args[0], key=lambda _x: _x[1])\n"
            f"    if not _iv:\n        return 0\n    _keep = 1\n    _end = _iv[0][1]\n    for _s, _e in _iv[1:]:\n"
            f"        if _s >= _end:\n            _keep += 1\n            _end = _e\n    return len(_iv) - _keep\n")  # erase_overlap
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 9


class GenerateurDPInt:
    """
    DP SUR ENTIER (campagne « <100 partout », 2026-06-20) — petit étage DÉDIÉ aux problèmes de programmation dynamique
    dont l'ENTRÉE et la SORTIE sont des entiers (n -> int). MOTIVÉ PAR LA MESURE : integer_break / perfect_squares
    vivent dans le gros `tableaux` (45 cand.) -> même clé chaude, round-robin sur 6 étages prédits = ~170-203 appels
    (plancher architectural). Un étage dédié de 4 templates DP les résout à l'index 0-3 -> routé < 30. Famille BORNÉE
    (4), templates STRUCTURELLEMENT distincts (pas un lookup) : partition-produit, somme-de-carrés, nombres de Hamming
    (2-3-5), Catalan. Honnête : entrée non-entière -> erreur -> rejet par le juge ; clé (1,int,int) -> le routeur l'isole.
    """

    TAB = (("integer_break",
            "    _n = args[0]\n    if _n <= 3:\n        return _n - 1\n    _dp = [0, 1, 2, 3] + [0] * (_n - 3)\n"
            "    for _i in range(4, _n + 1):\n        _dp[_i] = max(_j * _dp[_i - _j] for _j in range(1, _i))\n"
            "    return _dp[_n]"),
           ("perfect_squares",
            "    _n = args[0]\n    _dp = [0] + [_n + 1] * _n\n    for _i in range(1, _n + 1):\n        _k = 1\n"
            "        while _k * _k <= _i:\n            _dp[_i] = min(_dp[_i], _dp[_i - _k * _k] + 1)\n            _k += 1\n"
            "    return _dp[_n]"),
           ("nth_ugly_number",
            "    _n = args[0]\n    _u = [1]\n    _a = _b = _c = 0\n    while len(_u) < _n:\n"
            "        _x = min(_u[_a] * 2, _u[_b] * 3, _u[_c] * 5)\n        _u.append(_x)\n"
            "        if _x == _u[_a] * 2:\n            _a += 1\n        if _x == _u[_b] * 3:\n            _b += 1\n"
            "        if _x == _u[_c] * 5:\n            _c += 1\n    return _u[_n - 1]"),
           ("num_trees",
            "    _n = args[0]\n    _dp = [1] + [0] * _n\n    for _i in range(1, _n + 1):\n"
            "        _dp[_i] = sum(_dp[_j] * _dp[_i - 1 - _j] for _j in range(_i))\n    return _dp[_n]"))

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        cands = [f"def {g}(*args, **kwargs):\n{corps}\n" for _, corps in self.TAB]
        cands = list(dict.fromkeys(cands))
        random.Random(f"{self._seed}|{prompt}").shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return len(self.TAB)


class GenerateurDP2D:
    """
    PROGRAMMATION DYNAMIQUE 2D sur DEUX séquences — table dp[m+1][n+1] remplie par récurrence (diagonale/haut/gauche).
    Lacune MESURÉE par gap_probe (lcs_len, edit_distance — le plus dur : ÉTAT 2D, hors de tout étage 1D). Famille bornée
    par 3 axes indépendants (2×2×2 = 8) :

        INIT  : bords à 0 (LCS) | bords indexés dp[i][0]=i, dp[0][j]=j (edit)
        MATCH (a[i-1]==b[j-1]) : dp[i-1][j-1]+1 (LCS) | dp[i-1][j-1] (edit, recopie)
        SINON : max(dp[i-1][j], dp[i][j-1]) (LCS) | 1 + min(dp[i-1][j-1], dp[i-1][j], dp[i][j-1]) (edit)

    lcs_len = (0, +1, max) ; edit_distance = (index, recopie, 1+min). Les combos croisés sont inoffensifs (ne passent
    pas les exemples). Honnête : args[0]/args[1] non séquençables -> erreur -> rejet par le juge.
    """

    def __init__(self, seed: int = 0):
        self._seed = seed

    def propose(self, prompt: str, n: int) -> list[str]:
        mg = re.search(r"def\s+(\w+)\s*\(", prompt)
        if not mg:
            return []
        g = mg.group(1)
        inits = {
            "zero": "",
            "index": "    for i in range(m + 1):\n        dp[i][0] = i\n    for j in range(n + 1):\n        dp[0][j] = j\n",
        }
        matches = {
            "plus1": "dp[i - 1][j - 1] + 1",
            "copie": "dp[i - 1][j - 1]",
        }
        sinons = {
            "max": "max(dp[i - 1][j], dp[i][j - 1])",
            "min1": "1 + min(dp[i - 1][j - 1], dp[i - 1][j], dp[i][j - 1])",
        }
        cands = []
        for ini in inits.values():
            for mt in matches.values():
                for si in sinons.values():
                    cands.append(
                        f"def {g}(*args, **kwargs):\n    a = args[0]\n    b = args[1]\n    m = len(a)\n    n = len(b)\n"
                        f"    dp = [[0] * (n + 1) for _ in range(m + 1)]\n{ini}"
                        f"    for i in range(1, m + 1):\n        for j in range(1, n + 1):\n"
                        f"            if a[i - 1] == b[j - 1]:\n                dp[i][j] = {mt}\n"
                        f"            else:\n                dp[i][j] = {si}\n    return dp[m][n]\n")
        cands = list(dict.fromkeys(cands))
        rng = random.Random(f"{self._seed}|{prompt}")
        rng.shuffle(cands)
        return cands[:n] if n <= len(cands) else cands

    def apprendre(self, delta: float = 0.0) -> int:
        return 8


class GenerateurOrchestre:
    """
    L'ORCHESTRATEUR — une seule façade sur TOUTE la trousse, en ESCALADE DIRIGÉE.

    Le but : que le SYSTÈME assemblé résolve une tâche sans qu'on lui dise quel mécanisme
    employer. Il tente du MOINS cher au PLUS cher et s'arrête au 1er succès (escalade) :

        réutilisation -> recombinaison -> fusion d'expressions -> composition -> jointure -> multi-entrée -> pli
        [-> branchement, puis boucle bornée, si predicats fournis : contrôle (ternaire / accumuler-jusqu'à-arrêt)]
        [-> invention, si inventer=True : dernier recours, minte un atome neuf quand tout a échoué]

    L'escalade est le prior principal (les solutions simples sont plus fréquentes et moins
    chères à juger ; on n'atteint les étages combinatoires que si rien de plus simple ne passe).
    DANS chaque étage, un `Predicteur` optionnel ORDONNE les candidats (prédits-utiles d'abord,
    réfutés-récents en dernier) — la direction (pt 2) gagne son rôle là où l'espace explose.

    Rétroaction (gérée par la boucle/session) : un succès confirmé — composés inclus — rejoint
    le `store` (fragments) ET le registre de `primitives`/`ops` (briques appelables) -> les étages
    supérieurs grandissent tout seuls : tours de skills en continu. Frontière étanche tenue :
    l'orchestrateur ne voit que le prompt, jamais les tests.
    """

    def __init__(self, store, primitives=None, ops=None, predicteur=None, seed: int = 0,
                 inventer: bool = False, predicats=None, comparaisons: bool = True, substrat: bool = False,
                 ordre_etages=None, profondeur_compo: int = 2, recurrence: bool = False,
                 boucle_while: bool = False, map_repli: bool = False, invariant: bool = False,
                 jointure_profonde: bool = False, predicat_mesures: bool = False,
                 positionnel: bool = False, mots: bool = False, multipasse: bool = False,
                 adjacence: bool = False, imbrique: bool = False, dict_accu: bool = False,
                 group_by: bool = False, serie: bool = False, generer_tester: bool = False,
                 comprehension_generale: bool = False, fenetre: bool = False, matrice: bool = False,
                 repetition: bool = False, index_ordonne: bool = False, sous_suite: bool = False,
                 paires: bool = False, run_length: bool = False, dict_transform: bool = False,
                 profond: bool = False, filtre_seuil: bool = False, matrice_reduce: bool = False,
                 dedup: bool = False, prefixe_commun: bool = False, monnaie: bool = False, cesar: bool = False,
                 record: bool = False, anticipation: bool = False, optimisation: bool = False,
                 ranking: bool = False, bits: bool = False, logique: bool = False, ensembles: bool = False,
                 statistiques: bool = False, conversion: bool = False, parsing: bool = False,
                 math_avance: bool = False, chiffres: bool = False, liste_transforms: bool = False,
                 chaines_avancees: bool = False, diviseurs: bool = False, graphe: bool = False,
                 combinatoire: bool = False, iteration: bool = False, acc_courant: bool = False,
                 equilibre: bool = False, premier_unique: bool = False, chevauchement: bool = False,
                 dp2d: bool = False, geometrie: bool = False, comptage_combinatoire: bool = False,
                 pile: bool = False, suite: bool = False, calendrier: bool = False,
                 graphe_connexite: bool = False, tableaux: bool = False, numerique: bool = False,
                 checksum: bool = False,
                 conjugaison: bool = False,
                 conjugaison2: bool = False, passe_compose: bool = False,
                 adverbe: bool = False, participe_present: bool = False,
                 imperatif: bool = False, conditionnel: bool = False, subjonctif: bool = False,
                 pluriel: bool = False, feminin: bool = False,
                 relation_lexicale: bool = False, sens_executable: bool = False,
                 intention: bool = False, desambiguisation: bool = False,
                 normalisation: bool = False, ancetre_commun: bool = False,
                 intrus: bool = False, analyse_phrase: bool = False,
                 comprehension_phrase: bool = False, accord_phrase: bool = False,
                 inference: bool = False, comprehension_definition: bool = False,
                 distance_semantique: bool = False, accord_correct: bool = False,
                 antonyme: bool = False, paraphrase: bool = False,
                 negation: bool = False, quantificateur: bool = False,
                 coreference: bool = False, temporel: bool = False,
                 comptage: bool = False, chemin: bool = False,
                 generation: bool = False, analogie: bool = False,
                 interrogation: bool = False, negation_phrase: bool = False,
                 comparatif: bool = False, dp_int: bool = False):
        self._store = store
        self._primitives = list(primitives or [])
        self._ops = list(ops or [])
        self._predicats = list(predicats or [])   # prédicats confirmés -> étage branchement (si non vide)
        self._predicteur = predicteur
        self._seed = seed
        # ordre_etages : None = escalade humaine canonique (défaut, comportement historique). Sinon, une
        # liste ORDONNÉE de noms d'étages -> orchestration QUELCONQUE (la RÉALITÉ choisit l'ordre/le
        # sous-ensemble, pas le prior humain) — pour la recherche d'architecture.
        self._ordre_etages = list(ordre_etages) if ordre_etages is not None else None
        self._profondeur_compo = profondeur_compo   # profondeur max de nidification (étage composition)
        self._recurrence = recurrence   # ajoute l'étage récurrence (2-états sur un compte) — opt-in
        self._boucle_while = boucle_while   # ajoute l'étage while (boucle pilotée par condition) — opt-in
        self._map_repli = map_repli   # ajoute l'étage map-repli (AGG(prim(x) for x)) — opt-in
        self._invariant = invariant   # ajoute l'étage invariant (x == prim(x)) — opt-in
        self._jointure_profonde = jointure_profonde   # étage jointure profonde (op(G(xs),D(xs))) — opt-in
        self._predicat_mesures = predicat_mesures   # étage prédicat-mesures (m1(x) CMP m2(x)) — opt-in
        self._positionnel = positionnel   # étage positionnel (op(AGG(xs[::2]),AGG(xs[1::2]))) — opt-in
        self._mots = mots   # étage mots (SEP.join(transform(split))) — opt-in
        self._multipasse = multipasse   # étage multi-passe (filtrer par agrégat du tout) — opt-in
        self._adjacence = adjacence   # étage adjacence (AGG(xs[i] REL xs[i-1])) — opt-in
        self._imbrique = imbrique   # étage imbriqué (REDUC(elt for x in xs for y in x)) — opt-in
        self._dict_accu = dict_accu   # étage dict-accumulateur ({k: count(k) for k in set}) — opt-in
        self._group_by = group_by   # étage group-by ({k: AGG(grp) par clé}) — opt-in
        self._serie = serie   # étage série (run-length stateful) — opt-in
        self._generer_tester = generer_tester   # étage générer-tester (n-ième satisfaisant pred) — opt-in
        self._comprehension_generale = comprehension_generale   # étage compréhension générale (transform+filtre+reduce) — opt-in
        self._fenetre = fenetre   # étage fenêtre glissante (REDUC(AGG(xs[i:i+k])) sur fenêtres contiguës) — opt-in
        self._matrice = matrice   # étage matrice 2D (agrégat par axe lignes/colonnes + diagonale) — opt-in
        self._repetition = repetition   # étage répétition comptée (op appliquée args[1] fois -> puissance) — opt-in
        self._index_ordonne = index_ordonne   # étage indexation ordonnée (sélection par rang + dichotomie) — opt-in
        self._sous_suite = sous_suite   # étage sous-suite monotone (DP O(n²), LIS et variantes) — opt-in
        self._paires = paires   # étage paires (∃ sur tous les couples i<j -> two_sum) — opt-in
        self._run_length = run_length   # étage run-length encode (compression stateful -> chaîne/paires) — opt-in
        self._dict_transform = dict_transform   # étage transformation de dict existant ({KEY:VAL for k,v in d}) — opt-in
        self._profond = profond   # étage récursion sur structure (réduit les feuilles, profondeur arbitraire) — opt-in
        self._filtre_seuil = filtre_seuil   # étage filtre paramétré (REDUC(x if x CMP args[1])) — opt-in
        self._matrice_reduce = matrice_reduce   # étage matrice+reduce (REDUC(AGG(ligne) for ligne in axe)) — opt-in
        self._dedup = dedup   # étage dédup ordonnée / nb distinct (état ensembliste) — opt-in
        self._prefixe_commun = prefixe_commun   # étage préfixe/suffixe commun d'une liste de chaînes — opt-in
        self._monnaie = monnaie   # étage DP rendu de monnaie (min pièces / possible) — opt-in
        self._cesar = cesar   # étage chiffre de César (décalage mod 26) — opt-in
        self._conjugaison = conjugaison   # étage conjugaison (FORME du langage : règles -er + irréguliers) — opt-in
        self._conjugaison2 = conjugaison2   # étage conjugaison groupe 2 (-ir en -iss-) — opt-in
        self._passe_compose = passe_compose   # étage passé composé (auxiliaire avoir + participe réglé) — opt-in
        self._adverbe = adverbe   # étage adverbe en -ment (dérivation adj -> adv) — opt-in
        self._participe_present = participe_present   # étage participe présent (-ant) — opt-in
        self._imperatif = imperatif   # étage impératif (mode, tu/nous/vous) — opt-in
        self._conditionnel = conditionnel   # étage conditionnel présent (inf + terminaisons imparfait) — opt-in
        self._subjonctif = subjonctif   # étage subjonctif présent (mode du doute/souhait) — opt-in
        self._pluriel = pluriel   # étage pluriel (FORME : accord en nombre, noms/adjectifs) — opt-in
        self._feminin = feminin   # étage féminin (FORME : accord en genre, adjectifs) — opt-in
        self._relation_lexicale = relation_lexicale   # étage relations lexicales (SENS : closure sur graphe is-a/syn) — opt-in
        self._sens_executable = sens_executable   # étage sens exécutable (SENS : verbe mot↔action exécutée) — opt-in
        self._intention = intention   # étage intention/but (SENS : moyen-fin vers une post-condition vérifiable) — opt-in
        self._desambiguisation = desambiguisation   # étage désambiguïsation (SENS : mot + geste, 2 canaux) — opt-in
        self._normalisation = normalisation   # étage normalisation (SENS : robustesse au bruit/synonymes) — opt-in
        self._ancetre_commun = ancetre_commun   # étage ancêtre commun / lien (COMPRÉHENSION : catégorie partagée) — opt-in
        self._intrus = intrus   # étage intrus / catégorie commune (COMPRÉHENSION : logique de catégorie) — opt-in
        self._analyse_phrase = analyse_phrase   # étage analyse de phrase (COMPRÉHENSION : structure/POS) — opt-in
        self._comprehension_phrase = comprehension_phrase   # étage compréhension SVO (COMPRÉHENSION : qui fait quoi) — opt-in
        self._accord_phrase = accord_phrase   # étage accord du groupe nominal (COMPRÉHENSION : pluriel propagé) — opt-in
        self._inference = inference   # étage inférence logique (LOGIQUE : déduction 3 valeurs sur prémisses) — opt-in
        self._comprehension_definition = comprehension_definition   # étage compréhension de définition (genre+différence) — opt-in
        self._distance_semantique = distance_semantique   # étage distance sémantique (COMPRÉHENSION : proximité de sens) — opt-in
        self._accord_correct = accord_correct   # étage détection d'erreur d'accord (COMPRÉHENSION : juger la norme) — opt-in
        self._antonyme = antonyme   # étage antonymes (COMPRÉHENSION : les contraires) — opt-in
        self._paraphrase = paraphrase   # étage paraphrase (COMPRÉHENSION : même sens malgré les mots) — opt-in
        self._negation = negation   # étage négation (COMPRÉHENSION : comprendre ne...pas) — opt-in
        self._quantificateur = quantificateur   # étage quantificateurs (LOGIQUE : tous/certains/aucun) — opt-in
        self._coreference = coreference   # étage coréférence (DISCOURS : résoudre il/elle) — opt-in
        self._temporel = temporel   # étage logique temporelle (ordonner avant/après) — opt-in
        self._comptage = comptage   # étage comptage (COMPRÉHENSION : combien / lesquels sur une catégorie) — opt-in
        self._chemin = chemin   # étage chemin/explication (COMPRÉHENSION : la chaîne qui relie x à y) — opt-in
        self._generation = generation   # étage génération de phrase (PRODUCTION : écrire une phrase complète) — opt-in
        self._analogie = analogie   # étage analogie/transfert (COMPRÉHENSION : motif d'un domaine adapté à un autre) — opt-in
        self._interrogation = interrogation   # étage interrogation (production : phrase -> question) — opt-in
        self._negation_phrase = negation_phrase   # étage négation (production : phrase -> négative ne…pas) — opt-in
        self._comparatif = comparatif   # étage comparatif (production+cognition : comparaison a/b via adjectif) — opt-in
        self._record = record   # étage record génératif (dict clés-fixes à complétude graduable) — opt-in
        self._anticipation = anticipation   # étage anticipation (prédire le terme suivant d'une séquence) — opt-in
        self._optimisation = optimisation   # étage décision/optimisation (max|min par critère dérivé) — opt-in
        self._ranking = ranking   # étage classement/priorisation (sorted par critère dérivé) — opt-in
        self._bits = bits   # étage binaire/bits (opérations bit-à-bit : &|^ <<>> popcount) — opt-in
        self._logique = logique   # étage logique (quantificateurs de comptage : exactement_un/majorité/parité) — opt-in
        self._ensembles = ensembles   # étage ensembliste (intersection/union/différence/sous-ensemble) — opt-in
        self._statistiques = statistiques   # étage analyse statistique (médiane/mode/moyenne/écart) — opt-in
        self._conversion = conversion   # étage conversion de base (déc↔bin↔hex) — opt-in
        self._parsing = parsing   # étage parsing structuré (chaîne -> dict/liste) — opt-in
        self._math_avance = math_avance   # étage math avancé (isqrt/lcm/comb/pow_mod) — opt-in
        self._chiffres = chiffres   # étage décomposition décimale (somme/nb/inverse des chiffres) — opt-in
        self._liste_transforms = liste_transforms   # étage transforms de liste (rotation/blocs/entrelace) — opt-in
        self._chaines_avancees = chaines_avancees   # étage chaînes avancées (anagramme/sous-chaîne/remplace) — opt-in
        self._diviseurs = diviseurs   # étage théorie des diviseurs (diviseurs/nb/facteurs premiers) — opt-in
        self._graphe = graphe   # étage graphes (voisins/degré/sommets/arête sur liste d'arêtes) — opt-in
        self._combinatoire = combinatoire   # étage combinatoire générative (permutations/sous-ensembles/produit) — opt-in
        self._iteration = iteration   # étage itération/point-fixe (répéter un pas scalaire jusqu'à condition) — opt-in
        self._acc_courant = acc_courant   # étage accumulateur-courant (Kadane : cur étend/redémarre, best extremum) — opt-in
        self._equilibre = equilibre   # étage scan-compteur-profondeur (is_balanced) — opt-in
        self._premier_unique = premier_unique   # étage fréquence-puis-premier-unique (first_unique_char) — opt-in
        self._chevauchement = chevauchement   # étage balayage d'intervalles / sweep-line (max_overlap) — opt-in
        self._dp_int = dp_int                 # étage DÉDIÉ DP-sur-entier (integer_break/perfect_squares/ugly/Catalan) — opt-in
        self._dp2d = dp2d   # étage DP 2D sur deux séquences (lcs_len, edit_distance) — opt-in
        self._geometrie = geometrie   # étage géométrie entière (manhattan, aire² triangle/polygone) — opt-in
        self._comptage_combinatoire = comptage_combinatoire   # étage comptage combinatoire (catalan/derangements/partitions/…) — opt-in
        self._pile = pile   # étage pile/monotone une-passe (eval_rpn, next_greater) — opt-in
        self._suite = suite   # étage suites/motifs (tribonacci ordre 3, is_arithmetic) — opt-in
        self._calendrier = calendrier   # étage calendrier grégorien (days_in_month) — opt-in
        self._graphe_connexite = graphe_connexite   # étage connexité de graphe (union-find : num_components, has_cycle) — opt-in
        self._tableaux = tableaux   # étage algorithmes de tableau (house_robber, rotate_left, missing_number) — opt-in
        self._numerique = numerique   # étage réductions numériques (horner, lcm_list) — opt-in
        self._checksum = checksum   # étage sommes de contrôle (luhn_valid) — opt-in
        self._comparaisons = comparaisons   # M5 dans l'étage invention (toggle A/B « mutation des comparaisons »)
        # substrat : ajoute l'invention par ÉNUMÉRATION en TOUT DERNIER étage (le plus cher, derrière la
        # mutation). Opt-in : OFF par défaut -> ne change rien. ON -> minte un token neuf (méthode/littéral)
        # quand mutation comprise a échoué ; routé comme tout succès -> composable.
        self._substrat = substrat
        # inventer : ajoute l'INVENTION en DERNIER étage (dernier recours, le plus cher/risqué).
        # Opt-in : par défaut OFF -> l'orchestrateur reste la pure machine de COMPOSITION (la carte
        # du plafond mesure ce périmètre-là). ON -> le moteur peut minter un atome quand toute la
        # composition a échoué, et (via la rétroaction de la boucle) composer ensuite sur l'inventé.
        self._inventer = inventer

    def _catalogue(self):
        """Tous les étages CONSTRUCTIBLES (nom -> générateur). Permet de composer une orchestration
        d'ordre/sous-ensemble QUELCONQUE — pas seulement l'escalade humaine. L'invention mute le registre
        confirmé (primitives ∪ ops ∪ prédicats : inclure les prédicats permet d'inventer un prédicat
        inverse via M5)."""
        return {
            "réutilisation": GenerateurReutilisateur(self._store, self._seed),
            "recombinaison": GenerateurRecombinant(self._store, self._seed, TYPES_RICHES),
            "fusion":        GenerateurFusion(self._store, self._seed),
            "composition":   GenerateurCompose(self._primitives, self._seed, self._profondeur_compo),
            "jointure":      GenerateurJointure(self._primitives, self._ops, self._seed),
            "multi-entrée":  GenerateurMultiEntree(self._ops, self._seed),
            "pli":           GenerateurPli(self._ops, self._seed),
            "branchement":   GenerateurBranche(self._predicats, seed=self._seed),
            "boucle":        GenerateurBoucle(self._ops, self._predicats, seed=self._seed),
            "recurrence":    GenerateurRecurrence(self._ops, seed=self._seed),
            "while":         GenerateurWhile(self._ops, seed=self._seed),
            "map-repli":     GenerateurMapRepli(self._primitives, seed=self._seed),
            "invariant":     GenerateurInvariant(self._primitives, seed=self._seed),
            "jointure-profonde": GenerateurJointureProfonde(self._primitives, self._ops, seed=self._seed),
            "predicat-mesures":  GenerateurPredicatMesures(seed=self._seed),
            "positionnel":       GenerateurPositionnel(self._ops, seed=self._seed),
            "mots":              GenerateurMots(seed=self._seed),
            "multipasse":        GenerateurMultiPasse(seed=self._seed),
            "adjacence":         GenerateurAdjacence(seed=self._seed),
            "imbrique":          GenerateurImbrique(self._primitives, seed=self._seed),
            "dict-accu":         GenerateurDictAccumulateur(seed=self._seed),
            "group-by":          GenerateurGroupBy(seed=self._seed),
            "serie":             GenerateurSerie(seed=self._seed),
            "generer-tester":    GenerateurGenererTester(self._predicats, seed=self._seed),
            "comprehension-generale": GenerateurComprehensionGenerale(self._primitives, seed=self._seed,
                                                                      composite_dabord=True),  # étage fallback -> T3 d'abord (réel)
            "fenetre":       GenerateurFenetre(seed=self._seed),
            "matrice":       GenerateurMatrice2D(seed=self._seed),
            "repetition":    GenerateurRepetition(seed=self._seed),
            "index-ordonne": GenerateurIndexOrdonne(seed=self._seed),
            "sous-suite":    GenerateurSousSuite(seed=self._seed),
            "paires":        GenerateurPaires(seed=self._seed),
            "run-length":    GenerateurRunLength(seed=self._seed),
            "dict-transform": GenerateurDictTransform(seed=self._seed),
            "record":        GenerateurRecord(seed=self._seed),
            "anticipation":  GenerateurAnticipation(seed=self._seed),
            "optimisation":  GenerateurOptimisation(seed=self._seed),
            "ranking":       GenerateurRanking(seed=self._seed),
            "bits":          GenerateurBits(seed=self._seed),
            "logique":       GenerateurLogique(seed=self._seed),
            "ensembles":     GenerateurEnsembles(seed=self._seed),
            "statistiques":  GenerateurStatistiques(seed=self._seed),
            "conversion":    GenerateurConversion(seed=self._seed),
            "parsing":       GenerateurParsing(seed=self._seed),
            "math-avance":   GenerateurMathAvance(seed=self._seed),
            "chiffres":      GenerateurChiffres(seed=self._seed),
            "liste-transforms": GenerateurListeTransforms(seed=self._seed),
            "chaines-avancees": GenerateurChainesAvancees(seed=self._seed),
            "diviseurs":     GenerateurDiviseurs(seed=self._seed),
            "graphe":        GenerateurGraphe(seed=self._seed),
            "combinatoire":  GenerateurCombinatoire(seed=self._seed),
            "iteration":     GenerateurIteration(seed=self._seed),
            "accumulateur-courant": GenerateurAccumulateurCourant(seed=self._seed),
            "equilibre":     GenerateurEquilibre(seed=self._seed),
            "premier-unique": GenerateurPremierUnique(seed=self._seed),
            "chevauchement": GenerateurChevauchement(seed=self._seed),
            "dp-int": GenerateurDPInt(seed=self._seed),
            "dp2d":          GenerateurDP2D(seed=self._seed),
            "geometrie":     GenerateurGeometrie(seed=self._seed),
            "comptage-combinatoire": GenerateurComptageCombinatoire(seed=self._seed),
            "pile":          GenerateurPile(seed=self._seed),
            "suite":         GenerateurSuite(seed=self._seed),
            "calendrier":    GenerateurCalendrier(seed=self._seed),
            "graphe-connexite": GenerateurGrapheConnexite(seed=self._seed),
            "tableaux":      GenerateurTableaux(seed=self._seed),
            "numerique":     GenerateurNumerique(seed=self._seed),
            "checksum":      GenerateurChecksum(seed=self._seed),
            "profond":        GenerateurProfond(seed=self._seed),
            "filtre-seuil":   GenerateurFiltreSeuil(seed=self._seed),
            "matrice-reduce": GenerateurMatriceReduce(seed=self._seed),
            "dedup":          GenerateurDedup(seed=self._seed),
            "prefixe-commun": GenerateurPrefixeCommun(seed=self._seed),
            "monnaie":        GenerateurMonnaie(seed=self._seed),
            "cesar":          GenerateurCesar(seed=self._seed),
            "conjugaison":    GenerateurConjugaison(seed=self._seed),
            "conjugaison2":   GenerateurConjugaison2(seed=self._seed),
            "passe_compose":  GenerateurPasseCompose(seed=self._seed),
            "adverbe":        GenerateurAdverbe(seed=self._seed),
            "participe_present": GenerateurParticipePresent(seed=self._seed),
            "imperatif":      GenerateurImperatif(seed=self._seed),
            "conditionnel":   GenerateurConditionnel(seed=self._seed),
            "subjonctif":     GenerateurSubjonctif(seed=self._seed),
            "pluriel":        GenerateurPluriel(seed=self._seed),
            "feminin":        GenerateurFeminin(seed=self._seed),
            "relation-lexicale": GenerateurRelationLexicale(seed=self._seed),
            "sens-executable":   GenerateurSensExecutable(seed=self._seed),
            "intention":        GenerateurIntention(seed=self._seed),
            "desambiguisation": GenerateurDesambiguisation(seed=self._seed),
            "normalisation":    GenerateurNormalisation(seed=self._seed),
            "ancetre-commun":   GenerateurAncetreCommun(seed=self._seed),
            "intrus":           GenerateurIntrus(seed=self._seed),
            "analyse-phrase":   GenerateurAnalysePhrase(seed=self._seed),
            "comprehension-phrase": GenerateurComprehensionPhrase(seed=self._seed),
            "accord-phrase":    GenerateurAccordPhrase(seed=self._seed),
            "inference":        GenerateurInference(seed=self._seed),
            "comprehension-definition": GenerateurComprehensionDefinition(seed=self._seed),
            "distance-semantique": GenerateurDistanceSemantique(seed=self._seed),
            "accord-correct":   GenerateurAccordCorrect(seed=self._seed),
            "antonyme":         GenerateurAntonyme(seed=self._seed),
            "paraphrase":       GenerateurParaphrase(seed=self._seed),
            "negation":         GenerateurNegation(seed=self._seed),
            "quantificateur":   GenerateurQuantificateur(seed=self._seed),
            "coreference":      GenerateurCoreference(seed=self._seed),
            "temporel":         GenerateurTemporel(seed=self._seed),
            "comptage":         GenerateurComptage(seed=self._seed),
            "chemin":           GenerateurChemin(seed=self._seed),
            "generation":       GenerateurGeneration(seed=self._seed),
            "analogie":         GenerateurAnalogie(seed=self._seed),
            "interrogation":    GenerateurInterrogation(seed=self._seed),
            "negation_phrase":  GenerateurNegationPhrase(seed=self._seed),
            "comparatif":       GenerateurComparatif(seed=self._seed),
            "invention":     GenerateurInvention(self._primitives + self._ops + self._predicats,
                                                 self._seed, comparaisons=self._comparaisons),
            "substrat":      GenerateurSubstrat(seed=self._seed),
        }

    def _tiers(self):
        cat = self._catalogue()
        if self._ordre_etages is not None:
            # ORCHESTRATION LIBRE : exactement les étages demandés, dans l'ordre demandé (la RÉALITÉ, pas
            # le prior humain, choisit). Étage inconnu ignoré ; un étage sans matière rend [] (inoffensif).
            return [(n, cat[n]) for n in self._ordre_etages if n in cat]
        # Défaut = escalade canonique humaine, en respectant les flags de convenance (historique, inchangé).
        noms = ["réutilisation", "recombinaison", "fusion", "composition", "jointure", "multi-entrée", "pli"]
        if self._predicats:
            noms += ["branchement", "boucle"]
        if self._recurrence:
            noms += ["recurrence"]
        if self._boucle_while:
            noms += ["while"]
        if self._map_repli:
            noms += ["map-repli"]
        if self._invariant:
            noms += ["invariant"]
        if self._jointure_profonde:
            noms += ["jointure-profonde"]
        if self._predicat_mesures:
            noms += ["predicat-mesures"]
        if self._positionnel:
            noms += ["positionnel"]
        if self._mots:
            noms += ["mots"]
        if self._multipasse:
            noms += ["multipasse"]
        if self._adjacence:
            noms += ["adjacence"]
        if self._imbrique:
            noms += ["imbrique"]
        if self._dict_accu:
            noms += ["dict-accu"]
        if self._group_by:
            noms += ["group-by"]
        if self._serie:
            noms += ["serie"]
        if self._generer_tester:
            noms += ["generer-tester"]
        if self._comprehension_generale:
            noms += ["comprehension-generale"]
        if self._fenetre:
            noms += ["fenetre"]
        if self._matrice:
            noms += ["matrice"]
        if self._repetition:
            noms += ["repetition"]
        if self._index_ordonne:
            noms += ["index-ordonne"]
        if self._sous_suite:
            noms += ["sous-suite"]
        if self._paires:
            noms += ["paires"]
        if self._run_length:
            noms += ["run-length"]
        if self._dict_transform:
            noms += ["dict-transform"]
        if self._record:
            noms += ["record"]
        if self._anticipation:
            noms += ["anticipation"]
        if self._optimisation:
            noms += ["optimisation"]
        if self._ranking:
            noms += ["ranking"]
        if self._bits:
            noms += ["bits"]
        if self._logique:
            noms += ["logique"]
        if self._ensembles:
            noms += ["ensembles"]
        if self._statistiques:
            noms += ["statistiques"]
        if self._conversion:
            noms += ["conversion"]
        if self._parsing:
            noms += ["parsing"]
        if self._math_avance:
            noms += ["math-avance"]
        if self._chiffres:
            noms += ["chiffres"]
        if self._liste_transforms:
            noms += ["liste-transforms"]
        if self._chaines_avancees:
            noms += ["chaines-avancees"]
        if self._diviseurs:
            noms += ["diviseurs"]
        if self._graphe:
            noms += ["graphe"]
        if self._combinatoire:
            noms += ["combinatoire"]
        if self._iteration:
            noms += ["iteration"]
        if self._acc_courant:
            noms += ["accumulateur-courant"]
        if self._equilibre:
            noms += ["equilibre"]
        if self._premier_unique:
            noms += ["premier-unique"]
        if self._chevauchement:
            noms += ["chevauchement"]
        if self._dp_int:
            noms += ["dp-int"]
        if self._dp2d:
            noms += ["dp2d"]
        if self._geometrie:
            noms += ["geometrie"]
        if self._comptage_combinatoire:
            noms += ["comptage-combinatoire"]
        if self._pile:
            noms += ["pile"]
        if self._suite:
            noms += ["suite"]
        if self._calendrier:
            noms += ["calendrier"]
        if self._graphe_connexite:
            noms += ["graphe-connexite"]
        if self._tableaux:
            noms += ["tableaux"]
        if self._numerique:
            noms += ["numerique"]
        if self._checksum:
            noms += ["checksum"]
        if self._profond:
            noms += ["profond"]
        if self._filtre_seuil:
            noms += ["filtre-seuil"]
        if self._matrice_reduce:
            noms += ["matrice-reduce"]
        if self._dedup:
            noms += ["dedup"]
        if self._prefixe_commun:
            noms += ["prefixe-commun"]
        if self._monnaie:
            noms += ["monnaie"]
        if self._cesar:
            noms += ["cesar"]
        if self._conjugaison:
            noms += ["conjugaison"]
        if self._conjugaison2:
            noms += ["conjugaison2"]
        if self._passe_compose:
            noms += ["passe_compose"]
        if self._adverbe:
            noms += ["adverbe"]
        if self._participe_present:
            noms += ["participe_present"]
        if self._imperatif:
            noms += ["imperatif"]
        if self._conditionnel:
            noms += ["conditionnel"]
        if self._subjonctif:
            noms += ["subjonctif"]
        if self._pluriel:
            noms += ["pluriel"]
        if self._feminin:
            noms += ["feminin"]
        if self._relation_lexicale:
            noms += ["relation-lexicale"]
        if self._sens_executable:
            noms += ["sens-executable"]
        if self._intention:
            noms += ["intention"]
        if self._desambiguisation:
            noms += ["desambiguisation"]
        if self._normalisation:
            noms += ["normalisation"]
        if self._ancetre_commun:
            noms += ["ancetre-commun"]
        if self._intrus:
            noms += ["intrus"]
        if self._analyse_phrase:
            noms += ["analyse-phrase"]
        if self._comprehension_phrase:
            noms += ["comprehension-phrase"]
        if self._accord_phrase:
            noms += ["accord-phrase"]
        if self._inference:
            noms += ["inference"]
        if self._comprehension_definition:
            noms += ["comprehension-definition"]
        if self._distance_semantique:
            noms += ["distance-semantique"]
        if self._accord_correct:
            noms += ["accord-correct"]
        if self._antonyme:
            noms += ["antonyme"]
        if self._paraphrase:
            noms += ["paraphrase"]
        if self._negation:
            noms += ["negation"]
        if self._quantificateur:
            noms += ["quantificateur"]
        if self._coreference:
            noms += ["coreference"]
        if self._temporel:
            noms += ["temporel"]
        if self._comptage:
            noms += ["comptage"]
        if self._chemin:
            noms += ["chemin"]
        if self._generation:
            noms += ["generation"]
        if self._analogie:
            noms += ["analogie"]
        if self._interrogation:
            noms += ["interrogation"]
        if self._negation_phrase:
            noms += ["negation_phrase"]
        if self._comparatif:
            noms += ["comparatif"]
        if self._inventer:
            noms += ["invention"]
        if self._substrat:
            noms += ["substrat"]
        return [(n, cat[n]) for n in noms]

    def etages(self, prompt: str, k: int = 200):
        """Candidats PAR ÉTAGE, dans l'ordre d'escalade ; chaque étage ordonné par la
        direction si un prédicteur est fourni. (Sert à voir QUEL étage résout.)

        NB ORDRE : l'ordre canonique est CONSERVÉ (cf. `cherche_ordre.py`, 2026-06-17). Un cost-ascending
        donne −88 % d'appels sur la batterie durcie MAIS en défaut global il (1) provoque des MASQUAGES
        (l'uniqueté du solveur est RELATIVE à l'ordre, pas absolue : un étage cheap attrape une tâche s'il passe
        avant son solveur), (2) casse les validations sensibles au coût. « sûr avant rapide » -> non adopté en
        défaut. La voie SÛRE pour capter ce gain = la ZONE-ROUTING (gate + fallback préservant la couverture)."""
        res = []
        for nom, gen in self._tiers():
            cands = gen.propose(prompt, k)
            if self._predicteur is not None:
                cands = sorted(cands, key=self._predicteur.rang)   # direction intra-étage
            res.append((nom, cands))
        return res

    def propose(self, prompt: str, n: int) -> list[str]:
        flat = []
        for _, cands in self.etages(prompt, n):
            flat.extend(cands)
        flat = list(dict.fromkeys(flat))   # dé-dup en gardant le 1er (donc l'étage le moins cher)
        return flat[:n] if n <= len(flat) else flat

    def apprendre(self, delta: float = 0.0) -> int:
        return len(list(self._store)) + len(self._primitives) + len(self._ops)

    # --- Rétroaction : un succès confirmé grandit le registre appelable ---------
    # (cf. README §orchestrateur — « les étages hauts grandissent seuls »). Le store
    # (fragments) est nourri par la boucle ; ici on nourrit les briques APPELABLES.
    # Décision (fork rétroaction) : nom dérivé du point d'entrée, profondeur 2, PAS de
    # mangling -> sur collision de nom, on GARDE l'ancien (renvoie False), on n'écrase
    # pas. La direction de l'escalade gère le reste : un composé confirmé sert ensuite
    # de brique à l'étage du dessus (tours de skills).

    def _verse(self, registre, nom: str, source: str) -> bool:
        if any(n == nom for n, _ in registre):
            return False                      # collision : on garde l'ancien (pas de mangling)
        registre.append((nom, source))
        return True

    def verse_primitive(self, nom: str, source: str) -> bool:
        """Un succès confirmé devient une primitive nidifiable (étage composition)."""
        return self._verse(self._primitives, nom, source)

    def verse_op(self, nom: str, source: str) -> bool:
        """Une opération binaire confirmée devient repliable (étage pli)."""
        return self._verse(self._ops, nom, source)

    def verse_predicat(self, nom: str, source: str) -> bool:
        """Un test booléen confirmé (sur scalaire) alimente branchement / boucle bornée."""
        return self._verse(self._predicats, nom, source)


def banque_demo(tache) -> dict[str, list[str]]:
    """
    Construit une banque de démo pour UNE tâche : un mélange réaliste de candidats
    qui couvre tous les statuts du juge. Permet à B4 (la boucle) de tourner et de
    montrer le tri "garder seulement ce qui passe".

    Renvoie {prompt: [candidats]} — clé = le prompt, comme un vrai générateur.
    """
    p = tache.prompt
    candidats = [
        # --- corrects (doivent PASSER, et être distincts au dé-dup) ---
        # 1) la solution canonique (double boucle)
        tache.solution_ref,
        # 2) une variante correcte compacte (compréhension)
        p + "\n    return any(abs(a - b) < threshold "
            "for i, a in enumerate(numbers) "
            "for j, b in enumerate(numbers) if i != j)\n",
        # 3) une variante correcte triée (autre algo, toujours juste)
        p + "\n    s = sorted(numbers)\n"
            "    return any(s[k+1] - s[k] < threshold for k in range(len(s) - 1))\n",

        # --- faux (doit ÉCHOUER : test raté) ---
        p + "\n    return False\n",

        # --- lent mais correct (PASSE, mais durée visiblement plus haute) ---
        # NB : check() appelle le candidat 7 fois -> le sleep est payé 7x.
        # 0.1s * 7 ≈ 0.7s : sous le budget (timeout démo = 2s), donc accepté.
        # (Un sleep trop gros le ferait basculer en TIMEOUT, à juste titre :
        #  le juge fait respecter un budget de temps, pas que la justesse.)
        p + "\n    import time\n    time.sleep(0.1)\n"
            "    return any(abs(a - b) < threshold "
            "for i, a in enumerate(numbers) "
            "for j, b in enumerate(numbers) if i != j)\n",

        # --- boucle infinie (doit TIMEOUT) ---
        p + "\n    while True:\n        pass\n",

        # --- code invalide (doit ERROR) ---
        p + "\n    return ???\n",
    ]
    return {p: candidats}
