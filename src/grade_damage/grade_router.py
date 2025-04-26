from fastapi import APIRouter, Request

grade_router = APIRouter()


@grade_router.post("/predict")
async def predict(request: Request):
    model = request.app.state.model

    return {"message": f"{model}"}
