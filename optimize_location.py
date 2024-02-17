import numpy as np
import pandas as pd
import geopandas as gpd
import cvxpy as cp

#### OPTIMIZATION PROBLEM ####


def optimize_location(df_map, df_points, K = 4, R = 50, q = 0.25):

    print('OPTIMIZING LOCATION')

    # # get dataframes
    # df_map = df_surrey.copy()
    # df_points = df_surrey2.copy()
    # create a copy of the points
    df_circles = df_points.copy()
    # df_circles = gpd.GeoDataFrame(df_points, geometry=gpd.points_from_xy(df_points.x, df_points.y))
    # create geopa

    # Parameters
    M = len(df_map['SWT_Summar'].unique())  # number of unique areas
    N = len(df_points)  # number of points
    # K = 4  # number of monitors you can select
    # R = 50  # radius of the monitor

    # buffer to radius of 50 meters
    df_circles['geometry'] = df_circles.buffer(R)

    # select point in df_circles (N)
    x = cp.Variable(N, boolean=True)
    # variable for total area of each type
    z = cp.Variable(M, nonneg=True)
    # variable for minimum area
    y = cp.Variable(1, nonneg=True)


    # area of first polygon (parameter)
    circle_area = df_circles['geometry'].iloc[0].area

    # constraint list
    constraints = []


    # area types
    area_types = np.sort(df_map['SWT_Summar'].unique())
    # index of 'Wet Heathland' in area_types
    wet_heathland_index = np.where(area_types == 'Wet Heath/Grassland')[0][0]
    # print('Wet Heathland index:', wet_heathland_index)

    # areas list (NxM)
    areas = np.zeros((N, M))
    for ix in range(N):
        # INTERSECT with df_map
        intersection = df_circles.iloc[ix]['geometry'].intersection(df_map['geometry'])
        # compute area by catogires of SWT_Summar
        df_map[f'Intersect {ix}'] = intersection.area
        areas[ix, :] = df_map.groupby('SWT_Summar').sum(f'Intersect {ix}')[f'Intersect {ix}']
        # print(df_map.groupby('SWT_Summar').sum(f'Intersect {ix}')[f'Intersect {ix}'])

    # can only select K points
    constraints.append(cp.sum(x) == K)

    # z is less than the sum of the areas
    for j in range(M):
        constraints.append(z[j] == cp.sum(cp.multiply(x,areas[:, j])))

        # y is less than each area
        constraints.append(y <= z[j])

    # wet heathland is at least q of the total area
    constraints.append(cp.multiply(q, cp.sum(z)) <= z[wet_heathland_index])

    # maximize sum of log
    objective = cp.Maximize(y)

    # create the problem
    prob = cp.Problem(objective, constraints)

    # solve
    try:
        prob.solve()

        # show how much of each area type is covered
        # print('Area types')
        # print(area_types)
        # print('Area covered')
        # print(z.value)
        df_areas = pd.DataFrame(np.round(z.value, 2), index=area_types, columns=['Area covered (m2)'])
        # add index title
        df_areas.index.name = 'Habitat Type'
        # pass to column and reset
        df_areas.reset_index(inplace=True)
        # display(df_areas)

        # print('Minimum area cov   ered')
        # print(y.value)

        # return args where x is 1
        selected_index = np.where(x.value == 1)[0]
        return selected_index, df_areas

    except:
        print('No solution found')
        return [], pd.DataFrame({'Habitat Type': area_types, 'Area covered (m2)': [0]*len(area_types)})


    # print the solution
    # print('X values')
    # print(x.value)



    # sum z
# print(np.sum(z.value))
