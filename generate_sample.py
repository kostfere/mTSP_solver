import json
import random
import math

import argparse

def generate_mtsp_request(num_cities=20, num_salesmen=4):
    # Generate random coordinates for cities
    coords = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(num_cities)]
    
    cities = [{"id": i, "name": f"City_{i}"} for i in range(num_cities)]
    
    # Calculate Euclidean distance matrix
    distance_matrix = []
    for i in range(num_cities):
        row = []
        for j in range(num_cities):
            if i == j:
                row.append(0.0)
            else:
                d = math.sqrt((coords[i][0] - coords[j][0])**2 + (coords[i][1] - coords[j][1])**2)
                row.append(round(d, 2))
        distance_matrix.append(row)
    
    request = {
        "cities": cities,
        "distance_matrix": distance_matrix,
        "num_salesmen": num_salesmen,
        "depot_city_id": 0,
        "constraints": {
            "mandatory_city_assignments": [],
            "consecutive_visits": [],
            "starting_cities": []
        },
        "max_solve_time_seconds": 30,
        "optimize": False
    }
    
    # Add some sample constraints if there are enough cities
    if num_cities > 10:
        request["constraints"]["mandatory_city_assignments"] = [
            {"salesman_id": 0, "city_id": 5}
        ]
        if num_cities > 16:
            request["constraints"]["consecutive_visits"] = [
                {"city_id_1": 15, "city_id_2": 16}
            ]
    
    return request

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate mTSP request sample")
    parser.add_argument("-c", "--cities", type=int, default=20, help="Number of cities")
    parser.add_argument("-s", "--salesmen", type=int, default=4, help="Number of salesmen")
    parser.add_argument("-o", "--output", type=str, default="request_sample.json", help="Output filename")
    
    args = parser.parse_args()
    
    payload = generate_mtsp_request(args.cities, args.salesmen)
    
    with open(args.output, "w") as f:
        json.dump(payload, f, indent=2)
    
    print(f"Sample request with {args.cities} cities and {args.salesmen} salesmen saved to {args.output}")
    print("\nFirst 3 cities in generated distance matrix:")
    for row in payload["distance_matrix"][:3]:
        print(row[:3], "...")
