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

from pyproj import Proj

#wgs84 = Proj("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
utm13n = Proj("+proj=utm +zone=13 +ellps=GRS80 +datum=NAD83 +units=m +no_defs ")

folder_path = "data/"

files = glob.glob(os.path.abspath(os.path.join(folder_path, 'AgisoftErrors*')))

data_frame_list = []

for f in files:
    
    # read in table
    data_frame = pd.read_csv(f, skiprows=[0])#, skipfooter=1)
    data_frame.rename(columns={'#Label':'GCP'}, inplace=True)
    
    # add information about the file
    filename = os.path.basename(f)
    set_name = filename.split('.')[1]
    data_frame['Set'] = set_name
    point_name = filename.split('.')[2]
    data_frame['Point'] = point_name
    area_name = filename.split('.')[3]
    data_frame['Area'] = area_name
    
    data_frame.replace({'Area':{'Overall': 'Entire Basin'}}, inplace=True)
    
    # add to the data_frame_list
    data_frame_list.append(data_frame[data_frame.GCP != '#Total error'])
    
# concatenate all data frames together
df = pd.concat(data_frame_list).reset_index(drop=True)

# create UTM coordinates
easting, northing = utm13n(df['X/Longitude'].values, df['Y/Latitude'].values)
df['Easting'] = easting
df['Northing'] = northing

# create a squared residual value
df['Squared_Residual'] = df['Error_(m)']**2

# create a control/check value
df['Control_or_Check'] = df['Enable'] 
df.replace({"Control_or_Check": {0: 'Check Point', 1: 'Control Point'}}, inplace=True)

# group by Enabled (0 = Check point vs 1 = Control Point) and Set
rmse = np.sqrt(df.filter(['Set', "Area", 'Control_or_Check', 'Squared_Residual']).groupby(by=['Set', 'Area', 'Control_or_Check']).mean())
rmse.rename(columns={'Squared_Residual':'RMSE'}, inplace=True)
number_of_control_points = df.filter(['Set', 'Enable']).groupby(by=['Set']).sum()
number_of_control_points.rename(columns={"Enable": "Number_of_Control_Points"}, inplace=True)
    
# merge rmse together and remove multiindex
summary_table = rmse.join(number_of_control_points, how = 'left')
summary_table.reset_index(inplace=True)


#%%
# make a plot!
filtered_summary_table=summary_table.loc[summary_table['Control_or_Check'] == 'Check Point']
p = (ggplot(filtered_summary_table, aes(x='Number_of_Control_Points', 
                               y='RMSE', 
                               color='Area')) 
    + geom_point(size=3)
    + ylim(0, None)
    + scale_x_continuous(limits=(0, 9), breaks=[0, 3, 6, 9])
    + ggtitle("Model Accuracy in Meters by Area as Number of GCPs Increases")
    + xlab("Number of Ground Control Points Used")
    + ylab("Root Mean Squared Error (m)")
    + theme_bw(base_size=14))
    
p.draw()
# export as jpeg
p.save(filename='NumberofGCPs-RMSE.jpg', dpi=300)
#%%

#%%
# make a plot!
p = (ggplot(df, aes(x='GCP', 
                    y='Projections')) 
    + geom_point() 
    + ylim(0, None)
    + ggtitle("Number of Times GCPs Were Marked in Agisoft")
    + xlab("Ground Control Point")
    + ylab("Number of Projections")
    + theme_bw(base_size=14))
    
p.draw()
# export as jpeg
p.save(filename='GCP-Projections.jpg', dpi=300)
#%%

# make a plot!
p = (ggplot(df, aes(x='Projections',
                    y='Error_(m)',
                    color='Point',
                    shape='Control_or_Check'))
    + geom_jitter(width = 0, height = 0.09)
    + xlim(0, None)
    + ylim(0, None)
    + theme_bw(base_size=18))
    
p.draw()
# export as jpeg
p.save(filename='Projections-Error(m).jpg')

# make a plot!
p = (ggplot(df, aes(x='Projections',
                    y='Error_(m)',
                    color='GCP',
                    shape='Control_or_Check'))
    + geom_jitter(width = 0, height = 0.09)
    + xlim(0, None)
    + ylim(0, None)
    + facet_wrap("~Point", nrow=5)
    + theme_bw(base_size=18))
    
p.draw()
# export as jpeg
p.save(filename='Projections-Error(m)2.jpg')

#%%
# make a plot!
p = (ggplot(df, aes(x='Point',
                    y='Error_(m)',
                    color='Area',
                    shape='Control_or_Check'))
    + geom_point()
    + ylim(0, None)
    + ggtitle("Error (m) of Each Ground Control Point")
    + xlab("Number of Ground Control Points Used")
    + ylab("Root Mean Squared Error (m)")
    + facet_wrap("~GCP", nrow=4)
    + theme_bw(base_size=14))

p.draw()
# export as jpeg
p.save(filename='Point-Error(m).jpg', dpi=300)
#%%

#%%
# make a plot!
p = (ggplot(df, aes(x='Easting',
                    y='Northing',
                    color='Control_or_Check'))
    + geom_point()
    + scale_color_brewer(type='qual',palette=3)
    + ggtitle("Distribution of Control Points and Check Points")
    + xlab("Area of Focus for Control Points in Basin")
    + ylab("Number of GCPs Used")
    + facet_grid("Point~Area")
    + scale_x_continuous(breaks=[], labels=[])
    + scale_y_continuous(breaks=[], labels=[])
    + theme_bw(base_size=14))
    
p.draw()
# export as jpeg
p.save(filename='Easting-Northing.jpg', dpi=300)
#%%

# re order columns
df = df.reindex(columns=['Set', 'Point', 'Area','GCP','Projections', 'Control_or_Check', 'Error_(m)', 'Squared_Residual', 
                 'Enable', 'X/Longitude', 'Y/Latitude', 'Z/Altitude', 'Easting', 'Northing',
                     'X_error', 'Y_error', 'Z_error', 'X_est', 'Y_est', 'Z_est'])
# sort the table, first by Point, then by Area. then by Enable
df.sort_values(by=['Point', 'Area', 'Enable'], inplace=True)

# export as csv
df.to_csv(path_or_buf="GCP_Plot.csv")


