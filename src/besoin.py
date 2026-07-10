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
