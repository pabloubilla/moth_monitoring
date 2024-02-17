### python -m bokeh serve --show main.py ###

# Import the required packages
import pandas as pd
from functools import lru_cache
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, PreText, Select, Div, CheckboxGroup, Slider, Range1d
from bokeh.plotting import figure, show

# import geopandas as gpd
import numpy as np
import os
import requests
import geopandas as gpd

# Let's first do some coloring magic that converts the color palet into map numbers (it's okey not to understand)
from bokeh.palettes import RdYlBu11 as palette
from bokeh.models import LogColorMapper, CategoricalColorMapper

from optimize_location import optimize_location



# Useful guide for the following code:
### https://automating-gis-processes.github.io/2016/Lesson5-interactive-map-bokeh.html ###

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
############################################

# # chcek types of 'geometry' column
# print(type(gdf['geometry']))
# # check if the 'geometry' column is a polygon
# print(gdf['geometry'].geom_type.unique())
# # show rows that are multipolygons
# print(gdf[gdf['geometry'].geom_type == 'MultiPolygon']) 
# # separate the multipolygons into single polygons
gdf = df_surrey.copy()
gdf = gdf.explode()  


# create widget to choose colormap
select = Select(title='Choose colormap:', value='viridis',
                options=['viridis', 'plasma', 'inferno', 'magma', 'cividis'])

def getPolyCoords(row, geom, coord_type):
    """Returns the coordinates ('x' or 'y') of edges of a Polygon exterior"""

    # Parse the exterior of the coordinate
    exterior = row[geom].exterior

    if coord_type == 'x':
        # Get the x coordinates of the exterior
        return list( exterior.coords.xy[0] )
    elif coord_type == 'y':
        # Get the y coordinates of the exterior
        return list( exterior.coords.xy[1] )
    
# Calculate x coordinates
gdf['x'] = gdf.apply(getPolyCoords, geom='geometry', coord_type='x', axis=1)
# Calculate y coordinates
gdf['y'] = gdf.apply(getPolyCoords, geom='geometry', coord_type='y', axis=1)
# make a copy of the gdf for the plot
gdf_plot = gdf.copy()
# just keep x, y and SWT_Summar
gdf_plot = gdf_plot[['x', 'y', 'SWT_Summar']]

unique_habitats = gdf['SWT_Summar'].unique()
colors = ['olive', 'peachpuff', 'goldenrod', 'darkblue']
color_mapper = CategoricalColorMapper(factors=unique_habitats, palette=colors)

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
# calculate x coordinates with get PolyCoords
df_circles['x'] = df_circles.apply(getPolyCoords, geom='geometry', coord_type='x', axis=1)
# calculate y coordinates with get PolyCoords
df_circles['y'] = df_circles.apply(getPolyCoords, geom='geometry', coord_type='y', axis=1)



# create df_areas with each unique habitat type
df_areas = pd.DataFrame({'Habitat Type': unique_habitats, 'Area covered (m2)': [0]*len(unique_habitats)})

# Generate labels for each point in the coordinate list
point_labels = [f"Point {i}" for i, _ in enumerate(coordinate_list)]

# Create a CheckboxGroup widget with these labels
checkbox_group = CheckboxGroup(labels=point_labels, active=list(range(len(coordinate_list))))
# Create a selection for K number of points
select_K = Select(title='Select number of monitors (K):', value='4', options=[str(i) for i in range(1,10)])
# create slider to select R
slider_R = Slider(start=10, end=200, value=50, step=10, title="Select coverage radius (R)")
# create slider to select q
slider_q = Slider(start=0.1, end=0.4, value=0.2, step=0.05, title="Select Wet Heath priority (q)")

# source for the points
psource = ColumnDataSource(data = df_xy)

# Create a ColumnDataSource for grid: it's needed for updating plot data
source = ColumnDataSource(data=gdf_plot)

# habitat source
hsource = ColumnDataSource(data = df_areas)

# create source for circles
csource = ColumnDataSource(data = df_circles)

# Create a function to update the plot
def update():
    # Filter the coordinate list based on the active checkboxes
    # selected_points = [coordinate_list[i] for i in checkbox_group.active]
    
    selected_index, df_areas_new = optimize_location(df_surrey, df_xy, K = int(select_K.value),
                                       R = int(slider_R.value), q = slider_q.value)
    # get selected points from coordinate list
    x_selected = [coordinate_list[i][0] for i in selected_index]
    y_selected = [coordinate_list[i][1] for i in selected_index]

    # Update the data source for the points
    psource.data = {'x': x_selected, 
                    'y': y_selected,
                    'size': [int(slider_R.value)/5] * len(selected_index)}
    
    # Update the source for habitats
    hsource.data = {'Habitat Type': df_areas_new['Habitat Type'],
                    'Area covered (m2)': df_areas_new['Area covered (m2)']}
    
    # Update the source for the circles
    if len(selected_index) > 0:
        df_circles_new = df_xy.iloc[selected_index].copy()
        df_circles_new['geometry'] = df_circles_new.buffer(int(slider_R.value))
        df_circles_new['x'] = df_circles_new.apply(getPolyCoords, geom='geometry', coord_type='x', axis=1)
        df_circles_new['y'] = df_circles_new.apply(getPolyCoords, geom='geometry', coord_type='y', axis=1)
        csource.data = {'x': df_circles_new['x'],
                        'y': df_circles_new['y']}
    else:
        csource.data = {'x': [], 'y': []}

checkbox_group.on_change('active', lambda attr, old, new: update())
select_K.on_change('value', lambda attr, old, new: update())
slider_R.on_change('value', lambda attr, old, new: update())
slider_q.on_change('value', lambda attr, old, new: update())

# # Call the update function once initially to reflect the default selection
# update()



# Create a figure
p = figure(x_axis_label='Longitude', y_axis_label='Latitude', title = 'Location of monitors in Pirbright Range',
           height=910, width=710)

# Plot grid
p.patches('x', 'y', source=source,
         fill_color={'field': 'SWT_Summar', 'transform': color_mapper},
         fill_alpha=1.0, line_color="black", line_width=0.05, legend_field='SWT_Summar')

# add points
# p.circle('x', 'y', size='size', source=psource, color="deeppink")

# add circles on top of the same figure 
p.patches('x', 'y', source=csource, fill_alpha=0.8, line_alpha=1, line_color="red",
          line_width=2, fill_color="deeppink")



# see max area value
# range_y = Range1d(start=1, end=200000)
# create a figure for the habitat areas
p2 = figure(x_range=unique_habitats, title="Area covered by habitat type",
           toolbar_location=None, tools="", x_axis_label='Habitat Type', y_axis_label='Area covered (m2)',
           height=700, width=450)
# slightly rotate xaxis
p2.xaxis.major_label_orientation = 0.5

p2.vbar(x='Habitat Type', top='Area covered (m2)', width=0.9, source=hsource,
        fill_color={'field': 'Habitat Type', 'transform': color_mapper})
# use quad instead
# p2.quad(top='Area covered (m2)', bottom=0, left='Habitat Type', right='Habitat Type', source=hsource)


# define layout
# sliders on top and p and p2 below
layout = column(select_K, slider_R, slider_q, row(p, p2))

# put p in first column and p2, sliders in second column
layout = row(p, column(select_K, slider_R, slider_q, p2))

update()

# curdoc().theme = 'contrast' # if you want to change the theme
curdoc().add_root(layout)
show(layout)

# Save the figure
# outfp = r"/home/geo/data/travel_time_map.html"
# save(p, outfp)