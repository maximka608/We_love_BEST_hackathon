import pandas as pd
from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.grade_damage.services import get_city_data


class PredictRequest(BaseModel):
    total_house_area_m2: float
    damage_level: str
    floors: int


grade_router = APIRouter()


@grade_router.post("/predict")
def predict(request: Request, body: PredictRequest):
    model = request.app.state.model
    scaler_y = request.app.state.scaler_y

    input_data = pd.DataFrame([body.dict()])

    prediction = model.predict(input_data)
    y_pred_original = scaler_y.inverse_transform(prediction.reshape(-1, 1))
    std = scaler_y.var_**0.5
    return {"prediction": y_pred_original.tolist(), "std": std}


@grade_router.get("/getter")
def getter(request: Request):
    center_lat, center_lon = 49.8397, 24.0297  # Lviv center
    radii = [100, 300, 600]
    nodes = get_city_data(center_lat, center_lon, radii)

    return {"message": f"{nodes}"}
