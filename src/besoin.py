"""
BESOIN / OBJECTIF — couche d'OBJECTIFS pour le moteur d'invention (demande Yohan 2026-07-02 : « il faut tout
construire, c'est comme ça qu'on voit ce qui manque »).

POURQUOI. Le moteur `substrat_physique` raisonne en GRANDEURS d'énergie ; `coherence_physique` juge la faisabilité.
Il manquait la notion de BUT. Or l'avantage de la pensée machine, ce n'est PAS de réfuter les lois (c'est
impossible et ce serait une hallucination) — c'est de ne pas s'ancrer sur la SOLUTION humaine (« climatiseur ») et
de repartir du BESOIN pour peigner, sans biais, l'espace que les lois laissent OUVERT. Cette brique :

  1) DÉCOMPOSE un besoin BORNÉ (dont la physique fixe la structure) en sous-objectifs physiques + leviers, en
     NOMMANT la grandeur à manipuler (pont vers substrat_physique) ;
  2) ÉNUMÈRE des PRINCIPES candidats (dont des effets SOUS-EXPLOITÉS : caloriques magnéto/élasto/électro,
     radiatif, échange direct), chacun servi comme SUPPOSITION (atome, portée + confiance) puis JUGÉ par
     coherence_physique : l'impossible devient RÉFUTÉ, le possible RESTE une supposition (jamais promu en FAIT —
     la cohérence n'est PAS une preuve d'efficacité : l'asymétrie du projet) ;
  3) sur un besoin INCONNU -> HORS : le manque devient VISIBLE (c'est le but du test — « voir ce qui manque »).

FAUX=0. Chaque décomposition est un mécanisme ÉTABLI (les quatre canaux d'échange thermique du corps humain ;
le bilan d'énergie d'une enceinte). On route vers les grandeurs/effets et vers le juge ; on ne prétend JAMAIS
qu'une solution « marche ». LOI STRUCTURANTE rappelée : refroidir = déplacer de la chaleur vers un PUITS extérieur ;
aucun principe ne bat Carnot (COP ≤ Th/(Th−Tc), arbitré par coherence_physique). Les vrais gains viennent de :
(a) réduire la CHARGE (cibler le corps ~100 W, pas l'air de la pièce ~500–1000 W) ; (b) viser un PUITS déjà froid
(ΔT faible → COP élevé) ; (c) empêcher les APPORTS. C'est LÀ que la machine dépasse l'humain, pas en trichant.
"""
from __future__ import annotations

import unicodedata
from collections import namedtuple

import atome as A
import coherence_physique as COH
import substrat_physique as SP

HORS = "hors"

# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  REGISTRE DE DOMAINES (généralisation 2026-07-12 — Yohan « généralise d'abord l'archi »).
#  Le module ne modélisait qu'UN besoin-domaine (refroidissement). La structure — objectif réel + canaux
#  physiques + principes JUGÉS + stratégies naturelles + loi structurante — est la MÊME pour tout besoin
#  borné. On la factorise : un `Domaine` porte ces pièces ; `enregistre` l'ajoute ; les fonctions publiques
#  (decompose/objectif_reel/principes/strategies_naturelles) DISPATCHENT via le registre. Ajouter un domaine
#  = enregistrer un `Domaine`, RIEN d'autre à toucher. Le cooling est le premier domaine enregistré (comportement
#  préservé à l'identique : mêmes constantes, mêmes sorties — vérifié par valide_besoin). FAUX=0 inchangé :
#  les principes restent des SUPPOSITIONS jugées, jamais des faits.
#    `objectif`  : le REFRAMING machine (str).            `canaux`  : leviers physiques (list[Canal]).
#    `principes` : candidats à juger (list[_P]).          `strategies` : exemples naturels (list[_Nature]).
#    `loi`       : la loi structurante (str).             `extras`  : champs de decompose propres au domaine (dict).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
from collections import namedtuple as _nt

Domaine = _nt("Domaine", ["nom", "aliases", "objectif", "canaux", "principes", "strategies", "loi", "extras"])
_DOMAINES: list = []
_INDEX_ALIAS: dict = {}


def enregistre(domaine: "Domaine") -> "Domaine":
    """Ajoute un besoin-domaine au registre (idempotent par nom : ré-enregistrer remplace). Indexe ses alias
    NORMALISÉS pour le dispatch. Renvoie le domaine."""
    global _DOMAINES
    _DOMAINES = [d for d in _DOMAINES if d.nom != domaine.nom] + [domaine]
    for a in domaine.aliases:
        _INDEX_ALIAS[_norm(a)] = domaine
    return domaine


def _domaine(besoin: str):
    """Le domaine dont un alias == besoin normalisé, ou None (besoin non modélisé -> HORS honnête)."""
    return _INDEX_ALIAS.get(_norm(besoin))


def domaines_connus() -> list[str]:
    """Les noms des besoins-domaines modélisés (introspection : « ce que le moteur sait inventer »)."""
    return [d.nom for d in _DOMAINES]


# ── Canaux d'échange thermique du corps humain (physiologie établie) ────────────────────────────────────────────
# canal, grandeur (substrat_physique), levier qui AUGMENTE la perte de chaleur du corps, silencieux, note honnête.
Canal = namedtuple("Canal", ["canal", "grandeur", "levier", "silencieux", "note"])

_CANAUX_CORPS = [
    Canal("rayonnement", "chaleur", "offrir une SURFACE FROIDE (température radiante moyenne basse) : sol/panneau frais",
          True, "part dominante en air calme ; aucun mouvement d'air -> silencieux ; surveiller le point de rosée"),
    Canal("conduction", "chaleur", "CONTACT avec une masse fraîche (assise/plan/sol frais, poignets/nuque)",
          True, "très efficace localement pour peu d'énergie (petite surface, cible le corps)"),
    Canal("convection", "chaleur", "AIR plus frais OU mouvement d'air sur la peau",
          False, "le mouvement d'air exige un ventilateur = BRUIT ; refroidir l'air exige de pomper beaucoup de chaleur"),
    Canal("evaporation", "chaleur", "AIR plus SEC (déshumidification) ou air sur peau humide",
          True, "humidifier la pièce (rafraîchisseur évaporatif fermé) est CONTRE-PRODUCTIF : l'humidité s'accumule"),
]

# Le besoin « rafraîchir » et ses formulations -> une même décomposition bornée (CONFORT HUMAIN).
# On garde des libellés QUALIFIÉS ; on écarte les libellés nus ambigus (« refroidissement », « confort thermique »
# seuls) qui pourraient viser un autre domaine (refroidir un CPU, des aliments) -> HORS honnête plutôt que servir
# une décomposition de confort humain hors sujet.
_COOL = "rafraichissement_confort"
_ALIAS_COOL = {
    "rafraichir une piece", "rafraichir une personne", "rafraichir sans climatisation",
    "rafraichissement d une piece", "avoir moins chaud", "confort thermique en ete",
    "climatiser sans clim", "climatiser une piece sans clim",
}


def _norm(s: str) -> str:
    """Minuscule, sans accents (NFKD), sans ponctuation, espaces réduits — comparaison robuste (accents/ponctuation/
    unicode décomposé). Non-str -> "" (jamais d'exception)."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()
    s = "".join(c if (c.isalnum() or c.isspace()) else " " for c in s)
    return " ".join(s.split())


# ── PRINCIPES candidats de refroidissement (dont effets sous-exploités) — chacun JUGÉ par coherence_physique ─────
# nom, contenu (unique), spec pour le juge, silencieux, solide (sans gaz ni compresseur), puits, maturite, conf, base.
_P = namedtuple("_P", ["nom", "contenu", "spec", "silencieux", "solide", "puits", "maturite", "conf", "base"])

_PRINCIPES = [
    _P("compression de vapeur (clim classique)",
       "rafraîchir : cycle à compression de vapeur avec groupe extérieur",
       {"type": "refroidissement", "rejette_chaleur_exterieur": True, "cop": 3}, False, False,
       "air extérieur (condenseur/groupe)", "mature",
       0.5, "principe dominant ; bruyant (compresseur) et exige un rejet d'air extérieur — la référence à dépasser"),
    _P("boîte fermée sans évacuation (type Coolzy)",
       "rafraîchir : appareil clos dans la pièce, aucun rejet de chaleur vers l'extérieur",
       {"type": "refroidissement", "systeme_ferme": True, "puissance_entree": 50}, True, True,
       "aucun (revendiqué)", "commercial douteux",
       0.4, "idée « aspirer le chaud, rendre du froid, sans sortie » — à confronter à la thermodynamique"),
    _P("pompe magique COP 40 (ΔT 10 K)",
       "rafraîchir : pompe à chaleur revendiquant un COP de 40 pour un écart de 10 K",
       {"type": "pompe_chaleur", "cop": 40, "t_chaud_K": 303, "t_froid_K": 293}, True, True,
       "extérieur", "revendication",
       0.4, "revendication d'efficacité au-delà de la limite de Carnot — à réfuter si c'est le cas"),
    _P("thermoélectrique (Peltier), côté chaud refroidi par eau",
       "rafraîchir : module Peltier, chaleur du côté chaud évacuée par l'eau vers l'évacuation",
       {"type": "refroidissement", "rejette_chaleur_exterieur": True, "puissance_entree": 60}, True, True,
       "eau du réseau -> évacuation", "mature (COP faible)",
       0.55, "solide, silencieux sans ventilateur ; COP médiocre -> réservé au sol/personne, pas à l'air d'une pièce"),
    _P("magnétocalorique (réfrigération magnétique)",
       "rafraîchir : pompe à chaleur magnétocalorique (aimantation/désaimantation d'un solide)",
       {"type": "pompe_chaleur", "cop": 4, "t_chaud_K": 303, "t_froid_K": 288}, True, True,
       "extérieur (requis)", "émergent",
       0.6, "SANS GAZ ni compresseur, potentiellement silencieux — effet sous-exploité par le grand public"),
    _P("mécanocalorique (élasto/barocalorique, alliage superélastique)",
       "rafraîchir : effet élasto/barocalorique (contrainte mécanique cyclique d'un alliage à mémoire de forme)",
       {"type": "pompe_chaleur", "cop": 5, "t_chaud_K": 303, "t_froid_K": 288}, True, True,
       "extérieur (requis)", "recherche",
       0.55, "solide, sans fluide frigorigène ; COP de laboratoire prometteur — piste peu explorée hors labo"),
    _P("électrocalorique (champ électrique sur diélectrique)",
       "rafraîchir : effet électrocalorique (polarisation/dépolarisation d'un matériau diélectrique)",
       {"type": "pompe_chaleur", "cop": 4, "t_chaud_K": 303, "t_froid_K": 291}, True, True,
       "extérieur (requis)", "recherche",
       0.5, "solide, compact, silencieux ; encore au stade recherche — sous-exploité"),
    _P("échange direct avec l'eau du réseau (~15 °C)",
       "rafraîchir : circuler l'eau froide du réseau dans un sol/serpentin, chaleur rejetée à l'évacuation",
       {"type": "refroidissement", "rejette_chaleur_exterieur": True, "puissance_entree": 10}, True, True,
       "eau du réseau -> évacuation (ou réutilisation)", "simple",
       0.65, "quasi zéro énergie (pompe douce voire thermosiphon), silencieux ; coût = consommation d'eau"),
    _P("radiatif vers le ciel (nuit)",
       "rafraîchir : panneau émettant l'infrarouge vers le ciel, stocké puis diffusé au sol",
       {"type": "refroidissement", "rejette_chaleur_exterieur": True, "puissance_entree": 5}, True, True,
       "espace (rayonnement IR)", "connu (peu diffusé)",
       0.5, "puits = le ciel, gratuit ; exige une vue dégagée sur le ciel (contrainte en appartement)"),
    _P("puits périodique nocturne / couplage au sol (masse rechargée la nuit)",
       "rafraîchir : tampon (masse/MCP) rechargé en frais la nuit (air nocturne/sol), diffusé le jour au sol",
       {"type": "refroidissement", "rejette_chaleur_exterieur": True, "puissance_entree": 3}, True, True,
       "air nocturne / sol (recharge périodique)", "simple (principe de la maison en pierre)",
       0.7, "LE puits gratuit de la maison en pierre : stocker le frais la nuit, le libérer le jour ; silencieux, "
            "quasi zéro énergie ; conditionné à des nuits assez fraîches (échoue en canicule tropicale)"),
    _P("évaporatif adiabatique",
       "rafraîchir : évaporation d'eau (refroidissement adiabatique de l'air)",
       {"type": "refroidissement", "rejette_chaleur_exterieur": True, "puissance_entree": 30}, False, True,
       "air humide évacué", "mature",
       0.4, "efficace en air sec MAIS humidifie ; en circuit fermé sans évacuation d'air -> contre-productif"),
    # ── PRINCIPES EXOTIQUES / SOUS-EXPLORÉS (réels, ajoutés pour « pousser plus loin » — maturités honnêtes) ──
    _P("adsorption/sorption à chaleur-motrice (solaire)",
       "rafraîchir : cycle d'adsorption (zéolithe/gel de silice + eau) ENTRAÎNÉ par la chaleur (solaire), pas l'électricité",
       {"type": "refroidissement", "rejette_chaleur_exterieur": True, "puissance_entree": 5}, True, True,
       "extérieur (condenseur) ; MOTEUR = chaleur solaire", "émergent (chillers solaires)",
       0.6, "la CHALEUR/le SOLEIL alimente le froid (zéro électricité), silencieux, sans compresseur ; plus il fait "
            "chaud, plus il y a de puissance motrice — retourne l'ennemi en carburant ; sous-exploité en domestique"),
    _P("thermochimique (réaction réversible dense)",
       "rafraîchir : stocker le froid comme réaction chimique réversible (hydratation de sels…), densité 5–10× le MCP",
       {"type": "refroidissement", "rejette_chaleur_exterieur": True, "puissance_entree": 3}, True, True,
       "extérieur à la recharge (chaleur/nuit)", "recherche",
       0.55, "répond DIRECTEMENT à l'encombrement : densité de stockage 5–10× le MCP -> bien plus compact/léger ; "
             "recharge par chaleur (solaire) ; corrosion/cyclage à maîtriser"),
    _P("radiatif diurne (émetteur sélectif métamatériau)",
       "rafraîchir : surface à émissivité sélective (fenêtre 8–13 µm) descendant SOUS l'ambiant même en plein soleil",
       {"type": "refroidissement", "rejette_chaleur_exterieur": True, "puissance_entree": 0}, True, True,
       "espace (rayonnement IR), gratuit", "émergent (films sélectifs)",
       0.5, "ZÉRO énergie, puits = l'espace ; ~40–100 W/m² ; matériau passif (pas un appareil) ; exige une vue sur le ciel"),
    _P("thermionique / effet tunnel thermique (solide)",
       "rafraîchir : transport d'électrons chauds à travers une nanobarrière/un vide — pompe de chaleur solide au-delà du Peltier",
       {"type": "pompe_chaleur", "cop": 2, "t_chaud_K": 303, "t_froid_K": 288}, True, True,
       "extérieur (requis)", "recherche",
       0.4, "solide, compact, silencieux ; vise un meilleur rendement que le Peltier — encore en labo"),
    _P("refroidissement optique (fluorescence anti-Stokes)",
       "rafraîchir : un solide dopé émet des photons plus énergétiques qu'il n'en absorbe -> il se refroidit (froid par la lumière)",
       {"type": "pompe_chaleur", "cop": 1, "t_chaud_K": 303, "t_froid_K": 293}, True, True,
       "rayonnement de fluorescence (évacué)", "exotique (labo, petites puissances)",
       0.25, "principe contre-intuitif RÉEL (refroidir AVEC de la lumière) ; aujourd'hui puissances minuscules/"
             "matériaux spéciaux — horizon lointain, mais strictement dans les lois"),
    _P("thermoacoustique (onde sonore pompe la chaleur)",
       "rafraîchir : réfrigérateur thermoacoustique — une onde stationnaire pompe la chaleur, peu de pièces mobiles, sans frigorigène",
       {"type": "refroidissement", "rejette_chaleur_exterieur": True, "puissance_entree": 20}, False, True,
       "extérieur (échangeur chaud)", "recherche",
       0.4, "sans gaz nocif, robuste ; peut être ENTRAÎNÉ par la chaleur (froid sans électricité) ; le son interne "
            "exige un confinement acoustique sinon c'est bruyant"),
    _P("tube vortex (Ranque-Hilsch)",
       "rafraîchir : de l'air comprimé se sépare en un flux chaud et un flux froid, sans pièce mobile",
       {"type": "refroidissement", "rejette_chaleur_exterieur": True, "puissance_entree": 100}, False, True,
       "flux d'air chaud évacué", "mature (industriel)",
       0.3, "aucune pièce mobile, robuste ; MAIS exige de l'air comprimé (bruyant, énergivore) — peu adapté au domestique"),
]


# Objectif réel + loi structurante du domaine COOLING (extraits en constantes pour le registre).
_OBJECTIF_COOL = ("Le but réel n'est pas de refroidir l'AIR de la pièce (~500–1000 W à combattre en continu) mais de "
                  "permettre au CORPS de dissiper ses ~100 W à température de peau confortable. On cible donc les canaux "
                  "d'échange du corps (rayonnement, conduction, convection, évaporation), pas l'air — soit un ordre de "
                  "grandeur de charge en moins (estimation), dans les lois (chaque principe reste jugé séparément).")
_LOI_COOL = ("aucun principe ne bat Carnot (COP de FROID ≤ Tc/(Th−Tc)) ; gains réels = réduire la charge (cibler "
             "le corps), viser un puits déjà froid (ΔT faible), empêcher les apports")


def objectif_reel(besoin: str) -> str:
    """Le REFRAMING machine : ce que le besoin veut VRAIMENT (pas la solution humaine par défaut). HORS si inconnu."""
    d = _domaine(besoin)
    if d is None:
        return f"[{HORS}] besoin non modélisé : {besoin!r} — le manque est visible (brique d'objectif à ajouter)"
    return d.objectif


def decompose(besoin: str) -> dict:
    """Décompose un besoin borné en objectif réel + canaux/leviers physiques. Besoin inconnu -> {statut: HORS}.
    Dispatch par le registre de domaines : chaque domaine fournit son objectif, ses canaux, sa loi et ses
    `extras` (champs propres, ex. charges thermiques pour le cooling)."""
    d = _domaine(besoin)
    if d is None:
        return {"statut": HORS, "besoin": besoin,
                "raison": "besoin non modélisé — décomposition à construire (c'est le manque que le test révèle)"}
    return {
        "statut": "decompose",
        "besoin": besoin,
        "objectif_reel": d.objectif,
        "canaux": list(d.canaux),
        "loi": d.loi,
        **d.extras,
    }


def principes(besoin: str = "rafraichir une piece") -> dict:
    """Liste les PRINCIPES candidats, chacun en atome + verdict physique. Impossible -> atome RÉFUTÉ ; possible ->
    RESTE une SUPPOSITION (jamais promu en FAIT : la cohérence n'est pas une preuve d'efficacité). Besoin inconnu
    -> {statut: HORS}."""
    d = _domaine(besoin)
    if d is None:
        return {"statut": HORS, "besoin": besoin,
                "raison": "aucun catalogue de principes pour ce besoin — à construire (manque visible)"}
    liste = []
    for p in d.principes:
        at = A.suppose(p.contenu, A.GENERATIF, A.Portee(A.DOMAINE, "candidat pour " + d.nom + " ; efficacité non jugée"),
                       p.conf, p.base)
        st, raison, loi = COH.juge_dispositif(p.spec)
        if st == COH.VIOLE:
            at = A.promeut(at, A.Verdict("coherence_physique", False, f"{loi} — {raison}"), quand="2026-07-02")
        liste.append({
            "nom": p.nom, "atome": at, "verdict_physique": COH.explique(st, raison, loi),
            "statut_physique": st, "silencieux": p.silencieux, "solide_sans_gaz": p.solide,
            "puits": p.puits, "maturite": p.maturite,
        })
    return {"statut": "principes", "besoin": besoin, "liste": liste}


# ── STRATÉGIES NATURELLES (transfert inter-domaines : la nature = bibliothèque de leviers HONNÊTES empilés) ──────
# La nature ne crée jamais de froid (mêmes lois) : elle EMPILE gratuitement les leviers valides. Les copier
# (biomimétisme) est un espace de recherche puissant et sous-exploité — mais aucun exemple ne contient de « free
# lunch » : chacun se réduit aux leviers (bloquer les apports / évaporer / puits nocturne ou terrestre / masse).
_Nature = namedtuple("_Nature", ["exemple", "leviers", "lecon"])
_STRATEGIES_NATURE = [
    _Nature("forêt en été (plus fraîche que l'air libre)",
            ["ombrage (bloque le rayonnement solaire)", "évapotranspiration (évaporatif, chaleur latente)",
             "masse humide du sol", "rayonnement nocturne de la canopée vers le ciel"],
            "empiler ombre + évaporation + puits nocturne — aucun n'est un appareil, tout est gratuit"),
    _Nature("cycle jour/nuit (rotation de la Terre)",
            ["air nocturne frais (puits périodique)", "rayonnement vers le ciel la nuit (face à l'ombre)"],
            "LE puits périodique gratuit : stocker le frais la nuit, le libérer le jour (principe de la pierre)"),
    _Nature("grotte / cave (fraîche toute l'année)",
            ["inertie de la masse terrestre (T stable ~12–15 °C)", "couplage au sol comme puits/source"],
            "la masse profonde est un puits stable découplé de la météo — pas de canicule sous terre"),
    _Nature("termitière (climat interne régulé sans énergie)",
            ["cheminée thermique (convection naturelle)", "inertie des parois"],
            "tirage thermique passif = renouvellement d'air SANS ventilateur (silencieux) ; ne rafraîchit qu'en "
            "le couplant à un puits plus frais (air nocturne / masse chargée la nuit)"),
    _Nature("jarre poreuse / peau qui transpire (évaporation)",
            ["évaporation d'eau (chaleur latente prélevée)", "air sec/mouvement pour emporter la vapeur"],
            "l'évaporation refroidit fort et sans machine — mais exige d'ÉVACUER la vapeur (sinon ça sature)"),
]


def strategies_naturelles(besoin: str = "rafraichir une piece") -> list[dict]:
    """Transfert inter-domaines : exemples naturels RÉDUITS à leurs leviers physiques. Catalogue INFORMATIF à
    peigner ; chaque levier reste jugeable par coherence_physique — on ne PROMET pas qu'un exemple « marche »
    (efficacité non jugée). Dispatch par domaine ; besoin inconnu -> [] (dégradation propre). Défaut = cooling
    (compat : les appelants historiques sans argument gardent les stratégies de rafraîchissement)."""
    d = _domaine(besoin)
    if d is None:
        return []
    return [{"exemple": n.exemple, "leviers": list(n.leviers), "lecon": n.lecon} for n in d.strategies]


def chaines_physiques(sources=("lumiere", "pression", "mouvement", "magnetisme"),
                      cible: str = "chaleur", max_len: int = 4) -> list[dict]:
    """PONT vers substrat_physique : chaînes de transduction (dont NOUVELLES) pour piloter la gestion de chaleur
    depuis des sources disponibles. Montre l'espace physique ouvert que la machine peut peigner.
    `sources` None / non itérable / str, ou `cible` non-str -> [] (dégradation propre, jamais d'exception)."""
    if sources is None or isinstance(sources, (str, bytes)) or not hasattr(sources, "__iter__"):
        return []
    if not isinstance(cible, str) or not cible:
        return []
    out = []
    for s in sources:
        if s not in SP.GRANDEURS or cible not in SP.GRANDEURS:
            out.append({"source": s, "cible": cible, "statut": HORS, "chaine": []})
            continue
        c = SP.examine(s, cible, max_len=max_len)
        out.append({"source": s, "cible": cible, "statut": c.statut, "chaine": list(getattr(c, "chaine", ()))})
    return out


# ── PREMIER DOMAINE ENREGISTRÉ : refroidissement / confort thermique (comportement historique, à l'identique) ──
enregistre(Domaine(
    nom=_COOL,
    aliases=frozenset(_ALIAS_COOL),
    objectif=_OBJECTIF_COOL,
    canaux=_CANAUX_CORPS,
    principes=_PRINCIPES,
    strategies=_STRATEGIES_NATURE,
    loi=_LOI_COOL,
    extras={"charge_corps_W": 100, "charge_piece_W": "≈ 500–1000 (selon apports/isolation — conditionnel)"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  DEUXIÈME DOMAINE : chauffage / confort d'hiver — le symétrique du cooling, avec l'ASYMÉTRIE clé : en hiver le
#  corps est une SOURCE (~100 W produits en continu), pas un puits. Le reframing machine s'inverse donc : ne pas
#  PRODUIRE de la chaleur pour l'air, RETENIR celle qui existe déjà (corps, soleil, chaleur fatale) et n'apporter
#  que le complément. Les mêmes quatre canaux physiologiques deviennent des PERTES à réduire (tous les leviers
#  sont passifs -> silencieux). FAUX=0 : chaque principe = SUPPOSITION jugée par coherence_physique ; les
#  revendications impossibles (rendement 150 % -> conservation ; COP 40 -> Carnot chauffage Th/(Th−Tc)) sont
#  RÉFUTÉES ; rien n'est jamais promu en FAIT.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_CHAUF = "chauffage_confort"
# Libellés QUALIFIÉS seulement — « chauffage » nu est ambigu (industriel, eau sanitaire, four) -> HORS honnête.
_ALIAS_CHAUF = {
    "chauffer une piece", "chauffer une personne", "avoir moins froid", "se chauffer en hiver",
    "confort thermique en hiver", "chauffer sans radiateur", "se chauffer a moindre cout",
}

# Les mêmes canaux d'échange du corps, sens inversé : levier qui RÉDUIT la perte de chaleur du corps.
# Réduire une perte est passif -> tous silencieux (l'asymétrie d'hiver rend le silence gratuit).
_CANAUX_CORPS_HIVER = [
    Canal("rayonnement", "chaleur", "supprimer les PAROIS FROIDES (vitrage nu = puits radiatif) : rideaux/low-e, "
          "surfaces radiantes tièdes",
          True, "part dominante en air calme : une paroi froide « aspire » le rayonnement du corps même dans un air à 20 °C"),
    Canal("conduction", "chaleur", "isoler le CONTACT (sol, assise) ; masses tièdes locales (bouillotte, plancher tempéré)",
          True, "très efficace localement : quelques dizaines de watts ciblés remplacent des centaines dans l'air"),
    Canal("convection", "chaleur", "supprimer COURANTS D'AIR et infiltrations ; piéger de l'air immobile (étanchéité, couches)",
          True, "l'air en mouvement arrache la couche limite chaude du corps ; l'air IMMOBILE est un excellent isolant"),
    Canal("evaporation", "chaleur", "rester SEC (peau, vêtements) : l'humidité multiplie la perte par chaleur latente",
          True, "un vêtement humide évacue la chaleur du corps bien plus vite qu'un sec (chaleur latente)"),
]

_PRINCIPES_CHAUF = [
    _P("convecteur résistif (référence basse)",
       "chauffer : résistance électrique chauffant l'air de la pièce",
       {"type": "conversion", "rendement": 1.0}, True, True,
       "aucun (la pièce reçoit tout)", "mature",
       0.5, "COP = 1 par construction : chaque joule électrique finit en chaleur, jamais plus — la référence à "
            "DÉPASSER (une pompe à chaleur en déplace 3–5× plus pour le même courant)"),
    _P("radiateur « à rendement 150 % »",
       "chauffer : appareil électrique revendiquant plus de chaleur que d'électricité consommée, sans pompe",
       {"type": "conversion", "rendement": 1.5}, True, True,
       "aucun (revendiqué)", "revendication",
       0.3, "revendication marketing récurrente — créerait de l'énergie nette ; à confronter à la conservation"),
    _P("PAC magique COP 40 (ΔT 20 K)",
       "chauffer : pompe à chaleur revendiquant un COP de 40 entre 0 °C dehors et 20 °C dedans",
       {"type": "pompe_chaleur", "cop": 40, "t_chaud_K": 293, "t_froid_K": 273}, True, True,
       "source = air extérieur (revendiqué)", "revendication",
       0.4, "revendication au-delà de la limite de Carnot chauffage (≈ 14,7 pour cet écart) — à réfuter si c'est le cas"),
    _P("pompe à chaleur air/air (COP 3–4)",
       "chauffer : cycle à compression prélevant la chaleur de l'air extérieur",
       {"type": "pompe_chaleur", "cop": 3.5, "t_chaud_K": 293, "t_froid_K": 273}, False, False,
       "SOURCE = air extérieur", "mature",
       0.6, "la référence moderne : 1 kWh électrique en déplace 3–4 depuis l'air ; bruit (unité extérieure) et "
            "COP qui chute au grand froid (givrage) — c'est la référence à dépasser en silence"),
    _P("PAC sur sol/eau (source stable ~12 °C)",
       "chauffer : pompe à chaleur couplée au sol ou à une nappe (température stable, ΔT faible)",
       {"type": "pompe_chaleur", "cop": 5.5, "t_chaud_K": 303, "t_froid_K": 285}, True, False,
       "SOURCE = sol/nappe (découplée de la météo)", "mature (coût de forage)",
       0.6, "le miroir de la grotte : source stable ~12 °C toute l'année, pas de givrage, ΔT faible -> COP élevé ; "
            "pas d'unité extérieure ventilée -> silencieux"),
    _P("solaire passif (vitrage sud + masse, mur Trombe)",
       "chauffer : capter le rayonnement solaire par vitrage, le stocker dans une masse, le restituer la nuit",
       {"type": "conversion", "rendement": 0.6}, True, True,
       "SOURCE = soleil (gratuite, même en hiver par ciel clair)", "ancestral (sous-exploité en rénovation)",
       0.65, "zéro énergie payante : orientation + vitrage + masse ; le vitrage laisse entrer le rayonnement "
             "solaire et bloque l'infrarouge sortant ; la masse déphase le gain du jour vers la nuit"),
    _P("superisolation + chaleur métabolique (igloo / Passivhaus)",
       "chauffer : réduire les pertes jusqu'à ce que les ~100 W du corps (+ appareils) suffisent",
       {"type": "conversion", "puissance_entree": 100, "puissance_utile": 100}, True, True,
       "aucune source dédiée (le corps EST la source)", "prouvé (igloo ; Passivhaus certifié)",
       0.7, "l'inversion machine : ne pas PRODUIRE, RETENIR — l'igloo tient des dizaines de degrés d'écart avec la "
            "seule chaleur des corps ; le Passivhaus supprime le chauffage dédié"),
    _P("radiant infrarouge ciblé corps (panneau dirigé)",
       "chauffer : panneau rayonnant dirigé vers la personne, l'air restant frais",
       {"type": "conversion", "rendement": 0.98}, True, True,
       "aucun (chaleur directe au corps)", "mature (sous-exploité en domestique)",
       0.6, "chauffer la PERSONNE, pas l'air : quelques centaines de watts ciblés remplacent des kilowatts de "
            "pièce — le miroir hiver du « cibler le corps » d'été"),
    _P("récupération de chaleur fatale (double flux, eaux grises)",
       "chauffer : échangeur récupérant la chaleur de l'air extrait et des eaux chaudes évacuées",
       {"type": "conversion", "rendement": 0.85}, True, True,
       "SOURCE = chaleur déjà payée (ventilation, douche)", "mature (peu diffusé)",
       0.65, "sous-exploité : la chaleur déjà payée repart par la ventilation et l'égout ; un échangeur en rend "
             "une large part sans rien produire"),
    _P("thermochimique inter-saisonnier (hydrates de sels : été -> hiver)",
       "chauffer : stocker la chaleur solaire d'été dans une réaction réversible (hydratation de sels), la libérer l'hiver",
       {"type": "conversion", "rendement": 0.5}, True, True,
       "SOURCE = soleil d'été (stocké chimiquement, sans perte dans le temps)", "recherche (pilotes)",
       0.55, "densité 2–10× l'eau et AUCUNE perte au stockage (l'énergie est chimique, pas thermique) — le miroir "
             "hiver du thermochimique froid ; corrosion/cyclage à maîtriser"),
    _P("MCP déphasé (chaleur latente chargée quand l'énergie est bon marché)",
       "chauffer : stocker en chaleur latente (paraffine/sels) aux heures creuses ou solaires, restituer au besoin",
       {"type": "conversion", "rendement": 0.9}, True, True,
       "SOURCE = électricité creuse / soleil (déphasés)", "émergent (couplage PAC+MCP étudié)",
       0.55, "ne crée rien : DÉPLACE la source bon marché vers l'heure du besoin ; lisse aussi la pompe à chaleur "
             "(moins de cycles au pire moment)"),
    _P("élasto/magnétocalorique en mode pompe (solide, sans gaz)",
       "chauffer : effet calorique d'un solide (contrainte/champ) pompant la chaleur de dehors vers dedans",
       {"type": "pompe_chaleur", "cop": 4, "t_chaud_K": 293, "t_froid_K": 278}, True, True,
       "SOURCE = air extérieur", "recherche",
       0.5, "les mêmes effets caloriques que le froid, en sens inverse : sans fluide frigorigène, potentiellement "
            "silencieux — sous-exploités en chauffage aussi"),
    _P("micro-cogénération (chaleur + électricité du même combustible)",
       "chauffer : produire l'électricité sur place et récupérer la chaleur du moteur / de la pile",
       {"type": "conversion", "rendement": 0.9}, False, False,
       "SOURCE = combustible (gaz/bois/H2)", "mature (niche)",
       0.45, "un combustible brûlé pour l'électricité seule jette une grande part en chaleur ; produite sur place, "
             "cette chaleur chauffe la maison — rendement global élevé, bruit et combustible en contrepartie"),
]

_OBJECTIF_CHAUF = ("Le but réel n'est pas de chauffer l'AIR de la pièce (~1000–3000 W de pertes à compenser en "
                   "continu — conditionnel à l'isolation) mais de conserver les ~100 W que le corps PRODUIT déjà : "
                   "l'asymétrie d'hiver — le corps est une SOURCE, pas un puits. On réduit d'abord ses pertes par "
                   "les quatre canaux (parois froides, contact, courants d'air, humidité), puis on n'apporte que le "
                   "complément depuis les sources les moins chères (soleil, sol, chaleur fatale) — chaque principe "
                   "reste jugé séparément.")
_LOI_CHAUF = ("l'énergie ne se crée pas : résistif = COP 1 exactement ; pompe à chaleur : COP ≤ Th/(Th−Tc) (Carnot "
              "chauffage) ; gains réels = réduire les PERTES (isolation, étanchéité), cibler le corps (~100 W déjà "
              "produits), capter les sources gratuites ou déjà payées (soleil, sol, chaleur fatale)")

# La nature n'a pas de radiateur : elle RETIENT (isolation), MUTUALISE (groupe) et CAPTE (soleil, sol, déphasage).
_STRATEGIES_NATURE_HIVER = [
    _Nature("manchots empereurs (la « tortue » par −40 °C)",
            ["mutualiser la chaleur métabolique (groupe serré)", "réduire la surface exposée par individu",
             "rotation du bord vers le centre"],
            "réduire la SURFACE d'échange et mutualiser la production — aucun apport externe, que de la géométrie"),
    _Nature("fourrure d'hiver / duvet (air immobile piégé)",
            ["air immobilisé = isolant (conduction faible)", "épaisseur accrue en hiver (mue)",
             "couche limite protégée du vent"],
            "le meilleur isolant courant est l'air qu'on empêche de bouger — c'est l'ÉPAISSEUR qui compte, pas la matière"),
    _Nature("lézard au soleil du matin (thermorégulation comportementale)",
            ["capter le rayonnement solaire direct", "s'orienter face au soleil", "surface sombre (absorptivité)"],
            "la source gratuite existe même par air glacial : le rayonnement direct — s'orienter ne coûte rien"),
    _Nature("vie sous la neige (subnivium) / terrier",
            ["la neige est un isolant (air piégé)", "le sol est une source stable", "petit volume à tenir"],
            "sous une épaisse couche de neige la température reste proche de 0 °C par grand froid : l'isolant est "
            "déjà sur place, le sol fournit le reste"),
    _Nature("pierre/adobe du désert (nuits glaciales)",
            ["masse stockant le soleil du jour", "restitution déphasée la nuit"],
            "le même levier que l'été, inversé : stocker le CHAUD du jour pour la nuit froide — le déphasage est le levier"),
]

enregistre(Domaine(
    nom=_CHAUF,
    aliases=frozenset(_ALIAS_CHAUF),
    objectif=_OBJECTIF_CHAUF,
    canaux=_CANAUX_CORPS_HIVER,
    principes=_PRINCIPES_CHAUF,
    strategies=_STRATEGIES_NATURE_HIVER,
    loi=_LOI_CHAUF,
    extras={"production_corps_W": 100, "pertes_piece_W": "≈ 1000–3000 (selon isolation/ΔT — conditionnel)"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  TROISIÈME DOMAINE : dessaler / purifier l'eau — enjeu mondial (rareté), physique RICHE et surtout DUREMENT
#  bornée : le travail minimal de séparation (énergie de mélange de Gibbs ≈ π osmotique, van 't Hoff) est
#  l'analogue de Carnot. On a d'abord ÉTENDU `coherence_physique` d'un type `dessalement` qui RÉFUTE toute
#  énergie déclarée SOUS ce plancher (≈ 0,76 kWh/m³ pour l'eau de mer à récupération → 0) — donc ici, comme pour
#  le froid, l'impossible devient un atome RÉFUTÉ, pas une simple supposition. FAUX=0 : les principes cohérents
#  restent des SUPPOSITIONS jugées, jamais des faits.
#  REFRAMING machine : ne pas « bouillir toute l'eau » ni pousser en bloc contre π ; payer le MOINS possible
#  au-dessus du minimum en (a) ne sur-récupérant pas, (b) appariant la méthode à la salinité, (c) exploitant
#  les sources GRATUITES (solaire, chaleur fatale, gradient de salinité).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_EAU = "dessalement_eau"
# Libellés QUALIFIÉS (séparation du SEL) ; « purifier l'eau » nu est ambigu (bactéries, turbidité) → écarté.
_ALIAS_EAU = {
    "dessaler l eau de mer", "dessaler l eau", "dessaler l eau saumatre", "produire de l eau douce",
    "rendre l eau de mer potable", "dessalement de l eau", "dessalement",
}

# ── « Canaux » de séparation : les leviers physiques par lesquels on sépare l'eau du sel ─────────────────────────
# (grandeur = ce qu'on déplace : l'eau, ou l'ion.)
_CANAUX_EAU = [
    Canal("pression", "eau", "pousser l'eau à travers une membrane en DÉPASSANT π (osmose inverse)",
          False, "pompe haute pression = bruit + énergie ; l'échangeur de pression récupère l'énergie de la saumure"),
    Canal("changement de phase", "eau", "évaporer OU congeler : le sel reste dans la phase liquide résiduelle",
          True, "la congélation prend la chaleur latente de FUSION (334 kJ/kg) « au lieu » de vaporisation (2260) "
                "— théoriquement moins d'énergie, mais séparer les cristaux de glace du sel est délicat"),
    Canal("champ electrique", "ions", "tirer les IONS hors de l'eau (électrodialyse, désionisation capacitive)",
          True, "on déplace l'ion MINORITAIRE, pas toute l'eau → très économe en eau PEU salée, inadapté à l'eau de mer"),
    Canal("affinite selective", "ions", "capter sélectivement les ions (adsorption, résines, aquaporines, hydrates)",
          True, "sélectivité biomimétique (aquaporines) ou piégeage (clathrates) — jeune, prometteur hors labo"),
]

# ── PRINCIPES candidats de dessalement — chacun JUGÉ par le travail minimal de séparation (L3) ───────────────────
_PRINCIPES_EAU = [
    _P("osmose inverse eau de mer (SWRO, référence)",
       "dessaler : pousser l'eau de mer à travers une membrane semi-perméable au-delà de la pression osmotique",
       {"type": "dessalement", "energie_kWh_par_m3": 3.0, "osmose_pression_bar": 27}, False, True,
       "saumure concentrée (rejet à gérer)", "mature (dominant)",
       0.65, "la référence moderne : ~3 kWh/m³ avec échangeurs de pression, ~4× le minimum thermodynamique ; "
             "bruit de pompe et colmatage des membranes — la barre à descendre"),
    _P("osmose inverse eau saumâtre (BWRO)",
       "dessaler : osmose inverse sur une eau peu salée (nappe saumâtre), à basse pression",
       {"type": "dessalement", "energie_kWh_par_m3": 1.0, "osmose_pression_bar": 5}, False, True,
       "saumure (rejet, plus faible volume)", "mature",
       0.7, "π faible → énergie faible : APPARIER la méthode à la salinité est le premier levier (une eau "
            "saumâtre ne se traite pas comme l'eau de mer)"),
    _P("distillation multi-effet / MSF (thermique)",
       "dessaler : évaporer puis condenser l'eau en plusieurs effets, le sel restant dans la saumure",
       {"type": "dessalement", "energie_kWh_par_m3": 12.0, "osmose_pression_bar": 27}, True, False,
       "saumure chaude concentrée", "mature (pays chauds/pétroliers)",
       0.5, "robuste et insensible au colmatage, traite l'hypersalin ; ÉNERGIVORE (chaleur), rentable surtout "
            "adossé à de la chaleur fatale (centrale, industrie)"),
    _P("dessalement par congélation (freeze desalination)",
       "dessaler : congeler partiellement l'eau — la glace exclut le sel — puis séparer et fondre les cristaux",
       {"type": "dessalement", "energie_kWh_par_m3": 6.0, "osmose_pression_bar": 27}, True, False,
       "saumure froide concentrée", "recherche (sous-exploité)",
       0.5, "la chaleur latente de FUSION est ~7× plus faible que celle de vaporisation → potentiel d'énergie "
            "moindre que la distillation ; verrou = laver le sel piégé entre les cristaux ; peu exploité"),
    _P("électrodialyse (ED / EDR)",
       "dessaler : un champ électrique tire les ions à travers des membranes échangeuses d'ions",
       {"type": "dessalement", "energie_kWh_par_m3": 1.5, "osmose_pression_bar": 5}, True, True,
       "concentrat ionique", "mature (eau saumâtre)",
       0.6, "on déplace l'ION, pas toute l'eau → très efficace en eau PEU salée ; le coût monte avec la salinité "
            "(inadapté à l'eau de mer) — le miroir « cibler le minoritaire »"),
    _P("désionisation capacitive (CDI)",
       "dessaler : adsorber les ions sur des électrodes poreuses chargées, puis les relâcher en déchargeant",
       {"type": "dessalement", "energie_kWh_par_m3": 0.6, "osmose_pression_bar": 3}, True, True,
       "saumure de régénération", "émergent",
       0.5, "récupère une partie de l'énergie à la décharge ; réservé aux eaux FAIBLEMENT salées (l'adsorption "
            "sature) — sous-exploité pour l'eau saumâtre domestique"),
    _P("distillation membranaire (MD, chaleur fatale)",
       "dessaler : la vapeur traverse une membrane hydrophobe sous un faible écart de température",
       {"type": "dessalement", "energie_kWh_par_m3": 5.0, "osmose_pression_bar": 27}, True, False,
       "saumure", "recherche (niche chaleur fatale)",
       0.5, "fonctionne sur de la chaleur BASSE température (fatale, solaire) que rien d'autre ne valorise → "
            "l'énergie « payée » est quasi nulle si la chaleur est un déchet ; sous-exploité"),
    _P("dessalement solaire (still / solaire thermique)",
       "dessaler : évaporer l'eau au soleil sous une vitre, condenser le distillat (le sel reste)",
       {"type": "dessalement", "energie_kWh_par_m3": 630.0, "osmose_pression_bar": 27}, True, False,
       "saumure (bassin)", "ancestral (hors réseau)",
       0.55, "ÉNORME énergie thermique MAIS entièrement SOLAIRE (gratuite) et passive → idéal hors réseau / "
             "petite échelle ; le débit par m² de capteur est le vrai plafond, pas l'énergie"),
    _P("osmose directe (forward osmosis)",
       "dessaler : une solution d'appel très concentrée attire l'eau à travers la membrane, puis on régénère l'appel",
       {"type": "dessalement", "energie_kWh_par_m3": 4.0, "osmose_pression_bar": 27}, True, True,
       "solution d'appel à régénérer", "recherche",
       0.4, "l'étape membranaire est douce (peu de pression) MAIS l'énergie se paie à la RÉGÉNÉRATION de l'appel "
            "— pas de repas gratuit ; intérêt = adosser la régénération à de la chaleur fatale"),
    _P("extraction par solvant directionnel (chaleur fatale)",
       "dessaler : un solvant dont la solubilité dépend de la température capte l'eau à chaud, la relâche à froid",
       {"type": "dessalement", "energie_kWh_par_m3": 2.5, "osmose_pression_bar": 27}, True, True,
       "saumure", "recherche (sous-exploité)",
       0.4, "sans membrane (pas de colmatage), entraîné par un petit écart de température → valorise la chaleur "
            "fatale ; encore au stade laboratoire"),
    _P("hydrates de gaz (clathrates)",
       "dessaler : former des hydrates de gaz (cages d'eau) qui excluent le sel, puis les dissocier",
       {"type": "dessalement", "energie_kWh_par_m3": 5.0, "osmose_pression_bar": 27}, True, True,
       "saumure", "recherche",
       0.35, "les cages d'hydrate n'admettent que l'eau → séparation intrinsèque ; gestion de la pression/du gaz "
             "invité à maîtriser — piste peu explorée"),
    _P("membranes biomimétiques (aquaporines / graphène)",
       "dessaler : osmose inverse à travers des membranes à aquaporines ou à nanopores de graphène",
       {"type": "dessalement", "energie_kWh_par_m3": 2.5, "osmose_pression_bar": 27}, False, True,
       "saumure", "émergent",
       0.5, "perméabilité bien plus élevée → moins de perte de charge, on APPROCHE le minimum thermodynamique ; "
            "reste une osmose inverse (l'énergie ne descend JAMAIS sous π) ; industrialisation en cours"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER : sous le travail minimal de séparation) ──
    _P("osmose inverse « à 0,3 kWh/m³ pour l'eau de mer »",
       "dessaler : osmose inverse de l'eau de mer revendiquée à 0,3 kWh/m³",
       {"type": "dessalement", "energie_kWh_par_m3": 0.3, "osmose_pression_bar": 27}, False, True,
       "saumure", "revendication",
       0.3, "revendication SOUS le plancher thermodynamique (~0,76 kWh/m³) — à réfuter par le travail minimal"),
    _P("dessalement passif « sans énergie »",
       "dessaler : produire de l'eau douce à partir d'eau de mer sans aucun apport d'énergie",
       {"type": "dessalement", "energie_kWh_par_m3": 0.0, "osmose_pression_bar": 27}, True, True,
       "saumure", "revendication",
       0.25, "séparer le sel sans énergie ferait baisser l'entropie de mélange sans travail — impossible"),
]

_OBJECTIF_EAU = ("Le but réel n'est pas de « bouillir toute l'eau » ni de la pousser en bloc contre la pression "
                 "osmotique totale, mais de payer le MOINS possible au-dessus du travail minimal de séparation "
                 "(≈ 0,76 kWh/m³ pour l'eau de mer à récupération → 0, ≈ 1,06 à 50 %). Leviers : ne pas SUR-récupérer "
                 "(à récupération → 1 la saumure concentre π et l'énergie diverge), viser le procédé réversible "
                 "(échangeurs de pression, étages à contre-courant), APPARIER la méthode à la salinité (saumâtre → "
                 "osmose inverse bon marché ; hypersalin → thermique), exploiter les sources GRATUITES (chaleur "
                 "fatale, solaire, gradient de salinité) — chaque principe reste jugé par le travail minimal.")
_LOI_EAU = ("on ne sépare pas l'eau du sel pour moins que l'énergie de mélange de Gibbs (≈ π osmotique, van 't "
            "Hoff ≈ 0,76 kWh/m³ pour l'eau de mer) ; à récupération finie le minimum MONTE (la saumure se "
            "concentre) ; gains réels = récupération d'énergie, apparier la méthode à la salinité, sources "
            "gratuites (solaire / chaleur fatale / gradient de salinité)")

# La nature dessale déjà : membrane solaire (mangrove), pompe ionique (glande à sel), distillation planétaire.
_STRATEGIES_NATURE_EAU = [
    _Nature("mangrove / palétuvier (boit l'eau de mer)",
            ["ultrafiltration racinaire (~90–97 % du sel exclu)",
             "moteur = transpiration SOLAIRE (osmose inverse alimentée par le soleil)",
             "excrétion foliaire du sel résiduel"],
            "une membrane d'osmose inverse alimentée GRATUITEMENT par le soleil via la transpiration — sans pompe"),
    _Nature("glande à sel des oiseaux marins / tortues",
            ["transport ACTIF d'ions (pompe ionique dédiée)", "excrétion d'une saumure très concentrée",
             "organe séparé du métabolisme"],
            "concentrer puis rejeter activement le sel — l'analogue de l'électrodialyse, ciblé sur l'ion pas l'eau"),
    _Nature("néphron du rein (multiplicateur à contre-courant)",
            ["échange à CONTRE-COURANT", "concentration par étages", "réabsorption sélective de l'eau"],
            "l'étagement à contre-courant approche la séparation réversible — le levier contre la sur-récupération"),
    _Nature("cycle de l'eau (évaporation océan → pluie)",
            ["distillation SOLAIRE à l'échelle planétaire", "le sel reste dans l'océan (changement de phase)",
             "condensation gratuite en altitude"],
            "la plus grande usine de dessalement est solaire et passive : évaporer, le sel reste, la pluie est douce"),
    _Nature("cellules à chlorure des branchies de poisson",
            ["transport actif d'ions à travers un épithélium", "sélectivité ionique fine"],
            "pomper l'ion sélectivement plutôt que filtrer toute l'eau — économe quand le sel est minoritaire"),
]

enregistre(Domaine(
    nom=_EAU,
    aliases=frozenset(_ALIAS_EAU),
    objectif=_OBJECTIF_EAU,
    canaux=_CANAUX_EAU,
    principes=_PRINCIPES_EAU,
    strategies=_STRATEGIES_NATURE_EAU,
    loi=_LOI_EAU,
    extras={"travail_min_kWh_m3_mer": "≈ 0,76 (récupération → 0) à 1,06 (50 %)", "salinite_mer_g_L": 35},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  QUATRIÈME DOMAINE : stocker l'énergie — clé de la transition (intermittence solaire/éolien). Démonstration
#  que le patron passe SANS toucher au juge : la loi dure ici est le 1er principe (rendement ALLER-RETOUR ≤ 1),
#  DÉJÀ jugé par le type `conversion` existant (rendement > 1 → over-unity → VIOLE). On n'étend donc PAS
#  `coherence_physique` (contraste avec le dessalement, dont la loi manquait). FAUX=0 : principes = suppositions
#  jugées, 2 revendications over-unity/mouvement perpétuel RÉFUTÉES.
#  REFRAMING machine : le besoin n'est pas « stocker de l'électricité » mais DÉCALER l'énergie dans le TEMPS.
#  Leviers : (a) APPARIER la techno à la DURÉE (secondes → volant/supercap ; heures → batterie/pompage ;
#  saisonnier → hydrogène/thermochimique) ; (b) MINIMISER les conversions (chaque conversion perd — stocker
#  dans la forme la plus proche de l'usage final : si le besoin est de la chaleur, stocker de la chaleur).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_ENERGIE = "stockage_energie"
_ALIAS_ENERGIE = {
    "stocker de l energie", "stocker l energie", "stockage d energie", "stocker l electricite",
    "stockage d electricite", "conserver l energie pour plus tard", "lisser la production intermittente",
}

# ── « Canaux » de stockage : la FORME physique dans laquelle l'énergie est retenue ───────────────────────────────
_CANAUX_ENERGIE = [
    Canal("chimique", "energie", "stocker dans des liaisons chimiques (batterie, hydrogène)",
          True, "haute densité et longue durée, MAIS chaque conversion électricité↔chimique perd → rendement "
                "aller-retour plafonné (≈ 0,9 batterie, ≈ 0,4 hydrogène)"),
    Canal("mecanique", "energie", "stocker en énergie potentielle/cinétique (pompage, gravité, volant, air comprimé)",
          False, "robuste, très longue durée de vie, mais faible densité ; compresseurs/turbines = bruit ; le "
                 "pompage-turbinage reste le stockage de masse dominant"),
    Canal("thermique", "energie", "stocker en chaleur (sensible, latente, thermochimique)",
          True, "le MOINS cher et SANS perte de conversion SI le besoin final est de la chaleur (chauffage, "
                "procédé) — le levier clé : ne pas passer par l'électricité inutilement"),
    Canal("electrostatique", "energie", "stocker en séparation de charges (supercondensateur)",
          True, "très rapide, quasi sans perte, mais faible densité → sert la PUISSANCE (pics courts), pas "
                "l'énergie (autonomie)"),
]

# ── PRINCIPES candidats de stockage — chacun JUGÉ par le rendement aller-retour (type `conversion`, ≤ 1) ──────────
_PRINCIPES_ENERGIE = [
    _P("batterie lithium-ion (référence)",
       "stocker : batterie électrochimique lithium-ion, rendement aller-retour ~0,90",
       {"type": "conversion", "rendement": 0.90}, True, True,
       "réservoir chimique (électrodes)", "mature (dominant mobile/résidentiel)",
       0.65, "rendement élevé et réponse rapide ; densité et coût en baisse ; durée limitée (heures), "
             "ressources et cyclage à gérer — la référence pour l'intra-journalier"),
    _P("pompage-turbinage (STEP)",
       "stocker : pomper l'eau vers un réservoir d'altitude, la turbiner pour restituer, rendement ~0,80",
       {"type": "conversion", "rendement": 0.80}, False, False,
       "réservoir d'altitude (énergie potentielle)", "mature (dominant en masse)",
       0.6, "le stockage de MASSE dominant du réseau ; très longue durée de vie, grande capacité ; conditionné "
            "au relief et à l'eau — le mètre-étalon du stockage de plusieurs heures"),
    _P("air comprimé (CAES adiabatique)",
       "stocker : comprimer l'air dans une cavité, le détendre pour restituer, rendement ~0,65",
       {"type": "conversion", "rendement": 0.65}, False, True,
       "cavité d'air comprimé", "mature (niche)",
       0.5, "grande capacité, longue durée de vie ; la chaleur de compression doit être RÉCUPÉRÉE (adiabatique) "
            "sinon le rendement chute — sinon rejetée = perte ; conditionné à une cavité géologique"),
    _P("volant d'inertie (flywheel)",
       "stocker : accumuler l'énergie en rotation d'une masse, rendement aller-retour ~0,85",
       {"type": "conversion", "rendement": 0.85}, True, False,
       "rotor en rotation (énergie cinétique)", "mature (puissance)",
       0.5, "réponse quasi instantanée, cycles quasi illimités ; se décharge en heures (frottements) → sert la "
            "PUISSANCE et la stabilité de fréquence, pas l'autonomie longue"),
    _P("hydrogène (électrolyse → pile/combustion)",
       "stocker : produire de l'hydrogène par électrolyse, le restituer en pile, rendement aller-retour ~0,38",
       {"type": "conversion", "rendement": 0.38}, True, True,
       "réservoir chimique (H₂)", "émergent (saisonnier)",
       0.5, "faible rendement (double conversion) MAIS stockage SAISONNIER et très haute densité massique → le "
            "seul candidat crédible pour tenir des semaines/mois ; le levier n'est pas le rendement mais la DURÉE"),
    _P("thermique haute température (sels fondus, roche)",
       "stocker : chauffer une masse (sels fondus/roche), restituer en chaleur ou via un cycle, rendement élec ~0,45",
       {"type": "conversion", "rendement": 0.45}, True, True,
       "réservoir de chaleur", "mature (solaire concentré)",
       0.55, "peu cher, grande capacité ; rendement élec médiocre MAIS ~0,90 si le besoin final est de la CHALEUR "
             "(pas de conversion) — le levier « stocker dans la forme de l'usage »"),
    _P("supercondensateur",
       "stocker : séparation de charges dans un supercondensateur, rendement aller-retour ~0,95",
       {"type": "conversion", "rendement": 0.95}, True, True,
       "réservoir électrostatique", "mature (puissance)",
       0.5, "rendement et cycles excellents, réponse ultra-rapide ; TRÈS faible densité → pics de puissance "
            "(secondes), jamais l'autonomie ; complément d'une batterie, pas un substitut"),
    _P("stockage gravitaire solide (masses levées)",
       "stocker : lever des masses solides, les redescendre pour restituer, rendement ~0,80",
       {"type": "conversion", "rendement": 0.80}, False, False,
       "masses en hauteur (énergie potentielle)", "émergent",
       0.4, "principe du pompage SANS l'eau ni le relief (blocs, mines désaffectées) ; durée de vie longue ; "
            "densité faible → encombrant — piste pour sites sans hydro"),
    _P("thermochimique saisonnier (hydrates de sels)",
       "stocker : réaction réversible (hydratation de sels) stockant l'énergie sans perte dans le temps",
       {"type": "conversion", "rendement": 0.50}, True, True,
       "réservoir chimique (sels, ZÉRO auto-décharge)", "recherche",
       0.5, "AUCUNE auto-décharge (l'énergie est chimique, pas thermique) → stocker l'été pour l'hiver sans "
            "perte ; densité 5–10× le stockage de chaleur sensible — le levier saisonnier sous-exploité"),
    _P("batterie à flux (redox)",
       "stocker : électrolytes liquides pompés à travers une pile, rendement aller-retour ~0,75",
       {"type": "conversion", "rendement": 0.75}, True, True,
       "réservoirs d'électrolyte", "émergent (réseau)",
       0.5, "DÉCOUPLE puissance (pile) et énergie (taille des réservoirs) → dimensionnable pour de longues "
            "durées ; densité modeste, encombrant — piste réseau stationnaire"),
    _P("air liquide (LAES)",
       "stocker : liquéfier l'air, le regazéifier pour restituer, rendement ~0,55 (mieux avec chaleur/froid fatals)",
       {"type": "conversion", "rendement": 0.55}, False, True,
       "réservoir cryogénique", "émergent",
       0.45, "sans contrainte géologique (contrairement au CAES/hydro) ; rendement modeste MAIS remonte si l'on "
             "récupère le froid/la chaleur d'autres procédés — valorise l'énergie fatale"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER : conservation de l'énergie) ──
    _P("stockage « à rendement aller-retour 115 % »",
       "stocker : dispositif restituant plus d'énergie qu'on n'en injecte (rendement 1,15)",
       {"type": "conversion", "rendement": 1.15}, True, True,
       "—", "revendication",
       0.3, "rendement aller-retour > 1 = énergie créée nette — à réfuter par la conservation"),
    _P("batterie « auto-rechargeante » perpétuelle",
       "stocker : batterie qui se recharge seule indéfiniment et fournit un courant en continu sans source",
       {"type": "conversion", "mouvement_perpetuel": True}, True, True,
       "—", "revendication",
       0.25, "auto-recharge sans source = mouvement perpétuel — impossible"),
]

_OBJECTIF_ENERGIE = ("Le but réel n'est pas « stocker de l'électricité » mais DÉCALER l'énergie dans le TEMPS "
                     "(emmagasiner quand elle est abondante/bon marché, restituer au besoin). Leviers : APPARIER "
                     "la techno à la DURÉE de décalage (secondes → volant/supercondensateur ; heures → "
                     "batterie/pompage ; saisonnier → hydrogène/thermochimique) ; MINIMISER les conversions "
                     "(chacune perd définitivement — stocker dans la forme la plus proche de l'usage final : si le "
                     "besoin est de la chaleur, stocker de la chaleur, pas de l'électricité) ; rendement, densité, "
                     "durée et coût sont en TENSION — aucun gagnant universel, chaque principe reste jugé séparément.")
_LOI_ENERGIE = ("conservation de l'énergie : rendement ALLER-RETOUR ≤ 1 (jamais plus d'énergie récupérée "
                "qu'injectée) ; toute perte de conversion est DÉFINITIVE ; gains réels = réduire le nombre de "
                "conversions, apparier la techno à la durée de stockage et à la FORME d'énergie finale")

# La nature stocke déjà : graisse (saisonnier chimique), ATP (rapide), graine dormante (zéro auto-décharge), tendon.
_STRATEGIES_NATURE_ENERGIE = [
    _Nature("graisse / hibernation (ours, oiseaux migrateurs)",
            ["stockage CHIMIQUE haute densité", "constitué quand la nourriture abonde",
             "mobilisé lentement sur des mois"],
            "réserve chimique dense pour le LONG terme (saisonnier), faite quand l'énergie est abondante — "
            "l'analogue de l'hydrogène/thermochimique"),
    _Nature("ATP (monnaie énergétique de la cellule)",
            ["stock PETIT mais restitution instantanée", "recyclé des milliers de fois par jour",
             "tampon entre production et usage"],
            "stocker peu et cycler très vite pour lisser l'instantané — l'analogue du supercondensateur"),
    _Nature("graine / amidon dormant",
            ["stockage chimique à AUCUNE auto-décharge sur des années", "libéré sur déclencheur (eau, chaleur)"],
            "conserver l'énergie des années sans perte jusqu'au besoin — l'analogue du thermochimique saisonnier"),
    _Nature("tendon élastique (kangourou, puce, tendon d'Achille)",
            ["stockage MÉCANIQUE élastique", "restitution quasi instantanée à forte puissance",
             "rendement de restitution élevé"],
            "emmagasiner puis relâcher vite pour la PUISSANCE — l'analogue du volant/ressort, pas de l'autonomie"),
    _Nature("inertie thermique du sol / de la roche",
            ["stockage THERMIQUE sensible", "chargé le jour, restitué la nuit (déphasage)",
             "aucune conversion si le besoin est thermique"],
            "quand l'usage final est de la chaleur, stocker de la chaleur : zéro conversion, le levier le moins cher"),
]

enregistre(Domaine(
    nom=_ENERGIE,
    aliases=frozenset(_ALIAS_ENERGIE),
    objectif=_OBJECTIF_ENERGIE,
    canaux=_CANAUX_ENERGIE,
    principes=_PRINCIPES_ENERGIE,
    strategies=_STRATEGIES_NATURE_ENERGIE,
    loi=_LOI_ENERGIE,
    extras={"rendement_aller_retour": "0,38 (hydrogène) à 0,95 (supercondensateur) selon la techno",
            "note_duree": "secondes → volant/supercap ; heures → batterie/pompage ; saisonnier → hydrogène/thermochimique"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  CINQUIÈME DOMAINE : capter le CO₂ — enjeu climatique. Même FAMILLE de loi que le dessalement (travail minimal
#  de séparation), mais pas osmotique : on a GÉNÉRALISÉ `coherence_physique` d'un type `separation` (plancher
#  R·T·ln(1/x) pour une fraction molaire x quelconque). Le CO₂ de l'air est ULTRA-dilué (x ≈ 4,2e-4 = 420 ppm) →
#  travail minimal ≈ 19,3 kJ/mol ; aux fumées (x ≈ 0,12) il tombe à ≈ 5,3 kJ/mol. La DILUTION est l'ennemi.
#  REFRAMING machine : capter d'abord LÀ où c'est concentré (fumées, cimenterie) ; pour la capture dans l'air
#  (DAC) l'énergie réelle est dominée par la RÉGÉNÉRATION du sorbant (chaleur) → l'adosser à la chaleur fatale/
#  solaire ; et le PUITS compte (minéralisation permanente vs stockage géologique). FAUX=0 : principes =
#  suppositions jugées, 2 revendications sous le plancher RÉFUTÉES.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_CO2 = "capture_co2"
_ALIAS_CO2 = {
    "capter le co2", "capturer le co2", "capture du co2", "capter le dioxyde de carbone",
    "capture directe dans l air", "capter le carbone atmospherique", "capturer le carbone",
}

# ── « Canaux » de capture : les mécanismes physiques par lesquels on isole le CO₂ ────────────────────────────────
_CANAUX_CO2 = [
    Canal("absorption chimique", "co2", "lier le CO₂ dans un liquide (amines, hydroxydes), le relâcher par chauffage",
          True, "sélectivité élevée même en gaz dilué ; l'énergie part surtout dans la RÉGÉNÉRATION (chaleur) — "
                "à adosser à de la chaleur fatale"),
    Canal("adsorption solide", "co2", "fixer le CO₂ sur un solide poreux, le relâcher (chaleur, vide, humidité)",
          True, "modulable (amines greffées, MOF, zéolithes) ; la régénération par HUMIDITÉ (moisture-swing) ou "
                "vide évite la chaleur — piste sous-exploitée pour la capture dans l'air"),
    Canal("membrane", "co2", "laisser passer sélectivement le CO₂ à travers une membrane",
          True, "compact, sans consommable ; sélectivité qui chute quand le CO₂ est très dilué → mieux aux fumées"),
    Canal("mineralisation", "co2", "réagir le CO₂ avec des minéraux (olivine, basalte) en carbonate STABLE",
          True, "le seul canal qui donne un PUITS permanent en une étape (pas de fuite) ; lent, exploite l'énergie "
                "de réaction naturelle — l'altération des roches accélérée"),
]

# ── PRINCIPES candidats de capture — chacun JUGÉ par le travail minimal de séparation (type `separation`, L3) ─────
_PRINCIPES_CO2 = [
    _P("amines post-combustion (fumées, référence)",
       "capter : laver les fumées (~12 % CO₂) par une solution d'amines, régénérée à la chaleur",
       {"type": "separation", "fraction_molaire": 0.12, "energie_kJ_par_mol": 120.0}, True, False,
       "CO₂ concentré (à stocker/valoriser)", "mature (industrie)",
       0.6, "la référence : capter LÀ où le CO₂ est concentré (x élevé → plancher ~5 kJ/mol) ; l'énergie réelle "
            "est dominée par la régénération à la chaleur — bien au-dessus du minimum, marge à réduire"),
    _P("sorbant solide DAC (capture dans l'air)",
       "capter : fixer le CO₂ de l'air ambiant (420 ppm) sur un sorbant solide, régénéré à ~100 °C",
       {"type": "separation", "fraction_molaire": 4.2e-4, "energie_kJ_par_mol": 230.0}, True, True,
       "CO₂ (stockage/valorisation)", "émergent (DAC)",
       0.5, "capte l'air ULTRA-dilué → plancher ~19 kJ/mol, mais l'énergie réelle (régénération) est ~10× → "
            "le levier n'est pas de battre le minimum mais de valoriser une chaleur GRATUITE pour régénérer"),
    _P("solvant hydroxyde DAC (haute température)",
       "capter : absorber le CO₂ de l'air dans une solution alcaline, régénérée par calcination à ~900 °C",
       {"type": "separation", "fraction_molaire": 4.2e-4, "energie_kJ_par_mol": 350.0}, True, False,
       "CO₂ (stockage géologique)", "démonstrateur (DAC)",
       0.45, "voie industrielle robuste MAIS calcination très chaude = beaucoup d'énergie ; intérêt = échelle et "
             "sorbant régénérable indéfiniment — à décarboner par la chaleur de la source"),
    _P("séparation membranaire (fumées)",
       "capter : membrane sélective au CO₂ sur un flux de fumées concentré",
       {"type": "separation", "fraction_molaire": 0.12, "energie_kJ_par_mol": 80.0}, True, True,
       "CO₂ concentré", "émergent",
       0.5, "compacte, sans solvant ni chaleur de régénération ; efficace tant que le CO₂ est CONCENTRÉ "
            "(inadaptée à l'air ambiant) — le miroir « apparier à la concentration »"),
    _P("moisture-swing (régénération par l'humidité, DAC)",
       "capter : sorbant qui fixe le CO₂ sec et le relâche humide — régénéré par l'EAU, pas la chaleur",
       {"type": "separation", "fraction_molaire": 4.2e-4, "energie_kJ_par_mol": 60.0}, True, True,
       "CO₂ (valorisation)", "recherche (sous-exploité)",
       0.45, "évite la chaleur de régénération en jouant sur l'humidité ambiante → énergie potentiellement bien "
             "plus basse pour la capture dans l'air ; débit et durabilité du sorbant à prouver"),
    _P("électrochimique (électro-swing / bascule de pH)",
       "capter : fixer puis relâcher le CO₂ par un cycle électrique (bascule de pH ou quinones)",
       {"type": "separation", "fraction_molaire": 4.2e-4, "energie_kJ_par_mol": 100.0}, True, True,
       "CO₂ (valorisation)", "recherche",
       0.45, "entraîné par l'ÉLECTRICITÉ (pas la chaleur) → se marie au renouvelable intermittent, modulable ; "
             "encore au laboratoire, électrodes à faire durer — piste prometteuse"),
    _P("altération accélérée / minéralisation (olivine, basalte)",
       "capter : broyer des silicates (olivine) qui réagissent avec le CO₂ en carbonate stable",
       {"type": "separation", "fraction_molaire": 4.2e-4, "energie_kJ_par_mol": 30.0}, True, True,
       "carbonate SOLIDE (puits permanent, zéro fuite)", "recherche (terrain)",
       0.5, "exploite l'énergie de RÉACTION naturelle (exothermique) → très peu d'énergie (broyage) ; donne "
            "directement un puits PERMANENT ; lent, à l'échelle géologique — copie l'altération des roches"),
    _P("BECCS (la biomasse capte, on stocke)",
       "capter : laisser la photosynthèse capter le CO₂, brûler la biomasse et capter le CO₂ concentré des fumées",
       {"type": "separation", "fraction_molaire": 0.12, "energie_kJ_par_mol": 120.0}, True, False,
       "CO₂ concentré (stockage)", "déployé (niche)",
       0.5, "délègue la capture DILUÉE (la plus chère) à la plante, gratuite et solaire ; on ne capte que le CO₂ "
            "déjà CONCENTRÉ à la combustion — conditionné à la biomasse durable et à sa surface"),
    _P("valorisation directe (CO₂ → carburant/matériau)",
       "capter : convertir le CO₂ capté en carburant de synthèse ou en matériau (minéralisation du béton)",
       {"type": "separation", "fraction_molaire": 0.12, "energie_kJ_par_mol": 120.0}, True, False,
       "produit (carburant, béton) — puits selon durée de vie", "émergent",
       0.4, "referme la boucle carbone SI l'énergie de conversion est décarbonée ; attention : un carburant "
            "re-brûlé n'est PAS un puits (neutre au mieux) — seul un matériau durable stocke vraiment"),
    _P("océan : alcalinité renforcée",
       "capter : ajouter de l'alcalinité (roche broyée) à l'océan pour qu'il absorbe plus de CO₂ atmosphérique",
       {"type": "separation", "fraction_molaire": 4.2e-4, "energie_kJ_par_mol": 40.0}, True, True,
       "carbone dissous (bicarbonate stable ~millénaire)", "recherche",
       0.4, "utilise l'immense capacité de l'océan comme puits ; énergie surtout pour broyer/transporter la "
            "roche ; effets écologiques à cadrer — piste à grande échelle mais incertaine"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER : sous le travail minimal de séparation d'un gaz dilué) ──
    _P("DAC « à 10 kJ/mol depuis l'air ambiant »",
       "capter : capture directe dans l'air (420 ppm) revendiquée à 10 kJ/mol",
       {"type": "separation", "fraction_molaire": 4.2e-4, "energie_kJ_par_mol": 10.0}, True, True,
       "CO₂", "revendication",
       0.3, "revendication SOUS le plancher R·T·ln(1/x) ≈ 19,3 kJ/mol à 420 ppm — à réfuter par le travail minimal"),
    _P("capture du CO₂ de l'air « sans énergie »",
       "capter : extraire le CO₂ de l'air ambiant sans aucun apport d'énergie",
       {"type": "separation", "fraction_molaire": 4.2e-4, "energie_kJ_par_mol": 0.0}, True, True,
       "CO₂", "revendication",
       0.25, "séparer un gaz dilué sans énergie ferait baisser l'entropie de mélange sans travail — impossible"),
]

_OBJECTIF_CO2 = ("Le but réel n'est pas d'« aspirer le CO₂ de l'air ambiant » (420 ppm : le composant est "
                 "ULTRA-dilué, le travail minimal par mole y est le PLUS élevé, ≈ 19,3 kJ/mol) quand on peut le "
                 "capter À LA SOURCE (fumées ~12 %, x 100–300× plus grand → minimum ≈ 5,3 kJ/mol). La DILUTION "
                 "est l'ennemi. Leviers : capter d'abord aux sources concentrées ; pour la capture dans l'air, "
                 "l'énergie réelle est dominée par la RÉGÉNÉRATION du sorbant (chaleur) → l'adosser à de la "
                 "chaleur fatale/solaire, ou régénérer autrement (humidité, électricité) ; et le PUITS compte "
                 "(minéralisation permanente vs stockage géologique vs valorisation). Chaque principe reste jugé "
                 "par le travail minimal de séparation.")
_LOI_CO2 = ("on ne sépare pas un composant dilué pour moins que R·T·ln(1/x) par mole (énergie de mélange) ; plus "
            "x est petit (air ambiant 420 ppm → ~19,3 kJ/mol) plus le minimum MONTE ; gains réels = capter là où "
            "c'est concentré (fumées), valoriser une chaleur/électricité gratuite pour la régénération, viser un "
            "puits stable (minéralisation/géologie)")

# La nature capte déjà le CO₂ : photosynthèse (solaire, dilué), biominéralisation, altération, sols, enzyme.
_STRATEGIES_NATURE_CO2 = [
    _Nature("photosynthèse (forêts, phytoplancton)",
            ["capture SOLAIRE du CO₂ dilué (gratuite)", "à l'échelle planétaire", "fixé en matière organique"],
            "déléguer la capture DILUÉE (la plus chère) à une machine solaire gratuite — le levier de BECCS"),
    _Nature("coccolithophores / coraux / coquilles (biominéralisation)",
            ["fixation du CO₂ en carbonate de calcium", "puits SOLIDE permanent", "catalysé par le vivant"],
            "transformer le CO₂ en minéral stable = puits sans fuite — le modèle de la minéralisation"),
    _Nature("altération des silicates (olivine, basalte)",
            ["réaction lente roche + CO₂ → carbonate", "puits géologique du cycle du carbone long",
             "énergie de réaction naturelle"],
            "le thermostat géologique de la Terre : l'altération accélérée ne fait que le HÂTER"),
    _Nature("tourbière / sol anoxique",
            ["stockage du carbone en matière organique non décomposée", "conservé des millénaires si anoxique"],
            "stocker le carbone en le soustrayant à la décomposition — garder le milieu privé d'oxygène"),
    _Nature("anhydrase carbonique (enzyme)",
            ["catalyse l'hydratation du CO₂ ~10⁶×", "accélère la capture sans la forcer"],
            "un catalyseur rend la capture du dilué RAPIDE sans en changer l'énergie — copier l'enzyme"),
]

enregistre(Domaine(
    nom=_CO2,
    aliases=frozenset(_ALIAS_CO2),
    objectif=_OBJECTIF_CO2,
    canaux=_CANAUX_CO2,
    principes=_PRINCIPES_CO2,
    strategies=_STRATEGIES_NATURE_CO2,
    loi=_LOI_CO2,
    extras={"fraction_co2_air": "≈ 4,2e-4 (420 ppm)", "travail_min_air_kJ_mol": "≈ 19,3 (420 ppm, 298 K)",
            "note_source": "aux fumées x ≈ 0,12 le minimum tombe à ≈ 5,3 kJ/mol — capter concentré d'abord"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  SIXIÈME DOMAINE : produire de l'eau potable de l'air (AWG). La loi est DÉJÀ couverte par le type `separation`
#  généralisé : extraire l'eau d'un air à humidité relative φ vaut au minimum R·T·ln(1/φ) par mole (φ = ACTIVITÉ
#  de la vapeur d'eau ; on réutilise `fraction_molaire = HR`). Aucune extension du juge. À φ → 0 (air sec) le
#  minimum DIVERGE : on ne tire pas d'eau d'un air parfaitement sec.
#  REFRAMING machine : le rendement dépend D'ABORD de l'humidité, pas de la techno. Leviers : opérer QUAND/OÙ
#  l'air est humide (nuit, côte, brouillard) ; ne pas refroidir tout l'air mais SORBER (capter la nuit humide,
#  relâcher au soleil le jour) ; là où le brouillard existe, l'INTERCEPTER est quasi gratuit (un filet).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_AWG = "eau_potable_air"
_ALIAS_AWG = {
    "produire de l eau de l air", "produire de l eau potable de l air", "generateur d eau atmospherique",
    "extraire l eau de l air", "recuperer l eau de l air", "capter l humidite de l air",
}

# ── « Canaux » : les mécanismes pour tirer l'eau de l'air ────────────────────────────────────────────────────────
_CANAUX_AWG = [
    Canal("refroidissement", "eau", "refroidir une surface SOUS le point de rosée pour condenser la vapeur",
          False, "simple mais on paie le refroidissement de TOUT l'air ; gratuit si un puits froid existe (sol, "
                 "nuit) ; compresseur = bruit"),
    Canal("sorption", "eau", "capter la vapeur sur un dessiccant/MOF la nuit, la relâcher au soleil le jour",
          True, "découple capture (air humide, nuit) et régénération (chaleur solaire, jour) → marche en climat "
                "SEC là où la condensation échoue ; le levier clé"),
    Canal("interception", "eau", "intercepter les gouttelettes déjà condensées du brouillard/de la rosée sur un filet",
          True, "quasi gratuit LÀ où le brouillard existe (côtes, montagnes) : pas de séparation, juste une "
                "collecte — mais conditionné à la présence de brouillard"),
    Canal("membrane", "eau", "transporter sélectivement la vapeur à travers une membrane (dessiccant liquide)",
          True, "compact ; l'énergie reste dans la régénération du dessiccant — à adosser à une chaleur fatale"),
]

# ── PRINCIPES candidats — chacun JUGÉ par le travail minimal de séparation (type `separation`, x = HR) ────────────
_PRINCIPES_AWG = [
    _P("condensation par refroidissement (référence)",
       "produire de l'eau : refroidir l'air humide sous le point de rosée, collecter le condensat",
       {"type": "separation", "fraction_molaire": 0.6, "energie_kJ_par_mol": 26.0}, False, False,
       "condensat (eau liquide)", "mature",
       0.6, "la référence : ~0,3–0,5 kWh/L par air modérément humide ; on refroidit tout l'air (irréversible, "
            "latente non récupérée) → loin du minimum ; échoue en air sec — la barre à descendre"),
    _P("sorption solaire (dessiccant régénéré au soleil)",
       "produire de l'eau : un dessiccant capte la vapeur la nuit, le soleil la relâche le jour, condensée à part",
       {"type": "separation", "fraction_molaire": 0.3, "energie_kJ_par_mol": 20.0}, True, True,
       "condensat", "émergent",
       0.55, "marche en climat SEC (capte à basse HR) et l'énergie est SOLAIRE (gratuite) → le levier « découpler "
             "capture et régénération » ; débit par cycle jour/nuit limité"),
    _P("MOF hygroscopique (récolte d'eau à basse humidité)",
       "produire de l'eau : un réseau métallo-organique (MOF) capte l'eau à 10–20 % HR, relâchée par une chaleur douce",
       {"type": "separation", "fraction_molaire": 0.2, "energie_kJ_par_mol": 15.0}, True, True,
       "condensat", "recherche (démonstrateurs désert)",
       0.5, "capte l'eau même en plein désert (HR très basse) ; réglable par chimie du MOF ; coût et débit du "
            "matériau à industrialiser — piste sous-exploitée qui repousse la limite d'humidité"),
    _P("filet à brouillard (interception)",
       "produire de l'eau : un maillage intercepte les gouttelettes du brouillard, l'eau ruisselle par gravité",
       {"type": "separation", "fraction_molaire": 0.98, "energie_kJ_par_mol": 0.3}, True, True,
       "eau ruisselée", "mature (déployé)",
       0.55, "quasi ZÉRO énergie (maillage passif) LÀ où le brouillard existe (côtes, altitude) ; ce n'est pas de "
            "la séparation mais une COLLECTE de gouttes déjà formées — conditionné au brouillard"),
    _P("condensation radiative nocturne",
       "produire de l'eau : une surface rayonne vers le ciel, descend sous le point de rosée, la rosée est collectée",
       {"type": "separation", "fraction_molaire": 0.9, "energie_kJ_par_mol": 0.5}, True, True,
       "rosée collectée", "connu (peu diffusé)",
       0.5, "puits = le ciel (gratuit) ; passif, silencieux ; débit modeste, exige un ciel dégagé et un air déjà "
            "humide la nuit — sous-exploité en complément"),
    _P("dessiccant liquide (saumure LiCl, régénération solaire/fatale)",
       "produire de l'eau : une saumure hygroscopique absorbe la vapeur, régénérée par chaleur, l'eau condensée à part",
       {"type": "separation", "fraction_molaire": 0.4, "energie_kJ_par_mol": 22.0}, True, True,
       "condensat", "émergent",
       0.5, "absorbe fort même à HR modérée ; l'énergie part dans la régénération de la saumure → l'adosser à une "
            "chaleur fatale/solaire ; corrosion à gérer"),
    _P("condenseur couplé au sol (puits froid géothermique)",
       "produire de l'eau : condenser l'air humide sur une surface refroidie par le sol (température stable)",
       {"type": "separation", "fraction_molaire": 0.7, "energie_kJ_par_mol": 8.0}, True, False,
       "condensat", "simple",
       0.5, "utilise le SOL comme puits froid gratuit (comme la grotte) → atteindre le point de rosée coûte peu ; "
            "conditionné à un sol assez frais et à un air assez humide"),
    _P("membrane à dessiccant (vapeur transportée sélectivement)",
       "produire de l'eau : une membrane laisse passer la vapeur d'eau, condensée du côté sec",
       {"type": "separation", "fraction_molaire": 0.5, "energie_kJ_par_mol": 18.0}, True, True,
       "condensat", "recherche",
       0.45, "compacte, sans pièce froide ; l'énergie reste dans le maintien du gradient/de la régénération — "
             "piste jeune à valider hors labo"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER : sous le travail minimal de séparation R·T·ln(1/HR)) ──
    _P("générateur d'eau « à 0,5 kJ/mol par 50 % d'humidité »",
       "produire de l'eau : extraire l'eau d'un air à 50 % HR revendiqué à 0,5 kJ/mol",
       {"type": "separation", "fraction_molaire": 0.5, "energie_kJ_par_mol": 0.5}, True, True,
       "eau", "revendication",
       0.3, "revendication SOUS le plancher R·T·ln(1/0,5) ≈ 1,72 kJ/mol — à réfuter par le travail minimal"),
    _P("eau d'un air TRÈS SEC (5 % HR) « aussi peu cher qu'à 80 % »",
       "produire de l'eau : extraire l'eau d'un air à 5 % HR pour seulement 2 kJ/mol",
       {"type": "separation", "fraction_molaire": 0.05, "energie_kJ_par_mol": 2.0}, True, True,
       "eau", "revendication",
       0.25, "à 5 % HR le plancher monte à R·T·ln(20) ≈ 7,4 kJ/mol : la SÉCHERESSE renchérit l'extraction — 2 kJ/mol "
             "est impossible (à air parfaitement sec, le minimum diverge)"),
]

_OBJECTIF_AWG = ("Le but réel n'est pas d'« arracher de l'eau à n'importe quel air » : le rendement dépend "
                 "D'ABORD de l'HUMIDITÉ relative (le travail minimal est R·T·ln(1/HR) par mole — il DIVERGE quand "
                 "l'air devient sec). Leviers : opérer QUAND/OÙ l'air est humide (nuit, côte, brouillard) ; ne pas "
                 "refroidir TOUT l'air mais SORBER (capter la nuit humide, régénérer au soleil le jour → marche "
                 "même en climat sec) ; là où le brouillard existe, l'INTERCEPTER est quasi gratuit (un filet) ; "
                 "viser un puits froid gratuit (sol, ciel nocturne) plutôt qu'un compresseur. Chaque principe "
                 "reste jugé par le travail minimal de séparation.")
_LOI_AWG = ("on ne condense pas l'eau de l'air pour moins que R·T·ln(1/HR) par mole (HR = humidité relative = "
            "activité de la vapeur) ; plus l'air est SEC plus le minimum MONTE (il diverge à HR → 0) ; gains "
            "réels = opérer à HR élevée, sorber plutôt que tout refroidir, puits froid gratuit (sol/ciel), "
            "intercepter le brouillard existant")

# La nature récolte déjà l'eau de l'air : scarabée du Namib, toile d'araignée, lézard cornu, rosée, cactus.
_STRATEGIES_NATURE_AWG = [
    _Nature("scarabée du Namib (récolte le brouillard sur son dos)",
            ["surface à motifs hydrophiles/hydrophobes", "gouttes qui grossissent puis roulent vers la bouche",
             "posture face au vent de brouillard"],
            "structurer la MOUILLABILITÉ d'une surface capte le brouillard sans énergie — copier le motif"),
    _Nature("toile d'araignée (capte les gouttelettes de brouillard)",
            ["fibres à nœuds périodiques", "gradient de Laplace qui rassemble les gouttes aux nœuds"],
            "la GÉOMÉTRIE des fibres (nœuds) collecte l'eau du brouillard — un levier de matériau, pas d'énergie"),
    _Nature("lézard cornu (Moloch) — l'eau remonte sur la peau",
            ["réseau de micro-canaux entre les écailles", "transport CAPILLAIRE de la rosée vers la bouche",
             "contre la gravité, sans muscle"],
            "des canaux capillaires acheminent l'eau collectée sans énergie — copier le transport passif"),
    _Nature("rosée nocturne sur les feuilles",
            ["refroidissement RADIATIF vers le ciel", "descente sous le point de rosée", "collecte par ruissellement"],
            "le ciel nocturne est un puits froid gratuit : rayonner, condenser, collecter — sans machine"),
    _Nature("cactus / épines coniques",
            ["gouttes captées sur des épines CONIQUES", "gradient de Laplace qui les pousse vers la base"],
            "une géométrie conique déplace les gouttes toute seule — le levier de forme, zéro énergie"),
]

enregistre(Domaine(
    nom=_AWG,
    aliases=frozenset(_ALIAS_AWG),
    objectif=_OBJECTIF_AWG,
    canaux=_CANAUX_AWG,
    principes=_PRINCIPES_AWG,
    strategies=_STRATEGIES_NATURE_AWG,
    loi=_LOI_AWG,
    extras={"humidite_relative_moteur": "le rendement dépend D'ABORD de l'humidité relative (HR), pas de la techno",
            "note_secheresse": "à HR très basse le travail minimal R·T·ln(1/HR) diverge — pas d'eau d'un air parfaitement sec"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  SEPTIÈME DOMAINE : se propulser. Nouvelle loi dure ajoutée au juge (L4) : la conservation de la QUANTITÉ DE
#  MOUVEMENT. Pour produire une poussée, il faut pousser sur QUELQUE CHOSE — éjecter de la masse/du rayonnement
#  OU s'appuyer sur un milieu/momentum externe. Un « moteur sans réaction » (EmDrive, Dean drive) est réfuté ;
#  l'éjection supraluminique aussi.
#  REFRAMING machine : on ne CONTOURNE pas cette loi (impossible), on CHOISIT la meilleure réaction. Dans le VIDE
#  sans milieu, il FAUT emporter de la masse → maximiser la vitesse d'éjection (impulsion spécifique) pour en
#  emporter moins ; sinon emprunter un momentum qu'on ne porte PAS (lumière du Soleil, laser depuis le sol,
#  fronde gravitationnelle). S'il y a un milieu (air, eau, sol, champ), pousser dessus = zéro ergol.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_PROP = "propulsion"
_ALIAS_PROP = {
    "se propulser", "propulsion spatiale", "propulser un engin", "avancer dans le vide",
    "propulser une fusee", "propulsion sans ergol", "se deplacer dans l espace",
}

# ── « Canaux » : ce sur quoi on POUSSE pour avancer ──────────────────────────────────────────────────────────────
_CANAUX_PROP = [
    Canal("ejection de masse", "quantite_mouvement", "emporter puis éjecter de la masse/du rayonnement (fusée, ion, photon)",
          False, "la SEULE option dans le vide sans milieu ; le levier = maximiser la vitesse d'éjection (Isp) "
                 "pour emporter moins d'ergol ; bruit/chaleur du jet"),
    Canal("milieu fluide", "quantite_mouvement", "pousser sur l'air ou l'eau (hélice, réacteur, nage)",
          False, "zéro ergol emporté (le milieu EST la réaction) ; inutilisable dans le vide"),
    Canal("momentum externe", "quantite_mouvement", "emprunter un momentum qu'on ne porte pas (voile solaire, laser, fronde gravitationnelle)",
          True, "zéro ergol : la lumière/le champ/la planète fournit l'impulsion ; poussée faible ou source "
                "externe requise — sous-exploité pour l'espace lointain"),
    Canal("appui solide", "quantite_mouvement", "pousser sur le sol par friction ou champ (roue, patte, sustentation magnétique)",
          True, "très efficace au sol ; le rail/la route fournissent la réaction ; hors sol, inopérant"),
]

# ── PRINCIPES candidats — chacun JUGÉ par la conservation de la quantité de mouvement (type `propulsion`, L4) ─────
_PRINCIPES_PROP = [
    _P("fusée chimique (référence, vide)",
       "se propulser : brûler un ergol et éjecter les gaz à grande vitesse",
       {"type": "propulsion", "poussee_nette": 1e6, "ejecte_masse_ou_rayonnement": True,
        "vitesse_ejection_m_s": 4500}, False, False,
       "gaz éjectés (masse emportée)", "mature",
       0.6, "forte poussée MAIS vitesse d'éjection faible → il faut emporter ÉNORMÉMENT d'ergol (équation de "
            "Tsiolkovski) ; la référence pour décoller — à dépasser en Isp pour l'espace lointain"),
    _P("moteur ionique / à plasma",
       "se propulser : accélérer des ions par un champ électrique et les éjecter à très grande vitesse",
       {"type": "propulsion", "poussee_nette": 0.2, "ejecte_masse_ou_rayonnement": True,
        "vitesse_ejection_m_s": 30000}, True, True,
       "ions éjectés", "mature (spatial)",
       0.6, "vitesse d'éjection ~7× la chimie → emporte BEAUCOUP moins d'ergol pour la même mission ; poussée "
            "minuscule (accélération lente) → idéal espace lointain, pas le décollage — le levier « Isp élevé »"),
    _P("voile solaire (momentum de la lumière)",
       "se propulser : une grande voile réfléchit la lumière du Soleil, dont l'impulsion pousse le vaisseau",
       {"type": "propulsion", "poussee_nette": 0.01, "milieu_externe": True}, True, True,
       "aucun ergol (momentum externe : photons du Soleil)", "démontré (niche)",
       0.55, "ZÉRO ergol emporté : c'est le Soleil qui fournit l'impulsion ; poussée très faible mais CONTINUE et "
             "gratuite → vitesse cumulée élevée sur la durée ; s'affaiblit loin du Soleil"),
    _P("propulsion laser (voile poussée depuis le sol)",
       "se propulser : un laser puissant reste au sol/en orbite et pousse une voile légère embarquée",
       {"type": "propulsion", "poussee_nette": 0.1, "milieu_externe": True}, True, True,
       "aucun ergol embarqué (momentum externe : le laser)", "recherche (Breakthrough Starshot)",
       0.45, "l'ÉNERGIE reste à la maison → le vaisseau n'emporte presque rien → accélérations extrêmes possibles "
             "pour une sonde minuscule ; exige un laser gigantesque et un pointage parfait — sous-exploité"),
    _P("turboréacteur / hélice (atmosphère)",
       "se propulser : accélérer l'air vers l'arrière pour avancer (réacteur, hélice)",
       {"type": "propulsion", "poussee_nette": 5e4, "milieu_externe": True}, False, True,
       "aucun ergol de réaction (le milieu = l'air)", "mature",
       0.5, "n'emporte pas la masse de réaction (l'air est gratuit) → très efficace DANS l'atmosphère ; "
            "totalement inopérant dans le vide — apparier au milieu"),
    _P("fronde gravitationnelle (assistance gravitationnelle)",
       "se propulser : passer près d'une planète pour emprunter une part de sa quantité de mouvement orbitale",
       {"type": "propulsion", "poussee_nette": 1.0, "milieu_externe": True}, True, True,
       "aucun ergol (momentum emprunté à la planète)", "mature (missions lointaines)",
       0.5, "gain de vitesse SANS ergol en volant la quantité de mouvement d'une planète (conservée à l'échelle "
            "du système) ; conditionné aux alignements et aux fenêtres de tir — le levier « momentum externe »"),
    _P("voile magnétique / magnétoplasma (vent solaire)",
       "se propulser : un champ magnétique embarqué dévie le vent solaire, qui pousse le vaisseau",
       {"type": "propulsion", "poussee_nette": 1.0, "milieu_externe": True}, True, True,
       "aucun ergol (momentum externe : vent solaire / champ planétaire)", "recherche",
       0.4, "s'appuie sur le plasma interplanétaire ou le champ d'une planète → zéro ergol ; poussée faible et "
            "conditionnée à la présence de plasma/champ — piste peu explorée"),
    _P("propulsion nucléaire thermique",
       "se propulser : un réacteur chauffe un gaz léger (hydrogène) éjecté à haute vitesse",
       {"type": "propulsion", "poussee_nette": 5e5, "ejecte_masse_ou_rayonnement": True,
        "vitesse_ejection_m_s": 9000}, False, False,
       "hydrogène éjecté", "démonstrateur",
       0.45, "vitesse d'éjection ~2× la chimie avec une forte poussée → compromis pour l'espace habité ; "
             "contraintes de sûreté nucléaire — emporte tout de même sa masse de réaction"),
    _P("fusée à photons",
       "se propulser : éjecter des photons (lumière) dont l'impulsion propulse le vaisseau",
       {"type": "propulsion", "poussee_nette": 1e-6, "ejecte_masse_ou_rayonnement": True,
        "vitesse_ejection_m_s": 2.99e8}, True, True,
       "photons éjectés (vitesse d'éjection = c, l'ultime)", "théorique",
       0.3, "vitesse d'éjection = c → impulsion spécifique ULTIME (emporte le minimum de « masse ») ; MAIS poussée "
            "infime pour une énergie colossale → horizon lointain, strictement dans les lois"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER : conservation de la quantité de mouvement / v ≤ c) ──
    _P("moteur sans réaction (type EmDrive)",
       "se propulser : produire une poussée nette dans le vide sans éjecter de masse ni s'appuyer sur rien",
       {"type": "propulsion", "poussee_nette": 1.0, "milieu_externe": False,
        "ejecte_masse_ou_rayonnement": False}, True, True,
       "— (aucune réaction)", "revendication",
       0.3, "poussée sans réaction = viole la conservation de la quantité de mouvement — à réfuter (EmDrive/Dean)"),
    _P("éjection supraluminique",
       "se propulser : éjecter la masse de réaction plus vite que la lumière pour une impulsion spécifique infinie",
       {"type": "propulsion", "poussee_nette": 1.0, "ejecte_masse_ou_rayonnement": True,
        "vitesse_ejection_m_s": 3.0e8}, True, True,
       "masse éjectée", "revendication",
       0.25, "vitesse d'éjection > c = impossible (relativité)"),
]

_OBJECTIF_PROP = ("Le but réel n'est pas de « trouver un moteur qui avance tout seul » (impossible : il faut "
                  "pousser sur QUELQUE CHOSE) mais de CHOISIR la meilleure réaction. S'il y a un milieu (air, eau, "
                  "sol, champ), pousser dessus = zéro ergol emporté. Dans le VIDE sans milieu, il FAUT emporter de "
                  "la masse → maximiser la vitesse d'éjection (impulsion spécifique) pour en emporter moins ; ou "
                  "EMPRUNTER un momentum qu'on ne porte pas (lumière du Soleil, laser depuis le sol, fronde "
                  "gravitationnelle). Chaque principe reste jugé par la conservation de la quantité de mouvement.")
_LOI_PROP = ("conservation de la quantité de mouvement (3e loi de Newton) : pas de poussée nette sans réaction — "
             "éjecter de la masse/du rayonnement, s'appuyer sur un milieu, ou emprunter un momentum externe ; la "
             "vitesse d'éjection ≤ c ; gains réels = apparier au milieu, maximiser l'impulsion spécifique, "
             "emprunter un momentum gratuit (lumière/planète)")

# La nature se propulse par réaction (calmar), en poussant le fluide (poisson) ou le sol (serpent), ou emprunte le vent.
_STRATEGIES_NATURE_PROP = [
    _Nature("calmar / poulpe (jet d'eau)",
            ["remplir puis EXPULSER de l'eau", "poussée par réaction (masse éjectée)",
             "orientation du siphon"],
            "la fusée biologique : éjecter une masse pour avancer — le principe de la réaction pure"),
    _Nature("poisson / oiseau (pousser le fluide)",
            ["nageoires/ailes qui accélèrent l'eau/l'air vers l'arrière", "le milieu fournit la réaction"],
            "pousser sur le milieu = avancer sans rien emporter — inapplicable dans le vide"),
    _Nature("serpent / ver (pousser le sol)",
            ["friction directionnelle contre le substrat", "le sol fournit la réaction"],
            "s'appuyer sur le solide : la réaction vient de la route, pas d'un ergol"),
    _Nature("samare (graine ailée d'érable) / pissenlit",
            ["capte le momentum du VENT extérieur", "géométrie qui maximise la portance/traînée"],
            "emprunter le momentum de l'air en mouvement — zéro énergie propre, comme la voile"),
    _Nature("araignée « ballooning » (vol par fil de soie)",
            ["fil de soie captant le vent/le champ électrique atmosphérique", "s'élève sans muscle propulsif"],
            "emprunter un momentum/champ externe pour voyager loin — le levier de la voile, en vivant"),
]

enregistre(Domaine(
    nom=_PROP,
    aliases=frozenset(_ALIAS_PROP),
    objectif=_OBJECTIF_PROP,
    canaux=_CANAUX_PROP,
    principes=_PRINCIPES_PROP,
    strategies=_STRATEGIES_NATURE_PROP,
    loi=_LOI_PROP,
    extras={"regle_or": "pour avancer il faut pousser sur quelque chose : masse éjectée, milieu, ou momentum externe",
            "vide_note": "dans le vide sans milieu, il FAUT éjecter de la masse/du rayonnement — pas d'échappatoire"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  HUITIÈME DOMAINE : éclairer. Nouvelle loi dure au juge (L5) : l'EFFICACITÉ LUMINEUSE ≤ 683 lm/W (l'œil répond
#  au maximum à 555 nm ; au-delà, il faudrait > 100 % de rendement radiant). Une lampe revendiquant plus est
#  réfutée. La lumière BLANCHE à bon rendu plafonne plus bas (~300–350 lm/W) — noté au domaine, pas réfuté (c'est
#  fonction du spectre, pas une violation certaine).
#  REFRAMING machine : le but n'est pas de « produire de la lumière » mais de METTRE des lumens là où l'ŒIL en a
#  besoin, aux longueurs d'onde qu'il voit. Leviers : n'émettre que le VISIBLE (aucun watt en IR/UV) ; DIRIGER la
#  lumière (tâche, optique) au lieu d'inonder ; couleur ADAPTÉE (monochromatique là où le rendu n'importe pas) ;
#  et surtout — le lumen le moins cher est celui qu'on NE génère PAS (lumière du jour guidée).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_ECLAIRAGE = "eclairage"
_ALIAS_ECLAIRAGE = {
    "eclairer", "produire de la lumiere", "eclairer une piece", "eclairage efficace",
    "s eclairer", "eclairer un espace", "eclairer sans gaspiller",
}

# ── « Canaux » : les leviers d'un éclairage efficace ─────────────────────────────────────────────────────────────
_CANAUX_ECLAIRAGE = [
    Canal("efficacite spectrale", "lumiere", "n'émettre QUE les longueurs d'onde visibles (aucun watt en IR/UV)",
          True, "l'incandescence gaspille ~95 % en IR (chaleur) ; une source « froide » qui n'émet que le visible "
                "s'approche du plafond — le levier premier"),
    Canal("direction", "lumiere", "diriger les lumens là où l'œil regarde (optique, éclairage de tâche)",
          True, "inonder une pièce pour éclairer un livre gaspille l'essentiel ; l'optique met la lumière au bon "
                "endroit — souvent plus de gain que d'améliorer la source"),
    Canal("couleur adaptee", "lumiere", "monochromatique là où le rendu des couleurs n'importe pas (rue), large sinon",
          True, "une lumière monochromatique à 555 nm approche 683 lm/W mais rend mal les couleurs → parfait pour "
                "un lampadaire, inadapté à un salon : apparier le spectre au besoin"),
    Canal("lumiere naturelle", "lumiere", "guider la lumière du JOUR (puits de lumière, fibres) au lieu d'en générer",
          True, "le lumen le moins cher est celui qu'on ne produit pas : zéro électricité aux heures de jour — "
                "le levier le plus sous-exploité en bâtiment"),
]

# ── PRINCIPES candidats — chacun JUGÉ par l'efficacité lumineuse (type `eclairage`, ≤ 683 lm/W) ──────────────────
_PRINCIPES_ECLAIRAGE = [
    _P("LED blanche (référence)",
       "éclairer : diode électroluminescente blanche (bleu + luminophore)",
       {"type": "eclairage", "efficacite_lm_par_W": 150.0}, True, True,
       "lumière visible", "mature (dominant)",
       0.65, "~150 lm/W en pratique, ~10× l'incandescence ; marge encore réelle vers le plafond blanc (~300–350) ; "
             "la référence à dépasser en spectre et en optique"),
    _P("LED de laboratoire haute efficacité",
       "éclairer : LED blanche optimisée (record de laboratoire)",
       {"type": "eclairage", "efficacite_lm_par_W": 330.0}, True, True,
       "lumière visible", "recherche",
       0.5, "~330 lm/W en labo → approche le plafond de la lumière BLANCHE (~350) ; industrialiser le spectre et "
            "la thermique reste le verrou — sous le plafond physique de 683"),
    _P("sodium basse pression (monochromatique)",
       "éclairer : lampe à vapeur de sodium émettant une raie jaune quasi monochromatique",
       {"type": "eclairage", "efficacite_lm_par_W": 200.0}, True, True,
       "lumière jaune (589 nm)", "mature (déclin)",
       0.45, "très efficace CAR monochromatique (peu de spectre gaspillé) MAIS rend les couleurs en noir et blanc "
             "→ réservé aux routes ; illustre « couleur adaptée au besoin »"),
    _P("fluorescent (tube)",
       "éclairer : décharge dans un gaz excitant un luminophore",
       {"type": "eclairage", "efficacite_lm_par_W": 90.0}, True, False,
       "lumière visible", "mature (déclin)",
       0.4, "~90 lm/W, supplanté par la LED ; contient du mercure — en voie de remplacement"),
    _P("incandescence (référence basse)",
       "éclairer : filament chauffé au blanc (rayonnement thermique)",
       {"type": "eclairage", "efficacite_lm_par_W": 15.0}, False, True,
       "lumière + BEAUCOUP d'IR (chaleur)", "obsolète",
       0.5, "~15 lm/W : ~95 % de l'énergie part en IR invisible → l'archétype du gaspillage spectral, la barre "
            "basse qui montre le levier « n'émettre que le visible »"),
    _P("laser blanc (RGB) / éclairage laser",
       "éclairer : combiner des lasers rouge/vert/bleu en lumière blanche, faisceau dirigeable",
       {"type": "eclairage", "efficacite_lm_par_W": 250.0}, True, True,
       "lumière visible dirigée", "émergent (phares, projection)",
       0.4, "spectre choisi (peu de gaspillage) ET directivité extrême (optique) → double levier ; sécurité "
            "oculaire et coût à maîtriser — piste pour l'éclairage ciblé"),
    _P("électroluminescence directe (QLED / OLED efficace)",
       "éclairer : émission directe par des points quantiques/molécules, sans luminophore de conversion",
       {"type": "eclairage", "efficacite_lm_par_W": 200.0}, True, True,
       "lumière visible", "recherche",
       0.4, "évite la perte de conversion du luminophore ; spectre réglable finement → viser le plafond blanc en "
            "gaspillant moins ; durée de vie des émetteurs à prouver"),
    _P("lumière du jour guidée (puits de lumière, fibres optiques)",
       "éclairer : capter la lumière du soleil et la conduire à l'intérieur (conduits, fibres) sans électricité",
       {"type": "eclairage"}, True, True,
       "lumière solaire (zéro électricité de jour)", "mature (sous-exploité)",
       0.55, "le lumen le moins cher est celui qu'on NE génère PAS : de jour, zéro watt électrique ; conditionné à "
             "l'accès au soleil et à des conduits courts — le plus gros gain souvent ignoré en bâtiment"),
    _P("éclairage de tâche + détection de présence",
       "éclairer : n'éclairer QUE la zone utile et QUE quand quelqu'un est présent (optique + capteurs)",
       {"type": "eclairage"}, True, True,
       "lumière visible ciblée", "mature (sous-exploité)",
       0.5, "le gain n'est pas dans la source mais dans NE PAS éclairer l'inutile (pièces vides, plafonds) ; "
            "souvent plus d'économie que de changer d'ampoule — le levier « direction + à la demande »"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER : efficacité lumineuse > 683 lm/W) ──
    _P("LED « à 800 lm/W »",
       "éclairer : LED revendiquant 800 lm par watt électrique",
       {"type": "eclairage", "efficacite_lm_par_W": 800.0}, True, True,
       "lumière", "revendication",
       0.3, "800 > 683 lm/W (maximum spectral à 555 nm) — à réfuter par l'efficacité lumineuse maximale"),
    _P("ampoule « à 1000 lm/W »",
       "éclairer : ampoule revendiquant 1000 lm par watt électrique",
       {"type": "eclairage", "efficacite_lm_par_W": 1000.0}, True, True,
       "lumière", "revendication",
       0.25, "1000 > 683 lm/W = impossible (il faudrait un rendement radiant supérieur à 100 %)"),
]

_OBJECTIF_ECLAIRAGE = ("Le but réel n'est pas de « produire de la lumière » mais de METTRE des lumens là où l'ŒIL "
                       "en a besoin, aux longueurs d'onde qu'il voit (l'œil culmine à 555 nm ; le plafond absolu "
                       "est 683 lm/W, la lumière blanche à bon rendu ~300–350). Leviers : n'émettre que le VISIBLE "
                       "(l'incandescence gaspille ~95 % en IR) ; DIRIGER la lumière (optique, tâche) au lieu "
                       "d'inonder ; couleur ADAPTÉE (monochromatique là où le rendu n'importe pas) ; et surtout, "
                       "le lumen le moins cher est celui qu'on NE génère PAS (lumière du jour guidée, ne pas "
                       "éclairer l'inutile). Chaque principe reste jugé par l'efficacité lumineuse maximale.")
_LOI_ECLAIRAGE = ("l'efficacité lumineuse ≤ 683 lm/W (maximum spectral à 555 nm, rendement radiant 100 %) ; la "
                  "lumière blanche à bon rendu plafonne plus bas (~300–350 lm/W) ; gains réels = n'émettre que le "
                  "visible, diriger les lumens, adapter le spectre au besoin, et d'abord ne pas générer (jour, "
                  "présence)")

# La nature éclaire à froid (luciole), recycle les photons (tapetum), n'éclaire qu'à la demande (plancton).
_STRATEGIES_NATURE_ECLAIRAGE = [
    _Nature("luciole (bioluminescence froide)",
            ["réaction chimique émettant surtout du VISIBLE", "quasi aucune chaleur (lumière froide)",
             "rendement quantique élevé"],
            "n'émettre que le visible, sans gaspillage thermique — le levier de l'efficacité spectrale"),
    _Nature("tapetum lucidum (œil nocturne du chat)",
            ["couche réfléchissante derrière la rétine", "renvoie les photons non absorbés pour un 2e passage"],
            "RECYCLER la lumière (la faire repasser) plutôt que d'en produire plus — voir mieux à énergie égale"),
    _Nature("plancton / champignon bioluminescent (lumière à la demande)",
            ["émission déclenchée (stimulus, rythme)", "pas de lumière quand elle est inutile"],
            "n'éclairer QUE quand c'est utile — le levier « à la demande », zéro lumen gaspillé"),
    _Nature("feuille / structures qui guident la lumière",
            ["conduits qui amènent la lumière aux cellules utiles", "diffusion contrôlée"],
            "GUIDER la lumière vers la cible plutôt que la disperser — le levier de la direction"),
]

enregistre(Domaine(
    nom=_ECLAIRAGE,
    aliases=frozenset(_ALIAS_ECLAIRAGE),
    objectif=_OBJECTIF_ECLAIRAGE,
    canaux=_CANAUX_ECLAIRAGE,
    principes=_PRINCIPES_ECLAIRAGE,
    strategies=_STRATEGIES_NATURE_ECLAIRAGE,
    loi=_LOI_ECLAIRAGE,
    extras={"plafond_lm_par_W": "683 lm/W (monochromatique 555 nm) ; lumière blanche à bon rendu ~300–350 lm/W",
            "note": "le lumen le moins cher est celui qu'on ne génère pas (jour guidé, ne pas éclairer l'inutile)"},
))


if __name__ == "__main__":
    print("OBJECTIF RÉEL :", objectif_reel("rafraichir une piece"), "\n")
    d = decompose("rafraichir une piece")
    print("CANAUX DU CORPS :")
    for c in d["canaux"]:
        print(f"  - {c.canal:12s} [{c.grandeur}] silencieux={c.silencieux} : {c.levier}")
    print("\nPRINCIPES JUGÉS :")
    for e in principes()["liste"]:
        print(f"  - {e['nom']:52s} {e['atome'].statut.upper():11s} | {e['verdict_physique'][:60]}")
    print("\nBESOIN INCONNU :", decompose("faire pousser des plantes")["statut"])
