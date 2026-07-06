# Outils E2E — tests exhaustifs

- `couverture_atomique.py N` — génère des questions depuis les 1369 relations (N paires/relation), teste end-to-end
  en processus (source + base complète), rapport de couverture par famille + relations à 0%.
  `LECTEUR_DATASETS_DIR=/mnt/c/Users/yohan/.verax/datasets/lecteur python3 tests/e2e_exe/couverture_atomique.py 3`
- `e2e_massif.py` — 88 questions multi-domaines (curl.exe contre le .exe réel port 8765).
- `e2e_complexite.py` — composition N-sauts + compréhension longue + mémoire massive (en processus).
- `e2e_session3.sh` — E2E .exe des dernières briques (curl.exe).

PROTOCOLE .exe : serveur Windows sur 127.0.0.1:8765 injoignable directement du WSL -> `/mnt/c/Windows/system32/curl.exe`.
Couper le web : POST /api/web {"actif":false}. Mémoire propre : rm /mnt/c/Users/yohan/.verax/conversations/*.
PROTOCOLE source (rapide, code le plus récent) : en processus, LECTEUR_DATASETS_DIR = base complète.

⚠ PIÈGES de harness (appris en réel) :
- MÉMOIRE : les injections doivent passer par `serveur.ajoute_message(mem, cid, texte)` — `repond()` seul
  n'INDEXE pas le message (un harness qui l'appelle directement mesure 0/N à tort).
- SERVEUR SOURCE : `PORT=8899 LECTEUR_DATASETS_DIR=… python3 interface/serveur.py` (VERAX_ROOT vers un dossier
  jetable pour ne pas toucher la vraie mémoire) ; joignable en `curl` NATIF depuis WSL (contrairement au .exe).
- Un processus lancé depuis WSL sur le côté Windows (interop, schtasks) MEURT avec la session WSL : pour
  laisser le .exe tourner, c'est un lancement Windows natif qu'il faut (double-clic / session utilisateur).
