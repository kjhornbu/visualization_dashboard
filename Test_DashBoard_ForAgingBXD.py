#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import dash
import more_itertools
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import sqlite3
import re

def set_groupings(data, mode):
    groupings = {} 
    for i,col in enumerate(data.row_description):
        if type(col) is str:
            x=re.search(r'(group[0-9]+)$',col)
            if x:
                temp=list(data.data[str(data.row_description.index[i])].unique())
                if mode == 'indiv':
                    temp.append('-')
                groupings.update({str(data.row_description.index[i]):temp})
    return groupings

class DataStructure:
       def __init__(self,row_idx:pd.Series,row_description:pd.Series,mode:str,data: pd.DataFrame,groupings:dict):
        self.row_idx = row_idx
        self.row_description = row_description
        self.data = data
        self.mode = mode
        self.groupings = groupings
        
def load_data(path,mode):
    
    data = pd.read_csv(path,delimiter='\t',low_memory=False,header=1)
    data_col_idx=data.iloc[0]
    data_comments=data.iloc[1]
    data = data.drop([data.index[0],data.index[1]]).reset_index()
    
    myData=DataStructure # Create Data (indiv or Group) class
    
    #assign data to it
    myData.row_idx = data_col_idx
    myData.row_description = data_comments
    myData.data = data
    myData.mode=mode
    
    #find the groupings within the data
    groupings=set_groupings(myData, mode)
    
    myData.groupings = groupings
        
    return myData

Group_Stats = pd.read_csv('/Volumes/dusom_civm-kjh60/All_Staff/18.gaj.42/Scalar_and_Volume/Main_Effects_2025_01_14_NoB6/Non_Erode/Bilateral/Group_Statistical_Results_Age_Class_Strain_Sex.csv',delimiter='\t',low_memory=False)
Group_Data=load_data('/Volumes/dusom_civm-kjh60/All_Staff/18.gaj.42/Scalar_and_Volume/Main_Effects_2025_01_14_NoB6/Non_Erode/Bilateral/Group_Data_Table_Age_Class_Strain_Sex.csv',mode='group')
Indiv_Data=load_data('/Volumes/dusom_civm-kjh60/All_Staff/18.gaj.42/Scalar_and_Volume/Main_Effects_2025_01_14_NoB6/Non_Erode/Subject_Data_Table.csv',mode='indiv')

# Initialize the Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1(children='Aging BXD Visualization Dashboard', style={'textAlign':'center', 'color':"#91472a", 'font-size':24}),#Include style for title
     html.Div([
        html.Label("Run Dashboard:"),
        dcc.Dropdown(
            id='dropdown-run',
            options={'Yes': 'Yes',
                'No':'No'},
            value='Select to Run',
            placeholder='Select to Run'
        )
    ], style ={'width':'80%', 'font-size':20, 'margin':3}),
    html.Div(dcc.Dropdown(
            id='select-mode',
            options={'Manual': 'Manual',
                    'Prompt': 'Prompt'},
            value='Select Mode for Configuration Input',
            placeholder='Select Mode for Configuration Input',
        ),style ={'width':'80%', 'font-size':20, 'margin':3}),
    html.Div([html.Div(id='output-container', className='chart-grid', style={'display': 'flex'}),])
])
#Start mode callback
@app.callback(
    Output(component_id='select-mode', component_property='disabled'),
    Input(component_id='dropdown-run',component_property='value'))

def update_input_container (run):
    if run =='No': 
        return True
    else: 
        return False

#start plot callback
@app.callback(Output(component_id='output-container', component_property='children'),
             [Input(component_id='dropdown-run',component_property='value'), Input(component_id='select-mode', component_property='value')])

def update_output_container (run,mode):
    config = None
    if mode == 'Manual':
        config=create_config()
    elif mode == 'Prompt':
        config = config=create_config()
    if run == 'Yes' and config is not None:
        return plot_by_config(config,Group_Data,Group_Stats)
    else: 
        return None
class Config: 
    def __init__(self,x:str,y:str,config_reducereorder:dict,config_filter:dict):
        self.x = x
        self.y = y
        self.reduce_reorder = config_reducereorder #how the data to be plotted is reduced/ordered (show top Ntries, sorted on Y)
        self.filter = config_filter #Things applied to the Group Stats data set

def create_config():
    myconfig = Config
    myconfig.x='GN_Symbol'#'# ROI'
    myconfig.y='percent_change_Young - -_Old - -'
    myconfig.reduce_reorder={'top_amount':10,'sort_on':myconfig.y}
    myconfig.filter={'pval_BH':0.05,
                    'source_of_variation':'Age_Class',
                    'contrast':'fa_mean'}
    return myconfig

def create_config_from_prompt():
    myconfig = Config
    return myconfig

def plot_by_config(config,Data,Stats):
    Reduced_Stats=filter_stat_sheet(config.filter,Stats)
    Reduced_Stats=reduce_to_top(config.reduce_reorder,Reduced_Stats)
    
    ## Source - https://stackoverflow.com/a
    # Posted by Jonathan Chow
    # Retrieved 2025-12-03, License - CC BY-SA 4.0
    # dcc.Graph(id='my-graph',style={'width': '90vh', 'height': '90vh'}) 

    chart = dcc.Graph(id ='output-graph',
        figure=px.scatter(Reduced_Stats, 
            x=config.x,
            y=config.y,),
        style={'width': '50vw', 'height': '50vh'} )
    
    return [html.Div(className='chart-item', children=[html.Div(children=chart)])]
        
def filter_stat_sheet(config_filter,sheet):
    reduced_sheet=sheet 
    for f in config_filter:
        if f =='pval' or f =='pval_BH':
            reduced_sheet = reduced_sheet[reduced_sheet[f] < config_filter[f]]
        else:
            reduced_sheet=reduced_sheet[reduced_sheet[f] == config_filter[f]]
    return reduced_sheet

def collect_from_data(data,sheet):
    merged_data = pd.merge(sheet, data, on='GN_Symbol', how='inner',copy=False,suffixes= ("", "_delete_me"))
    col_names=merged_data.columns
    for col in col_names:
        x=re.search(r'(_delete_me)$',col)
        if x: 
            merged_data.drop(columns=col,inplace=True)

    return merged_data

def reduce_to_top(config_reduce,sheet):
    sheet = sheet.sort_values(by=config_reduce['sort_on'])
    return sheet[0:config_reduce['top_amount']]

# Run the Dash app
if __name__ == '__main__':
    app.run(debug=True)