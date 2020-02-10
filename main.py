# import folium
# import pandas


# map = folium.Map()
# map.add_child(folium.Marker(location=[49.817545, 24.023932],
#                             popup="Хіба я тут!", icon=folium.Icon()))
# map.save('map1.html')
# data = pandas.read_csv("Stan_1900.csv", error_bad_lines=False)
# # print(data['lat'])
# lat = data['lat']
# lon = data['lon']
# map = folium.Map(location=[48.314775, 25.082925],
#  zoom_start=10)
# map.save('map1.html')

import folium
import pandas
data = pandas.read_csv("Stan_1900.csv", error_bad_lines=False)
lat = data['lat']
lon = data['lon']
map = folium.Map(location=[48.314775, 25.082925], zoom_start=10)
fg = folium.FeatureGroup(name="Kosiv map")
for lt, ln in zip(lat, lon):
    fg.add_child(folium.Marker(location=[lt, ln], popup="1900 рік",
                               icon=folium.Icon()))
map.add_child(fg)
map.save('Map_5.html')
