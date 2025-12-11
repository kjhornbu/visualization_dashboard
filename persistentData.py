"""
persistentData

Global-ish data to share across our dash-app.
Includes default paths.
I think these will end up being shared between multiple users at the same time, which may be a mistake.

"""
import os


Indiv_Data='We'
Group_Data='R'
Group_Stats='Testing'

# James presumes a dict will be a good choice for plot configurations, as we'll name each one as we add it.
Plot_Configurations={}


# Kathryn defaults
itab1='/Volumes/dusom_civm-kjh60/All_Staff/18.gaj.42/Scalar_and_Volume/Main_Effects_2025_01_14_NoB6/Non_Erode/Subject_Data_Table.csv'
gtab1='/Volumes/dusom_civm-kjh60/All_Staff/18.gaj.42/Scalar_and_Volume/Main_Effects_2025_01_14_NoB6/Non_Erode/Bilateral/Group_Data_Table_Age_Class_Strain_Sex.csv'
rtab1='/Volumes/dusom_civm-kjh60/All_Staff/18.gaj.42/Scalar_and_Volume/Main_Effects_2025_01_14_NoB6/Non_Erode/Bilateral/Group_Statistical_Results_Age_Class_Strain_Sex.csv'

# James defaults
itab2='/home/james/mnt/dusom_civm_kjh60/All_Staff/18.gaj.42/Scalar_and_Volume/Main_Effects_2025_01_14_NoB6/Non_Erode/Subject_Data_Table.csv'
gtab2='/home/james/mnt/dusom_civm_kjh60/All_Staff/18.gaj.42/Scalar_and_Volume/Main_Effects_2025_01_14_NoB6/Non_Erode/Bilateral/Group_Data_Table_Age_Class_Strain_Sex.csv'
rtab2='/home/james/mnt/dusom_civm_kjh60/All_Staff/18.gaj.42/Scalar_and_Volume/Main_Effects_2025_01_14_NoB6/Non_Erode/Bilateral/Group_Statistical_Results_Age_Class_Strain_Sex.csv'

# Other friend derfaults?
# itab3=...
# gtab3=...
# rtab3=...

itab=itab1
gtab=gtab1
rtab=rtab1

if os.path.exists(itab2) and not os.path.exists(itab1):
    itab=itab2
if os.path.exists(gtab2) and not os.path.exists(gtab1):
    gtab=gtab2
if os.path.exists(rtab2) and not os.path.exists(rtab1):
    rtab=rtab2

default_files={"Subject": itab,
             "Group": gtab,
             "Result": rtab,
             }
