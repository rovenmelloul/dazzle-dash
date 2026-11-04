"""Lit les fichiers préparés par scripts/prepare_data.py et calcule les pourcentages."""

from pathlib import Path

import pandas as pd

DOSSIER_PREPARE = Path(__file__).resolve().parent / "data" / "processed"

resume = pd.read_parquet(DOSSIER_PREPARE / "resume.parquet").set_index("categorie")["vols"]
causes = pd.read_parquet(DOSSIER_PREPARE / "causes.parquet").set_index("cause")["minutes"]
par_heure_compagnie = pd.read_parquet(DOSSIER_PREPARE / "par_heure_compagnie.parquet")


def pourcentage(part, total):
    return part / total * 100


def retard_par_heure():
    """Part de vols en retard par heure de départ prévue, sur les vols arrivés."""
    heures = par_heure_compagnie.groupby("HEURE")[["vols_arrives", "vols_en_retard"]].sum()
    return pourcentage(heures["vols_en_retard"], heures["vols_arrives"])
