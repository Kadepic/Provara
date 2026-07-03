"""
SUBSTRAT-RÉEL — découverte d'inventions par TRANSDUCTION PHYSIQUE (vers l'objectif « inventions qui
changent le monde », cf. [[project-ia-objectif-final-inventions]]).

Idée (anti-LLM, sound par construction) : un PRINCIPE physique transduit une GRANDEUR en une autre
(lumière→électricité = photovoltaïque ; électricité→lumière = LED ; pression→électricité = piézo ; …).
Une CHAÎNE de principes dont les grandeurs s'enchaînent (sortie de l'un = entrée du suivant) réalise une
transduction entrée→sortie : c'est un CONCEPT DE DISPOSITIF **physiquement cohérent**, et cette cohérence
est VÉRIFIABLE PAR CONSTRUCTION (le juge = la compatibilité des grandeurs sur le graphe — déterministe).

Le moteur tranche une cible (grandeur_entrée -> grandeur_sortie) :
  • EXISTE_DEJA      — une chaîne réalisant la cible correspond à un dispositif déjà connu.
  • INVENTION        — il existe une chaîne cohérente NOUVELLE (absente des dispositifs connus) -> on
                       fournit LES PRINCIPES À COMBINER (les éléments à construire).
  • BRIQUE_MANQUANTE — aucune chaîne ne relie entrée à sortie = il manque un PRINCIPE (invention profonde).

HONNÊTETÉ (la borne) : on juge la COHÉRENCE DE TRANSDUCTION (chaque maillon est un effet réel, les
grandeurs s'enchaînent) et la NOUVEAUTÉ vs le connu. On NE JUGE PAS l'efficacité, les magnitudes, ni la
faisabilité d'ingénierie — c'est explicitement signalé « concept à évaluer ». « sûr avant rapide » :
jamais d'affirmation qu'un dispositif « marche » ; seulement qu'il est cohérent et nouveau.
"""
from __future__ import annotations

import dataclasses

EXISTE_DEJA = "existe_deja"
INVENTION = "invention"
BRIQUE_MANQUANTE = "brique_manquante"

# PRINCIPES physiques RÉELS : (nom, grandeur_entrée, grandeur_sortie, effet). Inventaire de l'existant.
# Chaque entrée est un effet physique NOMMÉ et avéré (la « réalité » du substrat = cette curation).
TRANSDUCTEURS = [
    # — électricité ↔ lumière / mécanique / acoustique / RF / chimie (le cœur historique) —
    ("photovoltaïque", "lumiere", "electricite", "effet photovoltaïque (cellule solaire)"),
    ("LED", "electricite", "lumiere", "électroluminescence (diode)"),
    ("Seebeck", "chaleur", "electricite", "effet thermoélectrique (Seebeck)"),
    ("Peltier", "electricite", "chaleur", "effet thermoélectrique inverse (Peltier)"),
    ("piézo direct", "pression", "electricite", "effet piézoélectrique direct"),
    ("piézo inverse", "electricite", "pression", "effet piézoélectrique inverse"),
    ("dynamo", "mouvement", "electricite", "induction électromagnétique (générateur)"),
    ("moteur", "electricite", "mouvement", "force de Laplace (moteur électrique)"),
    ("haut-parleur", "electricite", "son", "transduction électroacoustique"),
    ("microphone", "son", "electricite", "transduction acoustoélectrique"),
    ("antenne émission", "electricite", "radio", "rayonnement électromagnétique"),
    ("antenne réception", "radio", "electricite", "induction par onde radio"),
    ("pile", "chimie", "electricite", "réaction électrochimique (pile)"),
    ("électrolyse", "electricite", "chimie", "réaction électrochimique forcée"),
    ("incandescence", "chaleur", "lumiere", "rayonnement thermique (corps incandescent)"),
    # — magnétisme : grandeur ajoutée (couple Ampère/Faraday + force magnétique) —
    ("électroaimant", "electricite", "magnetisme", "champ magnétique créé par un courant (Ampère)"),
    ("induction (Faraday)", "magnetisme", "electricite", "f.é.m. par variation de flux (Faraday)"),
    ("force magnétique", "magnetisme", "mouvement", "attraction/répulsion magnétique"),
    # — chimie ↔ chaleur / lumière (combustion, photochimie, chimiluminescence) —
    ("combustion", "chimie", "chaleur", "réaction exothermique (combustion)"),
    ("thermolyse", "chaleur", "chimie", "dissociation thermique (réaction endothermique)"),
    ("photochimie", "lumiere", "chimie", "réaction photochimique (photosynthèse, photographie)"),
    ("chimiluminescence", "chimie", "lumiere", "émission lumineuse par réaction chimique"),
    # — couplages thermo-acoustiques / acousto-optiques avérés (effets connus) —
    ("thermoacoustique", "chaleur", "son", "moteur thermoacoustique (oscillation entretenue)"),
    ("sonoluminescence", "son", "lumiere", "émission lumineuse par cavitation acoustique"),
    ("photoacoustique", "lumiere", "son", "effet photoacoustique (échauffement périodique → son, photophone de Bell)"),
    # — magnéto-thermique / magnéto-mécanique avérés —
    ("magnétocalorique", "magnetisme", "chaleur", "effet magnétocalorique (réfrigération magnétique)"),
    ("magnétostriction", "magnetisme", "pression", "déformation d'un matériau sous champ magnétique"),
    # — GRAVITÉ : produit du mouvement (chute / hydro) mais on ne sait PAS la SYNTHÉTISER (pas d'arête
    #   entrante) — fait physique honnête : « antigravité » = la vraie brique manquante (X → gravite). —
    ("chute", "gravite", "mouvement", "énergie potentielle → cinétique (chute, barrage hydroélectrique)"),
    ("colonne hydrostatique", "gravite", "pression", "poids d'une colonne de fluide → pression (hydrostatique)"),
    # — NUCLÉAIRE : source-only réel (on ne synthétise pas l'énergie de liaison à la demande) —
    ("fission", "nucleaire", "chaleur", "fission/fusion nucléaire → chaleur (réacteur)"),
    ("bêtavoltaïque", "nucleaire", "electricite", "conversion directe du rayonnement bêta (pile nucléaire)"),
    ("radioluminescence", "nucleaire", "lumiere", "scintillation sous rayonnement (tritium luminescent)"),
    # — COUPLAGES MÉCANIQUES / THERMO avérés (2026-06-22 nuit) : nouvelles ARÊTES = plus de chaînes
    #   d'invention. `pression→chaleur` (compression adiabatique) VOLONTAIREMENT omis : il créerait un
    #   chemin pression→chaleur→lumiere (incandescence) concurrent de piézo+LED — non nécessaire ici. —
    ("moteur thermique", "chaleur", "mouvement", "détente d'un gaz chaud → travail (moteur à combustion/vapeur, Stirling)"),
    ("pompe", "mouvement", "pression", "travail mécanique → pression d'un fluide (pompe, compresseur)"),
    ("actionneur fluidique", "pression", "mouvement", "détente sous pression → travail (vérin pneumatique, turbine à vapeur)"),
    ("dilatation thermique", "chaleur", "pression", "hausse de pression d'un gaz chauffé à volume constant (Gay-Lussac)"),
    # — COUPLAGES avérés supplémentaires (2026-06-23, 2e passe) : encore des arêtes réelles —
    ("vibration", "mouvement", "son", "vibration mécanique → onde acoustique (corde, membrane, frottement)"),
    ("radiation acoustique", "son", "mouvement", "force de radiation acoustique (lévitation/poussée par ultrasons)"),
    ("actionneur chimique", "chimie", "mouvement", "réaction → travail mécanique (muscle/ATP, propulsion par gaz)"),
    ("dégagement gazeux", "chimie", "pression", "réaction produisant un gaz → pression (airbag, effervescence)"),
    ("pression de radiation", "lumiere", "pression", "quantité de mouvement des photons → pression (voile solaire)"),
    # — DISSIPATION (2e principe) : toute forme d'énergie dégénère en chaleur (puits universel) —
    ("frottement", "mouvement", "chaleur", "dissipation par friction (2e principe)"),
    ("effet Joule", "electricite", "chaleur", "dissipation résistive (effet Joule)"),
    ("absorption", "lumiere", "chaleur", "absorption du rayonnement (corps noir)"),
    ("amortissement", "son", "chaleur", "dissipation visqueuse de l'onde acoustique"),
    ("diélectrique RF", "radio", "chaleur", "absorption diélectrique (chauffage micro-ondes)"),
]

# DISPOSITIFS CONNUS — chaînes MULTI-MAILLONS déjà incarnées par un objet courant. (Les chaînes à UN
# maillon = un principe unique réel : connues par construction, gérées par `_connus()`, pas listées ici.)
# La NOUVEAUTÉ d'une COMBINAISON se mesure contre cet ensemble.
DISPOSITIFS_CONNUS = {
    ("mouvement", "electricite", "lumiere"),          # lampe-dynamo (torche à manivelle)
    ("son", "electricite", "radio"),                  # émetteur radio
    ("radio", "electricite", "son"),                  # récepteur radio
    ("chimie", "electricite", "lumiere"),             # lampe de poche à pile (pile → LED)
    ("mouvement", "electricite", "magnetisme"),       # alternateur → électroaimant (atelier)
    ("gravite", "mouvement", "electricite"),          # barrage hydroélectrique (chute → dynamo)
    ("nucleaire", "chaleur", "electricite"),          # centrale nucléaire (fission → thermoélectrique/turbine)
}

GRANDEURS = sorted({g for _, e, s, _ in TRANSDUCTEURS for g in (e, s)} | {"gravite"})


def _connus() -> set:
    """L'ensemble des transductions CONNUES = les dispositifs multi-maillons curés (DISPOSITIFS_CONNUS)
    UNION toutes les arêtes directes (un principe unique = un effet réel déjà connu, donc PAS une
    invention). Centralise la notion de « connu » pour le triage et les invariants."""
    return set(DISPOSITIFS_CONNUS) | {(e, s) for _, e, s, _ in TRANSDUCTEURS}


@dataclasses.dataclass(frozen=True)
class Concept:
    statut: str
    entree: str
    sortie: str
    chaine: tuple = ()          # suite de noms de principes (les éléments à combiner)
    grandeurs: tuple = ()       # suite de grandeurs traversées (entree … sortie)
    justification: str = ""

    def __str__(self) -> str:
        fleche = " → ".join(self.grandeurs) if self.grandeurs else f"{self.entree} → {self.sortie}"
        if self.statut == INVENTION:
            return (f"[INVENTION] {self.entree} → {self.sortie}\n      principes à combiner : "
                    f"{' + '.join(self.chaine)}\n      transduction : {fleche}\n      ({self.justification})")
        if self.statut == EXISTE_DEJA:
            return f"[EXISTE DÉJÀ] {self.entree} → {self.sortie} ({fleche}) — dispositif connu"
        return f"[BRIQUE MANQUANTE] {self.entree} → {self.sortie} — {self.justification}"


def _graphe():
    """grandeur -> [(grandeur_suivante, nom_principe)]."""
    g: dict = {}
    for nom, e, s, _ in TRANSDUCTEURS:
        g.setdefault(e, []).append((s, nom))
    return g


def chaines(entree: str, sortie: str, max_len: int = 4):
    """Toutes les chaînes SIMPLES (sans répéter une grandeur) reliant entree->sortie, longueur <= max_len
    transductions. Chaque chaîne = (principes, grandeurs). Le juge de cohérence est STRUCTUREL : par
    construction chaque maillon a sortie == entrée du suivant."""
    g = _graphe()
    res = []

    def dfs(courant, vus_grandeurs, principes):
        if len(principes) > max_len:
            return
        if courant == sortie and principes:
            res.append((tuple(principes), tuple(vus_grandeurs)))
            return
        for (suiv, nom) in g.get(courant, []):
            if suiv in vus_grandeurs:                 # chaîne simple : pas de cycle de grandeur
                continue
            dfs(suiv, vus_grandeurs + [suiv], principes + [nom])

    if entree in GRANDEURS:
        dfs(entree, [entree], [])
    # trie par longueur (concept le plus simple d'abord)
    res.sort(key=lambda c: len(c[0]))
    return res


def _coherente(grandeurs) -> bool:
    """VÉRIFIE qu'une chaîne de grandeurs est une transduction valide : chaque transition existe dans le KB."""
    aretes = {(e, s) for _, e, s, _ in TRANSDUCTEURS}
    return all((grandeurs[i], grandeurs[i + 1]) in aretes for i in range(len(grandeurs) - 1))


def examine(entree: str, sortie: str, max_len: int = 4) -> Concept:
    """Tranche la cible (grandeur entree -> grandeur sortie) : EXISTE_DEJA / INVENTION / BRIQUE_MANQUANTE."""
    cs = chaines(entree, sortie, max_len)
    if not cs:
        return Concept(BRIQUE_MANQUANTE, entree, sortie,
                       justification="aucune chaîne de principes connus ne relie ces grandeurs : un principe neuf est requis")
    connus = _connus()
    # 1) une chaîne est-elle CONNUE ? -> EXISTE_DEJA (le plus simple connu). Inclut tout principe UNIQUE
    #    (longueur 1) : un effet physique avéré n'est PAS une invention (garde anti-fausse-invention).
    for principes, grandeurs in cs:
        if grandeurs in connus:
            return Concept(EXISTE_DEJA, entree, sortie, chaine=principes, grandeurs=grandeurs)
    # 2) sinon : la COMBINAISON cohérente la PLUS SIMPLE et NOUVELLE (≥2 maillons) = concept d'invention.
    for principes, grandeurs in cs:
        if grandeurs not in connus and _coherente(grandeurs):
            return Concept(INVENTION, entree, sortie, chaine=principes, grandeurs=grandeurs,
                           justification="chaîne de transduction cohérente et nouvelle — concept à évaluer "
                                         "(efficacité/magnitudes non jugées)")
    # filet (ne devrait pas arriver : cs non vide implique au moins une chaîne)
    return Concept(BRIQUE_MANQUANTE, entree, sortie, justification="aucune chaîne nouvelle cohérente")


def _atteignables(extra=None) -> set:
    """Ensemble des paires (entrée, sortie) reliables par une chaîne de principes, en option AVEC une
    arête hypothétique `extra=(a,b)`. Pure reachability sur le graphe des grandeurs (déterministe)."""
    aretes: dict = {}
    for _, e, s, _ in TRANSDUCTEURS:
        aretes.setdefault(e, set()).add(s)
    if extra:
        aretes.setdefault(extra[0], set()).add(extra[1])
    paires = set()
    for depart in GRANDEURS:
        vus = set()
        pile = [depart]
        while pile:
            g = pile.pop()
            for suiv in aretes.get(g, ()):
                if suiv not in vus:
                    vus.add(suiv)
                    pile.append(suiv)
        for cible in vus:
            if cible != depart:
                paires.add((depart, cible))
    return paires


def lacunes_prioritaires(k: int = 5):
    """Classe les PRINCIPES MANQUANTS (transitions de grandeur sans transducteur) par LEVIER : combien de
    transductions aujourd'hui inatteignables seraient débloquées si ce principe existait. Répond, de façon
    SOUND (reachability), à « quel principe physique serait le plus précieux à inventer ? »."""
    base = _atteignables()
    aretes_existantes = {(e, s) for _, e, s, _ in TRANSDUCTEURS}
    scores = []
    for a in GRANDEURS:
        for b in GRANDEURS:
            if a == b or (a, b) in aretes_existantes:
                continue
            gain = len(_atteignables(extra=(a, b)) - base)
            if gain > 0:
                scores.append((gain, a, b))
    scores.sort(key=lambda t: (-t[0], t[1], t[2]))
    return scores[:k]


if __name__ == "__main__":
    from garde_ressources import borne
    borne()
    print("=== SUBSTRAT-RÉEL : invention par transduction physique (cohérent + nouveau, jugé sound) ===\n")
    CIBLES = [
        ("lumiere", "electricite"),    # existe déjà (cellule solaire)
        ("mouvement", "lumiere"),      # existe déjà (lampe-dynamo)
        ("son", "lumiere"),            # existe déjà (sonoluminescence : principe unique avéré)
        ("pression", "lumiere"),       # concept : piézo → LED (pression qui éclaire)
        ("chaleur", "radio"),          # concept : Seebeck → antenne (balise radio thermo-alimentée)
        ("lumiere", "son"),            # existe déjà (effet photoacoustique : principe unique avéré)
        ("magnetisme", "lumiere"),     # concept (grandeur ajoutée) : induction → LED
        ("son", "gravite"),            # brique manquante (aucun principe ne produit la gravité)
    ]
    for e, s in CIBLES:
        print("  " + str(examine(e, s)) + "\n")

    print("PRINCIPES MANQUANTS LES PLUS PRÉCIEUX À INVENTER (levier = capacités débloquées) :")
    for gain, a, b in lacunes_prioritaires(6):
        print(f"    ★ un principe {a} → {b} débloquerait {gain} transduction(s)")
