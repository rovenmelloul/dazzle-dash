"""Lit les fichiers préparés par scripts/prepare_data.py et calcule les pourcentages."""

from pathlib import Path

import pandas as pd

DOSSIER_PREPARE = Path(__file__).resolve().parent / "data" / "processed"

# Avant 5 h, il y a trop peu de vols pour qu'un pourcentage ait du sens (moins de 15 000 sur l'année).
HEURES = range(5, 24)
MOIS = range(1, 13)
# En dessous, un pourcentage bouge trop au moindre vol : on préfère ne pas l'afficher.
SEUIL_VOLS_AFFICHES = 100
# Même seuil que le notebook pour comparer les aéroports entre eux.
SEUIL_AEROPORT_COMPARABLE = 10_000

NOMS_COMPAGNIES = {
    "Alaska Airlines Inc.": "Alaska Airlines",
    "American Airlines Inc.": "American Airlines",
    "American Eagle Airlines Inc.": "American Eagle",
    "Atlantic Southeast Airlines": "Atlantic Southeast",
    "Delta Air Lines Inc.": "Delta",
    "Frontier Airlines Inc.": "Frontier",
    "Hawaiian Airlines Inc.": "Hawaiian Airlines",
    "JetBlue Airways": "JetBlue",
    "Skywest Airlines Inc.": "SkyWest",
    "Southwest Airlines Co.": "Southwest",
    "Spirit Air Lines": "Spirit",
    "US Airways Inc.": "US Airways",
    "United Air Lines Inc.": "United",
    "Virgin America": "Virgin America",
}
MINUTES_PAR_CAUSE = {
    "minutes_avion": "Avion arrivé en retard",
    "minutes_compagnie": "Compagnie",
    "minutes_systeme": "Système aérien",
    "minutes_meteo": "Météo extrême",
}

resume = pd.read_parquet(DOSSIER_PREPARE / "resume.parquet").set_index("categorie")["vols"]
causes = pd.read_parquet(DOSSIER_PREPARE / "causes.parquet").set_index("cause")["minutes"]
par_heure_compagnie = pd.read_parquet(DOSSIER_PREPARE / "par_heure_compagnie.parquet")
par_mois_compagnie = pd.read_parquet(DOSSIER_PREPARE / "par_mois_compagnie.parquet")
compagnies = pd.read_parquet(DOSSIER_PREPARE / "compagnies.parquet")
aeroports = pd.read_parquet(DOSSIER_PREPARE / "aeroports.parquet")
avion_precedent = pd.read_parquet(DOSSIER_PREPARE / "avion_precedent.parquet").set_index("precedent_en_retard")


def pourcentage(part, total):
    return part / total * 100


def _selectionner(table, compagnie):
    return table if compagnie is None else table[table["COMPAGNIE"] == compagnie]


def _part_en_retard(groupes):
    """Part de vols en retard, sur les vols arrivés, vide quand il y a trop peu de vols."""
    parts = pourcentage(groupes["vols_en_retard"], groupes["vols_arrives"])
    return parts.where(groupes["vols_arrives"] >= SEUIL_VOLS_AFFICHES)


def retard_selon_vol_precedent():
    """Part de vols en retard selon le vol précédent du même avion : False = à l'heure, True = en retard."""
    return _part_en_retard(avion_precedent)


def retard_par_heure(compagnie=None):
    """Part de vols en retard par heure de départ prévue."""
    colonnes = ["vols_arrives", "vols_en_retard"]
    heures = _selectionner(par_heure_compagnie, compagnie).groupby("HEURE")[colonnes].sum()
    return _part_en_retard(heures.reindex(HEURES))


def chiffres_par_mois(compagnie=None):
    """Part de vols en retard et part de vols annulés, pour chaque mois."""
    colonnes = ["vols", "vols_arrives", "vols_en_retard", "vols_annules"]
    mois = _selectionner(par_mois_compagnie, compagnie).groupby("MONTH")[colonnes].sum().reindex(MOIS)
    return pd.DataFrame({
        "retard": _part_en_retard(mois),
        "annules": pourcentage(mois["vols_annules"], mois["vols"]),
    })


def parts_causes():
    """Part de chaque cause dans le total des minutes de retard, de la plus grande à la plus petite."""
    return pourcentage(causes, causes.sum()).sort_values(ascending=False)


def minutes_par_vol_par_heure():
    """Minutes de retard par vol arrivé, pour chaque cause et chaque heure de départ prévue."""
    colonnes = ["vols_arrives", *MINUTES_PAR_CAUSE]
    heures = par_heure_compagnie.groupby("HEURE")[colonnes].sum().reindex(HEURES)
    minutes = heures[list(MINUTES_PAR_CAUSE)].div(heures["vols_arrives"], axis=0)
    return minutes.rename(columns=MINUTES_PAR_CAUSE)


def retard_global():
    """Part de vols en retard sur les vols arrivés, la base des comparaisons entre compagnies."""
    return pourcentage(compagnies["vols_en_retard"].sum(), compagnies["vols_arrives"].sum())


def classement_compagnies():
    """Compagnies classées de la moins en retard à la plus en retard."""
    return (
        compagnies.assign(
            nom=compagnies["COMPAGNIE"].map(NOMS_COMPAGNIES),
            retard=pourcentage(compagnies["vols_en_retard"], compagnies["vols_arrives"]),
        )
        .sort_values("retard")
        .reset_index(drop=True)
    )


def aeroports_comparables():
    """Aéroports assez gros pour être comparés, avec leur part de départs en retard."""
    gros = aeroports[aeroports["vols_depart"] >= SEUIL_AEROPORT_COMPARABLE]
    return gros.assign(retard=pourcentage(gros["departs_en_retard"], gros["vols_partis"]))


def lien_taille_retard():
    """Corrélation de rang entre la taille d'un aéroport et ses départs en retard."""
    gros = aeroports_comparables()
    return gros["vols_depart"].rank().corr(gros["retard"].rank())


def plus_gros_aeroports(nombre=30):
    """Les plus gros aéroports, classés du moins en retard au plus en retard."""
    return aeroports_comparables().nlargest(nombre, "vols_depart").sort_values("retard")
