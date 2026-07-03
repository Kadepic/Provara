"""BLOCKCHAIN / CRYPTOMONNAIES (mécanisme) — intégrité d'une chaîne, FAUX=0 (mission formule/concept 2026-06-29).

Hachage d'un bloc (SHA-256), chaînage cryptographique (chaque bloc référence le hash du précédent), validation de
l'intégrité d'une chaîne (toute altération casse le chaînage), arbre de Merkle (racine = empreinte de l'ensemble des
transactions), preuve de travail (hash sous un seuil de difficulté). Mécanisme EXACT et VÉRIFIABLE (la cryptographie
de hachage est déterministe). Abstention STRUCTURELLE : chaîne mal formée -> ValueError.

Couvre le sujet borné « Blockchain / cryptomonnaies (mécanisme) ».
Vérifié en adverse par `valide_blockchain.py` (chaîne valide vs altérée, racine de Merkle, PoW).
"""
from __future__ import annotations

import hashlib


def hash_bloc(index, donnees, hash_precedent, nonce=0) -> str:
    """Empreinte SHA-256 (hex) d'un bloc = H(index | données | hash_précédent | nonce). Déterministe."""
    contenu = f"{index}|{donnees}|{hash_precedent}|{nonce}"
    return hashlib.sha256(contenu.encode("utf-8")).hexdigest()


def cree_bloc(index, donnees, hash_precedent, nonce=0) -> dict:
    """Construit un bloc {index, donnees, prev, nonce, hash} avec son empreinte calculée."""
    return {"index": index, "donnees": donnees, "prev": hash_precedent, "nonce": nonce,
            "hash": hash_bloc(index, donnees, hash_precedent, nonce)}


def chaine_valide(blocs) -> bool:
    """True ssi la chaîne est intègre : chaque bloc a un hash correct ET référence le hash du bloc précédent.
    Toute altération d'un bloc (données, ordre) invalide la chaîne. ValueError si format invalide."""
    if not isinstance(blocs, (list, tuple)) or not blocs:
        raise ValueError("chaîne non vide de blocs requise")
    for i, b in enumerate(blocs):
        if not isinstance(b, dict) or not {"index", "donnees", "prev", "nonce", "hash"} <= set(b):
            raise ValueError(f"bloc mal formé à l'indice {i}")
        if b["hash"] != hash_bloc(b["index"], b["donnees"], b["prev"], b["nonce"]):
            return False                       # hash recalculé ≠ hash stocké -> bloc altéré
        if i > 0 and b["prev"] != blocs[i - 1]["hash"]:
            return False                       # chaînage rompu
    return True


def merkle_root(transactions) -> str:
    """Racine de l'arbre de Merkle d'une liste de transactions (SHA-256, duplication du dernier si impair)."""
    if not isinstance(transactions, (list, tuple)) or not transactions:
        raise ValueError("au moins une transaction requise")
    niveau = [hashlib.sha256(str(t).encode("utf-8")).hexdigest() for t in transactions]
    while len(niveau) > 1:
        if len(niveau) % 2 == 1:
            niveau.append(niveau[-1])          # duplique le dernier si nombre impair
        niveau = [hashlib.sha256((niveau[i] + niveau[i + 1]).encode("utf-8")).hexdigest()
                  for i in range(0, len(niveau), 2)]
    return niveau[0]


def preuve_travail_valide(hash_hex, difficulte) -> bool:
    """Preuve de travail : le hash commence-t-il par `difficulte` zéros hexadécimaux ?"""
    if not isinstance(difficulte, int) or isinstance(difficulte, bool) or difficulte < 0:
        raise ValueError("difficulté entière ≥ 0 requise")
    if not isinstance(hash_hex, str):
        raise ValueError("hash (chaîne hex) attendu")
    return hash_hex.startswith("0" * difficulte)


if __name__ == "__main__":
    g = cree_bloc(0, "genesis", "0")
    b1 = cree_bloc(1, "Alice->Bob:5", g["hash"])
    b2 = cree_bloc(2, "Bob->Carl:3", b1["hash"])
    chaine = [g, b1, b2]
    print("chaîne valide :", chaine_valide(chaine))
    chaine_falsifiee = [g, dict(b1, donnees="Alice->Bob:5000"), b2]
    print("chaîne falsifiée :", chaine_valide(chaine_falsifiee))
    print("racine de Merkle [a,b,c,d] :", merkle_root(["a", "b", "c", "d"])[:16], "…")
    print("PoW '000abc' difficulté 3 :", preuve_travail_valide("000abc", 3), "| difficulté 4 :", preuve_travail_valide("000abc", 4))
