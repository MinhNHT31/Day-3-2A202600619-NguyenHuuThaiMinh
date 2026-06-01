import json
from src.telemetry.logger import logger

# Static database of average living costs by city
LIVING_COST_DB = {
    "Hà Nội": {
        "rent_avg": 3000000,
        "food_avg": 3500000,
        "transport_avg": 500000,
        "note": "Chi phí thiết yếu rất cao, cần cảnh báo người dùng thắt chặt chi tiêu."
    },
    "TP.HCM": {
        "rent_avg": 3500000,
        "food_avg": 4000000,
        "transport_avg": 600000,
        "note": "Chi phí ăn uống và giải trí cao, ưu tiên tự nấu ăn."
    },
    "Đà Nẵng": {
        "rent_avg": 2000000,
        "food_avg": 2500000,
        "transport_avg": 400000,
        "note": "Chi phí hợp lý, dễ dàng phân bổ tiền tiết kiệm."
    }
}

def get_local_living_costs(city: str) -> str:
    """
    Get average living costs for a specific city.
    
    Args:
        city: City name (e.g., 'Hà Nội', 'TP.HCM', 'Đà Nẵng').
        
    Returns:
        JSON string containing average rent, food, transport costs and recommended budgeting rule.
    """
    logger.log_event("TOOL_CALL", {"tool": "get_local_living_costs", "city": city})
    
    # Fuzzy match handling
    matched_city = None
    for k in LIVING_COST_DB.keys():
        if city.lower() in k.lower() or k.lower() in city.lower():
            matched_city = k
            break
            
    if matched_city:
        data = LIVING_COST_DB[matched_city]
        data["city"] = matched_city
        logger.log_event("TOOL_SUCCESS", {"tool": "get_local_living_costs", "city": matched_city})
        return json.dumps(data)
    else:
        logger.log_event("TOOL_ERROR", {"tool": "get_local_living_costs", "error": "City not found"})
        return json.dumps({"error": f"No data found for city: {city}", "note": "Không có dữ liệu, hãy tự phân bổ linh hoạt."})
