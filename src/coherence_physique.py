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

import math

VIOLE = "viole"
COHERENT_BORNE = "coherent_borne"
HORS = "hors"

# Lois invoquées (référence lisible).
L1 = "1er principe (conservation de l'énergie)"
L2 = "2nd principe (entropie / Carnot)"
L3 = "2nd principe (travail minimal de séparation / énergie de mélange de Gibbs)"
L4 = "conservation de la quantité de mouvement (3e loi de Newton) / vitesse d'éjection ≤ c"
L5 = "efficacité lumineuse ≤ 683 lm/W (maximum spectral à 555 nm, rendement radiant 100 %)"
L6 = "limite de Landauer (≥ k·T·ln2 dissipés par bit d'information effacé)"
L7 = "limite de Shannon (débit ≤ B·log₂(1 + S/N))"
L8 = ("limite de Shockley-Queisser (rendement PV ≤ ~33,7 % pour une jonction simple standard sous 1 soleil) ; "
      "plafond ABSOLU = exergie du rayonnement solaire (Landsberg ≈ 93,3 %, Carnot 1 − Ta/Ts)")
L9 = ("électrolyse de l'eau : énergie électrique ≥ ΔG (tension de cellule ≥ E_rev(T) = ΔG(T)/nF, ~1,23 V à 25 °C) ; "
      "énergie TOTALE ≥ ΔH (PCS de H₂, ~285,8 kJ/mol)")

_C_LUMIERE = 299_792_458.0  # m/s
_EFFICACITE_LUM_MAX = 683.0  # lm/W : maximum théorique (monochromatique 555 nm, tout le rayonnement converti)
_K_BOLTZMANN = 1.380649e-23  # J/K
_RENDEMENT_SQ_MONO = 0.337   # limite de Shockley-Queisser (jonction simple standard, AM1.5, 1 soleil, gap ~1,34 eV)
_T_SOLEIL_K = 5778.0         # température de corps noir effective du Soleil (pour le plafond de Carnot solaire)
_DH_EAU = 285.8e3            # J/mol : enthalpie de dissociation de l'eau (PCS de H₂) — plancher 1er principe (énergie totale)
_DG_EAU = 237.1e3            # J/mol : enthalpie libre de Gibbs à 25 °C — travail électrique minimal (2nd principe)
_F_FARADAY = 96485.33        # C/mol ; n = 2 électrons par H₂ -> E_rev standard = ΔG/nF ≈ 1,229 V


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
    if t not in ("conversion", "refroidissement", "moteur_thermique", "pompe_chaleur",
                 "dessalement", "separation", "propulsion", "eclairage", "calcul", "communication",
                 "captation_solaire", "electrolyse"):
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

    # --- 2nd principe : séparation d'un composant DILUÉ sous le travail minimal (généralise L3 au gaz/mélange). ---
    # Le travail réversible minimal pour extraire un composant présent à la fraction molaire x d'un mélange idéal
    # vaut, à la limite diluée (récupération → 0), R·T·ln(1/x) par mole extraite (énergie de mélange). Toute
    # énergie déclarée SOUS ce plancher est impossible : on ne « démélange » pas pour moins que l'énergie de
    # mélange. CONSERVATEUR (récupération → 0) : le minimum réel d'un procédé à récupération finie ne peut
    # qu'être PLUS grand → aucun faux positif. C'est la forme GÉNÉRALE de la loi L3 (le dessalement en est le cas
    # osmotique) : elle borne aussi la capture du CO₂ (x ≈ 4,2e-4 dans l'air), la séparation de gaz, etc.
    if t == "separation":
        x = spec.get("fraction_molaire")
        tk = spec.get("t_K", 298.15)
        e_mol = spec.get("energie_kJ_par_mol")
        if _nb(x) and _nb(tk) and _nb(e_mol) and 0.0 < x < 1.0 and tk > 0:
            w_min_kJ = 8.314462618 * tk * math.log(1.0 / x) / 1000.0     # R·T·ln(1/x), J/mol → kJ/mol
            if e_mol < w_min_kJ - 1e-9:
                return (VIOLE, f"énergie déclarée {e_mol} kJ/mol < travail minimal de séparation "
                               f"{round(w_min_kJ, 3)} kJ/mol (fraction molaire x={x}, récupération → 0) : "
                               f"séparation sous l'énergie de mélange", L3)

    # --- Conservation de la QUANTITÉ DE MOUVEMENT : pas de poussée sans réaction (moteur « réactionless »). ---
    # Pour produire une poussée NETTE, il faut pousser sur QUELQUE CHOSE : éjecter de la masse/du rayonnement,
    # OU s'appuyer sur un milieu externe (air, eau, sol, champ). Une poussée revendiquée en l'ABSENCE des deux
    # (moteur clos dans le vide, type EmDrive/Dean) viole la conservation de la quantité de mouvement. CONSERVATEUR :
    # on ne réfute QUE si la spec déclare explicitement « ni milieu externe, ni éjection » — sinon (info absente,
    # ou l'un des deux présent) on ne tranche pas → jamais un faux positif sur une fusée, un jet, une voile.
    if t == "propulsion":
        milieu = bool(spec.get("milieu_externe", False))
        ejecte = bool(spec.get("ejecte_masse_ou_rayonnement", False))
        poussee = spec.get("poussee_nette", spec.get("poussee_revendiquee"))
        if (poussee is True or (_nb(poussee) and poussee > 0)) and not milieu and not ejecte:
            return (VIOLE, "poussée nette sans milieu externe NI éjection de masse/rayonnement : moteur sans "
                           "réaction — viole la conservation de la quantité de mouvement", L4)
        v = spec.get("vitesse_ejection_m_s")
        if _nb(v) and v > _C_LUMIERE:
            return (VIOLE, f"vitesse d'éjection {v} m/s > c ({_C_LUMIERE:.0f}) : impossible", L4)

    # --- Efficacité lumineuse : ≤ 683 lm/W (maximum spectral à 555 nm). ---
    # L'œil répond au maximum à 555 nm, où 1 W de rayonnement = 683 lm. Aucune source ne peut dépasser 683 lm par
    # watt ÉLECTRIQUE (il faudrait > 100 % de rendement radiant OU une réponse de l'œil > son pic). CONSERVATEUR :
    # on ne réfute qu'au-DELÀ de 683 (le plafond CERTAIN) ; la lumière blanche à bon rendu plafonne plus bas
    # (~300–350 lm/W) mais c'est fonction du spectre — pas une violation, donc jamais réfuté ici.
    if t == "eclairage":
        eff = spec.get("efficacite_lm_par_W")
        if _nb(eff) and eff > _EFFICACITE_LUM_MAX + 1e-9:
            return (VIOLE, f"efficacité lumineuse {eff} lm/W > {_EFFICACITE_LUM_MAX:.0f} lm/W (maximum à 555 nm, "
                           f"rendement radiant 100 %) : impossible", L5)

    # --- Limite de Landauer : effacer un bit dissipe au moins k·T·ln2. ---
    # Effacer un bit d'information (opération LOGIQUEMENT IRRÉVERSIBLE) réduit l'entropie informationnelle et
    # dissipe donc au minimum k·T·ln2 en chaleur (~2,87e-21 J à 300 K). Une machine qui déclare effacer des bits
    # pour MOINS viole ce principe. CONSERVATEUR : ne s'applique qu'à l'énergie déclarée par bit EFFACÉ (le calcul
    # réversible/adiabatique, qui n'efface pas, n'est pas concerné et n'est donc jamais réfuté ici).
    if t == "calcul":
        e_bit = spec.get("energie_par_bit_efface_J")
        tk = spec.get("t_K", 300.0)
        if _nb(e_bit) and _nb(tk) and tk > 0:
            e_min = _K_BOLTZMANN * tk * math.log(2.0)
            if e_bit < e_min * (1.0 - 1e-9):
                return (VIOLE, f"énergie par bit effacé {e_bit} J < limite de Landauer {e_min:.3e} J "
                               f"(k·T·ln2 à {tk} K) : impossible", L6)

    # --- Limite de Shannon : débit ≤ B·log₂(1 + S/N). ---
    # La capacité d'un canal (débit SANS erreur maximal) vaut B·log₂(1 + S/N) : on ne transmet pas d'information
    # plus vite, quel que soit le codage. Un débit revendiqué AU-DESSUS de la capacité (bande passante nulle, ou
    # rapport signal/bruit donné) est impossible. CONSERVATEUR : on ne réfute que si B, S/N ET débit sont donnés
    # et débit > capacité → jamais un faux positif sur un système réel (toujours sous la capacité).
    if t == "communication":
        debit = spec.get("debit_bits_par_s")
        b = spec.get("bande_passante_Hz")
        snr = spec.get("rapport_signal_bruit")
        if _nb(debit) and _nb(b) and _nb(snr) and b >= 0 and snr >= 0:
            capacite = b * math.log2(1.0 + snr)
            if debit > capacite + 1e-6:
                return (VIOLE, f"débit {debit} bit/s > capacité de Shannon {capacite:.4g} bit/s "
                               f"(B={b} Hz, S/N={snr}) : impossible", L7)

    # --- Limite de Shockley-Queisser / plafond thermodynamique du solaire : rendement de conversion borné. ---
    # Deux bornes, toutes deux CONSERVATRICES (faux positif INTERDIT) :
    #  (1) plafond ABSOLU, toute architecture : un convertisseur solaire est un moteur entre le Soleil (Ts ≈ 5778 K)
    #      et l'ambiance (Ta). Son rendement ne peut dépasser le facteur de Carnot 1 − Ta/Ts (borne LÂCHE — la vraie
    #      limite d'exergie du rayonnement, Landsberg ~93,3 %, est encore plus basse). Même le solaire IDÉAL
    #      (jonctions infinies + pleine concentration, ~86 %) reste sous cette borne → jamais de faux positif.
    #  (2) limite de SHOCKLEY-QUEISSER (~33,7 %) : ne vaut QUE pour une cellule à jonction simple en régime STANDARD
    #      (une paire électron-trou par photon, un seul seuil, 1 soleil). Les mécanismes exotiques (multi-excitons,
    #      porteurs chauds, bande intermédiaire) ou la concentration/les tandems la DÉPASSENT légitimement. On ne
    #      réfute donc via SQ que si la spec DÉCLARE ce régime standard (`bilan_detaille_standard`), une jonction
    #      simple et pas de concentration — sinon on ne tranche pas (conservateur).
    if t == "captation_solaire":
        eff = spec.get("rendement")
        if _nb(eff):
            ts = spec.get("t_soleil_K", _T_SOLEIL_K)
            ta = spec.get("t_ambiante_K", 300.0)
            if _nb(ts) and _nb(ta) and ts > 0 and ta > 0 and ta < ts:
                plafond_abs = 1.0 - ta / ts
                if eff > plafond_abs + 1e-9:
                    return (VIOLE, f"rendement solaire {eff} > plafond thermodynamique {round(plafond_abs, 4)} "
                                   f"(Carnot Ts={ts} K, Ta={ta} K) : au-delà de l'exergie du rayonnement solaire", L8)
            jonctions = spec.get("nb_jonctions")
            conc = spec.get("concentration_solaire", 1.0)
            if (spec.get("bilan_detaille_standard") is True and jonctions == 1
                    and _nb(conc) and conc <= 1.0 + 1e-9 and eff > _RENDEMENT_SQ_MONO + 1e-9):
                return (VIOLE, f"rendement {eff} > limite de Shockley-Queisser {_RENDEMENT_SQ_MONO} "
                               f"(jonction simple standard, 1 soleil) : au-delà du bilan détaillé", L8)

    # --- Électrolyse de l'eau : travail électrique ≥ ΔG (tension ≥ E_rev), énergie totale ≥ ΔH (PCS de H₂). ---
    if t == "electrolyse":
        # (1) 1er principe : l'énergie TOTALE par mole de H₂ ≥ ΔH (PCS de H₂) — sinon le H₂ produit restituerait à la
        #     combustion (son PCS = ΔH) PLUS d'énergie qu'il n'en a reçu = création nette. T-indépendant, plancher sûr.
        e_tot = spec.get("energie_kJ_par_mol_H2")
        if _nb(e_tot) and e_tot > 0 and e_tot < _DH_EAU / 1000.0 - 1e-9:
            return (VIOLE, f"énergie totale {e_tot} kJ/mol H₂ < PCS de H₂ {_DH_EAU / 1000:.1f} kJ/mol (ΔH) : "
                           f"le H₂ restituerait plus d'énergie qu'il n'en reçoit (création nette)", L9)
        # (2) 2nd principe : tension de cellule ≥ tension réversible E_rev(T) = ΔG(T)/(nF), ΔG(T) ≈ ΔH − T·ΔS.
        #     CONSERVATEUR : ne vaut QUE si l'anode fait la réaction STANDARD (dégagement d'O₂). L'électrolyse ASSISTÉE
        #     (oxydation sacrificielle d'un composé à l'anode) descend légitimement SOUS E_rev (une autre réaction
        #     fournit l'énergie manquante) → on ne réfute que si `reaction_anodique_standard` est déclaré vrai. Le
        #     modèle E_rev(T) linéaire SOUS-estime le plancher aux hautes températures → un SOEC (E_rev abaissée)
        #     n'est jamais réfuté à tort (faux positif INTERDIT).
        V = spec.get("tension_cellule_V")
        if spec.get("reaction_anodique_standard") is True and _nb(V) and V > 0:
            tk = spec.get("t_K", 298.15)
            if _nb(tk) and tk > 0:
                dS = (_DH_EAU - _DG_EAU) / 298.15
                dG_T = _DH_EAU - tk * dS
                if dG_T > 0:
                    e_rev = dG_T / (2.0 * _F_FARADAY)
                    if V < e_rev - 1e-6:
                        return (VIOLE, f"tension de cellule {V} V < tension réversible {round(e_rev, 3)} V "
                                       f"(ΔG(T)/2F à {tk} K, anode standard O₂) : le fractionnement net de l'eau "
                                       f"ne peut pas se produire", L9)

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
