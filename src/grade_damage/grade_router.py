from fastapi import APIRouter, Request

grade_router = APIRouter()


@grade_router.post("/predict")
async def predict(request: Request):
    model = request.app.state.model
    scaler_X = request.app.state.scaler_X
    scaler_y = request.app.state.scaler_y

    return {"message": f"{model}, scaler_X{scaler_X}, scaler_y{scaler_y}"}
