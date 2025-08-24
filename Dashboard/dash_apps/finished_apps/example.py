from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
from Dashboard.models import WorkOrder, CustomUser

# External stylesheets
external_stylesheets = [dbc.themes.BOOTSTRAP, '/static/css/print.css']

# Initialize the app
app = DjangoDash('Example', external_stylesheets=external_stylesheets)

# Query work orders and staff users (include staff and technicians)
staff_users = CustomUser.objects.filter(user_type__in=['staff', 'technician'])
work_orders = WorkOrder.objects.select_related('assigned_to').all()

# Prepare DataFrame
data = []
for wo in work_orders:
    data.append({
        'WorkOrder_ID': wo.id,
        'Title': wo.title,
        'Status': wo.status,
        'Priority': wo.priority,
        'Assigned_To': wo.assigned_to.email if wo.assigned_to else 'Unassigned',
        'Assigned_To_ID': wo.assigned_to.id if wo.assigned_to else None,
        'Created_Date': wo.created_date,
        'Due_Date': wo.due_date
    })

df = pd.DataFrame(data)

# Layout
app.layout = dbc.Container([

    # Dashboard title
    dbc.Row([
        dbc.Col([
            html.H1("Work Assignment Management Dashboard"),
            html.H6("View, filter, and manage all work assignments assigned to staff."),
        ])
    ], style={'margin-top': '20px', 'margin-bottom': '20px'}),

    # Summary Cards
    dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H5("Total Work Assignments"), html.H2(id='total-orders')])]), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H5("Completed Work Assignments"), html.H2(id='completed-orders')])]), width=3),
        dbc.Col(dbc.Card([dbc.CardBody([html.H5("Pending Work Assignments"), html.H2(id='pending-orders')])]), width=3),
    ], style={'margin-top': '20px', 'margin-bottom': '20px'}),

    # Filters
    dbc.Row([
        dbc.Col([
            html.Label("Filter by Status"),
            dcc.Dropdown(
                id='status-dropdown',
                options=[{'label': s, 'value': s} for s in df['Status'].unique()] if 'Status' in df.columns else [],
                value=[],
                multi=True,
                placeholder="Select status..."
            ),
        ], width=3),
        dbc.Col([
            html.Label("Filter by Staff"),
            dcc.Dropdown(
                id='staff-dropdown',
                options=[
                    {'label': f"{u.email} ({u.get_user_type_display()})", 'value': u.id}
                    for u in staff_users
                ] if staff_users.exists() else [],
                value=[],
                multi=True,
                placeholder="Select staff..."
            ),
        ], width=3),
    ], style={'margin-bottom': '20px'}),

    # Work Order Table
    dbc.Row([
        dbc.Col([
            html.H3("Work Assignments"),
            dash_table.DataTable(
                id='workorder-table',
                columns=[{"name": i, "id": i} for i in df.drop(columns=["Assigned_To_ID"]).columns] if not df.empty else [],
                data=df.drop(columns=["Assigned_To_ID"]).to_dict('records') if not df.empty else [],
                page_size=10,
                style_table={'height': '300px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '5px'},
                style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
            ),
        ])
    ], style={'margin-bottom': '20px'}),
])

# Callback
@app.callback(
    Output('workorder-table', 'data'),
    Output('total-orders', 'children'),
    Output('completed-orders', 'children'),
    Output('pending-orders', 'children'),
    Input('status-dropdown', 'value'),
    Input('staff-dropdown', 'value')
)
def update_table(selected_status, selected_staff):
    if df.empty:
        return [], 0, 0, 0

    filtered_df = df.copy()

    # Filter by status
    if selected_status:
        filtered_df = filtered_df[filtered_df['Status'].isin(selected_status)]

    # Filter by staff IDs
    if selected_staff:
        selected_staff = [int(s) for s in selected_staff]  # Ensure integers
        filtered_df = filtered_df[filtered_df['Assigned_To_ID'].isin(selected_staff)]

    # Summary counts
    total_orders = len(filtered_df)
    completed_orders = len(filtered_df[filtered_df['Status'] == 'Completed'])
    pending_orders = len(filtered_df[filtered_df['Status'].isin(['Pending', 'In Progress'])])

    # Drop helper column before display
    return filtered_df.drop(columns=["Assigned_To_ID"]).to_dict('records'), total_orders, completed_orders, pending_orders
