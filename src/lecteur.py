"""
LECTEUR GÉNÉRIQUE DE DONNÉES — le moteur du borné DATA (chantier #3 ; 566 sujets : faits/conventions/
constantes mesurées). Cf. `couverture_borne.py` (voies MESURE/FAIT/REFERENTIEL) et REPRISE.MD §#3.

POURQUOI un lecteur, pas une brique de calcul : pour un FAIT passé, une CONVENTION ou une CONSTANTE
mesurée, la réalité FIXE la réponse mais l'IA ne peut pas la DÉDUIRE — la deviner serait halluciner.
La brique auto-constructible est donc le LECTEUR d'un référentiel, JAMAIS le contenu : répondre =
LIRE une source vérifiée, sinon (HORS, None) honnête. C'est exactement le même contrat sound que
`base_faits`/`references`/`regle`, généralisé en UN point d'entrée + une INGESTION de table en lot.

CE QUE CE MODULE AJOUTE (sans refaire l'existant — il le COMPOSE) :
  • `ingere_table(relation, lignes, categorie, source)` — ingestion GÉNÉRIQUE d'une table vérifiable
    (entité -> valeur). INTÉGRITÉ D'UNE SOURCE AUTORITATIVE : une valeur DIVERGENTE pour une clé déjà
    présente -> ValueError (refus, pas d'écrasement silencieux), à l'image de `regle.Referentiel.apprend`.
    Réingérer la MÊME valeur est idempotent. Clé/valeur vide -> ignorée (jamais stockée). C'est ce que
    `memoire_faits.retient` NE fait pas (lui RÉVISE en gardant l'historique : bon pour l'actualité datée,
    mauvais pour une table figée comme le tableau périodique où une divergence = une erreur de données).
  • `cherche/repond(relation, entite)` — lookup EXACT sur les tables ingérées, REPLI sur l'amorce figée
    `base_faits` (les deux corpus se complètent sans collision : relations distinctes).
  • `repond_nl(question)` — quelques gabarits NL pour les tables ingérées, REPLI COMPLET sur
    `base_faits.repond_nl` -> jamais une régression de couverture, jamais une invention.

SOUNDNESS (FAUX=0, structurel) : présent+vérifié -> Fait complet (valeur+catégorie+source) ; absent ou
hors-gabarit -> (HORS, None). Aucune dérivation probabiliste. Les tables d'amorce sont des données
EXACTES et SOURCÉES (calendrier grégorien/ISO-8601 ; numéros atomiques IUPAC) — transcription d'un
référentiel connu, comme `physique.py` transcrit CODATA ; ce n'est pas de l'invention.
"""
from __future__ import annotations

from base_faits import (VERIFIE, HORS, Fait, normalise, _sans_articles,
                        CAT_PHYSIQUE, CAT_CONVENTION,
                        cherche as _cherche_base, repond_nl as _repond_base)
import re
import os
import sys
import json
import array
import bisect
import marshal
import tempfile
import mmap
import struct

_CATS_OK = {CAT_PHYSIQUE, "passe", CAT_CONVENTION}


class _Cles:
    """Séquence TRIÉE des clés d'une table, stockées DÉ-OBJETISÉES : un SEUL blob `str` (les clés
    concaténées, dans l'ordre) + un `array` d'offsets. Élimine l'overhead de ≈49 o/objet `str` que coûte
    une `list[str]` (sur des millions de clés uniques = des centaines de Mo). Les clés normalisées sont
    PUREMENT ASCII (cf. `base_faits.normalise` : NFD + suppression des marques + `[^a-z0-9 ]`), donc 1 o/car
    dans le blob compact CPython et offsets en unités de CARACTÈRES == octets. Expose `__len__`/`__getitem__`
    -> utilisable tel quel par `bisect` (boucle en C, slices `str` transitoires comparées en C)."""

    __slots__ = ("_blob", "_off")

    def __init__(self, blob: str, off):
        self._blob = blob        # clés triées concaténées (ascii) en UN objet str
        self._off = off          # array.array('I'/'Q'), longueur n+1 : clé i = blob[off[i]:off[i+1]]

    def __len__(self):
        return len(self._off) - 1

    def __getitem__(self, i):
        o = self._off
        return self._blob[o[i]:o[i + 1]]

    def __iter__(self):
        blob, o = self._blob, self._off
        for i in range(len(o) - 1):
            yield blob[o[i]:o[i + 1]]


class _ColTable:
    """Vue MAPPING figée et COMPACTE d'une table MONO-SOURCE (relation -> Fait), produite par
    `Lecteur.gele()`. Remplace le `dict[str, Fait]` (≈72 o/entrée : table de hachage + pointeur Fait +
    objet `str` de clé) par des COLONNES bien plus légères :
      • `_keys`   : `_Cles` — clés triées en blob+offsets (cf. ci-dessus) -> lookup `bisect` O(log n),
                    SANS objet str par clé (le gros poste sur les tables de noms de personnes).
      • `_codes`  : array.array('H' 2 o / 'I' 4 o) — code entier de la valeur de chaque fait (1 code/fait).
      • `_labels` : list des valeurs DISTINCTES de la table -> `_codes[i]` indexe `_labels`. La catégorie
                    et la source sont CONSTANTES par table (d'où « mono-source ») et stockées UNE fois.
    Les `Fait` sont reconstruits À LA VOLÉE et MUTUALISÉS par code (`_cache`) : on ne paie qu'un objet
    Fait par valeur distincte, comme l'ancienne mutualisation de `ingere_table`. RÉPONSES IDENTIQUES,
    moins de RAM. API LECTURE SEULE compatible dict (get/__getitem__/__contains__/items/values/keys/len/
    iter) pour ne RIEN casser des consommateurs qui lisent `LECTEUR.tables[rel]` comme un dict."""

    __slots__ = ("_keys", "_codes", "_labels", "_cat", "_src", "_cache")

    def __init__(self, keys: "_Cles", codes, labels, cat, src):
        self._keys = keys        # _Cles (blob+offsets), TRIÉE
        self._codes = codes      # array.array, aligné sur _keys
        self._labels = labels    # list[str] des valeurs distinctes
        self._cat = cat
        self._src = src
        self._cache: dict[int, Fait] = {}   # code -> Fait (mutualisé, paresseux)

    def _fait(self, code: int) -> Fait:
        f = self._cache.get(code)
        if f is None:
            f = self._cache[code] = Fait(self._labels[code], self._cat, self._src)
        return f

    def get(self, cle, defaut=None):
        keys = self._keys
        i = bisect.bisect_left(keys, cle)
        if i < len(keys) and keys[i] == cle:
            return self._fait(self._codes[i])
        return defaut

    def __getitem__(self, cle):
        f = self.get(cle)
        if f is None:
            raise KeyError(cle)
        return f

    def __contains__(self, cle):
        keys = self._keys
        i = bisect.bisect_left(keys, cle)
        return i < len(keys) and keys[i] == cle

    def __len__(self):
        return len(self._keys)

    def __iter__(self):
        return iter(self._keys)

    def keys(self):
        return iter(self._keys)

    def values(self):
        f = self._fait
        return (f(c) for c in self._codes)

    def items(self):
        f = self._fait
        return ((k, f(c)) for k, c in zip(self._keys, self._codes))

    def to_dict(self) -> dict:
        """Reconstitue le dict {clé: Fait} (dé-gel). Utilisé seulement si on doit RÉ-INGÉRER une table
        déjà figée (chemin froid, hors hot path) : `ingere_table` exige un dict mutable pour le contrôle
        conflit/idempotence. Rien ne l'appelle dans le chemin chaud."""
        f = self._fait
        return {k: f(c) for k, c in zip(self._keys, self._codes)}


class _ClesMmap:
    """Comme `_Cles` mais adossé à un buffer MMAP read-only (octets), pas un objet `str` privé. Le blob et les
    offsets vivent dans le fichier `.colf` mappé -> pages PARTAGÉES entre process + RÉCLAMABLES (page-cache).
    Clés normalisées = ASCII pur -> octets latin-1 1:1, ordre identique à `str` -> `bisect` inchangé.
    `__getitem__` renvoie des OCTETS (chemin bisect, comparés à la clé requête encodée) ; `__iter__` renvoie
    des `str` (API externe identique à `_Cles` pour keys()/items())."""

    __slots__ = ("_blob", "_off", "_n")

    def __init__(self, blob, off):
        self._blob = blob        # memoryview octets (région blob du mmap)
        self._off = off          # memoryview cast 'I'/'Q' (n+1 offsets, unités d'octets == caractères ASCII)
        self._n = len(off) - 1

    def __len__(self):
        return self._n

    def __getitem__(self, i):    # OCTETS (pour bisect contre la clé requête encodée latin-1)
        o = self._off
        return bytes(self._blob[o[i]:o[i + 1]])

    def __iter__(self):          # STR (consommateurs externes : keys()/items()/iter)
        blob, o = self._blob, self._off
        for i in range(self._n):
            yield bytes(blob[o[i]:o[i + 1]]).decode("latin-1")


class _LabelsMmap:
    """Vue SÉQUENCE (code entier -> valeur `str`) adossée au mmap `.colf`, jumelle de `_ClesMmap` pour les
    LABELS (valeurs distinctes d'une table). AVANT (VER 1) les labels vivaient dans une `list[str]` Python =
    TAS ANONYME non réclamable (mesuré 245 Mo sur le corpus : definition_nom 32 Mo, taxon_parent 22 Mo…). Ici
    ils sont un blob UTF-8 concaténé + offsets, MMAPPÉS -> pages file-backed PARTAGÉES et RÉCLAMABLES sous
    pression, décodées À LA DEMANDE (une valeur n'est matérialisée que si un `Fait` la réclame, puis mutualisée
    par `_ColTableMmap._cache`). Les valeurs peuvent contenir des accents -> UTF-8 (round-trip exact, FAUX=0).
    Offsets en OCTETS (utf-8), pas en caractères (contrairement aux clés ASCII)."""

    __slots__ = ("_blob", "_off", "_n")

    def __init__(self, blob, off):
        self._blob = blob        # memoryview octets (région lab_blob du mmap, utf-8)
        self._off = off          # memoryview cast 'I'/'Q' (n+1 offsets en octets)
        self._n = len(off) - 1

    def __len__(self):
        return self._n

    def __getitem__(self, i):    # STR décodée à la demande (code -> valeur)
        o = self._off
        return bytes(self._blob[o[i]:o[i + 1]]).decode("utf-8")

    def __iter__(self):          # STR (consommateurs externes qui font set(t._labels)/list(...))
        blob, o = self._blob, self._off
        for i in range(self._n):
            yield bytes(blob[o[i]:o[i + 1]]).decode("utf-8")


class _ColTableMmap:
    """Variante MMAP de `_ColTable` : MÊME API lecture seule (get/__getitem__/__contains__/len/iter/keys/
    values/items/to_dict + attributs _labels/_cat/_src), mais blob/offsets/codes ET labels sont des VUES sur un
    fichier `.colf` mappé read-only -> RAM PARTAGÉE entre process (Shared_Clean) et réclamable, load quasi-gratuit
    (demand-paged). RÉPONSES IDENTIQUES à `_ColTable` (prouvé par hash A/B). Garde une réf au mmap pour qu'il
    vive aussi longtemps que la table."""

    __slots__ = ("_keys", "_codes", "_labels", "_cat", "_src", "_cache", "_mm")

    def __init__(self, keys, codes, labels, cat, src, mm):
        self._keys = keys        # _ClesMmap
        self._codes = codes      # memoryview cast 'H'/'I' (1 code/fait, aligné sur _keys)
        self._labels = labels    # list[str] des valeurs distinctes (petite -> RAM privée minime)
        self._cat = cat
        self._src = src
        self._cache: dict[int, Fait] = {}
        self._mm = mm            # garde le mmap vivant (sinon le buffer sous-jacent est libéré)

    def _fait(self, code: int) -> Fait:
        f = self._cache.get(code)
        if f is None:
            f = self._cache[code] = Fait(self._labels[code], self._cat, self._src)
        return f

    def get(self, cle, defaut=None):
        try:
            cb = cle.encode("latin-1")
        except UnicodeEncodeError:
            return defaut        # clé non-ASCII -> jamais présente dans une table ASCII
        keys = self._keys
        i = bisect.bisect_left(keys, cb)
        if i < keys._n and keys[i] == cb:
            return self._fait(self._codes[i])
        return defaut

    def __getitem__(self, cle):
        f = self.get(cle)
        if f is None:
            raise KeyError(cle)
        return f

    def __contains__(self, cle):
        try:
            cb = cle.encode("latin-1")
        except UnicodeEncodeError:
            return False
        keys = self._keys
        i = bisect.bisect_left(keys, cb)
        return i < keys._n and keys[i] == cb

    def __len__(self):
        return self._keys._n

    def __iter__(self):
        return iter(self._keys)

    def keys(self):
        return iter(self._keys)

    def values(self):
        f = self._fait
        return (f(c) for c in self._codes)

    def items(self):
        f = self._fait
        return ((k, f(c)) for k, c in zip(self._keys, self._codes))

    def to_dict(self) -> dict:
        f = self._fait
        return {k: f(c) for k, c in zip(self._keys, self._codes)}


# ============================================================================================
#  OPTIM T9 — CACHE BINAIRE COLUMNAR (saute le parsing JSON, mesure x130 sur le load complet).
#  Par relation : un .bin marshal de la _ColTable batie (clés ASCII -> round-trip exact). Invalidé
#  par mtime+taille du .jsonl. Best-effort : TOUTE erreur (absent / version marshal / jsonl change)
#  = MISS -> parse normal (FAUX=0 : le cache stocke EXACTEMENT la table batie+validee ; A/B hash=egal).
# ============================================================================================
_CACHE_MAGIC = b"LCT9"
_CACHE_VER = 1
_CACHE_DIR = os.environ.get("LECTEUR_CACHE_DIR") or os.path.join(os.path.expanduser("~"), ".cache", "ia-lecteur")
# CACHE PORTABLE : quand un `.colf` pré-construit est LIVRÉ (Release) et extrait sur une autre machine, le mtime du
# jsonl change (l'extraction en pose un neuf) et invaliderait le cache à tort -> rebuild à froid non voulu. Ce mode
# (opt-in) fait confiance à la TAILLE du jsonl seule (contrôle d'intégrité qui survit à l'extraction). Défaut OFF.
_CACHE_PORTABLE = os.environ.get("LECTEUR_CACHE_PORTABLE", "0") != "0"


def _ecris_cache_coltable(nom, chemin_jsonl, ct, rel, articles):
    try:
        st = os.stat(chemin_jsonl)
        payload = marshal.dumps((
            _CACHE_VER, rel, articles, ct._cat, ct._src, st.st_mtime_ns, st.st_size,
            ct._keys._blob, ct._keys._off.typecode, ct._keys._off.tobytes(),
            ct._codes.typecode, ct._codes.tobytes(), ct._labels,
        ))
        os.makedirs(_CACHE_DIR, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=_CACHE_DIR, suffix=".tmp")
        with os.fdopen(fd, "wb") as fh:
            fh.write(_CACHE_MAGIC); fh.write(payload)
        os.replace(tmp, os.path.join(_CACHE_DIR, nom + ".bin"))   # atomique (writers concurrents OK)
    except Exception:
        pass


def _charge_cache_coltable(nom, chemin_jsonl):
    try:
        with open(os.path.join(_CACHE_DIR, nom + ".bin"), "rb") as fh:
            if fh.read(4) != _CACHE_MAGIC:
                return (None, None, None)
            (ver, rel, articles, cat, src, mtime_ns, size,
             blob, off_tc, off_bytes, codes_tc, codes_bytes, labels) = marshal.loads(fh.read())
        if ver != _CACHE_VER:
            return (None, None, None)
        st = os.stat(chemin_jsonl)
        if st.st_mtime_ns != mtime_ns or st.st_size != size:
            return (None, None, None)
        off = array.array(off_tc); off.frombytes(off_bytes)
        codes = array.array(codes_tc); codes.frombytes(codes_bytes)
        return (_ColTable(_Cles(blob, off), codes, labels, cat, src), rel, articles)
    except Exception:
        return (None, None, None)


# ============================================================================================
#  OPTIM LEVIER 2 — BACKEND MMAP FRUGAL (.colf). Le cache #4 marshal RECONSTRUIT des objets Python
#  (RAM privée, non réclamable, N process = N copies). Le format PLAT .colf pose blob/offsets/codes en
#  régions 8-alignées mmappées read-only -> N process PARTAGENT 1 copie (Shared_Clean), RAM réclamable,
#  load demand-paged quasi-gratuit. DÉFAUT ON (échappatoire `LECTEUR_MMAP=0`) : mesuré 2026-07-02 A/B sur le
#  corpus complet (71 144 812 faits) -> hash des faits IDENTIQUE mmap vs parse (byte-identique, FAUX=0 préservé),
#  import 2,6 s (mmap) vs 4,3 s (parse), pages .colf Shared_Clean réclamables (gain RAM inter-process : flotte
#  12 lanes 22 Go -> 4,7 Go Pss). Cache .colf chaud sur ext4 (~/.cache/ia-lecteur) ; repli parse+re-warm si MISS.
#  FAUX=0 : blob ASCII -> octets latin-1 1:1, offsets/codes = array.tobytes() exacts (hash A/B = égal).
# ============================================================================================
_COLF_MAGIC = b"LCF9"
_COLF_VER = 2   # VER 2 : labels dé-objetisés en blob UTF-8 mmappé (_LabelsMmap) — sort ~245 Mo du tas anonyme
# OPTIM LEVIER 3 — RÉSIDENCE PAGINÉE À LA DEMANDE. Les pages .colf sont file-backed CLEAN donc réclamables,
# mais restent RÉSIDENTES (comptées dans le RSS) tant que le noyau ne subit pas de pression — le RSS affiché
# gonfle alors à la taille du corpus chaud alors que la mémoire RÉELLEMENT possédée par le process est ~13 Mo.
# Après avoir lu l'en-tête (le seul besoin au load), on conseille MADV_RANDOM (aucune lecture anticipée : une
# requête ne fait remonter QUE les pages qu'elle touche via bisect) puis MADV_DONTNEED (rend tout de suite les
# pages faultées par la lecture d'en-tête). Résultat mesuré : RSS au load 332 Mo -> ~15 Mo ; les blob/offsets/
# codes refont surface À LA DEMANDE, identiques (mapping read-only, pages CLEAN rechargées du fichier). FAUX=0
# inchangé. Échappatoire LECTEUR_MADV=0 (garde les pages chaudes si la machine a de la RAM à revendre).
_MADV = os.environ.get("LECTEUR_MADV", "1") != "0"


def _rends_pages(mm):
    """Rend au noyau les pages faultées par la lecture d'en-tête et coupe la lecture anticipée (résidence à la
    demande). Best-effort : madvise indisponible / EINVAL -> on ignore (pages simplement gardées chaudes)."""
    if not _MADV:
        return
    try:
        mm.madvise(mmap.MADV_RANDOM)     # pas de readahead : le RSS ne suit que le working-set réel des requêtes
        mm.madvise(mmap.MADV_DONTNEED)   # libère maintenant les pages d'en-tête (refault propre du fichier au besoin)
    except (AttributeError, OSError, ValueError):
        pass
_MMAP = os.environ.get("LECTEUR_MMAP", "1") != "0"   # backend mmap frugal : DÉFAUT ON (échappatoire LECTEUR_MMAP=0)


def _ecris_colf(nom, chemin_jsonl, ct, rel, articles):
    """Sérialise la table figée `ct` (_ColTable) en fichier PLAT `.colf` mmappable. blob ASCII -> octets
    latin-1 1:1 ; offsets/codes = array.tobytes() ; régions 8-alignées ; header marshal (petit). Best-effort,
    écriture atomique (os.replace : writers concurrents OK)."""
    try:
        st = os.stat(chemin_jsonl)
        blob_b = ct._keys._blob.encode("latin-1")
        off_b = ct._keys._off.tobytes()
        codes_b = ct._codes.tobytes()
        # LABELS -> blob UTF-8 + offsets (VER 2) : sort la list[str] du tas anonyme vers une région mmappable
        # réclamable. UTF-8 car les valeurs peuvent porter des accents (round-trip exact -> FAUX=0).
        lab_off = array.array("Q", [0])
        acc = 0
        parts = []
        for s in ct._labels:
            sb = s.encode("utf-8")
            parts.append(sb)
            acc += len(sb)
            lab_off.append(acc)
        lab_blob = b"".join(parts)
        lab_off_tc = "I" if acc < 2**32 else "Q"
        if lab_off_tc == "I":
            lab_off = array.array("I", lab_off)   # ré-encode compact si le blob tient sur 32 bits
        lab_off_b = lab_off.tobytes()
        header = marshal.dumps((
            _COLF_VER, rel, articles, ct._cat, ct._src, st.st_mtime_ns, st.st_size,
            ct._keys._off.typecode, ct._codes.typecode, lab_off_tc,
            len(blob_b), len(off_b), len(codes_b), len(lab_blob), len(lab_off_b),
        ))
        buf = bytearray()
        buf += _COLF_MAGIC
        buf += struct.pack("<I", len(header))
        buf += header
        for region in (blob_b, off_b, codes_b, lab_blob, lab_off_b):
            while len(buf) % 8:
                buf.append(0)                   # chaque région alignée 8 (blob/off/codes/lab_blob/lab_off)
            buf += region
        os.makedirs(_CACHE_DIR, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=_CACHE_DIR, suffix=".tmp")
        with os.fdopen(fd, "wb") as fh:
            fh.write(buf)
        os.replace(tmp, os.path.join(_CACHE_DIR, nom + ".colf"))
    except Exception:
        pass


def _charge_colf_mmap(nom, chemin_jsonl):
    """mmap read-only le `.colf` -> (_ColTableMmap, rel, articles). MISS (None,None,None) si absent / mauvaise
    version / `.jsonl` modifié (mtime_ns+taille). Le fd est fermé après mmap (Linux conserve le mapping) pour
    ne pas épuiser les descripteurs sur des milliers de tables. Le mmap reste vivant via la table."""
    chemin = os.path.join(_CACHE_DIR, nom + ".colf")
    try:
        fd = os.open(chemin, os.O_RDONLY)
    except OSError:
        return (None, None, None)
    try:
        mm = mmap.mmap(fd, 0, prot=mmap.PROT_READ)
    except Exception:
        os.close(fd)
        return (None, None, None)
    os.close(fd)                                # le mapping survit à la fermeture du fd (Linux)
    try:
        if mm[:4] != _COLF_MAGIC:
            mm.close(); return (None, None, None)
        hlen = struct.unpack_from("<I", mm, 4)[0]
        (ver, rel, articles, cat, src, mtime_ns, size, off_tc, codes_tc, lab_off_tc,
         blob_len, off_len, codes_len, lab_blob_len, lab_off_len) = marshal.loads(mm[8:8 + hlen])
        if ver != _COLF_VER:
            mm.close(); return (None, None, None)
        st = os.stat(chemin_jsonl)
        # Invalidation : la TAILLE du jsonl doit toujours coïncider (garde d'intégrité forte, survit à une copie/
        # extraction d'archive). Le MTIME, lui, CHANGE quand on extrait un cache livré (tar/zip posent un mtime
        # neuf) -> en mode CACHE PORTABLE (`LECTEUR_CACHE_PORTABLE=1`, utilisé quand on livre un `.colf` pré-construit
        # dans une Release) on ignore le mtime et on se fie à la taille. Sûr : si le jsonl diffère, sa taille diffère
        # -> MISS -> rebuild. FAUX=0 préservé (le `.colf` livré est construit du MÊME code+données que le jsonl livré).
        if st.st_size != size or (st.st_mtime_ns != mtime_ns and not _CACHE_PORTABLE):
            mm.close(); return (None, None, None)
        pos = 8 + hlen
        blob_off = (pos + 7) & ~7
        off_off = (blob_off + blob_len + 7) & ~7
        codes_off = (off_off + off_len + 7) & ~7
        lab_blob_off = (codes_off + codes_len + 7) & ~7
        lab_off_off = (lab_blob_off + lab_blob_len + 7) & ~7
        mv = memoryview(mm)
        labels = _LabelsMmap(mv[lab_blob_off:lab_blob_off + lab_blob_len],
                             mv[lab_off_off:lab_off_off + lab_off_len].cast(lab_off_tc))
        tbl = _ColTableMmap(
            _ClesMmap(mv[blob_off:blob_off + blob_len], mv[off_off:off_off + off_len].cast(off_tc)),
            mv[codes_off:codes_off + codes_len].cast(codes_tc), labels, cat, src, mm)
        _rends_pages(mm)                         # résidence à la demande : rend les pages d'en-tête, coupe le readahead
        return (tbl, rel, articles)
    except Exception:
        return (None, None, None)               # mm/mv locaux -> GC démappe ; PAS de close() (BufferError si vues vivantes)

def _norme_valeur(val: str) -> str:
    """Normalisation MINIMALE de la VALEUR avant test de conflit/idempotence (durcissement 2026-07-02 : le
    conflit comparait des str brutes -> deux graphies du MÊME fait, « Paris » vs « Paris␠» ou avec espace
    insécable, déclenchaient un FAUX conflit ou passaient pour deux valeurs). Périmètre volontairement étroit :
    blancs exotiques (NBSP/fine/tab) -> espace, séquences de blancs -> un espace, bords rognés. On ne touche NI
    la casse NI les accents NI la ponctuation : deux valeurs réellement différentes RESTENT un conflit refusé.
    Chemin chaud : garde par balayages `in` (C) — une valeur déjà propre ne paie qu'un test, aucune allocation."""
    if ("\u00a0" in val or "\u202f" in val or "\u2009" in val or "\t" in val
            or "  " in val or "\n" in val):
        return " ".join(val.split())          # str.split() absorbe TOUS les blancs Unicode, séquences comprises
    if val[:1] == " " or val[-1:] == " ":
        return val.strip()
    return val


# Dossier des datasets ingérés HORS-LIGNE (un fichier .jsonl = une table). Le réseau n'est JAMAIS touché
# ici : ce sont les scripts `ingere_*.py` (lancés à la main, online) qui écrivent ces fichiers ; le lecteur
# se contente de les CHARGER au démarrage. Si le dossier est absent/vide, l'amorce hand-typed reste le socle.
_DOSSIER_DATASETS = os.environ.get("LECTEUR_DATASETS_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "lecteur")  # OPTIM T9: override opt-in (copie ext4 rapide) ; env absent = chemin 9p inchange


class Lecteur:
    """Lecteur générique : ingère des tables vérifiées (relation -> {entité: Fait}) et répond lookup-ou-HORS."""

    # Gabarits NL des tables ingérées. Un gabarit reconnu mais entité inconnue NE bloque PAS : on retombe
    # sur base_faits (cf. repond_nl) -> on n'invente jamais et on ne régresse jamais l'amorce.
    _GABARITS = [
        (re.compile(r"\bnumero atomique (?:de l |de la |du |de )?(.+)$"), "numero_atomique", 1),
        (re.compile(r"\b(?:combien de jours|nombre de jours)\b.*?\b(janvier|fevrier|mars|avril|mai|juin|"
                    r"juillet|aout|septembre|octobre|novembre|decembre)\b"), "jours_mois", 1),
        (re.compile(r"\bprefixe (?:si )?(?:du |de la |de l |des |de )?(.+)$"), "prefixe_si", 1),
        (re.compile(r"\bcode iso (?:du |de la |de l |des |de )?(?:pays )?(.+)$"), "code_iso_pays", 1),
        (re.compile(r"\bcode (?:iso )?(?:de la |de l |du |des |de )?(?:devise|monnaie) (?:du |de la |de l |des |de )?(.+)$"), "code_devise", 1),
        (re.compile(r"\bdurete (?:mohs )?(?:de |du |de la |de l |des )?(.+)$"), "durete_mohs", 1),
        (re.compile(r"\bindicatif (?:telephonique )?(?:du |de la |de l |des |de )?(.+)$"), "indicatif_telephonique", 1),
        (re.compile(r"\bformule (?:chimique )?(?:du |de la |de l |des |de )?(.+)$"), "formule_chimique", 1),
        (re.compile(r"\bsur quel continent (?:se trouve |est |se situe )?(?:l |le |la |les )?(.+)$"), "continent", 1),
        (re.compile(r"\b(?:position|rang|quelle position|quel rang) .*?\b(mercure|venus|terre|mars|jupiter|"
                    r"saturne|uranus|neptune)\b"), "rang_planete", 1),
        (re.compile(r"\b(?:monnaie|devise) (?:officielle )?(?:du |de la |de l |des |de )?(.+)$"), "monnaie", 1),
        (re.compile(r"\blangue (?:officielle |parlee )?(?:du |de la |de l |des |de |en |au )?(.+)$"), "langue_officielle", 1),
        (re.compile(r"\b(?:combien de cotes|nombre de cotes)\b.*?\b(triangle|quadrilatere|pentagone|hexagone|"
                    r"heptagone|octogone|nonagone|decagone|dodecagone)\b"), "cotes_polygone", 1),
        (re.compile(r"\b(?:combien de faces|nombre de faces)\b.*?\b(tetraedre|cube|hexaedre|octaedre|"
                    r"dodecaedre|icosaedre)\b"), "faces_solide", 1),
    ]

    def __init__(self):
        self.tables: dict[str, dict[str, Fait]] = {}   # relation -> {entité normalisée: Fait}
        self.norm_articles: dict[str, bool] = {}       # relation -> retirer les articles de tête ? (clé canonique)

    def _cle(self, relation: str, entite: str) -> str:
        """Clé canonique d'une entité selon la POLITIQUE de la relation. Par défaut on retire les articles
        de tête (« la france »->« france ») ; on les GARDE pour les tables de SYMBOLES où une lettre isolée
        EST un article français (chiffre romain L/D, etc.) — sinon la clé deviendrait vide."""
        if self.norm_articles.get(relation, True):
            return _sans_articles(str(entite))
        return normalise(str(entite))

    def ingere_table(self, relation: str, lignes, categorie: str, source: str, articles: bool = True) -> int:
        """Ingère une table (itérable de (entité, valeur)). Renvoie le nombre de NOUVELLES entrées.
        Conflit (valeur divergente sur une clé existante) -> ValueError. Clé/valeur vide -> ignorée.
        `articles` : retirer les articles de tête de l'entité (défaut True) ; False pour les tables de
        symboles (clés mono-lettre). La politique doit être COHÉRENTE pour une relation donnée."""
        if categorie not in _CATS_OK:
            raise ValueError(f"catégorie inconnue : {categorie!r} (attendu {sorted(_CATS_OK)})")
        if not source or not str(source).strip():
            raise ValueError("source obligatoire (traçabilité du fait)")
        if not relation or not str(relation).strip():
            raise ValueError("relation obligatoire")
        if relation in self.norm_articles and self.norm_articles[relation] != articles:
            raise ValueError(f"politique d'articles incohérente pour {relation!r} (déjà ingérée autrement)")
        self.norm_articles.setdefault(relation, articles)
        # Dé-gel de sécurité : si la relation a déjà été figée en colonnes (`gele()`), on la repasse en
        # dict mutable AVANT d'y écrire (le contrôle conflit/idempotence exige un mapping mutable). Chemin
        # FROID uniquement : l'ingestion en ligne n'écrit pas dans une table figée. Réponses inchangées.
        deja = self.tables.get(relation)
        if isinstance(deja, _ColTable):
            self.tables[relation] = deja.to_dict()
        t = self.tables.setdefault(relation, {})
        n = 0
        # LÉGÈRETÉ : catégorie/source sont CONSTANTES par table -> internées une seule fois (sinon 1 copie/fait,
        # soit des millions de copies d'une même chaîne source). La valeur est internée par fait : les valeurs
        # très répétées (≈200 pays, ≈872 sports partagés par des millions de faits) deviennent UN seul objet.
        cat_i = sys.intern(str(categorie))
        src_i = sys.intern(str(source))
        # MUTUALISATION DES FAITS : dans une table, cat/source sont fixes -> tous les faits de MÊME valeur ont un
        # triplet (valeur,cat,source) IDENTIQUE. `Fait` est frozen (immuable) -> on partage UN seul objet par
        # valeur distincte (ex. les millions de « -> France » deviennent ~1 objet au lieu d'un par fait). Sûr.
        cache_fait: dict[str, Fait] = {}
        # NB testé : interner les CLÉS est CONTRE-PRODUCTIF ici (+150 Mo) — trop de clés uniques (noms de
        # personnes) -> la table d'internement coûte plus que le partage inter-tables ne rapporte. Ne pas refaire.
        for entite, valeur in lignes:
            cle = self._cle(relation, entite)
            val = "" if valeur is None else str(valeur)
            val = _norme_valeur(val)
            if not cle or not val:
                continue                       # garde-fou : jamais de clé/valeur vide en table
            ancien = t.get(cle)
            if ancien is not None:
                if ancien.valeur != val:
                    raise ValueError(
                        f"conflit d'ingestion ({relation!r}, {cle!r}) : {ancien.valeur!r} vs {val!r} "
                        f"— source autoritative incohérente, pas d'écrasement")
                continue                       # idempotent : même valeur déjà présente
            f = cache_fait.get(val)
            if f is None:
                f = cache_fait[val] = Fait(sys.intern(val), cat_i, src_i)
            t[cle] = f
            n += 1
        return n

    def charge_jsonl(self, relation: str, chemin: str, categorie: str, source: str,
                     articles: bool = True) -> int:
        """Charge une table depuis un fichier JSONL OFFLINE (streaming) : chaque ligne non vide est un objet
        avec au moins les clés `entite` et `valeur`. Passe par `ingere_table` -> MÊMES garde-fous (conflit
        divergent refusé, idempotence, clé/valeur vide ignorée, FAUX=0). Renvoie le nb de NOUVELLES entrées.
        Une ligne d'en-tête éventuelle (clé `_relation`) est ignorée ici (cf. `charge_dossier`)."""
        def _lignes():
            with open(chemin, encoding="utf-8") as fh:
                for num, brut in enumerate(fh, 1):
                    brut = brut.strip()
                    if not brut:
                        continue
                    obj = json.loads(brut)
                    if "_relation" in obj:           # en-tête self-describing -> ignoré par charge_jsonl
                        continue
                    if "entite" not in obj or "valeur" not in obj:
                        raise ValueError(f"{chemin}:{num} ligne sans 'entite'/'valeur' : {obj!r}")
                    yield (obj["entite"], obj["valeur"])
        return self.ingere_table(relation, _lignes(), categorie, source, articles=articles)

    def charge_dossier(self, dossier: str = _DOSSIER_DATASETS, utiliser_mmap=None) -> dict[str, int]:
        """Auto-découverte OFFLINE : charge tous les `*.jsonl` du dossier (triés). Chaque fichier est
        SELF-DESCRIBING — sa 1ʳᵉ ligne non vide est un en-tête {`_relation`,`_categorie`,`_source`,`_articles`?},
        les suivantes des faits {`entite`,`valeur`}. Dossier absent -> ne fait rien (l'amorce reste le socle).
        Renvoie {relation: nb_nouvelles}. AUCUN accès réseau (le réseau vit dans les scripts `ingere_*`)."""
        charges: dict[str, int] = {}
        use_mmap = _MMAP if utiliser_mmap is None else utiliser_mmap   # OPTIM Levier2 : backend mmap frugal opt-in
        if not os.path.isdir(dossier):
            return charges
        for nom in sorted(os.listdir(dossier)):
            if not nom.endswith(".jsonl"):
                continue
            chemin = os.path.join(dossier, nom)
            if use_mmap:                                           # Levier2 : .colf mmappé (RAM partagée+réclamable, load ~gratuit)
                _mct, _mrel, _mart = _charge_colf_mmap(nom, chemin)
                if _mct is not None and _mrel not in self.tables:
                    self.tables[_mrel] = _mct
                    self.norm_articles.setdefault(_mrel, _mart)
                    charges[_mrel] = charges.get(_mrel, 0) + len(_mct)
                    continue
            _ct, _rel, _art = _charge_cache_coltable(nom, chemin)   # OPTIM T9 cache binaire columnar
            if _ct is not None and _rel not in self.tables:        # rel pur-dataset (pas amorce) -> reutilise tel quel
                self.tables[_rel] = _ct
                self.norm_articles.setdefault(_rel, _art)
                charges[_rel] = charges.get(_rel, 0) + len(_ct)
                if use_mmap:                                       # warm le .colf pour la prochaine fois (-> mmap)
                    _ecris_colf(nom, chemin, _ct, _rel, _art)
                continue
            tete, data = None, []
            with open(chemin, encoding="utf-8") as fh:
                for num, brut in enumerate(fh, 1):
                    brut = brut.strip()
                    if not brut:
                        continue
                    obj = json.loads(brut)
                    if tete is None and "_relation" in obj:
                        tete = obj
                        continue
                    if "entite" not in obj or "valeur" not in obj:
                        raise ValueError(f"{chemin}:{num} ligne sans 'entite'/'valeur' : {obj!r}")
                    data.append((obj["entite"], obj["valeur"]))
            if tete is None:
                raise ValueError(f"{chemin} : en-tête manquant (1ʳᵉ ligne {{_relation,_categorie,_source}})")
            for cle in ("_relation", "_categorie", "_source"):
                if not tete.get(cle):
                    raise ValueError(f"{chemin} : en-tête incomplet ({cle} obligatoire)")
            n = self.ingere_table(tete["_relation"], data, tete["_categorie"], tete["_source"],
                                  articles=bool(tete.get("_articles", True)))
            charges[tete["_relation"]] = charges.get(tete["_relation"], 0) + n
            self._gele_table(tete["_relation"])   # OPTIM T9 gel incremental : libere le dict tout de suite (pic -57%)
            _t = self.tables.get(tete["_relation"])
            if isinstance(_t, _ColTable):                          # OPTIM T9 : ecrit le cache binaire (mono-source figee)
                _ecris_cache_coltable(nom, chemin, _t, tete["_relation"], bool(tete.get("_articles", True)))
                if use_mmap:                                       # Levier2 : écrit aussi le .colf mmappable
                    _ecris_colf(nom, chemin, _t, tete["_relation"], bool(tete.get("_articles", True)))
                    # OPTIM LEVIER 3 (BUILD À FROID LÉGER) : la table vient d'être sérialisée en .colf -> on REMPLACE
                    # sa version RAM (_ColTable = clés blob + codes + labels, tout en TAS) par la vue mmap
                    # (_ColTableMmap = pages file-backed réclamables, madvise DONTNEED appliqué). Sans ça, un build
                    # à froid des 72M faits accumule ~3,3 Go de _ColTable ; avec, le pic ne retient qu'UNE table à la
                    # fois (transitoire). Réponses IDENTIQUES (même .colf que la lecture à chaud). MISS -> on garde
                    # le _ColTable RAM (aucune régression). Ne s'exécute qu'au tout premier build (ensuite = mmap HIT).
                    _mtb, _mrel, _mart = _charge_colf_mmap(nom, chemin)
                    if _mtb is not None:
                        self.tables[tete["_relation"]] = _mtb
        return charges

    def cherche(self, relation: str, entite: str) -> Fait | None:
        """Lookup EXACT : tables ingérées d'abord, REPLI sur l'amorce figée base_faits. None si absent."""
        t = self.tables.get(relation)
        if t is not None:
            f = t.get(self._cle(relation, entite))
            if f is not None:
                return f
        return _cherche_base(relation, entite)

    def repond(self, relation: str, entite: str) -> tuple[str, Fait | None]:
        """(VERIFIE, Fait) si connu, sinon (HORS, None). Le contrat sound du chantier #3."""
        f = self.cherche(relation, entite)
        return (VERIFIE, f) if f is not None else (HORS, None)

    def repond_nl(self, question: str) -> tuple[str, Fait | None]:
        """NL : gabarits des tables ingérées d'abord ; REPLI COMPLET sur base_faits.repond_nl.
        Jamais une régression de l'amorce, jamais une invention (gabarit + entité inconnue -> repli)."""
        q = normalise(question)
        for rx, relation, gi in self._GABARITS:
            m = rx.search(q)
            if m:
                entite = m.group(gi) if gi else ""
                f = self.cherche(relation, entite)
                if f is not None:
                    return (VERIFIE, f)
        return _repond_base(question)

    def relations(self) -> list[str]:
        return sorted(self.tables)

    def __len__(self) -> int:
        return sum(len(t) for t in self.tables.values())

    def _gele_table(self, rel):
        """OPTIM T9 (gel incremental, Gain #0 du brief) : fige UNE table mono-source en colonnes juste apres
        son chargement (chaque relation = 1 fichier, verifie 0 multi-fichier). MEMES colonnes que gele(),
        seul le MOMENT change -> sortie identique (hash 41M triplets verifie) ; libere le dict tout de suite
        (pic de chargement 6,2->2,7 Go, -57%)."""
        t = self.tables.get(rel)
        if not isinstance(t, dict) or not t:
            return None
        it = iter(t.values())
        f0 = next(it)
        cat, src = f0.categorie, f0.source
        if not all(f.categorie == cat and f.source == src for f in it):
            return None
        keys = sorted(t)
        labels = []
        code_de = {}
        codes_py = []
        off_py = [0]
        acc = 0
        for k in keys:
            v = t[k].valeur
            c = code_de.get(v)
            if c is None:
                c = code_de[v] = len(labels)
                labels.append(v)
            codes_py.append(c)
            acc += len(k)
            off_py.append(acc)
        tc = "I" if len(labels) > 65535 else "H"
        to = "I" if acc < 2**32 else "Q"
        cles = _Cles("".join(keys), array.array(to, off_py))
        self.tables[rel] = _ColTable(cles, array.array(tc, codes_py), labels, cat, src)
        return len(keys)

    def gele(self) -> dict[str, int]:
        """Fige en COLONNES compactes (`_ColTable`) toutes les tables MONO-SOURCE — gain RAM majeur sur
        les grosses tables (≈190 valeurs distinctes partagées par des millions de faits). Une table dont
        catégorie/source NE sont PAS constants (extension sans contradiction : base_faits + dataset, ou
        plusieurs datasets de sources ≠) reste un DICT (les 7 tables multi-source mesurées, toutes ≤249
        entrées : gain négligeable, on ne force pas). Idempotent. NE CHANGE AUCUNE RÉPONSE — seulement la
        disposition mémoire. À appeler UNE fois après `charge_dossier` (chemin chaud offline de la gate).
        Renvoie {relation: nb_entrées_figées}."""
        figees: dict[str, int] = {}
        for rel, t in list(self.tables.items()):
            if not isinstance(t, dict) or not t:
                continue                       # déjà figée, ou vide : rien à faire
            it = iter(t.values())
            f0 = next(it)
            cat, src = f0.categorie, f0.source
            if not all(f.categorie == cat and f.source == src for f in it):
                continue                       # multi-source -> laissée en dict (extension sans contradiction)
            keys = sorted(t)                   # clés triées (mêmes objets str : référencées, pas copiées)
            labels: list[str] = []
            code_de: dict[str, int] = {}
            codes_py: list[int] = []
            off_py: list[int] = [0]
            acc = 0
            for k in keys:
                v = t[k].valeur
                c = code_de.get(v)
                if c is None:
                    c = code_de[v] = len(labels)
                    labels.append(v)
                codes_py.append(c)
                acc += len(k)                  # clés ascii -> 1 car == 1 o ; offset en caractères
                off_py.append(acc)
            tc = "I" if len(labels) > 65535 else "H"   # code valeur : 'H' 2 o (<65536 distinctes), sinon 'I' 4 o
            to = "I" if acc < 2**32 else "Q"           # offsets : 'I' 4 o si blob < 4 Gio, sinon 'Q' 8 o
            cles = _Cles("".join(keys), array.array(to, off_py))   # blob str unique (libère n objets str de clé)
            self.tables[rel] = _ColTable(cles, array.array(tc, codes_py), labels, cat, src)
            figees[rel] = len(keys)
        return figees


# ============================================================================================
#  AMORCE — deux sources EXACTES & SOURCÉES ingérées au chargement (preuve de la boucle
#  source -> lecteur -> lookup-ou-HORS). Petit mais 100 % vérifiable ; le mécanisme est le sujet.
# ============================================================================================

# --- Calendrier grégorien / ISO-8601 (CONVENTION) — absorbe le résidu jours-mois de #1 (table, non calculable). ---
_JOURS_MOIS = [   # année NON bissextile (février = 28 ; le 29 est la règle bissextile, voie CALCUL séparée)
    ("janvier", 31), ("fevrier", 28), ("mars", 31), ("avril", 30), ("mai", 31), ("juin", 30),
    ("juillet", 31), ("aout", 31), ("septembre", 30), ("octobre", 31), ("novembre", 30), ("decembre", 31),
]
_MOIS_NOM = [(str(i + 1), nom) for i, (nom, _) in enumerate(_JOURS_MOIS)]          # numéro -> nom
_JOUR_SEMAINE = [(str(i + 1), j) for i, j in enumerate(                            # ISO : 1=lundi … 7=dimanche
    ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"])]

# --- Tableau périodique (IUPAC) : numéro atomique Z, ENTIER EXACT (définitionnel, non mesuré). Bucket MESURE. ---
_NUMERO_ATOMIQUE = [
    ("hydrogene", 1), ("helium", 2), ("lithium", 3), ("beryllium", 4), ("bore", 5), ("carbone", 6),
    ("azote", 7), ("oxygene", 8), ("fluor", 9), ("neon", 10), ("sodium", 11), ("magnesium", 12),
    ("aluminium", 13), ("silicium", 14), ("phosphore", 15), ("soufre", 16), ("chlore", 17), ("argon", 18),
    ("potassium", 19), ("calcium", 20), ("scandium", 21), ("titane", 22), ("vanadium", 23), ("chrome", 24),
    ("manganese", 25), ("fer", 26), ("cobalt", 27), ("nickel", 28), ("cuivre", 29), ("zinc", 30),
    ("gallium", 31), ("germanium", 32), ("arsenic", 33), ("selenium", 34), ("brome", 35), ("krypton", 36),
    ("argent", 47), ("etain", 50), ("iode", 53), ("or", 79), ("mercure", 80), ("plomb", 82), ("uranium", 92),
]

# --- Préfixes SI (CONVENTION, CGPM) : nom -> exposant de 10. Exact par définition. ---
_PREFIXE_SI = [
    ("deca", 1), ("hecto", 2), ("kilo", 3), ("mega", 6), ("giga", 9), ("tera", 12), ("peta", 15),
    ("exa", 18), ("zetta", 21), ("yotta", 24), ("ronna", 27), ("quetta", 30),
    ("deci", -1), ("centi", -2), ("milli", -3), ("micro", -6), ("nano", -9), ("pico", -12),
    ("femto", -15), ("atto", -18), ("zepto", -21), ("yocto", -24), ("ronto", -27), ("quecto", -30),
]

# --- Numération romaine (CONVENTION) : symbole -> valeur. Clés mono-lettre -> articles=False obligatoire. ---
_CHIFFRE_ROMAIN = [("I", 1), ("V", 5), ("X", 10), ("L", 50), ("C", 100), ("D", 500), ("M", 1000)]

# --- Alphabet grec (CONVENTION) : nom de la lettre -> rang 1..24. Exact. ---
_RANG_LETTRE_GRECQUE = [(nom, i + 1) for i, nom in enumerate([
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa", "lambda", "mu",
    "nu", "xi", "omicron", "pi", "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega"])]

# --- Système solaire (FAIT astronomique) : planète -> rang depuis le Soleil 1..8 (UAI 2006, Pluton exclue). ---
_RANG_PLANETE = [(nom, i + 1) for i, nom in enumerate([
    "mercure", "venus", "terre", "mars", "jupiter", "saturne", "uranus", "neptune"])]

# --- Préfixes binaires IEC 80000-13 (CONVENTION) : nom -> exposant de 2. Exact par définition. ---
_PREFIXE_BINAIRE = [
    ("kibi", 10), ("mebi", 20), ("gibi", 30), ("tebi", 40), ("pebi", 50), ("exbi", 60),
    ("zebi", 70), ("yobi", 80),
]

# --- Échelle de Mohs (CONVENTION/MESURE DÉFINITIONNELLE) : minéral de référence -> dureté 1..10. ---
_DURETE_MOHS = [
    ("talc", 1), ("gypse", 2), ("calcite", 3), ("fluorine", 4), ("apatite", 5),
    ("orthose", 6), ("quartz", 7), ("topaze", 8), ("corindon", 9), ("diamant", 10),
]

# --- Codes devises ISO 4217 (CONVENTION) : devise -> code 3 lettres. ---
_CODE_DEVISE = [
    ("euro", "EUR"), ("dollar americain", "USD"), ("livre sterling", "GBP"), ("yen", "JPY"),
    ("franc suisse", "CHF"), ("yuan", "CNY"), ("dollar canadien", "CAD"), ("dollar australien", "AUD"),
    ("roupie indienne", "INR"), ("real bresilien", "BRL"), ("rouble russe", "RUB"), ("peso mexicain", "MXN"),
    ("zloty", "PLN"), ("couronne suedoise", "SEK"), ("couronne norvegienne", "NOK"), ("couronne danoise", "DKK"),
    ("won", "KRW"), ("rand", "ZAR"), ("dollar de hong kong", "HKD"), ("dollar de singapour", "SGD"),
    ("lire turque", "TRY"),
]

# --- Codes pays ISO 3166-1 alpha-2 (CONVENTION) : pays -> code 2 lettres. Complète les capitales (base_faits). ---
_CODE_ISO_PAYS = [
    ("france", "FR"), ("allemagne", "DE"), ("espagne", "ES"), ("italie", "IT"), ("royaume uni", "GB"),
    ("etats unis", "US"), ("japon", "JP"), ("chine", "CN"), ("canada", "CA"), ("bresil", "BR"),
    ("russie", "RU"), ("inde", "IN"), ("australie", "AU"), ("belgique", "BE"), ("suisse", "CH"),
    ("portugal", "PT"), ("pays bas", "NL"), ("suede", "SE"), ("norvege", "NO"), ("mexique", "MX"),
    ("grece", "GR"), ("pologne", "PL"), ("autriche", "AT"), ("irlande", "IE"), ("danemark", "DK"),
    ("finlande", "FI"), ("maroc", "MA"), ("egypte", "EG"),
]

# --- Indicatifs téléphoniques internationaux (CONVENTION, UIT-T E.164) : pays -> indicatif (sans le +). ---
_INDICATIF_TEL = [
    ("france", 33), ("allemagne", 49), ("royaume uni", 44), ("etats unis", 1), ("canada", 1),
    ("espagne", 34), ("italie", 39), ("japon", 81), ("chine", 86), ("russie", 7), ("inde", 91),
    ("bresil", 55), ("belgique", 32), ("suisse", 41), ("pays bas", 31), ("portugal", 351),
    ("suede", 46), ("norvege", 47), ("maroc", 212), ("australie", 61), ("mexique", 52),
]

# --- Symboles des préfixes SI (CONVENTION) : nom -> symbole. Complète prefixe_si (nom -> exposant). ---
_SYMBOLE_PREFIXE_SI = [
    ("deca", "da"), ("hecto", "h"), ("kilo", "k"), ("mega", "M"), ("giga", "G"), ("tera", "T"),
    ("peta", "P"), ("exa", "E"), ("zetta", "Z"), ("yotta", "Y"), ("ronna", "R"), ("quetta", "Q"),
    ("deci", "d"), ("centi", "c"), ("milli", "m"), ("micro", "µ"), ("nano", "n"), ("pico", "p"),
    ("femto", "f"), ("atto", "a"), ("zepto", "z"), ("yocto", "y"), ("ronto", "r"), ("quecto", "q"),
]

# --- Continent d'un pays (FAIT géographique) : pays -> continent. ---
_CONTINENT = [
    ("france", "Europe"), ("allemagne", "Europe"), ("espagne", "Europe"), ("italie", "Europe"),
    ("royaume uni", "Europe"), ("russie", "Europe"), ("japon", "Asie"), ("chine", "Asie"),
    ("inde", "Asie"), ("egypte", "Afrique"), ("maroc", "Afrique"), ("nigeria", "Afrique"),
    ("kenya", "Afrique"), ("bresil", "Amérique du Sud"), ("argentine", "Amérique du Sud"),
    ("chili", "Amérique du Sud"), ("perou", "Amérique du Sud"), ("etats unis", "Amérique du Nord"),
    ("canada", "Amérique du Nord"), ("mexique", "Amérique du Nord"), ("australie", "Océanie"),
]

# --- Calendrier (CONVENTION) — relations INVERSES : nom -> numéro (complète mois_nom / jour_semaine). ---
_NUMERO_MOIS = [(nom, i + 1) for i, (nom, _) in enumerate(_JOURS_MOIS)]
_NUMERO_JOUR_SEMAINE = [(j, str(i + 1)) for i, (i_str, j) in enumerate(_JOUR_SEMAINE)]

# --- Formules chimiques de molécules courantes (FAIT chimique, non ambigu) : nom -> formule brute. ---
_FORMULE_CHIMIQUE = [
    ("eau", "H2O"), ("dioxyde de carbone", "CO2"), ("monoxyde de carbone", "CO"), ("methane", "CH4"),
    ("ammoniac", "NH3"), ("dioxygene", "O2"), ("diazote", "N2"), ("ozone", "O3"),
    ("chlorure de sodium", "NaCl"), ("acide chlorhydrique", "HCl"), ("peroxyde d hydrogene", "H2O2"),
    ("glucose", "C6H12O6"),
]

# --- Monnaie d'un pays (FAIT, état courant) : pays -> monnaie. Complète code_devise (devise -> code). ---
_MONNAIE = [
    ("france", "euro"), ("allemagne", "euro"), ("espagne", "euro"), ("italie", "euro"), ("portugal", "euro"),
    ("belgique", "euro"), ("pays bas", "euro"), ("grece", "euro"), ("autriche", "euro"), ("irlande", "euro"),
    ("finlande", "euro"), ("royaume uni", "livre sterling"), ("etats unis", "dollar americain"),
    ("japon", "yen"), ("suisse", "franc suisse"), ("chine", "yuan"), ("russie", "rouble"),
    ("inde", "roupie indienne"), ("bresil", "real"), ("canada", "dollar canadien"),
    ("australie", "dollar australien"), ("mexique", "peso mexicain"), ("suede", "couronne suedoise"),
    ("norvege", "couronne norvegienne"), ("danemark", "couronne danoise"), ("maroc", "dirham"), ("pologne", "zloty"),
]

# --- Langue officielle d'un pays (FAIT) — pays monolingues ÉVIDENTS uniquement (sûr). ---
_LANGUE_OFFICIELLE = [
    ("france", "français"), ("allemagne", "allemand"), ("espagne", "espagnol"), ("italie", "italien"),
    ("portugal", "portugais"), ("japon", "japonais"), ("russie", "russe"), ("bresil", "portugais"),
    ("mexique", "espagnol"), ("chine", "chinois"), ("pays bas", "néerlandais"), ("suede", "suédois"),
    ("norvege", "norvégien"), ("pologne", "polonais"), ("grece", "grec"), ("maroc", "arabe"), ("egypte", "arabe"),
]

# --- Polygones (CONVENTION géométrique) : nom -> nombre de côtés. Définitionnel. ---
_COTES_POLYGONE = [
    ("triangle", 3), ("quadrilatere", 4), ("pentagone", 5), ("hexagone", 6), ("heptagone", 7),
    ("octogone", 8), ("nonagone", 9), ("decagone", 10), ("dodecagone", 12),
]

# --- Solides de Platon (CONVENTION géométrique) : nom -> nombre de faces. Définitionnel. ---
_FACES_SOLIDE = [
    ("tetraedre", 4), ("cube", 6), ("hexaedre", 6), ("octaedre", 8), ("dodecaedre", 12), ("icosaedre", 20),
]

# --- Nom d'un polygone par son nombre de côtés (CONVENTION, inverse de cotes_polygone). ---
_NOM_POLYGONE = [(str(n), nom) for nom, n in _COTES_POLYGONE]

# --- Unités SI : grandeur mesurée + symbole (CONVENTION, SI). Complète base_faits.unite (description). ---
_GRANDEUR_UNITE = [
    ("metre", "longueur"), ("seconde", "temps"), ("kilogramme", "masse"), ("ampere", "courant électrique"),
    ("kelvin", "température"), ("mole", "quantité de matière"), ("candela", "intensité lumineuse"),
    ("watt", "puissance"), ("joule", "énergie"), ("newton", "force"), ("pascal", "pression"),
    ("hertz", "fréquence"), ("volt", "tension électrique"), ("ohm", "résistance électrique"),
    ("coulomb", "charge électrique"), ("tesla", "champ magnétique"), ("farad", "capacité électrique"),
    ("lumen", "flux lumineux"), ("lux", "éclairement"), ("becquerel", "activité radioactive"),
]
_SYMBOLE_UNITE = [
    ("metre", "m"), ("seconde", "s"), ("kilogramme", "kg"), ("ampere", "A"), ("kelvin", "K"), ("mole", "mol"),
    ("candela", "cd"), ("watt", "W"), ("joule", "J"), ("newton", "N"), ("pascal", "Pa"), ("hertz", "Hz"),
    ("volt", "V"), ("ohm", "Ω"), ("coulomb", "C"), ("tesla", "T"), ("farad", "F"), ("lumen", "lm"),
    ("lux", "lx"), ("becquerel", "Bq"), ("gray", "Gy"), ("sievert", "Sv"), ("henry", "H"), ("weber", "Wb"),
]

LECTEUR = Lecteur()
LECTEUR.ingere_table("jours_mois", _JOURS_MOIS, CAT_CONVENTION, "calendrier grégorien (convention)")
LECTEUR.ingere_table("mois_nom", _MOIS_NOM, CAT_CONVENTION, "calendrier grégorien (convention)")
LECTEUR.ingere_table("jour_semaine", _JOUR_SEMAINE, CAT_CONVENTION, "ISO-8601 (convention)")
LECTEUR.ingere_table("numero_atomique", _NUMERO_ATOMIQUE, CAT_PHYSIQUE, "tableau périodique (IUPAC)")
LECTEUR.ingere_table("prefixe_si", _PREFIXE_SI, CAT_CONVENTION, "Système international (préfixes, CGPM)")
LECTEUR.ingere_table("chiffre_romain", _CHIFFRE_ROMAIN, CAT_CONVENTION, "numération romaine (convention)", articles=False)
LECTEUR.ingere_table("rang_lettre_grecque", _RANG_LETTRE_GRECQUE, CAT_CONVENTION, "alphabet grec (convention)")
LECTEUR.ingere_table("rang_planete", _RANG_PLANETE, CAT_PHYSIQUE, "système solaire (UAI 2006)")
LECTEUR.ingere_table("code_iso_pays", _CODE_ISO_PAYS, CAT_CONVENTION, "ISO 3166-1 alpha-2")
LECTEUR.ingere_table("prefixe_binaire", _PREFIXE_BINAIRE, CAT_CONVENTION, "IEC 80000-13 (préfixes binaires)")
LECTEUR.ingere_table("durete_mohs", _DURETE_MOHS, CAT_PHYSIQUE, "échelle de Mohs (minéraux de référence)")
LECTEUR.ingere_table("code_devise", _CODE_DEVISE, CAT_CONVENTION, "ISO 4217")
LECTEUR.ingere_table("indicatif_telephonique", _INDICATIF_TEL, CAT_CONVENTION, "UIT-T E.164")
LECTEUR.ingere_table("symbole_prefixe_si", _SYMBOLE_PREFIXE_SI, CAT_CONVENTION, "Système international (préfixes, CGPM)")
LECTEUR.ingere_table("continent", _CONTINENT, CAT_PHYSIQUE, "géographie physique (référence)")
LECTEUR.ingere_table("numero_mois", _NUMERO_MOIS, CAT_CONVENTION, "calendrier grégorien (convention)")
LECTEUR.ingere_table("numero_jour_semaine", _NUMERO_JOUR_SEMAINE, CAT_CONVENTION, "ISO-8601 (convention)")
LECTEUR.ingere_table("formule_chimique", _FORMULE_CHIMIQUE, CAT_PHYSIQUE, "nomenclature chimique (référence)")
LECTEUR.ingere_table("monnaie", _MONNAIE, CAT_CONVENTION, "monnaies en circulation (référence)")
LECTEUR.ingere_table("langue_officielle", _LANGUE_OFFICIELLE, CAT_CONVENTION, "langues officielles (référence)")
LECTEUR.ingere_table("cotes_polygone", _COTES_POLYGONE, CAT_CONVENTION, "géométrie (définition des polygones)")
LECTEUR.ingere_table("faces_solide", _FACES_SOLIDE, CAT_CONVENTION, "géométrie (solides de Platon)")
LECTEUR.ingere_table("nom_polygone", _NOM_POLYGONE, CAT_CONVENTION, "géométrie (définition des polygones)")
LECTEUR.ingere_table("grandeur_unite", _GRANDEUR_UNITE, CAT_CONVENTION, "Système international (SI)")
LECTEUR.ingere_table("symbole_unite", _SYMBOLE_UNITE, CAT_CONVENTION, "Système international (SI)")

# Snapshot de l'AMORCE hand-typed (figé AVANT l'auto-load) : sert de référence de réconciliation aux
# scripts d'ingestion (ils comparent leurs données Wikidata à l'amorce canonique, pas aux datasets déjà
# chargés -> réconciliation STABLE entre runs, pas d'effet de bord). Lecture seule.
_AMORCE_TABLES: dict[str, dict[str, Fait]] = {rel: dict(t) for rel, t in LECTEUR.tables.items()}
_AMORCE_ARTICLES: dict[str, bool] = dict(LECTEUR.norm_articles)


def amorce_cherche(relation: str, entite: str) -> Fait | None:
    """Valeur de l'AMORCE hand-typed (lecteur OU base_faits) pour (relation, entité), sans les datasets
    auto-chargés. Utilisé par les scripts d'ingestion pour réconcilier (idempotence/conflit) de façon
    déterministe d'un run à l'autre."""
    t = _AMORCE_TABLES.get(relation)
    if t is not None:
        articles = _AMORCE_ARTICLES.get(relation, True)
        cle = _sans_articles(str(entite)) if articles else normalise(str(entite))
        f = t.get(cle)
        if f is not None:
            return f
    return _cherche_base(relation, entite)


# --- AUTO-CHARGEMENT OFFLINE des datasets ingérés à grande échelle (datasets/lecteur/*.jsonl). ---
# L'amorce ci-dessus reste le SOCLE ; ces fichiers (écrits par les scripts `ingere_*.py` online) l'ÉTENDENT.
# Aucun accès réseau : pur chargement local. Le conflit divergent reste refusé par `ingere_table`.
if os.environ.get("LECTEUR_AMORCE_SEULE") == "1":   # OPTIM T9 opt-in : ingestion = amorce seule (saute les 33M faits, ~5Go/180s sur 9p)
    _CHARGES_DATASETS = {}
else:
    _CHARGES_DATASETS = LECTEUR.charge_dossier()

# GEL COLUMNAR (légèreté) : une fois TOUTES les tables chargées (amorce + datasets offline), on fige les
# tables mono-source en colonnes compactes (clés triées + codes array + valeurs distinctes). Gain RAM net
# sur les grosses tables ; aucune réponse ne change. Fait APRÈS le snapshot `_AMORCE_TABLES` (qui copie les
# dicts plus haut) -> `amorce_cherche` n'est pas affecté. Les 7 tables multi-source restent en dict.
if os.environ.get("LECTEUR_AMORCE_SEULE") == "1":   # OPTIM T9 opt-in (cf. ci-dessus) : rien a geler sans datasets
    _FIGEES = {}
else:
    _FIGEES = LECTEUR.gele()


def cherche(relation: str, entite: str) -> Fait | None:
    return LECTEUR.cherche(relation, entite)


def repond(relation: str, entite: str) -> tuple[str, Fait | None]:
    return LECTEUR.repond(relation, entite)


def repond_nl(question: str) -> tuple[str, Fait | None]:
    return LECTEUR.repond_nl(question)


def libere_cache() -> int:
    """RÉCLAME les pages .colf résidentes (MADV_DONTNEED sur chaque table mmappée) : le RSS retombe au tas
    anonyme RÉEL du process (~15-60 Mo) après une opération lourde qui a balayé le corpus (moteur d'invention,
    validation, scan global). Les blob/offsets/codes/labels refont surface À LA DEMANDE, IDENTIQUES (mapping
    read-only, pages CLEAN rechargées du fichier) -> FAUX=0 inchangé, seule la dépense mémoire retombe. À appeler
    quand l'IA repasse en veille ou entre deux gros traitements. Renvoie le nombre de tables réclamées.
    No-op si LECTEUR_MADV=0 ou madvise indisponible. Idempotent, sans effet sur les réponses."""
    n = 0
    for t in LECTEUR.tables.values():
        mm = getattr(t, "_mm", None)
        if mm is not None:
            try:
                mm.madvise(mmap.MADV_DONTNEED)
                n += 1
            except (AttributeError, OSError, ValueError):
                pass
    return n


if __name__ == "__main__":
    from garde_ressources import borne
    borne()
    print("=== LECTEUR GÉNÉRIQUE DE DONNÉES (lookup-ou-HORS, sound) ===\n")
    print(f"Tables ingérées : {LECTEUR.relations()} ({len(LECTEUR)} entrées)\n")
    essais = [
        ("numero_atomique", "fer"), ("numero_atomique", "or"), ("numero_atomique", "oganesson"),  # dernier = absent
        ("jours_mois", "février"), ("jours_mois", "avril"), ("mois_nom", "12"), ("jour_semaine", "7"),
        ("capitale", "japon"),                # repli sur l'amorce base_faits
        ("numero_atomique", "kryptonite"),    # absent -> HORS
    ]
    for rel, ent in essais:
        statut, f = repond(rel, ent)
        if statut == VERIFIE:
            print(f"  [VÉRIFIÉ] {rel}({ent}) -> {f.valeur}   (source : {f.source})")
        else:
            print(f"  [HORS   ] {rel}({ent}) -> je n'ai pas ce fait vérifié (pas de devinette)")

    print("\n  NL : 'numéro atomique du cuivre' ->", repond_nl("Quel est le numéro atomique du cuivre ?")[1].valeur)
    print("  NL : 'combien de jours en février' ->", repond_nl("Combien de jours en février ?")[1].valeur)
    print("  NL : 'capitale de la France' (repli base) ->", repond_nl("Quelle est la capitale de la France ?")[1].valeur)

    # Démo INTÉGRITÉ : une ré-ingestion divergente est REFUSÉE (pas d'écrasement silencieux).
    try:
        LECTEUR.ingere_table("numero_atomique", [("fer", 99)], CAT_PHYSIQUE, "source erronée")
        print("\n  [BUG] conflit non détecté")
    except ValueError as e:
        print(f"\n  [OK] conflit d'ingestion refusé : {e}")
