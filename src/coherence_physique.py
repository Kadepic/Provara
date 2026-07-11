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
L10 = ("vol stationnaire : puissance ≥ puissance induite idéale P = T^1,5 / √(2ρA) (théorie de la quantité de "
       "mouvement / disque actuateur) — un rotor ne peut sustenter une poussée T sur un disque d'aire A pour moins")
L11 = ("limite de diffraction d'Abbe : résolution ≥ λ/(2·NA) en champ lointain conventionnel (super-résolution "
       "exceptée) ; ouverture numérique NA = n·sinθ ≤ n (indice du milieu)")
L12 = ("limite de Betz : une éolienne extrait au plus 16/27 (≈ 59,3 %) de la puissance du vent ½ρAv³ traversant "
       "son disque (rotor ouvert) — on ne peut pas arrêter tout l'air")
L13 = ("équation de Tsiolkovski : Δv ≤ ve·ln(m₀/mf) — le gain de vitesse d'une fusée croît seulement au "
       "logarithme du rapport de masse (le propergol embarqué donne des retours décroissants)")
L14 = ("plafond de rendement photosynthétique : la conversion solaire→biomasse ≤ ~12 % (maximum théorique avant "
       "respiration ; réalisé ~1–6 %) — bornée par la fraction utile du spectre et le rendement quantique")
L15 = ("borne d'entropie (codage de source de Shannon) : une compression SANS PERTE ne descend pas sous l'entropie "
       "H de la source, et aucun compresseur sans perte ne réduit TOUTE entrée (argument de comptage)")
L16 = ("plancher radiatif de Stefan-Boltzmann : pas d'isolant parfait — un objet à T>0 perd au moins "
       "ε·σ·A·(T⁴−T_env⁴) par rayonnement (ε>0), même sans conduction ni convection")
L17 = ("secret parfait de Shannon : une confidentialité PARFAITE (inconditionnelle) exige une entropie de clé ≥ "
       "l'entropie du message (le masque jetable l'atteint) — une clé plus courte ne garantit pas le secret parfait")
L18 = ("traînée induite minimale : produire une portance L à la vitesse V avec une envergure b coûte une traînée "
       "induite ≥ L²/(½ρV²πb²) (efficacité d'envergure ≤ 1) — le coût de la portance décroît en 1/b²")
L19 = ("bruit de grenaille (photonique) : compter N photons donne un rapport signal/bruit ≤ √N (statistique de "
       "Poisson), et le rendement quantique ≤ 1 — sauf lumière comprimée (au-delà de la limite quantique standard)")
L20 = ("un amplificateur n'améliore pas le rapport signal/bruit : facteur de bruit ≥ 1 (NF ≥ 0 dB) — il ajoute "
       "toujours du bruit, jamais n'en retire")
L21 = ("théorème d'échantillonnage de Nyquist-Shannon : reconstruire un signal de bande B exige un échantillonnage "
       "à fs ≥ 2B — en dessous, le repliement est irréversible (sauf signal parcimonieux / acquisition comprimée)")

_C_LUMIERE = 299_792_458.0  # m/s
_EFFICACITE_LUM_MAX = 683.0  # lm/W : maximum théorique (monochromatique 555 nm, tout le rayonnement converti)
_K_BOLTZMANN = 1.380649e-23  # J/K
_RENDEMENT_SQ_MONO = 0.337   # limite de Shockley-Queisser (jonction simple standard, AM1.5, 1 soleil, gap ~1,34 eV)
_T_SOLEIL_K = 5778.0         # température de corps noir effective du Soleil (pour le plafond de Carnot solaire)
_DH_EAU = 285.8e3            # J/mol : enthalpie de dissociation de l'eau (PCS de H₂) — plancher 1er principe (énergie totale)
_DG_EAU = 237.1e3            # J/mol : enthalpie libre de Gibbs à 25 °C — travail électrique minimal (2nd principe)
_F_FARADAY = 96485.33        # C/mol ; n = 2 électrons par H₂ -> E_rev standard = ΔG/nF ≈ 1,229 V
_RHO_AIR = 1.225             # kg/m³ : masse volumique de l'air au niveau de la mer (puissance induite du vol)
_G_TERRE = 9.80665           # m/s² : pesanteur standard (poussée de sustentation = masse × g)
_BETZ = 16.0 / 27.0          # ≈ 0,592593 : fraction maximale de la puissance du vent extractible (rotor ouvert)
_RENDEMENT_PHOTO_MAX = 0.12  # plafond théorique de la conversion solaire->biomasse (réalisé ~1–6 % ; champ ~1–2 %)
_SIGMA_SB = 5.670374419e-8   # W/m²K⁴ : constante de Stefan-Boltzmann (plancher radiatif de l'isolation)


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
                 "captation_solaire", "electrolyse", "sustentation", "imagerie_optique", "eolienne", "fusee",
                 "photosynthese", "compression", "isolation_thermique", "chiffrement", "vol_croisiere",
                 "detection", "amplification", "echantillonnage"):
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

    # --- Vol stationnaire : puissance ≥ puissance induite idéale (théorie de la quantité de mouvement). ---
    # Pour maintenir une poussée T (= poids) en vol stationnaire, un rotor de disque d'aire A dans un fluide de masse
    # volumique ρ délivre au fluide une puissance INDUITE idéale P = T·√(T/(2ρA)) = T^1,5/√(2ρA) (air libre, figure de
    # mérite = 1). CONSERVATEUR (faux positif INTERDIT) : l'EFFET DE SOL réduit la puissance induite (le sol agit comme
    # un rotor-image, aire effective jusqu'à ×2) — plancher absolu = P_ideal/√2, atteint au contact du sol. On ne
    # réfute donc que si la puissance déclarée est SOUS ce plancher indépassable → jamais un faux positif (un aéronef
    # réel, même en plein effet de sol, plane au-dessus). Il faut puissance, poussée (ou masse) ET aire de disque ;
    # la portance STATIQUE (aérostat) n'a pas de disque → non jugée.
    if t == "sustentation":
        a_disk = spec.get("aire_rotor_m2")
        rho = spec.get("rho_air", _RHO_AIR)
        poussee = spec.get("poussee_N")
        if poussee is None:
            m = spec.get("masse_kg")
            if _nb(m) and m > 0:
                poussee = m * _G_TERRE
        p_vol = spec.get("puissance_W")
        if (_nb(p_vol) and p_vol > 0 and _nb(poussee) and poussee > 0
                and _nb(a_disk) and a_disk > 0 and _nb(rho) and rho > 0):
            p_ideal = poussee * math.sqrt(poussee / (2.0 * rho * a_disk))
            p_floor = p_ideal / math.sqrt(2.0)                    # plancher indépassable (effet de sol maximal)
            if p_vol < p_floor * (1.0 - 1e-9):
                return (VIOLE, f"puissance de sustentation {p_vol} W < plancher indépassable {round(p_floor)} W "
                               f"(= puissance induite idéale {round(p_ideal)} W / √2, effet de sol maximal ; "
                               f"quantité de mouvement T^1,5/√(2ρA), T={round(poussee)} N, A={a_disk} m²) : "
                               f"sous le minimum physique du vol stationnaire", L10)

    # --- Limite de diffraction d'Abbe : résolution ≥ λ/(2·NA) (champ lointain conventionnel) ; NA ≤ n. ---
    # Deux volets durs. (1) L'ouverture numérique NA = n·sinθ ne peut dépasser l'indice n du milieu (sinθ ≤ 1). (2)
    # En champ lointain CONVENTIONNEL, on ne résout pas plus fin que la limite d'Abbe λ/(2·NA). La SUPER-RÉSOLUTION
    # (champ proche/NSOM, localisation de molécules uniques PALM/STORM, illumination structurée SIM, déplétion STED)
    # la dépasse LÉGITIMEMENT en exploitant des informations hors du régime d'Abbe → on ne réfute (2) que si la spec
    # NE déclare PAS `super_resolution`. CONSERVATEUR : faux positif INTERDIT (un instrument réel conventionnel reste
    # au-dessus de la limite ; un super-résolu est explicitement exempté).
    if t == "imagerie_optique":
        na = spec.get("ouverture_numerique")
        n = spec.get("indice_milieu", 1.0)
        lam = spec.get("longueur_onde_nm")
        res = spec.get("resolution_nm")
        if _nb(na) and _nb(n) and n > 0 and na > n + 1e-9:
            return (VIOLE, f"ouverture numérique {na} > indice du milieu {n} (NA = n·sinθ ≤ n) : impossible", L11)
        if (spec.get("super_resolution") is not True and _nb(lam) and _nb(na) and _nb(res)
                and lam > 0 and na > 0 and res > 0):
            d_abbe = lam / (2.0 * na)
            if res < d_abbe * (1.0 - 1e-9):
                return (VIOLE, f"résolution {res} nm < limite d'Abbe {round(d_abbe, 1)} nm (λ/2NA, λ={lam} nm, "
                               f"NA={na}, champ lointain conventionnel) : impossible sans super-résolution", L11)

    # --- Limite de Betz : une éolienne extrait au plus 16/27 de la puissance du vent (rotor ouvert). ---
    # On ne peut arrêter tout l'air (il doit continuer à s'écouler) : le rendement d'un disque actuateur dans un
    # flux libre plafonne à 16/27 ≈ 59,3 %. EXCEPTION (patron flag) : une turbine CARÉNÉE / à diffuseur dépasse Betz
    # PAR RAPPORT À L'AIRE DU ROTOR (le diffuseur aspire davantage d'air) — mais pas par rapport à l'aire frontale
    # TOTALE. On ne réfute donc que pour un rotor OUVERT (pas de `avec_diffuseur` déclaré). CONSERVATEUR : une
    # éolienne réelle (Cp ~0,35–0,45) reste bien sous Betz → jamais un faux positif.
    if t == "eolienne":
        ouvert = spec.get("avec_diffuseur") is not True
        cp = spec.get("coefficient_puissance")
        if ouvert and _nb(cp) and cp > _BETZ + 1e-9:
            return (VIOLE, f"coefficient de puissance {cp} > limite de Betz {round(_BETZ, 4)} (16/27, rotor "
                           f"ouvert) : on ne peut extraire plus de 16/27 de la puissance du vent", L12)
        p_ext = spec.get("puissance_W")
        a_bal = spec.get("aire_balayee_m2")
        v_vent = spec.get("vitesse_vent_m_s")
        rho = spec.get("rho_air", _RHO_AIR)
        if (ouvert and _nb(p_ext) and _nb(a_bal) and _nb(v_vent) and _nb(rho)
                and p_ext > 0 and a_bal > 0 and v_vent > 0 and rho > 0):
            p_dispo = 0.5 * rho * a_bal * (v_vent ** 3)
            if p_ext > _BETZ * p_dispo * (1.0 + 1e-9):
                return (VIOLE, f"puissance extraite {p_ext} W > limite de Betz {round(_BETZ * p_dispo)} W "
                               f"(16/27 de ½ρAv³, A={a_bal} m², v={v_vent} m/s, rotor ouvert) : impossible", L12)

    # --- Équation de Tsiolkovski : Δv ≤ ve·ln(m₀/mf) — la « tyrannie de l'équation de la fusée ». ---
    # Le gain de vitesse d'une fusée croît seulement au LOGARITHME du rapport de masse : embarquer plus de propergol
    # donne des retours décroissants. Un Δv revendiqué au-delà de ve·ln(m₀/mf) est impossible AVEC LE PROPERGOL
    # EMBARQUÉ. CONSERVATEUR : on ne réfute que si Δv, vitesse d'éjection ET rapport de masse (ou masses) sont donnés.
    # Le momentum EXTERNE (assistance gravitationnelle, voile solaire, tether) n'est pas borné par ce propergol → une
    # spec sans propergol n'est pas jugée ici (pas de faux positif sur une voile solaire). Distinct de L4.
    if t == "fusee":
        dv = spec.get("delta_v_m_s")
        ve = spec.get("vitesse_ejection_m_s")
        ratio = spec.get("rapport_masse")
        if ratio is None:
            m0 = spec.get("masse_initiale_kg")
            mf = spec.get("masse_finale_kg")
            if _nb(m0) and _nb(mf) and m0 > 0 and mf > 0:
                ratio = m0 / mf
        if _nb(dv) and dv > 0 and _nb(ve) and ve > 0 and _nb(ratio) and ratio >= 1.0:
            dv_max = ve * math.log(ratio)
            if dv > dv_max * (1.0 + 1e-9):
                return (VIOLE, f"Δv {dv} m/s > Δv max de Tsiolkovski {round(dv_max)} m/s (ve·ln(m₀/mf), "
                               f"ve={ve} m/s, rapport de masse {round(ratio, 3)}) : impossible avec ce propergol "
                               f"embarqué", L13)

    # --- Plafond de rendement photosynthétique : la conversion solaire→biomasse ≤ ~12 %. ---
    # La photosynthèse ne convertit qu'une fraction du spectre solaire (PAR) et perd aux étapes quantiques : le
    # maximum THÉORIQUE (avant respiration) est ~12 % ; le réalisé C3/C4 ~4,6–6 %, le champ ~1–2 %. CONSERVATEUR
    # (faux positif INTERDIT) : le plancher de réfutation (12 %) est bien AU-DESSUS du record (~8 % en pointe) → une
    # culture/algue réelle n'est jamais réfutée ; seul un rendement solaire→biomasse déclaré au-delà l'est.
    if t == "photosynthese":
        r = spec.get("rendement_solaire_biomasse")
        if _nb(r) and r > _RENDEMENT_PHOTO_MAX + 1e-9:
            return (VIOLE, f"rendement solaire→biomasse {r} > plafond photosynthétique {_RENDEMENT_PHOTO_MAX} "
                           f"(maximum théorique ; réalisé ~1–6 %) : impossible", L14)

    # --- Borne d'entropie (codage de source de Shannon) : compression sans perte ≥ entropie ; pas d'universel. ---
    # (1) Une compression SANS PERTE ne peut représenter une source à moins de bits/symbole que son entropie H
    #     (théorème du codage de source). (2) Aucun compresseur sans perte ne réduit TOUTE entrée : par comptage
    #     (pigeonnier), si certaines entrées rétrécissent, d'autres doivent grandir. CONSERVATEUR : on ne juge que
    #     le SANS PERTE déclaré (la compression AVEC PERTE descend légitimement sous H en jetant de l'information →
    #     jamais réfutée). Distinct de L7 (capacité de canal). Faux positif INTERDIT.
    if t == "compression":
        if bool(spec.get("sans_perte", False)):
            if spec.get("compresse_toute_entree") is True:
                return (VIOLE, "compression SANS PERTE réduisant TOUTE entrée : impossible (argument de comptage / "
                               "pigeonnier — si certaines entrées rétrécissent, d'autres doivent grandir)", L15)
            h = spec.get("entropie_bits_par_symbole")
            b = spec.get("bits_par_symbole")
            if _nb(h) and _nb(b) and h >= 0 and b < h * (1.0 - 1e-9):
                return (VIOLE, f"débit {b} bits/symbole < entropie {h} bits/symbole (codage de source de Shannon) : "
                               f"compression sans perte sous l'entropie impossible", L15)

    # --- Plancher radiatif de Stefan-Boltzmann : pas d'isolant parfait. ---
    # On peut supprimer la conduction et la convection (vide) mais PAS le rayonnement : un objet à T > T_env perd au
    # moins ε·σ·A·(T⁴−T_env⁴), et aucun matériau réel n'a une émissivité ε nulle. CONSERVATEUR : on ne réfute qu'une
    # perte déclarée SOUS le plancher radiatif de l'émissivité DÉCLARÉE (la conduction/convection ne font qu'ajouter
    # → la perte réelle est toujours ≥ ce plancher) → jamais un faux positif (un thermos réel perd plus que son
    # plancher radiatif). ε ≤ 0 est réfuté d'office (pas d'isolant radiatif parfait).
    if t == "isolation_thermique":
        eps = spec.get("emissivite")
        if _nb(eps) and eps <= 0.0:
            return (VIOLE, f"émissivité {eps} ≤ 0 : aucun matériau réel n'a une émissivité nulle (pas d'isolant "
                           f"radiatif parfait)", L16)
        a_iso = spec.get("aire_m2")
        to = spec.get("t_objet_K")
        te = spec.get("t_env_K")
        perte = spec.get("puissance_perdue_W")
        if (_nb(eps) and _nb(a_iso) and _nb(to) and _nb(te) and _nb(perte)
                and eps > 0 and a_iso > 0 and to > 0 and te > 0 and to > te):
            p_min = eps * _SIGMA_SB * a_iso * (to ** 4 - te ** 4)
            if perte < p_min * (1.0 - 1e-9):
                return (VIOLE, f"perte déclarée {perte} W < plancher radiatif {round(p_min, 3)} W "
                               f"(ε·σ·A·(T⁴−T_env⁴), ε={eps}, A={a_iso} m², {to}→{te} K) : un objet chaud rayonne "
                               f"au moins cela — pas d'isolant parfait", L16)

    # --- Secret parfait de Shannon : confidentialité inconditionnelle ⇒ entropie de clé ≥ entropie du message. ---
    # Une confidentialité PARFAITE (théorie de l'information, inconditionnelle) impose H(clé) ≥ H(message) (Shannon
    # 1949 ; le masque jetable l'atteint, clé = message). Une clé plus courte, ou réutilisée (two-time pad), ne peut
    # garantir le secret parfait. CONSERVATEUR : on ne juge QUE le secret PARFAIT déclaré — la sécurité CALCULATOIRE
    # (AES, RSA), qui ne prétend PAS à l'inconditionnel, n'est jamais réfutée. Faux positif INTERDIT.
    if t == "chiffrement":
        if bool(spec.get("securite_parfaite", False)):
            hk = spec.get("entropie_cle_bits")
            hm = spec.get("entropie_message_bits")
            if _nb(hk) and _nb(hm) and hk >= 0 and hm >= 0 and hk < hm * (1.0 - 1e-9):
                return (VIOLE, f"entropie de clé {hk} bits < entropie du message {hm} bits pour un secret PARFAIT "
                               f"revendiqué : impossible (Shannon 1949 — la clé doit être au moins aussi longue que "
                               f"le message)", L17)

    # --- Traînée induite minimale : produire de la portance coûte au moins L²/(½ρV²πb²). ---
    # Faire de la portance crée un sillage tourbillonnaire : la traînée INDUITE ≥ L²/(½ρV²πb²), atteinte par la
    # distribution elliptique (efficacité d'envergure e = 1) ; toute aile réelle a e < 1 → plus de traînée. On ne
    # descend pas sous ce plancher (e > 1 impossible). CONSERVATEUR : on ne réfute qu'une traînée induite déclarée
    # SOUS le minimum (e=1) ou une efficacité d'envergure > 1 → jamais un faux positif (avion réel toujours au-dessus).
    if t == "vol_croisiere":
        e_env = spec.get("efficacite_envergure")
        if _nb(e_env) and e_env > 1.0 + 1e-9:
            return (VIOLE, f"efficacité d'envergure {e_env} > 1 : impossible (la distribution elliptique e=1 est "
                           f"l'optimum)", L18)
        lift = spec.get("portance_N")
        b_env = spec.get("envergure_m")
        v_cr = spec.get("vitesse_m_s")
        rho = spec.get("rho_air", _RHO_AIR)
        di = spec.get("trainee_induite_N")
        if (_nb(lift) and _nb(b_env) and _nb(v_cr) and _nb(rho) and _nb(di)
                and lift > 0 and b_env > 0 and v_cr > 0 and rho > 0 and di >= 0):
            di_min = (lift * lift) / (0.5 * rho * v_cr * v_cr * math.pi * b_env * b_env)
            if di < di_min * (1.0 - 1e-9):
                return (VIOLE, f"traînée induite {di} N < minimum {round(di_min)} N (L²/(½ρV²πb²), portance "
                               f"{lift} N, envergure {b_env} m, V={v_cr} m/s) : en dessous il faudrait une "
                               f"efficacité d'envergure > 1 — impossible", L18)

    # --- Bruit de grenaille (photonique) : SNR ≤ √N ; rendement quantique ≤ 1. ---
    # La lumière arrive en photons discrets (Poisson) : compter N photons plafonne le rapport signal/bruit à √N
    # (bruit de grenaille), et un photon ne crée pas plus d'un électron compté (QE ≤ 1, hors multiplication). EXCEPTION
    # (flag) : la lumière COMPRIMÉE (squeezed) bat la limite quantique standard en interférométrie (LIGO) → on ne
    # réfute SNR > √N qu'en lumière CLASSIQUE (pas de `lumiere_comprimee`). CONSERVATEUR : un capteur réel reste SOUS
    # √N (bruits additionnels) → jamais un faux positif.
    if t == "detection":
        qe = spec.get("rendement_quantique")
        if _nb(qe) and qe > 1.0 + 1e-9:
            return (VIOLE, f"rendement quantique {qe} > 1 : un photon ne peut compter plus d'un électron (hors "
                           f"multiplication déclarée) — impossible", L19)
        if spec.get("lumiere_comprimee") is not True:
            n = spec.get("nb_photons")
            snr = spec.get("rapport_signal_bruit")
            if _nb(n) and _nb(snr) and n > 0 and snr > math.sqrt(n) * (1.0 + 1e-9):
                return (VIOLE, f"rapport signal/bruit {snr} > √N ({round(math.sqrt(n), 2)}) pour {n} photons : "
                               f"au-delà de la limite de bruit de grenaille (lumière classique) — impossible", L19)

    # --- Un amplificateur n'améliore pas le SNR : facteur de bruit ≥ 1 (NF ≥ 0 dB). ---
    # Amplifier multiplie le signal ET le bruit, et tout amplificateur réel ajoute son propre bruit : le facteur de
    # bruit F = SNR_entrée/SNR_sortie ≥ 1 (NF ≥ 0 dB). Un F < 1 (le dispositif AMÉLIORERAIT le SNR) est impossible.
    # CONSERVATEUR : on ne réfute qu'un F < 1 (ou NF < 0 dB) DÉCLARÉ → jamais un faux positif (même un amplificateur
    # paramétrique idéal atteint F = 1, pas moins ; l'amplification phase-sensible d'UNE quadrature est un cas à part
    # qui ne viole pas F ≥ 1 sur l'information totale).
    if t == "amplification":
        f = spec.get("facteur_de_bruit")
        if _nb(f) and f < 1.0 - 1e-9:
            return (VIOLE, f"facteur de bruit {f} < 1 : un amplificateur n'améliore jamais le rapport signal/bruit "
                           f"(il ajoute du bruit) — impossible", L20)
        nf_db = spec.get("facteur_de_bruit_dB")
        if _nb(nf_db) and nf_db < -1e-9:
            return (VIOLE, f"facteur de bruit {nf_db} dB < 0 dB : un amplificateur n'améliore jamais le rapport "
                           f"signal/bruit — impossible", L20)

    # --- Théorème d'échantillonnage de Nyquist-Shannon : fs ≥ 2B pour une reconstruction parfaite. ---
    # Reconstruire parfaitement un signal de bande B exige un échantillonnage à fs ≥ 2B ; en dessous, le repliement
    # (aliasing) mélange irréversiblement les fréquences. EXCEPTION (flag) : l'acquisition comprimée (compressed
    # sensing) reconstruit un signal PARCIMONIEUX bien sous Nyquist (IRM, radio-astronomie) → on ne réfute fs < 2B
    # que pour une reconstruction PARFAITE déclarée d'un signal NON parcimonieux. CONSERVATEUR : faux positif INTERDIT.
    if t == "echantillonnage":
        if bool(spec.get("reconstruction_parfaite", False)) and spec.get("signal_parcimonieux") is not True:
            b = spec.get("bande_passante_Hz")
            fs = spec.get("frequence_echantillonnage_Hz")
            if _nb(b) and _nb(fs) and b > 0 and fs >= 0 and fs < 2.0 * b * (1.0 - 1e-9):
                return (VIOLE, f"fréquence d'échantillonnage {fs} Hz < 2·B ({2 * b} Hz) pour une reconstruction "
                               f"PARFAITE d'un signal de bande {b} Hz : repliement irréversible (Nyquist-Shannon) — "
                               f"impossible sans parcimonie", L21)

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
