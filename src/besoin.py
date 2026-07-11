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


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  NEUVIÈME DOMAINE : calculer à basse énergie — au cœur de la vision Provara (l'IA légère). Nouvelle loi dure au
#  juge (L6) : la limite de LANDAUER (effacer un bit dissipe au moins k·T·ln2 ≈ 2,87e-21 J à 300 K). Une machine
#  qui prétend effacer des bits pour moins est réfutée. Les puces actuelles sont ~10⁴–10⁶× AU-DESSUS → l'immense
#  marge est réelle, ce n'est pas le mur physique qui limite aujourd'hui.
#  REFRAMING machine : le but n'est pas la VITESSE brute mais le calcul PAR JOULE. Leviers : (a) ne pas EFFACER
#  d'information inutilement (calcul réversible/adiabatique échappe entièrement à Landauer — le plus profond) ;
#  (b) ne pas DÉPLACER les bits (le vrai coût aujourd'hui est le transport des données, pas le calcul) ;
#  (c) moins d'OPÉRATIONS (algorithmes, matériel spécialisé — le gain court terme) ; (d) calcul froid (k·T ∝ T).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_CALCUL = "calcul"
_ALIAS_CALCUL = {
    "calculer efficacement", "reduire l energie du calcul", "calculer a basse consommation",
    "calcul econome en energie", "reduire la consommation d un ordinateur", "calcul basse consommation",
}

# ── « Canaux » : les leviers d'un calcul économe ─────────────────────────────────────────────────────────────────
_CANAUX_CALCUL = [
    Canal("ne pas effacer", "information", "calculer sans effacer d'information (logique réversible/adiabatique)",
          True, "Landauer ne coûte QUE sur l'effacement → un calcul réversible peut en principe descendre bien "
                "plus bas ; verrou = surcoût de complexité et de vitesse — le levier le plus profond"),
    Canal("ne pas deplacer", "information", "calculer LÀ où sont les données (in-memory, près du capteur)",
          True, "aujourd'hui l'énergie part surtout à DÉPLACER les bits (mémoire↔calcul), pas à les calculer → "
                "rapprocher calcul et données est le plus gros gain court terme"),
    Canal("moins d operations", "information", "réduire le nombre d'opérations (algorithme, matériel spécialisé)",
          True, "un meilleur algorithme ou un circuit dédié fait la même tâche en moins d'opérations → très loin "
                "du mur physique, l'essentiel des gains atteignables"),
    Canal("basse temperature", "information", "calculer à froid (k·T·ln2 diminue avec T) ou en supraconducteur",
          False, "le plancher de Landauer baisse avec la température ; les circuits supraconducteurs dissipent "
                 "très peu ; coût = le refroidissement lui-même — à réserver aux grands centres"),
]

# ── PRINCIPES candidats — chacun JUGÉ par la limite de Landauer (type `calcul`, ≥ k·T·ln2 par bit effacé) ────────
_PRINCIPES_CALCUL = [
    _P("CMOS numérique actuel (référence)",
       "calculer : logique CMOS irréversible, ~1e-17 J par opération de bit",
       {"type": "calcul", "energie_par_bit_efface_J": 1e-17, "t_K": 300}, True, True,
       "chaleur dissipée", "mature (dominant)",
       0.65, "~10⁴× au-dessus de Landauer → l'énorme marge est réelle ; l'énergie réelle part surtout dans les "
             "fuites et le déplacement des données, pas dans la limite physique — la référence à descendre"),
    _P("calcul sous-seuil (basse tension)",
       "calculer : faire fonctionner les transistors sous la tension de seuil, ~1e-18 J/bit",
       {"type": "calcul", "energie_par_bit_efface_J": 1e-18, "t_K": 300}, True, True,
       "chaleur", "mature (basse conso)",
       0.55, "l'énergie de commutation ∝ tension² → baisser la tension économe énormément ; verrou = lenteur et "
             "sensibilité au bruit — le levier « baisser la tension » déjà exploité en IoT"),
    _P("calcul réversible / adiabatique",
       "calculer : logique qui n'efface pas d'information (récupère la charge au lieu de la dissiper)",
       {"type": "calcul", "energie_par_bit_efface_J": 1e-20, "t_K": 300}, True, True,
       "chaleur minime (pas d'effacement)", "recherche",
       0.5, "en n'EFFAÇANT pas, échappe en principe à la limite de Landauer → plancher bien plus bas ; surcoût de "
            "portes et de vitesse à maîtriser — le levier le plus profond, sous-exploité"),
    _P("calcul in-memory (près de la mémoire)",
       "calculer : effectuer l'opération DANS la mémoire pour éviter de transporter les données",
       {"type": "calcul", "energie_par_bit_efface_J": 5e-18, "t_K": 300}, True, True,
       "chaleur", "émergent",
       0.55, "attaque le VRAI coût actuel : déplacer un bit entre mémoire et processeur coûte ~100× l'opération "
             "elle-même → calculer sur place est le plus gros levier court terme"),
    _P("calcul neuromorphique / événementiel (spikes)",
       "calculer : circuits qui ne consomment QUE lors d'événements (comme des neurones), pour tâches approximatives",
       {"type": "calcul", "energie_par_bit_efface_J": 1e-18, "t_K": 300}, True, True,
       "chaleur (activité éparse)", "émergent",
       0.5, "ne dépense QUE quand il se passe quelque chose (activité éparse) et tolère l'approximation → très "
            "économe pour la perception/l'inférence — s'inspire du cerveau (le levier « à la demande »)"),
    _P("calcul analogique",
       "calculer : effectuer l'opération dans la physique du circuit (courants, charges) plutôt qu'en bits",
       {"type": "calcul", "energie_par_bit_efface_J": 1e-18, "t_K": 300}, True, True,
       "chaleur", "recherche (regain)",
       0.45, "une addition/multiplication « gratuite » dans la loi d'Ohm/Kirchhoff, sans effacer de bits ; "
             "précision limitée → pour l'approximatif (IA, filtrage) ; regain d'intérêt sous-exploité"),
    _P("logique supraconductrice (SFQ, cryogénique)",
       "calculer : logique à quantum de flux unique, dissipant très peu, à basse température",
       {"type": "calcul", "energie_par_bit_efface_J": 1e-19, "t_K": 4}, True, True,
       "chaleur minime (mais refroidissement à payer)", "recherche",
       0.4, "commutation à très basse énergie ET k·T·ln2 plus bas à 4 K ; MAIS il faut PAYER le refroidissement "
            "cryogénique → gagnant surtout à grande échelle — le levier « froid »"),
    _P("spintronique / logique magnétique",
       "calculer : coder l'information dans le spin (aimantation), non-volatile, faible énergie de commutation",
       {"type": "calcul", "energie_par_bit_efface_J": 1e-18, "t_K": 300}, True, True,
       "chaleur", "recherche",
       0.4, "non-volatile (zéro énergie au repos, pas de rafraîchissement) et commutation économe ; maturité des "
            "matériaux à prouver — piste pour la mémoire-calcul basse conso"),
    _P("calcul photonique",
       "calculer : effectuer certaines opérations (produits matriciels) avec de la lumière",
       {"type": "calcul", "energie_par_bit_efface_J": 5e-18, "t_K": 300}, True, True,
       "chaleur", "émergent",
       0.4, "très rapide et peu dissipatif pour l'algèbre linéaire (cœur de l'IA) ; conversion optique/électrique "
            "coûteuse aux interfaces — piste ciblée, pas universelle"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER : sous la limite de Landauer) ──
    _P("effacement de bit « à 1e-23 J » (300 K)",
       "calculer : machine irréversible effaçant un bit pour 1e-23 J à température ambiante",
       {"type": "calcul", "energie_par_bit_efface_J": 1e-23, "t_K": 300}, True, True,
       "—", "revendication",
       0.3, "1e-23 J < limite de Landauer (~2,87e-21 J à 300 K) — à réfuter par le 2nd principe (Landauer)"),
    _P("calcul irréversible « à énergie nulle »",
       "calculer : effacer des bits sans dissiper aucune énergie",
       {"type": "calcul", "energie_par_bit_efface_J": 0.0, "t_K": 300}, True, True,
       "—", "revendication",
       0.25, "effacer de l'information sans dissipation ferait baisser l'entropie sans compensation — impossible"),
]

_OBJECTIF_CALCUL = ("Le but réel n'est pas la VITESSE brute mais le calcul PAR JOULE. Le plancher physique est la "
                    "limite de Landauer (≥ k·T·ln2 par bit EFFACÉ, ≈ 2,87e-21 J à 300 K) — mais les puces "
                    "actuelles sont ~10⁴–10⁶× au-dessus, donc le mur n'est PAS Landauer aujourd'hui. Leviers : ne "
                    "pas EFFACER d'information inutilement (calcul réversible/adiabatique échappe à Landauer) ; ne "
                    "pas DÉPLACER les bits (le vrai coût actuel est le transport, pas le calcul → in-memory) ; "
                    "moins d'OPÉRATIONS (algorithmes, matériel spécialisé, événementiel) ; calculer FROID (k·T ∝ "
                    "T). Chaque principe reste jugé par la limite de Landauer.")
_LOI_CALCUL = ("effacer un bit d'information dissipe au moins k·T·ln2 (limite de Landauer, ≈ 2,87e-21 J à 300 K) ; "
               "le calcul réversible qui n'efface pas échappe à ce plancher ; gains réels = ne pas effacer, ne pas "
               "déplacer les données, moins d'opérations, calculer à basse tension/température")

# La nature calcule à ~20 W (cerveau) : analogique, événementiel, en mémoire, au capteur.
_STRATEGIES_NATURE_CALCUL = [
    _Nature("cerveau humain (~20 W pour 10¹¹ neurones)",
            ["calcul ANALOGIQUE massivement parallèle", "événementiel (impulsions seulement quand utile)",
             "mémoire et calcul au MÊME endroit (synapses)"],
            "analogique + événementiel + en-mémoire : la cognition à ~20 W écrase le numérique — les 3 leviers réunis"),
    _Nature("rétine (pré-traitement au capteur)",
            ["extraction de contours/mouvement AVANT transmission", "n'envoie au cerveau que l'utile"],
            "calculer AU capteur et ne transmettre que l'essentiel — ne pas déplacer les données brutes"),
    _Nature("ADN (stockage d'information ultra-dense)",
            ["densité d'information proche de la molécule", "conservation passive à très basse énergie"],
            "stocker l'information dense et sans énergie de maintien — le levier du « repos gratuit »"),
    _Nature("fourmilière / essaim (calcul distribué émergent)",
            ["règles locales simples", "solution GLOBALE émergente (chemins, tri) sans contrôleur central"],
            "résoudre collectivement par des règles locales économes — pas de calcul central coûteux"),
]

enregistre(Domaine(
    nom=_CALCUL,
    aliases=frozenset(_ALIAS_CALCUL),
    objectif=_OBJECTIF_CALCUL,
    canaux=_CANAUX_CALCUL,
    principes=_PRINCIPES_CALCUL,
    strategies=_STRATEGIES_NATURE_CALCUL,
    loi=_LOI_CALCUL,
    extras={"limite_landauer_J_bit": "≈ 2,87e-21 J/bit effacé à 300 K (k·T·ln2)",
            "note": "les puces actuelles sont ~10⁴–10⁶× au-dessus ; le vrai coût aujourd'hui est de DÉPLACER les bits"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  DIXIÈME DOMAINE : communiquer / transmettre de l'information. Nouvelle loi dure au juge (L7) : la limite de
#  SHANNON — le débit sans erreur ≤ B·log₂(1 + S/N). Un débit revendiqué au-dessus de la capacité est réfuté.
#  REFRAMING machine : le but n'est pas de « crier plus fort » (la capacité ne croît que LOGARITHMIQUEMENT avec
#  le rapport signal/bruit) mais de livrer des bits fiables par joule et par Hz. Leviers : élargir la BANDE
#  (capacité LINÉAIRE en B → bien plus rentable que la puissance) ; se rapprocher/relayer (S/N chute en 1/d²) ;
#  bon CODAGE (approcher la capacité) et COMPRESSER la source (ne pas transmettre de bits redondants) ;
#  DIRIGER l'antenne (concentrer la puissance sans en dépenser plus).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_COMM = "communication"
_ALIAS_COMM = {
    "transmettre de l information", "communiquer a distance", "transmettre des donnees",
    "communication sans fil", "envoyer un signal loin", "communiquer efficacement",
}

# ── « Canaux » : les leviers de la capacité de communication ─────────────────────────────────────────────────────
_CANAUX_COMM = [
    Canal("bande passante", "information", "élargir la bande (la capacité croît LINÉAIREMENT avec B)",
          True, "doubler la bande double la capacité ; doubler la puissance ne l'augmente que de log₂(...) → "
                "élargir la bande est le levier le plus rentable ; le spectre est la ressource rare"),
    Canal("rapport signal sur bruit", "information", "augmenter S/N : antenne directive, se rapprocher, relayer",
          False, "gain seulement LOGARITHMIQUE en capacité → crier plus fort rapporte peu ; mais une antenne "
                 "directive concentre la puissance existante (S monte sans dépenser plus)"),
    Canal("codage", "information", "approcher la capacité (codes correcteurs) et COMPRESSER la source",
          True, "un bon code atteint presque la limite de Shannon ; compresser retire les bits redondants AVANT "
                "l'envoi → transmettre moins pour dire autant, le levier le moins cher"),
    Canal("energie par bit", "information", "minimiser l'énergie par bit (rétrodiffusion, proche de la limite de Shannon)",
          True, "la rétrodiffusion (backscatter) module un signal AMBIANT → communiquer à quasi zéro énergie "
                "propre ; sous-exploité pour les capteurs"),
]

# ── PRINCIPES candidats — chacun JUGÉ par la limite de Shannon (type `communication`, débit ≤ B·log₂(1+S/N)) ─────
_PRINCIPES_COMM = [
    _P("radio numérique moderne (5G, référence)",
       "communiquer : modulation numérique adaptative avec codage correcteur proche de la capacité",
       {"type": "communication", "debit_bits_par_s": 9.0e6, "bande_passante_Hz": 1e6, "rapport_signal_bruit": 1000},
       True, True, "signal reçu", "mature",
       0.65, "exploite déjà presque toute la capacité du canal avec de bons codes ; les gains restants viennent de "
             "la bande et de la directivité, pas de la puissance — la référence"),
    _P("étalement de spectre / ultra-large bande (UWB)",
       "communiquer : étaler le signal sur une très large bande à faible puissance",
       {"type": "communication", "debit_bits_par_s": 5e7, "bande_passante_Hz": 5e8, "rapport_signal_bruit": 0.1},
       True, True, "signal étalé", "mature",
       0.55, "échange de la BANDE contre de la puissance (capacité linéaire en B) → transmet SOUS le bruit, "
             "robuste et discret ; consomme du spectre — le levier « élargir la bande »"),
    _P("antenne directive / MIMO",
       "communiquer : concentrer et multiplexer le signal sur plusieurs antennes (faisceaux, flux parallèles)",
       {"type": "communication", "debit_bits_par_s": 8e6, "bande_passante_Hz": 1e6, "rapport_signal_bruit": 1000},
       True, True, "faisceaux dirigés", "mature",
       0.55, "concentre la puissance EXISTANTE (S monte) et multiplie les canaux spatiaux (MIMO) → plus de "
             "capacité sans plus d'énergie totale ; conditionné à la propagation — un des grands leviers"),
    _P("réseau maillé / relais (mesh)",
       "communiquer : relayer de proche en proche plutôt qu'émettre fort et loin",
       {"type": "communication", "debit_bits_par_s": 8e6, "bande_passante_Hz": 1e6, "rapport_signal_bruit": 1000},
       True, True, "signal relayé", "mature",
       0.5, "S/N chute en 1/d² → deux sauts courts battent un long saut en énergie ; le réseau se répare et "
            "s'étend tout seul ; latence et coordination à gérer — le levier « se rapprocher »"),
    _P("codage correcteur avancé (LDPC / turbo / polaire)",
       "communiquer : coder l'information pour corriger les erreurs et approcher la capacité de Shannon",
       {"type": "communication", "debit_bits_par_s": 9.8e6, "bande_passante_Hz": 1e6, "rapport_signal_bruit": 1000},
       True, True, "signal robuste", "mature",
       0.55, "atteint presque la limite théorique → tirer le MAXIMUM d'un canal donné sans plus de puissance ni "
             "de bande ; le levier « ne pas gaspiller le canal »"),
    _P("communication optique (fibre / laser espace libre)",
       "communiquer : porter l'information sur une porteuse optique à très large bande",
       {"type": "communication", "debit_bits_par_s": 1e11, "bande_passante_Hz": 1e13, "rapport_signal_bruit": 100},
       True, True, "signal optique", "mature (fibre)",
       0.5, "la bande optique est ÉNORME → capacité colossale ; en espace libre exige un pointage précis et un "
            "ciel clair (laser) — le levier « bande » poussé à l'extrême"),
    _P("compression de source avant émission",
       "communiquer : retirer la redondance de l'information AVANT de la transmettre",
       {"type": "communication", "debit_bits_par_s": 8e6, "bande_passante_Hz": 1e6, "rapport_signal_bruit": 1000},
       True, True, "flux compressé", "mature (sous-exploité en bord)",
       0.5, "le bit le moins cher à transmettre est celui qu'on n'envoie pas : compresser/résumer à la source "
            "réduit le débit requis → l'analogue de « ne pas générer » en éclairage"),
    _P("rétrodiffusion ambiante (backscatter, RFID passif)",
       "communiquer : moduler la réflexion d'un signal radio AMBIANT au lieu d'émettre le sien",
       {"type": "communication", "debit_bits_par_s": 1e3, "bande_passante_Hz": 1e5, "rapport_signal_bruit": 10},
       True, True, "signal réfléchi modulé", "émergent",
       0.45, "communique à quasi ZÉRO énergie propre (l'émetteur ambiant fournit la porteuse) → capteurs sans "
             "pile ; débit faible et portée courte — piste basse conso sous-exploitée"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER : au-dessus de la capacité de Shannon) ──
    _P("liaison « 20 Mbit/s sur 1 MHz à 30 dB »",
       "communiquer : 20 Mbit/s sans erreur sur 1 MHz de bande à un rapport signal/bruit de 1000",
       {"type": "communication", "debit_bits_par_s": 2e7, "bande_passante_Hz": 1e6, "rapport_signal_bruit": 1000},
       True, True, "—", "revendication",
       0.3, "20 Mbit/s > capacité de Shannon (~9,97 Mbit/s ici) — à réfuter par la limite de Shannon"),
    _P("transmission « sans bande passante »",
       "communiquer : transmettre 1 Mbit/s sur une bande passante nulle",
       {"type": "communication", "debit_bits_par_s": 1e6, "bande_passante_Hz": 0, "rapport_signal_bruit": 1000},
       True, True, "—", "revendication",
       0.25, "sans bande passante la capacité est nulle : transmettre de l'information exige de la bande — impossible"),
]

_OBJECTIF_COMM = ("Le but réel n'est pas de « crier plus fort » : la capacité d'un canal ne croît que "
                  "LOGARITHMIQUEMENT avec le rapport signal/bruit, mais LINÉAIREMENT avec la bande passante "
                  "(Shannon : débit ≤ B·log₂(1+S/N)). On vise donc des bits fiables par joule et par Hz. Leviers : "
                  "élargir la BANDE (bien plus rentable que la puissance) ; se rapprocher ou RELAYER (S/N chute en "
                  "1/d² → deux sauts courts battent un long) ; bon CODAGE pour approcher la capacité et COMPRESSER "
                  "la source (ne pas transmettre de redondance) ; DIRIGER l'antenne (concentrer la puissance "
                  "existante). Chaque principe reste jugé par la limite de Shannon.")
_LOI_COMM = ("le débit sans erreur ≤ B·log₂(1 + S/N) (limite de Shannon) : la capacité est LINÉAIRE en bande "
             "passante mais seulement LOGARITHMIQUE en signal/bruit ; gains réels = élargir la bande, relayer "
             "plutôt qu'émettre fort, coder près de la capacité, compresser la source, diriger l'antenne")

# La nature communique par le canal qui porte (baleine), un médium persistant (fourmi), un code dense (abeille), un relais (mycélium).
_STRATEGIES_NATURE_COMM = [
    _Nature("chant des baleines (très basse fréquence)",
            ["basse fréquence = faible atténuation dans l'eau", "porte sur des centaines de km",
             "choix du canal qui transmet le mieux"],
            "choisir la FRÉQUENCE/le canal qui se propage le mieux plutôt que d'émettre plus fort"),
    _Nature("phéromones de fourmis (canal chimique persistant)",
            ["signal DÉPOSÉ dans l'environnement (persistant)", "lu en différé (asynchrone)", "quasi zéro énergie"],
            "un médium persistant transmet sans émetteur actif — communiquer en différé pour presque rien"),
    _Nature("danse frétillante des abeilles (code dense)",
            ["direction ET distance encodées en peu de gestes", "information compressée dans un signal court"],
            "COMPRESSER beaucoup d'information dans un signal minimal — le levier du codage de source"),
    _Nature("réseau mycélien (relais chimique/électrique)",
            ["signaux propagés de proche en proche dans le réseau", "pas d'émetteur central puissant"],
            "RELAYER à travers un maillage plutôt qu'émettre fort et loin — le levier du mesh"),
]

enregistre(Domaine(
    nom=_COMM,
    aliases=frozenset(_ALIAS_COMM),
    objectif=_OBJECTIF_COMM,
    canaux=_CANAUX_COMM,
    principes=_PRINCIPES_COMM,
    strategies=_STRATEGIES_NATURE_COMM,
    loi=_LOI_COMM,
    extras={"capacite_shannon": "débit ≤ B·log₂(1 + S/N) bits/s",
            "note": "élargir la BANDE bat augmenter la puissance (capacité linéaire en B, logarithmique en S/N)"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  ONZIÈME DOMAINE : capter l'énergie solaire. Nouvelle loi dure au juge (L8) : la limite de SHOCKLEY-QUEISSER —
#  une cellule à jonction simple STANDARD (une paire électron-trou par photon, un seul seuil) plafonne à ~33,7 %
#  sous 1 soleil ; et, toute architecture confondue, le rendement reste sous le plafond THERMODYNAMIQUE du solaire
#  (exergie du rayonnement : Landsberg ~93 %, Carnot 1−Ta/Ts). REFRAMING machine : le but n'est pas de poser plus
#  de surface mais de convertir une plus grande part de CHAQUE photon. Une jonction simple gaspille deux fois — les
#  photons SOUS son gap la traversent, l'EXCÈS d'énergie des photons au-dessus part en chaleur (thermalisation).
#  Leviers : empiler des jonctions accordées à des bandes (tandem, plafond ~86 %) ; CONCENTRER (monte la tension,
#  remplace le semi-conducteur par de l'optique) ; récupérer la thermalisation (porteurs chauds / multi-excitons /
#  bande intermédiaire) ; s'approcher de la limite RADIATIVE (matériaux purs, recyclage des photons).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_SOLAIRE = "captation_solaire"
_ALIAS_SOLAIRE = {
    "capter l energie solaire", "convertir la lumiere du soleil", "produire de l electricite solaire",
    "capter le rayonnement solaire", "photovoltaique", "exploiter l energie du soleil",
}

# ── « Canaux » : les leviers du rendement de conversion solaire ──────────────────────────────────────────────────
_CANAUX_SOLAIRE = [
    Canal("spectre", "lumiere", "capter une PLUS GRANDE part du spectre : empiler des jonctions (tandem) accordées à des bandes différentes",
          True, "une jonction simple perd les photons SOUS son gap ET l'excès des photons au-dessus (thermalisation) ; "
                "empiler des gaps récupère les deux — le plus grand levier, plafond ~86 % en multi-jonction"),
    Canal("concentration", "lumiere", "CONCENTRER la lumière (miroirs/lentilles) : plus de photons par cellule → tension plus haute",
          True, "la concentration relève la limite de rendement (jusqu'à ~46 200 soleils) et remplace du semi-conducteur "
                "cher par de l'optique ; exige un suivi précis et d'évacuer la chaleur"),
    Canal("thermalisation", "lumiere", "récupérer l'excès d'énergie des photons chauds AVANT dissipation (porteurs chauds, bande intermédiaire, multi-excitons)",
          True, "l'énergie au-dessus du gap est perdue en chaleur dans une cellule normale ; l'extraire (porteurs "
                "chauds) ou la fractionner (MEG, bande intermédiaire) attaque la 2e grande perte — encore en labo"),
    Canal("recombinaison", "lumiere", "s'approcher de la limite RADIATIVE : supprimer la recombinaison non-radiative (matériaux purs, passivation, recyclage des photons)",
          True, "le meilleur émetteur est le meilleur absorbeur : une cellule qui ne perd de porteurs QUE par "
                "rayonnement atteint la limite de Shockley-Queisser — le levier « qualité du matériau »"),
]

# ── PRINCIPES candidats — chacun JUGÉ par la limite de Shockley-Queisser / le plafond thermodynamique (type `captation_solaire`) ──
_PRINCIPES_SOLAIRE = [
    _P("cellule silicium mono-jonction (référence)",
       "capter le solaire : cellule silicium à jonction unique sous lumière ambiante (1 soleil)",
       {"type": "captation_solaire", "rendement": 0.27, "nb_jonctions": 1, "concentration_solaire": 1,
        "bilan_detaille_standard": True}, True, True,
       "—", "mature",
       0.65, "la référence du marché (~27 % en labo, ~22 % en module) ; sous la limite de Shockley-Queisser (33,7 %) "
             "— les gains restants passent par la tandem, pas par le silicium seul"),
    _P("tandem pérovskite/silicium (multi-jonction)",
       "capter le solaire : empiler une jonction pérovskite (gap large) sur le silicium pour capter plus du spectre",
       {"type": "captation_solaire", "rendement": 0.33, "nb_jonctions": 2, "concentration_solaire": 1}, True, True,
       "—", "émergent (industrialisation)",
       0.6, "dépasse la limite mono-jonction : la jonction haute prend les photons bleus, le silicium les rouges ; "
            "stabilité de la pérovskite à prouver — le levier « spectre » le plus proche du marché"),
    _P("multi-jonction III-V sous concentration (CPV)",
       "capter le solaire : cellule III-V à 3+ jonctions sous forte concentration optique",
       {"type": "captation_solaire", "rendement": 0.47, "nb_jonctions": 3, "concentration_solaire": 500}, True, True,
       "—", "mature (spatial/CPV)",
       0.55, "record mondial (~47 %) : concentration ET plusieurs jonctions cumulent les deux leviers ; coût des "
             "matériaux III-V et suivi solaire exigeant → spatial et CPV, pas le toit domestique"),
    _P("cellule à porteurs chauds",
       "capter le solaire : extraire les porteurs AVANT qu'ils ne thermalisent, pour récupérer l'excès d'énergie des photons bleus",
       {"type": "captation_solaire", "rendement": 0.55, "nb_jonctions": 1, "concentration_solaire": 1000}, True, True,
       "—", "recherche",
       0.4, "attaque la 2e grande perte (thermalisation) SANS empiler de jonctions ; exige une extraction "
            "ultra-rapide et des contacts sélectifs en énergie — horizon lointain mais dans les lois"),
    _P("cellule à bande intermédiaire",
       "capter le solaire : une bande d'énergie intermédiaire absorbe AUSSI les photons sous le gap principal",
       {"type": "captation_solaire", "rendement": 0.45, "nb_jonctions": 1, "concentration_solaire": 100}, True, True,
       "—", "recherche",
       0.4, "récupère les photons infrarouges normalement perdus via un niveau intermédiaire, sans multiplier les "
            "jonctions ; matériaux à points quantiques/impuretés à maîtriser — piste sous-exploitée"),
    _P("génération multi-excitons (points quantiques)",
       "capter le solaire : un photon très énergétique libère PLUSIEURS paires électron-trou au lieu d'une",
       {"type": "captation_solaire", "rendement": 0.42, "nb_jonctions": 1, "concentration_solaire": 1}, True, True,
       "—", "recherche",
       0.35, "fractionne l'énergie d'un photon bleu en plusieurs porteurs au lieu de la perdre en chaleur (dépasse "
             "SQ légitimement, hors régime standard) ; rendements quantiques >100 % démontrés sur points quantiques "
             "mais courants faibles — exploratoire"),
    _P("concentrateur luminescent / découpage spectral",
       "capter le solaire : un guide fluorescent concentre et trie la lumière vers des cellules adaptées à chaque couleur",
       {"type": "captation_solaire", "rendement": 0.20, "nb_jonctions": 1, "concentration_solaire": 1}, True, True,
       "—", "recherche (BIPV)",
       0.35, "capte la lumière diffuse et se pose en façade/fenêtre (pas besoin de suivi) ; pertes de ré-absorption "
             "à réduire — le levier « intégration au bâti »"),
    _P("thermophotovoltaïque solaire (absorbeur chaud + PV IR)",
       "capter le solaire : chauffer un absorbeur qui ré-émet un spectre étroit adapté à une cellule infrarouge",
       {"type": "captation_solaire", "rendement": 0.30, "nb_jonctions": 1, "concentration_solaire": 1000}, True, True,
       "—", "recherche",
       0.35, "met en forme le spectre pour l'accorder à la cellule et permet le STOCKAGE thermique (produire la "
             "nuit) ; hautes températures et pertes radiatives à dompter — pont vers le stockage d'énergie"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER) ──
    _P("panneau mono-jonction « à 50 % » (1 soleil)",
       "capter le solaire : cellule à jonction unique STANDARD revendiquant 50 % sous lumière non concentrée",
       {"type": "captation_solaire", "rendement": 0.50, "nb_jonctions": 1, "concentration_solaire": 1,
        "bilan_detaille_standard": True}, True, True,
       "—", "revendication",
       0.3, "50 % > limite de Shockley-Queisser (33,7 % pour une jonction simple standard sous 1 soleil) — à réfuter "
            "par le bilan détaillé"),
    _P("panneau solaire « 100 % efficace »",
       "capter le solaire : convertir TOUTE l'énergie du rayonnement solaire en électricité",
       {"type": "captation_solaire", "rendement": 1.0}, True, True,
       "—", "revendication",
       0.25, "100 % dépasse le plafond thermodynamique du solaire (exergie du rayonnement, Landsberg ~93 % / Carnot "
             "~95 %) — impossible"),
]

_OBJECTIF_SOLAIRE = ("Le but réel n'est pas de poser plus de surface mais de convertir une plus grande part de "
                     "CHAQUE photon. Une jonction simple gaspille deux fois : les photons SOUS son gap la traversent, "
                     "et l'EXCÈS d'énergie des photons au-dessus part en chaleur (thermalisation) — d'où le plafond de "
                     "Shockley-Queisser (~33,7 % sous 1 soleil). Leviers : empiler des jonctions accordées à des "
                     "bandes différentes (tandem/multi-jonction, plafond ~86 %) ; CONCENTRER la lumière (monte la "
                     "tension, remplace le semi-conducteur par de l'optique) ; récupérer la thermalisation (porteurs "
                     "chauds, bande intermédiaire, multi-excitons) ; s'approcher de la limite RADIATIVE (matériaux "
                     "purs, recyclage des photons). La borne indépassable de toute architecture reste thermodynamique "
                     "(exergie du rayonnement solaire). Chaque principe reste jugé par ces limites.")
_LOI_SOLAIRE = ("le rendement de conversion solaire est borné : une cellule à jonction simple en régime STANDARD "
                "(une paire électron-trou par photon, un seul seuil) plafonne à la limite de Shockley-Queisser "
                "(~33,7 % sous 1 soleil) ; la borne ABSOLUE de toute architecture est thermodynamique (exergie du "
                "rayonnement, Landsberg ~93 %, Carnot 1−Ta/Ts) ; gains réels = empiler les jonctions (spectre), "
                "concentrer, récupérer la thermalisation (porteurs chauds/MEG/bande intermédiaire), s'approcher de "
                "la limite radiative")

# La nature capte la lumière par une large antenne (photosynthèse), un piège (papillon), un anti-reflet (mite), un suivi (tournesol).
_STRATEGIES_NATURE_SOLAIRE = [
    _Nature("photosynthèse (antennes collectrices + centre réactionnel)",
            ["large ANTENNE de pigments capte un spectre étendu", "transfert d'excitation quasi sans perte vers le centre",
             "canalise l'énergie vers un seul site de conversion"],
            "capter large PUIS canaliser l'énergie vers un convertisseur — le levier « spectre » + collecte"),
    _Nature("aile de papillon noir (écailles piège-à-lumière)",
            ["nanostructures qui piègent la lumière par réflexions multiples", "absorption quasi totale sur une couche mince"],
            "PIÉGER la lumière dans une couche mince plutôt qu'épaissir l'absorbeur — le light-trapping"),
    _Nature("œil de mite (nanostructures anti-reflet)",
            ["réseau de bosses sub-longueur d'onde annulant la réflexion", "transition d'indice progressive"],
            "ne rien RÉFLÉCHIR : capter les photons au lieu de les renvoyer — l'anti-reflet gratuit"),
    _Nature("héliotropisme du tournesol (suivi solaire)",
            ["orientation continue face au soleil", "maximise le flux reçu au fil du jour"],
            "SUIVRE le soleil pour maximiser le flux capté — l'analogue du tracking et de la concentration"),
]

enregistre(Domaine(
    nom=_SOLAIRE,
    aliases=frozenset(_ALIAS_SOLAIRE),
    objectif=_OBJECTIF_SOLAIRE,
    canaux=_CANAUX_SOLAIRE,
    principes=_PRINCIPES_SOLAIRE,
    strategies=_STRATEGIES_NATURE_SOLAIRE,
    loi=_LOI_SOLAIRE,
    extras={"plafond_shockley_queisser": "≈ 33,7 % (jonction simple standard, 1 soleil)",
            "plafond_absolu": "exergie du rayonnement solaire : Landsberg ~93,3 %, Carnot 1−Ta/Ts ~94,8 %",
            "note": "multi-jonction + concentration cumulent les leviers (record ~47 % ; idéal ~86 %)"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  DOUZIÈME DOMAINE : produire de l'hydrogène (électrolyse de l'eau). Nouvelle loi dure au juge (L9) : le travail
#  électrique minimal = l'enthalpie libre de Gibbs ΔG (tension de cellule ≥ E_rev ≈ 1,23 V à 25 °C) ET l'énergie
#  TOTALE ≥ l'enthalpie ΔH (PCS de H₂, ~285,8 kJ/mol). REFRAMING machine : l'ennemi n'est pas la faisabilité (on
#  sait scinder l'eau depuis 1800) mais la SURTENSION — les cellules réelles tournent à 1,8–2,0 V contre 1,23 V
#  réversible, soit ~40 % d'énergie gaspillée — et le COÛT des catalyseurs nobles (Pt/Ir). Leviers : réduire la
#  surtension (catalyseurs actifs abondants) ; monter la TEMPÉRATURE (SOEC : E_rev chute, une part de l'énergie
#  vient de la chaleur) ; réaction ANODIQUE alternative (oxydation sacrificielle valorisant un sous-produit, sous
#  1,23 V légitimement) ; coupler directement à la LUMIÈRE (photoélectrochimique).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_H2 = "production_hydrogene"
_ALIAS_H2 = {
    "produire de l hydrogene", "fabriquer de l hydrogene", "electrolyse de l eau",
    "produire de l hydrogene vert", "fractionner l eau", "hydrogene par electrolyse",
}

# ── « Canaux » : les leviers pour rapprocher l'électrolyse de son minimum thermodynamique ────────────────────────
_CANAUX_H2 = [
    Canal("surtension", "energie", "réduire la SURTENSION : catalyseurs très actifs pour approcher E_rev (~1,23 V)",
          True, "une cellule réelle à 1,8–2,0 V gaspille ~40 % en surtension ; chaque dixième de volt gagné est de "
                "l'énergie directe — le plus gros levier de rendement à basse température"),
    Canal("temperature", "energie", "monter la TEMPÉRATURE (électrolyse à oxyde solide) : E_rev baisse, la chaleur fournit une part",
          True, "à haute température ΔG diminue (une part de l'énergie vient de la chaleur, souvent fatale/solaire) → "
                "la demande ÉLECTRIQUE chute ; exige des matériaux céramiques tenant 700–900 °C"),
    Canal("catalyseur", "energie", "remplacer les métaux NOBLES (Pt/Ir) par des catalyseurs abondants (Ni-Fe, sulfures)",
          True, "attaque le COÛT et la rareté plus que l'énergie : des catalyseurs terrestres abondants rendent "
                "l'électrolyse déployable à l'échelle du térawatt — le verrou industriel"),
    Canal("anode", "energie", "réaction ANODIQUE alternative : oxyder un composé sacrificiel au lieu de dégager l'O₂",
          True, "remplacer l'oxydation de l'eau (coûteuse) par celle d'un sous-produit (urée, alcools, biomasse) "
                "abaisse la tension SOUS 1,23 V et valorise un déchet — le levier « changer la demi-réaction »"),
]

# ── PRINCIPES candidats — chacun JUGÉ par la limite d'électrolyse (type `electrolyse`, tension ≥ E_rev, énergie ≥ ΔH) ──
_PRINCIPES_H2 = [
    _P("électrolyse alcaline (référence)",
       "produire H₂ : électrolyse alcaline classique (électrodes nickel dans une solution de potasse)",
       {"type": "electrolyse", "tension_cellule_V": 1.9, "t_K": 353, "reaction_anodique_standard": True}, True, True,
       "—", "mature",
       0.65, "la technologie la plus déployée, robuste et sans métaux nobles ; tension ~1,8–2,0 V (surtension "
             "notable) → la référence dont il faut réduire la surtension"),
    _P("électrolyse PEM (membrane échangeuse de protons)",
       "produire H₂ : électrolyseur à membrane polymère, réactif et compact, sous catalyseurs iridium/platine",
       {"type": "electrolyse", "tension_cellule_V": 1.8, "t_K": 343, "reaction_anodique_standard": True}, True, True,
       "—", "mature",
       0.6, "densités de courant élevées et réponse rapide (adapté au renouvelable intermittent) ; dépend d'iridium "
            "rare à l'anode → le verrou catalyseur"),
    _P("électrolyse à oxyde solide (SOEC, haute température)",
       "produire H₂ : électrolyse à 700–900 °C où une part de l'énergie est apportée par la chaleur",
       {"type": "electrolyse", "tension_cellule_V": 1.3, "t_K": 1073, "reaction_anodique_standard": True}, True, True,
       "—", "émergent",
       0.55, "à haute température E_rev chute → demande électrique la plus basse, surtout si la chaleur est fatale "
             "ou solaire ; dégradation des céramiques et cyclage thermique à maîtriser — le levier « température »"),
    _P("électrolyse à membrane échangeuse d'anions (AEM)",
       "produire H₂ : membrane alcaline solide combinant catalyseurs abondants et architecture compacte",
       {"type": "electrolyse", "tension_cellule_V": 1.8, "t_K": 333, "reaction_anodique_standard": True}, True, True,
       "—", "recherche (industrialisation)",
       0.5, "vise le meilleur des deux mondes : catalyseurs non nobles (comme l'alcaline) et compacité (comme le "
            "PEM) ; durabilité des membranes à prouver — piste industrielle sous-exploitée"),
    _P("électrolyse assistée (oxydation sacrificielle à l'anode)",
       "produire H₂ : remplacer le dégagement d'O₂ par l'oxydation d'un composé (urée, alcool, biomasse) sous 1,23 V",
       {"type": "electrolyse", "tension_cellule_V": 0.8, "t_K": 298.15}, True, True,
       "—", "recherche",
       0.45, "descend LÉGITIMEMENT sous la tension réversible de l'eau car une AUTRE réaction fournit l'énergie et "
             "valorise un déchet ; consomme le composé sacrificiel → pas universel, mais élégant en co-production"),
    _P("cellule photoélectrochimique (scission directe par la lumière)",
       "produire H₂ : un semi-conducteur immergé scinde l'eau directement sous l'éclairement solaire",
       {"type": "electrolyse", "energie_kJ_par_mol_H2": 500}, True, True,
       "—", "recherche",
       0.4, "supprime l'étape électrique séparée (le photon fait le travail) → potentiellement simple et bon marché ; "
            "rendements et stabilité des photo-électrodes encore faibles — horizon lointain, dans les lois"),
    _P("cycle thermochimique (soufre-iode, chaleur haute température)",
       "produire H₂ : scinder l'eau par une suite de réactions chimiques entraînées par la chaleur, sans électricité",
       {"type": "electrolyse", "energie_kJ_par_mol_H2": 450}, True, True,
       "—", "recherche",
       0.4, "utilise directement de la chaleur haute température (nucléaire, solaire concentré) au lieu d'électricité ; "
            "corrosion et complexité des boucles chimiques à dompter — voie « chaleur → H₂ »"),
    _P("catalyseurs sans métaux nobles (Ni-Fe, sulfures, phosphures)",
       "produire H₂ : électrolyse alcaline avec catalyseurs terrestres abondants réduisant la surtension",
       {"type": "electrolyse", "tension_cellule_V": 1.7, "t_K": 353, "reaction_anodique_standard": True}, True, True,
       "—", "recherche (regain)",
       0.5, "attaque à la fois la surtension (matériaux plus actifs) et le coût (aucun métal rare) → condition du "
            "déploiement massif ; stabilité en fonctionnement continu à prouver — levier « catalyseur abondant »"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER) ──
    _P("électrolyseur « à 0,9 V » (anode standard, ambiant)",
       "produire H₂ : cellule à anode standard (dégagement d'O₂) revendiquant 0,9 V à température ambiante",
       {"type": "electrolyse", "tension_cellule_V": 0.9, "t_K": 298.15, "reaction_anodique_standard": True}, True, True,
       "—", "revendication",
       0.3, "0,9 V < tension réversible de l'eau (~1,23 V à 25 °C, anode O₂) — le fractionnement net ne peut pas se "
            "produire ; à réfuter par le 2nd principe (ΔG)"),
    _P("hydrogène « à 150 kJ/mol » (sous le PCS)",
       "produire H₂ : fabriquer une mole de H₂ avec 150 kJ d'énergie totale",
       {"type": "electrolyse", "energie_kJ_par_mol_H2": 150}, True, True,
       "—", "revendication",
       0.25, "150 kJ/mol < PCS de H₂ (285,8 kJ/mol, ΔH) : le H₂ restituerait à la combustion plus d'énergie qu'il "
             "n'en a reçu = création nette — impossible"),
]

_OBJECTIF_H2 = ("Le but réel n'est pas de « savoir » scinder l'eau (acquis depuis 1800) mais de le faire au plus "
                "près du minimum thermodynamique et avec des matériaux abondants. Deux planchers : le travail "
                "ÉLECTRIQUE ≥ ΔG (enthalpie libre de Gibbs, tension ≥ E_rev ≈ 1,23 V à 25 °C) et l'énergie TOTALE "
                "≥ ΔH (PCS de H₂, "
                "~285,8 kJ/mol). L'ennemi est la SURTENSION (cellules réelles à 1,8–2,0 V ≈ 40 % de pertes) et le "
                "coût des catalyseurs nobles. Leviers : réduire la surtension (catalyseurs actifs abondants) ; "
                "monter la TEMPÉRATURE (SOEC : E_rev chute, la chaleur fournit une part) ; changer la réaction "
                "ANODIQUE (oxydation sacrificielle sous 1,23 V, valorise un déchet) ; coupler directement à la "
                "LUMIÈRE (photoélectrochimique). Chaque principe reste jugé par ces limites.")
_LOI_H2 = ("électrolyse de l'eau : l'énergie électrique par mole de H₂ ≥ ΔG (tension de cellule ≥ E_rev(T) = "
           "ΔG(T)/nF, ~1,23 V à 25 °C, abaissée à haute température) et l'énergie TOTALE ≥ ΔH (PCS de H₂, "
           "~285,8 kJ/mol) ; gains réels = réduire la surtension, monter la température, changer la demi-réaction "
           "anodique, catalyseurs abondants")

# La nature scinde l'eau et fabrique H₂ : enzyme à métaux abondants, photosystème II, microbes, séparation membranaire.
_STRATEGIES_NATURE_H2 = [
    _Nature("hydrogénase (enzyme à fer/nickel)",
            ["catalyse H⁺ ⇄ H₂ à très basse surtension", "site actif à base de fer/nickel ABONDANTS", "vitesse comparable au platine"],
            "catalyser avec des métaux ABONDANTS aussi bien qu'avec le platine — le levier « catalyseur sans métal noble »"),
    _Nature("photosystème II (oxydation de l'eau par la lumière)",
            ["complexe au manganèse oxyde l'eau", "entraîné directement par les photons", "faible surtension à l'anode"],
            "oxyder l'eau à l'anode à basse surtension et sous la lumière — le levier « photo-assistance + catalyseur d'O₂ »"),
    _Nature("microbes producteurs d'H₂ (fermentation, nitrogénase)",
            ["produisent H₂ à température et pression ambiantes", "à partir de biomasse/déchets"],
            "produire H₂ en conditions douces à partir d'un déchet — la voie biologique sacrificielle"),
    _Nature("membrane biologique (tri des gaz à mesure)",
            ["sépare les gaz produits sélectivement", "évite la recombinaison H₂/O₂"],
            "SÉPARER H₂ et O₂ dès leur formation pour éviter la recombinaison — le levier « membrane sélective »"),
]

enregistre(Domaine(
    nom=_H2,
    aliases=frozenset(_ALIAS_H2),
    objectif=_OBJECTIF_H2,
    canaux=_CANAUX_H2,
    principes=_PRINCIPES_H2,
    strategies=_STRATEGIES_NATURE_H2,
    loi=_LOI_H2,
    extras={"tension_reversible_V": "~1,23 V (25 °C, ΔG/2F ; abaissée à haute température)",
            "pcs_h2_kJ_mol": "285,8 (ΔH, plancher de l'énergie totale)",
            "note": "cellules réelles à 1,8–2,0 V ≈ 40 % de surtension ; SOEC et anode alternative rapprochent de E_rev"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  TREIZIÈME DOMAINE : voler sur place / vol stationnaire. Nouvelle loi dure au juge (L10) : la PUISSANCE INDUITE
#  IDÉALE (théorie de la quantité de mouvement / disque actuateur) — pour sustenter une poussée T sur un disque
#  d'aire A dans un air de masse volumique ρ, il faut au moins P = T^1,5/√(2ρA) (plancher absolu P/√2 en effet de
#  sol maximal). REFRAMING machine : l'ennemi est la CHARGE DU DISQUE (T/A) — la puissance croît en √(T/A), donc
#  un GRAND disque lent bat un petit jet rapide (c'est pourquoi l'hélicoptère a un grand rotor et le drone est
#  inefficace). Leviers : agrandir le disque (P ∝ 1/√A, de loin le plus gros) ; alléger (T = m·g) ; exploiter
#  l'EFFET DE SOL ; et surtout la PORTANCE STATIQUE (aérostat, flottabilité d'Archimède) qui contourne
#  entièrement la puissance induite — ne pas combattre la gravité avec un rotor, mais flotter.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_VOL = "sustentation"
_ALIAS_VOL = {
    "voler sur place", "se sustenter en vol", "vol stationnaire", "faire du vol stationnaire",
    "planer en vol stationnaire", "soulever une charge en vol",
}

# ── « Canaux » : les leviers de la puissance de sustentation ─────────────────────────────────────────────────────
_CANAUX_VOL = [
    Canal("aire du disque", "portance", "AGRANDIR le disque rotor : la puissance induite décroît en 1/√A",
          True, "de loin le plus gros levier : décupler l'aire divise la puissance par ~3 (√10) ; c'est pourquoi un "
                "hélicoptère a un grand rotor lent et un quadricoptère à petites hélices est énergivore"),
    Canal("charge du disque", "portance", "baisser la CHARGE DU DISQUE (poussée par unité d'aire T/A) : puissance ∝ √(T/A)",
          True, "une faible charge de disque = air brassé lentement sur une grande surface = peu de puissance ; une "
                "forte charge (petit jet rapide) coûte cher — la variable qui gouverne l'efficacité du vol stationnaire"),
    Canal("masse", "portance", "ALLÉGER l'aéronef : la poussée requise T = m·g, et la puissance croît en T^1,5",
          True, "chaque gramme économisé compte doublement (T^1,5) ; structures composites, batteries denses — le "
                "levier « moins de poids à porter »"),
    Canal("portance statique / effet de sol", "portance", "CONTOURNER la puissance induite : flottabilité (aérostat) ou effet de sol",
          True, "la portance statique (Archimède, dirigeable) sustente à puissance quasi NULLE — elle échappe à la "
                "puissance induite ; l'effet de sol la réduit (sol = rotor-image) — le levier « ne pas brasser d'air »"),
]

# ── PRINCIPES candidats — chacun JUGÉ par la puissance induite idéale (type `sustentation`, P ≥ T^1,5/√(2ρA)/√2) ──
_PRINCIPES_VOL = [
    _P("hélicoptère à grand rotor (référence)",
       "voler sur place : un grand rotor unique brasse un large disque d'air à faible charge",
       {"type": "sustentation", "masse_kg": 2000, "aire_rotor_m2": 113, "puissance_W": 180000}, False, False,
       "air brassé vers le bas", "mature",
       0.6, "la référence efficace : grand disque = faible charge = puissance induite modérée (~165 kW idéal pour "
            "2 t) ; le grand rotor est précisément ce qui rend l'hélico viable — le levier « aire » incarné"),
    _P("multirotor / drone (petites hélices)",
       "voler sur place : plusieurs petites hélices à forte charge de disque",
       {"type": "sustentation", "masse_kg": 2, "aire_rotor_m2": 0.05, "puissance_W": 300}, False, False,
       "air brassé vers le bas", "mature",
       0.5, "simple et contrôlable, MAIS petites hélices = forte charge de disque = énergivore (autonomie courte) ; "
            "réel mais loin de l'optimum — illustre le COÛT d'un petit disque"),
    _P("drone à grand disque lent (rotor surdimensionné)",
       "voler sur place : un rotor bien plus grand tournant lentement pour la même charge",
       {"type": "sustentation", "masse_kg": 2, "aire_rotor_m2": 0.5, "puissance_W": 100}, False, False,
       "air brassé vers le bas", "émergent",
       0.55, "×10 d'aire → puissance ÷~3 (√10) pour la même charge : le levier direct de l'efficacité ; encombrement "
             "et fragilité du grand rotor à gérer — piste sous-exploitée en dronistique"),
    _P("rotors coaxiaux / tandem (charge répartie)",
       "voler sur place : deux rotors partageant la charge sur une plus grande aire effective",
       {"type": "sustentation", "masse_kg": 2000, "aire_rotor_m2": 150, "puissance_W": 150000}, False, False,
       "air brassé vers le bas", "mature",
       0.5, "répartir la poussée sur plus de surface baisse la charge de disque effective et supprime le rotor de "
            "queue ; complexité mécanique — variante du levier « aire »"),
    _P("aérostat (portance statique, Archimède)",
       "voler sur place : sustenter par flottabilité (gaz plus léger que l'air), sans brasser d'air",
       {"type": "sustentation"}, True, True,
       "aucun (portance statique)", "mature",
       0.55, "REFRAMING : la portance STATIQUE contourne entièrement la puissance induite → sustentation à puissance "
             "quasi nulle (silencieux, endurance énorme) ; volume encombrant et sensibilité au vent — ne pas "
             "combattre la gravité avec un rotor, mais flotter"),
    _P("effet de sol (vol au ras d'une surface)",
       "voler sur place : exploiter la proximité du sol qui réduit la puissance induite (rotor-image)",
       {"type": "sustentation", "masse_kg": 2, "aire_rotor_m2": 0.05, "puissance_W": 200}, False, False,
       "air brassé vers le bas (recyclé par le sol)", "mature",
       0.45, "près du sol, l'aire effective augmente (image) → moins de puissance pour la même poussée ; limité à "
             "une faible hauteur — le levier « laisser le sol aider »"),
    _P("rotor caréné (ventilateur en conduit)",
       "voler sur place : un carénage augmente l'aire effective et récupère la poussée de bord",
       {"type": "sustentation", "masse_kg": 2, "aire_rotor_m2": 0.08, "puissance_W": 250}, False, False,
       "air brassé vers le bas", "mature",
       0.45, "le carénage augmente la poussée pour un même disque et protège le rotor ; poids et traînée du conduit "
             "en avancement — variante du levier « aire effective »"),
    _P("propulsion distribuée (nombreux petits rotors répartis)",
       "voler sur place : répartir la sustentation sur beaucoup de rotors couvrant une grande aire totale",
       {"type": "sustentation", "masse_kg": 2, "aire_rotor_m2": 0.2, "puissance_W": 150}, False, False,
       "air brassé vers le bas", "émergent (eVTOL)",
       0.45, "beaucoup de rotors couvrant une grande aire totale baissent la charge de disque et ajoutent la "
             "redondance ; câblage et contrôle complexes — piste des eVTOL"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER) ──
    _P("drone 2 kg « qui plane à 5 W » (hélice 0,05 m²)",
       "voler sur place : sustenter 2 kg avec 5 W et une hélice de 0,05 m²",
       {"type": "sustentation", "masse_kg": 2, "aire_rotor_m2": 0.05, "puissance_W": 5}, True, True,
       "—", "revendication",
       0.3, "5 W ≪ puissance induite idéale (~248 W pour cette charge de disque) — à réfuter par la théorie de la "
            "quantité de mouvement"),
    _P("plateforme 100 kg « qui plane à 50 W » (disque 0,1 m²)",
       "voler sur place : sustenter 100 kg avec 50 W et un disque de 0,1 m²",
       {"type": "sustentation", "poussee_N": 981, "aire_rotor_m2": 0.1, "puissance_W": 50}, True, True,
       "—", "revendication",
       0.25, "50 W ≪ puissance induite idéale (~62 kW pour cette charge de disque) — impossible"),
]

_OBJECTIF_VOL = ("Le but réel n'est pas de « pousser plus fort » mais de brasser de l'air EFFICACEMENT : la "
                 "puissance induite idéale vaut T^1,5/√(2ρA), donc l'ennemi est la CHARGE DU DISQUE (poussée par "
                 "unité d'aire T/A). Un GRAND disque lent bat un petit jet rapide (puissance ∝ 1/√A) — c'est "
                 "pourquoi l'hélicoptère a un grand rotor et le drone à petites hélices est énergivore. Leviers : "
                 "agrandir le disque (le plus gros, P ∝ 1/√A) ; alléger (T = m·g, P ∝ T^1,5) ; exploiter l'effet de "
                 "sol ; et surtout la PORTANCE STATIQUE (aérostat, flottabilité) qui contourne entièrement la "
                 "puissance induite. Chaque principe reste jugé par ce plancher (P ≥ puissance induite / √2).")
_LOI_VOL = ("vol stationnaire : la puissance ≥ puissance induite idéale P = T^1,5/√(2ρA) (théorie de la quantité de "
            "mouvement / disque actuateur ; plancher absolu P/√2 en effet de sol maximal) ; gains réels = agrandir "
            "le disque (P ∝ 1/√A), baisser la charge de disque, alléger, et contourner par la portance statique")

# La nature sustente par un grand disque battu (colibri), l'autorotation (samare), le vol plané (albatros), la flottabilité (vessie natatoire).
_STRATEGIES_NATURE_VOL = [
    _Nature("colibri (vol stationnaire battu)",
            ["grand disque balayé par rapport à une masse minuscule (faible charge de disque)", "battement rapide symétrique",
             "musculature et métabolisme extrêmes"],
            "faible charge de disque (grande surface balayée / faible masse) — le levier « aire » du vivant"),
    _Nature("samare d'érable (descente en autorotation)",
            ["autorotation qui freine la chute sans énergie", "une seule aile portante en rotation"],
            "extraire de la portance du mouvement de chute lui-même (autorotation) — sustenter sans moteur"),
    _Nature("albatros (vol plané dynamique)",
            ["exploite le gradient de vent au lieu de battre", "évite le vol stationnaire coûteux"],
            "ÉVITER le stationnaire : glaner l'énergie du vent plutôt que la dépenser à brasser l'air"),
    _Nature("vessie natatoire du poisson (flottabilité neutre)",
            ["ajuste un volume de gaz pour flotter sans effort", "sustentation STATIQUE (Archimède)"],
            "flotter par portance statique à énergie quasi nulle — l'analogue de l'aérostat"),
]

enregistre(Domaine(
    nom=_VOL,
    aliases=frozenset(_ALIAS_VOL),
    objectif=_OBJECTIF_VOL,
    canaux=_CANAUX_VOL,
    principes=_PRINCIPES_VOL,
    strategies=_STRATEGIES_NATURE_VOL,
    loi=_LOI_VOL,
    extras={"puissance_induite_ideale": "P = T^1,5/√(2ρA) (théorie de la quantité de mouvement)",
            "note": "P ∝ 1/√A : un grand disque lent bat un petit jet rapide ; FM réel 0,6–0,8 ; la portance "
                    "statique (aérostat) contourne entièrement la puissance induite"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  QUATORZIÈME DOMAINE : voir plus petit / résolution optique. Nouvelle loi dure au juge (L11) : la limite de
#  DIFFRACTION d'Abbe — en champ lointain conventionnel, on ne résout pas plus fin que λ/(2·NA) ; et l'ouverture
#  numérique NA = n·sinθ ≤ n (indice du milieu). REFRAMING machine : ne pas « grossir » davantage (grandir l'image
#  ne crée pas de détail) mais AUGMENTER l'information spatiale — raccourcir λ, monter NA (immersion, plafonné par
#  l'indice), ou CONTOURNER le champ lointain : champ proche (ondes évanescentes, NSOM), localisation temporelle
#  de molécules uniques (PALM/STORM), illumination structurée (SIM), déplétion (STED). La super-résolution ne viole
#  pas Abbe : elle exploite une information hors de son régime (d'où le prix Nobel 2014).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_OPT = "resolution_optique"
_ALIAS_OPT = {
    "voir plus petit", "resoudre en microscopie", "augmenter la resolution optique",
    "observer des details fins", "depasser la limite de diffraction", "imager a l echelle nanometrique",
}

# ── « Canaux » : les leviers de la résolution optique ────────────────────────────────────────────────────────────
_CANAUX_OPT = [
    Canal("longueur d onde", "lumiere", "RACCOURCIR λ (UV, X, électrons) : la limite d'Abbe d = λ/2NA décroît avec λ",
          True, "diviser λ par 2 divise la limite par 2 ; l'UV, les rayons X et les électrons (λ picométrique) "
                "poussent la résolution bien plus bas — le levier direct sur le numérateur"),
    Canal("ouverture numerique", "lumiere", "AUGMENTER NA (immersion, indice élevé) : d ∝ 1/NA, plafonné par NA ≤ n",
          True, "l'immersion (huile n≈1,5) permet NA ~1,4 vs ~0,95 à sec ; mais NA = n·sinθ ne peut dépasser l'indice "
                "du milieu → mur physique à ~1,5 en optique visible"),
    Canal("champ proche", "lumiere", "capter les ondes ÉVANESCENTES (NSOM, superlentille) : contourne le champ lointain d'Abbe",
          True, "les détails fins sont portés par des ondes évanescentes qui meurent en champ lointain ; les lire à "
                "quelques nanomètres de l'objet (sonde à balayage) échappe à Abbe — le levier « rester tout près »"),
    Canal("localisation / commutation", "lumiere", "LOCALISER dans le temps des émetteurs isolés (PALM/STORM), illumination structurée (SIM), déplétion (STED)",
          True, "si les émetteurs s'allument un à un, on localise le CENTRE de chaque tache bien plus finement que sa "
                "largeur ; SIM/STED reconfigurent l'éclairage — le levier « séparer dans le temps ce qu'on ne peut "
                "séparer dans l'espace », cœur de la super-résolution"),
]

# ── PRINCIPES candidats — chacun JUGÉ par la limite d'Abbe (type `imagerie_optique`, résolution ≥ λ/2NA ; NA ≤ n) ──
_PRINCIPES_OPT = [
    _P("microscope optique à sec (référence)",
       "voir plus petit : objectif à sec (NA ~0,95) en lumière visible",
       {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 0.95, "indice_milieu": 1.0,
        "resolution_nm": 300}, True, True,
       "—", "mature",
       0.6, "la référence : à sec, NA plafonne vers 0,95 → résolution ~290 nm ; pour faire mieux il faut l'immersion, "
            "raccourcir λ, ou la super-résolution — pas grossir davantage"),
    _P("immersion à huile (NA élevé)",
       "voir plus petit : objectif à immersion d'huile (n≈1,5, NA ~1,4)",
       {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.4, "indice_milieu": 1.5,
        "resolution_nm": 200}, True, True,
       "—", "mature",
       0.55, "l'immersion relève NA à ~1,4 (résolution ~200 nm) ; mais NA ≤ n bute à ~1,5 en visible → le levier "
             "« ouverture » est presque épuisé, d'où le besoin de changer de régime"),
    _P("courte longueur d'onde (UV)",
       "voir plus petit : imager dans l'ultraviolet pour réduire λ",
       {"type": "imagerie_optique", "longueur_onde_nm": 250, "ouverture_numerique": 0.9, "indice_milieu": 1.0,
        "resolution_nm": 150}, True, True,
       "—", "mature (niche)",
       0.5, "λ divisé par ~2 → résolution divisée par ~2 (~140 nm) ; optiques UV coûteuses et échantillons sensibles "
            "— pousser encore (X, électrons) descend au nanomètre, le levier « raccourcir λ »"),
    _P("STED (déplétion par émission stimulée)",
       "voir plus petit : éteindre la fluorescence en couronne pour ne laisser émettre qu'un cœur sub-diffraction",
       {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.4, "indice_milieu": 1.5,
        "resolution_nm": 30, "super_resolution": True}, True, True,
       "—", "mature (super-résolution)",
       0.55, "reconfigure l'éclairage pour rétrécir le point émetteur bien SOUS Abbe (~30 nm) sans le violer ; "
             "puissances laser élevées et photoblanchiment — le levier « déplétion »"),
    _P("PALM / STORM (localisation de molécules uniques)",
       "voir plus petit : allumer les fluorophores un à un et localiser le centre de chaque tache",
       {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.4, "indice_milieu": 1.5,
        "resolution_nm": 20, "super_resolution": True}, True, True,
       "—", "mature (super-résolution)",
       0.55, "sépare les émetteurs dans le TEMPS pour localiser chaque centre à ~20 nm ; long temps d'acquisition et "
             "fluorophores commutables requis — le levier « localisation temporelle », cœur du Nobel 2014"),
    _P("illumination structurée (SIM)",
       "voir plus petit : éclairer par une grille connue et déplier le moiré pour doubler la résolution",
       {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.4, "indice_milieu": 1.5,
        "resolution_nm": 100, "super_resolution": True}, True, True,
       "—", "mature (super-résolution)",
       0.5, "le moiré entre l'objet et une grille connue ramène des détails fins dans la bande passante (~×2, "
            "~100 nm) ; gain plus modeste mais rapide et doux (cellules vivantes) — le levier « illumination »"),
    _P("champ proche (NSOM / superlentille)",
       "voir plus petit : lire les ondes évanescentes à quelques nanomètres de l'objet",
       {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 0.9, "indice_milieu": 1.0,
        "resolution_nm": 50, "super_resolution": True}, True, True,
       "—", "recherche",
       0.4, "capte les détails portés par les ondes évanescentes (perdues en champ lointain) → résolution ~λ/20, "
            "indépendante d'Abbe ; exige une sonde à quelques nm de la surface (balayage lent) — le levier « champ proche »"),
    _P("microscopie par expansion (ExM)",
       "voir plus petit : gonfler physiquement l'échantillon dans un gel avant de l'imager",
       {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.4, "indice_milieu": 1.5,
        "resolution_nm": 70, "super_resolution": True}, True, True,
       "—", "émergent",
       0.45, "au lieu d'améliorer l'optique, on AGRANDIT l'objet (gel gonflant ~4×) → les détails s'écartent au-delà "
             "d'Abbe, imagés par un microscope ordinaire ; distorsions du gel à contrôler — le levier « agrandir l'objet »"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER) ──
    _P("microscope conventionnel « résolvant 50 nm » (λ=550, NA=1,4)",
       "voir plus petit : microscope à champ lointain CONVENTIONNEL revendiquant 50 nm à λ=550 nm, NA=1,4",
       {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.4, "indice_milieu": 1.5,
        "resolution_nm": 50}, True, True,
       "—", "revendication",
       0.3, "50 nm < limite d'Abbe (~196 nm ici) sans super-résolution — à réfuter par la limite de diffraction"),
    _P("objectif « à NA 1,7 dans l'air »",
       "voir plus petit : objectif revendiquant une ouverture numérique de 1,7 dans l'air (n=1)",
       {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.7, "indice_milieu": 1.0,
        "resolution_nm": 300}, True, True,
       "—", "revendication",
       0.25, "NA = n·sinθ ≤ n : une ouverture numérique de 1,7 dans l'air (n=1) est impossible"),
]

_OBJECTIF_OPT = ("Le but réel n'est pas de « grossir » davantage (agrandir l'image ne crée aucun détail) mais "
                 "d'augmenter l'INFORMATION spatiale, bornée par la limite de diffraction d'Abbe : résolution "
                 "≥ λ/(2·NA), avec NA = n·sinθ ≤ n. Leviers : raccourcir λ (UV, X, électrons) ; monter NA "
                 "(immersion, plafonné par l'indice) ; ou CONTOURNER le champ lointain — champ proche (ondes "
                 "évanescentes, NSOM), localisation temporelle de molécules uniques (PALM/STORM), illumination "
                 "structurée (SIM), déplétion (STED). La super-résolution ne viole pas Abbe : elle exploite une "
                 "information hors de son régime. Chaque principe reste jugé par la limite de diffraction.")
_LOI_OPT = ("limite de diffraction d'Abbe : en champ lointain conventionnel, résolution ≥ λ/(2·NA), et NA = "
            "n·sinθ ≤ n (indice du milieu) ; gains réels = raccourcir λ, monter NA (jusqu'à l'indice), ou contourner "
            "par le champ proche, la localisation de molécules uniques, l'illumination structurée, la déplétion")

# La nature résout par une grande pupille (aigle), une lentille à gradient d'indice (céphalopode), des nanostructures (diatomée), du multiplexage (crevette-mante).
_STRATEGIES_NATURE_OPT = [
    _Nature("œil de l'aigle (grande pupille + rétine dense)",
            ["grande ouverture (pupille) → limite de diffraction plus fine", "densité de photorécepteurs qui échantillonne finement",
             "longue distance focale"],
            "grande ouverture + échantillonnage fin : maximiser NA et le nombre de points — le levier « ouverture »"),
    _Nature("œil à lentille à gradient d'indice (céphalopode, poisson)",
            ["indice variant en volume (GRIN) qui corrige l'aberration sphérique", "image nette jusqu'au bord"],
            "corriger l'aberration par un gradient d'indice pour ATTEINDRE la limite de diffraction, pas la dépasser"),
    _Nature("diatomée (frustule à nanostructures sous la longueur d'onde)",
            ["motifs de silice réguliers plus petits que λ", "manipulation de la lumière à l'échelle sous-longueur d'onde"],
            "structurer la matière SOUS λ pour maîtriser la lumière (photonique) — parent du champ proche"),
    _Nature("œil de la crevette-mante (multiplexage spectral/polarisation)",
            ["seize canaux spectraux + détection de polarisation", "plus d'information par point, pas plus de points"],
            "MULTIPLEXER l'information (couleur, polarisation) plutôt que la seule résolution spatiale — un autre axe"),
]

enregistre(Domaine(
    nom=_OPT,
    aliases=frozenset(_ALIAS_OPT),
    objectif=_OBJECTIF_OPT,
    canaux=_CANAUX_OPT,
    principes=_PRINCIPES_OPT,
    strategies=_STRATEGIES_NATURE_OPT,
    loi=_LOI_OPT,
    extras={"limite_abbe": "d = λ/(2·NA) (champ lointain conventionnel)",
            "note": "NA = n·sinθ ≤ n ; la super-résolution (champ proche, localisation, SIM, STED) contourne le "
                    "champ lointain sans violer Abbe"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  QUINZIÈME DOMAINE : capter l'énergie du vent (éolienne). Nouvelle loi dure au juge (L12) : la limite de BETZ —
#  un rotor ouvert extrait au plus 16/27 (≈ 59,3 %) de la puissance cinétique du vent ½ρAv³ qui traverse son
#  disque (on ne peut pas arrêter TOUT l'air : il doit continuer à s'écouler). REFRAMING machine : le mur n'est
#  pas la taille des pales mais 59,3 % ; la puissance disponible croît LINÉAIREMENT avec l'aire balayée A et au
#  CUBE de la vitesse du vent v. Leviers : agrandir l'aire balayée (A) ; choisir un site plus venté (v³, d'où
#  l'offshore et la hauteur) ; approcher Betz (profils, vitesse spécifique) ; caréner (diffuseur : dépasse Betz par
#  rapport à l'aire du rotor, pas à l'aire frontale totale).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_VENT = "energie_eolienne"
_ALIAS_VENT = {
    "capter l energie du vent", "produire de l electricite eolienne", "exploiter le vent",
    "eolienne", "convertir l energie du vent", "recuperer l energie du vent",
}

# ── « Canaux » : les leviers de la puissance éolienne captée ─────────────────────────────────────────────────────
_CANAUX_VENT = [
    Canal("aire balayee", "vent", "AGRANDIR l'aire balayée A : la puissance disponible ½ρAv³ croît linéairement avec A",
          True, "doubler le diamètre quadruple l'aire donc la puissance ; c'est le levier des rotors géants "
                "offshore — mais la fraction extractible reste plafonnée à 16/27"),
    Canal("vitesse du site", "vent", "CHOISIR un site plus venté (la puissance croît au CUBE de v)",
          True, "+26 % de vent = ×2 de puissance (v³) → l'offshore et la hauteur de mât (le vent forcit avec "
                "l'altitude) priment sur presque tout le reste ; le site est la variable reine"),
    Canal("approche de Betz", "vent", "APPROCHER la limite de Betz : profils de pale et vitesse spécifique optimaux",
          True, "un bon tripale atteint Cp ~0,45–0,50 sur 0,593 possible → il reste peu à grappiller sur le "
                "coefficient ; l'essentiel des gains vient de A et v, pas du raffinement aérodynamique"),
    Canal("carenage", "vent", "CARÉNER (diffuseur) : concentrer le flux pour dépasser Betz par rapport à l'aire du ROTOR",
          True, "un diffuseur aspire plus d'air dans le rotor → Cp>0,593 par aire de rotor (mais pas par aire "
                "frontale totale) ; poids et coût du carénage → surtout pour le petit éolien — le levier « concentrer le flux »"),
]

# ── PRINCIPES candidats — chacun JUGÉ par la limite de Betz (type `eolienne`, Cp ≤ 16/27 ; rotor ouvert) ──────────
_PRINCIPES_VENT = [
    _P("éolienne tripale à axe horizontal (référence)",
       "capter le vent : rotor tripale rapide à axe horizontal face au vent",
       {"type": "eolienne", "coefficient_puissance": 0.45}, False, True,
       "—", "mature",
       0.65, "la référence dominante : Cp ~0,45 sur 0,593 possible → déjà proche du mur de Betz ; les gains "
             "viennent désormais de la taille et du site, pas du coefficient — la référence à comprendre"),
    _P("grand rotor offshore",
       "capter le vent : rotor de très grand diamètre en mer",
       {"type": "eolienne", "coefficient_puissance": 0.48}, False, True,
       "—", "mature",
       0.6, "l'aire balayée (∝ D²) et un vent marin fort et régulier maximisent ½ρAv³ ; fondations et maintenance "
            "en mer coûteuses — le levier « aire × site » incarné"),
    _P("site très venté / mât haut (v³)",
       "capter le vent : implanter là où le vent est fort et monter le mât (le vent forcit avec l'altitude)",
       {"type": "eolienne", "coefficient_puissance": 0.46}, False, True,
       "—", "mature",
       0.6, "la puissance croît au CUBE de v : +26 % de vent double la production → le site et la hauteur priment ; "
            "contraintes de raccordement et d'acceptation — le levier « vitesse » (le plus rentable)"),
    _P("profil de pale optimisé (approcher Betz)",
       "capter le vent : profils et vitesse spécifique optimaux pour approcher le coefficient de Betz",
       {"type": "eolienne", "coefficient_puissance": 0.50}, True, True,
       "—", "mature",
       0.5, "raffiner l'aérodynamique gagne quelques points vers 0,593 (plafond) → rendement marginal décroissant ; "
            "bruit et érosion de bord d'attaque à gérer — le levier « approcher Betz », bientôt épuisé"),
    _P("éolienne carénée à diffuseur",
       "capter le vent : un carénage/diffuseur concentre le flux et augmente la puissance par aire de rotor",
       {"type": "eolienne", "coefficient_puissance": 0.7, "avec_diffuseur": True}, False, True,
       "—", "recherche (petit éolien)",
       0.4, "le diffuseur aspire plus d'air → dépasse Betz PAR AIRE DE ROTOR (pas par aire frontale totale) ; poids "
            "et coût du carénage le réservent au petit éolien — le levier « concentrer le flux », sans violer Betz"),
    _P("éolienne à axe vertical (VAWT)",
       "capter le vent : rotor à axe vertical, omnidirectionnel, générateur au sol",
       {"type": "eolienne", "coefficient_puissance": 0.35}, False, True,
       "—", "mature (niche)",
       0.45, "capte le vent de toute direction et met le générateur au sol (maintenance) ; Cp plus bas que le "
             "tripale → densité de puissance moindre, mais robuste et compact (urbain, offshore flottant dense)"),
    _P("éolien aéroporté (cerf-volant / aile captive)",
       "capter le vent : une aile captive vole en altitude où le vent est plus fort et régulier",
       {"type": "eolienne", "coefficient_puissance": 0.40}, True, True,
       "—", "recherche",
       0.4, "atteint des altitudes où le vent est bien plus fort (v³) avec très peu de matière (pas de mât ni de "
            "grand rotor) ; pilotage automatique et fiabilité à prouver — le levier « monter chercher le vent »"),
    _P("multi-rotor sur un même mât",
       "capter le vent : plusieurs rotors moyens sur une structure partagée plutôt qu'un seul géant",
       {"type": "eolienne", "coefficient_puissance": 0.44}, False, True,
       "—", "recherche",
       0.4, "des rotors plus petits, moins chers et interchangeables couvrent une grande aire totale ; complexité "
            "structurelle et sillages entre rotors — variante du levier « aire »"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER) ──
    _P("éolienne « à Cp 0,7 » (rotor ouvert)",
       "capter le vent : rotor ouvert revendiquant un coefficient de puissance de 0,7",
       {"type": "eolienne", "coefficient_puissance": 0.7}, False, True,
       "—", "revendication",
       0.3, "0,7 > limite de Betz (16/27 ≈ 0,593) pour un rotor ouvert — on ne peut extraire plus de 16/27 de la "
            "puissance du vent ; à réfuter par la limite de Betz"),
    _P("éolienne « 50 kW sur 100 m² à 10 m/s »",
       "capter le vent : extraire 50 kW d'un vent de 10 m/s sur une aire balayée de 100 m²",
       {"type": "eolienne", "puissance_W": 50000, "aire_balayee_m2": 100, "vitesse_vent_m_s": 10}, False, True,
       "—", "revendication",
       0.25, "la puissance du vent ici est ~61 kW (½ρAv³) ; Betz la plafonne à ~36 kW → 50 kW est impossible"),
]

_OBJECTIF_VENT = ("Le but réel n'est pas de « freiner le vent » au maximum (arrêter tout l'air annulerait le débit) "
                  "mais d'extraire le plus de puissance possible sous la limite de BETZ : au plus 16/27 (≈ 59,3 %) "
                  "de la puissance du vent ½ρAv³ traversant le disque. La puissance disponible croît LINÉAIREMENT "
                  "avec l'aire balayée A et au CUBE de la vitesse v. Leviers : agrandir A (rotors géants) ; choisir "
                  "un site plus venté et monter le mât (v³ → offshore, altitude) ; approcher Betz (profils, vitesse "
                  "spécifique) ; caréner (diffuseur, qui dépasse Betz par aire de rotor mais pas par aire frontale "
                  "totale). Chaque principe reste jugé par la limite de Betz.")
_LOI_VENT = ("limite de Betz : une éolienne à rotor ouvert extrait au plus 16/27 (≈ 59,3 %) de la puissance du vent "
             "½ρAv³ traversant son disque ; la puissance disponible est linéaire en aire balayée A et au cube de la "
             "vitesse v ; gains réels = agrandir A, viser un site plus venté (v³), approcher Betz, caréner (par aire "
             "de rotor)")

# La nature capte le vent par la traînée (pissenlit), la flexibilité (arbre), le cisaillement (oiseau), l'ondulation (graminée).
_STRATEGIES_NATURE_VENT = [
    _Nature("akène de pissenlit (vortex de traînée)",
            ["une aigrette poreuse crée un vortex stable qui capte la traînée du vent", "portance de traînée avec très peu de matière"],
            "capter la force du vent avec un minimum de matière poreuse — l'efficacité par gramme"),
    _Nature("arbre flexible (reconfiguration sous le vent)",
            ["ploie et réoriente ses branches pour réduire la charge", "survit aux rafales en se déformant"],
            "PLOIER pour réduire la charge et survivre aux extrêmes — la résilience structurelle face au vent"),
    _Nature("oiseau en vol dynamique (cisaillement de vent)",
            ["extrait l'énergie du GRADIENT de vitesse du vent en altitude", "parcourt de longues distances sans battre"],
            "récolter l'énergie du CISAILLEMENT de vent en hauteur — le levier « monter chercher le vent »"),
    _Nature("graminée / épillet (ondulation dissipative)",
            ["ondule pour dissiper l'énergie du vent sans casser", "tige élancée à faible traînée"],
            "onduler pour encaisser le vent sans rompre — capter/résister par la souplesse"),
]

enregistre(Domaine(
    nom=_VENT,
    aliases=frozenset(_ALIAS_VENT),
    objectif=_OBJECTIF_VENT,
    canaux=_CANAUX_VENT,
    principes=_PRINCIPES_VENT,
    strategies=_STRATEGIES_NATURE_VENT,
    loi=_LOI_VENT,
    extras={"limite_betz": "Cp ≤ 16/27 ≈ 0,593 (rotor ouvert)",
            "note": "puissance disponible ½ρAv³ : linéaire en aire A, au cube de la vitesse v ; le carénage dépasse "
                    "Betz par aire de rotor, pas par aire frontale totale"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  SEIZIÈME DOMAINE : atteindre une grande vitesse dans le vide (propulsion spatiale). Nouvelle loi dure au juge
#  (L13) : l'équation de TSIOLKOVSKI — Δv ≤ ve·ln(m₀/mf). Le gain de vitesse ne croît qu'au LOGARITHME du rapport
#  de masse : embarquer toujours plus de propergol donne des retours décroissants (la « tyrannie de l'équation de
#  la fusée »). REFRAMING machine : le levier n'est PAS d'ajouter du carburant mais d'augmenter la VITESSE
#  D'ÉJECTION ve (impulsion spécifique — d'où l'électrique/ionique, le nucléaire), d'ÉTAGER (larguer la masse
#  morte), ou d'exploiter un MOMENTUM EXTERNE (assistance gravitationnelle, voile solaire, ravitaillement in situ)
#  qui n'est pas borné par le propergol embarqué. Distinct de L4 (conservation de la quantité de mouvement).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_FUSEE = "propulsion_spatiale"
_ALIAS_FUSEE = {
    "atteindre une grande vitesse dans le vide", "propulser un vaisseau spatial", "propulsion spatiale",
    "accelerer une fusee", "voyager dans l espace", "gagner de la vitesse dans l espace",
}

# ── « Canaux » : les leviers du Δv atteignable ───────────────────────────────────────────────────────────────────
_CANAUX_FUSEE = [
    Canal("vitesse d ejection", "vitesse", "AUGMENTER la vitesse d'éjection ve (impulsion spécifique) : Δv est LINÉAIRE en ve",
          True, "Δv = ve·ln(m₀/mf) : doubler ve double le Δv, alors qu'empiler du propergol ne l'augmente qu'en "
                "logarithme → l'électrique/ionique (ve ~30 km/s) et le nucléaire écrasent le chimique (ve ~4,5 km/s)"),
    Canal("etagement", "vitesse", "ÉTAGER : larguer les réservoirs vides pour ne plus accélérer de masse morte",
          True, "chaque étage repart avec un meilleur rapport de masse effectif → contourne les retours "
                "décroissants d'un réservoir unique géant ; complexité et fiabilité des séparations"),
    Canal("masse a vide", "vitesse", "ALLÉGER la structure (masse à vide mf) : augmente le rapport de masse m₀/mf",
          True, "moins de masse sèche = rapport de masse plus élevé = plus de Δv ; réservoirs et structures "
                "ultralégers — mais le gain reste logarithmique, d'où la priorité à ve"),
    Canal("momentum externe", "vitesse", "EXPLOITER un momentum EXTERNE : assistance gravitationnelle, voile solaire, ravitaillement in situ",
          True, "un Δv qui ne vient PAS de ton propergol échappe entièrement à Tsiolkovski : fronde gravitationnelle "
                "(gratuit), poussée du Soleil (voile), refaire le plein en route (ISRU) — le levier « ne pas tout emporter »"),
]

# ── PRINCIPES candidats — chacun JUGÉ par l'équation de Tsiolkovski (type `fusee`, Δv ≤ ve·ln(m₀/mf)) ─────────────
_PRINCIPES_FUSEE = [
    _P("fusée chimique (référence)",
       "propulsion spatiale : moteur chimique à forte poussée, vitesse d'éjection ~4,5 km/s",
       {"type": "fusee", "delta_v_m_s": 13000, "vitesse_ejection_m_s": 4500, "rapport_masse": 20}, False, True,
       "—", "mature",
       0.65, "forte poussée pour décoller, MAIS faible ve (~4,5 km/s) → il faut un énorme rapport de masse pour peu "
             "de Δv (retours logarithmiques) ; la référence dont la limite pousse à monter ve ou étager"),
    _P("propulsion électrique / ionique (Isp élevé)",
       "propulsion spatiale : moteur ionique éjectant à ~30 km/s, faible poussée mais très efficace",
       {"type": "fusee", "delta_v_m_s": 12000, "vitesse_ejection_m_s": 30000, "rapport_masse": 1.5}, True, True,
       "—", "mature (spatial)",
       0.6, "ve ~7× le chimique → beaucoup de Δv pour peu de propergol (rapport de masse modeste) ; poussée "
            "minuscule (accélération lente) → transferts longs — le levier « augmenter ve » incarné"),
    _P("étagement (fusée multi-étages)",
       "propulsion spatiale : larguer les étages vides pour améliorer le rapport de masse effectif",
       {"type": "fusee", "delta_v_m_s": 18000, "vitesse_ejection_m_s": 4500, "rapport_masse": 60}, False, True,
       "—", "mature",
       0.55, "sans étagement, un rapport de masse de 60 est irréaliste (structure) ; en étageant, chaque étage "
             "repart léger → Δv cumulé bien plus haut — le levier « larguer la masse morte », clé de l'orbite"),
    _P("propulsion nucléaire thermique",
       "propulsion spatiale : chauffer un propergol léger (hydrogène) par un réacteur, ve ~9 km/s",
       {"type": "fusee", "delta_v_m_s": 14000, "vitesse_ejection_m_s": 9000, "rapport_masse": 5}, False, True,
       "—", "recherche",
       0.45, "double la ve du chimique en chauffant de l'hydrogène (bas poids moléculaire) → bon Δv à poussée "
             "élevée ; masse du réacteur et sûreté — le compromis poussée/ve pour l'interplanétaire"),
    _P("propulsion nucléaire pulsée (type Orion)",
       "propulsion spatiale : impulsions d'explosions nucléaires derrière un bouclier, ve très élevée",
       {"type": "fusee", "delta_v_m_s": 40000, "vitesse_ejection_m_s": 30000, "rapport_masse": 4}, False, True,
       "—", "concept",
       0.35, "ve énorme ET forte poussée simultanément → Δv très grand (interstellaire lent envisageable) ; "
             "retombées et traité d'interdiction — concept borné par la physique, pas par elle interdit"),
    _P("voile solaire (momentum externe)",
       "propulsion spatiale : se laisser pousser par la pression de radiation du Soleil, sans propergol",
       {"type": "fusee"}, True, True,
       "—", "démontré",
       0.5, "REFRAMING : le Δv vient du Soleil, PAS d'un propergol embarqué → échappe entièrement à Tsiolkovski "
            "(accélération faible mais gratuite et sans fin) ; grande voile et faible poussée — « ne rien emporter »"),
    _P("assistance gravitationnelle (fronde)",
       "propulsion spatiale : gagner de la vitesse en frôlant une planète (échange de quantité de mouvement)",
       {"type": "fusee"}, True, True,
       "—", "mature",
       0.5, "emprunte du momentum au mouvement orbital d'une planète → Δv « gratuit » hors du propergol ; exige un "
            "alignement et un calcul de trajectoire précis — le levier « momentum externe » (Voyager, Cassini)"),
    _P("ravitaillement en orbite / in situ (ISRU)",
       "propulsion spatiale : refaire le plein en route (dépôts orbitaux, ergols produits sur place)",
       {"type": "fusee"}, True, True,
       "—", "émergent",
       0.45, "remettre m₀ à son maximum en cours de route RÉINITIALISE l'équation → contourne le rapport de masse "
             "d'un seul plein ; logistique de dépôts et production d'ergols (eau lunaire, CO₂ martien) à bâtir"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER) ──
    _P("fusée chimique « à 30 km/s » (ve 4,5 km/s, rapport 20)",
       "propulsion spatiale : atteindre 30 km/s de Δv avec un moteur chimique (ve 4,5 km/s) et un rapport de masse de 20",
       {"type": "fusee", "delta_v_m_s": 30000, "vitesse_ejection_m_s": 4500, "rapport_masse": 20}, False, True,
       "—", "revendication",
       0.3, "30 km/s > Δv max de Tsiolkovski (~13,5 km/s ici) — impossible avec ce propergol embarqué ; à réfuter"),
    _P("fusée « qui accélère sans consommer d'ergols » (rapport de masse 1)",
       "propulsion spatiale : gagner du Δv sans éjecter de masse (rapport de masse m₀/mf = 1)",
       {"type": "fusee", "delta_v_m_s": 5000, "vitesse_ejection_m_s": 4500, "rapport_masse": 1}, False, True,
       "—", "revendication",
       0.25, "rapport de masse 1 → ln(1) = 0 → Δv max nul : sans éjecter de propergol, une fusée ne gagne aucun Δv "
             "(à distinguer d'un momentum externe) — impossible"),
]

_OBJECTIF_FUSEE = ("Le but réel n'est pas d'« emporter plus de carburant » : l'équation de Tsiolkovski Δv = "
                   "ve·ln(m₀/mf) montre que le Δv ne croît qu'au LOGARITHME du rapport de masse — les retours sont "
                   "décroissants (la « tyrannie de l'équation de la fusée »). Leviers : augmenter la VITESSE "
                   "D'ÉJECTION ve (Δv linéaire en ve → électrique/ionique, nucléaire) ; ÉTAGER (larguer la masse "
                   "morte) ; alléger la structure ; et surtout exploiter un MOMENTUM EXTERNE (assistance "
                   "gravitationnelle, voile solaire, ravitaillement in situ) qui échappe entièrement au propergol "
                   "embarqué. Chaque principe reste jugé par l'équation de Tsiolkovski.")
_LOI_FUSEE = ("équation de Tsiolkovski : Δv ≤ ve·ln(m₀/mf) — le gain de vitesse croît seulement au logarithme du "
              "rapport de masse ; gains réels = augmenter la vitesse d'éjection ve (Δv linéaire en ve), étager, "
              "alléger, et exploiter un momentum externe (fronde gravitationnelle, voile, ISRU) hors du propergol")

# La nature propulse par jet pulsé (salpe), éjection balistique (concombre), jet chimique (bombardier), momentum externe (raie manta).
_STRATEGIES_NATURE_FUSEE = [
    _Nature("salpe / méduse (jet pulsé efficace)",
            ["propulsion par pulsations à basse vitesse d'éjection", "très efficace pour de faibles gains de vitesse"],
            "éjecter beaucoup de masse lentement quand on vise un petit Δv — le compromis ve/rapport de masse"),
    _Nature("concombre sauvage (éjection balistique)",
            ["libère graines et fluide en une impulsion violente", "toute l'énergie dans une éjection unique"],
            "concentrer la poussée en une impulsion unique à haute vitesse d'éjection — le levier « ve élevée »"),
    _Nature("coléoptère bombardier (jet chimique)",
            ["réaction chimique explosive expulsant un jet dirigé", "réactifs stockés et mélangés à la demande"],
            "emporter des réactifs denses et les convertir en jet à la demande — l'analogue du propergol chimique"),
    _Nature("raie manta / planeur des courants (momentum externe)",
            ["exploite les courants marins pour avancer sans dépenser", "glisse sur l'énergie du milieu"],
            "emprunter le momentum du MILIEU plutôt que dépenser sa propre réserve — l'analogue de la fronde/voile"),
]

enregistre(Domaine(
    nom=_FUSEE,
    aliases=frozenset(_ALIAS_FUSEE),
    objectif=_OBJECTIF_FUSEE,
    canaux=_CANAUX_FUSEE,
    principes=_PRINCIPES_FUSEE,
    strategies=_STRATEGIES_NATURE_FUSEE,
    loi=_LOI_FUSEE,
    extras={"tsiolkovski": "Δv = ve·ln(m₀/mf)",
            "note": "Δv logarithmique en rapport de masse ; leviers = vitesse d'éjection ve (Isp), étagement, "
                    "momentum externe (fronde, voile, ISRU) hors du propergol embarqué"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  DIX-SEPTIÈME DOMAINE : nourrir / cultiver. Nouvelle loi dure au juge (L14) : le PLAFOND de rendement
#  PHOTOSYNTHÉTIQUE — la conversion solaire→biomasse est bornée (~12 % théorique avant respiration ; réalisé
#  ~1–6 % ; champ ~1–2 %) par la fraction utile du spectre (PAR ~48 %) et le rendement quantique. REFRAMING
#  machine : le but n'est pas la biomasse brute mais un maximum de CALORIES COMESTIBLES par surface, par eau et
#  par intrant. Leviers : combler l'écart au théorique (voie C4, court-circuiter la photorespiration, architecture
#  de canopée) ; SAUTER la photosynthèse (fermentation gazeuse H₂/CO₂ → protéine microbienne, découplée du sol et
#  du soleil) ; algues/cyanobactéries (plus efficaces) ; environnement contrôlé ; améliorer l'indice de récolte et
#  manger BAS dans la chaîne trophique (chaque niveau perd ~90 %).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_NOURRIR = "production_alimentaire"
_ALIAS_NOURRIR = {
    "nourrir", "cultiver", "produire de la nourriture", "produire des calories",
    "faire pousser des aliments", "produire de la biomasse alimentaire",
}

# ── « Canaux » : les leviers de la production de calories comestibles ─────────────────────────────────────────────
_CANAUX_NOURRIR = [
    Canal("rendement photosynthetique", "biomasse", "COMBLER l'écart au plafond théorique : voie C4, court-circuiter la photorespiration, canopée optimale",
          True, "le champ (~1–2 %) est loin du théorique (~6 %) : réduire la photorespiration (Rubisco), concentrer "
                "le CO₂ (C4), optimiser l'architecture foliaire — le levier « approcher le plafond »"),
    Canal("decouplage", "biomasse", "SAUTER la photosynthèse : fermentation gazeuse (H₂/CO₂ → protéine microbienne)",
          True, "produire des protéines à partir d'électricité, d'H₂ et de CO₂ (microbes) découple la nourriture du "
                "sol et du soleil → rendement surfacique bien supérieur ; énergie et bioréacteurs à fournir"),
    Canal("niveau trophique", "biomasse", "manger BAS dans la chaîne : chaque niveau trophique perd ~90 % de l'énergie",
          True, "convertir la biomasse végétale en viande gaspille ~90 % de l'énergie par niveau → manger les "
                "plantes (ou des microbes) directement multiplie les calories disponibles — le levier « chaîne courte »"),
    Canal("indice de recolte", "biomasse", "augmenter la FRACTION COMESTIBLE (indice de récolte) et réduire les pertes",
          True, "ne compte que ce qui finit dans l'assiette : maximiser la part comestible de la plante et réduire "
                "les pertes post-récolte donne des calories sans plus de photosynthèse — le levier « moins de gaspillage »"),
]

# ── PRINCIPES candidats — chacun JUGÉ par le plafond photosynthétique (type `photosynthese`, rendement ≤ ~12 %) ───
_PRINCIPES_NOURRIR = [
    _P("grande culture C3 en plein champ (référence)",
       "nourrir : culture C3 (blé, riz) en plein champ",
       {"type": "photosynthese", "rendement_solaire_biomasse": 0.01}, True, True,
       "—", "mature",
       0.65, "la référence mondiale : ~1 % du solaire en biomasse (photorespiration, saison, canopée) → loin du "
             "théorique ~4,6 % ; l'écart est le gisement, pas un mur physique"),
    _P("plante en C4 (maïs, canne, sorgho)",
       "nourrir : culture C4 qui concentre le CO₂ autour de la Rubisco",
       {"type": "photosynthese", "rendement_solaire_biomasse": 0.03}, True, True,
       "—", "mature",
       0.6, "la voie C4 supprime la photorespiration en pompant le CO₂ → ~2–3× le rendement du C3 en climat chaud ; "
            "porter le C4 dans le riz est un grand chantier — le levier « supprimer la photorespiration »"),
    _P("microalgue en photobioréacteur",
       "nourrir : cultiver des microalgues en réacteur éclairé",
       {"type": "photosynthese", "rendement_solaire_biomasse": 0.05}, True, True,
       "—", "émergent",
       0.5, "les microalgues approchent mieux le plafond (~5 %) et poussent sur des terres non arables/eau salée ; "
            "coût de récolte et d'énergie du réacteur — le levier « organisme plus efficace »"),
    _P("cyanobactérie optimisée",
       "nourrir : cyanobactéries ingénierées pour la protéine et les lipides",
       {"type": "photosynthese", "rendement_solaire_biomasse": 0.06}, True, True,
       "—", "recherche",
       0.45, "proches du maximum réaliste (~6 %), croissance rapide, fixation directe du CO₂ ; passage à l'échelle "
             "et stabilité des souches à prouver — pousser vers le plafond théorique"),
    _P("ingénierie de la photorespiration (court-circuit)",
       "nourrir : voie synthétique qui recycle le sous-produit de la photorespiration dans le chloroplaste",
       {"type": "photosynthese", "rendement_solaire_biomasse": 0.04}, True, True,
       "—", "recherche",
       0.45, "récupérer l'énergie perdue par la photorespiration a montré +20–40 % de biomasse au champ (essais "
             "tabac) → gisement direct ; transfert aux céréales à valider — le levier « colmater les pertes »"),
    _P("fermentation gazeuse (H₂/CO₂ → protéine microbienne)",
       "nourrir : produire des protéines microbiennes à partir d'électricité, d'hydrogène et de CO₂",
       {"type": "photosynthese"}, True, True,
       "—", "émergent",
       0.5, "REFRAMING : découple la nourriture du SOL et du SOLEIL (usine, pas champ) → rendement surfacique "
            "colossal, insensible à la météo ; demande de l'énergie propre et des bioréacteurs — « sauter la photosynthèse »"),
    _P("agriculture en environnement contrôlé (vertical, LED accordées)",
       "nourrir : cultures empilées sous LED aux longueurs d'onde optimales, climat maîtrisé",
       {"type": "photosynthese", "rendement_solaire_biomasse": 0.05}, True, True,
       "—", "mature (niche)",
       0.4, "éclairage accordé à la photosynthèse, zéro pesticide, très peu d'eau, rendement surfacique élevé ; "
            "MAIS l'électricité de la LED est un coût — gagnant si l'énergie est propre et bon marché"),
    _P("bas niveau trophique / indice de récolte",
       "nourrir : manger directement plantes/microbes et maximiser la fraction comestible récoltée",
       {"type": "photosynthese"}, True, True,
       "—", "mature (sous-exploité)",
       0.5, "chaque niveau trophique perd ~90 % → manger bas dans la chaîne et augmenter la part comestible multiplie "
            "les calories SANS plus de photosynthèse ; changement de régime et de variétés — le levier « chaîne courte »"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER) ──
    _P("culture « à 25 % de rendement solaire »",
       "nourrir : culture convertissant 25 % de l'énergie solaire en biomasse",
       {"type": "photosynthese", "rendement_solaire_biomasse": 0.25}, True, True,
       "—", "revendication",
       0.3, "25 % > plafond photosynthétique (~12 % théorique, ~6 % réalisé) — impossible ; à réfuter par le plafond "
            "de rendement photosynthétique"),
    _P("biomasse « produisant plus d'énergie que le soleil reçu »",
       "nourrir : plante restituant plus d'énergie qu'elle n'en reçoit du soleil",
       {"type": "photosynthese", "rendement_solaire_biomasse": 1.5}, True, True,
       "—", "revendication",
       0.25, "rendement 150 % : la biomasse contiendrait plus d'énergie que le rayonnement reçu = création nette — "
             "impossible"),
]

_OBJECTIF_NOURRIR = ("Le but réel n'est pas la biomasse brute mais un maximum de CALORIES COMESTIBLES par surface, "
                     "par eau et par intrant, sous le plafond de la photosynthèse : la conversion solaire→biomasse "
                     "est bornée (~12 % théorique, ~1–6 % réalisé). Leviers : combler l'écart au plafond (voie C4, "
                     "court-circuiter la photorespiration, canopée) ; SAUTER la photosynthèse (fermentation gazeuse "
                     "H₂/CO₂ → protéine microbienne, découplée du sol et du soleil) ; organismes plus efficaces "
                     "(algues/cyanobactéries) ; environnement contrôlé ; améliorer l'indice de récolte et manger BAS "
                     "dans la chaîne trophique (chaque niveau perd ~90 %). Chaque principe reste jugé par le plafond "
                     "photosynthétique.")
_LOI_NOURRIR = ("plafond de rendement photosynthétique : la conversion solaire→biomasse ≤ ~12 % (théorique, avant "
                "respiration ; réalisé ~1–6 %) ; gains réels = combler l'écart au plafond (C4, photorespiration, "
                "canopée), sauter la photosynthèse (fermentation gazeuse), manger bas dans la chaîne trophique, "
                "améliorer l'indice de récolte")

# La nature nourrit par la concentration du CO₂ (C4), l'économie d'eau (CAM), la symbiose (rhizobium), l'échelle (phytoplancton).
_STRATEGIES_NATURE_NOURRIR = [
    _Nature("plante en C4 (pompe à CO₂ autour de la Rubisco)",
            ["concentre le CO₂ sur le site de fixation", "supprime la photorespiration", "meilleur rendement en climat chaud"],
            "concentrer le CO₂ pour supprimer la perte de photorespiration — le levier « approcher le plafond »"),
    _Nature("plante CAM (stockage nocturne du CO₂)",
            ["fixe le CO₂ la nuit pour ouvrir les stomates au frais", "économise l'eau en milieu aride"],
            "séparer dans le TEMPS la capture du CO₂ et la photosynthèse pour économiser l'eau — cultiver le sec"),
    _Nature("symbiose légumineuse-rhizobium (azote gratuit)",
            ["bactéries fixant l'azote de l'air dans les racines", "fertilité sans engrais de synthèse"],
            "externaliser la fourniture de nutriments à un partenaire — réduire l'intrant, pas le rendement brut"),
    _Nature("phytoplancton océanique (fixation à grande échelle)",
            ["fixe la moitié du carbone de la planète", "croissance rapide sur une immense surface d'eau"],
            "produire de la biomasse à l'ÉCHELLE sur l'eau plutôt que sur des terres arables rares — le levier « surface »"),
]

enregistre(Domaine(
    nom=_NOURRIR,
    aliases=frozenset(_ALIAS_NOURRIR),
    objectif=_OBJECTIF_NOURRIR,
    canaux=_CANAUX_NOURRIR,
    principes=_PRINCIPES_NOURRIR,
    strategies=_STRATEGIES_NATURE_NOURRIR,
    loi=_LOI_NOURRIR,
    extras={"rendement_photo_max": "≈ 12 % (théorique, solaire→biomasse) ; réalisé ~1–6 %, champ ~1–2 %",
            "note": "sauter la photosynthèse (fermentation gazeuse H₂/CO₂→protéine) découple du sol et du soleil ; "
                    "manger bas dans la chaîne trophique évite la perte de ~90 % par niveau"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  DIX-HUITIÈME DOMAINE : compresser l'information. Nouvelle loi dure au juge (L15) : la BORNE D'ENTROPIE (codage
#  de source de Shannon) — une compression SANS PERTE ne descend pas sous l'entropie H de la source, et aucun
#  compresseur sans perte ne réduit TOUTE entrée (argument de comptage/pigeonnier). Distinct de L7 (capacité de
#  canal). REFRAMING machine : on ne « rétrécit » pas magiquement — on retire la REDONDANCE. Sans perte, la limite
#  est l'entropie (mieux MODÉLISER la source pour l'approcher) ; il n'existe pas de compresseur universel ; et la
#  compression AVEC PERTE ne gagne qu'en jetant de l'information imperceptible (fidélité contre taille).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_COMP = "compression_information"
_ALIAS_COMP = {
    "compresser des donnees", "compresser l information", "reduire la taille des donnees",
    "stocker l information densement", "comprimer un fichier", "encoder efficacement",
}

# ── « Canaux » : les leviers de la compression ───────────────────────────────────────────────────────────────────
_CANAUX_COMP = [
    Canal("modele de source", "information", "MIEUX MODÉLISER la source pour approcher son entropie H (sans perte)",
          True, "un meilleur modèle de probabilité (contextuel, prédictif) rapproche le débit de l'entropie réelle "
                "→ le gain sans perte vient de la PRÉDICTION, pas d'un tour de passe-passe ; on ne descend jamais sous H"),
    Canal("redondance", "information", "RETIRER la redondance et la répétition : dictionnaires, déduplication",
          True, "remplacer les motifs répétés par des références (LZ, dédup) capture la structure → énorme sur des "
                "données répétitives, nul sur du bruit (déjà à l'entropie) — le levier « ne pas se répéter »"),
    Canal("perte controlee", "information", "JETER l'information imperceptible (compression AVEC PERTE)",
          True, "abandonner ce que l'œil/l'oreille ne perçoit pas (perceptuel) descend SOUS l'entropie de la source "
                "en échangeant de la fidélité contre de la taille → le seul moyen de passer sous H, mais irréversible"),
    Canal("transformation", "information", "CHANGER de représentation (transformée) pour concentrer l'information",
          True, "une transformée (DCT, ondelettes) concentre l'énergie dans peu de coefficients → l'essentiel tient "
                "en peu de nombres, le reste est négligeable ; base du JPEG/MP3 — le levier « bonne représentation »"),
]

# ── PRINCIPES candidats — chacun JUGÉ par la borne d'entropie (type `compression`, sans perte ≥ H) ───────────────
_PRINCIPES_COMP = [
    _P("codage entropique (Huffman / arithmétique)",
       "compresser : coder chaque symbole selon sa probabilité pour approcher l'entropie",
       {"type": "compression", "sans_perte": True, "entropie_bits_par_symbole": 2.0, "bits_par_symbole": 2.05},
       True, True, "—", "mature",
       0.6, "atteint presque l'entropie H d'une source connue (arithmétique ~optimal) → la référence sans perte ; "
            "les gains restants viennent d'un meilleur MODÈLE, pas d'un meilleur code"),
    _P("dictionnaire / déduplication (LZ)",
       "compresser : remplacer les motifs répétés par des références à un dictionnaire",
       {"type": "compression", "sans_perte": True, "entropie_bits_par_symbole": 1.0, "bits_par_symbole": 1.1},
       True, True, "—", "mature",
       0.55, "capture la répétition (gzip, zstd, dédup de sauvegardes) → très efficace sur des données structurées, "
             "inutile sur du bruit (déjà incompressible) — le levier « redondance »"),
    _P("modèle contextuel / prédictif (PPM, transformeur)",
       "compresser : prédire le prochain symbole par le contexte, ne coder que la surprise",
       {"type": "compression", "sans_perte": True, "entropie_bits_par_symbole": 1.5, "bits_par_symbole": 1.55},
       True, True, "—", "émergent (IA)",
       0.55, "un meilleur prédicteur (grand modèle) abaisse l'entropie CONDITIONNELLE → compression sans perte "
             "record, au prix du calcul ; « compresser, c'est comprendre » — le levier « modèle de source »"),
    _P("déduplication à l'échelle (stockage)",
       "compresser : détecter et partager les blocs identiques à l'échelle d'un système de stockage",
       {"type": "compression", "sans_perte": True, "entropie_bits_par_symbole": 4.0, "bits_par_symbole": 4.1},
       True, True, "—", "mature",
       0.5, "à l'échelle d'un data-center, la plupart des blocs sont dupliqués → gains massifs sans perte ; index "
            "de hachage à maintenir — le levier « redondance » globalisé"),
    _P("transformée (DCT / ondelettes)",
       "compresser : changer de base pour concentrer l'information dans peu de coefficients (avec perte)",
       {"type": "compression", "sans_perte": False, "entropie_bits_par_symbole": 8.0, "bits_par_symbole": 0.8},
       True, True, "—", "mature",
       0.5, "concentre l'énergie du signal dans quelques coefficients, on jette le reste → forte compression AVEC "
            "perte (image/son) ; base du JPEG/MP3 — le levier « bonne représentation »"),
    _P("codage perceptuel (MP3, JPEG)",
       "compresser : supprimer ce que l'œil ou l'oreille ne perçoit pas (avec perte)",
       {"type": "compression", "sans_perte": False, "entropie_bits_par_symbole": 8.0, "bits_par_symbole": 0.5},
       True, True, "—", "mature",
       0.5, "modélise la PERCEPTION humaine pour jeter l'imperceptible → descend bien sous l'entropie du signal en "
            "gardant la qualité perçue ; irréversible — le levier « perte contrôlée »"),
    _P("codage prédictif vidéo (ne coder que le changement)",
       "compresser : ne transmettre que les différences entre images successives (avec perte)",
       {"type": "compression", "sans_perte": False, "entropie_bits_par_symbole": 8.0, "bits_par_symbole": 0.1},
       True, True, "—", "mature",
       0.5, "l'essentiel d'une vidéo est redondant d'une image à l'autre → ne coder que le mouvement/résidu réduit "
            "massivement le débit ; référence du streaming — redondance temporelle + perte contrôlée"),
    _P("représentation apprise (autoencodeur / compression neuronale)",
       "compresser : apprendre une représentation latente compacte des données (avec perte)",
       {"type": "compression", "sans_perte": False, "entropie_bits_par_symbole": 8.0, "bits_par_symbole": 0.3},
       True, True, "—", "recherche",
       0.4, "un réseau apprend une base adaptée aux données (visages, texte) → meilleure que les transformées fixes "
            "sur son domaine ; coût de calcul et généralisation hors domaine — le levier « représentation apprise »"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER) ──
    _P("compresseur sans perte « à 1 bit/symbole » (source d'entropie 4)",
       "compresser : coder SANS PERTE une source d'entropie 4 bits/symbole à 1 bit/symbole",
       {"type": "compression", "sans_perte": True, "entropie_bits_par_symbole": 4.0, "bits_par_symbole": 1.0},
       True, True, "—", "revendication",
       0.3, "1 < 4 bits/symbole : coder sans perte SOUS l'entropie de la source viole le codage de source de "
            "Shannon — à réfuter"),
    _P("compresseur sans perte « universel » (réduit tout fichier)",
       "compresser : algorithme sans perte réduisant la taille de TOUTE entrée",
       {"type": "compression", "sans_perte": True, "compresse_toute_entree": True},
       True, True, "—", "revendication",
       0.25, "aucun compresseur sans perte ne réduit TOUTE entrée (argument de comptage / pigeonnier : si certaines "
             "rétrécissent, d'autres grandissent) — impossible"),
]

_OBJECTIF_COMP = ("Le but réel n'est pas de « rétrécir » magiquement mais de retirer la REDONDANCE, sous la borne "
                  "d'entropie de Shannon : une compression SANS PERTE ne descend pas sous l'entropie H de la source, "
                  "et aucun compresseur sans perte n'est universel (argument de comptage). Leviers : mieux MODÉLISER "
                  "la source pour approcher H (codage contextuel/prédictif) ; retirer la redondance (dictionnaires, "
                  "déduplication) ; changer de représentation (transformée) ; et, pour passer SOUS H, la perte "
                  "contrôlée (jeter l'imperceptible, fidélité contre taille). Chaque principe reste jugé par la "
                  "borne d'entropie.")
_LOI_COMP = ("borne d'entropie (codage de source de Shannon) : une compression sans perte ≥ entropie H de la "
             "source (bits/symbole), et aucun compresseur sans perte ne réduit toute entrée ; gains réels = mieux "
             "modéliser la source, retirer la redondance, changer de représentation, ou accepter une perte contrôlée")

# La nature compresse par la règle courte (fractale), le motif répété (cristal), le résumé (mémoire), la réutilisation (évolution).
_STRATEGIES_NATURE_COMP = [
    _Nature("fractale naturelle (fougère, chou romanesco)",
            ["une règle de génération COURTE produit une structure complexe", "auto-similarité à toutes les échelles"],
            "décrire une structure complexe par une règle courte — la compression algorithmique (Kolmogorov)"),
    _Nature("cristal (maille répétée)",
            ["une petite maille décrit tout le solide par répétition", "l'ordre périodique = description minimale"],
            "décrire le tout par un MOTIF de base répété — le levier « redondance / périodicité »"),
    _Nature("mémoire humaine (rétention du sens, pas des détails)",
            ["garde le SENS (gist) et jette les détails littéraux", "reconstruit plausiblement le reste"],
            "conserver l'essentiel et reconstruire le reste — la compression AVEC perte du vivant"),
    _Nature("évolution modulaire (réutilisation de gènes)",
            ["réutilise des modules (domaines protéiques, gènes) au lieu de tout réinventer", "un répertoire partagé"],
            "réutiliser des modules d'un répertoire partagé plutôt que tout réencoder — le levier « dictionnaire »"),
]

enregistre(Domaine(
    nom=_COMP,
    aliases=frozenset(_ALIAS_COMP),
    objectif=_OBJECTIF_COMP,
    canaux=_CANAUX_COMP,
    principes=_PRINCIPES_COMP,
    strategies=_STRATEGIES_NATURE_COMP,
    loi=_LOI_COMP,
    extras={"borne_entropie": "sans perte ≥ H bits/symbole ; pas de compresseur sans perte universel",
            "note": "L7 = capacité de canal ≠ L15 = codage de source ; la compression avec perte échange fidélité "
                    "contre taille en descendant sous H"},
))


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  DIX-NEUVIÈME DOMAINE : isoler thermiquement / conserver la chaleur. Nouvelle loi dure au juge (L16) : le
#  PLANCHER RADIATIF de Stefan-Boltzmann — pas d'isolant parfait. On peut supprimer la conduction et la convection
#  (vide) mais PAS le rayonnement : un objet à T > T_env perd au moins ε·σ·A·(T⁴−T_env⁴), et aucun matériau réel
#  n'a une émissivité nulle. REFRAMING machine : il n'existe pas de « R infini » ; on attaque CHAQUE voie de perte
#  séparément (vide → conduction/convection ; faible émissivité / multicouche → rayonnement ; géométrie → aire et
#  gradient), mais la perte ne tombe jamais à zéro tant que T > T_env.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_ISO = "isolation_thermique"
_ALIAS_ISO = {
    "isoler thermiquement", "conserver la chaleur", "limiter les pertes de chaleur", "garder au chaud",
    "reduire les deperditions thermiques", "isoler du froid",
}

# ── « Canaux » : les leviers de la réduction des pertes thermiques ───────────────────────────────────────────────
_CANAUX_ISO = [
    Canal("conduction convection", "chaleur", "SUPPRIMER conduction et convection : créer un VIDE (ou un gaz lourd immobile)",
          True, "le vide tue les deux voies matérielles d'un coup (bouteille isotherme, panneau sous vide) → il ne "
                "reste que le rayonnement ; qualité du vide et tenue mécanique à assurer — le plus gros levier"),
    Canal("emissivite", "chaleur", "BAISSER l'émissivité : surfaces réfléchissantes, multicouches (MLI)",
          True, "des couches réfléchissantes (aluminisées) abaissent l'émissivité effective vers ~0 → attaquent le "
                "rayonnement, la voie que le vide ne bloque pas ; mais ε>0 toujours — jamais zéro"),
    Canal("aire gradient", "chaleur", "RÉDUIRE l'aire exposée et le gradient : compacité, moindre ΔT",
          True, "la perte croît avec l'aire et (radiativement) en T⁴ : une forme compacte (rapport surface/volume "
                "bas) et un moindre écart de température réduisent tout — le levier « géométrie »"),
    Canal("masse thermique", "chaleur", "TAMPONNER avec de la masse thermique / un changement de phase (retarder, pas annuler)",
          True, "une grande inertie (eau, MCP) lisse et RETARDE les variations sans réduire la perte en régime "
                "établi → utile pour passer un pic ou une nuit, pas pour isoler indéfiniment"),
]

# ── PRINCIPES candidats — chacun JUGÉ par le plancher radiatif (type `isolation_thermique`, perte ≥ εσA(T⁴−T_env⁴)) ──
_PRINCIPES_ISO = [
    _P("bouteille isotherme (vide + argenture)",
       "isoler : double paroi sous vide aux surfaces argentées (Dewar)",
       {"type": "isolation_thermique", "emissivite": 0.05, "aire_m2": 0.1, "t_objet_K": 363, "t_env_K": 293,
        "puissance_perdue_W": 5}, True, True,
       "—", "mature",
       0.65, "le vide tue conduction/convection, l'argenture le rayonnement → il ne reste qu'un plancher radiatif "
             "minuscule ; la référence de l'isolation quasi optimale — mais jamais zéro perte"),
    _P("isolant multicouche (MLI, spatial)",
       "isoler : dizaines de couches réfléchissantes sous vide (satellites)",
       {"type": "isolation_thermique", "emissivite": 0.02, "aire_m2": 1, "t_objet_K": 300, "t_env_K": 100,
        "puissance_perdue_W": 10}, True, True,
       "—", "mature (spatial)",
       0.6, "chaque couche réfléchit le rayonnement de la précédente → émissivité effective minuscule dans le vide "
            "spatial ; inefficace hors vide (les couches se touchent) — le levier « émissivité » poussé loin"),
    _P("aérogel (conduction quasi supprimée)",
       "isoler : solide nanoporeux à conductivité extrêmement basse",
       {"type": "isolation_thermique", "emissivite": 0.9, "aire_m2": 1, "t_objet_K": 323, "t_env_K": 293,
        "puissance_perdue_W": 250}, True, True,
       "—", "mature (niche)",
       0.5, "les nanopores bloquent la conduction du gaz sans vide poussé → très isolant et léger ; coût et "
            "fragilité, et le rayonnement reste (émissivité élevée) — le levier « conduction »"),
    _P("panneau isolant sous vide (VIP)",
       "isoler : coussin poreux mis sous vide et scellé (bâtiment, réfrigérateur)",
       {"type": "isolation_thermique", "emissivite": 0.1, "aire_m2": 1, "t_objet_K": 293, "t_env_K": 273,
        "puissance_perdue_W": 15}, True, True,
       "—", "mature",
       0.5, "combine cœur poreux et vide → très mince pour une forte résistance ; risque de perte du vide dans le "
            "temps (perçage) — le levier « vide » en format plaque"),
    _P("double vitrage à gaz lourd + low-e",
       "isoler : deux verres séparés par un gaz lourd, une face à basse émissivité",
       {"type": "isolation_thermique", "emissivite": 0.1, "aire_m2": 2, "t_objet_K": 293, "t_env_K": 273,
        "puissance_perdue_W": 40}, True, True,
       "—", "mature",
       0.5, "le gaz lourd (argon/krypton) freine la convection, le revêtement low-e le rayonnement → attaque les "
            "deux voies restantes ; référence du bâtiment — chaque voie traitée séparément"),
    _P("enveloppe réfléchissante (faible émissivité)",
       "isoler : recouvrir d'une surface à basse émissivité pour renvoyer le rayonnement",
       {"type": "isolation_thermique", "emissivite": 0.05, "aire_m2": 1, "t_objet_K": 313, "t_env_K": 293,
        "puissance_perdue_W": 20}, True, True,
       "—", "mature",
       0.45, "une feuille réfléchissante renvoie le rayonnement thermique → utile en complément (couverture de "
             "survie, sous-toiture) ; ne fait rien contre la conduction directe — le levier « émissivité » simple"),
    _P("masse thermique / matériau à changement de phase",
       "isoler : tamponner les variations avec une grande inertie thermique (retarde, ne supprime pas)",
       {"type": "isolation_thermique"}, True, True,
       "—", "mature",
       0.4, "lisse et RETARDE les pics (mur épais, MCP) sans réduire la perte en régime établi → complément de "
            "l'isolation, pas un substitut ; utile pour passer une nuit/un pic — le levier « inertie »"),
    _P("rupture des ponts thermiques",
       "isoler : éliminer les chemins de conduction concentrés (fixations, jonctions)",
       {"type": "isolation_thermique"}, True, True,
       "—", "mature (sous-exploité)",
       0.45, "un pont thermique (ossature, fixation métallique) court-circuite tout l'isolant autour → les traiter "
             "récupère des pertes invisibles ; détail de conception souvent négligé — le levier « chemins parasites »"),
    # ── PRINCIPES IMPOSSIBLES (à RÉFUTER) ──
    _P("isolation « parfaite » (zéro perte à 373 K vers 293 K)",
       "isoler : maintenir un objet à 373 K dans un environnement à 293 K sans aucune perte de chaleur",
       {"type": "isolation_thermique", "emissivite": 0.5, "aire_m2": 1, "t_objet_K": 373, "t_env_K": 293,
        "puissance_perdue_W": 0}, True, True,
       "—", "revendication",
       0.3, "zéro perte < plancher radiatif (~340 W ici) : un objet chaud rayonne toujours vers un environnement "
            "plus froid — pas d'isolant parfait ; à réfuter par Stefan-Boltzmann"),
    _P("matériau « à émissivité nulle »",
       "isoler : surface revendiquant une émissivité de 0 (aucun rayonnement)",
       {"type": "isolation_thermique", "emissivite": 0.0, "aire_m2": 1, "t_objet_K": 373, "t_env_K": 293}, True, True,
       "—", "revendication",
       0.25, "aucun matériau réel n'a une émissivité strictement nulle (ε > 0 toujours) → pas d'isolant radiatif "
             "parfait — impossible"),
]

_OBJECTIF_ISO = ("Le but réel n'est pas un « R infini » (il n'existe pas) mais de réduire CHAQUE voie de perte au "
                 "minimum, sous le plancher fixé par le RAYONNEMENT : un objet à T > T_env perd au moins "
                 "ε·σ·A·(T⁴−T_env⁴) (Stefan-Boltzmann), même parfaitement isolé de la conduction et de la "
                 "convection. Leviers : supprimer conduction/convection par le VIDE ; baisser l'ÉMISSIVITÉ "
                 "(surfaces réfléchissantes, multicouches) pour attaquer le rayonnement ; réduire l'AIRE et le "
                 "gradient (géométrie compacte, moindre ΔT) ; tamponner par la masse thermique (retarder, pas "
                 "annuler). La perte ne tombe jamais à zéro tant que T > T_env. Chaque principe reste jugé par le "
                 "plancher radiatif.")
_LOI_ISO = ("plancher radiatif de Stefan-Boltzmann : pas d'isolant parfait — un objet à T > T_env perd au moins "
            "ε·σ·A·(T⁴−T_env⁴) par rayonnement (ε>0 toujours), même sans conduction ni convection ; gains réels = "
            "vide (conduction/convection), basse émissivité (rayonnement), géométrie compacte, moindre gradient")

# La nature isole par l'air piégé (ours polaire), la réduction d'aire (manchot), la couche épaisse (phoque), la réflexion (duvet).
_STRATEGIES_NATURE_ISO = [
    _Nature("ours polaire (poils creux piégeant l'air)",
            ["poils creux et sous-poil dense piégeant une couche d'air immobile", "peau noire absorbant le rayonnement solaire"],
            "piéger une couche d'air immobile pour tuer la convection — le levier « conduction/convection »"),
    _Nature("manchot en tortue (huddle réduisant l'aire exposée)",
            ["se serrent pour réduire la surface exposée au froid", "rotation pour partager le bord exposé"],
            "réduire l'AIRE exposée collectivement — le levier « géométrie »"),
    _Nature("graisse (blubber) du phoque",
            ["couche épaisse à faible conductivité sous la peau", "isole même immergé dans l'eau glacée"],
            "une couche épaisse à faible conductivité contre la conduction — l'isolant massif du vivant"),
    _Nature("duvet / pruine réfléchissant",
            ["surfaces claires ou cireuses renvoyant le rayonnement", "limite le gain ou la perte radiative"],
            "renvoyer le rayonnement par une surface à basse émissivité — le levier « rayonnement »"),
]

enregistre(Domaine(
    nom=_ISO,
    aliases=frozenset(_ALIAS_ISO),
    objectif=_OBJECTIF_ISO,
    canaux=_CANAUX_ISO,
    principes=_PRINCIPES_ISO,
    strategies=_STRATEGIES_NATURE_ISO,
    loi=_LOI_ISO,
    extras={"plancher_radiatif": "ε·σ·A·(T⁴−T_env⁴), σ = 5,67e-8 W/m²K⁴",
            "note": "le vide tue conduction/convection ; les multicouches baissent ε ; jamais zéro (ε>0), pas de "
                    "résistance thermique infinie"},
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
