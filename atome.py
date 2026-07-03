"""
CONTRAT D'ATOME — l'unité universelle de connaissance de l'IA (borné ET non-borné), FAUX=0 (2026-07-02, durci).

VISION (Yohan) : « tout ce qui existe » — sujets, contextes, visions, éléments — est un ATOME que l'IA doit apprendre.
Le borné s'apprend comme FAIT ; le non-borné comme SUPPOSITION cadrée (pas une abstention, une réponse). Et « une
invention est une supposition qui a survécu à la réalité » : le statut d'un atome ÉVOLUE (supposition -> fait si un
juge réel valide ; fait -> réfuté/périmé sinon). Ce module est le contrat unique qui rend tout ça FAUX=0.

L'ASYMÉTRIE qui EST tout le jeu (sans elle « ma supposition devient vraie » = hallucination des LLM) :
  • SUPPOSER : sans limite. On peut supposer au-delà du réel — la seule façon d'inventer.
  • PROMOUVOIR supposition -> FAIT : SEULEMENT via un JUGE RÉEL, matérialisé par un objet `Verdict` (juge nommé +
    trace de confrontation). `promeut()`/`atteste()` n'acceptent PAS un booléen ni une chaîne nue — il faut un Verdict.

LIMITE HONNÊTE (assumée) : un contrat de DONNÉES en Python ne peut pas PROUVER qu'un Verdict vient d'un vrai juge (on
peut toujours fabriquer un faux Verdict). Ce qu'il garantit : la création d'un fait est EXPLICITE, TYPÉE et TRAÇABLE
(le juge apparaît dans la provenance) — jamais accidentelle, jamais par un bool/str anonyme. La discipline (n'appeler
promeut/atteste qu'avec le Verdict d'un vrai juge : coherence_physique, falsification, un test held-out, le lecteur)
reste à la charge de l'appelant ; le contrat rend toute triche visible. `frozen` n'est PAS une frontière de sécurité
(object.__setattr__ contourne tout frozen) : les lectures critiques REVALIDENT les invariants (défense en profondeur).

INVARIANTS FAUX=0 (imposés à la construction ET revalidés à la lecture) :
  • Rien n'est servi sans PORTÉE, et `sert()` expose TOUJOURS statut+portée+confiance (un fait hors portée EST un faux).
  • FAIT / CONVENTION => confiance == 1.0, preuve signifiante, régime vide ; CONVENTION => portée référentielle.
  • SUPPOSITION => 0 < confiance < 1 (jamais 1.00 ni 0.00, même à l'affichage) + régime (dérivable/génératif) + base.
  • RÉFUTÉ => confiance == 0.0 + preuve ; le contenu réfuté est une GARDE : on ne le re-promeut jamais (sauf rouvre()).
Souverain, stdlib pur, déterministe (timestamps passés en paramètre, jamais lus de l'horloge -> testable).
"""
from __future__ import annotations

import dataclasses
import unicodedata

# ── STATUT (axe épistémique) ──
FAIT = "fait"
CONVENTION = "convention"
SUPPOSITION = "supposition"
REFUTE = "refute"
_STATUTS = frozenset({FAIT, CONVENTION, SUPPOSITION, REFUTE})

# ── RÉGIME (pour distinguer deux suppositions qu'il ne faut JAMAIS confondre) ──
DERIVABLE = "derivable"        # déjà vrai dans le réel, non explicité (découverte de l'implicite)
GENERATIF = "generatif"        # pas encore réel — invention à construire/confronter (la vraie invention)
RAPPORTE = "rapporte"          # info sourcée (web/veille) à vérifier — matière à supposition
_REGIMES_SUPPOSITION = frozenset({DERIVABLE, GENERATIF, RAPPORTE})

# ── TYPE DE PORTÉE ──
UNIVERSEL = "universel"        # tautologie / vérité logique (rare — jamais par facilité)
DOMAINE = "domaine"
REFERENTIEL = "referentiel"
TEMPOREL = "temporel"
ECHELLE = "echelle"
EPISTEMIQUE = "epistemique"
_TYPES_PORTEE = frozenset({UNIVERSEL, DOMAINE, REFERENTIEL, TEMPOREL, ECHELLE, EPISTEMIQUE})


# ─────────── helpers preuve / contenu ───────────
def _norm_preuve(s) -> str:
    """Normalise une preuve : NFKC, retrait des caractères de contrôle et de format INVISIBLES (Cc/Cf, dont
    U+200B zero-width, U+FEFF), compactage des blancs. Une preuve doit être un contenu SIGNIFIANT, pas un blanc déguisé."""
    if not isinstance(s, str):
        raise ValueError("preuve/base doit être une chaîne")
    s = unicodedata.normalize("NFKC", s)
    s = "".join(c for c in s if unicodedata.category(c) not in ("Cc", "Cf"))
    return " ".join(s.split())


def _est_preuve_valide(s) -> bool:
    try:
        return len(_norm_preuve(s)) >= 3
    except ValueError:
        return False


def _contenu_valide(contenu) -> bool:
    if contenu is None:
        return False
    if isinstance(contenu, str) and not contenu.strip():
        return False
    return True


def _cle_contenu(contenu) -> str:
    """Clé stable d'un contenu pour la garde anti-re-proposition (repr normalisé)."""
    return " ".join(repr(contenu).split()).lower()


def _fmt_conf(c: float) -> str:
    """Affiche la confiance SANS mentir : une supposition (0<c<1) n'affiche jamais 1.00 ni 0.00 par arrondi."""
    r = round(c, 2)
    if 0.0 < c < 1.0 and (r >= 1.0 or r <= 0.0):
        return f"{c:.4f}".rstrip("0")
    return f"{c:.2f}"


# ── GARDE anti-re-proposition : contenus réfutés (état en-mémoire ; la persistance est une couche supérieure) ──
_GARDES_REFUTE: set = set()


def _reset_gardes():
    """Pour les tests : vide la garde anti-re-proposition."""
    _GARDES_REFUTE.clear()


def rouvre(contenu, raison: str) -> None:
    """Lève EXPLICITEMENT la garde sur un contenu réfuté (ré-ouverture tracée — ex. nouvelles preuves). FAUX=0 :
    la ré-ouverture est un acte délibéré, jamais un effet de bord."""
    if not _est_preuve_valide(raison):
        raise ValueError("rouvre() exige une raison signifiante")
    _GARDES_REFUTE.discard(_cle_contenu(contenu))


def est_refute(contenu) -> bool:
    return _cle_contenu(contenu) in _GARDES_REFUTE


# ─────────── PORTÉE ───────────
@dataclasses.dataclass(frozen=True)
class Portee:
    """Domaine de validité borné d'un atome. `condition` décrit concrètement OÙ l'atome tient (jamais « partout »
    implicite). `couvre()` est CONSERVATEUR : au moindre doute (contexte muet/ambigu), il ne couvre PAS."""
    type: str
    condition: str

    def __post_init__(self):
        if self.type not in _TYPES_PORTEE:
            raise ValueError(f"type de portée inconnu : {self.type!r}")
        if not isinstance(self.condition, str) or not self.condition.strip():
            raise ValueError("portée : condition de validité non vide requise (pas de 'vrai partout' implicite)")

    def couvre(self, contexte: dict) -> bool:
        """La portée s'applique-t-elle au `contexte` ? UNIVERSEL couvre tout ; sinon on exige que le contexte AFFIRME
        explicitement la condition — par ÉGALITÉ EXACTE (clé 'portee' == condition, ou 'conditions' = collection
        contenant la condition à l'identique, ou une str ÉGALE). PAS de correspondance de sous-chaîne (un contexte qui
        nie la condition ne doit jamais être jugé couvert). Contexte muet/ambigu -> False."""
        if self.type == UNIVERSEL:
            return True
        if not isinstance(contexte, dict):
            return False
        if contexte.get("portee") == self.condition:
            return True
        conds = contexte.get("conditions")
        if isinstance(conds, (list, set, tuple, frozenset)):
            return self.condition in conds                     # membership EXACT, jamais sous-chaîne
        if isinstance(conds, str):
            return self.condition == conds                     # égalité stricte, jamais `in`
        return False


def _fini_01(x, nom):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} doit être un nombre dans [0,1]")
    x = float(x)
    if x != x or x in (float("inf"), float("-inf")):
        raise ValueError(f"{nom} non fini")
    if not (0.0 <= x <= 1.0):
        raise ValueError(f"{nom} hors [0,1] : {x}")
    return x


# ─────────── VERDICT (trace d'un juge réel — clé de l'asymétrie) ───────────
@dataclasses.dataclass(frozen=True)
class Verdict:
    """Trace d'un JUGE RÉEL ayant confronté un contenu à la réalité. Requis pour créer/promouvoir un FAIT (au lieu
    d'un bool/str anonyme). Ne PROUVE pas la réalité du juge (impossible dans un contrat de données), mais rend la
    création de fait explicite, typée et traçable. `juge` = nom du mécanisme (coherence_physique/falsification/test…)."""
    juge: str
    verdict: bool
    trace: str

    def __post_init__(self):
        if not isinstance(self.juge, str) or not self.juge.strip():
            raise ValueError("Verdict : juge (nom du mécanisme réel) requis")
        if not isinstance(self.verdict, bool):
            raise ValueError("Verdict.verdict doit être un booléen issu d'un juge (pas une valeur ambiguë)")
        if not _est_preuve_valide(self.trace):
            raise ValueError("Verdict : trace de confrontation signifiante requise")

    def preuve(self) -> str:
        return f"{self.juge}: {_norm_preuve(self.trace)}"


# ─────────── ATOME ───────────
@dataclasses.dataclass(frozen=True)
class Atome:
    """Unité universelle : contenu, statut épistémique, portée, confiance, preuve. Immuable : l'ÉVOLUTION se fait en
    produisant un NOUVEL atome (promeut/refute/revise). `frozen` n'est pas une garde de sécurité -> revalidation à la
    lecture (est_servable_comme_fait)."""
    contenu: object
    statut: str
    portee: Portee
    confiance: float
    preuve: str = ""
    regime: str = ""
    provenance: tuple = ()

    def __post_init__(self):
        if self.statut not in _STATUTS:
            raise ValueError(f"statut inconnu : {self.statut!r}")
        if not _contenu_valide(self.contenu):
            raise ValueError("contenu d'atome invalide (None ou vide)")
        if not isinstance(self.portee, Portee):
            raise ValueError("tout atome doit porter une Portee (un fait sans portée est un faux hors champ)")
        c = _fini_01(self.confiance, "confiance")
        preuve_ok = _est_preuve_valide(self.preuve)
        # le RÉGIME est réservé aux suppositions (un fait/convention/réfuté n'a pas de régime de supposition)
        if self.statut == SUPPOSITION:
            if self.regime not in _REGIMES_SUPPOSITION:
                raise ValueError("SUPPOSITION exige un régime (derivable/generatif/rapporte)")
        elif self.regime != "":
            raise ValueError(f"un {self.statut} ne porte pas de régime de supposition (régime doit être vide)")
        # invariants par statut
        if self.statut in (FAIT, CONVENTION):
            if c != 1.0:
                raise ValueError(f"{self.statut} exige confiance == 1.0 (vu {c})")
            if not preuve_ok:
                raise ValueError(f"{self.statut} exige une preuve signifiante")
            if self.statut == CONVENTION and self.portee.type != REFERENTIEL:
                raise ValueError("une CONVENTION est vraie dans un RÉFÉRENTIEL : portée 'referentiel' requise")
        elif self.statut == SUPPOSITION:
            if not (0.0 < c < 1.0):
                raise ValueError(f"SUPPOSITION exige 0 < confiance < 1 (vu {c})")
            if not preuve_ok:
                raise ValueError("SUPPOSITION exige une base signifiante")
        elif self.statut == REFUTE:
            if c != 0.0:
                raise ValueError(f"REFUTE exige confiance == 0.0 (vu {c})")
            if not preuve_ok:
                raise ValueError("REFUTE exige une preuve (ce qui l'invalide) — garde anti-re-proposition")

    def _invariants_ok(self) -> bool:
        """Revalide l'état complet (défense contre une mutation frozen par object.__setattr__)."""
        try:
            Atome(self.contenu, self.statut, self.portee, self.confiance, self.preuve, self.regime)
            return True
        except (ValueError, TypeError):
            return False

    def sert(self, contexte: dict = None) -> str:
        """Rendu accompagné INDISSOCIABLEMENT du statut + portée + confiance (une supposition ne peut jamais être relue
        comme un fait ; un fait est toujours servi avec son domaine de validité). Si `contexte` est fourni et que la
        portée ne le couvre pas, le rendu le SIGNALE (fait hors de sa portée = pas un fait ici)."""
        if not self._invariants_ok():
            return "[ATOME INVALIDE — état incohérent, non servi]"
        portee_txt = f"valable si {self.portee.condition}" if self.portee.type != UNIVERSEL else "universel"
        tete = {
            FAIT: "FAIT",
            CONVENTION: f"CONVENTION[{self.portee.condition}]",
            SUPPOSITION: f"SUPPOSITION({self.regime}, conf={_fmt_conf(self.confiance)})",
            REFUTE: "RÉFUTÉ",
        }[self.statut]
        hors = ""
        if contexte is not None and self.statut in (FAIT, CONVENTION) and not self.portee.couvre(contexte):
            hors = " ⚠ HORS PORTÉE dans ce contexte (donc non affirmable ici)"
        suffixe = "" if self.statut == REFUTE else f" — {portee_txt}"
        return f"[{tete}] {self.contenu}{suffixe}{hors}"

    def est_servable_comme_fait(self, contexte: dict = None) -> bool:
        """True SEULEMENT si : invariants revalidés OK, statut FAIT/CONVENTION à confiance 1.0, ET (si un contexte est
        donné) la portée le couvre. Un fait hors de sa portée n'est PAS servable comme fait."""
        if not self._invariants_ok():
            return False
        if not (self.statut in (FAIT, CONVENTION) and self.confiance == 1.0):
            return False
        if contexte is not None and not self.portee.couvre(contexte):
            return False
        return True


# ─────────── CONSTRUCTEURS ───────────
def atteste(contenu, portee: Portee, verdict: Verdict) -> Atome:
    """Crée un FAIT — exige le VERDICT d'un juge réel (pas une chaîne de preuve arbitraire). Le verdict doit être
    positif. Un contenu réfuté ne peut pas être ré-attesté sans rouvre() explicite (garde anti-blanchiment)."""
    if not isinstance(verdict, Verdict):
        raise ValueError("atteste() exige un Verdict (trace d'un juge réel), pas une preuve nue")
    if not verdict.verdict:
        raise ValueError("atteste() : le juge doit VALIDER (verdict positif) pour créer un fait")
    if est_refute(contenu):
        raise ValueError("contenu RÉFUTÉ : ne pas ré-attester sans rouvre() explicite (garde anti-blanchiment)")
    return Atome(contenu, FAIT, portee, 1.0, preuve=verdict.preuve(),
                 provenance=(f"atteste<-{verdict.juge}",))


def convention(contenu, condition_referentiel: str, source: str) -> Atome:
    """Crée une CONVENTION vraie dans un référentiel nommé, établie par une SOURCE normative (norme/standard/droit).
    Distincte d'un fait empirique : établie par autorité, pas jugée par la réalité ; certaine dans son référentiel."""
    return Atome(contenu, CONVENTION, Portee(REFERENTIEL, condition_referentiel), 1.0, preuve=_norm_preuve(source))


def suppose(contenu, regime: str, portee: Portee, confiance: float, base: str) -> Atome:
    """Crée une SUPPOSITION cadrée — SANS LIMITE sur ce qu'on peut supposer (même un contenu déjà réfuté : supposer
    reste libre ; c'est la PROMOTION qui est gardée). `regime` ∈ {derivable, generatif, rapporte}, `confiance` ∈ ]0,1[."""
    return Atome(contenu, SUPPOSITION, portee, confiance, preuve=_norm_preuve(base) if isinstance(base, str) else base, regime=regime)


# ─────────── TRANSITIONS (évolution — asymétrie stricte) ───────────
def promeut(atome: Atome, verdict: Verdict, *, quand: str = "") -> Atome:
    """SUPPOSITION -> FAIT SEULEMENT via le VERDICT d'un juge réel (objet Verdict, pas un bool). verdict positif ->
    FAIT ; négatif -> RÉFUTÉ (+ garde anti-re-proposition). Sur un non-SUPPOSITION -> ValueError. Un contenu déjà
    réfuté ne peut être promu qu'après rouvre() explicite."""
    if atome.statut != SUPPOSITION:
        raise ValueError("promeut() ne s'applique qu'à une SUPPOSITION")
    if not isinstance(verdict, Verdict):
        raise ValueError("promeut() exige un Verdict (trace d'un juge réel), pas un booléen nu")
    if verdict.verdict and est_refute(atome.contenu):
        raise ValueError("contenu RÉFUTÉ : ne pas re-promouvoir sans rouvre() explicite (garde anti-blanchiment)")
    prov = atome.provenance + (f"{atome.statut}(conf={_fmt_conf(atome.confiance)})->{'fait' if verdict.verdict else 'refute'}<-{verdict.juge}@{quand or '?'}",)
    if verdict.verdict:
        return Atome(atome.contenu, FAIT, atome.portee, 1.0, preuve=verdict.preuve(), provenance=prov)
    _GARDES_REFUTE.add(_cle_contenu(atome.contenu))
    return Atome(atome.contenu, REFUTE, atome.portee, 0.0, preuve=verdict.preuve(), provenance=prov)


def refute(atome: Atome, preuve: str, *, quand: str = "") -> Atome:
    """Tout atome -> RÉFUTÉ (fait périmé/corrigé, supposition invalidée) + garde anti-re-proposition. Idempotent."""
    if not _est_preuve_valide(preuve):
        raise ValueError("réfutation : preuve signifiante requise (ce qui invalide l'atome)")
    prov = atome.provenance + (f"{atome.statut}(conf={_fmt_conf(atome.confiance)})->refute@{quand or '?'}",)
    _GARDES_REFUTE.add(_cle_contenu(atome.contenu))
    return Atome(atome.contenu, REFUTE, atome.portee, 0.0, preuve=_norm_preuve(preuve), regime="", provenance=prov)


def revise_confiance(atome: Atome, nouvelle_confiance: float, base: str, *, quand: str = "") -> Atome:
    """Met à jour la confiance d'une SUPPOSITION (bayésien/conformal). Reste dans ]0,1[ ; atteindre 1.0 n'est PAS une
    auto-promotion (passer par promeut() avec Verdict). ValueError hors ]0,1[."""
    if atome.statut != SUPPOSITION:
        raise ValueError("revise_confiance() ne s'applique qu'à une SUPPOSITION")
    c = _fini_01(nouvelle_confiance, "nouvelle_confiance")
    if not (0.0 < c < 1.0):
        raise ValueError("une supposition reste dans ]0,1[ ; pour la certifier, passer par promeut() (juge réel)")
    prov = atome.provenance + (f"conf {_fmt_conf(atome.confiance)}->{_fmt_conf(c)}@{quand or '?'}",)
    return Atome(atome.contenu, SUPPOSITION, atome.portee, c, preuve=_norm_preuve(base), regime=atome.regime, provenance=prov)
