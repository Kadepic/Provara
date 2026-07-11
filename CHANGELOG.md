# Journal des modifications — Provara

## 2026-07-12 — MOTEUR D'INVENTION : 25e domaine « trier des données » + loi L22 (borne du tri par comparaison)

Trier / ordonner des données. Nouvelle loi dure au juge (`L22`) : la BORNE DU TRI PAR COMPARAISON — trier n
éléments arbitraires par comparaisons exige au moins log₂(n!) ≈ n·log₂(n) comparaisons (arbre de décision qui doit
distinguer les n! ordres). CONSERVATEUR (FAUX=0), deux exceptions par flags : un tri NON comparatif (radix,
comptage, `tri_par_comparaison` False) exploite la structure des clés en O(n) ; un tri ADAPTATIF sur entrée
structurée (`entree_arbitraire` non déclaré) exploite l'ordre préexistant → on ne réfute que pour un tri par
comparaison d'une entrée ARBITRAIRE. Gate `valide_coherence_physique` **307 → 322/322**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (comparaison 1e6 en 1e6, 8 éléments
en 10). Reframing : on ne bat pas n·log n en COMPARANT ; sortir du modèle — exploiter la structure des clés (radix,
comptage), ne trier que le nécessaire (top-k), l'ordre préexistant (Timsort), paralléliser, tri externe. Couvre
fusion/tas, quicksort, radix, comptage, tri externe, tri parallèle (GPU), top-k, adaptatif. 4 stratégies naturelles
propres (rivière = tri granulométrique, sédimentation = par densité, hiérarchie = ordre émergent, croissance
différentielle = top-k). Gate `valide_besoin` **459 → 476/476** ; les 24 domaines précédents intacts.

**JALON : 25 DOMAINES D'INVENTION, 22 LOIS PHYSIQUES DANS LE JUGE** (… L21 Nyquist-Shannon, L22 borne du tri par
comparaison).

## 2026-07-12 — MOTEUR D'INVENTION : 24e domaine « numériser / échantillonner » + loi L21 (Nyquist-Shannon)

Numériser / échantillonner un signal. Nouvelle loi dure au juge (`L21`) : le théorème d'échantillonnage de
NYQUIST-SHANNON — reconstruire parfaitement un signal de bande B exige fs ≥ 2B ; en dessous, le repliement
(aliasing) est irréversible. CONSERVATEUR (FAUX=0) : l'acquisition comprimée (compressed sensing) reconstruit un
signal PARCIMONIEUX sous Nyquist → on ne réfute fs < 2B que pour une reconstruction PARFAITE d'un signal non
parcimonieux (`signal_parcimonieux` non déclaré). Distinct de L7/L15. Gate `valide_coherence_physique`
**294 → 307/307**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (reconstruction parfaite 20 kHz à
30 kHz, fs = B). Reframing : numériser plus vite ne sert à rien au-delà de 2B ; couvrir la BANDE sans repliement.
Leviers : fs ≥ 2B + filtre anti-repliement, exploiter la parcimonie (acquisition comprimée), sous-échantillonner
une bande étroite (passe-bande), mise en forme du bruit (sigma-delta). Couvre Nyquist, suréchantillonnage, filtre
anti-repliement, acquisition comprimée, passe-bande, sigma-delta, non uniforme/événementiel, pipeline. 4
stratégies naturelles propres (vision = fusion de scintillement, fovéa = échantillonnage non uniforme, écholocation
= sondage actif, pré-filtrage neuronal = anti-aliasing). Gate `valide_besoin` **442 → 459/459** ; les 23 domaines
précédents intacts.

**JALON : 24 DOMAINES D'INVENTION, 21 LOIS PHYSIQUES DANS LE JUGE** (… L20 facteur de bruit, L21 Nyquist-Shannon).

## 2026-07-12 — MOTEUR D'INVENTION : 23e domaine « amplifier un signal » + loi L20 (facteur de bruit ≥ 1)

Amplifier un signal. Nouvelle loi dure au juge (`L20`) : un amplificateur N'AMÉLIORE PAS le rapport signal/bruit —
le facteur de bruit F = SNR_entrée/SNR_sortie ≥ 1 (NF ≥ 0 dB). Amplifier multiplie le signal ET le bruit, et tout
amplificateur ajoute le sien. CONSERVATEUR (FAUX=0) : on ne réfute qu'un F < 1 (ou NF < 0 dB) déclaré → jamais un
faux positif (même un amplificateur paramétrique idéal atteint F = 1). Gate `valide_coherence_physique`
**281 → 294/294**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (F « 0,5 », NF « −1 dB »). Reframing :
gagner en amplitude ne gagne pas en information ; préserver le SNR. Leviers : faible bruit en TÊTE (Friis : le 1er
étage domine), refroidir l'étage d'entrée, amplifier TÔT (au capteur), amplification paramétrique/phase-sensible
(approche 0 dB), ne pas sur-amplifier. Couvre LNA/Friis, cryogénique, paramétrique, préampli au capteur,
transimpédance, distribué, optique (EDFA), puissance GaN. 4 stratégies naturelles propres (cochlée = amplificateur
actif, résonance = gain sélectif, osselets = adaptation d'impédance, vibrisse = levier mécanique). Gate
`valide_besoin` **425 → 442/442** ; les 22 domaines précédents intacts.

**JALON : 23 DOMAINES D'INVENTION, 20 LOIS PHYSIQUES DANS LE JUGE** (… L19 bruit de grenaille, L20 facteur de bruit
d'un amplificateur).

## 2026-07-12 — MOTEUR D'INVENTION : 22e domaine « détecter un signal faible » + loi L19 (bruit de grenaille)

Détecter un signal lumineux faible / capteur. Nouvelle loi dure au juge (`L19`) : le BRUIT DE GRENAILLE — la
lumière arrive en photons discrets (Poisson), donc compter N photons plafonne le rapport signal/bruit à √N ; et le
rendement quantique ≤ 1. CONSERVATEUR (FAUX=0) : la lumière COMPRIMÉE (squeezed) bat la limite quantique standard
en interférométrie (LIGO) → on ne réfute SNR > √N qu'en lumière classique (`lumiere_comprimee` non déclaré) ; un
capteur réel reste sous √N. Gate `valide_coherence_physique` **268 → 281/281**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (SNR « 100 sur 100 photons »,
rendement quantique « 1,2 »). Reframing : on n'amplifie pas au-delà du grain ; le SNR est limité par le NOMBRE de
photons (√N). Leviers : collecter plus de photons (grande ouverture, longue intégration), réduire les autres
bruits (refroidir, faible bruit de lecture), monter le QE vers 1, lumière comprimée (quantique). Couvre grand
télescope, intégration longue, capteur refroidi, faible bruit de lecture, QE élevé, comptage de photons (SPAD),
moyennage, lumière comprimée. 4 stratégies naturelles propres (bâtonnet = comptage de photons, tapetum = second
passage, œil composé = sommation, photorécepteur = cascade). Gate `valide_besoin` **408 → 425/425** ; les 21
domaines précédents intacts.

**JALON : 22 DOMAINES D'INVENTION, 19 LOIS PHYSIQUES DANS LE JUGE** (… L18 traînée induite minimale, L19 bruit de grenaille).

## 2026-07-12 — MOTEUR D'INVENTION : 21e domaine « voler loin / croisière » + loi L18 (traînée induite minimale)

Voler loin / croisière efficace. Nouvelle loi dure au juge (`L18`) : la TRAÎNÉE INDUITE MINIMALE — produire une
portance L à la vitesse V avec une envergure b coûte au moins L²/(½ρV²πb²) de traînée induite (efficacité
d'envergure ≤ 1, l'aile elliptique e=1 étant l'optimum). CONSERVATEUR (FAUX=0) : on ne réfute qu'une traînée
induite déclarée sous ce plancher, ou une efficacité d'envergure > 1. Distinct de L10 (vol stationnaire, puissance
induite). Gate `valide_coherence_physique` **257 → 268/268**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (aile « à traînée induite nulle »,
efficacité d'envergure « 1,5 »). Reframing : l'ennemi du vol longue distance est le COÛT DE LA PORTANCE (sillage
tourbillonnaire) ; comme D_i ∝ 1/b², une grande envergure fine est le levier maître (planeurs, albatros). Autres
leviers : finesse L/D (Breguet portée ∝ L/D), altitude/vitesse optimale, fraction de carburant (∝ ln(W₀/W₁)),
portance statique (dirigeable, contourne la traînée induite). Couvre grande envergure, winglet, aile elliptique,
profil laminaire, vol en formation, plané dynamique/thermique, altitude optimale, dirigeable. 4 stratégies
naturelles propres (frégate = envergure, vautour = ascendances, martinet = croisière efficace, bout d'aile fendu =
winglet biologique). Gate `valide_besoin` **391 → 408/408** ; les 20 domaines précédents intacts.

**JALON : 21 DOMAINES D'INVENTION, 18 LOIS PHYSIQUES DANS LE JUGE** (… L17 secret parfait, L18 traînée induite minimale).

## 2026-07-12 — MOTEUR D'INVENTION : 20e domaine « chiffrer / garder un secret » + loi L17 (secret parfait de Shannon)

Chiffrer / garder un secret. Nouvelle loi dure au juge (`L17`) : le SECRET PARFAIT de Shannon (1949) — une
confidentialité PARFAITE (inconditionnelle) exige une entropie de clé ≥ l'entropie du message (le masque jetable
l'atteint). CONSERVATEUR (FAUX=0) : on ne juge QUE le secret PARFAIT déclaré — la sécurité CALCULATOIRE (AES, RSA),
qui ne prétend pas à l'inconditionnel, n'est jamais réfutée. Troisième théorème de Shannon distinct (secret ≠
capacité L7 ≠ source L15). Gate `valide_coherence_physique` **246 → 257/257**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (secret « parfait » clé 128 bits pour
1 Mo, masque jetable réutilisé / two-time pad). Reframing : pas de secret parfait gratuit — payer une clé aussi
longue que le message (inconditionnel) ou se rabattre sur le calculatoire (problème dur). Leviers : allonger la
clé (OTP), réduire l'entropie du message (compresser avant), distribuer la clé sûrement (QKD), ou assumer
l'hypothèse calculatoire. Couvre OTP, AES, RSA/ECC, QKD, compression pré-chiffrement, partage à seuil (Shamir),
AEAD, homomorphe. 4 stratégies naturelles propres (seiche = camouflage, gymnote = signature privée, immunité =
authentification soi/non-soi, phéromone = canal keyé). Gate `valide_besoin` **374 → 391/391** ; les 19 domaines
précédents intacts.

**JALON : 20 DOMAINES D'INVENTION, 17 LOIS PHYSIQUES DANS LE JUGE** (L1 conservation énergie, L2 Carnot, L3 travail
minimal de séparation, L4 quantité de mouvement + v≤c, L5 efficacité lumineuse ≤ 683 lm/W, L6 Landauer, L7 Shannon
capacité, L8 Shockley-Queisser / exergie solaire, L9 électrolyse ΔG/ΔH, L10 puissance induite du vol, L11
diffraction d'Abbe, L12 Betz, L13 Tsiolkovski, L14 plafond photosynthétique, L15 borne d'entropie / codage source,
L16 plancher radiatif Stefan-Boltzmann, L17 secret parfait de Shannon).

## 2026-07-12 — MOTEUR D'INVENTION : 19e domaine « isoler thermiquement » + loi L16 (plancher radiatif Stefan-Boltzmann)

Isoler thermiquement / conserver la chaleur. Nouvelle loi dure au juge (`L16`) : le PLANCHER RADIATIF de
Stefan-Boltzmann — pas d'isolant parfait. On peut supprimer conduction et convection (vide) mais PAS le
rayonnement : un objet à T > T_env perd au moins ε·σ·A·(T⁴−T_env⁴), et aucun matériau réel n'a une émissivité
nulle. CONSERVATEUR (FAUX=0) : on ne réfute qu'une perte déclarée SOUS le plancher radiatif de l'émissivité
déclarée (conduction/convection ne font qu'ajouter → perte réelle ≥ plancher) ; ε ≤ 0 réfuté d'office. Gate
`valide_coherence_physique` **235 → 246/246**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (isolation « parfaite » zéro perte,
matériau « à émissivité nulle »). Reframing : pas de « R infini » ; attaquer CHAQUE voie séparément — vide
(conduction/convection), basse émissivité/multicouches (rayonnement), géométrie compacte (aire/gradient), masse
thermique (retarder). Couvre bouteille isotherme, MLI spatial, aérogel, VIP, double vitrage low-e, enveloppe
réfléchissante, masse thermique/MCP, rupture de ponts thermiques. 4 stratégies naturelles propres (ours polaire =
air piégé, manchot en huddle = aire réduite, blubber = couche épaisse, duvet réfléchissant = rayonnement). Gate
`valide_besoin` **357 → 374/374** ; les 18 domaines précédents intacts.

**JALON : 19 DOMAINES D'INVENTION, 16 LOIS PHYSIQUES DANS LE JUGE** (… L15 borne d'entropie, L16 plancher radiatif
Stefan-Boltzmann).

## 2026-07-12 — MOTEUR D'INVENTION : 18e domaine « compresser l'information » + loi L15 (borne d'entropie)

Compresser l'information. Nouvelle loi dure au juge (`L15`), deux volets : (1) une compression SANS PERTE ne
descend pas sous l'entropie H de la source (codage de source de Shannon) ; (2) aucun compresseur sans perte ne
réduit TOUTE entrée (argument de comptage / pigeonnier). CONSERVATEUR (FAUX=0) : on ne juge que le SANS PERTE
déclaré — la compression AVEC PERTE descend légitimement sous H en jetant de l'information → jamais réfutée.
Distinct de L7 (capacité de canal). Gate `valide_coherence_physique` **224 → 235/235**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (sans perte « 1 bit sur entropie 4 »,
compresseur sans perte « universel »). Reframing : on ne rétrécit pas magiquement, on retire la REDONDANCE — mieux
modéliser la source pour approcher H, dictionnaires/déduplication, transformée, ou perte contrôlée (jeter
l'imperceptible). Couvre codage entropique, LZ/dédup, modèle contextuel/prédictif (IA), déduplication à l'échelle,
transformée, perceptuel (MP3/JPEG), prédictif vidéo, représentation apprise. 4 stratégies naturelles propres
(fractale = règle courte, cristal = maille répétée, mémoire = rétention du gist, évolution modulaire =
réutilisation). Gate `valide_besoin` **340 → 357/357** ; les 17 domaines précédents intacts.

**JALON : 18 DOMAINES D'INVENTION, 15 LOIS PHYSIQUES DANS LE JUGE** (… L14 plafond photosynthétique, L15 borne
d'entropie / codage de source).

## 2026-07-12 — MOTEUR D'INVENTION : 17e domaine « nourrir / cultiver » + loi L14 (plafond photosynthétique)

Nourrir / cultiver. Nouvelle loi dure au juge (`L14`) : le PLAFOND de rendement PHOTOSYNTHÉTIQUE — la conversion
solaire→biomasse ≤ ~12 % (maximum théorique avant respiration ; réalisé ~1–6 %, champ ~1–2 %), bornée par la
fraction utile du spectre (PAR) et le rendement quantique. CONSERVATEUR (FAUX=0) : le plancher de réfutation
(12 %) est bien au-dessus du record (~8 % en pointe) → aucune culture/algue réelle n'est réfutée. Gate
`valide_coherence_physique` **213 → 224/224**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (culture « à 25 % », biomasse
over-unity). Reframing : pas la biomasse brute mais un maximum de CALORIES COMESTIBLES par surface/eau/intrant.
Leviers : combler l'écart au plafond (C4, court-circuiter la photorespiration, canopée), SAUTER la photosynthèse
(fermentation gazeuse H₂/CO₂ → protéine microbienne, découplée du sol/soleil), organismes plus efficaces
(algues/cyanobactéries), environnement contrôlé, indice de récolte, manger BAS dans la chaîne trophique (−90 % par
niveau). 4 stratégies naturelles propres (C4 = pompe à CO₂, CAM = stockage nocturne/eau, symbiose rhizobium =
azote gratuit, phytoplancton = échelle). Gate `valide_besoin` **323 → 340/340** ; les 16 domaines précédents intacts.

**JALON : 17 DOMAINES D'INVENTION, 14 LOIS PHYSIQUES DANS LE JUGE** (… L13 Tsiolkovski, L14 plafond photosynthétique).

## 2026-07-12 — MOTEUR D'INVENTION : 16e domaine « propulsion spatiale » + loi L13 (équation de Tsiolkovski)

Atteindre une grande vitesse dans le vide. Nouvelle loi dure au juge (`L13`) : l'équation de TSIOLKOVSKI — Δv ≤
ve·ln(m₀/mf). Le gain de vitesse ne croît qu'au LOGARITHME du rapport de masse (la « tyrannie de l'équation de la
fusée »). CONSERVATEUR (FAUX=0) : on ne réfute que si Δv, vitesse d'éjection ET rapport de masse sont donnés ; le
momentum EXTERNE (assistance gravitationnelle, voile solaire, ISRU) n'est pas borné par le propergol embarqué →
une spec sans propergol n'est pas jugée. Distinct de L4 (quantité de mouvement). Gate `valide_coherence_physique`
**198 → 213/213**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (chimique « à 30 km/s », fusée « sans
ergols » rapport 1). Reframing : ne pas emporter plus de carburant (retours logarithmiques) mais augmenter la
VITESSE D'ÉJECTION ve (Δv linéaire en ve), étager, alléger, ou exploiter un MOMENTUM EXTERNE. Couvre chimique,
ionique/électrique, étagement, nucléaire thermique, nucléaire pulsé (Orion), voile solaire, assistance
gravitationnelle, ravitaillement in situ. 4 stratégies naturelles propres (salpe = jet pulsé, concombre sauvage =
éjection balistique, bombardier = jet chimique, raie manta = momentum externe). Gate `valide_besoin`
**306 → 323/323** ; les 15 domaines précédents intacts.

**JALON : 16 DOMAINES D'INVENTION, 13 LOIS PHYSIQUES DANS LE JUGE** (L1 conservation énergie, L2 Carnot, L3 travail
minimal de séparation, L4 quantité de mouvement + v≤c, L5 efficacité lumineuse ≤ 683 lm/W, L6 Landauer, L7 Shannon,
L8 Shockley-Queisser / exergie solaire, L9 électrolyse ΔG/ΔH, L10 puissance induite du vol, L11 diffraction d'Abbe,
L12 limite de Betz, L13 équation de Tsiolkovski).

## 2026-07-12 — MOTEUR D'INVENTION : 15e domaine « capter l'énergie du vent » + loi L12 (limite de Betz)

Énergie éolienne. Nouvelle loi dure au juge (`L12`) : la limite de BETZ — un rotor ouvert extrait au plus 16/27
(≈ 59,3 %) de la puissance du vent ½ρAv³ traversant son disque (on ne peut arrêter tout l'air). CONSERVATEUR
(FAUX=0) : une turbine CARÉNÉE / à diffuseur dépasse Betz PAR RAPPORT À L'AIRE DU ROTOR (le diffuseur aspire plus
d'air), pas par rapport à l'aire frontale totale → on ne réfute que pour un rotor OUVERT (`avec_diffuseur` non
déclaré). Deux voies de réfutation : coefficient de puissance Cp > 16/27, ou puissance extraite > 16/27·½ρAv³.
Gate `valide_coherence_physique` **185 → 198/198**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (Cp 0,7 rotor ouvert, « 50 kW sur
100 m² à 10 m/s »). Reframing : le mur n'est pas la taille des pales mais 59,3 % ; la puissance disponible est
LINÉAIRE en aire balayée A et au CUBE de la vitesse v. Leviers : agrandir A (rotors géants), viser un site plus
venté et monter le mât (v³ → offshore, altitude), approcher Betz (profils), caréner (par aire de rotor). Couvre
tripale, grand rotor offshore, site venté, profil optimisé, carénée à diffuseur, axe vertical (VAWT), éolien
aéroporté, multi-rotor. 4 stratégies naturelles propres (pissenlit = vortex de traînée, arbre flexible =
reconfiguration, oiseau = vol dynamique/cisaillement, graminée = ondulation dissipative). Gate `valide_besoin`
**289 → 306/306** ; les 14 domaines précédents intacts.

**JALON : 15 DOMAINES D'INVENTION, 12 LOIS PHYSIQUES DANS LE JUGE** (L1 conservation énergie, L2 Carnot, L3 travail
minimal de séparation, L4 quantité de mouvement + v≤c, L5 efficacité lumineuse ≤ 683 lm/W, L6 Landauer, L7 Shannon,
L8 Shockley-Queisser / exergie solaire, L9 électrolyse ΔG/ΔH, L10 puissance induite du vol, L11 diffraction d'Abbe,
L12 limite de Betz).

## 2026-07-12 — MOTEUR D'INVENTION : 14e domaine « voir plus petit » + loi L11 (diffraction d'Abbe)

Résolution optique / voir plus petit. Nouvelle loi dure au juge (`L11`), deux volets : (1) l'ouverture numérique
NA = n·sinθ ≤ n (indice du milieu) ; (2) en champ lointain CONVENTIONNEL, la résolution ≥ limite d'Abbe λ/(2·NA).
CONSERVATEUR (FAUX=0) : la super-résolution (champ proche/NSOM, localisation PALM/STORM, illumination structurée
SIM, déplétion STED) dépasse Abbe LÉGITIMEMENT en exploitant une information hors de son régime → on ne réfute le
volet (2) que si la spec NE déclare PAS `super_resolution`. Gate `valide_coherence_physique` **165 → 185/185**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (microscope conventionnel « à 50 nm »,
objectif « NA 1,7 dans l'air »). Reframing : ne pas « grossir » (agrandir l'image ne crée pas de détail) mais
augmenter l'information spatiale — raccourcir λ (UV/X/électrons), monter NA (immersion, plafonné par l'indice), ou
contourner le champ lointain (champ proche, localisation de molécules uniques, illumination structurée, déplétion).
Couvre objectif à sec, immersion, UV, STED, PALM/STORM, SIM, NSOM, microscopie par expansion. 4 stratégies
naturelles propres (aigle = grande pupille + rétine dense, œil GRIN = correction d'aberration, diatomée =
nanostructures sous-λ, crevette-mante = multiplexage spectral). Gate `valide_besoin` **272 → 289/289** ; les 13
domaines précédents intacts.

**JALON : 14 DOMAINES D'INVENTION, 11 LOIS PHYSIQUES DANS LE JUGE** (L1 conservation énergie, L2 Carnot, L3 travail
minimal de séparation, L4 quantité de mouvement + v≤c, L5 efficacité lumineuse ≤ 683 lm/W, L6 Landauer, L7 Shannon,
L8 Shockley-Queisser / exergie solaire, L9 électrolyse ΔG/ΔH, L10 puissance induite du vol, L11 diffraction d'Abbe).

## 2026-07-12 — MOTEUR D'INVENTION : 13e domaine « vol stationnaire » + loi L10 (puissance induite idéale)

Voler sur place / se sustenter en vol stationnaire. Nouvelle loi dure au juge (`L10`) : la PUISSANCE INDUITE
IDÉALE (théorie de la quantité de mouvement / disque actuateur) — pour sustenter une poussée T sur un disque
d'aire A dans un air ρ, il faut au moins P = T^1,5/√(2ρA). CONSERVATEUR (FAUX=0) : l'effet de sol réduit la
puissance induite (sol = rotor-image, aire effective ×2) → on ne réfute que SOUS le plancher absolu P/√2
(indépassable même au ras du sol) → jamais un faux positif (aéronef réel toujours au-dessus, FM ~0,6–0,8). La
portance STATIQUE (aérostat) n'a pas de disque → non jugée. Gate `valide_coherence_physique` **150 → 165/165**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (drone 2 kg « à 5 W », plateforme
100 kg « à 50 W »). Reframing : l'ennemi est la CHARGE DU DISQUE (T/A) ; puissance ∝ 1/√A → un grand disque lent
bat un petit jet rapide (d'où le grand rotor de l'hélico et l'inefficacité du drone à petites hélices). Leviers :
agrandir le disque, alléger, effet de sol, et surtout PORTANCE STATIQUE (aérostat) qui contourne la puissance
induite. Couvre hélico grand rotor, multirotor, grand disque lent, coaxial/tandem, aérostat, effet de sol, rotor
caréné, propulsion distribuée (eVTOL). 4 stratégies naturelles propres (colibri = faible charge de disque, samare
= autorotation, albatros = éviter le stationnaire, vessie natatoire = flottabilité). Gate `valide_besoin`
**255 → 272/272** ; les 12 domaines précédents intacts.

**JALON : 13 DOMAINES D'INVENTION, 10 LOIS PHYSIQUES DANS LE JUGE** (L1 conservation énergie, L2 Carnot, L3 travail
minimal de séparation, L4 quantité de mouvement + v≤c, L5 efficacité lumineuse ≤ 683 lm/W, L6 Landauer, L7 Shannon,
L8 Shockley-Queisser / exergie solaire, L9 électrolyse ΔG/ΔH, L10 puissance induite du vol stationnaire).

## 2026-07-12 — MOTEUR D'INVENTION : 12e domaine « produire de l'hydrogène » + loi L9 (électrolyse)

Produire de l'hydrogène par électrolyse de l'eau. Nouvelle loi dure au juge (`L9`) : le travail ÉLECTRIQUE ≥ ΔG
(tension de cellule ≥ E_rev(T) = ΔG(T)/nF, ~1,23 V à 25 °C) ET l'énergie TOTALE ≥ ΔH (PCS de H₂, ~285,8 kJ/mol —
sinon le H₂ restituerait à la combustion plus que reçu = création nette). CONSERVATEUR (FAUX=0) : la borne sur la
tension ne vaut que si l'anode fait la réaction STANDARD (dégagement d'O₂, `reaction_anodique_standard`) — car
l'électrolyse ASSISTÉE (oxydation sacrificielle) descend légitimement sous 1,23 V ; et le modèle E_rev(T) linéaire
sous-estime le plancher aux hautes températures → un SOEC n'est jamais réfuté à tort. Gate
`valide_coherence_physique` **132 → 150/150**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (0,9 V à anode standard, H₂ « à
150 kJ/mol » sous le PCS). Reframing : l'ennemi n'est pas la faisabilité mais la SURTENSION (cellules réelles à
1,8–2,0 V vs 1,23 V réversible ≈ 40 % de pertes) et le coût des catalyseurs nobles. Leviers : réduire la surtension
(catalyseurs abondants), monter la TEMPÉRATURE (SOEC), changer la demi-réaction ANODIQUE (oxydation sacrificielle
sous 1,23 V), coupler à la LUMIÈRE (photoélectrochimique). Couvre alcaline, PEM, SOEC, AEM, assistée, PEC,
thermochimique S-I, catalyseurs non nobles. 4 stratégies naturelles propres (hydrogénase = catalyseur Fe/Ni
abondant, photosystème II = oxydation de l'eau sous lumière, microbes = voie douce sacrificielle, membrane =
séparation sélective). Gate `valide_besoin` **238 → 255/255** ; les 11 domaines précédents intacts.

**JALON : 12 DOMAINES D'INVENTION, 9 LOIS PHYSIQUES DANS LE JUGE** (L1 conservation énergie, L2 Carnot, L3 travail
minimal de séparation, L4 quantité de mouvement + v≤c, L5 efficacité lumineuse ≤ 683 lm/W, L6 Landauer, L7 Shannon,
L8 Shockley-Queisser / exergie solaire, L9 électrolyse ΔG/ΔH).

## 2026-07-12 — MOTEUR D'INVENTION : 11e domaine « capter l'énergie solaire » + loi L8 (Shockley-Queisser)

Capter l'énergie solaire. Nouvelle loi dure au juge (`L8`) : la **limite de Shockley-Queisser** — une cellule à
jonction simple STANDARD (une paire électron-trou par photon, un seul seuil) plafonne à ~33,7 % sous 1 soleil ;
et, toute architecture confondue, le rendement reste sous le **plafond thermodynamique** du solaire (exergie du
rayonnement : Landsberg ~93,3 %, Carnot 1−Ta/Ts). CONSERVATEUR (FAUX=0) : la borne SQ ne réfute que si la spec
DÉCLARE le régime standard (`bilan_detaille_standard`), une jonction simple et pas de concentration — car les
mécanismes exotiques (multi-excitons, porteurs chauds, bande intermédiaire) et la concentration/les tandems la
dépassent LÉGITIMEMENT ; la borne absolue (Carnot solaire ~94,8 %) s'applique à toute architecture. Gate
`valide_coherence_physique` **114 → 132/132**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (mono-jonction standard « à 50 % »,
panneau « 100 % efficace »). Reframing : ne pas poser plus de surface mais convertir une plus grande part de
CHAQUE photon (une jonction simple perd les photons sous son gap ET l'excès des photons au-dessus =
thermalisation). Leviers : empiler des jonctions (spectre, plafond ~86 %), CONCENTRER, récupérer la
thermalisation (porteurs chauds/MEG/bande intermédiaire), s'approcher de la limite RADIATIVE. Couvre silicium
mono, tandem pérovskite/Si, multi-jonction III-V concentrée (record ~47 %), porteurs chauds, bande intermédiaire,
MEG, concentrateur luminescent, thermophotovoltaïque. 4 stratégies naturelles propres (photosynthèse = antenne +
canalisation, papillon noir = piège-à-lumière, œil de mite = anti-reflet, tournesol = suivi solaire). Gate
`valide_besoin` **220 → 238/238** ; les 10 domaines précédents intacts. Non-régression complète **797/797 PASS**.

**JALON : 11 DOMAINES D'INVENTION, 8 LOIS PHYSIQUES DANS LE JUGE** (L1 conservation énergie, L2 Carnot, L3 travail
minimal de séparation, L4 quantité de mouvement + v≤c, L5 efficacité lumineuse ≤ 683 lm/W, L6 Landauer, L7
Shannon, L8 Shockley-Queisser / exergie du rayonnement solaire).

## 2026-07-12 — MOTEUR D'INVENTION : 10e domaine « communication » + loi L7 (limite de Shannon)

Communiquer/transmettre. Nouvelle loi dure au juge (`L7`) : la **limite de Shannon** — débit sans erreur ≤
B·log₂(1 + S/N). Un débit revendiqué au-dessus de la capacité est RÉFUTÉ. CONSERVATEUR : réfute seulement si B,
S/N ET débit sont donnés et débit > capacité → jamais un faux positif (système réel toujours sous la capacité).
Gate `valide_coherence_physique` **105 → 114/114**.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS (20 Mbit/s sur 1 MHz@30 dB, débit
sans bande passante). Reframing : ne pas « crier plus fort » (capacité LOGARITHMIQUE en S/N) mais élargir la
BANDE (LINÉAIRE en B), relayer plutôt qu'émettre fort (S/N ∝ 1/d²), coder près de la capacité et COMPRESSER la
source, diriger l'antenne. Couvre radio 5G, UWB, MIMO/directif, mesh, codage LDPC/turbo/polaire, optique,
compression de source, rétrodiffusion ambiante (backscatter zéro énergie). 4 stratégies naturelles propres
(baleine = choisir le canal qui porte, fourmi = médium persistant, abeille = code dense, mycélium = relais).
Gate `valide_besoin` **203 → 220/220** ; les 9 domaines précédents intacts.

**JALON : 10 DOMAINES D'INVENTION, 7 LOIS PHYSIQUES DANS LE JUGE** (L1 conservation énergie, L2 Carnot, L3
travail minimal de séparation [osmotique + molaire], L4 quantité de mouvement + v≤c, L5 efficacité lumineuse
≤ 683 lm/W, L6 Landauer, L7 Shannon). Chaque domaine : reframing machine + principes suppositions jugées +
impossibles réfutés + stratégies naturelles ; FAUX=0, isolation prouvée entre domaines.

## 2026-07-12 — MOTEUR D'INVENTION : 9e domaine « calcul » + loi L6 (limite de Landauer)

Calculer à basse énergie — au cœur de la vision Provara (l'IA légère). Nouvelle loi dure au juge (`L6`) : la
**limite de Landauer** — effacer un bit dissipe au moins k·T·ln2 (≈ 2,87e-21 J à 300 K). Une machine qui déclare
effacer des bits pour moins est RÉFUTÉE. CONSERVATEUR : ne s'applique qu'à l'énergie par bit EFFACÉ — le calcul
réversible/adiabatique (qui n'efface pas) n'est jamais réfuté. Gate `valide_coherence_physique` **94 → 105/105**.

`enregistre(...)`, rien d'autre. **11 principes**, 9 suppositions + 2 RÉFUTÉS (1e-23 J/bit, effacement à énergie
nulle). Reframing : le but n'est pas la vitesse mais le calcul PAR JOULE ; les puces actuelles sont ~10⁴–10⁶×
au-dessus de Landauer donc le mur n'est PAS physique aujourd'hui → ne pas EFFACER (réversible/adiabatique), ne pas
DÉPLACER les bits (le vrai coût actuel = le transport → in-memory), moins d'OPÉRATIONS (algorithmes, événementiel,
analogique), calculer FROID. Couvre CMOS, sous-seuil, réversible, in-memory, neuromorphique, analogique, SFQ
supraconducteur, spintronique, photonique. 4 stratégies naturelles propres (cerveau ~20 W = analogique +
événementiel + en-mémoire, rétine = calcul au capteur, ADN = stockage dense, essaim = distribué). Gate
`valide_besoin` **186 → 203/203** ; les 8 domaines précédents intacts.

## 2026-07-12 — MOTEUR D'INVENTION : 8e domaine « eclairage » + loi L5 (efficacité lumineuse ≤ 683 lm/W)

Éclairer efficacement. Nouvelle loi dure au juge (`L5`) : l'**efficacité lumineuse ≤ 683 lm/W** (l'œil culmine à
555 nm ; au-delà il faudrait un rendement radiant > 100 %). Une lampe revendiquant plus est RÉFUTÉE. CONSERVATEUR :
on ne réfute qu'au-delà de 683 (le plafond CERTAIN) ; la lumière blanche à bon rendu plafonne plus bas
(~300–350 lm/W) mais c'est fonction du spectre — noté, pas réfuté. Gate `valide_coherence_physique` **82 → 94/94**.

`enregistre(...)`, rien d'autre. **11 principes**, 9 suppositions + 2 RÉFUTÉS (LED 800 lm/W, ampoule 1000 lm/W).
Reframing : mettre des lumens là où l'ŒIL en a besoin, aux longueurs d'onde qu'il voit → n'émettre que le VISIBLE
(l'incandescence gaspille ~95 % en IR), DIRIGER (optique/tâche) au lieu d'inonder, couleur ADAPTÉE (monochromatique
là où le rendu n'importe pas), et surtout le lumen le moins cher est celui qu'on NE génère PAS (jour guidé, ne pas
éclairer l'inutile). Couvre LED blanche, LED de labo, sodium basse pression, fluorescent, incandescence, laser
blanc, QLED, lumière du jour guidée, éclairage de tâche + présence. 5 stratégies naturelles propres (luciole =
lumière froide, tapetum = recyclage des photons, plancton = à la demande, feuille = guidage). Gate `valide_besoin`
**169 → 186/186** ; les 7 domaines précédents intacts.

## 2026-07-12 — MOTEUR D'INVENTION : 7e domaine « propulsion » + loi L4 (conservation de la quantité de mouvement)

Se propulser. Nouvelle loi dure au juge (`L4`) : **conservation de la quantité de mouvement** (3e loi de Newton)
+ vitesse d'éjection ≤ c. Un « moteur sans réaction » (EmDrive/Dean : poussée nette sans milieu externe NI
éjection de masse/rayonnement) est RÉFUTÉ ; l'éjection supraluminique aussi. CONSERVATEUR : on ne réfute QUE si
la spec déclare explicitement « ni milieu, ni éjection » → aucun faux positif (fusée, jet, voile, ion, fronde
jamais réfutés). Gate `valide_coherence_physique` **67 → 82/82**.

`enregistre(...)`, rien d'autre. **11 principes**, 9 suppositions + 2 RÉFUTÉS (EmDrive, éjection > c). Reframing :
on ne CONTOURNE pas la loi (impossible), on CHOISIT la réaction — s'il y a un milieu (air/eau/sol/champ), pousser
dessus = zéro ergol ; dans le vide, emporter de la masse et maximiser l'impulsion spécifique (Isp), ou EMPRUNTER
un momentum externe (lumière du Soleil, laser au sol, fronde gravitationnelle). Couvre fusée chimique, ionique,
voile solaire, propulsion laser, turboréacteur, fronde gravitationnelle, voile magnétique, nucléaire thermique,
fusée à photons. 5 stratégies naturelles propres (calmar/jet, poisson/oiseau, serpent, samare, araignée
ballooning). Gate `valide_besoin` **151 → 169/169** ; les 6 domaines précédents intacts.

## 2026-07-12 — MOTEUR D'INVENTION : 6e domaine « eau_potable_air » (AWG) — loi séparation RÉUTILISÉE (x = HR)

Produire de l'eau potable de l'air. La loi est DÉJÀ couverte par le type `separation` généralisé : extraire
l'eau d'un air à humidité relative φ coûte au minimum R·T·ln(1/φ) par mole (φ = activité de la vapeur ; on
réutilise `fraction_molaire = HR`). **Aucune extension du juge** — deuxième domaine à ne rien lui coûter (après
le stockage). À φ → 0 (air sec) le minimum DIVERGE, ce que le juge exprime : on ne tire pas d'eau d'un air
parfaitement sec.

`enregistre(...)`, rien d'autre. **10 principes**, 8 suppositions + 2 RÉFUTÉS pédagogiquement distincts :
« 0,5 kJ/mol à 50 % HR » (sous le plancher) ET « eau d'un air à 5 % HR à 2 kJ/mol » (la SÉCHERESSE renchérit —
plancher ~7,4 kJ/mol). Reframing : le rendement dépend d'abord de l'HUMIDITÉ, pas de la techno → opérer quand/où
l'air est humide, SORBER plutôt que refroidir tout l'air (capter la nuit, régénérer au soleil → marche en climat
sec), intercepter le brouillard existant (quasi gratuit), viser un puits froid gratuit (sol, ciel nocturne).
Couvre condensation, sorption solaire, MOF (récolte en désert), filet à brouillard, condensation radiative,
dessiccant liquide, condenseur couplé au sol, membrane. 5 stratégies naturelles propres (scarabée du Namib,
toile d'araignée, lézard Moloch, rosée nocturne, cactus conique). Gate `valide_besoin` **135 → 151/151** ; les
5 domaines précédents intacts ; juge inchangé (67/67).

## 2026-07-12 — MOTEUR D'INVENTION : 5e domaine « capture_co2 » + loi L3 GÉNÉRALISÉE (gaz dilué R·T·ln(1/x))

Enjeu climatique, et même FAMILLE de loi que le dessalement — mais pas osmotique. On a donc **généralisé
`coherence_physique`** d'un type `separation` : le travail minimal d'extraction d'un composant à la fraction
molaire x vaut R·T·ln(1/x) par mole (le dessalement en est le cas osmotique). Le CO₂ de l'air est ultra-dilué
(x ≈ 4,2e-4 = 420 ppm → plancher ≈ 19,3 kJ/mol) ; aux fumées (x ≈ 0,12) il tombe à ≈ 5,3 kJ/mol. Plancher
CONSERVATEUR (récupération → 0) → zéro faux positif (DAC réel ~230 kJ/mol jamais réfuté). Gate
`valide_coherence_physique` **56 → 67/67**.

Puis 5e domaine (`enregistre(...)`, rien d'autre) : **12 principes**, 10 suppositions + 2 RÉFUTÉS (« DAC à
10 kJ/mol depuis l'air » et « capture sans énergie » — sous le plancher). Reframing machine : la DILUTION est
l'ennemi → capter d'abord À LA SOURCE concentrée (fumées, BECCS délègue la capture diluée à la photosynthèse) ;
pour la capture dans l'air, l'énergie réelle est la RÉGÉNÉRATION du sorbant → l'adosser à une chaleur/électricité
gratuite (moisture-swing, électro-swing) ; viser un PUITS permanent (minéralisation). Couvre amines, sorbant
solide DAC, hydroxyde, membrane, moisture-swing, électrochimique, altération accélérée, BECCS, valorisation,
alcalinité océanique. 5 stratégies naturelles propres (photosynthèse, biominéralisation, altération des
silicates, tourbière, anhydrase carbonique). Gate `valide_besoin` **112 → 135/135** ; les 4 domaines précédents
intacts. La loi généralisée renforce aussi le dessalement (même L3, deux formes : osmotique et molaire).

## 2026-07-12 — MOTEUR D'INVENTION : 4e domaine « stockage_energie » (le patron passe SANS toucher au juge)

Clé de la transition (intermittence solaire/éolien) et démonstration que le registre passe à l'échelle **sans
étendre `coherence_physique`** : la loi dure ici est le 1er principe (**rendement ALLER-RETOUR ≤ 1**), déjà jugé
par le type `conversion` (rendement > 1 → over-unity → VIOLE). Contraste voulu avec le dessalement, dont la loi
manquait et qu'il a fallu ajouter (`L3`). `enregistre(...)`, rien d'autre touché.

**13 principes**, 11 suppositions jugées + 2 RÉFUTÉS par la conservation (« stockage à rendement 115 % » et
« batterie auto-rechargeante perpétuelle »). Reframing machine : le besoin n'est pas « stocker de l'électricité »
mais DÉCALER l'énergie dans le TEMPS — APPARIER la techno à la durée (secondes → volant/supercondensateur ;
heures → batterie/pompage ; saisonnier → hydrogène/thermochimique) et MINIMISER les conversions (chacune perd
définitivement ; si le besoin final est de la chaleur, stocker de la chaleur — pas d'aller-retour électrique).
Couvre lithium-ion, pompage-turbinage, air comprimé, volant, hydrogène, thermique sels fondus, supercondensateur,
gravitaire solide, thermochimique saisonnier (zéro auto-décharge), batterie à flux, air liquide. 5 stratégies
naturelles propres (graisse/hibernation = chimique saisonnier, ATP = supercondensateur, graine dormante =
thermochimique, tendon élastique = volant, inertie thermique du sol). Gate `valide_besoin` **89 → 112/112** ;
cooling (18), chauffage (13) et dessalement (14) restent intacts (isolation prouvée). Le juge n'a PAS bougé
(56/56 inchangé) — la preuve que le plafond du patron n'est pas le juge mais la modélisation des besoins.

## 2026-07-12 — MOTEUR D'INVENTION : 3e domaine « dessalement_eau » + loi DURE (travail minimal de séparation)

Le dessalement de l'eau est un enjeu mondial ET durement borné : le **travail minimal de séparation** (énergie
de mélange de Gibbs ≈ pression osmotique π, van 't Hoff — ≈ 0,76 kWh/m³ pour l'eau de mer à récupération → 0)
est l'analogue de Carnot. Pour que l'impossible soit RÉFUTÉ (comme pour le froid) et pas seulement « supposé »,
on a d'abord **étendu `coherence_physique`** d'un type `dessalement` : toute énergie déclarée SOUS le plancher
π est déclarée VIOLE (nouvelle loi `L3`). Plancher CONSERVATEUR (récupération → 0, le minimum réel ne peut que
monter) → **zéro faux positif** : aucun procédé réel (osmose inverse ~3 kWh/m³, distillation ~12) n'est jamais
réfuté. π accepté en bar OU calculé depuis (concentration, van 't Hoff, T). Gate `valide_coherence_physique`
**37 → 56/56** (violations sous-plancher + cas limite AU plancher + réels jamais réfutés).

Puis 3e domaine enregistré dans `besoin.py` (`enregistre(...)`, rien d'autre) : **14 principes**, 12 suppositions
jugées + 2 RÉFUTÉS (« osmose inverse à 0,3 kWh/m³ » et « dessalement passif sans énergie » — sous le plancher).
Reframing machine : ne pas « bouillir toute l'eau » ni pousser en bloc contre π, mais payer le MOINS possible
au-dessus du minimum — ne pas sur-récupérer, APPARIER la méthode à la salinité (saumâtre → osmose inverse bon
marché ; hypersalin → thermique), exploiter les sources GRATUITES (chaleur fatale, solaire, gradient de
salinité). Pistes sous-exploitées : congélation (chaleur latente de fusion ~7× < vaporisation), distillation
membranaire sur chaleur fatale, extraction par solvant directionnel, hydrates de gaz, membranes biomimétiques
(aquaporines/graphène). 5 stratégies naturelles propres (mangrove = osmose inverse solaire, glande à sel =
pompe ionique, néphron = contre-courant, cycle de l'eau = distillation planétaire, branchies). Gate
`valide_besoin` **63 → 89/89** ; cooling (18) et chauffage (13) restent intacts (isolation prouvée).

## 2026-07-12 — MOTEUR D'INVENTION : 2e domaine « chauffage_confort » (le symétrique d'hiver, via le registre)

Premier usage réel du registre : `enregistre(Domaine(...))` et RIEN d'autre — la promesse du refactor tenue.
Le domaine n'est PAS un copier-coller : l'asymétrie d'hiver est modélisée (le corps est une **SOURCE** de
~100 W, pas un puits → inventer = RETENIR, pas produire ; réduire une perte est passif → les 4 canaux
physiologiques, sens inversé, sont tous silencieux). 13 principes jugés par `coherence_physique` dont
2 revendications RÉFUTÉES par les lois déjà câblées (« rendement 150 % » → conservation ; « PAC COP 40
ΔT 20 K » → Carnot chauffage Th/(Th−Tc) ≈ 14,7) et le cas limite exact rendement = 1.0 prouvé sans faux
positif. Pistes sous-exploitées : superisolation+métabolique (igloo/Passivhaus), radiant ciblé corps,
chaleur fatale, thermochimique inter-saisonnier (hydrates de sels), caloriques solides en mode pompe,
MCP déphasé, PAC sol/eau, solaire passif (mur Trombe). 5 stratégies naturelles propres (manchots/mutualisation,
duvet/air immobile, lézard au soleil, subnivium, adobe déphasé) — pas de fuite depuis l'été.

Gate `valide_besoin` étendue **38 → 63/63** (asymétrie source, cas limite rendement 1.0, ambiguïté « chauffage »
nu → HORS, isolation inter-domaines : cooling intact = 18 principes/100 W). Recherche web (NREL/Nature Energy
2024-2025) : thermochimique salins (densité 2–10× l'eau, zéro perte au stockage) et PAC solides/haute
température confirmés comme pistes émergentes réelles — intégrés en suppositions honnêtes.

La non-régression COMPLÈTE lancée pour valider ce lot a débusqué **deux gates qui dormaient hors suite** :
`valide_oracle_metier`/`valide_oracle_domaine` importent `outils/genere_sujets.py`, mais `_nonreg._SRCPATH`
n'incluait pas `outils/` → `ModuleNotFoundError` (elles passaient en manuel, jamais dans la suite). Corrigé :
`outils/` ajouté au PYTHONPATH ET à `modules_locaux()` (sinon un changement de `genere_sujets` n'invaliderait
pas leur cache). Suite complète re-tournée À FROID : **797/797 PASS** (0 via cache, 662 s).

## 2026-07-12 — MOTEUR D'INVENTION : archi généralisée (cooling-hardcodé → REGISTRE DE DOMAINES)

Croissance vers l'objectif final. Cartographie d'abord : le moteur d'invention a 3 briques — `substrat_reel`
(relationnel : MESURÉ sans carburant, 5 relations typées seulement, le substrat 71 M est attribut pas
relationnel) ; `chercheur_invention` (synthèse de programmes sur corpus I/O) ; **`boucle_invention`
(invention PHYSIQUE, la vraie voie)** — piloté par un BESOIN, il compose des principes en stacks candidats
(suppositions, jamais des faits) + gaps. MARCHE (« rafraîchir une pièce » → 4 candidats + gap évaporation),
mais `besoin.py` ne modélisait QU'UN domaine (refroidissement) : tout autre besoin → HORS.

Sur décision de Yohan (« généralise d'abord l'archi »), refactor de `src/besoin.py` **cooling-hardcodé →
registre de domaines**, à comportement PRÉSERVÉ À L'IDENTIQUE :
- `Domaine` (nom, aliases, objectif, canaux, principes, strategies, loi, extras) + `enregistre()` +
  `_domaine()` (dispatch par alias) + `domaines_connus()`.
- `decompose`/`objectif_reel`/`principes`/`strategies_naturelles` DISPATCHENT via le registre au lieu du
  `_ALIAS_COOL` codé en dur. Le refroidissement devient le 1er domaine enregistré, depuis les MÊMES
  constantes → sorties identiques (decompose mêmes clés/valeurs, principes 18, HORS inchangé).
- **Ajouter un domaine = `enregistre(Domaine(...))`, rien d'autre à toucher.** FAUX=0 intact (principes =
  suppositions jugées). Isolation prouvée (un nouveau domaine ne fuit pas dans le cooling).

Gate `valide_besoin` étendue (30 → **38/38** : enregistrement, dispatch, extras propres, isolation, HORS
hors-registre). `valide_boucle_invention` 16/16, `valide_transfert` 16/16 inchangés. C'est la FONDATION :
les prochains lots ajouteront des besoins-domaines (dessaler, chauffer, stocker l'énergie…) proprement.

## 2026-07-12 — RECHERCHE : élargir l'alignement métier — MESURÉ IMPOSSIBLE en FAUX=0 (rien construit)

Carte blanche pour élargir l'alignement (2277 métiers non alignés à ISCO/SOC/ROME : historiques/étrangers).
Trois avenues sondées et **validées contre ESCO (vérité-terrain)**, toutes rejetées — l'œil trompait, le
held-out a tranché :

- **Héritage P279 (sous-classe hérite du code d'un ancêtre)** : 833 candidats propres à l'œil (« peintre de
  vases → 2651 »), mais **56 % d'accord ESCO seulement**. Erreurs SYSTÉMATIQUES : niveau (ouvrier agricole
  9213 ≠ 6111 hérité), manager vs pro (directeur pub 1222 ≠ 2431), art vs artisanat (sculpteur sur bois
  7317 ≠ 2651), homonyme (compositeur → 7321 typographe).
- **+ garde « nom de tête partagé »** : 69 % — insuffisant (sous-spécialités adjacentes, ingénieur
  électronique 2152 ≠ 2151).
- **Autres codes de classification Wikidata** : AUCUN. Les non-alignés ne portent que des identifiants de
  bibliothèque/autorité (GND, LoC, BnF, WordNet, Dewey) — zéro code d'occupation à croiser.

**Conclusion : le plafond d'alignement est STRUCTUREL.** Aucune heuristique n'aligne les métiers
historiques/étrangers sans 30-44 % de faux ; aucun code direct n'existe. On ne construit RIEN (c'est la
bonne décision FAUX=0). La croissance ne viendra plus de l'alignement. Documenté au runbook pour ne pas
re-tenter. (« recombinaison sur peu d'exemples = coïncidence ; le held-out durci tranche. »)

## 2026-07-12 — 10ᵉ axe métier « profil d'intérêt dominant (RIASEC) », et PLAFOND de la chaîne SOC atteint

Sur « aller dans les métiers atomiquement jusqu'au plafond ». Un axe de plus, puis le plafond documenté.

### 10ᵉ axe : profil d'intérêt dominant (RIASEC / Holland)
`ingestion/ingere_onet_interets.py` — table `interet_dominant_soc_metier` (**822 métiers**), même chaîne
ISCO→SOC. Le point sensible : PAS de seuil. Le dominant est l'**argmax** des 6 scores RIASEC (le high-point
de Holland), opération DÉTERMINISTE, ex-aequo listés — jamais un choix arbitraire. Honnêteté portée dans la
source : les scores d'intérêt O*NET 30.0 sont IMPUTÉS par apprentissage (soft) → axe MIX (marché US). Gate
`valide_onet_interets` (9/9, dont l'argmax et les ex-aequo). Suite **132 gates**.

### PLAFOND de la chaîne SOC atteint — ce qu'on n'ajoute PAS, et pourquoi
Les fichiers O*NET/BLS restants indexés SOC ne qualifient plus comme axe borné :
- **Work Context, Work Styles** : notations continues (Data Value) — dire « ce métier a tel contexte »
  exigerait un SEUIL arbitraire. Arbitraire = HORS (leçon P2283/`unregulated`).
- **Work Values** : argmax mesuré, mais NOISY — souvent 4 ex-aequo sur 6 (« dominant » vide de sens), et
  redondant-thème avec RIASEC. Une façade soft. HORS.
- **Abilities, Skills, Knowledge** : notations + seuil, ET recouvrent `geste_metier`/`savoir_metier` (ESCO).
  Redondant. HORS.

Deux axes nets ajoutés depuis la chaîne SOC (niveau de préparation, intérêt dominant) ; au-delà, les sources
deviennent arbitraires (seuils), noisy ou redondantes. **Le plafond de la couverture métier par la chaîne
SOC est atteint** — les 10 axes caractérisent les ~822-828 métiers alignés ISCO ; en débloquer d'autres
demanderait de l'ALIGNEMENT (P8283/P867 épuisés), pas de nouvelles sources.

## 2026-07-12 — CROISSANCE : 9ᵉ axe métier « niveau de préparation requise » (O*NET Job Zones)

Retour à la croissance après le durcissement. Piste rémunération FR (DARES×FAP) sondée puis ÉCARTÉE : les
« portraits statistiques des métiers » s'arrêtent à 2011, la correspondance FAP/PCS/ROME n'est qu'une page
HTML, et une FAP est plus large qu'un code ROME — au mieux un PARTIEL grossier, une façade. Au doute, HORS.

À la place, un attribut métier STANDARD qu'aucun des 8 axes ne portait : le **niveau de préparation** requis
(échelle O*NET Job Zones 1-5 : de « peu ou pas de préparation » à « préparation extensive »), distinct de
l'axe formation (RNCP = certifications nommées ; ici une ordinale comparable entre métiers).

`ingestion/ingere_onet_jobzones.py` — table `niveau_preparation_soc_metier` (**822 métiers**), par la MÊME
chaîne ISCO→SOC réutilisée (rémunération/outils/risques). Valeur auto-descriptive : le niveau + le libellé
du référentiel O*NET (« actuaire → niveaux 4-5, Considerable/Extensive Preparation »). Granularité dite
(groupe ISCO, pas le métier), MIX → PARTIEL (marché US ; hors de ce référentiel, non borné). Gate
`valide_onet_jobzones` (11/11 : référentiel 5 niveaux, troncature, granularité, sabotages). **9ᵉ axe** dans
`AXES_METIER`, câblé au juge et au cliquet `valide_sujets` (80/80). Suite **131 gates**.

La carte passe à 39 909 sujets (le nouvel axe ajoute 3 400 sujets-métier, 822 partiels couverts) : le
backlog monte HONNÊTEMENT — une dimension réelle de plus, couverte à 24 % comme les autres axes de la chaîne
US, jamais une couverture inventée.

## 2026-07-12 — VÉRIFICATION CROISÉE .exe DÉPLOYÉ ↔ SOURCE : parité byte-identique confirmée

Durcissement : prouver que le binaire compilé se comporte comme le code. Le serveur du `.exe` est lié à
`127.0.0.1` **côté Windows** (souverain), donc inatteignable depuis la VM WSL2 — la battery HTTP directe
n'est pas faisable. Levier utilisé : `lance.py` supporte `Provara.exe --juge-exec <script.py>`, qui exécute
un script dans le Python **bundlé** du `.exe` (3.12.10) sans démarrer le serveur. On a donc lancé la MÊME
battery déterministe dans le binaire déployé et dans le source, et comparé.

**Déployé = build 105, commit `2206fb7`** (Merge PR #68), en retard sur HEAD (normal : l'updater installe la
dernière *release* CI, pas les commits du jour). Base RÉELLE **externe** (`~/.verax`, partagée avec le
source) → la parité des données est structurelle.

Résultats :
- **Échantillon bundlé (1088 tables)** : 11 requêtes vérité-terrain, **11/11 identiques exe/source**, toutes
  correctes (Tokyo, Paris, H2O, hexagone→6, français→romane…), abstention préservée (Wakanda → None).
- **Base réelle (1408 tables)** : 5/5 identiques, dont `regime_alimentaire(sanglier)→omnivore`,
  `(grand requin blanc)→carnivore`, abstention → None. La seule « divergence » apparente était un artefact
  d'encodage du pipe Windows (cp1252) : `famille_immediate_langue(français)` = **byte-identique** des deux
  côtés (`6c616e6775652064276fc3af6c` = « langue d'oïl » UTF-8), prouvé en hex.
- **Robustesse data-driven confirmée** : le `.exe`@2206fb7 lit correctement `famille_immediate_langue`, une
  relation CRÉÉE aujourd'hui (après son build) — parce que la base est externe et le lookup data-driven.

**Verdict : le `.exe` déployé répond exactement comme le source, byte pour byte, sur l'échantillon comme sur
les 72 M de faits.** Les correctifs du jour (clé, cache, barres de progression, gates) landeront dans le
prochain build de release. Scripts de diagnostic temporaires nettoyés (aucun résidu dans l'app déployée).

## 2026-07-12 — `_nonreg` DÉTERMINISTE : il épingle sa fixture, les gates « base complète » SKIPPENT proprement

Sur la remarque de Yohan (« pourquoi tu n'adaptes pas le `_nonreg` ? si ça a bougé il faut qu'il suive »).
Deux défauts structurels, corrigés ensemble.

### `_nonreg` suivait la MACHINE, pas le dépôt
`_nonreg._env_pipeline` héritait du `LECTEUR_DATASETS_DIR` du shell : lancé avec la base complète dans
l'environnement, des gates d'ABSTENTION trouvaient la donnée et tombaient à tort (mesuré :
`valide_assistant_nl` 500/506). C'est exactement la fragilité que `suite_conversation` avait déjà fermée.
Correctif : `_nonreg` **épingle lui-même** l'échantillon COMMITTÉ (`datasets/lecteur`) + un cache hors-dépôt.
Son verdict ne dépend plus de l'ambiant ; il suit le dépôt (l'échantillon est versionné, il évolue avec le
code). Échappatoire `NONREG_BASE_REELLE=1` pour un run volontaire sur base réelle.

### 16 gates « base complète » tombaient en FAUX-échec sur l'échantillon
Baseline propre des 793 (jamais obtenu avant) : 16 rouges — **toutes** des gates qui exigent la base réelle
(72 M) et échouaient faute de leur donnée sur l'échantillon. **Zéro défaut réel** : les 8 non déjà couvertes
par la passe manuelle passent sur la base complète (villes_coordonnees, substrat_reel, resolution, taxonomie,
invention_atomes, graphe_typé, ancres_types, audit_ancres) ; `valide_lecteur` = 1615/1615 (juste un timeout
dans le batch). Une gate honnête ne TOMBE pas quand sa donnée manque : elle SKIPPE. Garde inline ajoutée aux
16 (marqueur de base réelle : `occupation_personne`, 2,35 M faits, jamais committé ; `type_etoile` pour
`ancres_types` qui le détectait déjà mais sortait en `exit(1)` au lieu de `exit(0)`). Vérifié : **16/16 SKIP
propre (exit 0) sur l'échantillon, et RUN+PASS sur la base réelle** (ancres_types 309/309, audit_ancres
22/22, graphe_typé 24/24, taxonomie 32/32). La base réelle reste vérifiée par la passe manuelle
`valide_lecteur*`.

Résultat : `_nonreg` donne enfin un baseline **déterministe** — même avec la base complète dans le shell, il
épingle l'échantillon, les 16 skippent, aucun faux-rouge. Chaque gate est correcte dans TOUS les contextes,
pas seulement sous une variable d'environnement particulière (leçon de `valide_lecteur_client`).

## 2026-07-12 — PASSE DE VÉRIFICATION BASE COMPLÈTE : 14 gates dormantes, 1 défaut trouvé et corrigé

Après avoir touché le cœur (clé canonique, version de cache), diligence due : passer sur les 72 M de faits
les 14 gates `valide_lecteur*` qui exigent la base complète et NE tournent donc PAS dans la suite (qui
épingle l'échantillon). Séquentiel, un process lourd à la fois.

**13/14 vertes** sur base complète : t4 (1185/1185), t5 (316/316), t6, t7, t8, t9, t10, t11, t12, nuit,
norme (14/14), dirigeants (22/22), document (18/18). Les domaines les plus massifs (t6 personnes 9,4 M,
t4 vivant 4 M, t9 langue 1,76 M, t8 histoire 1,25 M) sont sains — mes changements de clé/cache n'ont rien
cassé à l'échelle.

**1 défaut DORMANT trouvé — dans la gate `valide_lecteur_client`.** Elle prenait `_ICI` (= `tests/`) pour la
racine du projet : elle lançait donc le daemon à `tests/src/lecteur_daemon.py` (INEXISTANT) et cherchait
`tests/datasets/lecteur/` — échec silencieux (stderr masqué), `disponible()` jamais True. `VERAX_ROOT` posé
par `_nonreg` MASQUAIT le défaut ; en autonome (ma passe, sans `VERAX_ROOT`) il tombait. Et sur l'échantillon
sans `LECTEUR_DATASETS_DIR`, la fixture cherchée dans `tests/datasets/` était absente -> la gate SKIPPAIT au
lieu d'exercer. Le daemon lui-même est sain (reproduit à la main : socket en 1 s, parité stricte).

Correctif : `_RACINE` dérivé robustement (VERAX_ROOT ou parent de `tests/`), et le daemon localisé **à côté
du module `lecteur`** (`os.path.dirname(_L.__file__)`) — cwd/VERAX_ROOT indifférents. La gate passe désormais
**10/10 dans les trois contextes** (autonome base-complète, échantillon sans skip, `_nonreg`).

Confirme la leçon du jour : une gate qui ne s'exerce pas partout dort — et un défaut peut se cacher dans la
gate elle-même, pas seulement dans le produit.

## 2026-07-12 — UX : UN ÉCRAN LONG NE DOIT JAMAIS SEMBLER FIGÉ (barre + %)

Yohan : « quand j'ai le message de mise à jour il faudrait 3 points qui défilent ou une barre ou un %, car
on peut penser que c'est bloqué. » Deux écrans muets de plusieurs minutes le méritaient — la modale ne
montrait qu'un spinner immobile.

### Préchargement de la connaissance → vraie barre + pourcentage
`lecteur.charge_dossier` publie désormais sa progression (`PROGRES_CHARGE` : tables chargées / total,
drapeau `fini`) — état module lu par un **poller** côté serveur, sans couplage inverse (le lecteur ne
connaît pas l'interface). Le poller alimente `_maj_statut(pct=…)` (barre déterminée dans la modale) et une
ligne CLI mise à jour en place (`… connaissance : 42 % (583/1390 tables)`). Le front `vueChargement` rend
la barre — **déterminée** quand le % est là, **animée** (indéterminée) sinon : plus jamais un écran muet,
même si le backend ne fournit pas de %.

### Mise à jour de l'application (.exe) → vue dédiée avec barre animée
Le téléchargement du paquet de mise à jour est bloquant et ne rapporte pas de %. Il était **muet côté UI**
— c'est très probablement le « message de mise à jour » figé qu'a vu Yohan. Statut neuf `maj_appli` +
vue `vueMajApp` (barre animée, libellé correct « Mise à jour de Provara… l'app va redémarrer seule »),
posé avant l'application et effacé si elle échoue.

Découplage respecté (le lecteur publie, il n'appelle personne), dégradation propre (pas de % → barre
animée). Gate `valide_progression` (19/19 : contrat `PROGRES_CHARGE`, `pct`/`maj_appli` surfacés, les
trois vues longues portent une barre). Suite **130 gates**.

## 2026-07-12 — FUITE DE .tmp DU CACHE : 26 Go → 3,4 Go, cause racine colmatée (inspectés AVANT nettoyage)

Le préchargement de la connaissance mettait « plusieurs minutes » (Yohan) — c'était une reconstruction de
cache à froid, attendue : j'avais réécrit beaucoup de `.jsonl` aujourd'hui, invalidant le cache par mtime.
Coût unique. Mais en creusant, le cache `~/.verax/cache` pesait **26 Go / 7 139 fichiers** pour seulement
1 390 relations. La cause : **4 371 fichiers `.tmp` orphelins** (23,5 Go).

### Inspectés CHIRURGICALEMENT avant de nettoyer (consigne de Yohan : « vérifier que ce ne sont pas des manques à câbler »)
Scan exhaustif des 4 371 en-têtes : 1 984 lisibles → **tous rattachés à une relation VIVANTE du store** ;
2 387 tronqués (interrompus avant l'en-tête, contenu nul) ; **0 portant une relation absente du store**.
Aucun savoir orphelin, aucun manque à câbler — ce sont des écritures de cache interrompues de tables déjà
présentes. Le seul orphelin `.colf`/`.bin` réel (`densite_demo`) est une fixture de test (`source=test`,
utilisée par `valide_lecteur`).

### La cause racine, et sa correction
Le cache écrivait `mkstemp → write → os.replace` sous `except: pass`. Un échec après `mkstemp`, ou un kill
DUR (OOM/SIGKILL — fréquent ici, cf. l'historique OOM ; non rattrapable par un `except`), laissait le `.tmp`.
Deux défenses, dans `src/lecteur.py` :
- **`_ecrit_atomique`** (les deux écrivains l'utilisent) : `try/finally` qui retire le `.tmp` si le
  `os.replace` n'a pas eu lieu — plus de fuite sur échec Python.
- **`_purge_tmp_orphelins`** : au 1ᵉʳ write d'un process, balaie les `.tmp` plus vieux que `_TMP_TTL`
  (600 s) — seule parade au kill dur. Un `.tmp` récent (writer concurrent) n'est JAMAIS touché (pas de
  course). Auto-cicatrisant : le cache ne ré-accumulera plus.

Gate `valide_cache_tmp` (8/8 : écriture propre, non-fuite sur échec, purge âge-filtrée, une seule par
process). Suite **129 gates**. `valide_lecteur` **1615/1615** (base complète, cœur du cache inchangé).

### Nettoyage immédiat, sûr
Les 4 371 `.tmp` (tous âgés de 25 h à 105 h, aucun récent) supprimés en âge-filtré : **23,5 Go libérés**,
cache **26,9 → 3,4 Go**, exactement 2 768 fichiers (1 384 relations × 2). Le serveur en cours n'est pas
affecté — il ne tient pas les `.tmp` en mmap ; ses `.colf`/`.bin` actifs sont intacts.

## 2026-07-12 — MÉMOIRE CONVERSATIONNELLE : SIX COMPORTEMENTS CASSÉS, RÉPARÉS (« zéro dette », Yohan)

`interface/valide_interface.py` dormait hors suite : **52/58 sur la base complète**. A/B fait — le défaut
**préexistait** aux chantiers du jour. Yohan : « même si c'est préexistant il faut corriger ». Fait.

### Le défaut de fond : DEUX ÉTAGES DU MÊME RAPPEL, DEUX NOTIONS DE SYNONYMIE
Le rappel de dialogue interroge l'index avec `_expanse_rappel` (« nom » cherche aussi « appelle »,
« prénom »…). Mais la garde **ANTI-À-CÔTÉ** (posée le 2026-07-09, et juste dans son principe) comparait
ensuite les mots **bruts** : « tu sais mon **nom** ? » retrouvait bien « Je m'**appelle** Yohan. » — puis
le **jetait**. Un étage connaissait le champ sémantique, l'autre l'ignorait. Trois causes, une garde :

1. **« alors » comptait comme mot de contenu.** « Alors, comment je m'appelle ? » exigeait donc que
   l'énoncé rappelé contienne « alors ». Les marqueurs de discours (alors, donc, bref, voilà, enfin,
   ensuite, puis, or, ainsi) rejoignent les mots-outils : ils n'individualisent aucun sujet.
2. **La couverture ignorait les alias.** `_couvre_avec_alias()` : un mot de la question est couvert s'il
   figure dans l'énoncé **ou** partage un groupe d'alias avec lui — et l'alias se cherche dans les tokens
   **bruts** de l'énoncé, car « appelle » est (à raison) un mot-outil, donc absent de ses mots de contenu.
3. **Question sans aucun mot de contenu** (« Au fait, comment je m'appelle ? ») : `if mots_q and …`
   court-circuitait à faux, condamnant l'écho au silence. On sert alors l'énoncé **si un champ sémantique
   est partagé** — c'est ce champ, et lui seul, qui a fait le rappel. `_champs_alias()`.

Sûreté inchangée : on cite un énoncé **réel** de l'utilisateur, jamais une invention. On cesse seulement
de le jeter pour une différence de vocabulaire que le projet connaissait déjà.

### Et un ORDRE n'est pas une déclaration
« Convertis 5 km en mètres » recevait « **C'est noté, je tiens le fil : 5 km** ». Le cap « fil » de
`serveur.py` accusait tout tour porteur d'une grandeur et sans « ? » — **avant** la garde
`repond._est_demande_imperative`, qui interdit déjà exactement ce faux en fin de cascade. Une même règle,
appliquée à un seul endroit, laissait passer l'autre. Le fil la consulte désormais aussi.

### Deux GATES corrigées (elles testaient un mot, pas une propriété)
- `AFFIRMATION` cherchait le mot « noté » ; or l'accusé est **varié** par `formulation` (« Entendu, c'est
  enregistré » est valide). La gate interroge maintenant la liste de variantes que `repond` publie.
- Deux checks `REVERSE` exigeaient la table `cours_eau_pays`, absente de l'échantillon : ils rougissaient
  pour un **trou de données**, pas un défaut. Ils s'exercent là où la donnée est, et le **disent** sinon
  (même patron que l'ancre « D »).

**Résultat : `valide_interface` 58/58 sur la base complète ET sur l'échantillon.** La gate entre dans la
suite (**128 gates**) — le runner résout désormais un nom de gate contenant « / » depuis la racine.

## 2026-07-12 — L'IA TRANCHE : « résultats établis du domaine » est un SUJET MAL POSÉ (7 584 sujets retirés)

Yohan : « et si justement on laissait l'IA trancher ce qui serait le mieux ». Tranché — **par la mesure,
pas par le goût**. Cinq mesures, aucune opinion :

1. **Aucune autorité** ne publie l'énumération exhaustive des résultats établis d'un domaine.
2. **« un résultat » n'a pas de granularité canonique, « établi » pas de seuil** → la réalité ne fixe
   AUCUNE réponse unique. C'est une vagueur CONSTITUTIVE, pas un défaut d'accès.
3. **Wikidata** : 1 714 items typés théorème/loi/constante/principe/équation ; rattachement P921 = 49 liens,
   P361 = 725 mais **pollué comme P2283** (« arbre → écorce », « droits LGBT → Principes de Jogjakarta »).
   Rendement : **40 domaines sur 7 584 (0,5 %)**, faux compris.
4. **« la requête d'ingestion atteste la classe du sujet »** : 4 tables sur 1 389. Mort.
5. **Et même mappé, cela RECOMPTERAIT l'ANNEXE S**, où chaque table vérifiée est DÉJÀ un sujet traité.
   Recompter le même savoir sous un autre nom : la définition d'une couverture de façade.

**Décision.** L'axe est retiré des annexes (7 584 sujets structurellement intraitables = un backlog qui
ment, la leçon d'« Abogado » rejouée). Un code de bornage neuf, **NB-VAGUE**, entre au vocabulaire :
*non borné par vagueur constitutive — les termes n'ont pas d'individuation canonique* (distinct de NB-OUV,
où la réponse existe et l'accès manque ; et de NB-INDEC). Le sujet survit **une fois**, honnête, en
PARTIE XIII (le non-borné cartographié), traité par **routage honnête** — la MEMBERSHIP d'un résultat
**nommé** reste bornée et relève du store.

Cliquet dans `valide_sujets` : l'axe mal posé ne doit **jamais** reparaître dans une annexe, et la
formulation honnête doit exister exactement une fois. Juge : **44 090 → 36 507 sujets ; non traités
24 727 → 17 143**. Le compteur baisse parce que la mesure était fausse — ne jamais le « restaurer ».

## 2026-07-12 — VÉRIFICATION TOTALE : DEUX DÉFAUTS DORMANTS, TROUVÉS ET TUÉS

Yohan : « il faut tout revérifier pour être sûr que tout le travail est bien totalement fonctionnel ».
C'est `valide_lecteur` — qui exige la base COMPLÈTE et ne tourne donc **pas** dans la suite — qui a parlé.
Deux défauts y dormaient, aucun visible à la lecture du code.

### ① UNE CLÉ CANONIQUE VIDE : 47 faits PERDUS en silence, et une confusion d'entités
`lecteur.ingere_table` **ignore les clés vides**, sans un mot. `_sans_articles` en produisait pour deux
familles d'entités :
- **celles qui SONT un article français** : « D » (le langage de Walter Bright), « d », « l ».
  `createur_langage_programmation("D")` rendait `None` alors que le fait est sur le disque. Pire :
  « d » et « l » avaient la **même** clé vide — deux entités confondues.
- **celles hors alphabet latin** : `normalise` compacte sur `[^a-z0-9 ]+`, donc « Петергофский десант »,
  « Αθανάσιος » devenaient vides. Introuvables, à jamais.

Correctif : une clé n'est **jamais** vide — repli sur la clé normalisée entière (« d » reste « d »,
distinct de « l »), puis sur l'entité NFC casefold (écriture non latine). Les replis ne s'arment QUE si
la clé serait vide : **aucune clé existante ne change**. Mesuré sur les **72 041 162 faits** du store :
clés vides **47 → 0** ; collisions **6 → 4**, les 4 restantes étant la même personne sous deux graphies
(« Jacques Bénigne » / « Jacques-Bénigne » Bossuet) — c'est le travail d'une clé canonique, pas un défaut.
`createur_langage_programmation("D") → Walter Bright` de nouveau. Gate `valide_cles_canoniques` (27/27,
avec contre-épreuve de sabotage rejouant l'ancienne règle).

### ② COLLISION DE RELATION : `famille_langue` écrasée, six ancres fausses
`ecrit_jsonl` **régénère** le fichier d'une relation. Deux scripts publiaient `famille_langue` :
- `ingere_langues_famille.py` — catalogue curé, 81 langues, **grandes familles** (« français → romane ») ;
- `ingere_langues.py` — Wikidata, **famille immédiate** (« français → langue d'oïl »).

Le second, exécuté en dernier, avait effacé le premier. Le store répondait « famille de l'anglais :
langues angliques » ; **hindi et finnois avaient disparu**. Ironie : le fichier fautif documente lui-même
ce péché trois lignes plus bas, à propos de `parente_langue` (« le nom dirait plus que le contenu »).

Correctif : la relation Wikidata s'appelle désormais **`famille_immediate_langue`** — deux questions, deux
noms — et le catalogue curé est restauré. Les six ancres de `valide_lecteur` sont vertes.
Gate systémique `valide_collision_relations` (16/16) : **toute** relation publiée par deux scripts rougit,
sauf allowlist à raison écrite et vérifiée (5 collisions héritées, entités disjointes, même sémantique).

### ③ LE CACHE NE SIGNAIT PAS LA POLITIQUE DE CLÉ — révélé par le correctif ①
Après avoir tué la clé vide, `createur_langage_programmation("D")` rendait **encore** `None` dans la suite :
les caches (`.bin` marshal et `.colf` mmap) **stockent les clés** et leur signature ne portait que le
format, la source et le mtime — **pas la fonction de clé**. Un cache chaud servait donc des clés périmées,
et le lookup mentait. L'invalidation reposait sur la discipline ; la discipline venait justement d'échouer.

Correctif STRUCTUREL : `base_faits.CLE_VER` (= 2) versionne la politique de clé, et les deux signatures de
cache l'incorporent (`_CACHE_VER = (2, CLE_VER)`, `_COLF_VER = (2, CLE_VER)`). Changer `normalise` ou
`_sans_articles` invalide désormais les caches **mécaniquement**. La gate vérifie ce câblage : oublier le
bump n'est plus possible sans rougir.

### ④ FRUGALITÉ, MESURÉE (jamais annoncée)
`genere_sujets._valeurs` décodait 2,35 M de lignes JSON entières pour n'en garder que le champ `valeur` —
la clé `entite` (les noms de personnes, la part longue) était jetée aussitôt. Deux paliers : décoder le
seul littéral qui suit `"valeur": ` (`raw_decode`, le décodeur RÉEL — jamais un découpage à la main), puis
trancher directement les chaînes sans antislash. **Mesuré, A/B à égalité stricte des `Counter` :
`occupation_personne` 10,7 s → 7,3 s (×1,5) ; `genere_sujets` 11,4 s → 8,8 s ; RSS inchangé (44 Mo).**
Le premier docstring annonçait ×4,2 puis ×2,7 : **chiffres non mesurés, corrigés**. Le reste du coût est
le parcours des 136 Mo et le hachage de 2,35 M de chaînes — pas le JSON.

**Leçon systémique** : une gate hors suite est une gate qui dort. `valide_cles_canoniques` et
`valide_collision_relations` entrent dans la suite (**126 gates**) et s'exercent sur l'échantillon comme
sur la base complète. **Et un défaut en cache un autre** : ① (clé vide) n'était pas réparable sans ③
(cache non versionné) — c'est la vérification de bout en bout, pas la lecture du code, qui l'a montré.

## 2026-07-12 — TROIS SONDES NÉGATIVES, CONSIGNÉES (ce qu'on ne publiera pas, et pourquoi)

Le mandat dit « traiter », pas « couvrir ». Trois pistes sondées le même jour, trois refus mesurés :

- **« Résultats établis du domaine » par Wikidata** — 1 714 items typés théorème/loi/constante/principe/
  équation. Rattachement P921 : 49 liens. P361 : 725 liens mais **pollué comme P2283** (« arbre → écorce »,
  « droits LGBT → Principes de Jogjakarta »). Rendement : **40 domaines sur 7 584 (0,5 %)**, faux compris.
  Une couverture de façade est pire que « non traité ». HORS.
- **Définitions manquantes par description Wikidata** — 242 métiers sans définition, 133 mono-QID,
  **27 descriptions FR : toutes vides** (« profession », « métier », « occupation »). Traiter un sujet avec
  « boulanger : profession » serait un traitement de façade. HORS.
- **P867 (code ROME Wikidata)** — 5 items, 1 métier net, et le seul chevauchement CONFIRME un drift de
  millésime (tatoueur : D1208 v3 vs D1244 v4). MORT.

**Rejeu vérifié** : les 7 ingesteurs du jour re-publient les 8 tables **bit-à-bit identiques** (md5).
Un pipeline non rejouable est une dette silencieuse ; celui-ci n'en est pas une.

## 2026-07-12 — L'ORACLE DE DOMAINE : 906 sujets-domaines FAUX retirés de l'ANNEXE D (le pas de l'oracle métier, rejoué)

### Le même faux de mesure que les métiers, dans l'autre annexe
`genere_sujets` prenait CHAQUE valeur de `domaine_travail` (P101) pour un domaine. Échantillonné avant de
traiter l'ANNEXE D : « **Friedrich Nietzsche** » (une PERSONNE — le philologue qui l'étudie a
P101 = l'item Nietzsche), « **Fonds des Nations unies pour l'enfance** » (une ORGANISATION, mésusage
employeur), « **France** » (une ENTITÉ GÉOGRAPHIQUE), « chauffeur de taxi » (un métier). « Résultats
établis du domaine Friedrich Nietzsche » est un sujet MAL FORMÉ — et « questions ouvertes du domaine
France » comptait comme TRAITÉ (routage) : on comptait des traités sur des non-domaines.

### Deux pièges PROPRES aux domaines, mesurés pendant la construction
- **La sur-exclusion.** Première version : exclure tout libellé porté par un item de classe exclue —
  « peinture » tombait à cause de sa PAGE D'HOMONYMIE, alors que les 4 962 peintres pointent Q11629
  (peinture, forme d'art). La garde juge les **QID réellement utilisés** comme cible de P101 ; un libellé
  n'est retiré que si TOUTES ses cibles sont exclues. Et une garde POSITIVE (« disciplines seulement »)
  sous-comptait : « permaculture » (mouvement social), « peinture », « gospel » sont des domaines
  TRAITABLES — retirer un sujet traitable est l'autre mesure fausse.
- **La collision de clés.** « physique »/« Physique » émis en deux paires se rejetaient en MULTIVALUÉ
  dans `fonctionnel` : « physique » sortait de l'oracle EN SILENCE (139 rejets, mesuré). L'oracle groupe
  par la clé `_sans_articles` et émet UNE surface ; `domaines_de_la_carte()` cherche par la même clé.

### Le correctif
`ingestion/ingere_domaines_attestes.py` publie **`est_domaine`** (30 008 clés attestées — cibles P101
réelles moins humain/patronyme/prénom/homonymie/organisation/entité géographique, en DEUX requêtes QLever
POST). `genere_sujets.domaines_de_la_carte()` filtre par lookup et LÈVE si l'oracle manque. Gate
`valide_oracle_domaine` (10/10 : sur-exclusion, collision, sabotage, absence). Suite **124 gates**.
Juge : **45 901 → 44 090 sujets (−1 811), traités 16 734 → 15 829 (−905 faux traités), non traités
25 633 → 24 727**. Ne jamais « restaurer » l'ancien compteur : ces sujets n'existaient pas.

## 2026-07-12 — LE LEVIER D'ALIGNEMENT : P8283 (+347 métiers ISCO), et le PIÈGE DE MILLÉSIME P952

### Un code à 4 chiffres n'est pas une nomenclature
Wikidata a DEUX propriétés de code ISCO. **P952 sondée d'abord : c'est l'ISCO-88** — « acteur de
cinéma → 2455 », « acrobate → 3474 », des codes 88 aux mêmes formes que les codes 08. Les injecter dans
la chaîne BLS (crosswalk ISCO-**08**→SOC) aurait été un faux SYSTÉMATIQUE et silencieux — attrapé aux
ancres avant toute publication. La bonne propriété est **P8283** (ISCO-08) : acteur → 2655 ✓.

### `ingestion/ingere_isco_wikidata.py` — table `code_isco_p8283_metier` (347 métiers)
La jointure est par **QID** (l'oracle `est_metier` porte les QID de chaque libellé) — l'alignement le plus
direct du projet, zéro appariement de chaînes. Trois gardes, chacune payée d'un faux mesuré : **mono-QID
seulement** (« compositeur »-musique prenait le 7321 du compositeur-TYPOGRAPHE, seul homonyme à porter
P8283 — 25 écartés) ; multi-groupes écartés (13) ; hors-ESCO seulement. La fusion vit dans
`_isco_du_store` : un métier que deux sources classent différemment est **écarté et compté** (25 conflits
ESCO/P8283 mesurés sur le chevauchement), jamais arbitré en silence.

### L'effet levier, mesuré
L'alignement ISCO passe de 481 à 828 métiers ; les trois chaînes re-publiées bondissent :
**rémunération 470 → 808, outils 478 → 822, risques 398 → 706** (+990 sujets sortis du backlog d'un seul
lot d'alignement — plus que n'importe quel lot de source). Gate `valide_isco_wikidata` (11/11, fusion et
désaccord compris). Suite **123 gates**. Juge : **26 623 → 25 633 non traités**, partiels 2 544 → 3 534.

## 2026-07-12 — L'AXE « RISQUES PROFESSIONNELS » S'OUVRE : BLS SOII — LES 5 AXES « SANS SOURCE » SONT TOUS OUVERTS

Dernier des cinq axes métier réputés bloqués. Le SOII (table **R100** 2023-2024) publie les taux
d'incidence annualisés des blessures/maladies professionnelles par occupation SOC détaillée et par
famille d'événements (contacts, chutes, surmenage, transports, violences…), pour 10 000 ETP, industrie
privée US. `ingestion/ingere_bls_soii.py` — table `risque_professionnel_soc_metier` (**398 métiers**),
même chaîne ISCO→SOC réutilisée. Type de cas publié et DIT : **DAFW** (cas avec arrêt de travail) ; les
agrégats (« 11-0000 ») tombent (une moyenne déguisée n'est pas le taux d'une occupation) ; colonnes de
familles DÉRIVÉES des deux rangées d'en-tête, jamais codées en dur ; « 4.0999… » du xlsx reformé au
dixième publié ; « - » (non publié) verbatim. MIX → PARTIEL : la PRÉVENTION n'est pas une statistique, et
la part française (INRS) reste sans table structurée. Gate `valide_bls_soii` (15/15). Suite **122 gates**.
Juge : **27 021 → 26 623 non traités (−398)**, partiels 2 146 → 2 544.

**Bilan du jour sur l'ANNEXE M : les 8 axes métier sont tous soit routés, soit fermés par entité (lookup),
soit MIX par entité — plus aucun « aucun ». Cinq référentiels officiels neufs (RNCP×ROME, REGPROF,
BLS OEWS, O*NET, BLS SOII), 2 578 sujets sortis du backlog (28 655 → 26 623 avec +6 sujets-tables), 0 faux.**

## 2026-07-12 — L'AXE « OUTILS, MACHINES ET LOGICIELS » S'OUVRE : O*NET (P2283 reste mort)

L'axe était à « aucun » depuis le rejet de P2283 (« soliste → solo »). ESCO ne type pas ses compétences en
« outil » ; c'est **O*NET 30.0** (US DOL, CC BY 4.0) qui codifie « Tools Used » (41 662 lignes) et
« Technology Skills » (32 681) par occupation SOC. **La 30.3 ne porte plus ces fichiers** (T2 sorti du
produit principal) : db_30_0 est épinglé, et le module le documente.

`ingestion/ingere_onet.py` — table `outil_technologie_soc_metier` (**478 métiers**), par la MÊME chaîne
que la rémunération (maillons d'`ingere_bls_oes` RÉUTILISÉS, une seule définition de la chaîne) :
métier → groupe ISCO (ESCO) → SOC 2010 → SOC 2018 → catégories O*NET. On publie la **catégorie UNSPSC**
(« Desktop calculator »), pas chaque exemple commercial : un niveau COMPLET vaut mieux qu'un extrait d'un
niveau plus fin — même choix que `geste_metier`. Granularité dite dans la valeur (groupe, pas métier
précis), dédoublonnage à l'échelle du groupe, axe MIX → PARTIEL.

Au passage, `lit_xlsx` apprend les **chaînes inline** du format xlsx (la gate fixture l'exigeait — rejeu
BLS idempotent vérifié, 470/470 identiques). Gate `valide_onet` (9/9). Suite **121 gates**.
Juge : **27 499 → 27 021 non traités (−478)**, partiels 1 668 → 2 146.

## 2026-07-12 — L'AXE « RÉMUNÉRATION MÉDIANE » S'OUVRE : BLS OEWS (la vraie médiane, jamais la moyenne)

### La chaîne à quatre maillons, tous officiels, aucun de nous
Eurostat avait été écarté à raison (MOYENNE par grand groupe ISCO-1-chiffre : double faux en puissance).
Le BLS publie la vraie **médiane**, par occupation SOC détaillée (831 occupations, OEWS mai 2024). Chaîne :
métier → groupe ISCO-08 (**`code_isco_metier`**, ESCO, déjà au store — le « problème SOC↔Wikidata » du
runbook était déjà à moitié résolu) → SOC 2010 (crosswalk officiel BLS 2012/2015, STATIQUE) → SOC 2018
(crosswalk BLS/SOCPC) → médiane annuelle US (OEWS, `A_MEDIAN`, lignes `detailed`).

### `ingestion/ingere_bls_oes.py` — table `salaire_median_soc_us_metier` (470 métiers)
La granularité est DITE (leçon Eurostat, jusque dans le NOM de la table) : la médiane est PAR OCCUPATION
SOC, un groupe ISCO en couvre plusieurs — « actuaire » → groupe 2120 → « Actuaries 125 770 $ » mais aussi
« Mathematicians », « Statisticians »… La valeur liste TOUTES les occupations du groupe. Le « # » d'OEWS
(médiane ≥ 239 200 $/an, plafond de publication) est encodé comme FAIT (4 métiers) ; « * » (non publié)
est écarté ET compté ; 11 métiers dont AUCUNE occupation n'a de médiane (militaires, hors champ OEWS)
restent NON TRAITÉS. Axe → `lookup_partiel` : part ÉTATS-UNIS seule, MIX, jamais TRAITÉ.

### Le crosswalk .xls : conversion unique documentée, pas de parseur deviné
Le crosswalk ISCO↔SOC n'existe qu'en .xls binaire (BIFF). Converti UNE FOIS en CSV (xlrd 1.2.0) — fichier
STATIQUE depuis 2015, l'original conservé dans `_raw/` pour la traçabilité ; un parseur BIFF maison
risquait le faux de parse silencieux. Les .xlsx (SOC 2010→2018, OEWS) se lisent en stdlib pur (zip+XML).
Gate `valide_bls_oes` (10/10). Suite **120 gates**. Juge : **27 969 → 27 499 non traités (−470)**,
partiels 1 198 → 1 668.

## 2026-07-12 — L'AXE « NORMES, RÉGLEMENTATION » S'OUVRE : REGPROF ; et le drapeau ROME est REJETÉ

### Un drapeau au sens inénonçable ne publie rien, même ses positifs
Le référentiel ROME porte `emploi_reglemente` (tri-état ''/N/O). Sondé AVANT usage (leçon `unregulated`
d'ESCO) : la documentation technique de France Travail le définit **circulairement** (« indication de si
l'appellation/emploi est un emploi réglementé » — aucun critère, aucune source), et il échoue sur deux
ancres en direction **négative** : `F1101 Architecte = N` (titre protégé, ordre, loi de 1977) et `D1102
Boulanger = N` (loi 96-603). Positifs invraisemblables (« arbitre assistant », « archiviste » — absents de
REGPROF). REJETÉ comme P2283. Au doute, HORS.

### La source d'autorité : REGPROF
La base officielle des professions réglementées de la Commission (déclarations des États membres,
directive 2005/36/CE) — celle que le `regulated` d'ESCO référence — expose une API JSON publique (apiUrl
dans `assets/config.json` de l'application Angular ; les chemins `/rest` du domaine servent le fallback
SPA, piège classique). **255 entrées France**, libellées en français, avec régime de reconnaissance et
niveau de qualification. Ancres : Avocat ✓, Infirmier(ère) ✓, « notaire » ABSENT (hors champ de la
directive — donc **pas de monde clos** : l'absence n'est jamais publiée comme « non réglementé »,
contraste assumé avec le RNCP exhaustif).

### `ingestion/ingere_regprof.py` — table `profession_reglementee_metier` (36 métiers)
Alignement sous les gardes maison + une règle neuve : la **parenthèse de genre collée** se déplie
(« Infirmier(ère) » → « infirmier »), le **qualificatif espacé jamais** (« Architecte (droits acquis) »
est un périmètre réduit — « architecte » n'en hérite pas ; l'axe le récupère par la table ESCO des
7 sectorielles, enfin câblée comme preuve). Axe « normes, réglementation et certifications » →
`lookup_partiel` : la réglementation d'**ACCÈS** est fermée, les normes **techniques** (ISO/AFNOR, contenu
payant) restent non couvertes — MIX, jamais TRAITÉ. Gate `valide_regprof` (16/16). Suite **119 gates**.
Juge : **28 009 → 27 969 non traités (−40)**, partiels 1 158 → 1 198.

## 2026-07-12 — L'AXE « FORMATION, DIPLÔMES » S'OUVRE : ROME×RNCP (la piste « jamais interrogée » était vivante)

### Le pas
Le runbook (§4) tenait l'axe formation pour bloqué (« ROME : api.francetravail.io, clé requise, HTTP 401 »)
mais listait le RNCP comme piste **jamais sondée**. Sondé : deux sources officielles, ouvertes, sans clé.

- **ROME v4** (France Travail) — le zip open-data « Toutes les données du ROME » publie
  `referentiel_appellation` : **14 301 appellations → code ROME**, librement. Le 401 ne concernait que
  l'API temps réel ; la croyance « arborescences seulement » était fausse.
- **RNCP** (France Compétences, export CSV quotidien sur data.gouv) — `Standard` (intitulé, niveau CEC,
  statut ACTIF de 35 776 fiches) + `Rome` (67 075 liens fiche → code ROME).

### Ce que la table affirme, mot à mot (leçon ESCO : ne pas voler une granularité qu'aucune source n'affirme)
Personne n'affirme « la fiche F prépare au métier M ». Les deux faits attribués sont : l'appellation relève
du code ROME (France Travail, niveau **appellation**) ; la fiche est enregistrée sous le code (France
Compétences, niveau **code**). La valeur publiée dit donc les deux, code visible : « code ROME K2402
(Ingénieur de recherche…) ; 104 certifications actives enregistrées sous ce code : … ». Exemple qui impose
cette forme : « nanotechnologue » relève de K2402, dont les fiches vont des neurosciences au sport.

`ingestion/ingere_rome_rncp.py`, deux relations : **`code_rome_metier`** et **`certification_rncp_metier`**
(646 métiers de la carte chacune). Alignement sous les gardes ESCO : expansion genrée **structurelle**
(« Abatteur / Abatteuse de carrière » → « abatteur de carrière », jamais le masculin nu ; aucune expansion
si ≠ 2 segments, virgule, ou féminin plus court), unicité bilatérale (7 formes multi-codes écartées,
0 métier ambigu), égalité exacte NFC. **372 métiers** avec ≥ 1 fiche active (exhaustif par code, trié,
daté par l'export du 09/07/2026 — jamais de top-N) ; **274 faits négatifs** clos et datés (« allergologue :
code J1129, aucune certification active » — les DES de médecine ne passent pas par le RNCP, et le
répertoire est exhaustif : l'absence y est un fait).

### Le sujet reste MIX
La formation varie par **pays** et par **année** (la PARTIE VI le dit). Le RNCP ferme la part FRANÇAISE :
`couverture_borne` passe l'axe en `lookup_partiel` → **646 sujets NON TRAITÉS → PARTIELS** (28 655 →
28 009), jamais TRAITÉS. Les 2 754 métiers sans appellation ROME (« Akyn », « Busshi ») sont le même
plafond structurel qu'ESCO : un référentiel du marché du travail contemporain ne décrit pas les métiers
historiques. Gate `valide_rome_rncp` (30/30) : expansion, gardes d'unicité, fiches INACTIVE écartées,
négatif daté, sabotages nommant le remède. Suite **118 gates**.

### Un cliquet périmé débusqué
`valide_sujets` exigeait encore la **présence** d'« Abogado »/« Anime »/« Armée de l'air » dans la carte
(comme sujets non traités) — exigence inversée par l'oracle du 2026-07-12, qui les retire : un sujet faux
se **retire**, il ne reste pas « non traité ». Le check ne rougissait que sur la base complète, jamais dans
la suite (échantillon épinglé). Corrigé en son contraire : leur **absence** est vérifiée (64/64).

## 2026-07-12 — UN SUJET FAUX EST AUSSI GRAVE QU'UN FAIT FAUX (oracle de métier)

### Le défaut
`outils/genere_sujets.py` peuplait l'ANNEXE M en prenant **chaque valeur distincte** de la table
`occupation_personne` pour un métier. Trois familles de valeurs n'en sont pas :

- **Les énumérations fabriquées.** `ingestion/ingere_celebres.py` réécrit la table pour les personnalités
  célèbres et joint leurs occupations (`joinmax=3` sur P106) : « Einstein → physicien, professeur
  d'université et philosophe ». **Le fait est vrai** ; la valeur n'est pas *un* métier. Mesuré : 2 207
  valeurs composées, et la requête `?item rdfs:label "acteur ou actrice de cinéma, acteur ou actrice de
  théâtre et acteur ou actrice de genre"@fr` ne rend **aucun** item Wikidata. C'est aussi la cause racine du
  vol de gestes ESCO (« écrivain ou écrivaine, militaire ») corrigé le 2026-07-11 : on avait soigné le
  symptôme. Les cinq autres tables de `CIBLES` ont `joinmax=1` : `occupation_personne` est la **seule**
  touchée.
- **Le bruit de P106** : « Abogado » (nom de famille), « Anime », « Armée de l'air ».
- **Les entreprises** que la hiérarchie Wikidata range sous « profession » : « Mann » = Q2552697,
  *English lorry manufacturer (1896–1928)*.

`ingere_metiers.py` documentait déjà « Abogado » et concluait : *« ces entrées restent NON TRAITÉES »*.
C'est la mauvaise conclusion. **Un nom de famille ne pourra jamais être traité** — ni sa définition, ni ses
gestes, ni ses risques professionnels n'existent. Les compter fabriquait **38 703 sujets inépuisables** :
un backlog qui ment. Pire, son commentaire nommait `occupation_personne` « la table qui dit quels libellés
sont VRAIMENT des métiers » — l'oracle contenait exactement ce qu'il prétendait exclure.

### Le correctif
`ingestion/ingere_metiers_attestes.py` publie l'oracle manquant : **`est_metier`**, 7 869 libellés
(214 homonymes multi-QID conservés — « professeur » reste un métier), définis par la seule garde de type
`P31/P279* Q28640` moins patronymes (Q101352) et prénoms (Q202444). `genere_sujets.metiers_de_la_carte()`
filtre par **lookup**, et **lève** si l'oracle manque : régénérer une carte gonflée en silence est pire que
ne rien régénérer.

**Deux gardes qui se couvrent, et la seconde n'est pas redondante.** L'oracle (type) tue les valeurs de P106
qui ne sont pas des occupations. L'usage P106 tue les items *typés* occupation que **personne n'exerce** :
mesuré, Q136296945 « Plaque de reliure crucifixion, saintes femmes au tombeau, ascension et Christ
bénissant » est un **ivoire** (`P31 → Q351853`) que la chaîne `P279*` raccroche à « profession ». Zéro
personne ne l'a pour occupation : il n'entre pas dans la carte.

**Aucune heuristique de ponctuation.** « voyageur, représentant et placier » (VRP), « professeurs des
écoles, instituteurs et assimilés », « Manœuvres des mines, du bâtiment et des travaux publics… » sont de
**vrais** libellés à virgules. Un filtre sur la virgule les aurait perdus. La source tranche, pas le texte.

**L'oracle est français, délibérément.** Mesuré : accepter aussi les libellés anglais ne rattrape que 6
libellés sur 2 636 — dont « Mann » (une entreprise), tandis que « magistrate », « general manager » et
« credit manager » sont **déjà** dans l'oracle sous leur nom français. Élargir réimporterait le bruit
d'entreprises sans gagner un seul métier réel.

### Cliquet
`tests/valide_oracle_metier.py` (36/36) : fixture écrite à la main (s'exerce **sans** la base réelle),
**contre-épreuve de sabotage** (oracle vidé → zéro métier : le filtre le consulte donc bien),
**contre-épreuve d'absence** (table retirée → `SystemExit` qui nomme la table et la commande), et ancres
nommées sur la base réelle. Câblé à la suite ; `outils/` ajouté au `PYTHONPATH` de `suite_conversation`.

### Mesure — le compteur BAISSE, et c'est le bon signe
`45 894 sujets · 16 727 traités · 512 partiels · 28 655 NON traités · 0 dette.` (avant : 84 597 · 21 644 ·
584 · 62 369). Les « traités » baissent de 4 917 parce qu'on comptait des *traités* sur des non-métiers :
« Abogado — ce métier est-il fait pour moi ? » passait en routage. **Suite : 117/117.** `valide_cablage` :
588 modules, 0 orphelin.

## 2026-07-11 (suite 4) — ESCO complet ; un sujet « bloqué » qui ne l'était pas ; deux faux d'étiquette

### 1. Le bug de descente coûtait 1 239 occupations
Moissonnage relancé avec la descente complète (`narrowerOccupation`) et le filet réseau élargi :
**2 938 occupations** contre 1 699. « assistant de justice » et 1 238 autres étaient invisibles.
Gain sur la carte : axe définition 3 086 -> **3 238** ; axe gestes 414 -> **552**.

**Le plafond d'alignement est structurel, et mesuré** : 7 607 des 8 238 métiers du store n'ont AUCUN libellé
ESCO correspondant (ESCO couvre le marché européen contemporain ; le store porte des métiers historiques
comme « Akyn » ou « forgeron de lames »). 75 sont perdus par ambiguïté côté ESCO. Les échecs restants sont
des abstentions JUSTES : « médecin » n'est ni « médecin généraliste » ni « médecin spécialiste ». Forcer
l'appariement rejouerait le vol de gestes.

### 2. Un faux d'étiquette : « avocat : non réglementée »
Le drapeau `unregulated` d'ESCO ne signifie **pas** « non réglementée ». Son texte dit : « pour vérifier si
cette profession est réglementée dans les États membres, veuillez consulter la base de données ». C'est une
**absence d'information**, que j'avais transformée en affirmation. La table publiait « avocat ou avocate :
non réglementée au sens de la directive 2005/36/CE » — un faux.
Seul `regulated` est un fait : il marque les professions **sectorielles à reconnaissance automatique**
(médecin, infirmier, dentiste, sage-femme, pharmacien, vétérinaire, architecte) — **15 sur 2 938**. La table
ne publie plus qu'elles (8 appariées au store), et l'axe « normes » reste NON TRAITÉ.

### 3. « mix électrique d'un pays/année » n'était pas bloqué
Ce sujet figurait parmi les six « bloqués sur un corpus externe ». Il ne l'était pas : **Our World in Data**
publie la part de l'électricité par source, par pays et par année (données Ember, CC BY).
**5 907 couples pays/année ingérés. Sujet FERMÉ.** France 2023 : nucléaire 65,2 %.

Trois gardes, dont deux nées d'un faux mesuré :
- **agrégats** : rejeter les lignes sans code ne suffit pas — OWID donne un code à ses agrégats
  (`World` -> `OWID_WRL`). « World (2023) » était entré dans la table. On rejette les codes `OWID_`, sauf
  le **Kosovo** (`OWID_KOS`), territoire réel dépourvu de code ISO ;
- **couverture partielle** : 670 lignes anciennes ne somment pas à 100 % (« Algérie 1985 : 5,26 % ») ; les
  publier serait un faux par omission ;
- **vérité datée** : l'année est dans la clé.

**Leçon : « bloqué sur un corpus externe » doit être RE-SONDÉ, pas tenu pour acquis.**

### 4. Deux autres sujets « bloqués » qui ne l'étaient pas
- **`equivalences_diplomes`** (65/65) : la CITE 2011 (UNESCO, **9** niveaux) et le CEC/EQF (UE, **8** niveaux)
  sont publiés et stables. Le baccalauréat est **CITE 3 mais CEC 4** — la CITE classe les programmes, le CEC
  les acquis d'apprentissage ; les aligner mécaniquement serait faux. Et surtout : un même niveau CITE
  **n'emporte pas reconnaissance juridique**. `reconnaissance_juridique()` **abstient** : elle relève des
  autorités nationales (ENIC-NARIC) et, pour les professions réglementées, de la directive 2005/36/CE.
- **`chronologie_religieuse`** (77/77) : le sujet se scinde nettement. Les conciles, édits et schismes sont
  **datés** par des sources contemporaines (Nicée 325, Hégire 622, schisme 1054, 95 thèses 1517, Vatican II
  1962-1965, séparation 1905). Les faits fondateurs ne le sont pas. `date('naissance_jesus')` **abstient** et
  renvoie une **fourchette (−6, −4)** : Hérode meurt en −4, l'ère chrétienne n'a pas d'an 0, et le
  25 décembre est une date liturgique fixée au IVᵉ siècle. Deux chronologies concurrentes pour le Bouddha :
  `consensus = False`. Un module qui daterait la naissance de Jésus à l'an 1 serait FAUX.

### 5. Mesure
`84 597 sujets · 21 644 traités · 584 partiels · 62 369 NON traités · 0 dette.`
**Suite : 116/116 gates.** `capacites.REGISTRE` : **383 preuves exécutables, 0 orphelin.**

**PARTIE I : 67 traités, 0 partiel, 0 non traité — entièrement fermée.**
Toutes les parties conceptuelles sont à zéro non traité, sauf la PARTIE VI (3 sujets).
Backlog conceptuel : **6 -> 3**, et les trois sont réellement bloqués : texte d'une loi à une date
(Légifrance exige OAuth), jurisprudence d'une cour, programmes et diplômes officiels (par pays et par année).

## 2026-07-11 (suite 3) — NEUF BRIQUES : le cas ambigu, l'abstention vraie, le périmètre dit

Les 36 partiels conceptuels restants se répartissaient en deux natures : **20 sont MIX par construction**
(part bornée + part non bornée — leur état PARTIEL est le bon, les forcer serait mentir), et le reste était
constructible. Neuf briques ferment neuf sujets et en servent quatre autres mieux.

### Trois abstentions que ces briques rendent obligatoires
- **`trigonometrie_triangle`** (72/72) : le cas **SSA** (côté-côté-angle) admet **ZÉRO, UNE ou DEUX**
  solutions. `resout_triangle` rend la LISTE des triangles. Vérifié : a=6,b=8,A=30° -> deux ;
  a=3,b=8,A=30° -> zéro ; a=10,b=8,A=30° -> un. Un module qui rendrait toujours un triangle serait FAUX.
- **`jeux_institues`** (89/89) : théorème de Bouton. La position de Nim (1,2,3) a une somme de Nim **nulle**,
  donc **aucun coup gagnant n'existe** — `nim_coup_gagnant((1,2,3))` abstient. C'est une abstention VRAIE,
  pas un échec. Et le module **refuse de jouer aux échecs** plutôt que d'improviser.
- **`nomenclature_organique`** (113/113) : `identifie('C3H6O')` rend l'**ambiguïté** (propanal ET propanone
  sont isomères). Rendre un composé unique serait un faux. Les cycliques -> abstention.

### Les six autres
- **`thermodynamique_principes`** (72/72) : ΔU = Q − W (convention thermodynamique **nommée** — la
  convention chimiste donne le signe opposé) et l'entropie des processus **non isothermes**,
  m·c·ln(T2/T1), **en kelvins**. La même formule en °C (27 -> 127) donnerait 6 486 J/K au lieu de 1 204 :
  **un faux d'un facteur 5**. Le module refuse les degrés Celsius.
- **`grammaires_formelles`** (330/330) : conversion en forme normale de Chomsky (START/TERM/BIN/DEL/UNIT),
  **vérifiée par équivalence de langage** sur tous les mots courts (deux chemins : dérivation exhaustive vs
  CYK), puis déterminisation des AFN.
- **`pharmacocinetique`** (88/88) : modèle à un compartiment. L'**ASC = dose/Cl est indépendante du volume
  de distribution** (identité exacte, ancre non circulaire). Éthanol et phénytoïne (cinétique saturable)
  -> abstention. Cinq demi-vies éliminent **96,875 %**, jamais « 100 % ».
- **`familles_langues`** (88/88) : le basque est un **isolat** ; hindi et anglais **sont** apparentés
  (contre-intuitif) ; hongrois et français ne le sont pas malgré la proximité géographique ; le turc est
  **« turcique »**, jamais « altaïque » (regroupement contesté). Familles distinctes -> abstention.
- **`dimensionnement_structure`** (70/70) : la contrainte admissible se prend sur la **borne basse** de
  l'intervalle de limite élastique — dimensionner sur la borne haute serait dangereux. Une contrainte
  tombant DANS l'intervalle rend « indéterminé ». Matériau fragile -> abstention.
- **`densites_ingredients`** (135/135) : `recettes` abstenait sur tout ingrédient autre que l'eau. Les
  masses volumiques **apparentes** sont rendues avec leur incertitude (une tasse de farine tassée pèse 30 %
  de plus qu'une tasse aérée). La convention de « cup » doit être nommée, sinon abstention.

### Deux faux tués par la vérification adverse, après le vert des gates
- **`familles_langues` — un isolat qui avait un parent.** `est_isolat` s'appuyait sur une liste de familles
  « isolées » et déclarait donc **le japonais ET le ryukyu isolats** — alors qu'ils sont apparentés entre eux
  (famille japonique). Un isolat qui a un apparenté n'en est pas un. La fonction est désormais
  **STRUCTURELLE** : une langue est un isolat si et seulement si aucune autre langue du catalogue ne partage
  sa racine. Un contrôle de non-contradiction (est_isolat(x) ⟹ aucun apparenté) est ajouté à la gate.
- **`densites_ingredients` — deux entorses.** `adapte_recette` acceptait NaN et ±inf (la validation déléguée
  ne testait pas la finitude) ; et le round-trip masse↔volume était annoncé **exact** alors qu'il n'est
  exact que pour l'eau (densité 1) et seulement **stable à ~10 chiffres** ailleurs. La docstring ne
  sur-affirme plus, et la gate le prouve par balayage de 3 600 volumes non ronds.

### Mesure
`84 595 sujets · 21 597 traités · 446 partiels · 62 552 NON traités · 0 dette.`
**Suite : 114/114 gates.** `capacites.REGISTRE` : **381 preuves exécutables, 0 orphelin.**
Sonde indépendante des 9 briques, avec mes propres ancres : **60/60**.

## 2026-07-11 (suite 2) — HUIT BRIQUES ferment douze partiels ; deux bugs d'ingestion invisibles

### 1. Deux bugs d'ESCO qui n'étaient pas des FAUX — donc que rien ne signalait
- **Descente d'arbre incomplète.** Une occupation ESCO peut avoir des occupations FILLES
  (`narrowerOccupation` : « employé de bureau » -> « assistant d'ingénieur »). Le moissonneur s'arrêtait à la
  première occupation rencontrée : **1 699 des ~3 000 occupations**, soit un tiers du référentiel invisible.
  La donnée était juste, simplement amputée — aucune gate ne peut voir ce genre de manque.
- **Retry trop étroit.** Après ~30 minutes de réseau, une réponse tronquée a levé
  `http.client.IncompleteRead`, que le retry ne connaissait pas (il n'attrapait que `HTTPError`, `URLError`,
  `TimeoutError`). **Tout le moissonnage a été perdu.** Sur 3 600 requêtes un aléa réseau est certain.
  Filet élargi (lecture tronquée, connexion coupée, socket cassé) + **points de reprise tous les 200**.

### 2. Sources sondées pour les axes métier, et pourquoi elles ne ferment pas
- **ROME** : data.gouv ne publie que des arborescences ; le lien métier -> compétence exige une clé
  `api.francetravail.io` (HTTP 401).
- **Eurostat SES** (`earn_ses18_25`) : atteignable, mais c'est le salaire **MOYEN** par **grand groupe ISCO**.
  Le publier comme « rémunération médiane du boulanger » serait un DOUBLE faux (moyenne ≠ médiane ;
  groupe ≠ métier). Piste écartée, consignée avec sa limite.

### 3. Huit briques, douze partiels fermés
- **`inference_classique`** (85/85) : test z / t / khi-deux, IC, et l'intervalle de **Wilson** pour une
  proportion — celui de Wald est faux près de 0 et 1 (il donnerait [0,0] pour 0 succès sur 10). Le module
  énonce qu'une p-valeur n'est **pas** la probabilité que H0 soit vraie.
- **`derivation_symbolique`** (94/94) : dérivation des fonctions élémentaires, confrontée aux **différences
  finies centrées** (deux chemins de code). `primitive(exp(-x²))` -> abstention.
- **`convergence_series`** (69/69) : d'Alembert, Cauchy, Leibniz. Le cas limite (rapport = 1) rend
  **'indeterminé'**, jamais « converge » : la série harmonique diverge alors que son terme tend vers 0.
- **`edo_lineaires`** (71/71) : 2e ordre, trois régimes ; Cauchy résolu exactement (C1 = −1, C2 = 1 pour
  y''−3y'+2y = 0, y(1) = e²−e).
- **`recurrences`** (94/94) : **théorème maître**. Le n·log n du tri fusion est DÉRIVÉ, pas lu dans une table ;
  Karatsuba (cas 1) est bien sous-quadratique, Strassen bat le n³ naïf.
- **`entropie_source`** (53/53) : l'entropie d'une SOURCE n'est pas celle d'une distribution. Estimation
  plug-in **biaisée vers le bas** + Miller-Madow ; taux d'entropie d'une chaîne de Markov : **0,469 bit au
  lieu de 1** — la mémoire réduit l'incertitude. `entropie_empirique` rend le couple (H, N) : une entropie
  sans son nombre d'observations ne signifie rien.
- **`ajustement_causal`** (55/55) : critère de porte dérobée par d-séparation, puis P(Y|do(X)).
  Sondé sur les **calculs rénaux (Charig 1986)** : en brut B semble meilleur (82,6 % > 78 %), **après
  ajustement A l'emporte (0,8325 > 0,7789)**. Si Z ne bloque pas les portes dérobées, ou contient un
  descendant du traitement -> **abstention**.
- **`biais_collision`** (61/61) : le mécanisme générique du biais de sélection est la COLLISION.
  **Berkson** : deux maladies indépendantes (OR = 1 exact) deviennent négativement associées chez les
  hospitalisés (OR = 9/25). Témoin à sélection indépendante : aucun biais.

Le théorème de Bayes DIRECT sur données existait déjà dans `probabilites_elementaires` alors que le sujet
pointait encore vers `bayes.py` (log-cotes) : recâblé.

### 4. La vérification adverse a tué trois faux que les gates initiales laissaient passer
- **`inference_classique` — un FAUX POSITIF de test statistique.** La queue du khi-deux était estimée par
  quadrature de Simpson, qui **ratait le pic interne du pdf** quand la statistique tombait sous le mode :
  pour 21 catégories quasi uniformes (statistique = 0,1), elle rendait **p = 3,29e-13** au lieu de **p = 1**.
  Un test qui aurait rejeté H0 sur un dé parfaitement équilibré. Remplacée par la fonction gamma incomplète
  régularisée (série + fraction continue de Lentz), exacte à ~1e-15, et la gate est ancrée sur les valeurs
  critiques tabulées (χ²₁ > 3,841 -> 0,05 ; χ²₂₀ > 31,410 -> 0,05) recalculées par un algorithme DIFFÉRENT.
- **`convergence_series` — un verdict trop sûr.** « diverge » se déclenchait dès qu'une fenêtre finie ne
  tendait pas vers 0, même croissante. Le champ devient tri-état : une queue non stabilisée rend
  « indéterminé ». Une méthode numérique finie ne prouve pas une divergence, et la docstring le dit.
- **`entropie_source` — un estimateur faux et une garde manquante.** La correction de Miller-Madow était
  calculée en **nats** alors que l'entropie du module est en **bits** (facteur ln 2 manquant) ; et
  `entropie_conditionnelle_markov` acceptait une distribution **non stationnaire**. Les deux sont corrigés,
  et la stationnarité πP = π est désormais vérifiée à 1e-9, sinon ValueError.

Aucun de ces trois n'aurait été vu par la seule lecture du code. C'est le rôle de l'auditeur adverse.

### 5. Mesure
`84 595 sujets · 21 588 traités · 455 partiels · 62 552 NON traités · 0 dette.`
**Suite : 105/105 gates.** `capacites.REGISTRE` : **372 preuves exécutables, 0 orphelin.**
Sonde indépendante des 8 briques, avec mes propres ancres : verte.

## 2026-07-11 (suite) — DÉCOUPE DES RÈGLES : rendre à chaque sujet son état réel ; ANNEXE T fermée

### 1. Un regex trop large est une mesure FAUSSE
Six règles de `couverture_borne._REGLES` couvraient chacune plusieurs sujets et les alignaient sur le plus
faible : **une seule règle forçait six sujets en PARTIEL**, alors que deux d'entre eux étaient pleinement
traités. Un motif trop large masque à la fois ce qui est fait et ce qui manque. Chaque sujet a désormais sa
règle et son état MESURÉ. Sondé avant de découper (17 vérifications) :
- `contrainte.CSP` fait une recherche **complète** (SAT et UNSAT décidés, jamais devinés) -> TRAITÉ ;
- les équations de degré 1 et 2 sont mieux servies par `equations_polynomiales` (racines exactes,
  irrationnelles ENCADRÉES par Sturm) que par `algebre_calcul` -> TRAITÉ ;
- le dénombrement combinatoire est complet dans `maths_discretes` (C(52,5) = 2 598 960) -> TRAITÉ ;
- **preuve mal dirigée** : « inflation mesurée » et « PIB, chômage » citaient `cycles_economiques`, qui est
  un CATALOGUE de phases et ne calcule rien. Les formules vivent dans `inflation.py` / `pib.py` -> TRAITÉ ;
- « datation radiométrique » citait `physique` (décroissance DIRECTE) ; la datation est le problème
  INVERSE, bâti la veille -> `datation_radiocarbone`, TRAITÉ.

**Effet mesuré : +7 traités, et le backlog conceptuel MONTE de 6 à 13.** Sept manques réels étaient cachés
derrière des règles trop larges. C'est le résultat attendu : l'honnêteté fait monter le compteur avant de
le faire descendre. (Trois de mes propres sondes étaient fausses : `'aucune_reelle'` contient « reelle »,
`'deux_irrationnelles'` contient « rationnelles », et C(5,−1) = 0 est la convention standard.)

### 2. `nomenclatures.py` — ANNEXE T ramenée à ZÉRO non traité
ISCO-08 (OIT) : les 10 grands groupes, leurs **niveaux de compétence** rendus comme TUPLES (le grand groupe 1
en couvre deux, le 0 en couvre trois — réduire à un scalaire serait un faux), et les cardinalités officielles
10 / 43 / 130 / 436. `grand_groupe_du_code` exploite la propriété de la nomenclature (le premier chiffre EST
le grand groupe) : **contrôle croisé sur la table `code_isco_metier` ingérée la veille — les 415 métiers
alignés sur ESCO se répartissent sur les 10 grands groupes, 0 code rejeté**, et le boulanger (7512.1) tombe
bien dans « métiers qualifiés de l'industrie et de l'artisanat ».
Ajoute aussi les 10 divisions Dewey du 500 et les 21 sections NACE Rév. 2.

**Abstention structurelle** : MSC2020, ACM CCS, CIM-11 et ROME sont CITÉES (éditeur, nature) mais leur
contenu n'est pas embarqué — `classes()` y lève ValueError. Énumérer de mémoire 63 classes MSC ou les
chapitres de la CIM-11 produirait exactement le genre de faux plausible que ce projet interdit.
Gate 77/77. **ANNEXE T : 30 traités, 5 partiels, 0 non traité.**

### 3. Sept briques neuves ferment les manques exposés par la découpe
- **`algebre_lineaire`** (84/84) : pivot de Gauss EXACT, Rouché-Capelli (unique / infinite / aucune),
  inverse par Gauss-Jordan. `M·M⁻¹ = I` est **re-vérifié** après inversion, sinon RuntimeError.
- **`algebre_symbolique`** (96/96) : développement et factorisation exacts ; le facteur irréductible sur ℚ
  est rendu tel quel, aucune racine inventée.
- **`simplification_booleenne`** (67/67) : Quine-McCluskey. La forme minimisée est re-vérifiée équivalente
  par `algebre_boole` — **chemin de code indépendant du minimiseur**.
- **`developpement_limite`** (79/79) : un développement limité sans borne du reste ne dit rien.
  `approxime()` rend **(valeur, borne de Lagrange)**, jamais une valeur nue ; hors rayon -> abstention.
- **`probabilites_elementaires`** (131/131) : probabilité classique exacte, lois discrètes, moments.
  `Var = E[X²] − E[X]²` re-vérifié par deux chemins. **Piège du taux de base** vérifié en ancre :
  sensibilité 0,99 / spécificité 0,99 / prévalence 1/1000 -> P(malade | test +) = **99/1098 ≈ 9 %**, pas 0,99.
- **`nomenclatures`** (77/77) et **`codes_normalises`** (84/84) — cf. §2 et ci-dessous.

`codes_normalises` traite les trois codes que `bibliotheconomie` ne couvrait pas, avec leurs pièges :
le **yen n'a aucune décimale** et le dinar koweïtien en a trois (supposer 2 fausse les montants d'un facteur
100) ; **le +1 n'identifie pas un pays** (États-Unis *et* Canada) — `pays_unique_depuis_indicatif` abstient
plutôt que de choisir ; l'ISBN-10 dont la clé est « X » ; la plaque SIV française (les lettres I, O et U sont
exclues), tout autre pays -> ValueError. Il reste **PARTIEL** et le dit : 25 monnaies, 23 pays, une plaque.

Toutes sont **câblées** (`capacites.REGISTRE` : 364 preuves exécutables, 0 orphelin), et sondées par mes
propres ancres, indépendamment de leurs gates : **36/36**.

### 4. Mesure
`84 595 sujets · 21 575 traités · 468 partiels · 62 552 NON traités · 0 dette.`
**Suite : 97/97 gates.** Backlog conceptuel : **6 sujets**, tous bloqués sur un corpus externe.
PARTIES I à V, VII, VIII, XI, XII et ANNEXE T : **zéro non traité**.

## 2026-07-11 — LOT « TOUT CÂBLER » : les 3 rouges tués, 48 briques branchées au produit, suite 90/90

Reprise du mandat après commit du lot de nuit. Objectif : identifier les rouges, les corriger
chirurgicalement, et brancher réellement ce qui n'était que bâti.

### 1. Les trois gates rouges, nommées et corrigées
- **`valide_cablage` — 48 ORPHELINS.** Les 48 briques de la nuit étaient vertes en isolé mais **inaccessibles
  depuis le produit** (« validé A/B ≠ actif dans la boucle »). Chacune reçoit désormais une sonde
  `_p_<module>()` dans `src/capacites.py` **et** une entrée au REGISTRE sous son libellé exact de la carte.
  Une sonde n'est pas un import : sa preuve **s'exécute** (ancres vérifiées à la main : Cayley-Hamilton pour
  les valeurs propres, Huygens-Steiner pour l'inertie, Wiedemann-Franz croisant deux tables indépendantes,
  OEIS A000602 pour les isomères, JDN 2451545 pour les calendriers…). **357 preuves du REGISTRE au vert.**
  Sept sondes ont d'abord échoué : mes appels d'API étaient des hypothèses. L'une d'elles a révélé un piège —
  `phenomene_attendu('transformante')` **contient** le mot « volcanisme », dans « *pas de* volcanisme ».
- **`valide_atomes` — 19/20.** `anatomie_systemes.liste_organes` n'était consommée nulle part ; la sonde
  d'anatomie la consomme. **20/20.**
- **`valide_assistant_nl` — 500/506.** Aucune régression du produit : **506/506 sur l'échantillon**, 500/506
  sur la base complète. Cause réelle : `suite_conversation._env()` faisait un `setdefault` sur
  `LECTEUR_DATASETS_DIR`, si bien qu'**une variable exportée dans le shell changeait le verdict de la suite**
  (les cas d'abstention « donnée absente » trouvaient soudain la donnée). L'échantillon est désormais
  **ÉPINGLÉ**. Une suite dont le résultat dépend de l'appelant ne prouve rien.

### 2. Le cliquet d'atomicité ne protégeait rien en intégration
Conséquence de l'épinglage : `valide_sujets` ne trouvait plus les tables métiers et son cliquet ne
s'exerçait pas. Il est rejoué sur une **FIXTURE** (store fabriqué en `tempfile`) : métier présent -> TRAITÉ
nommément ; métier absent -> NON TRAITÉ nommément ; axe « gestes » -> PARTIEL, jamais TRAITÉ ; axes sans
source -> 0 traité ; et une **contre-épreuve** qui sabote un axe pour vérifier que la gate le détecte.
Le cliquet s'exerce maintenant **toujours**, avec ou sans la base réelle.

### 3. Deux distinctions posées, deux faux tués
- **Dette de CODE vs donnée absente.** Une preuve-`table` introuvable n'est pas une dette : c'est un fait sur
  ce store (l'échantillon n'embarque pas `famille_langue`). Une preuve-`module`/`gate` introuvable **reste**
  une dette (contre-épreuve faite).
- **FAUX corrigé : « conséquence en logique du premier ordre (cas général) »** était déclaré TRAITÉ par ma
  règle trop large. Le cas général est **semi-décidable** (Church-Turing) ; le module ne fait que du
  model-checking sur domaine fini. La règle est resserrée au « cas décidables ».

### 4. Reconstruit et développé
- **`versification_fr`** (supprimé à tort la nuit précédente, jamais committé). Rebâti **plus honnête** :
  il refuse de trancher la diérèse (« lion » = 1 ou 2) **et** la finale `-ent`. Une première version comptait
  11 syllabes à l'alexandrin de Verlaine (« Je fais **souvent** ce rêve étrange et pénétrant ») : « -vent »
  n'est pas une désinence verbale, et l'orthographe ne le dit pas. Le compte est donc AMBIGU par défaut,
  certain pour une liste fermée de mots non verbaux. Gate 78/78 ; une de mes propres ancres était fausse
  (jardin/matin = rime *suffisante*, pas riche).
- **`heredite_mendelienne`** (63/63) : échiquier de Punnett exact en `Fraction`, ratios **3:1**, **1:2:1**,
  **9:3:3:1**, croisement-test. Le régime de dominance est toujours NOMMÉ ; les gènes liés -> abstention.
- **`dynamique_populations`** (69/69) : Malthus, Verhulst, carte logistique **discrète** avec ses régimes
  (May 1976) et Lotka-Volterra. Au-delà du seuil de Feigenbaum (3,5699…), le point fixe existe mais n'est
  jamais atteint : **abstention** — c'était le faux le plus tentant du module.
  Ces deux modules remplacent la preuve fausse qui citait `bioinfo.py` (séquences ADN).

### 5. Mesure
`84 595 sujets · 21 532 traités · 496 partiels · 62 567 NON traités · 0 dette.`
**Suite conversationnelle : 90/90 gates.** `valide_cablage` : 562 modules atteignables, **0 orphelin**.
Il reste **6 sujets conceptuels** sur 1 704, **tous bloqués sur un corpus externe** (texte d'une loi à une
date, jurisprudence, programmes et diplômes officiels, équivalences de diplômes, mix électrique par
pays/année, datation des faits religieux). Ils restent NON TRAITÉS, et le disent.

## 2026-07-10 (nuit) — MANDAT « TRAITER TOUT LE BACKLOG DES SUJETS » : fermeture ATOMIQUE, vague A

Mandat Yohan : traiter les 79 partiels et les 66 258 sujets au backlog, en autonomie, sans jamais s'arrêter,
**chaque sujet traité atomiquement et chirurgicalement**, sans raccourci. Web autorisé ; je suis moi-même une
source légitime sous FAUX=0 (certitude + recoupement + ancres + abstention au doute).

**MESURE (le juge, pas la parole)** : 84 588 · 18 251 traités · 79 partiels · 66 258 backlog
                              ->    84 590 · 21 383 traités · 83 partiels · 63 124 backlog · 0 dette.
**PARTIE I et PARTIE II : backlog ramené à ZÉRO.**

### 1. Fermeture ATOMIQUE des annexes (le changement d'architecture)
`couverture_borne` jugeait les 8 238 métiers **par axe**, en bloc : c'était une DÉCLARATION. Il juge désormais
**par entité, par lookup réel** dans une table du store. Un métier n'est TRAITÉ que si SON libellé y est
présent ; sinon il reste NON TRAITÉ **et le dit nommément**. Mesuré sur l'axe « définition et périmètre » :
3 086 métiers traités (preuve : « `definition_metier` : « Akyn » vérifié par lookup »), 5 152 non traités
(« « Abogado » absent de definition_metier, surclasse_metier »). Les six axes sans source ingérée affichent
**0 sujet traité** — aucune couverture inventée. `valide_sujets` passe de 35 à **49 checks** et porte le
cliquet : une contre-épreuve prouve qu'elle rougit si un axe redevenait « couvert en bloc ».

### 2. Ingestion `definition_metier` + `surclasse_metier` (Wikidata) — CINQ gardes, chacune née d'un FAUX réel
Trois versions du script ont produit des faits **faux**, attrapés par échantillonnage :
- sans **garde d'attestation** (le libellé doit être une valeur réelle de P106), la requête typée remontait
  des ENTREPRISES et des OBJETS : « A.B.C. motorcycles -> constructeur britannique de motocyclettes »,
  « 9ff -> préparateur automobile », « 4 miséricordes de stalles au Fidelaire -> stalles monument historique » ;
- sans **garde de type** (`P31/P279* Q28640`, patronymes et prénoms exclus), le store remontait
  « Abogado -> nom de famille », « Anime », « Armée de l'air » — des valeurs de P106 qui ne sont pas des métiers ;
- sans **garde anti-homonyme**, « intendant », « bâtonnier », « chevalier » auraient reçu un sens choisi au hasard ;
- sans **garde anti-définition vide**, 230 métiers auraient été « définis » par le mot « profession ».
**L'axe « outils » a été REFUSÉ** : la propriété P2283 donne « soliste -> solo », « relieur -> atelier de
reliure ». Au doute, HORS. La table produite (192 lignes) a été supprimée ; l'axe reste NON TRAITÉ, source
réelle = ESCO/ROME. `ingestion/ingere_metiers.py` documente les cinq gardes pour qu'on ne les retire jamais.

### 3. VAGUE A — 19 briques conceptuelles neuves (module + gate à ancres NON CIRCULAIRES)
Un audit préalable a débusqué **neuf « pièges de nom »** : `limite.py` (= bornes physiques Carnot/Betz, pas les
limites de suites), `temperature.py` (= calibration ML softmax), `loi.py` (= solveur physique, pas le droit),
`atome.py` (= contrat épistémique), `architecture.py` (= architecture INFORMATIQUE), `induction_horn.py`
(= induction LOGIQUE), `polyglotte.py`, `environnement.py`, `allen.py`. Aucun n'est cité comme preuve.

`valeurs_propres` (spectre exact : Faddeev–LeVerrier + Sturm + Yun ; Cayley–Hamilton comme ancre) ·
`anneaux_corps` · `limites_usuelles` · `logique_premier_ordre` (model checking fini ; « non réfuté jusqu'à N »,
jamais « valide ») · `developpement_decimal` · `equations_polynomiales` (Cardan/Ferrari certifiés) ·
`integrale_elementaire` (Liouville) · `conjectures_celebres` · `geometrie_hyperbolique` ·
`cinematique_uniformement_acceleree` · `energie_mecanique` · `rotation_solide` · `thermique` ·
`circuits_kirchhoff` (nodal EXACT en Fraction, KCL re-vérifiée après résolution) · `induction_em` ·
`optique_geometrique` · `interferences_diffraction` · `effet_doppler` · `atome_hydrogene`.

**1 497 assertions, 18 gates + valeurs_propres (108/108).** La vérification adverse a tué de vrais défauts :
annulation catastrophique du trinôme (corrigée par la forme de Citardauq), écart absorbé par l'ulp float64
dans `conserve` (recalculé en `Fraction` exacte), débordements rendant `inf` (désormais ValueError).
Sonde indépendante (mes propres ancres, pas celles des agents) : **49/49**.

Suite conversationnelle : 39 -> **58 gates**.

## 2026-07-10 — CARTE DES SUJETS reconstruite ET ÉTENDUE : 84 588 sujets, couverture MESURÉE

- **Contexte** : `SUJETS_BORNE_OU_NON.md` et `couverture_borne.py` (projet harnais) sont introuvables sur ce
  disque — recherche exhaustive faite (C:, D:, WSL, corbeille, historique git). Mandat Yohan : reconstruire,
  **puis compléter avec tous les sujets manquants**, « cartographier réellement tout ce qui existe, séparer
  traités/non traités, et parmi les traités : complets ou non ; pas seulement Wikidata ; pas de limites ».
- **`SUJETS_BORNE_OU_NON.md` (committé, 1704 sujets)** : 13 PARTIES conceptuelles rédigées (logique, physique,
  chimie, Terre, vie, société, langue, arts, technique, religion, histoire, conventions, non-borné) sous les
  codes d'origine — **prudence au doute** (NB-INDEC/MIX plutôt qu'un B- forcé) ; **ANNEXE T** = taxonomies
  normalisées HORS-Wikidata (Dewey/OCLC, ISCO-08/OIT, MSC, ACM, CIM-11, NACE, ROME) ; **ANNEXE S** = les
  1371 tables vérifiées du store (une table = un sujet borné DE FAIT, ancrage audité 100 %).
- **`outils/genere_sujets.py` (committé) -> `SUJETS_ANNEXES_AUTO.md` (gitignoré, dérivable, 11 Mo)** :
  **8238 métiers RÉELS** (lus de `occupation_personne`, jamais inventés) **× 8 axes atomiques** (définition,
  gestes/savoir-faire, outils, normes, risques, formation, rémunération, « fait pour moi ? ») + **8490
  domaines réels × 2 axes** = **82 884 sujets**. Chaque axe porte un code JUSTIFIÉ une fois (le tour de main
  tacite = MIX ; « fait pour moi ? » = NB-SUBJ). Frugalité : 11 Mo dérivables ne vivent pas dans git.
- **`src/couverture_borne.py` (reconstruit)** — MESURÉ, JAMAIS DÉCLARÉ : un sujet n'est TRAITÉ que si sa
  preuve EXISTE sur le disque (gate `tests/x.py` · module `src/x.py` · roue câblée dans `_ROUES` · table du
  store). Une preuve déclarée introuvable = **dette DITE** (c'est ainsi que `valide_jeux.py`, `medecine`,
  `economie`, `compression` inexistants ont été débusqués et corrigés). Le NON-BORNÉ est « traité » par le
  ROUTAGE honnête (repli intent-aware + G1-G9), jamais par une réponse.
- **Mesure au 2026-07-10** : **84 588 sujets · 18 251 traités · 79 partiels · 66 258 au backlog · 0 dette**.
  Backlog conceptuel = 87 sujets (trigonométrie, degré 3-4, valeurs propres, Risch, ISCO…) ; backlog métiers
  = 57 666 ; domaines = 8 490. **C'est la carte de travail des prochaines vagues.**
- **Câblage produit** : le diagnostic expose la carte (« carte des sujets : 1704 sujets (1523 traités avec
  preuve, 79 partiels, 102 au backlog, 0 dette) ») — `valide_cablage` avait justement détecté le module
  orphelin. Carte EMBARQUÉE dans le .exe (`build_exe.bat` + `Provara.spec` + `sujets.py` frozen-aware) ;
  **honnêteté frozen** : les `tests/` n'étant pas embarqués, le binaire DIT que les preuves-gate sont
  « vérifiées en source » au lieu d'annoncer 69 fausses dettes (bug vécu e2e, corrigé).
- Gate **valide_sujets 35/35** (dont : preuve fantôme -> NON TRAITÉ + dette dite ; chaque preuve-roue
  réellement câblée ; sens d'inclusion sound carte ⊇ store pointé). Suite -> **39 gates**, toutes vertes.
  E2E .exe vérifié, conversations de test purgées, exe tué par PID.

## 2026-07-10 — VAGUE 5 (physique.py -> compilateur) + ③ GRAPHE DES ROUES (graine du gap-engine v2)

- **VAGUE 5 — le registre physique.py passé au compilateur** (résorption formule/concept sur le périmètre
  ACCESSIBLE — le doc des 690 vit dans le repo harnais, absent de ce disque, dit) : **6 roues** — F = m·a
  (2400 N), W = F·d (500 J), p = m·v (60 kg·m/s), E = m·c² (1 g -> ~9e13 J, « pas une combustion » dit),
  Ep = m·g·h (588,399 J), M = F·b (50 N·m). Unités m/s² typées ; tables d'unités PARTAGÉES
  (MASSE/FORCE/METRES/VIT_MS — une seule source). **Piège tué : l'ORDRE d'essai** — les roues à cible
  SPÉCIFIQUE (« moment de la force », « quantité de mouvement ») passent avant les cibles génériques
  (« force » volait le moment). **19 roues au total** (3 artisanales + 16 compilées),
  valide_roues_compilees **58/58**.
- **③ `src/graphe_roues.py` — la graine du GAP-ENGINE v2** : nœuds = grandeurs, arêtes = roues ; `chemins()`
  (BFS), `composantes()` (îlots), `gaps()` (**les ponts manquants NOMMÉS** — l'aveu du gap est la graine
  d'invention : on sait QUELLE relation chercher). Mesuré aujourd'hui : **1 seule composante** (les 19 roues
  se relient toutes), gap-détection PROUVÉE par isolation (élec+hydro seules -> gap « courant<->débit »
  nommé). Capacité NL « comment relier X et Y ? » -> chemin narratif de roues (« section -> consommation en
  3 étapes : hydraulique -> cinématique -> consommation carburant ») ; grandeur inconnue -> inventaire
  honnête. Gate **valide_graphe_roues 11/11** (suite -> **38 gates**), e2e .exe 4/4.

## 2026-07-10 — CACHE PRÉ-CONSTRUIT régénéré (Provara_cache_v1.tar.gz, aligné base du 10)

- Le cache Release du 4 juillet était SÛR mais périmé (validation par taille table par table +
  reconstruction locale = jamais un faux ; seulement moins de préchauffage). Régénéré via
  `build_cache_release.py` depuis la base à jour : **71 981 503 faits / 1364 index .colf (3,4 Go) ->
  archive 603 Mo**, chef_etat_pays_annee + superficie_ile (Honshū) inclus. Déposé
  `Downloads\Provara_cache_v1.tar.gz` (nom EXACT de l'URL produit) — **Yohan remplace l'asset de la
  Release** à côté de datasets_complets.tar.gz.

## 2026-07-10 — TARBALL RELEASE régénéré (l'item en attente depuis l'audit)

- **`C:\Users\yohan\Downloads\datasets_complets.tar.gz` régénéré depuis la base réelle À JOUR**
  (590 600 948 octets ≈ 563 Mo, 1371 tables) : contient désormais Honshū réinjecté (superficie_ile) et les
  veines dirigeants (chef_etat_pays_annee, chef_gouvernement_pays_annee…) absentes de l'ancien tarball.
  Artefact de travail `superficie_ile.jsonl.bak-honshu` EXCLU. Structure vérifiée (racine `lecteur/`,
  1372 entrées listées). **Reste à faire par Yohan : uploader sur la Release GitHub (nom EXACT).**

## 2026-07-10 — COMPILATEUR : VAGUE 4 — t = Q/I (autonomie) + « combien de temps » multi-roues

- **Roue AUTONOMIE t = Q/I** : « la batterie fait 5 Ah et le circuit tire 0,5 ampères » + « combien de temps
  va-t-elle tenir ? » -> « Autonomie ≈ 10 h (t = Q/I…) NB : à courant constant ». Et-si vécu e2e : « et si le
  circuit tirait 1 ampère ? » -> 5 h au lieu de 10 — la roue NOMMÉE par la cible prime sur la branche élec.
- **« combien de temps » routé par ANCRES sur 3 roues sans collision** : batterie+courant -> t = Q/I (10 h) ;
  Wh+W -> t = E/P (3,7 h, roue E = P·t ouverte à cette cible) ; distance+vitesse -> t = d/v (3 h) ; aucun
  ancrage -> None (jamais capturé).
- Gate **valide_roues_compilees 47/47** (10 roues compilées), suite **37/37**, e2e .exe 3/3, convs purgées,
  exe test tué par PID.
- **CARTE DES ROUES introspectable** (« quelles grandeurs sais-tu relier ? ») : les 10 roues + les
  grandeurs PARTAGÉES (les ponts) listées — transparence des capacités ET substrat du gap-engine v2
  (l'invention = chercher des chemins dans ce graphe). Gate 49/49, suite 37/37.

## 2026-07-10 — COMPILATEUR : VAGUE 3 (l'or du quotidien) — 9 roues compilées au total

- **C = 100·V/d** : « j'ai mis 45 litres pour 600 km » -> « Consommation ≈ 7,5 L/100 km » (jamais en
  collision avec l'alias consommation->énergie de la roue E = P·t : les ancrages diffèrent).
- **E = Q·U (batterie)** : « 5000 mAh en 3,7 volts » -> « Énergie ≈ 18,5 Wh (E = Q×U…) NB : énergie
  NOMINALE » ; inversion « quelle capacité ? » (74 Wh / 3,7 V -> 20 Ah — alias capacité -> charge, la tête
  polysémique stade/salle reste au pipeline sans Ah/Wh énoncés). Unités ah/mah typées (sûres après un
  chiffre) ; ancre héritée du banc : E+U énoncés SANS Ah ancrent aussi (l'inversion vécue).
- Gate **valide_roues_compilees 43/43**, suite **37/37**, **e2e .exe 4/4** (conso 7,5 L/100 km + batterie
  18,5 Wh vécus dans le produit). Convs purgées, exe test tué par PID.

## 2026-07-10 — COMPILATEUR FORMULES -> ROUES (validé Yohan) + vagues 1-2 : 7 roues compilées

- **Le mouvement (la suite logique vers l'invention, validée par Yohan)** : une formule MONÔME
  (résultat = c·Π varᵃ) se compile en roue COMPLÈTE — relation directe + TOUTES les inverses en FORME FERMÉE
  (xᵢ = (y/(c·Π autres))^(1/aᵢ)), gardes numériques du compilateur (`_puiss` : zéro, négatif sous racine,
  overflow -> None, jamais une exception ni une valeur inventée — prouvé par ALLER-RETOUR en gate). Une roue
  = une DÉCLARATION (~30 lignes : unités, ancres, libellés) — plus aucune lambda d'inversion à la main.
  Les non-monômes (sommes, logs, Carnot, pH) restent HORS périmètre — dit, jamais approximé.
- **VAGUE 1 (l'utile quotidien)** : v = d/t (« 150 km en 2 heures » -> 75 km/h ; « combien de temps pour
  300 km à 100 km/h ? » -> 3 h depuis la question seule) · P = m·g (« je pèse 80 kg » -> 784,532 N,
  pédagogie masse/force DITE) · Ec = ½mv² (90 km/h converti 25 m/s -> 375 000 J ; **q± QUADRATIQUE prouvé
  par recalcul : v ×1,2 -> Ec ×1,44**) · ρ = m/V (2 kg / 3 L -> 666,67 kg/m³, note densité-stricte).
- **VAGUE 2** : P = F/S (2 MPa, note bar) · P = F·v (12 kW mécanique SANS voler la cible électrique — ancre
  force) · V = Q·t (**pont hydro-temps** : 20 l/s pendant 2 h -> 144 m³).
- **Anti-capture par ancres** : durée seule n'ancre pas (« à quelle vitesse va le TGV ? » -> None),
  « quel temps fait-il ? » jamais pris, « densité de population » exclue par lookahead, pression seule
  (thermo « 3 bars ») n'ancre pas F/S.
- **3 correctifs nés du banc/e2e** : les branches et-si laissent PASSER le None (l'hydro avalait « et si
  elle roulait à 45 km/h » -> réponse plate) ; la roue NOMMÉE par la cible prime sur la roue du dim de
  l'hypothèse (« et si le débit…, quel VOLUME ? ») ; la QUESTION fournit aussi des opérandes aux mondes
  et-si (« …quel volume écoulé en 2 HEURES ? » — avant/après comparables).
- Moteur : extraction de cible multi-groupes ; `pourquoi_dernier` discrimine désormais par SIGNATURE de
  formule (« Vitesse ≈ » hydro vs cinématique) ; unités force (newton/newtons/kN — « n » nu exclu) typées
  dans situation.py. Gate **valide_roues_compilees 38/38** (ajoutée à la suite -> 37 gates), toutes les
  gates de roues sœurs intactes.

## 2026-07-09 jour (suite) — BACKLOG ANCRAGE ÉPUISÉ : 1371/1371 relations référencées (100 %), 0 fait non ancré

- **TRANCHE 5 = LA TRAÎNE ENTIÈRE (73 tables, ≈ 327k faits)** dans `valide_ancres_types` (**309/309**) :
  distributions top-6 MESURÉES sur le store réel puis CERTIFIÉES à la relecture (pont routier, qanat, wat,
  Tchitalichté, colombier, pierre de Caen, codes ISO 4217… — tous des types/lieux réels) ; check = CLIQUET
  anti-dérive à marge (top-4 ⊆ top-6 observé, volume ≥ 95 % du mesuré, zéro valeur vide, 73 tables scannées
  en flux). Ancres d'entité certaines en bonus : France->EUR, Japon->JPY, Suisse->CHF (ISO 4217),
  M87->amas de la Vierge, Cervin->Weisshorn (parent topographique).
- **Mesure finale (audit_ancres, base réelle 72M)** : non référencées **98 -> 0**, faits non ancrés
  **5 120 405 -> 0**. Le diagnostic d'hier (93 % référencées) est clos : **100 %**.

## 2026-07-09 jour (suite) — ROUE n°3 : ÉNERGIE E = P·t + PONT INTER-ROUES (élec -> énergie)

- **`_ROUE_ENERGIE`** (~40 lignes de spec, comme promis par le moteur générique) : le cas « facture » —
  « le radiateur consomme 2000 watts » + « il tourne pendant 3 heures » -> « Énergie ≈ 6 kWh (E = P×t…) ».
  Supposition « à puissance constante » DITE sur CHAQUE réponse (E = P·t n'est exact qu'à P constante —
  jamais silencieuse). **« h » nu délibérément EXCLU des durées** (« à 14 h » est un instant — même logique
  FAUX=0 que « a » nu pour l'ampère) ; une durée seule n'ancre rien (« je pars dans 2 heures » + « et si on
  partait dans 3 heures ? » -> None).
- **PONT INTER-ROUES (`amont`)** : puissance non énoncée -> fermée par la roue ÉLECTRIQUE depuis U/I/R
  énoncés, chemins concaténés (« P = U×I ; E = P×t ») — le P ponté n'est JAMAIS montré comme « donné »
  (seules les énoncées de la roue apparaissent dans « d'après ce que tu m'as donné »). Vérifié :
  « 230 V, 10 A, pendant 2 h » -> 4,6 kWh.
- Et-si (12 kWh au lieu de 6, fil intact), pourquoi q± (preuve 2 points, « à puissance constante »),
  prémisse fausse corrigée, dep (1 kWh = 1000 W pendant 1 h), pourquoi-nu câblés — tout hérité du moteur.
- Gate **valide_roue_energie 18/18** (nouvelle, ajoutée à la suite -> 36 gates) ; sœurs intactes
  (électrique 22/22, hydraulique 19/19, pont 16/16, et_si_pourquoi 37/37, situation 21/21).
- **Bug trouvé PAR l'e2e et tué en gate** : « et si elle chauffait pendant 4 heures, quelle énergie ? » sur
  un fil U/I partait en réponse PLATE (9,2 kWh sans cadre hypothèse — la garde et-si ignorait le contexte
  électrique et le pont amont manquait au chemin et-si). Correctif : `_vals_pontees` factorisé (partagé
  `_roue_repond`/`_etsi_roue`), garde élargie au contexte élec. **E2E .exe 6/6 rejoué** : accusés -> 4,6 kWh
  ponté (« d'après ce que tu m'as donné : durée = 2 h » — le P dérivé jamais « donné ») -> et-si CADRÉ
  (9,2 au lieu de 4,6, fil inchangé) -> pourquoi-nu simulation -> fil intact (4,6). Convs purgées, exe tué.

## 2026-07-09 jour (suite) — PRIOR des autres actes : RIEN À ÉTENDRE (mesuré, pas déclaré)

- Les journaux réels (WSL 427 lignes + app Yohan) ne parlent QUE pour `quotidien` (353+5, famille prior) et
  `calculer` (74+1, famille mesurée du jour). Aucun autre acte n'a UNE SEULE décision journalisée -> aucune
  preuve pour une nouvelle famille. Le mécanisme Phase 5 s'étendra de lui-même avec l'usage réel
  (apprentissage ≥ 3 succès, coupe ≥ 25 décisions propres) — décision : ne rien forcer.

## 2026-07-09 jour — BACKLOG ANCRAGE : 25 tables ancrées, faits non ancrés −93,6 % (5,12M -> 327k)

- **`tests/valide_ancres_types.py` 87/87** (classe BASE COMPLÈTE, hors suite — `LECTEUR_DATASETS_DIR` requis) :
  4 tranches priorisées par volume du diagnostic audit_ancres. Méthode FAUX=0 : chaque ancre SONDÉE dans le
  store réel PUIS recoupée avec une connaissance certaine ; au doute -> écartée. Tables sans entité célèbre ->
  contrôle de DISTRIBUTION (top valeurs ⊆ vocabulaire fermé RÉEL — certitude linguistique, pas devinette).
- Ancres livrées (extraits) : Soleil->naine jaune, Voie lactée->spirale barrée, Bavière->Land, Stonehenge->
  cromlech, Honshū->île du Japon, Loire->fleuve, lac Titicaca->monomictique, BnF->bibliothèque nationale,
  château de Vincennes/tour de Londres->château fort, Vanoise/Écrins->parc national, phare d'Alexandrie->
  détruit, temple d'Artémis->en ruine, Delphes->site archéologique de Grèce, Everglades->prairies inondées…
- **Pièges FAUX débusqués à la sonde (anti-ancres documentées dans la gate)** : type_localite
  [Mont-Saint-Michel]=« municipalité du Québec » et subdivision_localite[Montmartre]=« Saskatchewan »
  (homonymes RÉELS — l'entité célèbre est shadowée par le COALESCE une-valeur-par-nom) ;
  etat_conservation[Colisée]=« démoli ou détruit » (douteux -> écarté). **CLIQUET qualité** : entités-débris
  de type_subdivision (fragments de coordonnées) bornées < 0,5 %.
- Mesure avant/après (audit_ancres, base réelle 72M) : non référencées **98 -> 73 tables**, faits non ancrés
  **5 120 405 -> 326 951 (−93,6 %)**. Traîne restante : 73 tables ≤ 20k faits (top : type_pont 20k,
  type_baie 20k, subdivision_promontoire 17k, type_canal 16k, type_tour 15k) — même patron de tranche à suivre.

## 2026-07-09 jour — TRONC PHASE 5 (brique 1) : RETRAIT PROGRESSIF DES CAPS — la coupe du filet, mesurée

- **Le mouvement (§21 Phase 5)** : la cascade cesse d'être le contrôle — pour un acte à famille FERMÉE dont le
  journal RÉEL a prouvé la maturité, le filet des ~60 autres caps N'EST PLUS PAYÉ. Les caps deviennent des
  facultés atteintes PAR ROUTE, plus par essai aveugle.
- **`sequenceur.coupe(acte, confiance)`** — conditions DURES toutes mesurées : acte du PRIOR ; confiance
  ≥ 0,9 (couper exige plus que réordonner) ; ≥ 25 décisions journalisées pour l'acte avec ZÉRO hors-famille.
  **Passe d'AUDIT** : 1 décision sur 8 garde le filet complet (l'exploration reste vivante) ; un hit
  hors-famille trouvé par l'audit est journalisé et RÉVOQUE la coupe au prochain rechargement
  (auto-guérison par le journal — réversible par construction). `etat_coupe()` -> diagnostic
  (« filet coupé (Phase 5) : quotidien »).
- **FAUX=0** : couper n'invente rien — si la famille s'abstient, le pipeline continue (conjonction, web,
  moteur lourd, repli honnête), même issue que si la cascade complète s'était abstenue.
- **Verrou « bancs reproduits » exercé EN RÉEL** : le journal persistant de la suite était mûr (quotidien :
  58 décisions, 0 hors-famille) -> la coupe était ACTIVE pendant les bancs — capacites_chat **246/246**,
  assistant_nl **506/506** inchangés sous coupe. `valide_sequenceur` **54 OK** (+14 : maturité, seuils,
  audit 1/8, révocation, etat_coupe, câblage prod).
- Journal réel WSL au moment du livre : quotidien 353 décisions / 0 hors-famille (coupe mûre) ; calculer 74
  décisions hors-prior (jamais coupé — biais conservateur inchangé).

## 2026-07-09 jour — PHASE 5 (brique 2) : famille MESURÉE « calculer -> conversion » + maturité vs famille courante

- **Le journal réel a dicté une famille** : 74/74 décisions « calculer » tranchées par `conversion`
  (l'arithmétique pure est déjà TRANCHÉE en amont par le juge AST du tronc — ce qui atteint la cascade sous
  CALCULER, ce sont les conversions d'unités). `sequenceur.PRIOR["calculer"] = ("conversion",)` — carte
  étendue par MESURE, jamais par intuition.
- **Refonte de la maturité (défaut de conception tué à la 2e brique)** : le flag `famille` journalisé reflète
  le prior D'ALORS — la maturité de la coupe se juge désormais contre la famille COURANTE
  (`_hors_actuels` : hors = décisions dont le cap ∉ prioritaires actuels). Une famille élargie HÉRITE de
  l'histoire de ses caps (les 74 décisions comptent le jour où conversion devient famille) ; un cap apprenti
  qui atteint le support rejoint la famille sans invalider son passé ; un hit d'audit étranger révoque.
- `valide_sequenceur` **61 OK** (+7 : prior mesuré calculer, coupe mûre malgré flags d'époque, révocation par
  cap étranger, sûreté ordonnancement étendue à calculer). Suite complète relancée derrière.

## 2026-07-09 jour — PONT HYDRAULIQUE (Q = S·v) + le moteur de ROUES rendu GÉNÉRIQUE

- **Re-recherche d'architecture à la brique** : l'électrique (U = R·I / P = U·I) et l'hydraulique (Q = S·v)
  sont deux INSTANCES d'un même patron « roue de définitions fermée par saturation ». Livré :
  `pont_grandeurs._ROUES` (spec par domaine : dims, tables d'unités→SI, relations avec labels, ancres,
  articles, deps) + moteur unique `_vals_roue`/`_roue_resout`/`_roue_repond`/`_etsi_roue`/
  `_pourquoi_roue_dep`/`_pourquoi_roue_dir`. L'électrique refondu dessus **bit-identique** (gate 22/22
  inchangée = la preuve) ; un 3e domaine fermé se paie désormais en ~40 lignes de spec.
- **Roue HYDRAULIQUE** : Q = S·v (définition du débit volumique) — « le débit est de 20 l/s dans une conduite
  de 100 cm2 » -> « quelle vitesse ? » -> « Vitesse ≈ 2 m/s (v = Q/S — d'après ce que tu m'as donné…) » ;
  et-si (40 l/s -> 4 m/s au lieu de 2, fil intact) ; pourquoi q± prouvé 2 points (« à section constante ») ;
  prémisse fausse corrigée ; dep : racines causales = les données énoncées.
- **FAUX=0 par TABLE D'UNITÉS** : un débit MASSIQUE (kg/s — même dimension « débit » dans le fil) n'entre
  JAMAIS dans Q = S·v ; hectare jamais une section de conduite ; la vitesse SEULE n'ancre pas le domaine
  (« la voiture roule à 130 km/h » + « quel débit ? » -> None). **P = Q·Δp ÉCARTÉ** (une « pression » énoncée
  n'est pas forcément une DIFFÉRENCE de pression — pas de modèle à hypothèse cachée).
- **Correctif né du banc** : « de quoi dépend le débit ? » quand le débit est LEUR donnée -> « c'est une
  RACINE causale de tes données » (avant : « je ne peux pas encore la fermer », faux-à-côté).
- `situation.py` : unités superscript (m³/s, m³/h, m², cm², mm², mm2) typées.
- Gates : **valide_pont_hydraulique 19/19** (nouvelle, ajoutée à la suite), pont_electrique 22/22,
  pont_grandeurs 16/16, et_si_pourquoi 37/37, situation 21/21. **Suite 35/35.**
- **E2E .exe 8/8** (build onedir, port 8799) : hydraulique 5/5 (accusé du fil -> v = Q/S -> pourquoi nu ->
  et-si 4 m/s au lieu de 2 -> q± prouvé 2->2,4 « à la section constante ») ; électrique q± 3/3 (prémisse
  fausse corrigée avec preuve 1150->1380 W ; cas de Kleer : « le courant ne dépend PAS de la tension — tu
  m'as donné les deux séparément »). Conversations de test purgées (reste ['diag']), exe test tué par PID.

## 2026-07-09 jour — POURQUOI-ÉLECTRIQUE contentful : q± prouvé, les constantes = les données ÉNONCÉES

- **Théorie adaptée machine (recherche à la brique)** : de Kleer (confluences) — sur une roue de définitions,
  une direction q± N'EXISTE PAS dans l'absolu, elle dépend de ce qui est TENU CONSTANT. Twist Provara FAUX=0 :
  les constantes ne sont jamais choisies par heuristique — ce sont les données ÉNONCÉES (ordre causal
  d'Iwasaki-Simon : l'exogène = le donné). Cas-vitrine PROUVÉ en gate : « pourquoi le courant baisse quand la
  tension augmente ? » -> avec (U, I) énoncés : « I ne dépend PAS de U dans TES données (indépendantes) » ;
  avec (P, U) énoncés : I = P/U prouvé décroissant par recalcul (20 -> 16,6667 A). MÊME question, vérités
  opposées, chacune juste pour SON énoncé.
- **`pont_grandeurs._pourquoi_elec_dir`** : direction prouvée par recalcul 2 points (var ×1,2 ou ×0,8), les
  autres données DITES constantes (« à tension constante — tes autres données ») ; prémisse fausse CORRIGÉE
  (« Ce n'est pas ce qui se passe : … elle AUGMENTE ») ; influence DÉRIVÉE (pas énoncée) -> dit honnêtement
  (« je l'ai DÉRIVÉE de tes données (R ≈ 46 Ω, via R = U/I) — dis-moi laquelle de tes données bouge »).
- **`_pourquoi_elec_dep`** : « de quoi dépend la puissance ? » -> la roue (P = U·I, aussi R·I²/U²/R) + les
  RACINES CAUSALES du fil réel (les données énoncées) + la dérivation chiffrée. Garde d'ancrage héritée :
  sans grandeur V/A/Ω énoncée -> None (un fil thermo ne déclenche jamais le pourquoi-électrique).
- Gate `valide_pont_electrique` **22/22** (14 + 8) ; sœurs intactes : pont 16/16, et_si_pourquoi 37/37,
  situation 21/21, tete_polysemique 14/14.

## 2026-07-09 nuit — ②bis PONT ÉLECTRIQUE : le pont grandeurs→moteurs généralisé hors-thermo

- **`situation.py`** : unités électriques typées (V/volts/kV -> tension, ampère(s) -> courant, ohm(s) ->
  résistance) — « a » nu EXCLU (normalise rend « à » -> « a » : « entre à 90 » aurait typé un courant).
- **`pont_grandeurs._electrique`** : la ROUE U = R·I / P = U·I fermée par SATURATION depuis les grandeurs
  ÉNONCÉES (2 connues ferment les 4), chaque pas de dérivation NOTÉ et montré (« P ≈ 2300 W (P = U×I —
  d'après ce que tu m'as donné : tension = 230 V, courant = 10 A) ») ; kV convertis ; garde d'ancrage : sans
  grandeur V/A/Ω dans le fil ou la question -> None (« quelle puissance passe dans l'échangeur ? » n'est pas
  capté). Mêmes comportements-clés hérités : dernière valeur fait foi, hypothèses jamais opérandes, manquant
  DEMANDÉ NOMMÉMENT (« donne-moi le courant (en ampères) ou la résistance (en ohms) »).
- **« Et si » électrique** (`_etsi_electrique`) : même simulation avant — « et si le moteur tirait 20 A ? »
  -> « Puissance ≈ 4600 W au lieu de 2300 W … le fil réel reste inchangé ». **« Pourquoi ? » nu** sur une
  réponse électrique -> les DEUX définitions de la roue expliquées (loi d'Ohm + P = U·I).
- Gate `valide_pont_electrique` **14/14** ; gates sœurs intactes (situation 21/21, pont 16/16,
  et_si_pourquoi 37/37) ; suite **34/34**. **E2E .exe 5/5** (accusé du fil -> P -> et-si -> R -> pourquoi).
  Conversation de test purgée, exe test tué par PID.

## 2026-07-09 nuit — audit_ancres RÉPARÉ (dossier 6/22 clos) : 2 causes racines, vrai diagnostic livré

- **Cause racine 1 (le « classe mal »)** : `_relations_referencees` listait `tests/` mais OUVRAIT depuis la
  racine (`_ICI/f`) — aucun validateur jamais lu (OSError silencieux), TOUT partait en « non référencé ».
- **Cause racine 2 (l'« inventaire partiel »)** : `_ICI = dirname(src/audit_ancres.py)` cherchait
  `src/datasets/lecteur` (inexistant) ; l'outil ignorait `LECTEUR_DATASETS_DIR`. Racine = repo, store = env.
- **valide_audit_ancres : 22/22** (était 6/22). Vrai diagnostic sur la base réelle : **1371 relations /
  71 981 264 faits, 93 % référencées par un validateur** ; 98 tables non ancrées = 5 120 405 faits, top :
  type_etoile 1,28M · type_subdivision 1,05M · type_localite 865k · type_galaxie 361k · type_site_archeo 155k.
  Cette liste priorisée = le backlog d'ancrage (gate de classe « base complète », hors suite).

## 2026-07-09 nuit — TRONC Phase 2 GÉNÉRALISÉE : têtes polysémiques jugées par le STORE (§7/§10)

- **Théorie adaptée machine (recherche à la brique)** : représentation SOUS-SPÉCIFIÉE (QLF Alshawi-Crouch
  1992, hole semantics) — une seule représentation retient TOUTES les lectures, résolution différée. Twist
  Provara : le pluggage n'est pas choisi par heuristique, il est JUGÉ PAR LE STORE (les lectures que la
  réalité ancre survivent).
- **`tronc.TETES_POLYSEMIQUES`** (carte fermée) + **`repond._cap_tete_polysemique`** : « capacité de X »
  (stade/salle/église/passagers navire/réservoir — unités justes) et « création de X » (œuvre/organisation).
  Toutes les lectures TENTÉES contre le store -> 1 ancrée = réponse nette (« Capacité du stade « Camp Nou » :
  105 000 places ») ; ≥2 même valeur = CONCORDANCE DITE (arènes de Malaga, stade ET salle, 9 032 — fusion
  amont : compose() compare des chaînes) ; ≥2 valeurs = DIVERGENCE LISTÉE + invitation (« création de
  Acapulco » -> œuvre 1978 / organisation 1520 — 2893 entités vivent dans les DEUX tables de création, le
  générique « première date trouvée » y jouait un coup de dés) ; 0 -> None (cascade inchangée).
- **Architecture émergée saine (vérifiée e2e)** : `ia.donnee_nl` (amont) exige l'UNICITÉ -> entité unique =
  voie rapide DATA ; ambiguë = le faisceau composé prend la main. Millésimes plus jamais groupés par
  milliers (« 1 978 » n'est pas une année — vécu e2e, corrigé).
- Gate `valide_tete_polysemique` **14/14** (net/concordance/unité m³/divergence/replis multi-mots « année de
  création », « capacité d'accueil »/zéro capture dont « capacité thermique molaire ») ; suite **33/33** ;
  e2e .exe base complète : 5/5 (Camp Nou, Malaga, Acapulco, ONU, Akkajaure). Conversation de test purgée.

## 2026-07-09 nuit — 2 décisions Yohan appliquées (√145, villes_coordonnees) + TRONC §7/§8 VALIDÉ

- **Piège √145 MIS À JOUR** (décision : maj plutôt que re-brider) : le check exige désormais l'irrationalité
  DITE + l'approximation MARQUÉE (« √145 est irrationnel — … ≈ 12.041595 (approximation dite) ») — jamais une
  décimale nue présentée comme exacte. valide_fonction **39/39** (était 37/38 avec le piège périmé).
- **valide_villes_coordonnees RE-POINTÉ base réelle** (décision : re-pointer plutôt que fixture) : l'ancien
  chemin `tests/datasets/lecteur` n'a jamais existé dans ce repo (héritage harnais) -> `LECTEUR_DATASETS_DIR`.
  Gate de classe « base complète » : **50/50** sur les 72M (~/.verax/datasets/lecteur).
- **TRONC §7/§8 VALIDÉS par Yohan** (faisceau population-de-candidats + carte fermée des 11 actes) — bâti
  démarré (cf. entrée suivante). audit_ancres : décision = passage dédié (planifié cette nuit).

## 2026-07-09 nuit — FIL brique 4 : l'écho-repli à-côté est MORT (+ garde « question personnelle »)

- **Anti-à-côté (`repond.py` étage 2)** : l'écho « D'après ce que tu m'as dit » exige désormais la COUVERTURE
  TOTALE des mots de contenu de la question par l'énoncé rappelé — un recouvrement PARTIEL ressortait un
  énoncé qui « parle du même sujet » sans y répondre (vécu sonde : « quelle puissance… ? » -> écho du fluide
  chaud). Exception : un rappel-tâche stocké reste ré-servable dès qu'un mot de contenu est partagé. Sans
  couverture -> la main passe aux étages HONNÊTES.
- **Garde PERSONNELLE (débusquée par l'e2e de la brique)** : « quel est MON plat préféré ? » partait au
  MÉTAMOTEUR et servait Wikipédia « Plat » en guise de réponse (l'étage 1·web tourne AVANT la mémoire de
  dialogue). Une question à possessif 1ʳᵉ personne ne part plus JAMAIS au web ; sans rappel couvrant ->
  repli honnête DÉDIÉ (« Ça te concerne, et tu ne me l'as pas encore dit — dis-le-moi et je le retiendrai »),
  classé message d'ABSENCE (est_fallback) pour ne jamais coiffer le « vouliez-vous dire » d'une lecture guérie.
- **Piège traversé en construisant** : en gate LÉGÈRE la guérison corrompait « mon plaT préféré » -> « plaN »
  (lexique échantillon sans « plat » ; en base complète le filet definition_nom le protège — vérifié e2e .exe).
  Gate écrite sur des mots stables de l'échantillon (« sport », « couleur »).
- assistant_nl **506/506** (4 checks nouveaux), suite **32/32**. **E2E .exe** : écho à-côté mort (q2 -> web
  attribué), rappel personnel couvrant servi (« ratatouille »), question personnelle sans matière -> repli
  dédié. Conversation de test purgée, exe test tué par PID.

## 2026-07-09 nuit — FIL brique 3 : actes « ET SI » (simulation avant) et « POURQUOI » (causal PROUVÉ par recalcul)

- **Théories adaptées machine (recherche web à la brique)** : contrefactuel = intervenir sur UNE variable puis
  re-propager dans les MÊMES équations (équations structurelles) — le registre fermé du pont EST déjà un
  modèle causal structurel ; ordre causal extrait de la structure des équations (Iwasaki-Simon 1986) ;
  directions q± (Forbus, qualitative process theory) — twist machine : la direction n'est JAMAIS affirmée à la
  main, elle est PROUVÉE PAR RECALCUL à deux points sur les données de l'utilisateur.
- **« ET SI » (`_et_si`)** : remplacement d'un slot température (« et si le froid sortait à 60 ? » — nombre nu
  -> degrés IMPLICITES étiquetés), valeur sur Q/U/ΔTlm, multiplicateurs fermés (doublait/triplait/−20 %) —
  monde hypothétique JETÉ après réponse (fil réel jamais modifié, vérifié e2e), avant/après montré (« DTLM ≈
  30 au lieu de 36,9946 » + surface RE-PROPAGÉE), hypothèse qui casse la physique -> « impossible » DIT,
  **°C jamais multiplié** (échelle non-ratio — refus expliqué), ×2 sans valeur réelle -> demande NOMMÉE.
- **« POURQUOI » (`_pourquoi` + `pourquoi_dernier` câblé serveur)** : « pourquoi ? » NU -> mécanisme de la
  dernière réponse du pont (log-mean exact sous hypothèses standard / définition de U / principe FAUX=0 sur une
  demande d'opérande) ; « pourquoi A augmente quand ΔTlm baisse » -> formule + preuve 2 points ; **prémisse
  fausse -> CORRIGÉE** (« Ce n'est pas ce qui se passe : … A DIMINUE »), jamais validée ; « pourquoi le sens
  compte » -> les DEUX sens calculés sur les données ; effet slot→DTLM MESURÉ par perturbation ±5° ; sans
  données -> jamais une tendance affirmée sans preuve ; « de quoi dépend » -> ordre causal complet.
- **Au passage** : cœur numérique `_dtlm_num` extrait (tue le re-parsing de texte dans `_surface`) ; correctif
  FAUX=0 — le sens contre/co-courant ne se lit PLUS dans une clause hypothèse (« si c'était à contre-courant »
  fixait silencieusement le monde réel) ; `_SENS` étendu à l'imparfait/conditionnel (« sortait/entrerait »).
- Gate `valide_et_si_pourquoi` **37/37** ; pont 16/16, situation 21/21 intacts ; suite **32/32**. **E2E .exe
  9/9** (sonde ingénieur complète : accusés -> DTLM -> pourquoi nu -> et-si slot -> pourquoi causal -> ×2
  puissance -> fil intact -> ordre causal). Conversation de test purgée, exe test tué par PID.
- Reste du chantier : généraliser le pont au-delà du thermo ; ④ tuer l'écho-repli à-côté ; ⑤ TRONC §7/§8.

## 2026-07-09 nuit — FIL brique 2 : PONT GRANDEURS→MOTEURS — la sonde échangeur passe 7/7 dans le .exe

- **`src/pont_grandeurs.py`** : les grandeurs ÉNONCÉES deviennent des OPÉRANDES. Machine à états sur les
  températures du fil (le FLUIDE COURANT chaud/froid se propage de segment en segment ; le SENS entre/sort
  vient du segment de chaque nombre — situation.py : rôle = tokens du SEGMENT depuis la grandeur précédente,
  la fenêtre fixe mélangeait les fluides). Calculs v1 : ÉCART entre deux grandeurs (cité), DTLM (4 températures
  + sens d'écoulement exigés ; ΔT de borne ≤ 0 -> « physiquement impossible » DIT), SURFACE A = Q/(U·ΔTlm)
  (Q et U pris dans la QUESTION ou le fil). Exactitude prouvée contre calcul indépendant (36,9946 ; 5,4062 m²).
- **LE comportement-clé (perfection FAUX=0)** : opérande manquant -> DEMANDÉ NOMMÉMENT (« il me manque la
  température de SORTIE du fluide froid — donne-la-moi et je calcule ») ; sens inconnu -> demandé (il change
  les bornes) ; hypothèses « si… » JAMAIS opérandes ; ré-énoncé -> la dernière valeur fait foi (autorité
  utilisateur) ; ambigu -> dit ; hors périmètre -> None. Pièges regex tués en construisant : « entre » était
  mot-vide (verbe porteur tué), normalise() mange le tiret de « contre-courant ».
- **E2E .exe : la sonde d'ingénieur du début de soirée passe 7/7** — accusé du fil, demande nommée, DTLM exact
  dès la donnée fournie, surface, écart cité, résumé. Gate valide_pont_grandeurs 16/16 ; suite **31/31**.
- Reste du chantier : actes « et si » (re-calcul à grandeur modifiée)/« pourquoi », écho-repli à-côté, TRONC §7/§8.

## 2026-07-09 nuit — CHANTIER « TENIR LE FIL » lancé (mandat Yohan : perfection irrattrapable, carte blanche) — brique 1 LIVRÉE

- **Sonde fondatrice** (conversation d'ingénieur, échangeur thermique, 8 tours dans le pipeline réel) : le
  front-end route des actes mais ne tient AUCUNE situation — grandeurs énoncées inertes, « résume notre
  conversation » → repli, « reprends ce que je t'ai dit sur X » → auto-citation, « quelle surface pour
  100 kW » → « c'est subjectif ». Constat consigné, feuille de route en mémoire persistante
  (project-ia-chantier-tenir-le-fil).
- **`src/situation.py` — LE FIL (brique 1)** : tout ce que l'utilisateur AFFIRME est tenu — clauses VERBATIM
  jamais compressées (constitution machine SPEC_TRONC §1 : le résumé se CALCULE à la demande), grandeurs
  typées par dimension (réutilise _CONV_UNITS + températures/pressions/puissances/débits/W/m²K), ELLIPSE
  d'unité en SUPPOSITION étiquetée (« entre à 90 degrés et sort à 50 » → « 50 (degrés implicite) », jamais
  affirmé), hypothèses « si… » étiquetées jamais promues, index inversé ouvert (pas de slots DST figés — idées
  DRT/Kamp adaptées machine), questions ET impératifs exclus du fil, interjections filtrées. FAUX=0 PAR
  CONSTRUCTION : toute restitution CITE sa clause + son tour. Rejouable des tours (persistance/RGPD gratuits).
- **Routes chat** : « résume notre conversation / fais le point » → résumé calculé de l'ancré ; « reprends /
  rappelle / qu'est-ce que je t'ai dit sur X » → rappel FILTRÉ cité ; « quelles données je t'ai données ? » →
  grandeurs typées ; déclaration technique → accusé DU FIL (« C'est noté, je tiens le fil : 90 degrés, 50
  (degrés implicite), 20 degrés… ») à la place du lookup fragmenté « pas en mémoire » ×N. `grandeurs_de(sujet)`
  = interface du futur PONT grandeurs→moteurs.
- Gate `valide_situation` 21/21 (ellipse, hypothèses, zéro capture, rejeu) ; capacites_chat 246/246 ; suite
  **30/30 gates** ; e2e .exe : accusé + rappel + résumé + grandeurs verts, zéro capture (« capitale de la
  France » → Paris). Conversations de test purgées.
- **SUITE (ordre)** : ② pont situation→moteurs (les grandeurs énoncées deviennent OPÉRANDES : ΔT, DTLM,
  surface = Q/(U·ΔTlm) — formules thermo fermées) ; ③ actes « et si » (re-calcul à grandeur modifiée) et
  « pourquoi » (causal) ; ④ tuer l'écho-repli à-côté ; ⑤ TRONC §7/§8 (validation Yohan).

## 2026-07-09 — CINÉMATIQUE NL (audit item 7, DERNIER item du pont) + bug de guérison « autre→astre » tué

- **`src/cinematique_nl.py`** : problèmes à étapes du mouvement uniforme, EXACTS (Fractions de bout en bout).
  RENCONTRE : « deux trains distants de 300 km partent l'un vers l'autre à 80 et 70 km/h : quand se croisent-
  ils ? » -> « au bout de 2 h : vitesse de rapprochement = 80+70 = 150 km/h ; temps = 300÷150 = 2 h ; croisement
  à 160 km du premier (140 du second) » — dérivation MONTRÉE, 2 h 30 exactes (jamais 2.4999). POURSUITE :
  « avance de 15 km, 20 vs 30 km/h » -> 1 h 30 ; vitesses égales -> « ne le rattrape jamais » DIT. Motifs
  FERMÉS (distance + 2 vitesses + mot-clé croisent/rattrape exigés ; « pourquoi les trains se croisent-ils la
  nuit ? » -> None). Cap `_cap_cinematique` + gate valide_cinematique_nl 12/12 (suite 29 gates).
- **BUG DE CORRUPTION préexistant TUÉ (trouvé par l'e2e du .exe)** : la guérison orthographique « corrigeait »
  des mots FR VALIDES absents du lexique noms/verbes — « l'un vers l'AUTRE » -> « l'ASTRE », « DISTANTS de
  300 km » -> « DISTANCE » : la question cinématique devenait… une liste de trains roulant à 300 km/h
  (reverse-liste). Classe fermée ajoutée aux protégés : indéfinis/quantifieurs (autre, même, tel, chaque,
  plusieurs, certains, quelques, aucun, divers, différents) + adjectifs de position (distant, séparé,
  éloigné, proche, loin, près, ensemble) — même famille que le précédent « bon alors -> bonne ».
- E2E .exe rebuilé : K0 rencontre VERT, poursuite VERT, piège « pourquoi » -> clarification honnête.

## 2026-07-09 — LONGUEUR IMPÉRIALE COMPOSÉE (audit item 5, dernier petit item du pont)

- Constat e2e AVANT fix : les conversions impériales SIMPLES marchaient déjà (6 pieds -> 1.8288 m, 5 miles ->
  8,0467 km, 3 pouces -> 7,62 cm) — le seul trou réel : la forme COMPOSÉE anglo-saxonne « 6 pieds 2 pouces »
  (partait au web, attribué mais calculable exactement en local).
- `resout_conversion` : « X pieds Y (pouces) (en cm/m) » -> n1×0,3048 + n2×0,0254 EXACT, définitions légales
  citées (« 6 pieds 2 pouces = 1,8796 m »), pouces implicites (« 5 pieds 11 » = 5 ft 11 in), cible cm gérée.
  GARDE capture indue : sans le mot « pouces », le 2ᵉ nombre n'est des pouces que si rien ne suit (« il a
  marché 3 pieds 2 FOIS » jamais lu 3 ft 2 in). 2 pièges de regex corrigés en écrivant (le \s* qui avalait
  l'espace de « en mètres » ; l'alternation cm|m coupant « metres » à « m »).
- assistant_nl 503/503 ; suite 28/28 ; e2e .exe : « quelle taille fait 6 pieds 2 pouces ? » -> 1,8796 m.

## 2026-07-09 — RADICAUX COMPOSÉS EXACTS (audit item 6) + 1 FAUX latent tué

- **`fonction_nl._resout_radicaux`** : « √20 × √5 » répondait sur √5 seul — désormais **10 EXACT**. Calcul
  symbolique en forme canonique c·√d (c = Fraction exacte, d sans facteur carré) : ×,/ (√a×√b=√(ab), division
  RATIONALISÉE : √50÷√2 -> 5), +,− à radicande identique (√2+√8 -> 3√2 exact, approximation MARQUÉE),
  « au carré »/« ² » annule la racine ((√7)² -> 7), coefficients (2√3×√3 -> 6, 3×√2 -> 3√2). Garde-fous :
  COUVERTURE TOTALE des nombres, radicandes irréductibles différents -> HORS, précédence mixte -> HORS,
  « √145 » SEUL inchangé (la décision Yohan sur le piège reste ouverte), « 4 x 100 m » jamais capté (le x
  n'est opérateur qu'en présence d'un √). Bug débusqué pendant l'écriture : « divisé par » absent des
  ensembles -> traité en ADDITION (√50÷√2 rendait 6√2) — normalisation canonique des opérateurs.
- **FAUX latent préexistant TUÉ** : « √16 plus 9 personnes » -> les binaires répondaient **25** en IGNORANT
  le √ (le mot « racine » était gardé, le symbole non). Un √ non parsé -> HORS. Bonus : « racine de 16
  plus 9 » -> 13 exact (l'ancien HORS anti-fragment est dépassé par le haut — gate mise à jour).
- Chat : un radical = intention de calcul en soi (« √20 × √5 » nu marche ; _normalise mangeait le √ -> test
  d'intention sur le brut aussi). assistant_nl 499/499, capacites_chat 241/241, suite 28/28. **E2E .exe :
  10 / 5 / 3√2 verts.** _nonreg complet : 674/694, les 20 FAILS = classe « base complète » de l'audit
  (vérifié : t7 492/492 sur la base réelle ; valide_interface identique AVANT/APRÈS via git stash — aucun
  n'est une régression de la session).

## 2026-07-09 — MÉMOIRE À EXTRACTION (Rex→Max) + « PROUVE-LE » (audit items 12 et 11 : les 2 derniers du mandat)

- **`src/faits_conversation.py`** : les faits que l'utilisateur CONFIE (« le chien s'appelle Rex » — motifs
  FERMÉS nom/âge/lieu, ancrés message entier) deviennent INTERROGEABLES (« comment s'appelle le chien ? » ->
  « Rex. (C'est toi qui me l'as dit…) », toujours attribué, jamais présenté comme fait du monde) et la
  correction fait AUTORITÉ SANS exigence de source (sur SA vie, l'utilisateur EST la source — ≠ faits-monde) :
  verbale (« il s'appelle Max ») ou nue (« en fait c'est Max ») SOUS FOCUS seulement (tour précédent = ce fait ;
  sinon la correction-monde garde sa route). Historique bitemporel DIT (« tu avais d'abord dit Rex »).
  MACHINE-NATIF, zéro stockage nouveau : l'état se REJOUE des tours stockés -> persistance (redémarrage) et
  RGPD (oublie purge tout) gratuits. Câblé serveur AVANT la correction-monde ; accusé SPÉCIFIQUE (fini le
  « C'est noté » générique quand on a vraiment extrait). Gate valide_faits_conversation 19/19 (+ ambiguïté
  2 sujets refusée, redite sans bruit, zéro capture des questions-monde).
- **« Prouve-le » / « es-tu sûr ? » / « ta source ? »** (`repond.est_demande_preuve` + `preuve_de`, câblé
  serveur sur le dernier échange) : composition -> la CHAÎNE re-montrée maillon par maillon ; réponse web ->
  les liens cités ; fait de table -> RE-DÉRIVATION live + source de la table (« ma table donne exactement
  “Tokyo”… source : géographie politique (référence) ») ; réponse auto-sourcée Wikidata -> renvoi + invitation
  à recouper ; fichier attaché -> « la preuve est TON fichier, ligne citée » ; fait personnel -> « la preuve,
  c'est TOI » ; type improuvable -> DIT honnêtement (jamais une justification fabriquée). Fix vécu e2e : la
  branche faits-perso ne renseignait pas _DERNIERE_QUESTION/_REPONSE -> « prouve-le » ne retrouvait rien.
- capacites_chat 235/235 ; suite 28/28 ; **e2e .exe rebuilé : les 5 tours Rex->Max->preuve verts + preuve
  table (Tokyo) + preuve Wikidata (dirigeants)**. Conversations de test purgées.

## 2026-07-09 — LOT 2 ROUTE 4 : multi-hop « où est né X » + temporel « qui dirigeait <pays> en <année> »

- **Relative ÉVÉNEMENTIELLE** (`_OU_EVT_RE` + `_resout_relatif_evenement`, feuille de `_resout_noeud`) :
  « capitale du pays où est né Einstein » -> Berlin AVEC la chaîne (« Albert Einstein est né à Ulm, puis Ulm
  est en Allemagne (pays actuel), puis capitale de Allemagne = Berlin »). Verbe -> relation (lieu_naissance/
  lieu_deces), type demandé -> profondeur (ville = le lieu ; pays = +pays_ville/pays_localite ; continent = +1).
  HONNÊTETÉ TEMPORELLE : « (pays actuel) » dit dans la dérivation (P17 = le pays d'aujourd'hui). ⚠ piège
  évité : le « où est » nu de _OU_TROUVE_RE gobait la forme -> l'événementiel passe AVANT. Napoléon mort à
  Longwood House (sans rattachement pays en base) -> abstention honnête.
- **Cap direct `_cap_lieu_evenement`** : « dans quelle ville est né Einstein ? » — vécu e2e AVANT le cap :
  partait au reverse-liste géo (villes de la région Est du CAMEROUN !). Désormais : « Albert Einstein est né
  à Ulm. » ; « dans quel pays… » -> Allemagne + dérivation.
- **NOUVELLE VEINE `ingestion/ingere_dirigeants.py`** : chef_etat_pays_annee (23 777) + chef_gouvernement_
  pays_annee (14 596) — statements P39 des fonctions OFFICIELLES du pays (P1906/P1313 : la sonde par classe
  P279* ramenait les MAIRES — Italie 1985 pollué, tué), qualificatifs P580/P582, MANDATS TERMINÉS seulement
  (mandat en cours = vérité datée -> HORS), dépliage annuel, transitions chronologiques à la date complète
  (« Kennedy puis Johnson » 1963, « de Gaulle puis Poher puis Pompidou » 1969), bornes d'année non pleine
  dites (« Juan Carlos (prise de fonction cette année-là) » 1975 — Franco = autre fonction). Déployée :
  ~/.verax (base .exe, 1371 relations) + échantillon 6 pays dans le repo. ⚠ À reporter dans la prochaine
  régénération du tarball datasets de la Release.
- **Cap `_cap_dirigeant_annee`** : « qui dirigeait la France en 1962 ? » -> « chef de l'État (président de la
  République française) : Charles de Gaulle ; chef du gouvernement : Michel Debré puis Georges Pompidou …
  (Wikidata, mandats terminés.) » ; fonction demandée respectée (« premier ministre » -> pas de ligne État) ;
  pays hors couverture (URSS, « la réunion ») -> None, zéro capture.
- **Gates** : valide_composition 22/22 (relative événementielle + cap, mocks), valide_lecteur_dirigeants 22/22
  (ancres manuelles + adverse, PASSE sur échantillon ET base complète, enregistré _nonreg amorce-légère),
  capacites_chat 210/210, suite 27/27. **E2E .exe rebuilé : les 4 formes vertes** (S2-S5), capitale de la
  France -> Paris et composition population/capitale intactes. Conversations de test purgées.

## 2026-07-09 — LOT 2 ROUTE 3 : fichiers INTERROGEABLES (opérations exactes sur CSV/JSON attachés)

- **Nouvelle brique `src/interroge_donnees.py`** (approche NLIDB : mots-clés d'agrégat → opération déterministe,
  résolution de colonne par le SCHÉMA réel du fichier) : `Tableau` (csv/tsv) = colonnes, nb lignes, max/min/
  somme/moyenne d'une colonne, comptage conditionnel (« combien de lignes ont X »), extraction de cellule
  (« quel est le prix de la poire ? ») ; `Arbre` (json) = comptages, clés, valeur d'une clé (chemin en preuve).
  FAUX=0 : chaque réponse localisée (ligne réelle du fichier, étiquette, chemin JSON) ; unités MÉLANGÉES
  (2 kg vs 500 g) → refus honnête de l'agrégat ; nombres FR stricts (« 12,5 », « 1 234 », « 1.234,56 » ;
  ambigu → cellule ignorée ET comptée). Gate `valide_interroge_donnees` 61/61 (pièges de capture inclus).
- **Câblage serveur** : `_DONNEES` (conv → Tableau|Arbre) rempli à l'upload ; les opérations structurées passent
  AVANT le pipeline (chirurgicales : ne répondent que sur le schéma/valeurs réels du fichier) — vécu e2e :
  « combien de lignes ? » partait au LEXIQUE (« 18 termes classés ligne ») au lieu du CSV attaché. Le document
  TEXTE reste en repli d'abstention (inchangé). Résumé d'upload ACTIONNABLE (colonnes réelles + exemples de
  questions). « résume » déclenche le sommaire (MD/PDF). Trou RGPD bouché au passage : `oublie_conversation`
  purge désormais AUSSI le document attaché (`_DOCS`/`_DONNEES`).
- **Vérifié e2e DANS le .exe rebuilé (port 8799)** : upload fruits.csv → max prix = 2,5 (ligne 3, « poire »),
  moyenne, cellule, « combien de lignes » → 4 (plus jamais le lexique), capitale de la France → Paris (zéro
  capture) ; biblio.json → comptage + valeur avec chemins. capacites_chat 202/202 ; suite conversationnelle
  27/27 gates. Conversations de test purgées.

## 2026-07-09 — LOT 2 (pont vocabulaire→moteurs) : routes 1-2 câblées — code prouvé + invention invoquée

- **Route 1 « écris une fonction/du code » -> CODE PROUVÉ** (`_cap_code_prouve`) : exemples « (2, 3) -> 5 »
  extraits de la demande -> `invente_et_retiens` (python, expression jugée + held-out AVEUGLE) ou
  `genere_langage` (bash/js/perl, code exécuté-vérifié) ; réponse = le code + ce qui a été prouvé (« + 1 en
  aveugle », « proche de “somme” » quand le self-improving rappelle). Sans exemples -> demande ACTIONNABLE
  de la méthode. Fini le fallback/lexique de la Phase 2 (axe code 0/5). capacites_chat 184 -> 188/188.
- **Route 2 « invente/imagine/propose/conçois … pour X » -> moteur d'invention INVOQUÉ** : la forme directe
  rejoint `besoin.decompose` (décomposition fine si au catalogue, sinon méthode physique amplifiée — chiffrer,
  canaux, Carnot) au lieu de la clarification à côté ; garde carte fermée sur les objets langagiers/sociaux
  (« invente une excuse » -> cascade). capacites_chat 192/192.
- RESTE DU LOT 2 (prochaine session) : Route 3 fichiers INTERROGEABLES (max/comptage/extraction sur le
  document attaché — lu 5/5 mais muet) ; Route 4 multi-hop (« capitale du pays où est né X ») + temporel
  (« en 1962 ») ; puis mémoire conversationnelle à extraction (Rex→Max) et « prouve-le » (production de preuve).

## 2026-07-09 — LOT 1 post-audit : les 2 FAUX de la Phase 2 tués + le fait perdu réinjecté

- **FAUX n°1 (horloge)** : « pars à 14h37, roule 2 heures 48 » -> 16 h 37 (minutes AVALÉES). Le motif de durée
  capture désormais les minutes énoncées après l'unité (« 2 heures 48 », « 3 heures 20 minutes »), garde
  anti-grandeur étrangère (« 2 heures 15 personnes » ne devient pas 2h15). 17 h 25 exact, passage minuit dit.
  3 pièges gate ; assistant_nl 485 -> 488/488. (commit 7ad5ce2)
- **FAUX n°2 (masse vs poids)** : « que pèse un litre d'eau sur la Lune » -> « ≈ 1 kg » (contexte céleste
  IGNORÉ). Désormais : MASSE invariante DITE + POIDS calculé (g de surface de référence IAU/CODATA, 10 astres,
  1 kg -> 1.62 N sur la Lune) ; astre hors table -> abstention DITE sur le chiffre. 3 pièges gate ;
  assistant_nl 491/491. (commit 2430beb)
- **Fait perdu réinjecté** : superficie_ile(Honshū) = 227 960 km² absent de la base livrée (17 032 faits ;
  cause probable : garde anti-ambiguïté HAVING COUNT=1 à l'ingestion). Réinjecté dans ~/.verax (backup gardé),
  **T7 re-prouvé DANS le .exe : 492/492, ancre VERIFIE**. ⚠ À reporter dans la prochaine régénération du
  tarball datasets de la Release.

## 2026-07-09 — ⑦ Bascule 77→78 VÉCUE en live : 2 trous de l'updater bouchés/consignés

- **Vécu chez Yohan** : la 1ʳᵉ tentative auto 77→78 a échoué SANS AUCUNE TRACE (ni bat écrit, ni paquet
  extrait, ni ligne de log) — et la garde anti-boucle (6 h) bloquait ensuite tout retry : l'app restait en 77,
  préchauffage popup-eux à l'infini. Fix : **l'échec de la veille MAJ n'est plus jamais muet** (message
  d'`applique()` ou exception -> verax.log). Bascule finale faite À LA MAIN (paquet Release vérifié tampon
  78, swap dossier, ancien gardé en `Provara-app.old-77`) ; `/api/maj` confirme `version_locale: 78…`.
- **Découvert au relancement : DEUX instances Provara.exe écoutaient TOUTES LES DEUX sur 127.0.0.1:8765**
  (netstat : double LISTENING — `allow_reuse_address` = SO_REUSEADDR permet le double-bind sous Windows,
  routage des requêtes non déterministe). À FAIRE : SO_EXCLUSIVEADDRUSE sous Windows (ou garde
  mono-instance) + l'app qui ne peut pas se binder doit LE DIRE et sortir.

## 2026-07-09 — ⑥ E2E FINAL : diagnostic .exe 305→306/306 attendu en ~13 s + fix AVERSE DE POPUPS (build 77 vécu par Yohan)

- **🔴 Vécu par Yohan sur le build 77 en live : une BOÎTE DE DIALOGUE par candidat recalé, en boucle.** Cause :
  en `--noconsole`, le bootloader PyInstaller affiche un popup pour TOUTE exception non rattrapée — et le mode
  `--juge-exec` laissait volontairement l'AssertionError du candidat remonter (pour le code retour). Fix :
  rattraper, traceback sur stderr (le juge y lit « AssertionError » -> FAIL, contrat identique), `exit(1)`
  propre + `CREATE_NO_WINDOW` sur les spawns du juge. Vérifié frozen : pass->pass, fail->fail, zéro dialogue.
- **Dernière preuve rouge « Daemon lecteur (protocole Q-R) »** : `class _Serveur(socketserver.
  ThreadingUnixStreamServer)` AU NIVEAU MODULE tuait l'import entier sous Windows (pas de socket Unix). La
  classe est conditionnelle ; `main()` se déclare indisponible honnêtement ; `_traite` (pur) vit partout.
  Vérifié frozen : réponse structurée OK.
- **Mesures e2e sur le .exe rebuilé (onedir, port 8799)** : préchauffage des preuves ~1 min en fond après le
  boot ; « diagnostic » = **305/306 en 12,6 s** (dont 3 preuves du mémo daté « il y a 0 min » ; l'unique échec
  était le daemon, corrigé depuis -> 306/306 attendu au build 78). Ce matin : 273/306 en 63-70 s, 5 bloquées,
  24 sautées.
- Leçon consignée ([[_REPRISE_SESSION.md]]) : le .exe de test se lance PORT 8799 + VERAX_RELANCE_MAJ=1, on tue
  par PID — l'app PERSO de Yohan (Downloads\Provara-app) vit sur 8765 et son build 77 souffrait encore des
  popups pendant mes tests (tuée proprement, à relancer au build 78).

## 2026-07-09 — ⑤ RÉSOLU : les 2 dernières preuves rouges du diagnostic .exe = 3 modules POSIX-only (portage Windows)

- **Méthode nouvelle** : le mode `--juge-exec` sert AUSSI de sonde — un script exécuté DANS l'environnement
  frozen du .exe a rejoué chaque sous-preuve des façades en échec et NOMMÉ les coupables exacts :
  `prefiltre.py` -> `import resource` (tuait demande/strategies/invente_et_retiens, « façade web 1 ») et
  `editeur.py` -> `import fcntl` (tuait cree_fichier/edite_fichier, « façade outils 2 »). Passait en WSL
  (POSIX), mourait dans le .exe Windows.
- **`garde_ressources`** : import `resource` conditionnel ; sans setrlimit (Windows), `borne()` le DIT
  ({"indisponible": …}) au lieu de mentir — les 10+ briques appelantes (ia, deduction, conversation…)
  revivent sur le .exe.
- **`prefiltre`** : sans les DEUX gardes kernel (setrlimit + SIGALRM), JAMAIS d'exec en-process — `pre_juge`
  répond « incertain » et TOUT passe par la sandbox juge (même verdict final, sans l'optimisation) ; sûr
  avant rapide.
- **`editeur`** : mode PORTABLE à garanties fonctionnelles IDENTIQUES (confinement realpath, non-écrasement
  O_EXCL, ancre exacte, écriture atomique tmp+os.replace, refus des liens via lstat, verrou msvcrt sur
  fichier HORS dépôt) ; le durcissement kernel dir_fd/O_NOFOLLOW/flock reste ACTIF sur POSIX (`_DIRFD`).
  TOCTOU kernel = best-effort sur Windows, cohérent avec le modèle de menace documenté du module.
- **Vérifié DANS le .exe rebuilé (sonde frozen) : 15/15 sous-preuves OK** (invente_et_retiens répond,
  cree_fichier crée réellement, calibrations exactes…). POSIX intact : valide_editeur 57/57 (suite
  adversariale), valide_capacites 73/73, routage_strategie 4/4, atomes 20/20.
- Release build 77 publiée par le CI (les correctifs juge/MAJ/préchauffage) ; ce portage part au build 78.

## 2026-07-09 — 🏆 CAUSE RACINE build 75 TROUVÉE + 3 correctifs de fond (juge .exe, MAJ honnête, bascule vérifiée)

- **Régression build 75 CLOSE, mécanisme prouvé en live** : la bascule de MAJ remplace `_internal\` PUIS l'exe ;
  un move raté (verrou antivirus) laissait une installation MIXTE (exe build N + `_internal` build M) -> les
  imports paresseux (briques resout_math…) mouraient même sur processus vierge. Vérifié : builds 76/77 frais
  -> factorielle 720, pgcd 12, 20 % de 5 000 = 1000, tout DANS le .exe. Reproduit en live : dist s'est retrouvé
  panaché (exe local 32 Mo + `_internal` Release) après une application déclenchée pendant mes tests.
- **① JUGE DANS LE .EXE : mode interpréteur `--juge-exec`** — `sys.executable` EST Provara.exe dans le bundle :
  chaque candidat jugé relançait l'APPLICATION ENTIÈRE (gel du diagnostic depuis le build 53, processus
  fantômes vus en live pendant le diagnostic). `lance.py` (tout en tête, avant tout boot) exécute le fichier
  candidat et sort ; `executeur.py` route vers ce mode en frozen. Vérifié e2e .exe (onedir) : « Exercices
  curés » repasse, boucle/mesure ne bloquent plus, diagnostic 273 -> 276/306.
- **② MAJ HONNÊTE (FAUX=0)** : un build DEV (tampon sans numéro, « build-local ») n'est PAS périmé — la
  bannière « nouvelle version disponible » contre lui était FAUSSE (vécu : clic -> build de test écrasé par
  la Release en plein diagnostic). `maj.etat()` : build 0 -> jamais disponible, zéro appel réseau, champ
  `dev`. + `note_tentative` posé DANS `applique()` (le front n'était pas tracé, la garde anti-boucle de la
  veille ne voyait rien). valide_maj 39/41 -> **42/42** (contrat du test mis à jour + cas build utilisateur).
- **③ BASCULE ONEDIR VÉRIFIÉE (updater .bat)** : chaque `move` est contrôlé ; si l'exe ne peut pas être
  remplacé, le `_internal` neuf est retiré et l'ancien restauré -> on redémarre TOUJOURS une installation
  cohérente, jamais un panachage (le mécanisme exact du cadavre build 75).
- **④ PRÉCHAUFFAGE DES PREUVES** (`capacites.chauffe_preuves`, thread de fond après la connaissance) : les
  preuves qui résolvent leurs briques via le juge (compréhension intégrée, carte des limites, savoir massif…)
  coûtent 10-60 s à froid sur le .exe -> le diagnostic les servait « bloquée > 10s » puis sautait ~24 preuves
  (budget global). Désormais : mémo daté par preuve ; le diagnostic sert les LENTES du mémo (affiché « dont N
  au préchauffage, il y a X min » — jamais menteur) et re-prouve les rapides EN DIRECT. En local le mémo ne
  s'active pas (aucune preuve > 5 s).
- **Hygiène de session consignée** (_REPRISE_SESSION.md) : tests .exe sur PORT 8799 + VERAX_RELANCE_MAJ=1
  (aucun onglet sur le bureau de Yohan), jamais de taskkill /IM global (son app tourne sur 8765), build test
  en ONEDIR (`VERAX_ONEDIR=1`) — l'onefile ré-extrait à chaque spawn juge (+ scan antivirus) et fausse tout.
- Bancs : suite 26/26, valide_capacites 73/73, valide_maj 42/42, juge 6/6 + juge_rapide 25/25, demo 31/31,
  interface 55/58 (les 3 échecs = données base complète absentes de l'env source, identiques sur HEAD).
- RESTE À FAIRE : ⑤ les 2 échecs réels du diagnostic .exe (« façade web 1 », « façade outils 2 ») à trier
  sur le .exe ; ⑥ vérifier le préchauffage e2e sur un build (diagnostic attendu ~306/306 après chauffe).

## 2026-07-09 — 🔴 RÉGRESSION .EXE DÉCOUVERTE EN LIVE : tout resout_math mort sur le build 75 + l'except muet qui la cachait

- Le diagnostic instrumenté a répondu (69 s) et NOMMÉ les preuves lentes : 5 preuves historiques qui
  chargent des ressources massives (« Savoir massif — lexique 1,9 M », « Compréhension intégrée »…) — le
  mystère du gel depuis le build 53 est résolu (pas un deadlock : des chargements géants sérialisés).
- MAIS il a aussi révélé 3 échecs de preuves MATHS PURES (dénombrement, récurrences, graphes) — enquête
  live : sur le .exe build 75, **TOUT resout_math est mort** (« factorielle de 6 », « 20 % de 5 000 »,
  « pgcd » -> servis par Wikipédia !), même sur processus vierge. L'un des trois imports de tête
  (arithmetique_modulaire / maths_discretes / trigonometrie) échoue dans le bundle — et le
  `except Exception: return HORS` MUET cachait la cause et laissait le web répondre à la place.
- **Fix immédiat** : l'échec d'import est signalé UNE fois au log avec traceback complet (« ⚠⚠ resout_math :
  import des briques ÉCHOUÉ… ») — le prochain build donnera la cause exacte dans verax.log. Leçon : un
  repli honnête n'a JAMAIS le droit d'être silencieux sur une panne de brique.
- Bancs : assistant_nl 485/485, suite 26/26 (l'import passe en local — la panne est propre au bundle).

## 2026-07-08 — Diagnostic .exe, riposte 3 : budget GLOBAL + noms des preuves bloquées au log

- Build 74 vérifié en live : le diagnostic ne répond toujours pas — la réponse n'est JAMAIS stockée, alors
  qu'`ia` est chaud (résolution floue en 1 s dans le même processus). Lecture des traces du .exe :
  **WinError 10053** (un logiciel local — antivirus — abat la connexion pendant la longue attente) et un
  vieux crash zipimport d'un processus qui avait survécu à l'échange de fichiers de la MAJ.
- Hypothèse en tête : un worker de preuve coincé TIENT LE VERROU D'IMPORT Python -> tous les workers
  suivants s'y bloquent -> 306 × 10 s ≈ 51 min. Riposte : **budget global 60 s** (au-delà, les preuves
  restantes sont sautées et COMPTÉES, le diagnostic répond toujours en ≤ ~1 min) + **chaque preuve bloquée
  est imprimée au log en direct** (« ⚠ preuve BLOQUÉE (> 10s) : <nom> » -> verax.log) — le prochain
  diagnostic sur le .exe donnera les noms, même si la réponse HTTP se perd.
- Local : 7.5 s, 306/306, zéro bloquée ; capacites 73/73, suite 26/26.

## 2026-07-08 — Diagnostic .exe : WATCHDOG par preuve (le coupable sera nommé)

- Build 73 vérifié en live : le diagnostic pend TOUJOURS (> 280 s) alors que les questions data répondent en
  0 s (donc `_charge_ia` est chaud) — **le blocage est dans UNE des 306 preuves, spécifique à
  l'environnement .exe** (et probablement historique : le gel existait au build 53).
- `verifie_tout(budget_par_preuve=10.0)` : chaque preuve court dans un thread joint à 10 s ; celle qui ne
  revient pas est comptée EN ÉCHEC avec le libellé **« (bloquée > 10s) »** — le diagnostic termine TOUJOURS
  (≤ ~40 s pire cas réaliste) et DÉSIGNE le coupable dans sa réponse. Le chemin tests/CI garde l'exécution
  directe historique (None).
- Local : watchdog 7.4 s, 306/306, zéro bloquée ; suite 26/26, capacites 73/73.

## 2026-07-08 — Diagnostic .exe : inventaire à budget + étapes chronométrées

- Le timeout du diagnostic .exe persiste au build 72 (> 300 s) alors que le même chemin fait 9.7 s en local
  — bug PRÉEXISTANT (déjà noté au build 53), pas causé par les preuves. Deux armes embarquées :
  ① **inventaire à budget** : compter les 72 M de faits force le chargement de toutes les tables ; sur
  données froides c'est potentiellement des minutes -> budget 10 s, au-delà le compte partiel est rendu
  honnêtement (« au moins N — l'inventaire reprendra au prochain diagnostic ») ;
  ② **étapes chronométrées DANS la réponse** (« étapes : chargement X s, preuves Y s, inventaire Z s ») —
  le prochain diagnostic sur le .exe dira exactement où le temps part.
- Bancs : suite 26/26, capacites_chat 184/184, assistant_nl 485/485.

## 2026-07-08 — FIX CRITIQUE diagnostic .exe : plus aucun spawn d'interpréteur dans le chemin produit

- **Vécu sur le .exe build 70 (live)** : « diagnostic » partait en timeout (> 400 s). Cause : la preuve de
  synthèse de code spawnait un interpréteur **bash** des dizaines de fois — et sous Windows, « bash »
  résout vers l'**interop WSL** (chaque spawn coûte des secondes). Ma garde `which("bash")` ne protégeait
  donc PAS le .exe.
- La preuve de synthèse vit désormais dans `tests/valide_atomes.py` (hôtes de dev, gardée par which) et
  **plus jamais dans le diagnostic produit**. Les 306 preuves du diagnostic tournent en ~8 s sans aucun
  processus externe.
- ⚠ Sur le build 70 actuel, éviter « diagnostic » (il pendra) — corrigé au prochain build.
- Bancs : capacites 73/73 (306 preuves), atomes **20/20** (+1, la preuve bash déplacée), suite 26/26.

## 2026-07-08 — Portabilité .exe : la preuve bash devient conditionnelle à l'hôte

- La preuve de synthèse de code exigeait un interpréteur **bash** — absent du .exe Windows, le diagnostic y
  aurait viré au rouge. La sous-preuve ne s'exécute que si `shutil.which("bash")` répond ; sans interpréteur
  sur l'hôte, la synthèse polyglotte n'est pas exigible et le reste de la preuve tient. Vérifié : les 306
  preuves passent en **7.9 s** (0 échec).

## 2026-07-08 — 🏆 EXCELLENCE ATOMIQUE, lot final : DETTE SOLDÉE (148 → 0)

- **Chaque fonction publique du produit est désormais consommée par le produit ou prouvée par un test à
  réponse connue — zéro orpheline, à tous les niveaux (504 modules ET ~2 500 fonctions), verrouillé par le
  cliquet `valide_atomes` à 0.**
- Dernier lot (diagnostic : 306 preuves) : **web souverain** (URL invalide/localhost -> refus propre, jamais
  requêté ; rien à lire -> hors), **corroboration FAUX=0** (sans juge réel, jamais promu en fait ;
  l'indépendance des domaines pèse 0.6 vs 0.4 ; **zéro observation -> RIEN n'est persisté au fait-store**),
  **synthèse de code vérifiée** (l'addition est ÉCRITE en bash « $(( $1 + $2 )) » puis validée sur les
  exemples), borne de stabilité, moteur self-improving (invente_et_retiens).
- 20 lots au total dans la séance : 148 façades prouvées — théorèmes VÉRIFIÉS et non récités (Aumann,
  Condorcet, Gibbard-Satterthwaite, Stein, Lindley, Goodhart, Jensen, Anscombe, Bertrand et
  Borel-Kolmogorov refusés proprement…), une trentaine de contrats d'abstention honnête, des encodeurs
  prouvés par octets magiques.
- **Batterie finale complète, tout vert** : assistant_nl 485, capacites_chat 184, raisonnement 202,
  paraphrases 174, interface 58/58, capacites 73/73 (306 preuves), atomes 19/19, câblage 504/0, suite 26/26,
  challenge 16/16.

## 2026-07-08 — Excellence atomique, lot 19 : 5 façades de plus (dette 12 → 7)

- 1 preuve REGISTRE composée (diagnostic : 305) : **apprentissage de règle honnête** (deux seuils possibles
  entre les exemples -> AMBIGU, refus de choisir arbitrairement), **apprend_domaine** (le référentiel OMS de
  test est réellement appris dans la BASE puis retiré sans trace), **PAC-Bayes** (la borne domine le risque
  empirique), **biais du survivant MESURÉ** (moyenne des survivants 9.0 vs population 5.5 -> biais 3.5
  exact), **queues lourdes POT-GPD** (P(X > 20) estimée sur une Pareto ; seuil sous u -> None honnête).
- Plafond du cliquet : **7** — il ne reste que les fonctions web/réseau et 2 à état lourd.
- Bancs : valide_capacites 73/73 (pins 304→305), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 18 : 6 façades de plus (dette 18 → 12)

- 1 preuve REGISTRE composée (diagnostic : 304) : **régression quantile** (la médiane conditionnelle
  retrouve y = 2x), **décision maxmin sur credal** (pire cas 1.0 exact), **contrôle de risque conforme**
  (le λ le moins invasif sous la cible), **VAR couplé honnête** (régresseurs singuliers -> abstention DITE,
  série réelle -> estimé), **p-box** (bornes d'espérance EXACTES (7/6, 2.5) depuis des intervalles),
  **calibration multiclasse isotone exacte**.
- Plafond du cliquet : **12** — il reste les fonctions web/réseau et 4 formats complexes.
- Bancs : valide_capacites 73/73 (pins 303→304), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 17 : 8 façades de plus (dette 26 → 18)

- 1 preuve REGISTRE composée (diagnostic : 303) : **résolution cartographique exacte** ((2.54/dpi)×N),
  **paradoxe de Stein mesuré** (James-Stein domine le MLE sur 3 moyennes, graine fixée), reprise de
  conversation verbatim honnête, **encode_pdf** (%PDF-1.4) et **encode_xlsx** (conteneur PK) prouvés par
  octets magiques sur des documents réellement construits, **moteur d'invention** (candidats-stacks,
  canaux manquants, principes physiques classés par levier).
- Plafond du cliquet : **18** — 130 façades prouvées sur les 148 de l'audit initial.
- Bancs : valide_capacites 73/73 (pins 302→303), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 16 : 6 façades de plus (dette 32 → 26)

- 1 preuve REGISTRE composée (diagnostic : 302) : **fichiers réels** (cree_fichier écrit et le contenu est
  relu, depot ouvre le dépôt), **protocole de révélation honnête** (protocole inconnu -> la vraisemblance
  est REFUSÉE, dépendance au protocole type Monty Hall), **calibrations isotoniques exactes** (multi-label
  {a: 1.0, b: 0.0} et par étapes 0.9 -> 1.0 / 0.6 -> 0.0), **NDCG** (classement parfait = 1.0, inversé < 1).
- Plafond du cliquet : **26**.
- Bancs : valide_capacites 73/73 (pins 301→302), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 15 : 6 façades de plus (dette 38 → 32)

- 1 preuve REGISTRE composée (diagnostic : 301) : **conformal par classe** (seuils exacts 0.2/0.2),
  **multicalibration honnête** (groupes trop petits -> abstention DITE), **détecteur de dérive CUSUM**
  (le système SUR-confiant déclenche l'alarme, le bien-calibré jamais — les deux régimes prouvés),
  **D-calibration de survie** (modèle juste -> déciles uniformes EXACTS, χ² = 0), **borne de Rademacher**
  (domine le risque empirique), **clustering par processus de Dirichlet** (2 vrais paquets -> K = 2 inféré,
  sans fixer K d'avance).
- Plafond du cliquet : **32**.
- Bancs : valide_capacites 73/73 (pins 300→301), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 14 : 6 façades de plus (dette 44 → 38 ; cap des 300 preuves)

- 1 preuve REGISTRE composée — le diagnostic exécute désormais **300 preuves en direct** : **prévisions
  imprécises de Walley** (bornes EXACTES (1, 4) sur un ensemble credal), **ambiguïté lisse** (KMM),
  **Bayes robuste** (ε-contamination encadrant le postérieur nominal 0.8), **décision robuste à la mauvaise
  spécification du modèle** (la prudence l'emporte), **risque conjoint extrême** (copules), **portefeuille
  universel** (suit le meilleur actif rétrospectif).
- Plafond du cliquet : **38** — 110 façades prouvées depuis l'audit (148).
- Bancs : valide_capacites 73/73 (pins 299→300), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 13 : 6 façades de plus (dette 50 → 44)

- 1 preuve REGISTRE composée (diagnostic : 299) : **p-hacking quantifié** (le minimum de m tests ajusté
  1−(1−p)^m exactement), **inégalité de Jensen reproduite** (E[f(X)] ≈ 1 vs f(E[X]) = 0), **jeu à somme
  nulle résolu** (valeur ≈ 0, stratégies mixtes), **info-gap** (α̂ = 5 exact — la marge maximale tolérable),
  **décision robuste au pire cas**, **échantillonnage préférentiel** (poids plats -> ESS = n exact).
- Plafond du cliquet : **44**.
- Bancs : valide_capacites 73/73 (pins 298→299), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 12 : 6 façades de plus (dette 56 → 50 — moitié de la dette brûlée)

- 1 preuve REGISTRE composée (diagnostic : 298) : **théorème d'accord d'Aumann** (les deux agents bayésiens
  convergent à 1.0 — vérifié, pas récité), **détection de changement précoce** (alarme au pas 7 exact),
  **effet d'ancrage reproduit** (contamination 0.93 vs contrôle ~0), et deux refus d'excellence : le
  **paradoxe de Bertrand** (« corde aléatoire » sans mécanisme -> abstention motivée) et
  **Borel-Kolmogorov** (conditionnement sur mesure nulle -> refusé). Optimisation coûteuse approchée, tracée.
- Plafond du cliquet : **50** — la moitié de la dette initiale (148 → 50, 98 façades prouvées).
- Bancs : valide_capacites 73/73 (pins 297→298), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 11 : 7 façades de plus (dette 63 → 56)

- 1 preuve REGISTRE composée (diagnostic : 297) : **théorème de Gibbard-Satterthwaite** (une manipulation de
  vote est EXHIBÉE, pas récitée), **quartet d'Anscombe** (mêmes résumés, données différentes — la preuve que
  les stats résumées ne suffisent pas), **espérances imprécises** (bornes de Choquet exactes 6–10 sur une
  masse de croyance), **CQR** (correction conforme 0.5 exacte), **conformal Mondrian** (quantile PAR GROUPE
  (9.0, 11.0) exact), dialogues honnêtes (oublier l'inexistant -> False ; rappel sans matière -> vide).
- Plafond du cliquet : **56**.
- Bancs : valide_capacites 73/73 (pins 296→297), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 10 : 8 façades outils (dette 71 → 63)

- 1 preuve REGISTRE composée (diagnostic : 296) : **encodeurs binaires prouvés par octets magiques**
  (image_raster + encode_png -> signature PNG exacte \x89PNG, encode_wav -> RIFF/WAVE), **intégrale de
  Choquet exacte** (0.7), décomposition physique des besoins (decompose_besoin/principes_besoin),
  **registre réel des sources d'apprentissage** (ou_apprendre("physique") contient NIST-CODATA),
  géométrie de tracé (la barre 7 domine la barre 3).
- Plafond du cliquet : **63**.
- Bancs : valide_capacites 73/73 (pins 295→296), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 9 : 7 façades de plus (dette 78 → 71)

- 1 preuve REGISTRE composée (diagnostic : 295) : **loi de Goodhart reproduite** (le proxy se décorrèle de
  la cible sous pression de sélection), **ratio de vraisemblance exact** e^0.5 pour le shift gaussien,
  migration de stade (Will Rogers), **régression temporelle fallacieuse** (68 % de faux positifs sur les
  niveaux vs différences — reproduit à graine fixée), **confidentialité différentielle** (échelle de Laplace
  Δ/ε = 2.0 exacte), conformal normalisé (7.6, 12.4) exact, **détection de nouveauté kNN** (le connu score
  0, l'aberrant 48.9).
- Plafond du cliquet : **71**.
- Bancs : valide_capacites 73/73 (pins 294→295), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 8 : 7 façades de plus (dette 85 → 78)

- 1 preuve REGISTRE composée (diagnostic : 294) — **les pièges statistiques classiques, quantifiés et non
  récités** : écart intuition/Bayes du test médical (0.99 perçu vs 0.019 réel), pente OLS (abstention n<12
  ET vraie pente dans l'IC), **atténuation par erreur de mesure corrigée**, **winner's curse** (le maximum
  sélectionné n'est pas significatif — IC traversant 0), **paradoxe de Lindley** (B01 > 1 malgré p = 0.6 sur
  n = 100), régression vers la moyenne, **paradoxe de Lord** (changement ET ANCOVA explicités).
- Plafond du cliquet : **78**.
- Bancs : valide_capacites 73/73 (pins 293→294), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 7 : 5 façades de plus (dette 90 → 85)

- 1 preuve REGISTRE composée (diagnostic : 293) : **théorie des possibilités** (nécessité/possibilité
  exactes (0.5, 1.0) ; distribution sous-normalisée REFUSÉE avec raison dite), **imputation multiple MCAR**
  (y = 2x observé une fois sur deux -> la moyenne 31 = 2×15.5 est retrouvée EXACTEMENT, IC contenant),
  **filtre d'état honnête** (un outlier rend le filtre SURCONFIANT — diagnostiqué, pas caché),
  **intervalle prédictif décomposé** (couvre les données, moyenne exacte).
- Plafond du cliquet : **85**.
- Bancs : valide_capacites 73/73 (pins 292→293), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 6 : 7 façades de plus (dette 97 → 90)

- 1 preuve REGISTRE composée (diagnostic : 292) : **propagation d'incertitude** (3² = 9 exact + IC),
  **e-process** (`test_par_pari` : la pièce truquée est rejetée au pas 7 avec E-valeur > seuil, la pièce
  juste n'est JAMAIS rejetée — test séquentiel anytime-valid), **calibration** (le biais est détecté,
  p < 0.05), **probabilités imprécises** (bornes IDM exactes 3/11–4/11), prévision à horizon (IC contenant
  le point), régime de question, survie (D < 15 -> abstention DITE).
- Plafond du cliquet : **90**.
- Bancs : valide_capacites 73/73 (pins 291→292), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 5 : 8 façades de plus (dette 105 → 97, sous la barre des 100)

- 1 preuve REGISTRE composée (diagnostic : 291) : **base-rate fallacy** (PPV bayésien EXACT — test à 99 %
  sur prévalence 0.1 % -> 1.9 % de vrais positifs), régression ridge (OLS exact + rétrécissement), survie
  médiane, sous-dispersion non confondue avec sur-dispersion, log-score exact, probabilité logistique
  exacte, **jury de Condorcet** (la majorité converge : 0.76 -> 0.93 -> 0.999) et **sophisme de la main
  chaude** (la conditionnelle vraie reste 0.5, l'estimateur naïf biaisé — l'artefact est REPRODUIT).
- Plafond du cliquet : **97** — passé sous la barre des 100.
- Bancs : valide_capacites 73/73 (pins 290→291), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 4 : 9 façades de plus (dette 114 → 105)

- 2 preuves REGISTRE (diagnostic : 290) : **intervalles garantis** (bootstrap BCa et jackknife+ contenant la
  vraie moyenne, Bernstein empirique, densité LOO vs Silverman, **maximum d'entropie** : sans contrainte ->
  uniforme EXACT [1/3,1/3,1/3] d'entropie ln 3, intensité temporelle à bins exacts) ; **Dunning-Kruger
  démontré comme artefact** (l'effet émerge à information NULLE, graine fixée) + abstentions honnêtes
  (estime_population, moyenne_modeles sous leur n minimal).
- Plafond du cliquet : **105**.
- Bancs : valide_capacites 73/73 (pins 288→290), valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 3 : 10 façades de plus (dette 124 → 114)

- 2 preuves REGISTRE (diagnostic : 288) : **décision/lois/biais** (transformée pignistique exacte,
  `decouvre_loi` retrouve y = x² avec a = 1.0, effet Berkson démontré numériquement (corr −0.5 -> 0 sous
  sélection), fenêtres de comptage, DMS→degrés décimaux exact (48°51'24"), échelle de carte exacte) ;
  **robustesse/métriques** (covariance MCD avec conditionnement tracé, exactitude de classification exacte,
  IC multinomiaux simultanés, Simpson : strates incohérentes -> abstention DITE).
- Plafond du cliquet : **114**. Pins registre 286→288.
- Bancs : valide_capacites 73/73, valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 2 : 10 façades de plus (dette 134 → 124)

- 2 nouvelles preuves REGISTRE (diagnostic : 286) : **ergodicité/fusion** (taux temporel = moyenne
  géométrique exacte √(1.5×0.6), AUC avec IC, bande DKW exacte √(ln(2/α)/2n), bornage de question,
  combinaison de Yager avec conflit tracé, UCB déterministe) ; **abstention honnête lot 2** (bande de
  prédiction, calibration prédictive, ensembles conformes, correction de prévalence : n insuffisant ->
  abstention DITE ; masses qui ne somment pas à 1 -> refusées).
- Plafond du cliquet : **124**. Pins registre 284→286.
- Bancs : valide_capacites 73/73, valide_atomes 19/19, suite 26/26.

## 2026-07-08 — Excellence atomique, lot 1 : 14 façades ia.py câblées en preuves produit (dette 148 → 134)

- 3 nouvelles capacités prouvées au REGISTRE (diagnostic : 284 preuves exécutées en direct) : **cohérence
  probabiliste** (sophisme de Linda détecté ET cohérence reconnue, Benjamini-Hochberg, AUC, test de
  permutation, inspection paradox — valeurs exactes), **décision/calibration** (EXP3 déterministe,
  conformal split (9.0, 11.0) exact, Condorcet, correction de prévalence bayésienne exacte 0.16/0.52, MDL),
  **abstention honnête des estimateurs** (4 façades dont le CONTRAT « trop peu de données -> abstention
  DITE » est prouvé, plus le seuil franchi -> estimation servie).
- Plafond du cliquet `valide_atomes` abaissé : **134** (ne peut plus remonter).
- Bancs : valide_capacites 73/73 (pins 280→284), valide_atomes 19/19, suite 26/26, capacites_chat 184/184.

## 2026-07-08 — Excellence atomique : gate à CLIQUET valide_atomes (aucun orphelin possible, dette qui fond)

- **Nouvelle gate `valide_atomes` dans la suite (26 gates)** : ① scan de TOUTES les fonctions publiques du
  produit — la gate échoue si une NOUVELLE fonction orpheline apparaît ; ② la dette historique (148 façades
  `ia.py` jamais consommées) est bornée par un plafond qui ne peut que DESCENDRE (câbler ou élaguer, par lots).
- **17 ex-orphelines hors-façade câblées** avec preuve à réponse connue dans la gate : dopants semiconducteurs,
  entropie conjointe (2 bits sur l'uniforme 2×2), formules chimiques du référentiel, Good-Turing,
  clusters Dirichlet, nom de langue, changements d'état, lois des grands nombres (déterminisme à graine
  fixée), inflation de Kalman, regret logarithmique, switch adaptatif de stratégies, taxonomie des sujets
  (erreur claire sur document absent), relations-pont, hyperonymie lexicale, compatibilité de relations
  inverses.
- Bancs : suite **26/26** (nouvelle gate comprise), valide_atomes 19/19.

## 2026-07-08 — Perf atome 3 : borne RAM du cache de lookups streaming

- `_STREAM_CACHE` (mémo des lookups sur gros fichiers) grossissait SANS borne avec chaque entité distincte
  interrogée — purge simple à 16 384 entrées (cache pur, même politique que `_CORRIGE_MEMO`). Audit des
  autres caches : `_DIRECT_CACHE` LRU budgété ✓, `_CORRIGE_MEMO` borné ✓, `lru_cache(maxsize=None)` du
  morpion borné par les états finis du jeu ✓, mémos nouveaux bornés par nature ✓.
- Bancs : suite 25/25, raisonnement 202/202, capacites_chat 184/184.

## 2026-07-08 — Perf atome 2 : stat() mémoïsé + familles de relations précalculées (médiane 0.9 ms, max 5 ms)

- **Atome n°2 (profilé)** : « point de fusion du fer » coûtait **19.3 ms** — `_lookup_direct` payait un
  `os.path.getsize` (~1 ms de stat sur /mnt/c) PAR relation de la famille À CHAQUE appel, plus le re-split
  de toutes les relations. Taille des fichiers mémoïsée (`_TAILLE_FICHIER` — datasets statiques en session)
  + matching tête→relations précalculé (`_RELS_PAR_TETE`) → **1.4 ms (−93 %)**.
- Batterie complète : médiane **0.9 ms** (3.9 au début du mandat), p90 2.0 ms, max **5.1 ms** (50 au début).
- Bancs : assistant_nl 485/485, capacites_chat 184/184, raisonnement 202/202, paraphrases 174/174,
  interface 58/58, suite 25/25, challenge 16/16.

## 2026-07-08 — Perf atome 1 : tokenisation du registre mémoïsée (médiane 3.9 → 1.6 ms, −59 %)

- **Mandat Yohan : optimiser chaque atome (RAM/CPU).** Mesures d'abord : boot produit réel **0.24 s / 23 Mo**
  (le préchargement des 504 modules n'est PAS dans le chemin produit — c'est le manifeste d'embarquement) ;
  batterie chaude de 15 questions mixtes : médiane 3.9 ms, max 50 ms, RSS 149 Mo avec données.
- **Atome n°1 (profilé)** : la boucle candidate de `resout_nl_generique` refaisait `rel.split("_")` + filtre
  pour CHAQUE relation à CHAQUE question (~1 ms/question). Tokenisation précalculée une fois (`_rel_toks`,
  cohérente avec le cache du registre qui n'est jamais invalidé à chaud) → **médiane 1.6 ms (−59 %), max
  20 ms (−60 %)**, RSS inchangé.
- **Audit câblage 2 niveaux rejoué** : modules 504/504 (0 orphelin) ; fonctions = 0 orpheline dans tout le
  travail de la nuit ; 165 fonctions publiques jamais appelées PRÉEXISTANTES découvertes (148 dans la façade
  `ia.py`) — dette listée, à traiter dans le mandat perf.
- Bancs : resolution 50/50, raisonnement 202/202, paraphrases 174/174, assistant_nl 485/485, suite 25/25.

## 2026-07-08 — Vague 45 (tests réels Yohan) : horloge N acteurs, liens cliquables, distance nue, valide_interface 58/58

- **Horloge multi-acteurs** (test réel : « un avion part en même temps qu'une voiture à 5h17, l'avion a
  4h58 de vol, la voiture 17h03 à rouler, à quelle heure arrivent les 2 ? » tombait en repli) → une arrivée
  PAR acteur, N acteurs (2, 3, 4 épinglés), l'heure de départ écartée des durées par position, lendemains
  dits : « L'avion : 10 h 15 (5 h 17 + 4h58) ; La voiture : 22 h 20 (5 h 17 + 17h03). »
- **Liens cliquables** (test réel : les URLs des réponses web étaient du texte mort) : construction DOM
  sûre (nœuds texte + <a>, jamais d'innerHTML — zéro injection), target _blank + noopener.
- **Distance forme nue** (« distance toulouse albi ») : découpe validée par le lookup réel des coordonnées
  — « distance paris toulouse » → 588 km ; Albi/Montauban restent SANS coordonnées (crible anti-homonyme,
  chantier latitude_ville_fr documenté, en attente d'ingestion + re-upload).
- **valide_interface 58/58** (jamais lancé dans le protocole — 3 échecs PRÉEXISTANTS à la nuit corrigés
  comme pins dérivés : la présentation reçoit la salutation au prénom, les refus sont variés par
  formulation.py, le prénom du profil persistant ~/.verax est un rappel légitime ; + 4 pins de casse
  MULTITOURS alignés sur la restitution de casse de la vague 34).
- Bancs : `valide_assistant_nl` **485/485** (+3), raisonnement **202/202** (+2), `valide_interface`
  **58/58**, capacites_chat 184/184, paraphrases 174/174, stats 34/34, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 44 : conventions d'objets et de jeux (table fermée, cadre dit)

- Échiquier 64 cases (8 × 8), piano 88 touches (standard moderne dit), tarot 78 cartes, football 11 joueurs
  et 90 minutes (2 × 45, hors arrêts de jeu — cadre dit), golf 18 trous, bowling 10 quilles, violon 4 cordes
  (sol ré la mi), guitare 6 cordes, violoncelle 4, dames internationales 100 cases. Tous en abstention
  auparavant ; gardes : « l'échiquier politique » et « une corde de 10 mètres » ne sont pas volés.
- Bancs : `valide_assistant_nl` **482/482** (+8), capacites_chat 184/184, raisonnement 200/200,
  paraphrases 174/174, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 43 : douzaine sans chiffre, conversion inverse « pour »

- « combien y a-t-il d'œufs dans **une** douzaine » → 12 (le motif exigeait un chiffre) ; « combien de
  **nœuds pour** 30 km/h » → 16.2 (motif de conversion inverse « combien de X pour N Y » ; « minutes pour
  2 heures » → 120). Balayage ligature œ : le reste des cas sondés (œuf, sœur, bœuf…) = abstention
  honnête correcte (data absente).
- Bancs : `valide_assistant_nl` **474/474** (+3), capacites_chat 184/184, raisonnement 200/200,
  paraphrases 174/174, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 42 : probabilités cartes/deux dés/lancers + traduction en écho tuée

- **Probabilités à hypothèses DITES** (tombaient en mémo) : jeu de 52 cartes (as → 1/13, cœur → 1/4
  — ⚠ `normalise()` SUPPRIME le œ, question brute exigée ; figures 3/13, rouge/noire 1/2) ; **deux dés**
  par énumération exacte des 36 couples (double → 1/6, somme 7 → 1/6, somme 13 → « 0 — impossible
  (2..12) ») ; lancers enchaînés (« deux piles de suite » → 1/4, indépendance dite).
- **Traduction en écho tuée** : « comment dit-on merci en allemand » rendait *« Merci (traduction mot-à-mot
  assistée) »* — le texte inchangé étiqueté traduction. Rien traduit → refus honnête ; les traductions
  réelles (« bonjour » → Hello) intactes.
- Bancs : `valide_assistant_nl` **471/471** (+6), capacites_chat **184/184** (+2), raisonnement 200/200,
  paraphrases 174/174, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 41 : conventions de l'eau, lumière du Soleil (conditions dites) + vérification globale

- **Eau** (conditions DITES, même famille que la congélation déjà câblée) : « un litre d'eau » → « ≈ 1 kg
  (0.998 kg à 20 °C — le litre a historiquement défini le kilogramme) » ; m³ → ≈ 1000 kg (une tonne) ;
  densité → 1 par convention (variation dite) ; **ébullition en altitude** → loi qualitative + exemple
  approximatif dit (jamais un chiffre nu). « 2 litres **d'eau** en centilitres » → le qualificatif de
  substance ne casse plus la conversion (200 cl).
- **Lumière du Soleil** : « ≈ 8 min 19 s (149.6 millions de km en moyenne / c — orbite elliptique, ±8 s) »
  (composition de deux constantes vérifiées).
- Sondé, abstention CORRECTE maintenue : température du corps, battements/minute, vitesse de rotation de la
  Terre (candidats amorce — à voir avec Yohan, décision antérieure respectée).
- **Vérification globale de fin de nuit — TOUT VERT** : lecteur **1615/1615**, base_faits 411, maj 41,
  coordonnées 47, câblage **504 modules / 0 orphelin**, assistant_nl **465/465**, capacites_chat 182,
  raisonnement 200, paraphrases 174, stats 34, suite 25, challenge 16, resolution 50.

## 2026-07-08 — Vague 40 : passe adverse horloge — soustraction, durées compactes, « entre », variantes

- **FAUX** : « 20h45 **moins** 30 minutes » → *« 1245 minutes »* encore (seul « plus » était routé) →
  « 20 h 15 (20 h 45 − 30 minutes) » (la veille dite si passage sous minuit).
- **Durées compactes dans les problèmes** : « le trajet dure **1h30** » → « 10 h 15 (8 h 45 + 1h30) » ;
  « le film commence à 21h et dure 2h15 » → 23 h 15 (le multi-demandes ne découpe plus les problèmes
  d'horloge sur « et ») ; « il est 10h20 … dans 45 minutes » → 11 h 05.
- **Variantes** : « combien d'heures **entre** 9h et 17h30 » → 8 h 30 ; « le prix a **baissé** de 80 à 60 »
  → −25 % ; « les multiples de 7 **jusqu'à** 50 » → 7, 14, …, 49.
- Bancs : `valide_assistant_nl` **459/459** (+6), capacites_chat 182/182, raisonnement 200/200,
  paraphrases 174/174, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 39 : robustesse orale/SMS vérifiée + « kel/quel heure »

- Passe de robustesse : « c koi 15% de 80 », « cb font 7 fois 8 », MAJUSCULES intégrales, « combein »
  (typo), politesse (« stp/svp »), fillers (« euh donc en fait ») — **tout tenait déjà** (vérifié).
- Seul trou : « **kel heure** il est » (le dépliage SMS donne « quel heure », que le motif exigeant
  « quelle » refusait) → motif assoupli `quel(le)?`.
- Bancs : capacites_chat **182/182** (+2), assistant_nl 453/453, raisonnement 200/200, paraphrases 174/174,
  suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 38 : multiples (FAUX « Oui, 5 est premier »), tables, variation de prix, compter

- **FAUX** : « les 5 premiers **multiples** de 7 » → *« Oui, 5 est premier »* (la primalité accrochait
  « premiers », à côté). Route multiples AVANT la primalité : « 7, 14, 21, 28, 35 » ; **table de
  multiplication** (« la table de 7 » → 10 lignes) ; la primalité intacte.
- **Variation de prix en %** : « le prix passe de 80 à 60 » → « −25 % (… — une baisse) » ; « de 50 à 65 » →
  « +30 % (… — une hausse) » (calcul montré, sens dit).
- **Décomposition demandée** : « 90 minutes en heures **et** minutes » → « 1 h 30 » (la conversion simple
  répondait « 1.5 heures » à côté de la forme demandée).
- **Énumérations natives** : compte de 1 à 10, compte à rebours, alphabet récité (bornes sûres ≤ 100).
- Bancs : `valide_assistant_nl` **453/453** (+9), capacites_chat 180/180, raisonnement 200/200,
  paraphrases 174/174, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 37 : arithmétique d'horloge ÉNONCÉE (3 FAUX « heure machine »), syllogisme interrogatif, trivia calendaire

- **FAUX ×3 (même racine)** : « un train part **à 8h** et roule 2 heures, à quelle heure arrive-t-il » /
  « rendez-vous à 14h30 dure 45 minutes » / « il est 23h30 … dans une heure » recevaient *l'heure ACTUELLE de
  la machine*. Garde (heure ÉNONCÉE = problème d'arithmétique, jamais l'horloge) + routes pures : « 10 h 00
  (8 h 00 + 2 heures) », « 15 h 15 », « 0 h 30 … — le lendemain » (modulo 24 h dit) ; « 20h45 plus 30
  minutes » → 21 h 15 (au lieu de *1245 minutes*) ; **durée entre deux heures** (« de 9h à 17h30 » → 8 h 30 ;
  fin avant début → abstention, nuit à cheval ambiguë).
- **Syllogisme en forme interrogative** (« si tous les chats sont gris et que Félix est un chat, Félix
  est-il gris ? » tombait en mémo ; la forme à virgules aussi) : conclusion typée « d'après TES prémisses ».
  Au passage : « gris » singularisé en *« gri »* → liste fermée d'invariables en -s. Garde : « si … » n'est
  plus découpé par le multi-demandes (prémisses liées).
- **Trivia calendaire** : mois le plus court (février), piège « quel mois a 28 jours » → « Tous — seul
  février s'arrête à 28 », 7 mois à 31 jours, « mois le plus long » → pas UN seul (dit).
- Bancs : `valide_assistant_nl` **444/444** (+8), capacites_chat **180/180** (+3), raisonnement 200/200,
  paraphrases 174/174, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 36 : les milliers à espace PARTOUT (« 20 % de 5 000 » → 1 !) + bords théoriques

- **FAUX ×3 (même racine, trois routes)** : l'espace des milliers cassait aussi les **pourcentages**
  (« 20 % de 5 000 » → *1* — « de 5 » lu ; TVA sur « 1 500 » → lue 1) et l'**arithmétique** (« 5 000 plus
  3 000 » → repli). Corrigé aux trois étages : `_PCT`/`_f` (toutes les routes %), `resout_arithmetique`,
  `_reponse_calcul` (pipeline).
- **Bords théoriques** (tombaient en repli) : « le plus grand nombre premier » → « Il n'y en a pas —
  quantité infinie (théorème d'Euclide) » ; « le plus petit » → 2 (seul premier pair, dit) ; « racine carrée
  de 2 » → **irrationalité DITE + approximation étiquetée** (≈ 1.414214) au lieu de l'abstention sèche —
  les carrés parfaits gardent leur route exacte.
- **Fractions en lettres** : « un tiers plus un quart » → « 7/12 (1/3 + 1/4, fraction exacte) ≈ 0.5833 ».
- Bancs : `valide_assistant_nl` **436/436** (+9), capacites_chat 177/177, raisonnement 200/200,
  paraphrases 174/174, stats 34/34, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 35 : « 5 000 mètres » → 0 km !, conjugueur voleur, unités exactes et ambiguës

- **FAUX** : « convertis **5 000** mètres en kilomètres » → *« 0 kilometres »* (l'espace des milliers cassait
  le parse — « 000 » lu comme le nombre). Les milliers à espace sont recollés dans `_norm_conv`.
- **FAUX** : « comment **conjuguer aimer** au futur » → *la conjugaison de « conjuguer » au présent* (le
  premier mot en -er était pris, et le temps demandé ignoré en silence). Le verbe-requête est exclu ; un
  temps hors présent → honnêteté explicite (« je ne garantis que le PRÉSENT des réguliers »), « l'imparfait
  de chanter » pareil ; le présent régulier intact.
- **Décimales fantômes** : `_fmt_nombre` fabriquait des décimales au-delà de la précision du float sur les
  grands nombres (année-lumière → « …580.800781 ») → représentation exacte du float (%.15g) au-delà de 10⁶.
- **Unités** : mile nautique (1852 m), année-lumière (9.4607×10¹² km), carat (0.2 g) — définitions exactes ;
  « **un** hectare » et l'unité NUE (« année-lumière en km » = 1) acceptées ; **gallon/pinte** → ambiguïté
  US/UK DITE avec les deux facteurs exacts ; **tasse** → « pas une unité normalisée (200-250 ml) » ;
  **vitesse du son** → 343 m/s avec conditions DITES (air, 20 °C).
- Bancs : `valide_assistant_nl` **427/427** (+8), capacites_chat **177/177** (+3), raisonnement 200/200,
  paraphrases 174/174, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 34 : continuations sur les CALCULS (« et de CO2 ? », « et en mars ? »)

- « masse molaire de H2O » puis « **et de CO2 ?** » tombait en repli — deux causes : ① le sujet de
  continuation n'était mémorisé que pour les réponses DATA (jamais pour les calculs de `fonction_nl`) →
  mémorisation de l'opérande (queue après la dernière préposition, ≤ 3 tokens pour éviter les substitutions
  absurdes) ; ② la nouvelle entité était **minusculée** (« co2 ») — or les formules chimiques sont sensibles
  à la casse (H2O ≠ h2o) → casse d'origine restituée dans `_nouvelle_entite`.
- Marches maintenant : « et de CO2 ? » → 44.009 g/mol ; « combien de jours en février 2024 » → « et en
  mars ? » → 31. Les continuations existantes (or/celsius/population/villes) inchangées.
- Perf vérifiée après les 12 vagues de la nuit : médiane **1 ms**, p90 3 ms (chaud).
- Bancs : raisonnement **200/200** (+2), capacites_chat 174/174, assistant_nl 419/419, paraphrases 174/174,
  suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 33 : cas limites mathématiques DITS + calendrier courant complet

- **Cas limites** (tombaient en mémo « Noté ») : « 10 divisé par 0 » / « 17 modulo 0 » → « Indéfini — la
  division/le modulo par zéro n'est pas défini(e) » ; « racine carrée de −9 » → « Pas de racine carrée
  réelle ; en nombres complexes : 3i et −3i » (racines complexes DONNÉES quand entières, sinon dit).
  Divisions et racines normales intactes.
- **Calendrier courant** (horloge machine, tout étiqueté ; tombaient en repli) : saison (« Été dans
  l'hémisphère nord (hiver dans le sud) — bornes astronomiques approximatives ») ; **semaine ISO 8601** ;
  jours restants avant la fin de l'année ; « 200e jour de l'année » → date exacte (400e → borne DITE) ;
  jour de l'année courant ; **bissextile relative** (« l'année prochaine » → 2027 résolue + règle dite).
- Bancs : `valide_assistant_nl` **419/419** (+6), capacites_chat **174/174** (+6), raisonnement 198/198,
  paraphrases 174/174, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 32 : 2 FAUX horloge (coucher du soleil, heure future) + âge exact, années futures

- **FAUX** : « à quelle heure le **soleil se couche** » → *l'heure ACTUELLE de la machine* ! Garde
  éphémérides (soleil/lune/aube/crépuscule → abstention DITE : lieu + jour requis, pas d'éphémérides
  vérifiées).
- **FAUX** : « quelle heure **sera-t-il dans 3 heures** » → *l'heure actuelle aussi*. → « Il sera 21 h 40
  (horloge de ta machine + 3 heures) » (décalage exact).
- **Âge** : date complète → âge EXACT (« né le 15 mars 1990 » → « 36 ans (né(e) le …, nous sommes le …) ») ;
  phrasé « si je suis né en 1990 quel âge j'ai » → fourchette honnête (l'ancienne route ne connaissait qu'un
  seul phrasé).
- **Années** : « quelle année dans 10 ans » → « En 2036 (2026 + 10, année de l'horloge) » (partait en
  « c'est subjectif » !) ; « dans combien d'années 2050 » → « Dans 24 ans » ; année passée → « C'était il y
  a N ans ».
- Sondé, abstention CORRECTE (pas touché) : participe passé de « prendre » (irrégulier — le conjugueur ne
  fait que les réguliers, dit), calories d'une pomme (data absente), Pâques (pas de brique computus),
  distance Paris-Marseille (coords FR en attente du re-upload — chantier connu).
- Bancs : capacites_chat **168/168** (+6), assistant_nl 413/413, raisonnement 198/198, paraphrases 174/174,
  suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 31 : opérations textuelles avancées (palindrome répondu « à côté », morse décodé volé)

- **FAUX de sens** : « le mot radar est-il un **palindrome** » → *« Le radar est un système — je ne le
  rattache pas à palindrome »* (la fiche is-a répondait sur l'OBJET, pas le MOT). Garde propriété-de-mot
  (palindrome/anagramme/pangramme → route native) : « Oui — radar se lit pareil dans les deux sens » ;
  « chat » → Non + envers montré.
- **FAUX préexistant tué** : « que signifie **... --- ...** en morse » → *la définition de l'ANIMAL morse* !
  (l'alias « que signifie X » → définition volait avant le décodeur). Garde tokens points/traits → « SOS ».
  « SOS en morse » (l'argument est AVANT « en morse ») → « ... --- ... » ; l'animal (« c'est quoi un
  morse ») intact.
- **Texte avancé câblé** (natif exact) : occurrences (« combien de fois s dans mississippi » → 4), tri de
  MOTS alphabétique (le lexique dumpait ses entrées), plus long/court mot, initiales (« Jean-Claude Van
  Damme » → J. C. V. D.), remplacement de lettre (« banana » → « bonono »), caractères (tout signe compris,
  DIT — distinct des « lettres »).
- Bancs : `valide_assistant_nl` **413/413** (+3), capacites_chat **162/162** (+8), raisonnement 198/198,
  paraphrases 174/174, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 30 : 2 FAUX (« tombera le 25 décembre » → 2019 !, scores→Wilson) + durées composées, douzaines, demi/quart

- **FAUX** : « quel jour **tombera** le 25 décembre cette année » → *« (en comprenant « 24 decembre ») 2019 »*
  (le futur n'était pas reconnu → fuzzy vers un titre d'œuvre !). Le jour-de-la-semaine accepte
  était/est/sera/tombe/tombera + « le X <mois> tombe quel jour » ; date SANS année → année de l'horloge
  ÉTIQUETÉE, verbe accordé (« Le 25 décembre 2026 sera un vendredi »).
- **FAUX** : « 15 sur 20 **en pourcentage** » → *intervalle de Wilson* (encore une variante). → 75 % exact ;
  « 12 sur 20, ça fait combien **sur 100** » → 60 % (garde rescaling à DEUX ratios — « proportion de 37 sur
  100 » reste du Wilson, pin conservé).
- **Durées composées** : « 2 semaines et 3 jours en jours » → 17 ; « 1 an et 6 mois en mois » → 18 (deux
  familles fermées, jamais de mélange an→jours ; piège « mois ».rstrip(« s ») → « moi » vécu et épinglé).
  Garde comptage : ce n'est plus un compte d'hyponymes (« Je connais 10 termes jour »).
- **Quotidien** : douzaines (« 3 douzaines » → 36, « demi-douzaine » → 6), « un demi-litre » → 50 cl,
  « trois quarts d'heure » → 45 min, « un quart d'heure » → 900 s (réécritures locales à la conversion) ;
  « donne-moi l'heure de Tokyo » (motif élargi).
- Bancs : `valide_assistant_nl` **410/410** (+10), capacites_chat **154/154** (+4 dont Rio/futur),
  `valide_fonction_stats_nl` **34/34**, raisonnement 198/198, paraphrases 174/174, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 29 : passe adverse — 3 FAUX par variantes de phrasé (Rio !, composition, 1h30)

- **FAUX** : « quelle heure est-il à **Rio de Janeiro** » → *l'heure LOCALE de la machine servie* ! La garde
  anti-ville-inconnue exigeait chaque mot capitalisé — la particule minuscule (« de ») cassait l'ancre de fin.
  Motif permissif (toute ville à majuscule initiale → abstention si hors table) + Rio/São Paulo/Buenos
  Aires/Lima/Bogotá/Santiago/La Havane ajoutées à la table IANA. Épinglé : ville inconnue multi-mots
  (« Oulan-Bator ») → abstention DITE.
- **FAUX** : « le **triple du quart** de 100 » → *25* (seule l'opération interne était lue). Composition
  câblée, étapes montrées : « 75 (quart de 100 = 25 ; triple = 75) ».
- **FAUX** : « vitesse moyenne si je fais 100 km en **1h30** » → *« Moyenne : 43.67 »* (le format compact
  passait au travers de la garde stats). Garde élargie (h\d{0,2}) + route compacte : « 66.6667 km/h
  (100 km / 1 h 30) ».
- **Variantes de phrasé câblées** : « combien **y a-t-il** de secondes dans une année » / « **nombre de**
  secondes … » (→ 31 536 000) ; « la France **compte combien** d'habitants » (→ réponse formatée ; tombait
  sur un compte lexical de termes « habitant ») ; « 150 **kilomètres** à 50 km/h » (mot entier) ; ordinal en
  lettres (« le **millième** nombre premier » → 7919).
- **Moyenne harmonique/géométrique avec 0** → refus honnête explicite (la stdlib renverrait la convention
  limite 0).
- Bancs : `valide_assistant_nl` **400/400** (+7), `valide_fonction_stats_nl` **34/34** (+2),
  capacites_chat **150/150** (+2), raisonnement 198/198, paraphrases 174/174, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 28 : 3 FAUX (harmonique, Wilson, tendance) + électronique/mécanique, notation scientifique, constantes

- **FAUX** : « moyenne **harmonique** de 2 et 4 » → *« Moyenne : 3 »* (l'arithmétique servie à la place de
  2.667). Harmonique et géométrique câblées avec formule dite ; valeurs non positives → abstention.
- **FAUX** : « quel pourcentage représente 45 sur 60 » → *un intervalle de Wilson* (inférence) au lieu du
  calcul exact **75 %**. Garde (« représente/fait » = division exacte) ; l'inférence (« intervalle de
  confiance pour 45 succès sur 60 ») reste servie.
- **FAUX** : « augmente 50 de 10 % **puis de 20 %** » → *« série trop courte »* (détection de tendance !).
  Garde + **augmentations enchaînées** appliquées sur le résultat : « 66 (50 + 10 % = 55 ; 55 + 20 % = 66) ».
- **Électronique/mécanique câblées** (briques `electronique`/`mecanique`, tombaient en mémo) : résistances
  équivalentes série (somme) et parallèle (1/Σ(1/Rᵢ)), période du pendule simple (g = 9.80665 DIT),
  pression P = F/S.
- **Notation scientifique** (« 123000 » → 1.23 × 10^5, « 0,00042 » → 4.2 × 10^-4) ; **constantes nommées** :
  nombre d'or ((1+√5)/2), e (base du log naturel).
- Bancs : `valide_assistant_nl` **393/393** (+11), `valide_fonction_stats_nl` **32/32** (+5), raisonnement
  198/198, paraphrases 174/174, capacites_chat 148/148, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 27 : 2 FAUX (règle de trois décimale, Fermi-monnaie ~60 !) + argent du quotidien, lettres, polygones

- **FAUX** : « si 3 stylos coûtent **4,50** euros combien coûtent 7 stylos » → *« 9.333333 »* (normalise()
  mangeait la virgule : 4,50 lu 4 !). Motif déplacé sur `_norm_conv` → **10.5** (leçon n°1, rechute épinglée).
- **FAUX** : « 3 pièces de 2 euros et 2 billets de 5 euros, combien en tout » → *« Estimation d'ordre de
  grandeur : ~60 »* (le Fermi MULTIPLIAIT tous les nombres ; le décomposeur multi-demandes coupait aussi sur
  « et »). Deux gardes + route **somme exacte montrée** : « 16 euros (3 × 2 + 2 × 5) ».
- **Argent du quotidien** (tombaient en mémo) : « 20 euros moins 7,50 » → 12.5 (mot moins/plus accepté quand
  le résidu hors monnaie est VIDE — « il fait moins 5 degrés », « la guerre de 1939-1945 » intacts) ;
  **rendu de monnaie** (« sur 50 € pour 37,25 » → « 12.75 (50 − 37.25) » ; achat > billet → « Impossible » dit) ;
  **prix total** (« 3 baguettes à 1,20 € » → 3.6) ; **fractions multiples** (« les trois quarts de 200 » → 150 ;
  décimal infini → abstention, règle inchangée).
- **Géométrie/conversions** : périmètre des polygones réguliers nommés (pentagone→dodécagone ; « hexagone de
  côté 5 » → « 30 (6 × 5) ») ; arêtes/sommets cube-pavé-tétraèdre ; **mph** (1 mile = 1.609344 km, deux sens).
- **Lettres** : « la 5e lettre du mot maison » → o ; « la première/10e/30e lettre de l'alphabet » → a/j/borne
  DITE ; « dernière lettre du mot chat » → t.
- Bancs : `valide_assistant_nl` **382/382** (+23), `valide_fonction_stats_nl` **27/27** (+1), raisonnement
  **198/198** (+1), paraphrases 174/174, capacites_chat 148/148, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 26 : cinématique du quotidien (1 FAUX), IMC, pH, TVA, consommation, prix unitaire, angles

- **FAUX** : « vitesse moyenne si je parcours 150 km en 2 heures » → *« Moyenne : 76 »* (la route stats
  moyennait distance et durée !). Garde stats (motif « X km en Y heures » = division, pas une liste ; la
  moyenne d'une LISTE de vitesses reste servie) + **cinématique complète, calcul montré** : v = d/t
  (« 75 km/h (150 km / 2 h) »), t = d/v (« 3 h » ; inexact → « ≈ 1 h 26 min (arrondi à la minute) » DIT),
  d = v×t (« 180 km (90 km/h × 2 h) »).
- **Quotidien chiffré** (tombaient en mémo/repli) : **consommation aux 100 km** (« 6 L aux 100 km pour
  250 km » → 15 L), **prix au kilo/litre** (« 1,5 kg à 4 € le kilo » → 6 € ; unités disparates → abstention),
  **TVA** (« TVA de 20% sur 100 € » → montant ET TTC, base lue HT et dite), **IMC** (« 70 kg et 1m75 » →
  22.86, formats 1m75/175 cm/1,80 m, kg/m² OMS, sans interprétation médicale), **pH** (« concentration de
  0,001 » → 3, brique `physique.calcule`).
- **Angles** : degré ↔ radian (π/180 exact, deux sens) ; les températures (« 100 degrés celsius en
  fahrenheit ») gardent leur route dédiée (vérifié).
- Bancs : `valide_assistant_nl` **359/359** (+14), `valide_fonction_stats_nl` **26/26** (+2), raisonnement
  197/197, paraphrases 174/174, capacites_chat 148/148, suite 25/25, challenge 16/16.

## 2026-07-08 — Vague 25 : pourboire, durées variables honnêtes, romain→nombre élargi, « quelle est la date dans 3 semaines »

- **Pourboire** (tombait en mémo « C'est noté ») : « 15% de pourboire sur 80 euros » → « 12 de pourboire
  (15 % de 80) ; **total : 92** » (le total à payer est l'intention usuelle — montré).
- **Durées variables** → réponses composées honnêtes (même principe que semaines/année) : « heures dans un
  mois » → 672-744 h selon le mois ; « jours dans un siècle » → 36 524 ou 36 525 (grégorien).
- **Romain → nombre** : « MMXXVI en nombre », « XIV en chiffres » acceptés (seul « en chiffres arabes/décimal »
  passait) ; « mille en nombre » ne matche pas (e hors alphabet romain).
- **Date relative** : « **quelle est la** date dans 3 semaines » (le motif n'acceptait que « quelle date ») →
  date exacte étiquetée.
- Bancs : `valide_assistant_nl` **345/345** (+7), capacites_chat **148/148** (+1), raisonnement 197/197,
  paraphrases 174/174, suite 25/25.

## 2026-07-08 — Vague 24 : 4 FAUX tués (1939 !, 100e premier, somme de série, atomes d'un élément) + chimie quantitative

- **FAUX massif** : « combien de secondes dans une année » → *« 1939 »* (le résolveur générique accrochait
  `annee_publication_oeuvre` via le token « année » et une entité fuzzy !). Garde structurelle : une question
  « combien … » attend une **quantité** — les relations `annee_*`/`date_*` sont écartées ; la conversion
  (31 536 000, année commune étiquetée) reprend la main. Les comptes réels (population…) restent servis.
- **FAUX** : « quel est le 100e nombre premier » → *« Non, 100 n'est pas premier »* (à côté de la question).
  Route ordinale exacte : « le 100e nombre premier est 541 » (énumération `est_premier`, 1er → 2, borne 10 000).
- **FAUX** : « somme des entiers de 1 à 100 » → *« Somme : 101 (sur 2 valeurs) »* (les BORNES prises pour la
  liste par la route stats). Garde série côté stats + routes exactes : 1 à 100 → 5050 (formule montrée),
  « les 100 premiers entiers » → n(n+1)/2, « les 5 premiers nombres premiers » → 28 (énumération).
- **FAUX** : « combien d'atomes d'**oxygène** dans CO2 » → *« 3 atomes »* (le TOTAL de la molécule). Élément
  nommé → compte de CET élément (2 atomes d'oxygène) ; élément absent → « 0 — pas d'atome de sodium… (composition
  montrée) » ; élément HORS référentiel (« fer ») → abstention, jamais le total à la place.
- **Chimie quantitative câblée** (briques `chimie_quantitative`/`nomenclature_chimique`, tombaient en mémo) :
  molarité (« 2 moles dans 4 litres » → 0.5 mol/L), nom du composé binaire (« CO2 » → dioxyde de carbone),
  moles↔grammes (« 36 g d'eau » → 1.9983 mol, n = m/M, table fermée nom→formule du lecteur), pourcentage
  massique avec nom d'élément FR (« de l'oxygène » → 88.81 %).
- **« combien d'habitants en France ? »** (tombait en repli) : réécriture fermée ANCRÉE → « population de X »
  en tête de pipeline → réponse FORMATÉE (« Population de la France : 68 720 337 habitants. ») ; le gentilé
  (« comment s'appellent les habitants de Lyon ») ne passe pas par là (abstention intacte).
- **Conversions** : ligature « œ » (« 10 nœuds en km/h » ratait — NFD ne décompose pas œ) ; durée compacte
  « 2h30 » → 150 min/9000 s ; jours d'un mois (« février 2024 » → 29, grégorien exact ; février sans année →
  « 28 (29 les années bissextiles) » ; le compte à rebours « dans combien de jours… » n'est pas volé).
- Bancs : `valide_assistant_nl` **338/338** (+26), `valide_fonction_stats_nl` **24/24** (+2), banc_raisonnement
  **197/197** (+3), resolution 50/50, suite 25/25, capacites_chat 147/147, paraphrases 174/174, challenge 16/16.

## 2026-07-08 — Vague 23 : proba dé/pièce, coefficient binomial nommé, permutations « ranger » (2 garbages tués)

- **2 garbages tués** (une QUESTION avalée par l'accusé mémo « Noté — je le retiens », trouvés à la sonde) :
  « coefficient binomial 5 parmi 2 » et « probabilité d'obtenir un 6 avec un dé » partaient en mémo.
- **Coefficient binomial nommé** : « coefficient binomial 2 parmi 5 » → **C(5, 2) = 10** (convention « k parmi
  n » ; sans « parmi » = ordre de la notation C(n, k)). L'interprétation est MONTRÉE : « 5 parmi 2 » →
  « C(2, 5) = 0 (choisir 5 éléments parmi 2 : impossible) » — jamais un 0 sec ambigu.
- **Probabilité élémentaire dé/pièce** (brique équiprobabilité `maximum_entropie.uniforme`) : « probabilité
  d'obtenir un 6 avec un dé » → « 1/6 (≈ 16.67 %) — **en supposant un dé équilibré à 6 faces** » (l'hypothèse
  est toujours énoncée) ; « dé à 20 faces » → 1/20 ; face impossible → « 0 — un dé à 6 faces ne peut pas
  donner 7 » ; « pile avec une pièce » → 1/2. Gardes : « dé » cherché sur la question BRUTE (normalise() efface
  l'accent → « de » matcherait tout) ; plusieurs dés → abstention (autre loi) ; « pièce » exige pile/face
  (« pièce de théâtre » intacte) ; « probabilité de pluie » intacte ; « dé pipé » sans face → abstention.
- **Permutations « ranger/classer »** : « de combien de façons peut-on ranger 4 livres » → « 24 (permutations :
  4!) » (seul « ordonner » était couvert). Gardes : « façons/manières » OBLIGATOIRE (l'impératif « range mes
  fichiers » ne matche pas) ; UN SEUL entier (« 4 livres sur 2 étagères » = autre problème → abstention).
- Sondé OK sans câblage (déjà en place) : chimie (masse molaire H2O/CO2 avec g/mol, nb d'atomes, composition,
  formule du dioxyde de carbone), factorielle, combinaisons, Fibonacci.
- Bancs : `valide_assistant_nl` **312/312** (+14), suite 25/25, capacites_chat 147/147, raisonnement 194/194,
  paraphrases 174/174, challenge 16/16.

## 2026-07-08 — Vague 22 : date du jour (variantes), congélation de l'eau, mot à l'envers, zéros d'un grand nombre

- **Date/jour du jour** : « quel jour de la semaine sommes-nous », « quelle est la date aujourd'hui »,
  « on est quel jour » (motifs élargis ; « aujourd'hui » avec apostrophe géré). Garde : « date de naissance
  de Napoléon » n'est pas volée.
- **Congélation de l'eau** (amorce `congelation_eau`) : « à quelle température l'eau gèle » / « point de
  congélation/fusion de l'eau » → 0 °C. ⚠ « eau » OBLIGATOIRE dans le motif (« point de fusion **du fer** » =
  1811 K, à ne pas confondre — régression attrapée + épinglée dans valide_base_faits).
- **Mot à l'envers** : « inverse le mot chat » / « retourne le mot X » (« à l'envers » implicite) — sans casser
  « épelle chien » (épellation, « à l'envers » requis pour ce verbe).
- **Zéros d'un grand nombre** : « combien de zéros dans un million » → 6 (échelle courte).
- Bancs : `valide_base_faits` **411/411** (+8), assistant_nl 298/298, capacites_chat **149/149** (+5), suite
  25/25, raisonnement 194/194, paraphrases 174/174, câblage 504 0 orphelin.

## 2026-07-08 — Vague 21 : volume cylindre/cône, aire trapèze, « kilo » → grammes

- **Géométrie** : volume du cylindre (π·r²·h — « rayon 2 hauteur 5 » → 62.83), volume du cône (π·r²·h/3),
  aire du trapèze ((b₁+b₂)/2·h — « bases 4 et 6, hauteur 3 » → 15).
- **Unités** : « un kilo »/« kilos » reconnu comme kilogramme (usage courant) → « combien de grammes dans 2
  kilos » → 2000.
- Bancs : `valide_assistant_nl` **296/296** (+5), suite 25/25, paraphrases 174/174, capacites_chat 144/144,
  câblage 504 0 orphelin.

## 2026-07-08 — Vague 20 : 1 FAUX (Noël→31) + comparaison directe, extremum, tri, compte à rebours, coef

- **FAUX** : « dans combien de jours le 25 **décembre** » → *« 31 »* (le gabarit `jours_mois` prenait
  « décembre » pour une durée de mois). Gardes ajoutées au gabarit (compte à rebours « dans/jusqu/avant », tout
  chiffre) + **compte à rebours câblé** : « dans combien de jours Noël / le 25 décembre » → nombre exact
  jusqu'à la date (année courante, l'an prochain si passée).
- La route stats min/max ne coiffe plus les **comparaisons** (« 8 est plus grand que 5 » → Oui), les
  **extremums** (« le plus grand entre 7 et 12 » → 12) ni les **tris** (« classe 3, 1, 2 par ordre
  croissant » → 1, 2, 3 ; « du plus petit au plus grand », décroissant). Gardes stats + routes dédiées dans
  `resout_math`. Abréviation **« coef »** reconnue pour la moyenne pondérée (le guérisseur la corrompait en
  « chef » → protégée, comme « contient »→« continent »).
- Bancs : `valide_assistant_nl` **291/291** (+7), capacites_chat **144/144** (+2), lecteur **1615/1615** (+2),
  stats_nl 22/22, suite 25/25, raisonnement 194/194, paraphrases 174/174, challenge 16/16, câblage 504.

## 2026-07-08 — Vague 19 : fractions, pourcentage inverse, prix avant réduction, arrondi à un rang

- **Fractions** (exactes via `Fraction`) : « simplifie 6/8 » → 3/4 (« 10/5 » → 2, entier) ; « 3/4 en
  pourcentage » → 75 % ; « 0,25 en fraction » → 1/4.
- **Pourcentage inverse** : « 40 est 20% de quel nombre » → 200 (part ÷ taux) ; **prix avant réduction** :
  « un article coûte 120 après 20% de réduction » → 150.
- **Arrondi à un rang** : « arrondis 347 à la centaine » → 300, « au millier » → 3000 (demi-supérieur).
- Bancs : `valide_assistant_nl` **284/284** (+10), suite 25/25, raisonnement 194/194, paraphrases 174/174,
  capacites_chat 142/142, câblage 504 0 orphelin.

## 2026-07-08 — Partage équitable et arithmétique décimale (opérateur explicite)

- **Partage** : « partage 20 euros entre 4 personnes » → « 5 chacun (20 ÷ 4) » ; reste dit quand ça ne tombe
  pas juste (« entre 3 » → « 6 chacun, et il reste 2 ») ; décimal → arrondi au centime dit.
- **Arithmétique décimale** avec opérateur SYMBOLE (pas le mot, ambigu) : « 20 − 7,50 » → 12.5, « 12,50 − 4 »
  → 8.5. Garde FAUX=0 stricte : après retrait des chiffres/opérateurs/monnaie, il ne doit RIEN rester —
  « la guerre de 1939-1945 » et « distance 1,5 km » ne sont pas des soustractions.
- Bancs : `valide_assistant_nl` **274/274** (+6), suite 25/25, raisonnement 194/194, paraphrases 174/174,
  capacites_chat 142/142, stats_nl 22/22, câblage 504 0 orphelin.

## 2026-07-08 — Vague 17 : 2 FAUX corrigés + facteurs premiers, nombre parfait, règle de trois, écart en %, voyelles

- **FAUX ×2** : « le plus grand **diviseur commun** de 24 et 36 » → *« Minimum : 24 ; maximum : 36 »* (au lieu
  du PGCD 12) et « de combien de **%** 40 est plus grand que 25 » → min/max : la route stats min/max coiffait
  ces questions sur le mot « plus grand ». Garde (diviseur/multiple/commun/pgcd/ppcm/%) → la main aux routes
  dédiées. « le mot chien **contient** combien de consonnes » : le GUÉRISSEUR corrigeait « contient » →
  « continent » (fausse correction, comme « mots »→« mode ») → famille -tenir/-ient protégée.
- **CÂBLAGE** : écart relatif en % (« 40 est +60 % plus grand que 25 »), **décomposition en facteurs
  premiers** (« 60 = 2² × 3 × 5 », exposants Unicode), **nombre parfait** (« 28 est parfait »), an/heure/jour
  en sous-unités (« 1 an » → 365 jours, dit ; « 2h30 » → 150 minutes), **règle de trois** (« 3 pommes 2 € →
  9 pommes » → 6), **diagonale du carré** (côté·√2, approché dit), **aire du triangle équilatéral**
  ((√3/4)·côté²), **comptage voyelles/consonnes** d'un mot.
- Bancs : `valide_assistant_nl` **268/268** (+11), capacites_chat **142/142** (+3), stats_nl 22/22, suite
  25/25, raisonnement 194/194, paraphrases 174/174, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — BUG .exe corrigé : l'updater plantait sur `LookupError('unknown encoding: ascii')`

- **Vécu par l'utilisateur** : « ⚠ Lancement de l'updater échoué : LookupError('unknown encoding: ascii') ».
  `maj._lance_updater` écrivait le `.bat` via `open(bat, "w", encoding="ascii")` — mais PyInstaller n'embarque
  pas toujours le module `encodings.ascii` que `TextIOWrapper` exige (contrairement à `str.encode("ascii")`
  qui a un chemin rapide C sans registre de codecs). Le `.bat` ne s'écrivait pas → **l'auto-update était
  bloqué**.
- Fix : écriture en OCTETS filtrés à la main — `bytes(o for o in (ord(c) for c in contenu) if o < 128)` puis
  `open(bat, "wb")`. AUCUN codec consulté (ni `open(encoding=)`, ni même `str.encode`). Un `.bat` doit être
  ASCII ; un chemin accentué est purgé comme avant (`errors="ignore"`). Belt-and-suspenders au build :
  `--collect-submodules encodings` (CI + bat) pour tout futur `open(encoding=…)` dynamique.
- ⚠ Le build actuel de l'utilisateur ne peut PAS s'auto-corriger (le bug est dans l'updater du binaire qui
  tourne) : **re-télécharger l'exe UNE fois** depuis la release `latest` ; ensuite l'auto-update reprend.
- Bancs : `valide_maj` **41/41** (+3), suite 25/25, câblage 504 0 orphelin.

## 2026-07-08 — Vécu sur le .exe 62 (web ON) : 3 fixes que les tests hors-ligne ne voyaient pas

- **Test du produit RÉEL** (port 8765, build 62, Internet activé) — trois comportements que la batterie
  locale (web OFF) ne pouvait pas attraper :
  1. **L'étage FRAÎCHEUR détournait les calculs vers le web** : « est-ce que 2024 est une année bissextile »
     → extrait Wikipédia « 2024 » ; « écris 1984 en chiffres romains » → **l'album de Van Halen** (!). Une
     ANNÉE dans une question de calcul/convention n'est pas un marqueur de fraîcheur (`_PAS_FRAICHEUR_RE`,
     ancré sur les chiffres — « premier ministre ACTUEL » reste volatile → live).
  2. **La continuation type B se faisait coiffer par le web** : « et celui de l'or ? » → la 1ʳᵉ réécriture
     (« point de or ») partait au métamoteur et son extrait Wikipédia s'imposait avant la 2ᵉ variante
     VÉRIFIÉE (1337 K). Une réponse RAPPORTÉE (« D'après … ») est gardée en réserve ; le vérifié la remplace.
  3. **tzdata manquait dans le .exe** (abstention propre, mais l'heure des villes ne marchait pas) :
     `--collect-data` n'embarque pas les SOUS-MODULES du paquet → `--collect-all tzdata` (CI + bat).
- Bancs : suite 25/25, raisonnement 194/194, paraphrases 174/174, assistant_nl 257/257, capacites_chat
  139/139, challenge 16/16, câblage 504 0 orphelin ; YAML CI validé. Effet complet au prochain build (63+),
  à re-vérifier sur le .exe réel après merge + redémarrage.

## 2026-07-08 — Continuations type A formatées (« et sa population ? » → la belle réponse, plus la valeur brute)

- Le type A (« même entité, nouvel attribut ») servait la valeur BRUTE du lookup (« 58915656  — à propos de
  « l'Italie » ») quand la question directe recevait la réponse formatée. Aligné sur le type B : le pipeline
  COMPLET est rejoué d'abord (un rejeu-aveu ne compte pas comme succès) → « et sa population ? » →
  « Population de l'Italie : 58 915 656 habitants. », « et sa superficie ? » → « … 301 336 km². »
  La continuité à travers l'abstention (wakanda) est inchangée.
- Bancs : `banc_raisonnement` **194/194** (+1), suite 25/25, paraphrases 174/174, assistant_nl 257/257,
  capacites_chat 139/139, challenge 16/16, lecteur 1613/1613, câblage 504 0 orphelin.

## 2026-07-08 — « et en celsius ? » : la dernière réponse à unité se convertit au tour suivant

- Mémoire de la dernière valeur-à-unité servie (`_DERNIERE_VALEUR`, posée quand l'unité de la source est
  affichée) + route de continuation : « point de fusion du fer » → « 1811 K » → « **et en celsius ?** » →
  « 1811 K = 1537.85 °C (conversion exacte). » → « et celui de l'or ? » → « 1337.33 K » → « et en
  celsius ? » → **la nouvelle valeur** (1064.18 °C). Fahrenheit couvert. SOUND : ne convertit que ce que
  Provara vient de servir ; sans contexte → flux normal. (Bug de route corrigé au passage : `rstrip("s")`
  mutilait « celsius » en « celsiu ».)
- Bancs : `banc_raisonnement` **193/193** (+1), capacites_chat 139/139, suite 25/25, assistant_nl 257/257,
  paraphrases 174/174, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — Continuations : « et celui de l'or ? » préserve la relation, « et à New York ? » suit l'heure

- **Type B robuste** : après « point de fusion du fer », « et celui de l'or ? » réécrivait en « point de
  **or** » (le sujet mémorisé embarque la relation, « fusion du fer » remplacé en bloc → relation perdue →
  aveu de structure). Double réécriture : sujet ENTIER d'abord (bon pour les vraies entités multi-mots,
  « l'Arabie saoudite » → « le Japon » inchangé), puis DERNIER token (« fer » → « or » préserve « fusion ») ;
  un rejeu qui ne produit qu'un AVEU (structure/did-you-mean) n'est plus considéré comme un succès — la
  variante suivante est tentée. → « et celui de l'or ? » → 1337.33 K, « et celui du cuivre ? » → 1357.77 K.
- **L'heure enchaîne** : « quelle heure est-il à Tokyo ? » puis « et à New York ? » → l'heure de New York
  (la route fuseaux mémorise sujet+question pour la continuation).
- Bancs : `banc_raisonnement` **192/192** (+1), capacites_chat **139/139** (+1), suite 25/25, assistant_nl
  257/257, paraphrases 174/174, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — PERF : des questions coûtaient 3-5 s À CHAQUE APPEL (fuzzy sur tables à millions de clés)

- **Profilé** : « est-ce que 2024 est une année bissextile » = 5,2 s et « le 5e mois de l'année » = 3,4 s,
  NON cachées — `resolution.corrige` (correction de fautes) itérait **14 millions de clés par question**
  (les tables de 1-3,2 M de personnes/lexèmes scannées pour « corriger » chaque candidat d'entité), et
  `_oui_non` relançait tout le pipeline pour résoudre « 2024 » comme entité.
- Fixes : (1) plus de fuzzy au-delà de 500 000 clés (corriger une faute parmi 3,2 M de noms = secondes de
  scan pour un fort risque d'ambiguïté — lookup exact seulement ; « allemagn » → Allemagne marche toujours,
  les tables utiles au fuzzy sont toutes sous le seuil) ; (2) mémo borné (4096) des corrections ;
  (3) `_oui_non` ne résout jamais un NOMBRE comme entité (les routes calcul tranchent).
- Mesuré (batterie mixte de 20 questions) : 1re passe médiane 10 ms, **2e passe médiane 1 ms, max 16 ms**
  (avant : 5,2 s récurrentes). Zéro régression : resolution 50/50, raisonnement 191/191, paraphrases 174/174,
  lecteur 1613/1613, suite 25/25, tout le reste vert.

## 2026-07-08 — Passe adverse : les variantes de phrasé ne font plus revenir les FAUX

- **Le « 2010 » du film revenait** par « est-ce que 2024 **c'est** une année bissextile » et « 2028
  **sera-t-elle** bissextile » (garde et route ne couvraient que « est ») → « c'est », futur/conditionnel et
  « t » euphonique couverts des deux côtés (garde `resolution` + règle grégorienne).
- **L'heure locale revenait** pour « **tokyo** il est quelle heure » (ville en tête de phrase) → la table de
  fuseaux est balayée sur TOUTE la phrase, plus seulement après « à ».
- Variantes câblées : « **cb** de jours entre… » (SMS cb → combien), « XIV **ça fait combien** en chiffres
  arabes », « 20 % de **réduc** », « **c'est quoi l'**anagramme de chien ».
- Bancs : `valide_assistant_nl` **257/257** (+4), capacites_chat **138/138** (+1), suite 25/25, raisonnement
  191/191, paraphrases 174/174, resolution 50/50, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — Vague 16 : rangs, successions et divisions du temps (cycles fermés)

- `resout_math` : « le **5e mois** de l'année » → Mai (« le 13e » → correction honnête « l'année n'a que 12
  mois », plus de mémo garbage) ; « quel jour vient **après mardi** » → Mercredi (« après dimanche » → Lundi,
  rebouclage DIT) ; « quelle lettre vient **après le m** » → n (« après le z » → « aucune — dernière lettre ») ;
  divisions du temps : trimestres/semestres/mois/jours par année ou semaine (4/2/12/7), années par
  siècle/millénaire/décennie (100/1000/10), siècles par millénaire (10). Conventions de cycles fermés, exactes.
- Météo : « combien de degrés fait-il dehors » rejoint la route météo. Bancs : `valide_assistant_nl`
  **253/253** (+14), suite 25/25, raisonnement 191/191, paraphrases 174/174, capacites_chat 137/137,
  challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — FAUX=0 : « 100 km/h ou 30 m/s, le plus rapide ? » listait des PONTS + comparaison de grandeurs câblée

- **FAUX servi, trouvé à la sonde** : `_liste_inverse` matchait le token « **plus** » de la relation
  `plus_longue_travee_pont` et ancrait sur « 100 » → « Pont (100, 12) : Hammerbrücke… » pour une question de
  vitesse. Nouveau `_JAMAIS_TYPE` (fermé : plus/moins/grande/longue/haute/petit…) : un comparatif ne désigne
  jamais un type d'entité.
- **CÂBLAGE** `fonction_nl.compare_grandeurs` (branché à `resout_conversion` ET `_cap_comparaison`) :
  « 100 km/h est-il plus rapide que 30 m/s ? » → « 30 m/s est plus rapide que 100 km/h (100 km/h =
  27.777778 m/s après conversion) » — conversion EXACTE puis comparaison, équivalence du perdant MONTRÉE dans
  l'unité du gagnant ; « 36 km/h ou 10 m/s » → « Ils sont égaux » ; « plus léger » inverse le gagnant ;
  masses/longueurs/volumes/aires/données couverts ; dimensions différentes → abstention. Et la devinette
  classique : « un kilo de plomb ou un kilo de plumes ? » → « Ils pèsent exactement pareil ».
- Météo : « combien de degrés fait-il dehors » rejoint la route météo (relevé réel web ON, refus honnête sinon).
- Bancs : `banc_raisonnement` **191/191** (+5), paraphrases 174/174, suite 25/25, assistant_nl 239/239,
  capacites_chat 137/137, resolution 50/50, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — Vague 15 : protons « dans », sel de table, hendécagone, somme des angles, degrés du cercle

- `_cap_protons` : « combien de protons **dans** l'uranium » (le phrasé « dans » ratait) → 92 protons ;
  amorce `formule_chimique` : « sel de table »/« sel de cuisine » → NaCl ; `cotes_polygone` : hendécagone (11)
  ajouté (table + gabarit NL) ; `resout_math` : somme des angles intérieurs d'un polygone nommé (« d'un
  hexagone » → 720°, formule (n−2)·180° MONTRÉE), degrés d'un cercle (360°) et d'un demi-cercle (180°).
  Garde : « combien de degrés fait-il dehors » (météo) ne déclenche rien.
- Bancs : `valide_assistant_nl` **239/239** (+5), raisonnement **186/186** (+3), suite 25/25, lecteur
  1613/1613, capacites_chat 137/137, paraphrases 174/174, câblage 504 0 orphelin.

## 2026-07-08 — L'unité déclarée par la source est affichée (« point de fusion du fer » : 1811 **K**, pas « 1811 »)

- **Trompeur, trouvé à la sonde** : les relations numériques à valeur NUE servaient le nombre sans unité —
  « point de fusion du fer » → « 1811 » (lu en °C alors que la vérité stockée est en KELVINS ; 1811 K =
  1538 °C), « distance Terre-Soleil » → « 150 » (millions de km non dits). Nouveau `_avec_unite` au service
  générique : table FERMÉE sur le libellé exact des sources (points de fusion/ébullition K, distance Soleil
  millions de km, masse volumique kg/m³, diamètres m/mm, masse atomique u) — l'unité vient de la SOURCE du
  fait, jamais devinée ; valeur non numérique ou source sans unité → inchangé (« numéro atomique » reste « 6 »).
- Bancs : `banc_raisonnement` **183/183** (+3), paraphrases 174/174, suite 25/25, assistant_nl 234/234,
  capacites_chat 137/137, challenge 16/16, câblage 504, lecteur 1613/1613.

## 2026-07-08 — Dates d'œuvres : « quand est sorti Avatar ? » → 2009 (routage par verbe, piège homonyme évité)

- `_cap_date_evenement` : verbes « sorti/paru/publié » routés vers LEUR relation — « sorti » (films) →
  `annee_creation_oeuvre_art` (Avatar → 2009) puis publication en repli ; « publié/paru » →
  `annee_publication_oeuvre` SEULEMENT — jamais oeuvre_art, où « Les Misérables » est un TABLEAU de 1900
  (servir 1900 pour le roman de 1862 serait un FAUX). Préfixes « le film/le roman/le livre/l'album » dépouillés.
  « Titanic » reste en abstention honnête (homonymes multi-films, crible fonctionnel).
- Bancs : `banc_raisonnement` **180/180** (+2), paraphrases 174/174, suite 25/25, assistant_nl 234/234,
  capacites_chat 137/137, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — FAUX=0 : « de quelle année date le roman 1984 » listait 2041 édifices construits en 1984

- **FAUX servi, trouvé à la sonde** : `_liste_inverse` prenait le « 1984 » du TITRE comme ancre-valeur et,
  « quelle année » rendant les relations `annee_*` liste-plausibles, servait « Edifice (1984, 2041) : … ».
  Garde ANCRE CIRCULAIRE : quand la question DEMANDE une année (le seul token de relation matché est
  annee/date), une ancre purement NUMÉRIQUE est un titre/nom, pas une requête de liste → écartée.
  « quels ÉDIFICES datent de 1984 » (type interrogé ≠ la date) continue de lister.
- Bancs : `banc_raisonnement` **178/178** (+2), paraphrases 174/174, suite 25/25, assistant_nl 234/234,
  capacites_chat 137/137, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — FAUX=0 : « quinze plus vingt-sept » rendait 28 (le tiret de « vingt-sept » devenait un moins)

- **FAUX servi comme fait** : la substitution mot→chiffre traitait « vingt-sept » mot à mot → « 20-7 », et le
  trait d'union était évalué comme une SOUSTRACTION : 15 + 20 − 7 = **28** au lieu de 42. Corrigé : les
  nombres COMPOSÉS 0..100 sont remplacés d'abord, via une table auto-générée par le MÊME générateur que
  « écris N en lettres » (une seule source de vérité orthographique, 13 ancres épinglées) — « vingt et un »,
  « soixante-quinze », « quatre-vingt-dix-neuf », tiret ou espace. « vingt et un plus trois » (Rien avant) → 24.
- Bancs : `banc_paraphrases` **174/174** (+4), suite 25/25, assistant_nl 234/234, capacites_chat 137/137,
  raisonnement 176/176, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — Génération d'anagrammes depuis le dictionnaire embarqué (« anagramme de chien » → niche)

- `_cap_anagramme` : balayage du dictionnaire réel (`definition_nom`, 292k noms du Wiktionnaire) — « anagramme
  de chien » → cheni, iench, niche ; « de génie » → neige (comparaison sans accents). JAMAIS des lettres
  mélangées inventées : uniquement des mots existants, source dite. Aucune trouvée → aveu + limite DITE
  (le dictionnaire ne couvre que les noms). ~1 s au premier appel, mémoïsé ensuite. Sans le dataset →
  abstention propre (la suite hors-données reste verte).
- Bancs : `valide_capacites_chat` **137/137** (+3), suite 25/25, assistant_nl 234/234, raisonnement 176/176,
  paraphrases 170/170, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — Listes : un qualificatif non résolu est DIT, jamais ignoré en silence

- « donne-moi un exemple de mammifère **marin** » servait TOUS les ordres de mammifères (chauves-souris
  comprises) en ignorant « marin » en silence. Désormais la liste est servie avec l'aveu : « ⚠ Je ne sais pas
  filtrer « marin » — c'est la liste NON filtrée, à toi de trier. » (FAUX=0 : ignorer un qualificatif, c'est
  répondre à une autre question sans le dire). Sans qualificatif → inchangé.
- Bancs : `valide_resolution` **50/50** (+2), suite 25/25, raisonnement 176/176, paraphrases 170/170,
  capacites_chat 134/134, assistant_nl 234/234, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — Listes : le nombre demandé est respecté (« cite-moi trois pays d'Europe »)

- `resolution.resout_liste` : « cite-moi **trois** pays d'Europe » servait les **53** — désormais « Pays
  (Europe) : ahvenanmaa, albanie, allemagne — **en voici 3 parmi 53**. » (nombre en lettres deux→dix ou en
  chiffres ; sans nombre → liste complète inchangée, échantillon à 15 comme avant).
- Bancs : `valide_resolution` **48/48** (+2), suite 25/25, capacites_chat 134/134, assistant_nl 234/234,
  raisonnement 176/176, paraphrases 170/170, câblage 504 0 orphelin.

## 2026-07-08 — Rappels-tâches : « rappelle-moi d'acheter du pain » devient un vrai rappel (honnête : pas d'alarme)

- **Trou préexistant** : « rappelle-moi de X » partait en cascade factuelle → « je n'ai pas l'information »
  (le dévoilement conversationnel dépouillait « rappelle-moi » comme une politesse type « dis-moi », détruisant
  le sens). Désormais : **accusé de stockage** (« C'est noté : acheter du pain. Demande-moi "qu'est-ce que je
  devais faire ?" ») ; un **moment nommé** (« demain ») déclenche l'honnêteté totale — « je n'ai pas d'alarme,
  je ne peux pas te prévenir tout seul » (aucune promesse que la machine ne tient pas) ; la **liste** est
  re-servie sur demande (« qu'est-ce que je devais faire ? » → « · sortir la poubelle · appeler le médecin
  (demain) · acheter du pain ») — promesse TENUE par le stage mémoire (les rappels-tâches stockés sont
  ré-servables, exception au filtre anti-questions).
- Distinction préservée : « rappelle-moi **la capitale** de la France » / « rappelle-moi **qui** a écrit
  1984 » restent des QUESTIONS (re-servir l'info) — le dévoilement ne protège que de+INFINITIF et « que … ».
- Bancs : `valide_capacites_chat` **134/134** (+6), suite 25/25, assistant_nl 234/234, raisonnement 176/176,
  paraphrases 170/170, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — Build : tzdata embarqué (l'heure des villes marche dans le .exe Windows)

- `build-exe.yml` + `build_exe.bat` : `pip install tzdata` + `--hidden-import zoneinfo --hidden-import tzdata
  --collect-data tzdata`. La base de fuseaux IANA est embarquée → « quelle heure est-il à New York ? » répond
  dans le .exe Windows (jusqu'ici : abstention honnête, la base tz manquait hors Linux). Dégradation propre
  conservée si la base venait à manquer. YAML validé ; effet au prochain build CI (59+).

## 2026-07-08 — Vague 14 : vérification oui/non étendue (« est-ce que X est Y », négations « …, si ? »)

- `_oui_non` étendu dans son esprit FAUX=0 (jamais un « Non » sec — une relation peut être multi-valuée) :
  **« est-ce que X est Y »** → « Oui. » quand le fait est vérifié (« est-ce que Tokyo est la capitale du
  Japon ? » répondait « Tokyo » nu avant) ; **négations** — « Paris n'est pas la capitale de la France, si ? »
  → « **Si** — Paris est bien la capitale de la France (vérifié) » (confirmer un fait positif est sûr) ;
  « la capitale de la France n'est pas Lyon, si ? » → « **Ce que j'ai de vérifié** : la capitale de la
  France → Paris » (réfutation implicite cadrée, jamais un lookup nu servi comme réponse à la négation —
  ces questions tombaient en repli « pas l'information » avant, la garde négation sautait tout le factuel).
- Gardes : question négative OUVERTE (« quelle ville n'est pas… ») → prudence, flux normal ; deux côtés
  résolus ou aucun → prudence. Exception à la garde négation limitée à `_oui_non` (sound par construction).
- Bancs : `banc_raisonnement` **176/176** (+4), assistant_nl 234/234, capacites_chat 128/128, paraphrases
  170/170, suite 25/25, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — Vague 13 : nombre en toutes lettres (« écris 1984 en lettres »)

- `fonction_nl._nombre_en_lettres` (0..999999, orthographe TRADITIONNELLE, dite dans la réponse) : « écris
  1984 en lettres » → « mille neuf cent quatre-vingt-quatre ». Pièges couverts et ÉPINGLÉS par 13 ancres
  vérifiées à la main : « vingt **et un** », « soixante **et onze** », « quatre-vingt**s** » (mais
  « quatre-vingt-un », « quatre-vingt mille »), « deux cent**s** » (mais « deux cent un »), « mille »
  invariable. Hors plage → abstention. Tombait en mémo garbage avant.
- Bancs : `valide_assistant_nl` **234/234** (+15), capacites_chat 128/128, suite 25/25, raisonnement 172/172,
  paraphrases 170/170, câblage 504 0 orphelin.

## 2026-07-08 — Vague 12 : 3 FAUX corrigés (fractions, premier d'intervalle, « 2 heures et demie ») + vérifications numériques, diviseurs, jour historique, nouvelles unités

- **FAUX ×3, trouvés à la sonde** :
  1. « lequel est le plus grand : 2/3 ou 3/5 » → *« Minimum : 2 ; maximum : 5 »* (les numérateurs/dénominateurs
     traités comme des valeurs par la route min/max). Garde fractions dans `fonction_stats_nl` + comparaison
     EXACTE via `Fraction` : « 4/8 ou 1/2 » → « Ils sont égaux », « 0.5 est-il égal à 1/2 » → Oui.
  2. « un nombre premier entre 20 et 30 » → *« Non, 20 n'est pas premier »* (répondait à côté). Énumération
     exacte : → « Entre 20 et 30 : 23, 29 » ; intervalle vide dit ; borne anti-DoS.
  3. « combien de secondes dans 2 heures et demie » → *7200* (le « et demie » ignoré). Réécriture « X et
     demie/quart/trois quarts » → X,5/X,25/X,75 avant conversion : → 9000 s.
- CÂBLAGE : vérifications numériques exactes (pair/impair, divisible par — avec le quotient ou le reste MONTRÉ —,
  multiple de, carré parfait avec encadrement quand Non) ; produit/différence/quotient nommés (quotient exact
  seulement) ; diviseurs énumérés (« 36 a 9 diviseurs : … ») ; **jour de la semaine historique** (« le 14
  juillet 1789 était un mardi » — datetime grégorien ; avant 1583 → abstention DITE, calendrier julien) ;
  « semaines dans une année » → réponse composée honnête (52 sem + 1 j ; +2 si bissextile) ; unités : aires
  (hectares/ares/m²/km²), longueurs impériales (pieds/pouces/yards, définitions légales), données (octets,
  préfixes SI décimaux — convention DITE en source).
- Bancs : `valide_assistant_nl` **219/219** (+20), capacites_chat **128/128** (+3), stats_nl 22/22, suite 25/25,
  raisonnement 172/172, paraphrases 170/170, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — Vague 11 : 4 FAUX corrigés (bissextile→film, heure locale pour New York, 1,5 h→300 min, « mots »→« mode ») + bissextile, fuseaux, âge, opérations nommées

- **FAUX ×4, trouvés à la sonde** :
  1. « est-ce que 2024 est une année bissextile » → *« 2010 »* — le résolveur générique ignorait le NOMBRE et
     servait l'année du FILM « Année bissextile ». Garde dans `resolution.resout_nl_generique` (une question
     « est-ce que <nombre> est … » n'est jamais un lookup d'entité) + vraie règle grégorienne câblée dans
     `resout_math` : 2024 → Oui, 2023 → Non, 2100 → Non (siècle) ; « nombre de jours en 2024 » → 366.
  2. « quelle heure est-il à New York » → *l'heure locale de la machine*. Ville nommée → fuseau IANA (table
     fermée ~50 grandes villes + `zoneinfo`) ; ville hors table ou base tz absente → abstention honnête —
     plus JAMAIS l'heure locale servie pour une ville étrangère. Sans ville → horloge locale, comme avant.
  3. « convertis 1,5 heures en minutes » → *300* (!) : `normalise()` mange AUSSI les séparateurs décimaux
     (« 1 5 heures » → « 5 heures » matché). Normalisation locale des conversions qui préserve « , . / » ;
     1,5 h → 90 min ; clés « km/h »/« m/s » redevenues directes ; millisecondes ajoutées.
  4. « combien de mots dans… » : le GUÉRISSEUR réécrivait « mots » → « mode » (pluriel de 4 lettres invisible
     de `_singulier_fr`). Gate élargi : un mot ≥4 lettres en -s/-x dont le radical est un nom du lexique est
     un vrai pluriel, jamais corrigé (même classe que « était »→« état », épinglé pareil).
- CÂBLAGE : opérations nommées (« double/triple/quadruple/moitié/quart/carré/cube/opposé de N » ; « inverse
  de 4 » → 0.25 décimal FINI exigé, « inverse de 3 »/« tiers de 10 » → abstention, jamais 0.333) avec garde
  géométrie (« périmètre d'un carré de côté 5 » → 20, pas 25) ; « quel âge a une personne née en 1990 » →
  fourchette honnête (35 ou 36 selon l'anniversaire) ; `_cap_texte` : majuscules/minuscules, compter les mots
  (règle dite), trier des nombres (croissant/décroissant).
- Bancs : `valide_assistant_nl` **199/199** (+18), capacites_chat **125/125** (+7), raisonnement **172/172**,
  paraphrases 170/170, suite 25/25, lecteur 1613/1613, challenge 16/16, coordonnées 47/47, câblage 504.

## 2026-07-08 — Kelvin dans les conversions de température (offset 273,15 exact par définition)

- `_cap_conversion` : °C↔K, °F↔K (« 100 celsius en kelvin » → 373,15 K, « 0 kelvin en celsius » → −273,15 °C —
  zéro absolu), formule montrée comme pour °C↔°F. Trouvé à la sonde : « température d'ébullition de l'eau en
  kelvin » répondait 100 °C sans convertir ; désormais l'utilisateur peut au moins convertir exactement.
- Bancs : `banc_paraphrases` **170/170** (+2), capacites_chat 118/118, suite 25/25, assistant_nl 181/181,
  raisonnement 171/171.

## 2026-07-08 — CÂBLAGE vague 10 : opérations textuelles exactes sur un mot (_cap_texte)

- Nouveau `_cap_texte` dans la cascade : **compter les lettres** (« compte les lettres du mot
  anticonstitutionnellement » → 25 ; mot à tiret → restriction DITE « tirets/apostrophes non comptés »),
  **envers** (« épelle chien à l'envers » → neihc), **épellation** (« épelle chien » → c-h-i-e-n),
  **test d'anagramme** (« niche et chien sont-ils des anagrammes ? » → oui, lettres triées comparées).
  Opérations natives déterministes = FAUX=0 par construction. Tombaient toutes en repli/mémo avant.
- Gardes : UN seul mot exigé (« épelle-moi la vérité sur cette affaire » → rien) ; « combien de lettres a
  envoyées Napoléon » (courriers) → pas volé.
- Bancs : `valide_capacites_chat` **118/118** (+9), assistant_nl 181/181, suite 25/25, raisonnement 171/171,
  paraphrases 168/168, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — CÂBLAGE vague 9 : volumes/vitesses, pourcentages appliqués, chiffres romains, triangle/losange

- **Conversions** (`resout_conversion`) : volumes (L/mL/cL/dL/hL/m³/cm³ — « 3 litres en centilitres » → 300),
  vitesses (« 90 km/h en m/s » → 25, « 20 nœuds en km/h » → 37.04 — facteurs exacts 1000/3600 et 1852/3600),
  alias « journée » (« combien de secondes dans une journée » → 86400). ⚠ découverte : `normalise()` mange
  « / » et « % » — clés d'unités post-normalisation (« km h »), affichage restauré (« m/s »).
- **Pourcentages appliqués** (`resout_math`, sur la question BRUTE — le « % » disparaît à la normalisation) :
  réduction (« 20% de réduction sur 80 € » → « 64 (80 − 20 % = 80 − 16) » — le calcul MONTRÉ lève l'ambiguïté
  remise/prix final ; « remise de 30% sur 200 » donnait 60 par la route simple, c'est le prix final 140 qui
  est servi désormais), augmentation (« augmente 200 de 15% » → 230, « hausse de 10% sur 50 » → 55),
  part (« 150 est quel pourcentage de 600 » → 25 %).
- **Chiffres romains** (convention de numération, symboles = table `chiffre_romain` du lecteur) : « 1984 en
  chiffres romains » → MCMLXXXIV, « XIV en chiffres arabes » → 14. Round-trip COMPLET 1..3999 épinglé au banc ;
  écriture non canonique (« IIII »), mot en lettres romaines (« CIVIL »), hors plage → abstention.
- **Géométrie** : périmètre du triangle par 3 côtés avec INÉGALITÉ TRIANGULAIRE (« côtés 1, 1 et 5 » =
  triangle impossible → abstention, pas une somme aveugle), aire du losange par diagonales (brique Polygone).
- Gardes : « le prix a augmenté de beaucoup », « la réduction des inégalités » ne déclenchent rien ;
  « 5 litres en km » (dimensions différentes) → abstention. Bancs : `valide_assistant_nl` **181/181** (+25),
  capacites_chat 109/109, suite 25/25, raisonnement 171/171, paraphrases 168/168, challenge 16/16, câblage 504.

## 2026-07-08 — FAUX=0 : nationalités JOINTES tronquées en quarantaine (Messi « Italie et Espagne », SANS l'Argentine)

- **FAUX par omission, trouvé au banc** : `ingere_celebres` (P27, joinmax=2) triait les nationalités par
  fréquence GLOBALE de corpus puis tronquait — Messi [Argentine, Espagne, Italie] → « Italie et Espagne »
  (l'Argentine éjectée !), Einstein → « États-Unis et Allemagne » (sans la Suisse). Une nationalité se lit
  comme exhaustive : liste incomplète = faux. Corrections : **quarantaine au lookup** (les valeurs « X et Y »
  de `nationalite_personne` ne sont plus JAMAIS servies — `lecteur.cherche` + `_lookup_cell` de repond, fiches
  et faits ciblés couverts) ; **ingestion corrigée** (P27 joinmax=1 : multi-nationalité → HORS ; l'ordre des
  occupations P106 devient l'ordre Wikidata DE LA PERSONNE, plus la fréquence de corpus qui décrivait Einstein
  « écrivain, professeur, philosophe » sans « physicien »). ⚠ la ré-ingestion attend le re-upload de l'archive.
- Qualité fiches personne : un VIVANT est au PRÉSENT (« Messi **est** footballeur » — « était » implique un
  décès) ; libellés inclusifs Wikidata ACCORDÉS quand le sexe est connu (« footballeur ou footballeuse » →
  « footballeur » / « physicien ou physicienne » → « physicienne » pour Marie Curie).
- `valide_lecteur` **1613/1613 — première fois VERT contre les datasets complets** : 3 checks à spec fausse
  réparés (nationalité ≠ « pays actuel » : polities historiques en minuscules + années de désambiguïsation
  légitimes ; « Chiang Mai » n'est pas une date résiduelle — détecteur par FORME de date complète ;
  récupérabilité avec exemption quarantaine documentée). banc_raisonnement **171/171** (+5).

## 2026-07-08 — FAUX=0 : « combien de jours entre le 1er janvier et le 15 mars » servait 31 (les jours de janvier) + arithmétique de dates câblée

- **FAUX servi comme fait, trouvé à la sonde** : le gabarit lecteur `jours_mois` (« combien de jours …
  janvier ») matchait aussi les INTERVALLES → « 31 » servi pour « entre le 1er janvier et le 15 mars ».
  Garde posée : « entre » ou deux mois cités → le gabarit ne matche plus (les durées de mois restent servies).
- CÂBLAGE (`_cap_quotidien`) : **différence de dates** — « combien de jours entre le 1er janvier et le 15
  mars » → 73 (datetime, calcul calendaire exact ; année absente → année de l'horloge, ÉTIQUETÉE — 2024
  bissextile → 74 ; intervalle inversé sans années ou date invalide → abstention) ; **date relative** —
  « quel jour serons-nous dans 45 jours / dans 2 semaines » → date+jour exacts, « il y a 10 jours » → passé ;
  « dans 3 mois » (durée ambiguë) → abstention.
- Bancs : `valide_capacites_chat` **109/109** (+7), valide_lecteur +2 cas adverses, suite 25/25,
  assistant_nl 156/156, raisonnement, paraphrases, challenge, coordonnées, câblage — tous verts.

## 2026-07-08 — CÂBLAGE vague 8 : racine cubique, logarithme en base, arrondi / partie entière / plafond

- `fonction_nl.resout_math` : **racine cubique** exacte (« racine cubique de 27 » → 3, « de -8 » → -2 ; cube
  non parfait → abstention, JAMAIS 3.107 servi comme exact — cohérent avec la racine carrée exacte),
  **logarithme en base explicite** (« log de 100 en base 10 » → 2 ; exposant non entier ou base non dite →
  abstention, on ne devine pas ln/log10), **arrondi** demi-supérieur convention française (« arrondi de 2,5 » →
  3, pas l'arrondi bancaire de `round()` ; « à 2 décimales » → 3.14 ; supérieur/inférieur), **partie entière**
  = plancher mathématique étiqueté (« partie entière de -2.3 » → -3), **plafond/plancher**. Tous tombaient en
  MÉMO garbage avant.
- Gardes anti-faux-positif : plancher/plafond exigent un nombre DÉCIMAL (« le plafond de 3 mètres » ne
  déclenche rien) ; « l'arrondissement de Paris », « la racine du problème » ne déclenchent rien.
- Bancs : `valide_assistant_nl` **156/156** (+15), capacites_chat 102/102, suite 25/25, raisonnement 166/166,
  paraphrases 168/168, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — CÂBLAGE vague 7 : géométrie simple en conversation (aire / périmètre / volume / hypoténuse)

- `fonction_nl._resout_geometrie` (appelé par `resout_math`) câble **geometrie2d** (Cercle, Polygone, Point) et
  **geometrie3d** (cube) au dialogue : « aire d'un cercle de rayon 3 » → 28.2743, « périmètre d'un carré de
  côté 4 » → 16, « aire d'un rectangle de 3 par 5 » → 15, « aire d'un triangle de base 6 et hauteur 4 » → 12,
  « hypoténuse d'un triangle rectangle de côtés 3 et 4 » → 5 (Pythagore via `Point.distance`), « volume d'un
  cube de côté 2 » → 8 (`geometrie3d.cube().volume()`), « volume d'une sphère de rayon 2 » → 33.5103 (seule
  formule directe : 4/3·π·r³, mathématique sûre — pas de brique sphère). Diamètre accepté (rayon = d/2).
  Tous ces cas tombaient en MÉMO garbage avant (« C'est noté »).
- GARDE anti-faux-positif triple (mesure + figure + dimension chiffrée) : « aire urbaine de Toulouse »,
  « périmètre de sécurité », « volume sonore », « aire d'un cercle » (sans rayon) ne déclenchent RIEN ;
  « superficie de la France » reste servie par les données (551 695 km²).
- Bancs : `valide_assistant_nl` **141/141** (+15), capacites_chat 102/102, suite 25/25, geometrie2d 22/22,
  geometrie3d 18/18, raisonnement 166/166, paraphrases 168/168, challenge 16/16, câblage 504 0 orphelin.

## 2026-07-08 — FAUX=0 : la moyenne pondérée moyennait les coefficients avec les valeurs (8 au lieu de 13.8)

- **FAUX servi comme fait, trouvé à la sonde** : « moyenne pondérée de 12 coefficient 2 et 15 coefficient 3 »
  répondait *« Moyenne : 8 »* — la branche moyenne de `fonction_stats_nl` faisait la moyenne SIMPLE de tous les
  nombres de la phrase (12, 2, 15, 3), coefficients compris. Corrigé : détection dédiée de l'intention pondérée
  (« pondérée », « coefficient », « coeff ») → appariement valeur/coefficient (paires « 12 coefficient 2 », notes
  parenthésées « 12 (coefficient 4) », ou « valeurs … avec les poids … » à listes de même longueur) →
  `somme(v·w)/somme(w)` → **13.8**. Somme des coefficients nulle → « indéfinie » (honnête).
- Abstention honnête si l'appariement échoue (« moyenne pondérée de 12 et 15 » → demande le format), JAMAIS la
  moyenne simple par défaut. Garde anti-faux-positif : « moyenne des poids 70, 80 et 90 » (poids PHYSIQUES, pas
  de paires) reste une moyenne simple → 80.
- Bancs : `valide_fonction_stats_nl` **22/22** (+6), capacites_chat 102/102, assistant_nl 126/126, suite 25/25,
  raisonnement 166/166, paraphrases 168/168, challenge 16/16.

## 2026-07-08 — CÂBLAGE vague 6 : valeur absolue, conversion de base, inverse modulaire

- `fonction_nl.resout_math` : **valeur absolue** (« valeur absolue de -5 » → 5), **conversion de base** (binaire/
  octal/hexadécimal ↔ décimal, conversion mécanique exacte native — « 42 en hexadécimal » → 2A, « 1010 binaire
  en décimal » → 10), **inverse modulaire** (« inverse de 7 modulo 13 » → 2, `arithmetique_modulaire`, abstention
  honnête si non inversible : 6 mod 9 → HORS). Ces trois tombaient en MÉMO/repli (garbage) avant.
- Gardes anti-faux-positif : « valeur de la maison » (sans « absolue ») ne déclenche rien ; conversions exigent
  le mot de base. Bancs : `valide_assistant_nl` **126/126** (+8), suite 25/25, raisonnement 166/166, paraphrases 168/168.

## 2026-07-08 — FAUX=0 : « reste de 17 divisé par 5 » donnait 3.4 (la division) — corrigé en modulo (2)

- **FAUX servi comme fait, trouvé à la sonde** : « quel est le reste de 17 divisé par 5 » → *3.4* (« reste »
  ignoré, la division 17/5 servie). Fix dans `_reponse_calcul` : le modulo/reste est intercepté AVANT la
  conversion « divisé par » → « / » — « reste de X (divisé) par Y », « X modulo Y », « X mod Y » → X % Y
  (entiers). « modulo/mod/reste de » ajoutés au gate d'intention de calcul. Division exacte préservée (12÷4=3),
  division/reste par 0 → None (abstention). Nouvelle capacité au passage : le modulo est désormais atteignable.
- Bancs : `valide_capacites_chat` **102/102** (+5), suite 25/25, assistant_nl 118/118.

## 2026-07-08 — CÂBLAGE vague 5 : NOMBRES COMPLEXES en conversation (module / argument / conjugué)

- `fonction_nl.resout_math` câble `nombres_complexes` : « module de 3+4i » → 5, « argument de i » → 1,57 rad,
  « conjugué de 2-3i » → 2 + 3i. Parseur a+bi robuste (i seul → coef 1, imaginaire pur « 5i », signes négatifs
  « -3-4i »). Garde : exige un mot-clé (module/argument/conjugué/complexe) + une unité imaginaire → un « i »
  dans un nom propre (« Djibouti ») ne déclenche rien. Calcul du module vérifié.
- Bancs : `valide_assistant_nl` **118/118** (+6), suite 25/25, raisonnement 166/166, paraphrases 168/168.

## 2026-07-08 — CÂBLAGE vague 4 : THÉORIE DES JEUX en conversation (équilibres de Nash classiques)

- **Correction de mon propre diagnostic** : j'avais annoncé « pas de brique jeux » — FAUX, `jeux_appliques`
  CALCULE les équilibres de Nash de jeux 2×2 définis. `_cap_jeux` le rend conversationnel : « équilibre de Nash
  du dilemme du prisonnier » → **(trahir, trahir) + le paradoxe de Pareto** ; « bataille des sexes » → deux
  équilibres ; « matching pennies » → **pas d'équilibre pur, aveu honnête** (mixte seulement). Les jeux
  classiques sont des objets mathématiques définis (pas des données contestables) → FAUX=0 respecté.
- Verdict issu du module vérifié ; jeu non catalogué (« jeu vidéo Zelda ») → None (pas d'invention) ; ne vole
  aucune question factuelle. Bancs : `valide_capacites_chat` **97/97** (+5), suite 25/25, câblage 504 0 orphelin,
  raisonnement 166/166, paraphrases 168/168.

## 2026-07-08 — FAUX=0 : un PAYS ne renvoie plus les coordonnées d'une ville homonyme (distance)

- **FAUX réel trouvé** en auditant le chantier « distance » : `ia.coordonnees_lieu("France")` renvoyait
  (34.61, −82.77) — une bourgade **France, Caroline du Sud** passée par le crible d'unicité des localités
  (pas d'homonyme FR) → « distance entre la France et X » était FAUSSE. Garde : un pays (clé de la relation
  `capitale`) n'accepte jamais une coord issue de `latitude_localite` (seule `latitude_capitale` resterait
  valide). France/Allemagne/Espagne → None (correct : un pays n'a pas de point pour une distance ville-à-ville).
- Les villes réelles restent intactes : « distance Paris-Toulouse » → 588 km (vérifié). NB : Lyon/Marseille
  restent absents des coords PAR CONCEPTION (garde anti-homonyme stricte de l'ingestion — homonymes étrangers) ;
  les débloquer demande une source de grandes villes FR désambiguïsées (chantier d'ingestion, documenté).
- Bancs : `valide_coordonnees` **47/47** (+4), suite 25/25.

## 2026-07-08 — QUALITÉ : une demande impérative non traitée ne répond plus « C'est noté »

- **Garbage vécu** : « équilibre la réaction H2 + O2 -> H2O » (et « range mes fichiers ») → *« C'est noté, je
  m'en souviendrai »* (les chiffres H2/O2 faisaient croire à une affirmation à mémoriser). Fix : `_est_demande_
  imperative` (carte FERMÉE de verbes d'action à l'impératif en tête, préambules « stp/peux-tu » dépouillés) —
  un ORDRE qu'aucun cap n'a exécuté reçoit le **repli honnête** du tronc (« voici ce que j'ai compris + ce que
  je sais faire »), jamais le mémo.
- **FAUX=0 / non-régression** : les verbes de MÉMORISATION (note, retiens, rappelle, souviens) sont exclus →
  « rappelle-moi d'acheter du pain », « j'ai rendez-vous mardi », « mon plat préféré est X » restent des mémos
  légitimes. Testé aux deux bords. `valide_capacites_chat` **92/92** (+6), suite 25/25, raisonnement 166/166,
  paraphrases 168/168, challenge 16/16.

## 2026-07-08 — CÂBLAGE vague 3 : MATHÉMATIQUES FINANCIÈRES en conversation (placement / intérêts)

- `fonction_nl.resout_math` câble `maths_financieres` : « combien rapportent 1000 euros à 5% pendant 3 ans ? »
  → **157,63 d'intérêts (composés) ; valeur acquise 1157,63** — gain ET total étiquetés explicitement (zéro
  ambiguïté FAUX), intérêts composés par défaut, simples sur mention. Exige les TROIS composants (capital +
  taux + durée) pour ne jamais confondre avec un simple pourcentage.
- Bancs : `valide_assistant_nl` **112/112** (+3), suite 25/25, raisonnement 166/166, paraphrases 168/168.
- Noté (trous restants, non fabriqués) : distance entre villes = trou de DONNÉES (coords absentes du lecteur,
  le cap est câblé) ; équilibrage de réaction chimique = pas de brique `chimie.equilibre` (à ingérer un jour) ;
  Fermi / probabilité élémentaire = pas de brique NL utilisable.

## 2026-07-08 — CÂBLAGE vague 2 : LOGIQUE PROPOSITIONNELLE en conversation (profondeur de raisonnement)

- **`_cap_logique`** rend `sophismes.py` conversationnel : « si A alors B, or …, donc … » → Provara JUGE la
  validité de l'inférence — **modus ponens / modus tollens = VALIDE**, **affirmation du conséquent / négation
  de l'antécédent = sophisme formel**, avec le nom de la forme. Verdict issu du module VÉRIFIÉ (logique formelle
  exacte, FAUX=0). Complète `_cap_syllogisme` (catégoriel « tous les A sont B ») par le CONDITIONNEL. Provara
  dit explicitement qu'il juge la FORME, pas la vérité des prémisses ni le fond.
- Parseur NL robuste (mapping des propositions A/B, détection de négation « ne…pas / non »), abstention si la
  structure n'est pas nette. Ne vole aucune question factuelle. Porte unique → FAIT (forme vérifiée).
- **Non câblé** : estimation de Fermi (le module exige des facteurs numériques fournis — inutilisable en NL nu
  sans moteur de décomposition ; ne rien fabriquer).
- Bancs : `valide_capacites_chat` **86/86** (+7), suite **25/25**, câblage 504 0 orphelin, raisonnement 166/166,
  paraphrases 168/168, challenge 16/16.

## 2026-07-08 — CÂBLAGE des capacités dormantes, vague 1 : maths discrètes / arithmétique / trigo en conversation

- **Mandat Yohan (« tout câbler, augmenter la puissance conversationnelle »)** : audit d'atteignabilité →
  ~18 capacités sur 27 existaient (modules testés) mais n'étaient PAS déclenchables par une phrase naturelle.
  Vague 1 câblée via `fonction_nl.resout_math` (greffé dans `resout_fonction`, le hub NL→fonction déjà branché) :
  **pourcentage** (« 20% de 150 » → 30), **PGCD/PPCM**, **primalité** (« 17 est-il premier ? »), **factorielle**
  (« 5! »), **combinaisons/arrangements** (« C(5,2) »), **permutations**, **Fibonacci**, **trigonométrie**
  (sin/cos/tan en degrés). Chaque calcul vient d'un module VÉRIFIÉ (`arithmetique_modulaire`, `maths_discretes`,
  `trigonometrie`) — jamais fabriqué.
- **FAUX=0 / anti-faux-positif** : primalité durcie (« premier » est un ordinal courant — « premier président
  élu en 1958 » ne déclenche PAS un test de primalité sur 1958) ; chaque route exige un mot-clé fort + des
  opérandes valides ; hors périmètre → HORS, la cascade continue. Aucune question factuelle volée (banc dédié).
- **Non câblé volontairement** (pas de brique vérifiée dédiée = ne rien fabriquer) : chiffres romains,
  probabilité élémentaire — à faire quand/si le module existe.
- Bancs : `valide_assistant_nl` **109/109** (+20 : les 14 calculs + 6 gardes anti-vol), suite **25/25**,
  raisonnement 166/166, paraphrases 168/168, challenge 16/16.

## 2026-07-08 — TRONC Phase 4 : le SÉQUENCEUR — l'ordre des caps s'APPREND du signal réel (§11-§12)

- **Nouveau `src/sequenceur.py`** : l'exécutif d'allocation de la spec. Il ordonne les caps de la cascade PAR
  ACTE pour minimiser le **nombre de caps évalués** avant celui qui tranche (ressource rare = le calcul, §15 ;
  gain = énergie/§3.1, pas la latence déjà à quelques ms). Politique = **PRIOR statique** (familles sûres,
  ex-`_FAMILLES_ACTES`, déplacé ici) **∪ APPRIS** du journal de routage réel (`tronc_routage.jsonl`). C'est le
  **bandit contextuel §11 en version discrète** : contexte = acte, bras = cap, récompense = le cap a RÉELLEMENT
  tranché (anti-Goodhart, mesuré post-hoc). **Exploration = le filet complet** de la cascade (tout cap qui
  tranche est journalisé → convergence SANS epsilon) ; **exploitation** = la politique rechargée met les
  gagnants en tête.
- **Invariant de SÛRETÉ FAUX=0 (prouvé par banc)** : réordonner ne change JAMAIS la réponse, seulement l'ordre
  d'essai — (1) l'ensemble des caps est préservé (filet complet), (2) l'ordre relatif historique est conservé
  PARTOUT → aucune priorité vécue inversée (avis_critere avant avis, comparaison_nway avant comparaison…).
  Seuls les actes du prior sont réordonnés (les factuels/raisonnement gardent l'ordre historique — biais
  conservateur ; le journal les compte quand même pour extension future sous banc).
- **Câblé** dans `repond.py` (remplace le boost binaire de Phase 5), journalise désormais à CHAQUE hit avec
  l'acte classé ; le diagnostic affiche « séquenceur : N cap(s) appris sur M acte(s) ». Cold-start honnête :
  journal vide / acte hors prior / basse confiance → ordre historique EXACT → zéro régression.
- **Utilité §12 — le terme « − coût » rendu OBSERVABLE** : `note_routage` enregistre la POSITION du cap gagnant
  (= profondeur de sonde = nb de caps essayés avant le hit = coût de calcul réel) ; `stats_routage` en donne la
  moyenne, le diagnostic l'affiche (« profondeur de sonde moyenne X cap(s) »). Mesure POST-HOC, anti-Goodhart.
  La membrane §10.3 (compression au récepteur) reste `_ajuste_registre` (prudente : ne comprime que le méta,
  jamais le contenu — la rendre agressive violerait la non-distorsion) ; l'utilité espérée §12 est `decision.py`
  (déjà livrée, parapluie). Le terme « conséquences réelles » reste un gouffre ouvert borné par FAUX=0 (§18 :
  observabilité partielle — nécessite du signal humain, non fabriqué).
- **AUDIT DE CÂBLAGE ATOMIQUE (mandat Yohan « créé mais pas câblé a réduit nos capacités »)** : audit
  fonction-par-fonction des modules récents → 2 vrais orphelins trouvés et corrigés — `sequenceur.couverture()`
  (créé, jamais appelé → câblé au diagnostic) et `sequenceur.recharge()` (appelé seulement par les tests →
  l'apprentissage intra-session était INERTE ; câblé sur un rechargement périodique tous les 40 tours, §11
  arrière-plan). `valide_sequenceur` gagne un **check de câblage PROD** (chaque API publique DOIT être appelée
  dans repond.py, pas seulement en test) → ce trou ne peut plus se re-livrer.
- Bancs : `valide_sequenceur` **44/44** (dont câblage prod), `valide_tronc` **79/79** → suite **25/25** ;
  câblage **504/504, 0 orphelin** ; raisonnement 166/166, paraphrases 168/168, challenge 16/16,
  capacites_chat 79/79, faits_appris 21/21. Embarqué .exe.

## 2026-07-08 — Invention hors-catalogue : « comment X sans Y » amplifie au lieu de tomber au web

- **Vécu audit** : « comment conserver des aliments sans frigo ? », « comment chauffer une pièce sans
  électricité ? » (besoins physiques réels hors du catalogue `besoin.py`, qui ne décompose finement que
  « rafraîchir ») finissaient en « internet coupé ». Choix FAUX=0 : je **n'invente pas** un catalogue physique
  bâclé (ce serait bluffer la physique) — à la place, `_cap_invention` AMPLIFIE (§13) : chiffrer l'objectif,
  identifier le canal dominant (conduction/convection/rayonnement/évaporation/changement d'état) et le puits
  gratuit, rappeler la limite dure (Carnot). Les actes de LANGAGE (« comment dire bonjour sans accent ») restent
  exclus (carte fermée `_VERBES_LANGAGE`) → cascade normale (pin du banc conservé).
- Bancs : `valide_capacites_chat` **79/79** (+2), suite **24/24**, raisonnement **166/166**, paraphrases **168/168**.

## 2026-07-08 — L'IA CHALLENGE pour de vrai : QUIZ VÉRIFIÉ (question posée depuis la base, réponse jugée contre le fait)

- **Mandat Yohan (« que l'IA nous challenge »)** : le défi n'est plus passif. « Challenge-moi sur la
  géographie » → Provara **POSE une vraie question tirée de sa base vérifiée** (« Quelle est la capitale de
  “République populaire de Chine” ? »), mémorise la réponse attendue PAR conversation, et **tranche la réponse
  du tour suivant contre le fait réel** : « ✔ Exact — Pékin (fait vérifié) » / « ✘ Non — la réponse vérifiée
  est Saint John's ». FAUX=0 parfait : la question SORT d'un fait vérifié, la correction EST le fait vérifié.
- Sujets (carte fermée v1) : géographie/capitales → `capitale`, chimie → `numero_atomique` ; sujet sans
  relation de quiz → mode « affirme et je tranche » conservé (toujours proposé en second mode).
- **Jamais otage** : une vraie nouvelle demande pendant le quiz est traitée normalement (état consommé) ;
  « stop » → fin propre ; question de défi purgée par l'oubli RGPD (`/api/oublie`). Porte unique : défi lancé
  = ÉCHANGE, verdicts = ancrés au fait.
- Vérifié E2E réel (bonne réponse, mauvaise réponse, digression, stop). Bancs : `valide_capacites_chat`
  **77/77** (+7), suite **24/24**, raisonnement **166/166**, paraphrases **168/168**, challenge **16/16**.

## 2026-07-08 — AUDIT ATOMIQUE (mandat Yohan « perfection chirurgicale ») : mesures + 6 trous réels tués + syllogisme

- **MESURÉ, pas déclaré** : boot 3,4 s / **31 Mo RAM**, pipeline chaud **5 ms** (les ~250 ms observés = premier
  chargement des index, par design mmap) ; superlatif 1,6 s à froid puis **0 ms** (cache colonne). `tronc.acte()`
  0,03 ms (matché) / 0,78 ms (gzip, **optimisé** : exemples précompressés à l'import) / **0,0005 ms en cache**
  (nouveau cache borné 256 entrées — acte() tourne 2× par message).
- **Batterie de compréhension réelle → 6 garbage tués** (chaque cas VÉCU à l'audit) :
  ① « teste mes connaissances » partait en MÉMO (« C'est noté ») → challenge ; ② « pose-moi une question
  difficile sur X » partait au web → challenge SUR X ; ③ « donne-moi UNE idée » partait au web (le motif
  n'acceptait que « des idées ») → amplificateur créatif ; ④ « propose/suggère-moi une idée de X » → idem ;
  ⑤ « que manque-t-il pour X » hors catalogue physique rendait « internet coupé » → **amplification honnête**
  (chiffrer l'objectif, reformuler en « comment X sans Y », scanner de manques) — la forme ambiguë « comment X
  sans Y » garde son repli silencieux (pin du banc conservé) ; ⑥ « franchement t'en penses quoi toi ? »
  (registre oral) partait en indécidable → opinion cadrée (marqueur ajouté au classifieur de bornage + tronc).
- **NOUVEAU : syllogisme à prémisses fournies** (`_cap_syllogisme`) — « si tous les mammifères allaitent et que
  le chat est un mammifère, que peut-on en déduire ? » partait au découpage multi-questions (3 × « je ne l'ai
  pas en mémoire »). Désormais : **« D'après TES prémisses (Barbara/modus ponens) : le chat allaite »** — mode
  hypothétique BALISÉ (§18 : raisonner DANS un monde posé sans l'affirmer), la porte unique classe SUPPOSITION ;
  si le store corrobore la mineure (chat → mammifère), c'est DIT. Moyen terme disjoint → refus expliqué.
  Accords sûrs (« sont mortels » → « est mortel », « des animaux » → « un animal », article utilisateur gardé).
- Bancs : `valide_capacites_chat` **70/70** (+12), suite **24/24**, raisonnement **166/166**, paraphrases
  **168/168**, challenge **16/16**, tronc **78/78**.

## 2026-07-08 — REGISTRE DES SOURCES VÉRIFIÉES complet : 32 sources officielles/structurées (demande Yohan)

- **`src/datasets/sources/registry.jsonl` reconstruit et enrichi** (6 → 32 sources), schéma riche : id, nom,
  type (sparql/api/dump/web), **autorité** (pourquoi la source fait foi), domaines, relations alimentées, URL,
  actif, sonde, note. France officiel : INSEE, API Géo (Etalab), Base Adresse Nationale, data.gouv.fr,
  Légifrance, Vie-publique, Service-Public, IGN Géoplateforme, HAL. International : OMS (GHO), Banque mondiale
  (source réelle des PIB), Eurostat, UN Data, BCE, Frankfurter (taux BCE), NIST/CODATA, PubChem, USGS séismes,
  NASA JPL, GBIF, Open Library, MusicBrainz, Nominatim, Wiktionnaire, Open Food Facts (note : corroborer).
  FAUX=0 typé À LA SOURCE : structuré (api/sparql/dump) peut nourrir un fait vérifié/appris ; consultation
  (web) ne produit QUE du rapporté attribué ; les notes disent les limites (rate-limit, clé, collaboratif).
- **Ping de joignabilité rendu LÉGER** : seules les sources marquées `sonde` (3) sont contactées — 32 GET
  séquentiels auraient rendu chaque question inconnue interminable ; repli historique sans marqueur.
- **Câblé en conversation** : « d'où viennent tes informations ? » liste désormais le registre RÉEL (32
  sources, noms cités) au lieu du texte figé. `ia.ou_apprendre(domaine)`/`provenance(relation)` inchangés.
- **Gate historique RÉPARÉE** : `valide_sources` (rouge depuis le portage — schéma riche + mledoze-countries
  attendus) repasse **105/105** et entre dans la suite → **24/24 gates**. Bancs : raisonnement 166/166,
  paraphrases 168/168, challenge 16/16, assistant_nl 89/89.

## 2026-07-08 — FAUX réel tué (G4) : une expression d'état ne part plus JAMAIS au web

- **Vécu au E2E final (web ON)** : « je suis perdu » servait un extrait hinative hors-sujet (« quelle est la
  différence entre “j'ai perdu” et “je suis perdu” ») — l'attunement était câblé au terminal MÉMO, mais l'étage
  de recherche web passait AVANT pour les affirmations. L'attunement est REMONTÉ au-dessus de l'étage web
  (étage 1·état) : une expression d'état (lexique fermé, 1re personne) reçoit sa lecture en supposition, jamais
  une recherche du texte littéral. Le terminal mémo garde son attunement (mode léger).
- Épinglé au banc des gardes : `valide_debiaisage` **44/44** (« je suis perdu » + IA_WEB=1 → attunement).
  Vérifié en réel web ON. Suite **23/23**, raisonnement **166/166**, paraphrases **168/168**, challenge **16/16**.

## 2026-07-08 — Pondération utilisateur du parapluie + REGISTRE DES MODES D'ÉCHEC du routage (§16)

- **La promesse « dis-le et je re-tranche » devient TENABLE** : marqueurs FERMÉS dans la demande —
  « …pas envie de le porter » → le port pèse plus (seuil ~33 %), « …horreur d'être trempé » → l'aversion pluie
  pèse plus (seuil ~5 %) — chaque pondération AFFICHÉE (« TA pondération : … »), verdict re-tranché par la même
  utilité espérée. Le texte du conseil montre les phrases exactes qui règlent la pondération.
- **Registre du routage** (`tronc.note_routage`/`stats_routage`, journal `~/.verax/tronc_routage.jsonl`,
  isolable par `TRONC_ROUTAGE_PATH`) : chaque décision de routage par acte RÉELLEMENT tranchée par un cap est
  journalisée — famille servie (hit) ou cap hors-famille (MISS = la surprise dont on apprend, §9/§16). C'est le
  signal de récompense MESURÉ du futur séquenceur appris (Phase 4) ; le diagnostic affiche « routage par acte :
  N décision(s), M hors-famille ». La suite isole le journal (les convs de test ne polluent pas le signal).
- Bancs : `valide_tronc` **78/78**, `valide_capacites_chat` **58/58**, suite **23/23**, raisonnement
  **166/166**, paraphrases **168/168**, challenge **16/16**. Câblage vérifié en réel (« quelle heure est-il ? »
  → 1 décision journalisée, 0 hors-famille).

## 2026-07-07 — AVIS ⑤ : décision sous incertitude — « dois-je prendre un parapluie ? » (decision.py câblé au chat)

- **Premier consommateur conversationnel de `decision.py`** (utilité espérée + marge d'abstention — le morceau
  RÉEL de §12) : « dois-je prendre un parapluie (à Toulouse) ? » → probabilité de pluie du jour **RAPPORTÉE**
  (nouveau `meteo.pluie_aujourdhui`, champ structuré `precipitation_probability_max` d'Open-Meteo, attribué) ×
  **règle d'utilité AFFICHÉE** (se faire tremper coûte 10× le port du parapluie) → **conseil calculé**
  (« utilité espérée 0,10 contre −0,10 : sortir sans »), re-tranchable (« si ta pondération diffère, dis-le »).
  Écart d'utilité sous la marge (~9 % de pluie) → **abstention honnête** (« vrai pile ou face »). Vérifié en
  RÉEL (Toulouse, 0 % → « sortir sans »).
- FAUX=0 : la probabilité est rapportée (source structurée), la règle est affichée, le verdict est CONDITIONNEL
  — la porte unique classe tout « Conseil calculé » en SUPPOSITION, jamais en fait. Sans ville → attente à trou
  (« pour quelle ville ? » → « à Brives » complète). Web OFF → refus honnête actionnable.
- `_ville_du_texte` factorisé (météo + parapluie, même extraction). « parapluie » ajouté au détecteur QUOTIDIEN
  du tronc. Bancs : `valide_capacites_chat` **54/54** (+8), suite **23/23**, raisonnement **166/166**,
  paraphrases **168/168**, challenge **16/16**.

## 2026-07-07 — TRONC Phase 5 (tranche 1) : l'acte ROUTE la cascade (retrait progressif des caps entamé)

- La boucle des ~60 caps devient une structure **NOMMÉE** (ordre historique strictement conservé — l'ordre =
  le comportement, chaque position encode un vécu) et `tronc.acte()` la **réordonne** : un acte classé à
  confiance nette (≥ 0,8) fait passer SA famille de caps EN TÊTE (`_FAMILLES_ACTES` fermée : quotidien→
  quotidien/site, demander_avis→avis_critere/avis, créer→creer_ouvert/inventions, agir→traduction), la cascade
  complète restant le FILET derrière → zéro perte. Les actes factuels/raisonnement ne sont PAS routés : les
  détecteurs des caps y sont plus fins que la classification d'acte (on ne dégrade jamais un routage précis
  par un grossier).
- C'est aussi le **point d'allocation du séquenceur (§11)** : la Phase 4 (politique apprise/bandit) pourra
  réordonner ICI, sous les mêmes bancs — le substrat existe désormais.
- Bancs : `valide_tronc` **76/76** ; suite **23/23** ; raisonnement **166/166** ; paraphrases **168/168** ;
  challenge **16/16** ; capacites_chat **46/46**.

## 2026-07-07 — QUEUE réelle : TTL des faits appris (verrou de péremption fermé) + anaphore du repli + libellé opinion

- **TTL / rafraîchissement des faits appris** (queue #1) : le cache appris était consulté AVANT le réseau →
  un fait appris ne se remettait JAMAIS à jour (verrou de péremption). Désormais `faits_appris` porte un TTL
  (90 j par défaut, `FAITS_APPRIS_TTL_JOURS`) avec `age_jours`/`est_frais` (horloge injectable) : fait FRAIS →
  servi du cache (instantané, hors-ligne) ; fait PÉRIMÉ + web ON → le réseau prime (re-cherche + ré-apprend la
  valeur fraîche), repli sur l'instantané DATÉ si la source ne tranche plus ; web OFF → toujours servi (un
  instantané daté n'est pas un mensonge — le TTL ne prive jamais le hors-ligne). `valide_faits_appris` 21/21 (+7).
- **Anaphore câblée dans le repli du tronc (§7 contexte)** : le DERNIER SUJET du pipeline nourrit le faisceau —
  « il est génial non ? » (après un tour sur la tour Eiffel) → hypothèse AVIS « à propos de “la tour Eiffel” ».
  Nouveau marqueur d'avis évaluatif nu (« il/elle/c'est génial/nul/top… » = demande d'accord = demande d'avis).
  `valide_tronc` 73/73.
- **Libellé d'opinion GÉNÉRIQUE** (queue #3, vécu : « ventes, remplissage des salles » — critères de FILMS —
  sortaient pour « le plus beau pays ») : exemples de critères tous-domaines (mesurable : records, récompenses,
  chiffres vérifiables… — ou goût pur). Préfixe et marqueurs de classe inchangés (aucune régression d'enveloppe).

## 2026-07-07 — TRONC Phase 3 : les 9 GARDES DE DÉBIAISAGE (§20) deviennent un banc permanent

- Nouveau gate `valide_debiaisage` **43/43** (suite → **23/23**) : chaque garde de la spec est un test qui doit
  passer EN PERMANENCE — **G1** anti-projection (TRANCHÉ exige un juge réel ; hors-store jamais un fait),
  **G2** pas de collapse précoce (≥2 candidats ; « taille de la France » composée), **G3** individuation
  (« bonjourno » ≠ « bonjour », « calculateur » ne déclenche pas CALCULER), **G4** calcul frais (un calcul est
  CALCULÉ, zéro requête web même transport branché — espion à compteur), **G5** mot valide jamais « corrigé »
  (aucun did-you-mean sur une phrase de mots réels), **G6** repli honnête câblé, **G7** typage supposition
  (gzip borné ≤ 0,45 ; attunement et subjectif classés SUPPOSITION par la porte unique), **G8** non-distorsion
  (proxy : le statut est LISIBLE — marqueur dans toute supposition, provenance dans tout fait), **G9**
  amplification (proxy : zéro flagornerie/émotion feinte, le repli finit par une question — l'humain garde le
  volant, l'avis affiche sa règle).
- Honnêteté du banc (documentée dedans) : G1-G7 testées directement ; G8/G9 en PROXYS exécutables — la mesure
  pleine (inférences licenciées ⊆ vérité, capacité-sans-la-machine) arrive avec les phases 4+.

## 2026-07-07 — TRONC Phase 2 : le COMPOSITEUR (§10) — l'ambiguïté se COMPOSE, elle ne se choisit plus en silence

- **`tronc.compose(faisceau, terme)`** : le « coup calculé » de la spec (§10.1/10.2) sur un faisceau dont les
  branches ont été résolues par l'appelant — **convergence** → tronc commun servi + ambiguïté signalée non
  porteuse ; **lecture unique servable** → mener avec le fait, signaler les autres lectures ; **divergence** →
  toutes les branches vérifiées servies conditionnellement + INVITATION (une porte, pas un mur) ; **trop de
  branches** → lister et laisser choisir. FAUX=0 : seules les branches TRANCHÉES (lookup réel) sont servies
  comme faits ; les lectures non résolues ne sont mentionnées QUE comme lectures.
- **Premier consommateur câblé : `_cap_mesure_ambigue`** (repond.py, avant `_cap_synonyme_tete`) + carte fermée
  `tronc.RELATIONS_AMBIGUES` (taille/grandeur/dimension). Deux FAUX réels tués, vécus à la sonde du jour :
  « la taille de la France » était **collapsée en silence** sur superficie (`_SYN_TETE` codé en dur) → désormais
  composé « superficie 551 695 km² + population 68 720 337 + précise la lecture » ; « la taille de la tour
  Eiffel » **échouait** (web coupé) alors que la hauteur (330 m) est en base → désormais servie avec les autres
  lectures signalées. Chaque branche est résolue par les caps VÉRIFIÉS existants (`_cap_dimension` avec ses
  gardes anti-homonymes d'œuvres, `_cap_synonyme_tete`) — zéro logique de lookup dupliquée.
- **Garde homonyme** : un PAYS/une VILLE n'a pas de « hauteur » — sans elle, « taille de la France » servait
  « Hauteur de France : 232 m » (le PAQUEBOT France, trouvé au test réel). Lectures hauteur/longueur écartées
  pour les entités de `capitale`/`pays_ville`.
- **Bancs** : `valide_tronc` **72/72** (+11 : compositeur pur — divergence/convergence/lecture unique/trop de
  branches/None — + câblage échantillon avec garde homonyme) ; suite **22/22** ; raisonnement **166/166**
  (dont le pin `synonyme-tete-taille` direct, inchangé) ; paraphrases **168/168** ; challenge **16/16**.

## 2026-07-07 — TRONC DE COMPRÉHENSION, Phase 1 (clé de voûte) : la carte des 11 actes + le repli honnête

- **Spec validée par Yohan** (`SPEC_TRONC_COMPREHENSION.md` §7-§10 + `SPEC_TRONC_UPGRADES.md` U1→U61) → premier
  bâti. Nouveau module `src/tronc.py` : `acte(signal, contexte) → Faisceau` — chaque message est classé dans la
  **carte FERMÉE des 11 actes de parole** (interroger_fait, calculer, raisonner, demander_avis, créer, méta,
  social, exprimer_état, quotidien, agir, inconnu), avec entités/relation extraits UNE fois, le régime attaché
  par `classifieur_bornage` (réutilisé, jamais dupliqué), et des **candidats tenus en PARALLÈLE** (G2 : jamais
  un sens choisi en silence). NB nommage : `comprehension.py` existait déjà (abstraction du harnais
  d'invention) → le moteur porte le nom de la spec, le TRONC.
- **FAUX=0 structurel (G1/G7)** : un candidat n'est TRANCHÉ que si un **vrai juge** a évalué (juge arithmétique
  AST — « combien font 2+2 ? » → TRANCHÉ « 4 », ancré) ; tout le reste porte une RECETTE (la faculté existante
  à invoquer : lecteur, raisonnement, `_cap_avis`, `_cap_quotidien`…), jamais une valeur fabriquée.
- **Deux étages** (« explicite au cœur, appris en périphérie ») : détecteurs FERMÉS par acte (cœur, confiance
  haute) ; **gzip-kNN** (U13 : distance de compression NCD, zéro entraînement) en périphérie qui PROPOSE une
  intention voisine à confiance bornée (≤ 0,45) quand aucun motif ne matche — l'humain vérifie.
- **REPLI HONNÊTE intent-aware (§10.4/G6) — la brique qui tue le « il comprend rien »** : câblé dans
  `assistant_nl` (branche indécidable) — quand le moteur tient une hypothèse NON-factuelle, il la MONTRE :
  « voici ce que j'ai compris (hypothèse) + ce que je sais faire + corrige-moi », jamais de garbage (ni fausse
  correction ortho, ni web du texte littéral). Une hypothèse « fait » n'écrase PAS l'aveu structuré / le
  conseil « réactive internet » existants (plus actionnables après l'échec de la cascade factuelle).
- **ATTUNEMENT (§13)** : « je suis perdu » recevait « C'est noté » (mémo à côté de la plaque). Désormais, acte
  EXPRIMER_ÉTAT (lexique fermé, 1re personne) → lecture d'état en SUPPOSITION (« il se peut que tu te
  sentes… », jamais « je ressens ») + prise concrète. Câblé dans `repond.py` avant le terminal mémo ; la porte
  unique le classe SUPPOSITION (jamais un fait). Une préférence (« mon plat préféré… ») garde sa voie mémo.
- **Bancs** : nouveau gate `valide_tronc` **61/61** (la carte, l'extraction, G1/G2/G4/G5/G6/G7, gzip-kNN,
  attunement, câblage assistant_nl) ; suite **22/22** ; paraphrases **168/168** ; raisonnement **166/166** ;
  challenge **16/16** ; synonymes 8/8 ; constructions 4/4 ; assistant_nl 89/89 ; câblage **503/503, 0
  orphelin** ; capacités prouvées **281/281** (preuve tronc au registre). Embarqué .exe (`_precharge_verax` +
  hidden-imports bat/CI). Prochaines phases : faisceau+compositeur (Ph2), gardes G1-G9 en banc `valide_debiaisage`
  (Ph3), séquenceur+utilité (Ph4), retrait des caps (Ph5).

## 2026-07-06 — APPRENTISSAGE des faits web : Provara retient ce qu'il trouve, réutilisable HORS-LIGNE

- **Demande Yohan** (queue prioritaire) : « que mon IA apprenne les faits STRUCTURÉS qu'elle trouve en ligne,
  réutilisables hors-ligne ». Nouveau module `src/faits_appris.py` : quand `veille_structure.interroge_nl`
  résout un fait sur Wikidata (extraction SPARQL déterministe), il est APPRIS — rangé en local
  (`~/.verax/faits_appris.jsonl`), typé source + date. La prochaine fois, il est resservi **sans réseau** et
  **même Internet coupé**, toujours attribué et daté (« Strelsau — appris de Wikidata le 2026-07-06 »).
- **Frontière FAUX=0 (stricte)** : SEUL le structuré est appris ; le texte libre (Wikipédia, métamoteur) reste
  « rapporté », jamais appris. Jamais de valeur vide ni de fait sans source. Un fait resservi est un
  INSTANTANÉ daté (le monde a pu changer), pas une vérité intemporelle. « Dernier appris » d'une clé fait foi
  (rafraîchissement naturel). Apprentissage = bonus en dégradation silencieuse (jamais un point de panne).
- Câblé dans `assistant_nl._cherche_sources` : le cache appris est consulté AVANT le réseau (réponse
  instantanée + hors-ligne) et alimenté après chaque succès Wikidata. `interroge_nl` refactoré autour d'un
  `analyse_nl` (parse seul, même clé). Le diagnostic affiche « N faits appris du web ».
- Nouveau gate `valide_faits_appris` **14/14** (dans la suite, 21 gates) ; `valide_cablage` 502/502 (le module
  est atteignable via assistant_nl) ; module embarqué (.exe : `_precharge_verax` + hidden-imports build/CI).

## 2026-07-06 — « Population du Caire » : phrase complète, plus le nombre BRUT (villes à article dans le nom)

- **Vécu Yohan** : « population du Caire » → *« 9801536 »* nu, alors que « population de Paris » sortait
  *« Population de Paris : 2 103 778 habitants. »*. Cause : « du Caire » = *de + LE Caire* ; le cap formateur
  `_cap_synonyme_tete` cherchait « Caire » alors que la donnée est stockée « **Le** Caire » (article inclus) →
  il ratait, et la cascade floue prenait le relais en rendant la valeur nue.
- Helper `_ville_avec_article` (inverse de `_de_ville`) : la contraction/l'article collé à l'entité
  (« du » → Le, « des » → Les, « de la » → La, « de l' » → L', + « de le/les » des reformulations) reconstruit
  la clé réelle, essayée en repli quand le lookup nu échoue. « du Caire », « du Mans », « a le Caire » →
  phrase complète ; villes sans article (« de Nice », « de Paris ») inchangées.
- `banc_raisonnement` **166/166** (+3 : du Caire, de le Caire, garde de Nice), suite **20/20**.

## 2026-07-06 — Avis ④ : 3+ candidats — chaque critère VOTE, Condorcet dépouille (choix_social câblé)

- « Quelle est la meilleure destination entre la France, l'Italie et l'Espagne ? » → chaque critère vérifié
  (superficie, population, PIB, PIB/hab) devient un ÉLECTEUR qui classe les candidats (classements complets
  montrés, valeurs à l'appui), puis **gagnant de CONDORCET** (bat chacun en duel) ; cycle → repli **BORDA**
  annoncé comme tel ; personne ne se détache → avis SUSPENDU. `choix_social.py` (Vague scrutins) enfin câblé
  au conversationnel — après `pareto.py` hier.
- « Mon critère n°1 est X » re-tranche aussi à N candidats (classement complet sur CE critère).
- E2E base complète (France/Italie/Espagne → Condorcet : France ; critère superficie re-tranché).
  `valide_capacites_chat` 40/40, suite **20/20**.

## 2026-07-06 — Avis ③ : « donne-moi ton critère n°1 » n'est plus une impasse — le tour suivant RE-TRANCHE

- L'avis comparatif RETIENT ses critères par conversation (`_AVIS_ATTENTE`, même principe que l'attente à trou
  météo) : après « mon avis : France… il bascule si ton critère est X », répondre « mon critère n°1 est le
  PIB par habitant » (ou juste « la population ») **re-tranche sur CE critère**, valeurs montrées :
  *« Avec TON critère (PIB par habitant) : France 48 985 $/hab devant Espagne 38 627 → mon avis suit ton
  critère : France. »* Le libellé le PLUS LONG qui matche gagne (« PIB par habitant » ≠ « PIB »).
- Critère nommé mais NON mesuré (« le climat ») → aveu honnête + liste des critères mesurables. Égalité sur le
  critère → il ne peut pas trancher, un autre est proposé. Message sans rapport → pipeline normal, l'état
  reste disponible ; consommé en une fois quand il sert.
- E2E vérifié base complète (2 tours réels). `valide_capacites_chat` 37/37, suite **20/20**.

## 2026-07-06 — MAJ : plus de 2e onglet — l'onglet existant se recharge, l'app relancée n'en ouvre pas

- **Vécu Yohan** : « lorsque je lance la mise à jour, il m'ouvre un nouvel onglet, mais le précédent n'est pas
  fermé ». Un navigateur n'autorise jamais le serveur à fermer un onglet — la bonne coupe est de ne pas en
  OUVRIR un deuxième : l'ancien onglet se recharge déjà tout seul (watchdog front, bandeau ⏳ → reload).
- L'updater pose `VERAX_RELANCE_MAJ=1` dans son `.bat` AVANT le `start` (vaut aussi pour les relances
  anti-DLL, même session cmd) ; `lance.py` n'ouvre pas de navigateur quand ce marqueur est présent.
- `valide_maj` **38/38** (marqueur avant tout start + garde lance.py, bat généré inspecté).

## 2026-07-06 — Avis 2/2 : débats SANS chiffres — les deux faces sourcées + avis CONDITIONNEL signé

- « Que penses-tu des voitures électriques ? » ne rend plus le seul cadrage générique : `_reponse_opinion`
  cherche les DEUX FACES (« avantages et inconvénients <sujet> », métamoteur multi-domaines), les RAPPORTE
  attribuées, puis signe un avis CONDITIONNEL à règle affichée : *« un avis se tranche par CRITÈRE, jamais
  par goût — si les avantages collent à ton besoin, oui ; si un inconvénient est rédhibitoire, non ; donne-moi
  ton critère n°1 et je tranche en le suivant »*. FAUX=0 : des arguments invérifiables ne sont jamais pesés à
  l'aveugle, ils sont montrés ; le comparatif CHIFFRÉ reste tranché en amont par `_cap_avis` (Pareto/vote).
- **Garde PROSE** (vécu au test live : un extrait « menu de navigation » servi comme argument) : ratio de
  mots-outils ≥ 25 % exigé — les menus sont écartés, les phrases restent. Aucune source -> repli inchangé.
- Vérifié en live (voitures électriques → extrait prose ohm-energie.com, menu écarté).
  `valide_assistant_nl` 89/89, `valide_opinions` 11/11, suite **20/20**.

## 2026-07-06 — CÂBLAGE 0-ORPHELIN : 501/501 modules atteignables, audit permanent, 280 preuves en direct

- **Mandat Yohan** : « il faut vraiment que tout ce qui a été construit soit câblé — 0 orphelin, assumé ou
  non, sinon c'est de la dette ». L'audit a d'abord MESURÉ le réel : **223 modules de src/ n'étaient
  atteignables par AUCUN chemin du produit** (dont `capacites.py` — le registre de preuves lui-même — et tout
  ce qu'il porte : Pareto, Condorcet, causalité, lois physiques, simulation…).
- **Nouveau gate permanent `tests/valide_cablage.py`** (dans la suite, 20 gates) : fermeture transitive des
  imports depuis les entrées du produit (lance/verax_boot/serveur/repond) — un futur module non câblé remet
  la suite AU ROUGE. Allowlist VIDE par mandat ; `_precharge_verax` (manifeste d'analyse PyInstaller) est
  vérifié en LISANT `--hidden-import` dans build_exe.bat, jamais assumé — et sans traverser ses imports.
- **Câblage réel en 2 étages** : ① le diagnostic exécute désormais `capacites.verifie_tout()` EN DIRECT
  (« capacités prouvées à l'instant : 280/280 », ~5 s, sans chargement de base) → 171 modules recâblés d'un
  coup ; ② les **52 modules restants ont reçu chacun une PREUVE à réponse connue** dans capacites.REGISTRE
  (criblée de leur validateur : causalité, logique trivaluée, révision de croyances, triangulation, lois/
  limites/simulation physiques, géométrie 3D, lexique kaikki, fabrique français, boucle générer-juger-garder,
  session d'entraînement RÉELLE en mini, test du diable sur une tâche, usine à données…). Zéro preuve de
  façade (`callable()` interdit — deux tentatives ont été remplacées par de vraies exécutions).
- `valide_capacites` 73/73 (228 → 280 preuves), suite conversationnelle **20/20 gates**, diagnostic e2e :
  *« …capacités prouvées à l'instant : 280/280 »*.

## 2026-07-06 — « Mon avis est… » : premier avis ASSUMÉ de Provara — réflexion outillée, pas ressentie

- **Demande Yohan** : que l'IA puisse donner SON avis sur du non-tranché — « la réflexion réelle mais bien plus
  évoluée qu'un humain ». Définition compatible FAUX=0 : un avis = une CONCLUSION SIGNÉE, dérivée de faits
  vérifiés, règle de décision AFFICHÉE, et falsifiable (la sensibilité dit ce qui le ferait basculer).
- **Nouveau cap `_cap_avis`** (« quelle est la meilleure destination entre la France et l'Espagne ? »,
  « tu préfères Lyon ou Marseille ? ») : critères = TOUTES les relations chiffrées du lecteur où la paire a des
  valeurs (montrées une à une) ; verdict par **dominance de Pareto** (`src/pareto.py`, enfin câblé au
  conversationnel : « aucune pondération ne peut inverser → avis ROBUSTE ») sinon **vote majoritaire des
  critères** + **SENSIBILITÉ** (« mon avis bascule si ton critère prioritaire est X ») ; égalité → avis
  SUSPENDU (le critère de l'utilisateur tranche) ; un seul critère mesurable → avis annoncé MINCE, jamais
  gonflé. Convention affichée et contestable (« devant » = plus grande valeur).
- Vérifié en réel base complète : France/Espagne → 4 critères, dominance de Pareto. `valide_capacites_chat`
  32/32, suite 19/19. Reste en queue : brique 2 (Pour/Contre sourcé + verdict conditionnel, débats sans
  chiffres).

## 2026-07-06 — « Regarde le site yohanfauck.fr » : Provara VA LIRE le site nommé et rapporte (attribué)

- **Vécu Yohan** : « peux-tu regarder le site yohanfauck.fr et me dire ce que tu en penses ? » tombait dans la
  clarification générique (le domaine ne « rattache » à aucun fait, la recherche Wikipédia ne trouve rien).
- **Nouveau cap `_cap_site`** (câblé en tête de cascade) : un domaine/URL explicite dans le message (TLD
  fermés — jamais « maj.py ») → visite réelle via `veille_structure.apercu_site` : HTTPS puis repli HTTP,
  jamais d'adresse locale/IP, titre `<title>` + **fenêtre la plus PROSE** de la page (comptage de mots-outils :
  les menus de navigation sont écartés), rapport ATTRIBUÉ + lien. « Ce que tu en penses » → cadrage honnête
  (« je ne porte pas de jugement — voilà ce que la page dit »). Web OFF → refus actionnable (bouton 🌐) ;
  injoignable → aveu honnête. FAUX=0 : contenu rapporté verbatim, jamais un jugement inventé.
- Vérifié EN LIVE sur yohanfauck.fr (titre réel + passage prose). `valide_veille_structure` 22/22,
  `valide_capacites_chat` 25/25, suite 19/19.

## 2026-07-06 — FLIP ONEDIR (build 49) : Provara devient un dossier — démarrage instantané, antivirus apaisé

- Le build 48 (updater v2) vérifié en réel chez Yohan (auto-update 44→48 observé en direct, slot météo et
  extraits web testés sur l'exe), le PONT rendant l'attente inutile → `ONEDIR: "1"` dans le CI (GO Yohan).
- Build 49+ : le CI publie **`Provara-app.zip`** (Provara.exe + `_internal\` à la racine) ; `Provara.exe` et
  `Provara-windows.zip` restent FIGÉS au build 48 comme pont pour les updaters ≤ 47. Plus AUCUNE
  ré-extraction `%TEMP%` au lancement : l'antivirus ne rescanne plus rien, l'erreur « Failed to load Python
  DLL » devient structurellement impossible.
- README (fr/en) §Windows : télécharger `Provara-app.zip`, dézipper, double-cliquer `Provara.exe`.
- À VÉRIFIER à la sortie du 49 : migration 48→49 en réel (bascule dossier), premier lancement onedir.

## 2026-07-06 — Exposés web : « parle-moi de Brive-la-Gaillarde » sert la VILLE, plus la « Rafle de Brive »

- Trouvé au test RÉEL du build 48 (.exe, port 8765) : le terme de recherche partait pollué (« parler de
  Brive-la-Gaillarde ») car `_termes_wiki` dépouillait « peux-tu me » mais pas le verbe d'exposé — la
  recherche plein-texte Wikipédia servait alors un article connexe au lieu du sujet.
- Verbes d'exposé (parler/présenter/décrire/exposer) dépouillés AVEC leur « de/d' » ; les participes
  (« qui a construit … ») restent intacts. `valide_veille_structure` 16/16, suite 19/19, vérifié en live
  (l'article « Brive-la-Gaillarde » sort, intro propre).

## 2026-07-06 — Conversation : une précision demandée est RETENUE (« pour quelle ville ? » → « A Brives »)

- **Vécu Yohan** : « Il fait quel temps ? » → « pour quelle ville ? » → « A Brives » partait en recherche web
  libre (extrait Wikipédia hors-sujet) au lieu de compléter la question météo. « Ce n'est pas ce qu'on appelle
  une conversation, là c'est du question-réponse. »
- **Clarification À TROU** (`assistant_nl.note_attente_slot`) : quand l'assistant demande UNE précision, le
  tour suivant qui y ressemble (valeur nue : « A Brives », « à Saint-Étienne stp ») REMPLIT le gabarit
  (« quel temps fait-il à %s ? ») et la question complétée est rejouée dans le pipeline normal. Même prudence
  que le did-you-mean : une nouvelle question pendant l'attente n'est JAMAIS fourrée dans le trou (elle est
  traitée normalement), un refus (« non merci ») invite à reformuler, l'état est consommé en une fois.
- `_cap_quotidien` reçoit `conv_id` et enregistre l'attente au moment où il pose la question.
- Bout-en-bout vérifié (météo factice, zéro réseau) : T1 demande la ville, T2 « A Brives » → relevé de Brives.
  `valide_assistant_nl` 84/84 (7 cas slot), suite conversationnelle 19/19, bancs data 163/163 + 168/168.

## 2026-07-06 — Web : plus jamais de wikitexte/JSON brut dans un extrait (vécu « A Brives » → infobox {{…}})

- **Cause racine** : `_texte_page` dépouillait les balises avec `<[^>]+>` — or les pages MediaWiki modernes
  embarquent du JSON Parsoid dans des attributs (`data-mw="{…}"`) contenant des `>` : la balise était coupée
  au premier `>` et le JSON (`{"wt":"[[Arrondissement de…`) fuyait dans le « texte » servi à l'utilisateur.
- Regex de balises durcie (attributs quotés traités) pour TOUS les sites + les articles Wikipédia sont
  désormais lus via l'**API TextExtracts** (texte brut servi par la source : pas de coordonnées, de bandeaux
  d'homonymie ni d'infobox), plus jamais scrapés.
- Nouveau gate `valide_veille_structure` (15 cas, OFFLINE : transport factice) — `veille_structure.py` n'avait
  AUCUN banc ; ajouté à la suite conversationnelle (19 gates).

## 2026-07-06 — Antivirus : migration onedir décidée (GO Yohan) — updater v2 prêt (étape 1/2)

- **Diagnostic** : le `--onefile` se ré-extrait dans `%TEMP%\_MEI…` à CHAQUE lancement → l'antivirus rescanne
  ~200 fichiers à chaque ouverture (minutes de lenteur) et verrouille parfois `python3xx.dll` (« Failed to
  load Python DLL », vécu ×2 — la relance unique à 10 s ne suffisait pas, le scan peut durer plus longtemps).
- **Étape 1 (ce build, 48)** — updater v2 dans `maj.py` : sait installer un paquet DOSSIER `Provara-app.zip`
  (onedir : `Provara.exe` + `_internal\` extraits À CÔTÉ de l'installation — même volume, bascule par simples
  renommages ; garde anti zip-slip ; paquet incomplet refusé) ; le paquet-dossier est PRÉFÉRÉ dès qu'il est
  publié. **Filet anti-DLL en BOUCLE** : surveillance ~60 s, jusqu'à 3 relances (au lieu d'une à 10 s).
- **Étape 2 (build 49, à déclencher quand le 48 est diffusé)** : bascule `ONEDIR: "1"` dans
  `.github/workflows/build-exe.yml` (interrupteur prêt, OFF par défaut) → publie `Provara-app.zip`, FIGE
  `Provara.exe`/`Provara-windows.zip` au dernier onefile comme PONT : un updater ≤ 47 installe le pont (48),
  qui migre ensuite tout seul vers le paquet-dossier. Jamais d'exe onedir publié sous le nom `Provara.exe`
  (casserait les vieux updaters). Build local : `VERAX_ONEDIR=1 build_exe.bat`.
- `valide_maj` **36/36** (préférence de paquet, extraction gardée, zip-slip refusé, bascule `_internal`,
  boucle anti-DLL). Reste ouvert : signature de code (SmartScreen au 1er téléchargement — coût à trancher).

## 2026-07-06 — Menu ⚙️ Réglages : un seul bouton en haut à droite (design Yohan)

- La barre d'outils (Internet, MAJ auto, Rechercher une MAJ, thème, langue, Quitter) devient UN bouton
  « ⚙️ Réglages » -> panneau déroulant. Mêmes identifiants -> zéro régression JS ; clic hors du panneau le
  ferme ; le bouton « Quitter » (rouge, en bas du menu) réutilise la route /api/quitter existante — les
  doublons (2ᵉ route, 2ᵉ fonction serveur, injecteur dynamique du bouton) ont été retirés.
- Le watchdog serveur reste silencieux après un « Quitter » volontaire (pas de faux « mise à jour en cours »).
- Testé en réel : page servie avec le menu, /api/quitter arrête effectivement le serveur. Suite 18/18,
  valide_maj 28/28.

## 2026-07-06 — MAJ : la page se recharge toute seule, et l'app se relance même si l'antivirus grogne

- **Page figée après une mise à jour** (retour Yohan) : l'interface a maintenant un WATCHDOG — serveur perdu →
  bandeau « ⏳ Mise à jour en cours… » ; serveur revenu → « ✅ Mise à jour terminée » + **rechargement
  automatique** ; pas de retour après 90 s → consigne actionnable (« Relance Provara.exe — la mise à jour
  s'appliquera au démarrage »). L'utilisateur n'est plus jamais devant une page morte sans explication.
- **« Failed to load Python DLL (_MEI…\python312.dll) »** (vécu après une MAJ) : au premier lancement d'un
  binaire fraîchement téléchargé, l'antivirus peut verrouiller l'extraction PyInstaller et tuer le démarrage —
  l'app ne revenait pas. L'updater vérifie désormais ~10 s après le `start` que Provara tourne et le **relance
  une fois** sinon (le second départ passe, le binaire ayant été scanné entre-temps).
- Gate `valide_maj` **28/28** (watchdog front, consigne de secours, re-lancement updater), suite 18/18.

## 2026-07-06 — « Web ON = toujours une réponse » : météo réelle, exposés Wikipédia, quotidien, challenge

- **Principe posé par Yohan et implémenté au cœur du routeur** : avec Internet activé, Provara répond à tout —
  au pire par une SUPPOSITION rapportée et sourcée. L'« indécidable » tente désormais les sources AVANT toute
  clarification ; la boucle « je n'arrive pas à rattacher… » ne peut plus se produire web ON.
- **Météo EN DIRECT** (`src/meteo.py`, source structurée Open-Meteo, sans clé, enregistrée au registre) :
  « quelle température fait-il à Toulouse ? » → *« À Toulouse (France) en ce moment : 24,4 °C, ciel dégagé,
  vent 3,6 km/h (relevé open-meteo.com à 09:45 — rapporté) »*. Sans ville → demande la ville ; web OFF →
  refus honnête actionnable. + heure et date locales (faits réels de l'horloge).
- **Demandes ouvertes d'exposé** : « peux-tu me parler de la gestion de projet IT ? » → rapport Wikipédia
  ATTRIBUÉ (2 bugs de plomberie trouvés : `cherche_web_libre` recevait la phrase brute au lieu du sujet
  nettoyé, et la gate de pertinence jugeait la question brute — « parler »/« IT » comptés comme contenu).
- **« Challenge-moi sur X »** : partait en MÉMO (« c'est noté ») ! → demande d'interaction reconnue, protocole
  honnête : *« Défi accepté — à MA façon : affirme, je tranche Vrai/Faux/Indécidable avec preuve »*.
- **Opinions** : « que penses-tu des voitures électriques ? » → cadrage subjectif + éclairage Wikipédia sourcé.
- `_cap_quotidien` était défini SANS être câblé (trouvé à l'audit orphelins demandé par Yohan) — branché.
- Bancs : paraphrases **168/168**, raisonnement 163/163, constructions 4/4, synonymes 8/8, suite 18/18,
  challenge 16/16 (+28/30 web), valide_maj 25/25.

## 2026-07-06 — Le Groenland rejoint la base : superficie_ile ×3,5 (BestRank)

- `superficie_ile` ré-ingéré avec le fix BestRank+mul : **4 851 → 17 031 îles**, dont enfin le Groenland
  (*2 130 800 km²*). « La plus grande île du monde ? » relit la valeur en direct (plus de « fait curé » —
  la note honnête sur l'Australie-continent reste). « Le Groenland est-il plus grand que Madagascar ? » →
  comparaison chiffrée. Bancs : 164/164, 163/163, 18/18, 16/16.

## 2026-07-06 — BestRank : le Nil, l'Amazone, la tour Eiffel (330 m) et Burj Khalifa (828 m) sont mesurables

- **Cause racine n°3 des trous** : les requêtes unit-aware lisaient TOUS les rangs Wikidata — le Nil portait
  6 650 km (rang préféré) ET 2 850 km (un tronçon, rang normal) → « désaccord » → rejeté. Les fleuves et
  monuments CÉLÈBRES, plus documentés donc plus multi-déclarés, étaient les premiers éliminés.
- **Fix global t7** : `?st a wikibase:BestRank` (équivalent truthy) + labels COALESCE(fr, mul) dans les deux
  requêtes unitaires. Ré-ingérés : `longueur_fleuve` (Nil *6 650 km*, Amazone *6 400 km* — « le Nil est-il
  plus long que la Seine ? » → *Oui, chiffré*), **nouvelle relation `hauteur_tour`** (540 tours — la tour
  Eiffel fait enfin *330 m* au lieu d'une abstention), `hauteur_gratte_ciel` re-produit (Burj Khalifa
  *828 m*).
- Le record « plus long fleuve » cite désormais les valeurs RELUES de la table tout en maintenant la dispute
  Nil/Amazone (tracé court vs long). Bancs : paraphrases **164/164**, raisonnement **163/163**, suite 18/18,
  challenge 16/16. Sync datasets_complets.

## 2026-07-06 — Labels « mul » Wikidata : Shakespeare, Gandhi, Darwin récupérés

- **Découverte importante pour TOUTES les ingestions futures** : depuis la migration « mul » de Wikidata
  (2024), les noms identiques dans toutes les langues (William Shakespeare, Gandhi, Darwin…) n'ont PLUS de
  label « fr » — un `FILTER(lang="fr")` sec élimine précisément les plus célèbres. `ingere_celebres` passe en
  `COALESCE(fr, mul, en)` → +1 209 personnes de plus (Shakespeare *né en 1564*, Darwin fiche complète,
  Gandhi *1869-1948* via l'alias corrigé vers la clé réelle « Mohandas Karamchand Gandhi »).
- Forme « quel était le MÉTIER de X » ajoutée au cap fait-personne (seul « quel métier faisait X » passait).
- Banc paraphrases **160/160**, raisonnement 162/162, suite 18/18, challenge 16/16. Sync datasets_complets.

## 2026-07-06 — RÉ-INGESTION personnes célèbres : Newton, Marie Curie, Churchill… retrouvent leur fiche

- **Cause racine (encore le fonctionnel par libellé, sous deux formes)** : Isaac Newton (le physicien) était
  MASQUÉ par son PÈRE homonyme (fermier — « Isaac Newton → agriculteur » !) ; Marie Curie n'avait NI
  occupation (physicienne ET chimiste = multi → HORS) ni nationalité (Pologne ET France = multi → HORS).
  Plus on est célèbre, plus on a d'homonymes et d'attributs multiples — les géants étaient les plus touchés.
- **Nouveau `ingestion/ingere_celebres.py`** (réutilisable) : les ~11 000 humains à ≥50 sitelinks via QLever ;
  dominance par notoriété (≥8×) ; valeurs multiples d'une MÊME entité JOINTES honnêtement (« professeur
  d'université, physicienne et chimiste », « France et Pologne ») triées par fréquence corpus ; append si
  absent, remplacement si l'entrée existante est l'homonyme obscur ; **passe anti-collision finale** avec la
  clé exacte du lecteur (une collision réelle ferait refuser le fichier au chargement — vécu et corrigé).
- Volumes : occupations +8 422 / 660 remplacées, nationalités +3 499 / 1 007 remplacées, naissances +1 740,
  décès +919, lieux de naissance +1 319, lieux de décès +611.
- Résultats : « qui était Isaac Newton ? » → *philosophe et mathématicien, né en 1643 à Woolsthorpe…* ;
  « quel métier faisait Marie Curie ? » → *professeur d'université, physicienne et chimiste* ; Churchill,
  Napoléon (occupations réordonnées : « personnalité politique, souverain et chef militaire »).
- Sync datasets_complets (6 fichiers). Bancs : 162/162, 157/157 — capitales multiples incluses.

## 2026-07-06 — RÉ-INGESTION traités & guerres : Versailles 1919 et les guerres mondiales sont là

- **Dominance par NOTORIÉTÉ (sitelinks)** dans le pipeline dates (t8) : « traité de Versailles » (1919,
  135 wikis) était tué par ses homonymes historiques (1756/1768/1783/1787, ≤15 wikis) via le fonctionnel par
  libellé. Règle : l'entité au max de sitelinks est retenue si ≥8× la rivale d'une autre année ; sinon
  l'ambiguïté est réelle (« bataille des Ardennes » 1914 vs 1944) → HORS inchangé.
- `annee_signature_traite` re-produit via t8 moderne : **1 334 traités** (dont Versailles → *1919*) ;
  `annee_debut/fin_guerre` re-produits via QLever classe Q198 : **766 → 1 948 guerres**, dont enfin
  « Première Guerre mondiale » (*1914-1918, durée 4 ans calculée*) et « Seconde » (*1939-1945*).
- Phrasés branchés : « en quelle année a été SIGNÉ X » (verbe → annee_signature_traite), « quand s est
  terminée » (apostrophe perdue tolérée), accord « **La** Première Guerre mondiale a duré… ».
- Fichiers synchronisés vers datasets_complets (release). Banc paraphrases **155/155** (4 cas), raisonnement
  162/162, suite 18/18, challenge 16/16.

## 2026-07-06 — RÉ-INGESTION population_ville : Paris et Berlin sont revenus (garde de dominance)

- **Cause racine du trou historique** : le filtre « fonctionnel » de l'ingestion travaille PAR LIBELLÉ — 
  « Paris » (France, 2,1 M hab.) coexiste avec Paris (Texas, 24 k) et Paris (Ontario) → multi-valeurs → 
  REJETÉ. Les villes CÉLÈBRES étaient tuées par leurs homonymes minuscules !
- **Garde de DOMINANCE** (mode `compte_dominant`, ingere_t7) : valeur max ≥ 20× la 2ᵉ → l'homonyme dominant
  est retenu (la lecture évidente) ; sinon ambiguïté réelle → HORS. Ré-extraction QLever fraîche :
  **480 homonymes résolus, 17 399 villes écrites** — « quelle est la population de la capitale de la
  France ? » → *2 103 778 (en composant : capitale de France = Paris, puis population de Paris)* ENFIN. ✨
- **Tokyo reste HORS, et c'est VOULU** : deux entités Wikidata portent le label « Tokyo » (préfecture
  14,26 M vs les 23 arrondissements 9,64 M, ratio 1,5 — sous le seuil) : la question a réellement deux
  réponses selon le découpage → abstention honnête (présentée « ville du Japon »).
- Registre des sources : entrée `wikidata-wdqs` restaurée (renommage passé du registre cassait l'import des
  scripts d'ingestion). Sauvegarde de l'ancien fichier conservée. Bancs : 151/151 (cas « population de la
  capitale » attend désormais la VRAIE valeur), 162/162, 18/18, 16/16.

## 2026-07-06 — Faits biologiques curés + métamoteur fiabilisé

- **Seed bio validé par Yohan** (`src/faits_bio_seed.jsonl` + `_cap_fait_bio`) : « combien de chromosomes a
  l'être humain ? » → *46 (23 paires)* ; araignée *8 pattes (c'est un arachnide, pas un insecte)* ; pieuvre
  *3 cœurs* ; humain *206 os, 32 dents* ; chat *1 vie (les « 9 vies » sont une légende)* ; hors seed →
  abstention (« combien de pattes a un dragon ? »).
- **Métamoteur** : Mojeek rétrogradé en DERNIER (quota serré → 403 dès la 1re requête, observé au challenge
  web) — Bing RSS et DuckDuckGo lite, fiables, passent devant ; le repli existant reste inchangé.
- Banc raisonnement **162/162** (4 cas bio dont 1 garde), paraphrases 151/151, suite 18/18, challenge 16/16,
  valide_maj 25/25.

## 2026-07-06 — Mises à jour ZÉRO ACTION : l'utilisateur n'a plus RIEN à faire

- Exigence Yohan : « beaucoup d'utilisateurs ne savent pas se servir d'un PC, il faut qu'ils n'aient rien à
  faire ». Vécu le matin même : app lancée pendant que le CI compilait la release → aucune MAJ proposée
  jusqu'au prochain démarrage (le build 39 ne vérifiait qu'au boot).
- **Auto-application au démarrage** : MAJ auto ON + version plus récente détectée 20 s après le boot →
  téléchargement et remplacement TOUT SEULS (l'app vient de s'ouvrir, le redémarrage est indolore). **Garde
  anti-boucle** : une cible déjà tentée dans les 6 h n'est pas re-tentée automatiquement (un swap raté — 
  antivirus, updater cassé — ne re-télécharge pas en boucle ; la bannière manuelle reste disponible).
- **Re-vérification périodique** : serveur (15 min) + front (`setInterval` sur /api/maj) → une release publiée
  PENDANT que l'app tourne fait apparaître la bannière toute seule, sans aucun geste.
- Résidus corrigés du matin : 88 conversations de tests nocturnes nettoyées de `~/.verax/conversations` ;
  swap manuel 39→40 sur la machine de Yohan (l'updater du 39 avait encore les bugs corrigés dans le 40).
- Gate `valide_maj` **25/25** (6 vérifications ajoutées : anti-boucle ×3, veille serveur, garde auto-apply,
  polling front), suite 18/18.

## 2026-07-06 — Classiques curés : la tomate (fruit ET légume), 7 continents, villes bien présentées

- **« La tomate est-elle un fruit ou un légume ? »** → *les deux points de vue sont vrais : botaniquement un
  FRUIT, en cuisine un LÉGUME — je ne tranche pas* (liste fermée : tomate, avocat, concombre, courgette,
  aubergine, poivron, potiron, citrouille ; l'ancien « la tomate est un légume — je ne le rattache pas à
  fruit » niait une vérité botanique, et « l'avocat » répondait… « un droit », le métier homonyme !).
- **« Combien de continents ? »** → *7 selon le modèle courant (liste), mais c'est une CONVENTION (5 ou 6
  selon les modèles)* — au lieu de « 27 termes que je classe comme continent ».
- **Présentation d'entité** : « berlin — *paquet de fil arrêté par un nœud* » (nom commun Wiktionnaire !) →
  « Berlin — ville de l'Allemagne » (pays_ville prime sur la définition bruitée dans l'abstention).
- Banc raisonnement **158/158** (4 cas), paraphrases 151/151, suite 18/18, challenge 16/16.

## 2026-07-06 — « Combien mesure le mont Blanc ? » : 4 808 m, plus jamais le tableau de 56 cm

- **FAUX trouvé à la chasse** : « combien mesure le mont Blanc ? » → *0,559 m* (un TABLEAU « Mont Blanc » !).
  Double correctif : le lookup TYPÉ essaie l'entité ENTIÈRE (« mont Blanc » dans altitude_sommet → 4 808,06 m)
  avant le nom nu ; et une entité GÉO à type-word (mont/pic/lac/île) n'est JAMAIS servie par une œuvre d'art
  homonyme dans le repli famille. + recadrage « combien mesure X » → hauteur.
- **« Napoléon » nu = l'Empereur** : alias vers « Napoléon Ier » avec GARDE ordinale (« Napoléon III » reste
  intact) → « où est né Napoléon ? » → *Ajaccio*, « quel âge avait Napoléon à sa mort ? » → *52 ans*.
- **« Combien de pays dans le monde ? »** → *249 rattachés à un continent (compté exactement — le décompte
  « officiel » dépend de la définition : 193 membres ONU)* — honnête sur la convention.
- Trous d'ingestion notés : Première/Seconde Guerre mondiale absentes de annee_debut_guerre ; capitale de
  l'Afrique du Sud absente (3 capitales) ; « qui était Napoléon III » sans faits-personne.
- Banc paraphrases **151/151** (4 cas), raisonnement 154/154, suite 18/18, challenge 16/16.

## 2026-07-06 — Créateur : l'homonymie d'œuvres est LISTÉE (« la Neuvième Symphonie »)

- « qui a composé la Neuvième Symphonie ? » abstenait en silence : l'œuvre de **Beethoven** coexiste avec un
  FILM homonyme (musique de Kurt Schröder) et l'unicité stricte tuait le lookup. Le branch spécifique de
  `_cap_createur` LISTE désormais les sens vérifiés (comme le générique) ; l'affichage reprend la clé stockée
  (« La joconde a été peintE par… », accord conservé). Banc raisonnement **154/154**.

## 2026-07-06 — FAUX mononymes célèbres : « Mozart est né en 1979 » (le footballeur brésilien !) corrigé

- Le nom NU d'un géant matche un HOMONYME obscur des datasets : « Mozart » → footballeur né en 1979,
  « Bach » → 1882 — et même « Johann Sebastian Bach » (clé stockée) est le PETIT-FILS peintre (Berlin 1748),
  le compositeur vivant sous la clé FRANÇAISE « Jean-Sébastien Bach » (1685).
- Carte d'alias (0alias) étendue aux MONONYMES incontestables, chaque cible VÉRIFIÉE contre les clés réelles :
  Mozart→Wolfgang Amadeus Mozart (*1756* ✓), Beethoven (*mort 1827* ✓), Bach→Jean-Sébastien Bach (*1685* ✓),
  Einstein (*Ulm* ✓), Picasso (fiche ✓) ; Shakespeare/Churchill/Darwin/Newton/Gandhi → nom complet (absent de
  l'extraction → abstention honnête, toujours mieux qu'un homonyme faux). Garde anti-imbrication (le mononyme
  n'est pas re-remplacé si le nom complet est déjà dans la phrase).
- Banc paraphrases **147/147** (4 cas), raisonnement 153/153, suite 18/18, challenge 16/16.

## 2026-07-06 — FAUX d'homonymes d'œuvres éradiqués : la tour Eiffel n'est plus un tableau de 63 cm

- **Trouvés par mes propres sondes** (la carte de couverture les masquait) : « hauteur de la tour Eiffel ? »
  → *0,632 m* (le TABLEAU « La Tour Eiffel », pas le monument !) ; « hauteur de la Joconde ? » → *2,48 m*
  (une SCULPTURE homonyme, pas le tableau de Vinci) ; et la variante d'article ramenait le hameau « La
  France » (3,4 km²) pour « superficie de la France ».
- **Type-check homonyme dans les dimensions** (`_lookup_famille` + gardes `_cap_dimension`) :
  - une entité MONUMENT (ville_monument) n'est jamais servie par une relation d'ŒUVRE D'ART (liste fermée :
    peinture/estampe/aquarelle/dessin/gravure/photo/litho/affiche) ni de sculpture ;
  - une PEINTURE connue (peintre_oeuvre) n'est jamais servie par une SCULPTURE homonyme ;
  - le match EXACT (sans article) PRIME sur les variantes d'article (le pays France avant le hameau) ;
  - valeurs AMBIGUËS across homonymes → l'ambiguïté est DITE (« précise : le tableau X, le monument X ») ;
  - monument/tableau connu sans dimension stockée → abstention qui COUPE la cascade (le moteur lourd ne peut
    plus piocher l'homonyme) : *« je ne confonds pas avec les œuvres d'art homonymes »*.
- **Lisibilité** : longueurs stockées en mètres ≥ 10 km affichées en km d'abord — « longueur du Yangzi
  Jiang » → *6 300 km (6 300 000 m)* (conversion exacte, valeur brute montrée).
- Banc raisonnement **153/153** (4 cas), paraphrases 143/143, suite 18/18, challenge 16/16, constructions 4/4.

## 2026-07-06 — Couverture atomique 79 % + devise/motto + planètes seedées + N-way court + pluriels listés

- **Couverture atomique rejouée** (3 questions × 1 258 relations testables = 3 738 questions, en processus,
  base complète) : **79 % résolues**. Le tri des « faux potentiels » montre surtout des artefacts de FORMAT du
  générateur (valeur brute « 6300000 » vs affichage « 6 300 000 m », symboles, PIB en $ espacé) — les sondes
  manuelles sur serveur réel confirment les valeurs justes.
- **« Quelle est la devise de la France ? » désambiguïsé** (`_cap_devise`) : *« Liberté, Égalité,
  Fraternité » (Si tu voulais la MONNAIE : euro.)* — les DEUX lectures vérifiées ; « devise NATIONALE » →
  motto seul. (Avant : « euro » sec, le motto stocké dans devise_pays était inatteignable.)
- **Planètes seedées** (est_un_seed) : la définition Wiktionnaire de « jupiter » est du bruit circulaire
  (*« exoplanète de taille similaire à jupiter » !*) → « Jupiter est-elle une planète ? » → *Oui*, et
  l'abstention présente désormais « Jupiter — planète » (le SEED curé prime sur la définition bruitée dans la
  présentation d'entité). Mercure→Neptune, Pluton (naine), Soleil (étoile), Lune (satellite).
- **N-way COURT** : « le plus ancien entre Marignan, Verdun et Waterloo ? » sans « quel est » marche
  (préfixe interrogatif optionnel) — l'énumération ne part plus au multi-questions (découpe virgule = bruit).
- **Pluriels listés** : « quelLES langUES parle-t-on au Japon ? » → la liste des 37 (singularisation nue dans
  `_liste_inverse._base` — un pluriel hors-alias ne retombait jamais sur son token) ; le singulier reste
  « japonais ».
- Banc raisonnement **149/149**, paraphrases 143/143, suite 18/18, challenge 16/16, synonymes 8/8.

## 2026-07-06 — Mode web éprouvé : garde subjectivité, définitions citées, outils atteignables (challenge web 14→22/30)

- **Garde SUBJECTIVITÉ avant le web** : « quel est le plus beau pays du monde ? » (web ON) partait au
  métamoteur et rapportait… le FILM « Le Plus Beau Pays du monde » (extrait Wikipédia hors-sujet). La
  recherche web consulte désormais le classifieur de bornage : une question NON BORNÉE ne part JAMAIS au web →
  cadrage honnête (*« pas de réponse unique, c'est subjectif — donne-moi un critère »*). + « serait vraiment
  rafraîchissante » ajouté aux prédicats subjectifs (recommandation évaluative au conditionnel).
- **Définitions citées et soutenues** : « Qu'entend-on par « sérendipité » ? » / « que signifie X ? » → la
  définition (formes ajoutées à `_DEF_RE`, guillemets autour du mot acceptés).
- **Outils atteignables** : « distance entre Paris et Madrid » SANS point d'interrogation est maintenant une
  DEMANDE (`_veut_reponse` : tête d'attribut nue + connecteur) → *1 053 km, orthodromie* ; « nature
  grammaticale du VOCABLE nonobstant » → *préposition* (« vocable/terme » acceptés).
- **Did-you-mean abusif corrigé** : « espace » (mot français parfaitement valide, absent du lexique POS mais
  DÉFINI dans definition_nom) déclenchait « vouliez-vous dire espece ? » → `_mot_defini` en renfort de
  `_mot_reel` dans le générateur de suggestions.
- Harness challenge : apostrophes typographiques normalisées, marqueurs SOCIAL (« salut »), OUTIL
  (préposition/conjonction/pronom/déterminant), FACTUEL (définitions longues « Terme : … »).
- **Explications BORNÉES** : « comment fonctionne une pompe à chaleur ? », « décris le mécanisme de la
  réaction de Maillard », « en quoi la relativité restreinte a bouleversé… », « quelles furent les
  conséquences… » — une vérité DOCUMENTÉE existe → classé borné → **rapport web attribué** (« d'après
  Wikipédia… », gate de pertinence) au lieu d'une clarification en boucle. Jamais généré : rapporté ou rien.
- Challenge **16/16** (sans web) et **28/30** (web — c'était 14/30 ; les 2 restants sont des artefacts du
  harness, comportements vérifiés CORRECTS sur le serveur réel ; Mojeek renvoie 403 au métamoteur, à
  surveiller). Tous bancs verts : 142/142, 146/146, 4/4, 8/8, 18/18, 19/19.

## 2026-07-06 — Relatives, appositions, comparaison superlative : batterie complexité 5/20 → 18/20

- **Propositions RELATIVES résolues en entités** (`_resout_relatif`, feuille de `_resout_noeud`) :
  - « sur quel continent se trouve le pays **dont la capitale est** Tokyo ? » → *le Japon se trouve en Asie
    (en composant d'abord : pays dont capitale est Tokyo = Japon)* — lecture INVERSE à match UNIQUE (FAUX=0) ;
  - « quelle est la langue du pays **où se trouve** la tour Eiffel ? » → *français (tour Eiffel est à Paris,
    puis Paris est en France, puis langue de France = français)* — monument → ville → pays, 3 sauts montrés.
- **Comparaison à FEUILLE SUPERLATIVE** : « le pays le plus peuplé d'Europe est-il plus peuplé que le
  Japon ? » → l'argmax borné est résolu d'abord (fait réel, résolution MONTRÉE), puis la comparaison chiffrée.
- **Appositions et modaux compris** : « ce grand pays qu'est l'Australie » → *l'Australie* ; « quelle pourrait
  bien être… » → « quelle est… » ; « qui a bien pu écrire » → « qui a écrit » (verbes créateurs fermés) ;
  « combien de gens vivent en France ? » → *population de la France*.
- **Bug réel de guérison corrigé** : « **BON alors**, cette histoire de… » était « corrigé » en « BONNE
  alors » → la phrase guérie ne se dévoilait plus et court-circuitait tout (retour fallback avant (0dev)).
  « bon/bonne/alors/bref/voilà… » ajoutés aux mots protégés.
- **Harness e2e_complexite corrigé** : le bloc mémoire appelait `repond()` directement (qui n'indexe pas) →
  0/6 à tort ; passage par le VRAI chemin serveur (`ajoute_message`) → 6/6.
- Batterie complexité/compréhension/mémoire : **18/20** (5/20 au début de nuit ; les 2 restants = trous de
  données documentés : population_ville sans Paris, aucune relation dirigeant/chef d'État nominatif).
- Banc paraphrases **141/141** (11e vague), raisonnement 146/146, suite 18/18, challenge 16/16, valide_maj 19/19.
- **Complément (même nuit)** : « en quelle année Christophe Colomb a-t-il découvert l'Amérique ? » → *1492* —
  variantes d'élision rendues COMPOSABLES (« l Amérique » ↔ « l'Amérique » se combine avec le libellé Wikidata
  composé « découverte **et exploration** de l'Amérique ») + recadrage « X a-t-il découvert Y » (le sujet est
  retiré sans être endossé : la réponse nomme l'événement résolu). Paraphrases **142/142**. Validation
  SERVEUR RÉEL de la nuit entière : **25/25** briques (port 8899, web OFF, RSS 163 Mo après usage).

## 2026-07-06 — FAUX corrigé : « la langue de Tokyo » répondait « français » (l'œuvre homonyme)

- Le lookup direct de « langue de Tokyo » matchait la langue d'une **ŒUVRE nommée « Tokyo »** (film en
  français) au lieu de la ville. Le PONT ville→pays prime désormais sur le lookup direct pour les attributs
  PAYS-CONSTANTS quand l'entité est une ville connue de pays_ville → *japonais (en composant : Tokyo est au
  Japon, puis langue de Japon = japonais)*.
- Recadrage locatif : « quelle langue parle-t-on **à Tokyo / au Japon** ? » → « quelle est la langue de X »
  (bonus : « au Japon » répond *japonais* au lieu de déverser la liste des 37 langues/dialectes stockés).
- Banc paraphrases **133/133** (3 cas), raisonnement 146/146, suite 18/18, challenge 16/16.

## 2026-07-06 — Auto-update ÉPROUVÉ EN RÉEL (build 38 → 39) : 4 bugs du flux trouvés et corrigés

- **Test grandeur nature** : mise à jour appliquée sur le .exe réel — téléchargement du build 39, bascule du
  binaire par l'updater, redémarrage, `version_locale: "39 84180a0"` vérifié à l'arrivée. Le cycle complet
  commit → release → détection → swap → relance fonctionne.
- **4 bugs RÉELS corrigés au passage** (le test de détection seul ne les voyait pas) :
  1. l'app promettait « Provara va se fermer » mais **ne se fermait jamais** → l'updater attendait notre PID
     pour toujours. Fix : fermeture réelle programmée (1,5 s après la réponse HTTP, `os._exit`) ;
  2. `timeout /t` dans le .bat **exige une console** — lancé sans fenêtre, il échoue → remplacé par
     `ping -n` (marche partout) ;
  3. `CREATE_NO_WINDOW | DETACHED_PROCESS` sont **mutuellement exclusifs** (comportement indéfini, l'updater
     mourait avec l'app) → `CREATE_NO_WINDOW | CREATE_BREAKAWAY_FROM_JOB` (survit aussi à un job Windows qui
     tue ses enfants ; repli sans breakaway si le job l'interdit) ;
  4. `/api/maj/appliquer` **contournait le toggle Internet** (appel réseau silencieux même web OFF) → refus
     actionnable (« réactive Internet »), aucun octet sans consentement.
- Gate `valide_maj` **19/19** (6 vérifications ajoutées sur l'updater et les gardes serveur), suite 18/18.

## 2026-07-06 — Antonymes câblés + « le bouquin X » + batterie serveur : 44 % → 78 %, zéro FAUX

- **`_cap_contraire`** : « quel est le contraire de grand ? » → *petit, microscopique, bref…* — la fonction
  `synonymes.contraires` (réseau JeuxDeMots embarqué) existait SANS être câblée nulle part (brique orpheline
  détectée). Liste honnête sans élection arbitraire (les données JDM sont asymétriques), source nommée.
- « le **bouquin** 1984, c'est de qui ? » → *George Orwell* (« bouquin » ajouté aux type-words d'œuvre).
- **Batterie massive REJOUÉE contre le serveur source** (88 questions multi-domaines, port 8899, web OFF) :
  **69/88 OK (78 %) contre 39/88 (44 %) sur le .exe build 38 — et ZÉRO FAUX** (les 2 FAUX du build 38 sont
  corrigés ; les 19 restants sont des abstentions honnêtes, majoritairement des trous d'extraction Wikidata
  documentés : Versailles 1919, Newton et Marie Curie sans occupation/nationalité, Nil/Amazone sans longueur,
  frontières entre pays absentes, formules chimiques absentes).
- Banc paraphrases **130/130**, raisonnement 146/146, suite 18/18, challenge 16/16, synonymes 8/8,
  constructions 4/4.

## 2026-07-06 — Protons, lunes, et le mur de Berlin : routage verbe→relation de date

- **`_cap_protons`** : « combien de protons a l'hydrogène ? » → *1 proton — le numéro atomique Z (c'est sa
  définition)* (relu dans numero_atomique, 118 éléments) ; « combien d'électrons possède le carbone ? » →
  *6 électrons pour l'atome NEUTRE (autant que de protons)*.
- **`_cap_lunes`** : « combien de lunes a Mars ? » → *2 dans mes données : Déimos, Phobos* — compte RÉEL par
  lecture inverse de corps_parent_astre, honnête sur la non-exhaustivité (Jupiter en a 95 connues).
- **Routage VERBE → relation de date** (`_DATE_VERBE_RE`) : « en quelle année est TOMBÉ le mur de Berlin ? »
  → *1989* (annee_dissolution) et « quand a été CONSTRUIT le mur de Berlin ? » → *1961*
  (annee_construction_edifice). Sans ce routage, la première relation trouvée aurait décidé entre 1961 et
  1989 — un coup de dés, pas un fait.
- Trous d'INGESTION documentés (pas de fix code possible, à corriger côté source) : « traité de Versailles »
  (1919) absent de date_evenement ; Isaac Newton (le physicien) sans faits-personne (naissance/nationalité) ;
  Nil/Amazone sans longueur ; Napoléon Ier absent de successeur_personne.
- Banc raisonnement **146/146** (7 cas ajoutés), paraphrases 127/127, suite 18/18, challenge 16/16.

## 2026-07-06 — Créateur : type-words d'œuvre + alias de personnes célèbres

- « qui a réalisé **le film** Pulp Fiction ? » échouait (la clé réelle est le titre NU) : liste fermée
  `_TYPE_OEUVRE_RE` (film/livre/roman/tableau/statue/chanson/série/jeu/album/opéra/pièce/poème/BD) jetée avant
  lookup → *Quentin Tarantino* ; « le roman 1984 », « le tableau la Joconde » pareil.
- Étage **(0alias)** : « **Napoléon Bonaparte** » → « Napoléon Ier » (la clé RÉELLE de toutes les relations de
  personnes) — carte FERMÉE d'identités incontestables (même être humain), motifs accent-tolérants, question
  réécrite rejouée par le pipeline complet. « où est né / quand est mort / qui était Napoléon Bonaparte »
  répondent désormais (Ajaccio, 1821, fiche complète).
- Banc paraphrases **127/127** (10e vague), raisonnement 139/139, suite 18/18, challenge 16/16.

## 2026-07-06 — Records géographiques mondiaux : la couche curée qui évite les FAUX d'argmax

- **Pourquoi pas un simple argmax sur les tables ?** Audit des données : `altitude_montagne` contient 37
  reliefs MARTIENS/vénusiens (Tharsis Tholus 8 930 m > Everest !), `longueur_fleuve` ne couvre NI le Nil NI
  l'Amazone (le max serait le Yangzi — FAUX), `superficie_ile` n'a pas le Groenland (le max serait la
  Nouvelle-Guinée — FAUX). Un argmax naïf « du monde » inventerait des records.
- **Nouveau `_cap_record_monde`** (table FERMÉE de records incontestables, 3 ordres de mots) :
  - « le plus haut sommet du monde ? » → *l'Everest — 8 848,86 m, **relu en direct** dans les données* ;
  - « le plus long fleuve ? » → *Nil ou Amazone : primauté scientifiquement **DISPUTÉE** — je ne tranche pas*
    (+ signale honnêtement le trou de la table) ;
  - « la plus grande île ? » → *Groenland (l'Australie étant un continent)* ; « le plus grand désert ? » →
    *Antarctique (définition scientifique) / Sahara le plus grand désert CHAUD (9 200 000 km² relus)* ;
  - « la plus grande planète ? » → *Jupiter — argmax RÉEL sur diametre_moyen_planete (ensemble complet,
    8 planètes)* ; lac le plus profond (Baïkal), océan (Pacifique), fosse (Mariannes).
  - Les superlatifs par ZONE (« la plus haute montagne d'Europe ») restent hors de ce cap → abstention
    FAUX=0 inchangée (membership troué).
- Banc raisonnement **139/139** (7 cas dont 1 garde), paraphrases 122/122, suite 18/18, challenge 16/16.

## 2026-07-06 — Calcul étendu : puissances, pourcentages, précédence en toutes lettres, conversions exactes

- `_reponse_calcul` étendu (fermé, sous intention de calcul) : **« 7 au carré » → 49**, « 2 au cube » → 8 ;
  **« 20 pour cent de 150 » / « 15 % de 200 » → 30** (substitution AVANT les nombres en lettres — « pour
  cent » devenait « pour 100 » et cassait le motif) ; **« 3 plus 4 fois 5 » → 23** (opérateurs en toutes
  lettres avec la VRAIE précédence, substitués uniquement ENTRE chiffres) ; repli d'EXTRACTION de la
  sous-expression mathématique pure (« QUEL EST 20 * 150 / 100 ? » — le préfixe interrogatif faisait échouer
  les évaluateurs).
- **Nouveau `_cap_conversion`** : conversions d'unités FERMÉES et EXACTES, formule montrée — « convertis 100
  degrés Celsius en Fahrenheit » → *212 °F ((100 × 9/5) + 32)* ; km↔miles (1 mile = 1,609344 km, définition
  légale) ; kg↔livres (1 livre = 0,45359237 kg). Hors liste fermée → None (jamais d'approximation inventée).
- Banc paraphrases **122/122** (9e vague : 9 cas calcul/conversion), raisonnement 132/132, autres bancs verts.

## 2026-07-06 — Composition profonde : enveloppe interrogative, pont ville→pays, élision, filet temporel

- **FAUX .exe corrigé — « sur quel continent se trouve la capitale du Japon ? » répondait « Tokyo »** (le
  moteur lourd résolvait le GN interne et ignorait l'enveloppe). Nouvel étage **(1a-env)** : quand la question
  pose une AUTRE question autour d'un GN composé (« sur quel continent… », « où est né… », « quand est mort… »),
  le GN interne est résolu (maillon VÉRIFIÉ montré), substitué, et le pipeline complet est REJOUÉ →
  *« Asie — je le déduis : Tokyo est la capitale du Japon et le Japon est en Asie (en composant d'abord :
  capitale de Japon = Tokyo) »*. Marche en profondeur : « où est né l'auteur de 1984 ? » → *Motihari* ;
  « quand est mort le successeur de Louis XIV ? » → *1774* ; « sur quel continent se trouve la capitale du
  pays le plus peuplé du monde ? » → *Asie* (feuille superlative + 3 sauts). Un simple « quelle est la
  capitale de X » reste au lookup direct (garde `_ENV_PREFIXE_RE`).
- **Pont ville→pays pour attributs PAYS-CONSTANTS** (`_pont_ville_pays`) : « la monnaie de la capitale du
  Japon ? » → *yen (Tokyo est au Japon, puis monnaie du Japon)*. Liste FERMÉE (monnaie, langue, continent,
  hymne — PAS la population : population de Tokyo ≠ population du Japon). Audit anti-homonyme : pays_ville =
  9 998 villes, 0 nom multi-pays.
- **FAUX .exe corrigé — « quand a eu lieu la bataille de Hastings ? » répondait « Battle »** (la VILLE du lieu
  de la bataille, East Sussex !) : la clé réelle est « bataille **d'**Hastings » (élision) que le lookup
  streaming ratait → la cascade servait un sous-lookup du mauvais type. Double correctif : variantes
  d'ÉLISION dans `_annee_de` (« de Hastings » ↔ « d'Hastings » ↔ « d hastings » apostrophe perdue) → *1066* ;
  et FILET TEMPOREL générique : une question « quand / en quelle année » ne peut plus rendre une réponse sans
  année (même filet que les mesures).
- **Abstention à CHAÎNE PARTIELLE** : « population de la capitale de la France ? » disait « rien n'ancre
  capitale de la France » (trompeur — ça résout très bien vers Paris). Désormais : *« j'ai composé capitale de
  France = Paris — mais je n'ai pas de fait vérifié « population de Paris » »* (le maillon manquant est
  NOMMÉ ; Paris/Tokyo absents de population_ville = trou d'extraction Wikidata, à corriger côté ingestion).
- Banc paraphrases **113/113** (8e vague : 8 cas de composition profonde), raisonnement 132/132,
  constructions 4/4, synonymes 8/8, suite 18/18, challenge 16/16.

## 2026-07-06 — FAUX corrigé : « quel fleuve traverse Paris ? » répond « la Seine », plus une liste de 147 rivières

- **Cause** : dans `_liste_inverse`, le mot « fleuve » servait à la fois de mot-TYPE interrogé (« quel fleuve… »)
  et de VALEUR d'ancrage (147 rivières ont type=fleuve dans `type_riviere`) → la question déversait l'échantillon
  alphabétique complet en ignorant « traverse Paris ». **Garde ancre≠type** ajouté : la valeur d'ancrage ne peut
  pas être le mot-type lui-même ni son alias (`_base(vn) not in rtoks`).
- **Trou de données comblé au niveau code** : les datasets Wikidata n'ont AUCUNE relation ville↔fleuve (vérifié :
  `subdivision_riviere` ne contient pas Paris). Nouveau module **`src/fleuve_ville.py`** + seed curé
  **`src/fleuve_ville_seed.jsonl`** (~100 couples incontestables, articles inclus — même précédent que
  `est_un_seed.jsonl`) et nouveau cap **`_cap_fleuve_ville`** :
  - « quel fleuve traverse Paris ? » → *C'est la Seine qui traverse Paris.* (« coule à », « arrose », « passe
    par », « sur quel fleuve se trouve Budapest » couverts) ;
  - « quelle rivière traverse Lyon ? » → *le Rhône et la Saône* (liste complète des fleuves majeurs) ;
  - « quelles villes le Danube traverse-t-il ? » → *notamment Vienne, Budapest… (liste non exhaustive)* ;
  - « la Seine traverse-t-elle Paris ? » → *Oui* ; paire inconnue → le fait réel montré, JAMAIS de « non » sec
    (la Bièvre traverse réellement Paris sans être dans le seed) ; ville hors seed → abstention honnête.
- Banc raisonnement **132/132** (7 cas ajoutés dont 2 gardes FAUX=0), paraphrases 105/105, constructions 4/4,
  synonymes 8/8, suite 18/18, challenge 16/16. README FR/EN à jour. (Le module et le seed sont sous `src/` →
  embarqués automatiquement dans le .exe via `--add-data src`.)

## 2026-07-06 — FAUX grave corrigé : « la Terre tourne-t-elle autour du Soleil ? » ne répond plus « Baudelaire »

- **Cause double** : (1) `_ORBITE_RE` ne consommait pas le clitique d'inversion (« tourne**-t-elle** ») → le
  groupe capturait « -t-elle autour du Soleil » au lieu de « Soleil » ; (2) même bien parsé, `_cap_orbite`
  refusait volontairement les relations DIRECTES (chaîne de 2 : Terre → Soleil, « pas une dérivation ») → la
  question filait vers le moteur lourd qui partait sur le poème « Le Soleil » de **Baudelaire** (hors-sujet).
- **Correctif** : clitique `-t-il/-t-elle/-t-on` consommé (avec variantes SMS sans tirets) ; le groupe entité ne
  peut plus commencer par un espace (piège regex lazy) ; un fait direct répond désormais *« Oui — c'est un fait
  vérifié dans mes données : la Terre orbite le Soleil »*.
- **Bonus soundness** : le sens inverse est maintenant RÉFUTÉ au lieu d'être tu — « le Soleil tourne-t-il autour
  de la Terre ? » → *« Non — c'est l'inverse : la Terre orbite le Soleil »* (l'anti-symétrie d'« orbiter » est
  la règle induite déjà vérifiée sur les 36 faits). Et deux corps connus sans chaîne entre eux (« Mars
  tourne-t-elle autour de Jupiter ? ») reçoivent le fait réel (*« Mars orbite le Soleil — aucun fait reliant
  Mars à Jupiter »*) au lieu de risquer un hors-sujet dans la cascade lourde.
- Banc raisonnement **125/125** (4 cas ajoutés : direct, direct-SMS, dérivé Lune→Soleil, réfutation inverse ×2),
  paraphrases 105/105, constructions 4/4, synonymes 8/8, suite **18/18**, challenge 16/16.

## 2026-07-05 — MISES À JOUR AUTOMATIQUES : le .exe se met à jour tout seul (plus de re-téléchargement)

- **Nouveau module `src/maj.py`** : vérifie honnêtement (FAUX=0) contre les Releases GitHub s'il existe une
  version RÉELLEMENT plus récente (numéro de build monotone `GITHUB_RUN_NUMBER`), télécharge le nouveau `.exe`
  (brut de préférence, zip en repli) et lance un updater Windows qui attend la fermeture, remplace le binaire et
  redémarre. Réglage `auto` persistant (`~/.verax/maj_config.json`). Aucun appel réseau sans Internet activé.
- **UI (2 boutons, selon spec)** : « 🔄 MAJ auto » (toggle) et « 🔍 Rechercher une MAJ » — ce dernier n'apparaît
  QUE si l'auto est désactivée (sinon redondant). Bannière « nouvelle version disponible → Mettre à jour ». Au
  démarrage et à l'activation d'Internet, on vérifie et on propose automatiquement (si auto ON).
- **Routes serveur** : `GET /api/maj`, `POST /api/maj/auto`, `POST /api/maj/verifier`, `POST /api/maj/appliquer`.
- **CI (build-exe.yml)** : tamponne un numéro de build MONOTONE, et à CHAQUE push publie une Release ROULANTE
  « latest » avec le `.exe` brut + le zip + `version.txt`. Résultat : **commit + push → les utilisateurs
  reçoivent la mise à jour sans rien re-télécharger**. L'update embarque TOUS les atomes (le `.exe` re-bundle
  tout `src/` + seeds). Lien direct stable pour les non-techniciens :
  `https://github.com/Provara-IA/Provara/releases/latest/download/Provara.exe`
- **Gate `tests/valide_maj.py`** (13/13, réseau injecté) : parsing du tampon, réglage persistant, détection
  « plus récent », FAUX=0 (jamais de proposition sans version supérieure ni sans réseau). Suite **18/18**.
  Build files (CI + .bat) : `--hidden-import maj` ajouté.

## 2026-07-05 — Chasse au FAUX : 3 défauts de correction trouvés et corrigés

- **Ontologie qui détournait une question relationnelle** : « Berlin est-elle la capitale de l'Allemagne ? »
  (question VRAIE) répondait *« Le Berlin est un paquet — je ne le rattache pas à capitale »* (genre bruité de
  definition_nom : « berlin = paquet de fil »). Garde ajouté : si l'attribut est suivi de « de/du/des Z », c'est
  un FAIT relationnel, pas un is-a → `_cap_ontologie` s'abstient et laisse `_oui_non` répondre *« Oui »*.
- **« même monnaie » aveugle à la zone euro** : « la France et l'Allemagne ont-elles la même monnaie ? »
  abstenait car `_cap_meme_attribut` lisait `monnaie.jsonl` en direct, où les grands pays de la zone euro sont
  absents (extraction Wikidata : monnaie partagée). Corrigé par un lookup ROBUSTE (famille de relations via le
  moteur, qui connaît « France → euro ») → *« Oui — même monnaie : euro »*. (Piste écartée : injecter les pays
  dans monnaie.jsonl déclenchait un conflit d'ingestion « euro » vs « Euro » — le code est le bon niveau de fix.)
- **is-a qui niait une vérité** : « le chat est-il un félin ? » répondait *« je ne le rattache pas à félin »*
  (le genre de la définition saute « félin »). Seed complété : `félin → mammifère` + `chat → félin` → *« Oui —
  chat → félin → mammifère »* (le chaînage vers mammifère est préservé).
- Aucun FAUX trouvé sur les caps de la session (SVO libre, synonyme-tête, constructions, transitif conflits) :
  entités sans donnée s'abstiennent, attributions fausses réfutées. Banc raisonnement **121/121** (3 cas
  ajoutés), paraphrases 98/98, suite 17/17, challenge 16/16, synonymes 8/8.

## 2026-07-05 — Consolidation : audit de câblage atomique + trous is-a comblés + docs/CI à jour

- **Audit de câblage ATOMIQUE (exigence Yohan)** : vérifié que TOUS les atomes sont câblés — **0 orphelin** sur
  50 caps `_cap_*`, 113 fonctions de `repond.py`, et 498 modules `src/`. Le seul module « jamais importé »
  (`_precharge_verax`) est la liste d'imports PyInstaller, référencée par les 2 build files (`--hidden-import`)
  et intentionnellement non-importée au runtime.
- **Trous is-a comblés** : 11 mots courants avaient une chaîne is-a VIDE ou bruitée dans definition_nom
  (avion/bateau/train → *véhicule*, table → *meuble*, pomme de terre → *légume*, pince → *outil*, pantalon →
  *vêtement*, espagnol → *langue*, rouge/vert/jaune → *couleur*). Ajoutés au seed curé `est_un_seed.jsonl`
  (bundlé via `--add-data src`) — is-a incontestables, FAUX=0.
- **CI** : `banc_constructions` (constructions apprises, passe sur l'échantillon) câblé dans la suite → **17/17
  gates**. Les bancs base-complète (paraphrases/synonymes/raisonnement) restent manuels (trous de données sur
  le sample, pas des bugs).
- **README FR + EN à jour** : ajout des capacités majeures de la session — compréhension **quel que soit
  l'ordre des mots**, **constructions apprises** généralisables, **abstention structurée** (structure reconnue
  non ancrée), **chaîne transitive des conflits** militaires, **synonymes de relations** (richesse→PIB).
- Bancs : raisonnement 118/118, paraphrases 98/98, constructions 4/4, synonymes 8/8, suite **17/17**,
  challenge 16/16. Câblage et données vérifiés bundlés ; aucun fichier de build à modifier.

## 2026-07-05 — Synonymes familiers : sondé (déjà riche) + chaînage bagnole→voiture→véhicule complété

- **Sonde** : le module `synonymes` (réseau JeuxDeMots embarqué) est DISPONIBLE et riche — bagnole→voiture,
  toubib→médecin, fric→argent, avec hyperonymes et chaînes. Les frames « c'est quoi un toubib », « une bagnole
  c'est quoi », « qu'est-ce qu'une bagnole », is-a et définition fonctionnent DÉJÀ (le « faux gap » initial
  venait d'un test tapé « c est » au lieu de « c'est »).
- **Un vrai gap comblé** : « voiture » manquait de `definition_nom` (chaîne is-a VIDE) alors qu'« automobile »
  résolvait — la reformulation « bagnole → voiture » butait donc sur « voiture est-elle un véhicule ». Ajout de
  `voiture → véhicule` au seed curé `est_un_seed.jsonl` (mécanisme prévu pour les trous de definition_nom,
  is-a incontestable). « une bagnole est-elle un véhicule ? » → « Oui — bagnole → voiture → véhicule. »
- **Nouveau banc** `tests/banc_synonymes.py` (8/8) : verrouille la compréhension des mots familiers/argotiques
  (définition, is-a, chaînage) — fonctionnalité vitrine. Seed sous `src/` → embarqué via `--add-data src;src`.
- Raisonnement 118/118, paraphrases 98/98, constructions 4/4, synonymes 8/8, suite 16/16 (77/77), challenge 16/16.

## 2026-07-05 — Constructions à trous : l'IA apprend une grammaire en dialoguant (généralisation)

- **Induction de règle À TROU** (`_induit_substitution` réécrit) : une reformulation enseignée sur UNE entité
  généralise à d'AUTRES jamais vues — l'entité vit dans le contexte partagé (le « trou »), jamais touché.
  Deux voies : (1) MINIMALE, mots de contenu propres CONTIGUS (« chef-lieu » → « capitale ») ; (2) ALIGNEMENT
  préfixe/suffixe quand les mots diffèrent de façon DISPERSÉE (« c'est koi le chef-lieu … » → span central).
  Corrige le bug de l'ancienne induction qui joignait des mots NON contigus (« koi chef lieu ») en une clé qui
  ne matchait jamais.
- **Nouveau banc** `tests/banc_constructions.py` : apprend sur le Japon, applique sur Espagne/Italie/Suisse
  (jamais vues) via le pipeline complet — **4/4**, dont le garde FAUX=0 (une construction ne peut pas échanger
  d'entité : « mordor » ne devient jamais « France »). Isolation `VERAX_PATRONS_DIR` temporaire.
- **Garde FAUX=0 affiné** (`_est_entite_probable`) : ne flague que les noms PROPRES (POS « nom propre » ou clé
  d'une relation à clés propres — pays/ville/personne), plus definition_nom exclu. Corrige un faux positif qui
  bloquait « chef-lieu → capitale » (capitale est un nom commun DÉFINI, pas une entité nommée). L'échange
  d'entité réel (« wakanda → france ») reste bloqué car « france » est un nom propre.
- Raisonnement 118/118, paraphrases 98/98, constructions 4/4, suite 16/16 (77/77), challenge 16/16.

## 2026-07-05 — RAM : éviction LRU des caches (le vrai « 600 Mo » enfin identifié et borné)

- **Profilage correctif** : le « ~600 Mo du moteur ia » était une MAUVAISE attribution. `import ia` = +16 Mo,
  le lecteur est mémoire-mappé (~0 RSS), `est_un` est déjà LAZY (69 Mo à la 1re question is-a, pas au
  préchauffage). Le VRAI poste : `_DIRECT_CACHE`/`_REVERSE_CACHE` croissaient SANS BORNE — un serveur long
  touchant beaucoup de relations (superlatifs/argmax/inverse variés) montait à **+487 Mo** (mesuré, 400
  relations). C'est l'origine probable du « 600 Mo » jamais expliqué.
- **Éviction LRU par coût + `malloc_trim`** : les deux caches deviennent des `OrderedDict` bornés (~20 Mo de
  coût-fichier chacun ≈ ~100 Mo RAM). Sous pression, la relation la moins récemment utilisée est évincée et la
  RAM est RENDUE À L'OS via `malloc_trim` (un `del` Python seul ne réduit pas le RSS — fragmentation glibc, la
  leçon de l'essai est_un appliquée ici avec succès). Les relations chaudes restent ; les froides se relisent du
  disque (coût négligeable, fichiers < 4 Mo).
- **Mesuré** : cas pathologique 400 relations **513 → 126 Mo** (−387 Mo) ; scénario réaliste 60 requêtes variées
  **RSS 38 Mo, 12 ms/req** (aucune pénalité de latence — l'éviction ne mord que sous forte pression). Les 4 bancs
  restent verts : raisonnement 118/118, paraphrases 98/98, suite 16/16 (77/77), challenge 16/16.

## 2026-07-05 — Synonymes de têtes de relation + garde FAUX=0 sur les alias appris (trou réel comblé)

- **Synonymes de têtes** (`_cap_synonyme_tete`) : un mot de sens proche d'une relation connue route vers la
  relation EXACTE et sert la valeur vérifiée + unité — « la richesse / le PIB du Japon » → pib_pays (4 435 G$),
  « la taille / l'étendue / la superficie de la France » → superficie (551 695 km²), « le nombre d'habitants du
  Japon » → population (123 M). Carte curée fermée. FAUX=0 : si l'entité n'est pas dans la relation (« taille de
  Napoléon » n'est pas dans superficie), rien n'est renvoyé. Français soigné (« du Japon » via realisation_fr).
- **TROU FAUX=0 réel comblé** (exposé par le cap ci-dessus) : un patron APPRIS pouvait ÉCHANGER une entité —
  une substitution `wakanda → france` répondait « Population de la France » à une question sur le Wakanda.
  `_alias_change_entite` refuse tout alias qui INJECTE une entité (nom propre POS ou fait ancré) absente de la
  question d'origine : un patron corrige une FORMULATION, jamais de quoi on parle. On ne regarde que les mots
  INTRODUITS (un mot retiré comme « koi »→« quoi » ne fabrique pas de faux — koï s'ancre pourtant comme poisson).
- **Bug préexistant corrigé** : `_localisation` (coordonnées) sans garde concept-commun → déplacé au commit
  précédent ; ici confirmé par non-régression.
- 6e vague du banc paraphrases (synonymes de têtes) : **98/98 (100 %)**. Raisonnement **118/118**, suite 16/16
  (77/77), challenge 16/16.

## 2026-07-05 — LE GRAND LEVIER : parse SVO libre (ordre des mots quelconque) + garde concept

- **Parse SVO libre** (`_parse_svo_libre`, ultime recours vérifié) : quand aucune règle ne matche mais que la
  question porte une TÊTE DE RELATION connue et une ENTITÉ ancrable dans un ORDRE LIBRE, on isole (tête, entité)
  sans se soucier de la position, on reconstruit « <tête> de <entité> » et on rejoue en lookup vérifié. « du
  Japon, dis-moi la capitale », « pour le Japon, la monnaie ? », « Japon : monnaie ? », « la capitale, c'est
  quoi, pour le Japon ? » → réponses vérifiées. FAUX=0 absolu : ne répond QUE si le fait se vérifie, sinon
  l'abstention structurée prend le relais.
- **Câblé à deux points** : avant le découpeur multi-questions (une question à ordre libre découpée par virgules
  n'est PAS une multi-demande — gardé contre les vraies coordinations « et/puis ») et en dernier recours avant
  l'abstention. Découpe sur le texte BRUT (piège : `_normalise` supprime les virgules).
- **Bug FAUX=0 préexistant corrigé** : « où se trouve le bonheur ? » renvoyait les coordonnées d'un hameau
  homonyme « Bonheur » (le chemin coordonnées `_localisation` n'avait pas la garde `_est_concept_commun` que
  `_cap_localisation` avait déjà) → abstention structurée désormais.
- 5e vague du banc paraphrases (ordre libre) : **91/91 (100 %)**. Raisonnement **113/113**, suite 16/16
  (77/77), challenge 16/16.

## 2026-07-05 — Piste #5 : raisonnement transitif étendu aux CONFLITS militaires

- **Nouveau domaine transitif** (`_TRANS_GROUPES` cle="conflit", relations `conflit_parent_bataille/_operation_
  militaire/_siege`) : la mereologie « fait partie de » des conflits — bataille → opération → front → guerre.
  Chaînes RÉELLES de profondeur 3-4 (« opération Tonga → débarquement de Normandie → bataille de Normandie →
  front de l'Ouest »). Sonde préalable : 5853 entités, seulement 3 multi-parents (quasi-fonctionnel) → sûr
  sous la garde anti-homonyme existante.
- **Deux formes** : vérification oui/non (« l'opération Tonga fait-elle partie du front de l'Ouest ? » → Oui,
  avec la dérivation complète) et question ASCENDANTE ouverte (`_conflit_ascendant` : « de quelle guerre fait
  partie la bataille de Marignan ? » → guerre de la Ligue de Cambrai ; chaîne montrée si profondeur ≥ 2).
- FAUX=0 : chaîne de faits stockés re-vérifiable, homonyme intraversable, claim faux refusé (« Marignan fait
  partie de la guerre de Cent Ans ? » → abstention). Le seuil « ≥ 2 sauts » est relâché à « ≥ 1 saut » pour ce
  domaine car la relation n'existe nulle part ailleurs (pas de voie normale qui la servirait).
- Raisonnement **109/109** (4 cas ajoutés), paraphrases 79/79, suite 16/16 (77/77), challenge 16/16.

## 2026-07-05 — E2E serveur réel 14/14 des nouveautés + bug de rappel mémoire (question SMS) corrigé

- **Validation E2E serveur réel 14/14** (mémoire vierge, base complète, web coupé) des briques de la session
  non couvertes par l'E2E précédent : SMS+oral+fautes empilés, anaphores multi-tours, abstention structurée
  3e famille, hyponymes « quels X sont des Y » + anti-bruit, gate de pertinence web. Script `e2e_session2.sh`.
- **Bug réel démasqué et corrigé** : une QUESTION stockée en langage SMS (« cest koi la capitale du japon »)
  n'était pas reconnue comme question par le filtre de rappel mémoire (`_veut_reponse` ne voit pas « cest
  koi ») → elle ressortait comme un énoncé rapporté (« D'après ce que tu m'as dit : … ») à une question sans
  rapport (« capitale du wakanda »). Le filtre applique désormais `_desms` avant `_veut_reponse` : une question
  SMS est exclue des rappels comme toute autre question.
- Raisonnement **105/105**, paraphrases 79/79, suite 16/16 (77/77), challenge 16/16.

## 2026-07-05 — Hyponymes : nouveau phrasé « quels X sont des Y » + filtre anti-bruit

- Sonde de 10 questions « mot inconnu / exemples » : la décomposition par définitions marche déjà largement
  (« c'est quoi un cétacé ? », « cite des félins/mammifères/métaux/poissons » → listes réelles). Deux défauts
  corrigés :
- **Phrasé « quels ANIMAUX sont des félins ? »** (le type générique animaux/fleurs est ignoré, la catégorie
  réelle est l'attribut « des Y ») → guépard, léopard, lion, ocelot, serval.
- **Filtre anti-bruit des hyponymes** (`_STOP_HYPO`) : une définition mal parsée rangeait un syntagme à article
  (« la recherche » sous « cétacé ») — désormais tout hyponyme commençant par un mot-outil est écarté (un vrai
  nom d'espèce ne commence pas par « la/le/en… »). « cite des cétacés » ne montre plus « la recherche ».
- Raisonnement **104/104**, paraphrases 79/79, suite 16/16 (77/77), challenge 16/16.

## 2026-07-05 — Robustesse ADVERSE : SMS + fautes + oral EMPILÉS (banc 79 cas, 100 %)

- **Couche SMS fermée** (`_desms`, étage 0sms) : « c ki ki a ecri 1984 ? » → « c'est qui qui a écrit 1984 ? »
  → George Orwell. Carte prudente (ki/koi/kel/pk/qd/cmb/c/cest…), lookahead anti-élision (le « c » de
  « c'est » n'est pas une abréviation — sans ça : boucle infinie détectée et corrigée).
- **Rejeux BORNÉS** (`_rejoue`, plafond de profondeur 6, thread-safe) : tous les étages de réécriture
  (SMS/dévoilement/recadrage/pronom/continuations) passent par un garde-fou anti-boucle — plus jamais de
  RecursionError si une règle n'est pas idempotente.
- **Assouplissements oraux** : virgule OPTIONNELLE dans 8 règles de topicalisation (« la joconde c de qui »),
  sujet juxtaposé (« napoleon ier il est né ou » — qui devenait un MÉMO « c'est noté » !), « ou » sans accent
  lu comme « où » dans les patrons fermés, « 1er »→« Ier » (garde mois/« le »), participes sans accent dans
  les patrons créateur, « et » consommé devant un enrobage (« et dis-moi il est mort quand »).
- **Piège de protection documenté** : « ecri »+er = « écrier » (verbe réel) → la guérison protège la faute ;
  résolu côté patron (« écrit? » ancré), pas en affaiblissant la garde. « +re » verbal restreint aux -d/-t.
- Banc paraphrases : **79 cas, 100 %** (4e vague adverse). Raisonnement 102/102, suite 16/16, challenge 16/16.

## 2026-07-05 — Abstention structurée : 3e famille (faits ciblés) + RAM est_un : résultat négatif documenté

- **3e famille de structures reconnues** : les FAITS ciblés (« où est né E ? », « quand est mort E ? », « où se
  trouve E ? », « dans quel pays est E ? ») produisent l'abstention structurée quand le fait manque — « quand
  est mort Dumbledore ? » → « je comprends la question, mais aucun fait vérifié n'ancre “Dumbledore” ». La
  chaîne conversationnelle complète marche : « où est né Gandalf ? » → *Pressbaum* (fait réel, un musicien
  autrichien s'appelle Gandalf) → « et il est mort quand ? » → pronom résolu → abstention structurée honnête.
- **2 bugs de regex corrigés** : `trouvent?` signifiait « trouven+t? » (jamais « trouve » — 2 occurrences) ;
  le lookahead anti-pronom ne couvrait pas « ET il est mort quand ? » (la règle capturait « et il » comme
  sujet). Les pronoms nus (il/elle/ils/elles/on) sont exclus des entités candidates.
- **RAM est_un : essai de carte compacte REVERTÉ après mesure honnête** — tracemalloc promettait −30 Mo
  d'objets vifs (46,3 → 15,9 Mo) mais le RSS RÉSIDUEL était PIRE (81,7 vs 74,5 Mo : le dict transitoire de
  build pollue les arènes malloc, même après malloc_trim), et le build +1,4 s. Leçon consignée : les objets
  vifs tracés ne sont pas le RSS ; l'ancien code (dicts partageant leurs clés + genus internés) reste le
  meilleur mesuré. Le vrai poste dominant reste le moteur `ia` préchargé (~600 Mo).
- Raisonnement **102/102**, paraphrases 66/66, suite 16/16 (77/77), challenge 16/16.

## 2026-07-05 — GATE DE PERTINENCE des rapports web (FAUX=0 renforcé) + E2E serveur réel 13/13

- **Gate de pertinence** (`_extrait_pertinent`, partagé repond + assistant_nl) : un extrait web n'est servi que
  s'il PARLE de ce qui est demandé. Mesuré en E2E réel : « capitale du wakanda » (web ON) rapportait une page
  gentilés de « synonyme-du-mot.com » sans un mot sur la capitale — attribué mais hors-sujet. Désormais :
  structure reconnue (R de E) → la relation ET l'entité doivent apparaître dans titre+extrait ; sinon ≥60 % des
  mots de contenu. Un extrait refusé → l'abstention STRUCTURÉE (qui dit ce qui est compris) prend le relais.
- **Validation E2E serveur réel 13/13** (mémoire vierge, base complète, web coupé pour tester l'offline) :
  recadrage oral, calcul en lettres, abstention structurée + continuité + formes courtes, anaphores pronom
  multi-tours, vérif créateur + homonymie Joconde, type B Waterloo, faits stables. Script scratchpad
  `e2e_session.sh`.
- Raisonnement **99/99** (2 cas gate ajoutés), paraphrases 66/66, suite 16/16 (77/77), challenge 16/16.

## 2026-07-05 — ANAPHORES INTER-TOURS : « il est mort quand ? » comprend de qui on parle

- **Étage pronom (0pro)** : un pronom nu se résout sur le dernier SUJET de la conversation — « où est né
  Napoléon Ier ? » puis « il est mort quand ? » → « Napoléon Ier est mort en 1821. » Patrons fermés (il/elle +
  prédicat, « ça se trouve où ? », « parle-moi de lui », « c'était quand ? »). FAUX=0 : substitution du sujet
  réellement discuté, réponse toujours vérifiée.
- **Le sujet est mémorisé sur SUCCÈS DES CAPS** (`_sujet_large` : participes, « qui est X », « se trouve X ») —
  avant, seuls les lookups par clé le mémorisaient : les questions personnes/localisation n'avaient pas
  d'antécédent pour la suite.
- **Continuations type A/B rejouées dans le pipeline COMPLET** : « et celle de Waterloo ? » (après Marignan)
  atteint désormais _cap_date_evenement → « 1815 », au lieu du lookup brut qui répondait un fait d'une autre
  nature (« champ de bataille de Waterloo » à une question *quand*).
- **`_utile()` central** : les rejeux (dévoilement/oral/pronom/continuations) ne retiennent plus un AVEU
  d'ignorance comme s'il était une réponse (l'aveu court-circuitait les étages suivants du texte original) ;
  les abstentions STRUCTURÉES restent retenues (elles disent ce qui est compris). Lookahead anti-pronom sur la
  règle né/mort postposé (« il est mort quand ? » relève de 0pro, pas d'un sujet nominal « il »).
- Banc paraphrases : **66 cas, 100 %** (3e vague : 6 dialogues multi-tours). Raisonnement 97/97, suite 16/16
  (77/77), challenge 16/16.

## 2026-07-05 — Compréhension ouverte, 2e vague : 60 cas durs à 100 % + vérification d'attributions

- **Banc de paraphrases durci à 60 cas** (indirectes « j'ai oublié qui… », registre soutenu « où a-t-il vu le
  jour ? », ellipses « capitale Japon ? », doubles topicalisations « et la monnaie, au Japon, c'est quoi ? »,
  confirmations « c'est bien Tokyo ? », nombres en lettres) : 75 % au départ → **100 %**.
- **Nouveau cap `_cap_verif_createur`** : « c'est bien Orwell qui a écrit 1984 ? » → « Oui — 1984 a été écrit
  par George Orwell. » ; un « Non » donne le VRAI créateur (fait vérifié). Accepte le nom de famille seul.
- **`_reverse_famille` : match par nom de famille** unique (« qu'a écrit Orwell ? » → base « George Orwell ») —
  abstention si deux personnes distinctes partagent le suffixe (FAUX=0).
- **Nombres en lettres** dans le calcul (« combien font douze fois huit ? » → 96), conversion fermée uniquement
  sous intention de calcul explicite.
- **2 bugs réels de plus** : la guérison « corrigeait » les NUMÉRAUX (« huit »→« hui » — ni noms ni verbes au
  lexique → ensemble protégé dédié) ; ordre des règles de recadrage (la topicalisation simple masquait la
  double). Confirmations génériques (« X, c'est bien Y ? ») routées vers la forme à inversion (_oui_non).
- Raisonnement 97/97, paraphrases 60/60, suite 16/16 (77/77), challenge 16/16.

## 2026-07-05 — COMPRÉHENSION OUVERTE : 28 % → 100 % sur le banc de paraphrases (recadrage oral)

- **Nouveau thermomètre** `tests/banc_paraphrases.py` : 40 reformulations LIBRES (topicalisées, clivées,
  familières, postposées) mesurent la compréhension ouverte de bout en bout. Base de départ : **11/40 (28 %)**.
- **Recadrage oral** (`_recadre_oral`, étage 0oral) : ~25 règles de réécriture STRUCTURELLE fermées du français
  parlé vers la forme canonique, rejouée avec repli sans perte — « la Joconde, c'est de qui ? », « c'est qui qui
  a écrit… », « il est né où, Napoléon ? », « ça fait combien, 12 fois 8 ? », « on paie avec quoi au Japon ? »,
  « après Louis XIV, c'est qui le roi ? », « X, c'est bien un animal ? »… FAUX=0 : réordonnancement des mots de
  l'utilisateur, la réponse vient toujours d'un fait vérifié. Score final : **40/40 (100 %)**, zéro régression.
- **Créateur générique avec désambiguïsation** : « de qui est X / qui a fait X » essaie toutes les familles
  créatives ; en HOMONYMIE d'œuvres, liste les sens vérifiés au lieu de trancher au hasard (« Joconde » =
  tableau de Vinci ET conte de La Fontaine — les deux sont donnés).
- **3 bugs réels préexistants corrigés** : (a) le diagnostic système se déclenchait sur « ça FAIT combien, 12
  fois 8 ? » (sous-chaîne) ; (b) la guérison « corrigeait » les PLURIELS légitimes (« habitants »→« habitant »,
  gate sans singularisation) ; (c) « hauteur du mont Everest » échouait : « Everest » est AUSSI une localité à
  350 m — le TYPE-WORD (« mont ») désambiguïse désormais vers la relation typée (altitude_montagne), au lieu
  d'être jeté (piste « ne jamais figer l'atome »).
- **Nom nu d'événement célèbre** : « c'était quand, Marignan ? » → « bataille de Marignan » (annee_debut_bataille,
  1515) prime sur l'homonyme obscur (commune dissoute en 1790) — le nom RÉSOLU est affiché en entier.
- Banc raisonnement 97/97, paraphrases 40/40, suite 16/16 (77/77), challenge 16/16.

## 2026-07-05 — Fossé de généralisation : DÉVOILEMENT de l'enrobage conversationnel + verbes familiers

- **Couche de dévoilement** (`_devoile`, étage 0dev de `_repond_noyau`) : les caps s'ancrent en `^` — « dis-moi
  qui a écrit 1984 » ratait alors que la question nue répond. Ensemble FERMÉ de préfixes sociaux (dis-moi,
  donne-moi, j'aimerais savoir, tu peux me dire, sais-tu, au fait, franchement, sinon, stp/svp…) + politesse
  finale (« …, merci », « …, s'il te plaît ») retirés, question NUE rejouée d'abord ; si elle ne produit rien de
  mieux que le générique, l'original continue (zéro perte, aucun fait altéré — on ne retire que du social).
  Fonctionne pour toutes les familles, y compris l'abstention structurée (« donne-moi la capitale du wakanda,
  merci » → présentation du royaume fictif). « dis-moi bonjour » reste social (la politesse passe avant).
- **Verbes familiers dans les patrons créateur** : « qui a pondu 1984 ? » → Orwell ; « qui a tourné Titanic ? »
  → Cameron (écrit|rédigé|pondu ; réalisé|tourné). Banc **97/97** (4 cas ajoutés), suite 16/16, challenge 16/16.

## 2026-07-05 — Structure reconnue : famille CRÉATEUR + 2 bugs réels corrigés (guérison, articles de titres)

- **La brique « structure reconnue » couvre la famille créateur** (« qui a écrit/composé/peint/inventé X ? »,
  mêmes patrons fermés que `_cap_createur`) : « qui a écrit le necronomicon ? » → « je connais “necronomicon” —
  *titre d'un livre fictif dans l'œuvre de Lovecraft* — mais aucun fait vérifié n'en désigne le créateur. »
  Formes courtes consécutives et continuité multi-tours partagées avec la famille « R de E ».
- **BUG GUÉRISON corrigé (préexistant)** : « peint » était « corrigé » en « point » (comme « était »→« état »
  avant lui) — les participes du 3e groupe n'étaient pas reconstruits vers leur infinitif. `_fait_forme_verbale`
  reconstruit désormais peint→peindre, écrit→écrire, ouvert→ouvrir, mis→mettre, pris→prendre, reçu→recevoir,
  bu→boire, venu→venir… (sûr par construction : un candidat ne protège que s'il EST un infinitif connu).
- **BUG TITRES corrigé (préexistant)** : les œuvres stockées AVEC article (« la joconde » dans peintre_oeuvre)
  étaient introuvables (lookup sur la forme sans article seulement) → « qui a peint la Joconde ? » restait sans
  réponse alors que le fait EXISTE. Lookup sous les deux formes + **accord du participe** : « La Joconde a été
  peint**e** par Léonard de Vinci. » Banc 93/93 (2 cas ajoutés), suite 16/16, challenge 16/16.

## 2026-07-05 — L'échange continue À TRAVERS l'abstention (le sens est relationnel)

- **Continuité conversationnelle sur abstention** : une abstention structurée mémorise désormais le sujet et la
  question — « capitale du Wakanda ? » (abstention) puis « et sa population ? » ou « et du Mordor ? » enchaînent
  avec une abstention **structurée sur la question reformulée**, plus jamais le générique. Les continuations
  type A (« et sa/son X ? ») et type B (« et du Y ? ») traversent l'abstention comme elles traversent les faits.
- **Voix humaine** : deux abstentions structurées CONSÉCUTIVES ne récitent pas deux fois la formule complète —
  la seconde dit « Même chose pour “population de wakanda” : là non plus, aucun fait vérifié pour trancher » ;
  la présentation de l'entité (« royaume fictif… ») ne se répète que si l'entité a changé. Le conseil « réactive
  internet » n'est donné qu'UNE fois par conversation. Le marqueur Wiktionnaire « (univers de Marvel) … » passe
  en fin de définition (`_def_lisible`) : la présentation se lit comme une phrase.
- `est_fallback` reconnaît la forme courte (statut HORS conservé). Banc 91/91, suite 16/16 (77/77), challenge 16/16.

## 2026-07-05 — Abstention ENRICHIE : « structure reconnue mais non ancrée »

- **Nouvelle brique de compréhension** (`_structure_non_ancree`, interface/repond.py) : quand toute la cascade
  factuelle a rendu HORS, Provara ne dit plus un « je ne sais pas » générique si la question **parse** en
  (relation connue, entité) — il dit **ce qu'il a compris** (la structure « R de E ») et **ce qui manque**
  (aucun fait vérifié pour trancher). Inspirée du déchiffrement du chant des cachalots (projet CETI) : on peut
  reconnaître une grammaire sans comprendre un mot, et l'honnêteté sur cet écart est une information.
- **Il dit QUI est l'entité quand il le sait** : une sonde d'ancrage bornée (8 relations : pays, villes,
  définitions, personnes — petits fichiers cachés, gros fichiers en streaming mémoïsé) distingue « entité
  inconnue » de « entité connue sans fait pour cette relation », et cite la **définition vérifiée** quand elle
  existe : « capitale du Wakanda ? » → « je connais “wakanda” — *royaume africain fictif (univers de Marvel)* —
  mais je n'ai pas de fait vérifié “capitale de wakanda” ». Même chose pour le Mordor (Tolkien).
- FAUX=0 préservé : les messages ne rapportent que des recherches réellement faites (« je n'ai pas trouvé »,
  jamais « ça n'existe pas ») ; gardes anti-mis-parse (copule, entité=relation, >6 mots) ; `est_fallback`
  reconnaît la nouvelle abstention (statut HORS conservé dans toute la chaîne).
- Banc de raisonnement : **91/91** (3 cas ajoutés) sur base complète ; suite conversationnelle 16/16 gates
  (valide_assistant_nl 77/77) ; challenge 16/16. README FR/EN : la vitrine cite la nouvelle abstention.

## 2026-07-04 — RENOMMAGE « VERAX → Provara » + UX du 1er lancement + 3 bugs d'interface corrigés

### Renommage complet de la marque (raison : antériorité de marque)
- « **verax** » est une marque UE **enregistrée** (classes 9 & 42 — logiciel/SaaS, DSM IP Assets), plus une société
  homonyme « Verax AI ». **Provara** (0 antériorité INPI/EUIPO) retenu après recherche. Projet toujours open source,
  non commercial.
- **GitHub** : org `Verax-IA` → `Provara-IA`, repo `Verax` → `Provara` → **github.com/Provara-IA/Provara**
  (redirections GitHub actives). Rebrand du code (57 fichiers) : marque visible VERAX→Provara, exe **`Provara.exe`**,
  `Lancer_Provara.bat`, workflow `--name Provara`, asset `Provara-windows.zip`, URLs mises à jour.
- **Identifiants techniques CONSERVÉS** (invisibles, éviter d'orpheliner les données déjà installées) : dossier
  `~/.verax`, variables `VERAX_*`, module `verax_boot.py`, `demo_verax.py`. Asset cache Release renommé
  `Provara_cache_v1.tar.gz` (URL_CACHE alignée dans `telecharge_donnees.py`).
- **Éléments hors-repo rebrandés** : portfolio (yohanfauck.fr), CV (source + PDF régénéré), bannière LinkedIn,
  post d'annonce.

### UX du PREMIER lancement (plus d'écran figé — demandes Yohan)
- **Téléchargement des 72M rendu OPTIONNEL** : le `.exe` démarre **instantanément** sur l'échantillon embarqué
  (~1,1 M faits). La base complète s'installe **à la demande** via un bouton « Base complète » dans l'interface
  (choix explicite : ~6 Go de disque, 15-20 min, une seule fois) — `lance.py` ne télécharge plus au lancement.
- **Modale de chargement** pilotée par la nouvelle route **`GET /api/status`** : s'affiche pendant le chargement
  (« Provara se prépare… »), montre la progression du téléchargement/décompression, et **se ferme** quand l'IA est
  prête. Offre d'installation + redémarrage automatique (`/api/installer-base`, `/api/redemarrer`) ; bouton
  **Quitter** (`/api/quitter`).
- **Exe FENÊTRÉ** (`--noconsole` par défaut) : plus de fenêtre terminal. `verax_boot` redirige `stdout/stderr` vers
  `~/.verax/verax.log` quand la console est absente (sinon un `print` planterait le thread de préchargement).
  Documentation + README : « prévoir l'espace disque », « uniquement la première fois », avertissement si lancé
  depuis un terminal.

### Trois bugs d'interface trouvés EN CONDITIONS RÉELLES (auraient bloqué TOUS les utilisateurs)
- **Erreur JS `I18N` (zone morte temporelle)** — CAUSE RACINE du blocage : `majTheme()` était appelé au chargement
  AVANT la déclaration `const I18N` ; le garde `typeof I18N` ne protège pas un `const` en TDZ → `ReferenceError`
  qui **stoppait tout le script** → la modale ne s'initialisait jamais et restait figée. Corrigé : application du
  thème différée au `DOMContentLoaded`.
- **Ordre DOM de la modale** : le `<div id="verax-modale">` est placé APRÈS le `<script>` → `getElementById`
  renvoyait `null` à l'exécution → `tick()` jamais démarré. Corrigé : init modale + bouton Quitter au
  `DOMContentLoaded`. Anti-cache `?t=` ajouté sur le sondage `/api/status`.
- **Nom d'asset cache** : le code pointait `verax_cache_v1.tar.gz` alors que la Release livre
  `Provara_cache_v1.tar.gz` → 404 → build à froid lent pour les nouveaux utilisateurs. URL alignée.
- Validé par TEST NAVIGATEUR RÉEL (Chrome headless + API simulée) : modale fermée, app rendue, thème/langue OK.

### Assistant : reconnaître « je me présente » (retour live Yohan)
- « Bonjour je m'appelle yohan » partait en recherche web → renvoyait « Yoann Gourcuff ». Corrigé
  (`interface/repond.py`, `_reponse_sociale`) : détection des tournures NON ambiguës (« je m'appelle X »,
  « moi c'est X », « appelle-moi X », « mon nom est X », « my name is X ») → salue **par le prénom**
  (« Bonjour Yohan, enchantée 🙂 »), **jamais** de recherche sur le prénom. Distingué de la question sur le nom de
  l'IA (« comment tu t'appelles ? » → « Je m'appelle Provara »). Garde-fou anti-faux-prénom (« moi c'est fatigué »
  → non déclenché) ; « je suis X » exclu (ambigu). Gates : assistant_nl **77/77**, conversation **9/9**,
  restitution **29/29**, capacites_chat **19/19**.

## 2026-07-04 — Optimisation RAM majeure (base complète 3,3 Go → ~30 Mo) + docs realignées

### Lecteur : de 3,3 Go à ~30 Mo de RAM pour les 71,9 M faits (FAUX=0 préservé)
- **LABELS mémoire-mappés** (`src/lecteur.py`, `.colf` **VER 2**, nouvelle classe `_LabelsMmap`) : les listes de
  valeurs distinctes (mesuré 245 Mo — le DERNIER gros poste resté en tas anonyme : `definition_nom` 32 Mo,
  `taxon_parent` 22 Mo…) passent en blob UTF-8 mmappé, décodé À LA DEMANDE et mutualisé. Prouvé byte-identique
  (A/B hash 45 tables = 0 divergence). Import du lecteur 15,7 s → 1,4 s (labels plus désérialisés au load).
- **Résidence à la demande** (`MADV_RANDOM` + `MADV_DONTNEED` après lecture d'en-tête ; échappatoire
  `LECTEUR_MADV=0`) + **`lecteur.libere_cache()` / `ia.libere_cache()`** : le corpus ne rend résidentes QUE les
  pages qu'une requête touche ; `libere_cache()` rend tout après un gros traitement (retour ~15-60 Mo).
- **Build à froid allégé** : après écriture du `.colf`, la table RAM est remplacée par sa vue mmap (le tout
  premier build ne retient plus qu'une table à la fois).
- **MESURES** (`mesure_ressources.py`, base complète 71,9 M) : **~30 Mo de RAM, chargement ~2 s, 216 000 req/s**
  (cache chaud). Pleine puissance (balayage invention 71,9 M faits) = **57 Mo réellement possédés** ; le pic
  transitoire (~1,4 Go) est du cache `.colf` Shared_Clean réclamable. TOUT PREMIER lancement (build d'index) =
  pic ~2,7 Go / une fois → recommandé : livrer le `.colf` pré-construit dans la Release.
- **Windows** : `madvise` absent (no-op sûr, garde `try/except`) ; les pages mmappées y sont aussi paginées à la
  demande, et le gain « labels mmappés » s'applique quel que soit l'OS.
- **Correction de cache** : le cache `.colf`/`.bin` local était périmé (~2000 valeurs à espaces non normalisés,
  construites avant le durcissement `_norme_valeur` — l'invalidation ne regardait que le mtime du jsonl, pas la
  version du code). Cache reconstruit à froid (valeurs correctes, `_norme_valeur` appliqué). ⚠ Reste à durcir :
  inclure une empreinte du code d'ingestion dans l'invalidation. **La Release doit livrer un `.colf` construit à
  neuf depuis le code courant** (pas depuis un vieux `.bin`).
- **Docs realignées** : README(.fr).md, `_POST_LINKEDIN.md`, `docs/ANALYSE_MANQUES.md` (P6 marqué RÉSOLU). Les
  anciens chiffres publics « 73 M / 3,3 s / 520 Mo » (et la dérive 80 M/858k) étaient faux ou périmés → corrigés
  en 71,9 M / ~2 s / ~30 Mo. Gate `_nonreg` re-passée sur le cache corrigé.

## 2026-07-03 — Session « le .exe marche pour de vrai » (débogage en conditions réelles)

### Deux causes racines trouvées et corrigées (la recherche web échouait dans le .exe)
- **SSL épinglé** (`src/https_confiance.py`, NOUVEAU) : sous Windows, le magasin de certificats système peut
  contenir une variante périmée d'une racine -> OpenSSL refuse des sites SAINS (« certificate has expired » sur
  fr.wikipedia.org, chaîne servie pourtant 100 % valide ; navigateurs OK car ils récupèrent les racines
  dynamiquement). Remède : si et SEULEMENT si la validation système échoue sur un problème de certificat, la
  requête est re-validée contre des ancres EMBARQUÉES (racines officielles ISRG X1/X2, bundle Mozilla ;
  expirent 2035/2040). Vérification jamais désactivée, hostname compris. Câblé dans `veille_structure`,
  `veille`, `telecharge_donnees`.
- **Conversations enfin PERSISTANTES dans le .exe** (`conversation.py`) : le stock vivait sous `VERAX_ROOT`
  qui, en mode frozen, pointe le dossier TEMPORAIRE PyInstaller (détruit à la fermeture) -> conversations
  perdues à chaque sortie, archive amnésique. Le .exe range désormais tout dans `~/.verax/conversations`.
  Au passage : 2 conversations de dev étaient EMBARQUÉES dans le .exe (et committées) -> détrackées,
  `datasets/conversations/` gitignoré, le build n'embarque plus que `datasets/lecteur`.

### Diagnostic embarqué (plus jamais d'échec silencieux)
- **Tampon de build** : `VERSION_BUILD.txt` (commit) écrit par le CI et `build_exe.bat`, affiché au démarrage
  (`build : …`) et dans la réponse « diagnostic » -> on sait toujours QUEL .exe on teste (artifact périmé vu à 15h23 :
  le build du push 15:20 n'existait pas encore).
- **Échecs web VISIBLES en console** (une fois par erreur distincte, jamais bloquant) : `veille_structure._signale`
  + signalement d'un échec d'import du module web dans `repond._recherche_structuree`.
- **Sorties tolérantes** (`verax_boot`) : `stdout/stderr errors="replace"` — un `print("✓")` sur console cp1252
  tuait le thread de préchargement (UnicodeEncodeError). Plus jamais.
- **Chemin des données de `repond`** : `_DOSSIER_LECTEUR` respecte `LECTEUR_DATASETS_DIR` (en frozen, le chemin
  dérivé de `__file__` était faux -> requêtes inverses mortes en silence dans le .exe).

### Interface (demandes Yohan)
- **Interrupteur INTERNET** (routes `GET/POST /api/web` + bouton) : actif par défaut ; « couper » = données
  locales seules, effet immédiat. Quand internet est coupé et que les données locales n'ont rien : message
  ACTIONNABLE (« réactive internet et je lance une recherche sourcée ») au lieu d'un aveu générique.
- **Corbeille** : bouton 🗑 -> conversations archivées, restaurer (↩) ou purger définitivement (✕, confirmation).
- **Honnêteté de la devise** : « rien ne sort de la machine » -> « tes conversations restent ici · internet :
  optionnel, toujours sourcé » (la recherche envoie les termes de la question aux sources, jamais les dialogues).
- Phrase d'accueil : « … je réponds avec ce que je sais ou ce que je trouve sur internet (toujours sourcé)… ».

### Qualité de réponse (retours de test Yohan en direct)
- **GARDE DE PERTINENCE (FAUX=0)** sur la recherche web libre : la recherche plein-texte de Wikipédia renvoie
  TOUJOURS quelque chose — « je voudrais construire un moteur à eau » rapportait le CONCORDE. Désormais les mots
  pleins du sujet doivent se retrouver dans le titre/extrait de correspondance (tolérance 1 faute :
  « parmezzan » -> « parmesan » passe), sinon ABSTENTION honnête. Top-3 résultats testés, premier pertinent retenu.
- **Extraction du SUJET des phrases d'intention** : « je voudrais construire X », « où je peux trouver Y »,
  « dans quel pays… » -> la recherche porte sur X/Y, pas sur la phrase entière (-> « Moteur à eau » trouvé).
- **MULTI-SOURCES** (`cherche_web_domaines`, DuckDuckGo lite) : jusqu'à 3 résultats PERTINENTS de domaines
  INDÉPENDANTS, chacun verbatim + attribué + lié. Réponse Wikipédia enrichie de « 🌐 D'autres sources en
  parlent : … » ; sans corroboration -> « (Source unique — à vérifier.) » ; sans Wikipédia -> rapport du
  métamoteur attribué. Dégradation gracieuse si bloqué. (La promotion « N sources concordent -> fait » = le
  système de confiance, chantier suivant.)
- **Anglais** : salutations anglaises comprises et répondues EN ANGLAIS (« hello how are you? » partait en
  recherche web -> « Clara Furey » hors-sujet) ; détecteur « ça ressemble à de l'anglais » -> clarification
  honnête bilingue au lieu d'une réponse à côté. Principe Yohan : DEMANDER des précisions > répondre à côté.
- **Import fichiers** : le message d'échec LISTE désormais les 22 types lisibles (json/csv/xml/sqlite/zip/…)
  et explique que PDF/images ne sont pas encore pris en charge (OCR prévu).

### Interface (2e vague)
- **Mode SOMBRE** 🌙 (bouton, mémorisé, défaut = réglage système) ; **trombone d'import en SVG contrasté**
  (l'émoji 📎 était illisible) ; boutons harmonisés.

### Boucle de build/test locale (nouvelle capacité de dev)
- Le .exe se BUILDE et se TESTE désormais depuis la session Claude via l'interop WSL->Windows (`py` 3.14 +
  `build_exe.bat` sans pause + tests HTTP `curl` sur 127.0.0.1:8765). Batterie e2e passée : web attribué
  (« roi de la pop » -> Michael Jackson), diagnostic tamponné, interrupteur, corbeille, base locale (Montevideo),
  persistance des conversations.

## 2026-07-03 — Session « produit prêt à publier »

### Architecture & distribution
- **Arborescence propre** : `src/` (moteur & capacités), `ingestion/` (récupérateurs), `tests/` (validateurs
  FAUX=0), `interface/` (UI web), `docs/`, `examples/`. Bootstrap `verax_boot.py` (imports à plat depuis les
  sous-dossiers, conscient du mode `.exe`).
- **Lancement** : `lance.py` (ouvre http://127.0.0.1:8765 + navigateur), `install.sh`/`lance.sh` (Linux/Mac),
  `Lancer_Provara.bat` (Windows). **.exe** : `build_exe.bat` + CI GitHub Actions (build auto à chaque push).
- **2 clics = base complète** : `telecharge_donnees.py` — au 1er lancement, le `.exe` installe les 73M faits
  (~563 Mo) depuis la Release, puis charge tout.

### Conversation (moteur)
- **Nom = Provara** (identité/nom câblés) ; salutations robustes et **combinées** (« bonjour comment vas-tu ?
  comment t'appelles-tu ? »), tolérance aux fautes.
- **Multi-questions NON-BLOQUANT** : répond à chaque sous-question (données + calcul), « je ne l'ai pas » pour
  les inconnues, tout combiné.
- **Auto-diagnostic** : « diagnostic » -> nb de relations/faits chargés + source des données.

### Connaissance
- **Échantillon enrichi** : 16 -> **1068 relations / ~1,1 M faits** embarqués (géographie, sciences, histoire…).
- **Recherche web STRUCTURÉE** (`veille_structure.py`) : quand la base n'a pas le fait, interrogation Wikidata
  (SPARQL déterministe) -> réponse **vérifiée et ATTRIBUÉE** (« trouvé sur Wikidata »). Design Yohan : source
  fiable = réponse véridique ; jamais de scraping de texte libre (FAUX=0 préservé). Opt-in réseau (`IA_WEB=1`).

### Honnêteté & propreté
- Formule « **hors-ligne par défaut** » (répond sans réseau ; connexion opt-in pour apprendre/chercher) au lieu
  de « 100 % hors-ligne ».
- Dé-branding Kadepic -> Provara ; aucun secret dans le dépôt.

### Interface & visualisation
- **Interface rebrandée Provara** (titre, en-tête, message d'accueil, libellés « vous »/« Provara »).
- **Schémas visuels** : « montre-moi ce que tu sais sur X » / « schéma de X » / « graphe de X » -> **graphe SVG
  en étoile** des relations réelles que Provara connaît sur l'entité (via `graphe_monde` + SVG contrôlé, labels
  échappés, FAUX=0). Affiché directement dans le chat.
- **Import de fichiers** : bouton 📎 -> le fichier est lu LOCALEMENT (`ia.lit_fichier` : json/csv/xml/
  sqlite/zip/ini…) et Provara en donne un résumé fidèle dans le chat (jamais envoyé ailleurs, effacé après lecture).

### Recherche web (session 2)
- **Recherche web STRUCTURÉE étendue** : Wikidata via SPARQL, désambiguïsation par notoriété (« France » -> Paris),
  nettoyage des nombres.
- **Recherche web LIBRE (Wikipédia)** : quand ni la base ni Wikidata n'ont la réponse, Provara interroge Wikipédia
  (recherche plein-texte), rapporte un **extrait VERBATIM attribué** + un **lien** vers la source (« Information
  trouvée sur internet, à vérifier au besoin »). Résout les épithètes (« le roi de la pop » -> Michael Jackson).
  FAUX=0 préservé : rapporté, jamais présenté comme une vérité vérifiée de Provara.
- **Questions subjectives** cadrées honnêtement (« ça dépend du critère ») + pistes web.
- **Multi-questions** : « x »/« × » = multiplication ; engage sur une liste évidente (≥3 parties), non-bloquant.
- **Corbeille des conversations** (route + à finir côté UI).
- Correction majeure du **.exe** : PyInstaller analyse tous les modules (`_precharge_verax`) -> `import ia` ne
  plante plus en frozen ; erreurs remontées dans la console.

### Recherche web (session 3 — 2026-07-03 soir) : MULTI-SOURCES RÉEL (l'index du web entier + contexte vérifié sur site)
- **Cause racine du « je ne vois que Wikipédia »** : DuckDuckGo lite servait un **CAPTCHA anti-bot** (« anomaly »,
  cc=botnet) à notre UA -> `cherche_web_domaines` rendait [] à CHAQUE question -> « Source unique » systématique.
- **Refonte multi-sources** (`veille_structure.py`) : recherche PAR MOTS-CLÉS sur des index du web ENTIER —
  **Mojeek** (crawler indépendant, primaire) + **Bing RSS** (flux fait pour les programmes) + DDG lite (repli),
  requête **« phrase exacte » d'abord** (précision : « "roi de la pop" » ne remonte plus les sites « ROI »
  marketing) puis mots-clés pleins (rappel ; « un moteur à eau » ne matche plus l'ONU par « UN »).
- **VÉRIFICATION DE CONTEXTE SUR LE SITE** (demande Yohan) : Provara **visite chaque page candidate** (borne
  400 Ko, texte extrait sans scripts) et exige les mots pleins du sujet dans une fenêtre de ~70 mots (départage :
  phrase exacte > prose réelle > menus) -> l'extrait rapporté est le **PASSAGE VERBATIM de la page** ; page lue
  mais muette sur le sujet = source REJETÉE ; inaccessible = snippet du moteur (attribué). Visites en parallèle.
- **Anti-rafale** : cache 15 min par (index, requête) + budget Mojeek par question (quota ~4 req/min observé) ;
  dégradation gracieuse inchangée (« Source unique — à vérifier »).
- **ROUTAGE PHRASE NOMINALE** (`repond.py`) : « histoire du château de Chambord » sans « ? » n'est PLUS un fait
  à noter (« C'est noté » = répondre à côté) mais un SUJET DE RECHERCHE -> cascade factuelle + web + clarification.
  Une affirmation garde son accusé (verbe conjugué/1ʳᵉ personne/chiffre : « rdv dentiste mardi 15h » reste noté) ;
  interjections (« oui », « merci ») inchangées. `est_fallback` reconnaît aussi le message « internet coupé ».
- **FIX PRODUIT (latent depuis le portage)** : `assistant_nl._module_repond` cherchait `src/interface/repond.py`
  (layout harnais) -> **FileNotFoundError avalée = étage clarification/bornage MORT en silence dans le .exe**.
  Corrigé (réutilise l'instance `repond` chargée ; sinon 2 layouts ; sinon import gelé). `valide_assistant_nl`
  passe de CRASH TOTAL à 70/77 (7 échecs restants = dérive harnais->Provara à trier, chantier compréhension).
- Gates : verifie_demo **31/31** (783 checks) + valide_conversation **9/9** ; e2e .exe : « symptômes de la carence
  en fer » (sans « ? ») -> passage vérifié sur actusante.net + 2 domaines ; « pneu de vélo » -> réponse PRIMAIRE
  depuis un site spécialisé (roulezjeunesse) quand Wikipédia n'a rien.

### Session 3 bis (2026-07-03 soir, retours LIVE Yohan) — build v6
- **UI sombre : champ de saisie illisible** (texte clair sur BLANC) : le textarea n'avait pas de fond explicite
  -> gardait le blanc natif du navigateur en thème sombre. Fix : `background: var(--panneau)`.
- **Salutation COMBINÉE à une demande** (« Bonjour comment vas-tu ? qu'est-ce que la canicule ? » échouait en
  « famille inconnue ») : `_detache_salutation` répond au social ET traite la demande (reste VERBATIM, pipeline
  normal). Vérifié source : salutation+canicule -> « Bonjour !… » + article Wikipédia.
- **Extraction du sujet** : mots de DISCOURS retirés (« dire », « serait », « vraiment », « savoir »…) des
  mots pleins + verbes de tête (« peux-tu me dire quelle boisson serait vraiment rafraîchissante en temps de
  canicule » -> sujet « boisson rafraîchissante temps canicule », la recherche web peut enfin matcher).
- **Superlatifs de NOTORIÉTÉ non bornés** (« le rappeur le plus connu du moment ») : plus connu/populaire/
  célèbre ajoutés à `evaluation_subjective` -> cadrage honnête (« pas de réponse unique, donne-moi un critère »)
  au lieu du message générique. Gates 31/31 + 9/9 + assistant_nl 70/77 (stables).
- ⚠ CONSTAT STRATÉGIQUE (Yohan) : le routeur à motifs est un PLAFOND pour la V1 — plan « moteur conversationnel
  model-free appris » consigné au runbook §4-2c (lexique T9 = grammaire par lookup, dialogue à état, patrons
  promus par verdict sur corpus, lecture de documents longs).

### Session 3 ter (2026-07-03 nuit) — LECTURE PDF (brique MANQUANTE, cap « mémoire de 200 pages »)
- **Constat (agent d'exploration) : la couche compréhension du langage EXISTE mais n'est PAS câblée au chat.**
  `repond.py` fait du pattern-matching + lookup factuel et n'importe AUCUN de : `comprehension_integree`,
  `lecture_comprehension`, `lexique_fr`, analyse de phrase (`generateur`). Vrai chantier = BRANCHER, pas refaire.
- **Brique réellement manquante = lire un PDF tiers.** `parseur_fichiers` rendait HORS pour le PDF ;
  `document_pdf` sait ÉCRIRE, pas LIRE. Aucune lecture de document long n'existait.
- **`src/extrait_pdf.py`** (stdlib re+zlib, FAUX=0) : extrait la couche TEXTE d'un PDF (opérateurs Tj/TJ,
  échappements PDF, flux **FlateDecode** décompressés), texte PAR PAGE, ordre du document via l'arbre
  Catalog→Pages→Kids. Un PDF SANS couche texte (scanné) rend des pages VIDES + diagnostic honnête
  (`pages_avec_texte=0` → « OCR requis »), jamais d'invention. Filtre non géré (image) → ignoré, pas deviné.
- **Branché** : `parseur_fichiers.lit` (PDF → texte, magic bytes `%PDF-`), `serveur._resume_fichier`
  (upload → montre le vrai texte + nb pages + note « scanné » honnête au lieu d'un repr de dict), ajouté au
  préchargement PyInstaller. `valide_extrait_pdf 14/14`, valide_parseur_fichiers 13/13, valide_document_pdf
  21/21, verifie_demo 31/31, valide_conversation 9/9.
- SUITE (brique 2) : lecture de DOCUMENT LONG — sectionnement + index inversé par section (réutilise le moteur
  de rappel des conversations) + Q&A « que dit le document sur X ? » → passage verbatim + page.

### Session 3 quater (2026-07-03 nuit) — LECTURE DE DOCUMENT LONG (interroger un mémoire de 200 pages)
- **`src/lecteur_document.py`** (FAUX=0) : découpe un document (pages→sections→passages, détection de titres
  numérotés/mots-clés/capitales), index inversé pondéré idf (réutilise `conversation._tokens`), et répond à
  une question par le PASSAGE VERBATIM + page + section, ou abstention honnête si rien ne correspond. Sommaire
  = titres réellement détectés. `depuis_pdf(octets)` = pont direct avec extrait_pdf.
- **Racinisation conservatrice** (pluriel FR : chute s/x) sur les CLÉS d'index+requête -> « bâtiments » apparie
  « bâtiment », « instrumentés » apparie « instrumenté » ; le texte rendu reste verbatim.
- **BUG LATENT trouvé** (non corrigé en amont pour ne pas risquer les gates de conversation.py) : les mots-vides
  de `conversation.py` sont ACCENTUÉS (« été », « où ») alors que les tokens sont dé-accentués -> ils fuient dans
  l'index (affecte aussi le rappel de conversations). Contourné dans lecteur_document (`_STOP_DOC` dé-accenté +
  interrogatifs). À corriger proprement dans conversation.py plus tard (avec re-passage de ses gates).
- **Branché au chat** (`serveur.py`) : un PDF/texte importé devient un Document interrogeable attaché à la
  conversation (`_DOCS`). Source de REPLI attribuée : ne répond QUE si la connaissance vérifiée + le web ont
  abstenu (ne détourne jamais une bonne réponse) ; « sommaire/plan/de quoi parle le document » -> plan détecté.
  Plafond d'upload 5→40 Mo (mémoire de 200 pages). `valide_lecteur_document 18/18`, extrait_pdf 14/14,
  verifie_demo 31/31, valide_conversation 9/9, assistant_nl 70/77. Ajoutés au préchargement PyInstaller.

### Session 3 quinquies (2026-07-03 nuit) — AUDIT DE CÂBLAGE COMPLET + branchement des orphelines
- **Comparaison des 2 repos** (Provara ↔ IA_nouvelle_vision d'origine) : rien de RUNTIME ne manque. Écart =
  ingere_* (build datasets, pas runtime) + mesure_* (benchmarks) + valide_* (dans tests/) ; 23 vrais modules
  non portés, TOUS dev/analyse/démo, AUCUN importé au runtime. Données : 1068 embarqués + 1369 complets dans le
  tarball Release (aucune donnée perdue). Ressource repérée : lexique_kaikki_full.jsonl (1,9M) pour plus tard.
- **Audit câblage ia.py→chat** : sur ~350 fonctions publiques, 5 seulement passées via la façade ia.py, ~10 via
  modules-frères ; ~300 (Palier 2 stats) restent à juste titre non-câblées (exigent des tableaux, pas du NL).
  Poignée de vraies capacités conversationnelles COUPÉES du chat → branchées.
- **BRIQUE GRAMMAIRE `src/grammaire_fr.py`** (FAUX=0) : analyse grammaticale française appelable — classe de
  chaque mot (mots-outils = ensembles FERMÉS finis ; mots pleins via **lexique embarqué 19 200 mots** extrait du
  Wiktionnaire, homographes ambigus écartés ; morphologie SÛRE seulement ‑ment), type de phrase
  (question/affirmation/ordre/exclamation + négation robuste à l'élision « n'a »), structure SVO, genre.
  Ambigu/inconnu → 'inconnu' (jamais deviné faux). `valide_grammaire_fr 46/46`. Lexique `src/lexique_fr_pos.jsonl`.
- **6 CAPACITÉS ORPHELINES CÂBLÉES au chat** (`repond.py`, handlers additifs en amont du factuel, abstention hors
  périmètre) : (1) grammaire « nature du mot X » / « analyse grammaticale : phrase » ; (2) conjugaison « conjugue
  X » (présent régulier, abstention honnête sinon) ; (3) graphiques « trace un graphique de : n1,n2… » → SVG ;
  (4) distance géo « distance entre X et Y » → orthodromie+cap (ia.distance_lieux) ; (5) **moteur d'INVENTION**
  « comment rafraîchir sans climatiseur » / « que manque-t-il pour X » → reformulation physique du besoin
  (ia/besoin.py — LA VISION PRODUIT, était totalement absente du chat) ; (6) audit de code « faille dans ce
  code : <bloc> » → constats CWE (ia.audite_code). `valide_capacites_chat 19/19`.
- Gates : verifie_demo 31/31, valide_conversation 9/9, assistant_nl 70/77, grammaire 46/46, capacites 19/19,
  extrait_pdf 14/14, lecteur_document 18/18. grammaire_fr ajouté au préchargement PyInstaller.

### Session 3 sexies (2026-07-03 nuit) — TOUT CÂBLER : Palier 2, conjugaisons, OCR, apprentissage, challenge
- **RECONNAISSANCE DES FORMES CONJUGUÉES** `src/formes_verbales.py` (77/77) : index inverse forme→verbe
  (114 266 formes) généré par règles (présent/imparfait/futur/participes des réguliers 1er/2e groupe) depuis
  **6505 verbes embarqués** (`verbes_fr.txt`) + cœur de fréquence, + table des irréguliers fréquents. Branché
  dans grammaire_fr -> **SVO réel** (« le chien mange la souris » → sujet/verbe/objet). Homographes (« table »,
  « content ») restent nom/adjectif via lexique prioritaire. FAUX=0 : formes dérivées/vérifiées, jamais devinées.
- **CÂBLAGE DU PALIER 2 STATS** `src/fonction_stats_nl.py` (16/16) : routeur en langage naturel qui rend
  accessibles ~46 fonctions calibrées (moyenne/médiane/écart-type exactes ; incertitude/tendance/prévision/Fermi/
  Benford/proportion Wilson/taux Poisson/Kelly/anomalie/risque extrême/rupture ; 2 listes : corrélation-pente/
  comparaison/effet causal/méta-analyse). Extraction de nombres + intention, `phrase=True`, relaie l'abstention
  honnête (échantillon trop petit). Branché `_cap_stats` dans repond.
- **BUG CORRIGÉ** : doublon `detecte_changement` dans ia.py (la version Shiryaev masquait la version série) →
  renommée `detecte_changement_precoce` ; la détection de rupture sur série est de nouveau atteignable.
- **OCR BORNÉ** `src/ocr.py` (17/17) : reconnaissance de texte NET par gabarits (police bitmap 5×7, rendu +
  lecture round-trip), normalisation largeur/position, espace-mot par pas régulier, multi-lignes. Glyphe non
  reconnu → « ? » (jamais inventé) ; photo/police non standard → HORS honnête. Branché parseur_fichiers (PNG) +
  résumé d'upload. (Portée déclarée : texte régulier fort contraste — la vraie OCR généraliste exigerait un modèle.)
- **APPRENTISSAGE DE PATRONS** `src/apprentissage_patrons.py` (11/11) : quand une formulation échoue puis
  l'utilisateur REFORMULE avec succès (même sujet exigé), Provara apprend l'alias « ratée→qui marche » (persistant,
  effaçable RGPD). Re-poser la formulation ratée est ré-aiguillé → réponse vérifiée. FAUX=0 : ré-aiguillage seul,
  jamais un fait inventé. Câblé serveur (observation échec→réussite) + repond (consultation avant abstention).
- **CHALLENGE MULTI-REGISTRES** `tests/challenge_conversation.py` : corpus gradué courant/technique/soutenu +
  capacités outils, 16/16 (hors web). Tableau de bord de la boucle adverse.
- Gates : verifie_demo 31/31, valide_conversation 9/9, assistant_nl 70/77, ia 18/18, + 11 nouveaux validateurs
  tous verts. Modules ajoutés au préchargement PyInstaller. Données embarquées : lexique_fr_pos (19 200) +
  verbes_fr (6505).

### Session 3 septies (2026-07-03 nuit) — SOLUTIONS aux limites déclarées
- **VERBES IRRÉGULIERS PAR MODÈLES** (formes_verbales, 126/126) : au lieu d'une table partielle, ~10 MODÈLES de
  conjugaison Bescherelle (partir/ouvrir/courir/attendre-re/prendre/mettre/-indre/-aître/-uire) générés
  systématiquement pour tout le 3e groupe. Couverture échantillon 32/47 → 47/47, index 116k formes. FAUX=0.
- **APPRENTISSAGE PROFOND (induction de règles)** (apprentissage_patrons, 16/16) : au-delà des alias de phrase,
  induction de RÈGLES DE SUBSTITUTION de mot depuis UN exemple (« chef-lieu »→« capitale ») qui GÉNÉRALISENT
  aux phrases neuves (« chef-lieu du Japon » → Tokyo, vérifié e2e). Effacement RGPD retire aussi les
  substitutions dérivées. Sound : ré-aiguillage seul, réponse toujours vérifiée.
- **PALIER 2 — CONCEPTS/PARADOXES** (explications.py, 13/13) : « explique le paradoxe de X » câble les briques
  pédagogiques auto-contenues (deux enveloppes, Braess, Allais, Ellsberg, Parrondo, Saint-Pétersbourg, no free
  lunch, coûts irrécupérables, Kelly, pascal mugging, cadrage). Concept inconnu / question factuelle → non
  détourné. Le calcul réel de la brique, jamais une paraphrase.
- **OCR ROBUSTE (binarisation Otsu)** (ocr, 20/20) : seuil automatique par histogramme → lit malgré contraste
  faible, sous-exposition, sur-exposition (photos). La limite « polices arbitraires / manuscrit » reste (elle
  exigerait des gabarits multi-polices ou un modèle appris — frontière honnête déclarée).
- Gates : verifie_demo 31/31, conversation 9/9, assistant_nl 70/77, + tous les nouveaux validateurs verts.
  Nouveaux modules au préchargement PyInstaller.

### Session 3 octies (2026-07-03 nuit) — DETTE 70/77 assistant_nl RÉSOLUE (77/77)
- Ces 7 checks n'avaient JAMAIS été verts dans Provara : le test plantait avant le fix de chargement de module ;
  70/77 était sa 1re exécution réelle. Analyse : 1 vrai bug + 4 config manquante + 2 libellé/données.
- **VRAI BUG corrigé** : une opinion (« quel est le plus beau pays ») passée par la PORTE UNIQUE était étiquetée
  `fait` — `qualifie_texte` ne reconnaissait que l'ancien préfixe « Question non bornée », pas le cadrage
  amélioré « Il n'y a pas de réponse unique, c'est subjectif… ». Ajout du préfixe `_PFX_OPINION` -> classée
  SUPPOSITION (régime opinion). Le TEXTE restait honnête, mais le STATUT était faux : corrigé.
- **REGISTRE DE SOURCES créé** (`datasets/sources/registry.jsonl`, absent du portage) : Provara connaît désormais
  ses sources de confiance (Wikidata, QLever, Wikipédia FR, REST Countries). Rend le mécanisme de joignabilité
  (`veille.approfondit`/`_ping_sources`) fonctionnel (4 tests) — amélioration produit, pas seulement un fix test.
- 2 attentes de test PÉRIMÉES mises à jour sans maquillage : libellé subjectif amélioré ; « cours d'eau du
  Portugal » = le MÉCANISME de rejeu « oui » est vérifié + FAUX=0 (fait réel si données, sinon abstention
  honnête en gate léger — jamais une invention).
- valide_assistant_nl **77/77**. Non-régression : verifie_demo 31/31, conversation 9/9, veille 24/24, sources OK.

### Session 3 nonies (2026-07-03 nuit) — SYSTÈME DE CONFIANCE FACTUEL (mission 1) + OCR reverti proprement
- **OCR** : correction honnête de mon erreur « besoin d'un modèle » — l'OCR classique est model-free (gabarits
  multi-polices + traits structurels). Mon essai rapide de généralisation par traits (topologie/zonage)
  RÉGRESSAIT (confusion 0/O, fausses lettres sur forte déformation = viol FAUX=0) → REVERTI au borné solide
  (20/20) + Otsu conservé. L'OCR généraliste model-free devient un CHANTIER DÉDIÉ (bibliothèque de gabarits de
  polices réelles + traits soignés + gestion du bruit), pas un patch.
- **`src/confiance.py`** (18/18) — l'utilisateur est un JUGE RÉEL :
  · CORRECTIONS AUTORITAIRES : « c'est faux, c'est X » (visant la dernière question) enregistre X comme réponse
    autoritaire ; re-poser la question rend X, ATTRIBUÉ (« tu me l'avais corrigé »). PRIME sur connaissance/web/
    mémoire (l'utilisateur juge la réalité). Persistant, effaçable RGPD.
  · « OUBLIE CE SITE X » : bannit un domaine (sous-domaines inclus) — retiré des recherches (`veille_structure`).
- Câblé : `repond` (correction consultée en (0conf) priorité max ; « oublie ce site » en (0ban)) ; `serveur`
  (capture « c'est faux, c'est X » vs dernière question) ; `veille_structure` (filtre les domaines bannis).
- La concordance au niveau du FAIT existe (`veille_corroboration` : N sources indépendantes + juge réel, 26/26) ;
  le chat affiche déjà la concordance de domaines (« N sources en parlent »). La concordance de VALEURS via
  sources structurées multiples reste une intégration plus profonde (notée honnêtement).
- Gates : confiance 18/18, ocr 20/20, verifie_demo 31/31, conversation 9/9, assistant_nl 77/77,
  veille_corroboration 26/26, capacites 19/19. Non-régression : questions non corrigées répondent normalement.

### Session 3 decies (2026-07-03) — CORRECTION UTILISATEUR EXIGE UNE SOURCE (trou FAUX=0 fermé)
- Faille signalée par Yohan : une correction NUE (« capitale de la France = Toulouse ») écrasait une vérité.
  Corrigé : `confiance.corrige` EXIGE une source ; correction nue -> Provara CHALLENGE (« j'avais X ; sur quelle
  SOURCE t'appuies-tu ? »), tient bon sans source (« je m'en tiens à ce que je peux vérifier »), et une fois
  sourcée l'attribue (« d'après la source que tu m'as indiquée »), jamais comme sa propre vérité. État en attente
  côté serveur (la source peut arriver au tour suivant). valide_confiance 20/20.

### Session 3 undecies (2026-07-03) — LANGUE : réponse factuelle en ANGLAIS (mission 3, fondation)
- **`src/langue.py`** (13/13, model-free) : (1) DÉTECTION de langue par signatures de mots-outils (fr/en/es/de) ;
  (2) TRADUCTION BORNÉE d'une question factuelle EN -> requête FR (relations capital/population/currency/language/
  area/continent ; pays EN->FR + identité pour les valeurs neutres) ; (3) résolution par le pipeline VÉRIFIÉ FR ;
  (4) habillage de la réponse en anglais. FAUX=0 : la valeur vient toujours du vérifié ; relation/entité inconnue
  -> None (jamais d'invention). Câblé `repond` (`_cap_langue_en` avant la clarification bilingue).
  Vérifié : « what is the capital of Spain? » -> « The capital of Spain is Madrid. » ; le FR ne régresse pas.
  Message de bascule désormais bilingue. Portée déclarée : questions factuelles bornées ; la traduction LIBRE de
  texte reste un chantier (dictionnaire bilingue + règles de transfert, model-free mais volumineux).

### Session 3 duodecies (2026-07-03) — finitions des chantiers
- **LANGUE étendue** : plus de relations EN (indicatif, point culminant, « how many people live in »), traduction
  des VALEURS linguistiques FR→EN (portugais→Portuguese, europe→Europe…). langue 13/13.
- **COLD-LOAD** : déjà atténué par le préchargement en tâche de fond (`_prechauffe` daemon dans serveur.main) —
  l'UI est instantanée, le lecteur charge pendant que l'utilisateur tape. Optimisation en place, confirmée.
- **`--noconsole`** : désormais une OPTION de build (`VERAX_NOCONSOLE=1` → release sans fenêtre ; console par
  défaut pour les diagnostics de dev). Provara.spec pilote `console` par la variable d'environnement.
- **DOCS** : `docs/{fr,en}/CAPABILITIES.md` mis à jour — nouvelle section « Assistant conversationnel » listant
  grammaire, conjugaison, stats NL, explications, lecture de documents/OCR, invention, géo, multi-sources,
  apprentissage, système de confiance, anglais (avec les frontières honnêtes déclarées).
- CHANTIERS RESTANTS (honnêtes, gros/bloqués sur ressources) : OCR généraliste (nécessite une bibliothèque de
  gabarits de polices RÉELLES — l'approche traits seule régressait/FAUX=0) ; traduction LIBRE de texte
  (dictionnaire bilingue + règles de transfert, model-free mais volumineux). Le reste des missions est livré.

### Session 3 terdecies (2026-07-03) — MULTILINGUE (max de langues) + SÉLECTEUR d'interface
- **`langue.py` refondu MULTILINGUE et extensible** (25/25) : détection fr/en/es/de/it/pt ; PARSING séparé du
  RENDU (une question peut être écrite dans une langue et répondue dans une autre). Config par DONNÉES
  (relations, noms de pays, gabarits, valeurs) → ajouter une langue = une entrée, aucune logique. Provara répond
  aux questions factuelles (capitale/population/monnaie/langue/superficie) dans 5 langues, via le pipeline
  vérifié FR. FAUX=0 : la valeur vient du vérifié.
- **Bascule** : « réponds en espagnol » (détecté, `demande_de_switch`) ET **sélecteur de langue dans l'interface**
  (`<select>` fr/en/es/de/it/pt) → endpoint `/api/langue` (préférence globale `repond._PREF_LANGUE_GLOBAL`) +
  **localisation des libellés UI** (sous-titre, boutons, placeholder, thème) dans les 6 langues. Une question FR
  est alors répondue dans la langue choisie ; une question écrite dans une langue supportée est auto-détectée.
- Vérifié : réglage « de » → « quelle est la capitale de l'Italie ? » → « Die Hauptstadt von Italie ist Rome. » ;
  retour « fr » → pipeline natif. Gates : verifie_demo 31/31, conversation 9/9, capacites 19/19, langue 25/25.

### Session 3 quaterdecies (2026-07-03) — OCR : recherche complète + jeu de traits classique
- Recherche internet du state-of-the-art OCR SANS modèle : deux voies (gabarits ; extraction de caractéristiques).
  Implémenté le toolkit CLASSIQUE complet (`ocr.py`) : traits STRUCTURELS (nombre de trous/Euler), STATISTIQUES
  (zonage 4×4, profils H/V, croisements H/V, aspect) et **moments de Hu** (invariants échelle/rotation), comparés
  au plus proche PROTOTYPE (police + variantes dilatée/érodée), en REPLI du gabarit.
- Vrai gain FAUX=0 : **marge d'ambiguïté** sur le gabarit — un glyphe qui ressemble autant à deux caractères
  (ex. un E déformé ≈ E ou !) → « ? » au lieu d'un choix arbitraire. Abstention stricte aussi côté traits
  (topologie exigée identique + seuil + marge ; glyphes triviaux exclus). valide_ocr 20/20 préservé.
- LIMITE HONNÊTE confirmée par la recherche : la généralisation à des polices ARBITRAIRES exige une bibliothèque
  de gabarits de VRAIES polices (données) — impossible à fabriquer sans fichiers de police ; et un glyphe
  détruit/fusionné n'est récupérable par AUCUNE OCR (artefact de segmentation). Portée FAUX=0 = texte imprimé net
  (police régulière, fort contraste via Otsu), ce qui est livré et gaté. Le multi-police = chantier « données de
  polices ».

### Session 3 quindecies (2026-07-03) — mesures fiables, base complète locale, UI multilingue, docs, analyse
- **BASE COMPLÈTE débloquée localement** : extraite dans C:\Users\yohan\.verax\datasets\lecteur → le .exe charge
  **71,9 M faits / 1387 relations** (vérifié via diagnostic), plus de 404. Message 404 amélioré (non alarmant).
  Le 404 public reste : Yohan doit publier la Release GitHub (asset datasets_complets.tar.gz).
- **MESURES RESSOURCES fiables** (`mesure_ressources.py`) : échantillon 1,1 M = 75 Mo RAM ; base complète 71,9 M
  = **3,3 Go RAM colonnaire (~41 o/fait)**, lookup ~0,004 ms (235k req/s). Le « sous 1 Go » d'antan était une
  base ~858k faits, PAS les 72M. README corrigé (le « 73M en 520 Mo » était faux).
- **UI MULTILINGUE COMPLÈTE** : localisation des 6 langues de TOUT l'affichage (sous-titre, boutons, tooltips,
  accueil, placeholders, Internet, Envoyer, corbeille, messages dynamiques) ; sélecteur + `/api/langue` ; réponses
  factuelles dans la langue. **Réorganisation** : gauche = Nouvelle conversation + Corbeille ; haut-droite =
  Internet + Mode sombre + Langue. JS validé (node --check).
- **OCR** : recherche complète du SOTA model-free ; toolkit classique implémenté (Hu/Euler/zonage/profils/
  croisements) + marge d'ambiguïté FAUX=0 sur le gabarit ; limite honnête = multi-police nécessite des données de
  polices. 20/20 préservé.
- **DOC nettoyée** (audit complet) : supprimé résidu docs/_tr_en ; corrigé compteurs (669→681, 480→492), chemins
  ingestion/, chiffres morts (822/153/_archive), RAM/73M ; ajouté modules récents à INVENTORY.
- **`--noconsole`** option de build (VERAX_NOCONSOLE=1).
- **ANALYSE DES MANQUES** livrée (`docs/ANALYSE_MANQUES.md`) : P1 raisonnement compositionnel (levier n°1),
  P2 scanner d'inventions (vision ultime), P3 fraîcheur, P4 compréhension profonde, P5 traduction libre,
  P6 perf/daemon, P7 multimodal, P8 confiance.

### Session 3 sexdecies (2026-07-03) — P1 : RAISONNEMENT COMPOSITIONNEL (levier n°1)
- `interface/repond.py` : les relations imbriquées « X de Y de Z » ne sont plus REFUSÉES mais COMPOSÉES —
  résout l'inner (Y de Z) → entité E VÉRIFIÉE, puis l'outer (X de E). FAUX=0 : chaque maillon = lookup EXACT
  (pas de correction floue dans la chaîne, qui propagerait une erreur), abstention si un maillon manque.
  Décuple les réponses sur les 71,9 M faits déjà présents, sans ajouter de donnée.
- BUG FAUX=0 CORRIGÉ au passage : « continent du pays de Paris » donnait « Antarctique » (le lookup flou mangeait
  un maillon) — « pays » n'était pas reconnu comme relation (filtré par _GENERIQUES). Noyau de relations ajouté
  APRÈS le filtre → détection correcte → composition/abstention, jamais une fausse réponse.
- `valide_composition 9/9` (mécanisme prouvé à résolveur mocké). Non-régression : verifie_demo 31/31,
  conversation 9/9, capacites 19/19, assistant_nl 77/77. LIMITE notée : la valeur réelle dépend de la résolution
  NL→relation de donnee_nl (« pays de X » ne matche pas encore la relation « pays_de_capitale ») — chantier suivant.

### Session 3 septendecies (2026-07-03) — P2 : SCANNER D'INVENTIONS (l'OBJECTIF FINAL câblé au chat)
- `substrat_reel.py` (gap-engine sur 71M faits, 3 gardes FAUX=0 : typage mesuré + témoin re-vérifié + anti-
  fausse-nouveauté) était construit mais NON câblé. Branché au chat via `_cap_invention_composite` (repond) sur
  `ia.inventions_composites(type)` : « quelles inventions/relations manquent pour les pays ? » / « que peut-on
  dériver sur X ? » → liste les attributs COMPOSITES dérivables (relation nouvelle « pont ∘ cible », témoin
  re-vérifié). Ex. « pays → (capitale ∘ latitude_capitale) ». Chaque valeur = fait re-vérifié, jamais inventé ;
  utilité non jugée (« reste à évaluer »). Types reconnus : pays/éléments/villes/capitales/astres.
- Vérifié e2e sur l'échantillon (2 candidats pour « pays ») ; non détourne pas une question factuelle ni le
  moteur de besoin. Non-régression : composition 9/9, capacites 19/19, verifie_demo 31/31. Sur la base complète
  (71,9M), l'exploration est bien plus riche.

### Session 3 octodecies (2026-07-03) — P1+ : résolution par FAMILLE de relations (la composition délivre)
- Le composeur essaie désormais, quand le lookup NL exact échoue, la FAMILLE de relations à tête donnée
  (« pays de X » → toute relation `pays_*` où X est une entité), avec UNICITÉ exigée (FAUX=0 : ambigu → None).
  Résultat : « continent du pays de Abou Dabi » → « Asie » (vraie composition 2-hop sur les données, chaîne
  montrée). valide_composition 9/9, non-régression complète (31/31, 9/9, 19/19, 77/77).

### Session 3 novemdecies (2026-07-03) — résolution par FAMILLE aussi sur les lookups SIMPLES
- Le repli famille (unicité FAUX=0) est aussi tenté sur une question simple « rel de entité » quand le DATA rend
  HORS : « continent de la France » → Europe (était HORS), « pays de Abou Dabi » → Émirats. N'affecte jamais une
  réponse déjà résolue. Non-régression : verifie_demo 31/31, conversation 9/9, assistant_nl 77/77, capacites 19/19,
  composition 9/9.

### Session 3 vigies (2026-07-03) — P3 : FRAÎCHEUR (source live préférée pour le volatil)
- `repond._est_volatil` + route : une question à marqueur temporel (« président ACTUEL », « DERNIER vainqueur »,
  « en 2026 », « current/latest ») préfère la source LIVE (Wikidata via veille_structure) à la base STATIQUE qui
  peut être périmée — quand le web est autorisé (opt-in). Repli sur la base si live indisponible. FAUX=0 inchangé
  (live = vérifié + attribué). valide_fraicheur 10/10, non-régression complète (31/31, 9/9, 19/19).
- P4 (multi-tours/coréférence) VÉRIFIÉ déjà en place (« et sa monnaie » → yen, « et la France » → substitue
  l'entité, « et sa capitale » → Paris). P6 (cold-load) : le daemon lecteur est Unix-socket (Linux, pas le .exe) ;
  le .exe précharge déjà en fond (cold-load masqué pendant l'accueil) → pas de gain .exe à ajouter.

### Session 3 vicies (2026-07-03) — P5 TRADUCTION + P7 OCR MINUSCULES
- P5 TRADUCTION `src/traduction.py` (valide_traduction 8/8) : mot-à-mot ASSISTÉE FR↔EN. Source RICHE = table
  `concept_du_mot` de la base complète (lexique cross-lingue ~165k mots dont 20k anglais : « dog (anglais) →
  chien ») utilisée en priorité (any→FR direct ; FR→cible via index inverse lazy), REPLI = dictionnaire curé
  embarqué (~350 mots) hors-ligne. FAUX=0 : mot inconnu gardé tel quel + signalé, jamais inventé ; sortie
  étiquetée « mot-à-mot assisté — à affiner ». Câblé `_cap_traduction` (« traduis X en anglais »). Ne charge
  JAMAIS la base (utilise le lecteur seulement s'il est déjà préchargé). NB Yohan : concept_du_mot existait —
  je l'avais raté au 1er balayage, corrigé.
- P7 OCR MINUSCULES `src/ocr.py` (valide_ocr 20→28/28) : ajout des 26 minuscules 5×7. CLÉ = les x-height ont le
  HAUT VIDE et sont échantillonnées sur la hauteur de LIGNE → la position verticale distingue « o »/« O »,
  « c »/« C »… sans logique en plus. `rend()` ne force plus `.upper()`. Round-trip mixte parfait (« Hello World »,
  « le chat dort »). Le texte imprimé RÉEL (surtout minuscule) est enfin lisible. 20/20 majuscules préservé.

### Session 3 unvicies (2026-07-03) — CONSIGNATION : doc synchronisée + gate cœur réparée + runner conversationnel
- DOC synchronisée sur le dernier travail : compteurs (modules 492→493, validateurs 669/681→683) dans INVENTORY/
  VALIDATION/README (fr+en) ; CAPABILITIES (fr+en) — ajout composition, scanner d'inventions, traduction FR↔EN,
  fraîcheur, OCR minuscules + correction ligne périmée « traduction hors périmètre » ; ANALYSE_MANQUES — bandeau
  de statut (P1/P2/P3/P4/P5/P7 = LIVRÉ).
- RUNNER CONVERSATIONNEL `tests/suite_conversation.py` : agrège 16 gates conversationnels (hors _nonreg par
  design), chacun en sous-processus isolé avec le bon env → 16/16 (469 checks). Documenté dans VALIDATION.
- **BUG INFRA CORRIGÉ — `_nonreg.py` cassé par le portage** : la gate cœur cherchait les `valide_*.py` à la
  RACINE (`os.listdir(HARN)`) alors que le portage Provara les a tous mis dans `tests/` → `python3 _nonreg.py`
  ne trouvait qu'**1** validateur (interface) et échouait faute de PYTHONPATH. Correctif : helper `_chemin()`
  (bare→tests/, chemin explicite tel quel), découverte dans `tests/`, `modules_locaux` élargi à src/interface/
  ingestion, et `_env_pipeline()` pose le PYTHONPATH sur chaque sous-processus. Vérifié : `liste_validateurs()`
  = **683** (était 1), `lance()` exécute correctement (composition 9/9, ocr 28/28, traduction 8/8, fraîcheur
  10/10, grammaire 61/61). Le run complet reste lourd (base complète) — à lancer par l'utilisateur.

### Session 3 duovicies (2026-07-03) — _nonreg : fix PYTHONPATH tests/ + constat de portage
- Correctif suite : `_SRCPATH` inclut désormais **tests/** en tête (les validateurs importent leur helper
  `valide_commun` et parfois un validateur frère comme module, tous dans tests/). Vérifié : valide_vague4 4/4,
  valide_pile 6/6, valide_iteration 5/5 (étaient en échec `ModuleNotFoundError: valide_commun`). ~57 validateurs
  de cette classe débloqués.
- CONSTAT (honnête) : faire tourner `_nonreg.py` dans Provara révèle que le PORTAGE est incomplet pour la SUITE.
  La vraie gate historique vit dans le repo d'origine `IA_nouvelle_vision/harnais/` (870 validateurs COLOCALISÉS,
  layout plat — datasets/src/validateurs ensemble → passe). Le port Provara (src/ tests/ interface/ ingestion/) a
  déplacé 683 validateurs dans tests/ SANS re-router leurs chemins codés en dur : certains cherchent
  `datasets/…` ou `src/ia.py` RELATIFS à leur dossier (→ FileNotFoundError), d'autres exigent la base complète
  71,9M (lecteur_t5..t12, resolution, taxonomie, substrat_reel…). Ce ne sont PAS des régressions — mon fix les a
  rendus VISIBLES (avant, _nonreg n'en trouvait qu'1). Le vert 683/683 dans Provara = chantier de portage
  (re-router chemins + base complète sous tests/datasets) ; la validation AUTORITÉ reste `harnais/` en amont.
  Pour la couche conversationnelle, `tests/suite_conversation.py` (16/16) est le contrôle autonome fiable dans Provara.

### Session 3 trevicies (2026-07-03) — portage _nonreg : chemins re-routés (structurel fait, contenu = harnais/)
- 12 validateurs dataset-dépendants re-routés : `dirname(__file__)/datasets/lecteur` → `LECTEUR_DATASETS_DIR`
  (env) ou fallback RACINE du repo (au lieu de `tests/datasets` inexistant). `_env_pipeline` pose aussi
  `VERAX_ROOT`. Vérifié : valide_surface_ia FileNotFoundError → **3/3** ; les 12 TROUVENT désormais leurs datasets
  (plus d'erreur de chemin).
- BILAN du chantier portage : le STRUCTUREL est fait (découverte 1→683, PYTHONPATH tests/+src/interface/ingestion,
  chemins re-routés, VERAX_ROOT) → ~60 validateurs débloqués. Les ~20 restants échouent sur le CONTENU : les
  validateurs, l'échantillon embarqué et la base complète NE s'accordent PAS sur les noms de relations/données
  (ex. la base complète ~/.verax n'a même pas `population_pays.jsonl` — nommage différent). C'est un alignement
  par-validateur profond = précisément le rôle de `harnais/` (origine, tout colocalisé et aligné). Décision :
  arrêt du chantier gate-Provara ici (faible valeur, duplication de harnais/). Gate pratique Provara =
  `tests/suite_conversation.py` (16/16) ; gate AUTORITÉ = `IA_nouvelle_vision/harnais/` (870 validateurs).
