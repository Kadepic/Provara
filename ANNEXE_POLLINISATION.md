# ANNEXE — Pollinisation croisée des briques (analyse, AUCUN câblage fait — GO Yohan requis)

> Base : graphe d'imports mesuré + fiches moteurs du 2026-07-09. Classement par levier estimé.
> Principe retenu (vision Yohan) : moteurs séparés, communicants, capables d'invoquer n'importe quelle
> fonctionnalité au besoin, voire de se COMBINER éphémèrement — pensée machine, jugée au résultat.

## Greffes à haut levier (candidates, à juger une par une par la réalité)

1. **JUGE → CONVERSATION (contestation)** : quand l'utilisateur dit « c'est faux », invoquer ancres +
   corroboration multi-domaines (veille_corroboration) et rendre une PREUVE structurée — aujourd'hui le
   chat rappelle le fait mais ne compose pas la machinerie de preuve complète.
2. **solveur_type / means-end → resout_math NL** : les problèmes à étapes (trains qui se croisent, heures
   d'arrivée) sont servis par des regex dédiées ; le solveur means-end (qui bat la force brute, cf. CAP LE
   COMMENT) les généraliserait — moins de motifs, plus de puissance.
3. **Briques calibration P2 (38 briques, ~430 checks) → réponses non-bornées du chat** : baliser chaque
   supposition d'un niveau de confiance CALIBRÉ (elles existent, câblées dans ia.py, mais le chat ne les
   invoque pas pour qualifier ses propres réponses).
4. **moteur_invention → questions procédurales (« comment faire X »)** : assemble_invention/candidats-stacks
   pourrait répondre AVANT ou AVEC le web — aujourd'hui l'invention n'est atteignable que par des formulations
   dédiées.
5. **prefiltre (predict-then-fallback) → routage conversationnel** : pré-jauger en-process les routes du tronc
   avant de sonder les étages (activation parcimonieuse ; moins d'appels à froid, cap < 100 partout).
6. **veille_corroboration → quiz/challenge** : questions de quiz corroborées multi-domaines + affirmations de
   l'utilisateur jugées avec le pipeline complet de corroboration (pas seulement la base).
7. **memoire_briques/ACT-R → routeur** : le rappel activé par contexte pourrait prioriser les capacités
   récemment utiles dans la conversation (le séquenceur apprend par acte ; la mémoire ACT-R affinerait).
8. **correction_ortho → entités partout** : le « parmezzan→parmesan » vécu ; l'orthographe tolérante est dans
   le pipeline repond mais pas systématique sur TOUTES les résolutions d'entités (reverse, quiz, fichiers).

## L'étage au-dessus (vision fusion éphémère)

**PLANIFICATEUR DE COMPOSITION** : au-dessus du routage par acte, un étage qui, pour un besoin donné, compose
un pipeline ad hoc de moteurs ({INVENTION propose → JUGE exécute/simule → SAVOIR ancre → CALIBRATION qualifie})
et le dissout après. Les briques existent TOUTES ; c'est l'orchestration dynamique qui manque. Candidat naturel :
généraliser `sequenceur` (qui apprend déjà des politiques par acte) en composeur multi-moteurs jugé au résultat.
