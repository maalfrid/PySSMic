import base64
import datetime
import io
import json
import xml.etree.ElementTree as ET

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html


from app import app

layout = html.Div([
    html.H2("Create a new neighbourhood"),
    html.Button("Add house"),
    html.Button("Add user in house"),
    html.Button("Add a userdevice"),

    dcc.Upload(
        id="upload-data",
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        }
    ),
    html.Div(id='output')
])


def create_neighborhood(num_of_houses):
    nabolag = html.Div("Nabolag")
    for x in range(num_of_houses):
        nabolag.children = nabolag.children, create_div(x)
    return nabolag


def create_div(num):
    return html.Div("Hus" + str(num))

# returns a XML Elementree of the neighborhood.


def parse_contents(contents):
    if contents is not None:
        content_type, content_string = contents.split(',')

        if 'xml' in content_type:
            decoded = base64.b64decode(content_string)
            root = ET.fromstring(decoded)
            return root

# Takes in a xml.Elementree.Element and produces a neighborhood
# TODO: change the print statements with what you decide to do


def create_neighborhood_list(neighborhood):
    nh = []
    print("---House---")
    for house in neighborhood:
        h = [house.get("id")]
        print(house.get("id"))
        for user in house:
            print(user.get("id"))
            u = [user.get("id")]
            for device in user:
                print(device.find("id").text)
                u.append(device.find("id").text)
            h.append(u)
        nh.append(h)
    print("---new house ---")

    return nh

# Creates a simple html output for the neighborhood input (XML file)


def create_neighborhood_html(neighborhood):
    htmlString = "<div>"
    htmlString += "Nabolag:"
    for house in neighborhood:
        htmlString += "<div>"
        htmlString += "Hus id: " + str(house.get("id"))
        for user in house:
            htmlString += "<div>"
            htmlString += "user id: " + str(user.get("id")) + "<ul>"
            for device in user:
                htmlString += "<li> device id: " + \
                    str(device.find("id").text) + \
                    " Name: " + str(device.find("name").text) + \
                    " Template: " + str(device.find("template").text) + \
                    " Type: " + str(device.find("type").text) + \
                    "</li>"  # closes device listelement
            htmlString += "</ul> </div> <br />"  # closes list and user element
        htmlString += "</div>  <br />"  # closes house div
    htmlString += "</div>"  # closes neighborhood
    return htmlString


@app.callback(Output('output', 'children'),
              [Input('upload-data', 'contents')])
def update_output(contents):
    root = parse_contents(contents)
    htmlstr = create_neighborhood_html(root)
    return html.Div([
        html.Iframe(
            sandbox='',
            height=500,
            width=600,
            srcDoc=htmlstr
        )
    ])