"""Transforme les CSV bruts en petits fichiers Parquet pour l'app.

Lancement, une seule fois : uv run python scripts/prepare_data.py

Les fichiers gardent des nombres de vols, pas des pourcentages : l'app recalcule
les pourcentages après filtrage, car on ne peut pas faire la moyenne de pourcentages.
Les choix de nettoyage sont expliqués dans notebooks/eda_flights.ipynb.
"""

from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_BRUT = RACINE / "data" / "raw"
DOSSIER_PREPARE = RACINE / "data" / "processed"

SEUIL_RETARD = 15

# Colonne du CSV -> (colonne dans nos fichiers, nom affiché dans l'app)
CAUSES = {
    "LATE_AIRCRAFT_DELAY": ("minutes_avion", "Avion arrivé en retard"),
    "AIRLINE_DELAY": ("minutes_compagnie", "Compagnie"),
    "AIR_SYSTEM_DELAY": ("minutes_systeme", "Système aérien"),
    "WEATHER_DELAY": ("minutes_meteo", "Météo extrême"),
    "SECURITY_DELAY": ("minutes_surete", "Sûreté"),
}
COLONNES_MINUTES = {colonne: nom for colonne, (nom, _) in CAUSES.items()}
COLONNES_AEROPORT = ["ORIGIN_AIRPORT", "DESTINATION_AIRPORT"]


def traduction_octobre(flights):
    """Relie les numéros d'aéroport d'octobre aux codes à trois lettres des autres mois."""
    # Ces fichiers ne sont pas en UTF-8. keep_default_na=False évite que le code "NA" soit lu comme une case vide.
    options = {"dtype": str, "encoding": "latin-1", "keep_default_na": False}
    table_numeros = pd.read_csv(DOSSIER_BRUT / "L_AIRPORT_ID.csv", **options)
    table_lettres = pd.read_csv(DOSSIER_BRUT / "L_AIRPORT.csv", **options)

    est_octobre = flights["MONTH"] == 10
    codes_octobre = pd.unique(flights.loc[est_octobre, COLONNES_AEROPORT].values.ravel())
    codes_autres_mois = pd.unique(flights.loc[~est_octobre, COLONNES_AEROPORT].values.ravel())

    correspondance = table_numeros[table_numeros["Code"].isin(codes_octobre)].merge(
        table_lettres[table_lettres["Code"].isin(codes_autres_mois)],
        on="Description",
        suffixes=("_numero", "_lettres"),
    )
    traduction = correspondance.set_index("Code_numero")["Code_lettres"]
    # Le nom de cet aéroport diffère entre les deux tables : le lien a été confirmé par les distances.
    traduction["14027"] = "PBI"
    return traduction


def charger_vols(airports):
    colonnes = [
        "MONTH",
        "AIRLINE",
        *COLONNES_AEROPORT,
        "SCHEDULED_DEPARTURE",
        "DEPARTURE_DELAY",
        "ARRIVAL_DELAY",
        "CANCELLED",
        "DIVERTED",
        *CAUSES,
    ]
    types = {colonne: str for colonne in COLONNES_AEROPORT}
    flights = pd.read_csv(DOSSIER_BRUT / "flights.csv", usecols=colonnes, dtype=types)

    traduction = traduction_octobre(flights)
    for colonne in COLONNES_AEROPORT:
        flights[colonne] = flights[colonne].map(traduction).fillna(flights[colonne])
        if not flights[colonne].isin(airports["IATA_CODE"]).all():
            raise ValueError(f"Aéroport inconnu dans {colonne}")

    flights["HEURE"] = flights["SCHEDULED_DEPARTURE"] // 100
    flights["EN_RETARD"] = flights["ARRIVAL_DELAY"] >= SEUIL_RETARD

    noms_compagnies = pd.read_csv(DOSSIER_BRUT / "airlines.csv").set_index("IATA_CODE")["AIRLINE"]
    flights["COMPAGNIE"] = flights["AIRLINE"].map(noms_compagnies)
    return flights.rename(columns=COLONNES_MINUTES)


def agreger(flights, cles):
    """Compte les vols et additionne les minutes de retard par groupe."""
    return (
        flights.groupby(cles)
        .agg(
            vols=("MONTH", "size"),
            vols_arrives=("ARRIVAL_DELAY", "count"),
            vols_en_retard=("EN_RETARD", "sum"),
            vols_annules=("CANCELLED", "sum"),
            **{nom: (nom, "sum") for nom in COLONNES_MINUTES.values()},
        )
        .reset_index()
    )


def resumer(flights):
    return pd.DataFrame({
        "categorie": ["À l'heure", "En retard", "Annulé", "Dévié"],
        "vols": [
            (flights["ARRIVAL_DELAY"] < SEUIL_RETARD).sum(),
            flights["EN_RETARD"].sum(),
            (flights["CANCELLED"] == 1).sum(),
            (flights["DIVERTED"] == 1).sum(),
        ],
    })


def totaliser_causes(flights):
    return pd.DataFrame({
        "cause": [nom_affiche for _, nom_affiche in CAUSES.values()],
        "minutes": [flights[colonne].sum() for colonne, _ in CAUSES.values()],
    })


def agreger_aeroports(flights, airports):
    flights = flights.assign(DEPART_EN_RETARD=flights["DEPARTURE_DELAY"] >= SEUIL_RETARD)
    departs = flights.groupby("ORIGIN_AIRPORT").agg(
        vols_depart=("MONTH", "size"),
        vols_partis=("DEPARTURE_DELAY", "count"),
        departs_en_retard=("DEPART_EN_RETARD", "sum"),
        vols_annules=("CANCELLED", "sum"),
    )
    arrivees = flights.groupby("DESTINATION_AIRPORT").agg(
        vols_arrives=("ARRIVAL_DELAY", "count"),
        arrivees_en_retard=("EN_RETARD", "sum"),
    )
    comptes = departs.join(arrivees, how="outer").fillna(0).astype(int)
    # Trois aéroports n'ont pas de coordonnées : ils restent dans les chiffres, mais pas sur la carte.
    infos = airports.set_index("IATA_CODE")[["AIRPORT", "CITY", "STATE", "LATITUDE", "LONGITUDE"]]
    return infos.join(comptes, how="inner").rename_axis("CODE").reset_index()


def verifier(fichiers):
    """Compare les résultats aux chiffres du notebook, et s'arrête au moindre écart."""
    resume = fichiers["resume"].set_index("categorie")["vols"]
    heures = fichiers["par_heure_compagnie"].groupby("HEURE")[["vols_arrives", "vols_en_retard"]].sum()
    mois = fichiers["par_mois_compagnie"].groupby("MONTH")[["vols_arrives", "vols_en_retard", "vols", "vols_annules"]].sum()
    causes = fichiers["causes"].set_index("cause")["minutes"]
    compagnies = fichiers["compagnies"].set_index("COMPAGNIE")
    aeroports = fichiers["aeroports"].set_index("CODE")

    controles = [
        ("vols au total", resume.sum(), 5_819_079),
        ("% en retard, tous vols", round(resume["En retard"] / resume.sum() * 100, 2), 18.28),
        ("% à l'heure, tous vols", round(resume["À l'heure"] / resume.sum() * 100, 2), 79.92),
        ("% en retard à 6 h", round(heures.loc[6, "vols_en_retard"] / heures.loc[6, "vols_arrives"] * 100, 1), 9.0),
        ("% en retard à 20 h", round(heures.loc[20, "vols_en_retard"] / heures.loc[20, "vols_arrives"] * 100, 1), 26.3),
        ("% en retard en juin", round(mois.loc[6, "vols_en_retard"] / mois.loc[6, "vols_arrives"] * 100, 1), 23.5),
        ("% annulés en février", round(mois.loc[2, "vols_annules"] / mois.loc[2, "vols"] * 100, 2), 4.78),
        ("% effet domino", round(causes["Avion arrivé en retard"] / causes.sum() * 100, 1), 39.8),
        (
            "% en retard chez Spirit",
            round(compagnies.loc["Spirit Air Lines", "vols_en_retard"] / compagnies.loc["Spirit Air Lines", "vols_arrives"] * 100, 1),
            29.7,
        ),
        ("vols au départ d'Atlanta", aeroports.loc["ATL", "vols_depart"], 379_424),
        ("% départs en retard à Baltimore", round(aeroports.loc["BWI", "departs_en_retard"] / aeroports.loc["BWI", "vols_partis"] * 100, 1), 24.1),
        ("% annulés à LaGuardia", round(aeroports.loc["LGA", "vols_annules"] / aeroports.loc["LGA", "vols_depart"] * 100, 2), 4.30),
    ]
    for nom, obtenu, attendu in controles:
        if obtenu != attendu:
            raise ValueError(f"{nom} : obtenu {obtenu}, attendu {attendu}")
        print(f"OK {nom} : {obtenu}")


def main():
    airports = pd.read_csv(DOSSIER_BRUT / "airports.csv")
    flights = charger_vols(airports)

    fichiers = {
        "resume": resumer(flights),
        "par_heure_compagnie": agreger(flights, ["HEURE", "COMPAGNIE"]),
        "par_mois_compagnie": agreger(flights, ["MONTH", "COMPAGNIE"]),
        "causes": totaliser_causes(flights),
        "compagnies": agreger(flights, ["COMPAGNIE"]),
        "aeroports": agreger_aeroports(flights, airports),
    }
    verifier(fichiers)

    DOSSIER_PREPARE.mkdir(parents=True, exist_ok=True)
    for nom, table in fichiers.items():
        chemin = DOSSIER_PREPARE / f"{nom}.parquet"
        table.to_parquet(chemin, index=False)
        print(f"{chemin.name} : {len(table)} lignes, {chemin.stat().st_size / 1024:.1f} Ko")


if __name__ == "__main__":
    main()
