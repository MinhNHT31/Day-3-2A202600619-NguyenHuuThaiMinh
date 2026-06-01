import json
from src.telemetry.logger import logger

def calculate_net_salary(gross_salary: float, region: str = "VN") -> str:
    """
    Calculate Net salary from Gross salary by deducting insurance and taxes.
    
    Args:
        gross_salary: The monthly Gross salary in VNĐ (e.g., 10000000).
        region: The region code (default "VN").
        
    Returns:
        JSON string containing gross, net, and deducted amounts.
    """
    logger.log_event("TOOL_CALL", {"tool": "calculate_net_salary", "gross": gross_salary})
    
    # Simplified calculation for Vietnam
    # Assuming standard insurance deduction ~10.5%
    insurance = gross_salary * 0.105
    
    # Personal deduction threshold is 11,000,000 VNĐ, so for 10M, Tax = 0
    taxable_income = max(0, gross_salary - insurance - 11000000)
    tax = taxable_income * 0.05 if taxable_income > 0 else 0
    
    net_salary = gross_salary - insurance - tax
    
    result = {
        "gross_salary": gross_salary,
        "insurance_deduction": insurance,
        "personal_income_tax": tax,
        "net_salary": net_salary
    }
    
    logger.log_event("TOOL_SUCCESS", {"tool": "calculate_net_salary", "net": net_salary})
    return json.dumps(result)
