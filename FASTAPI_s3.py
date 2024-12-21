from fastapi import FastAPI, HTTPException, Query
from typing import List
import math

app = FastAPI()

# ... (keep the EMISSION_FACTORS and calculate_performance_metrics function as they are)

@app.get("/api/performance_metrics")
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
