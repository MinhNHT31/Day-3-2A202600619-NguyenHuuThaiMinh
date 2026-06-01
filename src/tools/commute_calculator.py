import json
from src.telemetry.logger import logger

def calculate_commute_cost(from_location: str, to_location: str, vehicle_type: str = "xe máy") -> str:
    """
    Calculate estimated monthly commute cost based on distance and current gas prices.
    
    Args:
        from_location: Starting location (e.g., 'Cầu Giấy').
        to_location: Destination (e.g., 'Thanh Xuân').
        vehicle_type: Vehicle used (default 'xe máy').
        
    Returns:
        JSON string with distance, daily cost, and monthly commute cost estimate.
    """
    logger.log_event("TOOL_CALL", {"tool": "calculate_commute_cost", "from": from_location, "to": to_location})
    
    # Mock Google Maps API distance calculator
    # Cầu Giấy to Thanh Xuân is about 7km
    estimated_distance_km = 7.0
    
    # Current gas price (RON 95 ~ 24,000 VND/L)
    gas_price_per_liter = 24000
    
    # Average motorbike fuel efficiency ~ 45km / Liter
    liters_per_km = 1 / 45.0
    
    # Calculate costs
    cost_per_km = liters_per_km * gas_price_per_liter
    daily_round_trip_cost = estimated_distance_km * 2 * cost_per_km
    
    # Assuming 22 working days per month
    monthly_cost = round(daily_round_trip_cost * 22, -3) # Round to nearest thousand
    
    result = {
        "route": f"{from_location} -> {to_location}",
        "distance_km": estimated_distance_km,
        "vehicle": vehicle_type,
        "monthly_gas_cost_vnd": monthly_cost,
        "note": "Calculated based on 22 working days and RON 95 price."
    }
    
    logger.log_event("TOOL_SUCCESS", {"tool": "calculate_commute_cost", "cost": monthly_cost})
    return json.dumps(result)
