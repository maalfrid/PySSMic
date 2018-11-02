import os

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, Event, State
import dash_table_experiments as dt
import plotly.graph_objs as go
import json
import pandas as pd
from app import app
import pickle
import re

"""-------------------------ENERGY USE-------------------------"""


def energy_use():
    return (
        dcc.Graph(
            id="energy-use-graph",
            figure=go.Figure()
        )
    )


""""-------------------------CONTRACT OVERVIEW-------------------------"""


def contract_overview():
    return (
        dt.DataTable(
            rows=[{}],
            columns=[
                "id", "time_of_agreement", "job_id", "producer_id"],
            row_selectable=True,
            filterable=True,
            sortable=True,
            selected_row_indices=[],
            id="contract-table"
        )
    )


"""-------------------------AVAILABLE VS USED ENERGY-------------------------"""


def energy_consumption():
    return (
        dcc.Graph(
            id="energy-consumption-graph",
            figure=go.Figure(
                data=[
                    # TODO: Update to input values from simulator in 'get_consumption()'
                    go.Scatter(
                        x=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
                        y=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
                        name="Energy used"
                    ),
                    go.Scatter(
                        x=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
                        y=[6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6],
                        name="Energy available"
                    )
                ],
                layout=go.Layout(
                    xaxis={
                        'title': 'Time'
                    },
                    yaxis={
                        'title': 'Energy'
                    }
                )
            )
        )
    )


def get_dropdown_options():
    print("Loading options")
    options = []
    for root, dirnames, filenames in os.walk("results"):
        for filename in filenames:
            if filename.endswith('.pkl'):
                options.append({
                    "label": filename[:-4], "value": filename}
                )
    if not options:
        options.append({"label": "No results saved.", "value": []})
    return options


"""-------------------------LAYOUT-------------------------"""


layout = html.Div(children=[
    html.Div(html.H3("Simulation to display")),
    html.Span("Choose simulation "),
    dcc.Dropdown(
        id="result",
        options=get_dropdown_options(),
        value=get_dropdown_options()[0]["value"]
    ),
    html.Button('Update results', className='btn', id='btn-update'),
    html.Div(id='sim_id', children=[
        html.Br(),
        html.Span("Choose individual simulation"),
        html.Div(
            dcc.Dropdown(
                id="simulation_choice",
                options=[],
                value='1'
            )
        ),
    ]),
    html.Br(),
    html.Div(id='household_id', children=[
        html.Span("Choose household"),
        html.Div(
            dcc.Dropdown(
                id="household_choice",
                options=[],
                value='1'
            )
        ),
    ]), html.Br(),
    dcc.Tabs(id="tabs", children=[
        dcc.Tab(id='tab_all_housholds', label='All households', children=[
            html.Br(),
            html.Div(
                html.H2("Energy use", className="header")
            ),
            html.Div([
                energy_use()
            ], className="pie-chart"),
            html.Br(),

            html.Div(
                html.H2("Contracts", className="header")
            ),
            html.Div([
                contract_overview()
            ], className="contract-table"),
            html.Br(),

            html.Div(
                html.H2("Available vs Used energy", className="header")
            ),
            html.Div([
                energy_consumption()
            ], className="consumption-graph"),
            html.Br(),
        ]),
        dcc.Tab(id='tab_one_household', label='One household', children=[
            # TODO
        ]),
        dcc.Tab(id='tab_all_sim', label='All simulations', children=[
            # TODO
        ])
    ])
])


"""-------------------------APP CALLBACKS-------------------------"""


@app.callback(Output("result", "options"),
              [Input("btn-update", "n_clicks")])
def update_dropdown(n_clicks):
    print("click")
    return get_dropdown_options()


@app.callback(Output("contract-table", "rows"),
              [Input("simulation_choice", "value")],
              [State("result", "value")])
def update_contracts(simulation_choice, result):
    contracts = open_file(result)[0]
    contracts = pd.DataFrame(contracts)
    rows = []
    for e in range(0, len(contracts)):
        rows.append(contracts[e][int(simulation_choice)])
    return rows


@app.callback(Output("simulation_choice", "options"),
              [Input("result", "value")])
def update_simid_dropdown(value):
    search = re.search(r'_(\d+?)\.', value)
    num = search.group(0)[1:-1]
    sim_options = []
    for val in range(0, int(num)):
        sim_options.append({'label': 'Simulation {}'.format(val+1), 'value': '{}'.format(val+1)})
    return sim_options


@app.callback(Output("household_choice", "options"),
              [Input("simulation_choice", "value")],
              [State("result", "value")])
def update_houseid_dropdown(simulation_choice, result):
    contracts = open_file(str(result))[0]
    contracts = pd.DataFrame(contracts)
    house_options = []
    for e in range(0, len(contracts[0])):
        contract_e = contracts[e][int(simulation_choice)]
        house_options.append({'label': 'Consumer ID: {}'.format(contract_e.get("job_id")), 'value': '{}'.format(contract_e.get("job_id"))})
    #print(house_options)
    return house_options


@app.callback(
    Output("energy-use-graph", "figure"),
    [Input("simulation_choice", "value")],
    [State("result", "value")])
def update_pie_chart(simulation_choice, result):
    contracts = open_file(result)[0]
    contracts = pd.DataFrame(contracts)
    print(contracts)
    grid = 0
    pv = 0
    for e in range(0, len(contracts[0])):
        contract_e = contracts[e][int(simulation_choice)]
        if contract_e.get("producer_id") == 'grid':
            print('GRID')
            print(contract_e.get("producer_id"))
            print(contract_e.get("load_profile"))
            grid += contract_e.get("load_profile").iat[1]
        else:
            pv += contract_e.get("load_profile").iat[1]
            print('PV')
            print(contract_e.get("producer_id"))
            print(contract_e.get("load_profile"))
    return go.Figure(
        data=[
            go.Pie(
                values=[grid, pv],
                labels=["Grid", "PV"]
            )
        ]
    )


@app.callback(
    Output('sim_id', 'style'),
    [Input('tabs', 'value')]
)
def display_none(value):
    if value == 'tab-3':
        return {'display': 'none'}


@app.callback(
    Output('household_id', 'style'),
    [Input('tabs', 'value')]
)
def display_none(value):
    print(value)
    if (value == 'tab-1') or (value == 'tab-3'):
        return {'display': 'none'}


"""-------------------------HELPING METHODS-------------------------"""


def open_file(file_name):
    with open('./results/{}'.format(file_name), 'rb') as f:
        res = pickle.load(f)
        contracts = res[0]
        profiles = res[1]
    return contracts, profiles





