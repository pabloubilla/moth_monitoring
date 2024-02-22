import numpy as np
import os
import requests
import geopandas as gpd
import pandas as pd


# plot site and monitor locations
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.colors as mcolors

# read data\Pirbright_whole_NVC_2001-2.shp
df_surrey = gpd.read_file(os.path.join('data', 'Pirbright_whole_NVC_2001-2.shp'))


#### PRE-PROCESSING #######################
# remove NoneType from geometry
df_surrey = df_surrey[df_surrey.geometry.notnull()]

# remove if SWT_Summar is Other
df_surrey = df_surrey[df_surrey['SWT_Summar'] != 'Other']

# change 'Dry Heath Associated Communities' to 'Dry Heath'
df_surrey['SWT_Summar'] = df_surrey['SWT_Summar'].replace('Dry Heath Associated Communities', 'Dry Heath')

# change 'Dry Grassland' and 'Dry Heath' to 'Dry Heath/Grassland'
df_surrey['SWT_Summar'] = df_surrey['SWT_Summar'].replace('Dry Grassland', 'Dry Heath/Grassland')
df_surrey['SWT_Summar'] = df_surrey['SWT_Summar'].replace('Dry Heath', 'Dry Heath/Grassland')
# df_surrey['SWT_Summar'] = df_surrey['SWT_Summar'].replace('Dry Grassland', 'Dry Heath')

# change 'Wet Grassland' and 'Wet Heath' to 'Wet Heath/Grassland'
df_surrey['SWT_Summar'] = df_surrey['SWT_Summar'].replace('Wet Grassland', 'Wet Heath/Grassland')
df_surrey['SWT_Summar'] = df_surrey['SWT_Summar'].replace('Wet Heath', 'Wet Heath/Grassland')



# list of feasible points according to the Trust
coordinate_list = [ [491500, 160500],
                    [492200, 160600],
                    [492900, 160900],
                    [493400, 161160],
                    [491500, 159300],
                    [491700, 158900],
                    [492500, 158800],
                    [492000, 158000],
                    [493800, 158500],
                    [493000, 160000],
]

# get max and min x and y 
x_min = df_surrey.bounds.minx.min()
x_max = df_surrey.bounds.maxx.max()
y_min = df_surrey.bounds.miny.min()
y_max = df_surrey.bounds.maxy.max()

# create uniform square grid
x_range = np.linspace(x_min, x_max, 25)
y_range = np.linspace(y_min, y_max, 25)
x_grid = []
y_grid = []
for x in x_range:
    for y in y_range:
        x_grid.append(x)
        y_grid.append(y)
# create dataframe with the grid
df_grid = pd.DataFrame({'x': x_grid, 'y': y_grid})
# geopandas
df_grid = gpd.GeoDataFrame(df_grid, geometry=gpd.points_from_xy(df_grid['x'], df_grid['y']))
# keep points inside df_surrey
df_grid = gpd.sjoin(df_grid, df_surrey, how='inner', op='within')



# # create a dataframe with the random points
# df_xy = pd.DataFrame({'x': x, 'y': y})
# create a dataframe with the coordinate list
df_xy = pd.DataFrame(coordinate_list, columns=['x', 'y'])
# geopandas
df_xy = gpd.GeoDataFrame(df_xy, geometry=gpd.points_from_xy(df_xy['x'], df_xy['y']))
# add a size column
df_xy['size'] = 10
# df_circles, buffered
df_circles = df_xy.copy()
df_circles['geometry'] = df_circles.buffer(50)




# when there's only 4 colors
colors = ['peachpuff', 'goldenrod', 'darkblue', 'olive']
custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", colors)


# plot the site
ax1 = df_surrey.plot(column = 'SWT_Summar', cmap = custom_cmap, 
                     legend = True, figsize = (8, 14))
df_xy.plot(ax = ax1, color='red', alpha=1, marker = 'x', markersize=110,
           label = 'Candidate Location', legend = True, linewidth = 5)
# x and y axis as Latitude and Longitude
ax1.set_xlabel('Latitude', fontsize=11)
ax1.set_ylabel('Longitude', fontsize=11)
# bigger fontsize
ax1.tick_params(axis='both', which='major')
# reduce margins
plt.tight_layout()
# save the plot
plt.savefig('images/site_and_monitor_locations.png')

# plot the site
ax2 = df_surrey.plot(column = 'SWT_Summar', cmap = custom_cmap, 
                     legend = True, figsize = (8, 14))
# plot the grid
df_grid.plot(ax = ax2, color='black', alpha=1,
             marker = 'x', markersize=80, linewidth = 3)
# x and y axis as Latitude and Longitude
ax2.set_xlabel('Latitude', fontsize=11)
ax2.set_ylabel('Longitude', fontsize=11)
# save the plot
plt.savefig('images/site_and_grid.png')


# just plot the site
df_surrey.plot(column = 'SWT_Summar', cmap = custom_cmap, 
                     legend = True, figsize = (8, 14))
# x and y axis as Latitude and Longitude
plt.xlabel('Latitude', fontsize=11)
plt.ylabel('Longitude', fontsize=11)
# save the plot
plt.savefig('images/site_only.png')

