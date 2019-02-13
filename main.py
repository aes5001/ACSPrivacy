import googlemaps
import pickle
import polyline
import re


def readGoogleAPI():
    """read Google API key from the apikey.txt file"""

    with open('apikey.txt') as f:
        api_key = f.readline()
        f.close
    return api_key


def saveTempData(data_type, filename):
    """save temp data to disk"""

    with open(filename +'.temp', 'wb') as f:
        pickle.dump(data_type, f)
        f.close()
    print("Data saved to "+ filename +".temp in working directory")


def getTempData(filename):
    """get temp data from disk"""

    with open(filename + '.temp', 'rb') as f:
        data_file = pickle.load(f)
        f.close()
    print("Directions loaded from " + filename + ".temp in working directory")
    return data_file


def getDirections(api_key):
    """get directions with help of Google Maps API"""

    gmaps = googlemaps.Client(key=api_key, queries_per_second=10)
    directions_result = gmaps.directions(origin="Kumpulan kampus, 00560 Helsinki",
                                         destination="Sello, Leppävaarankatu 3-9, 02600 Espoo",
                                         mode="driving", alternatives="true", units="metric",
                                         waypoints=["Linnanmaki, Tivolikuja 1, 00510 Helsinki", 
                                         "Rush Helsinki, Valimotie 25, 00380 Helsinki"])
    # directions_result = gmaps.directions(origin="Kumpulan kampus, 00560 Helsinki",
    #                                      destination="Sello, Leppävaarankatu 3-9, 02600 Espoo",
    #                                      mode="driving", alternatives="true", units="metric",
    #                                      waypoints=["Linnanmaki, Tivolikuja 1, 00510 Helsinki", 
    #                                      "Rush Helsinki, Valimotie 25, 00380 Helsinki"])
    print("Directions received from Google")
    return directions_result


def inTimeDirections(directions, tracking_interval):
    """get only directions that are fit to the tracking interval. 
    Also find a free time that could be used to visit to POI"""

    available_directions = []
    for i in range(len(directions)): 
        # TODO waypoint/legs processing (multiplying)
        for j in directions[i]['legs']:
            duration = j['duration']['value']

            if duration < tracking_interval:
                # directions[i]['overview_time'] = 0
                directions[i]['overview_free_time'] = tracking_interval - duration 
                available_directions.append(directions[i])
    return available_directions


def decodePolylines(directions):
    """get coordinates from polylines"""

    for i in range(len(directions)):   
        directions[i]['polyline_coordinates'] = polyline.decode(directions[i]['overview_polyline']['points'])   
    print("Polyline decoded successfully")           
    return directions

def getNearPOI(api_key, directions):
    """get near POI from coordinates"""
    gmaps = googlemaps.Client(key=api_key, queries_per_second=10)
    place = gmaps.places_nearby(location='60.21255,24.88626',                         
                            language='en-US',
                            radius = 100)
    print("Nearby places are available")
    return place


tracking_interval = 1200 #tracking interval is seconds when vehicle position send to the vehicle owner

places = getTempData('places')

directions = decodePolylines(getTempData('directions'))



# getNearPOI(readGoogleAPI(), directions)
# directions = inTimeDirections(getTempDirections(), tracking_interval)

#############################################
"""get Direction and save them to temp file (useful to reduce amount of requests)"""
# saveTempData(getDirections(readGoogleAPI()), 'directions')
# saveTempData(getNearPOI(readGoogleAPI(), directions), 'places')
#############################################
