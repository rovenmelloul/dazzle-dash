"""Décrit ce qu'on voit : le menu, les pages et leurs graphiques."""

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html

from data import causes, pourcentage, resume, retard_par_heure

COULEURS_RESUME = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
COULEUR_SURFACE = "#fcfcfb"
GRAPHIQUE_SIMPLE = {"displayModeBar": False}

MENU = {
    "/": "L'essentiel",
    "/quand": "Quand ?",
    "/pourquoi": "Pourquoi ?",
    "/avec-qui-et-ou": "Avec qui et où ?",
}


def format_pct(valeur):
    return f"{valeur:.1f}".replace(".", ",") + " %"


def format_nombre(valeur):
    return f"{valeur:,}".replace(",", " ")


def menu():
    liens = [dbc.NavLink(nom, href=chemin, active="exact") for chemin, nom in MENU.items()]
    return dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("Dazzle Dash", href="/"),
            dbc.Nav(liens, pills=True, className="menu-pages"),
        ]),
        color="white",
        dark=False,
        className="barre-menu",
    )


def en_tete(question, message):
    return html.Header([
        html.P(question, className="question"),
        html.H1(message),
    ])


def chiffre_cle(valeur, libelle, detail):
    return dbc.Col(
        html.Div(
            [
                html.P(libelle, className="chiffre-libelle"),
                html.P(valeur, className="chiffre-valeur"),
                html.P(detail, className="chiffre-detail"),
            ],
            className="carte chiffre-cle",
        ),
        xs=12,
        sm=6,
        lg=3,
    )


def legende_100_vols():
    # Une légende HTML passe à la ligne sur téléphone, contrairement à celle de Plotly qui défile.
    elements = [
        html.Li(
            [
                html.Span(className="pastille", style={"backgroundColor": couleur}),
                f"{categorie} : {format_pct(pourcentage(vols, resume.sum()))}",
            ]
        )
        for (categorie, vols), couleur in zip(resume.items(), COULEURS_RESUME)
    ]
    return html.Ul(elements, className="legende")


def barre_100_vols():
    figure = go.Figure()
    for (categorie, vols), couleur in zip(resume.items(), COULEURS_RESUME):
        part = format_pct(pourcentage(vols, resume.sum()))
        figure.add_bar(
            y=["Tous les vols"],
            x=[pourcentage(vols, resume.sum())],
            orientation="h",
            marker={"color": couleur, "line": {"color": COULEUR_SURFACE, "width": 2}},
            hovertemplate=f"{categorie} : {part}<br>{format_nombre(vols)} vols<extra></extra>",
        )
    figure.update_layout(
        barmode="stack",
        height=70,
        showlegend=False,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "system-ui, -apple-system, 'Segoe UI', sans-serif", "color": "#52514e", "size": 14},
        xaxis={"visible": False, "range": [0, 100], "fixedrange": True},
        yaxis={"visible": False, "fixedrange": True},
    )
    return figure


def page_essentiel():
    total = resume.sum()
    retards = retard_par_heure()
    return html.Div([
        en_tete("Quelle est l'ampleur des retards ?", "Près d'un vol sur cinq n'arrive pas à l'heure"),
        html.P(
            f"Prendre le vol de 6 h ou celui de 20 h, ce n'est pas le même risque : "
            f"{format_pct(retards[6])} des vols de 6 h arrivent en retard, contre {format_pct(retards[20])} de ceux de 20 h.",
            className="accroche",
        ),
        dbc.Row(
            [
                chiffre_cle(
                    format_pct(pourcentage(resume["À l'heure"], total)),
                    "Vols à l'heure",
                    "Moins de 15 minutes de retard à l'arrivée",
                ),
                chiffre_cle(
                    format_pct(pourcentage(resume["En retard"], total)),
                    "Vols en retard",
                    "15 minutes de retard ou plus à l'arrivée",
                ),
                chiffre_cle(
                    format_pct(pourcentage(resume["Annulé"], total)),
                    "Vols annulés",
                    "Rare, mais très gênant pour le passager",
                ),
                chiffre_cle(
                    format_pct(pourcentage(causes["Avion arrivé en retard"], causes.sum())),
                    "Effet domino",
                    "Part des minutes de retard due à un avion déjà arrivé en retard",
                ),
            ],
            className="g-3",
        ),
        html.Section(
            [
                html.H2("Sur 100 vols, 80 arrivent à l'heure et 18 arrivent en retard"),
                dcc.Graph(figure=barre_100_vols(), config=GRAPHIQUE_SIMPLE),
                legende_100_vols(),
            ],
            className="carte",
        ),
        html.P(
            "Source : vols intérieurs américains de 2015, données publiques du Bureau of Transportation Statistics, "
            f"soit {format_nombre(total)} vols. Ces données ne contiennent aucune information sur les passagers.",
            className="note",
        ),
        dbc.Button("Suite : quand le risque monte-t-il ?", href="/quand", className="bouton-suite"),
    ])


def page_en_construction(nom):
    return en_tete(nom, "Page en construction")


def page_introuvable():
    return en_tete("Page introuvable", "Cette adresse n'existe pas")


PAGES = {
    "/": page_essentiel(),
    "/quand": page_en_construction("Quand ?"),
    "/pourquoi": page_en_construction("Pourquoi ?"),
    "/avec-qui-et-ou": page_en_construction("Avec qui et où ?"),
}

racine = html.Div([
    dcc.Location(id="adresse"),
    menu(),
    dbc.Container(id="contenu-page", className="page"),
])
