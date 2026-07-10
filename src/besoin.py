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
