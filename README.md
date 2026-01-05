# mTSP Solver API

A FastAPI application for solving the **Multiple Traveling Salesmen Problem (mTSP)** with constraint support.

## Features

- Solve mTSP with multiple salesmen
- **Mandatory city assignments**: Force a salesman to visit specific cities
- **Consecutive visits**: Require cities to be visited one after another (city_id_1 → city_id_2)
- **Starting city constraints**: Specify different starting points for salesmen

## Setup

```bash
# Install dependencies
poetry install

# Run the server
poetry run uvicorn main:app --reload
```

## API Endpoints

### Health Check
```
GET /health
```

### Solve mTSP
```
POST /solve
Content-Type: application/json
```

### Example Request

```json
{
  "cities": [
    {"id": 0, "name": "Depot"},
    {"id": 1, "name": "CityA"},
    {"id": 2, "name": "CityB"},
    {"id": 3, "name": "CityC"},
    {"id": 4, "name": "CityD"}
  ],
  "distance_matrix": [
    [0, 10, 15, 20, 25],
    [10, 0, 35, 25, 30],
    [15, 35, 0, 30, 20],
    [20, 25, 30, 0, 15],
    [25, 30, 20, 15, 0]
  ],
  "num_salesmen": 2,
  "depot_city_id": 0,
  "constraints": {
    "mandatory_city_assignments": [
      {"salesman_id": 0, "city_id": 1}
    ],
    "consecutive_visits": [
      {"city_id_1": 3, "city_id_2": 4}
    ],
    "starting_cities": [
      {"salesman_id": 1, "city_id": 2}
    ]
  },
  "max_solve_time_seconds": 30,
  "optimize": false
}
```

### Example Response

```json
{
  "status": "optimal",
  "routes": [
    {
      "salesman_id": 0,
      "city_sequence": [0, 1, 0],
      "city_names": ["Depot", "CityA", "Depot"],
      "total_distance": 20.0
    },
    {
      "salesman_id": 1,
      "city_sequence": [2, 3, 4, 0],
      "city_names": ["CityB", "CityC", "CityD", "Depot"],
      "total_distance": 75.0
    }
  ],
  "total_distance": 95.0,
  "solve_time_seconds": 0.15,
  "message": null
}
```

## Constraint Details

### Mandatory City Assignment
```json
{"salesman_id": 0, "city_id": 1}
```
Salesman 0 **must** visit city 1.

### Consecutive Visits
```json
{"city_id_1": 3, "city_id_2": 4}
```
City 3 must be visited **immediately before** city 4 (order: 3 → 4).

### Starting City
```json
{"salesman_id": 1, "city_id": 2}
```
Salesman 1 starts at city 2 instead of the depot.

## Interactive Docs

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
