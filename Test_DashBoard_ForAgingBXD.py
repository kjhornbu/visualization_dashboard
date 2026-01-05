#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import dash
import more_itertools
from dash import dcc, html, dash_table
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import re
import math
import time
import os

## ALL CLASS DEFINTIONS
class Config: 
    def __init__(self,use_sheet:str,x:str,y:str,groups_to_include:dict,config_reducereorder:dict,config_filter:dict):
        self.use_sheet = use_sheet
        self.x = x
        self.y = y
        self.groups_to_include=groups_to_include
        self.reduce_reorder = config_reducereorder #how the data to be plotted is reduced/ordered (show top Ntries, sorted on Y --- always sort on the Y entry?)
        self.filter = config_filter #Things applied to the Group Stats data set

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
    # Should this be more connected to the data struture, where we use what is found in one, to assume(and then validate) is present in the other?
    def __init__(self,row_idx:pd.Series,row_description:pd.Series,data: pd.DataFrame):
        DataStructure.__init__(self,row_idx=row_idx,row_description=row_description,mode='stats',data=data)
        [self.sov_options,self.contrast_options]= self.set_stats_groupings()
        
    def set_stats_groupings(self):
        self.sov_options=list(self.data['source_of_variation'].unique())
        self.contrast_options=list(self.data['contrast'].unique())
        
        return [self.sov_options, self.contrast_options]
    
## HELPER FUNCTIONS FOR DATA I/O
def check_header_rows(path):
    header_num = None
    n=0
    while header_num is None:
        data = pd.read_csv(path,delimiter='\t',low_memory=False,header=n,nrows=1000)
        for i,col in enumerate(data.columns):
            if type(col) is str:
                x=re.search(r'(id64_fSABI)$',col) #made one of our weird meta table regions so that we dont' accidently pull soemething from the raw meta table header in the googlesheet
                if x:
                    header_num=n
        n=n+1
    return header_num 

def load_data(path,mode):
    header_num=check_header_rows(path)
    data = pd.read_csv(path,delimiter='\t',low_memory=False,header=header_num)
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

## MODIFICTIONS TO DATA BASED ON FILTER TYPE AND OTHER CRITERIA
def use_config_on_Data():
    #main user of config
    if myConfig.filter is not None:
        Reduced_Stats=filter_stat_sheet(myConfig.filter,Group_Stats.data)
    else: 
        Reduced_Stats=Group_Stats.data
        
    if  myConfig.use_sheet == 'stats':
        plot_data=reduce_to_top(myConfig.reduce_reorder,Reduced_Stats)
    elif myConfig.use_sheet == 'indiv':
        Reduced_Stats=reduce_to_top(myConfig.reduce_reorder,Reduced_Stats)
        plot_data=collect_from_data(Reduced_Stats)
    elif myConfig.use_sheet == 'group':
        Reduced_Stats=reduce_to_top(myConfig.reduce_reorder,Reduced_Stats)
        plot_data=collect_from_data(Reduced_Stats)

    return plot_data

#Helper files for creating proper filtering of data table and stat sheet
def filter_stat_sheet(config_filter,sheet):
    reduced_sheet=sheet 
    
    for f in config_filter:
        if config_filter[f] is not None: # if is none in entry then we are not filtering based on that
            if f =='pval' or f =='pval_BH':
                reduced_sheet = reduced_sheet[reduced_sheet[f] < config_filter[f]]
            else:
                reduced_sheet=reduced_sheet[reduced_sheet[f] == config_filter[f]]
    return reduced_sheet

def collect_from_data(sheet):
    # Takes the (un)filtered Group Stats Results and combines it with the Indiv or Group Data Table so we have reduced or Maintained the # of ROI
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
    if config_reduce['top_amount']=='ALL':
        return sheet
    else:
        # Sort the reduced sheet on some sorting condition and return the top N (the sorting considered absolutes in conditioning)
        sheet = sheet.sort_values(by=config_reduce['sort_on'],key=abs,ascending=False)
        return sheet[0:config_reduce['top_amount']]

def reduce_to_top_Data():  
    ## To do not yet actually filtering the data based on the comparisons provided
    if myConfig.use_sheet == 'group':
        data_pivot = pd.pivot_table(Group_Data.data, values=myConfig.y, index=myConfig.x, columns=list(Group_Data.groupings.keys()))
    elif myConfig.use_sheet =='indiv':
        data_pivot = pd.pivot_table(Indiv_Data.data, values=myConfig.y, index=myConfig.x, columns=list(Indiv_Data.groupings.keys()))
    
    # we want to do a pairwise comparison of 
    for group_include in config.groups_to_include:
        data_pivot
    
    result = math.comb(n, k)
    # Do comparision to make sure we are considering all the comparisons to include in the graph. what has most to least. -- doesn't work currently
    myConfig.reduce_reorder['top_amount']
    data[0:myConfig.reduce_reorder['top_amount']]
    
    return 

## FIGURE LAYOUT BUILDER -- HELPER FUNCTIONS
# In the order of top to bottom of layout
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

def make_chart(plot_data):
    chart = dcc.Graph(id ='output-graph', figure=px.scatter(plot_data,x=myConfig.x, y=myConfig.y,),style={'width': '50vw', 'height': '50vh'})
    return chart

def make_slider(slider_input,id_name):
    slider_dict={}
    for i in range(len(slider_input)):
        slider_dict.update({i:slider_input[i]})
    slider=dcc.Slider(0, len(slider_input),marks=slider_dict, value=0, id=id_name)
    return slider

def make_grouping_selector(groups_to_include_options):
    group_datatable=dash_table.DataTable()
    return group_datatable

#Need the call back here to actually run the config manual generator
def generate_config(select_table_type,selected_radioPval,selected_radioTopN,selected_contrast,selected_sov,selected_x,selected_y,selected_groups_to_include):  
    
    if selected_radioPval=='NONE':
        set_pval='pval'
        set_pval_value=None
    else:
        set_pval=selected_radioPval
        set_pval_value=0.05
            
    if select_table_type == 'stats':
        selected_groups_to_include=None
        
    elif select_table_type == "indiv":
        selected_contrast=None
        selected_sov=None

    elif select_table_type == "group":
        selected_contrast=None
        selected_sov=None
    
    myConfig = Config(use_sheet=select_table_type,x=selected_x,y=selected_y,groups_to_include=selected_groups_to_include,config_reducereorder={'top_amount':selected_radioTopN,'sort_on':selected_y},config_filter={set_pval:set_pval_value,
                    'source_of_variation':selected_sov,
                    'contrast':selected_contrast})
    return myConfig

## INITALIZE THE DASH APP
app = dash.Dash(__name__)

## MAIN BODY OF THE DASH APP
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
    html.Div([html.Div(id='table-select-container')],style ={'width':'80%', 'font-size':18, 'margin':5,'font-family':'Arial'}),
    html.Div([html.Div(id='output-container', className='chart-grid', style={'display': 'flex'})])
])


# All your callbacks have to be between the end of the app layout and the app run call to work properly
## OBTAINING DATA CALLBACKS
@app.callback(Output("loading-stat_sheet", "children"),
    Input(component_id='group_stats_path',component_property='value'))
def update_input_stats (path):
    print(path)
    if path is not None and os.path.exists(path):
        time.sleep(1)
        global Group_Stats
        Group_Stats = load_stats(path)
    return

@app.callback(Output("loading-group_data", "children"),
    Input(component_id='group_data_path',component_property='value'))
def update_input_group_data (path):
    print(path)
    if path is not None and os.path.exists(path):
        time.sleep(1)
        global Group_Data
        Group_Data = load_data(path,mode='group')
    return

@app.callback(Output("loading-indiv_data", "children"),
    Input(component_id='indiv_data_path',component_property='value'))
def update_input_indiv_data (path):
    print(path)
    if path is not None and os.path.exists(path): 
        time.sleep(1)
        global Indiv_Data
        Indiv_Data = load_data(path,mode='indiv')
    return

@app.callback(Output(component_id='table-select-container',component_property='children'),Input(component_id='select-mode',component_property='value'))
def make_table_type_dropdown(input_mode):
    print('at table dropdown')
    if input_mode=='Manual':
        table_type_dropdown=dcc.Dropdown(options={'stats':'Group Statistical Results','group':'Group Data Table','indiv': 'Subject Data Table'},placeholder='Select Main Table for Visualization', id='main_plot_table')
        return table_type_dropdown
    elif input_mode =='Prompt':
        return None
    else:
        return None
    
## THE FULL FIGURE LAYOUT 
def full_fig_layout(select_table_4_plotting):
    #we need to know at least what table we are plotting from to be able to setup the full layout of the figure which then we query to setup the configuration
    radioPval=make_radiobutton_pvalue()# DCC
    radioTopN=make_radiobutton_topN()# DCC
    print('at full_fig_layout')
    if select_table_4_plotting == 'stats':
        x_options = list(Group_Stats.data.columns)
        y_options = list(Group_Stats.data.columns)
        
        drop_x=make_axis_input(x_options,'x') # DCC
        drop_y=make_axis_input(y_options,'y') #DCC
    
        slider_contrast=make_slider(Group_Stats.contrast_options,'contrast_slider') #DCC
        slider_sov=make_slider(Group_Stats.sov_options,'sov_slider') #DCC
    
        fig_layout = [html.Div(className='chart-item', children=[html.Div(children=drop_x),html.Div(children=drop_y)],style={'display':'grid'}),
                html.Div(className='chart-item', children=[html.Div(children=radioPval)],style={'display':'grid'}),
                html.Div(className='chart-item', children=[html.Div(children=radioTopN)],style={'display':'grid'}),
                html.Div(className='chart-item', children=[html.Div(children=radioTopN)],style={'display':'grid'})]

    elif select_table_4_plotting == 'indiv':
        x_options = list(Indiv_Data.data.columns)
        y_options = list(Indiv_Data.data.columns)
            
        drop_x=make_axis_input(x_options,'x') # DCC
        drop_y=make_axis_input(y_options,'y') #DCC
            
        groups_to_include_options = Indiv_Data.groupings

        group_datatable=make_grouping_selector(groups_to_include_options)#DCC    
        slider_contrast=None
        slider_sov=None

        fig_layout = [html.Div(className='chart-item', children=[html.Div(children=drop_x),html.Div(children=drop_y)],style={'display':'grid'}),
                html.Div(className='chart-item', children=[html.Div(children=radioPval)],style={'display':'grid'}),
                html.Div(className='chart-item', children=[html.Div(children=radioTopN)],style={'display':'grid'}),
                html.Div(className='chart-item', children=[html.Div(children=radioTopN)],style={'display':'grid'})]
            
    elif select_table_4_plotting == 'group':
        x_options = list(Group_Data.data.columns)
        y_options = list(Group_Data.data.columns)
            
        drop_x=make_axis_input(x_options,'x') # DCC
        drop_y=make_axis_input(y_options,'y') #DCC
            
        groups_to_include_options = Group_Data.groupings

        group_datatable=make_grouping_selector(groups_to_include_options)#DCC    
        slider_contrast=None
        slider_sov=None

        fig_layout = [html.Div(className='chart-item', children=[html.Div(children=drop_x),html.Div(children=drop_y)],style={'display':'grid'}),
                html.Div(className='chart-item', children=[html.Div(children=radioPval)],style={'display':'grid'}),
                html.Div(className='chart-item', children=[html.Div(children=radioTopN)],style={'display':'grid'}),
                html.Div(className='chart-item', children=[html.Div(children=radioTopN)],style={'display':'grid'})]
    
    return fig_layout

## HAve to have the config to do the config and that is screwing with me. The actual configuration setup needs a ton of selection points or at least set data....
#start Plot Callback
@app.callback(Output(component_id='output-container', component_property='children'),[Input(component_id='main_plot_table',component_property='value')])
def set_figure_to_output_Manual(select_table_4_plotting):
    global myConfig
    message= 'Make Sure All Data Files Are Loaded and Exist At Path Location'
    print('right before generating config')
    myConfig=generate_config()
    if isinstance(Indiv_Data, DataStructure) and isinstance(Group_Data, DataStructure) and isinstance(Group_Stats, StatsStructure):
        return full_fig_layout(select_table_4_plotting)
    else:
        return [html.Div(className='chart-item', children=[html.Div(children=dcc.Input(id="Error_on_loading_Manual", value=message))])]
    
    ## RUN THE DASH APP
if __name__ == '__main__':
    app.run(debug=True)