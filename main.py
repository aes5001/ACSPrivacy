import googlemaps
import pickle
import polyline


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
    print("Data loaded from " + filename + ".temp in working directory")
    return data_file


def getDirections(origin_addr, destination_addr, waypoints_list):
    """get directions with help of Google Maps API"""

    origin_addr = str(origin_addr)
    destination_addr = str(destination_addr)
    waypoints_list = list(waypoints_list)

    gmaps = googlemaps.Client(key=readGoogleAPI(), queries_per_second=10)
    directions_result = gmaps.directions(origin=origin_addr,
                                         destination=destination_addr,
                                         mode="driving", alternatives="true", units="metric",
                                         waypoints=waypoints_list)
    # directions_result = gmaps.directions(origin="Kumpulan kampus, 00560 Helsinki",
    #                                      destination="Sello, Leppävaarankatu 3-9, 02600 Espoo",
    #                                      mode="driving", alternatives="true", units="metric",
    #                                      waypoints=["Linnanmaki, Tivolikuja 1, 00510 Helsinki", 
    #                                      "Rush Helsinki, Valimotie 25, 00380 Helsinki"])
    print("Directions received from Google")
    return directions_result

# waylist = ["Linnanmaki, Tivolikuja 1, 00510 Helsinki", 
#                                          "Rush Helsinki, Valimotie 25, 00380 Helsinki"]
# direct = getDirections("Kumpulan kampus, 00560 Helsinki", 
# "Sello, Leppävaarankatu 3-9, 02600 Espoo",
# waylist)

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

def getNearPOI(location, max_radius):
    """get near POI from coordinates"""

    gmaps = googlemaps.Client(key = readGoogleAPI(), queries_per_second = 10)
    places = gmaps.places_nearby(location=location,                         
                                        language='en-US',
                                        radius = max_radius)
    # print("Nearby places are available")
    return places


def getNearPOIPolylines(directions, max_radius):
    """get POI for coordinates"""

    for i in range(len(directions)): 
        directions[i]['polyline_coor_POI'] = list()
        next_j = 0
        for j in range(len(directions[i]['polyline_coordinates'])):
            location = str(directions[i]['polyline_coordinates'][j][0]) + ',' + str(directions[i]['polyline_coordinates'][j][1])

            # coordinates = list(directions[i]['polyline_coordinates'][j])
            coordinates = directions[i]['polyline_coordinates'][j]
            # places = [1,2,3]
            # directions[i]['polyline_coor_POI'].append([tuple(coordinates)]+[places])
           

            if j == 0:
                places = getNearPOI(location, max_radius)
                directions[i]['polyline_coor_POI'].append([tuple(coordinates)]+[places])

            distance_lat = directions[i]['polyline_coordinates'][next_j][0] - directions[i]['polyline_coordinates'][j][0]
            distance_lon = directions[i]['polyline_coordinates'][next_j][1] - directions[i]['polyline_coordinates'][j][1]
            
            distance_lat = abs(distance_lat)
            distance_lat = round(distance_lat, 6)

            distance_lon = abs(distance_lon)
            distance_lon = round(distance_lon, 6)
            
            if distance_lat > 0.020 or distance_lon > 0.020: #distance between POIs by default 0.005
                next_j = j
                places = getNearPOI(location, max_radius)
                directions[i]['polyline_coor_POI'].append([tuple(coordinates)]+[places])
            
    saveTempData(directions, 'nearbyPOI')
    print("Nearby POIs are downloaded")
    return directions


def filterPOI():
    """select only POI that can be visited during free time"""
    directions = getTempData('nearbyPOI')
    for i in range(len(directions)):
        for j in range(len(directions[i]['polyline_coor_POI'])): 
            directions[i]['polyline_coor_POI'][j][1] = directions[i]['polyline_coor_POI'][j][1]['results']
    saveTempData(directions, 'nearbyPOI')
    return('POIs were filtered')

def getPOIType(type_POI):
    """Find POI type"""

    for i in range(len(type_POI)):
        if type_POI[i] == 'shopping_mall' or type_POI[i] == 'restaurant':
            return True
    return False

def getWaypointsForPOI(directions):
    """get waypoints for each POI"""
    
    waypoint_list = list()
    for i in range(len(directions)):
        origin_addr = directions[i]['legs'][0]['start_address'] #update to directions without waypoints
        destination_addr = directions[i]['legs'][2]['end_address'] #update to directions without waypoints
        for j in range(len(directions[i]['polyline_coor_POI'])):
            for k in range(len(directions[i]['polyline_coor_POI'][j][1])):
                if getPOIType(directions[i]['polyline_coor_POI'][j][1][k]['types']):
                    waypoint = directions[i]['polyline_coor_POI'][j][1][k]['place_id']
                    waypoint_list.append(waypoint)
                    # getDirections(origin_addr, destination_addr, waypoint)
                
    destination_wayp_list = [origin_addr, destination_addr, waypoint_list]
    saveTempData(destination_wayp_list,'dest_wayp_list')
    print("Potential waypoints were obtained")
    return destination_wayp_list

def getDestinationViaPOI (destination_list):
    """get all routes via POI"""
    for i in range(len(destination_list[2])):
        destination = getDirections(destination_list[0], destination_list[1], destination_list[2][i])

    return destination_list

tracking_interval = 1200 #tracking interval is seconds when vehicle position send to the vehicle owner

directions = getTempData('nearbyPOI') #download the last data

# places = getTempData('places')

destinations_POI = getWaypointsForPOI(directions)

# directions = inTimeDirections(getTempData('directions'), tracking_interval)
# directions = decodePolylines(getTempData('directions'))
# directions = getNearPOIPolylines(directions, 1000)
#############################################
"""get Direction and save them to temp file (useful to reduce amount of requests)"""
# saveTempData(getDirections(readGoogleAPI()), 'directions')

# directions = decodePolylines(getTempData('directions'))
# saveTempData(getNearPOIPolylines(directions), 'places')
#############################################
