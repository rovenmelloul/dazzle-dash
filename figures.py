"""Dessine les graphiques. Partagé par layout.py (pages fixes) et callbacks.py (filtre)."""

import math

import numpy as np
import plotly.graph_objects as go

from data import (
    aeroports_comparables,
    chiffres_par_mois,
    classement_compagnies,
    minutes_par_vol_par_heure,
    parts_causes,
    pourcentage,
    resume,
    retard_global,
    retard_par_heure,
)

# Une couleur suit toujours la même chose d'un graphique à l'autre.
COULEURS_RESUME = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
COULEURS_CAUSES = {
    "Avion arrivé en retard": "#2a78d6",
    "Compagnie": "#eb6834",
    "Système aérien": "#1baf7a",
    "Météo extrême": "#eda100",
    "Sûreté": "#e87ba4",
}
COULEUR_PRINCIPALE = "#2a78d6"
COULEUR_ATTENUEE = "#86b6ef"
COULEUR_REPERE = "#898781"
COULEUR_SURFACE = "#fcfcfb"
COULEUR_TEXTE = "#0b0b0b"
COULEUR_TEXTE_SECONDAIRE = "#52514e"
COULEUR_GRILLE = "#e1e0d9"
COULEUR_AXE = "#c3c2b7"
DEGRADE_BLEU = [[0, "#86b6ef"], [0.5, "#2a78d6"], [1, "#0d366b"]]
POLICE = "system-ui, -apple-system, 'Segoe UI', sans-serif"

NOMS_MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
MOIS_COURTS = ["jan", "fév", "mar", "avr", "mai", "jun", "jul", "aoû", "sep", "oct", "nov", "déc"]


def format_decimal(valeur, decimales=1):
    """Nombre à virgule, à la française : 7.84 devient « 7,8 »."""
    return f"{valeur:.{decimales}f}".replace(".", ",")


def format_pct(valeur):
    return format_decimal(valeur) + " %"


def format_nombre(valeur):
    return f"{valeur:,}".replace(",", " ")


def mettre_en_forme(figure, hauteur):
    """Applique le style commun : fond transparent, virgule décimale, zoom désactivé."""
    figure.update_layout(
        height=hauteur,
        margin={"l": 0, "r": 8, "t": 8, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": POLICE, "color": COULEUR_TEXTE_SECONDAIRE, "size": 13},
        separators=", ",
        dragmode=False,
        showlegend=False,
        hoverlabel={"bgcolor": COULEUR_SURFACE, "font": {"color": COULEUR_TEXTE}, "bordercolor": COULEUR_AXE},
    )
    return figure


def axe_valeurs(suffixe=""):
    return {"rangemode": "tozero", "ticksuffix": suffixe, "gridcolor": COULEUR_GRILLE, "zeroline": False, "fixedrange": True}


def axe_categories(valeurs, **options):
    return {
        "type": "category",
        "categoryorder": "array",
        "categoryarray": valeurs,
        "showgrid": False,
        "linecolor": COULEUR_AXE,
        "fixedrange": True,
        **options,
    }


def etiqueter_point(figure, x, y, texte, decalage_x=0, decalage_y=14):
    figure.add_annotation(
        x=x,
        y=y,
        text=texte,
        showarrow=False,
        xshift=decalage_x,
        yshift=decalage_y,
        font={"color": COULEUR_TEXTE, "size": 13},
        # Le fond garde le chiffre lisible quand une courbe passe derrière.
        bgcolor=COULEUR_SURFACE,
    )


def barre_100_vols():
    figure = go.Figure()
    for (categorie, vols), couleur in zip(resume.items(), COULEURS_RESUME):
        part = pourcentage(vols, resume.sum())
        figure.add_bar(
            y=["Tous les vols"],
            x=[part],
            orientation="h",
            marker={"color": couleur, "line": {"color": COULEUR_SURFACE, "width": 2}},
            hovertemplate=f"{categorie} : {format_pct(part)}<br>{format_nombre(vols)} vols<extra></extra>",
        )
    mettre_en_forme(figure, 70)
    figure.update_layout(
        barmode="stack",
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        xaxis={"visible": False, "range": [0, 100], "fixedrange": True},
        yaxis={"visible": False, "fixedrange": True},
    )
    return figure


def courbe_heures(compagnie=None, nom_compagnie=None):
    """Courbe du risque par heure. Avec une compagnie, la moyenne reste affichée pour comparer."""
    ensemble = retard_par_heure()
    etiquettes = [f"{heure} h" for heure in ensemble.index]
    figure = go.Figure()
    if compagnie is None:
        courbe = ensemble
    else:
        courbe = retard_par_heure(compagnie)
        figure.add_scatter(
            x=etiquettes,
            y=ensemble,
            mode="lines",
            name="Toutes les compagnies",
            line={"color": COULEUR_REPERE, "width": 2},
            hovertemplate="%{y:.1f} %",
        )
    figure.add_scatter(
        x=etiquettes,
        y=courbe,
        mode="lines",
        name=nom_compagnie or "Toutes les compagnies",
        line={"color": COULEUR_PRINCIPALE, "width": 2},
        hovertemplate="%{y:.1f} %",
    )
    reperes = [heure for heure in (6, 20) if not math.isnan(courbe[heure])]
    figure.add_scatter(
        x=[f"{heure} h" for heure in reperes],
        y=[courbe[heure] for heure in reperes],
        mode="markers",
        marker={"color": COULEUR_PRINCIPALE, "size": 9, "line": {"color": COULEUR_SURFACE, "width": 2}},
        hoverinfo="skip",
        showlegend=False,
    )
    # À 6 h la courbe monte : l'étiquette passe dessous, à droite, pour ne pas la toucher.
    decalages = {6: {"decalage_x": 24, "decalage_y": -12}, 20: {}}
    for heure in reperes:
        etiqueter_point(figure, f"{heure} h", courbe[heure], format_pct(courbe[heure]), **decalages[heure])
    mettre_en_forme(figure, 340)
    figure.update_layout(
        hovermode="x unified",
        showlegend=compagnie is not None,
        legend={"orientation": "h", "x": 0, "y": 1.12, "bgcolor": "rgba(0,0,0,0)"},
        margin={"l": 0, "r": 8, "t": 36 if compagnie else 8, "b": 0},
        xaxis=axe_categories(etiquettes, nticks=10),
        yaxis=axe_valeurs(" %"),
    )
    return figure


def barres_mois(compagnie=None):
    """Barres par mois, avec les deux mois les plus difficiles mis en avant."""
    chiffres = chiffres_par_mois(compagnie)
    pires = chiffres["retard"].nlargest(2).index
    couleurs = [COULEUR_PRINCIPALE if mois in pires else COULEUR_ATTENUEE for mois in chiffres.index]
    # Deux mois voisins : leurs chiffres se toucheraient sur téléphone, seul le pire garde le sien.
    voisins = abs(pires[0] - pires[1]) == 1
    chiffres_ecrits = pires[:1] if voisins else pires
    figure = go.Figure(
        go.Bar(
            x=MOIS_COURTS,
            y=chiffres["retard"],
            marker={"color": couleurs, "cornerradius": 4},
            text=[format_pct(chiffres["retard"][mois]) if mois in chiffres_ecrits else "" for mois in chiffres.index],
            textposition="outside",
            constraintext="none",
            textfont={"color": COULEUR_TEXTE, "size": 13},
            cliponaxis=False,
            customdata=np.column_stack([NOMS_MOIS, chiffres["annules"]]),
            hovertemplate="%{customdata[0]}<br>En retard : %{y:.1f} %<br>Annulés : %{customdata[1]:.1f} %<extra></extra>",
        )
    )
    mettre_en_forme(figure, 340)
    figure.update_layout(
        bargap=0.35,
        margin={"l": 0, "r": 8, "t": 24, "b": 0},
        xaxis=axe_categories(MOIS_COURTS),
        yaxis=axe_valeurs(" %"),
    )
    return figure


def barres_causes():
    parts = parts_causes().sort_values()
    figure = go.Figure(
        go.Bar(
            x=parts,
            y=parts.index,
            orientation="h",
            marker={"color": [COULEURS_CAUSES[cause] for cause in parts.index], "cornerradius": 4},
            text=[format_pct(part) for part in parts],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y} : %{x:.1f} % des minutes de retard<extra></extra>",
        )
    )
    mettre_en_forme(figure, 230)
    figure.update_layout(
        bargap=0.3,
        margin={"l": 0, "r": 56, "t": 0, "b": 0},
        xaxis={"visible": False, "rangemode": "tozero", "fixedrange": True},
        yaxis=axe_categories(list(parts.index), automargin=True, linecolor=COULEUR_AXE),
    )
    return figure


def courbe_domino():
    """Minutes de retard par vol selon l'heure : seul l'effet domino s'envole dans la journée."""
    minutes = minutes_par_vol_par_heure()
    etiquettes = [f"{heure} h" for heure in minutes.index]
    figure = go.Figure()
    for cause in minutes.columns:
        figure.add_scatter(
            x=etiquettes,
            y=minutes[cause],
            mode="lines",
            name=cause,
            line={"color": COULEURS_CAUSES[cause], "width": 2},
            hovertemplate="%{y:.1f} min",
        )
    domino = minutes["Avion arrivé en retard"]
    # Seul le pic est écrit : à 6 h, l'étiquette toucherait la courbe météo, et la phrase au-dessus donne déjà la valeur.
    etiqueter_point(figure, "20 h", domino[20], format_decimal(domino[20]) + " min")
    mettre_en_forme(figure, 320)
    figure.update_layout(
        hovermode="x unified",
        xaxis=axe_categories(etiquettes, nticks=10),
        yaxis=axe_valeurs(" min"),
    )
    return figure


def barres_compagnies():
    # Plotly dessine la première ligne en bas : ce tri place la compagnie la plus en retard en haut.
    classement = classement_compagnies()
    moyenne = retard_global()
    figure = go.Figure(
        go.Bar(
            x=classement["retard"],
            y=classement["nom"],
            orientation="h",
            marker={"color": COULEUR_PRINCIPALE, "cornerradius": 4},
            text=[format_pct(part) for part in classement["retard"]],
            textposition="outside",
            cliponaxis=False,
            customdata=classement["vols"],
            hovertemplate="%{y} : %{x:.1f} % en retard<br>%{customdata:,} vols<extra></extra>",
        )
    )
    mettre_en_forme(figure, 470)
    figure.add_shape(
        type="line",
        x0=moyenne,
        x1=moyenne,
        y0=0,
        y1=1,
        yref="paper",
        line={"color": COULEUR_REPERE, "width": 1, "dash": "dot"},
        layer="above",
    )
    figure.add_annotation(
        x=moyenne,
        y=1,
        yref="paper",
        yanchor="bottom",
        yshift=2,
        text=f"Moyenne : {format_pct(moyenne)}",
        showarrow=False,
        font={"color": COULEUR_TEXTE_SECONDAIRE, "size": 13},
    )
    figure.update_layout(
        bargap=0.3,
        margin={"l": 0, "r": 56, "t": 28, "b": 0},
        xaxis={"visible": False, "rangemode": "tozero", "fixedrange": True},
        yaxis=axe_categories(list(classement["nom"]), automargin=True),
    )
    return figure


def carte_aeroports():
    # Les gros cercles sont dessinés d'abord, pour ne pas cacher les petits.
    gros = aeroports_comparables().sort_values("vols_depart", ascending=False)
    survol = [
        f"<b>{ligne.CITY} ({ligne.CODE})</b><br>{format_pct(ligne.retard)} de départs en retard<br>{format_nombre(ligne.vols_depart)} vols au départ"
        for ligne in gros.itertuples()
    ]
    figure = go.Figure(
        go.Scattergeo(
            lat=gros["LATITUDE"],
            lon=gros["LONGITUDE"],
            mode="markers",
            text=survol,
            hovertemplate="%{text}<extra></extra>",
            marker={
                "size": gros["vols_depart"],
                "sizemode": "area",
                "sizeref": 2 * gros["vols_depart"].max() / 36**2,
                "sizemin": 6,
                "color": gros["retard"],
                "colorscale": DEGRADE_BLEU,
                "line": {"color": COULEUR_SURFACE, "width": 1},
                "colorbar": {
                    "orientation": "h",
                    "title": {"text": "Part de départs en retard", "side": "top"},
                    "ticksuffix": " %",
                    "thickness": 10,
                    "len": 0.5,
                    "x": 0.5,
                    "y": -0.02,
                    "yanchor": "top",
                    "outlinewidth": 0,
                },
            },
        )
    )
    mettre_en_forme(figure, None)  # la hauteur suit la largeur de l'écran : voir .graphique-carte
    figure.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 60},
        geo={
            "scope": "usa",
            "bgcolor": "rgba(0,0,0,0)",
            "landcolor": "#f0efea",
            "subunitcolor": COULEUR_GRILLE,
            "showlakes": False,
        },
    )
    return figure
