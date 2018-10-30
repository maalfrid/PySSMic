import base64
import datetime
import io
import json
import xml.etree.ElementTree as ET
import pandas as pd
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
from backend.neighbourhood import Neighbourhood
from backend.house import House
from backend.device import Device
from backend.user import User
from app import app
from util.input_utils import prediction_profile_from_csv

main_neighbourhood = None
active_house = None
active_device = None
# TODO: modal for adding house. modal with input field to set houseID


def create_house_tab(house):
    return(dcc.Tab(label='House Id: ' + str(house.id), value=str(house.id)))


def create_house_tabs(nei):
    houses = []
    for house in nei.houses:
        houses.append(create_house_tab(house))
    return houses


def create_house_view(house):
    content = []
    for user in house.users:
        for device in user.devices:
            content.append(
                html.Div(className="DeviceInHouse", children=[
                    html.Span("DeviceID: " + str(device.id) + "\t\t"),
                    html.Span("DeviceName: " + device.name + "\t\t"),
                    html.Span("DeviceTemplate: " + str(device.id) + "\t\t"),
                    html.Span("DeviceType: " + device.type + "\t\t")
                ])
            )
    return content


def displayHouse(house):
    numOfUsers = 0
    numOfDevices = 0
    for user in house.users:
        numOfUsers += 1
        for device in user.devices:
            numOfDevices += 1

    return html.Div(["House",
                     html.Span(str(house.id)),
                     html.Br(),
                     html.Span("Number of devices: " + str(numOfDevices)),
                     html.Div(children=create_house_view(house)),
                     ])


def addHouseToNeighbourhood(houseId):
    global main_neighbourhood
    # lastId = int(neighbourhood.houses[-1].id)
    house = House(houseId)
    main_neighbourhood.houses.append(house)

def configHouseModal():
    return html.Div(
        html.Div(
            [
                html.Div(
                    [
                        # header
                        html.Div(
                            [
                                html.Span(
                                    "Configure House",
                                    style={
                                        "color": "#506784",
                                        "fontWeight": "bold",
                                        "fontSize": "20",
                                    },
                                ),
                                html.Span(
                                    "×",
                                    id="leads_modal_close",
                                    n_clicks=0,
                                    style={
                                        "float": "right",
                                        "cursor": "pointer",
                                        "marginTop": "0",
                                        "marginBottom": "17",
                                    },
                                ),
                            ],
                            className="popup",
                            style={"borderBottom": "1px solid #C8D4E3"},
                        ),
                        dcc.Tabs(id="configHouseTabs", value='configHouseDevice', children=[
                            dcc.Tab(label='Configure a device',
                                    value="configHouseDevice"),
                            dcc.Tab(label='Add new device',
                                    value="addNewDevice")
                        ]),
                        # form
                        html.Div(id='configHouse-content'),
                        html.Span(
                            "Save",
                            id="save_house",
                            n_clicks_timestamp='0',
                            className="button button--primary add"
                        ),
                        html.Button("Delete")
                    ],
                    className="modal-content",
                    style={"textAlign": "center"},
                )
            ],
            className="modal",
        ),
        id="house_modal",
        style={"display": "none"},
    )


layout = html.Div([
    html.Div(id="save_hidden", style={'display': 'none'}),
    # hidden div to save data in
    html.Div(id="new_device_div", style={'display': 'block'}),
    html.Div(id='nInfo', children=[
        html.Div('nabolag: ' + str(main_neighbourhood),
                 id="main_neighbourhood-info"),
        html.Div('hus: ' + str(type(active_house)), id="active_house-info"),
        html.Div('device: ' + str(active_device), id="active_device-info")
    ]),
    html.H4("Create a new neighbourhood"),
    html.Div(id="initChoices", children=[
        html.Button("Create from XML", id="btnXmlInput"),
        html.Button("Create a new", id="btnNewNeighbourhood"),
        dcc.Upload(
            id="upload-data",
            children=html.Div([
                'Add neighbourhood XML file by Drag and Drop or ',
                html.A('Select Files')
            ]),
            style={
                'width': '500px',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px',
                'display': 'none'
            }
        ),
        html.Div(id="newNeighbourhoodInput", children=[
            dcc.Input(id="newNeighbourhoodId", value=0, type="number", style={
                'width': '50px'
            }),
            html.Button("Create Neighbourhood",
                        id="btnCreateNewNeighbourhood", n_clicks_timestamp='0')
        ],
            style={'display': 'none'}),
    ]),
    html.Div(id="newHouseInput", children=[
        html.Button("Add house", id="btnAddHouse", n_clicks_timestamp='0'),
        html.Button("Delete house", id="btnDeleteHouse",
                    n_clicks_timestamp='0'),
        html.Button("Configure", id="btnConfigHouse", n_clicks_timestamp='0')
    ]),
    html.Div(id="neighbourhood-info"),
    html.Div(id="tabs"),
    html.Button("Save Neighbourhood",id="btnSaveNeighbourhood"),
    configHouseModal()
])

# takes in a xmlfile and returns a XML Elementree of the neighborhood.


def parse_contents(contents):
    if contents is not None:
        content_type, content_string = contents.split(',')
        if 'xml' in content_type:
            decoded = base64.b64decode(content_string)
            root = ET.fromstring(decoded)
            return root


def create_neighborhood_object(treeroot):
    nabolag = Neighbourhood(int(treeroot.get("id")))
    for house in treeroot:
        h = House(int(house.get("id")))
        for user in house:
            u = User(int(user.get("id")))
            for device in user:
                d = Device(int(device.find("id").text), device.find("name").text, int(
                    device.find("template").text), device.find("type").text)
                u.devices.append(d)
            h.users.append(u)
        nabolag.houses.append(h)
    return nabolag


"""
Callback function to toggle the xml input field
"""


@app.callback(Output("upload-data", "style"), [Input("btnXmlInput", "n_clicks")])
def showXMLUpload(n):
    if n % 2 == 0:
        return {"display": "none"}
    return {"display": "block"}


"""
Callback to render id inputfield for a new Neighbourhood
"""


@app.callback(Output('newNeighbourhoodInput', 'style'),
              [Input("btnNewNeighbourhood", "n_clicks")])
def showNewNeighbourhoodInput(n):
    if n == 1:
        return {'display': 'block'}
    return {"display": "none"}


# Saves neighbourhood in hidden div on main page, so the output div can update on multiple other events
# Function to store and update main neighbourhood div / Controller

@app.callback(Output('new_device_div', 'children'),
              [Input('save_house', 'n_clicks_timestamp')],
              [
    State('newDeviceId', 'value'),
    State('newDeviceName', 'value'),
    State('newDeviceTemplate', 'value'),
    State('newDeviceType', 'value')
])
def addDevice(n, dId, dName, dTemp, dType):
    global active_house
    global active_device
    if (dId or dName or dTemp or dType) is not None:
        #Update old one -- can be duplicate deviceIds
        dev = Device(dId, dName, dTemp, dType)
        active_house.users[0].devices.append(dev)
    return html.Div(str(dev))


@app.callback(Output('neighbourhood_div', 'children'),
              [Input('upload-data', 'contents'),
               Input('btnCreateNewNeighbourhood', 'n_clicks_timestamp'),
               Input('btnAddHouse', 'n_clicks_timestamp'),
               Input('btnDeleteHouse', 'n_clicks_timestamp'),
               Input('save_house', 'n_clicks_timestamp')],
               [State('newNeighbourhoodId', 'value')])
def configure_neighbourhood(contents, btnNewNei, btnAddHouse, btnRemoveHouse, btnSave, value):
    global main_neighbourhood
    global active_house
    print(str(btnNewNei) + str(btnAddHouse) + str(btnRemoveHouse) + str(btnSave))
    if int(btnNewNei) > int(btnAddHouse) and int(btnNewNei) > int(btnRemoveHouse) and int(btnNewNei) > int(btnSave):
        newHouse = House(1)
        newHouse.users.append(User(1))
        main_neighbourhood = Neighbourhood(90)  # TODO: logic to set id.
        main_neighbourhood.houses.append(newHouse)
    elif int(btnAddHouse) > int(btnNewNei) and int(btnAddHouse) > int(btnRemoveHouse) and int(btnAddHouse) > int(btnSave):
        i = main_neighbourhood.nextHouseId()
        newHouse = House(i)
        newHouse.users.append(User(1))
        main_neighbourhood.houses.append(newHouse)  # TODO: logic to set id.
    elif int(btnRemoveHouse) > int(btnNewNei) and int(btnRemoveHouse) > int(btnAddHouse) and int(btnRemoveHouse) > int(btnSave):
        main_neighbourhood.houses.remove(
            active_house)
        if len(main_neighbourhood.houses) > 0:
            active_house=main_neighbourhood.houses[0]

    elif int(btnSave) > int(btnNewNei) and int(btnSave) > int(btnAddHouse) and int(btnSave) > int(btnRemoveHouse):
        print("hello")
    elif contents is not None:
        root = parse_contents(contents)
        main_neighbourhood = create_neighborhood_object(root)
        active_house = main_neighbourhood.houses[0]
    if main_neighbourhood is not None:
        nabolag = main_neighbourhood.to_json()
        return html.Div(nabolag)
    else:
        return html.Div()

# Function to update the view based on neighbourhood div


@app.callback(Output('tabs', 'children'),
              [Input('neighbourhood_div', 'children')])
def neighbourhood_tab_view(dictionary):
    global main_neighbourhood
    if main_neighbourhood is not None:
        tabs = create_house_tabs(main_neighbourhood)
        return html.Div(children=[
            dcc.Tabs(id='neighbourhoodTabs', children=tabs),
            html.Div(id='tabs-content', children=["some cool content"])
        ])


@app.callback(Output('initChoices', 'style'), [Input('tabs', 'children')])
def hideButton(children):
    if len(children) > 1:
        return {'display': 'none'}

# generate content for tabs


@app.callback(Output('tabs-content', 'children'),
              [Input('neighbourhoodTabs', 'value')])
def render_content(value):
    global main_neighbourhood
    global active_house
    if value is not None:
        tabId = int(value)
    else:  # get the id of first house in houselist
        tabId = int(main_neighbourhood.houses[0].id)
    if main_neighbourhood is not None:
        house = main_neighbourhood.findHouseById(tabId)
        if house is not None:
            dis = displayHouse(house)
            return html.Div([dis])


""" ------------------- configHouseModal callbacks ----------------------"""


@app.callback(Output("house_modal", "style"), [Input("btnConfigHouse", "n_clicks")])
def display_leads_modal_callback(n):
    if n > 0:
        return {"display": "block"}
    return {"display": "none"}
# reset to 0 add button n_clicks property


@app.callback(Output('configHouse-content', 'children'), [Input('configHouseTabs', 'value')])
def showHouseConfigContent(value):
    if value == 'configHouseDevice':
        return html.Div([
            dcc.Dropdown(id='user-device-dropdown', options=[{'label': device.name, 'value': device.id}
                                                             for user in active_house.users for device in user.devices], placeholder='Select device'),
            html.Div(id="deviceConfigForm")
        ])
    elif value == 'addNewDevice':
        return html.Div([
            dcc.Input(id="newDeviceId", type="number", placeholder="DeviceID", style={
                'width': '100px'
            }),
            html.Br(),
            dcc.Input(id="newDeviceName", type="text", placeholder="DeviceName", style={
                'width': '100px'
            }),
            html.Br(),
            dcc.Input(id="newDeviceTemplate", type="number", placeholder="TemplateName", style={
                'width': '100px'
            }),
            html.Br(),
            dcc.Dropdown(id="newDeviceType", placeholder="TemplateType",
                         options=[{'label': "Consumer", 'value': "consumer"}, {'label': "Producer", 'value': "producer"}])
        ])


@app.callback(Output('deviceConfigForm', 'children'), [Input('active_device-info', 'children')])
def renderConfigForm(children):
    if active_device is not None:
        return html.Div([
            dcc.Input(id="newDeviceId", type="number", value=active_device.id, style={
                'width': '100px'
            }),
            html.Br(),
            dcc.Input(id="newDeviceName", type="text", value=active_device.name, style={
                'width': '100px'
            }),
            html.Br(),
            dcc.Input(id="newDeviceTemplate", type="number", value=active_device.template, style={
                'width': '100px'
            }),
            html.Br(),
            dcc.Dropdown(id="newDeviceType", value=active_device.type,
                         options=[{'label': "Consumer", 'value': "consumer"}, {'label': "Producer", 'value': "producer"}]),
            dcc.Upload(id="LoadPredictionUpload",
            children=html.Div([
                'Add Load or Prediction CSV file by Drag and Drop or ',
                html.A('Select Files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
            }
        ),
            html.Div(id=''),
            dt.DataTable(
                id="loadOrPredictionTable",
                rows=[{}],
            )
        ])


def parse_csv(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string) #decoded is now bytes
    string = io.StringIO(decoded.decode('utf-8'))
    timestamps = []
    values = []
    for line in string:
        if line is not "":
            split_line = line.split(" ")
            timestamps.append(split_line[0])
            values.append(split_line[1].rstrip())
    output = [('Time', timestamps),
              ('Value', values)]
    df = pd.DataFrame.from_items(output)
    return df

@app.callback(Output('loadOrPredictionTable', 'rows'), [Input('LoadPredictionUpload', 'contents')], [State('LoadPredictionUpload', 'filename')])
def update_table(contents, filename):
    df = parse_csv(contents, filename)
    return df.to_dict('records')


@app.callback(
    Output("btnConfigHouse", "n_clicks"),
    [Input("leads_modal_close", "n_clicks"),
     Input("save_house", "n_clicks")],
)
def close_modal_callback(n, n2):
    return 0

''' Functions for developing mode'''

@app.callback(Output('nInfo', 'children'), [Input('neighbourhood_div', 'children')])
def showNid(children):
    global main_neighbourhood
    global active_house
    return html.Div([
        html.Div('nabolag: ' + str(len(main_neighbourhood.houses)),
                 id="main_neighbourhood-info"),
        html.Div('hus: ' + str(type(active_house)), id="active_house-info"),
        html.Div('device: ' + str(active_device), id="active_device-info")
    ])

# set active house.

@app.callback(Output('active_house-info', 'children'), [Input('neighbourhoodTabs', 'value'), Input('btnDeleteHouse', 'n_clicks')])
def setActiveHouse(value, n):
    global active_house
    global main_neighbourhood
    if value is not None:
        active_house = main_neighbourhood.findHouseById(int(value))
    return html.Div(str(type(active_house)))


@app.callback(Output('active_device-info', 'children'), [Input('user-device-dropdown', 'value')])
def setActiveDevice(value):
    global active_house
    global active_device
    if value is not None:
        active_device = active_house.findDeviceById(int(value))
    return html.Div(str(active_device))


#Change tab on delete. TODO:reset n and send signal instead of timestamp on adding house
@app.callback(Output('neighbourhoodTabs', 'value'), [Input('btnDeleteHouse', 'n_clicks_timestamp'), Input('btnAddHouse', 'n_clicks_timestamp')])
def tabChangeOnDelete(a, b):
    if int(a) > int(b):
        print(a)
        return str(main_neighbourhood.houses[0].id)
    elif int(b) > int(a):
        print(b)
        i = len(main_neighbourhood.houses) - 1
        print(i)
        return str(main_neighbourhood.houses[i].id)


'''
TODO: Create csv file for consumer events, producer events and for loads and predictions
'''
@app.callback(Output('save_hidden', 'children'), [Input('btnSaveNeighbourhood', 'n_clicks')])
def save_neighbourhood(n):
    #go through neighbourhood and create files
    for house in main_neighbourhood.houses:
        for device in house.users[0].devices: #only one user in each house
            for event in device.events: #Events are saved as dict. using utilfunction to create csv files for simulator
                if device.type == "producer":
                    print('producer') 
                    #TODO: add to producerevents
                    #TODO: add predictionfile
                elif device.type == "consumer":
                    print("consumer")
                    #TODO: add to consumer events
                    #TODO: add loadfile
                print('event')
            print(str(device.name))
    

