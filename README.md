### Data Pipeline Architecture
This diagram illustrates the flow of real-time flight telemetry from the OpenSky Network API, through the Python ETL engine, and into the locally hosted TimescaleDB.

```mermaid
graph LR
    A[OpenSky Network API] -->|Extract: Raw JSON| B(Python ETL Engine)
    B -->|Transform: Clean & Convert| B
    B -->|Load: psycopg2| C[(PostgreSQL + TimescaleDB)]
    
    subgraph Docker Container
    C
    end

### Database Schema (Star Schema)
The data is stored using a Star Schema optimized for time-series analysis, separating the static dimensional data (Aircraft, Flights) from the rapidly changing fact data (Telemetry).

erDiagram
    dim_aircraft ||--o{ dim_flight : "operates"
    dim_flight ||--o{ fact_telemetry : "generates"

    dim_aircraft {
        varchar aircraft_id PK
        varchar tail_number
        varchar manufacturer
        varchar model
    }

    dim_flight {
        varchar flight_id PK
        varchar aircraft_id FK
        varchar departure_airport
        varchar arrival_airport
        timestamptz scheduled_departure
    }

    fact_telemetry {
        timestamptz timestamp
        varchar flight_id FK
        float latitude
        float longitude
        float altitude_feet
        float velocity_knots
        float engine_temp_c
    }
