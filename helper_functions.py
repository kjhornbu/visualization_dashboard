# In[ ]:

from dash import Dash,dcc, html, dash_table, Input, Output, State
import pandas as pd
import numpy as np
import plotly.express as px
import re
import math
from classes import *
import persistentData

## HELPER FUNCTIONS FOR DATA I/O
def check_header_rows(path):
    header_num = None
    n=0
    nrows_load_max=100
    while header_num is None:
        data = pd.read_csv(path,delimiter='\t',low_memory=False,header=n,nrows=nrows_load_max)
        for i,col in enumerate(data.columns):
            if type(col) is str:
                x=re.search(r'^(id64_fSABI)$',col) #made one of our weird meta table regions so that we dont' accidently pull soemething from the raw meta table header in the googlesheet
                if x:
                    header_num=n
        n=n+1
        if n>nrows_load_max:
            return None

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
def collect_from_data(sheet,data_playwith):
    series=sheet[persistentData.Plot_Configurations["myConfig"].x]
    series_name=[]
    for n in range(0,len(data_playwith.columns[0])):
        if n==0:
            series_name.append(series.name)
        else:
            series_name.append('')
    
    series.name=tuple(series_name)
    # Takes the (un)filtered Group Stats Results and combines it with the Indiv or Group Data Table so we have reduced or Maintained the # of ROI
    if persistentData.Plot_Configurations["myConfig"].use_sheet == 'group':
        merged_data = pd.merge(series, data_playwith, on=persistentData.Plot_Configurations["myConfig"].x, how='inner',copy=False,suffixes= ("", "_delete_me"))
    elif persistentData.Plot_Configurations["myConfig"].use_sheet =='indiv':
        merged_data = pd.merge(series, data_playwith, on=persistentData.Plot_Configurations["myConfig"].x, how='inner',copy=False,suffixes= ("", "_delete_me"))
    col_names=merged_data.columns
    print(merged_data)
    for col in col_names:
        x=re.search(r'(_delete_me)$',col)
        if x:
            merged_data.drop(columns=col,inplace=True)
    return merged_data

def filter_stat_sheet(config_filter,sheet):
    reduced_sheet=sheet
    for f in config_filter:
        x=isinstance(config_filter[f], dict)
        if config_filter[f] is not None and not x: # if is none in entry then we are not filtering based on that
            if f =='pval' or f =='pval_BH':
                reduced_sheet = reduced_sheet[reduced_sheet[f] < config_filter[f]]
            else:
                reduced_sheet=reduced_sheet[reduced_sheet[f] == config_filter[f]]          
    return reduced_sheet

def use_config_on_Data():
    #main user of config
    if persistentData.Plot_Configurations["myConfig"].filter is not None and persistentData.Plot_Configurations["myConfig"].filter['contrast'] is not None and persistentData.Plot_Configurations["myConfig"].filter['source_of_variation'] is not None:
        Reduced_Stats=filter_stat_sheet(persistentData.Plot_Configurations["myConfig"].filter,persistentData.Group_Stats.data)
    else:  
        Reduced_Stats=persistentData.Group_Stats.data
      
    if  persistentData.Plot_Configurations["myConfig"].use_sheet == 'stats':
        plot_data=reduce_to_top(persistentData.Plot_Configurations["myConfig"].reduce_reorder,Reduced_Stats)
    elif persistentData.Plot_Configurations["myConfig"].use_sheet == 'indiv':
        data_playwith=reduce_to_top_Data(persistentData.Plot_Configurations["myConfig"].reduce_reorder)
        plot_data=collect_from_data(Reduced_Stats,data_playwith)
    elif persistentData.Plot_Configurations["myConfig"].use_sheet == 'group':
        data_playwith=reduce_to_top_Data(persistentData.Plot_Configurations["myConfig"].reduce_reorder)
        plot_data=collect_from_data(Reduced_Stats,data_playwith)
    return plot_data

#Helper files for creating proper filtering of data table and stat sheet
def reduce_to_top(config_reduce,Reduced_Stats):
    if config_reduce['top_amount'] == 'None':
        return Reduced_Stats
    elif config_reduce['top_amount'] == 'All':
        Reduced_Stats = Reduced_Stats.sort_values(by=config_reduce['sort_on'],key=abs,ascending=False)
        return Reduced_Stats
    else:
        Reduced_Stats = Reduced_Stats.sort_values(by=config_reduce['sort_on'],key=abs,ascending=False)
        return Reduced_Stats[0:int(config_reduce['top_amount'])]

def reduce_to_top_Data(config_reduce):
    frames=[]
    if persistentData.Plot_Configurations["myConfig"].use_sheet == 'group':
        data_pivot = pd.pivot_table(persistentData.Group_Data.data, values=persistentData.Plot_Configurations["myConfig"].y, index=persistentData.Plot_Configurations["myConfig"].x, columns=list(persistentData.Group_Data.groupings.keys()))
    elif persistentData.Plot_Configurations["myConfig"].use_sheet =='indiv':
        data_pivot = pd.pivot_table(persistentData.Indiv_Data.data, values=persistentData.Plot_Configurations["myConfig"].y, index=persistentData.Plot_Configurations["myConfig"].x, columns=list(persistentData.Indiv_Data.groupings.keys()))
    for i in range(len(persistentData.Plot_Configurations["myConfig"].groups_to_include)):
        data_dict=persistentData.Plot_Configurations["myConfig"].groups_to_include[i]
        data_values=tuple(data_dict.values())
        frames.append(data_pivot[data_values])
    data_playwith = pd.concat(frames, axis=1)
    
    # Sort data into most least different for each row to see the maximal range of expression
    max_per_row = data_playwith.max(axis='columns')
    min_per_row = data_playwith.min(axis='columns')
    data_playwith['sorting_column']=abs(max_per_row-min_per_row)

    if config_reduce['top_amount'] == 'None':
        return data_playwith
    elif config_reduce['top_amount'] == 'All':
        data_playwith = data_playwith.sort_values(by='sorting_column',key=abs,ascending=False)
        return data_playwith
    else:
        data_playwith = data_playwith.sort_values(by='sorting_column',key=abs,ascending=False)
        return data_playwith[0:int(config_reduce['top_amount'])]
    
## FIGURE LAYOUT BUILDER -- HELPER FUNCTIONS
# In the order of top to bottom of layout
def make_axis_input(data_options,id_name):
    value_name= f"Select Data for {id_name}-axis"
    placeholder_name=f"Select Data for {id_name}-axis"
    dropdown = dcc.Dropdown(id=id_name,
            options=data_options,
            value=value_name,
            placeholder=placeholder_name)
    return dropdown

def make_radiobutton_pvalue():
    radio=html.Div([html.Label("Filter by Significance:  ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),dcc.RadioItems(options={'NONE':'NONE','pval':'p-value','pval_BH':'p-value with BH correction'}, inline=True, id='radio_pval')])
    return radio

def make_radiobutton_topN():
    radio=html.Div([html.Label("Select X-Axis Windowing: ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),dcc.RadioItems({'None':'All without Sorting','All':'All with Sorting',10:'TOP 10',20:'TOP 20'}, inline=True,id='radio_TopN')])
    return radio

def make_chart(plot_data):
    chart = dcc.Graph(id ='output-graph', figure=px.scatter(plot_data,x=persistentData.Plot_Configurations["myConfig"].x, y=persistentData.Plot_Configurations["myConfig"].y,),style={'width': '50vw', 'height': '50vh'})
    return chart

def make_slider(slider_input,id_name,label):
    slider_dict={}
    for i in range(len(slider_input)):
        slider_dict.update({slider_input[i]:slider_input[i]})   
    slider=html.Div([html.Label(label, style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),dcc.RadioItems(slider_dict,inline=True,id=id_name)])
    return slider

def make_grouping_selector(groups_to_include):
    columns=[]
    data_row={}
    dropdown={}
    column_name=list(groups_to_include.keys())
    for i in range(len(column_name)):
        columns.append({'id':column_name[i], 'name':column_name[i], 'presentation':'dropdown'})
        data_row.update({column_name[i]: groups_to_include[column_name[i]][0]})
        dropdown_options=[]
        for j in range(len(groups_to_include[column_name[i]])):
            dropdown_options.append({'label':groups_to_include[column_name[i]][j], 'value':groups_to_include[column_name[i]][j]})       
        dropdown.update({column_name[i]:{'options': dropdown_options}})
    group_datatable=dash_table.DataTable(id='group_selection_table', columns = columns, data=[data_row], dropdown=dropdown, editable=True, row_deletable=True)
    return group_datatable
    
def make_go_button():
    button=html.Button('Plot Graph', id='go_button', n_clicks=0)
    return button
def make_add_button():
    add_button=html.Button('Add Row', id='add-rows-button', n_clicks=0)
    return add_button
def top_config_input():
    radioPval=make_radiobutton_pvalue() #DCC
    radioTopN=make_radiobutton_topN() #DCC
    
    if persistentData.Plot_Configurations["myConfig"].use_sheet == 'stats':
        x_options = list(persistentData.Group_Stats.data.columns)
        y_options = list(persistentData.Group_Stats.data.columns)
    else: 
        if persistentData.Plot_Configurations["myConfig"].use_sheet == 'indiv':
            x_options = list(persistentData.Indiv_Data.data.columns)
            y_options = list(persistentData.Indiv_Data.data.columns)

        elif persistentData.Plot_Configurations["myConfig"].use_sheet == 'group':
            x_options = list(persistentData.Group_Data.data.columns)
            y_options = list(persistentData.Group_Data.data.columns)
        
    drop_x=make_axis_input(x_options,'x') #DCC
    drop_y=make_axis_input(y_options,'y') #DCC
   
    config_layout_top = [
                    html.Div(className='chart-item', children=[html.Div(children=drop_x)],style={'display':'grid','width': '100%'}),
                    html.Div(className='chart-item', children=[html.Div(children=drop_y)],style={'display':'grid','width': '100%'}),
                    html.Div(className='chart-item', children=[html.Div(children=radioPval)],style={'display':'grid','width': '100%'}),
                    html.Div(className='chart-item', children=[html.Div(children=radioTopN)],style={'display':'grid','width': '100%'})]
    
    fig_layout=html.Div(className='chart-item', children=config_layout_top,id='config_top')
    return fig_layout

def bottom_config_input():
    plot_the_fig=make_go_button() #DCC
    
    slider_contrast=make_slider(persistentData.Group_Stats.contrast_options,'contrast_slider',"Contrast Options: ") #DCC
    slider_sov=make_slider(persistentData.Group_Stats.sov_options,'sov_slider',"Source of Variation Options: ") #DCC
        
    if persistentData.Plot_Configurations["myConfig"].use_sheet == 'stats':
        
        config_layout_bottom = [
            html.Div(className='chart-item', children=[html.Div(children=slider_contrast)],style={'display':'grid','width': '100%'}),
            html.Div(className='chart-item', children=[html.Div(children=slider_sov)],style={'display':'grid','width': '100%'}),
            html.Div(className='chart-item', children=[html.Div(children=plot_the_fig)],style={'display':'grid','width': '100%'})]
    else: 
        add_row=make_add_button()#DCC
        if persistentData.Plot_Configurations["myConfig"].use_sheet == 'indiv':
            groups_to_include_options = persistentData.Indiv_Data.groupings

        elif persistentData.Plot_Configurations["myConfig"].use_sheet == 'group':
            groups_to_include_options = persistentData.Group_Data.groupings
            
        group_datatable=make_grouping_selector(groups_to_include_options)#DCC

        config_layout_bottom= [
            html.Div(className='chart-item', children=[html.Div(children=slider_contrast)],style={'display':'grid','width': '100%'}),
            html.Div(className='chart-item', children=[html.Div(children=slider_sov)],style={'display':'grid','width': '100%'}),
            html.Div(className='chart-item', children=[html.Div(children=group_datatable)],style={'display':'grid','width': '100%'}),
            html.Div(className='chart-item', children=[html.Div(children=add_row)],style={'display':'grid','width': '100%'}),
            html.Div(className='chart-item', children=[html.Div(children=plot_the_fig)],style={'display':'grid','width': '100%'})]
    
    fig_layout=html.Div(className='chart-item', children=config_layout_bottom,id='config_bottom')
    return fig_layout

## THE FULL Config Input layout
def full_figure_config_input():
    top_layout=top_config_input()
    bottom_layout=bottom_config_input()
    return [html.Div(className='chart-item', children=top_layout),html.Div(className='chart-item', children=bottom_layout)]