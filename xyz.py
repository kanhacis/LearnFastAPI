import requests
from geopy.geocoders import Nominatim

def get_location():
    try:
        # Get the current IP location
        response = requests.get('https://ipinfo.io/json')
        data = response.json()

        # Extract latitude and longitude
        loc = data['loc'].split(',')
        latitude = loc[0]
        longitude = loc[1]
        city = data['city']
        address = data["org"]

        return city, latitude, longitude, address
    except Exception as e:
        print(f"Error: {e}")
        return None


location = get_location()
if location:
    city, latitude, longitude, address = location
    print(f"City: {city}")
    print(f"Address: {address}")
    print(f"Latitude: {latitude}")
    print(f"Longitude: {longitude}")
