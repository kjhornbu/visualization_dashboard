# In[ ]:

from dash import Dash,dcc, html, dash_table, Input, Output, State
import pandas as pd
import numpy as np
import plotly.express as px
import re
import math
from classes import *
import persistentData
import copy


## HELPER FUNCTIONS FOR DATA I/O


def check_header_rows(path):
    header_num = None
    n=0
    nrows_load_max=100
    while header_num is None:
        if n>nrows_load_max:
            return None
        try:
            data = pd.read_csv(path,delimiter='\t',low_memory=False,header=n,nrows=nrows_load_max)

            for i,col in enumerate(data.columns):
                if type(col) is str:
                    x=re.search(r'^(id64_fSABI)$',col) #made one of our weird meta table regions so that we dont' accidently pull soemething from the raw meta table header in the googlesheet
                    if x:
                        header_num=n
            n=n+1
        except:
            n=n+1
            continue
    return header_num

def load_data(path,mode):
    header_num=check_header_rows(path)
    data = pd.read_csv(path,delimiter='\t',low_memory=False,header=header_num)
    data_col_idx=data.iloc[0]
    data_comments=data.iloc[1]
    data = data.drop([data.index[0],data.index[1]]).reset_index()
    myData=DataStructure(path=path,row_idx = data_col_idx,row_description = data_comments,data = data,mode=mode) # Create Data (indiv or Group) class
    return myData

def load_stats(path):
    header_num=check_header_rows(path)
    stats = pd.read_csv(path,delimiter='\t',low_memory=False,header=header_num)
    stats_col_idx=stats.iloc[0]
    stats_comments=stats.iloc[1]
    stats = stats.drop([stats.index[0],stats.index[1]]).reset_index()
    myStats = StatsStructure(path=path,row_idx = stats_col_idx,row_description = stats_comments,data = stats)
    return myStats


## MODIFICTIONS TO DATA BASED ON FILTER TYPE AND OTHER CRITERIA


def collect_from_data(sheet,data_playwith):
    if (persistentData.Plot_Configurations["myConfig"].filter.get('pval') == None):
        return data_playwith #-- This would just not apply a filter in the case of indicating that there is no Filtering... but we want it to be dumb so no extra problems.
    else:
        # Takes the (un)filtered GStats Results and combines it with the Indiv or Group Data Table so we have reduced or Maintained the # of ROI
        df=sheet[persistentData.Plot_Configurations["myConfig"].x].to_frame()
        merged_data = pd.merge(data_playwith,df,on=persistentData.Plot_Configurations["myConfig"].x, how='inner',copy=False) # The order HAS TO BE this if you switch it you get a Requested axis not found in manager error

        for col in merged_data.columns:
            if not (isinstance(col, str) or (isinstance(col, tuple) and (isinstance(col[0],str)))):
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
    if persistentData.Plot_Configurations["myConfig"].filter is not None and persistentData.Plot_Configurations["myConfig"].filter['contrast'] is not None and persistentData.Plot_Configurations["myConfig"].filter['source_of_variation'] is not None:
        Reduced_Stats=filter_stat_sheet(persistentData.Plot_Configurations["myConfig"].filter,persistentData.Group_Stats.data)
    else:
        Reduced_Stats=persistentData.Group_Stats.data
    if  persistentData.Plot_Configurations["myConfig"].use_sheet == 'stats':
        plot_data=reduce_to_top(persistentData.Plot_Configurations["myConfig"].reduce_reorder,Reduced_Stats)
    elif persistentData.Plot_Configurations["myConfig"].use_sheet == 'indiv' or persistentData.Plot_Configurations["myConfig"].use_sheet == 'group':
        data_playwith=reduce_to_top_Data(persistentData.Plot_Configurations["myConfig"].reduce_reorder)
        plot_data=collect_from_data(Reduced_Stats,data_playwith)

    return plot_data


#Helper files for creating proper filtering of data table and stat sheet

def reduce_to_top(config_reduce,data):

    if (persistentData.Plot_Configurations["myConfig"].y == 'pval') or (persistentData.Plot_Configurations["myConfig"].y == 'pval_BH'):
        #pvalues that are meaninful are small not large (basically only thing to do that)
        ascending_dir=True
    else:
        ascending_dir=False

    if persistentData.Plot_Configurations["myConfig"].use_sheet == 'stats':
        sort_on=config_reduce['sort_on']
    elif persistentData.Plot_Configurations["myConfig"].use_sheet == 'group' or persistentData.Plot_Configurations["myConfig"].use_sheet == 'indiv':
        sort_on='sorting_column'


    if config_reduce['top_amount'] == 'None':
        return data
    elif config_reduce['top_amount'] == 'All':
        data = data.sort_values(by=sort_on,key=abs,ascending=ascending_dir)
        return data
    else:
        data = data.sort_values(by=sort_on,key=abs,ascending=ascending_dir)

        #Make adjustment factors for repeating units within the dataset
        if persistentData.Plot_Configurations["myConfig"].use_sheet == 'stats':
            factor=1
        elif persistentData.Plot_Configurations["myConfig"].use_sheet == 'group':
            factor=len(data['variable'].unique())
            #How many groupings to include

        elif persistentData.Plot_Configurations["myConfig"].use_sheet == 'indiv':
            #Need to just pull out of sheet because the n associated with each grouping is not defined simpliy
            x_inSheet=data[persistentData.Plot_Configurations["myConfig"].x].unique()
            for n in range(int(config_reduce['top_amount'])):
                select_data=data[data[persistentData.Plot_Configurations["myConfig"].x]==x_inSheet[n]]
                if n > 0:
                    temp_data=pd.concat([temp_data, select_data], ignore_index=True)
                else:
                    temp_data=select_data

        if (persistentData.Plot_Configurations["myConfig"].use_sheet == 'stats') or (persistentData.Plot_Configurations["myConfig"].use_sheet == 'group'):
            return data[0:(int(factor)*int(config_reduce['top_amount']))]
        elif persistentData.Plot_Configurations["myConfig"].use_sheet == 'indiv':
            return temp_data

def pull_hemisphere_data():
    # Filter to desired hemisphere in Indiv Data
    data_work=copy.deepcopy(persistentData.Indiv_Data.data)

    if persistentData.Plot_Configurations["myConfig"].reduce_reorder['hemisphere'] == 'B':
        data_work=data_work[data_work['hemisphere_assignment']=='0']
    elif persistentData.Plot_Configurations["myConfig"].reduce_reorder['hemisphere'] == 'L':
        data_work=data_work[data_work['hemisphere_assignment']=='-1']
    elif persistentData.Plot_Configurations["myConfig"].reduce_reorder['hemisphere'] == 'R':
        data_work=data_work[data_work['hemisphere_assignment']=='1']
    return data_work

def reduce_to_top_Data(config_reduce):
    Prepped_Data=prep_Data_for_reduce()
    if ('variable' not in Prepped_Data.columns) or ('value' not in Prepped_Data.columns):
        column_name=[]
        for i,col in enumerate(Prepped_Data.columns):
            column_name.append("".join(col))
        Prepped_Data.columns=column_name
        Prepped_Data_melt=pd.melt(Prepped_Data,id_vars=persistentData.Plot_Configurations["myConfig"].x,value_vars=Prepped_Data.columns[1:-1])
        Prepped_Data_Sorting=Prepped_Data[[persistentData.Plot_Configurations["myConfig"].x,'sorting_column']]
        Prepped_Data_Melt_Plus_Reattach=pd.merge(Prepped_Data_melt,Prepped_Data_Sorting,on=persistentData.Plot_Configurations["myConfig"].x, how='inner',copy=False)

        return reduce_to_top(config_reduce,Prepped_Data_Melt_Plus_Reattach)
    else:
        return reduce_to_top(config_reduce,Prepped_Data)

def prep_Data_for_reduce():
    if persistentData.Plot_Configurations["myConfig"].use_sheet == 'group':
        data_playwith=prep_Data_Group()
        data_playwith=data_playwith.reset_index()
    elif persistentData.Plot_Configurations["myConfig"].use_sheet =='indiv':
        data_playwith=prep_Data_Indiv()
    return data_playwith

def prep_Data_Group(from_indiv=False,alt_columns=None):
    frames=[]
    All_Group_Entries_v2=[]
    if from_indiv:
        data_work=pull_hemisphere_data()
        data_name_full=list(alt_columns)
        data_pivot = pd.pivot_table(data_work, values=persistentData.Plot_Configurations["myConfig"].y, index=persistentData.Plot_Configurations["myConfig"].x, columns=data_name_full)
        #Setup the All_group_Entries
        All_Group_Entries=copy.deepcopy(persistentData.Plot_Configurations["myConfig"].groups_to_include) # Using a Deep copy so we have an independent group of gorups to include to work off of for this

        full_alt_Key_Complier=[]
        for i in range(len(All_Group_Entries)):
            data_dict=All_Group_Entries[i]
            alt_columns_keys=alt_columns.keys()
            adjusted_dict={}
            alt_Key_Compiler=[]
            for j,key in enumerate(alt_columns_keys):
                adjusted_dict.update({key:data_dict.pop(key)})
                if adjusted_dict[key] != '-':
                    alt_Key_Compiler.append(key)
            full_alt_Key_Complier.append(alt_Key_Compiler)
            All_Group_Entries_v2.append(adjusted_dict)

        All_Group_Entries=All_Group_Entries_v2
        unique_tuples = set(tuple(inner_list) for inner_list in full_alt_Key_Complier)
        # Convert tuples back to lists
        unique_full_alt_Key_Complier = [list(tup) for tup in unique_tuples]

        #Chekc for unique_full_alt_Key_Complier == to the data_name_full so don't double up creating things
        for i in range(len(unique_full_alt_Key_Complier)):
            if data_name_full in unique_full_alt_Key_Complier[i]:
                unique_full_alt_Key_Complier[i].pop(1)

        if len(alt_columns)>1:
            # Make multiple extra rows with the - and stuff to fill out what is needed in combinations
            # Need combinations now can't just do the single add here.... how am I going to put that into here.
            for i in range(len(unique_full_alt_Key_Complier)):

                data_pivot_2 = pd.pivot_table(data_work, values=persistentData.Plot_Configurations["myConfig"].y, index=persistentData.Plot_Configurations["myConfig"].x, columns=unique_full_alt_Key_Complier[i])

                data_columns=data_pivot_2.columns
                data_name=data_pivot_2.columns.names
                data_column_total=[]

                for col in range(len(data_columns)):
                    data_column_adjust=[]
                    for n,name in enumerate(data_name_full):
                        count=0
                        for m,name_2 in enumerate(data_name):
                            if (name == name_2) and (count != 1):
                                count=1
                                if len(unique_full_alt_Key_Complier[i])>1:
                                    data_column_adjust.append(data_columns[col][m])
                                else:
                                    data_column_adjust.append(data_columns[col])
                        if count != 1:
                            data_column_adjust.append('-')
                    data_column_total.append(tuple(data_column_adjust))

                column_name=pd.MultiIndex.from_tuples(data_column_total,names=data_name_full)
                data_pivot_2.columns=column_name
                data_pivot=pd.concat([data_pivot,data_pivot_2],axis=1)

    else:
        data_pivot = pd.pivot_table(persistentData.Group_Data.data, values=persistentData.Plot_Configurations["myConfig"].y, index=persistentData.Plot_Configurations["myConfig"].x, columns=list(persistentData.Group_Data.groupings.keys()))
        All_Group_Entries=persistentData.Plot_Configurations["myConfig"].groups_to_include #These groups to include has the additional groups which we don't have

    for i in range(len(All_Group_Entries)):
        data_dict=All_Group_Entries[i]
        if len(data_dict) == 1:
            data_values=list(data_dict.values())
        else:
            data_values=tuple(data_dict.values())

        frames.append(data_pivot[data_values])

    data_playwith = pd.concat(frames, axis=1)
    max_per_row = data_playwith.max(axis='columns')
    min_per_row = data_playwith.min(axis='columns')
    data_playwith['sorting_column']=abs(max_per_row-min_per_row)

    return data_playwith

def prep_Data_Indiv():
    frames=[]
    alt_Key_Compiler=[]
    for i in range(len(persistentData.Plot_Configurations["myConfig"].groups_to_include)):
        data_work=pull_hemisphere_data()
        data_dict=persistentData.Plot_Configurations["myConfig"].groups_to_include[i]
        data_dict_keys=data_dict.keys()
        data_values=tuple(data_dict.values())

        for j,key in enumerate(data_dict_keys):
            if data_dict[key] != '-':
                data_work=data_work[data_work[key]==data_dict[key]]
                alt_Key_Compiler.append(key)

        temp_work=data_work[[persistentData.Plot_Configurations["myConfig"].x,persistentData.Plot_Configurations["myConfig"].y]]
        temp_work=temp_work.rename(columns={persistentData.Plot_Configurations["myConfig"].y:data_values})
        melt_plot_data=pd.melt(temp_work,id_vars=persistentData.Plot_Configurations["myConfig"].x,value_vars=temp_work.columns[1:])
        frames.append(melt_plot_data)

    data_playwith = pd.concat(frames, axis=0)  #This combines so each specimen's region entry for a given contrast is relayed (231*Nspecimen rows)
    data_playwith_Group=prep_Data_Group(True,dict.fromkeys(alt_Key_Compiler)) # we get the grouped data from the indiv data (don't use group because there is not a 1 to 1 for every data term in the group data table for the subject data table)

    data_playwith_GroupReduced=data_playwith_Group['sorting_column'] # grab the sorting column because we only want that don't need what came into it.
    data_playwith_GroupReduced.name=('sorting_column') # make sure its at a first level by reassigning like this

    merged_data = pd.merge(data_playwith,data_playwith_GroupReduced,on=persistentData.Plot_Configurations["myConfig"].x, how='inner',copy=False) # The order HAS TO BE this if you switch it you get a Requested axis not found in manager erro -- We are putting group mean responses onto the subject data so we can sort for plotting
    return merged_data


## FIGURE LAYOUT BUILDER -- HELPER FUNCTIONS
# These are all the parts needed to assign configuration for plotting


def make_axis_input(data_options,id_name):
    value_name= f"Select Data for {id_name}-axis"
    placeholder_name=f"Select Data for {id_name}-axis"
    dropdown = dcc.Dropdown(id=id_name,
            options=data_options,
            value=value_name,
            placeholder=placeholder_name)
    return dropdown

def make_radiobutton_pvalue():
    radio=html.Div([html.Label("Filter by Significance (NOTE HEMISPHERE OF Group_Statistical_Results FILE):  ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),dcc.RadioItems(options={'NONE':'NONE','pval':'p-value','pval_BH':'p-value with BH correction'}, inline=True, id='radio_pval')])
    return radio

def make_radiobutton_topN():
    radio=html.Div([html.Label("Select X-Axis Windowing: ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),dcc.RadioItems({'None':'All without Sorting','All':'All with Sorting',10:'TOP 10',20:'TOP 20'}, inline=True,id='radio_TopN')])
    return radio

def make_hemisphere_selector():
    hemisphere=html.Div([html.Label("Select Hemisphere to Include: ", style={'color':'#00539B', 'font-size':18,'font-family':'Arial'}),dcc.RadioItems({'B':'Bilateral','L':'Left','R':'Right'}, inline=True,id='hemisphere')])
    return hemisphere

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

def make_chart(plot_data):
    set_symbol_sequence=['circle']
    if persistentData.Plot_Configurations["myConfig"].use_sheet == 'stats':
        chart = dcc.Graph(id ='output-graph', figure=px.scatter(plot_data,x=persistentData.Plot_Configurations["myConfig"].x, y=persistentData.Plot_Configurations["myConfig"].y,symbol=persistentData.Plot_Configurations["myConfig"].x,symbol_sequence=set_symbol_sequence),style={'width': '50vw', 'height': '50vh'},config={"toImageButtonOptions":{"filename":persistentData.Plot_Configurations["myConfig"].x+"_vs_"+persistentData.Plot_Configurations["myConfig"].y, "format":'svg'}})
    else:
        chart = dcc.Graph(id ='output-graph', figure=px.scatter(plot_data,x=persistentData.Plot_Configurations["myConfig"].x, y='value',color='variable',symbol='variable',symbol_sequence=set_symbol_sequence,labels={"value": persistentData.Plot_Configurations["myConfig"].y})
                          ,style={'width': '50vw', 'height': '50vh'},config={"toImageButtonOptions":{"filename":persistentData.Plot_Configurations["myConfig"].x+"_vs_"+persistentData.Plot_Configurations["myConfig"].y, "format":'svg'}})
    return chart


## FIGURE CONFIG INPUT BUILDER -- HELPER FUNCTIONS
# These put together all the components into top/bottom divs for visualization


def top_config_input():
    radioPval=make_radiobutton_pvalue() #DCC
    radioTopN=make_radiobutton_topN() #DCC

    slider_contrast=make_slider(persistentData.Group_Stats.contrast_options,'contrast_slider',"Contrast Options For Significance Filtering: ") #DCC
    slider_sov=make_slider(persistentData.Group_Stats.sov_options,'sov_slider',"Source of Variation Options For Significance Filtering: ") #DCC

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
                    html.Div(className='chart-item', children=[html.Div(children=slider_contrast)],style={'display':'grid','width': '100%'}),
                    html.Div(className='chart-item', children=[html.Div(children=slider_sov)],style={'display':'grid','width': '100%'}),
                    html.Div(className='chart-item', children=[html.Div(children=radioTopN)],style={'display':'grid','width': '100%'}),]

    fig_layout=html.Div(className='chart-item', children=config_layout_top,id='config_top')
    return fig_layout

def bottom_config_input():
    plot_the_fig=make_go_button() #DCC
    radioTopN=make_radiobutton_topN() #DCC

    if persistentData.Plot_Configurations["myConfig"].use_sheet == 'stats':
        config_layout_bottom = [html.Div(className='chart-item', children=[html.Div(children=plot_the_fig)],style={'display':'grid','width': '100%'})]
    else:
        add_row=make_add_button()#DCC
        if persistentData.Plot_Configurations["myConfig"].use_sheet == 'indiv':
            groups_to_include_options = persistentData.Indiv_Data.groupings

            group_datatable=make_grouping_selector(groups_to_include_options)#DCC
            hemisphere = make_hemisphere_selector()#DCC

            config_layout_bottom= [
                html.Div(className='chart-item', children=[html.Div(children=hemisphere)],style={'display':'grid','width': '100%'}),
                html.Div(className='chart-item', children=[html.Div(children=group_datatable)],style={'display':'grid','width': '100%'}),
                html.Div(className='chart-item', children=[html.Div(children=add_row)],style={'display':'grid','width': '100%'}),
                html.Div(className='chart-item', children=[html.Div(children=plot_the_fig)],style={'display':'grid','width': '100%'})]

        elif persistentData.Plot_Configurations["myConfig"].use_sheet == 'group':
            groups_to_include_options = persistentData.Group_Data.groupings
            group_datatable=make_grouping_selector(groups_to_include_options)#DCC

            config_layout_bottom= [
                html.Div(className='chart-item', children=[html.Div(children=group_datatable)],style={'display':'grid','width': '100%'}),
                html.Div(className='chart-item', children=[html.Div(children=add_row)],style={'display':'grid','width': '100%'}),
                html.Div(className='chart-item', children=[html.Div(children=plot_the_fig)],style={'display':'grid','width': '100%'})]

    fig_layout=html.Div(className='chart-item', children=config_layout_bottom,id='config_bottom')
    return fig_layout

def full_figure_config_input():
    top_layout=top_config_input()
    bottom_layout=bottom_config_input()
    return [html.Div(className='chart-item', children=top_layout),html.Div(className='chart-item', children=bottom_layout)]
