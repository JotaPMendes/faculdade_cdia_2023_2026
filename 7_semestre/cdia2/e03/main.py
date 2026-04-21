from fastapi import FastAPI

from routers.predict import router as predict_router

app = FastAPI(title="Fraud Detection API")
app.include_router(predict_router, prefix="/ml", tags=["ML"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "message": "API ativa"}
