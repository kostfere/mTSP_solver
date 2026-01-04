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
    
    - **cities**: List of cities with id and name
    - **distance_matrix**: NxN matrix of distances between cities
    - **num_salesmen**: Number of salesmen/vehicles
    - **depot_city_id**: City ID of the depot (start/end point)
    - **constraints**: Optional constraints object
    - **max_solve_time_seconds**: Maximum solving time (default: 30s)
    
    ## Response
    
    - **status**: 'optimal', 'feasible', 'infeasible', 'timeout', or 'error'
    - **routes**: List of routes for each salesman
    - **total_distance**: Sum of all route distances
    - **solve_time_seconds**: Time taken to solve
    
    ## Example
    
    ```json
    {
      "cities": [
        {"id": 0, "name": "Depot"},
        {"id": 1, "name": "CityA"},
        {"id": 2, "name": "CityB"}
      ],
      "distance_matrix": [
        [0, 10, 20],
        [10, 0, 15],
        [20, 15, 0]
      ],
      "num_salesmen": 2,
      "depot_city_id": 0,
      "constraints": {
        "mandatory_city_assignments": [{"salesman_id": 0, "city_id": 1}],
        "consecutive_visits": [],
        "starting_cities": []
      }
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
