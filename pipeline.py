import os
import requests
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timezone
import random

# Load hidden password from .env
load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Database Connection Settings
DB_PARAMS = {
    "host": "localhost",
    "port": "5432",
    "dbname": "telemetry",
    "user": "aerospace_admin",
    "password": DB_PASSWORD
}

OPENSKY_URL = "https://opensky-network.org/api/states/all"

def run_etl_pipeline():
    print("Starting Aerospace Telemetry Pipeline...")

    try:
        # EXTRACT
        print("Fetching live data from OpenSky...")
        response = requests.get(OPENSKY_URL, timeout=10)
        response.raise_for_status()

        # Taking 50 planes
        flights = response.json().get('states', [])[:50]

        # Connect to Postgres/TimescaleDB
        print("Connecting to TimescaleDB...")
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()

        inserted_count = 0

        # Transform and Load
        print("Processing and loading records...")
        for flight in flights:
            aircraft_id = flight[0] # The unique ICAO24 transponder code
            callsign = str(flight[1]).strip() if flight[1] else "UNKNOWN"
            longitude = flight[5]
            latitude = flight[6]
            altitude_m = flight[7] 
            velocity_ms = flight[9]

            # skip invalid/missing GPS data
            if None in (longitude, latitude, altitude_m, velocity_ms):
                continue

            # Converting units to standard aviation metrics
            altitude_feet = altitude_m * 3.28084
            velocity_knots = velocity_ms * 1.94384

            # Mock data of engine temp since OpenSky doesn't give us engine temps
            engine_temp_c = random.uniform(700.0, 950.0)

            # Creating unique ID for this specific flight trip
            flight_id = f"{callsign}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
            current_time = datetime.now(timezone.utc)

            # Load 1: Insertion into Aircraft Dimension (ON CONFLICT prevents duplicates)
            cursor.execute("""
                    INSERT INTO dim_aircraft (aircraft_id, tail_number, manufacturer, model)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (aircraft_id) DO NOTHING;
                """, (aircraft_id, callsign, 'Unknown', 'Unknown')

            )

            # Load 2: Insert into Flight Dimension
            cursor.execute("""
                INSERT INTO dim_flight (flight_id, aircraft_id, departure_airport, arrival_airport, scheduled_departure)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (flight_id) DO NOTHING;
            """, (flight_id, aircraft_id, 'TBD', 'TBS', current_time)
            )

            # Load 3: Insert into Telemetry Fact Table
            cursor.execute("""
                INSERT INTO fact_telemetry (timestamp, flight_id, latitude, longitude, altitude_feet, velocity_knots, engine_temp_c)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (current_time, flight_id, latitude, longitude, altitude_feet, velocity_knots, engine_temp_c)
            )

            inserted_count +=1

        # Save all changes to database
        conn.commit()

        # Closing connection
        cursor.close()
        conn.close()

        print(f"Success: {inserted_count} telemetry records injected into TimescaleDB!")

    except Exception as e:
        print(f"Pipeline failed: {e}")

if __name__ == "__main__":
    run_etl_pipeline()
