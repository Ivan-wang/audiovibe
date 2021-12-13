# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import pandas as pd
import numpy as np
import dash
from dash import dcc
from dash import html
import plotly.express as px
from dash.dependencies import Output, Input, State
# import dash_core_components as dcc
# import dash_html_components as html

app = dash.Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

def connect_sliders_values(slider_id, value_id):
    @app.callback(Output(value_id, 'children'), [Input(slider_id, 'value')])
    def update_output(value):
        return f'{value:.2f}'

def wave_slider(i):
    div = html.Div(children=[
        dcc.Slider(id=f'wave-slider-{i}', min=0., max=1.,
        step=0.01, value=0.5, vertical=True,
        tooltip={"placement": "right", "always_visible": True}
        ),
        html.Div(id=f'wave-value-{i}')]
    , style={'display': 'flex', 'flex-direction': 'column', 
        'align-content': 'center'})
    connect_sliders_values(f'wave-slider-{i}', f'wave-value-{i}')
    return div

def slider_div():
    div = html.Div(children=[
        wave_slider(i) for i in range(24)
    ], style={'display': 'flex', 'flex-direction': 'row',
    'justify-content': 'space-evenly'})
    return div

def control_div():
    div = html.Div(children=[
    html.Div(children=[
        html.Label('Wave Family'),
        dcc.Dropdown(
            options=[
                {'label': 'Uniform', 'value': 'UNI'},
                {'label': 'Linear', 'value': 'LIN'},
                {'label': 'Quadratic', 'value': 'QUA'},
                {'label': 'Custom', 'value': 'CUS'}
            ],
            value='UNI',
            id='wave-family'
        ),

        html.Br(),
        html.Label('Wave Trends'),
        dcc.Dropdown(
            options=[
                {'label': 'Descent', 'value': 'DES'},
                {'label': 'Ascent', 'value': 'ASC'},
                # {'label': 'San Francisco', 'value': 'SF'}
            ],
            value='DES',
            id='wave-trends'
        ),
        html.Br(),
        html.Button(children='A Button', id='wave-load-btn', n_clicks=0),
        html.Div(id='wave-load-key'),
        html.Br(),
        html.Button(children='Save Waveform', id='wave-save-btn', n_clicks=0)
    ], style={'padding': 10, 'flex': 1}),

    html.Div(children=[
        html.Label('Checkboxes'),
        dcc.Checklist(
            options=[
                {'label': 'New York City', 'value': 'NYC'},
                {'label': u'Montréal', 'value': 'MTL'},
                {'label': 'San Francisco', 'value': 'SF'}
            ],
            value=['MTL', 'SF']
        ),

        html.Br(),
        html.Label('Text Input'),
        dcc.Input(value='MTL', type='text'),

        html.Br(),
        html.Label('Slider'),
        dcc.Slider(
            min=0,
            max=9,
            marks={i: 'Label {}'.format(i) if i == 1 else str(i) for i in range(1, 6)},
            value=5,
        ),
    ], style={'padding': 10, 'flex': 1})],
    style={'display': 'flex', 'flex-direction': 'row'})

    return div

@app.callback(
    *[Output(f'wave-slider-{i}', 'value') for i in range(24)],
    Output('wave-load-key', 'children'), Input('wave-load-btn', 'n_clicks'), State('wave-family', 'value'), State('wave-trends', 'value'))
def load_wave_form(n_clicks, wave_family, wave_trends):
    if n_clicks == 0:
        out = [1.] * 24
    else:
        out = [0.5] * 24
    return out + ['Clicks {}, loading {}-{}'.format(n_clicks, wave_family, wave_trends)]



app.layout = html.Div([
    # html.Div(children=[
    #     html.H1(children='Hello Dash'),
    #     html.Div(children='''
    #         Dash: A web application framework for your data.
    #     '''),
    #     dcc.Graph(
    #             id='example-graph',
    #             figure=fig
    #         )
    # ]),
    slider_div(),
    html.Br(),
    control_div()
], style={'display': 'flex', 'flex-direction': 'column'})

if __name__ == '__main__':
    app.run_server(debug=True)