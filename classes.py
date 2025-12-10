# In[ ]:

import pandas as pd
import re


## these don't work with the multipage layout need to have dcc store used adn not rely on global setting

## ALL CLASS DEFINTIONS
class PlotConfig: 
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