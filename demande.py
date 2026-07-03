"""
DEMANDE — L'INTERFACE DE REQUÊTE (« la parole », 2026-06-17, recadrage Yohan « il faut pouvoir lui DEMANDER des
choses, sinon c'est problématique »).

Le moteur complet (43 étages + invention/substrat) prend une DEMANDE = (signature + EXEMPLES entrée->sortie) et
rend du CODE VÉRIFIÉ, ou un HORS honnête. Les exemples SONT le vérificateur (la réalité tranche) ; les exemples
held-out (recommandés) prouvent que la réponse GÉNÉRALISE (pas du hard-coding). Pas de modèle externe : la
compétence vit dans les générateurs ; le juge tranche.

Portée HONNÊTE : large (preuve_domaines = 10 domaines, et les 43 familles) mais BORNÉE — pour de l'arbitraire au-delà
des familles, il faudra le modèle appris (fork stratégique, hors harnais). `demande` rend HORS plutôt que du faux.
"""

from __future__ import annotations

import dataclasses
import tempfile
from pathlib import Path

from auto_synthese import synthetise
from compounding import resoudre
from comprehension import Predicteur
from generateur import TYPES_RICHES, GenerateurOrchestre
from juge import Limites, juge
from routeur import RouteurZone, charge_config, resoudre_route, resoudre_route_rr, resoudre_route_rr2
from solveur_type import resoudre_demande
from store import Store
from strategies import RouteurStrategie, apprendre_toutes, resoudre_route_strategie
from taches import Tache

LIM = Limites(temps_s=1, cpu_s=1)


def _d(nom, corps):
    return (nom, f"def {nom}(*args, **kwargs):\n    return {corps}\n")


# Vocabulaire INNÉ que l'IA « connaît » au départ (primitives/ops/prédicats confirmés). La compétence émerge en les
# composant/inventant ; le store reste vide (la connaissance est dans les générateurs, pas des réponses pré-mâchées).
PRIMS = [_d("carre", "args[0]*args[0]"), _d("cube", "args[0]**3"), _d("incremente", "args[0]+1"),
         _d("double", "args[0]+args[0]"), _d("inverse_chaine", "args[0][::-1]"), _d("trie", "sorted(args[0])"),
         _d("avant_dernier", "args[0][-2]"), _d("premier", "args[0][0]"), _d("dernier", "args[0][-1]")]
OPS = [_d("mul", "args[0]*args[1]"), _d("add", "args[0]+args[1]"), _d("sub", "args[0]-args[1]"),
       _d("mod", "args[0]%args[1]"), _d("max2", "args[0] if args[0] > args[1] else args[1]"),
       _d("min2", "args[0] if args[0] < args[1] else args[1]")]
PREDS = [_d("est_positif", "args[0]>0"), _d("est_negatif", "args[0]<0"),
         ("is_pair", "def is_pair(*args, **kwargs):\n    return args[0] % 2 == 0\n")]


def construit_moteur(store):
    """Le moteur COMPLET (TOUS les étages ON) — la pleine compétence du cœur."""
    return GenerateurOrchestre(
        store, primitives=PRIMS, ops=OPS, predicats=PREDS,
        predicteur=Predicteur(store, types=TYPES_RICHES),
        inventer=True, substrat=True, profondeur_compo=2, recurrence=True, boucle_while=True,
        map_repli=True, invariant=True, jointure_profonde=True, predicat_mesures=True,
        positionnel=True, mots=True, multipasse=True, adjacence=True, imbrique=True,
        dict_accu=True, group_by=True, serie=True, generer_tester=True, comprehension_generale=True,
        fenetre=True, matrice=True, repetition=True, index_ordonne=True, sous_suite=True,
        paires=True, run_length=True, dict_transform=True, profond=True, filtre_seuil=True,
        matrice_reduce=True, dedup=True, prefixe_commun=True, monnaie=True, cesar=True, record=True,
        anticipation=True, optimisation=True, ranking=True, bits=True, logique=True, ensembles=True,
        statistiques=True, conversion=True, parsing=True, math_avance=True, chiffres=True,
        liste_transforms=True, chaines_avancees=True, diviseurs=True, graphe=True, combinatoire=True,
        iteration=True, acc_courant=True,
        equilibre=True, premier_unique=True, chevauchement=True, dp2d=True, geometrie=True,
        comptage_combinatoire=True, pile=True, suite=True, calendrier=True, graphe_connexite=True,
        tableaux=True, numerique=True, checksum=True, dp_int=True)


def _asserts(fn, exemples):
    lignes = [f"    assert c({', '.join(repr(a) for a in args)}) == {exp!r}" for args, exp in exemples]
    return "def check(c):\n" + "\n".join(lignes) + f"\ncheck({fn})\n"


@dataclasses.dataclass
class Reponse:
    """Le résultat d'une demande. `ok` = du code vérifié a été trouvé."""
    ok: bool
    code: str | None
    etage: str | None        # quelle compétence a résolu
    appels: int              # coût (appels juge)
    generalise: bool         # a passé les exemples held-out (preuve qu'il ne mémorise pas)

    def __str__(self) -> str:
        if not self.ok:
            return f"<HORS DE PORTÉE — aucun code vérifié ({self.appels} appels). La réalité n'a rien validé.>"
        g = "GÉNÉRALISE (held-out vérifié)" if self.generalise else "exemples visibles seulement (donne des held-out !)"
        return f"<RÉSOLU via `{self.etage}` en {self.appels} appels — {g}>\n{self.code}"


def demande(point_entree: str, signature: str, exemples, exemples_held=None,
            budget: int | None = None, k: int = 1000, rapide: bool = True) -> Reponse:
    """
    DEMANDE de code à l'IA. `point_entree`/`signature` = la fonction voulue ; `exemples` = [(args, sortie), ...] qui
    DÉFINISSENT le besoin (la réalité qui juge) ; `exemples_held` = contre-épreuve de généralisation (recommandé) ;
    `budget` = borne de puissance opt-in ; `rapide` = active le chemin rapide means-end (mettre False = moteur lourd
    seul, pour comparer). Rend une `Reponse` (code vérifié ou HORS honnête).
    """
    # CHEMIN RAPIDE dirigé par le but (le COMMENT : means-end < énumération en avant). N'agit que sur le mono-entrée
    # int/list ; reconfirmé au vrai juge ; sinon retombe sur le moteur lourd, INTACT. (cf. CAP_LE_COMMENT.md)
    if rapide:
        code_me, cout_me = resoudre_demande(point_entree, exemples, exemples_held, budget=budget)
        if code_me is not None:
            return Reponse(ok=True, code=code_me, etage="means-end", appels=cout_me, generalise=bool(exemples_held))

    prompt = f'def {point_entree}({signature}):\n    """..."""'
    tests = _asserts(point_entree, exemples)
    held = _asserts(point_entree, exemples_held) if exemples_held else ""
    tache = Tache(id=f"demande/{point_entree}", point_entree=point_entree, prompt=prompt,
                  tests=tests, tests_held_out=held)
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        orch = construit_moteur(store)
        etage, appels, code, _ = resoudre(orch, tache, LIM, k, budget=budget)
    # AUTO-SYNTHÈSE en dernier recours (cf. AssistantIA.demande) : l'IA construit la brique si le moteur a échoué.
    if code is None:
        src = synthetise(exemples, exemples_held)
        if src is not None:
            code_as = src.replace("def f(", f"def {point_entree}(", 1)
            if juge(code_as, _asserts(point_entree, list(exemples) + list(exemples_held or [])), LIM).passe:
                return Reponse(ok=True, code=code_as, etage="auto-synthese", appels=appels,
                               generalise=bool(exemples_held))
    # resoudre n'accepte un succès que s'il passe DÉJÀ le held-out -> generalise est garanti si held fourni.
    generalise = bool(code) and bool(held)
    return Reponse(ok=code is not None, code=code, etage=etage, appels=appels, generalise=generalise)


class AssistantIA:
    """
    L'IA à MÉMOIRE PERSISTANTE (2026-06-17, « moins de puissance, l'IA s'améliore à l'usage ») — un store + un
    routeur (zone-routing) qui SE RÉCHAUFFENT à chaque demande résolue : les demandes suivantes de même CLÉ
    `(arité, type_in, type_out, …)` sont ROUTÉES vers le bon étage -> bien moins d'appels juge. SÛR : la
    zone-routing est gate-protégée (jamais pire que l'escalade ; à froid == escalade). Le store persiste sur disque
    -> les compétences s'accumulent entre usages. C'est la voie SÛRE pour capter le plafond du routage (cf.
    `cherche_ordre.py` : le ré-ordonnancement brut donne −88 % mais MASQUE -> non adopté ; le routing, lui, est sûr)."""

    # PRIOR DE ROUTAGE livré (compétence accumulée hors-ligne) : rend le routeur CHAUD dès le 1ᵉʳ appel à froid sur les
    # clés connues -> capte le plafond du routing SANS attendre l'usage. Sound : gate de confiance + fallback escalade
    # intacts (un prior bruité ne fait jamais pire que l'escalade). Construit par `construit_prior.py`.
    PRIOR = str(Path(__file__).with_name("routeur_prior.json"))

    # CONFIG AUTO-MESURÉE (AutoFolio-lite, cf. routeur.auto_configure) : seuil/k mesurés offline au lieu de fixés
    # à la main. Opt-in comme le prior : sans config, les défauts codés (seuil=8, k par appel) restent EXACTS.
    CONFIG = str(Path(__file__).with_name("routeur_config.json"))

    def __init__(self, chemin_store, prior: str | None = None, config: str | None = None):
        # prior=None (DÉFAUT) -> escalade froide DÉTERMINISTE : les validations épinglent l'étage pour PROUVER la brique
        # (anti-coïncidence) ; le prior réordonnerait et changerait l'étage gagnant des tâches multi-résolubles.
        # prior="DEFAUT" -> charge le prior livré (production : routeur CHAUD à froid, « <100 partout »). prior=<chemin>
        # -> charge un prior donné. Le prior est SOUND (gate + fallback escalade) : il n'affecte QUE l'ordre/coût.
        # config="DEFAUT"/<chemin> -> charge la config auto-mesurée (seuil du gate + k par défaut) si présente.
        self._store = Store(chemin_store)
        cfg = None
        if config == "DEFAUT":
            cfg = charge_config(self.CONFIG)
        elif config:
            cfg = charge_config(config)
        self._k_defaut = int(cfg["k"]) if cfg else None
        self._routeur = RouteurZone(seuil=int(cfg["seuil"])) if cfg else RouteurZone()   # routage des ÉTAGES
        if prior == "DEFAUT":
            self._routeur.charge(self.PRIOR)       # charge le prior livré s'il existe (sinon no-op -> escalade froide)
        elif prior:
            self._routeur.charge(prior)
        self._routeur_strat = RouteurStrategie()   # méta-routage de la STRATÉGIE de traversée (clé -> rr2/occam/…)
        self._orch = construit_moteur(self._store)

    def prechauffe(self, taches, k: int = 1000) -> None:
        """WARM-UP AMORTI (one-shot) du méta-routeur sur une batterie de compétence : pour chaque tâche, on réchauffe
        le routeur d'ÉTAGES (clé -> zone gagnante) PUIS on mesure toutes les stratégies (apprendre_toutes) pour que le
        routeur de STRATÉGIE sache router toute tâche de même clé vers la moins chère. Hors chemin chaud ; sound (ne
        change aucun résultat, mesure pure de coût). En production sans batterie, l'amélioration vient de l'usage."""
        for t in taches:
            etage, _, code, _ = resoudre_route_strategie(self._orch, t, self._routeur, self._routeur_strat, LIM, k)
            if code is not None:
                self._routeur.apprendre(t, etage)
            apprendre_toutes(self._orch, t, self._routeur, self._routeur_strat, LIM, k)

    # BORNE du chemin rapide means-end (campagne « <100 partout », 2026-06-20). means-end churnait jusqu'à ~15-19k évals
    # sur des cibles que le MOTEUR résout (souvent moins cher ET via la vraie brique) — coût NON routable (means-end est
    # avant le routeur) + risque de COÏNCIDENCE (expr profonde calée sur peu de points). On CAPE : means-end garde ses
    # gains shallow/cheap (third_max ~6), sinon abandonne et laisse le moteur+routeur faire. SOUND : means-end NON-CAPÉ
    # reste en ULTIME secours si le moteur échoue -> couverture STRICTEMENT identique (le cap ne change que l'ordre/coût).
    MEANS_END_CAP = 300

    def demande(self, point_entree: str, signature: str, exemples, exemples_held=None, k: int | None = None) -> Reponse:
        # k explicite > config auto-mesurée > défaut codé 1000 (backward-compat : sans config, comportement EXACT).
        k = k if k is not None else (self._k_defaut or 1000)
        # CHEMIN FROID dirigé par le but, CAPÉ : means-end résout les cibles shallow en ~dizaines d'évals (quasi gratuit) ;
        # au-delà du cap il abandonne -> le moteur+routeur prend le relais (cf. MEANS_END_CAP).
        code_me, cout_me = resoudre_demande(point_entree, exemples, exemples_held, budget=self.MEANS_END_CAP)
        if code_me is not None:
            return Reponse(ok=True, code=code_me, etage="means-end", appels=cout_me, generalise=bool(exemples_held))

        prompt = f'def {point_entree}({signature}):\n    """..."""'
        tests = _asserts(point_entree, exemples)
        held = _asserts(point_entree, exemples_held) if exemples_held else ""
        tache = Tache(id=f"assist/{point_entree}", point_entree=point_entree, prompt=prompt,
                      tests=tests, tests_held_out=held)
        # MÉTA-ROUTAGE (2026-06-19, vision Yohan « s'adapter à la situation, router par clé/x/y comme le cerveau ») :
        # resoudre_route_strategie choisit la STRATÉGIE de traversée par clé (routeur_strat). À froid -> rr2 (DEFAUT) ==
        # comportement antérieur exact (round-robin prédits-puis-fallback, −95 % vs escalade). À chaud (clé réchauffée
        # par prechauffe/usage OU PRIOR livré) -> la stratégie la moins chère de la clé : per-clé LOO −24 % mesuré, SÛR.
        etage, appels, code, verdict = resoudre_route_strategie(self._orch, tache, self._routeur, self._routeur_strat, LIM, k)
        if code is None:
            # ULTIME SECOURS 1 (coverage) : means-end NON-CAPÉ, seulement si le moteur a échoué -> jamais une régression.
            code_me, cout_me = resoudre_demande(point_entree, exemples, exemples_held)
            if code_me is not None:
                return Reponse(ok=True, code=code_me, etage="means-end", appels=cout_me, generalise=bool(exemples_held))
            # ULTIME SECOURS 2 (2026-06-24) : AUTO-SYNTHÈSE PAR SQUELETTES — l'IA CONSTRUIT la brique manquante à partir
            # de squelettes génériques + les exemples (= la source de vérité). SOUND : synthetise n'émet que du sound
            # (anti-coïncidence par sondes), et on RE-VÉRIFIE au vrai juge sur exemples+held -> jamais un faux ; None
            # honnête sinon. C'est « l'IA se complète elle-même » quand le catalogue d'étages ne couvre pas la cible.
            src = synthetise(exemples, exemples_held)
            if src is not None:
                code_as = src.replace("def f(", f"def {point_entree}(", 1)
                verif = _asserts(point_entree, list(exemples) + list(exemples_held or []))
                if juge(code_as, verif, LIM).passe:
                    return Reponse(ok=True, code=code_as, etage="auto-synthese", appels=appels,
                                   generalise=bool(exemples_held))
        if code is not None:
            try:
                self._store.ajoute(tache, code, verdict)     # persiste le succès (compétence accumulée)
            except ValueError:
                pass
            self._routeur.apprendre(tache, etage)            # RÉCHAUFFE le routeur (clé -> étage)
        return Reponse(ok=code is not None, code=code, etage=etage, appels=appels, generalise=bool(code) and bool(held))


if __name__ == "__main__":
    # Démo : on PARLE à l'IA — on lui demande du code par l'exemple, du facile à l'infaisable.
    print("=== DÉMO — on demande du code à l'IA, par l'exemple (facile -> infaisable) ===\n")
    demandes = [
        ("somme_carres", "xs", [([1, 2, 3], 14), ([2, 3], 13)], [([5], 25), ([0, 4], 16)]),
        ("deuxieme_plus_grand", "xs", [([3, 1, 2], 2), ([5, 1, 4, 2], 4)], [([9, 7, 8], 8)]),
        ("gcd", "a, b", [(12, 8, 4), (7, 3, 1)], [(100, 60, 20)]),     # 3-uplets : (a, b, attendu)
        ("compress", "s", [("aaabb", "a3b2"), ("x", "x1")], [("", ""), ("abab", "a1b1a1b1")]),
        ("tri_fusion_bizarre", "xs", [([3, 1, 2], 42)], [([5], 99)]),  # incohérent/hors-portée -> HORS honnête
    ]
    for spec in demandes:
        pe, sig = spec[0], spec[1]
        ex = [(t[:-1], t[-1]) for t in spec[2]]
        exh = [(t[:-1], t[-1]) for t in spec[3]] if len(spec) > 3 else None
        rep = demande(pe, sig, ex, exh)
        print(f"# demande: {pe}({sig})")
        print(rep, "\n")
