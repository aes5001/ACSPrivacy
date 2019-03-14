import googlemaps
import pickle
import polyline
from time import sleep
import populartimes

import numpy as np
import scipy.stats
import matplotlib.pyplot as plt


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


def getDirections(origin_addr, destination_addr, waypoints_list=None):
    """get directions with help of Google Maps API"""

    origin_addr = str(origin_addr)
    destination_addr = str(destination_addr)
    
    gmaps = googlemaps.Client(key=readGoogleAPI(), queries_per_second=10)
    if waypoints_list is not None:
        directions_result = gmaps.directions(origin=origin_addr,
                                            destination=destination_addr,
                                            mode="driving", units="metric",
                                            waypoints=waypoints_list)
    else:
        directions_result = gmaps.directions(origin=origin_addr,
                                            destination=destination_addr,
                                            mode="driving", alternatives="true", units="metric")
    # directions_result = gmaps.directions(origin="Kumpulan kampus, 00560 Helsinki",
    #                                      destination="Sello, Leppävaarankatu 3-9, 02600 Espoo",
    #                                      mode="driving", alternatives="true", units="metric",
    #                                      waypoints=["Linnanmaki, Tivolikuja 1, 00510 Helsinki", 
    #                                      "Rush Helsinki, Valimotie 25, 00380 Helsinki"])
    print("Directions received from Google")
    return directions_result

# getDirections("helsinki", "porvoo", "lahti")
# getDirections(origin_addr, destination_addr, waypoints_list)

def inTimeDirections(directions, tracking_interval):
    """get only directions that are fit to the tracking interval. 
    Also find a free time that could be used to visit to POI"""

    available_directions = list ()
    duration = 0

    for i in range(len(directions)):
        duration = 0
        if len(directions[i]['legs']) == 1:         #do if there is no waypoints
                duration = directions[i]['legs'][0]['duration']['value'] 
                if duration < tracking_interval:
                    directions[i]['overview_free_time'] = tracking_interval - duration
                    available_directions.append(directions[i])
        else:                                       #do if there are waypoints
            for j in range(len(directions[i]['legs'])):
                duration += directions[i]['legs'][j]['duration']['value']
               
            if duration < tracking_interval:
                directions[i]['overview_free_time'] = tracking_interval - duration
                available_directions.append(directions[i])
        
    if len(available_directions) > 0:
        print("The number of intime directions: " + str(len(available_directions)))
    else:
        print("No in time directions were found")
    return available_directions

# saveTempData(inTimeDirections(getTempData('nearbyPOIs'),3600),'nearbyPOITime')

def decodePolylines(directions):
    """get coordinates from polylines"""

    for i in range(len(directions)):   
        directions[i]['polyline_coordinates'] = polyline.decode(directions[i]['overview_polyline']['points'])   
    print("Polyline decoded successfully")           
    return directions


def addPopularTimes(places):
    """add popular times, time spend to polyline_coor_POI list"""
    
    for i in range(len(places['results'])): 
        pop_times_res = popTimes(places['results'][i]['place_id'])
        pop_times_fields = dict()
        d_items = list(['rating', 'rating_n', 'time_spent', 'populartimes', 'time_wait'])
        for j in d_items:
            pop_times_fields[j] = pop_times_res.get(j, -1)
            
        if pop_times_fields['time_spent'] != -1:
            pop_times_fields['time_spent'][0] = pop_times_fields['time_spent'][0] * 60
            pop_times_fields['time_spent'][1] = pop_times_fields['time_spent'][1] * 60
        
        places['results'][i].update(pop_times_fields)
 
    print("Popular times were added to the places")
    return places


def getNearPOI(location, max_radius):
    """get near POI from coordinates"""
    
    gmaps = googlemaps.Client(key = readGoogleAPI(), queries_per_second = 10)
    places = gmaps.places_nearby(location = location,                         
                                        language = 'en-US',
                                        radius = max_radius)
    try:
        if places['next_page_token']: #Google maps provides only 20 result on return, we have to ask additional POIs
            all_results = list()
            all_results.extend(places['results'])                                               
            try:
                while places['next_page_token']:
                    sleep(3) # Google maps needs a time to create the next POI page
                    places = gmaps.places_nearby(page_token = places['next_page_token'])
                    all_results.extend(places['results'])  
            except:
                places['results'] = all_results 
    except: 
        print("Only " + str(len(places['results'])) + " POIs are available") 
    
    places = addPopularTimes(places)   #request popular times for all places
    # print("Nearby places are available")
    return places

# getNearPOI('70.502972, 25.039944',1000)   #somewhere in the north
# getNearPOI('60.261220, 25.080628', 1000) #Helsinki area

def getNearPOIPolylines(directions, max_radius):
    """get POI for polyline coordinates (polyline points)"""

    for i in range(len(directions)): 
        directions[i]['polyline_coor_POI'] = list()
        next_j = 0
        for j in range(len(directions[i]['polyline_coordinates'])):
            location = str(directions[i]['polyline_coordinates'][j][0]) + ',' + str(directions[i]['polyline_coordinates'][j][1])
            coordinates = directions[i]['polyline_coordinates'][j]
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
            
    saveTempData(directions, 'nearbyPOIs')
    print("Nearby POIs are downloaded")
    return directions


def filterPOI():
    """????select only POI that can be visited during free time"""
    directions = getTempData('nearbyPOIs')
    for i in range(len(directions)):
        for j in range(len(directions[i]['polyline_coor_POI'])): 
            directions[i]['polyline_coor_POI'][j][1] = directions[i]['polyline_coor_POI'][j][1]['results']
    saveTempData(directions, 'nearbyPOIs')
    return('POIs were filtered')

def getPOIByType(POI_list, POI_type):
    """Find POI type"""

    for i in range(len(POI_list)):
        for j in range(len(POI_type)):
            if POI_list[i] == POI_type[j]:
                return True
    return False


def getWaypointsForPOI(directions):
    """select (filter) potential waypoints from obtained list of POIs with help of getPOIByType(), 
    remove all unnecessary data. Add only POIs that have "time_spent" info and are in free time intertval"""
    
    waypoint_list = list()
    for i in range(len(directions)):
        origin_addr = directions[i]['legs'][0]['start_address'] #update to directions without waypoints
        if len(directions[i]['legs']) == 1:
            destination_addr = directions[i]['legs'][0]['end_address'] #for directions without waypoints
        else:
            destination_addr = directions[i]['legs'][2]['end_address'] #for directions with waypoints NEED TEST
        for j in range(len(directions[i]['polyline_coor_POI'])):
            for k in range(len(directions[i]['polyline_coor_POI'][j][1]['results'])):
                if getPOIByType(directions[i]['polyline_coor_POI'][j][1]['results'][k]['types'], ['shopping_mall', 'restaurant']): #POI types
                    if directions[i]['polyline_coor_POI'][j][1]['results'][k]['time_spent'] != -1:
                        if directions[i]['polyline_coor_POI'][j][1]['results'][k]['time_spent'][0] < directions[i]['overview_free_time']:
                            waypoint = directions[i]['polyline_coor_POI'][j][1]['results'][k]['place_id']
                            types = directions[i]['polyline_coor_POI'][j][1]['results'][k]['types']
                            time_spent = directions[i]['polyline_coor_POI'][j][1]['results'][k]['time_spent']
                            populartimes = directions[i]['polyline_coor_POI'][j][1]['results'][k]['populartimes']
                            waypoint_list.append(["place_id:" + waypoint, types, time_spent, populartimes])
                    
                    # else: #add POIs that do not have "time_spent" information
                    #     waypoint = directions[i]['polyline_coor_POI'][j][1]['results'][k]['place_id']
                    #     types = directions[i]['polyline_coor_POI'][j][1]['results'][k]['types']
                    #     time_spent = directions[i]['polyline_coor_POI'][j][1]['results'][k]['time_spent']
                    #     populartimes = directions[i]['polyline_coor_POI'][j][1]['results'][k]['populartimes']
                    #     waypoint_list.append(["place_id:" + waypoint, types, time_spent, populartimes])
    destination_wayp_list = [origin_addr, destination_addr, waypoint_list]
    saveTempData(destination_wayp_list,'dest_wayp_list')
    print("Potential in time waypoints were obtained")
    return destination_wayp_list

# destinations_POI = getWaypointsForPOI(getTempData('nearbyPOIs'))


def getDestinationViaPOI (destination_list):
    """get all routes via POI for dest_wayp_list (getWaypointsForPOI) list presentation"""

    destination = list()
    for i in range(len(destination_list[2])):
        destination.extend(getDirections(destination_list[0], destination_list[1], destination_list[2][i][0]))
        destination[i]['waypoint_types']=destination_list[2][i][1]
        destination[i]['time_spent']=destination_list[2][i][2]
        destination[i]['populartimes']=destination_list[2][i][3]
    saveTempData(destination,'potential_dest')
      
    print("Potential directions via POI received")
    return destination

# getDestinationViaPOI(getTempData('dest_wayp_list'))

def potentialVisitPOI (directions_in_time, visit_time=0):
    """calculate probability to visit a POI"""

    #TODO add POI type to directions for comparison
    for i in range(len(directions_in_time)):

        
        mean = np.mean(directions_in_time[i]['time_spent'])
        std = np.std(directions_in_time[i]['time_spent'])
        # variance = np.var(directions_in_time[i]['time_spent'])
        free_time = directions_in_time[i]['overview_free_time']
        pdf = scipy.stats.norm(mean,std).pdf(free_time)
       
        cdf = scipy.stats.norm(mean,std).cdf(free_time)
        plt.hist(cdf, normed=True, cumulative=True, label='CDF',
            histtype='step', alpha=0.8, color='k')
        plt.show()
        #draw plot
        # pdf = np.random.normal(mean, std, 100)

        count, bins, ignored = plt.hist(pdf, 30, density=True)
        plt.plot(bins, 1/(std * np.sqrt(2 * np.pi)) * 
            np.exp( - (bins - mean)**2 / (2 * std**2) ),
            linewidth=2, color='r')
        # plt.show()

        # mu, sigma = 0, 0.1 # mean and standard deviation
        # s = np.random.normal(mu, sigma, 1000)
        # count, bins, ignored = plt.hist(s, 30, density=True)
        
        # plt.plot(bins, 1/(sigma * np.sqrt(2 * np.pi)) * 
        #     np.exp( - (bins - mu)**2 / (2 * sigma**2) ),
        #     linewidth=2, color='r')
        # plt.show()
        
        # if directions_in_time[i]['overview_free_time'] >= visit_time.get('shopping_mall', 0):
        #     print("POI can be visited")

    return directions_in_time


def popTimes (placeID):
    """ Return popular time, rating, time spend with help of populartimes lib"""

    placeID = str(placeID)
    pop_times = populartimes.get_id(readGoogleAPI(), placeID)
    return pop_times


tracking_interval = 3600 #tracking interval is seconds when vehicle position send to the vehicle owner
POI_visit_time = {'shopping_mall': 1200, 'restaurant': 2400}

# poptimes = popTimes("")


#############################################
"""get Direction and save them to temp file (useful to reduce amount of requests)"""
# saveTempData(getDirections("Kumpulan kampus, 00560 Helsinki", "Sello, Leppävaarankatu 3-9, 02600 Espoo"), 'directions')
# directions = inTimeDirections(getTempData('directions'), tracking_interval)
# directions = decodePolylines(getTempData('directions'))
# directions = getNearPOIPolylines(directions, 1000)
# directions = getWaypointsForPOI(getTempData('nearbyPOIs'))
# directions = getDestinationViaPOI(getTempData('dest_wayp_list'))
directions = inTimeDirections(getTempData('potential_dest'), tracking_interval)
potentialVisitPOI(directions)
#############################################
