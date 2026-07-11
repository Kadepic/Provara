# REPRISE APRÈS /clear — 2026-07-12 (à coller dans la nouvelle session)

Repo : `/mnt/c/Users/yohan/Download/Provara`. `PYTHONPATH=src` pour toute gate isolée.
Commits atomiques `git commit --no-gpg-sign` — NE PAS `git push` (le release de Yohan pousse/merge).
Garde inviolable partout : **FAUX=0**, non-régression complète `_nonreg.py` **797/797** verte après chaque changement.

## CE QUI EST FAIT (nuit du 11→12, TOUT pushé/mergé)
Moteur d'invention : **+21 domaines (11→31), +21 lois dures (L8→L28)** dans `src/coherence_physique.py` + `src/besoin.py`.
État : **31 domaines, 28 lois**. `valide_besoin` **578/578**, `valide_coherence_physique` **398/398**, non-rég **797/797**.
Working tree propre. Détail : `CHANGELOG.md` + mémoire `project-ia-moteur-invention-carte`.
Patron d'exception mûri : une loi dure ne réfute un dépassement que si la spec DÉCLARE le régime standard via un flag
booléen (jamais sur absence d'info) → FAUX=0 partout.

## MANDAT (ordre décidé avec Yohan) : 1) fixer le cache de `_nonreg.py`, 2) attaquer la Phase 2.

### TÂCHE 1 — CORRIGER LE CACHE FROID de `_nonreg.py` (0/797 en cache → ~11 min/run)

**CAUSE RACINE (diagnostiquée, certaine).** `_nonreg.py` résout les `.py` des MODULES uniquement relativement à
`HARN` (racine) ou `tests/`, alors que les modules vivent dans `src/` (et `interface/`, `ingestion/`, `outils/`).
- `imports_directs(f)` fait `open(HARN/f)` → **OSError** pour tout module de `src/` → `except (OSError, SyntaxError):
  return set(), True` → **suspect=True** → propagé par `cloture()` à la clôture de CHAQUE validateur → les 797 sont
  dans `toujours` (toujours re-lancés), jamais cachés. VÉRIFIÉ : 797/797 suspect ; `src/atome.py` (aucun `__import__`)
  marqué suspect ; le détecteur voit « 755/756 modules à import dynamique » (faux — c'est l'OSError, pas `__import__`).
- `hash_fichiers` fait `open(HARN/f)` → OSError → hache `<absent>` pour tout module src → **fingerprint INSENSIBLE au
  contenu des modules src** (trou de soundness latent, aujourd'hui MASQUÉ par le suspect qui force le re-run).

**FIX — les DEUX ensemble** (fixer le suspect seul créerait un cache périmé : changer `besoin.py` n'invaliderait pas
ses dépendants). Ajouter un résolveur qui cherche un `.py` dans les vrais dossiers de modules (mêmes que
`modules_locaux()`), et l'utiliser pour l'`open` dans `imports_directs()` ET `hash_fichiers()`. Garder `_chemin()`
(validateurs → tests/ ou interface/) pour l'EXÉCUTION dans `lance()`.
```python
_MODDIRS = ("", "src", "interface", "ingestion", "outils", "tests")
def _chemin_fichier(f):
    """Résout un .py (validateur OU module) vers son chemin réel relatif à HARN."""
    if "/" in f or os.sep in f:
        return f
    for d in _MODDIRS:
        cand = os.path.join(d, f) if d else f
        if os.path.exists(os.path.join(HARN, cand)):
            return cand
    return f
```
- `imports_directs` : `chemin = os.path.join(HARN, _chemin_fichier(fichier))`.
- `hash_fichiers` : `with open(os.path.join(HARN, _chemin_fichier(f)), "rb") as fh:`.

**VALIDER LE FIX** (petit diagnostic + 3 runs) :
1. Le détecteur ne doit plus voir ~755 « imports dynamiques » ; `suspect` doit tomber à ~0 (ne rester que les modules
   à `__import__` VRAIMENT non-littéral — vérifier lesquels, ex. `moteur_invention`/`solveur_type`, et confirmer
   qu'ils sont légitimement dynamiques).
2. `python3 _nonreg.py` DEUX fois : 1er run ~complet (cache froid, format de fingerprint changé) ; 2e run doit afficher
   « ~797 en cache » et finir en SECONDES. **797/797 aux deux.**
3. SOUNDNESS : `touch src/besoin.py` puis relancer → SEULS les validateurs dont la clôture inclut `besoin.py` doivent
   re-tourner (les autres restent cachés). 797/797. (Prouve que le fingerprint est sensible ET que le cache est sound.)
4. Commit atomique du fix (`_nonreg.py` seul).

Snippet de diagnostic (compte suspect) :
```python
import importlib.util, os; HARN=os.getcwd()
s=importlib.util.spec_from_file_location("nr",os.path.join(HARN,"_nonreg.py")); nr=importlib.util.module_from_spec(s); s.loader.exec_module(nr)
loc=nr.modules_locaux(); ci={}; sus=[v for v in nr.liste_validateurs() if nr.cloture(v,loc,ci)[1]]
print("suspect:", len(sus), "/", len(nr.liste_validateurs()))
```

### TÂCHE 2 — PHASE 2 (les 3 axes) — Phase 1 déclarée ÉPUISÉE par Yohan

L'espace des lois DURES neuves et distinctes est saturé (restants = réutilisations de L1/L2/L3, ou bornes floues).
Câbler les 3 axes qui « ouvrent le champ des possibles » (cf. runbook `_REPRISE_MOTEUR_INVENTION.md` §PHASE 2 et
mémoire `project-ia-mandat-nuit-3-phases`) :
1. **Contrat d'atome UNIVERSEL** — faire de l'interface `atome` (borné=FAIT / non-borné=SUPPOSITION, jugé par la
   réalité) l'entrée/sortie de TOUTES les briques → composition typée et sûre. Cf. `src/atome.py`, mémoire
   `project-ia-contrat-atome-vision`.
2. **Blackboard / substrat partagé universel** — toute capacité lit/écrit une donnée commune (blackboard /
   `substrat_reel` / mémoire de conversation) au lieu de fils directs. Cf. `valide_blackboard`.
3. **Routeur multi-domaines** — muscler le méta-routeur / `capacites.py` / `solveur_type` pour COMPOSER plusieurs
   domaines-briques sur un même besoin (ex. data-center = thermique + stockage + calcul + communication sous 4 lois),
   proprement (PAS un maillage N×M — coût + bruit + casse FAUX=0/parcimonie).

Méthode : sonde → HORS → brique → held-out durci → non-reg ; l'orchestration co-évolue avec les briques. Une fois la
Phase 2 finie → Phase 3 (ingestion à l'échelle, mémoires `project-ia-ingestion-sources`, `project-ia-run-autonome-3j`).
