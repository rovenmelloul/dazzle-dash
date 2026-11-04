"""Réagit aux actions de l'utilisateur : ici, le choix d'une compagnie sur la page « Quand ? »."""

import math

from dash import Input, Output

from app import app
from data import NOMS_COMPAGNIES, chiffres_par_mois, retard_par_heure
from figures import NOMS_MOIS, barres_mois, courbe_heures, format_pct


def phrase_heures(compagnie, nom):
    retards = retard_par_heure(compagnie)
    sujet = f"Chez {nom}" if nom else "Toutes compagnies confondues"
    if math.isnan(retards[6]) or math.isnan(retards[20]):
        return f"{sujet}, il y a trop peu de vols à 6 h ou à 20 h pour comparer ces deux horaires."
    return f"{sujet}, {format_pct(retards[6])} des vols de 6 h arrivent en retard, contre {format_pct(retards[20])} de ceux de 20 h."


def phrase_mois(compagnie):
    pires = chiffres_par_mois(compagnie)["retard"].nlargest(2)
    mois = [f"{NOMS_MOIS[numero - 1]} ({format_pct(part)})" for numero, part in pires.items()]
    return f"Les deux mois les plus difficiles : {mois[0]} et {mois[1]}."


@app.callback(
    Output("courbe-heures", "figure"),
    Output("phrase-heures", "children"),
    Output("barres-mois", "figure"),
    Output("phrase-mois", "children"),
    Input("choix-compagnie", "value"),
)
def filtrer_par_compagnie(choix):
    # La valeur vient du navigateur : tout ce qui n'est pas une compagnie connue revient à « toutes ».
    compagnie = choix if choix in NOMS_COMPAGNIES else None
    nom = NOMS_COMPAGNIES.get(compagnie)
    return courbe_heures(compagnie, nom), phrase_heures(compagnie, nom), barres_mois(compagnie), phrase_mois(compagnie)
