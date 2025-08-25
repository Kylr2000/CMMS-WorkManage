import dash  # make sure dash is imported
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from django_plotly_dash import DjangoDash
from Dashboard.models import WorkOrder

# External styles
external_stylesheets = [dbc.themes.BOOTSTRAP, '/static/css/print.css']

# Initialize the DjangoDash app
app = DjangoDash('Detailed_Analysis', external_stylesheets=external_stylesheets)

# Layout
app.layout = dbc.Container([
    # Hidden dcc.Location to handle redirection
    dcc.Location(id='redirect', refresh=True),

    dbc.Row([
        dbc.Col([
            html.H1("Work Order Dashboard"),
            html.H6("""
                This dashboard allows administrators and technicians to manage work orders. 
                Use the buttons below to search, view, or add new work orders.
            """),
        ]),
    ], align='end', style={'margin-top': '20px', 'margin-bottom': '20px'}),

    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Button("🔍 Search Work Order", id="search-btn", color="primary", className="m-2", n_clicks=0),
                    dbc.Button("📄 View Recent Work Orders", id="recent-btn", color="info", className="m-2", n_clicks=0),
                    dbc.Button("➕ Add Work Order", id="add-btn", color="success", className="m-2", n_clicks=0),
                ], width=12, className="text-center")
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.Div(id="output-area")
                ])
            ])
        ])
    )
], fluid=True)


# ------------------------------
# Callback
# ------------------------------
@app.callback(
    [Output("output-area", "children"),
     Output("redirect", "href")],
    [Input("search-btn", "n_clicks"),
     Input("recent-btn", "n_clicks"),
     Input("add-btn", "n_clicks")]
)
def handle_button_click(search_clicks, recent_clicks, add_clicks):
    ctx = dash.callback_context

    # default output
    output_area = "Select an option above to get started."
    redirect_url = None

    if ctx.triggered:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "search-btn":
            output_area = dbc.Form([
                dbc.Label("Enter Work Order Title:"),
                dbc.Input(type="text", id="search-query", placeholder="e.g., Replace antenna"),
                dbc.Button("Search", color="primary", className="mt-2", id="submit-search"),
            ])

        elif button_id == "recent-btn":
            recent_orders = WorkOrder.objects.all().order_by("-created_date")[:5]
            if not recent_orders:
                output_area = html.P("No recent work orders found.")
            else:
                output_area = dbc.Table(
                    [html.Thead(html.Tr([html.Th("Title"), html.Th("Status"), html.Th("Priority"), html.Th("Created")]))] +
                    [html.Tbody([
                        html.Tr([
                            html.Td(order.title),
                            html.Td(order.status),
                            html.Td(order.priority),
                            html.Td(order.created_date.strftime("%Y-%m-%d")),
                        ]) for order in recent_orders
                    ])],
                    bordered=True,
                    hover=True,
                    responsive=True,
                    striped=True
                )

        elif button_id == "add-btn":
            # trigger redirect to add work order page
            redirect_url = "/create_workorder/"
            output_area = html.P("Redirecting to Add Work Order page...")

    return output_area, redirect_url
