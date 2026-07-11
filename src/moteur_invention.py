"""
MOTEUR DE DÉCOUVERTE D'INVENTIONS — la GRAINE de l'OBJECTIF FINAL de Yohan
(cf. [[project-ia-objectif-final-inventions]]) : « par rapport à la réalité et à tout ce qui existe,
déterminer s'il ne manque pas des inventions, et fournir les éléments pour les construire ».

Anti-LLM, « sûr avant rapide » : on N'AFFIRME rien qu'un juge ne confirme. Substrat VÉRIFIABLE
aujourd'hui = les CAPACITÉS (fonctions) jugées par l'EXÉCUTEUR. Le même mécanisme accueillera demain
des principes physiques (cat 2) dès que leur juge-base-de-faits existera — volontairement extensible.

Étant donné un REGISTRE de CE QUI EXISTE (capacités connues exécutables) et une FONCTION-CIBLE (définie
par exemples + held-out adverse), le moteur tranche en CINQ statuts, tous jugés par la réalité :
  • EXISTE_DEJA       — une capacité connue reproduit déjà la cible (pas un manque).
  • INVENTION         — réalisable par une RECOMBINAISON de briques connues, NOUVELLE (comportement
                        distinct de tout l'existant), UNIQUE sous le spec, vérifiée. -> on fournit LES ÉLÉMENTS.
  • AMBIGU            — réalisable MAIS le spec est sous-déterminé (≥2 fonctions distinctes le satisfont) :
                        on refuse de committer une « invention » douteuse et on rend une sonde DISCRIMINANTE.
  • BRIQUE_MANQUANTE  — cohérente mais AUCUNE recombinaison connue ne la réalise = FRONTIÈRE (atome neuf requis).
  • INCOHERENT        — exemples contradictoires : rien à inventer. HORS.

Soundness : INVENTION exige (a) une réalisation VÉRIFIÉE (juge sur held-out), (b) UNICITÉ comportementale
sous le spec (pas de coïncidence concurrente — sinon AMBIGU), (c) NOUVEAUTÉ vs l'existant. Une cible non
tranchée en INVENTION ne produit JAMAIS un faux : EXISTE_DEJA / AMBIGU / BRIQUE_MANQUANTE / INCOHERENT.
"""
from __future__ import annotations

import dataclasses

from auto_apprend import MoteurAutonome
from auto_invention_ouverte import LIM, _fn
from juge import juge

EXISTE_DEJA = "existe_deja"
INVENTION = "invention"
AMBIGU = "ambigu"
BRIQUE_MANQUANTE = "brique_manquante"
INCOHERENT = "incoherent"

# REGISTRE de « ce qui existe » : capacités connues, chacune une expression exécutable sur x (mono-arg).
# Inventaire de référence — la nouveauté se mesure CONTRE lui.
EXISTANT: dict[str, str] = {
    # — agrégats / accès (cœur historique ; « somme » reste en tête pour le triage EXISTE_DEJA) —
    "somme": "sum(x)",
    "maximum": "max(x)",
    "minimum": "min(x)",
    "longueur": "len(x)",
    "tri_croissant": "sorted(x)",
    "renverse": "x[::-1]",
    "premier": "x[0]",
    "dernier": "x[-1]",
    "double_chaque": "[_e * 2 for _e in x]",
    # — listes/nombres : inventaire élargi (effets réels, builtins seuls, distincts des cibles-test) —
    "tri_decroissant": "sorted(x, reverse=True)",
    "valeurs_uniques": "sorted(set(x))",
    "nb_distinct": "len(set(x))",
    "compte_positifs": "len([_e for _e in x if _e > 0])",
    "somme_absolue": "sum(abs(_e) for _e in x)",
    # NB : pas de « moyenne entière » (sum//len) — aimant à coïncidences (= médiane/2e élément sur specs
    # courts), il masquerait de vraies frontières. Cf. [[feedback-resolution-coincidence-froid]].
    "minimum_absolu": "min(abs(_e) for _e in x)",
    "incremente_chaque": "[_e + 1 for _e in x]",
    "tout_positif": "all(_e > 0 for _e in x)",
    "existe_pair": "any(_e % 2 == 0 for _e in x)",
    # — CROSS-DOMAINE (chaînes / fréquences) : « ce qui existe » au-delà des listes d'entiers —
    "majuscule": "x.upper()",
    "minuscule": "x.lower()",
    "mots": "x.split()",
    "occurrences": "{_e: x.count(_e) for _e in set(x)}",
    # — élargissement 2026-06-22 nuit (effets RÉELS distincts, collision-checkés : aucun ne reproduit une
    #   cible-test amplitude/somme_carres/deux/mediane ; `somme_pairs` ÉCARTÉ car = `deux` par coïncidence) —
    "produit": "__import__('math').prod(x)",
    "cumul": "list(__import__('itertools').accumulate(x))",
    "differences": "[x[_i + 1] - x[_i] for _i in range(len(x) - 1)]",
    "maximum_absolu": "max(abs(_e) for _e in x)",
    "compte_negatifs": "len([_e for _e in x if _e < 0])",
    # — MATRICES (liste de listes) — élargissement 2026-06-23 (CAP « plusieurs domaines »). Chaque expr
    #   ERREUR proprement sur une liste d'entiers (zip(*int)/int[i] -> TypeError attrapé par _reproduit) :
    #   donc elles ne matchent QUE de vraies matrices, jamais une cible 1-D par coïncidence.
    "matrice_transposee": "[list(_col) for _col in zip(*x)]",
    "matrice_somme_lignes": "[sum(_r) for _r in x]",
    "matrice_somme_colonnes": "[sum(_col) for _col in zip(*x)]",
    "matrice_diagonale": "[x[_i][_i] for _i in range(len(x))]",
    "matrice_aplatie": "[_v for _r in x for _v in _r]",
    # — DICT — capacités de base d'un mapping (erreur/inadéquates sur liste/str -> ne matchent que des dicts).
    "dict_valeurs": "list(x.values())",
    "dict_cles": "list(x.keys())",
    "dict_paires_triees": "sorted(x.items())",
}

_MOTEUR = None
_BASE_LEN = 0


def _moteur() -> MoteurAutonome:
    """Moteur autonome CACHÉ (l'éveil compositionnel est coûteux : une seule fois). On mémorise la taille
    de base pour pouvoir retirer, après chaque cible, les atomes contextuels ajoutés (pas de pollution)."""
    global _MOTEUR, _BASE_LEN
    if _MOTEUR is None:
        _MOTEUR = MoteurAutonome()
        _MOTEUR.explore_combine(budget=2500)
        _BASE_LEN = len(_MOTEUR.atomes)
    return _MOTEUR


def _MM():
    """Import PARESSEUX du module des propriétés métamorphiques (opt-in : ne coûte rien au flux par défaut)."""
    import metamorphique
    return metamorphique


@dataclasses.dataclass(frozen=True)
class Verdict:
    statut: str
    cible: str
    par: str | None = None          # élément qui réalise la cible (INVENTION / EXISTE_DEJA)
    proche_de: str | None = None    # capacité existante équivalente (si non nouveau)
    sonde: object = None            # entrée discriminante (AMBIGU)
    justification: str = ""

    def __str__(self) -> str:
        if self.statut == INVENTION:
            return f"[INVENTION] {self.cible}\n      éléments à construire : {self.par}\n      ({self.justification})"
        if self.statut == EXISTE_DEJA:
            return f"[EXISTE DÉJÀ] {self.cible} = « {self.proche_de} »  ({self.par})"
        if self.statut == AMBIGU:
            return f"[AMBIGU] {self.cible} — spec sous-déterminé ; sonde discriminante : {self.sonde!r}"
        if self.statut == BRIQUE_MANQUANTE:
            return f"[BRIQUE MANQUANTE] {self.cible} — {self.justification}"
        return f"[INCOHÉRENT] {self.cible} — {self.justification}"


def _callable(code_ou_expr: str, point_entree: str):
    src = code_ou_expr if code_ou_expr.lstrip().startswith("def ") else f"def {point_entree}(x):\n    return {code_ou_expr}\n"
    ns: dict = {}
    try:
        exec(src, ns)
        return ns.get(point_entree)
    except Exception:
        return None


def _reproduit(f, paires) -> bool:
    if f is None:
        return False
    for a, o in paires:
        try:
            r = f(a)
            # ÉGALITÉ TYPE-EXACTE sur bool : en Python 1 == True et 0 == False, donc une réalisation qui rend
            # un INT 0/1 (ex. (x+1)%2) « reproduirait » une cible BOOLÉENNE et créerait une fausse AMBIGU
            # (repr '1' ≠ repr 'True') OU une fausse capacité. Une fonction qui rend 1 n'EST PAS celle qui rend
            # True : on exige donc que le caractère booléen coïncide. Général (toutes cibles bool), sound.
            if r != o or isinstance(r, bool) != isinstance(o, bool):
                return False
        except Exception:
            return False
    return True


def _sig(f, sondes):
    """Signature comportementale (résultats/erreurs) sur les sondes. Sert à mesurer distinction/équivalence."""
    out = []
    for s in sondes:
        try:
            out.append(repr(f(s)))
        except Exception:
            out.append("ERR")
    return out


def _asserts_held(nom, paires):
    from demande import _asserts
    return _asserts(nom, [((a,), o) for a, o in paires])


def examine_cible(nom: str, signature: str, exemples, exemples_held, budget: int = 2000,
                  existant: dict | None = None, tours_cegis: int = 0, proprietes=()) -> Verdict:
    """Tranche une fonction-cible en EXISTE_DEJA / INVENTION / AMBIGU / BRIQUE_MANQUANTE / INCOHERENT.
    `existant` = registre de capacités à utiliser (défaut : EXISTANT global) ; permet de juger contre une
    bibliothèque ÉTENDUE (phase « sommeil » : voir bibliotheque_invention.py).
    `tours_cegis` (opt-in, défaut 0 = flux INCHANGÉ) = boucle CEGIS côté RECHERCHE (Solar-Lezama 2006) :
    face à une frontière, si un candidat PARTIEL (reproduit les exemples) est tué par une paire du held-out,
    cette paire est un CONTRE-EXEMPLE : promue au spec, elle REDIRIGE les familles etend_* (dirigées par les
    exemples : seuils/constantes synthétisés depuis les données) et la recherche est relancée, `tours_cegis`
    fois au plus. GARDES : le held-out n'est JAMAIS vidé (≥ 2 paires requises pour consommer : il reste
    toujours un juge final à froid) ; un tour par contre-exemple (le plus discriminant, déterministe) ; les
    gardes de soundness (unicité comportementale, juge subprocess, nouveauté) s'appliquent inchangées au
    résultat ; la promotion est TRACÉE dans la justification (provenance servable).
    `proprietes` (opt-in, défaut () = flux INCHANGÉ) = held-out durci MÉTAMORPHIQUE (Chen 1998) : exigences
    déclarées du spec reliant f(T(x)) à f(x) SANS oracle exact (noms du catalogue metamorphique.PROPRIETES
    ou dicts custom de même forme). Effets : DURCIR (une réalisation qui reproduit les paires mais viole
    une propriété est écartée, témoin tracé — jamais servie) et TRANCHER (un AMBIGU se résout en INVENTION
    si la propriété tue les candidats non conformes et qu'il ne reste qu'un comportement — sans aller-retour
    utilisateur). Une propriété erronée rend le moteur plus conservateur, jamais un faux : FAUX=0."""
    existant = EXISTANT if existant is None else existant
    exemples = list(exemples)
    held = list(exemples_held or [])
    toutes = exemples + held

    # 0) COHÉRENCE : même entrée -> deux sorties = contradiction.
    vus: dict = {}
    for a, o in toutes:
        cle = repr(a)
        if cle in vus and vus[cle] != o:
            return Verdict(INCOHERENT, nom, justification="deux sorties différentes pour la même entrée")
        vus[cle] = o

    # `sondes_auto` renvoie des TUPLES d'arguments. Pour une tâche mono-arg, _sig appelle f(sonde) en passant la
    # sonde comme L'argument. Les sondes LISTE/MATRICE sont des tuples-DONNÉES (f les traite comme la séquence),
    # mais les sondes CHAÎNE sont des 1-tuples `(arg,)` -> f(("abc",)) erre pour TOUTES -> signature « tout ERR »
    # dégénérée -> FAUX EXISTE_DEJA (bug soundness sur chaînes). Fix : dé-envelopper les 1-tuples (= format mono-arg
    # chaîne) ; les tuples multi-éléments (données list/matrice) restent intacts.
    sondes = [s[0] if isinstance(s, tuple) and len(s) == 1 else s
              for s in (MoteurAutonome.sondes_auto(exemples) or [a for a, _ in toutes])]

    # Propriétés métamorphiques déclarées (opt-in) : résolues UNE fois ; probes = entrées réelles + sondes.
    regles = _MM().resoud(proprietes) if proprietes else []
    probes = [a for a, _ in toutes] + list(sondes) if regles else []

    def _conforme(f):
        """f respecte les propriétés déclarées (vrai si aucune) ; second retour = témoin de violation."""
        return _MM().respecte(f, regles, probes) if regles else (True, None)

    # 1) EXISTE DÉJÀ : une capacité connue reproduit la cible (exemples + held) — ET respecte les
    #    propriétés déclarées (une capacité qui viole une exigence du spec N'EST PAS la cible).
    for capa, expr in existant.items():
        g = _callable(expr, nom)
        if _reproduit(g, toutes) and _conforme(g)[0]:
            return Verdict(EXISTE_DEJA, nom, par=expr, proche_de=capa,
                           justification="déjà couvert par l'inventaire existant")

    # 2) RÉALISABLE par recombinaison connue ? On cherche EN PROCESS tous les atomes qui reproduisent
    #    exemples + held, puis on teste l'UNICITÉ comportementale (anti-coïncidence) sur les sondes.
    m = _moteur()
    del m.atomes[_BASE_LEN:]                 # purge les atomes contextuels d'une cible précédente
    m.etend_vocabulaire(exemples)            # comble le gap pour CETTE cible (indexation/folds/str)
    m.etend_composition(exemples)            # + schémas compositionnels dirigés (AGG∘map(f))
    m.etend_composition_liste(exemples)      # + LISTE-OP∘map(f) (sorted/reverse d'un map : carres_tries…)
    m.etend_composition_filtree(exemples)    # + AGG/liste(F for _e in x if COND) (filtrer+transformer+agréger : somme_carres_pairs…)
    m.etend_indexe(exemples)                 # + AGG(G for _i,_e in enumerate(x) if COND) INDEXÉ (points fixes x[i]==i, positions paires, _e*_i…)
    m.etend_paires(exemples)                 # + AGG sur couples (i<j) TOUTES-PAIRES O(n²) (nb inversions, paires égales, produits/écarts de couples)
    m.etend_sous_tableaux(exemples)          # + AGG sur sommes de sous-tableaux CONTIGUS x[i:j] (Kadane = meilleur segment)
    m.etend_matrice(exemples)                # + vocabulaire matriciel (primitives + AGG∘matrice : trace, grand_total…)
    m.etend_dict(exemples)                   # + vocabulaire dict (AGG∘values/keys + argmax/argmin : somme_valeurs…)
    m.etend_chaines(exemples)                # + vocabulaire chaînes-compositions (initiales, mot_le_plus_long, compte_voyelles…)
    m.etend_entier(exemples)                 # + vocabulaire ENTIER (entrée mono-int : formules fermées, factorielle/fibonacci en fold, plages…)
    m.etend_liste_chaines_fusion(exemples)   # + FUSION liste-de-chaînes (map/agg sur mots)
    m.etend_dict_listes(exemples)            # + FUSION dict-de-listes (agg par clé)
    m.etend_liste_paires(exemples)           # + FUSION liste-de-paires (combiner les 2 champs)
    m.etend_liste_dicts(exemples)            # + FUSION liste-d'enregistrements (agg/projection par champ découvert)
    m.etend_paire_listes(exemples)           # + INTER-SÉQUENCES (deux listes [A,B] : zip somme/produit scalaire…)
    m.etend_synthese(exemples)               # + AUTO-SYNTHÈSE : synthétise des primitives en cherchant les constantes dans les données
    m.etend_composition_generale(exemples)   # + MÉCANISME GÉNÉRATIF : compose g(f_k(…f_1(x))) profondeur 2 (défaut)
    candidats = [e for e, _ti, _to in m.atomes if _reproduit(_fn(e), toutes)]
    if not candidats:                        # ESCALADE PARESSEUSE (nuit 2026-06-24, « plus long/complexe ») : sur le
        m.etend_composition_generale(exemples, profondeur=3)   # tail dur (~1 %), chaînes de 3 transforms (coûteux,
        candidats = [e for e, _ti, _to in m.atomes if _reproduit(_fn(e), toutes)]   # donc seulement si rien trouvé)

    # PROPRIÉTÉS DÉCLARÉES : écarte les réalisations qui violent une exigence métamorphique du spec —
    # DURCIT (une violation que les paires ne voyaient pas n'est jamais servie) et TRANCHE (si les non
    # conformes portaient l'ambiguïté, il reste UN comportement -> INVENTION sans aller-retour utilisateur).
    if candidats and regles:
        conformes, temoin = [], None
        for e in candidats:
            ok, t = _conforme(_fn(e))
            if ok:
                conformes.append(e)
            elif temoin is None:
                temoin = t
        if not conformes:
            p, x, tx = temoin
            return Verdict(BRIQUE_MANQUANTE, nom,
                           justification=f"toute réalisation connue viole la propriété déclarée "
                                         f"« {p} » (témoin : f({x!r}) vs f({tx!r}))")
        candidats = conformes

    if candidats:
        # désaccord entre candidats sur une sonde -> spec sous-déterminé -> AMBIGU (sonde discriminante).
        sigs = {e: _sig(_fn(e), sondes) for e in candidats}
        for j, s in enumerate(sondes):
            if len({sigs[e][j] for e in candidats}) > 1:
                return Verdict(AMBIGU, nom, sonde=s,
                               justification="plusieurs réalisations distinctes satisfont le spec")
        # unique comportement. On prend la plus courte (Occam) et on la CONFIRME au juge (subprocess) sur held.
        S = min(candidats, key=len)
        code = f"def {nom}(x):\n    return {S}\n"
        if held and not juge(code, _asserts_held(nom, held), LIM).passe:
            return Verdict(BRIQUE_MANQUANTE, nom, justification="réalisation non confirmée par le juge sur le held-out")
        # NOUVEAUTÉ : comportement distinct de TOUTE capacité existante sur les sondes ?
        # SOUNDNESS (fix 2026-06-23, bug somme_uniques) : on n'assimile S à une capacité existante que si CELLE-CI
        # reproduit RÉELLEMENT exemples+held — sinon les sondes (parfois trop faibles, ex. sans doublon) créent une
        # FAUSSE équivalence et on renverrait un `par` qui ne reproduit pas les données (hallucination).
        sig_S = _sig(_fn(S), sondes)
        for capa, expr in existant.items():
            g = _callable(expr, nom)
            if g is not None and _sig(g, sondes) == sig_S and _reproduit(g, toutes) and _conforme(g)[0]:
                return Verdict(EXISTE_DEJA, nom, par=expr, proche_de=capa,
                               justification="réalisable mais équivalent à une capacité existante (non nouveau)")
        return Verdict(INVENTION, nom, par=S,
                       justification="recombinaison unique sous le spec, vérifiée (held-out), comportement nouveau")

    # 3) Aucune recombinaison connue -> FRONTIÈRE… sauf si la boucle CEGIS (opt-in) peut la repousser :
    #    un candidat PARTIEL (reproduit les exemples, tué par le held-out) prouve que la recherche pointait
    #    dans une direction que le spec visible ne détermine pas. La paire tueuse est le contre-exemple du
    #    vérificateur : promue au spec, elle enrichit les DONNÉES qui dirigent etend_* (seuils, constantes,
    #    types) et on relance — au lieu de conclure. `len(held) > 1` : on ne consomme JAMAIS le dernier juge.
    if tours_cegis > 0 and len(held) > 1:
        partiels = [e for e, _ti, _to in m.atomes if _reproduit(_fn(e), exemples)]
        if partiels:
            # Contre-exemple LE PLUS DISCRIMINANT : la paire du held-out qui tue le plus de partiels
            # (sélection arbitraire ⊇ minimale en pouvoir — littérature CEGIS ; on maximise l'information
            # par tour). Déterministe : première paire à égalité. > 0 garanti (aucun partiel n'est candidat,
            # donc chacun est tué par au moins une paire du held-out).
            tue = [sum(not _reproduit(_fn(e), [p]) for e in partiels) for p in held]
            k = max(range(len(held)), key=lambda i: tue[i])
            v = examine_cible(nom, signature, exemples + [held[k]], held[:k] + held[k + 1:],
                              budget=budget, existant=existant, tours_cegis=tours_cegis - 1,
                              proprietes=proprietes)
            return dataclasses.replace(v, justification=(
                v.justification + f" ; CEGIS : contre-exemple {held[k]!r} promu du held-out au spec"))

    # Aucune recombinaison connue -> FRONTIÈRE : il manque un atome (invention plus profonde).
    return Verdict(BRIQUE_MANQUANTE, nom,
                   justification="cohérente mais non réalisable par recombinaison connue : un principe neuf est requis")


if __name__ == "__main__":
    from garde_ressources import borne
    borne()
    print("=== MOTEUR DE DÉCOUVERTE D'INVENTIONS (vs ce qui existe, réalité-jugé) ===\n")
    CIBLES = [
        ("somme_totale", "xs", [([1, 2, 3], 6), ([5], 5)], [([0, 4], 4), ([2, 2], 4)]),                 # existe déjà
        ("amplitude", "xs", [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)],
         [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4), ([2, 8], 6)]),                                       # invention max-min
        ("somme_carres", "xs", [([1, 2, 3], 14), ([2, 3], 13)], [([5], 25), ([0, 4], 16), ([1, 1], 2)]),  # invention
        ("absurde", "xs", [([1, 2], 5)], [([1, 2], 9)]),                                                  # incohérent
    ]
    for nom, sig, ex, held in CIBLES:
        print(f"  {examine_cible(nom, sig, ex, held)}\n")
