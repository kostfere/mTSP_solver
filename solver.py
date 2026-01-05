"""
mTSP Solver using Google OR-Tools.

Supports constraints:
- Mandatory city assignments (salesman X must visit city Y)
- Consecutive visits (city_id_2 → city_id_1, in that order)
- Starting city constraints (salesman X starts at city Y)
"""
import time
from dataclasses import dataclass
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from models import MTSPRequest, MTSPResponse, Route, Constraints


@dataclass
class SolverResult:
    """Internal result from the solver."""
    status: str
    routes: list[Route]
    total_distance: float
    solve_time: float
    message: str | None = None


def solve_mtsp(request: MTSPRequest) -> MTSPResponse:
    """
    Solve the Multiple Traveling Salesmen Problem with constraints.
    
    Args:
        request: The mTSP problem specification
        
    Returns:
        MTSPResponse with solution routes or error status
    """
    start_time = time.time()
    
    try:
        result = _solve_with_ortools(request)
    except Exception as e:
        result = SolverResult(
            status="error",
            routes=[],
            total_distance=0.0,
            solve_time=time.time() - start_time,
            message=str(e)
        )
    
    return MTSPResponse(
        status=result.status,
        routes=result.routes,
        total_distance=result.total_distance,
        solve_time_seconds=result.solve_time,
        message=result.message
    )


def _solve_with_ortools(request: MTSPRequest) -> SolverResult:
    """Core solving logic using OR-Tools."""
    start_time = time.time()
    
    num_locations = len(request.cities)
    num_vehicles = request.num_salesmen
    depot = request.depot_city_id
    
    # Create city ID to name mapping
    city_id_to_name = {c.id: c.name for c in request.cities}
    
    # Create the routing index manager
    # For starting city constraints, we need to handle them specially
    starts = [depot] * num_vehicles
    ends = [depot] * num_vehicles
    
    if request.constraints and request.constraints.starting_cities:
        for sc in request.constraints.starting_cities:
            starts[sc.salesman_id] = sc.city_id
    
    manager = pywrapcp.RoutingIndexManager(
        num_locations,
        num_vehicles,
        starts,
        ends
    )
    
    # Create Routing Model
    routing = pywrapcp.RoutingModel(manager)
    
    # Create distance callback
    def distance_callback(from_index: int, to_index: int) -> int:
        """Returns the distance between two nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        # OR-Tools works better with integers, so scale by 1000
        return int(request.distance_matrix[from_node][to_node] * 1000)
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    
    # Define cost of each arc
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Add Distance dimension for consecutive visit constraints
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        3000000,  # maximum distance per vehicle
        True,  # start cumul to zero
        dimension_name
    )
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    
    # Apply constraints
    if request.constraints:
        _apply_mandatory_city_constraints(routing, manager, request.constraints, num_vehicles)
        _apply_consecutive_visit_constraints(routing, manager, request.constraints)
    
    # Setting first solution heuristic
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    
    # Only use metaheuristic optimization if explicitly requested
    if request.optimize:
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = request.max_solve_time_seconds
    else:
        # Return immediately when first solution is found
        search_parameters.solution_limit = 1
        # Still set a time limit as a safety net
        search_parameters.time_limit.seconds = request.max_solve_time_seconds
    
    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)
    
    solve_time = time.time() - start_time
    
    if solution:
        routes = _extract_routes(routing, manager, solution, city_id_to_name, num_vehicles)
        total_distance = sum(r.total_distance for r in routes)
        
        # Solution found - mark as optimal (OR-Tools uses metaheuristics, so "optimal" means good solution found)
        return SolverResult(
            status="optimal",
            routes=routes,
            total_distance=total_distance,
            solve_time=solve_time
        )
    else:
        # No solution found - determine status from routing.status()
        solver_status = routing.status()
        # Status codes: 0=NOT_SOLVED, 1=SUCCESS, 2=FAIL, 3=FAIL_TIMEOUT, 4=INVALID
        status_map = {
            0: "not_solved",
            1: "success",  # shouldn't happen if solution is None
            2: "infeasible",
            3: "timeout",
            4: "invalid",
        }
        status = status_map.get(solver_status, f"unknown_{solver_status}")
        
        return SolverResult(
            status=status,
            routes=[],
            total_distance=0.0,
            solve_time=solve_time,
            message=f"No solution found. Solver status: {status}"
        )


def _apply_mandatory_city_constraints(
    routing: pywrapcp.RoutingModel,
    manager: pywrapcp.RoutingIndexManager,
    constraints: Constraints,
    num_vehicles: int
) -> None:
    """Apply mandatory city assignment constraints."""
    for mc in constraints.mandatory_city_assignments:
        node_index = manager.NodeToIndex(mc.city_id)
        if node_index == -1:
            continue
        # Set allowed vehicles for this node
        routing.SetAllowedVehiclesForIndex([mc.salesman_id], node_index)


def _apply_consecutive_visit_constraints(
    routing: pywrapcp.RoutingModel,
    manager: pywrapcp.RoutingIndexManager,
    constraints: Constraints
) -> None:
    """Apply consecutive visit constraints.
    
    city_id_1 → city_id_2 means city_id_1 is visited, then immediately city_id_2.
    We model this as a pickup-delivery pair where city_id_1 is pickup and city_id_2 is delivery.
    """
    for cv in constraints.consecutive_visits:
        pickup_index = manager.NodeToIndex(cv.city_id_1)  # First city (pickup)
        delivery_index = manager.NodeToIndex(cv.city_id_2)  # Second city (delivery)
        
        if pickup_index == -1 or delivery_index == -1:
            continue
        
        # Add pickup and delivery constraint
        routing.AddPickupAndDelivery(pickup_index, delivery_index)
        
        # Ensure same vehicle visits both
        routing.solver().Add(
            routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index)
        )
        
        # Ensure pickup comes before delivery (city_id_1 before city_id_2)
        distance_dimension = routing.GetDimensionOrDie('Distance')
        routing.solver().Add(
            distance_dimension.CumulVar(pickup_index) < distance_dimension.CumulVar(delivery_index)
        )
        
        # Force them to be immediately consecutive: 
        # The next node after pickup must be delivery
        routing.solver().Add(
            routing.NextVar(pickup_index) == delivery_index
        )


def _extract_routes(
    routing: pywrapcp.RoutingModel,
    manager: pywrapcp.RoutingIndexManager,
    solution: pywrapcp.Assignment,
    city_id_to_name: dict[int, str],
    num_vehicles: int
) -> list[Route]:
    """Extract routes from OR-Tools solution."""
    routes = []
    
    for vehicle_id in range(num_vehicles):
        route_cities = []
        route_names = []
        route_distance = 0.0
        
        index = routing.Start(vehicle_id)
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route_cities.append(node)
            route_names.append(city_id_to_name[node])
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id) / 1000.0
        
        # Add end depot
        end_node = manager.IndexToNode(index)
        route_cities.append(end_node)
        route_names.append(city_id_to_name[end_node])
        
        routes.append(Route(
            salesman_id=vehicle_id,
            city_sequence=route_cities,
            city_names=route_names,
            total_distance=route_distance
        ))
    
    return routes
