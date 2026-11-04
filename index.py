"""Point d'entrée : assemble l'app, choisit la page selon l'adresse et lance le serveur.

Lancement : uv run python index.py
"""

from dash import Input, Output

from app import app
from layout import PAGES, page_introuvable, racine

app.layout = racine


@app.callback(Output("contenu-page", "children"), Input("adresse", "pathname"))
def afficher_page(chemin):
    return PAGES.get(chemin, page_introuvable())


if __name__ == "__main__":
    # Le mode debug reste désactivé par défaut : DASH_DEBUG=true l'active en développement.
    app.run()
