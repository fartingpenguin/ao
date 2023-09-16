import googlemaps

# Requires API key
gmaps = googlemaps.Client(key='Your_API_key')

# Geocoding an address
my_dist = gmaps.distance_matrix('Delhi','Mumbai')['rows'][0]['elements'][0]


print(my_dist)
