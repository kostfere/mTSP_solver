"""
Pydantic models for mTSP API request/response validation.
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class City(BaseModel):
    """A city in the problem."""
    id: int = Field(..., ge=0, description="Unique city identifier")
    name: str = Field(..., min_length=1, description="City name")


class MandatoryCityConstraint(BaseModel):
    """Constraint: specific salesman must visit specific city."""
    salesman_id: int = Field(..., ge=0, description="Salesman index (0-based)")
    city_id: int = Field(..., ge=0, description="City ID that must be visited by this salesman")


class ConsecutiveVisitConstraint(BaseModel):
    """Constraint: city_id_1 must be visited immediately before city_id_2.
    
    Order: city_id_1 → city_id_2 (city_id_1 is visited first, then city_id_2)
    """
    city_id_1: int = Field(..., ge=0, description="City to visit first (immediately before city_id_2)")
    city_id_2: int = Field(..., ge=0, description="City to visit second (immediately after city_id_1)")


class StartingCityConstraint(BaseModel):
    """Constraint: specific salesman must start at specific city."""
    salesman_id: int = Field(..., ge=0, description="Salesman index (0-based)")
    city_id: int = Field(..., ge=0, description="City ID where this salesman must start")


class Constraints(BaseModel):
    """Container for all constraint types."""
    mandatory_city_assignments: list[MandatoryCityConstraint] = Field(
        default_factory=list,
        description="List of mandatory city assignments"
    )
    consecutive_visits: list[ConsecutiveVisitConstraint] = Field(
        default_factory=list,
        description="List of consecutive visit constraints (city_id_1 → city_id_2)"
    )
    starting_cities: list[StartingCityConstraint] = Field(
        default_factory=list,
        description="List of starting city constraints"
    )


class MTSPRequest(BaseModel):
    """Request body for mTSP solve endpoint."""
    cities: list[City] = Field(..., min_length=2, description="List of cities")
    distance_matrix: list[list[float]] = Field(
        ..., 
        description="NxN distance matrix where distance_matrix[i][j] is distance from city i to city j"
    )
    num_salesmen: int = Field(..., ge=1, description="Number of salesmen/vehicles")
    depot_city_id: int = Field(..., ge=0, description="City ID of the depot (start/end point)")
    constraints: Optional[Constraints] = Field(
        default=None,
        description="Optional constraints"
    )
    max_solve_time_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Maximum time allowed for solving (1-300 seconds)"
    )
    optimize: bool = Field(
        default=False,
        description="If True, spend full time limit optimizing for best solution. If False (default), return immediately when first feasible solution is found."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
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
                        "mandatory_city_assignments": [
                            {"salesman_id": 0, "city_id": 1}
                        ],
                        "consecutive_visits": [
                            {"city_id_1": 3, "city_id_2": 2}
                        ],
                        "starting_cities": []
                    },
                    "max_solve_time_seconds": 30,
                    "optimize": False
                }
            ]
        }
    }

    @field_validator('distance_matrix')
    @classmethod
    def validate_matrix_square(cls, v: list[list[float]]) -> list[list[float]]:
        """Ensure distance matrix is square."""
        n = len(v)
        for i, row in enumerate(v):
            if len(row) != n:
                raise ValueError(f"Distance matrix must be square. Row {i} has {len(row)} elements, expected {n}")
        return v

    @model_validator(mode='after')
    def validate_consistency(self) -> 'MTSPRequest':
        """Validate consistency between cities and distance matrix."""
        n_cities = len(self.cities)
        n_matrix = len(self.distance_matrix)
        
        if n_cities != n_matrix:
            raise ValueError(
                f"Number of cities ({n_cities}) must match distance matrix size ({n_matrix}x{n_matrix})"
            )
        
        # Validate city IDs are 0 to n-1
        city_ids = {c.id for c in self.cities}
        expected_ids = set(range(n_cities))
        if city_ids != expected_ids:
            raise ValueError(f"City IDs must be consecutive from 0 to {n_cities - 1}")
        
        # Validate depot exists
        if self.depot_city_id not in city_ids:
            raise ValueError(f"Depot city ID {self.depot_city_id} not found in cities")
        
        # Validate constraints reference valid cities and salesmen
        if self.constraints:
            for mc in self.constraints.mandatory_city_assignments:
                if mc.city_id not in city_ids:
                    raise ValueError(f"Mandatory constraint references invalid city ID {mc.city_id}")
                if mc.salesman_id >= self.num_salesmen:
                    raise ValueError(f"Mandatory constraint references invalid salesman ID {mc.salesman_id}")
            
            for cv in self.constraints.consecutive_visits:
                if cv.city_id_1 not in city_ids:
                    raise ValueError(f"Consecutive constraint references invalid city ID {cv.city_id_1}")
                if cv.city_id_2 not in city_ids:
                    raise ValueError(f"Consecutive constraint references invalid city ID {cv.city_id_2}")
                if cv.city_id_1 == cv.city_id_2:
                    raise ValueError("Consecutive constraint cannot have same city for both positions")
            
            for sc in self.constraints.starting_cities:
                if sc.city_id not in city_ids:
                    raise ValueError(f"Starting city constraint references invalid city ID {sc.city_id}")
                if sc.salesman_id >= self.num_salesmen:
                    raise ValueError(f"Starting city constraint references invalid salesman ID {sc.salesman_id}")
        
        return self


class Route(BaseModel):
    """A single salesman's route."""
    salesman_id: int = Field(..., description="Salesman index")
    city_sequence: list[int] = Field(..., description="Ordered list of city IDs visited")
    city_names: list[str] = Field(..., description="Ordered list of city names visited")
    total_distance: float = Field(..., description="Total distance of this route")


class MTSPResponse(BaseModel):
    """Response from mTSP solve endpoint."""
    status: str = Field(..., description="Solution status: 'optimal', 'feasible', 'infeasible', 'error'")
    routes: list[Route] = Field(default_factory=list, description="Routes for each salesman")
    total_distance: float = Field(default=0.0, description="Total distance across all routes")
    solve_time_seconds: float = Field(..., description="Time taken to solve")
    message: Optional[str] = Field(default=None, description="Additional information or error message")
