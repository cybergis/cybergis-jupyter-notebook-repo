import pandas as pd
import geopandas as gpd
from geopandas import GeoSeries, GeoDataFrame
from shapely.geometry import Polygon, Point
from shapely.ops import cascaded_union

import ipywidgets as widgets
from IPython.display import display

import json
import folium

import requests

coords = {"UIUC" : [40.115950, -88.241591], "USC" : [33.997022,-81.026541], "LV" : [36.1699,-115.1561]}

def rating_open(lat_search, lon_search, open_close, rating_minimum, rating_num_min):
    
    search_item = "supermarket"
    api_key = '&key=AIzaSyBp-sJGdfd9Y_bW8WQFEdtGF54FIU0XiAk'
    search_criteria = "&location=" + lat_search + "," + lon_search + "&query=" + search_item
    api_address = r"https://maps.googleapis.com/maps/api/place/textsearch/json?"
    api_request = api_address + search_criteria + api_key

    api_response = requests.get(api_request).json()
    data = api_response['results']
    for d in data:
        d["geometry"] = Point(d["geometry"]["location"]["lat"],d["geometry"]["location"]["lng"])

    gdf = gpd.GeoDataFrame(data).set_geometry("geometry")
    gdf.crs = {'init': 'epsg:4326'}
    
    storeList = []
    goodStores = []
    
    for instance in range(0, len(gdf)):
        storeList.append(gdf[instance:instance+1])

    for eachStore in storeList:
        if eachStore.rating.values >= rating_minimum and eachStore.user_ratings_total.values >= rating_num_min:
            if open_close:
                for open_v in eachStore.opening_hours.values:
                    if open_v['open_now'] == True:
                        goodStores.append(eachStore["id"].iloc[0])
            else:
                goodStores.append(eachStore["id"].iloc[0])
        
    return goodStores

def show_results(location, transit, duration, open_now, rating_min, rating_num_min):
    if location in ["UIUC", "USC","LV"]:
        data = gpd.GeoDataFrame.from_file("./output/"+location+"_results.shp")
    else:
        print("Location not found!")
        return
    
    goodStores = rating_open(str(coords[location][0]), str(coords[location][1]), open_now, rating_min, rating_num_min)
    if goodStores:
        data = data[data["GrocStore"].isin(goodStores)]
        data = data[(data.transit==transit) & (data.TripTime==duration)]
    
        if data.empty:
            print("No grocery stores found!")
            return folium.Map(coords[location], zoom_start=12, tiles='Stamen Toner')
        else:
            data_union = {"geometry": cascaded_union(data["geometry"])}
            crs = {'init': 'epsg:4326'}

            if type(cascaded_union(data["geometry"])) == Polygon:
                data_union = gpd.GeoDataFrame(data_union, crs=crs, geometry = "geometry", index=[0])
            else:
                data_union = gpd.GeoDataFrame(data_union, crs=crs, geometry = "geometry")
            
            final_result = folium.Map(coords[location], zoom_start=12, tiles='Stamen Toner')
            
            folium.GeoJson(data_union, style_function=lambda feature: {
                'fillColor': "green",
                'color' : "green",
                'fillOpacity' : 0.2,
                }).add_to(final_result)
            
            return final_result
    else:
        print("No grocery stores found!")
        return folium.Map(coords[location], zoom_start=12, tiles='Stamen Toner')
    
def widget():    
    style = {'description_width': 'initial'}
    w_time = widgets.IntSlider(
        value=5,
        min=5,
        max=30,
        step=5,
        description='Max time (in minutes): ',
        style = style,
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=True,
    )

    num = widgets.IntSlider(
        value = 10,
        min = 1,
        max = 100,
        step = 1,
        description = 'Minimum number of reviews: ',
        style = style,
        readout = True,
    )

    w_rate = widgets.FloatSlider(
        value=4,
        min=1,
        max=5,
        step=0.1,
        description = 'Rating: ',
        style = style,
        readout = True,
    )

    r = widgets.RadioButtons(
        options=['drive', 'bike', 'walk'],
        description = 'Transportation mode: ',
        style = style,
        disabled=False
    )
    d = widgets.Dropdown(
        options = ['University of Illinois at Urbana-Champaign', 'University of South Carolina', 'Las Vegas'],
        value='University of South Carolina',
        description='Search location: ',
        style = style
    )

    ck = widgets.Checkbox(
        value=False,
        description='Open now',
        style = style
    )

    display(d)
    display(w_time)
    display(r)
    display(ck)
    display(w_rate)
    display(num)

    button = widgets.Button(description="Submit")
    output = widgets.Output()
    button2=widgets.Button(description="plot")

    display(button, output)

    duration = w_time.value
    transit = r.value
    location = d.value
    rate = w_rate.value
    openCheck = ck.value
    rating_min = w_rate.value
    rating_num_min = num.value

    def on_button_clicked(b):
        duration = w_time.value
        transit = r.value
        loc = d.value
        rate = w_rate.value
        open_now = ck.value
        rating_min = w_rate.value
        rating_num_min = num.value
        
        if loc =='University of Illinois at Urbana-Champaign':
            location = "UIUC"
        
        if loc =='University of South Carolina':
            location = "USC"
        
        if loc == 'Las Vegas':
            location = "LV"

        with output:
            print ("You are at: %s" %loc)
            print ("You choose to %s" %transit)
            print ("Your maximum travel time to grocery store is %s minutes" %duration)
            print ("You only want stores have rating higher than %s" %rate )
            print ("Open check: %s" %open_now)
            print ("\n")
            print ("Your accessible area is shown in green!")
        
        final_plot = show_results(location, transit, duration, open_now, rating_min, rating_num_min)
        display(final_plot)

    button.on_click(on_button_clicked)