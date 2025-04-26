import pandas as pd
from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.grade_damage.services import get_city_data, get_destruction_radius


class PredictRequest(BaseModel):
    total_house_area_m2: float
    damage_level: str
    floors: int

class GetMapRequest(BaseModel):
    center_lat: float
    center_lon: float
    trotil_equivalent: float


grade_router = APIRouter()


@grade_router.post("/predict")
def predict(request: Request, body: PredictRequest):
    model = request.app.state.model
    scaler_y = request.app.state.scaler_y
    mean50 = request.app.state.mean50
    deviation = mean50 * 0.5

    input_data = pd.DataFrame([body.model_dump()])

    prediction = model.predict(input_data)
    y_pred_original = scaler_y.inverse_transform(prediction.reshape(-1, 1))

    return {"prediction": [y_pred_original.tolist()[0][0] - deviation, y_pred_original.tolist()[0][0] + deviation], "deviation": deviation}


@grade_router.post("/getmap")
def getter(request: Request, body: GetMapRequest):
    # body.center_lat = 49.8397
    # body.center_lon = 24.0297
    # body.trotil_equivalent = 500

    radii = get_destruction_radius(body.trotil_equivalent)
    nodes = get_city_data(body.center_lat, body.center_lon, radii)

    return {"nodes": f"{nodes}"}