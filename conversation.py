"""
MÉMOIRE DE CONVERSATION PERSISTANTE — « qu'elle se rappelle des conversations : ce que l'utilisateur a dit,
ses propres réponses, PAR conversation ; comme un LLM qu'on reprend, SAUF qu'elle n'est PAS bloquée par la
fenêtre de contexte » (mandat Yohan 2026-06-25, à partir du « fossé de l'intelligence éphémère », StackOverflow).

LE PROBLÈME (le post LinkedIn) : un agent règle un bug à 14 h, à 14 h 05 la fenêtre de contexte s'est vidée et
le savoir est parti avec. Un autre agent, ailleurs, re-galère vingt minutes sur le même cas réglé cinq minutes
plus tôt. La réponse : une base où l'agent CHERCHE D'ABORD une réponse validée, puis DÉPOSE ce qu'il apprend pour
les suivants. Trois pièges cités : frontière public/privé, RGPD vs CLOUD Act, et « aucune brique souveraine clé en
main n'existe encore ». Ce module EST cette brique, et elle est structurellement souveraine.

CE QUE CETTE BRIQUE AJOUTE (jumelle de `memoire_faits` [FAITS] et `memoire_briques` [CAPACITÉS] : ici, le DIALOGUE) :
  • RÉTENTION par conversation : chaque TOUR (qui parle, quoi, quand) est append-only sur disque (JSONL), durable,
    horodaté, séquencé. Survit aux runs, aux /clear, aux redémarrages. Un tour ≈ quelques dizaines/centaines d'o.
  • REPRISE (`reprend`) : rejouer une conversation, ou seulement sa FENÊTRE récente (n derniers tours), VERBATIM.
  • RAPPEL NON BORNÉ PAR LE CONTEXTE (`rappelle`) — le cœur anti-éphémère : on ne RECHARGE JAMAIS toute l'histoire
    dans un contexte. Un index inversé (token -> tours) ramène les k tours PERTINENTS d'un historique arbitrairement
    long en O(taille de la requête), pondérés idf. 1 million de tours -> on en lit k, pas 1 million. C'est l'inverse
    exact de la fenêtre de contexte qui sature : la mémoire CROÎT, le coût de rappel NON.
  • DÉPÔT-POUR-LE-SUIVANT (cross-conversation) : `rappelle(req)` sans conv = cherche dans TOUTES les conversations
    -> l'agent B retrouve la réponse validée que l'agent A a déposée. C'est la base de connaissances pour agents.
  • FRONTIÈRE PUBLIC/PRIVÉ (1er piège) : chaque conversation a un `scope` ("prive" par défaut / "public"). Le rappel
    public NE VOIT JAMAIS le privé. On ne fuite pas une conversation privée dans le pot commun.
  • RGPD — DROIT À L'EFFACEMENT (2e piège) : `oublie(conv)` supprime intégralement une conversation (fichier + index).
    Effacement réel, pas un drapeau. Souveraineté (3e piège) : 100 % local, zéro réseau, zéro IA tierce, tient sur
    clé USB (la thèse du projet). Le CLOUD Act n'a aucune prise sur des fichiers qui ne quittent jamais la machine.

SOUNDNESS (FAUX=0, comme tout le projet) : on RESTITUE ce qui a réellement été dit (verbatim) ou RIEN (liste vide,
« je n'ai pas de tour pertinent ») — JAMAIS une reformulation inventée. `rappelle` ne renvoie un tour que s'il
partage au moins un token DISCRIMINANT (hors mots-vides FR/EN) avec la requête : un recouvrement uniquement sur des
mots-fonction (le, la, de, the, of…) ne compte pas -> non renvoyé. Aucune devinette, aucune hallucination.
"""
from __future__ import annotations

import json
import math
import os
import tempfile
import time

from base_faits import normalise

# Dossier de persistance OFFLINE (comme datasets/lecteur) : un fichier .jsonl par conversation, append-only.
_DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "conversations")

_SCOPES = ("prive", "public")

# MOTS-VIDES FR/EN (mots-fonction). Ils ne sont JAMAIS discriminants : « tarte aux pommes » ne doit pas être
# rappelée par un tour qui partage seulement « aux »/« et ». L'idf seul ne suffit pas (un mot dans 1200/1202 tours
# garde un idf minuscule mais >0 -> fuite). On les exclut donc de l'indexation ET du rappel. Liste fixe et
# déterministe (model-free) ; le projet est FR-primaire + termes techniques EN, d'où ce périmètre assumé.
_MOTS_VIDES = frozenset("""
a à as au aux avec avait avoir c ce ces cet cette ceci cela d de des du dans donc elle elles en encore est et eu
être il ils j je l la le les leur leurs lui ma mais me mes moi mon n ne ni nos notre nous on ont ou où par pas
peu plus pour qu que quel quelle quels quelles qui quoi s sa sans se ses si son sont sous sur t ta te tes toi ton
tu un une vos votre vous y était été aussi alors comme dont fait faire son the of to in on at and or but is are be
was were it this that for with from as by an into your you we they he she his her our their not no yes do does did
has have had can will would should could about then than them there here what which who whom how when where why
""".split())


def _tokens(texte: str) -> list[str]:
    """Tokens DISCRIMINANTS d'un texte : `normalise` (minuscule, sans accents/ponctuation) puis retrait des
    mots-vides FR/EN. Base commune à l'indexation et au rappel. Model-free, déterministe."""
    return [t for t in normalise(texte).split() if t and t not in _MOTS_VIDES]


class MemoireConversation:
    """Mémoire de DIALOGUE persistante, par conversation. Model-free, souveraine (local), sound, compacte.
    Append-only ; reprise verbatim ; rappel idf non borné par le contexte ; scope public/privé ; effacement RGPD."""

    def __init__(self, racine: str | None = _DOSSIER):
        self.racine = racine                      # dossier de persistance ; None = mémoire volatile (tests)
        self.tours: dict[str, list[dict]] = {}    # conv_id -> [ {seq, role, texte, ts} ... ] (ordre chronologique)
        self.scope: dict[str, str] = {}           # conv_id -> "prive" | "public"
        self._index: dict[str, list[tuple[str, int]]] = {}   # token -> [(conv_id, seq), ...] (inversé, reconstruit)
        self._ndocs = 0                           # nombre total de tours indexés (pour l'idf)
        self.charge()

    # ————————————————————————————————— persistance (durable, append-only) —————————————————————————————————
    @staticmethod
    def _nom_fichier(conv_id: str, scope: str) -> str:
        # le scope est encodé dans le nom -> on connaît la frontière public/privé sans relire le contenu.
        return f"{scope}__{normalise(conv_id).replace(' ', '_') or 'sans_nom'}.jsonl"

    def charge(self) -> int:
        """Recharge toutes les conversations du dossier (offline) et reconstruit l'index inversé. Dossier absent
        -> mémoire vide (aucun effet). Reconstruire l'index au chargement reste LINÉAIRE et compact."""
        if not self.racine or not os.path.isdir(self.racine):
            return 0
        for nom in sorted(os.listdir(self.racine)):
            if not nom.endswith(".jsonl") or "__" not in nom:
                continue
            scope = nom.split("__", 1)[0]
            if scope not in _SCOPES:
                continue
            conv_id = None
            with open(os.path.join(self.racine, nom), encoding="utf-8") as fh:
                for brut in fh:
                    brut = brut.strip()
                    if not brut:
                        continue
                    obj = json.loads(brut)
                    conv_id = obj["conv"]
                    self.tours.setdefault(conv_id, []).append(
                        {"seq": obj["seq"], "role": obj["role"], "texte": obj["texte"], "ts": obj["ts"]})
            if conv_id is not None:
                self.scope[conv_id] = scope
        self._reindexe()
        return len(self.tours)

    def _ajoute_index(self, conv_id: str, tour: dict) -> None:
        seen = set()
        for tok in _tokens(tour["texte"]):
            if tok in seen:
                continue                          # un token compte UNE fois par tour (df = nb de tours, pas d'occur.)
            seen.add(tok)
            self._index.setdefault(tok, []).append((conv_id, tour["seq"]))
        self._ndocs += 1

    def _reindexe(self) -> None:
        self._index = {}
        self._ndocs = 0
        for conv_id, tours in self.tours.items():
            for tour in tours:
                self._ajoute_index(conv_id, tour)

    # ————————————————————————————————— RÉTENTION (déposer un tour) —————————————————————————————————
    def ajoute(self, conv_id: str, role: str, texte: str, ts: float | None = None,
               scope: str = "prive") -> int:
        """Dépose un TOUR (role ∈ libre, typiquement 'user'/'ia') dans la conversation. Append durable + index.
        Renvoie le numéro de séquence (croissant par conversation). Texte vide -> ignoré (renvoie -1)."""
        if not str(conv_id).strip():
            raise ValueError("conv_id obligatoire")
        if scope not in _SCOPES:
            raise ValueError(f"scope inconnu : {scope!r} (attendu {_SCOPES})")
        if not texte or not str(texte).strip():
            return -1                             # garde-fou : jamais de tour vide
        if conv_id in self.scope and self.scope[conv_id] != scope:
            raise ValueError(f"scope incohérent pour {conv_id!r} : {self.scope[conv_id]!r} vs {scope!r}")
        lst = self.tours.setdefault(conv_id, [])
        self.scope.setdefault(conv_id, scope)
        seq = lst[-1]["seq"] + 1 if lst else 0
        tour = {"seq": seq, "role": str(role), "texte": str(texte), "ts": time.time() if ts is None else float(ts)}
        lst.append(tour)
        self._ajoute_index(conv_id, tour)
        self._persiste(conv_id, tour)
        return seq

    def _persiste(self, conv_id: str, tour: dict) -> None:
        if not self.racine:
            return
        os.makedirs(self.racine, exist_ok=True)
        chemin = os.path.join(self.racine, self._nom_fichier(conv_id, self.scope[conv_id]))
        with open(chemin, "a", encoding="utf-8") as fh:    # APPEND-ONLY : on n'écrase jamais le passé
            fh.write(json.dumps({"conv": conv_id, **tour}, ensure_ascii=False) + "\n")

    # ————————————————————————————————— REPRISE (rejouer, verbatim) —————————————————————————————————
    def reprend(self, conv_id: str, n: int | None = None) -> list[dict]:
        """Les tours d'une conversation, dans l'ordre (VERBATIM). `n` = ne garder que les n DERNIERS (fenêtre de
        reprise bornée, à coût constant même si l'historique est immense). Conversation inconnue -> []."""
        lst = self.tours.get(conv_id, [])
        return list(lst) if n is None else lst[-n:] if n > 0 else []

    def conversations(self, scope: str | None = None) -> list[str]:
        """Identifiants connus (optionnellement filtrés par scope), triés."""
        return sorted(c for c in self.tours if scope is None or self.scope.get(c) == scope)

    # ————————————————————————————————— RAPPEL (non borné par le contexte) —————————————————————————————————
    def rappelle(self, requete: str, conv_id: str | None = None, k: int = 5,
                 scope: str | None = None) -> list[dict]:
        """Les k tours les PLUS PERTINENTS pour `requete`, sans recharger tout l'historique (index inversé +
        score idf). `conv_id` donné = dans cette conversation seulement ; None = dans TOUTES (dépôt-pour-le-suivant,
        cross-agent). `scope` filtre public/privé (par défaut, si conv_id=None, on NE cherche que le 'public' pour
        ne pas fuiter le privé ; passer scope='prive' explicitement pour fouiller ses propres conversations privées).
        SOUND : ne renvoie qu'un tour partageant ≥1 token DISCRIMINANT (hors mots-vides) ; sinon rien. Jamais d'invention.
        Chaque résultat = {conv, seq, role, texte, ts, score} (le tour réel, augmenté de son score)."""
        toks = set(_tokens(requete))
        if not toks:
            return []
        # frontière public/privé : recherche globale -> public uniquement par défaut (anti-fuite).
        if scope is None and conv_id is None:
            scope = "public"
        scores: dict[tuple[str, int], float] = {}
        n = max(self._ndocs, 1)
        for tok in toks:
            postings = self._index.get(tok)
            if not postings:
                continue
            idf = math.log(1.0 + n / len(postings))   # idf LISSÉ : toujours >0 pour un terme présent (même rare en
            #                                            petit corpus) ; un terme fréquent pèse moins. La soundness
            #                                            « pas de match sur du bruit » est portée par les mots-vides.
            for (c, seq) in postings:
                if conv_id is not None and c != conv_id:
                    continue
                if scope is not None and self.scope.get(c) != scope:
                    continue
                scores[(c, seq)] = scores.get((c, seq), 0.0) + idf
        if not scores:
            return []
        # tri par score décroissant, puis récence (ts) décroissante en départage -> le plus récent gagne à égalité.
        ordre = sorted(scores.items(), key=lambda kv: (-kv[1], -self._ts(kv[0])))
        out = []
        for (c, seq), sc in ordre[:k]:
            tour = self._tour(c, seq)
            if tour is not None:
                out.append({"conv": c, **tour, "score": round(sc, 4)})
        return out

    def _tour(self, conv_id: str, seq: int) -> dict | None:
        for t in self.tours.get(conv_id, []):
            if t["seq"] == seq:
                return t
        return None

    def _ts(self, cle: tuple[str, int]) -> float:
        t = self._tour(*cle)
        return t["ts"] if t else 0.0

    # ————————————————————————————————— RGPD : droit à l'effacement —————————————————————————————————
    def oublie(self, conv_id: str) -> bool:
        """Efface INTÉGRALEMENT une conversation : mémoire + index + fichier disque. Effacement réel (RGPD), pas un
        drapeau. Renvoie True si quelque chose a été supprimé. Souverain : la donnée n'a jamais quitté la machine."""
        if conv_id not in self.tours:
            return False
        scope = self.scope.get(conv_id, "prive")
        del self.tours[conv_id]
        self.scope.pop(conv_id, None)
        self._reindexe()                          # l'index purge les postings de cette conversation
        if self.racine:
            chemin = os.path.join(self.racine, self._nom_fichier(conv_id, scope))
            if os.path.exists(chemin):
                # Le nom de fichier peut être PARTAGÉ par plusieurs conv_id qui collisionnent après normalise()
                # (« test-1 » et « test 1 » -> prive__test_1.jsonl). N'effacer sur disque QUE les lignes de ce
                # conv_id (effacement RGPD réel) ; ne supprimer le fichier que s'il ne reste aucune autre
                # conversation. Réécriture ATOMIQUE (tmp + os.replace) -> jamais de fichier tronqué.
                reste = False
                fd, tmp = tempfile.mkstemp(dir=self.racine, suffix=".tmp")
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as out, \
                            open(chemin, encoding="utf-8") as fh:
                        for brut in fh:
                            s = brut.strip()
                            if not s:
                                continue
                            if json.loads(s).get("conv") == conv_id:
                                continue           # la ligne à oublier -> jetée (n'est PAS réécrite)
                            out.write(brut if brut.endswith("\n") else brut + "\n")
                            reste = True
                    if reste:
                        os.replace(tmp, chemin)    # il reste d'AUTRES conversations dans ce fichier
                    else:
                        os.remove(tmp)
                        os.remove(chemin)          # plus aucune ligne -> le fichier partagé peut disparaître
                except BaseException:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                    raise
        return True

    # ————————————————————————————————— stats —————————————————————————————————
    def __len__(self) -> int:
        return sum(len(v) for v in self.tours.values())


# Singleton « live » persistant (le dossier datasets/conversations sert l'IA en marche). Les tests passent leur
# propre `racine` temporaire pour ne pas polluer ce dossier.
MEMOIRE = MemoireConversation()


def ajoute(conv_id: str, role: str, texte: str, scope: str = "prive") -> int:
    return MEMOIRE.ajoute(conv_id, role, texte, scope=scope)


def reprend(conv_id: str, n: int | None = None) -> list[dict]:
    return MEMOIRE.reprend(conv_id, n)


def rappelle(requete: str, conv_id: str | None = None, k: int = 5, scope: str | None = None) -> list[dict]:
    return MEMOIRE.rappelle(requete, conv_id, k, scope)


if __name__ == "__main__":
    from garde_ressources import borne
    borne()
    print("=== MÉMOIRE DE CONVERSATION (sound, souveraine, non bornée par le contexte) ===\n")
    m = MemoireConversation(racine=None)          # démo en mémoire (pas de disque)
    # Agent A règle un bug à « 14h » dans sa conversation, scope PUBLIC (déposé pour les suivants).
    m.ajoute("agentA-2026", "user", "le build casse avec 'ELIFECYCLE' sur npm run build, comment régler ?", scope="public")
    m.ajoute("agentA-2026", "ia", "supprime node_modules et package-lock puis réinstalle : npm ci règle le ELIFECYCLE", scope="public")
    # bruit : 1000 tours sans rapport, pour montrer que le rappel n'est PAS bloqué par la taille de l'historique.
    for i in range(1000):
        m.ajoute("agentA-2026", "user", f"question sans rapport numero {i} sur la couleur du ciel et les nuages", scope="public")
    # Agent B, 5 min plus tard, ailleurs : il CHERCHE D'ABORD au lieu de re-galérer 20 min.
    res = m.rappelle("npm run build ELIFECYCLE qui casse", k=2)
    print(f"  Agent B cherche 'ELIFECYCLE' parmi {len(m)} tours -> {len(res)} tour(s) pertinent(s) :")
    for r in res:
        print(f"    [{r['role']}] {r['texte'][:70]}…  (score {r['score']})")
    # Soundness : une requête sans rapport ne ramène RIEN (pas d'invention).
    print("\n  Rappel sans rapport ('recette de tarte aux pommes') ->", m.rappelle("recette de tarte aux pommes", k=3))
    # Reprise verbatim (fenêtre des 2 derniers tours).
    print("  Reprise (2 derniers tours) ->", [t["texte"][:30] for t in m.reprend("agentA-2026", n=2)])
    # RGPD : effacement réel.
    print("  oublie(agentA) ->", m.oublie("agentA-2026"), "| tours restants :", len(m))
