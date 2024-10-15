import requests


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
        location = data["org"]

        return city, latitude, longitude, location
    except Exception as e:
        print(f"Error: {e}")
        return None 