import osmnx as ox
import networkx as nx
import pandas as pd
import pickle
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import timezone
from datetime import datetime


def load_graph(path_g='graph'):
    G = ox.io.load_graphml(path_g)
    return G

G = load_graph()

def get_route(graph, start_latlng, end_latlng):
    # find shortest route based on the mode of travel
#     mode = 'drive' # 'drive', 'bike', 'walk'

    # find shortest path based on distance or time
    optimizer = 'length' # 'length','time'

    # find the nearest node to the start location
    orig_node = ox.nearest_nodes(graph, start_latlng[1], start_latlng[0])

    # find the nearest node to the end location
    dest_node = ox.nearest_nodes(graph, end_latlng[1], end_latlng[0])

    shortest_route = []
    # find the shortest path
    if nx.has_path(graph, orig_node,dest_node):
        shortest_route = nx.shortest_path(graph, orig_node,dest_node,
                                          weight=optimizer)
    # else:
    #     orig_node = ox.nearest_nodes(graph, G[orig_node]['lon'], G[orig_node]['lat'])
    #     dest_node = ox.nearest_nodes(graph, G[dest_node]['lon'], G[dest_node]['lat'])

    return shortest_route


def get_nodes_coords(route):
    """
    returns latitutdes and longitudes lists for all node of a route
    :param route:
    :return:
    """
    long = []
    lat = []
    for i in route:
        point = G.nodes[i]
        long.append(point['x'])
        lat.append(point['y'])
    return lat, long


def get_nodes_coords_taxicab(route):
    long = []
    lat = []
    for i in route:
        point = G.nodes[i]
        long.append(point['x'])
        lat.append(point['y'])
    return lat, long


def plot_path(fig, lat, long, origin_point, destination_point):
    """
    Given a list of latitudes and longitudes, origin
    and destination point, plots a path on a map

    Parameters
    ----------
    lat, long: list of latitudes and longitudes
    origin_point, destination_point: co-ordinates of origin
    and destination
    Returns
    -------
    Nothing. Only shows the map.
    """
    # adding the lines joining the nodes
    fig.add_trace(go.Scattermapbox(
        name="Path",
        mode="lines",
        lon=long,
        lat=lat,
        marker={'size': 10},
        line=dict(width=4.5)))
    # adding source marker
    fig.add_trace(go.Scattermapbox(
        name="Source",
        mode="markers",
        lon=[origin_point[1]],
        lat=[origin_point[0]],
        marker={'size': 10}))

    # adding destination marker
    fig.add_trace(go.Scattermapbox(
        name="Destination",
        mode="markers",
        lon=[destination_point[1]],
        lat=[destination_point[0]],
        marker={'size': 10}))

    # getting center for plots:
    lat_center = np.mean(lat)
    long_center = np.mean(long)

    return fig


def unixTimeMillis(dt):
    ''' Convert datetime to unix timestamp '''
#     return int(time.mktime(dt.timetuple()))
    return int(dt.replace(tzinfo=timezone.utc).timestamp())


def unixToDatetime(unix):
    ''' Convert unix timestamp to datetime. '''
    return pd.to_datetime(unix,unit='s')
#     return pd.to_datetime(unix)


def getMarks(date_range, Nth=1):
    ''' Returns the marks for labeling.
        Every Nth value will be used.
    '''
#     date_range = pd.date_range(start=start, end=end, freq='15min')
    result = {}
    for i, date in enumerate(date_range):
        if(i%Nth == 0):
            # Append value to dict
            result[unixTimeMillis(date)] = str(date.strftime('%H:%M'))

    return result

def save_graph_and_routes(G, routes, file_G='graph', file_routes='city_routes'):
    with open(f'{file_routes}', 'wb') as fp:
        pickle.dump(routes, fp)
    ox.io.save_graphml(G, f'{file_G}')


def load_routes(path_route='city_routes'):
    with open(f'{path_route}', 'rb') as fp:
        routes = pickle.load(fp)
    return routes