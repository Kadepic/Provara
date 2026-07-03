"""
MOTEUR DE RESTITUTION — le pendant du moteur d'ANALYSE (examine_cible). L'analyse DÉRIVE ce qu'on ne sait pas ;
la restitution RAPPELLE ce qu'on sait déjà, vite, exact, routé par domaine (mandat Yohan 2026-06-24).

Architecture issue de la recherche profonde 50 sondes (model-free, sound, machine-native > réseau de neurones) :
  • SHARDS PAR DOMAINE (faits) — activation parcimonieuse : on ne consulte que le(s) shard(s) routé(s) (gated,
    predict-then-fallback, façon Mixture-of-Experts) -> énergie + vitesse, parallélisable à l'échelle.
  • RAPPEL EXACT MÉMOIRE-D'ABORD (O(1)) : on rappelle au lieu de re-dériver (3×5=15, Macron 2026) ; absent -> HORS.
  • SCORING ACT-R base-level `B = ln(Σ (Δt+1)^-d)` (fréquence+récence) -> chaud/froid principié, cheap (cf. routing).
  • CONSOLIDATION « sommeil » (fusion #1, TESTÉE ÷9) : compresse les résultats mémorisés en RÈGLES via le moteur
    d'analyse (N faits -> 1 brique + dérivation), sound (gardée seulement si reproduit le held-out -> FAUX=0).
  • SOUND : rappel exact ou HORS honnête ; jamais une devinette. Briques partagées (une capacité transcende les
    domaines), faits shardés (le savoir est local au domaine).
"""
from __future__ import annotations

import math
import os

from base_faits import VERIFIE, HORS, normalise, cherche as _cherche_base, Fait
from memoire_faits import MemoireFaits
from memoire_briques import MemoireBriques
from deduction import MoteurDeduction
import moteur_invention as MI
import lecteur as _LEC   # lecteur générique DATA (#3) : tables ingérées (numero_atomique, prefixe_si, continent…)

# ROUTAGE par relation -> domaine (table déterministe, sound, sans modèle ; fallback = 'general').
_ROUTAGE = {
    "calcul": "calcul",
    "capitale": "geo", "president": "geo", "pays": "geo", "continent": "geo", "monnaie": "geo",
    "symbole_chimique": "chimie", "masse_molaire": "chimie", "numero_atomique": "chimie",
    "definition": "langue", "traduction": "langue", "synonyme": "langue",
}
DOMAINES = ["calcul", "geo", "chimie", "langue", "general"]


def _route(relation: str) -> str:
    return _ROUTAGE.get(normalise(relation).split(" ")[0], "general")


class MoteurRestitution:
    """Restitution routée, exacte, model-free. Faits shardés par domaine + briques partagées + scoring ACT-R."""

    def __init__(self, racine: str | None = None, decay: float = 0.5):
        self.racine = racine
        self.decay = decay
        self.t = 0                                   # horloge logique (récence)
        self._acces: dict[str, list[int]] = {}       # clé -> ticks d'accès (pour ACT-R)
        self.shards: dict[str, MemoireFaits] = {}
        for d in DOMAINES:
            chem = os.path.join(racine, f"faits_{d}.json") if racine else None
            self.shards[d] = MemoireFaits(chemin=chem)
        self.briques = MemoireBriques(
            chemin=os.path.join(racine, "briques.json") if racine else None, base=MI.EXISTANT)
        self.cache_calc: dict[str, tuple] = {}       # "input" -> (input_obj, output) pour la compression
        self.regles: list[tuple] = []                # règles de déduction (tete, corps, nom)
        self._dede: MoteurDeduction | None = None    # moteur de déduction caché (invalidé si faits/règles changent)
        self._regle_calc = None                      # FUSION #2 : règle consolidée des calculs (répond les neufs)
        # compteurs de mesure
        self.stats = {"hits": 0, "miss": 0, "deduits": 0, "shards_consultes": 0, "shards_skippes": 0}

    # — horloge / activation ACT-R —
    def _tick(self, cle: str):
        self.t += 1
        self._acces.setdefault(cle, []).append(self.t)

    def activation(self, cle: str) -> float:
        """ACT-R base-level : B = ln(Σ (Δt+1)^-d). Plus c'est fréquent ET récent, plus c'est 'chaud'."""
        ts = self._acces.get(cle)
        if not ts:
            return float("-inf")
        return math.log(sum((self.t - tj + 1) ** (-self.decay) for tj in ts))

    def activation_provenance(self, cle: str) -> float:
        """FUSION #3 — activation ACT-R PONDÉRÉE par la PROVENANCE : un fait dont BEAUCOUP de faits dérivés
        dépendent (grand fan-out) reste chaud même peu consulté (il est structurellement central). Sound : simple
        score, n'affecte que le tiering (jamais la vérité). fan-out = nb de faits dérivés citant ce fait en support."""
        base = self.activation(cle)
        parts = cle.split("|")
        if len(parts) < 2 or not self.regles:
            return base
        rel, ent = parts[0], parts[1]
        fait = self.shards.get(_route(rel), self.shards["general"]).cherche(rel, ent)
        if fait is None:
            return base
        triplet = (rel, ent, str(fait.valeur))
        d = self._deduction()
        fanout = sum(1 for just in d.prov.values() for entry in just
                     if entry[0] != "base" and triplet in entry[1])
        return base + math.log(1 + fanout) if fanout else base

    def rappel_associatif(self, cue: str) -> list:
        """FUSION #4 (version SOUND) — rappel par INDICE PARTIEL : tous les faits dont la clé contient le cue
        (entité/relation), pas seulement la clé exacte. Index inversé exact (pas d'approximation neuronale) :
        « tout ce que je sais sur Paris » -> faits reliés. Model-free, jamais un faux (match de token exact)."""
        c = normalise(cue)
        out = []
        for dom, shard in self.shards.items():
            for k, e in shard.faits.items():
                if c in k.split("|"):
                    out.append((k, e["valeur"], dom))
        return out

    # — RESTITUTION (rappel exact routé, mémoire-d'abord) —
    def restitue(self, relation: str, entite: str, contexte: str = ""):
        """Route -> shard pertinent -> lookup exact. Renvoie (VERIFIE, Fait, origine) ou (HORS, None, None).
        Sound : rappel exact ou HORS honnête. Compte les shards consultés vs skippés (énergie)."""
        dom = _route(relation)
        self.stats["shards_consultes"] += 1
        self.stats["shards_skippes"] += len(DOMAINES) - 1      # activation parcimonieuse : les autres sont skippés
        f = self.shards[dom].cherche(relation, entite, contexte)
        if f is None and dom != "general":
            f = self.shards["general"].cherche(relation, entite, contexte)  # fallback gated
            self.stats["shards_consultes"] += 1
            self.stats["shards_skippes"] -= 1
        if f is None:
            f = _LEC.cherche(relation, entite)                  # repli : lecteur DATA (tables ingérées) PUIS amorce base_faits
        if f is not None:
            self._tick(f"{normalise(relation)}|{normalise(entite)}|{normalise(contexte)}")
            self.stats["hits"] += 1
            return VERIFIE, f, dom
        # RAISONNEMENT : pas en mémoire directe -> tenter de DÉRIVER par les règles (sound), puis MÉMOÏSER (tabling).
        if self.regles and not contexte:
            reps = self._deduction().reponses(normalise(relation), normalise(entite))
            if reps:
                val, _prov = reps[0]
                self.retient(relation, entite, val, "derive", "déduction")   # mémoïse -> direct la prochaine fois
                self.stats["deduits"] += 1
                return VERIFIE, Fait(val, "derive", "déduction"), "deduit"
        self.stats["miss"] += 1
        return HORS, None, None

    def retient(self, relation, entite, valeur, categorie, source, contexte=""):
        dom = _route(relation)
        ok = self.shards[dom].retient(relation, entite, valeur, categorie, source, contexte)
        if ok:
            self._tick(f"{normalise(relation)}|{normalise(entite)}|{normalise(contexte)}")
            self._dede = None                         # un nouveau fait invalide la fermeture déduite
        return ok

    # — RAISONNEMENT : règles de déduction sur les faits SANS contexte (Datalog semi-naïf, sound) —
    def ajoute_regle(self, tete, corps, nom=""):
        self.regles.append((tete, corps, nom))
        self._dede = None

    def _deduction(self) -> MoteurDeduction:
        """Construit (et cache) le moteur de déduction sur les faits contextless de tous les shards + règles."""
        if self._dede is not None:
            return self._dede
        d = MoteurDeduction()
        for shard in self.shards.values():
            for cle, e in shard.faits.items():
                parts = cle.split("|")
                rel, ent, ctx = parts[0], parts[1], (parts[2] if len(parts) > 2 else "")
                if not ctx and e.get("categorie") != "derive":   # base SEULEMENT : les faits dérivés/mémoïsés
                    d.ajoute_fait(rel, ent, str(e["valeur"]), e.get("source", "mémoire"))  # sont RE-dérivés (provenance intacte)
        for tete, corps, nom in self.regles:
            d.ajoute_regle(tete, corps, nom)
        d.materialise()
        self._dede = d
        return d

    # — mémoïsation de calcul (3×5=15 : calculé une fois, rappelé ensuite) —
    def memorise_calcul(self, input_obj, output):
        cle = repr(input_obj)
        self.cache_calc[cle] = (input_obj, output)
        self.shards["calcul"].retient("calcul", cle, str(output), "calcul", "arithmétique vérifiée")
        self._tick(f"calcul|{normalise(cle)}|")

    def rappelle_calcul(self, input_obj):
        f = self.shards["calcul"].cherche("calcul", repr(input_obj))
        if f:
            self._tick(f"calcul|{normalise(repr(input_obj))}|")
            self.stats["hits"] += 1
            return f.valeur
        # FUSION #2 — MÉMOÏSATION ADAPTATIVE : calcul jamais vu MAIS on a appris la RÈGLE (consolidation) ->
        # on l'APPLIQUE (sound, vérifiée) et on mémoïse le résultat, au lieu de re-chercher. CBR « reuse ».
        if self._regle_calc is not None:
            fn = MI._callable(self._regle_calc, "f")
            try:
                val = fn(input_obj)
            except Exception:
                val = None
            if val is not None:
                self.memorise_calcul(input_obj, val)
                self.stats["deduits"] += 1
                return str(val)
        self.stats["miss"] += 1
        return None

    # — CONSOLIDATION « sommeil » : compresse les résultats mémorisés en RÈGLES (fusion #1, sound) —
    def consolide(self):
        """Regarde les calculs mémorisés et INDUIT la règle qui les engendre (examine_cible) ; gardée seulement
        si elle reproduit un held-out (FAUX=0). N faits -> 1 brique + dérivation -> la mémoire RÉTRÉCIT. Renvoie
        un rapport (règles apprises, faits rendus dérivables, ratio)."""
        faits = list(self.cache_calc.values())
        rapport = {"faits": len(faits), "regles_neuves": 0, "regle_reutilisee": False, "derivables": 0, "par": []}
        if len(faits) >= 6:
            ex, held = faits[:3], faits[3:]
            v = MI.examine_cible("regle_consolidee", "x", ex, held)
            # la règle reproduit-elle TOUS les faits ? (neuve OU déjà connue : dans les deux cas ils deviennent
            # dérivables -> on les évince = compression. On note seulement si la brique est NOUVELLE pour la mémoire.)
            if v.par and MI._reproduit(MI._callable(v.par, "f"), faits):
                neuve = self.briques.retient(v.par)     # True si la mémoire ne la connaissait pas encore
                rapport["regles_neuves"] = 1 if neuve else 0
                rapport["regle_reutilisee"] = not neuve
                rapport["derivables"] = len(faits)
                rapport["par"].append(v.par)
                self._regle_calc = v.par                # FUSION #2 : la règle répondra les calculs NEUFS (adaptation)
                self.cache_calc.clear()                 # faits dérivables -> évincés (compression), règle gardée
        return rapport

    def sommeil(self):
        """CONSOLIDATION « sommeil » (CLS) — orchestration SOUND : (1) compresse les résultats mémorisés en RÈGLES
        (fusion #1, faits dérivables évincés -> mémoire RÉTRÉCIT) ; (2) tiering ACT-R = sépare CHAUD (souvent/récent)
        et FROID (rarement utilisé) pour un accès rapide. Ne perd RIEN (froid reste rappelable). Renvoie un rapport."""
        rap = {"compression": self.consolide()}
        # tiering ACT-R : médiane d'activation -> chaud au-dessus, froid en dessous (vue, pas de perte)
        cles = [c for c in self._acces]
        if cles:
            acts = sorted(self.activation(c) for c in cles)
            seuil = acts[len(acts) // 2]
            chaud = sum(1 for c in cles if self.activation(c) >= seuil)
            rap["tiering"] = {"total": len(cles), "chaud": chaud, "froid": len(cles) - chaud, "seuil": round(seuil, 3)}
        rap["briques"] = len(self.briques)
        rap["faits"] = sum(len(s) for s in self.shards.values())
        return rap

    def sauve(self):
        for s in self.shards.values():
            s.sauve()
        self.briques.sauve()


if __name__ == "__main__":
    from garde_ressources import borne
    borne(max_cpu_s=200)
    print("=== DÉMO MOTEUR DE RESTITUTION (routé, exact, ACT-R, consolidation) ===")
    m = MoteurRestitution()
    m.retient("president", "France", "Macron", "passe", "actualité", contexte="2026")
    m.retient("capitale", "Espagne", "Madrid", "convention", "géo")
    print("  restitue président/France/2026 ->", m.restitue("president", "France", "2026")[1])
    print("  restitue président/France/1800 ->", m.restitue("president", "France", "1800")[0], "(HORS)")
    print(f"  routage : {m.stats['shards_consultes']} shards consultés, {m.stats['shards_skippes']} skippés (énergie)")
    # mémoïsation + consolidation
    import random
    rng = random.Random(1)
    for _ in range(12):
        ab = [rng.randint(0, 12), rng.randint(0, 12)]
        m.memorise_calcul(ab, ab[0] * ab[1])
    rap = m.consolide()
    print(f"  consolidation : {rap['faits']} calculs -> {rap['derivables']} dérivables par règle "
          f"{'NEUVE' if rap['regles_neuves'] else 'réutilisée'} : {rap['par']}")
