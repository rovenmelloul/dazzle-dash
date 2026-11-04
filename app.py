"""Crée l'application Dash et charge le style."""

import dash_bootstrap_components as dbc
from dash import Dash

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    title="Dazzle Dash : les retards aériens de 2015",
    # Le filtre de la page « Quand ? » n'existe pas au démarrage : il arrive quand on ouvre cette page.
    suppress_callback_exceptions=True,
)
# La page est en français : le navigateur et les lecteurs d'écran doivent le savoir.
app.index_string = app.index_string.replace("<html>", '<html lang="fr">')
