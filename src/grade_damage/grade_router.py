import pandas as pd
from fastapi import APIRouter, Request
from pydantic import BaseModel
from enum import Enum

from src.grade_damage.services import get_city_data, get_destruction_radius


class DamageLevel(str, Enum):
    small = "small"
    medium = "medium"
    hard = "hard"


class PredictRequest(BaseModel):
    total_house_area_m2: float
    damage_level: DamageLevel
    floors: int


class GetMapRequest(BaseModel):
    center_lat: float
    center_lon: float
    trotil_equivalent: float


grade_router = APIRouter()


@grade_router.post(
    "/predict",
    summary="Predict recovery cost",
    description="Predict the recovery cost for a damaged building based on total area, damage level (small, medium, or hard), and number of floors."
)
def predict(request: Request, body: PredictRequest):
    model = request.app.state.model
    scaler_y = request.app.state.scaler_y
    mean50 = request.app.state.mean50
    deviation = mean50 * 0.5

    input_data = pd.DataFrame([body.model_dump()])

    prediction = model.predict(input_data)
    y_pred_original = scaler_y.inverse_transform(prediction.reshape(-1, 1))

    return {
        "prediction": [
            y_pred_original.tolist()[0][0] - deviation,
            y_pred_original.tolist()[0][0] + deviation
        ],
        "deviation": deviation
    }


@grade_router.post(
    "/getmap",
    summary="Get affected buildings",
    description="Return a list of buildings affected by an explosion based on its center coordinates and TNT equivalent."
)
def getter(request: Request, body: GetMapRequest):
    radii = get_destruction_radius(body.trotil_equivalent)
    nodes = get_city_data(body.center_lat, body.center_lon, radii)

    return {"nodes": nodes}
