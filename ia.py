"""
IA — POINT D'ENTRÉE UNIFIÉ (« complet ≠ utilisable » : ici on rend le stack UTILISABLE comme UNE IA).

Une seule porte pour tout ce qui a été bâti, bornée par la réalité, anti-LLM (vérifie, n'affirme pas
au hasard) :

  • ia.demande(texte) / ia.demande(point_entree=, signature=, exemples=, exemples_held=)
        -> aiguille par NATURE de réalité (classifieur_domaine) vers le bon juge :
           NÉCESSITÉ (exécuteur/arithmétique) · PHYSIQUE/PASSÉ/CONVENTION (base de faits) ·
           NON-BORNÉ (abstention de prétention au vrai) · INCONNU (HORS honnête).
        Renvoie une `Reponse` (valeur VÉRIFIÉE + source, ou ABSTENTION/HORS). Jamais un faux.

  • ia.invente(nom, signature, exemples, exemples_held)
        -> tranche une fonction-cible vs CE QUI EXISTE : EXISTE_DEJA / INVENTION (+ les éléments à
           construire) / AMBIGU (+ sonde discriminante) / BRIQUE_MANQUANTE (frontière) / INCOHERENT.

  • ia.inventaire(corpus)
        -> inventaire d'un corpus + abstractions de VALEUR (réutilisation mesurée) à construire d'abord.

  • ia.apprend(corpus)
        -> phase « sommeil » : promeut l'abstraction réutilisée en capacité nommée (auto-extension sound).

Tout est composé de briques DÉJÀ VALIDÉES (classifieur 26/26, invention_gap 12/12, chercheur 11/11,
bibliothèque 11/11, auto_optimise 12/12). Cette façade n'ajoute pas de logique de vérité — elle ORCHESTRE.
"""
from __future__ import annotations

import classifieur_domaine as _C
import moteur_invention as _MI
import chercheur_invention as _CH
import bibliotheque_invention as _B
import substrat_physique as _PH
import regle as _R
import chimie as _CHIM
import coherence_physique as _COH
import physique as _PHY
import genetique as _GEN
import references as _REF
import incertitude as _INC
import prevision as _PVS
import valeurs_extremes as _EXT
import survie as _SRV
import donnees_manquantes as _MIS
import regression_robuste as _ROB
import region_multivariee as _RMV
import quantile_regression as _QR
import poisson_nonhomogene as _NHPP
import processus_gaussien as _GP
import serie_autoregressive as _AR
import calibration_sequence as _SEQ
import surdispersion as _OD
import erreurs_variables as _EIV
import proportion_binomiale as _PBI
import optimisation_bayesienne as _OBA
import calibration_ranking as _CRK
import serie_multivariee as _SMV
import bootstrap as _BST
import roc_auc as _ROC
import prior_shift as _PSH
import bma as _BMA
import agregation_previsions as _AGP
import multinomial_simultane as _MUL
import multicalibration as _MCA
import intervalle_tolerance as _TOL
import fdr_controle as _FDR
import croyance_dempster_shafer as _DST
import possibilite as _POS
import arithmetique_intervalles as _ARI
import info_gap as _IGP
import dirichlet_imprecis as _IDM
import choquet as _CHQ
import robust_bayes as _RBY
import p_box as _PBX
import prevision_walley as _WAL
import tbm as _TBM
import decision_ambiguite as _AMB
import smooth_ambiguity as _SAM
import variational_preferences as _VAR
import pac_bayes as _PAC
import kalman_robuste as _KALR
import dkw as _DKW
import rademacher as _RAD
import shiryaev as _SHI
import concentration as _CON
import e_process as _EPR
import jeux_zero_somme as _JEU
import winner_curse as _WIN
import copules as _COP
import exp3 as _EXP
import stabilite_algorithmique as _STA
import confidentialite_differentielle as _DPV
import mdl as _MDL
import covariance_grande_dim as _CGD
import importance_sampling as _IMP
import kelly as _KEL
import maximum_entropie as _MEN
import kde as _KDE
import test_permutation as _PRM
import choix_social as _SOC
import matrice_confusion as _MCF
import biais_survie as _BSV
import regression_moyenne as _RTM
import simpson as _SIM
import benford as _BEN
import ridge as _RDG
import loi_puissance as _LPU
import saint_petersbourg as _STP
import berkson as _BRK
import ergodicite as _ERG
import petits_nombres as _PNB
import dirichlet_process as _DP
import portefeuille_universel as _PFU
import bandit_contextuel as _BCX
import p_hacking as _PHK
import revelation_bayesienne as _RVB
import lindley as _LDL
import will_rogers as _WLR
import biais_longueur as _BLG
import taux_de_base as _TDB
import deux_enveloppes as _DEV
import parrondo as _PAR
import braess as _BRA
import main_chaude as _MCH
import cadrage as _CAD
import good_turing as _GTU
import conjonction as _CJN
import cout_irrecuperable as _SUN
import bertrand as _BTR
import goodhart as _GDH
import stein as _STN
import anscombe as _ANS
import aumann as _AUM
import jury_condorcet as _JRY
import allais as _ALA
import lord as _LRD
import borel_kolmogorov as _BKL
import regression_fallacieuse as _RGF
import malediction_dimension as _MDD
import pascal_mugging as _PMG
import ellsberg as _ELL
import ancrage as _ANC
import biais_publication as _BPB
import no_free_lunch as _NFL
import gibbard_satterthwaite as _GST
import jensen as _JEN
import dunning_kruger as _DKR
import surapprentissage as _SAP
import loi_grands_nombres as _LGN
import changepoint as _CHG
import echantillon_pondere as _EPO
import fermi as _FRM
import poisson as _POI
import meta_analyse as _META
import incertitude_decomposee as _DEC2
import calibration as _CAL
import bayes as _BAY
import bayes_sequentiel as _BSQ
import inference_anytime as _ANY
import conformal as _CNF
import conformal_adaptatif as _CNFA
import conformal_normalise as _CNFN
import conformal_jackknife as _CNFJ
import conformal_quantile as _CQR
import conformal_label as _CNFL
import classif_calibree as _CLF
import classif_multiclasse as _CLFMC
import calibrateurs as _CALB
import temperature as _TMP
import multilabel as _MLB
import propagation as _PRP
import decision as _DEC
import bandit as _BND
import causal as _CAU
import opinions as _OPI
import predictif as _PRD
import test_calibration as _TST
import scores_propres as _SCP
import nouveaute as _NOU
import risque_conforme as _RQC
import ensemble_calibre as _ENS
import derive_calibration as _DRV
import venn_abers as _VA
import conformal_pondere as _CNFP
import restitution as _RST
import lecteur as _LEC
import sources as _SRC
import conversation as _CONV


def juge_dispositif(spec: dict):
    """SUBSTRAT-RÉEL / OBJECTIF FINAL : juge la COHÉRENCE PHYSIQUE d'une spec de dispositif vs les lois de
    conservation/entropie (1er & 2nd principes). Renvoie (statut, raison, loi) : VIOLE (impossible, + la loi
    enfreinte) / COHERENT_BORNE (pas de violation — PAS une preuve que ça marche) / HORS (spec insuffisante).
    Complète `invente_physique` (cohérence de transduction) en jugeant l'IMPOSSIBILITÉ (ce qui ne peut exister)."""
    return _COH.juge_dispositif(spec)


def reference(valeur: str, *, quoi: str):
    """CONVENTIONS bornées : `quoi` ∈ {morse, demorse, nato, resistance, note}.
    Renvoie (statut, valeur) du moteur `references` (VÉRIFIÉ exact ou HORS si hors table). Lookup/​formule sound."""
    if quoi == "morse":
        return _REF.vers_morse(valeur)
    if quoi == "demorse":
        return _REF.depuis_morse(valeur)
    if quoi == "nato":
        return _REF.nato(valeur)
    if quoi == "resistance":
        return _REF.couleur_resistance(valeur)
    if quoi == "note":
        return _REF.frequence_note(valeur)
    return (_REF.HORS, None)


def donnee(relation: str, entite: str):
    """LECTEUR GÉNÉRIQUE DU BORNÉ DATA (#3) : lookup-ou-HORS sur une table vérifiée (faits/conventions/
    constantes ingérées) avec REPLI sur l'amorce figée base_faits. Renvoie (VERIFIE, Fait) ou (HORS, None).
    Ex. donnee('numero_atomique','fer')→26, donnee('jours_mois','février')→28. Absent -> HORS (jamais inventé)."""
    return _LEC.repond(relation, entite)


def donnee_nl(question: str):
    """Variante langage naturel du lecteur DATA : gabarits des tables ingérées + repli base_faits.repond_nl."""
    return _LEC.repond_nl(question)


def coordonnees_lieu(lieu: str):
    """COORDONNÉES (latitude, longitude) en degrés décimaux d'un LIEU ingéré, ou None si inconnu (HORS, jamais
    deviné). Cherche dans toute paire de relations `latitude_*`/`longitude_*` du lecteur (capitales aujourd'hui,
    extensible villes/sommets…). Fait BORNÉ (la réalité fixe la position). cf. ingere_coordonnees.py."""
    for rel in _LEC.LECTEUR.relations():
        if not rel.startswith("latitude_"):
            continue
        rel_lon = "longitude_" + rel[len("latitude_"):]
        flat = _LEC.LECTEUR.cherche(rel, lieu)
        flon = _LEC.LECTEUR.cherche(rel_lon, lieu)
        if flat is not None and flon is not None:
            try:
                return (float(flat.valeur), float(flon.valeur))
            except (TypeError, ValueError):
                return None
    return None


def distance_lieux(lieu_a: str, lieu_b: str):
    """DISTANCE orthodromique (grand cercle, sphère R=6371 km) entre deux lieux ingérés, en km — fait DÉRIVÉ
    exact du MODÈLE sphérique (portée : orthodromie ; ≈0,1–0,5 % vs géodésique ellipsoïdal, PAS une donnée
    stockée). Renvoie None si l'un des deux lieux est inconnu (HORS, jamais deviné). cf. navigation.py."""
    ca, cb = coordonnees_lieu(lieu_a), coordonnees_lieu(lieu_b)
    if ca is None or cb is None:
        return None
    import navigation
    return navigation.distance_orthodromique(ca[0], ca[1], cb[0], cb[1])


def cap_lieux(lieu_a: str, lieu_b: str):
    """CAP INITIAL (azimut vrai de départ de l'orthodromie, degrés dans [0,360[) de `lieu_a` vers `lieu_b`.
    Fait DÉRIVÉ du modèle sphérique. None si un lieu est inconnu (HORS). cf. navigation.py."""
    ca, cb = coordonnees_lieu(lieu_a), coordonnees_lieu(lieu_b)
    if ca is None or cb is None:
        return None
    import navigation
    return navigation.cap_initial(ca[0], ca[1], cb[0], cb[1])


def dms_vers_dd(degres, minutes, secondes) -> float:
    """CONVERSION coordonnée sexagésimale (degrés-minutes-secondes) -> degrés décimaux, EXACTE par définition.
    Fait le pont vers coordonnees_lieu/distance_lieux. DMS malformé -> ValueError (jamais « corrigé »).
    cf. cartographie.py."""
    import cartographie
    return cartographie.conversion_dms_dd(degres, minutes, secondes)


def echelle_carte(distance_carte_cm, echelle_denominateur, inverse: bool = False) -> float:
    """ÉCHELLE cartographique 1:N (identité EXACTE). Par défaut : distance carte (cm) -> distance réelle (cm)
    (× N). `inverse=True` : distance réelle -> distance carte (÷ N). Dénominateur ≤ 0 -> ValueError. cf. cartographie.py."""
    import cartographie
    if inverse:
        return cartographie.distance_carte(distance_carte_cm, echelle_denominateur)
    return cartographie.echelle_distance_reelle(distance_carte_cm, echelle_denominateur)


def resolution_sol(dpi, echelle_denominateur) -> float:
    """RÉSOLUTION AU SOL (cm) d'un pixel d'une carte 1:N numérisée à `dpi` : (2,54/dpi) × N. dpi/échelle ≤ 0 ->
    ValueError. cf. cartographie.py."""
    import cartographie
    return cartographie.resolution_au_sol_depuis_dpi(dpi, echelle_denominateur).valeur_cm


def densite_pays(nom: str):
    """DENSITÉ de population d'un pays (hab/km²) = population_pays / superficie, deux tables ingérées alignées par
    nom FR. Fait DÉRIVÉ (population = instantané daté, volatile ; densité évolue lentement). None si l'un des deux
    manque (HORS, jamais deviné). cf. demographie.py (densite_population), ingere_worldbank.py."""
    fp = _LEC.LECTEUR.cherche("population_pays", nom)
    fs = _LEC.LECTEUR.cherche("superficie", nom)
    if fp is None or fs is None:
        return None
    import demographie
    try:
        return demographie.densite_population(float(fp.valeur), float(fs.valeur))
    except (TypeError, ValueError):
        return None


def indicateur_pays(relation: str, nom: str):
    """Valeur NUMÉRIQUE d'un indicateur-pays ingéré (Banque mondiale — instantané daté, millésime dans la source)
    ou None (HORS, jamais deviné). cf. ingere_worldbank.py."""
    f = _LEC.LECTEUR.cherche(relation, nom)
    if f is None:
        return None
    try:
        return float(f.valeur)
    except (TypeError, ValueError):
        return None


def pib_pays(nom: str):
    """PIB d'un pays (dollars US courants, Banque mondiale NY.GDP.MKTP.CD, instantané daté) ou None."""
    return indicateur_pays("pib_pays", nom)


def pib_par_habitant_pays(nom: str):
    """PIB par habitant (dollars US courants, NY.GDP.PCAP.CD, instantané daté) ou None."""
    return indicateur_pays("pib_par_habitant_pays", nom)


def taux_chomage_pays(nom: str):
    """Taux de chômage (% de la population active, estimation OIT SL.UEM.TOTL.ZS, instantané daté) ou None."""
    return indicateur_pays("taux_chomage_pays", nom)


def taux_inflation_pays(nom: str):
    """Inflation annuelle des prix à la consommation (%, FP.CPI.TOTL.ZG, instantané daté) ou None."""
    return indicateur_pays("taux_inflation_pays", nom)


def esperance_vie_pays(nom: str):
    """Espérance de vie à la naissance (années, SP.DYN.LE00.IN, instantané daté) ou None."""
    return indicateur_pays("esperance_vie_pays", nom)


def indice_gini_pays(nom: str):
    """Indice de Gini des revenus (0-100, SI.POV.GINI, instantané daté) ou None."""
    return indicateur_pays("indice_gini_pays", nom)


def pib_par_habitant_calcule(nom: str):
    """PIB par habitant DÉRIVÉ = pib_pays / population_pays via le moteur pib.py (fait dérivé à portée explicite,
    PAS stocké ; millésimes des deux instantanés potentiellement différents -> valeur indicative recoupable avec
    `pib_par_habitant_pays`). None si un pivot manque (HORS). cf. pib.py (moteur de formules réveillé)."""
    p = indicateur_pays("pib_pays", nom)
    h = indicateur_pays("population_pays", nom)
    if p is None or h is None:
        return None
    import pib
    try:
        return pib.pib_par_habitant(p, h)
    except (TypeError, ValueError):
        return None


def donnee_nl_floue(question: str):
    """Comme `donnee_nl` mais TOLÉRANT à une faute de frappe sur l'entité (« protugal »->« portugal »).
    Renvoie (statut, fait, correction) : `correction` = la forme corrigée utilisée (str) ou None si exact.
    D'abord le lookup normal (exact + repli amorce) ; seulement si HORS, on tente la résolution floue (sound,
    FAUX=0 : correction UNIQUE et proche, jamais ambiguë). Service additif (cf. resolution.py)."""
    from base_faits import VERIFIE
    statut, fait = _LEC.repond_nl(question)
    if statut == VERIFIE:
        return (statut, fait, None)
    import resolution
    statut, fait, corr = resolution.repond_floue(question)      # gabarits curés + fuzzy entité
    if statut == VERIFIE:
        return (statut, fait, corr)
    return resolution.resout_nl_generique(question)             # générique sur les ~298 relations


def voisins(entite: str):
    """GRAPHE RELATIONNEL TYPÉ : arêtes-ENTITÉS sortantes de `entite` [(relation, valeur, affichage)] — les faits
    dont la valeur est elle-même une entité du corpus (navigable). Service additif (cf. graphe_monde.py), FAUX=0 :
    une arête ⟺ un fait réel (jamais inventée). Voir aussi `chemin` pour la traversée multi-sauts."""
    import graphe_monde
    from base_faits import normalise
    return graphe_monde.voisins(normalise(entite))


def chemin(depart: str, arrivee: str, max_sauts: int = 3):
    """GRAPHE : plus court CHEMIN d'arêtes RÉELLES entre deux entités [(relation, nœud), …], ou None (HORS honnête).
    Déterministe, borné, cycle-sûr ; le chemin rendu est re-vérifiable (chaque arête re-lookupée). cf. graphe_monde.py."""
    import graphe_monde
    return graphe_monde.chemin(depart, arrivee, max_sauts)


def est_un(x: str, type_: str, relation: str = "taxon_parent"):
    """ONTOLOGIE : subsomption transitive — True ssi `type_` est un ancêtre RÉEL de `x` par `relation` hiérarchique
    (défaut `taxon_parent`). MONDE OUVERT : False = « non dérivable des faits présents », jamais « faux ». cf. ontologie.py."""
    import ontologie
    return ontologie.est_un(x, type_, relation)


# ————————————————— INVENTION DIVERGENTE (innover HORS des concepts existants — priorité #1) —————————————————
# Le moteur `ia.invente` recombine l'existant ; ces 6 modes font un geste DIFFÉRENT (apprendre une loi neuve, lever
# une contrainte, transférer une structure, arbitrer un compromis, expliquer, planifier). Additifs, sound (chaque
# brique abstient sans preuve → FAUX=0). Voir invention_divergente.py.
def apprend_loi(donnees, tol: float = 1e-6):
    """Découvre la loi y=f(x) qui colle à TOUS les points (held-out inclus), ou None. Apprendre une loi NEUVE du monde."""
    import invention_divergente
    return invention_divergente.apprend_loi(donnees, tol)


def leve_contrainte(variables: dict, contraintes):
    """TRIZ : plus petit ensemble de contraintes à LEVER pour rouvrir un design sur-contraint. Renvoie
    {contraintes_a_relacher, solution} ou None. `variables`={nom:domaine}, `contraintes`=[(portée, prédicat, nom)]."""
    import invention_divergente
    return invention_divergente.leve_contrainte(variables, contraintes)


def transfere_analogie(source, cible):
    """Analogie inter-domaines : correspondance structurelle (bijection préservant les prédicats) source→cible, ou None."""
    import invention_divergente
    return invention_divergente.transfere_analogie(source, cible)


def arbitre_compromis(candidats, sens):
    """Front de Pareto : les designs non dominés (choix rationnels) parmi `candidats`=[(étiquette, objectifs)], `sens`."""
    import invention_divergente
    return invention_divergente.arbitre_compromis(candidats, sens)


def explique_observations(graphe, observations, taille_max: int = 3):
    """Abduction : plus petit ensemble de causes expliquant toutes les observations (chemins causals réels), ou None."""
    import invention_divergente
    return invention_divergente.explique_observations(graphe, observations, taille_max)


def plan_procede(etat_initial, but, operateurs, max_etats: int = 100000):
    """Planification STRIPS : suite d'actions (procédé/assemblage) de l'état initial au but, re-jouée, ou None."""
    import invention_divergente
    return invention_divergente.plan_procede(etat_initial, but, operateurs, max_etats)


def relation_temporelle(a, b) -> str:
    """Relation d'Allen entre deux intervalles (début, fin) : before/after/meets/overlaps/during/… (1 des 13).
    Bornes = nombres OU dates ISO comparables. ValueError si un intervalle est mal formé. cf. allen.py."""
    import allen
    return allen.relation(a, b)


def vecteur(composantes, dimension=None):
    """Grandeur VECTORIELLE dimensionnée (composantes + unité SI). `dimension` = dimensions.Dimension (défaut : sans).
    Algèbre dimensionnellement sûre (+ même dimension, produit scalaire → dimension produit, norme). cf. grandeur_vectorielle.py."""
    import grandeur_vectorielle
    import dimensions
    return grandeur_vectorielle.GrandeurVectorielle(composantes, dimension if dimension is not None else dimensions.SANS)


# ————————————————— MODALITÉS & POLYGLOTTE (vision universelle : dessin, fichiers, langages) —————————————————
def dessin_svg(formes, largeur, hauteur):
    """DESSIN VECTORIEL : assemble des formes geometrie2d (Polygone/Cercle) en un document SVG déterministe.
    Noyau BORNÉ (géométrie exacte, SVG texte) ; l'esthétique reste non-bornée (non jugée). cf. geometrie2d.py."""
    import geometrie2d
    return geometrie2d.scene_svg(formes, largeur, hauteur)


_ECRIVAIN = None       # generation_coherente.Ecrivain : mint substrat ≈ secondes -> construit au 1er appel SEULEMENT


def conjugue(infinitif: str, personne: int, temps: str = "present") -> str:
    """CONJUGUER un verbe régulier (1er/2e groupe, présent). FAUX=0 : abstention (ValueError) hors périmètre
    garanti — 3e groupe, -ir hors catalogue, particularités orthographiques (-cer/-ger/-yer…), autre temps.
    cf. conjugaison.py (valide 84/84)."""
    import conjugaison
    return conjugaison.conjugue(infinitif, personne, temps)


def ecris(sujet: str, verbe: str, objet: str, adjectif=None, negatif: bool = False,
          pluriel: bool = False, question: bool = False):
    """ÉCRIRE une phrase à triple garantie (grammaticale + sémantique + ré-analysable) depuis la graine lexicale
    certifiée. Renvoie (phrase, coherent, raison) — REFUSE ((None, False, raison)) plutôt que produire faux ;
    vocabulaire borné à la graine = abstention honnête hors graine. cf. generation_coherente.py."""
    global _ECRIVAIN
    if _ECRIVAIN is None:
        import generation_coherente
        _ECRIVAIN = generation_coherente.Ecrivain()
    if question:
        return _ECRIVAIN.demande(sujet, verbe, objet)
    if pluriel:
        return _ECRIVAIN.ecris_pluriel(sujet, verbe, objet)
    if adjectif is not None or negatif:
        return _ECRIVAIN.ecris_riche(sujet, verbe, objet, adjectif=adjectif, negatif=negatif)
    return _ECRIVAIN.ecris(sujet, verbe, objet)


def comprends(question: str, faits=()):
    """COMPRENDRE une question en langue (définition / contraire / « X est-il un Y ? » / en-commun / comptage /
    « qui V Y ? ») et répondre depuis la graine lexicale + `faits` fournis. Hors portée -> « je ne sais pas »
    (jamais inventé). Avec `faits` de type SVO + négations, route vers le lecteur-compreneur. cf. questions.py,
    lecture_comprehension.py."""
    import questions
    return questions.RepondeurIA(faits=faits).repond(question)


def comprends_texte(faits, question: str):
    """LECTURE-COMPRÉHENSION : `faits` = phrases SVO (négations comprises), répond à `question` par déduction
    transitive trivaluée (oui / non / inconnu — jamais deviné). cf. lecture_comprehension.py."""
    import lecture_comprehension
    return lecture_comprehension.Lecteur(faits).repond(question)


def lit_fichier(chemin: str) -> dict:
    """LIRE UN FICHIER : route vers le bon parseur stdlib (json/csv/xml/sqlite/zip/ini/…) et rend {statut, type,
    contenu, meta}. Type inconnu/binaire -> HORS (jamais deviné) ; parse échoué -> ERREUR honnête. cf. parseur_fichiers.py."""
    import parseur_fichiers
    return parseur_fichiers.lit(chemin)


def depot(racine: str):
    """OUVRE UN DÉPÔT éditable (créer/modifier des fichiers dans un repo, souverain, stdlib, offline) confiné à
    `racine`. Renvoie un `editeur.Depot` : .cree/.edite/.remplace/.supprime/.previsualise_edition/.lit/.liste.
    FAUX=0 au niveau SUBSTRAT : l'opération s'applique EXACTEMENT ou lève ValueError (jamais d'écrasement à l'aveugle,
    jamais hors racine, jamais de fichier tronqué). QUOI écrire (justesse du changement) reste une SUPPOSITION à
    faire juger par la réalité (tests/compilation via les exécuteurs, équivalence via refactor). cf. editeur.py."""
    import editeur
    return editeur.Depot(racine)


def edite_fichier(racine: str, chemin_relatif: str, ancien: str, nouveau: str, *, tous: bool = False) -> int:
    """MODIFIE un fichier du dépôt `racine` : remplace le texte EXACT `ancien` par `nouveau`. Ancre absente ou
    ambiguë (>1 occurrence sans `tous`) -> ValueError, fichier INCHANGÉ. Renvoie le nombre de remplacements. cf. editeur.py."""
    import editeur
    return editeur.Depot(racine).edite(chemin_relatif, ancien, nouveau, tous=tous)


def cree_fichier(racine: str, chemin_relatif: str, contenu: str) -> str:
    """CRÉE un nouveau fichier dans le dépôt `racine`. Refuse si le fichier existe déjà (jamais d'écrasement à
    l'aveugle) ou hors racine -> ValueError. Écriture atomique. Renvoie le chemin absolu. cf. editeur.py."""
    import editeur
    return editeur.Depot(racine).cree(chemin_relatif, contenu)


def previsualise_edition(racine: str, chemin_relatif: str, ancien: str, nouveau: str, *, tous: bool = False) -> str:
    """APERÇU (diff unifié) de ce que ferait `edite_fichier`, SANS rien écrire — proposer puis juger avant d'agir.
    cf. editeur.py."""
    import editeur
    return editeur.Depot(racine).previsualise_edition(chemin_relatif, ancien, nouveau, tous=tous)


def modele_3d_obj(maillage) -> str:
    """MODÈLE 3D : sérialise un `geometrie3d.Maillage` (sommets + faces triangulaires) au format Wavefront OBJ (texte
    exact, déterministe). Noyau BORNÉ (géométrie/volume exacts) ; cf. geometrie3d.py (aussi `vers_stl`)."""
    return maillage.vers_obj()


def image_raster(largeur: int, hauteur: int, mode: str = "RGB", fond=None):
    """IMAGE MATRICIELLE (raster) : fabrique une `raster_png.Image` mutable (pose de pixels/rectangles/lignes exacts).
    Complète la modalité image (le VECTORIEL est `dessin_svg`). `raster_png.encode(img)` -> octets PNG valides et
    déterministes, re-décodables (round-trip pixel-parfait prouvé). Noyau BORNÉ ; cf. raster_png.py."""
    import raster_png
    return raster_png.Image(largeur, hauteur, mode, fond)


def encode_png(img, *, niveau: int = 6) -> bytes:
    """Sérialise une `raster_png.Image` en octets PNG (sans perte, déterministes). cf. raster_png.py."""
    import raster_png
    return raster_png.encode(img, niveau=niveau)


def encode_wav(samples, *, framerate: int = 44100, sampwidth: int = 2, canaux: int = 1) -> bytes:
    """SON : sérialise des échantillons PCM entiers en octets WAV valides (RIFF, sans perte, déterministes),
    re-décodables à l'identique (round-trip PCM exact prouvé, oracle stdlib `wave`). Générateurs déterministes :
    `audio_wav.sinus/carre/silence`. Noyau BORNÉ (échantillon entier exact) ; cf. audio_wav.py."""
    import audio_wav
    return audio_wav.encode(samples, framerate=framerate, sampwidth=sampwidth, canaux=canaux)


def classeur():
    """FEUILLE DE CALCUL : fabrique un `tableur_xlsx.Classeur` (feuilles de cellules texte/nombre). `tableur_xlsx.encode`
    -> octets .xlsx (OOXML) valides, déterministes, re-lisibles à l'identique (round-trip typé prouvé). cf. tableur_xlsx.py."""
    import tableur_xlsx
    return tableur_xlsx.Classeur()


def encode_xlsx(classeur_obj) -> bytes:
    """Sérialise un `tableur_xlsx.Classeur` en octets .xlsx. cf. tableur_xlsx.py."""
    import tableur_xlsx
    return tableur_xlsx.encode(classeur_obj)


def trace_barres(valeurs, *, largeur=400, hauteur=300, marge=20):
    """GRAPHIQUE : diagramme en barres. Renvoie une `graphique.Disposition` (coordonnées EXACTES, re-dérivables) —
    `graphique.vers_svg(d)` (texte) ou `graphique.vers_png(d)` (raster). Noyau BORNÉ = projection affine donnée->pixel
    exacte ; l'esthétique reste non jugée. cf. graphique.py (aussi `trace_nuage`/`trace_courbe`)."""
    import graphique
    return graphique.barres(valeurs, largeur=largeur, hauteur=hauteur, marge=marge)


def trace_nuage(xs, ys, *, largeur=400, hauteur=300, marge=20):
    """GRAPHIQUE : nuage de points (x,y) projetés exactement. cf. graphique.py."""
    import graphique
    return graphique.nuage(xs, ys, largeur=largeur, hauteur=hauteur, marge=marge)


def trace_courbe(xs, ys, *, largeur=400, hauteur=300, marge=20):
    """GRAPHIQUE : ligne brisée reliant les points (x,y). cf. graphique.py."""
    import graphique
    return graphique.courbe(xs, ys, largeur=largeur, hauteur=hauteur, marge=marge)


def document():
    """DOCUMENT PDF : fabrique un `document_pdf.Document` (pages A4, texte + vecteur). `document_pdf.encode(doc)` ->
    octets PDF 1.4 valides à `xref` exacte (offsets re-vérifiés au octet près), déterministes. cf. document_pdf.py."""
    import document_pdf
    return document_pdf.Document()


def encode_pdf(doc) -> bytes:
    """Sérialise un `document_pdf.Document` en octets PDF 1.4. cf. document_pdf.py."""
    import document_pdf
    return document_pdf.encode(doc)


# ————————————————— OBJECTIF FINAL : découverte d'inventions sur la base réelle (71 M faits) —————————————————
def attribut_derivable(type_source: str, relation_cible: str, *, budget: int = 300):
    """INVENTION sur le réel : l'attribut `relation_cible` est-il DÉRIVABLE (composé) pour les entités de
    `type_source` sans être stocké directement ? Renvoie un `substrat_reel.Composite` (EXISTE_DEJA / INVENTION /
    BRIQUE_MANQUANTE). FAUX=0 : une INVENTION exige une couverture SYSTÉMATIQUE de chaînes re-vérifiées (rejette les
    coïncidences d'homonymes). Ex. attribut_derivable('pays','population_ville') -> capitale ∘ population_ville.
    cf. substrat_reel.py."""
    import substrat_reel
    return substrat_reel.derive_attribut(type_source, relation_cible, budget=budget)


def inventions_composites(type_source: str, *, budget: int = 200, k: int = 12):
    """INVENTION sur le réel : énumère les attributs COMPOSITES dérivables pour un type d'entités (chacun = une
    relation nouvelle « pont ∘ cible » avec témoin re-vérifié). Le mécanisme d'invention branché sur les 71 M faits,
    FAUX=0 par couverture systématique + re-vérification de chemin. cf. substrat_reel.py (objectif final)."""
    import substrat_reel
    return substrat_reel.composites_utiles(type_source, budget=budget, k=k)


def invente_attribut(type_source: str, relation_cible: str, *, budget: int = 300):
    """INVENTION cadrée par le CONTRAT D'ATOME : renvoie (supposition_dérivable, fait_témoin). La supposition porte
    son statut (SUPPOSITION régime dérivable, confiance = couverture) et n'est JAMAIS servable comme fait ; le témoin
    d'instance re-vérifié est un FAIT (juge = graphe_monde.verifie_chemin). cf. invention_atomes.py, atome.py."""
    import invention_atomes
    return invention_atomes.invente_attribut(type_source, relation_cible, budget=budget)


def invente_dispositif(entree: str, sortie: str):
    """INVENTION GÉNÉRATIVE cadrée : une chaîne de transduction physique nouvelle -> `atome.Atome` SUPPOSITION régime
    génératif (plausibilité structurelle, « efficacité non jugée »), jamais servable comme fait, à confronter à un
    juge réel (coherence_physique) pour être promue. cf. invention_atomes.py."""
    import invention_atomes
    return invention_atomes.invente_dispositif(entree, sortie)


# ————————————————— OBJECTIF / BESOIN (repartir du BUT, pas de la solution humaine) —————————————————
def decompose_besoin(besoin: str) -> dict:
    """DÉCOMPOSE un besoin BORNÉ en objectif réel + canaux/leviers physiques (nomme la grandeur à manipuler, pont
    vers substrat_physique). Besoin inconnu -> {statut:'hors'} : le manque devient VISIBLE. cf. besoin.py."""
    import besoin as _BSN
    return _BSN.decompose(besoin)


def objectif_reel(besoin: str) -> str:
    """REFRAMING machine : ce qu'un besoin veut VRAIMENT (ex. « rafraîchir » -> évacuer les ~100 W du corps, pas
    refroidir l'air), sans s'ancrer sur la solution humaine par défaut. HORS si inconnu. cf. besoin.py."""
    import besoin as _BSN
    return _BSN.objectif_reel(besoin)


def principes_besoin(besoin: str = "rafraichir une piece") -> dict:
    """PRINCIPES candidats pour un besoin, chacun JUGÉ par coherence_physique : impossible -> atome RÉFUTÉ ; possible
    -> SUPPOSITION (jamais promu en FAIT — la cohérence n'est pas une preuve d'efficacité : l'asymétrie). cf. besoin.py."""
    import besoin as _BSN
    return _BSN.principes(besoin)


def strategies_naturelles() -> list:
    """TRANSFERT INTER-DOMAINES : stratégies de rafraîchissement de la NATURE (forêt, jour/nuit, grotte, termitière,
    évaporation) réduites à leurs leviers physiques HONNÊTES — l'espace biomimétique à peigner, sans free lunch. cf. besoin.py."""
    import besoin as _BSN
    return _BSN.strategies_naturelles()


# ————————————————— ASSEMBLEUR INTER-DOMAINES + VEILLE WEB —————————————————
def assemble_invention(besoin: str = "rafraichir une piece", k: int = 5):
    """ASSEMBLEUR : combine les leviers d'un besoin en candidats-stacks (SUPPOSITIONS classées par PLAUSIBILITÉ de
    composition, PAS par efficacité). Garde physique : exclut réfutés, sans-puits, bruyants. Inconnu -> HORS. cf. transfert.py."""
    import transfert as _TRF
    return _TRF.transfere(besoin, k)


def manque_invention(besoin: str = "rafraichir une piece"):
    """« Voir ce qui manque » pour un besoin : canaux non exploités, effets/puits à ajouter au catalogue. cf. transfert.py."""
    import transfert as _TRF
    return _TRF.manque(besoin)


def recherche_web(url: str, *, timeout: int = 15):
    """ACCÈS WEB souverain (urllib) : récupère une URL -> (OK, texte, meta) ou (HORS, None, meta). Dégradation
    gracieuse (toute erreur -> HORS, jamais d'info fabriquée). cf. veille.py."""
    import veille as _VEI
    return _VEI.recupere(url, timeout=timeout)


def approfondit_web(sujet: str, urls=None, *, domaine: str = None):
    """APPROFONDIR un sujet sur le web : récupère des sources de confiance et rend des SUPPOSITIONS RAPPORTÉES
    (jamais des faits ; provenance conservée). Pas de réseau -> HORS. cf. veille.py."""
    import veille as _VEI
    return _VEI.approfondit(sujet, urls, domaine=domaine)


def corrobore_web(enonce: str, temoignages, *, minimum: int = 2, juge=None):
    """Promeut un énoncé web RAPPORTÉ -> FAIT SEULEMENT si >= `minimum` sources INDÉPENDANTES (domaines distincts,
    non recopiés) ET un JUGE réel positif ; sinon reste SUPPOSITION. cf. veille.py."""
    import veille as _VEI
    return _VEI.corrobore(enonce, temoignages, minimum=minimum, juge=juge)


def corrobore_et_persiste(relation, entite, valeur, observations, *, categorie, source,
                          minimum=2, juge=None):
    """BOUCLE WEB->RÉALITÉ->FAIT-STORE : une valeur observée n'entre dans le lecteur (fait persistant, provenance
    tracée) QUE si (a) >= `minimum` sources INDÉPENDANTES la concordent ET (b) un JUGE réel la valide (défaut =
    cohérence avec le fait déjà connu du store) ; l'écriture est CONFLIT-REFUSÉE (2e garde FAUX=0). Sinon rien
    n'est stocké (SUPPOSITION) et un candidat réfuté est mis en garde anti-re-proposition. Renvoie le dict de
    veille_corroboration.corrobore_valeur (statut persiste/suppose/conflit/refute). `observations` = liste de
    veille_corroboration.Observation(domaine, url, valeur). cf. veille_corroboration.py."""
    import veille_corroboration as _VC
    return _VC.corrobore_valeur(relation, entite, valeur, observations, categorie=categorie, source=source,
                                minimum=minimum, juge=juge, lecteur=_LEC.LECTEUR)


def boucle_invention(besoin: str, faits_a_verifier=(), *, minimum: int = 2, juge=None):
    """CAPSTONE : enchaîne besoin -> assemblage -> gap -> corroboration -> writeback pour `besoin`, en abstenant au
    1er maillon manquant. Le CANDIDAT est une SUPPOSITION générative (jamais un fait) ; seuls les `faits_a_verifier`
    (affirmations factuelles + observations de sources structurées) qui SURVIVENT à la corroboration + juge réel sont
    persistés dans le store (non-éphémères, conflit-refusé). Renvoie le dict de boucle_invention.boucle. cf.
    boucle_invention.py / veille_corroboration.py / transfert.py / besoin.py."""
    import boucle_invention as _BI
    return _BI.boucle(besoin, faits_a_verifier, minimum=minimum, juge=juge, lecteur=_LEC.LECTEUR)


# ————————————————— GARDIEN DE BORNAGE (routeur de statut, anti-hallucination) —————————————————
def classe_bornage(question: str, *, juge_verdict: bool = None, juge_nom: str = ""):
    """GARDIEN ANTI-HALLUCINATION : classe une question sur deux axes — ontologique (borné/non-borné/indécidable)
    × accès (juge disponible ou non) → régime du contrat d'atome (fait / supposition-à-chercher / supposition-
    opinion). `Classement.route_fait()` = True SEULEMENT si borné ET juge disponible (sinon jamais affirmer un
    FAIT). Conservateur au doute. cf. classifieur_bornage.py."""
    import classifieur_bornage as _CBORNE
    return _CBORNE.classe(question, juge_verdict=juge_verdict, juge_nom=juge_nom)


def regime_question(question: str, *, juge_verdict: bool = None, juge_nom: str = "") -> str:
    """Raccourci : le RÉGIME d'atome à appliquer à une question (R_FAIT / R_SUPPOSITION_A_CHERCHER /
    R_SUPPOSITION_OPINION) — pour router une réponse vers FAIT vérifiable ou SUPPOSITION calibrée. cf. classifieur_bornage.py."""
    import classifieur_bornage as _CBORNE
    return _CBORNE.regime_atome_pour(question, juge_verdict=juge_verdict, juge_nom=juge_nom)


def assistant(question: str, conv_id: str = None, *, pleine: bool = True):
    """PORTE CONVERSATIONNELLE AUTONOME : comprend la question en langage naturel (pipeline vérifié existant),
    répond/calcule depuis le réel, CHERCHE elle-même sur les sources de confiance (bornage -> veille, opt-in
    IA_WEB=1) et POSE une question de clarification quand la demande est ambiguë — jamais deviner. Renvoie une
    assistant_nl.Reponse (statut fait/supposition/clarification/echange/hors + texte + régime + provenance).
    cf. assistant_nl.py."""
    import assistant_nl as _ASN
    return _ASN.repond(question, conv_id, pleine=pleine)


# ————————————————— RAISONNEMENT STRUCTURÉ (orchestrateurs de 1re classe, cf. audit anti-orphelin) —————————————————
def moteur_raisonnement():
    """Fabrique un MOTEUR DE RAISONNEMENT chaîné (fait→loi→limite→écart→arbitrage→verdict+trace) via blackboard.
    L'appelant observe des faits, dérive par des lois, arbitre les conflits, obtient un verdict tracé. cf. moteur_raisonnement.py."""
    import moteur_raisonnement
    return moteur_raisonnement.MoteurRaisonnement()


def registre_identite():
    """Fabrique un REGISTRE D'IDENTITÉ (canonicalisation d'entités) : distinct par défaut, fusion `sameAs` GATÉE par
    preuve (jamais deux entités distinctes fusionnées sans preuve). cf. identite.py."""
    import identite
    return identite.RegistreIdentite()


def banque_ancres():
    """Fabrique une BANQUE D'ANCRES (vérité-terrain non-circulaire) : rejette l'auto-corroboration (source==source),
    INCONNU faute d'ancre. Socle FAUX=0 de toute vérification. cf. ancres.py."""
    import ancres
    return ancres.BanqueAncres()


def induit_regles(positifs, negatifs):
    """INDUCTION DE RÈGLES DE HORN validée par exemples ± : propose transitivité/symétrie/réflexivité, ne VALIDE
    qu'une règle consistante (0 négatif dérivé, vérifié au POINT FIXE) ; sans négatifs -> non adoptée (abstention).
    cf. induction_horn.py."""
    import induction_horn
    return induction_horn.induit(positifs, negatifs)


def moteur_induit():
    """APPRENDRE→VALIDER→RAISONNER : fabrique un moteur Datalog dont les règles INDUITES (induction_horn) sont
    branchées après validation ; statut() étiquette verifie / incertain (dépend d'une règle induite — jamais fondu
    dans le certain) / refute (négatif déclaré, garde persistante) / hors. cf. regles_induites.py."""
    import regles_induites
    return regles_induites.MoteurInduit()


def minimise_echec(entree, echoue):
    """DELTA-DEBUG (ddmin) : réduit `entree` (séquence) au plus petit sous-ensemble qui satisfait ENCORE `echoue`
    (reproducteur 1-minimal re-vérifiable). Débogage générique d'un contre-exemple. cf. delta_debug.py."""
    import delta_debug
    return delta_debug.ddmin(entree, echoue)


def falsifie(propriete, generateur, n: int = 200, graine: int = 0):
    """PROPERTY-BASED : cherche activement un contre-exemple à `propriete` sur `n` entrées de `generateur(rng)`,
    et le RÉDUIT. Renvoie {refute, contre_exemple, essais}. Jamais « prouvé » — au mieux « non réfuté ». cf. property_based.py."""
    import property_based
    return property_based.pour_tout(propriete, generateur, n=n, graine=graine)


def equivalent(f, g, domaine=None, generateur=None, n: int = 500):
    """ÉQUIVALENCE SÉMANTIQUE : f et g calculent-elles la même fonction ? EQUIVALENTES seulement sur domaine FINI
    exhaustif ; sinon DIFFERENTES (contre-exemple) ou NON_DISTINGUEES (jamais « prouvé »). cf. equivalence_semantique.py."""
    import equivalence_semantique
    return equivalence_semantique.equivalent(f, g, domaine=domaine, generateur=generateur, n=n)


def refactor_sur(original, candidat, domaine=None, generateur=None, n: int = 500):
    """REFACTOR PRÉSERVANT LE COMPORTEMENT : adopte `candidat` SEULEMENT si prouvé équivalent sur `domaine` fini ;
    jamais sur échantillon ; différence -> rejet + contre-exemple. Ne régresse jamais. cf. refactor.py."""
    import refactor
    return refactor.adopte_refactor(original, candidat, domaine=domaine, generateur=generateur, n=n)


def complexite_empirique(tailles, couts):
    """PROFILAGE : classe la croissance d'un coût DÉTERMINISTE (nb d'opérations) — constante/log/linéaire/
    quadratique/cubique/exponentielle, ou 'indetermine' si incohérent (abstention). cf. profilage.py."""
    import profilage
    return profilage.classe_croissance(tailles, couts)


def localise_faute(couverture, verdicts):
    """LOCALISATION DE FAUTE (spectrum-based, Ochiai) : classe les éléments par suspicion à partir d'une couverture
    {test: éléments} + verdicts {test: passe}. Renvoie [(element, score)] décroissant — candidats, pas certitude. cf. localisation_faute.py."""
    import localisation_faute
    return localisation_faute.localise(couverture, verdicts)


def repare_par_recherche(candidats, teste):
    """RÉPARATION : premier patch de `candidats` qui satisfait `teste` (DOIT inclure le held-out, anti-surapprentissage).
    Renvoie {repare, essais, trouve}. cf. localisation_faute.py."""
    import localisation_faute
    return localisation_faute.repare(candidats, teste)


def mutation_score(reference, mutants, teste, domaine):
    """MUTATION TESTING : mesure l'adéquation d'une suite de tests. Mutant équivalent FILTRÉ (via preuve sur `domaine`),
    survivant = mutant prouvé différent non détecté (lacune réelle). Renvoie {score, tues, survivants, equivalents}. cf. mutation_testing.py."""
    import mutation_testing
    return mutation_testing.analyse(reference, mutants, teste, domaine)


def statut_fait(valeur_demandee, valeur_connue, fonctionnelle: bool):
    """FAIT NÉGATIF trivalué : VRAI / FAUX / INCONNU. FAUX conclu SEULEMENT sur relation FONCTIONNELLE (une autre valeur
    est alors certainement fausse) ; absence ou relation multi-valuée -> INCONNU (monde ouvert). cf. fait_negatif.py."""
    import fait_negatif
    return fait_negatif.statut_fait(valeur_demandee, valeur_connue, fonctionnelle)


def orchestre_invention():
    """CAPSTONE : fabrique un ORCHESTRATEUR MULTI-MODE qui ENCHAÎNE les 6 gestes divergents (abduction→plan, loi→TRIZ…)
    sur un blackboard. Abstient au 1er mode qui ne vérifie rien ; ne rapporte que des sorties re-vérifiées. cf. orchestrateur_invention.py."""
    import orchestrateur_invention
    return orchestrateur_invention.OrchestrateurInvention()


def sert_frais(fait_date, maintenant):
    """GATE FRAÎCHEUR : sert la valeur d'un fait DATÉ (fraicheur.FaitDate) SEULEMENT s'il n'est pas périmé à
    `maintenant` ; sinon HORS (jamais une valeur périmée servie comme courante). Prérequis données volatiles. cf. restitution_fraiche.py."""
    import restitution_fraiche
    return restitution_fraiche.sert_ou_hors(fait_date, maintenant)


def choisit_langage(besoin: str):
    """PORTFOLIO POLYGLOTTE : meilleur langage PRÉSENT et jugeable pour un besoin (perf/web/systeme/…) ->
    (langage, Executeur) ou None. L'IA génère dans le langage le mieux placé ; le juge tranche. cf. routeur_langage.py."""
    import routeur_langage
    return routeur_langage.choisit(besoin)


def ingere_donnees(relation: str, lignes, categorie: str, source: str) -> int:
    """INGESTION GÉNÉRIQUE d'une source vérifiable (entité->valeur) dans le lecteur runtime — l'IA APPREND un
    domaine DATA en lisant son référentiel. Conflit (valeur divergente) refusé (intégrité). Renvoie nb d'entrées."""
    return _LEC.LECTEUR.ingere_table(relation, lignes, categorie, source)


def ou_apprendre(domaine: str | None = None):
    """REGISTRE DES SOURCES : « où l'IA irait apprendre ». Sans argument -> toutes les sources fiables
    connues ; avec un domaine ('chimie', 'géographie'…) -> les sources qui le couvrent (URL, type,
    autorité). Sert un futur mode EN LIGNE autonome : parcourir ce registre = ré-ingérer chaque source."""
    return _SRC.toutes() if domaine is None else _SRC.pour_domaine(domaine)


def provenance(relation: str):
    """D'OÙ vient un type de fait : la/les source(s) du registre qui alimentent `relation` (ex. 'capitale')."""
    return _SRC.pour_relation(relation)


def genetique(seq: str, *, quoi: str = "complement"):
    """GÉNÉTIQUE bornée : `quoi` ∈ {complement, complement_inverse, transcrit, traduit, codon}.
    Renvoie (statut, valeur) du moteur `genetique` (VÉRIFIÉ exact ou HORS si base/longueur/codon invalide).
    Mécanisme (appariement + code génétique standard NCBI) garanti ; table = donnée sourcée."""
    if quoi == "complement":
        return _GEN.complement_adn(seq)
    if quoi == "complement_inverse":
        return _GEN.complement_inverse(seq)
    if quoi == "transcrit":
        return _GEN.transcrit(seq)
    if quoi == "traduit":
        return _GEN.traduit(seq)
    if quoi == "codon":
        return _GEN.codon_vers_aa(seq)
    return (_GEN.HORS, None)


def chimie(formule: str, *, quoi: str = "masse_molaire", element: str | None = None):
    """CHIMIE bornée : `quoi` ∈ {masse_molaire, nb_atomes, composition, pourcentage_massique}.
    Renvoie (statut, valeur) du moteur `chimie` (VÉRIFIÉ exact ou HORS si formule/élément inconnu).
    Le mécanisme parse+somme est garanti ; les masses atomiques sont une donnée sourcée (IUPAC)."""
    if quoi == "masse_molaire":
        return _CHIM.masse_molaire(formule)
    if quoi == "nb_atomes":
        return _CHIM.nb_atomes(formule)
    if quoi == "composition":
        return _CHIM.composition(formule)
    if quoi == "pourcentage_massique":
        return _CHIM.pourcentage_massique(formule, element)
    return (_CHIM.HORS, None)


def physique(grandeur: str, params: dict | None = None, **kw):
    """PHYSIQUE bornée (bloc FORMULE) : calcule une grandeur par formule exacte + constantes sourcées (SI/CODATA).
    `grandeur` ∈ physique.grandeurs() (mécanique, thermo, électrostatique, nucléaire, céleste, pH…). Renvoie
    (statut, valeur_arrondie, unité) — VÉRIFIÉ ou HORS (grandeur inconnue / paramètre manquant / domaine invalide,
    jamais un nombre faux). Le MÉCANISME (formule) est garanti ; les constantes sont une donnée sourcée.
    Complément de `coherence_physique` (qui juge l'IMPOSSIBILITÉ) : ici on CALCULE la grandeur."""
    return _PHY.calcule(grandeur, dict(params or {}, **kw))


def incertitude(echantillon, *, quoi: str = "moyenne", confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — estime une grandeur incertaine avec CONFIANCE CALIBRÉE. `quoi` ∈ {moyenne,
    proportion, prediction}. Renvoie (ESTIMATION, (point, (bas, haut)), confiance) — l'intervalle « à X% »
    contient la vraie valeur ~X% du temps (calibration prouvée Monte-Carlo) — ou ABSTENTION si trop peu de
    données. `phrase=True` -> phrase honnête (« je pense que…, mais ce n'est pas sûr »). Jamais de fausse précision."""
    if quoi == "moyenne":
        res = _INC.estime_moyenne(echantillon, confiance)
    elif quoi == "proportion":
        res = _INC.estime_proportion(echantillon, confiance)
    elif quoi == "prediction":          # où tombera la PROCHAINE observation (intervalle de prédiction)
        res = _INC.predit_intervalle(echantillon, confiance)
    else:
        res = (_INC.ABSTENTION, None, f"grandeur inconnue : {quoi}")
    return _INC.formule(res, quoi) if phrase else res


def compare(a, b, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — « les groupes A et B diffèrent-ils ? » avec faux positifs CONTRÔLÉS (calibré).
    Renvoie (DIFFERENT/INDETERMINE, diff, (bas, haut), confiance) ou ABSTENTION. Sur des 0/1 = comparaison de
    proportions (A/B test). `phrase=True` -> phrase honnête. INDETERMINE = pas de différence détectée (jamais
    « identiques » affirmé)."""
    res = _INC.compare_moyennes(a, b, confiance)
    return _INC.formule(res, "comparaison") if phrase else res


def anomalie(valeur, echantillon, *, confiance: float = 0.95, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — « cette valeur est-elle anormale ? » = hors de la plage attendue (intervalle de
    prédiction), avec FAUSSES ALERTES CONTRÔLÉES (calibré). Renvoie (ANORMAL/NORMAL, (bas, haut), confiance) ou
    ABSTENTION. `phrase=True` -> phrase honnête. NORMAL = pas d'anomalie détectée (pas une preuve de normalité)."""
    res = _INC.est_anormal(valeur, echantillon, confiance)
    return _INC.formule(res, "anomalie") if phrase else res


def tendance(serie, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — « la série monte / baisse / est stable ? » via la pente, avec FAUX POSITIFS
    CONTRÔLÉS (calibré, à peu près). Renvoie (HAUSSE/BAISSE/STABLE, pente, (bas, haut), confiance) ou ABSTENTION.
    `phrase=True` -> phrase honnête. STABLE = pas de tendance détectée (jamais « constant » affirmé)."""
    res = _INC.tendance(serie, confiance)
    return _INC.formule(res, "tendance") if phrase else res


def calibration(confiances, justesses, *, n_bins: int = 10, tol: float = 0.05, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — LE JUGE DE CALIBRATION : un lot de confiances annoncées est-il HONNÊTE ? À partir de
    couples (confiance ∈ [0,1], justesse 0/1 = la réponse était-elle juste ?), renvoie (verdict, infos) avec
    verdict ∈ {CALIBRE, SURCONFIANT, SOUSCONFIANT, ABSTENTION} et infos = {n, ece, mce, brier, ecart_signe}.
    SURCONFIANT = ligne rouge (annonce plus de certitude que la réalité = fausse précision). `phrase=True` ->
    phrase honnête. C'est le « mètre-étalon » qui juge l'honnêteté de TOUTE estimation P2 (cf. calibration.py)."""
    res = _CAL.est_calibre(confiances, justesses, n_bins, tol)
    return _CAL.formule(res, "forecast") if phrase else res


def couverture(intervalles, verites, nominal: float, *, tol: float = 0.05, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — juge un estimateur d'INTERVALLE : la couverture empirique tient-elle la promesse
    `nominal` (ex 0.90) ? À partir de couples (intervalle (bas,haut), vérité), renvoie (verdict, infos).
    SURCONFIANT = sous-couvre (intervalle trop étroit = ligne rouge) ; SOUSCONFIANT = sur-couvre (prudent) ;
    ABSTENTION si trop peu de cas. `phrase=True` -> phrase honnête. Sert à AUDITER incertitude.py sur des données réelles."""
    res = _CAL.verdict_couverture(intervalles, verites, nominal, tol)
    return _CAL.formule(res, "couverture") if phrase else res


def combine_indices(prior, indices, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — COMBINAISON BAYÉSIENNE : agrège plusieurs indices bruités en une probabilité
    postérieure CALIBRÉE, à partir d'un PRIOR explicite. `indices` = liste de (p_si_oui, p_si_non, observe).
    Renvoie (ESTIMATION, p_post, infos) ou ABSTENTION (prior/vraisemblance dégénérés = refus de fausse certitude).
    Suppose l'indépendance conditionnelle (sinon sur-confiance). `phrase=True` -> phrase honnête. Cf. bayes.py."""
    res = _BAY.posterior(prior, indices)
    return _BAY.formule(res) if phrase else res


def combine_indices_correle(prior, indices, *, rho: float = 0.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — combinaison bayésienne pour indices CORRÉLÉS (corrige le sur-comptage de
    `ia.combine_indices`). Escompte l'évidence par la taille d'échantillon effective n_eff = k/(1+(k−1)ρ). ρ=0 =
    indépendant ; ρ=1 sur des doublons = compte une fois (plus de sur-confiance). Renvoie (ESTIMATION, p, infos) ou
    ABSTENTION. Estimer ρ via `ia.estime_correlation`. `phrase=True` -> phrase honnête. Cf. bayes.py."""
    res = _BAY.posterior_correle(prior, indices, rho)
    return _BAY.formule(res) if phrase else res


def estime_correlation(signaux_par_cas):
    """PHASE 2 (NON-BORNÉ) — estime la corrélation moyenne ρ ∈ [0,1] entre indices à partir de l'historique de leurs
    signaux binaires (liste de vecteurs 0/1), à passer à `ia.combine_indices_correle`. Cf. bayes.rho_empirique."""
    return _BAY.rho_empirique(signaux_par_cas)


def conforme_intervalle(residus_calibration, prediction, *, alpha: float = 0.1, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PRÉDICTION CONFORME (régression) : intervalle autour de `prediction` garantissant une
    couverture ≥ 1−alpha SANS hypothèse de loi (échangeabilité seule), à partir des résidus de calibration |y−ŷ|.
    Renvoie (ESTIMATION, (bas, haut), 1−alpha) ou ABSTENTION si trop peu de points. `phrase=True` -> phrase honnête.
    Robuste au modèle mal spécifié / bruit non gaussien (cf. conformal.py)."""
    res = _CNF.intervalle_conforme(residus_calibration, prediction, alpha)
    return _CNF.formule(res, "intervalle") if phrase else res


def conforme_ensemble(probas_vraie_calibration, probas_test, *, alpha: float = 0.1, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PRÉDICTION CONFORME (classification) : ensemble de classes contenant la vraie réponse
    ≥ 1−alpha. `probas_vraie_calibration` = probas attribuées à la vraie classe en calibration ; `probas_test` =
    dict {classe: proba}. Renvoie (ENSEMBLE, set, 1−alpha) ou ABSTENTION. L'ensemble peut être vide (incertitude
    forte) ou multiple (refus honnête de trancher). `phrase=True` -> phrase honnête."""
    res = _CNF.ensemble_conforme(probas_vraie_calibration, probas_test, alpha)
    return _CNF.formule(res, "ensemble") if phrase else res


def conforme_adaptatif(*, confiance: float = 0.90, gamma: float = 0.05, taille_fenetre: int = 200):
    """PHASE 2 (NON-BORNÉ) — crée un estimateur d'intervalle conforme EN LIGNE, robuste à la DÉRIVE de distribution
    (« vérité datée » : le monde change). Usage : `aci = ia.conforme_adaptatif()` puis, à chaque pas,
    `aci.intervalle(prediction)` (intervalle courant) et `aci.observe(prediction, verite)` quand la vérité arrive.
    Maintient la couverture visée même quand le bruit/la loi changent (ACI ; cf. conformal_adaptatif.py)."""
    return _CNFA.ConformeAdaptatif(alpha_cible=1.0 - confiance, gamma=gamma, taille_fenetre=taille_fenetre)


def conforme_mondrian(groupes, residus, *, confiance: float = 0.90):
    """PHASE 2 (NON-BORNÉ) — CONFORME GROUP-CONDITIONNEL (Mondrian) : un quantile conforme PAR groupe, pour une
    couverture CONDITIONNELLE (chaque régime couvert ~confiance, pas seulement la moyenne). Renvoie un objet :
    `m.intervalle(groupe, prediction)` -> (ESTIMATION, (bas, haut), confiance) ou ABSTENTION (cf. conformal_normalise.py)."""
    return _CNFN.ConformeMondrian(alpha=1.0 - confiance).ajuste(groupes, residus)


def conforme_normalise(residus_cal, sigmas_cal, prediction, sigma_pred, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — CONFORME NORMALISÉ (hétéroscédastique) : score = |résidu|/σ̂ ; intervalle à largeur
    ADAPTATIVE = prediction ± q·σ_pred (resserre où c'est facile, élargit où c'est dur). Renvoie (ESTIMATION,
    (bas, haut), confiance) ou ABSTENTION. `phrase=True` -> phrase honnête."""
    res = _CNFN.intervalle_normalise(residus_cal, sigmas_cal, prediction, sigma_pred, 1.0 - confiance)
    return _CNFN.formule(res) if phrase else res


def ajuste_calibration(scores, issues):
    """PHASE 2 (NON-BORNÉ) — apprend un CALIBRATEUR (régression isotonique) à partir de couples (score, issue 0/1) :
    une fonction monotone qui RÉPARE la sur-confiance d'un classifieur. Renvoie un objet calibrateur (à passer à
    `ia.predit_calibre`) ou None si trop peu de données. Model-free, non paramétrique (cf. classif_calibree.py)."""
    return _CLF.ajuste_isotonique(scores, issues)


def predit_calibre(calibrateur, score, *, seuil_abstention: float = 0.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — applique un calibrateur à un score : renvoie (DECISION, proba_calibrée) si la confiance
    ≥ seuil_abstention, sinon (ABSTENTION, proba). `calibrateur=None` -> ABSTENTION. `phrase=True` -> phrase honnête."""
    res = _CLF.predit(calibrateur, score, seuil_abstention)
    return _CLF.formule(res) if phrase else res


def ajuste_calibration_multiclasse(scores_par_exemple, labels):
    """PHASE 2 (NON-BORNÉ) — apprend un calibrateur MULTI-CLASSE (isotonique un-contre-tous) à partir d'exemples
    {classe: score_brut} + vraie classe. Renvoie un calibrateur (à passer à `ia.predit_multiclasse`) ou None si
    trop peu de données. Donne une probabilité calibrée PAR classe (cf. classif_multiclasse.py)."""
    return _CLFMC.ajuste_multiclasse(scores_par_exemple, labels)


def predit_multiclasse(calibrateur, scores, *, seuil_abstention: float = 0.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — applique un calibrateur multi-classe à des scores {classe: score} : renvoie
    (DECISION, classe_gagnante, probas_calibrées) si la confiance gagnante ≥ seuil, sinon (ABSTENTION, None, probas).
    `phrase=True` -> phrase honnête."""
    res = _CLFMC.predit(calibrateur, scores, seuil_abstention)
    return _CLFMC.formule(res) if phrase else res


def propage_incertitude(f, entrees, *, confiance: float = 0.90, methode: str = "mc", phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PROPAGATION D'INCERTITUDE : combine des grandeurs mesurées (chacune (moyenne, σ)) dans
    un calcul `f` et propage l'incertitude. `methode='mc'` (Monte-Carlo, exact pour tout f) ou 'lineaire' (1er ordre,
    rapide mais peut être sur-confiant sur du non-linéaire). Renvoie (ESTIMATION, (point, (bas, haut)), confiance) ou
    ABSTENTION (σ invalide). `phrase=True` -> phrase honnête. Le PONT avec le borné mesuré P1 (cf. propagation.py)."""
    if methode == "lineaire":
        res = _PRP.intervalle_lineaire(f, [m for (m, _) in entrees], [s for (_, s) in entrees], confiance)
    else:
        res = _PRP.propage_mc(f, entrees, confiance)
    return _PRP.formule(res, methode) if phrase else res


def decide(probas, utilites, *, marge_abstention: float = 0.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — DÉCISION sous incertitude calibrée : choisit l'action d'UTILITÉ ESPÉRÉE maximale.
    `probas` = dict {classe: proba (calibrée)} ; `utilites` = dict {action: {classe: utilité}}. Renvoie
    (DECISION, action, eu) ou (ABSTENTION, None, eu) si l'écart d'utilité avec la 2ᵉ action < marge_abstention.
    Avec des probas CALIBRÉES, l'utilité espérée annoncée = l'utilité réellement obtenue (cf. decision.py).
    `phrase=True` -> phrase honnête."""
    res = _DEC.decide(probas, utilites, marge_abstention)
    return _DEC.formule(res) if phrase else res


def bandit(k, *, strategie: str = "ucb", seed: int = 0):
    """PHASE 2 (NON-BORNÉ) — DÉCISION SÉQUENTIELLE (bandit) : choisir répétément parmi k options aux récompenses
    inconnues en explorant juste assez. `strategie` ∈ {ucb (optimisme calibré), thompson (postérieur)}. Renvoie un
    objet : `b.choisis()` -> bras, `b.observe(bras, recompense)`. Regret sous-linéaire garanti. Cf. bandit.py."""
    return _BND.Bandit(k, strategie, seed)


def effet_causal(y_traites, y_controles, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — EFFET CAUSAL (ATE) par différence de moyennes, VALIDE pour un essai RANDOMISÉ. Renvoie
    (ESTIMATION, (ate, (bas, haut)), confiance) ou ABSTENTION. ⚠ sous CONFUSION (observationnel), utiliser
    `ia.effet_causal_ipw`. `phrase=True` -> phrase honnête. Cf. causal.py."""
    res = _CAU.ate_diff_moyennes(y_traites, y_controles, confiance)
    return _CAU.formule(res) if phrase else res


def effet_causal_ipw(y, traitement, propension, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — EFFET CAUSAL (ATE) par IPW (observationnel) : corrige la CONFUSION en pondérant par
    1/propension. `propension` = P(traité|X). Renvoie (ESTIMATION, (ate, (bas, haut)), confiance) ou ABSTENTION
    (pas de support commun). Couvre le vrai effet là où la diff naïve est biaisée. Cf. causal.py."""
    res = _CAU.ate_ipw(y, traitement, propension, confiance)
    return _CAU.formule(res) if phrase else res


def combine_opinions(probas_experts, *, poids=None, methode: str = "lineaire", phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — AGRÉGATION D'OPINIONS d'experts {expert: proba} par pool `methode` ∈ {lineaire, log},
    pondéré par fiabilité (`poids` dict ou None=uniforme). Renvoie la proba agrégée. `phrase=True` -> phrase honnête.
    Calculer les poids via `ia.poids_fiabilite`. Cf. opinions.py."""
    p = _OPI.combine(probas_experts, poids, methode)
    return _OPI.formule(p, methode) if phrase else p


def poids_fiabilite(sorties_experts, issues):
    """PHASE 2 (NON-BORNÉ) — poids de fiabilité ∝ 1/log-loss passé de chaque expert (dict {expert: liste_probas} +
    issues 0/1), à passer à `ia.combine_opinions`. Un mauvais expert reçoit un poids ~0. Cf. opinions.py."""
    return _OPI.poids_fiabilite(sorties_experts, issues)


def calibration_predictive(echantillons, verites, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — juge une DISTRIBUTION PRÉDICTIVE par la PIT : `echantillons` = liste (un par cas)
    d'échantillons prédictifs, `verites` = valeur réalisée. Renvoie (verdict, infos) ∈ {CALIBRE, SURCONFIANT
    (trop étroite), SOUSCONFIANT (trop large), ABSTENTION}. `phrase=True` -> phrase honnête. Cf. predictif.py."""
    pits = _PRD.pit_echantillon(echantillons, verites)
    res = _PRD.est_calibre_pit(pits)
    return _PRD.formule(res) if phrase else res


def quantile_pinball(echantillon, tau):
    """PHASE 2 (NON-BORNÉ) — estime le τ-quantile (minimise la perte pinball, règle propre orientée quantile). Cf. predictif.py."""
    return _PRD.quantile_pinball(echantillon, tau)


def teste_calibration(probas, issues, *, alpha: float = 0.05, methode: str = "spiegelhalter", phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — TEST D'HYPOTHÈSE de calibration : renvoie un VERDICT statistique (CALIBRE / NON_CALIBRE /
    ABSTENTION) + p-valeur, avec erreur de type I contrôlée. `methode` ∈ {spiegelhalter, hosmer}. Distinct de l'ECE
    (qui estime sans tester la significativité). `phrase=True` -> phrase honnête. Cf. test_calibration.py."""
    res = _TST.est_calibre_test(probas, issues, alpha, methode)
    return _TST.formule(res) if phrase else res


def estime_population(valeurs, poids, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — estime la moyenne d'une POPULATION depuis un échantillon BIAISÉ (poids ∝ 1/proba
    d'inclusion), via l'estimateur de Hájek + intervalle bootstrap. Corrige le biais que la moyenne brute ignore.
    Renvoie (ESTIMATION, (point, (bas, haut)), confiance) ou ABSTENTION (poids dégénérés). Cf. echantillon_pondere.py."""
    res = _EPO.intervalle_hajek(valeurs, poids, confiance)
    return _EPO.formule(res) if phrase else res


def estime_fermi(facteurs, *, confiance: float = 0.90, conf_facteurs=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — ESTIMATION D'ORDRE DE GRANDEUR (Fermi) : combine des facteurs multiplicatifs incertains
    (liste de (bas, haut) > 0) en une estimation + intervalle calibré (log-normal). `conf_facteurs` = niveau des
    intervalles d'entrée (défaut = `confiance`). Renvoie (ESTIMATION, (point, (bas, haut)), confiance) ou ABSTENTION.
    Pour estimer l'inestimable honnêtement (cf. fermi.py)."""
    res = _FRM.estime_fermi(facteurs, confiance, conf_facteurs)
    return _FRM.formule(res) if phrase else res


def meta_analyse(effets, erreurs_std, *, confiance: float = 0.95, modele: str = "aleatoire", phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — MÉTA-ANALYSE : combine des études (effets θᵢ ± erreurs-types seᵢ) en un effet global +
    hétérogénéité (I², τ²). `modele` ∈ {aleatoire (DerSimonian-Laird, recommandé), fixe}. Renvoie (ESTIMATION, infos)
    ou ABSTENTION. L'aléatoire couvre sous hétérogénéité là où le fixe sur-confie. `phrase=True`. Cf. meta_analyse.py."""
    res = _META.meta_analyse(effets, erreurs_std, confiance, modele)
    return _META.formule(res) if phrase else res


def decompose_incertitude(echantillon, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — sépare l'incertitude en ALÉATOIRE (irréductible, bruit inhérent) et ÉPISTÉMIQUE
    (réductible, manque de données ∝ 1/n). Renvoie (ESTIMATION, {moyenne, aleatoire, epistemique, total_predictif, n})
    ou ABSTENTION. Distingue « je n'ai pas assez vu » de « c'est intrinsèquement imprévisible ». `phrase=True`. Cf. module."""
    res = _DEC2.decompose_echantillon(echantillon)
    return _DEC2.formule(res) if phrase else res


def intervalle_predictif_decompose(echantillon, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — intervalle de PRÉDICTION d'une nouvelle observation (aléatoire + épistémique). Renvoie
    (ESTIMATION, (point, (bas, haut)), confiance) ou ABSTENTION. Cf. incertitude_decomposee.py."""
    res = _DEC2.intervalle_predictif(echantillon, confiance)
    return _DEC2.formule(res) if phrase else res


def prevoit(serie, *, periode=None, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PRÉVISION TEMPORELLE : prévoit la PROCHAINE valeur d'une série (tendance + saisonnalité
    optionnelle `periode`) avec un INTERVALLE DE PRÉDICTION calibré (résidus hold-out conformes). Renvoie
    (ESTIMATION, (point, (bas, haut)), confiance) ou ABSTENTION. Prédire le futur sans fausse précision. Cf. prevision.py."""
    res = _PVS.prevoit(serie, periode, confiance)
    return _PVS.formule(res) if phrase else res


def estime_taux(k, exposition=1.0, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — estime un TAUX d'événements (Poisson) depuis k comptages sur une exposition (durée,
    surface, lot) + IC exact de Garwood. Renvoie (ESTIMATION, (lambda, (bas, haut)), confiance) ou ABSTENTION.
    `phrase=True` -> phrase honnête. Cf. poisson.py."""
    res = _POI.estime_taux(k, exposition, confiance)
    return _POI.formule(res) if phrase else res


def proba_au_moins(lam, exposition, k):
    """PHASE 2 (NON-BORNÉ) — P(au moins k occurrences) pour un Poisson de moyenne λ·exposition. Cf. poisson.py."""
    return _POI.proba_au_moins(lam, exposition, k)


def detecte_changement(serie, *, alpha: float = 0.05, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — « le processus a-t-il CHANGÉ, et quand ? » : teste un changement de moyenne (CUSUM
    studentisé, p-valeur de Kolmogorov). Renvoie (CHANGEMENT, position, p) / (STABLE, None, p) / ABSTENTION ; faux
    positifs contrôlés à `alpha`. `phrase=True` -> phrase honnête. Cf. changepoint.py."""
    res = _CHG.detecte_changement(serie, alpha)
    return _CHG.formule(res) if phrase else res


def risque_extreme(donnees, p, *, confiance: float = 0.90, seuil_quantile: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — RISQUE DE QUEUE (VaR) par valeurs extrêmes (POT-GPD) : estime un quantile EXTRÊME (ex.
    p=0.99, 0.999) au-delà des données + IC bootstrap. Renvoie (ESTIMATION, (var, (bas, haut)), confiance) ou
    ABSTENTION. Extrapole honnêtement la queue là où l'empirique est plafonné. Cf. valeurs_extremes.py."""
    res = _EXT.var_pot_ic(donnees, p, confiance, seuil_quantile)
    return _EXT.formule(res, p) if phrase else res


def survie_estimee(temps, evenement, t, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — SURVIE sous CENSURE (Kaplan-Meier) : probabilité que la durée DÉPASSE t + IC de
    Greenwood/log-log. `evenement` : 1 = événement observé, 0 = censuré à droite. Renvoie (ESTIMATION, (S, (bas,
    haut)), confiance) ou ABSTENTION. Exploite les censurés là où les jeter (ou les compter comme événements)
    mentirait. Cf. survie.py."""
    res = _SRV.km_avec_ic(temps, evenement, t, confiance)
    return _SRV.formule(res, t) if phrase else res


def survie_mediane(temps, evenement):
    """PHASE 2 (NON-BORNÉ) — durée MÉDIANE de survie (plus petit t où S(t) <= 0.5), censure prise en compte.
    Renvoie un instant ou None si la courbe KM ne descend pas à 0.5. Cf. survie.py."""
    return _SRV.mediane(_SRV.kaplan_meier(temps, evenement))


def d_calibration_survie(temps, evenement, modele_survie, *, n_bins: int = 10):
    """PHASE 2 (NON-BORNÉ) — D-CALIBRATION : un modèle de survie `modele_survie(t)->S(t)` est-il bien calibré ?
    Renvoie (occupations_deciles, chi2) ; chi2 faible (df=n_bins−1) = déciles uniformes = D-calibré, les censurés
    étant traités honnêtement (masse étalée). Cf. survie.py."""
    return _SRV.d_calibration(temps, evenement, modele_survie, n_bins)


def moyenne_avec_manquants(x, y_obs, *, m: int = 20, confiance: float = 0.95, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — MOYENNE sous DONNÉES MANQUANTES par IMPUTATION MULTIPLE (Rubin). `y_obs` : liste où
    None = manquant ; `x` : covariable observée expliquant le manque (MAR). Renvoie (ESTIMATION, (moyenne, (bas,
    haut)), confiance) ou ABSTENTION. L'IC INCLUT l'incertitude d'imputation, là où le cas-complet biaise et
    l'imputation simple sur-confiance. ABSTENTION si aucun manquant (sans objet) ou trop peu d'observés. Cf.
    donnees_manquantes.py."""
    res = _MIS.imputation_multiple(x, y_obs, m, confiance)
    return _MIS.formule(res) if phrase else res


def imputation_simple_biais(x, y_obs, *, confiance: float = 0.95):
    """PHASE 2 (NON-BORNÉ) — référence NAÏVE (imputation simple, IC trop étroit) pour comparer/démontrer la
    sur-confiance que l'imputation multiple corrige. Renvoie (moyenne, ic) ou None. Cf. donnees_manquantes.py."""
    return _MIS.imputation_simple(x, y_obs, confiance)


def pente_robuste(xs, ys, *, confiance: float = 0.95, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PENTE de régression ROBUSTE (M-estimateur de Huber) + IC bootstrap, résistante aux
    OUTLIERS. Renvoie (ESTIMATION, (pente, (bas, haut)), confiance) ou ABSTENTION. L'IC reste calibré sous
    contamination, là où l'IC des moindres carrés ordinaires sous-couvre (sur-confiance). Cf. regression_robuste.py."""
    res = _ROB.huber_slope_ic(xs, ys, confiance)
    return _ROB.formule(res) if phrase else res


def pente_ols_naive(xs, ys, *, confiance: float = 0.95):
    """PHASE 2 (NON-BORNÉ) — pente OLS + IC classique (référence NAÏVE, tordue/sur-confiante sous outliers) pour
    comparer à la version robuste. Renvoie (ESTIMATION, (pente, ic), confiance) ou ABSTENTION. Cf. regression_robuste.py."""
    return _ROB.ols_slope_ic(xs, ys, confiance)


def region_prediction(train, calib, *, alpha: float = 0.10, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — RÉGION DE PRÉDICTION MULTIVARIÉE conforme (ellipsoïde de Mahalanobis), couverture JOINTE
    garantie ≥ 1−alpha (distribution-free). `train` estime le centre/forme, `calib` (indépendant) fixe le seuil.
    Renvoie (ESTIMATION, {mu, Sinv, seuil}, 1−alpha) ou ABSTENTION ; teste l'appartenance avec `ia.dans_region`. Une
    simple boîte par coordonnée sous-couvrirait. Cf. region_multivariee.py."""
    res = _RMV.region_conforme(train, calib, alpha)
    return _RMV.formule(res) if phrase else res


def dans_region(region, y) -> bool:
    """PHASE 2 (NON-BORNÉ) — `y` (vecteur) est-il dans la région de prédiction conforme renvoyée par
    `ia.region_prediction` (champ [1] du tuple ESTIMATION) ? Cf. region_multivariee.py."""
    return _RMV.dans_region(region, y)


def quantile_conditionnel(xs, ys, tau):
    """PHASE 2 (NON-BORNÉ) — ajuste le τ-QUANTILE conditionnel q_τ(x)=a+b·x par perte PINBALL (sans hypothèse de loi).
    Renvoie (a, b) ou None ; prédire avec `a + b*x`. Le 0.5 = médiane robuste ; couples (0.05,0.95) = bande. Cf.
    quantile_regression.py."""
    return _QR.quantile_fit(xs, ys, tau)


def bande_prediction(xs, ys, *, tau_lo: float = 0.05, tau_hi: float = 0.95, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — BANDE de prédiction par régression quantile : sa largeur SUIT la dispersion locale
    (hétéroscédasticité), couverture conditionnelle tenue là où un intervalle homoscédastique sous-couvre. Renvoie
    (ESTIMATION, (coef_lo, coef_hi), τhi−τlo) ou ABSTENTION ; q_lo(x)=coef_lo[0]+coef_lo[1]·x. Cf. quantile_regression.py."""
    res = _QR.bande_quantile(xs, ys, tau_lo, tau_hi)
    return _QR.formule(res) if phrase else res


def comptage_fenetre(temps, T, a, b, *, n_bins: int = 24, confiance: float = 0.90, homogene: bool = False, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — prédit le COMPTAGE d'événements dans une fenêtre future [a,b] d'un processus de Poisson
    NON-HOMOGÈNE (intensité variable). `temps` = instants observés sur [0,T]. Intervalle prédictif Gamma-Poisson au
    taux LOCAL (défaut) ; `homogene=True` = taux global (naïf, sous-couvre les fenêtres chargées). Renvoie
    (ESTIMATION, (moyenne, (bas, haut)), confiance) ou ABSTENTION. Cf. poisson_nonhomogene.py."""
    res = _NHPP.predit_fenetre(temps, T, n_bins, a, b, confiance, homogene)
    return _NHPP.formule(res) if phrase else res


def intensite_temporelle(temps, T, *, n_bins: int = 24):
    """PHASE 2 (NON-BORNÉ) — profil d'INTENSITÉ λ̂(t) par bacs d'un processus de Poisson sur [0,T]. Renvoie
    (liste_lambda_par_bac, largeur_bac) ou None. Cf. poisson_nonhomogene.py."""
    return _NHPP.intensite_bins(temps, T, n_bins)


def gp_ajuste(xs, ys, *, ell: float = 1.0, sigma_f: float = 1.0, sigma_n: float = 0.3):
    """PHASE 2 (NON-BORNÉ) — ajuste une RÉGRESSION par PROCESSUS GAUSSIEN (noyau exponentiel-quadratique). Renvoie
    (ESTIMATION, model, None) ou ABSTENTION ; prédire ensuite avec `ia.gp_predit(model, x*)`. L'incertitude prédictive
    GRANDIT loin des données (épistémique). Cf. processus_gaussien.py."""
    return _GP.ajuste(xs, ys, ell=ell, sigma_f=sigma_f, sigma_n=sigma_n)


def gp_predit(model, xstar, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — prédiction GP en x* : renvoie (moyenne, (bas, haut)) à `confiance`, intervalle plus large
    là où il n'y a pas de données. `model` vient de `ia.gp_ajuste`[1]. Cf. processus_gaussien.py."""
    if phrase:
        return _GP.formule(model, xstar, confiance)
    return _GP.gp_intervalle(model, xstar, confiance)


def prevoit_horizon(serie, h, *, confiance: float = 0.90, naif: bool = False, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — prévision AUTO-RÉGRESSIVE (AR(1)) à `h` pas avec intervalle dont la largeur CROÎT avec
    l'horizon (les erreurs s'accumulent). Renvoie (ESTIMATION, (moyenne, (bas, haut)), confiance) ou ABSTENTION.
    `naif=True` = largeur fixe d'un seul pas (sous-couvre aux horizons lointains). Distinct de `ia.prevoit`
    (1 pas, tendance/saison). Cf. serie_autoregressive.py."""
    res = _AR.prevoit(serie, h, confiance, naif)
    return _AR.formule(res, h) if phrase else res


def calibreur_etapes(confiances_etape, justesses_etape):
    """PHASE 2 (NON-BORNÉ) — apprend un recalibrateur ISOTONIQUE par étape (couples confiance_étape, étape_juste∈{0,1})
    pour une génération multi-étapes (type LLM). Renvoie un calibrateur (à passer à `ia.confiance_reponse`) ou None.
    Cf. calibration_sequence.py."""
    return _SEQ.ajuste_par_etape(confiances_etape, justesses_etape)


def confiance_reponse(calibreur, confiances_etape, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — confiance que la RÉPONSE ENTIÈRE (séquence) soit correcte = produit des confiances par
    étape RECALIBRÉES. Renvoie (ESTIMATION, proba) ou (ABSTENTION, None). Le produit des confiances BRUTES sur-estime
    (la sur-confiance par étape se compose). Cf. calibration_sequence.py."""
    res = _SEQ.confiance_sequence_calibree(calibreur, confiances_etape)
    return _SEQ.formule(res) if phrase else res


def comptage_surdisperse(comptes, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — intervalle prédictif d'un NOUVEAU comptage tenant compte de la SUR-DISPERSION (binomiale
    négative si Var>Moyenne, Poisson sinon). Renvoie (ESTIMATION, (moyenne, (bas, haut)), confiance) ou ABSTENTION.
    Supposer un Poisson sur des comptages sur-dispersés sous-couvre. Cf. surdispersion.py."""
    res = _OD.intervalle_negbin(comptes, confiance)
    return _OD.formule(res) if phrase else res


def teste_surdispersion(comptes):
    """PHASE 2 (NON-BORNÉ) — y a-t-il SUR-DISPERSION dans des comptages ? Renvoie (φ̂=Var/Moyenne, z, surdisperse_bool)
    ou None. φ>1 / z>2 = la variance dépasse ce qu'un Poisson prédit. Cf. surdispersion.py."""
    return _OD.test_surdispersion(comptes)


def pente_erreur_mesure(xs_obs, ys, variance_erreur, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — pente de régression CORRIGÉE du biais d'ATTÉNUATION quand x est mesuré avec erreur
    (variance d'erreur connue). Renvoie (ESTIMATION, (pente, (bas, haut)), confiance) ou ABSTENTION. Les moindres
    carrés bruts atténuent la pente vers zéro et se trompent avec assurance. Cf. erreurs_variables.py."""
    res = _EIV.pente_corrigee_ic(xs_obs, ys, variance_erreur, confiance)
    return _EIV.formule(res) if phrase else res


def combine_evidences(m1, m2, *, regle: str = "yager", focal=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — combine deux ÉVIDENCES imprécises (fonctions de masse Dempster-Shafer). Renvoie
    (COMBINAISON, masse, infos{conflit}) ou ABSTENTION. Défaut = règle de YAGER (robuste) ; `regle='dempster'`
    NORMALISE par 1−K et FABRIQUE de la fausse certitude sous fort conflit (paradoxe de Zadeh). Cf.
    croyance_dempster_shafer.py."""
    res = _DST.combine(m1, m2, regle=regle)
    return _DST.formule(res, focal=focal) if phrase else res


def intervalle_croyance(masse, hypothese):
    """PHASE 2 (NON-BORNÉ) — intervalle épistémique [croyance, plausibilité] d'une hypothèse sous une fonction de
    masse (Dempster-Shafer). La largeur Pl−Bel = l'ignorance ASSUMÉE (une proba ponctuelle l'écraserait = fausse
    précision). Cf. croyance_dempster_shafer.py."""
    return _DST.intervalle_croyance(masse, hypothese)


def encadre_probabilite(pi, evenement, *, nom: str = "l'événement", phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — encadre une probabilité INCONNUE par la THÉORIE DES POSSIBILITÉS (π → [nécessité,
    possibilité]). Théorème de Dubois-Prade : N(A) ≤ P(A) ≤ Π(A) pour toute loi compatible avec π. Renvoie
    (MESURE, (N, Π), True) ou ABSTENTION (π non normalisée). Lire Π(A) comme une probabilité serait SUR-confiant,
    N(A) sous-confiant — la réponse honnête est l'intervalle. Cf. possibilite.py."""
    res = _POS.encadre(pi, evenement)
    return _POS.formule(res, nom) if phrase else res


def propage_intervalle(f, *intervalles, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — propage une incertitude bornée (x ∈ [a,b]) à travers un calcul f par ARITHMÉTIQUE
    D'INTERVALLES (arrondi extérieur rigoureux). Renvoie (INTERVALLE, [bas,haut]) = encadrement GARANTI de la vraie
    valeur (théorème de Moore), ou ABSTENTION (÷ par un intervalle contenant 0). Annoncer le seul point milieu serait
    SUR-confiant. `intervalles` = `Intervalle(a,b)` ou scalaires. Cf. arithmetique_intervalles.py."""
    res = _ARI.evalue(f, *intervalles)
    return _ARI.formule(res) if phrase else res


Intervalle = _ARI.Intervalle  # façade : construire les bornes pour propage_intervalle (ia.Intervalle(a, b))


def decision_robuste(decisions, u_nominal, exigence, *, s: float = 1.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — choisit la décision la plus ROBUSTE à une incertitude SÉVÈRE (info-gap, Ben-Haim) :
    pas de probas, juste une estimation nominale ũ faillible. `decisions` = dict nom→récompense(u). Renvoie
    (ROBUSTE, nom*, table{nom:(α̂, perf_nominale)}) ou ABSTENTION. α̂ = horizon d'erreur de modèle toléré en gardant
    récompense ≥ exigence. Choisir la meilleure perf NOMINALE serait SUR-confiant. Cf. info_gap.py."""
    res = _IGP.choisis(decisions, u_nominal, exigence, s=s)
    return _IGP.formule(res, exigence) if phrase else res


def robustesse_infogap(recompense, u_nominal, exigence, *, s: float = 1.0):
    """PHASE 2 (NON-BORNÉ) — robustesse info-gap α̂ d'UNE décision : plus grand horizon d'erreur de modèle auquel
    `recompense(u)` reste ≥ `exigence` pour tout u dans U(α̂). Garantie exacte. Cf. info_gap.py."""
    return _IGP.robustesse(recompense, u_nominal, exigence, s=s)


def proba_categorielle_imprecise(comptes, *, indice=None, s: float = 1.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — estime des probabilités catégorielles par DIRICHLET IMPRÉCIS (IDM, Walley) : un
    INTERVALLE [n/(N+s), (n+s)/(N+s)] par catégorie au lieu d'un point. Honnête sur l'inobservé (jamais P=0, ≠ MLE
    sur-confiant) et INVARIANT à la représentation (≠ Laplace). Renvoie (BORNES, intervalles) / (BORNES, (bas,haut))
    si `indice`, ou ABSTENTION. Cf. dirichlet_imprecis.py."""
    res = _IDM.estime(comptes, indice=indice, s=s)
    return _IDM.formule(res) if phrase else res


def esperance_imprecise(masse, scores, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — encadre une ESPÉRANCE par intégrale de CHOQUET inférieure/supérieure d'une fonction de
    croyance (masse Dempster-Shafer). Renvoie (VALEUR, (inf, sup)) ou ABSTENTION. [inf,sup] contient E_P[scores] pour
    TOUTE proba du crédal (théorème de Schmeidler) ; s'engager sur un prior unique serait SUR-confiant. `scores` =
    dict label→score. Cf. choquet.py."""
    res = _CHQ.encadre_esperance(masse, scores)
    return _CHQ.formule(res) if phrase else res


def agrege_choquet(capacite, scores):
    """PHASE 2 (NON-BORNÉ) — agrégation multi-critères par intégrale de CHOQUET w.r.t. une capacité non-additive
    (callable frozenset→[0,1]) : capture l'INTERACTION entre critères (synergie/redondance) qu'une moyenne pondérée
    ignore. `scores` = dict critère→score. Cf. choquet.py (`capacite_additive`/`capacite_croyance` pour en bâtir)."""
    return _CHQ.choquet(capacite, scores)


def posterieur_robuste(prior0, vraisemblance, fonction, *, eps: float = 0.1, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — BAYES ROBUSTE (ε-contamination de Berger) : au lieu de s'engager sur le prior π₀, encadre
    la moyenne a posteriori de `fonction(θ)` (ou une proba d'événement via `robust_bayes.indicatrice`) sur toute la
    classe Γ={(1−ε)π₀+εq}. Renvoie (INTERVALLE, (inf,sup), nominal) ou ABSTENTION. Le posterior à prior unique serait
    SUR-confiant ; l'intervalle rétrécit quand les données sont informatives. `prior0`/`vraisemblance`/`fonction` =
    dicts θ→valeur. Cf. robust_bayes.py."""
    res = _RBY.estime(prior0, vraisemblance, fonction, eps=eps)
    return _RBY.formule(res) if phrase else res


def pbox_depuis_intervalles(intervalles, *, seuil=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — construit une P-BOX (paire de CDF [F̲,F̄]) encadrant une loi inconnue depuis des données
    connues par INTERVALLE [(a,b),…]. Encadre garanti : P(X≤seuil) ∈ [F̲,F̄], E[X] et quantiles bornés. Renvoie
    (PBOX, objet PBox) ou ABSTENTION. Réduire à une CDF précise (milieu) serait SUR-confiant. Cf. p_box.py
    (`.proba_seuil(x)`, `.esperance()`, `.quantile(p)`)."""
    res = _PBX.depuis_intervalles(intervalles)
    return _PBX.formule(res, x=seuil) if phrase else res


def prevision_imprecise(credal, gamble, *, nom="ce gamble", phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — prévisions INFÉRIEURE/SUPÉRIEURE de Walley (cadre le plus général de la proba imprécise) :
    encadre l'espérance d'un `gamble` (dict état→gain) par l'enveloppe d'un `credal` (liste de probas = sommets).
    Renvoie (PREVISION, (P̲, P̄)) ou ABSTENTION (crédal vide = perte sûre). S'engager sur un prix précis unique serait
    SUR-confiant ; un prix > max(gamble) garantit un pari hollandais. Cf. prevision_walley.py (`credal_depuis_croyance`
    pour bâtir le crédal d'une croyance Dempster-Shafer)."""
    res = _WAL.encadre_gamble(credal, gamble)
    return _WAL.formule(res, nom) if phrase else res


def decision_pignistique(masse, etats, utilites, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — décision sous croyances à MONDE OUVERT (Transferable Belief Model, Smets). La masse
    autorise m(∅)>0 (« la vérité est peut-être hors cadre » = avertissement de conflit). Pour décider, transforme en
    probabilité pignistique BetP et maximise l'utilité espérée. Renvoie (PIGNISTIQUE, action*, BetP) ou ABSTENTION
    (m(∅)=1). BetP n'est qu'un point de pari : au niveau crédal, garder [Bel,Pl]. Cf. tbm.py (`conjonctive` pour
    combiner sans normaliser, `masse_vide` pour lire le conflit)."""
    res = _TBM.decide(masse, etats, utilites)
    return _TBM.formule(masse, etats) if phrase else res


def decision_sous_ambiguite(credal, actions, *, critere: str = "maxmin", alpha: float = 1.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — décide entre des `actions` (dict action→{état→utilité}) quand l'incertitude est un
    CRÉDAL (liste de probas = sommets), pas une seule proba. `critere` ∈ {maxmin (Gilboa-Schmeidler, pire-cas),
    maxmax, hurwicz (α-mélange), regret_minimax (Savage)}. Renvoie (ROBUSTE, action*, table) ou ABSTENTION.
    Optimiser l'utilité espérée sous UNE proba ignorerait l'ambiguïté (acte fragile, pire-cas inférieur = SUR-confiant)
    ; le maxmin garantit un plancher. Cf. decision_ambiguite.py (`maximaux`/`e_admissibles` pour les actes non dominés)."""
    res = _AMB.choisir(credal, actions, critere=critere, alpha=alpha)
    return _AMB.formule(res, critere) if phrase else res


def decision_ambiguite_lisse(priors, mu, actions, *, aversion: float = 1.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — décision sous AMBIGUÏTÉ LISSE (Klibanoff-Marinacci-Mukerji) : sépare risque et ambiguïté
    via un prior de 2ᵉ ordre `mu` (croyance sur quel `priors[j]` est correct) et une aversion CARA `aversion`=λ
    (λ→0 = utilité espérée classique/ambiguïté-neutre ; λ→∞ = maxmin). `actions` = dict action→{état→utilité}. Renvoie
    (ROBUSTE, action*, table d'équivalents certains) ou ABSTENTION. Réduire μ à un seul prior (EU) ignore l'ambiguïté
    = SUR-confiant. Cf. smooth_ambiguity.py."""
    res = _SAM.choisir(priors, mu, actions, lam=aversion)
    return _SAM.formule(res) if phrase else res


def decision_robuste_modele(reference, actions, *, robustesse: float = 1.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — décision ROBUSTE à la mauvaise spécification d'un modèle de référence (préférences
    multiplier de Hansen-Sargent). `reference` = P₀ (dict état→proba), `actions` = dict action→{état→utilité},
    `robustesse`=θ>0 (θ→∞ = utilité espérée sous P₀ ; θ→0 = pire-cas). Valeur robuste V_θ=−θ·ln E_{P₀}[e^{−u/θ}] :
    une nature adverse distord P₀ en payant une pénalité d'entropie. Faire pleinement confiance à P₀ (EU) serait
    SUR-confiant. Renvoie (ROBUSTE, action*, table) ou ABSTENTION. Cf. variational_preferences.py."""
    res = _VAR.choisir(reference, actions, robustesse)
    return _VAR.formule(res, robustesse) if phrase else res


def borne_risque_generalisation(posterior, prior, risques_empiriques, n, *, delta: float = 0.05, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — MAJORANT PAC-BAYES du risque VRAI (généralisation) d'un prédicteur randomisé (distribution
    `posterior` Q sur les hypothèses), valide avec confiance 1−δ. `prior` P indépendant des données, `risques_empiriques`
    = dict hypothèse→risque sur l'échantillon, `n` = taille. Renvoie (BORNE, majorant) ou ABSTENTION. Annoncer le seul
    risque EMPIRIQUE serait SUR-confiant (il sous-estime l'erreur en population, surtout après sélection). Cf.
    pac_bayes.py (`gibbs` pour un posterior, `borne_mcallester` pour la variante racine)."""
    res = _PAC.borne(posterior, prior, risques_empiriques, n, delta)
    return _PAC.formule(res, _PAC.risque(posterior, risques_empiriques)) if phrase else res


def filtre_etat_robuste(mesures, a, q, r, *, x0: float = 0.0, P0: float = 1.0, inflation: float = 1.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — filtre de KALMAN scalaire + diagnostic de SUR-CONFIANCE. Estime un état caché (x_{t+1}=a·x+bruit
    q, mesure y=x+bruit r). Un filtre dont les covariances (q,r) sont SOUS-estimées rapporte une variance trop petite =
    SUR-confiant ; le NIS (νₜ²/Sₜ, moyenne ≈1 si calibré) le DÉTECTE sans vérité-terrain. `inflation` λ≥1 gonfle la
    covariance (mémoire qui s'efface) pour restaurer la calibration. Renvoie (verdict∈{coherent,surconfiant,sousconfiant},
    {est, var, nis}) ou ABSTENTION. Cf. kalman_robuste.py."""
    res = _KALR.analyse(mesures, a, q, r, x0, P0, inflation)
    return _KALR.formule(res) if phrase else res


def bande_confiance_cdf(echantillon, *, alpha: float = 0.05, seuil=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — BANDE DE CONFIANCE DKW sur la loi (CDF) inconnue d'où provient `echantillon` : une bande
    [F_n−ε, F_n+ε] SIMULTANÉE (tout x à la fois) et DISTRIBUTION-FREE, valide à 1−α (ε=√(ln(2/α)/(2n))). Prendre la CDF
    empirique pour la vérité, ou lire des IC ponctuels comme une bande (multiplicité), serait SUR-confiant. Renvoie
    (BANDE, objet) ou ABSTENTION ; `.proba_seuil(x)`, `.intervalle_quantile(p)`. Cf. dkw.py."""
    res = _DKW.bande(echantillon, alpha)
    return _DKW.formule(res, x=seuil) if phrase else res


def borne_generalisation_uniforme(loss_vectors, risques_empiriques, n, *, delta: float = 0.05, n_sigma: int = 400,
                                  graine: int = 0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — borne de généralisation UNIFORME via la COMPLEXITÉ DE RADEMACHER (Bartlett-Mendelson) :
    R_vrai(h) ≤ R_emp(h) + 2·R̂_n(H) + 3√(ln(2/δ)/2n) pour TOUT h. `loss_vectors` = pertes ∈[0,1] de chaque hypothèse
    sur l'échantillon (longueur n), `risques_empiriques` aligné. R̂_n mesure la capacité de SUR-APPRENTISSAGE (corrélation
    au bruit) ; annoncer le seul risque empirique est SUR-confiant. Renvoie (BORNE, {rad, bornes}) ou ABSTENTION.
    Cf. rademacher.py."""
    import random as _r
    res = _RAD.borne(loss_vectors, risques_empiriques, n, _r.Random(graine), delta, n_sigma)
    return _RAD.formule(res) if phrase else res


def detecte_changement(observations, densite_avant, densite_apres, taux_changement, *, alpha: float = 0.05, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — DÉTECTION AU PLUS TÔT d'un changement de régime (Shiryaev, quickest detection bayésienne).
    `densite_avant`/`densite_apres` = f0/f1 (callables x→densité ; `shiryaev.gaussienne(mu,σ)` pour en bâtir),
    `taux_changement`=ρ (prior géométrique). Alarme dès que la proba a posteriori de changement ≥ 1−α → **taux de
    fausse alarme garanti ≤ α** (≠ d'un détecteur naïf sur seuil, sur-confiant). Renvoie (DETECTION, {alarme, A,
    posteriors}) ou ABSTENTION. Cf. shiryaev.py (distinct du changepoint rétrospectif `changepoint.py`)."""
    res = _SHI.analyse(observations, densite_avant, densite_apres, taux_changement, alpha)
    return _SHI.formule(res) if phrase else res


def intervalle_moyenne_garanti(echantillon, borne_inf, borne_sup, *, delta: float = 0.05,
                               methode: str = "empirical_bernstein", phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — intervalle de confiance pour la MOYENNE de variables bornées [borne_inf, borne_sup],
    GARANTI à n fini et DISTRIBUTION-FREE (inégalités de concentration). `methode` ∈ {empirical_bernstein (défaut,
    adapté à la variance), hoeffding, gaussien}. L'intervalle GAUSSIEN (TCL) est SUR-confiant à petit n / loi
    asymétrique (sous-couvre, dégénère en [x̄,x̄] si variance nulle) ; Hoeffding/emp-Bernstein maintiennent la couverture
    ≥ 1−δ. Renvoie (INTERVALLE, (lo,hi), méthode) ou ABSTENTION. Cf. concentration.py."""
    res = _CON.intervalle(echantillon, borne_inf, borne_sup, delta, methode)
    return _CON.formule(res) if phrase else res


def test_par_pari(observations, p0, *, alpha: float = 0.05, grille_alternatives=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — TEST SÉQUENTIEL par PARI / e-process (e-values, Ville) de H0:p=p0 vs p>p0 sur des
    `observations` binaires. On REJETTE dès que la richesse (e-process de mélange) ≥ 1/α, à un instant QUELCONQUE :
    erreur de type I garantie ≤ α MÊME sous arrêt optionnel (peeking), là où un p-value classique répété l'explose
    (sur-confiant). Renvoie (TEST, {rejet, E_final, seuil}) ou ABSTENTION. Les e-values se multiplient (combinaison
    d'expériences). Cf. e_process.py (distinct de la séquence de confiance `inference_anytime.py`)."""
    res = _EPR.test_sequentiel(observations, p0, alpha, grille_alternatives)
    return _EPR.formule(res) if phrase else res


def strategie_securite(matrice_gains, *, iters: int = 5000, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — résout un JEU À SOMME NULLE (matrice de gains du joueur-ligne) et renvoie la stratégie de
    SÉCURITÉ (maximin) + la valeur du jeu (théorème minimax, via jeu fictif de Brown-Robinson). La maximin GARANTIT la
    valeur contre tout adversaire ; répondre au mieux à un adversaire PRÉSUMÉ serait SUR-confiant (exploitable si
    l'adversaire dévie). Renvoie (JEU, {valeur, x, y, encadrement}) ou ABSTENTION. Cf. jeux_zero_somme.py."""
    res = _JEU.analyse(matrice_gains, iters)
    return _JEU.formule(res) if phrase else res


def effet_selectionne(estimes, sigma, *, alpha: float = 0.05, methode: str = "simultane", phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — INFÉRENCE SÉLECTIVE sur le MEILLEUR de K effets bruités (X_i~N(μ_i,σ²)). L'estimé du
    vainqueur ĵ=argmax est BIAISÉ vers le haut (malédiction du vainqueur) ; un IC NAÏF (`methode='naif'`) sous-couvre =
    SUR-confiant (non-reproductibilité). L'IC `simultane` (Bonferroni) corrige : couvre μ_ĵ ≥ 1−α malgré la sélection.
    Renvoie (ESTIME, {indice, valeur, ic, methode}) ou ABSTENTION. Cf. winner_curse.py (distinct du FDR `fdr_controle`)."""
    res = _WIN.estime(estimes, sigma, alpha, methode)
    return _WIN.formule(res) if phrase else res


def risque_conjoint_extreme(echantillon_uniforme, *, q: float = 0.05, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — risque CONJOINT extrême via COPULE (dépendance). `echantillon_uniforme` = couples (u,v) à
    marginales uniformes (pseudo-observations). Compare P(deux extrêmes simultanés ≤ q) EMPIRIQUE vs l'estimation
    PRÉSUMANT l'INDÉPENDANCE (q²) : sous dépendance de queue, l'indépendance sous-estime massivement le risque
    (illusion de diversification = SUR-confiance). Renvoie (ANALYSE, {jointe_empirique, jointe_independance, lambda_inf,
    facteur}) ou ABSTENTION. Cf. copules.py (`clayton`, `echantillon_clayton`, `lambda_inf_clayton`)."""
    res = _COP.analyse(echantillon_uniforme, q)
    return _COP.formule(res) if phrase else res


def bandit_robuste(recompenses, *, graine: int = 0, gamma=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — BANDIT ADVERSARIAL (EXP3) : choisir des bras en n'observant que la récompense jouée,
    SANS supposer un monde stochastique. `recompenses` = matrice T×K ∈[0,1] (peut être adversariale). Garantit un
    regret SOUS-LINÉAIRE (≤ ~2√((e−1)TK ln K)) vs le meilleur bras fixe → un GLOUTON (qui suppose des récompenses
    stationnaires) serait EXPLOITABLE (regret linéaire) = SUR-confiant. Renvoie (JOUE, {gain, regret, regret_normalise,
    borne}) ou ABSTENTION. Cf. exp3.py (distinct du bandit stochastique UCB/Thompson `bandit.py`)."""
    import random as _r
    res = _EXP.joue(recompenses, _r.Random(graine), gamma)
    return _EXP.formule(res) if phrase else res


def borne_stabilite(train, population, k, *, delta: float = 0.05, graine: int = 0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — borne de généralisation par STABILITÉ ALGORITHMIQUE (Bousquet-Elisseeff), illustrée sur
    k-NN régression (`train`/`population` = listes de (x,y)). Mesure la stabilité β̂ (effet du changement d'un exemple)
    et renvoie R_vrai ≤ R_emp + 2β̂ + (4nβ̂+M)√(ln(1/δ)/2n). Un algorithme INSTABLE (1-NN, β̂ grand) MÉMORISE
    (R_emp≈0) → annoncer le risque empirique est SUR-confiant ; la borne reste large pour le signaler. Renvoie
    (ANALYSE, {r_emp, r_vrai, beta, borne}) ou ABSTENTION. Cf. stabilite_algorithmique.py."""
    import random as _r
    res = _STA.analyse(train, population, k, _r.Random(graine), delta)
    return _STA.formule(res) if phrase else res


def garantie_confidentialite(sensibilite, epsilon, *, bruit=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — vérifie une garantie de CONFIDENTIALITÉ DIFFÉRENTIELLE (mécanisme de Laplace ε-DP).
    `sensibilite`=Δf, `epsilon`=ε annoncé, `bruit`=échelle b (défaut = Δf/ε). SOUS-BRUITER (b<Δf/ε) rend la perte
    réelle Δf/b > ε : on ANNONCE ε mais on offre moins de vie privée = SUR-confiant (un attaquant distingue mieux les
    voisins). Renvoie (PRIVE, {b_requis, epsilon_reel, conforme,…}) ou ABSTENTION. Cf. confidentialite_differentielle.py
    (`mecanisme` pour bruiter, `composition` pour le budget cumulé de K requêtes)."""
    res = _DPV.analyse(sensibilite, epsilon, bruit)
    return _DPV.formule(res) if phrase else res


def choisit_modele_mdl(xs, ys, degre_max, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — SÉLECTION DE MODÈLE par MDL (longueur de description minimale, Rissanen) sur une régression
    polynomiale. Minimise L(modèle)+L(données|modèle) ≈ (n/2)ln(RSS/n)+(k/2)ln(n) = compression/rasoir d'Occam. Choisir
    par erreur d'ENTRAÎNEMENT prendrait le degré maximal (sur-ajustement → prédiction catastrophique = SUR-confiant) ;
    MDL prend le degré parcimonieux qui généralise. Renvoie (SELECTION, {degre_mdl, degre_train, codelengths}) ou
    ABSTENTION. Cf. mdl.py (`predit` pour prédire avec le degré choisi)."""
    res = _MDL.analyse(xs, ys, degre_max)
    return _MDL.formule(res) if phrase else res


def covariance_robuste(echantillons, *, alpha: float = 0.5, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — diagnostique la covariance empirique en GRANDE DIMENSION (Marchenko-Pastur) et la corrige
    par RÉTRÉCISSEMENT (Ledoit-Wolf). `echantillons` = liste de n vecteurs de dimension p. Quand p/n n'est pas petit,
    les valeurs propres empiriques s'étalent (support MP) même si la vraie covariance est isotrope → corrélations et
    facteurs FANTÔMES = SUR-confiance ; le rétrécissement Ŝ=(1−α)S+α·μ·I resserre le spectre. Renvoie (ANALYSE, {eigs,
    cond, eigs_retr, cond_retr, mp,…}) ou ABSTENTION. Cf. covariance_grande_dim.py."""
    res = _CGD.analyse(echantillons, alpha)
    return _CGD.formule(res) if phrase else res


def estime_importance(echantillons, f, densite_cible, densite_proposition, *, seuil_ess: float = 0.1, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — estime E_p[f] par ÉCHANTILLONNAGE PRÉFÉRENTIEL (tirages selon q, pondérés w=p/q) + diagnostic
    par la TAILLE EFFECTIVE D'ÉCHANTILLON ESS=(Σw)²/Σw². Si les poids dégénèrent (ESS≪n), l'écart-type naïf SOUS-ESTIME
    la vraie erreur → s'y fier est SUR-confiant ; le verdict passe à NON_FIABLE (mieux vaut avertir/abstenir). Renvoie
    (FIABLE/NON_FIABLE, {estime, ess, ratio, ic}) ou ABSTENTION. `f`/`densite_cible`/`densite_proposition` = callables.
    Cf. importance_sampling.py."""
    res = _IMP.analyse(echantillons, f, densite_cible, densite_proposition, seuil_ess)
    return _IMP.formule(res) if phrase else res


def mise_kelly(proba_gain, cote, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — fraction de mise optimale (critère de KELLY) pour un pari répété : `proba_gain`=p,
    `cote`=b (gain net par unité misée). f*=(pb−(1−p))/b maximise le taux de croissance LOGARITHMIQUE (fortune typique
    à long terme). SUR-MISER (par sur-confiance dans l'avantage) fait baisser la croissance et, au-delà de ~2f*, RUINE
    la fortune typique malgré une espérance positive ; maximiser l'ESPÉRANCE (miser tout) est l'erreur. Si l'avantage
    est négatif → f*≤0 (ne pas parier). Renvoie (KELLY, {f_kelly, croissance, avantage}) ou ABSTENTION. Cf. kelly.py."""
    res = _KEL.conseille(proba_gain, cote)
    return _KEL.formule(res) if phrase else res


def loi_maximum_entropie(valeurs, moyenne=None, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — loi de MAXIMUM D'ENTROPIE (Jaynes) sur un support `valeurs`, la moins engagée compatible
    avec ce qu'on sait : uniforme si on ne connaît que le support, exponentielle pᵢ∝exp(λ·valeurᵢ) si une `moyenne`
    E[f]=μ est imposée. Adopter une loi plus piquée injecterait une information non justifiée (assigne 0 à des issues
    possibles → surprise infinie) = SUR-confiance. Renvoie (MAXENT, {p, entropie, mu}) ou ABSTENTION (μ hors support).
    Cf. maximum_entropie.py."""
    res = _MEN.analyse(valeurs, moyenne)
    return _MEN.formule(res) if phrase else res


def estime_densite(echantillon, *, fenetre=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — estimation de DENSITÉ par noyau (KDE) avec choix HONNÊTE de la fenêtre h. `fenetre`=None →
    h optimal par vraisemblance leave-one-out (sinon h imposé). Une fenêtre trop ÉTROITE voit des modes-FANTÔMES (un
    mode par point = structure qui est du bruit) → log-vraisemblance held-out catastrophique = SUR-confiance ; le h LOO
    généralise. Renvoie (DENSITE, {h, h_silverman, loo, n_modes}) ou ABSTENTION. Cf. kde.py (`densite(xs,x,h)` pour
    évaluer, `n_modes`, `silverman`)."""
    res = _KDE.analyse(echantillon, fenetre)
    return _KDE.formule(res) if phrase else res


def compare_groupes(groupe_a, groupe_b, *, n_permutations: int = 2000, alpha: float = 0.05, graine: int = 0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — compare deux groupes par TEST DE PERMUTATION (distribution-free) : remélange les étiquettes
    pour obtenir la loi de la statistique sous H0, sans supposer la normalité. Contrôle l'erreur de type I sous
    ÉCHANGEABILITÉ. Sur des données ASYMÉTRIQUES à tailles inégales, le t-test SUR-REJETTE (type I gonflé = SUR-confiant)
    ; la permutation reste calibrée. Renvoie (TEST, {p_perm, p_ttest, rejet_perm, diff}) ou ABSTENTION. Cf.
    test_permutation.py."""
    import random as _r
    res = _PRM.teste(groupe_a, groupe_b, _r.Random(graine), n_permutations, alpha)
    return _PRM.formule(res) if phrase else res


def agrege_preferences(profil, candidats, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — agrège des préférences (CHOIX SOCIAL). `profil` = liste de classements (tuples du meilleur
    au pire), `candidats` = liste. Renvoie (CLAIR, …) si un gagnant de Condorcet existe ET pluralité=Borda=Condorcet,
    sinon (AMBIGU, {condorcet, pluralite, borda, cycle}) : prétendre « le » gagnant objectif quand il y a un cycle de
    Condorcet ou que les méthodes divergent (la pluralité peut élire un candidat battu par tous) serait SUR-confiant
    (Arrow : aucune règle parfaite ≥3 options). Ou ABSTENTION. Cf. choix_social.py."""
    res = _SOC.analyse(profil, candidats)
    return _SOC.formule(res) if phrase else res


def metriques_classification(y_vrai, y_predit, *, positif=1, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — métriques de classification HONNÊTES sous DÉSÉQUILIBRE. Se fier à l'EXACTITUDE est
    SUR-confiant (un classifieur « toujours négatif » a 99% d'exactitude sur une classe à 1% mais ne détecte rien) ;
    rappel / exactitude ÉQUILIBRÉE / MCC donnent l'image réelle. Renvoie (METRIQUES, {exactitude, exactitude_equilibree,
    precision, rappel, mcc, f1}) ou ABSTENTION. Pour la NÉGLIGENCE DU TAUX DE BASE, voir `matrice_confusion.ppv_bayes`
    (P(positif|test+) ≪ fiabilité du test à faible prévalence). Cf. matrice_confusion.py."""
    res = _MCF.analyse(y_vrai, y_predit, positif)
    return _MCF.formule(res) if phrase else res


def valeur_predictive(sensibilite, specificite, prevalence):
    """PHASE 2 (NON-BORNÉ) — P(positif réel | test positif) par Bayes (démasque le taux de base) : un test fiable à 95%
    donne ≈16% de probabilité de maladie à 1% de prévalence, pas 95%. Cf. matrice_confusion.ppv_bayes."""
    return _MCF.ppv_bayes(sensibilite, specificite, prevalence)


def diagnostique_biais_survie(population, seuil_survie, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — quantifie le BIAIS DE SURVIE : estimer sur les seuls SURVIVANTS (valeur ≥ seuil_survie)
    sur-estime la vraie moyenne (les échecs ont disparu de l'échantillon). Renvoie (BIAIS, {moy_survivants,
    moy_population, biais, taux_survie}) ou ABSTENTION. L'estimé survivant est une BORNE SUPÉRIEURE sur-confiante ;
    le biais croît avec la sélection (cf. leçon de Wald : le signal est dans la donnée manquante). Cf. biais_survie.py
    (`moyenne_tronquee_normale` pour la correction sous loi normale)."""
    res = _BSV.analyse(population, seuil_survie)
    return _BSV.formule(res) if phrase else res


def diagnostique_regression_moyenne(mesure1, mesure2, *, fraction: float = 0.1, cote: str = "bas", phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — détecte la RÉGRESSION VERS LA MOYENNE : un groupe sélectionné comme EXTRÊME sur `mesure1`
    (les pires/meilleurs) « rebondit » sur `mesure2` SANS aucune cause, par simple bruit. Renvoie (RTM, {moy_x1_sel,
    moy_x2_sel, changement, attendu_rtm, rho}) ou ABSTENTION. Le changement attendu = (1−ρ)·écart ; l'attribuer à une
    intervention (sans groupe de contrôle) serait SUR-confiant (« la punition marche », « la louange nuit »). Cf.
    regression_moyenne.py."""
    res = _RTM.analyse(mesure1, mesure2, fraction, cote)
    return _RTM.formule(res) if phrase else res


def detecte_simpson(donnees, traitement_a, traitement_b, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — détecte le PARADOXE DE SIMPSON : une tendance vraie dans CHAQUE sous-groupe peut s'inverser
    une fois agrégée. `donnees` = {traitement: {strate: (succès, total)}}. Renvoie (SIMPSON, infos) si renversement
    (gagnant par strate ≠ gagnant agrégé), (COHERENT, infos), ou ABSTENTION. Trancher d'un seul niveau (agrégat OU
    strates) sans modèle CAUSAL est SUR-confiant — les données seules ne disent pas lequel croire. Cf. simpson.py
    (et `causal.py` brique 31 pour l'estimation de l'effet sous confusion)."""
    res = _SIM.analyse(donnees, traitement_a, traitement_b)
    return _SIM.formule(res) if phrase else res


def test_benford(donnees, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — teste si les premiers chiffres de `donnees` suivent la LOI DE BENFORD (P(d)=log₁₀(1+1/d))
    par un χ². Outil d'ANOMALIE/fraude : un écart révèle des nombres possiblement fabriqués. Double prudence : croire
    des chiffres « normaux » à l'œil est sur-confiant, MAIS conclure « fraude » sur un écart l'est AUSSI (des données
    légitimes ne suivent pas Benford) → on rapporte une anomalie à investiguer, pas une preuve. Renvoie (TEST, {chi2,
    p_value, conforme, n}) ou ABSTENTION (<30 données). Cf. benford.py."""
    res = _BEN.analyse(donnees)
    return _BEN.formule(res) if phrase else res


def regression_ridge(X, y, *, penalite: float = 1.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — régression RIDGE (régularisée) vs OLS. `X`=lignes de features, `y`=cibles, `penalite`=λ.
    Sous COLINÉARITÉ, les coefficients OLS ne sont PAS identifiables (variance énorme, signe instable) → s'y fier est
    SUR-confiant ; ridge β̂=(XᵀX+λI)⁻¹Xᵀy les stabilise (biais-variance) et généralise mieux. Renvoie (RIDGE, {beta_ols,
    beta_ridge, norme_ols, norme_ridge}) ou ABSTENTION. Cf. ridge.py (`ajuste(X,y,λ)`, `predit`, `mse`)."""
    res = _RDG.analyse(X, y, penalite)
    return _RDG.formule(res) if phrase else res


def analyse_queue_lourde(donnees, *, k=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — détecte une LOI À QUEUE LOURDE (loi de puissance, P(X>x)∝x^{−α}) et juge la validité d'un
    IC de moyenne. Estime l'indice de queue α par HILL. Calculer moyenne/écart-type/IC gaussien sur des données à
    queue lourde est SUR-CONFIANT : α≤2 ⇒ variance infinie (l'IC du TCL SOUS-COUVRE), α≤1 ⇒ moyenne infinie (la
    moyenne d'échantillon ne converge jamais). Renvoie (ANALYSE, {alpha, variance_finie, moyenne_finie, ic_tcl,
    fiable_tcl}) ou ABSTENTION. Cf. loi_puissance.py (`hill`, `pareto`). Distinct de valeurs_extremes (VaR/quantiles)."""
    res = _LPU.analyse(donnees, k)
    return _LPU.formule(res) if phrase else res


def prix_loterie_petersbourg(fortune, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — prix rationnel d'une loterie à ESPÉRANCE INFINIE (paradoxe de Saint-Pétersbourg : gain 2ⁿ
    avec proba 2⁻ⁿ, E[gain]=∞). Payer selon l'espérance serait SUR-confiant (l'infini vient de gains astronomiques
    jamais réalisés ; la moyenne d'échantillon ne converge même pas). Le prix HONNÊTE est fini et petit ≈ log₂(fortune),
    via l'utilité log (E[ln(W−p+gain)]=ln W) ou un casino à bankroll fini — deux résolutions concordantes. Renvoie
    (PRIX, {prix_log, valeur_casino, esperance}) ou ABSTENTION. Cf. saint_petersbourg.py."""
    res = _STP.analyse(fortune)
    return _STP.formule(res) if phrase else res


def detecte_biais_collision(trait_a, trait_b, seuil_selection, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — détecte le PARADOXE DE BERKSON / biais de COLLISION : deux traits indépendants
    apparaissent NÉGATIVEMENT corrélés dès qu'on sélectionne l'échantillon sur un COLLISIONNEUR (C=A+B>seuil, p.ex.
    « admis si A ou B »). Conclure à une association réelle depuis l'échantillon sélectionné est SUR-confiant —
    l'anti-corrélation est INDUITE par la sélection (≠ confusion : là il faut contrôler l'ancêtre commun ; ici NE PAS
    sélectionner/contrôler le collisionneur). Renvoie (BERKSON, {corr_pop, corr_sel, biais}) ou ABSTENTION. Cf.
    berkson.py."""
    res = _BRK.analyse(trait_a, trait_b, seuil_selection)
    return _BRK.formule(res) if phrase else res


def analyse_ergodicite(facteurs, probas, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — compare moyenne d'ENSEMBLE (E[X], copies parallèles) et taux de croissance TEMPOREL
    (une trajectoire dans le temps) d'un processus multiplicatif. Pour un processus NON-ERGODIQUE (multiplicatif),
    E[X] peut CROÎTRE alors qu'une trajectoire typique DÉCROÎT vers 0 → décider sur l'espérance d'ensemble est
    SUR-confiant ; c'est le taux temporel (géométrique/log) qui compte pour qui vit UNE trajectoire. `facteurs`/`probas`
    = multiplicateurs par pas et leurs probabilités. Renvoie (ERGO, {moyenne_ensemble, taux_temporel, non_ergodique})
    ou ABSTENTION. Cf. ergodicite.py."""
    res = _ERG.analyse(facteurs, probas)
    return _ERG.formule(res) if phrase else res


def classe_taux_robuste(succes, essais, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — corrige la LOI DES PETITS NOMBRES : classer des entités par leur TAUX BRUT (succes/essais)
    à tailles inégales est SUR-confiant — les extrêmes (haut ET bas) sont du bruit de petit échantillon (variance ∝
    1/n). Renvoie des taux RÉTRÉCIS empirique-bayésiens (k+κμ)/(n+κ), κ estimé par vraisemblance marginale : fort
    rétrécissement si la variation est du bruit, faible si vrai signal. Renvoie (ANALYSE, {mu, kappa, bruts, retrecis})
    ou ABSTENTION. Cf. petits_nombres.py."""
    res = _PNB.analyse(succes, essais)
    return _PNB.formule(res) if phrase else res


def clustering_non_parametrique(donnees, *, alpha: float = 0.2, rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — clustering NON-PARAMÉTRIQUE par processus de Dirichlet : fixer K d'avance (k-means, mélange
    à K fixé) est SUR-confiant — le modèle force chaque point dans l'une des K classes, sans masse pour « classe
    nouvelle ». Le mélange DP (restaurant chinois, Gibbs collapsé) infère une LOI a posteriori sur K et réserve une masse
    α/(n+α) à une classe neuve (nouveauté honnête). Renvoie (ANALYSE, {k_estime, k_trace, z, alpha}) ou ABSTENTION
    (rng requis). Cf. dirichlet_process.py."""
    res = _DP.analyse(donnees, alpha=alpha, rng=rng)
    return _DP.formule(res) if phrase else res


def portefeuille_robuste(relatifs, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — allocation séquentielle par PORTEFEUILLE UNIVERSEL (Cover) : miser sur le meilleur actif/la
    meilleure allocation A POSTERIORI est SUR-confiant (inconnu d'avance, aucune garantie pire-cas). Le portefeuille
    universel (mélange de tous les CRP) traque le meilleur portefeuille à rééquilibrage constant avec un regret
    logarithmique borné ((m−1)·ln(n+1)) → 0 par période, sans modèle des rendements. `relatifs` = liste de vecteurs de
    relatifs de prix. Renvoie (ANALYSE, {w_univ, w_best, b_best, regret, regret_par_periode, n}) ou ABSTENTION.
    Cf. portefeuille_universel.py."""
    res = _PFU.analyse(relatifs)
    return _PFU.formule(res) if phrase else res


def bandit_contextuel(thetas, contextes, *, rng=None, alpha: float = 1.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — BANDIT CONTEXTUEL (LinUCB) : le choix GLOUTON (estimation ponctuelle, ε=0) est SUR-confiant
    — il se verrouille sur un bras sous-optimal (regret LINÉAIRE) ; ignorer le contexte l'est aussi quand le meilleur
    bras en dépend. LinUCB ajoute une largeur de confiance α·√(xᵀA⁻¹x) (optimisme calibré, rétrécit avec les données) →
    regret SUBLINÉAIRE. `thetas` = vecteurs de récompense vrais par bras, `contextes` = liste de vecteurs. Renvoie
    (ANALYSE, {regret_glouton, regret_linucb, ...}) ou ABSTENTION (rng requis). Cf. bandit_contextuel.py."""
    res = _BCX.analyse(thetas, contextes, rng, alpha=alpha)
    return _BCX.formule(res) if phrase else res


def inference_selective(pvalues, *, alpha: float = 0.05, methode: str = "sidak", phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — P-HACKING / jardin des chemins bifurquants : rapporter le p brut du « gagnant » sélectionné
    parmi m analyses est SUR-confiant — sous H0 le min de m p-values suit Beta(1,m), donc le FPR réel est 1−(1−α)^m ≈
    m·α ≫ α. Correction = INFÉRENCE SÉLECTIVE (p ajusté Šidák 1−(1−p_min)^m ou Bonferroni m·p_min) → Type-I ≤ α.
    Distinct de FDR (brique 13). Renvoie (ANALYSE, {p_min, p_ajuste, significatif_naif, significatif_ajuste, fpr_naif})
    ou ABSTENTION. Cf. p_hacking.py."""
    res = _PHK.analyse(pvalues, alpha=alpha, methode=methode)
    return _PHK.formule(res) if phrase else res


def revelation_protocole(protocole, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — RÉVÉLATION BAYÉSIENNE / dépendance au protocole (Monty Hall) : le réflexe « 50/50 » qui
    ignore COMMENT l'information a été révélée est SUR-confiant. La vraisemblance P(donnée|hypothèse) dépend du mécanisme :
    protocole « animateur » (informé) → P(gagner en changeant)=2/3 ; protocole « aleatoire » → 1/2. La même observation de
    surface donne des posteriors différents. Renvoie (ANALYSE, {protocole, post, p_changer, brier_naif, brier_bayes}) ou
    ABSTENTION si protocole inconnu. Cf. revelation_bayesienne.py."""
    res = _RVB.analyse(protocole)
    return _RVB.formule(res) if phrase else res


def evidence_vs_n(p, n, *, sigma: float = 1.0, tau: float = 1.0, alpha: float = 0.05, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PARADOXE DE LINDLEY : un seuil de signification α FIXE (« p<0.05 ⇒ rejeter H0 ») est
    SUR-confiant à grand n — à p fixe l'effet x̄=z·σ/√n → 0 et le facteur de Bayes B01 → ∞ (soutient H0). Le fréquentiste
    rejette pendant que le bayésien soutient H0 : la preuve probante d'un même p DÉPEND de n. Correction = rapporter le
    facteur de Bayes. Distinct d'anytime (35, peeking) et p-hacking (98, multiplicité). Renvoie
    (ANALYSE, {z, B01, post_h0, rejette_freq, soutient_h0_bayes, ...}) ou ABSTENTION. Cf. lindley.py."""
    res = _LDL.analyse(p, n, sigma=sigma, tau=tau, alpha=alpha)
    return _LDL.formule(res) if phrase else res


def migration_de_stade(groupe_haut, groupe_bas, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PHÉNOMÈNE DE WILL ROGERS : conclure que « les deux groupes se sont améliorés » après
    reclassification est SUR-confiant. Déplacer d'un groupe haut vers un groupe bas des éléments sous la moyenne du haut
    mais au-dessus de celle du bas fait MONTER les DEUX moyennes — alors que la population groupée est strictement
    INVARIANTE (artefact, rien n'a changé). Migration de stade médicale = survie ↑ dans chaque stade sans progrès réel.
    Distinct de Simpson (87). Renvoie (ANALYSE, {avant, apres, migrants, ...}) ou ABSTENTION. Cf. will_rogers.py."""
    res = _WLR.analyse(groupe_haut, groupe_bas)
    return _WLR.formule(res) if phrase else res


def biais_de_longueur(tailles, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — BIAIS DE LONGUEUR / paradoxe d'inspection & d'amitié : croire que la moyenne d'un échantillon
    biaisé en TAILLE reflète la population est SUR-confiant. L'échantillonnage ∝ taille sur-représente les grands éléments
    → moyenne observée = E[X²]/E[X] = μ + σ²/μ > μ (temps d'attente du bus, « vos amis ont plus d'amis que vous »,
    taille de classe perçue). Correction = moyenne harmonique. Distinct de echantillon_pondere (28, HT général) et
    biais_survie (85). Renvoie (ANALYSE, {mu, mu_biaisee, ecart, ecart_theorique}) ou ABSTENTION. Cf. biais_longueur.py."""
    res = _BLG.analyse(tailles)
    return _BLG.formule(res) if phrase else res


def probabilite_posterieure_test(sensibilite, specificite, prevalence, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — NÉGLIGENCE DU TAUX DE BASE / paradoxe du faux positif : lire « test positif » comme
    « malade » (confondre la sensibilité P(+|malade) avec la VPP P(malade|+)) est SUR-confiant — ça ignore la PRÉVALENCE.
    À faible prévalence, même un excellent test donne une VPP basse (la plupart des positifs sont faux). VPP =
    sens·prév/[sens·prév+(1−spéc)(1−prév)]. Distinct de matrice_confusion (84). Renvoie
    (ANALYSE, {vpp, naive, ecart, frac_faux_positifs, brier_naif, brier_bayes}) ou ABSTENTION. Cf. taux_de_base.py."""
    res = _TDB.analyse(sensibilite, specificite, prevalence)
    return _TDB.formule(res) if phrase else res


def deux_enveloppes(K: int = 10, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PARADOXE DES DEUX ENVELOPPES : l'argument « l'autre vaut 1.25× la mienne, échangeons
    toujours » est SUR-confiant — il pose P(petite|montant)=½ pour TOUTE valeur, ce qui suppose un a priori IMPROPRE
    (uniforme non borné). Sous un a priori propre, P(petite|a)=½ seulement à l'intérieur (1 au plancher, 0 au plafond) et
    le gain INCONDITIONNEL d'échange = 0 (échangeabilité). Renvoie (ANALYSE, {gain_interieur, gain_inconditionnel,
    p_petite_interieur, ...}) ou ABSTENTION. Cf. deux_enveloppes.py."""
    res = _DEV.analyse(K)
    return _DEV.formule(res) if phrase else res


def jeux_parrondo(n: int = 40000, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PARADOXE DE PARRONDO : conclure « perdant + perdant = perdant » est SUR-confiant. Deux jeux
    qui perdent ISOLÉMENT (A = pièce biaisée ½−ε ; B = dépendant de l'état capital mod 3) deviennent GAGNANTS quand on
    les mélange — A redistribue l'état caché hors de la configuration où B est mauvais. L'intuition de dominance ignore la
    chaîne de Markov de l'état. Renvoie (ANALYSE, {derive_A, derive_B, derive_mix, A_perd, B_perd, mix_gagne}) ou
    ABSTENTION. Distinct d'ergodicite (93). Cf. parrondo.py."""
    res = _PAR.analyse(n)
    return _PAR.formule(res) if phrase else res


def reseau_braess(n: int = 4000, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PARADOXE DE BRAESS : « ajouter une route/option ne peut qu'aider » (monotonie) est
    SUR-confiant en routage ÉGOÏSTE. Sur le réseau canonique, ajouter un raccourci gratuit fait passer le temps de trajet
    d'équilibre de 65 à 80 (PIRE pour tous) — l'équilibre de Nash est sous-optimal (prix de l'anarchie). Renvoie
    (ANALYSE, {temps_sans_pont, temps_avec_pont, optimum_social, braess, prix_anarchie}) ou ABSTENTION. Distinct de
    jeux_zero_somme (70) et choix_social (83). Cf. braess.py."""
    res = _BRA.analyse(n)
    return _BRA.formule(res) if phrase else res


def sophisme_main_chaude(p: float = 0.5, n: int = 4, *, rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — SOPHISME DU JOUEUR & MAIN CHAUDE : DEUX sur-confiances. (a) attendre un renversement après une
    série (« Face est dû ») est SUR-confiant — l'indépendance donne P(succès|succès précédent)=p. (b) MAIS l'estimateur
    naïf de cette conditionnelle sur séquences FINIES est biaisé SOUS p (Miller-Sanjurjo) : conclure « pas de main chaude »
    sans corriger ce biais est AUSSI sur-confiant. Renvoie (ANALYSE, {cond_vraie, biais_naif, ampleur_biais, n}) ou
    ABSTENTION (rng requis). Distinct de regression_moyenne (86). Cf. main_chaude.py."""
    res = _MCH.analyse(p, n, rng=rng)
    return _MCH.formule(res) if phrase else res


def effet_de_cadrage(*, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — EFFET DE CADRAGE / invariance de description : tenir une préférence ÉNONCÉE pour « la »
    préférence est SUR-confiant. Le même choix (maladie asiatique) présenté en GAINS vs PERTES renverse le risque (averse
    en gain, chercheur en perte) alors que les loteries sont IDENTIQUES — violation de l'invariance de description,
    incohérence exploitable (money pump). L'agent à utilité frame-INVARIANTE ne renverse pas. Renvoie
    (ANALYSE, {choix_cadre_gain, choix_cadre_perte, renversement, etapes_money_pump, ...}). Distinct de decision (8) et
    variational_preferences (62). Cf. cadrage.py."""
    res = _CAD.analyse()
    return _CAD.formule(res) if phrase else res


def masse_manquante(comptes, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — GOOD-TURING / espèces invisibles : assigner probabilité 0 à un événement JAMAIS observé (MLE)
    est SUR-confiant — log-loss infini sur un tirage inédit ; et le nombre d'espèces vues SOUS-estime la richesse. La
    probabilité que le prochain tirage soit INÉDIT ≈ N₁/N (singletons) ; richesse totale ≈ Chao1 S_obs+N₁²/(2N₂). `comptes`
    = dict espèce→nb d'observations. Renvoie (ANALYSE, {masse_manquante, richesse_chao1, especes_vues, logloss_naif,
    logloss_gt}) ou ABSTENTION. Distinct de loi_puissance (90) et maximum_entropie (80). Cf. good_turing.py."""
    res = _GTU.analyse(comptes)
    return _GTU.formule(res) if phrase else res


def coherence_conjonction(pA, pB, pAB, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — SOPHISME DE LA CONJONCTION (Linda) : juger P(A∧B) > P(A) (par représentativité) est
    SUR-confiant — viol de la monotonie, un conjoint inclut sa conjonction. Tout jugement de conjonction doit respecter
    les bornes de Fréchet max(0,pA+pB−1) ≤ P(A∧B) ≤ min(pA,pB) ; sinon un LIVRE HOLLANDAIS extrait une perte sûre
    (pAB−pA) dans tous les états. Renvoie (ANALYSE, {coherent, bornes, sophisme, profit_livre_hollandais}) ou ABSTENTION.
    Distinct de copules (72) et bayes. Cf. conjonction.py."""
    res = _CJN.analyse(pA, pB, pAB)
    return _CJN.formule(res) if phrase else res


def cout_irrecuperable(valeur_esperee, cout_restant, sunk, *, lam: float = 0.5, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — SOPHISME DU COÛT IRRÉCUPÉRABLE (effet Concorde) : intégrer une dépense DÉJÀ engagée S dans une
    décision future est SUR-confiant. La décision rationnelle ne compare que le FUTUR : continuer ssi E[V] > C,
    INDÉPENDAMMENT de S. L'agent biaisé pondère S positivement et poursuit des projets perdants (E[V]<C) → perte d'argent
    en espérance + escalade d'engagement. Renvoie (ANALYSE, {continuer_rationnel, continuer_biaise, erreur_biais,
    ev_continuation}) ou ABSTENTION. Distinct de decision (8) et risque_conforme (12). Cf. cout_irrecuperable.py."""
    res = _SUN.analyse(valeur_esperee, cout_restant, sunk, lam=lam)
    return _SUN.formule(res) if phrase else res


def probabilite_geometrique(methode=None, *, n: int = 200000, rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PARADOXE DE BERTRAND : énoncer « LA » probabilité d'un événement géométrique (« une corde
    aléatoire ») sans spécifier le MÉCANISME de tirage est SUR-confiant. Trois constructions « uniformes » légitimes
    donnent 1/3 (extrémités), 1/2 (rayon), 1/4 (milieu) — le principe d'indifférence est ambigu en continu. methode=None
    → ABSTENTION (question mal posée) ; une méthode fixée → probabilité déterminée. Renvoie (ANALYSE, {methode, p_sim,
    p_theorique}) ou ABSTENTION. Cf. bertrand.py."""
    res = _BTR.analyse(methode, n=n, rng=rng)
    return _BTR.formule(res) if phrase else res


def loi_de_goodhart(pressions=(0.0, 1.0, 3.0), *, lam: float = 1.0, n: int = 4000, rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — LOI DE GOODHART : optimiser un PROXY corrélé à l'objectif vrai est SUR-confiant (« quand une
    mesure devient une cible, elle cesse d'être une bonne mesure »). Sous pression d'optimisation, la composante gameable
    inflate la mesure (P=U+g) en dégradant la qualité livrée (U−λg) : la corrélation proxy/objectif s'effondre, le
    métrique des sélectionnés MONTE pendant que leur qualité TOMBE. Distinct de winner_curse (71). Renvoie
    (ANALYSE, {courbe, corr_chute, qualite_chute, proxy_monte}) ou ABSTENTION (rng requis). Cf. goodhart.py."""
    res = _GDH.analyse(pressions, lam=lam, n=n, rng=rng)
    return _GDH.formule(res) if phrase else res


def estimation_jointe_stein(theta, *, sigma2: float = 1.0, T: int = 20000, rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PARADOXE DE STEIN : estimer d≥3 moyennes en prenant chaque observation comme son estimation
    (le MLE θ̂=X) est SUR-confiant — le MLE est INADMISSIBLE, dominé en risque total par James-Stein θ̂=(1−(d−2)σ²/‖X‖²)₊X
    pour TOUT θ (même quantités sans rapport). Le rétrécissement mutualise le bruit. Distinct de petits_nombres (94) et
    ridge (89). Renvoie (ANALYSE, {d, risque_mle, risque_js, domine, gain_relatif}) ou ABSTENTION (d<3 : MLE admissible).
    Cf. stein.py."""
    res = _STN.analyse(theta, sigma2=sigma2, T=T, rng=rng)
    return _STN.formule(res) if phrase else res


def stats_resumees_suffisent(jeux=None, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — QUARTET D'ANSCOMBE : conclure « même relation » à partir de statistiques RÉSUMÉES identiques
    (moyenne, variance, corrélation, droite de régression) est SUR-confiant. Quatre jeux aux stats identiques (corr 0.82,
    y=3+0.5x) ont des structures radicalement différentes : linéaire / courbe / valeur aberrante / point à fort levier.
    Il faut examiner les DIAGNOSTICS (résidu max, gain quadratique, levier). Renvoie (ANALYSE, {stats, diagnostics,
    stats_identiques}) ou ABSTENTION. Distinct de regression_moyenne (86) et ridge (89). Cf. anscombe.py."""
    res = _ANS.analyse(jeux)
    return _ANS.formule(res) if phrase else res


def accord_aumann(omega_etats, P1, P2, E, omega, *, prior1=None, prior2=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — THÉORÈME D'ACCORD D'AUMANN : « convenir d'être en désaccord » est SUR-confiant. Deux agents
    bayésiens à PRIOR COMMUN dont les postérieurs d'un événement E sont de connaissance commune ne peuvent PAS différer —
    échanger les postérieurs les force à converger vers une valeur égale (en un nombre fini de tours). À priors DIFFÉRENTS,
    un désaccord peut persister (le théorème requiert le prior commun). Renvoie (ANALYSE, {init1, init2, final1, final2,
    egaux, rounds}) ou ABSTENTION. Distinct de bayes (combinaison). Cf. aumann.py."""
    res = _AUM.analyse(omega_etats, P1, P2, E, omega, prior1=prior1, prior2=prior2)
    return _AUM.formule(res) if phrase else res


def sagesse_des_foules(p: float = 0.6, *, kappa=None, tailles=(11, 51, 201), rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — THÉORÈME DU JURY DE CONDORCET : « plus de votants ⇒ meilleure décision » est SUR-confiant.
    La majorité ne converge vers la vérité que si les votants sont INDÉPENDANTS et COMPÉTENTS (p>½). Si p<½ la majorité
    converge vers le FAUX (de plus en plus confiante et fausse) ; si les votants sont CORRÉLÉS (kappa fini), la précision
    PLAFONNE loin de 1. Renvoie (ANALYSE, {courbe, monte, acc_grand_N, ...}) ou ABSTENTION. Distinct de choix_social (83,
    agrégation de préférences). Cf. jury_condorcet.py."""
    res = _JRY.analyse(p, kappa=kappa, tailles=tailles, rng=rng)
    return _JRY.formule(res) if phrase else res


def paradoxe_allais(gamma: float = 0.5, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PARADOXE D'ALLAIS : supposer que les préférences satisfont l'axiome d'INDÉPENDANCE (donc
    l'utilité espérée) est SUR-confiant. Le schéma d'Allais (1A≻1B et 2B≻2A, à conséquence commune partagée) est
    INCOHÉRENT avec TOUTE utilité — il impose 0.11·u(1M) à la fois > et < 0.10·u(5M)+0.01·u(0). Un agent à effet de
    certitude (rang-dépendant, γ<1) le reproduit. Renvoie (ANALYSE, {eu_allais, rdu_allais, A, B}) ou ABSTENTION.
    Distinct de cadrage (108) et decision (8). Cf. allais.py."""
    res = _ALA.analyse(gamma)
    return _ALA.formule(res) if phrase else res


def paradoxe_lord(groupe_A, groupe_B, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PARADOXE DE LORD : annoncer « l'effet » d'un groupe depuis une donnée pré/post
    observationnelle sans modèle causal est SUR-confiant. Le score de changement (gain Y−X) et l'ANCOVA (Y ajusté sur X)
    donnent des conclusions OPPOSÉES sur les mêmes données quand la pente intra b≠1 : ANCOVA = changement +
    (1−b)·écart_baselines. Ils répondent à des questions DIFFÉRENTES. `groupe_A`/`groupe_B` = listes de (X, Y). Renvoie
    (ANALYSE, {diff_changement, diff_ancova, pente_intra, divergence}) ou ABSTENTION. Distinct de Simpson (87) et causal
    (31). Cf. lord.py."""
    res = _LRD.analyse(groupe_A, groupe_B)
    return _LRD.formule(res) if phrase else res


def conditionnement_continu(procedure=None, *, n: int = 2000000, rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PARADOXE DE BOREL-KOLMOGOROV : écrire P(X | Y=y) pour Y CONTINUE comme un objet unique est
    SUR-confiant. {Y=y} est de mesure nulle ; la loi conditionnelle dépend de la PROCÉDURE limite. Sur une sphère, deux
    bandes rétrécissant vers le même grand cercle donnent une latitude ∝ cos θ (longitude) ou UNIFORME (perpendiculaire).
    procedure=None → ABSTENTION (loi non définie). Renvoie (ANALYSE, {procedure, e_abs, theorique}) ou ABSTENTION.
    Distinct de Bertrand (112) et revelation_bayesienne (99). Cf. borel_kolmogorov.py."""
    res = _BKL.analyse(procedure, n=n, rng=rng)
    return _BKL.formule(res) if phrase else res


def regression_temporelle_fallacieuse(n: int = 100, *, T: int = 2000, rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — RÉGRESSION FALLACIEUSE (Granger-Newbold) : régresser deux séries NON-STATIONNAIRES (marches
    aléatoires, tendances) et lire le t/R² comme une relation est SUR-confiant. Deux marches INDÉPENDANTES donnent ~75 %
    de t « significatif » (au lieu de 5 %) et un R² élevé — les résidus sont non-stationnaires, l'inférence OLS est
    invalide. Correction = DIFFÉRENCIER (→ ~5 %). Séries stationnaires (bruit blanc) → OLS correct. Renvoie
    (ANALYSE, {fp_niveaux, r2_niveaux, fp_differences, fp_bruit_blanc}) ou ABSTENTION. Cf. regression_fallacieuse.py."""
    res = _RGF.analyse(n=n, T=T, rng=rng)
    return _RGF.formule(res) if phrase else res


def malediction_dimension(dims=(2, 10, 100, 1000), *, rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — MALÉDICTION DE LA DIMENSION : se fier aux DISTANCES (kNN, noyaux, similarité euclidienne) en
    haute dimension est SUR-confiant. Les distances se CONCENTRENT : (D_max−D_min)/D_min → 0 et D_min/D_max → 1 (le plus
    proche voisin ≈ le plus lointain) ; la masse d'une gaussienne se concentre dans une coquille à √d, pas près du mode.
    En basse dimension, le contraste reste informatif. Renvoie (ANALYSE, {courbe}) ou ABSTENTION. Distinct de
    covariance_grande_dim (77) et concentration (68). Cf. malediction_dimension.py."""
    res = _MDD.analyse(dims, rng=rng)
    return _MDD.formule(res) if phrase else res


def pascal_mugging(eps: float = 1e-9, D: float = 5.0, *, U_max: float = 1e6, c: float = 1.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PROBLÈME DE PASCAL (Pascal's mugging) : maximiser naïvement l'espérance d'utilité avec des
    gains NON BORNÉS est SUR-confiant. Une promesse colossale M de probabilité infime ε domine la décision (ε·M > D dès
    que M est grand) → l'agent paie n'importe quel maître-chanteur : exploitable sans borne. Corrections = utilité BORNÉE
    (plafond U_max) ou PÉNALITÉ DE LEVIER (P(délivrer M)=min(ε,c/M) ⇒ P·M ≤ c). Renvoie (ANALYSE, {lignes,
    naif_paie_la_plus_grande, ev_levier_max, ...}) ou ABSTENTION. Distinct de saint_petersbourg (91) et decision (8).
    Cf. pascal_mugging.py."""
    res = _PMG.analyse(eps=eps, D=D, U_max=U_max, c=c)
    return _PMG.formule(res) if phrase else res


def paradoxe_ellsberg(pB: float = 1.0 / 3.0, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — PARADOXE D'ELLSBERG (aversion à l'ambiguïté) : supposer qu'un agent rationnel a un PRIOR
    UNIQUE (probabilités précises) est SUR-confiant. Le schéma d'Ellsberg (préférer le connu : A≻B et D≻C) est INCOHÉRENT
    avec toute probabilité unique — il exige P(noir) à la fois < et > 1/3 (violation du principe de la chose sûre). Un
    agent averse à l'ambiguïté (maxmin / probabilités inférieures) le reproduit ; l'ambiguïté exige des probabilités
    IMPRÉCISES. Renvoie (ANALYSE, {eu_ellsberg, maxmin_ellsberg, pB}) ou ABSTENTION. Analogue ambiguïté d'Allais (118).
    Distinct de decision_ambiguite (60) et smooth_ambiguity (61). Cf. ellsberg.py."""
    res = _ELL.analyse(pB)
    return _ELL.formule(res) if phrase else res


def effet_ancrage(theta: float = 100.0, alpha: float = 0.6, *, n: int = 5000, rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — EFFET D'ANCRAGE QUANTITATIF : se fier à une estimation contaminée par une ancre NON
    PERTINENTE est SUR-confiant. L'ancrage-ajustement (estimation = ancre + α·(signal−ancre), α<1) rend l'estimation
    corrélée à un nombre aléatoire dénué de sens (devrait être 0) et augmente l'erreur quadratique. Débiaiser = ajuster
    pleinement (α=1). Renvoie (ANALYSE, {contamination, contamination_libre, mse_ancre, mse_libre, ecart_haute_basse})
    ou ABSTENTION. Distinct de cadrage (108). Cf. ancrage.py."""
    res = _ANC.analyse(theta, alpha, n=n, rng=rng)
    return _ANC.formule(res) if phrase else res


def biais_publication(theta: float = 0.2, *, n_etudes: int = 20000, rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — BIAIS DE PUBLICATION (file-drawer) : se fier à l'effet moyen de la littérature PUBLIÉE est
    SUR-confiant. Seuls les résultats significatifs sont publiés ⇒ la méta-analyse du publié SUR-ESTIME l'effet, surtout
    via le small-study effect (petites études publiées = effet bien plus grand = asymétrie en entonnoir). Sans filtre, la
    moyenne est non biaisée. Renvoie (ANALYSE, {moyenne_toutes, moyenne_publiee, effet_petites, effet_grandes}) ou
    ABSTENTION. Distinct de meta_analyse (37) et p_hacking (98, sélection intra-étude). Cf. biais_publication.py."""
    res = _BPB.analyse(theta, n_etudes=n_etudes, rng=rng)
    return _BPB.formule(res) if phrase else res


def no_free_lunch(N: int = 5, train=(0, 1), test=(2, 3, 4), *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — THÉORÈME NO FREE LUNCH (Wolpert-Macready) : prétendre qu'un apprenant/optimiseur est
    universellement meilleur est SUR-confiant. Moyenné sur TOUTES les fonctions cibles, tous les apprenants ont la même
    erreur hors-échantillon (0.5) ; ce qu'un biais inductif gagne sur une classe, il le perd exactement sur le
    complément. Un biais adapté aide sur un monde STRUCTURÉ (hypothèse, pas garantie universelle). Renvoie
    (ANALYSE, {moyennes, sur_constantes}) ou ABSTENTION. Distinct de PAC (63), Rademacher (66), stabilité (74).
    Cf. no_free_lunch.py."""
    res = _NFL.analyse(N, tuple(train), tuple(test))
    return _NFL.formule(res) if phrase else res


def vote_manipulable(profil=None, cands=("A", "B", "C"), *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — THÉORÈME DE GIBBARD-SATTERTHWAITE : croire qu'une règle de vote révèle les VRAIES préférences
    est SUR-confiant. Pour ≥3 options, toute règle déterministe non-dictatoriale est MANIPULABLE — un votant gagne à
    MENTIR (enterrer un rival). Avec 2 options, la majorité est strategyproof (l'impossibilité requiert ≥3). Renvoie
    (ANALYSE, {gagnant_sincere, manipulation, manipulable, profil}) ou ABSTENTION. Distinct de choix_social (83,
    Condorcet/Arrow = agrégation). Cf. gibbard_satterthwaite.py."""
    res = _GST.analyse(profil, cands)
    return _GST.formule(res) if phrase else res


def flaw_of_averages(f, mu, sigma, convexite, *, rng=None, n: int = 200000, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — INÉGALITÉ DE JENSEN / flaw of averages : brancher la MOYENNE des entrées dans une fonction
    NON LINÉAIRE pour obtenir la sortie moyenne est SUR-confiant. f convexe ⇒ E[f(X)] ≥ f(E[X]) (sous-estime) ; f concave
    ⇒ ≤ (sur-estime) ; l'écart de Jensen croît avec la variance (= σ² pour x²). Pour une fonction linéaire, c'est exact.
    `convexite` ∈ {'convexe','concave','lineaire'}. Renvoie (ANALYSE, {e_f, f_e, ecart, signe_attendu_ok}) ou ABSTENTION.
    Distinct de propagation (5) et fermi (29). Cf. jensen.py."""
    res = _JEN.analyse(f, mu, sigma, convexite, rng=rng, n=n)
    return _JEN.formule(res) if phrase else res


def dunning_kruger_artefact(info: float = 0.0, *, n: int = 20000, rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — EFFET DUNNING-KRUGER comme ARTEFACT : lire le graphe DK (les faibles se surestiment, les
    forts se sous-estiment) comme une preuve d'« incompétence sur-confiante » est SUR-confiant. Le motif émerge même
    quand l'auto-évaluation est du PUR BRUIT (info=0 → pente −1), par régression vers la moyenne ; il disparaît avec une
    connaissance parfaite (info=1 → pente 0) ; la pente vaut −(1−info). Le graphe ne distingue pas un vrai effet d'un
    bruit. Renvoie (ANALYSE, {quartiles, surestim_bas, surestim_haut, pente}) ou ABSTENTION. Distinct de
    regression_moyenne (86). Cf. dunning_kruger.py."""
    res = _DKR.analyse(info, n=n, rng=rng)
    return _DKR.formule(res) if phrase else res


def surapprentissage(degres=(1, 2, 3, 5, 7, 9), n_train: int = 15, *, rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — SUR-APPRENTISSAGE (overfitting) : juger un modèle sur son ajustement EN ÉCHANTILLON est
    SUR-confiant. L'erreur d'entraînement décroît toujours avec la complexité, mais l'erreur de TEST suit une courbe en U
    (un polynôme de degré élevé colle aux données mais explose hors échantillon). Correction = validation croisée /
    hold-out. À la bonne complexité, train ≈ test. Renvoie (ANALYSE, {courbe, degre_choisi_holdout}) ou ABSTENTION.
    Distinct des bornes (PAC 63, Rademacher 66, MDL 76). Cf. surapprentissage.py."""
    res = _SAP.analyse(degres, n_train=n_train, rng=rng)
    return _SAP.formule(res) if phrase else res


def loi_grands_nombres(n: int = 10000, *, T: int = 3000, rng=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — LOI DES GRANDS NOMBRES MAL COMPRISE : « à la longue ça s'équilibre, je vais me refaire » est
    SUR-confiant. C'est la MOYENNE qui converge vers 0 (LGN), pas la SOMME : pour une marche équitable, E|S_n|=√(2n/π)
    GRANDIT comme √n (la richesse cumulée diverge), et le temps passé en tête suit la loi de l'ARCSINUS (en U, pas ½).
    Confondre moyenne et somme est l'erreur. Renvoie (ANALYSE, {moyenne, abs_somme, abs_theorique, frac_extreme,
    frac_milieu}) ou ABSTENTION. Distinct du sophisme du joueur (107) et d'ergodicite (93). Cf. loi_grands_nombres.py."""
    res = _LGN.analyse(n=n, T=T, rng=rng)
    return _LGN.formule(res) if phrase else res


def intervalle_proportion(k: int, n: int, *, confiance: float = 0.95, methode: str = "wilson", phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — intervalle de confiance d'une PROPORTION (k succès sur n). Renvoie
    (ESTIMATION, (lo, hi), confiance) ou ABSTENTION. Défaut = WILSON (calibré même à petit effectif / p extrême) ;
    l'intervalle de Wald (`methode='wald'`) est SUR-CONFIANT et dégénère en certitude factice [0,0] si k=0.
    Cf. proportion_binomiale.py."""
    res = _PBI.intervalle(k, n, confiance, methode)
    return _PBI.formule(res) if phrase else res


def optimise_couteux(f, borne_inf, borne_sup, *, n_init: int = 4, n_iter: int = 12, methode: str = "ucb",
                     kappa: float = 2.0, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — OPTIMISATION BAYÉSIENNE d'une fonction coûteuse (maximisation, peu d'évaluations).
    Surrogate par processus gaussien + acquisition UCB/EI : l'incertitude calibrée guide l'exploration et évite le
    piège de l'optimum local où une recherche GLOUTONNE (`methode='glouton'`) reste coincée. Renvoie
    (ESTIMATION, (x*, y*), historique) ou ABSTENTION. Cf. optimisation_bayesienne.py."""
    res = _OBA.optimise(f, borne_inf, borne_sup, n_init=n_init, n_iter=n_iter, methode=methode, kappa=kappa)
    return _OBA.formule(res) if phrase else res


def acquisition_prochain_essai(xs, ys, borne_inf, borne_sup, *, methode: str = "ucb", kappa: float = 2.0):
    """PHASE 2 (NON-BORNÉ) — étant donné les évaluations déjà faites (xs, ys), propose le PROCHAIN point à évaluer
    (celui qui maximise l'acquisition UCB/EI). Renvoie un x ou None. Cf. optimisation_bayesienne.py."""
    return _OBA.propose_prochain(xs, ys, borne_inf, borne_sup, methode=methode, kappa=kappa)


def calibre_classement(diffs, ordres, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — calibre la CONFIANCE des comparaisons par paires d'un classement : apprend une température
    T sur (diffs=s_i−s_j, ordres=1 si i vraiment mieux) de sorte que « X % sûr que A passe avant B » s'avère juste ~X %.
    Le sigmoïde brut sur-confie en tête de liste ; T n'altère pas l'ordre. Renvoie (ESTIMATION, T, log-perte) ou
    ABSTENTION. Cf. calibration_ranking.py."""
    res = _CRK.calibre(diffs, ordres)
    return _CRK.formule(res) if phrase else res


def proba_mieux_classe(score_a, score_b, *, temperature: float = 1.0):
    """PHASE 2 (NON-BORNÉ) — probabilité (calibrée si `temperature` apprise via calibre_classement) que A soit mieux
    classé que B : σ((score_a − score_b)/temperature). Cf. calibration_ranking.py."""
    return _CRK.proba_mieux(score_a, score_b, temperature)


def qualite_classement(ordre_predit, pertinences, *, k=None):
    """PHASE 2 (NON-BORNÉ) — NDCG@k du classement prédit (1 = idéal). Cf. calibration_ranking.py."""
    return _CRK.ndcg(ordre_predit, pertinences, k)


def prevoit_series_couplees(serie, *, horizon: int = 1, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — ajuste un VAR(1) sur des séries multivariées COUPLÉES (`serie` = liste de vecteurs) et
    prépare la prévision à `horizon` pas. Renvoie (ESTIMATION, modele, None) puis utiliser
    `ia.region_conjointe_prevision(modele, ...)`. L'incertitude croît avec l'horizon ; une boîte d'intervalles
    indépendants serait sur-confiante sur l'événement conjoint. Cf. serie_multivariee.py."""
    res = _SMV.ajuste(serie)
    return _SMV.formule(res) if phrase else res


def region_conjointe_prevision(modele, x_dernier, erreurs_calibration, *, horizon: int = 1, confiance: float = 0.90):
    """PHASE 2 (NON-BORNÉ) — région CONJOINTE de prévision à `horizon` pas : (mu, cov, seuil_conforme, cov_inv). Un
    point y est dans la région ssi serie_multivariee.mahalanobis2(y, mu, cov_inv) <= seuil. `erreurs_calibration` =
    erreurs de prévision passées (pour le seuil conforme, distribution-free). Cf. serie_multivariee.py."""
    mu, cov = _SMV.prevision(modele, x_dernier, horizon)
    cinv = _SMV._inv(cov)
    d2 = [_SMV.mahalanobis2(e, [0.0] * len(mu), cinv) for e in erreurs_calibration]
    return {"mu": mu, "cov": cov, "seuil": _SMV.seuil_conforme(d2, confiance), "cov_inv": cinv}


def intervalle_bootstrap(data, stat, *, confiance: float = 0.90, methode: str = "bca", B: int = 2000, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — intervalle de confiance par BOOTSTRAP pour une statistique ARBITRAIRE `stat` (médiane,
    variance, ratio, corrélation…), sans formule analytique. Renvoie (ESTIMATION, (lo, hi), confiance) ou ABSTENTION.
    methode ∈ {'bca','percentile','normal'} ; le BCa corrige biais/asymétrie. Plaquer l'erreur-type de la moyenne sur
    une autre statistique serait sur-confiant. Cf. bootstrap.py."""
    res = _BST.intervalle(data, stat, confiance, methode, B)
    return _BST.formule(res) if phrase else res


def auc_avec_intervalle(scores, labels, *, confiance: float = 0.95, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — pouvoir DISCRIMINANT d'un classifieur (AUC = P(positif mieux scoré qu'un négatif)) AVEC son
    intervalle de confiance de Hanley-McNeil (qui dépend de la taille des DEUX classes). Renvoie
    (ESTIMATION, (auc, (lo, hi)), confiance) ou ABSTENTION. Annoncer l'AUC sans intervalle, ou avec une erreur-type
    « paires indépendantes », est sur-confiant. Cf. roc_auc.py."""
    res = _ROC.evalue(scores, labels, confiance)
    return _ROC.formule(res) if phrase else res


def auc_bat_le_hasard(scores, labels, *, confiance: float = 0.95):
    """PHASE 2 (NON-BORNÉ) — le classifieur discrimine-t-il SIGNIFICATIVEMENT (borne basse de l'IC de Hanley > 0.5) ?
    Renvoie True/False/None. Évite de conclure « mon modèle marche » sur une AUC ponctuelle incertaine. Cf. roc_auc.py."""
    return _ROC.bat_le_hasard(scores, labels, confiance)


def corrige_prevalence(posteriors_cible, prior_train, *, prior_cible=None, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — corrige les probabilités d'un classifieur quand la PRÉVALENCE des classes a changé entre
    l'entraînement et le déploiement (LABEL SHIFT, Saerens). `posteriors_cible` = liste de distributions p_train(y|x) sur
    la cible ; si `prior_cible` est None il est estimé par EM SANS étiquettes. Sans correction, le classifieur est
    sur-confiant sur la classe devenue rare. Renvoie (ESTIMATION, {prior_cible, posteriors}, None) ou ABSTENTION.
    Cf. prior_shift.py."""
    res = _PSH.adapte(posteriors_cible, prior_train, prior_cible)
    return _PSH.formule(res) if phrase else res


def corrige_posterior_prevalence(p_train, prior_train, prior_cible):
    """PHASE 2 (NON-BORNÉ) — corrige UN posterior p_train(y|x) vers la prévalence cible (label shift). Cf. prior_shift.py."""
    return _PSH.corrige_posterior(p_train, prior_train, prior_cible)


def moyenne_modeles(xs, ys, *, degres=(1, 2, 3), phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — ajuste plusieurs modèles polynomiaux candidats et les pondère par leur probabilité a
    posteriori (BMA, poids ∝ exp(−½·BIC)). Renvoie (ESTIMATION, {modeles, poids}, None) puis utiliser
    `ia.prediction_modeles(etat, x0)`. Choisir le seul « meilleur » modèle ignore l'incertitude de SÉLECTION et
    sur-confie (surtout à l'extrapolation). Cf. bma.py."""
    res = _BMA.ajuste(xs, ys, degres)
    return _BMA.formule(res) if phrase else res


def prediction_modeles(etat, x0, *, confiance: float = 0.90, meilleur_seul: bool = False):
    """PHASE 2 (NON-BORNÉ) — prédiction à x0 par BMA (variance intra + INTER modèles) ou, si `meilleur_seul`, par le seul
    modèle de poids max (sur-confiant). Renvoie (mu, (lo, hi)). Cf. bma.py."""
    return _BMA.intervalle_meilleur(etat, x0, confiance) if meilleur_seul else _BMA.intervalle_bma(etat, x0, confiance)


def calibre_agregateur_previsions(previsions, issues, historiques, *, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — apprend à AGRÉGER des prévisions probabilistes de plusieurs sources : pondère chaque source
    par son score de Brier passé (`historiques`) puis apprend un facteur d'extrémisation borné qui défait la
    SOUS-CONFIANCE de la moyenne simple. Renvoie (ESTIMATION, {poids, a}, None) puis utiliser
    `ia.agrege_previsions(probas, etat)`. Cf. agregation_previsions.py."""
    res = _AGP.calibre_agregateur(previsions, issues, historiques)
    return _AGP.formule(res) if phrase else res


def agrege_previsions(probas, etat):
    """PHASE 2 (NON-BORNÉ) — agrège une liste de probabilités (une par source) en une proba calibrée, via l'état appris
    (`{poids, a}`) de `calibre_agregateur_previsions`. Plus tranché que la moyenne (sous-confiante) sans sur-confier.
    Cf. agregation_previsions.py."""
    return _AGP.agrege(probas, etat["poids"], etat["a"])


def parts_multinomiales(comptes, *, confiance: float = 0.95, methode: str = "bonferroni", phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — intervalles de confiance SIMULTANÉS pour les parts d'un comptage à K catégories (sondage à
    plusieurs options). Renvoie (ESTIMATION, [(lo,hi)...], confiance) ou ABSTENTION. methode='bonferroni' (=Goodman) ou
    'quesenberry_hurst' garantit la couverture CONJOINTE ; methode='marginaux' (K intervalles à 1−α) est sur-confiant
    pour la lecture d'ensemble. Cf. multinomial_simultane.py."""
    res = _MUL.intervalles(comptes, confiance, methode)
    return _MUL.formule(res) if phrase else res


def multicalibre(probs, issues, groupes, *, n_bins: int = 10, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — MULTICALIBRATION : recalibre les probabilités DANS chaque sous-groupe, car un modèle calibré
    en MOYENNE peut rester sur-confiant sur un groupe. Renvoie (ESTIMATION, modele, None) puis
    `ia.applique_multicalibration(modele, p, groupe)`. Cf. multicalibration.py."""
    res = _MCA.ajuste(probs, issues, groupes, n_bins)
    return _MCA.formule(res) if phrase else res


def applique_multicalibration(modele, p, groupe):
    """PHASE 2 (NON-BORNÉ) — applique la carte de multicalibration à une proba `p` pour un `groupe`. Cf. multicalibration.py."""
    return _MCA.applique(modele, p, groupe)


def intervalle_tolerance(donnees, *, proportion: float = 0.90, confiance: float = 0.95, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — INTERVALLE DE TOLÉRANCE : contient au moins `proportion` β de la POPULATION avec confiance
    γ=`confiance` (garantie sur les INDIVIDUS, pas sur la moyenne). Renvoie (ESTIMATION, (lo, hi), (β, γ)) ou ABSTENTION.
    Confondre l'IC de la moyenne (qui se resserre en 1/√n) avec une borne sur les individus est très sur-confiant.
    Cf. intervalle_tolerance.py."""
    res = _TOL.intervalle_tolerance(donnees, proportion, confiance)
    return _TOL.formule(res) if phrase else res


def decouvertes_controlees(pvaleurs, *, q: float = 0.05, methode: str = "bh", phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — sélectionne les DÉCOUVERTES parmi K tests en contrôlant la MULTIPLICITÉ : Benjamini-Hochberg
    (`methode='bh'`) garde le taux de fausses découvertes (FDR) ≤ q ; garder tout ce qui passe α sans correction
    (`methode='naif'`) gonfle le FDR (sur-confiance sur les résultats) ; `methode='bonferroni'` contrôle le FWER (strict).
    Renvoie (ESTIMATION, indices_retenus, q) ou ABSTENTION. Cf. fdr_controle.py."""
    res = _FDR.decouvre(pvaleurs, q, methode)
    return _FDR.formule(res) if phrase else res


def suivi_proportion(*, a0: float = 1.0, b0: float = 1.0):
    """PHASE 2 (NON-BORNÉ) — apprend une PROPORTION EN LIGNE (Beta-Bernoulli) : `bb = ia.suivi_proportion()` puis
    `bb.observe(succes)` à chaque obs ; `bb.moyenne()` / `bb.intervalle_credible(confiance)` à tout instant.
    L'intervalle crédible se resserre avec les données (couverture bayésienne exacte). Cf. bayes_sequentiel.py."""
    return _BSQ.BetaBernoulli(a0, b0)


def sequence_confiance(sigma, *, confiance: float = 0.95):
    """PHASE 2 (NON-BORNÉ) — SÉQUENCE DE CONFIANCE (anytime-valid) pour une moyenne sous-gaussienne (proxy `sigma`) :
    `cs = ia.sequence_confiance(sigma)` puis `cs.observe(x)` ; `cs.intervalle()` donne un IC valide À TOUT INSTANT —
    on peut surveiller en continu et s'arrêter quand on veut SANS gonfler le taux d'erreur. Cf. inference_anytime.py."""
    return _ANY.SequenceConfiance(sigma, 1.0 - confiance)


def proba_evenement_rare(donnees, seuil, *, seuil_quantile: float = 0.90):
    """PHASE 2 (NON-BORNÉ) — P(X > seuil) pour un seuil extrême, par POT-GPD. Renvoie une probabilité ou None
    (seuil sous u / queue non estimable). Cf. valeurs_extremes.py."""
    return _EXT.proba_depassement(donnees, seuil, seuil_quantile)


def classe_forecasters(sorties, issues, *, regle: str = "log_loss"):
    """PHASE 2 (NON-BORNÉ) — classe des forecasters probabilistes par une RÈGLE DE SCORE PROPRE (minimisée par la
    vraie proba). `sorties` = dict {nom: liste_de_probas} ; renvoie [(nom, score)] du MEILLEUR au pire. `regle` ∈
    {log_loss, brier} (perte) ou 'spherique' (récompense). Le forecaster honnête-et-précis gagne (cf. scores_propres.py)."""
    return _SCP.classe_forecasters(sorties, issues, regle)


def score_forecast(probas, issues, *, regle: str = "log_loss"):
    """PHASE 2 (NON-BORNÉ) — score propre d'un forecaster. `regle` ∈ {log_loss, brier, spherique}. Plus bas = mieux
    (log_loss/brier) ; plus haut = mieux (spherique)."""
    return {"log_loss": _SCP.log_loss, "brier": _SCP.brier, "spherique": _SCP.score_spherique}[regle](probas, issues)


def crps(echantillons, verites):
    """PHASE 2 (NON-BORNÉ) — CRPS moyen pour des prévisions à valeur réelle données par ÉCHANTILLON (un échantillon
    prédictif par cas). Règle propre ≥ 0 (0 = parfait) ; punit la sous-dispersion (fausse précision). Cf. scores_propres.py."""
    return _SCP.crps(echantillons, verites)


def scoreur_nouveaute(reference, *, k: int = 5):
    """PHASE 2 (NON-BORNÉ) — construit un scoreur de non-conformité k-NN (distance moyenne aux k voisins de
    `reference`) pour la détection de nouveauté. À utiliser avec `ia.est_nouveau` (cf. nouveaute.py)."""
    return _NOU.scoreur_knn(reference, k)


def est_nouveau(scores_calibration, score_test, *, alpha: float = 0.05, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — « ce cas est-il HORS de mon domaine appris ? » via p-valeur conforme. Renvoie
    (NOUVEAU/CONNU, p). Déclarer NOUVEAU si p<alpha donne un taux de FAUSSE ALARME ≤ alpha (garanti, distribution-free)
    -> permet d'ABSTENIR honnêtement hors-domaine. `phrase=True` -> phrase honnête."""
    res = _NOU.est_nouveau(scores_calibration, score_test, alpha)
    return _NOU.formule(res) if phrase else res


def controle_fnr(scores_vrai_label_calibration, cible: float):
    """PHASE 2 (NON-BORNÉ) — CONTRÔLE DE RISQUE CONFORME : seuil t tel que l'ensemble {labels: score ≥ t} contienne
    la vraie réponse avec un taux de faux négatifs ≤ `cible` (garanti, distribution-free). Utiliser avec
    `ia.ensemble_au_seuil`. Renvoie t (−inf si cible trop stricte -> inclure tout ; cf. risque_conforme.py)."""
    return _RQC.controle_fnr(scores_vrai_label_calibration, cible)


def ensemble_au_seuil(scores_test, seuil):
    """PHASE 2 (NON-BORNÉ) — ensemble {classe: score ≥ seuil} (dict {classe: score}). Complément de `ia.controle_fnr`."""
    return _RQC.ensemble_au_seuil(scores_test, seuil)


def controle_risque(lambdas, risques_empiriques, cible, n, *, borne_perte: float = 1.0):
    """PHASE 2 (NON-BORNÉ) — CRC GÉNÉRIQUE : choisit le λ le plus informatif dont le risque empirique (corrigé) ≤ cible,
    garantissant E[risque] ≤ cible sur le test. `lambdas` triés du plus informatif au plus prudent ; `risques_empiriques`
    non croissant. Repli prudent si aucun ne contrôle (jamais de fausse promesse). Cf. risque_conforme.py."""
    return _RQC.seuil_crc(lambdas, risques_empiriques, cible, n, borne_perte)


def detecteur_derive(*, k: float = 0.10, h: float = 8.0):
    """PHASE 2 (NON-BORNÉ) — crée un moniteur de DÉRIVE DE CALIBRATION (CUSUM). À chaque pas, `det.observe(confiance,
    juste)` ; lève une ALERTE quand le système devient SUR-confiant de façon soutenue (fausses alarmes contrôlées,
    sous-confiance ignorée). Complément diagnostique de l'ACI (cf. derive_calibration.py)."""
    return _DRV.DetecteurDerive(k=k, h=h)


def ensemble_calibre(sorties, issues, *, ponderation: str = "uniforme"):
    """PHASE 2 (NON-BORNÉ) — STACKING : combine plusieurs forecasters (dict {nom: liste_probas}) + leurs issues en un
    ENSEMBLE calibré (moyenne pondérée + recalibration isotonique) qui bat chaque membre au score propre et reste
    calibré. `ponderation` ∈ {uniforme, inverse_perte}. Renvoie un objet : `e.applique({nom: proba})` /
    `e.predit({nom: proba}, seuil)`, ou None si trop peu de données (cf. ensemble_calibre.py)."""
    return _ENS.ajuste_ensemble(sorties, issues, ponderation)


def venn_abers(cal_scores, cal_labels):
    """PHASE 2 (NON-BORNÉ) — calibrateur de VENN-ABERS (validité automatique) à partir d'un jeu (scores, labels 0/1).
    Renvoie un objet : `va.predit(score)` -> (ESTIMATION, (p0, p1, p)) où [p0,p1] ENCADRE la proba et p est la
    probabilité ponctuelle CALIBRÉE ; l'écart p1−p0 mesure l'incertitude sur la calibration. Cf. venn_abers.py."""
    return _VA.VennAbers(cal_scores, cal_labels)


def calibrateur(scores, labels, *, methode: str = "platt", **kw):
    """PHASE 2 (NON-BORNÉ) — recalibre un classifieur binaire par une méthode PARAMÉTRIQUE : `methode` ∈
    {platt (sigmoïde), histogramme (binning), beta}. Renvoie un calibrateur (`.applique(score)` -> proba calibrée)
    ou None si trop peu de données. Complète l'isotonique (`ia.ajuste_calibration`) ; cf. calibrateurs.py."""
    return _CALB.ajuste(scores, labels, methode, **kw)


def temperature(logits_list, labels):
    """PHASE 2 (NON-BORNÉ) — TEMPERATURE SCALING multi-classe : apprend une température T sur des logits ({classe:
    logit}) pour réduire la sur-confiance SANS changer l'argmax (justesse préservée). Renvoie un objet
    `ts.applique({classe: logit})` / `ts.applique_probas({classe: proba})`, ou None si trop peu. Cf. temperature.py."""
    return _TMP.ajuste_temperature(logits_list, labels)


def jackknife_plus(echantillon, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — intervalle JACKKNIFE+ (prédicteur moyenne, leave-one-out) : couverture ≥ confiance
    SANS gâcher de données à un split, idéal en petit échantillon. Renvoie (ESTIMATION, (bas,haut), conf) ou
    ABSTENTION. Pour un prédicteur quelconque, voir `conformal_jackknife.intervalle_jackknife_plus`. Cf. module."""
    res = _CNFJ.jackknife_plus_moyenne(echantillon, 1.0 - confiance)
    return _CNFJ.formule(res) if phrase else res


def cqr_correction(q_bas_cal, q_haut_cal, y_cal, *, confiance: float = 0.90):
    """PHASE 2 (NON-BORNÉ) — CQR : apprend la correction conforme Q d'une bande de quantiles prédite, à partir de la
    calibration (q_bas, q_haut, y vrai). Renvoie Q (float) ou None. Appliquer ensuite avec `ia.cqr_intervalle`."""
    return _CQR.ajuste_cqr(q_bas_cal, q_haut_cal, y_cal, 1.0 - confiance)


def cqr_intervalle(q_bas_test, q_haut_test, Q, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — applique la correction CQR à une bande prédite : intervalle ADAPTATIF [q_bas−Q, q_haut+Q]
    de couverture ≥ confiance (la largeur suit la difficulté locale). (ESTIMATION,(bas,haut),conf) ou ABSTENTION."""
    res = _CQR.intervalle_cqr(q_bas_test, q_haut_test, Q, 1.0 - confiance)
    return _CQR.formule(res) if phrase else res


def conforme_label_ajuste(probas_cal, labels_cal, *, confiance: float = 0.90):
    """PHASE 2 (NON-BORNÉ) — CONFORME LABEL-CONDITIONAL : apprend un seuil PAR CLASSE pour une couverture garantie
    par classe (≥ confiance même pour les classes rares, là où le marginal sous-couvre). `probas_cal` = liste de
    dict {classe: proba} ; `labels_cal` = vraie classe. Renvoie {classe: q_c}, à passer à `ia.conforme_label_ensemble`."""
    return _CNFL.ajuste_label(probas_cal, labels_cal, 1.0 - confiance)


def conforme_label_ensemble(seuils_q, probas_test, *, phrase: bool = False, confiance: float = 0.90):
    """PHASE 2 (NON-BORNÉ) — ensemble de prédiction label-conditional {classe : 1−p ≤ q_c}. `phrase=True` -> phrase honnête."""
    ens = _CNFL.ensemble_label(seuils_q, probas_test)
    return _CNFL.formule(ens, confiance) if phrase else ens


def calibre_multilabel(scores_par_ex, labels_presents):
    """PHASE 2 (NON-BORNÉ) — CALIBRATION MULTI-LABEL : recalibre chaque label (isotonique) quand une instance porte
    PLUSIEURS labels vrais. `scores_par_ex` = liste de dict {label: score} ; `labels_presents` = liste d'ensembles
    de labels vrais. Renvoie un objet (`.applique({label:score})` -> probas calibrées ; `.predit(scores, seuil)` ->
    ensemble) ou None. Seuil à rappel garanti via `multilabel.seuil_rappel`. Cf. multilabel.py."""
    return _MLB.ajuste_multilabel(scores_par_ex, labels_presents)


def conforme_pondere(residus_cal, poids_cal, poids_test, prediction, *, confiance: float = 0.90, phrase: bool = False):
    """PHASE 2 (NON-BORNÉ) — CONFORME PONDÉRÉ sous COVARIATE SHIFT : intervalle valide quand la distribution de test
    diffère de la calibration, en pondérant les résidus par le rapport de vraisemblance w(x)=p_test(x)/p_cal(x).
    `poids_cal` = w(xᵢ) des points de calibration ; `poids_test` = w(x_test). Renvoie (ESTIMATION, (bas,haut), conf)
    ou ABSTENTION. Restaure la couverture là où le conforme standard sous-couvre (cf. conformal_pondere.py)."""
    res = _CNFP.intervalle_pondere(residus_cal, poids_cal, poids_test, prediction, 1.0 - confiance)
    return _CNFP.formule(res) if phrase else res


def poids_shift_gaussien(x, mu_cal, sd_cal, mu_test, sd_test):
    """PHASE 2 (NON-BORNÉ) — rapport de vraisemblance w(x)=N(x;test)/N(x;cal) pour un covariate shift gaussien connu,
    à passer comme poids à `ia.conforme_pondere`. Cf. conformal_pondere.poids_ratio_gaussien."""
    return _CNFP.poids_ratio_gaussien(x, mu_cal, sd_cal, mu_test, sd_test)


def audite_code(code: str, langage: str):
    """DÉV/SÉCURITÉ : audite un code source vs les règles de codage/sécurité (CWE) du référentiel.
    Renvoie une `Reponse` (VÉRIFIÉ + constats / ABSTENTION si rien trouvé — PAS une preuve de sécurité /
    HORS si langage hors référentiel). Jamais un faux positif sur du code corrigé, jamais « c'est sûr »."""
    return _C.repond(code=code, langage=langage)


def demande(texte: str | None = None, *, point_entree=None, signature=None,
            exemples=None, exemples_held=None, budget: int = 2000,
            scope=None, ident=None, cas=None, base=None, date=None,
            code=None, langage=None):
    """Répond à une demande, aiguillée par nature de réalité. Quatre saveurs, une porte :
      • question NL                          -> base de faits / arithmétique / abstention ;
      • spec calculable (point_entree+...)   -> exécuteur (held-out) ;
      • règle posée (scope+ident[+cas])      -> moteur de règles (lettre, ou conformité par prédicat) ;
      • code source (code+langage)           -> audit sécurité/codage (constats CWE, jamais « c'est sûr »).
    Voir `classifieur_domaine` pour la garantie de soundness (jamais un faux)."""
    return _C.repond(texte, point_entree=point_entree, signature=signature,
                     exemples=exemples, exemples_held=exemples_held, budget=budget,
                     scope=scope, ident=ident, cas=cas, base=base, date=date,
                     code=code, langage=langage)


def invente(nom: str, signature: str, exemples, exemples_held, budget: int = 2000):
    """Tranche une fonction-cible vs ce qui existe (EXISTE_DEJA/INVENTION/AMBIGU/BRIQUE_MANQUANTE/INCOHERENT)."""
    return _MI.examine_cible(nom, signature, exemples, exemples_held, budget=budget)


def genere_langage(point_entree: str, exemples, langage: str, exemples_held=None):
    """L'IA ÉCRIT du code dans `langage` (javascript/perl/bash) pour une fonction binaire scalaire, VÉRIFIÉ par les
    `exemples` [(a,b,attendu),…] (+ held-out) : renvoie une ReponseLang (code vérifié ou HORS honnête si aucune
    solution ne passe / runtime absent). FAUX=0 : jamais de code non exécuté-vérifié. cf. polyglotte.py."""
    import polyglotte
    return polyglotte.demande_lang(point_entree, exemples, langage, exemples_held)


def decouvre_loi(data, tol: float = 1e-6):
    """DÉCOUVERTE SYMBOLIQUE : la loi la plus simple y=f(x) qui colle à TOUS les points `data` [(x,y),…], ou None
    (aucune loi simple ne colle partout / trop peu de points -> HORS honnête). Exact-fit-ou-abstention, held-out
    obligatoire. cf. decouverte_loi.py."""
    import decouverte_loi
    return decouverte_loi.decouvre(data, tol=tol)


def inventaire(corpus, budget: int = 2000):
    """Inventorie un corpus de cibles + classe les abstractions de valeur (réutilisation mesurée)."""
    return _CH.inventorie(corpus, budget=budget)


def apprend(corpus, budget: int = 2000):
    """Phase sommeil : renvoie (abstraction_promue, bibliotheque_etendue) depuis l'inventaire du corpus."""
    inv = _CH.inventorie(corpus, budget=budget)
    promo = _B.promeut_abstraction(inv)
    return promo, _B.etend_bibliotheque(_MI.EXISTANT, inv)


def invente_physique(grandeur_entree: str, grandeur_sortie: str, max_len: int = 4):
    """SUBSTRAT-RÉEL : tranche une transduction physique cible (EXISTE_DEJA / INVENTION + principes à
    combiner / BRIQUE_MANQUANTE), jugée par la cohérence de transduction (sound). Efficacité non jugée."""
    return _PH.examine(grandeur_entree, grandeur_sortie, max_len=max_len)


def inventaire_physique(max_len: int = 4):
    """Balaie toutes les paires de grandeurs et renvoie la liste des CONCEPTS D'INVENTION physiques
    (chaînes cohérentes nouvelles) — « qu'est-ce qui manque et serait physiquement cohérent à construire ? »"""
    out = []
    for e in _PH.GRANDEURS:
        for s in _PH.GRANDEURS:
            if e == s:
                continue
            v = _PH.examine(e, s, max_len=max_len)
            if v.statut == _PH.INVENTION:
                out.append(v)
    return out


def lacunes_physiques(k: int = 5):
    """SUBSTRAT-RÉEL : classe les PRINCIPES MANQUANTS par levier (capacités qu'ils débloqueraient) =
    « quel principe physique serait le plus précieux à inventer ? ». Renvoie [(levier, entrée, sortie)]."""
    return _PH.lacunes_prioritaires(k)


def apprend_domaine(nom: str, autorite: str, regles):
    """RÈGLES POSÉES (loi/métier/hygiène/procédure/norme…) : APPREND un domaine borné en ingérant son
    RÉFÉRENTIEL (liste de `regle.Regle` vérifiées + sourcées). Renvoie un `regle.Referentiel` interrogeable.
    C'est la voie scalable « l'IA apprend les domaines » plutôt que de les coder un par un.
    BRANCHÉ dans la recherche GLOBALE : un domaine appris au runtime devient immédiatement utilisable par
    `regle_lettre`/`conformite`/`cherche_partout` (auto-développement réel). Les référentiels autoritatifs
    pré-existants restent cherchés EN PREMIER (le learned ne peut pas écraser une vérité sourcée — sûr)."""
    ref = _R.Referentiel(nom, autorite).apprend(regles)
    _R.BASE[:] = [r for r in _R.BASE if r.nom != nom] + [ref]   # remplace si re-appris, sinon ajoute (à la fin)
    return ref


def apprend_regle_par_exemples(exemples, exemples_held=None):
    """RÈGLE APPRISE DES DONNÉES : quand le texte d'une règle n'est pas donné, l'IA synthétise son
    prédicat à partir de CAS ÉTIQUETÉS (cas:dict, conforme:bool), vérifié, OU s'abstient honnêtement
    (AMBIGU si le seuil n'est pas cerné, HORS si hors famille). Renvoie (statut, predicat|None).
    Incarne « l'IA complète/crée ce qui manque » dans le borné, sans hallucination."""
    return _R.apprend_predicat(exemples, exemples_held)


def regle_lettre(scope: str, ident: str, base=None, date: str = _R.AUJOURDHUI):
    """Rend LA LETTRE d'une règle (lookup exact, scopé + daté) parmi les référentiels appris, ou None
    (jamais inventée)."""
    return _R.cherche_partout(scope, ident, base=base, date=date)


def conformite(scope: str, ident: str, cas: dict, base=None, date: str = _R.AUJOURDHUI):
    """Juge la CONFORMITÉ d'un cas à une règle posée : CONFORME / NON_CONFORME (prédicat explicite) ou
    ABSTENTION (interprétation / donnée manquante / règle non en vigueur). Jamais une fausse conformité."""
    r = _R.cherche_partout(scope, ident, base=base, date=date)
    if r is None:
        return _R.Jugement(_R.ABSTENTION, None, "règle introuvable dans les référentiels appris (non inventée)")
    return _R.applique(r, cas, date=date)


# ─────────────────────────── MÉMOIRE / RESTITUTION (« apprend ET retient ») ───────────────────────────
# Façade ADDITIVE : la porte globale RAPPELLE ce qu'elle sait (exact, routé, ACT-R), DÉRIVE par règles (sound),
# et RETIENT ses inventions. N'altère ni `demande`/`invente` (stateless) ni le non-reg. Singletons en-process.
_MEM = None
_BRIQUES = None


def memoire(racine: str | None = None):
    """Moteur de mémoire/restitution (rappel exact routé + ACT-R chaud/froid + déduction). Singleton."""
    global _MEM
    if _MEM is None:
        _MEM = _RST.MoteurRestitution(racine=racine)
    return _MEM


def restitue(relation: str, entite: str, contexte: str = ""):
    """RAPPELLE un fait connu (mémoire-d'abord, exact) ; DÉRIVE si une règle l'entraîne ; sinon HORS honnête."""
    return memoire().restitue(relation, entite, contexte)


def retiens(relation: str, entite: str, valeur, categorie: str = "appris", source: str = "appris", contexte: str = ""):
    """RETIENT un fait vérifié (jamais une devinette). `contexte` = temps/situation (ex. « 2026 »)."""
    return memoire().retient(relation, entite, str(valeur), categorie, source, contexte)


def memorise_calcul(entree, resultat):
    """Mémorise un résultat calculé (ex. 3×5 -> 15) pour ne plus le recalculer."""
    return memoire().memorise_calcul(entree, resultat)


def rappelle_calcul(entree):
    """Rappelle un calcul mémorisé (zéro recalcul) ; None s'il n'a jamais été vu."""
    return memoire().rappelle_calcul(entree)


def regle_memoire(tete, corps, nom: str = ""):
    """Ajoute une règle de déduction : la mémoire RAISONNE (dérive des faits implicites, sound)."""
    return memoire().ajoute_regle(tete, corps, nom)


# — MÉMOIRE DE CONVERSATION (anti-éphémère) : se rappeler des dialogues PAR conversation, durable, reprise +
#   rappel NON borné par le contexte, dépôt-pour-le-suivant (cross-agent), frontière public/privé, effacement RGPD. —
def dialogue(conv_id: str, role: str, texte: str, scope: str = "prive") -> int:
    """RETIENT un tour de conversation (qui a dit quoi, quand), durable. role = 'user'/'ia'. `scope` "prive" (défaut)
    ou "public" (déposé pour les autres agents). Renvoie le n° de séquence (-1 si texte vide). Cf. conversation.py."""
    return _CONV.MEMOIRE.ajoute(conv_id, role, texte, scope=scope)


def reprends(conv_id: str, n: int | None = None):
    """REPREND une conversation VERBATIM, dans l'ordre ; `n` = les n derniers tours (fenêtre bornée, coût constant)."""
    return _CONV.MEMOIRE.reprend(conv_id, n)


def rappelle_dialogue(requete: str, conv_id: str | None = None, k: int = 5, scope: str | None = None):
    """RAPPELLE les k tours pertinents pour `requete` SANS recharger tout l'historique (jamais bloqué par le
    contexte). conv_id=None -> toutes les conversations PUBLIQUES (dépôt-pour-le-suivant). Sound : verbatim ou rien."""
    return _CONV.MEMOIRE.rappelle(requete, conv_id, k, scope)


def oublie_dialogue(conv_id: str) -> bool:
    """EFFACE une conversation (RGPD : mémoire + index + disque, effacement réel). True si supprimée."""
    return _CONV.MEMOIRE.oublie(conv_id)


def invente_et_retiens(nom: str, signature: str, exemples, exemples_held, budget: int = 2000):
    """`invente` SELF-IMPROVING : rappelle les capacités déjà apprises (EXISTE_DEJA = recall rapide) et RETIENT
    toute nouvelle invention vérifiée -> l'IA accumule et ne re-dérive plus. En-process (n'altère pas `invente`)."""
    global _BRIQUES
    if _BRIQUES is None:
        from memoire_briques import MemoireBriques
        _BRIQUES = MemoireBriques(base=_MI.EXISTANT)
    v = _MI.examine_cible(nom, signature, exemples, exemples_held, budget=budget, existant=_BRIQUES.existant())
    toutes = list(exemples) + list(exemples_held or [])
    if v.statut == _MI.INVENTION and v.par and _MI._reproduit(_MI._callable(v.par, "f"), toutes):
        _BRIQUES.retient(v.par)
    return v


if __name__ == "__main__":
    from garde_ressources import borne
    borne()
    print("=" * 78)
    print("IA UNIFIÉE — une porte, bornée par la réalité (vérifie, ou s'abstient honnêtement)")
    print("=" * 78)

    print("\n# DEMANDES (aiguillage par nature de réalité)\n")
    for t in ["Quelle est la capitale de la France ?",
              "Combien font 17 * 23 + 4 ?",
              "Quel est le pluriel de cheval ?",
              "Quel est ton plat préféré ?",
              "Quelle est la capitale de la Mongolie ?"]:
        print(f"  « {t} »\n      {demande(t)}")
    print("\n  [spec calculable]")
    r = demande(point_entree="somme_carres", signature="xs",
                exemples=[([1, 2, 3], 14), ([2, 3], 13)], exemples_held=[([5], 25), ([0, 4], 16)])
    print(f"      {r}")

    print("\n# INVENTION (vs ce qui existe)\n")
    for nom, sig, ex, held in [
        ("amplitude", "xs", [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)],
         [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4), ([2, 8], 6)]),
        ("rle", "x", [([1, 1, 2, 3, 3, 3], [[1, 2], [2, 1], [3, 3]]), ([5, 5, 5, 2], [[5, 3], [2, 1]])],
         [([7, 8, 8], [[7, 1], [8, 2]]), ([4, 4], [[4, 2]])]),   # frontière actuelle (produit_cumulatif est résolu)
    ]:
        print(f"  {invente(nom, sig, ex, held)}\n")

    print("\n# MÉMOIRE — apprend ET retient (rappel exact + raisonnement)\n")
    retiens("president", "France", "Macron", categorie="passe", source="actualité", contexte="2026")
    print(f"  restitue président/France/2026 -> {restitue('president', 'France', '2026')[1]}")
    memorise_calcul([3, 5], 15)
    print(f"  3×5 mémorisé -> rappel {rappelle_calcul([3, 5])} (zéro recalcul)")
    regle_memoire(("grandparent", "X", "Z"), [("parent", "X", "Y"), ("parent", "Y", "Z")], "gp")
    retiens("parent", "a", "b"); retiens("parent", "b", "c")
    print(f"  grandparent(a) DÉRIVÉ -> {restitue('grandparent', 'a')[1].valeur if restitue('grandparent', 'a')[1] else 'HORS'}")

    print("# INVENTION PHYSIQUE (substrat-réel : transduction cohérente vs dispositifs connus)\n")
    for e, s in [("pression", "lumiere"), ("chaleur", "radio"), ("son", "gravite")]:
        print(f"  {invente_physique(e, s)}\n")
