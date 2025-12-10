#!/usr/bin/env python
# coding: utf-8

# In[ ]:
from dash import Dash, dcc, html
from helper_functions import *
from classes import *
from callbacks import *
import persistentData
from persistentData import default_files

#import helper_functions
#import classes
#import callbacks

## INITALIZE THE DASH APP
app = Dash(__name__, suppress_callback_exceptions=True)

## MAIN BODY OF THE DASH APP
app.layout = html.Div([
    html.H1(children='CIVM Visualization Dashboard', style={'textAlign':'center', 'color':"#012169", 'font-size':24,'font-family':'Arial'}),
    html.Div([
        html.Div([
            html.Label("Group Statistical Results File Path: " , style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            dcc.Input(id='group_stats_path', type='text', value=default_files["Result"],
                      placeholder=default_files["Result"],
                      style={'width': '50%'}),
            dcc.Loading(id="loading-1", type="default", delay_show=0, delay_hide=500, children=html.Div(id="loading-stat_sheet"))
        ]),
        html.Div([
            html.Label("Group Data Table File Path: ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            dcc.Input(id='group_data_path', type='text', value=default_files["Group"],
                      placeholder=default_files["Group"],
                      style={'width': '50%'}),
            dcc.Loading(id="loading-2", type="default", delay_show=0, delay_hide=500, children=html.Div(id="loading-group_data"))
            ]),
        html.Div([
            html.Label("Subject Data Table File Path: ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            dcc.Input(id='indiv_data_path', type='text', value=default_files["Subject"],
                      placeholder=default_files["Subject"],
                      style={'width': '50%'}),
            dcc.Loading(id="loading-3", type="default", delay_show=0, delay_hide=500, children=html.Div(id="loading-indiv_data"))
            ]),
    ], style ={'width':'80%','margin':5}),

    html.Div([dcc.Dropdown(id='select-mode',
            options={'Manual': 'Manual','Prompt': 'Prompt'},
            value='Select Mode for Configuration Input',
            placeholder='Select Mode for Configuration Input',
        )],style ={'width':'80%', 'font-size':18, 'margin':5,'font-family':'Arial'}),
    html.Div([html.Div(id='prompt-container')],style ={'width':'80%', 'font-size':18, 'margin':5,'font-family':'Arial'}),
    html.Div([html.Div(id='output-container', className='chart-grid', style={'display': 'flex'})])
])

    ## RUN THE DASH APP
if __name__ == '__main__':
    app.run(debug=True)
