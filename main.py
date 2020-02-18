import geocoder
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import pandas
import folium
import requests
import pycountry
import doctest


def get_data_from_films_locations_file(path):
    """
    Return data with location and year of every film in file

    (str) -> dict
    ex. dict1['2020'] = {location1: {film1, ...}, location2: {film2, ...}}
    """
    film_locations_data = {}
    with open(path, encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            line_values = line.split(',')
            film, year, location = line_values[0], line_values[1],\
                line_values[-1]
            if year in film_locations_data:
                if location not in film_locations_data[year]:
                    film_locations_data[year][location] = {film}
                else:
                    film_locations_data[year][location].add(film)
            else:
                film_locations_data[year] = {location: {film}}
    return film_locations_data


def find_nearest_countries_from_coordinates(countries_coordinates_path,
                                            user_coordinates):
    """
    Return at least 2 nearest countries to user from coordinates

    (str, list) -> list
    >>> find_nearest_countries_from_coordinates('countries_coordinates.csv',\
     [1.3061832,103.85058749683245])
    ['Singapore', 'Malaysia']
    """
    data = pandas.read_csv(countries_coordinates_path, sep='\t')
    latitudes, longitudes = data['latitude'], data['longitude']
    countries = data['name']
    distance_list = []
    for x, y, country in zip(latitudes, longitudes, countries):
        distance = geodesic((x, y), user_coordinates).km
        distance_list.append((distance, country))
    nearest_countries = [elem[1] for elem in sorted(distance_list)][:2]
    try:
        user_country = get_country_from_coordinates(user_coordinates)
        if user_country not in nearest_countries:
            nearest_countries.append(user_country)
    except Exception:
        # if doesn't matter what we fill in user_country, but
        # if it's empty string, there will be an exception later
        user_country = 'Ukraine'
    # If user's country is not USA, but it's near his country,
    # get rid of USA
    if pycountry.countries.search_fuzzy(user_country)[0].alpha_3 != 'USA':
        for country in nearest_countries:
            if pycountry.countries.search_fuzzy(country)[0].alpha_3 == 'USA':
                nearest_countries.remove(country)
                break
    else:
        # There too many filming in USA, get rid of near countries
        return ['USA']
    return nearest_countries


def get_near_cities_from_user_coordinates(user_coordinates):
    """
    Return 100 nearest cities to user

    (list) -> list
    >>> get_near_cities_from_user_coordinates([38.9344, -95.0956])
    ['Eudora', 'De Soto', 'Lawrence', 'Tonganoxie', 'Gardner']
    """
    data = pandas.read_csv('city_coordinates.tsv', sep='\t')
    cities = data['city_ascii']
    latitudes, longitudes = data['lat'], data['lng']
    distance_list = []
    for city, lat, lng in zip(cities, latitudes, longitudes):
        try:
            distance = geodesic((lat, lng), user_coordinates).km
            distance_list.append(((lat, lng), city, distance))
        except Exception:
            continue
    distance_list_sorted = sorted(distance_list, key=lambda x: x[-1])
    return [elem[-2] for elem in distance_list_sorted[:100]]


def write_films_in_user_country_to_file_usa(from_path, to_path,
                                            user_year, user_coordinates):
    """
    Write films filming locations to data file if user_country is USA

    (str, str, int, list) -> None
    ex. file structure: location;\tlatitude;\tlongitude;\tfilms...
    """
    near_cities = get_near_cities_from_user_coordinates(user_coordinates)
    films_locations = get_data_from_films_locations_file(from_path)[
        str(user_year)]
    with open(to_path, mode='w', encoding='utf-8') as f:
        f.write("location;\tlatitude;\tlongitude;\tfilms\n")
        for location in films_locations:
            for city in near_cities:
                if 'USA' in location and city in location:
                    try:
                        latitude, longitude = \
                            get_coordinates_from_location(location)
                    except Exception:
                        continue
                    films_str = '/'.join(films_locations[location])
                    f.write(location + ';\t' + str(latitude) + ';\t'
                            + str(longitude) + ';\t' + films_str + '\n')


def write_films_in_user_country_to_file_check(from_path, to_path,
                                              user_year, user_coordinates):
    """
    Write films, which were filmed in user_country in a certain year
    to file with path=to_path, while all the info about films is in from_path

    (str, str, int, str, list, int) -> None
    ex. of file structure: location;\tlatitude;\tlongitude;\tfilm1/film2/...
    """
    # if the number of points on map in user country is too small
    # (not popular country),alg will parse other country,
    # till finds enough points
    near_countries = find_nearest_countries_from_coordinates(
        'countries_coordinates.csv', user_coordinates)
    if near_countries[0] == 'USA':
        write_films_in_user_country_to_file_usa(from_path, to_path,
                                                user_year, user_coordinates)
        return None
    country_v = [pycountry.countries.search_fuzzy(country)[0]
                 for country in near_countries]
    try:
        user_country_variety = [[elem.official_name,
                                elem.name,
                                elem.alpha_3] for elem in country_v]
    except AttributeError:
        user_country_variety = [[elem.name] for elem in country_v]
    films_locations = get_data_from_films_locations_file(from_path)[
        str(user_year)]
    with open(to_path, mode='w', encoding='utf-8') as f:
        f.write("location;\tlatitude;\tlongitude;\tfilms\n")
        for location in films_locations:
            for country_v in user_country_variety:
                for name_of_country in country_v:
                    if name_of_country in location:
                        try:
                            latitude, longitude = \
                                get_coordinates_from_location(location)
                        except Exception:
                            continue
                        films_str = '/'.join(films_locations[location])
                        f.write(location + ';\t' + str(latitude) + ';\t'
                                + str(longitude) + ';\t' + films_str + '\n')


def get_coordinates_from_location(location):
    """
    Return coordinates from location

    (str) -> list
    >>> get_coordinates_from_location("Arena Lviv Lviv Ukraine")
    [49.8055205, 23.973569165549602]
    """
    g = geocoder.osm(location)
    return g.latlng


def get_country_from_coordinates(coordinates):
    """
    Return country from coordinates

    (list) -> str
    >>> get_country_from_coordinates([44.4970713, 34.1586871])
    'Ukraine'
    """
    geolocator = Nominatim(user_agent="random_one")
    location = geolocator.reverse(coordinates, language='en')
    country = location.address.split(',')[-1].strip()
    return country


# def get_address_values_from_coordinates(coordinates):
#     """
#     Return address values up to code of state
#
#     >>> get_address_values_from_coordinates([38.8061, -94.2654])
#     ['Matthes Lane', 'Pleasant Hill', 'Cass County']
#     """
#     geolocator = Nominatim(user_agent="random_one")
#     location = geolocator.reverse(coordinates, language='en')
#     values = [elem.strip() for elem in location.address.split(',')[2:5]]
#     return values


def get_nearest_films_filming_from_file(path, user_coordinates):
    """
    Return list with nearest filming of films, based on user_coordinates and
    films from database from path

    (str, list) -> list

    ex. [(film), (lat, long), ...], sorted by a distance to user
    """
    data = pandas.read_csv(path, sep=';\t', engine='python')
    locations, films = data['location'], data['films']
    lat, long = data['latitude'], data['longitude']

    distance_list = []
    for location, x, y, film in zip(locations, lat, long, films):
        distance = geodesic((x, y), user_coordinates).km
        distance_list.append((location, film, (x, y), distance))
    distance_list_sorted = sorted(distance_list, key=lambda t: t[-1])
    nearest_films_filming = [(elem[1], elem[2])
                             for elem in distance_list_sorted]
    return nearest_films_filming


def create_html_from_coordinates(film_coordinates_list, film_year,
                                 user_coordinates):
    """
    Create html file with the nearest film filming to user
    with a certain year

    (list, int, list) -> None
    """
    map = folium.Map(location=user_coordinates, zoom_start=10)
    main_layer = folium.FeatureGroup(name="10 Nearest movies filming")

    for elem in film_coordinates_list[:10]:
        lat, long = elem[1]
        films = elem[0]
        text = "There're some movies, filmed here: {}"\
            .format(','.join(films.split('/')))
        main_layer.add_child(folium.Marker(location=(lat, long),
                                           popup=text,
                                           color='green',
                                           icon=folium.Icon()))
    map.add_child(main_layer)

    boarders = folium.FeatureGroup(name="Boarders")

    boarders.add_child(folium.GeoJson(data=open('world.json', 'r',
                                                encoding='utf-8-sig').read()))
    map.add_child(boarders)
    create_new_layer_with_world_capitals(map, 'concap.csv')
    map.add_child(folium.LayerControl())
    map.save(str(film_year) + 'movies_map.html')


def run_program():
    """
    Run the program
    """
    start = time.time()
    try:
        user_year = int(input("Please enter a year"
                        " you would like to have a map for: "))
    except ValueError:
        print("Year should be entered as int value! Try again")
        return None
    try:
        user_coordinates = [float(value) for value in
                            input("Please enter your location"
                                  " (format: lat, long): ").split(',')]
    except ValueError:
        print("Check for correctness of format you entered!")
        return None
    print("Map is generating...")
    print("Please wait...")
    write_films_in_user_country_to_file_check('locations.csv', 'data.csv',
                                              user_year, user_coordinates)
    create_html_from_coordinates(
        get_nearest_films_filming_from_file('data.csv',
                                            user_coordinates),
        user_year, user_coordinates)
    # create_html_from_coordinates(123, user_coordinates)
    print("Finished. Please have look at the map {}_movies_map.html".
          format(str(user_year)))
    print("Succeeded in {} sec".format(round(time.time() - start), 2))


def create_new_layer_with_world_capitals(map, path):
    """
    To object map add world capitals from file path

    (map_object, str) -> None
    """
    capitals_layer = folium.FeatureGroup(name="World capitals")
    data = pandas.read_csv(path)
    for lat, long in zip(data['CapitalLatitude'], data['CapitalLongitude']):
        capitals_layer.add_child(folium.CircleMarker(location=(lat, long),
                                                     radius=6,
                                                     color='red'))
    map.add_child(capitals_layer)


if __name__ == "__main__":
    # doctest.testmod()
    run_program()
