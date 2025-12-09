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
import re
import math
import time
import os

#Create a Configuration for Plotting
class Config: 
    def __init__(self,use_sheet:str,x:str,y:str,groups_to_include:dict,config_reducereorder:dict,config_filter:dict):
        self.use_sheet = use_sheet
        self.x = x
        self.y = y
        self.groups_to_include=groups_to_include
        self.reduce_reorder = config_reducereorder #how the data to be plotted is reduced/ordered (show top Ntries, sorted on Y --- always sort on the Y entry?)
        self.filter = config_filter #Things applied to the Group Stats data set


#Input and Organize Data Tables and Stat Sheets 
class DataStructure:
    def __init__(self,row_idx:pd.Series,row_description:pd.Series,mode:str,data: pd.DataFrame):
        self.row_idx = row_idx
        self.row_description = row_description
        self.data = data
        self.mode = mode
        self.groupings = self.set_groupings()
        
    def set_groupings(self):
        groupings = {} 
        for i,col in enumerate(self.row_description):
            if type(col) is str:
                x=re.search(r'(group[0-9]+)$',col)
                if x:
                    temp=list(self.data[str(self.row_description.index[i])].unique())
                    ordered_temp=sorted(temp)
                    if self.mode == 'indiv':
                        temp.append('-')
                    groupings.update({str(self.row_description.index[i]):ordered_temp})
        self.groupings = groupings
        return self.groupings
        
class StatsStructure(DataStructure): 
    def __init__(self,row_idx:pd.Series,row_description:pd.Series,data: pd.DataFrame):
        DataStructure.__init__(self,row_idx=row_idx,row_description=row_description,mode='stats',data=data)
        [self.sov_options,self.contrast_options]= self.set_stats_groupings()
        
    def set_stats_groupings(self):
        self.sov_options=list(self.data['source_of_variation'].unique())
        self.contrast_options=list(self.data['contrast'].unique())
        
        return [self.sov_options, self.contrast_options]

def check_header_rows(path):
    header_num = None
    n=0
    while header_num is None:
        data = pd.read_csv(path,delimiter='\t',low_memory=False,header=n)
        for i,col in enumerate(data.columns):
            if type(col) is str:
                x=re.search(r'(id64_fSABI)$',col) #made one of our weird meta table regions so that we dont' accidently pull soemething from the raw meta table header in the googlesheet
                if x:
                    header_num=n
        n=n+1
    return header_num 

def load_data(path,mode):
    header_num=check_header_rows(path)
    data = pd.read_csv(path,delimiter='\t',low_memory=False,header=header_num) #This number gets adjusted depending on how much stuff is in the description of the csv... unsure how we will deal with that in python versus matlab. 
    data_col_idx=data.iloc[0]
    data_comments=data.iloc[1]
    data = data.drop([data.index[0],data.index[1]]).reset_index()
    
    myData=DataStructure(row_idx = data_col_idx,row_description = data_comments,data = data,mode=mode) # Create Data (indiv or Group) class
        
    return myData

def load_stats(path):
    header_num=check_header_rows(path)
    stats = pd.read_csv(path,delimiter='\t',low_memory=False,header=header_num) 
    stats_col_idx=stats.iloc[0]
    stats_comments=stats.iloc[1]
    stats = stats.drop([stats.index[0],stats.index[1]]).reset_index()
    
    myStats = StatsStructure(row_idx = stats_col_idx,row_description = stats_comments,data = stats)
    
    return myStats

def create_config_manual():
    #table_type = organize_table_type()
    table_type='stats'
    if table_type == 'stats':
        x_options = list(Group_Stats.data.columns)
        #drop_x=make_axis_input(x_options,'x')

        y_options = list(Group_Stats.data.columns)
        #drop_y=make_axis_input(y_options,'y')

        '''
        radio_topN=make_radiobutton_topN()
        radio_Pval=make_radiobutton_pvalue()

        contrast_slider=make_slider(Group_Stats.contrast_options,'contrast_slider')
        sov_slider=make_slider(Group_Stats.sov_options,'sov_slider')


        [
         html.Div(className='x_y_input', children=[html.Div(children=drop_x),html.Div(children=drop_y)],style={'display':'grid'}),
         html.Div(
            html.Label("FILTER BY: ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            radio_Pval
         ),
        html.Div(
            html.Label("SHOW: ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            radio_topN,
         ),
           html.Div(
            html.Label("Contrast ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            contrast_slider,
         ),
           html.Div(
            html.Label("Source of Variation: ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            sov_slider,
         )
        ]

        '''
        groups_to_include_options=None
        
    elif table_type == "indiv":
        x_options = list(Indiv_Data.data.columns)
        y_options = list(Indiv_Data.data.columns)
        groups_to_include_options = Indiv_Data.groupings
    elif table_type == "group":
        x_options = list(Group_Data.data.columns)
        y_options = list(Group_Data.data.columns)
        groups_to_include_options = Group_Data.groupings
        
        rank_number = int 
        rank_sort_options= y_options
            
    
    '''
    source_of_variation=
    
    dcc.Dropdown(s
            id='select-data',
            options={'Stats Output': 'stats_output',
                    'Group Data Table': 'group_data_table',
                    'Subject Data Table': 'subject_data_table'},
            value='Select the table you are using to plot data',
            placeholder='Select the table you are using to plot data',
        )
    
    
        dcc.Dropdown(
            id='select-axis-x',
            options={'Stats Output': 'stats_output',
                    'Group Data Table': 'group_data_table',
                    'Subject Data Table': 'subject_data_table'},
            value='Select the table you are using to plot data',
            placeholder='Select the table you are using to plot data',
        )
        
        dcc.Dropdown(
            id='select-axis-y',
            options={'Stats Output': 'stats_output',
                    'Group Data Table': 'group_data_table',
                    'Subject Data Table': 'subject_data_table'},
            value='Select the table you are using to plot data',
            placeholder='Select the table you are using to plot data',
        )
    
    #What table are we using for plot data?
        #Stats, Indiv_Data,Group_Data
        # If Indiv_Data or Group Data Need to kow how to filter the data such that selecting correct points -- the groups to pull
    
    #What data should be on the x axis?
    
    #What data should be on the y axis?
    
    #What phenotype and source of variation should be plotted? 
        #phenotype volume, FA AD RD MD etc, Source f variation (pull from stat sheet)
    #    
    #Would you like to reduce the number of entries displayed via a Rank ordering? 
        #Y,N -> then assign as None
        # if Y then assign the top_amount to the number given and sort_on to myConfig.y
    '''
    
    myConfig = Config(use_sheet='stats',x='GN_Symbol',y='percent_change_Young - -_Old - -',groups_to_include=None,config_reducereorder={'top_amount':10,'sort_on':'percent_change_Young - -_Old - -'},config_filter={'pval_BH':0.05,
                    'source_of_variation':'Age_Class',
                    'contrast':'fa_mean'})
    
    return myConfig

def create_config_prompt():
    myConfig=None

    return myConfig

# Initialize the Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1(children='CIVM Visualization Dashboard', style={'textAlign':'center', 'color':"#012169", 'font-size':24,'font-family':'Arial'}),
    html.Div([
        html.Div([
            html.Label("Group Statistical Results File Path: " , style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            dcc.Input(id='group_stats_path', type='text', value=None, placeholder='/Volumes/dusom_civm-kjh60/All_Staff/18.gaj.42/Scalar_and_Volume/Main_Effects_2025_01_14_NoB6/Non_Erode/Bilateral/Group_Statistical_Results_Age_Class_Strain_Sex.csv',style={'width': '50%'}),
            dcc.Loading(id="loading-1", type="default", delay_show=0, delay_hide=500, children=html.Div(id="loading-stat_sheet"))
        ]),
        html.Div([
            html.Label("Group Data Table File Path: ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            dcc.Input(id='group_data_path', type='text', value=None, placeholder='/Volumes/dusom_civm-kjh60/All_Staff/18.gaj.42/Scalar_and_Volume/Main_Effects_2025_01_14_NoB6/Non_Erode/Bilateral/Group_Data_Table_Age_Class_Strain_Sex.csv',style={'width': '50%'}),
            dcc.Loading(id="loading-2", type="default", delay_show=0, delay_hide=500, children=html.Div(id="loading-group_data"))
            ]),
        html.Div([
            html.Label("Subject Data Table File Path: ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            dcc.Input(id='indiv_data_path', type='text', value=None, placeholder='/Volumes/dusom_civm-kjh60/All_Staff/18.gaj.42/Scalar_and_Volume/Main_Effects_2025_01_14_NoB6/Non_Erode/Subject_Data_Table.csv',style={'width': '50%'}),
            dcc.Loading(id="loading-3", type="default", delay_show=0, delay_hide=500, children=html.Div(id="loading-indiv_data"))
            ]),
    ], style ={'width':'80%','margin':5}),
    
    html.Div([dcc.Dropdown(id='select-mode',
            options={'Manual': 'Manual','Prompt': 'Prompt'},
            value='Select Mode for Configuration Input',
            placeholder='Select Mode for Configuration Input',
        )],style ={'width':'80%', 'font-size':18, 'margin':5,'font-family':'Arial'}),
    html.Div([html.Div(id='table_select-container',children = dcc.Dropdown(options={'stats':'Group Statistical Results','group':'Group Data Table','indiv': 'Subject Data Table'},placeholder='Select Main Table for Visualization', id='table_options'), style ={'width':'80%', 'font-size':18, 'margin':5,'font-family':'Arial'}),]),
    html.Div([html.Div(id='output-container', className='chart-grid', style={'display': 'flex'}),])
])
#upload all data tables and stats sheets
@app.callback(Output("loading-stat_sheet", "children"),
    Input(component_id='group_stats_path',component_property='value'))
def update_input_stats (path):
    if path is not None and os.path.exists(path):
        time.sleep(2)
        global Group_Stats
        Group_Stats = load_stats(path)
        
        #This still does not handle what happens if the path does not extist or is none this will still spin but it won't actually load the data need a good error handler here
    return
@app.callback(Output("loading-group_data", "children"),
    Input(component_id='group_data_path',component_property='value'))
def update_input_group_data (path):
    if path is not None and os.path.exists(path):
        time.sleep(1)
        global Group_Data
        Group_Data = load_data(path,mode='group')
        
        #This still does not handle what happens if the path does not extist or is none this will still spin but it won't actually load the data need a good error handler here
    return
@app.callback(Output("loading-indiv_data", "children"),
    Input(component_id='indiv_data_path',component_property='value'))
def update_input_indiv_data (path):   
    if path is not None and os.path.exists(path): 
        time.sleep(1)
        global Indiv_Data
        Indiv_Data = load_data(path,mode='indiv')
        
        #This still does not handle what happens if the path does not extist or is none this will still spin but it won't actually load the data need a good error handler here
    return
#start Plot Callback
@app.callback(Output(component_id='output-container', component_property='children'),
             [Input(component_id='select-mode', component_property='value')])
def set_figure_to_output (mode):
    global myConfig
    if mode == 'Manual':
        myConfig=create_config_manual()
        if isinstance(Indiv_Data, DataStructure) and isinstance(Group_Data, DataStructure) and isinstance(Group_Stats, StatsStructure):
            return plot_by_config()
        else:
            return None
    elif mode == 'Prompt':
        myConfig=create_config_prompt()
        if isinstance(Indiv_Data, DataStructure) and isinstance(Group_Data, DataStructure) and isinstance(Group_Stats, StatsStructure):
            return plot_by_config()
        else: 
            return None
        '''
        drop_x=make_axis_input(list(Group_Stats.data.columns),'x')
        drop_y=make_axis_input(list(Group_Stats.data.columns),'y')
        radio_topN=make_radiobutton_topN()
        radio_Pval=make_radiobutton_pvalue()
        contrast_slider=make_slider(Group_Stats.contrast_options,'contrast_slider')
        sov_slider=make_slider(Group_Stats.sov_options,'sov_slider')

        A=[
         html.Div(className='x_y_input', children=[html.Div(children=drop_x),html.Div(children=drop_y)],style={'display':'grid'}),
         html.Div(
            html.Label("FILTER BY: ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            radio_Pval
         ),
        html.Div(
            html.Label("SHOW: ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            radio_topN,
         ),
         plot_by_config(config,Indiv_Data,Group_Data,Group_Stats),
        html.Div(
            html.Label("Contrast ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            contrast_slider,
         ),
        html.Div(
            html.Label("Source of Variation: ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),
            sov_slider,
         )
        ]
        print(A)
        '''
# filter and plot via the config file
def plot_by_config():
    if myConfig.filter is not None:
        Reduced_Stats=filter_stat_sheet(myConfig.filter,Group_Stats.data)
    else: 
        Reduced_Stats=Stats.data
        
    if myConfig.reduce_reorder is not None and myConfig.use_sheet == 'stats':
        plot_data=reduce_to_top(myConfig.reduce_reorder,Reduced_Stats)
    elif myConfig.reduce_reorder is not None and myConfig.use_sheet == 'indiv':
        Reduced_Stats=reduce_to_top(myConfig.reduce_reorder,Reduced_Stats)
        plot_data=collect_from_data(Reduced_Stats)
    elif myConfig.reduce_reorder is not None and myConfig.use_sheet == 'group':
        Reduced_Stats=reduce_to_top(myConfig.reduce_reorder,Reduced_Stats)
        plot_data=collect_from_data(Reduced_Stats)
    
    chart = dcc.Graph(id ='output-graph',
        figure=px.scatter(plot_data, 
            x=myConfig.x,
            y=myConfig.y,),
        style={'width': '50vw', 'height': '50vh'})
    
    return [html.Div(className='chart-item', children=[html.Div(children=chart)])]

#Helper files for creating proper filtering of data table and stat sheet
def filter_stat_sheet(config_filter,sheet):
    reduced_sheet=sheet 
    for f in config_filter:
        if f =='pval' or f =='pval_BH':
            reduced_sheet = reduced_sheet[reduced_sheet[f] < config_filter[f]]
        else:
            reduced_sheet=reduced_sheet[reduced_sheet[f] == config_filter[f]]
    return reduced_sheet

def collect_from_data(sheet):
    if myConfig.use_sheet == 'group':
        merged_data = pd.merge(sheet, Group_Data, on=myConfig.x, how='inner',copy=False,suffixes= ("", "_delete_me"))
    elif myConfig.use_sheet =='indiv':
        merged_data = pd.merge(sheet, Indiv_Data, on=myConfig.x, how='inner',copy=False,suffixes= ("", "_delete_me"))
        
    col_names=merged_data.columns
    for col in col_names:
        x=re.search(r'(_delete_me)$',col)
        if x: 
            merged_data.drop(columns=col,inplace=True)
    return merged_data

def reduce_to_top(config_reduce,sheet):
    sheet = sheet.sort_values(by=config_reduce['sort_on'],key=abs,ascending=False)
    return sheet[0:config_reduce['top_amount']]

def reduce_to_top_Data():  
    ## To do not yet actually filtering the data based on teh comparisons provided
    if myConfig.use_sheet == 'group':
        data_pivot = pd.pivot_table(Group_Data.data, values=myConfig.y, index=myConfig.x, columns=list(Group_Data.groupings.keys()))
    elif myConfig.use_sheet =='indiv':
        data_pivot = pd.pivot_table(Indiv_Data.data, values=myConfig.y, index=myConfig.x, columns=list(Indiv_Data.groupings.keys()))
    
    # we want to do a pairwise comparison of 
    for group_include in config.groups_to_include:
        data_pivot
    
    result = math.comb(n, k)
    # Do comparision to make sure we are considering all the comparisons to include in the graph. what has most to least. 
    myConfig.reduce_reorder['top_amount']
    data[0:myConfig.reduce_reorder['top_amount']]
    
    return 

def define_group_inputs_to_plot():
    if myConfig.use_sheet == 'group':
        group_iputs = Group_Data.groupings
    elif myConfig.use_sheet =='indiv':
        group_inputs = Indiv_Data.groupings
    
    return group_inputs

def make_axis_input(data_options,id_name):
    value_name= f"Select Data for {id_name}-axis"
    placeholder_name=f"Select Data for {id_name}-axis"
    dropdown = dcc.Dropdown(id=id_name,
            options=data_options,
            value=value_name,
            placeholder=placeholder_name,
        )
    return dropdown

def make_radiobutton_pvalue():
    radio=dcc.RadioItems(options={'NONE':'NONE','p-value':'pval','p-value with BH':'pval_BH'}, value='NONE', inline=True, id='radio_pval')
    return radio

def make_radiobutton_topN():
    radio=dcc.RadioItems(['ALL', 'TOP 10','TOP 20'], 'TOP 10', inline=True,id='radio_top')
    return radio

def make_slider(slider_input,id_name):
    slider_dict={}
    for i in range(len(slider_input)):
        slider_dict.update({i:slider_input[i]})
    slider=dcc.Slider(0, len(slider_input),marks=slider_dict, value=0, id=id_name)
    #either use'contrast_slider' or 'source_slider'
    return slider
            
# Run the Dash app
if __name__ == '__main__':
    app.run(debug=True)