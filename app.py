"""
Ideas: avg trip duration, most popular bike stations, avg distance travelled, median trip duration, mode trip duration, most popular times of day for bike share
can group by user type; categorize by toronto areas instead of stations; by month, year, etc.,
add a map
"""	
import pandas as pd
from datetime import datetime
import numpy as np

import dash
import dash_core_components as dcc
import dash_html_components as html

from data import Data

app = dash.Dash(__name__)
server = app.server

def process(process=False):
    data = Data()
    if process:
        data.call_api("https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show", { "id": "7e876c24-177c-4605-9cef-e50dd74c617f"})
        f = ["Bike share ridership 2021-01", "Bike share ridership 2020", "Bike Share Ridership 2019 "]
        data.process_api_file(f, True)
        # data.resource_to_sql(ind_one)
    return data

def get_avg_trip_dur(df):
    avg_trip_duration_df = df.groupby([df["Start Time"].dt.date, df["Start Station Name"]])["Trip  Duration"].mean().reset_index(name="average")
    avg_trip_duration_df["Start Time"] = pd.to_datetime(avg_trip_duration_df["Start Time"])
    avg_trip_duration_df["average"] = avg_trip_duration_df["average"].round(2)
    return avg_trip_duration_df

def get_avg_trips(df):
    avg_trips_df = df.groupby([df["Start Time"].dt.date, df["Start Station Name"]])["Trip  Duration"].count().reset_index(name="count")
    avg_trips_df["Start Time"] = pd.to_datetime(avg_trips_df["Start Time"])
    return avg_trips_df

obj = process()
df = obj.read_csv("bike-share-2019_2021.csv")

avg_dur_df = get_avg_trip_dur(df)
avg_trips_df = get_avg_trips(df)

app.layout = html.Div(
    children=[
        html.H1(
            children="Toronto Bike Shares Visualized",
            className="header-one"
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed = avg_dur_df["Start Time"].min(),
                            max_date_allowed = avg_dur_df["Start Time"].max(),
                            start_date = avg_dur_df["Start Time"].min(),
                            end_date = avg_dur_df["Start Time"].max(),
                        ),
                    ],
                    className="date-filter"
                ),
                html.Div(
                    children=[
                        dcc.Dropdown(
                            id="start-station-filter",
                            options=[
                                {"label": start_station_name, "value": start_station_name}
                                for start_station_name in np.sort(avg_dur_df["Start Station Name"].unique())
                            ],
                            value="1 Market St",
                            searchable=False,
                            clearable=False,
                            className="dropdown",
                        ),
                    ],
                )
            ],
            className="filters"
        ),
        html.Div(
            children=[
                html.Div( 
                    children=dcc.Graph(
                        id="avg-duration",
                        # config={"displayModeBar": False},
                    ),
                    className="card"
                )
            ]
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(                            
                        id="avg-trips",
                        # config={"displayModeBar": False},                            
                    ),
                    className="card"
                )
            ]
        )
    ]   
)

@app.callback(
    [
        dash.dependencies.Output("avg-duration", "figure"), 
        dash.dependencies.Output("avg-trips", "figure")
    ],
    [
        dash.dependencies.Input("date-range", "start_date"),
        dash.dependencies.Input("date-range", "end_date"),
        dash.dependencies.Input("start-station-filter", "value")
    ],
)
def update_charts(start_date, end_date, start_station_name):
    mask_dur = (
        (avg_dur_df["Start Time"] >= start_date) &
        (avg_dur_df["Start Time"] <= end_date) & 
        (avg_dur_df["Start Station Name"] == start_station_name)
    )

    mask_trips = (
        (avg_trips_df["Start Time"] >= start_date) &
        (avg_trips_df["Start Time"] <= end_date) & 
        (avg_dur_df["Start Station Name"] == start_station_name)
    )

    filtered_data_dur = avg_dur_df.loc[mask_dur]
    filtered_data_trips = avg_trips_df.loc[mask_trips]

    avg_trips_figure = {
        "data": [
            {
                "x": filtered_data_trips["Start Time"],
                "y": filtered_data_trips["count"],
                "type": "lines",
                'line': dict(color='orange')
            }
        ],
        "layout": {
            "title": "Average # of Trips Per Day",
        },
    }

    avg_dur_figure = {
        "data": [
            {
                "x": filtered_data_dur["Start Time"],
                "y": filtered_data_dur["average"],
                "type": "lines",
                'line': dict(color='orange')
            }
        ],
        "layout": {
            "title": "Average Trip Duration Per Day",
            "yaxis": {
                "title":"Time (m)"
            }
        },
    }

    return avg_dur_figure, avg_trips_figure

if __name__ == "__main__":
    app.run_server(debug=True)
    
