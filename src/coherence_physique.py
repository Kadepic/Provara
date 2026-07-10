"""
COHÉRENCE PHYSIQUE — détecteur d'IMPOSSIBILITÉS (mandat Yohan 2026-06-23, inspiré de l'annonce « Coolzy »).

Yohan : « si un climatiseur peut tourner sous 45 W, l'IA peut tourner sous bien moins ». L'ASPIRATION
(légèreté/parcimonie) est juste et déjà un cap du projet ([[project-ia-vision-usb]], activation parcimonieuse).
MAIS la réalité juge, pas le marketing : une clim « 45 W, SANS évacuation, qui rend de l'air FROID et SEC dans
une pièce » VIOLE la thermodynamique (un système fermé ne peut PAS se refroidir net — sans rejet de chaleur
vers un puits extérieur, l'effet net est un RÉCHAUFFEMENT égal à la puissance consommée). Le service que doit
rendre cette IA, ce n'est PAS copier un chiffre magique : c'est SAVOIR JUGER qu'une telle annonce est incohérente.

C'est exactement la frontière que `substrat_physique` laissait ouverte (« on NE juge PAS l'efficacité ni les
magnitudes »). Cette brique ferme ce trou, BORNÉE par deux lois établies :
  • 1er principe (conservation de l'énergie) : pas de création nette d'énergie ; rendement de CONVERSION ≤ 1.
  • 2nd principe (entropie) : pas de travail tiré d'une seule source de chaleur ; rendement d'un moteur
    thermique ≤ Carnot (1 − Tc/Th) ; COP d'une pompe/clim ≤ COP de Carnot ; un système FERMÉ ne se refroidit
    pas net (il faut un puits extérieur).

POSTURE (symétrique de « jamais un faux ») : on n'affirme JAMAIS qu'un dispositif « marche ». On rend :
  • VIOLE         — une LOI précise est enfreinte par la spec DÉCLARÉE (fait vérifiable) + laquelle ;
  • COHERENT_BORNE— aucune violation détectée. CE N'EST PAS une preuve que ça marche (efficacité/faisabilité
    non jugées) — exactement le « RAS » de l'audit de code ;
  • HORS          — spec insuffisante / type inconnu : on ne juge pas à l'aveugle.

Détecteurs CONSERVATEURS : on ne déclare VIOLE que sur une contradiction CERTAINE de la spec donnée
(faux négatif toléré, faux positif INTERDIT). Vérifié en adverse par `valide_coherence_physique.py`.
"""
from __future__ import annotations

VIOLE = "viole"
COHERENT_BORNE = "coherent_borne"
HORS = "hors"

# Lois invoquées (référence lisible).
L1 = "1er principe (conservation de l'énergie)"
L2 = "2nd principe (entropie / Carnot)"
L3 = "2nd principe (travail minimal de séparation / énergie de mélange de Gibbs)"


def _nb(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def juge_dispositif(spec: dict) -> tuple[str, str, str | None]:
    """Juge une spec DÉCLARÉE d'un dispositif. Renvoie (statut, raison, loi|None).

    Clés reconnues (toutes optionnelles, mais il en faut assez pour trancher) :
      type ∈ {conversion, refroidissement, moteur_thermique, pompe_chaleur}
      puissance_entree, puissance_utile   (W, mêmes unités) — pour le bilan d'énergie
      rendement                            (sortie utile / entrée, sans unité)
      cop                                  (chaleur déplacée / travail fourni) pour pompe/clim
      systeme_ferme (bool)                 (clim : aucun rejet vers l'extérieur)
      rejette_chaleur_exterieur (bool)
      t_chaud_K, t_froid_K                 (températures de source, en KELVIN) — pour Carnot
      source_energie_externe (bool)        (un apport déclaré autorise puissance_utile > entrée mesurée)
    """
    if not isinstance(spec, dict):
        return (HORS, "spec absente ou invalide", None)
    t = spec.get("type")
    if t not in ("conversion", "refroidissement", "moteur_thermique", "pompe_chaleur", "dessalement"):
        return (HORS, "type de dispositif inconnu ou non précisé", None)

    pe = spec.get("puissance_entree")
    pu = spec.get("puissance_utile")
    rend = spec.get("rendement")
    src = bool(spec.get("source_energie_externe", False))

    # --- 1er principe : pas de création nette d'énergie (sauf source externe DÉCLARÉE). ---
    # Rendement de CONVERSION > 1 (ou utile > entrée) = over-unity = impossible.
    if not src:
        if _nb(rend) and rend > 1.0 and t in ("conversion", "moteur_thermique"):
            return (VIOLE, f"rendement de conversion déclaré {rend} > 1 : énergie créée nette", L1)
        if _nb(pe) and _nb(pu) and pe > 0 and pu > pe and t in ("conversion", "moteur_thermique"):
            return (VIOLE, f"puissance utile {pu} W > puissance d'entrée {pe} W : énergie créée nette", L1)

    # --- 2nd principe : système fermé ne se refroidit pas net (cas Coolzy). ---
    if t == "refroidissement":
        ferme = spec.get("systeme_ferme")
        rejette = spec.get("rejette_chaleur_exterieur")
        # « refroidir une pièce » sans rejeter la chaleur dehors = impossible : l'effet net est un
        # réchauffement (de la puissance consommée). Il faut un puits extérieur (tuyau/condenseur dehors).
        if ferme is True or rejette is False:
            return (VIOLE,
                    "refroidissement net d'un système fermé sans rejet de chaleur vers l'extérieur : "
                    "l'effet net est un réchauffement (= puissance consommée). Un puits extérieur est requis.",
                    L2)
        # Carnot AUSSI pour le refroidissement : la garde ne doit pas dépendre du `type` déclaré. Si un COP et les
        # deux températures sont donnés, on plafonne au COP de FROID de Carnot = Tc/(Th−Tc) (spécifique au froid).
        thr, tcr = spec.get("t_chaud_K"), spec.get("t_froid_K")
        copr = spec.get("cop")
        if _nb(copr) and _nb(thr) and _nb(tcr) and thr > 0 and tcr > 0 and thr > tcr:
            cop_froid = tcr / (thr - tcr)
            if copr > cop_froid + 1e-9:
                return (VIOLE, f"COP de froid {copr} > COP de Carnot (froid) {round(cop_froid, 3)} "
                               f"(Th={thr} K, Tc={tcr} K)", L2)

    # --- 2nd principe : Carnot (moteur thermique). ---
    th, tc = spec.get("t_chaud_K"), spec.get("t_froid_K")
    if t == "moteur_thermique" and _nb(th) and _nb(tc) and th > 0 and tc > 0:
        if tc >= th:
            return (VIOLE, "source froide ≥ source chaude : aucun travail extractible", L2)
        carnot = 1.0 - tc / th
        if _nb(rend) and rend > carnot + 1e-9:
            return (VIOLE, f"rendement {rend} > limite de Carnot {round(carnot, 4)} "
                           f"(Th={th} K, Tc={tc} K)", L2)

    # --- 2nd principe : COP de Carnot (pompe à chaleur / climatisation réversible). ---
    cop = spec.get("cop")
    if t == "pompe_chaleur" and _nb(th) and _nb(tc) and th > 0 and tc > 0 and th > tc:
        cop_carnot = th / (th - tc)                       # COP de chauffage idéal
        if _nb(cop) and cop > cop_carnot + 1e-9:
            return (VIOLE, f"COP {cop} > COP de Carnot {round(cop_carnot, 3)} "
                           f"(Th={th} K, Tc={tc} K)", L2)

    # --- 2nd principe : dessalement/séparation SOUS le travail minimal (énergie de mélange de Gibbs). ---
    # Le travail réversible minimal pour extraire de l'eau PURE d'une solution vaut, à récupération → 0,
    # la PRESSION OSMOTIQUE de l'alimentation (π = i·C·R·T, van 't Hoff). Toute énergie déclarée SOUS ce
    # plancher est impossible : on ne « démélange » pas pour moins que l'énergie de mélange (l'entropie de
    # mélange baisserait sans travail compensatoire). Plancher CONSERVATEUR (récupération → 0) : le minimum
    # réel d'un procédé à récupération finie ne peut qu'être PLUS grand → aucun faux positif. On accepte π en
    # bar, ou on le calcule depuis (concentration mol/L, facteur de van 't Hoff, température K).
    if t == "dessalement":
        e = spec.get("energie_kWh_par_m3")
        pi_bar = spec.get("osmose_pression_bar")
        if pi_bar is None:
            c = spec.get("concentration_mol_par_L")
            i = spec.get("facteur_vant_hoff", 1.0)
            tk = spec.get("t_K", 298.15)
            if _nb(c) and _nb(i) and _nb(tk) and c > 0 and i > 0 and tk > 0:
                pi_pa = i * (c * 1000.0) * 8.314462618 * tk        # C mol/L → mol/m³ ; π en Pa
                pi_bar = pi_pa / 1e5
        if _nb(e) and _nb(pi_bar) and pi_bar > 0:
            e_min = (pi_bar * 1e5) / 3.6e6                          # π (bar) → J/m³ → kWh/m³
            if e < e_min - 1e-9:
                return (VIOLE, f"énergie déclarée {e} kWh/m³ < travail minimal de séparation "
                               f"{round(e_min, 3)} kWh/m³ (π = {round(pi_bar, 2)} bar, récupération → 0) : "
                               f"séparation sous l'énergie de mélange de Gibbs", L3)

    # --- Drapeaux explicites de pseudo-science (énergie libre / mouvement perpétuel). ---
    if spec.get("mouvement_perpetuel") is True:
        return (VIOLE, "mouvement perpétuel revendiqué : viole la conservation de l'énergie", L1)
    if spec.get("energie_libre") is True:
        return (VIOLE, "« énergie libre » (création d'énergie sans source) revendiquée", L1)

    return (COHERENT_BORNE,
            "aucune violation des lois de conservation/entropie détectée dans la spec DÉCLARÉE — "
            "ce n'est PAS une preuve que le dispositif fonctionne (efficacité/faisabilité non jugées).",
            None)


def explique(statut: str, raison: str, loi: str | None) -> str:
    if statut == VIOLE:
        return f"[IMPOSSIBLE — {loi}] {raison}"
    if statut == COHERENT_BORNE:
        return f"[COHÉRENT (borné)] {raison}"
    return f"[HORS] {raison}"


if __name__ == "__main__":
    cas = [
        ("Coolzy (clim sans évacuation)", {"type": "refroidissement", "systeme_ferme": True,
                                            "puissance_entree": 45}),
        ("clim normale (rejet dehors)", {"type": "refroidissement", "rejette_chaleur_exterieur": True,
                                          "puissance_entree": 800, "cop": 3}),
        ("moteur 60% entre 800K et 300K", {"type": "moteur_thermique", "rendement": 0.60,
                                           "t_chaud_K": 800, "t_froid_K": 300}),         # > Carnot 0.625? non: 0.625 -> ok
        ("moteur 70% entre 800K et 300K", {"type": "moteur_thermique", "rendement": 0.70,
                                           "t_chaud_K": 800, "t_froid_K": 300}),         # > Carnot 0.625 -> VIOLE
        ("convertisseur 120%", {"type": "conversion", "rendement": 1.2}),
        ("PAC COP 12 entre 293/278", {"type": "pompe_chaleur", "cop": 12, "t_chaud_K": 293, "t_froid_K": 278}),
        ("PAC COP 5 (réaliste)", {"type": "pompe_chaleur", "cop": 5, "t_chaud_K": 293, "t_froid_K": 278}),
        ("mouvement perpétuel", {"type": "conversion", "mouvement_perpetuel": True}),
    ]
    for nom, spec in cas:
        st, r, loi = juge_dispositif(spec)
        print(f"{nom:34s} -> {explique(st, r, loi)}")
