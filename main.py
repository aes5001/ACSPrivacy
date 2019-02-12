import googlemaps
import pickle


def readGoogleAPI():
    """read Google API key from the apikey.txt file"""

    with open('apikey.txt') as f:
        api_key = f.readline()
        f.close
    return api_key


def saveTempDirections(directions):
    """save temp directions to disk"""

    with open('directions.temp', 'wb') as f:
        pickle.dump(directions, f)
        f.close()
    print("Directions saved to directions.temp in working directory")


def getTempDirections():
    """get temp directions from disk"""

    with open('directions.temp', 'rb') as f:
        directions_file = pickle.load(f)
        f.close()
    print("Directions loaded from directions.temp in working directory")
    return directions_file

def getDirections(api_key):
    """get directions with help of Google Maps API"""

    gmaps = googlemaps.Client(key=api_key, queries_per_second=10)
    directions_result = gmaps.directions(origin="Kumpulan kampus, 00560 Helsinki",
                                         destination="Sello, Leppävaarankatu 3-9, 02600 Espoo",
                                         mode="driving", alternatives="true", units="metric")
    return directions_result


def inTimeDirections(directions, free_time):
    """get only directions that are fit to the free time"""

    available_directions = []
    for i in range(len(directions)):
            for j in directions[i]['legs']: #TODO waypoint/legs processing (multiplying)
                duration = j['duration']['value']
               
                if duration < free_time:
                    available_directions.append(directions[i])
    return available_directions                   
        


inTimeDirections(getTempDirections(), 1200)

##############################################
# get Direction and save them to temp file
# saveTempDirections(getDirections(readGoogleAPI()))
#############################################