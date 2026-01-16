# In[ ]:
from dash import Dash, dcc, html, dash_table,Input, Output, callback,ctx
import pandas as pd
import time
import os
from helper_functions import *
from classes import *
import persistentData
import json


## OBTAINING DATA CALLBACKS


@callback(Output("loading-stat_sheet", "children"),
          Input(component_id='group_stats_path',component_property='value'))
def update_input_stats (path):
    if path is not None and os.path.exists(path):
        time.sleep(1)
        persistentData.Group_Stats = load_stats(path)
    return

@callback(Output("loading-group_data", "children"),
          Input(component_id='group_data_path',component_property='value'))
def update_input_group_data (path):
    if path is not None and os.path.exists(path):
        time.sleep(1)
        persistentData.Group_Data = load_data(path,mode='group')
    return

@callback(Output("loading-indiv_data", "children"),
          Input(component_id='indiv_data_path',component_property='value'))
def update_input_indiv_data (path):
    if path is not None and os.path.exists(path):
        time.sleep(1)
        persistentData.Indiv_Data = load_data(path,mode='indiv')
    return


## ASSIGNING MANUAL VERSUS PROMPT INPUT


@callback(Output(component_id='prompt-container',component_property='children'),
          Output(component_id='prompt-knobs-container', component_property='children', allow_duplicate=True),
          Output(component_id='output-container', component_property='children', allow_duplicate=True),
          Input(component_id='select-mode',component_property='value'),prevent_initial_call=True)
def make_manual_versus_prompt_input(input_mode):
    if input_mode=='Manual':
        table_type_dropdown=dcc.Dropdown(options={'stats':'Group Statistical Results','group':'Group Data Table','indiv': 'Subject Data Table'}, placeholder='Select Main Table for Visualization', id='main_plot_table')
        return table_type_dropdown,[],[]
    elif input_mode =='Prompt':
        prompt_input=dcc.Textarea(value=None,placeholder='Input Prompt for Figure Generation, such as "Show me the Top 10 significant FA regions for Age_Class"',id='prompt_input',style={'width': '100%'})
        
        return prompt_input,[],[]
    else:
        return None,[],[]
    
    
 ## CREATE THE WHOLE OF LOADING WITH THE TOP/BOTTOM COMPONENTS


@callback(Output(component_id='prompt-knobs-container', component_property='children', allow_duplicate=True),
          Input(component_id='main_plot_table',component_property='value'),
          prevent_initial_call=True)
def set_figure_to_output_Manual(select_table_4_plotting):
    persistentData.Plot_Configurations["myConfig"].use_sheet=select_table_4_plotting
    if persistentData.Plot_Configurations["myConfig"].use_sheet is not None  and isinstance(persistentData.Indiv_Data, DataStructure) and isinstance(persistentData.Group_Data, DataStructure) and isinstance(persistentData.Group_Stats, StatsStructure):
        return full_figure_config_input()
    elif persistentData.Plot_Configurations["myConfig"].use_sheet is None  and isinstance(persistentData.Indiv_Data, DataStructure) and isinstance(persistentData.Group_Data, DataStructure) and isinstance(persistentData.Group_Stats, StatsStructure):
        message= 'Make sure to --  "Select Main Table for Visualization"'
        return [html.Div(className='chart-item', children=[html.Div(children=dcc.Input(id="Error_on_loading_Manual", value=message,style={'width': '100%'}))])]
    else:
        message= 'Make Sure All Data Files Are Loaded and Exist At Path Location'
        return [html.Div(className='chart-item', children=[html.Div(children=dcc.Input(id="Error_on_loading_Manual", value=message,style={'width': '100%'}))])]
     
@callback(Output(component_id='output-container', component_property='children', allow_duplicate=True),
          Input(component_id='prompt_input', component_property='value'),prevent_initial_call=True)
def set_figure_to_output_Prompt(prompt_text):
    message= 'Make Sure All Data Files Are Loaded and Exist At Path Location'

    #parse the group text pulling out key aspects of the request
    #push that to the configuration generation
    #apply that to the figure
    #push that to the output container
    if isinstance(persistentData.Indiv_Data, DataStructure) and isinstance(persistentData.Group_Data, DataStructure) and isinstance(persistentData.Group_Stats, StatsStructure):
        return None
    else:
        return [html.Div(className='chart-item', children=[html.Div(children=dcc.Input(id="Error_on_loading_Prompt", value=message))])]
    return None


## GETTERS FOR HTML COMPONENTS IN CONFIG SETTING

@callback(Input(component_id='radio_pval', component_property='value'))
def get_radiobutton_pvalue(radio_pval):
    removed_value = persistentData.Plot_Configurations["myConfig"].filter.pop('pval',None)
    removed_value = persistentData.Plot_Configurations["myConfig"].filter.pop('pval_BH',None)
    if radio_pval=='NONE':
        set_pval='pval'
        set_pval_value=None
    else:
        set_pval=radio_pval
        set_pval_value=0.05
        
    new_items={set_pval:set_pval_value}
    persistentData.Plot_Configurations["myConfig"].filter.update(new_items)
    return 

@callback(Input(component_id='radio_TopN', component_property='value'))
def get_radiobutton_topN(radio_TopN):
    new_items={'top_amount':radio_TopN}
    persistentData.Plot_Configurations["myConfig"].reduce_reorder.update(new_items)
    return

@callback(Input(component_id='x', component_property='value'))
def get_x(x_value):
    persistentData.Plot_Configurations["myConfig"].x=x_value
    return

@callback(Input(component_id='y', component_property='value'))
def get_y(y_value):
    persistentData.Plot_Configurations["myConfig"].y=y_value
    new_items={'sort_on':y_value}
    persistentData.Plot_Configurations["myConfig"].reduce_reorder.update(new_items)
    return

@callback(Input(component_id='contrast_slider', component_property='value'))
def get_contrast_slider(contrast_value):
    persistentData.Plot_Configurations["myConfig"].filter['contrast']=contrast_value
    return

@callback(Input(component_id='sov_slider', component_property='value'))
def get_sov_slider(sov_value):
    persistentData.Plot_Configurations["myConfig"].filter['source_of_variation']=sov_value
    return

@callback(Input(component_id='hemisphere', component_property='value'))
def get_hemisphere(hemisphere_value):
    persistentData.Plot_Configurations["myConfig"].reduce_reorder.pop('hemisphere',None)
    persistentData.Plot_Configurations["myConfig"].reduce_reorder['hemisphere']=hemisphere_value
    return

@callback(Input('group_selection_table', 'data'),
          Input('group_selection_table', 'columns'))
def get_desired_grouping(rows, columns):
    persistentData.Plot_Configurations["myConfig"].groups_to_include=rows
    return
    
@callback(
    Output('group_selection_table', 'data'),
    Input('add-rows-button', 'n_clicks'),
    State('group_selection_table', 'data'),
    State('group_selection_table', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '-' for c in columns})
    return rows


## OUTPUT TO CSV FILE SETUP


@callback(
    Output("download_data", "data"),
    Input("csv-button", "n_clicks"),
    prevent_initial_call=True
)
def export_data_as_csv(n_clicks):
    if n_clicks >0:
        
        if persistentData.Plot_Configurations["myConfig"].use_sheet == 'stats':
            persistentData.Plot_Configurations['myConfig'].data_path=persistentData.Group_Stats.path
        elif persistentData.Plot_Configurations["myConfig"].use_sheet == 'indiv':
            persistentData.Plot_Configurations['myConfig'].data_path=persistentData.Indiv_Data.path
        elif persistentData.Plot_Configurations["myConfig"].use_sheet == 'group':
            persistentData.Plot_Configurations['myConfig'].data_path=persistentData.Group_Data.path
        
        config_out=json.dumps(persistentData.Plot_Configurations["myConfig"].__dict__)
        data_out=persistentData.Plot_Configurations['Data'].to_csv()
        data_filename=persistentData.Plot_Configurations["myConfig"].x+"_vs_"+persistentData.Plot_Configurations["myConfig"].y+"_data_for_fig.csv"
        
        config_data_out = f"#{config_out}\n{data_out}"
        return dict(content=config_data_out, filename=data_filename)
    else:
        return None

## MAKE ACTUAL PLOT

@callback(Output(component_id='output-container',component_property='children', allow_duplicate=True),
          Input(component_id='go_button',component_property='n_clicks'),prevent_initial_call=True)
def make_graph(isgo): 
    if "go_button" == ctx.triggered_id and isgo>0:
        plot_data_out=use_config_on_Data()
        persistentData.Plot_Configurations['Data']=plot_data_out
        chart=make_chart(plot_data_out)
        
        download_button=html.Button("Download CSV", id="csv-button", n_clicks=0)  
        download_link=dcc.Download(id="download_data")
        download=html.Div([download_button,download_link])       
        
        return [chart,html.Div(className='chart-item', children=[html.Div(children=download)],style={'display':'grid','width': '100%'})]
    else:
        return None


