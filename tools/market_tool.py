import os
import httpx
from typing import Dict, Any, List

# Comprehensive mock database of popular Indian mandis and current commodity prices (INR per Quintal)
MOCK_MANDI_DATABASE = {
    "wheat": [
        {"state": "Punjab", "district": "Ludhiana", "market": "Khanna", "min_price": 2275, "max_price": 2350, "modal_price": 2300, "date": "2026-06-25"},
        {"state": "Haryana", "district": "Karnal", "market": "Karnal", "min_price": 2275, "max_price": 2320, "modal_price": 2290, "date": "2026-06-25"},
        {"state": "Madhya Pradesh", "district": "Indore", "market": "Indore", "min_price": 2200, "max_price": 2500, "modal_price": 2350, "date": "2026-06-25"},
        {"state": "Uttar Pradesh", "district": "Hapur", "market": "Hapur", "min_price": 2250, "max_price": 2300, "modal_price": 2270, "date": "2026-06-25"},
        {"state": "Rajasthan", "district": "Kota", "market": "Kota", "min_price": 2220, "max_price": 2400, "modal_price": 2310, "date": "2026-06-25"},
    ],
    "onion": [
        {"state": "Maharashtra", "district": "Nashik", "market": "Lasalgaon", "min_price": 1500, "max_price": 2200, "modal_price": 1850, "date": "2026-06-25"},
        {"state": "Maharashtra", "district": "Nashik", "market": "Pimpalgaon", "min_price": 1400, "max_price": 2100, "modal_price": 1780, "date": "2026-06-25"},
        {"state": "Karnataka", "district": "Bangalore", "market": "Yeswanthpur", "min_price": 1600, "max_price": 2400, "modal_price": 2000, "date": "2026-06-25"},
        {"state": "Gujarat", "district": "Rajkot", "market": "Rajkot", "min_price": 1300, "max_price": 1900, "modal_price": 1650, "date": "2026-06-25"},
        {"state": "Delhi", "district": "Delhi", "market": "Azadpur", "min_price": 1700, "max_price": 2300, "modal_price": 2100, "date": "2026-06-25"},
    ],
    "potato": [
        {"state": "Uttar Pradesh", "district": "Agra", "market": "Achhnera", "min_price": 1100, "max_price": 1300, "modal_price": 1200, "date": "2026-06-25"},
        {"state": "West Bengal", "district": "Hooghly", "market": "Sheoraphuly", "min_price": 1300, "max_price": 1500, "modal_price": 1400, "date": "2026-06-25"},
        {"state": "Bihar", "district": "Patna", "market": "Patna City", "min_price": 1200, "max_price": 1450, "modal_price": 1320, "date": "2026-06-25"},
        {"state": "Gujarat", "district": "Ahmedabad", "market": "Ahmedabad", "min_price": 1000, "max_price": 1400, "modal_price": 1250, "date": "2026-06-25"},
        {"state": "Punjab", "district": "Jalandhar", "market": "Jalandhar Cantt", "min_price": 1050, "max_price": 1250, "modal_price": 1150, "date": "2026-06-25"},
    ],
    "paddy": [
        {"state": "Punjab", "district": "Amritsar", "market": "Amritsar", "min_price": 2183, "max_price": 2250, "modal_price": 2200, "date": "2026-06-25"},
        {"state": "West Bengal", "district": "Bardhaman", "market": "Burdwan", "min_price": 2183, "max_price": 2300, "modal_price": 2220, "date": "2026-06-25"},
        {"state": "Andhra Pradesh", "district": "Nellore", "market": "Nellore", "min_price": 2200, "max_price": 2450, "modal_price": 2300, "date": "2026-06-25"},
        {"state": "Karnataka", "district": "Raichur", "market": "Raichur", "min_price": 2150, "max_price": 2500, "modal_price": 2350, "date": "2026-06-25"},
        {"state": "Telangana", "district": "Warangal", "market": "Warangal", "min_price": 2183, "max_price": 2350, "modal_price": 2250, "date": "2026-06-25"},
    ],
    "tomato": [
        {"state": "Karnataka", "district": "Kolar", "market": "Kolar", "min_price": 2000, "max_price": 3200, "modal_price": 2600, "date": "2026-06-25"},
        {"state": "Maharashtra", "district": "Pune", "market": "Pune", "min_price": 1800, "max_price": 3000, "modal_price": 2400, "date": "2026-06-25"},
        {"state": "Andhra Pradesh", "district": "Chittoor", "market": "Madanapalle", "min_price": 2200, "max_price": 3500, "modal_price": 2800, "date": "2026-06-25"},
        {"state": "Delhi", "district": "Delhi", "market": "Azadpur", "min_price": 2500, "max_price": 3800, "modal_price": 3100, "date": "2026-06-25"},
    ],
    "cotton": [
        {"state": "Gujarat", "district": "Rajkot", "market": "Rajkot", "min_price": 6800, "max_price": 7500, "modal_price": 7200, "date": "2026-06-25"},
        {"state": "Maharashtra", "district": "Yavatmal", "market": "Yavatmal", "min_price": 6700, "max_price": 7300, "modal_price": 7000, "date": "2026-06-25"},
        {"state": "Telangana", "district": "Adilabad", "market": "Adilabad", "min_price": 6600, "max_price": 7250, "modal_price": 6950, "date": "2026-06-25"},
    ],
    "soybean": [
        {"state": "Madhya Pradesh", "district": "Ujjain", "market": "Ujjain", "min_price": 4300, "max_price": 4750, "modal_price": 4550, "date": "2026-06-25"},
        {"state": "Maharashtra", "district": "Latur", "market": "Latur", "min_price": 4400, "max_price": 4800, "modal_price": 4600, "date": "2026-06-25"},
        {"state": "Rajasthan", "district": "Kota", "market": "Kota", "min_price": 4200, "max_price": 4650, "modal_price": 4450, "date": "2026-06-25"},
    ]
}

# Default mock data for any other commodity requested
DEFAULT_MOCK_DATA = [
    {"state": "National Average", "district": "All Districts", "market": "Primary Mandis", "min_price": 3000, "max_price": 4000, "modal_price": 3500, "date": "2026-06-25"}
]

def get_mandi_prices(commodity: str, state: str = None) -> Dict[str, Any]:
    """
    Fetches live agricultural mandi (market) prices from data.gov.in, with a comprehensive mock fallback.
    Prices are listed in INR per Quintal (100 kg).
    
    Args:
        commodity: The agricultural commodity to search for (e.g., "Wheat", "Onion", "Potato", "Paddy").
        state: Optional filter for a specific Indian State (e.g., "Punjab", "Maharashtra", "Karnataka").
        
    Returns:
        A dictionary containing the list of matching markets, district details, date, 
        and commodity prices (min, max, and modal/average).
    """
    api_key = os.getenv("DATAGOV_API_KEY")
    commodity_clean = commodity.strip().lower()
    
    # Try using data.gov.in API if API key is provided and not mocked
    if api_key and api_key != "mock_key" and api_key.strip():
        try:
            # daily market real time prices resource ID
            resource_id = "9ef8428b-2a6c-4821-ac73-6137401d77c4"
            url = f"https://api.data.gov.in/resource/{resource_id}"
            
            params = {
                "api-key": api_key,
                "format": "json",
                "limit": 50,
                "filters[commodity]": commodity.strip()
            }
            
            if state:
                params["filters[state]"] = state.strip()
                
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    records = data.get("records", [])
                    if records:
                        formatted_records = []
                        for record in records:
                            formatted_records.append({
                                "state": record.get("state"),
                                "district": record.get("district"),
                                "market": record.get("market"),
                                "min_price": float(record.get("min_price", 0)),
                                "max_price": float(record.get("max_price", 0)),
                                "modal_price": float(record.get("modal_price", 0)),
                                "date": record.get("arrival_date", "2026-06-25")
                            })
                        return {
                            "success": True,
                            "source": "data.gov.in API",
                            "commodity": commodity,
                            "records": formatted_records
                        }
        except Exception:
            # Silently fallback to mock database if API call fails
            pass

    # Mock Database Lookup
    # Find matching key in mock database
    matched_key = None
    for key in MOCK_MANDI_DATABASE.keys():
        if key in commodity_clean or commodity_clean in key:
            matched_key = key
            break
            
    # If commodity is not found in mock database, return error
    if matched_key is None:
        return {
            "success": False,
            "error_type": "no_data_found",
            "commodity": commodity,
            "state": state,
            "error": f"No market price data available for '{commodity}'."
        }
        
    records = MOCK_MANDI_DATABASE[matched_key]
    
    # Filter by state if provided
    if state:
        state_clean = state.strip().lower()
        filtered_records = [r for r in records if state_clean in r["state"].lower() or r["state"].lower() in state_clean]
        if filtered_records:
            records = filtered_records
        else:
            return {
                "success": False,
                "error_type": "no_data_found",
                "commodity": commodity,
                "state": state,
                "error": f"No market price data available for '{commodity}' in state '{state}'."
            }
            
    return {
        "success": True,
        "source": "Mock Mandi Database (data.gov.in Fallback)",
        "commodity": commodity.title(),
        "records": records
    }
