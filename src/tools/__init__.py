"""
Tool Registry for Personal Finance Agent
"""
import json

from .tax_calculator import calculate_net_salary
from .living_costs import get_local_living_costs
from .real_estate_scraper import get_rent_prices
from .commute_calculator import calculate_commute_cost

TOOL_REGISTRY = {
    "calculate_net_salary": calculate_net_salary,
    "get_local_living_costs": get_local_living_costs,
    "get_rent_prices": get_rent_prices,
    "calculate_commute_cost": calculate_commute_cost,
}

TOOL_DEFINITIONS = [
    {
        "name": "calculate_net_salary",
        "description": (
            "Calculate Net salary from Gross salary by deducting insurance and taxes. "
            "Args: gross_salary (float): Monthly Gross salary in VNĐ (e.g., 10000000)."
        )
    },
    {
        "name": "get_local_living_costs",
        "description": (
            "Get average living costs for a specific city. "
            "Args: city (str): City name (e.g., 'Hà Nội', 'TP.HCM')."
        )
    },
    {
        "name": "get_rent_prices",
        "description": (
            "Scrape/Fetch current rent prices for a specific district. "
            "Args: district (str): District name (e.g., 'Cầu Giấy'). "
            "city (str): Optional city name."
        )
    },
    {
        "name": "calculate_commute_cost",
        "description": (
            "Calculate estimated monthly commute cost based on distance and current gas prices. "
            "Args: from_location (str): Starting point. "
            "to_location (str): Destination point."
        )
    }
]
