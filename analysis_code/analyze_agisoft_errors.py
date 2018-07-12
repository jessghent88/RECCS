#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 10 07:52:24 2018

@author: barnhark
"""
import os
import glob
import numpy as np
import pandas as pd
from plotnine import *

folder_path = "/media/halibut/ExtraDrive11/DroneData/chalk_cliffs/2018-06-18/photoscan/exported_marker_errors"

files = glob.glob(os.path.abspath(os.path.join(folder_path, 'AgisoftErrors*')))

data_frame_list = []

for f in files:
    
    # read in table
    data_frame = pd.read_csv(f, skiprows=[0])
    
    # drop the last row, its incompleted
    data_frame.dropna(inplace=True)
    
    # add information about the file
    filename = os.path.basename(f)
    set_name = filename.split('.')[1]
    data_frame['Set'] = set_name
    point_name = filename.split('.')[2]
    data_frame['Point'] = point_name
    reason_name = filename.split('.')[3]
    data_frame['Reason'] = reason_name
    
    
    # add to the data_frame_list
    data_frame_list.append(data_frame)
    
# concatenate all data frames together
df = pd.concat(data_frame_list).reset_index(drop=True)

# create a squared residual value
df['Squared_Residual'] = df['Error_(m)']**2

# create a control/check value
df['Control_or_Check'] = df['Enable'] 
df.replace({"Control_or_Check": {0: 'Check Point', 1: 'Control Point'}}, inplace=True)

# group by Enabled (0 = Check point vs 1 = Control Point) and Set
rmse = np.sqrt(df.filter(['Set', 'Control_or_Check', 'Squared_Residual']).groupby(by=['Set', 'Control_or_Check']).mean())
rmse.rename(columns={'Squared_Residual':'RMSE'}, inplace=True)
number_of_control_points = df.filter(['Set', 'Enable']).groupby(by=['Set']).sum()
number_of_control_points.rename(columns={"Enable": "Number_of_Control_Points"}, inplace=True)
    
# merge rmse together and remove multiindex
summary_table = rmse.join(number_of_control_points, how = 'left')
summary_table.reset_index(inplace=True)


# make a plot!
p = (ggplot(summary_table, aes(x='Number_of_Control_Points', 
                               y='RMSE', 
                               color='Set')) 
    + geom_point() 
    + xlim(0, None)
    + ylim(0, None)
    + facet_wrap("~Control_or_Check", nrow=2) 
    + theme_bw())
    
print(p)