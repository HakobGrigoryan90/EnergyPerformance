from fastapi import FastAPI, HTTPException, Query
from typing import List
import math

app = FastAPI()

# Emission factors in kg CO2/kWh
EMISSION_FACTORS = {
    "coal": 0.9,
    "natural_gas": 0.45,
    "oil": 0.7,
    "nuclear": 0.004,
    "renewables": 0.03,
    "grid_mix": 0.5  # Average global grid mix
}

def calculate_performance_metrics(hourly_consumption, day_tariff, night_tariff, source):
    # Validate inputs
    if len(hourly_consumption) < 1:
        raise ValueError("Hourly consumption must contain at least 1 value.")
    
    source = source.lower()
    if source not in EMISSION_FACTORS:
        raise ValueError(f"Invalid energy source '{source}'. Valid options are: {list(EMISSION_FACTORS.keys())}")
    
    # Fetch emission factor for the specified source
    emission_factor = EMISSION_FACTORS[source]
    
    # Define daytime and nighttime hours
    day_hours = list(range(6, 22))  # 6 AM to 9 PM (06:00 to 21:59)
    night_hours = list(range(22, 24)) + list(range(0, 6))  # 10 PM to 5 AM (22:00 to 05:59)
    
    # Calculate daytime and nighttime consumption
    daytime_consumption = sum(hourly_consumption[hour] for hour in day_hours if hour < len(hourly_consumption))
    nighttime_consumption = sum(hourly_consumption[hour] for hour in night_hours if hour < len(hourly_consumption))
    
    # Calculate total daily consumption
    total_consumption = sum(hourly_consumption)
    
    # Calculate CO2 emissions
    total_co2_emissions = total_consumption * emission_factor
    
    # Calculate costs for daytime and nighttime consumption
    daytime_cost = daytime_consumption * day_tariff if daytime_consumption > 0 else 0
    nighttime_cost = nighttime_consumption * night_tariff if nighttime_consumption > 0 else 0
    
    # Calculate total cost
    total_cost = daytime_cost + nighttime_cost
    
    # Prepare response metrics
    performance_metrics = {
        "Average Energy Cost per kWh": round(total_cost / total_consumption, 2) if total_consumption > 0 else 0,
        "Total Day Time Consumption (kWh)": round(daytime_consumption, 2),
        "Total Night Time Consumption (kWh)": round(nighttime_consumption, 2),
        "Total Carbon Emissions (kg CO2)": round(total_co2_emissions, 3),
        "Total Energy Consumption (kWh)": round(total_consumption, 2),
        "Daytime Cost ($)": round(daytime_cost, 2),
        "Nighttime Cost ($)": round(nighttime_cost, 2),
        "Total Cost ($)": round(total_cost, 2)
    }
    
    return performance_metrics

@app.post("/api/performance_metrics")
async def performance_metrics(
    hourly_consumption: List[float] = Query(..., description="Hourly energy consumption in kWh (minimum of 1 value)"),
    day_tariff: float = Query(..., description="Daytime tariff in $/kWh"),
    night_tariff: float = Query(..., description="Nighttime tariff in $/kWh"),
    source: str = Query(..., description="Energy source (e.g., coal, natural_gas, oil, nuclear, renewables)")
):
    """
    API endpoint to calculate performance metrics based on hourly consumption,
    day and night tariffs, and energy source.
    
    Parameters:
        - hourly_consumption: List of hourly energy consumption values in kWh.
                              Minimum of one value is required.
                              If more than 24 values are provided, calculations will be done per day.
        - day_tariff: Daytime tariff in $/kWh.
        - night_tariff: Nighttime tariff in $/kWh.
        - source: Energy source used for electricity generation.
    
    Returns:
        - Performance metrics as a JSON response.
          If more than one day is provided, returns metrics per day.
    """
    
    if len(hourly_consumption) == 0:
        raise HTTPException(status_code=400, detail="Hourly consumption must contain at least one value.")
    
    try:
        results = []
        
        # Split hourly consumption into chunks of up to 24 hours (1 day each)
        num_days = math.ceil(len(hourly_consumption) / 24)
        
        for day_index in range(num_days):
            start_index = day_index * 24
            end_index = start_index + 24
            daily_hourly_consumption = hourly_consumption[start_index:end_index]
            
            metrics = calculate_performance_metrics(daily_hourly_consumption, day_tariff, night_tariff, source)
            results.append({"Day": day_index + 1, "Metrics": metrics})
        
        return results
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
