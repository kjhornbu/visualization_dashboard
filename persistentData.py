"""
persistentData

Global-ish data to share across our dash-app.
Includes default paths.
I think these will end up being shared between multiple users at the same time, which may be a mistake.

"""
import os
from classes import *

# These variables are placeholders so that we remember we load tables and stuff them into these names. 
# this whole method of keeepin ghte same tables loaded is a hack. We dont know when this will be a problem.
Indiv_Data='We'
Group_Data='R'
Group_Stats='Testing'

# James presumes a dict will be a good choice for plot configurations, as we'll name each one as we add it.
Plot_Configurations={}

itab=''
gtab=''
rtab=''

default_files={"Subject": itab,
             "Group": gtab,
             "Result": rtab,
             }

Plot_Configurations["myConfig"]=PlotConfig()