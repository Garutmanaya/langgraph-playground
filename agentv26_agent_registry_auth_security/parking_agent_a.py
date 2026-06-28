from __future__ import annotations

from fastapi import Depends, FastAPI

from .schemas import ParkingOption, ParkingSearchRequest, ParkingSearchResponse
from .security import require_api_key


AGENT_ID = "company_a_parking_agent"

app = FastAPI(title="Company A Parking Agent", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "agent_id": AGENT_ID}


@app.post("/parking/search", response_model=ParkingSearchResponse, dependencies=[Depends(require_api_key)])
def search_parking(request: ParkingSearchRequest):
    options = [
        ParkingOption(
            company="Company A",
            parking_id="A-G101",
            level="ground",
            price_per_hour=12.0,
            available_slots=4,
            distance_meters=180,
            reservation_supported=True,
        ),
        ParkingOption(
            company="Company A",
            parking_id="A-L201",
            level="level-2",
            price_per_hour=9.5,
            available_slots=8,
            distance_meters=160,
            reservation_supported=True,
        ),
    ]

    filtered = [
        option for option in options
        if option.distance_meters <= request.max_distance_meters
    ]

    return ParkingSearchResponse(agent_id=AGENT_ID, options=filtered)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8601)
