import pandas as pd
from dash import Dash, dcc, html, Input, Output
import os
from utils import *
from datetime import datetime
from datetime import timedelta
import plotly.graph_objects as go
import plotly.figure_factory as ff
import numpy as np


colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}


taxi_loc = pd.read_pickle('data/taxi_loc_dropdup_df')
taxi_loc['Taxi ID'] = taxi_loc['Taxi ID'].astype("string")




app = Dash(__name__)
app.layout = html.Div(
    className="app-header",
    children=[
    html.H1(
        'One day of a city',
        style={
            'textAlign': 'center',
            'color': colors['text'],
        }
    ),
    html.Label(
        'Date',
        style={"margin-top": "60px"}
    ),
    dcc.Dropdown(
        id='city_day',
        value=unixTimeMillis(datetime.strptime('2014-10-12', '%Y-%m-%d')),
        # options=[{'label':date.date() ,'value':unixTimeMillis(date)} for date in pd.date_range(taxi_loc['Trip Start Timestamp'].dt.date.min(),
        #                                                         taxi_loc['Trip Start Timestamp'].dt.date.max(),
        #                                                      freq='D')],
        options=[{'label': pd.DatetimeIndex([date])[0], 'value': unixTimeMillis(unixToDatetimeNs(date))} for date in list(taxi_loc['Trip Start Timestamp'].sort_values().dt.normalize().unique())]
    ),
    html.Label(
        'Taxi ID',
        style={"margin-top": "30px"}
    ),
    dcc.Dropdown(
        id='taxiID',
        value=list(taxi_loc['Taxi ID'].unique())[0:1],
        options=list(taxi_loc['Taxi ID'].unique())[:20],
        multi=True
    ),
    html.Label(
        'Time',
        style={"margin-top": "30px"}
    ),
    dcc.Slider(
        id='time_start',
        min=unixTimeMillis(datetime.strptime('2014-10-12', '%Y-%m-%d')),
        max=unixTimeMillis(datetime.strptime('2014-10-12', '%Y-%m-%d')),
        marks={},
        value=unixTimeMillis(datetime.strptime('2014-10-12', '%Y-%m-%d')),
    ),
    dcc.Graph(id="graph"),
    ],
    style={
    # 'background-color': colors['background']
    }
)

@app.callback(
    [
        Output("time_start", 'min'),
        Output("time_start", 'max'),
        Output("time_start", 'marks'),
        Output("time_start",  'value'),
        Output("taxiID", 'options'),
        Output("taxiID", 'value')
    ],


    [Input("city_day", "value")])
def set_date(date):
    print(date)
    print(unixToDatetime(date))
    min_date = date
    max_date = unixTimeMillis(unixToDatetime(min_date) + timedelta(days=1))
    value = date
    daterange = pd.date_range(unixToDatetime(min_date), unixToDatetime(max_date), freq='15min')
    # print(daterange)
    marks = getMarks(daterange, 4)

    taxi_ids = list(taxi_loc[taxi_loc['Trip Start Timestamp'].dt.date == datetime.utcfromtimestamp(date).date()][
                        'Taxi ID'].unique())
    print(taxi_ids)
    if len(taxi_ids) == 0:
        taxi_ids = list(taxi_loc['Taxi ID'].unique())[0:1]

    return min_date, max_date, marks, value, taxi_ids, taxi_ids[0:1]

@app.callback(
    Output("graph", "figure"),
    [
        Input('taxiID', 'value'),
        Input("time_start", "value"),
     ])
def update_line_chart(taxiID, time_start):
    taxi_trips = taxi_loc[taxi_loc['Taxi ID'].isin(taxiID)]
    taxi_trips = taxi_trips[(taxi_trips['Trip Start Timestamp'].apply(unixTimeMillis) <= time_start)
                           & (taxi_trips['Trip End Timestamp'].apply(unixTimeMillis) >= time_start)]
    # print(taxi_trips)

    # taxi_trips = taxi_trips.groupby(['Trip Start Timestamp',
    #                               'Trip End Timestamp',
    #                               'Pickup Centroid Latitude',
    #                               'Pickup Centroid Longitude',
    #                               'Dropoff Centroid Latitude',
    #                               'Dropoff Centroid Longitude'], as_index=False)['Fare'].sum()
    # taxi_trips = taxi_trips.groupby('Trip Start Timestamp', as_index=False).agg({
    #     'Trip End Timestamp': 'max',
    #     'Pickup Centroid Latitude': 'min',
    #     'Pickup Centroid Longitude': 'min',
    #     'Dropoff Centroid Latitude': 'max',
    #     'Dropoff Centroid Longitude': 'max',
    #     'Fare': 'sum'
    # })
    # print(taxi_trips)

    fig = go.Figure(go.Scattermapbox())
    fig.update_layout(mapbox_style="stamen-terrain",
                      )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                      mapbox={
                          'center': {'lat': 41.87,
                                     'lon': -87.6},
                          'zoom': 11})
    try:
        # print('here')
        taxi_routes = [get_route(G, (r['Pickup Centroid Latitude'], r['Pickup Centroid Longitude']),
                                 (r['Dropoff Centroid Latitude'], r['Dropoff Centroid Longitude'])) for _, r in taxi_trips.iterrows()]
        # print(taxi_routes)
        taxi_trips.reset_index(inplace=True)
        taxi_trips['route'] = pd.Series(taxi_routes)

        # print(taxi_trips)
        taxi_trips['lat'], taxi_trips['long'] = zip(*taxi_trips['route'].map(get_nodes_coords))
        # print(taxi_trips)

        for _, r in taxi_trips.iterrows():
            lat, long = r['lat'], r['long']
            plot_path(fig, lat,
                      long,
                      (r['Pickup Centroid Latitude'], r['Pickup Centroid Longitude']),
                      (r['Dropoff Centroid Latitude'], r['Dropoff Centroid Longitude']))
            # print('path plotted')
    except Exception:
        pass
    fig.add_annotation(
        text=f"Time: {unixToDatetime(time_start)}",
        showarrow=False,
        ax=10,
        ay=-40,
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=4,
        bgcolor="#ff7f0e",
        opacity=0.8,
        font=dict(
            family="Courier New, monospace",
            size=16,
            color="#ffffff"
        ),
        align="center",
    )
    return fig


app.run_server(port=8050, debug=True)


# app = Dash(__name__)
# app.layout = html.Div([
#     dcc.Dropdown(['NYC', 'MTL', 'SF'], 'NYC', id='demo-dropdown'),
#     html.Div(id='dd-output-container'),
#
#     html.H4('One day of a driver'),
#     html.Label(
#         'Date',
#         style={"margin-top": "30px"}
#     ),
#     dcc.Dropdown(
#         id='city_day',
#         value=unixTimeMillis(datetime.strptime('2016-05-31', '%Y-%m-%d')),
#         options=[{'label': date.date(),
#                   'value': unixTimeMillis(date)} for date in pd.date_range(taxi_loc['Trip Start Timestamp'].dt.date.min(),
#                                                                                              taxi_loc['Trip Start Timestamp'].dt.date.max(),
#                                                                                              freq='D')]
#     ),
#     html.Label(
#         'Time',
#         style={"margin-top": "30px"}
#     ),
#     dcc.Slider(
#         id='time_start',
#         min=unixTimeMillis(datetime.strptime('2016-05-31', '%Y-%m-%d')),
#         max=unixTimeMillis(datetime.strptime('2016-05-31', '%Y-%m-%d')),
#         marks={},
#         value=unixTimeMillis(datetime.strptime('2016-05-31', '%Y-%m-%d')),
#     ),
#     html.Div(id='date'),
# ])
#
#
# @app.callback(
#     Output('dd-output-container', 'children'),
#     Input('demo-dropdown', 'value')
# )
# def update_output(value):
#     return f'You have selected {value}'
#
# # @app.callback(
# #     [
# #         Output("date", 'children'),
# #     ],
# #
# #
# #     [Input("city_day", "value")])
# # def set_date(date):
# #     # print(date)
# #     return f'You have selected {date}'
#
# @app.callback(
#
#     Output("time_start", 'min'),
#     Output("time_start", 'max'),
#     Output("time_start", 'marks'),
#     Output("time_start",  'value'),
#
#     [Input("city_day", "value")])
# def set_date(date):
#     print(date)
#     min_date = date
#     max_date = unixTimeMillis(unixToDatetime(min_date) + timedelta(days=1))
#     value = date
#     daterange = pd.date_range(unixToDatetime(min_date), unixToDatetime(max_date), freq='15min')
#     # print(daterange)
#     marks = getMarks(daterange, 4)
#     print(min_date, max_date, marks, value)
#     return min_date, max_date, marks, value
#
# if __name__ == '__main__':
#     app.run_server(debug=True)