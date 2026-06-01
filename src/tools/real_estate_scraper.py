import json
from src.telemetry.logger import logger

# Mock DB simulating a real-estate scraper
RENT_DB = {
    "Cầu Giấy": {"min": 2500000, "avg": 3500000, "max": 6000000, "trend": "HIGH"},
    "Thanh Xuân": {"min": 2000000, "avg": 2800000, "max": 5000000, "trend": "MEDIUM"},
    "Đống Đa": {"min": 3000000, "avg": 4000000, "max": 8000000, "trend": "VERY HIGH"},
    "Hà Đông": {"min": 1500000, "avg": 2200000, "max": 4000000, "trend": "LOW"}
}

def get_rent_prices(district: str, city: str = "Hà Nội") -> str:
    """
    Scrape/Fetch current rent prices for a specific district.
    
    Args:
        district: District name (e.g., 'Cầu Giấy').
        city: City name (default 'Hà Nội').
        
    Returns:
        JSON string containing min, avg, max rent prices and market trend.
    """
    logger.log_event("TOOL_CALL", {"tool": "get_rent_prices", "district": district, "city": city})
    
    matched_district = None
    for k in RENT_DB.keys():
        if district.lower() in k.lower() or k.lower() in district.lower():
            matched_district = k
            break
            
    if matched_district:
        data = RENT_DB[matched_district]
        data["district"] = matched_district
        data["city"] = city
        logger.log_event("TOOL_SUCCESS", {"tool": "get_rent_prices", "district": matched_district})
        return json.dumps(data)
    else:
        # Generic fallback
        fallback = {"district": district, "city": city, "min": 2000000, "avg": 3000000, "max": 5000000, "trend": "UNKNOWN"}
        return json.dumps(fallback)
