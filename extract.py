import requests
import json

# OpenSky API endpoint for current flights
OPENSKY_URL = "https://opensky-network.org/api/states/all"

def fetch_live_flights():
    print("Pinging OpenSky API for live flight data...")

    try:
        # 10 second timeout so script doesn't hang if server is slow
        response = requests.get(OPENSKY_URL, timeout=10)
        response.raise_for_status()

        data = response.json()

        flights = data.get('states',[])

        if not flights:
            print("No flights found right now.")
            return

        print(f"Successfully fetched {len(flights)} flights currently in the air!")
        print("Here is a sample of the first 5 flights:\n")

        # Slicing list
        for flight in flights[:5]:
            callsign = str(flight[1]).strip() if flight[1] else "UNKNOWN"
            origin_country = flight[2]
            longitude = flight[5]
            latitude = flight[6]
            altitude_m = flight[7] 
            velocity_ms = flight[9]

            # Skip planes missing GPS data
            if longitude is None or latitude is None:
                continue

            print(f" Flight: {callsign} ({origin_country})")
            print(f"   Postition: Lat {latitude}, Lon {longitude}")
            print(f"   Altitude: {altitude_m}m | Velocity: {velocity_ms}m/s")
            print("-" * 40)

    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    fetch_live_flights()