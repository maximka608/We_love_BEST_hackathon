import time
from joblib import load

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.config import origins
from src.grade_damage.grade_router import grade_router

app = FastAPI()

model = load('src/model/weights/xgb_pipeline.pkl')
scaler_y = load('src/model/scalers/scaler_y.pkl')

app.state.model = model
app.state.scaler_y = scaler_y

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
async def health_check():
    return {"status": "OK"}


app.include_router(grade_router, prefix="/api/grade", tags=["Grade"])

if __name__ == '__main__':
    uvicorn.run("src.app:app", host="127.0.0.1", port=8000, reload=True)

    print(f"Model loaded successfully {model}")