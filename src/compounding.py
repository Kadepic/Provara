"""
LA MONTÉE AUTONOME (compounding) — la boucle vivante.

C'est la pièce qui rend la vision VISIBLE : on branche l'orchestrateur (toute la
trousse, en escalade dirigée) sur un curriculum gradué, AVEC RÉTROACTION — chaque
succès confirmé nourrit le passé qui nourrit le présent :

    le CURATEUR sert un palier (du trivial au stateful)
      -> pour CHAQUE tâche, l'ORCHESTRATEUR escalade SEUL (réutilisation -> ... -> pli),
         s'arrête au 1er candidat qui passe LE VISIBLE *et* généralise (held-out)
        -> RÉTROACTION : le succès confirmé rejoint le STORE (fragments) ET le registre
           de PRIMITIVES appelables (briques) -> les étages hauts grandissent seuls
          -> on MESURE, le curateur gradue, on remonte d'un cran.

Décisions de design tranchées avec Yohan (cf. REPRISE/README) :
  - Curriculum FIXE (gradué de l'extérieur, garanti honnête par l'auto-validation du
    curateur) ; l'orchestrateur, lui, escalade LIBREMENT sur chaque tâche.
  - Rétroaction = versement AUTO, profondeur 2, SANS mangling (nom = point d'entrée ;
    sur collision on garde l'ancien).
  - Seul le JUGE promeut un savoir ; on confirme sur le HELD-OUT avant de verser
    (anti hard-coding) — la réalité tranche, au niveau SYSTÈME.

Ce module n'embarque AUCUN curriculum : il est agnostique. La matière (seeds +
tâches graduées) vit dans la validation `valide_compounding.py`, comme il se doit
(la matière vient de l'extérieur).
"""

from __future__ import annotations

import ast
import dataclasses

from juge import Limites, juge
from routeur import resoudre_route


# --- L'AUTO-ROUTAGE DU VERSEMENT --------------------------------------------
# Un succès confirmé doit rejoindre LE BON registre — primitive (composition),
# op (pli/jointure/multi-entrée/boucle) ou prédicat (branchement/boucle) — sinon
# l'étage qui en a besoin ne le voit jamais (mesuré : `valide_cloture` versait
# l'op `sub` À LA MAIN). La règle a été TRANCHÉE PAR LA DONNÉE (`recense.py`,
# 20/20 atomes) : arité ≥ 2 -> op ; unaire rendant un booléen SUR SCALAIRE ->
# prédicat ; tout autre unaire -> primitive. (Le seul piège mesuré : un booléen
# unaire sur CONTENEUR — `tous_pairs` — est un skill agrégat, PAS un prédicat de
# branche ; d'où la finesse « sur scalaire ».)
#
# Fork tranché avec Yohan : le routeur VIT dans `montee` (un seul appelant vivant
# du versement -> pas de module dédié). Et l'exécution de sonde passe par le JUGE
# (sous-process isolé) : on ne fait qu'une question oui/non au réel, jamais d'`exec`
# en-process (principe 1 : le juge seul exécute, isolé).

def _def_entree(code: str, nom: str):
    """La FunctionDef de la fonction d'entrée `nom` (pas les helpers embarqués en
    préambule — un candidat composé EMBARQUE les sources de ses briques)."""
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.FunctionDef) and node.name == nom:
            return node
    return None


def _arite_entree(fn_node) -> int:
    """Arité = 1 + plus grand indice constant utilisé sur `args` DANS LE CORPS de la
    fonction d'entrée seule. `produit = mul(premier(args[0]), dernier(args[0]))` n'utilise
    que `args[0]` -> arité 1 (unaire), même si le helper `mul` embarqué lit `args[1]`."""
    maxi = -1
    for node in ast.walk(fn_node):
        if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
                and node.value.id == "args" and isinstance(node.slice, ast.Constant)
                and isinstance(node.slice.value, int) and not isinstance(node.slice.value, bool)):
            maxi = max(maxi, node.slice.value)
    return maxi + 1 if maxi >= 0 else 1


def route(code: str, nom: str, limites: Limites | None = None) -> str:
    """Range un succès confirmé : 'op' | 'predicat' | 'primitive'.

    `nom` = la fonction d'entrée (point d'entrée de la tâche) : on raisonne sur ELLE,
    pas sur les briques qu'un candidat composé embarque. Règle décidable sans choix
    arbitraire sur tout le substrat connu (cf. recense.py). La seule sonde dynamique —
    « rend-il un booléen sur un scalaire ? » — passe par le juge (sous-process isolé),
    jamais par un exec en-process (principe 1)."""
    fn = _def_entree(code, nom)
    if fn is not None and _arite_entree(fn) >= 2:
        return "op"
    sonde = f"assert isinstance({nom}(3), bool)\n"      # booléen sur scalaire -> prédicat
    if juge(code, sonde, limites).passe:
        return "predicat"
    return "primitive"


@dataclasses.dataclass
class PasMontee:
    """Le compte-rendu d'UNE tâche tentée pendant la montée."""
    tour: int                 # quel palier de curriculum (0-indexé)
    niveau: int               # difficulté servie
    tache_id: str
    point_entree: str
    etage: str | None         # étage de la trousse qui a résolu (None = hors de portée)
    appels_juge: int          # jugements du visible jusqu'au 1er succès confirmé (coût d'escalade)
    confirme: bool            # passe le visible ET le held-out ?
    nouvelle_primitive: bool  # ce succès a-t-il AJOUTÉ une brique appelable (vs collision/connu) ?

    def resume(self) -> str:
        etat = self.etage if self.confirme else "HORS-PORTÉE"
        plus = "  +brique" if self.nouvelle_primitive else ""   # routée op/prédicat/primitive selon signature
        return (f"  tour {self.tour} | niv {self.niveau} | {self.point_entree:<22} "
                f"-> {etat:<14} | {self.appels_juge:>3} appels{plus}")


def resoudre(orchestre, tache, limites: Limites | None = None, k: int = 400,
             budget: int | None = None):
    """
    L'orchestrateur escalade SEUL sur une tâche et s'arrête au 1er candidat qui
    passe le visible ET généralise (held-out). Renvoie (etage, appels, code, verdict).

    Garde-fou (principe 1) : on n'accepte un succès que s'il GÉNÉRALISE. Un candidat
    qui passe le visible mais rate le held-out est ignoré (hard-coding) — il ne sera
    ni gardé ni versé. Seul le juge promeut.

    `budget` (opt-in, défaut None = comportement inchangé) : BUDGET DE PUISSANCE (vision Yohan « dépenser à hauteur
    du besoin » ; 2e cran par-dessus `niveau_richesse`). Borne DURE le nombre d'appels juge : si l'escalade atteint
    `budget` appels sans succès, on s'arrête et on rend HORS (None) PROPREMENT — jamais un faux (on ne rend que ce
    qui a passé le juge). Cape le gaspillage sur tâches dures/insolubles (cf. `observe_sans_solution` : ~1888
    candidats brûlés). La couverture sous budget LARGE reste identique à l'escalade illimitée.
    """
    appels = 0
    for nom_etage, cands in orchestre.etages(tache.prompt, k):
        for code in cands:
            if budget is not None and appels >= budget:
                return None, appels, None, None   # budget épuisé -> HORS propre, jamais de faux
            appels += 1
            v = juge(code, tache.tests, limites)
            if not v.passe:
                continue
            if tache.tests_held_out and not juge(code, tache.tests_held_out, limites).passe:
                continue   # passe le visible, rate le held-out -> hard-coding, on n'en veut pas
            return nom_etage, appels, code, v
    return None, appels, None, None


def _porte_niveau(point_entree: str, paliers, niveau: int, idx: int) -> str:
    """Assemble la porte CUMULÉE T1..T_niveau en UN programme de test. `paliers` = [(visibles, held), ...]
    du plus basique au plus adverse ; chaque élément = liste d'asserts. idx 0=visibles, 1=held-out."""
    lignes: list[str] = []
    for t in range(min(niveau, len(paliers))):
        lignes += paliers[t][idx]
    if not lignes:
        return ""
    return "def check(c):\n" + "\n".join(lignes) + f"\ncheck({point_entree})\n"


def resoudre_niveau(orchestre, prompt: str, point_entree: str, paliers, niveau: int,
                    limites: Limites | None = None, k: int = 400):
    """
    RÉSOLUTION À NIVEAU DE RICHESSE CHOISI — le « cran » que l'appelant règle (vision Yohan : pouvoir
    SÉLECTIONNER ce qu'on veut — une bonne réponse de base OU une réponse complète). 1 = correct sur le
    régime de base ; plus haut = + edge + adverse + général.

    `paliers` = [(visibles, held_out), ...] du plus basique au plus adverse (listes d'asserts). La porte du
    niveau N = cumul des visibles T1..TN ET des held-out T1..TN. Le held-out PAR NIVEAU est le garde-fou de
    SÛRETÉ : un candidat qui game les visibles faibles (coïncidence, ex. gcd≈a%b qui matche 2 points par hasard)
    est REJETÉ s'il rate le held-out -> on ne rend JAMAIS de faux, au pire la réponse complète (plus chère).

    Renvoie (etage, appels, code). Plus N est bas, plus tôt/moins cher on s'engage QUAND un candidat
    correct-sur-le-domaine-N existe en amont de l'escalade ; sinon on monte jusqu'au candidat complet.
    """
    vis = _porte_niveau(point_entree, paliers, niveau, 0)
    held = _porte_niveau(point_entree, paliers, niveau, 1)
    appels = 0
    for nom_etage, cands in orchestre.etages(prompt, k):
        for code in cands:
            appels += 1
            if not juge(code, vis, limites).passe:
                continue
            if held and not juge(code, held, limites).passe:
                continue   # game les visibles mais rate le held-out de ce niveau -> coïncidence, refusée
            return nom_etage, appels, code
    return None, appels, None


def _verse_route(orchestre, nom: str, code: str, routage: bool,
                 limites: Limites | None) -> bool:
    """Verse un succès confirmé dans le BON registre.

    `routage=True` : on route par signature (arité/type) -> op / prédicat / primitive,
    le moteur range lui-même ses inventions. `routage=False` : ancien comportement
    naïf (tout en primitive) -> le CONTRÔLE de l'A/B (une op inventée n'atteint jamais
    multi-entrée, qui ne lit que les ops)."""
    if not routage:
        return orchestre.verse_primitive(nom, code)
    cible = route(code, nom, limites)
    if cible == "op":
        return orchestre.verse_op(nom, code)
    if cible == "predicat":
        return orchestre.verse_predicat(nom, code)
    return orchestre.verse_primitive(nom, code)


def montee(orchestre, curateur, store, limites: Limites | None = None,
           retroaction: bool = True, routage: bool = True, k: int = 400,
           verbose: bool = False, routeur=None) -> list[PasMontee]:
    """
    Lance la montée le long du curriculum du curateur et rend le journal (un
    PasMontee par tâche tentée par palier).

    `retroaction` est le LEVIER de l'expérience : True = le passé nourrit le présent
    (les succès deviennent des briques) ; False = le registre reste figé au seed
    (le CONTRÔLE). L'écart entre les deux EST la preuve du compounding.

    `routage` est le LEVIER de l'auto-routage : True = chaque succès rejoint le bon
    registre (op/prédicat/primitive) par sa signature ; False = tout en primitive
    (l'ancien comportement, CONTRÔLE de l'A/B du routage).

    `routeur` (opt-in, défaut None = comportement inchangé) : un RouteurZone (zone-routing
    « activation parcimonieuse »). Fourni -> on résout via `resoudre_route` (essaie les zones
    prédites d'abord, fallback escalade complète -> couverture identique) ET le routeur APPREND
    en ligne `clé -> étage` à chaque succès confirmé : il se réordonnance au fil de la montée
    (le gain croît avec la chaleur du store), sans jamais perdre la couverture.
    """
    journal: list[PasMontee] = []
    tour = 0

    while True:
        niveau = curateur.niveau
        lot = curateur.lot()
        confirmes = []

        for tache in lot:
            if routeur is not None:
                etage, appels, code, verdict = resoudre_route(orchestre, tache, routeur, limites, k)
            else:
                etage, appels, code, verdict = resoudre(orchestre, tache, limites, k)
            confirme = code is not None
            nouvelle = False
            if confirme:
                store.ajoute(tache, code, verdict)              # fragment (toujours)
                if routeur is not None:
                    routeur.apprendre(tache, etage)             # apprentissage EN LIGNE de la zone (clé -> étage)
                if retroaction:
                    nouvelle = _verse_route(orchestre, tache.point_entree, code, routage, limites)
            pas = PasMontee(tour, niveau, tache.id, tache.point_entree, etage,
                            appels, confirme, nouvelle)
            journal.append(pas)
            if verbose:
                print(pas.resume())
            confirmes.append(1.0 if confirme else 0.0)

        generalisation = sum(confirmes) / len(confirmes) if confirmes else 0.0
        monte = curateur.progresse(generalisation)
        tour += 1

        # Au sommet du curriculum et plus rien à débloquer -> fin (le dernier palier
        # vient d'être servi). Garde-fou anti-boucle infinie : borne dure sur les tours.
        if (curateur.fini() and not monte) or tour > len(curateur.valides) + 5:
            break

    return journal


# --- Lecture des courbes (la boîte de verre) --------------------------------

def franchies(journal: list[PasMontee]) -> set[str]:
    """L'ensemble des point_entree résolus (confirmés) sur toute la montée."""
    return {p.point_entree for p in journal if p.confirme}


def etages_atteints(journal: list[PasMontee]) -> dict[str, int]:
    """Combien de tâches chaque étage de la trousse a résolu (la hauteur des tours)."""
    compte: dict[str, int] = {}
    for p in journal:
        if p.confirme and p.etage:
            compte[p.etage] = compte.get(p.etage, 0) + 1
    return compte
