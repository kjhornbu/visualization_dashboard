# In[ ]:

from dash import Dash, dcc, html, dash_table,Input, Output, callback
import pandas as pd
import time
import os
from helper_functions import *
from classes import *
#from persistentData import Indiv_Data, Group_Data, Group_Stats
import persistentData

# All your callbacks have to be between the end of the app layout and the app run call to work properly
## OBTAINING DATA CALLBACKS
@callback(Output("loading-stat_sheet", "children"),
    Input(component_id='group_stats_path',component_property='value'))
def update_input_stats (path):
    print(path)
    if path is not None and os.path.exists(path):
        time.sleep(1)
        print(path)
        persistentData.Group_Stats = load_stats(path)
        print(f'LOADED GROUP STATS {path}')
    return

@callback(Output("loading-group_data", "children"),
    Input(component_id='group_data_path',component_property='value'))
def update_input_group_data (path):
    if path is not None and os.path.exists(path):
        time.sleep(1)
        persistentData.Group_Data = load_data(path,mode='group')
        print(f'LOADED GROUP DATA {path}')
    return

@callback(Output("loading-indiv_data", "children"),
    Input(component_id='indiv_data_path',component_property='value'))
def update_input_indiv_data (path):
    if path is not None and os.path.exists(path):
        time.sleep(1)
        persistentData.Indiv_Data = load_data(path,mode='indiv')
        print(f'LOADED INDIV DATA {path}')
    return

@callback(
    Output(component_id='prompt-container',component_property='children'),
    Input(component_id='select-mode',component_property='value'),prevent_initial_call=True)
def make_manual_versus_prompt_input(input_mode):
    if input_mode=='Manual':
        table_type_dropdown=dcc.Dropdown(options={'stats':'Group Statistical Results','group':'Group Data Table','indiv': 'Subject Data Table'},
                                         placeholder='Select Main Table for Visualization', id='main_plot_table')
        return table_type_dropdown
    elif input_mode =='Prompt':
        prompt_input=dcc.Textarea(value=None,placeholder='Input Prompt for Figure Generation, such as "Show me the Top 10 significant FA regions for Age_Class"',id='prompt_input',style={'width': '100%'})
        return prompt_input
    else:
        return None

@callback(
    Output(component_id='output-container', component_property='children', allow_duplicate=True),
    Input(component_id='prompt_input', component_property='value'),
    prevent_initial_call=True)
def set_figure_to_output_Prompt(prompt_text):
    message= 'Make Sure All Data Files Are Loaded and Exist At Path Location'

    #parse the group text pulling out key aspects of the request
    #push that to the configuration generation
    #apply that to the figure
    #push that to the output container
    print(persistentData.Indiv_Data)
    print(persistentData.Group_Data)
    print(persistentData.Group_Stats)
    if isinstance(persistentData.Indiv_Data, DataStructure) and isinstance(persistentData.Group_Data, DataStructure) and isinstance(persistentData.Group_Stats, StatsStructure):
        return full_fig_layout(select_table_4_plotting)
    else:
        return [html.Div(className='chart-item', children=[html.Div(children=dcc.Input(id="Error_on_loading_Prompt", value=message))])]
    return None

## Have to have the config to do the config and that is screwing with me. The actual configuration setup needs a ton of selection points or at least set data....
#start Plot Callback
@callback(Output(component_id='output-container', component_property='children', allow_duplicate=True),[Input(component_id='main_plot_table',component_property='value')],prevent_initial_call=True)
def set_figure_to_output_Manual(select_table_4_plotting):
    message= 'Make Sure All Data Files Are Loaded and Exist At Path Location'
    myConfig=generate_config()
    # cheesy method to hold onto configs, see persistentData for the name of our "global-ish" variables.o
    Plot_Configurations["myConfig"]=myConfig

    if isinstance(persistentData.Indiv_Data, DataStructure) and isinstance(persistentData.Group_Data, DataStructure) and isinstance(persistentData.Group_Stats, StatsStructure):
        return full_fig_layout(select_table_4_plotting)
    else:
        return [html.Div(className='chart-item', children=[html.Div(children=dcc.Input(id="Error_on_loading_Manual", value=message))])]
