# In[ ]:

from dash import Dash,dcc, html, dash_table, Input, Output
import pandas as pd
import plotly.express as px
import re
import math
from classes import *
#from persistentData import Indiv_Data, Group_Data, Group_Stats
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
    print(header_num)
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
    if myPlotConfig.filter is not None:
        Reduced_Stats=filter_stat_sheet(myPlotConfig.filter,persistentData.Group_Stats.data)
    else:
        Reduced_Stats=persistentData.Group_Stats.data

    if  myPlotConfig.use_sheet == 'stats':
        plot_data=reduce_to_top(myPlotConfig.reduce_reorder,Reduced_Stats)
    elif myPlotConfig.use_sheet == 'indiv':
        Reduced_Stats=reduce_to_top(myPlotConfig.reduce_reorder,Reduced_Stats)
        plot_data=collect_from_data(Reduced_Stats)
    elif myPlotConfig.use_sheet == 'group':
        Reduced_Stats=reduce_to_top(myPlotConfig.reduce_reorder,Reduced_Stats)
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
    if myPlotConfig.use_sheet == 'group':
        merged_data = pd.merge(sheet, persistentData.Group_Data, on=myPlotConfig.x, how='inner',copy=False,suffixes= ("", "_delete_me"))
    elif myPlotConfig.use_sheet =='indiv':
        merged_data = pd.merge(sheet, persistentData.Indiv_Data, on=myPlotConfig.x, how='inner',copy=False,suffixes= ("", "_delete_me"))

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
    if myPlotConfig.use_sheet == 'group':
        data_pivot = pd.pivot_table(persistentData.Group_Data.data, values=myPlotConfig.y, index=myPlotConfig.x, columns=list(persistentData.Group_Data.groupings.keys()))
    elif myPlotConfig.use_sheet =='indiv':
        data_pivot = pd.pivot_table(persistentData.Indiv_Data.data, values=myPlotConfig.y, index=myPlotConfig.x, columns=list(persistentData.Indiv_Data.groupings.keys()))

    # we want to do a pairwise comparison of
    for group_include in config.groups_to_include:
        data_pivot

    result = math.comb(n, k)
    # Do comparision to make sure we are considering all the comparisons to include in the graph. what has most to least. -- doesn't work currently
    myPlotConfig.reduce_reorder['top_amount']
    data[0:myPlotConfig.reduce_reorder['top_amount']]

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
    chart = dcc.Graph(id ='output-graph', figure=px.scatter(plot_data,x=myPlotConfig.x, y=myPlotConfig.y,),style={'width': '50vw', 'height': '50vh'})
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
        selected_contrast=Nonem
        selected_sov=None

    myPlotConfig = PlotConfig(use_sheet=select_table_type,x=selected_x,y=selected_y,groups_to_include=selected_groups_to_include,config_reducereorder={'top_amount':selected_radioTopN,'sort_on':selected_y},config_filter={set_pval:set_pval_value,
                    'source_of_variation':selected_sov,
                    'contrast':selected_contrast})
    return myPlotConfig

## THE FULL FIGURE LAYOUT
def full_fig_layout(select_table_4_plotting):
    #we need to know at least what table we are plotting from to be able to setup the full layout of the figure which then we query to setup the configuration
    radioPval=make_radiobutton_pvalue()# DCC
    radioTopN=make_radiobutton_topN()# DCC
    if select_table_4_plotting == 'stats':
        x_options = list(persistentData.Group_Stats.data.columns)
        y_options = list(persistentData.Group_Stats.data.columns)

        drop_x=make_axis_input(x_options,'x') # DCC
        drop_y=make_axis_input(y_options,'y') #DCC

        slider_contrast=make_slider(persistentData.Group_Stats.contrast_options,'contrast_slider') #DCC
        slider_sov=make_slider(persistentData.Group_Stats.sov_options,'sov_slider') #DCC

        fig_layout = [html.Div(className='chart-item', children=[html.Div(children=drop_x),html.Div(children=drop_y)],style={'display':'grid'}),
                html.Div(className='chart-item', children=[html.Div(children=radioPval)],style={'display':'grid'}),
                html.Div(className='chart-item', children=[html.Div(children=radioTopN)],style={'display':'grid'}),
                html.Div(className='chart-item', children=[html.Div(children=radioTopN)],style={'display':'grid'})]

    elif select_table_4_plotting == 'indiv':
        x_options = list(persistentData.Indiv_Data.data.columns)
        y_options = list(persistentData.Indiv_Data.data.columns)

        drop_x=make_axis_input(x_options,'x') # DCC
        drop_y=make_axis_input(y_options,'y') #DCC

        groups_to_include_options = persistentData.Indiv_Data.groupings

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
