"""
FastAPI application for solving the Multiple Traveling Salesmen Problem.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import MTSPRequest, MTSPResponse
from solver import solve_mtsp

app = FastAPI(
    title="mTSP Solver API",
    description="""
    Solve the Multiple Traveling Salesmen Problem (mTSP) with constraints.
    
    ## Supported Constraints
    
    - **Mandatory city assignments**: Specify that a particular salesman must visit a specific city
    - **Consecutive visits**: Require that two cities are visited one immediately after the other (city_id_2 → city_id_1)
    - **Starting city**: Specify a different starting city for a specific salesman
    
    ## Usage
    
    Send a POST request to `/solve` with your problem specification.
    """,
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/solve", response_model=MTSPResponse)
async def solve(request: MTSPRequest) -> MTSPResponse:
    """
    Solve the Multiple Traveling Salesmen Problem.
    
    ## Request Body
    
    - **cities**: List of cities with id (0 to N-1) and name. IDs must be consecutive starting from 0.
    - **distance_matrix**: NxN matrix of distances. Size must match number of cities.
    - **num_salesmen**: Number of salesmen/vehicles (≥1)
    - **depot_city_id**: City ID of the depot (start/end point for all salesmen)
    - **constraints**: Optional constraints object containing:
      - `mandatory_city_assignments`: Force a salesman to visit a specific city
      - `consecutive_visits`: Force city_id_2 to be visited immediately before city_id_1
      - `starting_cities`: Override starting city for a specific salesman
    - **max_solve_time_seconds**: Maximum solving time (1-300 seconds, default: 30)
    
    ## Response
    
    - **status**: 'optimal', 'feasible', 'infeasible', 'timeout', or 'error'
    - **routes**: List of routes for each salesman (includes depot at start and end)
    - **total_distance**: Sum of all route distances
    - **solve_time_seconds**: Time taken to solve
    
    ## Important Notes
    
    1. **City IDs**: Must be consecutive integers from 0 to N-1
    2. **Distance Matrix**: Must be NxN where N = number of cities
    3. **Constraints**: All referenced city_ids and salesman_ids must be valid
    
    ## Examples
    
    ### Minimal Example (2 cities, 1 salesman, no constraints)
    
    ```json
    {
      "cities": [
        {"id": 0, "name": "Depot"},
        {"id": 1, "name": "CityA"}
      ],
      "distance_matrix": [
        [0, 10],
        [10, 0]
      ],
      "num_salesmen": 1,
      "depot_city_id": 0,
      "optimize": false
    }
    ```
    
    ### Full Example (4 cities, 2 salesmen, all constraint types)
    
    ```json
    {
      "cities": [
        {"id": 0, "name": "Depot"},
        {"id": 1, "name": "CityA"},
        {"id": 2, "name": "CityB"},
        {"id": 3, "name": "CityC"}
      ],
      "distance_matrix": [
        [0, 10, 20, 15],
        [10, 0, 25, 30],
        [20, 25, 0, 12],
        [15, 30, 12, 0]
      ],
      "num_salesmen": 2,
      "depot_city_id": 0,
      "constraints": {
        "mandatory_city_assignments": [{"salesman_id": 0, "city_id": 1}],
        "consecutive_visits": [{"city_id_1": 3, "city_id_2": 2}],
        "starting_cities": [{"salesman_id": 1, "city_id": 2}]
      },
      "max_solve_time_seconds": 30,
      "optimize": true
    }
    ```
    """
    try:
        return solve_mtsp(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
