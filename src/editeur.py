"""
ÉDITEUR DE DÉPÔT — substrat DÉTERMINISTE de création/modification de fichiers, FAUX=0 (souverain, stdlib, offline).

VISION (demande Yohan) : « mon IA doit pouvoir modifier et créer des fichiers dans un repo, comme un agent de code ».
Décomposition selon le CONTRAT D'ATOME :
  • L'OPÉRATION de mutation (créer, remplacer un texte EXACT, écrire) est BORNÉE / déterministe : elle s'applique
    EXACTEMENT comme spécifié, ou elle ÉCHOUE honnêtement (ValueError) — JAMAIS une écriture au mauvais endroit,
    jamais un écrasement d'un contenu non lu, jamais un fichier tronqué. C'est le FAUX=0 au niveau du substrat.
  • QUOI écrire (le contenu, la justesse du changement) est le plus souvent NON-BORNÉ = SUPPOSITION : ce module ne
    juge PAS le contenu. La promotion « le changement est bon » revient à un JUGE RÉEL (tests/compilation via les
    exécuteurs, équivalence via refactor.py) — l'asymétrie du projet : proposer librement, promouvoir par la réalité.

DURCI contre une passe adversariale (workflow, 21 failles confirmées fermées). Toutes les mutations passent par un
DESCRIPTEUR DE DOSSIER PARENT (dir_fd) résolu et confiné UNE fois, puis des opérations relatives O_NOFOLLOW/O_EXCL :
le chemin vérifié == le chemin muté (pas de TOCTOU par ré-résolution de chaîne, pas de suivi de symlink).

GARANTIES (vérifiées en adverse par valide_editeur.py) :
  1. CONFINEMENT ATOMIQUE : parent résolu (realpath) + confiné + RE-confiné via /proc/self/fd après ouverture du
     dir_fd ; toute opération est relative à ce dir_fd. Évasion `..`/absolu/symlink (dossier ET fichier final) →
     ValueError, RIEN hors racine. Le composant final n'est JAMAIS suivi (O_NOFOLLOW ; symlink cible → refus).
  2. NON-ÉCRASEMENT ATOMIQUE : `cree` et `remplace(empreinte_attendue=None)` créent via O_CREAT|O_EXCL → EEXIST
     (toute entrée présente, y compris symlink/dossier via lstat) → ValueError, jamais d'écrasement à l'aveugle.
     `remplace`/`supprime` d'un fichier existant exigent l'EMPREINTE lue (verrou optimiste) ; verrou `flock` par
     dossier sérialise les mutations concurrentes DU MÊME OUTIL (modèle de menace : tâches parallèles de l'IA).
  3. ÉDITION EXACTE NON AMBIGUË : `edite` exige l'ancre présente et UNIQUE, y compris positionnellement (les ancres
     à AUTO-CHEVAUCHEMENT sont rejetées) ; sinon → ValueError, fichier INCHANGÉ. `previsualise_edition` applique
     EXACTEMENT les mêmes gardes (aperçu ⇔ édition).
  4. ATOMICITÉ + DURABILITÉ : écriture = tmp (même dossier, mode préservé) + fsync(tmp) + os.replace(dir_fd) +
     fsync(dossier) → jamais un fichier tronqué ; le mode/permissions d'un fichier édité est PRÉSERVÉ.
  5. APERÇU SANS EFFET : `previsualise_edition` rend le diff unifié SANS rien écrire.
  6. ABSTENTION HONNÊTE : contenu non-`str`, chemin invalide, fichier non-texte (utf-8), cible non-régulière, toute
     OSError inattendue → ValueError (l'appelant ne voit JAMAIS fuiter une exception OS).

Modèle de menace (honnête) : outil SOUVERAIN mono-utilisateur ; les courses couvertes sont celles des tâches
PARALLÈLES DE L'IA elle-même (dir_fd + O_NOFOLLOW + flock coopératif). Un processus TIERS non coopératif et hostile
sur le même FS sort du périmètre (exigerait un bac à sable OS). La durabilité fsync est best-effort sur 9p/drvfs.
"""
from __future__ import annotations

import difflib
import errno
import hashlib
import os
import stat
import tempfile

try:
    import fcntl                        # POSIX : flock par dossier
except ImportError:                     # Windows (.exe) — vécu 2026-07-09 : l'import en dur tuait cree_fichier/
    fcntl = None                        # edite_fichier (« façade outils 2 » rouge au diagnostic du .exe).

# MODE PORTABLE (Windows) : pas de dir_fd/O_NOFOLLOW/flock. Les GARANTIES FONCTIONNELLES restent identiques
# (confinement realpath, non-écrasement O_EXCL, ancre exacte, écriture atomique tmp+replace, refus des liens
# via lstat, verrou par dossier via msvcrt sur un fichier de verrou HORS dépôt) ; seules les protections
# TOCTOU kernel (inode épinglé par dir_fd) deviennent best-effort — cohérent avec le modèle de menace du
# module : outil souverain mono-utilisateur, un processus tiers hostile sort déjà du périmètre.
_DIRFD = (fcntl is not None and hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW")
          and os.open in os.supports_dir_fd)
_O_BIN = getattr(os, "O_BINARY", 0)     # Windows : IO binaire exact ; 0 ailleurs

_TAILLE = 1 << 16


def empreinte(contenu: str) -> str:
    """SHA-256 hexadécimal du contenu texte (utf-8). Verrou optimiste : identifie EXACTEMENT une version."""
    if not isinstance(contenu, str):
        raise ValueError("contenu : str attendu")
    return hashlib.sha256(contenu.encode("utf-8")).hexdigest()


def _lire_tout(fd: int) -> bytes:
    morceaux = []
    while True:
        b = os.read(fd, _TAILLE)
        if not b:
            return b"".join(morceaux)
        morceaux.append(b)


def _prepare_edition(contenu: str, ancien: str, nouveau: str, tous: bool):
    """Gardes COMMUNES à edite et previsualise (⇔). Renvoie (n_remplacements, nouveau_contenu) ou lève ValueError."""
    if not isinstance(ancien, str) or not isinstance(nouveau, str):
        raise ValueError("ancien/nouveau : str attendus")
    if ancien == "":
        raise ValueError("ancien : chaîne vide interdite (ancre ambiguë)")
    if ancien == nouveau:
        raise ValueError("ancien == nouveau : aucune modification")
    n = contenu.count(ancien)                                  # occurrences NON chevauchantes
    if n == 0:
        raise ValueError(f"ancre absente (aucun remplacement) : {ancien!r}")
    # positions CHEVAUCHANTES : « aa » dans « aaa » = 1 non-chevauchant mais 2 positions -> ambigu.
    pos, chevauche = 0, 0
    while True:
        i = contenu.find(ancien, pos)
        if i < 0:
            break
        chevauche += 1
        pos = i + 1
    if not tous:
        if n > 1:
            raise ValueError(f"ancre ambiguë ({n} occurrences) — préciser tous=True ou une ancre unique")
        if chevauche > 1:
            raise ValueError("ancre à auto-chevauchement (position ambiguë) — préciser une ancre unique")
        return 1, contenu.replace(ancien, nouveau, 1)
    return n, contenu.replace(ancien, nouveau)


class Depot:
    """Bac à sable d'un dépôt : toutes les opérations sont CONFINÉES à `racine` (chemin réel). Pur système de
    fichiers déterministe : aucune opération réseau, aucun `git` invoqué."""

    def __init__(self, racine: str):
        if not isinstance(racine, str) or not racine.strip():
            raise ValueError("racine : chemin non vide attendu")
        r = os.path.realpath(racine)
        if not os.path.isdir(r):
            raise ValueError(f"racine inexistante ou non-dossier : {racine!r}")
        self.racine = r

    # ── confinement ───────────────────────────────────────────────────────────────────────────────────────
    def _confine(self, chemin_reel: str) -> None:
        base = self.racine
        if chemin_reel != base and not chemin_reel.startswith(base + os.sep):
            raise ValueError(f"chemin hors du dépôt (évasion refusée) : {chemin_reel!r}")

    def _resout_parent(self, rel: str):
        """(chemin_parent_reel_confiné, basename) pour un chemin relatif. basename jamais '', '.', '..'."""
        if not isinstance(rel, str) or not rel.strip():
            raise ValueError("chemin relatif : str non vide attendu")
        if os.path.isabs(rel):
            raise ValueError(f"chemin relatif attendu (pas absolu) : {rel!r}")
        brut = os.path.join(self.racine, rel)
        base = os.path.basename(brut.rstrip(os.sep))
        if base in ("", ".", ".."):
            raise ValueError(f"nom de fichier invalide : {rel!r}")
        parent = os.path.realpath(os.path.dirname(brut))       # résout les symlinks des dossiers parents
        self._confine(parent)
        return parent, base

    def _ouvre_dir(self, parent: str, creer: bool = False) -> int:
        """Ouvre un dir_fd sur `parent` (déjà confiné en chaîne) et RE-confine via /proc/self/fd (l'inode ouvert
        est bien dans la racine, quel que soit un éventuel échange concurrent). O_NOFOLLOW : `parent` étant déjà
        realpath, pas un lien ; garde défensive. `creer` crée l'arborescence parente (confinée) si absente.
        PORTABLE (Windows) : un dossier ne s'ouvre pas en fd -> on ouvre un FICHIER DE VERROU hors dépôt
        (tempdir, nommé par empreinte du chemin parent : même parent -> même verrou) ; os.close() le libère."""
        if creer and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)                 # parent déjà confiné
        if not _DIRFD:
            if not os.path.isdir(parent):
                raise ValueError(f"dossier parent inexistant : {parent!r}")
            nom = "provara_verrou_" + hashlib.sha256(parent.encode("utf-8")).hexdigest()[:16]
            try:
                return os.open(os.path.join(tempfile.gettempdir(), nom), os.O_CREAT | os.O_RDWR | _O_BIN)
            except OSError as e:
                raise ValueError(f"ouverture du dossier impossible : {e.strerror}")
        try:
            dfd = os.open(parent, os.O_DIRECTORY | os.O_RDONLY | os.O_NOFOLLOW)
        except FileNotFoundError:
            raise ValueError(f"dossier parent inexistant : {parent!r}")
        except OSError as e:
            raise ValueError(f"ouverture du dossier impossible : {e.strerror}")
        try:
            reel = os.readlink(f"/proc/self/fd/{dfd}")          # inode réellement ouvert
            self._confine(reel)
        except OSError:
            pass                                                # /proc indisponible -> confinement chaîne déjà fait
        return dfd

    def _verrou(self, dfd: int) -> None:
        try:
            if _DIRFD:
                fcntl.flock(dfd, fcntl.LOCK_EX)                  # sérialise nos mutations concurrentes par dossier
            else:
                import msvcrt
                msvcrt.locking(dfd, msvcrt.LK_LOCK, 1)           # verrou 1 octet, libéré à la fermeture du fd
        except (OSError, ImportError):
            pass                                                # FS/hôte sans verrou -> best-effort (documenté)

    def _refuse_lien(self, dfd: int, parent: str, base: str, rel: str) -> None:
        try:
            st = (os.lstat(base, dir_fd=dfd) if _DIRFD else os.lstat(os.path.join(parent, base)))
        except FileNotFoundError:
            return                                              # absent -> traité en aval
        if stat.S_ISLNK(st.st_mode):
            raise ValueError(f"la cible est un lien symbolique (refusé) : {rel!r}")

    def _lit_fd(self, dfd: int, parent: str, base: str, rel: str, obligatoire: bool):
        """Lit le fichier régulier via dir_fd + O_NOFOLLOW (portable : chemin joint + refus lstat du lien)."""
        try:
            if _DIRFD:
                fd = os.open(base, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dfd)
            else:
                self._refuse_lien(dfd, parent, base, rel)       # pas d'O_NOFOLLOW -> refus AVANT ouverture
                fd = os.open(os.path.join(parent, base), os.O_RDONLY | _O_BIN)
        except FileNotFoundError:
            if obligatoire:
                raise ValueError(f"fichier inexistant : {rel!r}")
            return None
        except OSError as e:
            if e.errno == errno.ELOOP:
                raise ValueError(f"la cible est un lien symbolique (refusé) : {rel!r}")
            raise ValueError(f"lecture impossible ({rel!r}) : {e.strerror}")
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise ValueError(f"pas un fichier régulier : {rel!r}")
            octets = _lire_tout(fd)
        finally:
            os.close(fd)
        try:
            return octets.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"fichier non-texte (utf-8 invalide) : {rel!r}")

    def _ecrit_atomique(self, dfd: int, parent: str, base: str, contenu: str, mode: int | None) -> None:
        """tmp (même dossier, mode préservé) -> fsync -> os.replace(dir_fd) -> fsync(dossier). Jamais tronqué."""
        fd, tmp = tempfile.mkstemp(dir=parent, suffix=".tmp")
        tmpbase = os.path.basename(tmp)
        try:
            if mode is not None:
                try:
                    os.chmod(tmp, mode & 0o777)                 # préserve les permissions (best-effort : drvfs/9p sans perms Unix)
                except OSError:
                    pass
            with os.fdopen(fd, "wb") as fh:
                fh.write(contenu.encode("utf-8"))
                fh.flush()
                os.fsync(fh.fileno())
            if _DIRFD:
                os.replace(tmpbase, base, src_dir_fd=dfd, dst_dir_fd=dfd)
            else:
                os.replace(tmp, os.path.join(parent, base))     # atomique sur même volume (NTFS inclus)
        except BaseException:
            try:
                os.unlink(tmpbase, dir_fd=dfd) if _DIRFD else os.unlink(tmp)
            except OSError:
                pass
            raise
        if _DIRFD:
            try:
                os.fsync(dfd)                                   # durabilité du renommage (best-effort 9p/drvfs)
            except OSError:
                pass

    # ── API publique ──────────────────────────────────────────────────────────────────────────────────────
    def chemin_absolu(self, rel: str) -> str:
        """Chemin absolu SÛR (confiné) d'un chemin relatif ; ne touche pas le disque."""
        parent, base = self._resout_parent(rel)
        return os.path.join(parent, base)

    def existe(self, rel: str) -> bool:
        """True si un FICHIER RÉGULIER existe à ce chemin (ne suit pas les liens)."""
        parent, base = self._resout_parent(rel)
        dfd = self._ouvre_dir(parent)
        try:
            st = (os.lstat(base, dir_fd=dfd) if _DIRFD else os.lstat(os.path.join(parent, base)))
            return stat.S_ISREG(st.st_mode)
        except FileNotFoundError:
            return False
        finally:
            os.close(dfd)

    def lit(self, rel: str):
        """(contenu, empreinte) du fichier régulier, ou (None, None) s'il n'existe pas. Non-texte/lien → ValueError."""
        parent, base = self._resout_parent(rel)
        try:
            dfd = self._ouvre_dir(parent)
        except ValueError:
            return (None, None)                                 # dossier parent absent -> fichier absent
        try:
            c = self._lit_fd(dfd, parent, base, rel, obligatoire=False)
            return (c, empreinte(c)) if c is not None else (None, None)
        finally:
            os.close(dfd)

    def cree(self, rel: str, contenu: str) -> str:
        """Crée un NOUVEAU fichier (O_CREAT|O_EXCL : échoue si une entrée existe déjà, sans jamais l'écraser).
        Crée les dossiers parents dans le dépôt. Écriture fsync. Renvoie le chemin absolu."""
        if not isinstance(contenu, str):
            raise ValueError("contenu : str attendu")
        parent, base = self._resout_parent(rel)
        dfd = self._ouvre_dir(parent, creer=True)
        try:
            self._verrou(dfd)
            try:
                if _DIRFD:
                    fd = os.open(base, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o644, dir_fd=dfd)
                else:
                    # O_EXCL refuse TOUTE entrée existante (fichier, dossier, lien) : non-écrasement identique.
                    fd = os.open(os.path.join(parent, base), os.O_CREAT | os.O_EXCL | os.O_WRONLY | _O_BIN, 0o644)
            except FileExistsError:
                raise ValueError(f"le fichier existe déjà (utiliser edite/remplace) : {rel!r}")
            except OSError as e:
                raise ValueError(f"création impossible ({rel!r}) : {e.strerror}")
            try:
                with os.fdopen(fd, "wb") as fh:
                    fh.write(contenu.encode("utf-8"))
                    fh.flush()
                    os.fsync(fh.fileno())
            except BaseException:
                try:
                    os.unlink(base, dir_fd=dfd) if _DIRFD else os.unlink(os.path.join(parent, base))
                except OSError:
                    pass
                raise
            if _DIRFD:
                try:
                    os.fsync(dfd)
                except OSError:
                    pass
            return os.path.join(parent, base)
        finally:
            os.close(dfd)

    def edite(self, rel: str, ancien: str, nouveau: str, *, tous: bool = False) -> int:
        """Remplace le texte EXACT `ancien` par `nouveau`. Ancre absente / ambiguë (multiple ou auto-chevauchante,
        sans `tous`) → ValueError, fichier INCHANGÉ. Ne suit jamais un lien. Renvoie le nombre de remplacements."""
        parent, base = self._resout_parent(rel)
        dfd = self._ouvre_dir(parent)
        try:
            self._verrou(dfd)
            self._refuse_lien(dfd, parent, base, rel)
            contenu = self._lit_fd(dfd, parent, base, rel, obligatoire=True)
            n, neuf = _prepare_edition(contenu, ancien, nouveau, tous)
            mode = (os.stat(base, dir_fd=dfd, follow_symlinks=False) if _DIRFD
                    else os.lstat(os.path.join(parent, base))).st_mode
            self._ecrit_atomique(dfd, parent, base, neuf, mode)
            return n
        finally:
            os.close(dfd)

    def remplace(self, rel: str, contenu: str, *, empreinte_attendue) -> str:
        """Réécrit TOUT le fichier si son empreinte actuelle == `empreinte_attendue` (verrou optimiste : jamais un
        contenu modifié depuis sa lecture). `empreinte_attendue=None` ⇒ le fichier doit être ABSENT (⇔ cree)."""
        if not isinstance(contenu, str):
            raise ValueError("contenu : str attendu")
        if empreinte_attendue is None:
            return self.cree(rel, contenu)                      # création atomique O_EXCL (refuse toute entrée)
        parent, base = self._resout_parent(rel)
        dfd = self._ouvre_dir(parent)
        try:
            self._verrou(dfd)
            self._refuse_lien(dfd, parent, base, rel)
            actuel = self._lit_fd(dfd, parent, base, rel, obligatoire=True)
            if empreinte(actuel) != empreinte_attendue:
                raise ValueError("empreinte périmée (le fichier a changé depuis sa lecture) — relire avant d'écrire")
            mode = (os.stat(base, dir_fd=dfd, follow_symlinks=False) if _DIRFD
                    else os.lstat(os.path.join(parent, base))).st_mode
            self._ecrit_atomique(dfd, parent, base, contenu, mode)
            return os.path.join(parent, base)
        finally:
            os.close(dfd)

    def supprime(self, rel: str, *, empreinte_attendue) -> None:
        """Supprime le fichier si son empreinte == `empreinte_attendue` (jamais un fichier non lu/modifié/lien)."""
        parent, base = self._resout_parent(rel)
        dfd = self._ouvre_dir(parent)
        try:
            self._verrou(dfd)
            self._refuse_lien(dfd, parent, base, rel)
            actuel = self._lit_fd(dfd, parent, base, rel, obligatoire=True)
            if empreinte(actuel) != empreinte_attendue:
                raise ValueError("empreinte périmée — relire avant de supprimer")
            os.unlink(base, dir_fd=dfd) if _DIRFD else os.unlink(os.path.join(parent, base))
            if _DIRFD:
                try:
                    os.fsync(dfd)
                except OSError:
                    pass
        finally:
            os.close(dfd)

    def previsualise_edition(self, rel: str, ancien: str, nouveau: str, *, tous: bool = False) -> str:
        """Diff unifié de ce que ferait `edite`, SANS rien écrire — MÊMES gardes qu'`edite` (ancre présente+unique,
        ancien≠nouveau) → ValueError si l'édition serait invalide. Proposer puis JUGER avant d'agir."""
        parent, base = self._resout_parent(rel)
        dfd = self._ouvre_dir(parent)
        try:
            self._refuse_lien(dfd, parent, base, rel)
            contenu = self._lit_fd(dfd, parent, base, rel, obligatoire=True)
            _, neuf = _prepare_edition(contenu, ancien, nouveau, tous)
        finally:
            os.close(dfd)
        diff = difflib.unified_diff(contenu.splitlines(keepends=True), neuf.splitlines(keepends=True),
                                    fromfile=f"a/{rel}", tofile=f"b/{rel}")
        return "".join(diff)

    def liste(self, sous_dossier: str = "") -> list[str]:
        """Liste RÉCURSIVE triée (relative à la racine) des fichiers réguliers du dépôt (ou d'un sous-dossier
        confiné). Sous-dossier inexistant / non-dossier → ValueError. Ne suit pas les liens."""
        if sous_dossier:
            parent, base = self._resout_parent(sous_dossier)
            base_dir = os.path.realpath(os.path.join(parent, base))
            self._confine(base_dir)
        else:
            base_dir = self.racine
        if not os.path.isdir(base_dir):
            raise ValueError(f"sous-dossier inexistant ou non-dossier : {sous_dossier!r}")
        out = []
        for dossier, _, fichiers in os.walk(base_dir, followlinks=False):
            for f in fichiers:
                out.append(os.path.relpath(os.path.join(dossier, f), self.racine))
        return sorted(out)
