"""Décrit ce qu'on voit : le menu et le contenu de chaque page."""

import dash_bootstrap_components as dbc
from dash import dcc, html

from data import (
    NOMS_COMPAGNIES,
    SEUIL_VOLS_AFFICHES,
    aeroports_comparables,
    causes,
    chiffres_par_mois,
    classement_compagnies,
    lien_taille_retard,
    minutes_par_vol_par_heure,
    parts_causes,
    retard_selon_vol_precedent,
    plus_gros_aeroports,
    pourcentage,
    resume,
    retard_par_heure,
)
from figures import (
    COULEURS_CAUSES,
    COULEURS_RESUME,
    barre_100_vols,
    barres_causes,
    barres_compagnies,
    carte_aeroports,
    courbe_domino,
    format_nombre,
    format_pct,
)

GRAPHIQUE_SIMPLE = {"displayModeBar": False}
TOUTES_COMPAGNIES = "toutes"

MENU = {
    "/": "L'essentiel",
    "/quand": "Quand ?",
    "/pourquoi": "Pourquoi ?",
    "/avec-qui-et-ou": "Avec qui et où ?",
}


def format_minutes(valeur):
    return f"{valeur:.1f}".replace(".", ",") + " minutes"


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


def en_tete(question, message, accroche=None):
    elements = [html.P(question, className="question"), html.H1(message)]
    if accroche:
        elements.append(html.P(accroche, className="accroche"))
    return html.Header(elements)


def graphique(description, **options):
    """Graphique avec une description pour les lecteurs d'écran."""
    return html.Div(
        dcc.Graph(config=GRAPHIQUE_SIMPLE, **options),
        role="img",
        **{"aria-label": description},
    )


def bouton_suite(texte, chemin):
    return dbc.Button(texte, href=chemin, className="bouton-suite")


def legende(elements):
    # Une légende HTML passe à la ligne sur téléphone, contrairement à celle de Plotly qui défile.
    lignes = [
        html.Li([html.Span(className="pastille", style={"backgroundColor": couleur}), texte])
        for texte, couleur in elements
    ]
    return html.Ul(lignes, className="legende")


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


def page_essentiel():
    total = resume.sum()
    retards = retard_par_heure()
    parts = [
        (f"{categorie} : {format_pct(pourcentage(vols, total))}", couleur)
        for (categorie, vols), couleur in zip(resume.items(), COULEURS_RESUME)
    ]
    return html.Div([
        en_tete(
            "Quelle est l'ampleur des retards ?",
            "Près d'un vol sur cinq n'arrive pas à l'heure",
            f"Prendre le vol de 6 h ou celui de 20 h, ce n'est pas le même risque : "
            f"{format_pct(retards[6])} des vols de 6 h arrivent en retard, contre {format_pct(retards[20])} de ceux de 20 h.",
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
                graphique(
                    "Barre découpée en quatre parts : à l'heure, en retard, annulé et dévié. Les valeurs sont dans la légende.",
                    figure=barre_100_vols(),
                ),
                legende(parts),
            ],
            className="carte",
        ),
        html.P(
            "Source : vols intérieurs américains de 2015, données publiques du Bureau of Transportation Statistics, "
            f"soit {format_nombre(total)} vols. Ces données ne contiennent aucune information sur les passagers.",
            className="note",
        ),
        bouton_suite("Suite : quand le risque monte-t-il ?", "/quand"),
    ])


def page_quand():
    fevrier = chiffres_par_mois().loc[2, "annules"]
    options = [{"label": "Toutes les compagnies", "value": TOUTES_COMPAGNIES}]
    options += [{"label": nom, "value": valeur} for valeur, nom in sorted(NOMS_COMPAGNIES.items(), key=lambda paire: paire[1])]
    return html.Div([
        en_tete(
            "À quel moment le risque monte-t-il ?",
            "Le risque grimpe de 9\u00a0% à 6\u00a0h à 26\u00a0% à 20\u00a0h, et février et juin sont les mois les plus difficiles",
        ),
        html.Div(
            [
                html.Label("Voir une compagnie", htmlFor="choix-compagnie", className="filtre-libelle"),
                dbc.Select(id="choix-compagnie", options=options, value=TOUTES_COMPAGNIES, className="filtre-choix"),
            ],
            className="filtre",
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Section(
                        [
                            html.H2("Plus le vol part tard, plus il risque d'arriver en retard"),
                            html.P(id="phrase-heures", className="phrase", **{"aria-live": "polite"}),
                            dcc.Loading(
                                graphique(
                                    "Courbe de la part de vols en retard selon l'heure de départ prévue, de 5 h à 23 h. "
                                    "Elle monte du matin jusqu'à 20 h, puis redescend.",
                                    id="courbe-heures",
                                ),
                            ),
                        ],
                        className="carte carte-pleine",
                    ),
                    lg=7,
                ),
                dbc.Col(
                    html.Section(
                        [
                            html.H2("Certains mois sont bien plus difficiles que d'autres"),
                            html.P(id="phrase-mois", className="phrase", **{"aria-live": "polite"}),
                            dcc.Loading(
                                graphique(
                                    "Barres de la part de vols en retard pour chacun des douze mois.",
                                    id="barres-mois",
                                ),
                            ),
                        ],
                        className="carte carte-pleine",
                    ),
                    lg=5,
                ),
            ],
            className="g-3",
        ),
        html.P(
            f"Toutes compagnies confondues, février a aussi le plus d'annulations : {format_pct(fevrier)} des vols. "
            "Pour juin, la météo est une explication probable, mais ces données ne le prouvent pas.",
            className="note",
        ),
        html.P(
            "Calcul sur les vols arrivés à destination, selon leur heure de départ prévue. Sont masqués les vols d'avant "
            f"5 h, très peu nombreux, et, pour une compagnie, les heures et les mois de moins de {SEUIL_VOLS_AFFICHES} vols. "
            "Survole un point ou une barre pour voir le détail.",
            className="note",
        ),
        bouton_suite("Suite : d'où viennent ces retards ?", "/pourquoi"),
    ])


def explication_cause(cause, texte, part):
    return html.Li(
        [
            html.Span(className="pastille", style={"backgroundColor": COULEURS_CAUSES[cause]}),
            html.Strong(f"{cause} ({format_pct(part)}) : "),
            texte,
        ]
    )


def resultat_avion(libelle, part):
    return dbc.Col(
        [
            html.P(libelle, className="chiffre-libelle"),
            html.P(format_pct(part), className="chiffre-valeur"),
            html.P("des vols suivants arrivent en retard", className="chiffre-detail"),
        ],
        xs=12,
        sm=6,
    )


def page_pourquoi():
    parts = parts_causes()
    selon_precedent = retard_selon_vol_precedent()
    minutes = minutes_par_vol_par_heure()
    domino = minutes["Avion arrivé en retard"]
    compagnie = minutes["Compagnie"]
    courbes = [(cause, COULEURS_CAUSES[cause]) for cause in minutes.columns]
    return html.Div([
        en_tete(
            "D'où viennent les retards ?",
            "La première cause est l'effet domino : un avion en retard repart en retard",
            f"Le même avion enchaîne plusieurs vols dans la journée. {format_pct(parts['Avion arrivé en retard'])} des minutes "
            "de retard viennent d'un avion arrivé trop tard de son vol précédent.",
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Section(
                        [
                            html.H2("L'effet domino pèse plus que chaque autre cause"),
                            graphique(
                                "Barres de la part des minutes de retard par cause. Les valeurs sont écrites à côté de chaque barre.",
                                figure=barres_causes(),
                            ),
                            html.Ul(
                                [
                                    explication_cause(
                                        "Avion arrivé en retard",
                                        "le vol précédent du même avion a fini trop tard.",
                                        parts["Avion arrivé en retard"],
                                    ),
                                    explication_cause(
                                        "Compagnie",
                                        "problème de son ressort, comme une panne, l'équipage ou les bagages.",
                                        parts["Compagnie"],
                                    ),
                                    explication_cause(
                                        "Système aérien",
                                        "trafic chargé, contrôle aérien, météo ordinaire.",
                                        parts["Système aérien"],
                                    ),
                                    explication_cause(
                                        "Météo extrême",
                                        "conditions qui empêchent de voler, comme un ouragan.",
                                        parts["Météo extrême"],
                                    ),
                                    explication_cause(
                                        "Sûreté",
                                        "évacuation d'un terminal, longues files au contrôle.",
                                        parts["Sûreté"],
                                    ),
                                ],
                                className="liste-causes",
                            ),
                        ],
                        className="carte carte-pleine",
                    ),
                    lg=6,
                ),
                dbc.Col(
                    html.Section(
                        [
                            html.H2("Le matin, il n'y a presque pas d'effet domino. Le soir, c'est la première cause"),
                            html.P(
                                f"Pour un vol de 6 h : {format_minutes(domino[6])} de retard par vol en moyenne. "
                                f"Pour un vol de 20 h : {format_minutes(domino[20])}. La cause « compagnie », elle, "
                                f"bouge peu : de {format_minutes(compagnie[6])} à {format_minutes(compagnie[20])}.",
                                className="phrase",
                            ),
                            graphique(
                                "Courbes des minutes de retard par vol selon l'heure de départ prévue, pour quatre causes. "
                                "Seule la courbe de l'avion arrivé en retard monte fortement dans la journée.",
                                figure=courbe_domino(),
                            ),
                            legende(courbes),
                        ],
                        className="carte carte-pleine",
                    ),
                    lg=6,
                ),
            ],
            className="g-3",
        ),
        html.Section(
            [
                html.H2("Sur un même avion, un retard en entraîne souvent un autre"),
                html.P(
                    "On suit chaque avion au fil de sa journée, et on regarde comment son vol précédent s'est terminé.",
                    className="phrase",
                ),
                dbc.Row(
                    [
                        resultat_avion("Vol précédent à l'heure", selon_precedent[False]),
                        resultat_avion("Vol précédent en retard", selon_precedent[True]),
                    ],
                    className="g-3",
                ),
                html.P(
                    "Un lien, pas une preuve à lui seul : un même orage peut par exemple retarder les deux vols. "
                    "Calcul sur 4,3 millions de vols arrivés, dont l'avion repart de l'aéroport où il vient d'atterrir, le même jour.",
                    className="note",
                ),
            ],
            className="carte",
        ),
        html.P(
            "À lire avec prudence : la météo extrême est sous-estimée. Une météo ordinaire est comptée dans « système aérien », "
            "et un retard lié à la météo sur un vol précédent est compté dans « avion arrivé en retard ».",
            className="note",
        ),
        html.P(
            "Les causes ne sont renseignées que pour les vols arrivés avec 15 minutes de retard ou plus. Les minutes par vol "
            "sont réparties sur tous les vols arrivés. La sûreté, presque nulle, n'apparaît pas sur la courbe.",
            className="note",
        ),
        bouton_suite("Suite : avec qui et où ?", "/avec-qui-et-ou"),
    ])


def tableau_aeroports(titre, aeroports):
    lignes = [
        html.Tr([
            html.Td(f"{ligne.CITY} ({ligne.CODE})"),
            html.Td(format_nombre(ligne.vols_depart), className="nombre"),
            html.Td(format_pct(ligne.retard), className="nombre"),
        ])
        for ligne in aeroports.itertuples()
    ]
    entete = html.Thead(html.Tr([
        html.Th("Aéroport", scope="col"),
        html.Th("Vols au départ", scope="col", className="nombre"),
        html.Th("Départs en retard", scope="col", className="nombre"),
    ]))
    return dbc.Col(
        html.Div([
            html.H3(titre),
            dbc.Table([entete, html.Tbody(lignes)], className="tableau", borderless=True, size="sm"),
        ]),
        md=6,
    )


def bloc_a_retenir():
    classement = classement_compagnies()
    gros = plus_gros_aeroports()
    moins_en_retard, plus_en_retard = classement.iloc[0], classement.iloc[-1]
    retards = retard_par_heure()
    constats = [
        f"{format_pct(pourcentage(resume['En retard'], resume.sum()))} des vols arrivent en retard, et l'heure de départ change beaucoup le risque : "
        f"de {format_pct(retards[6])} à 6 h à {format_pct(retards[20])} à 20 h.",
        f"L'effet domino est la première cause, avec {format_pct(parts_causes()['Avion arrivé en retard'])} des minutes de retard.",
        f"L'écart entre compagnies va de {format_pct(moins_en_retard['retard'])} ({moins_en_retard['nom']}) à {format_pct(plus_en_retard['retard'])} ({plus_en_retard['nom']}).",
        f"Parmi les 30 plus gros aéroports, les départs en retard vont de {format_pct(gros.iloc[0]['retard'])} à {format_pct(gros.iloc[-1]['retard'])}.",
    ]
    pistes = [
        "Regarder si plus de marge entre deux vols d'un même avion limite l'effet domino en fin de journée.",
        "Étudier ce que font les compagnies et les aéroports les plus ponctuels, à conditions comparables.",
        "Refaire l'analyse sur d'autres années, pour vérifier que 2015 n'est pas une exception.",
    ]
    return html.Section(
        [
            html.H2("Ce qu'il faut retenir"),
            dbc.Row(
                [
                    dbc.Col([html.H3("Les constats"), html.Ul([html.Li(texte) for texte in constats])], md=6),
                    dbc.Col(
                        [
                            html.H3("Des pistes à étudier"),
                            html.Ul([html.Li(texte) for texte in pistes]),
                            html.P(
                                "Ce sont des pistes et non des recommandations : ces données montrent ce qui s'est passé en 2015, "
                                "pas ce qui marcherait.",
                                className="chiffre-detail",
                            ),
                        ],
                        md=6,
                    ),
                ],
                className="g-3",
            ),
        ],
        className="carte a-retenir",
    )


def page_avec_qui_et_ou():
    gros = plus_gros_aeroports()
    classement = classement_compagnies()
    lien = f"{lien_taille_retard():.2f}".replace(".", ",")
    return html.Div([
        en_tete(
            "Qu'est-ce qui change le risque ?",
            "La compagnie et l'aéroport comptent, mais la taille n'explique pas tout",
            f"En général, les gros aéroports ont plus de départs en retard, mais le lien reste moyen : {lien} sur "
            f"{len(aeroports_comparables())} aéroports, où 0 veut dire aucun lien et 1 un lien parfait. "
            f"Salt Lake City, pourtant très gros, n'a que {format_pct(gros.iloc[0]['retard'])} de départs en retard.",
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Section(
                        [
                            html.H2(
                                f"Selon la compagnie, le risque va de {format_pct(classement.iloc[0]['retard'])} "
                                f"à {format_pct(classement.iloc[-1]['retard'])}"
                            ),
                            graphique(
                                "Barres de la part de vols en retard par compagnie, de la plus en retard à la moins en retard. "
                                "Les valeurs sont écrites à côté de chaque barre.",
                                figure=barres_compagnies(),
                            ),
                        ],
                        className="carte carte-pleine",
                    ),
                    lg=5,
                ),
                dbc.Col(
                    html.Section(
                        [
                            html.H2("Les aéroports les plus en retard ne sont pas tous les plus gros"),
                            html.P(
                                "Plus le cercle est grand, plus l'aéroport a de vols. Plus il est foncé, plus ses départs "
                                "sont en retard. Survole un cercle pour voir le détail.",
                                className="phrase",
                            ),
                            graphique(
                                "Carte des États-Unis avec un cercle par aéroport. Les valeurs principales sont dans les tableaux ci-dessous.",
                                figure=carte_aeroports(),
                                className="graphique-carte",
                                responsive=True,
                            ),
                        ],
                        className="carte carte-pleine",
                    ),
                    lg=7,
                ),
            ],
            className="g-3",
        ),
        html.Section(
            [
                html.H2("Parmi les 30 plus gros aéroports"),
                dbc.Row(
                    [
                        tableau_aeroports("Les moins de départs en retard", gros.head(5)),
                        tableau_aeroports("Le plus de départs en retard", gros.tail(5).iloc[::-1]),
                    ],
                    className="g-3",
                ),
            ],
            className="carte",
        ),
        html.P(
            "Ces écarts ne sont pas une note de qualité : compagnies et aéroports n'ont ni les mêmes lignes, ni le même climat, "
            "ni le même trafic. Tous les chiffres portent uniquement sur 2015.",
            className="note",
        ),
        html.P(
            "Compagnies : vols arrivés en retard. Aéroports : départs en retard, car c'est là que l'aéroport joue sur le vol. "
            "La carte montre les aéroports d'au moins 10 000 vols au départ, sauf San Juan (Porto Rico), hors du cadre de la carte.",
            className="note",
        ),
        bloc_a_retenir(),
    ])


def page_introuvable():
    return html.Div([
        en_tete("Page introuvable", "Cette adresse n'existe pas"),
        bouton_suite("Retour à l'essentiel", "/"),
    ])


PAGES = {
    "/": page_essentiel(),
    "/quand": page_quand(),
    "/pourquoi": page_pourquoi(),
    "/avec-qui-et-ou": page_avec_qui_et_ou(),
}

racine = html.Div([
    dcc.Location(id="adresse"),
    menu(),
    dbc.Container(id="contenu-page", className="page"),
])
